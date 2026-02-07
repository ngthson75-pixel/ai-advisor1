# VIETNAM HOLIDAY CALENDAR SYSTEM

## 📋 OVERVIEW

Hệ thống tự động kiểm tra ngày giao dịch để tránh chạy scanner vào:
- ❌ Thứ 7, Chủ nhật
- ❌ Ngày lễ (Tết, 30/4, 1/5, 2/9...)

---

## 🚀 SETUP

### Bước 1: Upload files lên GitHub

```bash
# Trong repo ai-advisor1
git add vietnam_holidays.json
git add check_trading_day.py
git commit -m "Add holiday calendar system"
git push
```

### Bước 2: Update workflows

**Thay thế file workflows:**

```bash
# Backup old files
mv .github/workflows/daily-scanner.yml .github/workflows/daily-scanner.yml.backup
mv .github/workflows/hourly-sell-scanner.yml .github/workflows/hourly-sell-scanner.yml.backup

# Copy new files
cp daily-scanner-with-holiday-check.yml .github/workflows/daily-scanner.yml
cp hourly-sell-scanner-with-holiday-check.yml .github/workflows/hourly-sell-scanner.yml

# Commit
git add .github/workflows/
git commit -m "Update workflows with holiday check"
git push
```

### Bước 3: Verify

1. Vào: https://github.com/ngthson75-pixel/ai-advisor1/actions
2. Check workflows chỉ chạy T2-T6
3. Test manual run vào T7: Nên skip với message "Not a trading day"

---

## 📅 CẬP NHẬT NGÀY LỄ HÀNG NĂM

### Lịch nghỉ lễ 2026 (Tham khảo)

```json
{
  "holidays": {
    "2026": [
      "2026-01-01",          // Tết Dương lịch
      "2026-02-16",          // 30 Tết (dự kiến)
      "2026-02-17",          // Mùng 1 Tết
      "2026-02-18",          // Mùng 2 Tết
      "2026-02-19",          // Mùng 3 Tết
      "2026-02-20",          // Mùng 4 Tết
      "2026-04-02",          // Giỗ Tổ Hùng Vương
      "2026-04-30",          // 30/4
      "2026-05-01",          // 1/5
      "2026-09-02"           // 2/9
    ]
  }
}
```

**Cách update:**

1. Mỗi cuối năm, lấy lịch nghỉ chính thức từ HOSE/HNX
2. Update file `vietnam_holidays.json`
3. Commit & push lên GitHub

---

## 🧪 TEST LOCAL

### Test check_trading_day.py

```bash
# Check hôm nay
python check_trading_day.py

# Check ngày cụ thể
python check_trading_day.py --date 2026-01-01

# Check ngày giao dịch tiếp theo
python check_trading_day.py --next

# Quiet mode (chỉ exit code)
python check_trading_day.py --quiet
echo $?  # 0 = trading day, 1 = not trading day
```

### Expected outputs

**Ngày thường (T2-T6):**
```
📅 VIETNAM TRADING DAY CHECK
Date: 2026-02-05
Weekday: Thursday (ISO: 4)

✅ TRADING DAY - Market open
   Morning: 09:00 - 11:30
   Afternoon: 13:00 - 15:00

✅ EXIT CODE 0 - Trading day
```

**Thứ 7:**
```
📅 VIETNAM TRADING DAY CHECK
Date: 2026-02-07
Weekday: Saturday (ISO: 6)

❌ WEEKEND - Market closed
   Weekday 6 not in trading days [1, 2, 3, 4, 5]

❌ EXIT CODE 1 - Non-trading day
```

**Ngày lễ:**
```
📅 VIETNAM TRADING DAY CHECK
Date: 2026-01-01
Weekday: Thursday (ISO: 4)

❌ PUBLIC HOLIDAY - Market closed
   2026-01-01 is in holiday list

❌ EXIT CODE 1 - Non-trading day
```

---

## 📊 WORKFLOW SCHEDULE

### Daily Scanner
- **Schedule:** 6:00 PM Vietnam time (11:00 AM UTC)
- **Days:** Monday-Friday only (cron: `0 11 * * 1-5`)
- **Holiday check:** ✅ Yes

### Hourly SELL Scanner
- **Schedule:** Mỗi giờ 9 AM - 3 PM Vietnam time
- **Days:** Monday-Friday only (cron: `0 2-8 * * 1-5`)
- **Holiday check:** ✅ Yes
- **Trading hours check:** ✅ Yes (9:00-11:30, 13:00-15:00)

---

## 🔧 TROUBLESHOOTING

### Workflow vẫn chạy vào T7/CN

**Check 1:** Verify cron syntax
```yaml
# ĐÚNG (T2-T6):
- cron: '0 11 * * 1-5'

# SAI (Cả tuần):
- cron: '0 11 * * *'
```

**Check 2:** Check holiday check step
- Xem logs trong GitHub Actions
- Tìm step "Check if trading day"
- Verify output: `trading_day=false` vào ngày nghỉ

### Script báo lỗi "vietnam_holidays.json not found"

**Fix:** Ensure file đã được commit và push:

```bash
git add vietnam_holidays.json
git commit -m "Add holiday calendar"
git push
```

**Verify:** Check file tồn tại trên GitHub:
```
https://github.com/ngthson75-pixel/ai-advisor1/blob/main/vietnam_holidays.json
```

### Backend vẫn nhận request vào ngày nghỉ

**Root cause:** User gọi API trực tiếp (không qua workflow)

**Fix:** Thêm holiday check vào backend API:

```python
# backend_api.py
from check_trading_day import is_trading_day

@app.route('/api/scan', methods=['POST'])
def scan():
    # Check trading day
    if not is_trading_day(verbose=False):
        return jsonify({
            'error': 'Market closed',
            'message': 'Today is not a trading day'
        }), 400
    
    # ... rest of scan logic
```

---

## 📱 NOTIFICATIONS (Optional)

### Thêm Telegram notification khi skip

```yaml
- name: Notify skip (non-trading day)
  if: steps.check_trading_day.outputs.trading_day == 'false'
  env:
    TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
  run: |
    DATE=$(date +%Y-%m-%d)
    curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
      -d chat_id="$TELEGRAM_CHAT_ID" \
      -d text="⏸️ Scan skipped: $DATE is not a trading day"
```

---

## 🎯 BEST PRACTICES

1. **Update holidays yearly:** Mỗi cuối năm
2. **Test before deploy:** Chạy local test trước khi push
3. **Monitor logs:** Check GitHub Actions logs định kỳ
4. **Backup configs:** Backup workflow files trước khi sửa

---

## 📞 SUPPORT

Nếu có vấn đề:
1. Check GitHub Actions logs
2. Test local: `python check_trading_day.py`
3. Verify holiday calendar: `cat vietnam_holidays.json`

---

## 🔄 UPDATE LOG

- **2026-02-05:** Initial setup
- **2026-02-05:** Added holiday check to workflows
- **Next:** Update 2027 holidays (Dec 2026)
