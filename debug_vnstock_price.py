def check_sell_condition(ticker, entry_price, stop_loss, take_profit, retry=True):
    """Kiểm tra điều kiện SELL - FIXED price parsing"""
    
    if VERBOSE:
        print(f"\n  Checking {ticker}...")
    
    try:
        data = Quote(symbol=ticker, source='VCI')
        today = datetime.now()
        yesterday = today - timedelta(days=3)
        
        df = data.history(
            start=yesterday.strftime('%Y-%m-%d'),
            end=today.strftime('%Y-%m-%d')
        )
        
        if df.empty:
            if VERBOSE:
                print(f"    ⚠️  No data")
            return None
        
        # FIX: Try different column names and check if need to multiply
        raw_price = None
        if 'close' in df.columns:
            raw_price = float(df['close'].iloc[-1])
        elif 'Close' in df.columns:
            raw_price = float(df['Close'].iloc[-1])
        else:
            print(f"    ❌ No close price column found!")
            return None
        
        # FIX: If price too small, multiply by 1000
        if raw_price < 1000:  # Giá VN thường > 1,000 VND
            current_price = raw_price * 1000
            if VERBOSE:
                print(f"    ⚠️  Price adjusted: {raw_price} → {current_price:,.0f} VND")
        else:
            current_price = raw_price
        
        if VERBOSE:
            print(f"    Current: {current_price:,.0f}")
            print(f"    Entry:   {entry_price:,.0f}")
            print(f"    SL:      {stop_loss:,.0f}")
            print(f"    TP:      {take_profit:,.0f}")
        
        # ... rest of logic stays same