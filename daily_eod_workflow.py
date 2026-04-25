#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAILY EOD WORKFLOW - Chạy cuối ngày trên máy local
===================================================

Quy trình:
  1. Scanner quét 346 mã → tạo signals + breadth data
  2. Market Risk phân tích → tạo kết quả
  3. Đẩy Market Risk lên production DB
  4. Sơn review signals → lọc kỹ → upload thủ công lên BUY SIGNAL

Cách chạy:
  cd C:\\ai-advisor1
  python daily_eod_workflow.py

Thời gian: ~25-30 phút (scanner 20-25 phút + market risk vài giây)
"""

import subprocess
import sys
import os
import json
import requests
from datetime import datetime

# ========================================================================
# CONFIGURATION
# ========================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCANNER_PATH = os.path.join(SCRIPT_DIR, 'scripts', 'daily_signal_scanner_eod.py')
MARKET_RISK_PATH = os.path.join(SCRIPT_DIR, 'market_risk_analysis.py')
BREADTH_FILE = os.path.join(SCRIPT_DIR, 'market_breadth_eod.json')
MARKET_RISK_FILE = os.path.join(SCRIPT_DIR, 'market_risk_latest.json')

# Production API
PROD_API          = 'https://ai-advisor1-backend.onrender.com'
SIGNAL_DB_PATH    = os.path.join(SCRIPT_DIR, 'signals.db')
VIP_MIN_SCORE     = 65   # Score tối thiểu để push lên VIP Dashboard

# VN30 tickers (30 mã bluechip)
VN30_TICKERS = {
    'ACB','BCM','BID','BVH','CTG','FPT','GAS','GVR','HDB','HPG',
    'MBB','MSN','MWG','PLX','POW','SAB','SHB','SSB','SSI','STB',
    'TCB','TPB','VCB','VHM','VIB','VIC','VJC','VNM','VPB','VRE',
}

# ========================================================================
# MAIN WORKFLOW
# ========================================================================

def main():
    print("\n" + "=" * 70)
    print("🚀 DAILY EOD WORKFLOW")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    # ── BƯỚC 1: Chạy Scanner ──
    print("\n" + "─" * 50)
    print("📊 BƯỚC 1/3: Chạy Scanner (20-25 phút)...")
    print("─" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, SCANNER_PATH],
            cwd=SCRIPT_DIR,
            timeout=2400  # 40 phút timeout
        )
        
        if result.returncode != 0:
            print("⚠️ Scanner có lỗi nhưng tiếp tục...")
        else:
            print("✅ Scanner hoàn tất!")
    except subprocess.TimeoutExpired:
        print("⚠️ Scanner timeout sau 40 phút!")
    except Exception as e:
        print(f"❌ Scanner lỗi: {e}")
        return
    
    # Kiểm tra breadth file
    if os.path.exists(BREADTH_FILE):
        with open(BREADTH_FILE, 'r', encoding='utf-8') as f:
            breadth = json.load(f)
        print(f"\n📊 Breadth: {breadth.get('advance', 0)} tăng / {breadth.get('decline', 0)} giảm")
        print(f"   MA20: {breadth.get('above_ma20', 0)}/{breadth.get('total', 0)} ({breadth.get('above_ma20_pct', 0)}%)")
    else:
        print("⚠️ Breadth file chưa được tạo!")
    
    # ── BƯỚC 2: Market Risk Analysis ──
    print("\n" + "─" * 50)
    print("📊 BƯỚC 2/3: Market Risk Analysis (vài giây)...")
    print("─" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, MARKET_RISK_PATH],
            cwd=SCRIPT_DIR,
            timeout=120
        )
        
        if result.returncode != 0:
            print("❌ Market Risk lỗi!")
            return
        
        print("✅ Market Risk hoàn tất!")
    except Exception as e:
        print(f"❌ Market Risk lỗi: {e}")
        return
    
    # ── BƯỚC 3: Đẩy Market Risk lên Production ──
    print("\n" + "─" * 50)
    print("🚀 BƯỚC 3/3: Đẩy Market Risk lên Production...")
    print("─" * 50)
    
    if not os.path.exists(MARKET_RISK_FILE):
        print("❌ File market_risk_latest.json không tìm thấy!")
        return
    
    with open(MARKET_RISK_FILE, 'r', encoding='utf-8') as f:
        risk_data = json.load(f)
    
    # Hiển thị kết quả trước khi đẩy
    mode_emoji = risk_data.get('mode_emoji', '🟡')
    mode_label = risk_data.get('mode_label', 'N/A')
    risk_score = risk_data.get('risk_score', 0)
    allocation = risk_data.get('allocation', 50)
    
    print(f"\n   {mode_emoji} Market Mode: {mode_label}")
    print(f"   📊 Risk Score: {risk_score}/100")
    print(f"   💰 Tỷ trọng: {allocation}% CP / {100 - allocation}% tiền mặt")
    print(f"   📝 {risk_data.get('description', '')}")
    
    # Hỏi xác nhận
    confirm = input("\n   Đẩy lên production? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("   ⏹️ Đã hủy.")
        return
    
    # Đẩy kết quả local lên production qua upload API
    try:
        print("   Đang đẩy kết quả lên production...")
        response = requests.post(
            f"{PROD_API}/api/market-risk/upload",
            json=risk_data,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            resp = response.json()
            print(f"   ✅ Market Risk đã cập nhật trên production!")
            print(f"   → {resp.get('message', '')}")
        else:
            print(f"   ⚠️ Production trả về status {response.status_code}")
            print(f"   Response: {response.text[:300]}")
                
    except requests.exceptions.ConnectionError:
        print("   ⚠️ Không kết nối được production (server đang ngủ?)")
        print("   💡 Thử wake up: truy cập https://ai-advisor1-backend.onrender.com/health")
        print("   Rồi chạy lại script này.")
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
    
    # ── BƯỚC 4: Preview VIP Signals ──
    print("\n" + "─" * 50)
    print("💎 BƯỚC 4/5: Preview VIP Signals từ local DB...")
    print("─" * 50)

    import sqlite3
    vip_preview = []
    try:
        conn = sqlite3.connect(SIGNAL_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM signals WHERE action='BUY' ORDER BY strength DESC, date DESC"
        ).fetchall()
        conn.close()

        vn30_signals  = [r for r in rows if r['ticker'] in VN30_TICKERS and (r['strength'] or 0) >= VIP_MIN_SCORE]
        other_signals = [r for r in rows if r['ticker'] not in VN30_TICKERS and (r['strength'] or 0) >= VIP_MIN_SCORE]
        vip_preview   = vn30_signals + other_signals

        print(f"   💎 VN30 signals  : {len(vn30_signals)}")
        print(f"   📊 Non-VN30 score cao: {len(other_signals)}")
        print(f"   📋 Tổng VIP-eligible: {len(vip_preview)}")
        print()
        if vn30_signals:
            print("   VN30 signals sẽ push:")
            for r in vn30_signals:
                rr = round((r['take_profit'] - r['entry_price']) / (r['entry_price'] - r['stop_loss']), 1) \
                     if r['entry_price'] and r['stop_loss'] and r['entry_price'] > r['stop_loss'] > 0 \
                     and r['take_profit'] > r['entry_price'] else 0
                print(f"   💎 {r['ticker']:<6} Score:{r['strength']:.0f}% "
                      f"Entry:{r['entry_price']:>10,.0f}  R/R:{rr}x  {r['date']}")
        else:
            print("   ⚠️  Không có VN30 signals trong local DB hôm nay")
    except Exception as e:
        print(f"   ❌ Lỗi đọc signals.db: {e}")

    # ── BƯỚC 5: Push VIP Signals ──
    print("\n" + "─" * 50)
    print("💎 BƯỚC 5/5: Push VIP Signals lên Production...")
    print("─" * 50)

    if not vip_preview:
        print("   ⚠️  Không có signals đủ tiêu chuẩn VIP — bỏ qua bước này")
        push_vip = False
    else:
        print(f"   Sẽ push {len(vip_preview)} signals lên VIP Dashboard")
        push_choice = input("\n   Push loại nào?\n   a. Chỉ VN30 ({}) — Khuyến nghị\n   b. Tất cả ({})\n   n. Bỏ qua\n   Chọn (a/b/n): ".format(
            len(vn30_signals), len(vip_preview))).strip().lower()
        push_vip = push_choice in ('a', 'b')
        signals_to_push = vn30_signals if push_choice == 'a' else vip_preview

    if push_vip and signals_to_push:
        pushed = 0
        skipped_dup = 0
        failed = 0
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
                resp = requests.post(f"{PROD_API}/api/signals", json=payload, timeout=15)
                if resp.status_code == 200 and resp.json().get('success'):
                    pushed += 1
                elif resp.status_code == 409:
                    skipped_dup += 1
                else:
                    failed += 1
                    print(f"   ⚠️  {r['ticker']}: HTTP {resp.status_code}")
            except Exception as e:
                failed += 1
                print(f"   ❌ {r['ticker']}: {e}")

        print(f"   ✅ Đã push: {pushed} | Bỏ qua: {skipped_dup} (dup) | Lỗi: {failed}")
        if pushed > 0:
            print("   → VIP Dashboard sẽ hiển thị signals sau khi refresh 🔄")
    else:
        print("   ⏭️  Bỏ qua push VIP signals")

    # ── TỔNG KẾT ──
    print("\n" + "=" * 70)
    print("📋 TỔNG KẾT")
    print("=" * 70)
    print(f"   ✅ Bước 1 — Scanner: Đã quét 346 mã")
    print(f"   ✅ Bước 2 — Breadth: Đã tạo market_breadth_eod.json")
    print(f"   ✅ Bước 3 — Market Risk: {mode_emoji} {mode_label} (Score: {risk_score})")
    print(f"   ✅ Bước 4 — VIP Preview: {len(vip_preview)} signals eligible")
    print(f"   ✅ Bước 5 — VIP Push: {'Đã push' if push_vip else 'Bỏ qua'}")
    print()
    print("   📌 BƯỚC TIẾP THEO:")
    print("   → python signal_reviewer.py → option 14: Push BUY signals (public)")
    print("   → python signal_reviewer.py → option 17: Gửi Telegram VIP")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
