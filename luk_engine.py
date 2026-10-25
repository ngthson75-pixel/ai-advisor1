#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LUK ENGINE — lõi chiến lược "LUK Model Portfolio" (Luk Pullback 9/21)
=====================================================================
Version : LUK-PB v1.0 (2026-10-14) — LUẬT ĐÓNG BĂNG cho forward test.
          KHÔNG sửa tham số trong Rules khi đang forward test; muốn đổi
          thì tăng RULES_VERSION và khởi tạo danh mục mới.

Dùng chung bởi:
  - luk_daily_runner.py   (chạy hằng ngày sau phiên, ghi DB staging)
  - luk_portfolio_api.py  (chỉ đọc, không import file này)

Luật v1 = cấu hình core đã backtest (expectancy +0,34R) + 3 sửa đổi
từ phân tích 86 lệnh:
  (1) bỏ giới hạn 60 phiên cho vị thế đã chốt 1/3 (để siêu cổ phiếu chạy)
  (2) cắt lỗ dưới đáy 3 phiên (thay vì 5), tối đa 7%
  (3) không mua lại mã vừa thua trong 10 phiên

Trình tự mỗi phiên D (giống hệt backtest):
  1. Bán: lệnh chờ bán (giá mở cửa) → cắt lỗ (gap: giá mở cửa / chạm: giá cắt lỗ)
     → chốt 1/3 ở +3R. Chỉ bán được khi đã đủ T+2.
  2. Mua: tín hiệu phiên D-1, mua giá mở cửa phiên D, sizing 1% NAV rủi ro.
  3. Cuối phiên: cập nhật trailing EMA21 / giữ tối đa → lệnh chờ bán phiên sau; NAV.
  4. Quét tín hiệu mới ở giá đóng cửa D → chờ mua phiên D+1.
