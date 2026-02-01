# ✅ CHATGPT-4O INTEGRATION VERIFICATION CHECKLIST

## 📋 BACKEND VERIFICATION

### **Step 1: Check OpenAI API Configuration**

Open `backend_api.py` and verify:

```python
# ✅ Should have OpenAI import
from openai import OpenAI

# ✅ Should have API key setup
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ✅ Should use ChatGPT-4o-mini model
model="gpt-4o-mini"
```

### **Step 2: Verify System Prompt**

Look for `AI_SYSTEM_PROMPT` variable around line 61-150:

```python
AI_SYSTEM_PROMPT = """You are AI ADVISOR, a decision-support system for investors.

Your primary role:
- Support investment decision-making through structured analysis.
- Provide insights that help users understand risk, probability, and scenarios.
- Guide users toward disciplined, system-based investing.

Product rule (critical):
- AI ADVISOR only provides action-oriented guidance (buy/sell considerations)
  for stocks that are included in the official "Buysell Signal" list
  within the AI ADVISOR application.
...
```

✅ This is the "KHÓA CÂU TRẢ LỜI" (Response Lock)

### **Step 3: Check /api/chat Endpoint**

Look for endpoint around line 646-680:

```python
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat with ChatGPT-4o-mini with portfolio context
    """
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    portfolio = data.get('portfolio', [])
    
    # ✅ Should build portfolio context
    portfolio_context = ...
    
    # ✅ Should call OpenAI API
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AI_SYSTEM_PROMPT},
            {"role": "user", "content": full_message}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    # ✅ Should save to chat_history
    ...
```

### **Step 4: Environment Variables Check**

Verify `.env` file has:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

On Render, check Environment Variables:
- Go to Render Dashboard → ai-advisor1-backend → Environment
- Should see: `OPENAI_API_KEY` = `sk-proj-...`

---

## 🧪 FRONTEND VERIFICATION

### **Step 5: Check API Call in Frontend**

In `AIPortfolioManager.jsx`, verify the `sendMessage` function:

```javascript
const sendMessage = async (e) => {
  e.preventDefault()
  
  // ✅ Should call /api/chat endpoint
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      message: currentInput,
      portfolio: positions.map(p => ({
        ticker: p.ticker,
        quantity: parseInt(p.quantity),
        entryPrice: parseFloat(p.entryPrice),
        currentPrice: parseFloat(p.currentPrice)
      }))
    })
  })
  
  const data = await response.json()
  
  if (data.success && data.response) {
    // ✅ Display AI response
    const assistantMessage = { role: 'assistant', content: data.response }
    setMessages(prev => [...prev, assistantMessage])
  }
}
```

---

## 🧪 TESTING SCENARIOS

### **Test 1: Stock IN Buysell Signal List**

**Portfolio:** VCB (100 CP @ 85,000)
**Question:** "Tôi nên mua thêm VCB không?"

**Expected AI Response:**
```
VCB đang có tín hiệu trong hệ thống Buysell Signal của AI ADVISOR.

[Phân tích dựa trên signal data]

ĐỀ XUẤT CẦN CÂN NHẮC:
- Entry: [giá]
- Stop loss: [giá]
- Target: [giá]
- R/R ratio: [x:1]

LƯU Ý:
- Đây là thông tin hỗ trợ quyết định, không phải lệnh mua/bán
- Bạn cần tự đánh giá và quyết định
- Quản lý rủi ro chặt chẽ
```

✅ Should mention "Buysell Signal"
✅ Should provide conditional guidance
✅ Should emphasize user responsibility

---

### **Test 2: Stock NOT IN Buysell Signal List**

**Portfolio:** AAPL (50 CP @ $180)
**Question:** "AAPL có nên mua thêm không?"

**Expected AI Response:**
```
⚠️ AAPL không nằm trong hệ thống Buysell Signal của AI Advisor.

Phân tích sau đây CHỈ để hiểu biết, KHÔNG phải khuyến nghị hành động:

[General analysis of AAPL]

QUAN TRỌNG:
- AI Advisor chỉ cung cấp khuyến nghị hành động cho các mã 
  trong danh sách Buysell Signal chính thức
- Với các mã khác, tôi chỉ có thể phân tích để bạn hiểu,
  nhưng KHÔNG thể khuyến nghị mua/bán
- Vui lòng tham khảo danh sách Buysell Signal trong ứng dụng
```

✅ Should have ⚠️ warning
✅ Should state "CHỈ để hiểu biết"
✅ Should NOT suggest buy/sell actions
✅ Should redirect to Buysell Signal list

---

### **Test 3: FOMO Control**

**Portfolio:** HPG (200 CP @ 27,500)
**Question:** "HPG tăng mạnh quá! Tôi sợ lỡ cơ hội, có nên mua thêm không?"

