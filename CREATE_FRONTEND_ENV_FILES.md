# 📝 TẠO FRONTEND ENVIRONMENT FILES

## 🎯 MỤC TIÊU

Tạo 2 files config để frontend biết connect đến backend nào:
- `.env.staging` → Connect đến staging backend
- `.env.production` → Connect đến production backend

---

## 📍 VỊ TRÍ

Tạo **TRONG** folder:
```
C:\ai-advisor1\frontend\
```

**Cấu trúc folder:**
```
C:\ai-advisor1\
├── frontend\
│   ├── src\
│   ├── public\
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.staging        ← Tạo file này
│   └── .env.production     ← Tạo file này
├── backend_api.py
└── ...
```

---

## 🔧 CÁCH 1: TẠO BẰNG NOTEPAD (ĐƠN GIẢN NHẤT)

### **Bước 1: Mở Notepad**

Press `Windows + R` → Gõ `notepad` → Enter

### **Bước 2: Paste nội dung file staging**

Copy và paste vào Notepad:

```
VITE_API_URL=https://ai-advisor1-staging.onrender.com/api
VITE_ENVIRONMENT=staging
VITE_APP_NAME=AI Advisor [STAGING]
```

### **Bước 3: Save as `.env.staging`**

1. Click **File → Save As**
2. Navigate đến: `C:\ai-advisor1\frontend\`
3. **Tên file:** `.env.staging` (bao gồm dấu chấm đầu!)
4. **Save as type:** "All Files (*.*)" ⚠️ QUAN TRỌNG!
5. Click **Save**

### **Bước 4: Tạo file production**

Mở Notepad mới, paste:

```
VITE_API_URL=https://ai-advisor1-backend.onrender.com/api
VITE_ENVIRONMENT=production
VITE_APP_NAME=AI Advisor
```

Save as: `.env.production` (cùng folder, "All Files")

---

## 🔧 CÁCH 2: TẠO BẰNG VS CODE (KHUYẾN NGHỊ)

### **Bước 1: Mở VS Code**

Mở folder: `C:\ai-advisor1`

### **Bước 2: Navigate to frontend folder**

Trong VS Code Explorer (bên trái), click vào folder `frontend`

### **Bước 3: Tạo file mới**

1. Right-click vào folder `frontend`
2. Click **"New File"**
3. Đặt tên: `.env.staging`
4. Press Enter

### **Bước 4: Paste nội dung**

Paste vào file `.env.staging`:

```env
VITE_API_URL=https://ai-advisor1-staging.onrender.com/api
VITE_ENVIRONMENT=staging
VITE_APP_NAME=AI Advisor [STAGING]
```

**Save:** `Ctrl + S`

### **Bước 5: Tạo file production**

Lặp lại:
1. New File → `.env.production`
2. Paste:

```env
VITE_API_URL=https://ai-advisor1-backend.onrender.com/api
VITE_ENVIRONMENT=production
VITE_APP_NAME=AI Advisor
```

**Save:** `Ctrl + S`

---

## 🔧 CÁCH 3: TẠO BẰNG COMMAND LINE

### **Mở PowerShell**

Press `Windows + X` → Chọn "Windows PowerShell"

### **Navigate to frontend folder**

```powershell
cd C:\ai-advisor1\frontend
```

### **Tạo file staging**

```powershell
@"
VITE_API_URL=https://ai-advisor1-staging.onrender.com/api
VITE_ENVIRONMENT=staging
VITE_APP_NAME=AI Advisor [STAGING]
"@ | Out-File -FilePath ".env.staging" -Encoding utf8
```

### **Tạo file production**

```powershell
@"
VITE_API_URL=https://ai-advisor1-backend.onrender.com/api
VITE_ENVIRONMENT=production
VITE_APP_NAME=AI Advisor
"@ | Out-File -FilePath ".env.production" -Encoding utf8
```

---

## ✅ XÁC NHẬN ĐÃ TẠO ĐÚNG

### **Kiểm tra bằng PowerShell:**

```powershell
cd C:\ai-advisor1\frontend
dir -Name
```

**Phải thấy:**
```
.env.production
.env.staging
package.json
src
vite.config.js
...
```

### **Kiểm tra nội dung:**

```powershell
# Xem file staging
type .env.staging

# Xem file production
type .env.production
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### **1. Dấu chấm đầu tiên (`.`) rất quan trọng!**

