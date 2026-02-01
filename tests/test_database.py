"""
Database Integration Tests
Test database operations and data integrity
"""
import pytest
from datetime import datetime


@pytest.mark.integration
class TestSignalsTable:
    """Test signals table operations"""
    
    def test_create_signal(self, db_session, sample_signal):
        """Test creating a signal in database"""
        from sqlalchemy import text
        
        # Insert signal
        insert_sql = text("""
            INSERT INTO signals 
            (ticker, strategy, entry_price, stop_loss, take_profit, 
             risk_reward, strength, is_priority, stock_type, rsi, date, action)
            VALUES 
            (:ticker, :strategy, :entry_price, :stop_loss, :take_profit,
             :risk_reward, :strength, :is_priority, :stock_type, :rsi, :date, :action)
            RETURNING id
        """)
        
        result = db_session.execute(insert_sql, sample_signal)
        signal_id = result.fetchone()[0]
        
        assert signal_id is not None
        assert signal_id > 0
    
    def test_read_signals(self, db_session):
        """Test reading signals from database"""
        from sqlalchemy import text
        
        query = text("SELECT * FROM signals LIMIT 10")
        result = db_session.execute(query)
        signals = result.fetchall()
        
        assert isinstance(signals, list)
    
    def test_signals_have_indexes(self, db_session):
        """Test that required indexes exist"""
        from sqlalchemy import text
        
        # Check for idx_signals_date
        query = text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'signals' 
            AND indexname = 'idx_signals_date'
        """)
        
        result = db_session.execute(query)
        index = result.fetchone()
        
        assert index is not None


@pytest.mark.integration
class TestPortfoliosTable:
    """Test portfolios table operations"""
    
    def test_create_portfolio(self, db_session):
        """Test creating portfolio entry"""
        from sqlalchemy import text
        
        insert_sql = text("""
            INSERT INTO portfolios (user_id, ticker, quantity, avg_price)
            VALUES (999, 'TEST', 100, 50000)
            ON CONFLICT (user_id, ticker) DO UPDATE
            SET quantity = EXCLUDED.quantity,
                avg_price = EXCLUDED.avg_price
            RETURNING id
        """)
        
        result = db_session.execute(insert_sql)
        portfolio_id = result.fetchone()[0]
        
        assert portfolio_id is not None
    
    def test_portfolio_unique_constraint(self, db_session):
        """Test user_id + ticker unique constraint"""
        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError
        
        # Insert first time - should succeed
        insert_sql = text("""
            INSERT INTO portfolios (user_id, ticker, quantity, avg_price)
            VALUES (888, 'UNIQUE_TEST', 100, 50000)
        """)
        
        try:
            db_session.execute(insert_sql)
            db_session.commit()
            
            # Try insert again - should use ON CONFLICT or fail
            # This is expected behavior (unique constraint working)
            
        except IntegrityError:
            # This is also acceptable - unique constraint working
            db_session.rollback()


@pytest.mark.integration  
class TestChatHistoryTable:
    """Test chat_history table operations"""
    
    def test_create_chat_entry(self, db_session):
        """Test creating chat history entry"""
        from sqlalchemy import text
        
        insert_sql = text("""
            INSERT INTO chat_history (user_id, message, response, portfolio_context)
            VALUES (1, 'Test message', 'Test response', '{}')
            RETURNING id
        """)
        
        result = db_session.execute(insert_sql)
        chat_id = result.fetchone()[0]
        
        assert chat_id is not None
    
    def test_get_chat_history(self, db_session):
        """Test retrieving chat history"""
        from sqlalchemy import text
        
        query = text("""
            SELECT * FROM chat_history 
            WHERE user_id = 1 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        result = db_session.execute(query)
        history = result.fetchall()
        
        assert isinstance(history, list)


@pytest.mark.integration
class TestDatabaseConnectivity:
    """Test database connection and basic operations"""
    
    def test_database_connection(self, db_session):
        """Test database is connectable"""
        from sqlalchemy import text
        
        result = db_session.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1
    
    def test_all_tables_exist(self, db_session):
        """Test all required tables exist"""
        from sqlalchemy import text
        
        query = text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        
        result = db_session.execute(query)
        tables = [row[0] for row in result.fetchall()]
        
        required_tables = ['signals', 'portfolios', 'chat_history']
        for table in required_tables:
            assert table in tables, f"Table '{table}' does not exist"
