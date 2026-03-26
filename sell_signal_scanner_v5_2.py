#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sell Signal Scanner v5.3
Replaced MA20_STRICT with 3 Technical Exit Criteria

NEW EXIT RULES:
1. Daily MACD + RSI>80 + Support break → BÁN 100% (CRITICAL)
2. 4H MACD + Volume divergence → BÁN 50% (HIGH)
3. 1H Volume Climax (BSR pattern) → BÁN 100% (HIGH)

SCHEDULE: Mỗi giờ 9:30-15:30 VN time (trading hours)
"""

import os
import sys
from datetime import datetime, timedelta
from vnstock3 import Vnstock
import psycopg2
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv()

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db_connection():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )


# ============================================================================
# DATA RETRIEVAL FUNCTIONS
# ============================================================================

def get_daily_data(ticker, days_back=100):
    """
    Get daily OHLCV data
    
    Args:
        ticker: Stock symbol
        days_back: Number of days to fetch
    
    Returns:
        DataFrame: Daily OHLCV data
    """
    try:
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        df = stock.quote.history(start=start_date, end=end_date)
        
        if df is None or len(df) == 0:
            return None
        
        return df
        
    except Exception as e:
        print(f"⚠️ {ticker}: Error getting daily data - {e}")
        return None


def get_intraday_4h_data(ticker, days_back=15):
    """
    Get 4H intraday data (aggregated from 1H or intraday)
    
    Args:
        ticker: Stock symbol
        days_back: Number of days for intraday data
    
    Returns:
        DataFrame: 4H OHLCV data
    """
    try:
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        
        # Try to get intraday data
        intraday_df = stock.quote.intraday(symbol=ticker, page_size=200)
        
        if intraday_df is None or len(intraday_df) == 0:
            print(f"⚠️ {ticker}: No intraday data for 4H aggregation")
            return None
        
        # Convert to datetime
        if 'time' in intraday_df.columns:
            intraday_df['datetime'] = pd.to_datetime(intraday_df['time'])
            intraday_df.set_index('datetime', inplace=True)
        
        # Resample to 4H
        df_4h = intraday_df.resample('4H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Keep trading hours only
        df_4h = df_4h.between_time('09:00', '15:00')
        
        if len(df_4h) < 20:  # Need minimum data
            print(f"⚠️ {ticker}: Not enough 4H bars ({len(df_4h)})")
            return None
        
        return df_4h
        
    except Exception as e:
        print(f"⚠️ {ticker}: Error getting 4H data - {e}")
        return None


def get_intraday_1h_data(ticker, days_back=10):
    """
    Get 1H intraday data for volume climax detection
    
    Args:
        ticker: Stock symbol
        days_back: Number of days to fetch
    
    Returns:
        DataFrame: 1H OHLCV data
    """
    try:
        stock = Vnstock().stock(symbol=ticker, source='VCI')
        
        # Get intraday data
        intraday_df = stock.quote.intraday(symbol=ticker, page_size=200)
        
        if intraday_df is None or len(intraday_df) == 0:
            return None
        
        # Convert time to datetime
        if 'time' in intraday_df.columns:
            intraday_df['datetime'] = pd.to_datetime(intraday_df['time'])
            intraday_df.set_index('datetime', inplace=True)
        
        # Resample to 1H
        df_1h = intraday_df.resample('1H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Keep trading hours
        df_1h = df_1h.between_time('09:00', '15:00')
        
        if len(df_1h) < 30:
            return None
        
        return df_1h
        
    except Exception as e:
        print(f"⚠️ {ticker}: Error getting 1H data - {e}")
        return None


# ============================================================================
# TECHNICAL INDICATOR CALCULATIONS
# ============================================================================

def calculate_macd(df):
    """
    Calculate MACD indicator
    
    Returns:
        DataFrame with macd, signal, histogram columns added
    """
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_histogram'] = histogram
    
    return df


def calculate_rsi(df, period=14):
    """
    Calculate RSI indicator
    
    Returns:
        DataFrame with rsi column added
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    df['rsi'] = rsi
    
    return df


# ============================================================================
# EXIT CRITERION 1: DAILY MACD + RSI>80 + SUPPORT BREAK
# ============================================================================

