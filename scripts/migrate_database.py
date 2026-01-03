"""
Database Migration - Add Portfolio & Chat History
"""

import sqlite3
from datetime import datetime

DB_PATH = 'signals.db'

def migrate_database():
    """Add new tables for portfolio and chat history"""
    
    print("Starting database migration...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create portfolios table
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
    
    # 2. Create chat_history table
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
    
    # 3. Create index for faster queries
    print("Creating indexes...")
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
    print("\nNew tables:")
    print("  - portfolios: Store user portfolios")
    print("  - chat_history: Store chat conversations")
    print("\nIndexes created for better performance")

if __name__ == "__main__":
    migrate_database()
