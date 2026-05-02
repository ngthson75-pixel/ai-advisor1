#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI ADVISOR - CAMPAIGN REGISTRATION API v2 (Simplified)
=======================================================
File: campaign_api.py
Campaign: 30 Beta Users · 25/03 – 10/4/2026

Flow (còn suất):
  1. User điền form → auto-activate ngay
  2. Tài khoản tạo tự động (tier='free', hết hạn 10/4/2026)
  3. User nhận email có mật khẩu tạm → đăng nhập ngay
  4. Sơn nhận Telegram "User mới #{n}/30"

Flow (đủ 30 người):
  1. User điền form → status='waiting'
  2. User nhận email "Đang chờ suất"
  3. Sơn nhận Telegram "Waiting list #{n}"
  4. Khi Sơn mở thêm → POST /api/campaign/admin/open-slots
     → Tự động activate + gửi email từng người trong waiting list

Admin endpoints (header: X-Admin-Key):
  GET  /api/campaign/admin/list         — xem toàn bộ
  POST /api/campaign/admin/open-slots   — mở thêm suất từ waiting list
  Body: { "count": 5 }

Điều chỉnh số đếm hiển thị:
  Set env var CAMPAIGN_SLOT_OFFSET=N trên Render → redeploy
  (VD: CAMPAIGN_SLOT_OFFSET=5 → hiển thị thêm 5 suất đã dùng)

Tích hợp vào backend_api.py:
  from campaign_api import init_campaign_routes
  init_campaign_routes(app, engine, Session)   # sau khi có engine + Session

Env vars cần thiết:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
  ADMIN_EMAIL, FRONTEND_URL, BACKEND_URL, ADMIN_SECRET
  CAMPAIGN_SLOT_OFFSET (int, default 0)
