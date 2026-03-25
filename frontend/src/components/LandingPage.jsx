import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10000/api';

export default function LandingPage({ onLogin }) {
  const [showAuth, setShowAuth] = useState(false)
  const [showTerms, setShowTerms] = useState(false)
  const [showAbout, setShowAbout] = useState(false)
  const [showCampaign, setShowCampaign] = useState(false)
  const [showChangePwd, setShowChangePwd] = useState(false)
  const [loginToken, setLoginToken] = useState('')
  const [loginUserData, setLoginUserData] = useState(null)
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  })

  // Fetch recommendations from API + historical data
  const [recommendations, setRecommendations] = useState([])
  const [closedSignals, setClosedSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [marketRisk, setMarketRisk] = useState(null)

  // Historical signals from 06/01/2026
  const historicalSignals = [
    {
      id: 'hist-1',
      ticker: 'VNM',
      entryPrice: 60700,
      stopLoss: 57665,
      takeProfit: 65556,
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026',
      status: 'active',
      action: null
    },
    {
      id: 'hist-2',
      ticker: 'BID',
      entryPrice: 38750,
      stopLoss: 36812,
      takeProfit: 41850,
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026',
      status: 'active',
      action: null
    },
    {
      id: 'hist-3',
      ticker: 'CTG',
      entryPrice: 36120,
      stopLoss: 34314,
      takeProfit: 39010,
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026',
      status: 'active',
      action: null
    },
    {
      id: 'hist-4',
      ticker: 'POW',
      entryPrice: 12750,
      stopLoss: 12112,
      takeProfit: 13770,
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026',
      status: 'active',
      action: null
    },
    {
      id: 'hist-5',
      ticker: 'SAB',
      entryPrice: 45700,
      stopLoss: 43415,
      takeProfit: 49356,
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026',
      status: 'active',
      action: null
    },
    {
      id: 'hist-6',
      ticker: 'HNG',
      entryPrice: 6300,
      stopLoss: 5985,
      takeProfit: 6804,
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026',
      status: 'active',
      action: null
    }
  ]

  useEffect(() => {
    fetchRecommendations()
  }, [])

  // Fetch market risk data
  useEffect(() => {
    fetch(`${API_BASE}/market-risk`)
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data) {
          setMarketRisk(data.data)
        }
      })
      .catch(err => console.error('Market risk fetch error:', err))
  }, [])

  // Format date from various formats to DD/MM/YYYY
  const formatDate = (dateString) => {
    if (!dateString) return ''
    
    // If already in DD/MM/YYYY format, return as-is
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateString)) {
      return dateString
    }
    
    // Parse ISO format (YYYY-MM-DD or ISO datetime)
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      
      const day = String(date.getDate()).padStart(2, '0')
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const year = date.getFullYear()
      
      return `${day}/${month}/${year}`
    } catch (e) {
      return dateString
    }
  }

  // Simulate sell signal logic (in real app, this would be backend)
  const evaluateSellSignal = (signal, currentPrice, ma20) => {
    // This is a simulation - in production, fetch real prices and MA20
    
    // If price reached TP → Sell 1/2
    if (currentPrice >= signal.takeProfit && signal.status === 'active') {
      return {
        status: 'half_sold',
        action: 'BÁN 1/2',
        reason: 'Đạt Take Profit'
      }
    }
    
    // If already sold 1/2 and price cuts below MA20 → Sell remaining 1/2
    if (signal.status === 'half_sold' && currentPrice < ma20) {
      return {
        status: 'fully_sold',
        action: 'BÁN NỐT 1/2',
        reason: 'Cắt xuống MA20'
      }
    }
    
    // Otherwise hold
    if (signal.status === 'half_sold') {
      return {
        status: 'half_sold',
        action: 'NẮM GIỮ',
        reason: 'Trên MA20'
      }
    }
    
    return {
      status: 'active',
      action: null,
      reason: null
    }
  }

  const fetchRecommendations = async () => {
    try {
      const response = await fetch(`${API_BASE}/signals`)
      const data = await response.json()

      if (data.success && data.signals) {
        const allBuySignals = data.signals.filter(s => s.action === 'BUY' || !s.action)

        const activeApiSignals = allBuySignals
          .filter(s => s.status === 'open' || s.status === 'partial' || !s.status)
          .slice(0, 10)
          .map((signal, index) => ({
            id: signal.id || `api-${index + 1}`,
            ticker: signal.ticker || signal.code,
            entryPrice: signal.entry_price,
            stopLoss: signal.stop_loss,
            takeProfit: signal.take_profit,
            score: signal.strength || 75,
            type: signal.stock_type || 'Blue Chip',
            date: formatDate(signal.date || signal.created_at),
            status: 'active',
            action: null
          }))

        const closedApiSignals = allBuySignals
          .filter(s => s.status === 'closed')
          .map(signal => ({
            id: signal.id,
            ticker: signal.ticker || signal.code,
            entryPrice: signal.entry_price,
            exitPrice: signal.exit_price || null,
            exitReason: signal.exit_reason || null,
            exitDate: signal.exit_date || null,
            score: signal.strength || 75,
            type: signal.stock_type || 'Blue Chip',
            date: formatDate(signal.date || signal.created_at),
            status: 'closed'
          }))

        const closedApiKeys = new Set(closedApiSignals.map(s => `${s.ticker}_${s.date}`))
        const filteredHistorical = historicalSignals.filter(
          s => !closedApiKeys.has(`${s.ticker}_${s.date}`)
        )
        const mergedClosed = [
          ...closedApiSignals,
          ...filteredHistorical.map(s => ({
            id: s.id, ticker: s.ticker, entryPrice: s.entryPrice,
            exitPrice: null, exitReason: null, exitDate: null,
            score: s.score, type: s.type, date: s.date, status: 'closed'
          }))
        ].sort((a, b) => {
          const da = a.date ? a.date.split('/').reverse().join('') : ''
          const db = b.date ? b.date.split('/').reverse().join('') : ''
          return db.localeCompare(da)
        })

        setRecommendations(activeApiSignals)
        setClosedSignals(mergedClosed)
      } else {
        setRecommendations([])
        setClosedSignals(historicalSignals.map(s => ({
          id: s.id, ticker: s.ticker, entryPrice: s.entryPrice,
          exitPrice: null, exitReason: null, exitDate: null,
          score: s.score, type: s.type, date: s.date, status: 'closed'
        })))
      }
    } catch (error) {
      console.error('Error fetching signals:', error)
      setRecommendations([])
      setClosedSignals(historicalSignals.map(s => ({
        id: s.id, ticker: s.ticker, entryPrice: s.entryPrice,
        exitPrice: null, exitReason: null, exitDate: null,
        score: s.score, type: s.type, date: s.date, status: 'closed'
      })))
    } finally {
      setLoading(false)
    }
  }

    const stats = {
    totalSignals: 127,
    successRate: 78.5,
    avgReturn: 6.8,
    failureRate: 21.5
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const API_URL = window.location.hostname.includes('staging')
      ? 'https://ai-advisor1-staging.onrender.com'
      : 'https://ai-advisor1-backend.onrender.com'

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email, password: formData.password }),
      })
      const data = await res.json()

      if (!res.ok || !data.success) {
        alert(data.error || 'Email hoặc mật khẩu không đúng')
        return
      }

      const userData = {
        email: data.user.email,
        name: data.user.full_name || data.user.email.split('@')[0],
        tier: data.user.tier,
        token: data.token,
        loginTime: new Date().toISOString()
      }

      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('authToken', data.token)

      if (data.is_first_login) {
        // Lần đầu đăng nhập → bắt đổi mật khẩu
        setLoginToken(data.token)
        setLoginUserData(userData)
        setShowAuth(false)
        setShowChangePwd(true)
      } else {
        onLogin(userData)
      }
    } catch (err) {
      alert('Không thể kết nối server. Vui lòng thử lại.')
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN').format(value)
  }

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <div className="hero-text">
              <h1 className="hero-title">
                Đầu tư thông minh với
                <span className="gradient-text" style={{display:"inline-flex",alignItems:"center",gap:"10px",verticalAlign:"middle"}}>
                  <svg width="56" height="56" viewBox="0 0 40 40" fill="none" style={{display:"inline-block",verticalAlign:"middle",marginLeft:"4px",flexShrink:0}}>
                    <defs>
                      <linearGradient id="heroLogoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style={{stopColor:'#3b82f6',stopOpacity:1}}/>
                        <stop offset="100%" style={{stopColor:'#8b5cf6',stopOpacity:1}}/>
                      </linearGradient>
                    </defs>
                    <path d="M20 8L32 14V26L20 32L8 26V14L20 8Z" stroke="url(#heroLogoGradient)" strokeWidth="2" fill="none"/>
                    <path d="M20 8V20M20 20L32 26M20 20L8 26" stroke="url(#heroLogoGradient)" strokeWidth="2"/>
                    <circle cx="20" cy="20" r="3" fill="url(#heroLogoGradient)"/>
                  </svg>
                  AI Advisor
                </span>
              </h1>
              <p className="hero-subtitle">
                Tín hiệu mua bán chính xác, quản trị danh mục tự động, và tư vấn AI 24/7 - 
                Nền tảng đầu tư chứng khoán thế hệ mới
              </p>
              
              <div className="hero-stats">
                <div className="stat-item">
                  <div className="stat-number">{stats.totalSignals}+</div>
                  <div className="stat-label">Tín hiệu phát sinh</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{stats.successRate}%</div>
                  <div className="stat-label">Tỷ lệ thành công</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{stats.avgReturn}%</div>
                  <div className="stat-label">Lợi nhuận TB</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number" style={{color: '#ef4444'}}>{stats.failureRate}%</div>		
                  <div className="stat-label">Tỷ lệ không thành công</div>
                </div>
              </div>

              <div className="hero-cta">
                <button className="btn-primary-large" onClick={() => setShowCampaign(true)}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                    <polyline points="10 17 15 12 10 7"/>
                    <line x1="15" y1="12" x2="3" y2="12"/>
                  </svg>
                  Đăng ký Beta - Miễn phí
                </button>
                <button className="btn-secondary-large" onClick={() => { setIsLogin(true); setShowAuth(true); }}>
                  Đăng nhập
                </button>
              </div>
            </div>

            <div className="hero-image">
              <div className="dashboard-preview">
                <div className="preview-header">
                  <div className="preview-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <div className="preview-title">AI Advisor Market Dashboard</div>
                </div>

                {/* Market Risk Widget */}
                {marketRisk ? (
                  <div style={{
                    padding: '20px',
                    background: 'linear-gradient(135deg, #0B0F1A 0%, #1a1f3a 100%)',
                    borderRadius: '0 0 12px 12px',
                  }}>
                    {/* Market Mode Header */}
                    <div style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      marginBottom: '16px', flexWrap: 'wrap', gap: '12px',
                    }}>
                      <div>
                        <div style={{
                          fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase',
                          letterSpacing: '1px', marginBottom: '4px',
                        }}>Market Mode</div>
                        <div style={{
                          fontSize: '22px', fontWeight: '800',
                          color: marketRisk.market_mode === 'BULL' ? '#00E676'
                               : marketRisk.market_mode === 'BEAR' ? '#FF1744' : '#FFD600',
                        }}>
                          {marketRisk.market_mode === 'BULL' ? '🟢' : marketRisk.market_mode === 'BEAR' ? '🔴' : '🟡'}{' '}
                          {marketRisk.mode_label}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '12px', color: '#94a3b8' }}>Risk Score</div>
                        <div style={{
                          fontSize: '28px', fontWeight: '800',
                          fontFamily: "'JetBrains Mono', monospace",
                          color: marketRisk.risk_score <= 35 ? '#00E676'
                               : marketRisk.risk_score <= 65 ? '#FFD600' : '#FF1744',
                        }}>{marketRisk.risk_score}<span style={{ fontSize: '14px', color: '#64748b' }}>/100</span></div>
                      </div>
                    </div>

                    {/* Description */}
                    <div style={{
                      fontSize: '13px', color: '#94a3b8', marginBottom: '16px',
                      padding: '10px 14px', background: 'rgba(255,255,255,0.04)',
                      borderRadius: '8px', borderLeft: '3px solid',
                      borderLeftColor: marketRisk.market_mode === 'BULL' ? '#00E676'
                                     : marketRisk.market_mode === 'BEAR' ? '#FF1744' : '#FFD600',
                    }}>
                      {marketRisk.description}
                    </div>

                    {/* Allocation Bar */}
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{
                        display: 'flex', justifyContent: 'space-between',
                        fontSize: '12px', color: '#94a3b8', marginBottom: '6px',
                      }}>
                        <span>Tỷ trọng CP: <strong style={{ color: '#e2e8f0' }}>{marketRisk.allocation}%</strong></span>
                        <span>Tiền mặt: <strong style={{ color: '#e2e8f0' }}>{100 - marketRisk.allocation}%</strong></span>
                      </div>
                      <div style={{
                        height: '8px', background: 'rgba(255,255,255,0.1)',
                        borderRadius: '4px', overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%', borderRadius: '4px',
                          width: `${marketRisk.allocation}%`,
                          background: marketRisk.market_mode === 'BULL'
                            ? 'linear-gradient(90deg, #00E676, #00C853)'
                            : marketRisk.market_mode === 'BEAR'
                            ? 'linear-gradient(90deg, #FF1744, #D50000)'
                            : 'linear-gradient(90deg, #FFD600, #FFC107)',
                          transition: 'width 1s ease',
                        }}></div>
                      </div>
                    </div>

                    {/* Factors - chỉ hiện những yếu tố có dữ liệu */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {(marketRisk.factors || [])
                        .filter(factor => !factor.isRef && !factor.value?.includes('Chưa có'))
                        .map((factor, i) => (
                        <div key={i} style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          padding: '8px 12px', background: 'rgba(255,255,255,0.03)',
                          borderRadius: '6px', fontSize: '13px',
                        }}>
                          <span style={{ color: '#94a3b8' }}>{factor.label}</span>
                          <span style={{
                            color: factor.positive ? '#00E676' : '#FF6B6B',
                            fontWeight: '600',
                          }}>
                            {factor.positive ? '▲ ' : '▼ '}
                            {factor.value}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Timestamp */}
                    <div style={{
                      marginTop: '12px', fontSize: '11px', color: '#475569', textAlign: 'right',
                    }}>
                      Cập nhật: {marketRisk.analyzed_at ? new Date(marketRisk.analyzed_at).toLocaleString('vi-VN') : 'N/A'}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: '40px 20px', textAlign: 'center',
                    background: 'linear-gradient(135deg, #0B0F1A 0%, #1a1f3a 100%)',
                    borderRadius: '0 0 12px 12px',
                  }}>
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>📊</div>
                    <div style={{ color: '#64748b', fontSize: '14px' }}>Đang tải phân tích thị trường...</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="container">
          <div className="section-header">
            <h2>Tính năng nổi bật</h2>
            <p>Công nghệ AI tiên tiến giúp tối ưu hóa quyết định đầu tư</p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <polyline points="19 12 12 19 5 12"/>
                </svg>
              </div>
              <h3>Tín hiệu mua bán AI</h3>
              <p>Phân tích 343 mã chứng khoán 24/7, tạo tín hiệu chính xác với tỷ lệ thành công 78.5%</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                </svg>
              </div>
              <h3>Quản trị danh mục thông minh</h3>
              <p>Theo dõi hiệu suất, phân bổ tài sản tối ưu, và nhận cảnh báo rủi ro kịp thời</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <h3>Tư vấn AI 24/7</h3>
              <p>Trợ lý AI cá nhân giúp kiểm soát cảm xúc, duy trì kỷ luật và ra quyết định sáng suốt</p>
            </div>
          </div>
        </div>
      </section>

      {/* Top 6 Best Signals Section */}
      <section style={{ padding: '60px 0', background: 'linear-gradient(180deg, #0B0F1A 0%, #0f172a 100%)' }}>
        <div className="container">
          <div className="section-header">
            <h2>Top tín hiệu nổi bật</h2>
            <p>Những tín hiệu sinh lời cao nhất từ hệ thống AI Advisor</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginTop: '32px' }}>
            {[
              { ticker: 'BID',  type: 'Blue Chip', entry: 38750, exit: 52700, pl: 35.8, date: '06/01/2026', days: 9  },
              { ticker: 'PC1',  type: 'Mid Cap',   entry: 24200, exit: 30200, pl: 24.8, date: '30/01/2026', days: 32 },
              { ticker: 'VNM',  type: 'Blue Chip', entry: 60700, exit: 73300, pl: 20.8, date: '06/01/2026', days: 14 },
              { ticker: 'SAB',  type: 'Blue Chip', entry: 45700, exit: 54800, pl: 19.9, date: '06/01/2026', days: 9  },
              { ticker: 'POW',  type: 'Blue Chip', entry: 12800, exit: 15000, pl: 17.2, date: '06/01/2026', days: 7  },
              { ticker: 'PVB',  type: 'Mid Cap',   entry: 35100, exit: 41300, pl: 17.7, date: '25/02/2026', days: 6  },
            ].map((s, i) => (
              <div key={i} style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid #334155', borderRadius: '14px', padding: '20px', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: 'linear-gradient(90deg, #10b981, #059669)' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                  <div>
                    <div style={{ fontSize: '22px', fontWeight: '700', color: '#3b82f6', letterSpacing: '1px' }}>{s.ticker}</div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{s.type} · {s.date}</div>
                  </div>
                  <div style={{ background: 'linear-gradient(135deg, #10b981, #059669)', borderRadius: '20px', padding: '4px 12px', fontSize: '16px', fontWeight: '700', color: 'white' }}>
                    +{s.pl}%
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                  <div style={{ background: '#0f172a', borderRadius: '8px', padding: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '2px' }}>Giá vào</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#e2e8f0' }}>{s.entry.toLocaleString('vi-VN')}</div>
                  </div>
                  <div style={{ background: '#0f172a', borderRadius: '8px', padding: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', marginBottom: '2px' }}>Giá ra</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#10b981' }}>{s.exit.toLocaleString('vi-VN')}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: '#64748b' }}>Nắm giữ {s.days} ngày</span>
                  <span style={{ fontSize: '10px', fontWeight: '600', padding: '2px 8px', borderRadius: '10px', background: '#dcfce7', color: '#166534' }}>Chốt lời TP</span>
                </div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: '28px' }}>
            <button className="btn-secondary-large" onClick={() => document.getElementById('showcase').scrollIntoView({ behavior: 'smooth' })}>
              Xem lịch sử đầy đủ ↓
            </button>
          </div>
        </div>
      </section>

      {/* Recommendations Table */}
      <section className="showcase" id="showcase">
        <div className="container">
          <div className="section-header">
            <h2>Lịch sử khuyến nghị</h2>
            <p>Các tín hiệu BUY đã đóng vị thế — dữ liệu minh bạch, cập nhật liên tục</p>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <div style={{ fontSize: '16px' }}>⏳ Đang tải tín hiệu...</div>
            </div>
          ) : closedSignals.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
              <div style={{ fontSize: '18px', marginBottom: '10px' }}>Chưa có lịch sử</div>
              <div style={{ fontSize: '14px' }}>Hệ thống sẽ tự động cập nhật khi có tín hiệu đóng vị thế</div>
            </div>
          ) : (
            <>
              {/* Mobile Cards */}
              <div className="mobile-cards">
                {closedSignals.slice(0, 10).map((signal, idx) => {
                  const entryPrice = signal.entryPrice || 0
                  const exitPrice = signal.exitPrice || 0
                  const plPct = exitPrice > 0 && entryPrice > 0 ? ((exitPrice - entryPrice) / entryPrice * 100) : null
                  const plColor = plPct === null ? '#94a3b8' : plPct >= 0 ? '#10b981' : '#ef4444'
                  const borderColor = plPct === null ? '#334155' : plPct >= 0 ? '#10b981' : '#ef4444'
                  const exitReasonDisplay = (() => {
                    const r = signal.exitReason
                    if (!r) return { text: 'Thủ công', icon: '⚪' }
                    if (r === 'STOP_LOSS') return { text: 'Cắt lỗ (SL)', icon: '🔴' }
                    if (r === 'TAKE_PROFIT') return { text: 'Chốt lời (TP)', icon: '🟢' }
                    if (r === 'MA20_BREAK') return { text: 'MA20 Cross', icon: '🟠' }
                    if (r === 'MA20_CONSECUTIVE') return { text: 'MA20 (2 ngày)', icon: '🟠' }
                    if (r === 'MA20_HIGH_VOLUME') return { text: 'MA20 (Vol)', icon: '🟠' }
                    return { text: 'Thủ công', icon: '⚪' }
                  })()
                  return (
                    <div key={signal.id || idx} style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid #334155', borderRadius: '14px', padding: '16px', marginBottom: '12px', borderLeft: `4px solid ${borderColor}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <strong style={{ color: '#3b82f6', fontSize: '22px', letterSpacing: '1px' }}>{signal.ticker}</strong>
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                          {signal.exitReason && (<span style={{ padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: '600', background: '#1e293b', color: '#94a3b8', border: '1px solid #334155' }}>{exitReasonDisplay.icon} {exitReasonDisplay.text}</span>)}
                          <span style={{ padding: '4px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', background: signal.type === 'Blue Chip' ? '#1d4ed8' : signal.type === 'Mid Cap' ? '#6d28d9' : '#374151', color: 'white' }}>{signal.type || 'N/A'}</span>
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                        <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                          <div style={{ color: '#94a3b8', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Giá vào</div>
                          <div style={{ color: '#e2e8f0', fontWeight: '700', fontSize: '13px' }}>{entryPrice > 0 ? formatCurrency(entryPrice) : '-'}</div>
                        </div>
                        <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                          <div style={{ color: '#94a3b8', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>Giá ra</div>
                          <div style={{ color: plColor, fontWeight: '700', fontSize: '13px' }}>{exitPrice > 0 ? formatCurrency(exitPrice) : '-'}</div>
                        </div>
                        <div style={{ background: '#0f172a', borderRadius: '10px', padding: '10px', textAlign: 'center' }}>
                          <div style={{ color: '#94a3b8', fontSize: '10px', textTransform: 'uppercase', marginBottom: '4px' }}>P/L</div>
                          <div style={{ color: plColor, fontWeight: '700', fontSize: '14px' }}>{plPct !== null ? `${plPct >= 0 ? '+' : ''}${plPct.toFixed(1)}%` : '-'}</div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                        <span style={{ color: '#64748b', fontSize: '11px', padding: '3px 8px', background: '#0f172a', borderRadius: '6px' }}>📅 Vào: {signal.date || 'N/A'}</span>
                        <span style={{ color: '#64748b', fontSize: '11px', padding: '3px 8px', background: '#0f172a', borderRadius: '6px' }}>📅 Ra: {signal.exitDate ? formatDate(signal.exitDate) : 'N/A'}</span>
                        <span style={{ padding: '3px 8px', background: '#1e40af', color: 'white', borderRadius: '6px', fontSize: '11px', fontWeight: '600' }}>Score: {signal.score}</span>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Desktop Table */}
              <div className="signals-table-container desktop-table">
                <table className="signals-table">
                  <thead>
                    <tr>
                      <th>MÃ CK</th>
                      <th>GIÁ VÀO</th>
                      <th>GIÁ RA</th>
                      <th>P/L</th>
                      <th>LÝ DO</th>
                      <th>SCORE</th>
                      <th>LOẠI</th>
                      <th>NGÀY VÀO</th>
                      <th>NGÀY RA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {closedSignals.slice(0, 10).map((signal, idx) => {
                      const entryPrice = signal.entryPrice || 0
                      const exitPrice = signal.exitPrice || 0
                      const plPct = exitPrice > 0 && entryPrice > 0 ? ((exitPrice - entryPrice) / entryPrice * 100) : null
                      const plColor = plPct === null ? '#94a3b8' : plPct >= 0 ? '#10b981' : '#ef4444'
                      const exitReasonDisplay = (() => {
                        const r = signal.exitReason
                        if (!r) return { text: '-', icon: '' }
                        if (r === 'STOP_LOSS') return { text: 'Cắt lỗ', icon: '🔴' }
                        if (r === 'TAKE_PROFIT') return { text: 'Chốt lời', icon: '🟢' }
                        if (r === 'MA20_BREAK') return { text: 'MA20 Cross', icon: '🟠' }
                        if (r === 'MA20_CONSECUTIVE') return { text: 'MA20 (2N)', icon: '🟠' }
                        if (r === 'MA20_HIGH_VOLUME') return { text: 'MA20 (Vol)', icon: '🟠' }
                        return { text: 'Thủ công', icon: '⚪' }
                      })()
                      return (
                        <tr key={signal.id || idx}>
                          <td className="ticker-cell">{signal.ticker}</td>
                          <td className="price-cell">{entryPrice > 0 ? formatCurrency(entryPrice) : '-'}</td>
                          <td style={{ color: plColor, fontWeight: '600' }}>{exitPrice > 0 ? formatCurrency(exitPrice) : '-'}</td>
                          <td style={{ color: plColor, fontWeight: '700' }}>{plPct !== null ? `${plPct >= 0 ? '+' : ''}${plPct.toFixed(1)}%` : '-'}</td>
                          <td>{signal.exitReason ? <span style={{ fontSize: '12px' }}>{exitReasonDisplay.icon} {exitReasonDisplay.text}</span> : <span style={{ color: '#475569' }}>-</span>}</td>
                          <td className="score-cell"><span className="score-badge">{signal.score}</span></td>
                          <td className="type-cell">{signal.type}</td>
                          <td className="date-cell">{signal.date}</td>
                          <td className="date-cell">{signal.exitDate ? formatDate(signal.exitDate) : '-'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Lock overlay */}
              {closedSignals.length > 10 && (
                <div style={{ position: 'relative', marginTop: '-20px' }}>
                  <div style={{ height: '100px', background: 'linear-gradient(to bottom, transparent, #0B0F1A)', pointerEvents: 'none' }} />
                  <div style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid #334155', borderRadius: '16px', padding: '32px 24px', textAlign: 'center', marginBottom: '24px' }}>
                    <div style={{ fontSize: '28px', marginBottom: '12px' }}>🔒</div>
                    <h3 style={{ color: '#e2e8f0', fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
                      Còn {closedSignals.length - 10} tín hiệu chưa hiển thị
                    </h3>
                    <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '20px', lineHeight: '1.6' }}>
                      Đăng ký tài khoản miễn phí để xem toàn bộ lịch sử<br/>
                      tín hiệu với đầy đủ P/L và phân tích chi tiết
                    </p>
                    <button className="btn-primary-large" onClick={() => setShowCampaign(true)} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                      Đăng ký miễn phí — Xem full lịch sử →
                    </button>
                    <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'center', gap: '24px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>✅ Miễn phí 100%</span>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>✅ Không cần thẻ tín dụng</span>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>✅ Dữ liệu thật, minh bạch</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          <div className="showcase-cta">
            <button className="btn-primary-large" onClick={() => setShowCampaign(true)}>
              Nhận tín hiệu mới nhất miễn phí →
            </button>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section style={{ padding: '80px 0', background: 'linear-gradient(180deg, #0B0F1A 0%, #0f172a 100%)' }}>
        <div className="container">
          <div className="section-header">
            <h2>Nhà đầu tư nói gì về AI Advisor</h2>
            <p>Phản hồi thực tế từ cộng đồng MVP đang sử dụng hệ thống</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginTop: '40px' }}>
            {[
              { icon: 'H', color: '#10b981', border: '#10b981', quote: 'Hôm trước hệ thống cảnh báo giảm tỷ trọng, tôi kịp thoát phần lớn vị thế trước khi tin xấu ra. Cảnh báo rủi ro của AI Advisor thực sự có tác dụng.', years: '3 năm kinh nghiệm · Hà Nội' },
              { icon: 'K', color: '#3b82f6', border: '#3b82f6', quote: 'Theo tín hiệu của hệ thống, tôi vào HAH và chốt lời 9%. Tôi vẫn theo cảnh báo thị trường để quyết định có nên vào tiếp hay không — kỷ luật hơn hẳn so với trước.', years: '4 năm kinh nghiệm · Hà Nội' },
              { icon: 'P', color: '#8b5cf6', border: '#8b5cf6', quote: 'Mua PVB theo tín hiệu hệ thống, chốt được 17%. Tôi đang test với số lượng nhỏ nhưng kết quả rất khả quan — sẽ tăng tỷ trọng khi thị trường ổn định hơn.', years: '5 năm kinh nghiệm · Hà Nội' },
            ].map((t, i) => (
              <div key={i} style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid #334155', borderRadius: '16px', padding: '28px' }}>
                <div style={{ fontSize: '36px', color: t.color, marginBottom: '16px', lineHeight: 1 }}>"</div>
                <p style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: '1.7', marginBottom: '24px', fontStyle: 'italic' }}>{t.quote}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '44px', height: '44px', borderRadius: '50%', flexShrink: 0, background: `linear-gradient(135deg, ${t.color}, ${t.border})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px', fontWeight: '700', color: 'white' }}>{t.icon}</div>
                  <div>
                    <div style={{ color: '#e2e8f0', fontWeight: '600', fontSize: '14px' }}>Nhà đầu tư cá nhân</div>
                    <div style={{ color: '#64748b', fontSize: '12px' }}>{t.years}</div>
                  </div>
                  <div style={{ marginLeft: 'auto', display: 'flex', gap: '2px' }}>
                    {[1,2,3,4,5].map(i => <span key={i} style={{ color: '#f59e0b', fontSize: '13px' }}>★</span>)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Auth Modal */}
      {showAuth && (
        <div className="auth-modal">
          <div className="modal-overlay" onClick={() => setShowAuth(false)}></div>
          <div className="modal-content">
            <button className="modal-close" onClick={() => setShowAuth(false)}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>

            <div className="auth-header">
              <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:"9px",marginBottom:"10px"}}>
                <svg width="32" height="32" viewBox="0 0 40 40" fill="none">
                  <defs>
                    <linearGradient id="authLogoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style={{stopColor:'#3b82f6',stopOpacity:1}}/>
                      <stop offset="100%" style={{stopColor:'#8b5cf6',stopOpacity:1}}/>
                    </linearGradient>
                  </defs>
                  <path d="M20 8L32 14V26L20 32L8 26V14L20 8Z" stroke="url(#authLogoGradient)" strokeWidth="2" fill="none"/>
                  <path d="M20 8V20M20 20L32 26M20 20L8 26" stroke="url(#authLogoGradient)" strokeWidth="2"/>
                  <circle cx="20" cy="20" r="3" fill="url(#authLogoGradient)"/>
                </svg>
                <span style={{fontWeight:700,fontSize:"18px",background:"linear-gradient(135deg,#3b82f6,#8b5cf6)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>AI Advisor</span>
              </div>
              <h2>{isLogin ? 'Đăng nhập' : 'Đăng ký'}</h2>
              <p style={{color:"#64748b",fontSize:"13px",marginTop:"4px"}}>Đầu tư thông minh với AI</p>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              {!isLogin && (
                <div className="form-field">
                  <label>Họ và tên</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Nguyễn Văn A"
                    required={!isLogin}
                  />
                </div>
              )}

              <div className="form-field">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="email@example.com"
                  required
                />
              </div>

              <div className="form-field">
                <label>Mật khẩu</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  placeholder="••••••••"
                  required
                />
              </div>

              <button type="submit" className="btn-submit">
                {isLogin ? 'Đăng nhập' : 'Tạo tài khoản'}
              </button>

              <div className="auth-switch">
                {isLogin ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}
                <button
                  type="button"
                  onClick={() => { if(isLogin){ setShowAuth(false); setShowCampaign(true); } else { setIsLogin(true); } }}
                  className="switch-btn"
                >
                  {isLogin ? 'Đăng ký tài khoản mới' : 'Đăng nhập'}
                </button>
              </div>
            </form>

            <div className="auth-footer">
              <p>Bằng việc đăng nhập, bạn đồng ý với</p>
              <div className="auth-links">
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(false); setShowTerms(true); }}>Điều khoản dịch vụ</a>
                <span>•</span>
                <a href="#">Chính sách bảo mật</a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* About Us Modal */}
      {showAbout && (
        <div className="about-modal">
          <div className="modal-overlay" onClick={() => setShowAbout(false)}></div>
          <div className="modal-content about-content">
            <button className="modal-close" onClick={() => setShowAbout(false)}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>

            <div className="about-header">
              <div className="about-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="16" x2="12" y2="12"/>
                  <line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
              </div>
              <h2>Về AI Advisor</h2>
              <p>Hệ thống hỗ trợ ra quyết định đầu tư thông minh</p>
            </div>

            <div className="about-body">
              <div className="about-section">
                <h3>Vấn đề chúng tôi giải quyết</h3>
                <p>
                  Hầu hết nhà đầu tư cá nhân – dù có kinh nghiệm – đều từng đối mặt với những thách thức sau:
                </p>

                <div className="about-problems">
                  <div className="about-problem-item">
                    <div className="problem-icon-small">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <div>
                      <strong>Hành động bốc đồng theo cảm xúc</strong> (FOMO mua đỉnh, hoảng loạn bán đáy)
                    </div>
                  </div>

                  <div className="about-problem-item">
                    <div className="problem-icon-small">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <div>
                      <strong>Không có cơ chế cảnh báo rủi ro đủ sớm</strong>
                    </div>
                  </div>

                  <div className="about-problem-item">
                    <div className="problem-icon-small">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <div>
                      <strong>Không có ai hoặc công cụ nào "nhắc họ dừng lại"</strong> khi hành vi bắt đầu lệch khỏi kế hoạch ban đầu
                    </div>
                  </div>
                </div>
              </div>

              <div className="about-section">
                <div className="about-philosophy">
                  <div className="philosophy-icon-large">💡</div>
                  <h3>Triết lý cốt lõi</h3>
                  <p className="philosophy-quote-modal">
                    "Không thay nhà đầu tư quyết định – mà giúp nhà đầu tư ra quyết định tỉnh táo hơn."
                  </p>
                </div>
              </div>

              <div className="about-section">
                <h3>Hệ thống được thiết kế xoay quanh 3 trụ cột:</h3>
                <div className="about-pillars">
                  <div className="about-pillar-item">
                    <div className="pillar-number-small">1</div>
                    <div className="pillar-content">
                      <h4>Hỗ trợ quyết định</h4>
                      <p>Cung cấp tín hiệu, kịch bản và bối cảnh thị trường theo logic nhất quán</p>
                    </div>
                  </div>

                  <div className="about-pillar-item">
                    <div className="pillar-number-small">2</div>
                    <div className="pillar-content">
                      <h4>Bảo vệ rủi ro</h4>
                      <p>Cảnh báo khi xác suất bất lợi tăng cao, khi danh mục hoặc hành vi vượt ngưỡng an toàn</p>
                    </div>
                  </div>

                  <div className="about-pillar-item">
                    <div className="pillar-number-small">3</div>
                    <div className="pillar-content">
                      <h4>Kỷ luật hóa hành vi</h4>
                      <p>Giúp nhà đầu tư tuân thủ kế hoạch đã chọn, thay vì phản ứng bốc đồng theo thị trường</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="about-section">
                <div className="about-vision">
                  <h3>Tầm nhìn dài hạn</h3>
                  <p>
                    Xây dựng một trợ lý tài chính AI cá nhân, đóng vai trò như <strong>"bản đồ định hướng"</strong> cho nhà đầu tư – không dẫn đường tắt, không hứa lợi nhuận, nhưng <strong>giúp giảm sai lầm nghiêm trọng và tăng xác suất tồn tại bền vững trên thị trường.</strong>
                  </p>
                </div>
              </div>
            </div>

            <div className="about-actions">
              <button className="btn-understand" onClick={() => { setShowAbout(false); setShowAuth(true); }}>
                Trải nghiệm ngay
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Terms & Disclaimer Modal */}
      {showTerms && (
        <div className="terms-modal">
          <div className="modal-overlay" onClick={() => setShowTerms(false)}></div>
          <div className="modal-content terms-content">
            <button className="modal-close" onClick={() => setShowTerms(false)}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>

            <div className="terms-header">
              <div className="terms-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="12" y1="18" x2="12" y2="12"/>
                  <line x1="12" y1="9" x2="12.01" y2="9"/>
                </svg>
              </div>
              <h2>Disclaimer – Tuyên bố miễn trừ trách nhiệm</h2>
              <p>AI Advisor</p>
            </div>

            <div className="terms-body">
              <div className="terms-section">
                <p className="terms-intro">
                  <strong>AI Advisor là hệ thống hỗ trợ ra quyết định, không phải dịch vụ tư vấn đầu tư, và không đại diện cho bất kỳ tổ chức môi giới hay tài chính nào.</strong>
                </p>
              </div>

              <div className="terms-section">
                <h3>Các nội dung do AI Advisor cung cấp bao gồm (nhưng không giới hạn):</h3>
                <ul className="terms-list">
                  <li>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>Tín hiệu mua/bán và cảnh báo rủi ro</span>
                  </li>
                  <li>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>Phân tích xu hướng, kịch bản thị trường</span>
                  </li>
                  <li>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>Gợi ý quản trị hành vi và kỷ luật đầu tư</span>
                  </li>
                </ul>
              </div>

              <div className="terms-section important-notice">
                <div className="notice-icon">⚠️</div>
                <div className="notice-content">
                  <h4>Lưu ý quan trọng</h4>
                  <p>
                    Tất cả các nội dung trên <strong>chỉ mang tính tham khảo</strong> và hỗ trợ quá trình ra quyết định.
                  </p>
                  <p className="highlight">
                    <strong>Người dùng tự chịu hoàn toàn trách nhiệm đối với mọi quyết định mua, bán, nắm giữ tài sản.</strong>
                  </p>
                </div>
              </div>

              <div className="terms-section">
                <p className="terms-footer-text">
                  Bằng việc sử dụng AI Advisor, bạn xác nhận rằng bạn đã đọc, hiểu và đồng ý với các điều khoản miễn trừ trách nhiệm này.
                </p>
              </div>
            </div>

            <div className="terms-actions">
              <button className="btn-understand" onClick={() => setShowTerms(false)}>
                Tôi đã hiểu
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-brand">
              <h3>AI Advisor</h3>
              <p>Nền tảng đầu tư chứng khoán thông minh với AI</p>
            </div>

            <div className="footer-links">
              <div className="footer-column">
                <h4>Sản phẩm</h4>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(true); }}>Tín hiệu mua bán</a>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(true); }}>Quản trị danh mục</a>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(true); }}>Tư vấn AI</a>
              </div>

              <div className="footer-column">
                <h4>Công ty</h4>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAbout(true); }}>Về chúng tôi</a>
                <a href="#">Blog</a>
                <a href="#">Liên hệ</a>
              </div>

              <div className="footer-column">
                <h4>Hỗ trợ</h4>
                <a href="#">Trung tâm trợ giúp</a>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowTerms(true); }}>Điều khoản</a>
                <a href="#">Bảo mật</a>
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <p>© 2025 AI Advisor. All rights reserved.</p>
            <p className="disclaimer-small">
              Đầu tư chứng khoán có rủi ro. Vui lòng nghiên cứu kỹ trước khi quyết định.
            </p>
          </div>
        </div>
      </footer>

      {/* Custom CSS for table */}
      <style jsx>{`
        .signals-table-container {
          overflow-x: auto;
          margin: 30px 0;
        }

        .signals-table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          border-radius: 12px;
          overflow: hidden;
        }

        .signals-table thead {
          background: rgba(15, 23, 42, 0.8);
        }

        .signals-table th {
          padding: 16px 20px;
          text-align: left;
          font-size: 12px;
          font-weight: 600;
          color: #94a3b8;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          border-bottom: 1px solid #334155;
        }

        .signals-table tbody tr {
          border-bottom: 1px solid #334155;
          transition: background 0.2s;
        }

        .signals-table tbody tr:last-child {
          border-bottom: none;
        }

        .signals-table tbody tr:hover {
          background: rgba(59, 130, 246, 0.05);
        }

        .signals-table td {
          padding: 20px;
          font-size: 14px;
          color: #e2e8f0;
        }

        .ticker-cell {
          font-weight: 700;
          font-size: 16px;
          color: #3b82f6;
        }

        .price-cell {
          font-weight: 500;
          color: #e2e8f0;
        }

        .stoploss-cell {
          font-weight: 600;
          color: #ef4444;
        }

        .takeprofit-cell {
          font-weight: 600;
          color: #10b981;
        }

        .score-cell {
          text-align: center;
        }

        .score-badge {
          display: inline-block;
          padding: 6px 16px;
          background: #10b981;
          color: #fff;
          font-weight: 700;
          font-size: 14px;
          border-radius: 20px;
        }

        .type-cell {
          color: #94a3b8;
          font-size: 13px;
        }

        .date-cell {
          color: #94a3b8;
          font-size: 13px;
        }

        .strategy-info {
          margin-top: 40px;
          padding: 20px 0;
        }

        .strategy-card {
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 30px;
          display: flex;
          gap: 20px;
        }

        .strategy-icon {
          font-size: 48px;
          flex-shrink: 0;
        }

        .strategy-content h4 {
          font-size: 20px;
          color: #3b82f6;
          margin-bottom: 12px;
        }

        .strategy-content p {
          color: #94a3b8;
          margin-bottom: 16px;
          line-height: 1.6;
        }

        .strategy-content ul {
          list-style: none;
          padding: 0;
        }

        .strategy-content li {
          color: #e2e8f0;
          padding: 8px 0;
          padding-left: 24px;
          position: relative;
          line-height: 1.6;
        }

        .strategy-content li:before {
          content: "→";
          position: absolute;
          left: 0;
          color: #3b82f6;
          font-weight: bold;
        }

        .strategy-content strong {
          color: #10b981;
        }

        .mobile-cards { display: none; }
        .desktop-table { display: block; }

        @media (max-width: 768px) {
          .mobile-cards { display: block !important; }
          .desktop-table { display: none !important; }

          .signals-table {
            font-size: 12px;
          }

          .signals-table th,
          .signals-table td {
            padding: 12px 10px;
          }

          .ticker-cell {
            font-size: 14px;
          }

          .strategy-card {
            flex-direction: column;
            padding: 20px;
          }

          .strategy-icon {
            font-size: 36px;
          }
        }
      `}</style>

      {/* ── CHANGE PASSWORD MODAL (first login) ── */}
      {showChangePwd && (
        <ChangePwdModal
          token={loginToken}
          userData={loginUserData}
          onSuccess={() => { setShowChangePwd(false); onLogin(loginUserData); }}
        />
      )}

      {/* ── CAMPAIGN POPUP ── */}
      {showCampaign && (
        <CampaignPopup onClose={() => setShowCampaign(false)} />
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// CAMPAIGN POPUP — 30 Beta Users · 25/03–10/4/2026
// ─────────────────────────────────────────────────────────────
function CampaignPopup({ onClose }) {
  const API_URL = window.location.hostname.includes('staging')
    ? 'https://ai-advisor1-staging.onrender.com'
    : 'https://ai-advisor1-backend.onrender.com'

  const [slots, setSlots] = useState({ taken: 0, remaining: 30, is_full: false })
  const [form, setForm] = useState({ fullName: '', email: '', phone: '', experience: '', source: '' })
  const [phase, setPhase] = useState('form')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [agreed, setAgreed] = useState(false)
  const [countdown, setCountdown] = useState({ d: '--', h: '--', m: '--', s: '--' })

  useEffect(() => {
    fetch(`${API_URL}/api/campaign/slots`)
      .then(r => r.json())
      .then(d => setSlots(d))
      .catch(() => {})
  }, [])

  useEffect(() => {
    const tick = () => {
      const diff = Math.max(0, new Date('2026-04-10T23:59:59+07:00') - Date.now())
      setCountdown({
        d: String(Math.floor(diff / 86400000)).padStart(2, '0'),
        h: String(Math.floor((diff % 86400000) / 3600000)).padStart(2, '0'),
        m: String(Math.floor((diff % 3600000) / 60000)).padStart(2, '0'),
        s: String(Math.floor((diff % 60000) / 1000)).padStart(2, '0'),
      })
    }
    tick(); const id = setInterval(tick, 1000); return () => clearInterval(id)
  }, [])

  const handleSubmit = async () => {
    if (!form.fullName.trim()) return setError('Vui lòng nhập họ tên')
    if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return setError('Email chưa hợp lệ')
    if (!form.phone || form.phone.replace(/\D/g, '').length < 9) return setError('Số điện thoại chưa hợp lệ')
    if (!agreed) return setError('Vui lòng đồng ý điều khoản')
    setError(''); setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/campaign/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (data.success) setPhase(data.status === 'waiting' ? 'waiting' : 'success')
      else setError(data.error || 'Lỗi không xác định. Thử lại sau.')
    } catch { setError('Không thể kết nối server. Vui lòng thử lại.') }
    finally { setLoading(false) }
  }

  const pct = Math.min(100, (slots.taken / 30) * 100)

  const S = {
    backdrop: { position:'fixed', inset:0, background:'rgba(5,6,8,0.9)', display:'flex', alignItems:'center', justifyContent:'center', padding:16, zIndex:9999, fontFamily:"'Be Vietnam Pro', Arial, sans-serif" },
    popup: { position:'relative', background:'#11141a', border:'1px solid rgba(201,168,76,0.25)', borderRadius:4, width:'100%', maxWidth:500, maxHeight:'92vh', overflowY:'auto', boxShadow:'0 32px 80px rgba(0,0,0,0.8)', scrollbarWidth:'none' },
    topBar: { height:2, background:'linear-gradient(90deg,transparent,#c9a84c 30%,#f0d690 50%,#c9a84c 70%,transparent)' },
    closeBtn: { position:'absolute', top:12, right:12, width:26, height:26, border:'1px solid rgba(201,168,76,0.25)', borderRadius:2, background:'transparent', color:'#aaa', fontSize:14, cursor:'pointer', display:'flex', alignItems:'center', justifyContent:'center' },
    header: { padding:'22px 28px 0' },
    eyebrow: { fontSize:10, fontWeight:700, letterSpacing:'2px', textTransform:'uppercase', color:'#c9a84c', marginBottom:10 },
    title: { fontFamily:'Georgia,serif', fontSize:'clamp(20px,4vw,24px)', lineHeight:1.2, color:'#f7f5f0', marginBottom:8, margin:'0 0 8px' },
    sub: { fontSize:13, color:'#888d96', lineHeight:1.65, marginBottom:18 },
    urgBar: { margin:'0 28px', display:'flex', alignItems:'center', gap:8, background:'rgba(201,168,76,0.07)', border:'1px solid rgba(201,168,76,0.18)', borderRadius:2, padding:'10px 14px' },
    urgItem: { display:'flex', flexDirection:'column', alignItems:'center', flex:1, textAlign:'center' },
    urgValRed: { fontSize:18, fontWeight:900, color:'#ef4444', lineHeight:1 },
    urgVal: { fontSize:13, fontWeight:900, color:'#c9a84c', lineHeight:1 },
    urgLabel: { fontSize:9, color:'#555a63', textTransform:'uppercase', letterSpacing:'0.5px', marginTop:2 },
    urgSep: { width:1, height:30, background:'rgba(201,168,76,0.18)', flexShrink:0 },
    cdRow: { display:'flex', alignItems:'center', gap:2, marginBottom:2 },
    cdNum: { fontSize:15, fontWeight:900, color:'#f7f5f0', minWidth:22, background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:2, padding:'1px 3px', textAlign:'center' },
    cdSep: { fontSize:13, fontWeight:700, color:'#c9a84c', lineHeight:2 },
    slotsWrap: { padding:'12px 28px 0' },
    slotsHdr: { display:'flex', justifyContent:'space-between', marginBottom:5 },
    track: { height:3, background:'rgba(255,255,255,0.06)', borderRadius:2, overflow:'hidden', marginBottom:14 },
    fill: { height:'100%', background:'linear-gradient(90deg,#8a6b28,#c9a84c)', borderRadius:2, transition:'width 1.2s ease' },
    offerSec: { padding:'0 28px 14px' },
    secLabel: { fontSize:10, fontWeight:700, letterSpacing:'2px', textTransform:'uppercase', color:'#8a6b28', marginBottom:10 },
    offerGrid: { display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:8, marginBottom:10 },
    card: { background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:2, padding:'10px 12px', display:'flex', alignItems:'flex-start', gap:8 },
    cardHi: { background:'rgba(201,168,76,0.05)', border:'1px solid rgba(201,168,76,0.28)', borderRadius:2, padding:'10px 12px', display:'flex', alignItems:'flex-start', gap:8 },
    icon: { width:24, height:24, background:'rgba(201,168,76,0.1)', borderRadius:2, display:'flex', alignItems:'center', justifyContent:'center', fontSize:12, flexShrink:0 },
    cardName: { fontSize:11, fontWeight:700, color:'#f7f5f0', marginBottom:2 },
    cardDesc: { fontSize:10, color:'#555a63', lineHeight:1.4 },
    priceRow: { display:'flex', alignItems:'center', gap:8, background:'rgba(201,168,76,0.06)', border:'1px solid rgba(201,168,76,0.15)', borderRadius:2, padding:'9px 12px' },
    priceOrig: { fontSize:12, color:'#555', textDecoration:'line-through', textDecorationColor:'#d63c3c' },
    priceNew: { fontSize:18, fontWeight:900, color:'#c9a84c' },
    priceSub: { fontSize:10, color:'#555a63', marginLeft:'auto', textAlign:'right', lineHeight:1.3 },
    formSec: { padding:'0 28px 22px' },
    fRow: { marginBottom:9 },
    fLabel: { display:'block', fontSize:11, fontWeight:600, color:'#888d96', marginBottom:4 },
    // ── FIX 3: select background dark so options readable ──
    input: { width:'100%', background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.1)', borderRadius:2, padding:'10px 12px', fontSize:13, color:'#f7f5f0', outline:'none', boxSizing:'border-box', fontFamily:'inherit' },
    select: { width:'100%', background:'#1e2230', border:'1px solid rgba(255,255,255,0.15)', borderRadius:2, padding:'10px 12px', fontSize:13, color:'#e2e8f0', outline:'none', appearance:'none', WebkitAppearance:'none', boxSizing:'border-box', fontFamily:'inherit', cursor:'pointer' },
    twoCol: { display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 },
    checkRow: { display:'flex', alignItems:'flex-start', gap:8, marginBottom:10, cursor:'pointer' },
    checkText: { fontSize:11, color:'#888d96', lineHeight:1.5 },
    errBox: { background:'rgba(214,60,60,0.1)', border:'1px solid rgba(214,60,60,0.25)', borderRadius:2, padding:'8px 12px', fontSize:12, color:'#ef8888', marginBottom:10 },
    btn: { width:'100%', padding:'14px', background:'#c9a84c', color:'#0d0f12', border:'none', borderRadius:2, fontSize:13, fontWeight:800, cursor:'pointer', textTransform:'uppercase', letterSpacing:'0.5px' },
    btnSub: { textAlign:'center', fontSize:10, color:'#555a63', marginTop:7 },
    footer: { padding:'10px 28px 16px', borderTop:'1px solid rgba(255,255,255,0.05)', display:'flex', alignItems:'center', gap:7 },
    footerNote: { fontSize:10, color:'#3d4249', lineHeight:1.5 },
    center: { padding:'40px 28px', textAlign:'center' },
    successIcon: { width:50, height:50, background:'rgba(26,122,74,0.15)', border:'1px solid rgba(26,122,74,0.4)', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20, margin:'0 auto 14px', color:'#4ade80' },
    waitIcon: { width:50, height:50, background:'rgba(201,168,76,0.1)', border:'1px solid rgba(201,168,76,0.3)', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20, margin:'0 auto 14px' },
    succTitle: { fontFamily:'Georgia,serif', fontSize:20, color:'#f7f5f0', marginBottom:8 },
    succSub: { fontSize:13, color:'#888d96', lineHeight:1.65, maxWidth:320, margin:'0 auto 18px' },
    steps: { textAlign:'left', background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.07)', borderRadius:2, padding:14, marginBottom:16 },
    stepItem: { display:'flex', alignItems:'flex-start', gap:8, fontSize:12, color:'#888d96', padding:'4px 0' },
    stepNum: { width:16, height:16, background:'rgba(201,168,76,0.15)', border:'1px solid rgba(201,168,76,0.3)', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:8, fontWeight:800, color:'#c9a84c', flexShrink:0, marginTop:1 },
  }

  return (
    <div style={S.backdrop} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={S.popup}>
        <div style={S.topBar}/>
        <button style={S.closeBtn} onClick={onClose}>✕</button>

        {phase === 'form' && (<>
          <div style={S.header}>
            <div style={S.eyebrow}>✦ Chiến dịch beta · 25/3 – 10/4/2026</div>
            <h2 style={S.title}>Tham gia <em style={{color:'#c9a84c'}}>30 nhà đầu tư</em><br/>đầu tiên — Miễn phí hoàn toàn</h2>
            <p style={S.sub}>AI Advisor mở cửa cho đúng <strong style={{color:'#f7f5f0'}}>30 tài khoản mới</strong>. Không mất tiền — chỉ cần cam kết trải nghiệm và phản hồi thực tế.</p>
          </div>

          {/* Urgency */}
          <div style={S.urgBar}>
            <div style={S.urgItem}>
              <div style={S.urgValRed}>{slots.remaining}</div>
              <div style={S.urgLabel}>Suất còn lại</div>
            </div>
            <div style={S.urgSep}/>
            <div style={S.urgItem}>
              <div style={S.cdRow}>
                {['d','h','m','s'].map((k,i) => (
                  <span key={k} style={{display:'flex',alignItems:'center',gap:2}}>
                    <span style={S.cdNum}>{countdown[k]}</span>
                    {i < 3 && <span style={S.cdSep}>:</span>}
                  </span>
                ))}
              </div>
              <div style={S.urgLabel}>Thời gian còn lại</div>
            </div>
            <div style={S.urgSep}/>
            <div style={S.urgItem}>
              <div style={S.urgVal}>đến 10/4</div>
              <div style={S.urgLabel}>Miễn phí</div>
            </div>
          </div>

          {/* Slots bar */}
          <div style={S.slotsWrap}>
            <div style={S.slotsHdr}>
              <span style={{fontSize:11,color:'#555a63'}}>Đã đăng ký</span>
              <span style={{fontSize:11,fontWeight:700,color:'#ef4444'}}>{slots.taken}/30 suất</span>
            </div>
            <div style={S.track}><div style={{...S.fill, width:`${pct}%`}}/></div>
          </div>

          {/* Offer */}
          <div style={S.offerSec}>
            <div style={S.secLabel}>Bạn nhận được gì</div>
            <div style={S.offerGrid}>
              {[
                {icon:'📈',name:'Tín hiệu Mua/Bán',desc:'VN30 blue-chip hàng ngày',hi:true},
                {icon:'🛡️',name:'AI Risk Shield',desc:'Cảnh báo danh mục'},
                {icon:'🧘',name:'AI Coach',desc:'Ngăn FOMO & panic'},
              ].map((c,i)=>(
                <div key={i} style={c.hi?S.cardHi:S.card}>
                  <div style={S.icon}>{c.icon}</div>
                  <div><div style={S.cardName}>{c.name}</div><div style={S.cardDesc}>{c.desc}</div></div>
                </div>
              ))}
            </div>
            <div style={S.priceRow}>
              <span style={S.priceOrig}>199.000đ/tháng</span>
              <span style={{color:'#c9a84c',fontSize:11}}>→</span>
              <span style={S.priceNew}>MIỄN PHÍ</span>
              <div style={S.priceSub}>Miễn phí đến<br/><strong>hết 10/4/2026</strong></div>
            </div>
          </div>

          {/* Form */}
          <div style={S.formSec}>
            <div style={S.secLabel}>Đăng ký ngay</div>
            {error && <div style={S.errBox}>⚠ {error}</div>}
            <div style={S.fRow}>
              <label style={S.fLabel}>Họ và tên <span style={{color:'#c9a84c'}}>*</span></label>
              <input style={S.input} placeholder="Nguyễn Văn A" value={form.fullName} onChange={e=>setForm({...form,fullName:e.target.value})}/>
            </div>
            <div style={S.twoCol}>
              <div style={S.fRow}>
                <label style={S.fLabel}>Email <span style={{color:'#c9a84c'}}>*</span></label>
                <input style={S.input} type="email" placeholder="ban@email.com" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/>
              </div>
              <div style={S.fRow}>
                <label style={S.fLabel}>Số điện thoại <span style={{color:'#c9a84c'}}>*</span></label>
                <input style={S.input} type="tel" placeholder="09xx xxx xxx" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/>
              </div>
            </div>
            <div style={S.twoCol}>
              <div style={S.fRow}>
                <label style={S.fLabel}>Kinh nghiệm đầu tư</label>
                <select style={S.select} value={form.experience} onChange={e=>setForm({...form,experience:e.target.value})}>
                  <option value="" style={{background:'#1e2230',color:'#e2e8f0'}}>Chọn...</option>
                  <option value="new" style={{background:'#1e2230',color:'#e2e8f0'}}>Mới bắt đầu</option>
                  <option value="mid" style={{background:'#1e2230',color:'#e2e8f0'}}>1–3 năm</option>
                  <option value="senior" style={{background:'#1e2230',color:'#e2e8f0'}}>3–5 năm</option>
                  <option value="expert" style={{background:'#1e2230',color:'#e2e8f0'}}>&gt;5 năm</option>
                </select>
              </div>
              <div style={S.fRow}>
                <label style={S.fLabel}>Nguồn biết đến</label>
                <select style={S.select} value={form.source} onChange={e=>setForm({...form,source:e.target.value})}>
                  <option value="" style={{background:'#1e2230',color:'#e2e8f0'}}>Chọn...</option>
                  <option value="facebook" style={{background:'#1e2230',color:'#e2e8f0'}}>Facebook</option>
                  <option value="zalo" style={{background:'#1e2230',color:'#e2e8f0'}}>Zalo</option>
                  <option value="friend" style={{background:'#1e2230',color:'#e2e8f0'}}>Bạn bè</option>
                  <option value="search" style={{background:'#1e2230',color:'#e2e8f0'}}>Google</option>
                  <option value="other" style={{background:'#1e2230',color:'#e2e8f0'}}>Khác</option>
                </select>
              </div>
            </div>
            <label style={S.checkRow}>
              <input type="checkbox" checked={agreed} onChange={e=>setAgreed(e.target.checked)} style={{accentColor:'#c9a84c',marginTop:2,flexShrink:0}}/>
              <span style={S.checkText}>Tôi đồng ý với <span style={{color:'#c9a84c'}}>Điều khoản sử dụng</span> và <span style={{color:'#c9a84c'}}>Chính sách bảo mật</span>. Tôi hiểu AI Advisor là công cụ hỗ trợ, không phải tư vấn đầu tư.</span>
            </label>
            <button style={{...S.btn, opacity:loading?0.7:1}} onClick={handleSubmit} disabled={loading}>
              {loading ? 'Đang gửi...' : '✦ ĐĂNG KÝ THAM GIA NGAY'}
            </button>
            <div style={S.btnSub}>Còn <strong style={{color:'#ef4444'}}>{slots.remaining}</strong> suất · Miễn phí · Không cần thẻ ngân hàng</div>
          </div>
          <div style={S.footer}>
            <div style={{width:5,height:5,borderRadius:'50%',background:'#1a7a4a',flexShrink:0}}/>
            <div style={S.footerNote}>AI Advisor là công cụ hỗ trợ, không phải tư vấn đầu tư. · ai-advisor.vn</div>
          </div>
        </>)}

        {phase === 'success' && (
          <div style={S.center}>
            <div style={S.successIcon}>✓</div>
            <div style={S.succTitle}>Tài khoản đã sẵn sàng!</div>
            <div style={S.succSub}>Kiểm tra email ngay — mật khẩu tạm đã được gửi đến hòm thư của bạn.</div>
            <div style={S.steps}>
              {['Mở email từ AI Advisor, lấy mật khẩu tạm (kiểm tra cả spam)','Đăng nhập tại ai-advisor.vn/login → đổi mật khẩu','Tài khoản miễn phí đến hết 10/04/2026 🎉'].map((s,i)=>(
                <div key={i} style={{...S.stepItem, borderBottom:i<2?'1px solid rgba(255,255,255,0.04)':'none'}}>
                  <div style={S.stepNum}>{i+1}</div><span>{s}</span>
                </div>
              ))}
            </div>
            <button style={S.btn} onClick={onClose}>Đóng</button>
          </div>
        )}

        {phase === 'waiting' && (
          <div style={S.center}>
            <div style={S.waitIcon}>⏳</div>
            <div style={S.succTitle}>Bạn đã vào danh sách chờ</div>
            <div style={S.succSub}>Chương trình đã đủ 30 người. Chúng tôi sẽ <strong style={{color:'#c9a84c'}}>thông báo qua email</strong> ngay khi có suất mới.</div>
            <div style={S.steps}>
              {['Kiểm tra email xác nhận vị trí chờ từ AI Advisor','Khi có suất mới, bạn sẽ được thông báo tự động'].map((s,i)=>(
                <div key={i} style={{...S.stepItem, borderBottom:i<1?'1px solid rgba(255,255,255,0.04)':'none'}}>
                  <div style={S.stepNum}>{i+1}</div><span>{s}</span>
                </div>
              ))}
            </div>
            <button style={S.btn} onClick={onClose}>Đóng</button>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// CHANGE PASSWORD MODAL — Hiện khi đăng nhập lần đầu
// ─────────────────────────────────────────────────────────────
function ChangePwdModal({ token, userData, onSuccess }) {
  const API_URL = window.location.hostname.includes('staging')
    ? 'https://ai-advisor1-staging.onrender.com'
    : 'https://ai-advisor1-backend.onrender.com'

  const [oldPwd, setOldPwd]   = useState('')
  const [newPwd, setNewPwd]   = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)
  const [showPwd, setShowPwd] = useState(false)

  const strength = [/.{8,}/, /[A-Z]/, /[0-9]/, /[^A-Za-z0-9]/].filter(r => r.test(newPwd)).length
  const strengthLabel = ['', 'Yếu', 'Trung bình', 'Khá', 'Mạnh'][strength]
  const strengthColor = ['', '#ef4444', '#f59e0b', '#3b82f6', '#22c55e'][strength]

  const handleSubmit = async () => {
    if (!oldPwd) return setError('Vui lòng nhập mật khẩu tạm từ email')
    if (newPwd.length < 8) return setError('Mật khẩu mới phải ít nhất 8 ký tự')
    if (newPwd !== confirm) return setError('Mật khẩu xác nhận không khớp')
    setError(''); setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/auth/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ old_password: oldPwd, new_password: newPwd }),
      })
      const data = await res.json()
      if (data.success) {
        onSuccess()
      } else {
        setError(data.error || 'Lỗi không xác định')
      }
    } catch { setError('Không thể kết nối server') }
    finally { setLoading(false) }
  }

  const S = {
    backdrop: { position:'fixed', inset:0, background:'rgba(5,6,8,0.92)', display:'flex', alignItems:'center', justifyContent:'center', padding:16, zIndex:10000, fontFamily:"'Be Vietnam Pro', Arial, sans-serif" },
    card: { background:'#11141a', border:'1px solid rgba(201,168,76,0.25)', borderRadius:4, width:'100%', maxWidth:420, boxShadow:'0 32px 80px rgba(0,0,0,0.8)' },
    topBar: { height:2, background:'linear-gradient(90deg,transparent,#c9a84c 30%,#f0d690 50%,#c9a84c 70%,transparent)', borderRadius:'4px 4px 0 0' },
    body: { padding:'28px 28px 24px' },
    iconWrap: { width:48, height:48, background:'rgba(201,168,76,0.1)', border:'1px solid rgba(201,168,76,0.3)', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20, margin:'0 auto 16px' },
    title: { fontFamily:'Georgia,serif', fontSize:20, color:'#f7f5f0', textAlign:'center', marginBottom:6 },
    sub: { fontSize:12, color:'#888d96', textAlign:'center', lineHeight:1.65, marginBottom:20 },
    notice: { background:'rgba(201,168,76,0.08)', border:'1px solid rgba(201,168,76,0.2)', borderRadius:2, padding:'10px 14px', fontSize:12, color:'#c9a84c', marginBottom:18, lineHeight:1.6 },
    fRow: { marginBottom:12 },
    fLabel: { display:'block', fontSize:11, fontWeight:600, color:'#888d96', marginBottom:4 },
    inputWrap: { position:'relative' },
    input: { width:'100%', background:'rgba(255,255,255,0.04)', border:'1px solid rgba(255,255,255,0.1)', borderRadius:2, padding:'10px 36px 10px 12px', fontSize:13, color:'#f7f5f0', outline:'none', boxSizing:'border-box', fontFamily:'inherit' },
    eyeBtn: { position:'absolute', right:10, top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', fontSize:14, opacity:0.5, color:'#f7f5f0' },
    strengthRow: { display:'flex', gap:3, marginTop:6 },
    strengthBar: (i) => ({ flex:1, height:3, borderRadius:2, transition:'background .3s', background: i < strength ? strengthColor : 'rgba(255,255,255,0.08)' }),
    strengthLabel: { fontSize:10, color: strengthColor, marginTop:4 },
    matchMsg: { fontSize:10, marginTop:4, color: confirm && confirm !== newPwd ? '#ef4444' : '#22c55e' },
    errBox: { background:'rgba(214,60,60,0.1)', border:'1px solid rgba(214,60,60,0.25)', borderRadius:2, padding:'8px 12px', fontSize:12, color:'#ef8888', marginBottom:12 },
    btn: { width:'100%', padding:'13px', background:'#c9a84c', color:'#0d0f12', border:'none', borderRadius:2, fontSize:13, fontWeight:800, cursor:'pointer', textTransform:'uppercase' },
    hint: { fontSize:10, color:'#3d4249', textAlign:'center', marginTop:8, lineHeight:1.5 },
  }

  return (
    <div style={S.backdrop}>
      <div style={S.card}>
        <div style={S.topBar}/>
        <div style={S.body}>
          <div style={S.iconWrap}>🔐</div>
          <div style={S.title}>Đặt mật khẩu mới</div>
          <div style={S.sub}>Đây là lần đăng nhập đầu tiên của bạn.<br/>Vui lòng đổi mật khẩu tạm để bảo mật tài khoản.</div>

          <div style={S.notice}>
            📧 Mật khẩu tạm đã được gửi đến email của bạn khi đăng ký.<br/>
            Hãy kiểm tra hộp thư (kể cả spam) và nhập vào ô bên dưới.
          </div>

          {error && <div style={S.errBox}>⚠ {error}</div>}

          {/* Mật khẩu tạm */}
          <div style={S.fRow}>
            <label style={S.fLabel}>Mật khẩu tạm (từ email) <span style={{color:'#c9a84c'}}>*</span></label>
            <div style={S.inputWrap}>
              <input
                style={S.input}
                type={showPwd ? 'text' : 'password'}
                placeholder="Nhập mật khẩu tạm..."
                value={oldPwd}
                onChange={e => setOldPwd(e.target.value)}
              />
              <button style={S.eyeBtn} onClick={() => setShowPwd(v => !v)} tabIndex={-1}>{showPwd ? '🙈' : '👁'}</button>
            </div>
          </div>

          {/* Mật khẩu mới */}
          <div style={S.fRow}>
            <label style={S.fLabel}>Mật khẩu mới <span style={{color:'#c9a84c'}}>*</span></label>
            <div style={S.inputWrap}>
              <input
                style={S.input}
                type={showPwd ? 'text' : 'password'}
                placeholder="Ít nhất 8 ký tự..."
                value={newPwd}
                onChange={e => setNewPwd(e.target.value)}
              />
            </div>
            {newPwd && (<>
              <div style={S.strengthRow}>{[0,1,2,3].map(i => <div key={i} style={S.strengthBar(i)}/>)}</div>
              {strengthLabel && <div style={S.strengthLabel}>{strengthLabel}</div>}
            </>)}
          </div>

          {/* Xác nhận */}
          <div style={{...S.fRow, marginBottom:20}}>
            <label style={S.fLabel}>Xác nhận mật khẩu mới <span style={{color:'#c9a84c'}}>*</span></label>
            <input
              style={{...S.input, border: confirm && confirm !== newPwd ? '1px solid rgba(239,68,68,0.5)' : '1px solid rgba(255,255,255,0.1)'}}
              type={showPwd ? 'text' : 'password'}
              placeholder="Nhập lại mật khẩu mới..."
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
            />
            {confirm && <div style={S.matchMsg}>{confirm === newPwd ? '✓ Khớp' : '✗ Chưa khớp'}</div>}
          </div>

          <button style={{...S.btn, opacity: loading ? 0.7 : 1}} onClick={handleSubmit} disabled={loading}>
            {loading ? 'Đang xử lý...' : '🔐 XÁC NHẬN ĐỔI MẬT KHẨU'}
          </button>
          <div style={S.hint}>Sau khi đổi mật khẩu thành công bạn sẽ vào trang chính ngay lập tức</div>
        </div>
      </div>
    </div>
  )
}
