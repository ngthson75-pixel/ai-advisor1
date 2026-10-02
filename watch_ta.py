"""
AI ADVISOR - WATCH TA (phân tích kỹ thuật cho Giám sát danh mục VIP)
====================================================================
File: watch_ta.py
Version: 2.4b (2026-10-02) — chân nền = giá thấp nhất KỂ CẢ RÂU của các phiên chạm nền (khớp MBB thật: 19.600, thủng 02/10)
Version: 2.4 (2026-10-02) — thêm THỦNG NỀN GIÁ (vùng nhiều lần về rồi bật lên trong 1 năm), cả trong phiên lẫn cuối ngày
Version: 1.0 (2026-10-01)

Module THUẦN (không Flask, không DB) — nhận chuỗi nến ngày và trả về:
  - các mốc cản / hỗ trợ (đỉnh-đáy nổi bật 1 năm, đỉnh cũ, MA50/100/200, mốc admin nhập tay)
  - các BIẾN CỐ của phiên (chỉ khi có thay đổi đột biến) kèm GỢI Ý HÀNH ĐỘNG 2 kịch bản

Nến: list dict theo thời gian tăng dần {date:'YYYY-MM-DD', open, high, low, close, volume}, giá VND.

Biến cố (EOD — sau phiên, giá đóng cửa đã xác nhận):
  BREAKDOWN    Thủng hỗ trợ: đóng cửa dưới hỗ trợ >= 1%
  TOP_SELL     Bán lớn ở đỉnh: KL >= 2x TB20 + giảm >= 3% hoặc râu trên dài, tại vùng đỉnh 6 tháng / đỉnh cũ
  FAILED_BREAKOUT  Đã đóng cửa trên đỉnh cũ trong 10 phiên gần đây, nay rơi lại dưới đỉnh cũ >= 1%
  (v2.2: bỏ SELL_VOLUME giữa nhịp và NEAR_RESIST tự động — chỉ còn mốc admin nhập tay; không đề xuất tỷ lệ bán)
  SHARP_DROP   Giảm >= 5% trong phiên (khi không có biến cố nặng hơn cho mã đó)
  NEAR_PEAK    Chạm vùng đỉnh cũ (±2% quanh đỉnh lớn nhất 1 năm, trừ 10 phiên gần nhất)
  NEAR_RESIST  Áp sát vùng cản (cách <= 3%) hoặc chạm cản trong phiên rồi bị đẩy xuống
  BREAKOUT     Vượt cản >= 1% với KL >= 1,5x TB20
Biến cố trong phiên (10h30–14h30):
  INTRADAY     Giảm >= 5% so với giá đóng cửa hôm trước, hoặc thủng hỗ trợ > 2%
  NEAR_PEAK cũng được kiểm tra trong phiên (giá hiện tại) để báo kịp lúc giá chạm đỉnh cũ
  (Không cảnh báo 'tăng nóng/quá mua' — triết lý: cắt lỗ nhanh, giữ lãi lâu nhất có thể)
"""

import math

PIVOT_WIN      = 10      # đỉnh/đáy nổi bật = cao/thấp nhất trong ±10 phiên (~1 tháng)
LOOKBACK       = 250     # ~1 năm giao dịch
CLUSTER_TOL    = 0.02    # gộp các mốc cách nhau <= 2%
NEAR_PCT       = 3.0     # áp sát cản (khớp cách đọc của admin: BSR 31,9 vs cản ~33)
PEAK_ZONE_PCT  = 2.0     # vùng đỉnh cũ
BREAK_PCT      = 1.0     # vượt / thủng xác nhận
VOL_SPIKE      = 2.0     # bán đột biến
VOL_BREAKOUT   = 1.5     # vượt cản cần KL
SHARP_PCT      = 5.0     # giảm mạnh
INTRADAY_BREAK = 2.0     # thủng hỗ trợ trong phiên
LIQ_SHARE      = 0.15    # mỗi phiên chỉ nên bán <= 15% KL TB
MIN_BARS       = 60

SEVERITY = {'BASE_BREAK': 1, 'TOP_SELL': 1, 'FAILED_BREAKOUT': 1, 'BREAKDOWN': 1, 'INTRADAY': 1, 'SELL_VOLUME': 2, 'SYSTEM_SELL': 2, 'SHARP_DROP': 2,
            'MARKET': 3, 'NEAR_PEAK': 3, 'NEAR_RESIST': 4, 'GIVEBACK': 4, 'BREAKOUT': 5, 'CONCENTRATION': 5}
EMOJI = {'BASE_BREAK': '🔴', 'TOP_SELL': '🔴', 'FAILED_BREAKOUT': '🔴', 'BREAKDOWN': '🔴', 'INTRADAY': '⚡', 'SELL_VOLUME': '🔴', 'SYSTEM_SELL': '🔔', 'SHARP_DROP': '📉',
         'MARKET': '🌐', 'NEAR_PEAK': '🟡', 'NEAR_RESIST': '🟠', 'GIVEBACK': '💰', 'BREAKOUT': '🟢',
         'CONCENTRATION': '🎯'}


