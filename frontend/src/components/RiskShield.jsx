import { useState } from 'react'

export default function RiskShield() {
  const [capital, setCapital] = useState('')
  const [positions, setPositions] = useState([])
  const [newPosition, setNewPosition] = useState({
    ticker: '',
    quantity: '',
    entryPrice: '',
    currentPrice: ''
  })
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)

  const addPosition = () => {
    if (newPosition.ticker && newPosition.quantity && newPosition.entryPrice && newPosition.currentPrice) {
      setPositions([...positions, { ...newPosition, id: Date.now() }])
      setNewPosition({ ticker: '', quantity: '', entryPrice: '', currentPrice: '' })
    }
  }

  const removePosition = (id) => {
    setPositions(positions.filter(p => p.id !== id))
  }

  const analyzeRisk = async () => {
    if (!capital || positions.length === 0) {
      alert('Vui lòng nhập vốn và thêm ít nhất một vị thế!')
      return
    }

    setLoading(true)
    
    // Simulate AI analysis (replace with actual Gemini API call)
    setTimeout(() => {
      const totalInvested = positions.reduce((sum, p) => 
        sum + (parseFloat(p.quantity) * parseFloat(p.entryPrice)), 0
      )
      
      const currentValue = positions.reduce((sum, p) => 
        sum + (parseFloat(p.quantity) * parseFloat(p.currentPrice)), 0
      )
      
      const pnl = currentValue - totalInvested
      const pnlPercent = (pnl / totalInvested) * 100
      const capitalUsage = (totalInvested / parseFloat(capital)) * 100

      setAnalysis({
        totalInvested,
        currentValue,
        pnl,
        pnlPercent,
        capitalUsage,
        riskScore: capitalUsage > 80 ? 'Cao' : capitalUsage > 50 ? 'Trung bình' : 'Thấp',
        recommendation: capitalUsage > 80 
          ? 'Danh mục đang sử dụng quá nhiều vốn. Nên cân nhắc giảm bớt vị thế.'
          : capitalUsage > 50
          ? 'Mức độ rủi ro ở mức trung bình. Theo dõi chặt chẽ các vị thế.'
          : 'Mức độ rủi ro thấp. Vẫn còn khả năng mở thêm vị thế.'
      })
      setLoading(false)
    }, 1500)
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(value)
  }

  return (
    <div className="risk-shield">
      <div className="module-header">
        <h2>🛡️ Risk Shield</h2>
        <p>Phân tích rủi ro danh mục đầu tư với AI</p>
      </div>

      <div className="risk-grid">
        {/* Capital Input Section */}
        <div className="risk-section">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="1" x2="12" y2="23"/>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            Vốn đầu tư
          </h3>
          
          <div className="form-group">
            <label>Tổng vốn (VND)</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              placeholder="Nhập tổng vốn của bạn"
            />
          </div>

          <div className="form-group">
            <label>Thêm vị thế mới</label>
            <input
              type="text"
              value={newPosition.ticker}
              onChange={(e) => setNewPosition({...newPosition, ticker: e.target.value.toUpperCase()})}
              placeholder="Mã cổ phiếu (VD: VCB)"
              style={{marginBottom: '8px'}}
            />
            <input
              type="number"
              value={newPosition.quantity}
              onChange={(e) => setNewPosition({...newPosition, quantity: e.target.value})}
              placeholder="Số lượng"
              style={{marginBottom: '8px'}}
            />
            <input
              type="number"
              value={newPosition.entryPrice}
              onChange={(e) => setNewPosition({...newPosition, entryPrice: e.target.value})}
              placeholder="Giá mua"
              style={{marginBottom: '8px'}}
            />
            <input
              type="number"
              value={newPosition.currentPrice}
              onChange={(e) => setNewPosition({...newPosition, currentPrice: e.target.value})}
              placeholder="Giá hiện tại"
              style={{marginBottom: '8px'}}
            />
            <button onClick={addPosition} className="btn-secondary">
              + Thêm vị thế
            </button>
          </div>
        </div>

        {/* Portfolio Section */}
        <div className="risk-section">
          <h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            Danh mục hiện tại ({positions.length})
          </h3>

          {positions.length === 0 ? (
            <div className="empty-state" style={{padding: '40px 20px'}}>
              <p>Chưa có vị thế nào. Thêm vị thế để phân tích.</p>
            </div>
          ) : (
            <div className="position-list">
              {positions.map(position => {
                const invested = parseFloat(position.quantity) * parseFloat(position.entryPrice)
                const current = parseFloat(position.quantity) * parseFloat(position.currentPrice)
                const pnl = current - invested
                const pnlPercent = (pnl / invested) * 100

                return (
                  <div key={position.id} className="position-item">
                    <div className="position-info">
                      <div className="position-ticker">{position.ticker}</div>
                      <div className="position-details">
                        {position.quantity} CP × {formatCurrency(position.entryPrice)}
                        <span style={{
                          marginLeft: '8px',
                          color: pnl >= 0 ? '#10b981' : '#ef4444',
                          fontWeight: 600
                        }}>
                          {pnl >= 0 ? '+' : ''}{pnlPercent.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <button onClick={() => removePosition(position.id)} className="btn-remove">
                      Xóa
                    </button>
                  </div>
                )
              })}
            </div>
          )}

          <button 
            onClick={analyzeRisk} 
            className="btn-primary" 
            disabled={loading || !capital || positions.length === 0}
          >
            {loading ? (
              <>
                <div className="spinner" style={{width: '16px', height: '16px', borderWidth: '2px'}}></div>
                Đang phân tích...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                Phân tích rủi ro với AI
              </>
            )}
          </button>

          {/* Analysis Result */}
          {analysis && (
            <div className="analysis-result">
              <h4>📊 Kết quả phân tích</h4>
              
              <p><strong>Vốn đã sử dụng:</strong> {formatCurrency(analysis.totalInvested)} ({analysis.capitalUsage.toFixed(1)}%)</p>
              <p><strong>Giá trị hiện tại:</strong> {formatCurrency(analysis.currentValue)}</p>
              <p>
                <strong>Lãi/Lỗ:</strong>{' '}
                <span style={{ color: analysis.pnl >= 0 ? '#10b981' : '#ef4444' }}>
                  {formatCurrency(analysis.pnl)} ({analysis.pnl >= 0 ? '+' : ''}{analysis.pnlPercent.toFixed(2)}%)
                </span>
              </p>
              
              <div className="risk-score">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                Mức rủi ro: {analysis.riskScore}
              </div>
              
              <p><strong>Khuyến nghị:</strong></p>
              <p>{analysis.recommendation}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
