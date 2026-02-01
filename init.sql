-- ========================================================================
-- AI ADVISOR - DATABASE INITIALIZATION SCRIPT
-- ========================================================================
-- This script runs automatically when PostgreSQL container first starts

-- Create tables
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL,
    stop_loss DECIMAL(10,2) NOT NULL,
    take_profit DECIMAL(10,2) NOT NULL,
    risk_reward DECIMAL(5,2),
    strength DECIMAL(5,2),
    is_priority INTEGER DEFAULT 0,
    stock_type VARCHAR(20),
    rsi DECIMAL(5,2),
    date VARCHAR(20),
    action VARCHAR(10) DEFAULT 'BUY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    avg_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, ticker)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    portfolio_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_signals_date ON signals(date DESC);
CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id, created_at DESC);

-- Insert sample data for testing
INSERT INTO signals (ticker, strategy, entry_price, stop_loss, take_profit, risk_reward, strength, is_priority, stock_type, rsi, date, action)
VALUES 
    ('VCB', 'PULLBACK', 88500, 83044, 95580, 1.6, 75, 1, 'Blue Chip', 45.2, '2026-01-31', 'BUY'),
    ('VHM', 'EMA_CROSS', 45000, 43200, 49500, 1.8, 85, 1, 'Blue Chip', 55.0, '2026-01-31', 'BUY'),
    ('HPG', 'PULLBACK', 28500, 27075, 30780, 1.5, 70, 0, 'Blue Chip', 48.5, '2026-01-31', 'BUY')
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aiadvisor;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aiadvisor;
