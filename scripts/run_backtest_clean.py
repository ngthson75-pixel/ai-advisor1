#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST RUNNER - CLEAN VERSION

Suppress VNStock ads and fix encoding issues
"""

import sys
import os
import io
import warnings

# Force UTF-8 encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ['PYTHONIOENCODING'] = 'utf-8'

# Suppress warnings
warnings.filterwarnings('ignore')

# Redirect VNStock ads to null
class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass

# Temporarily suppress prints during import
original_stdout = sys.stdout
original_stderr = sys.stderr

sys.stdout = NullWriter()
sys.stderr = NullWriter()

# Import VNStock (ads will be suppressed)
from vnstock import Vnstock

# Restore output
sys.stdout = original_stdout
sys.stderr = original_stderr

# Now import backtest modules
from backtest_system import (
    BacktestEngine,
    StrategyBacktester,
    run_backtest
)

import json
from datetime import datetime, timedelta

def main():
    """Run backtest without ads"""
    
    # Configuration
    STOCK_CODES = [
        'VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC'
    ]
    
    # Backtest period (6 months)
    END_DATE = datetime.now().strftime('%Y-%m-%d')
    START_DATE = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    # Strategy parameters
    PARAMS = {
        'volume_multiplier': 3.0,
        'rsi_threshold': 70
    }
    
    # Initial capital
    INITIAL_CAPITAL = 100_000_000  # 100M VND
    
    # Run backtests
    results = {}
    
    print("=" * 60, file=sys.stderr)
    print("BACKTEST SYSTEM - STARTING", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Period: {START_DATE} to {END_DATE}", file=sys.stderr)
    print(f"Stocks: {STOCK_CODES}", file=sys.stderr)
    print(f"Capital: {INITIAL_CAPITAL:,} VND", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    
    # 1. Backtest Breakout strategy
    print("BACKTESTING BREAKOUT STRATEGY...", file=sys.stderr)
    results['breakout'] = run_backtest(
        strategy_type='breakout',
        stock_codes=STOCK_CODES,
        start_date=START_DATE,
        end_date=END_DATE,
        params=PARAMS,
        initial_capital=INITIAL_CAPITAL
    )
    
    print("", file=sys.stderr)
    print("BACKTESTING DIVERGENCE STRATEGY...", file=sys.stderr)
    
    # 2. Backtest Divergence strategy
    results['divergence'] = run_backtest(
        strategy_type='divergence',
        stock_codes=STOCK_CODES,
        start_date=START_DATE,
        end_date=END_DATE,
        params=PARAMS,
        initial_capital=INITIAL_CAPITAL
    )
    
    # Output results
    output = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'backtest_period': {
            'start': START_DATE,
            'end': END_DATE,
            'days': (datetime.now() - datetime.strptime(START_DATE, '%Y-%m-%d')).days
        },
        'results': results
    }
    
    # Print to stdout (for JSON capture)
    print(json.dumps(output, indent=2, default=str))
    
    # Summary to stderr
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("BACKTEST COMPLETE", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    if 'breakout' in results and 'metrics' in results['breakout']:
        b_metrics = results['breakout']['metrics']
        print(f"Breakout:  WR={b_metrics['win_rate']}%, PF={b_metrics['profit_factor']:.2f}", file=sys.stderr)
    
    if 'divergence' in results and 'metrics' in results['divergence']:
        d_metrics = results['divergence']['metrics']
        print(f"Divergence: WR={d_metrics['win_rate']}%, PF={d_metrics['profit_factor']:.2f}", file=sys.stderr)
    
    print("=" * 60, file=sys.stderr)


if __name__ == '__main__':
    main()
