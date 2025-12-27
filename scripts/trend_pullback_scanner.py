#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TREND + PULLBACK SCANNER

Chiến lược: Xác nhận uptrend → Chờ pullback → Entry khi trend resume
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class TrendPullbackDetector:
    """
    Detect trend following with pullback entry setups
    
    Conditions:
    1. Uptrend: EMA20 > EMA50
    2. Pullback: Price retraces 3-8%
    3. RSI: 40-60 zone
    4. Volume: Increases (≥1.5x) on bounce
    """
    
    def __init__(
        self,
        ema_short: int = 20,
        ema_long: int = 50,
        rsi_period: int = 14,
        rsi_lower: int = 40,
        rsi_upper: int = 60,
        volume_multiplier: float = 1.5,
        pullback_min: float = 0.03,
        pullback_max: float = 0.08
    ):
        self.ema_short = ema_short
        self.ema_long = ema_long
        self.rsi_period = rsi_period
        self.rsi_lower = rsi_lower
        self.rsi_upper = rsi_upper
        self.volume_multiplier = volume_multiplier
        self.pullback_min = pullback_min
        self.pullback_max = pullback_max
    
    
    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()
    
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    
    def is_uptrend(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Check if in uptrend
        
        Uptrend = EMA20 > EMA50 + Price > EMA20
        """
        current = df.loc[idx]
        
        # EMA20 must be above EMA50
        if current['ema20'] <= current['ema50']:
            return False
        
        # Price should be above EMA20 (or recently was)
        # Allow for pullback to EMA20
        if current['close'] < current['ema50']:
            return False
        
        # EMA20 should be trending up (compare to 5 bars ago)
        if idx >= 5:
            prev_idx = df.index[df.index.get_loc(idx) - 5]
            if current['ema20'] <= df.loc[prev_idx, 'ema20']:
                return False
        
        return True
    
    
    def find_recent_high(self, df: pd.DataFrame, idx: int, lookback: int = 20) -> Optional[float]:
        """Find recent high in lookback period"""
        if idx < lookback:
            return None
        
        period_data = df.iloc[max(0, df.index.get_loc(idx) - lookback):df.index.get_loc(idx)]
        return period_data['high'].max()
    
    
    def is_pullback(self, df: pd.DataFrame, idx: int) -> tuple[bool, Optional[float]]:
        """
        Check if price is in pullback
        
        Pullback = Retraced 3-8% from recent high
        """
        recent_high = self.find_recent_high(df, idx, lookback=20)
        
        if recent_high is None:
            return False, None
        
        current_price = df.loc[idx, 'close']
        pullback_pct = (recent_high - current_price) / recent_high
        
        # Must be within pullback range
        if pullback_pct < self.pullback_min or pullback_pct > self.pullback_max:
            return False, None
        
        # Price should be near EMA20 or EMA50
        current = df.loc[idx]
        distance_to_ema20 = abs(current_price - current['ema20']) / current_price
        distance_to_ema50 = abs(current_price - current['ema50']) / current_price
        
        # Within 3% of either EMA
        if distance_to_ema20 > 0.03 and distance_to_ema50 > 0.03:
            return False, None
        
        return True, pullback_pct
    
    
    def is_bounce(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Check if price is bouncing from support
        
        Bounce = Green candle + Volume increase
        """
        if idx < 1:
            return False
        
        current = df.loc[idx]
        prev = df.loc[df.index[df.index.get_loc(idx) - 1]]
        
        # Must be green candle
        if current['close'] <= current['open']:
            return False
        
        # Volume must increase
        if current['volume'] < current['avg_volume_20'] * self.volume_multiplier:
            return False
        
        # Price should be moving up from pullback
        if current['close'] <= prev['close']:
            return False
        
        return True
    
    
    def detect_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main detection logic
        
        Returns DataFrame with signals
        """
        df = df.copy()
        
        # Calculate indicators
        df['ema20'] = self.calculate_ema(df['close'], self.ema_short)
        df['ema50'] = self.calculate_ema(df['close'], self.ema_long)
        df['rsi'] = self.calculate_rsi(df, self.rsi_period)
        df['avg_volume_20'] = df['volume'].rolling(window=20).mean()
        
        # Initialize signal columns
        df['uptrend'] = False
        df['pullback'] = False
        df['pullback_pct'] = np.nan
        df['rsi_zone'] = False
        df['bounce'] = False
        df['buy_signal'] = False
        
        for idx in range(len(df)):
            current_idx = df.index[idx]
            
            if idx < max(self.ema_short, self.ema_long, 20):
                continue
            
            current = df.loc[current_idx]
            
            # Check uptrend
            if self.is_uptrend(df, current_idx):
                df.loc[current_idx, 'uptrend'] = True
            
            # Check pullback
            is_pb, pb_pct = self.is_pullback(df, current_idx)
            if is_pb:
                df.loc[current_idx, 'pullback'] = True
                df.loc[current_idx, 'pullback_pct'] = pb_pct * 100
            
            # Check RSI zone
            if self.rsi_lower <= current['rsi'] <= self.rsi_upper:
                df.loc[current_idx, 'rsi_zone'] = True
            
            # Check bounce
            if self.is_bounce(df, current_idx):
                df.loc[current_idx, 'bounce'] = True
            
            # BUY SIGNAL: All conditions met
            if (df.loc[current_idx, 'uptrend'] and
                df.loc[current_idx, 'pullback'] and
                df.loc[current_idx, 'rsi_zone'] and
                df.loc[current_idx, 'bounce']):
                df.loc[current_idx, 'buy_signal'] = True
        
        return df
    
    
    def get_signal_details(self, df: pd.DataFrame, signal_idx) -> Dict:
        """Get detailed information about a signal"""
        signal = df.loc[signal_idx]
        
        # Calculate stop loss (EMA50 - 1%)
        stop_loss = signal['ema50'] * 0.99
        risk_pct = ((signal['close'] - stop_loss) / signal['close']) * 100
        
        details = {
            'date': signal.name,
            'price': float(signal['close']),
            'ema20': float(signal['ema20']),
            'ema50': float(signal['ema50']),
            'rsi': float(signal['rsi']),
            'volume_ratio': float(signal['volume'] / signal['avg_volume_20']),
            'pullback_pct': float(signal['pullback_pct']),
            'stop_loss': float(stop_loss),
            'risk_pct': float(risk_pct),
            'tp1': float(signal['close'] * 1.05),  # +5%
            'tp2': float(signal['close'] * 1.10),  # +10%
        }
        
        return details


def main():
    """Test the detector"""
    pass


if __name__ == '__main__':
    main()
