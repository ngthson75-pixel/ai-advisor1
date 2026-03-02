#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SELL SIGNAL SCANNER v3 - Đọc từ Production API
================================================

Khác biệt với v2:
  - v2: Đọc từ SQLite local → chỉ có signals hôm nay
  - v3: Đọc từ Production API → có TẤT CẢ signals đang hiện trên website

Cách chạy:
  cd C:\\ai-advisor1
  python sell_signal_scanner_v3.py
  python sell_signal_scanner_v3.py --days 30 --delay 2.0
  python sell_signal_scanner_v3.py --staging   (test staging trước)
"""

import os
import sys
import time
import argparse
import json
import sqlite3
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
LOCAL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signals.db')


# ========================================================================
# STEP 1: Lấy BUY signals từ Production API
# ========================================================================

def get_buy_signals_from_api(api_url):
    """Lấy danh sách BUY signals đang active từ production/staging API"""
    
    print(f"📡 Fetching BUY signals từ: {api_url}/signals")
    
    try:
        response = requests.get(f"{api_url}/signals", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API trả về status {response.status_code}")
            return []
        
        data = response.json()
        all_signals = data.get('signals', [])
        
        # Lọc chỉ BUY signals đang open
        buy_signals = [
            s for s in all_signals
            if s.get('action') == 'BUY' and s.get('status', 'open') == 'open'
        ]
        
        print(f"✅ Tìm thấy {len(buy_signals)} BUY signals đang mở (từ {len(all_signals)} tổng)")
        
        return buy_signals
        
    except requests.exceptions.ConnectionError:
        print("❌ Không kết nối được API (server đang ngủ?)")
        print("   Wake up: Invoke-WebRequest -Uri 'https://ai-advisor1-backend.onrender.com/health'")
        return []
    except Exception as e:
        print(f"❌ Lỗi: {e}")
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
# STEP 3: Kiểm tra điều kiện SELL
# ========================================================================

def check_sell_conditions(signal, df):
    """
    Kiểm tra 4 điều kiện SELL:
    1. Stop Loss: Giá hiện tại <= Stop Loss
    2. Take Profit: Giá hiện tại >= Take Profit  
    3. MA20 Consecutive: 2 ngày liên tiếp < MA20
    4. MA20 High Volume: Giá < MA20 + Volume > AvgVol20
    """
    
    if df is None or len(df) < 20:
        return None
    
    ticker = signal['ticker']
    entry_price = signal.get('entry_price', 0)
    stop_loss = signal.get('stop_loss', 0)
    take_profit = signal.get('take_profit', 0)
    position_pct = signal.get('position_pct', 100)
    
    # Đã bán hết → bỏ qua
    if position_pct <= 0:
        return None
    
    # Giá hiện tại từ VNStock (đơn vị: nghìn đồng, VD: 38 = 38.000 VND)
    raw_price = df['close'].iloc[-1]
    
    # Auto-detect đơn vị: nếu giá từ API > 1000 (full VND) mà giá VNStock < 1000 → nhân 1000
    # VD: entry_price=37600, raw_price=38 → cần nhân 1000
    # VD: entry_price=37.6, raw_price=38 → không cần nhân (cả hai đều theo nghìn)
    if entry_price > 1000 and raw_price < 1000:
        price_multiplier = 1000
    else:
        price_multiplier = 1
    
    current_price = raw_price * price_multiplier
    
    # MA20
    df['ma20'] = df['close'].rolling(20).mean()
    ma20 = df['ma20'].iloc[-1] * price_multiplier
    
    # Volume trung bình 20 ngày
    avg_vol_20 = df['volume'].rolling(20).mean().iloc[-1]
    current_vol = df['volume'].iloc[-1]
    
    # Giá ngày hôm trước
    prev_close = (df['close'].iloc[-2] if len(df) >= 2 else raw_price) * price_multiplier
    prev_ma20 = (df['ma20'].iloc[-2] if len(df) >= 2 else df['ma20'].iloc[-1]) * price_multiplier
    
    # ── CHECK 1: Stop Loss ──
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
            'exit_quantity_pct': 100,
            'signal_code': signal.get('signal_code', ''),
            'buy_signal_code': signal.get('signal_code', ''),
        }
    
    # ── CHECK 2: Take Profit (bán 50%) ──
    if take_profit > 0 and current_price >= take_profit and position_pct >= 100:
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        return {
            'ticker': ticker,
            'exit_reason': 'TAKE_PROFIT',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': 50,  # Chỉ bán 50%
            'signal_code': signal.get('signal_code', ''),
            'buy_signal_code': signal.get('signal_code', ''),
        }
    
    # ── CHECK 3: MA20 Consecutive (2 ngày < MA20) ──
    if (current_price < ma20 and prev_close < prev_ma20):
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        return {
            'ticker': ticker,
            'exit_reason': 'MA20_CONSECUTIVE',
            'entry_price': entry_price,
            'exit_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': round(pnl_pct, 2),
            'exit_quantity_pct': 100,
            'signal_code': signal.get('signal_code', ''),
            'buy_signal_code': signal.get('signal_code', ''),
            'ma20': round(ma20, 0),
        }
    
    # ── CHECK 4: MA20 High Volume ──
    if (current_price < ma20 and avg_vol_20 > 0 and current_vol > avg_vol_20 * 1.5):
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
            'exit_quantity_pct': 100,
            'signal_code': signal.get('signal_code', ''),
            'buy_signal_code': signal.get('signal_code', ''),
            'volume_ratio': volume_ratio,
        }
    
    return None


# ========================================================================
# STEP 4: Push SELL signals lên production
# ========================================================================

def push_sell_signal(sell_signal, api_url):
    """Đẩy 1 SELL signal lên production qua POST /api/signals"""
    
    payload = {
        'ticker': sell_signal['ticker'],
        'action': 'SELL',
        'strategy': sell_signal['exit_reason'],
        'entry_price': sell_signal['entry_price'],
        'stop_loss': sell_signal['stop_loss'],
        'take_profit': sell_signal['take_profit'],
        'strength': 80,
        'stock_type': 'Mid Cap',
        'rsi': 0,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'signal_code': f"SELL-{sell_signal['ticker']}-{datetime.now().strftime('%Y%m%d')}",
        'buy_signal_code': sell_signal.get('buy_signal_code', ''),
        'status': 'closed',
        'position_pct': 0 if sell_signal['exit_quantity_pct'] >= 100 else 50,
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
    parser = argparse.ArgumentParser(description='SELL Signal Scanner v3')
    parser.add_argument('--days', type=int, default=30, help='Days of price data to fetch')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between VCI requests')
    parser.add_argument('--staging', action='store_true', help='Use staging API')
    parser.add_argument('--dry-run', action='store_true', help='Scan only, do not push')
    args = parser.parse_args()
    
    api_url = STAGING_API if args.staging else PROD_API
    env_name = 'STAGING' if args.staging else 'PRODUCTION'
    
    print("\n" + "=" * 70)
    print("🔍 SELL SIGNAL SCANNER v3 — Đọc từ Production API")
    print("=" * 70)
    print(f"🎯 API: {env_name} ({api_url})")
    print(f"⚙️ Settings: delay={args.delay}s, price_days={args.days}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    print("🎯 SELL RULES:")
    print("  1. SL: Price ≤ Stop Loss → SELL 100%")
    print("  2. TP: Price ≥ Take Profit → SELL 50% (partial)")
    print("  3. MA20 Consecutive: 2 ngày < MA20 → SELL 100%")
    print("  4. MA20 High Volume: < MA20 + Volume spike → SELL 100%")
    print()
    
    # ── STEP 1: Lấy BUY signals từ API ──
    print("─" * 50)
    print("STEP 1: Lấy BUY signals từ Production API...")
    print("─" * 50)
    
    buy_signals = get_buy_signals_from_api(api_url)
    
    if not buy_signals:
        print("⚠️ Không có BUY signals nào. Dừng.")
        return
    
    # Lấy unique tickers
    tickers_map = {}  # ticker → list of signals
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
        
        # Lấy dữ liệu giá
        df = get_stock_data(ticker, days=args.days + 30)
        
        if df is None:
            print(f"  ⚠️ Không lấy được data → bỏ qua")
            continue
        
        raw_price = df['close'].iloc[-1]
        df['ma20'] = df['close'].rolling(20).mean()
        raw_ma20 = df['ma20'].iloc[-1]
        
        # Auto-detect đơn vị giá
        sample_entry = signals_for_ticker[0].get('entry_price', 0)
        if sample_entry > 1000 and raw_price < 1000:
            multiplier = 1000
        else:
            multiplier = 1
        
        current_price = raw_price * multiplier
        ma20 = raw_ma20 * multiplier
        
        print(f"  ✅ Price: {current_price:,.0f}, MA20: {ma20:,.0f}" + (f" (VNStock: {raw_price}×1000)" if multiplier > 1 else ""))
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
            
            result = check_sell_conditions(signal, df)
            
            if result:
                reason = result['exit_reason']
                pnl = result['profit_loss_pct']
                qty = result['exit_quantity_pct']
                emoji = '🔴' if pnl < 0 else '🟢'
                print(f"    {emoji} SELL! {reason} | P/L: {pnl:+.2f}% | Bán: {qty}%")
                sell_signals.append(result)
            else:
                print(f"    ✅ Chưa chạm điều kiện bán")
    
    # ── KẾT QUẢ ──
    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ SCAN")
    print("=" * 70)
    print(f"✅ Mã đã quét: {len(tickers)}")
    print(f"🔴 SELL signals: {len(sell_signals)}")
    
    if sell_signals:
        print("\n📋 Chi tiết SELL signals:")
        
        sl_count = sum(1 for s in sell_signals if s['exit_reason'] == 'STOP_LOSS')
        tp_count = sum(1 for s in sell_signals if s['exit_reason'] == 'TAKE_PROFIT')
        ma20c_count = sum(1 for s in sell_signals if s['exit_reason'] == 'MA20_CONSECUTIVE')
        ma20v_count = sum(1 for s in sell_signals if s['exit_reason'] == 'MA20_HIGH_VOLUME')
        
        print(f"  🔴 Stop Loss:       {sl_count}")
        print(f"  🟢 Take Profit:     {tp_count}")
        print(f"  📉 MA20 Consecutive: {ma20c_count}")
        print(f"  📊 MA20 High Volume: {ma20v_count}")
        
        for s in sell_signals:
            emoji = '🔴' if s['profit_loss_pct'] < 0 else '🟢'
            print(f"\n  {emoji} {s['ticker']} — {s['exit_reason']}")
            print(f"     Entry: {s['entry_price']:,.0f} → Exit: {s['exit_price']:,.0f} | P/L: {s['profit_loss_pct']:+.2f}% | Bán: {s['exit_quantity_pct']}%")
        
        # Push lên production
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
    
    # Lưu local (optional)
    if sell_signals:
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sell_signals_latest.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'sell_signals': sell_signals,
                'count': len(sell_signals),
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📂 Saved: {output_file}")
    
    print()


if __name__ == '__main__':
    main()
