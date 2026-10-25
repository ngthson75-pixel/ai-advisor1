# -*- coding: utf-8 -*-
"""
LUK PORTFOLIO API — chỉ ĐỌC dữ liệu LUK Model Portfolio (v1.0, 2026-10-14)
==========================================================================
Routes:
  GET /api/luk/portfolio   JSON (cần key)
  GET /luk                 Trang theo dõi cho admin (nhập key 1 lần)

Bảo vệ: biến môi trường LUK_VIEW_KEY. Gửi qua header X-LUK-Key hoặc ?key=.
Không ghi/xóa gì trong DB.

Đăng ký trong backend_api.py (graceful import, giống các module khác):
    try:
        from luk_portfolio_api import init_luk_routes
        init_luk_routes(app, engine)
    except Exception as _luk_err:
        print(f"⚠️  LUK routes not loaded: {_luk_err}")
"""
import hmac
import os
from datetime import datetime

from flask import Response, jsonify, request
from sqlalchemy import text

TARGET_TRADES = 30          # tiêu chí đánh giá: 30 lệnh đóng
TARGET_MONTHS = 6           #   hoặc 6 tháng
MAX_DD_LIMIT = -15.0        # max drawdown không vượt -15%


def _authorized():
    key = os.getenv("LUK_VIEW_KEY", "")
    got = request.headers.get("X-LUK-Key") or request.args.get("key") or ""
    return bool(key) and hmac.compare_digest(key, got)


def _rows(c, sql, **kw):
    return [dict(r) for r in c.execute(text(sql), kw).mappings().all()]


def _stats(closed, nav, capital):
    out = {"n_closed": len(closed)}
    if nav:
        navs = [x["nav"] for x in nav]
        peak, mdd = navs[0], 0.0
        for v in navs:
            peak = max(peak, v)
            mdd = min(mdd, v / peak - 1)
        v0, v1 = nav[0]["vnindex"], nav[-1]["vnindex"]
        out.update(nav=navs[-1], ret_pct=round((navs[-1] / capital - 1) * 100, 2),
                   vnindex_pct=round((v1 / v0 - 1) * 100, 2) if v0 else None,
                   max_dd_pct=round(mdd * 100, 2),
                   exposure_pct=round(nav[-1]["exposure"] * 100, 1))
    if closed:
        wins = [t for t in closed if (t["pnl"] or 0) > 0]
        loss = [t for t in closed if (t["pnl"] or 0) <= 0]
        gl = -sum(t["pnl"] for t in loss)
        mean = lambda xs: round(sum(xs) / len(xs), 2) if xs else 0.0
        out.update(win_rate=round(len(wins) / len(closed) * 100, 1),
                   avg_win_pct=mean([t["ret_pct"] for t in wins]),
                   avg_loss_pct=mean([t["ret_pct"] for t in loss]),
                   expectancy_r=mean([t["r_mult"] for t in closed]),
                   profit_factor=round(sum(t["pnl"] for t in wins) / gl, 2) if gl > 0 else None)
    return out


def _evaluation(stats, inception, last_date):
    months = 0.0
    if inception and last_date:
        d0, d1 = datetime.fromisoformat(inception), datetime.fromisoformat(last_date)
        months = round((d1 - d0).days / 30.44, 1)
    done = stats["n_closed"] >= TARGET_TRADES or months >= TARGET_MONTHS
    exp_ok = (stats.get("expectancy_r") or 0) > 0
    dd_ok = (stats.get("max_dd_pct") or 0) > MAX_DD_LIMIT
    verdict = "dang_theo_doi"
    if done:
        verdict = "dat" if (exp_ok and dd_ok) else "khong_dat"
    elif not dd_ok:
        verdict = "canh_bao_dd"
    return dict(trades=stats["n_closed"], target_trades=TARGET_TRADES, months=months,
                target_months=TARGET_MONTHS, expectancy_ok=exp_ok, dd_ok=dd_ok, verdict=verdict)