def detect_macd_divergence(df, lookback=20):
    """
    Detect MACD bearish divergence
    
    Returns:
        dict: Divergence signal if detected, None otherwise
    """
    if len(df) < lookback:
        return None
    
    # Calculate MACD if not already done
    if 'macd' not in df.columns:
        df = calculate_macd(df)
    
    recent = df.tail(lookback)
    
    # Find price peaks
    price_peaks = []
    for i in range(1, len(recent) - 1):
        if (recent['close'].iloc[i] > recent['close'].iloc[i-1] and
            recent['close'].iloc[i] > recent['close'].iloc[i+1]):
            price_peaks.append({
                'idx': i,
                'price': recent['close'].iloc[i],
                'macd': recent['macd'].iloc[i]
            })
    
    if len(price_peaks) < 2:
        return None
    
    # Compare last 2 peaks
    peak1 = price_peaks[-2]
    peak2 = price_peaks[-1]
    
    # Bearish divergence: price higher, MACD lower
    price_higher = peak2['price'] > peak1['price']
    macd_lower = peak2['macd'] < peak1['macd']
    
    if price_higher and macd_lower:
        return {
            'detected': True,
            'peak1_price': peak1['price'],
            'peak2_price': peak2['price'],
            'peak1_macd': peak1['macd'],
            'peak2_macd': peak2['macd']
        }
    
    return None


def find_support_levels(df, window=50, threshold=0.02):
    """
    Find support levels using recent lows
    
    Args:
        df: Price dataframe
        window: Lookback period
        threshold: Price clustering threshold (2%)
    
    Returns:
        list: Support levels (top 3)
    """
    if len(df) < window:
        return []
    
    recent = df.tail(window)
    
    # Find local lows
    lows = []
    for i in range(1, len(recent) - 1):
        if (recent['low'].iloc[i] <= recent['low'].iloc[i-1] and
            recent['low'].iloc[i] <= recent['low'].iloc[i+1]):
            lows.append(recent['low'].iloc[i] * 1000)
    
    if len(lows) < 3:
        return []
    
    # Cluster lows
    from collections import Counter
    rounded_lows = [round(low / (low * threshold)) * (low * threshold) for low in lows]
    support_counter = Counter(rounded_lows)
    
    # Top 3 most tested levels
    top_supports = [s[0] for s in support_counter.most_common(3)]
    
    return top_supports


def check_support_break(df, support_levels):
    """
    Check if any support level is broken with volume confirmation
    
    Returns:
        dict: Break signal if detected
    """
    if not support_levels or len(df) < 2:
        return None
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    current_close = current['close'] * 1000
    prev_close = prev['close'] * 1000
    current_volume = current['volume']
    
    # Average volume (last 20 days)
    avg_volume = df['volume'].tail(20).mean()
    
    for support in support_levels:
        # Break conditions:
        # 1. Current close < support
        # 2. Previous close >= support (fresh break)
        # 3. Volume > 1.2x average (confirmation)
        
        if (current_close < support and
            prev_close >= support and
            current_volume > avg_volume * 1.2):
            
            break_pct = ((support - current_close) / support) * 100
            
            return {
                'detected': True,
                'support_level': support,
                'current_price': current_close,
                'break_pct': break_pct,
                'volume_ratio': current_volume / avg_volume
            }
    
    return None


def check_daily_critical_exit(df):
    """
    EXIT CRITERION 1: Daily MACD + RSI>80 + Support break
    → BÁN 100% (CRITICAL)
    
    Returns:
        dict: Exit signal if all 3 conditions met
    """
    if df is None or len(df) < 50:
        return None
    
    # Calculate indicators
    df = calculate_macd(df)
    df = calculate_rsi(df)
    
    # Check 1: MACD Divergence
    macd_div = detect_macd_divergence(df)
    
    # Check 2: RSI > 80
    current_rsi = df['rsi'].iloc[-1]
    rsi_extreme = current_rsi > 80
    
    # Check 3: Support Break
    supports = find_support_levels(df)
    support_break = check_support_break(df, supports)
    
    # All 3 must be TRUE
    if macd_div and rsi_extreme and support_break:
        return {
            'signal': 'DAILY_CRITICAL_EXIT',
            'macd_divergence': macd_div,
            'rsi': current_rsi,
            'support_break': support_break,
            'action': 'SELL',
            'exit_pct': 100,
            'urgency': 'CRITICAL',
            'note': f'Daily MACD div + RSI={current_rsi:.0f} + Support break @ {support_break["support_level"]:,.0f}',
            'confidence': 'EXTREME_HIGH'
        }
    
    return None


