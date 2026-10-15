#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR — SELL SIGNAL SCANNER v6.0 (2026-10-11)
==================================================
File DUY NHẤT cho máy quét BÁN. Thay thế:
  - sell_signal_scanner_v5_2.py  (bản "v5.4 DB-first" — logic được GIỮ NGUYÊN trong file này)
  - sell_signal_scanner_v5.2.py  (bản cũ đẩy qua API, không còn workflow nào chạy)

Nguồn giá: bảng eod_prices (update_eod_prices.py cập nhật trong phiên). Không phụ thuộc vnstock.

LUẬT BÁN (giữ nguyên v5.4):
  1. STOP LOSS: giá <= cắt lỗ → bán 100%
  2. Daily MACD + RSI>80 + thủng hỗ trợ → 100%   (tạm tắt: chưa có dữ liệu nến — giữ code để bật lại)
  3. 1H volume climax → 100% · 4. 4H MACD + volume div → 50%   (tạm tắt, như v5.4)
  5. TAKE PROFIT: giá >= mục tiêu → bán 50% / 30% / phần còn lại

MỚI trong v6.0:
  - Quyền cổ tức/thưởng (corporate actions): áp dụng các quyền đang chờ TRƯỚC khi quét (chỉnh giá tín hiệu MUA);
    mã có quyền chưa áp dụng → KHÔNG xét cắt lỗ/chốt lời, báo admin.        (lỗi GMD 08/10, HDB 09/10)
  - Chặn cắt lỗ bất thường: giá thấp hơn cắt lỗ > 15% (không thể xảy ra trong 1 phiên) → không bán, báo admin.
  - Tín hiệu MUA thiếu signal_code → tự gán TICKER-ID; cập nhật vị thế theo id.  (lỗi bán lặp CNG/GMD)
  - Không ghi trùng lệnh bán cùng tín hiệu, cùng lý do, cùng ngày.
  - Ghi đủ created_at / exit_date cho lệnh bán; mỗi lệnh commit riêng (lỗi 1 mã không xóa lệnh mã khác).
  - Kết nối: DATABASE_URL hoặc DB_HOST/DB_NAME/DB_USER/DB_PASSWORD/DB_PORT.

Chạy:
  python sell_signal_scanner_v6.py              # trong giờ 9:30–15:30, hỏi xác nhận (CI: tự chạy)
  python sell_signal_scanner_v6.py --dry-run    # chỉ in, không ghi DB
  python sell_signal_scanner_v6.py --yes        # không hỏi xác nhận
  python sell_signal_scanner_v6.py --ignore-hours --dry-run   # thử ngoài giờ
