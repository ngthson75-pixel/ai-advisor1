import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

// ── Question bank (mirrors iis_engine.py) ─────────────────────────────
const QUESTIONS = [
  // Chiều 1: IIS Kỷ Luật
  {
    id: 'Q1', dim: 'kl',
    text: 'Bạn thường đặt stop loss như thế nào?',
    options: [
      { text: 'Không bao giờ đặt stop loss', score: 0 },
      { text: 'Đặt sau khi mua, dựa trên cảm giác', score: 1 },
      { text: 'Đặt trước khi mua, dựa trên vùng hỗ trợ kỹ thuật', score: 3 },
      { text: 'Đặt trước, không bao giờ dời xuống — chỉ được kéo lên', score: 4 },
    ]
  },
  {
    id: 'Q2', dim: 'kl',
    text: 'Cổ phiếu đang lỗ 8%, SL đặt ở -12%, giá giảm thêm 3%. Bạn làm gì?',
    options: [
      { text: 'Dời stop loss xuống -16% để tránh bị dừng lỗ', score: 0 },
      { text: 'Thoát ngay, không chờ stop hit', score: 1 },
      { text: 'Giữ nguyên plan, chờ stop loss hit đúng mức đã đặt', score: 3 },
      { text: 'Xem lại luận điểm — nếu vẫn đúng giữ, sai thì cắt ngay', score: 4 },
    ]
  },
  {
    id: 'Q3', dim: 'kl',
    text: 'HPG tăng trần 3 phiên liên tiếp. Group đang mua ồ ạt. Bạn chưa có vị thế. Bạn làm gì?',
    options: [
      { text: 'Mua ngay, sợ bỏ lỡ cơ hội', score: 0 },
      { text: 'Hỏi thêm vài người rồi quyết định', score: 1 },
      { text: 'Kiểm tra setup kỹ thuật, chỉ mua nếu đủ điều kiện', score: 3 },
      { text: 'Chờ pullback về vùng hỗ trợ — không mua đuổi theo đám đông', score: 4 },
    ]
  },
  {
    id: 'Q4', dim: 'kl',
    text: 'VN-Index đột ngột giảm 2% trong phiên. Cổ phiếu bạn đang lỗ 6%. Phản xạ đầu tiên?',
    options: [
      { text: 'Mở app ngay, cân nhắc bán hết để cắt lỗ', score: 0 },
      { text: 'Hồi hộp, theo dõi giá liên tục', score: 1 },
      { text: 'Kiểm tra: stop loss hit chưa? Nếu chưa → giữ nguyên plan', score: 3 },
      { text: 'Tắt app, làm việc khác — 1 ngày không ảnh hưởng plan', score: 4 },
    ]
  },
  {
    id: 'Q5', dim: 'kl',
    text: 'Ba lệnh gần nhất của bạn được đặt dựa trên cơ sở nào?',
    options: [
      { text: 'Tip từ group, người quen, hoặc thấy nhiều người đang mua', score: 0 },
      { text: 'Cảm tính và xem chart sơ qua', score: 1 },
      { text: 'Setup kỹ thuật rõ ràng, có entry/SL xác định', score: 3 },
      { text: 'Hệ thống cụ thể: entry, SL, TP, size — xác định trước khi mua', score: 4 },
    ]
  },
  // Chiều 2: IIS Phương Pháp
  {
    id: 'Q6', dim: 'pp',
    text: 'Mỗi ngày bạn có bao nhiêu thời gian thực sự cho việc đầu tư?',
    options: [
      { text: 'Dưới 20 phút — check cuối tuần là chủ yếu', method: 'l' },
      { text: '20–45 phút — buổi sáng trước giờ làm hoặc tối', method: 'm' },
      { text: '45–90 phút — xem trước và sau giờ giao dịch', method: 'm' },
      { text: 'Trên 90 phút — theo dõi được trong giờ giao dịch', method: 's' },
    ]
  },
  {
    id: 'Q7', dim: 'pp',
    text: 'Bạn giữ lệnh đang lỗ 7% sau 2 tuần. Luận điểm đầu tư vẫn còn giá trị. Cảm giác thật sự?',
    options: [
      { text: 'Rất khó chịu, muốn thoát sớm cho nhẹ đầu', method: 's' },
      { text: 'Lo nhưng kiên nhẫn được thêm 2–3 tuần', method: 'm' },
      { text: 'Bình thường — tôi mua vì FA tốt, giá ngắn hạn không phải vấn đề', method: 'l' },
    ]
  },
  {
    id: 'Q8', dim: 'pp',
    text: 'Bạn thích phân tích cổ phiếu bằng cách nào nhất?',
    options: [
      { text: 'Biểu đồ kỹ thuật — MA, RSI, Volume, candlestick', method: 's' },
      { text: 'Kết hợp: TA để timing entry, FA để chọn cổ phiếu chất lượng', method: 'm' },
      { text: 'Báo cáo tài chính — P/E, ROE, tăng trưởng EPS, dòng tiền', method: 'l' },
    ]
  },
  {
    id: 'Q9', dim: 'pp',
    text: 'Trong 1 năm, bạn muốn thực hiện bao nhiêu lệnh giao dịch?',
    options: [
      { text: '3–10 lệnh — rất chọn lọc, mỗi lệnh giữ rất lâu', method: 'l' },
      { text: '10–30 lệnh — chọn lọc, giữ vài tháng mỗi lệnh', method: 'm' },
      { text: '30–80 lệnh — nhiều cơ hội, mỗi lệnh ngắn hơn', method: 's' },
    ]
  },
  {
    id: 'Q10', dim: 'pp',
    text: 'Công việc và lối sống của bạn hiện tại?',
    options: [
      { text: 'Rất bận — ít có thời gian theo dõi thị trường ban ngày', method: 'l' },
      { text: 'Văn phòng — có thể check điện thoại giữa giờ nghỉ', method: 'm' },
      { text: 'Linh hoạt — có thể theo dõi thị trường trong giờ giao dịch', method: 's' },
    ]
  },
  // Chiều 3: IIS Kiến Thức
  {
    id: 'Q11', dim: 'kt',
    text: 'Hệ thống có: win rate 42%, lãi trung bình +16%, lỗ trung bình -6%. Bạn đánh giá thế nào?',
    options: [
      { text: 'Tệ — thua nhiều hơn thắng, không dùng được', score: 0 },
      { text: 'Bình thường — cần thêm thông tin mới kết luận được', score: 1 },
      { text: 'Tốt — EV = (0.42×16)-(0.58×6) = +3.2% mỗi lệnh, EV dương', score: 4 },
    ]
  },
  {
    id: 'Q12', dim: 'kt',
    text: 'VN-Index dưới MA20, MA50 và MA200 cùng lúc. Market breadth âm 3 tuần liên tiếp. Bạn nên làm gì?',
    options: [
      { text: 'Mua cổ phiếu tốt đang rẻ hơn — cơ hội tốt', score: 0 },
      { text: 'Chờ xem thêm vài phiên rồi quyết định', score: 1 },
      { text: 'Giảm tỷ trọng, tăng tiền mặt, không mở lệnh mới', score: 3 },
      { text: 'Chuyển sang chế độ Bear — chiến lược và tỷ trọng thay đổi hoàn toàn', score: 4 },
    ]
  },
  {
    id: 'Q13', dim: 'kt',
    text: 'Tài khoản 400 triệu. Risk 2%/lệnh. Stop loss dự kiến -8% từ giá mua. Mua tối đa bao nhiêu?',
    options: [
      { text: 'Không biết tính — thường mua theo cảm tính', score: 0 },
      { text: 'Khoảng 50–80 triệu, ước chừng', score: 1 },
      { text: '400M × 2% = 8M risk. 8M ÷ 8% = 100 triệu tối đa', score: 4 },
    ]
  },
  {
    id: 'Q14', dim: 'kt',
    text: 'Cổ phiếu Y: P/E=7 (ngành=16), ROE=24%, nợ/vốn=0.25, EPS tăng 35% YoY. Bạn kết luận gì?',
    options: [
      { text: 'Không đọc được các chỉ số này', score: 0 },
      { text: 'Có vẻ tốt nhưng chưa chắc — cần hỏi thêm', score: 1 },
      { text: 'Cổ phiếu đang rẻ hơn ngành, nền tảng tốt — đáng nghiên cứu sâu', score: 3 },
      { text: 'Discount 56% so ngành + ROE cao + tăng trưởng mạnh + nợ thấp = Value play', score: 4 },
    ]
  },
  {
    id: 'Q15', dim: 'kt',
    text: 'Sau khi mua, bạn sẽ bán khi nào? (chọn mô tả đúng thực tế nhất)',
    options: [
      { text: 'Khi thấy lãi đủ rồi, hoặc khi cần tiền', score: 0 },
      { text: 'Khi lãi 10–15% hoặc khi nghe tin xấu về cổ phiếu', score: 1 },
      { text: 'Khi đạt target price đã đặt trước, hoặc stop loss hit', score: 3 },
      { text: 'Khi stop loss hit, trailing stop kích hoạt, hoặc luận điểm thay đổi cơ bản', score: 4 },
    ]
  },
]

