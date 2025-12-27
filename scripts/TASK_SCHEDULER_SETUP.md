# 🤖 TỰ ĐỘNG HÓA SCANNER - WINDOWS TASK SCHEDULER

**Tự động chạy scanner mỗi ngày lúc 3:45 PM**

---

## 📋 CHUẨN BỊ

### **Files cần có:**

```
C:\ai-advisor1\scripts\
├── daily_signal_scanner.py       # Scanner engine
├── run_daily_scanner.py          # Automated wrapper
└── run_scanner.bat               # Windows batch file
```

---

## 🚀 SETUP WINDOWS TASK SCHEDULER

### **Bước 1: Mở Task Scheduler**

```
1. Press Win + R
2. Type: taskschd.msc
3. Press Enter
```

### **Bước 2: Create New Task**

```
1. Click "Create Task..." (right panel)
2. NOT "Create Basic Task"
```

### **Bước 3: General Tab**

```
Name: AI Advisor Daily Scanner
Description: Scan stocks daily for PULLBACK & EMA_CROSS signals
Security Options:
  ✓ Run whether user is logged on or not
  ✓ Run with highest privileges
```

### **Bước 4: Triggers Tab**

```
Click "New..."

Settings:
  Begin the task: On a schedule
  Daily
  Start: [Today's date] 3:45:00 PM
  Recur every: 1 days
  
  ✓ Enabled
  
Advanced:
  ✓ Stop task if it runs longer than: 2 hours
```

### **Bước 5: Actions Tab**

```
Click "New..."

Action: Start a program

Settings:
  Program/script: C:\ai-advisor1\scripts\run_scanner.bat
  
  OR (if .bat doesn't work):
  Program/script: python
  Add arguments: run_daily_scanner.py
  Start in: C:\ai-advisor1\scripts
```

### **Bước 6: Conditions Tab**

```
✓ Start only if the computer is on AC power (optional)
✗ Stop if the computer switches to battery power
✓ Wake the computer to run this task (important!)
```

### **Bước 7: Settings Tab**

```
✓ Allow task to be run on demand
✓ Run task as soon as possible after a scheduled start is missed
✓ If the task fails, restart every: 10 minutes
  Attempt to restart up to: 3 times
✗ Stop the task if it runs longer than: (already set in Triggers)
```

### **Bước 8: Save**

```
Click OK
Enter Windows password if prompted
```

---

## ✅ TEST TASK

### **Manual Test:**

```
1. Find task in Task Scheduler
2. Right-click → Run
3. Check if it runs successfully
4. Check output in C:\ai-advisor1\scripts\signals\
```

### **Check Logs:**

```
Task Scheduler → History tab
Look for:
  - Task Started (event 100)
  - Task Completed (event 102)
```

---

## 📊 EXPECTED BEHAVIOR

### **Daily at 3:45 PM:**

```
1. Task starts automatically
2. Scanner runs for 10-30 minutes
3. Generates signals
4. Saves to signals/signals_latest.json
5. Copies to frontend (if configured)
6. Sends Telegram notification
7. Task completes
```

---

## 🔧 TROUBLESHOOTING

### **Task doesn't run:**

```
Check:
1. Computer is on at 3:45 PM
2. "Wake computer" is checked
3. Task is Enabled
4. Python is in PATH
5. Working directory is correct
```

### **Task runs but fails:**

```
Check:
1. Python dependencies installed
2. vnstock working
3. File paths correct
4. Check Task Scheduler History for error codes
```

### **Task runs but no signals:**

```
Check:
1. Market was open today
2. Stock list loaded correctly
3. Check signals/failed_stocks.txt
4. Run manually to see errors:
   python run_daily_scanner.py
```

---

## 📱 MONITORING

### **Daily Check:**

```
1. Check signals/signals_latest.json timestamp
2. Check Telegram notification
3. Verify frontend updated
```

### **Weekly Review:**

```
1. Check Task Scheduler history
2. Review success rate
3. Check for errors
4. Update stock lists if needed
```

---

## 🎯 ALTERNATIVE: MANUAL RUN

**If Task Scheduler doesn't work:**

### **Option 1: Desktop Shortcut**

```
1. Right-click desktop → New → Shortcut
2. Location: C:\ai-advisor1\scripts\run_scanner.bat
3. Name: Run Scanner
4. Double-click daily at 3:45 PM
```

### **Option 2: Command Line**

```bash
cd C:\ai-advisor1\scripts
python run_daily_scanner.py
```

---

## 📋 CONFIGURATION

### **In run_daily_scanner.py:**

```python
# Line 21-23
AUTO_RUN = True       # Automated mode
SCAN_ALL = False      # True = all stocks, False = priority
MAX_STOCKS = None     # None = no limit

# Line 26-35
PRIORITY_STOCKS = [   # Edit this list
    'TCH', 'PWA', 'GEE', ...
]
```

---

## 🔔 NOTIFICATIONS

### **Telegram Setup:**

```python
# In run_daily_scanner.py, line 154-156
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Already configured
CHAT_ID = "YOUR_CHAT_ID"      # Already configured
```

**Test notification:**

```bash
python -c "from run_daily_scanner import send_telegram_notification; send_telegram_notification({'pullback': [], 'ema_cross': []})"
```

---

## 📊 OUTPUT FILES

```
signals/
├── signals_20251220_154530.json    # Daily archive
├── signals_latest.json             # Latest (for frontend)
├── summary_latest.json             # Summary
└── vnstock_symbols.csv             # Stock list cache
```

---

## 🎯 NEXT STEPS AFTER SETUP

**Day 1:**
```
1. Setup Task Scheduler
2. Run manual test
3. Verify outputs
4. Check Telegram notification
```

**Day 2-7:**
```
1. Monitor daily runs
2. Check signal quality
3. Verify frontend updates
4. Adjust if needed
```

**Week 2+:**
```
1. Review historical signals
2. Compare with actual performance
3. Optimize parameters
4. Scale to more stocks
```

---

## ✅ CHECKLIST

**Setup Complete When:**

- [ ] Task Scheduler configured
- [ ] Test run successful
- [ ] Signals generated
- [ ] Frontend receives data
- [ ] Telegram notification working
- [ ] Daily run scheduled (3:45 PM)
- [ ] Wake computer enabled
- [ ] Monitoring in place

---

**READY TO AUTOMATE! 🤖**

**SET IT AND FORGET IT! ⚡**

*Generated: December 20, 2025*
