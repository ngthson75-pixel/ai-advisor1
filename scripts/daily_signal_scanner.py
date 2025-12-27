#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAILY SIGNAL SCANNER - PULLBACK & EMA_CROSS
Scan toàn bộ stocks và tìm signals cho 2 chiến lược chính
Upload results to frontend

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com
"""

from vnstock import Vnstock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# Output
OUTPUT_FOLDER = "signals"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Scan settings
LOOKBACK_DAYS = 60  # 60 days for indicators
MIN_VOLUME = 100_000  # Min 100k daily volume
MIN_PRICE = 1_000  # Min 1,000 VND

# Stock classification
BLUE_CHIPS = ['VNM', 'VIC', 'VHM', 'HPG', 'TCB', 'VCB', 'BID', 'CTG', 'MBB', 
              'VPB', 'MSN', 'VJC', 'GAS', 'PLX', 'SSI', 'HDB', 'VRE', 'NVL',
              'POW', 'FPT', 'SAB', 'MWG', 'ACB', 'TPB', 'STB', 'SHB']

MID_CAPS = ['DIG', 'DXG', 'HCM', 'VPI', 'PDR', 'PVD', 'PVT', 'PVS',
            'DCM', 'DPM', 'NT2', 'GMD', 'KDH', 'PC1', 'REE', 'SBT', 'VGC',
            'VHC', 'VIB', 'VND', 'VSH', 'PVG', 'PVI', 'EVE', 'ITA']

# Top performers from backtest
TOP_2025_STOCKS = ['TCH', 'PWA', 'GEE', 'QCG', 'LGL', 'HID', 'VHE', 'HHV', 
                   'HTN', 'GIL', 'NDN', 'TCO', 'CSV', 'TIG', 'TC6']

print("="*70)
print("DAILY SIGNAL SCANNER - PULLBACK & EMA_CROSS")
print("="*70)
print(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# INDICATOR CALCULATIONS
# ============================================================================

def calculate_ema(series, period):
    """Calculate EMA"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series, period=14):
    """Calculate RSI"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(high, low, close, period=14):
    """Calculate ATR for stop loss"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


# ============================================================================
# STRATEGY 1: PULLBACK
# ============================================================================

def scan_pullback_signal(df, ticker):
    """
    Scan for PULLBACK entry signals
    
    Entry Conditions:
    1. EMA20 > EMA50 (uptrend)
    2. Price pulled back to EMA20
    3. Price bouncing from EMA20
    4. RSI 40-60 (not overbought/oversold)
    5. Volume confirmation
    
    Returns:
        dict or None
    """
    if len(df) < 60:
        return None
    
    # Calculate indicators
    df = df.copy()
    df['ema20'] = calculate_ema(df['close'], 20)
    df['ema50'] = calculate_ema(df['close'], 50)
    df['rsi'] = calculate_rsi(df['close'], 14)
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'])
    
    # Get latest data
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Check conditions
    conditions = []
    
    # 1. Uptrend (EMA20 > EMA50)
    uptrend = latest['ema20'] > latest['ema50']
    conditions.append(('Uptrend', uptrend, f"EMA20: {latest['ema20']:.0f} > EMA50: {latest['ema50']:.0f}"))
    
    # 2. Price near EMA20 (within 3%)
    price_to_ema20_pct = (latest['close'] - latest['ema20']) / latest['ema20'] * 100
    near_ema20 = abs(price_to_ema20_pct) < 3
    conditions.append(('Near EMA20', near_ema20, f"Distance: {price_to_ema20_pct:.2f}%"))
    
    # 3. Bouncing (close > open today, or close > prev close)
    bouncing = latest['close'] > latest['open'] or latest['close'] > prev['close']
    conditions.append(('Bouncing', bouncing, f"Close: {latest['close']:.0f} vs Open: {latest['open']:.0f}"))
    
    # 4. RSI in range
    rsi_ok = 40 <= latest['rsi'] <= 60
    conditions.append(('RSI OK', rsi_ok, f"RSI: {latest['rsi']:.1f}"))
    
    # 5. Volume confirmation
    volume_ok = latest['volume'] > latest['volume_ma'] * 0.8
    conditions.append(('Volume OK', volume_ok, f"{latest['volume']:,.0f} vs avg {latest['volume_ma']:,.0f}"))
    
    # Signal strength
    passed = sum([c[1] for c in conditions])
    total = len(conditions)
    strength = passed / total * 100
    
    # Require at least 4/5 conditions (80%)
    if passed >= 4:
        # Calculate entry levels
        entry_price = latest['close']
        
        # Stop loss: Below recent swing low or 2*ATR
        recent_low = df['low'].tail(5).min()
        stop_loss = min(recent_low, entry_price - 2 * latest['atr'])
        
        # Take profit: Previous high or 1.5x risk
        recent_high = df['high'].tail(10).max()
        risk = entry_price - stop_loss
        take_profit = max(recent_high, entry_price + 1.5 * risk)
        
        return {
            'ticker': ticker,
            'strategy': 'PULLBACK',
            'date': latest['time'].strftime('%Y-%m-%d') if hasattr(latest['time'], 'strftime') else str(latest['time']),
            'entry_price': float(entry_price),
            'stop_loss': float(stop_loss),
            'take_profit': float(take_profit),
            'risk_reward': float((take_profit - entry_price) / (entry_price - stop_loss)),
            'rsi': float(latest['rsi']),
            'strength': float(strength),
            'conditions': {c[0]: {'passed': c[1], 'value': c[2]} for c in conditions},
            'ema20': float(latest['ema20']),
            'ema50': float(latest['ema50']),
            'volume': int(latest['volume']),
            'volume_avg': int(latest['volume_ma'])
        }
    
    return None