const LEVELS = [
  { name: 'Khởi Hành',  min: 0,  max: 24,  color: '#ef4444', bg: '#1a0a0a' },
  { name: 'Định Hướng', min: 25, max: 39,  color: '#f59e0b', bg: '#1a1000' },
  { name: 'Phát Triển', min: 40, max: 54,  color: '#94a3b8', bg: '#0f172a' },
  { name: 'Vững Vàng',  min: 55, max: 69,  color: '#3b82f6', bg: '#0a1628' },
  { name: 'Tinh Thông', min: 70, max: 84,  color: '#22c55e', bg: '#091a10' },
  { name: 'Chuyên Gia', min: 85, max: 100, color: '#a855f7', bg: '#0f0a1a' },
]

const METHOD_MAP = {
  luot_song:  { name: 'Lướt Sóng AI', horizon: 'Ngắn hạn',         hold: '3 ngày – 3 tuần',    wr: '45–55%', rr: '1:2–3',    color: '#3b82f6' },
  bat_song:   { name: 'Bắt Sóng AI',  horizon: 'Trung hạn',         hold: '3 tuần – 4 tháng',   wr: '50–62%', rr: '1:3–5',    color: '#f59e0b' },
  tich_san:   { name: 'Tích Sản AI',  horizon: 'Dài hạn',            hold: '4 tháng – 2+ năm',   wr: '60–70%', rr: '1:5–15',   color: '#22c55e' },
  hybrid_sm:  { name: 'Hybrid Lướt + Bắt', horizon: 'Ngắn + Trung', hold: 'Linh hoạt',          wr: '47–58%', rr: '1:2.5–4',  color: '#3b82f6' },
  hybrid_ml:  { name: 'Hybrid Bắt + Tích', horizon: 'Trung + Dài',  hold: 'Linh hoạt',          wr: '52–65%', rr: '1:3.5–8',  color: '#f59e0b' },
}

