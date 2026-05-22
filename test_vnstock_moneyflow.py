#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST VNSTOCK — Money Flow Data Availability
===========================================
Chạy script này trên máy local để kiểm tra:
1. Daily OHLCV có những cột gì
2. Foreign flow (buy/sell) có không
3. Intraday data trả về gì
4. Tính thử CMF, MFI, OBV và xem kết quả

Chạy: python test_vnstock_moneyflow.py
"""

from vnstock import Vnstock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

TICKER   = 'HPG'          # đổi mã để test
DAYS     = 60
SEP      = "=" * 60

# ============================================================
# HELPER: in kết quả rõ ràng
# ============================================================

def section(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

def ok(msg):   print(f"  ✅  {msg}")
def warn(msg): print(f"  ⚠️  {msg}")
def err(msg):  print(f"  ❌  {msg}")


# ============================================================
# 1. DAILY HISTORY — xem đủ cột gì
# ============================================================

section(f"1. DAILY HISTORY — {TICKER}")

try:
    stock  = Vnstock().stock(symbol=TICKER, source='VCI')
    end    = datetime.now().strftime('%Y-%m-%d')
    start  = (datetime.now() - timedelta(days=DAYS)).strftime('%Y-%m-%d')
    df     = stock.quote.history(start=start, end=end)

    print(f"\n  Số hàng: {len(df)}")
    print(f"  Cột có: {list(df.columns)}")
    print(f"\n  5 hàng gần nhất:")
    print(df.tail(5).to_string(max_cols=10))

    # Kiểm tra foreign flow columns
    foreign_cols = [c for c in df.columns
                    if 'foreign' in c.lower() or 'nn' in c.lower()]
    if foreign_cols:
        ok(f"Có foreign flow columns: {foreign_cols}")
        print(f"\n  Foreign data (5 hàng):")
        print(df[foreign_cols].tail(5).to_string())
    else:
        warn("Không có foreign flow trong daily history")

    # Kiểm tra volume columns
    vol_cols = [c for c in df.columns if 'vol' in c.lower()]
    print(f"\n  Volume columns: {vol_cols}")

except Exception as e:
    err(f"Daily history failed: {e}")
    df = None


# ============================================================
# 2. CMF — Chaikin Money Flow (tính từ OHLCV)
# ============================================================

section("2. CMF — Chaikin Money Flow")

def calc_cmf(df, period=20):
    """
    Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low)
    Money Flow Volume     = MFM × Volume
    CMF                   = sum(MFV, period) / sum(Volume, period)

    > 0  : dòng tiền vào (bullish)
    < 0  : dòng tiền ra  (bearish)
    """
    high  = df['high']  if 'high'  in df.columns else df['High']
    low   = df['low']   if 'low'   in df.columns else df['Low']
    close = df['close'] if 'close' in df.columns else df['Close']
    vol   = df['volume']if 'volume'in df.columns else df['Volume']

    mfm = ((close - low) - (high - close)) / (high - low).replace(0, 0.001)
    mfv = mfm * vol
    return mfv.rolling(period).sum() / vol.rolling(period).sum()

if df is not None:
    try:
        # vnstock trả giá dạng nghìn đồng → nhân 1000 nếu cần
        df_calc = df.copy()
        if df_calc['close'].mean() < 1000:
            for col in ['open','high','low','close']:
                if col in df_calc.columns:
                    df_calc[col] = df_calc[col] * 1000

        cmf = calc_cmf(df_calc)
        latest_cmf = cmf.iloc[-1]

        print(f"\n  CMF (20 ngày) hiện tại : {latest_cmf:.4f}")
        print(f"  CMF 5 ngày gần nhất   :")
        for i, (idx, val) in enumerate(cmf.tail(5).items()):
            sign = "▲" if val > 0 else "▼"
            print(f"    {idx}  {sign}  {val:.4f}")

        if latest_cmf > 0.05:
            ok("CMF dương mạnh → dòng tiền đang vào")
        elif latest_cmf > 0:
            warn("CMF dương nhẹ → tích lũy yếu")
        elif latest_cmf > -0.05:
            warn("CMF âm nhẹ → phân phối nhẹ")
        else:
            err("CMF âm mạnh → dòng tiền đang thoát")

        # Phát hiện CMF cross xuống 0 (tín hiệu bán)
        prev_cmf = cmf.iloc[-2]
        if prev_cmf >= 0 and latest_cmf < 0:
            err("⚡ CMF vừa cắt xuống 0 → SELL SIGNAL")
        elif prev_cmf < 0 and latest_cmf >= 0:
            ok("⚡ CMF vừa cắt lên 0 → BUY SIGNAL")

    except Exception as e:
        err(f"CMF calculation failed: {e}")


# ============================================================
# 3. MFI — Money Flow Index
# ============================================================

section("3. MFI — Money Flow Index")

def calc_mfi(df, period=14):
    """
    Typical Price (TP) = (High + Low + Close) / 3
    Raw Money Flow     = TP × Volume
    MFI = 100 - [100 / (1 + Positive MF / Negative MF)]

    > 80 : overbought (có thể đảo chiều xuống)
    < 20 : oversold   (có thể đảo chiều lên)
    Phân kỳ âm với giá = tín hiệu bán sớm
    """
    high  = df['high']  if 'high'  in df.columns else df['High']
    low   = df['low']   if 'low'   in df.columns else df['Low']
    close = df['close'] if 'close' in df.columns else df['Close']
    vol   = df['volume']if 'volume'in df.columns else df['Volume']

    tp  = (high + low + close) / 3
    mf  = tp * vol
    pos = mf.where(tp > tp.shift(1), 0).rolling(period).sum()
    neg = mf.where(tp <= tp.shift(1), 0).rolling(period).sum()
    return 100 - (100 / (1 + pos / neg.replace(0, 0.001)))

if df is not None:
    try:
        df_calc = df.copy()
        if df_calc['close'].mean() < 1000:
            for col in ['open','high','low','close']:
                if col in df_calc.columns:
                    df_calc[col] = df_calc[col] * 1000

        mfi    = calc_mfi(df_calc)
        latest = mfi.iloc[-1]

        print(f"\n  MFI (14 ngày) hiện tại: {latest:.1f}")
        print(f"  MFI 5 ngày gần nhất   :")
        for idx, val in mfi.tail(5).items():
            bar = "█" * int(val / 10)
            print(f"    {idx}  {val:5.1f}  {bar}")

        if latest > 80:
            err(f"MFI = {latest:.0f} → OVERBOUGHT, cảnh báo đảo chiều")
        elif latest > 60:
            warn(f"MFI = {latest:.0f} → Neutral-high")
        elif latest > 40:
            ok(f"MFI = {latest:.0f} → Neutral")
        else:
            warn(f"MFI = {latest:.0f} → Oversold, có thể bounce")

        # Phân kỳ âm: giá tăng 5 ngày nhưng MFI giảm
        price_5d_ago = df_calc['close'].iloc[-5]
        price_now    = df_calc['close'].iloc[-1]
        mfi_5d_ago   = mfi.iloc[-5]
        mfi_now      = mfi.iloc[-1]

        price_up = price_now > price_5d_ago
        mfi_down = mfi_now   < mfi_5d_ago

        if price_up and mfi_down:
            err(f"⚡ Phân kỳ âm MFI: giá +{(price_now/price_5d_ago-1)*100:.1f}% "
                f"nhưng MFI {mfi_5d_ago:.0f} → {mfi_now:.0f} (giảm)")
        elif not price_up and not mfi_down:
            warn("Phân kỳ dương: giá giảm nhưng MFI tăng → tiền vẫn vào")
        else:
            ok("Không có phân kỳ — giá và MFI di chuyển cùng chiều")

    except Exception as e:
        err(f"MFI calculation failed: {e}")


# ============================================================
# 4. OBV — On Balance Volume
# ============================================================

section("4. OBV — On Balance Volume")

def calc_obv(df):
    """
    OBV tăng: volume ngày tăng cộng dồn → tiền vào
    OBV giảm: volume ngày giảm trừ dồn  → tiền ra
    Divergence: giá tạo đỉnh mới nhưng OBV không → phân phối
    """
    close = df['close'] if 'close' in df.columns else df['Close']
    vol   = df['volume']if 'volume'in df.columns else df['Volume']
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * vol).cumsum()

if df is not None:
    try:
        df_calc = df.copy()
        obv = calc_obv(df_calc)
        obv_trend_5  = obv.iloc[-1] - obv.iloc[-5]
        obv_trend_20 = obv.iloc[-1] - obv.iloc[-20]
        close_trend  = df_calc['close'].iloc[-1] - df_calc['close'].iloc[-5]

        print(f"\n  OBV thay đổi 5 ngày : {obv_trend_5:+,.0f}")
        print(f"  OBV thay đổi 20 ngày: {obv_trend_20:+,.0f}")

        # Divergence check: OBV vs Price (20 ngày)
        price_20 = df_calc['close'].iloc[-1] > df_calc['close'].iloc[-20]
        obv_20   = obv.iloc[-1] > obv.iloc[-20]

        if price_20 and not obv_20:
            err("⚡ OBV Divergence: giá tăng 20 ngày nhưng OBV GIẢM → phân phối!")
        elif price_20 and obv_20:
            ok("Giá và OBV đều tăng 20 ngày → accumulation")
        elif not price_20 and obv_20:
            warn("Giá giảm nhưng OBV tăng → tiền vào âm thầm, có thể bounce")
        else:
            warn("Cả giá và OBV đều giảm → downtrend rõ")

    except Exception as e:
        err(f"OBV calculation failed: {e}")


# ============================================================
# 5. FOREIGN FLOW — thử các nguồn khác nhau
# ============================================================

section("5. FOREIGN FLOW — thử lấy từ vnstock")

# Thử 1: TCBS source (thường có foreign data tốt hơn VCI)
for src in ['TCBS', 'VCI', 'MSN']:
    try:
        print(f"\n  Thử source='{src}'...")
        st2 = Vnstock().stock(symbol=TICKER, source=src)
        df2 = st2.quote.history(start=start, end=end)
        foreign_cols = [c for c in df2.columns
                        if any(k in c.lower() for k in
                               ['foreign','nn','buy_vol','sell_vol','net'])]
        if foreign_cols:
            ok(f"Source {src} có: {foreign_cols}")
            print(df2[foreign_cols].tail(5).to_string())
        else:
            warn(f"Source {src}: không có foreign cols. Tất cả cols: {list(df2.columns)}")
    except Exception as e:
        err(f"Source {src}: {e}")


# ============================================================
# 6. INTRADAY — xem có gì
# ============================================================

section("6. INTRADAY DATA")

try:
    st3 = Vnstock().stock(symbol=TICKER, source='VCI')
    df_intra = st3.quote.intraday(symbol=TICKER, page_size=50)

    print(f"\n  Số hàng: {len(df_intra)}")
    print(f"  Cột có : {list(df_intra.columns)}")
    print(f"\n  10 hàng đầu:")
    print(df_intra.head(10).to_string())

    foreign_intra = [c for c in df_intra.columns
                     if any(k in c.lower() for k in ['foreign','nn','buy','sell'])]
    if foreign_intra:
        ok(f"Intraday có foreign cols: {foreign_intra}")
    else:
        warn("Intraday không có foreign cols")

except Exception as e:
    err(f"Intraday failed: {e}")


# ============================================================
# 7. TÓM TẮT — scoring hệ thống
# ============================================================

section("7. TÓM TẮT DÒNG TIỀN")

if df is not None:
    try:
        df_calc = df.copy()
        if df_calc['close'].mean() < 1000:
            for col in ['open','high','low','close']:
                if col in df_calc.columns:
                    df_calc[col] = df_calc[col] * 1000

        cmf_val  = calc_cmf(df_calc).iloc[-1]
        mfi_val  = calc_mfi(df_calc).iloc[-1]
        obv_data = calc_obv(df_calc)
        obv_div  = (df_calc['close'].iloc[-1] > df_calc['close'].iloc[-20]) and \
                   (obv_data.iloc[-1] < obv_data.iloc[-20])

        score = 0
        signals = []

        if cmf_val < 0:
            score += 1
            signals.append(f"CMF âm ({cmf_val:.3f})")
        if mfi_val > 70:
            score += 1
            signals.append(f"MFI overbought ({mfi_val:.0f})")
        if obv_div:
            score += 1
            signals.append("OBV divergence")

        # MFI divergence
        if (df_calc['close'].iloc[-1] > df_calc['close'].iloc[-5] and
                calc_mfi(df_calc).iloc[-1] < calc_mfi(df_calc).iloc[-5]):
            score += 1
            signals.append("MFI phân kỳ âm")

        print(f"\n  Cổ phiếu : {TICKER}")
        print(f"  Điểm cảnh báo thoát tiền: {score}/4")

        if score == 0:
            print("  → Không có tín hiệu thoát tiền")
        elif score == 1:
            print(f"  → Cảnh báo nhẹ: {', '.join(signals)}")
        elif score == 2:
            print(f"  → Cảnh báo TB — xem xét trailing chặt hơn: {', '.join(signals)}")
        else:
            print(f"  → CẢNH BÁO CAO — giảm trailing threshold: {', '.join(signals)}")

        print("\n  Gợi ý tích hợp vào sell scanner:")
        print("  • score >= 2 → giảm trailing pullback từ tier hiện tại xuống 1 bậc")
        print("  • score >= 3 → bán 50% ngay (không chờ trailing trigger)")

    except Exception as e:
        err(f"Summary failed: {e}")

print(f"\n{'='*60}")
print("  Test hoàn tất.")
print(f"{'='*60}\n")
