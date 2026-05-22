"""
AI Advisor - Daily Signal Scanner
Uses vnstock 3.3.1 Quote API
UPDATED: PostgreSQL support for production deployment
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import random
import os
import sys
import json

# CORRECT vnstock 3.3.1 API
from vnstock import Quote

# SQLAlchemy for database (works with both SQLite and PostgreSQL)
from sqlalchemy import create_engine, text, Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE SETUP - Works with SQLite (local) or PostgreSQL (production)
# ============================================================

# Get DATABASE_URL from environment (production) or use SQLite (local dev)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')

# Fix PostgreSQL URL format if needed (Render uses postgresql://, but SQLAlchemy needs postgresql+psycopg://)
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

# Create engine
try:
    engine = create_engine(DATABASE_URL)
    logger.info(f"✓ Database connected: {DATABASE_URL.split('@')[0]}...")  # Log without password
except Exception as e:
    logger.error(f"✗ Database connection failed: {e}")
    raise

# Create session maker
Session = sessionmaker(bind=engine)

# ============================================================
# STOCK LIST
# ============================================================

# ============================================================
# WATCHLIST 172 - Cổ phiếu ưu tiên thanh khoản cao
# Tiêu chí: avg volume > 200k cp/ngày, loại bỏ penny & illiquid
# Updated: 2026-04-02  |  172 mã unique
# ============================================================

WATCHLIST_172 = [
    # ── TIER 1: VN30 + Blue Chips (43 mã) ─────────────────────────────
    # avg volume > 3M cp/ngày, trụ cột thị trường
    'VCB', 'BID', 'CTG', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB',
    'STB', 'MSN', 'FPT', 'SSI', 'GAS', 'PLX', 'MWG', 'VJC', 'HDB', 'ACB',
    'VRE', 'BCM', 'POW', 'SAB', 'SHB', 'LPB', 'VIB', 'EIB', 'BVH', 'GVR',
    'TPB', 'NVL', 'KDH', 'DGC', 'REE', 'VCI', 'HVN', 'DIG', 'GEX', 'VIX',
    'BSR', 'GMD', 'PNJ',

    # ── TIER 2: Large-Mid Cap HOSE (42 mã) ────────────────────────────
    # avg volume > 1M cp/ngày
    'DPM', 'KBC', 'DXG', 'VPL', 'MSB', 'OCB', 'TCX',
    'HSG', 'DCM', 'HCM', 'VND', 'PC1', 'DGW', 'HDG', 'PVD', 'PVT', 'VTP',
    'SCS', 'TCH', 'NLG', 'CII', 'PDR', 'IDC', 'ANV', 'HAH', 'DBC', 'MCH',
    'CTD', 'HT1', 'VSC', 'BWE', 'PVS', 'VHC', 'SSB', 'FRT', 'ELC', 'BMI',
    'BSI', 'TV2', 'DPG', 'LCG', 'BAF',

    # ── TIER 3: Mid Cap HOSE chất lượng (48 mã) ───────────────────────
    # avg volume 300k–1M cp/ngày, cơ bản tốt
    'TNG', 'KSB', 'MSH', 'SBT', 'VCG', 'CTR', 'SZC', 'PHR', 'GEG', 'PTB',
    'HAX', 'FMC', 'CSV', 'TCM', 'CMG', 'PAN', 'SGN', 'NTL', 'GIL', 'VFC',
    'IDI', 'AAA', 'TLH', 'HBC', 'VPG', 'CRE', 'CSM', 'ASM', 'HHS', 'PDC',
    'PAC', 'TAL', 'KOS', 'SIP', 'ORS', 'CMX', 'NBB', 'SMC', 'DCL', 'QCG',
    'SJS', 'NAF', 'HAG', 'NHA', 'EVF', 'VHG', 'HAP', 'ASG',

    # ── TIER 4: HNX thanh khoản cao (39 mã) ───────────────────────────
    # avg volume > 200k cp/ngày trên HNX
    'SHS', 'MBS', 'VFS', 'CEO', 'NVB', 'VCS', 'HUT', 'NDN', 'PLC', 'EVS',
    'PSI', 'VC3', 'BVS', 'BAB', 'TIG', 'APS', 'IPA', 'DXP', 'TVS', 'LIG',
    'VHE', 'VC7', 'DTT', 'KSV', 'HLD', 'OCH', 'PVI', 'MIG', 'PGB', 'DHT',
    'API', 'NRC', 'MBG', 'SJE', 'INN', 'NAG', 'SD9', 'AMV', 'IDJ',
]

# Dùng WATCHLIST_172 cho scanner
TOP_343_STOCKS = WATCHLIST_172  # backward-compat alias
# Blue Chip = Tier 1 (43 mã vốn hoá lớn nhất)
BLUE_CHIP_STOCKS = [
    'VCB', 'BID', 'CTG', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB',
    'STB', 'MSN', 'FPT', 'SSI', 'GAS', 'PLX', 'MWG', 'VJC', 'HDB', 'ACB',
    'VRE', 'BCM', 'POW', 'SAB', 'SHB', 'LPB', 'VIB', 'EIB', 'BVH', 'GVR',
    'TPB', 'NVL', 'KDH', 'DGC', 'REE', 'VCI', 'HVN', 'DIG', 'GEX', 'VIX',
    'BSR', 'GMD', 'PNJ',
]


def get_stock_type(ticker):
    """
    Classify stock based on ticker list, NOT price.
    
    Blue Chip: Top 50 large-cap stocks with high liquidity
    Mid Cap: In TOP_343 but not Blue Chip  
    Penny: Not in TOP_343
    """
    if ticker in BLUE_CHIP_STOCKS:
        return "Blue Chip"
    elif ticker in TOP_343_STOCKS:
        return "Mid Cap"
    else:
        return "Penny"

def get_top_343_stocks():
    """
    Return 172 highest liquidity stocks (WATCHLIST_172)
    Curated list: avg vol > 200k/day, no penny stocks
    """
    logger.info(f"Using WATCHLIST_172: {len(WATCHLIST_172)} high-liquidity stocks (no penny/illiquid)")
    return TOP_343_STOCKS

def get_last_trading_day():
    """Get last trading day"""
    today = datetime.now()
    
    if today.weekday() == 5:
        last_trading_day = today - timedelta(days=1)
    elif today.weekday() == 6:
        last_trading_day = today - timedelta(days=2)
    else:
        last_trading_day = today
    
    return last_trading_day.strftime('%Y-%m-%d')

def get_stock_data(ticker, days=100, max_retries=3):
    """
    Get stock data using Quote API with retry logic
    
    Args:
        ticker: Stock symbol
        days: Days of historical data
        max_retries: Max retry attempts for rate limit
    
    Returns:
        Processed DataFrame or None
    """
    
    for attempt in range(max_retries):
        try:
            end_date = get_last_trading_day()
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=days*2)).strftime('%Y-%m-%d')
            
            logger.info(f"Fetching {ticker} ({start_date} to {end_date})")
            
            # CORRECT vnstock 3.3.1 syntax!
            quote = Quote(symbol=ticker, source='VCI')
            
            # Get historical data
            df = quote.history(start=start_date, end=end_date)
            
            if df is None or len(df) == 0:
                logger.warning(f"No data for {ticker}")
                return None
            
            logger.info(f"✓ Got {len(df)} days for {ticker}")
            
            return process_dataframe(df, ticker)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Detect rate limit errors
            is_rate_limit = any(phrase in error_msg for phrase in [
                'quá nhiều request',
                'rate limit',
                'too many',
                'vui lòng thử lại'
            ])
            
            if is_rate_limit:
                wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
                logger.warning(f"⚠️ RATE LIMIT for {ticker}. Waiting {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying {ticker}...")
                    continue  # Retry
                else:
                    logger.error(f"✗ Max retries reached for {ticker}")
                    return None
            else:
                # Other errors - don't retry
                logger.error(f"Error {ticker}: {str(e)}")
                return None
    
    return None

def process_dataframe(df, ticker):
    """Process dataframe"""
    try:
        if df is None or len(df) == 0:
            return None
        
        # Standardize columns
        column_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # 🔧 CRITICAL FIX: Convert from thousands VND to VND
        # vnstock 3.3.1 (VCI) returns prices in thousands: 36.5 = 36,500 VND
        # Without this conversion, all prices will be 1000x too small!
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df[col] = df[col] * 1000
        
        # Check required
        required = ['Close', 'High', 'Low', 'Volume']
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            logger.error(f"Missing {ticker}: {missing}")
            return None
        
        # Add Open if missing
        if 'Open' not in df.columns:
            df['Open'] = df['Close'].shift(1)
        
        df = df.sort_index()
        df = df.dropna()
        
        if len(df) < 50:
            logger.warning(f"Not enough {ticker}: {len(df)}")
            return None
        
        logger.info(f"✓ Processed {ticker}: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Process error {ticker}: {str(e)}")
        return None

def calculate_ema(data, period):
    """Calculate EMA"""
    return data['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    """Calculate RSI"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 0.0001)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD line, signal line, and histogram"""
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def find_pivot_lows(series, window=5, lookback=40):
    """
    Find local minimum pivot points within a lookback window.
    A pivot low is the lowest point within ±window candles.
    
    Returns list of (index_position, value) tuples, sorted oldest → newest.
    """
    pivots = []
    # Only search within last `lookback` bars
    start = max(window, len(series) - lookback)
    # Exclude the very last candle (it's current, not yet confirmed)
    end = len(series) - 1

    for i in range(start, end):
        local_range = series.iloc[max(0, i - window): i + window + 1]
        if series.iloc[i] <= local_range.min() + 1e-9:  # allow tiny float tolerance
            # Avoid duplicate pivots too close together
            if pivots and (i - pivots[-1][0]) < window:
                # Keep the lower one
                if series.iloc[i] < pivots[-1][1]:
                    pivots[-1] = (i, series.iloc[i])
            else:
                pivots.append((i, float(series.iloc[i])))
    return pivots

