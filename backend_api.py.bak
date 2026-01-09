"""
AI Advisor Backend API - With Gemini Integration
Enhanced Portfolio Manager with chat history
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import json
import logging

# Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Warning: google-generativeai not installed. Install with: pip install google-generativeai")

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'signals.db'

# Initialize Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    logger.info("✓ Gemini AI initialized")
else:
    model = None
    logger.warning("⚠️ Gemini API key not found. Set GEMINI_API_KEY environment variable.")

# ============================================================================
# PORTFOLIO ENDPOINTS
# ============================================================================

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get user's portfolio"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticker, quantity, avg_price, created_at, updated_at
            FROM portfolios
            WHERE user_id = ?
            ORDER BY ticker
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        portfolio = []
        for row in rows:
            portfolio.append({
                'ticker': row[0],
                'quantity': row[1],
                'avgPrice': row[2],
                'createdAt': row[3],
                'updatedAt': row[4]
            })
        
        return jsonify({
            'success': True,
            'portfolio': portfolio
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio', methods=['POST'])
def add_to_portfolio():
    """Add stock to portfolio"""
    try:
        data = request.json
        user_id = data.get('user_id', 1)
        ticker = data.get('ticker', '').upper()
        quantity = data.get('quantity', 0)
        price = data.get('price', 0)
        
        if not ticker or quantity <= 0 or price <= 0:
            return jsonify({'success': False, 'error': 'Invalid input'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if stock exists in portfolio
        cursor.execute('''
            SELECT quantity, avg_price FROM portfolios
            WHERE user_id = ? AND ticker = ?
        ''', (user_id, ticker))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing position (average price)
            old_qty = existing[0]
            old_price = existing[1]
            
            new_qty = old_qty + quantity
            new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty
            
            cursor.execute('''
                UPDATE portfolios
                SET quantity = ?, avg_price = ?, updated_at = ?
                WHERE user_id = ? AND ticker = ?
            ''', (new_qty, new_avg_price, datetime.now(), user_id, ticker))
        else:
            # Insert new position
            cursor.execute('''
                INSERT INTO portfolios (user_id, ticker, quantity, avg_price)
                VALUES (?, ?, ?, ?)
            ''', (user_id, ticker, quantity, price))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Portfolio updated'})
        
    except Exception as e:
        logger.error(f"Error adding to portfolio: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/portfolio/<ticker>', methods=['DELETE'])
def remove_from_portfolio(ticker):
    """Remove stock from portfolio"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM portfolios
            WHERE user_id = ? AND ticker = ?
        ''', (user_id, ticker.upper()))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock removed'})
        
    except Exception as e:
        logger.error(f"Error removing from portfolio: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CHAT ENDPOINTS WITH GEMINI
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat with Gemini AI about portfolio"""
    try:
        data = request.json
        user_id = data.get('user_id', 1)
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message required'}), 400
        
        # Get user's portfolio for context
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticker, quantity, avg_price
            FROM portfolios
            WHERE user_id = ?
        ''', (user_id,))
        
        portfolio_data = cursor.fetchall()
        
        # Build portfolio context
        portfolio_context = ""
        if portfolio_data:
            portfolio_context = "\n\nPortfolio hiện tại của khách hàng:\n"
            for ticker, qty, price in portfolio_data:
                portfolio_context += f"- {ticker}: {qty} cổ phiếu @ {price:,.0f} VND\n"
        
        # Generate AI response
        if model:
            # Build context-aware prompt
            system_prompt = f"""Bạn là AI Advisor chuyên nghiệp về đầu tư chứng khoán Việt Nam.
Khách hàng đang hỏi về danh mục đầu tư của họ.
{portfolio_context}

Nhiệm vụ:
- Trả lời câu hỏi một cách chuyên nghiệp, chi tiết
- Phân tích danh mục nếu được hỏi
- Đưa ra lời khuyên đầu tư thông minh
- Giải thích rõ ràng, dễ hiểu
- Luôn nhắc nhở về rủi ro

Câu hỏi của khách hàng: {message}
"""
            
            response = model.generate_content(system_prompt)
            ai_response = response.text
        else:
            # Fallback response
            ai_response = f"""Xin chào! Tôi là AI Advisor.

Danh mục hiện tại của bạn:
{portfolio_context if portfolio_context else "Chưa có cổ phiếu nào"}

Để tôi có thể tư vấn tốt hơn, vui lòng cung cấp API key cho Gemini AI.

Câu hỏi của bạn: "{message}"

(Chức năng AI đang trong chế độ demo. Cấu hình GEMINI_API_KEY để sử dụng đầy đủ.)
"""
        
        # Save chat history
        cursor.execute('''
            INSERT INTO chat_history (user_id, message, response, portfolio_context)
            VALUES (?, ?, ?, ?)
        ''', (user_id, message, ai_response, portfolio_context))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'hasGemini': model is not None
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.'
        }), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response, created_at
            FROM chat_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in reversed(rows):  # Reverse to show oldest first
            history.append({
                'message': row[0],
                'response': row[1],
                'timestamp': row[2]
            })
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat/history', methods=['DELETE'])
def clear_chat_history():
    """Clear chat history"""
    try:
        user_id = request.args.get('user_id', 1, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM chat_history
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'History cleared'})
        
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# SIGNALS ENDPOINTS (existing)
# ============================================================================

@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Get all signals"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticker, strategy, entry_price, stop_loss, take_profit,
                   risk_reward, strength, is_priority, stock_type, rsi, date, action
            FROM signals
            ORDER BY strength DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        signals = []
        for row in rows:
            signals.append({
                'ticker': row[0],
                'strategy': row[1],
                'entryPrice': row[2],
                'stopLoss': row[3],
                'takeProfit': row[4],
                'riskReward': row[5],
                'strength': row[6],
                'isPriority': row[7],
                'stockType': row[8],
                'rsi': row[9],
                'date': row[10],
                'action': row[11]
            })
        
        return jsonify({
            'success': True,
            'count': len(signals),
            'signals': signals
        })
        
    except Exception as e:
        logger.error(f"Error getting signals: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger signal scanner"""
    try:
        import subprocess
        import threading
        
        def run_scanner():
            try:
                subprocess.run(['python', 'scripts/daily_signal_scanner_eod.py'])
            except Exception as e:
                logger.error(f"Scanner error: {str(e)}")
        
        thread = threading.Thread(target=run_scanner)
        thread.start()
        
        return jsonify({
            'success': True,
            'status': 'scanning',
            'message': 'Signal scanner started. This will take 2-3 minutes.'
        })
        
    except Exception as e:
        logger.error(f"Error triggering scan: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gemini': model is not None,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
