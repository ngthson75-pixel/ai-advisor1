# 📋 DAILY OPERATIONS MANUAL - AI ADVISOR
## Quy trình vận hành hàng ngày (Manual Mode)

**Cập nhật:** 2026-02-19  
**Mục đích:** Kiểm soát chất lượng tín hiệu trước khi tự động hóa  
**Thời gian chạy:** Sau 15h00 mỗi ngày giao dịch  
**Tổng thời gian:** ~35-40 phút (chủ yếu đợi scanner)

---

## ⏱️ TỔNG QUAN QUY TRÌNH

```
15h00 - Thị trường đóng cửa
  │
  ▼
BƯỚC 1: BUY Signal Scanner ─────── 20-25 phút (tự động)
  → Quét 346 mã EOD → raw signals + breadth data
  │
  ▼
BƯỚC 2: Lọc & Dedup tín hiệu ──── vài giây (tự động)
  → Loại trùng, lọc chất lượng → signals sạch
  │
  ▼
BƯỚC 3: SELL Signal Scanner ────── 2-5 phút (tự động)
  → Quét tín hiệu bán cho mã đã khuyến nghị mua
  │
  ▼
BƯỚC 4: Market Risk Analysis ───── vài giây (tự động)
  → Phân tích rủi ro từ breadth data
  │
  ▼
BƯỚC 5: Review tín hiệu ──────── 5-10 phút (THỦ CÔNG)
  → Sơn kiểm tra, loại bỏ tín hiệu kém
  │
  ▼
BƯỚC 6: Đẩy lên Production ────── 2-3 phút (xác nhận)
  → Push Market Risk + Signals lên website
```

---

## 🚀 CÁCH 1: CHẠY TỪNG BƯỚC (Khuyến nghị khi mới bắt đầu)

### BƯỚC 1: BUY Signal Scanner

```powershell
cd C:\ai-advisor1\scripts
python daily_signal_scanner_eod.py
```

⏱️ **20-25 phút**  
📂 Output:
- `signals.db` → raw BUY signals (SQLite local)
- `market_breadth_eod.json` → breadth data (dùng cho Market Risk)

Kết quả mong đợi:
```
📊 Scanning 346 stocks...
📊 BREADTH DATA SAVED → market_breadth_eod.json
   Tổng: 341 | Tăng: 165 | Giảm: 103
   Trên MA20: 129/341 (37.8%)

══════════════════════════════════════
📊 FINAL SUMMARY
Total signals: 40-50 (raw, có trùng)
   PULLBACK: XX
   EMA_CROSS: YY
   Priority: ZZ
```

---

### BƯỚC 2: Lọc & Dedup tín hiệu

```powershell
cd C:\ai-advisor1\scripts
python daily_scanner_FILTERED.py
```

⏱️ **Vài giây**  
📂 Output: `signals/signals_latest.json` → 15-20 tín hiệu sạch

Logic lọc:
- **Dedup:** Mỗi ticker chỉ giữ 1 tín hiệu (score cao nhất)
- **Quality:** Loại tín hiệu score < 70%
- **Penny stock:** Loại mã penny (giá < 10.000 VND)

```
Before: 42 signals (raw, trùng lặp)
After:  18 signals (sạch, unique)
```

> ⚠️ **Nếu chưa có file `daily_scanner_FILTERED.py`:** Bỏ qua bước này, dùng signals từ `signals.db` trực tiếp và lọc thủ công ở Bước 5.

---

### BƯỚC 3: SELL Signal Scanner

```powershell
cd C:\ai-advisor1
python sell_signal_scanner_v3.py --days 30 --delay 2.0
```

⏱️ **2-5 phút** (tùy số mã trên production)  
📂 Output: Hiển thị SELL signals + lưu `sell_signals_latest.json`

**v3 khác v2:**
- **v2 (cũ, SAI):** Đọc từ `signals.db` local → chỉ thấy 11 mã vừa scan hôm nay
- **v3 (mới, ĐÚNG):** Đọc từ Production API → thấy TẤT CẢ 26 mã đang hiện trên website

Logic: Lấy BUY signals đang open trên production → kiểm tra 4 điều kiện:

| Điều kiện | Hành động | Tỷ lệ bán |
|-----------|-----------|------------|
| **Stop Loss:** Giá ≤ SL | SELL | 100% |
| **Take Profit:** Giá ≥ TP | SELL | 50% (chốt lời 1 phần) |
| **MA20 Consecutive:** 2 ngày < MA20 | SELL | 100% |
| **MA20 High Volume:** < MA20 + vol cao | SELL | 100% |

```
✓ Found 15 active BUY signals to check
✅ SELL SIGNAL: HPG (STOP_LOSS) -9.43%
✅ SELL SIGNAL: TCB (MA20_CONSECUTIVE)
📊 RESULTS: Found 2 SELL signals
```

> **Lưu ý:** Có ngày 0 SELL signals = bình thường (thị trường mạnh)

---

### BƯỚC 4: Market Risk Analysis

```powershell
cd C:\ai-advisor1
python market_risk_analysis.py
```

⏱️ **Vài giây** (1 API call VN-Index)  
📂 Output: `market_risk_latest.json`

```
🟡 MARKET MODE: THẬN TRỌNG (SIDEWAYS)
📊 Risk Score: 43/100
💰 Tỷ trọng khuyến nghị: 50% cổ phiếu
🔌 API calls: 1 (VN-Index only)
```

