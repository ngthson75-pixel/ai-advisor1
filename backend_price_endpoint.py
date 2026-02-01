"""
BACKEND API ENHANCEMENT - Auto-fetch EOD Price Endpoint

Add this to your existing backend_api.py
"""

from datetime import datetime, timedelta
from vnstock import Vnstock

# ============================================================================
# NEW ENDPOINT: Auto-fetch current/EOD price
# ============================================================================

@app.route('/api/stock/current-price', methods=['GET'])
def get_current_price():
    """
    Get current/latest EOD price for a stock
    
    Usage:
        GET /api/stock/current-price?ticker=VCB
    
    Returns:
        {
            "success": true,
            "price": 96500.0,
            "source": "intraday" | "eod",
            "timestamp": "2025-01-24T10:30:00"
        }
    """
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({
            'success': False,
            'error': 'Ticker required'
        }), 400
    
    ticker = ticker.upper()
    
    try:
        stock_api = Vnstock()
        stock = stock_api.stock(symbol=ticker, source='VCI')
        
        # Try intraday data first (real-time if market is open)
        try:
            intraday = stock.quote.intraday(symbol=ticker, page_size=1)
            if not intraday.empty:
                price = float(intraday['close'].iloc[-1])
                return jsonify({
                    'success': True,
                    'price': price,
                    'source': 'intraday',
                    'timestamp': datetime.now().isoformat(),
                    'ticker': ticker
                })
        except Exception as e:
            print(f"Intraday failed for {ticker}: {e}")
        
        # Fallback to EOD (End of Day) data
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        daily = stock.quote.history(symbol=ticker, start=yesterday, end=today)
        
        if not daily.empty:
            price = float(daily['close'].iloc[-1])
            trade_date = daily.index[-1].strftime('%Y-%m-%d') if hasattr(daily.index[-1], 'strftime') else 'recent'
            
            return jsonify({
                'success': True,
                'price': price,
                'source': 'eod',
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'trade_date': trade_date
            })
        
        # No data found
        return jsonify({
            'success': False,
            'error': f'No price data found for {ticker}',
            'ticker': ticker
        }), 404
        
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'ticker': ticker
        }), 500


# ============================================================================
# OPTIONAL: Batch price fetch (for updating multiple stocks at once)
# ============================================================================

@app.route('/api/stock/batch-prices', methods=['POST'])
def get_batch_prices():
    """
    Get prices for multiple stocks at once
    
    Usage:
        POST /api/stock/batch-prices
        Body: {
            "tickers": ["VCB", "HPG", "VNM"]
        }
    
    Returns:
        {
            "success": true,
            "prices": {
                "VCB": 96500.0,
                "HPG": 28300.0,
                "VNM": 87400.0
            },
            "failed": []
        }
    """
    data = request.json
    tickers = data.get('tickers', [])
    
    if not tickers or not isinstance(tickers, list):
        return jsonify({
            'success': False,
            'error': 'Tickers array required'
        }), 400
    
    stock_api = Vnstock()
    prices = {}
    failed = []
    
    for ticker in tickers:
        try:
            stock = stock_api.stock(symbol=ticker.upper(), source='VCI')
            
            # Try intraday first
            try:
                intraday = stock.quote.intraday(symbol=ticker.upper(), page_size=1)
                if not intraday.empty:
                    prices[ticker.upper()] = float(intraday['close'].iloc[-1])
                    continue
            except:
                pass
            
            # Fallback to EOD
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            
            daily = stock.quote.history(symbol=ticker.upper(), start=yesterday, end=today)
            
            if not daily.empty:
                prices[ticker.upper()] = float(daily['close'].iloc[-1])
            else:
                failed.append(ticker.upper())
                
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            failed.append(ticker.upper())
    
    return jsonify({
        'success': True,
        'prices': prices,
        'failed': failed,
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# DATABASE SCHEMA UPDATE (if needed)
# ============================================================================

"""
Add 'current_price' column to portfolios table if not exists:

ALTER TABLE portfolios ADD COLUMN current_price REAL;
ALTER TABLE portfolios ADD COLUMN price_updated_at TIMESTAMP;

Or in SQLAlchemy:

class Portfolio(Base):
    # ... existing columns ...
    current_price = Column(Float, nullable=True)
    price_updated_at = Column(DateTime, nullable=True)
"""
