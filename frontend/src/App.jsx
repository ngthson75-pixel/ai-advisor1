import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'
import LandingPage from './components/LandingPage'
import SignalsModule from './components/SignalsModule'
import AIPortfolioManager from './components/AIPortfolioManager'
import SignalHistory from './components/SignalHistory'
import VIPDashboard from './components/VIPDashboard'
import VIPAdminPanel from './components/VIPAdminPanel'
import Blog from './components/Blog'
import IISTest from './components/IISTest'
import IISScoreWidget from './components/IISScoreWidget'

// API Configuration — same pattern as VIPDashboard.jsx (BUG6 fix)
// VITE_API_URL không set trên Cloudflare Pages → fallback về localhost → signals rỗng
// Fix: detect hostname để hardcode đúng backend URL
const _hostname     = typeof window !== 'undefined' ? window.location.hostname : ''
const _IS_STAGING   = _hostname.includes('staging')
const _IS_LOCALHOST = _hostname === 'localhost' || _hostname === '127.0.0.1'
const API_URL = _IS_STAGING
  ? 'https://ai-advisor1-staging.onrender.com/api'
  : _IS_LOCALHOST
    ? 'http://localhost:10000/api'
    : 'https://ai-advisor1-backend.onrender.com/api'

// ── Auth headers helper ──────────────────────────────────────────────────
function getAuthHeaders() {
  try {
    const stored = localStorage.getItem('user')
    if (!stored) return { 'Content-Type': 'application/json' }
    const u = JSON.parse(stored)
    if (u.token) return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${u.token}` }
  } catch {}
  return { 'Content-Type': 'application/json' }
}

// ── InlineAIChat — dùng cho Free, Basic, Trial ───────────────────────────
// Free: chat đầy đủ nhưng không có IIS coaching (FOMO/Panic gated)
// Basic/Trial: chat đầy đủ + IIS coaching
function InlineAIChat({ userId, userTier }) {
  const [messages,  setMessages]  = useState([])
  const [input,     setInput]     = useState('')
  const [loading,   setLoading]   = useState(false)
  const [expanded,  setExpanded]  = useState(false)
  const [focused,   setFocused]   = useState(false)
  const chatEndRef = useRef(null)
  const inputRef   = useRef(null)
  const isFree     = userTier === 'free'

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  // Load lịch sử chat + chào hỏi thị trường
  useEffect(() => {
    async function initChat() {
      try {
        const r = await fetch(`${API_URL}/chat/history?user_id=${userId}&limit=30`, { headers: getAuthHeaders() })
        const d = await r.json()
        if (d.success && d.messages?.length > 0) {
          setMessages(d.messages)
          setExpanded(true)
          return
        }
      } catch {}

      // Chưa có lịch sử → inject market summary
      try {
        const mr = await fetch(`${API_URL.replace('/api','')}/api/market-risk`)
        const md = await mr.json()
        if (md.success && md.data) {
          const m    = md.data
          const date = m.date ? new Date(m.date).toLocaleDateString('vi-VN', { day:'2-digit', month:'2-digit' }) : ''
          const riskEmoji = (m.risk_score ?? 50) <= 40 ? '🟢' : (m.risk_score ?? 50) <= 65 ? '🟡' : '🔴'
          const greeting = isFree
            ? `Xin chào! Đây là tóm tắt thị trường hôm nay (${date}):\n\n${riskEmoji} Chế độ thị trường: ${m.market_mode || '—'}\n📊 Điểm rủi ro: ${m.risk_score ?? '—'}/100\n💼 Tỷ trọng khuyến nghị: ${m.allocation ?? '—'}%\n\nBạn muốn tôi phân tích cổ phiếu nào không? (Nâng cấp Basic để dùng AI Coach FOMO/Panic)`
            : `Xin chào! Đây là tóm tắt thị trường hôm nay (${date}):\n\n${riskEmoji} Chế độ thị trường: ${m.market_mode || '—'}\n📊 Điểm rủi ro: ${m.risk_score ?? '—'}/100\n💼 Tỷ trọng khuyến nghị: ${m.allocation ?? '—'}%\n\nBạn muốn tôi phân tích cổ phiếu nào, hoặc đánh giá danh mục hiện tại không?`
          setMessages([{ role: 'assistant', content: greeting }])
        }
      } catch {}
    }
    if (userId) initChat()
  }, [userId, isFree])

  async function handleSend(e) {
    e.preventDefault()
    const msg = input.trim()
    if (!msg || loading) return
    setInput(''); setExpanded(true)
    setMessages(prev => [...prev, { role: 'user', content: msg }])
    setLoading(true)
    try {
      const r = await fetch(`${API_URL}/chat`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ user_id: userId, message: msg, user_tier: userTier }),
      })
      const d = await r.json()
      setMessages(prev => [...prev, { role: 'assistant', content: d.response || d.message || '...' }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Lỗi kết nối. Thử lại sau.' }])
    }
    setLoading(false)
  }

  const latestMessages = expanded ? messages : messages.slice(-3)
  const accentColor = isFree ? '#3b82f6' : '#10b981'  // blue for free, green for basic

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto 16px', padding: '0 16px' }}>
      <div style={{
        background: '#0f172a', border: `1px solid ${accentColor}44`,
        borderRadius: '16px',
        boxShadow: `0 4px 24px ${accentColor}18`,
      }}>
        {/* Header */}
        <div style={{
          padding: '12px 16px',
          background: `linear-gradient(135deg, ${accentColor}22, ${accentColor}11)`,
          borderBottom: '1px solid #1e293b',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '16px' }}>💬</span>
            <span style={{ fontWeight: '700', fontSize: '13px', color: '#e2e8f0' }}>
              AI Advisor — Tư vấn riêng
            </span>
            {isFree ? (
              <span style={{ fontSize: '10px', fontWeight: '700', background: '#3b82f644', color: '#60a5fa', padding: '1px 7px', borderRadius: '4px', border: '1px solid #3b82f644' }}>
                FREE
              </span>
            ) : (
              <span style={{ fontSize: '10px', fontWeight: '700', background: '#10b98144', color: '#34d399', padding: '1px 7px', borderRadius: '4px', border: '1px solid #10b98144' }}>
                BASIC
              </span>
            )}
            {isFree && (
              <span style={{ fontSize: '11px', color: '#64748b', marginLeft: '4px' }}>
                · AI Coach FOMO/Panic cần <span style={{ color: '#f59e0b', fontWeight: 600 }}>Basic</span>
              </span>
            )}
          </div>
          <button onClick={() => setExpanded(e => !e)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '12px' }}>
              {expanded ? '▲ Thu gọn' : messages.length > 0 ? `▼ Xem lịch sử (${messages.length})` : '▼ Mở chat'}
            </button>
        </div>

        {/* Messages — hidden when collapsed and no messages */}
        <div style={{
          minHeight: expanded ? '120px' : '0px',
          maxHeight: expanded ? '480px' : '0px',
          height: expanded ? 'auto' : '0',
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: expanded ? '12px 16px' : '0',
          display: expanded ? 'flex' : 'none',
          flexDirection: 'column', gap: '8px',
          transition: 'max-height 0.3s ease',
        }}>
          {messages.length === 0 ? (
            <div style={{ color: '#64748b', fontSize: '13px', lineHeight: '1.6' }}>
              <div>👋 Xin chào! Tôi có thể giúp bạn:</div>
              <div style={{ paddingLeft: '8px', marginTop: '4px' }}>• Phân tích cổ phiếu và xu hướng thị trường</div>
              <div style={{ paddingLeft: '8px' }}>• Đánh giá danh mục và gợi ý tỷ trọng</div>
              {!isFree && <div style={{ paddingLeft: '8px' }}>• AI Coach: kiểm soát FOMO và panic selling</div>}
            </div>
          ) : (
            latestMessages.map((m, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{
                  maxWidth: '82%', padding: '8px 12px', borderRadius: '12px',
                  fontSize: '13px', lineHeight: '1.5', color: '#fff',
                  background: m.role === 'user' ? `linear-gradient(135deg, ${accentColor}, ${accentColor}cc)` : '#1e293b',
                  borderBottomRightRadius: m.role === 'user' ? '3px' : '12px',
                  borderBottomLeftRadius:  m.role === 'user' ? '12px' : '3px',
                  whiteSpace: 'pre-wrap',
                }}>
                  {m.content}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{ background: '#1e293b', padding: '8px 12px', borderRadius: '12px', borderBottomLeftRadius: '3px' }}>
                <span style={{ color: '#64748b', fontSize: '12px' }}>⏳ Đang phân tích...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSend} style={{ padding: '10px 12px', borderTop: '1px solid #1e293b', display: 'flex', gap: '8px', background: '#080f1e' }}>
          <input
            ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
            onFocus={() => { setExpanded(true); setFocused(true) }}
            onBlur={() => setFocused(false)}
            placeholder={isFree ? 'Hỏi về cổ phiếu, xu hướng thị trường...' : 'Hỏi về cổ phiếu, danh mục, FOMO/Panic coaching...'}
            style={{ flex: 1, background: '#0f1a2e', border: '1px solid #1e293b', color: '#e2e8f0', borderRadius: '10px', padding: '8px 14px', fontSize: '13px', outline: 'none' }}
          />
          <button
            type="submit" disabled={loading || !input.trim()}
            style={{
              padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
              fontWeight: '600', fontSize: '13px', color: '#fff',
              background: `linear-gradient(135deg, ${accentColor}, ${accentColor}cc)`,
              opacity: (loading || !input.trim()) ? 0.5 : 1,
            }}
          >
            Gửi ➤
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Tier helpers ─────────────────────────────────────────────────────────
/**
 * Trả về tier hiện tại của user, tự động downgrade nếu trial hết hạn.
 * tier values: 'free' | 'basic_trial' | 'basic' | 'vip'
 */
function resolveUserTier(user) {
  if (!user) return 'free'
  if (user.isVip) return 'vip'

  const tier = user.tier || 'free'

  // Basic trial: kiểm tra còn hạn không
  if (tier === 'basic_trial') {
    const end = user.trialEndDate ? new Date(user.trialEndDate) : null
    if (!end || new Date() > end) {
      return 'free'   // Hết hạn → downgrade
    }
    return 'basic_trial'
  }

  return tier  // 'basic' hoặc 'free'
}

/** Số ngày còn lại của trial (trả -1 nếu không phải trial) */
function trialDaysLeft(user) {
  if (!user || user.tier !== 'basic_trial') return -1
  const end = user.trialEndDate ? new Date(user.trialEndDate) : null
  if (!end) return -1
  const diff = Math.ceil((end - new Date()) / (1000 * 60 * 60 * 24))
  return Math.max(0, diff)
}

function App() {
  const isAdmin = window.location.pathname === '/admin'
  const isBlog  = window.location.pathname.startsWith('/blog')

  const [user, setUser]             = useState(null)
  const [resolvedTier, setResolvedTier] = useState('free')
  const [activeTab, setActiveTab]   = useState('signals')
  const [showIISModal, setShowIISModal] = useState(false)
  const [signals, setSignals]       = useState([])
  const [loading, setLoading]       = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  // ── Load user từ localStorage ──────────────────────────────────────────
  useEffect(() => {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        // Migrate khách cũ chưa có tier → free
        if (!parsed.tier && !parsed.isVip) {
          parsed.tier = 'free'
        }
        const tier = resolveUserTier(parsed)
        // Nếu trial vừa hết → cập nhật localStorage
        if (parsed.tier === 'basic_trial' && tier === 'free') {
          parsed.tier = 'free'
          localStorage.setItem('user', JSON.stringify(parsed))
        }
        setUser(parsed)
        setResolvedTier(tier)
      } catch (e) {
        localStorage.removeItem('user')
      }
    }
  }, [])

  // ── Fetch signals: truyền ?delay=7 cho Free users ─────────────────────
  const fetchSignals = async (tier) => {
    const currentTier = tier || resolvedTier
    try {
      setLoading(true)
      const isFullAccess = ['basic_trial', 'basic', 'vip'].includes(currentTier)
      const url = isFullAccess ? `${API_URL}/signals` : `${API_URL}/signals?delay=7`
      const token = localStorage.getItem('authToken') || ''
      const response = await fetch(url, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      const data = await response.json()
      if (data.success) {
        setSignals(data.signals)
        setLastUpdate(new Date())
      }
    } catch (error) {
      console.error('Error fetching signals:', error)
      setSignals([])
      setLastUpdate(new Date())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      const tier = resolveUserTier(user)
      setResolvedTier(tier)
      fetchSignals(tier)
      const interval = setInterval(() => fetchSignals(tier), 5 * 60 * 1000)
      return () => clearInterval(interval)
    }
  }, [user])

  // ── Handlers ───────────────────────────────────────────────────────────
  const handleLogin = async (userData) => {
    const tier = resolveUserTier(userData)
    if (!userData.tier && !userData.isVip) {
      userData.tier = 'free'
      localStorage.setItem('user', JSON.stringify(userData))
    }
    setUser(userData)
    setResolvedTier(tier)
    if (userData.isVip) {
      setActiveTab('vip')
      // VIP cũng check IIS — họ có full coaching
      try {
        const r = await fetch(`${API_URL}/iis/result/${encodeURIComponent(userData.email)}`)
        const d = await r.json()
        if (!d.has_result) setShowIISModal(true)
      } catch {}
      return
    }

    // Auto-show IIS modal nếu user chưa làm test lần nào
    try {
      const r = await fetch(`${API_URL}/iis/result/${encodeURIComponent(userData.email)}`)
      const d = await r.json()
      if (!d.has_result) setShowIISModal(true)
    } catch { /* silent — không block login */ }
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    setUser(null)
    setResolvedTier('free')
    setActiveTab('signals')
  }

  // ── Blog (public, không cần login) ───────────────────────────────────
  if (isBlog)  return <Blog />

  // ── Admin panel ────────────────────────────────────────────────────────
  if (isAdmin) return <VIPAdminPanel />
  if (!user)   return <LandingPage onLogin={handleLogin} />

  const daysLeft    = trialDaysLeft(user)
  const isFree      = resolvedTier === 'free'
  const isTrial     = resolvedTier === 'basic_trial'
  const isBasic     = resolvedTier === 'basic'
  const isVip       = resolvedTier === 'vip'
  const hasFullAccess = isTrial || isBasic || isVip

  // ── Tier badge cho header ──────────────────────────────────────────────
  const TierBadge = () => {
    if (isVip)   return <span style={badgeStyle('#7c3aed','#a855f7')}>💎 VIP</span>
    if (isBasic) return <span style={badgeStyle('#059669','#10b981')}>✅ Basic</span>
    if (isTrial) return (
      <span style={badgeStyle('#d97706','#f59e0b')}>
        🕐 Trial {daysLeft}d còn
      </span>
    )
    return <span style={badgeStyle('#475569','#64748b')}>Free</span>
  }

  // ── Banners ────────────────────────────────────────────────────────────
  const FreeBanner = () => (
    <div style={{
      background: 'linear-gradient(90deg, #1a1200, #1a0a00)',
      border: '1px solid #f59e0b66',
      borderRadius: '10px',
      padding: '10px 18px',
      margin: '12px 0',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '8px',
      fontSize: '13px',
    }}>
      <div>
        <span style={{color:'#fbbf24', fontWeight:600}}>⏰ Tín hiệu đang hiển thị delay 7 ngày</span>
        <span style={{color:'#94a3b8', marginLeft:'8px'}}>— Nâng lên Basic để xem real-time</span>
      </div>
      <a href="https://ai-advisor.vn" target="_blank" rel="noreferrer" style={{
        background:'#f59e0b', color:'#000', border:'none',
        borderRadius:'6px', padding:'5px 14px',
        fontSize:'12px', fontWeight:700, cursor:'pointer',
        textDecoration:'none', whiteSpace:'nowrap',
      }}>
        Đăng ký Basic →
      </a>
    </div>
  )

  const TrialBanner = () => {
    const isLow = daysLeft <= 3
    return (
      <div style={{
        background: isLow ? 'linear-gradient(90deg,#2d0a0a,#1a0000)' : 'linear-gradient(90deg,#0a1a0a,#001a00)',
        border: `1px solid ${isLow ? '#ef444466' : '#22c55e44'}`,
        borderRadius: '10px',
        padding: '10px 18px',
        margin: '12px 0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px',
        fontSize: '13px',
      }}>
        <div>
          <span style={{color: isLow ? '#f87171' : '#4ade80', fontWeight:600}}>
            {isLow ? '⚠️' : '🎁'} Bạn đang dùng thử Basic — còn {daysLeft} ngày
          </span>
          <span style={{color:'#94a3b8', marginLeft:'8px'}}>
            {isLow ? '— Đăng ký ngay để không gián đoạn!' : '— Tín hiệu real-time, đầy đủ tính năng'}
          </span>
        </div>
        <a href="mailto:aiadvisorhotline@gmail.com" style={{
          background: isLow ? '#ef4444' : '#22c55e', color:'#fff', border:'none',
          borderRadius:'6px', padding:'5px 14px',
          fontSize:'12px', fontWeight:700, cursor:'pointer',
          textDecoration:'none', whiteSpace:'nowrap',
        }}>
          {isLow ? 'Đăng ký ngay →' : 'Nâng cấp Basic 199k →'}
        </a>
      </div>
    )
  }

  // ── Render ─────────────────────────────────────────────────────────────
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="brand">
              <div className="logo">
                <svg width="48" height="48" viewBox="0 0 40 40" fill="none">
                  <defs>
                    <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style={{stopColor: '#3b82f6', stopOpacity: 1}} />
                      <stop offset="100%" style={{stopColor: '#8b5cf6', stopOpacity: 1}} />
                    </linearGradient>
                  </defs>
                  <path d="M20 8L32 14V26L20 32L8 26V14L20 8Z" stroke="url(#logoGradient)" strokeWidth="2" fill="none"/>
                  <path d="M20 8V20M20 20L32 26M20 20L8 26" stroke="url(#logoGradient)" strokeWidth="2"/>
                  <circle cx="20" cy="20" r="3" fill="url(#logoGradient)"/>
                </svg>
              </div>
              <div className="brand-text">
                <h1>AI Advisor</h1>
                <p>Đầu tư thông minh với AI</p>
              </div>
            </div>

            <div className="header-right">
              {lastUpdate && (
                <div className="last-update">
                  <span className="pulse"></span>
                  Updated: {lastUpdate.toLocaleTimeString()}
                </div>
              )}

              <div className="user-menu">
                <div className="user-avatar" style={
                  isVip  ? { background:'linear-gradient(135deg,#7c3aed,#a855f7)', boxShadow:'0 0 12px rgba(168,85,247,0.5)' }
                  : isBasic ? { background:'linear-gradient(135deg,#059669,#10b981)', boxShadow:'0 0 8px rgba(16,185,129,0.3)' }
                  : isTrial ? { background:'linear-gradient(135deg,#d97706,#f59e0b)', boxShadow:'0 0 8px rgba(245,158,11,0.3)' }
                  : {}
                }>
                  {user.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="user-info">
                  <div className="user-name">
                    {user.name} <TierBadge />
                  </div>
                  <button onClick={handleLogout} className="logout-btn">Đăng xuất</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="nav-tabs">
        <div className="container">
          <div className="tabs">
            {!isVip && (
              <>
                <button
                  className={`tab ${activeTab === 'signals' ? 'active' : ''}`}
                  onClick={() => setActiveTab('signals')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  </svg>
                  Tín hiệu mua bán
                  <span className="badge">{signals.length}</span>
                </button>

                <button
                  className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
                  onClick={() => setActiveTab('portfolio')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                  </svg>
                  Quản trị đầu tư bằng AI
                </button>
              </>
            )}

            {isVip && (
              <>
                <button
                  className={`tab ${activeTab === 'vip' ? 'active' : ''}`}
                  onClick={() => setActiveTab('vip')}
                  style={activeTab === 'vip' ? {
                    background: 'linear-gradient(135deg,#7c3aed22,#a855f722)',
                    borderBottom: '2px solid #a855f7', color: '#c084fc',
                  } : { color: '#a855f7' }}
                >
                  💎 VIP Dashboard
                </button>
                <button
                  className={`tab ${activeTab === 'basic' ? 'active' : ''}`}
                  onClick={() => setActiveTab('basic')}
                  style={{
                    color: activeTab === 'basic' ? '#94a3b8' : '#64748b',
                    fontSize: '13px',
                    borderBottom: activeTab === 'basic' ? '2px solid #64748b' : 'none',
                  }}
                >
                  📊 Basic Dashboard
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="container">

          {/* ── AI Chat — luôn hiển thị cho Free/Basic, không phụ thuộc tab ── */}
          {!isVip && user && (
            <InlineAIChat userId={user.email} userTier={resolvedTier} />
          )}

          {/* ── Banners theo tier ── */}
          {isFree   && activeTab === 'signals' && <FreeBanner />}
          {isTrial  && activeTab === 'signals' && <TrialBanner />}

          {activeTab === 'signals' && (
            <>
              <SignalHistory />
              <SignalsModule
                signals={signals}
                loading={loading}
                onRefresh={fetchSignals}
              />
            </>
          )}

          {activeTab === 'portfolio' && (
            <>
              {/* IIS Widget — cùng maxWidth và padding với InlineAIChat */}
              <div style={{ maxWidth: '900px', margin: '0 auto 16px', padding: '0 16px' }}>
                <IISScoreWidget
                  userId={user.email}
                  onRequestUpdate={() => setShowIISModal(true)}
                />
              </div>
              <AIPortfolioManager userId={user.email} userTier={resolvedTier} hideChat={!isVip} />
            </>
          )}

          {activeTab === 'vip' && isVip && (
            <VIPDashboard user={user} onSwitchBasic={() => setActiveTab('basic')} onOpenIIS={() => setShowIISModal(true)} />
          )}

          {activeTab === 'basic' && isVip && (
            <>
              <SignalHistory />
              <SignalsModule signals={signals} loading={loading} onRefresh={fetchSignals} />
            </>
          )}
        </div>
      </main>

      {/* IIS Onboarding Modal */}
      {showIISModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: '#0a0f1e',
          overflowY: 'auto',
          display: 'flex', flexDirection: 'column',
        }}>
          {/* Header bar */}
          <div style={{
            padding: '12px 20px',
            borderBottom: '1px solid #1e293b',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: '#0f172a', flexShrink: 0,
          }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#C8780F' }}>
              AI ADVISOR — Investor Intelligence Score
            </span>
            <button
              onClick={() => setShowIISModal(false)}
              style={{
                background: 'transparent', border: '1px solid #334155',
                color: '#64748b', borderRadius: '6px',
                padding: '4px 10px', fontSize: '12px', cursor: 'pointer',
              }}
            >
              Bỏ qua ✕
            </button>
          </div>
          {/* IIS Test */}
          <div style={{ flex: 1 }}>
            <IISTest
              userId={user?.email}
              onComplete={(result) => {
                setShowIISModal(false)
                setActiveTab('portfolio')
              }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>© 2026 AI Advisor. Professional Stock Trading Signals Platform.</p>
          <p className="disclaimer">
            Đầu tư chứng khoán có rủi ro. Vui lòng tự nghiên cứu trước khi giao dịch.
          </p>
        </div>
      </footer>
    </div>
  )
}

// ── Helper ─────────────────────────────────────────────────────────────────
function badgeStyle(from, to) {
  return {
    marginLeft: '6px', fontSize: '10px', fontWeight: '700',
    background: `linear-gradient(135deg,${from},${to})`,
    color: '#fff', padding: '2px 7px', borderRadius: '4px',
    verticalAlign: 'middle', whiteSpace: 'nowrap',
  }
}

export default App
