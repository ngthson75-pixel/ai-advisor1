#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL SCANNER V5 - Optimized Exit Strategy
=================================================

CHANGES FROM V3:
  V3: TP bán 50%, MA20 cần 2 ngày
  V5: 5-step exit: 50% → 30% → 20% với bảo vệ đầy đủ

EXIT STRATEGY V5:
  1. TP (110k):           Bán 50% → Còn 50%
  2. TP+10% (121k):       Bán 30% → Còn 20%
  3. TP Pullback (106.7k): Bán 50% (nếu chưa bán @ step 2)
  4. Trailing Stop (5%):  Bán 20% (nếu chưa < MA20)
  5. < MA20:              Bán hết còn lại

Cách chạy:
  python sell_signal_scanner_v5.py
  python sell_signal_scanner_v5.py --days 30 --delay 2.0
  python sell_signal_scanner_v5.py --staging
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


# ========================================================================
# STEP 1: Lấy BUY signals từ Production API
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
            timeout = 60 if retry > 0 else 30  # Increase timeout on retry
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
            
            # Lọc BUY signals đang open hoặc partial (còn vị thế > 0)
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
                print("  ❌ Max retries reached. Backend may be sleeping.")
                print("  💡 Try: Invoke-WebRequest -Uri '{}/health'".format(base_url))
                return []
        except requests.exceptions.ConnectionError:
            print("  ❌ Không kết nối được API")
            if retry < max_retries - 1:
                print(f"  🔄 Retry {retry + 1}/{max_retries}...")
                time.sleep(10)
            else:
                return []
        except Exception as e:
            print(f"  ❌ Lỗi: {e}")
            if retry < max_retries - 1:
                print(f"  🔄 Retry {retry + 1}/{max_retries}...")
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
# STEP 3: Kiểm tra điều kiện SELL V5
# ========================================================================

