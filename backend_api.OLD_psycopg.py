#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - BACKEND v3.3 - FIXED
WITH STRICT AI SYSTEM PROMPT FOR INVESTMENT GUIDANCE
"""

# ========================================================================
# IMPORTS (ALL AT TOP - NO DUPLICATES)
# ========================================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json
import subprocess
import sqlite3
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from vnstock import Vnstock

# SELL Signal Integration
from backend_sell_api import register_sell_routes

# ========================================================================
# FLASK APP INITIALIZATION
# ========================================================================

app = Flask(__name__)
CORS(app)

# Register SELL Signal Routes
register_sell_routes(app)
print("✅ SELL signal routes registered")

# ========================================================================
# CONFIGURATION
# ========================================================================

# Configure OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI configured")
else:
    print("⚠️ OPENAI_API_KEY not set")
    openai_client = None

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')

# Fix PostgreSQL URL for psycopg3
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

# EOD file settings
EOD_FILE = 'latest_prices_all.json'
PRICES_CACHE = {}
CACHE_LOADED = False

# ========================================================================
# DATABASE SETUP
# ========================================================================

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# ========================================================================
# AI SYSTEM PROMPT
# ========================================================================

AI_SYSTEM_PROMPT = """You are AI ADVISOR, a decision-support system for investors.

Your primary role:
- Support investment decision-making through structured analysis.
- Provide insights that help users understand risk, probability, and scenarios.
- Guide users toward disciplined, system-based investing.

Product rule (critical):
- AI ADVISOR only provides action-oriented guidance (buy/sell considerations)
  for stocks that are included in the official "Buysell Signal" list
  within the AI ADVISOR application.
- For all other stocks, AI ADVISOR may analyze and explain,
  but must NOT suggest or imply any investment action.

Core principles:
1. You do NOT provide direct buy/sell commands outside the Buysell Signal list.
2. You do NOT promise profits or guaranteed outcomes.
3. You do NOT encourage speculation, gambling, or impulsive behavior.
4. You prioritize capital protection, risk management, and discipline.
5. You clearly distinguish between:
   - Analysis-only stocks
   - System-approved Buysell Signal stocks

Behavior rules by stock type:

A. If the stock IS in the "Buysell Signal" list:
- You may discuss:
  - Signal status (trend, momentum, valuation context)
  - Risk conditions and invalidation scenarios
  - Position sizing considerations (conceptual, not numeric)
- You must still avoid explicit trade commands or price targets.
- You must emphasize that signals are system-based, not guarantees.

B. If the stock is NOT in the "Buysell Signal" list:
- You may:
  - Analyze fundamentals, trends, and risks
  - Explain why the stock may or may not fit certain strategies
- You must:
  - Clearly state that the stock is NOT in the Buysell Signal system
  - Avoid any form of recommendation, suggestion, or implied action
  - Redirect the user toward the Buysell Signal list if they seek action

Mandatory phrasing for non-signal stocks:
- Explicitly include a sentence equivalent to:
  "This stock is currently not part of the AI ADVISOR Buysell Signal system.
   Therefore, the following analysis is for understanding only,
   not for action guidance."

Response style:
- Professional, disciplined, and neutral.
- No hype, no emotional language, no persuasive tone.
- Concise by default; expand only if explicitly requested.
- RESPOND IN VIETNAMESE unless user writes in English.

Default output structure:

For Buysell Signal stocks:
1. Signal context summary
2. Supporting analysis
3. Risk & invalidation conditions
4. System-based considerations (not advice)

For non-signal stocks:
1. Analysis summary
2. Key factors & risks
3. Why it is outside the Buysell Signal scope
4. What type of stock typically qualifies for the system (educational)

User expectation management:
- Clearly state that AI ADVISOR supports decision-making,
  but final responsibility belongs to the user.
- Emphasize that the Buysell Signal list is the only source
  of system-approved actionable guidance.

If user pushes for action on non-signal stocks:
- Politely refuse.
- Reframe toward analysis or suggest checking the Buysell Signal list.

If user intent is unclear:
- Ask ONE clarifying question only.

Always act as a disciplined, system-driven investment advisor,
not a trader, promoter, or discretionary stock picker.

