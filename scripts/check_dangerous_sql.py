"""
AI ADVISOR — CHẶN CODE XÓA DỮ LIỆU NGUY HIỂM TRƯỚC KHI DEPLOY (v1.1, 2026-10-11)
File: scripts/check_dangerous_sql.py — chạy trong GitHub Actions trước bước deploy.

Quét mọi file .py trong repo, báo LỖI (exit 1 → không deploy) nếu thấy:
  - DELETE FROM <bảng> không có WHERE         (đúng loại lỗi đã xóa sạch signals ngày 02/10)
  - TRUNCATE, DROP TABLE, drop_all(), .query(...).delete() không có filter
Dòng nào CỐ Ý làm vậy (ví dụ reset có xác nhận) phải ghi chú cuối dòng:  # SAFE-DELETE: <lý do>
Chạy thử trên máy:  python scripts/check_dangerous_sql.py
"""
import os
import re
import sys

SKIP_DIRS = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '_archive', 'data_safety'}
PATTERNS = [
    (re.compile(r"""DELETE\s+FROM\s+[\w"{}.]+\s*(?:['"]|\)|;|$)""", re.I), 'DELETE không có WHERE'),
    (re.compile(r"""\bTRUNCATE\b""", re.I), 'TRUNCATE'),
    (re.compile(r"""\bDROP\s+TABLE\b""", re.I), 'DROP TABLE'),
    (re.compile(r"""\.drop_all\s*\("""), 'metadata.drop_all()'),
    (re.compile(r"""\.query\(\s*\w+\s*\)\s*\.delete\s*\("""), 'query(Model).delete() không có filter'),
]
ALLOW = 'SAFE-DELETE'


def scan(root='.'):
    hits = []
    me = os.path.abspath(__file__)
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if not f.endswith('.py') or f.startswith('test_') or os.sep + 'tests' in d \
                    or f == 'check_dangerous_sql.py':
                continue
            p = os.path.join(d, f)
            if os.path.abspath(p) == me:
                continue
            try:
                lines = open(p, encoding='utf-8', errors='ignore').read().splitlines()
            except OSError:
                continue
            for i, ln in enumerate(lines, 1):
                if ALLOW in ln or ln.strip().startswith('#'):
                    continue
                for rx, label in PATTERNS:
                    if rx.search(ln):
                        # SQL nhiều dòng: "DELETE FROM x" ở cuối dòng, WHERE nằm ở dòng kế tiếp → không phải lỗi
                        if label.startswith('DELETE') and any(
                                re.match(r'\s*WHERE\b', nx, re.I) for nx in lines[i:i + 3]):
                            continue
                        hits.append((p, i, label, ln.strip()[:120]))
    return hits


if __name__ == '__main__':
    hits = scan(sys.argv[1] if len(sys.argv) > 1 else '.')
    if not hits:
        print('✅ Không có lệnh xóa dữ liệu nguy hiểm')
        sys.exit(0)
    print(f'❌ {len(hits)} lệnh xóa dữ liệu nguy hiểm — sửa hoặc ghi chú "# {ALLOW}: <lý do>" nếu cố ý:\n')
    for p, i, label, ln in hits:
        print(f'  {p}:{i}  [{label}]  {ln}')
    sys.exit(1)
