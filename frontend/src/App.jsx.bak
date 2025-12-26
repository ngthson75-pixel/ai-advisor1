import { useState, useEffect } from 'react'
import './App.css'

// API Configuration
const API_URL = import.meta.env.PROD 
  ? 'https://ai-advisor1-backend.onrender.com/api'
  : 'http://localhost:10000/api'

function App() {
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, pullback, ema_cross
  const [typeFilter, setTypeFilter] = useState('all') // all, Blue Chip, Mid Cap, Penny
  const [lastUpdate, setLastUpdate] = useState(null)

  // Fetch signals from API
  const fetchSignals = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/signals`)
      const data = await response.json()
      
      if (data.success) {
        setSignals(data.signals)
        setLastUpdate(new Date())
      }
    } catch (error) {
      console.error('Error fetching signals:', error)
      // Use mock data if API fails
      setSignals(getMockData())
      setLastUpdate(new Date())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSignals()
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchSignals, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

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
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="brand">
              <div className="logo">
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                  <path d="M20 8L32 14V26L20 32L8 26V14L20 8Z" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <path d="M20 8V20M20 20L32 26M20 20L8 26" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="20" cy="20" r="3" fill="currentColor"/>
                </svg>
              </div>
              <div className="brand-text">
                <h1>AI Advisor</h1>
                <p>Stock Trading Signals</p>
              </div>
            </div>
            
            <div className="header-actions">
              {lastUpdate && (
                <div className="last-update">
                  <span className="pulse"></span>
                  Updated: {lastUpdate.toLocaleTimeString()}
                </div>
              )}
              <button onClick={fetchSignals} className="refresh-btn" disabled={loading}>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M4 2v6h6M16 18v-6h-6"/>
                  <path d="M20 10a8 8 0 01-12.8 6.4M0 10a8 8 0 0112.8-6.4" stroke="currentColor" fill="none" strokeWidth="2"/>
                </svg>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container">
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
              <div className="stat-label">Total Signals</div>
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
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            </div>
            <div className="stat-content">
              <div className="stat-value">{stats.priority}</div>
              <div className="stat-label">Priority Stars</div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="filters">
          <div className="filter-group">
            <label>Strategy:</label>
            <div className="filter-buttons">
              <button 
                className={filter === 'all' ? 'active' : ''} 
                onClick={() => setFilter('all')}
              >
                All ({signals.length})
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
            <label>Stock Type:</label>
            <div className="filter-buttons">
              <button 
                className={typeFilter === 'all' ? 'active' : ''} 
                onClick={() => setTypeFilter('all')}
              >
                All
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

        {/* Signals Grid */}
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading signals...</p>
          </div>
        ) : sortedSignals.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="32" cy="32" r="30"/>
              <path d="M32 16v16l8 8"/>
            </svg>
            <h3>No signals found</h3>
            <p>Try adjusting your filters or check back later</p>
          </div>
        ) : (
          <div className="signals-grid">
            {sortedSignals.map((signal, index) => (
              <SignalCard key={signal.id || index} signal={signal} index={index} />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>© 2025 AI Advisor. Professional Stock Trading Signals Platform.</p>
          <p className="disclaimer">
            Investment involves risks. Please do your own research before trading.
          </p>
        </div>
      </footer>
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
          {signal.is_priority && <span className="priority-star">⭐</span>}
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
          <span className="strength-label">{formatPercent(signal.strength)} strength</span>
        </div>
      )}

      {/* Price Info */}
      <div className="price-grid">
        <div className="price-item entry">
          <label>Entry Price</label>
          <div className="price-value">{formatPrice(signal.entry_price)}</div>
        </div>
        
        <div className="price-item stop-loss">
          <label>Stop Loss</label>
          <div className="price-value">{formatPrice(signal.stop_loss)}</div>
          <div className="price-change">
            -{((signal.entry_price - signal.stop_loss) / signal.entry_price * 100).toFixed(1)}%
          </div>
        </div>
        
        <div className="price-item take-profit">
          <label>Take Profit</label>
          <div className="price-value">{formatPrice(signal.take_profit)}</div>
          <div className="price-change">
            +{((signal.take_profit - signal.entry_price) / signal.entry_price * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Risk/Reward */}
      {signal.risk_reward && (
        <div className="risk-reward">
          <label>Risk/Reward Ratio</label>
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
            <span className="info-label">Date:</span>
            <span className="info-value">{signal.date}</span>
          </div>
        )}
      </div>
    </div>
  )
}

// Mock data for testing (when API is unavailable)
function getMockData() {
  return [
    {
      id: 1,
      ticker: 'TCH',
      strategy: 'PULLBACK',
      entry_price: 12500,
      stop_loss: 11800,
      take_profit: 13800,
      risk_reward: 1.86,
      rsi: 52.3,
      strength: 100,
      stock_type: 'Penny',
      is_priority: 1,
      date: '2025-12-25'
    },
    {
      id: 2,
      ticker: 'PWA',
      strategy: 'EMA_CROSS',
      entry_price: 8900,
      stop_loss: 8300,
      take_profit: 9800,
      risk_reward: 2.1,
      rsi: 58.7,
      strength: 100,
      stock_type: 'Penny',
      is_priority: 1,
      date: '2025-12-25'
    },
    {
      id: 3,
      ticker: 'VCB',
      strategy: 'PULLBACK',
      entry_price: 85000,
      stop_loss: 82000,
      take_profit: 92000,
      risk_reward: 2.33,
      rsi: 48.2,
      strength: 80,
      stock_type: 'Blue Chip',
      is_priority: 0,
      date: '2025-12-25'
    }
  ]
}

export default App