const DIM_CONFIG = {
  kl: { label: 'IIS Kỷ Luật',     color: '#ef4444', desc: 'Kỷ luật giao dịch' },
  pp: { label: 'IIS Phương Pháp', color: '#f59e0b', desc: 'Phong cách phù hợp' },
  kt: { label: 'IIS Kiến Thức',   color: '#3b82f6', desc: 'Hiểu biết nền tảng' },
}

// ── Styles ─────────────────────────────────────────────────────────────
const S = {
  wrap: {
    maxWidth: '600px', margin: '0 auto', padding: '24px 16px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    color: '#e2e8f0',
  },
  card: {
    background: '#1e293b', border: '1px solid #334155',
    borderRadius: '12px', overflow: 'hidden', marginBottom: '16px',
  },
  cardHead: {
    padding: '14px 18px', background: '#0f172a',
    borderBottom: '1px solid #334155',
  },
  cardBody: { padding: '12px 8px' },
  opt: (sel) => ({
    display: 'flex', alignItems: 'flex-start', gap: '10px',
    padding: '10px 12px', borderRadius: '8px', cursor: 'pointer',
    marginBottom: '4px',
    background: sel ? 'rgba(59,130,246,0.12)' : 'transparent',
    border: sel ? '1px solid rgba(59,130,246,0.4)' : '1px solid transparent',
    transition: 'all .12s',
  }),
  radio: (sel) => ({
    flexShrink: 0, width: '16px', height: '16px', borderRadius: '50%',
    border: sel ? '5px solid #3b82f6' : '2px solid #475569',
    marginTop: '3px', transition: 'all .12s',
    background: sel ? '#3b82f6' : 'transparent',
  }),
  optText: { fontSize: '15px', color: '#cbd5e1', lineHeight: 1.6 },
  btn: (primary, disabled) => ({
    padding: '9px 20px', borderRadius: '8px', cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: '13px', fontWeight: 500, border: 'none', transition: 'all .12s',
    background: disabled ? '#1e293b' : primary ? '#3b82f6' : '#1e293b',
    color: disabled ? '#475569' : primary ? '#fff' : '#94a3b8',
    border: primary ? 'none' : '1px solid #334155',
    opacity: disabled ? 0.5 : 1,
  }),
  progTrack: {
    height: '4px', background: '#1e293b', borderRadius: '2px', overflow: 'hidden',
    marginBottom: '12px',
  },
  dimPip: (state, dim) => {
    const colors = { kl: '#ef4444', pp: '#f59e0b', kt: '#3b82f6' }
    return {
      flex: 1, height: '3px', borderRadius: '2px', transition: 'background .2s',
      background: state === 'done' ? '#22c55e' : state === 'active' ? colors[dim] : '#1e293b',
    }
  },
  scoreBar: (pct, color) => ({
    height: '7px', borderRadius: '4px', background: color,
    width: `${pct}%`, transition: 'width .6s ease',
  }),
}


