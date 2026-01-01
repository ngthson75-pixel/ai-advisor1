import { useState, useEffect } from 'react'

const API_URL = import.meta.env.PROD
  ? 'https://ai-advisor1-backend.onrender.com/api'
  : 'http://localhost:10000/api'

export default function SignalsModule({ signals, loading, onRefresh }) {
  const [filter, setFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState('')

  // Separate BUY and SELL signals
  const buySignals = signals.filter(signal => signal.action === 'BUY' || signal.action === 'MUA' || !signal.action)
  const sellSignals = signals.filter(signal => signal.action === 'SELL' || signal.action === 'BÁN')

  // Filter signals
  const filterSignals = (signalList) => {
    return signalList.filter(signal => {
      const strategyMatch = filter === 'all' || signal.strategy === filter.toUpperCase()
      const typeMatch = typeFilter === 'all' || signal.stock_type === typeFilter
      return strategyMatch && typeMatch
    })
  }

  const filteredBuySignals = filterSignals(buySignals)
  const filteredSellSignals = filterSignals(sellSignals)

  // Calculate stats
  const stats = {
    total: signals.length,
    buy: buySignals.length,
    sell: sellSignals.length,
    pullback: signals.filter(s => s.strategy === 'PULLBACK').length,
    ema_cross: signals.filter(s => s.strategy === 'EMA_CROSS').length,
    priority: signals.filter(s => s.is_priority).length
  }

  const formatPrice = (price) => {
    return new Intl.NumberFormat('vi-VN').format(price)
  }

  // Trigger scan
  const startScan = async () => {
    try {
      setScanning(true)
      setScanProgress('Đang khởi động quét 343 cổ phiếu...')

      const response = await fetch(`${API_URL}/scan`, {
        method: 'POST'
      })
      
      const data = await response.json()
      
      if (data.success) {
        setScanProgress('Đang phân tích thị trường... (2-3 phút)')
        
        // Poll for status every 5 seconds
        const pollInterval = setInterval(async () => {
          try {
            const statusRes = await fetch(`${API_URL}/scan/status`)
            const statusData = await statusRes.json()
            
            if (statusData.signals_count > 0) {
              clearInterval(pollInterval)
              setScanProgress(`✅ Đã tìm thấy ${statusData.signals_count} tín hiệu!`)
              setTimeout(() => {
                setScanning(false)
                setScanProgress('')
                onRefresh() // Refresh signals
              }, 1500)
            } else {
              setScanProgress(`Đang quét... vui lòng chờ thêm ít phút`)
            }
          } catch (error) {
            console.error('Status check error:', error)
          }
        }, 5000)
        
        // Timeout after 5 minutes
        setTimeout(() => {
          clearInterval(pollInterval)
          if (scanning) {
            setScanProgress('⏱️ Quét mất nhiều thời gian. Vui lòng refresh sau 2 phút.')
            setTimeout(() => {
              setScanning(false)
              setScanProgress('')
              onRefresh()
            }, 3000)
          }
        }, 300000)
        
      } else {
        setScanProgress('❌ Không thể khởi động quét: ' + data.message)
        setTimeout(() => {
          setScanning(false)
          setScanProgress('')
        }, 3000)
      }
    } catch (error) {
      console.error('Scan error:', error)
      setScanProgress('❌ Lỗi kết nối: ' + error.message)
      setTimeout(() => {
        setScanning(false)
        setScanProgress('')
      }, 3000)
    }
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
            <div className="stat-value">{stats.buy}</div>
            <div className="stat-label">Tín hiệu MUA</div>
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
            <div className="stat-value">{stats.sell}</div>
            <div className="stat-label">Tín hiệu BÁN</div>
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
          <button onClick={onRefresh} className="refresh-btn" disabled={loading || scanning}>
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

      {/* Signals Tables */}
      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Đang tải tín hiệu...</p>
        </div>
      ) : signals.length === 0 ? (
        <div className="empty-state-large">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
          <h3>Chưa có tín hiệu nào</h3>
          <p>Hệ thống sẽ tự động quét 343 cổ phiếu có thanh khoản cao nhất<br/>
          và phân tích theo chiến lược Pullback & EMA Cross</p>
          
          {scanning ? (
            <div className="scan-progress">
              <div className="spinner" style={{width: '32px', height: '32px', borderWidth: '3px'}}></div>
              <p className="scan-status">{scanProgress}</p>
            </div>
          ) : (
            <button onClick={startScan} className="btn-scan" disabled={scanning}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10"/>
                <polyline points="1 20 1 14 7 14"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              Tạo tín hiệu mới (2-3 phút)
            </button>
          )}
        </div>
      ) : (
        <div className="signals-tables">
          {/* BUY Signals Table */}
          <div className="signal-table-section">
            <div className="table-header buy">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                </svg>
                1. Tín hiệu MUA
              </h3>
              <span className="table-count">{filteredBuySignals.length} tín hiệu</span>
            </div>

            {filteredBuySignals.length === 0 ? (
              <div className="empty-state-small">
                <p>Không có tín hiệu mua</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="signals-table">
                  <thead>
                    <tr>
                      <th>Mã</th>
                      <th>Tín hiệu</th>
                      <th>Score</th>
                      <th>Xác xuất</th>
                      <th>Giá mua</th>
                      <th>Ngày</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBuySignals.map((signal, index) => (
                      <tr key={signal.id || index} className={signal.is_priority ? 'priority-row' : ''}>
                        <td className="ticker-cell">
                          {signal.is_priority && <span className="priority-star">⭐</span>}
                          <strong>{signal.ticker}</strong>
                          {signal.stock_type && (
                            <span className={`stock-badge ${signal.stock_type?.toLowerCase().replace(' ', '-')}`}>
                              {signal.stock_type}
                            </span>
                          )}
                        </td>
                        <td>
                          <span className="signal-badge buy">{signal.strategy || 'Swing T+'}</span>
                        </td>
                        <td>
                          <span className="score-badge">{Math.round(signal.strength || 70)}</span>
                        </td>
                        <td>
                          <span className="probability">{Math.round(signal.strength || 70)}%</span>
                        </td>
                        <td className="price-cell">
                          <strong>{formatPrice(signal.entry_price)}</strong>
                        </td>
                        <td className="date-cell">{signal.date || new Date().toISOString().split('T')[0]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* SELL Signals Table */}
          <div className="signal-table-section">
            <div className="table-header sell">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="1 18 10.5 8.5 15.5 13.5 23 6"/>
                </svg>
                2. Tín hiệu BÁN
              </h3>
              <span className="table-count">{filteredSellSignals.length} tín hiệu</span>
            </div>

            {filteredSellSignals.length === 0 ? (
              <div className="empty-state-small">
                <p>Không có tín hiệu bán</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="signals-table">
                  <thead>
                    <tr>
                      <th>Mã</th>
                      <th>Tín hiệu</th>
                      <th>Score</th>
                      <th>Xác xuất</th>
                      <th>Giá bán</th>
                      <th>Ngày</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSellSignals.map((signal, index) => (
                      <tr key={signal.id || index} className={signal.is_priority ? 'priority-row' : ''}>
                        <td className="ticker-cell">
                          {signal.is_priority && <span className="priority-star">⭐</span>}
                          <strong>{signal.ticker}</strong>
                          {signal.stock_type && (
                            <span className={`stock-badge ${signal.stock_type?.toLowerCase().replace(' ', '-')}`}>
                              {signal.stock_type}
                            </span>
                          )}
                        </td>
                        <td>
                          <span className="signal-badge sell">{signal.strategy || 'Swing T+'}</span>
                        </td>
                        <td>
                          <span className="score-badge">{Math.round(signal.strength || 70)}</span>
                        </td>
                        <td>
                          <span className="probability">{Math.round(signal.strength || 70)}%</span>
                        </td>
                        <td className="price-cell">
                          <strong>{formatPrice(signal.take_profit || signal.entry_price)}</strong>
                        </td>
                        <td className="date-cell">{signal.date || new Date().toISOString().split('T')[0]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
