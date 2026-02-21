import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10000/api';

export default function LandingPage({ onLogin }) {
  const [showAuth, setShowAuth] = useState(false)
  const [showTerms, setShowTerms] = useState(false)
  const [showAbout, setShowAbout] = useState(false)
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  })

  // Fetch recommendations from API + historical data
  const [recommendations, setRecommendations] = useState([])
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
    
    // If price reached TP â†’ Sell 1/2
    if (currentPrice >= signal.takeProfit && signal.status === 'active') {
      return {
        status: 'half_sold',
        action: 'BÃN 1/2',
        reason: 'Äáº¡t Take Profit'
      }
    }
    
    // If already sold 1/2 and price cuts below MA20 â†’ Sell remaining 1/2
    if (signal.status === 'half_sold' && currentPrice < ma20) {
      return {
        status: 'fully_sold',
        action: 'BÃN Ná»T 1/2',
        reason: 'Cáº¯t xuá»‘ng MA20'
      }
    }
    
    // Otherwise hold
    if (signal.status === 'half_sold') {
      return {
        status: 'half_sold',
        action: 'Náº®M GIá»®',
        reason: 'TrÃªn MA20'
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
        // Map API signals to table format with correct date format
        const apiSignals = data.signals.slice(0, 10).map((signal, index) => {
          const dateStr = signal.date || signal.created_at
          
          return {
            id: signal.id || `api-${index + 1}`,
            ticker: signal.ticker || signal.code,
            entryPrice: signal.entry_price,
            stopLoss: signal.stop_loss,
            takeProfit: signal.take_profit,
            score: signal.strength || 75,
            type: signal.stock_type || 'Blue Chip',
            date: formatDate(dateStr), // Fix date format here
            status: 'active',
            action: null
          }
        })
        
        // Combine historical + API signals
        setRecommendations([...historicalSignals, ...apiSignals])
      } else {
        // If no API signals, show only historical
        setRecommendations(historicalSignals)
      }
    } catch (error) {
      console.error('Error fetching signals:', error)
      // On error, show historical signals
      setRecommendations(historicalSignals)
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

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Mock authentication
    const userData = {
      email: formData.email,
      name: formData.name || formData.email.split('@')[0],
      loginTime: new Date().toISOString()
    }
    
    localStorage.setItem('user', JSON.stringify(userData))
    onLogin(userData)
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
                Äáº§u tÆ° thÃ´ng minh vá»›i
                <span className="gradient-text" style={{display:"inline-flex",alignItems:"center",gap:"8px",verticalAlign:"middle"}}>
                  <svg width="42" height="42" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg" style={{display:"inline-block",verticalAlign:"middle",marginLeft:"6px",flexShrink:0}}>
                    <defs>
                      <linearGradient id="heroLogoG1" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stopColor="#38bdf8"/>
                        <stop offset="100%" stopColor="#2563eb"/>
                      </linearGradient>
                      <linearGradient id="heroLogoG2" x1="22" y1="0" x2="22" y2="44" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stopColor="#1e40af"/>
                        <stop offset="100%" stopColor="#0369a1"/>
                      </linearGradient>
                    </defs>
                    <path d="M22 3 L39 12.5 L39 31.5 L22 41 L5 31.5 L5 12.5 Z" fill="url(#heroLogoG2)" opacity="0.2" stroke="url(#heroLogoG1)" strokeWidth="1.5"/>
                    <path d="M22 10 L35 17.5 L35 26.5 L22 34 L9 26.5 L9 17.5 Z" fill="url(#heroLogoG1)" opacity="0.15"/>
                    <path d="M22 11 L32 22 L22 33 L12 22 Z" fill="url(#heroLogoG1)" opacity="0.95"/>
                    <path d="M22 16 L28 22 L22 28 L16 22 Z" fill="white" opacity="0.9"/>
                    <circle cx="22" cy="22" r="2" fill="white" opacity="0.6"/>
                  </svg>
                  AI Advisor
                </span>
              </h1>
              <p className="hero-subtitle">
                TÃ­n hiá»‡u mua bÃ¡n chÃ­nh xÃ¡c, quáº£n trá»‹ danh má»¥c tá»± Ä‘á»™ng, vÃ  tÆ° váº¥n AI 24/7 - 
                Ná»n táº£ng Ä‘áº§u tÆ° chá»©ng khoÃ¡n tháº¿ há»‡ má»›i
              </p>
              
              <div className="hero-stats">
                <div className="stat-item">
                  <div className="stat-number">{stats.totalSignals}+</div>
                  <div className="stat-label">TÃ­n hiá»‡u phÃ¡t sinh</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{stats.successRate}%</div>
                  <div className="stat-label">Tá»· lá»‡ thÃ nh cÃ´ng</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{stats.avgReturn}%</div>
                  <div className="stat-label">Lá»£i nhuáº­n TB</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number" style={{color: '#ef4444'}}>{stats.failureRate}%</div>		
                  <div className="stat-label">Tá»· lá»‡ khÃ´ng thÃ nh cÃ´ng</div>
                </div>
              </div>

              <div className="hero-cta">
                <button className="btn-primary-large" onClick={() => setShowAuth(true)}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                    <polyline points="10 17 15 12 10 7"/>
                    <line x1="15" y1="12" x2="3" y2="12"/>
                  </svg>
                  Báº¯t Ä‘áº§u ngay - Miá»…n phÃ­
                </button>
                <button className="btn-secondary-large" onClick={() => scrollToSection('showcase')}>
                  Xem lá»‹ch sá»­ khuyáº¿n nghá»‹
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
                          {marketRisk.market_mode === 'BULL' ? 'ðŸŸ¢' : marketRisk.market_mode === 'BEAR' ? 'ðŸ”´' : 'ðŸŸ¡'}{' '}
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
                        <span>Tá»· trá»ng CP: <strong style={{ color: '#e2e8f0' }}>{marketRisk.allocation}%</strong></span>
                        <span>Tiá»n máº·t: <strong style={{ color: '#e2e8f0' }}>{100 - marketRisk.allocation}%</strong></span>
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

                    {/* Factors - chá»‰ hiá»‡n nhá»¯ng yáº¿u tá»‘ cÃ³ dá»¯ liá»‡u */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {(marketRisk.factors || [])
                        .filter(factor => !factor.isRef && !factor.value?.includes('ChÆ°a cÃ³'))
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
                            {factor.positive ? 'â–² ' : 'â–¼ '}
                            {factor.value}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Timestamp */}
                    <div style={{
                      marginTop: '12px', fontSize: '11px', color: '#475569', textAlign: 'right',
                    }}>
                      Cáº­p nháº­t: {marketRisk.analyzed_at ? new Date(marketRisk.analyzed_at).toLocaleString('vi-VN') : 'N/A'}
                    </div>
                  </div>
                ) : (
                  <div style={{
                    padding: '40px 20px', textAlign: 'center',
                    background: 'linear-gradient(135deg, #0B0F1A 0%, #1a1f3a 100%)',
                    borderRadius: '0 0 12px 12px',
                  }}>
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>ðŸ“Š</div>
                    <div style={{ color: '#64748b', fontSize: '14px' }}>Äang táº£i phÃ¢n tÃ­ch thá»‹ trÆ°á»ng...</div>
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
            <h2>TÃ­nh nÄƒng ná»•i báº­t</h2>
            <p>CÃ´ng nghá»‡ AI tiÃªn tiáº¿n giÃºp tá»‘i Æ°u hÃ³a quyáº¿t Ä‘á»‹nh Ä‘áº§u tÆ°</p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <polyline points="19 12 12 19 5 12"/>
                </svg>
              </div>
              <h3>TÃ­n hiá»‡u mua bÃ¡n AI</h3>
              <p>PhÃ¢n tÃ­ch 343 mÃ£ chá»©ng khoÃ¡n 24/7, táº¡o tÃ­n hiá»‡u chÃ­nh xÃ¡c vá»›i tá»· lá»‡ thÃ nh cÃ´ng 78.5%</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                </svg>
              </div>
              <h3>Quáº£n trá»‹ danh má»¥c thÃ´ng minh</h3>
              <p>Theo dÃµi hiá»‡u suáº¥t, phÃ¢n bá»• tÃ i sáº£n tá»‘i Æ°u, vÃ  nháº­n cáº£nh bÃ¡o rá»§i ro ká»‹p thá»i</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <h3>TÆ° váº¥n AI 24/7</h3>
              <p>Trá»£ lÃ½ AI cÃ¡ nhÃ¢n giÃºp kiá»ƒm soÃ¡t cáº£m xÃºc, duy trÃ¬ ká»· luáº­t vÃ  ra quyáº¿t Ä‘á»‹nh sÃ¡ng suá»‘t</p>
            </div>
          </div>
        </div>
      </section>

      {/* Recommendations Table */}
      <section className="showcase" id="showcase">
        <div className="container">
          <div className="section-header">
            <h2>Lá»‹ch sá»­ khuyáº¿n nghá»‹</h2>
            <p>CÃ¡c tÃ­n hiá»‡u Ä‘Ã£ thÃ nh cÃ´ng trong thá»i gian gáº§n Ä‘Ã¢y</p>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <div style={{ fontSize: '16px' }}>â³ Äang táº£i tÃ­n hiá»‡u...</div>
            </div>
          ) : recommendations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>ðŸ“Š</div>
              <div style={{ fontSize: '18px', marginBottom: '10px' }}>ChÆ°a cÃ³ tÃ­n hiá»‡u nÃ o</div>
              <div style={{ fontSize: '14px' }}>Há»‡ thá»‘ng sáº½ tá»± Ä‘á»™ng táº¡o tÃ­n hiá»‡u má»›i</div>
            </div>
          ) : (
            <>
              <div className="signals-table-container">
                <table className="signals-table">
                  <thead>
                    <tr>
                      <th>MÃƒ CK</th>
                      <th>GIÃ VÃ€O</th>
                      <th>STOP LOSS</th>
                      <th>TAKE PROFIT</th>
                      <th>SCORE</th>
                      <th>LOáº I</th>
                      <th>NGÃ€Y</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendations.map((signal) => (
                      <tr key={signal.id}>
                        <td className="ticker-cell">{signal.ticker}</td>
                        <td className="price-cell">{formatCurrency(signal.entryPrice)}</td>
                        <td className="stoploss-cell">{formatCurrency(signal.stopLoss)}</td>
                        <td className="takeprofit-cell">{formatCurrency(signal.takeProfit)}</td>
                        <td className="score-cell">
                          <span className="score-badge">{signal.score}</span>
                        </td>
                        <td className="type-cell">{signal.type}</td>
                        <td className="date-cell">{signal.date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Sell Signal Strategy Info */}
              <div className="strategy-info">
                <div className="strategy-card">
                  <div className="strategy-icon">ðŸ“Š</div>
                  <div className="strategy-content">
                    <h4>Chiáº¿n lÆ°á»£c bÃ¡n tá»± Ä‘á»™ng</h4>
                    <p>Há»‡ thá»‘ng theo dÃµi cÃ¡c CP trong danh sÃ¡ch vÃ  Ä‘Æ°a ra tÃ­n hiá»‡u bÃ¡n theo quy táº¯c:</p>
                    <ul>
                      <li><strong>BÃ¡n 1/2:</strong> Khi giÃ¡ Ä‘áº¡t Take Profit</li>
                      <li><strong>BÃ¡n ná»‘t 1/2:</strong> Khi giÃ¡ cáº¯t xuá»‘ng MA20 (sau khi Ä‘Ã£ bÃ¡n 1/2)</li>
                      <li><strong>Náº¯m giá»¯:</strong> Khi giÃ¡ trÃªn MA20 (sau khi Ä‘Ã£ bÃ¡n 1/2)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          )}

          <div className="showcase-cta">
            <button className="btn-primary-large" onClick={() => setShowAuth(true)}>
              Truy cáº­p tÃ­n hiá»‡u má»›i nháº¥t
            </button>
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
              <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:"8px",marginBottom:"8px"}}>
                <svg width="28" height="28" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <defs>
                    <linearGradient id="authLogoG" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stopColor="#38bdf8"/>
                      <stop offset="100%" stopColor="#2563eb"/>
                    </linearGradient>
                  </defs>
                  <path d="M22 3 L39 12.5 L39 31.5 L22 41 L5 31.5 L5 12.5 Z" fill="#1e3a5f" stroke="url(#authLogoG)" strokeWidth="1.5"/>
                  <path d="M22 11 L32 22 L22 33 L12 22 Z" fill="url(#authLogoG)" opacity="0.95"/>
                  <path d="M22 16 L28 22 L22 28 L16 22 Z" fill="white" opacity="0.9"/>
                </svg>
                <span style={{fontWeight:700,fontSize:"17px",background:"linear-gradient(135deg,#38bdf8,#2563eb)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>AI Advisor</span>
              </div>
              <h2>{isLogin ? 'Đăng nhập' : 'Đăng ký'}</h2>
              <p style={{color:"#94a3b8",fontSize:"13px",marginTop:"4px"}}>Đầu tư thông minh với AI</p>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              {!isLogin && (
                <div className="form-field">
                  <label>Há» vÃ  tÃªn</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Nguyá»…n VÄƒn A"
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
                <label>Máº­t kháº©u</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  placeholder="â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢"
                  required
                />
              </div>

              <button type="submit" className="btn-submit">
                {isLogin ? 'ÄÄƒng nháº­p' : 'Táº¡o tÃ i khoáº£n'}
              </button>

              <div className="auth-switch">
                {isLogin ? 'ChÆ°a cÃ³ tÃ i khoáº£n?' : 'ÄÃ£ cÃ³ tÃ i khoáº£n?'}
                <button
                  type="button"
                  onClick={() => setIsLogin(!isLogin)}
                  className="switch-btn"
                >
                  {isLogin ? 'ÄÄƒng kÃ½ ngay' : 'ÄÄƒng nháº­p'}
                </button>
              </div>
            </form>

            <div className="auth-footer">
              <p>Báº±ng viá»‡c Ä‘Äƒng nháº­p, báº¡n Ä‘á»“ng Ã½ vá»›i</p>
              <div className="auth-links">
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(false); setShowTerms(true); }}>Äiá»u khoáº£n dá»‹ch vá»¥</a>
                <span>â€¢</span>
                <a href="#">ChÃ­nh sÃ¡ch báº£o máº­t</a>
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
              <h2>Vá» AI Advisor</h2>
              <p>Há»‡ thá»‘ng há»— trá»£ ra quyáº¿t Ä‘á»‹nh Ä‘áº§u tÆ° thÃ´ng minh</p>
            </div>

            <div className="about-body">
              <div className="about-section">
                <h3>Váº¥n Ä‘á» chÃºng tÃ´i giáº£i quyáº¿t</h3>
                <p>
                  Háº§u háº¿t nhÃ  Ä‘áº§u tÆ° cÃ¡ nhÃ¢n â€“ dÃ¹ cÃ³ kinh nghiá»‡m â€“ Ä‘á»u tá»«ng Ä‘á»‘i máº·t vá»›i nhá»¯ng thÃ¡ch thá»©c sau:
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
                      <strong>HÃ nh Ä‘á»™ng bá»‘c Ä‘á»“ng theo cáº£m xÃºc</strong> (FOMO mua Ä‘á»‰nh, hoáº£ng loáº¡n bÃ¡n Ä‘Ã¡y)
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
                      <strong>KhÃ´ng cÃ³ cÆ¡ cháº¿ cáº£nh bÃ¡o rá»§i ro Ä‘á»§ sá»›m</strong>
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
                      <strong>KhÃ´ng cÃ³ ai hoáº·c cÃ´ng cá»¥ nÃ o "nháº¯c há» dá»«ng láº¡i"</strong> khi hÃ nh vi báº¯t Ä‘áº§u lá»‡ch khá»i káº¿ hoáº¡ch ban Ä‘áº§u
                    </div>
                  </div>
                </div>
              </div>

              <div className="about-section">
                <div className="about-philosophy">
                  <div className="philosophy-icon-large">ðŸ’¡</div>
                  <h3>Triáº¿t lÃ½ cá»‘t lÃµi</h3>
                  <p className="philosophy-quote-modal">
                    "KhÃ´ng thay nhÃ  Ä‘áº§u tÆ° quyáº¿t Ä‘á»‹nh â€“ mÃ  giÃºp nhÃ  Ä‘áº§u tÆ° ra quyáº¿t Ä‘á»‹nh tá»‰nh tÃ¡o hÆ¡n."
                  </p>
                </div>
              </div>

              <div className="about-section">
                <h3>Há»‡ thá»‘ng Ä‘Æ°á»£c thiáº¿t káº¿ xoay quanh 3 trá»¥ cá»™t:</h3>
                <div className="about-pillars">
                  <div className="about-pillar-item">
                    <div className="pillar-number-small">1</div>
                    <div className="pillar-content">
                      <h4>Há»— trá»£ quyáº¿t Ä‘á»‹nh</h4>
                      <p>Cung cáº¥p tÃ­n hiá»‡u, ká»‹ch báº£n vÃ  bá»‘i cáº£nh thá»‹ trÆ°á»ng theo logic nháº¥t quÃ¡n</p>
                    </div>
                  </div>

                  <div className="about-pillar-item">
                    <div className="pillar-number-small">2</div>
                    <div className="pillar-content">
                      <h4>Báº£o vá»‡ rá»§i ro</h4>
                      <p>Cáº£nh bÃ¡o khi xÃ¡c suáº¥t báº¥t lá»£i tÄƒng cao, khi danh má»¥c hoáº·c hÃ nh vi vÆ°á»£t ngÆ°á»¡ng an toÃ n</p>
                    </div>
                  </div>

                  <div className="about-pillar-item">
                    <div className="pillar-number-small">3</div>
                    <div className="pillar-content">
                      <h4>Ká»· luáº­t hÃ³a hÃ nh vi</h4>
                      <p>GiÃºp nhÃ  Ä‘áº§u tÆ° tuÃ¢n thá»§ káº¿ hoáº¡ch Ä‘Ã£ chá»n, thay vÃ¬ pháº£n á»©ng bá»‘c Ä‘á»“ng theo thá»‹ trÆ°á»ng</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="about-section">
                <div className="about-vision">
                  <h3>Táº§m nhÃ¬n dÃ i háº¡n</h3>
                  <p>
                    XÃ¢y dá»±ng má»™t trá»£ lÃ½ tÃ i chÃ­nh AI cÃ¡ nhÃ¢n, Ä‘Ã³ng vai trÃ² nhÆ° <strong>"báº£n Ä‘á»“ Ä‘á»‹nh hÆ°á»›ng"</strong> cho nhÃ  Ä‘áº§u tÆ° â€“ khÃ´ng dáº«n Ä‘Æ°á»ng táº¯t, khÃ´ng há»©a lá»£i nhuáº­n, nhÆ°ng <strong>giÃºp giáº£m sai láº§m nghiÃªm trá»ng vÃ  tÄƒng xÃ¡c suáº¥t tá»“n táº¡i bá»n vá»¯ng trÃªn thá»‹ trÆ°á»ng.</strong>
                  </p>
                </div>
              </div>
            </div>

            <div className="about-actions">
              <button className="btn-understand" onClick={() => { setShowAbout(false); setShowAuth(true); }}>
                Tráº£i nghiá»‡m ngay
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
              <h2>Disclaimer â€“ TuyÃªn bá»‘ miá»…n trá»« trÃ¡ch nhiá»‡m</h2>
              <p>AI Advisor</p>
            </div>

            <div className="terms-body">
              <div className="terms-section">
                <p className="terms-intro">
                  <strong>AI Advisor lÃ  há»‡ thá»‘ng há»— trá»£ ra quyáº¿t Ä‘á»‹nh, khÃ´ng pháº£i dá»‹ch vá»¥ tÆ° váº¥n Ä‘áº§u tÆ°, vÃ  khÃ´ng Ä‘áº¡i diá»‡n cho báº¥t ká»³ tá»• chá»©c mÃ´i giá»›i hay tÃ i chÃ­nh nÃ o.</strong>
                </p>
              </div>

              <div className="terms-section">
                <h3>CÃ¡c ná»™i dung do AI Advisor cung cáº¥p bao gá»“m (nhÆ°ng khÃ´ng giá»›i háº¡n):</h3>
                <ul className="terms-list">
                  <li>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>TÃ­n hiá»‡u mua/bÃ¡n vÃ  cáº£nh bÃ¡o rá»§i ro</span>
                  </li>
                  <li>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>PhÃ¢n tÃ­ch xu hÆ°á»›ng, ká»‹ch báº£n thá»‹ trÆ°á»ng</span>
                  </li>
                  <li>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    <span>Gá»£i Ã½ quáº£n trá»‹ hÃ nh vi vÃ  ká»· luáº­t Ä‘áº§u tÆ°</span>
                  </li>
                </ul>
              </div>

              <div className="terms-section important-notice">
                <div className="notice-icon">âš ï¸</div>
                <div className="notice-content">
                  <h4>LÆ°u Ã½ quan trá»ng</h4>
                  <p>
                    Táº¥t cáº£ cÃ¡c ná»™i dung trÃªn <strong>chá»‰ mang tÃ­nh tham kháº£o</strong> vÃ  há»— trá»£ quÃ¡ trÃ¬nh ra quyáº¿t Ä‘á»‹nh.
                  </p>
                  <p className="highlight">
                    <strong>NgÆ°á»i dÃ¹ng tá»± chá»‹u hoÃ n toÃ n trÃ¡ch nhiá»‡m Ä‘á»‘i vá»›i má»i quyáº¿t Ä‘á»‹nh mua, bÃ¡n, náº¯m giá»¯ tÃ i sáº£n.</strong>
                  </p>
                </div>
              </div>

              <div className="terms-section">
                <p className="terms-footer-text">
                  Báº±ng viá»‡c sá»­ dá»¥ng AI Advisor, báº¡n xÃ¡c nháº­n ráº±ng báº¡n Ä‘Ã£ Ä‘á»c, hiá»ƒu vÃ  Ä‘á»“ng Ã½ vá»›i cÃ¡c Ä‘iá»u khoáº£n miá»…n trá»« trÃ¡ch nhiá»‡m nÃ y.
                </p>
              </div>
            </div>

            <div className="terms-actions">
              <button className="btn-understand" onClick={() => setShowTerms(false)}>
                TÃ´i Ä‘Ã£ hiá»ƒu
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
              <p>Ná»n táº£ng Ä‘áº§u tÆ° chá»©ng khoÃ¡n thÃ´ng minh vá»›i AI</p>
            </div>

            <div className="footer-links">
              <div className="footer-column">
                <h4>Sáº£n pháº©m</h4>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(true); }}>TÃ­n hiá»‡u mua bÃ¡n</a>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(true); }}>Quáº£n trá»‹ danh má»¥c</a>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(true); }}>TÆ° váº¥n AI</a>
              </div>

              <div className="footer-column">
                <h4>CÃ´ng ty</h4>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAbout(true); }}>Vá» chÃºng tÃ´i</a>
                <a href="#">Blog</a>
                <a href="#">LiÃªn há»‡</a>
              </div>

              <div className="footer-column">
                <h4>Há»— trá»£</h4>
                <a href="#">Trung tÃ¢m trá»£ giÃºp</a>
                <a href="#" onClick={(e) => { e.preventDefault(); setShowTerms(true); }}>Äiá»u khoáº£n</a>
                <a href="#">Báº£o máº­t</a>
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <p>Â© 2025 AI Advisor. All rights reserved.</p>
            <p className="disclaimer-small">
              Äáº§u tÆ° chá»©ng khoÃ¡n cÃ³ rá»§i ro. Vui lÃ²ng nghiÃªn cá»©u ká»¹ trÆ°á»›c khi quyáº¿t Ä‘á»‹nh.
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
          content: "â†’";
          position: absolute;
          left: 0;
          color: #3b82f6;
          font-weight: bold;
        }

        .strategy-content strong {
          color: #10b981;
        }

        @media (max-width: 768px) {
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
    </div>
  )
}