// ── Client-side scoring (mirrors iis_engine.py) ──────────────────────
function computeScoreLocally(answers) {
  let kl = 0, kt = 0
  const mv = { s: 0, m: 0, l: 0 }
  QUESTIONS.forEach((q, i) => {
    const opt = q.options[answers[i]]
    if (!opt) return
    if (q.dim === 'kl') kl += opt.score || 0
    if (q.dim === 'kt') kt += opt.score || 0
    if (q.dim === 'pp' && opt.method) mv[opt.method]++
  })
  const kl_score = Math.round(kl / 20 * 100)
  const kt_score = Math.round(kt / 20 * 100)
  const total    = Math.round(kl_score * 0.5 + kt_score * 0.5)
  const level    = LEVELS.find(l => total >= l.min && total <= l.max) || LEVELS[5]

  const sorted = Object.entries(mv).sort((a, b) => b[1] - a[1])
  const [top, sec] = sorted
  let method
  if (top[1] - sec[1] >= 2) {
    method = { s: 'luot_song', m: 'bat_song', l: 'tich_san' }[top[0]]
  } else {
    const combo = [top[0], sec[0]].sort().join('')
    method = combo === 'ms' ? 'hybrid_sm' : combo === 'lm' ? 'hybrid_ml' : 'hybrid_sm'
  }
  const mInfo = METHOD_MAP[method] || METHOD_MAP.bat_song
  const improve_tips = []
  if (kl_score < 50) improve_tips.push('Ưu tiên xây kỷ luật: luôn đặt stop loss trước khi mua và hoàn thành pre-trade checklist.')
  else if (kl_score < 70) improve_tips.push('Kỷ luật đang tốt — tiếp tục duy trì, đặc biệt khi thị trường biến động mạnh.')
  if (kt_score < 50) improve_tips.push('Nâng kiến thức: học cách tính Risk-Reward, đọc Market Regime và FA cơ bản.')
  else if (kt_score < 70) improve_tips.push('Kiến thức khá tốt — áp dụng EV thinking vào từng quyết định giao dịch.')

  return {
    kl_score, kt_score, total,
    level:          level.name,
    level_color:    level.color,
    ai_role:        ['Bảo vệ','Dạy','Huấn luyện','Tối ưu','Đồng hành','Alumni'][LEVELS.indexOf(level)],
    method,
    method_name:    mInfo.name,
    method_horizon: mInfo.horizon,
    method_hold:    mInfo.hold,
    method_win_rate:mInfo.wr,
    method_rr:      mInfo.rr,
    method_strategies: [],
    buckets:        mInfo.buckets || null,
    improve_tips,
  }
}