def indicator_at_pivot(series, idx, window=3, use_min=True):
    """
    Get indicator value at a price pivot, using a small ±window buffer
    to account for RSI/MACD lag vs price.
    use_min=True  → return minimum value (for finding most oversold / most negative hist)
    use_min=False → return value at exact index
    """
    n = len(series)
    sl = series.iloc[max(0, idx - window): min(n, idx + window + 1)]
    if use_min:
        return float(sl.min())
    return float(series.iloc[idx])

def check_pullback_strategy(df, ticker):
    """Check Pullback signals"""
    signals = []
    
    try:
        df['EMA20'] = calculate_ema(df, 20)
        df['EMA50'] = calculate_ema(df, 50)
        df['RSI'] = calculate_rsi(df)
        
        latest = df.iloc[-1]
        
        close = latest['Close']
        ema20 = latest['EMA20']
        ema50 = latest['EMA50']
        rsi = latest['RSI']
        
        if pd.isna(ema20) or pd.isna(ema50) or pd.isna(rsi):
            return signals
        
        # Pullback conditions
        uptrend = ema20 > ema50
        near_ema20 = abs(close - ema20) / ema20 < 0.03
        rsi_ok = rsi < 60
        
        if uptrend and near_ema20 and rsi_ok:
            entry_price = close
            stop_loss = ema50 * 0.97
            take_profit = close * 1.08
            risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)
            
            strength = 60
            avg_volume = df['Volume'].tail(20).mean()
            if latest['Volume'] > avg_volume:
                strength += 10
            if rsi < 40:
                strength += 10
            if ema20 > ema50 * 1.02:
                strength += 10
            
            is_priority = strength >= 75
            
            # Classify stock by ticker list (not price)
            stock_type = get_stock_type(ticker)
            
            signal = {
                'ticker': ticker,
                'strategy': 'PULLBACK',
                'action': 'BUY',
                'entry_price': float(entry_price),
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'risk_reward': float(risk_reward) if not np.isnan(risk_reward) else 2.0,
                'strength': int(strength),
                'is_priority': int(is_priority),
                'stock_type': stock_type,
                'rsi': float(rsi),
                'date': get_last_trading_day()
            }
            
            signals.append(signal)
            logger.info(f"✓ PULLBACK {ticker}: {strength}%")
    
    except Exception as e:
        logger.error(f"Pullback error {ticker}: {str(e)}")
    
    return signals

