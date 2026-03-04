#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MARKET RISK ANALYSIS MODULE v2
Sử dụng dữ liệu EOD từ scanner (đã download sẵn) thay vì gọi API từng mã.

Flow:
  1. Scanner chạy → download history 346 mã → tính breadth → lưu file
  2. Module này chạy sau scanner:
     - VN-Index trend + thanh khoản: 1 API call duy nhất
     - Breadth + MA20: đọc từ file market_breadth_eod.json (0 API call)

Tổng: 1 API call → không bị rate limit.
"""

import json
import os
from datetime import datetime, timedelta

# ========================================================================
# CONFIGURATION
# ========================================================================

BREADTH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'market_breadth_eod.json')

WEIGHTS = {
    'vnindex_trend': 25,      # Giảm từ 30 → 25 (EMA chậm phản ứng)
    'liquidity': 15,           # Giảm từ 20 → 15 (ít quan trọng nhất)
    'advance_decline': 30,     # Tăng từ 25 → 30 (phản ứng nhanh nhất)
    'above_ma20': 30,          # Tăng từ 25 → 30 (sức khỏe trung hạn)
}

THRESHOLDS = {
    'BULL': 35,
    'SIDEWAYS': 65,
}

ALLOCATION_MAP = {
    'BULL': 80,       # Fallback nếu cần
    'SIDEWAYS': 50,
    'BEAR': 20,
}


def dynamic_allocation(risk_score):
    """
    Tỷ trọng CP trượt mượt theo risk score, không giật cục.
    
    BULL (0-35):     75% → 60% CP
    SIDEWAYS (36-65): 55% → 35% CP  
    BEAR (66-100):    30% → 15% CP
    
    VD: Score 58 → ~40% CP (thay vì nhảy cứng 50%)
        Score 64 → ~36% CP
        Score 70 → ~27% CP
    """
    if risk_score <= 35:
        # BULL: 75 → 60
        ratio = risk_score / 35
        return round(75 - ratio * 15)
    elif risk_score <= 65:
        # SIDEWAYS: 55 → 35
        ratio = (risk_score - 36) / 29
        return round(55 - ratio * 20)
    else:
        # BEAR: 30 → 15
        ratio = min(1, (risk_score - 66) / 34)
        return round(30 - ratio * 15)


# ========================================================================
# HELPER
# ========================================================================

def calculate_ema(prices, period):
    if len(prices) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema


# ========================================================================
# 1. VN-INDEX TREND + LIQUIDITY (1 API call duy nhất)
# ========================================================================

def analyze_vnindex_and_liquidity():
    """1 API call cho cả trend + thanh khoản VN-Index."""
    try:
        from vnstock import Vnstock

        stock = Vnstock().stock(symbol='VNINDEX', source='VCI')
        end = datetime.now()
        start = end - timedelta(days=120)

        df = stock.quote.history(
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            interval='1D'
        )

        if df is None or len(df) < 50:
            return 50, 50, {'trend': 'N/A'}, {'label': 'N/A'}

        closes = df['close'].tolist()
        volumes = df['volume'].tolist()

        # ── Trend ──
        ema20 = calculate_ema(closes, 20)
        ema50 = calculate_ema(closes, 50)
        current_price = closes[-1]
        ema_diff_pct = (ema20 - ema50) / ema50 * 100 if ema50 else 0

        if ema20 > ema50 and current_price > ema20:
            trend, trend_score = 'Uptrend', max(0, 20 - ema_diff_pct * 5)
        elif ema20 > ema50 and current_price < ema20:
            trend, trend_score = 'Uptrend yếu', 35
        elif ema20 < ema50 and current_price > ema20:
            trend, trend_score = 'Phục hồi', 45
        elif abs(ema_diff_pct) < 0.5:
            trend, trend_score = 'Sideway', 50
        elif ema20 < ema50 and current_price < ema20:
            trend, trend_score = 'Downtrend', min(100, 70 + abs(ema_diff_pct) * 5)
        else:
            trend, trend_score = 'Downtrend yếu', 60

        trend_detail = {
            'trend': trend,
            'vnindex': round(current_price, 2),
            'ema20': round(ema20, 2),
            'ema50': round(ema50, 2),
            'ema_diff_pct': round(ema_diff_pct, 2),
        }

        # ── Thanh khoản ──
        vol_5d = sum(volumes[-5:]) / 5 if len(volumes) >= 5 else 0
        vol_20d = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 0
        change_pct = (vol_5d - vol_20d) / vol_20d * 100 if vol_20d > 0 else 0

        if change_pct > 30:    liq_score = 15
        elif change_pct > 10:  liq_score = 25
        elif change_pct > -10: liq_score = 50
        elif change_pct > -25: liq_score = 70
        else:                  liq_score = 85

        if change_pct > 0:
            liq_label = f'Tăng {abs(round(change_pct))}% vs TB20'
        elif change_pct < -10:
            liq_label = f'Giảm {abs(round(change_pct))}% vs TB20'
        else:
            liq_label = 'Ngang TB20'

        liq_detail = {
            'label': liq_label,
            'vol_5d': round(vol_5d),
            'vol_20d': round(vol_20d),
            'change_pct': round(change_pct, 1),
        }

        return trend_score, liq_score, trend_detail, liq_detail

    except Exception as e:
        print(f"⚠️ VN-Index analysis error: {e}")
        return 50, 50, {'trend': 'Error', 'detail': str(e)}, {'label': 'Error'}


# ========================================================================
# 2. BREADTH + MA20 (đọc từ file, 0 API call)
# ========================================================================

def analyze_breadth_from_eod():
    """Đọc market_breadth_eod.json do scanner tạo sẵn."""
    if not os.path.exists(BREADTH_FILE):
        print(f"⚠️ Breadth file not found: {BREADTH_FILE}")
        print("   → Chạy scanner trước để tạo file này")
        return 50, 50, {
            'advance_label': 'Chưa có dữ liệu', 'ma20_label': 'Chưa có dữ liệu',
            'advance': 0, 'decline': 0, 'total_analyzed': 0,
            'above_ma20': 0, 'above_ma20_pct': 0,
        }

    try:
        with open(BREADTH_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        advance = data.get('advance', 0)
        decline = data.get('decline', 0)
        unchanged = data.get('unchanged', 0)
        total = data.get('total', 0)
        above_ma20 = data.get('above_ma20', 0)
        above_ma20_pct = data.get('above_ma20_pct', 0)

        data_date = data.get('date', '')
        today = datetime.now().strftime('%Y-%m-%d')
        if data_date and data_date != today:
            print(f"   ℹ️ Breadth data từ {data_date} (hôm nay: {today})")

        # Advance/Decline Score
        total_ad = advance + decline
        if total_ad > 0:
            ratio = advance / total_ad
            if ratio > 0.65:   ad_score = 15
            elif ratio > 0.55: ad_score = 30
            elif ratio > 0.45: ad_score = 50
            elif ratio > 0.35: ad_score = 70
            else:              ad_score = 85
        else:
            ad_score = 50

        # MA20 Score
        if above_ma20_pct > 65:   ma20_score = 15
        elif above_ma20_pct > 55: ma20_score = 30
        elif above_ma20_pct > 45: ma20_score = 50
        elif above_ma20_pct > 35: ma20_score = 70
        else:                     ma20_score = 85

        detail = {
            'advance': advance, 'decline': decline, 'unchanged': unchanged,
            'total_analyzed': total,
            'above_ma20': above_ma20, 'above_ma20_pct': round(above_ma20_pct, 1),
            'advance_label': f'{advance} tăng / {decline} giảm',
            'ma20_label': f'{round(above_ma20_pct)}% ({above_ma20}/{total})',
            'data_date': data_date,
        }
        return ad_score, ma20_score, detail

    except Exception as e:
        print(f"⚠️ Breadth analysis error: {e}")
        return 50, 50, {
            'advance_label': 'Error', 'ma20_label': 'Error',
            'advance': 0, 'decline': 0, 'total_analyzed': 0,
            'above_ma20': 0, 'above_ma20_pct': 0,
        }


# ========================================================================
# 3. HÀM THU THẬP BREADTH DATA (GỌI TỪ SCANNER)
# ========================================================================

def collect_breadth_data(stock_data_list):
    """
    Gọi từ daily_signal_scanner_eod.py SAU KHI download xong tất cả mã.

    Params:
        stock_data_list: list of dict
            [{'ticker': 'VCB', 'closes': [85000, 86000, ...]}, ...]

    Tính advance/decline + MA20 rồi lưu market_breadth_eod.json
    """
    advance = decline = unchanged = above_ma20 = total = 0

    for item in stock_data_list:
        closes = item.get('closes', [])
        if len(closes) < 2:
            continue

        total += 1
        today_close = closes[-1]
        yesterday_close = closes[-2]

        if today_close > yesterday_close:
            advance += 1
        elif today_close < yesterday_close:
            decline += 1
        else:
            unchanged += 1

        if len(closes) >= 20:
            ma20 = sum(closes[-20:]) / 20
            if today_close > ma20:
                above_ma20 += 1

    above_ma20_pct = (above_ma20 / total * 100) if total > 0 else 0

    result = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total': total,
        'advance': advance,
        'decline': decline,
        'unchanged': unchanged,
        'above_ma20': above_ma20,
        'above_ma20_pct': round(above_ma20_pct, 1),
        'generated_at': datetime.now().isoformat(),
    }

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'market_breadth_eod.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n📊 BREADTH DATA SAVED → {output_path}")
    print(f"   Tổng: {total} | Tăng: {advance} | Giảm: {decline} | Không đổi: {unchanged}")
    print(f"   Trên MA20: {above_ma20}/{total} ({round(above_ma20_pct, 1)}%)")

    return result


# ========================================================================
# MAIN
# ========================================================================

def run_market_analysis():
    """
    Full market analysis. Total: 1 API call.
    """
    print("\n" + "=" * 60)
    print("🔍 MARKET RISK ANALYSIS v2")
    print("=" * 60)

    # 1+2. VN-Index + Thanh khoản (1 API call)
    print("\n📊 [1/2] VN-Index Trend + Thanh khoản (1 API call)...")
    trend_score, liq_score, trend_detail, liq_detail = analyze_vnindex_and_liquidity()
    print(f"   → Trend: {trend_detail.get('trend')} | Score: {round(trend_score)}")
    print(f"   → Thanh khoản: {liq_detail.get('label')} | Score: {liq_score}")

    # 3. Breadth + MA20 (0 API call)
    print("\n📊 [2/2] Breadth + MA20 (từ file EOD, 0 API call)...")
    ad_score, ma20_score, breadth_detail = analyze_breadth_from_eod()
    print(f"   → A/D: {breadth_detail.get('advance_label')} | Score: {ad_score}")
    print(f"   → MA20: {breadth_detail.get('ma20_label')} | Score: {ma20_score}")

    # ── Risk Score ──
    risk_score = round(
        trend_score * WEIGHTS['vnindex_trend'] / 100 +
        liq_score * WEIGHTS['liquidity'] / 100 +
        ad_score * WEIGHTS['advance_decline'] / 100 +
        ma20_score * WEIGHTS['above_ma20'] / 100
    )

    # ── Market Mode ──
    if risk_score <= THRESHOLDS['BULL']:
        market_mode, mode_label, mode_emoji = 'BULL', 'TÍCH CỰC', '🟢'
        description = 'Thị trường uptrend — Ưu tiên tìm điểm mua'
    elif risk_score <= THRESHOLDS['SIDEWAYS']:
        market_mode, mode_label, mode_emoji = 'SIDEWAYS', 'THẬN TRỌNG', '🟡'
        description = 'Thị trường sideway — Chỉ mua khi tín hiệu rõ ràng'
    else:
        market_mode, mode_label, mode_emoji = 'BEAR', 'PHÒNG THỦ', '🔴'
        description = 'Thị trường rủi ro cao — Giảm tỷ trọng, giữ kỷ luật stop-loss'

    # ── Dynamic Allocation (mượt, không giật cục) ──
    allocation = dynamic_allocation(risk_score)

    factors = [
        {'label': 'VN-Index Trend', 'value': trend_detail.get('trend', 'N/A'),
         'positive': trend_score < 50, 'score': round(trend_score)},
        {'label': 'Thanh khoản', 'value': liq_detail.get('label', 'N/A'),
         'positive': liq_score < 50, 'score': liq_score},
        {'label': 'Số CP tăng/giảm', 'value': breadth_detail.get('advance_label', 'N/A'),
         'positive': ad_score < 50, 'score': ad_score},
        {'label': 'CP trên MA20', 'value': breadth_detail.get('ma20_label', 'N/A'),
         'positive': ma20_score < 50, 'score': ma20_score},
        {'label': 'Tham khảo: NN', 'value': 'Chỉ tham khảo',
         'positive': False, 'isRef': True},
    ]

    analysis = {
        'market_mode': market_mode,
        'mode_label': mode_label,
        'mode_emoji': mode_emoji,
        'description': description,
        'risk_score': risk_score,
        'allocation': allocation,
        'factors': factors,
        'raw_scores': {
            'vnindex_trend': round(trend_score),
            'liquidity': liq_score,
            'advance_decline': ad_score,
            'above_ma20': ma20_score,
        },
        'vnindex_detail': trend_detail,
        'breadth_detail': {
            'advance': breadth_detail.get('advance', 0),
            'decline': breadth_detail.get('decline', 0),
            'total_analyzed': breadth_detail.get('total_analyzed', 0),
            'above_ma20': breadth_detail.get('above_ma20', 0),
            'above_ma20_pct': breadth_detail.get('above_ma20_pct', 0),
        },
        'analyzed_at': datetime.now().isoformat(),
        'api_calls_used': 1,
    }

    print("\n" + "=" * 60)
    print(f"{mode_emoji} MARKET MODE: {mode_label} ({market_mode})")
    print(f"📊 Risk Score: {risk_score}/100")
    print(f"💰 Tỷ trọng khuyến nghị: {allocation}% cổ phiếu")
    print(f"📝 {description}")
    print(f"🔌 API calls: 1 (VN-Index only)")
    print("=" * 60 + "\n")

    return analysis


if __name__ == '__main__':
    print("🚀 Market Risk Analysis v2")
    print("   VN-Index: 1 API call | Breadth: từ file EOD\n")

    result = run_market_analysis()

    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'market_risk_latest.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved to {output_file}")