# ============================================================================
# EXIT CRITERION 2: 4H MACD + VOLUME DIVERGENCE
# ============================================================================

def detect_volume_divergence(df, lookback=20):
    """
    Detect volume divergence
    Price higher but volume lower = Weakness
    
    Returns:
        dict: Divergence signal if detected
    """
    if len(df) < lookback:
        return None
    
    recent = df.tail(lookback)
    
    # Find price peaks with volume
    peaks = []
    for i in range(1, len(recent) - 1):
        if (recent['close'].iloc[i] > recent['close'].iloc[i-1] and
            recent['close'].iloc[i] > recent['close'].iloc[i+1]):
            peaks.append({
                'idx': i,
                'price': recent['close'].iloc[i],
                'volume': recent['volume'].iloc[i]
            })
    
    if len(peaks) < 2:
        return None
    
    peak1 = peaks[-2]
    peak2 = peaks[-1]
    
    # Divergence: price higher, volume lower
    price_higher = peak2['price'] > peak1['price']
    volume_lower = peak2['volume'] < peak1['volume']
    
    if price_higher and volume_lower:
        volume_drop_pct = ((peak1['volume'] - peak2['volume']) / peak1['volume']) * 100
        
        return {
            'detected': True,
            'volume_drop_pct': volume_drop_pct,
            'peak1_volume': peak1['volume'],
            'peak2_volume': peak2['volume']
        }
    
    return None


def check_4h_medium_exit(df_4h):
    """
    EXIT CRITERION 2: 4H MACD + Volume divergence
    → BÁN 50% (HIGH)
    
    Returns:
        dict: Exit signal if both conditions met
    """
    if df_4h is None or len(df_4h) < 30:
        return None
    
    # Calculate MACD on 4H
    df_4h = calculate_macd(df_4h)
    
    # Check 1: MACD Divergence on 4H
    macd_div = detect_macd_divergence(df_4h, lookback=15)
    
    # Check 2: Volume Divergence
    vol_div = detect_volume_divergence(df_4h, lookback=15)
    
    # Both must be TRUE
    if macd_div and vol_div:
        return {
            'signal': '4H_MEDIUM_EXIT',
            'macd_divergence': macd_div,
            'volume_divergence': vol_div,
            'action': 'SELL',
            'exit_pct': 50,
            'urgency': 'HIGH',
            'note': f'4H MACD div + Volume drop {vol_div["volume_drop_pct"]:.0f}%',
            'confidence': 'HIGH'
        }
    
    return None


# ============================================================================
# EXIT CRITERION 3: 1H VOLUME CLIMAX (BSR PATTERN)
# ============================================================================

def detect_climax_volume_1h(df_1h, lookback_hours=40, volume_multiplier=2.5):
    """
    Detect volume climax on 1H chart (BSR pattern)
    Volume spike @ near high = Distribution
    
    Returns:
        dict: Climax signal if detected
    """
    if df_1h is None or len(df_1h) < lookback_hours:
        return None
    
    recent = df_1h.tail(lookback_hours + 1)
    current = recent.iloc[-1]
    
    current_price = current['close'] * 1000
    current_volume = current['volume']
    
    # Average volume (excluding current)
    avg_volume = recent['volume'].iloc[:-1].mean()
    
    # Recent high/low
    recent_high = recent['high'].max() * 1000
    recent_low = recent['low'].min() * 1000
    
    # Condition 1: Volume spike (>> average)
    volume_ratio = current_volume / avg_volume
    is_volume_spike = volume_ratio >= volume_multiplier
    
    if not is_volume_spike:
        return None
    
    # Condition 2: At/near high (top 10% of range)
    range_position = (current_price - recent_low) / (recent_high - recent_low)
    is_near_high = range_position >= 0.90
    
    if not is_near_high:
        return None
    
    # Condition 3: Uptrend before (check last 20 bars)
    if len(df_1h) >= 25:
        price_20h_ago = df_1h.iloc[-20]['close'] * 1000
        is_uptrend = current_price > price_20h_ago * 1.03
    else:
        is_uptrend = True
    
    if not is_uptrend:
        return None
    
    # CLIMAX DETECTED!
    return {
        'signal': '1H_VOLUME_CLIMAX',
        'current_price': current_price,
        'volume_ratio': volume_ratio,
        'range_position': range_position * 100,
        'action': 'SELL',
        'exit_pct': 100,
        'urgency': 'HIGH',
        'note': f'1H volume spike {volume_ratio:.1f}x @ top {range_position*100:.0f}%',
        'confidence': 'VERY_HIGH'
    }


