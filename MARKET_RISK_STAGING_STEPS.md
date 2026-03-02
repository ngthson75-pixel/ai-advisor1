# 🚀 MARKET RISK - TRIỂN KHAI STAGING
# Thực hiện lần lượt từng bước trên máy local (C:\ai-advisor1)

# ══════════════════════════════════════════════════
# BƯỚC 1: Tạo feature branch
# ══════════════════════════════════════════════════

```powershell
cd C:\ai-advisor1
git checkout staging
git pull origin staging
git checkout -b feature/market-risk
```

# ══════════════════════════════════════════════════
# BƯỚC 2: Thêm file market_risk_analysis.py
# ══════════════════════════════════════════════════

# Copy file market_risk_analysis.py (đã tải về) vào thư mục gốc:
# C:\ai-advisor1\market_risk_analysis.py
# (Ngang hàng với backend_api.py)


# ══════════════════════════════════════════════════
# BƯỚC 3: Sửa backend_api.py - Thêm MarketRisk model
# ══════════════════════════════════════════════════

# Tìm dòng sau class Signal(Base) và thêm class MarketRisk ngay phía dưới.
# Vị trí: sau class CashPosition (hoặc class cuối cùng trong phần DATABASE MODELS)

# --- THÊM ĐOẠN NÀY ---

```python
class MarketRisk(Base):
    __tablename__ = 'market_risk'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(20), nullable=False, unique=True)
    market_mode = Column(String(20), nullable=False)
    mode_label = Column(String(50))
    risk_score = Column(Integer)
    allocation = Column(Integer)
    description = Column(Text)
    factors_json = Column(Text)
    vnindex_value = Column(Float)
    raw_scores_json = Column(Text)
    analyzed_at = Column(DateTime, default=datetime.now)
```


# ══════════════════════════════════════════════════
# BƯỚC 4: Sửa backend_api.py - Thêm 3 API endpoints
# ══════════════════════════════════════════════════

# Thêm trước dòng "if __name__ == '__main__'" ở cuối file
# hoặc gần khu vực các route khác.

# --- THÊM ĐOẠN NÀY ---

```python
# ========================================================================
# MARKET RISK ENDPOINTS
# ========================================================================

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


@app.route('/api/market-risk/scan', methods=['POST'])
def trigger_market_risk_scan():
    """Trigger market risk analysis"""
    try:
        from market_risk_analysis import run_market_analysis
        
        result = run_market_analysis()
        
        # Save to database
        session = Session()
        today = datetime.now().strftime('%Y-%m-%d')
        
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
    finally:
        try:
            session.close()
        except:
            pass


@app.route('/api/market-risk/history', methods=['GET'])
def get_market_risk_history():
    """Get market risk history (last N days)"""
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
        
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
```


# ══════════════════════════════════════════════════
# BƯỚC 5: Đảm bảo table được tạo tự động
# ══════════════════════════════════════════════════

# Tìm dòng Base.metadata.create_all(engine) trong backend_api.py
# (thường ở phần khởi tạo database)
# Dòng này sẽ tự động tạo table market_risk khi backend khởi động
# Nếu không thấy, thêm sau phần Session = sessionmaker(bind=engine):

```python
Base.metadata.create_all(engine)
```


# ══════════════════════════════════════════════════
# BƯỚC 6: Test local
# ══════════════════════════════════════════════════

```powershell
cd C:\ai-advisor1

# Chạy backend local
python backend_api.py

# Mở terminal khác, test endpoints:

# Test 1: Check health
Invoke-WebRequest -Uri "http://localhost:10000/health"

# Test 2: Lấy market risk (sẽ trả về null ban đầu)
Invoke-WebRequest -Uri "http://localhost:10000/api/market-risk"
# Expected: {"success":true,"data":null,"message":"No market analysis available yet"}

# Test 3: Chạy market risk scan (mất 4-6 phút)
Invoke-WebRequest -Uri "http://localhost:10000/api/market-risk/scan" -Method POST
# Expected: {"success":true,"data":{...},"message":"Market risk analysis completed"}

# Test 4: Lấy kết quả vừa scan
Invoke-WebRequest -Uri "http://localhost:10000/api/market-risk"
# Expected: {"success":true,"data":{"market_mode":"BULL",...}}
```


# ══════════════════════════════════════════════════
# BƯỚC 7: Commit & Push to staging
# ══════════════════════════════════════════════════

```powershell
cd C:\ai-advisor1

# Kiểm tra files thay đổi
git status
# Phải thấy:
#   modified: backend_api.py
#   new file: market_risk_analysis.py

# Add & commit
git add backend_api.py market_risk_analysis.py
git commit -m "feat: add market risk analysis - EOD market mode, risk score, allocation"

# Merge vào staging
git checkout staging
git merge feature/market-risk

# Push staging
git push origin staging
```

# → GitHub Actions auto-deploy tới:
#   Backend: ai-advisor1-staging.onrender.com
#   Frontend: staging.ai-advisor.vn


# ══════════════════════════════════════════════════
# BƯỚC 8: Test trên staging
# ══════════════════════════════════════════════════

```powershell
# Đợi 5-10 phút cho staging deploy xong

# 1. Wake up staging backend (free tier ngủ sau 15 phút)
Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/health"
# Đợi 30-60 giây nếu cold start

# 2. Check table đã tạo
Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/market-risk"
# Expected: {"success":true,"data":null,...}

# 3. Chạy market risk scan trên staging
Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/market-risk/scan" -Method POST
# Đợi 4-6 phút...

# 4. Verify kết quả
Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/market-risk"
# Expected: {"success":true,"data":{"market_mode":"...", "risk_score":..., ...}}

# 5. Check history
Invoke-WebRequest -Uri "https://ai-advisor1-staging.onrender.com/api/market-risk/history?days=7"
```


# ══════════════════════════════════════════════════
# BƯỚC 9: Staging OK → Deploy production
# ══════════════════════════════════════════════════

# Chỉ thực hiện sau khi staging test thành công!

```powershell
git checkout main
git merge staging
git push origin main
```

# → Auto-deploy tới production:
#   Backend: ai-advisor1-backend.onrender.com
#   Frontend: ai-advisor.vn

# Verify production:
```powershell
# Đợi 10-15 phút

Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/market-risk"

# Chạy scan lần đầu
Invoke-WebRequest -Uri "https://ai-advisor1-backend.onrender.com/api/market-risk/scan" -Method POST
```


# ══════════════════════════════════════════════════
# CHECKLIST TỔNG HỢP
# ══════════════════════════════════════════════════

# LOCAL:
# [ ] market_risk_analysis.py đặt đúng vị trí (ngang backend_api.py)
# [ ] backend_api.py có class MarketRisk
# [ ] backend_api.py có 3 endpoints market-risk
# [ ] Base.metadata.create_all(engine) có trong code
# [ ] python backend_api.py chạy không lỗi
# [ ] GET /api/market-risk trả về JSON hợp lệ
# [ ] POST /api/market-risk/scan chạy thành công

# STAGING:
# [ ] git push origin staging thành công
# [ ] Render staging deploy không lỗi
# [ ] GET /api/market-risk trả về data
# [ ] POST /api/market-risk/scan chạy + lưu DB
# [ ] Không ảnh hưởng các endpoint cũ (signals, portfolio, chat)

# PRODUCTION (sau khi staging OK):
# [ ] git merge staging → main
# [ ] Render production deploy thành công
# [ ] Market risk endpoints hoạt động
# [ ] Signal scan vẫn hoạt động bình thường
# [ ] Website ai-advisor.vn load bình thường
