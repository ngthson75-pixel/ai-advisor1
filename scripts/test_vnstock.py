#!/usr/bin/env python3
"""
Test VNStock connection
"""

from vnstock import Vnstock
from datetime import datetime

print("Testing VNStock...")

# Create stock object
stock = Vnstock().stock(symbol='VNM', source='VCI')

# Fetch historical data
print("\nFetching VNM data (Jun-Dec 2024)...")
df = stock.quote.history(
    symbol='VNM',
    start='2024-06-01',
    end='2024-12-31'
)

# Display results
print(f"\nTotal rows: {len(df)}")
print(f"\nFirst 5 rows:")
print(df.head())

print(f"\nLast 5 rows:")
print(df.tail())

print(f"\nColumns: {df.columns.tolist()}")

print("\n✅ VNStock working!")