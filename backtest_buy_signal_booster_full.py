# ================================================
# BACKTEST BUY SIGNAL BOOSTER - OPTIMIZED VERSION
# File: backtest_buy_signal_booster_optimized.py
# Trailing SL (5.5%/2.5%), TP 10%, Confidence >=65%, Volume 1.4x
# Thời gian quét ~20-25 phút + cache local
# ================================================

import pandas as pd
import numpy as np
import time
import argparse
import os
import json
from datetime import datetime, timedelta
import random
import warnings
warnings.filterwarnings('ignore')

# ================== CONFIG ==================
START_DATE = '2024-01-01'
END_DATE   = datetime.now().strftime('%Y-%m-%d')
CACHE_DIR  = 'data_cache'
os.makedirs(CACHE_DIR, exist_ok=True)

TP_PERCENT       = 10.0          # Tăng TP để cải thiện R:R
SL_PERCENT       = 4.5
HOLD_DAYS        = 20
TRAILING_TRIGGER = 5.5           # % tăng để bắt đầu trailing
TRAILING_OFFSET  = 2.5           # % trên entry để đặt trailing SL

WEIGHTS = {'legacy': 0.45, 'booster': 0.55}

# ================== DANH SÁCH 343 MÃ ==================
TOP_343_STOCKS = [
    'VCB', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB', 'STB', 'MSN',
    'FPT', 'VRE', 'SSI', 'BID', 'CTG', 'PLX', 'GAS', 'MWG', 'VJC', 'HDB',
    'BSR', 'POW', 'SAB', 'NVL', 'BCM', 'KDH', 'DGC', 'REE', 'TPB', 'ACB',
    'GVR', 'PNJ', 'VGC', 'DHG', 'DPM', 'GMD', 'SHB', 'LPB', 'VCI', 'TCX',
    'BVH', 'HVN', 'BMP', 'DXG', 'VPL', 'KBC', 'DIG', 'GEX', 'VIB', 'EIB',
    'VPI', 'HT1', 'HSG', 'DCM', 'NT2', 'HNG', 'VND', 'VCG', 'SBT', 'EVF',
    'DBC', 'HCM', 'CTD', 'PC1', 'DGW', 'SZC', 'CTR', 'MCH', 'VIX', 'HDG',
    'PPC', 'VSC', 'BWE', 'VCK', 'VDS', 'VSH', 'VTP', 'SCS', 'CNG', 'PVD',
    'PVT', 'VOS', 'CSV', 'PVS', 'NLG', 'VCF', 'CMG', 'TCH', 'PAN', 'SGN',
    'PHR', 'NBB', 'DPR', 'DVP', 'NHA', 'GEG', 'CII', 'PTB', 'NAF', 'HAG',
    'CMX', 'ORS', 'HDC', 'DMC', 'KDC', 'TNG', 'HRC', 'SVC', 'TCL', 'KSB',
    'VHC', 'HHS', 'MSH', 'SSB', 'HAX', 'SZL', 'VTO', 'VPX', 'PET', 'PVP',
    'QCG', 'FRT', 'SJS', 'FCN', 'GEE', 'TRA', 'DSE', 'TCM', 'VGT', 'DHA',
    'GEL', 'PDN', 'PMG', 'GIL', 'VFC', 'CTI', 'PDR', 'IDC', 'KHG', 'MSB',
    'DXS', 'OCB', 'HAH', 'IJC', 'ANV', 'LCG', 'DPG', 'BAF', 'HPA', 'TV2',
    'SMC', 'CTF', 'KOS', 'SIP', 'ELC', 'BMI', 'NTL', 'TAL', 'DCL', 'BSI',
    'HSL', 'BFC', 'HQC', 'HTN', 'PDC', 'LSS', 'AGG', 'VIP', 'CDC', 'ASG',
    'ITC', 'TIP', 'ASM', 'VTB', 'PGC', 'SHI', 'SRC', 'TDH', 'DVN', 'GDT',
    'VLA', 'APH', 'VPG', 'VRC', 'HPX', 'CRE', 'PGI', 'TTF', 'TNT', 'VDP',
    'CSM', 'CTS', 'FMC', 'TCO', 'DLG', 'PGS', 'PAC', 'TMT', 'KLB', 'DC4',
    'GTA', 'PGT', 'ST8', 'TCR', 'TLG', 'LBM', 'GDW', 'THG', 'VNE', 'VNL',
    'HTI', 'HU1', 'NHH', 'HID', 'HU6', 'HVH', 'TDP', 'PNC', 'PTL', 'HDM',
    'VHL', 'IDI', 'TCW', 'VIM', 'CLC', 'SAM', 'EVG', 'PTI', 'FIT', 'SMA',
    'VIT', 'VGG', 'CRC', 'TSC', 'TLH', 'DRI', 'BCC', 'TYA', 'VE1', 'HBC',
    'OGC', 'YEG', 'VPH', 'VE9', 'VHG', 'VID', 'AAA', 'VIF', 'VIG', 'LDG',
    'CIG', 'DRH', 'DXV', 'TNI', 'ASP', 'HU3', 'HAP', 'PVX', 'PVS', 'VFS',
    'AAV', 'SHS', 'PVB', 'CEO', 'NNC', 'BVS', 'BAB', 'NVB', 'TIG', 'API',
    'AST', 'PVC', 'BVB', 'VTZ', 'VBB', 'PGB', 'VC3', 'ASG', 'MST', 'DST',
    'PVI', 'HUT', 'DVM', 'PTI', 'VIG', 'MIG', 'NRC', 'ABI', 'C69', 'PGI',
    'EVS', 'PSI', 'HBS', 'TVS', 'APS', 'IDJ', 'DL1', 'DTD', 'MBS', 'DXP',
    'LAS', 'VGS', 'L40', 'EVS', 'L18', 'NDN', 'VC2', 'LIG', 'VCS', 'SJE',
    'VHE', 'INN', 'DHT', 'DHA', 'NAG', 'VC7', 'IPA', 'L14', 'VIG', 'MBG',
    'LAS', 'LDP', 'BCC', 'PVG', 'DTD', 'DTT', 'NBC', 'KSV', 'PLC', 'PTC',
    'PVL', 'PVV', 'HGM', 'TIG', 'HLD', 'VE2', 'NBC', 'AMV', 'KSF', 'SD9',
    'OCH', 'PSD', 'VIG', 'VGG', 'VTB'
]

