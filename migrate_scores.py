#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_scores.py — Normalize DIVERGENCE_FB scores ve thang diem moi
=====================================================================

Cach chay:
  cd C:\\ai-advisor1

  # Buoc 1: Preview (khong thay doi DB)
  python migrate_scores.py --dry-run

  # Buoc 2: Update production
  python migrate_scores.py --run

  # Hoac chi dinh DB URL thu cong:
  python migrate_scores.py --run --db-url "postgresql://user:pass@host:5432/dbname"
"""

import os, sys, argparse
from datetime import datetime
from pathlib import Path

# =========================================================
# AUTO-LOAD .env (khong can python-dotenv)
# =========================================================
def load_dotenv():
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        return
    with open(env_path, encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key   = key.strip()
            value = value.strip().strip('"').strip("'")
            # comment cuoi dong
            if ' #' in value:
                value = value[:value.index(' #')].strip()
            if key and key not in os.environ:
                os.environ[key] = value

load_dotenv()

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("Thieu sqlalchemy. Chay: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# =========================================================
# RESOLVE DB URL
# =========================================================
def get_db_url():
    """
    Thu theo thu tu uu tien:
      1. DATABASE_URL truc tiep (neu khong phai sqlite)
      2. DB_HOST + DB_NAME + DB_USER + DB_PASSWORD + DB_PORT
      3. Local SQLite fallback
    """
    url = os.getenv('DATABASE_URL', '')
    if url and 'postgresql' in url:
        return url

    host = os.getenv('DB_HOST', '')
    if host:
        name = os.getenv('DB_NAME', 'signals')
        user = os.getenv('DB_USER', 'postgres')
        pw   = os.getenv('DB_PASSWORD', '')
        port = os.getenv('DB_PORT', '5432')
        return f"postgresql://{user}:{pw}@{host}:{port}/{name}"

    # Local SQLite
    sqlite = Path(__file__).parent / 'signals.db'
    if sqlite.exists():
        return f"sqlite:///{sqlite}"

    return ''

def fix_pg_url(url):
    """SQLAlchemy 2.x can postgresql+psycopg2 hoac postgresql+psycopg"""
    if not url.startswith('postgresql://'):
        return url
    try:
        import psycopg2
        return url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    except ImportError:
        pass
    try:
        import psycopg
        return url.replace('postgresql://', 'postgresql+psycopg://', 1)
    except ImportError:
        pass
    return url

def mask_url(url):
    """An password trong URL de hien thi"""
    if '@' in url and '://' in url:
        proto_end = url.index('://') + 3
        at_pos    = url.index('@')
        creds     = url[proto_end:at_pos]
        if ':' in creds:
            user = creds.split(':')[0]
            return url[:proto_end] + user + ':***@' + url[at_pos+1:]
    return url

# =========================================================
# NORMALIZE FORMULA
# =========================================================
def normalize_div_fb(old_score):
    """
    Linear map: old DIVERGENCE_FB (65-172) -> new (40-100)
    new = 40 + (old - 65) / 107.0 * 60
    """
    new = 40 + (old_score - 65) / 107.0 * 60
    return max(40, min(100, round(new)))

# =========================================================
# PREVIEW
# =========================================================
def preview(engine):
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(
                "SELECT id, ticker, strength, date "
                "FROM signals WHERE strategy = 'DIVERGENCE_FB' "
                "ORDER BY strength DESC"
            )).fetchall()
        except Exception as e:
            print(f"  Loi doc DB: {e}")
            return []

    if not rows:
        print("  Khong co DIVERGENCE_FB signals trong DB")
        return []

    need_update = []
    no_change   = []

    for row in rows:
        old = int(row.strength)
        new = normalize_div_fb(old)
        if old > 100 or abs(old - new) > 2:
            need_update.append((row.id, row.ticker, old, new, str(row.date)))
        else:
            no_change.append((row.ticker, old))

    print(f"\n  {'ID':<8} {'Ticker':<8} {'Old':>6}    {'New':>5}  {'Date'}")
    print("  " + "-"*52)
    for sid, ticker, old, new, date in need_update:
        delta = new - old
        arrow = f"d{abs(delta)}" if delta < 0 else f"+{delta}"
        print(f"  {sid:<8} {ticker:<8} {old:>5}%  ->  {new:>3}%  {date}  ({arrow})")

    if no_change:
        sample = ", ".join(f"{t}({s}%)" for t, s in no_change[:6])
        more   = f"... +{len(no_change)-6}" if len(no_change) > 6 else ""
        print(f"\n  Giu nguyen ({len(no_change)}): {sample}{more}")

    print(f"\n  Tong: {len(rows)} | Can update: {len(need_update)} | Giu nguyen: {len(no_change)}")
    return need_update

# =========================================================
# EXECUTE
# =========================================================
def run_migration(engine, dry_run=False):
    mode = "DRY RUN (khong ghi DB)" if dry_run else "LIVE UPDATE"
    print(f"\n{'='*55}")
    print(f"  Mode: {mode}")
    print(f"{'='*55}")

    changes = preview(engine)

    if not changes:
        print("\n  Khong co gi can update.")
        return

    if dry_run:
        print(f"\n  DRY RUN: {len(changes)} rows se duoc update khi chay --run")
        return

    print()
    confirm = input(f"  Thuc hien update {len(changes)} signals? (y/n): ").strip().lower()
    if confirm != 'y':
        print("  Da huy.")
        return

    updated = 0
    errors  = 0
    with engine.begin() as conn:
        for sid, ticker, old_score, new_score, _ in changes:
            try:
                r = conn.execute(text(
                    "UPDATE signals SET strength = :new "
                    "WHERE id = :sid AND strategy = 'DIVERGENCE_FB'"
                ), {'new': new_score, 'sid': sid})
                if r.rowcount > 0:
                    updated += 1
                    print(f"  OK  {ticker:<6} {old_score}% -> {new_score}%")
            except Exception as e:
                errors += 1
                print(f"  ERR ID {sid} ({ticker}): {e}")

    print(f"\n  Updated: {updated}  |  Errors: {errors}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Cap EMA_CROSS / PULLBACK > 100
    with engine.begin() as conn:
        try:
            r = conn.execute(text(
                "UPDATE signals SET strength = 100 "
                "WHERE strategy IN ('EMA_CROSS','PULLBACK') AND strength > 100"
            ))
            if r.rowcount > 0:
                print(f"  Cap {r.rowcount} EMA_CROSS/PULLBACK > 100 ve 100%")
        except Exception:
            pass

# =========================================================
# MAIN
# =========================================================
def main():
    parser = argparse.ArgumentParser(
        description='Normalize DIVERGENCE_FB scores (old 65-172) -> new (40-100)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python migrate_scores.py --dry-run
  python migrate_scores.py --run
  python migrate_scores.py --run --db-url "postgresql://user:pass@host:5432/db"
        """
    )
    parser.add_argument('--dry-run', action='store_true', help='Preview, khong ghi DB')
    parser.add_argument('--run',     action='store_true', help='Thuc hien update')
    parser.add_argument('--db-url',  default='',          help='Override DB URL')
    args = parser.parse_args()

    if not args.dry_run and not args.run:
        parser.print_help()
        print("\nTip: chay --dry-run truoc de xem truoc thay doi")
        sys.exit(0)

    print(f"\n{'='*55}")
    print("  SCORE MIGRATION — DIVERGENCE_FB scoring v2")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    db_url = args.db_url or get_db_url()

    if not db_url:
        print("""
Khong tim thay DB URL. Thu 1 trong cac cach sau:

  Cach 1 — Them vao file .env:
    DATABASE_URL=postgresql://user:pass@host:5432/dbname
    hoac:
    DB_HOST=your-render-host.oregon-postgres.render.com
    DB_NAME=your_db_name
    DB_USER=your_user
    DB_PASSWORD=your_password
    DB_PORT=5432

  Cach 2 — Truyen truc tiep:
    python migrate_scores.py --run --db-url "postgresql://..."

  Xem thong tin DB tren Render.com:
    Dashboard -> your-db -> Connect -> External Database URL
        """)
        sys.exit(1)

    print(f"\n  DB: {mask_url(db_url)}")

    try:
        fixed  = fix_pg_url(db_url)
        kwargs = {'connect_args': {'connect_timeout': 15}} if 'postgresql' in fixed else {}
        engine = create_engine(fixed, **kwargs)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  Ket noi DB thanh cong")
    except Exception as e:
        print(f"\n  Loi ket noi: {e}")
        print("\n  Tips:")
        print("  - Kiem tra DB_HOST, DB_PASSWORD trong .env")
        print("  - Render server co the dang ngu - try wake up truoc")
        print("  - Cai driver: pip install psycopg2-binary")
        sys.exit(1)

    run_migration(engine, dry_run=args.dry_run)
    print(f"\n{'='*55}\n")


if __name__ == '__main__':
    main()
