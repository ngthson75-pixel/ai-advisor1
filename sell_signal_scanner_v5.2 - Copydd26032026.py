#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL SCANNER V5.2 - T+2 Settlement (2 Trading Days)
===========================================================

CRITICAL UNDERSTANDING:
  T+2 CHIỀU: Cổ phiếu về tài khoản
  T+2 CHIỀU: BÁN ĐƯỢC NGAY! ✅
  
QUY ĐỊNH TTCK VIỆT NAM:
  → Phải giữ 2 NGÀY GIAO DỊCH (T+2 chiều bán được)

EXAMPLE T+2 SETTLEMENT:
  Mua: 27/02 (T6)
  T+1: 03/03 (T2) - trading day 1 - CHƯA được bán
  T+2: 04/03 (T3) - trading day 2 - CHIỀU BÁN ĐƯỢC! ✅

EXIT STRATEGY V5.2:
  0. T+2 Settlement: Giữ 2 trading days (T+2 chiều bán được)
  1. Stop Loss: Bán 100%
  2. TP1: Bán 50%
  3. TP2: Bán 30%
  4. TP Pullback: Bán 50%
  5. Trailing: Bán 20%
  6. MA20 STRICT: 2 ngày < MA20 VÀ (thua >= 3% OR lời < 2%)