CRITICAL: Help users control FOMO (fear of missing out) and PANIC SELLING by:
- Reminding them of their investment plan and system rules
- Encouraging rational analysis over emotional reactions
- Pointing out when market behavior is driven by emotion vs fundamentals
- Supporting disciplined decision-making based on data, not fear or greed
"""

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
    user_id = Column(String(100), nullable=False)
    ticker = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CashPosition(Base):
    __tablename__ = 'cash_positions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, unique=True)
    cash_amount = Column(Float, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ChatHistory(Base):
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    portfolio_context = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def load_eod_prices():
    """Load EOD prices from file"""
    global PRICES_CACHE, CACHE_LOADED
    
    if not os.path.exists(EOD_FILE):
        print(f"⚠️ EOD file not found: {EOD_FILE}")
        PRICES_CACHE = {}
        CACHE_LOADED = True
        return False
    
    try:
        with open(EOD_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        PRICES_CACHE = data.get('prices', {})
        print(f"✅ Loaded {len(PRICES_CACHE)} prices from EOD file")
        CACHE_LOADED = True
        return True
        
    except Exception as e:
        print(f"❌ Error loading EOD file: {e}")
        PRICES_CACHE = {}
        CACHE_LOADED = True
        return False


def get_current_price(ticker):
    """Get current price for ticker from EOD file"""
    global PRICES_CACHE, CACHE_LOADED
    
    if not CACHE_LOADED:
        load_eod_prices()
    
    ticker = ticker.upper().strip()
    
    if ticker in PRICES_CACHE:
        price_data = PRICES_CACHE[ticker]
        return price_data.get('price')
    
    return None


def get_portfolio_context(user_id):
    """Get portfolio context with P&L"""
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        cash = cash_pos.cash_amount if cash_pos else 0
        
        signals = session.query(Signal).all()
        signal_tickers = set([s.ticker for s in signals])
        
        if not portfolios and cash == 0:
            return "Danh mục: Trống", signal_tickers
        
        context = "DANH MỤC ĐẦU TƯ:\n\n"
        
        if portfolios:
            context += "CỔ PHIẾU:\n"
            total_cost = 0
            total_value = 0
            
            for p in portfolios:
                cost = p.quantity * p.avg_price
                total_cost += cost
                
                current_price = get_current_price(p.ticker)
                if not current_price:
                    current_price = p.avg_price
                
                current_value = p.quantity * current_price
                total_value += current_value
                
                pl = current_value - cost
                pl_pct = (pl / cost * 100) if cost > 0 else 0
                
                in_signal = "✅ [IN BUYSELL SIGNAL]" if p.ticker in signal_tickers else "⚠️ [NOT IN SIGNAL LIST]"
                
                context += f"- {p.ticker} {in_signal}: {p.quantity} CP @ {p.avg_price:,.0f} VND\n"
                context += f"  Giá hiện tại: {current_price:,.0f} VND\n"
                context += f"  P&L: {pl:+,.0f} VND ({pl_pct:+.1f}%)\n"
            
            context += f"\nTổng giá trị CP: {total_value:,.0f} VND\n"
            context += f"Lãi/Lỗ: {total_value - total_cost:+,.0f} VND\n"
        
        if cash > 0:
            context += f"\nTIỀN MẶT: {cash:,.0f} VND\n"
        
        total_assets = (total_value if portfolios else 0) + cash
        if total_assets > 0:
            stock_pct = ((total_value if portfolios else 0) / total_assets * 100)
            cash_pct = (cash / total_assets * 100)
            context += f"\nTỔNG TÀI SẢN: {total_assets:,.0f} VND\n"
            context += f"Phân bổ: {stock_pct:.1f}% CP / {cash_pct:.1f}% TM\n"
        
        context += f"\n\nCỔ PHIẾU TRONG BUYSELL SIGNAL SYSTEM:\n"
        context += ", ".join(sorted(signal_tickers)) if signal_tickers else "Chưa có signal nào"
        
        return context, signal_tickers
        
    except Exception as e:
        print(f"Error: {e}")
        return "Danh mục: Lỗi", set()
    finally:
        session.close()


def chat_with_gpt(message, portfolio_context, signal_tickers):
    """Chat with OpenAI using strict system prompt"""
    if not openai_client:
        return "Xin lỗi, AI chưa được cấu hình."
    
    try:
        system_message = AI_SYSTEM_PROMPT + f"\n\n{portfolio_context}"
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Xin lỗi, AI không phản hồi được."


# ========================================================================
# API ROUTES - BASIC
# ========================================================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'AI Advisor Backend v3.3',
        'version': '3.3 (Strict AI Prompt) - FIXED',
        'features': ['signals', 'portfolio', 'cash', 'eod_prices', 'chat_ai_strict', 'fomo_control', 'automation'],
        'eod_file': {
            'exists': os.path.exists(EOD_FILE),
            'tickers': len(PRICES_CACHE)
        },
        'status': 'running'
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'openai': openai_client is not None,
        'eod_file_loaded': CACHE_LOADED,
        'eod_tickers': len(PRICES_CACHE),
        'timestamp': datetime.now().isoformat()
    })


# ========================================================================
# SIGNALS ENDPOINTS
# ========================================================================

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


# ========================================================================
# AUTOMATION ENDPOINTS (GitHub Actions)
# ========================================================================

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """
    Trigger signal scanner manually
    Used by GitHub Actions automation
    """
    try:
        scanner_path = os.path.join(
            os.path.dirname(__file__), 
            'scripts', 
            'daily_signal_scanner_eod.py'
        )
        
        if not os.path.exists(scanner_path):
            return jsonify({
                'success': False,
                'error': f'Scanner not found at {scanner_path}'
            }), 404
        
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
    """Check scan status and signal count"""
    try:
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
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM signals 
            WHERE date = date('now')
        """)
        today_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM signals")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(created_at) FROM signals")
        last_scan = cursor.fetchone()[0]
        
        conn.close()
        
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


