#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LUK DAILY RUNNER — chạy LUK Model Portfolio mỗi ngày sau phiên
=============================================================
Version: 1.0 (2026-10-14) · Luật: luk_engine.RULES_VERSION

Việc làm mỗi lần chạy:
  1. Tải giá ngày của WATCHLIST (174 mã) + VNINDEX qua vnstock
  2. Xử lý TỪNG phiên chưa xử lý (tự bù nếu lỡ ngày; nghỉ lễ thì không có phiên mới)
  3. Ghi DB: chỉ THÊM dòng hoặc ĐỔI TRẠNG THÁI — không xóa dữ liệu (DATA_SAFETY_RULES)
  4. Gửi tóm tắt Telegram (nếu cấu hình)

An toàn:
  - Mặc định chỉ chạy SQLite local. Staging: --target staging + biến LUK_DATABASE_URL.
  - Production bị chặn trừ khi có --target production --i-know-this-is-production.
  - Không xử lý phiên hôm nay trước 15:15 (tránh nến chưa đóng).
  - Phiên có < 80% mã có giá → dừng, không ghi (dữ liệu chưa đủ).

Chạy:
  python luk_daily_runner.py                         # SQLite local: luk_local.db
  python luk_daily_runner.py --target staging        # ghi DB staging (LUK_DATABASE_URL)
  python luk_daily_runner.py --backtest-from 2020-01-01   # backtest luật v1, không ghi DB

Biến môi trường:
  LUK_DATABASE_URL        DB đích (staging) — bắt buộc khi --target staging/production
  TELEGRAM_BOT_TOKEN      bot gửi tóm tắt (tuỳ chọn)
  LUK_TELEGRAM_CHAT_IDS   danh sách chat id, cách nhau dấu phẩy (Sơn, Vương)
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import luk_engine as LE  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VN_TZ = timezone(timedelta(hours=7))
RUNNER_VERSION = "1.0"

# WATCHLIST_172 (174 mã) — đồng bộ với scripts/daily_signal_scanner_eod.py (2026-10-01)
WATCHLIST = [
    'VCB', 'BID', 'CTG', 'VHM', 'VIC', 'VNM', 'HPG', 'TCB', 'VPB', 'MBB',
    'STB', 'MSN', 'FPT', 'SSI', 'GAS', 'PLX', 'MWG', 'VJC', 'HDB', 'ACB',
    'VRE', 'BCM', 'POW', 'SAB', 'SHB', 'LPB', 'VIB', 'EIB', 'BVH', 'GVR',
    'TPB', 'NVL', 'KDH', 'DGC', 'REE', 'VCI', 'HVN', 'DIG', 'GEX', 'VIX',
    'BSR', 'GMD', 'PNJ',
    'DPM', 'KBC', 'DXG', 'VPL', 'MSB', 'OCB', 'TCX',
    'HSG', 'DCM', 'HCM', 'VND', 'PC1', 'DGW', 'HDG', 'PVD', 'PVT', 'VTP',
    'SCS', 'TCH', 'NLG', 'CII', 'PDR', 'IDC', 'ANV', 'HAH', 'DBC', 'MCH',
    'CTD', 'HT1', 'VSC', 'BWE', 'PVS', 'VHC', 'SSB', 'FRT', 'ELC', 'BMI',
    'BSI', 'TV2', 'DPG', 'LCG', 'BAF',
    'TNG', 'KSB', 'MSH', 'SBT', 'VCG', 'CTR', 'SZC', 'PHR', 'GEG', 'PTB',
    'HAX', 'FMC', 'CSV', 'TCM', 'CMG', 'PAN', 'SGN', 'NTL', 'GIL', 'VFC',
    'IDI', 'AAA', 'TLH', 'HBC', 'VPG', 'CRE', 'CSM', 'ASM', 'HHS', 'PDC',
    'PAC', 'TAL', 'KOS', 'SIP', 'ORS', 'CMX', 'NBB', 'SMC', 'DCL', 'QCG',
    'SJS', 'NAF', 'HAG', 'NHA', 'EVF', 'VHG', 'HAP', 'ASG',
    'SHS', 'MBS', 'VFS', 'CEO', 'NVB', 'VCS', 'HUT', 'NDN', 'PLC', 'EVS',
    'PSI', 'VC3', 'BVS', 'BAB', 'TIG', 'APS', 'IPA', 'DXP', 'TVS', 'LIG',
    'VHE', 'VC7', 'DTT', 'KSV', 'HLD', 'OCH', 'PVI', 'MIG', 'PGB', 'DHT',
    'API', 'NRC', 'MBG', 'SJE', 'INN', 'NAG', 'SD9', 'AMV', 'IDJ',
    'SGB', 'VBB',
]
WATCHLIST = list(dict.fromkeys(WATCHLIST))

