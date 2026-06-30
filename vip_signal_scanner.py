#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIP SIGNAL SCANNER
==================
File: vip_signal_scanner.py
Đặt cùng thư mục với backend_api.py

CHỨC NĂNG:
  - Chạy scanner riêng cho VIP users
  - Lọc từ signals hiện có: ưu tiên VN30 + confidence >= 65%
  - Thêm route: GET /api/vip/signals, POST /api/vip/signals/scan
  - Tự động gửi Telegram khi có tín hiệu VN30 mới

TÍCH HỢP VÀO backend_api.py:
  # Trong imports:
  try:
      from vip_signal_scanner import init_vip_signal_routes
      _has_vip_signals = True
  except ImportError as e:
      _has_vip_signals = False
      print(f'⚠️  VIP signal scanner not found: {e}')

  # Trong if __name__ == '__main__' (sau init_vip_system):
  if _has_vip_signals:
      init_vip_signal_routes(app, engine, Session)
      print("✅ VIP Signal routes registered")

YAML CRON (GitHub Actions):
  Thêm job vào ci-cd.yml hoặc file mới vip-signal-scanner.yml:
  - cron: '30 2 * * 1-5'  # 9:30 SA giờ VN (UTC+7), thứ 2-6
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import request, jsonify
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ============================================================
# VN30 BASKET
# ============================================================

VN30_TICKERS = {
    'ACB','BCM','BID','BVH','CTG','FPT','GAS','GVR','HDB','HPG',
    'MBB','MSN','MWG','PLX','POW','SAB','SHB','SSB','SSI','STB',
    'TCB','TPB','VCB','VHM','VIB','VIC','VJC','VNM','VPB','VRE'
}

# ============================================================
# CONFIG
# ============================================================

VIP_MIN_CONFIDENCE  = int(os.getenv('VIP_MIN_CONFIDENCE', '65'))  # Ngưỡng confidence tối thiểu
VIP_MIN_RR          = float(os.getenv('VIP_MIN_RR', '1.5'))       # R/R tối thiểu
TELEGRAM_BOT_TOKEN  = os.getenv('TELEGRAM_BOT_TOKEN', '')
ADMIN_SECRET        = os.getenv('ADMIN_SECRET', 'ai-advisor-admin-2026')

# ============================================================
# HELPERS
# ============================================================

def _is_vn30(ticker: str) -> bool:
    return (ticker or '').upper().strip() in VN30_TICKERS


def _get_signal_score(signal_row) -> float:
    """
    Tính điểm ưu tiên cho VIP signal.
    VN30 được ưu tiên cao hơn.
    """
    ticker   = getattr(signal_row, 'ticker', '') or ''
    conf     = float(getattr(signal_row, 'confidence', 0) or getattr(signal_row, 'strength', 0) or 0)
    rr_ratio = float(getattr(signal_row, 'rr_ratio', 0) or 0)

    score = conf
    if _is_vn30(ticker):
        score += 20  # VN30 bonus
    if rr_ratio >= 2.0:
        score += 10
    elif rr_ratio >= 1.5:
        score += 5
    return score


def _signal_to_dict(row) -> dict:
    """Convert SQLAlchemy row to dict for API response."""
    def safe(attr, default=None):
        val = getattr(row, attr, default)
        if val is None:
            return default
        return val

    ticker = (safe('ticker') or '').upper()
    return {
        'id':            safe('id'),
        'ticker':        ticker,
        'action':        safe('action') or safe('signal_type') or 'BUY',
        'strategy':      safe('strategy') or safe('signal_code') or '',
        'strategy_type': safe('strategy_type') or safe('strategy') or '',
        'confidence':    float(safe('confidence') or safe('strength') or 0),
        'entry_price':   float(safe('entry_price') or 0),
        'stop_loss':     float(safe('stop_loss') or 0),
        'take_profit':   float(safe('take_profit') or 0),
        'rr_ratio':      float(safe('rr_ratio') or 0),
        'risk_pct':      float(safe('risk_pct') or 0),
        'reward_pct':    float(safe('reward_pct') or 0),
        'rsi':           float(safe('rsi') or 0) if safe('rsi') else None,
        'ema20':         float(safe('ema20') or 0) if safe('ema20') else None,
        'ema50':         float(safe('ema50') or 0) if safe('ema50') else None,
        'reasoning':     safe('reasoning') or safe('ai_reasoning') or '',
        'status':        safe('status') or 'open',
        'is_vn30':       _is_vn30(ticker),
        'created_at':    safe('created_at').isoformat() if safe('created_at') else None,
        'vip_score':     _get_signal_score(row),
    }