def check_ema_cross_strategy(df, ticker):
    """Check EMA Cross signals"""
    signals = []
    
    try:
        df['EMA20'] = calculate_ema(df, 20)
        df['EMA50'] = calculate_ema(df, 50)
        df['RSI'] = calculate_rsi(df)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        close = latest['Close']
        ema20_curr = latest['EMA20']
        ema50_curr = latest['EMA50']
        ema20_prev = prev['EMA20']
        ema50_prev = prev['EMA50']
        rsi = latest['RSI']
        
        if pd.isna(ema20_curr) or pd.isna(ema50_curr) or pd.isna(rsi):
            return signals
        
        # EMA Cross conditions
        golden_cross = (ema20_prev <= ema50_prev) and (ema20_curr > ema50_curr)
        near_cross = abs(ema20_curr - ema50_curr) / ema50_curr < 0.02
        rsi_ok = 30 <= rsi <= 70
        
        if golden_cross or (near_cross and ema20_curr > ema50_curr and rsi_ok):
            entry_price = close
            stop_loss = ema50_curr * 0.96
            take_profit = close * 1.10
            risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)
            
            strength = 65
            if golden_cross:
                strength += 15
            avg_volume = df['Volume'].tail(20).mean()
            if latest['Volume'] > avg_volume:
                strength += 10
            if 40 <= rsi <= 60:
                strength += 10
            
            is_priority = strength >= 80
            
            # Classify stock by ticker list (not price)
            stock_type = get_stock_type(ticker)
            
            signal = {
                'ticker': ticker,
                'strategy': 'EMA_CROSS',
                'action': 'BUY',
                'entry_price': float(entry_price),
                'stop_loss': float(stop_loss),
                'take_profit': float(take_profit),
                'risk_reward': float(risk_reward) if not np.isnan(risk_reward) else 2.5,
                'strength': int(strength),
                'is_priority': int(is_priority),
                'stock_type': stock_type,
                'rsi': float(rsi),
                'date': get_last_trading_day()
            }
            
            signals.append(signal)
            logger.info(f"✓ EMA_CROSS {ticker}: {strength}%")
    
    except Exception as e:
        logger.error(f"EMA Cross error {ticker}: {str(e)}")
    
    return signals