def check_sell_conditions_v5(signal, df):
    """
    V5 EXIT STRATEGY - 5 bước:
    
    1. Stop Loss: Price <= SL → SELL 100%
    
    2. TAKE_PROFIT_1: Price >= TP → SELL 50%
       → Còn 50%
    
    3. TAKE_PROFIT_2: Price >= TP*1.1 → SELL 30% (60% của 50% còn lại)
       → Còn 20%
    
    4. TP_PULLBACK: Price < TP*0.97 AND position_pct == 50% → SELL 50%
       (Bảo vệ 50% giữa nếu chưa đạt TP+10%)
    
    5. TRAILING_STOP: Price < recent_high*0.95 AND position_pct == 20% → SELL 20%
       (Bảo vệ 20% cuối khi đã vượt TP)
    
    6. MA20_BREAK: Price < MA20 → SELL hết còn lại
       (Exit cuối cùng, đơn giản)
    """
    
    if df is None or len(df) < 20:
        return None
    
    ticker = signal['ticker']
    entry_price = signal.get('entry_price', 0)
    stop_loss = signal.get('stop_loss', 0)
    take_profit = signal.get('take_profit', 0)
    position_pct = signal.get('position_pct', 100)
    signal_code = signal.get('signal_code', '')
    
    # Đã bán hết → skip
    if position_pct <= 0:
        return None
    
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
    
    # Đỉnh gần nhất (20 ngày)
    recent_high = df['close'].tail(20).max() * price_multiplier
    
    # Volume
    avg_vol_20 = df['volume'].rolling(20).mean().iloc[-1]
    current_vol = df['volume'].iloc[-1]
    
    # ========================================================================
    # CHECK 1: STOP LOSS (Priority #1)
    # ========================================================================
    if stop_loss > 0 and current_price <= stop_loss:
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        return {
            'ticker': ticker,
            'exit_reason': 'STOP_LOSS',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': 100,  # Bán hết
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
        }
    
    # ========================================================================
    # CHECK 2: TAKE PROFIT 1 - Bán 50% đầu tiên
    # ========================================================================
    if take_profit > 0 and current_price >= take_profit and position_pct == 100:
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        return {
            'ticker': ticker,
            'exit_reason': 'TAKE_PROFIT_1',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': 50,  # Bán 50%
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'note': f'Bán 50% @ TP {take_profit:,.0f}'
        }
    
    # ========================================================================
    # CHECK 3: TAKE PROFIT 2 - Bán 30% (khi còn 50%)
    # ========================================================================
    # Trigger khi: position_pct == 50% (đã bán 50% @ TP1) và giá >= TP*1.1
    if position_pct == 50 and take_profit > 0:
        tp2_price = take_profit * 1.1
        if current_price >= tp2_price:
            pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            return {
                'ticker': ticker,
                'exit_reason': 'TAKE_PROFIT_2',
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'profit_loss_pct': round(pnl_pct, 2),
                'exit_quantity_pct': 30,  # Bán 30% (60% của 50% còn lại)
                'signal_code': signal_code,
                'buy_signal_code': signal_code,
                'note': f'Bán 30% @ TP+10% ({tp2_price:,.0f})'
            }
    
    # ========================================================================
    # CHECK 4: TP PULLBACK - Bảo vệ 50% giữa (nếu chưa bán @ TP2)
    # ========================================================================
    # Trigger khi: position_pct == 50% (chưa bán TP2) và giá pullback 3% từ TP
    if position_pct == 50 and take_profit > 0:
        pullback_threshold = take_profit * 0.97
        if current_price < pullback_threshold:
            pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            return {
                'ticker': ticker,
                'exit_reason': 'TP_PULLBACK',
                'entry_price': entry_price,
                'exit_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'profit_loss_pct': round(pnl_pct, 2),
                'exit_quantity_pct': 50,  # Bán hết 50% còn lại
                'signal_code': signal_code,
                'buy_signal_code': signal_code,
                'note': f'Pullback từ TP ({take_profit:,.0f}) → bán 50%'
            }
    
    # ========================================================================
    # CHECK 5: TRAILING STOP - Bảo vệ 20% cuối (khi đã vượt TP+10%)
    # ========================================================================
    # Trigger khi: position_pct == 20% (đã bán 50% + 30%) và giá giảm 5% từ đỉnh
    if position_pct == 20:
        # Chỉ kích hoạt trailing nếu đã vượt TP (có lãi)
        if take_profit > 0 and recent_high > take_profit:
            trailing_stop_price = recent_high * 0.95
            if current_price <= trailing_stop_price:
                pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                return {
                    'ticker': ticker,
                    'exit_reason': 'TRAILING_STOP',
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'profit_loss_pct': round(pnl_pct, 2),
                    'exit_quantity_pct': 20,  # Bán 20% còn lại
                    'signal_code': signal_code,
                    'buy_signal_code': signal_code,
                    'note': f'Trailing Stop: Đỉnh {recent_high:,.0f} → {trailing_stop_price:,.0f}'
                }
    
    # ========================================================================
    # CHECK 6: MA20 BREAK - Exit cuối cùng (bán hết còn lại)
    # ========================================================================
    # Đơn giản hóa: chỉ cần 1 ngày < MA20 là bán (không cần 2 ngày như V3)
    if current_price < ma20:
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        return {
            'ticker': ticker,
            'exit_reason': 'MA20_BREAK',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': position_pct,  # Bán hết còn lại (có thể 50%, 30% hoặc 20%)
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'ma20': round(ma20, 0),
            'note': f'Phá MA20 ({ma20:,.0f}) → bán {position_pct}% còn lại'
        }
    
    # ========================================================================
    # CHECK 7: MA20 HIGH VOLUME (Bonus - exit sớm khi volume spike)
    # ========================================================================
    if current_price < ma20 and avg_vol_20 > 0 and current_vol > avg_vol_20 * 1.5:
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        volume_ratio = round(current_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 0
        return {
            'ticker': ticker,
            'exit_reason': 'MA20_HIGH_VOLUME',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': position_pct,  # Bán hết
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'volume_ratio': volume_ratio,
            'note': f'< MA20 + Volume spike {volume_ratio}x'
        }
    
    return None


# ========================================================================
# STEP 4: Push SELL signals lên production
# ========================================================================

def push_sell_signal(sell_signal, api_url):
    """Đẩy 1 SELL signal lên production qua POST /api/signals"""
    
    # Tính position_pct mới của BUY signal
    exit_pct = sell_signal['exit_quantity_pct']
    
    if exit_pct >= 100:
        new_position_pct = 0
        new_status = 'closed'
    else:
        # Nếu bán một phần, backend sẽ tự tính
        new_position_pct = None  # Backend tự handle
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
        'exit_quantity_pct': exit_pct,  # Thêm field này để backend biết bán bao nhiêu %
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
    parser = argparse.ArgumentParser(description='SELL Signal Scanner V5')
    parser.add_argument('--days', type=int, default=30, help='Days of price data to fetch')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between VCI requests')
    parser.add_argument('--staging', action='store_true', help='Use staging API')
    parser.add_argument('--dry-run', action='store_true', help='Scan only, do not push')
    args = parser.parse_args()
    
    api_url = STAGING_API if args.staging else PROD_API
    env_name = 'STAGING' if args.staging else 'PRODUCTION'
    
    print("\n" + "=" * 70)
    print("🔍 SELL SIGNAL SCANNER V5 — Optimized 3-Step Exit Strategy")
    print("=" * 70)
    print(f"🎯 API: {env_name} ({api_url})")
    print(f"⚙️ Settings: delay={args.delay}s, price_days={args.days}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    print("🎯 SELL RULES V5:")
    print("  1. SL: Price ≤ Stop Loss → SELL 100%")
    print("  2. TP1: Price ≥ Take Profit → SELL 50%")
    print("  3. TP2: Price ≥ TP*1.1 (position=50%) → SELL 30%")
    print("  4. TP Pullback: Price < TP*0.97 (position=50%) → SELL 50%")
    print("  5. Trailing: Price < Peak*0.95 (position=20%) → SELL 20%")
    print("  6. MA20 Break: Price < MA20 → SELL remaining")
    print()
    
    # ── STEP 1: Lấy BUY signals từ API ──
    print("─" * 50)
    print("STEP 1: Lấy BUY signals từ Production API...")
    print("─" * 50)
    
    buy_signals = get_buy_signals_from_api(api_url)
    
    if not buy_signals:
        print("⚠️ Không có BUY signals nào. Dừng.")
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
    
    # ── STEP 2-4: Quét từng ticker ──
    print("\n" + "─" * 50)
    print(f"STEP 2-4: Quét {len(tickers)} mã...")
    print("─" * 50)
    
    sell_signals = []
    
    for i, ticker in enumerate(tickers):
        signals_for_ticker = tickers_map[ticker]
        
        print(f"\n[{i+1}/{len(tickers)}] {ticker}")
        
        if i > 0:
            print(f"  ⏳ Đợi {args.delay}s...")
            time.sleep(args.delay)
        
        # Lấy data
        df = get_stock_data(ticker, days=args.days + 30)
        
        if df is None:
            print(f"  ⚠️ Không lấy được data → bỏ qua")
            continue
        
        raw_price = df['close'].iloc[-1]
        df['ma20'] = df['close'].rolling(20).mean()
        raw_ma20 = df['ma20'].iloc[-1]
        
        # Auto-detect multiplier
        sample_entry = signals_for_ticker[0].get('entry_price', 0)
        if sample_entry > 1000 and raw_price < 1000:
            multiplier = 1000
        else:
            multiplier = 1
        
        current_price = raw_price * multiplier
        ma20 = raw_ma20 * multiplier
        
        print(f"  ✅ Price: {current_price:,.0f}, MA20: {ma20:,.0f}" + 
              (f" (VNStock: {raw_price}×1000)" if multiplier > 1 else ""))
        print(f"  → Kiểm tra {len(signals_for_ticker)} BUY signal(s)")
        
        # Check từng signal
        for j, signal in enumerate(signals_for_ticker):
            entry = signal.get('entry_price', 0)
            sl = signal.get('stop_loss', 0)
            tp = signal.get('take_profit', 0)
            pos = signal.get('position_pct', 100)
            code = signal.get('signal_code', f"{ticker}-?")
            date = signal.get('date', '?')
            
            print(f"    [{j+1}] {code} | Entry: {entry:,.0f} | SL: {sl:,.0f} | TP: {tp:,.0f} | Pos: {pos}% | Date: {date}")
            
            result = check_sell_conditions_v5(signal, df)
            
            if result:
                reason = result['exit_reason']
                pnl = result['profit_loss_pct']
                qty = result['exit_quantity_pct']
                note = result.get('note', '')
                emoji = '🔴' if pnl < 0 else '🟢'
                print(f"    {emoji} SELL! {reason} | P/L: {pnl:+.2f}% | Bán: {qty}%")
                if note:
                    print(f"       Note: {note}")
                sell_signals.append(result)
            else:
                print(f"    ✅ Chưa chạm điều kiện bán")
    
    # ── KẾT QUẢ ──
    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ SCAN V5")
    print("=" * 70)
    print(f"✅ Mã đã quét: {len(tickers)}")
    print(f"🔴 SELL signals: {len(sell_signals)}")
    
    if sell_signals:
        print("\n📋 Chi tiết SELL signals:")
        
        # Count by reason
        reasons = {}
        for s in sell_signals:
            r = s['exit_reason']
            reasons[r] = reasons.get(r, 0) + 1
        
        for reason, count in sorted(reasons.items()):
            print(f"  {reason}: {count}")
        
        # Detail list
        for s in sell_signals:
            emoji = '🔴' if s['profit_loss_pct'] < 0 else '🟢'
            print(f"\n  {emoji} {s['ticker']} — {s['exit_reason']}")
            print(f"     Entry: {s['entry_price']:,.0f} → Exit: {s['exit_price']:,.0f} | " +
                  f"P/L: {s['profit_loss_pct']:+.2f}% | Bán: {s['exit_quantity_pct']}%")
            if s.get('note'):
                print(f"     {s['note']}")
        
        # Push to production
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
                
                print(f"\n✅ Đã push {success}/{len(sell_signals)} SELL signals lên {env_name}")
            else:
                print("⏹️ Đã hủy push.")
        else:
            print("\n⚠️ DRY RUN — không push lên server")
    else:
        print("\n✅ Không có SELL signal — thị trường chưa chạm điều kiện bán")
    
    # Save results
    if sell_signals:
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sell_signals_v5_latest.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': 'V5',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'sell_signals': sell_signals,
                'count': len(sell_signals),
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📂 Saved: {output_file}")
    
    print()


if __name__ == '__main__':
    main()
