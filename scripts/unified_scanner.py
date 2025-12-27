#!/usr/bin/env python3
"""
UNIFIED SIGNAL SCANNER - BUY & SELL

Scan cả 2 strategies:
1. Breakout (BUY): Volume spike + MACD crossover + RSI > 70
2. Divergence (SELL): Volume spike + MACD divergence + RSI reversal

Output: Combined signals for trading decisions
"""

import json
import sys
from datetime import datetime

# Import both detectors
try:
    import importlib.util
    import os
    
    # Load breakout scanner
    spec1 = importlib.util.spec_from_file_location(
        "breakout_scanner",
        os.path.join(os.path.dirname(__file__), "breakout_scanner.py")
    )
    breakout_module = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(breakout_module)
    
    # Load divergence scanner
    spec2 = importlib.util.spec_from_file_location(
        "divergence_scanner",
        os.path.join(os.path.dirname(__file__), "divergence_scanner.py")
    )
    divergence_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(divergence_module)
    
    BreakoutDetector = breakout_module.BreakoutDetector
    BearishDivergenceDetector = divergence_module.BearishDivergenceDetector
    fetch_1h_data = breakout_module.fetch_1h_data
    
except Exception as e:
    print(f"Error importing modules: {e}", file=sys.stderr)
    sys.exit(1)


def scan_stock_for_all_signals(code, lookback_hours=168):
    """
    Scan 1 mã cho cả BUY và SELL signals
    
    Args:
        code: Stock code
        lookback_hours: Hours of data to fetch
        
    Returns:
        Dict with BUY and/or SELL signals
    """
    # Fetch data
    df = fetch_1h_data(code, lookback_hours)
    
    if df is None or len(df) < 50:
        return None
    
    result = {
        'code': code,
        'timestamp': datetime.now().isoformat(),
        'buy_signal': None,
        'sell_signal': None
    }
    
    # Check for BUY signal (Breakout)
    try:
        buy_detector = BreakoutDetector(volume_multiplier=3.0, rsi_threshold=70)
        df_buy = buy_detector.detect_signal(df.copy())
        buy_signal = buy_detector.get_latest_signal(df_buy)
        
        if buy_signal:
            result['buy_signal'] = buy_signal
    except Exception as e:
        print(f"  Error in BUY detection: {e}", file=sys.stderr)
    
    # Check for SELL signal (Divergence)
    try:
        sell_detector = BearishDivergenceDetector(
            volume_multiplier=3.0,
            rsi_threshold=70
        )
        df_sell = sell_detector.detect_signal(df.copy())
        sell_signal = sell_detector.get_latest_signal(df_sell)
        
        if sell_signal:
            result['sell_signal'] = sell_signal
    except Exception as e:
        print(f"  Error in SELL detection: {e}", file=sys.stderr)
    
    return result


def scan_all_stocks(stock_codes):
    """
    Scan all stocks cho cả BUY và SELL
    
    Args:
        stock_codes: List of stock codes
        
    Returns:
        Dict with categorized signals
    """
    buy_signals = []
    sell_signals = []
    conflict_signals = []  # Stocks with both BUY and SELL (unusual)
    
    for code in stock_codes:
        print(f"Scanning {code}...", file=sys.stderr)
        
        result = scan_stock_for_all_signals(code)
        
        if result is None:
            print(f"  → Not enough data", file=sys.stderr)
            continue
        
        has_buy = result['buy_signal'] is not None
        has_sell = result['sell_signal'] is not None
        
        if has_buy and has_sell:
            # Conflict: Both BUY and SELL (rare, need investigation)
            conflict_signals.append(result)
            print(f"  → ⚠️  CONFLICT: Both BUY and SELL signals!", file=sys.stderr)
            
        elif has_buy:
            buy_signals.append(result['buy_signal'])
            confidence = result['buy_signal']['confidence']
            print(f"  → ✅ BUY signal (confidence: {confidence}/100)", file=sys.stderr)
            
        elif has_sell:
            sell_signals.append(result['sell_signal'])
            confidence = result['sell_signal']['confidence']
            print(f"  → 🔻 SELL signal (confidence: {confidence}/100)", file=sys.stderr)
            
        else:
            print(f"  → No signal", file=sys.stderr)
    
    return {
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'conflict_signals': conflict_signals
    }


def main():
    """Main execution"""
    STOCK_CODES = [
        'VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC', 
        'MSN', 'VHM', 'GVR', 'SAB', 'GAS', 'CTG',
        'BID', 'PLX', 'VRE', 'VPB', 'TCB', 'SSI',
        'HDB', 'ACB', 'MWG', 'POW', 'VJC', 'VND',
        'TPB', 'STB', 'SHB', 'EIB', 'LPB', 'KDH'
    ]
    
    print("=" * 60, file=sys.stderr)
    print("UNIFIED SCANNER - BUY & SELL SIGNALS", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("Strategies:", file=sys.stderr)
    print("  1. Breakout (BUY): Volume spike + MACD cross + RSI > 70", file=sys.stderr)
    print("  2. Divergence (SELL): Volume spike + MACD div + RSI < 70", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    
    # Scan all stocks
    results = scan_all_stocks(STOCK_CODES)
    
    # Prepare output
    output = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'timeframe': '1H',
        'total_scanned': len(STOCK_CODES),
        'summary': {
            'buy_signals': len(results['buy_signals']),
            'sell_signals': len(results['sell_signals']),
            'conflicts': len(results['conflict_signals'])
        },
        'signals': results,
        'strategies': {
            'buy': {
                'name': 'Breakout',
                'description': 'Volume spike + MACD crossover + RSI > 70'
            },
            'sell': {
                'name': 'Bearish Divergence',
                'description': 'Volume spike + MACD divergence + RSI reversal'
            }
        }
    }
    
    print(json.dumps(output, indent=2))
    
    # Summary to stderr
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Total scanned: {len(STOCK_CODES)}", file=sys.stderr)
    print(f"BUY signals: {len(results['buy_signals'])}", file=sys.stderr)
    print(f"SELL signals: {len(results['sell_signals'])}", file=sys.stderr)
    print(f"Conflicts: {len(results['conflict_signals'])}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == '__main__':
    main()
