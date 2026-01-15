# 🎯 CẬP NHẬT UI + AI SYSTEM PROMPT

## 📋 **TỔNG QUAN CẬP NHẬT:**

### **1. UI Updates (Frontend):**
✅ Thêm hướng dẫn dưới tiêu đề "Danh Mục Đầu Tư"
✅ Thêm hướng dẫn dưới "Quản lý danh mục với phân tích AI"

**Text mới:**
```
Hãy cập nhật danh mục của quý vị vào đây và hỏi AI để 
AI tư vấn và hỗ trợ kiểm soát tâm lý tránh FOMO và HOẢNG SỢ.
```

### **2. AI System Prompt (Backend):**
✅ Strict investment guidance rules
✅ Phân biệt stocks IN vs NOT IN "Buysell Signal list"
✅ KHÔNG đưa ra gợi ý hành động cho stocks ngoài signal list
✅ Kiểm soát FOMO và PANIC SELLING
✅ Professional, disciplined tone
✅ Vietnamese language support

---

## 🚀 **DEPLOY (10 PHÚT):**

### **BƯỚC 1: Update Frontend (5 phút)**

```powershell
cd C:\ai-advisor1\frontend\src\components

# Download AIPortfolioManager_UPDATED.jsx from attachment
# Rename to: AIPortfolioManager.jsx (overwrite old file)

# Verify changes:
Select-String -Path AIPortfolioManager.jsx -Pattern "FOMO và HOẢNG SỢ"
# Should return 2 lines with the new text
```

---

### **BƯỚC 2: Update Backend (5 phút)**

```powershell
cd C:\ai-advisor1

# Download backend_api_UPDATED_AI_PROMPT.py from attachment
# Rename to: backend_api.py (overwrite old file)

# Verify changes:
Select-String -Path backend_api.py -Pattern "AI_SYSTEM_PROMPT"
# Should return the new strict prompt definition
```

---

### **BƯỚC 3: Deploy Both (5 phút)**

```powershell
cd C:\ai-advisor1

# Add both files:
git add frontend/src/components/AIPortfolioManager.jsx backend_api.py

# Commit:
git commit -m "Update: Add UI guidance text + strict AI system prompt"

# Push:
git push origin main

# Wait:
# - Backend: 7 minutes (Render)
# - Frontend: 10 minutes (Cloudflare Pages)
```

---

### **BƯỚC 4: Test (5 phút)**

**Test Frontend:**
```
1. Wait 10 minutes sau push
2. Visit: https://ai-advisor.vn
3. Ctrl+Shift+R (x5 clear cache)
4. Tab: "Quản trị đầu tư bằng AI"

Expected:
✅ Dưới tiêu đề "Danh Mục Đầu Tư":
   Text: "Hãy cập nhật danh mục của quý vị vào đây..."

✅ Dưới "Quản lý danh mục với phân tích AI":
   Text: "Hãy cập nhật danh mục của quý vị vào đây..."
```

**Test AI Chat:**
```
1. Add stock VCB to portfolio
2. Chat: "Tôi nên mua thêm VCB không?"

Expected AI Response (if VCB in Buysell Signal):
- Discusses signal status
- Risk conditions
- System-based considerations
- NO explicit buy/sell command
- Emphasizes user responsibility

Expected AI Response (if VCB NOT in Signal):
- "VCB currently not part of the AI ADVISOR Buysell Signal system"
- Analysis for understanding only
- NO action guidance
- Redirects to Buysell Signal list

3. Chat: "Tôi sợ quá, có nên bán không?"

Expected AI Response:
- Calm, rational analysis
- Check investment plan
- Distinguish emotion vs fundamentals
- Support disciplined decision
- Control FOMO/PANIC
```

---

## 🎯 **KEY CHANGES:**

### **Frontend (AIPortfolioManager.jsx):**

**Line 45-51 (Added):**
```jsx
<p style={{ 
  fontSize: '14px', 
  color: '#94a3b8',
  margin: '10px 0 0 0',
  lineHeight: '1.5'
}}>
  Hãy cập nhật danh mục của quý vị vào đây và hỏi AI để AI tư vấn và hỗ trợ kiểm soát tâm lý tránh FOMO và HOẢNG SỢ.
</p>
```

**Line 334-341 (Added):**
```jsx
<p style={{ 
  fontSize: '13px', 
  color: '#94a3b8',
  marginBottom: '15px',
  lineHeight: '1.5'
}}>
  Hãy cập nhật danh mục của quý vị vào đây và hỏi AI để AI tư vấn và hỗ trợ kiểm soát tâm lý tránh FOMO và HOẢNG SỢ.
</p>
```

---

### **Backend (backend_api.py):**

