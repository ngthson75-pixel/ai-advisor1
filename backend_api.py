#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - COMPLETE BACKEND v3.0
ALL FEATURES: Signals, EOD Prices, Cash, P&L, Chat AI
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import json
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configure OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI configured")
else:
    print("⚠️ OPENAI_API_KEY not set")
    openai_client = None

# Database
Base = declarative_base()
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:////tmp/ai_advisor.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# EOD prices file
PRICES_FILE = 'latest_prices.json'

# Mock EOD prices (fallback if file doesn't exist)
MOCK_PRICES = {
    'VCB': {'price': 90000, 'change_percent': 1.5},
    'VHM': {'price': 58000, 'change_percent': -0.8},
    'VIC': {'price': 42000, 'change_percent': 0.5},
    'TCB': {'price': 26500, 'change_percent': 2.1},
    'HPG': {'price': 28000, 'change_percent': 1.2},
    'MBB': {'price': 27500, 'change_percent': -0.3},
    'FPT': {'price': 145000, 'change_percent': 0.8},
    'VNM': {'price': 87000, 'change_percent': 0.2}
}


# ========================================================================
# DATABASE MODELS
# ========================================================================

class Signal(Base):
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    strategy = Column(String(50))
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    risk_reward = Column(Float)
    strength = Column(Float)
    stock_type = Column(String(50))
    rsi = Column(Float)
    date = Column(String(20))
    action = Column(String(10), default='BUY')
    created_at = Column(DateTime, default=datetime.now)


class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    ticker = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CashPosition(Base):
    __tablename__ = 'cash_positions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)
    cash_amount = Column(Float, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ChatHistory(Base):
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    portfolio_context = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def load_latest_prices():
    """Load EOD prices from file or use mock"""
    try:
        if os.path.exists(PRICES_FILE):
            with open(PRICES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('prices', {})
    except Exception as e:
        print(f"Error loading prices: {e}")
    
    # Fallback to mock prices
    return MOCK_PRICES


def get_current_price(ticker):
    """Get current price for ticker"""
    prices = load_latest_prices()
    if ticker in prices:
        return prices[ticker].get('price', 0)
    return 0


def get_portfolio_context(user_id):
    """Get portfolio context with P&L for AI"""
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        cash = cash_pos.cash_amount if cash_pos else 0
        
        prices = load_latest_prices()
        
        if not portfolios and cash == 0:
            return "Danh mục: Trống"
        
        context = "DANH MỤC ĐẦU TƯ:\n\n"
        
        if portfolios:
            context += "CỔ PHIẾU:\n"
            total_cost = 0
            total_value = 0
            
            for p in portfolios:
                cost = p.quantity * p.avg_price
                total_cost += cost
                
                current_price = prices.get(p.ticker, {}).get('price', p.avg_price)
                current_value = p.quantity * current_price
                total_value += current_value
                
                pl = current_value - cost
                pl_pct = (pl / cost * 100) if cost > 0 else 0
                
                context += f"- {p.ticker}: {p.quantity} CP @ {p.avg_price:,.0f} VND\n"
                context += f"  Giá hiện tại: {current_price:,.0f} VND\n"
                context += f"  P&L: {pl:+,.0f} VND ({pl_pct:+.1f}%)\n"
            
            context += f"\nTổng giá trị CP: {total_value:,.0f} VND\n"
            context += f"Lãi/Lỗ: {total_value - total_cost:+,.0f} VND\n"
        
        if cash > 0:
            context += f"\nTIỀN MẶT: {cash:,.0f} VND\n"
        
        total_assets = (total_value if portfolios else 0) + cash
        if total_assets > 0:
            stock_pct = ((total_value if portfolios else 0) / total_assets * 100)
            cash_pct = (cash / total_assets * 100)
            context += f"\nTỔNG TÀI SẢN: {total_assets:,.0f} VND\n"
            context += f"Phân bổ: {stock_pct:.1f}% CP / {cash_pct:.1f}% TM\n"
        
        return context
        
    except Exception as e:
        print(f"Error: {e}")
        return "Danh mục: Lỗi"
    finally:
        session.close()


def chat_with_gpt(message, portfolio_context):
    """Chat with OpenAI"""
    if not openai_client:
        return "Xin lỗi, AI chưa được cấu hình."
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Bạn là AI tư vấn đầu tư VN.\n\n{portfolio_context}\n\nTrả lời ngắn gọn, thực tế."},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Xin lỗi, AI không phản hồi được."


# ========================================================================
# API ROUTES
# ========================================================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'AI Advisor Backend v3.0',
        'version': '3.0',
        'features': ['signals', 'portfolio', 'cash', 'eod_prices', 'chat_ai'],
        'status': 'running'
    })


