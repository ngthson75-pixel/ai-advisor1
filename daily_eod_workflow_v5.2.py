#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAILY EOD WORKFLOW - Chạy cuối ngày trên máy local
===================================================

Quy trình:
  1. BUY Scanner: Quét 346 mã → tạo signals + breadth data
  2. Filter & Dedup: Lọc signals chất lượng + loại bỏ trùng lặp
  3. SELL Scanner V5.2: Quét SELL signals (T+2 + MA20 strict)
  4. Market Risk: Phân tích → tạo kết quả
  
  [MANUAL REVIEW - Chọn 1 trong 2]
  5. Signal Reviewer: python signal_reviewer.py
     → Review BUY/SELL/Market Risk trong UI
     → Upload lên staging/production
  
  6. Push Thủ Công:
     → python push_market_risk.py
     → python push_local_signals.py

Cách chạy:
  cd C:\\ai-advisor1
  python daily_eod_workflow.py

Thời gian: ~25-30 phút (BUY 20-25 min + SELL 2-5 min + others vài giây)
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

# Script paths
BUY_SCANNER_PATH = os.path.join(SCRIPT_DIR, 'scripts', 'daily_signal_scanner_eod.py')
FILTERED_PATH = os.path.join(SCRIPT_DIR, 'daily_scanner_FILTERED.py')
SELL_SCANNER_PATH = os.path.join(SCRIPT_DIR, 'sell_signal_scanner_v5.2.py')
MARKET_RISK_PATH = os.path.join(SCRIPT_DIR, 'market_risk_analysis.py')

# Data files
BREADTH_FILE = os.path.join(SCRIPT_DIR, 'market_breadth_eod.json')
MARKET_RISK_FILE = os.path.join(SCRIPT_DIR, 'market_risk_latest.json')
SELL_SIGNALS_FILE = os.path.join(SCRIPT_DIR, 'sell_signals_v5.2_latest.json')

# Production API (for reference only)
PROD_API = 'https://ai-advisor1-backend.onrender.com'

# ========================================================================
# MAIN WORKFLOW
# ========================================================================

