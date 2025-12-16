#!/usr/bin/env python3
"""
VNStock Data Fetcher
Fetches real stock data from VNStock library v3.3.0 (FREE)
"""

import json
import sys
from datetime import datetime

try:
    from vnstock import Vnstock
except ImportError:
    print(json.dumps({"error": "vnstock not installed. Run: pip install vnstock --upgrade"}))
    sys.exit(1)

STOCK_CODES = ['MBB', 'VNM', 'HPG', 'FPT', 'VCB', 'VIC']

def fetch_stock_data(code):
    try:
        stock = Vnstock().stock(symbol=code, source='VCI')
        
        # Get current quote
        quote = stock.quote.history(symbol=code, start='2024-12-01', end='2024-12-31')
        
        if quote.empty:
            return None
        
        latest = quote.iloc[-1]
        
        return {
            'code': code,
            'price': float(latest['close']),
            'change': float(latest['close'] - latest['open']),
            'changePercent': float((latest['close'] - latest['open']) / latest['open'] * 100),
            'volume': int(latest['volume']),
            'high': float(latest['high']),
            'low': float(latest['low']),
            'open': float(latest['open'])
        }
    except Exception as e:
        print(f"Error fetching {code}: {e}", file=sys.stderr)
        return None

def main():
    results = []
    
    for code in STOCK_CODES:
        data = fetch_stock_data(code)
        if data:
            results.append(data)
    
    print(json.dumps({
        'success': True,
        'data': results,
        'timestamp': datetime.now().isoformat()
    }))

if __name__ == '__main__':
    main()
