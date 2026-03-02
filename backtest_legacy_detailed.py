# ================================================
# BACKTEST LEGACY DETAILED - PHÂN TÍCH SÂU PULLBACK & EMA CROSS
# File: backtest_legacy_detailed.py
# ĐÃ FIX TRIỆT ĐỂ LỖI: 'numpy.int64' object has no attribute 'strftime'
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

TP_PERCENT = 10.0
SL_PERCENT = 4.5
HOLD_DAYS  = 20

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
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, unit='ms')
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
            return None
            
        df = df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
        for col in ['Open','High','Low','Close']:
            if col in df.columns:
                df[col] = df[col] * 1000
                
        df = df.sort_index().dropna()
        # Ép index thành DatetimeIndex chuẩn
        df.index = pd.to_datetime(df.index)
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

def atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def classify_stock_type(price):
    if price >= 50000: return "Bluechip"
    elif price >= 20000: return "Midcap"
    else: return "Penny"

def classify_sector(ticker):
    sector_map = {
        'VCB':'Ngân hàng', 'BID':'Ngân hàng', 'CTG':'Ngân hàng', 'TCB':'Ngân hàng', 'MBB':'Ngân hàng',
        'ACB':'Ngân hàng', 'HDB':'Ngân hàng', 'SHB':'Ngân hàng', 'LPB':'Ngân hàng',
        'VHM':'BĐS', 'VIC':'BĐS', 'VRE':'BĐS', 'NVL':'BĐS', 'KDH':'BĐS',
        'HPG':'Sản xuất', 'HCM':'Chứng khoán', 'FPT':'Công nghệ', 'MWG':'Bán lẻ',
        'VNM':'Tiêu dùng', 'SAB':'Tiêu dùng', 'GAS':'Năng lượng', 'POW':'Năng lượng'
    }
    return sector_map.get(ticker, "Khác")

# ================== GENERATE SIGNALS + METADATA ==================
def generate_legacy_signals_detailed(df, ticker):
    signals = []
    df = df.copy()
    df['EMA20'] = ema(df['Close'], 20)
    df['EMA50'] = ema(df['Close'], 50)
    df['RSI'] = calculate_rsi(df)
    df['ATR'] = atr(df, 14)
    df['Vol_Ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
    df['Dist_EMA20'] = abs(df['Close'] - df['EMA20']) / df['EMA20']

    for i in range(50, len(df) - HOLD_DAYS):
        row = df.iloc[i]
        prev = df.iloc[i-1]

        # LẤY NGÀY AN TOÀN TỪ INDEX (đã ép datetime)
        signal_date = df.index[i]

        # Pullback
        if row['EMA20'] > row['EMA50'] and row['Dist_EMA20'] < 0.035 and row['RSI'] < 58:
            signals.append(create_trade_record(row, df, i, ticker, 'PULLBACK', signal_date))

        # EMA Cross
        if prev['EMA20'] <= prev['EMA50'] and row['EMA20'] > row['EMA50'] and 38 < row['RSI'] < 68:
            signals.append(create_trade_record(row, df, i, ticker, 'EMA_CROSS', signal_date))

    return signals

def create_trade_record(row, df, i, ticker, strategy, signal_date):
    entry = row['Close']
    tp = entry * (1 + TP_PERCENT/100)
    sl = entry * (1 - SL_PERCENT/100)

    future = df.iloc[i+1:i+HOLD_DAYS+1]
    exit_price = None
    exit_reason = "Time Exit"

    for _, r in future.iterrows():
        if r['Low'] <= sl:
            exit_price = sl
            exit_reason = "SL"
            break
        if r['High'] >= tp:
            exit_price = tp
            exit_reason = "TP"
            break

    if exit_price is None:
        exit_price = future.iloc[-1]['Close']

    pnl = (exit_price - entry) / entry * 100

    return {
        'ticker': ticker,
        'date': signal_date.strftime('%Y-%m-%d') if hasattr(signal_date, 'strftime') else str(signal_date),
        'strategy': strategy,
        'entry': round(entry, 0),
        'exit': round(exit_price, 0),
        'pnl': round(pnl, 2),
        'win': pnl > 0,
        'rsi': round(row['RSI'], 1),
        'vol_ratio': round(row['Vol_Ratio'], 2),
        'dist_ema20': round(row['Dist_EMA20'], 4),
        'atr_pct': round(row['ATR'] / row['Close'] * 100, 2),
        'stock_type': classify_stock_type(entry),
        'sector': classify_sector(ticker)
    }

# ================== RUN ==================
def run_detailed_backtest(sample=None):
    universe = TOP_343_STOCKS[:sample] if sample else TOP_343_STOCKS
    print(f"🚀 BẮT ĐẦU BACKTEST CHI TIẾT {len(universe)} MÃ\n")

    all_trades = []

    for i, ticker in enumerate(universe, 1):
        print(f"[{i:3d}/{len(universe)}] {ticker}...", end=" ")
        df = get_stock_data(ticker)
        if df is None:
            print("❌")
            continue
        trades = generate_legacy_signals_detailed(df, ticker)
        all_trades.extend(trades)
        print(f"✅ {len(trades)} signals")

    df = pd.DataFrame(all_trades)
    df.to_csv('legacy_detailed_trades.csv', index=False, encoding='utf-8-sig')
    
    print(f"\n✅ HOÀN TẤT!")
    print(f"   Tổng trades: {len(df)}")
    print(f"   File đã lưu: legacy_detailed_trades.csv")
    print(f"   Bây giờ bạn có thể chạy file analyze để phân tích sâu.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', type=int, default=None, help='Số mã test (ví dụ --sample 100)')
    args = parser.parse_args()
    run_detailed_backtest(args.sample)