# ============================================================
# TELEGRAM NOTIFICATION
# ============================================================

def _send_telegram(chat_id: str, message: str) -> bool:
    """Gửi Telegram message đến 1 chat_id."""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        import requests as _req
        resp = _req.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id':    chat_id,
                'text':       message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
            },
            timeout=10,
        )
        return resp.status_code == 200
    except Exception as e:
        logger.error(f'[VIP Telegram] Error: {e}')
        return False


def _build_vip_signal_message(signal: dict) -> str:
    """Tạo Telegram message đẹp cho VIP signal."""
    action   = signal.get('action', 'BUY')
    ticker   = signal.get('ticker', '')
    is_vn30  = signal.get('is_vn30', False)
    conf     = signal.get('confidence', 0)
    entry    = signal.get('entry_price', 0)
    sl       = signal.get('stop_loss', 0)
    tp       = signal.get('take_profit', 0)
    rr       = signal.get('rr_ratio', 0)
    strategy = signal.get('strategy_type') or signal.get('strategy', '')
    reasoning= signal.get('reasoning', '')

    action_emoji = '📈' if action == 'BUY' else '📉'
    action_text  = 'MUA VÀO' if action == 'BUY' else 'BÁN RA'
    vn30_tag     = ' ⭐ <b>VN30</b>' if is_vn30 else ''

    msg = (
        f"👑 <b>AI ADVISOR VIP</b>{vn30_tag}\n"
        f"{'─' * 30}\n\n"
        f"{action_emoji} <b>{action_text}: {ticker}</b>\n\n"
        f"💰 Giá vào:  <code>{entry:,.0f}</code>\n"
        f"🛑 Cắt lỗ:   <code>{sl:,.0f}</code>\n"
        f"🎯 Chốt lời: <code>{tp:,.0f}</code>\n"
        f"📊 R/R:      <code>{rr:.1f}x</code>\n"
        f"🔮 Tin cậy:  <code>{conf:.0f}%</code>\n"
    )
    if strategy:
        msg += f"📐 Chiến lược: <code>{strategy}</code>\n"
    if reasoning:
        short_reason = reasoning[:200] + '...' if len(reasoning) > 200 else reasoning
        msg += f"\n💡 {short_reason}\n"

    msg += (
        f"\n{'─' * 30}\n"
        f"⚠️ Đây là công cụ hỗ trợ, không phải tư vấn đầu tư.\n"
        f"🌐 <a href='https://ai-advisor.vn'>ai-advisor.vn</a>"
    )
    return msg


