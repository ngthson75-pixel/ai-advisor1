import { useState } from 'react'

export default function RiskShield({ signals }) {
  const [portfolio, setPortfolio] = useState([])
  const [capital, setCapital] = useState(100000000) // 100M VND
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)

  const addPosition = () => {
    setPortfolio([...portfolio, {
      ticker: '',
      quantity: 0,
      entry_price: 0,
      current_price: 0
    }])
  }

  const updatePosition = (index, field, value) => {
    const updated = [...portfolio]
    updated[index][field] = value
    setPortfolio(updated)
  }

  const analyzeRisk = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/risk/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          positions: portfolio,
          total_capital: capital
        })
      })
      const data = await response.json()
      setAnalysis(data.analysis)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="risk-shield">
      <div className="module-header">
        <div className="header-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <div>
          <h2>Risk Shield</h2>
          <p>Quản lý rủi ro thông minh với AI</p>
        </div>
      </div>

      <div className="risk-content">
        {/* Capital Input */}
        <div className="capital-section">
          <label>Tổng vốn đầu tư (VND):</label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(Number(e.target.value))}
            className="capital-input"
          />
        </div>

        {/* Portfolio Positions */}
        <div className="positions-section">
          <div className="section-header">
            <h3>Danh mục hiện tại</h3>
            <button onClick={addPosition} className="add-btn">
              + Thêm cổ phiếu
            </button>
          </div>

          {portfolio.map((pos, idx) => (
            <div key={idx} className="position-row">
              <input
                placeholder="Mã CP"
                value={pos.ticker}
                onChange={(e) => updatePosition(idx, 'ticker', e.target.value)}
              />
              <input
                type="number"
                placeholder="Số lượng"
                value={pos.quantity}
                onChange={(e) => updatePosition(idx, 'quantity', Number(e.target.value))}
              />
              <input
                type="number"
                placeholder="Giá mua"
                value={pos.entry_price}
                onChange={(e) => updatePosition(idx, 'entry_price', Number(e.target.value))}
              />
              <input
                type="number"
                placeholder="Giá hiện tại"
                value={pos.current_price}
                onChange={(e) => updatePosition(idx, 'current_price', Number(e.target.value))}
              />
            </div>
          ))}
        </div>

        {/* Analyze Button */}
        <button
          onClick={analyzeRisk}
          disabled={loading || portfolio.length === 0}
          className="analyze-btn"
        >
          {loading ? 'Đang phân tích...' : '🛡️ Phân tích rủi ro'}
        </button>

        {/* Analysis Result */}
        {analysis && (
          <div className="analysis-result">
            <h3>📊 Kết quả phân tích</h3>
            <div className="analysis-content">
              {analysis}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}