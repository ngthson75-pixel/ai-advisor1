#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAILY PORTFOLIO PRICE AUTO-UPDATE SCRIPT

Cron job này chạy hàng ngày sau giờ đóng cửa (17:00) để:
1. Lấy giá EOD của tất cả stocks trong portfolios
2. Update current_price cho mỗi portfolio entry
3. Log kết quả

Setup on Render:
- Go to Dashboard → Environment → Add Cron Job
- Schedule: 0 17 * * 1-5  (Mon-Fri at 5PM Vietnam time)
- Command: python scripts/update_portfolio_prices.py

Or run manually:
    python scripts/update_portfolio_prices.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from vnstock import Vnstock
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Install: pip install vnstock sqlalchemy")
    sys.exit(1)


# ============================================================================
# DATABASE SETUP
# ============================================================================

Base = declarative_base()

class Portfolio(Base):
    """Portfolio table model"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)  # Will be updated
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    price_updated_at = Column(DateTime, nullable=True)  # Last price update


# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# ============================================================================
# PRICE FETCHER
# ============================================================================

class PriceFetcher:
    """Fetch EOD prices from vnstock"""
    
    def __init__(self):
        self.stock_api = Vnstock()
        self.cache = {}  # Avoid fetching same ticker multiple times
    
    def get_eod_price(self, ticker):
        """
        Get End-of-Day price for a ticker
        
        Returns:
            float: Price or None if failed
        """
        # Check cache first
        if ticker in self.cache:
            return self.cache[ticker]
        
        try:
            stock = self.stock_api.stock(symbol=ticker, source='VCI')
            
            # Try intraday first (if market just closed)
            try:
                intraday = stock.quote.intraday(symbol=ticker, page_size=1)
                if not intraday.empty:
                    price = float(intraday['close'].iloc[-1])
                    self.cache[ticker] = price
                    return price
            except:
                pass
            
            # Fallback to EOD history
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            
            daily = stock.quote.history(symbol=ticker, start=yesterday, end=today)
            
            if not daily.empty:
                price = float(daily['close'].iloc[-1])
                self.cache[ticker] = price
                return price
            
            return None
            
        except Exception as e:
            print(f"  ❌ Error fetching {ticker}: {e}")
            return None


# ============================================================================
# UPDATE LOGIC
# ============================================================================

def update_all_portfolio_prices():
    """
    Main function: Update prices for all portfolios
    """
    
    print("=" * 70)
    print("📊 PORTFOLIO PRICE AUTO-UPDATE")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    session = Session()
    fetcher = PriceFetcher()
    
    try:
        # Get all portfolios
        portfolios = session.query(Portfolio).all()
        
        if not portfolios:
            print("⚠️  No portfolios found in database")
            return
        
        # Get unique tickers
        unique_tickers = set(p.ticker for p in portfolios)
        print(f"📈 Found {len(portfolios)} portfolio entries")
        print(f"📊 Unique tickers: {len(unique_tickers)}")
        print()
        
        # Fetch prices for all unique tickers
        print("🔄 Fetching latest prices...")
        print()
        
        ticker_prices = {}
        success_count = 0
        fail_count = 0
        
        for ticker in sorted(unique_tickers):
            price = fetcher.get_eod_price(ticker)
            
            if price:
                ticker_prices[ticker] = price
                success_count += 1
                print(f"  ✅ {ticker:6s}: {price:>10,.0f} VND")
            else:
                fail_count += 1
                print(f"  ❌ {ticker:6s}: Failed to fetch")
        
        print()
        print(f"Fetch results: ✅ {success_count} success, ❌ {fail_count} failed")
        print()
        
        # Update database
        print("💾 Updating database...")
        updated_count = 0
        
        for portfolio in portfolios:
            if portfolio.ticker in ticker_prices:
                new_price = ticker_prices[portfolio.ticker]
                
                # Calculate P/L
                old_price = portfolio.current_price or portfolio.avg_price
                price_change = ((new_price - old_price) / old_price) * 100 if old_price else 0
                
                # Update
                portfolio.current_price = new_price
                portfolio.price_updated_at = datetime.now()
                portfolio.updated_at = datetime.now()
                
                updated_count += 1
                
                # Log if significant change
                if abs(price_change) > 2:
                    change_emoji = "📈" if price_change > 0 else "📉"
                    print(f"  {change_emoji} {portfolio.ticker}: {old_price:,.0f} → {new_price:,.0f} ({price_change:+.1f}%)")
        
        session.commit()
        
        print()
        print(f"✅ Updated {updated_count} portfolio entries")
        
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        session.rollback()
        
    finally:
        session.close()
    
    print()
    print("=" * 70)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)


# ============================================================================
# CLI OPTIONS
# ============================================================================

def show_portfolio_summary():
    """Show current portfolio summary"""
    
    session = Session()
    
    try:
        portfolios = session.query(Portfolio).all()
        
        if not portfolios:
            print("No portfolios in database")
            return
        
        print("\n" + "=" * 70)
        print("📊 CURRENT PORTFOLIO SUMMARY")
        print("=" * 70)
        
        # Group by user
        from collections import defaultdict
        user_portfolios = defaultdict(list)
        
        for p in portfolios:
            user_portfolios[p.user_id].append(p)
        
        for user_id, positions in user_portfolios.items():
            print(f"\n👤 User: {user_id[:20]}...")
            print(f"   Positions: {len(positions)}")
            
            total_invested = 0
            total_current = 0
            
            for p in positions:
                invested = p.quantity * p.avg_price
                current = p.quantity * (p.current_price or p.avg_price)
                pnl = current - invested
                pnl_pct = (pnl / invested) * 100 if invested else 0
                
                total_invested += invested
                total_current += current
                
                pnl_emoji = "🟢" if pnl >= 0 else "🔴"
                print(f"   {pnl_emoji} {p.ticker:6s}: {p.quantity:>6} CP × {p.avg_price:>8,.0f} = {invested:>12,.0f} VND ({pnl_pct:+6.1f}%)")
            
            total_pnl = total_current - total_invested
            total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested else 0
            
            print(f"\n   💰 Total:")
            print(f"      Invested: {total_invested:>12,.0f} VND")
            print(f"      Current:  {total_current:>12,.0f} VND")
            print(f"      P/L:      {total_pnl:>12,.0f} VND ({total_pnl_pct:+.1f}%)")
        
        print("\n" + "=" * 70 + "\n")
        
    finally:
        session.close()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Portfolio Price Auto-Update')
    parser.add_argument('--summary', action='store_true', help='Show portfolio summary')
    parser.add_argument('--ticker', type=str, help='Test fetch for specific ticker')
    
    args = parser.parse_args()
    
    if args.summary:
        show_portfolio_summary()
    elif args.ticker:
        # Test single ticker
        fetcher = PriceFetcher()
        price = fetcher.get_eod_price(args.ticker.upper())
        if price:
            print(f"✅ {args.ticker.upper()}: {price:,.0f} VND")
        else:
            print(f"❌ {args.ticker.upper()}: Failed to fetch")
    else:
        # Run full update
        update_all_portfolio_prices()
