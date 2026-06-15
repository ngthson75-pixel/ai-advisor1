import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

// ── Level definitions ────────────────────────────────────────────────
const LEVELS = [
  { name: 'Khởi Hành',  min: 0,  max: 24,  color: '#ef4444', next: 'Định Hướng',
    triggers: ['Đặt stop loss cho ≥ 3 lệnh đầu', 'Mở Clearance Card ≥ 3 lần', 'Hoàn thành checklist ≥ 3 lệnh'] },
  { name: 'Định Hướng', min: 25, max: 39,  color: '#f59e0b', next: 'Phát Triển',
    triggers: ['Checklist ≥ 70% lệnh trong 1 tháng', 'Không average down ngoài kế hoạch 30 ngày', 'Mở email sáng ≥ 10 ngày liên tiếp'] },
  { name: 'Phát Triển', min: 40, max: 54,  color: '#94a3b8', next: 'Vững Vàng',
    triggers: ['Checklist 10/10 lệnh trong 1 tháng', 'Giữ ≥ 1 lệnh đến target (không panic sell)', 'IIS Kỷ Luật tăng ≥ 10 điểm vs baseline'] },
  { name: 'Vững Vàng',  min: 55, max: 69,  color: '#3b82f6', next: 'Tinh Thông',
    triggers: ['Win rate ≥ 45% trong 3 tháng liên tiếp', 'Đọc Monthly IIS Report 3 tháng liên tiếp', 'Discipline Streak ≥ 20 ngày'] },
  { name: 'Tinh Thông', min: 70, max: 84,  color: '#22c55e', next: 'Chuyên Gia',
    triggers: ['IIS retest ≥ 70 sau 90 ngày', 'Return dương 2 quý liên tiếp', '≥ 2 behavioral bias đã cải thiện'] },
  { name: 'Chuyên Gia', min: 85, max: 100, color: '#a855f7', next: null,
    triggers: [] },
]

const METHOD_LABELS = {
  luot_song: { name: 'Lướt Sóng AI', horizon: 'Ngắn hạn',  rr: '1:2–3',   color: '#3b82f6' },
  bat_song:  { name: 'Bắt Sóng AI',  horizon: 'Trung hạn', rr: '1:3–5',   color: '#f59e0b' },
  tich_san:  { name: 'Tích Sản AI',  horizon: 'Dài hạn',   rr: '1:5–15',  color: '#22c55e' },
  hybrid_sm: { name: 'Hybrid Lướt + Bắt', horizon: 'Ngắn + Trung', rr: '1:2.5–4', color: '#3b82f6' },
  hybrid_ml: { name: 'Hybrid Bắt + Tích', horizon: 'Trung + Dài',  rr: '1:3.5–8', color: '#f59e0b' },
}

// ── Styles ───────────────────────────────────────────────────────────
const card = {
  background: '#0f172a',
  border: '1px solid #1e3a5f',
  borderRadius: '16px',
  overflow: 'hidden',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  boxShadow: '0 4px 24px rgba(59,130,246,0.08)',
}
const tag = (color) => ({
  display: 'inline-block', fontSize: '11px', fontWeight: 500,
  padding: '2px 8px', borderRadius: '4px',
  background: `${color}20`, color, border: `1px solid ${color}40`,
})