def check_rsi_macd_divergence_strategy(df, ticker):
    """
    Bullish Divergence Strategy (RSI AND MACD - Daily chart)
    Version 4 — Thuật toán pivot mới: ABSOLUTE MINIMUM thay vì local-swing pivot

    ═══════════════════════════════════════════════════════════════
    VẤN ĐỀ CỦA V1-V3 (đã fix):
      - find_pivot_lows() dùng "local minimum ±window" → bỏ sót pivot1 khi giá
        giảm liên tục (không có bounce rõ giữa 2 đáy, như VJC, GEX)
      - lookback=60 quá ngắn → pivot1 (50-80 bars ago) nằm ngoài vùng search

    CÁCH TIẾP CẬN MỚI (đúng với cách trader vẽ divergence trên chart):
      pivot2 = ABSOLUTE price minimum trong 5-45 bars gần nhất
              → đây là đáy giá thực tế mà trader vẽ divergence
      pivot1 = điểm có RSI MINIMUM trong bars 45-130 trước đó
              → kể cả khi giá không có bounce rõ, RSI vẫn có điểm oversold

    Đây chính xác là cách VJC và GEX được vẽ trên chart:
      • GEX: RSI circle 1 (32.92) tại đáy RSI cũ → RSI circle 2 (47.89) tại đáy giá mới
      • VJC: RSI tạo higher low tại đáy Feb 2026 so với đáy RSI tháng 11/2025

    ═══════════════════════════════════════════════════════════════
    ĐIỀU KIỆN BẮT BUỘC (AND — tất cả phải pass):
      C1.  Price LOWER LOW    : p2_price < p1_price × 0.985  (giá mới thấp hơn ≥ 1.5%)
      C2.  Gap tối thiểu      : ≥ 20 bars giữa pivot1 và pivot2
      C3.  RSI HIGHER LOW     : rsi2 > rsi1 + 3pt  (RSI phân kỳ rõ ràng)
      C4.  RSI tại pivot1     : rsi1 < 50  (pivot1 phải trong vùng oversold)
      C5.  RSI tại pivot2     : rsi2 < 58  (pivot2 chưa phục hồi hoàn toàn)
      C6.  MACD hist HIGHER LOW: hist2 > hist1  (momentum phân kỳ — BẮT BUỘC)
      C7.  hist1 < 0          : đáy cũ phải trong vùng MACD âm
      C8.  MACD hist improving: h[-1] > h[-2] (2 phiên gần nhất đang cải thiện)
      C9.  RSI hiện tại       : 30 ≤ rsi_now ≤ 68
      C10. Recovery           : 0.5% ≤ rec ≤ 25%  (đã hồi phục, chưa bứt quá xa)
      C11. R/R                : ≥ 1.5
    ═══════════════════════════════════════════════════════════════
    """
    signals = []

    try:
        N = len(df)
        # Cần tối thiểu 160 bars:
        #   40 bars warmup (RSI14+MACD26+signal9 ổn định)
        #   + 120 bars usable để p1 (~100 bars ago) có RSI/MACD hợp lệ
        if N < 160:
            return signals

        df = df.copy()
        df['RSI']  = calculate_rsi(df, 14)
        macd_line, signal_line, histogram = calculate_macd(df, fast=12, slow=26, signal=9)
        df['MACD_HIST'] = histogram

        if pd.isna(df['RSI'].iloc[-1]) or pd.isna(df['MACD_HIST'].iloc[-1]):
            return signals

        close_series = df['Close']
        rsi_series   = df['RSI']
        hist_series  = df['MACD_HIST']

        # ══════════════════════════════════════════════════════
        # PIVOT 2: ABSOLUTE PRICE MINIMUM trong 5-45 bars gần nhất
        # Không yêu cầu local swing low — chỉ cần là đáy thực tế gần đây
        # ══════════════════════════════════════════════════════
        p2_search_start = max(0, N - 45)
        p2_search_end   = N - 3          # cần ít nhất 3 bars để xác nhận hồi phục
        if p2_search_end <= p2_search_start:
            return signals

        p2_slice = close_series.iloc[p2_search_start: p2_search_end]
        p2_local = int(p2_slice.values.argmin())
        p2_idx   = p2_search_start + p2_local
        p2_price = float(close_series.iloc[p2_idx])
        bars_since_p2 = N - 1 - p2_idx

        # pivot2 phải cách today ít nhất 3 bars, nhiều nhất 45 bars
        if bars_since_p2 < 3 or bars_since_p2 > 45:
            return signals

        # ══════════════════════════════════════════════════════
        # PIVOT 1: RSI MINIMUM trong khoảng 45-160 bars trước today
        # Mở rộng từ 130→160 để cover pivot1 Nov 2025 (~100-110 bars ago)
        # Với fetch=250 cal days → ~180 trading bars → p1 nằm chắc trong usable range
        # ══════════════════════════════════════════════════════
        p1_search_start = max(0, N - 160)
        p1_search_end   = max(0, N - 45)
        if p1_search_end <= p1_search_start + 5:
            return signals

        older_rsi = rsi_series.iloc[p1_search_start: p1_search_end]
        p1_local  = int(older_rsi.values.argmin())
        p1_idx    = p1_search_start + p1_local
        p1_price  = float(close_series.iloc[p1_idx])

        # ══════════════════════════════════════════════════════
        # Lấy RSI và MACD hist tại mỗi pivot (dùng local min ±3 bars để
        # handle RSI/MACD lag so với price)
        # ══════════════════════════════════════════════════════
        rsi1  = indicator_at_pivot(rsi_series,  p1_idx, window=3, use_min=True)
        rsi2  = indicator_at_pivot(rsi_series,  p2_idx, window=3, use_min=True)
        hist1 = indicator_at_pivot(hist_series, p1_idx, window=3, use_min=True)
        hist2 = indicator_at_pivot(hist_series, p2_idx, window=3, use_min=True)

        if any(pd.isna(v) for v in [rsi1, rsi2, hist1, hist2]):
            return signals

        # ── C1: Price lower low ≥ 1.5% ──
        if p2_price >= p1_price * 0.985:
            return signals

        # ── C2: Gap tối thiểu 20 bars ──
        if (p2_idx - p1_idx) < 20:
            return signals

        # ── C3: RSI higher low ≥ 5pt — BẮT BUỘC ──
        # 5pt (tăng từ 3pt) → filter weak/noise divergence, giữ lại VJC (+8-20pt), GEX (+15pt)
        rsi_diff = rsi2 - rsi1
        if rsi_diff < 5.0:
            return signals

        # ── C4: RSI tại pivot1 phải < 50 (thực sự oversold) ──
        if rsi1 >= 50:
            return signals

        # ── C5: RSI tại pivot2 < 58 (chưa phục hồi hoàn toàn) ──
        if rsi2 >= 58:
            return signals

        # ── C6: MACD histogram higher low — BẮT BUỘC ──
        if hist2 <= hist1:
            return signals

        # ── C7: hist1 phải âm (pivot1 trong vùng MACD bearish) ──
        if hist1 >= 0:
            return signals

        # ── C8: MACD hist đang cải thiện (2 bars gần nhất) ──
        h = hist_series
        if h.iloc[-1] <= h.iloc[-2]:
            return signals
        macd_3bar_up = (h.iloc[-1] > h.iloc[-2] > h.iloc[-3])

        # ── C9: RSI hiện tại trong vùng phục hồi ──
        rsi_now = float(rsi_series.iloc[-1])
        if not (30 <= rsi_now <= 68):
            return signals

        # ── C10: Recovery từ pivot2 (0.5%–25%) ──
        current_close = float(close_series.iloc[-1])
        recovery_pct  = (current_close - p2_price) / p2_price * 100
        if recovery_pct < 0.5 or recovery_pct > 25.0:
            return signals

        # ── Volume tối thiểu: chỉ lọc cp có thanh khoản thực sự ──
        # Tránh tín hiệu từ cp có volume quá thấp → dễ bị méo bởi 1-2 phiên bất thường
        avg_vol_20 = float(df['Volume'].tail(20).mean())
        if avg_vol_20 < 200_000:   # < 200k cp/ngày = quá ít thanh khoản
            return signals

        # ── C11: Entry / SL / TP và R/R ──
        entry_price = current_close

        # SL: lấy GIÁ TRỊ LỚN HƠN giữa 2 cách tính:
        #   a) 3% dưới đáy tuyệt đối (p2) → anchor vào structure
        #   b) 7% dưới entry hiện tại   → tránh SL quá xa khi đã hồi nhiều
        # Ví dụ VJC: max(148×0.97=143.6, 166.9×0.93=155.2) = 155.2 → R/R hợp lý
        stop_loss   = max(p2_price * 0.97, entry_price * 0.93)

        # TP: 15% từ entry (tăng từ 12% để phù hợp với divergence recovery trade)
        take_profit = entry_price * 1.15

        risk        = entry_price - stop_loss
        if risk <= 0:
            return signals
        risk_reward = (take_profit - entry_price) / risk
        if risk_reward < 1.5:
            return signals

        # ════════════════════════════════
        # STRENGTH SCORING
        # ════════════════════════════════
        strength = 62   # Base — đã pass tất cả điều kiện AND

        # RSI divergence margin
        if rsi_diff >= 12:
            strength += 13
        elif rsi_diff >= 8:
            strength += 10
        elif rsi_diff >= 5:
            strength += 6
        else:
            strength += 3

        # MACD hist improvement tại pivot (hist2 ít âm hơn hist1 bao nhiêu %)
        if hist1 != 0:
            hist_impr = (hist2 - hist1) / abs(hist1)
            if hist_impr >= 0.5:
                strength += 10
            elif hist_impr >= 0.25:
                strength += 6
            elif hist_impr >= 0.1:
                strength += 3

        # RSI tại pivot1 rất thấp → oversold mạnh
        if rsi1 < 25:
            strength += 10
        elif rsi1 < 32:
            strength += 7
        elif rsi1 < 40:
            strength += 4

        # RSI tại pivot2 cũng còn thấp → vẫn còn dư địa
        if rsi2 < 35:
            strength += 8
        elif rsi2 < 45:
            strength += 4

        # Volume tăng → xác nhận lực cầu (dùng lại avg_vol_20 đã tính ở trên)
        if df['Volume'].iloc[-1] > avg_vol_20 * 1.2:
            strength += 8
        elif df['Volume'].iloc[-1] > avg_vol_20:
            strength += 4

        # MACD hist improving 3 phiên liên tiếp → momentum mạnh hơn
        if macd_3bar_up:
            strength += 8

        # R/R cao
        if risk_reward >= 2.5:
            strength += 5
        elif risk_reward >= 2.0:
            strength += 3

        # Entry gần đáy → R/R tốt hơn
        if recovery_pct <= 5.0:
            strength += 6
        elif recovery_pct <= 10.0:
            strength += 3

        is_priority = strength >= 78

        stock_type = get_stock_type(ticker)

        signal = {
            'ticker':      ticker,
            'strategy':    'RSI_MACD_DIV',
            'action':      'BUY',
            'entry_price': float(entry_price),
            'stop_loss':   float(stop_loss),
            'take_profit': float(take_profit),
            'risk_reward': float(round(risk_reward, 2)),
            'strength':    int(strength),
            'is_priority': int(is_priority),
            'stock_type':  stock_type,
            'rsi':         float(round(rsi_now, 1)),
            'date':        get_last_trading_day()
        }

        signals.append(signal)
        logger.info(
            f"✓ RSI_MACD_DIV {ticker}: {strength}% "
            f"[RSI: {rsi1:.1f}→{rsi2:.1f} (+{rsi_diff:.1f}pt) | "
            f"HIST: {hist1:.3f}→{hist2:.3f} | "
            f"RSI_now={rsi_now:.1f} | Rec={recovery_pct:.1f}% | "
            f"p2={bars_since_p2}bars_ago | {'3-bar' if macd_3bar_up else '2-bar'}]"
        )

    except Exception as e:
        logger.error(f"RSI_MACD_DIV error {ticker}: {str(e)}")

    return signals


