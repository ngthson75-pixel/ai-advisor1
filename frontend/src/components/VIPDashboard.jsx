/**
 * AI ADVISOR - VIP DASHBOARD v2.3
 * ================================
 * FIXES (2026-03-22):
 *   BUG1 - Gọi đúng /api/vip/signals thay vì /api/signals (public)
 *   BUG4 - VN30 list khớp chính xác 30 tickers trong vip_signal_scanner.py
 *   BUG5 - Thêm date filter (7 / 30 / all ngày) + hiển thị rõ số ngày
 *   MISC - Error state, loading state, và auth token header
 * FIXES (2026-06-01):
 *   BUG6 - Production (ai-advisor.vn) fallback về localhost vì VITE_API_URL không set
 *          → Fix: detect hostname production → hardcode production backend URL
 * FIXES (2026-06-22):
 *   BUG7 - Chat history không load được: frontend đọc d.messages nhưng backend trả d.history
 *          → Fix: đổi sang d.history + convert format {message,response} → {role,content}
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import IISScoreWidget from './IISScoreWidget'

// ─── Environment Detection ───────────────────────────────────
const _hostname     = typeof window !== 'undefined' ? window.location.hostname : ''
const _IS_STAGING   = _hostname.includes('staging')
const _IS_LOCALHOST = _hostname === 'localhost' || _hostname === '127.0.0.1'
// Production = ai-advisor.vn hoặc www.ai-advisor.vn (bất kỳ hostname nào không phải staging/localhost)
const _IS_PRODUCTION = !_IS_STAGING && !_IS_LOCALHOST

const API_BASE = _IS_STAGING
  ? 'https://ai-advisor1-staging.onrender.com/api'
  : _IS_PRODUCTION
    ? 'https://ai-advisor1-backend.onrender.com/api'
    : (import.meta.env.VITE_API_URL || 'http://localhost:10000/api')

const VIP_API = API_BASE.replace(/\/api\/?$/, '')

const RESCUE_QUESTIONS = [
  'Tại sao bạn mua cổ phiếu này? (1-2 câu ngắn gọn)',
  'Lý do đó có còn đúng ở thời điểm hiện tại không?',
  'Nếu bạn không có cổ phiếu này, bạn có mua nó ngay hôm nay không?',
]

// ─── BUG4 FIX: VN30 list khớp chính xác vip_signal_scanner.py ─
// Nguồn gốc: vip_signal_scanner.py → VN30_TICKERS set (30 tickers)
const VN30_TICKERS = new Set([
  'ACB','BCM','BID','BVH','CTG','FPT','GAS','GVR','HDB','HPG',
  'MBB','MSN','MWG','PLX','POW','SAB','SHB','SSB','SSI','STB',
  'TCB','TPB','VCB','VHM','VIB','VIC','VJC','VNM','VPB','VRE',
])
// Tổng: 30 tickers (đúng VN30 index)

// ─── Auth Token Helper ────────────────────────────────────────
// Token được lưu khi VIP login qua handleVipLogin() trong LandingPage
function getVipToken() {
  try {
    // Ưu tiên 1: vip_token riêng
    const token = localStorage.getItem('vip_token')
    if (token) return token
    // Ưu tiên 2: token trong user object
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const u = JSON.parse(userStr)
      if (u.token) return u.token
    }
  } catch {}
  return null
}

function authHeaders() {
  const token = getVipToken()
  const h = { 'Content-Type': 'application/json' }
  if (token) h['Authorization'] = `Bearer ${token}`
  return h
}

// ─── Design Tokens ────────────────────────────────────────────
const C = {
  bg: '#0b0a14', bgCard: '#13111f', border: '#2d2550',
  purple: '#7c3aed', purpleLight: '#a855f7',
  purpleFade: 'rgba(124,58,237,0.12)', purpleGlow: 'rgba(168,85,247,0.3)',
  green: '#22c55e', red: '#f87171', yellow: '#fbbf24',
  text: '#e2d9f3', muted: '#7c6fa0',
}

const card = {
  background: C.bgCard, border: `1px solid ${C.border}`,
  borderRadius: '16px', padding: '20px', marginBottom: '16px',
}
const badge = (color) => ({
  display: 'inline-flex', alignItems: 'center',
  padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700',
  background: color + '22', color, border: `1px solid ${color}44`,
})
const btn = (bg) => ({
  padding: '8px 16px', borderRadius: '8px', border: 'none',
  background: bg || C.purple, color: '#fff', fontWeight: '600',
  fontSize: '13px', cursor: 'pointer',
})
const tabStyle = (active) => ({
  padding: '10px 18px', borderRadius: '10px 10px 0 0',
  fontSize: '13px', fontWeight: '600', border: 'none',
  background: active ? C.purpleFade : 'transparent',
  color: active ? C.purpleLight : C.muted,
  borderBottom: `2px solid ${active ? C.purpleLight : 'transparent'}`,
  cursor: 'pointer', transition: 'all 0.2s',
})
const fmt     = (n) => n == null ? '—' : Number(n).toLocaleString('vi-VN')
// Làm tròn giá cổ phiếu đến hàng trăm (quy định TTCK VN: bước giá 100đ)
const roundPrice = (n) => n == null ? null : Math.round(Number(n) / 100) * 100
const fmtPrice   = (n) => n == null ? '—' : roundPrice(n).toLocaleString('vi-VN')
const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' }) : '—'

// ─── Markdown → HTML converter (strip dấu * từ GPT response) ──
// Chuyển **bold** → <strong>, *italic* → <em>, xuống dòng → <br>
// Không dùng thư viện ngoài để tránh tăng bundle size
function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    // Escape HTML để tránh XSS trước khi inject
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // **bold** hoặc __bold__
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    // *italic* hoặc _italic_ (không dính vào bullet - *)
    .replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
    .replace(/_([^_\n]+?)_/g, '<em>$1</em>')
    // - item hoặc • item → bullet đẹp
    .replace(/^[\-•]\s+(.+)$/gm, '• $1')
    // Xuống dòng
    .replace(/\n/g, '<br/>')
  return html
}

// ─── Telegram Status Badge (static — toggle feature pending) ──
function TelegramBadge() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '6px',
      background: '#22c55e22', border: '1px solid #22c55e44',
      borderRadius: '8px', padding: '6px 12px', fontSize: '13px',
    }}>
      <span>🔔</span>
      <span style={{ color: '#22c55e', fontWeight: '600' }}>Telegram đang bật</span>
    </div>
  )
}

// ─── Signal Card ─────────────────────────────────────────────
function SignalCard({ signal }) {
  const isBuy  = (signal.action || 'BUY') === 'BUY'
  const ticker = (signal.ticker || signal.code || '').toUpperCase()
  const isVN30 = VN30_TICKERS.has(ticker)
  // VIP endpoint trả về rr_ratio; public endpoint trả về risk_reward
  const rrRatio = signal.rr_ratio || signal.risk_reward

  return (
    <div style={{
      background: isBuy ? 'linear-gradient(135deg,#052e1618,#13111f)' : 'linear-gradient(135deg,#2e050518,#13111f)',
      border: `1px solid ${isBuy ? '#22c55e33' : '#f8717133'}`,
      borderRadius: '14px', padding: '16px', marginBottom: '10px', position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ position: 'absolute', top: 0, right: 0, width: '80px', height: '80px',
        background: `radial-gradient(circle,${C.purpleGlow} 0%,transparent 70%)`, borderRadius: '0 14px 0 0' }} />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '20px', fontWeight: '800', color: '#fff' }}>{ticker}</span>
          <span style={badge(isBuy ? C.green : C.red)}>{isBuy ? '▲ MUA' : '▼ BÁN'}</span>
          {isVN30 && <span style={badge(C.purpleLight)}>VN30</span>}
          {/* strategy_type badge hidden */}
          {signal.confidence > 0 && (
            <span style={badge(signal.confidence >= 75 ? C.green : C.yellow)}>
              {Math.round(signal.confidence)}%
            </span>
          )}
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ color: C.muted, fontSize: '11px' }}>{fmtDate(signal.created_at || signal.entry_date)}</div>
          {signal.status && <span style={badge(signal.status === 'open' ? C.green : signal.status === 'closed' ? C.muted : C.yellow)}>
            {signal.status === 'open' ? 'Đang mở' : signal.status === 'closed' ? 'Đã đóng' : signal.status}
          </span>}
        </div>
      </div>

       {isBuy ? (
        // ── BUY signal fields ──────────────────────────────────
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '8px' }}>
            {[
              { label: '📍 Entry', val: fmtPrice(signal.entry_price), color: C.text },
              { label: '🛑 Stop Loss', val: fmtPrice(signal.stop_loss), color: C.red },
              { label: '🎯 Target', val: fmtPrice(signal.take_profit), color: C.green },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ background: '#ffffff06', borderRadius: '8px', padding: '8px 10px', border: '1px solid #ffffff08' }}>
                <div style={{ color: C.muted, fontSize: '10px', marginBottom: '3px' }}>{label}</div>
                <div style={{ color, fontWeight: '700', fontSize: '14px' }}>{val}</div>
              </div>
            ))}
          </div>
          {(rrRatio || signal.position_pct != null) && (
            <div style={{ display: 'flex', gap: '12px', marginTop: '10px', fontSize: '12px', color: C.muted }}>
              {rrRatio > 0 && <span>⚖️ R/R: <b style={{ color: C.text }}>{Number(rrRatio).toFixed(1)}x</b></span>}
              {signal.position_pct != null && <span>📊 Tỷ trọng: <b style={{ color: C.purpleLight }}>{signal.position_pct}%</b></span>}
            </div>
          )}

          <button
            onClick={() => window.dispatchEvent(new CustomEvent('askAI', {detail: `[IN BUYSELL SIGNAL] Co phieu ${signal.ticker} tin hieu MUA score ${signal.strength||signal.confidence||0}%, gia vao ${(signal.entry_price||0).toLocaleString('vi-VN')}, SL ${(signal.stop_loss||0).toLocaleString('vi-VN')}, TP ${(signal.take_profit||0).toLocaleString('vi-VN')}. Phan tich va cho biet nen hanh dong the nao?`}))}
            style={{ display:'inline-flex', alignItems:'center', gap:'5px', marginTop:'10px', padding:'5px 12px', borderRadius:'8px', cursor:'pointer', fontSize:'11px', fontWeight:600, background:'rgba(168,85,247,0.12)', border:'1px solid rgba(168,85,247,0.35)', color:'#a855f7' }}
          >🤖 Phân tích AI</button>
        </>
      ) : (
        // ── SELL signal fields ─────────────────────────────────
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '8px' }}>
            {[
              { label: '📍 Giá vào', val: fmtPrice(signal.entry_price), color: C.muted },
              { label: '💰 Giá bán', val: fmtPrice(signal.exit_price), color: C.text },
              { label: (signal.profit_loss_pct >= 0 ? '🟢 Lãi' : '🔴 Lỗ'),
                val: signal.profit_loss_pct != null
                  ? `${signal.profit_loss_pct >= 0 ? '+' : ''}${Number(signal.profit_loss_pct).toFixed(2)}%`
                  : '—',
                color: signal.profit_loss_pct >= 0 ? C.green : C.red },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ background: '#ffffff06', borderRadius: '8px', padding: '8px 10px', border: '1px solid #ffffff08' }}>
                <div style={{ color: C.muted, fontSize: '10px', marginBottom: '3px' }}>{label}</div>
                <div style={{ color, fontWeight: '700', fontSize: '14px' }}>{val}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '12px', marginTop: '10px', fontSize: '12px', color: C.muted, flexWrap: 'wrap' }}>
            {signal.exit_reason && (
              <span>📋 Lý do: <b style={{ color: C.text }}>
                {signal.exit_reason === 'STOP_LOSS' ? '🔴 Cắt lỗ'
                 : signal.exit_reason === 'TAKE_PROFIT' ? '🟢 Chốt lời'
                 : signal.exit_reason === 'MA20_STRICT' ? '🟡 MA20 Cross'
                 : signal.exit_reason}
              </b></span>
            )}
            {signal.exit_quantity_pct != null && signal.exit_quantity_pct < 100 && (
              <span>📊 Bán: <b style={{ color: C.purpleLight }}>{signal.exit_quantity_pct}%</b></span>
            )}
          </div>

          <button
            onClick={() => window.dispatchEvent(new CustomEvent('askAI', {detail: `[IN BUYSELL SIGNAL] Co phieu ${signal.ticker} tin hieu BAN. Ly do: ${signal.exit_reason||'He thong'}. Gia vao ${(signal.entry_price||0).toLocaleString('vi-VN')}, gia ra ${(signal.exit_price||0).toLocaleString('vi-VN')}. Phan tich va cho biet nen ban khong?`}))}
            style={{ display:'inline-flex', alignItems:'center', gap:'5px', marginTop:'10px', padding:'5px 12px', borderRadius:'8px', cursor:'pointer', fontSize:'11px', fontWeight:600, background:'rgba(168,85,247,0.12)', border:'1px solid rgba(168,85,247,0.35)', color:'#a855f7' }}
          >🤖 Phân tích AI</button>
        </>
      )}
    </div> )
}

