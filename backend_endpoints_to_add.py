# ==========================================
# ADD THESE ENDPOINTS TO backend_api.py
# ==========================================

# Add imports at top if not already there:
import subprocess
import os
from datetime import datetime
import sqlite3

# Add these endpoints anywhere in the file:

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """
    Trigger signal scanner manually
    Used by GitHub Actions automation
    
    Returns:
        202: Scanner started successfully
        500: Error starting scanner
    """
    try:
        # Get scanner path
        scanner_path = os.path.join(
            os.path.dirname(__file__), 
            'scripts', 
            'daily_signal_scanner_eod.py'
        )
        
        # Check scanner file exists
        if not os.path.exists(scanner_path):
            return jsonify({
                'success': False,
                'error': f'Scanner not found at {scanner_path}'
            }), 404
        
        # Run scanner in background
        process = subprocess.Popen([
            'python', 
            scanner_path
        ], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(__file__)
        )
        
        return jsonify({
            'success': True,
            'status': 'scanning',
            'message': 'Signal scanner started. This will take 20-25 minutes for 343 stocks.',
            'process_id': process.pid
        }), 202
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/scan/status', methods=['GET'])
def scan_status():
    """
    Check scan status and signal count
    
    Returns:
        200: Status info with signal count
    """
    try:
        # Connect to database
        db_path = os.path.join(os.path.dirname(__file__), 'signals.db')
        
        if not os.path.exists(db_path):
            return jsonify({
                'success': True,
                'signals_count': 0,
                'status': 'no_database',
                'message': 'Database not found - no scans run yet'
            })
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get today's signal count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM signals 
            WHERE date = date('now')
        """)
        today_count = cursor.fetchone()[0]
        
        # Get total signal count
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_count = cursor.fetchone()[0]
        
        # Get last scan time (from latest signal)
        cursor.execute("""
            SELECT MAX(created_at) 
            FROM signals
        """)
        last_scan = cursor.fetchone()[0]
        
        conn.close()
        
        # Determine status
        if today_count > 0:
            status = 'complete'
            is_recent = True
        elif total_count > 0:
            status = 'old_data'
            is_recent = False
        else:
            status = 'no_signals'
            is_recent = False
        
        return jsonify({
            'success': True,
            'signals_count': today_count,
            'total_signals': total_count,
            'last_scan': last_scan,
            'is_recent': is_recent,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': True,
            'signals_count': 0,
            'status': 'error',
            'error': str(e)
        })


# ==========================================
# USAGE FROM GITHUB ACTIONS:
# ==========================================

# 1. Trigger scan:
#    POST https://ai-advisor1-staging.onrender.com/api/scan
#    Returns: 202 {"status":"scanning"}

# 2. Check status:
#    GET https://ai-advisor1-staging.onrender.com/api/scan/status
#    Returns: 200 {"signals_count":78, "status":"complete"}

# 3. Get signals:
#    GET https://ai-advisor1-staging.onrender.com/api/signals
#    Returns: 200 {"success":true, "signals":[...]}