# ========================================================================
# PORTFOLIO ENDPOINTS
# ========================================================================

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio with P&L from EOD file"""
    user_id = request.args.get('user_id', '1')
    
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        cash = cash_pos.cash_amount if cash_pos else 0
        
        portfolio_data = []
        for p in portfolios:
            current_price = get_current_price(p.ticker)
            if not current_price:
                current_price = p.avg_price
            
            cost = p.quantity * p.avg_price
            current_value = p.quantity * current_price
            pl_amount = current_value - cost
            pl_pct = (pl_amount / cost * 100) if cost > 0 else 0
            
            portfolio_data.append({
                'id': p.id,
                'ticker': p.ticker,
                'quantity': p.quantity,
                'avg_price': p.avg_price,
                'current_price': current_price,
                'cost': cost,
                'current_value': current_value,
                'pl_amount': pl_amount,
                'pl_pct': pl_pct,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'portfolio': portfolio_data,
            'cash': cash
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/portfolio', methods=['POST'])
def add_portfolio():
    """Add stock to portfolio"""
    data = request.json
    
    user_id = data.get('user_id', 1)
    ticker = data.get('ticker', '').upper().strip()
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0))
    
    if not ticker or quantity <= 0 or price <= 0:
        return jsonify({'success': False, 'error': 'Invalid input'}), 400
    
    session = Session()
    try:
        existing = session.query(Portfolio).filter_by(
            user_id=user_id,
            ticker=ticker
        ).first()
        
        if existing:
            new_qty = existing.quantity + quantity
            new_value = (existing.quantity * existing.avg_price) + (quantity * price)
            existing.quantity = new_qty
            existing.avg_price = new_value / new_qty
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
    """Delete stock"""
    user_id = request.args.get('user_id', '1')
    
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


# ========================================================================
# CASH & CHAT ENDPOINTS
# ========================================================================

@app.route('/api/cash', methods=['GET'])
def get_cash():
    user_id = request.args.get('user_id', '1')
    session = Session()
    try:
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        return jsonify({'success': True, 'cash': cash_pos.cash_amount if cash_pos else 0})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/cash', methods=['POST'])
def update_cash():
    data = request.json
    user_id = data.get('user_id', 1)
    cash_amount = float(data.get('cash', 0))
    
    if cash_amount < 0:
        return jsonify({'success': False, 'error': 'Cash cannot be negative'}), 400
    
    session = Session()
    try:
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        
        if cash_pos:
            cash_pos.cash_amount = cash_amount
            cash_pos.updated_at = datetime.now()
        else:
            cash_pos = CashPosition(user_id=user_id, cash_amount=cash_amount)
            session.add(cash_pos)
        
        session.commit()
        return jsonify({'success': True, 'message': 'Cash updated', 'cash': cash_amount})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with AI using strict system prompt"""
    data = request.json
    user_id = data.get('user_id', 1)
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Message required'}), 400
    
    session = Session()
    try:
        portfolio_context, signal_tickers = get_portfolio_context(user_id)
        ai_response = chat_with_gpt(message, portfolio_context, signal_tickers)
        
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
            'response': 'Xin lỗi, có lỗi xảy ra.'
        }), 500
    finally:
        session.close()


@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    user_id = request.args.get('user_id', '1')
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


# ========================================================================
# STOCK PRICE ENDPOINTS (Real-time price fetching)
# ========================================================================

