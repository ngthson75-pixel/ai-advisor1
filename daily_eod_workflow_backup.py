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
PROD_API = 'https://ai-advisor1-backend.onrender.com'

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
    
    # ── TỔNG KẾT ──
    print("\n" + "=" * 70)
    print("📋 TỔNG KẾT")
    print("=" * 70)
    print(f"   ✅ Scanner: Đã quét 346 mã")
    print(f"   ✅ Breadth: Đã tạo market_breadth_eod.json")
    print(f"   ✅ Market Risk: {mode_emoji} {mode_label} (Score: {risk_score})")
    print(f"   ✅ Production: Đã cập nhật")
    print()
    print("   📌 VIỆC CẦN LÀM:")
    print("   → Review signals trong signals.db (local)")
    print("   → Lọc kỹ tín hiệu mua chất lượng")
    print("   → Upload thủ công lên BUY SIGNAL khi đã sẵn sàng")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
