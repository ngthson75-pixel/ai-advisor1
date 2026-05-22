#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volume Climax at Resistance Detector
=====================================
Phát hiện pattern phân phối tổ chức:
  - Giá tiếp cận vùng đỉnh cũ
  - Volume lớn bất thường nhiều phiên liên tiếp
  - Giá không tăng được (distribution)
  - MACD phân kỳ âm xác nhận

Dựa trên chart PC1 tháng 3/2026 làm ví dụ chuẩn.
"""

import pandas as pd
import numpy as np


# ============================================================
# HELPER INDICATORS
# ============================================================

def calc_macd(df, fast=12, slow=26, signal=9):
    close = df['close'] if 'close' in df.columns else df['Close']
    exp1  = close.ewm(span=fast,   adjust=False).mean()
    exp2  = close.ewm(span=slow,   adjust=False).mean()
    macd  = exp1 - exp2
    sig   = macd.ewm(span=signal, adjust=False).mean()
    hist  = macd - sig
    return macd, sig, hist


def find_resistance_levels(df, lookback=60, cluster_pct=0.03):
    """
    Tìm vùng kháng cự từ đỉnh cũ trong lookback phiên.
    Cluster các đỉnh nằm trong ±cluster_pct% lại thành 1 vùng.
    """
    close = df['close'] if 'close' in df.columns else df['Close']
    high  = df['high']  if 'high'  in df.columns else df['High']

    recent = df.tail(lookback)
    highs  = high.tail(lookback)

    # Tìm local highs (đỉnh của nến)
    peaks = []
    for i in range(1, len(recent) - 1):
        if (highs.iloc[i] >= highs.iloc[i-1] and
                highs.iloc[i] >= highs.iloc[i+1]):
            peaks.append(highs.iloc[i])

    if not peaks:
        return []

    # Cluster các đỉnh gần nhau
    peaks_sorted = sorted(peaks, reverse=True)
    resistance_zones = []
    used = set()

    for i, p in enumerate(peaks_sorted):
        if i in used:
            continue
        cluster = [p]
        for j, q in enumerate(peaks_sorted):
            if j != i and j not in used:
                if abs(p - q) / p < cluster_pct:
                    cluster.append(q)
                    used.add(j)
        used.add(i)
        resistance_zones.append(np.mean(cluster))

    # Trả về top 3 vùng kháng cự mạnh nhất (cao nhất)
    return sorted(resistance_zones, reverse=True)[:3]


# ============================================================
# CORE DETECTOR
# ============================================================

def detect_volume_climax_at_resistance(df, entry_price=None):
    """
    Phát hiện pattern: Volume Climax at Resistance (Buying Climax / Distribution)

    Điều kiện:
      1. Giá đang ở gần vùng kháng cự lịch sử (±3%)
      2. Có ≥3 phiên volume cao bất thường (≥1.5x avg) trong 10 phiên
      3. Trong các phiên volume cao đó, giá không tăng được
         (close phiên sau <= close đỉnh của cụm)
      4. MACD phân kỳ âm: giá tạo đỉnh cao hơn nhưng MACD thấp hơn

    Returns:
        dict | None
    """
    if df is None or len(df) < 40:
        return None

    # Chuẩn hóa giá (vnstock trả về nghìn đồng)
    df = df.copy()
    close_raw = df['close'] if 'close' in df.columns else df['Close']
    if close_raw.mean() < 1000:
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                df[col] = df[col] * 1000

    close  = df['close']
    high   = df['high']
    low    = df['low']
    volume = df['volume']

    current_price = close.iloc[-1]
    avg_vol_20    = volume.rolling(20).mean().iloc[-1]

    # ── Điều kiện 1: Giá gần kháng cự ──────────────────────
    resistance_zones = find_resistance_levels(df, lookback=60)

    near_resistance  = False
    resistance_level = None
    resistance_pct   = None

    for zone in resistance_zones:
        dist_pct = (current_price - zone) / zone * 100
        # Gần kháng cự = trong vòng -5% đến +1% (dưới hoặc vừa chạm)
        if -5.0 <= dist_pct <= 1.0:
            near_resistance  = True
            resistance_level = zone
            resistance_pct   = dist_pct
            break

    # ── Điều kiện 2 & 3: Volume cao + giá không tăng ────────
    recent_10 = df.tail(10).copy()
    vol_10    = volume.tail(10)

    # Đếm phiên volume cao (≥ 1.5x avg)
    high_vol_sessions = vol_10[vol_10 >= avg_vol_20 * 1.5]
    high_vol_count    = len(high_vol_sessions)

    # Kiểm tra giá có tăng trong các phiên volume cao không
    price_stalled = False
    stall_detail  = ""
    if high_vol_count >= 3:
        # Giá cao nhất trong cụm volume cao
        peak_in_cluster = recent_10.loc[
            high_vol_sessions.index, 'close'
        ].max()
        # Giá hiện tại không vượt đỉnh cụm đó
        price_advance   = (current_price - peak_in_cluster) / peak_in_cluster * 100
        price_stalled   = price_advance <= 1.0   # không tăng thêm được >1%
        stall_detail    = (
            f"{high_vol_count} phiên vol ≥1.5x avg, "
            f"giá đỉnh cụm {peak_in_cluster:,.0f}, "
            f"hiện tại {price_advance:+.1f}%"
        )

    # ── Điều kiện 4: MACD phân kỳ âm ────────────────────────
    macd, sig, hist = calc_macd(df)

    # So sánh đỉnh giá gần đây vs đỉnh cũ hơn (lookback 20 phiên)
    recent_20      = df.tail(20)
    macd_recent_20 = macd.tail(20)
    close_20       = close.tail(20)

    # Tìm 2 đỉnh giá gần nhất trong 20 phiên
    price_peaks = []
    for i in range(1, len(recent_20) - 1):
        if (close_20.iloc[i] >= close_20.iloc[i-1] and
                close_20.iloc[i] >= close_20.iloc[i+1]):
            price_peaks.append({
                'idx':   i,
                'price': close_20.iloc[i],
                'macd':  macd_recent_20.iloc[i]
            })

    macd_divergence      = False
    divergence_detail    = ""
    if len(price_peaks) >= 2:
        p1, p2        = price_peaks[-2], price_peaks[-1]
        price_higher  = p2['price'] > p1['price']
        macd_lower    = p2['macd']  < p1['macd']
        if price_higher and macd_lower:
            macd_divergence   = True
            divergence_detail = (
                f"Giá {p1['price']:,.0f}→{p2['price']:,.0f} "
                f"(+{(p2['price']/p1['price']-1)*100:.1f}%), "
                f"MACD {p1['macd']:.4f}→{p2['macd']:.4f} (giảm)"
            )

    # ── Tính điểm tổng hợp ──────────────────────────────────
    score = 0
    signals_found = []

    if near_resistance:
        score += 2
        signals_found.append(
            f"Kháng cự {resistance_level:,.0f} "
            f"({resistance_pct:+.1f}%)"
        )

    if high_vol_count >= 3 and price_stalled:
        score += 3    # điều kiện cốt lõi — nặng nhất
        signals_found.append(stall_detail)
    elif high_vol_count >= 2 and price_stalled:
        score += 1
        signals_found.append(f"2 phiên vol cao, giá không tăng")

    if macd_divergence:
        score += 2
        signals_found.append(f"MACD phân kỳ âm: {divergence_detail}")

    # ── Kết quả ─────────────────────────────────────────────
    if score < 3:
        return None   # chưa đủ tín hiệu

    urgency = 'CRITICAL' if score >= 6 else 'HIGH' if score >= 4 else 'MEDIUM'

    return {
        'pattern':          'VOLUME_CLIMAX_AT_RESISTANCE',
        'score':            score,
        'max_score':        7,
        'urgency':          urgency,
        'near_resistance':  near_resistance,
        'resistance_level': resistance_level,
        'high_vol_count':   high_vol_count,
        'price_stalled':    price_stalled,
        'macd_divergence':  macd_divergence,
        'signals':          signals_found,
        'note': (
            f"Volume Climax tại kháng cự — "
            f"{', '.join(signals_found[:2])}"
        ),
        'action':           'SELL',
        'exit_pct':         100 if score >= 6 else 50,
    }


# ============================================================
# TÍCH HỢP VÀO SELL SCANNER
# Thêm đoạn này vào scan_for_sell_signals() sau Priority 1b
# ============================================================

def priority_1c_volume_climax(
        ticker, signal_code, entry_price, stop_loss,
        take_profit, position_pct, pnl_pct,
        current_price, df_daily):
    """
    PRIORITY 1c: Volume Climax at Resistance
    Gọi sau Priority 1b (Trailing Profit Protection)
    Chỉ kích hoạt khi đang có lãi (pnl_pct > 0)
    """
    if pnl_pct <= 0:
        # Đang lỗ → không dùng pattern này, để Stop Loss xử lý
        return None

    result = detect_volume_climax_at_resistance(df_daily, entry_price)

    if result is None:
        return None

    return {
        'ticker':            ticker,
        'signal_code':       signal_code,
        'exit_reason':       'VOLUME_CLIMAX_RESISTANCE',
        'entry_price':       entry_price,
        'exit_price':        current_price,
        'stop_loss':         stop_loss,
        'take_profit':       take_profit,
        'profit_loss_pct':   pnl_pct,
        'exit_quantity_pct': result['exit_pct'],
        'position_pct':      position_pct,
        'note':              result['note'],
        'urgency':           result['urgency'],
        'signal_details':    result,
    }


# ============================================================
# TEST STANDALONE
# ============================================================

if __name__ == '__main__':
    from vnstock import Vnstock
    from datetime import datetime, timedelta

    TICKERS = ['PC1', 'HPG', 'VCB', 'FPT']

    for ticker in TICKERS:
        print(f"\n{'='*55}")
        print(f"  {ticker}")
        print('='*55)
        try:
            stock = Vnstock().stock(symbol=ticker, source='VCI')
            end   = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            df    = stock.quote.history(start=start, end=end)

            result = detect_volume_climax_at_resistance(df)

            if result:
                print(f"  ⚠️  PATTERN DETECTED — Score {result['score']}/{result['max_score']}")
                print(f"  Urgency : {result['urgency']}")
                print(f"  Exit    : {result['exit_pct']}%")
                for s in result['signals']:
                    print(f"  • {s}")
            else:
                print(f"  ✅  Không có pattern phân phối")

        except Exception as e:
            print(f"  ❌  {e}")
