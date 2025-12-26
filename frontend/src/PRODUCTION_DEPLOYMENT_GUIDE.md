# AI ADVISOR - PRODUCTION DEPLOYMENT GUIDE
## 3-Module Platform: Signals + Risk Shield + AI Coach

---

## 🎯 OVERVIEW

Complete production-ready platform with:
1. **Trading Signals** - PULLBACK & EMA_CROSS strategies
2. **Risk Shield** - AI-powered risk management (Gemini)
3. **AI Coach** - Behavioral coaching to prevent FOMO/Fear (Gemini)

---

## 📦 FRONTEND STRUCTURE

```
frontend/src/
├── App.jsx                    # Main app with 3 tabs
├── App.css                    # All styles
├── index.css                  # Global styles
├── components/
│   ├── SignalsModule.jsx      # Signal cards & filters
│   ├── RiskShield.jsx         # Risk analysis (Gemini AI)
│   └── AICoach.jsx            # Behavioral coach (Gemini AI)
└── services/
    └── geminiService.js       # Gemini API wrapper
```

---

## 🔑 GEMINI API SETUP

### Backend Integration (Recommended - Secure)

**Create: backend/gemini_service.py**

```python
import google.generativeai as genai
from flask import jsonify
import os

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_KEY_HERE')
genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 1.5 Flash for fast responses
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_portfolio_risk(portfolio_data):
    """
    Analyze portfolio risk using Gemini AI
    portfolio_data: { positions: [], total_capital: float }
    """
    prompt = f"""
    Bạn là chuyên gia quản lý rủi ro đầu tư chứng khoán Việt Nam.
    
    Danh mục đầu tư:
    {portfolio_data}
    
    Hãy phân tích:
    1. Tỷ lệ phân bổ vốn có hợp lý không?
    2. Rủi ro tập trung vào cổ phiếu/ngành nào?
    3. Điểm rủi ro tổng thể (0-100)
    4. 3 khuyến nghị cụ thể để giảm rủi ro
    5. Cảnh báo FOMO nếu có dấu hiệu đuổi giá
    
    Trả lời ngắn gọn, dễ hiểu, tiếng Việt.
    """
    
    try:
        response = model.generate_content(prompt)
        return {
            'success': True,
            'analysis': response.text
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def coaching_chat(user_message, context=None):
    """
    AI Coach for trading psychology
    """
    system_context = """
    Bạn là AI Coach chuyên về tâm lý giao dịch chứng khoán.
    Mục tiêu: Giúp nhà đầu tư cá nhân tránh FOMO và sợ hãi.
    
    Nguyên tắc:
    - Nhận diện cảm xúc trong tin nhắn (lo lắng, hưng phấn, hoảng loạn)
    - Đưa ra lời khuyên thực tế, không quá lạc quan
    - Nhắc nhở về quản lý vốn và cắt lỗ
    - Khuyến khích kỷ luật, kiên nhẫn
    - Ngắn gọn, dễ hiểu, tiếng Việt
    """
    
    full_prompt = f"""
    {system_context}
    
    Context (nếu có): {context or 'Không có'}
    
    Nhà đầu tư hỏi: "{user_message}"
    
    Trả lời:
    """
    
    try:
        response = model.generate_content(full_prompt)
        return {
            'success': True,
            'message': response.text
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def check_fomo_signals(signal, market_context):
    """
    Check if user is making FOMO decision
    """
    prompt = f"""
    Tín hiệu: {signal['ticker']} - {signal['strategy']}
    Entry: {signal['entry_price']}
    Market context: {market_context}
    
    Đây có phải quyết định FOMO không? Phân tích:
    1. Giá đã tăng bao nhiêu % so với đáy gần nhất?
    2. Volume có bất thường không?
    3. Điểm FOMO (0-100)
    4. Nên vào lệnh hay đợi?
    
    Trả lời ngắn gọn.
    """
    
    try:
        response = model.generate_content(prompt)
        return {
            'success': True,
            'analysis': response.text
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

### Backend API Endpoints

**Add to backend_api.py:**

```python
from gemini_service import analyze_portfolio_risk, coaching_chat, check_fomo_signals

# Risk Shield endpoint
@app.route('/api/risk/analyze', methods=['POST'])
def analyze_risk():
    data = request.json
    result = analyze_portfolio_risk(data)
    return jsonify(result)