"""

import os
import sys
import argparse
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import psycopg2
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv()

VERSION = '6.0'
ABNORMAL_GAP = 0.15          # giá thấp hơn cắt lỗ > 15% → bất thường (biên độ tối đa 1 phiên: HOSE 7%, HNX 10%, UPCoM 15%)


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def _db_params():
    url = os.getenv('DATABASE_URL', '')
    if url.startswith(('postgres://', 'postgresql://', 'postgresql+psycopg://', 'postgresql+psycopg2://')):
        url = url.replace('postgresql+psycopg2://', 'postgresql://').replace('postgresql+psycopg://', 'postgresql://')
        return {'dsn': url}
    host, name, user, pw = (os.getenv(k) for k in ('DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD'))
    missing = [k for k, v in (('DB_HOST', host), ('DB_NAME', name), ('DB_USER', user), ('DB_PASSWORD', pw)) if not v]
    if missing:
        raise ValueError(f"❌ Thiếu {', '.join(missing)} (hoặc DATABASE_URL) — kiểm tra GitHub Secrets / .env")
    return {'host': host, 'database': name, 'user': user, 'password': pw, 'port': int(os.getenv('DB_PORT', '5432'))}


def get_db_connection():
    p = _db_params()
    return psycopg2.connect(p['dsn']) if 'dsn' in p else psycopg2.connect(**p)


def _sa_url():
    p = _db_params()
    if 'dsn' in p:
        return p['dsn'].replace('postgres://', 'postgresql+psycopg2://', 1).replace('postgresql://', 'postgresql+psycopg2://', 1)
    return (f"postgresql+psycopg2://{urllib.parse.quote(p['user'])}:{urllib.parse.quote(p['password'])}"
            f"@{p['host']}:{p['port']}/{p['database']}")


def notify_admin(msg):
    token, chat = os.getenv('TELEGRAM_BOT_TOKEN', ''), os.getenv('ADMIN_TELEGRAM_CHAT_ID', '')
    if not token or not chat:
        return
    try:
        data = urllib.parse.urlencode({'chat_id': chat, 'text': msg}).encode()
        urllib.request.urlopen(f'https://api.telegram.org/bot{token}/sendMessage', data=data, timeout=15).read()
    except Exception as e:
        print(f"   ⚠️ Telegram lỗi: {e}")


# ============================================================================
# CORPORATE ACTIONS (quyền cổ tức / cổ phiếu thưởng)
# ============================================================================

def apply_corporate_actions():
    """Áp dụng các quyền 'detected' (chỉnh giá tín hiệu MUA, nến, danh mục mẫu) trước khi quét."""
    try:
        from sqlalchemy import create_engine
        import corporate_actions
    except Exception as e:
        print(f"   ℹ️ Bỏ qua áp dụng quyền tự động ({e.__class__.__name__}) — vẫn chặn mã có quyền chờ")
        return []
    try:
        eng = create_engine(_sa_url(), pool_pre_ping=True)
        done = corporate_actions.apply_pending(eng) or []
        for d in done:
            print(f"   🏷️ Đã áp dụng quyền {d.get('ticker')} (GDKHQ {d.get('ex_date')}, hệ số {float(d.get('factor', 1)):.4f})")
        return done
    except Exception as e:
        print(f"   ⚠️ Áp dụng quyền lỗi: {str(e)[:150]}")
        return []


def pending_corporate_actions(conn):
    """{ticker: ex_date} các quyền CHƯA áp dụng (detected / review / applying). Bảng chưa có → {}."""
    try:
        cur = conn.cursor()
        cur.execute("""SELECT ticker, MIN(ex_date) FROM corporate_actions
                       WHERE status IN ('detected', 'review', 'applying') GROUP BY ticker""")
        return {r[0]: str(r[1])[:10] for r in cur.fetchall()}
    except Exception:
        conn.rollback()
        return {}


# ============================================================================
# DATA RETRIEVAL - DB FIRST ARCHITECTURE (giữ nguyên v5.4)
# ============================================================================

def get_all_prices_from_db(tickers):
    """Lấy giá mới nhất cho tất cả mã từ eod_prices — 1 truy vấn. Returns {ticker: price_vnd}"""
    if not tickers:
        return {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholders = ','.join(['%s'] * len(tickers))
        cursor.execute(f"""
            SELECT ticker, price, trade_date, updated_at
            FROM eod_prices
            WHERE ticker IN ({placeholders})
        """, tickers)
        rows = cursor.fetchall()
        conn.close()

        prices = {}
        now_vn = datetime.utcnow() + timedelta(hours=7)
        for ticker, price, trade_date, updated_at in rows:
            prices[ticker] = float(price)
            if updated_at:
                age_minutes = (now_vn - updated_at).total_seconds() / 60
                if age_minutes > 120:
                    print(f"   ⚠️ {ticker}: giá cũ ({age_minutes:.0f} phút)")
        print(f"   📦 Giá từ DB: {len(prices)}/{len(set(tickers))} mã")
        return prices
    except Exception as e:
        print(f"   ❌ Lấy giá từ DB lỗi: {e}")
        return {}


def get_daily_data(ticker, days_back=100):
    """Tạm tắt (vnstock giới hạn tần suất) — trả None → chỉ xét cắt lỗ / chốt lời theo giá DB."""
    return None


def get_intraday_4h_data(ticker, days_back=15):
    """Tạm tắt."""
    return None


def get_intraday_1h_data(ticker, days_back=10):
    """Tạm tắt."""
    return None


# TECHNICAL INDICATOR CALCULATIONS
# ============================================================================

def calculate_macd(df):
    """
    Calculate MACD indicator
    
    Returns:
        DataFrame with macd, signal, histogram columns added
    """
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_histogram'] = histogram
    
    return df


def calculate_rsi(df, period=14):
    """
    Calculate RSI indicator
    
    Returns:
        DataFrame with rsi column added
    """
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    df['rsi'] = rsi
    
    return df


# ============================================================================
# EXIT CRITERION 1: DAILY MACD + RSI>80 + SUPPORT BREAK
# ============================================================================

def detect_macd_divergence(df, lookback=20):
    """
    Detect MACD bearish divergence
    
    Returns:
        dict: Divergence signal if detected, None otherwise
    """
    if len(df) < lookback:
        return None
    
    # Calculate MACD if not already done
    if 'macd' not in df.columns:
        df = calculate_macd(df)
    
    recent = df.tail(lookback)
    
    # Find price peaks
    price_peaks = []
    for i in range(1, len(recent) - 1):
        if (recent['close'].iloc[i] > recent['close'].iloc[i-1] and
            recent['close'].iloc[i] > recent['close'].iloc[i+1]):
            price_peaks.append({
                'idx': i,
                'price': recent['close'].iloc[i],
                'macd': recent['macd'].iloc[i]
            })
    
    if len(price_peaks) < 2:
        return None
    
    # Compare last 2 peaks
    peak1 = price_peaks[-2]
    peak2 = price_peaks[-1]
    
    # Bearish divergence: price higher, MACD lower
    price_higher = peak2['price'] > peak1['price']
    macd_lower = peak2['macd'] < peak1['macd']
    
    if price_higher and macd_lower:
        return {
            'detected': True,
            'peak1_price': peak1['price'],
            'peak2_price': peak2['price'],
            'peak1_macd': peak1['macd'],
            'peak2_macd': peak2['macd']
        }
    
    return None


def find_support_levels(df, window=50, threshold=0.02):
    """
    Find support levels using recent lows
    
    Args:
        df: Price dataframe
        window: Lookback period
        threshold: Price clustering threshold (2%)
    
    Returns:
        list: Support levels (top 3)
    """
    if len(df) < window:
        return []
    
    recent = df.tail(window)
    
    # Find local lows
    lows = []
    for i in range(1, len(recent) - 1):
        if (recent['low'].iloc[i] <= recent['low'].iloc[i-1] and
            recent['low'].iloc[i] <= recent['low'].iloc[i+1]):
            lows.append(recent['low'].iloc[i] * 1000)
    
    if len(lows) < 3:
        return []
    
    # Cluster lows
    from collections import Counter
    rounded_lows = [round(low / (low * threshold)) * (low * threshold) for low in lows]
    support_counter = Counter(rounded_lows)
    
    # Top 3 most tested levels
    top_supports = [s[0] for s in support_counter.most_common(3)]
    
    return top_supports


def check_support_break(df, support_levels):
    """
    Check if any support level is broken with volume confirmation
    
    Returns:
        dict: Break signal if detected
    """
    if not support_levels or len(df) < 2:
        return None
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    current_close = current['close'] * 1000
    prev_close = prev['close'] * 1000
    current_volume = current['volume']
    
    # Average volume (last 20 days)
    avg_volume = df['volume'].tail(20).mean()
    
    for support in support_levels:
        # Break conditions:
        # 1. Current close < support
        # 2. Previous close >= support (fresh break)
        # 3. Volume > 1.2x average (confirmation)
        
        if (current_close < support and
            prev_close >= support and
            current_volume > avg_volume * 1.2):
            
            break_pct = ((support - current_close) / support) * 100
            
            return {
                'detected': True,
                'support_level': support,
                'current_price': current_close,
                'break_pct': break_pct,
                'volume_ratio': current_volume / avg_volume
            }
    
    return None


def check_daily_critical_exit(df):
    """
    EXIT CRITERION 1: Daily MACD + RSI>80 + Support break
    → BÁN 100% (CRITICAL)
    
    Returns:
        dict: Exit signal if all 3 conditions met
    """
    if df is None or len(df) < 50:
        return None
    
    # Calculate indicators
    df = calculate_macd(df)
    df = calculate_rsi(df)
    
    # Check 1: MACD Divergence
    macd_div = detect_macd_divergence(df)
    
    # Check 2: RSI > 80
    current_rsi = df['rsi'].iloc[-1]
    rsi_extreme = current_rsi > 80
    
    # Check 3: Support Break
    supports = find_support_levels(df)
    support_break = check_support_break(df, supports)
    
    # All 3 must be TRUE
    if macd_div and rsi_extreme and support_break:
        return {
            'signal': 'DAILY_CRITICAL_EXIT',
            'macd_divergence': macd_div,
            'rsi': current_rsi,
            'support_break': support_break,
            'action': 'SELL',
            'exit_pct': 100,
            'urgency': 'CRITICAL',
            'note': f'Daily MACD div + RSI={current_rsi:.0f} + Support break @ {support_break["support_level"]:,.0f}',
            'confidence': 'EXTREME_HIGH'
        }
    
    return None


# ============================================================================
# EXIT CRITERION 2: 4H MACD + VOLUME DIVERGENCE
# ============================================================================

def detect_volume_divergence(df, lookback=20):
    """
    Detect volume divergence
    Price higher but volume lower = Weakness
    
    Returns:
        dict: Divergence signal if detected
    """
    if len(df) < lookback:
        return None
    
    recent = df.tail(lookback)
    
    # Find price peaks with volume
    peaks = []
    for i in range(1, len(recent) - 1):
        if (recent['close'].iloc[i] > recent['close'].iloc[i-1] and
            recent['close'].iloc[i] > recent['close'].iloc[i+1]):
            peaks.append({
                'idx': i,
                'price': recent['close'].iloc[i],
                'volume': recent['volume'].iloc[i]
            })
    
    if len(peaks) < 2:
        return None
    
    peak1 = peaks[-2]
    peak2 = peaks[-1]
    
    # Divergence: price higher, volume lower
    price_higher = peak2['price'] > peak1['price']
    volume_lower = peak2['volume'] < peak1['volume']
    
    if price_higher and volume_lower:
        volume_drop_pct = ((peak1['volume'] - peak2['volume']) / peak1['volume']) * 100
        
        return {
            'detected': True,
            'volume_drop_pct': volume_drop_pct,
            'peak1_volume': peak1['volume'],
            'peak2_volume': peak2['volume']
        }
    
    return None


def check_4h_medium_exit(df_4h):
    """
    EXIT CRITERION 2: 4H MACD + Volume divergence
    → BÁN 50% (HIGH)
    
    Returns:
        dict: Exit signal if both conditions met
    """
    if df_4h is None or len(df_4h) < 30:
        return None
    
    # Calculate MACD on 4H
    df_4h = calculate_macd(df_4h)
    
    # Check 1: MACD Divergence on 4H
    macd_div = detect_macd_divergence(df_4h, lookback=15)
    
    # Check 2: Volume Divergence
    vol_div = detect_volume_divergence(df_4h, lookback=15)
    
    # Both must be TRUE
    if macd_div and vol_div:
        return {
            'signal': '4H_MEDIUM_EXIT',
            'macd_divergence': macd_div,
            'volume_divergence': vol_div,
            'action': 'SELL',
            'exit_pct': 50,
            'urgency': 'HIGH',
            'note': f'4H MACD div + Volume drop {vol_div["volume_drop_pct"]:.0f}%',
            'confidence': 'HIGH'
        }
    
    return None


# ============================================================================
# EXIT CRITERION 3: 1H VOLUME CLIMAX (BSR PATTERN)
# ============================================================================

def detect_climax_volume_1h(df_1h, lookback_hours=40, volume_multiplier=2.5):
    """
    Detect volume climax on 1H chart (BSR pattern)
    Volume spike @ near high = Distribution
    
    Returns:
        dict: Climax signal if detected
    """
    if df_1h is None or len(df_1h) < lookback_hours:
        return None
    
    recent = df_1h.tail(lookback_hours + 1)
    current = recent.iloc[-1]
    
    current_price = current['close'] * 1000
    current_volume = current['volume']
    
    # Average volume (excluding current)
    avg_volume = recent['volume'].iloc[:-1].mean()
    
    # Recent high/low
    recent_high = recent['high'].max() * 1000
    recent_low = recent['low'].min() * 1000
    
    # Condition 1: Volume spike (>> average)
    volume_ratio = current_volume / avg_volume
    is_volume_spike = volume_ratio >= volume_multiplier
    
    if not is_volume_spike:
        return None
    
    # Condition 2: At/near high (top 10% of range)
    range_position = (current_price - recent_low) / (recent_high - recent_low)
    is_near_high = range_position >= 0.90
    
    if not is_near_high:
        return None
    
    # Condition 3: Uptrend before (check last 20 bars)
    if len(df_1h) >= 25:
        price_20h_ago = df_1h.iloc[-20]['close'] * 1000
        is_uptrend = current_price > price_20h_ago * 1.03
    else:
        is_uptrend = True
    
    if not is_uptrend:
        return None
    
    # CLIMAX DETECTED!
    return {
        'signal': '1H_VOLUME_CLIMAX',
        'current_price': current_price,
        'volume_ratio': volume_ratio,
        'range_position': range_position * 100,
        'action': 'SELL',
        'exit_pct': 100,
        'urgency': 'HIGH',
        'note': f'1H volume spike {volume_ratio:.1f}x @ top {range_position*100:.0f}%',
        'confidence': 'VERY_HIGH'
    }


def detect_distribution_pattern_1h(df_1h, lookback_hours=60):
    """
    Detect distribution pattern - Multiple volume spikes @ resistance
    BSR pattern: 2+ spikes in resistance zone
    
    Returns:
        dict: Distribution signal if detected
    """
    if df_1h is None or len(df_1h) < lookback_hours:
        return None
    
    recent = df_1h.tail(lookback_hours)
    
    # Find resistance zone (top 15%)
    recent_high = recent['high'].max() * 1000
    recent_low = recent['low'].min() * 1000
    resistance_zone = recent_high - (recent_high - recent_low) * 0.15
    
    # Find volume spikes in resistance
    avg_volume = recent['volume'].mean()
    spikes = []
    
    for i in range(len(recent)):
        bar = recent.iloc[i]
        price = bar['close'] * 1000
        volume = bar['volume']
        
        if price >= resistance_zone and volume > avg_volume * 2.0:
            spikes.append({
                'idx': i,
                'time': recent.index[i],
                'price': price,
                'volume': volume,
                'volume_ratio': volume / avg_volume
            })
    
    # Need at least 2 spikes
    if len(spikes) < 2:
        return None
    
    # Check time span (should be 4-40 hours)
    time_diff = (spikes[-1]['time'] - spikes[0]['time']).total_seconds() / 3600
    
    if not (4 <= time_diff <= 40):
        return None
    
    # Check if failed to make new high
    max_spike_price = max(s['price'] for s in spikes)
    current_price = recent['close'].iloc[-1] * 1000
    failed_new_high = current_price < max_spike_price * 0.97
    
    if failed_new_high:
        return {
            'signal': '1H_DISTRIBUTION_PATTERN',
            'num_spikes': len(spikes),
            'resistance_zone': resistance_zone,
            'time_span_hours': time_diff,
            'failed_new_high': True,
            'action': 'SELL',
            'exit_pct': 100,
            'urgency': 'CRITICAL',
            'note': f'{len(spikes)} volume spikes 1H @ resistance - Distribution!',
            'confidence': 'EXTREME_HIGH'
        }
    
    return None


def check_1h_climax_exit(df_1h):
    """
    EXIT CRITERION 3: 1H Volume Climax (BSR pattern)
    → BÁN 100% (HIGH)
    
    Checks both:
    - Distribution pattern (multiple spikes) - PRIORITY
    - Single climax (single spike)
    
    Returns:
        dict: Exit signal if detected
    """
    if df_1h is None:
        return None
    
    # Priority 1: Distribution pattern (stronger signal)
    distribution = detect_distribution_pattern_1h(df_1h)
    if distribution:
        return distribution
    
    # Priority 2: Single climax
    climax = detect_climax_volume_1h(df_1h)
    if climax:
        return climax
    
    return None



# ============================================================================
# MAIN SCANNER
# ============================================================================

def _sell(ticker, code, sid, reason, entry, price, sl, tp, pnl, qty, pos, note, urgency, details=None):
    d = {'ticker': ticker, 'signal_code': code, 'signal_id': sid, 'exit_reason': reason,
         'entry_price': entry, 'exit_price': price, 'stop_loss': sl, 'take_profit': tp,
         'profit_loss_pct': pnl, 'exit_quantity_pct': qty, 'position_pct': pos, 'note': note, 'urgency': urgency}
    if details:
        d['signal_details'] = details
    return d


def scan_for_sell_signals(dry_run=False):
    """
    Thứ tự ưu tiên (giữ nguyên v5.4):
      1. Cắt lỗ  2. Daily critical (tắt)  3. 1H climax (tắt)  4. 4H medium (tắt)  5. Chốt lời
    Trả về (signals_to_sell, blocked) — blocked: mã không xét vì quyền chưa áp dụng / giá bất thường.
    """
    print("\n" + "=" * 80)
    print(f"🔍 SELL SIGNAL SCANNER v{VERSION}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    if not dry_run:
        apply_corporate_actions()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ticker, signal_code, entry_price, stop_loss, take_profit, position_pct, date
        FROM signals
        WHERE action = 'BUY' AND status = 'open'
        ORDER BY ticker, id
    """)
    open_signals = cursor.fetchall()
    pending_ca = pending_corporate_actions(conn)

    # Tín hiệu thiếu signal_code → gán TICKER-ID (máy quét cũ không đóng được các tín hiệu này → bán lặp)
    missing = [(r[0], f"{r[1]}-{r[0]}") for r in open_signals if not r[2]]
    if missing and not dry_run:
        for sid, code in missing:
            cursor.execute("UPDATE signals SET signal_code = %s WHERE id = %s AND signal_code IS NULL", (code, sid))
        conn.commit()
        print(f"   🔧 Gán signal_code cho {len(missing)} tín hiệu MUA")
    conn.close()

    if not open_signals:
        print("\n✅ Không có tín hiệu MUA nào đang mở")
        return [], []

    print(f"\n📋 Kiểm tra {len(open_signals)} vị thế đang mở\n")
    db_prices = get_all_prices_from_db(sorted({r[1] for r in open_signals}))
    print()

    signals_to_sell, blocked = [], []
    for sid, ticker, signal_code, entry_price, stop_loss, take_profit, position_pct, entry_date in open_signals:
        code = signal_code or f"{ticker}-{sid}"
        position_pct = int(position_pct if position_pct is not None else 100)
        print(f"🔍 {ticker} ({code})...", end=" ")
        try:
            current_price = db_prices.get(ticker)
            if current_price is None:
                print("⚠️ Không có giá trong DB")
                continue
            entry_price = float(entry_price or 0)
            stop_loss = float(stop_loss or 0)
            take_profit = float(take_profit or 0)
            if entry_price <= 0:
                print("⚠️ Thiếu giá vào")
                continue

            # ── Quyền chưa áp dụng: giá DB đã điều chỉnh, giá tín hiệu chưa → không so sánh ──
            ex = pending_ca.get(ticker)
            if ex and str(entry_date or '')[:10] < ex:
                msg = f"{ticker} ({code}): có quyền GDKHQ {ex} chưa áp dụng — tạm không xét cắt lỗ/chốt lời"
                print(f"⏸️ {msg}")
                blocked.append(msg)
                continue

            df_daily = None  # phân tích kỹ thuật tạm tắt (như v5.4)
            pnl_pct = ((current_price - entry_price) / entry_price) * 100

            # PRIORITY 1: STOP LOSS
            if stop_loss > 0 and current_price <= stop_loss:
                if current_price < stop_loss * (1 - ABNORMAL_GAP):
                    msg = (f"{ticker} ({code}): giá {current_price:,.0f} thấp hơn cắt lỗ {stop_loss:,.0f} "
                           f"{(1 - current_price / stop_loss) * 100:.0f}% — nghi chia cổ tức/thưởng, KHÔNG bán, cần admin kiểm tra")
                    print(f"⛔ {msg}")
                    blocked.append(msg)
                    continue
                print(f"🚨 CẮT LỖ @ {current_price:,.0f}")
                signals_to_sell.append(_sell(ticker, code, sid, 'STOP_LOSS', entry_price, current_price, stop_loss,
                                             take_profit, pnl_pct, 100, position_pct, 'Stop loss triggered', 'CRITICAL'))
                continue

            # PRIORITY 2: DAILY CRITICAL EXIT (MACD + RSI>80 + thủng hỗ trợ → 100%)
            daily_exit = check_daily_critical_exit(df_daily) if df_daily is not None else None
            if daily_exit:
                print(f"🚨 DAILY CRITICAL! RSI={daily_exit['rsi']:.0f}")
                signals_to_sell.append(_sell(ticker, code, sid, 'DAILY_CRITICAL_EXIT', entry_price, current_price, stop_loss,
                                             take_profit, pnl_pct, 100, position_pct, daily_exit['note'], 'CRITICAL', daily_exit))
                continue

            # PRIORITY 3: 1H VOLUME CLIMAX → 100%
            df_1h = get_intraday_1h_data(ticker, days_back=10)
            if df_1h is not None:
                climax_1h = check_1h_climax_exit(df_1h)
                if climax_1h:
                    print(f"⚠️ 1H CLIMAX! {climax_1h['signal']}")
                    signals_to_sell.append(_sell(ticker, code, sid, climax_1h['signal'], entry_price, current_price, stop_loss,
                                                 take_profit, pnl_pct, climax_1h['exit_pct'], position_pct,
                                                 climax_1h['note'], climax_1h['urgency'], climax_1h))
                    continue

            # PRIORITY 4: 4H MEDIUM EXIT → 50%
            df_4h = get_intraday_4h_data(ticker, days_back=15)
            if df_4h is not None:
                medium_4h = check_4h_medium_exit(df_4h)
                if medium_4h:
                    print("⚠️ 4H MEDIUM! Bán 50%")
                    signals_to_sell.append(_sell(ticker, code, sid, '4H_MEDIUM_EXIT', entry_price, current_price, stop_loss,
                                                 take_profit, pnl_pct, 50, position_pct, medium_4h['note'], 'HIGH', medium_4h))
                    continue

            # PRIORITY 5: TAKE PROFIT
            if take_profit > 0 and current_price >= take_profit:
                if position_pct == 100:
                    exit_qty = 50
                elif position_pct == 50:
                    exit_qty = 30
                else:
                    exit_qty = position_pct
                print(f"✅ CHỐT LỜI! Bán {exit_qty}%")
                signals_to_sell.append(_sell(ticker, code, sid, 'TAKE_PROFIT', entry_price, current_price, stop_loss,
                                             take_profit, pnl_pct, exit_qty, position_pct,
                                             f'Take profit - exit {exit_qty}%', 'MEDIUM'))
                continue

            print(f"✅ Chưa có tín hiệu (P/L: {pnl_pct:+.2f}%)")
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()
            continue

    if signals_to_sell:
        print("\n" + "=" * 80)
        print(f"🚨 {len(signals_to_sell)} TÍN HIỆU BÁN")
        print("=" * 80)
        for sig in signals_to_sell:
            print(f"   {sig['ticker']}: {sig['exit_reason']} - Bán {sig['exit_quantity_pct']}% - {sig['urgency']}")
    else:
        print("\n✅ Không có tín hiệu bán")
    return signals_to_sell, blocked


