# MARKET RISK INTEGRATION GUIDE
# Hướng dẫn tích hợp Market Risk Analysis vào hệ thống AI Advisor

## ══════════════════════════════════════════════════
## 1. DATABASE MODEL - Thêm vào backend_api.py
## ══════════════════════════════════════════════════

# Thêm sau class Signal(Base) trong backend_api.py:

```python
class MarketRisk(Base):
    __tablename__ = 'market_risk'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(20), nullable=False, unique=True)   # '2026-02-10'
    market_mode = Column(String(20), nullable=False)          # 'BULL', 'SIDEWAYS', 'BEAR'
    mode_label = Column(String(50))                           # 'TÍCH CỰC', 'THẬN TRỌNG', 'PHÒNG THỦ'
    risk_score = Column(Integer)                              # 0-100
    allocation = Column(Integer)                              # 0-100 (% cổ phiếu)
    description = Column(Text)
    factors_json = Column(Text)                               # JSON string of factors array
    vnindex_value = Column(Float)
    raw_scores_json = Column(Text)                            # JSON string of raw scores
    analyzed_at = Column(DateTime, default=datetime.now)
```


## ══════════════════════════════════════════════════
## 2. API ENDPOINTS - Thêm vào backend_api.py
## ══════════════════════════════════════════════════

```python
# ── GET /api/market-risk ──────────────────────────
# Trả về market risk analysis mới nhất
@app.route('/api/market-risk', methods=['GET'])
def get_market_risk():
    """Get latest market risk analysis"""
    session = Session()
    try:
        latest = session.query(MarketRisk).order_by(
            MarketRisk.date.desc()
        ).first()
        
        if not latest:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No market analysis available yet'
            })
        
        factors = json.loads(latest.factors_json) if latest.factors_json else []
        raw_scores = json.loads(latest.raw_scores_json) if latest.raw_scores_json else {}
        
        return jsonify({
            'success': True,
            'data': {
                'date': latest.date,
                'market_mode': latest.market_mode,
                'mode_label': latest.mode_label,
                'risk_score': latest.risk_score,
                'allocation': latest.allocation,
                'description': latest.description,
                'factors': factors,
                'vnindex_value': latest.vnindex_value,
                'raw_scores': raw_scores,
                'analyzed_at': latest.analyzed_at.isoformat() if latest.analyzed_at else None,
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()


# ── POST /api/market-risk/scan ────────────────────
# Chạy market risk analysis (manual trigger)
@app.route('/api/market-risk/scan', methods=['POST'])
def trigger_market_risk_scan():
    """Trigger market risk analysis"""
    try:
        from market_risk_analysis import run_market_analysis
        
        result = run_market_analysis()
        
        # Save to database
        session = Session()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Upsert: update if exists, create if not
        existing = session.query(MarketRisk).filter_by(date=today).first()
        
        if existing:
            existing.market_mode = result['market_mode']
            existing.mode_label = result['mode_label']
            existing.risk_score = result['risk_score']
            existing.allocation = result['allocation']
            existing.description = result['description']
            existing.factors_json = json.dumps(result['factors'], ensure_ascii=False)
            existing.vnindex_value = result.get('vnindex_detail', {}).get('vnindex')
            existing.raw_scores_json = json.dumps(result['raw_scores'])
            existing.analyzed_at = datetime.now()
        else:
            new_record = MarketRisk(
                date=today,
                market_mode=result['market_mode'],
                mode_label=result['mode_label'],
                risk_score=result['risk_score'],
                allocation=result['allocation'],
                description=result['description'],
                factors_json=json.dumps(result['factors'], ensure_ascii=False),
                vnindex_value=result.get('vnindex_detail', {}).get('vnindex'),
                raw_scores_json=json.dumps(result['raw_scores']),
                analyzed_at=datetime.now(),
            )
            session.add(new_record)
        
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Market risk analysis completed'
        }), 201
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ── GET /api/market-risk/history ──────────────────
# Lấy lịch sử market risk (7 ngày gần nhất)
@app.route('/api/market-risk/history', methods=['GET'])
def get_market_risk_history():
    """Get market risk history"""
    session = Session()
    try:
        days = request.args.get('days', 7, type=int)
        
        records = session.query(MarketRisk).order_by(
            MarketRisk.date.desc()
        ).limit(days).all()
        
        history = []
        for r in records:
            history.append({
                'date': r.date,
                'market_mode': r.market_mode,
                'risk_score': r.risk_score,
                'allocation': r.allocation,
            })
        
        return jsonify({
            'success': True,
            'data': history
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
```


## ══════════════════════════════════════════════════
## 3. TÍCH HỢP VÀO DAILY SCANNER FLOW
## ══════════════════════════════════════════════════

### Option A: Chạy trong cùng scan endpoint (khuyến nghị)

Sửa trigger_scan() trong backend_api.py:

