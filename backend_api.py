#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - BACKEND API (PRODUCTION READY)
Fixed for Render deployment with proper database path
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import google.generativeai as genai
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # ✅ Use new model (gemini-pro is deprecated)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini API configured with gemini-1.5-flash")
else:
    print("⚠️ WARNING: GEMINI_API_KEY not set")
    gemini_model = None

# Database setup - FIXED for Render
Base = declarative_base()

# ✅ Use /tmp directory on Render (ephemeral but works)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:////tmp/ai_advisor.db')
print(f"📊 Database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


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

def get_portfolio_context(user_id):
    """Get user portfolio for AI context"""
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        
        if not portfolios:
            return "Portfolio: Empty (no stocks added yet)"
        
        context = "Current Portfolio:\n"
        total_value = 0
        
        for p in portfolios:
            value = p.quantity * p.avg_price
            total_value += value
            context += f"- {p.ticker}: {p.quantity} shares @ {p.avg_price:,.0f} VND = {value:,.0f} VND\n"
        
        context += f"\nTotal Portfolio Value: {total_value:,.0f} VND"
        return context
        
    except Exception as e:
        print(f"Error getting portfolio context: {e}")
        return "Portfolio: Error loading data"
    finally:
        session.close()


def chat_with_gemini(message, portfolio_context):
    """Chat with Gemini AI"""
    if not gemini_model:
        return "Xin lỗi, dịch vụ AI chưa được cấu hình. Vui lòng liên hệ admin."
    
    try:
        prompt = f"""Bạn là AI tư vấn đầu tư chứng khoán Việt Nam.

Danh mục của người dùng:
{portfolio_context}

Câu hỏi: {message}

Hãy đưa ra lời khuyên đầu tư hữu ích bằng tiếng Việt. Ngắn gọn và thực tế.
Nếu danh mục trống, gợi ý các nguyên tắc đầu tư cơ bản.
"""
        
        response = gemini_model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        error_msg = str(e)
        print(f"Gemini error: {error_msg}")
        
        # Handle specific errors
        if "429" in error_msg:
            return "Xin lỗi, AI đang quá tải. Vui lòng thử lại sau 1 phút."
        elif "quota" in error_msg.lower():
            return "Xin lỗi, đã hết quota API. Vui lòng thử lại sau."
        else:
            return f"Xin lỗi, AI không thể trả lời lúc này. Vui lòng thử lại."


# ========================================================================
# API ROUTES
# ========================================================================

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'AI Advisor Backend API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'signals': '/api/signals',
            'portfolio': '/api/portfolio',
            'chat': '/api/chat',
            'migrate': '/api/migrate'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'gemini': gemini_model is not None,
        'database': 'sqlite',
        'timestamp': datetime.now().isoformat()
    })


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
                'date': s.date or s.created_at.strftime('%Y-%m-%d') if s.created_at else None,
                'action': s.action,
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        
        return jsonify({
            'success': True,
            'signals': signals_data,
            'count': len(signals_data)
        })
        
    except Exception as e:
        print(f"Error in get_signals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get user portfolio"""
    user_id = request.args.get('user_id', 1, type=int)
    
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        
        portfolio_data = []
        for p in portfolios:
            portfolio_data.append({
                'id': p.id,
                'ticker': p.ticker,
                'quantity': p.quantity,
                'avg_price': p.avg_price,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'portfolio': portfolio_data
        })
        
    except Exception as e:
        print(f"Error in get_portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/portfolio', methods=['POST'])
def add_portfolio():
    """Add or update stock in portfolio"""
    data = request.json
    
    user_id = data.get('user_id', 1)
    ticker = data.get('ticker', '').upper().strip()
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0))
    
    if not ticker or quantity <= 0 or price <= 0:
        return jsonify({
            'success': False,
            'error': 'Invalid input: ticker, quantity, and price are required'
        }), 400
    
    session = Session()
    try:
        # Check if exists
        existing = session.query(Portfolio).filter_by(
            user_id=user_id,
            ticker=ticker
        ).first()
        
        if existing:
            # Update existing - calculate new average
            new_total_quantity = existing.quantity + quantity
            new_total_value = (existing.quantity * existing.avg_price) + (quantity * price)
            existing.quantity = new_total_quantity
            existing.avg_price = new_total_value / new_total_quantity
            existing.updated_at = datetime.now()
        else:
            # Add new
            portfolio = Portfolio(
                user_id=user_id,
                ticker=ticker,
                quantity=quantity,
                avg_price=price
            )
            session.add(portfolio)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio updated'
        })
        
    except Exception as e:
        session.rollback()
        print(f"Error in add_portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/portfolio/<ticker>', methods=['DELETE'])
def delete_portfolio(ticker):
    """Delete stock from portfolio"""
    user_id = request.args.get('user_id', 1, type=int)
    
    session = Session()
    try:
        portfolio = session.query(Portfolio).filter_by(
            user_id=user_id,
            ticker=ticker.upper()
        ).first()
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Stock not found in portfolio'
            }), 404
        
        session.delete(portfolio)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {ticker}'
        })
        
    except Exception as e:
        session.rollback()
        print(f"Error in delete_portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with AI"""
    data = request.json
    
    user_id = data.get('user_id', 1)
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'Message is required'
        }), 400
    
    session = Session()
    try:
        # Get portfolio context
        portfolio_context = get_portfolio_context(user_id)
        
        # Get AI response
        ai_response = chat_with_gemini(message, portfolio_context)
        
        # Save to history
        chat_entry = ChatHistory(
            user_id=user_id,
            message=message,
            response=ai_response,
            portfolio_context=portfolio_context
        )
        session.add(chat_entry)
        session.commit()
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        session.rollback()
        print(f"Error in chat: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Xin lỗi, đã có lỗi xảy ra.'
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
        
        # Reverse to show oldest first
        history_data.reverse()
        
        return jsonify({
            'success': True,
            'history': history_data
        })
        
    except Exception as e:
        print(f"Error in get_chat_history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/chat/history', methods=['DELETE'])
def clear_chat_history():
    """Clear chat history"""
    user_id = request.args.get('user_id', 1, type=int)
    
    session = Session()
    try:
        session.query(ChatHistory).filter_by(user_id=user_id).delete()
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Chat history cleared'
        })
        
    except Exception as e:
        session.rollback()
        print(f"Error in clear_chat_history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/migrate', methods=['POST'])
def migrate():
    """Run database migration"""
    try:
        Base.metadata.create_all(engine)
        print("✅ Database tables created successfully")
        
        return jsonify({
            'success': True,
            'message': 'Complete migration successful',
            'tables_created': ['signals', 'portfolios', 'chat_history']
        })
        
    except Exception as e:
        print(f"Error in migrate: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# STARTUP
# ========================================================================

# Create tables on startup
try:
    print("\n🚀 Starting AI Advisor Backend API...")
    Base.metadata.create_all(engine)
    print("✅ Database initialized")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")


# ========================================================================
# MAIN
# ========================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print(f"\n{'='*70}")
    print("🚀 AI ADVISOR BACKEND API")
    print(f"{'='*70}")
    print(f"Gemini: {'✅ Configured' if gemini_model else '❌ Not configured'}")
    print(f"Database: {DATABASE_URL}")
    print(f"Port: {port}")
    print(f"{'='*70}\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