def init_luk_routes(app, engine):

    @app.route("/api/luk/portfolio", methods=["GET"])
    def luk_portfolio():
        if not os.getenv("LUK_VIEW_KEY"):
            return jsonify(success=False, error="Chưa cấu hình LUK_VIEW_KEY"), 503
        if not _authorized():
            return jsonify(success=False, error="Sai key"), 401
        try:
            with engine.connect() as c:
                try:
                    meta = {r["key"]: r["value"] for r in _rows(c, "SELECT key, value FROM luk_meta")}
                except Exception:
                    # Bảng luk_* chưa có (runner chưa chạy lần đầu) → báo chưa khởi tạo, không lỗi 500
                    return jsonify(success=True, initialized=False)
                if "last_processed" not in meta:
                    return jsonify(success=True, initialized=False)
                capital = float(meta.get("capital", 1e9))
                nav = _rows(c, "SELECT trade_date, nav, cash, exposure, vnindex, n_positions "
                               "FROM luk_nav ORDER BY trade_date")
                open_pos = _rows(c, "SELECT * FROM luk_positions WHERE status = 'open' ORDER BY entry_date")
                closed = _rows(c, "SELECT ticker, entry_date, exit_date, entry_price, stop0, exit_price, "
                                  "init_shares, pnl, ret_pct, r_mult, hold_days, reasons "
                                  "FROM luk_positions WHERE status = 'closed' ORDER BY exit_date DESC")
                orders = _rows(c, "SELECT trade_date, ticker, side, qty, price, reason FROM luk_orders "
                                  "ORDER BY trade_date DESC, id DESC LIMIT 200")
                pending = _rows(c, "SELECT ticker, close_price, stop, stop_pct, rs FROM luk_signals "
                                   "WHERE signal_date = :d AND status = 'cho_mua' ORDER BY rs DESC",
                                d=meta["last_processed"])
                recent_sig = _rows(c, "SELECT signal_date, ticker, status, fill_date FROM luk_signals "
                                      "ORDER BY signal_date DESC, rs DESC LIMIT 60")
            dates = [x["trade_date"] for x in nav]
            for p in open_pos:
                p["sessions"] = sum(1 for d in dates if d > p["entry_date"])
                p["unreal_pct"] = round((p["last_price"] / p["entry_price"] - 1) * 100, 2) if p["entry_price"] else 0
                p["r_now"] = round((p["last_price"] - p["entry_price"]) / p["r_per_share"], 2) if p["r_per_share"] else 0
                p["value"] = round((p["shares"] or 0) * (p["last_price"] or 0))
            stats = _stats(closed, nav, capital)
            return jsonify(success=True, initialized=True, meta=meta, stats=stats,
                           evaluation=_evaluation(stats, meta.get("inception_date"), meta.get("last_processed")),
                           nav=nav, positions=open_pos, closed=closed, orders=orders,
                           pending_signals=pending, recent_signals=recent_sig)
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500

    @app.route("/luk", methods=["GET"])
    def luk_page():
        return Response(LUK_PAGE, mimetype="text/html; charset=utf-8")

    print("✅ LUK Model Portfolio routes: /api/luk/portfolio, /luk")


