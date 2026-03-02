# SESSION UPDATE - AI ADVISOR MARKET DASHBOARD INTEGRATION
**Date:** 2026-02-21  
**Status:** ✅ DEPLOYED TO PRODUCTION  
**Version:** backend v3.4 · AIPortfolioManager layout v2

---

## 🎯 TÓM TẮT THAY ĐỔI

### 3 nhóm thay đổi chính:

1. **AI Chat hiểu Market Dashboard** — inject dữ liệu thị trường vào context GPT
2. **AI nhận diện Buysell Signal list** — đọc đúng danh sách cổ phiếu từ context
3. **Layout AIPortfolioManager** — Chat trên, Portfolio dưới, Tiền mặt trong tổng quan

---

## 🔧 THAY ĐỔI 1: backend_api.py → AI_SYSTEM_PROMPT

### Vấn đề cũ:
AI trả lời: *"AI ADVISOR không cung cấp chỉ số rủi ro thị trường"*

### Fix:
Thêm section `=== MARKET DASHBOARD ===` vào `AI_SYSTEM_PROMPT` với:

```python
# Các điểm then chốt trong system prompt mới:

# 1. Giải thích Market Mode và cách dùng
"""
MARKET MODE:
- BULL: Risk 0-40, allocation 80-100% → Duy trì/tăng tỷ trọng
- SIDEWAYS/THAN TRONG: Risk 41-65, allocation 40-70% → Thận trọng
- BEAR: Risk 66-100, allocation 0-30% → Phòng thủ tối đa
"""

# 2. CRITICAL instruction — tránh AI hỏi user cung cấp data
"""
⚠️ CRITICAL: Market Dashboard data is AUTOMATICALLY INJECTED into context.
NEVER ask the user to "provide" or "share" Market Dashboard data.
NEVER say "Vui lòng cung cấp dữ liệu Market Dashboard"
NEVER repeat or echo the "=== MARKET DASHBOARD ===" header in response.
The data is ALREADY in your context. Just read and use it.
"""

# 3. Hướng dẫn đọc Signal list
"""
BEFORE answering any stock question:
1. LOOK UP "=== OFFICIAL BUYSELL SIGNAL LIST ===" in context
2. CHECK if ticker appears in the "Tickers:" line
3. ONLY then determine if it is IN or NOT IN the signal list
"""
```

### Kết quả:
- ✅ AI cite: *"Theo Market Dashboard, thị trường SIDEWAYS, Risk 43/100, khuyến nghị 50%..."*
- ✅ AI nhận diện đúng cổ phiếu trong/ngoài Signal list

---

## 🔧 THAY ĐỔI 2: backend_api.py → get_portfolio_context()

### Vấn đề cũ:
`get_portfolio_context()` chỉ trả về portfolio + signal list, không có Market data.

### Fix — Inject Market Dashboard vào đầu context:

```python
def get_portfolio_context(user_id):
    """Get portfolio context with P&L + Market Dashboard data for AI advisor"""
    
    # 1. Query MarketRisk table
    latest_risk = session.query(MarketRisk).order_by(MarketRisk.date.desc()).first()
    
    # 2. Build market_context string
    market_context = "\n=== MARKET DASHBOARD (AI ADVISOR) ===\n"
    market_context += f"Market Mode: {latest_risk.market_mode}\n"
    market_context += f"Risk Score: {latest_risk.risk_score}/100\n"
    market_context += f"Khuyen nghi ty trong CP: {latest_risk.allocation}%\n"
    # ... factors ...
    market_context += "=== KET THUC MARKET DASHBOARD ===\n"
    
    # 3. Inject vào đầu context
    context = f"{market_context}\n"
    context += "DANH MUC DAU TU:\n..."
    
    # 4. So sánh tỷ trọng user vs khuyến nghị
    if stock_pct > rec_alloc + 10:
        context += f"[CANH BAO] Đang giữ {stock_pct:.1f}% CP, khuyến nghị {rec_alloc}%..."
```

### Format Signal list mới (rõ ràng hơn cho AI):

```
# Cũ - AI không nhận ra:
CO PHIEU TRONG BUYSELL SIGNAL SYSTEM:
ABI, ASG, VCB...

# Mới - AI đọc được:
=== OFFICIAL BUYSELL SIGNAL LIST ===
Total: 53 stocks.
Tickers: ABI, ASG, ASP, ..., VCB, VCI...
=== END BUYSELL SIGNAL LIST ===
```

### Fix thêm:
- `signal_tickers` chỉ lấy `action='BUY'` (trước lấy tất cả kể cả SELL)

---

## 🔧 THAY ĐỔI 3: AIPortfolioManager.jsx — Layout mới

### Layout cũ:
```
[Chat AI] | [Portfolio]   ← 2 cột ngang, khó dùng mobile
```