// ─── Signals Tab ─────────────────────────────────────────────
function VIPSignalsTab({ signals, loading, fetchError, onRefresh, days, onDaysChange }) {
  const [filter, setFilter] = useState('vn30')

  // isOpen: chỉ hiện signal đang mở hoặc bán 1 phần
  const isOpen  = s => !s.status || s.status === 'open' || s.status === 'partial'
  const isVN30s = s => VN30_TICKERS.has((s.ticker || s.code || '').toUpperCase())

  // Helper sort: mới nhất lên trên
  const getDate = s => s.created_at || s.entry_date || s.signal_date || s.date || ''
  const sortDesc = arr => [...arr].sort((a, b) => getDate(b).localeCompare(getDate(a)))

  // Tab VN30: chỉ VN30 đang mở, mới nhất lên trên
  const vn30Buy = sortDesc(signals.filter(s => isVN30s(s) && (s.action || 'BUY') === 'BUY' && isOpen(s)))

  // Tab Tất cả MUA: VN30 + non-VN30 score >= 80%, đang mở, mới nhất lên trên
  const allBuy  = sortDesc(signals.filter(s =>
    (s.action || 'BUY') === 'BUY' && isOpen(s) &&
    (isVN30s(s) || (s.strength || s.confidence || 0) >= 80)
  ))

  // Tab BÁN: đang mở, mới nhất lên trên
  // SELL signals: VN30 only, không filter isOpen (SELL đã là lệnh đã thực hiện)
  const allSell = sortDesc(signals.filter(s => s.action === 'SELL' && isVN30s(s)))

  const filtered = filter === 'vn30' ? vn30Buy
                 : filter === 'buy'  ? allBuy
                 : filter === 'sell' ? allSell
                 : sortDesc([...allBuy, ...allSell])

  // BUG5 FIX: Hiển thị label date filter rõ ràng
  const dayLabel = days === 999 ? 'Tất cả' : `${days} ngày gần nhất`

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: '0 16px' }}>

      {/* Stats cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '10px', marginBottom: '20px' }}>
        {[
          { label: 'Tổng', val: signals.length, color: C.purpleLight, icon: '📊' },
          { label: 'VN30 Mua', val: vn30Buy.length, color: '#a78bfa', icon: '💎' },
          { label: 'Tín hiệu MUA', val: allBuy.length, color: C.green, icon: '▲' },
          { label: 'Tín hiệu BÁN', val: allSell.length, color: C.red, icon: '▼' },
        ].map(({ label, val, color, icon }) => (
          <div key={label} style={{ ...card, marginBottom: 0, textAlign: 'center', padding: '14px',
            background: `linear-gradient(135deg,${color}08,${C.bgCard})`, border: `1px solid ${color}22` }}>
            <div style={{ fontSize: '18px' }}>{icon}</div>
            <div style={{ fontSize: '22px', fontWeight: '800', color }}>{val}</div>
            <div style={{ fontSize: '10px', color: C.muted, marginTop: '2px' }}>{label}</div>
          </div>
        ))}
      </div>

      <div style={card}>
        {/* Filter row */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          {[
            { key: 'vn30', label: `💎 VN30 (${vn30Buy.length})` },
            { key: 'buy',  label: `▲ Tất cả MUA (${allBuy.length})` },
            { key: 'sell', label: `▼ BÁN (${allSell.length})` },
            { key: 'all',  label: `📋 Tất cả (${signals.length})` },
          ].map(({ key, label }) => (
            <button key={key} onClick={() => setFilter(key)} style={{
              padding: '6px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: '600', border: 'none',
              background: filter === key ? C.purpleFade : 'transparent',
              color: filter === key ? C.purpleLight : C.muted, cursor: 'pointer',
              outline: filter === key ? `1px solid ${C.purpleLight}` : 'none',
            }}>{label}</button>
          ))}
          <button onClick={onRefresh} style={{ ...btn('#334155'), marginLeft: 'auto', padding: '6px 12px', fontSize: '12px' }}>🔄</button>
        </div>

        {/* BUG5 FIX: Date range selector */}
        <div style={{ display: 'flex', gap: '6px', marginBottom: '14px', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: C.muted, marginRight: '4px' }}>📅 Hiển thị:</span>
          {[
            { val: 7,   label: '7 ngày' },
            { val: 30,  label: '30 ngày' },
            { val: 999, label: 'Tất cả' },
          ].map(({ val, label }) => (
            <button key={val} onClick={() => onDaysChange(val)} style={{
              padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', border: 'none',
              background: days === val ? C.purpleFade : 'transparent',
              color: days === val ? C.purpleLight : C.muted, cursor: 'pointer',
              outline: days === val ? `1px solid ${C.purpleLight}55` : 'none',
            }}>{label}</button>
          ))}
          {!loading && <span style={{ fontSize: '11px', color: C.muted, marginLeft: '4px' }}>({dayLabel})</span>}
        </div>

        {/* VN30 info banner */}
        {filter === 'vn30' && (
          <div style={{ background: `linear-gradient(135deg,#7c3aed22,#a855f722)`,
            border: `1px solid ${C.purpleLight}44`, borderRadius: '10px', padding: '10px 14px',
            fontSize: '12px', color: C.purpleLight, marginBottom: '14px' }}>
            💎 <strong>VIP Exclusive:</strong> Tín hiệu mua cổ phiếu VN30 — bluechip thanh khoản cao nhất
          </div>
        )}

        {/* Error state */}
        {fetchError && (
          <div style={{ background: '#2e050522', border: '1px solid #f8717133', borderRadius: '10px',
            padding: '14px', marginBottom: '14px', fontSize: '13px', color: C.red }}>
            ⚠️ {fetchError}
            <button onClick={onRefresh} style={{ ...btn('#7f1d1d'), marginLeft: '12px', padding: '4px 10px', fontSize: '12px' }}>Thử lại</button>
          </div>
        )}

        {/* Signal list */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: C.muted }}>
            <div style={{ fontSize: '28px', marginBottom: '8px' }}>⏳</div>Đang tải tín hiệu...
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: C.muted }}>
            <div style={{ fontSize: '28px', marginBottom: '8px' }}>📭</div>
            Không có tín hiệu nào trong {dayLabel}
            {filter === 'vn30' && <div style={{ fontSize: '12px', marginTop: '8px' }}>Thử chuyển sang "Tất cả MUA" hoặc mở rộng khoảng ngày</div>}
          </div>
        ) : (
          filtered.map((s, i) => <SignalCard key={s.id || i} signal={s} />)
        )}
      </div>
    </div>
  )
}

