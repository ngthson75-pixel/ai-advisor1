#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANUAL SIGNAL TESTING - PULLBACK & EMA_CROSS

Purpose: Manually test signal generation with EOD data
Usage: python manual_test_signals.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import time
import time

try:
    from vnstock import Quote
except ImportError:
    print("❌ ERROR: vnstock not installed!")
    print("Run: pip install vnstock --break-system-packages")
    sys.exit(1)


class ManualSignalTester:
    """
    Manual testing for PULLBACK and EMA_CROSS signals
    
    Based on: daily_signal_scanner_eod.py
    """
    
    def __init__(self):
        self.results = []
        self.top_stocks = []  # Will store 343 top liquidity stocks
    
    # ========================================================================
    # GET TOP STOCKS BY LIQUIDITY
    # ========================================================================
    
    def get_top_stocks_by_liquidity(self, top_n=343):
        """
        Get top N stocks by liquidity from VN market
        
        Args:
            top_n: Number of top stocks to get (default 343)
        
        Returns:
            List of ticker codes
        """
        print(f"\n{'='*70}")
        print(f"📊 FETCHING TOP {top_n} STOCKS BY LIQUIDITY")
        print(f"{'='*70}")
        
        try:
            from vnstock import listing_companies
            
            print("📥 Downloading all stocks data...")
            
            # Get all stocks
            all_stocks = listing_companies()
            
            if all_stocks is None or len(all_stocks) == 0:
                print("❌ Cannot fetch stock list")
                return []
            
            print(f"✅ Found {len(all_stocks)} total stocks")
            
            # Filter by exchanges (HOSE, HNX, UPCOM)
            all_stocks = all_stocks[all_stocks['exchange'].isin(['HOSE', 'HNX', 'UPCOM'])]
            
            print(f"📊 After filtering: {len(all_stocks)} stocks")
            
            # Sort by market cap (proxy for liquidity)
            # If market_cap not available, we'll download recent volume data
            if 'market_cap' in all_stocks.columns:
                print("📊 Sorting by market cap...")
                all_stocks = all_stocks.sort_values('market_cap', ascending=False)
            else:
                print("📊 Getting volume data (this may take a few minutes)...")
                # Alternative: Use recent trading volume
                volumes = []
                
                for i, ticker in enumerate(all_stocks['ticker'].head(500).tolist(), 1):
                    if i % 50 == 0:
                        print(f"   Progress: {i}/500 stocks...")
                    
                    try:
                        quote = Quote(symbol=ticker, source='VCI')
                        df = quote.history(start=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                                         end=datetime.now().strftime('%Y-%m-%d'))
                        
                        if df is not None and len(df) > 0:
                            avg_volume = df['volume'].mean() if 'volume' in df.columns else 0
                            volumes.append({'ticker': ticker, 'avg_volume': avg_volume})
                    except:
                        volumes.append({'ticker': ticker, 'avg_volume': 0})
                    
                    time.sleep(0.1)  # Rate limiting
                
                volume_df = pd.DataFrame(volumes)
                volume_df = volume_df.sort_values('avg_volume', ascending=False)
                
                top_tickers = volume_df.head(top_n)['ticker'].tolist()
                
                print(f"✅ Selected top {len(top_tickers)} stocks by volume")
                return top_tickers
            
            # Get top N by market cap
            top_stocks = all_stocks.head(top_n)
            top_tickers = top_stocks['ticker'].tolist()
            
            print(f"✅ Selected top {len(top_tickers)} stocks by market cap")
            print(f"\nSample: {', '.join(top_tickers[:10])}...")
            
            return top_tickers
            
        except Exception as e:
            print(f"❌ Error fetching stocks: {e}")
            print(f"\n⚠️ Falling back to hardcoded top 50 stocks...")
            
            # Fallback: Top 50 blue chips
            fallback_stocks = [
                'VCB', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB', 'STB', 'MSN',
                'FPT', 'VRE', 'SSI', 'BID', 'CTG', 'PLX', 'GAS', 'MWG', 'VJC', 'HDB',
                'PDR', 'POW', 'SAB', 'NVL', 'BCM', 'KDH', 'DGC', 'REE', 'TPB', 'ACB',
                'GVR', 'PNJ', 'VGC', 'DHG', 'DPM', 'GMD', 'HPX', 'LPB', 'VCI', 'SSB',
                'BVH', 'HNG', 'TCH', 'DXG', 'VHC', 'PC1', 'DIG', 'HT1', 'VGS', 'IDC'
            ]
            
            print(f"✅ Using {len(fallback_stocks)} stocks")
            return fallback_stocks
    
    # ========================================================================
    # CORE FUNCTIONS (SAME AS SCANNER)
    # ========================================================================
    
    def get_last_trading_day(self):
        """Get last trading day (skip weekends)"""
        today = datetime.now()
        
        if today.weekday() == 5:  # Saturday
            last_day = today - timedelta(days=1)
        elif today.weekday() == 6:  # Sunday
            last_day = today - timedelta(days=2)
        else:
            last_day = today
        
        return last_day.strftime('%Y-%m-%d')
    
    def download_eod_data(self, ticker, days=100):
        """Download EOD data from vnstock (EXACT same as scanner)"""
        try:
            end_date = self.get_last_trading_day()
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - 
                         timedelta(days=days*2)).strftime('%Y-%m-%d')
            
            print(f"📥 Downloading data: {start_date} to {end_date}")
            
            # EXACT vnstock API call
            quote = Quote(symbol=ticker, source='VCI')
            df = quote.history(start=start_date, end=end_date)
            
            if df is None or len(df) == 0:
                print(f"❌ No data for {ticker}")
                return None
            
            # Process dataframe
            df = self.process_dataframe(df, ticker)
            
            if df is not None:
                print(f"✅ Downloaded {len(df)} bars")
            
            return df
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None
    
    def process_dataframe(self, df, ticker):
        """Process dataframe (EXACT same as scanner)"""
        try:
            # Rename columns
            mapping = {
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            
            for old, new in mapping.items():
                if old in df.columns:
                    df = df.rename(columns={old: new})
            
            # 🔧 FIX: Convert from thousands VND to VND
            # vnstock 3.3.1 returns prices in thousands (e.g., 36.5 = 36,500 VND)
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in df.columns:
                    df[col] = df[col] * 1000
            
            # Check required columns
            required = ['Close', 'High', 'Low', 'Volume']
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                print(f"❌ Missing columns: {missing}")
                return None
            
            # Add Open if missing
            if 'Open' not in df.columns:
                df['Open'] = df['Close'].shift(1)
            
            df = df.sort_index()
            df = df.dropna()
            
            if len(df) < 50:
                print(f"❌ Not enough data: {len(df)} bars")
                return None
            
            return df
            
        except Exception as e:
            print(f"❌ Process error: {e}")
            return None
    
    def calculate_ema(self, data, period):
        """Calculate EMA (EXACT same as scanner)"""
        return data['Close'].ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, data, period=14):
        """Calculate RSI (EXACT same as scanner)"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 0.0001)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    # ========================================================================
    # PULLBACK STRATEGY
    # ========================================================================
    
    def test_pullback(self, df, ticker):
        """
        Test PULLBACK strategy
        
        Conditions:
        1. EMA20 > EMA50 (uptrend)
        2. |Close - EMA20| / EMA20 < 0.03 (within 3%)
        3. RSI < 60
        """
        print(f"\n{'='*70}")
        print(f"🎯 PULLBACK STRATEGY TEST: {ticker}")
        print(f"{'='*70}")
        
        try:
            # Calculate indicators
            df['EMA20'] = self.calculate_ema(df, 20)
            df['EMA50'] = self.calculate_ema(df, 50)
            df['RSI'] = self.calculate_rsi(df, 14)
            
            latest = df.iloc[-1]
            
            close = latest['Close']
            ema20 = latest['EMA20']
            ema50 = latest['EMA50']
            rsi = latest['RSI']
            volume = latest['Volume']
            
            # Display current values
            print(f"\n📊 Current Values:")
            print(f"   Date: {self.get_last_trading_day()}")
            print(f"   Close: {close:,.0f} VND")
            print(f"   EMA20: {ema20:,.0f} VND")
            print(f"   EMA50: {ema50:,.0f} VND")
            print(f"   RSI: {rsi:.2f}")
            print(f"   Volume: {volume:,.0f}")
            
            # Check each condition
            print(f"\n✓ Condition Checks:")
            
            # Condition 1: Uptrend
            uptrend = ema20 > ema50
            print(f"\n   1️⃣ UPTREND (EMA20 > EMA50)")
            print(f"      EMA20: {ema20:,.0f}")
            print(f"      EMA50: {ema50:,.0f}")
            print(f"      Result: {uptrend} {'✅' if uptrend else '❌'}")
            
            # Condition 2: Near EMA20
            price_diff = abs(close - ema20)
            price_diff_pct = (price_diff / ema20) * 100
            near_ema20 = price_diff_pct < 3.0
            
            print(f"\n   2️⃣ NEAR EMA20 (within 3%)")
            print(f"      Price: {close:,.0f}")
            print(f"      EMA20: {ema20:,.0f}")
            print(f"      Difference: {price_diff:,.0f} VND ({price_diff_pct:.2f}%)")
            print(f"      Threshold: 3.00%")
            print(f"      Result: {near_ema20} {'✅' if near_ema20 else '❌'}")
            
            # Condition 3: RSI < 60
            rsi_ok = rsi < 60
            print(f"\n   3️⃣ RSI < 60")
            print(f"      RSI: {rsi:.2f}")
            print(f"      Threshold: 60.00")
            print(f"      Result: {rsi_ok} {'✅' if rsi_ok else '❌'}")
            
            # Final result
            signal_detected = uptrend and near_ema20 and rsi_ok
            
            print(f"\n{'='*70}")
            if signal_detected:
                print(f"✅ PULLBACK SIGNAL DETECTED!")
                print(f"{'='*70}")
                
                # Calculate entry/exit
                entry_price = close
                stop_loss = ema50 * 0.97
                take_profit = close * 1.08
                
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
                risk_pct = (risk / entry_price) * 100
                reward_pct = (reward / entry_price) * 100
                rr_ratio = reward / risk if risk > 0 else 0
                
                print(f"\n💰 Entry/Exit Prices:")
                print(f"   Entry:  {entry_price:,.0f} VND")
                print(f"   Stop:   {stop_loss:,.0f} VND (EMA50 * 0.97)")
                print(f"   Target: {take_profit:,.0f} VND (Entry * 1.08)")
                
                print(f"\n📊 Risk/Reward:")
                print(f"   Risk:   {risk:,.0f} VND ({risk_pct:.2f}%)")
                print(f"   Reward: {reward:,.0f} VND ({reward_pct:.2f}%)")
                print(f"   R/R:    {rr_ratio:.2f}x")
                
                # Calculate strength
                strength = 60
                bonuses = []
                
                avg_volume = df['Volume'].tail(20).mean()
                if volume > avg_volume:
                    strength += 10
                    bonuses.append("Volume > avg (+10)")
                
                if rsi < 40:
                    strength += 10
                    bonuses.append("RSI < 40 (+10)")
                
                if ema20 > ema50 * 1.02:
                    strength += 10
                    bonuses.append("Strong uptrend (+10)")
                
                is_priority = strength >= 75
                
                print(f"\n⭐ Quality Score:")
                print(f"   Base: 60")
                if bonuses:
                    for bonus in bonuses:
                        print(f"   + {bonus}")
                print(f"   Total: {strength}/100")
                print(f"   Priority: {'YES ⭐⭐⭐' if is_priority else 'NO'}")
                
                # Stock type
                if close >= 50000:
                    stock_type = "Blue Chip"
                elif close >= 20000:
                    stock_type = "Mid Cap"
                else:
                    stock_type = "Penny"
                
                print(f"   Type: {stock_type}")
                
                # Create signal dict
                signal = {
                    'ticker': ticker,
                    'strategy': 'PULLBACK',
                    'entry_price': float(entry_price),
                    'stop_loss': float(stop_loss),
                    'take_profit': float(take_profit),
                    'risk_pct': float(risk_pct),
                    'reward_pct': float(reward_pct),
                    'rr_ratio': float(rr_ratio),
                    'strength': int(strength),
                    'is_priority': int(is_priority),
                    'stock_type': stock_type,
                    'rsi': float(rsi),
                    'date': self.get_last_trading_day()
                }
                
                return signal
                
            else:
                print(f"❌ NO PULLBACK SIGNAL")
                print(f"{'='*70}")
                
                failed = []
                if not uptrend:
                    failed.append("Uptrend")
                if not near_ema20:
                    failed.append("Near EMA20")
                if not rsi_ok:
                    failed.append("RSI < 60")
                
                print(f"   Failed conditions: {', '.join(failed)}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # ========================================================================
    # EMA_CROSS STRATEGY
    # ========================================================================
    
    def test_ema_cross(self, df, ticker):
        """
        Test EMA_CROSS strategy
        
        Two paths:
        1. Golden Cross: EMA20 crosses above EMA50
        2. Near Cross: EMAs close (<2%) AND EMA20 > EMA50 AND RSI 30-70
        """
        print(f"\n{'='*70}")
        print(f"🎯 EMA_CROSS STRATEGY TEST: {ticker}")
        print(f"{'='*70}")
        
        try:
            # Calculate indicators
            df['EMA20'] = self.calculate_ema(df, 20)
            df['EMA50'] = self.calculate_ema(df, 50)
            df['RSI'] = self.calculate_rsi(df, 14)
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            close = latest['Close']
            ema20_curr = latest['EMA20']
            ema50_curr = latest['EMA50']
            ema20_prev = prev['EMA20']
            ema50_prev = prev['EMA50']
            rsi = latest['RSI']
            volume = latest['Volume']
            
            # Display current values
            print(f"\n📊 Current Values:")
            print(f"   Date: {self.get_last_trading_day()}")
            print(f"   Close: {close:,.0f} VND")
            print(f"   EMA20 (today): {ema20_curr:,.0f} VND")
            print(f"   EMA50 (today): {ema50_curr:,.0f} VND")
            print(f"   EMA20 (yesterday): {ema20_prev:,.0f} VND")
            print(f"   EMA50 (yesterday): {ema50_prev:,.0f} VND")
            print(f"   RSI: {rsi:.2f}")
            print(f"   Volume: {volume:,.0f}")
            
            # Check conditions
            print(f"\n✓ Condition Checks:")
            
            # PATH 1: Golden Cross
            print(f"\n   PATH 1: GOLDEN CROSS")
            
            prev_below = ema20_prev <= ema50_prev
            curr_above = ema20_curr > ema50_curr
            golden_cross = prev_below and curr_above
            
            print(f"      Yesterday: EMA20 ({ema20_prev:,.0f}) <= EMA50 ({ema50_prev:,.0f})")
            print(f"      Result: {prev_below} {'✅' if prev_below else '❌'}")
            
            print(f"      Today: EMA20 ({ema20_curr:,.0f}) > EMA50 ({ema50_curr:,.0f})")
            print(f"      Result: {curr_above} {'✅' if curr_above else '❌'}")
            
            print(f"      → Golden Cross: {golden_cross} {'✅' if golden_cross else '❌'}")
            
            # PATH 2: Near Cross
            print(f"\n   PATH 2: NEAR CROSS")
            
            ema_diff = abs(ema20_curr - ema50_curr)
            ema_diff_pct = (ema_diff / ema50_curr) * 100
            near_cross = ema_diff_pct < 2.0
            
            print(f"      EMA difference: {ema_diff:,.0f} VND ({ema_diff_pct:.2f}%)")
            print(f"      Threshold: 2.00%")
            print(f"      Near: {near_cross} {'✅' if near_cross else '❌'}")
            
            print(f"      EMA20 > EMA50: {curr_above} {'✅' if curr_above else '❌'}")
            
            rsi_ok = 30 <= rsi <= 70
            print(f"      RSI 30-70: {rsi_ok} {'✅' if rsi_ok else '❌'}")
            print(f"      (RSI: {rsi:.2f})")
            
            path2 = near_cross and curr_above and rsi_ok
            print(f"      → Near Cross: {path2} {'✅' if path2 else '❌'}")
            
            # Final result
            signal_detected = golden_cross or path2
            
            print(f"\n{'='*70}")
            if signal_detected:
                print(f"✅ EMA_CROSS SIGNAL DETECTED!")
                
                if golden_cross:
                    print(f"   Triggered by: Golden Cross (Path 1) ⭐")
                else:
                    print(f"   Triggered by: Near Cross (Path 2)")
                
                print(f"{'='*70}")
                
                # Calculate entry/exit
                entry_price = close
                stop_loss = ema50_curr * 0.96
                take_profit = close * 1.10
                
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
                risk_pct = (risk / entry_price) * 100
                reward_pct = (reward / entry_price) * 100
                rr_ratio = reward / risk if risk > 0 else 0
                
                print(f"\n💰 Entry/Exit Prices:")
                print(f"   Entry:  {entry_price:,.0f} VND")
                print(f"   Stop:   {stop_loss:,.0f} VND (EMA50 * 0.96)")
                print(f"   Target: {take_profit:,.0f} VND (Entry * 1.10)")
                
                print(f"\n📊 Risk/Reward:")
                print(f"   Risk:   {risk:,.0f} VND ({risk_pct:.2f}%)")
                print(f"   Reward: {reward:,.0f} VND ({reward_pct:.2f}%)")
                print(f"   R/R:    {rr_ratio:.2f}x")
                
                # Calculate strength
                strength = 65
                bonuses = []
                
                if golden_cross:
                    strength += 15
                    bonuses.append("Golden Cross (+15)")
                
                avg_volume = df['Volume'].tail(20).mean()
                if volume > avg_volume:
                    strength += 10
                    bonuses.append("Volume > avg (+10)")
                
                if 40 <= rsi <= 60:
                    strength += 10
                    bonuses.append("RSI 40-60 (+10)")
                
                is_priority = strength >= 80
                
                print(f"\n⭐ Quality Score:")
                print(f"   Base: 65")
                if bonuses:
                    for bonus in bonuses:
                        print(f"   + {bonus}")
                print(f"   Total: {strength}/100")
                print(f"   Priority: {'YES ⭐⭐⭐' if is_priority else 'NO'}")
                
                # Stock type
                if close >= 50000:
                    stock_type = "Blue Chip"
                elif close >= 20000:
                    stock_type = "Mid Cap"
                else:
                    stock_type = "Penny"
                
                print(f"   Type: {stock_type}")
                
                # Create signal dict
                signal = {
                    'ticker': ticker,
                    'strategy': 'EMA_CROSS',
                    'entry_price': float(entry_price),
                    'stop_loss': float(stop_loss),
                    'take_profit': float(take_profit),
                    'risk_pct': float(risk_pct),
                    'reward_pct': float(reward_pct),
                    'rr_ratio': float(rr_ratio),
                    'strength': int(strength),
                    'is_priority': int(is_priority),
                    'stock_type': stock_type,
                    'rsi': float(rsi),
                    'date': self.get_last_trading_day()
                }
                
                return signal
                
            else:
                print(f"❌ NO EMA_CROSS SIGNAL")
                print(f"{'='*70}")
                print(f"   Neither Golden Cross nor Near Cross conditions met")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # ========================================================================
    # TESTING WORKFLOWS
    # ========================================================================
    
    def test_single_stock(self, ticker, days=100):
        """Test a single stock for both strategies"""
        print(f"\n{'#'*70}")
        print(f"🧪 TESTING STOCK: {ticker}")
        print(f"{'#'*70}")
        print(f"Date: {self.get_last_trading_day()}")
        
        # Download data
        df = self.download_eod_data(ticker, days)
        
        if df is None:
            print(f"\n❌ Cannot test {ticker} - no data")
            return []
        
        signals = []
        
        # Test PULLBACK
        pullback = self.test_pullback(df, ticker)
        if pullback:
            signals.append(pullback)
            self.results.append(pullback)
        
        # Small delay
        time.sleep(0.5)
        
        # Test EMA_CROSS
        ema_cross = self.test_ema_cross(df, ticker)
        if ema_cross:
            signals.append(ema_cross)
            self.results.append(ema_cross)
        
        # Summary
        print(f"\n{'='*70}")
        print(f"📊 SUMMARY FOR {ticker}")
        print(f"{'='*70}")
        print(f"Signals found: {len(signals)}")
        
        if signals:
            for sig in signals:
                print(f"  ✅ {sig['strategy']}: {sig['strength']}/100 - R/R {sig['rr_ratio']:.2f}x")
        else:
            print(f"  ℹ️  No signals (normal based on market conditions)")
        
        return signals
    
    def test_multiple_stocks(self, tickers, days=100):
        """Test multiple stocks"""
        print(f"\n{'#'*70}")
        print(f"🧪 BATCH TESTING: {len(tickers)} STOCKS")
        print(f"{'#'*70}")
        print(f"Date: {self.get_last_trading_day()}")
        print(f"Stocks: {', '.join(tickers)}")
        
        all_signals = []
        success = 0
        failed = 0
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}]", end=" ")
            
            try:
                signals = self.test_single_stock(ticker, days)
                if signals:
                    all_signals.extend(signals)
                    success += 1
                else:
                    success += 1  # No signal is still success
                    
            except Exception as e:
                print(f"❌ Failed: {e}")
                failed += 1
            
            # Rate limiting
            if i < len(tickers):
                time.sleep(1)
        
        # Final summary
        self.print_final_summary(all_signals, len(tickers), success, failed)
        
        return all_signals
    
    def print_final_summary(self, signals, total, success, failed):
        """Print final summary"""
        print(f"\n{'#'*70}")
        print(f"📊 FINAL TEST SUMMARY")
        print(f"{'#'*70}")
        print(f"Date: {self.get_last_trading_day()}")
        print(f"Stocks tested: {total}")
        print(f"Successful: {success}")
        print(f"Failed: {failed}")
        print(f"Total signals: {len(signals)}")
        
        if signals:
            # By strategy
            pullback = [s for s in signals if s['strategy'] == 'PULLBACK']
            ema_cross = [s for s in signals if s['strategy'] == 'EMA_CROSS']
            priority = [s for s in signals if s['is_priority'] == 1]
            
            print(f"\n📈 By Strategy:")
            print(f"   PULLBACK: {len(pullback)}")
            print(f"   EMA_CROSS: {len(ema_cross)}")
            print(f"   Priority: {len(priority)}")
            
            # Top signals
            print(f"\n⭐ Top 5 Signals:")
            sorted_sigs = sorted(signals, key=lambda x: x['strength'], reverse=True)[:5]
            
            for i, sig in enumerate(sorted_sigs, 1):
                priority_mark = "⭐" if sig['is_priority'] else ""
                print(f"   {i}. {sig['ticker']:4s} - {sig['strategy']:10s} - "
                      f"{sig['strength']:3d}/100 - R/R {sig['rr_ratio']:.2f}x {priority_mark}")
            
            # Export option
            print(f"\n💾 Export Results:")
            export = input("Export to CSV? (y/n): ").strip().lower()
            if export == 'y':
                self.export_to_csv(signals)
        else:
            print(f"\n  ℹ️  No signals found (normal based on market conditions)")
    
    def export_to_csv(self, signals):
        """Export signals to CSV"""
        if not signals:
            print("⚠️  No signals to export")
            return
        
        filename = f"test_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = pd.DataFrame(signals)
        df.to_csv(filename, index=False)
        
        print(f"✅ Exported to: {filename}")
        print(f"   Rows: {len(signals)}")
        print(f"   Columns: {', '.join(df.columns)}")


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """Main program"""
    print("\n" + "="*70)
    print("🧪 MANUAL SIGNAL TESTING - PULLBACK & EMA_CROSS")
    print("="*70)
    
    tester = ManualSignalTester()
    
    print("\nSelect testing mode:")
    print("1. Test single stock")
    print("2. Test 5 popular stocks (VCB, VHM, HPG, FPT, MBB)")
    print("3. Test 10 stocks (Quick batch)")
    print("4. Test TOP 343 STOCKS by liquidity (⚠️ Takes 30-60 mins)")
    print("5. Test TOP 50 stocks (Quick scan)")
    print("6. Custom stock list")
    print("7. Exit")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    if choice == '1':
        # Single stock
        ticker = input("Enter ticker code (e.g., VCB): ").strip().upper()
        if ticker:
            tester.test_single_stock(ticker)
            
            if tester.results:
                export = input("\nExport to CSV? (y/n): ").strip().lower()
                if export == 'y':
                    tester.export_to_csv(tester.results)
    
    elif choice == '2':
        # 5 popular stocks
        stocks = ['VCB', 'VHM', 'HPG', 'FPT', 'MBB']
        tester.test_multiple_stocks(stocks)
    
    elif choice == '3':
        # 10 stocks batch
        stocks = ['VCB', 'VHM', 'HPG', 'FPT', 'MBB', 
                  'TCB', 'VNM', 'VIC', 'STB', 'MSN']
        tester.test_multiple_stocks(stocks)
    
    elif choice == '4':
        # TOP 343 STOCKS - FULL SCAN
        print("\n" + "⚠️"*35)
        print("⚠️  WARNING: FULL SCAN OF 343 STOCKS")
        print("⚠️"*35)
        print("\nThis will:")
        print("  • Download data for 343 stocks")
        print("  • Take approximately 30-60 minutes")
        print("  • Use significant API calls")
        print("  • Generate comprehensive report")
        
        confirm = input("\n📍 Continue? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            # Get top 343 stocks
            print("\n🔍 Getting top 343 stocks by liquidity...")
            top_stocks = tester.get_top_stocks_by_liquidity(343)
            
            if top_stocks:
                print(f"\n✅ Got {len(top_stocks)} stocks")
                print(f"📊 Starting comprehensive scan...")
                
                # Test all
                tester.test_multiple_stocks(top_stocks)
            else:
                print("\n❌ Cannot fetch stock list")
        else:
            print("\n⚠️  Scan cancelled")
    
    elif choice == '5':
        # TOP 50 stocks - QUICK SCAN
        print("\n🔍 Getting top 50 stocks by liquidity...")
        top_stocks = tester.get_top_stocks_by_liquidity(50)
        
        if top_stocks:
            print(f"\n✅ Got {len(top_stocks)} stocks")
            tester.test_multiple_stocks(top_stocks)
        else:
            print("\n❌ Cannot fetch stock list")
    
    elif choice == '6':
        # Custom list
        tickers_input = input("Enter ticker codes (comma-separated, e.g., VCB,VHM,HPG): ").strip()
        if tickers_input:
            tickers = [t.strip().upper() for t in tickers_input.split(',')]
            tester.test_multiple_stocks(tickers)
    
    elif choice == '7':
        print("\n👋 Goodbye!")
        return
    
    else:
        print("\n❌ Invalid choice!")
    
    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
