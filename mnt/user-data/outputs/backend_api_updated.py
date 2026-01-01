# Add this to your backend_api.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import subprocess
import os
import threading

app = Flask(__name__)
CORS(app)

# Database setup
DB_PATH = 'signals.db'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            strategy TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            take_profit REAL NOT NULL,
            risk_reward REAL,
            strength REAL,
            is_priority INTEGER DEFAULT 0,
            stock_type TEXT,
            rsi REAL,
            date TEXT,
            action TEXT DEFAULT 'BUY',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'signals_count': count,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get all signals from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all signals
        cursor.execute('''
            SELECT id, ticker, strategy, entry_price, stop_loss, take_profit,
                   risk_reward, strength, is_priority, stock_type, rsi, date, action
            FROM signals
            ORDER BY is_priority DESC, strength DESC, created_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'id': row[0],
                'ticker': row[1],
                'strategy': row[2],
                'entry_price': row[3],
                'stop_loss': row[4],
                'take_profit': row[5],
                'risk_reward': row[6],
                'strength': row[7],
                'is_priority': row[8],
                'stock_type': row[9],
                'rsi': row[10],
                'date': row[11],
                'action': row[12] or 'BUY'
            })
        
        return jsonify({
            'success': True,
            'count': len(signals),
            'signals': signals
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'signals': []
        }), 500

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger signal scanner"""
    try:
        # Check if scanner script exists
        scanner_path = os.path.join(os.path.dirname(__file__), 'scripts', 'daily_signal_scanner.py')
        
        if not os.path.exists(scanner_path):
            # Try alternative path
            scanner_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'daily_signal_scanner.py')
        
        if not os.path.exists(scanner_path):
            return jsonify({
                'success': False,
                'message': 'Scanner script not found',
                'scanner_path': scanner_path
            }), 404
        
        # Run scanner in background thread
        def run_scanner():
            try:
                result = subprocess.run(
                    ['python', scanner_path],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                print(f"Scanner output: {result.stdout}")
                if result.stderr:
                    print(f"Scanner errors: {result.stderr}")
            except Exception as e:
                print(f"Scanner error: {str(e)}")
        
        # Start scanner in background
        thread = threading.Thread(target=run_scanner)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Signal scanner started. This will take 2-3 minutes.',
            'status': 'scanning'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scan/status', methods=['GET'])
def scan_status():
    """Check if scanning is in progress"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check last signal timestamp
        cursor.execute('''
            SELECT MAX(created_at) FROM signals
        ''')
        last_scan = cursor.fetchone()[0]
        
        # Count signals
        cursor.execute('SELECT COUNT(*) FROM signals')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        # If last scan was less than 5 minutes ago, consider it "recent"
        is_recent = False
        if last_scan:
            from datetime import datetime, timedelta
            last_scan_time = datetime.fromisoformat(last_scan)
            is_recent = (datetime.now() - last_scan_time) < timedelta(minutes=5)
        
        return jsonify({
            'success': True,
            'signals_count': count,
            'last_scan': last_scan,
            'is_recent': is_recent,
            'status': 'complete' if count > 0 else 'empty'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
