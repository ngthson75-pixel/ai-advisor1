import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';

const API_BASE = 'https://ai-advisor1-backend.onrender.com/api';

export default function SignalsModule() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [activeTab, setActiveTab] = useState('buy'); // NEW: Tab state

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE}/signals`);
      const data = await response.json();
      
      if (data.success) {
        setSignals(data.signals || []);
      } else {
        setError('Không thể tải tín hiệu');
      }
    } catch (err) {
      setError('Lỗi kết nối: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const triggerScan = async () => {
    try {
      setScanning(true);
      const response = await fetch(`${API_BASE}/scan`, { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        alert('Đã bắt đầu quét! Vui lòng đợi 2-3 phút và refresh lại.');
        setTimeout(fetchSignals, 180000); // Auto refresh sau 3 phút
      }
    } catch (err) {
      alert('Lỗi khi quét: ' + err.message);
    } finally {
      setScanning(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);

  // Filter signals by tab
  const buySignals = signals.filter(s => s.action === 'BUY' || !s.action);
  const sellSignals = signals.filter(s => s.action === 'SELL');
  const displaySignals = activeTab === 'buy' ? buySignals : sellSignals;

  // ============================================================================
  // NEW: Helper function - Format exit reason for SELL signals
  // ============================================================================
  const getExitReasonDisplay = (strategy) => {
    if (strategy === 'STOP_LOSS') {
      return {
        text: 'Cắt lỗ (SL)',
        icon: '🔴',
        color: '#ef4444',
        bgColor: '#fee2e2'
      };
    } else if (strategy === 'TAKE_PROFIT') {
      return {
        text: 'Chốt lời (TP)',
        icon: '🟢',
        color: '#10b981',
        bgColor: '#dcfce7'
      };
    }
    return {
      text: 'Khác',
      icon: '⚪',
      color: '#6b7280',
      bgColor: '#f3f4f6'
    };
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <RefreshCw className="spin" size={40} style={{ color: '#3b82f6' }} />
        <p style={{ marginTop: '20px', color: '#94a3b8' }}>Đang tải tín hiệu...</p>
      </div>
    );
  }

  return (
    <div className="signals-module">
      {/* Header */}
      <div className="signals-header">
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <TrendingUp size={28} style={{ color: '#3b82f6' }} />
            Tín Hiệu Giao Dịch
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '14px' }}>
            Tín hiệu được tạo tự động từ hệ thống phân tích AI
          </p>
        </div>

        <button 
          onClick={fetchSignals}
          disabled={scanning}
          style={{
            padding: '10px 20px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <RefreshCw size={16} className={scanning ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* NEW: Tabs */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveTab('buy')}
          style={{
            padding: '12px 24px',
            backgroundColor: activeTab === 'buy' ? '#10b981' : '#334155',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s'
          }}
        >
          📈 Tín hiệu MUA ({buySignals.length})
        </button>
        
        <button
          onClick={() => setActiveTab('sell')}
          style={{
            padding: '12px 24px',
            backgroundColor: activeTab === 'sell' ? '#ef4444' : '#334155',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s'
          }}
        >
          📉 Tín hiệu BÁN ({sellSignals.length})
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          padding: '15px',
          background: '#fee',
          border: '1px solid #fcc',
          borderRadius: '8px',
          marginBottom: '20px',
          color: '#c33'
        }}>
          <AlertCircle size={20} style={{ marginRight: '10px' }} />
          {error}
        </div>
      )}

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#10b981' }}>
            {buySignals.length}
          </div>
          <div className="stat-label">Tín hiệu MUA</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#ef4444' }}>
            {sellSignals.length}
          </div>
          <div className="stat-label">Tín hiệu BÁN</div>
        </div>

        <div className="stat-card">
          <div className="stat-value" style={{ color: '#3b82f6' }}>
            {buySignals.filter(s => (s.strength || 0) >= 70).length}
          </div>
          <div className="stat-label">Tín hiệu mạnh (&gt;70%)</div>
        </div>

        <div className="stat-card">
          <div className="stat-value" style={{ color: '#f59e0b' }}>
            {signals.length}
          </div>
          <div className="stat-label">Tổng tín hiệu</div>
        </div>
      </div>

      {/* Signals Table */}
      {displaySignals.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
          background: '#1e293b',
          borderRadius: '12px',
          border: '1px dashed #334155'
        }}>
          <AlertCircle size={48} style={{ color: '#64748b', marginBottom: '15px' }} />
          <h3 style={{ color: '#94a3b8', marginBottom: '10px' }}>
            Chưa có tín hiệu {activeTab === 'buy' ? 'MUA' : 'BÁN'}
          </h3>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '20px' }}>
            Hệ thống sẽ tự động quét và cập nhật tín hiệu mới
          </p>
          <button
            onClick={triggerScan}
            disabled={scanning}
            style={{
              padding: '12px 24px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: scanning ? 'not-allowed' : 'pointer',
              opacity: scanning ? 0.6 : 1
            }}
          >
            {scanning ? 'Đang quét...' : 'Quét ngay'}
          </button>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="signals-table">
            <thead>
              <tr>
                <th>Mã CK</th>
                <th>Giá vào</th>
                {/* UPDATED: Different headers for BUY vs SELL */}
                {activeTab === 'buy' ? (
                  <>
                    <th>Stop Loss</th>
                    <th>Take Profit</th>
                  </>
                ) : (
                  <>
                    <th>Giá ra</th>
                    <th>Lý do bán</th>
                  </>
                )}
                <th>Score</th>
                <th>Ngày</th>
              </tr>
            </thead>
            <tbody>
              {displaySignals.map((signal, idx) => {
                // Calculate exit reason for SELL signals
                const exitReason = getExitReasonDisplay(signal.strategy);
                const exitPrice = signal.strategy === 'STOP_LOSS' 
                  ? signal.stop_loss 
                  : signal.take_profit;

                return (
                  <tr key={signal.id || idx}>
                    {/* Ticker */}
                    <td>
                      <strong style={{ 
                        color: signal.action === 'SELL' ? '#ef4444' : '#3b82f6', 
                        fontSize: '16px' 
                      }}>
                        {signal.ticker || signal.code}
                      </strong>
                    </td>

                    {/* Entry Price */}
                    <td>{signal.entry_price?.toLocaleString()}</td>

                    {/* UPDATED: Different cells for BUY vs SELL */}
                    {activeTab === 'buy' ? (
                      <>
                        {/* BUY: Show Stop Loss */}
                        <td style={{ color: '#ef4444' }}>
                          {signal.stop_loss?.toLocaleString()}
                        </td>
                        {/* BUY: Show Take Profit */}
                        <td style={{ color: '#10b981' }}>
                          {signal.take_profit?.toLocaleString()}
                        </td>
                      </>
                    ) : (
                      <>
                        {/* SELL: Show Exit Price */}
                        <td style={{ fontWeight: '600' }}>
                          {exitPrice?.toLocaleString()}
                        </td>
                        {/* SELL: Show Exit Reason Badge */}
                        <td>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '6px 12px',
                            borderRadius: '16px',
                            fontSize: '13px',
                            fontWeight: '600',
                            backgroundColor: exitReason.bgColor,
                            color: exitReason.color,
                            gap: '6px'
                          }}>
                            <span>{exitReason.icon}</span>
                            {exitReason.text}
                          </span>
                        </td>
                      </>
                    )}

                    {/* Score */}
                    <td>
                      <span style={{
                        padding: '4px 12px',
                        background: (signal.strength || 0) >= 70 ? '#10b981' : 
                                   (signal.strength || 0) >= 50 ? '#3b82f6' :
                                   (signal.strength || 0) > 0 ? '#f59e0b' : '#6b7280',
                        color: 'white',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold'
                      }}>
                        {(signal.strength || 0) > 0 ? `${(signal.strength || 0).toFixed(0)}%` : 'N/A'}
                      </span>
                    </td>

                    {/* Date */}
                    <td style={{ color: '#94a3b8', fontSize: '13px' }}>
                      {signal.date ? new Date(signal.date).toLocaleDateString('vi-VN') : 'N/A'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <style jsx>{`
        .signals-module {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .signals-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 30px;
          flex-wrap: wrap;
          gap: 20px;
        }

        .stat-card {
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          padding: 20px;
          border-radius: 12px;
          border: 1px solid #334155;
        }

        .stat-value {
          font-size: 32px;
          font-weight: bold;
          margin-bottom: 5px;
        }

        .stat-label {
          color: #94a3b8;
          font-size: 14px;
        }

        .signals-table {
          width: 100%;
          border-collapse: collapse;
          background: #1e293b;
          border-radius: 12px;
          overflow: hidden;
        }

        .signals-table th {
          background: #0f172a;
          padding: 15px;
          text-align: left;
          color: #94a3b8;
          font-weight: 600;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .signals-table td {
          padding: 15px;
          border-top: 1px solid #334155;
          color: #e2e8f0;
        }

        .signals-table tbody tr:hover {
          background: #334155;
          cursor: pointer;
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
          .signals-header {
            flex-direction: column;
          }

          .signals-table {
            font-size: 12px;
          }

          .signals-table th,
          .signals-table td {
            padding: 10px 8px;
          }
        }
      `}</style>
    </div>
  );
}
