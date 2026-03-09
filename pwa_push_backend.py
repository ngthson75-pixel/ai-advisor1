"""
AI ADVISOR - WEB PUSH NOTIFICATION BACKEND MODULE
==================================================
File: pwa_push_backend.py
Version: 1.0

Tích hợp vào backend_api.py để gửi push notification
khi có tín hiệu mua/bán mới được duyệt.

INSTALL:
  pip install pywebpush

SETUP:
  1. Generate VAPID keys (chạy 1 lần duy nhất):
     python pwa_push_backend.py --generate-keys

  2. Add vào .env:
     VAPID_PUBLIC_KEY=...
     VAPID_PRIVATE_KEY=...
     VAPID_EMAIL=mailto:admin@ai-advisor.vn

  3. Import vào backend_api.py:
     from pwa_push_backend import push_service, init_push_routes
     init_push_routes(app, db_session_factory)
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List

# ============================================================
# GRACEFUL IMPORT - App vẫn chạy nếu chưa install pywebpush
# ============================================================
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
    print("✅ pywebpush loaded - Push notifications enabled")
except ImportError:
    WEBPUSH_AVAILABLE = False
    print("⚠️  pywebpush not installed. Run: pip install pywebpush")
    print("   Push notifications disabled but app continues normally.")

from flask import Blueprint, request, jsonify
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, text
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# ============================================================
# DATABASE MODEL - Push Subscriptions
# ============================================================
# Thêm vào models hiện có trong backend_api.py

PUSH_SUBSCRIPTION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    endpoint TEXT NOT NULL UNIQUE,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    failed_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_push_sub_user_id ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_sub_active ON push_subscriptions(is_active);
"""

# ============================================================
# PUSH NOTIFICATION SERVICE
# ============================================================

class PushNotificationService:
    """
    Web Push Notification Service
    Gửi real-time push đến user mobile/desktop khi có tín hiệu mới
    """

    def __init__(self):
        self.vapid_private_key = os.getenv('VAPID_PRIVATE_KEY', '')
        self.vapid_public_key = os.getenv('VAPID_PUBLIC_KEY', '')
        self.vapid_email = os.getenv('VAPID_EMAIL', 'mailto:admin@ai-advisor.vn')
        self.enabled = WEBPUSH_AVAILABLE and bool(self.vapid_private_key)

        if not self.enabled:
            if not WEBPUSH_AVAILABLE:
                logger.warning("Push disabled: pywebpush not installed")
            else:
                logger.warning("Push disabled: VAPID_PRIVATE_KEY not set in .env")

    def send(self, subscription_info: dict, payload: dict) -> bool:
        """
        Gửi push notification đến 1 subscription
        
        Args:
            subscription_info: {endpoint, keys: {p256dh, auth}}
            payload: notification data dict
        Returns:
            True if sent, False if failed
        """
        if not self.enabled:
            logger.debug(f"[PUSH SKIP] {payload.get('title')} - push disabled")
            return False

        try:
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": self.vapid_email,
                    "exp": int(datetime.now().timestamp()) + 86400  # 24h
                }
            )
            return True

        except WebPushException as e:
            status_code = e.response.status_code if e.response else None

            # 410 Gone = subscription expired, remove from DB
            if status_code == 410:
                return None  # Signal to remove subscription

            logger.error(f"[PUSH ERROR] {status_code}: {e}")
            return False

        except Exception as e:
            logger.error(f"[PUSH EXCEPTION] {e}")
            return False

    def broadcast_to_all(self, db_session, payload: dict) -> dict:
        """
        Gửi notification đến TẤT CẢ users đang subscribe
        Dùng khi có tín hiệu mới cho mọi user (Premium)
        
        Returns:
            {sent: int, failed: int, removed: int}
        """
        try:
            result = db_session.execute(
                text("SELECT id, endpoint, p256dh_key, auth_key FROM push_subscriptions WHERE is_active = TRUE")
            ).fetchall()

            stats = {"sent": 0, "failed": 0, "removed": 0, "total": len(result)}

            for row in result:
                sub_info = {
                    "endpoint": row[1],
                    "keys": {
                        "p256dh": row[2],
                        "auth": row[3]
                    }
                }
                send_result = self.send(sub_info, payload)

                if send_result is True:
                    stats["sent"] += 1
                elif send_result is None:
                    # Subscription expired - deactivate
                    db_session.execute(
                        text("UPDATE push_subscriptions SET is_active = FALSE WHERE id = :id"),
                        {"id": row[0]}
                    )
                    stats["removed"] += 1
                else:
                    stats["failed"] += 1

            db_session.commit()
            logger.info(f"[PUSH BROADCAST] {stats}")
            return stats

        except Exception as e:
            logger.error(f"[PUSH BROADCAST ERROR] {e}")
            db_session.rollback()
            return {"sent": 0, "failed": 0, "removed": 0, "error": str(e)}

    def broadcast_to_user(self, db_session, user_id: str, payload: dict) -> dict:
        """
        Gửi notification đến 1 user cụ thể (tất cả devices của họ)
        """
        try:
            result = db_session.execute(
                text("SELECT id, endpoint, p256dh_key, auth_key FROM push_subscriptions WHERE user_id = :uid AND is_active = TRUE"),
                {"uid": user_id}
            ).fetchall()

            stats = {"sent": 0, "failed": 0}
            for row in result:
                sub_info = {
                    "endpoint": row[1],
                    "keys": {"p256dh": row[2], "auth": row[3]}
                }
                ok = self.send(sub_info, payload)
                if ok is True:
                    stats["sent"] += 1
                elif ok is None:
                    db_session.execute(
                        text("UPDATE push_subscriptions SET is_active = FALSE WHERE id = :id"),
                        {"id": row[0]}
                    )
                else:
                    stats["failed"] += 1

            db_session.commit()
            return stats

        except Exception as e:
            logger.error(f"[PUSH USER ERROR] {e}")
            return {"sent": 0, "failed": 0, "error": str(e)}


