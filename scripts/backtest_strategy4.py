#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRATEGY 4 BACKTEST: EMA Crossover (Golden Cross / Death Cross)

Entry: Golden Cross + Volume
Exit: Death Cross OR -3% Stop Loss
Hold: Until death cross (can be weeks/months)
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
from ema_crossover_scanner import EMACrossoverDetector


def backtest_stock(code, start_date, end_date, detector):
    """
    Backtest Strategy 4 on a single stock
    
    Simple strategy:
    - Entry: Golden Cross (EMA20 > EMA50) + Volume
    - Exit: Death Cross (EMA20 < EMA50) OR -3% stop loss
    - Hold: Until exit signal (can be long!)
    """
    
    try:
        # Get data
        stock = Vnstock().stock(symbol=code, source='VCI')
        df = stock.quote.history(
            symbol=code,
            start=start_date,
            end=end_date
        )
        
        if df.empty or len(df) < 60:
            return []
        
        # Detect signals
        df = detector.detect_signal(df)
        
        # Find golden cross signals (entries)
        golden_crosses = df[df['golden_cross'] == True].copy()
        
        if len(golden_crosses) == 0:
            return []
        
        # Execute trades
        trades = []
        
        for entry_idx, entry_row in golden_crosses.iterrows():
            # Entry details
            entry_date = entry_row.name
            entry_price = float(entry_row['close'])
            stop_loss = entry_price * 0.97  # -3%
            
            # Get future bars for exit simulation
            entry_loc = df.index.get_loc(entry_idx)
            future_bars = df.iloc[entry_loc + 1:]
            
            if len(future_bars) == 0:
                continue
            
            # Track trade
            exit_price = None
            exit_date = None
            exit_reason = None
            
            for future_idx, future_bar in future_bars.iterrows():
                current_price = float(future_bar['close'])
                current_low = float(future_bar['low'])
                
                # Check stop loss first (priority)
                if current_low <= stop_loss:
                    exit_price = stop_loss
                    exit_date = future_bar.name
                    exit_reason = 'STOP_LOSS'
                    break
                
                # Check death cross
                if future_bar['death_cross']:
                    exit_price = current_price
                    exit_date = future_bar.name
                    exit_reason = 'DEATH_CROSS'
                    break
            
            # If no exit signal, close at last bar
            if exit_price is None:
                last_bar = future_bars.iloc[-1]
                exit_price = float(last_bar['close'])
                exit_date = last_bar.name
                exit_reason = 'END_OF_DATA'
            
            # Calculate return
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            
            # Calculate hold days
            hold_days = (exit_date - entry_date).days if hasattr(exit_date, 'days') else 0
            
            trade = {
                'code': code,
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'return_pct': return_pct,
                'exit_reason': exit_reason,
                'stop_loss': stop_loss,
                'hold_days': hold_days,
                'ema20_entry': float(entry_row['ema20']),
                'ema50_entry': float(entry_row['ema50']),
                'volume_ratio': float(entry_row['volume'] / entry_row['avg_volume_20'])
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
    
    # Total return (assuming 20% position size per trade)
    total_return = sum(returns) * 0.20
    
    # Calculate hold days statistics
    hold_days = [t['hold_days'] for t in trades]
    avg_hold = np.mean(hold_days) if hold_days else 0
    
    # Calculate exit reasons
    death_cross_exits = sum(1 for t in trades if t['exit_reason'] == 'DEATH_CROSS')
    stop_loss_exits = sum(1 for t in trades if t['exit_reason'] == 'STOP_LOSS')
    
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
        'worst_trade': min(returns) if returns else 0,
        'avg_hold_days': avg_hold,
        'death_cross_exits': death_cross_exits,
        'stop_loss_exits': stop_loss_exits,
        'death_cross_pct': (death_cross_exits / len(trades)) * 100 if trades else 0,
        'stop_loss_pct': (stop_loss_exits / len(trades)) * 100 if trades else 0
    }


def main():
    """Run backtest on VN100"""
    
    # VN100 stocks
    STOCK_CODES = [
        # VN30 core
        'ACB', 'BCM', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
        'MBB', 'MSN', 'MWG', 'PLX', 'POW', 'REE', 'SAB', 'SHB', 'SSB', 'SSI',
        'STB', 'TCB', 'TPB', 'VCB', 'VHM', 'VIB', 'VIC', 'VJC', 'VNM', 'VPB',
        
        # Extended
        'DIG', 'DXG', 'KDH', 'NLG', 'PDR', 'VRE', 'VCG', 'CII', 'CTD', 'HDC',
        'HDG', 'KBC', 'SZL', 'TCH', 'PC1', 'VCI', 'VND', 'HCM', 'VIX', 'FTS',
        'BSI', 'CTS', 'ORS', 'AGR', 'EVF', 'DGC', 'DPM', 'DCM', 'DBC', 'GMD',
        'ANV', 'VHC', 'HSG', 'NKG', 'BMP', 'PHR', 'PAN', 'IMP', 'DHG', 'TRA',
        'BWE', 'NT2', 'TDM', 'VSH', 'GEG', 'GEX', 'GEE', 'FRT', 'DGW', 'CMG',
        'CTR', 'PET', 'VNA', 'SCS', 'HAH', 'VOS', 'PVT', 'PVD', 'PVS', 'HAG'
    ]
    
    START_DATE = '2025-01-02'
    END_DATE = '2025-12-17'
    
    print("=" * 70)
    print("STRATEGY 4: EMA CROSSOVER (GOLDEN/DEATH CROSS)")
    print("=" * 70)
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Stocks: {len(STOCK_CODES)} (VN100)")
    print("Entry: Golden Cross (EMA20 > EMA50) + Volume 1.2x")
    print("Exit: Death Cross (EMA20 < EMA50) OR Stop Loss -3%")
    print("=" * 70)
    print()
    
    # Initialize detector
    detector = EMACrossoverDetector(
        ema_fast=20,
        ema_slow=50,
        volume_multiplier=1.2
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
                      f"({trade['return_pct']:+.1f}%) [{trade['exit_reason']}] "
                      f"Hold: {trade['hold_days']} days", file=sys.stderr)
                all_trades.append(trade)
        else:
            print(f"    → No signals", file=sys.stderr)
    
    # Calculate metrics
    metrics = calculate_metrics(all_trades)
    
    print("\n" + "=" * 70)
    print("✅ RESULTS:")
    print("=" * 70)
    print(f"   Trades: {metrics['total_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.2f}%")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}x")
    print(f"   Total Return: {metrics['total_return']:.2f}%")
    print(f"   Avg Win: {metrics['avg_win']:.2f}%")
    print(f"   Avg Loss: {metrics['avg_loss']:.2f}%")
    print(f"   Best Trade: {metrics['best_trade']:.2f}%")
    print(f"   Worst Trade: {metrics['worst_trade']:.2f}%")
    print()
    print("   Hold Statistics:")
    print(f"   Average Hold: {metrics['avg_hold_days']:.1f} days")
    print()
    print("   Exit Analysis:")
    print(f"   Death Cross Exits: {metrics['death_cross_exits']} ({metrics['death_cross_pct']:.1f}%)")
    print(f"   Stop Loss Exits: {metrics['stop_loss_exits']} ({metrics['stop_loss_pct']:.1f}%)")
    print()


if __name__ == '__main__':
    main()
