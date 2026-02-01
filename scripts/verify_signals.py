#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIGNAL VERIFICATION SYSTEM

Purpose: Verify signals in staging/production database match manual calculation
Usage: python verify_signals.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import requests
import json

try:
    from vnstock import Quote
except ImportError:
    print("❌ ERROR: vnstock not installed!")
    print("Run: pip install vnstock --break-system-packages")
    sys.exit(1)


class SignalVerifier:
    """
    Verify signals in database match manual calculation
    
    Workflow:
    1. Get signals from database (staging or production)
    2. Recalculate manually using EOD data
    3. Compare results
    4. Report discrepancies
    """
    
    # API endpoints
    STAGING_API = "https://ai-advisor1-staging.onrender.com/api"
    PRODUCTION_API = "https://ai-advisor1-backend.onrender.com/api"
    
    def __init__(self, environment='staging'):
        """
        Args:
            environment: 'staging' or 'production'
        """
        self.environment = environment
        
        if environment == 'staging':
            self.api_base = self.STAGING_API
            self.env_name = "STAGING"
        elif environment == 'production':
            self.api_base = self.PRODUCTION_API
            self.env_name = "PRODUCTION"
        else:
            raise ValueError("environment must be 'staging' or 'production'")
        
        print(f"\n{'='*70}")
        print(f"🔍 SIGNAL VERIFIER - {self.env_name}")
        print(f"{'='*70}")
        print(f"API: {self.api_base}")
    
    # ========================================================================
    # DATABASE QUERIES
    # ========================================================================
    
    def get_database_signals(self):
        """Get signals from database via API"""
        print(f"\n📥 Fetching signals from {self.env_name} database...")
        
        try:
            url = f"{self.api_base}/signals"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    signals = data.get('signals', [])
                    print(f"✅ Found {len(signals)} signals in database")
                    return signals
                else:
                    print(f"❌ API error: {data.get('error', 'Unknown')}")
                    return []
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            print(f"⚠️  Timeout - {self.env_name} backend may be sleeping (free tier)")
            print(f"   Waiting 30s for cold start...")
            
            try:
                import time
                time.sleep(30)
                response = requests.get(url, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        signals = data.get('signals', [])
                        print(f"✅ Found {len(signals)} signals after retry")
                        return signals
                
            except Exception as e:
                print(f"❌ Retry failed: {e}")
                return []
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    # ========================================================================
    # MANUAL CALCULATION (SAME AS manual_test_signals.py)
    # ========================================================================
    
    def get_last_trading_day(self):
        """Get last trading day"""
        today = datetime.now()
        
        if today.weekday() == 5:
            last_day = today - timedelta(days=1)
        elif today.weekday() == 6:
            last_day = today - timedelta(days=2)
        else:
            last_day = today
        
        return last_day.strftime('%Y-%m-%d')
    
    def download_eod_data(self, ticker, days=100):
        """Download EOD data"""
        try:
            end_date = self.get_last_trading_day()
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - 
                         timedelta(days=days*2)).strftime('%Y-%m-%d')
            
            quote = Quote(symbol=ticker, source='VCI')
            df = quote.history(start=start_date, end=end_date)
            
            if df is None or len(df) == 0:
                return None
            
            # Process
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
            
            if 'Open' not in df.columns:
                df['Open'] = df['Close'].shift(1)
            
            df = df.sort_index()
            df = df.dropna()
            
            return df if len(df) >= 50 else None
            
        except Exception as e:
            print(f"⚠️  Error downloading {ticker}: {e}")
            return None
    
    def calculate_ema(self, data, period):
        """Calculate EMA"""
        return data['Close'].ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, data, period=14):
        """Calculate RSI"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 0.0001)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def recalculate_signal(self, ticker):
        """
        Recalculate signal manually for a ticker
        
        Returns:
            dict with PULLBACK and EMA_CROSS signals (if any)
        """
        df = self.download_eod_data(ticker, days=100)
        
        if df is None:
            return None
        
        # Calculate indicators
        df['EMA20'] = self.calculate_ema(df, 20)
        df['EMA50'] = self.calculate_ema(df, 50)
        df['RSI'] = self.calculate_rsi(df, 14)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        close = latest['Close']
        ema20 = latest['EMA20']
        ema50 = latest['EMA50']
        ema20_prev = prev['EMA20']
        ema50_prev = prev['EMA50']
        rsi = latest['RSI']
        
        result = {
            'ticker': ticker,
            'date': self.get_last_trading_day(),
            'close': float(close),
            'ema20': float(ema20),
            'ema50': float(ema50),
            'rsi': float(rsi),
            'signals': []
        }
        
        # Check PULLBACK
        uptrend = ema20 > ema50
        near_ema20 = abs(close - ema20) / ema20 < 0.03
        rsi_ok = rsi < 60
        
        if uptrend and near_ema20 and rsi_ok:
            result['signals'].append({
                'strategy': 'PULLBACK',
                'entry_price': float(close),
                'stop_loss': float(ema50 * 0.97),
                'take_profit': float(close * 1.08)
            })
        
        # Check EMA_CROSS
        golden_cross = (ema20_prev <= ema50_prev) and (ema20 > ema50)
        near_cross = abs(ema20 - ema50) / ema50 < 0.02
        rsi_range = 30 <= rsi <= 70
        
        if golden_cross or (near_cross and ema20 > ema50 and rsi_range):
            result['signals'].append({
                'strategy': 'EMA_CROSS',
                'entry_price': float(close),
                'stop_loss': float(ema50 * 0.96),
                'take_profit': float(close * 1.10)
            })
        
        return result
    
    # ========================================================================
    # COMPARISON
    # ========================================================================
    
    def compare_signals(self, db_signals):
        """
        Compare database signals with manual calculation
        
        Args:
            db_signals: List of signals from database
        
        Returns:
            dict with comparison results
        """
        print(f"\n{'='*70}")
        print(f"🔍 VERIFYING {len(db_signals)} SIGNALS")
        print(f"{'='*70}")
        
        results = {
            'total_checked': 0,
            'matches': [],
            'discrepancies': [],
            'missing_in_db': [],
            'extra_in_db': []
        }
        
        # Group DB signals by ticker
        db_by_ticker = {}
        for sig in db_signals:
            ticker = sig.get('ticker')
            if ticker not in db_by_ticker:
                db_by_ticker[ticker] = []
            db_by_ticker[ticker].append(sig)
        
        # Check each ticker
        for ticker in db_by_ticker.keys():
            print(f"\n{'─'*70}")
            print(f"Checking {ticker}...")
            
            results['total_checked'] += 1
            
            # Recalculate manually
            manual = self.recalculate_signal(ticker)
            
            if manual is None:
                print(f"  ⚠️  Cannot download data for {ticker}")
                continue
            
            db_sigs = db_by_ticker[ticker]
            manual_sigs = manual['signals']
            
            print(f"  DB signals: {len(db_sigs)}")
            print(f"  Manual signals: {len(manual_sigs)}")
            
            # Compare
            for db_sig in db_sigs:
                strategy = db_sig.get('strategy')
                
                # Find matching manual signal
                manual_match = None
                for m_sig in manual_sigs:
                    if m_sig['strategy'] == strategy:
                        manual_match = m_sig
                        break
                
                if manual_match:
                    # Compare prices
                    db_entry = float(db_sig.get('entry_price', 0))
                    manual_entry = float(manual_match['entry_price'])
                    
                    diff = abs(db_entry - manual_entry)
                    diff_pct = (diff / manual_entry * 100) if manual_entry > 0 else 0
                    
                    if diff_pct < 1.0:  # Within 1%
                        print(f"  ✅ {strategy}: MATCH (diff: {diff_pct:.2f}%)")
                        results['matches'].append({
                            'ticker': ticker,
                            'strategy': strategy,
                            'db_entry': db_entry,
                            'manual_entry': manual_entry,
                            'diff_pct': diff_pct
                        })
                    else:
                        print(f"  ⚠️  {strategy}: DISCREPANCY (diff: {diff_pct:.2f}%)")
                        results['discrepancies'].append({
                            'ticker': ticker,
                            'strategy': strategy,
                            'db_entry': db_entry,
                            'manual_entry': manual_entry,
                            'diff_pct': diff_pct
                        })
                else:
                    print(f"  ❌ {strategy}: In DB but NOT in manual calculation")
                    results['extra_in_db'].append({
                        'ticker': ticker,
                        'strategy': strategy,
                        'db_entry': db_sig.get('entry_price')
                    })
            
            # Check for signals in manual but not in DB
            for m_sig in manual_sigs:
                strategy = m_sig['strategy']
                
                db_match = None
                for db_sig in db_sigs:
                    if db_sig.get('strategy') == strategy:
                        db_match = db_sig
                        break
                
                if not db_match:
                    print(f"  ⚠️  {strategy}: In manual but MISSING from DB")
                    results['missing_in_db'].append({
                        'ticker': ticker,
                        'strategy': strategy,
                        'manual_entry': m_sig['entry_price']
                    })
        
        return results
    
    def print_summary(self, results):
        """Print comparison summary"""
        print(f"\n{'='*70}")
        print(f"📊 VERIFICATION SUMMARY")
        print(f"{'='*70}")
        
        print(f"\nTickers checked: {results['total_checked']}")
        print(f"Matching signals: {len(results['matches'])}")
        print(f"Discrepancies: {len(results['discrepancies'])}")
        print(f"Missing in DB: {len(results['missing_in_db'])}")
        print(f"Extra in DB: {len(results['extra_in_db'])}")
        
        # Accuracy
        total_comparisons = (len(results['matches']) + 
                           len(results['discrepancies']) + 
                           len(results['extra_in_db']))
        
        if total_comparisons > 0:
            accuracy = (len(results['matches']) / total_comparisons) * 100
            print(f"\n✅ Accuracy: {accuracy:.1f}%")
        
        # Details
        if results['discrepancies']:
            print(f"\n⚠️  DISCREPANCIES FOUND:")
            for disc in results['discrepancies']:
                print(f"   {disc['ticker']} - {disc['strategy']}")
                print(f"      DB: {disc['db_entry']:,.0f}")
                print(f"      Manual: {disc['manual_entry']:,.0f}")
                print(f"      Diff: {disc['diff_pct']:.2f}%")
        
        if results['missing_in_db']:
            print(f"\n⚠️  MISSING IN DATABASE:")
            for miss in results['missing_in_db']:
                print(f"   {miss['ticker']} - {miss['strategy']}")
                print(f"      Manual entry: {miss['manual_entry']:,.0f}")
        
        if results['extra_in_db']:
            print(f"\n⚠️  EXTRA IN DATABASE (false positives?):")
            for extra in results['extra_in_db']:
                print(f"   {extra['ticker']} - {extra['strategy']}")
                print(f"      DB entry: {extra['db_entry']:,.0f}")
    
    # ========================================================================
    # MAIN WORKFLOW
    # ========================================================================
    
    def run_verification(self):
        """Run full verification workflow"""
        # Get DB signals
        db_signals = self.get_database_signals()
        
        if not db_signals:
            print(f"\n⚠️  No signals in {self.env_name} database")
            print(f"   Possible reasons:")
            print(f"   - Scanner hasn't run yet")
            print(f"   - Database is empty")
            print(f"   - API connection issue")
            return None
        
        # Compare
        results = self.compare_signals(db_signals)
        
        # Print summary
        self.print_summary(results)
        
        return results


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """Main program"""
    print("\n" + "="*70)
    print("🔍 SIGNAL VERIFICATION SYSTEM")
    print("="*70)
    
    print("\nSelect environment to verify:")
    print("1. STAGING (ai-advisor1-staging.onrender.com)")
    print("2. PRODUCTION (ai-advisor1-backend.onrender.com)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        verifier = SignalVerifier('staging')
        results = verifier.run_verification()
        
    elif choice == '2':
        verifier = SignalVerifier('production')
        results = verifier.run_verification()
        
    elif choice == '3':
        print("\n👋 Goodbye!")
        return
    
    else:
        print("\n❌ Invalid choice!")
        return
    
    if results:
        # Ask to export
        export = input("\nExport results to JSON? (y/n): ").strip().lower()
        if export == 'y':
            filename = f"verification_{verifier.environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"✅ Exported to: {filename}")
    
    print("\n" + "="*70)
    print("✅ VERIFICATION COMPLETE")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