"""

import os
import string
import random
import hashlib
import hmac
import json
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

import requests as req_lib
import threading
from flask import request, jsonify
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# ── CONFIG ──────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN     = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
ADMIN_EMAIL   = os.getenv('ADMIN_EMAIL', 'ngthson75@gmail.com')
FRONTEND_URL  = os.getenv('FRONTEND_URL', 'https://ai-advisor.vn')
ADMIN_SECRET  = os.getenv('ADMIN_SECRET', 'ai-advisor-admin-2026')

CAMPAIGN_LIMIT = 100
CAMPAIGN_END   = datetime(2026, 5, 31, 23, 59, 59)
TRIAL_DAYS     = 15   # Số ngày dùng thử Basic Trial
SLOT_OFFSET    = int(os.getenv('CAMPAIGN_SLOT_OFFSET', '0'))

# Gmail API config (thay thế SMTP)
GMAIL_SENDER       = os.getenv('SMTP_USER', 'aiadvisorhotline@gmail.com')
GMAIL_CLIENT_ID     = os.getenv('GMAIL_CLIENT_ID', '')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET', '')
GMAIL_REFRESH_TOKEN = os.getenv('GMAIL_REFRESH_TOKEN', '')


# ── DB MODEL ────────────────────────────────────────────────
CampaignBase = declarative_base()

class CampaignRegistration(CampaignBase):
    __tablename__ = 'campaign_registrations'
    id           = Column(Integer, primary_key=True)
    full_name    = Column(String(255), nullable=False)
    email        = Column(String(255), unique=True, nullable=False)
    phone        = Column(String(20),  nullable=False)
    experience   = Column(String(50))
    source       = Column(String(50))
    status       = Column(String(20), default='activated')  # activated | waiting
    created_at   = Column(DateTime, default=datetime.now)
    activated_at = Column(DateTime)


# ── HELPERS ─────────────────────────────────────────────────
def _require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Admin-Key', '')
        if not hmac.compare_digest(key, ADMIN_SECRET):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def _gen_temp_password(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def _send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_CHAT_ID:
        return
    try:
        req_lib.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={'chat_id': TELEGRAM_ADMIN_CHAT_ID, 'text': message,
                  'parse_mode': 'HTML', 'disable_web_page_preview': True},
            timeout=10
        )
    except Exception as e:
        logger.error(f'[Telegram] {e}')


def _send_email(to: str, subject: str, html: str):
    """Gửi email qua Gmail API (OAuth2) — không bị chặn bởi Render free tier."""
    if not GMAIL_CLIENT_ID or not GMAIL_CLIENT_SECRET or not GMAIL_REFRESH_TOKEN:
        logger.warning('[Email] Gmail API chưa config — bỏ qua')
        return False
    try:
        import base64
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import urllib.request
        import urllib.parse

        # 1. Lấy access token từ refresh token
        token_data = urllib.parse.urlencode({
            'client_id':     GMAIL_CLIENT_ID,
            'client_secret': GMAIL_CLIENT_SECRET,
            'refresh_token': GMAIL_REFRESH_TOKEN,
            'grant_type':    'refresh_token',
        }).encode()
        req = urllib.request.Request(
            'https://oauth2.googleapis.com/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_resp = json.loads(resp.read())
        access_token = token_resp.get('access_token')
        if not access_token:
            logger.error(f'[Email] Không lấy được access token: {token_resp}')
            return False

        # 2. Build email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'AI Advisor <{GMAIL_SENDER}>'
        msg['To']      = to
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        # 3. Gửi qua Gmail API
        send_data = json.dumps({'raw': raw}).encode()
        send_req = urllib.request.Request(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            data=send_data,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }
        )
        with urllib.request.urlopen(send_req, timeout=15) as resp:
            result = json.loads(resp.read())
        logger.info(f'[Email] Gửi thành công → {to} (id: {result.get("id")})')
        return True

    except Exception as e:
        logger.error(f'[Email] {e}')
        return False


def _email_activated(reg, temp_password: str):
    """Email gửi user ngay sau khi activate — có mật khẩu tạm."""
    login_url = f"{FRONTEND_URL}/login"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;background:#f7f5f0;padding:32px">
      <div style="background:#0d0f12;padding:24px;border-top:3px solid #c9a84c;border-radius:4px 4px 0 0;text-align:center">
        <div style="font-size:32px;margin-bottom:8px">🎉</div>
        <h2 style="margin:0;color:#c9a84c;font-size:20px">Chào mừng {reg.full_name}!</h2>
        <p style="margin:6px 0 0;color:#888;font-size:13px">Tài khoản Beta AI Advisor đã sẵn sàng</p>
      </div>
      <div style="background:#fff;padding:28px;border:1px solid #e0dbd0;border-top:none">
        <p style="font-size:14px;color:#333;line-height:1.7">
          Bạn là một trong <strong>30 nhà đầu tư đầu tiên</strong> trải nghiệm AI Advisor.
          Tài khoản của bạn đã được kích hoạt — <strong>miễn phí đến hết 10/04/2026</strong>.
        </p>
        <div style="background:#f7f5f0;border:1px solid #e0dbd0;border-radius:4px;padding:16px;margin:20px 0">
          <p style="margin:0 0 10px;font-size:11px;color:#888;font-weight:700;text-transform:uppercase;letter-spacing:1px">Thông tin đăng nhập</p>
          <table style="width:100%;font-size:14px;border-collapse:collapse">
            <tr><td style="color:#888;padding:5px 0;width:90px">Email</td><td style="font-weight:700">{reg.email}</td></tr>
            <tr><td style="color:#888;padding:5px 0">Mật khẩu</td><td style="font-weight:800;color:#c9a84c;font-size:17px;letter-spacing:2px">{temp_password}</td></tr>
          </table>
          <p style="margin:10px 0 0;font-size:11px;color:#bbb">⚠️ Hãy đổi mật khẩu sau khi đăng nhập lần đầu</p>
        </div>
        <div style="text-align:center;margin:24px 0 16px">
          <a href="{login_url}" style="background:#c9a84c;color:#0d0f12;padding:14px 32px;text-decoration:none;border-radius:4px;font-weight:800;font-size:14px;display:inline-block">🚀 ĐĂNG NHẬP NGAY</a>
        </div>
        <div style="background:#f7f5f0;border-left:3px solid #c9a84c;padding:12px 16px;font-size:12px;color:#555;line-height:1.8">
          <strong>Bạn có quyền truy cập:</strong><br>
          ✅ Tín hiệu Mua/Bán VN30 blue-chip hàng ngày<br>
          ✅ AI Risk Shield — cảnh báo danh mục real-time<br>
          ✅ AI Discipline Coach — ngăn FOMO & panic selling
        </div>
      </div>
      <p style="font-size:11px;color:#aaa;margin-top:16px;text-align:center">
        AI Advisor là công cụ hỗ trợ quyết định, không phải tư vấn đầu tư. · ai-advisor.vn
      </p>
    </div>"""
    _send_email(reg.email, "🎉 Tài khoản Beta AI Advisor của bạn đã sẵn sàng!", html)