LOOKBACK_DAYS = 430          # đủ 252 phiên cho RS + đệm
MIN_COVERAGE = 0.80          # phiên phải có giá cho >= 80% mã
REQUEST_PAUSE = 3.5
RATE_LIMIT_WAIT = 65


def log(msg):
    print(f"[{datetime.now(VN_TZ).strftime('%H:%M:%S')}] {msg}", flush=True)


# =============================================================================
# TẢI DỮ LIỆU (vnstock, xử lý rate limit)
# =============================================================================
def _vn_history(symbol, start, end, source):
    try:
        from vnstock import Quote
        return Quote(symbol=symbol, source=source).history(start=start, end=end, interval="1D")
    except ImportError:
        from vnstock import Vnstock
        return Vnstock().stock(symbol=symbol, source=source).quote.history(start=start, end=end, interval="1D")


def _normalize(raw):
    df = raw.copy()
    df.columns = [c.lower() for c in df.columns]
    dc = "time" if "time" in df.columns else ("date" if "date" in df.columns else df.columns[0])
    df["date"] = pd.to_datetime(df[dc]).dt.tz_localize(None).dt.normalize()
    df = df[["date", "open", "high", "low", "close", "volume"]].dropna(subset=["close"])
    return df.drop_duplicates("date").sort_values("date").reset_index(drop=True)


def fetch_one(symbol, start, end):
    for source in ("VCI", "TCBS"):
        for attempt in range(4):
            try:
                raw = _vn_history(symbol, start, end, source)
                time.sleep(REQUEST_PAUSE)
                if raw is not None and len(raw):
                    return _normalize(raw)
                break
            except KeyboardInterrupt:
                raise
            except BaseException as ex:  # vnstock gọi sys.exit() khi rate limit
                msg = str(ex).lower()
                if isinstance(ex, SystemExit) or "rate" in msg or "quá nhiều" in msg or "too many" in msg:
                    log(f"  ⏳ rate limit {symbol}/{source} — chờ {RATE_LIMIT_WAIT}s")
                    time.sleep(RATE_LIMIT_WAIT)
                    continue
                time.sleep(REQUEST_PAUSE)
                break
    return None


def load_market_data(start, end, tickers=WATCHLIST):
    data = {}
    idx = fetch_one(LE.INDEX_SYMBOL, start, end)
    if idx is None or not len(idx):
        raise RuntimeError("Không tải được VNINDEX")
    data[LE.INDEX_SYMBOL] = idx
    for k, t in enumerate(tickers, 1):
        df = fetch_one(t, start, end)
        if df is not None and len(df) > 60:
            data[t] = df
        if k % 25 == 0:
            log(f"  tải {k}/{len(tickers)} mã")
    log(f"Đã tải {len(data) - 1}/{len(tickers)} mã + VNINDEX ({start} → {end})")
    return data


