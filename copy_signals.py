"""
copy_signals.py
Copy signals từ DB restored (ai_advisor_ilm5_0t17) → DB gốc (ai_advisor_ilm5)
Chỉ copy signals chưa có trong DB gốc (tránh duplicate)
"""

import psycopg2
from datetime import datetime

# ── Connection strings ────────────────────────────────────────
DB_SOURCE = "postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d7macfgk1i2s7391hpm0-a.singapore-postgres.render.com/ai_advisor_ilm5_0t17"
DB_TARGET = "postgresql://ai_advisor_user:OPmx1O1UTpXknFgW0UakvlZFlfYM8wfo@dpg-d5npf8fgi27c73eplem0-a.singapore-postgres.render.com/ai_advisor_ilm5"

def run():
    print("=" * 60)
    print("COPY SIGNALS: DB restored → DB gốc")
    print("=" * 60)

    # ── Connect ───────────────────────────────────────────────
    print("\n🔌 Kết nối DB restored (nguồn)...")
    src = psycopg2.connect(DB_SOURCE)
    print("✅ DB restored OK")

    print("🔌 Kết nối DB gốc (đích)...")
    tgt = psycopg2.connect(DB_TARGET)
    print("✅ DB gốc OK")

    src_cur = src.cursor()
    tgt_cur = tgt.cursor()

    # ── Đếm trước ────────────────────────────────────────────
    src_cur.execute("SELECT COUNT(*) FROM signals")
    src_count = src_cur.fetchone()[0]
    tgt_cur.execute("SELECT COUNT(*) FROM signals")
    tgt_count_before = tgt_cur.fetchone()[0]
    print(f"\n📊 DB restored: {src_count} signals")
    print(f"📊 DB gốc hiện tại: {tgt_count_before} signals")

    # ── Lấy columns của bảng signals trong DB gốc ────────────
    tgt_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'signals' AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    tgt_cols = [r[0] for r in tgt_cur.fetchall()]
    print(f"\n📋 Columns trong DB gốc: {tgt_cols}")

    # ── Lấy tất cả signals từ nguồn ──────────────────────────
    src_cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'signals' AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    src_cols = [r[0] for r in src_cur.fetchall()]

    # Chỉ copy các columns có trong CẢ HAI DB
    common_cols = [c for c in src_cols if c in tgt_cols and c != 'id']
    print(f"📋 Columns sẽ copy: {common_cols}")

    src_cur.execute(f"SELECT {','.join(common_cols)} FROM signals ORDER BY id")
    src_signals = src_cur.fetchall()
    print(f"\n📥 Đọc {len(src_signals)} signals từ DB restored")

    # ── Lấy existing signals trong DB gốc để tránh duplicate ─
    tgt_cur.execute("SELECT ticker, date, action FROM signals")
    existing = set(tgt_cur.fetchall())
    print(f"🔍 DB gốc có {len(existing)} existing (ticker, date, action) combos")

    # ── Copy ──────────────────────────────────────────────────
    inserted = 0
    skipped  = 0
    errors   = 0

    col_idx = {col: i for i, col in enumerate(common_cols)}
    placeholders = ','.join(['%s'] * len(common_cols))
    insert_sql = f"INSERT INTO signals ({','.join(common_cols)}) VALUES ({placeholders})"

    for row in src_signals:
        ticker = row[col_idx['ticker']] if 'ticker' in col_idx else None
        date   = row[col_idx['date']]   if 'date'   in col_idx else None
        action = row[col_idx['action']] if 'action' in col_idx else None

        if (ticker, date, action) in existing:
            skipped += 1
            continue

        try:
            tgt_cur.execute(insert_sql, row)
            existing.add((ticker, date, action))
            inserted += 1
        except Exception as e:
            print(f"  ⚠️  Lỗi insert {ticker} {date}: {e}")
            tgt.rollback()
            errors += 1
            continue

    tgt.commit()

    # ── Kết quả ───────────────────────────────────────────────
    tgt_cur.execute("SELECT COUNT(*) FROM signals")
    tgt_count_after = tgt_cur.fetchone()[0]

    print(f"\n{'='*60}")
    print(f"✅ HOÀN THÀNH")
    print(f"   Đã insert : {inserted} signals")
    print(f"   Bỏ qua    : {skipped} signals (đã có)")
    print(f"   Lỗi       : {errors} signals")
    print(f"   DB gốc trước: {tgt_count_before} → sau: {tgt_count_after}")
    print(f"{'='*60}")

    src_cur.close(); src.close()
    tgt_cur.close(); tgt.close()

if __name__ == '__main__':
    run()
