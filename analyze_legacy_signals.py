# ================================================
# ANALYZE LEGACY SIGNALS - PHÂN TÍCH SÂU
# File: analyze_legacy_signals.py
# Yêu cầu: File legacy_detailed_trades.csv phải tồn tại
# ================================================

import pandas as pd
import numpy as np
import os

# ================== CONFIG ==================
CSV_FILE = 'legacy_detailed_trades.csv'

# ================== LOAD & KIỂM TRA ==================
def load_data():
    if not os.path.exists(CSV_FILE):
        print(f"❌ Không tìm thấy file: {CSV_FILE}")
        print("   Hãy chạy lại backtest_legacy_detailed.py trước!")
        exit(1)
    
    df = pd.read_csv(CSV_FILE)
    print(f"✅ Đã load {len(df):,} trades từ {CSV_FILE}")
    
    # Kiểm tra cột cần thiết
    required_cols = ['pnl', 'win', 'rsi', 'vol_ratio', 'dist_ema20', 'atr_pct', 'stock_type', 'sector', 'strategy']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"❌ Thiếu cột: {missing}")
        exit(1)
    
    return df

# ================== PHÂN TÍCH THEO NHÓM ==================
def analyze_group(df, group_col, group_name, bins=None, labels=None):
    if group_col not in df.columns:
        return
    
    print(f"\n{'='*70}")
    print(f"PHÂN TÍCH THEO {group_name.upper()}")
    print(f"{'='*70}")
    
    if bins is not None:
        df['group'] = pd.cut(df[group_col], bins=bins, labels=labels, include_lowest=True)
    else:
        df['group'] = df[group_col]
    
    stats = df.groupby('group').agg({
        'win': ['count', 'mean'],
        'pnl': ['mean', 'median', 'sum'],
    }).round(3)
    
    stats.columns = ['Trades', 'WinRate', 'AvgPnL', 'MedianPnL', 'TotalPnL']
    stats['WinRate'] = stats['WinRate'] * 100
    stats = stats.rename(columns={'mean': 'WinRate'})
    
    # Thêm Profit Factor đơn giản
    def pf(group):
        profit = group[group['pnl'] > 0]['pnl'].sum()
        loss = abs(group[group['pnl'] < 0]['pnl'].sum())
        return round(profit / loss, 2) if loss > 0 else float('inf')
    
    stats['PF'] = df.groupby('group').apply(pf)
    
    print(stats)
    
    # Top 5 nhóm tốt nhất theo AvgPnL
    print("\nTop 5 nhóm có AvgPnL cao nhất:")
    print(stats.sort_values('AvgPnL', ascending=False).head(5))

# ================== MAIN ==================
def main():
    df = load_data()
    
    # 1. Tổng quan
    print("\nTỔNG QUAN")
    print("- Tổng trades:", len(df))
    print("- Win Rate tổng:", round(df['win'].mean() * 100, 1), "%")
    print("- Avg PnL:", round(df['pnl'].mean(), 2), "%")
    print("- Profit Factor:", round(df[df['pnl']>0]['pnl'].sum() / abs(df[df['pnl']<0]['pnl'].sum()), 2))
    print("- Theo strategy:")
    print(df.groupby('strategy')['win'].agg(['count', 'mean']).rename(columns={'mean':'WinRate'}) * [1, 100])
    
    # 2. Phân tích theo RSI
    rsi_bins = [-np.inf, 40, 50, 60, np.inf]
    rsi_labels = ['<40', '40-50', '50-60', '>60']
    analyze_group(df, 'rsi', 'RSI', rsi_bins, rsi_labels)
    
    # 3. Theo Vol Ratio
    vol_bins = [-np.inf, 1.0, 1.5, 2.0, np.inf]
    vol_labels = ['<1.0', '1.0-1.5', '1.5-2.0', '>2.0']
    analyze_group(df, 'vol_ratio', 'Volume Ratio', vol_bins, vol_labels)
    
    # 4. Theo Dist_EMA20 (khoảng cách giá đến EMA20)
    dist_bins = [-np.inf, 0.01, 0.02, 0.035, np.inf]
    dist_labels = ['<1%', '1-2%', '2-3.5%', '>3.5%']
    analyze_group(df, 'dist_ema20', 'Dist to EMA20 (%)', dist_bins, dist_labels)
    
    # 5. Theo ATR %
    atr_bins = [-np.inf, 1.5, 2.5, 4.0, np.inf]
    atr_labels = ['<1.5%', '1.5-2.5%', '2.5-4.0%', '>4.0%']
    analyze_group(df, 'atr_pct', 'ATR % (biến động)', atr_bins, atr_labels)
    
    # 6. Theo Loại cổ phiếu
    analyze_group(df, 'stock_type', 'Loại cổ phiếu (Bluechip/Midcap/Penny)')
    
    # 7. Theo Ngành (Sector)
    analyze_group(df, 'sector', 'Ngành/Nhóm ngành')
    
    # 8. Theo Strategy
    analyze_group(df, 'strategy', 'Chiến lược (PULLBACK / EMA_CROSS)')

if __name__ == "__main__":
    main()