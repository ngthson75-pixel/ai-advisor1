#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL SCANNER V5.1 - Vietnam Market Optimized
====================================================

CHANGES FROM V5.0:
  V5.0: Bán ngay khi < MA20 (1 ngày), không check T+2
  V5.1: 
    - ✅ T+2 Filter: Chỉ bán sau T+2 (chiều ngày thứ 3)
    - ✅ MA20 Strict: < MA20 VÀ (2 ngày liên tiếp HOẶC thua >= 3%)
    - ✅ Stop Loss Priority: Vẫn bán ngay nếu chạm SL (bất kể T+2)

EXIT STRATEGY V5.1:
  0. T+2 CHECK: Nếu signal < 2 ngày → SKIP (trừ SL)
  1. TP (110k):           Bán 50% (nếu >= T+2)
  2. TP+10% (121k):       Bán 30%
  3. TP Pullback (106.7k): Bán 50%
  4. Trailing Stop (5%):  Bán 20%
  5. MA20 STRICT:         < MA20 VÀ (2 ngày HOẶC thua >= 3%)
  6. Stop Loss:           Bán 100% (NGAY, bất kể T+2)

Cách chạy:
  python sell_signal_scanner_v5.1.py --dry-run
  python sell_signal_scanner_v5.1.py --staging --dry-run
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

# Vietnam market T+2 rule
T_PLUS_DAYS = 2  # Chỉ được bán sau 2 ngày


# ========================================================================
# HELPER: Check T+2 Settlement
# ========================================================================

def can_sell_t_plus_2(signal_date_str):
    """
    Kiểm tra có được bán theo quy định T+2 chưa
    
    Args:
        signal_date_str: Date string 'YYYY-MM-DD'
    
    Returns:
        tuple: (can_sell: bool, days_held: int)
    """
    try:
        signal_date = datetime.strptime(signal_date_str, '%Y-%m-%d')
        days_held = (datetime.now() - signal_date).days
        
        # T+2 = phải giữ ít nhất 2 ngày
        can_sell = days_held >= T_PLUS_DAYS
        
        return can_sell, days_held
    except:
        # Nếu parse lỗi, assume có thể bán (fallback)
        return True, 999


# ========================================================================
# STEP 1: Lấy BUY signals từ API (with auto-retry)
# ========================================================================

def get_buy_signals_from_api(api_url):
    """Lấy danh sách BUY signals đang active từ production/staging API"""
    
    print(f"📡 Fetching BUY signals từ: {api_url}/signals")
    
    # Try to wake backend first (3 attempts)
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
            else:
                print(f"  ⚠️ Backend may be sleeping, trying anyway...")
    
    # Fetch signals with retry
    max_retries = 2
    for retry in range(max_retries):
        try:
            timeout = 60 if retry > 0 else 30
            print(f"  📥 Fetching signals (timeout={timeout}s)...")
            
            response = requests.get(f"{api_url}/signals", timeout=timeout)
            
            if response.status_code != 200:
                print(f"  ❌ API trả về status {response.status_code}")
                if retry < max_retries - 1:
                    print(f"  🔄 Retry {retry + 1}/{max_retries}...")
                    time.sleep(5)
                    continue
                return []
            
            data = response.json()
            all_signals = data.get('signals', [])
            
            # Lọc BUY signals đang có vị thế > 0
            buy_signals = [
                s for s in all_signals
                if s.get('action') == 'BUY' and s.get('position_pct', 100) > 0
            ]
            
            print(f"✅ Tìm thấy {len(buy_signals)} BUY signals đang có vị thế (từ {len(all_signals)} tổng)")
            
            return buy_signals
            
        except requests.exceptions.Timeout:
            print(f"  ⏱️ Timeout after {timeout}s")
            if retry < max_retries - 1:
                print(f"  🔄 Retry {retry + 1}/{max_retries}...")
                time.sleep(10)
            else:
                print("  ❌ Max retries reached")
                return []
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
            if retry < max_retries - 1:
                time.sleep(10)
            else:
                return []
    
    return []


# ========================================================================
# STEP 2: Lấy giá hiện tại từ VNStock
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
# STEP 3: Kiểm tra điều kiện SELL V5.1
# ========================================================================

