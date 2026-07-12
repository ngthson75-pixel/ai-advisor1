import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';

// FIX: hostname detection — VITE_API_URL không set trên Cloudflare Pages
const _h = typeof window !== 'undefined' ? window.location.hostname : ''
const API_BASE = _h.includes('staging')
  ? 'https://ai-advisor1-staging.onrender.com/api'
  : (_h === 'localhost' || _h === '127.0.0.1')
    ? 'http://localhost:10000/api'
    : 'https://ai-advisor1-backend.onrender.com/api'

// VN30 tickers — dành riêng cho VIP Dashboard, ẩn khỏi Basic
const VN30_TICKERS = new Set([
  'ACB','BCM','BID','BVH','CTG','FPT','GAS','GVR','HDB','HPG',
  'MBB','MSN','MWG','PLX','POW','SAB','SHB','SSB','SSI','STB',
  'TCB','TPB','VCB','VHM','VIB','VIC','VJC','VNM','VPB','VRE',
]);

// Nhận props từ App.jsx — dùng chung data, không tự fetch riêng (tránh URL sai)

function AIBtn({ signal, openPopover, handleAIBtn }) {
  const id     = sigId(signal)
  const isOpen = openPopover === id
  return (
    <button
      onClick={(e) => handleAIBtn(e, signal)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '5px',
        padding: '4px 10px', borderRadius: '6px', cursor: 'pointer',
        fontSize: '11px', fontWeight: 600, whiteSpace: 'nowrap',
        background: isOpen ? 'rgba(59,130,246,0.2)' : 'rgba(59,130,246,0.08)',
        border: `1px solid ${isOpen ? '#3b82f6' : 'rgba(59,130,246,0.3)'}`,
        color: '#3b82f6', transition: 'all .15s',
      }}
    >
      🤖 Phân tích AI
    </button>
  )
}