### Layout mới:
```
[Market Mode Badge]          ← header nhỏ
[AI CHAT — full width]       ← ưu tiên trên cùng, 420px scroll
  [Quick Prompts]
  [Input box]
[DANH MỤC — full width]     ← bên dưới
  [4 Summary Cards]          ← Tổng tài sản | CP | Tiền mặt | Lãi/Lỗ
  [Allocation Bar]           ← so sánh vs Market Dashboard
  [Nút nhập tiền mặt]
  [Form thêm CP]
  [Bảng danh sách CP]
```

### 4 Summary Cards (FIX tiền mặt không hiển thị):

| Card | Nội dung |
|------|----------|
| Tổng tài sản | CP + Tiền mặt |
| Cổ phiếu | Giá trị + % tổng tài sản |
| **Tiền mặt** ← mới | Số tiền + % tổng tài sản, click để sửa |
| Lãi/Lỗ | Màu đỏ/xanh theo P&L |

### Allocation Bar:
- Bar gradient = tỷ lệ CP hiện tại
- Đường kẻ dọc màu = khuyến nghị từ Market Dashboard
- Màu theo mode: BULL=xanh lá, SIDEWAYS=vàng, BEAR=đỏ

### Mobile responsive:
```css
@media (max-width: 600px) {
  /* Form thêm CP: 3 input → 2 cột */
  grid-template-columns: 1fr 1fr;
  button: grid-column: 1 / -1;  /* full width */
}
```

---

## 🐛 DEBUG ENDPOINT (tạm thời, xóa trước launch)

```
GET /api/debug/context?user_id=1
```

Response:
```json
{
  "has_market_dashboard": true,
  "context_preview": "=== MARKET DASHBOARD...",
  "signal_count": 53,
  "version": "3.4"
}
```

⚠️ **Nhớ xóa endpoint này trước khi marketing launch** — nó expose signal list cho bất kỳ ai.

---

## 🚀 DEPLOYMENT HISTORY

| Thời gian | Thay đổi | Branch |
|-----------|----------|--------|
| 2026-02-21 sáng | backend_api.py v3.4 (Market Dashboard context) | main |
| 2026-02-21 trưa | Fix system prompt — AI không hỏi user cung cấp data | main |
| 2026-02-21 chiều | Fix Signal list format `=== OFFICIAL BUYSELL SIGNAL LIST ===` | main |
| 2026-02-21 chiều | AIPortfolioManager.jsx — layout mới | main |
| 2026-02-21 cuối | Cleanup backup files (3739 dòng xóa) | staging + main |

---

## 🧹 REPO CLEANUP

Đã xóa các file rác tích lũy:
- `AIPortfolioManager_OLD1~10.jsx`
- `backend_api_OLD*.py`, `backend_api_Copydd*.py`
- `backend_api_BACKUP*.py`

**Lý do:** File rác gây merge conflict khi sync staging ↔ main.

---

## 📋 GIT WORKFLOW SỰ CỐ & GIẢI PHÁP

### Sự cố hôm nay:
Staging branch bị **drift** so với main do nhiều lần cherry-pick và push trực tiếp lên main → merge conflict khi sync.

### Giải pháp một lần:
```powershell
git checkout staging
git reset --hard origin/main
git push origin staging --force
```

### Quy trình chuẩn (giữ nguyên):
```
local → staging → test → merge vào main (production)
```

### Chỉ dùng reset ngược khi:
Staging bị hỏng/drift nghiêm trọng, không đáng giải quyết conflict thủ công.

---

## ✅ KIỂM TRA SAU DEPLOY

```powershell
# 1. Verify backend version
Invoke-RestMethod "https://ai-advisor1-backend.onrender.com/"
# version: "3.4 (Market Dashboard Context) - 2026-02-21"

# 2. Test AI chat hiểu market
$body = @{user_id=1; message="Thi truong hien tai the nao?"} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "https://ai-advisor1-backend.onrender.com/api/chat" -Method POST -Body $body -ContentType "application/json"
$r.response
# Kỳ vọng: cite Market Mode, Risk Score, allocation %

# 3. Test AI nhận diện Signal list
$body = @{user_id=1; message="VCB co trong Buysell Signal khong?"} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "https://ai-advisor1-backend.onrender.com/api/chat" -Method POST -Body $body -ContentType "application/json"
$r.response
# Kỳ vọng: "VCB CÓ trong danh sách Buysell Signal..."
```

---

## 🔮 TODO TRƯỚC MARKETING LAUNCH

- [ ] Xóa `/api/debug/context` endpoint khỏi `backend_api.py`
- [ ] Cập nhật market risk mới nhất (hiện data ngày 2026-02-15)
- [ ] Test toàn bộ flow trên mobile thực tế