@app.route('/api/stock/current-price', methods=['GET'])
def get_stock_price_endpoint():
    """Get current/latest EOD price for a stock"""
    ticker = request.args.get('ticker')
    
    if not ticker:
        return jsonify({
            'success': False,
            'error': 'Ticker required'
        }), 400
    
    ticker = ticker.upper()
    
    try:
        stock_api = Vnstock()
        stock = stock_api.stock(symbol=ticker, source='VCI')
        
        # Try intraday first
        try:
            intraday = stock.quote.intraday(symbol=ticker, page_size=1)
            if not intraday.empty:
                price = float(intraday['close'].iloc[-1])
                return jsonify({
                    'success': True,
                    'price': price,
                    'source': 'intraday',
                    'timestamp': datetime.now().isoformat(),
                    'ticker': ticker
                })
        except Exception as e:
            print(f"Intraday failed for {ticker}: {e}")
        
        # Fallback to EOD
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        
        daily = stock.quote.history(symbol=ticker, start=yesterday, end=today)
        
        if not daily.empty:
            price = float(daily['close'].iloc[-1])
            trade_date = daily.index[-1].strftime('%Y-%m-%d') if hasattr(daily.index[-1], 'strftime') else 'recent'
            
            return jsonify({
                'success': True,
                'price': price,
                'source': 'eod',
                'timestamp': datetime.now().isoformat(),
                'ticker': ticker,
                'trade_date': trade_date
            })
        
        return jsonify({
            'success': False,
            'error': f'No price data found for {ticker}',
            'ticker': ticker
        }), 404
        
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'ticker': ticker
        }), 500


@app.route('/api/stock/batch-prices', methods=['POST'])
def get_batch_prices():
    """Get prices for multiple stocks at once"""
    data = request.json
    tickers = data.get('tickers', [])
    
    if not tickers or not isinstance(tickers, list):
        return jsonify({
            'success': False,
            'error': 'Tickers array required'
        }), 400
    
    stock_api = Vnstock()
    prices = {}
    failed = []
    
    for ticker in tickers:
        try:
            stock = stock_api.stock(symbol=ticker.upper(), source='VCI')
            
            # Try intraday first
            try:
                intraday = stock.quote.intraday(symbol=ticker.upper(), page_size=1)
                if not intraday.empty:
                    prices[ticker.upper()] = float(intraday['close'].iloc[-1])
                    continue
            except:
                pass
            
            # Fallback to EOD
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            
            daily = stock.quote.history(symbol=ticker.upper(), start=yesterday, end=today)
            
            if not daily.empty:
                prices[ticker.upper()] = float(daily['close'].iloc[-1])
            else:
                failed.append(ticker.upper())
                
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            failed.append(ticker.upper())
    
    return jsonify({
        'success': True,
        'prices': prices,
        'failed': failed,
        'timestamp': datetime.now().isoformat()
    })


# ========================================================================
# UTILITY ENDPOINTS
# ========================================================================

@app.route('/api/eod/status', methods=['GET'])
def eod_status():
    """Get EOD file status"""
    file_exists = os.path.exists(EOD_FILE)
    file_age_days = None
    last_modified = None
    
    if file_exists:
        file_time = datetime.fromtimestamp(os.path.getmtime(EOD_FILE))
        file_age_days = (datetime.now() - file_time).days
        last_modified = file_time.isoformat()
    
    return jsonify({
        'success': True,
        'file_exists': file_exists,
        'tickers_count': len(PRICES_CACHE),
        'file_age_days': file_age_days,
        'last_modified': last_modified,
        'needs_refresh': file_age_days > 5 if file_age_days is not None else True
    })


@app.route('/api/migrate', methods=['POST'])
def migrate():
    try:
        Base.metadata.create_all(engine)
        return jsonify({
            'success': True,
            'message': 'Migration successful',
            'tables': ['signals', 'portfolios', 'cash_positions', 'chat_history']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# APPLICATION STARTUP
# ========================================================================

if __name__ == '__main__':
    # Initialize database
    try:
        print("\n🚀 Starting AI Advisor Backend v3.3 - FIXED...")
        Base.metadata.create_all(engine)
        print("✅ Database initialized")
        
        # Load EOD prices
        load_eod_prices()
        
    except Exception as e:
        print(f"⚠️ Warning: {e}")
    
    # Get port from environment (CRITICAL for Render!)
    port = int(os.getenv('PORT', 10000))
    
    print(f"\n{'='*70}")
    print("🚀 AI ADVISOR BACKEND v3.3 - FIXED VERSION")
    print(f"{'='*70}")
    print(f"AI: {'✅ GPT-4o-mini (Strict Rules)' if openai_client else '❌ Not configured'}")
    print(f"EOD File: {'✅ Loaded' if CACHE_LOADED and PRICES_CACHE else '⚠️ Not found'}")
    print(f"Tickers: {len(PRICES_CACHE)}")
    print(f"Database: {DATABASE_URL}")
    print(f"Host: 0.0.0.0 (Render-ready)")
    print(f"Port: {port}")
    print(f"{'='*70}\n")
    
    # CRITICAL: Bind to 0.0.0.0 and use PORT from environment!
    app.run(debug=False, host='0.0.0.0', port=port)