def main():
    print("\n" + "=" * 70)
    print("🚀 DAILY EOD WORKFLOW - V5.2")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    # ──────────────────────────────────────────────────────────────────
    # BƯỚC 1: BUY Scanner
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("📊 BƯỚC 1/4: BUY Signal Scanner (20-25 phút)...")
    print("─" * 70)
    print("   Quét 346 mã → Tạo BUY signals + market breadth")
    
    if not os.path.exists(BUY_SCANNER_PATH):
        print(f"   ❌ File {BUY_SCANNER_PATH} không tồn tại!")
        print(f"   💡 Check đường dẫn: {BUY_SCANNER_PATH}")
        return
    
    try:
        result = subprocess.run(
            [sys.executable, BUY_SCANNER_PATH],
            cwd=SCRIPT_DIR,
            timeout=2400  # 40 phút timeout
        )
        
        if result.returncode != 0:
            print("   ⚠️ BUY Scanner có lỗi nhưng tiếp tục...")
        else:
            print("   ✅ BUY Scanner hoàn tất!")
    except subprocess.TimeoutExpired:
        print("   ⚠️ BUY Scanner timeout sau 40 phút!")
    except Exception as e:
        print(f"   ❌ BUY Scanner lỗi: {e}")
        return
    
    # Kiểm tra breadth file
    if os.path.exists(BREADTH_FILE):
        with open(BREADTH_FILE, 'r', encoding='utf-8') as f:
            breadth = json.load(f)
        advance = breadth.get('advance', 0)
        decline = breadth.get('decline', 0)
        above_ma20 = breadth.get('above_ma20', 0)
        total = breadth.get('total', 0)
        above_ma20_pct = breadth.get('above_ma20_pct', 0)
        
        print(f"\n   📊 Breadth: {advance} tăng / {decline} giảm")
        print(f"      MA20: {above_ma20}/{total} ({above_ma20_pct:.1f}%)")
    else:
        print("   ⚠️ Breadth file chưa được tạo!")
    
    # ──────────────────────────────────────────────────────────────────
    # BƯỚC 2: Filter & Dedup
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("🔍 BƯỚC 2/4: Filter & Dedup BUY Signals (vài giây)...")
    print("─" * 70)
    print("   Lọc signals chất lượng + loại bỏ trùng lặp")
    
    if not os.path.exists(FILTERED_PATH):
        print(f"   ⚠️ File {FILTERED_PATH} không tồn tại!")
        print(f"   → Bỏ qua bước filter, signals vẫn ở signals.db gốc")
    else:
        try:
            result = subprocess.run(
                [sys.executable, FILTERED_PATH],
                cwd=SCRIPT_DIR,
                timeout=120
            )
            
            if result.returncode != 0:
                print("   ⚠️ Filter có lỗi nhưng tiếp tục...")
            else:
                print("   ✅ Filter hoàn tất!")
        except Exception as e:
            print(f"   ❌ Filter lỗi: {e}")
    
    # ──────────────────────────────────────────────────────────────────
    # BƯỚC 3: SELL Scanner V5.2
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("🔴 BƯỚC 3/4: SELL Signal Scanner V5.2 (2-5 phút)...")
    print("─" * 70)
    print("   📌 V5.2 Features:")
    print("      • T+2 settlement: Chỉ bán sau 2 trading days")
    print("      • MA20 STRICT: 2 days < MA20 AND (loss >= 3% OR profit < 2%)")
    print("      • 5-step exit: TP1 50% → TP2 30% → Pullback/Trailing/MA20")
    
    if not os.path.exists(SELL_SCANNER_PATH):
        print(f"   ❌ File {SELL_SCANNER_PATH} không tồn tại!")
        print(f"   💡 Download V5.2 từ Claude và đặt vào: {SCRIPT_DIR}")
        print(f"   → Bỏ qua SELL scan")
    else:
        try:
            # Chạy dry-run để review trước
            print("   🔍 Chạy dry-run (không push)...")
            result = subprocess.run(
                [sys.executable, SELL_SCANNER_PATH, '--dry-run'],
                cwd=SCRIPT_DIR,
                timeout=600  # 10 phút timeout
            )
            
            if result.returncode != 0:
                print("   ⚠️ SELL Scanner có lỗi!")
            else:
                print("   ✅ SELL Scanner hoàn tất (dry-run)!")
                
                # Hiển thị kết quả nếu có
                if os.path.exists(SELL_SIGNALS_FILE):
                    with open(SELL_SIGNALS_FILE, 'r', encoding='utf-8') as f:
                        sell_data = json.load(f)
                    
                    count = sell_data.get('count', 0)
                    skipped = len(sell_data.get('skipped_t_plus', []))
                    
                    print(f"\n   📊 SELL Signals: {count}")
                    print(f"      ⏳ Skip T+2: {skipped}")
                    
                    # Group by exit reason
                    signals = sell_data.get('sell_signals', [])
                    if signals:
                        reasons = {}
                        for s in signals:
                            r = s.get('exit_reason', 'UNKNOWN')
                            reasons[r] = reasons.get(r, 0) + 1
                        
                        print(f"      Exit reasons:")
                        for reason, cnt in sorted(reasons.items()):
                            print(f"         • {reason}: {cnt}")
                    
                    print(f"\n   💾 File: {SELL_SIGNALS_FILE}")
                    print(f"   💡 Review trước khi push!")
                
        except subprocess.TimeoutExpired:
            print("   ⚠️ SELL Scanner timeout sau 10 phút!")
        except Exception as e:
            print(f"   ❌ SELL Scanner lỗi: {e}")
    
    # ──────────────────────────────────────────────────────────────────
    # BƯỚC 4: Market Risk Analysis
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("📊 BƯỚC 4/4: Market Risk Analysis (vài giây)...")
    print("─" * 70)
    
    if not os.path.exists(MARKET_RISK_PATH):
        print(f"   ❌ File {MARKET_RISK_PATH} không tồn tại!")
        return
    
    try:
        result = subprocess.run(
            [sys.executable, MARKET_RISK_PATH],
            cwd=SCRIPT_DIR,
            timeout=120
        )
        
        if result.returncode != 0:
            print("   ❌ Market Risk lỗi!")
        else:
            print("   ✅ Market Risk hoàn tất!")
    except Exception as e:
        print(f"   ❌ Market Risk lỗi: {e}")
    
    # Hiển thị kết quả Market Risk
    if os.path.exists(MARKET_RISK_FILE):
        with open(MARKET_RISK_FILE, 'r', encoding='utf-8') as f:
            risk_data = json.load(f)
        
        mode_emoji = risk_data.get('mode_emoji', '🟡')
        mode_label = risk_data.get('mode_label', 'N/A')
        risk_score = risk_data.get('risk_score', 0)
        allocation = risk_data.get('allocation', 50)
        
        print(f"\n   {mode_emoji} Market Mode: {mode_label}")
        print(f"   📊 Risk Score: {risk_score}/100")
        print(f"   💰 Tỷ trọng: {allocation}% CP / {100 - allocation}% tiền mặt")
        print(f"   📝 {risk_data.get('description', '')}")
    
    # ──────────────────────────────────────────────────────────────────
    # TỔNG KẾT & HƯỚNG DẪN
    # ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("📋 TỔNG KẾT - 4 BƯỚC TỰ ĐỘNG HOÀN TẤT")
    print("=" * 70)
    print(f"   ✅ Bước 1: BUY Scanner → signals.db + market_breadth_eod.json")
    print(f"   ✅ Bước 2: Filter & Dedup → signals.db (cleaned)")
    print(f"   ✅ Bước 3: SELL Scanner V5.2 → {os.path.basename(SELL_SIGNALS_FILE)}")
    print(f"   ✅ Bước 4: Market Risk → market_risk_latest.json")
    print()
    print("=" * 70)
    print("📌 MANUAL REVIEW - CHỌN 1 TRONG 2 CÁCH:")
    print("=" * 70)
    
    print("\n🔹 CÁCH 1: Signal Reviewer (Khuyến nghị)")
    print("   python signal_reviewer.py")
    print("   → Review BUY/SELL/Market Risk trong UI")
    print("   → Chọn signals muốn giữ")
    print("   → Upload staging/production trực tiếp")
    
    print("\n🔹 CÁCH 2: Push Thủ Công")
    print("   python push_market_risk.py      ← Đẩy Market Dashboard")
    print("   python push_local_signals.py    ← Đẩy signals đã lọc")
    
    print("\n💡 LƯU Ý:")
    print("   • SELL Scanner chạy --dry-run (chưa push tự động)")
    print("   • Review SELL signals trong: " + os.path.basename(SELL_SIGNALS_FILE))
    print("   • Nếu SELL OK → chạy lại không --dry-run:")
    print("     python sell_signal_scanner_v5.2.py")
    print("   • Hoặc dùng signal_reviewer.py để review & push tất cả")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
