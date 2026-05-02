"""
AI ADVISOR - VIP USER MANAGEMENT + AUTH
========================================
File: vip_auth.py
Version: 1.0

Tích hợp vào backend_api.py:
    from vip_auth import init_vip_system, push_vip_users
    init_vip_system(app, engine, Session)

Admin dùng X-Admin-Key header để gọi admin routes.
Users dùng JWT Bearer token sau khi login.
"""

import os
import json
import secrets
import hashlib
import hmac
import random
import string
import logging
from datetime import datetime, timedelta
from functools import wraps

import jwt  # pip install PyJWT
from flask import request, jsonify, g
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ============================================================
# CONFIG
# ============================================================

ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'ai-advisor-admin-2026')
JWT_SECRET   = os.getenv('JWT_SECRET',   'ai-advisor-jwt-secret-2026')
JWT_EXPIRY_DAYS = 30

# ============================================================
# DATABASE MODEL
# ============================================================

VIPBase = declarative_base()


class VIPUser(VIPBase):
    __tablename__ = 'vip_users'

    id              = Column(Integer, primary_key=True)
    email           = Column(String(255), unique=True, nullable=False)
    password_hash   = Column(String(255), nullable=False)
    full_name       = Column(String(255))
    phone           = Column(String(20))
    tier            = Column(String(20), default='vip')        # free / vip / pro
    is_push_enabled = Column(Boolean, default=False)           # Admin bật/tắt
    is_active       = Column(Boolean, default=True)
    notes           = Column(Text)                              # Admin private notes
    telegram_chat_id = Column(String(50))                      # Telegram chat_id để gửi notification
    created_at      = Column(DateTime, default=datetime.now)
    last_login_at   = Column(DateTime)


# ============================================================
# AUTH HELPERS
# ============================================================

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def _check_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(_hash_password(password), hashed)