# =============================================================================
# DATABASE (chỉ INSERT / UPDATE — không xóa dữ liệu)
# =============================================================================
def make_engine(target, db_url=None, allow_prod=False):
    if target == "local":
        url = db_url or "sqlite:///luk_local.db"
    else:
        url = db_url or os.getenv("LUK_DATABASE_URL")
        if not url:
            sys.exit("Thiếu LUK_DATABASE_URL cho --target " + target)
        if target == "production" and not allow_prod:
            sys.exit("Chặn ghi production. Thêm --i-know-this-is-production nếu thật sự muốn.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, pool_pre_ping=True)


def ensure_tables(engine):
    pg = engine.dialect.name == "postgresql"
    ID = "SERIAL PRIMARY KEY" if pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    F = "DOUBLE PRECISION" if pg else "REAL"
    ddl = [
        """CREATE TABLE IF NOT EXISTS luk_meta (
            key VARCHAR(50) PRIMARY KEY, value TEXT)""",
        f"""CREATE TABLE IF NOT EXISTS luk_nav (
            trade_date VARCHAR(10) PRIMARY KEY, nav {F}, cash {F}, stock_value {F},
            exposure {F}, vnindex {F}, n_positions INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        f"""CREATE TABLE IF NOT EXISTS luk_positions (
            id {ID}, ticker VARCHAR(10) NOT NULL, entry_date VARCHAR(10) NOT NULL,
            status VARCHAR(10) NOT NULL, entry_price {F}, stop0 {F}, stop {F}, r_per_share {F},
            shares INTEGER, init_shares INTEGER, partial_done INTEGER, trail_on INTEGER,
            pending_exit VARCHAR(40), last_price {F}, pnl {F}, reasons VARCHAR(200),
            exit_date VARCHAR(10), exit_price {F}, hold_days INTEGER, ret_pct {F}, r_mult {F},
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (ticker, entry_date))""",
        f"""CREATE TABLE IF NOT EXISTS luk_orders (
            id {ID}, trade_date VARCHAR(10) NOT NULL, ticker VARCHAR(10) NOT NULL,
            side VARCHAR(6) NOT NULL, qty INTEGER, price {F}, reason VARCHAR(60),
            entry_date VARCHAR(10), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (trade_date, ticker, side, reason))""",
        f"""CREATE TABLE IF NOT EXISTS luk_signals (
            id {ID}, signal_date VARCHAR(10) NOT NULL, ticker VARCHAR(10) NOT NULL,
            close_price {F}, stop {F}, stop_pct {F}, rs {F},
            status VARCHAR(30) DEFAULT 'cho_mua', fill_date VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (signal_date, ticker))""",
    ]
    with engine.begin() as c:
        for q in ddl:
            c.execute(text(q))


def meta_get(c):
    return {k: v for k, v in c.execute(text("SELECT key, value FROM luk_meta")).fetchall()}


def meta_set(c, key, value):
    c.execute(text("""INSERT INTO luk_meta (key, value) VALUES (:k, :v)
                      ON CONFLICT (key) DO UPDATE SET value = excluded.value"""),
              {"k": key, "v": str(value)})


def load_state(c):
    m = meta_get(c)
    if "last_processed" not in m:
        return None, m
    st = LE.new_state()
    st["cash"], st["peak"], st["nav_prev"] = float(m["cash"]), float(m["peak"]), float(m["nav_prev"])
    rows = c.execute(text("SELECT * FROM luk_positions WHERE status = 'open'")).mappings().all()
    for p in rows:
        st["positions"][p["ticker"]] = dict(
            ticker=p["ticker"], entry_date=p["entry_date"], status="open",
            entry=p["entry_price"], stop=p["stop"], stop0=p["stop0"], R=p["r_per_share"],
            shares=int(p["shares"]), init_shares=int(p["init_shares"]),
            partial=bool(p["partial_done"]), trail_on=bool(p["trail_on"]),
            pending=p["pending_exit"] or None, pnl=float(p["pnl"] or 0),
            reasons=[x for x in (p["reasons"] or "").split("+") if x], last=p["last_price"])
    sig = c.execute(text("""SELECT signal_date, ticker, close_price, stop, stop_pct, rs FROM luk_signals
                            WHERE signal_date = :d AND status = 'cho_mua'"""),
                    {"d": m["last_processed"]}).mappings().all()
    st["pending_signals"] = [dict(signal_date=s["signal_date"], ticker=s["ticker"], close=s["close_price"],
                                  stop=s["stop"], stop_pct=s["stop_pct"], rs=s["rs"]) for s in sig]
    for t, d in c.execute(text("""SELECT ticker, MAX(exit_date) FROM luk_positions
                                  WHERE status = 'closed' AND pnl < 0 GROUP BY ticker""")).fetchall():
        st["last_loss_exit"][t] = d
    return st, m


UPSERT_POS = """INSERT INTO luk_positions
 (ticker, entry_date, status, entry_price, stop0, stop, r_per_share, shares, init_shares,
  partial_done, trail_on, pending_exit, last_price, pnl, reasons, exit_date, exit_price,
  hold_days, ret_pct, r_mult, updated_at)
 VALUES (:ticker, :entry_date, :status, :entry, :stop0, :stop, :R, :shares, :init_shares,
  :partial, :trail_on, :pending, :last, :pnl, :reasons, :exit_date, :exit_price,
  :hold_days, :ret_pct, :r_mult, CURRENT_TIMESTAMP)
 ON CONFLICT (ticker, entry_date) DO UPDATE SET
  status = excluded.status, entry_price = excluded.entry_price, stop0 = excluded.stop0,
  stop = excluded.stop, r_per_share = excluded.r_per_share, shares = excluded.shares,
  init_shares = excluded.init_shares, partial_done = excluded.partial_done,
  trail_on = excluded.trail_on, pending_exit = excluded.pending_exit,
  last_price = excluded.last_price, pnl = excluded.pnl, reasons = excluded.reasons,
  exit_date = excluded.exit_date, exit_price = excluded.exit_price,
  hold_days = excluded.hold_days, ret_pct = excluded.ret_pct, r_mult = excluded.r_mult,
  updated_at = CURRENT_TIMESTAMP"""


def _pos_row(p):
    return dict(ticker=p["ticker"], entry_date=p["entry_date"], status=p.get("status", "open"),
                entry=float(p["entry"]), stop0=float(p["stop0"]), stop=float(p["stop"]), R=float(p["R"]),
                shares=int(p["shares"]), init_shares=int(p["init_shares"]),
                partial=int(bool(p["partial"])), trail_on=int(bool(p["trail_on"])),
                pending=p.get("pending"), last=float(p["last"]), pnl=float(p["pnl"]),
                reasons="+".join(p["reasons"])[:200], exit_date=p.get("exit_date"),
                exit_price=p.get("exit_price"), hold_days=p.get("hold_days"),
                ret_pct=p.get("ret_pct"), r_mult=p.get("r_mult"))


def persist_day(c, state, ev):
    for o in ev["orders"]:
        c.execute(text("""INSERT INTO luk_orders (trade_date, ticker, side, qty, price, reason, entry_date)
                          VALUES (:trade_date, :ticker, :side, :qty, :price, :reason, :entry_date)
                          ON CONFLICT (trade_date, ticker, side, reason) DO NOTHING"""), o)
    for _, p in ev["closed"]:
        c.execute(text(UPSERT_POS), _pos_row(p))
    for p in state["positions"].values():
        c.execute(text(UPSERT_POS), _pos_row(p))
    for u in ev["signal_updates"]:
        c.execute(text("""UPDATE luk_signals SET status = :status, fill_date = :fill_date
                          WHERE signal_date = :signal_date AND ticker = :ticker"""), u)
    for s in ev["new_signals"]:
        c.execute(text("""INSERT INTO luk_signals (signal_date, ticker, close_price, stop, stop_pct, rs)
                          VALUES (:signal_date, :ticker, :close, :stop, :stop_pct, :rs)
                          ON CONFLICT (signal_date, ticker) DO NOTHING"""), s)
    c.execute(text("""INSERT INTO luk_nav (trade_date, nav, cash, stock_value, exposure, vnindex, n_positions)
                      VALUES (:trade_date, :nav, :cash, :stock_value, :exposure, :vnindex, :n_positions)
                      ON CONFLICT (trade_date) DO NOTHING"""), ev["nav"])
    meta_set(c, "cash", state["cash"])
    meta_set(c, "peak", state["peak"])
    meta_set(c, "nav_prev", state["nav_prev"])
    meta_set(c, "last_processed", ev["date"])
    meta_set(c, "last_run_at", datetime.now(VN_TZ).isoformat(timespec="seconds"))


# =============================================================================
# CHẠY
# =============================================================================
def processable_dates(P, data, after, asof=None):
    """Các phiên > after, đã đóng cửa và đủ dữ liệu."""
    now = datetime.now(VN_TZ)
    today = pd.Timestamp(now.date())
    cutoff_today = now.hour * 60 + now.minute >= 15 * 60 + 15
    out = []
    n_t = len(P["tickers"])
    for i, d in enumerate(P["dates"]):
        if i == 0 or (after and d <= pd.Timestamp(after)):
            continue
        if asof and d > pd.Timestamp(asof):
            break
        if d > today or (d == today and not cutoff_today):
            break
        cover = np.isfinite(P["C"][i]).sum() / max(n_t, 1)
        if cover < MIN_COVERAGE:
            log(f"⚠️  Phiên {d.date()} chỉ có giá {cover:.0%} mã — dừng, chờ lần chạy sau")
            break
        out.append(i)
    return out


def known_corporate_actions(engine):
    """Đọc hệ số quyền từ bảng corporate_actions (nếu DB có). Không có thì bỏ qua."""
    try:
        with engine.connect() as c:
            rows = c.execute(text("SELECT ticker, ex_date, factor FROM corporate_actions "
                                  "WHERE factor IS NOT NULL")).fetchall()
        out = {}
        for t, d, f in rows:
            out.setdefault(t, []).append((pd.Timestamp(d), float(f)))
        return out
    except Exception:
        return {}


def run(engine, loader, asof=None, notify=True):
    ensure_tables(engine)
    with engine.connect() as c:
        state, meta = load_state(c)

    end = (pd.Timestamp(asof) if asof else pd.Timestamp(datetime.now(VN_TZ).date()))
    anchor = pd.Timestamp(meta.get("last_processed", end.strftime("%Y-%m-%d")))
    if state and state["positions"]:
        anchor = min([anchor] + [pd.Timestamp(p["entry_date"]) for p in state["positions"].values()])
    start = (anchor - pd.Timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    data = loader(start, end.strftime("%Y-%m-%d"))
    P = LE.build_panel(data, known_ca=known_corporate_actions(engine))

    all_events = []
    if state is None:
        # KHỞI TẠO: phiên đóng cửa gần nhất = ngày bắt đầu; chỉ quét tín hiệu, mua từ phiên sau
        idxs = processable_dates(P, data, None, asof)
        if not idxs:
            log("Chưa có phiên hợp lệ để khởi tạo.")
            return []
        i = idxs[-1]
        state = LE.new_state()
        D = LE._ds(P["dates"][i])
        ev = {"date": D, "orders": [], "closed": [], "adjusted": [], "signal_updates": [], "new_signals": [],
              "nav": dict(trade_date=D, nav=state["cash"], cash=state["cash"], stock_value=0.0, exposure=0.0,
                          vnindex=float(P["index_close"][i]), n_positions=0)}
        sig = []
        for j in np.flatnonzero(P["SIG"][i]):
            cc, stp = P["C"][i, j], P["STOP"][i, j]
            sig.append(dict(signal_date=D, ticker=P["tickers"][j], close=float(cc), stop=float(stp),
                            stop_pct=float((cc - stp) / cc * 100), rs=float(P["RS"][i, j])))
        ev["new_signals"] = sorted(sig, key=lambda x: -x["rs"])
        state["pending_signals"] = [dict(x) for x in ev["new_signals"]]
        with engine.begin() as c:
            meta_set(c, "inception_date", D)
            meta_set(c, "capital", LE.RULES.capital)
            meta_set(c, "rules_version", LE.RULES_VERSION)
            meta_set(c, "rules_json", json.dumps(LE.rules_dict()))
            persist_day(c, state, ev)
        log(f"✅ Khởi tạo LUK Model Portfolio ngày {D} · {len(sig)} tín hiệu chờ mua phiên sau")
        all_events.append(ev)
    else:
        if meta.get("rules_version") != LE.RULES_VERSION:
            sys.exit(f"Luật đã đổi ({meta.get('rules_version')} → {LE.RULES_VERSION}). "
                     "Forward test phải dùng luật cố định — tạo danh mục mới thay vì chạy tiếp.")
        for i in processable_dates(P, data, meta["last_processed"], asof):
            ev = LE.process_day(state, P, i)
            with engine.begin() as c:
                persist_day(c, state, ev)
            log(f"✅ {ev['date']}: NAV {ev['nav']['nav']/1e6:,.1f} tr · "
                f"{sum(o['side'] == 'BUY' for o in ev['orders'])} mua · "
                f"{sum(o['side'] == 'SELL' for o in ev['orders'])} bán · {len(ev['new_signals'])} tín hiệu mới")
            all_events.append(ev)
        if not all_events:
            log("Không có phiên mới (cuối tuần / nghỉ lễ / chưa hết phiên).")
    if notify and all_events:
        send_telegram(all_events[-1], state)
    return all_events


# =============================================================================
# TELEGRAM
# =============================================================================
REASON_VI = {
    "cat_lo": "chạm cắt lỗ", "cat_lo_gap": "mở cửa dưới cắt lỗ", "thung_ema21": "thủng EMA21",
    "giu_toi_da": "giữ tối đa 60 phiên", "mua_pullback": "mua pullback",
}


def _reason(r):
    if r.startswith("chot_1_3"):
        return "chốt 1/3 ở +3R"
    if r.startswith("dieu_chinh_quyen"):
        return "điều chỉnh quyền"
    return REASON_VI.get(r, r)


def build_message(ev, state):
    n = ev["nav"]
    cap = LE.RULES.capital
    lines = [f"<b>📈 LUK Model Portfolio · {ev['date']}</b> (staging)",
             f"NAV: <b>{n['nav']/1e6:,.1f} tr</b> ({(n['nav']/cap-1)*100:+.2f}%) · "
             f"CP {n['exposure']*100:.0f}% · {n['n_positions']} mã"]
    buys = [o for o in ev["orders"] if o["side"] == "BUY"]
    sells = [o for o in ev["orders"] if o["side"] == "SELL"]
    if buys:
        lines.append("\n<b>🟢 Mua</b>")
        lines += [f"• {o['ticker']} {o['qty']:,} cp @ {o['price']:,.0f}" for o in buys]
    if sells:
        lines.append("\n<b>🔴 Bán</b>")
        lines += [f"• {o['ticker']} {o['qty']:,} cp @ {o['price']:,.0f} — {_reason(o['reason'])}" for o in sells]
    for t, p in ev["closed"]:
        lines.append(f"  ↳ {t} đóng: {p['ret_pct']:+.1f}% ({p['r_mult']:+.2f}R)")
    if ev["adjusted"]:
        lines.append("\n⚠️ Điều chỉnh quyền: " + ", ".join(f"{a['ticker']} x{a['factor']}" for a in ev["adjusted"]))
    if ev["new_signals"]:
        lines.append("\n<b>⏳ Chờ mua phiên tới (giá mở cửa)</b>")
        lines += [f"• {s['ticker']} · cắt lỗ {s['stop']:,.0f} ({s['stop_pct']:.1f}%) · RS {s['rs']:.0f}"
                  for s in ev["new_signals"][:5]]
    lines.append("\n<i>Danh mục mô phỏng — công cụ hỗ trợ, không phải tư vấn đầu tư.</i>")
    return "\n".join(lines)


def send_telegram(ev, state):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    ids = [x.strip() for x in os.getenv("LUK_TELEGRAM_CHAT_IDS", "").split(",") if x.strip()]
    if not token or not ids:
        return
    try:
        import requests
        msg = build_message(ev, state)
        for cid in ids:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": cid, "text": msg, "parse_mode": "HTML"}, timeout=15)
    except Exception as e:
        log(f"Telegram lỗi (bỏ qua): {e}")


# =============================================================================
# MAIN
# =============================================================================
def main():
    global REQUEST_PAUSE
    ap = argparse.ArgumentParser(description="LUK Model Portfolio — chạy hằng ngày")
    ap.add_argument("--target", choices=["local", "staging", "production"], default="local")
    ap.add_argument("--db-url", default=None)
    ap.add_argument("--i-know-this-is-production", action="store_true")
    ap.add_argument("--asof", default=None, help="Chỉ xử lý đến ngày này (bù dữ liệu / kiểm thử)")
    ap.add_argument("--pause", type=float, default=3.5)
    ap.add_argument("--no-telegram", action="store_true")
    ap.add_argument("--backtest-from", default=None, help="Backtest luật v1 từ ngày này, không ghi DB")
    a = ap.parse_args()
    REQUEST_PAUSE = a.pause

    log(f"LUK runner {RUNNER_VERSION} · {LE.RULES_VERSION} · target={a.target}")
    if a.backtest_from:
        end = datetime.now(VN_TZ).strftime("%Y-%m-%d")
        start = (pd.Timestamp(a.backtest_from) - pd.Timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
        P = LE.build_panel(load_market_data(start, end))
        state, events = LE.replay(P, a.backtest_from)
        closed = [p for ev in events for _, p in ev["closed"]]
        print(json.dumps(LE.summarize(closed, [ev["nav"] for ev in events]), ensure_ascii=False, indent=2))
        pd.DataFrame(closed).to_csv("luk_v1_backtest_trades.csv", index=False, encoding="utf-8-sig")
        log("Đã lưu luk_v1_backtest_trades.csv")
        return

    engine = make_engine(a.target, a.db_url, a.i_know_this_is_production)
    run(engine, load_market_data, asof=a.asof, notify=not a.no_telegram)


if __name__ == "__main__":
    main()
