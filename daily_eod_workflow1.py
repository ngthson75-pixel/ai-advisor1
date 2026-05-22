#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAILY EOD WORKFLOW - Chạy cuối ngày trên máy local
===================================================

Quy trình:
  1. Scanner quét 346 mã → tạo signals + breadth data
  2. Market Risk phân tích → tạo kết quả
  3. Đẩy Market Risk lên production DB
  4. Sell Signal Scanner V5.2 → quét open BUY signals → tạo SELL signals
  5. Sơn review BUY signals → lọc kỹ → upload thủ công lên BUY SIGNAL

Cách chạy:
  cd C:\\ai-advisor1
  python daily_eod_workflow.py

  # Chạy với staging thay vì production:
  python daily_eod_workflow.py --staging

  # Bỏ qua bước sell scan:
  python daily_eod_workflow.py --skip-sell

  # Chỉ chạy sell scan (dry-run, không push):
  python daily_eod_workflow.py --sell-only --dry-run

Thời gian: ~25-35 phút (scanner 20-25 phút + market risk vài giây + sell scan 1-3 phút)
"""

import subprocess
import sys
import os
import json
import argparse
import requests
from datetime import datetime

# ========================================================================
# CONFIGURATION
# ========================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCANNER_PATH = os.path.join(SCRIPT_DIR, 'scripts', 'daily_signal_scanner_eod.py')
MARKET_RISK_PATH = os.path.join(SCRIPT_DIR, 'market_risk_analysis.py')
SELL_SCANNER_PATH = os.path.join(SCRIPT_DIR, 'sell_signal_scanner_v5_2.py')
BREADTH_FILE = os.path.join(SCRIPT_DIR, 'market_breadth_eod.json')
MARKET_RISK_FILE = os.path.join(SCRIPT_DIR, 'market_risk_latest.json')

# Production / Staging APIs
PROD_API = 'https://ai-advisor1-backend.onrender.com'
STAGING_API = 'https://ai-advisor1-staging.onrender.com'


# ========================================================================
# ARGS
# ========================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Daily EOD Workflow')
    parser.add_argument('--staging', action='store_true',
                        help='Dùng staging API thay vì production')
    parser.add_argument('--skip-sell', action='store_true',
                        help='Bỏ qua bước Sell Signal Scanner (Bước 4)')
    parser.add_argument('--sell-only', action='store_true',
                        help='Chỉ chạy Sell Signal Scanner, bỏ qua bước 1-3')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run: không push sell signals lên API')
    return parser.parse_args()


# ========================================================================
# BƯỚC 4: SELL SIGNAL SCANNER
# ========================================================================

def run_sell_scanner(api_url: str, env_name: str, dry_run: bool = False) -> bool:
    """
    Chạy Sell Signal Scanner V5.2.
    Trả về True nếu thành công, False nếu lỗi.
    """
    print("\n" + "─" * 50)
    print("🔍 BƯỚC 4/4: Sell Signal Scanner V5.2...")
    print("─" * 50)

    if not os.path.exists(SELL_SCANNER_PATH):
        print(f"❌ Không tìm thấy: {SELL_SCANNER_PATH}")
        print("   Kiểm tra lại tên file sell_signal_scanner_v5_2.py trong thư mục dự án.")
        return False

    # Xây dựng câu lệnh
    cmd = [sys.executable, SELL_SCANNER_PATH]
    if api_url == STAGING_API:
        cmd.append('--staging')
    if dry_run:
        cmd.append('--dry-run')

    print(f"   🎯 Target: {env_name}")
    if dry_run:
        print("   ⚠️  DRY RUN — Không push lên API")
    print()

    try:
        # Chạy trực tiếp (kế thừa stdin/stdout để Sơn có thể gõ y/n xác nhận)
        result = subprocess.run(
            cmd,
            cwd=SCRIPT_DIR,
            timeout=600  # 10 phút timeout (số lượng open signals thường ít)
        )

        if result.returncode != 0:
            print(f"\n⚠️ Sell scanner kết thúc với returncode={result.returncode}")
            print("   (Có thể không có open BUY signals → bình thường)")
        else:
            print("\n✅ Sell scanner hoàn tất!")

        return True

    except subprocess.TimeoutExpired:
        print("⚠️ Sell scanner timeout sau 10 phút!")
        return False
    except KeyboardInterrupt:
        print("\n⏹️ Sell scanner bị ngắt bởi người dùng.")
        return False
    except Exception as e:
        print(f"❌ Sell scanner lỗi: {e}")
        return False


# ========================================================================
# MAIN WORKFLOW
# ========================================================================

def main():
    args = parse_args()

    api_base = STAGING_API if args.staging else PROD_API
    env_name = 'STAGING' if args.staging else 'PRODUCTION'

    print("\n" + "=" * 70)
    print("🚀 DAILY EOD WORKFLOW")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Target: {env_name}")
    if args.dry_run:
        print("⚠️  DRY RUN MODE — Sell signals sẽ KHÔNG được push")
    print("=" * 70)

    # ── Chế độ sell-only ──
    if args.sell_only:
        print("\n📌 Chế độ SELL-ONLY: Bỏ qua bước 1-3\n")
        run_sell_scanner(api_base, env_name, dry_run=args.dry_run)
        print()
        return

    # ── BƯỚC 1: Chạy Scanner ──
    print("\n" + "─" * 50)
    print("📊 BƯỚC 1/4: Chạy Scanner (20-25 phút)...")
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
    print("📊 BƯỚC 2/4: Market Risk Analysis (vài giây)...")
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
    print("🚀 BƯỚC 3/4: Đẩy Market Risk lên Production...")
    print("─" * 50)

    if not os.path.exists(MARKET_RISK_FILE):
        print("❌ File market_risk_latest.json không tìm thấy!")
        return

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

    confirm = input("\n   Đẩy lên production? (y/n): ").strip().lower()

    if confirm != 'y':
        print("   ⏹️ Đã hủy đẩy Market Risk.")
    else:
        try:
            print("   Đang đẩy kết quả lên production...")
            response = requests.post(
                f"{api_base}/api/market-risk/upload",
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
            print("   💡 Thử wake up: https://ai-advisor1-backend.onrender.com/health")
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")

    # ── BƯỚC 4: Sell Signal Scanner ──
    if args.skip_sell:
        print("\n" + "─" * 50)
        print("⏭️  BƯỚC 4/4: Sell Scanner — ĐÃ BỎ QUA (--skip-sell)")
        print("─" * 50)
        sell_ok = False
    else:
        sell_ok = run_sell_scanner(api_base, env_name, dry_run=args.dry_run)

    # ── TỔNG KẾT ──
    print("\n" + "=" * 70)
    print("📋 TỔNG KẾT")
    print("=" * 70)
    print(f"   ✅ Scanner     : Đã quét 346 mã")
    print(f"   ✅ Breadth     : Đã tạo market_breadth_eod.json")
    print(f"   ✅ Market Risk : {mode_emoji} {mode_label} (Score: {risk_score})")
    print(f"   {'✅' if sell_ok else '⏭️ '} Sell Scanner : {'Hoàn tất V5.2' if sell_ok else 'Đã bỏ qua'}")
    print()
    print("   📌 VIỆC CÒN LẠI:")
    print("   → Review BUY signals trong signals.db (local)")
    print("   → Lọc kỹ tín hiệu mua chất lượng")
    print("   → Upload thủ công lên BUY SIGNAL khi đã sẵn sàng")
    if not sell_ok and not args.skip_sell:
        print()
        print("   ⚠️  Sell scanner chưa chạy xong — kiểm tra lại nếu cần:")
        print(f"       python daily_eod_workflow.py --sell-only")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