# ============================================================================
# STRATEGY 2: EMA_CROSS
# ============================================================================

def scan_ema_cross_signal(df, ticker):
    """
    Scan for EMA_CROSS entry signals
    
    Entry Conditions:
    1. EMA20 crosses above EMA50 (within last 3 days)
    2. Volume > 1.3x average
    3. RSI > 50 (trending up)
    4. Price above both EMAs
    
    Returns:
        dict or None
    """
    if len(df) < 60:
        return None
    
    # Calculate indicators
    df = df.copy()
    df['ema20'] = calculate_ema(df['close'], 20)
    df['ema50'] = calculate_ema(df['close'], 50)
    df['rsi'] = calculate_rsi(df['close'], 14)
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'])
    
    # Get latest data
    latest = df.iloc[-1]
    
    # Check for recent crossover (within last 3 days)
    crossover_found = False
    crossover_day = None
    
    for i in range(1, min(4, len(df))):
        curr = df.iloc[-i]
        prev = df.iloc[-i-1]
        
        # Check if EMA20 crossed above EMA50
        if curr['ema20'] > curr['ema50'] and prev['ema20'] <= prev['ema50']:
            crossover_found = True
            crossover_day = i
            break
    
    if not crossover_found:
        return None
    
    # Check other conditions
    conditions = []
    
    # 1. Crossover found
    conditions.append(('Crossover', True, f"{crossover_day} days ago"))
    
    # 2. Volume confirmation
    volume_ok = latest['volume'] > latest['volume_ma'] * 1.3
    conditions.append(('Volume', volume_ok, f"{latest['volume']/latest['volume_ma']:.2f}x average"))
    
    # 3. RSI trending
    rsi_ok = latest['rsi'] > 50
    conditions.append(('RSI > 50', rsi_ok, f"RSI: {latest['rsi']:.1f}"))
    
    # 4. Price above EMAs
    above_emas = latest['close'] > latest['ema20'] and latest['close'] > latest['ema50']
    conditions.append(('Above EMAs', above_emas, f"Close: {latest['close']:.0f}"))
    
    # 5. EMA20 still above EMA50
    ema_order = latest['ema20'] > latest['ema50']
    conditions.append(('EMA Order', ema_order, f"EMA20 > EMA50"))
    
    # Signal strength
    passed = sum([c[1] for c in conditions])
    total = len(conditions)
    strength = passed / total * 100
    
    # Require at least 4/5 conditions (80%)
    if passed >= 4:
        # Calculate entry levels
        entry_price = latest['close']
        
        # Stop loss: Below EMA50
        stop_loss = latest['ema50'] * 0.97  # 3% below EMA50
        
        # Take profit: +10%
        take_profit = entry_price * 1.10
        
        return {
            'ticker': ticker,
            'strategy': 'EMA_CROSS',
            'date': latest['time'].strftime('%Y-%m-%d') if hasattr(latest['time'], 'strftime') else str(latest['time']),
            'entry_price': float(entry_price),
            'stop_loss': float(stop_loss),
            'take_profit': float(take_profit),
            'risk_reward': float((take_profit - entry_price) / (entry_price - stop_loss)),
            'rsi': float(latest['rsi']),
            'strength': float(strength),
            'crossover_day': int(crossover_day),
            'conditions': {c[0]: {'passed': c[1], 'value': c[2]} for c in conditions},
            'ema20': float(latest['ema20']),
            'ema50': float(latest['ema50']),
            'volume': int(latest['volume']),
            'volume_avg': int(latest['volume_ma'])
        }
    
    return None