# ------------------------------------------------------------------ format
def fp(v):
    """Giá kiểu Việt Nam: 33900 -> '33.900'."""
    if v is None:
        return '—'
    return f"{round(v / 50) * 50:,.0f}".replace(',', '.') if v >= 10000 else f"{round(v / 10) * 10:,.0f}".replace(',', '.')


def fpct(v, sign=True):
    if v is None:
        return '—'
    s = f"{v:+.1f}" if sign else f"{abs(v):.1f}"
    return s.replace('.', ',') + '%'


def fqty(v):
    return f"{int(v):,}".replace(',', '.')


def _month(d):
    try:
        return f"{int(str(d)[5:7])}/{str(d)[:4]}"
    except Exception:
        return str(d)[:7]


# ------------------------------------------------------------------ indicators
def sma(vals, n):
    return sum(vals[-n:]) / n if len(vals) >= n else None


def rsi(closes, n=14):
    """RSI Wilder (như TradingView)."""
    if len(closes) < n + 1:
        return None
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0); losses += max(-d, 0)
    ag, al = gains / n, losses / n
    for i in range(n + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * (n - 1) + max(d, 0)) / n
        al = (al * (n - 1) + max(-d, 0)) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def bollinger(closes, n=20, k=2.0):
    if len(closes) < n:
        return None
    w = closes[-n:]
    m = sum(w) / n
    sd = (sum((x - m) ** 2 for x in w) / n) ** 0.5
    return m, m + k * sd, m - k * sd


def avg_volume(bars, n=20, exclude_last=True):
    vs = [b['volume'] for b in (bars[:-1] if exclude_last else bars)][-n:]
    vs = [v for v in vs if v]
    return sum(vs) / len(vs) if vs else None


def pivots(bars, win=PIVOT_WIN):
    out = []
    hs, ls = [b['high'] for b in bars], [b['low'] for b in bars]
    for i in range(win, len(bars) - win):
        if hs[i] == max(hs[i - win:i + win + 1]):
            out.append({'price': hs[i], 'date': bars[i]['date'], 'kind': 'H'})
        if ls[i] == min(ls[i - win:i + win + 1]):
            out.append({'price': ls[i], 'date': bars[i]['date'], 'kind': 'L'})
    return out


def _cluster(pts, tol=CLUSTER_TOL):
    pts = sorted(pts, key=lambda p: p['price'])
    groups = []
    for p in pts:
        if groups and p['price'] <= groups[-1][0]['price'] * (1 + tol):
            groups[-1].append(p)
        else:
            groups.append([p])
    return groups


def find_levels(bars, manual=None):
    """
    Mốc giá từ dữ liệu ĐẾN HẾT bars (không gồm phiên đang xét — hàm gọi tự cắt).
    Trả list {price, lo, hi, touches, label, source} sắp theo giá.
    """
    bars = bars[-LOOKBACK:]
    levels = []
    for g in _cluster(pivots(bars)):
        prices = [p['price'] for p in g]
        last = max(g, key=lambda p: p['date'])
        kinds = {p['kind'] for p in g}
        if kinds == {'H'}:
            label = f"đỉnh tháng {_month(last['date'])}"
        elif kinds == {'L'}:
            label = f"đáy tháng {_month(last['date'])}"
        else:
            label = f"vùng đỉnh/đáy cũ tháng {_month(last['date'])}"
        levels.append({'price': sum(prices) / len(prices), 'lo': min(prices), 'hi': max(prices),
                       'touches': len(g), 'label': label, 'source': 'pivot'})
    closes = [b['close'] for b in bars]
    for n in (50, 100, 200):
        m = sma(closes, n)
        if m:
            levels.append({'price': m, 'lo': m, 'hi': m, 'touches': 0, 'label': f"MA{n}", 'source': 'ma'})
    for m in manual or []:
        p = float(m['price'])
        # mốc admin nhập tay THAY THẾ mốc tự động gần nó (±2%) — kế hoạch đã thống nhất với khách được ưu tiên
        levels = [l for l in levels if l['source'] == 'manual' or abs(l['price'] / p - 1) > CLUSTER_TOL]
        levels.append({'price': p, 'lo': p, 'hi': p, 'touches': 0,
                       'label': m.get('note') or 'mốc theo dõi', 'source': 'manual'})
    return sorted(levels, key=lambda l: l['price'])


def nearest(levels, price, above=True, prefer_manual=True):
    """Mốc gần nhất phía trên (cản) / dưới (hỗ trợ). Mốc admin nhập tay được ưu tiên khi gần tương đương (<1%)."""
    cands = [l for l in levels if (l['price'] > price if above else l['price'] < price)]
    if not cands:
        return None
    cands.sort(key=lambda l: abs(l['price'] - price))
    best = cands[0]
    if prefer_manual:
        for l in cands[1:]:
            if l['source'] == 'manual' and abs(l['price'] - best['price']) / best['price'] < 0.01:
                return l
    return best


