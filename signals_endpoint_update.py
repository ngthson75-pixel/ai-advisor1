# ========================================================================
# SIGNALS ENDPOINTS - COMPLETE REPLACEMENT (Lines 386-425)
# ========================================================================
# This code replaces lines 386-425 in backend_api.py
# FIND:    Line 386: # SIGNALS ENDPOINTS
# REPLACE: Everything from line 386 to line 425 (before # AUTOMATION ENDPOINTS)

# ========================================================================
# SIGNALS ENDPOINTS
# ========================================================================

@app.route('/api/signals', methods=['GET', 'POST'])
def signals_endpoint():
    """
    GET: Retrieve all signals
    POST: Create new signal (for push script)
    """
    
    if request.method == 'GET':
        # GET: Return all signals (original functionality)
        session = Session()
        try:
            signals = session.query(Signal).order_by(Signal.created_at.desc()).all()
            
            signals_data = []
            for s in signals:
                signals_data.append({
                    'id': s.id,
                    'ticker': s.ticker,
                    'code': s.ticker,
                    'strategy': s.strategy,
                    'entry_price': s.entry_price,
                    'stop_loss': s.stop_loss,
                    'take_profit': s.take_profit,
                    'risk_reward': s.risk_reward,
                    'strength': s.strength or 0,
                    'stock_type': s.stock_type,
                    'rsi': s.rsi,
                    'date': s.date or (s.created_at.strftime('%Y-%m-%d') if s.created_at else None),
                    'action': s.action,
                    'created_at': s.created_at.isoformat() if s.created_at else None
                })
            
            return jsonify({
                'success': True,
                'signals': signals_data,
                'count': len(signals_data)
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()
    
    elif request.method == 'POST':
        # POST: Create new signal (NEW - for push script)
        data = request.json
        
        # Validate request has data
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['ticker', 'entry_price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False, 
                    'error': f'Missing required field: {field}'
                }), 400
        
        session = Session()
        try:
            # Create new signal from push script data
            signal = Signal(
                ticker=data['ticker'],
                strategy=data.get('strategy'),
                entry_price=data['entry_price'],
                stop_loss=data.get('stop_loss'),
                take_profit=data.get('take_profit'),
                risk_reward=data.get('risk_reward'),
                strength=data.get('strength'),
                stock_type=data.get('stock_type'),
                rsi=data.get('rsi'),
                date=data.get('date'),
                action=data.get('action', 'BUY')
            )
            
            # Save to database
            session.add(signal)
            session.commit()
            
            print(f"✅ Signal created: {signal.ticker} ({signal.strategy}) - {signal.date}")
            
            return jsonify({
                'success': True,
                'id': signal.id,
                'ticker': signal.ticker,
                'message': 'Signal created successfully'
            }), 201
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating signal: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()


# ========================================================================
# AUTOMATION ENDPOINTS (GitHub Actions)
# ========================================================================
# (Continue with existing code from line 428...)
