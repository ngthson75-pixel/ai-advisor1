#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIGNAL REVIEWER & EDITOR
=========================
Xem, lọc, xóa, sửa tín hiệu MUA/BÁN trước khi push lên production.

Cách chạy:
  cd C:\\ai-advisor1
  python signal_reviewer.py
"""

import sqlite3
import json
import os
import requests
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signals.db')
SELL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sell_signals_latest.json')
MARKET_RISK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'market_risk_latest.json')

# ── Backend URLs ──────────────────────────────────────────────────────────
BACKEND_PROD    = 'https://ai-advisor1-backend.onrender.com/api'
BACKEND_STAGING = 'https://ai-advisor1-staging.onrender.com/api'

# ── Admin secret — đọc từ .env nếu có, fallback về giá trị mặc định ──────
def _load_admin_secret():
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('ADMIN_SECRET='):
                    return line.split('=', 1)[1].strip().strip('"').strip("'")
    return os.getenv('ADMIN_SECRET', 'ai-advisor-admin-2026')

ADMIN_SECRET = _load_admin_secret()

# ── VN30 tickers (30 mã bluechip) ────────────────────────────────
VN30_TICKERS = {
    'ACB','BCM','BID','BVH','CTG','FPT','GAS','GVR','HDB','HPG',
    'MBB','MSN','MWG','PLX','POW','SAB','SHB','SSB','SSI','STB',
    'TCB','TPB','VCB','VHM','VIB','VIC','VJC','VNM','VPB','VRE',
}
VIP_MIN_SCORE = 65  # Score tối thiểu để hiển thị trên VIP dashboard


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ========================================================================
# VIEW FUNCTIONS
# ========================================================================

def view_buy_signals(date_filter=None):
    """Xem BUY signals"""
    conn = get_db_connection()
    
    if date_filter:
        rows = conn.execute(
            "SELECT * FROM signals WHERE action='BUY' AND date=? ORDER BY strength DESC",
            (date_filter,)
        ).fetchall()
        title = f"BUY SIGNALS — {date_filter}"
    else:
        rows = conn.execute(
            "SELECT * FROM signals WHERE action='BUY' ORDER BY date DESC, strength DESC"
        ).fetchall()
        title = "TẤT CẢ BUY SIGNALS"
    
    print(f"\n{'='*80}")
    print(f"📈 {title} ({len(rows)} tín hiệu)")
    print(f"{'='*80}")
    
    if not rows:
        print("  (Không có tín hiệu)")
        conn.close()
        return
    
    print(f"{'#':>3} {'ID':>5} {'Ticker':<8} {'Entry':>10} {'SL':>10} {'TP':>10} {'Score':>6} {'Type':<10} {'Strategy':<12} {'Date':<12}")
    print("-" * 100)
    
    for i, r in enumerate(rows, 1):
        ticker = r['ticker'] or ''
        entry = r['entry_price'] or 0
        sl = r['stop_loss'] or 0
        tp = r['take_profit'] or 0
        strength = r['strength'] or 0
        stock_type = r['stock_type'] or ''
        strategy = r['strategy'] or ''
        date = r['date'] or ''
        sig_id = r['id'] or 0
        
        # Color indicators
        score_mark = '⭐' if strength >= 90 else ('✅' if strength >= 80 else ('⚠️' if strength >= 70 else '❌'))
        
        print(f"{i:>3} {sig_id:>5} {ticker:<8} {entry:>10,.0f} {sl:>10,.0f} {tp:>10,.0f} {score_mark}{strength:>4}% {stock_type:<10} {strategy:<12} {date:<12}")
    
    conn.close()
    return rows


def view_sell_signals():
    """Xem SELL signals từ file sell_signals_latest.json"""
    print(f"\n{'='*80}")
    print(f"📉 SELL SIGNALS")
    print(f"{'='*80}")
    
    if not os.path.exists(SELL_FILE):
        print("  (Chưa chạy SELL scanner hoặc không có file sell_signals_latest.json)")
        
        # Thử xem từ DB
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT * FROM signals WHERE action='SELL' ORDER BY date DESC"
        ).fetchall()
        
        if rows:
            print(f"\n  Tìm thấy {len(rows)} SELL signals trong database:")
            for r in rows:
                print(f"  🔴 {r['ticker']} — {r['strategy']} | Date: {r['date']}")
        conn.close()
        return
    
    with open(SELL_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sells = data.get('sell_signals', [])
    print(f"📅 Date: {data.get('date', '?')}")
    print(f"🔴 Total: {len(sells)}")
    
    if not sells:
        print("  ✅ Không có SELL signal — thị trường chưa chạm điều kiện bán")
        return
    
    print(f"\n{'#':>3} {'Ticker':<8} {'Reason':<18} {'Entry':>10} {'Exit':>10} {'P/L':>8} {'Bán':>5}")
    print("-" * 70)
    
    for i, s in enumerate(sells, 1):
        emoji = '🔴' if s.get('profit_loss_pct', 0) < 0 else '🟢'
        print(f"{i:>3} {s['ticker']:<8} {s['exit_reason']:<18} {s['entry_price']:>10,.0f} {s['exit_price']:>10,.0f} {emoji}{s['profit_loss_pct']:>+7.2f}% {s['exit_quantity_pct']:>4}%")
    
    return sells


def view_market_risk():
    """Xem Market Risk analysis"""
    print(f"\n{'='*80}")
    print(f"🛡️ MARKET RISK")
    print(f"{'='*80}")
    
    if not os.path.exists(MARKET_RISK_FILE):
        print("  (Chưa chạy market_risk_analysis.py)")
        return
    
    with open(MARKET_RISK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    emoji = data.get('mode_emoji', '🟡')
    mode = data.get('mode_label', '?')
    score = data.get('risk_score', 0)
    alloc = data.get('allocation', 50)
    desc = data.get('description', '')
    
    print(f"  {emoji} Mode: {mode}")
    print(f"  📊 Risk Score: {score}/100")
    print(f"  💰 Tỷ trọng: {alloc}% CP / {100-alloc}% tiền mặt")
    print(f"  📝 {desc}")
    
    factors = data.get('factors', [])
    if factors:
        print(f"\n  📋 Chi tiết yếu tố:")
        for f in factors:
            if not f.get('isRef', False):
                print(f"     {f.get('icon','')} {f.get('label','')}: {f.get('value','')}")


def view_all_summary():
    """Tổng quan tất cả"""
    view_market_risk()
    
    conn = get_db_connection()
    
    # BUY today
    today = datetime.now().strftime('%Y-%m-%d')
    buy_today = conn.execute(
        "SELECT COUNT(*) as cnt FROM signals WHERE action='BUY' AND date=?", (today,)
    ).fetchone()['cnt']
    
    # All BUY
    buy_all = conn.execute(
        "SELECT COUNT(*) as cnt FROM signals WHERE action='BUY'"
    ).fetchone()['cnt']
    
    # Dates
    dates = conn.execute(
        "SELECT DISTINCT date FROM signals WHERE action='BUY' ORDER BY date DESC LIMIT 5"
    ).fetchall()
    
    print(f"\n{'='*80}")
    print(f"📊 TỔNG QUAN")
    print(f"{'='*80}")
    print(f"  📈 BUY signals hôm nay ({today}): {buy_today}")
    print(f"  📈 BUY signals tổng cộng: {buy_all}")
    print(f"  📅 Ngày có tín hiệu: {', '.join(r['date'] for r in dates)}")
    
    # SELL
    if os.path.exists(SELL_FILE):
        with open(SELL_FILE, 'r', encoding='utf-8') as f:
            sell_data = json.load(f)
        print(f"  📉 SELL signals: {sell_data.get('count', 0)}")
    
    conn.close()


# ========================================================================
# EDIT FUNCTIONS
# ========================================================================

def delete_signal_by_id(signal_id):
    """Xóa signal theo ID"""
    conn = get_db_connection()
    
    # Check exists
    row = conn.execute("SELECT * FROM signals WHERE id=?", (signal_id,)).fetchone()
    if not row:
        print(f"❌ Không tìm thấy signal ID {signal_id}")
        conn.close()
        return
    
    print(f"\n⚠️ Xóa signal:")
    print(f"  ID: {row['id']} | {row['ticker']} | {row['action']} | {row['strategy']} | {row['date']}")
    confirm = input("  Xác nhận xóa? (y/n): ").strip().lower()
    
    if confirm == 'y':
        conn.execute("DELETE FROM signals WHERE id=?", (signal_id,))
        conn.commit()
        print(f"  ✅ Đã xóa signal ID {signal_id}")
    else:
        print("  ⏹️ Hủy")
    
    conn.close()


def delete_signals_by_ticker(ticker):
    """Xóa tất cả signals của 1 ticker"""
    conn = get_db_connection()
    ticker = ticker.upper()
    
    rows = conn.execute(
        "SELECT * FROM signals WHERE ticker=? ORDER BY date DESC", (ticker,)
    ).fetchall()
    
    if not rows:
        print(f"❌ Không tìm thấy signals cho {ticker}")
        conn.close()
        return
    
    print(f"\n⚠️ Xóa {len(rows)} signals của {ticker}:")
    for r in rows:
        print(f"  {r['id']} | {r['action']} | {r['strategy']} | {r['strength']}% | {r['date']}")
    
    confirm = input(f"  Xác nhận xóa TẤT CẢ {len(rows)} signals của {ticker}? (y/n): ").strip().lower()
    
    if confirm == 'y':
        conn.execute("DELETE FROM signals WHERE ticker=?", (ticker,))
        conn.commit()
        print(f"  ✅ Đã xóa {len(rows)} signals của {ticker}")
    else:
        print("  ⏹️ Hủy")
    
    conn.close()


def delete_low_score(min_score=70):
    """Xóa signals có score < threshold"""
    conn = get_db_connection()
    
    rows = conn.execute(
        "SELECT * FROM signals WHERE action='BUY' AND (strength < ? OR strength IS NULL) ORDER BY strength ASC",
        (min_score,)
    ).fetchall()
    
    if not rows:
        print(f"✅ Không có signal nào score < {min_score}%")
        conn.close()
        return
    
    print(f"\n⚠️ Tìm thấy {len(rows)} signals có score < {min_score}%:")
    for r in rows:
        print(f"  {r['ticker']} | {r['strategy']} | {r['strength']}% | {r['date']}")
    
    confirm = input(f"  Xóa tất cả? (y/n): ").strip().lower()
    
    if confirm == 'y':
        conn.execute(
            "DELETE FROM signals WHERE action='BUY' AND (strength < ? OR strength IS NULL)",
            (min_score,)
        )
        conn.commit()
        print(f"  ✅ Đã xóa {len(rows)} signals score < {min_score}%")
    
    conn.close()


def delete_old_signals(days=30):
    """Xóa signals cũ hơn N ngày"""
    conn = get_db_connection()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    rows = conn.execute(
        "SELECT COUNT(*) as cnt FROM signals WHERE date < ?", (cutoff,)
    ).fetchone()
    
    count = rows['cnt']
    if count == 0:
        print(f"✅ Không có signal nào cũ hơn {days} ngày")
        conn.close()
        return
    
    print(f"\n⚠️ Tìm thấy {count} signals cũ hơn {days} ngày (trước {cutoff})")
    confirm = input(f"  Xóa tất cả? (y/n): ").strip().lower()
    
    if confirm == 'y':
        conn.execute("DELETE FROM signals WHERE date < ?", (cutoff,))
        conn.commit()
        print(f"  ✅ Đã xóa {count} signals cũ")
    
    conn.close()


def add_signal_manual():
    """Thêm signal thủ công"""
    print(f"\n{'='*60}")
    print("➕ THÊM TÍN HIỆU MỚI")
    print(f"{'='*60}")
    
    try:
        ticker = input("  Mã CP (VD: VCB): ").strip().upper()
        if not ticker:
            print("  ❌ Hủy")
            return
        
        entry = float(input("  Giá vào (VD: 85000): ").strip())
        sl = float(input("  Stop Loss (VD: 80000): ").strip())
        tp = float(input("  Take Profit (VD: 93000): ").strip())
        
        strength = input("  Score % (mặc định 80): ").strip()
        strength = int(strength) if strength else 80
        
        stock_type = input("  Loại (Blue Chip / Mid Cap, mặc định Mid Cap): ").strip()
        stock_type = stock_type if stock_type else 'Mid Cap'
        
        strategy = input("  Strategy (PULLBACK / EMA_CROSS, mặc định PULLBACK): ").strip()
        strategy = strategy if strategy else 'PULLBACK'
        
        date = input(f"  Ngày (mặc định {datetime.now().strftime('%Y-%m-%d')}): ").strip()
        date = date if date else datetime.now().strftime('%Y-%m-%d')
        
        rr = round((tp - entry) / (entry - sl), 2) if entry > sl else 0
        
        print(f"\n  📋 Xác nhận:")
        print(f"     {ticker} | Entry: {entry:,.0f} | SL: {sl:,.0f} | TP: {tp:,.0f}")
        print(f"     Score: {strength}% | R/R: {rr}x | {stock_type} | {strategy} | {date}")
        
        confirm = input("  Thêm? (y/n): ").strip().lower()
        if confirm != 'y':
            print("  ⏹️ Hủy")
            return
        
        conn = get_db_connection()
        conn.execute(
            """INSERT INTO signals (ticker, action, entry_price, stop_loss, take_profit, 
               risk_reward, strength, stock_type, strategy, date, rsi, is_priority)
               VALUES (?, 'BUY', ?, ?, ?, ?, ?, ?, ?, ?, 50, 1)""",
            (ticker, entry, sl, tp, rr, strength, stock_type, strategy, date)
        )
        conn.commit()
        conn.close()
        
        print(f"  ✅ Đã thêm {ticker} vào database!")
        
    except ValueError:
        print("  ❌ Giá trị không hợp lệ. Nhập số, VD: 85000")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")


# ========================================================================
# SELL SIGNAL EDITING
# ========================================================================

def edit_sell_signals():
    """Sửa SELL signals từ file sell_signals_latest.json"""
    print(f"\n{'='*60}")
    print("📉 SỬA SELL SIGNALS")
    print(f"{'='*60}")
    
    if not os.path.exists(SELL_FILE):
        print("  (Chưa có file sell_signals_latest.json — chạy sell scanner trước)")
        return
    
    with open(SELL_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sells = data.get('sell_signals', [])
    
    if not sells:
        print("  ✅ Không có SELL signal nào")
        return
    
    # Hiển thị
    print(f"  📅 Date: {data.get('date', '?')}")
    print(f"  🔴 Total: {len(sells)}\n")
    print(f"  {'#':>3} {'Ticker':<8} {'Reason':<18} {'Entry':>10} {'Exit':>10} {'P/L':>8} {'Bán':>5}")
    print("  " + "-" * 65)
    
    for i, s in enumerate(sells):
        emoji = '🔴' if s.get('profit_loss_pct', 0) < 0 else '🟢'
        print(f"  {i+1:>3} {s['ticker']:<8} {s['exit_reason']:<18} {s['entry_price']:>10,.0f} {s['exit_price']:>10,.0f} {emoji}{s['profit_loss_pct']:>+7.2f}% {s['exit_quantity_pct']:>4}%")
    
    while True:
        print(f"\n  Tùy chọn:")
        print(f"  a. Xóa 1 SELL signal (nhập số thứ tự)")
        print(f"  b. Xóa tất cả SELL signals")
        print(f"  c. Sửa exit_reason của 1 signal")
        print(f"  d. Quay lại")
        
        sub = input("\n  Chọn (a/b/c/d): ").strip().lower()
        
        if sub == 'd':
            break
        elif sub == 'a':
            try:
                idx = int(input("  Nhập số thứ tự cần xóa: ").strip()) - 1
                if 0 <= idx < len(sells):
                    removed = sells.pop(idx)
                    data['sell_signals'] = sells
                    data['count'] = len(sells)
                    with open(SELL_FILE, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"  ✅ Đã xóa {removed['ticker']} ({removed['exit_reason']})")
                else:
                    print(f"  ❌ Số thứ tự không hợp lệ (1-{len(sells)})")
            except ValueError:
                print("  ❌ Nhập số, VD: 1")
        elif sub == 'b':
            confirm = input(f"  ⚠️ Xóa TẤT CẢ {len(sells)} SELL signals? (y/n): ").strip().lower()
            if confirm == 'y':
                data['sell_signals'] = []
                data['count'] = 0
                with open(SELL_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  ✅ Đã xóa tất cả SELL signals")
                break
        elif sub == 'c':
            try:
                idx = int(input("  Nhập số thứ tự cần sửa: ").strip()) - 1
                if 0 <= idx < len(sells):
                    s = sells[idx]
                    print(f"  Hiện tại: {s['ticker']} — {s['exit_reason']}")
                    print(f"  Lựa chọn: STOP_LOSS / TAKE_PROFIT / MA20_CONSECUTIVE / MA20_HIGH_VOLUME")
                    new_reason = input("  Reason mới: ").strip().upper()
                    if new_reason in ['STOP_LOSS', 'TAKE_PROFIT', 'MA20_CONSECUTIVE', 'MA20_HIGH_VOLUME']:
                        sells[idx]['exit_reason'] = new_reason
                        # Nếu đổi sang TAKE_PROFIT → bán 50%
                        if new_reason == 'TAKE_PROFIT':
                            sells[idx]['exit_quantity_pct'] = 50
                        else:
                            sells[idx]['exit_quantity_pct'] = 100
                        data['sell_signals'] = sells
                        with open(SELL_FILE, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"  ✅ Đã đổi {s['ticker']} → {new_reason}")
                    else:
                        print("  ❌ Reason không hợp lệ")
                else:
                    print(f"  ❌ Số thứ tự không hợp lệ")
            except ValueError:
                print("  ❌ Nhập số, VD: 1")


def push_sell_signals_to_production():
    """Push SELL signals từ file lên production"""
    if not os.path.exists(SELL_FILE):
        print("  ❌ Chưa có file sell_signals_latest.json")
        return
    
    with open(SELL_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sells = data.get('sell_signals', [])
    if not sells:
        print("  ✅ Không có SELL signal nào để push")
        return
    
    print(f"\n  📉 {len(sells)} SELL signals sẽ được push:")
    for s in sells:
        emoji = '🔴' if s.get('profit_loss_pct', 0) < 0 else '🟢'
        print(f"     {emoji} {s['ticker']} — {s['exit_reason']} | P/L: {s['profit_loss_pct']:+.2f}%")
    
    print(f"\n  1. Production")
    print(f"  2. Staging")
    env = input("  Chọn (1/2): ").strip()
    api_url = 'https://ai-advisor1-backend.onrender.com/api' if env == '1' else 'https://ai-advisor1-staging.onrender.com/api'
    env_name = 'Production' if env == '1' else 'Staging'
    
    confirm = input(f"  Push {len(sells)} SELL signals lên {env_name}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ⏹️ Hủy")
        return
    
    success = 0
    for s in sells:
        payload = {
            'ticker': s['ticker'],
            'action': 'SELL',
            'strategy': s['exit_reason'],
            'entry_price': s['entry_price'],
            'stop_loss': s.get('stop_loss', 0),
            'take_profit': s.get('take_profit', 0),
            'strength': 80,
            'stock_type': 'Mid Cap',
            'rsi': 0,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'signal_code': f"SELL-{s['ticker']}-{datetime.now().strftime('%Y%m%d')}",
            'buy_signal_code': s.get('buy_signal_code', ''),
            'status': 'closed',
            'position_pct': 0 if s.get('exit_quantity_pct', 100) >= 100 else 50,
        }
        try:
            resp = requests.post(f"{api_url}/signals", json=payload, timeout=15)
            if resp.status_code in [200, 201]:
                print(f"     ✅ {s['ticker']}")
                success += 1
            else:
                print(f"     ❌ {s['ticker']} — Status {resp.status_code}")
        except Exception as e:
            print(f"     ❌ {s['ticker']} — {e}")
    
    print(f"\n  ✅ Push xong: {success}/{len(sells)} SELL signals lên {env_name}")


# ========================================================================
# MARKET RISK EDITING
# ========================================================================

def edit_market_risk():
    """Sửa Market Risk trước khi push"""
    print(f"\n{'='*60}")
    print("🛡️ SỬA MARKET RISK")
    print(f"{'='*60}")
    
    if not os.path.exists(MARKET_RISK_FILE):
        print("  ❌ Chưa có file market_risk_latest.json — chạy market_risk_analysis.py trước")
        return
    
    with open(MARKET_RISK_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Hiển thị hiện tại
    print(f"\n  📋 HIỆN TẠI:")
    print(f"  {data.get('mode_emoji', '🟡')} Mode: {data.get('mode_label', '?')}")
    print(f"  📊 Risk Score: {data.get('risk_score', 0)}/100")
    print(f"  💰 Tỷ trọng: {data.get('allocation', 50)}% CP / {100 - data.get('allocation', 50)}% tiền mặt")
    print(f"  📝 Mô tả: {data.get('description', '')}")
    
    factors = data.get('factors', [])
    if factors:
        print(f"\n  📋 Yếu tố:")
        for i, f_item in enumerate(factors):
            if not f_item.get('isRef', False):
                print(f"     {i+1}. {f_item.get('icon','')} {f_item.get('label','')}: {f_item.get('value','')}")
    
    while True:
        print(f"\n  Tùy chọn:")
        print(f"  a. Đổi Market Mode (TÍCH CỰC / THẬN TRỌNG / PHÒNG THỦ)")
        print(f"  b. Sửa Risk Score (0-100)")
        print(f"  c. Sửa tỷ trọng CP (%)")
        print(f"  d. Sửa mô tả")
        print(f"  e. Xem lại")
        print(f"  f. Lưu & Quay lại")
        
        sub = input("\n  Chọn (a-f): ").strip().lower()
        
        if sub == 'f':
            with open(MARKET_RISK_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  ✅ Đã lưu market_risk_latest.json")
            break
        elif sub == 'a':
            print(f"  Chọn mode:")
            print(f"    1. 🟢 TÍCH CỰC (Bull) — Score 0-35, CP 70-80%")
            print(f"    2. 🟡 THẬN TRỌNG (Sideways) — Score 36-60, CP 40-60%")
            print(f"    3. 🔴 PHÒNG THỦ (Bear) — Score 61-100, CP 0-30%")
            mode_choice = input("  Chọn (1/2/3): ").strip()
            
            if mode_choice == '1':
                data['mode'] = 'bull'
                data['mode_label'] = 'TÍCH CỰC'
                data['mode_emoji'] = '🟢'
                data['risk_score'] = data.get('risk_score', 30)
                if data['risk_score'] > 35:
                    data['risk_score'] = 30
                data['allocation'] = 80
                data['description'] = 'Thị trường uptrend — Ưu tiên tìm điểm mua'
            elif mode_choice == '2':
                data['mode'] = 'sideways'
                data['mode_label'] = 'THẬN TRỌNG'
                data['mode_emoji'] = '🟡'
                data['risk_score'] = data.get('risk_score', 50)
                if data['risk_score'] < 36 or data['risk_score'] > 60:
                    data['risk_score'] = 50
                data['allocation'] = 50
                data['description'] = 'Thị trường sideway — Chỉ mua khi tín hiệu rõ ràng'
            elif mode_choice == '3':
                data['mode'] = 'bear'
                data['mode_label'] = 'PHÒNG THỦ'
                data['mode_emoji'] = '🔴'
                data['risk_score'] = data.get('risk_score', 75)
                if data['risk_score'] < 61:
                    data['risk_score'] = 75
                data['allocation'] = 20
                data['description'] = 'Thị trường downtrend — Ưu tiên bảo toàn vốn'
            else:
                print("  ❌ Không hợp lệ")
                continue
            print(f"  ✅ Đã đổi → {data['mode_emoji']} {data['mode_label']}")
            
        elif sub == 'b':
            try:
                score = int(input("  Risk Score mới (0-100): ").strip())
                if 0 <= score <= 100:
                    data['risk_score'] = score
                    print(f"  ✅ Score → {score}")
                else:
                    print("  ❌ Phải từ 0-100")
            except ValueError:
                print("  ❌ Nhập số")
        elif sub == 'c':
            try:
                alloc = int(input("  Tỷ trọng CP mới (0-100%): ").strip())
                if 0 <= alloc <= 100:
                    data['allocation'] = alloc
                    print(f"  ✅ Tỷ trọng → {alloc}% CP / {100-alloc}% tiền mặt")
                else:
                    print("  ❌ Phải từ 0-100")
            except ValueError:
                print("  ❌ Nhập số")
        elif sub == 'd':
            desc = input("  Mô tả mới: ").strip()
            if desc:
                data['description'] = desc
                print(f"  ✅ Mô tả → {desc}")
        elif sub == 'e':
            print(f"\n  {data.get('mode_emoji', '🟡')} {data.get('mode_label', '?')} | Score: {data.get('risk_score', 0)} | CP: {data.get('allocation', 50)}%")
            print(f"  📝 {data.get('description', '')}")


# ========================================================================
# VIP TELEGRAM NOTIFICATION
# ========================================================================

def push_vip_telegram():
    """
    Gửi Telegram tổng hợp tín hiệu đến toàn bộ VIP users.
    Gọi sau khi đã push BUY signals (option 14) hoặc Market Risk (option 13).
    """
    print(f"\n{'='*60}")
    print("💎 GỬI TELEGRAM VIP")
    print(f"{'='*60}")

    # ── Chọn môi trường ───────────────────────────────────────
    print("\n  Môi trường:")
    print("  1. Production")
    print("  2. Staging (test)")
    env = input("  Chọn (1/2): ").strip()
    if env not in ('1', '2'):
        print("  ❌ Hủy")
        return
    api_url  = BACKEND_PROD if env == '1' else BACKEND_STAGING
    env_name = 'Production' if env == '1' else 'Staging'

    # ── Chọn loại thông báo ───────────────────────────────────
    print(f"\n  Loại thông báo ({env_name}):")
    print("  a. 📈 Tín hiệu MUA hôm nay (từ signals.db)")
    print("  b. 🛡️  Cập nhật Market Risk (từ market_risk_latest.json)")
    print("  c. ✏️  Tin nhắn tùy chỉnh")
    kind = input("  Chọn (a/b/c): ").strip().lower()

    title = ''
    body  = ''

    # ── Loại A: BUY signals hôm nay ──────────────────────────
    if kind == 'a':
        today = datetime.now().strftime('%Y-%m-%d')
        conn  = get_db_connection()
        rows  = conn.execute(
            "SELECT ticker, entry_price, stop_loss, take_profit, strength "
            "FROM signals WHERE action='BUY' AND date=? ORDER BY strength DESC",
            (today,)
        ).fetchall()
        conn.close()

        if not rows:
            print(f"  ⚠️  Không có BUY signal nào hôm nay ({today})")
            alt = input("  Lấy signals ngày khác? Nhập ngày (YYYY-MM-DD) hoặc Enter để hủy: ").strip()
            if not alt:
                return
            conn  = get_db_connection()
            rows  = conn.execute(
                "SELECT ticker, entry_price, stop_loss, take_profit, strength "
                "FROM signals WHERE action='BUY' AND date=? ORDER BY strength DESC",
                (alt,)
            ).fetchall()
            conn.close()
            today = alt
            if not rows:
                print(f"  ❌ Không có signal nào ngày {alt}")
                return

        date_fmt = datetime.strptime(today, '%Y-%m-%d').strftime('%d/%m/%Y')
        title = f"[AI ADVISOR] Tín hiệu MUA {date_fmt}"

        lines = [f"📈 <b>Tín hiệu MUA — {date_fmt}</b>\n"]
        for r in rows:
            entry = int(r['entry_price']) if r['entry_price'] else 0
            sl    = int(r['stop_loss'])   if r['stop_loss']   else 0
            tp    = int(r['take_profit']) if r['take_profit'] else 0
            score = r['strength'] or 0
            rr    = round((tp - entry) / (entry - sl), 1) if entry > sl > 0 and tp > entry else 0
            lines.append(
                f"🔹 <b>{r['ticker']}</b>  Score: {score:.0f}%\n"
                f"   Vào: {entry:,}  |  SL: {sl:,}  |  TP: {tp:,}\n"
                f"   R/R: {rr}x"
            )

        lines.append("\n⚠️ <i>Đây là tín hiệu hỗ trợ quyết định, không phải khuyến nghị đầu tư.</i>")
        body = "\n".join(lines)

        print(f"\n  📋 Preview ({len(rows)} tín hiệu):")
        for r in rows:
            print(f"     🔹 {r['ticker']} — Entry: {int(r['entry_price'] or 0):,} | Score: {r['strength'] or 0:.0f}%")

    # ── Loại B: Market Risk ───────────────────────────────────
    elif kind == 'b':
        if not os.path.exists(MARKET_RISK_FILE):
            print("  ❌ Chưa có market_risk_latest.json — chạy market_risk_analysis.py trước")
            return

        with open(MARKET_RISK_FILE, 'r', encoding='utf-8') as f:
            mr = json.load(f)

        mode_emoji = mr.get('mode_emoji', '🟡')
        mode_label = mr.get('mode_label', 'THẬN TRỌNG')
        risk_score = mr.get('risk_score', 0)
        allocation = mr.get('allocation', 50)
        description = mr.get('description', '')
        date_str = mr.get('date', datetime.now().strftime('%Y-%m-%d'))
        try:
            date_fmt = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            date_fmt = date_str

        title = f"[AI ADVISOR] Cập nhật thị trường {date_fmt}"
        body  = (
            f"🛡️ <b>Cập nhật Market Risk — {date_fmt}</b>\n\n"
            f"{mode_emoji} Chế độ thị trường: <b>{mode_label}</b>\n"
            f"📊 Điểm rủi ro: <b>{risk_score}/100</b>\n"
            f"💼 Khuyến nghị tỷ trọng CP: <b>{allocation}%</b> (tiền mặt: {100-allocation}%)\n"
            f"📝 {description}\n\n"
            f"⚠️ <i>Đây là công cụ hỗ trợ quyết định, không phải khuyến nghị đầu tư.</i>"
        )

        print(f"\n  📋 Preview:")
        print(f"  {mode_emoji} {mode_label} | Score: {risk_score}/100 | CP: {allocation}%")
        print(f"  {description}")

    # ── Loại C: Tùy chỉnh ────────────────────────────────────
    elif kind == 'c':
        title = input("  Tiêu đề (VD: Thông báo thị trường hôm nay): ").strip()
        if not title:
            print("  ❌ Hủy — tiêu đề không được trống")
            return
        print("  Nội dung (nhập xong gõ Enter 2 lần):")
        lines_input = []
        while True:
            line = input()
            if line == '' and lines_input and lines_input[-1] == '':
                break
            lines_input.append(line)
        body = "\n".join(lines_input).strip()
        if not body:
            print("  ❌ Hủy — nội dung không được trống")
            return
    else:
        print("  ❌ Lựa chọn không hợp lệ")
        return

    # ── Xác nhận và gửi ──────────────────────────────────────
    print(f"\n  {'─'*50}")
    print(f"  Tiêu đề : {title}")
    print(f"  Nội dung: {body[:120]}{'...' if len(body) > 120 else ''}")
    print(f"  Gửi đến : Tất cả VIP users trên {env_name}")
    print(f"  {'─'*50}")

    confirm = input("\n  Gửi Telegram VIP? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ⏹️ Hủy")
        return

    # ── Gọi API broadcast ─────────────────────────────────────
    try:
        resp = requests.post(
            f"{api_url}/admin/telegram/broadcast",
            headers={'X-Admin-Key': ADMIN_SECRET},
            data={'title': title, 'body': body},
            timeout=30,
        )
        if resp.status_code == 200:
            result = resp.json()
            sent    = result.get('sent', 0)
            failed  = result.get('failed', 0)
            skipped = result.get('skipped', 0)
            print(f"\n  ✅ Gửi thành công!")
            print(f"     Đã gửi : {sent} users")
            if failed:
                print(f"     Thất bại: {failed} users")
            if skipped:
                print(f"     Bỏ qua  : {skipped} users (chưa có chat_id)")
        else:
            print(f"\n  ❌ Lỗi HTTP {resp.status_code}: {resp.text[:200]}")
    except requests.exceptions.ConnectionError:
        print(f"\n  ❌ Không kết nối được {env_name} backend — kiểm tra Render đang chạy không")
    except requests.exceptions.Timeout:
        print(f"\n  ❌ Timeout — backend mất quá 30 giây")
    except Exception as e:
        print(f"\n  ❌ Lỗi: {e}")



# ========================================================================
# VIP SIGNAL FUNCTIONS
# ========================================================================

def view_vip_signals():
    """
    Option 18: Preview tín hiệu VIP — hiển thị tín hiệu BUY từ local DB
    đủ tiêu chuẩn VIP (VN30 + score >= VIP_MIN_SCORE)
    """
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM signals WHERE action='BUY' ORDER BY strength DESC, date DESC"
    ).fetchall()
    conn.close()

    vn30_rows  = [r for r in rows if r['ticker'] in VN30_TICKERS and (r['strength'] or 0) >= VIP_MIN_SCORE]
    other_rows = [r for r in rows if r['ticker'] not in VN30_TICKERS and (r['strength'] or 0) >= VIP_MIN_SCORE]

    print(f"\n{'='*65}")
    print("💎 VIP SIGNALS PREVIEW (từ local signals.db)")
    print(f"   Tiêu chuẩn: VN30 hoặc Score >= {VIP_MIN_SCORE}%")
    print(f"{'='*65}")

    print(f"\n{'─'*65}")
    print(f"  💎 VN30 BLUECHIP ({len(vn30_rows)} signals):")
    print(f"  {'Mã':<8} {'Score':>6} {'Entry':>10} {'SL':>10} {'TP':>10}  {'Ngày':<12}")
    print(f"{'─'*65}")
    for r in vn30_rows:
        print(f"  {r['ticker']:<8} {(r['strength'] or 0):>5.0f}% {(r['entry_price'] or 0):>10,.0f} "
              f"{(r['stop_loss'] or 0):>10,.0f} {(r['take_profit'] or 0):>10,.0f}  {r['date'] or '—':<12}")

    if other_rows:
        print(f"\n{'─'*65}")
        print(f"  📊 Non-VN30 score cao ({len(other_rows)} signals):")
        print(f"  {'Mã':<8} {'Score':>6} {'Entry':>10} {'SL':>10} {'TP':>10}  {'Ngày':<12}")
        print(f"{'─'*65}")
        for r in other_rows[:10]:
            print(f"  {r['ticker']:<8} {(r['strength'] or 0):>5.0f}% {(r['entry_price'] or 0):>10,.0f} "
                  f"{(r['stop_loss'] or 0):>10,.0f} {(r['take_profit'] or 0):>10,.0f}  {r['date'] or '—':<12}")

    print(f"\n  Tổng VIP-eligible: {len(vn30_rows)+len(other_rows)} signals "
          f"({len(vn30_rows)} VN30 + {len(other_rows)} non-VN30)")

    return vn30_rows, other_rows


def push_vip_signals_to_dashboard():
    """
    Option 19: Push VIP signals lên Production VIP Dashboard.
    Đọc từ local signals.db → lọc VN30 + score >= VIP_MIN_SCORE
    → POST lên /api/signals production (cùng endpoint với option 14)
    → VIP scanner sẽ tự lọc khi user vào VIP Dashboard
    """
    print(f"\n{'='*60}")
    print("💎 PUSH VIP SIGNALS LÊN PRODUCTION")
    print(f"{'='*60}")

    # Preview trước
    vn30_rows, other_rows = view_vip_signals()
    all_vip = vn30_rows + other_rows

    if not all_vip:
        print("\n  ⚠️  Không có signal nào đủ tiêu chuẩn VIP trong local DB")
        print("  Hãy chạy scanner trước hoặc thêm signal thủ công (option 10)")
        return

    # Chọn loại push
    print(f"\n  Push loại nào?")
    print(f"  a. Chỉ VN30 ({len(vn30_rows)} signals) — Khuyến nghị")
    print(f"  b. Tất cả VIP-eligible ({len(all_vip)} signals)")
    kind = input("  Chọn (a/b): ").strip().lower()
    if kind not in ('a', 'b'):
        print("  ❌ Hủy")
        return
    signals_to_push = vn30_rows if kind == 'a' else all_vip

    # Chọn môi trường
    print(f"\n  Môi trường:")
    print(f"  1. Production (ai-advisor.vn)")
    print(f"  2. Staging (test)")
    env = input("  Chọn (1/2): ").strip()
    if env not in ('1', '2'):
        print("  ❌ Hủy")
        return
    api_url  = BACKEND_PROD if env == '1' else BACKEND_STAGING
    env_name = 'Production' if env == '1' else 'Staging'

    print(f"\n  Sẽ push {len(signals_to_push)} signals lên {env_name}:")
    for r in signals_to_push:
        rr = round((r['take_profit'] - r['entry_price']) / (r['entry_price'] - r['stop_loss']), 1) \
             if r['entry_price'] and r['stop_loss'] and r['entry_price'] > r['stop_loss'] > 0 and r['take_profit'] > r['entry_price'] else 0
        vn30_tag = ' 💎' if r['ticker'] in VN30_TICKERS else ''
        print(f"    {r['ticker']}{vn30_tag} | Score: {r['strength']:.0f}% | "
              f"Entry: {r['entry_price']:,.0f} | R/R: {rr}x | {r['date']}")

    confirm = input(f"\n  Xác nhận push {len(signals_to_push)} signals lên {env_name}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ⏹️  Hủy")
        return

    # Push
    print(f"\n  Đang push...")
    success = 0
    failed  = 0
    skipped = 0

    for r in signals_to_push:
        payload = {
            'ticker':      r['ticker'],
            'strategy':    r['strategy'] or 'PULLBACK',
            'entry_price': float(r['entry_price'] or 0),
            'stop_loss':   float(r['stop_loss']   or 0),
            'take_profit': float(r['take_profit'] or 0),
            'risk_reward': float(round(
                (r['take_profit'] - r['entry_price']) / (r['entry_price'] - r['stop_loss']), 2
            )) if r['entry_price'] and r['stop_loss'] and r['entry_price'] > r['stop_loss'] > 0 else 0,
            'strength':    float(r['strength'] or 0),
            'stock_type':  r['stock_type'] or 'Mid Cap',
            'is_priority': 1 if r['ticker'] in VN30_TICKERS else 0,
            'rsi':         float(r['rsi']) if r['rsi'] else None,
            'date':        r['date'] or datetime.now().strftime('%Y-%m-%d'),
            'action':      'BUY',
        }
        try:
            resp = requests.post(f"{api_url}/signals", json=payload, timeout=15)
            if resp.status_code == 200 and resp.json().get('success'):
                success += 1
                print(f"    ✅ {r['ticker']}")
            elif resp.status_code == 409:
                skipped += 1
                print(f"    ⏭️  {r['ticker']} (đã có)")
            else:
                failed += 1
                print(f"    ❌ {r['ticker']}: HTTP {resp.status_code}")
        except Exception as e:
            failed += 1
            print(f"    ❌ {r['ticker']}: {e}")

    print(f"\n  {'─'*40}")
    print(f"  ✅ Thành công : {success}")
    print(f"  ⏭️  Bỏ qua    : {skipped} (đã có)")
    print(f"  ❌ Thất bại  : {failed}")
    print(f"\n  → Vào VIP Dashboard → click 🔄 để xem tín hiệu mới")

# ========================================================================
# MAIN MENU
# ========================================================================

def main():
    while True:
        print(f"\n{'='*60}")
        print("📋 SIGNAL REVIEWER & EDITOR")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"📂 DB: {DB_PATH}")
        print(f"{'='*60}")
        print()
        print("  XEM:")
        print("  1. 📊 Tổng quan (Market Risk + Signals)")
        print("  2. 📈 BUY signals hôm nay")
        print("  3. 📈 TẤT CẢ BUY signals")
        print("  4. 📉 SELL signals")
        print("  5. 🛡️ Market Risk")
        print()
        print("  SỬA BUY:")
        print("  6. ❌ Xóa BUY signal theo ID")
        print("  7. ❌ Xóa BUY signals theo mã CP")
        print("  8. ❌ Xóa signals score thấp")
        print("  9. ❌ Xóa signals cũ")
        print("  10. ➕ Thêm BUY signal thủ công")
        print()
        print("  SỬA SELL & MARKET:")
        print("  11. 📉 Sửa SELL signals (xóa/sửa reason)")
        print("  12. 🛡️ Sửa Market Risk (mode/score/tỷ trọng)")
        print()
        print("  PUSH LÊN WEBSITE:")
        print("  13. 🚀 Push Market Risk")
        print("  14. 🚀 Push BUY signals")
        print("  15. 🚀 Push SELL signals")
        print("  16. ➕ Thêm SELL signal thủ công")
        print()
        print("  VIP:")
        print("  17. 💎 Gửi Telegram VIP (BUY signals / Market Risk / Tùy chỉnh)")
        print("  18. 🔍 Xem VIP signals (preview)")
        print("  19. 💎 Push VIP signals lên VIP Dashboard")
        print()
        print("  0. Thoát")
        print()

        choice = input("Chọn (0-19): ").strip()
        
        if choice == '0':
            print("\n👋 Bye!")
            break
        elif choice == '1':
            view_all_summary()
        elif choice == '2':
            today = datetime.now().strftime('%Y-%m-%d')
            view_buy_signals(date_filter=today)
        elif choice == '3':
            view_buy_signals()
        elif choice == '4':
            view_sell_signals()
        elif choice == '5':
            view_market_risk()
        elif choice == '6':
            view_buy_signals()
            raw = input("\nNhập ID (hoặc nhiều ID cách dấu phẩy, VD: 1044,1050,1059): ").strip()
            if raw:
                ids = []
                for part in raw.replace(',', ' ').split():
                    digits = ''.join(c for c in part if c.isdigit())
                    if digits:
                        ids.append(int(digits))
                if ids:
                    for sid in ids:
                        delete_signal_by_id(sid)
                else:
                    print("❌ Không tìm thấy ID hợp lệ. Chỉ nhập số, VD: 1044")
        elif choice == '7':
            ticker = input("\nNhập mã CP (VD: SSI hoặc nhiều mã: SSI,VDS,ORS): ").strip().upper()
            if ticker:
                for t in ticker.replace(',', ' ').split():
                    t = t.strip()
                    if t:
                        delete_signals_by_ticker(t)
        elif choice == '8':
            try:
                score = input("Score tối thiểu (mặc định 70): ").strip()
                score = int(score) if score else 70
                delete_low_score(score)
            except ValueError:
                delete_low_score(70)
        elif choice == '9':
            try:
                days = input("Xóa signals cũ hơn bao nhiêu ngày (mặc định 30): ").strip()
                days = int(days) if days else 30
                delete_old_signals(days)
            except ValueError:
                delete_old_signals(30)
        elif choice == '10':
            add_signal_manual()
        elif choice == '11':
            edit_sell_signals()
        elif choice == '12':
            edit_market_risk()
        elif choice == '13':
            print("\n🚀 Push Market Risk...")
            os.system(f'python "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "push_market_risk.py")}"')
        elif choice == '14':
            print("\n🚀 Push BUY signals...")
            os.system(f'python "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "push_local_signals.py")}"')
        elif choice == '15':
            push_sell_signals_to_production()
        elif choice == '16':
            add_sell_signal_manual()
        elif choice == '17':
            push_vip_telegram()
        elif choice == '18':
            view_vip_signals()
        elif choice == '19':
            push_vip_signals_to_dashboard()
        else:
            print("❌ Lựa chọn không hợp lệ")


if __name__ == '__main__':
    main()
