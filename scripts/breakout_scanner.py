#!/usr/bin/env python3
"""
BREAKOUT DETECTION STRATEGY - 1H Timeframe

Tín hiệu MUA khi:
1. Volume spike: Vol tăng 200% (3x) so với cây trước
2. MACD crossover: Chuyển từ âm sang dương (bullish crossover)
3. RSI breakout: RSI vượt 70

Pattern này detect điểm mua khi có:
- Breakout khỏi consolidation
- Volume confirmation (smart money đang vào)
- Momentum mạnh (RSI > 70)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys

try:
    from vnstock import Vnstock
except ImportError:
    print(json.dumps({"error": "vnstock not installed"}))
    sys.exit(1)


class BreakoutDetector:
    """
    Detect breakout pattern với volume spike + MACD crossover + RSI breakout
    """
    
    def __init__(self, volume_multiplier=3.0, rsi_threshold=70):
        """
        Args:
            volume_multiplier: Vol phải tăng gấp bao nhiêu lần (default: 3x = 200% increase)
            rsi_threshold: RSI threshold để xác nhận breakout (default: 70)
        """
        self.volume_multiplier = volume_multiplier
        self.rsi_threshold = rsi_threshold
    
    def calculate_rsi(self, prices, period=14):
        """
        Calculate RSI (Relative Strength Index)
        
        Args:
            prices: Series of close prices
            period: RSI period (default: 14)
            
        Returns:
            Series of RSI values
        """
        deltas = prices.diff()
        gain = deltas.clip(lower=0)
        loss = -deltas.clip(upper=0)
        
        # Exponential moving average
        avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            prices: Series of close prices
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line period (default: 9)
            
        Returns:
            Tuple of (macd, signal_line, histogram)
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    def detect_volume_spike(self, volumes):
        """
        Detect volume spike (Vol tăng >= 200% so với cây trước)
        
        Args:
            volumes: Series of volume data
            
        Returns:
            Boolean series indicating volume spikes
        """
        # Volume tăng so với cây trước
        volume_ratio = volumes / volumes.shift(1)
        
        # Volume spike = tăng >= volume_multiplier lần
        is_volume_spike = volume_ratio >= self.volume_multiplier
        
        return is_volume_spike, volume_ratio
    
    def detect_macd_crossover(self, macd, signal_line):
        """
        Detect MACD bullish crossover (chuyển từ âm sang dương)
        
        Args:
            macd: MACD line
            signal_line: Signal line
            
        Returns:
            Boolean series indicating bullish crossovers
        """
        histogram = macd - signal_line
        
        # Điều kiện 1: MACD histogram chuyển từ âm sang dương
        prev_histogram = histogram.shift(1)
        is_crossover = (prev_histogram < 0) & (histogram > 0)
        
        # Điều kiện 2: MACD line đang dương (bullish)
        is_macd_positive = histogram > 0
        
        return is_crossover, is_macd_positive
    
    def detect_rsi_breakout(self, rsi):
        """
        Detect RSI breakout (RSI vượt threshold)
        
        Args:
            rsi: RSI series
            
        Returns:
            Boolean series indicating RSI breakouts
        """
        is_rsi_breakout = rsi > self.rsi_threshold
        
        return is_rsi_breakout
    
    def detect_signal(self, df):
        """
        Detect tín hiệu MUA dựa trên 3 điều kiện
        
        Args:
            df: DataFrame with columns [time, open, high, low, close, volume]
            
        Returns:
            DataFrame with added indicator columns and signal
        """
        # Calculate indicators
        df['rsi'] = self.calculate_rsi(df['close'])
        df['macd'], df['macd_signal'], df['macd_histogram'] = self.calculate_macd(df['close'])
        
        # Detect conditions
        df['volume_spike'], df['volume_ratio'] = self.detect_volume_spike(df['volume'])
        df['macd_crossover'], df['macd_positive'] = self.detect_macd_crossover(
            df['macd'], df['macd_signal']
        )
        df['rsi_breakout'] = self.detect_rsi_breakout(df['rsi'])
        
        # Combined signal: Tất cả 3 điều kiện phải thỏa mãn
        df['buy_signal'] = (
            df['volume_spike'] & 
            df['macd_crossover'] & 
            df['rsi_breakout']
        )
        
        return df
    
    def get_latest_signal(self, df):
        """
        Get tín hiệu mới nhất (cây nến gần nhất)
        
        Args:
            df: DataFrame with indicators
            
        Returns:
            Dict with signal details or None
        """
        # Get latest candle
        latest = df.iloc[-1]
        
        if latest['buy_signal']:
            return {
                'time': latest['time'],
                'close': float(latest['close']),
                'volume': int(latest['volume']),
                'volume_ratio': float(latest['volume_ratio']),
                'rsi': float(latest['rsi']),
                'macd': float(latest['macd']),
                'macd_histogram': float(latest['macd_histogram']),
                'signal': 'BUY',
                'confidence': self._calculate_confidence(latest)
            }
        
        return None
    
    def _calculate_confidence(self, row):
        """
        Calculate confidence score (0-100) dựa trên strength của các indicators
        
        Args:
            row: DataFrame row with indicator values
            
        Returns:
            Confidence score (0-100)
        """
        confidence = 0
        
        # Volume strength (0-40 points)
        if row['volume_ratio'] >= 5:  # 400%+
            confidence += 40
        elif row['volume_ratio'] >= 4:  # 300%+
            confidence += 35
        elif row['volume_ratio'] >= 3:  # 200%+
            confidence += 30
        
        # RSI strength (0-30 points)
        if row['rsi'] >= 80:  # Very strong
            confidence += 30
        elif row['rsi'] >= 75:
            confidence += 25
        elif row['rsi'] >= 70:
            confidence += 20
        
        # MACD strength (0-30 points)
        macd_strength = abs(row['macd_histogram'])
        if macd_strength >= 0.05:  # Strong momentum
            confidence += 30
        elif macd_strength >= 0.03:
            confidence += 25
        elif macd_strength >= 0.01:
            confidence += 20
        
        return min(confidence, 100)


def fetch_1h_data(code, lookback_hours=168):
    """
    Fetch 1H intraday data từ VNStock
    
    Args:
        code: Stock code (e.g., 'VNM')
        lookback_hours: Số giờ lấy data (default: 168 = 1 tuần)
        
    Returns:
        DataFrame with 1H data
    """
    try:
        stock = Vnstock().stock(symbol=code, source='VCI')
        
        # Get intraday data (VNStock returns recent candles)
        # Note: page_size controls how many candles to fetch
        data = stock.quote.intraday(
            symbol=code,
            page_size=lookback_hours  # Get enough data for indicators
        )
        
        if data.empty:
            return None
        
        # Ensure data is sorted by time
        data = data.sort_values('time')
        
        # Reset index
        data = data.reset_index(drop=True)
        
        return data
        
    except Exception as e:
        print(f"Error fetching {code}: {e}", file=sys.stderr)
        return None


def scan_multiple_stocks(stock_codes, volume_multiplier=3.0, rsi_threshold=70):
    """
    Scan nhiều mã cổ phiếu để tìm tín hiệu
    
    Args:
        stock_codes: List of stock codes
        volume_multiplier: Volume multiplier threshold
        rsi_threshold: RSI threshold
        
    Returns:
        List of stocks với tín hiệu MUA
    """
    detector = BreakoutDetector(
        volume_multiplier=volume_multiplier,
        rsi_threshold=rsi_threshold
    )
    
    signals = []
    
    for code in stock_codes:
        print(f"Scanning {code}...", file=sys.stderr)
        
        # Fetch 1H data
        df = fetch_1h_data(code, lookback_hours=168)
        
        if df is None or len(df) < 50:  # Need enough data for indicators
            print(f"  → Not enough data", file=sys.stderr)
            continue
        
        # Detect signal
        df_with_indicators = detector.detect_signal(df)
        signal = detector.get_latest_signal(df_with_indicators)
        
        if signal:
            signal['code'] = code
            signals.append(signal)
            print(f"  → ✅ BUY signal detected!", file=sys.stderr)
        else:
            print(f"  → No signal", file=sys.stderr)
    
    return signals


def main():
    """
    Main execution
    """
    # Stock universe (VN30 + popular stocks)
    STOCK_CODES = [
        # VN30
        'VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC', 
        'MSN', 'VHM', 'GVR', 'SAB', 'GAS', 'CTG',
        'BID', 'PLX', 'VRE', 'VPB', 'TCB', 'SSI',
        'HDB', 'ACB', 'MWG', 'POW', 'VJC', 'VND',
        'TPB', 'STB', 'SHB', 'EIB', 'LPB', 'KDH'
    ]
    
    # Parameters
    VOLUME_MULTIPLIER = 3.0  # 200% increase = 3x
    RSI_THRESHOLD = 70
    
    print("=" * 60, file=sys.stderr)
    print("BREAKOUT SCANNER - 1H TIMEFRAME", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Volume spike: >= {VOLUME_MULTIPLIER}x ({(VOLUME_MULTIPLIER-1)*100:.0f}% increase)", file=sys.stderr)
    print(f"MACD: Crossover from negative to positive", file=sys.stderr)
    print(f"RSI: > {RSI_THRESHOLD}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    
    # Scan stocks
    signals = scan_multiple_stocks(
        STOCK_CODES,
        volume_multiplier=VOLUME_MULTIPLIER,
        rsi_threshold=RSI_THRESHOLD
    )
    
    # Output results
    result = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'timeframe': '1H',
        'total_scanned': len(STOCK_CODES),
        'signals_found': len(signals),
        'signals': signals,
        'strategy': {
            'name': 'Volume Spike + MACD Crossover + RSI Breakout',
            'volume_multiplier': VOLUME_MULTIPLIER,
            'rsi_threshold': RSI_THRESHOLD
        }
    }
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
