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
    logger.info(f"âœ“ Database connected: {DATABASE_URL.split('@')[0]}...")  # Log without password
except Exception as e:
    logger.error(f"âœ— Database connection failed: {e}")
    raise

# Create session maker
Session = sessionmaker(bind=engine)

# ============================================================
# STOCK LIST
# ============================================================

# ============================================================
# WATCHLIST 172 - Cá»• phiáº¿u Æ°u tiÃªn thanh khoáº£n cao
# TiÃªu chÃ­: avg volume > 200k cp/ngÃ y, loáº¡i bá» penny & illiquid
# Updated: 2026-04-02  |  172 mÃ£ unique
# ============================================================

WATCHLIST_172 = [
    # â”€â”€ TIER 1: VN30 + Blue Chips (43 mÃ£) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # avg volume > 3M cp/ngÃ y, trá»¥ cá»™t thá»‹ trÆ°á»ng
    'VCB', 'BID', 'CTG', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB',
    'STB', 'MSN', 'FPT', 'SSI', 'GAS', 'PLX', 'MWG', 'VJC', 'HDB', 'ACB',
    'VRE', 'BCM', 'POW', 'SAB', 'SHB', 'LPB', 'VIB', 'EIB', 'BVH', 'GVR',
    'TPB', 'NVL', 'KDH', 'DGC', 'REE', 'VCI', 'HVN', 'DIG', 'GEX', 'VIX',
    'BSR', 'GMD', 'PNJ',

    # â”€â”€ TIER 2: Large-Mid Cap HOSE (42 mÃ£) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # avg volume > 1M cp/ngÃ y
    'DPM', 'KBC', 'DXG', 'VPL', 'MSB', 'OCB', 'TCX',
    'HSG', 'DCM', 'HCM', 'VND', 'PC1', 'DGW', 'HDG', 'PVD', 'PVT', 'VTP',
    'SCS', 'TCH', 'NLG', 'CII', 'PDR', 'IDC', 'ANV', 'HAH', 'DBC', 'MCH',
    'CTD', 'HT1', 'VSC', 'BWE', 'PVS', 'VHC', 'SSB', 'FRT', 'ELC', 'BMI',
    'BSI', 'TV2', 'DPG', 'LCG', 'BAF',

    # â”€â”€ TIER 3: Mid Cap HOSE cháº¥t lÆ°á»£ng (48 mÃ£) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # avg volume 300kâ€“1M cp/ngÃ y, cÆ¡ báº£n tá»‘t
    'TNG', 'KSB', 'MSH', 'SBT', 'VCG', 'CTR', 'SZC', 'PHR', 'GEG', 'PTB',
    'HAX', 'FMC', 'CSV', 'TCM', 'CMG', 'PAN', 'SGN', 'NTL', 'GIL', 'VFC',
    'IDI', 'AAA', 'TLH', 'HBC', 'VPG', 'CRE', 'CSM', 'ASM', 'HHS', 'PDC',
    'PAC', 'TAL', 'KOS', 'SIP', 'ORS', 'CMX', 'NBB', 'SMC', 'DCL', 'QCG',
    'SJS', 'NAF', 'HAG', 'NHA', 'EVF', 'VHG', 'HAP', 'ASG',

    # â”€â”€ TIER 4: HNX thanh khoáº£n cao (39 mÃ£) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # avg volume > 200k cp/ngÃ y trÃªn HNX
    'SHS', 'MBS', 'VFS', 'CEO', 'NVB', 'VCS', 'HUT', 'NDN', 'PLC', 'EVS',
    'PSI', 'VC3', 'BVS', 'BAB', 'TIG', 'APS', 'IPA', 'DXP', 'TVS', 'LIG',
    'VHE', 'VC7', 'DTT', 'KSV', 'HLD', 'OCH', 'PVI', 'MIG', 'PGB', 'DHT',
    'API', 'NRC', 'MBG', 'SJE', 'INN', 'NAG', 'SD9', 'AMV', 'IDJ',
]

