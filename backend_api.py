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

# === VIP + PWA Push (graceful import) ===
try:
    from vip_auth import init_vip_system, push_vip_users
    from pwa_push_backend import init_push_routes, SignalPayloadBuilder
    _has_vip = True
    print("✅ VIP/Push modules loaded")
except ImportError as e:
    _has_vip = False
    push_vip_users = None
    print(f'⚠️  VIP/Push modules not found: {e}')

# SELL Signal Integration (graceful import)
try:
    from backend_sell_api import register_sell_routes
    _has_sell_api = True
except ImportError:
    _has_sell_api = False
    print('âš ï¸  backend_sell_api not found - using built-in sell routes')

# ========================================================================
# FLASK APP INITIALIZATION
# ========================================================================

app = Flask(__name__)
CORS(app)

# Register SELL Signal Routes (only if external file exists)
if _has_sell_api:
    register_sell_routes(app)
    print("âœ… SELL signal routes registered from backend_sell_api")

# ========================================================================
# CONFIGURATION
# ========================================================================

# Configure OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("Ã¢Å“â€¦ OpenAI configured")
else:
    print("Ã¢Å¡ Ã¯Â¸Â OPENAI_API_KEY not set")
    openai_client = None

# ========================================================================
# DATABASE CONFIGURATION - ENVIRONMENT-AWARE Ã°Å¸Å’Â
# ========================================================================

ENVIRONMENT = os.getenv('ENVIRONMENT', 'production').lower()
print(f"\n{'='*70}")
print(f"Ã°Å¸Å’Â Environment: {ENVIRONMENT.upper()}")
print(f"{'='*70}")

# Choose database based on environment
if ENVIRONMENT == 'staging':
    DATABASE_URL = os.getenv('DATABASE_URL_STAGING') or os.getenv('DATABASE_URL', 'sqlite:///signals.db')
    print("Ã°Å¸â€œÅ  Using STAGING database (Supabase)")
else:
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
    print("Ã°Å¸â€œÅ  Using PRODUCTION database (Render Postgres)")

# Fix PostgreSQL URL for psycopg3 (Python 3.13 compatible)
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
    print(f"Ã¢Å“â€¦ Using PostgreSQL with psycopg (v3) driver")

# Print database URL (first 50 chars for security)
db_url_display = DATABASE_URL[:50] + "..." if len(DATABASE_URL) > 50 else DATABASE_URL
print(f"Ã°Å¸â€â€” Database URL: {db_url_display}")
print(f"{'='*70}\n")

# EOD prices now stored in PostgreSQL (eod_prices table)
# No more file-based caching

# ========================================================================
# DATABASE SETUP
# ========================================================================

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# === INIT VIP + PUSH (module level — works with Gunicorn on Render) ===
def get_session():
    return Session()

if _has_vip:
    try:
        init_push_routes(app, get_session)
        init_vip_system(app, engine, Session)
        print("✅ VIP Auth + Push Notification routes registered")
    except Exception as _vip_err:
        print(f"⚠️  VIP init error: {_vip_err}")

# ========================================================================
# AI SYSTEM PROMPT
# ========================================================================