def send_vip_signal_telegram(db_session, signal: dict):
    """
    Gửi Telegram notification đến tất cả VIP users có telegram_chat_id.
    Được gọi sau khi tạo signal mới.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning('[VIP Telegram] TELEGRAM_BOT_TOKEN chưa set')
        return {'sent': 0, 'skipped': 0, 'reason': 'No bot token'}

    try:
        # Import VIPUser từ vip_auth
        from vip_auth import VIPUser
        users = db_session.query(VIPUser).filter(
            VIPUser.is_active == True,
            VIPUser.telegram_chat_id != None,
            VIPUser.telegram_chat_id != '',
        ).all()

        if not users:
            return {'sent': 0, 'skipped': 0, 'reason': 'No VIP users with Telegram'}

        message = _build_vip_signal_message(signal)
        stats = {'sent': 0, 'failed': 0}

        for user in users:
            ok = _send_telegram(user.telegram_chat_id, message)
            if ok:
                stats['sent'] += 1
                logger.info(f'[VIP Telegram] Sent to {user.email}')
            else:
                stats['failed'] += 1
                logger.error(f'[VIP Telegram] Failed for {user.email}')

        return stats

    except Exception as e:
        logger.error(f'[VIP Telegram] send_vip_signal_telegram error: {e}')
        return {'sent': 0, 'error': str(e)}


# ============================================================
# SIGNAL FILTERING LOGIC
# ============================================================

def get_vip_signals_from_db(db_session, limit: int = 50, days: int = 30) -> list:
    """
    Lấy VIP signals từ DB:
    1. VN30 tickers (ưu tiên cao nhất) với confidence >= VIP_MIN_CONFIDENCE
    2. Non-VN30 với confidence cao >= 75
    3. Sort theo VIP score (VN30 + confidence + R/R)

    Args:
        days: Số ngày nhìn lại. 0 hoặc None = không giới hạn (lấy tất cả)
    """
    # Xây dựng date filter clause
    # Dùng COALESCE(created_at, entry_date::timestamp, NOW()) để xử lý NULL created_at
    # days=0 hoặc days >= 999 → không filter ngày (lấy toàn bộ lịch sử)
    if days and days < 999:
        # COALESCE fallback: nếu created_at NULL thì dùng cột date (string 'YYYY-MM-DD')
        # NULLIF('', '') tránh cast empty string → error
        date_clause = """
            AND COALESCE(
                created_at,
                NULLIF(date, '')::timestamp,
                NOW() - INTERVAL '999 days'
            ) >= NOW() - (:days * INTERVAL '1 day')
        """
        date_params = {'days': days}
    else:
        date_clause = ""
        date_params = {}

    try:
        # Thử bảng trading_signals trước, fallback sang signals
        try:
            rows = db_session.execute(text(f"""
                SELECT * FROM trading_signals
                WHERE (
                      (ticker = ANY(:vn30_list) AND confidence >= :min_conf)
                      OR
                      (confidence >= 75)
                  )
                  {date_clause}
                ORDER BY COALESCE(created_at, NOW() - INTERVAL '999 days') DESC
                LIMIT 200
            """), {
                'vn30_list': list(VN30_TICKERS),
                'min_conf':  VIP_MIN_CONFIDENCE,
                **date_params,
            }).fetchall()
        except Exception:
            # CRITICAL: rollback transaction bị abort trước khi retry
            # PostgreSQL abort toàn bộ transaction khi 1 query fail
            try: db_session.rollback()
            except: pass
            # Fallback: bảng signals (production schema — chỉ có cột strength, không có confidence)
            # KHÔNG dùng date filter vì created_at có thể NULL và date là string → cast lỗi
            # FIX (2026-07-01): SELL signals luôn được include bất kể strength.
            # SELL signals không bao giờ được gán strength (luôn NULL) →
            # NULL >= 75 = FALSE trong SQL → VIC SELL và nhiều mã khác biến mất khỏi VIP.
            rows = db_session.execute(text("""
                SELECT * FROM signals
                WHERE (
                      action = 'SELL'
                      OR
                      (ticker = ANY(:vn30_list) AND strength >= :min_conf)
                      OR
                      (strength >= 75)
                  )
                ORDER BY
                    CASE WHEN created_at IS NOT NULL THEN created_at ELSE NULL END DESC NULLS LAST,
                    date DESC NULLS LAST
                LIMIT 200
            """), {
                'vn30_list': list(VN30_TICKERS),
                'min_conf':  VIP_MIN_CONFIDENCE,
            }).fetchall()

        signals = [_signal_to_dict(row) for row in rows]

        # Sort: VN30 trước, sau đó theo vip_score
        signals.sort(key=lambda s: (
            0 if s['is_vn30'] else 1,    # VN30 first
            -s['vip_score'],              # Higher score first
            s.get('created_at', '') or ''
        ))

        return signals[:limit]

    except Exception as e:
        logger.error(f'[VIP Signals] get_vip_signals_from_db error: {e}')
        return []


# ============================================================
# ADMIN AUTH DECORATOR
# ============================================================

import hmac

def require_vip_auth(f):
    """
    Cho phép cả admin (X-Admin-Key) và VIP user (JWT Bearer).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Admin bypass
        admin_key = request.headers.get('X-Admin-Key', '')
        if admin_key and hmac.compare_digest(admin_key, ADMIN_SECRET):
            return f(*args, **kwargs)

        # JWT check
        auth  = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
        if token:
            try:
                import jwt
                JWT_SECRET = os.getenv('JWT_SECRET', 'ai-advisor-jwt-secret-2026')
                jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                return f(*args, **kwargs)
            except Exception:
                pass

        # Fallback: allow nếu không có auth (staging/dev)
        if os.getenv('ENVIRONMENT', 'production') == 'staging':
            return f(*args, **kwargs)

        return jsonify({'error': 'VIP access required'}), 403
    return decorated


