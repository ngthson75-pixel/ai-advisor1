import { useState } from 'react'

export default function LandingPage({ onLogin }) {
  const [showAuth, setShowAuth] = useState(false)
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  })

  // Mock recommendations history
  const recommendations = [
    {
      id: 1,
      ticker: 'VCB',
      action: 'MUA',
      entryPrice: 88500,
      targetPrice: 95000,
      actualPrice: 94200,
      result: '+6.4%',
      date: '2024-12-15',
      status: 'success'
    },
    {
      id: 2,
      ticker: 'MBB',
      action: 'MUA',
      entryPrice: 23800,
      targetPrice: 26000,
      actualPrice: 25800,
      result: '+8.4%',
      date: '2024-12-10',
      status: 'success'
    },
    {
      id: 3,
      ticker: 'FPT',
      action: 'BÁN',
      entryPrice: 125000,
      targetPrice: 118000,
      actualPrice: 119500,
      result: '+4.4%',
      date: '2024-12-05',
      status: 'success'
    },
    {
      id: 4,
      ticker: 'HPG',
      action: 'MUA',
      entryPrice: 25200,
      targetPrice: 27500,
      actualPrice: 27100,
      result: '+7.5%',
      date: '2024-11-28',
      status: 'success'
    },
    {
      id: 5,
      ticker: 'TCB',
      action: 'MUA',
      entryPrice: 24500,
      targetPrice: 26800,
      actualPrice: 26200,
      result: '+6.9%',
      date: '2024-11-20',
      status: 'success'
    },
    {
      id: 6,
      ticker: 'VNM',
      action: 'BÁN',
      entryPrice: 75000,
      targetPrice: 71000,
      actualPrice: 71800,
      result: '+4.3%',
      date: '2024-11-15',
      status: 'success'
    }
  ]

  const stats = {
    totalSignals: 127,
    successRate: 78.5,
    avgReturn: 6.8,
    activeUsers: 1250
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Mock authentication - In production, call API
    const userData = {
      email: formData.email,
      name: formData.name || formData.email.split('@')[0],
      loginTime: new Date().toISOString()
    }
    
    // Store in localStorage
    localStorage.setItem('user', JSON.stringify(userData))
    
    // Notify parent
    onLogin(userData)
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN').format(value)
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
                  <div className="stat-number">{stats.activeUsers.toLocaleString()}</div>
                  <div className="stat-label">Người dùng</div>
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
                <button className="btn-secondary-large" onClick={() => {
                  document.getElementById('showcase').scrollIntoView({ behavior: 'smooth' })
                }}>
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
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                </svg>
              </div>
              <h3>Tín hiệu chính xác</h3>
              <p>AI phân tích hàng nghìn điểm dữ liệu để đưa ra tín hiệu mua bán tối ưu với độ chính xác cao</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>
              <h3>Quản lý rủi ro</h3>
              <p>Phân tích danh mục tự động, cảnh báo rủi ro, và đề xuất chiến lược phân bổ vốn hợp lý</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                </svg>
              </div>
              <h3>Tư vấn AI 24/7</h3>
              <p>Trợ lý AI sẵn sàng giải đáp mọi thắc mắc về thị trường, chiến lược và danh mục đầu tư</p>
            </div>
          </div>
        </div>
      </section>

      {/* Showcase Recommendations */}
      <section className="showcase" id="showcase">
        <div className="container">
          <div className="section-header">
            <h2>Lịch sử khuyến nghị</h2>
            <p>Các tín hiệu đã thành công trong thời gian gần đây</p>
          </div>

          <div className="recommendations-grid">
            {recommendations.map((rec) => (
              <div key={rec.id} className="recommendation-card">
                <div className="rec-header">
                  <div className="rec-info">
                    <span className={`rec-badge ${rec.action.toLowerCase()}`}>
                      {rec.action}
                    </span>
                    <span className="rec-ticker">{rec.ticker}</span>
                  </div>
                  <div className="rec-date">{rec.date}</div>
                </div>

                <div className="rec-body">
                  <div className="rec-prices">
                    <div className="price-item">
                      <label>Giá {rec.action === 'MUA' ? 'mua' : 'bán'}</label>
                      <div className="price">{formatCurrency(rec.entryPrice)}</div>
                    </div>
                    <div className="price-arrow">→</div>
                    <div className="price-item">
                      <label>Mục tiêu</label>
                      <div className="price">{formatCurrency(rec.targetPrice)}</div>
                    </div>
                  </div>

                  <div className="rec-result">
                    <div className="result-label">Kết quả thực tế:</div>
                    <div className="result-value">
                      {formatCurrency(rec.actualPrice)}
                      <span className="result-percent success">{rec.result}</span>
                    </div>
                  </div>
                </div>

                <div className="rec-footer">
                  <span className="status-badge success">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    Thành công
                  </span>
                </div>
              </div>
            ))}
          </div>

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
                <a href="#">Điều khoản dịch vụ</a>
                <span>•</span>
                <a href="#">Chính sách bảo mật</a>
              </div>
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
                <a href="#">Tín hiệu mua bán</a>
                <a href="#">Quản trị danh mục</a>
                <a href="#">Tư vấn AI</a>
              </div>

              <div className="footer-column">
                <h4>Công ty</h4>
                <a href="#">Về chúng tôi</a>
                <a href="#">Blog</a>
                <a href="#">Liên hệ</a>
              </div>

              <div className="footer-column">
                <h4>Hỗ trợ</h4>
                <a href="#">Trung tâm trợ giúp</a>
                <a href="#">Điều khoản</a>
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
    </div>
  )
}
