#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRATEGY 2 BACKTEST: Breakout with Confirmation

Conservative approach với SL chặt, TP trailing
"""

import sys
import os
import io

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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

import pandas as pd
import numpy as np
from datetime import datetime
from breakout_confirmation_scanner import BreakoutConfirmationDetector


def backtest_stock(code, start_date, end_date, detector):
    """
    Backtest Strategy 2 on a single stock
    
    Risk Management:
    - Stop Loss: 2% below breakout level (TIGHT)
    - Take Profit: Trailing stop (2×ATR)
    - Position Size: 15% capital
    """
    
    try:
        # Get data
        stock = Vnstock().stock(symbol=code, source='VCI')
        df = stock.quote.history(
            symbol=code,
            start=start_date,
            end=end_date
        )
        
        if df.empty or len(df) < 30:
            return []
        
        # Detect signals
        df = detector.detect_signal(df)
        
        # Find buy signals
        signals = df[df['buy_signal'] == True].copy()
        
        if len(signals) == 0:
            return []
        
        # Execute trades
        trades = []
        
        for signal_idx, signal_row in signals.iterrows():
            # Entry details
            entry_date = signal_row.name
            entry_price = float(signal_row['close'])
            breakout_level = float(signal_row['breakout_level'])
            atr = float(signal_row['atr'])
            
            # Risk management
            stop_loss = breakout_level * 0.98  # 2% below breakout (TIGHT)
            trailing_distance = atr * 2  # Trailing stop distance
            
            # Get future bars for exit simulation
            entry_idx = df.index.get_loc(signal_idx)
            future_bars = df.iloc[entry_idx + 1:entry_idx + 61]  # Max 60 days hold
            
            if len(future_bars) == 0:
                continue
            
            # Track trade
            highest_price = entry_price
            exit_price = None
            exit_date = None
            exit_reason = None
            
            for future_idx, future_bar in future_bars.iterrows():
                current_price = float(future_bar['close'])
                current_high = float(future_bar['high'])
                current_low = float(future_bar['low'])
                
                # Update highest price
                if current_high > highest_price:
                    highest_price = current_high
                
                # Calculate trailing stop
                trailing_stop = highest_price - trailing_distance
                
                # Use tighter of: fixed SL or trailing SL
                effective_sl = max(stop_loss, trailing_stop)
                
                # Check stop loss
                if current_low <= effective_sl:
                    exit_price = effective_sl
                    exit_date = future_bar.name
                    
                    if effective_sl == stop_loss:
                        exit_reason = 'STOP_LOSS'
                    else:
                        exit_reason = 'TRAILING_STOP'
                    break
            
            # If no exit, close at last bar
            if exit_price is None:
                exit_price = float(future_bars.iloc[-1]['close'])
                exit_date = future_bars.iloc[-1].name
                exit_reason = 'END_OF_DATA'
            
            # Calculate return
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            trade = {
                'code': code,
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'return_pct': return_pct,
                'exit_reason': exit_reason,
                'breakout_level': breakout_level,
                'stop_loss': stop_loss,
                'confirmation': signal_row['confirmation'],
                'atr': atr
            }
            
            trades.append(trade)
        
        return trades
        
    except Exception as e:
        print(f"Error processing {code}: {e}", file=sys.stderr)
        return []


def calculate_metrics(trades):
    """Calculate performance metrics"""
    if not trades:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'total_return': 0
        }
    
    returns = [t['return_pct'] for t in trades]
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r < 0]
    
    win_rate = (len(wins) / len(returns)) * 100 if returns else 0
    
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Total return (assuming 15% position size per trade)
    total_return = sum(returns) * 0.15
    
    return {
        'total_trades': len(trades),
        'winning_trades': len(wins),
        'losing_trades': len(losses),
        'win_rate': win_rate,
        'avg_win': np.mean(wins) if wins else 0,
        'avg_loss': np.mean(losses) if losses else 0,
        'profit_factor': profit_factor,
        'total_return': total_return,
        'best_trade': max(returns) if returns else 0,
        'worst_trade': min(returns) if returns else 0
    }


def main():
    """Run backtest on VN100"""
    
    # VN100 stocks (same as before)
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
    
    START_DATE = '2025-01-02'
    END_DATE = '2025-12-17'
    
    print("=" * 60)
    print("STRATEGY 2: BREAKOUT WITH CONFIRMATION")
    print("=" * 60)
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Stocks: {', '.join(STOCK_CODES[:10])}... ({len(STOCK_CODES)} total)")
    print("Params: Consolidation 10d, Vol 2.0x, SL -2%, TP Trailing")
    print("=" * 60)
    print()
    
    # Initialize detector
    detector = BreakoutConfirmationDetector(
        consolidation_days=10,
        volume_multiplier=2.0,
        atr_threshold=0.7,
        breakout_lookback=20
    )
    
    # Run backtest
    all_trades = []
    
    for code in STOCK_CODES:
        print(f"\n  Testing {code}...", file=sys.stderr)
        
        trades = backtest_stock(code, START_DATE, END_DATE, detector)
        
        if trades:
            print(f"    → Found {len(trades)} signals", file=sys.stderr)
            for trade in trades:
                print(f"    → Trade: {trade['entry_price']:.0f} → {trade['exit_price']:.0f} "
                      f"({trade['return_pct']:+.1f}%) [{trade['exit_reason']}]", file=sys.stderr)
                all_trades.append(trade)
        else:
            print(f"    → No signals", file=sys.stderr)
    
    # Calculate metrics
    metrics = calculate_metrics(all_trades)
    
    print("\n" + "=" * 60)
    print("✅ RESULTS:")
    print("=" * 60)
    print(f"   Trades: {metrics['total_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.2f}%")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}x")
    print(f"   Total Return: {metrics['total_return']:.2f}%")
    print(f"   Avg Win: {metrics['avg_win']:.2f}%")
    print(f"   Avg Loss: {metrics['avg_loss']:.2f}%")
    print(f"   Best Trade: {metrics['best_trade']:.2f}%")
    print(f"   Worst Trade: {metrics['worst_trade']:.2f}%")
    print()
    
    # Save results
    if all_trades:
        df_trades = pd.DataFrame(all_trades)
        df_trades.to_csv('backtest_strategy2_results.csv', index=False)
        print(f"✅ Results saved to: backtest_strategy2_results.csv")
        print()


if __name__ == '__main__':
    main()