def _generate_temp_password(length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def _create_jwt(user_id: int, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email':   email,
        'exp':     datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
        'iat':     datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def _verify_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ============================================================
# DECORATORS
# ============================================================

def require_admin(f):
    """Bảo vệ admin routes bằng X-Admin-Key header"""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Admin-Key', '')
        if not hmac.compare_digest(key, ADMIN_SECRET):
            return jsonify({'error': 'Unauthorized - Admin key required'}), 401
        return f(*args, **kwargs)
    return decorated


def require_vip_auth(f):
    """Bảo vệ VIP routes bằng JWT Bearer token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth  = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
        if not token:
            return jsonify({'error': 'Token required'}), 401
        payload = _verify_jwt(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        g.user_id = payload['user_id']
        g.email   = payload['email']
        return f(*args, **kwargs)
    return decorated


# ============================================================
# ============================================================
# TELEGRAM - Gửi notification đến VIP users qua Telegram
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

def send_telegram_to_vip_users(db_session, message: str) -> dict:
    """
    Gửi Telegram message đến tất cả VIP users có telegram_chat_id.
    Dùng sau khi có tín hiệu mới.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning('[Telegram] TELEGRAM_BOT_TOKEN chưa được set')
        return {'sent': 0, 'failed': 0, 'skipped': 0}

    try:
        users = db_session.query(VIPUser).filter(
            VIPUser.is_active == True,
            VIPUser.telegram_chat_id != None,
            VIPUser.telegram_chat_id != '',
        ).all()

        if not users:
            return {'sent': 0, 'failed': 0, 'skipped': 0,
                    'note': 'Không có VIP user nào có Telegram chat_id'}

        import requests as req_lib
        stats = {'sent': 0, 'failed': 0, 'skipped': 0}

        for user in users:
            try:
                resp = req_lib.post(
                    f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                    json={
                        'chat_id':    user.telegram_chat_id,
                        'text':       message,
                        'parse_mode': 'HTML',
                        'disable_web_page_preview': True,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    stats['sent'] += 1
                    logger.info(f'[Telegram] Sent to {user.email}')
                else:
                    stats['failed'] += 1
                    logger.error(f'[Telegram] Failed {user.email}: {resp.text}')
            except Exception as e:
                stats['failed'] += 1
                logger.error(f'[Telegram] Error {user.email}: {e}')

        return stats

    except Exception as e:
        logger.error(f'[Telegram] send_telegram_to_vip_users error: {e}')
        return {'sent': 0, 'failed': 0, 'error': str(e)}


# ============================================================
# PUSH VIP USERS - Thay thế broadcast_to_all()
# ============================================================

def push_vip_users(db_session, payload: dict) -> dict:
    """
    Gửi push ONLY đến users có is_push_enabled = TRUE trong vip_users.
    
    Dùng thay thế notify_signal_created() trong backend_api.py:
        from vip_auth import push_vip_users
        from pwa_push_backend import SignalPayloadBuilder
        
        signal_payload = SignalPayloadBuilder.buy_signal(signal_dict)
        push_vip_users(session, signal_payload)
    """
    try:
        rows = db_session.execute(text("""
            SELECT ps.id, ps.endpoint, ps.p256dh_key, ps.auth_key
            FROM   push_subscriptions ps
            JOIN   vip_users          vu
                   ON ps.user_id = vu.email
            WHERE  ps.is_active       = TRUE
              AND  vu.is_push_enabled = TRUE
              AND  vu.is_active       = TRUE
        """)).fetchall()

        if not rows:
            return {"sent": 0, "failed": 0, "total": 0,
                    "note": "No VIP users with push enabled"}

        from pwa_push_backend import push_service

        stats = {"sent": 0, "failed": 0, "removed": 0, "total": len(rows)}

        for row in rows:
            sub_info = {
                "endpoint": row[1],
                "keys": {"p256dh": row[2], "auth": row[3]}
            }
            result = push_service.send(sub_info, payload)

            if result is True:
                stats["sent"] += 1
                db_session.execute(text(
                    "UPDATE push_subscriptions SET last_used_at = NOW() WHERE id = :id"
                ), {"id": row[0]})
            elif result is None:               # 410 Gone - subscription expired
                db_session.execute(text(
                    "UPDATE push_subscriptions SET is_active = FALSE WHERE id = :id"
                ), {"id": row[0]})
                stats["removed"] += 1
            else:
                stats["failed"] += 1

        db_session.commit()
        logger.info(f"[PUSH VIP] {stats}")
        return stats

    except Exception as e:
        db_session.rollback()
        logger.error(f"[PUSH VIP ERROR] {e}")
        return {"sent": 0, "failed": 0, "error": str(e)}


# ============================================================
# INIT - Đăng ký routes vào Flask app
# ============================================================

def init_vip_system(app, engine, Session):
    """
    Gọi trong backend_api.py SAU KHI khởi tạo app và engine:

        from vip_auth import init_vip_system
        init_vip_system(app, engine, Session)
    """
    # Tạo bảng vip_users nếu chưa có
    VIPBase.metadata.create_all(engine)
    logger.info("✅ VIP tables ready")

    # ─────────────────────────────────────────────
    # USER ROUTES
    # ─────────────────────────────────────────────

    @app.route('/api/auth/login', methods=['POST'])
    def vip_login():
        """
        POST /api/auth/login
        Body: { "email": "...", "password": "..." }
        Returns: { token, user }
        """
        data     = request.get_json() or {}
        email    = data.get('email', '').lower().strip()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email và mật khẩu không được để trống'}), 400

        session = Session()
        try:
            user = session.query(VIPUser).filter_by(
                email=email, is_active=True
            ).first()

            if not user or not _check_password(password, user.password_hash):
                return jsonify({'error': 'Email hoặc mật khẩu không đúng'}), 401

            is_first_login = user.last_login_at is None  # chưa đăng nhập lần nào
            user.last_login_at = datetime.now()
            session.commit()

            token = _create_jwt(user.id, user.email)
            # Tính trial_end_date từ created_at (không cần cột DB mới)
            _trial_end = None
            if user.tier == 'basic_trial' and user.created_at:
                from datetime import timedelta as _td
                _trial_end = (user.created_at + _td(days=15)).isoformat()
            return jsonify({
                'success': True,
                'token': token,
                'is_first_login': is_first_login,
                'user': {
                    'id':              user.id,
                    'email':           user.email,
                    'full_name':       user.full_name,
                    'trial_end_date':  _trial_end,
                    'tier':            user.tier,
                    'is_push_enabled': user.is_push_enabled,
                }
            })
        finally:
            session.close()


    @app.route('/api/auth/me', methods=['GET'])
    @require_vip_auth
    def vip_me():
        """GET /api/auth/me  — Bearer token required"""
        session = Session()
        try:
            user = session.query(VIPUser).filter_by(id=g.user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            return jsonify({
                'success': True,
                'user': {
                    'id':              user.id,
                    'email':           user.email,
                    'full_name':       user.full_name,
                    'tier':            user.tier,
                    'is_push_enabled': user.is_push_enabled,
                }
            })
        finally:
            session.close()


    @app.route('/api/vip/notification/toggle', methods=['POST'])
    @require_vip_auth
    def vip_toggle_notification():
        """POST /api/vip/notification/toggle — User tự bật/tắt nhận Telegram"""
        session = Session()
        try:
            user = session.query(VIPUser).filter_by(id=g.user_id).first()
            if not user:
                return jsonify({'error': 'User not found'}), 404
            if not user.telegram_chat_id:
                return jsonify({'error': 'Bạn chưa kết nối Telegram. Nhắn /start vào @aiadvisorvn_bot rồi báo admin.'}), 400
            user.is_push_enabled = not user.is_push_enabled
            session.commit()
            return jsonify({
                'success': True,
                'is_push_enabled': user.is_push_enabled,
                'message': 'Đã bật nhận tín hiệu qua Telegram' if user.is_push_enabled else 'Đã tắt thông báo Telegram',
            })
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()


    @app.route('/api/auth/change-password', methods=['POST'])
    @require_vip_auth
    def vip_change_password():
        """POST /api/auth/change-password  — Bearer token required"""
        data         = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')

        if not old_password or not new_password:
            return jsonify({'error': 'Thiếu mật khẩu cũ hoặc mới'}), 400
        if len(new_password) < 6:
            return jsonify({'error': 'Mật khẩu mới phải ít nhất 6 ký tự'}), 400

        session = Session()
        try:
            user = session.query(VIPUser).filter_by(id=g.user_id).first()
            if not user or not _check_password(old_password, user.password_hash):
                return jsonify({'error': 'Mật khẩu cũ không đúng'}), 401

            user.password_hash = _hash_password(new_password)
            session.commit()
            return jsonify({'success': True, 'message': 'Đổi mật khẩu thành công'})
        finally:
            session.close()

    # ─────────────────────────────────────────────
    # ADMIN ROUTES — protected by X-Admin-Key header
    # ─────────────────────────────────────────────

    @app.route('/api/admin/users', methods=['GET'])
    @require_admin
    def admin_list_users():
        """GET /api/admin/users  — Danh sách VIP users + trạng thái push"""
        session = Session()
        try:
            users = session.query(VIPUser).order_by(
                VIPUser.created_at.desc()
            ).all()

            # Đếm số thiết bị subscribe per user
            sub_counts = {}
            try:
                rows = session.execute(text(
                    "SELECT user_id, COUNT(*) as cnt "
                    "FROM push_subscriptions WHERE is_active = TRUE "
                    "GROUP BY user_id"
                )).fetchall()
                for row in rows:
                    sub_counts[str(row[0])] = row[1]
            except Exception:
                pass  # Bảng chưa tạo — bỏ qua

            result = []
            for u in users:
                result.append({
                    'id':              u.id,
                    'email':           u.email,
                    'full_name':       u.full_name,
                    'phone':           u.phone,
                    'tier':            u.tier,
                    'is_push_enabled': u.is_push_enabled,
                    'is_active':       u.is_active,
                    'notes':           u.notes,
                    'push_devices':    sub_counts.get(str(u.email), sub_counts.get(str(u.id), 0)),
                    'telegram_chat_id': u.telegram_chat_id or '',
                    'created_at':      u.created_at.isoformat() if u.created_at else None,
                    'last_login_at':   u.last_login_at.isoformat() if u.last_login_at else None,
                })

            return jsonify({'success': True, 'users': result, 'total': len(result)})
        finally:
            session.close()


    @app.route('/api/admin/users/create', methods=['POST'])
    @require_admin
    def admin_create_user():
        """
        POST /api/admin/users/create
        Body: { email, full_name, phone, tier, notes, password? }
        
        Returns credentials để gửi cho khách.
        """
        data      = request.get_json() or {}
        email     = data.get('email', '').lower().strip()
        full_name = data.get('full_name', '')
        phone     = data.get('phone', '')
        tier      = data.get('tier', 'vip')
        notes     = data.get('notes', '')
        custom_pw = data.get('password', '').strip()

        if not email:
            return jsonify({'error': 'Email là bắt buộc'}), 400

        session = Session()
        try:
            if session.query(VIPUser).filter_by(email=email).first():
                return jsonify({'error': f'Email {email} đã tồn tại'}), 409

            temp_password = custom_pw if custom_pw else _generate_temp_password()

            user = VIPUser(
                email=email,
                password_hash=_hash_password(temp_password),
                full_name=full_name,
                phone=phone,
                tier=tier,
                notes=notes,
                is_push_enabled=False,  # Admin bật sau khi khách cài app
            )
            session.add(user)
            session.commit()

            return jsonify({
                'success': True,
                'message': 'Tạo tài khoản VIP thành công',
                'user': {
                    'id':       user.id,
                    'email':    email,
                    'full_name': full_name,
                    'tier':     tier,
                },
                # Thông tin gửi cho khách
                'credentials': {
                    'email':     email,
                    'password':  temp_password,
                    'login_url': 'https://ai-advisor.vn',
                }
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()


    @app.route('/api/admin/users/<int:user_id>/toggle-push', methods=['POST'])
    @require_admin
    def admin_toggle_push(user_id):
        """
        POST /api/admin/users/<id>/toggle-push
        Bật hoặc tắt push notification cho user cụ thể.
        """
        session = Session()
        try:
            user = session.query(VIPUser).filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User không tồn tại'}), 404

            user.is_push_enabled = not user.is_push_enabled
            session.commit()

            status = 'ĐÃ BẬT 🔔' if user.is_push_enabled else 'ĐÃ TẮT 🔕'
            return jsonify({
                'success':         True,
                'user_id':         user_id,
                'email':           user.email,
                'is_push_enabled': user.is_push_enabled,
                'message':         f'Push notification {status} cho {user.email}'
            })
        finally:
            session.close()


    @app.route('/api/admin/users/<int:user_id>', methods=['PATCH'])
    @require_admin
    def admin_update_user(user_id):
        """
        PATCH /api/admin/users/<id>
        Cập nhật: notes, tier, is_active, full_name, phone, new_password
        """
        data    = request.get_json() or {}
        session = Session()
        try:
            user = session.query(VIPUser).filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User không tồn tại'}), 404

            for field in ('notes', 'tier', 'full_name', 'phone', 'telegram_chat_id'):
                if field in data:
                    setattr(user, field, data[field])
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])
            if 'new_password' in data and data['new_password']:
                user.password_hash = _hash_password(data['new_password'])

            session.commit()
            return jsonify({'success': True, 'message': 'Cập nhật thành công'})
        finally:
            session.close()


    @app.route('/api/admin/push/broadcast', methods=['POST'])
    @require_admin
    def admin_broadcast_push():
        """
        POST /api/admin/push/broadcast
        Body: { title, body, url? }
        Admin tự tay push thông báo đến tất cả VIP users đang bật push.
        """
        data  = request.get_json() or {}
        title = data.get('title', '📊 AI Advisor')
        body  = data.get('body', 'Thông báo từ AI Advisor')
        url   = data.get('url', '/dashboard')

        payload = {
            'type':  'admin_broadcast',
            'title': title,
            'body':  body,
            'url':   url,
        }

        session = Session()
        try:
            stats = push_vip_users(session, payload)
            return jsonify({'success': True, 'stats': stats})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()


    @app.route('/api/admin/push/test/<int:user_id>', methods=['POST'])
    @require_admin
    def admin_test_push_user(user_id):
        """
        POST /api/admin/push/test/<user_id>
        Gửi test notification đến 1 user cụ thể để kiểm tra.
        """
        session = Session()
        try:
            user = session.query(VIPUser).filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User không tồn tại'}), 404

            # Tạm thời enable push để test, rồi restore
            original = user.is_push_enabled
            user.is_push_enabled = True
            session.commit()

            payload = {
                'type':  'test',
                'title': '🧪 Test Notification',
                'body':  f'Xin chào {user.full_name or user.email}! Push notification đang hoạt động.',
                'url':   '/dashboard',
            }
            stats = push_vip_users(session, payload)

            # Restore
            user.is_push_enabled = original
            session.commit()

            return jsonify({'success': True, 'stats': stats, 'user': user.email})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()


    @app.route('/api/admin/telegram/test/<int:user_id>', methods=['POST'])
    @require_admin
    def admin_test_telegram(user_id):
        """
        POST /api/admin/telegram/test/<user_id>
        Gửi test Telegram message đến 1 user cụ thể.
        """
        session = Session()
        try:
            user = session.query(VIPUser).filter_by(id=user_id).first()
            if not user:
                return jsonify({'error': 'User không tồn tại'}), 404
            if not user.telegram_chat_id:
                return jsonify({'error': 'User chưa có Telegram chat_id'}), 400

            import requests as _req
            msg = (
                f"🧪 <b>Test Notification</b>\n\n"
                f"Xin chào <b>{user.full_name or user.email}</b>!\n\n"
                f"✅ Telegram notification đang hoạt động.\n"
                f"Bạn sẽ nhận tín hiệu VIP tại đây.\n\n"
                f"🌐 <a href='https://ai-advisor.vn'>ai-advisor.vn</a>"
            )
            resp = _req.post(
                f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                json={'chat_id': user.telegram_chat_id, 'text': msg,
                      'parse_mode': 'HTML', 'disable_web_page_preview': True},
                timeout=10,
            )
            ok = resp.status_code == 200
            return jsonify({
                'success': ok,
                'user': user.email,
                'telegram_chat_id': user.telegram_chat_id,
                'telegram_response': resp.json(),
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()


    @app.route('/api/admin/telegram/broadcast', methods=['POST'])
    @require_admin
    def admin_broadcast_telegram():
        """
        POST /api/admin/telegram/broadcast
        Multipart form: title (opt), body (required), file (opt)
        Gửi tin nhắn Telegram đến tất cả VIP users có chat_id.
        Hỗ trợ text, ảnh, file đính kèm (PDF, Excel...).
        """
        import requests as _req

        title = request.form.get('title', '').strip()
        body  = request.form.get('body', '').strip()
        if not body:
            return jsonify({'error': 'Nội dung không được trống'}), 400

        # Build message text
        msg = ''
        if title:
            msg += f'<b>{title}</b>\n\n'
        msg += body
        msg += '\n\n🌐 <a href="https://ai-advisor.vn">ai-advisor.vn</a>'

        # Get file if attached
        file_obj = request.files.get('file')
        file_bytes = file_obj.read() if file_obj else None
        file_name  = file_obj.filename if file_obj else None
        file_mime  = file_obj.content_type if file_obj else None

        session = Session()
        try:
            users = session.query(VIPUser).filter(
                VIPUser.is_active == True,
                VIPUser.telegram_chat_id != None,
                VIPUser.telegram_chat_id != '',
            ).all()

            total_active = session.query(VIPUser).filter(VIPUser.is_active == True).count()
            stats = {'sent': 0, 'failed': 0, 'skipped': total_active - len(users)}

            for user in users:
                try:
                    if file_bytes and file_mime and file_mime.startswith('image/'):
                        # Send photo
                        resp = _req.post(
                            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto',
                            data={'chat_id': user.telegram_chat_id, 'caption': msg,
                                  'parse_mode': 'HTML'},
                            files={'photo': (file_name, file_bytes, file_mime)},
                            timeout=30,
                        )
                    elif file_bytes:
                        # Send document (PDF, Excel, etc.)
                        resp = _req.post(
                            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument',
                            data={'chat_id': user.telegram_chat_id, 'caption': msg,
                                  'parse_mode': 'HTML'},
                            files={'document': (file_name, file_bytes, file_mime or 'application/octet-stream')},
                            timeout=30,
                        )
                    else:
                        # Text only
                        resp = _req.post(
                            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                            json={'chat_id': user.telegram_chat_id, 'text': msg,
                                  'parse_mode': 'HTML', 'disable_web_page_preview': False},
                            timeout=15,
                        )

                    if resp.status_code == 200:
                        stats['sent'] += 1
                        logger.info(f'[Telegram broadcast] Sent to {user.email}')
                    else:
                        stats['failed'] += 1
                        logger.error(f'[Telegram broadcast] Failed {user.email}: {resp.text}')

                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f'[Telegram broadcast] Error {user.email}: {e}')

            return jsonify({'success': True, 'stats': stats})

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            session.close()


    print("✅ VIP Auth + Admin routes registered:")
    print("   POST /api/auth/login")
    print("   GET  /api/auth/me")
    print("   POST /api/auth/change-password")
    print("   GET  /api/admin/users              [ADMIN]")
    print("   POST /api/admin/users/create       [ADMIN]")
    print("   POST /api/admin/users/<id>/toggle-push [ADMIN]")
    print("   PATCH /api/admin/users/<id>        [ADMIN]")
    print("   POST /api/admin/push/broadcast     [ADMIN]")
    print("   POST /api/admin/push/test/<id>     [ADMIN]")
