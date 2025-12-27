#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST 4 STRATEGIES - SỬ DỤNG DỮ LIỆU ĐÃ DOWNLOAD
Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com

Backtest 4 chiến lược trên dữ liệu PKL đã download sẵn
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import pickle
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths - TÌM TRONG FOLDER HIỆN TẠI
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(SCRIPT_DIR, "data")  # Folder chứa PKL files
RESULTS_FOLDER = os.path.join(SCRIPT_DIR, "backtest_results_4strategies")
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Backtest parameters
INITIAL_CAPITAL = 100_000_000  # 100 triệu VND
POSITION_SIZE = 0.2  # 20% vốn mỗi lệnh
COMMISSION = 0.0015  # 0.15% phí giao dịch
SLIPPAGE = 0.001  # 0.1% slippage

# Date range
START_DATE = "2023-01-01"
END_DATE = "2024-12-31"

# ============================================================================
# LOAD DATA FROM PKL
# ============================================================================

def load_data_from_pkl():
    """
    Load all stock data from PKL checkpoint files
    
    Returns:
        dict: {ticker: DataFrame}
    """
    print(f"\n📂 Loading data from: {DATA_FOLDER}")
    
    if not os.path.exists(DATA_FOLDER):
        print(f"❌ Folder not found: {DATA_FOLDER}")
        return {}
    
    # Find all PKL files
    pkl_files = []
    for file in os.listdir(DATA_FOLDER):
        if file.endswith('.pkl') and 'liquid_stocks' in file:
            pkl_files.append(os.path.join(DATA_FOLDER, file))
    
    if len(pkl_files) == 0:
        print(f"❌ No PKL files found in {DATA_FOLDER}")
        return {}
    
    print(f"✅ Found {len(pkl_files)} PKL files")
    
    # Load all data
    all_stocks_data = {}
    
    for pkl_file in sorted(pkl_files):
        print(f"   Loading: {os.path.basename(pkl_file)}...", end=" ")
        try:
            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)
            
            # Data structure: {ticker: DataFrame}
            if isinstance(data, dict):
                all_stocks_data.update(data)
                print(f"✅ {len(data)} stocks")
            else:
                print("⚠️ Unknown format")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Total stocks loaded: {len(all_stocks_data)}")
    
    return all_stocks_data


def prepare_dataframe(df, ticker):
    """
    Prepare DataFrame for backtesting
    
    Args:
        df: Raw DataFrame from PKL
        ticker: Stock ticker
    
    Returns:
        DataFrame: Prepared data with required columns
    """
    # Create a copy
    df = df.copy()
    
    # Standardize column names
    column_mapping = {
        'time': 'time',
        'Time': 'time',
        'open': 'open',
        'Open': 'open',
        'high': 'high',
        'High': 'high',
        'low': 'low',
        'Low': 'low',
        'close': 'close',
        'Close': 'close',
        'volume': 'volume',
        'Volume': 'volume'
    }
    
    # Rename columns
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)
    
    # Ensure required columns exist
    required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df.columns:
            print(f"   ⚠️ Missing column: {col}")
            return None
    
    # Add ticker column
    df['ticker'] = ticker
    
    # Convert time to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = pd.to_datetime(df['time'])
    
    # Sort by time
    df = df.sort_values('time').reset_index(drop=True)
    
    # Filter date range
    df = df[(df['time'] >= START_DATE) & (df['time'] <= END_DATE)]
    
    return df


# ============================================================================
# STRATEGY 1: BREAKOUT
# ============================================================================

def strategy_1_breakout(df):
    """
    Chiến lược Breakout
    
    Entry: 
    - Price breaks 20-day high
    - Volume > 1.5x average
    - RSI 50-70
    
    Exit:
    - Stop Loss: -5%
    - Take Profit: +10%
    """
    signals = []
    
    # Calculate indicators
    df['high_20'] = df['high'].rolling(20).max()
    df['volume_avg'] = df['volume'].rolling(20).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    for i in range(20, len(df)):
        # Entry conditions
        if (df['close'].iloc[i] > df['high_20'].iloc[i-1] and
            df['volume'].iloc[i] > df['volume_avg'].iloc[i] * 1.5 and
            50 <= df['rsi'].iloc[i] <= 70):
            
            entry_price = df['close'].iloc[i]
            stop_loss = entry_price * 0.95
            take_profit = entry_price * 1.10
            
            signals.append({
                'date': df['time'].iloc[i],
                'code': df['ticker'].iloc[0],
                'strategy': 'BREAKOUT',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'rsi': df['rsi'].iloc[i],
                'volume_ratio': df['volume'].iloc[i] / df['volume_avg'].iloc[i]
            })
    
    return signals


