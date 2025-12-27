#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADMIN SIGNAL APPROVAL API + TELEGRAM NOTIFICATION

Owner: Nguyễn Thanh Sơn
Email: ngthson75@gmail.com  
Phone: +84938127666
Dashboard: https://ai-advisor1.netlify.app/admin/signals
"""

from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, timedelta
import os
from vnstock import Vnstock
from telegram_notifier import TelegramNotifier

# Admin info
ADMIN_EMAIL = "ngthson75@gmail.com"
ADMIN_PHONE = "+84938127666"
ADMIN_NAME = "Nguyễn Thanh Sơn"

# Create blueprint
admin_bp = Blueprint('admin', __name__)

# Initialize Telegram
telegram = TelegramNotifier()


# ========================================================================
# DATABASE MODELS (Example using SQLAlchemy)
# ========================================================================

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Signal(Base):
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    
    # Stock info
    code = Column(String(10), nullable=False)
    strategy_type = Column(String(50), nullable=False)
    
    # Prices
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Metrics
    price_diff_pct = Column(Float, default=0)
    risk_pct = Column(Float, default=0)
    reward_pct = Column(Float, default=0)
    rr_ratio = Column(Float, default=0)
    rsi = Column(Float, default=0)
    volume_ratio = Column(Float, default=0)
    
    # Validation
    validation_errors = Column(Text, default='[]')
    validation_warnings = Column(Text, default='[]')
    quality_score = Column(Integer, default=0)
    
    # State
    state = Column(String(20), default='pending_review')
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.now)
    reviewed_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Admin
    reviewed_by = Column(String(100), nullable=True)
    admin_notes = Column(Text, nullable=True)
    reject_reason = Column(Text, nullable=True)


# Initialize database
engine = create_engine('sqlite:///signals.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


# ========================================================================
# SIGNAL VALIDATOR
# ========================================================================

class SignalValidator:
    """Validate signals in real-time"""
    
    def __init__(self):
        self.stock_api = Vnstock()
    
    def validate_signal(self, signal_data):
        """Comprehensive validation"""
        
        errors = []
        warnings = []
        
        # Get real-time price
        current_price = self.get_realtime_price(signal_data['code'])
        
        if not current_price:
            errors.append("Cannot fetch current price")
            return {
                'valid': False,
                'errors': errors,
                'warnings': warnings,
                'quality_score': 0,
                'current_price': signal_data['entry_price']
            }
        
        signal_data['current_price'] = current_price
        
        # Calculate price difference
        entry_price = signal_data['entry_price']
        price_diff_pct = ((entry_price - current_price) / current_price) * 100
        signal_data['price_diff_pct'] = price_diff_pct
        
        # 1. Price mismatch check
        if abs(price_diff_pct) > 5:
            errors.append(
                f"CRITICAL: Price mismatch! Entry {entry_price:,.0f} vs Current {current_price:,.0f} "
                f"({price_diff_pct:+.1f}% difference)"
            )
        elif abs(price_diff_pct) > 2:
            warnings.append(f"Price difference: {price_diff_pct:+.1f}%")
        
        # 2. Stop Loss check
        if signal_data['stop_loss'] >= signal_data['entry_price']:
            errors.append("Stop Loss ABOVE entry price!")
        
        # 3. Take Profit check
        if signal_data['take_profit'] <= signal_data['entry_price']:
            errors.append("Take Profit BELOW entry price!")
        
        # 4. Risk/Reward calculation
        risk_pct = abs((signal_data['entry_price'] - signal_data['stop_loss']) / signal_data['entry_price'] * 100)
        reward_pct = abs((signal_data['take_profit'] - signal_data['entry_price']) / signal_data['entry_price'] * 100)
        
        signal_data['risk_pct'] = risk_pct
        signal_data['reward_pct'] = reward_pct
        
        if risk_pct > 0:
            rr_ratio = reward_pct / risk_pct
            signal_data['rr_ratio'] = rr_ratio
            
            if rr_ratio < 1.5:
                warnings.append(f"Poor R/R ratio: {rr_ratio:.2f}x")
        else:
            signal_data['rr_ratio'] = 0
            errors.append("Invalid risk calculation")
        
        # 5. Risk check
        if risk_pct > 10:
            warnings.append(f"High risk: {risk_pct:.1f}%")
        
        # 6. Volume check
        if signal_data.get('volume_ratio', 0) < 1.2:
            warnings.append(f"Low volume: {signal_data.get('volume_ratio', 0):.2f}x")
        
        # 7. RSI check
        rsi = signal_data.get('rsi', 50)
        if rsi > 75:
            warnings.append(f"RSI very high: {rsi}")
        elif rsi < 25:
            warnings.append(f"RSI very low: {rsi}")
        
        # Calculate quality score
        quality_score = self.calculate_quality_score(signal_data, errors, warnings)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'quality_score': quality_score,
            'current_price': current_price
        }
    
    def get_realtime_price(self, code):
        """Get real-time price from VNStock"""
        try:
            stock = self.stock_api.stock(symbol=code, source='VCI')
            
            # Try intraday first
            try:
                intraday = stock.quote.intraday(symbol=code, page_size=1)
                if not intraday.empty:
                    return float(intraday['close'].iloc[-1])
            except:
                pass
            
            # Fallback to daily
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            
            daily = stock.quote.history(symbol=code, start=yesterday, end=today)
            if not daily.empty:
                return float(daily['close'].iloc[-1])
            
            return None
            
        except Exception as e:
            print(f"Error getting price for {code}: {e}")
            return None
    
    def calculate_quality_score(self, signal_data, errors, warnings):
        """Calculate quality score 0-100"""
        score = 100
        score -= len(errors) * 20
        score -= len(warnings) * 5
        
        # Bonuses
        if signal_data.get('rr_ratio', 0) >= 2:
            score += 10
        if signal_data.get('volume_ratio', 0) >= 2:
            score += 5
        
        rsi = signal_data.get('rsi', 50)
        if 40 <= rsi <= 60:
            score += 5
        
        return max(0, min(100, score))


# ========================================================================
# API ROUTES
# ========================================================================

validator = SignalValidator()


@admin_bp.route('/api/admin/signals', methods=['GET'])
def get_signals():
    """Get all signals with optional filter"""
    
    filter_type = request.args.get('filter', 'pending')
    session = Session()
    
    try:
        query = session.query(Signal)
        
        if filter_type == 'pending':
            query = query.filter(Signal.state == 'pending_review')
        elif filter_type == 'approved':
            query = query.filter(Signal.state == 'approved')
        elif filter_type == 'rejected':
            query = query.filter(Signal.state == 'rejected')
        
        query = query.order_by(Signal.detected_at.desc())
        signals = query.all()
        
        # Calculate stats
        stats = {
            'pending': session.query(Signal).filter(Signal.state == 'pending_review').count(),
            'approved': session.query(Signal).filter(Signal.state == 'approved').count(),
            'rejected': session.query(Signal).filter(Signal.state == 'rejected').count(),
            'total': session.query(Signal).count()
        }
        
        # Convert to dict
        signals_data = []
        for sig in signals:
            signals_data.append({
                'id': sig.id,
                'code': sig.code,
                'strategy_type': sig.strategy_type,
                'entry_price': sig.entry_price,
                'stop_loss': sig.stop_loss,
                'take_profit': sig.take_profit,
                'current_price': sig.current_price,
                'price_diff_pct': sig.price_diff_pct,
                'risk_pct': sig.risk_pct,
                'reward_pct': sig.reward_pct,
                'rr_ratio': sig.rr_ratio,
                'rsi': sig.rsi,
                'volume_ratio': sig.volume_ratio,
                'validation': {
                    'errors': eval(sig.validation_errors) if sig.validation_errors else [],
                    'warnings': eval(sig.validation_warnings) if sig.validation_warnings else [],
                    'quality_score': sig.quality_score
                },
                'state': sig.state,
                'detected_at': sig.detected_at.isoformat(),
                'reviewed_at': sig.reviewed_at.isoformat() if sig.reviewed_at else None,
                'admin_notes': sig.admin_notes,
                'reject_reason': sig.reject_reason
            })
        
        return jsonify({
            'success': True,
            'signals': signals_data,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


@admin_bp.route('/api/admin/signals/<int:signal_id>/approve', methods=['POST'])
def approve_signal(signal_id):
    """Approve signal and publish to users"""
    
    session = Session()
    
    try:
        signal = session.query(Signal).get(signal_id)
        
        if not signal:
            return jsonify({'error': 'Signal not found'}), 404
        
        # Update signal
        signal.state = 'approved'
        signal.reviewed_at = datetime.now()
        signal.published_at = datetime.now()
        signal.reviewed_by = ADMIN_NAME
        
        session.commit()
        
        # Send Telegram notification
        telegram.send_approval_notification({
            'code': signal.code,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'user_count': 'N/A'
        })
        
        return jsonify({'success': True, 'message': 'Signal approved'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@admin_bp.route('/api/admin/signals/<int:signal_id>/reject', methods=['POST'])
def reject_signal(signal_id):
    """Reject signal with reason"""
    
    data = request.json
    reason = data.get('reason', 'No reason provided')
    
    session = Session()
    
    try:
        signal = session.query(Signal).get(signal_id)
        
        if not signal:
            return jsonify({'error': 'Signal not found'}), 404
        
        # Update signal
        signal.state = 'rejected'
        signal.reviewed_at = datetime.now()
        signal.reviewed_by = ADMIN_NAME
        signal.reject_reason = reason
        
        session.commit()
        
        # Send Telegram notification
        telegram.send_rejection_notification({
            'code': signal.code
        }, reason)
        
        return jsonify({'success': True, 'message': 'Signal rejected'})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@admin_bp.route('/api/admin/signals', methods=['POST'])
def create_signal():
    """Create new signal (from scanner)"""
    
    data = request.json
    
    # Validate signal
    validation = validator.validate_signal(data)
    
    session = Session()
    
    try:
        # Create signal
        signal = Signal(
            code=data['code'],
            strategy_type=data['strategy_type'],
            entry_price=data['entry_price'],
            stop_loss=data['stop_loss'],
            take_profit=data['take_profit'],
            current_price=validation['current_price'],
            price_diff_pct=data.get('price_diff_pct', 0),
            risk_pct=data.get('risk_pct', 0),
            reward_pct=data.get('reward_pct', 0),
            rr_ratio=data.get('rr_ratio', 0),
            rsi=data.get('rsi', 50),
            volume_ratio=data.get('volume_ratio', 1.0),
            validation_errors=str(validation['errors']),
            validation_warnings=str(validation['warnings']),
            quality_score=validation['quality_score'],
            state='pending_review'
        )
        
        session.add(signal)
        session.commit()
        
        # Send Telegram notification
        signal_data = {
            'id': signal.id,
            'code': signal.code,
            'strategy_type': signal.strategy_type,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'current_price': signal.current_price,
            'price_diff_pct': signal.price_diff_pct,
            'risk_pct': signal.risk_pct,
            'reward_pct': signal.reward_pct,
            'rr_ratio': signal.rr_ratio,
            'rsi': signal.rsi,
            'volume_ratio': signal.volume_ratio,
            'validation': validation
        }
        
        telegram.send_signal_notification(signal_data)
        
        return jsonify({
            'success': True,
            'signal_id': signal.id,
            'validation': validation
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# Register blueprint
def register_admin_routes(app):
    """Register admin routes with Flask app"""
    app.register_blueprint(admin_bp)


if __name__ == '__main__':
    # Test
    print("=" * 70)
    print("🛡️ ADMIN API SERVER")
    print("=" * 70)
    print(f"\nOwner: {ADMIN_NAME}")
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Phone: {ADMIN_PHONE}")
    print(f"Dashboard: https://ai-advisor1.netlify.app/admin/signals")
    print("\n" + "=" * 70)
    print("Starting server on http://localhost:5000")
    print("=" * 70 + "\n")
    
    app = Flask(__name__)
    register_admin_routes(app)
    app.run(debug=True, port=5000)
