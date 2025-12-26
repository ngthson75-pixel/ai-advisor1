import { useState, useEffect, useRef } from 'react'

export default function AICoach() {
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: 'Xin chào! Tôi là AI Coach của bạn. Hãy chia sẻ cảm xúc hoặc quyết định giao dịch, tôi sẽ giúp bạn quản lý tâm lý đầu tư. 💪'
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/coach/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          context: messages.slice(-3) // Last 3 messages for context
        })
      })
      const data = await response.json()
      
      if (data.success) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message
        }])
      }
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-coach">
      <div className="module-header">
        <div className="header-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
          </svg>
        </div>
        <div>
          <h2>AI Coach</h2>
          <p>Huấn luyện tâm lý giao dịch - Tránh FOMO & Sợ hãi</p>
        </div>
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'assistant' ? '🤖' : '👤'}
              </div>
              <div className="message-content">
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Chia sẻ cảm xúc hoặc quyết định của bạn..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Quick Tips */}
      <div className="quick-tips">
        <h4>💡 Câu hỏi gợi ý:</h4>
        <button onClick={() => setInput('Tôi thấy cổ phiếu tăng mạnh, có nên vào không?')}>
          Cổ phiếu tăng mạnh, vào được không?
        </button>
        <button onClick={() => setInput('Tôi đang lỗ 20%, có nên cắt lỗ không?')}>
          Đang lỗ 20%, cắt lỗ hay giữ?
        </button>
        <button onClick={() => setInput('Làm sao để không FOMO khi thấy người khác lãi?')}>
          Làm sao tránh FOMO?
        </button>
      </div>
    </div>
  )
}