function AIPopover({ openPopover, popoverSignal, popoverRef, popoverPos, setOpenPopover, computeScores, FEATURES, statusOf, watchNote }) {
  if (!openPopover || !popoverSignal) return null
  const scores = computeScores(popoverSignal)
  return (
    <div
      ref={popoverRef}
      style={{
        position: 'fixed', top: popoverPos.top, left: popoverPos.left,
        zIndex: 99999, width: '300px',
        background: '#080e1a', border: '1px solid #1e3a5f',
        borderRadius: '12px', boxShadow: '0 8px 32px rgba(0,0,0,0.7)',
        padding: '14px 16px',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div>
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#e2e8f0' }}>🤖 AI phân tích</span>
          <span style={{ marginLeft: '8px', fontSize: '13px', fontWeight: 700, color: '#3b82f6' }}>
            {popoverSignal.ticker || popoverSignal.code}
          </span>
        </div>
        <button onClick={() => setOpenPopover(null)}
          style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '20px', lineHeight: 1, padding: '0 2px' }}>
          ×
        </button>
      </div>

      <div style={{ fontSize: '10px', color: '#475569', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '10px' }}>
        AI đánh giá dựa trên:
      </div>

      {/* Feature bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
        {FEATURES.map(({ key, label, weight, icon }) => {
          const score  = scores[key]
          const status = statusOf(score)
          return (
            <div key={key}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3px' }}>
                <span style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  {icon} {label}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '10px', color: status.color, fontWeight: 600 }}>{status.label}</span>
                  <span style={{ fontSize: '10px', color: '#2d3f55', minWidth: '26px', textAlign: 'right' }}>{weight}%</span>
                </div>
              </div>
              <div style={{ height: '4px', background: '#1a2535', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: '2px', width: `${score}%`, background: status.color, opacity: 0.85, transition: 'width .4s ease' }} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Watch note */}
      <div style={{ borderTop: '1px solid #1e293b', paddingTop: '10px' }}>
        <div style={{ fontSize: '10px', color: '#3b82f6', fontWeight: 600, marginBottom: '4px' }}>📡 AI đang theo dõi</div>
        <div style={{ fontSize: '11px', color: '#64748b', lineHeight: 1.65 }}>{watchNote(scores)}</div>
      </div>
    </div>
  )
}
export default function SignalsModule({ signals: propSignals, loading: propLoading, onRefresh }) {
  const [signals,   setSignals]   = useState(propSignals || []);
  const [loading,   setLoading]   = useState(propLoading ?? true);
  const [error,     setError]     = useState(null);
  const [scanning,  setScanning]  = useState(false);
  const [activeTab, setActiveTab] = useState('buy');

  // Sync khi App.jsx fetch xong
  useEffect(() => { if (propSignals !== undefined) { setSignals(propSignals); setError(null); } }, [propSignals]);
  useEffect(() => { if (propLoading !== undefined) setLoading(propLoading); }, [propLoading]);

  // Fallback fetch — chỉ chạy nếu render standalone (không có propSignals)
  const fetchSignalsFallback = async () => {
    try {
      setLoading(true); setError(null);
      const res = await fetch(`${API_BASE}/signals`);
      const data = await res.json();
      if (data.success) setSignals(data.signals || []);
      else setError('Không thể tải tín hiệu');
    } catch (err) {
      setError('Lỗi kết nối: ' + err.message);
    } finally { setLoading(false); }
  };

  useEffect(() => {
    if (propSignals === undefined) fetchSignalsFallback();
  }, []);

  const handleRefresh = () => { onRefresh ? onRefresh() : fetchSignalsFallback(); };

  const triggerScan = async () => {
    try {
      setScanning(true);
      const res = await fetch(`${API_BASE}/scan`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        alert('Đã bắt đầu quét! Vui lòng đợi 2-3 phút và refresh lại.');
        setTimeout(handleRefresh, 180000);
      }
    } catch (err) {
      alert('Lỗi khi quét: ' + err.message);
    } finally { setScanning(false); }
  };

  // Filter signals by tab
  const buySignals = signals
    .filter(s => (s.action === 'BUY' || !s.action) && !VN30_TICKERS.has((s.ticker || s.code || '').toUpperCase()))
    .sort((a, b) => {
      // Open/partial signals first, closed last
      const statusOrder = { open: 0, partial: 1, closed: 2 };
      const sa = statusOrder[a.status] ?? 0;
      const sb = statusOrder[b.status] ?? 0;
      if (sa !== sb) return sa - sb;
      // Within same status: sort by signal date DESC (newest first)
      const da = a.date ? new Date(a.date).getTime() : 0;
      const db = b.date ? new Date(b.date).getTime() : 0;
      return db - da;
    });
  const sellSignals = signals
    .filter(s => s.action === 'SELL')
    .sort((a, b) => {
      const da = a.date ? new Date(a.date).getTime() : 0;
      const db = b.date ? new Date(b.date).getTime() : 0;
      return db - da;
    });
  const displaySignals = activeTab === 'buy' ? buySignals : sellSignals;

  // === HELPER FUNCTIONS: Signal tracking display ===
  const getStatusDisplay = (signal) => {
    const status = signal.status || (signal.action === 'BUY' ? 'open' : 'closed');
    if (status === 'open')    return { text: 'Mở',         icon: '🟢', color: '#10b981', bg: '#dcfce7' };
    if (status === 'partial') return { text: 'Bán 1 phần', icon: '🟡', color: '#f59e0b', bg: '#fef3c7' };
    if (status === 'closed')  return { text: 'Đóng',       icon: '🔴', color: '#ef4444', bg: '#fee2e2' };
    return { text: 'Mở', icon: '🟢', color: '#10b981', bg: '#dcfce7' };
  };

  const getPositionPct = (signal) => {
    if (signal.position_pct !== undefined && signal.position_pct !== null) return signal.position_pct;
    return signal.action === 'BUY' ? 100 : 0;
  };

const getExitReason = (signal) => {
    const reason = signal.exit_reason || signal.strategy || '';
    if (reason === 'STOP_LOSS')        return { text: 'Cắt lỗ (SL)',    icon: '🔴', color: '#ef4444', bg: '#fee2e2' };
    if (reason === 'TAKE_PROFIT')      return { text: 'Chốt lời (TP)',  icon: '🟢', color: '#10b981', bg: '#dcfce7' };
    if (reason === 'MA20_BREAK')       return { text: 'MA20 Cross',      icon: '🟠', color: '#f59e0b', bg: '#fef3c7' };
    if (reason === 'MA20_CONSECUTIVE') return { text: 'MA20 (2 ngày)',   icon: '🟠', color: '#f59e0b', bg: '#fef3c7' };
    if (reason === 'MA20_HIGH_VOLUME') return { text: 'MA20 (Vol cao)',  icon: '🟠', color: '#f59e0b', bg: '#fef3c7' };
    return { text: 'Thủ công', icon: '⚪', color: '#94a3b8', bg: '#1e293b' };
  };
  // ================================================

  // ════════════════════════════════════════════════════════════════════════
  // SIGNAL REASONING — Bloomberg-style feature bars (Popover)
  // ════════════════════════════════════════════════════════════════════════

  const FEATURES = [
    { key: 'trend',      label: 'Xu hướng',    weight: 30, icon: '📈' },
    { key: 'momentum',   label: 'Động lượng',  weight: 22, icon: '⚡' },
    { key: 'market',     label: 'Thị trường',  weight: 18, icon: '🏛️' },
    { key: 'moneyflow',  label: 'Dòng tiền',   weight: 15, icon: '💰' },
    { key: 'liquidity',  label: 'Thanh khoản', weight: 10, icon: '🔄' },
    { key: 'volatility', label: 'Biến động',   weight:  5, icon: '📊' },
  ]

  const computeScores = (signal) => {
    const s  = signal.strength || 0
    const r  = signal.rsi      || 50
    const rr = (() => {
      if (signal.risk_reward) return parseFloat(signal.risk_reward)
      if (signal.entry_price && signal.stop_loss && signal.take_profit)
        return (signal.take_profit - signal.entry_price) / (signal.entry_price - signal.stop_loss)
      return 2
    })()
    return {
      trend:      Math.min(100, Math.round(s * 1.05)),
      momentum:   r <= 30 ? 95 : r <= 40 ? 85 : r <= 50 ? 70 : r <= 60 ? 52 : 32,
      market:     s >= 80 ? 88 : s >= 65 ? 70 : s >= 50 ? 52 : 38,
      moneyflow:  Math.min(100, Math.round((s * 0.6) + (Math.max(0, 70 - r) * 0.8))),
      liquidity:  signal.stock_type === 'Blue Chip' ? 95 : signal.stock_type === 'Mid Cap' ? 75 : 48,
      volatility: rr >= 3 ? 88 : rr >= 2 ? 68 : rr >= 1.5 ? 48 : 30,
    }
  }

  const statusOf = (score) =>
    score >= 80 ? { label: 'Tích cực',     color: '#22c55e' }
  : score >= 60 ? { label: 'Khá tốt',      color: '#3b82f6' }
  : score >= 40 ? { label: 'Trung bình',   color: '#f59e0b' }
  :               { label: 'Cần theo dõi', color: '#ef4444' }

  const watchNote = (scores) => {
    const weak = FEATURES.filter(f => scores[f.key] < 50).map(f => f.label.toLowerCase())
    if (!weak.length) return 'Tất cả tiêu chí đều đạt ngưỡng tích cực. AI sẽ cảnh báo nếu bất kỳ điều kiện nào suy yếu.'
    return `AI đang theo dõi ${weak.join(', ')}. Tín hiệu sẽ được đánh giá lại nếu các chỉ số này tiếp tục suy yếu.`
  }

  // id luôn là string để so sánh nhất quán
  const sigId = (s) => String(s.id || s.signal_code || s.ticker || '')

  // Popover state
  const [openPopover, setOpenPopover] = useState(null)
  const [popoverPos,  setPopoverPos]  = useState({ top: 0, left: 0 })
  const [popoverSignal, setPopoverSignal] = useState(null)  // lưu signal object trực tiếp
  const popoverRef = React.useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target))
        setOpenPopover(null)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleAIBtn = (e, signal) => {
    e.stopPropagation()
    const id = sigId(signal)
    if (openPopover === id) { setOpenPopover(null); setPopoverSignal(null); return }
    const rect   = e.currentTarget.getBoundingClientRect()
    const scrollY = window.scrollY || document.documentElement.scrollTop
    setPopoverPos({
      top:  rect.bottom + scrollY + 6,
      left: Math.max(8, Math.min(rect.left, window.innerWidth - 316)),
    })
    setOpenPopover(id)
    setPopoverSignal(signal)  // lưu trực tiếp — tránh stale closure
  }

  // ════════════════════════════════════════════════════════════════════════

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <RefreshCw className="spin" size={40} style={{ color: '#3b82f6' }} />
        <p style={{ marginTop: '20px', color: '#94a3b8' }}>Đang tải tín hiệu...</p>
      </div>
    );
  }

  return (
    <div className="signals-module">
      {/* Header */}
      <div className="signals-header">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <TrendingUp size={28} style={{ color: '#3b82f6' }} />
            Tín Hiệu Giao Dịch
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '14px' }}>
            Tín hiệu được tạo tự động từ hệ thống phân tích AI
          </p>
        </div>

        <button 
          onClick={handleRefresh}
          disabled={scanning}
          style={{
            padding: '10px 20px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <RefreshCw size={16} className={scanning ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* NEW: Tabs */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveTab('buy')}
          style={{
            padding: '12px 24px',
            backgroundColor: activeTab === 'buy' ? '#10b981' : '#334155',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s'
          }}
        >
          📈 Tín hiệu MUA ({buySignals.length})
        </button>
        
        <button
          onClick={() => setActiveTab('sell')}
          style={{
            padding: '12px 24px',
            backgroundColor: activeTab === 'sell' ? '#ef4444' : '#334155',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s'
          }}
        >
          📉 Tín hiệu BÁN ({sellSignals.length})
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: '15px',
          background: '#fee',
          border: '1px solid #fcc',
          borderRadius: '8px',
          marginBottom: '20px',
          color: '#c33'
        }}>
          <AlertCircle size={20} style={{ marginRight: '10px' }} />
          {error}
        </div>
      )}

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#10b981' }}>
            {buySignals.length}
          </div>
          <div className="stat-label">Tín hiệu MUA</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#ef4444' }}>
            {sellSignals.length}
          </div>
          <div className="stat-label">Tín hiệu BÁN</div>
        </div>

        <div className="stat-card">
          <div className="stat-value" style={{ color: '#3b82f6' }}>
            {buySignals.filter(s => (s.strength || 0) >= 70).length}
          </div>
          <div className="stat-label">Tín hiệu mạnh (&gt;70%)</div>
        </div>

        <div className="stat-card">
          <div className="stat-value" style={{ color: '#f59e0b' }}>
            {signals.length}
          </div>
          <div className="stat-label">Tổng tín hiệu</div>
        </div>
      </div>

      {/* Signals Table */}
      {displaySignals.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          background: '#1e293b',
          borderRadius: '12px',
          border: '1px dashed #334155'
        }}>
          <AlertCircle size={48} style={{ color: '#64748b', marginBottom: '15px' }} />
          <h3 style={{ color: '#94a3b8', marginBottom: '10px' }}>
            Chưa có tín hiệu {activeTab === 'buy' ? 'MUA' : 'BÁN'}
          </h3>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '20px' }}>
            Hệ thống sẽ tự động quét và cập nhật tín hiệu mới
          </p>
          <button
            onClick={triggerScan}
            disabled={scanning}
            style={{
              padding: '12px 24px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: scanning ? 'not-allowed' : 'pointer',
              opacity: scanning ? 0.6 : 1
            }}
          >
            {scanning ? 'Đang quét...' : 'Quét ngay'}
          </button>
        </div>
      ) : (
        <div>
          {/* ===== MOBILE CARDS ===== */}
          <div className="mobile-cards">
            {activeTab === 'buy' && displaySignals.map((signal, idx) => {
              const statusDisplay = getStatusDisplay(signal);
              const positionPct = getPositionPct(signal);
              const barColor = positionPct === 100 ? '#10b981' : positionPct === 0 ? '#6b7280' : '#f59e0b';
              const strength = signal.strength || 0;
              const strengthColor = strength >= 70 ? '#10b981' : strength >= 50 ? '#3b82f6' : strength > 0 ? '#f59e0b' : '#6b7280';
              return (
                <div key={signal.id || idx} style={{
                  background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                  border: '1px solid #334155',
                  borderRadius: '14px',
                  padding: '16px',
                  marginBottom: '12px',
                  borderLeft: '4px solid #10b981'
                }}>
                  {/* Header row */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <strong style={{ color: '#3b82f6', fontSize: '22px', letterSpacing: '1px' }}>
                      {signal.ticker || signal.code}
                    </strong>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span style={{
                        padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold',
                        background: strengthColor, color: 'white'
                      }}>{strength > 0 ? `${strength.toFixed(0)}%` : 'N/A'}</span>
                      <span style={{
                        padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '600',
                        background: signal.stock_type === 'Blue Chip' ? '#1d4ed8' : signal.stock_type === 'Mid Cap' ? '#6d28d9' : '#374151',
                        color: 'white'
                      }}>{signal.stock_type || 'N/A'}</span>
                    </div>
                  </div>

                  {/* Price grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                      <div style={{ color: '#94a3b8', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Giá vào</div>
                      <div style={{ color: '#e2e8f0', fontWeight: '700', fontSize: '14px' }}>{signal.entry_price?.toLocaleString() || '-'}</div>
                    </div>
                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                      <div style={{ color: '#ef4444', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Stop Loss</div>
                      <div style={{ color: '#ef4444', fontWeight: '700', fontSize: '14px' }}>{signal.stop_loss?.toLocaleString() || '-'}</div>
                    </div>
                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                      <div style={{ color: '#10b981', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Take Profit</div>
                      <div style={{ color: '#10b981', fontWeight: '700', fontSize: '14px' }}>{signal.take_profit?.toLocaleString() || '-'}</div>
                    </div>
                  </div>

                  {/* Footer row */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span style={{
                        fontFamily: 'monospace', fontSize: '11px', padding: '3px 8px',
                        backgroundColor: '#0f172a', color: '#60a5fa',
                        borderRadius: '6px', border: '1px solid #1e40af', fontWeight: '600'
                      }}>{signal.signal_code || `#${signal.id}`}</span>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: '4px',
                        padding: '3px 8px', borderRadius: '12px',
                        backgroundColor: statusDisplay.bg, color: statusDisplay.color,
                        fontSize: '11px', fontWeight: '600'
                      }}>{statusDisplay.icon} {statusDisplay.text}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ color: '#94a3b8', fontSize: '11px' }}>Vị thế:</span>
                      <div style={{ width: '60px', height: '6px', backgroundColor: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${positionPct}%`, height: '100%', backgroundColor: barColor, borderRadius: '3px' }} />
                      </div>
                      <span style={{ fontSize: '12px', color: barColor, fontWeight: '700' }}>{positionPct}%</span>
                    </div>
                    <span style={{ color: '#64748b', fontSize: '11px' }}>
                      📅 {signal.date ? new Date(signal.date).toLocaleDateString('vi-VN') : 'N/A'}
                    </span>
                  </div>

                  {/* ── AI Reasoning ── */}
                  <div style={{ marginTop: '10px' }}><AIBtn signal={signal} openPopover={openPopover} handleAIBtn={handleAIBtn} /></div>
                </div>
              );
            })}

            {activeTab === 'sell' && displaySignals.map((signal, idx) => {
              const exitReason = getExitReason(signal);
              
              // Use exit_price from database (NEW column)
              const exitPrice = signal.exit_price || 0;
              const entryPrice = signal.entry_price || 0;
              
              // Calculate P/L percentage
              const plPct = entryPrice > 0 
                ? ((exitPrice - entryPrice) / entryPrice * 100) 
                : 0;
              
              const plColor = plPct >= 0 ? '#10b981' : '#ef4444';
              const plIcon = plPct >= 0 ? '📈' : '📉';
              
              return (
                <div key={signal.id || idx} style={{
                  background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                  border: '1px solid #334155',
                  borderRadius: '14px',
                  padding: '16px',
                  marginBottom: '12px',
                  borderLeft: `4px solid ${plColor}`
                }}>
                  {/* Header row */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <strong style={{ color: '#ef4444', fontSize: '22px', letterSpacing: '1px' }}>
                      {signal.ticker || signal.code}
                    </strong>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: '4px',
                        padding: '4px 10px', borderRadius: '12px',
                        backgroundColor: exitReason.bg, color: exitReason.color,
                        fontSize: '12px', fontWeight: '600'
                      }}>{exitReason.icon} {exitReason.text}</span>
                    </div>
                  </div>

                  {/* Price grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                      <div style={{ color: '#94a3b8', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Giá vào</div>
                      <div style={{ color: '#e2e8f0', fontWeight: '700', fontSize: '14px' }}>
                        {entryPrice > 0 ? entryPrice.toLocaleString() : '-'}
                      </div>
                    </div>
                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                      <div style={{ color: '#94a3b8', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Giá ra</div>
                      <div style={{ color: exitReason.color, fontWeight: '700', fontSize: '14px' }}>
                        {exitPrice > 0 ? exitPrice.toLocaleString() : '-'}
                      </div>
                    </div>
                    <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                      <div style={{ color: '#94a3b8', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>P/L</div>
                      <div style={{ 
                        color: plColor, 
                        fontWeight: '700', 
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '2px'
                      }}>
                        {plIcon} {plPct >= 0 ? '+' : ''}{plPct.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Footer */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                    <span style={{ 
                      color: '#64748b', 
                      fontSize: '11px',
                      padding: '3px 8px',
                      background: '#0f172a',
                      borderRadius: '6px'
                    }}>
                      📅 Vào: {signal.date ? new Date(signal.date).toLocaleDateString('vi-VN') : 'N/A'}
                    </span>
                    <span style={{ 
                      color: '#64748b', 
                      fontSize: '11px',
                      padding: '3px 8px',
                      background: '#0f172a',
                      borderRadius: '6px'
                    }}>
                      📅 Ra: {signal.exit_date ? new Date(signal.exit_date).toLocaleDateString('vi-VN') : 'N/A'}
                    </span>
                    <span style={{
                      padding: '3px 8px',
                      background: signal.stock_type === 'Blue Chip' ? '#1d4ed8' : signal.stock_type === 'Mid Cap' ? '#6d28d9' : '#374151',
                      color: 'white',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: '600'
                    }}>
                      {signal.stock_type || 'N/A'}
                    </span>
                  </div>

                  {/* ── AI Analysis ── */}
                  <div style={{ marginTop: '10px' }}><AIBtn signal={signal} openPopover={openPopover} handleAIBtn={handleAIBtn} /></div>
                </div>
              );
            })}
          </div>

          {/* ===== DESKTOP TABLE ===== */}
          <div className="desktop-table" style={{ overflowX: 'auto' }}>
          {/* ===== BUY TABLE: 9 cột ===== */}
          {activeTab === 'buy' && (
            <table className="signals-table">
              <thead>
                <tr>
                  <th>Mã CK</th>
                  <th>Giá vào</th>
                  <th>Stop Loss</th>
                  <th>Take Profit</th>
                  <th>Score</th>
                  <th>Loại</th>
                  <th>Ngày</th>
                  <th>Mã Tín Hiệu</th>
                  <th>Trạng Thái</th>
                  <th>Vị Thế</th>
                  <th>Phân tích</th>
                </tr>
              </thead>
              <tbody>
                {displaySignals.map((signal, idx) => {
                  const statusDisplay = getStatusDisplay(signal);
                  const positionPct = getPositionPct(signal);
                  const barColor = positionPct === 100 ? '#10b981' : positionPct === 0 ? '#6b7280' : '#f59e0b';
                  const sigId = signal.id || signal.signal_code || signal.ticker
                  return (
                    <React.Fragment key={sigId || idx}>
                      <tr>
                        <td>
                          <strong style={{ color: '#3b82f6', fontSize: '16px' }}>
                            {signal.ticker || signal.code}
                          </strong>
                        </td>
                        <td>{signal.entry_price?.toLocaleString()}</td>
                        <td style={{ color: '#ef4444' }}>{signal.stop_loss?.toLocaleString()}</td>
                        <td style={{ color: '#10b981' }}>{signal.take_profit?.toLocaleString()}</td>
                        <td>
                          <span style={{
                            padding: '4px 12px',
                            background: (signal.strength || 0) >= 70 ? '#10b981' :
                                       (signal.strength || 0) >= 50 ? '#3b82f6' :
                                       (signal.strength || 0) > 0 ? '#f59e0b' : '#6b7280',
                            color: 'white', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold'
                          }}>
                            {(signal.strength || 0) > 0 ? `${(signal.strength || 0).toFixed(0)}%` : 'N/A'}
                          </span>
                        </td>
                        <td>
                          <span style={{
                            padding: '4px 8px',
                            background: signal.stock_type === 'Blue Chip' ? '#3b82f6' :
                                       signal.stock_type === 'Mid Cap' ? '#8b5cf6' : '#6b7280',
                            borderRadius: '6px', fontSize: '11px', color: 'white', fontWeight: '500'
                          }}>
                            {signal.stock_type || 'N/A'}
                          </span>
                        </td>
                        <td style={{ color: '#94a3b8', fontSize: '13px' }}>
                          {signal.date ? new Date(signal.date).toLocaleDateString('vi-VN') : 'N/A'}
                        </td>
                        <td>
                          <span style={{
                            fontFamily: 'monospace', fontSize: '12px', padding: '4px 8px',
                            backgroundColor: '#0f172a', color: '#60a5fa',
                            borderRadius: '6px', border: '1px solid #1e40af', fontWeight: '600'
                          }}>
                            {signal.signal_code || `#${signal.id}`}
                          </span>
                        </td>
                        <td>
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', gap: '4px',
                            padding: '4px 10px', borderRadius: '12px',
                            backgroundColor: statusDisplay.bg, color: statusDisplay.color,
                            fontSize: '12px', fontWeight: '600'
                          }}>
                            {statusDisplay.icon} {statusDisplay.text}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <div style={{ width: '64px', height: '6px', backgroundColor: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ width: `${positionPct}%`, height: '100%', backgroundColor: barColor, borderRadius: '3px', transition: 'width 0.3s' }} />
                            </div>
                            <span style={{ fontSize: '12px', color: barColor, fontWeight: '600', minWidth: '32px' }}>
                              {positionPct}%
                            </span>
                          </div>
                        </td>
                        <td><AIBtn signal={signal} openPopover={openPopover} handleAIBtn={handleAIBtn} /></td>
                      </tr>
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          )}

          {/* ===== SELL TABLE: 8 cột + Exit Price, Exit Date, P/L ===== */}
          {activeTab === 'sell' && (
            <table className="signals-table">
              <thead>
                <tr>
                  <th>Mã CK</th>
                  <th>Giá vào</th>
                  <th>Giá ra</th>
                  <th>P/L</th>
                  <th>Lý do bán</th>
                  <th>Loại</th>
                  <th>Ngày vào</th>
                  <th>Ngày ra</th>
                </tr>
              </thead>
              <tbody>
                {displaySignals.map((signal, idx) => {
                  const exitReason = getExitReason(signal);
                  
                  // Use exit_price from database (NEW column)
                  const exitPrice = signal.exit_price || 0;
                  const entryPrice = signal.entry_price || 0;
                  
                  // Calculate P/L percentage
                  const plPct = entryPrice > 0 
                    ? ((exitPrice - entryPrice) / entryPrice * 100) 
                    : 0;
                  
                  const plColor = plPct >= 0 ? '#10b981' : '#ef4444';
                  const plIcon = plPct >= 0 ? '📈' : '📉';
                  
                  return (
                    <tr key={signal.id || idx}>
                      <td>
                        <strong style={{ color: '#ef4444', fontSize: '16px' }}>
                          {signal.ticker || signal.code}
                        </strong>
                      </td>
                      <td style={{ color: '#94a3b8', fontSize: '14px' }}>
                        {entryPrice > 0 ? entryPrice.toLocaleString() : '-'}
                      </td>
                      <td style={{ color: exitReason.color, fontWeight: '600', fontSize: '14px' }}>
                        {exitPrice > 0 ? exitPrice.toLocaleString() : '-'}
                      </td>
                      <td>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: '4px',
                          padding: '4px 10px', borderRadius: '12px',
                          backgroundColor: plPct >= 0 ? '#dcfce7' : '#fee2e2',
                          color: plColor,
                          fontSize: '12px', fontWeight: '700'
                        }}>
                          {plIcon} {plPct >= 0 ? '+' : ''}{plPct.toFixed(2)}%
                        </span>
                      </td>
                      <td>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: '4px',
                          padding: '4px 10px', borderRadius: '12px',
                          backgroundColor: exitReason.bg, color: exitReason.color,
                          fontSize: '12px', fontWeight: '600'
                        }}>
                          {exitReason.icon} {exitReason.text}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          padding: '4px 8px',
                          background: signal.stock_type === 'Blue Chip' ? '#3b82f6' :
                                     signal.stock_type === 'Mid Cap' ? '#8b5cf6' : '#6b7280',
                          borderRadius: '6px', fontSize: '11px', color: 'white', fontWeight: '500'
                        }}>
                          {signal.stock_type || 'N/A'}
                        </span>
                      </td>
                      <td style={{ color: '#94a3b8', fontSize: '13px' }}>
                        {signal.date ? new Date(signal.date).toLocaleDateString('vi-VN') : 'N/A'}
                      </td>
                      <td style={{ color: '#94a3b8', fontSize: '13px' }}>
                        {signal.exit_date ? new Date(signal.exit_date).toLocaleDateString('vi-VN') : 'N/A'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
          </div>{/* end desktop-table */}
        </div>
      )}

      <style jsx>{`
        .signals-module {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .signals-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 30px;
          flex-wrap: wrap;
          gap: 20px;
        }

        .stat-card {
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          padding: 20px;
          border-radius: 12px;
          border: 1px solid #334155;
        }

        .stat-value {
          font-size: 32px;
          font-weight: bold;
          margin-bottom: 5px;
        }

        .stat-label {
          color: #94a3b8;
          font-size: 14px;
        }

        .signals-table {
          width: 100%;
          border-collapse: collapse;
          background: #1e293b;
          border-radius: 12px;
          overflow: hidden;
        }

        .signals-table th {
          background: #0f172a;
          padding: 15px;
          text-align: left;
          color: #94a3b8;
          font-weight: 600;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .signals-table td {
          padding: 15px;
          border-top: 1px solid #334155;
          color: #e2e8f0;
        }

        .signals-table tbody tr:hover {
          background: #334155;
          cursor: pointer;
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
          .signals-header {
            flex-direction: column;
          }

          .signals-table {
            font-size: 12px;
          }

          .signals-table th,
          .signals-table td {
            padding: 10px 8px;
          }

          .mobile-cards {
            display: block;
          }

          .desktop-table {
            display: none;
          }
        }

        @media (min-width: 769px) {
          .mobile-cards {
            display: none;
          }

          .desktop-table {
            display: block;
          }
        }
      `}</style>

      {/* AI Analysis Popover — global fixed position */}
      <AIPopover />
    </div>
  );
}
