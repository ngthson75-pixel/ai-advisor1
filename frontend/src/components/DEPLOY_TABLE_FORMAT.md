# ✅ **LỊCH SỬ KHUYẾN NGHỊ - TABLE FORMAT**

## 🎯 **NHỮNG GÌ ĐÃ THAY ĐỔI:**

### **1. Cards → Table Format**
```
OLD: Recommendation cards (6 cards)
NEW: Simple table (giống screenshot)
```

### **2. Thêm Tín Hiệu 06/01/2026**
```
✅ VNM: 60,700
✅ BID: 38,750
✅ CTG: 36,120
✅ POW: 12,750
✅ SAB: 45,700
✅ HNG: 6,300
```

### **3. Table Columns**
```
MÃ CK       | Mã cổ phiếu (xanh dương)
GIÁ VÀO     | Giá mua
STOP LOSS   | Cắt lỗ (đỏ)
TAKE PROFIT | Chốt lời (xanh lá)
SCORE       | Badge xanh lá
LOẠI        | Blue Chip
NGÀY        | Ngày tín hiệu
```

---

## 📊 **DỮ LIỆU:**

### **Historical Signals (06/01/2026):**
```
1. VNM - 60,700  → TP: 65,556  | SL: 57,665
2. BID - 38,750  → TP: 41,850  | SL: 36,812
3. CTG - 36,120  → TP: 39,010  | SL: 34,314
4. POW - 12,750  → TP: 13,770  | SL: 12,112
5. SAB - 45,700  → TP: 49,356  | SL: 43,415
6. HNG - 6,300   → TP: 6,804   | SL: 5,985
```

### **API Signals (13/01/2026):**
```
Fetch from: /api/signals
Display: Latest 10 signals
Combined: Historical + API signals
```

---

## 🚀 **DEPLOY (3 PHÚT):**

### **Bước 1: Replace file**
```powershell
cd C:\ai-advisor1\frontend\src\components

# Download: LandingPage_TABLE.jsx from attachment ⬆️
# Rename to: LandingPage.jsx (overwrite)
```

### **Bước 2: Push**
```powershell
cd C:\ai-advisor1

git add frontend/src/components/LandingPage.jsx
git commit -m "Update: Table format for signal history + add 06/01 signals"
git push origin main
```

### **Bước 3: Test**
```
1. Wait 10 minutes

2. Visit: https://ai-advisor.vn

3. Clear cache: Ctrl+Shift+R (x5)

4. Scroll to "Lịch sử khuyến nghị"

Expected:
✅ Table format (giống screenshot)
✅ 6 tín hiệu từ 06/01/2026
✅ + Tín hiệu mới từ API (nếu có)
✅ Blue tickers, red SL, green TP
✅ Green score badges
```

---

## 🎨 **TABLE DESIGN:**

### **Colors:**
```css
Background: Dark gradient (#1e293b → #0f172a)
Header: Dark (#0f172a)
Border: #334155
Hover: Blue tint

Ticker: #3b82f6 (blue)
Price: #e2e8f0 (white)
Stop Loss: #ef4444 (red)
Take Profit: #10b981 (green)
Score Badge: #10b981 background (green)
Type/Date: #94a3b8 (gray)
```

### **Layout:**
```
┌─────────────────────────────────────────────────┐
│ MÃ CK  │ GIÁ VÀO │ STOP LOSS │ TAKE PROFIT │ ... │
├─────────────────────────────────────────────────┤
│ VNM    │ 60,700  │ 57,665    │ 65,556      │ 75  │
│ BID    │ 38,750  │ 36,812    │ 41,850      │ 75  │
│ CTG    │ 36,120  │ 34,314    │ 39,010      │ 75  │
└─────────────────────────────────────────────────┘
```

---

## ✅ **EXPECTED RESULTS:**

### **Section "Lịch sử khuyến nghị":**

**Data:**
```
Row 1: VNM  - 60,700  → 65,556  (06/01/2026)
Row 2: BID  - 38,750  → 41,850  (06/01/2026)
Row 3: CTG  - 36,120  → 39,010  (06/01/2026)
Row 4: POW  - 12,750  → 13,770  (06/01/2026)
Row 5: SAB  - 45,700  → 49,356  (06/01/2026)
Row 6: HNG  - 6,300   → 6,804   (06/01/2026)
Row 7+: API signals (if available)
```

**Design:**
```
✅ Dark table background
✅ Blue stock codes
✅ Red stop loss
✅ Green take profit
✅ Green score badges (75)
✅ Hover effect on rows
✅ Responsive on mobile
```

---

## 🔍 **WHAT CHANGED:**

### **From Previous Version:**

**REMOVED:**
```jsx
// OLD: Card grid
<div className="recommendations-grid">
  <div className="recommendation-card">...</div>
</div>
```

**ADDED:**
```jsx
// NEW: Table
<table className="signals-table">
  <thead>...</thead>
  <tbody>
    {recommendations.map(signal => (
      <tr>
        <td className="ticker-cell">{signal.ticker}</td>
        ...
      </tr>
    ))}
  </tbody>
</table>
```

**ALSO ADDED:**
```jsx
// Historical signals data (06/01/2026)
const historicalSignals = [
  { ticker: 'VNM', entryPrice: 60700, ... },
  { ticker: 'BID', entryPrice: 38750, ... },
  ...
]

// Combine with API signals
setRecommendations([...historicalSignals, ...apiSignals])
```

---

## 📱 **RESPONSIVE:**

### **Desktop:**
```
Full table width
All columns visible
Font size: 14-16px
```

### **Mobile:**
```
Horizontal scroll
Smaller padding
Font size: 12-14px
All data still accessible
```

---

## 🔧 **TROUBLESHOOTING:**

### **Issue: Table not showing**

**Check 1: CSS loaded?**
```
F12 → Check if <style jsx> is rendered
Should see .signals-table styles
```

**Check 2: Data exists?**
```jsx
console.log(recommendations)
// Should show 6+ items
```

### **Issue: Only 6 rows**

**This is correct!** Shows historical signals (06/01).

**To add API signals:**
```powershell
# Trigger scan:
Invoke-WebRequest https://ai-advisor1-backend.onrender.com/api/scan -Method POST

# Then table will show 6 historical + new API signals
```

---

## 📞 **QUICK DEPLOY:**

```powershell
# 1. Replace
cd C:\ai-advisor1\frontend\src\components
# Download LandingPage_TABLE.jsx → Rename to LandingPage.jsx

# 2. Push
cd C:\ai-advisor1
git add frontend/src/components/LandingPage.jsx
git commit -m "Table format + 06/01 signals"
git push origin main

# 3. Test (10 mins later)
# Visit https://ai-advisor.vn
# Ctrl+Shift+R → See table!
```

---

## 🎯 **SUMMARY:**

**Format:** Cards → Simple Table ✅  
**Data:** 6 historical (06/01) + API signals ✅  
**Design:** Dark, blue/red/green colors ✅  
**Responsive:** Mobile-friendly ✅

---

**File sẵn sàng deploy!** 🚀

**Table format đơn giản, chuyên nghiệp như screenshot!** ✅