AI_SYSTEM_PROMPT = """You are AI ADVISOR, a decision-support system for Vietnamese investors.

Your primary role:
- Support investment decision-making through structured analysis.
- Provide insights that help users understand risk, probability, and scenarios.
- Guide users toward disciplined, system-based investing.
- Use Market Dashboard data to provide context-aware allocation advice.

=== MARKET DASHBOARD (AI ADVISOR MARKET RISK SYSTEM) ===

You will receive real-time Market Dashboard data in the context. This includes:

1. MARKET MODE: Overall market state
   - BULL (Thị trường tăng): Risk score 0-40, allocation 80-100%
     → Có thể duy trì hoặc tăng tỷ trọng cổ phiếu theo tín hiệu
     → Khuyến khích giữ vị thế trong Buysell Signal list
   - NEUTRAL / THẬN TRỌNG (Thị trường trung tính): Risk score 41-65, allocation 40-70%
     → Giảm tỷ trọng, ưu tiên bảo toàn vốn
     → Chỉ giữ cổ phiếu có nền tảng tốt trong Signal list
     → Tăng tỷ lệ tiền mặt
   - BEAR (Thị trường giảm): Risk score 66-100, allocation 0-30%
     → Ưu tiên cắt lỗ và giảm tỷ trọng tối đa
     → Tăng tiền mặt, phòng thủ là ưu tiên số 1
     → Không mở vị thế mới dù có tín hiệu

2. RISK SCORE (0-100): Điểm rủi ro thị trường tổng hợp
   - 0-40: Rủi ro thấp → Có thể tích cực hơn
   - 41-65: Rủi ro trung bình → Thận trọng
   - 66-80: Rủi ro cao → Giảm tỷ trọng
   - 81-100: Rủi ro rất cao → Phòng thủ tối đa

3. ALLOCATION (% tài sản nên đầu tư vào cổ phiếu):
   - Ví dụ: allocation=50 → Chỉ nên giữ 50% tài sản là cổ phiếu, 50% tiền mặt
   - So sánh với tỷ lệ hiện tại của user để đưa ra khuyến nghị cụ thể

4. MARKET FACTORS: Các yếu tố chi tiết (VN-Index trend, thanh khoản, AD ratio, MA indicators)
   - Dùng để giải thích tại sao thị trường đang ở trạng thái đó

=== QUY TẮC SỬ DỤNG MARKET DASHBOARD ===

LUÔN tham chiếu Market Dashboard khi:
- User hỏi về việc có nên mua/bán không
- User hỏi về tỷ trọng danh mục
- User đang FOMO (sợ bỏ lỡ) hoặc PANIC SELLING
- User hỏi về thị trường chung

Cách sử dụng allocation để tư vấn:
- Tính tỷ lệ cổ phiếu hiện tại của user = (tổng giá trị CP) / (tổng tài sản) × 100
- So sánh với allocation được khuyến nghị từ Market Dashboard
- Nếu user đang giữ nhiều hơn allocation → khuyến nghị giảm tỷ trọng
- Nếu user đang giữ ít hơn allocation → có thể xem xét tăng (chỉ với Signal stocks)

Ví dụ tư vấn dựa trên Market Dashboard:
- BEAR + allocation=20%, user đang giữ 80% CP → "Thị trường đang BEAR với rủi ro cao.
  Hệ thống khuyến nghị chỉ giữ 20% tài sản là cổ phiếu. Danh mục hiện tại của bạn
  đang ở mức 80% - cao hơn khuyến nghị đáng kể. Cân nhắc giảm tỷ trọng để bảo vệ vốn."
- BULL + allocation=90%, user đang giữ 60% → "Thị trường đang BULL. Bạn có thể
  xem xét tăng tỷ trọng với các cổ phiếu trong Buysell Signal list."

=== PRODUCT RULE (CRITICAL) ===

- AI ADVISOR only provides action-oriented guidance (buy/sell considerations)
  for stocks that are included in the official "Buysell Signal" list.
- For all other stocks: analysis only, NO action guidance.

Core principles:
1. You do NOT provide direct buy/sell commands outside the Buysell Signal list.
2. You do NOT promise profits or guaranteed outcomes.
3. You do NOT encourage speculation, gambling, or impulsive behavior.
4. You prioritize capital protection, risk management, and discipline.
5. Market Dashboard data ALWAYS takes precedence — even Signal stocks should not
   be bought aggressively during BEAR market conditions.

Behavior rules by stock type:

A. If the stock IS in the "Buysell Signal" list:
- Discuss signal context relative to current Market Mode
- In BULL market: can discuss entry considerations
- In NEUTRAL/THẬN TRỌNG: emphasize caution and smaller position sizing
- In BEAR market: advise waiting even for Signal stocks
- Always include Risk & invalidation conditions

B. If the stock is NOT in the "Buysell Signal" list:
- Analyze only, no action guidance
- State clearly: cổ phiếu này không trong hệ thống Buysell Signal
- Redirect user to Signal list if they want actionable guidance

=== RESPONSE STYLE ===

- Professional, disciplined, neutral — no hype, no emotional language
- Concise by default; expand only if requested
- RESPOND IN VIETNAMESE unless user writes in English
- Always cite Market Dashboard data when giving allocation advice
- Use concrete numbers: "Rủi ro hiện tại: X/100", "Khuyến nghị tỷ trọng: Y%"

Default output structure:
1. Trạng thái thị trường hiện tại (từ Market Dashboard)
2. Đánh giá danh mục so với khuyến nghị allocation
3. Phân tích cổ phiếu cụ thể (nếu user hỏi)
4. Khuyến nghị hành động (chỉ cho Signal stocks, tùy market mode)
5. Cảnh báo rủi ro

User expectation management:
- Clearly state AI ADVISOR supports decision-making, not investment advice
- Emphasize Buysell Signal list + Market Dashboard are the two pillars

If user pushes for action on non-signal stocks:
- Politely refuse, redirect to Signal list

If user intent is unclear:
- Ask ONE clarifying question only

CRITICAL: Help users control FOMO and PANIC SELLING by:
- Citing Market Dashboard data (objective, not emotional)
- Reminding them of allocation targets
- Pointing out when emotions conflict with system data
- Supporting disciplined, data-driven decisions
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
    # Position tracking - MUST be in model for ORM to load from DB
    status = Column(String(20), default='open')       # open / partial / closed
    position_pct = Column(Integer, default=100)        # 0-100%
    
    # SELL signal exit tracking (for SELL signals)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True)
    exit_date = Column(String(20), nullable=True)


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
class EodPrice(Base):
    """EOD prices stored in PostgreSQL - persistent across Render redeploys"""
    __tablename__ = 'eod_prices'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    trade_date = Column(String(20))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def get_current_price(ticker):
    """Get EOD price from PostgreSQL - persistent across Render redeploys"""
    ticker = ticker.upper().strip()
    session = Session()
    try:
        record = session.query(EodPrice).filter_by(ticker=ticker).first()
        if record:
            return record.price
        return None
    except Exception as e:
        print(f"⚠️ get_current_price error for {ticker}: {e}")
        return None
    finally:
        session.close()


def get_portfolio_context(user_id):
    """Get portfolio context with P&L + Market Dashboard data for AI advisor"""
    session = Session()
    try:
        portfolios = session.query(Portfolio).filter_by(user_id=user_id).all()
        cash_pos = session.query(CashPosition).filter_by(user_id=user_id).first()
        cash = cash_pos.cash_amount if cash_pos else 0

        # ALL active BUY signals (for Signal list)
        signals = session.query(Signal).filter(Signal.action == 'BUY').all()
        signal_tickers = set([s.ticker for s in signals])

        # MARKET DASHBOARD: Inject latest market risk into context
        market_context = ""
        try:
            latest_risk = session.query(MarketRisk).order_by(
                MarketRisk.date.desc()
            ).first()

            if latest_risk:
                mode_emoji = {
                    'BULL': '🟢', 'NEUTRAL': '🟡', 'THAN TRONG': '🟡', 'BEAR': '🔴'
                }.get(latest_risk.market_mode, '⚪')

                market_context += "\n=== MARKET DASHBOARD (AI ADVISOR) ===\n"
                market_context += f"Ngay phan tich: {latest_risk.date}\n"
                market_context += f"Market Mode: {mode_emoji} {latest_risk.market_mode}"
                if latest_risk.mode_label:
                    market_context += f" - {latest_risk.mode_label}"
                market_context += "\n"
                market_context += f"Risk Score: {latest_risk.risk_score}/100\n"
                market_context += f"Khuyen nghi ty trong CP: {latest_risk.allocation}%\n"
                if latest_risk.vnindex_value:
                    market_context += f"VN-Index: {latest_risk.vnindex_value:,.2f}\n"
                if latest_risk.description:
                    market_context += f"Mo ta: {latest_risk.description}\n"

                # Append key factors
                try:
                    factors = json.loads(latest_risk.factors_json) if latest_risk.factors_json else []
                    if factors:
                        market_context += "Cac yeu to chinh:\n"
                        for fac in factors[:4]:
                            status = fac.get('status', '')
                            name = fac.get('name', '')
                            detail = fac.get('detail', '')
                            market_context += f"  - {name}: {status} - {detail}\n"
                except Exception:
                    pass

                market_context += "=== KET THUC MARKET DASHBOARD ===\n"
            else:
                market_context = "\n[Market Dashboard: Chua co du lieu phan tich thi truong]\n"
        except Exception as e:
            print(f"Market risk context error: {e}")
            market_context = "\n[Market Dashboard: Loi khi tai du lieu thi truong]\n"

        # Empty portfolio
        if not portfolios and cash == 0:
            context = f"{market_context}\nDanh muc: Trong\n"
            context += f"\nCO PHIEU TRONG BUYSELL SIGNAL SYSTEM:\n"
            context += ", ".join(sorted(signal_tickers)) if signal_tickers else "Chua co signal nao"
            return context, signal_tickers

        context = f"{market_context}\n"
        context += "DANH MUC DAU TU:\n\n"

        total_cost = 0
        total_value = 0

        if portfolios:
            context += "CO PHIEU:\n"

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

                in_signal = "[IN BUYSELL SIGNAL]" if p.ticker in signal_tickers else "[NOT IN SIGNAL LIST]"

                context += f"- {p.ticker} {in_signal}: {p.quantity} CP @ {p.avg_price:,.0f} VND\n"
                context += f"  Gia hien tai: {current_price:,.0f} VND\n"
                context += f"  P&L: {pl:+,.0f} VND ({pl_pct:+.1f}%)\n"

            context += f"\nTong gia tri CP: {total_value:,.0f} VND\n"
            context += f"Lai/Lo: {total_value - total_cost:+,.0f} VND\n"

        if cash > 0:
            context += f"\nTIEN MAT: {cash:,.0f} VND\n"

        total_assets = total_value + cash
        if total_assets > 0:
            stock_pct = (total_value / total_assets * 100)
            cash_pct = (cash / total_assets * 100)
            context += f"\nTONG TAI SAN: {total_assets:,.0f} VND\n"
            context += f"Phan bo hien tai: {stock_pct:.1f}% CP / {cash_pct:.1f}% TM\n"

            # Compare vs Market Dashboard allocation recommendation
            try:
                if latest_risk and latest_risk.allocation is not None:
                    rec_alloc = latest_risk.allocation
                    diff = stock_pct - rec_alloc
                    if diff > 10:
                        context += f"[CANH BAO] Dang giu {stock_pct:.1f}% CP, he thong khuyen nghi {rec_alloc}%. "
                        context += f"CAO HON {diff:.1f}% so voi khuyen nghi.\n"
                    elif diff < -10:
                        context += f"[INFO] Dang giu {stock_pct:.1f}% CP, he thong khuyen nghi {rec_alloc}%. "
                        context += f"Con du dia tang {abs(diff):.1f}% neu thi truong phu hop.\n"
                    else:
                        context += f"[OK] Ty trong hien tai ({stock_pct:.1f}%) phu hop voi khuyen nghi ({rec_alloc}%).\n"
            except Exception:
                pass

        context += f"\n\nCO PHIEU TRONG BUYSELL SIGNAL SYSTEM:\n"
        context += ", ".join(sorted(signal_tickers)) if signal_tickers else "Chua co signal nao"

        return context, signal_tickers

    except Exception as e:
        print(f"Error: {e}")
        return "Danh muc: Loi", set()
    finally:
        session.close()


def chat_with_gpt(message, portfolio_context, signal_tickers):
    """Chat with OpenAI using strict system prompt"""
    if not openai_client:
        return "Xin lÃ¡Â»â€”i, AI chÃ†Â°a Ã„â€˜Ã†Â°Ã¡Â»Â£c cÃ¡ÂºÂ¥u hÃƒÂ¬nh."
    
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
        return "Xin lÃ¡Â»â€”i, AI khÃƒÂ´ng phÃ¡ÂºÂ£n hÃ¡Â»â€œi Ã„â€˜Ã†Â°Ã¡Â»Â£c."


# ========================================================================
# API ROUTES - BASIC
# ========================================================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'AI Advisor Backend v3.3',
        'version': '3.6 (EOD Prices in PostgreSQL) - 2026-02-26',
        'features': ['signals', 'portfolio', 'cash', 'eod_prices', 'chat_ai_strict', 'fomo_control', 'automation'],
        'eod_prices': {
            'source': 'postgresql',
            'tickers': 0
        },
        'status': 'running'
    })


@app.route('/health', methods=['GET'])
def health():
    session = Session()
    try:
        eod_count = session.query(EodPrice).count()
    except:
        eod_count = 0
    finally:
        session.close()
    return jsonify({
        'status': 'healthy',
        'openai': openai_client is not None,
        'eod_source': 'postgresql',
        'eod_tickers': eod_count,
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
                    # Signal tracking fields (status/position_pct now in model)
                    'signal_code': s.signal_code or f"{s.ticker}-{s.id}",
                    'buy_signal_code': s.buy_signal_code,
                    'status': s.status or ('open' if s.action == 'BUY' else 'closed'),
                    'position_pct': s.position_pct if s.position_pct is not None else (100 if s.action == 'BUY' else 0),
                    # SELL signal exit fields (for SELL signals display)
                    'exit_price': round(s.exit_price / 100) * 100 if s.exit_price else None,
                    'exit_reason': s.exit_reason,
                    'exit_date': s.exit_date,
                })
            
            # Deduplicate: Keep BEST signal per ticker per date (highest strength)
            seen = {}  # Track: ticker_date Ã¢â€ â€™ signal
            deduplicated = []
            
            for signal in signals_data:
                key = f"{signal['ticker']}_{signal['date']}"
                
                if key not in seen:
                    # First signal for this ticker+date Ã¢â€ â€™ Keep it
                    seen[key] = signal
                    deduplicated.append(signal)
                else:
                    # Duplicate found Ã¢â€ â€™ Keep signal with HIGHER strength
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
            session.flush()  # Get ID trÆ°á»›c khi commit
            
            # Set signal code vÃ  defaults qua ORM (khÃ´ng dÃ¹ng raw SQL Ä‘á»ƒ trÃ¡nh cache issue)
            if signal.action == 'BUY':
                signal.signal_code = f"{signal.ticker}-{signal.id}"
                signal.status = 'open'
                signal.position_pct = 100
            
            # --- AUTO-UPDATE BUY STATUS khi táº¡o SELL signal ---
            buy_update_info = None
            if signal.action == 'SELL':
                signal.status = 'closed'
                signal.position_pct = 0
                # Lấy sell_pct từ request (TAKE_PROFIT=50%, STOP_LOSS=100%)
                sell_pct = data.get('exit_quantity_pct') or data.get('sell_pct', 100)
                # Update BUY signal tương ứng (FIFO)
                buy_update_info = auto_update_buy_status(signal.ticker, session, sell_pct=sell_pct)
                # Link SELL â†’ BUY
                if buy_update_info:
                    signal.buy_signal_code = buy_update_info['buy_signal_code']
            # --- Káº¾T THÃšC ---
            
            session.commit()
            
            print(f"âœ… Signal created: {signal.ticker} ({signal.action}) - {signal.date}")
            if buy_update_info:
                print(f"   â””â”€ BUY {buy_update_info['buy_signal_code']} â†’ closed")
            
            response_data = {
                'success': True,
                'id': signal.id,
                'ticker': signal.ticker,
                'action': signal.action,
                'message': 'Signal created successfully'
            }
            if buy_update_info:
                response_data['buy_signal_updated'] = buy_update_info
            
            return jsonify(response_data), 201
            
        except Exception as e:
            session.rollback()
            print(f"âŒ Error creating signal: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()


# ========================================================================
# HELPER: AUTO-UPDATE BUY STATUS KHI CÃ“ SELL SIGNAL
# ========================================================================

def auto_update_buy_status(ticker, session, sell_pct=100):
    """
    Tá»± Ä‘á»™ng update BUY signal cÅ© nháº¥t (FIFO) sang closed khi cÃ³ SELL signal má»›i.
    DÃ¹ng ORM query Ä‘á»ƒ trÃ¡nh session cache issue.
    """
    try:
        # TÃ¬m BUY signal cÅ© nháº¥t cÃ²n má»Ÿ (FIFO) - dÃ¹ng ORM
        buy_signal = session.query(Signal).filter(
            Signal.ticker == ticker,
            Signal.action == 'BUY',
            Signal.status.in_(['open', 'partial'])
        ).order_by(
            Signal.date.asc(),
            Signal.created_at.asc()
        ).first()
        
        # Náº¿u khÃ´ng cÃ³ status (cÅ©), tÃ¬m khÃ´ng lá»c status
        if not buy_signal:
            buy_signal = session.query(Signal).filter(
                Signal.ticker == ticker,
                Signal.action == 'BUY',
                Signal.status == None
            ).order_by(
                Signal.date.asc(),
                Signal.created_at.asc()
            ).first()
        
        if not buy_signal:
            print(f"âš ï¸  No open BUY signal found for {ticker}")
            return None
        
        old_status = buy_signal.status or 'open'
        old_pct = buy_signal.position_pct if buy_signal.position_pct is not None else 100
        buy_signal_code = buy_signal.signal_code or f"{ticker}-{buy_signal.id}"
        
        # Tinh position con lai
        remaining_pct = max(0, old_pct - sell_pct)
        
        if remaining_pct <= 0:
            buy_signal.status = 'closed'
            buy_signal.position_pct = 0
        else:
            buy_signal.status = 'partial'
            buy_signal.position_pct = remaining_pct
        
        print(f"BUY {buy_signal_code}: {old_status}/{old_pct}% -> {buy_signal.status}/{buy_signal.position_pct}%")
        
        return {
            'buy_id': buy_signal.id,
            'buy_signal_code': buy_signal_code,
            'old_status': old_status,
            'new_status': buy_signal.status,
            'new_pct': buy_signal.position_pct
        }
        
    except Exception as e:
        print(f"âŒ Error in auto_update_buy_status for {ticker}: {e}")
        return None
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
    - If buy_signal_code provided â†’ Use that specific signal (Manual)
    - If not provided â†’ Auto-match oldest open signal (FIFO)
    
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
            stop_loss=sell_price if sell_reason == 'STOP_LOSS' else buy_signal.stop_loss,
            take_profit=sell_price if sell_reason == 'TAKE_PROFIT' else buy_signal.take_profit,
            risk_reward=0,
            strength=100 if sell_reason == 'STOP_LOSS' else 80,
            stock_type=buy_signal.stock_type,
            date=datetime.now().strftime('%Y-%m-%d'),
            action='SELL',
            buy_signal_code=buy_signal.signal_code  # Link to BUY signal
        )
        
        session.add(sell_signal)
        session.flush()  # Get sell_signal.id
        
        # Set SELL status qua ORM
        sell_signal.status = 'closed'
        sell_signal.position_pct = 0
        
        # --- AUTO-UPDATE BUY STATUS (FIFO) qua ORM ---
        current_pct = buy_signal.position_pct if buy_signal.position_pct is not None else 100
        new_pct = max(0, current_pct - sell_pct)
        new_status = 'closed' if new_pct == 0 else 'partial'
        
        buy_signal.status = new_status
        buy_signal.position_pct = new_pct
        print(f"âœ… BUY {buy_signal.signal_code}: {current_pct}% â†’ {new_status} ({new_pct}%)")
        # --- Káº¾T THÃšC AUTO-UPDATE ---
        
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
            'buy_signal_updated': {
                'id': buy_signal.id,
                'signal_code': buy_signal.signal_code,
                'previous_pct': current_pct,
                'new_status': new_status,
                'new_pct': new_pct
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
            time.sleep(60)  # Ã„ÂÃ¡Â»Â£i signal scan chÃ¡ÂºÂ¡y 1 phÃƒÂºt
            
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
                print("Ã¢Å“â€¦ Market risk analysis saved!")
                
            except Exception as e:
                print(f"Ã¢Å¡ Ã¯Â¸Â Market risk analysis failed: {e}")
        
        # Start market risk in background
        thread = threading.Thread(target=run_market_risk_after_scan)
        thread.daemon = True
        thread.start()
        
        return jsonify({...}), 202

@app.route('/api/scan-sell', methods=['POST'])
def trigger_sell_scan():
    """
    Trigger SELL signal scanner. Called by GitHub Actions hourly.
    Scans all open BUY signals and creates SELL signals if SL/TP hit.
    """
    try:
        scanner_path = os.path.join(
            os.path.dirname(__file__),
            'scripts',
            'sell_signal_scanner.py'
        )
        
        if not os.path.exists(scanner_path):
            # Fallback: Run inline sell check
            session = Session()
            try:
                # Get all open BUY signals
                open_buys = session.query(Signal).filter(
                    Signal.action == 'BUY',
                    Signal.status.in_(['open', 'partial'])
                ).all()
                
                # Also get BUY signals with no status (legacy)
                legacy_buys = session.query(Signal).filter(
                    Signal.action == 'BUY',
                    Signal.status == None
                ).all()
                
                all_open = open_buys + legacy_buys
                
                return jsonify({
                    'success': True,
                    'message': f'Sell scanner script not found. {len(all_open)} open BUY signals tracked.',
                    'open_signals': len(all_open),
                    'note': 'Deploy sell_signal_scanner.py to scripts/ for full automation'
                })
            finally:
                session.close()
        
        process = subprocess.Popen(
            ['python', scanner_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(__file__)
        )
        
        return jsonify({
            'success': True,
            'status': 'scanning',
            'message': 'SELL signal scanner started.',
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
            'response': 'Xin lÃ¡Â»â€”i, cÃƒÂ³ lÃ¡Â»â€”i xÃ¡ÂºÂ£y ra.'
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
    """Get EOD price status from DB"""
    session = Session()
    try:
        count = session.query(EodPrice).count()
        latest = session.query(EodPrice).order_by(EodPrice.updated_at.desc()).first()
        last_updated = latest.updated_at.isoformat() if latest else None
        trade_date = latest.trade_date if latest else None
        
        age_days = None
        needs_refresh = True
        if latest and latest.updated_at:
            age_days = (datetime.now() - latest.updated_at).days
            needs_refresh = age_days >= 1
        
        return jsonify({
            'success': True,
            'source': 'postgresql',
            'tickers_count': count,
            'last_updated': last_updated,
            'trade_date': trade_date,
            'age_days': age_days,
            'needs_refresh': needs_refresh
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/prices/update', methods=['POST'])
def update_prices():
    """Update EOD prices from vnstock into PostgreSQL.
    Called by GitHub Actions at 4PM Vietnam time daily."""
    import subprocess
    
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_eod_prices.py')
    
    if not os.path.exists(script_path):
        return jsonify({
            'success': False,
            'error': f'update_eod_prices.py not found. Please deploy the script.'
        }), 404
    
    try:
        env = os.environ.copy()
        # Non-blocking: fire and forget, do NOT wait for process
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env
        )
        
        return jsonify({
            'success': True,
            'status': 'running',
            'message': f'Price update started (PID {process.pid}). Takes ~8 min. Check /api/eod/status.',
            'pid': process.pid
        }), 202
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/migrate', methods=['POST'])
def migrate():
    try:
        Base.metadata.create_all(engine)
        return jsonify({
            'success': True,
            'message': 'Migration successful',
            'tables': ['signals', 'portfolios', 'cash_positions', 'chat_history', 'ticker_blacklist', 'market_risk', 'eod_prices']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================================================
# ADMIN: Update signal status/position
# ========================================================================

@app.route('/api/admin/fix-signal', methods=['POST'])
def admin_fix_signal():
    """Admin endpoint to fix signal status and position_pct"""
    session = Session()
    try:
        data = request.json
        signal_id = data.get('signal_id')
        
        if not signal_id:
            return jsonify({'error': 'Missing signal_id'}), 400
        
        signal = session.query(Signal).filter_by(id=signal_id).first()
        if not signal:
            return jsonify({'error': f'Signal {signal_id} not found'}), 404
        
        old_status = signal.status
        old_pct = signal.position_pct
        
        if 'status' in data:
            signal.status = data['status']
        if 'position_pct' in data:
            signal.position_pct = data['position_pct']
        
        session.commit()
        
        code = signal.signal_code or f"{signal.ticker}-{signal.id}"
        print(f"ADMIN FIX: {code} | {old_status}/{old_pct}% -> {signal.status}/{signal.position_pct}%")
        
        return jsonify({
            'success': True,
            'signal_code': code,
            'ticker': signal.ticker,
            'old_status': old_status,
            'old_pct': old_pct,
            'new_status': signal.status,
            'new_pct': signal.position_pct
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ========================================================================
# SYNC SELL STATUS - Batch update BUY signals dá»±a trÃªn SELL signals cÃ³ sáºµn
# ========================================================================

@app.route('/api/signals/sync-sell-status', methods=['POST'])
def sync_sell_status():
    """Batch update BUY signals status dua tren SELL signals co san trong DB."""
    session = Session()
    try:
        sell_signals = session.query(Signal).filter(
            Signal.action == 'SELL'
        ).order_by(Signal.date.asc()).all()

        updated = []
        skipped = []
        errors = []

        for sell in sell_signals:
            try:
                buy = session.query(Signal).filter(
                    Signal.ticker == sell.ticker,
                    Signal.action == 'BUY',
                    Signal.status.in_(['open', 'partial'])
                ).order_by(
                    Signal.date.asc(),
                    Signal.created_at.asc()
                ).first()

                if not buy:
                    buy = session.query(Signal).filter(
                        Signal.ticker == sell.ticker,
                        Signal.action == 'BUY',
                        Signal.status == None
                    ).order_by(
                        Signal.date.asc(),
                        Signal.created_at.asc()
                    ).first()

                if not buy:
                    skipped.append({'ticker': sell.ticker, 'sell_date': sell.date})
                    continue

                old_status = buy.status or 'open'
                buy_code = buy.signal_code or f"{buy.ticker}-{buy.id}"

                buy.status = 'closed'
                buy.position_pct = 0

                if not sell.buy_signal_code:
                    sell.buy_signal_code = buy_code
                sell.status = 'closed'
                sell.position_pct = 0

                updated.append({
                    'ticker': sell.ticker,
                    'buy_code': buy_code,
                    'sell_date': sell.date,
                    'old_status': old_status
                })

            except Exception as e:
                errors.append({'ticker': sell.ticker, 'error': str(e)})

        session.commit()

        return jsonify({
            'success': True,
            'summary': {
                'total_sell_signals': len(sell_signals),
                'updated': len(updated),
                'skipped': len(skipped),
                'errors': len(errors)
            },
            'updated': updated,
            'skipped': skipped[:10],
            'errors': errors
        })

    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


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

@app.route('/api/market-risk/upload', methods=['POST'])
def upload_market_risk():
    """Upload market risk data from local analysis"""
    session = Session()
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        today = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        existing = session.query(MarketRisk).filter_by(date=today).first()
        
        factors_json = json.dumps(data.get('factors', []), ensure_ascii=False)
        raw_scores_json = json.dumps(data.get('raw_scores', {}))
        
        if existing:
            existing.market_mode = data.get('mode', data.get('market_mode', 'sideways'))
            existing.mode_label = data.get('mode_label', 'THẬN TRỌNG')
            existing.risk_score = data.get('risk_score', 50)
            existing.allocation = data.get('allocation', 50)
            existing.description = data.get('description', '')
            existing.factors_json = factors_json
            existing.vnindex_value = data.get('vnindex_value')
            existing.raw_scores_json = raw_scores_json
            existing.analyzed_at = datetime.now()
        else:
            new_record = MarketRisk(
                date=today,
                market_mode=data.get('mode', data.get('market_mode', 'sideways')),
                mode_label=data.get('mode_label', 'THẬN TRỌNG'),
                risk_score=data.get('risk_score', 50),
                allocation=data.get('allocation', 50),
                description=data.get('description', ''),
                factors_json=factors_json,
                vnindex_value=data.get('vnindex_value'),
                raw_scores_json=raw_scores_json,
                analyzed_at=datetime.now(),
            )
            session.add(new_record)
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Market risk uploaded for {today}',
            'date': today,
            'risk_score': data.get('risk_score'),
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
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


@app.route('/api/admin/fix-orphaned-signals', methods=['POST'])
def fix_orphaned_signals():
    """
    Fix BUY signals that have exit_date/exit_reason but status still 'open'
    
    ADMIN ONLY endpoint for database cleanup
    """
    session = get_session()
    
    try:
        # Find orphaned BUY signals
        orphaned = session.query(Signal).filter(
            Signal.action == 'buy',
            Signal.status == 'open',
            Signal.exit_date.isnot(None),
            Signal.exit_date != ''
        ).all()
        
        if not orphaned:
            return jsonify({
                'success': True,
                'fixed': 0,
                'message': 'No orphaned signals found'
            })
        
        # Get list before fixing
        orphaned_list = []
        for sig in orphaned:
            orphaned_list.append({
                'id': sig.id,
                'ticker': sig.ticker,
                'entry_date': sig.entry_date,
                'exit_date': sig.exit_date,
                'exit_reason': sig.exit_reason,
                'old_status': sig.status
            })
        
        # Fix them
        for sig in orphaned:
            sig.status = 'closed'
        
        session.commit()
        
        return jsonify({
            'success': True,
            'fixed': len(orphaned),
            'signals': orphaned_list,
            'message': f'Fixed {len(orphaned)} orphaned BUY signals'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


if __name__ == '__main__':
    # Initialize database
    try:
        print("\nÃ°Å¸Å¡â‚¬ Starting AI Advisor Backend v3.3 - FIXED...")
        Base.metadata.create_all(engine)
        print("Ã¢Å“â€¦ Database initialized")
        
        # EodPrice table will be created by migrate
        print("✅ EodPrice: prices stored in PostgreSQL")
        
    except Exception as e:
        print(f"Ã¢Å¡ Ã¯Â¸Â Warning: {e}")
    
    # Get port from environment (CRITICAL for Render!)
    port = int(os.getenv('PORT', 10000))
    
    print(f"\n{'='*70}")
    print("Ã°Å¸Å¡â‚¬ AI ADVISOR BACKEND v3.3 - FIXED VERSION")
    print(f"{'='*70}")
    print(f"AI: {'Ã¢Å“â€¦ GPT-4o-mini (Strict Rules)' if openai_client else 'Ã¢ÂÅ’ Not configured'}")
    print("EOD Prices: Stored in PostgreSQL (eod_prices table)")
    print(f"VIP/Push: {'✅ Enabled' if _has_vip else '⚠️  Not loaded'}")
    print("Use /api/eod/status to check price count")
    print(f"Database: {DATABASE_URL}")
    print(f"Host: 0.0.0.0 (Render-ready)")
    print(f"Port: {port}")
    print(f"{'='*70}\n")
    
    # CRITICAL: Bind to 0.0.0.0 and use PORT from environment!
    app.run(debug=False, host='0.0.0.0', port=port)