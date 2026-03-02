"""
Add to backend_api.py as a temporary endpoint
"""

@app.route('/api/admin/copy-to-staging', methods=['POST'])
def copy_to_staging():
    """Copy production data to staging database"""
    import psycopg
    
    # Staging DB
    staging_db = "postgresql://postgres.xyzxaxajshlowpkiouon:3NfbmvjGThaS2l2L@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=prefer"
    
    try:
        # Get all signals from current (production) database
        session = Session()
        signals = session.query(Signal).all()
        blacklist = session.query(TickerBlacklist).all()
        
        # Connect to staging
        with psycopg.connect(staging_db) as staging_conn:
            with staging_conn.cursor() as cur:
                # Clear staging
                cur.execute("TRUNCATE TABLE signals RESTART IDENTITY CASCADE")
                cur.execute("TRUNCATE TABLE ticker_blacklist RESTART IDENTITY CASCADE")
                
                # Copy signals
                for signal in signals:
                    cur.execute("""
                        INSERT INTO signals (
                            ticker, strategy, entry_price, stop_loss, take_profit,
                            risk_reward, strength, stock_type, rsi, date, action, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        signal.ticker, signal.strategy, signal.entry_price,
                        signal.stop_loss, signal.take_profit, signal.risk_reward,
                        signal.strength, signal.stock_type, signal.rsi,
                        signal.date, signal.action, signal.created_at
                    ))
                
                # Copy blacklist
                for item in blacklist:
                    cur.execute("""
                        INSERT INTO ticker_blacklist (ticker, reason, created_at)
                        VALUES (%s, %s, %s)
                    """, (item.ticker, item.reason, item.created_at))
                
                staging_conn.commit()
        
        return jsonify({
            'success': True,
            'signals_copied': len(signals),
            'blacklist_copied': len(blacklist)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()