**Line 40-160 (New AI_SYSTEM_PROMPT):**

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
- For all other stocks, AI ADVISOR may analyze and explain,
  but must NOT suggest or imply any investment action.

Core principles:
1. You do NOT provide direct buy/sell commands outside the Buysell Signal list.
2. You do NOT promise profits or guaranteed outcomes.
3. You do NOT encourage speculation, gambling, or impulsive behavior.
4. You prioritize capital protection, risk management, and discipline.
5. You clearly distinguish between:
   - Analysis-only stocks
   - System-approved Buysell Signal stocks
...
(120+ lines of strict rules)
```

**Key Features:**
- ✅ Distinguishes IN/OUT Buysell Signal stocks
- ✅ Mandatory phrasing for non-signal stocks
- ✅ Behavior rules by stock type
- ✅ FOMO & PANIC control guidance
- ✅ Professional, neutral tone
- ✅ Vietnamese language default

---

## 🔍 **AI BEHAVIOR EXAMPLES:**

### **Example 1: Stock IN Buysell Signal (VCB)**

**User:** "Tôi nên mua VCB không?"

**AI Response (Good):**
```
VCB đang có tín hiệu trong hệ thống Buysell Signal của AI ADVISOR.

PHÂN TÍCH TÍN HIỆU:
- Trend: Uptrend ngắn hạn
- Momentum: RSI 65 (trung bình)
- Valuation: P/E 12.5 (hợp lý cho ngân hàng)

RỦI RO & ĐIỀU KIỆN VÔ HIỆU:
- Stop loss: 85,000 VND
- Nếu phá vỡ mức hỗ trợ → Signal không còn hiệu lực
- Risk/Reward ratio: 1:2

LƯU Ý:
- Đây là tín hiệu dựa trên hệ thống, không phải lời khuyên đầu tư
- Quyết định cuối cùng thuộc về quý vị
- Hãy cân nhắc kỹ rủi ro trước khi hành động
```

---

### **Example 2: Stock NOT IN Signal (MBB)**

**User:** "Tôi nên mua MBB không?"

**AI Response (Good):**
```
⚠️ MBB hiện KHÔNG THUỘC hệ thống Buysell Signal của AI ADVISOR.

Do đó, phân tích dưới đây chỉ để hiểu biết, KHÔNG phải hướng dẫn hành động.

PHÂN TÍCH (CHỈ ĐỂ THAM KHẢO):
- Fundamentals: P/E 8.5, ROE 18% (tốt)
- Technical: Đang sidways, chưa có breakout rõ ràng
- Risks: Thanh khoản thấp hơn VCB

TẠI SAO KHÔNG TRONG SIGNAL LIST?
- Chưa đáp ứng đủ tiêu chí của hệ thống
- Volume hoặc momentum chưa đủ mạnh
- Cần thêm xác nhận từ các chỉ báo khác

GỢI Ý:
Nếu quý vị muốn có hướng dẫn hành động, hãy kiểm tra danh sách 
Buysell Signal trong ứng dụng để xem các cổ phiếu được hệ thống 
phê duyệt.
```

---

### **Example 3: FOMO Control**

**User:** "VHM tăng 5% hôm nay, tôi phải mua ngay không?"

**AI Response (Good):**
```
Tôi hiểu quý vị đang cảm thấy FOMO (fear of missing out) khi thấy 
VHM tăng mạnh.

PHÂN TÍCH LÝ TRÍ:
- VHM KHÔNG THUỘC Buysell Signal hiện tại
- Tăng giá 1 ngày không đồng nghĩa với cơ hội đầu tư
- Mua vì FOMO thường dẫn đến mua đắt, bán rẻ

CÂU HỎI ĐỂ TỰ KIỂM TRA:
1. VHM có phù hợp với kế hoạch đầu tư của tôi không?
2. Tôi đã nghiên cứu kỹ về VHM chưa?
3. Tôi có kế hoạch cắt lỗ rõ ràng không?
4. Tôi đang mua vì phân tích hay vì cảm xúc?

KHUYẾN NGHỊ:
- Hãy bình tĩnh, đừng để cảm xúc chi phối
- Quay lại danh sách Buysell Signal
- Chỉ hành động với cổ phiếu có tín hiệu hệ thống
- Kỷ luật > Cảm xúc
```

---

### **Example 4: PANIC Control**

**User:** "Thị trường giảm mạnh, tôi có nên bán hết không?"

**AI Response (Good):**
```
Tôi hiểu quý vị đang cảm thấy HOẢNG SỢ (panic) khi thị trường giảm.

