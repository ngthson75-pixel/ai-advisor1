#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Production Signals JSON to SQL INSERT Statements
"""

import json
from datetime import datetime

def escape_sql_string(s):
    """Escape single quotes in SQL strings"""
    if s is None:
        return 'NULL'
    return str(s).replace("'", "''")

def convert_json_to_sql():
    """Convert production_signals.json to SQL"""
    
    print("📄 Reading production_signals.json...")
    
    # Read JSON file
    try:
        with open('production_signals.json', 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ ERROR: production_signals.json not found!")
        print("   Run this first:")
        print("   Invoke-WebRequest -Uri 'https://ai-advisor1-backend.onrender.com/api/signals' -UseBasicParsing | Out-File production_signals.json -Encoding utf8")
        return
    
    # Extract signals
    signals = data.get('signals', [])
    count = len(signals)
    
    print(f"✅ Found {count} signals")
    
    if count == 0:
        print("❌ No signals found in JSON!")
        return
    
    # Generate SQL
    print("🔄 Generating SQL INSERT statements...")
    
    sql_lines = []
    
    # Add header
    sql_lines.append("-- =====================================================")
    sql_lines.append("-- Copy Production Signals to Staging")
    sql_lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_lines.append(f"-- Total signals: {count}")
    sql_lines.append("-- =====================================================")
    sql_lines.append("")
    
    # Clear existing data
    sql_lines.append("-- Clear existing signals")
    sql_lines.append("TRUNCATE TABLE signals RESTART IDENTITY CASCADE;")
    sql_lines.append("")
    
    # Insert signals
    sql_lines.append("-- Insert signals")
    
    for i, signal in enumerate(signals, 1):
        # Extract fields with defaults
        ticker = escape_sql_string(signal.get('ticker', ''))
        strategy = escape_sql_string(signal.get('strategy', ''))
        entry_price = signal.get('entry_price', 0)
        stop_loss = signal.get('stop_loss')
        take_profit = signal.get('take_profit')
        risk_reward = signal.get('risk_reward')
        strength = signal.get('strength')
        stock_type = escape_sql_string(signal.get('stock_type', ''))
        rsi = signal.get('rsi')
        date = escape_sql_string(signal.get('date', ''))
        action = escape_sql_string(signal.get('action', 'BUY'))
        
        # Format NULL values
        stop_loss_str = stop_loss if stop_loss is not None else 'NULL'
        take_profit_str = take_profit if take_profit is not None else 'NULL'
        risk_reward_str = risk_reward if risk_reward is not None else 'NULL'
        strength_str = strength if strength is not None else 'NULL'
        rsi_str = rsi if rsi is not None else 'NULL'
        
        # Build INSERT statement
        sql = f"""INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, stock_type, rsi, date, action, created_at)
VALUES ('{ticker}', '{strategy}', {entry_price}, {stop_loss_str}, {take_profit_str}, {risk_reward_str}, {strength_str}, '{stock_type}', {rsi_str}, '{date}', '{action}', NOW());"""
        
        sql_lines.append(sql)
        
        # Progress indicator
        if i % 10 == 0:
            print(f"  Processed {i}/{count} signals...")
    
    # Write to file
    output_file = 'insert_signals.sql'
    print(f"\n📝 Writing SQL to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"✅ Generated {output_file}")
    print(f"   Total lines: {len(sql_lines)}")
    print(f"   Total signals: {count}")
    
    # Show sample
    print("\n📄 First 5 lines of SQL:")
    print("="*70)
    for line in sql_lines[:10]:
        print(line)
    print("...")
    print("="*70)
    
    print("\n🎉 DONE! Now:")
    print("1. Open Supabase SQL Editor: https://supabase.com/dashboard")
    print("2. Open your project → SQL Editor")
    print("3. Copy content from insert_signals.sql")
    print("4. Paste and Run")

if __name__ == '__main__':
    print("="*70)
    print("🔄 CONVERT PRODUCTION JSON TO SQL")
    print("="*70)
    print()
    
    convert_json_to_sql()
