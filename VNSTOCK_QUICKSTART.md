# 🚀 VNSTOCK QUICKSTART - UPDATED

## ⚠️ QUAN TRỌNG: VNSTOCK ĐÃ CẬP NHẬT

### **Thay đổi:**
- ❌ **CŨ**: `vnstock3` (deprecated)
- ✅ **MỚI**: `vnstock` (v3.3.0+)

### **Lý do:**
Thư viện `vnstock3` đã được hợp nhất với tên gọi `vnstock`. 
Phiên bản mới nhất 3.3.0+ đã có mặt.

---

## 🚀 CÀI ĐẶT (5 PHÚT)

### **Bước 1: Uninstall vnstock3 (nếu đã cài)**

```powershell
pip uninstall vnstock3 -y
```

### **Bước 2: Install vnstock mới**

```powershell
pip install vnstock --upgrade
```

### **Bước 3: Verify version**

```powershell
pip show vnstock
```

**Output:**
```
Name: vnstock
Version: 3.3.0 (hoặc cao hơn)
Summary: Vietnam Stock Market Analysis Library
```

### **Bước 4: Test**

```powershell
cd C:\ai-advisor1
python scripts/fetch_vnstock.py
```

**Kết quả mong đợi:**
```json
{
  "success": true,
  "data": [
    {
      "code": "VNM",
      "price": 86500,
      "change": 1300,
      "changePercent": 1.52,
      ...
    }
  ]
}
```

---

## 📊 VNSTOCK v3.3.0+ FEATURES

### **Có gì mới:**
- ✅ Hợp nhất từ vnstock3 → vnstock
- ✅ Performance improvements
- ✅ Bug fixes
- ✅ More stable API
- ✅ Better documentation

### **API Usage (không đổi):**

```python
from vnstock import Vnstock

stock = Vnstock().stock(symbol='VNM', source='VCI')
quote = stock.quote.history(symbol='VNM', start='2024-12-01')
latest = quote.iloc[-1]

print(f"Price: {latest['close']}")
```

---

## 🔄 MIGRATION GUIDE

### **Nếu bạn đã cài vnstock3:**

```powershell
# 1. Uninstall old
pip uninstall vnstock3 -y

# 2. Install new
pip install vnstock --upgrade

# 3. Code vẫn hoạt động (import đã fix)
python scripts/fetch_vnstock.py
```

**Không cần thay đổi code gì thêm!** ✅

---

## 📚 TÀI LIỆU THAM KHẢO

### **Official Docs:**
- Website: https://vnstocks.com
- Docs: https://vnstocks.com/docs
- Version History: https://vnstocks.com/docs/tai-lieu/lich-su-phien-ban
- GitHub: https://github.com/thinh-vu/vnstock

### **Version Timeline:**
- v3.2.1: Current stable
- v3.3.0: Latest release
- vnstock3 → vnstock: Migration complete

---

## 🚀 FULL WORKFLOW

### **Fresh install:**

```powershell
# 1. Navigate to project
cd C:\ai-advisor1

# 2. Install vnstock
pip install vnstock --upgrade

# 3. Install other dependencies
pip install pandas requests

# 4. Test VNStock script
python scripts/fetch_vnstock.py

# 5. Run dev server
npm run dev

# 6. Open browser
# http://localhost:3000

# 7. Check prices - should be REAL!
```

---

## 💡 TROUBLESHOOTING

### **Error: "vnstock3 not installed"**
```powershell
# Fix:
pip uninstall vnstock3 -y
pip install vnstock --upgrade
```

### **Error: "No module named vnstock"**
```powershell
# Fix:
pip install vnstock --upgrade
```

### **Error: Import error**
```powershell
# Fix:
pip install vnstock pandas requests --upgrade
```

### **Prices không hiển thị:**
```powershell
# Debug:
python scripts/fetch_vnstock.py

# Nếu có data → OK
# Nếu error → Check network/firewall
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] Uninstall vnstock3
- [ ] Install vnstock (v3.3.0+)
- [ ] Verify: `pip show vnstock`
- [ ] Test script: `python scripts/fetch_vnstock.py`
- [ ] See real data in JSON
- [ ] Run dev: `npm run dev`
- [ ] Check prices on http://localhost:3000
- [ ] Compare với vietstock.vn
- [ ] Prices match! ✅

---

## 🎉 DONE!

**Bây giờ bạn có:**
- ✅ VNStock v3.3.0+ (latest)
- ✅ Real market data
- ✅ FREE forever
- ✅ Local dev working perfectly

**Next steps:**
1. Test local thoroughly
2. Push to GitHub
3. Deploy to Netlify (will fallback to mock)
4. Demo với investors!

---

**Chạy `pip install vnstock --upgrade` ngay! 🚀**
