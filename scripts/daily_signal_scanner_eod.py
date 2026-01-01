"""
AI Advisor - Daily Signal Scanner
Uses vnstock 3.3.1 Quote API
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import time
import logging

# CORRECT vnstock 3.3.1 API
from vnstock import Quote

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = 'signals.db'

TOP_STOCKS = [
    'VCB', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB', 'STB', 'MSN',
    'FPT', 'VRE', 'SSI', 'BID', 'CTG', 'PLX', 'GAS', 'MWG', 'VJC', 'HDB',
    'PDR', 'POW', 'SAB', 'NVL', 'BCM', 'KDH', 'DGC', 'REE', 'TPB', 'ACB',
    'GVR', 'PNJ', 'VGC', 'DHG', 'DPM', 'GMD', 'HPX', 'LPB', 'VCI', 'SSB',
    'BVH', 'HNG', 'TCH', 'DXG', 'VHC', 'PC1', 'DIG', 'HT1', 'VGS', 'IDC'
]

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

def get_stock_data(ticker, days=100):
    """Get stock data using Quote API"""
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
        logger.error(f"Error {ticker}: {str(e)}")
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
    """Initialize database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
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
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✓ Database initialized")
        return True
        
    except Exception as e:
        logger.error(f"DB error: {str(e)}")
        return False

def save_signals_to_db(signals):
    """Save signals"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM signals')
        
        for signal in signals:
            cursor.execute('''
                INSERT INTO signals (
                    ticker, strategy, entry_price, stop_loss, take_profit,
                    risk_reward, strength, is_priority, stock_type, rsi, date, action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal['ticker'], signal['strategy'], signal['entry_price'],
                signal['stop_loss'], signal['take_profit'], signal['risk_reward'],
                signal['strength'], signal['is_priority'], signal['stock_type'],
                signal['rsi'], signal['date'], signal['action']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ Saved {len(signals)} signals")
        return True
        
    except Exception as e:
        logger.error(f"Save error: {str(e)}")
        return False

def scan_all_stocks():
    """Scan stocks"""
    logger.info("=" * 60)
    logger.info("Starting scan...")
    logger.info(f"Date: {get_last_trading_day()}")
    logger.info(f"Stocks: {len(TOP_STOCKS)}")
    logger.info("=" * 60)
    
    init_database()
    
    all_signals = []
    processed = 0
    failed = 0
    
    for ticker in TOP_STOCKS:
        try:
            logger.info(f"Processing {ticker} ({processed + 1}/{len(TOP_STOCKS)})...")
            
            df = get_stock_data(ticker, days=100)
            
            if df is None or len(df) < 50:
                logger.warning(f"Skip {ticker}")
                failed += 1
                time.sleep(0.5)
                continue
            
            pullback = check_pullback_strategy(df, ticker)
            ema_cross = check_ema_cross_strategy(df, ticker)
            
            all_signals.extend(pullback)
            all_signals.extend(ema_cross)
            
            processed += 1
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error {ticker}: {str(e)}")
            failed += 1
            time.sleep(0.5)
    
    logger.info("=" * 60)
    logger.info("COMPLETE")
    logger.info(f"Processed: {processed}/{len(TOP_STOCKS)}")
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