# ============================================================================
# STRATEGY 2: SWING T+
# ============================================================================

def strategy_2_swing(df):
    """
    Chiến lược Swing Trading với xác nhận
    
    Entry:
    - Breakout + confirmation next day
    - Volume spike on both days
    
    Exit:
    - Stop Loss: -5%
    - Take Profit: +8%
    - Hold: T+2 (2 days)
    """
    signals = []
    
    df['high_20'] = df['high'].rolling(20).max()
    df['volume_avg'] = df['volume'].rolling(20).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    for i in range(21, len(df)):
        # Check breakout yesterday
        breakout_yesterday = (df['close'].iloc[i-1] > df['high_20'].iloc[i-2] and
                             df['volume'].iloc[i-1] > df['volume_avg'].iloc[i-1] * 1.3)
        
        # Confirmation today
        confirmation_today = (df['close'].iloc[i] > df['close'].iloc[i-1] and
                             df['volume'].iloc[i] > df['volume_avg'].iloc[i] * 1.2)
        
        if breakout_yesterday and confirmation_today and 50 <= df['rsi'].iloc[i] <= 70:
            entry_price = df['close'].iloc[i]
            stop_loss = entry_price * 0.95
            take_profit = entry_price * 1.08
            
            signals.append({
                'date': df['time'].iloc[i],
                'code': df['ticker'].iloc[0],
                'strategy': 'SWING_T+',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'rsi': df['rsi'].iloc[i],
                'volume_ratio': df['volume'].iloc[i] / df['volume_avg'].iloc[i],
                'hold_days': 2
            })
    
    return signals


# ============================================================================
# STRATEGY 3: TREND PULLBACK
# ============================================================================

def strategy_3_pullback(df):
    """
    Chiến lược Pullback trong xu hướng tăng
    
    Entry:
    - EMA20 > EMA50 (uptrend)
    - Price pullback to EMA20
    - Bounce from EMA20
    - RSI 40-60
    
    Exit:
    - Stop Loss: Below recent low (-6%)
    - Take Profit: Previous high (+12%)
    """
    signals = []
    
    # EMAs
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Recent high/low
    df['high_20'] = df['high'].rolling(20).max()
    df['low_10'] = df['low'].rolling(10).min()
    
    for i in range(50, len(df)):
        # Uptrend
        uptrend = df['ema20'].iloc[i] > df['ema50'].iloc[i]
        
        # Pullback to EMA20
        near_ema20 = abs(df['close'].iloc[i] - df['ema20'].iloc[i]) / df['ema20'].iloc[i] < 0.02
        
        # Bounce
        bounce = (df['close'].iloc[i] > df['ema20'].iloc[i] and
                 df['close'].iloc[i-1] < df['ema20'].iloc[i-1])
        
        if uptrend and (near_ema20 or bounce) and 40 <= df['rsi'].iloc[i] <= 60:
            entry_price = df['close'].iloc[i]
            stop_loss = df['low_10'].iloc[i] * 0.99
            take_profit = df['high_20'].iloc[i]
            
            # Ensure min R:R ratio
            if (take_profit - entry_price) / (entry_price - stop_loss) >= 1.5:
                signals.append({
                    'date': df['time'].iloc[i],
                    'code': df['ticker'].iloc[0],
                    'strategy': 'PULLBACK',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'rsi': df['rsi'].iloc[i],
                    'r_r_ratio': (take_profit - entry_price) / (entry_price - stop_loss)
                })
    
    return signals


# ============================================================================
# STRATEGY 4: EMA CROSSOVER
# ============================================================================

def strategy_4_ema_crossover(df):
    """
    Chiến lược EMA Crossover
    
    Entry:
    - EMA20 crosses above EMA50
    - Volume > 1.3x average
    - Trending market
    
    Exit:
    - Stop Loss: Below EMA50 (-5%)
    - Take Profit: +10%
    """
    signals = []
    
    # EMAs
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['volume_avg'] = df['volume'].rolling(20).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    for i in range(50, len(df)):
        # EMA crossover
        crossover = (df['ema20'].iloc[i] > df['ema50'].iloc[i] and
                    df['ema20'].iloc[i-1] <= df['ema50'].iloc[i-1])
        
        # Volume confirmation
        volume_ok = df['volume'].iloc[i] > df['volume_avg'].iloc[i] * 1.3
        
        # Trending
        trending = df['rsi'].iloc[i] > 50
        
        if crossover and volume_ok and trending:
            entry_price = df['close'].iloc[i]
            stop_loss = df['ema50'].iloc[i] * 0.98
            take_profit = entry_price * 1.10
            
            signals.append({
                'date': df['time'].iloc[i],
                'code': df['ticker'].iloc[0],
                'strategy': 'EMA_CROSS',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'rsi': df['rsi'].iloc[i],
                'volume_ratio': df['volume'].iloc[i] / df['volume_avg'].iloc[i]
            })
    
    return signals


