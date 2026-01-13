import React, { useState, useEffect } from 'react';
import { TrendingUp, Shield, Brain, ArrowRight, Clock, Target, TrendingDown } from 'lucide-react';

const API_BASE = 'https://ai-advisor1-backend.onrender.com/api';

export default function LandingPage({ onNavigate }) {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSignalHistory();
  }, []);

  const fetchSignalHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/signals`);
      const data = await response.json();
      
      if (data.success) {
        // Get latest 6 signals for display
        const latestSignals = data.signals.slice(0, 6);
        setSignals(latestSignals);
      }
    } catch (error) {
      console.error('Error fetching signals:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      background: 'linear-gradient(180deg, #0a0e27 0%, #1a1f3a 100%)',
      minHeight: '100vh',
      color: '#fff'
    }}>
      {/* Hero Section */}
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto', 
        padding: '80px 20px 60px',
        textAlign: 'center'
      }}>
        <div style={{
          display: 'inline-block',
          padding: '8px 20px',
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '20px',
          marginBottom: '30px',
          fontSize: '14px',
          color: '#60a5fa'
        }}>
          🤖 Powered by AI • Trusted by Investors
        </div>

        <h1 style={{ 
          fontSize: '56px', 
          fontWeight: 'bold',
          marginBottom: '20px',
          lineHeight: '1.2',
          background: 'linear-gradient(135deg, #fff 0%, #60a5fa 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          AI Advisor
        </h1>
        
        <p style={{ 
          fontSize: '24px', 
          color: '#94a3b8',
          marginBottom: '40px',
          maxWidth: '700px',
          margin: '0 auto 40px'
        }}>
          Tín hiệu giao dịch thông minh • Phân tích AI real-time • Kiểm soát tâm lý đầu tư
        </p>

        <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', marginBottom: '60px' }}>
          <button
            onClick={() => onNavigate('signals')}
            style={{
              padding: '16px 32px',
              background: '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            Xem tín hiệu <ArrowRight size={20} />
          </button>
          
          <button
            onClick={() => onNavigate('portfolio')}
            style={{
              padding: '16px 32px',
              background: 'transparent',
              color: '#fff',
              border: '2px solid #334155',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.background = '#334155';
              e.target.style.borderColor = '#475569';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
              e.target.style.borderColor = '#334155';
            }}
          >
            Quản trị danh mục
          </button>
        </div>

        {/* Stats */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '20px',
          maxWidth: '900px',
          margin: '0 auto'
        }}>
          <div style={{
            background: 'rgba(59, 130, 246, 0.05)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            padding: '24px',
            borderRadius: '12px'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#3b82f6', marginBottom: '8px' }}>
              343
            </div>
            <div style={{ fontSize: '14px', color: '#94a3b8' }}>
              Cổ phiếu theo dõi
            </div>
          </div>

          <div style={{
            background: 'rgba(16, 185, 129, 0.05)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            padding: '24px',
            borderRadius: '12px'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#10b981', marginBottom: '8px' }}>
              21.5%
            </div>
            <div style={{ fontSize: '14px', color: '#94a3b8' }}>
              Tỷ lệ thành công
            </div>
          </div>

          <div style={{
            background: 'rgba(139, 92, 246, 0.05)',
            border: '1px solid rgba(139, 92, 246, 0.2)',
            padding: '24px',
            borderRadius: '12px'
          }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#8b5cf6', marginBottom: '8px' }}>
              AI
            </div>
            <div style={{ fontSize: '14px', color: '#94a3b8' }}>
              Phân tích thông minh
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto', 
        padding: '60px 20px'
      }}>
        <h2 style={{ 
          fontSize: '36px', 
          fontWeight: 'bold',
          textAlign: 'center',
          marginBottom: '50px'
        }}>
          Tính Năng Nổi Bật
        </h2>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '30px'
        }}>
          {/* Feature 1 */}
          <div style={{
            background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            padding: '30px',
            borderRadius: '16px',
            border: '1px solid #334155',
            cursor: 'pointer',
            transition: 'all 0.3s'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
            e.currentTarget.style.borderColor = '#3b82f6';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.borderColor = '#334155';
          }}
          onClick={() => onNavigate('signals')}
          >
            <div style={{
              width: '60px',
              height: '60px',
              background: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px'
            }}>
              <TrendingUp size={30} color="#3b82f6" />
            </div>
            <h3 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '12px' }}>
              Tín Hiệu Giao Dịch
            </h3>
            <p style={{ color: '#94a3b8', lineHeight: '1.6', marginBottom: '15px' }}>
              Tín hiệu MUA/BÁN được tạo tự động từ hệ thống phân tích AI. 
              Theo dõi 343 cổ phiếu với độ chính xác 21.5%.
            </p>
            <div style={{ color: '#3b82f6', fontSize: '14px', fontWeight: '600' }}>
              Xem tín hiệu →
            </div>
          </div>

          {/* Feature 2 */}
          <div style={{
            background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            padding: '30px',
            borderRadius: '16px',
            border: '1px solid #334155',
            cursor: 'pointer',
            transition: 'all 0.3s'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
            e.currentTarget.style.borderColor = '#10b981';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.borderColor = '#334155';
          }}
          >
            <div style={{
              width: '60px',
              height: '60px',
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px'
            }}>
              <Shield size={30} color="#10b981" />
            </div>
            <h3 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '12px' }}>
              AI Risk Shield
            </h3>
            <p style={{ color: '#94a3b8', lineHeight: '1.6', marginBottom: '15px' }}>
              Phân tích rủi ro real-time, cảnh báo xu hướng thị trường, 
              bảo vệ vốn đầu tư của bạn.
            </p>
            <div style={{ 
              display: 'inline-block',
              padding: '4px 12px',
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '12px',
              fontSize: '12px',
              color: '#f59e0b'
            }}>
              VIP Feature
            </div>
          </div>

          {/* Feature 3 */}
          <div style={{
            background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            padding: '30px',
            borderRadius: '16px',
            border: '1px solid #334155',
            cursor: 'pointer',
            transition: 'all 0.3s'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
            e.currentTarget.style.borderColor = '#8b5cf6';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.borderColor = '#334155';
          }}
          onClick={() => onNavigate('portfolio')}
          >
            <div style={{
              width: '60px',
              height: '60px',
              background: 'rgba(139, 92, 246, 0.1)',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px'
            }}>
              <Brain size={30} color="#8b5cf6" />
            </div>
            <h3 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '12px' }}>
              AI Discipline Coach
            </h3>
            <p style={{ color: '#94a3b8', lineHeight: '1.6', marginBottom: '15px' }}>
              Coaching tâm lý đầu tư, kiểm soát FOMO và hoảng sợ. 
              Giúp bạn đưa ra quyết định sáng suốt.
            </p>
            <div style={{ color: '#8b5cf6', fontSize: '14px', fontWeight: '600' }}>
              Trò chuyện với AI →
            </div>
          </div>
        </div>
      </div>

      {/* Signal History Section */}
      <div style={{ 
        maxWidth: '1200px', 
        margin: '0 auto', 
        padding: '60px 20px'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '30px'
        }}>
          <div>
            <h2 style={{ 
              fontSize: '36px', 
              fontWeight: 'bold',
              marginBottom: '10px'
            }}>
              Lịch Sử Khuyến Nghị
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '16px' }}>
              Các tín hiệu giao dịch gần đây từ hệ thống AI
            </p>
          </div>
          
          <button
            onClick={() => onNavigate('signals')}
            style={{
              padding: '12px 24px',
              background: 'transparent',
              color: '#3b82f6',
              border: '1px solid #3b82f6',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            Xem tất cả <ArrowRight size={16} />
          </button>
        </div>

        {loading ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '60px 20px',
            color: '#64748b'
          }}>
            <div style={{ 
              fontSize: '16px',
              marginBottom: '10px'
            }}>
              ⏳ Đang tải tín hiệu...
            </div>
          </div>
        ) : signals.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '60px 20px',
            color: '#64748b'
          }}>
            <div style={{ 
              fontSize: '48px',
              marginBottom: '20px'
            }}>
              📊
            </div>
            <div style={{ 
              fontSize: '18px',
              marginBottom: '10px',
              color: '#94a3b8'
            }}>
              Chưa có tín hiệu nào
            </div>
            <div style={{ fontSize: '14px' }}>
              Hệ thống sẽ tự động quét và tạo tín hiệu mới
            </div>
          </div>
        ) : (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '20px'
          }}>
            {signals.map((signal) => {
              const isProfit = signal.entry_price < signal.take_profit;
              const potentialReturn = ((signal.take_profit - signal.entry_price) / signal.entry_price * 100).toFixed(1);
              const risk = ((signal.entry_price - signal.stop_loss) / signal.entry_price * 100).toFixed(1);
              
              return (
                <div
                  key={signal.id}
                  style={{
                    background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                    padding: '24px',
                    borderRadius: '12px',
                    border: '1px solid #334155',
                    cursor: 'pointer',
                    transition: 'all 0.3s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.transform = 'translateY(-5px)';
                    e.currentTarget.style.borderColor = signal.action === 'BUY' ? '#10b981' : '#ef4444';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.borderColor = '#334155';
                  }}
                  onClick={() => onNavigate('signals')}
                >
                  {/* Header */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'flex-start',
                    marginBottom: '16px'
                  }}>
                    <div>
                      <div style={{ 
                        fontSize: '24px', 
                        fontWeight: 'bold',
                        color: '#fff',
                        marginBottom: '4px'
                      }}>
                        {signal.ticker || signal.code}
                      </div>
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#64748b'
                      }}>
                        {signal.stock_type || 'Blue Chip'}
                      </div>
                    </div>
                    
                    <div style={{
                      display: 'inline-block',
                      padding: '6px 14px',
                      background: signal.action === 'BUY' 
                        ? 'rgba(16, 185, 129, 0.15)' 
                        : 'rgba(239, 68, 68, 0.15)',
                      border: `1px solid ${signal.action === 'BUY' ? '#10b981' : '#ef4444'}`,
                      borderRadius: '20px',
                      fontSize: '13px',
                      fontWeight: '600',
                      color: signal.action === 'BUY' ? '#10b981' : '#ef4444'
                    }}>
                      {signal.action === 'BUY' ? '🟢 MUA' : '🔴 BÁN'}
                    </div>
                  </div>

                  {/* Price Info */}
                  <div style={{ 
                    background: 'rgba(15, 23, 42, 0.5)',
                    padding: '16px',
                    borderRadius: '8px',
                    marginBottom: '16px'
                  }}>
                    <div style={{ 
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '12px'
                    }}>
                      <div>
                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>
                          Giá vào
                        </div>
                        <div style={{ fontSize: '16px', fontWeight: '600', color: '#fff' }}>
                          {signal.entry_price.toLocaleString('vi-VN')}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>
                          Mục tiêu
                        </div>
                        <div style={{ fontSize: '16px', fontWeight: '600', color: '#10b981' }}>
                          {signal.take_profit.toLocaleString('vi-VN')}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div style={{ 
                    display: 'flex',
                    gap: '12px',
                    marginBottom: '16px'
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '6px',
                        marginBottom: '4px'
                      }}>
                        <Target size={14} color="#10b981" />
                        <span style={{ fontSize: '11px', color: '#64748b' }}>Lợi nhuận</span>
                      </div>
                      <div style={{ 
                        fontSize: '16px', 
                        fontWeight: '600',
                        color: '#10b981'
                      }}>
                        +{potentialReturn}%
                      </div>
                    </div>
                    
                    <div style={{ flex: 1 }}>
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '6px',
                        marginBottom: '4px'
                      }}>
                        <TrendingDown size={14} color="#ef4444" />
                        <span style={{ fontSize: '11px', color: '#64748b' }}>Rủi ro</span>
                      </div>
                      <div style={{ 
                        fontSize: '16px', 
                        fontWeight: '600',
                        color: '#ef4444'
                      }}>
                        -{risk}%
                      </div>
                    </div>

                    {signal.strength && (
                      <div style={{ flex: 1 }}>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '6px',
                          marginBottom: '4px'
                        }}>
                          <div style={{ 
                            width: '14px', 
                            height: '14px', 
                            background: '#3b82f6',
                            borderRadius: '50%'
                          }} />
                          <span style={{ fontSize: '11px', color: '#64748b' }}>Score</span>
                        </div>
                        <div style={{ 
                          fontSize: '16px', 
                          fontWeight: '600',
                          color: '#3b82f6'
                        }}>
                          {signal.strength || 75}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer */}
                  <div style={{ 
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    paddingTop: '16px',
                    borderTop: '1px solid #334155'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '6px',
                      fontSize: '12px',
                      color: '#64748b'
                    }}>
                      <Clock size={14} />
                      {signal.date || new Date(signal.created_at).toLocaleDateString('vi-VN')}
                    </div>
                    
                    <div style={{ 
                      fontSize: '12px',
                      color: '#3b82f6',
                      fontWeight: '600'
                    }}>
                      Xem chi tiết →
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {signals.length > 0 && (
          <div style={{ 
            textAlign: 'center',
            marginTop: '40px'
          }}>
            <button
              onClick={() => onNavigate('signals')}
              style={{
                padding: '14px 32px',
                background: 'transparent',
                color: '#3b82f6',
                border: '2px solid #3b82f6',
                borderRadius: '12px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => {
                e.target.style.background = '#3b82f6';
                e.target.style.color = '#fff';
              }}
              onMouseOut={(e) => {
                e.target.style.background = 'transparent';
                e.target.style.color = '#3b82f6';
              }}
            >
              Xem tất cả {signals.length > 6 ? `${signals.length - 6}+ tín hiệu khác` : 'tín hiệu'} <ArrowRight size={20} />
            </button>
          </div>
        )}
      </div>

      {/* CTA Section */}
      <div style={{ 
        maxWidth: '1200px', 
        margin: '60px auto',
        padding: '0 20px'
      }}>
        <div style={{
          background: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
          padding: '60px 40px',
          borderRadius: '20px',
          textAlign: 'center'
        }}>
          <h2 style={{ 
            fontSize: '36px', 
            fontWeight: 'bold',
            marginBottom: '20px'
          }}>
            Sẵn sàng đầu tư thông minh hơn?
          </h2>
          <p style={{ 
            fontSize: '18px',
            color: 'rgba(255, 255, 255, 0.9)',
            marginBottom: '30px',
            maxWidth: '600px',
            margin: '0 auto 30px'
          }}>
            Bắt đầu ngay với AI Advisor - công cụ hỗ trợ quyết định đầu tư được tin dùng
          </p>
          <button
            onClick={() => onNavigate('signals')}
            style={{
              padding: '16px 40px',
              background: '#fff',
              color: '#1e40af',
              border: 'none',
              borderRadius: '12px',
              fontSize: '18px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'transform 0.2s'
            }}
            onMouseOver={(e) => e.target.style.transform = 'scale(1.05)'}
            onMouseOut={(e) => e.target.style.transform = 'scale(1)'}
          >
            Bắt đầu ngay - Miễn phí
          </button>
        </div>
      </div>

      {/* Footer */}
      <div style={{ 
        borderTop: '1px solid #334155',
        padding: '40px 20px',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ 
            fontSize: '24px', 
            fontWeight: 'bold',
            marginBottom: '10px',
            color: '#3b82f6'
          }}>
            AI Advisor
          </div>
          <p style={{ 
            color: '#64748b',
            fontSize: '14px',
            marginBottom: '20px'
          }}>
            Tín hiệu giao dịch thông minh • Phân tích AI • Kiểm soát tâm lý
          </p>
          <div style={{ 
            color: '#64748b',
            fontSize: '12px'
          }}>
            © 2026 AI Advisor. All rights reserved.
          </div>
        </div>
      </div>
    </div>
  );
}
