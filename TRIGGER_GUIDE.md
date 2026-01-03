# 🚀 TRIGGER SCANNER - 2 CÁCH

## ✅ CÁCH 1: DÙNG HTML FILE (RECOMMENDED!)

### **1. Download file `trigger_scanner.html`**

### **2. Mở file bằng browser:**
- Double-click file
- Hoặc kéo thả vào Chrome/Edge

### **3. Click nút "Chạy Scanner Ngay"**

### **4. Đợi 30-60 giây**

**Sẽ thấy:**
```
✓ Scanner hoàn thành! Tìm thấy X signals!
```

**Nếu có signals → Click link "Xem trên Website"**

---

## ✅ CÁCH 2: DÙNG POWERSHELL

### **1. Mở PowerShell:**
- Windows key
- Gõ "PowerShell"
- Click "Windows PowerShell"

### **2. Paste command:**

```powershell
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/scan" -Method POST
```

### **3. Enter**

**Expected output:**
```
StatusCode        : 200
StatusDescription : OK
Content           : {"message":"Scan started","status":"success"}
```

### **4. Đợi 2 phút, check signals:**

```powershell
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/signals" | Select-Object -ExpandProperty Content
```

---

## 🎯 KHUYẾN NGHỊ:

**DÙNG CÁCH 1 (HTML FILE)** vì:
- ✅ Đơn giản nhất
- ✅ Có UI đẹp
- ✅ Tự động check kết quả
- ✅ Hiển thị progress
- ✅ Link trực tiếp đến website

---

## 📋 SAU KHI TRIGGER:

### **Nếu thấy signals:**
1. Click "Xem trên Website"
2. Login
3. Vào tab "Tín hiệu mua bán"
4. Sẽ thấy signals!

### **Nếu không có signals:**
1. Click link "Xem Logs"
2. Check Render logs
3. Tìm lỗi
4. Có thể do:
   - Ngày nghỉ lễ (không có data)
   - API timeout
   - Network error

---

## 🐛 TROUBLESHOOTING:

### **HTML file không work:**
- Check network connection
- Try PowerShell method
- Check browser console (F12)

### **PowerShell lỗi:**
- Check internet
- Try running as Administrator
- Check firewall

### **Scanner timeout:**
- Đợi lâu hơn (2-3 phút)
- Check Render logs manually
- Try trigger again

---

## ✅ QUICK START:

**3 BƯỚC:**

1. **Download `trigger_scanner.html`**
2. **Mở file trong browser**
3. **Click "Chạy Scanner Ngay"**

**DONE! 🎉**