def check_sell_conditions_v51(signal, df):
    """
    V5.1 EXIT STRATEGY - Vietnam Market Optimized
    
    CHANGES:
    1. T+2 Filter: Chỉ trigger SELL nếu signal >= 2 ngày (trừ SL)
    2. MA20 STRICT: Cần (2 ngày < MA20) HOẶC (< MA20 VÀ thua >= 3%)
    3. Stop Loss: LUÔN trigger ngay (override T+2)
    
    EXIT RULES:
    1. STOP_LOSS: Price <= SL → SELL 100% (NGAY, bất kể T+2)
    
    2. TAKE_PROFIT_1: Price >= TP AND position=100% → SELL 50%
       (Chỉ trigger nếu >= T+2)
    
    3. TAKE_PROFIT_2: Price >= TP*1.1 AND position=50% → SELL 30%
       (Chỉ trigger nếu >= T+2)
    
    4. TP_PULLBACK: Price < TP*0.97 AND position=50% → SELL 50%
       (Chỉ trigger nếu >= T+2)
    
    5. TRAILING_STOP: Price < recent_high*0.95 AND position=20% → SELL 20%
       (Chỉ trigger nếu >= T+2)
    
    6. MA20_STRICT: (Price < MA20 AND prev < MA20) OR (Price < MA20 AND P/L <= -3%)
       → SELL remaining (Chỉ trigger nếu >= T+2)
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
    
    # Đã bán hết
    if position_pct <= 0:
        return None
    
    # Check T+2
    can_sell, days_held = can_sell_t_plus_2(signal_date)
    
    # Giá hiện tại
    raw_price = df['close'].iloc[-1]
    
    # Auto-detect đơn vị
    if entry_price > 1000 and raw_price < 1000:
        price_multiplier = 1000
    else:
        price_multiplier = 1
    
    current_price = raw_price * price_multiplier
    
    # MA20
    df['ma20'] = df['close'].rolling(20).mean()
    ma20 = df['ma20'].iloc[-1] * price_multiplier
    
    # Giá ngày hôm trước
    prev_close = (df['close'].iloc[-2] if len(df) >= 2 else raw_price) * price_multiplier
    prev_ma20 = (df['ma20'].iloc[-2] if len(df) >= 2 else ma20) * price_multiplier
    
    # Đỉnh gần nhất
    recent_high = df['close'].tail(20).max() * price_multiplier
    
    # P/L %
    pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
    
    # ========================================================================
    # CHECK 0: STOP LOSS - PRIORITY #1 (Override T+2)
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
            'note': f'⚠️ STOP LOSS chạm - bán ngay (override T+{days_held})'
        }
    
    # ========================================================================
    # T+2 GATE: Nếu chưa đủ T+2 → SKIP tất cả checks còn lại
    # ========================================================================
    if not can_sell:
        # Chưa đủ T+2 → không trigger bất kỳ exit nào (trừ SL đã check trên)
        return None
    
    # ========================================================================
    # Từ đây trở xuống: Đã đủ T+2 → có thể trigger các exits
    # ========================================================================
    
    # CHECK 1: TAKE PROFIT 1
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
            'note': f'Bán 50% @ TP {take_profit:,.0f} (T+{days_held})'
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
                'note': f'Bán 30% @ TP+10% ({tp2_price:,.0f}) (T+{days_held})'
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
                'note': f'Pullback từ TP ({take_profit:,.0f}) → bán 50% (T+{days_held})'
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
                    'note': f'Trailing: Đỉnh {recent_high:,.0f} → {trailing_stop_price:,.0f} (T+{days_held})'
                }
    
    # ========================================================================
    # CHECK 5: MA20 STRICT (V5.1 - Cải tiến)
    # ========================================================================
    # Điều kiện: (2 ngày liên tiếp < MA20) HOẶC (< MA20 VÀ thua >= 3%)
    
    two_days_below_ma20 = (current_price < ma20 and prev_close < prev_ma20)
    below_ma20_and_losing = (current_price < ma20 and pnl_pct <= -3.0)
    
    if two_days_below_ma20 or below_ma20_and_losing:
        reason_detail = ""
        if two_days_below_ma20 and below_ma20_and_losing:
            reason_detail = "2 ngày < MA20 VÀ thua >= 3%"
        elif two_days_below_ma20:
            reason_detail = "2 ngày liên tiếp < MA20"
        else:
            reason_detail = f"< MA20 VÀ thua {pnl_pct:.1f}% (>= 3%)"
        
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
            'note': f'{reason_detail} (T+{days_held})'
        }
    
    # CHECK 6: MA20 High Volume (Bonus)
    avg_vol_20 = df['volume'].rolling(20).mean().iloc[-1]
    current_vol = df['volume'].iloc[-1]
    
    if current_price < ma20 and avg_vol_20 > 0 and current_vol > avg_vol_20 * 1.5:
        volume_ratio = round(current_vol / avg_vol_20, 2)
        return {
            'ticker': ticker,
            'exit_reason': 'MA20_HIGH_VOLUME',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': position_pct,
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'volume_ratio': volume_ratio,
            'note': f'< MA20 + Volume spike {volume_ratio}x (T+{days_held})'
        }
    
    return None


# ========================================================================
# STEP 4: Push SELL signals lên production
# ========================================================================

def push_sell_signal(sell_signal, api_url):
    """Đẩy 1 SELL signal lên production qua POST /api/signals"""
    
    exit_pct = sell_signal['exit_quantity_pct']
    
    if exit_pct >= 100:
        new_position_pct = 0
        new_status = 'closed'
    else:
        new_position_pct = None
        new_status = 'partial'
    
    payload = {
        'ticker': sell_signal['ticker'],
        'action': 'SELL',
        'strategy': sell_signal['exit_reason'],
        'entry_price': sell_signal['entry_price'],
        'stop_loss': sell_signal.get('stop_loss', 0),
        'take_profit': sell_signal.get('take_profit', 0),
        'strength': 80,
        'stock_type': 'Mid Cap',
        'rsi': 0,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'signal_code': f"SELL-{sell_signal['ticker']}-{datetime.now().strftime('%Y%m%d-%H%M')}",
        'buy_signal_code': sell_signal.get('buy_signal_code', ''),
        'status': new_status,
        'position_pct': new_position_pct if new_position_pct is not None else (0 if exit_pct >= 100 else 50),
        'exit_quantity_pct': exit_pct,
    }
    
    try:
        response = requests.post(f"{api_url}/signals", json=payload, timeout=15)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"  ❌ Error pushing: {e}")
        return False


# ========================================================================
# MAIN
# ========================================================================

def main():
    parser = argparse.ArgumentParser(description='SELL Signal Scanner V5.1')
    parser.add_argument('--days', type=int, default=30, help='Days of price data')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests')
    parser.add_argument('--staging', action='store_true', help='Use staging API')
    parser.add_argument('--dry-run', action='store_true', help='Scan only, no push')
    args = parser.parse_args()
    
    api_url = STAGING_API if args.staging else PROD_API
    env_name = 'STAGING' if args.staging else 'PRODUCTION'
    
    print("\n" + "=" * 70)
    print("🔍 SELL SIGNAL SCANNER V5.1 — Vietnam Market Optimized")
    print("=" * 70)
    print(f"🎯 API: {env_name} ({api_url})")
    print(f"⚙️ Settings: delay={args.delay}s, price_days={args.days}, T+{T_PLUS_DAYS}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    print("🎯 SELL RULES V5.1 (Vietnam Market):")
    print(f"  0. T+{T_PLUS_DAYS} Filter: Chỉ bán sau {T_PLUS_DAYS} ngày (trừ SL)")
    print("  1. SL: Price ≤ Stop Loss → SELL 100% (NGAY)")
    print("  2. TP1: Price ≥ TP → SELL 50%")
    print("  3. TP2: Price ≥ TP*1.1 (pos=50%) → SELL 30%")
    print("  4. TP Pullback: Price < TP*0.97 (pos=50%) → SELL 50%")
    print("  5. Trailing: Price < Peak*0.95 (pos=20%) → SELL 20%")
    print("  6. MA20 STRICT: (2 ngày < MA20) OR (< MA20 + thua >= 3%)")
    print()
    
    # Lấy BUY signals
    print("─" * 50)
    print("STEP 1: Lấy BUY signals...")
    print("─" * 50)
    
    buy_signals = get_buy_signals_from_api(api_url)
    
    if not buy_signals:
        print("⚠️ Không có BUY signals. Dừng.")
        return
    
    # Group by ticker
    tickers_map = {}
    for s in buy_signals:
        ticker = s['ticker']
        if ticker not in tickers_map:
            tickers_map[ticker] = []
        tickers_map[ticker].append(s)
    
    tickers = sorted(tickers_map.keys())
    print(f"\n✅ {len(tickers)} mã cần quét: {', '.join(tickers)}")
    
    # Quét từng ticker
    print("\n" + "─" * 50)
    print(f"STEP 2-4: Quét {len(tickers)} mã...")
    print("─" * 50)
    
    sell_signals = []
    skipped_t_plus = []
    
    for i, ticker in enumerate(tickers):
        signals_for_ticker = tickers_map[ticker]
        
        print(f"\n[{i+1}/{len(tickers)}] {ticker}")
        
        if i > 0:
            print(f"  ⏳ Đợi {args.delay}s...")
            time.sleep(args.delay)
        
        df = get_stock_data(ticker, days=args.days + 30)
        
        if df is None:
            print(f"  ⚠️ Không lấy được data → bỏ qua")
            continue
        
        raw_price = df['close'].iloc[-1]
        df['ma20'] = df['close'].rolling(20).mean()
        raw_ma20 = df['ma20'].iloc[-1]
        
        sample_entry = signals_for_ticker[0].get('entry_price', 0)
        if sample_entry > 1000 and raw_price < 1000:
            multiplier = 1000
        else:
            multiplier = 1
        
        current_price = raw_price * multiplier
        ma20 = raw_ma20 * multiplier
        
        print(f"  ✅ Price: {current_price:,.0f}, MA20: {ma20:,.0f}")
        print(f"  → Kiểm tra {len(signals_for_ticker)} BUY signal(s)")
        
        for j, signal in enumerate(signals_for_ticker):
            entry = signal.get('entry_price', 0)
            sl = signal.get('stop_loss', 0)
            tp = signal.get('take_profit', 0)
            pos = signal.get('position_pct', 100)
            code = signal.get('signal_code', f"{ticker}-?")
            date = signal.get('date', '?')
            
            can_sell, days_held = can_sell_t_plus_2(date)
            t_status = f"T+{days_held}" + (" ✅" if can_sell else " ⏳")
            
            print(f"    [{j+1}] {code} | Entry: {entry:,.0f} | SL: {sl:,.0f} | TP: {tp:,.0f} | Pos: {pos}% | {t_status}")
            
            result = check_sell_conditions_v51(signal, df)
            
            if result:
                reason = result['exit_reason']
                pnl = result['profit_loss_pct']
                qty = result['exit_quantity_pct']
                note = result.get('note', '')
                emoji = '🔴' if pnl < 0 else '🟢'
                print(f"    {emoji} SELL! {reason} | P/L: {pnl:+.2f}% | Bán: {qty}%")
                if note:
                    print(f"       {note}")
                sell_signals.append(result)
            else:
                if not can_sell:
                    print(f"    ⏳ Chưa đủ T+{T_PLUS_DAYS} → chờ")
                    skipped_t_plus.append(code)
                else:
                    print(f"    ✅ Chưa chạm điều kiện bán")
    
    # Kết quả
    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ SCAN V5.1")
    print("=" * 70)
    print(f"✅ Mã đã quét: {len(tickers)}")
    print(f"🔴 SELL signals: {len(sell_signals)}")
    print(f"⏳ Skipped (chưa T+{T_PLUS_DAYS}): {len(skipped_t_plus)}")
    
    if skipped_t_plus:
        print(f"\n⏳ Signals chưa đủ T+{T_PLUS_DAYS}: {', '.join(skipped_t_plus[:10])}")
        if len(skipped_t_plus) > 10:
            print(f"   ... và {len(skipped_t_plus) - 10} signals khác")
    
    if sell_signals:
        print("\n📋 Chi tiết SELL signals:")
        
        reasons = {}
        for s in sell_signals:
            r = s['exit_reason']
            reasons[r] = reasons.get(r, 0) + 1
        
        for reason, count in sorted(reasons.items()):
            print(f"  {reason}: {count}")
        
        for s in sell_signals:
            emoji = '🔴' if s['profit_loss_pct'] < 0 else '🟢'
            print(f"\n  {emoji} {s['ticker']} — {s['exit_reason']}")
            print(f"     Entry: {s['entry_price']:,.0f} → Exit: {s['exit_price']:,.0f} | " +
                  f"P/L: {s['profit_loss_pct']:+.2f}% | Bán: {s['exit_quantity_pct']}%")
            if s.get('note'):
                print(f"     {s['note']}")
        
        if not args.dry_run:
            print(f"\n" + "─" * 50)
            confirm = input(f"Đẩy {len(sell_signals)} SELL signals lên {env_name}? (y/n): ").strip().lower()
            
            if confirm == 'y':
                success = 0
                for s in sell_signals:
                    if push_sell_signal(s, api_url):
                        print(f"  ✅ {s['ticker']} pushed")
                        success += 1
                    else:
                        print(f"  ❌ {s['ticker']} failed")
                
                print(f"\n✅ Đã push {success}/{len(sell_signals)} lên {env_name}")
            else:
                print("⏹️ Đã hủy push.")
        else:
            print("\n⚠️ DRY RUN — không push lên server")
    else:
        print("\n✅ Không có SELL signal")
    
    if sell_signals:
        output_file = 'sell_signals_v5.1_latest.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': 'V5.1',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'sell_signals': sell_signals,
                'skipped_t_plus': skipped_t_plus,
                'count': len(sell_signals),
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📂 Saved: {output_file}")
    
    print()


if __name__ == '__main__':
    main()