def check_divergence_fb_strategy(df, ticker):
    """
    Strategy 3: Divergence + Fake Breakdown (DIVERGENCE_FB)
    Fixes vs original code:
      Bug1: Pivot via v4 approach (absolute-min + RSI-min), not is_pivot_low(left=3)
      Bug2: fake_break is SCORE BONUS (+10), not mandatory filter
      Bug3: Data 250 cal days / N>=160 bars
      Bug4: SL = max(p2_low*0.97, entry*0.93)
    """
    signals = []
    try:
        N = len(df)
        if N < 160:
            return signals

        df = df.copy()
        df['RSI']   = calculate_rsi(df)
        df['EMA20'] = calculate_ema(df, 20)
        df['EMA50'] = calculate_ema(df, 50)
        macd_line, signal_line, histogram = calculate_macd(df)
        df['MACD_HIST'] = histogram

        if pd.isna(df['RSI'].iloc[-1]) or pd.isna(df['MACD_HIST'].iloc[-1]):
            return signals

        close_series = df['Close']
        low_series   = df['Low']
        rsi_series   = df['RSI']
        hist_series  = df['MACD_HIST']

        avg_vol_20 = float(df['Volume'].tail(20).mean())
        if avg_vol_20 < 200_000:
            return signals

        # PIVOT 2: absolute price min in last 5-45 bars
        p2_start = max(0, N - 45); p2_end = N - 3
        if p2_end <= p2_start: return signals
        p2_local = int(close_series.iloc[p2_start:p2_end].values.argmin())
        p2_idx   = p2_start + p2_local
        p2_price = float(close_series.iloc[p2_idx])
        p2_low   = float(low_series.iloc[p2_idx])
        bars_p2  = N - 1 - p2_idx
        if bars_p2 < 3 or bars_p2 > 45: return signals

        # PIVOT 1: RSI min in bars 45-160 from end
        p1_start = max(0, N - 160); p1_end = max(0, N - 45)
        if p1_end <= p1_start + 5: return signals
        p1_local = int(rsi_series.iloc[p1_start:p1_end].values.argmin())
        p1_idx   = p1_start + p1_local
        p1_price = float(close_series.iloc[p1_idx])

        rsi1  = indicator_at_pivot(rsi_series,  p1_idx, window=3, use_min=True)
        rsi2  = indicator_at_pivot(rsi_series,  p2_idx, window=3, use_min=True)
        hist1 = indicator_at_pivot(hist_series, p1_idx, window=3, use_min=True)
        hist2 = indicator_at_pivot(hist_series, p2_idx, window=3, use_min=True)

        if any(pd.isna(v) for v in [rsi1, rsi2, hist1, hist2]): return signals

        # C1: RSI higher low >= 5pt
        rsi_diff = rsi2 - rsi1
        if rsi_diff < 5.0: return signals

        # C2: MACD hist higher low (both must be negative at pivots)
        if hist2 <= hist1 or hist1 >= 0: return signals

        # C3: Price lower low >= 1.5%
        if p2_price >= p1_price * 0.985: return signals

        # C4: Gap >= 20 bars
        if (p2_idx - p1_idx) < 20: return signals

        # C5: rsi1 < 50  C6: rsi2 < 60
        if rsi1 >= 50 or rsi2 >= 60: return signals

        # C7: MACD hist improving 2 bars
        h = hist_series
        if h.iloc[-1] <= h.iloc[-2]: return signals
        macd_3bar_up = (h.iloc[-1] > h.iloc[-2] > h.iloc[-3])

        # C8: RSI now <= 72
        rsi_now = float(rsi_series.iloc[-1])
        if rsi_now > 72: return signals

        # C9: EMA20 trigger — BONUS (không mandatory)
        # Mandatory sẽ block GEX (37.05 < EMA20 37.73) dù divergence rõ ràng
        # Giải pháp: EMA20 cross = strong score bonus (+15), còn tiếp cận EMA20 = bonus nhỏ (+8)
        ema20_now     = float(df['EMA20'].iloc[-1])
        current_close = float(close_series.iloc[-1])
        ema50_now     = float(df['EMA50'].iloc[-1])

        above_ema20 = current_close > ema20_now     # đã vượt EMA20 → tín hiệu mạnh
        near_ema20  = current_close > ema20_now * 0.97  # trong vòng 3% dưới EMA20 → pre-trigger

        # Nếu giá vẫn nằm xa bên dưới EMA20 (>3%) VÀ dưới EMA50 → downtrend mạnh, bỏ qua
        if not near_ema20 and current_close < ema50_now:
            return signals

        # C10: Recovery 0.5-30%
        recovery_pct = (current_close - p2_price) / p2_price * 100
        if recovery_pct < 0.5 or recovery_pct > 30.0: return signals

        # C11/12: SL/TP/R/R
        entry_price = current_close
        stop_loss   = max(p2_low * 0.97, entry_price * 0.93)
        take_profit = entry_price * 1.15
        risk        = entry_price - stop_loss
        if risk <= 0: return signals
        risk_reward = (take_profit - entry_price) / risk
        if risk_reward < 1.5: return signals

        # FAKE BREAKDOWN - bonus score only, not mandatory
        fake_break = False; fb_score = 0
        try:
            if p2_idx >= 20:
                support     = float(low_series.iloc[max(0, p2_idx-20):p2_idx].min())
                broke_below = p2_low < support
                if broke_below:
                    lookahead   = min(4, N - p2_idx - 1)
                    no_follow   = all(close_series.iloc[p2_idx+j] >= close_series.iloc[p2_idx] for j in range(1, lookahead+1))
                    rsi_hold    = rsi_series.iloc[p2_idx] >= rsi_series.iloc[max(0,p2_idx-5):p2_idx].min()
                    vol_spike_p2 = float(df['Volume'].iloc[p2_idx]) > avg_vol_20 * 1.5
                    fb_score    = broke_below*2 + no_follow*2 + rsi_hold*2 + vol_spike_p2*2
                    fake_break  = fb_score >= 5
        except Exception:
            pass

        # STRENGTH SCORING
        strength = 65
        if rsi_diff >= 15:    strength += 12
        elif rsi_diff >= 10:  strength += 8
        elif rsi_diff >= 7:   strength += 5
        else:                 strength += 2
        if hist1 != 0:
            hi = (hist2 - hist1) / abs(hist1)
            if hi >= 0.5:    strength += 10
            elif hi >= 0.25: strength += 6
            elif hi >= 0.1:  strength += 3
        if rsi1 < 25:    strength += 10
        elif rsi1 < 32:  strength += 7
        elif rsi1 < 40:  strength += 4
        if rsi2 < 38:    strength += 6
        elif rsi2 < 48:  strength += 3
        if macd_3bar_up: strength += 8
        if fake_break:   strength += 10

        # EMA20 trigger bonus (thay vì mandatory)
        if above_ema20:   strength += 15   # đã vượt EMA20 → xác nhận đảo chiều mạnh
        elif near_ema20:  strength += 8    # tiếp cận EMA20 → pre-trigger, vẫn có điểm
        if df['Volume'].iloc[-1] > avg_vol_20 * 1.5:   strength += 8
        elif df['Volume'].iloc[-1] > avg_vol_20 * 1.2: strength += 4
        if risk_reward >= 2.5:   strength += 5
        elif risk_reward >= 2.0: strength += 3
        if recovery_pct <= 10.0:   strength += 5
        elif recovery_pct <= 20.0: strength += 2

        is_priority = strength >= 78
        stock_type  = get_stock_type(ticker)

        signal = {
            'ticker':      ticker,
            'strategy':    'DIVERGENCE_FB',
            'action':      'BUY',
            'entry_price': float(entry_price),
            'stop_loss':   float(stop_loss),
            'take_profit': float(take_profit),
            'risk_reward': float(round(risk_reward, 2)),
            'strength':    int(strength),
            'is_priority': int(is_priority),
            'stock_type':  stock_type,
            'rsi':         float(round(rsi_now, 1)),
            'date':        get_last_trading_day()
        }
        signals.append(signal)
        fb_tag = f"FB+{fb_score}" if fake_break else "no-FB"
        logger.info(
            f"✓ DIVERGENCE_FB {ticker}: {strength}% "
            f"[RSI: {rsi1:.1f}->{rsi2:.1f} (+{rsi_diff:.1f}pt) | "
            f"HIST: {hist1:.3f}->{hist2:.3f} | "
            f"EMA20={ema20_now:.1f} | Rec={recovery_pct:.1f}% | {fb_tag}]"
        )

    except Exception as e:
        logger.error(f"DIVERGENCE_FB error {ticker}: {str(e)}")

    return signals