# ============================================================
# FLASK ROUTES
# ============================================================

def init_vip_signal_routes(app, engine, Session):
    """
    Đăng ký VIP signal routes vào Flask app.

    Thêm vào backend_api.py:
        from vip_signal_scanner import init_vip_signal_routes
        init_vip_signal_routes(app, engine, Session)
    """

    # ─── GET /api/vip/signals ───────────────────────────────────
    @app.route('/api/vip/signals', methods=['GET'])
    @require_vip_auth
    def get_vip_signals():
        """
        GET /api/vip/signals?limit=50&action=BUY&vn30_only=true&days=30
        Trả về tín hiệu VIP đã lọc theo VN30 + confidence.

        Params:
            days      (int)  : Số ngày nhìn lại, mặc định 30. days=0 → toàn bộ lịch sử
            limit     (int)  : Số tín hiệu tối đa trả về, mặc định 50
            action    (str)  : BUY / SELL / '' (all)
            vn30_only (bool) : true → chỉ trả VN30
        """
        limit     = int(request.args.get('limit', 50))
        action    = request.args.get('action', '').upper()        # BUY / SELL / ''
        vn30_only = request.args.get('vn30_only', '').lower() == 'true'
        # days=0 hoặc không truyền → 30 ngày mặc định; days=999 → lấy tất cả
        raw_days  = request.args.get('days', '30')
        try:
            days = int(raw_days)
        except (ValueError, TypeError):
            days = 30

        session = Session()
        try:
            signals = get_vip_signals_from_db(session, limit=limit * 3, days=days)

            # Filter by action
            if action in ('BUY', 'SELL'):
                signals = [s for s in signals if s.get('action') == action]

            # Filter VN30 only
            if vn30_only:
                signals = [s for s in signals if s['is_vn30']]

            signals = signals[:limit]

            buy_count  = sum(1 for s in signals if s.get('action') == 'BUY')
            sell_count = sum(1 for s in signals if s.get('action') == 'SELL')
            vn30_count = sum(1 for s in signals if s['is_vn30'])

            return jsonify({
                'success':    True,
                'signals':    signals,
                'total':      len(signals),
                'buy_count':  buy_count,
                'sell_count': sell_count,
                'vn30_count': vn30_count,
                'vn30_list':  sorted(list(VN30_TICKERS)),
                'filter': {
                    'min_confidence': VIP_MIN_CONFIDENCE,
                    'min_rr':         VIP_MIN_RR,
                    'vn30_priority':  True,
                    'days':           days if days < 999 else 'all',
                },
                'generated_at': datetime.now().isoformat(),
            })

        except Exception as e:
            logger.error(f'[VIP Signals] GET /api/vip/signals error: {e}')
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()


    # ─── GET /api/vip/signals/history ───────────────────────────
    @app.route('/api/vip/signals/history', methods=['GET'])
    @require_vip_auth
    def get_vip_signal_history():
        """
        GET /api/vip/signals/history?days=7&limit=100
        Lịch sử tín hiệu VIP trong N ngày gần nhất.
        """
        days  = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 100))

        session = Session()
        try:
            try:
                rows = session.execute(text("""
                    SELECT * FROM trading_signals
                    WHERE created_at >= NOW() - (:days * INTERVAL '1 day')
                      AND (
                          ticker = ANY(:vn30_list)
                          OR confidence >= :min_conf
                          OR strength >= :min_conf
                      )
                    ORDER BY created_at DESC
                    LIMIT :lim
                """), {'days': days, 'vn30_list': list(VN30_TICKERS), 'min_conf': VIP_MIN_CONFIDENCE, 'lim': limit}).fetchall()
            except Exception:
                rows = session.execute(text("""
                    SELECT * FROM signals
                    WHERE created_at >= NOW() - (:days * INTERVAL '1 day')
                    ORDER BY created_at DESC
                    LIMIT :lim
                """), {'days': days, 'lim': limit}).fetchall()

            signals = [_signal_to_dict(row) for row in rows]
            signals.sort(key=lambda s: (-int(s['is_vn30']), -(s['vip_score'] or 0)))

            return jsonify({
                'success': True,
                'signals': signals,
                'total':   len(signals),
                'days':    days,
            })

        except Exception as e:
            logger.error(f'[VIP Signals] history error: {e}')
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()


    # ─── POST /api/vip/signals/scan ─────────────────────────────
    @app.route('/api/vip/signals/scan', methods=['POST'])
    @require_vip_auth
    def trigger_vip_scan():
        """
        POST /api/vip/signals/scan
        Kích hoạt chạy scanner VIP ngay lập tức (background thread).
        Scanner sẽ: lọc VN30 → lưu DB → gửi Telegram VIP.
        """
        import threading

        def _run_vip_scan():
            logger.info('[VIP Scanner] Starting VIP signal scan...')
            session_inner = Session()
            try:
                # Thử gọi scanner chính nếu có
                try:
                    from sell_signal_scanner_v5_2 import main as run_scanner
                    # Scanner sẽ tự lưu vào DB
                    logger.info('[VIP Scanner] Running main scanner...')
                    run_scanner()
                except ImportError:
                    logger.warning('[VIP Scanner] Main scanner not importable, using vnstock direct')
                    _run_vn30_scan_direct(session_inner)

                # Sau khi scanner xong, lấy signals mới nhất và gửi Telegram
                new_signals = get_vip_signals_from_db(session_inner, limit=10)
                if new_signals:
                    stats = {'sent': 0, 'failed': 0}
                    for sig in new_signals:
                        result = send_vip_signal_telegram(session_inner, sig)
                        stats['sent']   += result.get('sent', 0)
                        stats['failed'] += result.get('failed', 0)
                    logger.info(f'[VIP Scanner] Telegram sent: {stats}')

            except Exception as e:
                logger.error(f'[VIP Scanner] _run_vip_scan error: {e}')
            finally:
                session_inner.close()

        thread = threading.Thread(target=_run_vip_scan, daemon=True)
        thread.start()

        return jsonify({
            'success': True,
            'message': 'VIP scan đang chạy. Kết quả sẽ tự động gửi qua Telegram.',
            'eta_minutes': 3,
        })


    # ─── GET /api/vip/info ──────────────────────────────────────
    @app.route('/api/vip/info', methods=['GET'])
    @require_vip_auth
    def get_vip_info():
        """
        GET /api/vip/info
        Thông tin về VIP signal system: VN30 list, config, stats.
        """
        session = Session()
        try:
            # Đếm tín hiệu hôm nay
            try:
                today_count = session.execute(text("""
                    SELECT COUNT(*) FROM trading_signals
                    WHERE created_at >= CURRENT_DATE
                      AND (ticker = ANY(:vn30_list) OR confidence >= :min_conf)
                """), {'vn30_list': list(VN30_TICKERS), 'min_conf': VIP_MIN_CONFIDENCE}).scalar()
            except Exception:
                today_count = 0

            return jsonify({
                'success': True,
                'vn30_list':          sorted(list(VN30_TICKERS)),
                'vn30_count':         len(VN30_TICKERS),
                'min_confidence':     VIP_MIN_CONFIDENCE,
                'min_rr':             VIP_MIN_RR,
                'today_signal_count': today_count,
                'features': [
                    'Tín hiệu ưu tiên VN30 (30 mã vốn hóa lớn nhất)',
                    'Lọc confidence ≥ 65%',
                    'Tự động gửi Telegram khi có tín hiệu',
                    'Chiến lược: EMA Cross + Pullback',
                    'R/R ratio ≥ 1.5x',
                ],
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()


    # ─── POST /api/admin/vip/signals/notify ─────────────────────
    @app.route('/api/admin/vip/signals/notify', methods=['POST'])
    def admin_broadcast_vip_signal():
        """
        POST /api/admin/vip/signals/notify
        Admin tay gửi custom signal notification đến VIP users.
        Body: { ticker, action, entry_price, stop_loss, take_profit, reasoning }
        """
        admin_key = request.headers.get('X-Admin-Key', '')
        if not hmac.compare_digest(admin_key, ADMIN_SECRET):
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json() or {}
        if not data.get('ticker'):
            return jsonify({'error': 'ticker required'}), 400

        signal_dict = {
            'ticker':       data.get('ticker', '').upper(),
            'action':       data.get('action', 'BUY').upper(),
            'entry_price':  float(data.get('entry_price', 0)),
            'stop_loss':    float(data.get('stop_loss', 0)),
            'take_profit':  float(data.get('take_profit', 0)),
            'rr_ratio':     float(data.get('rr_ratio', 0)),
            'confidence':   float(data.get('confidence', 0)),
            'strategy_type':data.get('strategy_type', ''),
            'reasoning':    data.get('reasoning', ''),
            'is_vn30':      _is_vn30(data.get('ticker', '')),
        }

        session = Session()
        try:
            stats = send_vip_signal_telegram(session, signal_dict)
            return jsonify({'success': True, 'stats': stats, 'signal': signal_dict})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()


    print("✅ VIP Signal routes registered:")
    print("   GET  /api/vip/signals              [VIP AUTH]")
    print("   GET  /api/vip/signals/history      [VIP AUTH]")
    print("   POST /api/vip/signals/scan         [VIP AUTH]")
    print("   GET  /api/vip/info                 [VIP AUTH]")
    print("   POST /api/admin/vip/signals/notify [ADMIN]")


# ============================================================
# DIRECT VN30 SCAN (fallback nếu không import được scanner chính)
# ============================================================

def _run_vn30_scan_direct(db_session):
    """
    Fallback scanner: Trực tiếp dùng vnstock để scan VN30.
    Chỉ chạy khi không import được sell_signal_scanner_v5_2.
    """
    logger.info('[VIP Scanner] Running direct VN30 scan via vnstock...')
    try:
        try:
            from vnstock import Vnstock
        except ImportError:
            from vnstock3 import Vnstock

        import numpy as np

        results = []
        stock_client = Vnstock()

        for ticker in sorted(VN30_TICKERS):
            try:
                stock = stock_client.stock(symbol=ticker, source='VCI')
                df = stock.quote.history(start='2024-01-01', end=datetime.now().strftime('%Y-%m-%d'), interval='1D')

                if df is None or len(df) < 60:
                    continue

                close = df['close'].values.astype(float)
                volume= df['volume'].values.astype(float)

                # EMA calculations
                def ema(arr, period):
                    result = np.zeros(len(arr))
                    result[:period] = arr[:period].mean()
                    k = 2.0 / (period + 1)
                    for i in range(period, len(arr)):
                        result[i] = arr[i] * k + result[i-1] * (1 - k)
                    return result

                ema20 = ema(close, 20)
                ema50 = ema(close, 50)

                # RSI
                def rsi(arr, period=14):
                    delta = np.diff(arr)
                    gain  = np.where(delta > 0, delta, 0)
                    loss  = np.where(delta < 0, -delta, 0)
                    avg_gain = np.mean(gain[-period:])
                    avg_loss = np.mean(loss[-period:])
                    if avg_loss == 0:
                        return 100.0
                    rs = avg_gain / avg_loss
                    return 100 - (100 / (1 + rs))

                current_rsi  = rsi(close)
                current_price = close[-1]
                prev_ema20   = ema20[-2]
                curr_ema20   = ema20[-1]
                prev_ema50   = ema50[-2]
                curr_ema50   = ema50[-1]

                signal_type  = None
                confidence   = 0.0
                strategy     = ''

                # EMA Cross strategy
                if prev_ema20 <= prev_ema50 and curr_ema20 > curr_ema50:
                    if 40 <= current_rsi <= 65:
                        vol_avg = np.mean(volume[-20:])
                        vol_increase = volume[-1] > vol_avg * 1.2
                        signal_type = 'BUY'
                        confidence  = 65.0 + (10.0 if vol_increase else 0) + max(0, (60 - current_rsi) * 0.3)
                        strategy    = 'EMA_CROSS'

                # Pullback strategy
                elif curr_ema20 > curr_ema50 * 1.02:  # Uptrend
                    near_ema20 = abs(current_price - curr_ema20) / curr_ema20 < 0.015
                    if near_ema20 and current_rsi < 45:
                        signal_type = 'BUY'
                        confidence  = 68.0 + (50 - current_rsi) * 0.3
                        strategy    = 'PULLBACK'

                if signal_type and confidence >= VIP_MIN_CONFIDENCE:
                    risk   = current_price - curr_ema20 * 0.97
                    reward = current_price * 0.08  # 8% take profit
                    rr     = reward / risk if risk > 0 else 0

                    if rr >= VIP_MIN_RR:
                        signal_data = {
                            'ticker':       ticker,
                            'action':       signal_type,
                            'strategy':     strategy,
                            'strategy_type':strategy,
                            'confidence':   round(min(confidence, 95.0), 1),
                            'entry_price':  round(current_price, 2),
                            'stop_loss':    round(curr_ema20 * 0.97, 2),
                            'take_profit':  round(current_price * 1.08, 2),
                            'rr_ratio':     round(rr, 2),
                            'risk_pct':     round((current_price - curr_ema20 * 0.97) / current_price * 100, 1),
                            'reward_pct':   8.0,
                            'rsi':          round(current_rsi, 1),
                            'ema20':        round(curr_ema20, 2),
                            'ema50':        round(curr_ema50, 2),
                            'is_vn30':      True,
                        }
                        results.append(signal_data)
                        logger.info(f'[VIP Scanner] {ticker}: {signal_type} signal (conf={confidence:.0f}%)')

            except Exception as e:
                logger.warning(f'[VIP Scanner] Skip {ticker}: {e}')
                continue

        logger.info(f'[VIP Scanner] Direct scan complete: {len(results)} signals found')
        return results

    except Exception as e:
        logger.error(f'[VIP Scanner] _run_vn30_scan_direct error: {e}')
        return []


# ============================================================
# STANDALONE RUNNER
# ============================================================

if __name__ == '__main__':
    """
    Chạy standalone để test:
        python vip_signal_scanner.py --test
        python vip_signal_scanner.py --scan
    
    Hoặc dùng trong GitHub Actions cron:
        python vip_signal_scanner.py --scan --notify
    """
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    parser = argparse.ArgumentParser(description='VIP Signal Scanner')
    parser.add_argument('--test',   action='store_true', help='Test Telegram connection')
    parser.add_argument('--scan',   action='store_true', help='Run VN30 scan')
    parser.add_argument('--notify', action='store_true', help='Send Telegram after scan')
    parser.add_argument('--ticker', help='Test single ticker', default=None)
    args = parser.parse_args()

    if args.test:
        print('🧪 Testing Telegram...')
        ok = _send_telegram(
            os.getenv('TEST_CHAT_ID', ''),
            '🧪 VIP Signal Scanner — Test connection OK!\n\n✅ Hệ thống sẵn sàng gửi tín hiệu VN30.'
        )
        print(f'Result: {"✅ OK" if ok else "❌ Failed (check TELEGRAM_BOT_TOKEN and TEST_CHAT_ID)"}')

    elif args.scan:
        print(f'🔍 Scanning VN30 ({len(VN30_TICKERS)} tickers)...')
        results = _run_vn30_scan_direct(None)
        print(f'\n📊 Found {len(results)} signals:')
        for r in results:
            print(f"  {r['ticker']:5} | {r['action']:4} | {r['strategy']:12} | conf={r['confidence']:.0f}% | entry={r['entry_price']:.0f} | R/R={r['rr_ratio']:.1f}x")

        if args.notify and results:
            print(f'\n📲 Sending {len(results)} signals to Telegram...')
            for sig in results[:5]:  # Giới hạn 5 tín hiệu để không spam
                chat_id = os.getenv('TEST_CHAT_ID', '')
                if chat_id:
                    msg = _build_vip_signal_message(sig)
                    ok  = _send_telegram(chat_id, msg)
                    print(f'  {sig["ticker"]}: {"✅" if ok else "❌"}')

    else:
        print('VIP Signal Scanner — Chạy với --test hoặc --scan [--notify]')
        print(f'VN30 list ({len(VN30_TICKERS)}): {", ".join(sorted(VN30_TICKERS))}')
        print(f'Min confidence: {VIP_MIN_CONFIDENCE}%')
        print(f'Min R/R: {VIP_MIN_RR}x')