# ============================================================================
# BACKTEST ENGINE
# ============================================================================

def simulate_trade(signal, df_future):
    """Simulate trade execution and calculate P&L"""
    entry_price = signal['entry_price']
    stop_loss = signal['stop_loss']
    take_profit = signal['take_profit']
    
    # Apply slippage
    entry_price_actual = entry_price * (1 + SLIPPAGE)
    
    # Position size
    shares = (INITIAL_CAPITAL * POSITION_SIZE) / entry_price_actual
    commission_entry = entry_price_actual * shares * COMMISSION
    
    # Find exit
    exit_date = None
    exit_price = None
    exit_reason = None
    
    max_hold_days = signal.get('hold_days', 30)
    
    for i, row in df_future.iterrows():
        days_held = (row['time'] - signal['date']).days
        
        if days_held > max_hold_days:
            exit_date = row['time']
            exit_price = row['close']
            exit_reason = 'MAX_HOLD'
            break
        
        # Check stop loss
        if row['low'] <= stop_loss:
            exit_date = row['time']
            exit_price = stop_loss
            exit_reason = 'STOP_LOSS'
            break
        
        # Check take profit
        if row['high'] >= take_profit:
            exit_date = row['time']
            exit_price = take_profit
            exit_reason = 'TAKE_PROFIT'
            break
    
    # If no exit
    if exit_date is None:
        exit_date = df_future.iloc[-1]['time']
        exit_price = df_future.iloc[-1]['close']
        exit_reason = 'END_OF_DATA'
    
    # Apply slippage
    exit_price_actual = exit_price * (1 - SLIPPAGE)
    
    # Calculate P&L
    commission_exit = exit_price_actual * shares * COMMISSION
    total_commission = commission_entry + commission_exit
    
    gross_pnl = (exit_price_actual - entry_price_actual) * shares
    net_pnl = gross_pnl - total_commission
    
    pnl_percent = (net_pnl / (entry_price_actual * shares)) * 100
    
    return {
        'entry_date': signal['date'],
        'exit_date': exit_date,
        'days_held': (exit_date - signal['date']).days,
        'entry_price': entry_price_actual,
        'exit_price': exit_price_actual,
        'shares': shares,
        'gross_pnl': gross_pnl,
        'net_pnl': net_pnl,
        'pnl_percent': pnl_percent,
        'exit_reason': exit_reason,
        'commission': total_commission
    }


def backtest_stock(ticker, df, strategies):
    """Backtest all strategies on one stock"""
    print(f"\n{'='*70}")
    print(f"Backtesting: {ticker}")
    print(f"{'='*70}")
    
    # Prepare data
    df = prepare_dataframe(df, ticker)
    
    if df is None or len(df) < 100:
        print(f"⚠️  Not enough data: {len(df) if df is not None else 0} rows")
        return []
    
    print(f"✅ Loaded {len(df)} rows ({df['time'].min()} to {df['time'].max()})")
    
    all_trades = []
    
    # Run each strategy
    for strategy_func in strategies:
        strategy_name = strategy_func.__name__.replace('strategy_', '').replace('_', ' ').upper()
        print(f"\n📊 Testing {strategy_name}...", end=" ")
        
        try:
            signals = strategy_func(df.copy())
            print(f"Found {len(signals)} signals")
            
            # Simulate trades
            for signal in signals:
                signal_date = signal['date']
                df_future = df[df['time'] > signal_date].reset_index(drop=True)
                
                if len(df_future) < 5:
                    continue
                
                trade_result = simulate_trade(signal, df_future)
                trade = {**signal, **trade_result}
                all_trades.append(trade)
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return all_trades


