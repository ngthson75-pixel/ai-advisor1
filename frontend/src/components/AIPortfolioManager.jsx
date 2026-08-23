import IISScoreWidget from './IISScoreWidget'
import { useState, useEffect } from 'react'
import { track } from '../analytics'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

const fmt = (n) => n?.toLocaleString('vi-VN') || '0'
const fmtPct = (n) => (n >= 0 ? '+' : '') + n?.toFixed(1) + '%'

export default function AIPortfolioManager({ userId, userTier = 'free', onOpenIIS }) {
  // ── Portfolio state ──────────────────────────────────────────
  const [portfolio, setPortfolio] = useState([])
  const [cash, setCash]           = useState(0)
  const [cashInput, setCashInput] = useState('')
  const [editingCash, setEditingCash] = useState(false)

  const [addForm, setAddForm]     = useState({ ticker: '', quantity: '', price: '' })
  const [addLoading, setAddLoading] = useState(false)
  const [addError, setAddError]   = useState('')

  // ── Chat state ───────────────────────────────────────────────


  // ── Market risk for header badge ─────────────────────────────
  const [marketMode, setMarketMode] = useState(null)

  // ── Load data on mount ───────────────────────────────────────
  useEffect(() => {
    loadPortfolio()
    loadCash()
    loadMarketMode()
  }, [userId])



  async function loadPortfolio() {
    try {
      const r = await fetch(`${API_BASE}/portfolio?user_id=${userId}`)
      const d = await r.json()
      if (d.success) setPortfolio(d.portfolio || [])
    } catch {}
  }

  async function loadCash() {
    try {
      const r = await fetch(`${API_BASE}/cash?user_id=${userId}`)
      const d = await r.json()
      if (d.success) {
        setCash(d.cash || 0)
        setCashInput(d.cash > 0 ? String(d.cash) : '')
      }
    } catch {}
  }



  async function loadMarketMode() {
    try {
      const r = await fetch(`${API_BASE.replace('/api', '')}/api/market-risk`)
      const d = await r.json()
      if (d.success && d.data) setMarketMode(d.data)
    } catch {}
  }

  // ── Portfolio actions ────────────────────────────────────────
  async function handleAddStock(e) {
    e.preventDefault()
    if (!addForm.ticker || !addForm.quantity || !addForm.price) {
      setAddError('Vui lòng điền đầy đủ thông tin')
      return
    }
    setAddLoading(true)
    setAddError('')
    try {
      const r = await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ticker: addForm.ticker.toUpperCase(),
          quantity: parseInt(addForm.quantity),
          price: parseFloat(addForm.price)
        })
      })
      const d = await r.json()
      if (d.success) {
        track('portfolio_stock_add', { ticker: addForm.ticker.toUpperCase(), user_tier: userTier })
        setAddForm({ ticker: '', quantity: '', price: '' })
        loadPortfolio()
      } else {
        setAddError(d.error || 'Lỗi thêm cổ phiếu')
      }
    } catch { setAddError('Lỗi kết nối') }
    setAddLoading(false)
  }

  async function handleDeleteStock(ticker) {
    if (!confirm(`Xóa ${ticker} khỏi danh mục?`)) return
    track('portfolio_stock_del', { ticker, user_tier: userTier })
    try {
      await fetch(`${API_BASE}/portfolio/${ticker}?user_id=${userId}`, { method: 'DELETE' })
      loadPortfolio()
    } catch {}
  }

  async function handleSaveCash() {
    const val = parseFloat(cashInput.replace(/[^0-9.]/g, '')) || 0
    try {
      const r = await fetch(`${API_BASE}/cash`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, cash: val })
      })
      const d = await r.json()
      if (d.success) {
        track('portfolio_cash_set', { user_tier: userTier })
        setCash(val)
        setEditingCash(false)
      }
    } catch {}
  }

  // ── Chat ─────────────────────────────────────────────────────


  // ── Computed totals ──────────────────────────────────────────
  const totalStock   = portfolio.reduce((s, p) => s + (p.current_value || 0), 0)
  const totalCost    = portfolio.reduce((s, p) => s + (p.cost || 0), 0)
  const totalPL      = totalStock - totalCost
  const totalPLPct   = totalCost > 0 ? (totalPL / totalCost) * 100 : 0
  const totalAssets  = totalStock + cash
  const stockPct     = totalAssets > 0 ? (totalStock / totalAssets) * 100 : 0
  const cashPct      = totalAssets > 0 ? (cash / totalAssets) * 100 : 0

  const modeColor = {
    BULL: '#00e676', SIDEWAYS: '#ffd600', 'THAN TRONG': '#ffd600', BEAR: '#ff1744'
  }[marketMode?.market_mode] || '#94a3b8'

  const quickPrompts = [
    'Danh mục tôi đang ở mức rủi ro nào?',
    'Tỷ trọng có phù hợp thị trường không?',
    'Cổ phiếu nào nên xem xét bán?',
  ]

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
      maxWidth: '900px',
      margin: '0 auto',
      padding: '0 0 40px',
      fontFamily: "'DM Sans', sans-serif",
    }}>

      {/* ── IIS SCORE WIDGET ── */}
      <IISScoreWidget
        userId={userId}
        onRequestUpdate={onOpenIIS || (() => {})}
      />



      {/* ══════════════════════════════════════════════
          PHẦN 2: DANH MỤC (bên dưới)
      ══════════════════════════════════════════════ */}
      <div style={{
        background: 'linear-gradient(160deg, #0f172a 0%, #1a1f3a 100%)',
        borderRadius: '16px',
        border: '1px solid #1e293b',
        overflow: 'hidden',
      }}>
        {/* Portfolio header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid #1e293b',
          display: 'flex', alignItems: 'center', gap: '10px',
        }}>
          <span style={{ fontSize: '18px' }}>📊</span>
          <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '15px' }}>Danh mục đầu tư</div>
        </div>

        {/* ── TỔNG QUAN: 4 cards bao gồm tiền mặt ── */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '12px',
          padding: '16px 20px',
        }}>
          {/* Tổng tài sản */}
          <SummaryCard
            label="Tổng tài sản"
            value={`${fmt(totalAssets)} ₫`}
            sub={portfolio.length > 0 || cash > 0 ? `${portfolio.length} mã · ${cashPct.toFixed(0)}% TM` : 'Chưa có dữ liệu'}
            accent="#2563eb"
          />
          {/* Giá trị cổ phiếu */}
          <SummaryCard
            label="Cổ phiếu"
            value={`${fmt(totalStock)} ₫`}
            sub={`${stockPct.toFixed(1)}% tổng tài sản`}
            accent="#7c3aed"
          />
          {/* Tiền mặt */}
          <SummaryCard
            label="Tiền mặt"
            value={`${fmt(cash)} ₫`}
            sub={`${cashPct.toFixed(1)}% tổng tài sản`}
            accent="#0891b2"
            onClick={() => setEditingCash(true)}
            clickable
          />
          {/* Lãi/Lỗ */}
          <SummaryCard
            label="Lãi/Lỗ"
            value={`${totalPL >= 0 ? '+' : ''}${fmt(totalPL)} ₫`}
            sub={totalCost > 0 ? fmtPct(totalPLPct) : '—'}
            accent={totalPL >= 0 ? '#10b981' : '#ef4444'}
            valueColor={totalPL >= 0 ? '#10b981' : '#ef4444'}
          />
        </div>

        {/* Allocation bar */}
        {totalAssets > 0 && (
          <div style={{ padding: '0 20px 16px' }}>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              fontSize: '12px', color: '#64748b', marginBottom: '6px',
            }}>
              <span>Cổ phiếu {stockPct.toFixed(1)}%</span>
              {marketMode && (
                <span style={{ color: modeColor }}>
                  Khuyến nghị: {marketMode.allocation}%
                </span>
              )}
              <span>Tiền mặt {cashPct.toFixed(1)}%</span>
            </div>
            <div style={{
              height: 8, borderRadius: 4,
              background: 'rgba(255,255,255,0.08)',
              overflow: 'hidden',
              position: 'relative',
            }}>
              <div style={{
                height: '100%',
                width: `${stockPct}%`,
                background: 'linear-gradient(90deg, #2563eb, #7c3aed)',
                borderRadius: 4,
                transition: 'width 0.5s ease',
              }}/>
              {/* Recommended line */}
              {marketMode && (
                <div style={{
                  position: 'absolute',
                  left: `${marketMode.allocation}%`,
                  top: 0, bottom: 0, width: 2,
                  background: modeColor,
                  opacity: 0.8,
                }}/>
              )}
            </div>
          </div>
        )}

        {/* ── Cập nhật tiền mặt ── */}
        <div style={{
          padding: '0 20px 16px',
          display: editingCash ? 'flex' : 'none',
          gap: '8px', alignItems: 'center',
        }}>
          <input
            value={cashInput}
            onChange={e => setCashInput(e.target.value)}
            placeholder="Nhập số tiền mặt (VND)"
            style={{
              flex: 1, padding: '8px 14px',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid #0891b2',
              borderRadius: '8px', color: '#e2e8f0', fontSize: '14px', outline: 'none',
            }}
            onKeyDown={e => e.key === 'Enter' && handleSaveCash()}
            autoFocus
          />
          <button onClick={handleSaveCash} style={{
            padding: '8px 16px',
            background: '#0891b2', border: 'none',
            borderRadius: '8px', color: '#fff',
            fontSize: '13px', cursor: 'pointer', fontWeight: 600,
          }}>Lưu</button>
          <button onClick={() => setEditingCash(false)} style={{
            padding: '8px 12px',
            background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px', color: '#94a3b8',
            fontSize: '13px', cursor: 'pointer',
          }}>✕</button>
        </div>

        {/* Nút mở nhập tiền mặt nếu chưa đang edit */}
        {!editingCash && (
          <div style={{ padding: '0 20px 12px' }}>
            <button onClick={() => setEditingCash(true)} style={{
              padding: '6px 14px',
              background: 'rgba(8,145,178,0.1)',
              border: '1px solid rgba(8,145,178,0.3)',
              borderRadius: '20px',
              color: '#67e8f9',
              fontSize: '12px', cursor: 'pointer',
            }}>
              💵 {cash > 0 ? 'Cập nhật tiền mặt' : 'Nhập tiền mặt'}
            </button>
          </div>
        )}

        {/* ── Thêm cổ phiếu ── */}
        <div style={{
          padding: '0 20px 16px',
          borderTop: '1px solid #1e293b',
          paddingTop: '16px',
        }}>
          <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px', fontWeight: 600 }}>
            + Thêm cổ phiếu
          </div>
          <form onSubmit={handleAddStock} style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr auto',
            gap: '8px',
          }}>
            {[
              { key: 'ticker', placeholder: 'Mã CP (VD: VCB)', upper: true },
              { key: 'quantity', placeholder: 'Số lượng (CP)', type: 'number' },
              { key: 'price', placeholder: 'Giá vốn (VND)', type: 'number' },
            ].map(f => (
              <input key={f.key}
                value={addForm[f.key]}
                onChange={e => setAddForm(prev => ({
                  ...prev,
                  [f.key]: f.upper ? e.target.value.toUpperCase() : e.target.value
                }))}
                placeholder={f.placeholder}
                type={f.type || 'text'}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px', color: '#e2e8f0',
                  fontSize: '13px', outline: 'none',
                  minWidth: 0,
                }}
                onFocus={e => e.target.style.borderColor = '#2563eb'}
                onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
              />
            ))}
            <button type="submit" disabled={addLoading} style={{
              padding: '8px 16px',
              background: addLoading ? 'rgba(37,99,235,0.3)' : 'linear-gradient(135deg, #2563eb, #1d4ed8)',
              border: 'none', borderRadius: '8px',
              color: '#fff', fontSize: '13px',
              cursor: addLoading ? 'not-allowed' : 'pointer',
              fontWeight: 600, whiteSpace: 'nowrap',
            }}>
              {addLoading ? '...' : 'Thêm'}
            </button>
          </form>
          {addError && (
            <div style={{ color: '#f87171', fontSize: '12px', marginTop: '6px' }}>{addError}</div>
          )}
        </div>

        {/* ── Danh sách cổ phiếu ── */}
        {portfolio.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%', borderCollapse: 'collapse',
              fontSize: '13px',
            }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                  {['Mã', 'SL', 'Giá vốn', 'Giá TT', 'Giá trị', 'Lãi/Lỗ', ''].map(h => (
                    <th key={h} style={{
                      padding: '10px 16px', textAlign: 'right',
                      color: '#64748b', fontWeight: 600, fontSize: '12px',
                      textTransform: 'uppercase', letterSpacing: '0.5px',
                      borderBottom: '1px solid #1e293b',
                      ...(h === 'Mã' || h === '' ? { textAlign: 'left' } : {}),
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolio.map((p, i) => {
                  const pl = p.pl_amount || 0
                  const plPct = p.pl_pct || 0
                  const isPos = pl >= 0
                  return (
                    <tr key={i} style={{
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '12px 16px', color: '#e2e8f0', fontWeight: 700 }}>
                        {p.ticker}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right', color: '#94a3b8' }}>
                        {fmt(p.quantity)}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right', color: '#94a3b8' }}>
                        {fmt(p.avg_price)}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right', color: '#e2e8f0' }}>
                        {fmt(p.current_price)}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right', color: '#e2e8f0' }}>
                        {fmt(p.current_value)}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        <span style={{ color: isPos ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                          {isPos ? '+' : ''}{fmt(pl)}<br/>
                          <span style={{ fontSize: '11px', opacity: 0.8 }}>
                            {fmtPct(plPct)}
                          </span>
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'left' }}>
                        <button onClick={() => handleDeleteStock(p.ticker)} style={{
                          padding: '4px 8px',
                          background: 'rgba(239,68,68,0.1)',
                          border: '1px solid rgba(239,68,68,0.2)',
                          borderRadius: '6px', color: '#f87171',
                          fontSize: '11px', cursor: 'pointer',
                          transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => e.target.style.background = 'rgba(239,68,68,0.25)'}
                        onMouseLeave={e => e.target.style.background = 'rgba(239,68,68,0.1)'}
                        >Xóa</button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{
            padding: '32px 20px',
            textAlign: 'center',
            color: '#475569',
            fontSize: '14px',
          }}>
            📭 Chưa có cổ phiếu nào trong danh mục.<br/>
            <span style={{ fontSize: '12px' }}>Thêm cổ phiếu ở trên để AI có thể tư vấn chính xác hơn.</span>
          </div>
        )}

        <div style={{ padding: '12px 20px', borderTop: '1px solid #1e293b' }}>
          <p style={{ fontSize: '11px', color: '#334155', margin: 0, textAlign: 'center' }}>
            AI Advisor là công cụ hỗ trợ quyết định, không phải tư vấn đầu tư.
            Mọi quyết định là trách nhiệm của bạn.
          </p>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1); }
        }
        @media (max-width: 600px) {
          form[style*="grid-template-columns"] {
            grid-template-columns: 1fr 1fr !important;
          }
          form[style*="grid-template-columns"] button {
            grid-column: 1 / -1;
          }
        }
      `}</style>
    </div>
  )
}

// ── Summary Card component ───────────────────────────────────
function SummaryCard({ label, value, sub, accent, valueColor, onClick, clickable }) {
  return (
    <div onClick={onClick}
      style={{
        padding: '14px 16px',
        background: 'rgba(255,255,255,0.03)',
        border: `1px solid ${accent}22`,
        borderRadius: '12px',
        cursor: clickable ? 'pointer' : 'default',
        transition: 'all 0.2s',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={e => { if (clickable) e.currentTarget.style.background = 'rgba(255,255,255,0.06)' }}
      onMouseLeave={e => { if (clickable) e.currentTarget.style.background = 'rgba(255,255,255,0.03)' }}
    >
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        height: 2, background: accent, borderRadius: '12px 12px 0 0',
      }}/>
      <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label} {clickable && <span style={{ color: accent, fontSize: '10px' }}>✎</span>}
      </div>
      <div style={{ fontSize: '16px', fontWeight: 700, color: valueColor || '#e2e8f0', marginBottom: '4px' }}>
        {value}
      </div>
      <div style={{ fontSize: '11px', color: '#475569' }}>{sub}</div>
    </div>
  )
}
