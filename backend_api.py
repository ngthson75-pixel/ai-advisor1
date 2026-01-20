#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - BACKEND v3.3
WITH STRICT AI SYSTEM PROMPT FOR INVESTMENT GUIDANCE
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import json
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SELL Signal Integration
from backend_sell_api import register_sell_routes

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Register SELL Signal Routes
register_sell_routes(app)
print("✅ SELL signal routes registered")

# Configure OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI configured")
else:
    print("⚠️ OPENAI_API_KEY not set")
    openai_client = None

# Database
Base = declarative_base()

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# EOD file settings
EOD_FILE = 'latest_prices_all.json'
PRICES_CACHE = {}
CACHE_LOADED = False


# ========================================================================
# AI SYSTEM PROMPT - STRICT INVESTMENT GUIDANCE RULES
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
    user_id = Column(Integer, nullable=False)
    ticker = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CashPosition(Base):
    __tablename__ = 'cash_positions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)
    cash_amount = Column(Float, nullable=False, default=0)
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
# EOD FILE MANAGEMENT
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


# ========================================================================
# PORTFOLIO CONTEXT & AI CHAT
# ========================================================================

def get_portfolio_context(user_id):
    """Get portfolio context with P&L"""
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        cash = cash_pos.cash_amount if cash_pos else 0
        
        # Get list of stocks in Buysell Signal system
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
                
                # Mark if stock is in Buysell Signal system
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
        # Build system message with portfolio context
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
# API ROUTES
# ========================================================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'AI Advisor Backend v3.3',
        'version': '3.3 (Strict AI Prompt)',
        'features': ['signals', 'portfolio', 'cash', 'eod_prices', 'chat_ai_strict', 'fomo_control'],
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


@app.route('/api/scan', methods=['POST'])
def scan_signals():
    """Scan for new signals (mock)"""
    try:
        session = Session()
        
        sample_tickers = ['VCB', 'VHM', 'HPG', 'TCB']
        created_count = 0
        
        for ticker in sample_tickers:
            today = datetime.now().strftime('%Y-%m-%d')
            existing = session.query(Signal).filter(
                Signal.ticker == ticker,
                Signal.date == today
            ).first()
            
            if existing:
                continue
            
            price = get_current_price(ticker)
            if not price:
                price = 50000
            
            signal = Signal(
                ticker=ticker,
                strategy='PULLBACK',
                entry_price=price,
                stop_loss=price * 0.95,
                take_profit=price * 1.08,
                risk_reward=1.6,
                strength=75,
                stock_type='Blue Chip',
                rsi=65,
                date=today,
                action='BUY'
            )
            session.add(signal)
            created_count += 1
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Quét hoàn tất! Tìm thấy {created_count} tín hiệu mới.',
            'signals_created': created_count
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ========================================================================
# PORTFOLIO ENDPOINTS
# ========================================================================

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio with P&L from EOD file"""
    user_id = request.args.get('user_id', 1, type=int)
    
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


# ========================================================================
# CASH & CHAT ENDPOINTS
# ========================================================================

@app.route('/api/cash', methods=['GET'])
def get_cash():
    user_id = request.args.get('user_id', 1, type=int)
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


@app.route('/api/eod/status', methods=['GET'])
def eod_status():
    """Get EOD file status"""
    from datetime import timedelta
    
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
# STARTUP
# ========================================================================

try:
    print("\n🚀 Starting AI Advisor Backend v3.3...")
    Base.metadata.create_all(engine)
    print("✅ Database initialized")
    
    load_eod_prices()
    
except Exception as e:
    print(f"⚠️ Warning: {e}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADDITIONAL API ENDPOINTS FOR DATABASE MANAGEMENT
Add these to backend_api.py
"""

from flask import jsonify, request
from datetime import datetime
from sqlalchemy import func

# ============================================================================
# DEDUPLICATE SIGNALS ENDPOINT
# ============================================================================