# DÃ¹ng WATCHLIST_172 cho scanner
TOP_343_STOCKS = WATCHLIST_172  # backward-compat alias
# Blue Chip = Tier 1 (43 mÃ£ vá»‘n hoÃ¡ lá»›n nháº¥t)
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
            quote = Quote(symbol=ticker, source='TCBS')
            
            # Get historical data
            df = quote.history(start=start_date, end=end_date)
            
            if df is None or len(df) == 0:
                logger.warning(f"No data for {ticker}")
                return None
            
            logger.info(f"âœ“ Got {len(df)} days for {ticker}")
            
            return process_dataframe(df, ticker)
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Detect rate limit errors
            is_rate_limit = any(phrase in error_msg for phrase in [
                'quÃ¡ nhiá»u request',
                'rate limit',
                'too many',
                'vui lÃ²ng thá»­ láº¡i'
            ])
            
            if is_rate_limit:
                wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
                logger.warning(f"âš ï¸ RATE LIMIT for {ticker}. Waiting {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                
                if attempt < max_retries - 1:
                    logger.info(f"ðŸ”„ Retrying {ticker}...")
                    continue  # Retry
                else:
                    logger.error(f"âœ— Max retries reached for {ticker}")
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
        
        # ðŸ”§ CRITICAL FIX: Convert from thousands VND to VND
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
        
        logger.info(f"âœ“ Processed {ticker}: {len(df)} rows")
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
    A pivot low is the lowest point within Â±window candles.
    
    Returns list of (index_position, value) tuples, sorted oldest â†’ newest.
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
    Get indicator value at a price pivot, using a small Â±window buffer
    to account for RSI/MACD lag vs price.
    use_min=True  â†’ return minimum value (for finding most oversold / most negative hist)
    use_min=False â†’ return value at exact index
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
            strength    = min(100, strength)   # cap display score
            
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
            logger.info(f"âœ“ PULLBACK {ticker}: {strength}%")
    
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
            strength    = min(100, strength)   # cap display score
            
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
            logger.info(f"âœ“ EMA_CROSS {ticker}: {strength}%")
    
    except Exception as e:
        logger.error(f"EMA Cross error {ticker}: {str(e)}")
    
    return signals

def check_rsi_macd_divergence_strategy(df, ticker):
    """
    Bullish Divergence Strategy (RSI AND MACD - Daily chart)
    Version 4 â€” Thuáº­t toÃ¡n pivot má»›i: ABSOLUTE MINIMUM thay vÃ¬ local-swing pivot

    â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    Váº¤N Äá»€ Cá»¦A V1-V3 (Ä‘Ã£ fix):
      - find_pivot_lows() dÃ¹ng "local minimum Â±window" â†’ bá» sÃ³t pivot1 khi giÃ¡
        giáº£m liÃªn tá»¥c (khÃ´ng cÃ³ bounce rÃµ giá»¯a 2 Ä‘Ã¡y, nhÆ° VJC, GEX)
      - lookback=60 quÃ¡ ngáº¯n â†’ pivot1 (50-80 bars ago) náº±m ngoÃ i vÃ¹ng search

    CÃCH TIáº¾P Cáº¬N Má»šI (Ä‘Ãºng vá»›i cÃ¡ch trader váº½ divergence trÃªn chart):
      pivot2 = ABSOLUTE price minimum trong 5-45 bars gáº§n nháº¥t
              â†’ Ä‘Ã¢y lÃ  Ä‘Ã¡y giÃ¡ thá»±c táº¿ mÃ  trader váº½ divergence
      pivot1 = Ä‘iá»ƒm cÃ³ RSI MINIMUM trong bars 45-130 trÆ°á»›c Ä‘Ã³
              â†’ ká»ƒ cáº£ khi giÃ¡ khÃ´ng cÃ³ bounce rÃµ, RSI váº«n cÃ³ Ä‘iá»ƒm oversold

    ÄÃ¢y chÃ­nh xÃ¡c lÃ  cÃ¡ch VJC vÃ  GEX Ä‘Æ°á»£c váº½ trÃªn chart:
      â€¢ GEX: RSI circle 1 (32.92) táº¡i Ä‘Ã¡y RSI cÅ© â†’ RSI circle 2 (47.89) táº¡i Ä‘Ã¡y giÃ¡ má»›i
      â€¢ VJC: RSI táº¡o higher low táº¡i Ä‘Ã¡y Feb 2026 so vá»›i Ä‘Ã¡y RSI thÃ¡ng 11/2025

    â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    ÄIá»€U KIá»†N Báº®T BUá»˜C (AND â€” táº¥t cáº£ pháº£i pass):
      C1.  Price LOWER LOW    : p2_price < p1_price Ã— 0.985  (giÃ¡ má»›i tháº¥p hÆ¡n â‰¥ 1.5%)
      C2.  Gap tá»‘i thiá»ƒu      : â‰¥ 20 bars giá»¯a pivot1 vÃ  pivot2
      C3.  RSI HIGHER LOW     : rsi2 > rsi1 + 3pt  (RSI phÃ¢n ká»³ rÃµ rÃ ng)
      C4.  RSI táº¡i pivot1     : rsi1 < 50  (pivot1 pháº£i trong vÃ¹ng oversold)
      C5.  RSI táº¡i pivot2     : rsi2 < 58  (pivot2 chÆ°a phá»¥c há»“i hoÃ n toÃ n)
      C6.  MACD hist HIGHER LOW: hist2 > hist1  (momentum phÃ¢n ká»³ â€” Báº®T BUá»˜C)
      C7.  hist1 < 0          : Ä‘Ã¡y cÅ© pháº£i trong vÃ¹ng MACD Ã¢m
      C8.  MACD hist improving: h[-1] > h[-2] (2 phiÃªn gáº§n nháº¥t Ä‘ang cáº£i thiá»‡n)
      C9.  RSI hiá»‡n táº¡i       : 30 â‰¤ rsi_now â‰¤ 68
      C10. Recovery           : 0.5% â‰¤ rec â‰¤ 25%  (Ä‘Ã£ há»“i phá»¥c, chÆ°a bá»©t quÃ¡ xa)
      C11. R/R                : â‰¥ 1.5
    â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    """
    signals = []

    try:
        N = len(df)
        # Cáº§n tá»‘i thiá»ƒu 160 bars:
        #   40 bars warmup (RSI14+MACD26+signal9 á»•n Ä‘á»‹nh)
        #   + 120 bars usable Ä‘á»ƒ p1 (~100 bars ago) cÃ³ RSI/MACD há»£p lá»‡
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

        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # PIVOT 2: ABSOLUTE PRICE MINIMUM trong 5-45 bars gáº§n nháº¥t
        # KhÃ´ng yÃªu cáº§u local swing low â€” chá»‰ cáº§n lÃ  Ä‘Ã¡y thá»±c táº¿ gáº§n Ä‘Ã¢y
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        p2_search_start = max(0, N - 45)
        p2_search_end   = N - 3          # cáº§n Ã­t nháº¥t 3 bars Ä‘á»ƒ xÃ¡c nháº­n há»“i phá»¥c
        if p2_search_end <= p2_search_start:
            return signals

        p2_slice = close_series.iloc[p2_search_start: p2_search_end]
        p2_local = int(p2_slice.values.argmin())
        p2_idx   = p2_search_start + p2_local
        p2_price = float(close_series.iloc[p2_idx])
        bars_since_p2 = N - 1 - p2_idx

        # pivot2 pháº£i cÃ¡ch today Ã­t nháº¥t 3 bars, nhiá»u nháº¥t 45 bars
        if bars_since_p2 < 3 or bars_since_p2 > 45:
            return signals

        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # PIVOT 1: RSI MINIMUM trong khoáº£ng 45-160 bars trÆ°á»›c today
        # Má»Ÿ rá»™ng tá»« 130â†’160 Ä‘á»ƒ cover pivot1 Nov 2025 (~100-110 bars ago)
        # Vá»›i fetch=250 cal days â†’ ~180 trading bars â†’ p1 náº±m cháº¯c trong usable range
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        p1_search_start = max(0, N - 160)
        p1_search_end   = max(0, N - 45)
        if p1_search_end <= p1_search_start + 5:
            return signals

        older_rsi = rsi_series.iloc[p1_search_start: p1_search_end]
        p1_local  = int(older_rsi.values.argmin())
        p1_idx    = p1_search_start + p1_local
        p1_price  = float(close_series.iloc[p1_idx])

        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # Láº¥y RSI vÃ  MACD hist táº¡i má»—i pivot (dÃ¹ng local min Â±3 bars Ä‘á»ƒ
        # handle RSI/MACD lag so vá»›i price)
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        rsi1  = indicator_at_pivot(rsi_series,  p1_idx, window=3, use_min=True)
        rsi2  = indicator_at_pivot(rsi_series,  p2_idx, window=3, use_min=False)  # exact RSI at price bottom
        hist1 = indicator_at_pivot(hist_series, p1_idx, window=3, use_min=True)
        hist2 = indicator_at_pivot(hist_series, p2_idx, window=3, use_min=True)

        if any(pd.isna(v) for v in [rsi1, rsi2, hist1, hist2]):
            return signals

        # â”€â”€ C1: Price lower low â‰¥ 1.5% â”€â”€
        if p2_price >= p1_price * 0.985:
            return signals

        # â”€â”€ C2: Gap tá»‘i thiá»ƒu 20 bars â”€â”€
        if (p2_idx - p1_idx) < 20:
            return signals

        # â”€â”€ C3: RSI higher low â‰¥ 5pt â€” Báº®T BUá»˜C â”€â”€
        # 5pt (tÄƒng tá»« 3pt) â†’ filter weak/noise divergence, giá»¯ láº¡i VJC (+8-20pt), GEX (+15pt)
        rsi_diff = rsi2 - rsi1
        if rsi_diff < 5.0:
            return signals

        # â”€â”€ C4: RSI táº¡i pivot1 pháº£i < 50 (thá»±c sá»± oversold) â”€â”€
        if rsi1 >= 50:
            return signals

        # â”€â”€ C5: RSI táº¡i pivot2 < 58 (chÆ°a phá»¥c há»“i hoÃ n toÃ n) â”€â”€
        if rsi2 >= 58:
            return signals

        # â”€â”€ C6: MACD histogram higher low â€” Báº®T BUá»˜C â”€â”€
        if hist2 <= hist1:
            return signals

        # â”€â”€ C7: hist1 pháº£i Ã¢m (pivot1 trong vÃ¹ng MACD bearish) â”€â”€
        if hist1 >= 0:
            return signals

        # â”€â”€ C8: MACD hist Ä‘ang cáº£i thiá»‡n (2 bars gáº§n nháº¥t) â”€â”€
        h = hist_series
        if h.iloc[-1] <= h.iloc[-2]:
            return signals
        macd_3bar_up = (h.iloc[-1] > h.iloc[-2] > h.iloc[-3])

        # â”€â”€ C9: RSI hiá»‡n táº¡i trong vÃ¹ng phá»¥c há»“i â”€â”€
        rsi_now = float(rsi_series.iloc[-1])
        if not (30 <= rsi_now <= 68):
            return signals

        # â”€â”€ C10: Recovery tá»« pivot2 (0.5%â€“25%) â”€â”€
        current_close = float(close_series.iloc[-1])
        recovery_pct  = (current_close - p2_price) / p2_price * 100
        if recovery_pct < 0.5 or recovery_pct > 25.0:
            return signals

        # â”€â”€ Volume tá»‘i thiá»ƒu: chá»‰ lá»c cp cÃ³ thanh khoáº£n thá»±c sá»± â”€â”€
        # TrÃ¡nh tÃ­n hiá»‡u tá»« cp cÃ³ volume quÃ¡ tháº¥p â†’ dá»… bá»‹ mÃ©o bá»Ÿi 1-2 phiÃªn báº¥t thÆ°á»ng
        avg_vol_20 = float(df['Volume'].tail(20).mean())
        if avg_vol_20 < 200_000:   # < 200k cp/ngÃ y = quÃ¡ Ã­t thanh khoáº£n
            return signals

        # â”€â”€ C11: Entry / SL / TP vÃ  R/R â”€â”€
        entry_price = current_close

        # SL: láº¥y GIÃ TRá»Š Lá»šN HÆ N giá»¯a 2 cÃ¡ch tÃ­nh:
        #   a) 3% dÆ°á»›i Ä‘Ã¡y tuyá»‡t Ä‘á»‘i (p2) â†’ anchor vÃ o structure
        #   b) 7% dÆ°á»›i entry hiá»‡n táº¡i   â†’ trÃ¡nh SL quÃ¡ xa khi Ä‘Ã£ há»“i nhiá»u
        # VÃ­ dá»¥ VJC: max(148Ã—0.97=143.6, 166.9Ã—0.93=155.2) = 155.2 â†’ R/R há»£p lÃ½
        stop_loss   = max(p2_price * 0.97, entry_price * 0.93)

        # TP: 15% tá»« entry (tÄƒng tá»« 12% Ä‘á»ƒ phÃ¹ há»£p vá»›i divergence recovery trade)
        take_profit = entry_price * 1.15

        risk        = entry_price - stop_loss
        if risk <= 0:
            return signals
        risk_reward = (take_profit - entry_price) / risk
        if risk_reward < 1.5:
            return signals

        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # STRENGTH SCORING
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        strength = 62   # Base â€” Ä‘Ã£ pass táº¥t cáº£ Ä‘iá»u kiá»‡n AND

        # RSI divergence margin
        if rsi_diff >= 12:
            strength += 13
        elif rsi_diff >= 8:
            strength += 10
        elif rsi_diff >= 5:
            strength += 6
        else:
            strength += 3

        # MACD hist improvement táº¡i pivot (hist2 Ã­t Ã¢m hÆ¡n hist1 bao nhiÃªu %)
        if hist1 != 0:
            hist_impr = (hist2 - hist1) / abs(hist1)
            if hist_impr >= 0.5:
                strength += 10
            elif hist_impr >= 0.25:
                strength += 6
            elif hist_impr >= 0.1:
                strength += 3

        # RSI táº¡i pivot1 ráº¥t tháº¥p â†’ oversold máº¡nh
        if rsi1 < 25:
            strength += 10
        elif rsi1 < 32:
            strength += 7
        elif rsi1 < 40:
            strength += 4

        # RSI táº¡i pivot2 cÅ©ng cÃ²n tháº¥p â†’ váº«n cÃ²n dÆ° Ä‘á»‹a
        if rsi2 < 35:
            strength += 8
        elif rsi2 < 45:
            strength += 4

        # Volume tÄƒng â†’ xÃ¡c nháº­n lá»±c cáº§u (dÃ¹ng láº¡i avg_vol_20 Ä‘Ã£ tÃ­nh á»Ÿ trÃªn)
        if df['Volume'].iloc[-1] > avg_vol_20 * 1.2:
            strength += 8
        elif df['Volume'].iloc[-1] > avg_vol_20:
            strength += 4

        # MACD hist improving 3 phiÃªn liÃªn tiáº¿p â†’ momentum máº¡nh hÆ¡n
        if macd_3bar_up:
            strength += 8

        # R/R cao
        if risk_reward >= 2.5:
            strength += 5
        elif risk_reward >= 2.0:
            strength += 3

        # Entry gáº§n Ä‘Ã¡y â†’ R/R tá»‘t hÆ¡n
        if recovery_pct <= 5.0:
            strength += 6
        elif recovery_pct <= 10.0:
            strength += 3

        is_priority = strength >= 78
        strength    = min(100, strength)   # cap display score

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
            f"âœ“ RSI_MACD_DIV {ticker}: {strength}% "
            f"[RSI: {rsi1:.1f}â†’{rsi2:.1f} (+{rsi_diff:.1f}pt) | "
            f"HIST: {hist1:.3f}â†’{hist2:.3f} | "
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

        # RSI: dÃ¹ng use_min=True cho p1 (p1 IS the RSI minimum â†’ Ä‘Ãºng)
        #      dÃ¹ng use_min=FALSE cho p2 (p2 lÃ  PRICE minimum, khÃ´ng pháº£i RSI minimum)
        #      â†’ BUG CÅ¨: use_min=True cho rsi2 láº¥y RSI tháº¥p nháº¥t Â±3 bars quanh Ä‘Ã¡y giÃ¡,
        #        vÃ´ tÃ¬nh match vá»›i rsi1 â†’ diff â‰ˆ 0pt â†’ fail C3
        # MACD hist: use_min=True cho cáº£ 2 (so sÃ¡nh Ä‘á»™ sÃ¢u Ã¢m táº¡i má»—i Ä‘Ã¡y â†’ Ä‘Ãºng)
        rsi1  = indicator_at_pivot(rsi_series,  p1_idx, window=3, use_min=True)
        rsi2  = indicator_at_pivot(rsi_series,  p2_idx, window=3, use_min=False)  # FIX: exact RSI at price bottom
        hist1 = indicator_at_pivot(hist_series, p1_idx, window=3, use_min=True)
        hist2 = indicator_at_pivot(hist_series, p2_idx, window=3, use_min=True)

        if any(pd.isna(v) for v in [rsi1, rsi2, hist1, hist2]): return signals

        # C1: RSI higher low >= 5pt
        rsi_diff = rsi2 - rsi1
        if rsi_diff < 5.0: return signals

        # C2: MACD hist higher low (hist1 pháº£i Ã¢m Ä‘á»ƒ xÃ¡c nháº­n setup bearish thá»±c sá»±)
        if hist2 <= hist1 or hist1 >= 0: return signals

        # C3: Price lower low >= 1.5%
        if p2_price >= p1_price * 0.985: return signals

        # C4: Gap >= 20 bars
        if (p2_idx - p1_idx) < 20: return signals

        # C5: rsi1 < 50  C6: rsi2 < 65 (ná»›i tá»« 60: cho phÃ©p rsi2 nhÆ° GEX 47.89)
        if rsi1 >= 50 or rsi2 >= 65: return signals

        # C7: MACD histogram Ä‘ang cáº£i thiá»‡n â€” dÃ¹ng 4-bar trend thay vÃ¬ single bar
        # LÃ½ do: single-bar h[-1]>h[-2] tháº¥t báº¡i khi histogram cÃ³ 1 ngÃ y wobble
        # VHM: hist 0.15â†’0.22â†’0.30 (3 bars liÃªn tá»¥c) â€” cáº£ hai check Ä‘á»u pass
        # GEX: hist -0.20â†’-0.15â†’-0.12 (trend rÃµ) â€” 4-bar check pass ngay cáº£ khi 1 bar dip
        h = hist_series
        macd_4bar_trend = h.iloc[-1] > h.iloc[-4]   # xu hÆ°á»›ng 4 bars (allow 1-2 bar wobble)
        macd_1bar_up    = h.iloc[-1] > h.iloc[-2]   # Ä‘ang tÄƒng ngay hÃ´m nay
        if not macd_4bar_trend: return signals       # overall trend pháº£i lÃªn
        macd_3bar_up = (h.iloc[-1] > h.iloc[-2] > h.iloc[-3])

        # MACD line vs signal line (dÃ¹ng cho trigger & scoring)
        macd_line_now    = float(macd_line.iloc[-1])
        signal_line_now  = float(signal_line.iloc[-1])
        hist_positive    = h.iloc[-1] > 0                    # MACD hist Ä‘Ã£ dÆ°Æ¡ng (VHM: +0.30)
        macd_line_above  = macd_line_now > signal_line_now   # MACD line vÆ°á»£t signal

        # C8: RSI now 30-75 (ná»›i tá»« 72: VHM RSI=69.15 pass rÃµ rÃ ng)
        rsi_now = float(rsi_series.iloc[-1])
        if not (30 <= rsi_now <= 75): return signals

        # C9: EMA20 trigger â€” BONUS (khÃ´ng mandatory)
        # Mandatory sáº½ block GEX (37.05 < EMA20 37.73) dÃ¹ divergence rÃµ rÃ ng
        # Giáº£i phÃ¡p: EMA20 cross = strong score bonus (+15), cÃ²n tiáº¿p cáº­n EMA20 = bonus nhá» (+8)
        ema20_now     = float(df['EMA20'].iloc[-1])
        current_close = float(close_series.iloc[-1])
        ema50_now     = float(df['EMA50'].iloc[-1])

        above_ema20 = current_close > ema20_now     # Ä‘Ã£ vÆ°á»£t EMA20 â†’ tÃ­n hiá»‡u máº¡nh
        near_ema20  = current_close > ema20_now * 0.97  # trong vÃ²ng 3% dÆ°á»›i EMA20 â†’ pre-trigger

        # Náº¿u giÃ¡ váº«n náº±m xa bÃªn dÆ°á»›i EMA20 (>3%) VÃ€ dÆ°á»›i EMA50 â†’ downtrend máº¡nh, bá» qua
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

        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        # STRENGTH SCORING â€” Redesigned v2
        # Base=40, MAX natural=105, threshold=62 â†’ phÃ¢n phá»‘i cÃ³ Ã½ nghÄ©a
        #
        # NHÃ“M 1 â€” CORE DIVERGENCE          max 28pt  (Ä‘iá»u kiá»‡n cá»‘t lÃµi)
        # NHÃ“M 2 â€” OVERSOLD DEPTH           max 12pt  (Ä‘á»™ sÃ¢u oversold)
        # NHÃ“M 3 â€” MOMENTUM CONFIRMATION    max 18pt  (xÃ¡c nháº­n Ä‘Ã  phá»¥c há»“i)
        # NHÃ“M 4 â€” SIGNAL QUALITY           max  7pt  (cháº¥t lÆ°á»£ng setup)
        # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        # Má»¥c tiÃªu phÃ¢n phá»‘i:
        #   47-61%: TÃ­n hiá»‡u yáº¿u (dÆ°á»›i threshold â€” khÃ´ng hiá»ƒn thá»‹)
        #   62-71%: Äá»§ Ä‘iá»u kiá»‡n â€” ðŸŸ¡ OK
        #   72-81%: Tá»‘t          â€” ðŸŸ¢ Good
        #   82-91%: Ráº¥t tá»‘t      â€” â­ Strong
        #   92-100%: Xuáº¥t sáº¯c    â€” ðŸ† Exceptional (hiáº¿m)
        # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
        strength = 40   # base

        # â”€â”€ NHÃ“M 1: CORE DIVERGENCE (max 28) â”€â”€
        # RSI divergence magnitude â€” thÆ°á»›c Ä‘o quan trá»ng nháº¥t
        if rsi_diff >= 20:   strength += 16
        elif rsi_diff >= 15: strength += 13
        elif rsi_diff >= 10: strength += 10
        elif rsi_diff >= 7:  strength += 7
        else:                strength += 4   # 5-7pt â€” pass nhÆ°ng biÃªn Ä‘á»™ háº¹p

        # MACD histogram divergence quality
        if hist1 != 0:
            hi = (hist2 - hist1) / abs(hist1)  # % cáº£i thiá»‡n táº¡i Ä‘Ã¡y
            if hi >= 0.8:    strength += 12
            elif hi >= 0.5:  strength += 9
            elif hi >= 0.3:  strength += 6
            elif hi >= 0.1:  strength += 3
            # hi < 0.1: Ä‘á»§ Ä‘iá»u kiá»‡n (>0) nhÆ°ng khÃ´ng cá»™ng thÃªm

        # â”€â”€ NHÃ“M 2: OVERSOLD DEPTH (max 12) â”€â”€
        # Äá»™ sÃ¢u oversold táº¡i pivot1 (cÃ ng tháº¥p â†’ recovery cÃ ng máº¡nh)
        if rsi1 < 20:   strength += 8
        elif rsi1 < 28: strength += 6
        elif rsi1 < 35: strength += 4
        elif rsi1 < 42: strength += 2

        # RSI táº¡i pivot2 cÃ²n tháº¥p â†’ cÃ²n dÆ° Ä‘á»‹a tÄƒng
        if rsi2 < 35:   strength += 4
        elif rsi2 < 45: strength += 2
        elif rsi2 < 55: strength += 1

        # â”€â”€ NHÃ“M 3: MOMENTUM CONFIRMATION (max 18) â”€â”€
        # MACD hist Ä‘Ã£ dÆ°Æ¡ng â†’ reversal Ä‘Æ°á»£c xÃ¡c nháº­n hoÃ n toÃ n
        if hist_positive:      strength += 10  # VHM: hist +0.30
        elif macd_3bar_up:     strength += 5   # 3 bars cáº£i thiá»‡n liÃªn tiáº¿p
        elif macd_4bar_trend:  strength += 2   # xu hÆ°á»›ng 4 bars (cÃ³ wobble)

        # MACD line vÆ°á»£t signal line â†’ crossover xÃ¡c nháº­n
        if macd_line_above:    strength += 5

        # EMA20 status (nhá» â€” khÃ´ng overshadow core divergence)
        if above_ema20:        strength += 3
        elif near_ema20:       strength += 1

        # â”€â”€ NHÃ“M 4: SIGNAL QUALITY (max 7) â”€â”€
        # Fake breakdown â†’ rÅ© hÃ ng rÃµ rÃ ng, quality setup
        if fake_break:         strength += 4

        # R/R ratio
        if risk_reward >= 2.5:    strength += 2
        elif risk_reward >= 2.0:  strength += 1

        # Entry gáº§n Ä‘Ã¡y
        if recovery_pct <= 8:     strength += 1

        # Threshold calibrated cho scoring má»›i: 62 (thay vÃ¬ 78 cá»§a scoring cÅ©)
        is_priority = strength >= 62
        strength    = min(100, strength)   # safety cap (hiáº¿m khi trigger vá»›i design má»›i)
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
        fb_tag    = f"FB+{fb_score}" if fake_break else "no-FB"
        macd_tag  = f"hist+{h.iloc[-1]:.2f}" if hist_positive else f"hist{h.iloc[-1]:.2f}"
        logger.info(
            f"âœ“ DIVERGENCE_FB {ticker}: {strength}% "
            f"[RSI: {rsi1:.1f}->{rsi2:.1f} (+{rsi_diff:.1f}pt) | "
            f"HIST: {hist1:.3f}->{hist2:.3f} | {macd_tag} | "
            f"EMA20={'above' if above_ema20 else 'near'} | Rec={recovery_pct:.1f}% | {fb_tag}]"
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
        
        logger.info("âœ“ Database initialized")
        return True
        
    except Exception as e:
        logger.error(f"DB error: {str(e)}")
        return False

def save_signals_to_db(signals):
    """Save signals using SQLAlchemy (works with SQLite and PostgreSQL)
    FIXED: Không xóa signals cũ — chỉ INSERT signals mới, tránh duplicate bằng signal_code
    """
    try:
        with engine.connect() as conn:
            inserted = 0
            skipped  = 0
            for signal in signals:
                # Kiểm tra đã tồn tại chưa (tránh duplicate theo ticker+date+action)
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
                    continue  # Đã có rồi, bỏ qua

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
    breadth_data = []  # Thu tháº­p dá»¯ liá»‡u breadth cho Market Risk Analysis
    
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

            # Thu tháº­p closes cho Market Breadth Analysis
            try:
                closes_list = df['Close'].tolist()
                if len(closes_list) >= 2:
                    breadth_data.append({'ticker': ticker, 'closes': closes_list})
            except:
                pass

            # Collect signals:
            # - PULLBACK / EMA_CROSS: dedup per ticker (giá»¯ strength cao nháº¥t)
            # - DIVERGENCE_FB: luÃ´n lÆ°u náº¿u is_priority (khÃ´ng bá»‹ loáº¡i bá»Ÿi chiáº¿n lÆ°á»£c khÃ¡c)
            tickers_in_batch    = {s['ticker'] for s in all_signals if s.get('strategy') != 'DIVERGENCE_FB'}
            div_tickers_in_batch = {s['ticker'] for s in all_signals if s.get('strategy') == 'DIVERGENCE_FB'}

            # PULLBACK + EMA_CROSS: dedup per ticker
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

            # DIVERGENCE_FB: lÆ°u Ä‘á»™c láº­p, dedup riÃªng (1 signal/ticker/ngÃ y)
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
    
    # â”€â”€ Thu tháº­p Market Breadth Data â”€â”€
    if breadth_data:
        try:
            logger.info(f"\nðŸ“Š Collecting breadth data from {len(breadth_data)} stocks...")
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
            logger.info(f"ðŸ“Š Breadth saved: {advance} tÄƒng / {decline} giáº£m / MA20: {above_ma20}/{total}")
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
    logger.info(f"\nâœ“ Done. {len(signals)} signals")