# ================== CACHE HELPER ==================
def load_cache(ticker):
    path = os.path.join(CACHE_DIR, f"{ticker}.json")
    if os.path.exists(path):
        try:
            df = pd.read_json(path, orient='split', date_unit='ms')
            print(f"  [CACHE] {ticker}")
            return df
        except:
            os.remove(path)
    return None

def save_cache(ticker, df):
    path = os.path.join(CACHE_DIR, f"{ticker}.json")
    df.to_json(path, orient='split', date_unit='ms')

# ================== GET DATA ==================
def get_stock_data(ticker, days=150):
    cached = load_cache(ticker)
    if cached is not None:
        return cached

    try:
        from vnstock import Quote
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
        
        quote = Quote(symbol=ticker, source='VCI')
        df = quote.history(start=start_date, end=end_date)
        
        if df is None or len(df) < 60:
            print(f"  {ticker} - dữ liệu không đủ")
            return None
            
        df = df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
        for col in ['Open','High','Low','Close']:
            if col in df.columns:
                df[col] = df[col] * 1000
                
        df = df.sort_index().dropna()
        save_cache(ticker, df)
        time.sleep(random.uniform(0.8, 1.5))
        return df
    except Exception as e:
        print(f"  {ticker} lỗi: {str(e)[:80]}...")
        time.sleep(3.5)
        return None

# ================== HELPER FUNCTIONS ==================
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss.replace(0, 0.0001)
    return 100 - (100 / (1 + rs))

def macd(df):
    ema12 = ema(df['Close'], 12)
    ema26 = ema(df['Close'], 26)
    macd_line = ema12 - ema26
    signal_line = ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

# ================== LEGACY SIGNALS ==================
def generate_legacy_signals(df, ticker):
    signals = []
    df = df.copy()
    df['EMA20'] = ema(df['Close'], 20)
    df['EMA50'] = ema(df['Close'], 50)
    df['RSI'] = calculate_rsi(df)

    for i in range(50, len(df) - HOLD_DAYS):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # Pullback
        if row['EMA20'] > row['EMA50'] and \
           abs(row['Close'] - row['EMA20']) / row['EMA20'] < 0.035 and \
           row['RSI'] < 58:
            signals.append({'date': row.name, 'ticker': ticker, 'type': 'PULLBACK', 
                            'entry': row['Close'], 'strength': 72})

        # EMA Cross
        if prev['EMA20'] <= prev['EMA50'] and row['EMA20'] > row['EMA50'] and \
           38 < row['RSI'] < 68:
            signals.append({'date': row.name, 'ticker': ticker, 'type': 'EMA_CROSS', 
                            'entry': row['Close'], 'strength': 78})
    return signals

