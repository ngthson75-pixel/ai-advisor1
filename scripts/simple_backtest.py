#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMPLIFIED BACKTEST - GUARANTEED TO WORK

Focus on getting trades to execute properly
"""

import sys
import os
import io
import warnings
import json
from datetime import datetime, timedelta
import pandas as pd

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ['PYTHONIOENCODING'] = 'utf-8'
warnings.filterwarnings('ignore')

# Suppress VNStock ads
class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass

original_stdout = sys.stdout
sys.stdout = NullWriter()

from vnstock import Vnstock

sys.stdout = original_stdout

from breakout_scanner import BreakoutDetector
from divergence_scanner import BearishDivergenceDetector


def simple_backtest(code, start_date, end_date, strategy='breakout'):
    """
    Simple backtest that definitely executes trades
    """
    print(f"\n  Testing {code}...", file=sys.stderr)
    
    # Fetch data
    try:
        stock = Vnstock().stock(symbol=code, source='VCI')
        df = stock.quote.history(symbol=code, start=start_date, end=end_date)
        
        if df.empty or len(df) < 50:
            print(f"    → Not enough data", file=sys.stderr)
            return []
            
    except Exception as e:
        print(f"    → Error: {e}", file=sys.stderr)
        return []
    
    # Detect signals
    if strategy == 'breakout':
        detector = BreakoutDetector(volume_multiplier=3.0, rsi_threshold=70)
        df = detector.detect_signal(df)
        signal_col = 'buy_signal'
    else:
        detector = BearishDivergenceDetector(volume_multiplier=3.0, rsi_threshold=70)
        df = detector.detect_signal(df)
        signal_col = 'sell_signal'
    
    # Find signals
    signals = df[df[signal_col] == True].copy()
    
    if len(signals) == 0:
        print(f"    → No signals", file=sys.stderr)
        return []
    
    print(f"    → Found {len(signals)} signals", file=sys.stderr)
    
    # Simulate trades
    trades = []
    
    for idx, signal_row in signals.iterrows():
        entry_date = signal_row['time']
        entry_price = float(signal_row['close'])
        
        # Calculate stops
        stop_loss = entry_price * 0.95  # 5% below
        take_profit = entry_price * 1.08  # 8% above
        
        # Find exit
        future_data = df[df['time'] > entry_date].copy()
        
        if len(future_data) == 0:
            continue  # No future data to exit
        
        exit_date = None
        exit_price = None
        exit_reason = None
        
        for future_idx, future_row in future_data.iterrows():
            current_price = float(future_row['close'])
            
            # Check stop loss
            if current_price <= stop_loss:
                exit_date = future_row['time']
                exit_price = stop_loss
                exit_reason = 'STOP_LOSS'
                break
            
            # Check take profit
            if current_price >= take_profit:
                exit_date = future_row['time']
                exit_price = take_profit
                exit_reason = 'TAKE_PROFIT'
                break
        
        # If no exit found, use last price
        if exit_date is None:
            exit_date = future_data.iloc[-1]['time']
            exit_price = float(future_data.iloc[-1]['close'])
            exit_reason = 'END_OF_DATA'
        
        # Calculate P&L
        profit_pct = ((exit_price - entry_price) / entry_price) * 100
        
        trade = {
            'code': code,
            'entry_date': str(entry_date),
            'entry_price': entry_price,
            'exit_date': str(exit_date),
            'exit_price': exit_price,
            'profit_pct': profit_pct,
            'exit_reason': exit_reason,
            'hold_days': (exit_date - entry_date).days if hasattr(exit_date, 'days') else 0
        }
        
        trades.append(trade)
        
        print(f"    → Trade: {entry_price:,.0f} → {exit_price:,.0f} ({profit_pct:+.1f}%) [{exit_reason}]", file=sys.stderr)
    
    return trades


def calculate_metrics(trades):
    """Calculate performance metrics"""
    if not trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'avg_profit': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'total_return': 0
        }
    
    df = pd.DataFrame(trades)
    
    total_trades = len(df)
    winning = df[df['profit_pct'] > 0]
    losing = df[df['profit_pct'] <= 0]
    
    winning_trades = len(winning)
    losing_trades = len(losing)
    win_rate = (winning_trades / total_trades) * 100
    
    avg_profit = winning['profit_pct'].mean() if len(winning) > 0 else 0
    avg_loss = losing['profit_pct'].mean() if len(losing) > 0 else 0
    
    gross_profit = winning['profit_pct'].sum() if len(winning) > 0 else 0
    gross_loss = abs(losing['profit_pct'].sum()) if len(losing) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Assume 15% position size
    total_return = df['profit_pct'].sum() * 0.15
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': round(win_rate, 2),
        'avg_profit': round(avg_profit, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 999,
        'total_return': round(total_return, 2)
    }


def main():
    """Run simplified backtest"""
    
    # VN100 stocks - extracted from uploaded document + popular additions
    STOCK_CODES = [
        # VN30 core (30 stocks)
        'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
        'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'REE', 'SAB', 'SHB', 'SSB', 'SSI',
        'STB', 'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB',
        
        # Real estate & Construction (15 stocks)
        'DIG', 'DXG', 'KDH', 'NLG', 'PDR', 'VRE', 'VCG', 'CII', 'CTD', 'HDC',
        'HDG', 'KBC', 'SZL', 'TCH', 'PC1',
        
        # Finance & Securities (10 stocks)
        'VCI', 'VND', 'HCM', 'VIX', 'FTS', 'BSI', 'CTS', 'ORS', 'AGR', 'EVF',
        
        # Manufacturing & Resources (15 stocks)
        'DGC', 'DPM', 'DCM', 'DBC', 'GMD', 'ANV', 'VHC', 'HSG', 'NKG', 'BMP',
        'PHR', 'PAN', 'IMP', 'DHG', 'TRA',
        
        # Energy & Utilities (7 stocks)
        'BWE', 'NT2', 'TDM', 'VSH', 'GEG', 'GEX', 'GEE',
        
        # Retail & Tech (5 stocks)
        'FRT', 'DGW', 'CMG', 'CTR', 'PET',
        
        # Transportation & Others (8 stocks)
        'VNA', 'SCS', 'HAH', 'VOS', 'PVT', 'PVD', 'PVS', 'HAG'
    ]
    
    # Total: 90 stocks (high quality selection from VN100)
    
    START_DATE = '2025-01-02'
    END_DATE = '2025-12-17'
    
    print("=" * 60, file=sys.stderr)
    print("SIMPLIFIED BACKTEST - STRICT PARAMS", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Period: {START_DATE} to {END_DATE}", file=sys.stderr)
    print(f"Stocks: {', '.join(STOCK_CODES)}", file=sys.stderr)
    print(f"Params: Vol 3.0x, RSI 70", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    results = {}
    
    # Breakout
    print("\n📊 BREAKOUT STRATEGY", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    
    breakout_trades = []
    for code in STOCK_CODES:
        trades = simple_backtest(code, START_DATE, END_DATE, 'breakout')
        breakout_trades.extend(trades)
    
    breakout_metrics = calculate_metrics(breakout_trades)
    
    print("\n✅ BREAKOUT RESULTS:", file=sys.stderr)
    print(f"   Trades: {breakout_metrics['total_trades']}", file=sys.stderr)
    print(f"   Win Rate: {breakout_metrics['win_rate']}%", file=sys.stderr)
    print(f"   Profit Factor: {breakout_metrics['profit_factor']}", file=sys.stderr)
    print(f"   Total Return: {breakout_metrics['total_return']}%", file=sys.stderr)
    
    results['breakout'] = {
        'metrics': breakout_metrics,
        'trades': breakout_trades
    }
    
    # Divergence
    print("\n📉 DIVERGENCE STRATEGY", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    
    divergence_trades = []
    for code in STOCK_CODES:
        trades = simple_backtest(code, START_DATE, END_DATE, 'divergence')
        divergence_trades.extend(trades)
    
    divergence_metrics = calculate_metrics(divergence_trades)
    
    print("\n✅ DIVERGENCE RESULTS:", file=sys.stderr)
    print(f"   Trades: {divergence_metrics['total_trades']}", file=sys.stderr)
    print(f"   Win Rate: {divergence_metrics['win_rate']}%", file=sys.stderr)
    print(f"   Profit Factor: {divergence_metrics['profit_factor']}", file=sys.stderr)
    print(f"   Total Return: {divergence_metrics['total_return']}%", file=sys.stderr)
    
    results['divergence'] = {
        'metrics': divergence_metrics,
        'trades': divergence_trades
    }
    
    # Output JSON
    output = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'period': {'start': START_DATE, 'end': END_DATE},
        'results': results
    }
    
    print(json.dumps(output, indent=2, default=str))
    
    print("\n" + "=" * 60, file=sys.stderr)
    print("🎉 BACKTEST COMPLETE!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == '__main__':
    main()
