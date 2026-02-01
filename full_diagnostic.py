#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE SYSTEM DIAGNOSTIC
Kiểm tra TẤT CẢ vấn đề trong AI Advisor

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com
"""

import sqlite3
from datetime import datetime
from collections import Counter

def diagnostic_report():
    """Run full system diagnostic"""
    
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🔍 AI ADVISOR - COMPREHENSIVE DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # ========================================================================
    # ISSUE 1: DUPLICATE SIGNALS
    # ========================================================================
    
    print("=" * 80)
    print("🚨 ISSUE #1: DUPLICATE SIGNALS CHECK")
    print("=" * 80)
    
    # Get all signals
    cursor.execute("SELECT ticker, date, COUNT(*) as count FROM signals GROUP BY ticker, date HAVING count > 1")
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"❌ FOUND {len(duplicates)} DUPLICATE GROUPS:\n")
        
        for ticker, date, count in duplicates:
            print(f"   📊 {ticker} on {date}: {count} signals")
            
            # Show details
            cursor.execute("""
                SELECT id, ticker, strategy, entry_price, strength, created_at 
                FROM signals 
                WHERE ticker = ? AND date = ?
                ORDER BY id
            """, (ticker, date))
            
            signals = cursor.fetchall()
            for sig in signals:
                print(f"      → ID={sig[0]}, Strategy={sig[2]}, Entry={sig[3]:,.0f}, Strength={sig[4]:.0f}, Created={sig[5]}")
            print()
        
        # Recommend action
        print("💡 RECOMMENDED ACTION:")
        print("   Keep signal with highest ID (newest)")
        print("   Delete older duplicates")
        print()
        
    else:
        print("✅ No duplicate signals found\n")
    
    # Check for same ticker different dates
    cursor.execute("""
        SELECT ticker, COUNT(DISTINCT date) as dates, COUNT(*) as total
        FROM signals 
        GROUP BY ticker
        HAVING dates > 1
    """)
    
    multi_date_tickers = cursor.fetchall()
    
    if multi_date_tickers:
        print(f"📅 TICKERS WITH MULTIPLE DATES: {len(multi_date_tickers)}")
        for ticker, dates, total in multi_date_tickers[:5]:
            print(f"   {ticker}: {dates} dates, {total} total signals")
            
            cursor.execute("""
                SELECT date, COUNT(*) 
                FROM signals 
                WHERE ticker = ?
                GROUP BY date
                ORDER BY date DESC
            """, (ticker,))
            
            for date, count in cursor.fetchall():
                print(f"      → {date}: {count} signals")
        
        if len(multi_date_tickers) > 5:
            print(f"   ... and {len(multi_date_tickers) - 5} more")
        print()
    
    # ========================================================================
    # ISSUE 2: USER DATA ISOLATION
    # ========================================================================
    
    print("=" * 80)
    print("🔒 ISSUE #2: USER DATA ISOLATION CHECK")
    print("=" * 80)
    
    # Check portfolios
    cursor.execute("SELECT COUNT(*) FROM portfolios")
    total_portfolios = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM portfolios")
    unique_users = cursor.fetchone()[0] if total_portfolios > 0 else 0
    
    print(f"📊 PORTFOLIOS:")
    print(f"   Total entries: {total_portfolios}")
    print(f"   Unique user_ids: {unique_users}")
    
    if total_portfolios > 0:
        cursor.execute("SELECT user_id, COUNT(*) FROM portfolios GROUP BY user_id")
        user_counts = cursor.fetchall()
        
        for user_id, count in user_counts:
            print(f"   user_id={user_id}: {count} stocks")
            
            if user_id == 1:
                print(f"      ⚠️  WARNING: user_id=1 likely hardcoded in frontend!")
    
    if unique_users <= 1 and total_portfolios > 0:
        print("\n❌ ISSUE CONFIRMED: All users share same user_id!")
        print("💡 FIX REQUIRED: Implement unique user sessions in frontend")
    else:
        print("\n✅ User isolation working correctly")
    
    print()
    
    # Check chat history
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    total_chats = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM chat_history")
    unique_chat_users = cursor.fetchone()[0] if total_chats > 0 else 0
    
    print(f"💬 CHAT HISTORY:")
    print(f"   Total messages: {total_chats}")
    print(f"   Unique user_ids: {unique_chat_users}")
    
    if total_chats > 0 and unique_chat_users <= 1:
        print(f"   ⚠️  All chats from same user_id - isolation issue!")
    
    print()
    
    # ========================================================================
    # ISSUE 3: SIGNAL ORDERING
    # ========================================================================
    
    print("=" * 80)
    print("📅 ISSUE #3: SIGNAL ORDERING CHECK")
    print("=" * 80)
    
    # Check current order in database
    cursor.execute("""
        SELECT id, ticker, date, created_at 
        FROM signals 
        ORDER BY id DESC
        LIMIT 10
    """)
    
    signals_by_id = cursor.fetchall()
    
    print("Current signals (by ID DESC - database insertion order):")
    for i, (sig_id, ticker, date, created) in enumerate(signals_by_id, 1):
        print(f"   {i}. ID={sig_id:3d}, {ticker:5s}, Date={date}, Created={created}")
    
    print()
    
    # Check if dates are properly ordered
    cursor.execute("""
        SELECT id, ticker, date, created_at 
        FROM signals 
        ORDER BY date DESC, id DESC
        LIMIT 10
    """)
    
    signals_by_date = cursor.fetchall()
    
    print("Signals ordered by DATE DESC (newest first):")
    for i, (sig_id, ticker, date, created) in enumerate(signals_by_date, 1):
        print(f"   {i}. ID={sig_id:3d}, {ticker:5s}, Date={date}, Created={created}")
    
    # Check if backend is ordering correctly
    print("\n💡 RECOMMENDATIONS:")
    print("   1. Backend API should ORDER BY date DESC, id DESC")
    print("   2. Frontend should NOT re-sort (trust backend order)")
    print("   3. Or frontend should sort by date DESC if needed")
    print()
    
    # ========================================================================
    # ADDITIONAL CHECKS
    # ========================================================================
    
    print("=" * 80)
    print("📊 ADDITIONAL STATISTICS")
    print("=" * 80)
    
    # Signal stats
    cursor.execute("SELECT COUNT(*) FROM signals")
    total_signals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT ticker) FROM signals")
    unique_tickers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT date) FROM signals")
    unique_dates = cursor.fetchone()[0]
    
    print(f"Total signals: {total_signals}")
    print(f"Unique tickers: {unique_tickers}")
    print(f"Unique dates: {unique_dates}")
    print(f"Avg signals per ticker: {total_signals / unique_tickers if unique_tickers > 0 else 0:.1f}")
    
    # Most frequent tickers
    cursor.execute("""
        SELECT ticker, COUNT(*) as count 
        FROM signals 
        GROUP BY ticker 
        ORDER BY count DESC 
        LIMIT 5
    """)
    
    print("\nMost frequent tickers:")
    for ticker, count in cursor.fetchall():
        print(f"   {ticker}: {count} signals")
    
    # Date distribution
    cursor.execute("""
        SELECT date, COUNT(*) as count 
        FROM signals 
        GROUP BY date 
        ORDER BY date DESC
    """)
    
    print("\nSignals by date:")
    for date, count in cursor.fetchall():
        print(f"   {date}: {count} signals")
    
    print()
    
    # ========================================================================
    # SUMMARY & ACTION PLAN
    # ========================================================================
    
    print("=" * 80)
    print("🎯 SUMMARY & ACTION PLAN")
    print("=" * 80)
    
    issues_found = []
    
    if duplicates:
        issues_found.append("Duplicate signals")
    
    if total_portfolios > 0 and unique_users <= 1:
        issues_found.append("User isolation broken")
    
    # Check if ordering might be wrong
    if signals_by_id != signals_by_date:
        issues_found.append("Signal ordering inconsistent")
    
    if issues_found:
        print(f"❌ ISSUES FOUND: {len(issues_found)}")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
        
        print("\n📋 PRIORITY ACTIONS:")
        
        if "Duplicate signals" in issues_found:
            print("\n1️⃣  FIX DUPLICATE SIGNALS:")
            print("   Run: python fix_duplicate_signals.py")
        
        if "User isolation broken" in issues_found:
            print("\n2️⃣  FIX USER ISOLATION:")
            print("   - Add frontend/src/utils/userSession.js")
            print("   - Update frontend/src/components/AIPortfolioManager.jsx")
            print("   - Deploy to production")
        
        if "Signal ordering inconsistent" in issues_found:
            print("\n3️⃣  FIX SIGNAL ORDERING:")
            print("   - Update backend API: ORDER BY date DESC, id DESC")
            print("   - Update frontend: Sort by date DESC")
        
    else:
        print("✅ No critical issues found!")
    
    print("\n" + "=" * 80)
    print("📞 Support: ngthson75@gmail.com")
    print("=" * 80)
    
    conn.close()


if __name__ == '__main__':
    try:
        diagnostic_report()
    except Exception as e:
        print(f"❌ Error running diagnostic: {e}")
        import traceback
        traceback.print_exc()
