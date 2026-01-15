#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAILY SIGNAL RUNNER

Chạy mỗi ngày 6:00 PM:
1. Scan BUY signals (daily_signal_scanner_eod.py)
2. Generate SELL signals (sell_signal_generator.py)

Sử dụng để tích hợp vào GitHub Actions hoặc cron job
"""

import sys
import os
from datetime import datetime

# Add scripts directory to path
sys.path.append(os.path.dirname(__file__))

def run_buy_signal_scanner():
    """Run the BUY signal scanner"""
    print("\n" + "=" * 70)
    print("📊 STEP 1: SCANNING BUY SIGNALS")
    print("=" * 70)
    
    try:
        # Import scanner
        from daily_signal_scanner_eod import main as scanner_main
        
        # Run scanner
        scanner_main()
        
        print("\n✅ BUY signal scan completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Error running BUY scanner: {e}")
        return False

def run_sell_signal_generator():
    """Run the SELL signal generator"""
    print("\n" + "=" * 70)
    print("🎯 STEP 2: GENERATING SELL SIGNALS")
    print("=" * 70)
    
    try:
        # Import generator
        from sell_signal_generator import SellSignalGenerator
        
        # Create generator
        generator = SellSignalGenerator()
        
        # Generate SELL signals
        sell_count = generator.generate_sell_signals()
        
        if sell_count > 0:
            print(f"\n✅ Created {sell_count} SELL signals")
        else:
            print(f"\n📭 No SELL signals needed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error generating SELL signals: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main runner function"""
    print("\n" + "=" * 70)
    print("🚀 DAILY SIGNAL RUNNER")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Step 1: Scan BUY signals
    buy_success = run_buy_signal_scanner()
    
    if not buy_success:
        print("\n⚠️  BUY scanner failed, but continuing to SELL generation...")
    
    # Step 2: Generate SELL signals
    sell_success = run_sell_signal_generator()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DAILY SIGNAL RUNNER - SUMMARY")
    print("=" * 70)
    print(f"BUY Signals:  {'✅ Success' if buy_success else '❌ Failed'}")
    print(f"SELL Signals: {'✅ Success' if sell_success else '❌ Failed'}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Exit code
    if buy_success and sell_success:
        print("\n🎉 All tasks completed successfully!")
        return 0
    else:
        print("\n⚠️  Some tasks failed, check logs above")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
