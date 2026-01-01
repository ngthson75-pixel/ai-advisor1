"""
Test Signal Scanner
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from daily_signal_scanner_eod import (
    get_stock_data, 
    check_pullback_strategy,
    check_ema_cross_strategy,
    get_last_trading_day,
    save_signals_to_db,
    init_database
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_single_stock(ticker):
    """Test single stock"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {ticker}")
    logger.info(f"{'='*60}")
    
    df = get_stock_data(ticker, days=100)
    
    if df is None:
        logger.error(f"No data for {ticker}")
        return []
    
    logger.info(f"✓ Got {len(df)} days")
    logger.info(f"Close: {df['Close'].iloc[-1]:,.0f}")
    
    signals = []
    
    pullback = check_pullback_strategy(df, ticker)
    if pullback:
        logger.info(f"✓ PULLBACK found!")
        for sig in pullback:
            profit = ((sig['take_profit']/sig['entry_price']-1)*100)
            logger.info(f"  Entry: {sig['entry_price']:,.0f}")
            logger.info(f"  Target: {sig['take_profit']:,.0f} (+{profit:.1f}%)")
            logger.info(f"  Stop: {sig['stop_loss']:,.0f}")
            logger.info(f"  Strength: {sig['strength']}%")
        signals.extend(pullback)
    else:
        logger.info("No PULLBACK")
    
    ema_cross = check_ema_cross_strategy(df, ticker)
    if ema_cross:
        logger.info(f"✓ EMA_CROSS found!")
        for sig in ema_cross:
            profit = ((sig['take_profit']/sig['entry_price']-1)*100)
            logger.info(f"  Entry: {sig['entry_price']:,.0f}")
            logger.info(f"  Target: {sig['take_profit']:,.0f} (+{profit:.1f}%)")
            logger.info(f"  Stop: {sig['stop_loss']:,.0f}")
            logger.info(f"  Strength: {sig['strength']}%")
        signals.extend(ema_cross)
    else:
        logger.info("No EMA_CROSS")
    
    return signals

def test_multiple_stocks():
    """Test multiple stocks"""
    
    test_stocks = ['VCB', 'VHM', 'HPG', 'FPT', 'MBB', 'TCB', 'VNM', 'VIC', 'STB', 'MSN']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"TESTING {len(test_stocks)} STOCKS")
    logger.info(f"Date: {get_last_trading_day()}")
    logger.info(f"{'='*60}\n")
    
    init_database()
    
    all_signals = []
    success = 0
    
    for ticker in test_stocks:
        try:
            signals = test_single_stock(ticker)
            if signals:
                all_signals.extend(signals)
                success += 1
        except Exception as e:
            logger.error(f"Error {ticker}: {str(e)}")
    
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Tested: {len(test_stocks)}")
    logger.info(f"Success: {success}")
    logger.info(f"Signals: {len(all_signals)}")
    
    if len(all_signals) > 0:
        logger.info("\n✓ Signals:")
        for i, sig in enumerate(all_signals, 1):
            profit = ((sig['take_profit']/sig['entry_price'])-1)*100
            logger.info(f"{i}. {sig['ticker']:4s} - {sig['strategy']:10s} - {sig['strength']:3d}% - +{profit:.1f}%")
        
        save_signals_to_db(all_signals)
        logger.info(f"\n✓ Saved to DB")
        
        pullback = len([s for s in all_signals if s['strategy'] == 'PULLBACK'])
        ema = len([s for s in all_signals if s['strategy'] == 'EMA_CROSS'])
        
        logger.info(f"\nPULLBACK: {pullback}")
        logger.info(f"EMA_CROSS: {ema}")
        
    else:
        logger.warning("\n⚠ No signals")
    
    return all_signals

if __name__ == "__main__":
    signals = test_multiple_stocks()
    
    if len(signals) > 0:
        logger.info(f"\n{'='*60}")
        logger.info("✓ TEST PASSED")
        logger.info(f"{len(signals)} signals")
        logger.info(f"{'='*60}")
        sys.exit(0)
    else:
        logger.warning(f"\n{'='*60}")
        logger.warning("⚠ WARNING - No signals")
        logger.warning("May be normal based on market")
        logger.warning(f"{'='*60}")
        sys.exit(1)
