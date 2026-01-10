#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - BACKEND API (OpenAI Version)
Simple, fast deployment with GPT-4o-mini
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
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
    print("✅ OpenAI API configured")
else:
    print("⚠️ WARNING: OPENAI_API_KEY not set")
    openai_client = None

# Database setup
Base = declarative_base()
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
            return "Danh mục đầu tư: Trống (chưa có cổ phiếu nào)"
        
        context = "Danh mục đầu tư hiện tại:\n"
        total_value = 0
        
        for p in portfolios:
            value = p.quantity * p.avg_price
            total_value += value
            context += f"- {p.ticker}: {p.quantity} cổ phiếu @ {p.avg_price:,.0f} VND = {value:,.0f} VND\n"
        
        context += f"\nTổng giá trị danh mục: {total_value:,.0f} VND"
        return context
        
    except Exception as e:
        print(f"Error getting portfolio: {e}")
        return "Danh mục: Lỗi khi tải dữ liệu"
    finally:
        session.close()


def chat_with_gpt(message, portfolio_context):
    """Chat with GPT-4o-mini"""
    if not openai_client:
        return "Xin lỗi, dịch vụ AI chưa được cấu hình. Vui lòng liên hệ admin."
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Cheapest GPT-4 model
            messages=[
                {
                    "role": "system", 
                    "content": f"""Bạn là AI tư vấn đầu tư chứng khoán Việt Nam.
                    
{portfolio_context}

Hãy đưa ra lời khuyên đầu tư hữu ích, ngắn gọn và thực tế.
Nếu danh mục trống, gợi ý các nguyên tắc đầu tư cơ bản."""
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        print(f"OpenAI error: {error_msg}")
        
        if "rate_limit" in error_msg.lower():
            return "Xin lỗi, AI đang quá tải. Vui lòng thử lại sau 1 phút."
        elif "quota" in error_msg.lower():
            return "Xin lỗi, đã hết quota API. Vui lòng nạp thêm credit."
        elif "invalid" in error_msg.lower():
            return "Xin lỗi, API key không hợp lệ. Vui lòng kiểm tra cấu hình."
        else:
            return "Xin lỗi, AI không thể trả lời lúc này. Vui lòng thử lại."


# ========================================================================
# API ROUTES
# ========================================================================

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'AI Advisor Backend API',
        'version': '1.0 (OpenAI)',
        'status': 'running',
        'ai': 'GPT-4o-mini' if openai_client else 'Not configured'
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'openai': openai_client is not None,
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
            'error': 'Invalid input'
        }), 400
    
    session = Session()
    try:
        existing = session.query(Portfolio).filter_by(
            user_id=user_id,
            ticker=ticker
        ).first()
        
        if existing:
            new_total_quantity = existing.quantity + quantity
            new_total_value = (existing.quantity * existing.avg_price) + (quantity * price)
            existing.quantity = new_total_quantity
            existing.avg_price = new_total_value / new_total_quantity
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
    """Delete stock from portfolio"""
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
        
        history_data.reverse()
        return jsonify({'success': True, 'history': history_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/migrate', methods=['POST'])
def migrate():
    """Run database migration"""
    try:
        Base.metadata.create_all(engine)
        return jsonify({
            'success': True,
            'message': 'Migration successful',
            'tables': ['signals', 'portfolios', 'chat_history']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# STARTUP
# ========================================================================

try:
    print("\n🚀 Starting AI Advisor Backend...")
    Base.metadata.create_all(engine)
    print("✅ Database initialized")
except Exception as e:
    print(f"⚠️ Warning: {e}")


# ========================================================================
# MAIN
# ========================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print(f"\n{'='*70}")
    print("🚀 AI ADVISOR BACKEND (OpenAI)")
    print(f"{'='*70}")
    print(f"AI: {'✅ GPT-4o-mini' if openai_client else '❌ Not configured'}")
    print(f"Database: {DATABASE_URL}")
    print(f"Port: {port}")
    print(f"{'='*70}\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