"""

import os
import sys
import time
import argparse
import json
import requests
from datetime import datetime, timedelta

try:
    from vnstock import Vnstock
except ImportError:
    from vnstock3 import Vnstock


# ========================================================================
# CONFIGURATION
# ========================================================================

PROD_API = 'https://ai-advisor1-backend.onrender.com/api'
STAGING_API = 'https://ai-advisor1-staging.onrender.com/api'

T_PLUS_TRADING_DAYS = 2  # T+2 chiều cổ phiếu về → bán được ngay!


# ========================================================================
# VIETNAM MARKET CALENDAR
# ========================================================================

def load_vietnam_holidays():
    """Load Vietnam holidays from vietnam_holidays.json"""
    try:
        holidays_file = os.path.join(os.path.dirname(__file__), 'vietnam_holidays.json')
        with open(holidays_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Flatten all years into single list
        all_holidays = []
        for year, dates in data.get('holidays', {}).items():
            all_holidays.extend(dates)
        
        # Convert to datetime objects
        holiday_dates = set()
        for date_str in all_holidays:
            try:
                holiday_dates.add(datetime.strptime(date_str, '%Y-%m-%d').date())
            except:
                pass
        
        return holiday_dates
    except:
        # Fallback: no holidays if file not found
        return set()


VIETNAM_HOLIDAYS = load_vietnam_holidays()


def is_trading_day(date):
    """
    Check if a date is a trading day (Mon-Fri, not holiday)
    
    Args:
        date: datetime.date object
    
    Returns:
        bool: True if trading day
    """
    # Weekend check (5=Saturday, 6=Sunday in Python)
    if date.weekday() >= 5:
        return False
    
    # Holiday check
    if date in VIETNAM_HOLIDAYS:
        return False
    
    return True


def count_trading_days(start_date, end_date):
    """
    Count number of trading days between two dates (inclusive)
    
    Args:
        start_date: datetime or string 'YYYY-MM-DD'
        end_date: datetime or string 'YYYY-MM-DD'
    
    Returns:
        int: Number of trading days
    """
    # Parse dates
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    elif isinstance(start_date, datetime):
        start_date = start_date.date()
    
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    elif isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Count trading days
    trading_days = 0
    current = start_date
    
    while current <= end_date:
        if is_trading_day(current):
            trading_days += 1
        current += timedelta(days=1)
    
    return trading_days


def can_sell_t_plus_2(signal_date_str):
    """
    Kiểm tra có được bán theo quy định T+2 settlement chưa
    
    QUY ĐỊNH TTCK VIỆT NAM:
    - T+2 CHIỀU: Cổ phiếu về tài khoản
    - T+2 CHIỀU: BÁN ĐƯỢC NGAY! ✅
    → Phải giữ 2 NGÀY GIAO DỊCH (T+2 chiều bán được)
    
    Args:
        signal_date_str: Date string 'YYYY-MM-DD' (ngày mua)
    
    Returns:
        tuple: (can_sell: bool, trading_days_held: int)
        
    Example:
        Mua 27/02 (T6)
        03/03 (T2) = TD+1 → can_sell = False (CHƯA được bán)
        04/03 (T3) = TD+2 → can_sell = True ✅ (chiều bán được!)
    """
    try:
        signal_date = datetime.strptime(signal_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # Count TRADING days từ ngày sau khi mua
        trading_days_held = count_trading_days(signal_date + timedelta(days=1), today)
        
        # T+2 chiều bán được = phải >= 2 trading days
        can_sell = trading_days_held >= T_PLUS_TRADING_DAYS
        
        return can_sell, trading_days_held
    except:
        return True, 999


# ========================================================================
# STEP 1: Lấy BUY signals từ API
# ========================================================================

def get_buy_signals_from_api(api_url):
    """Lấy danh sách BUY signals đang active từ production/staging API"""
    
    print(f"📡 Fetching BUY signals từ: {api_url}/signals")
    
    # Wake backend
    base_url = api_url.replace('/api', '')
    for attempt in range(3):
        try:
            print(f"  ⏳ Wake attempt {attempt + 1}/3...")
            wake_response = requests.get(f"{base_url}/health", timeout=10)
            if wake_response.status_code == 200:
                print(f"  ✅ Backend awake!")
                break
        except:
            if attempt < 2:
                print(f"  ⏸️ Waiting 5s...")
                time.sleep(5)
    
    # Fetch with retry
    max_retries = 2
    for retry in range(max_retries):
        try:
            timeout = 60 if retry > 0 else 30
            print(f"  📥 Fetching signals (timeout={timeout}s)...")
            
            response = requests.get(f"{api_url}/signals", timeout=timeout)
            
            if response.status_code != 200:
                if retry < max_retries - 1:
                    time.sleep(5)
                    continue
                return []
            
            data = response.json()
            all_signals = data.get('signals', [])
            
            buy_signals = [
                s for s in all_signals
                if s.get('action') == 'BUY' and s.get('position_pct', 100) > 0
            ]
            
            print(f"✅ Tìm thấy {len(buy_signals)} BUY signals (từ {len(all_signals)} tổng)")
            
            return buy_signals
            
        except:
            if retry < max_retries - 1:
                time.sleep(10)
            else:
                return []
    
    return []


# ========================================================================
# STEP 2: Lấy giá từ VNStock
# ========================================================================

def get_stock_data(ticker, days=30):
    """Lấy dữ liệu giá từ VCI"""
    try:
        stock_api = Vnstock()
        stock = stock_api.stock(symbol=ticker, source='VCI')
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        df = stock.quote.history(start=start_date, end=end_date, interval='1D')
        
        if df is None or len(df) < 5:
            return None
        
        return df
        
    except Exception as e:
        print(f"  ⚠️ Lỗi lấy data {ticker}: {e}")
        return None


# ========================================================================
# STEP 3: Kiểm tra điều kiện SELL V5.2
# ========================================================================

def check_sell_conditions_v52(signal, df):
    """
    V5.2 EXIT STRATEGY - T+2 Settlement (2 trading days)
    
    CRITICAL:
    - T+2 chiều cổ phiếu về
    - T+2 chiều BÁN ĐƯỢC NGAY!
    - Phải giữ 2 TRADING DAYS
    
    FIXES:
    1. T+2 settlement = 2 trading days (T+2 chiều bán được!)
    2. MA20 STRICT = 2 ngày < MA20 VÀ (thua >= 3% OR lời < 2%)
    
    EXIT RULES (sau khi đủ T+2):
    1. STOP_LOSS: <= SL → 100%
    2. TAKE_PROFIT_1: >= TP → 50%
    3. TAKE_PROFIT_2: >= TP*1.1 (pos=50%) → 30%
    4. TP_PULLBACK: < TP*0.97 (pos=50%) → 50%
    5. TRAILING_STOP: < peak*0.95 (pos=20%) → 20%
    6. MA20_STRICT: < MA20 2 days VÀ (P/L <= -3% OR 0% <= P/L < 2%)
    """
    
    if df is None or len(df) < 20:
        return None
    
    ticker = signal['ticker']
    entry_price = signal.get('entry_price', 0)
    stop_loss = signal.get('stop_loss', 0)
    take_profit = signal.get('take_profit', 0)
    position_pct = signal.get('position_pct', 100)
    signal_code = signal.get('signal_code', '')
    signal_date = signal.get('date', '')
    
    if position_pct <= 0:
        return None
    
    # T+2 TRADING DAYS check
    can_sell, trading_days_held = can_sell_t_plus_2(signal_date)
    
    # Giá hiện tại
    raw_price = df['close'].iloc[-1]
    if entry_price > 1000 and raw_price < 1000:
        price_multiplier = 1000
    else:
        price_multiplier = 1
    current_price = raw_price * price_multiplier
    
    # MA20
    df['ma20'] = df['close'].rolling(20).mean()
    ma20 = df['ma20'].iloc[-1] * price_multiplier
    prev_close = (df['close'].iloc[-2] if len(df) >= 2 else raw_price) * price_multiplier
    prev_ma20 = (df['ma20'].iloc[-2] if len(df) >= 2 else ma20) * price_multiplier
    
    # Đỉnh gần nhất
    recent_high = df['close'].tail(20).max() * price_multiplier
    
    # P/L
    pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
    
    # ========================================================================
    # T+2 GATE - ÁP DỤNG CHO TẤT CẢ (kể cả SL)
    # ========================================================================
    # Quy định TTCK Việt Nam: T+2 chiều mới có cổ phiếu → KHÔNG THỂ bán trước!
    if not can_sell:
        # Nếu SL đã chạm nhưng chưa T+2 → Ghi nhận nhưng không execute
        if stop_loss > 0 and current_price <= stop_loss:
            # TODO: Log warning - SL hit but cannot sell until T+2
            pass
        return None
    
    # ========================================================================
    # CHECK 1: STOP LOSS (sau khi đủ T+2)
    # ========================================================================
    if stop_loss > 0 and current_price <= stop_loss:
        return {
            'ticker': ticker,
            'exit_reason': 'STOP_LOSS',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': 100,
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'note': f'⚠️ STOP LOSS (TD+{trading_days_held})'
        }
    
    # ========================================================================
    # CHECK 1: TAKE PROFIT 1
    # ========================================================================
    if take_profit > 0 and current_price >= take_profit and position_pct == 100:
        return {
            'ticker': ticker,
            'exit_reason': 'TAKE_PROFIT_1',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': 50,
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'note': f'Bán 50% @ TP (TD+{trading_days_held})'
        }
    
    # CHECK 2: TAKE PROFIT 2
    if position_pct == 50 and take_profit > 0:
        tp2_price = take_profit * 1.1
        if current_price >= tp2_price:
            return {
                'ticker': ticker,
                'exit_reason': 'TAKE_PROFIT_2',
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'profit_loss_pct': round(pnl_pct, 2),
                'exit_quantity_pct': 30,
                'signal_code': signal_code,
                'buy_signal_code': signal_code,
                'note': f'Bán 30% @ TP+10% (TD+{trading_days_held})'
            }
    
    # CHECK 3: TP PULLBACK
    if position_pct == 50 and take_profit > 0:
        pullback_threshold = take_profit * 0.97
        if current_price < pullback_threshold:
            return {
                'ticker': ticker,
                'exit_reason': 'TP_PULLBACK',
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'profit_loss_pct': round(pnl_pct, 2),
                'exit_quantity_pct': 50,
                'signal_code': signal_code,
                'buy_signal_code': signal_code,
                'note': f'Pullback từ TP (TD+{trading_days_held})'
            }
    
    # CHECK 4: TRAILING STOP
    if position_pct == 20:
        if take_profit > 0 and recent_high > take_profit:
            trailing_stop_price = recent_high * 0.95
            if current_price <= trailing_stop_price:
                return {
                    'ticker': ticker,
                    'exit_reason': 'TRAILING_STOP',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'profit_loss_pct': round(pnl_pct, 2),
                    'exit_quantity_pct': 20,
                    'signal_code': signal_code,
                    'buy_signal_code': signal_code,
                    'note': f'Trailing: {recent_high:,.0f}→{trailing_stop_price:,.0f} (TD+{trading_days_held})'
                }
    
    # ========================================================================
    # CHECK 5: MA20 STRICT V5.2
    # ========================================================================
    # Điều kiện: < MA20 2 ngày VÀ (thua >= 3% HOẶC lời nhỏ < 2%)
    # → KHÔNG bán mã lời >= 2% (như CTR +2.47%)
    
    two_days_below_ma20 = (current_price < ma20 and prev_close < prev_ma20)
    
    # Thua nặng hoặc lời nhỏ
    significant_loss = (pnl_pct <= -3.0)
    small_profit = (0 <= pnl_pct < 2.0)
    
    if two_days_below_ma20 and (significant_loss or small_profit):
        reason_detail = ""
        if significant_loss:
            reason_detail = f"2 ngày < MA20 VÀ thua {pnl_pct:.1f}% (>= 3%)"
        elif small_profit:
            reason_detail = f"2 ngày < MA20 VÀ lời nhỏ {pnl_pct:.1f}% (< 2%)"
        
        return {
            'ticker': ticker,
            'exit_reason': 'MA20_STRICT',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': position_pct,
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'ma20': round(ma20, 0),
            'note': f'{reason_detail} (TD+{trading_days_held})'
        }
    
    return None


# ========================================================================
# STEP 4: Push SELL signals
# ========================================================================

def push_sell_signal(sell_signal, api_url):
    """Push SELL signal to API"""
    exit_pct = sell_signal['exit_quantity_pct']
    
    payload = {
        'ticker': sell_signal['ticker'],
        'action': 'SELL',
        'strategy': sell_signal['exit_reason'],
        'entry_price': sell_signal['entry_price'],
        'exit_price': sell_signal['exit_price'],  # ✅ FIX: Add exit_price!
        'exit_date': datetime.now().strftime('%Y-%m-%d'),  # ✅ FIX: Add exit_date!
        'stop_loss': sell_signal.get('stop_loss', 0),
        'take_profit': sell_signal.get('take_profit', 0),
        'strength': 80,
        'stock_type': 'Mid Cap',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'signal_code': f"SELL-{sell_signal['ticker']}-{datetime.now().strftime('%Y%m%d-%H%M')}",
        'buy_signal_code': sell_signal.get('buy_signal_code', ''),
        'status': 'closed' if exit_pct >= 100 else 'partial',
        'position_pct': 0 if exit_pct >= 100 else None,
        'exit_quantity_pct': exit_pct,
    }
    
    try:
        response = requests.post(f"{api_url}/signals", json=payload, timeout=15)
        return response.status_code in [200, 201]
    except:
        return False


# ========================================================================
# MAIN
# ========================================================================

def main():
    parser = argparse.ArgumentParser(description='SELL Signal Scanner V5.2')
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--delay', type=float, default=2.0)
    parser.add_argument('--staging', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    api_url = STAGING_API if args.staging else PROD_API
    env_name = 'STAGING' if args.staging else 'PRODUCTION'
    
    print("\n" + "=" * 70)
    print("🔍 SELL SIGNAL SCANNER V5.2 — T+2 Settlement (2 Trading Days)")
    print("=" * 70)
    print(f"🎯 API: {env_name}")
    print(f"⚙️ Settings: T+2 = {T_PLUS_TRADING_DAYS} trading days (chiều bán được)")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🗓️ Holidays loaded: {len(VIETNAM_HOLIDAYS)} dates")
    print()
    
    print("🎯 SELL RULES V5.2:")
    print(f"  0. T+2 SETTLEMENT: {T_PLUS_TRADING_DAYS} trading days (T+2 chiều bán được)")
    print("  1. SL: <= Stop Loss → 100%")
    print("  2. TP1: >= TP → 50%")
    print("  3. TP2: >= TP*1.1 (pos=50%) → 30%")
    print("  4. TP Pullback: < TP*0.97 (pos=50%) → 50%")
    print("  5. Trailing: < Peak*0.95 (pos=20%) → 20%")
    print("  6. MA20 STRICT: < MA20 2d VÀ (thua >=3% OR lời <2%)")
    print()
    
    # Lấy signals
    buy_signals = get_buy_signals_from_api(api_url)
    
    if not buy_signals:
        print("⚠️ Không có BUY signals")
        return
    
    # Group by ticker
    tickers_map = {}
    for s in buy_signals:
        ticker = s['ticker']
        if ticker not in tickers_map:
            tickers_map[ticker] = []
        tickers_map[ticker].append(s)
    
    tickers = sorted(tickers_map.keys())
    print(f"✅ {len(tickers)} mã cần quét: {', '.join(tickers[:10])}" + 
          (f" +{len(tickers)-10} mã khác" if len(tickers) > 10 else ""))
    print()
    
    # Quét
    sell_signals = []
    skipped_t_plus = []
    
    for i, ticker in enumerate(tickers):
        signals_for_ticker = tickers_map[ticker]
        
        print(f"[{i+1}/{len(tickers)}] {ticker}")
        
        if i > 0:
            time.sleep(args.delay)
        
        df = get_stock_data(ticker, days=args.days + 30)
        
        if df is None:
            continue
        
        raw_price = df['close'].iloc[-1]
        sample_entry = signals_for_ticker[0].get('entry_price', 0)
        multiplier = 1000 if (sample_entry > 1000 and raw_price < 1000) else 1
        current_price = raw_price * multiplier
        
        for j, signal in enumerate(signals_for_ticker):
            code = signal.get('signal_code', f"{ticker}-?")
            date = signal.get('date', '?')
            
            can_sell, trading_days = can_sell_t_plus_2(date)
            t_status = f"TD+{trading_days}" + (" ✅" if can_sell else " ⏳")
            
            print(f"  [{j+1}] {code} | {t_status}")
            
            result = check_sell_conditions_v52(signal, df)
            
            if result:
                reason = result['exit_reason']
                pnl = result['profit_loss_pct']
                qty = result['exit_quantity_pct']
                emoji = '🔴' if pnl < 0 else '🟢'
                print(f"    {emoji} SELL! {reason} | P/L: {pnl:+.2f}% | Bán: {qty}%")
                if result.get('note'):
                    print(f"       {result['note']}")
                sell_signals.append(result)
            else:
                if not can_sell:
                    print(f"    ⏳ Chưa đủ T+{T_PLUS_TRADING_DAYS}")
                    skipped_t_plus.append(code)
                else:
                    print(f"    ✅ Chưa chạm điều kiện")
    
    # Kết quả
    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ V5.2")
    print("=" * 70)
    print(f"✅ Mã quét: {len(tickers)}")
    print(f"🔴 SELL: {len(sell_signals)}")
    print(f"⏳ Skip (chưa T+2): {len(skipped_t_plus)}")
    
    if skipped_t_plus:
        print(f"\n⏳ Chưa đủ {T_PLUS_TRADING_DAYS} trading days (T+2 chiều bán được):")
        print(f"   {', '.join(skipped_t_plus[:5])}" +
              (f" +{len(skipped_t_plus)-5}" if len(skipped_t_plus) > 5 else ""))
    
    if sell_signals:
        print("\n📋 SELL signals:")
        for s in sell_signals:
            emoji = '🔴' if s['profit_loss_pct'] < 0 else '🟢'
            print(f"\n  {emoji} {s['ticker']} — {s['exit_reason']}")
            print(f"     {s['entry_price']:,.0f} → {s['exit_price']:,.0f} | " +
                  f"{s['profit_loss_pct']:+.2f}% | {s['exit_quantity_pct']}%")
            if s.get('note'):
                print(f"     {s['note']}")
        
        if not args.dry_run:
            confirm = input(f"\nĐẩy {len(sell_signals)} signals lên {env_name}? (y/n): ").lower()
            if confirm == 'y':
                success = sum(1 for s in sell_signals if push_sell_signal(s, api_url))
                print(f"✅ {success}/{len(sell_signals)} pushed")
        else:
            print("\n⚠️ DRY RUN")
    
    print()


if __name__ == '__main__':
    main()
