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
  background: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '12px',
  marginBottom: '20px',
  overflow: 'hidden',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
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

  // ── Positive framing helpers ─────────────────────────────────────
  // Thay vì show điểm số thô, dùng label tích cực theo ngưỡng
  const getDimLabel = (score) => {
    if (score >= 75) return { label: 'Xuất sắc ✦',    color: '#22c55e' }
    if (score >= 55) return { label: 'Đang tiến bộ →', color: '#3b82f6' }
    if (score >= 35) return { label: 'Đang xây dựng →', color: '#f59e0b' }
    return              { label: 'Bắt đầu hành trình →', color: '#94a3b8' }
  }
  const klLabel  = getDimLabel(data.kl_score)
  const ktLabel  = getDimLabel(data.kt_score)

  // Coaching message cụ thể theo level — động viên, không phán xét
  const coachMsg = [
    'Bạn đang đặt những viên gạch đầu tiên. Mỗi lần đặt stop loss đúng là một bước tiến thực sự.',
    'Bạn đã có nền tảng. Tập trung vào việc thực hiện nhất quán — kỷ luật nhỏ tạo ra kết quả lớn.',
    'Bạn đang tiến bộ rõ rệt. Giữ vững hệ thống, đặc biệt khi thị trường biến động mạnh.',
    'Bạn có hệ thống vững chắc. Hãy tập trung tối ưu win rate và risk/reward theo từng lệnh.',
    'Bạn đầu tư như một doanh nghiệp. AI-Advisor đồng hành để cùng phân tích các quyết định phức tạp.',
    'Bạn đã đạt đỉnh cao. Kinh nghiệm của bạn là tài sản — hãy tiếp tục đồng hành cùng AI-Advisor.',
  ][lvlIdx] || ''

  // Next step action cụ thể theo level
  const nextAction = [
    'Bước tiếp theo: Đặt stop loss cho lệnh tiếp theo trước khi mua.',
    'Bước tiếp theo: Hoàn thành checklist ≥ 70% số lệnh trong tháng này.',
    'Bước tiếp theo: Giữ ít nhất 1 lệnh đến đúng target đã đặt, không panic sell.',
    'Bước tiếp theo: Duy trì win rate ≥ 45% trong 3 tháng liên tiếp.',
    'Bước tiếp theo: Cải thiện ≥ 2 behavioral bias đã nhận diện trong 90 ngày.',
    'Bạn đã đạt cấp độ cao nhất trong hệ thống IIS.',
  ][lvlIdx] || ''

  // Show/hide điểm chi tiết
  const [showDetail, setShowDetail] = useState(false)

  return (
    <div style={card}>
      {/* Header */}
      <div style={{
        padding: '14px 18px 12px',
        background: '#0f172a',
        borderBottom: '1px solid #1e293b',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>
            Hành trình đầu tư của bạn
          </div>
          {testedAt && (
            <div style={{ fontSize: '11px', color: '#475569', marginTop: '2px' }}>
              Cập nhật lần cuối: {testedAt}
            </div>
          )}
        </div>
        <button
          onClick={() => {
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

      {/* Main content */}
      <div style={{ padding: '16px 18px' }}>

        {/* Level badge — nổi bật, tích cực */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '14px' }}>
          <div style={{
            width: '52px', height: '52px', borderRadius: '14px', flexShrink: 0,
            background: `${lvl.color}18`, border: `2px solid ${lvl.color}55`,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
          }}>
            <div style={{ fontSize: '20px', fontWeight: 700, color: lvl.color, lineHeight: 1 }}>
              {lvlIdx + 1}
            </div>
            <div style={{ fontSize: '9px', color: `${lvl.color}99`, marginTop: '1px' }}>LEVEL</div>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '16px', fontWeight: 700, color: lvl.color, marginBottom: '2px' }}>
              {lvl.name}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={tag(method.color)}>{method.name}</span>
              <span style={{ fontSize: '11px', color: '#475569' }}>
                {method.horizon} · RR {method.rr}
              </span>
            </div>
          </div>
        </div>

        {/* 2 chiều đánh giá — label tích cực, không show số điểm */}
        <div style={{ marginBottom: '12px' }}>
          {/* Kỷ Luật */}
          <div style={{ marginBottom: '9px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>Kỷ luật giao dịch</span>
              <span style={{ fontSize: '11px', fontWeight: 600, color: klLabel.color }}>
                {klLabel.label}
              </span>
            </div>
            <div style={{ height: '5px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: '3px', background: klLabel.color,
                width: `${data.kl_score}%`, transition: 'width .6s ease',
                opacity: 0.85,
              }} />
            </div>
          </div>

          {/* Kiến Thức */}
          <div style={{ marginBottom: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>Nền tảng kiến thức</span>
              <span style={{ fontSize: '11px', fontWeight: 600, color: ktLabel.color }}>
                {ktLabel.label}
              </span>
            </div>
            <div style={{ height: '5px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: '3px', background: ktLabel.color,
                width: `${data.kt_score}%`, transition: 'width .6s ease',
                opacity: 0.85,
              }} />
            </div>
          </div>

          {/* Toggle xem điểm chi tiết */}
          <button
            onClick={() => setShowDetail(v => !v)}
            style={{
              marginTop: '6px', background: 'none', border: 'none',
              color: '#334155', fontSize: '11px', cursor: 'pointer',
              padding: '2px 0', textDecoration: 'underline',
            }}
          >
            {showDetail ? 'Ẩn điểm chi tiết ↑' : 'Xem điểm chi tiết ↓'}
          </button>

          {/* Chi tiết — chỉ hiện khi user chủ động click */}
          {showDetail && (
            <div style={{
              marginTop: '8px', padding: '10px 12px',
              background: '#0f172a', borderRadius: '8px',
              border: '1px solid #1e293b',
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                {[
                  { label: 'IIS Score',    value: `${data.total}/100`,    color: lvl.color },
                  { label: 'Kỷ Luật',     value: `${data.kl_score}/100`, color: '#ef4444' },
                  { label: 'Kiến Thức',   value: `${data.kt_score}/100`, color: '#3b82f6' },
                ].map(({ label, value, color }) => (
                  <div key={label} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', color: '#475569', marginBottom: '3px' }}>{label}</div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color }}>{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Progress đến level tiếp theo */}
        {nextLvl && (
          <div style={{ padding: '10px 12px', background: '#0f172a', borderRadius: '8px', marginBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                Tiến độ lên{' '}
                <span style={{ color: nextLvl.color, fontWeight: 600 }}>{nextLvl.name}</span>
              </span>
              <span style={{ fontSize: '11px', color: nextLvl.color, fontWeight: 600 }}>
                {progressInLvl}%
              </span>
            </div>
            <div style={{ height: '4px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
              <div style={{
                height: '100%',
                background: `linear-gradient(90deg, ${lvl.color}, ${nextLvl.color})`,
                width: `${progressInLvl}%`,
                transition: 'width .6s ease', borderRadius: '2px',
              }} />
            </div>
          </div>
        )}

        {/* Chuyên gia badge */}
        {lvlIdx === 5 && (
          <div style={{ padding: '10px 12px', background: '#2e1065', borderRadius: '8px', marginBottom: '12px', border: '1px solid #7c3aed44' }}>
            <div style={{ fontSize: '12px', color: '#c084fc' }}>
              🏆 Bạn đã đạt cấp độ cao nhất trong hệ thống IIS.
            </div>
          </div>
        )}

        {/* Coaching message — động viên theo level */}
        <div style={{
          borderTop: '1px solid #1e293b', paddingTop: '12px',
          display: 'flex', flexDirection: 'column', gap: '8px',
        }}>
          {/* Coach message */}
          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '16px', flexShrink: 0 }}>💬</span>
            <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.7 }}>
              {coachMsg}
            </div>
          </div>

          {/* Next action — cụ thể, actionable */}
          {nextAction && (
            <div style={{
              display: 'flex', gap: '10px', alignItems: 'flex-start',
              background: `${lvl.color}10`, borderRadius: '8px',
              padding: '8px 10px', border: `1px solid ${lvl.color}22`,
            }}>
              <span style={{ fontSize: '14px', flexShrink: 0 }}>🎯</span>
              <div style={{ fontSize: '12px', color: lvl.color, lineHeight: 1.6, fontWeight: 500 }}>
                {nextAction}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
