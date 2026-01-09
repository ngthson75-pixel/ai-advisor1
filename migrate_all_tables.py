"""
Complete Database Migration - Fix all tables
"""

import sqlite3
from datetime import datetime

DB_PATH = 'signals.db'

def migrate_all_tables():
    """Create all necessary tables"""
    
    print("Starting complete migration...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create signals table (if not exists)
    print("Creating signals table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            strategy TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            take_profit REAL NOT NULL,
            risk_reward REAL,
            strength REAL,
            is_priority INTEGER DEFAULT 0,
            stock_type TEXT,
            rsi REAL,
            date TEXT,
            action TEXT DEFAULT 'BUY',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Create portfolios table
    print("Creating portfolios table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            avg_price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, ticker)
        )
    ''')
    
    # 3. Create chat_history table
    print("Creating chat_history table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            portfolio_context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Create indexes
    print("Creating indexes...")
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_signals_date 
        ON signals(date DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_portfolio_user 
        ON portfolios(user_id)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chat_user 
        ON chat_history(user_id, created_at DESC)
    ''')
    
    conn.commit()
    conn.close()
    
    print("✓ Migration completed successfully!")
    print("\nTables created:")
    print("  - signals")
    print("  - portfolios")
    print("  - chat_history")
    print("\nIndexes created for better performance")

if __name__ == "__main__":
    migrate_all_tables()