def detect_distribution_pattern_1h(df_1h, lookback_hours=60):
    """
    Detect distribution pattern - Multiple volume spikes @ resistance
    BSR pattern: 2+ spikes in resistance zone
    
    Returns:
        dict: Distribution signal if detected
    """
    if df_1h is None or len(df_1h) < lookback_hours:
        return None
    
    recent = df_1h.tail(lookback_hours)
    
    # Find resistance zone (top 15%)
    recent_high = recent['high'].max() * 1000
    recent_low = recent['low'].min() * 1000
    resistance_zone = recent_high - (recent_high - recent_low) * 0.15
    
    # Find volume spikes in resistance
    avg_volume = recent['volume'].mean()
    spikes = []
    
    for i in range(len(recent)):
        bar = recent.iloc[i]
        price = bar['close'] * 1000
        volume = bar['volume']
        
        if price >= resistance_zone and volume > avg_volume * 2.0:
            spikes.append({
                'idx': i,
                'time': recent.index[i],
                'price': price,
                'volume': volume,
                'volume_ratio': volume / avg_volume
            })
    
    # Need at least 2 spikes
    if len(spikes) < 2:
        return None
    
    # Check time span (should be 4-40 hours)
    time_diff = (spikes[-1]['time'] - spikes[0]['time']).total_seconds() / 3600
    
    if not (4 <= time_diff <= 40):
        return None
    
    # Check if failed to make new high
    max_spike_price = max(s['price'] for s in spikes)
    current_price = recent['close'].iloc[-1] * 1000
    failed_new_high = current_price < max_spike_price * 0.97
    
    if failed_new_high:
        return {
            'signal': '1H_DISTRIBUTION_PATTERN',
            'num_spikes': len(spikes),
            'resistance_zone': resistance_zone,
            'time_span_hours': time_diff,
            'failed_new_high': True,
            'action': 'SELL',
            'exit_pct': 100,
            'urgency': 'CRITICAL',
            'note': f'{len(spikes)} volume spikes 1H @ resistance - Distribution!',
            'confidence': 'EXTREME_HIGH'
        }
    
    return None


def check_1h_climax_exit(df_1h):
    """
    EXIT CRITERION 3: 1H Volume Climax (BSR pattern)
    → BÁN 100% (HIGH)
    
    Checks both:
    - Distribution pattern (multiple spikes) - PRIORITY
    - Single climax (single spike)
    
    Returns:
        dict: Exit signal if detected
    """
    if df_1h is None:
        return None
    
    # Priority 1: Distribution pattern (stronger signal)
    distribution = detect_distribution_pattern_1h(df_1h)
    if distribution:
        return distribution
    
    # Priority 2: Single climax
    climax = detect_climax_volume_1h(df_1h)
    if climax:
        return climax
    
    return None


# ============================================================================
# MAIN SCANNER
# ============================================================================

