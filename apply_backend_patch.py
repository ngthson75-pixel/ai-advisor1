#!/usr/bin/env python3
"""
Apply delay=3 patch to backend_api.py
Thực hiện trên máy local: python apply_backend_patch.py
"""
import re

with open('backend_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

OLD = """    if request.method == 'GET':
        # GET: Return all signals with rounding and deduplication
        session = Session()
        try:
            signals = session.query(Signal)\\
              .filter(
              ~exists().where(
                and_(
                TickerBlacklist.ticker == Signal.ticker,
                TickerBlacklist.is_active == True
                     )
                  )
               )\\
              .order_by(Signal.created_at.desc())\\
              .all()"""

NEW = """    if request.method == 'GET':
        # GET: Return all signals with rounding and deduplication
        # ── TIER FILTER: ?delay=N để trả tín hiệu cũ hơn N ngày (Free users) ──
        delay_days = request.args.get('delay', type=int)
        session = Session()
        try:
            query = session.query(Signal).filter(
                ~exists().where(
                    and_(
                        TickerBlacklist.ticker == Signal.ticker,
                        TickerBlacklist.is_active == True
                    )
                )
            )
            if delay_days and delay_days > 0:
                cutoff = datetime.utcnow() - timedelta(days=delay_days)
                query = query.filter(Signal.created_at <= cutoff)

            signals = query.order_by(Signal.created_at.desc()).all()"""

if OLD in content:
    content = content.replace(OLD, NEW)
    with open('backend_api.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ backend_api.py patched: delay filter added")
else:
    print("❌ Không tìm thấy đoạn cần thay. Kiểm tra lại file hoặc thực hiện thủ công.")
    print("\nThay thủ công: trong /api/signals GET, sau dòng 'session = Session()' thêm:")
    print("""
        delay_days = request.args.get('delay', type=int)
    """)
    print("Và thêm điều kiện filter sau khi build query:")
    print("""
        if delay_days and delay_days > 0:
            cutoff = datetime.utcnow() - timedelta(days=delay_days)
            query = query.filter(Signal.created_at <= cutoff)
    """)
