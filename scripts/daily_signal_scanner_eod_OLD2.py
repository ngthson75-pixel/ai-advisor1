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

# 343 Cổ phiếu có thanh khoản cao nhất HOSE + HNX
# Updated: 2026-01-27
TOP_343_STOCKS = [
    # HOSE - Top Blue Chips & Large Caps (50 stocks)
    'VCB', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB', 'STB', 'MSN',
    'FPT', 'VRE', 'SSI', 'BID', 'CTG', 'PLX', 'GAS', 'MWG', 'VJC', 'HDB',
    'BSR', 'POW', 'SAB', 'NVL', 'BCM', 'KDH', 'DGC', 'REE', 'TPB', 'ACB',
    'GVR', 'PNJ', 'VGC', 'DHG', 'DPM', 'GMD', 'SHB', 'LPB', 'VCI', 'TCX',
    'BVH', 'HVN', 'BMP', 'DXG', 'VPL', 'KBC', 'DIG', 'GEX', 'VIB', 'EIB',
    
    # HOSE - Mid Caps (100 stocks)
    'VPI', 'HT1', 'HSG', 'DCM', 'NT2', 'HNG', 'VND', 'VCG', 'SBT', 'EVF',
    'DBC', 'HCM', 'CTD', 'PC1', 'DGW', 'SZC', 'CTR', 'MCH', 'VIX', 'HDG',
    'PPC', 'VSC', 'BWE', 'VCK', 'VDS', 'VSH', 'VTP', 'SCS', 'CNG', 'PVD',
    'PVT', 'VOS', 'CSV', 'PVS', 'NLG', 'VCF', 'CMG', 'TCH', 'PAN', 'SGN',
    'PHR', 'NBB', 'DPR', 'DVP', 'NHA', 'GEG', 'CII', 'PTB', 'NAF', 'HAG',
    'CMX', 'ORS', 'HDC', 'DMC', 'KDC', 'TNG', 'HRC', 'SVC', 'TCL', 'KSB',
    'VHC', 'HHS', 'MSH', 'SSB', 'HAX', 'SZL', 'VTO', 'VPX', 'PET', 'PVP',
    'VCK', 'QCG', 'FRT', 'SJS', 'FCN', 'GEE', 'TRA', 'DSE', 'TCM', 'VGT',
    'DHA', 'GEL', 'PDN', 'PMG', 'GIL', 'VFC', 'CTI', 'PDR', 'IDC', 'KHG',
    'MSB', 'DXS', 'OCB', 'HAH', 'IJC', 'ANV', 'LCG', 'DPG', 'BAF', 'HPA',
    'TV2', 'SMC', 'CTF', 'KOS', 'SIP', 'ELC', 'BMI', 'NTL', 'TAL', 'DCL',
    'BSI', 'HSL', 'BFC', 
    
    # HOSE - Small Caps (93 stocks)
    'HQC', 'HTN', 'PDC', 'LSS', 'AGG', 'VIP', 'CDC', 'ASG', 'ITC', 'TIP',
    'ASM', 'VTB', 'PGC', 'SHI', 'SRC', 'TDH', 'DVN', 'GDT', 'VLA', 'APH',
    'VPG', 'VRC', 'HPX', 'CRE', 'PGI', 'TTF', 'TNT', 'VDP', 'CSM', 'CTS',
    'FMC', 'TCO', 'DLG', 'PGS', 'PAC', 'TMT', 'KLB', 'DC4', 'GTA', 'PGT',
    'ST8', 'TCR', 'TLG', 'LBM', 'GDW', 'THG', 'VNE', 'VNL', 'HTI', 'HU1',
    'NHH', 'HID', 'HU6', 'HVH', 'TDP', 'PNC', 'PTL', 'HDM', 'VHL', 'IDI',
    'TCW', 'VIM', 'CLC', 'SAM', 'EVG', 'PTI', 'FIT', 'SMA', 'VIT', 'VGG',
    'CRC', 'TSC', 'TLH', 'DRI', 'BCC', 'TYA', 'VE1', 'HBC', 'OGC', 'YEG',
    'VPH', 'VE9', 'VHG', 'VID', 'AAA', 'VIF', 'VIG', 'LDG', 'CIG', 'DRH',
    'DXV', 'TNI', 'ASP', 'HU3', 'HAP', 'PVX', 
    
    # HNX - Top Stocks (100 stocks)
    'PVS', 'VFS', 'AAV', 'SHS', 'PVB', 'CEO', 'NNC', 'BVS', 'BAB', 'NVB',
    'TIG', 'API', 'AST', 'PVC', 'BVB', 'VTZ', 'VBB', 'PGB', 'VC3', 'ASG',
    'MST', 'DST', 'PVI', 'HUT', 'DVM', 'PTI', 'VIG', 'MIG', 'NRC', 'ABI',
    'C69', 'PGI', 'EVS', 'PSI', 'HBS', 'TVS', 'APS', 'IDJ', 'DL1', 'DTD',
    'MBS', 'DXP', 'LAS', 'VGS', 'L40', 'EVS', 'L18', 'NDN', 'VC2', 'LIG',
    'VCS', 'SJE', 'VHE', 'INN', 'DHT', 'DHA', 'NAG', 'VC7', 'IPA', 'L14',
    'VIG', 'MBG', 'LAS', 'LDP', 'BCC', 'PVG', 'DTD', 'DTT', 'NBC', 'KSV',
    'PLC', 'PTC', 'PVL', 'PVV', 'HGM', 'TIG', 'HLD', 'VE2', 'NBC', 'AMV',
    'KSF', 'SD9', 'OCH', 'PSD', 'VIG', 'VGG', 'VTB',
    
]

