#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Reversal Detector — MACD & RSI Divergence
================================================
Phát hiện điểm đảo chiều dựa trên DAILY data (vnstock confirmed OK).
Không dùng 1H/4H intraday vì vnstock 3.3.1 không hỗ trợ ổn định.

Tín hiệu như chart PC1 tháng 3/2026:
  - Giá tạo đỉnh cao hơn
  - MACD histogram thấp hơn (momentum yếu dần)
  - RSI thấp hơn (lực mua yếu dần)
  → Đảo chiều xuống sắp xảy ra
"""

import pandas as pd
import numpy as np
from vnstock import Vnstock
from datetime import datetime, timedelta


# ============================================================
# INDICATORS
# ============================================================

def calc_macd(close, fast=12, slow=26, signal=9):
    exp1 = close.ewm(span=fast,   adjust=False).mean()
    exp2 = close.ewm(span=slow,   adjust=False).mean()
    macd = exp1 - exp2
    sig  = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist


def calc_rsi(close, period=14):
    delta = close.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss.replace(0, 0.001)
    return 100 - (100 / (1 + rs))


def find_price_peaks(series, min_distance=3):
    """
    Tìm các đỉnh giá trong series.
    min_distance: số phiên tối thiểu giữa 2 đỉnh.
    """
    peaks = []
    vals  = series.values
    idxs  = series.index

    for i in range(1, len(vals) - 1):
        # Kiểm tra đỉnh cục bộ
        left_ok  = all(vals[i] >= vals[max(0, i-j)]
                       for j in range(1, min(min_distance+1, i+1)))
        right_ok = all(vals[i] >= vals[min(len(vals)-1, i+j)]
                       for j in range(1, min(min_distance+1, len(vals)-i)))
        if left_ok and right_ok:
            peaks.append({'pos': i, 'idx': idxs[i], 'val': vals[i]})

    return peaks


# ============================================================
# CORE: DIVERGENCE DETECTOR
# ============================================================

def detect_bearish_divergence(df, lookback=30):
    """
    Phát hiện phân kỳ âm (bearish divergence) trên daily chart.

    Nguyên lý:
      Giá tạo đỉnh mới (Higher High)
      MACD histogram tạo đỉnh thấp hơn (Lower High) → momentum suy yếu
      RSI tạo đỉnh thấp hơn (Lower High) → lực mua suy yếu
      → Smart money đang rút ra, giá sắp đảo chiều

    Returns:
        dict với điểm score và chi tiết, hoặc None nếu không có
    """
    if df is None or len(df) < lookback + 10:
        return None

    df = df.copy()

    # Chuẩn hóa giá vnstock (nghìn đồng → đồng)
    close = df['close'] if 'close' in df.columns else df['Close']
    if close.mean() < 1000:
        close = close * 1000

    # Tính indicators
    macd, macd_sig, macd_hist = calc_macd(close)
    rsi                        = calc_rsi(close)

    # Lấy lookback phiên gần nhất
    close_w     = close.tail(lookback)
    macd_hist_w = macd_hist.tail(lookback)
    rsi_w       = rsi.tail(lookback)

    # Tìm đỉnh giá
    price_peaks = find_price_peaks(close_w, min_distance=3)

    if len(price_peaks) < 2:
        return None

    # Lấy 2 đỉnh gần nhất
    p1 = price_peaks[-2]
    p2 = price_peaks[-1]

    # Điều kiện cơ bản: đỉnh giá sau cao hơn đỉnh trước
    if p2['val'] <= p1['val']:
        return None     # không phải Higher High → không có divergence

    price_diff_pct = (p2['val'] - p1['val']) / p1['val'] * 100

    # ── MACD divergence ──────────────────────────────────────
    macd_at_p1 = macd_hist_w.iloc[p1['pos']]
    macd_at_p2 = macd_hist_w.iloc[p2['pos']]

    macd_div  = macd_at_p2 < macd_at_p1      # MACD thấp hơn dù giá cao hơn
    macd_drop = (macd_at_p2 - macd_at_p1)     # âm = divergence

    # ── RSI divergence ───────────────────────────────────────
    rsi_at_p1 = rsi_w.iloc[p1['pos']]
    rsi_at_p2 = rsi_w.iloc[p2['pos']]

    rsi_div  = rsi_at_p2 < rsi_at_p1         # RSI thấp hơn dù giá cao hơn
    rsi_drop = rsi_at_p1 - rsi_at_p2          # dương = RSI giảm

    # ── Volume: volume tăng không xác nhận giá ───────────────
    vol = df['volume'] if 'volume' in df.columns else df['Volume']
    vol_w    = vol.tail(lookback)
    avg_vol  = vol_w.mean()

    vol_at_p1 = vol_w.iloc[p1['pos']]
    vol_at_p2 = vol_w.iloc[p2['pos']]

    # Volume tại đỉnh 2 cao hơn avg (volume spike) nhưng giá không tăng tương ứng
    vol_spike_p2    = vol_at_p2 >= avg_vol * 1.3
    vol_not_confirm = vol_at_p2 >= vol_at_p1   # volume cao nhưng không push được giá

    # ── Scoring ──────────────────────────────────────────────
    score   = 0
    details = []

    if macd_div:
        strength = abs(macd_drop) / (abs(macd_at_p1) + 0.0001)
        pts      = 3 if strength > 0.3 else 2
        score   += pts
        details.append(
            f"MACD div: đỉnh1={macd_at_p1:.4f} → đỉnh2={macd_at_p2:.4f} "
            f"(giảm {abs(macd_drop):.4f})"
        )

    if rsi_div:
        pts    = 3 if rsi_drop > 10 else 2 if rsi_drop > 5 else 1
        score += pts
        details.append(
            f"RSI div: đỉnh1={rsi_at_p1:.1f} → đỉnh2={rsi_at_p2:.1f} "
            f"(giảm {rsi_drop:.1f}pt)"
        )

    if vol_spike_p2 and vol_not_confirm:
        score += 1
        details.append(
            f"Vol spike tại đỉnh2: {vol_at_p2/avg_vol:.1f}x avg "
            f"nhưng giá chỉ +{price_diff_pct:.1f}%"
        )

    # Thêm điểm nếu RSI hiện tại bắt đầu rớt xuống
    current_rsi = rsi.iloc[-1]
    if current_rsi < rsi_at_p2:
        score += 1
        details.append(f"RSI hiện tại {current_rsi:.1f} < RSI đỉnh2 {rsi_at_p2:.1f} → đã quay đầu")

    if score < 3:
        return None     # không đủ tín hiệu

    # ── Urgency ──────────────────────────────────────────────
    if score >= 7:
        urgency = 'CRITICAL'
    elif score >= 5:
        urgency = 'HIGH'
    else:
        urgency = 'MEDIUM'

    # ── Khoảng cách giữa 2 đỉnh ─────────────────────────────
    peak_gap_days = p2['pos'] - p1['pos']

    return {
        'pattern':        'BEARISH_DIVERGENCE_DAILY',
        'score':          score,
        'urgency':        urgency,
        'macd_div':       macd_div,
        'rsi_div':        rsi_div,
        'vol_warning':    vol_spike_p2 and vol_not_confirm,
        'price_peak1':    round(p1['val']),
        'price_peak2':    round(p2['val']),
        'price_diff_pct': round(price_diff_pct, 1),
        'rsi_peak1':      round(rsi_at_p1, 1),
        'rsi_peak2':      round(rsi_at_p2, 1),
        'current_rsi':    round(current_rsi, 1),
        'peak_gap_days':  peak_gap_days,
        'details':        details,
        'note': (
            f"Phân kỳ âm daily — giá +{price_diff_pct:.1f}% "
            f"nhưng " +
            (f"MACD giảm" if macd_div else "") +
            (" + " if macd_div and rsi_div else "") +
            (f"RSI giảm {rsi_drop:.0f}pt" if rsi_div else "")
        ),
    }


# ============================================================
# TEST — chạy trên nhiều mã
# ============================================================

if __name__ == '__main__':

    TICKERS  = ['PC1', 'HPG', 'VCB', 'FPT', 'VHM', 'MBB', 'TCB']
    DAYS     = 120    # cần nhiều data hơn để tìm đỉnh

    print(f"\n{'='*60}")
    print(f"  BEARISH DIVERGENCE SCANNER — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*60}")

    for ticker in TICKERS:
        try:
            stock = Vnstock().stock(symbol=ticker, source='VCI')
            end   = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=DAYS)).strftime('%Y-%m-%d')
            df    = stock.quote.history(start=start, end=end)

            result = detect_bearish_divergence(df, lookback=40)

            if result:
                urg_icon = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '🔔'}.get(
                    result['urgency'], '•')
                print(f"\n  {urg_icon}  {ticker} — Score {result['score']} — {result['urgency']}")
                print(f"     Giá  : đỉnh1={result['price_peak1']:,} → "
                      f"đỉnh2={result['price_peak2']:,} "
                      f"(+{result['price_diff_pct']}%)")
                print(f"     RSI  : {result['rsi_peak1']} → {result['rsi_peak2']} "
                      f"(hiện tại {result['current_rsi']})")
                for d in result['details']:
                    print(f"     • {d}")
            else:
                print(f"  ✅  {ticker}: không có phân kỳ âm")

        except Exception as e:
            print(f"  ❌  {ticker}: {e}")

    print(f"\n{'='*60}\n")
