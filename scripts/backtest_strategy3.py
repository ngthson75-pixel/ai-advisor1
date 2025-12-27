#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STRATEGY 3 BACKTEST: Trend Following + Pullback Entry

Multiple exit strategy: TP1 (+5%), TP2 (+10%), TP3 (Trailing EMA20)
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
from trend_pullback_scanner import TrendPullbackDetector


def backtest_stock(code, start_date, end_date, detector):
    """
    Backtest Strategy 3 on a single stock
    
    Multiple Exit Strategy:
    - TP1: +5% (sell 1/3)
    - TP2: +10% (sell 1/3)  
    - TP3: Trail with EMA20 (final 1/3)
    - SL: EMA50 - 1%
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
            ema50 = float(signal_row['ema50'])
            
            # Risk management
            stop_loss = ema50 * 0.99  # EMA50 - 1%
            tp1 = entry_price * 1.05  # +5%
            tp2 = entry_price * 1.10  # +10%
            
            # Get future bars
            entry_idx = df.index.get_loc(signal_idx)
            future_bars = df.iloc[entry_idx + 1:entry_idx + 61]  # Max 60 days
            
            if len(future_bars) == 0:
                continue
            
            # Track positions (3 parts: 33%, 33%, 34%)
            position_1 = 0.33  # First third
            position_2 = 0.33  # Second third
            position_3 = 0.34  # Final third (slightly larger for rounding)
            
            exits = []
            remaining_position = 1.0
            
            for future_idx, future_bar in future_bars.iterrows():
                current_high = float(future_bar['high'])
                current_low = float(future_bar['low'])
                current_close = float(future_bar['close'])
                current_ema20 = float(future_bar['ema20'])
                
                # Check TP1 (sell first 1/3)
                if remaining_position > 0.65 and current_high >= tp1:
                    exits.append({
                        'date': future_bar.name,
                        'price': tp1,
                        'portion': position_1,
                        'reason': 'TP1',
                        'return_pct': 5.0
                    })
                    remaining_position -= position_1
                
                # Check TP2 (sell second 1/3)
                if 0.30 < remaining_position <= 0.67 and current_high >= tp2:
                    exits.append({
                        'date': future_bar.name,
                        'price': tp2,
                        'portion': position_2,
                        'reason': 'TP2',
                        'return_pct': 10.0
                    })
                    remaining_position -= position_2
                
                # Check Stop Loss (for ALL remaining)
                if current_low <= stop_loss:
                    if remaining_position > 0:
                        return_pct = ((stop_loss - entry_price) / entry_price) * 100
                        exits.append({
                            'date': future_bar.name,
                            'price': stop_loss,
                            'portion': remaining_position,
                            'reason': 'STOP_LOSS',
                            'return_pct': return_pct
                        })
                        remaining_position = 0
                        break
                
                # Check Trailing Stop (EMA20) for final portion
                if remaining_position <= 0.35:  # Only final third left
                    if current_close < current_ema20:
                        # Exit at close
                        return_pct = ((current_close - entry_price) / entry_price) * 100
                        exits.append({
                            'date': future_bar.name,
                            'price': current_close,
                            'portion': remaining_position,
                            'reason': 'TRAILING_EMA20',
                            'return_pct': return_pct
                        })
                        remaining_position = 0
                        break
            
            # If still have position at end, close at last price
            if remaining_position > 0:
                last_bar = future_bars.iloc[-1]
                last_price = float(last_bar['close'])
                return_pct = ((last_price - entry_price) / entry_price) * 100
                exits.append({
                    'date': last_bar.name,
                    'price': last_price,
                    'portion': remaining_position,
                    'reason': 'END_OF_DATA',
                    'return_pct': return_pct
                })
            
            # Calculate total return (weighted average)
            if exits:
                total_return = sum(e['portion'] * e['return_pct'] for e in exits)
                
                trade = {
                    'code': code,
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'tp1': tp1,
                    'tp2': tp2,
                    'exits': exits,
                    'total_return': total_return,
                    'num_exits': len(exits),
                    'ema20': float(signal_row['ema20']),
                    'ema50': ema50,
                    'rsi': float(signal_row['rsi']),
                    'pullback_pct': float(signal_row['pullback_pct'])
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
    
    returns = [t['total_return'] for t in trades]
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r < 0]
    
    win_rate = (len(wins) / len(returns)) * 100 if returns else 0
    
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Total return (assuming 20% position size per trade)
    total_return = sum(returns) * 0.20
    
    # Calculate how many trades hit each TP
    tp1_hits = sum(1 for t in trades if any(e['reason'] == 'TP1' for e in t['exits']))
    tp2_hits = sum(1 for t in trades if any(e['reason'] == 'TP2' for e in t['exits']))
    trailing_exits = sum(1 for t in trades if any(e['reason'] == 'TRAILING_EMA20' for e in t['exits']))
    
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
        'tp1_hit_rate': (tp1_hits / len(trades)) * 100 if trades else 0,
        'tp2_hit_rate': (tp2_hits / len(trades)) * 100 if trades else 0,
        'trailing_rate': (trailing_exits / len(trades)) * 100 if trades else 0
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
    
    print("=" * 60)
    print("STRATEGY 3: TREND FOLLOWING + PULLBACK")
    print("=" * 60)
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Stocks: {len(STOCK_CODES)} (VN100)")
    print("Entry: EMA20>50, Pullback 3-8%, RSI 40-60, Vol 1.5x")
    print("Exit: TP1 +5% (1/3), TP2 +10% (1/3), Trail EMA20 (1/3)")
    print("=" * 60)
    print()
    
    # Initialize detector
    detector = TrendPullbackDetector(
        ema_short=20,
        ema_long=50,
        rsi_period=14,
        rsi_lower=40,
        rsi_upper=60,
        volume_multiplier=1.5,
        pullback_min=0.03,
        pullback_max=0.08
    )
    
    # Run backtest
    all_trades = []
    
    for code in STOCK_CODES:
        print(f"\n  Testing {code}...", file=sys.stderr)
        
        trades = backtest_stock(code, START_DATE, END_DATE, detector)
        
        if trades:
            print(f"    → Found {len(trades)} signals", file=sys.stderr)
            for trade in trades:
                print(f"    → Trade: {trade['entry_price']:.0f} → "
                      f"{trade['total_return']:+.1f}% "
                      f"({trade['num_exits']} exits)", file=sys.stderr)
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
    print("   Exit Analysis:")
    print(f"   TP1 (+5%) Hit: {metrics['tp1_hit_rate']:.1f}%")
    print(f"   TP2 (+10%) Hit: {metrics['tp2_hit_rate']:.1f}%")
    print(f"   Trailing Exit: {metrics['trailing_rate']:.1f}%")
    print()


if __name__ == '__main__':
    main()