// ─── Portfolio Tab ────────────────────────────────────────────
function VIPPortfolioTab({ userId }) {
  const [portfolio, setPortfolio] = useState([])
  const [cash, setCash]           = useState(0)
  const [cashInput, setCashInput] = useState('')
  const [editingCash, setEditingCash] = useState(false)
  const [addForm, setAddForm]     = useState({ ticker: '', quantity: '', price: '' })
  const [addLoading, setAddLoading] = useState(false)
  const [marketMode, setMarketMode] = useState(null)

  useEffect(() => { loadPortfolio(); loadCash(); loadMarket() }, [userId])

  async function loadPortfolio() {
    try { const r = await fetch(`${API_BASE}/portfolio?user_id=${userId}`, { headers: authHeaders() }); const d = await r.json(); if (d.success) setPortfolio(d.portfolio || []) } catch {}
  }
  async function loadCash() {
    try { const r = await fetch(`${API_BASE}/cash?user_id=${userId}`, { headers: authHeaders() }); const d = await r.json(); if (d.success) setCash(d.cash || 0) } catch {}
  }
  async function loadMarket() {
    try { const r = await fetch(`${VIP_API}/api/market-risk`); const d = await r.json(); if (d.success && d.data) setMarketMode(d.data) } catch {}
  }
  async function handleAddStock(e) {
    e.preventDefault(); setAddLoading(true)
    try {
      const r = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ user_id: userId, ...addForm, quantity: Number(addForm.quantity), price: Number(addForm.price) }),
      })
      const d = await r.json(); if (d.success) { setAddForm({ ticker: '', quantity: '', price: '' }); loadPortfolio() }
    } catch {}
    setAddLoading(false)
  }
  async function handleDeleteStock(ticker) {
    try { await fetch(`${API_BASE}/portfolio/${ticker}?user_id=${userId}`, { method: 'DELETE', headers: authHeaders() }); loadPortfolio() } catch {}
  }
  async function handleSaveCash() {
    try {
      await fetch(`${API_BASE}/cash`, { method: 'POST', headers: authHeaders(), body: JSON.stringify({ user_id: userId, cash: Number(cashInput) }) })
      setCash(Number(cashInput)); setEditingCash(false)
    } catch {}
  }

  const totalValue = portfolio.reduce((s, x) => s + (x.current_value || 0), 0) + cash
  const totalPnL   = portfolio.reduce((s, x) => s + (x.pl_amount || 0), 0)

  return (
    <div style={{ maxWidth: '760px', margin: '0 auto', padding: '0 16px' }}>
      {marketMode && (
        <div style={{ ...card, background: 'linear-gradient(135deg,#7c3aed22,#13111f)', border: `1px solid ${C.purpleLight}44` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '11px', color: C.muted, marginBottom: '4px' }}>CHẾ ĐỘ THỊ TRƯỜNG</div>
              <div style={{ fontSize: '18px', fontWeight: '800', color: C.purpleLight }}>{marketMode.market_mode || '—'}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: C.muted }}>Risk Score</div>
              <div style={{ fontSize: '22px', fontWeight: '800', color: C.text }}>{marketMode.risk_score ?? '—'}<span style={{ fontSize: '13px', color: C.muted }}>/100</span></div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '10px', marginBottom: '16px' }}>
        {[
          { label: 'Tổng tài sản', val: fmt(totalValue) + ' đ', color: C.purpleLight },
          { label: 'Tiền mặt', val: fmt(cash) + ' đ', color: C.text },
          { label: 'Lãi/Lỗ', val: (totalPnL >= 0 ? '+' : '') + fmt(totalPnL) + ' đ', color: totalPnL >= 0 ? C.green : C.red },
        ].map(({ label, val, color }) => (
          <div key={label} style={{ ...card, marginBottom: 0, textAlign: 'center', padding: '14px' }}>
            <div style={{ fontSize: '11px', color: C.muted, marginBottom: '6px' }}>{label}</div>
            <div style={{ fontSize: '15px', fontWeight: '700', color }}>{val}</div>
          </div>
        ))}
      </div>

      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ margin: 0, fontSize: '14px', color: C.purpleLight }}>💰 Tiền mặt</h3>
          {!editingCash
            ? <button style={{ ...btn('#334155'), fontSize: '12px', padding: '6px 12px' }} onClick={() => { setCashInput(cash); setEditingCash(true) }}>✏️ Sửa</button>
            : <div style={{ display: 'flex', gap: '8px' }}>
                <input type="number" value={cashInput} onChange={e => setCashInput(e.target.value)}
                  style={{ background: '#0f172a', border: `1px solid ${C.border}`, color: C.text, borderRadius: '8px', padding: '6px 10px', width: '140px', fontSize: '13px' }} />
                <button style={{ ...btn(C.green), padding: '6px 10px' }} onClick={handleSaveCash}>💾</button>
                <button style={{ ...btn('#475569'), padding: '6px 10px' }} onClick={() => setEditingCash(false)}>✕</button>
              </div>}
        </div>
        <div style={{ fontSize: '20px', fontWeight: '700', color: C.text }}>{fmt(cash)} đ</div>
      </div>

      <div style={card}>
        <h3 style={{ margin: '0 0 14px', fontSize: '14px', color: C.purpleLight }}>📈 Danh mục cổ phiếu</h3>
        {portfolio.length === 0 ? (
          <div style={{ color: C.muted, textAlign: 'center', padding: '20px', fontSize: '13px' }}>Chưa có cổ phiếu. Thêm vào bên dưới.</div>
        ) : (
          <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                  {['Mã', 'SL', 'Giá mua', 'Giá HT', 'Giá trị', 'Lãi/Lỗ', ''].map(h => (
                    <th key={h} style={{ padding: '8px 6px', color: C.muted, fontWeight: '600', textAlign: 'left', fontSize: '11px' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolio.map(s => (
                  <tr key={s.ticker} style={{ borderBottom: `1px solid ${C.border}22` }}>
                    <td style={{ padding: '8px 6px', fontWeight: '700', color: C.purpleLight }}>{s.ticker}</td>
                    <td style={{ padding: '8px 6px' }}>{s.quantity?.toLocaleString()}</td>
                    <td style={{ padding: '8px 6px' }}>{fmt(s.avg_price)}</td>
                    <td style={{ padding: '8px 6px' }}>{fmt(s.current_price)}</td>
                    <td style={{ padding: '8px 6px' }}>{fmt(s.current_value)}</td>
                    <td style={{ padding: '8px 6px', color: (s.pl_amount || 0) >= 0 ? C.green : C.red, fontWeight: '600' }}>
                      <div>{(s.pl_amount || 0) >= 0 ? '+' : ''}{fmt(s.pl_amount)}</div>
                      <div style={{ fontSize: '11px', opacity: 0.85 }}>
                        {(s.pl_pct || 0) >= 0 ? '+' : ''}{(s.pl_pct || 0).toFixed(1)}%
                      </div>
                    </td>
                    <td style={{ padding: '8px 6px' }}>
                      <button onClick={() => handleDeleteStock(s.ticker)} style={{ background: 'none', border: 'none', color: C.red, cursor: 'pointer' }}>🗑️</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <form onSubmit={handleAddStock} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            { key: 'ticker', ph: 'Mã CP (HPG)', type: 'text' },
            { key: 'quantity', ph: 'Số lượng', type: 'number' },
            { key: 'price', ph: 'Giá mua', type: 'number' },
          ].map(({ key, ph, type }) => (
            <input key={key} type={type} placeholder={ph} required value={addForm[key]}
              onChange={e => setAddForm(f => ({ ...f, [key]: e.target.value }))}
              style={{ flex: '1', minWidth: '90px', background: '#0f172a', border: `1px solid ${C.border}`, color: C.text, borderRadius: '8px', padding: '8px 10px', fontSize: '13px' }} />
          ))}
          <button type="submit" disabled={addLoading} style={btn(C.purple)}>
            {addLoading ? '...' : '+ Thêm'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ─── Inline AI Chat ───────────────────────────────────────────
function InlineAIChat({ userId }) {
  const [messages, setMessages] = useState([])
  const [bnChips, setBnChips]   = useState([])   // v2.2: chip theo điểm nghẽn
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [expanded, setExpanded] = useState(false)
  const chatEndRef   = useRef(null)
  const inputRef     = useRef(null)
  const containerRef = useRef(null)
  // ── Rescue flow ─────────────────────────────────────────────
  const [rescueMode,   setRescueMode]   = useState(false)
  const [rescueStep,   setRescueStep]   = useState(0)
  const [rescueStocks, setRescueStocks] = useState([{ ticker: '', lossP: '' }])
  const [rescueCur,    setRescueCur]    = useState(0)

  // Langhe Phan tich AI tu SignalCard
  useEffect(() => {
    const h = (e) => {
      if (!e.detail) return
      setExpanded(true)
      handleSend({ preventDefault: () => {} }, e.detail)
      setTimeout(() => {
        const el = document.getElementById('vip-ai-chat')
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 500)
    }
    window.addEventListener('askAI', h)
    return () => window.removeEventListener('askAI', h)
  }, [])

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages])

  // ─── Load chat history + inject market summary nếu chưa có lịch sử ───
  useEffect(() => {
    async function initChat() {
      // 1. Thử load lịch sử chat
      // BUG7 FIX: backend trả về d.history (không phải d.messages)
      // BUG7 FIX: convert format {message, response} → [{role:'user'}, {role:'assistant'}]
      try {
        const r = await fetch(`${API_BASE}/chat/history?user_id=${userId}&limit=30`, { headers: authHeaders() })
        const d = await r.json()
        if (d.success && d.history?.length > 0) {
          const converted = []
          for (const h of d.history) {
            if (h.message)  converted.push({ role: 'user',      content: h.message })
            if (h.response) converted.push({ role: 'assistant', content: h.response })
          }
          if (converted.length > 0) {
            setMessages(converted)
            setExpanded(true)
            return  // Đã có lịch sử → không inject market summary
          }
        }
      } catch {}

      // 2. Chưa có lịch sử → fetch market risk và tạo tin nhắn chào
      try {
        const mr = await fetch(`${VIP_API}/api/market-risk`)
        const md = await mr.json()
        if (md.success && md.data) {
          const m = md.data
          const mode       = m.market_mode || '—'
          const risk       = m.risk_score ?? '—'
          const allocation = m.allocation ?? '—'
          const date       = m.date ? new Date(m.date).toLocaleDateString('vi-VN', { day:'2-digit', month:'2-digit' }) : ''

          // Màu theo risk score
          const riskEmoji = risk <= 40 ? '🟢' : risk <= 65 ? '🟡' : '🔴'

          const summary = `Xin chào! Đây là tóm tắt thị trường hôm nay (${date}):

${riskEmoji} Chế độ thị trường: ${mode}
📊 Điểm rủi ro: ${risk}/100
💼 Tỷ trọng khuyến nghị: ${allocation}%

Bạn muốn tôi phân tích cổ phiếu nào, hoặc đánh giá danh mục hiện tại không?`

          setMessages([{ role: 'assistant', content: summary }])
        }
      } catch {}
    }
    initChat()
  }, [userId])

  async function handleSend(e, directMsg) {
    e.preventDefault()
    const msg = directMsg || input.trim()
    if (!msg || loading) return
    setInput(''); setExpanded(true)
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)
    try {
      // IIS profile fallback từ localStorage
      let _iisLocal = null
      try {
        const _c = localStorage.getItem(`iis_result_${userId}`)
        if (_c) { const _p = JSON.parse(_c); if (_p.has_result) _iisLocal = { total: _p.total, level: _p.level, method: _p.method, kl: _p.kl_score, kt: _p.kt_score } }
      } catch {}
      const r = await fetch(`${API_BASE}/chat`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ user_id: userId, message: msg, user_tier: 'vip', iis_profile_fallback: _iisLocal }),
      })
      const d = await r.json()
      setMessages(prev => [...prev, { role: 'assistant', content: d.response || d.message || '...', meta: d.meta || null }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Lỗi kết nối. Thử lại sau.' }])
    }
    setLoading(false)
  }

  const latestMessages = expanded ? messages : messages.slice(-3)

  const startRescue = () => {
    setRescueMode(true); setRescueStep(0)
    setRescueStocks([{ ticker: '', lossP: '' }]); setRescueCur(0)
    setExpanded(true)
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '🩺 **Khám sức khỏe danh mục kẹp**\n\nNhập cổ phiếu đang kẹp lỗ. Tôi sẽ hỏi 3 câu về từng mã để đánh giá mức rủi ro.',
    }])
  }

  const submitRescueStocks = () => {
    const valid = rescueStocks.filter(s => s.ticker.trim())
    if (!valid.length) return
    setRescueStocks(valid); setRescueStep(1); setRescueCur(0)
    const names = valid.map(s => `${s.ticker.toUpperCase()}${s.lossP ? ` (-${s.lossP}%)` : ''}`).join(', ')
    setMessages(prev => [...prev,
      { role: 'user', content: `Danh mục kẹp: ${names}` },
      { role: 'assistant', content: `**${valid[0].ticker.toUpperCase()}${valid[0].lossP ? ` (lỗ ${valid[0].lossP}%)` : ''}**\n\n${RESCUE_QUESTIONS[0]}` }
    ])
  }

  // === v2.2: nạp chip gợi ý theo ĐIỂM NGHẼN — thay cho menu ===
  useEffect(() => {
    if (!userId) return
    let alive = true
    fetch(`${API_BASE}/chips/${encodeURIComponent(userId)}`)
      .then(r => r.json())
      .then(d => { if (alive && d.success) setBnChips((d.chips || []).slice(0, 2)) })
      .catch(() => {})
    return () => { alive = false }
  }, [userId])

  const handleRescueAnswer = async (answer) => {
    if (!answer.trim()) return
    const stocks = rescueStocks.filter(s => s.ticker.trim())
    const stock  = stocks[rescueCur]
    const qIdx   = (rescueStep - 1) % 3
    setMessages(prev => [...prev, { role: 'user', content: answer }])
    setInput('')
    if (qIdx < 2) {
      setRescueStep(s => s + 1)
      setTimeout(() => setMessages(prev => [...prev, { role: 'assistant', content: RESCUE_QUESTIONS[qIdx + 1] }]), 300)
    } else {
      setLoading(true)
      const prompt = `Portfolio Rescue:\nCổ phiếu: ${stock.ticker.toUpperCase()}${stock.lossP ? ` | Lỗ: -${stock.lossP}%` : ''}\nCâu 3: "${answer}"\nĐưa ra: 1) ĐÁNH GIÁ RỦI RO của vị thế 2) Lý do 2-3 câu dựa trên dữ liệu 3) Các kịch bản user có thể cân nhắc, kèm hệ quả từng kịch bản. KHÔNG đưa khuyến nghị mua/bán — chỉ đối chiếu với ngưỡng rủi ro user đã đặt.`
      try {
        const r = await fetch(`${API_BASE}/chat`, {
          method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, message: prompt, user_tier: 'vip' })
        })
        const d = await r.json()
        setMessages(prev => [...prev, { role: 'assistant', content: d.response || '...' }])
      } catch { setMessages(prev => [...prev, { role: 'assistant', content: 'Không thể phân tích lúc này.' }]) }
      setLoading(false)
      if (rescueCur < stocks.length - 1) {
        const next = stocks[rescueCur + 1]
        setRescueCur(c => c + 1); setRescueStep(1)
        setTimeout(() => setMessages(prev => [...prev, {
          role: 'assistant',
          content: `**${next.ticker.toUpperCase()}${next.lossP ? ` (lỗ ${next.lossP}%)` : ''}**\n\n${RESCUE_QUESTIONS[0]}`
        }]), 500)
      } else {
        setRescueMode(false)
        setTimeout(() => setMessages(prev => [...prev, {
          role: 'assistant',
          content: '✅ **Khám xong toàn bộ danh mục.**\n\nBạn đã có đánh giá rủi ro cho từng mã. Quyết định thuộc về bạn.'
        }]), 600)
      }
    }
  }

  return (
    <div id="vip-ai-chat" style={{ maxWidth: '760px', margin: '0 auto 16px', padding: '0 16px' }}>
      <div id="vip-ai-chat" style={{ background: C.bgCard, border: `1px solid ${C.purpleLight}55`, borderRadius: '16px', overflow: 'hidden', boxShadow: `0 4px 24px rgba(124,58,237,0.15)` }}>
        <div style={{ padding: '12px 16px', background: `linear-gradient(135deg, ${C.purple}33, ${C.purpleLight}22)`, borderBottom: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px' }}>💬</span>
            <span style={{ fontWeight: '700', fontSize: '13px', color: C.purpleLight }}>AI Advisor — Tư vấn riêng</span>
            <span style={{ ...badge(C.green), fontSize: '10px', padding: '1px 6px' }}>VIP</span>
          </div>
          {messages.length > 3 && (
            <button onClick={() => setExpanded(e => !e)} style={{ background: 'none', border: 'none', color: C.muted, cursor: 'pointer', fontSize: '12px' }}>
              {expanded ? '▲ Thu gọn' : `▼ Xem ${messages.length} tin nhắn`}
            </button>
          )}
        </div>
        <div style={{ minHeight: '88px', maxHeight: expanded ? '320px' : '96px', overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '8px', transition: 'max-height 0.3s ease' }} ref={containerRef}>
          {messages.length === 0 ? (
            <div style={{ color: C.muted, fontSize: '13px', lineHeight: '1.6' }}>
              <div>👋 Xin chào! Tôi có thể giúp bạn:</div>
              <div style={{ paddingLeft: '8px', marginTop: '4px' }}>• Phân tích cổ phiếu VN30 và xu hướng thị trường</div>
              <div style={{ paddingLeft: '8px' }}>• Đánh giá danh mục và gợi ý tỷ trọng</div>
            </div>
          ) : (
            latestMessages.map((m, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{ maxWidth: '82%' }}>
                  {/* FOMO/Panic badge — VIP có full IIS coaching */}
                  {m.role === 'assistant' && m.meta && m.meta.emotional_state && m.meta.emotional_state !== 'neutral' && (
                    <div style={{
                      display: 'inline-flex', alignItems: 'center', gap: '5px',
                      marginBottom: '5px', padding: '3px 9px', borderRadius: '10px',
                      fontSize: '11px', fontWeight: 600,
                      background: (m.meta.emotional_state === 'fomo' || m.meta.emotional_state === 'detected') ? 'rgba(239,68,68,0.2)' : m.meta.emotional_state === 'panic' ? 'rgba(245,158,11,0.2)' : 'rgba(59,130,246,0.2)',
                      color: (m.meta.emotional_state === 'fomo' || m.meta.emotional_state === 'detected') ? '#fca5a5' : m.meta.emotional_state === 'panic' ? '#fcd34d' : '#93c5fd',
                      border: '1px solid rgba(255,255,255,0.1)',
                    }}>
                      {(m.meta.emotional_state === 'fomo' || m.meta.emotional_state === 'detected') && '⚠️ FOMO detected'}
                      {m.meta.emotional_state === 'panic'    && '⚠️ Panic detected'}
                      {m.meta.emotional_state === 'avg_down' && '⚠️ Average down detected'}
                      {m.meta.iis_level_name && <span style={{ opacity:.7, marginLeft:'4px' }}>· {m.meta.iis_level_name}</span>}
                    </div>
                  )}
                  {m.role === 'assistant' ? (
                    <div style={{ padding: '8px 12px', borderRadius: '12px', fontSize: '13px', lineHeight: '1.6', color: '#fff',
                      background: '#1e1b2e',
                      borderBottomLeftRadius: '3px' }}
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(m.content) }}
                    />
                  ) : (
                    <div style={{ padding: '8px 12px', borderRadius: '12px', fontSize: '13px', lineHeight: '1.5', color: '#fff',
                      background: `linear-gradient(135deg, ${C.purple}, ${C.purpleLight})`,
                      borderBottomRightRadius: '3px' }}>
                      {m.content}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ background: '#1e1b2e', padding: '8px 12px', borderRadius: '12px', borderBottomLeftRadius: '3px' }}>
                <span style={{ color: C.muted, fontSize: '12px' }}>⏳ Đang phân tích...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        {/* === v2.2: Chip theo điểm nghẽn — TỐI ĐA 2 === */}
        {bnChips.length > 0 && !rescueMode && (
          <div style={{ padding: '0 12px 8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {bnChips.map((c, i) => (
              <button key={`bn-${i}`} onClick={() => handleSend(null, c)} style={{
                padding: '5px 11px', borderRadius: '16px',
                border: '1px solid rgba(245,158,11,0.35)',
                background: 'rgba(245,158,11,0.10)', color: '#fcd34d',
                fontSize: '11px', cursor: 'pointer', fontWeight: 500,
              }}>{c}</button>
            ))}
          </div>
        )}

                {/* Rescue: nhập cổ phiếu kẹp */}
        {rescueMode && rescueStep === 0 && (
          <div style={{ padding: '10px 12px', borderTop: `1px solid ${C.border}`, background: 'rgba(220,38,38,0.04)' }}>
            <div style={{ fontSize: '12px', color: '#fca5a5', marginBottom: '8px', fontWeight: 600 }}>🩺 Nhập cổ phiếu đang kẹp lỗ:</div>
            {rescueStocks.map((s, i) => (
              <div key={i} style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
                <input placeholder="Mã CP" value={s.ticker}
                  onChange={e => setRescueStocks(p => p.map((r,j) => j===i ? {...r, ticker: e.target.value.toUpperCase()} : r))}
                  style={{ flex:2, background:'#1a1730', border:`1px solid ${C.border}`, borderRadius:'8px', padding:'7px 10px', color:'#e2e8f0', fontSize:'12px', outline:'none' }} />
                <input placeholder="% lỗ" value={s.lossP}
                  onChange={e => setRescueStocks(p => p.map((r,j) => j===i ? {...r, lossP: e.target.value} : r))}
                  style={{ flex:1, background:'#1a1730', border:`1px solid ${C.border}`, borderRadius:'8px', padding:'7px 10px', color:'#e2e8f0', fontSize:'12px', outline:'none' }} />
                {rescueStocks.length > 1 && (
                  <button onClick={() => setRescueStocks(p => p.filter((_,j) => j!==i))}
                    style={{ background:'none', border:'none', color:'#64748b', cursor:'pointer', fontSize:'16px' }}>×</button>
                )}
              </div>
            ))}
            <div style={{ display:'flex', gap:'6px', marginTop:'4px' }}>
              <button onClick={() => setRescueStocks(p => [...p, {ticker:'',lossP:''}])}
                style={{ padding:'5px 10px', borderRadius:'7px', border:`1px solid ${C.border}`, background:'transparent', color:'#64748b', fontSize:'11px', cursor:'pointer' }}>
                + Thêm mã
              </button>
              <button onClick={submitRescueStocks} disabled={!rescueStocks.some(s => s.ticker.trim())}
                style={{ padding:'5px 12px', borderRadius:'7px', border:'none', background:'#dc2626', color:'#fff', fontSize:'11px', fontWeight:600, cursor:'pointer' }}>
                Bắt đầu →
              </button>
              <button onClick={() => { setRescueMode(false); setRescueStep(0) }}
                style={{ padding:'5px 10px', borderRadius:'7px', border:`1px solid ${C.border}`, background:'transparent', color:'#64748b', fontSize:'11px', cursor:'pointer' }}>
                Hủy
              </button>
            </div>
          </div>
        )}

        {/* Khám sức khỏe button */}
        {!rescueMode && (
          <div style={{ padding: '0 12px 8px' }}>
            <button onClick={startRescue} style={{
              width:'100%', padding:'7px 14px', borderRadius:'9px',
              border:'1px solid rgba(220,38,38,0.4)', background:'rgba(220,38,38,0.07)',
              color:'#fca5a5', fontSize:'12px', fontWeight:600, cursor:'pointer',
              display:'flex', alignItems:'center', justifyContent:'center', gap:'6px',
            }}>
              🩺 Khám sức khỏe danh mục kẹp
              <span style={{ fontSize:'10px', fontWeight:400, color:'#ef4444' }}>
                — AI phân tích vị thế lỗ, đưa kế hoạch thoát
              </span>
            </button>
          </div>
        )}

        <form onSubmit={rescueMode && rescueStep > 0
            ? (e) => { e.preventDefault(); handleRescueAnswer(input) }
            : handleSend} style={{ padding: '10px 12px', borderTop: `1px solid ${C.border}`, display: 'flex', gap: '8px', background: '#0f0b1e' }}>
          <input
            ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
            onFocus={() => messages.length > 0 && setExpanded(true)}
            placeholder={rescueMode && rescueStep > 0 ? "Nhập câu trả lời..." : "Hỏi về cổ phiếu VN30, xu hướng thị trường, danh mục..."}
            style={{ flex: 1, background: '#1a1730', border: `1px solid ${C.border}`, color: C.text, borderRadius: '10px', padding: '8px 14px', fontSize: '13px', outline: 'none' }}
          />
          <button type="submit" disabled={loading || !input.trim()} style={{ ...btn(C.purple), padding: '8px 16px', opacity: (loading || !input.trim()) ? 0.5 : 1, background: `linear-gradient(135deg, ${C.purple}, ${C.purpleLight})` }}>
            Gửi ➤
          </button>
        </form>
      </div>
    </div>
  )
}

// ─── MAIN ─────────────────────────────────────────────────────
export default function VIPDashboard({ user, onSwitchBasic, onOpenIIS }) {
  const [tab, setTab]         = useState('signals')
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)

  // BUG5 FIX: days state — default 30 ngày (không quá hẹp, không quá rộng)
  const [days, setDays] = useState(30)

  // BUG1 FIX: Gọi /api/vip/signals thay vì /api/signals
  // BUG5 FIX: Gửi ?days= param để backend filter theo ngày
  const fetchSignals = useCallback(async () => {
    setLoading(true)
    setFetchError(null)
    try {
      const daysParam = days === 999 ? '' : `?days=${days}`
      const url = `${API_BASE}/vip/signals${daysParam}`
      const res = await fetch(url, { headers: authHeaders() })

      if (!res.ok) {
        // Nếu 401/403 → có thể token expired
        if (res.status === 401 || res.status === 403) {
          setFetchError('Phiên VIP đã hết hạn. Vui lòng đăng nhập lại.')
          setSignals([])
          return
        }
        // Nếu 404 → route chưa được đăng ký trên server
        if (res.status === 404) {
          setFetchError('API /vip/signals chưa được khởi tạo trên server. Kiểm tra vip_signal_scanner.py đã được import trong backend_api.py chưa.')
          setSignals([])
          return
        }
        throw new Error(`HTTP ${res.status}`)
      }

      const d = await res.json()
      if (d.success) {
        setSignals(d.signals || [])
        setLastUpdate(new Date())
      } else {
        setFetchError(d.error || 'Lỗi không xác định từ server')
        setSignals([])
      }
    } catch (err) {
      setFetchError(`Không thể tải tín hiệu: ${err.message}`)
      setSignals([])
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => { fetchSignals() }, [fetchSignals])

  return (
    <div style={{ minHeight: '100vh', background: `linear-gradient(160deg,${C.bg} 0%,#0f0b1e 60%,#110a1a 100%)`,
      color: C.text, fontFamily: "'Inter',-apple-system,sans-serif", paddingBottom: '120px' }}>

      {/* VIP Header */}
      <div style={{ background: 'linear-gradient(135deg,#7c3aed18,#0b0a14)', borderBottom: `1px solid ${C.border}`, padding: '16px 24px' }}>
        <div style={{ maxWidth: '760px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '20px' }}>💎</span>
              <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '800',
                background: 'linear-gradient(135deg,#a855f7,#c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                VIP Dashboard
              </h2>
            </div>
            <p style={{ color: C.muted, fontSize: '12px', margin: '2px 0 0' }}>
              Xin chào <strong style={{ color: C.text }}>{user.name || user.full_name}</strong>
              {lastUpdate && <> · <span style={{ color: C.green }}>●</span> {lastUpdate.toLocaleTimeString('vi-VN')}</>}
            </p>
          </div>
          <TelegramBadge />
        </div>
      </div>

      {/* Sub-tabs */}
      <div style={{ borderBottom: `1px solid ${C.border}`, padding: '0 24px' }}>
        <div style={{ maxWidth: '760px', margin: '0 auto', display: 'flex', gap: '4px', paddingTop: '10px' }}>
          {[
            { key: 'signals',   label: '📊 Tín hiệu mua bán' },
            { key: 'portfolio', label: '💼 Quản trị đầu tư' },
          ].map(({ key, label }) => (
            <button key={key} onClick={() => setTab(key)} style={tabStyle(tab === key)}>{label}</button>
          ))}
        </div>
      </div>

      {/* IIS Score Widget — VIP có full IIS */}
      <div style={{ maxWidth: '760px', margin: '0 auto', padding: '20px 16px 0' }}>
        <IISScoreWidget
          userId={user.email}
          userTier={user.tier || 'vip'}
          onRequestUpdate={onOpenIIS || (() => {})}
        />
      </div>

      {/* Inline AI Chat — always visible */}
      <div style={{ paddingTop: '8px' }}>
        <InlineAIChat userId={user.email} />
      </div>

      {/* Content */}
      <div style={{ paddingTop: '8px' }}>
        {tab === 'signals' && (
          <VIPSignalsTab
            signals={signals}
            loading={loading}
            fetchError={fetchError}
            onRefresh={fetchSignals}
            days={days}
            onDaysChange={setDays}
          />
        )}
        {tab === 'portfolio' && <VIPPortfolioTab userId={user.email} />}
      </div>
    </div>
  )
}
