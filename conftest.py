"""
Pytest Configuration and Shared Fixtures
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'postgresql://aiadvisor:dev123456@localhost:5432/aiadvisor_test'


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Import here to ensure env vars are set first
    from backend_api import app as flask_app
    
    flask_app.config.update({
        'TESTING': True,
        'DEBUG': False,
        'WTF_CSRF_ENABLED': False,
    })
    
    yield flask_app


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session():
    """Create database session for testing"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture
def sample_signal():
    """Sample signal data for testing"""
    return {
        'ticker': 'VCB',
        'strategy': 'PULLBACK',
        'entry_price': 88500,
        'stop_loss': 83044,
        'take_profit': 95580,
        'risk_reward': 1.6,
        'strength': 75,
        'is_priority': 1,
        'stock_type': 'Blue Chip',
        'rsi': 45.2,
        'date': '2026-01-31',
        'action': 'BUY'
    }


@pytest.fixture
def sample_portfolio():
    """Sample portfolio data for testing"""
    return {
        'user_id': 1,
        'ticker': 'VCB',
        'quantity': 100,
        'price': 85000
    }


@pytest.fixture
def auth_headers():
    """Sample auth headers for testing"""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
    }