def key_levels(levels):
    """Mốc đủ mạnh để BÁO: đỉnh/đáy nổi bật, mốc admin, MA200. MA50/MA100 chỉ dùng tham khảo (quá dày, gây nhiễu)."""
    return [l for l in levels if l['source'] != 'ma' or l['label'] == 'MA200']


PEAK_MIN_AGE   = 40      # đỉnh cũ phải cách >= 40 phiên (~2 tháng)
PEAK_PULLBACK  = 10.0    # và sau đỉnh giá đã điều chỉnh >= 10% (nếu không: chỉ là cổ phiếu đang lập đỉnh mới)


def old_peak(bars):
    """Đỉnh lớn nhất ~1 năm đã CŨ (>= 40 phiên) và đã có nhịp điều chỉnh >= 10% sau đó."""
    hist = bars[-LOOKBACK:-PEAK_MIN_AGE]
    if len(hist) < 30:
        return None
    i = max(range(len(hist)), key=lambda k: hist[k]['high'])
    peak = hist[i]['high']
    after = bars[len(bars) - len(bars[-LOOKBACK:]) + i + 1:]
    if not after or min(x['close'] for x in after) > peak * (1 - PEAK_PULLBACK / 100):
        return None
    return {'price': peak, 'date': hist[i]['date']}


def _zone_txt(l):
    if l['hi'] - l['lo'] > l['price'] * 0.004:
        return f"{fp(l['lo'])}–{fp(l['hi'])}"
    return fp(l['price'])


def _lvl_txt(l):
    return f"{_zone_txt(l)} ({l['label']})"


# ------------------------------------------------------------------ action helpers
PEAK_TOP_SHARE = 0.65    # đỉnh cũ phải ở phần trên (>= 65%) biên độ đóng cửa 1 năm: giữ đỉnh T5 BSR (~34 trong biên 24–40), loại đỉnh đi ngang giữa nhịp
PEAK_NEAR_PCT  = 3.0     # "về vùng đỉnh cũ" = cách đỉnh cũ <= 3%
FAIL_LOOKBACK  = 10      # vượt đỉnh cũ trong 10 phiên gần đây rồi rơi lại = vượt đỉnh thất bại
TOP_SELL_VOL   = 2.0     # bán lớn ở đỉnh: KL >= 2x TB20
TOP_SELL_DROP  = 3.0     #   và giảm >= 3% (hoặc nến râu trên dài)
TOP_ZONE_PCT   = 3.0     #   tại vùng đỉnh: giá cao nhất phiên cách đỉnh 6 tháng / đỉnh cũ <= 3%
CHOICE         = "tỷ lệ tùy anh/chị"


def _body_top(b):
    return max(b['open'], b['close'])


def peak_levels(bars, win=PIVOT_WIN):
    """
    ĐỈNH CŨ = vùng 'trần' tạo bởi các đỉnh THÂN NẾN (không tính râu) trong ~1 năm, gộp các đỉnh cách nhau <= 2%,
    và chỉ giữ vùng nằm ở phần trên của biên độ (để không gọi các đỉnh nhỏ giữa nhịp giảm là 'đỉnh cũ').
    Trả list {price (trần vùng), lo, touches, label} sắp theo giá.
    """
    bars = bars[-LOOKBACK:]
    if len(bars) < 2 * win + 5:
        return []
    tops = [_body_top(b) for b in bars]
    pts = [{'price': tops[i], 'date': bars[i]['date'], 'kind': 'H'}
           for i in range(win, len(bars) - win) if tops[i] == max(tops[i - win:i + win + 1])]
    closes = [b['close'] for b in bars]
    lo_c, hi_c = min(closes), max(closes)
    floor = lo_c + PEAK_TOP_SHARE * (hi_c - lo_c)
    out = []
    for g in _cluster(pts):
        top = max(p['price'] for p in g)
        if top < floor:
            continue
        months = sorted({_month(p['date']) for p in g}, key=lambda m: (m.split('/')[1], int(m.split('/')[0])))
        out.append({'price': top, 'lo': min(p['price'] for p in g), 'touches': len(g),
                    'label': 'đỉnh cũ tháng ' + ', '.join(months[-3:])})
    return sorted(out, key=lambda l: l['price'])


