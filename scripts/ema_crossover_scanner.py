#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA CROSSOVER SCANNER

Chiến lược: Golden Cross (EMA20 > EMA50) → Entry → Hold → Death Cross → Exit
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class EMACrossoverDetector:
    """
    Detect EMA crossover signals (Golden Cross / Death Cross)
    
    Golden Cross: EMA20 crosses above EMA50 → BUY
    Death Cross: EMA20 crosses below EMA50 → SELL
    """
    
    def __init__(
        self,
        ema_fast: int = 20,
        ema_slow: int = 50,
        volume_multiplier: float = 1.2
    ):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.volume_multiplier = volume_multiplier
    
    
    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()
    
    
    def detect_golden_cross(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Detect Golden Cross
        
        Conditions:
        1. Previous day: EMA20 < EMA50
        2. Today: EMA20 > EMA50
        3. Volume confirmation
        """
        if idx < 1:
            return False
        
        current_idx = df.index[idx]
        prev_idx = df.index[idx - 1]
        
        current = df.loc[current_idx]
        prev = df.loc[prev_idx]
        
        # Check crossover
        if not (prev['ema20'] <= prev['ema50'] and current['ema20'] > current['ema50']):
            return False
        
        # Volume confirmation
        if current['volume'] < current['avg_volume_20'] * self.volume_multiplier:
            return False
        
        # Price confirmation (green candle)
        if current['close'] <= current['open']:
            return False
        
        # Price should be above EMA20
        if current['close'] < current['ema20']:
            return False
        
        return True
    
    
    def detect_death_cross(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Detect Death Cross
        
        Conditions:
        1. Previous day: EMA20 > EMA50
        2. Today: EMA20 < EMA50
        """
        if idx < 1:
            return False
        
        current_idx = df.index[idx]
        prev_idx = df.index[idx - 1]
        
        current = df.loc[current_idx]
        prev = df.loc[prev_idx]
        
        # Check crossover
        if prev['ema20'] > prev['ema50'] and current['ema20'] <= current['ema50']:
            return True
        
        return False
    
    
    def detect_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main detection logic
        
        Returns DataFrame with golden/death cross signals
        """
        df = df.copy()
        
        # Calculate indicators
        df['ema20'] = self.calculate_ema(df['close'], self.ema_fast)
        df['ema50'] = self.calculate_ema(df['close'], self.ema_slow)
        df['avg_volume_20'] = df['volume'].rolling(window=20).mean()
        
        # Initialize signal columns
        df['golden_cross'] = False
        df['death_cross'] = False
        df['buy_signal'] = False
        df['sell_signal'] = False
        
        for idx in range(len(df)):
            if idx < max(self.ema_fast, self.ema_slow, 20):
                continue
            
            current_idx = df.index[idx]
            
            # Check for golden cross
            if self.detect_golden_cross(df, idx):
                df.loc[current_idx, 'golden_cross'] = True
                df.loc[current_idx, 'buy_signal'] = True
            
            # Check for death cross
            if self.detect_death_cross(df, idx):
                df.loc[current_idx, 'death_cross'] = True
                df.loc[current_idx, 'sell_signal'] = True
        
        return df
    
    
    def get_signal_details(self, df: pd.DataFrame, signal_idx) -> Dict:
        """Get detailed information about a signal"""
        signal = df.loc[signal_idx]
        
        # Calculate stop loss (3% below entry)
        stop_loss = signal['close'] * 0.97
        
        details = {
            'date': signal.name,
            'price': float(signal['close']),
            'ema20': float(signal['ema20']),
            'ema50': float(signal['ema50']),
            'volume_ratio': float(signal['volume'] / signal['avg_volume_20']),
            'stop_loss': float(stop_loss),
            'risk_pct': 3.0,
            'signal_type': 'golden_cross' if signal['golden_cross'] else 'death_cross'
        }
        
        return details


def main():
    """Test the detector"""
    pass


if __name__ == '__main__':
    main()
