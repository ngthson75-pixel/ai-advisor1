import { useState } from 'react'

export default function SignalsModule({ signals, loading, onRefresh }) {
  const [filter, setFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')

  // Filter signals
  const filteredSignals = signals.filter(signal => {
    const strategyMatch = filter === 'all' || signal.strategy === filter.toUpperCase()
    const typeMatch = typeFilter === 'all' || signal.stock_type === typeFilter
    return strategyMatch && typeMatch
  })

  // Sort by priority and strength
  const sortedSignals = [...filteredSignals].sort((a, b) => {
    if (a.is_priority !== b.is_priority) return b.is_priority - a.is_priority
    return (b.strength || 0) - (a.strength || 0)
  })

  // Calculate stats
  const stats = {
    total: signals.length,
    pullback: signals.filter(s => s.strategy === 'PULLBACK').length,
    ema_cross: signals.filter(s => s.strategy === 'EMA_CROSS').length,
    priority: signals.filter(s => s.is_priority).length
  }

  return (
    <div className="signals-module">
      {/* Stats Dashboard */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon total">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Tổng tín hiệu</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon pullback">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.pullback}</div>
            <div className="stat-label">PULLBACK</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon ema">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <polyline points="19 12 12 19 5 12"/>
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.ema_cross}</div>
            <div className="stat-label">EMA CROSS</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon priority">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-value">{stats.priority}</div>
            <div className="stat-label">Ưu tiên</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters">
        <div className="filter-header">
          <h3>Bộ lọc tín hiệu</h3>
          <button onClick={onRefresh} className="refresh-btn" disabled={loading}>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path d="M4 2v6h6M16 18v-6h-6"/>
              <path d="M20 10a8 8 0 01-12.8 6.4M0 10a8 8 0 0112.8-6.4" stroke="currentColor" fill="none" strokeWidth="2"/>
            </svg>
            Làm mới
          </button>
        </div>

        <div className="filter-groups">
          <div className="filter-group">
            <label>Chiến lược:</label>
            <div className="filter-buttons">
              <button
                className={filter === 'all' ? 'active' : ''}
                onClick={() => setFilter('all')}
              >
                Tất cả ({signals.length})
              </button>
              <button
                className={filter === 'pullback' ? 'active' : ''}
                onClick={() => setFilter('pullback')}
              >
                PULLBACK ({stats.pullback})
              </button>
              <button
                className={filter === 'ema_cross' ? 'active' : ''}
                onClick={() => setFilter('ema_cross')}
              >
                EMA CROSS ({stats.ema_cross})
              </button>
            </div>
          </div>

          <div className="filter-group">
            <label>Loại cổ phiếu:</label>
            <div className="filter-buttons">
              <button
                className={typeFilter === 'all' ? 'active' : ''}
                onClick={() => setTypeFilter('all')}
              >
                Tất cả
              </button>
              <button
                className={typeFilter === 'Blue Chip' ? 'active' : ''}
                onClick={() => setTypeFilter('Blue Chip')}
              >
                Blue Chip
              </button>
              <button
                className={typeFilter === 'Mid Cap' ? 'active' : ''}
                onClick={() => setTypeFilter('Mid Cap')}
              >
                Mid Cap
              </button>
              <button
                className={typeFilter === 'Penny' ? 'active' : ''}
                onClick={() => setTypeFilter('Penny')}
              >
                Penny
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Signals Grid */}
      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Đang tải tín hiệu...</p>
        </div>
      ) : sortedSignals.length === 0 ? (
        <div className="empty-state">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="32" cy="32" r="30"/>
            <path d="M32 16v16l8 8"/>
          </svg>
          <h3>Không tìm thấy tín hiệu</h3>
          <p>Thử điều chỉnh bộ lọc hoặc quay lại sau</p>
        </div>
      ) : (
        <div className="signals-grid">
          {sortedSignals.map((signal, index) => (
            <SignalCard key={signal.id || index} signal={signal} index={index} />
          ))}
        </div>
      )}
    </div>
  )
}

// Signal Card Component
function SignalCard({ signal, index }) {
  const isPullback = signal.strategy === 'PULLBACK'
  const strategyClass = isPullback ? 'pullback' : 'ema-cross'

  const formatPrice = (price) => {
    return new Intl.NumberFormat('vi-VN').format(price)
  }

  const formatPercent = (value) => {
    return value ? `${value.toFixed(0)}%` : 'N/A'
  }

  return (
    <div
      className={`signal-card ${strategyClass}`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header */}
      <div className="signal-header">
        <div className="signal-ticker">
          {signal.is_priority === 1 && <span className="priority-star">⭐</span>}
          <span className="ticker">{signal.ticker}</span>
          <span className={`stock-type ${signal.stock_type?.toLowerCase().replace(' ', '-')}`}>
            {signal.stock_type}
          </span>
        </div>
        <div className={`strategy-badge ${strategyClass}`}>
          {signal.strategy}
        </div>
      </div>

      {/* Strength Bar */}
      {signal.strength && (
        <div className="strength-container">
          <div className="strength-bar">
            <div
              className="strength-fill"
              style={{ width: `${signal.strength}%` }}
            ></div>
          </div>
          <span className="strength-label">{formatPercent(signal.strength)} độ mạnh</span>
        </div>
      )}

      {/* Price Info */}
      <div className="price-grid">
        <div className="price-item entry">
          <label>Giá vào</label>
          <div className="price-value">{formatPrice(signal.entry_price)}</div>
        </div>

        <div className="price-item stop-loss">
          <label>Cắt lỗ</label>
          <div className="price-value">{formatPrice(signal.stop_loss)}</div>
          <div className="price-change">
            -{((signal.entry_price - signal.stop_loss) / signal.entry_price * 100).toFixed(1)}%
          </div>
        </div>

        <div className="price-item take-profit">
          <label>Chốt lời</label>
          <div className="price-value">{formatPrice(signal.take_profit)}</div>
          <div className="price-change">
            +{((signal.take_profit - signal.entry_price) / signal.entry_price * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Risk/Reward */}
      {signal.risk_reward && (
        <div className="risk-reward">
          <label>Tỷ lệ Rủi ro/Lợi nhuận</label>
          <div className="rr-value">1 : {signal.risk_reward.toFixed(2)}</div>
        </div>
      )}

      {/* Additional Info */}
      <div className="additional-info">
        {signal.rsi && (
          <div className="info-item">
            <span className="info-label">RSI:</span>
            <span className="info-value">{signal.rsi.toFixed(1)}</span>
          </div>
        )}
        {signal.date && (
          <div className="info-item">
            <span className="info-label">Ngày:</span>
            <span className="info-value">{signal.date}</span>
          </div>
        )}
      </div>
    </div>
  )
}