LUK_PAGE = r"""<!doctype html>
<html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LUK Model Portfolio</title>
<style>
:root{--bg:#f6f7fb;--card:#fff;--text:#14171f;--muted:#667085;--line:#e4e7ec;--accent:#5b4bdb;
--up:#0e9f6e;--down:#d92d20;--warn:#b54708;--chip:#eef0f6}
@media (prefers-color-scheme:dark){:root{--bg:#0f1117;--card:#171a23;--text:#e8eaf0;--muted:#98a2b3;
--line:#272b36;--accent:#9b8cff;--up:#34d399;--down:#f87171;--warn:#fbbf24;--chip:#232735}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:4px 0 2px}h2{font-size:15px;margin:0 0 10px}
.sub{color:var(--muted);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px}
.kpi .l{color:var(--muted);font-size:12px}.kpi .v{font-size:20px;font-weight:650;margin-top:2px}
.up{color:var(--up)}.down{color:var(--down)}.warn{color:var(--warn)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 6px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:500;font-size:12px}
.tw{overflow-x:auto}.chip{display:inline-block;padding:1px 8px;border-radius:99px;background:var(--chip);font-size:12px}
.legend{display:flex;gap:14px;font-size:12px;color:var(--muted)}.legend i{display:inline-block;width:14px;height:3px;
vertical-align:middle;margin-right:5px;border-radius:2px}
#login{max-width:360px;margin:80px auto}input,button{font:inherit;padding:9px 12px;border-radius:9px;
border:1px solid var(--line);background:var(--card);color:var(--text)}button{background:var(--accent);color:#fff;border:0;cursor:pointer}
.bar{height:8px;background:var(--chip);border-radius:99px;overflow:hidden}.bar>div{height:100%;background:var(--accent)}
.foot{color:var(--muted);font-size:12px;margin:18px 0 30px}
.empty{color:var(--muted);padding:6px 0}
</style></head><body>
<div id="login" class="card" hidden>
  <h2>LUK Model Portfolio</h2><p class="sub">Nhập key xem (LUK_VIEW_KEY)</p>
  <form onsubmit="saveKey(event)"><input id="k" type="password" style="width:100%;margin-bottom:10px">
  <button>Xem danh mục</button></form><p id="lerr" class="down"></p>
</div>
<div class="wrap" id="app" hidden></div>
<script>
const fmt=(v,d=0)=>v==null?'—':Number(v).toLocaleString('vi-VN',{maximumFractionDigits:d,minimumFractionDigits:d});
const pct=(v,d=2)=>v==null?'—':`${v>=0?'+':''}${fmt(v,d)}%`;
const cls=v=>v==null?'':(v>=0?'up':'down');
const REASON={cat_lo:'Chạm cắt lỗ',cat_lo_gap:'Mở cửa dưới cắt lỗ',thung_ema21:'Thủng EMA21',giu_toi_da:'Giữ tối đa 60 phiên',
 mua_pullback:'Mua pullback',end:'Kết thúc'};
const reason=r=>(r||'').split('+').filter(Boolean).map(x=>x.startsWith('chot_1_3')?'Chốt 1/3 ở +3R':
 x.startsWith('dieu_chinh_quyen')?'Điều chỉnh quyền':(REASON[x]||x)).join(' → ');
const SIGST={cho_mua:'Chờ mua',da_mua:'Đã mua','bo_qua:dang_giu':'Bỏ: đang giữ','bo_qua:du_5_ma':'Bỏ: đủ 5 mã',
 'bo_qua:vua_thua':'Bỏ: vừa thua <10 phiên','bo_qua:gap_tang':'Bỏ: gap tăng >3%','bo_qua:tran_khoa':'Bỏ: trần khóa',
 'bo_qua:cat_lo_xa':'Bỏ: cắt lỗ ngoài 2–7%','bo_qua:het_tien':'Bỏ: hết tiền','bo_qua:khong_co_gia':'Bỏ: không có giá'};
function getKey(){try{return localStorage.getItem('luk_key')||''}catch(e){return window._k||''}}
function setKey(k){window._k=k;try{localStorage.setItem('luk_key',k)}catch(e){}}
function saveKey(e){e.preventDefault();setKey(document.getElementById('k').value.trim());load()}
async function load(){
  const k=getKey();if(!k){document.getElementById('login').hidden=false;return}
  const r=await fetch('/api/luk/portfolio',{headers:{'X-LUK-Key':k}});const d=await r.json().catch(()=>({}));
  if(!d.success){document.getElementById('login').hidden=false;document.getElementById('lerr').textContent=d.error||'Lỗi tải';return}
  document.getElementById('login').hidden=true;const app=document.getElementById('app');app.hidden=false;
  if(!d.initialized){app.innerHTML='<div class="card">Chưa khởi tạo — chạy luk_daily_runner.py lần đầu.</div>';return}
  render(d)}
function chart(nav,capital){
  if(nav.length<2)return'<div class="empty">Cần ít nhất 2 phiên để vẽ biểu đồ.</div>';
  const cw=(document.getElementById('app').clientWidth||1000)-30;
  const W=Math.min(1000,Math.max(320,cw)),H=W<600?190:240,pl=48,pr=10,pt=10,pb=24;const a=nav.map(x=>(x.nav/capital-1)*100);
  const b=nav.map(x=>(x.vnindex/nav[0].vnindex-1)*100);const all=a.concat(b,[0]);
  let lo=Math.min(...all),hi=Math.max(...all);if(hi-lo<2){hi+=1;lo-=1}
  const X=i=>pl+i*(W-pl-pr)/(nav.length-1),Y=v=>pt+(hi-v)*(H-pt-pb)/(hi-lo);
  const line=(s,c,w)=>`<polyline fill="none" stroke="${c}" stroke-width="${w}" points="${s.map((v,i)=>X(i).toFixed(1)+','+Y(v).toFixed(1)).join(' ')}"/>`;
  let g='';for(let k=0;k<=4;k++){const v=lo+(hi-lo)*k/4;g+=`<line x1="${pl}" x2="${W-pr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/>
  <text x="${pl-6}" y="${Y(v)+4}" text-anchor="end" font-size="11" fill="var(--muted)">${v.toFixed(1)}%</text>`}
  const lab=[0,Math.floor((nav.length-1)/2),nav.length-1].map(i=>`<text x="${X(i)}" y="${H-6}" font-size="11" fill="var(--muted)"
  text-anchor="${i==0?'start':i==nav.length-1?'end':'middle'}">${nav[i].trade_date}</text>`).join('');
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="NAV so với VNINDEX">${g}
  <line x1="${pl}" x2="${W-pr}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--muted)" stroke-dasharray="3 3"/>
  ${line(b,'var(--muted)',1.5)}${line(a,'var(--accent)',2.4)}${lab}</svg>
  <div class="legend"><span><i style="background:var(--accent)"></i>LUK</span><span><i style="background:var(--muted)"></i>VNINDEX</span></div>`}
function render(d){
  const s=d.stats,m=d.meta,e=d.evaluation,cap=Number(m.capital||1e9);
  const V={dang_theo_doi:['Đang theo dõi',''],dat:['ĐẠT tiêu chí','up'],khong_dat:['KHÔNG đạt','down'],canh_bao_dd:['Cảnh báo sụt giảm','warn']}[e.verdict];
  const prog=Math.min(100,Math.max(e.trades/e.target_trades,e.months/e.target_months)*100);
  const pos=d.positions.map(p=>`<tr><td><b>${p.ticker}</b></td><td>${p.entry_date}</td><td>${fmt(p.entry_price)}</td>
   <td>${fmt(p.last_price)}</td><td class="${cls(p.unreal_pct)}">${pct(p.unreal_pct)}</td><td class="${cls(p.r_now)}">${fmt(p.r_now,2)}R</td>
   <td>${fmt(p.stop)}</td><td>${fmt(p.shares)}</td><td>${fmt(p.value/1e6,1)} tr</td>
   <td><span class="chip">${p.sessions<2?'Chờ hàng T+2':p.pending_exit?'Bán phiên tới':p.partial_done?'Đã chốt 1/3 · bám EMA21':p.trail_on?'Bám EMA21':'Đang giữ'}</span></td></tr>`).join('');
  const pend=d.pending_signals.map(x=>`<tr><td><b>${x.ticker}</b></td><td>${fmt(x.close_price)}</td><td>${fmt(x.stop)}</td>
   <td>${fmt(x.stop_pct,1)}%</td><td>${fmt(x.rs,0)}</td></tr>`).join('');
  const cl=d.closed.map(t=>`<tr><td><b>${t.ticker}</b></td><td>${t.entry_date}</td><td>${t.exit_date}</td><td>${t.hold_days}</td>
   <td class="${cls(t.ret_pct)}">${pct(t.ret_pct)}</td><td class="${cls(t.r_mult)}">${fmt(t.r_mult,2)}R</td>
   <td class="${cls(t.pnl)}">${fmt(t.pnl/1e6,1)} tr</td><td>${reason(t.reasons)}</td></tr>`).join('');
  const od=d.orders.map(o=>`<tr><td>${o.trade_date}</td><td><b>${o.ticker}</b></td>
   <td class="${o.side=='BUY'?'up':o.side=='SELL'?'down':'warn'}">${o.side=='BUY'?'Mua':o.side=='SELL'?'Bán':'Điều chỉnh'}</td>
   <td>${fmt(o.qty)}</td><td>${fmt(o.price)}</td><td>${reason(o.reason)}</td></tr>`).join('');
  const sg=d.recent_signals.map(x=>`<tr><td>${x.signal_date}</td><td><b>${x.ticker}</b></td><td>${SIGST[x.status]||x.status}</td><td>${x.fill_date||''}</td></tr>`).join('');
  const tbl=(head,body,empty)=>body?`<div class="tw"><table><thead><tr>${head.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${body}</tbody></table></div>`:`<div class="empty">${empty}</div>`;
  document.getElementById('app').innerHTML=`
  <h1>LUK Model Portfolio</h1>
  <div class="sub">Luk Pullback 9/21 · ${m.rules_version} · Bắt đầu ${m.inception_date} · Cập nhật phiên ${m.last_processed} · <b>STAGING</b></div>
  <div class="grid">
   <div class="card kpi"><div class="l">NAV</div><div class="v">${fmt(s.nav/1e6,1)} tr</div></div>
   <div class="card kpi"><div class="l">Lợi nhuận</div><div class="v ${cls(s.ret_pct)}">${pct(s.ret_pct)}</div></div>
   <div class="card kpi"><div class="l">VNINDEX cùng kỳ</div><div class="v ${cls(s.vnindex_pct)}">${pct(s.vnindex_pct)}</div></div>
   <div class="card kpi"><div class="l">Max drawdown</div><div class="v ${s.max_dd_pct<=-15?'down':''}">${pct(s.max_dd_pct)}</div></div>
   <div class="card kpi"><div class="l">Tỷ trọng cổ phiếu</div><div class="v">${fmt(s.exposure_pct,0)}%</div></div>
  </div>
  <div class="card"><h2>Diễn biến NAV so với VNINDEX</h2>${chart(d.nav,cap)}</div>
  <div class="card"><h2>Tiêu chí đánh giá forward test · <span class="${V[1]}">${V[0]}</span></h2>
   <div class="bar"><div style="width:${prog}%"></div></div>
   <p class="sub">${e.trades}/${e.target_trades} lệnh đóng · ${fmt(e.months,1)}/${e.target_months} tháng — đến mốc nào trước thì chốt.
   Đạt khi expectancy &gt; 0 <b class="${e.expectancy_ok?'up':'down'}">${e.expectancy_ok?'✓':'✗'}</b>
   và max drawdown &gt; -15% <b class="${e.dd_ok?'up':'down'}">${e.dd_ok?'✓':'✗'}</b></p>
   <div class="grid" style="margin:8px 0 0">
    <div class="kpi"><div class="l">Tỷ lệ thắng</div><div class="v">${s.win_rate==null?'—':fmt(s.win_rate,1)+'%'}</div></div>
    <div class="kpi"><div class="l">Lãi TB / Lỗ TB</div><div class="v"><span class="up">${pct(s.avg_win_pct,1)}</span> / <span class="down">${pct(s.avg_loss_pct,1)}</span></div></div>
    <div class="kpi"><div class="l">Expectancy</div><div class="v ${cls(s.expectancy_r)}">${s.expectancy_r==null?'—':fmt(s.expectancy_r,2)+'R'}</div></div>
    <div class="kpi"><div class="l">Profit factor</div><div class="v">${s.profit_factor==null?'—':fmt(s.profit_factor,2)}</div></div>
   </div></div>
  <div class="card"><h2>Đang nắm giữ (${d.positions.length}/5)</h2>${tbl(['Mã','Ngày mua','Giá vốn','Giá','Lãi/lỗ','R','Cắt lỗ','SL','Giá trị','Trạng thái'],pos,'Chưa có vị thế.')}</div>
  <div class="card"><h2>Chờ mua phiên tới (giá mở cửa)</h2>${tbl(['Mã','Đóng cửa','Cắt lỗ','Rủi ro','RS'],pend,'Không có tín hiệu.')}</div>
  <div class="card"><h2>Lệnh đã đóng</h2>${tbl(['Mã','Mua','Bán','Phiên','Lãi/lỗ','R','Tiền','Lý do'],cl,'Chưa có lệnh đóng.')}</div>
  <div class="card"><h2>Nhật ký lệnh</h2>${tbl(['Ngày','Mã','Lệnh','SL','Giá','Lý do'],od,'Chưa có lệnh.')}</div>
  <div class="card"><h2>Tín hiệu gần đây</h2>${tbl(['Ngày tín hiệu','Mã','Kết quả','Ngày xử lý'],sg,'Chưa có tín hiệu.')}</div>
  <div class="foot">Danh mục MÔ PHỎNG 1 tỷ, tự vận hành theo luật cố định. Mua ở giá mở cửa phiên sau tín hiệu, bán theo T+2, đã tính phí 0,15% và thuế 0,1%.
  AI Advisor là công cụ hỗ trợ quyết định, không phải tư vấn đầu tư. Đầu tư chứng khoán có rủi ro, bạn có thể mất toàn bộ số tiền đầu tư.</div>`}
load();
</script></body></html>"""
