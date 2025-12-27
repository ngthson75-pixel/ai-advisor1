#!/usr/bin/env python3
"""
BEARISH DIVERGENCE DETECTION - 1H Timeframe

Tín hiệu BÁN khi:
1. Volume spike: Vol tăng 200% (3x) so với cây trước
2. MACD Bearish Divergence: Price tạo higher high, MACD tạo lower high
3. RSI reversal: RSI quay đầu giảm xuống dưới 70

Pattern này detect đỉnh phân kỳ (divergence) - dấu hiệu đảo chiều xuống mạnh!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
from scipy.signal import argrelextrema

try:
    from vnstock import Vnstock
except ImportError:
    print(json.dumps({"error": "vnstock not installed"}))
    sys.exit(1)


class BearishDivergenceDetector:
    """
    Detect bearish divergence pattern:
    - Volume spike
    - MACD bearish divergence (price higher high, MACD lower high)
    - RSI reversal below 70
    """
    
    def __init__(self, volume_multiplier=3.0, rsi_threshold=70, lookback_peaks=20):
        """
        Args:
            volume_multiplier: Vol phải tăng gấp bao nhiêu lần (default: 3x)
            rsi_threshold: RSI threshold (default: 70)
            lookback_peaks: Số bars để tìm peaks (default: 20)
        """
        self.volume_multiplier = volume_multiplier
        self.rsi_threshold = rsi_threshold
        self.lookback_peaks = lookback_peaks
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        deltas = prices.diff()
        gain = deltas.clip(lower=0)
        loss = -deltas.clip(upper=0)
        
        avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    def find_peaks(self, data, order=5):
        """
        Find local peaks (maxima) in data
        
        Args:
            data: Series or array
            order: How many points on each side to use for comparison
            
        Returns:
            Array of peak indices
        """
        peaks = argrelextrema(data.values, np.greater, order=order)[0]
        return peaks
    
    def detect_volume_spike(self, volumes):
        """Detect volume spike"""
        volume_ratio = volumes / volumes.shift(1)
        is_volume_spike = volume_ratio >= self.volume_multiplier
        
        return is_volume_spike, volume_ratio
    
    def detect_bearish_divergence(self, df, lookback=20):
        """
        Detect MACD bearish divergence:
        - Price tạo higher high (đỉnh sau cao hơn đỉnh trước)
        - MACD tạo lower high (đỉnh sau thấp hơn đỉnh trước)
        
        Args:
            df: DataFrame with 'high' and 'macd' columns
            lookback: Số bars để tìm 2 đỉnh
            
        Returns:
            Boolean series indicating divergence
        """
        # Find peaks in price (high)
        price_peaks_idx = self.find_peaks(df['high'], order=3)
        
        # Find peaks in MACD
        macd_peaks_idx = self.find_peaks(df['macd'], order=3)
        
        # Initialize divergence column
        df['bearish_divergence'] = False
        
        # Check each recent bar
        for i in range(len(df) - lookback, len(df)):
            if i < lookback:
                continue
            
            # Get recent price peaks trong lookback window
            recent_price_peaks = [idx for idx in price_peaks_idx 
                                 if i - lookback <= idx <= i]
            
            # Get recent MACD peaks trong lookback window
            recent_macd_peaks = [idx for idx in macd_peaks_idx 
                                if i - lookback <= idx <= i]
            
            # Need at least 2 peaks để compare
            if len(recent_price_peaks) >= 2 and len(recent_macd_peaks) >= 2:
                # Get 2 đỉnh gần nhất
                price_peak1_idx = recent_price_peaks[-2]
                price_peak2_idx = recent_price_peaks[-1]
                
                macd_peak1_idx = recent_macd_peaks[-2]
                macd_peak2_idx = recent_macd_peaks[-1]
                
                # Get values
                price_peak1 = df.iloc[price_peak1_idx]['high']
                price_peak2 = df.iloc[price_peak2_idx]['high']
                
                macd_peak1 = df.iloc[macd_peak1_idx]['macd']
                macd_peak2 = df.iloc[macd_peak2_idx]['macd']
                
                # Check divergence:
                # Price: higher high (đỉnh sau > đỉnh trước)
                # MACD: lower high (đỉnh sau < đỉnh trước)
                is_price_higher = price_peak2 > price_peak1
                is_macd_lower = macd_peak2 < macd_peak1
                
                if is_price_higher and is_macd_lower:
                    df.at[i, 'bearish_divergence'] = True
                    
                    # Store divergence info
                    df.at[i, 'divergence_strength'] = (
                        (price_peak2 - price_peak1) / price_peak1 * 100 +
                        (macd_peak1 - macd_peak2) / abs(macd_peak1) * 100
                    )
        
        return df['bearish_divergence']
    
    def detect_rsi_reversal(self, rsi):
        """
        Detect RSI reversal (từ > 70 quay đầu xuống < 70)
        
        Args:
            rsi: RSI series
            
        Returns:
            Boolean series indicating reversal
        """
        # RSI hiện tại < 70
        current_below = rsi < self.rsi_threshold
        
        # RSI trước đó >= 70
        previous_above = rsi.shift(1) >= self.rsi_threshold
        
        # Reversal = chuyển từ >= 70 xuống < 70
        is_reversal = previous_above & current_below
        
        # Also check: RSI đang trend xuống
        rsi_decreasing = rsi < rsi.shift(1)
        
        return is_reversal, (current_below & rsi_decreasing)
    
    def detect_signal(self, df):
        """
        Detect tín hiệu BÁN
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicators and signals
        """
        # Calculate indicators
        df['rsi'] = self.calculate_rsi(df['close'])
        df['macd'], df['macd_signal'], df['macd_histogram'] = self.calculate_macd(df['close'])
        
        # Detect conditions
        df['volume_spike'], df['volume_ratio'] = self.detect_volume_spike(df['volume'])
        
        # Detect bearish divergence
        df['bearish_divergence'] = self.detect_bearish_divergence(df, self.lookback_peaks)
        
        # Detect RSI reversal
        df['rsi_reversal'], df['rsi_declining'] = self.detect_rsi_reversal(df['rsi'])
        
        # Combined SELL signal
        df['sell_signal'] = (
            df['volume_spike'] &
            df['bearish_divergence'] &
            (df['rsi_reversal'] | df['rsi_declining'])
        )
        
        return df
    
    def get_latest_signal(self, df):
        """Get tín hiệu mới nhất"""
        latest = df.iloc[-1]
        
        if latest['sell_signal']:
            return {
                'time': latest['time'],
                'close': float(latest['close']),
                'high': float(latest['high']),
                'volume': int(latest['volume']),
                'volume_ratio': float(latest['volume_ratio']),
                'rsi': float(latest['rsi']),
                'macd': float(latest['macd']),
                'macd_histogram': float(latest['macd_histogram']),
                'signal': 'SELL',
                'confidence': self._calculate_confidence(latest),
                'reason': 'Bearish Divergence + Volume Spike + RSI Reversal'
            }
        
        return None
    
    def _calculate_confidence(self, row):
        """Calculate confidence score (0-100)"""
        confidence = 0
        
        # Volume strength (0-40 points)
        if row['volume_ratio'] >= 5:
            confidence += 40
        elif row['volume_ratio'] >= 4:
            confidence += 35
        elif row['volume_ratio'] >= 3:
            confidence += 30
        
        # Divergence strength (0-30 points)
        if 'divergence_strength' in row and pd.notna(row['divergence_strength']):
            div_strength = row['divergence_strength']
            if div_strength >= 10:
                confidence += 30
            elif div_strength >= 5:
                confidence += 25
            elif div_strength >= 2:
                confidence += 20
        else:
            confidence += 20  # Default if no divergence strength
        
        # RSI position (0-30 points)
        rsi_distance = abs(row['rsi'] - self.rsi_threshold)
        if rsi_distance >= 10:  # RSI far below 70
            confidence += 30
        elif rsi_distance >= 5:
            confidence += 25
        elif rsi_distance >= 2:
            confidence += 20
        
        return min(confidence, 100)


def fetch_1h_data(code, lookback_hours=168):
    """Fetch 1H data from VNStock"""
    try:
        stock = Vnstock().stock(symbol=code, source='VCI')
        
        data = stock.quote.intraday(
            symbol=code,
            page_size=lookback_hours
        )
        
        if data.empty:
            return None
        
        data = data.sort_values('time')
        data = data.reset_index(drop=True)
        
        return data
        
    except Exception as e:
        print(f"Error fetching {code}: {e}", file=sys.stderr)
        return None


def scan_multiple_stocks(stock_codes, volume_multiplier=3.0, rsi_threshold=70):
    """Scan nhiều mã để tìm tín hiệu BÁN"""
    detector = BearishDivergenceDetector(
        volume_multiplier=volume_multiplier,
        rsi_threshold=rsi_threshold
    )
    
    signals = []
    
    for code in stock_codes:
        print(f"Scanning {code}...", file=sys.stderr)
        
        df = fetch_1h_data(code, lookback_hours=168)
        
        if df is None or len(df) < 50:
            print(f"  → Not enough data", file=sys.stderr)
            continue
        
        df_with_indicators = detector.detect_signal(df)
        signal = detector.get_latest_signal(df_with_indicators)
        
        if signal:
            signal['code'] = code
            signals.append(signal)
            print(f"  → ✅ SELL signal detected!", file=sys.stderr)
        else:
            print(f"  → No signal", file=sys.stderr)
    
    return signals


def main():
    """Main execution"""
    STOCK_CODES = [
        'VNM', 'HPG', 'FPT', 'MBB', 'VCB', 'VIC', 
        'MSN', 'VHM', 'GVR', 'SAB', 'GAS', 'CTG',
        'BID', 'PLX', 'VRE', 'VPB', 'TCB', 'SSI',
        'HDB', 'ACB', 'MWG', 'POW', 'VJC', 'VND',
        'TPB', 'STB', 'SHB', 'EIB', 'LPB', 'KDH'
    ]
    
    VOLUME_MULTIPLIER = 3.0
    RSI_THRESHOLD = 70
    
    print("=" * 60, file=sys.stderr)
    print("BEARISH DIVERGENCE SCANNER - 1H TIMEFRAME", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Volume spike: >= {VOLUME_MULTIPLIER}x", file=sys.stderr)
    print(f"MACD: Bearish divergence (price HH, MACD LH)", file=sys.stderr)
    print(f"RSI: Reversal below {RSI_THRESHOLD}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("", file=sys.stderr)
    
    signals = scan_multiple_stocks(
        STOCK_CODES,
        volume_multiplier=VOLUME_MULTIPLIER,
        rsi_threshold=RSI_THRESHOLD
    )
    
    result = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'timeframe': '1H',
        'total_scanned': len(STOCK_CODES),
        'signals_found': len(signals),
        'signals': signals,
        'strategy': {
            'name': 'Bearish Divergence + Volume Spike + RSI Reversal',
            'volume_multiplier': VOLUME_MULTIPLIER,
            'rsi_threshold': RSI_THRESHOLD
        }
    }
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
