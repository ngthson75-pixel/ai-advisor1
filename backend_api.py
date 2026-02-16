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
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func, Boolean, and_, not_, exists
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
print("âœ… SELL signal routes registered")

# ========================================================================
# CONFIGURATION
# ========================================================================

# Configure OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("âœ… OpenAI configured")
else:
    print("âš ï¸ OPENAI_API_KEY not set")
    openai_client = None

# ========================================================================
# DATABASE CONFIGURATION - ENVIRONMENT-AWARE ðŸŒ
# ========================================================================

ENVIRONMENT = os.getenv('ENVIRONMENT', 'production').lower()
print(f"\n{'='*70}")
print(f"ðŸŒ Environment: {ENVIRONMENT.upper()}")
print(f"{'='*70}")

# Choose database based on environment
if ENVIRONMENT == 'staging':
    DATABASE_URL = os.getenv('DATABASE_URL_STAGING') or os.getenv('DATABASE_URL', 'sqlite:///signals.db')
    print("ðŸ“Š Using STAGING database (Supabase)")
else:
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
    print("ðŸ“Š Using PRODUCTION database (Render Postgres)")

# Fix PostgreSQL URL for psycopg3 (Python 3.13 compatible)
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
    print(f"âœ… Using PostgreSQL with psycopg (v3) driver")

# Print database URL (first 50 chars for security)
db_url_display = DATABASE_URL[:50] + "..." if len(DATABASE_URL) > 50 else DATABASE_URL
print(f"ðŸ”— Database URL: {db_url_display}")
print(f"{'='*70}\n")

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
    
    # Signal code tracking (Hybrid FIFO) - PATCHED
    signal_code = Column(String(50), unique=True)  # e.g., VCB-1001
    buy_signal_code = Column(String(50))  # For SELL signals to link to BUY


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

class TickerBlacklist(Base):
    __tablename__ = 'ticker_blacklist'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False)
    reason = Column(String(255))
    added_by = Column(String(50))
    added_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

