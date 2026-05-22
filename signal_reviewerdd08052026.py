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

DB_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signals.db')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
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


def delete_duplicate_signals():
    """Xóa signals trùng lặp — giữ lại record mới nhất (id cao nhất)"""
    conn = get_db_connection()
    dupes = conn.execute("""
        SELECT ticker, action, date, strategy,
               COUNT(*) as cnt, MAX(id) as keep_id
        FROM signals
        GROUP BY ticker, action, date, strategy
        HAVING COUNT(*) > 1
        ORDER BY date DESC
    """).fetchall()
    if not dupes:
        print("\n  ✅ Không có signal trùng lặp nào")
        conn.close(); return
    total_dupes = sum(r['cnt'] - 1 for r in dupes)
    print(f"\n  ⚠️  Tìm thấy {len(dupes)} nhóm trùng ({total_dupes} records sẽ bị xóa):")
    print(f"  {'#':>3} {'Ticker':<8} {'Action':<6} {'Date':<12} {'Strategy':<16} {'Trùng':>5} {'Giữ ID':>7}")
    print("  " + "-"*60)
    for i, r in enumerate(dupes, 1):
        print(f"  {i:>3} {r['ticker']:<8} {r['action']:<6} {r['date']:<12} {r['strategy'] or '?':<16} {r['cnt']:>5}x  {r['keep_id']:>7}")
    if input(f"\n  Xóa {total_dupes} records trùng? (y/n): ").strip().lower() != 'y':
        conn.close(); print("  ⏹️ Hủy"); return
    deleted = 0
    for r in dupes:
        res = conn.execute(
            "DELETE FROM signals WHERE ticker=? AND action=? AND date=? AND (strategy=? OR (strategy IS NULL AND ?='')) AND id != ?",
            (r['ticker'], r['action'], r['date'], r['strategy'] or '', r['strategy'] or '', r['keep_id'])
        )
        deleted += res.rowcount
    conn.commit(); conn.close()
    print(f"  ✅ Đã xóa {deleted} records trùng lặp")


def clean_signals_menu():
    """Menu con cho option 9 — Dọn dẹp & Xóa signals"""
    while True:
        conn = get_db_connection()
        total    = conn.execute("SELECT COUNT(*) as c FROM signals").fetchone()['c']
        today    = datetime.now().strftime('%Y-%m-%d')
        today_buy= conn.execute("SELECT COUNT(*) as c FROM signals WHERE action='BUY' AND date=?", (today,)).fetchone()['c']
        dupes_c  = conn.execute("""
            SELECT COALESCE(SUM(cnt-1),0) as c FROM (
                SELECT COUNT(*) as cnt FROM signals GROUP BY ticker, action, date, strategy HAVING COUNT(*) > 1)
        """).fetchone()['c']
        conn.close()
        print(f"\n{'='*60}")
        print("🗑️  DỌN DẸP & XÓA SIGNALS")
        print(f"{'='*60}")
        print(f"  📊 Tổng: {total} | Hôm nay BUY: {today_buy} | Trùng: {dupes_c}")
        print()
        print("  a. 🔍 Xóa TRÙNG LẶP (giữ id mới nhất)")
        print("  b. 📅 Xóa CŨ hơn N ngày")
        print("  c. ⭐ Xóa SCORE THẤP")
        print("  d. 🧹 Xóa TẤT CẢ BUY signals")
        print("  e. ↩️  Quay lại")
        sub = input("\n  Chọn (a-e): ").strip().lower()
        if sub == 'e': break
        elif sub == 'a': delete_duplicate_signals()
        elif sub == 'b':
            try:
                days = input("  Cũ hơn bao nhiêu ngày (mặc định 30): ").strip()
                delete_old_signals(int(days) if days else 30)
            except ValueError: delete_old_signals(30)
        elif sub == 'c':
            try:
                score = input("  Score tối thiểu (mặc định 70): ").strip()
                delete_low_score(int(score) if score else 70)
            except ValueError: delete_low_score(70)
        elif sub == 'd':
            conn = get_db_connection()
            cnt = conn.execute("SELECT COUNT(*) as c FROM signals WHERE action='BUY'").fetchone()['c']
            conn.close()
            if cnt == 0: print("  ✅ Không có BUY signal nào"); continue
            if input(f"  ⚠️  Xóa TẤT CẢ {cnt} BUY signals? (yes/no): ").strip().lower() == 'yes':
                conn = get_db_connection()
                conn.execute("DELETE FROM signals WHERE action='BUY'")
                conn.commit(); conn.close()
                print(f"  ✅ Đã xóa {cnt} BUY signals")
            else: print("  ⏹️ Hủy")
        else: print("  ❌ Lựa chọn không hợp lệ")


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



