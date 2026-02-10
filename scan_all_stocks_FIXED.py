def scan_all_stocks():
    """Scan stocks - PRIORITY SIGNALS ONLY"""
    logger.info("=" * 60)
    logger.info("Starting scan...")
    logger.info(f"Date: {get_last_trading_day()}")
    logger.info(f"Stocks: {len(TOP_STOCKS)}")
    logger.info("=" * 60)
    
    init_database()
    
    all_signals = []
    processed = 0
    failed = 0
    
    for ticker in TOP_STOCKS:
        try:
            logger.info(f"Processing {ticker} ({processed + 1}/{len(TOP_STOCKS)})...")
            
            df = get_stock_data(ticker, days=100)
            
            if df is None or len(df) < 50:
                logger.warning(f"Skip {ticker}")
                failed += 1
                time.sleep(0.5)
                continue
            
            pullback = check_pullback_strategy(df, ticker)
            ema_cross = check_ema_cross_strategy(df, ticker)
            
            # Priority only filter
            for signal in pullback:
                if signal['is_priority'] == 1:
                    all_signals.append(signal)
                    
            for signal in ema_cross:
                if signal['is_priority'] == 1:
                    all_signals.append(signal)
            
            processed += 1
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error {ticker}: {str(e)}")
            failed += 1
            time.sleep(0.5)
    
    logger.info("=" * 60)
    logger.info("COMPLETE")
    logger.info(f"Processed: {processed}/{len(TOP_STOCKS)}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Signals: {len(all_signals)}")
    logger.info("=" * 60)
    
    if len(all_signals) > 0:
        save_signals_to_db(all_signals)
        
        pullback_cnt = len([s for s in all_signals if s['strategy'] == 'PULLBACK'])
        ema_cross_cnt = len([s for s in all_signals if s['strategy'] == 'EMA_CROSS'])
        priority_cnt = len([s for s in all_signals if s['is_priority'] == 1])
        
        logger.info(f"PULLBACK: {pullback_cnt}")
        logger.info(f"EMA_CROSS: {ema_cross_cnt}")
        logger.info(f"Priority: {priority_cnt}")
        
        logger.info("\nTop 5:")
        sorted_sigs = sorted(all_signals, key=lambda x: x['strength'], reverse=True)[:5]
        for i, sig in enumerate(sorted_sigs, 1):
            logger.info(f"{i}. {sig['ticker']} - {sig['strategy']} - {sig['strength']}%")
    else:
        logger.warning("No signals")
    
    return all_signals