# ============================================================================
# EXECUTE SELL SIGNALS
# ============================================================================

def execute_sell_signals(signals_to_sell):
    """Ghi lệnh bán + cập nhật vị thế MUA. Mỗi lệnh commit riêng; bỏ qua lệnh trùng trong ngày."""
    if not signals_to_sell:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    done = 0
    for sig in signals_to_sell:
        try:
            cursor.execute("""SELECT 1 FROM signals WHERE action = 'SELL' AND buy_signal_code = %s
                              AND exit_reason = %s AND status = 'executed' LIMIT 1""",
                           (sig['signal_code'], sig['exit_reason']))
            if cursor.fetchone():
                print(f"⏭️ {sig['ticker']}: đã có lệnh bán {sig['exit_reason']} cho tín hiệu này — bỏ qua")
                conn.rollback()
                continue

            f = lambda v: float(v) if v is not None else None
            cursor.execute("""
                INSERT INTO signals
                (ticker, action, entry_price, exit_price, stop_loss, take_profit,
                 profit_loss_pct, exit_quantity_pct, exit_reason, signal_code,
                 buy_signal_code, note, date, exit_date, status, created_at)
                VALUES (%s, 'SELL', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        CAST(CURRENT_DATE AS TEXT), CURRENT_DATE, 'executed', NOW())
            """, (
                sig['ticker'], f(sig['entry_price']), f(sig['exit_price']), f(sig['stop_loss']), f(sig['take_profit']),
                f(sig['profit_loss_pct']), int(sig['exit_quantity_pct']), sig['exit_reason'],
                f"{sig['ticker']}-SELL-{datetime.now().strftime('%Y%m%d%H%M')}",
                sig['signal_code'], sig['note'],
            ))

            new_position_pct = int(sig['position_pct'] - sig['exit_quantity_pct'])
            if new_position_pct <= 0:
                cursor.execute("UPDATE signals SET status = 'closed', position_pct = 0 WHERE id = %s", (sig['signal_id'],))
            else:
                cursor.execute("UPDATE signals SET position_pct = %s WHERE id = %s", (new_position_pct, sig['signal_id']))
            conn.commit()
            done += 1
            print(f"✅ {sig['ticker']}: đã ghi lệnh bán")
        except Exception as e:
            print(f"❌ {sig['ticker']}: lỗi - {e}")
            conn.rollback()
    conn.close()
    print(f"\n✅ Đã ghi {done}/{len(signals_to_sell)} lệnh bán")
    return done