BASE_WIN       = 5       # đáy thân nến = thấp nhất trong ±5 phiên (nền đi ngang có nhiều nhịp chạm ngắn)
BASE_BOUNCE    = 3.0     # sau mỗi lần chạm phải bật lên >= 3% trong 15 phiên
BASE_TOUCHES   = 3       # nền giá = >= 3 lần về rồi bật lên
BASE_SPAN      = 40      # các lần chạm trải >= 40 phiên (~2 tháng) — không phải 1 nhịp tích lũy ngắn
BASE_HELD      = 20      # trước khi thủng, nền phải giữ được >= 20 phiên (đóng cửa trên chân nền)
BASE_BREAK_PCT = 0.3     # thủng nền = giá dưới chân nền >= 0,3% (~1 bước giá)


def _body_bot(b):
    return min(b['open'], b['close'])


def base_levels(bars, win=BASE_WIN):
    """
    NỀN GIÁ = vùng giá cổ phiếu NHIỀU LẦN về rồi bật lên trong ~1 năm (đáy THÂN NẾN, không tính râu —
    để nhịp rũ bỏ râu dài kiểu 'spring' không kéo nền xuống). Gộp các lần chạm cách nhau <= 2%.
    Trả list {price (= chân nền: giá thấp nhất kể cả râu của các phiên chạm nền), hi, touches, label} sắp theo giá giảm dần.
    """
    bars = bars[-LOOKBACK:]
    n = len(bars)
    if n < 2 * win + 20:
        return []
    bots = [_body_bot(b) for b in bars]
    closes = [b['close'] for b in bars]
    pts = []
    for i in range(win, n - win):
        if bots[i] != min(bots[i - win:i + win + 1]):
            continue
        after = closes[i + 1:i + 16]
        if after and max(after) >= bots[i] * (1 + BASE_BOUNCE / 100):
            pts.append({'price': bots[i], 'low': bars[i]['low'], 'date': bars[i]['date'], 'i': i, 'kind': 'L'})
    # gộp kiểu chuỗi: mỗi lần chạm cách lần liền kề <= 1,5%, cả vùng rộng <= 4% (nền thường hơi xô lệch theo thời gian)
    groups = []
    for p in sorted(pts, key=lambda p: p['price']):
        if groups and p['price'] <= groups[-1][-1]['price'] * 1.015 and p['price'] <= groups[-1][0]['price'] * 1.04:
            groups[-1].append(p)
        else:
            groups.append([p])
    out = []
    for g in groups:
        idx = sorted(p['i'] for p in g)
        if len(g) < BASE_TOUCHES or idx[-1] - idx[0] < BASE_SPAN:
            continue
        months = sorted({_month(p['date']) for p in g}, key=lambda m: (m.split('/')[1], int(m.split('/')[0])))
        span = months[0] if len(months) == 1 else f"{months[0]} – {months[-1]}"
        # CHÂN NỀN = giá thấp nhất (tính cả râu) của các phiên chạm nền — mức mà mọi lần về nền đều giữ được.
        # (Nhịp rũ bỏ sâu kiểu 'spring' nằm ngoài cụm nên không kéo chân nền xuống.)
        out.append({'price': min(p['low'] for p in g), 'hi': max(p['price'] for p in g), 'touches': len(g),
                    'label': f"{len(g)} lần về nền rồi bật lên, tháng {span}"})
    return sorted(out, key=lambda l: -l['price'])


def _base_txt(b):
    rng = f"{fp(b['price'])}–{fp(b['hi'])}" if b['hi'] > b['price'] * 1.004 else fp(b['price'])
    return f"nền giá {rng} ({b['label']})"


def base_break(bars, price, prev_close):
    """Nền giá vừa bị thủng: giá < chân nền -0,3%, trong khi ~1 tháng qua (20 phiên) giá vẫn đóng cửa trên ngưỡng đó
    (nền đang giữ — không báo lại khi giá đã lình xình quanh/dưới nền). Lấy nền cao nhất."""
    recent = min([b['close'] for b in bars[-BASE_HELD:]] + [prev_close])
    for b in base_levels(bars):
        lim = b['price'] * (1 - BASE_BREAK_PCT / 100)
        if price < lim <= recent:
            return b
    return None


def _fraction(weight):
    """Không còn đề xuất tỷ lệ cụ thể (để khách tự chọn) — giữ hàm cho tương thích."""
    return CHOICE


def _liquidity_note(pos, avg_vol, fraction=None):
    """Vị thế lớn so với thanh khoản -> nhắc chia nhiều phiên khi bán."""
    if not pos or not avg_vol or not pos.get('qty'):
        return None
    per_session = avg_vol * LIQ_SHARE
    if pos['qty'] <= per_session * 3:
        return None
    n = math.ceil(pos['qty'] / per_session)
    return (f"Nếu bán: thanh khoản ~{fqty(round(avg_vol, -3))} cp/phiên → mỗi phiên nên ≤ {fqty(round(per_session, -2))} cp "
            f"để không đè giá (bán toàn bộ vị thế cần ~{n} phiên)")