def analyze_results(all_trades):
    """Analyze backtest results"""
    df = pd.DataFrame(all_trades)
    
    if len(df) == 0:
        print("\n❌ No trades to analyze!")
        return {}, df
    
    print(f"\n{'='*70}")
    print(f"BACKTEST RESULTS")
    print(f"{'='*70}")
    
    results = {}
    
    for strategy in df['strategy'].unique():
        strategy_trades = df[df['strategy'] == strategy]
        
        total_trades = len(strategy_trades)
        winning_trades = len(strategy_trades[strategy_trades['net_pnl'] > 0])
        losing_trades = len(strategy_trades[strategy_trades['net_pnl'] <= 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = strategy_trades[strategy_trades['net_pnl'] > 0]['pnl_percent'].mean()
        avg_loss = strategy_trades[strategy_trades['net_pnl'] <= 0]['pnl_percent'].mean()
        
        total_pnl = strategy_trades['net_pnl'].sum()
        total_return = (total_pnl / INITIAL_CAPITAL) * 100
        
        avg_hold_days = strategy_trades['days_held'].mean()
        
        # Max drawdown
        cumulative_pnl = strategy_trades['net_pnl'].cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown = (cumulative_pnl - running_max) / INITIAL_CAPITAL * 100
        max_drawdown = drawdown.min()
        
        results[strategy] = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf'),
            'total_pnl': total_pnl,
            'total_return': total_return,
            'avg_hold_days': avg_hold_days,
            'max_drawdown': max_drawdown
        }
        
        print(f"\n{'='*70}")
        print(f"STRATEGY: {strategy}")
        print(f"{'='*70}")
        print(f"Total Trades:      {total_trades:,}")
        print(f"Winning Trades:    {winning_trades:,} ({win_rate:.1f}%)")
        print(f"Losing Trades:     {losing_trades:,} ({100-win_rate:.1f}%)")
        print(f"")
        print(f"Average Win:       {avg_win:+.2f}%")
        print(f"Average Loss:      {avg_loss:+.2f}%")
        print(f"Profit Factor:     {results[strategy]['profit_factor']:.2f}")
        print(f"")
        print(f"Total P&L:         {total_pnl:+,.0f} VND")
        print(f"Total Return:      {total_return:+.2f}%")
        print(f"Average Hold:      {avg_hold_days:.1f} days")
        print(f"Max Drawdown:      {max_drawdown:.2f}%")
    
    return results, df


def save_results(results, all_trades_df):
    """Save results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save trades
    trades_file = f"{RESULTS_FOLDER}/all_trades_{timestamp}.csv"
    all_trades_df.to_csv(trades_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Trades saved to: {trades_file}")
    
    # Save summary
    summary_file = f"{RESULTS_FOLDER}/summary_{timestamp}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("BACKTEST SUMMARY - 4 STRATEGIES\n")
        f.write("="*70 + "\n")
        f.write(f"Period: {START_DATE} to {END_DATE}\n")
        f.write(f"Initial Capital: {INITIAL_CAPITAL:,} VND\n")
        f.write(f"Position Size: {POSITION_SIZE*100}%\n")
        f.write(f"Commission: {COMMISSION*100}%\n")
        f.write("\n")
        
        for strategy, metrics in results.items():
            f.write(f"\n{strategy}:\n")
            f.write(f"  Trades: {metrics['total_trades']:,}\n")
            f.write(f"  Win Rate: {metrics['win_rate']:.1f}%\n")
            f.write(f"  Total Return: {metrics['total_return']:+.2f}%\n")
            f.write(f"  Profit Factor: {metrics['profit_factor']:.2f}\n")
            f.write(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%\n")
    
    print(f"✅ Summary saved to: {summary_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main backtest function"""
    print("="*70)
    print("AI ADVISOR - BACKTEST 4 STRATEGIES")
    print("="*70)
    print(f"Data Folder: {DATA_FOLDER}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Initial Capital: {INITIAL_CAPITAL:,} VND")
    print(f"Position Size: {POSITION_SIZE*100}%")
    print("="*70)
    
    # Load data from PKL
    all_stocks_data = load_data_from_pkl()
    
    if len(all_stocks_data) == 0:
        print("\n❌ No data loaded!")
        return
    
    print(f"\n✅ Stocks available: {len(all_stocks_data)}")
    
    # Ask how many to test
    try:
        num_stocks = int(input(f"\nHow many stocks to test? (max {len(all_stocks_data)}): "))
        num_stocks = min(num_stocks, len(all_stocks_data))
    except:
        num_stocks = len(all_stocks_data)
    
    # Get stock tickers
    stock_tickers = list(all_stocks_data.keys())[:num_stocks]
    
    # Define strategies
    strategies = [
        strategy_1_breakout,
        strategy_2_swing,
        strategy_3_pullback,
        strategy_4_ema_crossover
    ]
    
    # Run backtest
    all_trades = []
    
    for ticker in stock_tickers:
        df = all_stocks_data[ticker]
        trades = backtest_stock(ticker, df, strategies)
        all_trades.extend(trades)
    
    # Analyze results
    if len(all_trades) > 0:
        results, trades_df = analyze_results(all_trades)
        save_results(results, trades_df)
        
        print(f"\n{'='*70}")
        print("BACKTEST COMPLETE!")
        print(f"{'='*70}")
        print(f"Total Stocks Tested: {len(stock_tickers)}")
        print(f"Total Trades: {len(all_trades):,}")
        print(f"Results saved to: {RESULTS_FOLDER}/")
    else:
        print("\n❌ No trades generated. Check data and parameters.")


if __name__ == "__main__":
    main()
