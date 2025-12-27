import { useState } from 'react'

export default function SignalsModule({ signals, loading, onRefresh }) {
  const [filter, setFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')

  const filteredSignals = signals.filter(signal => {
    const strategyMatch = filter === 'all' || signal.strategy === filter.toUpperCase()
    const typeMatch = typeFilter === 'all' || signal.stock_type === typeFilter
    return strategyMatch && typeMatch
  })

  const sortedSignals = [...filteredSignals].sort((a, b) => {
    if (a.is_priority !== b.is_priority) return b.is_priority - a.is_priority
    return (b.strength || 0) - (a.strength || 0)
  })

  const stats = {
    total: signals.length,
    pullback: signals.filter(s => s.strategy === 'PULLBACK').length,
    ema_cross: signals.filter(s => s.strategy === 'EMA_CROSS').length,
    priority: signals.filter(s => s.is_priority).length
  }

  return (
    <div className="signals-module">
      <div className="stats-grid">
        <StatCard icon="total" value={stats.total} label="Tổng tín hiệu" />
        <StatCard icon="pullback" value={stats.pullback} label="PULLBACK" />
        <StatCard icon="ema" value={stats.ema_cross} label="EMA CROSS" />
        <StatCard icon="priority" value={stats.priority} label="Ưu tiên" />
      </div>

      <div className="filters">
        <div className="filter-header">
          <h3>Bộ lọc tín hiệu</h3>
          <button onClick={onRefresh} className="refresh-btn" disabled={loading}>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
              <path d="M4 2v6h6M16 18v-6h-6"/><path d="M20 10a8 8 0 01-12.8 6.4M0 10a8 8 0 0112.8-6.4" stroke="currentColor" fill="none" strokeWidth="2"/>
            </svg>
            Làm mới
          </button>
        </div>
        
        <div className="filter-groups">
          <FilterGroup label="Chiến lược:" options={[
            { value: 'all', label: `Tất cả (${signals.length})`, active: filter === 'all', onClick: () => setFilter('all') },
            { value: 'pullback', label: `PULLBACK (${stats.pullback})`, active: filter === 'pullback', onClick: () => setFilter('pullback') },
            { value: 'ema_cross', label: `EMA CROSS (${stats.ema_cross})`, active: filter === 'ema_cross', onClick: () => setFilter('ema_cross') }
          ]} />
          
          <FilterGroup label="Loại cổ phiếu:" options={[
            { value: 'all', label: 'Tất cả', active: typeFilter === 'all', onClick: () => setTypeFilter('all') },
            { value: 'Blue Chip', label: 'Blue Chip', active: typeFilter === 'Blue Chip', onClick: () => setTypeFilter('Blue Chip') },
            { value: 'Mid Cap', label: 'Mid Cap', active: typeFilter === 'Mid Cap', onClick: () => setTypeFilter('Mid Cap') },
            { value: 'Penny', label: 'Penny', active: typeFilter === 'Penny', onClick: () => setTypeFilter('Penny') }
          ]} />
        </div>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Đang tải tín hiệu...</p>
          <p className="loading-note">Lần đầu có thể mất 30-60 giây</p>
        </div>
      ) : sortedSignals.length === 0 ? (
        <div className="empty-state">
          <h3>Không tìm thấy tín hiệu</h3>
          <p>Thử điều chỉnh bộ lọc hoặc quay lại sau</p>
        </div>
      ) : (
        <div className="signals-grid">
          {sortedSignals.map((signal, idx) => (
            <SignalCard key={signal.id || idx} signal={signal} index={idx} />
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, value, label }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${icon}`}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          {icon === 'total' && <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>}
          {icon === 'pullback' && <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>}
          {icon === 'ema' && <><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></>}
          {icon === 'priority' && <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>}
        </svg>
      </div>
      <div className="stat-content">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

function FilterGroup({ label, options }) {
  return (
    <div className="filter-group">
      <label>{label}</label>
      <div className="filter-buttons">
        {options.map(opt => (
          <button key={opt.value} className={opt.active ? 'active' : ''} onClick={opt.onClick}>
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function SignalCard({ signal, index }) {
  const isPullback = signal.strategy === 'PULLBACK'
  const formatPrice = (price) => new Intl.NumberFormat('vi-VN').format(price)
  
  return (
    <div className={`signal-card ${isPullback ? 'pullback' : 'ema-cross'}`} style={{ animationDelay: `${index * 50}ms` }}>
      <div className="signal-header">
        <div className="signal-ticker">
          {signal.is_priority && <span className="priority-star">⭐</span>}
          <span className="ticker">{signal.ticker}</span>
          <span className={`stock-type ${signal.stock_type?.toLowerCase().replace(' ', '-')}`}>
            {signal.stock_type}
          </span>
        </div>
        <div className={`strategy-badge ${isPullback ? 'pullback' : 'ema-cross'}`}>
          {signal.strategy}
        </div>
      </div>

      {signal.strength && (
        <div className="strength-container">
          <div className="strength-bar">
            <div className="strength-fill" style={{ width: `${signal.strength}%` }}></div>
          </div>
          <span className="strength-label">{signal.strength}% độ mạnh</span>
        </div>
      )}

      <div className="price-grid">
        <div className="price-item entry">
          <label>Giá vào</label>
          <div className="price-value">{formatPrice(signal.entry_price)}</div>
        </div>
        <div className="price-item stop-loss">
          <label>Cắt lỗ</label>
          <div className="price-value">{formatPrice(signal.stop_loss)}</div>
          <div className="price-change">-{((signal.entry_price - signal.stop_loss) / signal.entry_price * 100).toFixed(1)}%</div>
        </div>
        <div className="price-item take-profit">
          <label>Chốt lời</label>
          <div className="price-value">{formatPrice(signal.take_profit)}</div>
          <div className="price-change">+{((signal.take_profit - signal.entry_price) / signal.entry_price * 100).toFixed(1)}%</div>
        </div>
      </div>

      {signal.risk_reward && (
        <div className="risk-reward">
          <label>Tỷ lệ Rủi ro/Lợi nhuận</label>
          <div className="rr-value">1 : {signal.risk_reward.toFixed(2)}</div>
        </div>
      )}

      <div className="additional-info">
        {signal.rsi && <div className="info-item"><span className="info-label">RSI:</span><span className="info-value">{signal.rsi.toFixed(1)}</span></div>}
        {signal.date && <div className="info-item"><span className="info-label">Ngày:</span><span className="info-value">{signal.date}</span></div>}
      </div>
    </div>
  )
}export default SignalsModule