PHÂN TÍCH LÝ TRÍ:
1. Thị trường giảm là phần bình thường của chu kỳ
2. Bán vì sợ hãi thường là quyết định tồi nhất
3. Hãy xem lại kế hoạch và stop loss của từng cổ phiếu

CÂU HỎI ĐỂ TỰ KIỂM TRA:
- Có cổ phiếu nào chạm stop loss chưa?
- Fundamentals của các cổ phiếu có thay đổi không?
- Tôi đang bán vì sợ hãi hay vì phân tích?

HÀNH ĐỘNG ĐỀ XUẤT:
1. Kiểm tra từng cổ phiếu một:
   - Nếu chạm stop loss → Cắt lỗ theo kế hoạch
   - Nếu chưa chạm → Giữ và theo dõi
2. KHÔNG bán hết vì cảm xúc
3. Đây có thể là cơ hội mua thêm (nếu có tín hiệu)

LƯU Ý:
Quyết định cuối cùng của quý vị, nhưng hãy dựa trên KẾ HOẠCH, 
không phải SỢ HÃI.
```

---

## ✅ **CHECKLIST:**

### **Deploy:**
- [ ] Download 2 files UPDATED
- [ ] Replace AIPortfolioManager.jsx
- [ ] Replace backend_api.py
- [ ] Verify changes (Select-String)
- [ ] Git add, commit, push
- [ ] Wait 10 mins for deploys

### **Test Frontend:**
- [ ] Visit website + clear cache
- [ ] See guidance text under titles (x2)
- [ ] Text mentions "FOMO và HOẢNG SỢ"

### **Test AI Chat:**
- [ ] Add VCB to portfolio
- [ ] Ask about VCB → Check response
- [ ] Ask about non-signal stock → Check response
- [ ] Test FOMO question → Check control response
- [ ] Test PANIC question → Check control response
- [ ] AI responds in Vietnamese ✅
- [ ] AI is professional, not hype ✅
- [ ] AI distinguishes signal vs non-signal ✅

---

## 🎯 **EXPECTED RESULTS:**

### **UI:**
```
Homepage → Tab "Quản trị đầu tư bằng AI"

Header:
  📈 Danh Mục Đầu Tư
  Hãy cập nhật danh mục của quý vị vào đây và hỏi AI 
  để AI tư vấn và hỗ trợ kiểm soát tâm lý tránh FOMO và HOẢNG SỢ.
  
Chat Section:
  💬 Quản lý danh mục với phân tích AI
  Hãy cập nhật danh mục của quý vị vào đây và hỏi AI 
  để AI tư vấn và hỗ trợ kiểm soát tâm lý tránh FOMO và HOẢNG SỢ.
```

### **AI Behavior:**
```
IN Signal List:
✅ Discusses signal status
✅ Risk conditions
✅ System-based considerations
❌ NO explicit buy/sell commands
✅ Emphasizes user responsibility

NOT IN Signal List:
✅ Analysis only
✅ Clear "NOT in Buysell Signal" statement
❌ NO action guidance
✅ Redirects to signal list

FOMO/PANIC Control:
✅ Calm, rational analysis
✅ Checks investment plan
✅ Distinguishes emotion vs fundamentals
✅ Supports disciplined decisions
```

---

## 📞 **QUICK COMMANDS:**

```powershell
# Deploy:
cd C:\ai-advisor1
git add frontend/src/components/AIPortfolioManager.jsx backend_api.py
git commit -m "Update: UI guidance + strict AI prompt"
git push origin main

# Verify frontend:
Select-String -Path frontend/src/components/AIPortfolioManager.jsx -Pattern "FOMO"

# Verify backend:
Select-String -Path backend_api.py -Pattern "AI_SYSTEM_PROMPT"

# Check deployment:
# Render: https://dashboard.render.com
# Cloudflare: https://dash.cloudflare.com
```

---

## 🎉 **SUMMARY:**

**Cập nhật:**
1. ✅ UI: Thêm 2 dòng hướng dẫn về FOMO/HOẢNG SỢ
2. ✅ AI: Strict system prompt với 120+ lines rules
3. ✅ AI: Phân biệt signal vs non-signal stocks
4. ✅ AI: Kiểm soát FOMO & PANIC
5. ✅ AI: Professional, disciplined tone

**Kết quả:**
- Người dùng hiểu rõ mục đích của AI chat
- AI không "bán hàng" hoặc encourage speculation
- AI hỗ trợ kỷ luật đầu tư, không phải cảm xúc
- Giảm rủi ro pháp lý (không đưa ra lời khuyên đầu tư trực tiếp)
- Tăng giá trị cho Buysell Signal list (official guidance source)

---

**Deploy ngay nhé!** 🚀

Sau khi deploy, test kỹ AI chat để đảm bảo behavior đúng như mong đợi!
