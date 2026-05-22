import { useState, useEffect } from 'react'
import './App.css'
import LandingPage from './components/LandingPage'
import SignalsModule from './components/SignalsModule'
import AIPortfolioManager from './components/AIPortfolioManager'
import SignalHistory from './components/SignalHistory'
import VIPDashboard from './components/VIPDashboard'
import VIPAdminPanel from './components/VIPAdminPanel'

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

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

  const [user, setUser]             = useState(null)
  const [resolvedTier, setResolvedTier] = useState('free')
  const [activeTab, setActiveTab]   = useState('signals')
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

  // ── Fetch signals: truyền ?delay=3 cho Free users ─────────────────────
  const fetchSignals = async (tier) => {
    const currentTier = tier || resolvedTier
    try {
      setLoading(true)
      const isFullAccess = ['basic_trial', 'basic', 'vip'].includes(currentTier)
      const url = isFullAccess ? `${API_URL}/signals` : `${API_URL}/signals?delay=3`
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

  // ── Handlers ───────────────────────────────────────────────────────────
  const handleLogin = (userData) => {
    const tier = resolveUserTier(userData)
    // Migrate khách cũ nếu chưa có tier
    if (!userData.tier && !userData.isVip) {
      userData.tier = 'free'
      localStorage.setItem('user', JSON.stringify(userData))
    }
    setUser(userData)
    setResolvedTier(tier)
    if (userData.isVip) setActiveTab('vip')
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    setUser(null)
    setResolvedTier('free')
    setActiveTab('signals')
  }

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
        <span style={{color:'#fbbf24', fontWeight:600}}>⏰ Tín hiệu đang hiển thị delay 3 ngày</span>
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
            <AIPortfolioManager userId={user.email} />
          )}

          {activeTab === 'vip' && isVip && (
            <VIPDashboard user={user} onSwitchBasic={() => setActiveTab('basic')} />
          )}

          {activeTab === 'basic' && isVip && (
            <>
              <SignalHistory />
              <SignalsModule signals={signals} loading={loading} onRefresh={fetchSignals} />
            </>
          )}
        </div>
      </main>

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