```python
@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger signal scanner + market risk analysis"""
    try:
        # ... existing scanner code ...
        
        # Thêm: chạy market risk analysis sau khi signal scan
        # (chạy trong background thread riêng)
        import threading
        
        def run_market_risk_after_scan():
            """Wait for signal scan to finish, then run market risk"""
            import time
            time.sleep(60)  # Đợi signal scan chạy 1 phút
            
            try:
                from market_risk_analysis import run_market_analysis
                result = run_market_analysis()
                
                # Save to DB
                session = Session()
                today = datetime.now().strftime('%Y-%m-%d')
                existing = session.query(MarketRisk).filter_by(date=today).first()
                
                if existing:
                    existing.market_mode = result['market_mode']
                    existing.risk_score = result['risk_score']
                    existing.allocation = result['allocation']
                    existing.factors_json = json.dumps(result['factors'], ensure_ascii=False)
                    existing.analyzed_at = datetime.now()
                else:
                    session.add(MarketRisk(
                        date=today,
                        market_mode=result['market_mode'],
                        mode_label=result['mode_label'],
                        risk_score=result['risk_score'],
                        allocation=result['allocation'],
                        description=result['description'],
                        factors_json=json.dumps(result['factors'], ensure_ascii=False),
                        vnindex_value=result.get('vnindex_detail', {}).get('vnindex'),
                        raw_scores_json=json.dumps(result['raw_scores']),
                    ))
                
                session.commit()
                session.close()
                print("✅ Market risk analysis saved!")
                
            except Exception as e:
                print(f"⚠️ Market risk analysis failed: {e}")
        
        # Start market risk in background
        thread = threading.Thread(target=run_market_risk_after_scan)
        thread.daemon = True
        thread.start()
        
        return jsonify({...}), 202
```


### Option B: GitHub Actions chạy riêng (nếu muốn tách biệt)

Thêm step vào daily-scanner.yml:

```yaml
      # After signal scan completes...
      
      - name: Trigger Market Risk Analysis
        run: |
          echo "📊 Triggering market risk analysis..."
          curl -X POST "$API_URL/market-risk/scan"
          
      - name: Verify Market Risk
        run: |
          sleep 120  # Đợi 2 phút cho breadth scan
          RISK=$(curl -s "$API_URL/market-risk")
          echo "Market Risk Result: $RISK"
```


## ══════════════════════════════════════════════════
## 4. FRONTEND INTEGRATION
## ══════════════════════════════════════════════════

Thêm vào LandingPage.jsx (thay bảng mockup dashboard):

```javascript
// Fetch market risk data
const [marketRisk, setMarketRisk] = useState(null);

useEffect(() => {
  fetch(`${API_BASE}/market-risk`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.data) {
        setMarketRisk(data.data);
      }
    })
    .catch(err => console.error('Market risk fetch error:', err));
}, []);

// Render MarketRiskWidget thay cho mockup dashboard
{marketRisk ? (
  <MarketRiskWidget data={marketRisk} />
) : (
  <div>Đang tải phân tích thị trường...</div>
)}
```


## ══════════════════════════════════════════════════
## 5. THỜI GIAN CHẠY ƯỚC TÍNH
## ══════════════════════════════════════════════════

| Bước                    | Thời gian     | Ghi chú                      |
|-------------------------|---------------|-------------------------------|
| VN-Index Trend          | ~5 giây       | 1 API call                   |
| Thanh khoản             | ~5 giây       | 1 API call                   |
| Breadth (100 CP)        | ~3-5 phút     | 100 API calls (rate limited) |
| Foreign flow            | ~5 giây       | 1 API call                   |
| **Tổng**                | **~4-6 phút** | Chạy song song signal scan   |

→ Chạy đồng thời với signal scan (20-25 phút), không ảnh hưởng tổng thời gian.


## ══════════════════════════════════════════════════
## 6. FILE PLACEMENT
## ══════════════════════════════════════════════════

```
ai-advisor1/
├── market_risk_analysis.py          ← Module chính (NEW)
├── backend_api.py                   ← Thêm endpoints + model
├── scripts/
│   ├── daily_signal_scanner_eod.py  ← Existing
│   └── high_liquidity_tickers.json  ← Optional: danh sách CP
└── market_risk_latest.json          ← Cache file (auto-generated)
```


## ══════════════════════════════════════════════════
## 7. TESTING
## ══════════════════════════════════════════════════

```powershell
# Test standalone
cd C:\ai-advisor1
python market_risk_analysis.py
# → Output: market_risk_latest.json

# Test API endpoint
Invoke-WebRequest -Uri "http://localhost:10000/api/market-risk/scan" -Method POST
# → Returns analysis result

# Check latest
Invoke-WebRequest -Uri "http://localhost:10000/api/market-risk"
# → Returns latest analysis

# Check history
Invoke-WebRequest -Uri "http://localhost:10000/api/market-risk/history?days=7"
```
