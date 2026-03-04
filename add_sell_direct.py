#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADD SELL SIGNAL - DIRECT TO DATABASE
=====================================

Thêm SELL signal trực tiếp vào database (bypass signal_reviewer)

Cách chạy:
  cd C:\\ai-advisor1
  python add_sell_direct.py
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'signals.db')

print("\n" + "=" * 60)
print("➕ THÊM SELL SIGNAL TRỰC TIẾP")
print("=" * 60)

# Check DB
if not os.path.exists(DB_PATH):
    print(f"❌ Database not found: {DB_PATH}")
    exit()

try:
    # Input
    ticker = input("\n  Mã CP (VD: VCB): ").strip().upper()
    if not ticker:
        print("  ❌ Hủy")
        exit()
    
    entry = float(input("  Giá mua ban đầu (VD: 85000): ").strip())
    exit_price = float(input("  Giá bán (VD: 80000): ").strip())
    
    # Calculate P/L
    pl_pct = ((exit_price - entry) / entry) * 100
    
    # Exit reason
    print("\n  Exit Reason:")
    print("    1. STOP_LOSS (Cắt lỗ)")
    print("    2. TAKE_PROFIT (Chốt lời)")
    print("    3. MA20_BREAK (MA20)")
    
    reason_choice = input("  Chọn (1-3, mặc định 2): ").strip()
    reason_map = {
        '1': 'STOP_LOSS',
        '2': 'TAKE_PROFIT',
        '3': 'MA20_BREAK'
    }
    exit_reason = reason_map.get(reason_choice, 'TAKE_PROFIT')
    
    # Exit quantity
    exit_qty = input("  % bán (50, 100, mặc định 100): ").strip()
    exit_qty = int(exit_qty) if exit_qty else 100
    
    # Stock type
    stock_type = input("  Loại (Blue Chip / Mid Cap, mặc định Mid Cap): ").strip()
    stock_type = stock_type if stock_type else 'Mid Cap'
    
    # Date - IMPORTANT: Dùng today
    today = datetime.now().strftime('%Y-%m-%d')
    date = input(f"  Ngày (mặc định {today}): ").strip()
    date = date if date else today
    
    # Confirmation
    pl_emoji = '🟢' if pl_pct >= 0 else '🔴'
    print(f"\n  📋 Xác nhận:")
    print(f"     {ticker} | Entry: {entry:,.0f} → Exit: {exit_price:,.0f}")
    print(f"     {pl_emoji} P/L: {pl_pct:+.2f}%")
    print(f"     Exit: {exit_reason} | Bán: {exit_qty}%")
    print(f"     {stock_type} | {date}")
    
    confirm = input("  Thêm SELL signal? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  ⏹️ Hủy")
        exit()
    
    # Insert to database
    conn = sqlite3.connect(DB_PATH)
    
    # Calculate position_pct remaining
    position_pct = 0 if exit_qty >= 100 else (100 - exit_qty)
    status = 'closed' if exit_qty >= 100 else 'partial'
    
    # INSERT
    conn.execute(
        """INSERT INTO signals (
            ticker, action, entry_price, exit_price, 
            stop_loss, take_profit, strategy, strength, 
            stock_type, date, rsi, is_priority, 
            profit_loss_pct, exit_quantity_pct
        ) VALUES (?, 'SELL', ?, ?, 0, 0, ?, 80, ?, ?, 50, 0, ?, ?)""",
        (ticker, entry, exit_price, exit_reason, stock_type, date, pl_pct, exit_qty)
    )
    
    conn.commit()
    signal_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    print(f"\n  ✅ Đã thêm SELL signal {ticker} vào database!")
    print(f"  🆔 Signal ID: {signal_id}")
    print(f"  📅 Date: {date}")
    
    # Verify
    print(f"\n  🔍 Verify...")
    conn.row_factory = sqlite3.Row
    
    rows = conn.execute(
        "SELECT * FROM signals WHERE id=?",
        (signal_id,)
    ).fetchall()
    
    if rows:
        r = rows[0]
        print(f"     ✅ Signal found in database!")
        print(f"        Ticker: {r['ticker']}")
        print(f"        Strategy: {r['strategy']}")
        print(f"        Entry: {r['entry_price']:,.0f}")
        print(f"        Exit: {r['exit_price']:,.0f}")
        print(f"        Date: {r['date']}")
    
    conn.close()
    
    print(f"\n  💡 Xem signals:")
    print(f"     python signal_reviewer.py → Option 4")
    print(f"\n  💡 Push lên production:")
    print(f"     python signal_reviewer.py → Option 15")
    
except ValueError:
    print("  ❌ Giá trị không hợp lệ. Nhập số, VD: 85000")
except Exception as e:
    print(f"  ❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
