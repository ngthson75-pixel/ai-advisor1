import { useState, useEffect } from 'react'
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
import AIAdvisorChat from './components/AIAdvisorChat'
import PortfolioRescue from './components/PortfolioRescue'

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

// ── GA4 helper (safe — không crash nếu gtag chưa load) ───────────────────
function track(eventName, params = {}) {
  try {
    if (typeof window.gtag === 'function') {
      window.gtag('event', eventName, params)
    }
  } catch (e) { /* silent */ }
}

// ── Tier helpers ─────────────────────────────────────────────────────────
function resolveUserTier(user) {
  if (!user) return 'free'
  if (user.isVip) return 'vip'
  const tier = user.tier || 'free'
  if (tier === 'basic_trial') {
    const end = user.trialEndDate ? new Date(user.trialEndDate) : null
    if (!end || new Date() > end) return 'free'
    return 'basic_trial'
  }
  return tier
}

function trialDaysLeft(user) {
  if (!user || user.tier !== 'basic_trial') return -1
  const end = user.trialEndDate ? new Date(user.trialEndDate) : null
  if (!end) return -1
  return Math.max(0, Math.ceil((end - new Date()) / (1000 * 60 * 60 * 24)))
}

function App() {
  const isAdmin = window.location.pathname === '/admin'
  const isBlog  = window.location.pathname.startsWith('/blog')

  const [user, setUser]                 = useState(null)
  const [resolvedTier, setResolvedTier] = useState('free')
  const [activeTab, setActiveTab]       = useState('signals')
  const [showIISModal, setShowIISModal] = useState(false)
  const [signals, setSignals]           = useState([])
  const [loading, setLoading]           = useState(true)
  const [lastUpdate, setLastUpdate]     = useState(null)

  // ── Load user từ localStorage ─────────────────────────────────────────
  useEffect(() => {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        if (!parsed.tier && !parsed.isVip) parsed.tier = 'free'
        const tier = resolveUserTier(parsed)
        if (parsed.tier === 'basic_trial' && tier === 'free') {
          parsed.tier = 'free'
          localStorage.setItem('user', JSON.stringify(parsed))
        }
        setUser(parsed)
        setResolvedTier(tier)

        // ✅ GA4: User quay lại (session restore từ localStorage)
        track('session_restore', { user_tier: tier })

      } catch (e) {
        localStorage.removeItem('user')
      }
    }
  }, [])

  // ── Fetch signals ─────────────────────────────────────────────────────
  const fetchSignals = async (tier) => {
    const currentTier = tier || resolvedTier
    try {
      setLoading(true)
      const isFullAccess = ['basic_trial', 'basic', 'vip'].includes(currentTier)
      // FIX (2026-07-01): luôn truyền ?delay tường minh (0 hoặc 7).
      // Trước đây full-access gọi /signals KHÔNG kèm param, khiến backend
      // tự ý auto-detect qua JWT token (mà FE không hề gửi) và MẶC ĐỊNH
      // ép delay=7 cho mọi request thiếu token — kể cả VIP đã login.
      // Truyền rõ delay=0 đảm bảo backend luôn nhận đúng ý định real-time.
      const url = isFullAccess ? `${API_URL}/signals?delay=0` : `${API_URL}/signals?delay=7`
      const response = await fetch(url)
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

  // ── Handlers ──────────────────────────────────────────────────────────
  const handleLogin = async (userData) => {
    const tier = resolveUserTier(userData)
    if (!userData.tier && !userData.isVip) {
      userData.tier = 'free'
      localStorage.setItem('user', JSON.stringify(userData))
    }
    setUser(userData)
    setResolvedTier(tier)

    // ✅ GA4: Login event — quan trọng nhất để đo DAU
    track('login', {
      user_tier:  tier,
      is_vip:     !!userData.isVip,
      login_type: 'email',
    })

    if (userData.isVip) {
      setActiveTab('vip')
      try {
        const r = await fetch(`${API_URL}/iis/result/${encodeURIComponent(userData.email)}`)
        const d = await r.json()
        if (!d.has_result) {
          setShowIISModal(true)
          // ✅ GA4: IIS modal hiện ra (chưa làm test)
          track('iis_modal_shown', { user_tier: tier, trigger: 'login_vip' })
        }
      } catch {}
      return
    }

    try {
      const r = await fetch(`${API_URL}/iis/result/${encodeURIComponent(userData.email)}`)
      const d = await r.json()
      if (!d.has_result) {
        setShowIISModal(true)
        // ✅ GA4: IIS modal hiện ra
        track('iis_modal_shown', { user_tier: tier, trigger: 'login_new' })
      } else {
        // ✅ GA4: User đã có IIS score (returning user đã test)
        track('iis_already_done', { user_tier: tier, iis_score: d.total })
      }
    } catch {}
  }

  const handleLogout = () => {
    // ✅ GA4: Logout
    track('logout', { user_tier: resolvedTier })
    localStorage.removeItem('user')
    setUser(null)
    setResolvedTier('free')
    setActiveTab('signals')
  }

  // ── Tab change tracking ───────────────────────────────────────────────
  const handleTabChange = (tab) => {
    setActiveTab(tab)
    // ✅ GA4: Xem tab nào
    track('tab_view', { tab_name: tab, user_tier: resolvedTier })
  }

  // ── Blog ──────────────────────────────────────────────────────────────
  if (isBlog)  return <Blog />
  if (isAdmin) return <VIPAdminPanel />
  if (!user)   return <LandingPage onLogin={handleLogin} />

  const daysLeft    = trialDaysLeft(user)
  const isFree      = resolvedTier === 'free'
  const isTrial     = resolvedTier === 'basic_trial'
  const isBasic     = resolvedTier === 'basic'
  const isVip       = resolvedTier === 'vip'
  const hasFullAccess = isTrial || isBasic || isVip

  // ── Tier badge ────────────────────────────────────────────────────────
  const TierBadge = () => {
    if (isVip)   return <span style={badgeStyle('#7c3aed','#a855f7')}>💎 VIP</span>
    if (isBasic) return <span style={badgeStyle('#059669','#10b981')}>✅ Basic</span>
    if (isTrial) return (
      <span style={badgeStyle('#d97706','#f59e0b')}>🕐 Trial {daysLeft}d còn</span>
    )
    return <span style={badgeStyle('#475569','#64748b')}>Free</span>
  }

  // ── Banners ───────────────────────────────────────────────────────────
  const FreeBanner = () => (
    <div style={{
      background: 'linear-gradient(90deg, #1a1200, #1a0a00)',
      border: '1px solid #f59e0b66', borderRadius: '10px',
      padding: '10px 18px', margin: '12px 0',
      display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', flexWrap: 'wrap',
      gap: '8px', fontSize: '13px',
    }}>
      <div>
        <span style={{color:'#fbbf24', fontWeight:600}}>⏰ Tín hiệu đang hiển thị delay 7 ngày</span>
        <span style={{color:'#94a3b8', marginLeft:'8px'}}>— Nâng lên Basic để xem real-time</span>
      </div>
      <a
        href="https://ai-advisor.vn" target="_blank" rel="noreferrer"
        onClick={() => track('upgrade_click', { source: 'free_banner', user_tier: 'free' })}
        style={{
          background:'#f59e0b', color:'#000', border:'none',
          borderRadius:'6px', padding:'5px 14px',
          fontSize:'12px', fontWeight:700, cursor:'pointer',
          textDecoration:'none', whiteSpace:'nowrap',
        }}
      >
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
        borderRadius: '10px', padding: '10px 18px', margin: '12px 0',
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', flexWrap: 'wrap',
        gap: '8px', fontSize: '13px',
      }}>
        <div>
          <span style={{color: isLow ? '#f87171' : '#4ade80', fontWeight:600}}>
            {isLow ? '⚠️' : '🎁'} Bạn đang dùng thử Basic — còn {daysLeft} ngày
          </span>
          <span style={{color:'#94a3b8', marginLeft:'8px'}}>
            {isLow ? '— Đăng ký ngay để không gián đoạn!' : '— Tín hiệu real-time, đầy đủ tính năng'}
          </span>
        </div>
        <a
          href="mailto:aiadvisorhotline@gmail.com"
          onClick={() => track('upgrade_click', { source: 'trial_banner', days_left: daysLeft, user_tier: 'basic_trial' })}
          style={{
            background: isLow ? '#ef4444' : '#22c55e', color:'#fff', border:'none',
            borderRadius:'6px', padding:'5px 14px',
            fontSize:'12px', fontWeight:700, cursor:'pointer',
            textDecoration:'none', whiteSpace:'nowrap',
          }}
        >
          {isLow ? 'Đăng ký ngay →' : 'Nâng cấp Basic 199k →'}
        </a>
      </div>
    )
  }

  // ── Render ────────────────────────────────────────────────────────────
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
                  isVip   ? { background:'linear-gradient(135deg,#7c3aed,#a855f7)', boxShadow:'0 0 12px rgba(168,85,247,0.5)' }
                  : isBasic ? { background:'linear-gradient(135deg,#059669,#10b981)', boxShadow:'0 0 8px rgba(16,185,129,0.3)' }
                  : isTrial ? { background:'linear-gradient(135deg,#d97706,#f59e0b)', boxShadow:'0 0 8px rgba(245,158,11,0.3)' }
                  : {}
                }>
                  {user.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="user-info">
                  <div className="user-name">{user.name} <TierBadge /></div>
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
                  onClick={() => handleTabChange('signals')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  </svg>
                  Tín hiệu mua bán
                  <span className="badge">{signals.length}</span>
                </button>

                <button
                  className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
                  onClick={() => handleTabChange('portfolio')}
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
                  onClick={() => handleTabChange('vip')}
                  style={activeTab === 'vip' ? {
                    background: 'linear-gradient(135deg,#7c3aed22,#a855f722)',
                    borderBottom: '2px solid #a855f7', color: '#c084fc',
                  } : { color: '#a855f7' }}
                >
                  💎 VIP Dashboard
                </button>
                <button
                  className={`tab ${activeTab === 'basic' ? 'active' : ''}`}
                  onClick={() => handleTabChange('basic')}
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

          {isFree  && activeTab === 'signals' && <FreeBanner />}
          {isTrial && activeTab === 'signals' && <TrialBanner />}

          {activeTab === 'signals' && (
            <>
              <AIAdvisorChat userId={user.email} userTier={resolvedTier} onOpenIIS={() => setShowIISModal(true)} />
              <SignalHistory />
              <SignalsModule signals={signals} loading={loading} onRefresh={fetchSignals} userTier={resolvedTier} />
            </>
          )}

          {activeTab === 'rescue' && (
            <PortfolioRescue userId={user.email} userTier={resolvedTier} />
          )}

          {activeTab === 'portfolio' && (
            <>
              <AIAdvisorChat userId={user.email} userTier={resolvedTier} onOpenIIS={() => setShowIISModal(true)} />
              <AIPortfolioManager userId={user.email} userTier={resolvedTier} onOpenIIS={() => setShowIISModal(true)} />
            </>
          )}

          {activeTab === 'vip' && isVip && (
            <VIPDashboard user={user} onSwitchBasic={() => handleTabChange('basic')} onOpenIIS={() => setShowIISModal(true)} />
          )}

          {activeTab === 'basic' && isVip && (
            <>
              <SignalHistory />
              <SignalsModule signals={signals} loading={loading} onRefresh={fetchSignals} userTier="basic" />
            </>
          )}
        </div>
      </main>

      {/* IIS Onboarding Modal */}
      {showIISModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: '#0a0f1e', overflowY: 'auto',
          display: 'flex', flexDirection: 'column',
        }}>
          <div style={{
            padding: '12px 20px', borderBottom: '1px solid #1e293b',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: '#0f172a', flexShrink: 0,
          }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#C8780F' }}>
              AI ADVISOR — Investor Intelligence Score
            </span>
            <button
                  className={`tab ${activeTab === 'rescue' ? 'active' : ''}`}
                  onClick={() => setActiveTab('rescue')}
                >
                  🚑 Giải Phóng Danh Mục
                </button>
                 useState, useEffect } from 'react'
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
import AIAdvisorChat from './components/AIAdvisorChat'
import PortfolioRescue from './components/PortfolioRescue'

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

// ── GA4 helper (safe — không crash nếu gtag chưa load) ───────────────────
function track(eventName, params = {}) {
  try {
    if (typeof window.gtag === 'function') {
      window.gtag('event', eventName, params)
    }
  } catch (e) { /* silent */ }
}

// ── Tier helpers ─────────────────────────────────────────────────────────
function resolveUserTier(user) {
  if (!user) return 'free'
  if (user.isVip) return 'vip'
  const tier = user.tier || 'free'
  if (tier === 'basic_trial') {
    const end = user.trialEndDate ? new Date(user.trialEndDate) : null
    if (!end || new Date() > end) return 'free'
    return 'basic_trial'
  }
  return tier
}

function trialDaysLeft(user) {
  if (!user || user.tier !== 'basic_trial') return -1
  const end = user.trialEndDate ? new Date(user.trialEndDate) : null
  if (!end) return -1
  return Math.max(0, Math.ceil((end - new Date()) / (1000 * 60 * 60 * 24)))
}

function App() {
  const isAdmin = window.location.pathname === '/admin'
  const isBlog  = window.location.pathname.startsWith('/blog')

  const [user, setUser]                 = useState(null)
  const [resolvedTier, setResolvedTier] = useState('free')
  const [activeTab, setActiveTab]       = useState('signals')
  const [showIISModal, setShowIISModal] = useState(false)
  const [signals, setSignals]           = useState([])
  const [loading, setLoading]           = useState(true)
  const [lastUpdate, setLastUpdate]     = useState(null)

  // ── Load user từ localStorage ─────────────────────────────────────────
  useEffect(() => {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        if (!parsed.tier && !parsed.isVip) parsed.tier = 'free'
        const tier = resolveUserTier(parsed)
        if (parsed.tier === 'basic_trial' && tier === 'free') {
          parsed.tier = 'free'
          localStorage.setItem('user', JSON.stringify(parsed))
        }
        setUser(parsed)
        setResolvedTier(tier)

        // ✅ GA4: User quay lại (session restore từ localStorage)
        track('session_restore', { user_tier: tier })

      } catch (e) {
        localStorage.removeItem('user')
      }
    }
  }, [])

  // ── Fetch signals ─────────────────────────────────────────────────────
  const fetchSignals = async (tier) => {
    const currentTier = tier || resolvedTier
    try {
      setLoading(true)
      const isFullAccess = ['basic_trial', 'basic', 'vip'].includes(currentTier)
      // FIX (2026-07-01): luôn truyền ?delay tường minh (0 hoặc 7).
      // Trước đây full-access gọi /signals KHÔNG kèm param, khiến backend
      // tự ý auto-detect qua JWT token (mà FE không hề gửi) và MẶC ĐỊNH
      // ép delay=7 cho mọi request thiếu token — kể cả VIP đã login.
      // Truyền rõ delay=0 đảm bảo backend luôn nhận đúng ý định real-time.
      const url = isFullAccess ? `${API_URL}/signals?delay=0` : `${API_URL}/signals?delay=7`
      const response = await fetch(url)
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

  // ── Handlers ──────────────────────────────────────────────────────────
  const handleLogin = async (userData) => {
    const tier = resolveUserTier(userData)
    if (!userData.tier && !userData.isVip) {
      userData.tier = 'free'
      localStorage.setItem('user', JSON.stringify(userData))
    }
    setUser(userData)
    setResolvedTier(tier)

    // ✅ GA4: Login event — quan trọng nhất để đo DAU
    track('login', {
      user_tier:  tier,
      is_vip:     !!userData.isVip,
      login_type: 'email',
    })

    if (userData.isVip) {
      setActiveTab('vip')
      try {
        const r = await fetch(`${API_URL}/iis/result/${encodeURIComponent(userData.email)}`)
        const d = await r.json()
        if (!d.has_result) {
          setShowIISModal(true)
          // ✅ GA4: IIS modal hiện ra (chưa làm test)
          track('iis_modal_shown', { user_tier: tier, trigger: 'login_vip' })
        }
      } catch {}
      return
    }

    try {
      const r = await fetch(`${API_URL}/iis/result/${encodeURIComponent(userData.email)}`)
      const d = await r.json()
      if (!d.has_result) {
        setShowIISModal(true)
        // ✅ GA4: IIS modal hiện ra
        track('iis_modal_shown', { user_tier: tier, trigger: 'login_new' })
      } else {
        // ✅ GA4: User đã có IIS score (returning user đã test)
        track('iis_already_done', { user_tier: tier, iis_score: d.total })
      }
    } catch {}
  }

  const handleLogout = () => {
    // ✅ GA4: Logout
    track('logout', { user_tier: resolvedTier })
    localStorage.removeItem('user')
    setUser(null)
    setResolvedTier('free')
    setActiveTab('signals')
  }

  // ── Tab change tracking ───────────────────────────────────────────────
  const handleTabChange = (tab) => {
    setActiveTab(tab)
    // ✅ GA4: Xem tab nào
    track('tab_view', { tab_name: tab, user_tier: resolvedTier })
  }

  // ── Blog ──────────────────────────────────────────────────────────────
  if (isBlog)  return <Blog />
  if (isAdmin) return <VIPAdminPanel />
  if (!user)   return <LandingPage onLogin={handleLogin} />

  const daysLeft    = trialDaysLeft(user)
  const isFree      = resolvedTier === 'free'
  const isTrial     = resolvedTier === 'basic_trial'
  const isBasic     = resolvedTier === 'basic'
  const isVip       = resolvedTier === 'vip'
  const hasFullAccess = isTrial || isBasic || isVip

  // ── Tier badge ────────────────────────────────────────────────────────
  const TierBadge = () => {
    if (isVip)   return <span style={badgeStyle('#7c3aed','#a855f7')}>💎 VIP</span>
    if (isBasic) return <span style={badgeStyle('#059669','#10b981')}>✅ Basic</span>
    if (isTrial) return (
      <span style={badgeStyle('#d97706','#f59e0b')}>🕐 Trial {daysLeft}d còn</span>
    )
    return <span style={badgeStyle('#475569','#64748b')}>Free</span>
  }

  // ── Banners ───────────────────────────────────────────────────────────
  const FreeBanner = () => (
    <div style={{
      background: 'linear-gradient(90deg, #1a1200, #1a0a00)',
      border: '1px solid #f59e0b66', borderRadius: '10px',
      padding: '10px 18px', margin: '12px 0',
      display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', flexWrap: 'wrap',
      gap: '8px', fontSize: '13px',
    }}>
      <div>
        <span style={{color:'#fbbf24', fontWeight:600}}>⏰ Tín hiệu đang hiển thị delay 7 ngày</span>
        <span style={{color:'#94a3b8', marginLeft:'8px'}}>— Nâng lên Basic để xem real-time</span>
      </div>
      <a
        href="https://ai-advisor.vn" target="_blank" rel="noreferrer"
        onClick={() => track('upgrade_click', { source: 'free_banner', user_tier: 'free' })}
        style={{
          background:'#f59e0b', color:'#000', border:'none',
          borderRadius:'6px', padding:'5px 14px',
          fontSize:'12px', fontWeight:700, cursor:'pointer',
          textDecoration:'none', whiteSpace:'nowrap',
        }}
      >
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
        borderRadius: '10px', padding: '10px 18px', margin: '12px 0',
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', flexWrap: 'wrap',
        gap: '8px', fontSize: '13px',
      }}>
        <div>
          <span style={{color: isLow ? '#f87171' : '#4ade80', fontWeight:600}}>
            {isLow ? '⚠️' : '🎁'} Bạn đang dùng thử Basic — còn {daysLeft} ngày
          </span>
          <span style={{color:'#94a3b8', marginLeft:'8px'}}>
            {isLow ? '— Đăng ký ngay để không gián đoạn!' : '— Tín hiệu real-time, đầy đủ tính năng'}
          </span>
        </div>
        <a
          href="mailto:aiadvisorhotline@gmail.com"
          onClick={() => track('upgrade_click', { source: 'trial_banner', days_left: daysLeft, user_tier: 'basic_trial' })}
          style={{
            background: isLow ? '#ef4444' : '#22c55e', color:'#fff', border:'none',
            borderRadius:'6px', padding:'5px 14px',
            fontSize:'12px', fontWeight:700, cursor:'pointer',
            textDecoration:'none', whiteSpace:'nowrap',
          }}
        >
          {isLow ? 'Đăng ký ngay →' : 'Nâng cấp Basic 199k →'}
        </a>
      </div>
    )
  }

  // ── Render ────────────────────────────────────────────────────────────
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
                  isVip   ? { background:'linear-gradient(135deg,#7c3aed,#a855f7)', boxShadow:'0 0 12px rgba(168,85,247,0.5)' }
                  : isBasic ? { background:'linear-gradient(135deg,#059669,#10b981)', boxShadow:'0 0 8px rgba(16,185,129,0.3)' }
                  : isTrial ? { background:'linear-gradient(135deg,#d97706,#f59e0b)', boxShadow:'0 0 8px rgba(245,158,11,0.3)' }
                  : {}
                }>
                  {user.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="user-info">
                  <div className="user-name">{user.name} <TierBadge /></div>
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
                  onClick={() => handleTabChange('signals')}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  </svg>
                  Tín hiệu mua bán
                  <span className="badge">{signals.length}</span>
                </button>

                <button
                  className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
                  onClick={() => handleTabChange('portfolio')}
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
                  onClick={() => handleTabChange('vip')}
                  style={activeTab === 'vip' ? {
                    background: 'linear-gradient(135deg,#7c3aed22,#a855f722)',
                    borderBottom: '2px solid #a855f7', color: '#c084fc',
                  } : { color: '#a855f7' }}
                >
                  💎 VIP Dashboard
                </button>
                <button
                  className={`tab ${activeTab === 'basic' ? 'active' : ''}`}
                  onClick={() => handleTabChange('basic')}
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

          {isFree  && activeTab === 'signals' && <FreeBanner />}
          {isTrial && activeTab === 'signals' && <TrialBanner />}

          {activeTab === 'signals' && (
            <>
              <AIAdvisorChat userId={user.email} userTier={resolvedTier} onOpenIIS={() => setShowIISModal(true)} />
              <SignalHistory />
              <SignalsModule signals={signals} loading={loading} onRefresh={fetchSignals} userTier={resolvedTier} />
            </>
          )}

          {activeTab === 'portfolio' && (
            <>
              <AIAdvisorChat userId={user.email} userTier={resolvedTier} onOpenIIS={() => setShowIISModal(true)} />
              <AIPortfolioManager userId={user.email} userTier={resolvedTier} onOpenIIS={() => setShowIISModal(true)} />
            </>
          )}

          {activeTab === 'vip' && isVip && (
            <VIPDashboard user={user} onSwitchBasic={() => handleTabChange('basic')} onOpenIIS={() => setShowIISModal(true)} />
          )}

          {activeTab === 'basic' && isVip && (
            <>
              <SignalHistory />
              <SignalsModule signals={signals} loading={loading} onRefresh={fetchSignals} userTier="basic" />
            </>
          )}
        </div>
      </main>

      {/* IIS Onboarding Modal */}
      {showIISModal && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: '#0a0f1e', overflowY: 'auto',
          display: 'flex', flexDirection: 'column',
        }}>
          <div style={{
            padding: '12px 20px', borderBottom: '1px solid #1e293b',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: '#0f172a', flexShrink: 0,
          }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#C8780F' }}>
              AI ADVISOR — Investor Intelligence Score
            </span>
            <button
              onClick={() => {
                setShowIISModal(false)
                // ✅ GA4: User bỏ qua IIS modal — friction point quan trọng
                track('iis_modal_skipped', { user_tier: resolvedTier })
              }}
              style={{
                background: 'transparent', border: '1px solid #334155',
                color: '#64748b', borderRadius: '6px',
                padding: '4px 10px', fontSize: '12px', cursor: 'pointer',
              }}
            >
              Bỏ qua ✕
            </button>
          </div>
          <div style={{ flex: 1 }}>
            <IISTest
              userId={user?.email}
              onComplete={(result) => {
                setShowIISModal(false)
                setActiveTab('portfolio')
                // ✅ GA4: IIS hoàn thành — event quan trọng nhất để đo activation
                track('iis_test_completed', {
                  iis_score:  result?.total,
                  iis_level:  result?.level,
                  iis_method: result?.method,
                  user_tier:  resolvedTier,
                })
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

function badgeStyle(from, to) {
  return {
    marginLeft: '6px', fontSize: '10px', fontWeight: '700',
    background: `linear-gradient(135deg,${from},${to})`,
    color: '#fff', padding: '2px 7px', borderRadius: '4px',
    verticalAlign: 'middle', whiteSpace: 'nowrap',
  }
}

export default App