# ================== BOOSTER FILTERS (nới lỏng) ==================
def apply_booster_filters(df, idx, ticker):
    row = df.iloc[idx]
    score = 0
    reasons = []

    # 1. Market Regime
    if row['Close'] > ema(df['Close'], 50).iloc[-1]:
        score += 20
        reasons.append("Market OK")

    # 2. Volume Surge (nới lỏng 1.4x)
    avg_vol = df['Volume'].iloc[max(0, idx-20):idx].mean()
    if row['Volume'] > avg_vol * 1.4 and row['Close'] > 10000:
        score += 22
        reasons.append("Volume OK")

    # 3. MACD Confirmation
    macd_line, signal_line, hist = macd(df.iloc[:idx+1])
    if hist.iloc[-1] > 0 and macd_line.iloc[-1] > signal_line.iloc[-1]:
        score += 25
        reasons.append("MACD OK")

    # 4. Sector Strength (danh sách mở rộng)
    strong_tickers = {'VCB','BID','CTG','TCB','MBB','ACB','HDB','VHM','VIC','VRE','HPG','FPT','MWG','PNJ','SAB','GAS','MSN'}
    if ticker in strong_tickers:
        score += 13
        reasons.append("Sector OK")

    return min(100, score), reasons

# ================== BACKTEST ENGINE ==================
def run_backtest(sample=None):
    universe = TOP_343_STOCKS[:sample] if sample else TOP_343_STOCKS
    print(f"🚀 BẮT ĐẦU BACKTEST {len(universe)} MÃ (Optimized Trailing SL)\n")

    legacy_trades = []
    boosted_trades = []

    for i, ticker in enumerate(universe, 1):
        print(f"[{i:3d}/{len(universe)}] {ticker}...", end=" ")
        df = get_stock_data(ticker)
        if df is None:
            print("❌ No data")
            continue

        legacy_signals = generate_legacy_signals(df, ticker)

        for sig in legacy_signals:
            try:
                idx = df.index.get_loc(sig['date'])
            except KeyError:
                continue

            entry = sig['entry']
            tp = entry * (1 + TP_PERCENT/100)
            initial_sl = entry * (1 - SL_PERCENT/100)
            trailing_sl = initial_sl
            max_price = entry

            future = df.iloc[idx+1:idx+HOLD_DAYS+1]
            if len(future) == 0:
                continue

            exit_price = None
            exit_reason = "Time Exit"

            for _, row in future.iterrows():
                max_price = max(max_price, row['High'])

                # Trailing SL
                if max_price >= entry * (1 + TRAILING_TRIGGER/100):
                    trailing_sl = max(trailing_sl, entry * (1 + TRAILING_OFFSET/100))

                if row['Low'] <= trailing_sl:
                    exit_price = trailing_sl
                    exit_reason = "Trailing SL"
                    break
                if row['High'] >= tp:
                    exit_price = tp
                    exit_reason = "TP"
                    break

            if exit_price is None:
                exit_price = future.iloc[-1]['Close']
                exit_reason = "Time Exit"

            pnl = (exit_price - entry) / entry * 100

            trade = {
                'ticker': ticker,
                'entry_date': sig['date'],
                'entry': entry,
                'exit': exit_price,
                'pnl': pnl,
                'exit_reason': exit_reason,
                'type': sig['type']
            }

            legacy_trades.append(trade)

            # Boosted
            booster_score, reasons = apply_booster_filters(df, idx, ticker)
            final_confidence = round(sig['strength'] * WEIGHTS['legacy'] + booster_score * WEIGHTS['booster'])

            if final_confidence >= 65:  # Ngưỡng mới
                boosted_trades.append(trade)

        print("✅")

    # ================== KẾT QUẢ ==================
    df_legacy = pd.DataFrame(legacy_trades)
    df_boosted = pd.DataFrame(boosted_trades)

    def stats(df, name):
        if len(df) == 0:
            return f"{name}: Không có trade"
        win_rate = (df['pnl'] > 0).mean() * 100
        avg_pnl = df['pnl'].mean()
        gross_profit = df[df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        return f"{name:8} | Trades: {len(df):5} | WinRate: {win_rate:5.1f}% | AvgPnL: {avg_pnl:+6.2f}% | PF: {pf:6.2f}"

    print("\n" + "="*90)
    print("          KẾT QUẢ BACKTEST BUY SIGNAL BOOSTER (Optimized)")
    print("="*90)
    print(stats(df_legacy, "LEGACY "))
    print(stats(df_boosted, "BOOSTED "))
    print("="*90)

    if len(df_boosted) > 0:
        df_boosted.to_csv('backtest_results_boosted_optimized.csv', index=False, encoding='utf-8-sig')
        print(f"Đã lưu {len(df_boosted)} trades BOOSTED vào backtest_results_boosted_optimized.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=None, help='Số mã test (ví dụ --sample 100)')
    args = parser.parse_args()
    run_backtest(args.sample)