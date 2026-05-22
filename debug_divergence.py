#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUG DIVERGENCE_FB — Xem tại sao mã không pass điều kiện
==========================================================
Chạy: python debug_divergence.py
      python debug_divergence.py --tickers VCB HPG FPT

Output: bảng thống kê từng mã fail ở điều kiện nào
        → giúp xác định điều kiện nào cần nới lỏng
"""

import os, sys, time, argparse
import pandas as pd
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'scripts'))

try:
    from vnstock import Quote
except ImportError:
    from vnstock3 import Quote

# ── Copy functions từ scanner ─────────────────────────────────────────
WATCHLIST_172 = [
    'VCB','BID','CTG','VHM','VIC','VNM','HPG','TCB','VPB','MBB',
    'STB','MSN','FPT','SSI','GAS','PLX','MWG','VJC','HDB','ACB',
    'VRE','BCM','POW','SAB','SHB','LPB','VIB','EIB','BVH','GVR',
    'TPB','NVL','KDH','DGC','REE','VCI','HVN','DIG','GEX','VIX',
    'BSR','GMD','PNJ','DPM','KBC','DXG','VPL','MSB','OCB','TCX',
    'HSG','DCM','HCM','VND','PC1','DGW','HDG','PVD','PVT','VTP',
    'SCS','TCH','NLG','CII','PDR','IDC','ANV','HAH','DBC','MCH',
    'CTD','HT1','VSC','BWE','PVS','VHC','SSB','FRT','ELC','BMI',
    'BSI','TV2','DPG','LCG','BAF','TNG','KSB','MSH','SBT','VCG',
    'CTR','SZC','PHR','GEG','PTB','HAX','FMC','CSV','TCM','CMG',
    'PAN','SGN','NTL','GIL','VFC','IDI','AAA','TLH','HBC','VPG',
    'CRE','CSM','ASM','HHS','PDC','PAC','TAL','KOS','SIP','ORS',
    'CMX','NBB','SMC','DCL','QCG','SJS','NAF','HAG','NHA','EVF',
    'VHG','HAP','ASG','SHS','MBS','VFS','CEO','NVB','VCS','HUT',
    'NDN','PLC','EVS','PSI','VC3','BVS','BAB','TIG','APS','IPA',
    'DXP','TVS','LIG','VHE','VC7','DTT','KSV','HLD','OCH','PVI',
    'MIG','PGB','DHT','API','NRC','MBG','SJE','INN','NAG','SD9',
    'AMV','IDJ',
]

def get_last_trading_day():
    d = datetime.now()
    if d.hour < 15:
        d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime('%Y-%m-%d')

def get_data(ticker):
    try:
        end   = get_last_trading_day()
        start = (datetime.strptime(end,'%Y-%m-%d') - timedelta(days=500)).strftime('%Y-%m-%d')
        q  = Quote(symbol=ticker, source='VCI')
        df = q.history(start=start, end=end)
        if df is None or len(df) == 0: return None
        df.columns = [c.lower() for c in df.columns]
        for col in ['open','high','low','close']:
            if col in df.columns and df[col].median() < 1000:
                df[col] = df[col] * 1000
        # Normalize column names for scanner compatibility
        df = df.rename(columns={'close':'Close','high':'High','low':'Low',
                                  'open':'Open','volume':'Volume'})
        return df.sort_values('time').reset_index(drop=True)
    except:
        return None

def calc_rsi(df, period=14):
    delta = df['Close'].diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

def calc_macd(df, fast=12, slow=26, sig=9):
    ema_f = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_s = df['Close'].ewm(span=slow, adjust=False).mean()
    macd  = ema_f - ema_s
    signal= macd.ewm(span=sig, adjust=False).mean()
    return macd, signal, macd - signal

def indicator_at_pivot(series, idx, window=3, use_min=True):
    lo = max(0, idx - window)
    hi = min(len(series) - 1, idx + window)
    sub = series.iloc[lo:hi+1]
    return float(sub.min() if use_min else sub.max())

def debug_divergence(df, ticker):
    """Trả về dict mô tả mã fail ở điều kiện nào, hoặc PASS."""
    N = len(df)
    if N < 160:
        return {'result': 'SKIP', 'reason': f'data<160 ({N})', 'ticker': ticker}

    df = df.copy()
    df['RSI']  = calc_rsi(df)
    macd_l, sig_l, hist = calc_macd(df)
    df['MACD_HIST'] = hist
    df['MACD_LINE'] = macd_l
    df['SIG_LINE']  = sig_l

    import numpy as np
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    if pd.isna(df['RSI'].iloc[-1]) or pd.isna(df['MACD_HIST'].iloc[-1]):
        return {'result': 'SKIP', 'reason': 'NaN RSI/MACD', 'ticker': ticker}

    close_s = df['Close']
    rsi_s   = df['RSI']
    hist_s  = df['MACD_HIST']
    h       = hist_s

    avg_vol_20 = float(df['Volume'].tail(20).mean())
    if avg_vol_20 < 200_000:
        return {'result': 'FAIL', 'reason': f'VOL<200k ({avg_vol_20/1e3:.0f}k)', 'ticker': ticker}

    # Pivot 2
    p2_s = max(0, N - 45)
    p2_e = N - 3
    if p2_e <= p2_s:
        return {'result': 'FAIL', 'reason': 'p2 window invalid', 'ticker': ticker}
    p2_local = int(close_s.iloc[p2_s:p2_e].values.argmin())
    p2_idx   = p2_s + p2_local
    p2_price = float(close_s.iloc[p2_idx])
    bars_p2  = N - 1 - p2_idx
    if bars_p2 < 3 or bars_p2 > 45:
        return {'result': 'FAIL', 'reason': f'bars_p2={bars_p2} (need 3-45)', 'ticker': ticker}

    # Pivot 1
    p1_s = max(0, N - 160)
    p1_e = max(0, N - 45)
    if p1_e <= p1_s + 5:
        return {'result': 'FAIL', 'reason': 'p1 window invalid', 'ticker': ticker}
    p1_local = int(rsi_s.iloc[p1_s:p1_e].values.argmin())
    p1_idx   = p1_s + p1_local
    p1_price = float(close_s.iloc[p1_idx])
    bars_p1  = N - 1 - p1_idx

    rsi1 = indicator_at_pivot(rsi_s,  p1_idx, window=3, use_min=True)
    rsi2 = indicator_at_pivot(rsi_s,  p2_idx, window=3, use_min=True)
    hist1= indicator_at_pivot(hist_s, p1_idx, window=3, use_min=True)
    hist2= indicator_at_pivot(hist_s, p2_idx, window=3, use_min=True)

    rsi_diff  = rsi2 - rsi1
    rsi_now   = float(rsi_s.iloc[-1])
    cur_close = float(close_s.iloc[-1])
    recovery  = (cur_close - p2_price) / p2_price * 100
    gap       = p2_idx - p1_idx

    # Check điều kiện từng bước
    info = {
        'ticker': ticker, 'result': 'PASS',
        'p1_bars_ago': bars_p1, 'p2_bars_ago': bars_p2,
        'p1_price': round(p1_price), 'p2_price': round(p2_price),
        'rsi1': round(rsi1,1), 'rsi2': round(rsi2,1),
        'rsi_diff': round(rsi_diff,1),
        'hist1': round(hist1,3), 'hist2': round(hist2,3),
        'gap': gap, 'rsi_now': round(rsi_now,1),
        'recovery_pct': round(recovery,1),
        'macd_1bar_up': bool(h.iloc[-1] > h.iloc[-2]),
        'reason': '',
    }

    if p2_price >= p1_price * 0.985:
        info.update(result='FAIL', reason=f'C1:price_LL p2({p2_price:.0f})>=p1({p1_price:.0f})×0.985')
    elif gap < 20:
        info.update(result='FAIL', reason=f'C2:gap={gap}<20')
    elif rsi_diff < 5.0:
        info.update(result='FAIL', reason=f'C3:rsi_diff={rsi_diff:.1f}<5')
    elif rsi1 >= 50:
        info.update(result='FAIL', reason=f'C4:rsi1={rsi1:.1f}>=50')
    elif rsi2 >= 58:
        info.update(result='FAIL', reason=f'C5:rsi2={rsi2:.1f}>=58')
    elif hist2 <= hist1:
        info.update(result='FAIL', reason=f'C6:hist2({hist2:.3f})<=hist1({hist1:.3f})')
    elif hist1 >= 0:
        info.update(result='FAIL', reason=f'C7:hist1={hist1:.3f}>=0 (not bearish)')
    elif not (h.iloc[-1] > h.iloc[-4]):
        info.update(result='FAIL', reason=f'C8:MACD_4bar_trend h[-1]({h.iloc[-1]:.3f})<=h[-4]({h.iloc[-4]:.3f})')
    elif not (30 <= rsi_now <= 68):
        info.update(result='FAIL', reason=f'C9:rsi_now={rsi_now:.1f} (need 30-68)')
    elif recovery < 0.5 or recovery > 25.0:
        info.update(result='FAIL', reason=f'C10:recovery={recovery:.1f}% (need 0.5-25%)')
    else:
        ema20 = float(df['EMA20'].iloc[-1])
        ema50 = float(df['EMA50'].iloc[-1])
        near_ema20 = cur_close > ema20 * 0.97
        if not near_ema20 and cur_close < ema50:
            info.update(result='FAIL', reason=f'C_EMA:price({cur_close:.0f})<EMA20×0.97({ema20*0.97:.0f}) & <EMA50({ema50:.0f})')

    return info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tickers', nargs='+', help='Danh sách mã cụ thể')
    parser.add_argument('--delay',   type=float, default=2.0)
    parser.add_argument('--show-fail', action='store_true', default=True,
                        help='Hiển thị chi tiết tất cả FAIL')
    args = parser.parse_args()

    tickers = args.tickers or WATCHLIST_172

    print("\n" + "=" * 75)
    print("🔍 DEBUG DIVERGENCE_FB — Tại sao không có tín hiệu?")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(tickers)} mã")
    print("=" * 75)

    results   = []
    fail_cnts = {}

    for i, ticker in enumerate(tickers, 1):
        print(f"  [{i:3d}/{len(tickers)}] {ticker:<6}", end='', flush=True)
        df = get_data(ticker)
        if df is None:
            print(" ✗ no data")
            results.append({'ticker': ticker, 'result': 'SKIP', 'reason': 'no data'})
            time.sleep(args.delay)
            continue

        info = debug_divergence(df, ticker)
        results.append(info)

        if info['result'] == 'PASS':
            print(f" ✅ PASS! rsi_diff={info['rsi_diff']} rec={info['recovery_pct']}% rsi_now={info['rsi_now']}")
        elif info['result'] == 'FAIL':
            reason_short = info['reason'].split(':')[0]
            fail_cnts[reason_short] = fail_cnts.get(reason_short, 0) + 1
            print(f" ✗ {info['reason']}")
        else:
            print(f" – {info['reason']}")

        time.sleep(args.delay)

    # ── Tổng kết ─────────────────────────────────────────────────────
    passed = [r for r in results if r['result'] == 'PASS']
    failed = [r for r in results if r['result'] == 'FAIL']
    skipped= [r for r in results if r['result'] == 'SKIP']

    print("\n" + "=" * 75)
    print("📊 TỔNG KẾT")
    print("=" * 75)
    print(f"  ✅ PASS : {len(passed)} mã  → {[r['ticker'] for r in passed]}")
    print(f"  ✗ FAIL : {len(failed)} mã")
    print(f"  – SKIP : {len(skipped)} mã")

    if passed:
        print(f"\n  🚀 Mã pass DIVERGENCE_FB:")
        for r in passed:
            print(f"     {r['ticker']} | RSI diff: {r['rsi_diff']}pt | "
                  f"Recovery: {r['recovery_pct']}% | RSI now: {r['rsi_now']}")

    print(f"\n  📋 Điều kiện bị fail nhiều nhất:")
    for cond, cnt in sorted(fail_cnts.items(), key=lambda x: -x[1]):
        bar = '█' * min(30, cnt)
        print(f"     {cond:<12} {bar} {cnt}")

    # Gợi ý nới lỏng
    if fail_cnts:
        top_fail = max(fail_cnts, key=fail_cnts.get)
        top_cnt  = fail_cnts[top_fail]
        pct      = top_cnt / max(len(failed), 1) * 100
        print(f"\n  💡 GỢI Ý: {top_cnt} mã ({pct:.0f}%) fail tại {top_fail}")

        suggestions = {
            'C5':  'rsi2 >= 58 → nới thành >= 65 (cho phép RSI đáy 2 cao hơn)',
            'C10': 'recovery > 25% → nới thành > 30-35% (thị trường đang hồi)',
            'C8':  'MACD not improving → bỏ hoặc dùng 4-bar trend thay vì 1-bar',
            'C9':  'rsi_now out of 30-68 → nới thành 25-75',
            'C3':  'rsi_diff < 5 → giảm threshold xuống 3pt',
            'C4':  'rsi1 >= 50 → nới thành >= 55',
            'C1':  'price không lower low → đây là điều kiện cốt lõi, nên giữ',
        }
        if top_fail in suggestions:
            print(f"  → {suggestions[top_fail]}")

    print("=" * 75 + "\n")


if __name__ == '__main__':
    main()