# ============================================================
# PAYLOAD BUILDERS - Tạo nội dung thông báo chuẩn
# ============================================================

class SignalPayloadBuilder:
    """
    Tạo notification payload chuẩn cho từng loại tín hiệu
    """

    @staticmethod
    def buy_signal(signal: dict) -> dict:
        """
        Payload khi có tín hiệu MUA mới được duyệt
        """
        ticker = signal.get('ticker', signal.get('code', ''))
        entry = signal.get('entry_price', 0)
        sl = signal.get('stop_loss', 0)
        tp = signal.get('take_profit', 0)
        strategy = signal.get('strategy_type', '')
        rr = signal.get('rr_ratio', 0)
        
        # Risk/reward percentage  
        risk_pct = signal.get('risk_pct', 0)
        reward_pct = signal.get('reward_pct', 0)

        return {
            "type": "buy_signal",
            "title": f"🟢 Tín Hiệu MUA: {ticker}",
            "body": (
                f"Giá vào: {entry:,.0f} | SL: {sl:,.0f} (-{risk_pct:.1f}%) | "
                f"TP: {tp:,.0f} (+{reward_pct:.1f}%) | R/R: {rr:.1f}x"
            ),
            "ticker": ticker,
            "signal_id": signal.get('id'),
            "signal_code": signal.get('signal_code'),
            "strategy": strategy,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "url": f"/dashboard/signals?type=buy&ticker={ticker}",
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def sell_signal(signal: dict) -> dict:
        """
        Payload khi có tín hiệu BÁN / Chốt lời / Cắt lỗ
        """
        ticker = signal.get('ticker', signal.get('code', ''))
        sell_price = signal.get('entry_price', 0)  # For SELL signals, entry_price = sell price
        sell_reason = signal.get('sell_reason', 'MANUAL')
        
        # Determine emoji and urgency based on sell reason
        reason_map = {
            'STOP_LOSS': ('🔴 CẮT LỖ', 'URGENT - Dừng lỗ ngay!', True),
            'TAKE_PROFIT': ('💰 CHỐT LỜI', 'Đạt mục tiêu lợi nhuận', False),
            'MANUAL': ('🟡 TÍN HIỆU BÁN', 'Xem xét bán theo tín hiệu', False),
            'TRAILING_STOP': ('🟠 TRAILING STOP', 'Bảo vệ lợi nhuận', True),
        }
        
        label, desc, urgent = reason_map.get(sell_reason, ('🟡 TÍN HIỆU BÁN', '', False))
        buy_signal_code = signal.get('buy_signal_code', '')
        
        body_parts = [f"Giá bán: {sell_price:,.0f}"]
        if buy_signal_code:
            body_parts.append(f"Lệnh: {buy_signal_code}")
        body_parts.append(desc)

        return {
            "type": "sell_signal",
            "title": f"{label}: {ticker}",
            "body": " | ".join(body_parts),
            "ticker": ticker,
            "signal_id": signal.get('id'),
            "sell_reason": sell_reason,
            "sell_price": sell_price,
            "buy_signal_code": buy_signal_code,
            "urgent": urgent,
            "url": f"/dashboard/signals?type=sell&ticker={ticker}",
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# FLASK BLUEPRINT - API Routes
# ============================================================

push_bp = Blueprint('push', __name__)
push_service = PushNotificationService()


def init_push_routes(app, get_db_session):
    """
    Đăng ký push notification routes vào Flask app hiện có.
    
    Gọi trong backend_api.py:
        from pwa_push_backend import push_service, init_push_routes, SignalPayloadBuilder
        init_push_routes(app, get_session)
    """

    @app.route('/api/push/vapid-public-key', methods=['GET'])
    def get_vapid_public_key():
        """
        Frontend cần public key để subscribe
        """
        key = push_service.vapid_public_key
        if not key:
            return jsonify({'error': 'VAPID not configured'}), 503
        return jsonify({'publicKey': key})


    @app.route('/api/push/subscribe', methods=['POST'])
    def subscribe_push():
        """
        Lưu push subscription từ browser/mobile
        
        Body:
        {
          "userId": "user_123",          // Optional nếu chưa login
          "subscription": {
            "endpoint": "https://fcm.googleapis.com/...",
            "keys": {
              "p256dh": "...",
              "auth": "..."
            }
          }
        }
        """
        data = request.get_json()
        if not data or 'subscription' not in data:
            return jsonify({'error': 'Missing subscription data'}), 400

        sub = data['subscription']
        endpoint = sub.get('endpoint', '')
        keys = sub.get('keys', {})
        p256dh = keys.get('p256dh', '')
        auth = keys.get('auth', '')

        if not endpoint or not p256dh or not auth:
            return jsonify({'error': 'Invalid subscription format'}), 400

        user_id = data.get('userId', 'anonymous')
        user_agent = request.headers.get('User-Agent', '')[:200]

        try:
            session = get_db_session()

            # Upsert subscription
            existing = session.execute(
                text("SELECT id FROM push_subscriptions WHERE endpoint = :ep"),
                {"ep": endpoint}
            ).fetchone()

            if existing:
                session.execute(
                    text("""UPDATE push_subscriptions 
                       SET user_id = :uid, p256dh_key = :p256dh, auth_key = :auth,
                           is_active = TRUE, last_used_at = NOW()
                       WHERE endpoint = :ep"""),
                    {"uid": user_id, "p256dh": p256dh, "auth": auth, "ep": endpoint}
                )
            else:
                session.execute(
                    text("""INSERT INTO push_subscriptions 
                       (user_id, endpoint, p256dh_key, auth_key, user_agent)
                       VALUES (:uid, :ep, :p256dh, :auth, :ua)"""),
                    {"uid": user_id, "ep": endpoint, "p256dh": p256dh,
                     "auth": auth, "ua": user_agent}
                )

            session.commit()
            logger.info(f"[PUSH] Subscribed: user={user_id}, endpoint=...{endpoint[-20:]}")
            return jsonify({'status': 'subscribed', 'userId': user_id})

        except Exception as e:
            logger.error(f"[PUSH SUBSCRIBE ERROR] {e}")
            return jsonify({'error': str(e)}), 500


    @app.route('/api/push/unsubscribe', methods=['POST'])
    def unsubscribe_push():
        """
        User tắt notifications
        """
        data = request.get_json()
        endpoint = data.get('endpoint', '') if data else ''

        if not endpoint:
            return jsonify({'error': 'Missing endpoint'}), 400

        try:
            session = get_db_session()
            session.execute(
                text("UPDATE push_subscriptions SET is_active = FALSE WHERE endpoint = :ep"),
                {"ep": endpoint}
            )
            session.commit()
            return jsonify({'status': 'unsubscribed'})

        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/api/push/test', methods=['POST'])
    def test_push():
        """
        Test gửi push (chỉ dùng khi develop/admin)
        """
        data = request.get_json() or {}
        signal_type = data.get('type', 'buy_signal')
        
        test_signal = {
            "id": 9999,
            "code": "VCB",
            "ticker": "VCB",
            "signal_code": "VCB-TEST",
            "strategy_type": "SWING_T+",
            "entry_price": 89500,
            "stop_loss": 85025,
            "take_profit": 96660,
            "sell_reason": "TAKE_PROFIT",
            "buy_signal_code": "VCB-1001",
            "risk_pct": 5.0,
            "reward_pct": 8.0,
            "rr_ratio": 1.6,
        }

        if signal_type == 'sell_signal':
            payload = SignalPayloadBuilder.sell_signal(test_signal)
        else:
            payload = SignalPayloadBuilder.buy_signal(test_signal)

        try:
            session = get_db_session()
            stats = push_service.broadcast_to_all(session, payload)
            return jsonify({'status': 'sent', 'stats': stats, 'payload': payload})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    print("✅ Push notification routes registered:")
    print("   GET  /api/push/vapid-public-key")
    print("   POST /api/push/subscribe")
    print("   POST /api/push/unsubscribe")
    print("   POST /api/push/test")


# ============================================================
# HELPER FUNCTION - Gọi sau khi signal được tạo/duyệt
# ============================================================

def notify_signal_created(db_session, signal: dict, signal_action: str = 'BUY'):
    """
    Gọi function này trong /api/signals POST handler
    sau khi signal được tạo thành công.
    
    Tích hợp vào backend_api.py:
    
        # Trong route /api/signals (POST):
        from pwa_push_backend import push_service, notify_signal_created, SignalPayloadBuilder
        
        # ... sau khi lưu signal ...
        notify_signal_created(session, signal_data, signal.action)
    
    Args:
        db_session: SQLAlchemy session
        signal: dict với thông tin signal
        signal_action: 'BUY' hoặc 'SELL'
    """
    try:
        if signal_action == 'BUY':
            payload = SignalPayloadBuilder.buy_signal(signal)
        elif signal_action == 'SELL':
            payload = SignalPayloadBuilder.sell_signal(signal)
        else:
            return

        stats = push_service.broadcast_to_all(db_session, payload)
        logger.info(f"[PUSH SIGNAL] {signal_action} {signal.get('ticker', '')} → {stats}")
        return stats

    except Exception as e:
        logger.error(f"[PUSH SIGNAL ERROR] {e}")
        # Don't raise - push failure shouldn't break signal creation


# ============================================================
# KEY GENERATOR - Chạy 1 lần để tạo VAPID keys
# ============================================================

def generate_vapid_keys():
    """
    Tạo VAPID key pair.
    Chạy: python pwa_push_backend.py --generate-keys
    """
    try:
        from py_vapid import Vapid
        vapid = Vapid()
        vapid.generate_keys()
        
        # Export as base64url
        public_key = vapid.public_key.public_bytes(
            encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.PEM,
            format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PublicFormat']).PublicFormat.SubjectPublicKeyInfo
        )
        
        print("\n" + "="*60)
        print("🔑 VAPID KEYS GENERATED")
        print("="*60)
        print("\nThêm vào file .env:")
        print(f"VAPID_PUBLIC_KEY={vapid.public_key_urlsafe}")
        print(f"VAPID_PRIVATE_KEY={vapid.private_key_urlsafe}")
        print(f"VAPID_EMAIL=mailto:admin@ai-advisor.vn")
        print("\n⚠️  QUAN TRỌNG:")
        print("- Lưu keys này cẩn thận, KHÔNG commit lên git")
        print("- VAPID_PUBLIC_KEY dùng ở cả frontend và backend")
        print("- VAPID_PRIVATE_KEY chỉ dùng ở backend (secret)")
        print("="*60)
        
    except ImportError:
        print("❌ Cần install: pip install pywebpush")
        print("\nAlternative - dùng online generator:")
        print("https://vapidkeys.com/")
        print("Hoặc: npx web-push generate-vapid-keys")


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == '__main__':
    import sys
    
    if '--generate-keys' in sys.argv:
        generate_vapid_keys()
    else:
        print("AI Advisor - Push Notification Backend Module")
        print("\nUsage:")
        print("  python pwa_push_backend.py --generate-keys  # Tạo VAPID keys")
        print("\nIntegration vào backend_api.py:")
        print("  from pwa_push_backend import push_service, init_push_routes, notify_signal_created")
        print("  init_push_routes(app, get_session)")
        print("\nGọi khi signal mới được tạo:")
        print("  notify_signal_created(session, signal_dict, 'BUY')")