def _ctx(pos):
    """Dòng bối cảnh vị thế: lãi/lỗ + tỷ trọng."""
    if not pos:
        return ''
    parts = []
    if pos.get('pl_pct') is not None:
        parts.append(f"{'lãi' if pos['pl_pct'] >= 0 else 'lỗ'} {fpct(abs(pos['pl_pct']), sign=False)}")
    if pos.get('weight') is not None:
        parts.append(f"tỷ trọng {fpct(pos['weight'], sign=False)}")
    return ('Vị thế: ' + ', '.join(parts) + '.') if parts else ''


# ------------------------------------------------------------------ EOD detection
def detect_eod(ticker, bars, pos=None, manual=None, intraday=False):
    """
    Biến cố của phiên cuối cùng trong bars. pos = {qty, pl_pct, weight} (tùy chọn).
    Trả (events, info). Mỗi event: {type, ticker, key, level, price, headline, context, actions[], short}

    Tín hiệu BÁN (theo phương pháp của admin — chart POW 2026):
      TOP_SELL         Bán lớn ở đỉnh: KL >= 2x TB20 + giảm mạnh / râu trên dài, ngay tại vùng đỉnh
      FAILED_BREAKOUT  Vượt đỉnh cũ rồi thất bại: đã đóng cửa trên đỉnh cũ trong 10 phiên, nay rơi lại dưới
      NEAR_PEAK        Về vùng đỉnh cũ: cân nhắc chốt lời từng phần
    BASE_BREAK       Thủng nền giá: đóng cửa dưới vùng giá đã nhiều lần về rồi bật lên trong 1 năm
    Rủi ro: BREAKDOWN (thủng hỗ trợ), SHARP_DROP (giảm >= 5%). Tích cực: BREAKOUT (vượt cản có KL).
    Mốc admin nhập tay: NEAR_RESIST (áp sát mốc theo dõi).
    Không đề xuất tỷ lệ bán cụ thể — khách tự chọn.
    """
    if len(bars) < MIN_BARS:
        return [], {'skip': f'chỉ có {len(bars)} phiên dữ liệu (cần >= {MIN_BARS})'}
    today, prev = bars[-1], bars[-2]
    hist = bars[:-1]                                   # mốc tính trên dữ liệu ĐẾN HÔM QUA
    c, pc = today['close'], prev['close']
    chg = (c / pc - 1) * 100 if pc else 0.0
    av = avg_volume(bars)
    vr = (today['volume'] / av) if av and today.get('volume') else None
    levels = find_levels(hist, manual)
    key = key_levels(levels)
    res_prev = nearest(key, pc, above=True)
    sup_prev = nearest(key, pc, above=False)
    res = nearest(key, c, above=True)
    sup = nearest(key, c, above=False)
    peaks = peak_levels(bars[:-(FAIL_LOOKBACK + 1)])   # đỉnh cũ đã hình thành TRƯỚC nhịp hiện tại
    pl = (pos or {}).get('pl_pct')
    profit = pl is None or pl >= 0
    ctx = _ctx(pos)
    ev = []
    vol_txt = f", KL gấp {str(round(vr, 1)).replace('.', ',')} lần TB20" if vr and vr >= 1.3 else ''
    head_px = f"<b>{ticker}</b> {fp(c)} ({fpct(chg)})"
    liq = _liquidity_note(pos, av)

    def add(t, key_, level, headline, actions, short=None):
        ev.append({'type': t, 'ticker': ticker, 'key': key_, 'level': level, 'price': c, 'chg': chg,
                   'headline': headline, 'context': ctx, 'actions': [a for a in actions if a],
                   'short': short or headline})

    def has(*types):
        return any(e['type'] in types for e in ev)

    # 1) BÁN LỚN Ở ĐỈNH
    top6m = max(b['high'] for b in hist[-120:])
    near_peak_hi = any(abs(today['high'] / p['price'] - 1) * 100 <= TOP_ZONE_PCT for p in peaks)
    at_top = today['high'] >= top6m * (1 - TOP_ZONE_PCT / 100) or near_peak_hi
    rng = today['high'] - today['low']
    wick = rng > 0 and (today['high'] - max(today['open'], c)) / rng >= 0.5 and c <= today['open']
    if at_top and vr is not None and vr >= TOP_SELL_VOL and (chg <= -TOP_SELL_DROP or (wick and chg <= 0)):
        drop_from_high = (c / today['high'] - 1) * 100
        add('TOP_SELL', f"TOP_SELL:{today['date']}", today['high'],
            f"{head_px} — <b>bán lớn ở vùng đỉnh</b>: KL gấp {str(round(vr, 1)).replace('.', ',')} lần TB20, "
            f"rút từ {fp(today['high'])} về {fp(c)} ({fpct(drop_from_high)})",
            [("Tín hiệu phân phối tại đỉnh — cân nhắc chốt lời từng phần (" + CHOICE + ")") if profit
             else ("Tín hiệu phân phối tại đỉnh — cân nhắc hạ tỷ trọng (" + CHOICE + ")"),
             f"Các phiên tới đóng cửa dưới {fp(today['low'])} (đáy phiên bán lớn) → tín hiệu bán được xác nhận",
             "Không mua thêm ở vùng giá này",
             liq],
            short=f"<b>{ticker}</b> {fp(c)} — bán lớn ở vùng đỉnh (KL x{str(round(vr, 1)).replace('.', ',')}): cân nhắc chốt lời từng phần")

    # 2) VƯỢT ĐỈNH CŨ THẤT BẠI
    recent = bars[-(FAIL_LOOKBACK + 1):-1]
    for p in sorted(peaks, key=lambda x: -x['price']):
        P = p['price']
        was_above = [b for b in recent if b['close'] >= P * (1 + BREAK_PCT / 100)]
        if was_above and pc >= P * (1 - BREAK_PCT / 100) and c < P * (1 - BREAK_PCT / 100):
            add('FAILED_BREAKOUT', f"FAILED_BREAKOUT:{round(P, -2)}", P,
                f"{head_px} — <b>vượt đỉnh cũ thất bại</b>: rơi lại dưới {fp(P)} ({p['label']}) "
                f"sau khi đã vượt lên tới {fp(max(b['high'] for b in recent))}{vol_txt}",
                [("Tín hiệu bán — cân nhắc chốt lời (" + CHOICE + ")") if profit
                 else ("Tín hiệu bán — cân nhắc hạ tỷ trọng (" + CHOICE + ")"),
                 f"Lấy lại {fp(P * (1 + BREAK_PCT / 100))} với KL lớn → tín hiệu bán bị hủy",
                 liq],
                short=f"<b>{ticker}</b> {fp(c)} — vượt đỉnh cũ {fp(P)} thất bại: tín hiệu bán")
            break

    # 3a) THỦNG NỀN GIÁ (vùng nhiều lần về rồi bật lên trong 1 năm)
    bb = base_break(hist, c, pc) if not has('FAILED_BREAKOUT') else None
    if bb:
        nxt = nearest(key, c, above=False)
        strong = vr is not None and vr >= VOL_BREAKOUT
        add('BASE_BREAK', f"BASE_BREAK:{round(bb['price'], -2)}", bb['price'],
            f"{head_px} — <b>đóng cửa thủng {_base_txt(bb)}</b>{vol_txt}" + (" — xác nhận bằng khối lượng" if strong else ""),
            ["Tín hiệu hạ tỷ trọng (" + CHOICE + ")" + (" — vị thế đang lỗ, ưu tiên bảo vệ phần vốn còn lại" if pl is not None and pl < 0 else ""),
             liq,
             f"Rút chân lấy lại {fp(bb['price'])} trong 1–2 phiên (rũ bỏ) → tạm dừng bán, đánh giá lại",
             f"Hỗ trợ tiếp theo: {_lvl_txt(nxt)}" if nxt else "Không còn vùng hỗ trợ nào trong 1 năm — rủi ro giảm sâu cao hơn"],
            short=f"<b>{ticker}</b> {fp(c)} — thủng nền giá {fp(bb['price'])}: tín hiệu hạ tỷ trọng")

    # 3) THỦNG HỖ TRỢ
    broke = not bb and sup_prev and pc >= sup_prev['price'] * (1 - BREAK_PCT / 100) and c <= sup_prev['price'] * (1 - BREAK_PCT / 100)
    if broke and not has('FAILED_BREAKOUT'):
        nxt = nearest(key, c, above=False)
        strong = vr is not None and vr >= VOL_BREAKOUT
        add('BREAKDOWN', f"BREAKDOWN:{round(sup_prev['price'], -2)}", sup_prev['price'],
            f"{head_px} thủng hỗ trợ {_lvl_txt(sup_prev)}{vol_txt}" + (" — tín hiệu xấu được xác nhận bằng khối lượng" if strong else ""),
            ["Cân nhắc giảm tỷ trọng (" + CHOICE + ")" + (" — vị thế đang lỗ, ưu tiên bảo vệ phần vốn còn lại" if pl is not None and pl < 0 else ""),
             liq,
             f"Hồi lại trên {fp(sup_prev['price'])} → tạm dừng bán, đánh giá lại",
             f"Hỗ trợ tiếp theo: {_lvl_txt(nxt)}" if nxt else "Không còn vùng hỗ trợ nào trong 1 năm — rủi ro giảm sâu cao hơn"],
            short=f"<b>{ticker}</b> {fp(c)} — thủng hỗ trợ {_zone_txt(sup_prev)}: cân nhắc giảm tỷ trọng")

    # 4) GIẢM MẠNH (khi chưa có tín hiệu nặng hơn)
    if chg <= -SHARP_PCT and not has('TOP_SELL', 'FAILED_BREAKOUT', 'BREAKDOWN', 'BASE_BREAK'):
        add('SHARP_DROP', 'SHARP_DROP', None, f"{head_px} giảm mạnh trong phiên{vol_txt}",
            [f"Giữ bình tĩnh, chưa bán đuổi; mốc cần giữ: {_lvl_txt(sup)}" if sup else "Theo dõi phiên tới trước khi quyết định",
             f"Đóng cửa dưới {fp(sup['price'] * (1 - BREAK_PCT / 100))} → cân nhắc giảm tỷ trọng" if sup else None])

    # 5) VƯỢT CẢN CÓ KHỐI LƯỢNG (tích cực)
    if (res_prev and pc <= res_prev['price'] * (1 + BREAK_PCT / 100) and c >= res_prev['price'] * (1 + BREAK_PCT / 100)
            and vr is not None and vr >= VOL_BREAKOUT and not has('TOP_SELL')):
        nxt = nearest(key, c, above=True)
        add('BREAKOUT', f"BREAKOUT:{round(res_prev['price'], -2)}", res_prev['price'],
            f"{head_px} vượt cản {_lvl_txt(res_prev)}{vol_txt}",
            ["Giữ vị thế — xu hướng đang được xác nhận",
             f"Dời điểm dừng lên ~{fp(res_prev['lo'] * 0.97)} (ngay dưới vùng cản vừa vượt)",
             f"Rơi lại dưới {fp(res_prev['price'] * (1 - BREAK_PCT / 100))} trong vài phiên tới → vượt cản thất bại, cân nhắc bán",
             f"Cản tiếp theo: {_lvl_txt(nxt)}" if nxt else None],
            short=f"<b>{ticker}</b> {fp(c)} — vượt cản {_zone_txt(res_prev)}: giữ, dời điểm dừng lên ~{fp(res_prev['lo'] * 0.97)}")

    # 6) VỀ VÙNG ĐỈNH CŨ → chốt lời từng phần
    if not has('TOP_SELL', 'FAILED_BREAKOUT', 'BREAKDOWN', 'BASE_BREAK', 'BREAKOUT') and chg > -SHARP_PCT:
        above = [p for p in peaks if p['price'] * (1 + PEAK_ZONE_PCT / 100) >= c]   # gồm cả lúc vừa nhú qua đỉnh <= 2%
        P = min(above, key=lambda p: p['price']) if above else None
        if P and (P['price'] - c) / P['price'] * 100 <= PEAK_NEAR_PCT:
            testing = c >= P['price']
            add('NEAR_PEAK', f"NEAR_PEAK:{round(P['price'], -2)}", P['price'],
                f"{head_px} " + ("chạm / đang thử vượt " if testing else "về vùng ") + f"đỉnh cũ {fp(P['price'])} ({P['label'].replace('đỉnh cũ ', '')}){vol_txt}",
                ([("Cân nhắc chốt lời từng phần (" + CHOICE + ")") if profit
                  else f"Đang lỗ: vùng đỉnh cũ là cơ hội giảm tỷ trọng ({CHOICE})",
                  f"Phần còn lại: giữ được trên {fp(P['price'])} 2–3 phiên với KL tốt → tiếp tục giữ, dời điểm dừng lên ~{fp(P['price'] * 0.95)}",
                  f"Rơi lại dưới {fp(P['price'] * (1 - BREAK_PCT / 100))} → tín hiệu bán (vượt đỉnh thất bại)"]
                 if testing else
                 [("Cân nhắc chốt lời từng phần (" + CHOICE + ")") if profit
                  else "Đang lỗ: vùng đỉnh cũ là cơ hội giảm tỷ trọng (" + CHOICE + ")",
                  f"Vượt {fp(P['price'] * (1 + BREAK_PCT / 100))} với KL lớn → giữ phần còn lại, dời điểm dừng lên ~{fp(P['price'] * 0.95)}",
                  f"Vượt lên rồi rơi lại dưới {fp(P['price'] * (1 - BREAK_PCT / 100))} → tín hiệu bán (vượt đỉnh thất bại)"]),
                short=(f"<b>{ticker}</b> {fp(c)} — chạm đỉnh cũ {fp(P['price'])}: cân nhắc chốt lời từng phần, rơi lại dưới thì bán"
                       if testing else f"<b>{ticker}</b> {fp(c)} — về vùng đỉnh cũ {fp(P['price'])}: cân nhắc chốt lời từng phần"))
            ev[-1]['testing'] = testing

    # 7) MỐC THEO DÕI ADMIN NHẬP TAY (kế hoạch đã thống nhất với khách)
    if not ev:
        man = [l for l in levels if l['source'] == 'manual' and l['price'] > c]
        m = min(man, key=lambda l: l['price']) if man else None
        if m and (m['price'] - c) / m['price'] * 100 <= NEAR_PCT:
            add('NEAR_RESIST', f"NEAR_RESIST:{round(m['price'], -2)}", m['price'],
                f"{head_px} áp sát mốc theo dõi {_lvl_txt(m)}",
                [("Theo kế hoạch: cân nhắc chốt lời từng phần (" + CHOICE + ")") if profit
                 else ("Theo kế hoạch: cân nhắc giảm tỷ trọng (" + CHOICE + ") nếu không vượt"),
                 f"Vượt {fp(m['price'] * (1 + BREAK_PCT / 100))} với KL lớn → giữ, theo dõi mốc tiếp theo"],
                short=f"<b>{ticker}</b> {fp(c)} — áp sát mốc theo dõi {fp(m['price'])}")

    if intraday:
        # Trong phiên chỉ dùng tín hiệu tính được từ GIÁ (chưa có KL/đỉnh-đáy phiên chính xác)
        ev = [e for e in ev if e['type'] == 'NEAR_PEAK']
        for e in ev:
            e['headline'] += " <i>(trong phiên, giá tạm tính)</i>"
    near_pk = min([p for p in peaks if p['price'] >= c], key=lambda p: p['price'], default=None)
    info = {'close': c, 'chg': round(chg, 2), 'vol_ratio': round(vr, 2) if vr else None,
            'resistance': res, 'support': sup, 'levels': levels, 'peaks': peaks,
            'peak': {'price': near_pk['price'], 'date': near_pk['label']} if near_pk else None}
    return ev, info