def scan_for_sell_signals():
    """
    Main sell signal scanner with 3 technical exit criteria
    
    PRIORITY ORDER:
    1. Stop Loss (URGENT!)
    2. Daily Critical Exit (MACD+RSI+Support) → 100%
    3. 1H Volume Climax (BSR pattern) → 100%
    4. 4H Medium Exit (MACD+Volume div) → 50%
    5. Take Profit
    
    Returns:
        list: Sell signals to execute
    """
    print("\n" + "="*80)
    print("🔍 SELL SIGNAL SCANNER v5.3 - TECHNICAL EXIT CRITERIA")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get open BUY signals
    cursor.execute("""
        SELECT 
            ticker,
            signal_code,
            entry_price,
            stop_loss,
            take_profit,
            position_pct,
            date
        FROM signals
        WHERE action = 'BUY'
          AND status = 'open'
        ORDER BY ticker
    """)
    
    open_signals = cursor.fetchall()
    conn.close()
    
    if not open_signals:
        print("\n✅ Không có signal nào đang open")
        return []
    
    print(f"\n📋 Checking {len(open_signals)} open positions\n")
    
    signals_to_sell = []
    
    for signal in open_signals:
        ticker = signal[0]
        signal_code = signal[1]
        entry_price = signal[2]
        stop_loss = signal[3]
        take_profit = signal[4]
        position_pct = signal[5]
        entry_date = signal[6]
        
        print(f"🔍 {ticker} ({signal_code})...", end=" ")
        
        try:
            # Get daily data
            df_daily = get_daily_data(ticker, days_back=100)
            
            if df_daily is None or len(df_daily) == 0:
                print("⚠️ No data")
                continue
            
            current_price = df_daily['close'].iloc[-1] * 1000
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            # ========================================
            # PRIORITY 1: STOP LOSS (URGENT!)
            # ========================================
            if current_price <= stop_loss:
                print(f"🚨 STOP LOSS @ {current_price:,.0f}")
                
                signals_to_sell.append({
                    'ticker': ticker,
                    'signal_code': signal_code,
                    'exit_reason': 'STOP_LOSS',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'profit_loss_pct': pnl_pct,
                    'exit_quantity_pct': 100,
                    'position_pct': position_pct,
                    'note': f'Stop loss triggered',
                    'urgency': 'CRITICAL'
                })
                continue
            
            # ========================================
            # PRIORITY 2: DAILY CRITICAL EXIT
            # MACD + RSI>80 + Support break → 100%
            # ========================================
            daily_exit = check_daily_critical_exit(df_daily)
            
            if daily_exit:
                print(f"🚨 DAILY CRITICAL! RSI={daily_exit['rsi']:.0f}")
                
                signals_to_sell.append({
                    'ticker': ticker,
                    'signal_code': signal_code,
                    'exit_reason': 'DAILY_CRITICAL_EXIT',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'profit_loss_pct': pnl_pct,
                    'exit_quantity_pct': 100,
                    'position_pct': position_pct,
                    'note': daily_exit['note'],
                    'urgency': 'CRITICAL',
                    'signal_details': daily_exit
                })
                continue
            
            # ========================================
            # PRIORITY 3: 1H VOLUME CLIMAX
            # BSR pattern → 100%
            # ========================================
            df_1h = get_intraday_1h_data(ticker, days_back=10)
            
            if df_1h is not None:
                climax_1h = check_1h_climax_exit(df_1h)
                
                if climax_1h:
                    print(f"⚠️ 1H CLIMAX! {climax_1h['signal']}")
                    
                    signals_to_sell.append({
                        'ticker': ticker,
                        'signal_code': signal_code,
                        'exit_reason': climax_1h['signal'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'profit_loss_pct': pnl_pct,
                        'exit_quantity_pct': climax_1h['exit_pct'],
                        'position_pct': position_pct,
                        'note': climax_1h['note'],
                        'urgency': climax_1h['urgency'],
                        'signal_details': climax_1h
                    })
                    continue
            
            # ========================================
            # PRIORITY 4: 4H MEDIUM EXIT
            # MACD + Volume div → 50%
            # ========================================
            df_4h = get_intraday_4h_data(ticker, days_back=15)
            
            if df_4h is not None:
                medium_4h = check_4h_medium_exit(df_4h)
                
                if medium_4h:
                    print(f"⚠️ 4H MEDIUM! Bán 50%")
                    
                    signals_to_sell.append({
                        'ticker': ticker,
                        'signal_code': signal_code,
                        'exit_reason': '4H_MEDIUM_EXIT',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'profit_loss_pct': pnl_pct,
                        'exit_quantity_pct': 50,
                        'position_pct': position_pct,
                        'note': medium_4h['note'],
                        'urgency': 'HIGH',
                        'signal_details': medium_4h
                    })
                    continue
            
            # ========================================
            # PRIORITY 5: TAKE PROFIT
            # ========================================
            if current_price >= take_profit:
                # Partial TP
                if position_pct == 100:
                    exit_qty = 50
                elif position_pct == 50:
                    exit_qty = 30
                else:
                    exit_qty = position_pct
                
                print(f"✅ TP! Exit {exit_qty}%")
                
                signals_to_sell.append({
                    'ticker': ticker,
                    'signal_code': signal_code,
                    'exit_reason': 'TAKE_PROFIT',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'profit_loss_pct': pnl_pct,
                    'exit_quantity_pct': exit_qty,
                    'position_pct': position_pct,
                    'note': f'Take profit - exit {exit_qty}%',
                    'urgency': 'MEDIUM'
                })
                continue
            
            # No signal
            print(f"✅ No signal (P/L: {pnl_pct:+.2f}%)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    if signals_to_sell:
        print("\n" + "="*80)
        print(f"🚨 FOUND {len(signals_to_sell)} SELL SIGNALS!")
        print("="*80)
        
        for sig in signals_to_sell:
            print(f"   {sig['ticker']}: {sig['exit_reason']} - Exit {sig['exit_quantity_pct']}% - {sig['urgency']}")
        
        print("="*80)
    else:
        print("\n✅ No sell signals detected")
    
    return signals_to_sell


# ============================================================================
# EXECUTE SELL SIGNALS
# ============================================================================

def execute_sell_signals(signals_to_sell):
    """
    Save sell signals to database and update positions
    """
    if not signals_to_sell:
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for sig in signals_to_sell:
        try:
            # Insert SELL signal
            cursor.execute("""
                INSERT INTO signals 
                (ticker, action, entry_price, exit_price, stop_loss, take_profit,
                 profit_loss_pct, exit_quantity_pct, exit_reason, signal_code,
                 buy_signal_code, note, date, status)
                VALUES (%s, 'SELL', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, 'executed')
            """, (
                sig['ticker'],
                sig['entry_price'],
                sig['exit_price'],
                sig['stop_loss'],
                sig['take_profit'],
                sig['profit_loss_pct'],
                sig['exit_quantity_pct'],
                sig['exit_reason'],
                f"{sig['ticker']}-SELL-{datetime.now().strftime('%Y%m%d%H%M')}",
                sig['signal_code'],
                sig['note']
            ))
            
            # Update BUY signal position
            new_position_pct = sig['position_pct'] - sig['exit_quantity_pct']
            
            if new_position_pct <= 0:
                # Full exit
                cursor.execute("""
                    UPDATE signals
                    SET status = 'closed', position_pct = 0
                    WHERE signal_code = %s
                """, (sig['signal_code'],))
            else:
                # Partial exit
                cursor.execute("""
                    UPDATE signals
                    SET position_pct = %s
                    WHERE signal_code = %s
                """, (new_position_pct, sig['signal_code']))
            
            print(f"✅ {sig['ticker']}: Saved SELL signal")
            
        except Exception as e:
            print(f"❌ {sig['ticker']}: Error - {e}")
            conn.rollback()
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Executed {len(signals_to_sell)} sell signals!")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Check if running during trading hours (9:30-15:30 VN time)
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # Weekend check (Saturday=5, Sunday=6)
    if now.weekday() >= 5:
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        print("\n" + "="*80)
        print(f"⏰ TODAY IS {day_names[now.weekday()].upper()}")
        print("="*80)
        print("\n📅 Stock market is CLOSED on weekends")
        print("   Markets are open Monday-Friday only")
        print("\n✅ Scanner will exit gracefully")
        print("   Run again on Monday during trading hours (9:30-15:30)")
        print("\n" + "="*80 + "\n")
        sys.exit(0)
    
    # VN time check (assuming server is UTC+7)
    if current_hour < 9 or (current_hour == 9 and current_minute < 30):
        print(f"⏰ Before market hours ({now.strftime('%H:%M')})")
        print("   Scanner runs 9:30-15:30 VN time")
        sys.exit(0)
    
    if current_hour > 15 or (current_hour == 15 and current_minute > 30):
        print(f"⏰ After market hours ({now.strftime('%H:%M')})")
        print("   Use daily_eod_workflow.py for EOD scan")
        sys.exit(0)
    
    # Run scanner
    sell_signals = scan_for_sell_signals()
    
    # Execute signals
    if sell_signals:
        # Auto-execute in CI/GitHub Actions
        if os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true':
            print(f"\n🤖 CI Environment - Auto-executing {len(sell_signals)} signals...")
            execute_sell_signals(sell_signals)
        else:
            # Manual confirmation for local runs
            response = input(f"\n⚠️ Execute {len(sell_signals)} sell signals? (y/n): ")
            if response.lower() == 'y':
                execute_sell_signals(sell_signals)
            else:
                print("❌ Cancelled - signals not executed")
    
    print("\n✅ Scanner completed!")
