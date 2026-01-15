#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKEND API INTEGRATION FOR SELL SIGNALS

Add these routes to your backend_api.py
"""

from flask import jsonify, Blueprint
from datetime import datetime
import sys
import os

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from sell_signal_generator import SellSignalGenerator

# Create blueprint
sell_bp = Blueprint('sell_signals', __name__)


@sell_bp.route('/api/sell-signals', methods=['GET'])
def get_sell_signals():
    """
    Get all SELL signals for display
    
    GET /api/sell-signals
    
    Returns:
        {
            "success": true,
            "signals": [
                {
                    "ticker": "TCB",
                    "type": "Cắt lỗ",
                    "price": 34500,
                    "quantity": 100,
                    "date": "2026-01-15"
                }
            ],
            "count": 1
        }
    """
    try:
        generator = SellSignalGenerator()
        signals = generator.get_sell_signals_for_display()
        
        return jsonify({
            'success': True,
            'signals': signals,
            'count': len(signals)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sell_bp.route('/api/generate-sell-signals', methods=['POST'])
def generate_sell_signals():
    """
    Manually trigger SELL signal generation
    
    POST /api/generate-sell-signals
    
    Returns:
        {
            "success": true,
            "created": 3,
            "message": "Created 3 SELL signals"
        }
    """
    try:
        generator = SellSignalGenerator()
        sell_count = generator.generate_sell_signals()
        
        return jsonify({
            'success': True,
            'created': sell_count,
            'message': f'Created {sell_count} SELL signals',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sell_bp.route('/api/signal-status/<ticker>', methods=['GET'])
def get_signal_status(ticker):
    """
    Get status of BUY signal for a specific ticker
    
    GET /api/signal-status/TCB
    
    Returns:
        {
            "success": true,
            "ticker": "TCB",
            "status": "PARTIAL_SOLD",
            "quantity_sold": 50,
            "entry_price": 36650,
            "current_status": "Holding 50%"
        }
    """
    try:
        import sqlite3
        
        conn = sqlite3.connect('signals.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ticker, entry_price, stop_loss, take_profit, 
                   signal_status, quantity_sold, date
            FROM signals 
            WHERE ticker = ? 
            AND action = 'BUY'
            ORDER BY date DESC
            LIMIT 1
        """, (ticker.upper(),))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({
                'success': False,
                'error': f'No BUY signal found for {ticker}'
            }), 404
        
        # Parse data
        status_labels = {
            'ACTIVE': 'Active - Holding 100%',
            'PARTIAL_SOLD': f'Partial - Sold {row[5]:.0f}%',
            'FULLY_SOLD': 'Fully Sold - Closed'
        }
        
        return jsonify({
            'success': True,
            'ticker': row[0],
            'entry_price': row[1],
            'stop_loss': row[2],
            'take_profit': row[3],
            'status': row[4],
            'quantity_sold': row[5],
            'buy_date': row[6],
            'current_status': status_labels.get(row[4], 'Unknown')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# INTEGRATION INSTRUCTIONS
# ============================================================================

def register_sell_routes(app):
    """
    Register SELL signal routes with Flask app
    
    Usage in backend_api.py:
    
        from backend_sell_api import register_sell_routes
        
        # After creating Flask app
        register_sell_routes(app)
    """
    app.register_blueprint(sell_bp)
    print("✅ SELL signal routes registered")


# ============================================================================
# EXAMPLE USAGE IN backend_api.py
# ============================================================================

"""
Add to backend_api.py:

# At top of file
from backend_sell_api import register_sell_routes

# After app = Flask(__name__)
register_sell_routes(app)

# That's it! Routes are now available:
# GET  /api/sell-signals
# POST /api/generate-sell-signals
# GET  /api/signal-status/<ticker>
"""
