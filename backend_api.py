#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - BACKEND API (FIXED GEMINI MODEL)
Complete backend with portfolio, chat, and signals
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
    # ✅ FIX: Use new model
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("⚠️ WARNING: GEMINI_API_KEY not set")
    gemini_model = None

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///ai_advisor.db')
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


# Create tables
Base.metadata.create_all(engine)


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def get_portfolio_context(user_id):
    """Get user portfolio for AI context"""
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        
        if not portfolios:
            return "Portfolio: Empty"
        
        context = "Portfolio:\n"
        total_value = 0
        
        for p in portfolios:
            value = p.quantity * p.avg_price
            total_value += value
            context += f"- {p.ticker}: {p.quantity} shares @ {p.avg_price:,.0f} VND = {value:,.0f} VND\n"
        
        context += f"\nTotal value: {total_value:,.0f} VND"
        return context
        
    except Exception as e:
        print(f"Error getting portfolio context: {e}")
        return "Portfolio: Error loading"
    finally:
        session.close()


def chat_with_gemini(message, portfolio_context):
    """Chat with Gemini AI"""
    if not gemini_model:
        return "AI service not available. Please contact admin."
    
    try:
        prompt = f"""You are an AI investment advisor for Vietnamese stock market.

User's Portfolio:
{portfolio_context}

User's Question: {message}

Provide helpful investment advice in Vietnamese. Be concise and practical.
If portfolio is empty, suggest general investment principles.
"""
        
        response = gemini_model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Gemini error: {e}")
        return f"Xin lỗi, AI không thể trả lời lúc này. Lỗi: {str(e)}"


# ========================================================================
# API ROUTES
# ========================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'gemini': gemini_model is not None,
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
                'code': s.ticker,  # Alias for compatibility
                'strategy': s.strategy,
                'entry_price': s.entry_price,
                'stop_loss': s.stop_loss,
                'take_profit': s.take_profit,
                'risk_reward': s.risk_reward,
                'strength': s.strength or 0,
                'stock_type': s.stock_type,
                'rsi': s.rsi,
                'date': s.date or s.created_at.strftime('%Y-%m-%d'),
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
    ticker = data.get('ticker', '').upper()
    quantity = data.get('quantity', 0)
    price = data.get('price', 0)
    
    if not ticker or quantity <= 0 or price <= 0:
        return jsonify({
            'success': False,
            'error': 'Invalid input data'
        }), 400
    
    session = Session()
    try:
        # Check if exists
        existing = session.query(Portfolio).filter_by(
            user_id=user_id,
            ticker=ticker
        ).first()
        
        if existing:
            # Update existing
            new_total_quantity = existing.quantity + quantity
            new_total_value = (existing.quantity * existing.avg_price) + (quantity * price)
            existing.quantity = new_total_quantity
            existing.avg_price = new_total_value / new_total_quantity
            existing.updated_at = datetime.now()
            message = f"Updated {ticker}"
        else:
            # Add new
            portfolio = Portfolio(
                user_id=user_id,
                ticker=ticker,
                quantity=quantity,
                avg_price=price
            )
            session.add(portfolio)
            message = f"Added {ticker}"
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Portfolio updated'
        })
        
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
            'message': 'Complete migration successful',
            'tables_created': ['signals', 'portfolios', 'chat_history']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# MAIN
# ========================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 AI ADVISOR BACKEND API")
    print("="*70)
    print(f"Gemini API: {'✅ Configured' if gemini_model else '❌ Not configured'}")
    print(f"Database: ai_advisor.db")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=10000)
