import { useState, useEffect, useRef } from 'react'

export default function AICoach() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Xin chào! Tôi là AI Coach của bạn. Tôi có thể giúp bạn phân tích thị trường, đánh giá tín hiệu, và tư vấn chiến lược đầu tư. Bạn cần hỗ trợ gì?'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const quickQuestions = [
    'Phân tích tín hiệu VCB',
    'Chiến lược Pullback là gì?',
    'Khi nào nên cắt lỗ?',
    'Tỷ lệ rủi ro/lợi nhuận tốt'
  ]

  const handleQuickQuestion = (question) => {
    setInput(question)
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // Simulate AI response (replace with actual Gemini API call)
    setTimeout(() => {
      let response = ''
      
      if (input.toLowerCase().includes('pullback')) {
        response = 'Chiến lược Pullback là một phương pháp giao dịch phổ biến:\n\n' +
          '📊 **Khái niệm:** Mua vào khi giá điều chỉnh (pullback) trong xu hướng tăng chính.\n\n' +
          '✅ **Ưu điểm:**\n' +
          '- Giá tốt hơn so với mua ở đỉnh\n' +
          '- Tỷ lệ Risk/Reward cao\n' +
          '- Xu hướng chính vẫn tăng\n\n' +
          '⚠️ **Lưu ý:**\n' +
          '- Cần xác nhận xu hướng chính\n' +
          '- Đặt stop loss dưới vùng hỗ trợ\n' +
          '- Chờ tín hiệu xác nhận trước khi vào lệnh'
      } else if (input.toLowerCase().includes('cắt lỗ') || input.toLowerCase().includes('stoploss')) {
        response = '🛡️ **Cắt lỗ (Stop Loss) là nguyên tắc sống còn:**\n\n' +
          '1. **Khi nào cắt lỗ?**\n' +
          '   - Giá phá vỡ stop loss đã đặt\n' +
          '   - Lý do vào lệnh không còn\n' +
          '   - Tín hiệu đảo chiều xuất hiện\n\n' +
          '2. **Mức cắt lỗ hợp lý:**\n' +
          '   - Blue Chip: 5-7%\n' +
          '   - Mid Cap: 7-10%\n' +
          '   - Penny: 10-15%\n\n' +
          '3. **Nguyên tắc vàng:**\n' +
          '   - LUÔN đặt stop loss trước khi vào lệnh\n' +
          '   - Không di chuyển stop loss xa hơn\n' +
          '   - Thua nhỏ để thắng lớn'
      } else if (input.toLowerCase().includes('vcb')) {
        response = '📈 **Phân tích VCB (Vietcombank):**\n\n' +
          '**Thông tin cơ bản:**\n' +
          '- Loại: Blue Chip\n' +
          '- Ngành: Ngân hàng\n' +
          '- Vốn hóa: Lớn\n\n' +
          '**Đánh giá:**\n' +
          '✅ Blue chip chất lượng cao\n' +
          '✅ Thanh khoản tốt\n' +
          '✅ Phù hợp đầu tư dài hạn\n\n' +
          '**Chiến lược gợi ý:**\n' +
          '- Mua khi có tín hiệu Pullback\n' +
          '- Giữ stop loss 5-7%\n' +
          '- Target: 10-15% trong 3-6 tháng'
      } else if (input.toLowerCase().includes('risk') || input.toLowerCase().includes('rủi ro')) {
        response = '⚖️ **Tỷ lệ Rủi ro/Lợi nhuận (Risk/Reward):**\n\n' +
          '**Tỷ lệ tốt:** >= 1:2\n' +
          '- Có nghĩa: Rủi ro $1 để kiếm $2\n\n' +
          '**Ví dụ:**\n' +
          '- Giá vào: 100,000\n' +
          '- Stop loss: 95,000 (rủi ro -5%)\n' +
          '- Take profit: 110,000 (lợi nhuận +10%)\n' +
          '- R/R = 5/10 = 1:2 ✅\n\n' +
          '**Lời khuyên:**\n' +
          '- Chỉ vào lệnh khi R/R >= 1:2\n' +
          '- R/R tốt không đảm bảo thắng 100%\n' +
          '- Kết hợp với các yếu tố khác'
      } else {
        response = 'Cảm ơn câu hỏi của bạn! Đây là chủ đề thú vị.\n\n' +
          'Để tôi có thể tư vấn chính xác hơn, bạn có thể:\n\n' +
          '1. Hỏi về chiến lược cụ thể (Pullback, EMA Cross)\n' +
          '2. Yêu cầu phân tích mã cổ phiếu\n' +
          '3. Tìm hiểu về quản lý rủi ro\n' +
          '4. Hỏi về khi nào nên vào/ra lệnh\n\n' +
          'Hoặc chọn một trong các câu hỏi gợi ý bên dưới! 😊'
      }

      const assistantMessage = { role: 'assistant', content: response }
      setMessages(prev => [...prev, assistantMessage])
      setLoading(false)
    }, 1000)
  }

  return (
    <div className="ai-coach">
      <div className="module-header">
        <h2>🤖 AI Coach</h2>
        <p>Trợ lý AI hỗ trợ phân tích và tư vấn đầu tư 24/7</p>
      </div>

      <div className="coach-container">
        <div className="chat-container">
          {/* Messages */}
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

          {/* Input */}
          <div className="chat-input-container">
            <div className="quick-actions">
              {quickQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickQuestion(question)}
                  className="quick-btn"
                  disabled={loading}
                >
                  {question}
                </button>
              ))}
            </div>

            <form onSubmit={sendMessage} className="chat-input-form">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Đặt câu hỏi cho AI Coach..."
                disabled={loading}
              />
              <button type="submit" className="btn-send" disabled={loading || !input.trim()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
                Gửi
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
