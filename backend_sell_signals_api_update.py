"""
BACKEND API UPDATE - SELL SIGNALS WITH EXIT REASON
Thêm field 'exit_reason' vào API response để frontend hiển thị

Add to: backend_api.py
"""

# ==============================================================================
# UPDATE GET SIGNALS ENDPOINT
# ==============================================================================

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get signals with proper exit_reason field"""
    
    action = request.args.get('action')  # 'BUY' or 'SELL'
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Build query based on action filter
                if action:
                    query = """
                        SELECT 
                            ticker,
                            strategy,
                            entry_price,
                            stop_loss,
                            take_profit,
                            risk_reward,
                            strength,
                            stock_type,
                            date,
                            action,
                            created_at
                        FROM signals
                        WHERE action = %s
                        ORDER BY created_at DESC
                    """
                    cur.execute(query, (action,))
                else:
                    query = """
                        SELECT 
                            ticker,
                            strategy,
                            entry_price,
                            stop_loss,
                            take_profit,
                            risk_reward,
                            strength,
                            stock_type,
                            date,
                            action,
                            created_at
                        FROM signals
                        ORDER BY created_at DESC
                    """
                    cur.execute(query)
                
                rows = cur.fetchall()
                
                # Format response
                signals = []
                for row in rows:
                    signal = {
                        'ticker': row[0],
                        'strategy': row[1],
                        'entry_price': float(row[2]) if row[2] else None,
                        'stop_loss': float(row[3]) if row[3] else None,
                        'take_profit': float(row[4]) if row[4] else None,
                        'risk_reward': float(row[5]) if row[5] else None,
                        'strength': int(row[6]) if row[6] else None,
                        'stock_type': row[7],
                        'date': row[8].isoformat() if row[8] else None,
                        'action': row[9],
                        'created_at': row[10].isoformat() if row[10] else None
                    }
                    
                    # Add exit_reason for SELL signals
                    if signal['action'] == 'SELL':
                        signal['exit_reason'] = row[1]  # strategy field contains STOP_LOSS or TAKE_PROFIT
                        
                        # Calculate exit price (for display)
                        # Note: This should ideally be stored in DB, but we can calculate for now
                        # You may want to add an 'exit_price' column to your DB schema
                    
                    signals.append(signal)
                
                return jsonify({
                    'success': True,
                    'count': len(signals),
                    'signals': signals
                }), 200
                
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==============================================================================
# HELPER FUNCTION - Format Exit Reason for Display
# ==============================================================================

def format_exit_reason(strategy):
    """
    Format exit reason từ strategy field
    
    Args:
        strategy: 'STOP_LOSS' or 'TAKE_PROFIT'
        
    Returns:
        dict với text, icon, color
    """
    
    exit_reasons = {
        'STOP_LOSS': {
            'text': 'Cắt lỗ (SL)',
            'text_en': 'Stop Loss',
            'icon': '🔴',
            'color': 'red',
            'badge_class': 'bg-red-100 text-red-800 border-red-200'
        },
        'TAKE_PROFIT': {
            'text': 'Chốt lời (TP)',
            'text_en': 'Take Profit',
            'icon': '🟢',
            'color': 'green',
            'badge_class': 'bg-green-100 text-green-800 border-green-200'
        },
        'MA20_BREAK': {
            'text': 'Phá MA20',
            'text_en': 'MA20 Break',
            'icon': '🟡',
            'color': 'yellow',
            'badge_class': 'bg-yellow-100 text-yellow-800 border-yellow-200'
        }
    }
    
    return exit_reasons.get(strategy, {
        'text': 'Khác',
        'text_en': 'Other',
        'icon': '⚪',
        'color': 'gray',
        'badge_class': 'bg-gray-100 text-gray-800 border-gray-200'
    })


# ==============================================================================
# OPTIONAL: Add exit_price column to database
# ==============================================================================

"""
SQL Migration (run once):

ALTER TABLE signals 
ADD COLUMN exit_price NUMERIC(10, 2);

Then update scanner to save exit_price when creating SELL signal:

def save_sell_signal(ticker, entry_price, exit_price, sl, tp, reason):
    query = '''
        INSERT INTO signals (
            ticker, strategy, entry_price, exit_price, 
            stop_loss, take_profit, date, action
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    values = (ticker, reason, entry_price, exit_price, sl, tp, today, 'SELL')
"""
