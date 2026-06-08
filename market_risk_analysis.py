#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MARKET RISK ANALYSIS MODULE v4
================================
Thay đổi so với v3:
  + Dùng VN30 thay VNINDEX (MA50/MA200 có ý nghĩa thực hơn)
  + Thêm MA200 tracking (long-term support/resistance)
  + Thêm RSI oversold bounce detection (signal đáy ngắn/trung hạn)
  + Thêm MACD histogram crossover detection
  + Thêm BB %B (oversold/overbought theo Bollinger Bands)
  + Thêm Volume capitulation detection
  + Giữ nguyên v3: smoothing 5-day, confirmation 3 ngày, hysteresis

Các tín hiệu mới phát hiện CHÍNH XÁC:
  - Sideways → Downtrend (như 02/03/2026): price break MA50 + MACD death cross
  - Downtrend → Sideways (như 08/04/2026): RSI oversold bounce + MA200 support

Files:
  - market_breadth_eod.json    (input, do scanner tạo)
  - market_regime_history.json (state, module tự quản lý)
  - market_risk_latest.json    (output)
"""

import json
import os
from datetime import datetime, timedelta

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
BREADTH_FILE = os.path.join(BASE_DIR, 'market_breadth_eod.json')
HISTORY_FILE = os.path.join(BASE_DIR, 'market_regime_history.json')
OUTPUT_FILE  = os.path.join(BASE_DIR, 'market_risk_latest.json')

# ================================================================
# CẤU HÌNH
# ================================================================

WEIGHTS = {
    'vn30_trend':      30,
    'liquidity':       20,
    'advance_decline': 25,
    'above_ma20':      25,
}

ALLOCATION_MAP = {'BULL': 80, 'SIDEWAYS': 50, 'BEAR': 20}

# Hysteresis — ngưỡng vào ≠ ra
BULL_ENTER = 32
BULL_EXIT  = 38
BEAR_ENTER = 68
BEAR_EXIT  = 62

MIN_CONFIRMATION_DAYS = 3
SMOOTH_WINDOW         = 5
HISTORY_KEEP_DAYS     = 14

# Cap điều chỉnh từ VN30 signals (tránh 1 event đẩy score quá mạnh)
MAX_RISK_ADJ_UP   = +55   # Tối đa tăng risk score bao nhiêu điểm
MAX_RISK_ADJ_DOWN = -50   # Tối đa giảm risk score bao nhiêu điểm


# ================================================================
# HELPERS — tính chỉ báo kỹ thuật từ list giá
# ================================================================

def _ema_series(prices: list, period: int) -> list:
    """Trả về toàn bộ series EMA"""
    if len(prices) < period:
        return []
    mult = 2 / (period + 1)
    result = [sum(prices[:period]) / period]
    for p in prices[period:]:
        result.append((p - result[-1]) * mult + result[-1])
    return result


def _sma(prices: list, period: int):
    """Simple Moving Average của N giá cuối"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def _rsi_series(prices: list, period: int = 14) -> list:
    """Trả về toàn bộ series RSI"""
    if len(prices) < period + 1:
        return [50.0]
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains   = [max(c, 0) for c in changes]
    losses  = [max(-c, 0) for c in changes]

    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    result = []
    for i in range(period, len(changes)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
        rs = avg_g / avg_l if avg_l > 0 else 100
        result.append(100 - 100 / (1 + rs))
    return result if result else [50.0]


def _macd_hist_series(prices: list, fast=12, slow=26, signal=9) -> list:
    """Trả về toàn bộ series MACD histogram"""
    ema_f = _ema_series(prices, fast)
    ema_s = _ema_series(prices, slow)
    if not ema_f or not ema_s:
        return [0.0]
    offset   = slow - fast
    macd_line = [f - s for f, s in zip(ema_f[offset:], ema_s)]
    sig_line  = _ema_series(macd_line, signal)
    if not sig_line:
        return [0.0]
    hist = [m - s for m, s in zip(macd_line[-len(sig_line):], sig_line)]
    return hist if hist else [0.0]


def _bb_pband(prices: list, period: int = 20, mult: float = 2.0) -> float:
    """Bollinger %B — 0=lower band, 0.5=middle, 1=upper band"""
    if len(prices) < period:
        return 0.5
    recent = prices[-period:]
    ma  = sum(recent) / period
    std = (sum((p - ma) ** 2 for p in recent) / period) ** 0.5
    if std == 0:
        return 0.5
    upper  = ma + mult * std
    lower  = ma - mult * std
    return (prices[-1] - lower) / (upper - lower)


def _calc_ema(prices: list, period: int):
    """EMA giá trị cuối cùng"""
    s = _ema_series(prices, period)
    return s[-1] if s else None


def _roc(prices: list, period: int) -> float:
    if len(prices) <= period:
        return 0.0
    return (prices[-1] - prices[-period]) / prices[-period] * 100


# ================================================================
# LOAD / SAVE HISTORY
# ================================================================

def load_history() -> dict:
    default = {
        'current_mode':        'SIDEWAYS',
        'mode_confirmed_date': None,
        'days_in_mode':        0,
        'pending_mode':        None,
        'pending_days':        0,
        'daily_scores':        [],
    }
    if not os.path.exists(HISTORY_FILE):
        return default
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for k, v in default.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return default


def save_history(h: dict):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(h, f, ensure_ascii=False, indent=2)


# ================================================================
# TREND SCORING — stepped, ổn định
# ================================================================

def score_vn30_trend(closes: list) -> tuple:
    """
    Stepped scoring (không dùng công thức nhân khuếch đại).
    Trả về (trend_score, label, detail_dict)
    """
    if len(closes) < 50:
        return 50, 'Không đủ dữ liệu', {}

    ema20 = _calc_ema(closes, 20)
    ema50 = _calc_ema(closes, 50)
    price = closes[-1]

    ema_diff = (ema20 - ema50) / ema50 * 100 if ema50 else 0
    roc5     = _roc(closes, 5)
    roc20    = _roc(closes, 20)

    if ema20 > ema50:
        d = ema_diff
        if d > 3 and price > ema20:    base, label = 12, 'Uptrend mạnh'
        elif d > 1.5 and price > ema20: base, label = 18, 'Uptrend'
        elif d > 0.5 and price > ema20: base, label = 25, 'Uptrend nhẹ'
        elif price > ema20:             base, label = 32, 'Uptrend yếu'
        else:                           base, label = 40, 'Điều chỉnh trong uptrend'
    else:
        d = abs(ema_diff)
        if d > 3 and price < ema20:    base, label = 82, 'Downtrend mạnh'
        elif d > 1.5 and price < ema20: base, label = 72, 'Downtrend'
        elif d > 0.5 and price < ema20: base, label = 62, 'Downtrend nhẹ'
        elif price > ema20:             base, label = 45, 'Phục hồi'
        else:                           base, label = 55, 'Downtrend yếu'

    # Momentum adjustment nhỏ (±3 điểm tối đa)
    adj = 0
    if roc5 > 3:   adj = -3
    elif roc5 > 1: adj = -1
    elif roc5 < -3: adj = +3
    elif roc5 < -1: adj = +1

    score = max(5, min(95, base + adj))
    detail = {
        'trend': label, 'price': round(price, 2),
        'ema20': round(ema20, 2), 'ema50': round(ema50, 2),
        'ema_diff_pct': round(ema_diff, 2),
        'roc5': round(roc5, 1), 'roc20': round(roc20, 1),
    }
    return round(score), label, detail


def score_liquidity(volumes: list) -> tuple:
    if len(volumes) < 20:
        return 50, {'label': 'N/A'}
    vol5  = sum(volumes[-5:])  / 5
    vol20 = sum(volumes[-20:]) / 20
    chg   = (vol5 - vol20) / vol20 * 100 if vol20 > 0 else 0

    if chg > 30:    score, label = 15, f'Tăng {round(chg)}% vs TB20'
    elif chg > 10:  score, label = 25, f'Tăng {round(chg)}% vs TB20'
    elif chg > -10: score, label = 50, 'Ngang TB20'
    elif chg > -25: score, label = 70, f'Giảm {round(abs(chg))}% vs TB20'
    else:           score, label = 85, f'Giảm {round(abs(chg))}% vs TB20'

    return score, {'label': label, 'vol5d': round(vol5),
                   'vol20d': round(vol20), 'change_pct': round(chg, 1)}


# ================================================================
# VN30-SPECIFIC SIGNALS — phát hiện breakdown + recovery
# ================================================================

def score_breakdown_signals(closes: list, volumes: list) -> tuple:
    """
    Phát hiện tín hiệu Sideways → Downtrend (như 02/03/2026).
    Trả về (risk_adjustment, signals_fired, detail)
      risk_adjustment > 0: tăng risk score (bearish)
    """
    if len(closes) < 50 or len(volumes) < 20:
        return 0, [], {}

    ma50      = _sma(closes, 50)
    rsi_s     = _rsi_series(closes, 14)
    macd_s    = _macd_hist_series(closes)
    vol_avg20 = sum(volumes[-20:]) / 20

    if ma50 is None or not rsi_s or not macd_s:
        return 0, [], {}

    rsi       = rsi_s[-1]
    rsi_prev  = rsi_s[-2] if len(rsi_s) >= 2 else rsi
    macd_hist = macd_s[-1]
    macd_prev = macd_s[-2] if len(macd_s) >= 2 else macd_hist
    price     = closes[-1]
    prev_price = closes[-2] if len(closes) >= 2 else price
    vol_today = volumes[-1] if volumes else vol_avg20

    adj      = 0
    signals  = []

    # ── Signal 1: Price break xuống dưới MA50 ──
    # Breakdown vừa xảy ra hôm nay (+40) hoặc đang duy trì dưới MA50 (+20)
    if prev_price >= ma50 and price < ma50:
        adj += 40
        signals.append('MA50 breakdown hôm nay (+40)')
    elif price < ma50:
        adj += 20
        signals.append('Đang dưới MA50 (+20)')

    # ── Signal 2: MACD death cross (histogram vừa chuyển âm) ──
    if macd_prev >= 0 and macd_hist < 0:
        adj += 20
        signals.append('MACD death cross (+20)')
    elif macd_hist < 0 and macd_hist < macd_prev:
        adj += 10
        signals.append('MACD histogram âm tăng tốc (+10)')

    # ── Signal 3: RSI phá dưới 50 trong 2 phiên ──
    rsi_2ago = rsi_s[-3] if len(rsi_s) >= 3 else rsi_prev
    if rsi < 50 and rsi_prev < 50 and rsi_2ago >= 50:
        adj += 15
        signals.append('RSI break dưới 50 liên tiếp (+15)')
    elif rsi < 50 and rsi_prev >= 50:
        adj += 8
        signals.append('RSI vừa phá dưới 50 (+8)')

    # ── Signal 4: Volume spike bán ──
    if price < prev_price and vol_today > vol_avg20 * 1.8:
        adj += 15
        signals.append(f'Volume bán spike {round(vol_today/vol_avg20, 1)}× TB (+15)')
    elif price < prev_price and vol_today > vol_avg20 * 1.4:
        adj += 7
        signals.append(f'Volume bán tăng {round(vol_today/vol_avg20, 1)}× TB (+7)')

    detail = {
        'ma50': round(ma50, 2),
        'price_vs_ma50': round((price - ma50) / ma50 * 100, 1),
        'rsi': round(rsi, 1),
        'macd_hist': round(macd_hist, 2),
        'vol_ratio': round(vol_today / vol_avg20, 2) if vol_avg20 > 0 else 0,
    }

    return min(adj, MAX_RISK_ADJ_UP), signals, detail


def score_recovery_signals(closes: list, highs: list,
                            lows: list, volumes: list) -> tuple:
    """
    Phát hiện tín hiệu Downtrend → Sideways (như 08/04/2026).
    Trả về (risk_adjustment, signals_fired, detail)
      risk_adjustment < 0: giảm risk score (bullish recovery)
    """
    if len(closes) < 50 or len(volumes) < 20:
        return 0, [], {}

    ma200     = _sma(closes, 200)
    rsi_s     = _rsi_series(closes, 14)
    macd_s    = _macd_hist_series(closes)
    bb_pct    = _bb_pband(closes, 20)
    vol_max20 = max(volumes[-20:]) if len(volumes) >= 20 else 0
    vol_avg20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 1

    if not rsi_s or not macd_s:
        return 0, [], {}

    rsi        = rsi_s[-1]
    rsi_prev   = rsi_s[-2]  if len(rsi_s) >= 2 else rsi
    rsi_3      = rsi_s[-4]  if len(rsi_s) >= 4 else rsi_prev  # 3 ngày trước
    macd_hist  = macd_s[-1]
    macd_prev  = macd_s[-2] if len(macd_s) >= 2 else macd_hist
    price      = closes[-1]
    prev_price = closes[-2] if len(closes) >= 2 else price
    vol_today  = volumes[-1] if volumes else vol_avg20
    low_3d     = min(lows[-3:])  if len(lows) >= 3 else lows[-1]

    adj     = 0
    signals = []

    # ── Signal 1: RSI oversold bounce ──
    # RSI từng dưới 30 trong 3 ngày qua và đang phục hồi vượt 35
    rsi_min_3d = min(rsi_s[-4:]) if len(rsi_s) >= 4 else rsi_prev
    if rsi_min_3d < 30 and rsi > 35 and rsi > rsi_prev:
        adj -= 35
        signals.append(f'RSI oversold bounce ({round(rsi_min_3d, 0)}→{round(rsi, 0)}) (-35)')
    elif rsi < 30:
        adj -= 15
        signals.append(f'RSI oversold zone {round(rsi, 0)} (-15)')
    elif rsi_prev < 35 and rsi >= 35:
        adj -= 12
        signals.append(f'RSI vừa vượt 35 (-12)')

    # ── Signal 2: Giá chạm MA200 rồi bounced ──
    if ma200 and low_3d <= ma200 * 1.02 and price > ma200:
        adj -= 25
        signals.append(f'Bounce từ MA200 ({round(ma200, 0)}) (-25)')
    elif ma200 and price > ma200 * 0.98 and price < ma200:
        adj -= 10
        signals.append('Tiếp cận MA200 (-10)')

    # ── Signal 3: Volume capitulation (đáy ngắn hạn) ──
    # Volume hôm nay trong top 10% 20 ngày VÀ nến đóng cửa xanh
    if vol_max20 > 0 and vol_today >= vol_max20 * 0.85 and price > prev_price:
        adj -= 20
        signals.append(f'Volume capitulation {round(vol_today/vol_avg20, 1)}× TB (-20)')

    # ── Signal 4: BB lower band oversold ──
    if bb_pct < 0.05:
        adj -= 12
        signals.append(f'BB %B cực thấp ({round(bb_pct, 2)}) (-12)')
    elif bb_pct < 0.15:
        adj -= 6
        signals.append(f'BB %B thấp ({round(bb_pct, 2)}) (-6)')

    # ── Signal 5: MACD histogram phục hồi ──
    if macd_hist > macd_prev and macd_prev < 0 and macd_hist < 0:
        adj -= 8
        signals.append('MACD histogram cải thiện (-8)')
    elif macd_prev < 0 and macd_hist >= 0:
        adj -= 15
        signals.append('MACD histogram chuyển dương (-15)')

    detail = {
        'rsi':        round(rsi, 1),
        'rsi_min_3d': round(rsi_min_3d, 1) if len(rsi_s) >= 4 else None,
        'ma200':      round(ma200, 2) if ma200 else None,
        'bb_pband':   round(bb_pct, 3),
        'macd_hist':  round(macd_hist, 2),
        'vol_cap_ratio': round(vol_today / vol_max20, 2) if vol_max20 > 0 else 0,
    }

    return max(adj, MAX_RISK_ADJ_DOWN), signals, detail



# ================================================================
# WYCKOFF PHASE DETECTION
# ================================================================

def detect_wyckoff_phase(closes: list, highs: list, lows: list, volumes: list) -> dict:
    """
    Nhận diện pha Wyckoff dựa trên VN30.
    Spring: giá phá đáy TR ≤5% → pha C tích lũy
    Downtrend: giá phá đáy TR >5% → downtrend thật
    """
    if len(closes) < 60 or len(lows) < 60 or len(highs) < 60:
        return {'phase': 'UNKNOWN', 'description': 'Không đủ dữ liệu', 'action_hint': ''}

    tr_window    = 60
    tr_high      = max(highs[-tr_window:])
    tr_low       = min(lows[-tr_window:])
    tr_range_pct = (tr_high - tr_low) / tr_low * 100 if tr_low > 0 else 0

    price        = closes[-1]
    vol_avg20    = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 1
    vol_today    = volumes[-1] if volumes else vol_avg20
    vol_ratio    = vol_today / vol_avg20 if vol_avg20 > 0 else 1

    # Độ sâu phá đáy TR (>0 = đang dưới TR_low)
    spring_depth_pct = (tr_low - price) / tr_low * 100 if price < tr_low else 0
    price_in_tr_pct  = (price - tr_low) / (tr_high - tr_low) * 100 if tr_high > tr_low else 50

    roc5 = _roc(closes, 5)
    rsi  = _rsi_series(closes, 14)[-1] if len(closes) >= 15 else 50

    if spring_depth_pct > 5:
        phase       = 'DOWNTREND'
        description = f'Downtrend thật: VN30 phá đáy TR {spring_depth_pct:.1f}% (>5%)'
        action_hint = 'Hạn chế mua. Chờ giá quay về TR mới xét lại'
        color       = 'red'

    elif 3 <= spring_depth_pct <= 5:
        phase       = 'PHASE_C_SHAKEOUT'
        description = f'Wyckoff Phase C - Shakeout: VN30 phá đáy TR {spring_depth_pct:.1f}% (volume {vol_ratio:.1f}x)'
        action_hint = 'Cân nhắc mua từng phần 20-25%. Chờ xác nhận Secondary Test'
        color       = 'orange'

    elif 0 < spring_depth_pct < 3:
        phase       = 'PHASE_C_SPRING'
        description = f'Wyckoff Phase C - Spring: VN30 phá đáy TR {spring_depth_pct:.1f}% (nhẹ)'
        action_hint = 'Theo dõi volume. Nếu volume giảm khi test lại đáy → xác nhận Spring'
        color       = 'yellow'

    elif price_in_tr_pct > 80 and roc5 > 0 and rsi > 60:
        phase       = 'PHASE_D_MARKUP'
        description = f'Wyckoff Phase D - Markup: VN30 breakout khỏi TR (giá ở top {price_in_tr_pct:.0f}%)'
        action_hint = 'Thị trường đang markup. Tăng tỷ trọng theo tín hiệu'
        color       = 'green'

    elif price_in_tr_pct > 75:
        phase       = 'DISTRIBUTION'
        description = f'Có thể Distribution: giá cao trong TR ({price_in_tr_pct:.0f}%) nhưng RSI {rsi:.0f}'
        action_hint = 'Thận trọng. Theo dõi volume spike bán tại vùng đỉnh TR'
        color       = 'yellow'

    elif tr_range_pct < 10 and price_in_tr_pct < 60:
        phase       = 'ACCUMULATION'
        description = f'Wyckoff Accumulation: VN30 tích lũy trong biên độ hẹp ({tr_range_pct:.1f}%)'
        action_hint = 'Giai đoạn tích lũy. Mua từng phần khi có tín hiệu mạnh'
        color       = 'blue'

    else:
        phase       = 'RANGING'
        description = f'VN30 dao động trong TR ({tr_range_pct:.1f}%), vị trí {price_in_tr_pct:.0f}%'
        action_hint = 'Thị trường sideway. Chọn lọc kỹ trước khi vào lệnh'
        color       = 'gray'

    return {
        'phase':            phase,
        'description':      description,
        'action_hint':      action_hint,
        'color':            color,
        'tr_high':          round(tr_high, 2),
        'tr_low':           round(tr_low, 2),
        'tr_range_pct':     round(tr_range_pct, 1),
        'spring_depth_pct': round(spring_depth_pct, 2),
        'price_in_tr_pct':  round(price_in_tr_pct, 1),
        'vol_ratio':        round(vol_ratio, 2),
        'rsi':              round(rsi, 1),
        'is_spring':        phase in ('PHASE_C_SPRING', 'PHASE_C_SHAKEOUT'),
        'is_markup':        phase == 'PHASE_D_MARKUP',
    }

# ================================================================
# VN30 API CALL (thay VNINDEX)
# ================================================================

def analyze_vn30():
    """
    Fetch VN30 data (1 API call).
    Tính: trend score, liquidity score, breakdown signals, recovery signals.
    Trả về: (trend_score, liq_score, risk_adj, trend_detail, liq_detail,
              breakdown_signals, recovery_signals, vn30_detail)
    """
    try:
        from vnstock import Vnstock
        end   = datetime.now()
        start = end - timedelta(days=250)   # ~200 ngày giao dịch để có đủ MA200

        df = Vnstock().stock(symbol='VN30', source='VCI').quote.history(
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            interval='1D'
        )

        if df is None or len(df) < 60:
            print("⚠️  VN30: không đủ dữ liệu, thử VNINDEX...")
            df = Vnstock().stock(symbol='VNINDEX', source='VCI').quote.history(
                start=start.strftime('%Y-%m-%d'),
                end=end.strftime('%Y-%m-%d'),
                interval='1D'
            )

        if df is None or len(df) < 60:
            return 50, 50, 0, {'trend': 'N/A'}, {'label': 'N/A'}, [], [], {}

        closes  = df['close'].tolist()
        volumes = df['volume'].tolist()
        highs   = df['high'].tolist()  if 'high'  in df.columns else closes
        lows    = df['low'].tolist()   if 'low'   in df.columns else closes

        # ── Trend scoring ──
        trend_score, trend_label, trend_detail = score_vn30_trend(closes)

        # ── Liquidity scoring ──
        liq_score, liq_detail = score_liquidity(volumes)

        # ── VN30-specific signals ──
        down_adj, down_sigs, down_detail = score_breakdown_signals(closes, volumes)
        up_adj, up_sigs, up_detail       = score_recovery_signals(closes, highs, lows, volumes)

        # Tổng risk adjustment (breakdown tăng risk, recovery giảm risk)
        # Hai loại signal không cộng vào nhau vô hạn — lấy phần chiếm ưu thế
        risk_adj = down_adj + up_adj   # down_adj >= 0, up_adj <= 0

        # Thêm vào detail
        ma50  = _sma(closes, 50)
        ma200 = _sma(closes, 200)
        trend_detail.update({
            'ma50':       round(ma50,  2) if ma50  else None,
            'ma200':      round(ma200, 2) if ma200 else None,
            'bb_pband':   round(_bb_pband(closes), 3),
            'rsi':        round(_rsi_series(closes)[-1], 1),
            'data_source': 'VN30',
        })

        # ── Wyckoff Phase Detection ──
        wyckoff = detect_wyckoff_phase(closes, highs, lows, volumes)
        print(f"   → Wyckoff: {wyckoff['phase']} | {wyckoff['description']}")

        vn30_detail = {
            'breakdown': {'adj': down_adj, 'signals': down_sigs, **down_detail},
            'recovery':  {'adj': up_adj,   'signals': up_sigs,   **up_detail},
            'net_risk_adj': risk_adj,
            'wyckoff': wyckoff,
        }

        return (trend_score, liq_score, risk_adj,
                trend_detail, liq_detail,
                down_sigs, up_sigs, vn30_detail)

    except Exception as e:
        print(f"⚠️  VN30 analyze error: {e}")
        return 50, 50, 0, {'trend': 'Error'}, {'label': 'Error'}, [], [], {}


# ================================================================
# BREADTH (0 API, đọc file)
# ================================================================

def analyze_breadth_from_eod():
    if not os.path.exists(BREADTH_FILE):
        print(f"⚠️  Breadth file not found: {BREADTH_FILE}")
        return 50, 50, {
            'advance_label': 'Chưa có dữ liệu', 'ma20_label': 'Chưa có dữ liệu',
            'advance': 0, 'decline': 0, 'total_analyzed': 0,
            'above_ma20': 0, 'above_ma20_pct': 0,
        }
    try:
        with open(BREADTH_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        advance      = data.get('advance', 0)
        decline      = data.get('decline', 0)
        unchanged    = data.get('unchanged', 0)
        total        = data.get('total', 0)
        above_ma20   = data.get('above_ma20', 0)
        above_ma20_pct = data.get('above_ma20_pct', 0)
        data_date    = data.get('date', '')

        today = datetime.now().strftime('%Y-%m-%d')
        if data_date and data_date != today:
            print(f"   ℹ️ Breadth data từ {data_date}")

        total_ad = advance + decline
        ratio    = advance / total_ad if total_ad > 0 else 0.5

        if ratio > 0.65:   ad_score = 15
        elif ratio > 0.55: ad_score = 30
        elif ratio > 0.45: ad_score = 50
        elif ratio > 0.35: ad_score = 70
        else:              ad_score = 85

        if above_ma20_pct > 65:   ma20_score = 15
        elif above_ma20_pct > 55: ma20_score = 30
        elif above_ma20_pct > 45: ma20_score = 50
        elif above_ma20_pct > 35: ma20_score = 70
        else:                     ma20_score = 85

        return ad_score, ma20_score, {
            'advance': advance, 'decline': decline,
            'unchanged': unchanged, 'total_analyzed': total,
            'above_ma20': above_ma20,
            'above_ma20_pct': round(above_ma20_pct, 1),
            'advance_label': f'{advance} tăng / {decline} giảm',
            'ma20_label':    f'{round(above_ma20_pct)}% ({above_ma20}/{total})',
            'data_date': data_date,
        }
    except Exception as e:
        print(f"⚠️  Breadth error: {e}")
        return 50, 50, {
            'advance_label': 'Error', 'ma20_label': 'Error',
            'advance': 0, 'decline': 0, 'total_analyzed': 0,
            'above_ma20': 0, 'above_ma20_pct': 0,
        }


# ================================================================
# COLLECT BREADTH (gọi từ scanner — không đổi)
# ================================================================

def collect_breadth_data(stock_data_list):
    advance = decline = unchanged = above_ma20 = total = 0
    for item in stock_data_list:
        closes = item.get('closes', [])
        if len(closes) < 2: continue
        total += 1
        if   closes[-1] > closes[-2]: advance   += 1
        elif closes[-1] < closes[-2]: decline   += 1
        else:                         unchanged += 1
        if len(closes) >= 20 and closes[-1] > sum(closes[-20:]) / 20:
            above_ma20 += 1

    above_ma20_pct = above_ma20 / total * 100 if total > 0 else 0
    result = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total': total, 'advance': advance,
        'decline': decline, 'unchanged': unchanged,
        'above_ma20': above_ma20,
        'above_ma20_pct': round(above_ma20_pct, 1),
        'generated_at': datetime.now().isoformat(),
    }
    with open(BREADTH_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n📊 BREADTH SAVED | Tổng:{total} Tăng:{advance} Giảm:{decline} "
          f"MA20:{above_ma20}({round(above_ma20_pct,1)}%)")
    return result


# ================================================================
# MODE DETERMINATION — smoothing + confirmation + hysteresis
# ================================================================

def determine_mode_with_confirmation(adjusted_score: int, components: dict) -> tuple:
    """
    Quyết định Market Mode với 3 lớp bảo vệ:
      1. Smoothing: trung bình 5 ngày
      2. Hysteresis: ngưỡng vào/ra khác nhau
      3. Confirmation: 3 ngày liên tiếp vượt ngưỡng
    """
    today   = datetime.now().strftime('%Y-%m-%d')
    history = load_history()

    # Cập nhật daily_scores
    existing = [d['date'] for d in history['daily_scores']]
    if today not in existing:
        history['daily_scores'].append({
            'date': today, 'raw_score': adjusted_score, 'components': components,
        })
    else:
        for d in history['daily_scores']:
            if d['date'] == today:
                d['raw_score'] = adjusted_score
                d['components'] = components
                break

    history['daily_scores'] = sorted(
        history['daily_scores'], key=lambda x: x['date']
    )[-HISTORY_KEEP_DAYS:]

    # Smoothed score
    recent = [d['raw_score'] for d in history['daily_scores'][-SMOOTH_WINDOW:]]
    score_5d = round(sum(recent) / len(recent))

    # Proposed mode dựa theo hysteresis
    current = history.get('current_mode', 'SIDEWAYS')
    if current == 'BULL':
        proposed = 'BULL' if score_5d < BULL_EXIT else (
            'BEAR' if score_5d >= BEAR_ENTER else 'SIDEWAYS'
        )
    elif current == 'BEAR':
        proposed = 'BEAR' if score_5d > BEAR_EXIT else (
            'BULL' if score_5d <= BULL_ENTER else 'SIDEWAYS'
        )
    else:
        if score_5d <= BULL_ENTER:       proposed = 'BULL'
        elif score_5d >= BEAR_ENTER:     proposed = 'BEAR'
        else:                            proposed = 'SIDEWAYS'

    # Confirmation
    transition_info = None
    if proposed == current:
        history['pending_mode'] = None
        history['pending_days'] = 0
        history['days_in_mode'] = history.get('days_in_mode', 0) + 1
        final_mode = current
    else:
        if history.get('pending_mode') == proposed:
            history['pending_days'] = history.get('pending_days', 0) + 1
        else:
            history['pending_mode'] = proposed
            history['pending_days'] = 1

        pd_ = history['pending_days']
        transition_info = {
            'pending_mode': proposed,
            'pending_days': pd_,
            'days_needed':  MIN_CONFIRMATION_DAYS,
        }

        if pd_ >= MIN_CONFIRMATION_DAYS:
            print(f"\n  🔄 MODE CHANGE: {current} → {proposed} (confirmed {pd_}d)")
            history['current_mode']        = proposed
            history['mode_confirmed_date'] = today
            history['days_in_mode']        = 1
            history['pending_mode']        = None
            history['pending_days']        = 0
            final_mode = proposed
        else:
            print(f"\n  ⏳ Pending: {current}→{proposed} ({pd_}/{MIN_CONFIRMATION_DAYS}d)...")
            final_mode = current

    save_history(history)

    MAP = {
        'BULL':     ('TÍCH CỰC', '🟢'),
        'SIDEWAYS': ('THẬN TRỌNG', '🟡'),
        'BEAR':     ('PHÒNG THỦ', '🔴'),
    }
    label, emoji = MAP[final_mode]
    return final_mode, label, emoji, score_5d, history, transition_info


# ================================================================
# MAIN
# ================================================================

def run_market_analysis():
    print("\n" + "=" * 60)
    print("🔍 MARKET RISK ANALYSIS v4  (VN30 + MA200 + RSI + BB + MACD)")
    print("   Smoothing: 5d | Confirmation: 3d | Hysteresis: ON")
    print("=" * 60)

    # 1. VN30 (1 API call: trend + liquidity + breakdown + recovery)
    print("\n📊 [1/2] VN30 Trend + Liquidity + Technical Signals...")
    (trend_score, liq_score, risk_adj,
     trend_detail, liq_detail,
     down_sigs, up_sigs, vn30_detail) = analyze_vn30()

    print(f"   → Trend: {trend_detail.get('trend')} | score={trend_score}")
    print(f"   → RSI={trend_detail.get('rsi')}  BB%B={trend_detail.get('bb_pband')}")
    print(f"   → Liquidity: {liq_detail.get('label')} | score={liq_score}")
    if down_sigs:
        for s in down_sigs: print(f"   ⚠️  Breakdown: {s}")
    if up_sigs:
        for s in up_sigs:   print(f"   ✅ Recovery:  {s}")
    print(f"   → Net risk adjustment từ VN30: {risk_adj:+d}")

    # 2. Breadth + MA20 (0 API)
    print("\n📊 [2/2] Breadth + MA20 (từ file EOD)...")
    ad_score, ma20_score, breadth_detail = analyze_breadth_from_eod()
    print(f"   → A/D: {breadth_detail.get('advance_label')} | score={ad_score}")
    print(f"   → MA20: {breadth_detail.get('ma20_label')} | score={ma20_score}")

    # Raw base score (từ 4 component)
    base_score = round(
        trend_score  * WEIGHTS['vn30_trend']      / 100 +
        liq_score    * WEIGHTS['liquidity']        / 100 +
        ad_score     * WEIGHTS['advance_decline']  / 100 +
        ma20_score   * WEIGHTS['above_ma20']       / 100
    )

    # Áp dụng risk adjustment từ VN30 signals
    adjusted_score = int(max(0, min(100, base_score + risk_adj)))

    components = {
        'vn30_trend':      trend_score,
        'liquidity':       liq_score,
        'advance_decline': ad_score,
        'above_ma20':      ma20_score,
        'base_score':      base_score,
        'risk_adj':        risk_adj,
    }
    print(f"\n   Base score: {base_score} | Adj: {risk_adj:+d} → Adjusted: {adjusted_score}/100")

    # Quyết định mode
    (market_mode, mode_label, mode_emoji,
     score_5d, history, transition_info) = determine_mode_with_confirmation(
        adjusted_score, components
    )

    if transition_info:
        pm = transition_info['pending_mode']
        pd = transition_info['pending_days']
        dn = transition_info['days_needed']
        print(f"   Score 5d avg: {score_5d} → Pending: {pm} ({pd}/{dn}d)")
    else:
        print(f"   Score 5d avg: {score_5d} → Mode ổn định")

    DESC = {
        'BULL':     'Thị trường uptrend — Ưu tiên tìm điểm mua',
        'SIDEWAYS': 'Thị trường sideway — Chỉ mua khi tín hiệu rõ ràng',
        'BEAR':     'Thị trường downtrend — Hạn chế mua, ưu tiên bảo toàn vốn',
    }

    factors = [
        {'label': 'VN30 Trend',       'value': trend_detail.get('trend', 'N/A'),
         'positive': trend_score < 50, 'score': trend_score},
        {'label': 'Thanh khoản',      'value': liq_detail.get('label', 'N/A'),
         'positive': liq_score < 50,  'score': liq_score},
        {'label': 'Số CP tăng/giảm', 'value': breadth_detail.get('advance_label', 'N/A'),
         'positive': ad_score < 50,   'score': ad_score},
        {'label': 'CP trên MA20',     'value': breadth_detail.get('ma20_label', 'N/A'),
         'positive': ma20_score < 50, 'score': ma20_score},
        {'label': 'Tham khảo: NN',   'value': 'Chỉ tham khảo',
         'positive': False, 'isRef': True},
    ]

    analysis = {
        # Trường tương thích v2/v3
        'market_mode':  market_mode,
        'mode_label':   mode_label,
        'mode_emoji':   mode_emoji,
        'description':  DESC[market_mode],
        'risk_score':   score_5d,
        'allocation':   ALLOCATION_MAP[market_mode],
        'factors':      factors,
        # Trường mới v4
        'raw_scores':   components,
        'base_score':   base_score,
        'risk_adj':     risk_adj,
        'adjusted_score_today': adjusted_score,
        'vn30_signals': {
            'breakdown': down_sigs,
            'recovery':  up_sigs,
            'detail':    vn30_detail,
        },
        'wyckoff': vn30_detail.get('wyckoff', {}),
        'vnindex_detail':  trend_detail,
        'breadth_detail': {
            'advance':        breadth_detail.get('advance', 0),
            'decline':        breadth_detail.get('decline', 0),
            'total_analyzed': breadth_detail.get('total_analyzed', 0),
            'above_ma20':     breadth_detail.get('above_ma20', 0),
            'above_ma20_pct': breadth_detail.get('above_ma20_pct', 0),
        },
        'days_in_mode':  history.get('days_in_mode', 0),
        'transition':    transition_info,
        'analyzed_at':   datetime.now().isoformat(),
        'version':       'v4',
        'api_calls_used': 1,
    }

    print("\n" + "=" * 60)
    print(f"{mode_emoji} MARKET MODE: {mode_label} ({market_mode})")
    print(f"📊 Score 5d avg: {score_5d}/100  |  Adjusted hôm nay: {adjusted_score}/100")
    print(f"   Base={base_score} | VN30 adj={risk_adj:+d}")
    print(f"📅 Đã ở mode này: {history.get('days_in_mode', 0)} ngày")
    print(f"💰 Tỷ trọng khuyến nghị: {ALLOCATION_MAP[market_mode]}% cổ phiếu")
    if transition_info:
        pm = transition_info['pending_mode']
        pd = transition_info['pending_days']
        dn = transition_info['days_needed']
        print(f"⏳ Cảnh báo: Pending {pm} ({pd}/{dn} ngày nữa mới đổi)")
    if down_sigs: print(f"⚠️  Breakdown signals: {', '.join(down_sigs[:2])}")
    if up_sigs:   print(f"✅ Recovery signals:  {', '.join(up_sigs[:2])}")
    print("=" * 60 + "\n")

    return analysis


if __name__ == '__main__':
    result = run_market_analysis()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved → {OUTPUT_FILE}")
