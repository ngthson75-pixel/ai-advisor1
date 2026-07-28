/**
 * MarketWatchWidget — Tầng 1
 * Tóm lược thị trường phiên sáng (11h) dựa trên data MarketRisk đã có.
 *
 * Data source: GET /api/market-risk  (đã có sẵn, không cần endpoint mới)
 * Refresh: tự động mỗi 30 phút trong giờ giao dịch (9h–15h)
 *
 * Props:
 *   userTier — 'free' | 'basic_trial' | 'basic' | 'vip'
 *   signals  — array signals từ App.jsx (đã có sẵn)
 */

import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'
const VIP_API  = import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:10000'

// ── Helpers ──────────────────────────────────────────────────────────────────

// Giờ VN (UTC+7)
const vnNow = () => new Date(Date.now() + 7 * 60 * 60 * 1000)

// Phiên hiện tại
const getSession = () => {
  const h = vnNow().getUTCHours()
  const m = vnNow().getUTCMinutes()
  const t = h * 60 + m
  if (t < 9 * 60)           return 'pre'       // Trước 9h
  if (t < 11 * 60 + 30)     return 'morning'   // 9h–11h30
  if (t < 13 * 60)          return 'lunch'     // 11h30–13h
  if (t < 14 * 60 + 45)     return 'afternoon' // 13h–14h45
  if (t <= 15 * 60)         return 'close'     // 14h45–15h
  return 'after'                                 // Sau 15h
}

// Là ngày giao dịch không (T2–T6)
const isTradingDay = () => {
  const d = vnNow().getUTCDay()   // 0=Sun … 6=Sat
  return d >= 1 && d <= 5
}

// Mode display config
const MODE_CONFIG = {
  BULL:     { label: 'TÍCH CỰC',   color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  border: 'rgba(34,197,94,0.25)',  icon: '🟢' },
  SIDEWAYS: { label: 'THẬN TRỌNG', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.25)', icon: '🟡' },
  BEAR:     { label: 'PHÒNG THỦ',  color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.25)',  icon: '🔴' },
}

