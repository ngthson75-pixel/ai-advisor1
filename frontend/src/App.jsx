import { useState, useEffect } from 'react'
import './App.css'
import LandingPage from './components/LandingPage'
import SignalsModule from './components/SignalsModule'
import AIPortfolioManager from './components/AIPortfolioManager'
import SignalHistory from './components/SignalHistory'
import PWANotificationManager from './components/PWANotificationManager'
import VIPAdminPanel from './components/VIPAdminPanel'
import VIPDashboard from './components/VIPDashboard'
import { initGA, trackLogin, trackTabView } from './analytics'

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

function App() {
  const [user, setUser] = useState(null)
  const [activeTab, setActiveTab] = useState('signals')
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  // VIP Auth state (JWT — song song với free user flow, không đụng nhau)
  const [vipToken, setVipToken] = useState(() => localStorage.getItem('vip_token') || '')
  const [vipUser, setVipUser]   = useState(null)

  // Restore VIP session khi app load
  useEffect(() => {
    const savedToken = localStorage.getItem('vip_token')
    if (!savedToken) return
    const base = API_URL.replace('/api', '')
    fetch(`${base}/api/auth/me`, {
      headers: { Authorization: `Bearer ${savedToken}` }
    })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          setVipUser(data.user)
          setVipToken(savedToken)
          // Nếu là VIP user → tự động chuyển sang tab vip
          const tier = data.user?.tier || ''
          if (tier === 'vip' || tier === 'pro') {
            setActiveTab('vip')
          }
        } else {
          localStorage.removeItem('vip_token')
          setVipToken('')
        }
      })
      .catch(() => {/* server unreachable — giữ token, thử lại sau */})
  }, [])

  // Check for existing user on mount + init GA4
  useEffect(() => {
    initGA()
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser))
      } catch (e) {
        console.error('Error parsing stored user:', e)
        localStorage.removeItem('user')
      }
    }
  }, [])

  // Fetch signals from API
  const fetchSignals = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/signals`)
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
      fetchSignals()
      const interval = setInterval(fetchSignals, 5 * 60 * 1000)
      return () => clearInterval(interval)
    }
  }, [user])

  const handleLogin = (userData) => {
    setUser(userData)
    trackLogin(userData.id || userData.email, userData.name)
  }

  const handleLogout = () => {
    localStorage.removeItem('user')
    localStorage.removeItem('vip_token')
    setUser(null)
    setVipUser(null)
    setVipToken('')
    setActiveTab('signals')
  }

  // Helper: kiểm tra user có phải VIP/Pro không
  const isVipUser = vipUser && (vipUser.tier === 'vip' || vipUser.tier === 'pro')

  // Show landing page if not logged in
  if (!user) {
    return <LandingPage onLogin={handleLogin} />
  }

  // Nếu đang ở tab VIP → render toàn trang VIPDashboard (full screen, không có header/nav chung)
  if (activeTab === 'vip' && isVipUser) {
    return (
      <>
        {/* Nút quay lại để thoát khỏi VIP dashboard */}
        <div style={{
          position: 'fixed',
          top: '16px',
          left: '16px',
          zIndex: 9999,
        }}>
          <button
            onClick={() => setActiveTab('signals')}
            style={{
              background: 'rgba(45,10,94,0.9)',
              border: '1px solid rgba(139,92,246,0.4)',
              color: '#c4b5fd',
              padding: '8px 14px',
              borderRadius: '10px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backdropFilter: 'blur(12px)',
            }}
          >
            ← Quay lại
          </button>
        </div>
        <VIPDashboard user={vipUser} token={vipToken} />
        <PWANotificationManager
          userId={vipUser?.id}
          token={vipToken}
          isPushEnabled={vipUser?.is_push_enabled ?? true}
        />
      </>
    )
  }

  // Show main app if logged in
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
                <div className="user-avatar">
                  {user.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="user-info">
                  <div className="user-name">{user.name}</div>
                  <button onClick={handleLogout} className="logout-btn">
                    Đăng xuất
                  </button>
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
            <button
              className={`tab ${activeTab === 'signals' ? 'active' : ''}`}
              onClick={() => { setActiveTab('signals'); trackTabView('signals') }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              </svg>
              Tín hiệu mua bán
              <span className="badge">{signals.length}</span>
            </button>

            <button
              className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
              onClick={() => { setActiveTab('portfolio'); trackTabView('portfolio') }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              </svg>
              Quản trị đầu tư bằng AI
            </button>

            {/* Tab VIP — chỉ hiện khi user có tier vip/pro */}
            {isVipUser && (
              <button
                className={`tab ${activeTab === 'vip' ? 'active' : ''}`}
                onClick={() => { setActiveTab('vip'); trackTabView('vip') }}
                style={{
                  background: activeTab === 'vip'
                    ? 'linear-gradient(135deg, rgba(124,58,237,0.3), rgba(139,92,246,0.2))'
                    : 'transparent',
                  borderColor: activeTab === 'vip' ? '#8b5cf6' : 'transparent',
                  color: activeTab === 'vip' ? '#c4b5fd' : '#a78bfa',
                  position: 'relative',
                }}
              >
                <span>👑</span>
                VIP Dashboard
                {/* Glow dot để báo có tính năng mới */}
                <span style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: '#8b5cf6',
                  display: 'inline-block',
                  marginLeft: 4,
                  boxShadow: '0 0 6px #8b5cf6',
                  animation: 'pulse 2s infinite',
                }} />
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="container">
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

          {activeTab === 'portfolio' && <AIPortfolioManager userId={user.email} />}
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>© 2025 AI Advisor. Professional Stock Trading Signals Platform.</p>
          <p className="disclaimer">
            Investment involves risks. Please do your own research before trading.
          </p>
        </div>
      </footer>

      {/* PWA Push Notification — hiện với VIP users đã login */}
      <PWANotificationManager
        userId={vipUser?.id || user?.email}
        token={vipToken}
        isPushEnabled={vipUser?.is_push_enabled ?? true}
      />
    </div>
  )
}

// Wrapper: route /admin → VIPAdminPanel, còn lại → App bình thường
function AppWithAdmin() {
  if (window.location.pathname === '/admin') {
    return <VIPAdminPanel />
  }
  return <App />
}

export default AppWithAdmin
