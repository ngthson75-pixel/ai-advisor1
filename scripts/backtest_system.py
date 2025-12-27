#!/usr/bin/env python3
"""
COMPREHENSIVE BACKTESTING SYSTEM

Backtest both strategies:
1. Breakout (BUY)
2. Divergence (SELL)

Features:
- Historical data collection from VNStock
- Signal generation replay
- Trade simulation with realistic slippage
- Performance metrics calculation
- Detailed reporting
- Parameter optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
import os
from typing import Dict, List, Tuple

try:
    from vnstock import Vnstock
except ImportError:
    print("Error: vnstock not installed")
    sys.exit(1)


class BacktestEngine:
    """
    Core backtesting engine
    """
    
    def __init__(
        self,
        initial_capital=100_000_000,  # 100M VND
        position_size_pct=0.15,  # 15% per trade
        slippage_pct=0.001,  # 0.1% slippage
        commission_pct=0.0015  # 0.15% commission
    ):
        """
        Args:
            initial_capital: Starting capital
            position_size_pct: % of capital per trade
            slippage_pct: Slippage percentage
            commission_pct: Commission percentage
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position_size_pct = position_size_pct
        self.slippage_pct = slippage_pct
        self.commission_pct = commission_pct
        
        self.positions = []  # Open positions
        self.closed_trades = []  # Completed trades
        self.equity_curve = []  # Daily equity
        
    def enter_position(
        self,
        code: str,
        entry_date: datetime,
        entry_price: float,
        signal_type: str,
        stop_loss: float,
        take_profit: float,
        confidence: int
    ):
        """Enter a new position"""
        # Apply slippage
        actual_entry = entry_price * (1 + self.slippage_pct)
        
        # Calculate position size
        position_value = self.capital * self.position_size_pct
        shares = int(position_value / actual_entry)
        
        if shares <= 0:
            return None
        
        # Calculate costs
        trade_value = shares * actual_entry
        commission = trade_value * self.commission_pct
        total_cost = trade_value + commission
        
        # Check if enough capital
        if total_cost > self.capital:
            return None
        
        # Deduct from capital
        self.capital -= total_cost
        
        # Create position
        position = {
            'code': code,
            'entry_date': entry_date,
            'entry_price': actual_entry,
            'shares': shares,
            'signal_type': signal_type,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'entry_value': trade_value,
            'entry_commission': commission
        }
        
        self.positions.append(position)
        
        return position
    
    def exit_position(
        self,
        position: Dict,
        exit_date: datetime,
        exit_price: float,
        exit_reason: str
    ):
        """Exit an existing position"""
        # Apply slippage
        actual_exit = exit_price * (1 - self.slippage_pct)
        
        # Calculate proceeds
        proceeds = position['shares'] * actual_exit
        commission = proceeds * self.commission_pct
        net_proceeds = proceeds - commission
        
        # Calculate P&L
        profit = net_proceeds - position['entry_value']
        profit_pct = (profit / position['entry_value']) * 100
        
        # Add back to capital
        self.capital += net_proceeds
        
        # Record trade
        trade = {
            **position,
            'exit_date': exit_date,
            'exit_price': actual_exit,
            'exit_value': proceeds,
            'exit_commission': commission,
            'profit': profit,
            'profit_pct': profit_pct,
            'exit_reason': exit_reason,
            'hold_days': (exit_date - position['entry_date']).days
        }
        
        self.closed_trades.append(trade)
        
        # Remove from positions
        self.positions.remove(position)
        
        return trade
    
    def check_stops(self, current_date: datetime, current_prices: Dict[str, float]):
        """Check if any positions hit stop loss or take profit"""
        for position in self.positions[:]:  # Copy list to avoid modification during iteration
            code = position['code']
            
            if code not in current_prices:
                continue
            
            current_price = current_prices[code]
            
            # Check stop loss
            if current_price <= position['stop_loss']:
                self.exit_position(
                    position,
                    current_date,
                    current_price,
                    'STOP_LOSS'
                )
                continue
            
            # Check take profit
            if current_price >= position['take_profit']:
                self.exit_position(
                    position,
                    current_date,
                    current_price,
                    'TAKE_PROFIT'
                )
                continue
    
    def update_equity(self, current_date: datetime, current_prices: Dict[str, float]):
        """Update equity curve"""
        # Start with available capital
        equity = self.capital
        
        # Add unrealized P&L from open positions
        for position in self.positions:
            code = position['code']
            if code in current_prices:
                current_value = position['shares'] * current_prices[code]
                equity += current_value
        
        self.equity_curve.append({
            'date': current_date,
            'equity': equity,
            'open_positions': len(self.positions)
        })
    
    def get_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'final_capital': self.capital,
                'total_profit': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'max_profit': 0,
                'max_loss': 0,
                'expectancy': 0,
                'profit_factor': 0,
                'avg_hold_days': 0,
                'max_drawdown': 0
            }
        
        df = pd.DataFrame(self.closed_trades)
        
        # Basic metrics
        total_trades = len(df)
        winning_trades = len(df[df['profit'] > 0])
        losing_trades = len(df[df['profit'] <= 0])
        win_rate = (winning_trades / total_trades) * 100
        
        # Profit metrics
        total_profit = df['profit'].sum()
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        avg_profit = df[df['profit'] > 0]['profit_pct'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['profit'] <= 0]['profit_pct'].mean() if losing_trades > 0 else 0
        
        # Risk metrics
        max_profit = df['profit_pct'].max()
        max_loss = df['profit_pct'].min()
        
        # Expectancy
        if losing_trades > 0:
            expectancy = (win_rate/100 * avg_profit) + ((1-win_rate/100) * avg_loss)
        else:
            expectancy = avg_profit
        
        # Profit factor
        gross_profit = df[df['profit'] > 0]['profit'].sum()
        gross_loss = abs(df[df['profit'] <= 0]['profit'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average hold time
        avg_hold_days = df['hold_days'].mean()
        
        # Max drawdown
        equity_series = pd.DataFrame(self.equity_curve)['equity']
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_return': round(total_return, 2),
            'final_capital': round(self.capital, 2),
            'total_profit': round(total_profit, 2),
            'avg_profit': round(avg_profit, 2),
            'avg_loss': round(avg_loss, 2),
            'max_profit': round(max_profit, 2),
            'max_loss': round(max_loss, 2),
            'expectancy': round(expectancy, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_hold_days': round(avg_hold_days, 1),
            'max_drawdown': round(max_drawdown, 2)
        }


class StrategyBacktester:
    """
    Backtest specific strategies
    """
    
    def __init__(self, strategy_type: str, detector_class, params: Dict):
        """
        Args:
            strategy_type: 'breakout' or 'divergence'
            detector_class: Strategy detector class
            params: Strategy parameters
        """
        self.strategy_type = strategy_type
        self.detector_class = detector_class
        self.params = params
    
    def backtest_stock(
        self,
        code: str,
        start_date: str,
        end_date: str,
        engine: BacktestEngine
    ) -> List[Dict]:
        """
        Backtest strategy on one stock
        
        Returns:
            List of signals generated
        """
        print(f"  Backtesting {code}...", file=sys.stderr)
        
        # Fetch historical data
        try:
            stock = Vnstock().stock(symbol=code, source='VCI')
            df = stock.quote.history(
                symbol=code,
                start=start_date,
                end=end_date
            )
            
            if df.empty or len(df) < 50:
                print(f"    → Not enough data", file=sys.stderr)
                return []
            
            # Sort by date
            df = df.sort_values('time')
            df = df.reset_index(drop=True)
            
        except Exception as e:
            print(f"    → Error fetching data: {e}", file=sys.stderr)
            return []
        
        # Create detector
        detector = self.detector_class(**self.params)
        
        # Detect signals
        try:
            df = detector.detect_signal(df)
        except Exception as e:
            print(f"    → Error detecting signals: {e}", file=sys.stderr)
            return []
        
        # Find all signals
        signals = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            current_date = row['time']
            
            # Check for signal
            signal_col = 'buy_signal' if self.strategy_type == 'breakout' else 'sell_signal'
            
            if signal_col not in row or not row[signal_col]:
                # Check stops for existing positions on non-signal days
                if i < len(df) - 1:  # Not last bar
                    current_prices = {code: float(row['close'])}
                    engine.check_stops(current_date, current_prices)
                continue
            
            # Extract signal details
            signal = {
                'code': code,
                'date': row['time'],
                'close': float(row['close']),
                'high': float(row.get('high', row['close'])),
                'rsi': float(row['rsi']),
                'macd': float(row['macd']),
                'volume_ratio': float(row['volume_ratio']),
                'strategy': self.strategy_type
            }
            
            signals.append(signal)
            
            # Simulate trade
            if self.strategy_type == 'breakout':
                # BUY signal
                entry_price = signal['close']
                stop_loss = entry_price * 0.95  # 5% below
                take_profit = entry_price * 1.08  # 8% above
                
                position = engine.enter_position(
                    code=code,
                    entry_date=signal['date'],
                    entry_price=entry_price,
                    signal_type='BUY',
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    confidence=70  # Default
                )
                
                if position:
                    print(f"    → BUY signal @ {entry_price:,.0f}", file=sys.stderr)
                    
                    # Check stops on remaining bars
                    for j in range(i + 1, len(df)):
                        future_row = df.iloc[j]
                        future_date = future_row['time']
                        future_price = float(future_row['close'])
                        
                        current_prices = {code: future_price}
                        engine.check_stops(future_date, current_prices)
                        
                        # If position closed, break
                        if position not in engine.positions:
                            break
                
            else:
                # SELL signal (for this backtest, just close any open position in this stock)
                for pos in engine.positions[:]:
                    if pos['code'] == code:
                        engine.exit_position(
                            pos,
                            signal['date'],
                            signal['close'],
                            'SIGNAL_EXIT'
                        )
                        print(f"    → SELL signal @ {signal['close']:,.0f}", file=sys.stderr)
        
        return signals


def fetch_historical_data_batch(
    stock_codes: List[str],
    start_date: str,
    end_date: str
) -> Dict[str, pd.DataFrame]:
    """
    Fetch historical data for multiple stocks
    
    Returns:
        Dict mapping code to DataFrame
    """
    data = {}
    
    for code in stock_codes:
        try:
            stock = Vnstock().stock(symbol=code, source='VCI')
            df = stock.quote.history(
                symbol=code,
                start=start_date,
                end=end_date
            )
            
            if not df.empty and len(df) >= 50:
                df = df.sort_values('time')
                df = df.reset_index(drop=True)
                data[code] = df
                
        except Exception as e:
            print(f"Error fetching {code}: {e}", file=sys.stderr)
            continue
    
    return data


def run_backtest(
    strategy_type: str,
    stock_codes: List[str],
    start_date: str,
    end_date: str,
    params: Dict,
    initial_capital: float = 100_000_000
) -> Dict:
    """
    Run complete backtest for a strategy
    
    Args:
        strategy_type: 'breakout' or 'divergence'
        stock_codes: List of stocks to test
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        params: Strategy parameters
        initial_capital: Starting capital
        
    Returns:
        Backtest results
    """
    print("=" * 60, file=sys.stderr)
    print(f"BACKTESTING: {strategy_type.upper()}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Period: {start_date} to {end_date}", file=sys.stderr)
    print(f"Stocks: {len(stock_codes)}", file=sys.stderr)
    print(f"Capital: {initial_capital:,.0f} VND", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    
    # Import detector class
    if strategy_type == 'breakout':
        from breakout_scanner import BreakoutDetector
        detector_class = BreakoutDetector
    else:
        from divergence_scanner import BearishDivergenceDetector
        detector_class = BearishDivergenceDetector
    
    # Create engine
    engine = BacktestEngine(initial_capital=initial_capital)
    
    # Create strategy backtester
    strategy = StrategyBacktester(strategy_type, detector_class, params)
    
    # Backtest each stock
    all_signals = []
    
    for code in stock_codes:
        signals = strategy.backtest_stock(code, start_date, end_date, engine)
        all_signals.extend(signals)
    
    # Calculate metrics
    metrics = engine.get_metrics()
    
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("RESULTS", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Total trades: {metrics.get('total_trades', 0)}", file=sys.stderr)
    print(f"Win rate: {metrics.get('win_rate', 0)}%", file=sys.stderr)
    print(f"Total return: {metrics.get('total_return', 0)}%", file=sys.stderr)
    
    # Only print these if we have trades
    if metrics.get('total_trades', 0) > 0:
        print(f"Profit factor: {metrics.get('profit_factor', 0)}", file=sys.stderr)
        print(f"Max drawdown: {metrics.get('max_drawdown', 0)}%", file=sys.stderr)
    
    print("=" * 60, file=sys.stderr)
    
    return {
        'strategy': strategy_type,
        'params': params,
        'period': {
            'start': start_date,
            'end': end_date
        },
        'stocks': stock_codes,
        'metrics': metrics,
        'signals_generated': len(all_signals),
        'trades': engine.closed_trades,
        'equity_curve': engine.equity_curve
    }


def main():
    """
    Main backtest execution
    """
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
    
    # 1. Backtest Breakout strategy
    results['breakout'] = run_backtest(
        strategy_type='breakout',
        stock_codes=STOCK_CODES,
        start_date=START_DATE,
        end_date=END_DATE,
        params=PARAMS,
        initial_capital=INITIAL_CAPITAL
    )
    
    print("", file=sys.stderr)
    
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
    
    print(json.dumps(output, indent=2, default=str))


if __name__ == '__main__':
    main()
