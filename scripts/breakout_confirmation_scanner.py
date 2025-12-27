#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BREAKOUT CONFIRMATION SCANNER

Chiến lược: Nền giá chặt → Breakout với volume → Xác nhận → Entry
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class BreakoutConfirmationDetector:
    """
    Detect breakout with confirmation setups
    
    Conditions:
    1. Consolidation ≥ 10 days (tight range)
    2. Breakout with volume ≥ 2x
    3. Confirmation (pullback test or continuation)
    """
    
    def __init__(
        self,
        consolidation_days: int = 10,
        volume_multiplier: float = 2.0,
        atr_threshold: float = 0.7,
        breakout_lookback: int = 20
    ):
        self.consolidation_days = consolidation_days
        self.volume_multiplier = volume_multiplier
        self.atr_threshold = atr_threshold
        self.breakout_lookback = breakout_lookback
    
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    
    def detect_consolidation(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Check if price is consolidating
        
        Consolidation = ATR declining + tight range
        """
        if idx < self.consolidation_days + 20:
            return False
        
        # Get consolidation period
        period_start = idx - self.consolidation_days
        period_end = idx
        
        # Calculate ATR for consolidation period
        atr_current = df.loc[period_end, 'atr']
        atr_20 = df.loc[period_start:period_end, 'atr'].mean()
        
        # ATR should be declining (tight range)
        if atr_current > atr_20 * self.atr_threshold:
            return False
        
        # Check price range is tight
        period_data = df.loc[period_start:period_end]
        price_range = (period_data['high'].max() - period_data['low'].min()) / period_data['close'].mean()
        
        # Range should be < 5% over consolidation period
        if price_range > 0.05:
            return False
        
        return True
    
    
    def detect_breakout(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Check if price breaks out with volume
        
        Breakout = Close > Highest(20) + Volume ≥ 2x
        """
        if idx < self.breakout_lookback:
            return False
        
        current = df.loc[idx]
        lookback_data = df.loc[idx - self.breakout_lookback:idx - 1]
        
        # Breakout condition
        highest_high = lookback_data['high'].max()
        if current['close'] <= highest_high:
            return False
        
        # Volume confirmation
        avg_volume = lookback_data['volume'].mean()
        if current['volume'] < avg_volume * self.volume_multiplier:
            return False
        
        # Strong candle (close near high)
        candle_strength = (current['close'] - current['low']) / (current['high'] - current['low'])
        if candle_strength < 0.7:
            return False
        
        return True
    
    
    def detect_confirmation(self, df: pd.DataFrame, breakout_idx: int, current_idx: int) -> Optional[str]:
        """
        Check for confirmation after breakout
        
        Returns: 'pullback', 'continuation', 'sideways', or None
        """
        if current_idx <= breakout_idx:
            return None
        
        breakout_candle = df.loc[breakout_idx]
        current = df.loc[current_idx]
        
        # Get data since breakout
        period_data = df.loc[breakout_idx:current_idx]
        
        # Pullback test (BEST!)
        # Price comes back to test breakout level but holds
        if current['low'] <= breakout_candle['close'] * 1.02:  # Within 2% of breakout
            if current['close'] > breakout_candle['close'] * 0.98:  # But holds above breakout
                if current['volume'] < period_data['volume'].mean() * 1.2:  # Lower volume (no panic)
                    return 'pullback'
        
        # Continuation (GOOD)
        # Price continues higher
        if current['close'] > breakout_candle['high']:
            if current['volume'] >= period_data['volume'].mean() * 1.5:
                return 'continuation'
        
        # Sideways (OK)
        # Price consolidates above breakout
        if current['low'] > breakout_candle['close']:
            range_pct = (period_data['high'].max() - period_data['low'].min()) / period_data['close'].mean()
            if range_pct < 0.03:  # Tight 3% range
                return 'sideways'
        
        return None
    
    
    def detect_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main detection logic
        
        Returns DataFrame with signals
        """
        df = df.copy()
        
        # Calculate indicators
        df['atr'] = self.calculate_atr(df)
        df['avg_volume_20'] = df['volume'].rolling(window=20).mean()
        df['highest_20'] = df['high'].rolling(window=self.breakout_lookback).max()
        
        # Initialize signal columns
        df['consolidation'] = False
        df['breakout'] = False
        df['confirmation'] = None
        df['buy_signal'] = False
        df['breakout_level'] = np.nan
        df['breakout_idx'] = np.nan
        
        # Track breakouts waiting for confirmation
        pending_breakouts = {}  # {idx: breakout_level}
        
        for idx in range(len(df)):
            current_idx = df.index[idx]
            
            # Check consolidation
            if self.detect_consolidation(df, current_idx):
                df.loc[current_idx, 'consolidation'] = True
            
            # Check breakout (only if consolidation present in recent past)
            recent_consolidation = df.loc[max(0, idx - 20):idx, 'consolidation'].any()
            
            if recent_consolidation and self.detect_breakout(df, current_idx):
                df.loc[current_idx, 'breakout'] = True
                df.loc[current_idx, 'breakout_level'] = df.loc[current_idx, 'close']
                pending_breakouts[current_idx] = df.loc[current_idx, 'close']
            
            # Check confirmation for pending breakouts
            if pending_breakouts:
                for breakout_idx, breakout_level in list(pending_breakouts.items()):
                    # Only check within 5 days of breakout
                    if idx - df.index.get_loc(breakout_idx) > 5:
                        del pending_breakouts[breakout_idx]
                        continue
                    
                    confirmation_type = self.detect_confirmation(df, breakout_idx, current_idx)
                    
                    if confirmation_type:
                        df.loc[current_idx, 'confirmation'] = confirmation_type
                        df.loc[current_idx, 'buy_signal'] = True
                        df.loc[current_idx, 'breakout_idx'] = breakout_idx
                        df.loc[current_idx, 'breakout_level'] = breakout_level
                        
                        # Remove from pending
                        del pending_breakouts[breakout_idx]
        
        return df
    
    
    def get_signal_details(self, df: pd.DataFrame, signal_idx) -> Dict:
        """Get detailed information about a signal"""
        signal = df.loc[signal_idx]
        
        details = {
            'date': signal.name,
            'price': float(signal['close']),
            'confirmation_type': signal['confirmation'],
            'breakout_level': float(signal['breakout_level']),
            'volume_ratio': float(signal['volume'] / signal['avg_volume_20']),
            'atr': float(signal['atr']),
            'stop_loss': float(signal['breakout_level'] * 0.98),  # 2% below breakout
            'risk_pct': 2.0
        }
        
        return details


def main():
    """Test the detector"""
    # This would be used by backtest system
    pass


if __name__ == '__main__':
    main()