export default function IISScoreWidget({ userId, onRequestUpdate }) {
  const [data,    setData]    = useState(null)   // IIS result from backend
  const [loading, setLoading] = useState(true)
  const [canUpdate, setCanUpdate] = useState(false)

  useEffect(() => {
    if (!userId) { setLoading(false); return }

    // Bước 1: Check localStorage ngay lập tức — hiển thị kết quả không chờ backend
    try {
      const cached = localStorage.getItem(`iis_result_${userId}`)
      if (cached) {
        const local = JSON.parse(cached)
        if (local.has_result) {
          setData(local)
          if (local.tested_at) {
            const days = (Date.now() - new Date(local.tested_at)) / 86400000
            setCanUpdate(days >= 30)
          }
          setLoading(false)
          // Vẫn sync từ API ở background để cập nhật nếu có retest mới hơn
          fetch(`${API_URL}/iis/result/${encodeURIComponent(userId)}`)
            .then(r => r.json())
            .then(d => {
              if (d.has_result && d.tested_at) {
                const localTime = new Date(local.tested_at || 0).getTime()
                const apiTime   = new Date(d.tested_at).getTime()
                if (apiTime >= localTime) {
                  setData(d)  // API có kết quả mới hơn localStorage
                  try { localStorage.setItem(`iis_result_${userId}`, JSON.stringify({...d})) } catch {}
                }
              } else if (!d.has_result && local.answers) {
                // Backend không có data nhưng localStorage có → re-submit
                console.log('[IIS] Re-submitting to backend...')
                fetch(`${API_URL}/iis/submit`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ user_id: userId, answers: local.answers })
                }).catch(() => {})
              }
            })
            .catch(() => {})
          return
        }
      }
    } catch {}

    // Bước 2: Không có localStorage — fetch từ API
    fetch(`${API_URL}/iis/result/${encodeURIComponent(userId)}`)
      .then(r => r.json())
      .then(d => {
        if (d.has_result) {
          setData(d)
          try { localStorage.setItem(`iis_result_${userId}`, JSON.stringify(d)) } catch {}
          if (d.tested_at) {
            const days = (Date.now() - new Date(d.tested_at)) / 86400000
            setCanUpdate(days >= 30)
          }
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [userId])

  // ── Loading ──────────────────────────────────────────────────────
  if (loading) return (
    <div style={{ ...card, padding: '20px 16px', textAlign: 'center' }}>
      <div style={{ fontSize: '12px', color: '#475569' }}>Đang tải IIS Score...</div>
    </div>
  )

  // ── No result — prompt to take test ─────────────────────────────
  if (!data) return (
    <div style={{
      ...card,
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      border: '1px solid #3b82f655',
    }}>
      <div style={{ padding: '24px 20px', textAlign: 'center' }}>
        <div style={{ fontSize: '32px', marginBottom: '8px' }}>🎯</div>
        <div style={{ fontSize: '15px', fontWeight: 500, color: '#e2e8f0', marginBottom: '6px' }}>
          Bạn chưa có IIS Score
        </div>
        <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px', lineHeight: 1.6 }}>
          Làm bài test 15 câu để biết phong cách đầu tư phù hợp nhất với bạn
        </div>
        <button
          onClick={onRequestUpdate}
          style={{
            background: '#3b82f6', color: '#fff', border: 'none',
            borderRadius: '8px', padding: '10px 24px',
            fontSize: '13px', fontWeight: 500, cursor: 'pointer',
          }}
        >
          Làm IIS Test ngay →
        </button>
      </div>
    </div>
  )

  // ── Has result ───────────────────────────────────────────────────
  const lvl      = LEVELS.find(l => l.name === data.level) || LEVELS[0]
  const lvlIdx   = LEVELS.indexOf(lvl)
  const method   = METHOD_LABELS[data.method] || METHOD_LABELS.bat_song
  const testedAt = data.tested_at
    ? new Date(data.tested_at).toLocaleDateString('vi-VN')
    : null

  // Progress to next level
  const nextLvl       = LEVELS[lvlIdx + 1]
  const progressInLvl = nextLvl
    ? Math.round(((data.total - lvl.min) / (lvl.max - lvl.min + 1)) * 100)
    : 100

  return (
    <div style={card}>
      {/* Header */}
      <div style={{
        padding: '14px 18px 12px',
        background: 'linear-gradient(135deg, #3b82f622, #3b82f611)',
        borderBottom: '1px solid #1e293b',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>
            Investor Intelligence Score
          </div>
          {testedAt && (
            <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>
              Cập nhật lần cuối: {testedAt}
            </div>
          )}
        </div>
        <button
          onClick={() => {
            // Xoá cache để sau khi retest sẽ lưu kết quả mới
            try { localStorage.removeItem(`iis_result_${userId}`) } catch {}
            onRequestUpdate()
          }}
          disabled={!canUpdate}
          title={canUpdate ? 'Cập nhật IIS Score' : 'Có thể cập nhật sau 30 ngày từ lần test trước'}
          style={{
            fontSize: '11px', padding: '5px 12px', borderRadius: '6px',
            border: '1px solid #334155', cursor: canUpdate ? 'pointer' : 'not-allowed',
            background: 'transparent',
            color: canUpdate ? '#94a3b8' : '#334155',
            display: 'flex', alignItems: 'center', gap: '4px',
          }}
        >
          ↻ Cập nhật IIS
        </button>
      </div>

      {/* Score area */}
      <div style={{ padding: '16px 18px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '20px', alignItems: 'start' }}>

          {/* Left — big score */}
          <div style={{ textAlign: 'center', minWidth: '90px' }}>
            <div style={{ fontSize: '52px', fontWeight: 600, color: lvl.color, lineHeight: 1 }}>
              {data.total}
            </div>
            <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>/100</div>
            <div style={{
              marginTop: '8px', fontSize: '12px', fontWeight: 600, color: lvl.color,
              background: `${lvl.color}18`, border: `1px solid ${lvl.color}44`,
              borderRadius: '6px', padding: '3px 8px',
            }}>
              {lvlIdx + 1}. {lvl.name}
            </div>
          </div>

          {/* Right — bars + method */}
          <div>
            {/* IIS Kỷ Luật */}
            <div style={{ marginBottom: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
                <span>IIS Kỷ Luật</span>
                <span style={{ fontWeight: 500, color: '#e2e8f0' }}>{data.kl_score}/100</span>
              </div>
              <div style={{ height: '5px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: '3px', background: '#ef4444', width: `${data.kl_score}%`, transition: 'width .6s ease' }} />
              </div>
            </div>

            {/* IIS Kiến Thức */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
                <span>IIS Kiến Thức</span>
                <span style={{ fontWeight: 500, color: '#e2e8f0' }}>{data.kt_score}/100</span>
              </div>
              <div style={{ height: '5px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: '3px', background: '#3b82f6', width: `${data.kt_score}%`, transition: 'width .6s ease' }} />
              </div>
            </div>

            {/* Method */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={tag(method.color)}>{method.name}</span>
              <span style={{ fontSize: '11px', color: '#475569' }}>
                {method.horizon} · RR {method.rr}
              </span>
            </div>
          </div>
        </div>

        {/* Level progress */}
        {nextLvl && (
          <div style={{ marginTop: '14px', padding: '10px 12px', background: '#0f172a', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                Tiến độ → <span style={{ color: nextLvl.color, fontWeight: 500 }}>{nextLvl.name}</span>
              </span>
              <span style={{ fontSize: '11px', color: '#475569' }}>{progressInLvl}%</span>
            </div>
            <div style={{ height: '3px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{ height: '100%', background: `linear-gradient(90deg, ${lvl.color}, ${nextLvl.color})`, width: `${progressInLvl}%`, transition: 'width .6s ease', borderRadius: '2px' }} />
            </div>
          </div>
        )}

        {/* Motivating CTA — hối thúc dùng app thường xuyên */}
        <div style={{
          marginTop: '12px', borderTop: '1px solid #1e293b', paddingTop: '12px',
          display: 'flex', gap: '10px', alignItems: 'flex-start',
        }}>
          <span style={{ fontSize: '18px', flexShrink: 0, marginTop: '1px' }}>💬</span>
          <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.7 }}>
            Hãy thường xuyên trao đổi với{' '}
            <span style={{ color: lvl.color, fontWeight: 500 }}>AI-Advisor chat</span>
            {' '}để hệ thống giúp bạn kỷ luật và từng bước nâng hiệu quả đầu tư của bạn.
          </div>
        </div>

        {/* Chuyên gia */}
        {lvlIdx === 5 && (
          <div style={{ marginTop: '12px', padding: '10px 12px', background: '#2e1065', borderRadius: '8px', border: '1px solid #7c3aed44' }}>
            <div style={{ fontSize: '12px', color: '#c084fc' }}>
              🏆 Bạn đã đạt cấp độ cao nhất — Chuyên Gia. Cảm ơn bạn đã đồng hành cùng AI-Advisor!
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
