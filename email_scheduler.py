#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMAIL SCHEDULER — AI-Advisor Habit Loop
v1.0

4 loại email tự động tạo thói quen user quay lại app:
  Email 1: Bản tin sáng   — 8:00 AM thứ 2-6 (anchor habit)
  Email 2: Signal Alert    — khi có signal Grade A/S cho watchlist
  Email 3: Portfolio Alert — khi SL gần hit hoặc regime đổi
  Email 4: IIS Weekly      — thứ Hai 7:30 AM (feedback loop)

Chạy qua GitHub Actions hoặc cron job trên Render.

Env vars cần thiết (đã có sẵn từ campaign_api.py):
  GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
  DATABASE_URL (hoặc DATABASE_URL_STAGING)
  FRONTEND_URL  (default: https://ai-advisor.vn)

Chạy thủ công để test:
  python3 email_scheduler.py --type morning
  python3 email_scheduler.py --type signal --ticker HPG
  python3 email_scheduler.py --type portfolio
  python3 email_scheduler.py --type weekly
  python3 email_scheduler.py --dry-run
"""

import os
import sys
import json
import base64
import logging
import argparse
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ── Config ───────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

GMAIL_SENDER        = os.getenv('SMTP_USER', 'aiadvisorhotline@gmail.com')
GMAIL_CLIENT_ID     = os.getenv('GMAIL_CLIENT_ID', '')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET', '')
GMAIL_REFRESH_TOKEN = os.getenv('GMAIL_REFRESH_TOKEN', '')
FRONTEND_URL        = os.getenv('FRONTEND_URL', 'https://ai-advisor.vn')

# Kết nối DB — tái sử dụng DATABASE_URL từ backend
_DB_URL = os.getenv('DATABASE_URL', 'sqlite:///signals.db')
if _DB_URL.startswith('postgresql://'):
    _DB_URL = _DB_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

engine  = create_engine(_DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

# ── Gmail send (tái sử dụng logic từ campaign_api.py) ───────────────────

def _get_access_token():
    """Lấy Gmail access token từ refresh token."""
    if not all([GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN]):
        log.warning('[Gmail] Chưa config OAuth2 credentials')
        return None
    try:
        data = urllib.parse.urlencode({
            'client_id':     GMAIL_CLIENT_ID,
            'client_secret': GMAIL_CLIENT_SECRET,
            'refresh_token': GMAIL_REFRESH_TOKEN,
            'grant_type':    'refresh_token',
        }).encode()
        req = urllib.request.Request(
            'https://oauth2.googleapis.com/token', data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            token = json.loads(r.read()).get('access_token')
        return token
    except Exception as e:
        log.error(f'[Gmail] Token error: {e}')
        return None


def send_email(to: str, subject: str, html: str, dry_run: bool = False) -> bool:
    """Gửi email qua Gmail API. dry_run=True chỉ log, không gửi."""
    if dry_run:
        log.info(f'[DRY-RUN] → {to} | {subject}')
        return True

    token = _get_access_token()
    if not token:
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'AI Advisor <{GMAIL_SENDER}>'
        msg['To']      = to
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        send_req = urllib.request.Request(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            data=json.dumps({'raw': raw}).encode(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        )
        with urllib.request.urlopen(send_req, timeout=15) as r:
            result = json.loads(r.read())
        log.info(f'[Gmail] Sent → {to} (id:{result.get("id")})')
        return True
    except Exception as e:
        log.error(f'[Gmail] Send error → {to}: {e}')
        return False


# ── Data helpers ──────────────────────────────────────────────────────────

def get_active_users(session):
    """Lấy danh sách user active có email (từ campaign_registrations)."""
    try:
        rows = session.execute(text(
            "SELECT email, full_name FROM campaign_registrations WHERE status = 'activated'"
        )).fetchall()
        return [{'email': r[0], 'name': r[1]} for r in rows]
    except Exception as e:
        log.warning(f'[DB] get_active_users: {e}')
        return []


def get_iis_profile(session, email: str) -> dict:
    """Lấy IIS profile mới nhất của user theo email."""
    try:
        row = session.execute(text(
            """SELECT total, level_name, method, kl_score, kt_score
               FROM iis_results
               WHERE user_id = :uid
               ORDER BY created_at DESC LIMIT 1"""
        ), {'uid': email}).fetchone()
        if row:
            return {
                'total': row[0], 'level': row[1], 'method': row[2],
                'kl': row[3], 'kt': row[4], 'has_iis': True
            }
    except Exception:
        pass
    return {'has_iis': False, 'method': 'bat_song'}  # default Bắt Sóng AI


def get_market_regime(session) -> dict:
    """Lấy Market Regime mới nhất."""
    try:
        row = session.execute(text(
            "SELECT market_mode, mode_label, risk_score, allocation FROM market_risk ORDER BY date DESC LIMIT 1"
        )).fetchone()
        if row:
            return {
                'mode': row[0], 'label': row[1] or row[0],
                'risk': row[2], 'allocation': row[3],
            }
    except Exception as e:
        log.warning(f'[DB] get_market_regime: {e}')
    return {'mode': 'NEUTRAL', 'label': 'Thận Trọng', 'risk': 50, 'allocation': 50}


def get_top_signals(session, method="bat_song", limit=3):
    """Lấy top signals theo phương pháp của user."""
    # Mapping method → strategies trong DB
    strategy_map = {
        'luot_song':  ['PULLBACK', 'EMA_CROSS', 'BREAKOUT'],
        'bat_song':   ['TREND_FOLLOWING', 'EARNINGS_MOMENTUM', 'FA_HYBRID',
                       'PULLBACK_PLUS', 'EMA_CROSS_PLUS'],
        'tich_san':   ['VALUE', 'GROWTH'],
        'hybrid_sm':  ['PULLBACK', 'EMA_CROSS', 'BREAKOUT', 'TREND_FOLLOWING'],
        'hybrid_ml':  ['TREND_FOLLOWING', 'FA_HYBRID', 'VALUE', 'GROWTH'],
    }
    strategies = strategy_map.get(method, strategy_map['bat_song'])
    placeholders = ','.join([f"'{s}'" for s in strategies])

    try:
        rows = session.execute(text(
            f"""SELECT ticker, strategy, entry_price, stop_loss, take_profit,
                       risk_reward, strength
                FROM signals
                WHERE action = 'BUY'
                  AND strategy IN ({placeholders})
                ORDER BY strength DESC, created_at DESC
                LIMIT {limit}"""
        )).fetchall()
        return [{
            'ticker': r[0], 'strategy': r[1],
            'entry':  round(r[2]/100)*100 if r[2] else 0,
            'sl':     round(r[3]/100)*100 if r[3] else 0,
            'tp':     round(r[4]/100)*100 if r[4] else 0,
            'rr':     round(r[5], 1) if r[5] else 0,
            'grade':  'S' if (r[6] or 0) >= 90 else 'A' if (r[6] or 0) >= 75 else 'B',
        } for r in rows]
    except Exception as e:
        log.warning(f'[DB] get_top_signals: {e}')
        return []


def get_portfolio_alerts(session, email):
    """
    Tìm các vị thế đang lỗ và gần hit stop loss.
    Chỉ cảnh báo khi lỗ > 70% khoảng cách đến SL.
    """
    try:
        rows = session.execute(text(
            """SELECT p.ticker, p.avg_price, p.quantity,
                      s.stop_loss, e.price as current_price
               FROM portfolios p
               JOIN eod_prices e ON e.ticker = p.ticker
               LEFT JOIN signals s ON s.ticker = p.ticker AND s.action = 'BUY'
               WHERE p.user_id = :uid"""
        ), {'uid': email}).fetchall()

        alerts = []
        for r in rows:
            ticker, avg, qty, sl, cur = r
            if not all([avg, cur, sl]):
                continue
            loss_pct    = (cur - avg) / avg * 100
            sl_pct      = (sl - avg) / avg * 100  # negative
            if sl_pct == 0:
                continue
            proximity   = (cur - sl) / (avg - sl)  # 0=at SL, 1=at entry
            if proximity < 0.25:  # gần SL hơn 75%
                alerts.append({
                    'ticker':      ticker,
                    'avg_price':   avg,
                    'current':     cur,
                    'stop_loss':   sl,
                    'loss_pct':    round(loss_pct, 1),
                    'sl_gap_pct':  round((cur - sl) / cur * 100, 1),
                })
        return alerts
    except Exception as e:
        log.warning(f'[DB] portfolio_alerts: {e}')
        return []


def get_iis_weekly_stats(session, email: str) -> dict:
    """Stats cho Email 4 — IIS Weekly Report."""
    # IIS score hiện tại
    profile = get_iis_profile(session, email)

    # Lấy IIS score tuần trước (nếu có)
    prev_total = profile.get('total', 0)
    current_total = profile.get('total', 0)
    delta = 0  # sẽ cập nhật khi có behavior-based IIS update

    # Win/Loss từ portfolio (tháng này)
    wins = losses = 0
    try:
        rows = session.execute(text(
            """SELECT exit_reason FROM signals
               WHERE user_id = :uid AND exit_date >= :start"""
        ), {'uid': email, 'start': (datetime.now() - timedelta(days=30)).date()}).fetchall()
        for r in rows:
            if r[0] and 'TP' in str(r[0]):
                wins += 1
            elif r[0] and 'SL' in str(r[0]):
                losses += 1
    except Exception:
        pass

    return {
        'iis_total':  current_total,
        'iis_delta':  delta,
        'iis_level':  profile.get('level', 'Chưa test'),
        'kl_score':   profile.get('kl', 0),
        'kt_score':   profile.get('kt', 0),
        'wins':       wins,
        'losses':     losses,
        'win_rate':   round(wins / (wins + losses) * 100) if (wins + losses) > 0 else 0,
    }


# ── HTML Templates ────────────────────────────────────────────────────────
# Inline CSS — Gmail không hỗ trợ external CSS

_BASE_STYLE = """
font-family:Arial,Helvetica,sans-serif;
max-width:520px;margin:0 auto;background:#f4f2ee;padding:24px 16px
"""
_HEADER_STYLE = """
background:#1B3A6B;padding:20px 24px;border-radius:8px 8px 0 0;
border-top:3px solid #C8780F;text-align:center
"""
_BODY_STYLE  = "background:#fff;padding:24px;border:1px solid #e0dbd0;border-top:none;border-radius:0 0 8px 8px"
_FOOTER_STYLE = "margin-top:16px;text-align:center;font-size:11px;color:#999;line-height:1.6"

def _signal_row(s: dict) -> str:
    grade_color = {'S': '#1A6B3C', 'A': '#2355A0', 'B': '#5A5A5A'}
    sl_pct  = round((s['sl']  - s['entry']) / s['entry'] * 100, 1) if s['entry'] else 0
    tp_pct  = round((s['tp']  - s['entry']) / s['entry'] * 100, 1) if s['entry'] else 0
    return f"""
    <div style="background:#f7f9fd;border-left:3px solid {grade_color.get(s['grade'],'#888')};
                padding:10px 12px;margin:8px 0;border-radius:0 6px 6px 0">
      <div style="font-size:14px;font-weight:bold;color:#1B3A6B">{s['ticker']}
        <span style="font-size:11px;font-weight:normal;color:#666;margin-left:6px">{s['strategy']}</span>
        <span style="float:right;font-size:11px;font-weight:bold;
                     color:{grade_color.get(s['grade'],'#888')};
                     background:#fff;padding:2px 7px;border-radius:4px;
                     border:1px solid {grade_color.get(s['grade'],'#ccc')}">
          Grade {s['grade']}
        </span>
      </div>
      <div style="font-size:12px;color:#444;margin-top:5px">
        Entry <b>{s['entry']:,.0f}</b> &nbsp;|&nbsp;
        SL <b style="color:#A0281E">{s['sl']:,.0f} ({sl_pct}%)</b> &nbsp;|&nbsp;
        TP <b style="color:#1A6B3C">{s['tp']:,.0f} (+{tp_pct}%)</b> &nbsp;|&nbsp;
        RR <b>1:{s['rr']}</b>
      </div>
    </div>"""


def build_morning_email(user: dict, regime: dict, signals: list, iis_profile: dict) -> tuple[str, str]:
    """Trả về (subject, html)."""
    today   = datetime.now().strftime('%d/%m/%Y, %A')
    day_vn  = ['Thứ Hai','Thứ Ba','Thứ Tư','Thứ Năm','Thứ Sáu'][datetime.now().weekday()]
    today   = f"{day_vn} {datetime.now().strftime('%d/%m/%Y')}"

    regime_emoji = {'BULL': '🟢', 'NEUTRAL': '🟡', 'BEAR': '🔴'}.get(regime['mode'], '⚪')
    regime_label = regime.get('label', regime['mode'])
    method_name  = {'luot_song':'Lướt Sóng AI','bat_song':'Bắt Sóng AI',
                    'tich_san':'Tích Sản AI','hybrid_sm':'Hybrid','hybrid_ml':'Hybrid'
                   }.get(iis_profile.get('method','bat_song'), 'Bắt Sóng AI')

    signal_html = ''.join([_signal_row(s) for s in signals]) if signals else \
        '<p style="color:#888;font-size:13px;text-align:center">Chưa có signal mới hôm nay — thị trường đang chờ setup tốt hơn.</p>'

    subject = f'[AI-Advisor] {today} — {regime_emoji} {regime_label} · {len(signals)} signal mới'

    html = f"""<div style="{_BASE_STYLE}">
  <div style="{_HEADER_STYLE}">
    <div style="font-size:20px;font-weight:bold;color:#C8780F">AI-ADVISOR</div>
    <div style="font-size:13px;color:#9BAEC8;margin-top:4px">Bản tin sáng — {today}</div>
  </div>
  <div style="{_BODY_STYLE}">
    <div style="background:#EEF3FA;border-left:4px solid #2355A0;
                padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:16px">
      <div style="font-size:13px;font-weight:bold;color:#1B3A6B">
        Thị trường hôm nay: {regime_emoji} {regime_label}
      </div>
      <div style="font-size:12px;color:#444;margin-top:3px">
        Risk score: {regime['risk']}/100 &nbsp;|&nbsp; Tỷ trọng khuyến nghị: {regime['allocation']}%
      </div>
    </div>

    <div style="font-size:13px;font-weight:bold;color:#1B3A6B;margin-bottom:8px">
      Signal mới cho {method_name} của bạn:
    </div>
    {signal_html}

    <div style="margin-top:16px;text-align:center">
      <a href="{FRONTEND_URL}" style="display:inline-block;background:#1B3A6B;
         color:#fff;font-size:13px;font-weight:bold;padding:10px 24px;
         border-radius:6px;text-decoration:none">
        Xem đầy đủ trên AI-Advisor →
      </a>
    </div>
  </div>
  <div style="{_FOOTER_STYLE}">
    <a href="{FRONTEND_URL}/unsubscribe?email={user['email']}&type=morning"
       style="color:#999">Huỷ đăng ký email sáng</a>
    &nbsp;·&nbsp; AI Advisor © 2026
  </div>
</div>"""
    return subject, html


def build_signal_alert_email(user: dict, signal: dict, regime: dict) -> tuple[str, str]:
    """Email 2: Signal Alert cho watchlist."""
    subject = f'[AI-Advisor] {signal["ticker"]} — Signal Grade {signal["grade"]} vừa xuất hiện'

    sl_pct = round((signal['sl'] - signal['entry']) / signal['entry'] * 100, 1) if signal['entry'] else 0
    tp_pct = round((signal['tp'] - signal['entry']) / signal['entry'] * 100, 1) if signal['entry'] else 0
    regime_emoji = {'BULL':'🟢','NEUTRAL':'🟡','BEAR':'🔴'}.get(regime['mode'],'⚪')

    html = f"""<div style="{_BASE_STYLE}">
  <div style="{_HEADER_STYLE}">
    <div style="font-size:20px;font-weight:bold;color:#C8780F">AI-ADVISOR</div>
    <div style="font-size:13px;color:#9BAEC8;margin-top:4px">Signal Alert</div>
  </div>
  <div style="{_BODY_STYLE}">
    <div style="background:#EEF3FA;border-left:4px solid #1A6B3C;
                padding:12px 14px;border-radius:0 6px 6px 0;margin-bottom:14px">
      <div style="font-size:16px;font-weight:bold;color:#1B3A6B">
        {signal['ticker']} — Grade {signal['grade']} ({signal['strategy']})
      </div>
    </div>

    <table style="width:100%;font-size:13px;border-collapse:collapse">
      <tr>
        <td style="padding:6px 0;color:#666">Entry</td>
        <td style="padding:6px 0;font-weight:bold;color:#1B3A6B">{signal['entry']:,.0f} VND</td>
      </tr>
      <tr style="background:#fafafa">
        <td style="padding:6px 0;color:#666">Stop Loss</td>
        <td style="padding:6px 0;font-weight:bold;color:#A0281E">{signal['sl']:,.0f} ({sl_pct}%)</td>
      </tr>
      <tr>
        <td style="padding:6px 0;color:#666">Take Profit</td>
        <td style="padding:6px 0;font-weight:bold;color:#1A6B3C">{signal['tp']:,.0f} (+{tp_pct}%)</td>
      </tr>
      <tr style="background:#fafafa">
        <td style="padding:6px 0;color:#666">Risk-Reward</td>
        <td style="padding:6px 0;font-weight:bold">1:{signal['rr']}</td>
      </tr>
    </table>

    <div style="background:#f7f9fd;border-left:3px solid #888;
                padding:8px 12px;margin:14px 0;border-radius:0 4px 4px 0;font-size:12px;color:#444">
      Thị trường: {regime_emoji} {regime.get('label','Neutral')} &nbsp;|&nbsp; Risk: {regime['risk']}/100
    </div>

    <div style="text-align:center;margin-top:16px">
      <a href="{FRONTEND_URL}" style="display:inline-block;background:#C8780F;
         color:#fff;font-size:13px;font-weight:bold;padding:10px 24px;
         border-radius:6px;text-decoration:none">
        Xem Pre-Trade Clearance Card →
      </a>
    </div>
  </div>
  <div style="{_FOOTER_STYLE}">
    <a href="{FRONTEND_URL}/unsubscribe?email={user['email']}&type=signal"
       style="color:#999">Huỷ signal alerts</a>
    &nbsp;·&nbsp; AI Advisor © 2026
  </div>
</div>"""
    return subject, html


def build_portfolio_alert_email(user: dict, alerts: list, regime: dict) -> tuple[str, str]:
    """Email 3: Portfolio Alert — SL gần hit."""
    count   = len(alerts)
    subject = f'⚠️ [AI-Advisor] {count} vị thế cần kiểm tra — Stop Loss gần hit'

    rows_html = ''
    for a in alerts:
        rows_html += f"""
    <div style="background:#FBEAEA;border-left:4px solid #A0281E;
                padding:10px 14px;margin:8px 0;border-radius:0 6px 6px 0">
      <div style="font-size:14px;font-weight:bold;color:#A0281E">{a['ticker']}
        <span style="float:right;font-size:12px">Lỗ {a['loss_pct']}%</span>
      </div>
      <div style="font-size:12px;color:#555;margin-top:4px">
        Giá mua: {a['avg_price']:,.0f} &nbsp;|&nbsp;
        Giá hiện tại: {a['current']:,.0f} &nbsp;|&nbsp;
        Stop Loss: {a['stop_loss']:,.0f}
      </div>
      <div style="font-size:12px;color:#A0281E;margin-top:4px;font-weight:bold">
        Còn cách SL: {a['sl_gap_pct']}%
      </div>
    </div>"""

    html = f"""<div style="{_BASE_STYLE}">
  <div style="{_HEADER_STYLE}">
    <div style="font-size:20px;font-weight:bold;color:#C8780F">AI-ADVISOR</div>
    <div style="font-size:13px;color:#9BAEC8;margin-top:4px">⚠️ Cảnh báo danh mục</div>
  </div>
  <div style="{_BODY_STYLE}">
    <p style="font-size:13px;color:#333;margin-bottom:12px">
      Có <b>{count} vị thế</b> trong danh mục của bạn đang gần chạm Stop Loss.
      Hãy kiểm tra và xem xét hành động phù hợp.
    </p>
    {rows_html}
    <div style="background:#FFF8E8;border-left:3px solid #C8780F;
                padding:10px 14px;margin:14px 0;border-radius:0 4px 4px 0;font-size:12px;color:#444">
      <b>3 bước cần làm:</b><br>
      1. Kiểm tra luận điểm đầu tư còn đúng không?<br>
      2. Nếu còn đúng → giữ nguyên plan đã đặt<br>
      3. Nếu có gì thay đổi cơ bản → xem xét thoát sớm
    </div>
    <div style="text-align:center;margin-top:16px">
      <a href="{FRONTEND_URL}" style="display:inline-block;background:#A0281E;
         color:#fff;font-size:13px;font-weight:bold;padding:10px 24px;
         border-radius:6px;text-decoration:none">
        Kiểm tra danh mục ngay →
      </a>
    </div>
  </div>
  <div style="{_FOOTER_STYLE}">
    AI Advisor © 2026 &nbsp;·&nbsp;
    <a href="{FRONTEND_URL}/unsubscribe?email={user['email']}&type=portfolio"
       style="color:#999">Huỷ cảnh báo</a>
  </div>
</div>"""
    return subject, html


def build_weekly_report_email(user: dict, stats: dict) -> tuple[str, str]:
    """Email 4: IIS Weekly Report — thứ Hai sáng."""
    week_num = datetime.now().isocalendar()[1]
    delta_str = f'+{stats["iis_delta"]}' if stats['iis_delta'] >= 0 else str(stats['iis_delta'])
    delta_color = '#1A6B3C' if stats['iis_delta'] >= 0 else '#A0281E'

    subject = f'[AI-Advisor] Tuần {week_num}: IIS {stats["iis_total"]}/100 — Báo cáo hàng tuần'

    html = f"""<div style="{_BASE_STYLE}">
  <div style="{_HEADER_STYLE}">
    <div style="font-size:20px;font-weight:bold;color:#C8780F">AI-ADVISOR</div>
    <div style="font-size:13px;color:#9BAEC8;margin-top:4px">Báo cáo IIS — Tuần {week_num}</div>
  </div>
  <div style="{_BODY_STYLE}">
    <!-- IIS Score -->
    <div style="text-align:center;padding:16px 0;border-bottom:1px solid #eee;margin-bottom:16px">
      <div style="font-size:42px;font-weight:bold;color:#1B3A6B">{stats['iis_total']}</div>
      <div style="font-size:13px;color:#666">Investor Intelligence Score</div>
      <div style="font-size:13px;font-weight:bold;color:{delta_color};margin-top:4px">
        {delta_str} điểm so với tuần trước &nbsp;|&nbsp; {stats['iis_level']}
      </div>
    </div>

    <!-- Score breakdown -->
    <table style="width:100%;font-size:13px;border-collapse:collapse;margin-bottom:14px">
      <tr>
        <td style="padding:7px 0;color:#666">IIS Kỷ Luật</td>
        <td style="padding:7px 0;text-align:right">
          <b style="color:#1B3A6B">{stats['kl_score']}/100</b>
        </td>
      </tr>
      <tr style="background:#fafafa">
        <td style="padding:7px 0;color:#666">IIS Kiến Thức</td>
        <td style="padding:7px 0;text-align:right">
          <b style="color:#1B3A6B">{stats['kt_score']}/100</b>
        </td>
      </tr>
      <tr>
        <td style="padding:7px 0;color:#666">Win / Loss (30 ngày)</td>
        <td style="padding:7px 0;text-align:right">
          <b style="color:#1A6B3C">{stats['wins']}W</b> /
          <b style="color:#A0281E">{stats['losses']}L</b>
          {f'· Win rate: {stats["win_rate"]}%' if (stats['wins']+stats['losses'])>0 else ''}
        </td>
      </tr>
    </table>

    <div style="background:#EEF3FA;border-left:3px solid #2355A0;
                padding:10px 14px;border-radius:0 4px 4px 0;
                font-size:12px;color:#1B3A6B;margin-bottom:16px">
      <b>Tuần này hãy chú ý:</b> Hoàn thành pre-trade checklist trước mỗi lệnh
      và đặt stop loss ngay khi mua để cải thiện IIS Kỷ Luật.
    </div>

    <div style="text-align:center">
      <a href="{FRONTEND_URL}" style="display:inline-block;background:#1A6B3C;
         color:#fff;font-size:13px;font-weight:bold;padding:10px 24px;
         border-radius:6px;text-decoration:none">
        Xem báo cáo đầy đủ →
      </a>
    </div>
  </div>
  <div style="{_FOOTER_STYLE}">
    <a href="{FRONTEND_URL}/unsubscribe?email={user['email']}&type=weekly"
       style="color:#999">Huỷ báo cáo tuần</a>
    &nbsp;·&nbsp; AI Advisor © 2026
  </div>
</div>"""
    return subject, html


# ── Main scheduler functions ──────────────────────────────────────────────

def run_morning_email(dry_run: bool = False):
    """Email 1: Bản tin sáng — gửi cho tất cả user active."""
    log.info('=== EMAIL 1: Bản tin sáng ===')
    session = Session()
    try:
        users   = get_active_users(session)
        regime  = get_market_regime(session)
        log.info(f'Regime: {regime["mode"]} | Users: {len(users)}')

        sent = failed = 0
        for user in users:
            profile = get_iis_profile(session, user['email'])
            signals = get_top_signals(session, profile.get('method', 'bat_song'), limit=3)
            subject, html = build_morning_email(user, regime, signals, profile)
            ok = send_email(user['email'], subject, html, dry_run)
            if ok: sent += 1
            else:  failed += 1

        log.info(f'Morning email: sent={sent} failed={failed}')
    finally:
        session.close()


def run_signal_alert(ticker: str = None, dry_run: bool = False):
    """Email 2: Signal Alert — gửi khi có Grade A/S signal mới."""
    log.info('=== EMAIL 2: Signal Alert ===')
    session = Session()
    try:
        # Tìm signals Grade A/S tạo trong 2 giờ vừa qua
        cutoff = datetime.now() - timedelta(hours=2)
        rows = session.execute(text(
            """SELECT ticker, strategy, entry_price, stop_loss, take_profit,
                      risk_reward, strength
               FROM signals
               WHERE action = 'BUY'
                 AND strength >= 75
                 AND created_at >= :cutoff
                 AND (:ticker IS NULL OR ticker = :ticker)
               ORDER BY strength DESC"""
        ), {'cutoff': cutoff, 'ticker': ticker}).fetchall()

        if not rows:
            log.info('Không có signal Grade A/S mới trong 2 giờ qua')
            return

        regime = get_market_regime(session)
        users  = get_active_users(session)

        for row in rows:
            signal = {
                'ticker': row[0], 'strategy': row[1],
                'entry': round(row[2]/100)*100 if row[2] else 0,
                'sl':    round(row[3]/100)*100 if row[3] else 0,
                'tp':    round(row[4]/100)*100 if row[4] else 0,
                'rr':    round(row[5], 1) if row[5] else 0,
                'grade': 'S' if (row[6] or 0) >= 90 else 'A',
            }
            sent = 0
            for user in users:
                subject, html = build_signal_alert_email(user, signal, regime)
                ok = send_email(user['email'], subject, html, dry_run)
                if ok: sent += 1

            log.info(f'Signal alert {signal["ticker"]} Grade {signal["grade"]}: sent={sent}')
    finally:
        session.close()


def run_portfolio_alert(dry_run: bool = False):
    """Email 3: Portfolio Alert — gửi khi SL gần hit."""
    log.info('=== EMAIL 3: Portfolio Alert ===')
    session = Session()
    try:
        regime = get_market_regime(session)
        users  = get_active_users(session)
        sent   = 0

        for user in users:
            alerts = get_portfolio_alerts(session, user['email'])
            if not alerts:
                continue
            subject, html = build_portfolio_alert_email(user, alerts, regime)
            ok = send_email(user['email'], subject, html, dry_run)
            if ok: sent += 1
            log.info(f'Portfolio alert → {user["email"]}: {len(alerts)} alerts')

        log.info(f'Portfolio alerts: {sent} emails sent')
    finally:
        session.close()


def run_weekly_report(dry_run: bool = False):
    """Email 4: IIS Weekly Report — gửi thứ Hai sáng."""
    log.info('=== EMAIL 4: IIS Weekly Report ===')
    session = Session()
    try:
        users = get_active_users(session)
        sent  = failed = 0

        for user in users:
            stats   = get_iis_weekly_stats(session, user['email'])
            subject, html = build_weekly_report_email(user, stats)
            ok = send_email(user['email'], subject, html, dry_run)
            if ok: sent += 1
            else:  failed += 1

        log.info(f'Weekly report: sent={sent} failed={failed}')
    finally:
        session.close()


# ── CLI entry point ───────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AI-Advisor Email Scheduler')
    parser.add_argument('--type',    choices=['morning','signal','portfolio','weekly'],
                        default='morning', help='Loại email cần gửi')
    parser.add_argument('--ticker',  default=None, help='Ticker cụ thể cho signal alert')
    parser.add_argument('--dry-run', action='store_true', help='Log nhưng không gửi email')
    args = parser.parse_args()

    if args.dry_run:
        log.info('🔍 DRY-RUN mode — không gửi email thực')

    if args.type == 'morning':
        run_morning_email(dry_run=args.dry_run)
    elif args.type == 'signal':
        run_signal_alert(ticker=args.ticker, dry_run=args.dry_run)
    elif args.type == 'portfolio':
        run_portfolio_alert(dry_run=args.dry_run)
    elif args.type == 'weekly':
        run_weekly_report(dry_run=args.dry_run)
