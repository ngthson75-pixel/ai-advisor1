"""
AI ADVISOR - COMPLETE BACKEND API
Full-featured backend with signal management, admin panel, and database

Deploy to: Render.com
Author: Nguyễn Thanh Sơn
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE = 'signals.db'
SIGNALS_FILE = 'signals_latest.json'

# ============================================================================
# DATABASE SETUP
# ============================================================================

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Signals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            strategy TEXT NOT NULL,
            date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            take_profit REAL NOT NULL,
            risk_reward REAL,
            rsi REAL,
            strength REAL,
            stock_type TEXT,
            is_priority INTEGER,
            conditions TEXT,
            ema20 REAL,
            ema50 REAL,
            volume INTEGER,
            volume_avg INTEGER,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Scan history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TEXT NOT NULL,
            total_stocks INTEGER,
            pullback_count INTEGER,
            ema_cross_count INTEGER,
            duration_seconds REAL,
            status TEXT,
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Admin users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized")

# Initialize database on startup
init_db()

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def dict_from_row(row):
    """Convert sqlite row to dict"""
    return {key: row[key] for key in row.keys()}

# ============================================================================
# API ENDPOINTS - PUBLIC
# ============================================================================

@app.route('/')
def home():
    """API home page"""
    return jsonify({
        'service': 'AI Advisor Backend API',
        'version': '1.0',
        'status': 'online',
        'endpoints': {
            'signals': '/api/signals',
            'signal_detail': '/api/signals/<ticker>',
            'scan_history': '/api/scan-history',
            'admin_panel': '/admin',
            'health': '/health'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if os.path.exists(DATABASE) else 'not found'
    })

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """
    Get all active signals
    Query params:
    - strategy: filter by strategy (pullback, ema_cross)
    - stock_type: filter by type (Blue Chip, Mid Cap, Penny)
    - priority_only: true/false
    - limit: number of results
    """
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Build query
        query = "SELECT * FROM signals WHERE status = 'active'"
        params = []
        
        # Filters
        strategy = request.args.get('strategy')
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy.upper())
        
        stock_type = request.args.get('stock_type')
        if stock_type:
            query += " AND stock_type = ?"
            params.append(stock_type)
        
        priority_only = request.args.get('priority_only')
        if priority_only == 'true':
            query += " AND is_priority = 1"
        
        # Order by strength
        query += " ORDER BY strength DESC, created_at DESC"
        
        # Limit
        limit = request.args.get('limit', 100)
        query += f" LIMIT {limit}"
        
        # Execute
        c.execute(query, params)
        rows = c.fetchall()
        
        signals = []
        for row in rows:
            signal = dict_from_row(row)
            # Parse JSON fields
            if signal.get('conditions'):
                signal['conditions'] = json.loads(signal['conditions'])
            signals.append(signal)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(signals),
            'signals': signals
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/signals/<ticker>', methods=['GET'])
def get_signal_detail(ticker):
    """Get signal detail for specific ticker"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute(
            "SELECT * FROM signals WHERE ticker = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (ticker.upper(),)
        )
        row = c.fetchone()
        conn.close()
        
        if row:
            signal = dict_from_row(row)
            if signal.get('conditions'):
                signal['conditions'] = json.loads(signal['conditions'])
            
            return jsonify({
                'success': True,
                'signal': signal
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Signal not found'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/signals/summary', methods=['GET'])
def get_signals_summary():
    """Get signals summary statistics"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Count by strategy
        c.execute("""
            SELECT strategy, COUNT(*) as count
            FROM signals
            WHERE status = 'active'
            GROUP BY strategy
        """)
        by_strategy = {row['strategy']: row['count'] for row in c.fetchall()}
        
        # Count by stock type
        c.execute("""
            SELECT stock_type, COUNT(*) as count
            FROM signals
            WHERE status = 'active'
            GROUP BY stock_type
        """)
        by_type = {row['stock_type']: row['count'] for row in c.fetchall()}
        
        # Top signals
        c.execute("""
            SELECT ticker, strategy, strength, entry_price
            FROM signals
            WHERE status = 'active'
            ORDER BY strength DESC
            LIMIT 10
        """)
        top_signals = [dict_from_row(row) for row in c.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_signals': sum(by_strategy.values()),
                'by_strategy': by_strategy,
                'by_type': by_type,
                'top_signals': top_signals,
                'last_updated': datetime.now().isoformat()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scan-history', methods=['GET'])
def get_scan_history():
    """Get scan history"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        limit = request.args.get('limit', 30)
        
        c.execute("""
            SELECT * FROM scan_history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        history = [dict_from_row(row) for row in c.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(history),
            'history': history
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# API ENDPOINTS - ADMIN
# ============================================================================

@app.route('/api/admin/signals', methods=['POST'])
def add_signal():
    """Add new signal (admin only)"""
    try:
        data = request.json
        
        conn = get_db()
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO signals (
                ticker, strategy, date, entry_price, stop_loss, take_profit,
                risk_reward, rsi, strength, stock_type, is_priority,
                conditions, ema20, ema50, volume, volume_avg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['ticker'],
            data['strategy'],
            data['date'],
            data['entry_price'],
            data['stop_loss'],
            data['take_profit'],
            data.get('risk_reward'),
            data.get('rsi'),
            data.get('strength'),
            data.get('stock_type'),
            1 if data.get('is_priority') else 0,
            json.dumps(data.get('conditions', {})),
            data.get('ema20'),
            data.get('ema50'),
            data.get('volume'),
            data.get('volume_avg')
        ))
        
        conn.commit()
        signal_id = c.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'signal_id': signal_id,
            'message': 'Signal added successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/signals/bulk', methods=['POST'])
def add_signals_bulk():
    """Add multiple signals from scanner output"""
    try:
        data = request.json
        
        conn = get_db()
        c = conn.cursor()
        
        # Clear old signals (optional)
        clear_old = data.get('clear_old', False)
        if clear_old:
            c.execute("UPDATE signals SET status = 'archived' WHERE status = 'active'")
        
        # Add new signals
        added_count = 0
        
        for signal in data.get('pullback', []):
            c.execute("""
                INSERT INTO signals (
                    ticker, strategy, date, entry_price, stop_loss, take_profit,
                    risk_reward, rsi, strength, stock_type, is_priority,
                    conditions, ema20, ema50, volume, volume_avg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['ticker'],
                'PULLBACK',
                signal['date'],
                signal['entry_price'],
                signal['stop_loss'],
                signal['take_profit'],
                signal.get('risk_reward'),
                signal.get('rsi'),
                signal.get('strength'),
                signal.get('stock_type'),
                1 if signal.get('is_priority') else 0,
                json.dumps(signal.get('conditions', {})),
                signal.get('ema20'),
                signal.get('ema50'),
                signal.get('volume'),
                signal.get('volume_avg')
            ))
            added_count += 1
        
        for signal in data.get('ema_cross', []):
            c.execute("""
                INSERT INTO signals (
                    ticker, strategy, date, entry_price, stop_loss, take_profit,
                    risk_reward, rsi, strength, stock_type, is_priority,
                    conditions, ema20, ema50, volume, volume_avg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal['ticker'],
                'EMA_CROSS',
                signal['date'],
                signal['entry_price'],
                signal['stop_loss'],
                signal['take_profit'],
                signal.get('risk_reward'),
                signal.get('rsi'),
                signal.get('strength'),
                signal.get('stock_type'),
                1 if signal.get('is_priority') else 0,
                json.dumps(signal.get('conditions', {})),
                signal.get('ema20'),
                signal.get('ema50'),
                signal.get('volume'),
                signal.get('volume_avg')
            ))
            added_count += 1
        
        # Add scan history
        metadata = data.get('metadata', {})
        c.execute("""
            INSERT INTO scan_history (
                scan_date, total_stocks, pullback_count, ema_cross_count, status
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            metadata.get('scan_date', datetime.now().isoformat()),
            0,  # Will be filled by scanner
            len(data.get('pullback', [])),
            len(data.get('ema_cross', [])),
            'completed'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'added_count': added_count,
            'message': f'Added {added_count} signals successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/signals/<int:signal_id>', methods=['DELETE'])
def delete_signal(signal_id):
    """Delete signal (admin only)"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute("UPDATE signals SET status = 'deleted' WHERE id = ?", (signal_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Signal deleted'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ADMIN PANEL (Simple HTML)
# ============================================================================

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Advisor - Admin Panel</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .signals-table {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f8f9fa;
            font-weight: bold;
        }
        .strategy-pullback { color: #28a745; }
        .strategy-ema { color: #007bff; }
        .priority-star { color: #ffc107; }
        .button {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .button:hover {
            background: #5568d3;
        }
        .button-danger {
            background: #dc3545;
        }
        .button-danger:hover {
            background: #c82333;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Advisor - Admin Panel</h1>
        <p>Manage trading signals and monitor system</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value" id="total-signals">-</div>
            <div class="stat-label">Total Active Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="pullback-count">-</div>
            <div class="stat-label">PULLBACK Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="ema-count">-</div>
            <div class="stat-label">EMA_CROSS Signals</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="last-scan">-</div>
            <div class="stat-label">Last Scan</div>
        </div>
    </div>

    <div class="signals-table">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <h2>📊 Active Signals</h2>
            <div>
                <button class="button" onclick="refreshSignals()">🔄 Refresh</button>
                <button class="button button-danger" onclick="archiveAll()">🗄️ Archive All</button>
            </div>
        </div>
        
        <table id="signals-table">
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Strategy</th>
                    <th>Entry Price</th>
                    <th>Stop Loss</th>
                    <th>Take Profit</th>
                    <th>R:R</th>
                    <th>Strength</th>
                    <th>Type</th>
                    <th>Date</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="signals-tbody">
                <tr><td colspan="10" style="text-align: center; padding: 50px;">Loading...</td></tr>
            </tbody>
        </table>
    </div>

    <script>
        async function loadStats() {
            try {
                const res = await fetch('/api/signals/summary');
                const data = await res.json();
                
                if (data.success) {
                    const summary = data.summary;
                    document.getElementById('total-signals').textContent = summary.total_signals;
                    document.getElementById('pullback-count').textContent = summary.by_strategy['PULLBACK'] || 0;
                    document.getElementById('ema-count').textContent = summary.by_strategy['EMA_CROSS'] || 0;
                    document.getElementById('last-scan').textContent = new Date(summary.last_updated).toLocaleTimeString();
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        async function loadSignals() {
            try {
                const res = await fetch('/api/signals');
                const data = await res.json();
                
                if (data.success) {
                    const tbody = document.getElementById('signals-tbody');
                    
                    if (data.signals.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 50px;">No active signals</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = data.signals.map(signal => `
                        <tr>
                            <td>
                                ${signal.is_priority ? '<span class="priority-star">⭐</span>' : ''}
                                <strong>${signal.ticker}</strong>
                            </td>
                            <td class="strategy-${signal.strategy.toLowerCase().split('_')[0]}">${signal.strategy}</td>
                            <td>${Number(signal.entry_price).toLocaleString()}</td>
                            <td>${Number(signal.stop_loss).toLocaleString()}</td>
                            <td>${Number(signal.take_profit).toLocaleString()}</td>
                            <td>${signal.risk_reward ? signal.risk_reward.toFixed(2) : '-'}</td>
                            <td><strong>${signal.strength ? signal.strength.toFixed(0) : '-'}%</strong></td>
                            <td>${signal.stock_type}</td>
                            <td>${signal.date}</td>
                            <td>
                                <button class="button button-danger" onclick="deleteSignal(${signal.id})">Delete</button>
                            </td>
                        </tr>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading signals:', error);
            }
        }

        async function deleteSignal(id) {
            if (!confirm('Delete this signal?')) return;
            
            try {
                const res = await fetch(`/api/admin/signals/${id}`, { method: 'DELETE' });
                const data = await res.json();
                
                if (data.success) {
                    refreshSignals();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error deleting signal: ' + error);
            }
        }

        async function archiveAll() {
            if (!confirm('Archive all active signals?')) return;
            
            // Not implemented yet
            alert('Archive all functionality - coming soon!');
        }

        function refreshSignals() {
            loadStats();
            loadSignals();
        }

        // Auto-refresh every 5 minutes
        setInterval(refreshSignals, 5 * 60 * 1000);

        // Initial load
        refreshSignals();
    </script>
</body>
</html>
"""

@app.route('/admin')
def admin_panel():
    """Admin panel page"""
    return render_template_string(ADMIN_TEMPLATE)

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
