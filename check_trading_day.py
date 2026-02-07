#!/usr/bin/env python3
"""
VIETNAM TRADING DAY CHECKER
Kiểm tra xem hôm nay có phải ngày giao dịch chứng khoán không

Usage:
    python check_trading_day.py
    
Exit codes:
    0 - Ngày giao dịch (trading day)
    1 - Ngày nghỉ (weekend/holiday)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ==============================================================================
# CONFIGURATION
# ==============================================================================

HOLIDAYS_FILE = Path(__file__).parent / "vietnam_holidays.json"

# ==============================================================================
# LOAD HOLIDAYS
# ==============================================================================

def load_holidays():
    """Load danh sách ngày lễ từ JSON file"""
    try:
        with open(HOLIDAYS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"⚠️  Warning: {HOLIDAYS_FILE} not found. Using empty holiday list.")
        return {"holidays": {}, "market_schedule": {"trading_days": [1, 2, 3, 4, 5]}}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {HOLIDAYS_FILE}: {e}")
        sys.exit(2)

# ==============================================================================
# CHECK TRADING DAY
# ==============================================================================

def is_trading_day(date=None, verbose=True):
    """
    Kiểm tra xem date có phải ngày giao dịch không
    
    Args:
        date: datetime object (default: today)
        verbose: Print detailed info
        
    Returns:
        bool: True if trading day, False otherwise
    """
    
    if date is None:
        date = datetime.now()
    
    # Load holiday data
    data = load_holidays()
    holidays = data.get("holidays", {})
    market_schedule = data.get("market_schedule", {})
    trading_days = market_schedule.get("trading_days", [1, 2, 3, 4, 5])
    
    # Format date
    date_str = date.strftime("%Y-%m-%d")
    year_str = str(date.year)
    weekday = date.isoweekday()  # Monday=1, Sunday=7
    
    if verbose:
        print("\n" + "="*70)
        print("📅 VIETNAM TRADING DAY CHECK")
        print("="*70)
        print(f"\nDate: {date_str}")
        print(f"Weekday: {date.strftime('%A')} (ISO: {weekday})")
    
    # Check 1: Weekend?
    if weekday not in trading_days:
        if verbose:
            print(f"\n❌ WEEKEND - Market closed")
            print(f"   Weekday {weekday} not in trading days {trading_days}")
        return False
    
    # Check 2: Public holiday?
    year_holidays = holidays.get(year_str, [])
    if date_str in year_holidays:
        if verbose:
            print(f"\n❌ PUBLIC HOLIDAY - Market closed")
            print(f"   {date_str} is in holiday list")
        return False
    
    # Trading day!
    if verbose:
        print(f"\n✅ TRADING DAY - Market open")
        trading_hours = market_schedule.get("trading_hours", {})
        print(f"   Morning: {trading_hours.get('morning_start', 'N/A')} - {trading_hours.get('morning_end', 'N/A')}")
        print(f"   Afternoon: {trading_hours.get('afternoon_start', 'N/A')} - {trading_hours.get('afternoon_end', 'N/A')}")
    
    return True

# ==============================================================================
# NEXT TRADING DAY
# ==============================================================================

def next_trading_day(from_date=None, verbose=True):
    """Tìm ngày giao dịch tiếp theo"""
    
    if from_date is None:
        from_date = datetime.now()
    
    current = from_date + timedelta(days=1)
    max_days = 30  # Safety limit
    
    for i in range(max_days):
        if is_trading_day(current, verbose=False):
            if verbose:
                print(f"\n📅 Next trading day: {current.strftime('%Y-%m-%d (%A)')}")
            return current
        current += timedelta(days=1)
    
    if verbose:
        print(f"\n⚠️  No trading day found in next {max_days} days")
    return None

# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def main():
    """Main CLI function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check if today is a Vietnam stock market trading day"
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Check specific date (YYYY-MM-DD). Default: today'
    )
    parser.add_argument(
        '--next',
        action='store_true',
        help='Show next trading day'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Quiet mode (exit code only)'
    )
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        try:
            check_date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Invalid date format: {args.date}")
            print("   Use: YYYY-MM-DD")
            sys.exit(2)
    else:
        check_date = datetime.now()
    
    # Check trading day
    is_trading = is_trading_day(check_date, verbose=not args.quiet)
    
    # Show next trading day if requested
    if args.next:
        next_trading_day(check_date, verbose=not args.quiet)
    
    # Print summary
    if not args.quiet:
        print("\n" + "="*70)
        if is_trading:
            print("✅ EXIT CODE 0 - Trading day")
        else:
            print("❌ EXIT CODE 1 - Non-trading day")
        print("="*70 + "\n")
    
    # Exit with appropriate code
    sys.exit(0 if is_trading else 1)

# ==============================================================================
# RUN
# ==============================================================================

if __name__ == '__main__':
    main()