def get_top_343_stocks():
    """
    Return 343 highest liquidity stocks (HOSE + HNX)
    Static list updated periodically
    """
    logger.info(f"Using curated list of {len(TOP_343_STOCKS)} high-liquidity stocks")
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
            
            if close >= 50000:
                stock_type = "Blue Chip"
            elif close >= 20000:
                stock_type = "Mid Cap"
            else:
                stock_type = "Penny"
            
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
            
            if close >= 50000:
                stock_type = "Blue Chip"
            elif close >= 20000:
                stock_type = "Mid Cap"
            else:
                stock_type = "Penny"
            
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
    logger.info(f"Stocks: {len(TOP_343_STOCKS)}")
    logger.info("=" * 60)
    
    init_database()
    
    all_signals = []
    processed = 0
    failed = 0
    
    for ticker in TOP_343_STOCKS:
        try:
            logger.info(f"Processing {ticker} ({processed + 1}/{len(TOP_343_STOCKS)})...")
            
            df = get_stock_data(ticker, days=100)
            
            if df is None or len(df) < 50:
                logger.warning(f"Skip {ticker}")
                failed += 1
                time.sleep(2)
                continue
            
            pullback = check_pullback_strategy(df, ticker)
            ema_cross = check_ema_cross_strategy(df, ticker)
            
            # Priority only filter
            for signal in pullback:
                if signal['is_priority'] == 1:
                    all_signals.append(signal)
                    
            for signal in ema_cross:
                if signal['is_priority'] == 1:
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
    
    if len(all_signals) > 0:
        save_signals_to_db(all_signals)
        
        pullback_cnt = len([s for s in all_signals if s['strategy'] == 'PULLBACK'])
        ema_cross_cnt = len([s for s in all_signals if s['strategy'] == 'EMA_CROSS'])
        priority_cnt = len([s for s in all_signals if s['is_priority'] == 1])
        
        logger.info(f"PULLBACK: {pullback_cnt}")
        logger.info(f"EMA_CROSS: {ema_cross_cnt}")
        logger.info(f"Priority: {priority_cnt}")
        
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
