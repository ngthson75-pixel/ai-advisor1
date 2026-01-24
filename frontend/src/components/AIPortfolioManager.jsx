import { useState, useEffect, useRef } from 'react'
import { getUserId } from '../utils/userSession'

export default function AIPortfolioManager() {
  // ✅ User isolation - mỗi user có ID riêng
  const [userId] = useState(() => getUserId())
  
  // Portfolio state
  const [capital, setCapital] = useState('')
  const [positions, setPositions] = useState([])
  const [newPosition, setNewPosition] = useState({
    ticker: '',
    quantity: '',
    entryPrice: '',
    currentPrice: ''
  })

  // Chat state
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Xin chào! Tôi là AI Advisor của bạn.\n\nHãy bắt đầu bằng cách:\n1. Nhập vốn đầu tư của bạn\n2. Thêm các vị thế hiện tại (nếu có)\n3. Đặt câu hỏi hoặc yêu cầu phân tích\n\nTôi sẽ phân tích danh mục và tư vấn chiến lược phù hợp! 🚀'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const API_BASE = import.meta.env.VITE_API_URL || 'https://ai-advisor1-backend.onrender.com/api'

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // ✅ Load portfolio from backend on mount
  useEffect(() => {
    loadPortfolioFromBackend()
    loadChatHistoryFromBackend()
  }, [userId])

  const loadPortfolioFromBackend = async () => {
    try {
      const response = await fetch(`${API_BASE}/portfolio?user_id=${userId}`)
      const data = await response.json()
      
      if (data.success && data.portfolio && data.portfolio.length > 0) {
        // Convert backend format to frontend format
        const loadedPositions = data.portfolio.map(stock => ({
          id: stock.ticker + '_' + Date.now(),
          ticker: stock.ticker,
          quantity: stock.quantity.toString(),
          entryPrice: stock.avg_price.toString(),
          currentPrice: stock.avg_price.toString() // Default to entry price
        }))
        
        setPositions(loadedPositions)
        console.log('✅ Portfolio loaded:', loadedPositions.length, 'positions')
      }
    } catch (error) {
      console.error('Error loading portfolio:', error)
    }
  }

  const loadChatHistoryFromBackend = async () => {
    try {
      const response = await fetch(`${API_BASE}/chat/history?user_id=${userId}`)
      const data = await response.json()
      
      if (data.success && data.history && data.history.length > 0) {
        const loadedMessages = data.history.map(chat => [
          { role: 'user', content: chat.message },
          { role: 'assistant', content: chat.response }
        ]).flat()
        
        setMessages(prev => [...prev, ...loadedMessages])
        console.log('✅ Chat history loaded:', data.history.length, 'messages')
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
    }
  }

  const savePositionToBackend = async (position) => {
    try {
      await fetch(`${API_BASE}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ticker: position.ticker,
          quantity: parseInt(position.quantity),
          price: parseFloat(position.entryPrice)
        })
      })
      console.log('✅ Saved to backend:', position.ticker)
    } catch (error) {
      console.error('Error saving:', error)
    }
  }

  const deletePositionFromBackend = async (ticker) => {
    try {
      await fetch(`${API_BASE}/portfolio/${ticker}?user_id=${userId}`, {
        method: 'DELETE'
      })
      console.log('✅ Deleted from backend:', ticker)
    } catch (error) {
      console.error('Error deleting:', error)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(value)
  }

  const addPosition = () => {
    if (newPosition.ticker && newPosition.quantity && newPosition.entryPrice && newPosition.currentPrice) {
      const position = { ...newPosition, id: Date.now() }
      setPositions([...positions, position])
      
      // ✅ Save to backend
      savePositionToBackend(position)
      
      setNewPosition({ ticker: '', quantity: '', entryPrice: '', currentPrice: '' })
      
      const positionMsg = {
        role: 'assistant',
        content: `✅ Đã thêm vị thế ${newPosition.ticker}!\n\nBạn có thể hỏi tôi về:\n- Nên giữ hay bán ${newPosition.ticker}?\n- Rủi ro của danh mục hiện tại?\n- Chiến lược phân bổ vốn?`
      }
      setMessages(prev => [...prev, positionMsg])
    }
  }

  const removePosition = (id) => {
    const position = positions.find(p => p.id === id)
    setPositions(positions.filter(p => p.id !== id))
    
    if (position) {
      // ✅ Delete from backend
      deletePositionFromBackend(position.ticker)
      
      const msg = {
        role: 'assistant',
        content: `Đã xóa vị thế ${position.ticker}. Danh mục của bạn đã được cập nhật.`
      }
      setMessages(prev => [...prev, msg])
    }
  }

  const analyzePortfolio = () => {
    if (!capital || positions.length === 0) {
      const errorMsg = {
        role: 'assistant',
        content: '⚠️ Vui lòng nhập vốn và thêm ít nhất một vị thế để tôi có thể phân tích!'
      }
      setMessages(prev => [...prev, errorMsg])
      return
    }

    setLoading(true)

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

      let analysis = `📊 **PHÂN TÍCH DANH MỤC ĐẦU TƯ**\n\n`
      analysis += `💰 **Tổng quan:**\n`
      analysis += `- Vốn: ${formatCurrency(parseFloat(capital))}\n`
      analysis += `- Đã đầu tư: ${formatCurrency(totalInvested)} (${capitalUsage.toFixed(1)}%)\n`
      analysis += `- Giá trị hiện tại: ${formatCurrency(currentValue)}\n`
      analysis += `- Lãi/Lỗ: ${formatCurrency(pnl)} (${pnl >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%)\n\n`

      analysis += `🎯 **Đánh giá rủi ro:**\n`
      if (capitalUsage > 80) {
        analysis += `⚠️ **Mức rủi ro: CAO**\n`
        analysis += `- Bạn đang sử dụng ${capitalUsage.toFixed(1)}% vốn\n`
        analysis += `- Khuyến nghị: Giảm bớt vị thế để duy trì thanh khoản\n`
        analysis += `- Nên giữ ít nhất 20% vốn dự phòng\n\n`
      } else if (capitalUsage > 50) {
        analysis += `⚡ **Mức rủi ro: TRUNG BÌNH**\n`
        analysis += `- Mức sử dụng vốn hợp lý (${capitalUsage.toFixed(1)}%)\n`
        analysis += `- Theo dõi chặt chẽ các vị thế\n`
        analysis += `- Cân nhắc đặt stop loss cho từng mã\n\n`
      } else {
        analysis += `✅ **Mức rủi ro: THẤP**\n`
        analysis += `- Sử dụng ${capitalUsage.toFixed(1)}% vốn - an toàn\n`
        analysis += `- Vẫn còn khả năng mở thêm vị thế\n`
        analysis += `- Có thể tìm kiếm cơ hội mới\n\n`
      }

      analysis += `💡 **Khuyến nghị:**\n`
      
      positions.forEach(p => {
        const invested = parseFloat(p.quantity) * parseFloat(p.entryPrice)
        const current = parseFloat(p.quantity) * parseFloat(p.currentPrice)
        const posPnl = current - invested
        const posPnlPercent = (posPnl / invested) * 100
        
        if (posPnlPercent > 10) {
          analysis += `- **${p.ticker}**: Đang lãi ${posPnlPercent.toFixed(1)}% - Cân nhắc chốt lời một phần\n`
        } else if (posPnlPercent < -7) {
          analysis += `- **${p.ticker}**: Đang lỗ ${posPnlPercent.toFixed(1)}% - Xem xét cắt lỗ nếu xu hướng không đảo chiều\n`
        } else {
          analysis += `- **${p.ticker}**: Trong vùng an toàn (${posPnlPercent.toFixed(1)}%) - Tiếp tục theo dõi\n`
        }
      })

      const analysisMsg = {
        role: 'assistant',
        content: analysis
      }
      setMessages(prev => [...prev, analysisMsg])
      setLoading(false)
    }, 1500)
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setLoading(true)

    try {
      // ✅ Call GEMINI AI through backend (đã có sẵn)
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          message: currentInput,
          portfolio: positions.map(p => p.ticker) // Portfolio context
        })
      })

      const data = await response.json()
      
      if (data.success && data.response) {
        const assistantMessage = { role: 'assistant', content: data.response }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        throw new Error('Backend response failed')
      }
    } catch (error) {
      console.error('Error calling AI:', error)
      
      // Fallback message
      const errorMsg = {
        role: 'assistant',
        content: '⚠️ Xin lỗi, tôi gặp sự cố kết nối. Vui lòng thử lại sau!'
      }
      setMessages(prev => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-portfolio-manager">
      <div className="module-header">
        <h2>🤖 Quản trị đầu tư bằng AI</h2>
        <p>Chia sẻ danh mục của bạn và nhận tư vấn từ AI 24/7</p>
      </div>

      <div className="portfolio-grid">
        {/* Left: Portfolio Input */}
        <div className="portfolio-section">
          <div className="section-header">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
              </svg>
              Danh mục của bạn
            </h3>
          </div>

          <div className="form-group">
            <label>Tổng vốn (VND)</label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              placeholder="Nhập tổng vốn đầu tư"
            />
          </div>

          <div className="form-group">
            <label>Thêm vị thế</label>
            <div className="position-inputs">
              <input
                type="text"
                value={newPosition.ticker}
                onChange={(e) => setNewPosition({...newPosition, ticker: e.target.value.toUpperCase()})}
                placeholder="Mã (VD: VCB)"
              />
              <input
                type="number"
                value={newPosition.quantity}
                onChange={(e) => setNewPosition({...newPosition, quantity: e.target.value})}
                placeholder="Số lượng"
              />
              <input
                type="number"
                value={newPosition.entryPrice}
                onChange={(e) => setNewPosition({...newPosition, entryPrice: e.target.value})}
                placeholder="Giá mua"
              />
              <input
                type="number"
                value={newPosition.currentPrice}
                onChange={(e) => setNewPosition({...newPosition, currentPrice: e.target.value})}
                placeholder="Giá hiện tại"
              />
            </div>
            <button onClick={addPosition} className="btn-add">
              + Thêm vị thế
            </button>
          </div>

          {positions.length > 0 && (
            <>
              <div className="positions-list">
                <label>Các vị thế hiện tại ({positions.length})</label>
                {positions.map(position => {
                  const invested = parseFloat(position.quantity) * parseFloat(position.entryPrice)
                  const current = parseFloat(position.quantity) * parseFloat(position.currentPrice)
                  const pnl = current - invested
                  const pnlPercent = (pnl / invested) * 100

                  return (
                    <div key={position.id} className="position-card">
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
                      <button onClick={() => removePosition(position.id)} className="btn-remove-small">
                        ×
                      </button>
                    </div>
                  )
                })}
              </div>

              <button onClick={analyzePortfolio} className="btn-analyze" disabled={loading}>
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
                    Phân tích danh mục
                  </>
                )}
              </button>
            </>
          )}
        </div>

        {/* Right: AI Chat */}
        <div className="chat-section">
          <div className="section-header">
            <h3>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              </svg>
              Tư vấn AI (Gemini)
            </h3>
          </div>

          <div className="chat-messages-container">
            <div className="chat-messages">
              {messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  <div className="message-avatar">
                    {message.role === 'assistant' ? '🤖' : '👤'}
                  </div>
                  <div className="message-content">
                    {message.content.split('\n').map((line, i) => (
                      <p key={i} style={{ margin: line ? '0 0 8px 0' : '4px 0' }}>
                        {line}
                      </p>
                    ))}
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="message assistant">
                  <div className="message-avatar">🤖</div>
                  <div className="message-content">
                    <div className="spinner" style={{width: '20px', height: '20px', borderWidth: '2px'}}></div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={sendMessage} className="chat-input">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Đặt câu hỏi cho AI (VD: Tôi nên mua hay bán VCB?)"
                disabled={loading}
              />
              <button type="submit" disabled={loading || !input.trim()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