# ------------------------------------------------------------------ intraday detection
def detect_intraday(ticker, bars, price, pos=None, manual=None):
    """Trong phiên: so giá hiện tại với nến đã đóng gần nhất (bars[-1] = hôm qua)."""
    if len(bars) < MIN_BARS or not price:
        return []
    pc = bars[-1]['close']
    chg = (price / pc - 1) * 100
    sup = nearest(key_levels(find_levels(bars, manual)), pc, above=False)
    broke = sup and price <= sup['price'] * (1 - INTRADAY_BREAK / 100) and pc >= sup['price']
    # Phía TĂNG: tăng nóng / về vùng đỉnh cũ — dựng nến tạm của phiên từ giá hiện tại
    from datetime import date as _date
    tmp = {'date': _date.today().isoformat(), 'open': pc, 'high': max(pc, price), 'low': min(pc, price),
           'close': price, 'volume': 0}
    up = detect_eod(ticker, bars + [tmp], pos, manual, intraday=True)[0] if chg > 0 else []
    # Phía GIẢM: thủng nền giá ngay trong phiên → báo sớm, chờ xem cuối phiên có rút chân không
    bb = base_break(bars, price, pc) if chg < 0 else None
    if bb:
        pl = (pos or {}).get('pl_pct')
        nxt = nearest(key_levels(find_levels(bars, manual)), price, above=False)
        return [{'type': 'BASE_BREAK', 'ticker': ticker, 'key': f"BASE_BREAK_I:{round(bb['price'], -2)}", 'level': bb['price'],
                 'price': price, 'chg': chg,
                 'headline': f"<b>{ticker}</b> {fp(price)} ({fpct(chg)}) — <b>thủng {_base_txt(bb)}</b> <i>(trong phiên, giá tạm tính)</i>",
                 'context': _ctx(pos),
                 'actions': [a for a in [f"Cuối phiên không rút chân (đóng cửa dưới {fp(bb['price'])}) → điểm hạ tỷ trọng ({CHOICE})"
                             + (" — vị thế đang lỗ, ưu tiên bảo vệ vốn" if pl is not None and pl < 0 else ""),
                             f"Rút chân đóng cửa lại trên {fp(bb['price'])} → nền giá vẫn giữ, chưa cần bán",
                             _liquidity_note(pos, avg_volume(bars, exclude_last=False)),
                             f"Hỗ trợ tiếp theo: {_lvl_txt(nxt)}" if nxt else None] if a],
                 'short': f"<b>{ticker}</b> {fp(price)} — thủng nền giá {fp(bb['price'])} trong phiên: cuối phiên không rút chân → hạ tỷ trọng"}]
    if chg > -SHARP_PCT and not broke:
        return up
    what = f"giảm {fpct(abs(chg), sign=False)} so với hôm qua" + (f", xuyên hỗ trợ {_lvl_txt(sup)}" if broke else "")
    return [{'type': 'INTRADAY', 'ticker': ticker, 'key': 'INTRADAY', 'level': sup['price'] if sup else None,
             'price': price, 'chg': chg,
             'headline': f"<b>{ticker}</b> {fp(price)} — {what} (trong phiên)",
             'context': _ctx(pos),
             'actions': [f"Chờ giá đóng cửa: đóng cửa dưới {fp(sup['price'] * (1 - BREAK_PCT / 100))} → cân nhắc giảm tỷ trọng"
                         if sup else "Chờ giá đóng cửa trước khi quyết định",
                         "Tránh bán tháo giữa phiên khi thanh khoản mỏng"]}]
