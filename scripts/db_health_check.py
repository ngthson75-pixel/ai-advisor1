"""
AI ADVISOR — KIỂM TRA SỨC KHỎE DỮ LIỆU (v1.0, 2026-10-09)
File: scripts/db_health_check.py  — chạy bởi .github/workflows/db-backup.yml

Mỗi lần chạy:
  1. Đếm số dòng các bảng quan trọng, lưu snapshot vào bảng data_health.
  2. So với snapshot trước. Nếu một bảng GIẢM bất thường (signals giảm > 5 dòng, bảng khác giảm > 20%)
     hoặc biến mất → gửi Telegram cho admin + exit 1 (workflow báo đỏ).
  3. Báo số dòng bị xóa trong 24h qua (từ data_audit của DATA GUARD).

Sự cố 02/10 (signals 1.164 → 11 dòng) sẽ bị phát hiện ở lần chạy kế tiếp, thay vì 8 ngày sau.

ENV: DATABASE_URL (bắt buộc), TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_CHAT_ID (không có thì chỉ in log).
"""
import os
import sys
import json
import urllib.parse
import urllib.request
from datetime import datetime

from sqlalchemy import create_engine, text

TABLES = ['signals', 'vip_users', 'portfolios', 'cash_positions', 'watch_prefs', 'watch_levels',
          'mp_positions', 'mp_trades', 'mp_nav', 'price_history', 'corporate_actions']
SIGNALS_MAX_DROP = 5          # signals chỉ được thêm/đóng, gần như không bao giờ giảm
OTHER_MAX_DROP_PCT = 20       # bảng khác: giảm > 20% là bất thường


def _engine():
    url = os.environ['DATABASE_URL']
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
    return create_engine(url, pool_pre_ping=True)


def _telegram(msg):
    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat = os.getenv('ADMIN_TELEGRAM_CHAT_ID', '')
    if not token or not chat:
        print('(Không có TELEGRAM_BOT_TOKEN / ADMIN_TELEGRAM_CHAT_ID → chỉ in log)')
        return
    data = urllib.parse.urlencode({'chat_id': chat, 'text': msg}).encode()
    try:
        urllib.request.urlopen(f'https://api.telegram.org/bot{token}/sendMessage', data=data, timeout=15).read()
    except Exception as e:
        print('Telegram lỗi:', e)


def check(engine, now=None):
    now = now or datetime.utcnow()
    problems, lines = [], []
    with engine.begin() as c:
        c.execute(text("""CREATE TABLE IF NOT EXISTS data_health (
                              id SERIAL PRIMARY KEY, snap_at TIMESTAMP NOT NULL, counts TEXT NOT NULL)"""))
        prev_row = c.execute(text("SELECT counts FROM data_health ORDER BY snap_at DESC, id DESC LIMIT 1")).first()
        prev = json.loads(prev_row[0]) if prev_row else {}

        counts = {}
        for t in TABLES:
            exists = c.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {'t': t}).scalar() \
                if engine.dialect.name == 'postgresql' else \
                c.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=:t"), {'t': t}).scalar() > 0
            if not exists:
                if prev.get(t) is not None:
                    problems.append(f'Bảng {t} BIẾN MẤT (trước có {prev[t]} dòng)')
                continue
            counts[t] = int(c.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar())

        for t, n in counts.items():
            p = prev.get(t)
            lines.append(f'{t}: {n}' + (f' (trước {p})' if p is not None and p != n else ''))
            if p is None or n >= p:
                continue
            drop = p - n
            if t == 'signals' and drop > SIGNALS_MAX_DROP:
                problems.append(f'signals giảm {drop} dòng ({p} → {n})')
            elif t != 'signals' and p > 0 and drop * 100.0 / p > OTHER_MAX_DROP_PCT:
                problems.append(f'{t} giảm {drop * 100.0 / p:.0f}% ({p} → {n})')

        deleted_24h = []
        has_audit = c.execute(text("SELECT to_regclass('data_audit') IS NOT NULL")).scalar() \
            if engine.dialect.name == 'postgresql' else False
        if has_audit:
            for t, n in c.execute(text("""SELECT tbl, COUNT(*) FROM data_audit
                                          WHERE at >= now() - interval '24 hours' GROUP BY tbl""")):
                deleted_24h.append(f'{t}: {n}')
        else:
            problems.append('Chưa cài DATA GUARD (bảng data_audit chưa có) — chạy 1_db_guard.sql')

        c.execute(text("INSERT INTO data_health (snap_at, counts) VALUES (:a, :c)"),
                  {'a': now, 'c': json.dumps(counts)})
    return problems, lines, deleted_24h


def main():
    problems, lines, deleted = check(_engine())
    print('\n'.join(lines))
    if deleted:
        print('Dòng bị xóa trong 24h (đã lưu trong data_audit):', ', '.join(deleted))
    if problems:
        msg = '🚨 AI Advisor — DỮ LIỆU BẤT THƯỜNG\n' + '\n'.join('• ' + p for p in problems) + \
              '\n\nKiểm tra ngay. Bản sao lưu: GitHub → Actions → DB Backup & Health → Artifacts.'
        print(msg)
        _telegram(msg)
        sys.exit(1)
    print('✅ Dữ liệu bình thường')


if __name__ == '__main__':
    main()
