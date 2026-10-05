"""
AI Advisor - Daily Signal Scanner
Version: 5.0 (Yahoo Finance — không cần vnstock)
THAY ĐỔI DUY NHẤT so với bản gốc:
  - Bỏ `from vnstock import Quote`
  - get_stock_data() dùng Yahoo Finance thay TCBS
  - process_dataframe() KHÔNG nhân ×1000 (Yahoo trả về VND đầy đủ)
  - init_database() compatible với cả SQLite và PostgreSQL
  - Tất cả logic strategies, scoring, breadth, watchlist GIỮ NGUYÊN 100%
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
import requests

# SQLAlchemy for database (works with both SQLite and PostgreSQL)
from sqlalchemy import create_engine, text, Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE SETUP
# ============================================================
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

try:
    engine = create_engine(DATABASE_URL)
    logger.info(f"✓ Database connected: {DATABASE_URL.split('@')[0]}...")
except Exception as e:
    logger.error(f"✗ Database connection failed: {e}")
    raise

Session = sessionmaker(bind=engine)

# ============================================================
# STOCK LIST
# ============================================================
WATCHLIST_172 = [
    # ── TIER 1: VN30 + Blue Chips (43 mã) ─────────────────────────────
    'VCB', 'BID', 'CTG', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB',
    'STB', 'MSN', 'FPT', 'SSI', 'GAS', 'PLX', 'MWG', 'VJC', 'HDB', 'ACB',
    'VRE', 'BCM', 'POW', 'SAB', 'SHB', 'LPB', 'VIB', 'EIB', 'BVH', 'GVR',
    'TPB', 'NVL', 'KDH', 'DGC', 'REE', 'VCI', 'HVN', 'DIG', 'GEX', 'VIX',
    'BSR', 'GMD', 'PNJ',

    # ── TIER 2: Large-Mid Cap HOSE (42 mã) ────────────────────────────
    'DPM', 'KBC', 'DXG', 'VPL', 'MSB', 'OCB', 'TCX',
    'HSG', 'DCM', 'HCM', 'VND', 'PC1', 'DGW', 'HDG', 'PVD', 'PVT', 'VTP',
    'SCS', 'TCH', 'NLG', 'CII', 'PDR', 'IDC', 'ANV', 'HAH', 'DBC', 'MCH',
    'CTD', 'HT1', 'VSC', 'BWE', 'PVS', 'VHC', 'SSB', 'FRT', 'ELC', 'BMI',
    'BSI', 'TV2', 'DPG', 'LCG', 'BAF',

    # ── TIER 3: Mid Cap HOSE chất lượng (48 mã) ───────────────────────
    'TNG', 'KSB', 'SBT', 'VCG', 'CTR', 'SZC', 'PHR', 'GEG', 'PTB', 'HAG',
    'HAX', 'CSV', 'TCM', 'CMG', 'PAN', 'NTL', 'GIL', 'EVF', 'NHA', 'NAF',
    'IDI', 'AAA', 'TLH', 'HBC', 'VPG', 'CRE', 'CSM', 'ASM', 'HHS', 'QCG',
    'PAC', 'TAL', 'KOS', 'SIP', 'ORS', 'SMC', 'DCL',

    # ── TIER 4: HNX thanh khoản cao (39 mã) ───────────────────────────
    'SHS', 'MBS', 'VFS', 'CEO', 'NVB', 'VCS', 'HUT', 'NDN', 'PLC', 'EVS',
    'PSI', 'VC3', 'BVS', 'BAB', 'TIG', 'APS', 'IPA', 'DXP', 'API', 'IDJ',
    'VC7', 'MIG', 'PGB', 'NRC', 'NAG',
]

VIP_EXTRA_TICKERS = [
    'IJC', 'SGB', 'VBB', 'BVB', 'NKG', 'VGT', 'SD9',
]
TOP_343_STOCKS = list(dict.fromkeys(WATCHLIST_172 + VIP_EXTRA_TICKERS))

BLUE_CHIP_STOCKS = [
    'VCB', 'BID', 'CTG', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB',
    'STB', 'MSN', 'FPT', 'SSI', 'GAS', 'PLX', 'MWG', 'VJC', 'HDB', 'ACB',
    'VRE', 'BCM', 'POW', 'SAB', 'SHB', 'LPB', 'VIB', 'EIB', 'BVH', 'GVR',
    'TPB', 'NVL', 'KDH', 'DGC', 'REE', 'VCI', 'HVN', 'DIG', 'GEX', 'VIX',
    'BSR', 'GMD', 'PNJ',
]

# HNX-listed stocks (suffix .HN thay vì .VN)
HNX_TICKERS = {
    'SHB', 'MBS', 'SHS', 'VCS', 'PVS', 'TNG', 'NDN', 'NVB', 'HUT', 'PLC',
    'EVS', 'PSI', 'VC3', 'BVS', 'BAB', 'TIG', 'APS', 'IPA', 'DXP', 'API',
    'IDJ', 'VC7', 'MIG', 'PGB', 'NRC', 'NAG', 'VFS', 'CEO', 'IJC', 'SGB',
    'VBB', 'BVB', 'VGT', 'SD9', 'ACB',
}


def get_stock_type(ticker):
    if ticker in BLUE_CHIP_STOCKS:
        return "Blue Chip"
    elif ticker in TOP_343_STOCKS:
        return "Mid Cap"
    else:
        return "Penny"

def get_top_343_stocks():
    logger.info(f"Using WATCHLIST_172: {len(WATCHLIST_172)} high-liquidity stocks")
    return TOP_343_STOCKS

def get_last_trading_day():
    today = datetime.now()
    if today.weekday() == 5:
        last_trading_day = today - timedelta(days=1)
    elif today.weekday() == 6:
        last_trading_day = today - timedelta(days=2)
    else:
        last_trading_day = today
    return last_trading_day.strftime('%Y-%m-%d')

# ============================================================
# DATA FETCHING — YAHOO FINANCE (thay vnstock)
# ============================================================
def _yahoo_fetch(symbol, max_retries=3):
    """Gọi Yahoo Finance API cho 1 symbol (e.g. 'VCB.VN')"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {'interval': '1d', 'range': '2y'}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            if r.status_code != 200:
                if attempt < max_retries - 1:
                    time.sleep(2)
                continue
            j = r.json()
            result = j.get('chart', {}).get('result', [])
            if not result:
                return None
            res = result[0]
            timestamps = res.get('timestamp', [])
            quotes = res['indicators']['quote'][0]
            df = pd.DataFrame({
                'time':   pd.to_datetime(timestamps, unit='s'),
                'open':   quotes.get('open', []),
                'high':   quotes.get('high', []),
                'low':    quotes.get('low', []),
                'close':  quotes.get('close', []),
                'volume': quotes.get('volume', []),
            })
            df = df.dropna(subset=['close'])
            df = df.sort_values('time').reset_index(drop=True)
            return df
        except Exception as e:
            logger.debug(f"{symbol} attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    return None

def get_stock_data(ticker, days=250, max_retries=3):
    """
    Lấy dữ liệu từ Yahoo Finance.
    Thử .VN trước (HOSE), fallback sang .HN (HNX) nếu không có data.
    """
    # Xác định exchange
    if ticker in HNX_TICKERS:
        suffixes = ['.HN', '.VN']
    else:
        suffixes = ['.VN', '.HN']

    df_raw = None
    for suffix in suffixes:
        symbol = ticker + suffix
        df_raw = _yahoo_fetch(symbol, max_retries)
        if df_raw is not None and len(df_raw) >= 50:
            logger.info(f"✓ Got {len(df_raw)} days for {ticker} ({symbol})")
            break

    if df_raw is None or len(df_raw) < 50:
        logger.warning(f"No data for {ticker}")
        return None

    return process_dataframe(df_raw, ticker)

def process_dataframe(df, ticker):
    """
    Chuẩn hóa DataFrame từ Yahoo Finance.
    Yahoo Finance VN đã trả về VND đầy đủ — KHÔNG nhân ×1000.
    """
    try:
        if df is None or len(df) == 0:
            return None

        # Map tên cột Yahoo → chuẩn
        column_mapping = {
            'time':   'Date',
            'open':   'Open',
            'high':   'High',
            'low':    'Low',
            'close':  'Close',
            'volume': 'Volume',
        }
        df = df.rename(columns=column_mapping)

        # Yahoo Finance VN trả về giá VND đầy đủ (e.g. 57300) — KHÔNG ×1000
        # (vnstock cũ trả về nghìn VND → cần ×1000, nhưng Yahoo thì không)

        required = ['Close', 'High', 'Low', 'Volume']
        missing = [col for col in required if col not in df.columns]
        if missing:
            logger.error(f"Missing {ticker}: {missing}")
            return None

        if 'Open' not in df.columns:
            df['Open'] = df['Close'].shift(1)

        if 'Date' in df.columns:
            df = df.set_index('Date')

        df = df.sort_index()
        df = df.dropna(subset=['Close', 'High', 'Low'])

        if len(df) < 50:
            logger.warning(f"Not enough {ticker}: {len(df)}")
            return None

        logger.info(f"✓ Processed {ticker}: {len(df)} rows, last close={df['Close'].iloc[-1]:,.0f}")
        return df

    except Exception as e:
        logger.error(f"Process error {ticker}: {str(e)}")
        return None

# ============================================================
# INDICATORS — GIỮ NGUYÊN 100% từ bản gốc
# ============================================================
def calculate_ema(data, period):
    return data['Close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 0.0001)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def find_pivot_lows(series, window=5, lookback=40):
    pivots = []
    start = max(window, len(series) - lookback)
    end = len(series) - 1
    for i in range(start, end):
        local_range = series.iloc[max(0, i - window): i + window + 1]
        if series.iloc[i] <= local_range.min() + 1e-9:
            if pivots and (i - pivots[-1][0]) < window:
                if series.iloc[i] < pivots[-1][1]:
                    pivots[-1] = (i, series.iloc[i])
            else:
                pivots.append((i, float(series.iloc[i])))
    return pivots

def indicator_at_pivot(series, idx, window=3, use_min=True):
    n = len(series)
    sl = series.iloc[max(0, idx - window): min(n, idx + window + 1)]
    if use_min:
        return float(sl.min())
    return float(series.iloc[idx])

# ============================================================
# STRATEGIES — GIỮ NGUYÊN 100% từ bản gốc
# ============================================================
def check_pullback_strategy(df, ticker):
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
            strength = min(100, strength)
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
            strength = min(100, strength)
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
    """Bullish Divergence Strategy (RSI AND MACD - Daily chart) v4"""
    signals = []
    try:
        N = len(df)
        if N < 160:
            return signals

        df = df.copy()
        df['RSI'] = calculate_rsi(df, 14)
        macd_line, signal_line, histogram = calculate_macd(df, fast=12, slow=26, signal=9)
        df['MACD_HIST'] = histogram

        if pd.isna(df['RSI'].iloc[-1]) or pd.isna(df['MACD_HIST'].iloc[-1]):
            return signals

        close_series = df['Close']
        rsi_series = df['RSI']
        hist_series = df['MACD_HIST']

        # PIVOT 2: absolute price min in last 5-45 bars
        p2_search_start = max(0, N - 45)
        p2_search_end = N - 3
        if p2_search_end <= p2_search_start:
            return signals

        p2_slice = close_series.iloc[p2_search_start: p2_search_end]
        p2_local = int(p2_slice.values.argmin())
        p2_idx = p2_search_start + p2_local
        p2_price = float(close_series.iloc[p2_idx])
        bars_since_p2 = N - 1 - p2_idx

        if bars_since_p2 < 3 or bars_since_p2 > 45:
            return signals

        # PIVOT 1: RSI min in bars 45-160 from end
        p1_search_start = max(0, N - 160)
        p1_search_end = max(0, N - 45)
        if p1_search_end <= p1_search_start + 5:
            return signals

        older_rsi = rsi_series.iloc[p1_search_start: p1_search_end]
        p1_local = int(older_rsi.values.argmin())
        p1_idx = p1_search_start + p1_local
        p1_price = float(close_series.iloc[p1_idx])

        rsi1 = indicator_at_pivot(rsi_series, p1_idx, window=3, use_min=True)
        rsi2 = indicator_at_pivot(rsi_series, p2_idx, window=3, use_min=False)
        hist1 = indicator_at_pivot(hist_series, p1_idx, window=3, use_min=True)
        hist2 = indicator_at_pivot(hist_series, p2_idx, window=3, use_min=True)

        if any(pd.isna(v) for v in [rsi1, rsi2, hist1, hist2]):
            return signals

        # C1: Price lower low >= 1.5%
        if p2_price >= p1_price * 0.985:
            return signals
        # C2: Gap >= 20 bars
        if (p2_idx - p1_idx) < 20:
            return signals
        # C3: RSI higher low >= 5pt
        rsi_diff = rsi2 - rsi1
        if rsi_diff < 5.0:
            return signals
        # C4: RSI at pivot1 < 50
        if rsi1 >= 50:
            return signals
        # C5: RSI at pivot2 < 58
        if rsi2 >= 58:
            return signals
        # C6: MACD hist higher low
        if hist2 <= hist1:
            return signals
        # C7: hist1 < 0
        if hist1 >= 0:
            return signals
        # C8: MACD hist improving
        h = hist_series
        if h.iloc[-1] <= h.iloc[-2]:
            return signals
        macd_3bar_up = (h.iloc[-1] > h.iloc[-2] > h.iloc[-3])
        # C9: RSI now 30-68
        rsi_now = float(rsi_series.iloc[-1])
        if not (30 <= rsi_now <= 68):
            return signals
        # C10: Recovery 0.5-25%
        current_close = float(close_series.iloc[-1])
        recovery_pct = (current_close - p2_price) / p2_price * 100
        if recovery_pct < 0.5 or recovery_pct > 25.0:
            return signals

        avg_vol_20 = float(df['Volume'].tail(20).mean())
        if avg_vol_20 < 200_000:
            return signals

        # C11: SL/TP/R/R
        entry_price = current_close
        stop_loss = max(p2_price * 0.97, entry_price * 0.93)
        take_profit = entry_price * 1.15
        risk = entry_price - stop_loss
        if risk <= 0:
            return signals
        risk_reward = (take_profit - entry_price) / risk
        if risk_reward < 1.5:
            return signals

        # STRENGTH SCORING
        strength = 62
        if rsi_diff >= 12:    strength += 13
        elif rsi_diff >= 8:   strength += 10
        elif rsi_diff >= 5:   strength += 6
        else:                 strength += 3

        if hist1 != 0:
            hist_impr = (hist2 - hist1) / abs(hist1)
            if hist_impr >= 0.5:   strength += 10
            elif hist_impr >= 0.25: strength += 6
            elif hist_impr >= 0.1: strength += 3

        if rsi1 < 25:    strength += 10
        elif rsi1 < 32:  strength += 7
        elif rsi1 < 40:  strength += 4

        if rsi2 < 35:    strength += 8
        elif rsi2 < 45:  strength += 4

        if df['Volume'].iloc[-1] > avg_vol_20 * 1.2:  strength += 8
        elif df['Volume'].iloc[-1] > avg_vol_20:        strength += 4

        if macd_3bar_up:   strength += 8
        if risk_reward >= 2.5: strength += 5
        elif risk_reward >= 2.0: strength += 3

        if recovery_pct <= 5.0:    strength += 6
        elif recovery_pct <= 10.0: strength += 3

        is_priority = strength >= 78
        strength = min(100, strength)
        stock_type = get_stock_type(ticker)

        signal = {
            'ticker': ticker,
            'strategy': 'RSI_MACD_DIV',
            'action': 'BUY',
            'entry_price': float(entry_price),
            'stop_loss': float(stop_loss),
            'take_profit': float(take_profit),
            'risk_reward': float(round(risk_reward, 2)),
            'strength': int(strength),
            'is_priority': int(is_priority),
            'stock_type': stock_type,
            'rsi': float(round(rsi_now, 1)),
            'date': get_last_trading_day()
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
    """Strategy: Divergence + Fake Breakdown (DIVERGENCE_FB)"""
    signals = []
    try:
        N = len(df)
        if N < 160:
            return signals

        df = df.copy()
        df['RSI'] = calculate_rsi(df)
        df['EMA20'] = calculate_ema(df, 20)
        df['EMA50'] = calculate_ema(df, 50)
        macd_line, signal_line, histogram = calculate_macd(df)
        df['MACD_HIST'] = histogram

        if pd.isna(df['RSI'].iloc[-1]) or pd.isna(df['MACD_HIST'].iloc[-1]):
            return signals

        close_series = df['Close']
        low_series = df['Low']
        rsi_series = df['RSI']
        hist_series = df['MACD_HIST']

        avg_vol_20 = float(df['Volume'].tail(20).mean())
        if avg_vol_20 < 200_000:
            return signals

        # PIVOT 2: absolute price min in last 5-45 bars
        p2_start = max(0, N - 45); p2_end = N - 3
        if p2_end <= p2_start: return signals
        p2_local = int(close_series.iloc[p2_start:p2_end].values.argmin())
        p2_idx = p2_start + p2_local
        p2_price = float(close_series.iloc[p2_idx])
        p2_low = float(low_series.iloc[p2_idx])
        bars_p2 = N - 1 - p2_idx
        if bars_p2 < 3 or bars_p2 > 45: return signals

        # PIVOT 1: RSI min in bars 45-160 from end
        p1_start = max(0, N - 160); p1_end = max(0, N - 45)
        if p1_end <= p1_start + 5: return signals
        p1_local = int(rsi_series.iloc[p1_start:p1_end].values.argmin())
        p1_idx = p1_start + p1_local
        p1_price = float(close_series.iloc[p1_idx])

        rsi1 = indicator_at_pivot(rsi_series, p1_idx, window=3, use_min=True)
        rsi2 = indicator_at_pivot(rsi_series, p2_idx, window=3, use_min=False)
        hist1 = indicator_at_pivot(hist_series, p1_idx, window=3, use_min=True)
        hist2 = indicator_at_pivot(hist_series, p2_idx, window=3, use_min=True)

        if any(pd.isna(v) for v in [rsi1, rsi2, hist1, hist2]): return signals

        rsi_diff = rsi2 - rsi1
        if rsi_diff < 5.0: return signals
        if hist2 <= hist1 or hist1 >= 0: return signals
        if p2_price >= p1_price * 0.985: return signals
        if (p2_idx - p1_idx) < 20: return signals
        if rsi1 >= 50 or rsi2 >= 65: return signals

        h = hist_series
        macd_4bar_trend = h.iloc[-1] > h.iloc[-4]
        macd_1bar_up = h.iloc[-1] > h.iloc[-2]
        if not macd_4bar_trend: return signals
        macd_3bar_up = (h.iloc[-1] > h.iloc[-2] > h.iloc[-3])

        macd_line_now = float(macd_line.iloc[-1])
        signal_line_now = float(signal_line.iloc[-1])
        hist_positive = h.iloc[-1] > 0
        macd_line_above = macd_line_now > signal_line_now

        rsi_now = float(rsi_series.iloc[-1])
        if not (30 <= rsi_now <= 75): return signals

        ema20_now = float(df['EMA20'].iloc[-1])
        current_close = float(close_series.iloc[-1])
        ema50_now = float(df['EMA50'].iloc[-1])

        above_ema20 = current_close > ema20_now
        near_ema20 = current_close > ema20_now * 0.97

        if not near_ema20 and current_close < ema50_now:
            return signals

        recovery_pct = (current_close - p2_price) / p2_price * 100
        if recovery_pct < 0.5 or recovery_pct > 30.0: return signals

        entry_price = current_close
        stop_loss = max(p2_low * 0.97, entry_price * 0.93)
        take_profit = entry_price * 1.15
        risk = entry_price - stop_loss
        if risk <= 0: return signals
        risk_reward = (take_profit - entry_price) / risk
        if risk_reward < 1.5: return signals

        # Fake breakdown bonus
        fake_break = False; fb_score = 0
        try:
            if p2_idx >= 20:
                support = float(low_series.iloc[max(0, p2_idx-20):p2_idx].min())
                broke_below = p2_low < support
                if broke_below:
                    lookahead = min(4, N - p2_idx - 1)
                    no_follow = all(close_series.iloc[p2_idx+j] >= close_series.iloc[p2_idx] for j in range(1, lookahead+1))
                    rsi_hold = rsi_series.iloc[p2_idx] >= rsi_series.iloc[max(0,p2_idx-5):p2_idx].min()
                    vol_spike_p2 = float(df['Volume'].iloc[p2_idx]) > avg_vol_20 * 1.5
                    fb_score = broke_below*2 + no_follow*2 + rsi_hold*2 + vol_spike_p2*2
                    fake_break = fb_score >= 5
        except Exception:
            pass

        # STRENGTH SCORING
        strength = 40
        if rsi_diff >= 20:   strength += 16
        elif rsi_diff >= 15: strength += 13
        elif rsi_diff >= 10: strength += 10
        elif rsi_diff >= 7:  strength += 7
        else:                strength += 4

        if hist1 != 0:
            hi = (hist2 - hist1) / abs(hist1)
            if hi >= 0.8:    strength += 12
            elif hi >= 0.5:  strength += 9
            elif hi >= 0.3:  strength += 6
            elif hi >= 0.1:  strength += 3

        if rsi1 < 20:   strength += 8
        elif rsi1 < 28: strength += 6
        elif rsi1 < 35: strength += 4
        elif rsi1 < 42: strength += 2

        if rsi2 < 35:   strength += 4
        elif rsi2 < 45: strength += 2
        elif rsi2 < 55: strength += 1

        if hist_positive:     strength += 10
        elif macd_3bar_up:    strength += 5
        elif macd_4bar_trend: strength += 2

        if macd_line_above:   strength += 5
        if above_ema20:       strength += 3
        elif near_ema20:      strength += 1

        if fake_break:        strength += 4
        if risk_reward >= 2.5: strength += 2
        elif risk_reward >= 2.0: strength += 1
        if recovery_pct <= 8:  strength += 1

        is_priority = strength >= 62
        strength = min(100, strength)
        stock_type = get_stock_type(ticker)

        signal = {
            'ticker': ticker,
            'strategy': 'DIVERGENCE_FB',
            'action': 'BUY',
            'entry_price': float(entry_price),
            'stop_loss': float(stop_loss),
            'take_profit': float(take_profit),
            'risk_reward': float(round(risk_reward, 2)),
            'strength': int(strength),
            'is_priority': int(is_priority),
            'stock_type': stock_type,
            'rsi': float(round(rsi_now, 1)),
            'date': get_last_trading_day()
        }
        signals.append(signal)
        fb_tag = f"FB+{fb_score}" if fake_break else "no-FB"
        macd_tag = f"hist+{h.iloc[-1]:.2f}" if hist_positive else f"hist{h.iloc[-1]:.2f}"
        logger.info(
            f"✓ DIVERGENCE_FB {ticker}: {strength}% "
            f"[RSI: {rsi1:.1f}->{rsi2:.1f} (+{rsi_diff:.1f}pt) | "
            f"HIST: {hist1:.3f}->{hist2:.3f} | {macd_tag} | "
            f"EMA20={'above' if above_ema20 else 'near'} | Rec={recovery_pct:.1f}% | {fb_tag}]"
        )
    except Exception as e:
        logger.error(f"DIVERGENCE_FB error {ticker}: {str(e)}")
    return signals


# ============================================================
# DATABASE — init_database() fixed cho cả SQLite & PostgreSQL
# ============================================================
def init_database():
    try:
        is_postgres = 'postgresql' in DATABASE_URL or 'psycopg' in DATABASE_URL
        if is_postgres:
            ddl = '''
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
                    created_at TIMESTAMP DEFAULT NOW()
                )
            '''
        else:
            # SQLite
            ddl = '''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            '''
        with engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()
        logger.info("✓ Database initialized")
        return True
    except Exception as e:
        logger.error(f"DB error: {str(e)}")
        return False


def save_signals_to_db(signals):
    """Save signals — GIỮ NGUYÊN logic gốc (dedup theo ticker+date+action)"""
    try:
        with engine.connect() as conn:
            inserted = 0
            skipped = 0
            for signal in signals:
                existing = conn.execute(text('''
                    SELECT id FROM signals
                    WHERE ticker = :ticker
                      AND date  = :date
                      AND action = :action
                    LIMIT 1
                '''), {
                    'ticker': signal.get('ticker'),
                    'date':   signal.get('date'),
                    'action': signal.get('action', 'BUY'),
                }).fetchone()

                if existing:
                    skipped += 1
                    continue

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
                inserted += 1

            conn.commit()
        logger.info(f"✅ Signals: {inserted} inserted, {skipped} skipped (duplicate)")
        return True
    except Exception as e:
        logger.error(f"Save error: {str(e)}")
        return False


# ============================================================
# MAIN SCAN — GIỮ NGUYÊN logic gốc
# ============================================================
def scan_all_stocks():
    logger.info("=" * 60)
    logger.info("Starting scan...")
    logger.info(f"Date: {get_last_trading_day()}")
    logger.info(f"Stocks: {len(TOP_343_STOCKS)} (WATCHLIST_172 + VIP_EXTRA)")
    logger.info("=" * 60)

    init_database()

    all_signals = []
    processed = 0
    failed = 0
    breadth_data = []

    for ticker in TOP_343_STOCKS:
        try:
            logger.info(f"Processing {ticker} ({processed + 1}/{len(TOP_343_STOCKS)})...")

            df = get_stock_data(ticker, days=250)

            if df is None or len(df) < 160:
                logger.warning(f"Skip {ticker}")
                failed += 1
                time.sleep(1)
                continue

            pullback  = check_pullback_strategy(df, ticker)
            ema_cross = check_ema_cross_strategy(df, ticker)
            div_fb    = check_divergence_fb_strategy(df, ticker)

            # Breadth data collection
            try:
                closes_list = df['Close'].tolist()
                if len(closes_list) >= 2:
                    breadth_data.append({'ticker': ticker, 'closes': closes_list})
            except:
                pass

            # Collect signals (giữ nguyên logic dedup gốc)
            tickers_in_batch     = {s['ticker'] for s in all_signals if s.get('strategy') != 'DIVERGENCE_FB'}
            div_tickers_in_batch = {s['ticker'] for s in all_signals if s.get('strategy') == 'DIVERGENCE_FB'}

            for signal in pullback + ema_cross:
                if signal['is_priority'] == 1:
                    if signal['ticker'] not in tickers_in_batch:
                        all_signals.append(signal)
                        tickers_in_batch.add(signal['ticker'])
                    else:
                        existing = next(
                            (s for s in all_signals
                             if s['ticker'] == signal['ticker'] and s.get('strategy') != 'DIVERGENCE_FB'),
                            None
                        )
                        if existing and signal['strength'] > existing['strength']:
                            all_signals.remove(existing)
                            all_signals.append(signal)

            for signal in div_fb:
                if signal['is_priority'] == 1:
                    if signal['ticker'] not in div_tickers_in_batch:
                        all_signals.append(signal)
                        div_tickers_in_batch.add(signal['ticker'])
                    else:
                        existing = next(
                            (s for s in all_signals
                             if s['ticker'] == signal['ticker'] and s.get('strategy') == 'DIVERGENCE_FB'),
                            None
                        )
                        if existing and signal['strength'] > existing['strength']:
                            all_signals.remove(existing)
                            all_signals.append(signal)

            processed += 1
            time.sleep(1)  # Yahoo Finance: 1s thay vì 2s của vnstock

        except Exception as e:
            logger.error(f"Error {ticker}: {str(e)}")
            failed += 1
            time.sleep(1)

    logger.info("=" * 60)
    logger.info("COMPLETE")
    logger.info(f"Processed: {processed}/{len(TOP_343_STOCKS)}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Signals: {len(all_signals)}")
    logger.info("=" * 60)

    # Market Breadth
    if breadth_data:
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from market_risk_analysis import collect_breadth_data
            collect_breadth_data(breadth_data)
        except ImportError:
            logger.warning("market_risk_analysis module not found, saving breadth directly...")
            advance = decline = unchanged = above_ma20 = total = 0
            for item in breadth_data:
                closes = item.get('closes', [])
                if len(closes) < 2:
                    continue
                total += 1
                if closes[-1] > closes[-2]:   advance += 1
                elif closes[-1] < closes[-2]: decline += 1
                else:                          unchanged += 1
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
            logger.info(f"📊 Breadth: {advance} tăng / {decline} giảm / MA20: {above_ma20}/{total}")
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
