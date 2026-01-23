#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMPORT SIGNAL ENDPOINT
Add this to backend_api.py
"""

@app.route('/api/signals/import', methods=['POST'])
def import_signal():
    """
    Import a single signal from external source (e.g., local scanner)
    """
    session = Session()
    
    try:
        data = request.json
        
        # Validate required fields
        required = ['ticker', 'strategy', 'entry_price', 'stop_loss', 'take_profit', 'date']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        # Check if signal already exists
        existing = session.query(Signal).filter_by(
            ticker=data['ticker'],
            date=data['date'],
            action=data.get('action', 'BUY')
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Signal already exists',
                'existing_id': existing.id
            }), 409
        
        # Create new signal
        signal = Signal(
            ticker=data['ticker'],
            strategy=data['strategy'],
            entry_price=data['entry_price'],
            stop_loss=data['stop_loss'],
            take_profit=data['take_profit'],
            risk_reward=data.get('risk_reward', 0),
            strength=data.get('strength', 0),
            is_priority=data.get('is_priority', 0),
            stock_type=data.get('stock_type', 'Penny'),
            rsi=data.get('rsi', 50),
            date=data['date'],
            action=data.get('action', 'BUY'),
            signal_status=data.get('signal_status', 'ACTIVE'),
            quantity_sold=data.get('quantity_sold', 0)
        )
        
        session.add(signal)
        session.commit()
        
        return jsonify({
            'success': True,
            'signal_id': signal.id,
            'ticker': signal.ticker,
            'message': 'Signal imported successfully'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@app.route('/api/signals/import-batch', methods=['POST'])
def import_signals_batch():
    """
    Import multiple signals at once
    """
    session = Session()
    
    try:
        data = request.json
        signals_data = data.get('signals', [])
        
        if not signals_data:
            return jsonify({'success': False, 'error': 'No signals provided'}), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        for sig_data in signals_data:
            try:
                # Check if exists
                existing = session.query(Signal).filter_by(
                    ticker=sig_data['ticker'],
                    date=sig_data['date'],
                    action=sig_data.get('action', 'BUY')
                ).first()
                
                if existing:
                    error_count += 1
                    errors.append(f"{sig_data['ticker']}: Already exists")
                    continue
                
                # Create signal
                signal = Signal(
                    ticker=sig_data['ticker'],
                    strategy=sig_data['strategy'],
                    entry_price=sig_data['entry_price'],
                    stop_loss=sig_data['stop_loss'],
                    take_profit=sig_data['take_profit'],
                    risk_reward=sig_data.get('risk_reward', 0),
                    strength=sig_data.get('strength', 0),
                    is_priority=sig_data.get('is_priority', 0),
                    stock_type=sig_data.get('stock_type', 'Penny'),
                    rsi=sig_data.get('rsi', 50),
                    date=sig_data['date'],
                    action=sig_data.get('action', 'BUY'),
                    signal_status=sig_data.get('signal_status', 'ACTIVE'),
                    quantity_sold=sig_data.get('quantity_sold', 0)
                )
                
                session.add(signal)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"{sig_data.get('ticker', 'Unknown')}: {str(e)}")
        
        session.commit()
        
        return jsonify({
            'success': True,
            'imported': success_count,
            'errors': error_count,
            'error_details': errors[:10],  # Max 10 error messages
            'message': f'Imported {success_count} signals, {error_count} errors'
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