"""
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

RULES_VERSION = "LUK-PB v1.0 (2026-10-14)"
INDEX_SYMBOL = "VNINDEX"


@dataclass(frozen=True)
class Rules:
    capital: float = 1_000_000_000      # vốn mô phỏng 1 tỷ

    # 1. Chọn mã
    min_value_bn: float = 10.0          # GTGD TB 20 phiên >= 10 tỷ
    min_adr: float = 2.5                # biên độ dao động ngày TB >= 2,5%
    rs_min: float = 90.0                # RS top 10% trong rổ

    # 2. Setup
    run_min: float = 0.25               # đã có sóng tăng >= 25%
    pb_min: float = 0.04                # điều chỉnh 4%..20% từ đỉnh 30 phiên
    pb_max: float = 0.20
    touch_tol: float = 0.02             # đáy 3 phiên chạm vùng EMA21 (+2%)
    quiet_ratio: float = 0.90           # KL 5 phiên < 90% KL 50 phiên

    # 3. Kích hoạt
    trigger_vol: float = 1.0            # KL phiên kích hoạt >= KL TB 20 phiên
    max_gap: float = 0.03               # không mua đuổi khi mở cửa gap > 3%

    # 4. Rủi ro
    stop_lookback: int = 3              # v1: đáy 3 phiên
    min_stop: float = 0.02
    max_stop: float = 0.07              # v1: cắt lỗ tối đa 7%
    risk_pct: float = 0.01              # rủi ro 1% NAV/lệnh
    max_weight: float = 0.30
    max_pos: int = 5
    cooldown: int = 10                  # v1: không mua lại mã vừa thua trong 10 phiên

    # 5. Thoát
    partial_r: float = 3.0
    partial_frac: float = 1 / 3
    trail_start_r: float = 1.0
    trail_ema: int = 21
    max_hold: int = 60                  # v1: chỉ áp dụng khi CHƯA chốt 1/3

    # Quy tắc VN
    buy_fee: float = 0.0015
    sell_fee: float = 0.0015
    sell_tax: float = 0.001
    settle_days: int = 2
    lock_move: float = 0.065


RULES = Rules()


def rules_dict():
    return asdict(RULES)


# =============================================================================
# DỮ LIỆU
# =============================================================================
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def normalize_units(df, is_index=False):
    """vnstock (VCI) trả giá cổ phiếu theo nghìn đồng → đổi ra đồng."""
    df = df.sort_values("date").reset_index(drop=True).copy()
    if not is_index and len(df) and df["close"].median() < 500:
        for k in ["open", "high", "low", "close"]:
            df[k] = df[k] * 1000
    return df


def adjust_corporate_actions(df, known=None, auto_ratio=0.85, tol=0.06):
    """Điều chỉnh lùi giá lịch sử tại ngày GDKHQ.
    - known: [(ex_date, factor)] từ bảng corporate_actions (nếu có) — chỉ áp dụng
      khi dữ liệu thật sự còn khoảng gap tương ứng (tránh điều chỉnh 2 lần).
    - auto: giá mở cửa < 85% đóng cửa phiên trước (vượt mọi biên độ sàn)
      → chắc chắn là quyền, factor ≈ mở cửa / đóng cửa trước.
    Trả về (df_đã_điều_chỉnh, [(ngày, factor, nguồn)])."""
    df = df.copy()
    if len(df) < 2:
        return df, []
    prev = df["close"].shift(1)
    ratio = (df["open"] / prev).to_numpy()
    known_map = {pd.Timestamp(d).normalize(): float(f) for d, f in (known or []) if f}
    events = []
    cols = ["open", "high", "low", "close"]
    for k in range(1, len(df)):
        r = ratio[k]
        if not np.isfinite(r) or r <= 0:
            continue
        d = pd.Timestamp(df.at[k, "date"]).normalize()
        f = src = None
        if d in known_map and abs(r - known_map[d]) <= tol:
            f, src = known_map[d], "corporate_actions"
        elif r < auto_ratio:
            f, src = float(r), "auto_gap"
        if f:
            df.loc[: k - 1, cols] = df.loc[: k - 1, cols] * f
            df.loc[: k - 1, "volume"] = df.loc[: k - 1, "volume"] / f
            events.append((d, f, src))
    return df, events


def compute_features(df, r=RULES):
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
    f = pd.DataFrame(index=df.index)
    f["e9"], f["e21"], f["e50"] = ema(c, 9), ema(c, 21), ema(c, 50)
    f["etrail"] = ema(c, r.trail_ema)
    f["adr"] = ((h / l) - 1).rolling(20).mean() * 100
    f["value_bn"] = (c * v).rolling(20).mean() / 1e9
    f["rs_raw"] = (0.4 * c.pct_change(63) + 0.2 * c.pct_change(126)
                   + 0.2 * c.pct_change(189) + 0.2 * c.pct_change(252))

    run_up = h.rolling(30).max() / l.shift(30).rolling(60).min() - 1
    hh30 = h.rolling(30).max()
    pb_prev = 1 - c.shift(1) / hh30.shift(1)
    trend = (f["e21"] > f["e50"]) & (f["e50"] > f["e50"].shift(10)) & (c > f["e50"])
    touch = l.rolling(3).min() <= f["e21"] * (1 + r.touch_tol)
    quiet = v.rolling(5).mean().shift(1) < v.rolling(50).mean().shift(1) * r.quiet_ratio
    setup = (run_up >= r.run_min) & pb_prev.between(r.pb_min, r.pb_max) & trend & touch & quiet
    trigger = (c > h.shift(1)) & (c > f["e9"]) & (v >= v.rolling(20).mean() * r.trigger_vol)

    f["setup_trig"] = (setup & trigger).fillna(False)
    f["stop"] = l.rolling(r.stop_lookback).min() * 0.997
    return f


def build_panel(data, r=RULES, known_ca=None):
    """data: {ticker: df(date, open, high, low, close, volume)} có VNINDEX.
    known_ca: {ticker: [(ex_date, factor)]}"""
    idx = normalize_units(data[INDEX_SYMBOL], is_index=True).set_index("date")
    idx = idx[~idx.index.duplicated()]
    dates = pd.DatetimeIndex(idx.index)
    tickers = sorted(t for t in data if t != INDEX_SYMBOL)
    keys = ["open", "high", "low", "close", "etrail", "adr", "value_bn", "rs_raw", "setup_trig", "stop"]
    cols = {k: {} for k in keys}
    ca_events = {}
    for t in tickers:
        raw = normalize_units(data[t])
        adj, ev = adjust_corporate_actions(raw, (known_ca or {}).get(t))
        for d, fct, src in ev:
            ca_events[(t, d)] = (fct, src)
        f = compute_features(adj, r)
        # GIAO DỊCH dùng giá THẬT (raw). Chỉ báo/tín hiệu dùng chuỗi đã điều chỉnh;
        # cắt lỗ & EMA trailing quy đổi về giá thật của chính ngày đó (M = adj/raw).
        m = (adj["close"] / raw["close"]).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        f["etrail"] = f["etrail"] / m
        f["stop"] = f["stop"] / m
        df = pd.concat([raw, f], axis=1).set_index("date")
        df = df[~df.index.duplicated()].reindex(dates)
        for k in keys:
            cols[k][t] = df[k]
    P = {k: pd.DataFrame(v, index=dates, columns=tickers) for k, v in cols.items()}

    eligible = (P["value_bn"] >= r.min_value_bn) & (P["adr"] >= r.min_adr) & P["rs_raw"].notna()
    rs = P["rs_raw"].where(eligible).rank(axis=1, pct=True) * 100
    sig = P["setup_trig"].fillna(False).astype(bool) & eligible & (rs >= r.rs_min)

    arr = lambda k: P[k].to_numpy(dtype=float)
    return {
        "dates": dates, "tickers": tickers,
        "tidx": {t: j for j, t in enumerate(tickers)},
        "didx": {d: i for i, d in enumerate(dates)},
        "O": arr("open"), "H": arr("high"), "L": arr("low"), "C": arr("close"),
        "TR": arr("etrail"), "STOP": arr("stop"),
        "RS": rs.to_numpy(dtype=float), "SIG": sig.to_numpy(dtype=bool),
        "index_close": idx["close"].to_numpy(dtype=float),
        "ca_events": ca_events,
    }


# =============================================================================
# TRẠNG THÁI & XỬ LÝ 1 PHIÊN
# =============================================================================
def new_state(r=RULES):
    return {"cash": float(r.capital), "peak": float(r.capital), "nav_prev": float(r.capital),
            "positions": {}, "pending_signals": [], "last_loss_exit": {}}


def _ds(d):
    return pd.Timestamp(d).strftime("%Y-%m-%d")


def _sessions_between(P, d_from, i_to):
    """Số phiên từ ngày d_from đến chỉ số i_to (theo lịch VNINDEX)."""
    i_from = int(np.searchsorted(P["dates"], pd.Timestamp(d_from)))
    return i_to - i_from


def process_day(state, P, i, r=RULES):
    """Xử lý phiên thứ i. Sửa state tại chỗ, trả về sự kiện để ghi DB/thông báo."""
    O, H, L, C, TR, STOP, RS, SIG = (P[k] for k in ["O", "H", "L", "C", "TR", "STOP", "RS", "SIG"])
    d = P["dates"][i]
    D = _ds(d)
    tidx = P["tidx"]
    sell_cost = r.sell_fee + r.sell_tax
    ev = {"date": D, "orders": [], "closed": [], "adjusted": [], "signal_updates": [], "new_signals": []}
    pos = state["positions"]

    # ---- 0. Điều chỉnh quyền cho vị thế/tín hiệu đang mở ----
    for t, p in pos.items():
        ca = P["ca_events"].get((t, d))
        if ca:
            f = ca[0]
            for k in ["entry", "stop", "stop0", "R", "last"]:
                p[k] *= f
            p["shares"] = int(round(p["shares"] / f))
            p["init_shares"] = int(round(p["init_shares"] / f))
            ev["adjusted"].append(dict(ticker=t, factor=round(f, 4), source=ca[1]))
            ev["orders"].append(dict(trade_date=D, ticker=t, side="ADJ", qty=p["shares"],
                                     price=round(p["entry"]), reason=f"dieu_chinh_quyen x{f:.4f}",
                                     entry_date=p["entry_date"]))
    for s in state["pending_signals"]:
        ca = P["ca_events"].get((s["ticker"], d))
        if ca:
            s["stop"] *= ca[0]

    def sell(t, qty, price, reason):
        p = pos[t]
        state["cash"] += qty * price * (1 - sell_cost)
        p["pnl"] += qty * (price * (1 - sell_cost) - p["entry"] * (1 + r.buy_fee))
        p["shares"] -= qty
        p["reasons"].append(reason)
        ev["orders"].append(dict(trade_date=D, ticker=t, side="SELL", qty=int(qty),
                                 price=round(price), reason=reason, entry_date=p["entry_date"]))
        if p["shares"] <= 0:
            cost0 = p["init_shares"] * p["entry"] * (1 + r.buy_fee)
            closed = dict(ticker=t, entry_date=p["entry_date"], exit_date=D, exit_price=round(price),
                          hold_days=_sessions_between(P, p["entry_date"], i),
                          pnl=round(p["pnl"]), ret_pct=round(p["pnl"] / cost0 * 100, 2),
                          r_mult=round(p["pnl"] / (p["init_shares"] * p["R"]), 2),
                          exit_reason="+".join(p["reasons"]))
            p["status"] = "closed"
            p.update(exit_date=D, exit_price=round(price), hold_days=closed["hold_days"],
                     ret_pct=closed["ret_pct"], r_mult=closed["r_mult"])
            ev["closed"].append((t, dict(p)))
            if p["pnl"] < 0:
                state["last_loss_exit"][t] = D
            del pos[t]

    # ---- 1. BÁN (mở cửa / trong phiên) ----
    for t in list(pos):
        p = pos[t]
        j = tidx.get(t)
        if j is None:
            continue
        if _sessions_between(P, p["entry_date"], i) < r.settle_days:
            continue                                   # T+2 chưa có hàng
        o, h, l, c, pc = O[i, j], H[i, j], L[i, j], C[i, j], C[i - 1, j]
        if np.isnan(o):
            continue                                   # tạm ngừng giao dịch
        if h == l and c <= pc * (1 - r.lock_move):
            continue                                   # sàn trắng bên mua
        if p["pending"]:
            sell(t, p["shares"], o, p["pending"]); continue
        if o <= p["stop"]:
            sell(t, p["shares"], o, "cat_lo_gap"); continue
        if l <= p["stop"]:
            sell(t, p["shares"], p["stop"], "cat_lo"); continue
        if r.partial_r > 0 and not p["partial"]:
            tgt = p["entry"] + r.partial_r * p["R"]
            if h >= tgt:
                qty = int(p["shares"] * r.partial_frac // 100 * 100)
                if qty >= 100:
                    sell(t, qty, max(o, tgt), f"chot_1_3_{r.partial_r:g}R")
                p["partial"] = True

    # ---- 2. MUA (giá mở cửa, tín hiệu phiên trước) ----
    nav_prev = state["nav_prev"]
    for s in sorted(state["pending_signals"], key=lambda x: -x["rs"]):
        t = s["ticker"]
        j = tidx.get(t)
        status = None
        if t in pos:
            status = "bo_qua:dang_giu"
        elif len(pos) >= r.max_pos:
            status = "bo_qua:du_5_ma"
        elif t in state["last_loss_exit"] and \
                _sessions_between(P, state["last_loss_exit"][t], i) <= r.cooldown:
            status = "bo_qua:vua_thua"
        elif j is None or np.isnan(O[i, j]) or np.isnan(C[i - 1, j]):
            status = "bo_qua:khong_co_gia"
        else:
            o, pc, stop = O[i, j], C[i - 1, j], s["stop"]
            dist = (o - stop) / o
            if o > pc * (1 + r.max_gap):
                status = "bo_qua:gap_tang"
            elif H[i, j] == L[i, j] and o >= pc * (1 + r.lock_move):
                status = "bo_qua:tran_khoa"
            elif not (r.min_stop <= dist <= r.max_stop):
                status = "bo_qua:cat_lo_xa"
            else:
                shares = nav_prev * r.risk_pct / (o - stop)
                shares = min(shares, nav_prev * r.max_weight / o, state["cash"] / (o * (1 + r.buy_fee)))
                shares = int(shares // 100 * 100)
                if shares < 100:
                    status = "bo_qua:het_tien"
                else:
                    state["cash"] -= shares * o * (1 + r.buy_fee)
                    pos[t] = dict(ticker=t, entry_date=D, status="open", entry=float(o), stop=float(stop),
                                  stop0=float(stop), R=float(o - stop), shares=shares, init_shares=shares,
                                  partial=False, trail_on=False, pending=None, pnl=0.0, reasons=[],
                                  last=float(o))
                    ev["orders"].append(dict(trade_date=D, ticker=t, side="BUY", qty=shares,
                                             price=round(o), reason="mua_pullback", entry_date=D))
                    status = "da_mua"
        ev["signal_updates"].append(dict(signal_date=s["signal_date"], ticker=t, status=status, fill_date=D))
    state["pending_signals"] = []

    # ---- 3. CUỐI PHIÊN ----
    mv = 0.0
    for t, p in pos.items():
        j = tidx.get(t)
        c = C[i, j] if j is not None else np.nan
        if not np.isnan(c):
            p["last"] = float(c)
            if c >= p["entry"] + r.trail_start_r * p["R"]:
                p["trail_on"] = True
            if p["trail_on"] and not np.isnan(TR[i, j]) and c < TR[i, j] and not p["pending"]:
                p["pending"] = f"thung_ema{r.trail_ema}"
            if not p["partial"] and _sessions_between(P, p["entry_date"], i) >= r.max_hold \
                    and not p["pending"]:
                p["pending"] = "giu_toi_da"
        mv += p["shares"] * p["last"]
    nav = state["cash"] + mv
    state["peak"] = max(state["peak"], nav)
    state["nav_prev"] = nav
    ev["nav"] = dict(trade_date=D, nav=nav, cash=state["cash"], stock_value=mv,
                     exposure=mv / nav if nav else 0.0, vnindex=float(P["index_close"][i]),
                     n_positions=len(pos))

    # ---- 4. TÍN HIỆU MỚI (giá đóng cửa D → mua phiên sau) ----
    new = []
    for j in np.flatnonzero(SIG[i]):
        t = P["tickers"][j]
        if t in pos:
            continue
        c, stop = C[i, j], STOP[i, j]
        new.append(dict(signal_date=D, ticker=t, close=float(c), stop=float(stop),
                        stop_pct=float((c - stop) / c * 100), rs=float(RS[i, j])))
    new.sort(key=lambda x: -x["rs"])
    state["pending_signals"] = [dict(x) for x in new]
    ev["new_signals"] = new
    return ev


def replay(P, start, end=None, r=RULES):
    """Chạy liên tục trong bộ nhớ (dùng cho backtest luật v1 và kiểm thử)."""
    state = new_state(r)
    dates = P["dates"]
    i0 = max(int(np.searchsorted(dates, pd.Timestamp(start))), 1)
    i1 = len(dates) if end is None else int(np.searchsorted(dates, pd.Timestamp(end), side="right"))
    events = [process_day(state, P, i, r) for i in range(i0, i1)]
    return state, events


def summarize(closed_rows, nav_rows, capital=RULES.capital):
    """Thống kê từ danh sách lệnh đã đóng + chuỗi NAV (list dict)."""
    out = {"n_closed": len(closed_rows)}
    if nav_rows:
        nav = pd.Series([x["nav"] for x in nav_rows])
        vni = pd.Series([x["vnindex"] for x in nav_rows])
        out.update(ret_pct=round((nav.iloc[-1] / capital - 1) * 100, 2),
                   vnindex_pct=round((vni.iloc[-1] / vni.iloc[0] - 1) * 100, 2),
                   max_dd_pct=round(((nav / nav.cummax()) - 1).min() * 100, 2),
                   exposure_avg_pct=round(float(np.mean([x["exposure"] for x in nav_rows])) * 100, 1))
    if closed_rows:
        df = pd.DataFrame(closed_rows)
        w, l = df[df.pnl > 0], df[df.pnl <= 0]
        gl = -l.pnl.sum()
        out.update(win_rate=round(len(w) / len(df) * 100, 1),
                   avg_win_pct=round(w.ret_pct.mean(), 2) if len(w) else 0.0,
                   avg_loss_pct=round(l.ret_pct.mean(), 2) if len(l) else 0.0,
                   expectancy_r=round(df.r_mult.mean(), 2),
                   profit_factor=round(w.pnl.sum() / gl, 2) if gl > 0 else None,
                   best_r=round(df.r_mult.max(), 2))
    return out
