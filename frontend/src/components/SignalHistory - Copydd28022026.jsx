import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Clock, Star } from 'lucide-react'

const API_URL = import.meta.env.PROD
  ? 'https://ai-advisor1-backend.onrender.com/api'
  : 'http://localhost:10000/api'

export default function SignalHistory() {
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSignals()
  }, [])

  const fetchSignals = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/signals`)
      const data = await response.json()
      
      if (data.success) {
  // Sort by date DESC (newest first), then get latest 10
  const sortedSignals = data.signals
    .sort((a, b) => {
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);
      return dateB - dateA; // Descending (newest first)
    })
    .slice(0, 10);
  
  setSignals(sortedSignals);
}
    } catch (error) {
      console.error('Error fetching signals:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = (price) => {
    return new Intl.NumberFormat('vi-VN').format(price)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = Math.abs(now - date)
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) return 'Hôm nay'
    if (diffDays === 1) return 'Hôm qua'
    if (diffDays < 7) return `${diffDays} ngày trước`
    return date.toLocaleDateString('vi-VN')
  }

  if (loading) {
    return (
      <div className="signal-history loading">
        <div className="spinner"></div>
        <p>Đang tải lịch sử tín hiệu...</p>
      </div>
    )
  }

  if (signals.length === 0) {
    return null // Don't show if no signals
  }

  return (
    <div className="signal-history">
      <div className="history-header">
        <h3>
          <Clock className="w-5 h-5" />
          Lịch sử tín hiệu gần đây
        </h3>
        <span className="signal-count">{signals.length} tín hiệu</span>
      </div>

      <div className="history-grid">
        {signals.map((signal, index) => (
          <div key={index} className={`history-card ${signal.action === 'BUY' ? 'buy' : 'sell'}`}>
            <div className="card-header">
              <div className="ticker-info">
                {signal.is_priority && <Star className="priority-icon" fill="currentColor" />}
                <span className="ticker">{signal.ticker}</span>
                {signal.stock_type && (
                  <span className={`badge ${signal.stock_type.toLowerCase().replace(' ', '-')}`}>
                    {signal.stock_type}
                  </span>
                )}
              </div>
              <div className={`action-badge ${signal.action === 'BUY' ? 'buy' : 'sell'}`}>
                {signal.action === 'BUY' ? (
                  <>
                    <TrendingUp className="w-4 h-4" />
                    MUA
                  </>
                ) : (
                  <>
                    <TrendingDown className="w-4 h-4" />
                    BÁN
                  </>
                )}
              </div>
            </div>

            <div className="card-body">
              <div className="price-row">
                <span className="label">Giá:</span>
                <span className="value">{formatPrice(signal.entry_price)} VND</span>
              </div>
              
              <div className="stats-row">
                <div className="stat">
                  <span className="stat-label">Score</span>
                  <span className="stat-value">{Math.round(signal.strength || 70)}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Xác xuất</span>
                  <span className="stat-value">{Math.round(signal.strength || 70)}%</span>
                </div>
              </div>
            </div>

            <div className="card-footer">
              <span className="date">{formatDate(signal.date)}</span>
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .signal-history {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
          margin: 24px 0;
        }

        .signal-history.loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 48px;
          color: #666;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #f3f3f3;
          border-top: 3px solid #3498db;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 12px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .history-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 2px solid #f0f0f0;
        }

        .history-header h3 {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 20px;
          font-weight: 600;
          color: #333;
          margin: 0;
        }

        .signal-count {
          background: #f0f0f0;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 14px;
          color: #666;
        }

        .history-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 16px;
        }

        .history-card {
          background: #f9f9f9;
          border-radius: 10px;
          padding: 16px;
          border: 2px solid transparent;
          transition: all 0.3s ease;
        }

        .history-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .history-card.buy {
          border-color: #10b981;
        }

        .history-card.sell {
          border-color: #ef4444;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .ticker-info {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .priority-icon {
          width: 16px;
          height: 16px;
          color: #f59e0b;
        }

        .ticker {
          font-size: 18px;
          font-weight: 700;
          color: #111;
        }

        .badge {
          font-size: 10px;
          padding: 2px 6px;
          border-radius: 4px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .badge.blue-chip {
          background: #dbeafe;
          color: #1e40af;
        }

        .badge.mid-cap {
          background: #fef3c7;
          color: #92400e;
        }

        .badge.penny {
          background: #fee2e2;
          color: #991b1b;
        }

        .action-badge {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 600;
        }

        .action-badge.buy {
          background: #d1fae5;
          color: #065f46;
        }

        .action-badge.sell {
          background: #fee2e2;
          color: #991b1b;
        }

        .card-body {
          margin: 12px 0;
        }

        .price-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .price-row .label {
          font-size: 13px;
          color: #666;
        }

        .price-row .value {
          font-size: 16px;
          font-weight: 700;
          color: #111;
        }

        .stats-row {
          display: flex;
          gap: 12px;
        }

        .stat {
          flex: 1;
          background: white;
          padding: 8px;
          border-radius: 6px;
          text-align: center;
        }

        .stat-label {
          display: block;
          font-size: 11px;
          color: #666;
          margin-bottom: 4px;
        }

        .stat-value {
          display: block;
          font-size: 16px;
          font-weight: 700;
          color: #111;
        }

        .card-footer {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid #e5e5e5;
        }

        .date {
          font-size: 12px;
          color: #999;
        }

        @media (max-width: 768px) {
          .history-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  )
}
