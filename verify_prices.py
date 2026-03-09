import os
from sqlalchemy import create_engine, text

url = os.environ['DATABASE_URL'].replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(url)

with engine.connect() as conn:
    count = conn.execute(text('SELECT COUNT(*) FROM eod_prices')).scalar()
    latest = conn.execute(text('SELECT trade_date FROM eod_prices ORDER BY updated_at DESC LIMIT 1')).scalar()
    szc = conn.execute(text("SELECT price FROM eod_prices WHERE ticker='SZC'")).scalar()
    stb = conn.execute(text("SELECT price FROM eod_prices WHERE ticker='STB'")).scalar()
    print(f'Tickers: {count} | Trade date: {latest} | SZC: {szc:,.0f} | STB: {stb:,.0f} VND')
