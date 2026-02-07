#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADD TO backend_api.py

SELL SIGNAL SCANNER ENDPOINT
Scan SELL signals from existing BUY signals in production database
"""

# ============================================================================
# IMPORTS (Add to top of backend_api.py)
# ============================================================================

import subprocess
import threading
from datetime import datetime, timedelta
import os

# ============================================================================
# SELL SIGNAL SCANNER ENDPOINT (Add after /api/scan endpoint)
# ============================================================================

@app.route('/api/scan-sell', methods=['POST'])
def scan_sell_signals():
    """
    Trigger SELL signal scanner
    
    Scans existing BUY signals and generates SELL signals
    based on 4 exit conditions:
    1. Stop Loss
    2. Take Profit (Partial)
    3. MA20 Consecutive
    4. MA20 High Volume
    
    Returns:
        202: Scanner started successfully
        500: Error starting scanner
    """
    
    def run_scanner():
        """Background task to run SELL scanner"""
        try:
            # Get days parameter (default 2)
            days = request.json.get('days', 2) if request.json else 2
            
            print(f"🔍 Starting SELL scanner (days={days})...")
            
            # Import scanner class
            from sell_signal_scanner_v2 import SellSignalScannerV2
            
            # Use production database
            db_path = os.getenv('DATABASE_URL', 'signals.db')
            
            # If PostgreSQL URL, convert to proper format
            if db_path.startswith('postgres://'):
                db_path = db_path.replace('postgres://', 'postgresql://')
            
            # Initialize scanner
            scanner = SellSignalScannerV2(db_path=db_path)
            
            # Run scan
            sell_signals = scanner.scan(days=days, delay=2.0)
            
            print(f"✓ SELL scanner complete: {len(sell_signals)} signals")
            
        except Exception as e:
            print(f"❌ SELL scanner error: {e}")
    
    try:
        # Start scanner in background thread
        thread = threading.Thread(target=run_scanner)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'SELL signal scanner started. This will take 2-5 minutes.',
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
    
    Returns count of SELL signals generated today
    """
    
    try:
        # Get today's SELL signals
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Count SELL signals
        sell_signals = Signal.query.filter(
            Signal.action == 'SELL',
            Signal.exit_date == today
        ).all()
        
        # Group by exit reason
        by_reason = {}
        for sig in sell_signals:
            reason = sig.exit_reason or 'UNKNOWN'
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        return jsonify({
            'success': True,
            'date': today,
            'total_sell_signals': len(sell_signals),
            'by_reason': by_reason,
            'signals': [{
                'id': sig.id,
                'ticker': sig.ticker,
                'exit_reason': sig.exit_reason,
                'profit_loss_pct': sig.profit_loss_pct,
                'exit_quantity_pct': sig.exit_quantity_pct
            } for sig in sell_signals[:10]]  # Return first 10
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HELPER: AUTO-MIGRATE DATABASE FOR SELL COLUMNS
# ============================================================================

def auto_migrate_sell_columns():
    """
    Auto-add SELL signal columns if they don't exist
    
    Run this on app startup
    """
    
    try:
        from sqlalchemy import inspect
        
        # Get existing columns
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('signals')]
        
        # Required columns for SELL signals
        required_columns = {
            'exit_reason': 'VARCHAR(50)',
            'exit_date': 'DATE',
            'profit_loss_pct': 'FLOAT',
            'exit_quantity_pct': 'FLOAT DEFAULT 100',
            'buy_signal_id': 'INTEGER',
            'volume_ratio': 'FLOAT'
        }
        
        # Add missing columns
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE signals ADD COLUMN {col_name} {col_type}"
                    db.engine.execute(sql)
                    print(f"✓ Added column: {col_name}")
                except Exception as e:
                    print(f"⚠ Column {col_name} already exists or error: {e}")
        
        print("✓ Database migration complete")
        
    except Exception as e:
        print(f"⚠ Migration error: {e}")


# ============================================================================
# ADD TO APP INITIALIZATION
# ============================================================================

# Add this after app initialization, before routes
if __name__ == '__main__' or 'gunicorn' in os.environ.get('SERVER_SOFTWARE', ''):
    # Run migration on startup
    with app.app_context():
        auto_migrate_sell_columns()


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
TRIGGER SELL SCANNER:
---------------------
curl -X POST https://ai-advisor1-backend.onrender.com/api/scan-sell

Or with custom days:
curl -X POST https://ai-advisor1-backend.onrender.com/api/scan-sell \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'


CHECK STATUS:
-------------
curl https://ai-advisor1-backend.onrender.com/api/scan-sell/status


RESPONSE:
---------
{
  "success": true,
  "date": "2026-02-05",
  "total_sell_signals": 26,
  "by_reason": {
    "SL": 2,
    "TP_PARTIAL": 3,
    "MA20_CONSECUTIVE": 20,
    "MA20_HIGH_VOLUME": 1
  }
}
"""