// Tóm lược hành động theo mode + session
const getActionText = (mode, allocation, session, buyCount) => {
  const actions = {
    BULL: {
      morning:   `Xu hướng tích cực — duy trì tỷ trọng ${allocation}% cổ phiếu. Ưu tiên các mã trong danh sách tín hiệu AI.`,
      afternoon: `Phiên chiều tiếp tục xu hướng tích cực. Có thể giữ vị thế, chú ý chốt lời nếu mã tăng >5%.`,
      lunch:     `Nghỉ trưa — thị trường đang tích cực. Chuẩn bị chiến lược cho phiên chiều 13h.`,
      close:     `Phiên đóng cửa — market tích cực. Đánh giá danh mục, cân nhắc mở vị thế mới phiên mai.`,
      pre:       `Trước phiên — thị trường đang ở trạng thái tích cực. Chuẩn bị kế hoạch cho 9h.`,
      after:     `Kết thúc phiên — thị trường tích cực. Tỷ trọng khuyến nghị ${allocation}% cho phiên mai.`,
    },
    SIDEWAYS: {
      morning:   `Thị trường sideways — thận trọng, giữ tỷ trọng ${allocation}% cổ phiếu. Chỉ mua các mã có tín hiệu AI rõ ràng.`,
      afternoon: `Phiên chiều trong vùng sideways. Hạn chế mở vị thế mới, ưu tiên bảo vệ vốn.`,
      lunch:     `Thị trường sideways — theo dõi phiên chiều để xác nhận xu hướng.`,
      close:     `Đóng cửa sideways — cân nhắc giảm tỷ trọng về ${allocation}% nếu đang cao hơn.`,
      pre:       `Trước phiên — thị trường đang sideways. Chuẩn bị kế hoạch thận trọng.`,
      after:     `Kết thúc phiên sideways. Tỷ trọng khuyến nghị ${allocation}% cho phiên mai.`,
    },
    BEAR: {
      morning:   `⚠️ Thị trường rủi ro cao — giảm tỷ trọng về ${allocation}% cổ phiếu. Ưu tiên bảo vệ vốn, không mua đuổi.`,
      afternoon: `⚠️ Phiên chiều tiếp tục rủi ro. Cân nhắc cắt giảm vị thế nếu thấy dấu hiệu xấu.`,
      lunch:     `⚠️ Thị trường đang phòng thủ — theo dõi chặt phiên chiều.`,
      close:     `⚠️ Đóng cửa trong xu hướng xấu — xem xét giảm mạnh tỷ trọng về ${allocation}%.`,
      pre:       `⚠️ Trước phiên — thị trường đang rủi ro. Chuẩn bị kế hoạch phòng thủ.`,
      after:     `⚠️ Kết thúc phiên rủi ro. Tỷ trọng khuyến nghị chỉ ${allocation}% cho phiên mai.`,
    },
  }
  return (actions[mode] || actions.SIDEWAYS)[session] || actions.SIDEWAYS.morning
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function MarketWatchWidget({ userTier = 'free', signals = [] }) {
  const [data,        setData]        = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [lastFetch,   setLastFetch]   = useState(null)
  const [collapsed,   setCollapsed]   = useState(false)
  const [session,     setSession]     = useState(getSession())
  const [sectors,     setSectors]     = useState([])
  const [sectorLoading, setSectorLoading] = useState(false)

  // ── Fetch market risk data ─────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE.replace('/api', '')}/api/market-risk`)
      const d = await r.json()
      if (d.success && d.data) {
        setData(d.data)
        setLastFetch(new Date())
      }
    } catch {}
    finally { setLoading(false) }
  }, [])

  // Fetch sector pulse data
  const fetchSectors = useCallback(async () => {
    setSectorLoading(true)
    try {
      const r = await fetch(`${VIP_API}/api/sector-pulse`)
      const d = await r.json()
      if (d.success && d.sectors) setSectors(d.sectors)
    } catch {}
    finally { setSectorLoading(false) }
  }, [])

  useEffect(() => {
    fetchData()
    fetchSectors()
    // Cập nhật session mỗi phút
    const sessionTimer = setInterval(() => setSession(getSession()), 60 * 1000)
    // Refresh data mỗi 30 phút trong giờ giao dịch
    const dataTimer = setInterval(() => {
      if (isTradingDay()) { fetchData(); fetchSectors() }
    }, 30 * 60 * 1000)
    return () => { clearInterval(sessionTimer); clearInterval(dataTimer) }
  }, [fetchData, fetchSectors])

  // ── Derived values ─────────────────────────────────────────────
  const mode       = data?.market_mode || 'SIDEWAYS'
  const cfg        = MODE_CONFIG[mode] || MODE_CONFIG.SIDEWAYS
  const riskScore  = data?.risk_score  ?? 50
  const allocation = data?.allocation  ?? 50
  const vni        = data?.vnindex_value
  const factors    = Array.isArray(data?.factors) ? data.factors : []

  // Signal counts từ prop
  const buySignals  = signals.filter(s => s.action === 'BUY'  && s.status === 'open')
  const sellSignals = signals.filter(s => s.action === 'SELL' || s.status === 'closed')
  const strongBuys  = buySignals.filter(s => (s.strength || 0) >= 70)

  // 11h morning note — chỉ hiện trong phiên sáng
  const isMorningSession = session === 'morning'
  const vnTime = vnNow()
  const isNear11 = vnTime.getUTCHours() === 3 && vnTime.getUTCMinutes() >= 45  // 10h45 UTC+7 ≈ 11h VN
    || vnTime.getUTCHours() === 4  // 11h UTC+7

  const sessionLabel = {
    pre:       '⏰ Trước phiên',
    morning:   '📈 Phiên sáng',
    lunch:     '🍜 Nghỉ trưa',
    afternoon: '📊 Phiên chiều',
    close:     '🔔 Sắp đóng cửa',
    after:     '✅ Kết thúc phiên',
  }[session]

  const actionText = getActionText(mode, allocation, session, buySignals.length)

  // ── Không hiện ngoài giờ giao dịch (thứ 7, CN) nếu không có data ──
  if (!isTradingDay() && !data) return null

  // ── Render ────────────────────────────────────────────────────
  return (
    <div style={{
      background: `linear-gradient(135deg, #0a0f1e 0%, #0d1525 100%)`,
      border: `1px solid ${cfg.border}`,
      borderRadius: '14px',
      marginBottom: '16px',
      overflow: 'hidden',
      transition: 'all .2s',
    }}>

      {/* ── Header bar ── */}
      <div
        onClick={() => setCollapsed(v => !v)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '11px 16px',
          background: cfg.bg,
          borderBottom: collapsed ? 'none' : `1px solid ${cfg.border}`,
          cursor: 'pointer', userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '15px' }}>📺</span>
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#e2e8f0' }}>
            Market Watch
          </span>
          {/* Session pill */}
          <span style={{
            fontSize: '10px', fontWeight: 600,
            padding: '2px 7px', borderRadius: '10px',
            background: cfg.bg, border: `1px solid ${cfg.border}`,
            color: cfg.color,
          }}>
            {sessionLabel}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Mode badge */}
          {data && (
            <span style={{
              fontSize: '11px', fontWeight: 700,
              padding: '3px 10px', borderRadius: '20px',
              background: cfg.color + '22',
              border: `1px solid ${cfg.color}55`,
              color: cfg.color,
            }}>
              {cfg.icon} {cfg.label}
            </span>
          )}
          {/* Refresh time */}
          {lastFetch && (
            <span style={{ fontSize: '10px', color: '#334155' }}>
              {lastFetch.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          {/* Toggle */}
          <span style={{ color: '#475569', fontSize: '12px' }}>
            {collapsed ? '▼' : '▲'}
          </span>
        </div>
      </div>

      {/* ── Body ── */}
      {!collapsed && (
        <div style={{ padding: '14px 16px' }}>

          {loading && (
            <div style={{ textAlign: 'center', padding: '20px', color: '#475569', fontSize: '13px' }}>
              Đang tải dữ liệu thị trường...
            </div>
          )}

          {!loading && !data && (
            <div style={{ textAlign: 'center', padding: '16px', color: '#475569', fontSize: '13px' }}>
              Chưa có dữ liệu thị trường hôm nay.
            </div>
          )}

          {!loading && data && (
            <>
              {/* ── Row 1: 3 số liệu chính ── */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '10px',
                marginBottom: '14px',
              }}>
                {/* Risk Score */}
                <div style={metricCard(cfg.color)}>
                  <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Risk Score
                  </div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: cfg.color, lineHeight: 1 }}>
                    {riskScore}
                  </div>
                  <div style={{ fontSize: '10px', color: '#475569', marginTop: '3px' }}>/100</div>
                  {/* Mini bar */}
                  <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', marginTop: '6px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${riskScore}%`, background: cfg.color, borderRadius: '2px' }} />
                  </div>
                </div>

                {/* Tỷ trọng khuyến nghị */}
                <div style={metricCard('#3b82f6')}>
                  <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Tỷ trọng CP
                  </div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: '#3b82f6', lineHeight: 1 }}>
                    {allocation}%
                  </div>
                  <div style={{ fontSize: '10px', color: '#475569', marginTop: '3px' }}>khuyến nghị</div>
                  <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', marginTop: '6px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${allocation}%`, background: '#3b82f6', borderRadius: '2px' }} />
                  </div>
                </div>

                {/* Tín hiệu mua */}
                <div style={metricCard('#22c55e')}>
                  <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Tín hiệu AI
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                    <span style={{ fontSize: '22px', fontWeight: 700, color: '#22c55e', lineHeight: 1 }}>
                      {buySignals.length}
                    </span>
                    <span style={{ fontSize: '11px', color: '#475569' }}>MUA</span>
                  </div>
                  <div style={{ fontSize: '10px', color: '#475569', marginTop: '3px' }}>
                    {strongBuys.length} mạnh (&gt;70%)
                  </div>
                  <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', marginTop: '6px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${Math.min(100, buySignals.length * 2)}%`, background: '#22c55e', borderRadius: '2px' }} />
                  </div>
                </div>
              </div>

              {/* ── Row 2: Tóm lược phiên sáng 11h ── */}
              <div style={{
                background: 'rgba(59,130,246,0.06)',
                border: '1px solid rgba(59,130,246,0.15)',
                borderRadius: '10px',
                padding: '12px 14px',
                marginBottom: '12px',
              }}>
                {/* Label phiên sáng */}
                {isMorningSession && (
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '5px',
                    fontSize: '10px', fontWeight: 700, color: '#f59e0b',
                    marginBottom: '7px', letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                  }}>
                    ☀️ TÓM LƯỢC 11H SÁNG
                  </div>
                )}

                {/* Action text */}
                <div style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.7, marginBottom: '8px' }}>
                  {actionText}
                </div>

                {/* VN-Index nếu có */}
                {vni && (
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '6px',
                    fontSize: '12px', color: '#64748b',
                    background: '#0f172a', borderRadius: '6px',
                    padding: '4px 10px',
                  }}>
                    <span>VN30 tham chiếu:</span>
                    <span style={{ color: '#e2e8f0', fontWeight: 600 }}>
                      {vni.toLocaleString('vi-VN', { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                )}
              </div>

              {/* ── Row 3: Factors (nếu có) ── */}
              {factors.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontSize: '10px', color: '#334155', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '8px' }}>
                    Tín hiệu kỹ thuật
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                    {factors.slice(0, 6).map((f, i) => {
                      const fStr   = typeof f === 'string' ? f : String(f || '')
                      const isUp   = fStr.toLowerCase().includes('tăng') || fStr.toLowerCase().includes('tích') || fStr.toLowerCase().includes('bull') || fStr.toLowerCase().includes('phục')
                      const isDown = fStr.toLowerCase().includes('giảm') || fStr.toLowerCase().includes('rủi') || fStr.toLowerCase().includes('bear') || fStr.toLowerCase().includes('cảnh')
                      const fColor = isUp ? '#22c55e' : isDown ? '#ef4444' : '#64748b'
                      return (
                        <span key={i} style={{
                          fontSize: '11px', color: fColor,
                          background: fColor + '12',
                          border: `1px solid ${fColor}30`,
                          borderRadius: '6px', padding: '3px 8px',
                          lineHeight: 1.4,
                        }}>
                          {fStr || f}
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* ── Row 4: Sector Pulse ── */}
              {sectors.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{
                    fontSize: '10px', color: '#334155', fontWeight: 600,
                    letterSpacing: '0.05em', textTransform: 'uppercase',
                    marginBottom: '8px',
                  }}>
                    📊 Dòng tiền theo ngành (EOD)
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                    {sectors.slice(0, 8).map((s) => {
                      const isUp   = s.avg_pct > 0
                      const isFlat = Math.abs(s.avg_pct) < 0.1
                      const color  = isFlat ? '#64748b' : isUp ? '#22c55e' : '#ef4444'
                      const barW   = Math.min(100, Math.abs(s.avg_pct) * 20) // max 5% = 100%
                      return (
                        <div key={s.sector}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px' }}>
                            <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                              {s.sector}
                              <span style={{ fontSize: '10px', color: '#475569', marginLeft: '4px' }}>
                                ({s.advancing}↑ {s.declining}↓)
                              </span>
                            </span>
                            <span style={{ fontSize: '11px', fontWeight: 600, color }}>
                              {isUp ? '+' : ''}{s.avg_pct}%
                            </span>
                          </div>
                          {/* Bar */}
                          <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{
                              height: '100%', borderRadius: '2px',
                              width: `${barW}%`, background: color, opacity: 0.8,
                            }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  {/* Top movers nhanh */}
                  {sectors[0]?.top_movers?.length > 0 && (
                    <div style={{ marginTop: '8px', fontSize: '10px', color: '#475569' }}>
                      Dẫn dắt: {sectors.slice(0, 3).map(s =>
                        `${s.sector} (${s.avg_pct > 0 ? '+' : ''}${s.avg_pct}%)`
                      ).join(' · ')}
                    </div>
                  )}
                </div>
              )}

              {/* ── Row 5: Disclaimer nhỏ ── */}
              <div style={{ fontSize: '10px', color: '#1e293b', lineHeight: 1.5 }}>
                Market Watch cập nhật EOD mỗi ngày sau 15h · Dữ liệu từ hệ thống phân tích AI Advisor
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ── Style helper ────────────────────────────────────────────────────────────
const metricCard = (accentColor) => ({
  background: '#0a0f1e',
  border: `1px solid ${accentColor}22`,
  borderRadius: '10px',
  padding: '10px 12px',
})