# ============================================================================
# MAIN
# ============================================================================

def main():
    ap = argparse.ArgumentParser(description=f'Sell Signal Scanner v{VERSION}')
    ap.add_argument('--dry-run', action='store_true', help='Chỉ in kết quả, không ghi DB')
    ap.add_argument('--yes', action='store_true', help='Không hỏi xác nhận')
    ap.add_argument('--ignore-hours', action='store_true', help='Chạy cả ngoài giờ giao dịch')
    args = ap.parse_args()

    vn_tz = timezone(timedelta(hours=7))
    now_utc = datetime.now(timezone.utc)
    now_vn = now_utc.astimezone(vn_tz)
    print(f"🕐 UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')} | VN: {now_vn.strftime('%Y-%m-%d %H:%M:%S')}")

    if not args.ignore_hours:
        if now_vn.weekday() >= 5:
            print("📅 Cuối tuần — thị trường nghỉ. Thoát.")
            sys.exit(0)
        h, m = now_vn.hour, now_vn.minute
        if h < 9 or (h == 9 and m < 30):
            print(f"⏰ Trước giờ giao dịch ({now_vn.strftime('%H:%M')}) — máy quét chạy 9:30–15:30")
            sys.exit(0)
        if h > 15 or (h == 15 and m > 30):
            print(f"⏰ Sau giờ giao dịch ({now_vn.strftime('%H:%M')}) — máy quét chạy 9:30–15:30")
            sys.exit(0)

    sell_signals, blocked = scan_for_sell_signals(dry_run=args.dry_run)

    if blocked and not args.dry_run:
        notify_admin("⏸️ Máy quét BÁN tạm không xét các mã sau (cần admin kiểm tra):\n• " + "\n• ".join(blocked[:15]))

    if sell_signals:
        if args.dry_run:
            print("\n⚠️ DRY RUN — không ghi DB")
        elif args.yes or os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true':
            print(f"\n🤖 Tự động ghi {len(sell_signals)} lệnh bán")
            execute_sell_signals(sell_signals)
        else:
            response = input(f"\n⚠️ Ghi {len(sell_signals)} lệnh bán? (y/n): ")
            if response.lower() == 'y':
                execute_sell_signals(sell_signals)
            else:
                print("❌ Đã hủy — không ghi")

    print("\n✅ Hoàn tất")


if __name__ == '__main__':
    main()
