#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick DB Connection Test
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*60)
print("🔍 DATABASE CONNECTION TEST")
print("="*60)

# Show loaded variables
print("\n1. Environment variables loaded:")
print(f"   DB_HOST: {os.getenv('DB_HOST')}")
print(f"   DB_NAME: {os.getenv('DB_NAME')}")
print(f"   DB_USER: {os.getenv('DB_USER')}")
print(f"   DB_PORT: {os.getenv('DB_PORT')}")

if not os.getenv('DB_HOST'):
    print("\n❌ DB_HOST not found in .env!")
    print("   Make sure you added DB credentials to .env file")
    exit(1)

print("\n2. Testing connection...")
print(f"   Connecting to {os.getenv('DB_HOST')}...")

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432),
        connect_timeout=10
    )
    
    print("   ✅ Connection successful!")
    
    # Test query
    print("\n3. Testing query...")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM signals WHERE action='BUY' AND status='open'")
    count = cursor.fetchone()[0]
    
    print(f"   ✅ Query successful!")
    print(f"   Found {count} open BUY signals")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour database connection is working.")
    print("You can now run the scanner:")
    print("  python sell_signal_scanner_v5_2.py")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED!")
    print(f"   Error: {e}")
    print("\n" + "="*60)
    print("🔧 TROUBLESHOOTING:")
    print("="*60)
    print("\nIf you see timeout or connection refused:")
    print("1. Render may block external connections from local")
    print("2. Switch to Supabase for local development")
    print("\nTo use Supabase:")
    print("1. Edit .env file")
    print("2. Comment Render credentials (add # at start)")
    print("3. Add Supabase credentials instead")

print("\n")