Yếu tố phân tích:
| Yếu tố | Trọng số | Nguồn |
|---------|----------|-------|
| VN-Index Trend | 30% | 1 API call |
| Thanh khoản | 20% | 1 API call (cùng VN-Index) |
| Số CP tăng/giảm | 25% | market_breadth_eod.json |
| CP trên MA20 | 25% | market_breadth_eod.json |

---

### BƯỚC 5: Review tín hiệu (THỦ CÔNG)

**5a. Xem BUY signals hôm nay:**
```powershell
cd C:\ai-advisor1
sqlite3 signals.db "SELECT ticker, strategy, strength, entry_price, stop_loss, take_profit, stock_type FROM signals WHERE action='BUY' AND date=DATE('now') ORDER BY strength DESC"
```

**5b. Xem SELL signals hôm nay:**
```powershell
sqlite3 signals.db "SELECT ticker, exit_reason, profit_loss_pct, exit_date FROM signals WHERE action='SELL' AND exit_date=DATE('now')"
```

**5c. Dùng Signal Editor (nếu có):**
```powershell
cd C:\ai-advisor1\scripts
python signal_editor.py
```
→ Menu tương tác: Xem / Xóa / Sửa / Thêm signals  
→ Lưu thay đổi vào `signals_latest.json`

**5d. Tiêu chí review:**
- ✅ Giữ: Blue-chip & Mid-cap, score ≥ 75%, R/R ≥ 1.5x
- ⚠️ Cân nhắc: Score 70-74%, stock type không rõ
- ❌ Loại: Penny stock, score < 70%, thanh khoản thấp

---

### BƯỚC 6: Đẩy lên Production

**6a. Đẩy Market Risk (Market Dashboard):**
```powershell
cd C:\ai-advisor1
python push_market_risk.py
```
→ Hiện kết quả → Hỏi xác nhận → Website cập nhật Market Dashboard

**6b. Đẩy BUY/SELL Signals:**
```powershell
python push_local_signals.py
```
→ Chọn: 1 (Production) → Xác nhận: y  
→ Website cập nhật bảng tín hiệu

---

## ⚡ CÁCH 2: CHẠY TẤT CẢ 1 LỆNH

```powershell
cd C:\ai-advisor1
python daily_eod_workflow.py
```

Script tự động: Bước 1 → 2 → 3 → 4 → Hỏi xác nhận push Market Risk

Sau đó làm thủ công:
```powershell
# Review signals
sqlite3 signals.db "SELECT ticker, strategy, strength FROM signals WHERE action='BUY' AND date=DATE('now') ORDER BY strength DESC"

# Push signals đã lọc
python push_local_signals.py
```

---

## 📁 CẤU TRÚC FILE

```
C:\ai-advisor1\
│
├── scripts\
│   ├── daily_signal_scanner_eod.py   ← Bước 1: BUY scanner (346 mã)
│   ├── daily_scanner_FILTERED.py     ← Bước 2: Lọc & dedup
│   ├── sell_signal_scanner_v2.py     ← (cũ, đọc local DB - KHÔNG DÙNG)
│   ├── signal_editor.py             ← Bước 5: Review thủ công
│   └── signals\
│       ├── signals_latest.json       ← Tín hiệu đã lọc sạch
│       └── summary_latest.json       ← Tóm tắt tín hiệu
│
├── sell_signal_scanner_v3.py         ← Bước 3: SELL scanner (đọc từ API) ✅
├── market_risk_analysis.py           ← Bước 4: Market Risk
├── push_market_risk.py               ← Bước 6a: Push Market Dashboard
├── push_local_signals.py             ← Bước 6b: Push Signals
├── daily_eod_workflow.py             ← Chạy tất cả 1 lần
│
├── market_breadth_eod.json           ← Breadth data (từ scanner)
├── market_risk_latest.json           ← Kết quả Market Risk
└── signals.db                        ← Local database
```

---

## 🔧 XỬ LÝ SỰ CỐ

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| Server không phản hồi | Render Free Tier ngủ | `Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/health"` đợi 2-3 phút |
| VCI Rate Limit | Quá nhiều request | Tăng delay: `--delay 3.0` |
| Breadth "Chưa có dữ liệu" | Scanner chưa chạy | Chạy lại Bước 1 |
| Push market risk lỗi | Server ngủ hoặc table chưa tạo | Wake up server → `POST /api/migrate` |
| 0 SELL signals | Thị trường mạnh | Bình thường, không phải lỗi |
| 0 BUY signals | Thị trường không đủ điều kiện | Bình thường, đợi ngày khác |

---

## 📌 NGUYÊN TẮC VẬN HÀNH

1. **Chỉ push DATA hàng ngày** — code đã deploy sẵn, KHÔNG cần git push mỗi ngày
2. **Khi sửa code** → git push staging → test → merge production
3. **Luôn review trước khi upload** — kiểm soát chất lượng tín hiệu
4. **Ngày nghỉ lễ/cuối tuần** → không cần chạy (không có dữ liệu mới)
5. **Manual trước, auto sau** → khi tín hiệu ổn định mới chuyển automation

---

## 🎯 LỘ TRÌNH AUTOMATION

```
HIỆN TẠI: Manual ← đang ở đây
  → Chạy 3-4 lệnh mỗi ngày
  → Kiểm soát chất lượng 100%

PHASE 2: Semi-auto (sau 2-4 tuần tín hiệu ổn)
  → Scanner tự chạy qua GitHub Actions
  → Sơn chỉ review + approve
  → Market Risk tự push

PHASE 3: Full-auto (khi confident)
  → Tất cả tự động
  → Alert qua Telegram nếu bất thường
```