def add_sell_signal_manual():
    """Thêm SELL signal thủ công vào sell_signals_latest.json"""
    print(f"\n{'='*60}")
    print("➕ THÊM SELL SIGNAL THỦ CÔNG")
    print(f"{'='*60}")

    try:
        # Lấy danh sách BUY signals đang open từ SQLite
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT ticker, signal_code, entry_price, stop_loss, take_profit, stock_type
            FROM signals
            WHERE action='BUY' AND status='open'
            ORDER BY ticker
        """).fetchall()
        conn.close()

        if not rows:
            print("  ❌ Không có BUY signal nào đang open")
            return

        print("  📋 BUY signals đang open:")
        for i, r in enumerate(rows):
            print(f"  {i+1:>3}. {r[0]:<8} Entry: {r[2]:>10,.0f}  SL: {r[3]:>10,.0f}  TP: {r[4]:>10,.0f}  [{r[1]}]")

        pick = input("\n  Chọn số thứ tự (hoặc nhập mã CP): ").strip()

        # Find matching signal
        selected = None
        if pick.isdigit():
            idx = int(pick) - 1
            if 0 <= idx < len(rows):
                selected = rows[idx]
        else:
            ticker_input = pick.upper()
            matches = [r for r in rows if r[0] == ticker_input]
            if matches:
                selected = matches[0]

        if not selected:
            print("  ❌ Không tìm thấy signal")
            return

        ticker, signal_code, entry_price, stop_loss, take_profit, stock_type = selected
        print(f"\n  ✅ Đã chọn: {ticker} ({signal_code}) | Entry: {entry_price:,.0f}")

        # Get current exit price
        exit_price_str = input(f"  Giá thoát (giá hiện tại): ").strip()
        if not exit_price_str:
            print("  ❌ Cần nhập giá thoát")
            return
        exit_price = float(exit_price_str)

        # Exit reason
        print("  Lý do thoát:")
        print("  1. STOP_LOSS")
        print("  2. TAKE_PROFIT")
        print("  3. MANUAL_EXIT")
        reason_pick = input("  Chọn (1/2/3, mặc định 1): ").strip()
        reason_map = {'1': 'STOP_LOSS', '2': 'TAKE_PROFIT', '3': 'MANUAL_EXIT'}
        exit_reason = reason_map.get(reason_pick, 'STOP_LOSS')

        exit_pct_str = input("  % thoát (100 = toàn bộ, mặc định 100): ").strip()
        exit_pct = int(exit_pct_str) if exit_pct_str else 100

        pnl = round(((exit_price - entry_price) / entry_price) * 100, 2)

        print(f"\n  📋 Xác nhận SELL:")
        print(f"     {ticker} | {exit_reason} | Entry: {entry_price:,.0f} → Exit: {exit_price:,.0f}")
        print(f"     P/L: {pnl:+.2f}% | Bán: {exit_pct}%")

        confirm = input("  Thêm? (y/n): ").strip().lower()
        if confirm != 'y':
            print("  ⏹️ Hủy")
            return

        # Load or create sell_signals_latest.json
        import json
        if os.path.exists(SELL_FILE):
            with open(SELL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {'date': datetime.now().strftime('%Y-%m-%d'), 'sell_signals': [], 'count': 0}

        new_signal = {
            'ticker': ticker,
            'exit_reason': exit_reason,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'profit_loss_pct': pnl,
            'exit_quantity_pct': exit_pct,
            'signal_code': signal_code,
            'buy_signal_code': signal_code,
            'note': f'Manual SELL - {exit_reason}'
        }

        data['sell_signals'].append(new_signal)
        data['count'] = len(data['sell_signals'])
        data['date'] = datetime.now().strftime('%Y-%m-%d')

        with open(SELL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        emoji = '🔴' if pnl < 0 else '🟢'
        print(f"  {emoji} Đã thêm SELL signal {ticker} vào sell_signals_latest.json")
        print(f"  👉 Dùng Option 15 để push lên website")

    except ValueError:
        print("  ❌ Giá trị không hợp lệ")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


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


def wake_up_server(api_base_url: str, env_name: str) -> bool:
    """Ping /health để wake up Render server trước khi push."""
    base = api_base_url.replace('/api', '')
    url  = f"{base}/health"
    print(f"  ⏳ Wake up {env_name}...", end='', flush=True)
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            print(f" ✅ OK ({resp.elapsed.total_seconds():.1f}s)")
            return True
        else:
            print(f" ⚠️  Status {resp.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"\n  ❌ Timeout — thử lại sau 30 giây")
        return False
    except Exception as e:
        print(f"\n  ❌ Lỗi kết nối: {e}")
        return False


def push_with_env_choice(script_name: str, label: str):
    """Hỏi production hay staging rồi wake up + gọi script tương ứng."""
    import subprocess, sys as _sys
    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"\n  ❌ Không tìm thấy {script_name}")
        return
    print(f"\n  🚀 Push {label}")
    print(f"     1. Production  ({BACKEND_PROD.replace('/api','')})")
    print(f"     2. Staging     ({BACKEND_STAGING.replace('/api','')})")
    env = input("     Chọn (1/2, Enter = Production): ").strip()
    if env == '2':
        env_name = 'STAGING';  api_base = BACKEND_STAGING; cmd = [_sys.executable, script_path, '--staging']
    else:
        env_name = 'PRODUCTION'; api_base = BACKEND_PROD; cmd = [_sys.executable, script_path]
    if not wake_up_server(api_base, env_name):
        if input("  Server chưa sẵn sàng. Vẫn tiếp tục? (y/n): ").strip().lower() != 'y':
            print("  ⏹️ Đã hủy."); return
    if input(f"  Push {label} lên {env_name}? (y/n): ").strip().lower() != 'y':
        print("  ⏹️ Đã hủy."); return
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    if result.returncode == 0:
        print(f"  ✅ Push {label} lên {env_name} xong!")
    else:
        print(f"  ⚠️ Script kết thúc returncode={result.returncode}")


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
            resp = requests.post(f"{api_url}/signals", json=payload, timeout=30)
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

    # Dedup: cùng ticker+date → giữ 1 signal có score cao nhất
    seen = {}
    for r in signals_to_push:
        key = (r['ticker'], r['date'] or '')
        if key not in seen or (r['strength'] or 0) > (seen[key]['strength'] or 0):
            seen[key] = r
    signals_to_push = list(seen.values())
    dup_removed = len(seen) != len(list(seen.values()))

    if dup_removed or len(seen) < len(signals_to_push):
        print(f"\n  ⚠️  Đã loại {len(signals_to_push) - len(seen)} signals trùng ticker+date (giữ score cao nhất)")

    confirm = input(f"\n  Xác nhận push {len(signals_to_push)} signals lên {env_name}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ⏹️  Hủy")
        return

    # Push
    # Wake up server trước khi push
    if not wake_up_server(api_url, env_name):
        if input("  Server chưa sẵn sàng. Vẫn tiếp tục? (y/n): ").strip().lower() != 'y':
            print("  ⏹️  Đã hủy."); return

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
            resp = requests.post(f"{api_url}/signals", json=payload, timeout=30)
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

def delete_vip_signal():
    """Option 20: Xóa VIP signal từ production hoặc staging"""
    print(f"\n{'='*60}")
    print("❌ XÓA VIP SIGNAL KHỎI SERVER")
    print(f"{'='*60}")

    print("  Môi trường:")
    print("  1. Production (ai-advisor.vn)")
    print("  2. Staging (test)")
    env = input("  Chọn (1/2): ").strip()
    api_url  = BACKEND_PROD if env == '1' else BACKEND_STAGING
    env_name = 'Production' if env == '1' else 'Staging'

    # Lấy danh sách BUY signals từ server
    try:
        resp = requests.get(f"{api_url}/signals", timeout=30)
        if resp.status_code != 200:
            print(f"  ❌ Không lấy được signals: HTTP {resp.status_code}")
            return
        data = resp.json()
        signals = data.get('signals', data.get('data', []))
        buys = [s for s in signals if s.get('action') == 'BUY' and s.get('status') in ('open', None, '')]
        if not buys:
            print("  ⚠️  Không có BUY signals nào trên server")
            return
    except Exception as e:
        print(f"  ❌ Lỗi kết nối: {e}")
        return

    # Hiển thị danh sách
    print(f"\n  📋 BUY signals hiện có trên {env_name} ({len(buys)} signals):")
    print(f"  {'#':>3} {'ID':>6} {'Ticker':<7} {'Score':>6} {'Entry':>10} {'Date':<12} {'Strategy':<14}")
    print("  " + "-" * 65)
    for i, s in enumerate(buys, 1):
        print(f"  {i:>3} {str(s.get('id','')):>6} {s.get('ticker','?'):<7} "
              f"{s.get('strength',0):>5.0f}% {s.get('entry_price',0):>10,.0f} "
              f"{str(s.get('date','')):<12} {s.get('strategy','?'):<14}")

    print()
    picks = input("  Nhập số thứ tự cần xóa (VD: 1 3 5, hoặc Enter để hủy): ").strip()
    if not picks:
        print("  ⏹️  Hủy")
        return

    to_delete = []
    for p in picks.split():
        try:
            idx = int(p) - 1
            if 0 <= idx < len(buys):
                to_delete.append(buys[idx])
        except ValueError:
            pass

    if not to_delete:
        print("  ❌ Không có signal hợp lệ được chọn")
        return

    print(f"\n  Sẽ xóa {len(to_delete)} signal(s):")
    for s in to_delete:
        print(f"    → {s.get('ticker')} | ID:{s.get('id')} | {s.get('date')} | {s.get('strategy')}")

    confirm = input("\n  Xác nhận xóa? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ⏹️  Hủy")
        return

    deleted = 0
    for s in to_delete:
        try:
            resp = requests.delete(f"{api_url}/signals/{s['id']}", timeout=30)
            if resp.status_code in (200, 204):
                print(f"  ✅ Đã xóa {s.get('ticker')} (ID:{s.get('id')})")
                deleted += 1
            else:
                print(f"  ❌ {s.get('ticker')}: HTTP {resp.status_code} — {resp.text[:80]}")
        except Exception as e:
            print(f"  ❌ {s.get('ticker')}: {e}")

    print(f"\n  ✅ Đã xóa {deleted}/{len(to_delete)} signals khỏi {env_name}")


def add_vip_signal_manual():
    """Option 21: Thêm VIP signal thủ công lên production/staging"""
    print(f"\n{'='*60}")
    print("💎 THÊM VIP SIGNAL THỦ CÔNG")
    print(f"{'='*60}")

    try:
        ticker = input("  Mã CP (VD: TCB): ").strip().upper()
        if not ticker:
            print("  ❌ Hủy")
            return

        # Tìm trong local DB để điền sẵn
        conn = get_db_connection()
        local = conn.execute(
            "SELECT * FROM signals WHERE ticker=? AND action='BUY' ORDER BY date DESC LIMIT 3",
            (ticker,)
        ).fetchall()
        conn.close()

        entry_default = sl_default = tp_default = score_default = None
        strategy_default = 'PULLBACK'
        stock_type_default = 'Blue Chip' if ticker in VN30_TICKERS else 'Mid Cap'

        if local:
            r = local[0]
            entry_default    = r['entry_price']
            sl_default       = r['stop_loss']
            tp_default       = r['take_profit']
            score_default    = r['strength']
            strategy_default = r['strategy'] or 'PULLBACK'
            stock_type_default = r['stock_type'] or stock_type_default
            print(f"\n  📋 Tìm thấy trong local DB:")
            for row in local:
                print(f"     {row['date']} | {row['strategy']} | Score:{row['strength']:.0f}% | Entry:{row['entry_price']:,.0f}")
            use_local = input("  Dùng dữ liệu từ local? (Enter=có / n=nhập tay): ").strip().lower()
            if use_local == 'n':
                entry_default = sl_default = tp_default = score_default = None

        # Nhập thông tin
        def ask(prompt, default=None, cast=float):
            if default is not None:
                val = input(f"  {prompt} (mặc định {default:,.0f}): ").strip()
                return cast(val) if val else cast(default)
            return cast(input(f"  {prompt}: ").strip())

        entry_price = ask("Giá vào (Entry)", entry_default)
        stop_loss   = ask("Stop Loss", sl_default)
        take_profit = ask("Take Profit", tp_default)
        strength    = ask("Score % (VD: 80)", score_default or 80, cast=float)

        # Strategy
        print("  Chiến lược: 1.PULLBACK  2.EMA_CROSS  3.DIVERGENCE_FB  4.MANUAL")
        strat_map = {'1':'PULLBACK','2':'EMA_CROSS','3':'DIVERGENCE_FB','4':'MANUAL'}
        strat_in  = input(f"  Chọn (1-4, mặc định {strategy_default}): ").strip()
        strategy  = strat_map.get(strat_in, strategy_default)

        # Stock type
        st_in      = input(f"  Loại (mặc định {stock_type_default}): ").strip()
        stock_type = st_in if st_in else stock_type_default

        # Ngày
        today      = datetime.now().strftime('%Y-%m-%d')
        date_in    = input(f"  Ngày (mặc định {today}): ").strip()
        signal_date = date_in if date_in else today

        # R/R
        rr = round((take_profit - entry_price) / (entry_price - stop_loss), 2)              if entry_price > stop_loss > 0 and take_profit > entry_price else 0

        print(f"\n  📋 Xác nhận VIP signal:")
        print(f"     {ticker} 💎 | {strategy} | Score: {strength:.0f}%")
        print(f"     Entry: {entry_price:,.0f} | SL: {stop_loss:,.0f} | TP: {take_profit:,.0f} | R/R: {rr}x")
        print(f"     {stock_type} | {signal_date}")

        # Môi trường
        print("\n  Đẩy lên:")
        print("  1. Production")
        print("  2. Staging")
        print("  3. Cả hai")
        env_choice = input("  Chọn (1/2/3): ").strip()

        envs = []
        if env_choice == '1': envs = [('Production', BACKEND_PROD)]
        elif env_choice == '2': envs = [('Staging', BACKEND_STAGING)]
        elif env_choice == '3': envs = [('Production', BACKEND_PROD), ('Staging', BACKEND_STAGING)]
        else:
            print("  ❌ Hủy")
            return

        confirm = input("\n  Xác nhận push? (y/n): ").strip().lower()
        if confirm != 'y':
            print("  ⏹️  Hủy")
            return

        payload = {
            'ticker':      ticker,
            'strategy':    strategy,
            'entry_price': entry_price,
            'stop_loss':   stop_loss,
            'take_profit': take_profit,
            'risk_reward': rr,
            'strength':    strength,
            'stock_type':  stock_type,
            'is_priority': 1 if ticker in VN30_TICKERS else 0,
            'date':        signal_date,
            'action':      'BUY',
        }

        for env_name, api_url in envs:
            try:
                resp = requests.post(f"{api_url}/signals", json=payload, timeout=30)
                if resp.status_code in (200, 201):
                    print(f"  ✅ Đã push {ticker} lên {env_name}!")
                elif resp.status_code == 409:
                    print(f"  ⚠️  {ticker} đã có trên {env_name} (duplicate)")
                else:
                    print(f"  ❌ {env_name}: HTTP {resp.status_code} — {resp.text[:100]}")
            except Exception as e:
                print(f"  ❌ {env_name}: {e}")

    except ValueError:
        print("  ❌ Giá trị không hợp lệ")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")


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
        print("  9. 🗑️  Dọn dẹp signals (cũ / trùng / reset)")
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
        print("  20. ❌ Xóa VIP signal khỏi server (manual)")
        print("  21. ➕ Thêm VIP signal thủ công lên server")
        print()
        print("  0. Thoát")
        print()

        choice = input("Chọn (0-21): ").strip()
        
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
            clean_signals_menu()
        elif choice == '10':
            add_signal_manual()
        elif choice == '11':
            edit_sell_signals()
        elif choice == '12':
            edit_market_risk()
        elif choice == '13':
            push_with_env_choice('push_market_risk.py', 'Market Risk')
        elif choice == '14':
            push_with_env_choice('push_local_signals.py', 'BUY signals')
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
        elif choice == '20':
            delete_vip_signal()
        elif choice == '21':
            add_vip_signal_manual()
        else:
            print("❌ Lựa chọn không hợp lệ")


if __name__ == '__main__':
    main()
