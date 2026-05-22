#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACCUMULATION SCANNER - Quét tích lũy trung hạn
================================================

Tiêu chí phát hiện tích lũy:
  1. RANGE HẸP   : Biên độ giá (High-Low) trong N ngày < ngưỡng (ví dụ 15%)
  2. VOL THẤP    : Volume trung bình N ngày < vol trung bình dài hạn × threshold
  3. THỜI GIAN   : Nền tích lũy kéo dài ≥ 60 phiên (~3 tháng)
  4. TREND TRƯỚC : Có uptrend trước tích lũy (tránh cổ phiếu đang giảm không đáy)
  5. GIÁ ỔN ĐỊNH : Độ lệch chuẩn giá đóng cửa thấp (narrow price band)

Cách dùng:
  cd C:\\ai-advisor1
  python accumulation_scanner.py

  # Tùy chỉnh:
  python accumulation_scanner.py --days 90      # cửa sổ tích lũy 90 phiên
  python accumulation_scanner.py --range 12     # range hẹp < 12%
  python accumulation_scanner.py --vol 0.7      # vol < 70% trung bình dài hạn
  python accumulation_scanner.py --top 20       # chỉ hiện top 20
  python accumulation_scanner.py --save         # lưu kết quả ra file CSV
"""

import os
import sys
import time
import argparse
import json
import csv
from datetime import datetime, timedelta

# ── Cùng thư mục với daily_signal_scanner_eod.py ──────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'scripts'))

try:
    from vnstock import Quote
except ImportError:
    try:
        from vnstock3 import Quote
    except ImportError:
        print("❌ Không tìm thấy vnstock. Cài đặt: pip install vnstock")
        sys.exit(1)


# ========================================================================
# WATCHLIST (copy từ daily_signal_scanner_eod.py)
# ========================================================================

WATCHLIST_172 = [
    # TIER 1: VN30 + Blue Chips
    'VCB', 'BID', 'CTG', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB',
    'STB', 'MSN', 'FPT', 'SSI', 'GAS', 'PLX', 'MWG', 'VJC', 'HDB', 'ACB',
    'VRE', 'BCM', 'POW', 'SAB', 'SHB', 'LPB', 'VIB', 'EIB', 'BVH', 'GVR',
    'TPB', 'NVL', 'KDH', 'DGC', 'REE', 'VCI', 'HVN', 'DIG', 'GEX', 'VIX',
    'BSR', 'GMD', 'PNJ',
    # TIER 2: Large-Mid Cap HOSE
    'DPM', 'KBC', 'DXG', 'VPL', 'MSB', 'OCB', 'TCX',
    'HSG', 'DCM', 'HCM', 'VND', 'PC1', 'DGW', 'HDG', 'PVD', 'PVT', 'VTP',
    'SCS', 'TCH', 'NLG', 'CII', 'PDR', 'IDC', 'ANV', 'HAH', 'DBC', 'MCH',
    'CTD', 'HT1', 'VSC', 'BWE', 'PVS', 'VHC', 'SSB', 'FRT', 'ELC', 'BMI',
    'BSI', 'TV2', 'DPG', 'LCG', 'BAF',
    # TIER 3: Mid Cap HOSE
    'TNG', 'KSB', 'MSH', 'SBT', 'VCG', 'CTR', 'SZC', 'PHR', 'GEG', 'PTB',
    'HAX', 'FMC', 'CSV', 'TCM', 'CMG', 'PAN', 'SGN', 'NTL', 'GIL', 'VFC',
    'IDI', 'AAA', 'TLH', 'HBC', 'VPG', 'CRE', 'CSM', 'ASM', 'HHS', 'PDC',
    'PAC', 'TAL', 'KOS', 'SIP', 'ORS', 'CMX', 'NBB', 'SMC', 'DCL', 'QCG',
    'SJS', 'NAF', 'HAG', 'NHA', 'EVF', 'VHG', 'HAP', 'ASG',
    # TIER 4: HNX
    'SHS', 'MBS', 'VFS', 'CEO', 'NVB', 'VCS', 'HUT', 'NDN', 'PLC', 'EVS',
    'PSI', 'VC3', 'BVS', 'BAB', 'TIG', 'APS', 'IPA', 'DXP', 'TVS', 'LIG',
    'VHE', 'VC7', 'DTT', 'KSV', 'HLD', 'OCH', 'PVI', 'MIG', 'PGB', 'DHT',
    'API', 'NRC', 'MBG', 'SJE', 'INN', 'NAG', 'SD9', 'AMV', 'IDJ',
]


# ========================================================================
# HELPERS
# ========================================================================

def get_last_trading_day():
    d = datetime.now()
    # Nếu sau 15h thì dùng hôm nay, trước thì dùng hôm qua
    if d.hour < 15:
        d -= timedelta(days=1)
    while d.weekday() >= 5:  # bỏ qua T7, CN
        d -= timedelta(days=1)
    return d.strftime('%Y-%m-%d')


def get_stock_data(ticker: str, days: int = 350) -> 'pd.DataFrame | None':
    """Lấy dữ liệu OHLCV từ vnstock VCI source."""
    try:
        end_date   = get_last_trading_day()
        start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=days * 2)).strftime('%Y-%m-%d')

        quote = Quote(symbol=ticker, source='VCI')
        df    = quote.history(start=start_date, end=end_date)

        if df is None or len(df) == 0:
            return None

        # Normalize columns
        df.columns = [c.lower() for c in df.columns]
        rename = {'open': 'open', 'high': 'high', 'low': 'low',
                  'close': 'close', 'volume': 'volume'}
        df = df.rename(columns=rename)

        # vnstock trả về giá × 1000 → nhân lại
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns and df[col].median() < 1000:
                df[col] = df[col] * 1000

        df = df.sort_values('time').reset_index(drop=True)
        return df

    except Exception as e:
        return None


def score_label(score: float) -> str:
    if score >= 80:
        return '⭐⭐⭐ MẠNH'
    elif score >= 65:
        return '⭐⭐  KHÁ'
    elif score >= 50:
        return '⭐   VỪA'
    else:
        return '·    YẾU'


# ========================================================================
# CORE: ACCUMULATION DETECTOR
# ========================================================================

def check_accumulation(df, ticker: str, accum_days: int, range_pct: float, vol_ratio: float):
    """
    Phân tích tích lũy trung hạn.

    Trả về dict kết quả nếu thỏa điều kiện, None nếu không.

    Thuật toán:
      - BASE_WINDOW   = accum_days (cửa sổ tích lũy, mặc định 90 phiên)
      - REF_WINDOW    = 250 phiên (tham chiếu dài hạn cho volume)
      - PRIOR_WINDOW  = 60 phiên trước base (kiểm tra uptrend trước tích lũy)

    Tiêu chí:
      1. Đủ dữ liệu    : ≥ BASE_WINDOW + PRIOR_WINDOW phiên
      2. Range hẹp     : (max_high - min_low) / min_low ≤ range_pct %
      3. Vol thấp      : avg_vol_base ≤ avg_vol_ref × vol_ratio
      4. Giá ổn định   : std(close) / mean(close) ≤ 8% (coefficient of variation)
      5. Trend trước   : close trước tích lũy > close đầu tích lũy (đã có đà tăng)
      6. Không downtrend hiện tại: close[-1] > close đáy tích lũy × 0.95
    """
    import statistics

    MIN_ROWS     = accum_days + 60
    REF_WINDOW   = 250
    PRIOR_WINDOW = 60

    if len(df) < MIN_ROWS:
        return None

    # Lấy các cửa sổ
    base  = df.tail(accum_days)
    prior = df.iloc[-(accum_days + PRIOR_WINDOW):-(accum_days)]
    ref   = df.tail(min(REF_WINDOW, len(df)))

    closes  = list(base['close'])
    highs   = list(base['high'])
    lows    = list(base['low'])
    volumes = list(base['volume'])
    ref_vols = list(ref['volume'])

    # ── Tiêu chí 1: Range hẹp ─────────────────────────────────────────
    max_high = max(highs)
    min_low  = min(lows)
    if min_low <= 0:
        return None
    actual_range_pct = (max_high - min_low) / min_low * 100
    if actual_range_pct > range_pct:
        return None

    # ── Tiêu chí 2: Volume thấp ───────────────────────────────────────
    avg_vol_base = sum(volumes) / len(volumes)
    avg_vol_ref  = sum(ref_vols) / len(ref_vols)
    if avg_vol_ref <= 0:
        return None
    actual_vol_ratio = avg_vol_base / avg_vol_ref
    if actual_vol_ratio > vol_ratio:
        return None

    # ── Tiêu chí 3: Giá ổn định (CV thấp) ────────────────────────────
    mean_close = sum(closes) / len(closes)
    std_close  = statistics.stdev(closes) if len(closes) > 1 else 0
    cv = std_close / mean_close if mean_close > 0 else 1
    if cv > 0.08:
        return None

    # ── Tiêu chí 4: Có uptrend trước tích lũy ────────────────────────
    if len(prior) >= 20:
        prior_close_start = float(prior['close'].iloc[0])
        prior_close_end   = float(prior['close'].iloc[-1])
        prior_gain        = (prior_close_end - prior_close_start) / prior_close_start * 100
        # Nếu trước đó đang downtrend mạnh (giảm > 20%) thì bỏ qua
        if prior_gain < -20:
            return None
    else:
        prior_gain = 0

    # ── Tiêu chí 5: Giá hiện tại không phá đáy tích lũy ─────────────
    current_price = float(df['close'].iloc[-1])
    if current_price < min_low * 0.95:
        return None

    # ── Bonus: Đang ở cuối nền (giá gần đỉnh tích lũy → sắp bứt phá) ─
    range_position = (current_price - min_low) / (max_high - min_low) if (max_high - min_low) > 0 else 0.5

    # ── Tính điểm tích lũy (0-100) ───────────────────────────────────
    # Range càng hẹp → điểm càng cao
    range_score = max(0, 40 - actual_range_pct * 2)          # max 40đ khi range 0%
    # Vol càng thấp so với avg → điểm càng cao
    vol_score   = max(0, (1 - actual_vol_ratio) * 30)        # max 30đ khi vol = 0
    # CV càng thấp → điểm cao
    cv_score    = max(0, (0.08 - cv) / 0.08 * 20)           # max 20đ khi cv = 0
    # Range position gần đỉnh → điểm cao (sắp bứt phá)
    pos_score   = range_position * 10                         # max 10đ

    total_score = range_score + vol_score + cv_score + pos_score
    total_score = min(100, round(total_score))

    return {
        'ticker':         ticker,
        'score':          total_score,
        'current_price':  current_price,
        'range_pct':      round(actual_range_pct, 1),
        'vol_ratio':      round(actual_vol_ratio, 2),
        'cv_pct':         round(cv * 100, 1),
        'range_position': round(range_position * 100),   # % trong nền (100=đỉnh)
        'high_base':      round(max_high),
        'low_base':       round(min_low),
        'avg_vol_base':   round(avg_vol_base / 1000),    # nghìn cp
        'avg_vol_ref':    round(avg_vol_ref / 1000),     # nghìn cp
        'prior_gain':     round(prior_gain, 1),
        'accum_days':     accum_days,
    }


# ========================================================================
# MAIN SCANNER
# ========================================================================

def main():
    parser = argparse.ArgumentParser(description='Accumulation Scanner — Quét tích lũy trung hạn')
    parser.add_argument('--days',  type=int,   default=90,   help='Cửa sổ tích lũy (phiên, mặc định 90 ~ 4.5 tháng)')
    parser.add_argument('--range', type=float, dest='range_pct', default=15.0,
                        help='Range hẹp tối đa %% (mặc định 15)')
    parser.add_argument('--vol',   type=float, dest='vol_ratio',  default=0.75,
                        help='Vol/AvgVol tối đa (mặc định 0.75 = 75%% avg dài hạn)')
    parser.add_argument('--top',   type=int,   default=30,   help='Số mã hiển thị top (mặc định 30)')
    parser.add_argument('--delay', type=float, default=2.5,  help='Delay giữa các mã (giây)')
    parser.add_argument('--save',  action='store_true',       help='Lưu kết quả ra file CSV + JSON')
    parser.add_argument('--tickers', nargs='+',               help='Quét danh sách mã cụ thể (VD: VCB HPG FPT)')
    args = parser.parse_args()

    tickers = args.tickers if args.tickers else WATCHLIST_172

    print("\n" + "=" * 70)
    print("🔍 ACCUMULATION SCANNER — Quét Tích Lũy Trung Hạn")
    print("=" * 70)
    print(f"📅 Ngày quét   : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📊 Số mã quét  : {len(tickers)}")
    print(f"📆 Cửa sổ TL   : {args.days} phiên (~{args.days // 20} tháng)")
    print(f"📏 Range tối đa: {args.range_pct}%")
    print(f"📉 Vol tối đa  : {args.vol_ratio * 100:.0f}% avg dài hạn")
    print("=" * 70)

    results    = []
    failed     = []
    total      = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        print(f"  [{i:3d}/{total}] {ticker:<6}", end='', flush=True)

        df = get_stock_data(ticker, days=args.days + 100)

        if df is None or len(df) < args.days + 40:
            print(" ✗ no data")
            failed.append(ticker)
            time.sleep(args.delay)
            continue

        result = check_accumulation(
            df, ticker,
            accum_days  = args.days,
            range_pct   = args.range_pct,
            vol_ratio   = args.vol_ratio,
        )

        if result:
            score = result['score']
            label = score_label(score)
            print(f" ✓ TL {result['accum_days']}ph | Range:{result['range_pct']:4.1f}% | "
                  f"Vol:{result['vol_ratio']:.2f}x | Pos:{result['range_position']:3d}% | {label} ({score})")
            results.append(result)
        else:
            print(f" – không tích lũy")

        time.sleep(args.delay)

    # ── Sắp xếp theo điểm ────────────────────────────────────────────
    results.sort(key=lambda x: x['score'], reverse=True)
    top_results = results[:args.top]

    # ── In bảng kết quả ───────────────────────────────────────────────
    print("\n\n" + "=" * 90)
    print(f"📋 KẾT QUẢ TÍCH LŨY TRUNG HẠN — Top {min(args.top, len(results))}/{len(results)} mã")
    print(f"   Cửa sổ: {args.days} phiên | Range ≤ {args.range_pct}% | Vol ≤ {args.vol_ratio*100:.0f}% avg")
    print("=" * 90)

    if not top_results:
        print("\n  Không tìm thấy mã nào thỏa tiêu chí tích lũy.")
        print(f"  Gợi ý: thử nới lỏng --range {args.range_pct + 3} hoặc --vol {args.vol_ratio + 0.1:.1f}")
    else:
        print(f"\n{'#':>3} {'Ticker':<7} {'Giá':>8} {'Range':>6} {'Vol/Avg':>8} {'CV':>5} "
              f"{'Vị trí':>7} {'Đáy':>9} {'Đỉnh':>9} {'Score':>6}  Nhận xét")
        print("-" * 90)

        for rank, r in enumerate(top_results, 1):
            pos_bar = '▓' * (r['range_position'] // 10) + '░' * (10 - r['range_position'] // 10)
            label   = score_label(r['score'])
            print(
                f"{rank:>3} {r['ticker']:<7} {r['current_price']:>8,.0f} "
                f"{r['range_pct']:>5.1f}% {r['vol_ratio']:>7.2f}x {r['cv_pct']:>4.1f}% "
                f"  {r['range_position']:>3d}% [{pos_bar}] "
                f"{r['low_base']:>9,.0f} {r['high_base']:>9,.0f} "
                f"{r['score']:>5}  {label}"
            )

        print()
        print("  Vị trí trong nền: 0%=đáy, 100%=đỉnh → gần 100% có thể sắp bứt phá")
        print("  Vol/Avg: tỷ lệ vol tích lũy so với avg 250 phiên (< 1 = vol thấp hơn bình thường)")

    # ── Phân nhóm ─────────────────────────────────────────────────────
    if results:
        strong  = [r for r in results if r['score'] >= 80]
        good    = [r for r in results if 65 <= r['score'] < 80]
        near_breakout = [r for r in results if r['range_position'] >= 70]

        print("\n" + "─" * 70)
        print("📌 PHÂN NHÓM:")
        if strong:
            print(f"   ⭐⭐⭐ Tích lũy MẠNH (≥80đ) : {', '.join(r['ticker'] for r in strong)}")
        if good:
            print(f"   ⭐⭐  Tích lũy KHÁ  (65-79đ): {', '.join(r['ticker'] for r in good)}")
        if near_breakout:
            print(f"   🚀 Gần bứt phá (vị trí ≥70%): {', '.join(r['ticker'] for r in near_breakout)}")

    # ── Lưu file ──────────────────────────────────────────────────────
    if args.save and results:
        date_str  = datetime.now().strftime('%Y%m%d_%H%M')
        csv_path  = os.path.join(SCRIPT_DIR, f'accumulation_{date_str}.csv')
        json_path = os.path.join(SCRIPT_DIR, f'accumulation_{date_str}.json')

        # CSV
        fieldnames = ['ticker', 'score', 'current_price', 'range_pct', 'vol_ratio',
                      'cv_pct', 'range_position', 'low_base', 'high_base',
                      'avg_vol_base', 'avg_vol_ref', 'prior_gain', 'accum_days']
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        # JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'date':       datetime.now().strftime('%Y-%m-%d %H:%M'),
                'params':     {'days': args.days, 'range_pct': args.range_pct, 'vol_ratio': args.vol_ratio},
                'count':      len(results),
                'results':    results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n  💾 Đã lưu: {csv_path}")
        print(f"  💾 Đã lưu: {json_path}")

    # ── Tổng kết ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("📊 TỔNG KẾT")
    print("=" * 70)
    print(f"   Đã quét   : {total} mã")
    print(f"   Thỏa TL   : {len(results)} mã")
    print(f"   Không data : {len(failed)} mã")
    if failed:
        print(f"   Lỗi       : {', '.join(failed[:10])}" +
              (f" +{len(failed)-10}" if len(failed) > 10 else ""))
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