def init_database():
    """Initialize database using SQLAlchemy (works with SQLite and PostgreSQL)"""
    try:
        with engine.connect() as conn:
            # Create table if not exists
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
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
            '''))
            conn.commit()
        
        logger.info("✓ Database initialized")
        return True
        
    except Exception as e:
        logger.error(f"DB error: {str(e)}")
        return False

def save_signals_to_db(signals):
    """Save signals using SQLAlchemy (works with SQLite and PostgreSQL)"""
    try:
        with engine.connect() as conn:
            # Delete old signals
            conn.execute(text('DELETE FROM signals'))
            
            # Insert new signals
            for signal in signals:
                conn.execute(text('''
                    INSERT INTO signals (
                        ticker, strategy, entry_price, stop_loss, take_profit,
                        risk_reward, strength, is_priority, stock_type, rsi, date, action
                    ) VALUES (
                        :ticker, :strategy, :entry_price, :stop_loss, :take_profit,
                        :risk_reward, :strength, :is_priority, :stock_type, :rsi, :date, :action
                    )
                '''), {
                    'ticker': signal['ticker'],
                    'strategy': signal['strategy'],
                    'entry_price': signal['entry_price'],
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'risk_reward': signal['risk_reward'],
                    'strength': signal['strength'],
                    'is_priority': signal['is_priority'],
                    'stock_type': signal['stock_type'],
                    'rsi': signal['rsi'],
                    'date': signal['date'],
                    'action': signal['action']
                })
            
            conn.commit()
        
        logger.info(f"✓ Saved {len(signals)} signals")
        return True
        
    except Exception as e:
        logger.error(f"Save error: {str(e)}")
        return False

def scan_all_stocks():
    """Scan stocks - PRIORITY SIGNALS ONLY"""
    logger.info("=" * 60)
    logger.info("Starting scan...")
    logger.info(f"Date: {get_last_trading_day()}")
    logger.info(f"Stocks: {len(WATCHLIST_172)} (high-liquidity watchlist)")
    logger.info("=" * 60)
    
    init_database()
    
    all_signals = []
    processed = 0
    failed = 0
    breadth_data = []  # Thu thập dữ liệu breadth cho Market Risk Analysis
    
    for ticker in TOP_343_STOCKS:
        try:
            logger.info(f"Processing {ticker} ({processed + 1}/{len(TOP_343_STOCKS)})...")
            
            df = get_stock_data(ticker, days=250)
            
            if df is None or len(df) < 160:
                logger.warning(f"Skip {ticker}")
                failed += 1
                time.sleep(2)
                continue
            
            pullback  = check_pullback_strategy(df, ticker)
            ema_cross = check_ema_cross_strategy(df, ticker)
            div_fb    = check_divergence_fb_strategy(df, ticker)

            # Thu thập closes cho Market Breadth Analysis
            try:
                closes_list = df['Close'].tolist()
                if len(closes_list) >= 2:
                    breadth_data.append({'ticker': ticker, 'closes': closes_list})
            except:
                pass

            # Priority only + dedup: mỗi ticker chỉ lấy signal mạnh nhất
            tickers_in_batch = {s['ticker'] for s in all_signals}

            for signal in pullback + ema_cross + div_fb:
                if signal['is_priority'] == 1:
                    if signal['ticker'] not in tickers_in_batch:
                        all_signals.append(signal)
                        tickers_in_batch.add(signal['ticker'])
                    else:
                        # Nếu ticker đã có, giữ signal có strength cao hơn
                        existing = next(s for s in all_signals if s['ticker'] == signal['ticker'])
                        if signal['strength'] > existing['strength']:
                            all_signals.remove(existing)
                            all_signals.append(signal)
            
            processed += 1
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error {ticker}: {str(e)}")
            failed += 1
            time.sleep(2)
    
    logger.info("=" * 60)
    logger.info("COMPLETE")
    logger.info(f"Processed: {processed}/{len(TOP_343_STOCKS)}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Signals: {len(all_signals)}")
    logger.info("=" * 60)
    
    # ── Thu thập Market Breadth Data ──
    if breadth_data:
        try:
            logger.info(f"\n📊 Collecting breadth data from {len(breadth_data)} stocks...")
            # Import here to avoid circular import issues
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from market_risk_analysis import collect_breadth_data
            collect_breadth_data(breadth_data)
        except ImportError:
            # Fallback: save breadth data directly if module not found
            logger.warning("market_risk_analysis module not found, saving breadth directly...")
            advance = decline = unchanged = above_ma20 = total = 0
            for item in breadth_data:
                closes = item.get('closes', [])
                if len(closes) < 2:
                    continue
                total += 1
                if closes[-1] > closes[-2]:
                    advance += 1
                elif closes[-1] < closes[-2]:
                    decline += 1
                else:
                    unchanged += 1
                if len(closes) >= 20:
                    ma20 = sum(closes[-20:]) / 20
                    if closes[-1] > ma20:
                        above_ma20 += 1
            
            breadth_result = {
                'date': get_last_trading_day(),
                'total': total, 'advance': advance, 'decline': decline,
                'unchanged': unchanged, 'above_ma20': above_ma20,
                'above_ma20_pct': round(above_ma20 / total * 100, 1) if total > 0 else 0,
                'generated_at': datetime.now().isoformat(),
            }
            breadth_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'market_breadth_eod.json')
            with open(breadth_path, 'w', encoding='utf-8') as f:
                json.dump(breadth_result, f, ensure_ascii=False, indent=2)
            logger.info(f"📊 Breadth saved: {advance} tăng / {decline} giảm / MA20: {above_ma20}/{total}")
        except Exception as e:
            logger.error(f"Breadth collection error: {e}")
    
    if len(all_signals) > 0:
        save_signals_to_db(all_signals)
        
        pullback_cnt  = len([s for s in all_signals if s['strategy'] == 'PULLBACK'])
        ema_cross_cnt = len([s for s in all_signals if s['strategy'] == 'EMA_CROSS'])
        div_fb_cnt    = len([s for s in all_signals if s['strategy'] == 'DIVERGENCE_FB'])
        priority_cnt  = len([s for s in all_signals if s['is_priority'] == 1])

        logger.info(f"PULLBACK: {pullback_cnt}")
        logger.info(f"EMA_CROSS: {ema_cross_cnt}")
        logger.info(f"DIVERGENCE_FB: {div_fb_cnt}")
        logger.info(f"Total priority: {priority_cnt}")
        
        logger.info("\nTop 5:")
        sorted_sigs = sorted(all_signals, key=lambda x: x['strength'], reverse=True)[:5]
        for i, sig in enumerate(sorted_sigs, 1):
            logger.info(f"{i}. {sig['ticker']} - {sig['strategy']} - {sig['strength']}%")
    else:
        logger.warning("No signals")
    
    return all_signals


if __name__ == "__main__":
    signals = scan_all_stocks()
    logger.info(f"\n✓ Done. {len(signals)} signals")
