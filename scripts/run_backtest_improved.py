#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMPROVED BACKTEST RUNNER

With better error handling and date validation
"""

import sys
import os
import io
import warnings
import json
from datetime import datetime, timedelta

# Force UTF-8 encoding
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
original_stderr = sys.stderr

sys.stdout = NullWriter()
sys.stderr = NullWriter()

from vnstock import Vnstock

sys.stdout = original_stdout
sys.stderr = original_stderr

from backtest_system import (
    BacktestEngine,
    StrategyBacktester,
    run_backtest
)


def safe_run_backtest(strategy_type, stock_codes, start_date, end_date, params, initial_capital):
    """
    Run backtest with error handling
    """
    try:
        result = run_backtest(
            strategy_type=strategy_type,
            stock_codes=stock_codes,
            start_date=start_date,
            end_date=end_date,
            params=params,
            initial_capital=initial_capital
        )
        return result
    except Exception as e:
        print(f"ERROR in {strategy_type}: {e}", file=sys.stderr)
        return {
            'strategy': strategy_type,
            'error': str(e),
            'metrics': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'final_capital': initial_capital,
                'total_profit': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'max_profit': 0,
                'max_loss': 0,
                'expectancy': 0,
                'profit_factor': 0,
                'avg_hold_days': 0,
                'max_drawdown': 0
            },
            'trades': [],
            'equity_curve': []
        }


def main():
    """Run backtest with proper error handling"""
    
    # Configuration
    STOCK_CODES = [
        'VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC'
    ]
    
    # Use full year 2025 for maximum statistical significance
    # Full year = ~238 trading days, expected 100+ signals
    END_DATE = '2025-12-17'
    START_DATE = '2025-01-02'  # Full year 2025
    
    # Strategy parameters (STRICT - Quality over Quantity!)
    # Fewer signals = Higher accuracy = Better results
    PARAMS = {
        'volume_multiplier': 3.0,  # Strict: 200% volume increase
        'rsi_threshold': 70       # Strict: Only strong momentum
    }
    
    # Initial capital
    INITIAL_CAPITAL = 100_000_000  # 100M VND
    
    print("=" * 60, file=sys.stderr)
    print("BACKTEST SYSTEM - IMPROVED VERSION", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Period: {START_DATE} to {END_DATE}", file=sys.stderr)
    print(f"Stocks: {len(STOCK_CODES)} - {', '.join(STOCK_CODES)}", file=sys.stderr)
    print(f"Capital: {INITIAL_CAPITAL:,} VND", file=sys.stderr)
    print(f"Volume multiplier: {PARAMS['volume_multiplier']}x", file=sys.stderr)
    print(f"RSI threshold: {PARAMS['rsi_threshold']}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    
    results = {}
    
    # 1. Backtest Breakout strategy
    print("📊 BACKTESTING BREAKOUT STRATEGY...", file=sys.stderr)
    print("", file=sys.stderr)
    
    results['breakout'] = safe_run_backtest(
        strategy_type='breakout',
        stock_codes=STOCK_CODES,
        start_date=START_DATE,
        end_date=END_DATE,
        params=PARAMS,
        initial_capital=INITIAL_CAPITAL
    )
    
    if 'error' in results['breakout']:
        print(f"⚠️  Breakout backtest failed: {results['breakout']['error']}", file=sys.stderr)
    else:
        b_metrics = results['breakout']['metrics']
        print("", file=sys.stderr)
        print("✅ BREAKOUT RESULTS:", file=sys.stderr)
        print(f"   Trades: {b_metrics['total_trades']}", file=sys.stderr)
        print(f"   Win Rate: {b_metrics['win_rate']:.1f}%", file=sys.stderr)
        print(f"   Profit Factor: {b_metrics['profit_factor']:.2f}", file=sys.stderr)
        print(f"   Total Return: {b_metrics['total_return']:.1f}%", file=sys.stderr)
    
    print("", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    
    # 2. Backtest Divergence strategy
    print("📉 BACKTESTING DIVERGENCE STRATEGY...", file=sys.stderr)
    print("", file=sys.stderr)
    
    results['divergence'] = safe_run_backtest(
        strategy_type='divergence',
        stock_codes=STOCK_CODES,
        start_date=START_DATE,
        end_date=END_DATE,
        params=PARAMS,
        initial_capital=INITIAL_CAPITAL
    )
    
    if 'error' in results['divergence']:
        print(f"⚠️  Divergence backtest failed: {results['divergence']['error']}", file=sys.stderr)
    else:
        d_metrics = results['divergence']['metrics']
        print("", file=sys.stderr)
        print("✅ DIVERGENCE RESULTS:", file=sys.stderr)
        print(f"   Trades: {d_metrics['total_trades']}", file=sys.stderr)
        print(f"   Win Rate: {d_metrics['win_rate']:.1f}%", file=sys.stderr)
        print(f"   Profit Factor: {d_metrics['profit_factor']:.2f}", file=sys.stderr)
        print(f"   Total Return: {d_metrics['total_return']:.1f}%", file=sys.stderr)
    
    # Output JSON
    output = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'backtest_period': {
            'start': START_DATE,
            'end': END_DATE,
            'days': (datetime.strptime(END_DATE, '%Y-%m-%d') - 
                    datetime.strptime(START_DATE, '%Y-%m-%d')).days
        },
        'configuration': {
            'stocks': STOCK_CODES,
            'initial_capital': INITIAL_CAPITAL,
            'parameters': PARAMS
        },
        'results': results
    }
    
    print(json.dumps(output, indent=2, default=str))
    
    # Final summary
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("🎉 BACKTEST COMPLETE", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Comparison table
    if ('error' not in results['breakout'] and 
        'error' not in results['divergence'] and
        results['breakout']['metrics']['total_trades'] > 0):
        
        b = results['breakout']['metrics']
        d = results['divergence']['metrics']
        
        print("", file=sys.stderr)
        print("COMPARISON:", file=sys.stderr)
        print(f"{'Metric':<20} | {'Breakout':>12} | {'Divergence':>12} | {'Winner':>12}", file=sys.stderr)
        print("-" * 63, file=sys.stderr)
        print(f"{'Win Rate':<20} | {b['win_rate']:>11.1f}% | {d['win_rate']:>11.1f}% | {'Breakout' if b['win_rate'] > d['win_rate'] else 'Divergence':>12}", file=sys.stderr)
        print(f"{'Profit Factor':<20} | {b['profit_factor']:>12.2f} | {d['profit_factor']:>12.2f} | {'Breakout' if b['profit_factor'] > d['profit_factor'] else 'Divergence':>12}", file=sys.stderr)
        print(f"{'Total Return':<20} | {b['total_return']:>11.1f}% | {d['total_return']:>11.1f}% | {'Breakout' if b['total_return'] > d['total_return'] else 'Divergence':>12}", file=sys.stderr)
        
    elif results['breakout']['metrics']['total_trades'] == 0:
        print("", file=sys.stderr)
        print("⚠️  WARNING: No trades generated!", file=sys.stderr)
        print("", file=sys.stderr)
        print("Possible reasons:", file=sys.stderr)
        print("  1. Date range too short or no data available", file=sys.stderr)
        print("  2. Strategy parameters too strict", file=sys.stderr)
        print("  3. VNStock API returning wrong dates", file=sys.stderr)
        print("", file=sys.stderr)
        print("Suggestions:", file=sys.stderr)
        print("  1. Check date range in script (edit START_DATE/END_DATE)", file=sys.stderr)
        print("  2. Relax parameters (lower volume_multiplier or rsi_threshold)", file=sys.stderr)
        print("  3. Try different stocks or longer period", file=sys.stderr)
    
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    print("📄 Results saved to: backtest_results.json", file=sys.stderr)
    print("📊 Generate report: python generate_report.py backtest_results.json", file=sys.stderr)
    print("", file=sys.stderr)


if __name__ == '__main__':
    main()
