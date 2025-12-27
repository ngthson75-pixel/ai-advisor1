#!/usr/bin/env python3
"""
PARAMETER OPTIMIZATION SYSTEM

Test nhiều parameter combinations để tìm optimal settings:
- Volume multiplier: 2.5x, 3.0x, 3.5x, 4.0x
- RSI threshold: 65, 70, 75, 80
- Stop loss: 3%, 5%, 7%
- Take profit: 6%, 8%, 10%

Goal: Maximize Sharpe ratio or win rate
"""

import json
import sys
from datetime import datetime, timedelta
from itertools import product
import pandas as pd

try:
    from backtest_system import run_backtest
except ImportError:
    print("Error: Cannot import backtest_system")
    sys.exit(1)


class ParameterOptimizer:
    """
    Grid search optimization for strategy parameters
    """
    
    def __init__(
        self,
        strategy_type: str,
        stock_codes: list,
        start_date: str,
        end_date: str,
        initial_capital: float = 100_000_000
    ):
        """
        Args:
            strategy_type: 'breakout' or 'divergence'
            stock_codes: List of stocks to test
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
        """
        self.strategy_type = strategy_type
        self.stock_codes = stock_codes
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        self.results = []
    
    def define_parameter_grid(self) -> list:
        """
        Define parameter combinations to test
        
        Returns:
            List of parameter dicts
        """
        # Parameter ranges
        volume_multipliers = [2.5, 3.0, 3.5, 4.0]
        rsi_thresholds = [65, 70, 75, 80]
        
        # Generate all combinations
        combinations = []
        
        for vol_mult, rsi_thresh in product(volume_multipliers, rsi_thresholds):
            combinations.append({
                'volume_multiplier': vol_mult,
                'rsi_threshold': rsi_thresh
            })
        
        return combinations
    
    def evaluate_params(self, params: dict) -> dict:
        """
        Evaluate one parameter combination
        
        Args:
            params: Parameter dict
            
        Returns:
            Results dict
        """
        print(f"Testing: vol={params['volume_multiplier']}x, rsi={params['rsi_threshold']}", file=sys.stderr)
        
        try:
            result = run_backtest(
                strategy_type=self.strategy_type,
                stock_codes=self.stock_codes,
                start_date=self.start_date,
                end_date=self.end_date,
                params=params,
                initial_capital=self.initial_capital
            )
            
            # Extract key metrics
            metrics = result['metrics']
            
            # Calculate score (weighted combination of metrics)
            score = self.calculate_score(metrics)
            
            return {
                'params': params,
                'metrics': metrics,
                'score': score
            }
            
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            return None
    
    def calculate_score(self, metrics: dict) -> float:
        """
        Calculate optimization score
        
        Weighted combination of:
        - Win rate (40%)
        - Profit factor (30%)
        - Total return (20%)
        - Max drawdown penalty (10%)
        
        Args:
            metrics: Performance metrics
            
        Returns:
            Score (0-100)
        """
        # Win rate component (0-40 points)
        win_rate_score = min(metrics['win_rate'] * 0.67, 40)  # 60% win rate = 40 pts
        
        # Profit factor component (0-30 points)
        profit_factor = min(metrics['profit_factor'], 3.0)  # Cap at 3.0
        pf_score = (profit_factor / 3.0) * 30
        
        # Total return component (0-20 points)
        total_return = max(metrics['total_return'], 0)
        return_score = min(total_return / 2, 20)  # 40% return = 20 pts
        
        # Max drawdown penalty (subtract up to 10 points)
        drawdown_penalty = min(abs(metrics['max_drawdown']) / 2, 10)
        
        # Total score
        score = win_rate_score + pf_score + return_score - drawdown_penalty
        
        return max(score, 0)
    
    def optimize(self) -> dict:
        """
        Run optimization
        
        Returns:
            Results with best parameters
        """
        print("=" * 60, file=sys.stderr)
        print("PARAMETER OPTIMIZATION", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"Strategy: {self.strategy_type}", file=sys.stderr)
        print(f"Period: {self.start_date} to {self.end_date}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("", file=sys.stderr)
        
        # Get parameter grid
        param_combinations = self.define_parameter_grid()
        
        print(f"Testing {len(param_combinations)} parameter combinations...", file=sys.stderr)
        print("", file=sys.stderr)
        
        # Test each combination
        self.results = []
        
        for i, params in enumerate(param_combinations, 1):
            print(f"[{i}/{len(param_combinations)}] ", file=sys.stderr, end='')
            
            result = self.evaluate_params(params)
            
            if result:
                self.results.append(result)
                print(f"  → Score: {result['score']:.2f}, Win rate: {result['metrics']['win_rate']}%", file=sys.stderr)
            else:
                print(f"  → Failed", file=sys.stderr)
        
        # Sort by score
        self.results.sort(key=lambda x: x['score'], reverse=True)
        
        # Get best parameters
        best = self.results[0] if self.results else None
        
        if best:
            print("", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print("BEST PARAMETERS FOUND", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(f"Volume multiplier: {best['params']['volume_multiplier']}x", file=sys.stderr)
            print(f"RSI threshold: {best['params']['rsi_threshold']}", file=sys.stderr)
            print(f"Score: {best['score']:.2f}", file=sys.stderr)
            print(f"Win rate: {best['metrics']['win_rate']}%", file=sys.stderr)
            print(f"Profit factor: {best['metrics']['profit_factor']}", file=sys.stderr)
            print(f"Total return: {best['metrics']['total_return']}%", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
        
        return {
            'strategy': self.strategy_type,
            'optimization_completed': datetime.now().isoformat(),
            'combinations_tested': len(param_combinations),
            'best_params': best['params'] if best else None,
            'best_score': best['score'] if best else 0,
            'best_metrics': best['metrics'] if best else None,
            'all_results': self.results[:10]  # Top 10 only
        }


def compare_strategies(
    stock_codes: list,
    start_date: str,
    end_date: str
) -> dict:
    """
    Optimize both strategies and compare
    
    Args:
        stock_codes: Stocks to test
        start_date: Start date
        end_date: End date
        
    Returns:
        Comparison results
    """
    results = {}
    
    # Optimize Breakout
    print("", file=sys.stderr)
    print("╔" + "═" * 58 + "╗", file=sys.stderr)
    print("║" + " " * 18 + "BREAKOUT STRATEGY" + " " * 23 + "║", file=sys.stderr)
    print("╚" + "═" * 58 + "╝", file=sys.stderr)
    
    breakout_optimizer = ParameterOptimizer(
        strategy_type='breakout',
        stock_codes=stock_codes,
        start_date=start_date,
        end_date=end_date
    )
    
    results['breakout'] = breakout_optimizer.optimize()
    
    # Optimize Divergence
    print("", file=sys.stderr)
    print("╔" + "═" * 58 + "╗", file=sys.stderr)
    print("║" + " " * 17 + "DIVERGENCE STRATEGY" + " " * 22 + "║", file=sys.stderr)
    print("╚" + "═" * 58 + "╝", file=sys.stderr)
    
    divergence_optimizer = ParameterOptimizer(
        strategy_type='divergence',
        stock_codes=stock_codes,
        start_date=start_date,
        end_date=end_date
    )
    
    results['divergence'] = divergence_optimizer.optimize()
    
    # Compare
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("STRATEGY COMPARISON", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    if results['breakout']['best_params'] and results['divergence']['best_params']:
        b_metrics = results['breakout']['best_metrics']
        d_metrics = results['divergence']['best_metrics']
        
        print("", file=sys.stderr)
        print("Metric                 | Breakout      | Divergence    | Winner", file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        
        # Win rate
        print(f"Win Rate               | {b_metrics['win_rate']:6.2f}%      | {d_metrics['win_rate']:6.2f}%      | ", file=sys.stderr, end='')
        print("Breakout" if b_metrics['win_rate'] > d_metrics['win_rate'] else "Divergence", file=sys.stderr)
        
        # Total return
        print(f"Total Return           | {b_metrics['total_return']:6.2f}%      | {d_metrics['total_return']:6.2f}%      | ", file=sys.stderr, end='')
        print("Breakout" if b_metrics['total_return'] > d_metrics['total_return'] else "Divergence", file=sys.stderr)
        
        # Profit factor
        print(f"Profit Factor          | {b_metrics['profit_factor']:6.2f}       | {d_metrics['profit_factor']:6.2f}       | ", file=sys.stderr, end='')
        print("Breakout" if b_metrics['profit_factor'] > d_metrics['profit_factor'] else "Divergence", file=sys.stderr)
        
        # Max drawdown
        print(f"Max Drawdown           | {b_metrics['max_drawdown']:6.2f}%      | {d_metrics['max_drawdown']:6.2f}%      | ", file=sys.stderr, end='')
        print("Breakout" if abs(b_metrics['max_drawdown']) < abs(d_metrics['max_drawdown']) else "Divergence", file=sys.stderr)
        
        print("-" * 60, file=sys.stderr)
        
        # Overall winner
        b_score = results['breakout']['best_score']
        d_score = results['divergence']['best_score']
        
        print(f"Overall Score          | {b_score:6.2f}       | {d_score:6.2f}       | ", file=sys.stderr, end='')
        print("BREAKOUT ✓" if b_score > d_score else "DIVERGENCE ✓", file=sys.stderr)
        
        print("=" * 60, file=sys.stderr)
    
    return {
        'success': True,
        'comparison_date': datetime.now().isoformat(),
        'period': {
            'start': start_date,
            'end': end_date
        },
        'stocks': stock_codes,
        'results': results
    }


def main():
    """Main optimization"""
    # Configuration
    STOCK_CODES = [
        'VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC'
    ]
    
    # Test period (6 months)
    END_DATE = datetime.now().strftime('%Y-%m-%d')
    START_DATE = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    # Run comparison
    results = compare_strategies(STOCK_CODES, START_DATE, END_DATE)
    
    # Output
    print(json.dumps(results, indent=2, default=str))


if __name__ == '__main__':
    main()