@app.route('/api/signals/deduplicate', methods=['POST'])
def deduplicate_signals():
    """
    Remove duplicate BUY signals
    Keep signal with highest score for each ticker+date combination
    """
    session = Session()
    
    try:
        # Find duplicate groups
        duplicates = session.query(
            Signal.ticker,
            Signal.date,
            func.count(Signal.id).label('count')
        ).filter(
            Signal.action == 'BUY'
        ).group_by(
            Signal.ticker,
            Signal.date
        ).having(
            func.count(Signal.id) > 1
        ).all()
        
        removed = 0
        details = []
        
        for ticker, date, count in duplicates:
            # Get all signals for this ticker+date, ordered by strength DESC
            signals = session.query(Signal).filter_by(
                ticker=ticker,
                date=date,
                action='BUY'
            ).order_by(
                Signal.strength.desc()
            ).all()
            
            # Keep first (highest score), delete rest
            kept_signal = signals[0]
            for sig in signals[1:]:
                session.delete(sig)
                removed += 1
            
            details.append({
                'ticker': ticker,
                'date': date,
                'kept_score': kept_signal.strength,
                'removed': len(signals) - 1
            })
        
        session.commit()
        
        return jsonify({
            'success': True,
            'removed': removed,
            'duplicate_groups': len(duplicates),
            'details': details,
            'message': f'Removed {removed} duplicate signals from {len(duplicates)} groups'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# UPDATE STOCK TYPES ENDPOINT
# ============================================================================

@app.route('/api/signals/update-stock-types', methods=['POST'])
def update_stock_types():
    """
    Update stock_type classification for all signals
    """
    session = Session()
    
    try:
        # Define stock classifications
        blue_chips = [
            'VCB', 'VHM', 'VNM', 'VIC', 'GAS', 'MSN', 'MBB', 'TCB', 'VPB', 'HPG',
            'BID', 'CTG', 'FPT', 'PLX', 'SAB', 'VRE', 'VJC', 'GVR', 'POW', 'ACB',
            'HDB', 'MWG', 'SSI', 'TPB', 'VHC', 'NVL', 'KDH', 'PDR', 'STB', 'BCM',
            'BVH', 'VCI', 'DHG', 'PNJ', 'REE'
        ]
        
        mid_caps = [
            'DGC', 'DPM', 'FRT', 'GMD', 'HAG', 'HNG', 'HSG', 'HT1', 'KBC',
            'LGC', 'NT2', 'NVT', 'PC1', 'PET', 'PPC', 'PVD', 'PVT', 'QCG',
            'SBT', 'SCS', 'SZC', 'TLG', 'VCS', 'VGC', 'VHG', 'VPI'
        ]
        
        # Update Blue Chip
        blue_updated = 0
        for ticker in blue_chips:
            result = session.query(Signal).filter(
                Signal.ticker == ticker
            ).update({
                'stock_type': 'Blue Chip'
            })
            blue_updated += result
        
        # Update Mid Cap
        mid_updated = 0
        for ticker in mid_caps:
            result = session.query(Signal).filter(
                Signal.ticker == ticker,
                Signal.ticker.notin_(blue_chips)
            ).update({
                'stock_type': 'Mid Cap'
            })
            mid_updated += result
        
        # Update Penny (everything else)
        penny_updated = session.query(Signal).filter(
            Signal.ticker.notin_(blue_chips + mid_caps)
        ).update({
            'stock_type': 'Penny'
        }, synchronize_session=False)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'updated': {
                'blue_chip': blue_updated,
                'mid_cap': mid_updated,
                'penny': penny_updated,
                'total': blue_updated + mid_updated + penny_updated
            },
            'message': f'Updated {blue_updated + mid_updated + penny_updated} signals'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# CLEAR OLD SIGNALS ENDPOINT
# ============================================================================

@app.route('/api/signals/clear-old', methods=['POST'])
def clear_old_signals():
    """
    Delete signals older than X days
    Default: 30 days
    """
    session = Session()
    
    try:
        # Get days parameter (default 30)
        days = request.json.get('days', 30) if request.is_json else 30
        
        # Calculate cutoff date
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Delete old signals
        deleted = session.query(Signal).filter(
            Signal.date < cutoff_date
        ).delete()
        
        session.commit()
        
        return jsonify({
            'success': True,
            'deleted': deleted,
            'cutoff_date': cutoff_date,
            'message': f'Deleted {deleted} signals older than {cutoff_date}'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# DATABASE STATS ENDPOINT
# ============================================================================

@app.route('/api/signals/stats', methods=['GET'])
def get_signals_stats():
    """
    Get database statistics
    """
    session = Session()
    
    try:
        # Total signals
        total = session.query(Signal).count()
        
        # By action
        buy_count = session.query(Signal).filter_by(action='BUY').count()
        sell_count = session.query(Signal).filter_by(action='SELL').count()
        
        # By stock type
        stock_types = session.query(
            Signal.stock_type,
            func.count(Signal.id)
        ).filter(
            Signal.action == 'BUY'
        ).group_by(
            Signal.stock_type
        ).all()
        
        # By date
        dates = session.query(
            Signal.date,
            func.count(Signal.id)
        ).filter(
            Signal.action == 'BUY'
        ).group_by(
            Signal.date
        ).order_by(
            Signal.date.desc()
        ).limit(10).all()
        
        # Date range
        min_date = session.query(func.min(Signal.date)).scalar()
        max_date = session.query(func.max(Signal.date)).scalar()
        
        # Duplicates check
        duplicates = session.query(
            Signal.ticker,
            Signal.date,
            func.count(Signal.id).label('count')
        ).filter(
            Signal.action == 'BUY'
        ).group_by(
            Signal.ticker,
            Signal.date
        ).having(
            func.count(Signal.id) > 1
        ).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_signals': total,
                'buy_signals': buy_count,
                'sell_signals': sell_count,
                'stock_types': {st: count for st, count in stock_types},
                'date_range': {
                    'min': min_date,
                    'max': max_date
                },
                'recent_dates': [{'date': d, 'count': c} for d, c in dates],
                'duplicates': len(duplicates),
                'has_duplicates': len(duplicates) > 0
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
"""
# Deduplicate signals
curl -X POST https://ai-advisor1-backend.onrender.com/api/signals/deduplicate

# Update stock types
curl -X POST https://ai-advisor1-backend.onrender.com/api/signals/update-stock-types

# Clear signals older than 30 days
curl -X POST https://ai-advisor1-backend.onrender.com/api/signals/clear-old \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'

# Get stats
curl https://ai-advisor1-backend.onrender.com/api/signals/stats
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMPORT SIGNAL ENDPOINT
Add this to backend_api.py
"""

@app.route('/api/signals/import', methods=['POST'])
def import_signal():
    """
    Import a single signal from external source
    """
    session = Session()
    
    try:
        data = request.json
        
        # Validate required fields
        required = ['ticker', 'strategy', 'entry_price', 'stop_loss', 'take_profit', 'date']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        # Check if signal already exists
        existing = session.query(Signal).filter_by(
            ticker=data['ticker'],
            date=data['date'],
            action=data.get('action', 'BUY')
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Signal already exists',
                'existing_id': existing.id
            }), 409
        
        # Create new signal - ONLY with fields that exist in production
        signal = Signal(
            ticker=data['ticker'],
            strategy=data['strategy'],
            entry_price=data['entry_price'],
            stop_loss=data['stop_loss'],
            take_profit=data['take_profit'],
            risk_reward=data.get('risk_reward', 0),
            strength=data.get('strength', 0),
            stock_type=data.get('stock_type', 'Penny'),
            rsi=data.get('rsi', 50),
            date=data['date'],
            action=data.get('action', 'BUY')
            # REMOVED: is_priority, signal_status, quantity_sold
        )
        
        session.add(signal)
        session.commit()
        
        return jsonify({
            'success': True,
            'signal_id': signal.id,
            'ticker': signal.ticker,
            'message': 'Signal imported successfully'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/signals/import-batch', methods=['POST'])
def import_signals_batch():
    """
    Import multiple signals at once
    """
    session = Session()
    
    try:
        data = request.json
        signals_data = data.get('signals', [])
        
        if not signals_data:
            return jsonify({'success': False, 'error': 'No signals provided'}), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        for sig_data in signals_data:
            try:
                # Check if exists
                existing = session.query(Signal).filter_by(
                    ticker=sig_data['ticker'],
                    date=sig_data['date'],
                    action=sig_data.get('action', 'BUY')
                ).first()
                
                if existing:
                    error_count += 1
                    errors.append(f"{sig_data['ticker']}: Already exists")
                    continue
                
                # Create signal
                signal = Signal(
                    ticker=sig_data['ticker'],
                    strategy=sig_data['strategy'],
                    entry_price=sig_data['entry_price'],
                    stop_loss=sig_data['stop_loss'],
                    take_profit=sig_data['take_profit'],
                    risk_reward=sig_data.get('risk_reward', 0),
                    strength=sig_data.get('strength', 0),
                    is_priority=sig_data.get('is_priority', 0),
                    stock_type=sig_data.get('stock_type', 'Penny'),
                    rsi=sig_data.get('rsi', 50),
                    date=sig_data['date'],
                    action=sig_data.get('action', 'BUY'),
                    signal_status=sig_data.get('signal_status', 'ACTIVE'),
                    quantity_sold=sig_data.get('quantity_sold', 0)
                )
                
                session.add(signal)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"{sig_data.get('ticker', 'Unknown')}: {str(e)}")
        
        session.commit()
        
        return jsonify({
            'success': True,
            'imported': success_count,
            'errors': error_count,
            'error_details': errors[:10],  # Max 10 error messages
            'message': f'Imported {success_count} signals, {error_count} errors'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print(f"\n{'='*70}")
    print("🚀 AI ADVISOR BACKEND v3.3 - STRICT AI PROMPT")
    print(f"{'='*70}")
    print(f"AI: {'✅ GPT-4o-mini (Strict Rules)' if openai_client else '❌ Not configured'}")
    print(f"EOD File: {'✅ Loaded' if CACHE_LOADED and PRICES_CACHE else '⚠️ Not found'}")
    print(f"Tickers: {len(PRICES_CACHE)}")
    print(f"Database: {DATABASE_URL}")
    print(f"Port: {port}")
    print(f"{'='*70}\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