@app.route('/health', methods=['GET'])
def health():
    prices = load_latest_prices()
    return jsonify({
        'status': 'healthy',
        'openai': openai_client is not None,
        'prices_loaded': len(prices),
        'timestamp': datetime.now().isoformat()
    })


# ========================================================================
# SIGNALS ENDPOINTS
# ========================================================================

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get all signals"""
    session = Session()
    try:
        signals = session.query(Signal).order_by(Signal.created_at.desc()).all()
        
        signals_data = []
        for s in signals:
            signals_data.append({
                'id': s.id,
                'ticker': s.ticker,
                'code': s.ticker,
                'strategy': s.strategy,
                'entry_price': s.entry_price,
                'stop_loss': s.stop_loss,
                'take_profit': s.take_profit,
                'risk_reward': s.risk_reward,
                'strength': s.strength or 0,
                'stock_type': s.stock_type,
                'rsi': s.rsi,
                'date': s.date or (s.created_at.strftime('%Y-%m-%d') if s.created_at else None),
                'action': s.action,
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        
        return jsonify({
            'success': True,
            'signals': signals_data,
            'count': len(signals_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/scan', methods=['POST'])
def scan_signals():
    """Scan for new signals (mock for now)"""
    try:
        # Mock signals for testing
        session = Session()
        
        # Create sample signals
        sample_tickers = ['VCB', 'VHM', 'HPG', 'TCB']
        prices = load_latest_prices()
        
        created_count = 0
        for ticker in sample_tickers:
            # Check if already exists today
            today = datetime.now().strftime('%Y-%m-%d')
            existing = session.query(Signal).filter(
                Signal.ticker == ticker,
                Signal.date == today
            ).first()
            
            if existing:
                continue
            
            # Get price
            price = prices.get(ticker, {}).get('price', 50000)
            
            # Create signal
            signal = Signal(
                ticker=ticker,
                strategy='PULLBACK',
                entry_price=price,
                stop_loss=price * 0.95,
                take_profit=price * 1.08,
                risk_reward=1.6,
                strength=75,
                stock_type='Blue Chip',
                rsi=65,
                date=today,
                action='BUY'
            )
            session.add(signal)
            created_count += 1
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Quét hoàn tất! Tìm thấy {created_count} tín hiệu mới.',
            'signals_created': created_count
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/scan/status', methods=['GET'])
def scan_status():
    """Get scan status"""
    return jsonify({
        'success': True,
        'status': 'ready',
        'last_scan': datetime.now().isoformat()
    })


# ========================================================================
# PORTFOLIO ENDPOINTS
# ========================================================================

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio with P&L"""
    user_id = request.args.get('user_id', 1, type=int)
    
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        cash = cash_pos.cash_amount if cash_pos else 0
        
        prices = load_latest_prices()
        
        portfolio_data = []
        for p in portfolios:
            current_price = prices.get(p.ticker, {}).get('price', p.avg_price)
            cost = p.quantity * p.avg_price
            current_value = p.quantity * current_price
            pl_amount = current_value - cost
            pl_pct = (pl_amount / cost * 100) if cost > 0 else 0
            
            portfolio_data.append({
                'id': p.id,
                'ticker': p.ticker,
                'quantity': p.quantity,
                'avg_price': p.avg_price,
                'current_price': current_price,
                'cost': cost,
                'current_value': current_value,
                'pl_amount': pl_amount,
                'pl_pct': pl_pct,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'portfolio': portfolio_data,
            'cash': cash
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/portfolio', methods=['POST'])
def add_portfolio():
    """Add stock to portfolio"""
    data = request.json
    
    user_id = data.get('user_id', 1)
    ticker = data.get('ticker', '').upper().strip()
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0))
    
    if not ticker or quantity <= 0 or price <= 0:
        return jsonify({'success': False, 'error': 'Invalid input'}), 400
    
    session = Session()
    try:
        existing = session.query(Portfolio).filter_by(
            user_id=user_id,
            ticker=ticker
        ).first()
        
        if existing:
            new_qty = existing.quantity + quantity
            new_value = (existing.quantity * existing.avg_price) + (quantity * price)
            existing.quantity = new_qty
            existing.avg_price = new_value / new_qty
            existing.updated_at = datetime.now()
        else:
            portfolio = Portfolio(
                user_id=user_id,
                ticker=ticker,
                quantity=quantity,
                avg_price=price
            )
            session.add(portfolio)
        
        session.commit()
        return jsonify({'success': True, 'message': 'Portfolio updated'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/portfolio/<ticker>', methods=['DELETE'])
def delete_portfolio(ticker):
    """Delete stock"""
    user_id = request.args.get('user_id', 1, type=int)
    
    session = Session()
    try:
        portfolio = session.query(Portfolio).filter_by(
            user_id=user_id,
            ticker=ticker.upper()
        ).first()
        
        if not portfolio:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        
        session.delete(portfolio)
        session.commit()
        return jsonify({'success': True, 'message': f'Deleted {ticker}'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ========================================================================
# CASH ENDPOINTS
# ========================================================================

@app.route('/api/cash', methods=['GET'])
def get_cash():
    """Get cash position"""
    user_id = request.args.get('user_id', 1, type=int)
    
    session = Session()
    try:
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        return jsonify({
            'success': True,
            'cash': cash_pos.cash_amount if cash_pos else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/cash', methods=['POST'])
def update_cash():
    """Update cash position"""
    data = request.json
    
    user_id = data.get('user_id', 1)
    cash_amount = float(data.get('cash', 0))
    
    if cash_amount < 0:
        return jsonify({'success': False, 'error': 'Cash cannot be negative'}), 400
    
    session = Session()
    try:
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        
        if cash_pos:
            cash_pos.cash_amount = cash_amount
            cash_pos.updated_at = datetime.now()
        else:
            cash_pos = CashPosition(user_id=user_id, cash_amount=cash_amount)
            session.add(cash_pos)
        
        session.commit()
        return jsonify({'success': True, 'message': 'Cash updated', 'cash': cash_amount})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ========================================================================
# PRICES ENDPOINTS
# ========================================================================

@app.route('/api/prices/latest', methods=['GET'])
def get_latest_prices():
    """Get all latest prices"""
    try:
        prices = load_latest_prices()
        return jsonify({
            'success': True,
            'prices': prices,
            'count': len(prices)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prices/<ticker>', methods=['GET'])
def get_ticker_price(ticker):
    """Get price for ticker"""
    try:
        prices = load_latest_prices()
        
        if ticker.upper() not in prices:
            return jsonify({
                'success': False,
                'error': f'Price not found for {ticker}'
            }), 404
        
        return jsonify({
            'success': True,
            'ticker': ticker.upper(),
            'data': prices[ticker.upper()]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# CHAT ENDPOINTS
# ========================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with AI"""
    data = request.json
    
    user_id = data.get('user_id', 1)
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400
    
    session = Session()
    try:
        portfolio_context = get_portfolio_context(user_id)
        ai_response = chat_with_gpt(message, portfolio_context)
        
        chat_entry = ChatHistory(
            user_id=user_id,
            message=message,
            response=ai_response,
            portfolio_context=portfolio_context
        )
        session.add(chat_entry)
        session.commit()
        
        return jsonify({'success': True, 'response': ai_response})
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Xin lỗi, có lỗi xảy ra.'
        }), 500
    finally:
        session.close()


@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    user_id = request.args.get('user_id', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    session = Session()
    try:
        history = session.query(ChatHistory)\
            .filter_by(user_id=user_id)\
            .order_by(ChatHistory.created_at.desc())\
            .limit(limit)\
            .all()
        
        history_data = []
        for h in history:
            history_data.append({
                'id': h.id,
                'message': h.message,
                'response': h.response,
                'created_at': h.created_at.isoformat() if h.created_at else None
            })
        
        history_data.reverse()
        return jsonify({'success': True, 'history': history_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ========================================================================
# MIGRATION
# ========================================================================

@app.route('/api/migrate', methods=['POST'])
def migrate():
    """Run migration"""
    try:
        Base.metadata.create_all(engine)
        return jsonify({
            'success': True,
            'message': 'Migration successful',
            'tables': ['signals', 'portfolios', 'cash_positions', 'chat_history']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# STARTUP
# ========================================================================

try:
    print("\n🚀 Starting AI Advisor Backend v3.0...")
    Base.metadata.create_all(engine)
    print("✅ Database initialized")
    
    prices = load_latest_prices()
    print(f"💰 Loaded {len(prices)} prices")
    
except Exception as e:
    print(f"⚠️ Warning: {e}")


# ========================================================================
# MAIN
# ========================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print(f"\n{'='*70}")
    print("🚀 AI ADVISOR BACKEND v3.0 - COMPLETE")
    print(f"{'='*70}")
    print(f"AI: {'✅ GPT-4o-mini' if openai_client else '❌ Not configured'}")
    print(f"Database: {DATABASE_URL}")
    print(f"Prices: {len(load_latest_prices())} tickers")
    print(f"Port: {port}")
    print(f"{'='*70}\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
