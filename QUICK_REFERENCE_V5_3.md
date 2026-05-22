# QUICK REFERENCE - 3 EXIT CRITERIA

**Scanner v5.3 - Technical Exit Rules**

---

## ⚡ PRIORITY 1: DAILY CRITICAL EXIT

**Signal:** 🚨 DAILY_CRITICAL_EXIT  
**Action:** BÁN 100% NGAY  
**Urgency:** CRITICAL  

### **3 Conditions (ALL must be TRUE):**

1. **MACD Divergence (Daily chart)** ⭐
   ```
   Price: Đỉnh cao hơn
   MACD: Đỉnh THẤP hơn
   → Momentum yếu đi!
   ```

2. **RSI > 80** ⭐
   ```
   RSI > 80 = EXTREME overbought
   → Profit-taking sắp xảy ra!
   ```

3. **Support Break (với volume)** ⭐
   ```
   Price đóng cửa < support
   Volume > 1.2x average
   → Downtrend confirmed!
   ```

### **How to Verify on Chart:**

```
✅ Open TradingView → Daily chart
✅ Check MACD indicator (bottom)
   → See 2 peaks: Price↑ MACD↓?
✅ Check RSI indicator
   → Above 80 line?
✅ Check support levels
   → Price broke below with high volume?

If ALL 3 ✅ → Signal is VALID!
```

### **When This Triggers:**

- Rare (0-1 per week)
- Very strong signal
- High confidence exit
- Usually at major tops

---

## ⚡ PRIORITY 2: 4H MEDIUM EXIT

**Signal:** ⚠️ 4H_MEDIUM_EXIT  
**Action:** BÁN 50%  
**Urgency:** HIGH  

### **2 Conditions (BOTH must be TRUE):**

1. **MACD Divergence (4H chart)** ⭐
   ```
   Same as daily, but on 4H chart
   → Medium-term momentum weak
   ```

2. **Volume Divergence** ⭐
   ```
   Price: Đỉnh cao hơn
   Volume: Đỉnh THẤP hơn
   → Uptrend thiếu conviction!
   ```

### **How to Verify on Chart:**

```
✅ Open chart → 4H timeframe
✅ Check MACD: Price↑ MACD↓?
✅ Check volume bars @ peaks
   → 2nd peak volume < 1st peak?

If BOTH ✅ → Signal is VALID!
```

### **When This Triggers:**

- Moderate frequency (1-2 per week)
- Medium confidence
- Partial exit (keep 50% for upside)
- Good risk/reward balance

---

## ⚡ PRIORITY 3: 1H VOLUME CLIMAX

**Signal:** ⚠️ 1H_VOLUME_CLIMAX or 1H_DISTRIBUTION_PATTERN  
**Action:** BÁN 100%  
**Urgency:** HIGH  

### **Pattern: BSR Example**

**Single Climax:**
```
Volume: ████████ (SPIKE @ đỉnh)
Price: Near recent high
→ Distribution! Smart money exit!
```

**Distribution Pattern (STRONGER):**
```
Volume: ████ ████ (2+ spikes @ resistance)
Price: Không vượt được đỉnh
→ Multiple distribution attempts!
```

### **How to Verify on Chart:**

```
✅ Open chart → 1H timeframe
✅ Look for volume bars @ top
   → Any bar 2.5x+ higher than average?
✅ Check price position
   → In top 10% of recent range?
✅ Check price after spike
   → Failed to break higher?

If pattern matches → Signal is VALID!
```

### **When This Triggers:**

- More common (2-4 per week)
- High confidence when detected
- Classic distribution pattern
- Often marks exact top

---

## 🎯 MANUAL VERIFICATION PROCESS

**When scanner generates signal:**

### **Step 1: Check Signal Type**
```
DAILY_CRITICAL → Go to Daily chart
4H_MEDIUM → Go to 4H chart
1H_CLIMAX → Go to 1H chart
```

### **Step 2: Verify Conditions**
```
Use checklist above for that signal type
Mark each condition: ✅ or ❌
```

### **Step 3: Make Decision**
```
ALL conditions ✅:
→ Execute signal (trust scanner)

Some conditions ❌:
→ False signal (don't execute)
→ Report to improve scanner
```

### **Step 4: Track Result**
```
Record:
- Date executed
- Entry price
- Exit price
- P/L %
- Signal was correct? (Y/N)

→ Build accuracy stats!
```

---

## 📊 SIGNAL CHARACTERISTICS

### **Daily Critical:**
```
Frequency: RARE (0-1/week)
Confidence: VERY HIGH (80-90%)
Exit: 100% (full exit)
Typical P/L: +5% to +20%
Best at: Major market tops
```

### **4H Medium:**
```
Frequency: MODERATE (1-2/week)
Confidence: HIGH (70-80%)
Exit: 50% (partial)
Typical P/L: +3% to +15%
Best at: Intermediate tops
```

### **1H Climax:**
```
Frequency: COMMON (2-4/week)
Confidence: HIGH (75-85%)
Exit: 100% (full exit)
Typical P/L: +2% to +10%
Best at: Intraday/short-term tops
```

---

## 🎨 VISUAL EXAMPLES

### **MACD Divergence:**
```
Price Chart:
      Peak 2 ↑ (higher)
        /\
Peak 1 /  \
  /\  /    \

MACD:
Peak 1 ↑ (higher)
  /\
 /  \
/    Peak 2 ↓ (LOWER!)
      /\

→ DIVERGENCE!
```

### **Volume Climax (BSR):**
```
Price: ________/‾‾‾\___ (top)
                ↑
Volume: __|____|████|__|__ (spike!)
                ↑
         Climax here!

→ EXIT!
```

### **Support Break:**
```
Price:
_________ Support line
         \
          \__ Break!
             ↓
         Current price

Volume @ break: HIGH ✅

→ CONFIRMED BREAK!
```

---

## 💡 TIPS

**Do:**
✅ Always verify signals manually first week
✅ Track accuracy in spreadsheet
✅ Adjust if false positive rate > 30%
✅ Trust high-confidence signals
✅ Use as confirmation (not sole reason)

**Don't:**
❌ Blindly execute without verification
❌ Ignore signals (they're there for a reason)
❌ Overtrade (wait for quality signals)
❌ Panic if 1-2 signals wrong (normal)
❌ Change parameters too quickly

---

## 🚨 RED FLAGS (False Signals)

**Be cautious if:**

⚠️ Signal triggers on low volume day  
⚠️ Market overall very volatile  
⚠️ Stock just had major news  
⚠️ Pattern doesn't "look right" on chart  
⚠️ Multiple conflicting signals same day  

**→ Manual override OK in these cases!**

---

## ✅ CONFIDENCE LEVELS

**Execute with confidence:**
```
EXTREME_HIGH (90%+):
- Distribution pattern 1H (2+ spikes)
- Daily critical with all 3 strong

VERY_HIGH (80-90%):
- Single 1H climax clear pattern
- Daily critical with strong divergence

HIGH (70-80%):
- 4H medium with both conditions clear
- 1H climax with good volume ratio

MEDIUM (60-70%):
- Borderline signals
- Consider partial exit only
```

---

## 📞 WHEN TO CONTACT SUPPORT

**Report if:**

🐛 Same stock triggers > 3 times in 1 day  
🐛 Signal makes no sense on chart  
🐛 Scanner crashes repeatedly  
🐛 False positive rate > 50% (1 week)  
🐛 No signals for > 2 weeks (with open positions)  

---

**KEEP THIS REFERENCE HANDY!** 📌

(Print or bookmark for quick verification!)
