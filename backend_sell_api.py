#!/usr/bin/env python3
"""
BACKEND SELL API - SELL Signal Routes
Separate module for SELL signal endpoints
"""

from flask import request, jsonify
import threading
import os

def register_sell_routes(app):
    """
    Register SELL signal routes to Flask app
    
    Args:
        app: Flask application instance
    """
    
    from sell_signal_scanner_v2 import SellSignalScannerV2
    
    @app.route('/api/scan-sell', methods=['POST'])
    def scan_sell_signals():
        """
        Trigger SELL signal scanner
        
        Request body (optional):
            {
                "days": 7,  // Look back N days
                "delay": 2.0  // Delay between requests
            }
        
        Returns:
            202 Accepted - Scanner started in background
        """
        
        # ✅ Read request data BEFORE thread (in request context!)
        try:
            data = request.json or {}
        except:
            data = {}
        
        days = data.get('days', 7)
        delay = data.get('delay', 2.0)
        
        def run_scanner(days, delay):
            """Thread function - receives parameters, no request access"""
            try:
                print(f"🔍 Starting SELL scanner (days={days}, delay={delay}s)...")
                
                # Use PRODUCTION database URL from environment
                db_url = os.getenv('DATABASE_URL')
                
                if not db_url:
                    print("❌ ERROR: DATABASE_URL not set in environment!")
                    print("❌ Cannot run SELL scanner without database connection")
                    return
                
                # Run scanner with PRODUCTION database
                scanner = SellSignalScannerV2(db_url=db_url)
                sell_signals = scanner.scan(days=days, delay=delay)
                
                print(f"✅ Generated {len(sell_signals)} SELL signals")
                
            except Exception as e:
                print(f"❌ Scanner error: {e}")
                import traceback
                traceback.print_exc()
        
        try:
            # Run in background thread with parameters
            thread = threading.Thread(target=run_scanner, args=(days, delay))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'message': 'SELL scanner started. This will take 5-15 minutes depending on number of stocks.',
                'status': 'scanning'
            }), 202
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    
    @app.route('/api/scan-sell/status', methods=['GET'])
    def get_sell_scan_status():
        """
        Get SELL scanner status
        
        Returns:
            Current status including:
            - Total SELL signals today
            - Count by exit_reason (STOP_LOSS, TAKE_PROFIT)
        """
        
        try:
            from datetime import datetime
            from sqlalchemy import text
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Query SELL signals today
            query = text("""
                SELECT 
                    exit_reason,
                    COUNT(*) as count
                FROM signals
                WHERE action = 'SELL'
                  AND exit_date = :today
                GROUP BY exit_reason
            """)
            
            # Get database engine from app context
            from backend_api import engine
            
            with engine.connect() as conn:
                result = conn.execute(query, {'today': today})
                rows = result.fetchall()
            
            by_reason = {}
            total = 0
            
            for row in rows:
                reason = row[0] or 'UNKNOWN'
                count = row[1]
                by_reason[reason] = count
                total += count
            
            return jsonify({
                'success': True,
                'date': today,
                'total_sell_signals': total,
                'by_reason': by_reason,
                'breakdown': {
                    'stop_loss': by_reason.get('STOP_LOSS', 0),
                    'take_profit': by_reason.get('TAKE_PROFIT', 0)
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    
    @app.route('/api/signals/sell', methods=['GET'])
    def get_sell_signals_only():
        """
        Get only SELL signals with exit_reason
        
        Query params:
            - limit: Number of signals (default 50)
            - exit_reason: Filter by STOP_LOSS or TAKE_PROFIT
        
        Returns:
            List of SELL signals with exit details
        """
        
        try:
            limit = request.args.get('limit', 50, type=int)
            exit_reason = request.args.get('exit_reason', None)
            
            from sqlalchemy import text
            from backend_api import engine
            
            query = text("""
                SELECT 
                    id,
                    ticker,
                    entry_price,
                    exit_price,
                    exit_reason,
                    exit_date,
                    stop_loss,
                    take_profit,
                    strength,
                    created_at
                FROM signals
                WHERE action = 'SELL'
                  AND (:exit_reason IS NULL OR exit_reason = :exit_reason)
                ORDER BY exit_date DESC, created_at DESC
                LIMIT :limit
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query, {
                    'exit_reason': exit_reason,
                    'limit': limit
                })
                rows = result.fetchall()
            
            signals = []
            for row in rows:
                # Calculate P/L
                pl = row[3] - row[2] if row[3] and row[2] else 0
                pl_pct = (pl / row[2] * 100) if row[2] > 0 else 0
                
                signals.append({
                    'id': row[0],
                    'ticker': row[1],
                    'entry_price': row[2],
                    'exit_price': row[3],
                    'exit_reason': row[4],
                    'exit_date': row[5],
                    'stop_loss': row[6],
                    'take_profit': row[7],
                    'strength': row[8],
                    'profit_loss': pl,
                    'profit_loss_pct': pl_pct,
                    'created_at': row[9].isoformat() if row[9] else None
                })
            
            return jsonify({
                'success': True,
                'signals': signals,
                'count': len(signals)
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    print("✅ SELL signal routes registered:")
    print("   POST /api/scan-sell - Trigger scanner")
    print("   GET  /api/scan-sell/status - Get status")
    print("   GET  /api/signals/sell - Get SELL signals")