def _email_waiting(reg, position: int):
    """Email gửi user vào waiting list."""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;background:#f7f5f0;padding:32px">
      <div style="background:#0d0f12;padding:24px;border-top:3px solid #c9a84c;border-radius:4px 4px 0 0">
        <h2 style="margin:0;color:#f7f5f0;font-size:18px">AI Advisor — Danh sách chờ</h2>
      </div>
      <div style="background:#fff;padding:28px;border:1px solid #e0dbd0;border-top:none">
        <p style="font-size:14px;color:#333;line-height:1.7">
          Xin chào <strong>{reg.full_name}</strong>,<br><br>
          Chương trình Basic Trial đã <strong>đủ 100 suất</strong>. Bạn đang ở vị trí
          <strong style="color:#c9a84c">#{position}</strong> trong danh sách chờ.
          Chúng tôi sẽ thông báo ngay khi có suất mới mở ra.
        </p>
        <p style="font-size:12px;color:#aaa">Cảm ơn bạn đã quan tâm đến AI Advisor!</p>
      </div>
      <p style="font-size:11px;color:#aaa;margin-top:16px;text-align:center">ai-advisor.vn</p>
    </div>"""
    _send_email(reg.email, "Bạn đang trong danh sách chờ — AI Advisor", html)


# ── ROUTES ──────────────────────────────────────────────────
def init_campaign_routes(app, engine, Session):
    CampaignBase.metadata.create_all(engine)
    print("✅ Campaign: campaign_registrations table ready")

    # ── Số suất (public, popup dùng) ────────────────────────
    @app.route('/api/campaign/slots', methods=['GET'])
    def campaign_slots():
        db = Session()
        try:
            activated = db.query(CampaignRegistration).filter_by(status='activated').count()
            waiting   = db.query(CampaignRegistration).filter_by(status='waiting').count()
            display   = min(activated + SLOT_OFFSET, CAMPAIGN_LIMIT)
            return jsonify({
                'total':     CAMPAIGN_LIMIT,
                'taken':     display,
                'remaining': max(0, CAMPAIGN_LIMIT - display),
                'waiting':   waiting,
                'is_full':   display >= CAMPAIGN_LIMIT,
                'is_open':   datetime.now() <= CAMPAIGN_END,
            })
        finally:
            db.close()

    # ── Đăng ký (public) ────────────────────────────────────
    @app.route('/api/campaign/register', methods=['POST'])
    def campaign_register():
        data = request.get_json() or {}
        full_name  = (data.get('fullName') or '').strip()
        email      = (data.get('email')    or '').strip().lower()
        phone      = (data.get('phone')    or '').strip()
        experience = data.get('experience', '')
        source     = data.get('source', '')

        if not full_name or not email or not phone:
            return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        if '@' not in email:
            return jsonify({'success': False, 'error': 'Email không hợp lệ'}), 400
        if datetime.now() > CAMPAIGN_END:
            return jsonify({'success': False, 'error': 'Chương trình đăng ký đã kết thúc. Vui lòng liên hệ 0938127666.'}), 410

        db = Session()
        try:
            existing = db.query(CampaignRegistration).filter_by(email=email).first()
            if existing:
                msg = {
                    'activated': 'Email này đã có tài khoản. Vui lòng đăng nhập tại ai-advisor.vn/login',
                    'waiting':   'Email này đã trong danh sách chờ. Chúng tôi sẽ thông báo khi có suất.',
                }.get(existing.status, 'Email này đã đăng ký rồi.')
                return jsonify({'success': False, 'error': msg}), 409

            activated_count = db.query(CampaignRegistration).filter_by(status='activated').count()
            is_full = (activated_count + SLOT_OFFSET) >= CAMPAIGN_LIMIT

            reg = CampaignRegistration(
                full_name=full_name, email=email, phone=phone,
                experience=experience, source=source,
            )

            if not is_full:
                # ── AUTO ACTIVATE ──────────────────────────────
                temp_pwd      = _gen_temp_password()
                password_hash = hashlib.sha256(temp_pwd.encode()).hexdigest()
                reg.status       = 'activated'
                reg.activated_at = datetime.now()
                db.add(reg)
                db.commit()

                slot_num = activated_count + 1 + SLOT_OFFSET

                # Tạo tài khoản trong vip_users
                try:
                    from vip_auth import VIPUser
                    # Kiểm tra email đã tồn tại trong vip_users chưa
                    existing_vip = db.query(VIPUser).filter_by(email=email).first()
                    if existing_vip:
                        # Đã có rồi → chỉ cập nhật expires + active
                        existing_vip.is_active = True
                        existing_vip.tier = 'basic_trial'
                        existing_vip.notes = f'Basic Trial 15 ngày · Cập nhật {datetime.now().strftime("%d/%m/%Y")} · {source}'
                        logger.info(f'[Campaign] VIPUser đã tồn tại, cập nhật: {email}')
                    else:
                        db.add(VIPUser(
                            email=email, password_hash=password_hash,
                            full_name=full_name, phone=phone,
                            tier='basic_trial', is_active=True,
                                notes=f'Basic Trial 15 ngày · Đăng ký {datetime.now().strftime("%d/%m/%Y")} · {source}',
                        ))
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f'[Campaign] VIPUser error: {e}')

                # Copy data ra khỏi db session trước khi close
                _reg_copy = type('R', (), {
                    'email': reg.email, 'full_name': reg.full_name,
                    'phone': reg.phone,
                })()
                _pwd_copy = temp_pwd
                _slot_copy = slot_num
                db.close()

                def _notify_activated(r, pwd, sn):
                    _email_activated(r, pwd)
                    _send_telegram(
                        f"🆕 <b>User mới #{sn}/{CAMPAIGN_LIMIT}</b>\n"
                        f"👤 {r.full_name}  📧 {r.email}  📱 {r.phone}\n"
                        f"✅ Basic Trial 15 ngày"
                    )
                threading.Thread(target=_notify_activated, args=(_reg_copy, _pwd_copy, _slot_copy), daemon=True).start()
                return jsonify({
                    'success': True, 'status': 'activated', 'slot': slot_num,
                    'message': 'Tài khoản đã được tạo! Kiểm tra email để lấy thông tin đăng nhập.',
                })

            else:
                # ── WAITING LIST ───────────────────────────────
                reg.status = 'waiting'
                db.add(reg)
                db.commit()
                pos = db.query(CampaignRegistration).filter_by(status='waiting').count()
                _reg_copy2 = type('R', (), {
                    'email': reg.email, 'full_name': reg.full_name,
                })()
                _pos_copy = pos
                db.close()

                def _notify_waiting(r, p):
                    _email_waiting(r, p)
                    _send_telegram(
                        f"⏳ <b>Waiting list #{p}</b>\n"
                        f"👤 {r.full_name}  📧 {r.email}"
                    )
                threading.Thread(target=_notify_waiting, args=(_reg_copy2, _pos_copy), daemon=True).start()
                return jsonify({
                    'success': True, 'status': 'waiting', 'position': pos,
                    'message': 'Chương trình đã đủ 30 người. Bạn đã được thêm vào danh sách chờ!',
                })

        except Exception as e:
            db.rollback()
            logger.error(f'[Campaign] register: {e}')
            return jsonify({'success': False, 'error': 'Lỗi server. Vui lòng thử lại.'}), 500
        finally:
            db.close()

    # ── Admin: xem danh sách ────────────────────────────────
    @app.route('/api/campaign/admin/list', methods=['GET'])
    @_require_admin
    def campaign_admin_list():
        db = Session()
        try:
            regs = db.query(CampaignRegistration).order_by(
                CampaignRegistration.created_at.desc()
            ).all()
            activated = sum(1 for r in regs if r.status == 'activated')
            waiting   = sum(1 for r in regs if r.status == 'waiting')
            exp_map = {'new': '<1 năm', 'mid': '1–3 năm', 'senior': '3–5 năm', 'expert': '>5 năm'}
            src_map = {'facebook': 'Facebook', 'zalo': 'Zalo', 'friend': 'Bạn bè', 'search': 'Google', 'other': 'Khác'}
            return jsonify({
                'activated': activated, 'waiting': waiting,
                'display_count': activated + SLOT_OFFSET,
                'offset': SLOT_OFFSET,
                'registrations': [{
                    'id': r.id, 'full_name': r.full_name, 'email': r.email, 'phone': r.phone,
                    'experience': exp_map.get(r.experience, r.experience or '—'),
                    'source': src_map.get(r.source, r.source or '—'),
                    'status': r.status,
                    'created_at': r.created_at.strftime('%d/%m %H:%M') if r.created_at else None,
                } for r in regs]
            })
        finally:
            db.close()

    # ── Admin: mở suất từ waiting list ──────────────────────
    @app.route('/api/campaign/admin/open-slots', methods=['POST'])
    @_require_admin
    def campaign_open_slots():
        data  = request.get_json() or {}
        count = int(data.get('count', 1))
        db    = Session()
        try:
            waiting = db.query(CampaignRegistration).filter_by(status='waiting').order_by(
                CampaignRegistration.created_at.asc()
            ).limit(count).all()
            done = []
            for reg in waiting:
                temp_pwd = _gen_temp_password()
                reg.status = 'activated'
                reg.activated_at = datetime.now()
                try:
                    from vip_auth import VIPUser
                    db.add(VIPUser(
                        email=reg.email,
                        password_hash=hashlib.sha256(temp_pwd.encode()).hexdigest(),
                        full_name=reg.full_name, phone=reg.phone,
                        tier='basic_trial', is_active=True,
                        notes=f'Basic Trial 15 ngày · Mở từ waiting list · {datetime.now().strftime("%d/%m/%Y")}',
                    ))
                except Exception as e:
                    logger.error(f'[Campaign] open-slots VIPUser: {e}')
                _email_activated(reg, temp_pwd)
                done.append(reg.email)
            db.commit()
            if done:
                _send_telegram(
                    f"✅ <b>Mở {len(done)} suất từ waiting list</b>\n"
                    + "\n".join(f"  • {e}" for e in done)
                )
            return jsonify({'success': True, 'activated': done, 'count': len(done)})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            db.close()


    # ── Admin: hủy 1 user → tự động fill waiting list ──────
    @app.route('/api/campaign/admin/deactivate', methods=['POST'])
    @_require_admin
    def campaign_deactivate():
        """
        Deactivate 1 user (hủy suất) → tự động kéo người đầu
        trong waiting list vào thay (auto-fill).
        Body: { "email": "user@email.com", "reason": "tùy chọn" }
        """
        data   = request.get_json() or {}
        email  = (data.get('email') or '').strip().lower()
        reason = data.get('reason', 'Admin hủy')
        if not email:
            return jsonify({'success': False, 'error': 'Thiếu email'}), 400

        db = Session()
        try:
            # 1. Deactivate user
            reg = db.query(CampaignRegistration).filter_by(email=email, status='activated').first()
            if not reg:
                return jsonify({'success': False, 'error': f'Không tìm thấy user activated: {email}'}), 404

            reg.status = 'cancelled'
            db.commit()

            try:
                from vip_auth import VIPUser
                vip = db.query(VIPUser).filter_by(email=email).first()
                if vip:
                    vip.is_active = False
                    vip.notes = (vip.notes or '') + f' | Hủy: {reason}'
                    db.commit()
            except Exception as e:
                logger.error(f'[Campaign] deactivate VIPUser: {e}')

            _send_telegram(
                f"🚫 <b>Hủy suất:</b> {reg.full_name} ({email})\nLý do: {reason}"
            )

            # 2. Auto-fill: kéo người đầu waiting list vào
            next_w = db.query(CampaignRegistration).filter_by(status='waiting').order_by(
                CampaignRegistration.created_at.asc()
            ).first()

            if next_w:
                temp_pwd = _gen_temp_password()
                next_w.status = 'activated'
                next_w.activated_at = datetime.now()
                try:
                    from vip_auth import VIPUser
                    db.add(VIPUser(
                        email=next_w.email,
                        password_hash=hashlib.sha256(temp_pwd.encode()).hexdigest(),
                        full_name=next_w.full_name, phone=next_w.phone,
                        tier='basic_trial', is_active=True,
                        notes=f'Basic Trial 15 ngày · Auto-fill · {__import__("datetime").datetime.now().strftime("%d/%m/%Y")}',
                    ))
                except Exception as e:
                    logger.error(f'[Campaign] auto-fill VIPUser: {e}')
                db.commit()
                _email_activated(next_w, temp_pwd)
                _send_telegram(
                    f"🔄 <b>Auto-fill:</b> {next_w.full_name} ({next_w.email})\nVừa được kéo từ waiting list vào thay ✅"
                )
                return jsonify({
                    'success': True, 'deactivated': email,
                    'auto_filled': next_w.email,
                    'message': f'Đã hủy {email} và tự động kích hoạt {next_w.email} từ waiting list.',
                })
            else:
                return jsonify({
                    'success': True, 'deactivated': email, 'auto_filled': None,
                    'message': f'Đã hủy {email}. Waiting list trống — suất sẽ mở cho đăng ký mới.',
                })

        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            db.close()


    # ── Admin: reset password user bất kỳ ──────────────────
    @app.route('/api/campaign/admin/reset-password', methods=['POST'])
    @_require_admin
    def campaign_reset_password():
        """
        Reset password cho user bất kỳ.
        Body: { "email": "user@email.com", "new_password": "NewPass123" }
        Nếu không truyền new_password → tự generate 10 ký tự random.
        """
        data     = request.get_json() or {}
        email    = (data.get('email') or '').strip().lower()
        new_pwd  = data.get('new_password') or _gen_temp_password()

        if not email:
            return jsonify({'success': False, 'error': 'Thiếu email'}), 400

        db = Session()
        try:
            from vip_auth import VIPUser
            user = db.query(VIPUser).filter_by(email=email).first()
            if not user:
                return jsonify({'success': False, 'error': f'Không tìm thấy user: {email}'}), 404

            user.password_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
            user.last_login_at = None  # force đổi mật khẩu lần sau login
            db.commit()

            # Gửi email thông báo
            def _notify():
                _email_activated(type('R', (), {
                    'email': email, 'full_name': user.full_name or email,
                })(), new_pwd)
            threading.Thread(target=_notify, daemon=True).start()

            _send_telegram(
                f"🔑 <b>Reset password:</b> {email}\n"
                f"Mật khẩu mới: <code>{new_pwd}</code>"
            )

            return jsonify({
                'success': True,
                'email': email,
                'new_password': new_pwd,
                'message': f'Đã reset password cho {email}. Email thông báo đã gửi.',
            })
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            db.close()

    print("✅ Campaign routes registered: /api/campaign/*")