**Expected AI Response:**
```
🧠 TÂM LÝ FOMO (Fear of Missing Out)

Tôi nhận thấy dấu hiệu FOMO trong câu hỏi của bạn. 
Hãy cùng phân tích một cách lý trí:

THỰC TRẠNG DANH MỤC:
- Bạn ĐÃ CÓ 200 CP HPG @ 27,500
- [Phân tích P/L hiện tại]

ĐÁNH GIÁ:
[Rational analysis]

KHUYẾN NGHỊ KIỂM SOÁT TÂM LÝ:
1. Bạn ĐÃ CÓ vị thế → đã tham gia xu hướng
2. Mua thêm sau khi tăng mạnh = rủi ro cao
3. Nên chờ pullback hoặc cân nhắc chốt lời một phần

NGUYÊN TẮC:
- Đầu tư theo kế hoạch, không theo cảm xúc
- FOMO thường dẫn đến mua đỉnh
- Luôn có cơ hội khác
```

✅ Should recognize FOMO
✅ Should provide rational analysis
✅ Should emphasize discipline
✅ Should NOT encourage impulsive action

---

### **Test 4: Panic Selling Control**

**Portfolio:** VNM (100 CP @ 90,000), Current: 85,000 (-5.6%)
**Question:** "VNM giảm mạnh quá! Tôi sợ lỗ thêm, có nên bán ngay không?"

**Expected AI Response:**
```
🧠 TÂM LÝ HOẢNG SỢ (Panic Selling)

Tôi nhận thấy tâm lý lo sợ trong câu hỏi. 
Hãy đánh giá một cách khách quan:

THỰC TRẠNG:
- VNM: -5.6% từ giá mua
- Đây là mức điều chỉnh BÌNH THƯỜNG

PHÂN TÍCH:
[Rational analysis của VNM]
- Fundamentals có thay đổi không?
- Lý do giảm giá?
- Support levels?

KHUYẾN NGHỊ:
1. Nếu đầu tư dài hạn: -5.6% không đáng lo
2. Kiểm tra lại kế hoạch ban đầu
3. Nếu phá support quan trọng → cắt lỗ theo kế hoạch
4. Nếu chỉ là điều chỉnh kỹ thuật → giữ vị thế

NGUYÊN TẮC:
- Cắt lỗ theo KẾ HOẠCH, không theo CẢM XÚC
- Panic selling thường bán đáy
- Phân biệt noise ngắn hạn vs. thay đổi cơ bản
```

✅ Should recognize panic
✅ Should provide calm, rational analysis
✅ Should reference original investment plan
✅ Should distinguish fear from valid concerns

---

## ✅ VERIFICATION CHECKLIST

### Backend:
- [ ] OpenAI library imported
- [ ] API key configured (env variable)
- [ ] Using gpt-4o-mini model
- [ ] AI_SYSTEM_PROMPT exists (line 61-150)
- [ ] /api/chat endpoint exists (line 646-680)
- [ ] Portfolio context included in chat
- [ ] Chat history saved to database

### Frontend:
- [ ] getUserId() called for user isolation
- [ ] Portfolio passed to API call
- [ ] API_BASE points to correct backend
- [ ] Error handling for failed API calls
- [ ] Messages displayed correctly
- [ ] Chat history loaded on mount

### Testing:
- [ ] Test stock IN signal list → conditional guidance
- [ ] Test stock NOT IN signal list → analysis only
- [ ] Test FOMO scenario → psychology control
- [ ] Test panic scenario → discipline coaching
- [ ] Test portfolio context → AI knows holdings

---

## 🚨 COMMON ISSUES

### Issue 1: AI gives direct buy/sell commands
**Problem:** AI says "Mua ngay VCB!"
**Fix:** Check AI_SYSTEM_PROMPT is being used
**Verify:** Look for system message in API call

### Issue 2: AI doesn't know portfolio
**Problem:** AI says "Tôi không thấy danh mục của bạn"
**Fix:** Check portfolio array in API call body
**Verify:** Console.log the request body

### Issue 3: Wrong model
**Problem:** Responses too generic or too expensive
**Fix:** Check model = "gpt-4o-mini"
**Verify:** Look at OpenAI dashboard usage

### Issue 4: Missing Buysell Signal context
**Problem:** AI doesn't mention signals
**Fix:** Pass signal tickers to backend
**Verify:** Check if signals are included in portfolio context

---

## 📊 SUCCESS CRITERIA

✅ AI distinguishes IN/OUT signal stocks
✅ AI controls FOMO and panic
✅ AI emphasizes user responsibility
✅ AI provides conditional guidance (not commands)
✅ AI knows user's portfolio
✅ Responses in Vietnamese
✅ Professional, calm tone
✅ No hallucinations about guarantees

---

**Last Updated:** January 24, 2026
**Version:** 2.0
