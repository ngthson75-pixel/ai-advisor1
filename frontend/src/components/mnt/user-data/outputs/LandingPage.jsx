import { useState } from 'react'

export default function LandingPage({ onLogin }) {
  const [showAuth, setShowAuth] = useState(false)
  const [showTerms, setShowTerms] = useState(false)
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

      {/* About Us Section */}
      <section className="about-us" id="about">
        <div className="container">
          <div className="section-header">
            <h2>Về chúng tôi</h2>
            <p>Sứ mệnh và triết lý của AI Advisor</p>
          </div>

          <div className="about-content">
            <div className="about-story">
              <div className="story-intro">
                <p className="lead-text">
                  Chúng tôi là một nhóm những người đã trực tiếp trải qua nhiều chu kỳ thị trường, chứng kiến cùng một thực tế lặp đi lặp lại: <strong>đa số nhà đầu tư cá nhân không thua vì thiếu thông tin, mà thua vì thiếu kỷ luật, thiếu hệ thống và không có "lan can bảo vệ" cho hành vi của chính mình.</strong>
                </p>
              </div>

              <div className="problem-section">
                <h3>Thực trạng thị trường</h3>
                <p>
                  Thị trường luôn đầy ắp dữ liệu, tin tức, khuyến nghị. Nhưng trong những thời điểm quan trọng nhất – khi cần ra quyết định mua, bán, giữ hay đứng ngoài – nhà đầu tư thường:
                </p>
                
                <div className="problem-list">
                  <div className="problem-item">
                    <div className="problem-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <div className="problem-text">
                      <strong>Bị cảm xúc chi phối</strong>
                      <p>FOMO, hoảng loạn, tiếc nuối làm lu mờ lý trí</p>
                    </div>
                  </div>

                  <div className="problem-item">
                    <div className="problem-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <div className="problem-text">
                      <strong>Thiếu quy trình nhất quán</strong>
                      <p>Không có hệ thống ra quyết định rõ ràng</p>
                    </div>
                  </div>

                  <div className="problem-item">
                    <div className="problem-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <div className="problem-text">
                      <strong>Cảnh báo rủi ro muộn</strong>
                      <p>Không có cơ chế cảnh báo đủ sớm</p>
                    </div>
                  </div>

                  <div className="problem-item">
                    <div className="problem-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                    </div>
                    <div className="problem-text">
                      <strong>Thiếu "phanh an toàn"</strong>
                      <p>Không có ai nhắc dừng lại khi hành vi lệch kế hoạch</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="solution-section">
                <div className="philosophy-box">
                  <div className="philosophy-icon">💡</div>
                  <h3>Triết lý cốt lõi</h3>
                  <p className="philosophy-quote">
                    "Không thay nhà đầu tư quyết định – mà giúp nhà đầu tư ra quyết định tỉnh táo hơn."
                  </p>
                </div>

                <h3>3 Trụ cột hệ thống</h3>
                <div className="pillars-grid">
                  <div className="pillar-card">
                    <div className="pillar-number">1</div>
                    <h4>Hỗ trợ quyết định</h4>
                    <p>Cung cấp tín hiệu, kịch bản và bối cảnh thị trường theo logic nhất quán</p>
                  </div>

                  <div className="pillar-card">
                    <div className="pillar-number">2</div>
                    <h4>Bảo vệ rủi ro</h4>
                    <p>Cảnh báo khi xác suất bất lợi tăng cao, khi danh mục hoặc hành vi vượt ngưỡng an toàn</p>
                  </div>

                  <div className="pillar-card">
                    <div className="pillar-number">3</div>
                    <h4>Kỷ luật hóa hành vi</h4>
                    <p>Giúp nhà đầu tư tuân thủ kế hoạch đã chọn, thay vì phản ứng bốc đồng theo thị trường</p>
                  </div>
                </div>
              </div>

              <div className="vision-section">
                <h3>Tầm nhìn dài hạn</h3>
                <p className="vision-text">
                  Xây dựng một trợ lý tài chính AI cá nhân, đóng vai trò như <strong>"bản đồ định hướng"</strong> cho nhà đầu tư – không dẫn đường tắt, không hứa lợi nhuận, nhưng <strong>giúp giảm sai lầm nghiêm trọng và tăng xác suất tồn tại bền vững trên thị trường.</strong>
                </p>
              </div>
            </div>

            <div className="about-cta">
              <button className="btn-primary-large" onClick={() => setShowAuth(true)}>
                Trải nghiệm ngay
              </button>
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
                <a href="#" onClick={(e) => { e.preventDefault(); setShowAuth(false); setShowTerms(true); }}>Điều khoản dịch vụ</a>
                <span>•</span>
                <a href="#">Chính sách bảo mật</a>
              </div>
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
                <a href="#" onClick={(e) => { e.preventDefault(); scrollToSection('about'); }}>Về chúng tôi</a>
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
    </div>
  )
}
