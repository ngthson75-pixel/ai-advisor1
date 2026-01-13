import { useState, useEffect } from 'react'

const API_BASE = 'https://ai-advisor1-backend.onrender.com/api'

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

  // Historical signals from 06/01/2026
  const historicalSignals = [
    {
      id: 'hist-1',
      ticker: 'VNM',
      entryPrice: 60700,
      stopLoss: 57665,  // -5%
      takeProfit: 65556, // +8%
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026'
    },
    {
      id: 'hist-2',
      ticker: 'BID',
      entryPrice: 38750,
      stopLoss: 36812,  // -5%
      takeProfit: 41850, // +8%
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026'
    },
    {
      id: 'hist-3',
      ticker: 'CTG',
      entryPrice: 36120,
      stopLoss: 34314,  // -5%
      takeProfit: 39010, // +8%
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026'
    },
    {
      id: 'hist-4',
      ticker: 'POW',
      entryPrice: 12750,
      stopLoss: 12112,  // -5%
      takeProfit: 13770, // +8%
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026'
    },
    {
      id: 'hist-5',
      ticker: 'SAB',
      entryPrice: 45700,
      stopLoss: 43415,  // -5%
      takeProfit: 49356, // +8%
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026'
    },
    {
      id: 'hist-6',
      ticker: 'HNG',
      entryPrice: 6300,
      stopLoss: 5985,   // -5%
      takeProfit: 6804,  // +8%
      score: 75,
      type: 'Blue Chip',
      date: '06/01/2026'
    }
  ]

  useEffect(() => {
    fetchRecommendations()
  }, [])

  const fetchRecommendations = async () => {
    try {
      const response = await fetch(`${API_BASE}/signals`)
      const data = await response.json()
      
      if (data.success && data.signals) {
        // Map API signals to table format
        const apiSignals = data.signals.slice(0, 10).map((signal, index) => ({
          id: signal.id || `api-${index + 1}`,
          ticker: signal.ticker || signal.code,
          entryPrice: signal.entry_price,
          stopLoss: signal.stop_loss,
          takeProfit: signal.take_profit,
          score: signal.strength || 75,
          type: signal.stock_type || 'Blue Chip',
          date: signal.date || new Date(signal.created_at).toLocaleDateString('vi-VN')
        }))
        
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
                Đầu tư thông minh với
                <span className="gradient-text"> AI Advisor</span>
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
                <button className="btn-primary-large" onClick={() => setShowAuth(true)}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
                    <polyline points="10 17 15 12 10 7"/>
                    <line x1="15" y1="12" x2="3" y2="12"/>
                  </svg>
                  Bắt đầu ngay - Miễn phí
                </button>
                <button className="btn-secondary-large" onClick={() => scrollToSection('showcase')}>
                  Xem lịch sử khuyến nghị
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
                  <div className="preview-title">AI Advisor Dashboard</div>
                </div>
                <div className="preview-content">
                  <div className="preview-card">
                    <div className="preview-card-header">
                      <span className="preview-badge buy">MUA</span>
                      <span className="preview-ticker">VCB</span>
                    </div>
                    <div className="preview-price">88,500</div>
                    <div className="preview-target">Target: 95,000 (+7.3%)</div>
                  </div>
                  <div className="preview-card">
                    <div className="preview-card-header">
                      <span className="preview-badge buy">MUA</span>
                      <span className="preview-ticker">MBB</span>
                    </div>
                    <div className="preview-price">23,800</div>
                    <div className="preview-target">Target: 26,000 (+9.2%)</div>
                  </div>
                  <div className="preview-stats">
                    <div>📊 15 tín hiệu mới</div>
                    <div>✅ 78.5% thành công</div>
                  </div>
                </div>
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

      {/* Recommendations Table */}
      <section className="showcase" id="showcase">
        <div className="container">
          <div className="section-header">
            <h2>Lịch sử khuyến nghị</h2>
            <p>Các tín hiệu đã thành công trong thời gian gần đây</p>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <div style={{ fontSize: '16px' }}>⏳ Đang tải tín hiệu...</div>
            </div>
          ) : recommendations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
              <div style={{ fontSize: '18px', marginBottom: '10px' }}>Chưa có tín hiệu nào</div>
              <div style={{ fontSize: '14px' }}>Hệ thống sẽ tự động tạo tín hiệu mới</div>
            </div>
          ) : (
            <div className="signals-table-container">
              <table className="signals-table">
                <thead>
                  <tr>
                    <th>MÃ CK</th>
                    <th>GIÁ VÀO</th>
                    <th>STOP LOSS</th>
                    <th>TAKE PROFIT</th>
                    <th>SCORE</th>
                    <th>LOẠI</th>
                    <th>NGÀY</th>
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
          )}

          <div className="showcase-cta">
            <button className="btn-primary-large" onClick={() => setShowAuth(true)}>
              Truy cập tín hiệu mới nhất
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
              <h2>{isLogin ? 'Đăng nhập' : 'Đăng ký'}</h2>
              <p>{isLogin ? 'Chào mừng trở lại!' : 'Tạo tài khoản miễn phí'}</p>
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
                  onClick={() => setIsLogin(!isLogin)}
                  className="switch-btn"
                >
                  {isLogin ? 'Đăng ký ngay' : 'Đăng nhập'}
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
        }
      `}</style>
    </div>
  )
}