// Lưu kết quả lên backend trong nền — không block UI
async function saveToBackgroundSilent(userId, answers) {
  for (let attempt = 1; attempt <= 6; attempt++) {
    try {
      const res = await fetch(`${API_URL}/iis/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, answers }),
      })
      const data = await res.json()
      if (data.success) return  // Lưu thành công
    } catch { /* ignore */ }
    // Đợi trước khi retry (exponential: 5s, 10s, 20s, 40s, 60s)
    await new Promise(r => setTimeout(r, Math.min(5000 * Math.pow(2, attempt - 1), 60000)))
  }
}

// ── Component ──────────────────────────────────────────────────────────
export default function IISTest({ userId, onComplete }) {
  const [phase, setPhase]       = useState('loading')   // loading|check|intro|test|submitting|result
  const [cur,   setCur]         = useState(0)
  const [ans,   setAns]         = useState(new Array(15).fill(null))
  const [result, setResult]     = useState(null)
  const [prevResult, setPrev]   = useState(null)
  const [error, setError]       = useState(null)

  // Check existing result on mount
  useEffect(() => {
    if (!userId) { setPhase('intro'); return }
    fetch(`${API_URL}/iis/result/${encodeURIComponent(userId)}`)
      .then(r => r.json())
      .then(data => {
        if (data.has_result) {
          setPrev(data)
          setPhase('result_prev')
        } else {
          setPhase('intro')
        }
      })
      .catch(() => setPhase('intro'))
  }, [userId])

  const pickOpt = (i) => {
    const next = [...ans]
    next[cur] = i
    setAns(next)
  }

  const goNext = async () => {
    if (ans[cur] === null) return
    if (cur < 14) { setCur(c => c + 1); return }
    // Last question → submit
    setPhase('submitting')

    // Tính điểm ngay trên frontend — không chờ server
    const clientResult = computeScoreLocally(ans)
    setResult(clientResult)
    setPhase('result')

    // Lưu vào localStorage ngay lập tức — widget đọc được ngay
    const uid = userId || 'guest'
    const localRecord = {
      total:      clientResult.total,
      kl_score:   clientResult.kl_score,
      kt_score:   clientResult.kt_score,
      level:      clientResult.level,
      method:     clientResult.method,
      has_result: true,
      tested_at:  new Date().toISOString(),
      answers:    ans,
    }
    try { localStorage.setItem(`iis_result_${uid}`, JSON.stringify(localRecord)) } catch {}

    // Lưu lên backend chạy ngầm (không block user, retry 6 lần)
    saveToBackgroundSilent(uid, ans)
  }

  const restart = () => {
    setAns(new Array(15).fill(null))
    setCur(0)
    setResult(null)
    setError(null)
    setPhase('intro')
  }

  const q      = QUESTIONS[cur]
  const dimCfg = q ? DIM_CONFIG[q.dim] : null
  const pct    = Math.round(cur / 15 * 100)

  // ── Loading ─────────────────────────────────────────────────────────
  if (phase === 'loading') return (
    <div style={{ ...S.wrap, textAlign: 'center', paddingTop: '60px' }}>
      <div style={{ fontSize: '13px', color: '#64748b' }}>Đang tải...</div>
    </div>
  )

  // ── Previous result view ─────────────────────────────────────────────
  if (phase === 'result_prev' && prevResult) {
    const lvl   = LEVELS.find(l => l.name === prevResult.level) || LEVELS[0]
    const mInfo = METHOD_MAP[prevResult.method] || METHOD_MAP.bat_song
    const tested = prevResult.tested_at
      ? new Date(prevResult.tested_at).toLocaleDateString('vi-VN')
      : null
    return (
      <div style={S.wrap}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div style={{ fontSize: '11px', fontWeight: 500, color: '#3b82f6', letterSpacing: '.06em', marginBottom: '6px' }}>KẾT QUẢ IIS CỦA BẠN</div>
          <div style={{ fontSize: '48px', fontWeight: 600, color: '#f1f5f9', lineHeight: 1 }}>{prevResult.total}</div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Investor Intelligence Score</div>
          <div style={{ fontSize: '14px', fontWeight: 500, color: lvl.color, marginTop: '6px' }}>
            {LEVELS.indexOf(lvl) + 1}. {lvl.name}
          </div>
          {tested && <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>Làm lần cuối: {tested}</div>}
        </div>

        <div style={{ ...S.card, marginBottom: '12px' }}>
          <div style={{ padding: '14px 16px' }}>
            {[
              { label: 'IIS Kỷ Luật',   val: prevResult.kl_score, color: '#ef4444' },
              { label: 'IIS Kiến Thức', val: prevResult.kt_score, color: '#3b82f6' },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8', marginBottom: '5px' }}>
                  <span>{label}</span><span style={{ fontWeight: 500, color: '#e2e8f0' }}>{val}/100</span>
                </div>
                <div style={{ height: '6px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={S.scoreBar(val, color)} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ ...S.card, border: `1px solid ${mInfo.color}33`, background: `${mInfo.color}0d`, marginBottom: '16px' }}>
          <div style={{ padding: '14px 16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 500, color: mInfo.color, marginBottom: '3px' }}>
              Phương pháp: {mInfo.name}
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '10px' }}>
              {mInfo.horizon} · Hold {mInfo.hold}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              {[
                ['Win Rate', mInfo.wr],
                ['Risk-Reward', mInfo.rr],
                ['Thời hạn', mInfo.horizon],
                ['Nắm giữ', mInfo.hold],
              ].map(([k, v]) => (
                <div key={k} style={{ background: '#0f172a', borderRadius: '6px', padding: '8px 10px', border: '1px solid #1e293b' }}>
                  <div style={{ fontSize: '10px', color: '#475569', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '.04em' }}>{k}</div>
                  <div style={{ fontSize: '12px', fontWeight: 500, color: '#e2e8f0' }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button style={S.btn(false, false)} onClick={restart}>Làm lại test</button>
          <button style={{ ...S.btn(true, false), flex: 1 }} onClick={() => setPhase('intro')}>
            Cập nhật IIS Score →
          </button>
        </div>
      </div>
    )
  }

  // ── Intro ────────────────────────────────────────────────────────────
  if (phase === 'intro') return (
    <div style={S.wrap}>
      <div style={{ textAlign: 'center', padding: '12px 0 20px' }}>
        <div style={{ fontSize: '11px', fontWeight: 500, color: '#3b82f6', letterSpacing: '.08em', marginBottom: '8px' }}>AI-ADVISOR</div>
        <div style={{ fontSize: '22px', fontWeight: 500, color: '#f1f5f9', marginBottom: '6px' }}>Investor Intelligence Score</div>
        <div style={{ fontSize: '14px', color: '#64748b', lineHeight: 1.7, marginBottom: '20px' }}>
          15 câu hỏi · 5 phút · Kết quả cá nhân hóa<br/>
          Xác định phong cách đầu tư phù hợp nhất với bạn
        </div>
      </div>

      {/* 3 dimensions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '20px' }}>
        {Object.entries(DIM_CONFIG).map(([k, d]) => (
          <div key={k} style={{ ...S.card, marginBottom: 0 }}>
            <div style={{ padding: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', fontWeight: 500, color: d.color, marginBottom: '4px' }}>{d.label}</div>
              <div style={{ fontSize: '12px', color: '#475569' }}>{d.desc}</div>
              <div style={{ fontSize: '10px', color: '#334155', marginTop: '3px' }}>
                {k === 'kl' ? 'Q1–Q5' : k === 'pp' ? 'Q6–Q10' : 'Q11–Q15'}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 6 levels */}
      <div style={{ ...S.card, marginBottom: '20px' }}>
        <div style={{ padding: '12px 16px 8px', borderBottom: '1px solid #334155' }}>
          <div style={{ fontSize: '12px', color: '#64748b' }}>6 cấp độ nhà đầu tư</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', padding: '10px 8px 8px' }}>
          {LEVELS.map((l, i) => (
            <div key={l.name} style={{ textAlign: 'center', padding: '6px 2px' }}>
              <div style={{ fontSize: '16px', fontWeight: 500, color: l.color, lineHeight: 1 }}>{i + 1}</div>
              <div style={{ fontSize: '10px', color: '#64748b', lineHeight: 1.3, marginTop: '3px' }}>{l.name}</div>
              <div style={{ fontSize: '9px', color: '#334155' }}>{l.min}–{l.max}</div>
            </div>
          ))}
        </div>
      </div>

      <button
        style={{ ...S.btn(true, false), width: '100%', padding: '12px', fontSize: '14px' }}
        onClick={() => setPhase('test')}
      >
        Bắt đầu IIS Test →
      </button>
    </div>
  )

  // ── Test ─────────────────────────────────────────────────────────────
  if (phase === 'test' || phase === 'submitting') return (
    <div style={S.wrap}>
      {/* Progress */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#64748b', marginBottom: '6px' }}>
          <span>
            {q.dim === 'kl' ? 'Chiều 1/3 — IIS Kỷ Luật' : q.dim === 'pp' ? 'Chiều 2/3 — IIS Phương Pháp' : 'Chiều 3/3 — IIS Kiến Thức'}
          </span>
          <span>{cur} / 15</span>
        </div>
        <div style={S.progTrack}>
          <div style={{ height: '100%', borderRadius: '2px', background: '#3b82f6', width: `${pct}%`, transition: 'width .3s' }} />
        </div>
        <div style={{ display: 'flex', gap: '3px' }}>
          {QUESTIONS.map((qq, i) => (
            <div key={i} style={S.dimPip(ans[i] !== null ? 'done' : i === cur ? 'active' : 'idle', qq.dim)} />
          ))}
        </div>
      </div>

      {/* Dim badge */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: '5px',
        fontSize: '11px', fontWeight: 500, padding: '3px 10px', borderRadius: '20px',
        background: `${dimCfg.color}18`, color: dimCfg.color, marginBottom: '12px',
      }}>
        {dimCfg.label} — {dimCfg.desc}
      </div>

      {/* Question card */}
      <div style={S.card}>
        <div style={S.cardHead}>
          <div style={{ fontSize: '12px', color: '#475569', marginBottom: '5px', fontWeight: 500 }}>Câu {cur + 1} / 15</div>
          <div style={{ fontSize: '16px', fontWeight: 500, color: '#e2e8f0', lineHeight: 1.6 }}>{q.text}</div>
        </div>
        <div style={S.cardBody}>
          {q.options.map((o, i) => (
            <div key={i} style={S.opt(ans[cur] === i)} onClick={() => pickOpt(i)}>
              <span style={S.radio(ans[cur] === i)} />
              <span style={S.optText}>{o.text}</span>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ fontSize: '12px', color: '#ef4444', marginBottom: '8px', padding: '8px 12px', background: '#1a0a0a', borderRadius: '6px', border: '1px solid #7f1d1d' }}>
          {error}
        </div>
      )}

      {/* Nav */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
        <button style={S.btn(false, cur === 0)} onClick={() => cur > 0 && setCur(c => c - 1)} disabled={cur === 0}>
          ← Quay lại
        </button>
        <span style={{ fontSize: '12px', color: '#475569' }}>
          {ans[cur] === null ? 'Chọn đáp án để tiếp tục' : ''}
        </span>
        <button
          style={S.btn(true, ans[cur] === null || phase === 'submitting')}
          onClick={goNext}
          disabled={ans[cur] === null}
        >
          {cur === 14 ? 'Xem kết quả →' : 'Tiếp theo →'}
        </button>
      </div>
    </div>
  )

  // ── Result ───────────────────────────────────────────────────────────
  if (phase === 'result' && result) {
    const lvl   = LEVELS.find(l => l.name === result.level) || LEVELS[0]
    const lvlIdx = LEVELS.indexOf(lvl)
    const mInfo = METHOD_MAP[result.method] || METHOD_MAP.bat_song

    return (
      <div style={S.wrap}>
        {/* Score hero */}
        <div style={{ textAlign: 'center', padding: '16px', background: '#1e293b', borderRadius: '12px', border: '1px solid #334155', marginBottom: '14px' }}>
          <div style={{ fontSize: '52px', fontWeight: 600, color: '#f1f5f9', lineHeight: 1 }}>{result.total}</div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Investor Intelligence Score</div>
          <div style={{ fontSize: '15px', fontWeight: 500, color: lvl.color, marginTop: '8px' }}>
            Level {lvlIdx + 1}: {lvl.name}
          </div>
          <div style={{ fontSize: '12px', color: '#475569', marginTop: '2px' }}>{result.ai_role}</div>
        </div>

        {/* Score breakdown */}
        <div style={{ ...S.card, marginBottom: '12px' }}>
          <div style={{ padding: '14px 16px' }}>
            {[
              { label: 'IIS Kỷ Luật',   val: result.kl_score, color: '#ef4444' },
              { label: 'IIS Kiến Thức', val: result.kt_score, color: '#3b82f6' },
            ].map(({ label, val, color }) => (
              <div key={label} style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8', marginBottom: '5px' }}>
                  <span>{label}</span>
                  <span style={{ fontWeight: 500, color: '#e2e8f0' }}>{val}/100</span>
                </div>
                <div style={{ height: '6px', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={S.scoreBar(val, color)} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Method box */}
        <div style={{ ...S.card, border: `1px solid ${mInfo.color}33`, background: `${mInfo.color}0d`, marginBottom: '12px' }}>
          <div style={{ padding: '14px 16px' }}>
            <div style={{ fontSize: '14px', fontWeight: 500, color: mInfo.color, marginBottom: '3px' }}>
              Phương pháp phù hợp: {mInfo.name}
            </div>
            <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '12px' }}>
              {mInfo.horizon} · Hold {mInfo.hold}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              {[['Win Rate', mInfo.wr], ['Risk-Reward', mInfo.rr], ['Thời hạn', mInfo.horizon], ['Nắm giữ', mInfo.hold]].map(([k, v]) => (
                <div key={k} style={{ background: '#0f172a', borderRadius: '6px', padding: '8px 10px', border: '1px solid #1e293b' }}>
                  <div style={{ fontSize: '10px', color: '#475569', marginBottom: '2px', textTransform: 'uppercase', letterSpacing: '.04em' }}>{k}</div>
                  <div style={{ fontSize: '12px', fontWeight: 500, color: '#e2e8f0' }}>{v}</div>
                </div>
              ))}
            </div>
            {result.buckets && (
              <div style={{ marginTop: '10px', padding: '8px 10px', background: '#0f172a', borderRadius: '6px', border: '1px solid #1e293b', fontSize: '12px', color: '#94a3b8' }}>
                <span style={{ color: mInfo.color, fontWeight: 500 }}>Hybrid bucket: </span>
                {Object.entries(result.buckets).map(([k, v]) => `${METHOD_MAP[k]?.name || k} ${v}%`).join(' · ')}
              </div>
            )}
          </div>
        </div>

        {/* Tips */}
        {result.improve_tips?.length > 0 && (
          <div style={{ ...S.card, border: '1px solid #78350f44', background: '#1a0f0022', marginBottom: '12px' }}>
            <div style={{ padding: '12px 16px' }}>
              <div style={{ fontSize: '12px', fontWeight: 500, color: '#f59e0b', marginBottom: '8px' }}>
                💡 Ưu tiên cải thiện
              </div>
              {result.improve_tips.map((tip, i) => (
                <div key={i} style={{ fontSize: '12px', color: '#94a3b8', padding: '3px 0', lineHeight: 1.5 }}>
                  · {tip}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Level map */}
        <div style={{ ...S.card, marginBottom: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', padding: '12px 8px 8px' }}>
            {LEVELS.map((l, i) => (
              <div key={l.name} style={{
                textAlign: 'center', padding: '6px 2px',
                borderRadius: '6px',
                background: l === lvl ? `${l.color}18` : 'transparent',
                border: l === lvl ? `1px solid ${l.color}44` : '1px solid transparent',
              }}>
                <div style={{ fontSize: '15px', fontWeight: 500, color: l.color, lineHeight: 1 }}>{i + 1}</div>
                <div style={{ fontSize: '10px', color: l === lvl ? l.color : '#475569', marginTop: '3px', lineHeight: 1.3 }}>{l.name}</div>
                <div style={{ fontSize: '9px', color: '#334155' }}>{l.min}–{l.max}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Primary CTA — chỉ hiện khi có onComplete (modal mode) */}
        {onComplete && (
          <button
            style={{
              ...S.btn(true, false),
              width: '100%',
              marginBottom: '8px',
              padding: '12px',
              fontSize: '14px',
              background: '#22c55e',
              borderColor: '#22c55e',
            }}
            onClick={() => onComplete(result)}
          >
            Bắt đầu đầu tư với AI-Advisor →
          </button>
        )}

        <button
          style={{ ...S.btn(false, false), width: '100%', marginBottom: '8px', opacity: 0.6 }}
          onClick={restart}
        >
          Làm lại từ đầu
        </button>
      </div>
    )
  }

  return null
}