# AI Coach endpoint
@app.route('/api/coach/chat', methods=['POST'])
def coach_chat():
    data = request.json
    message = data.get('message', '')
    context = data.get('context', None)
    result = coaching_chat(message, context)
    return jsonify(result)

# FOMO Check endpoint
@app.route('/api/risk/fomo-check', methods=['POST'])
def fomo_check():
    data = request.json
    signal = data.get('signal', {})
    market_context = data.get('market_context', '')
    result = check_fomo_signals(signal, market_context)
    return jsonify(result)
```

### Environment Variables

**Add to Render.com:**

```
GEMINI_API_KEY=AIzaSy... (your key)
```

---

## 💻 FRONTEND COMPONENTS

### 1. RiskShield.jsx

```jsx
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
```

### 2. AICoach.jsx

```jsx
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
```

---

## 🎨 UPDATED CSS

**Key additions for new modules:**

```css
/* Module Headers */
.module-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding: var(--spacing-xl);
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-xl);
}

.header-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--color-primary), var(--color-info));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

/* Risk Shield */
.risk-shield {
  animation: fadeInUp 0.6s ease-out;
}

.capital-section {
  padding: var(--spacing-xl);
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-lg);
}

.capital-input {
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-family: var(--font-mono);
  font-size: 1.25rem;
  margin-top: var(--spacing-sm);
}

.position-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.position-row input {
  padding: var(--spacing-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
}

.analyze-btn {
  width: 100%;
  padding: var(--spacing-md);
  background: linear-gradient(135deg, var(--color-success), var(--color-success-light));
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: transform var(--transition-base);
}

.analyze-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.analysis-result {
  margin-top: var(--spacing-xl);
  padding: var(--spacing-xl);
  background: var(--color-bg-card);
  border: 1px solid var(--color-success);
  border-radius: var(--radius-lg);
}

/* AI Coach */
.chat-container {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.message {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  animation: fadeInUp 0.3s ease-out;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-bg-elevated);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-bg-elevated);
  line-height: 1.6;
}

.message.user .message-content {
  background: var(--color-primary);
  color: white;
}

.typing {
  display: flex;
  gap: 0.25rem;
  padding: var(--spacing-md);
}

.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-muted);
  animation: typing 1.4s infinite;
}

.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-10px); }
}

.chat-input {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border);
}

.chat-input input {
  flex: 1;
  padding: var(--spacing-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
}

.chat-input button {
  padding: var(--spacing-md);
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  cursor: pointer;
}

.quick-tips {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
}

.quick-tips button {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--spacing-sm) var(--spacing-md);
  margin-top: var(--spacing-sm);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  cursor: pointer;
  transition: all var(--transition-base);
}

.quick-tips button:hover {
  border-color: var(--color-primary);
  background: var(--color-bg-elevated);
}
```

---

## 🚀 DEPLOYMENT STEPS

### 1. Backend Setup

```bash
cd C:\ai-advisor1\backend

# Install Gemini SDK
pip install google-generativeai --break-system-packages

# Create gemini_service.py (code above)
# Update backend_api.py with new endpoints

# Set environment variable in Render.com
GEMINI_API_KEY=YOUR_KEY_HERE

# Push to GitHub
git add .
git commit -m "Add Gemini AI integration"
git push origin main
```

### 2. Frontend Setup

```bash
cd C:\ai-advisor1\frontend

# Add logo to public folder
copy logo.png public\logo.png

# Copy all new components to src/
# Copy updated App.jsx, App.css

# Push to GitHub
git add .
git commit -m "Add 3-module UI with Gemini"
git push origin main
```

### 3. Verify

- Backend: https://ai-advisor1-backend.onrender.com/health
- Frontend: https://ai-advisor.vn
- Test all 3 tabs

---

## 💰 COSTS

```
Domain: 350k VND/year
Frontend: FREE (Cloudflare)
Backend: $7/month (84k/year) - Recommended
Gemini API: FREE (60 requests/min)

Total: ~434k VND/year (~36k/month)
```

---

## ✅ PRODUCTION CHECKLIST

- [ ] Backend Gemini integration
- [ ] 3 frontend modules
- [ ] Logo in public folder
- [ ] Environment variables set
- [ ] Backend not sleeping ($7/month)
- [ ] CORS updated
- [ ] Test all features
- [ ] Ready for 20 users!

---

## 📞 SUPPORT

Issues? Check:
1. Backend logs in Render.com
2. Browser console (F12)
3. Gemini API quota
4. CORS settings

Good luck with your 20 users! 🚀