# ============================================================================
# STOCK CLASSIFICATION
# ============================================================================

def classify_stock(ticker):
    """Classify stock type"""
    if ticker in BLUE_CHIPS:
        return 'Blue Chip'
    elif ticker in MID_CAPS:
        return 'Mid Cap'
    else:
        return 'Penny'


def is_priority_stock(ticker):
    """Check if stock is in priority list"""
    return ticker in TOP_2025_STOCKS


# ============================================================================
# MAIN SCANNER
# ============================================================================

def scan_all_stocks(stock_list, max_stocks=None):
    """
    Scan all stocks for signals
    
    Args:
        stock_list: List of tickers to scan
        max_stocks: Limit number of stocks (for testing)
    
    Returns:
        dict: {pullback: [], ema_cross: []}
    """
    signals = {
        'pullback': [],
        'ema_cross': []
    }
    
    scanned = 0
    errors = []
    
    if max_stocks:
        stock_list = stock_list[:max_stocks]
    
    print(f"Scanning {len(stock_list)} stocks...")
    print()
    
    for i, ticker in enumerate(stock_list, 1):
        print(f"[{i}/{len(stock_list)}] {ticker}...", end=" ", flush=True)
        
        try:
            # Get data
            stock = Vnstock().stock(symbol=ticker, source='VCI')
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=LOOKBACK_DAYS)
            
            df = stock.quote.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            )
            
            if df is None or len(df) < 50:
                print("⚠️ Insufficient data")
                continue
            
            # Standardize columns
            df.columns = [c.lower() for c in df.columns]
            if 'time' not in df.columns and 'date' in df.columns:
                df.rename(columns={'date': 'time'}, inplace=True)
            
            # Filter by volume and price
            latest_volume = df['volume'].iloc[-1]
            latest_price = df['close'].iloc[-1]
            
            if latest_volume < MIN_VOLUME or latest_price < MIN_PRICE:
                print(f"❌ Filtered (vol: {latest_volume:,.0f}, price: {latest_price:,.0f})")
                continue
            
            # Scan for signals
            pullback_signal = scan_pullback_signal(df, ticker)
            ema_cross_signal = scan_ema_cross_signal(df, ticker)
            
            # Add classification
            stock_type = classify_stock(ticker)
            is_priority = is_priority_stock(ticker)
            
            if pullback_signal:
                pullback_signal['stock_type'] = stock_type
                pullback_signal['is_priority'] = is_priority
                signals['pullback'].append(pullback_signal)
                print(f"✅ PULLBACK ({pullback_signal['strength']:.0f}%)")
            elif ema_cross_signal:
                ema_cross_signal['stock_type'] = stock_type
                ema_cross_signal['is_priority'] = is_priority
                signals['ema_cross'].append(ema_cross_signal)
                print(f"✅ EMA_CROSS ({ema_cross_signal['strength']:.0f}%)")
            else:
                print("⚪ No signal")
            
            scanned += 1
            
        except Exception as e:
            errors.append((ticker, str(e)))
            print(f"❌ Error: {e}")
        
        # Rate limit
        time.sleep(1.5)
        
        # Progress update
        if i % 20 == 0:
            print(f"\n  Progress: {i}/{len(stock_list)}, "
                  f"PULLBACK: {len(signals['pullback'])}, "
                  f"EMA_CROSS: {len(signals['ema_cross'])}\n")
    
    # Summary
    print("\n" + "="*70)
    print("SCAN COMPLETE")
    print("="*70)
    print(f"Stocks scanned: {scanned}")
    print(f"PULLBACK signals: {len(signals['pullback'])}")
    print(f"EMA_CROSS signals: {len(signals['ema_cross'])}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for ticker, error in errors[:5]:
            print(f"  {ticker}: {error}")
    
    return signals


# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_signals(signals):
    """Save signals to JSON for frontend"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Sort by strength
    signals['pullback'].sort(key=lambda x: x['strength'], reverse=True)
    signals['ema_cross'].sort(key=lambda x: x['strength'], reverse=True)
    
    # Prioritize top stocks
    for signal_list in [signals['pullback'], signals['ema_cross']]:
        signal_list.sort(key=lambda x: (x['is_priority'], x['strength']), reverse=True)
    
    # Full signals
    filename_full = f"{OUTPUT_FOLDER}/signals_{timestamp}.json"
    with open(filename_full, 'w', encoding='utf-8') as f:
        json.dump(signals, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved: {filename_full}")
    
    # Latest signals (symlink/copy)
    filename_latest = f"{OUTPUT_FOLDER}/signals_latest.json"
    with open(filename_latest, 'w', encoding='utf-8') as f:
        json.dump(signals, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved: {filename_latest}")
    
    # Summary for frontend
    summary = {
        'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_signals': len(signals['pullback']) + len(signals['ema_cross']),
        'pullback_count': len(signals['pullback']),
        'ema_cross_count': len(signals['ema_cross']),
        'top_pullback': signals['pullback'][:10] if signals['pullback'] else [],
        'top_ema_cross': signals['ema_cross'][:10] if signals['ema_cross'] else []
    }
    
    filename_summary = f"{OUTPUT_FOLDER}/summary_latest.json"
    with open(filename_summary, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved: {filename_summary}")
    
    # Print top signals
    print("\n" + "="*70)
    print("TOP SIGNALS")
    print("="*70)
    
    print("\nTOP 10 PULLBACK:")
    for i, sig in enumerate(signals['pullback'][:10], 1):
        priority = "⭐" if sig['is_priority'] else ""
        print(f"{i:2d}. {priority}{sig['ticker']:6s} ({sig['stock_type']:10s}): "
              f"Strength: {sig['strength']:.0f}%, "
              f"Entry: {sig['entry_price']:8,.0f}, "
              f"R:R: {sig['risk_reward']:.2f}")
    
    print("\nTOP 10 EMA_CROSS:")
    for i, sig in enumerate(signals['ema_cross'][:10], 1):
        priority = "⭐" if sig['is_priority'] else ""
        print(f"{i:2d}. {priority}{sig['ticker']:6s} ({sig['stock_type']:10s}): "
              f"Strength: {sig['strength']:.0f}%, "
              f"Entry: {sig['entry_price']:8,.0f}, "
              f"R:R: {sig['risk_reward']:.2f}, "
              f"Cross: {sig['crossover_day']}d ago")
    
    return filename_latest


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Get stock list
    print("Loading stock list...")
    
    # Option 1: Use saved list
    if os.path.exists('vnstock_symbols.csv'):
        stock_df = pd.read_csv('vnstock_symbols.csv')
        stock_list = stock_df['symbol'].tolist()
        print(f"✅ Loaded {len(stock_list)} stocks from vnstock_symbols.csv")
    
    # Option 2: Get from API
    else:
        try:
            print("Fetching from vnstock API...")
            stock = Vnstock().stock(symbol='VNM', source='VCI')
            listing = stock.listing.all_symbols()
            stock_list = listing['symbol'].tolist()
            
            # Save for future
            listing.to_csv('vnstock_symbols.csv', index=False)
            print(f"✅ Fetched {len(stock_list)} stocks from API")
        except Exception as e:
            print(f"❌ Could not fetch stock list: {e}")
            print("Using fallback list...")
            stock_list = BLUE_CHIPS + MID_CAPS + TOP_2025_STOCKS
    
    # Filter to priority stocks first (for testing)
    use_priority = input("\nScan priority stocks only? (y/n): ").strip().lower() == 'y'
    
    if use_priority:
        stock_list = [s for s in stock_list if s in TOP_2025_STOCKS + BLUE_CHIPS]
        print(f"Scanning {len(stock_list)} priority stocks")
    
    # Scan
    signals = scan_all_stocks(stock_list)
    
    # Save
    output_file = save_signals(signals)
    
    print(f"\n{'='*70}")
    print("READY TO UPLOAD TO FRONTEND!")
    print(f"{'='*70}")
    print(f"File: {output_file}")
    print("\nNext steps:")
    print("1. Copy signals_latest.json to frontend/public/data/")
    print("2. Frontend will auto-refresh signals")
    print("3. Users can view and trade signals")