✅ Đúng: `.env.staging`  
❌ Sai: `env.staging`

### **2. Không có extension `.txt`**

✅ Đúng: `.env.staging`  
❌ Sai: `.env.staging.txt`

**Để tránh `.txt`:** Khi Save as trong Notepad, nhớ chọn "All Files (*.*)"!

### **3. Encoding UTF-8**

Files phải là UTF-8 (Notepad và VS Code mặc định UTF-8 rồi).

### **4. Không có khoảng trắng thừa**

```env
# ✅ Đúng:
VITE_API_URL=https://ai-advisor1-staging.onrender.com/api

# ❌ Sai (có space sau dấu =):
VITE_API_URL= https://ai-advisor1-staging.onrender.com/api
```

### **5. Không commit vào Git (optional)**

Files `.env.*` thường được ignore trong Git. Kiểm tra `.gitignore`:

```
# Should have:
.env
.env.*
.env.local
```

Nhưng `.env.staging` và `.env.production` **CÓ THỂ commit** vì không chứa secrets.

---

## 🎯 NỘI DUNG CHI TIẾT

### **File 1: `.env.staging`**

```env
VITE_API_URL=https://ai-advisor1-staging.onrender.com/api
VITE_ENVIRONMENT=staging
VITE_APP_NAME=AI Advisor [STAGING]
```

**Giải thích:**
- `VITE_API_URL`: Backend staging URL (Free tier Render)
- `VITE_ENVIRONMENT`: Môi trường staging
- `VITE_APP_NAME`: Tên hiển thị có [STAGING] để phân biệt

### **File 2: `.env.production`**

```env
VITE_API_URL=https://ai-advisor1-backend.onrender.com/api
VITE_ENVIRONMENT=production
VITE_APP_NAME=AI Advisor
```

**Giải thích:**
- `VITE_API_URL`: Backend production URL (Paid tier Render)
- `VITE_ENVIRONMENT`: Môi trường production
- `VITE_APP_NAME`: Tên hiển thị không có [STAGING]

---

## 🧪 TEST SAU KHI TẠO

### **Test local với staging config:**

```powershell
cd C:\ai-advisor1\frontend
npm run dev -- --mode staging
```

**Hoặc nếu cấu hình trong package.json:**

```powershell
npm run dev:staging
```

**Check:** Vào http://localhost:5173, mở DevTools (F12) → Console, gõ:

```javascript
console.log(import.meta.env.VITE_API_URL)
// Phải show: https://ai-advisor1-staging.onrender.com/api
```

### **Test local với production config:**

```powershell
npm run dev -- --mode production
```

---

## 📋 CHECKLIST

Sau khi tạo xong:

- [ ] File `.env.staging` tồn tại trong `C:\ai-advisor1\frontend\`
- [ ] File `.env.production` tồn tại trong `C:\ai-advisor1\frontend\`
- [ ] Cả 2 files có dấu chấm (`.`) đầu tiên
- [ ] Không có extension `.txt`
- [ ] Nội dung đúng (3 dòng mỗi file)
- [ ] Không có khoảng trắng thừa
- [ ] Test `type .env.staging` để xem nội dung

---

## ❓ TROUBLESHOOTING

### **Issue 1: Không thấy file `.env.staging`**

**Nguyên nhân:** Windows ẩn files bắt đầu bằng dấu chấm.

**Solution:** 
1. Mở File Explorer
2. View → Options → View tab
3. Check: "Show hidden files, folders, and drives"
4. Uncheck: "Hide extensions for known file types"

### **Issue 2: File có extension `.txt`**

**Nguyên nhân:** Notepad tự động thêm `.txt`.

**Solution:**
1. Rename file: Xóa `.txt` ở cuối
2. Hoặc dùng VS Code/PowerShell để tạo

### **Issue 3: Frontend không đọc được env**

**Nguyên nhân:** Vite chỉ đọc env khi start.

**Solution:** Restart dev server:
```powershell
# Stop server (Ctrl+C)
# Start lại
npm run dev
```

---

## 🎉 HOÀN THÀNH!

Sau khi tạo xong 2 files, tiếp tục với **Phase 3, Step 3.2** trong STAGING_SETUP_GUIDE.md!

---

**Version:** 1.0  
**Last Updated:** 2026-01-25  
**Guide:** Create Frontend Environment Files