class MarketRisk(Base):
    __tablename__ = 'market_risk'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(20), nullable=False, unique=True)
    market_mode = Column(String(20), nullable=False)
    mode_label = Column(String(50))
    risk_score = Column(Integer)
    allocation = Column(Integer)
    description = Column(Text)
    factors_json = Column(Text)
    vnindex_value = Column(Float)
    raw_scores_json = Column(Text)
    analyzed_at = Column(DateTime, default=datetime.now)

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def load_eod_prices():
    """Load EOD prices from file"""
    global PRICES_CACHE, CACHE_LOADED
    
    if not os.path.exists(EOD_FILE):
        print(f"âš ï¸ EOD file not found: {EOD_FILE}")
        PRICES_CACHE = {}
        CACHE_LOADED = True
        return False
    
    try:
        with open(EOD_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        PRICES_CACHE = data.get('prices', {})
        print(f"âœ… Loaded {len(PRICES_CACHE)} prices from EOD file")
        CACHE_LOADED = True
        return True
        
    except Exception as e:
        print(f"âŒ Error loading EOD file: {e}")
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
            return "Danh má»¥c: Trá»‘ng", signal_tickers
        
        context = "DANH Má»¤C Äáº¦U TÆ¯:\n\n"
        
        if portfolios:
            context += "Cá»” PHIáº¾U:\n"
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
                
                in_signal = "âœ… [IN BUYSELL SIGNAL]" if p.ticker in signal_tickers else "âš ï¸ [NOT IN SIGNAL LIST]"
                
                context += f"- {p.ticker} {in_signal}: {p.quantity} CP @ {p.avg_price:,.0f} VND\n"
                context += f"  GiÃ¡ hiá»‡n táº¡i: {current_price:,.0f} VND\n"
                context += f"  P&L: {pl:+,.0f} VND ({pl_pct:+.1f}%)\n"
            
            context += f"\nTá»•ng giÃ¡ trá»‹ CP: {total_value:,.0f} VND\n"
            context += f"LÃ£i/Lá»—: {total_value - total_cost:+,.0f} VND\n"
        
        if cash > 0:
            context += f"\nTIá»€N Máº¶T: {cash:,.0f} VND\n"
        
        total_assets = (total_value if portfolios else 0) + cash
        if total_assets > 0:
            stock_pct = ((total_value if portfolios else 0) / total_assets * 100)
            cash_pct = (cash / total_assets * 100)
            context += f"\nTá»”NG TÃ€I Sáº¢N: {total_assets:,.0f} VND\n"
            context += f"PhÃ¢n bá»•: {stock_pct:.1f}% CP / {cash_pct:.1f}% TM\n"
        
        context += f"\n\nCá»” PHIáº¾U TRONG BUYSELL SIGNAL SYSTEM:\n"
        context += ", ".join(sorted(signal_tickers)) if signal_tickers else "ChÆ°a cÃ³ signal nÃ o"
        
        return context, signal_tickers
        
    except Exception as e:
        print(f"Error: {e}")
        return "Danh má»¥c: Lá»—i", set()
    finally:
        session.close()


def chat_with_gpt(message, portfolio_context, signal_tickers):
    """Chat with OpenAI using strict system prompt"""
    if not openai_client:
        return "Xin lá»—i, AI chÆ°a Ä‘Æ°á»£c cáº¥u hÃ¬nh."
    
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
        return "Xin lá»—i, AI khÃ´ng pháº£n há»“i Ä‘Æ°á»£c."


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

@app.route('/api/signals', methods=['GET', 'POST'])
def signals_endpoint():
    """
    GET: Retrieve all signals
    POST: Create new signal (for push script)
    """
    
    if request.method == 'GET':
        # GET: Return all signals with rounding and deduplication
        session = Session()
        try:
            signals = session.query(Signal)\
              .filter(
              ~exists().where(
                and_(
                TickerBlacklist.ticker == Signal.ticker,
                TickerBlacklist.is_active == True
                     )
                  )
               )\
              .order_by(Signal.created_at.desc())\
              .all()
            
            # Build signals with rounded prices
            signals_data = []
            for s in signals:
                signals_data.append({
                    'id': s.id,
                    'ticker': s.ticker,
                    'code': s.ticker,
                    'strategy': s.strategy,
                    'entry_price': round(s.entry_price / 100) * 100,  # Round to nearest 100 VND
                    'stop_loss': round(s.stop_loss / 100) * 100,      # Round to nearest 100 VND
                    'take_profit': round(s.take_profit / 100) * 100,  # Round to nearest 100 VND
                    'risk_reward': round(s.risk_reward, 2) if s.risk_reward else None,
                    'strength': s.strength or 0,
                    'stock_type': s.stock_type,
                    'rsi': round(s.rsi, 1) if s.rsi else None,
                    'date': s.date or (s.created_at.strftime('%Y-%m-%d') if s.created_at else None),
                    'action': s.action,
                    'created_at': s.created_at.isoformat() if s.created_at else None,
                    # Signal code fields (NEW)
                    'signal_code': s.signal_code,
                    'buy_signal_code': s.buy_signal_code
                })
            
            # Deduplicate: Keep BEST signal per ticker per date (highest strength)
            seen = {}  # Track: ticker_date â†’ signal
            deduplicated = []
            
            for signal in signals_data:
                key = f"{signal['ticker']}_{signal['date']}"
                
                if key not in seen:
                    # First signal for this ticker+date â†’ Keep it
                    seen[key] = signal
                    deduplicated.append(signal)
                else:
                    # Duplicate found â†’ Keep signal with HIGHER strength
                    existing_strength = seen[key].get('strength', 0)
                    new_strength = signal.get('strength', 0)
                    
                    if new_strength > existing_strength:
                        # Replace with better signal
                        deduplicated.remove(seen[key])
                        seen[key] = signal
                        deduplicated.append(signal)
            
            return jsonify({
                'success': True,
                'signals': deduplicated,
                'count': len(deduplicated),
                'total_before_dedup': len(signals_data)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()
    
    elif request.method == 'POST':
        # POST: Create new signal (NEW - for push script)
        data = request.json
        
        # Validate request has data
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['ticker', 'entry_price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False, 
                    'error': f'Missing required field: {field}'
                }), 400
        
        session = Session()
        try:
            # Create new signal from push script data
            signal = Signal(
                ticker=data['ticker'],
                strategy=data.get('strategy'),
                entry_price=data['entry_price'],
                stop_loss=data.get('stop_loss'),
                take_profit=data.get('take_profit'),
                risk_reward=data.get('risk_reward'),
                strength=data.get('strength'),
                stock_type=data.get('stock_type'),
                rsi=data.get('rsi'),
                date=data.get('date'),
                action=data.get('action', 'BUY')
            )
            
            # Save to database
            session.add(signal)
            session.flush()  # Get ID
            
            # Generate signal_code for BUY
            if signal.action == 'BUY' and not signal.signal_code:
                signal.signal_code = f"{signal.ticker}-{signal.id}"
            
            session.commit()
            
            print(f"âœ… Signal created: {signal.ticker} ({signal.strategy}) - {signal.date}")
            
            return jsonify({
                'success': True,
                'id': signal.id,
                'signal_code': signal.signal_code,  # NEW
                'ticker': signal.ticker,
                'message': 'Signal created successfully'
            }), 201
            
        except Exception as e:
            session.rollback()
            print(f"âŒ Error creating signal: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()

# ========================================================================
# AUTOMATION ENDPOINTS (GitHub Actions)
# ========================================================================


# ========================================================================
# SIGNAL CODE ENDPOINTS (HYBRID FIFO) - NEW
# ========================================================================

@app.route('/api/signals/open-buys/<ticker>', methods=['GET'])
def get_open_buy_signals(ticker):
    """
    Get all open/partial BUY signals for a ticker
    Used in SELL form dropdown for manual signal selection
    """
    session = Session()
    try:
        ticker = ticker.upper().strip()
        
        # Get open/partial BUY signals, ordered by FIFO (oldest first)
        signals = session.query(Signal).filter(
            Signal.ticker == ticker,
            Signal.action == 'BUY'
        ).order_by(
            Signal.date.asc(),
            Signal.created_at.asc()
        ).all()
        
        result = []
        for s in signals:
            result.append({
                'id': s.id,
                'signal_code': s.signal_code,
                'ticker': s.ticker,
                'strategy': s.strategy,
                'entry_price': round(s.entry_price / 100) * 100,
                'date': s.date,
                'display_text': f"{s.signal_code or f'#{s.id}'} @ {round(s.entry_price/1000, 1)}k ({s.strategy})"
            })
        
        return jsonify({
            'success': True,
            'signals': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/signals/sell', methods=['POST'])
def create_sell_signal():
    """
    Create SELL signal with HYBRID approach:
    - If buy_signal_code provided → Use that specific signal (Manual)
    - If not provided → Auto-match oldest open signal (FIFO)
    
    Request body:
    {
        "ticker": "VCB",
        "sell_price": 95000,
        "sell_reason": "TAKE_PROFIT",  // or "STOP_LOSS", "MANUAL"
        "sell_pct": 100,  // Optional: 0-100, default 100
        "buy_signal_code": "VCB-1001"  // OPTIONAL - for manual selection
    }
    """
    session = Session()
    try:
        data = request.json
        
        ticker = data.get('ticker')
        sell_price = data.get('sell_price')
        sell_reason = data.get('sell_reason', 'MANUAL')
        sell_pct = data.get('sell_pct', 100)
        buy_signal_code = data.get('buy_signal_code')  # OPTIONAL
        
        # Validate
        if not ticker or not sell_price:
            return jsonify({'error': 'Missing ticker or sell_price'}), 400
        
        if sell_pct < 0 or sell_pct > 100:
            return jsonify({'error': 'sell_pct must be 0-100'}), 400
        
        ticker = ticker.upper().strip()
        
        # HYBRID APPROACH: Find BUY signal
        if buy_signal_code:
            # MANUAL: User specified signal code
            buy_signal = session.query(Signal).filter_by(
                signal_code=buy_signal_code,
                action='BUY'
            ).first()
            
            if not buy_signal:
                return jsonify({'error': f'Signal {buy_signal_code} not found'}), 404
            
            selection_method = 'manual'
        else:
            # AUTO FIFO: Find oldest open signal for this ticker
            buy_signal = session.query(Signal).filter(
                Signal.ticker == ticker,
                Signal.action == 'BUY'
            ).order_by(
                Signal.date.asc(),
                Signal.created_at.asc()
            ).first()
            
            if not buy_signal:
                return jsonify({'error': f'No BUY signal found for {ticker}'}), 404
            
            selection_method = 'auto_fifo'
        
        # Create SELL signal
        sell_signal = Signal(
            ticker=ticker,
            strategy=sell_reason,
            entry_price=buy_signal.entry_price,
            stop_loss=sell_price,
            take_profit=sell_price,
            risk_reward=0,
            strength=100 if sell_reason == 'STOP_LOSS' else 80,
            stock_type=buy_signal.stock_type,
            date=datetime.now().strftime('%Y-%m-%d'),
            action='SELL',
            buy_signal_code=buy_signal.signal_code  # Link to BUY signal
        )
        
        session.add(sell_signal)
        session.commit()
        
        return jsonify({
            'success': True,
            'selection_method': selection_method,
            'sell_signal': {
                'id': sell_signal.id,
                'ticker': ticker,
                'sell_price': sell_price,
                'sell_reason': sell_reason,
                'sell_pct': sell_pct
            },
            'buy_signal_linked': {
                'id': buy_signal.id,
                'signal_code': buy_signal.signal_code
            }
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger signal scanner + market risk analysis. Used by GitHub Actions automation."""
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

        import threading
        
        def run_market_risk_after_scan():
            """Wait for signal scan to finish, then run market risk"""
            import time
            time.sleep(60)  # Äá»£i signal scan cháº¡y 1 phÃºt
            
            try:
                from market_risk_analysis import run_market_analysis
                result = run_market_analysis()
                
                # Save to DB
                session = Session()
                today = datetime.now().strftime('%Y-%m-%d')
                existing = session.query(MarketRisk).filter_by(date=today).first()
                
                if existing:
                    existing.market_mode = result['market_mode']
                    existing.risk_score = result['risk_score']
                    existing.allocation = result['allocation']
                    existing.factors_json = json.dumps(result['factors'], ensure_ascii=False)
                    existing.analyzed_at = datetime.now()
                else:
                    session.add(MarketRisk(
                        date=today,
                        market_mode=result['market_mode'],
                        mode_label=result['mode_label'],
                        risk_score=result['risk_score'],
                        allocation=result['allocation'],
                        description=result['description'],
                        factors_json=json.dumps(result['factors'], ensure_ascii=False),
                        vnindex_value=result.get('vnindex_detail', {}).get('vnindex'),
                        raw_scores_json=json.dumps(result['raw_scores']),
                    ))
                
                session.commit()
                session.close()
                print("âœ… Market risk analysis saved!")
                
            except Exception as e:
                print(f"âš ï¸ Market risk analysis failed: {e}")
        
        # Start market risk in background
        thread = threading.Thread(target=run_market_risk_after_scan)
        thread.daemon = True
        thread.start()
        
        return jsonify({...}), 202

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
            'response': 'Xin lá»—i, cÃ³ lá»—i xáº£y ra.'
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
            'tables': ['signals', 'portfolios', 'cash_positions', 'chat_history', 'ticker_blacklist', 'market_risk']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# APPLICATION STARTUP
# ========================================================================
# ============================================================================
# SELL SIGNAL SCANNER ENDPOINT
# ============================================================================

import threading
from sell_signal_scanner_v2 import SellSignalScannerV2

# ========================================================================
# MARKET RISK ENDPOINTS
# ========================================================================

@app.route('/api/market-risk', methods=['GET'])
def get_market_risk():
    """Get latest market risk analysis"""
    session = Session()
    try:
        latest = session.query(MarketRisk).order_by(
            MarketRisk.date.desc()
        ).first()
        
        if not latest:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No market analysis available yet'
            })
        
        factors = json.loads(latest.factors_json) if latest.factors_json else []
        raw_scores = json.loads(latest.raw_scores_json) if latest.raw_scores_json else {}
        
        return jsonify({
            'success': True,
            'data': {
                'date': latest.date,
                'market_mode': latest.market_mode,
                'mode_label': latest.mode_label,
                'risk_score': latest.risk_score,
                'allocation': latest.allocation,
                'description': latest.description,
                'factors': factors,
                'vnindex_value': latest.vnindex_value,
                'raw_scores': raw_scores,
                'analyzed_at': latest.analyzed_at.isoformat() if latest.analyzed_at else None,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/market-risk/scan', methods=['POST'])
def trigger_market_risk_scan():
    """Trigger market risk analysis"""
    try:
        from market_risk_analysis import run_market_analysis
        
        result = run_market_analysis()
        
        # Save to database
        session = Session()
        today = datetime.now().strftime('%Y-%m-%d')
        
        existing = session.query(MarketRisk).filter_by(date=today).first()
        
        if existing:
            existing.market_mode = result['market_mode']
            existing.mode_label = result['mode_label']
            existing.risk_score = result['risk_score']
            existing.allocation = result['allocation']
            existing.description = result['description']
            existing.factors_json = json.dumps(result['factors'], ensure_ascii=False)
            existing.vnindex_value = result.get('vnindex_detail', {}).get('vnindex')
            existing.raw_scores_json = json.dumps(result['raw_scores'])
            existing.analyzed_at = datetime.now()
        else:
            new_record = MarketRisk(
                date=today,
                market_mode=result['market_mode'],
                mode_label=result['mode_label'],
                risk_score=result['risk_score'],
                allocation=result['allocation'],
                description=result['description'],
                factors_json=json.dumps(result['factors'], ensure_ascii=False),
                vnindex_value=result.get('vnindex_detail', {}).get('vnindex'),
                raw_scores_json=json.dumps(result['raw_scores']),
                analyzed_at=datetime.now(),
            )
            session.add(new_record)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Market risk analysis completed'
        }), 201
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
    finally:
        try:
            session.close()
        except:
            pass


@app.route('/api/market-risk/history', methods=['GET'])
def get_market_risk_history():
    """Get market risk history (last N days)"""
    session = Session()
    try:
        days = request.args.get('days', 7, type=int)
        
        records = session.query(MarketRisk).order_by(
            MarketRisk.date.desc()
        ).limit(days).all()
        
        history = []
        for r in records:
            history.append({
                'date': r.date,
                'market_mode': r.market_mode,
                'risk_score': r.risk_score,
                'allocation': r.allocation,
            })
        
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    # Initialize database
    try:
        print("\nðŸš€ Starting AI Advisor Backend v3.3 - FIXED...")
        Base.metadata.create_all(engine)
        print("âœ… Database initialized")
        
        # Load EOD prices
        load_eod_prices()
        
    except Exception as e:
        print(f"âš ï¸ Warning: {e}")
    
    # Get port from environment (CRITICAL for Render!)
    port = int(os.getenv('PORT', 10000))
    
    print(f"\n{'='*70}")
    print("ðŸš€ AI ADVISOR BACKEND v3.3 - FIXED VERSION")
    print(f"{'='*70}")
    print(f"AI: {'âœ… GPT-4o-mini (Strict Rules)' if openai_client else 'âŒ Not configured'}")
    print(f"EOD File: {'âœ… Loaded' if CACHE_LOADED and PRICES_CACHE else 'âš ï¸ Not found'}")
    print(f"Tickers: {len(PRICES_CACHE)}")
    print(f"Database: {DATABASE_URL}")
    print(f"Host: 0.0.0.0 (Render-ready)")
    print(f"Port: {port}")
    print(f"{'='*70}\n")
    
    # CRITICAL: Bind to 0.0.0.0 and use PORT from environment!
    app.run(debug=False, host='0.0.0.0', port=port)