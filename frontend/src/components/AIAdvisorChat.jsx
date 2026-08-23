import { useState, useEffect, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

// ── Quick prompts theo tab ────────────────────────────────────────
const QUICK_SIGNALS   = ['Thị trường hôm nay thế nào?', 'Cổ phiếu VN30 nào đang có tín hiệu tốt?', 'Market risk hiện tại là bao nhiêu?']
const QUICK_PORTFOLIO = ['Danh mục của tôi có ổn không?', 'Tôi nên tăng hay giảm tỷ trọng?', 'Cổ phiếu nào nên xem xét bán?']

// ── Rescue triage questions ───────────────────────────────────────
const RESCUE_QUESTIONS = [
  'Tại sao bạn mua cổ phiếu này? (1-2 câu ngắn gọn)',
  'Lý do đó có còn đúng ở thời điểm hiện tại không?',
  'Nếu bạn không có cổ phiếu này, bạn có mua nó ngay hôm nay không?',
]

// ─── Markdown → HTML converter (strip dấu * từ GPT response) ──
function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
    .replace(/_([^_\n]+?)_/g, '<em>$1</em>')
    .replace(/^[-•]\s+(.+)$/gm, '• $1')
    .replace(/\n/g, '<br/>')
  return html
}

export default function AIAdvisorChat({ userId, userTier = 'free', onOpenIIS, activeTab = 'signals' }) {
  const [messages, setMessages]         = useState([])
  const [input, setInput]               = useState('')
  const [chatLoading, setChatLoading]   = useState(false)
  const [expanded, setExpanded]         = useState(true)
  const [histLoaded, setHistLoaded]     = useState(false)
  const [marketBar, setMarketBar]       = useState(null)
  const chatEndRef   = useRef(null)
  const containerRef  = useRef(null)
  // ── Rescue flow state ──────────────────────────────────────────
  const [bnChips,       setBnChips]      = useState([])   // v2.2: chip theo điểm nghẽn
  const [rescueMode,    setRescueMode]   = useState(false)
  const [rescueStep,    setRescueStep]   = useState(0)
  const [rescueStocks,  setRescueStocks] = useState([{ ticker: '', lossP: '' }])
  const [rescueCurrent, setRescueCur]    = useState(0)

  // ── Lắng nghe "Phân tích AI" từ SignalsModule ──────────────
  useEffect(() => {
    const handler = (e) => {
      if (e.detail) {
        setExpanded(true)
        sendMessage(e.detail)
        // Scroll lên ô chat
        setTimeout(() => {
          const chatEl = document.getElementById('ai-advisor-chat')
          if (chatEl) chatEl.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 100)
      }
    }
    window.addEventListener('askAI', handler)
    return () => window.removeEventListener('askAI', handler)
  }, [])

  // Load chat history on mount
  useEffect(() => {
    if (!userId || histLoaded) return
    fetch(`${API_BASE}/chat/history?user_id=${encodeURIComponent(userId)}&limit=20`)
      .then(r => r.json())
      .then(d => {
        if (d.history?.length > 0) {
          setMessages(d.history.flatMap(h => ([
            { role: 'user', content: h.message,  meta: null, faded: true },
            { role: 'ai',   content: h.response, meta: null, faded: true },
          ])))
        }
        setHistLoaded(true)
      })
      .catch(() => setHistLoaded(true))
  }, [userId])

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages])

  // Fetch market bar data (light - không cần GPT)
  useEffect(() => {
    const fetchMarket = async () => {
      try {
        const r = await fetch(`${API_BASE.replace('/api','')}/api/market-risk`)
        const d = await r.json()
        if (d.success && d.data) {
          const m = d.data
          const modeLabel = {BULL:'🟢 Tích cực', SIDEWAYS:'🟡 Thận trọng', BEAR:'🔴 Phòng thủ'}[m.market_mode] || m.market_mode
          setMarketBar({
            mode:  modeLabel,
            risk:  m.risk_score,
            alloc: m.allocation,
          })
        }
      } catch {}
    }
    fetchMarket()
  }, [])


  // === v2.2: nạp chip gợi ý theo ĐIỂM NGHẼN của user ===
  // Chip thay thế menu — mỗi user thấy gợi ý khác nhau, tự đổi theo ngữ cảnh
  useEffect(() => {
    if (!userId) return
    let alive = true
    fetch(`${API_BASE}/chips/${encodeURIComponent(userId)}`)
      .then(r => r.json())
      .then(d => { if (alive && d.success) setBnChips((d.chips || []).slice(0, 2)) })
      .catch(() => {})
    return () => { alive = false }
  }, [userId])

  const sendMessage = async (msg) => {
    if (!msg.trim() || chatLoading) return
    const userMsg = { role: 'user', content: msg, meta: null, faded: false }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setChatLoading(true)
    try {
      let iisLocal = null
      try {
        const _c = localStorage.getItem(`iis_result_${userId}`)
        if (_c) { const _p = JSON.parse(_c); if (_p.has_result) iisLocal = { total: _p.total, level: _p.level, method: _p.method, kl: _p.kl_score, kt: _p.kt_score } }
      } catch {}
      const r = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, message: msg, user_tier: userTier, iis_profile_fallback: iisLocal }),
      })
      const d = await r.json()
      console.log('[AI-Advisor Chat] response meta:', d.meta)
      const aiMsg = { role: 'ai', content: d.response || d.message || '...', meta: d.meta || null, faded: false }
      setMessages(prev => [...prev, aiMsg])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ai', content: '⚠️ Lỗi kết nối. Vui lòng thử lại.', meta: null, faded: false }])
    }
    setChatLoading(false)
  }

  const QUICK = activeTab === 'portfolio' ? QUICK_PORTFOLIO : QUICK_SIGNALS

  // ── Start rescue flow ─────────────────────────────────────────
  const startRescue = () => {
    setRescueMode(true)
    setRescueStep(0)
    setRescueStocks([{ ticker: '', lossP: '' }])
    setRescueCur(0)
    setExpanded(true)
    setMessages(prev => [...prev, {
      role: 'ai',
      content: '🩺 **Khám sức khỏe danh mục kẹp**\n\nHãy nhập các cổ phiếu bạn đang bị kẹp lỗ. Tôi sẽ hỏi 3 câu về từng mã để đánh giá mức rủi ro và nêu các kịch bản bạn có thể cân nhắc.',
      meta: null, faded: false, isRescueQ: false,
    }])
  }

  // ── Submit stocks → start triage ──────────────────────────────
  const submitStocks = () => {
    const valid = rescueStocks.filter(s => s.ticker.trim())
    if (!valid.length) return
    setRescueStocks(valid)
    setRescueStep(1)
    setRescueCur(0)
    const names = valid.map(s => `${s.ticker.toUpperCase()}${s.lossP ? ` (-${s.lossP}%)` : ''}`).join(', ')
    setMessages(prev => [...prev,
      { role: 'user', content: `Danh mục kẹp: ${names}`, meta: null, faded: false },
      { role: 'ai',
        content: `Được rồi. Tôi sẽ hỏi 3 câu về từng mã.\n\n**Bắt đầu với ${valid[0].ticker.toUpperCase()}${valid[0].lossP ? ` (đang lỗ ${valid[0].lossP}%)` : ''}:**\n\n${RESCUE_QUESTIONS[0]}`,
        meta: null, faded: false, isRescueQ: true, qIdx: 0 }
    ])
  }

  // ── Handle rescue answer ──────────────────────────────────────
  const handleRescueAnswer = async (answer) => {
    if (!answer.trim()) return
    const stocks = rescueStocks.filter(s => s.ticker.trim())
    const stock  = stocks[rescueCurrent]
    const qIdx   = (rescueStep - 1) % 3

    setMessages(prev => [...prev, { role: 'user', content: answer, meta: null, faded: false }])
    setInput('')

    if (qIdx < 2) {
      setRescueStep(s => s + 1)
      setTimeout(() => setMessages(prev => [...prev, {
        role: 'ai', content: RESCUE_QUESTIONS[qIdx + 1],
        meta: null, faded: false, isRescueQ: true, qIdx: qIdx + 1,
      }]), 300)
    } else {
      // All 3 answered → get AI verdict
      setRescueStep(s => s + 1)
      setChatLoading(true)
      const prompt = `Portfolio Rescue — Phân tích vị thế kẹp:\nCổ phiếu: ${stock.ticker.toUpperCase()}${stock.lossP ? ` | Lỗ: -${stock.lossP}%` : ''}\n\nUser trả lời 3 câu:\n1. Tại sao mua: (câu trả lời trước đó)\n2. Thesis còn đúng không: (câu trả lời trước đó)\n3. Có mua lại ngay hôm nay không: "${answer}"\n\nĐưa ra: 1) ĐÁNH GIÁ RỦI RO của vị thế 2) Lý do 2-3 câu dựa trên dữ liệu 3) Các kịch bản user có thể cân nhắc, kèm hệ quả từng kịch bản. KHÔNG đưa khuyến nghị mua/bán — chỉ đối chiếu với ngưỡng rủi ro user đã đặt.`
      try {
        const r = await fetch(`${API_BASE}/chat`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, message: prompt, user_tier: userTier }),
        })
        const d = await r.json()
        setMessages(prev => [...prev, { role: 'ai', content: d.response || '...', meta: null, faded: false }])
      } catch {
        setMessages(prev => [...prev, { role: 'ai', content: 'Không thể phân tích lúc này.', meta: null, faded: false }])
      }
      setChatLoading(false)

      if (rescueCurrent < stocks.length - 1) {
        const next = stocks[rescueCurrent + 1]
        setRescueCur(c => c + 1)
        setRescueStep(1)
        setTimeout(() => setMessages(prev => [...prev, {
          role: 'ai',
          content: `**Tiếp theo: ${next.ticker.toUpperCase()}${next.lossP ? ` (lỗ ${next.lossP}%)` : ''}**\n\n${RESCUE_QUESTIONS[0]}`,
          meta: null, faded: false, isRescueQ: true, qIdx: 0,
        }]), 500)
      } else {
        setRescueMode(false)
        setTimeout(() => setMessages(prev => [...prev, {
          role: 'ai',
          content: '✅ **Khám xong toàn bộ danh mục.**\n\nBạn đã có đánh giá rủi ro cho từng mã. Quyết định thuộc về bạn. Bạn muốn tôi giúp thêm điều gì?',
          meta: null, faded: false,
        }]), 600)
      }
    }
  }

  const tierBadge = userTier === 'vip'
    ? { label: '💎 VIP', bg: '#7c3aed' }
    : userTier === 'basic'
    ? { label: '✅ Basic', bg: '#059669' }
    : { label: 'FREE', bg: '#334155' }

  return (
    <>
    {/* ── Market Greeting Bar ── */}
    {marketBar && (
      <div
        onClick={() => sendMessage('Tóm tắt tình hình thị trường hôm nay cho tôi')}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '8px 14px', marginBottom: '8px',
          background: 'linear-gradient(90deg, #0f172a, #1e293b)',
          border: '1px solid #1e3a5f', borderRadius: '10px',
          cursor: 'pointer', userSelect: 'none',
          fontSize: '12px', gap: '8px',
        }}
      >
        <span style={{ color: '#94a3b8' }}>
          📺 <strong style={{ color: '#e2e8f0' }}>{marketBar.mode}</strong>
          {' '}· Risk {marketBar.risk}/100 · CP {marketBar.alloc}%
        </span>
        <span style={{
          color: '#3b82f6', fontWeight: 600, fontSize: '11px',
          whiteSpace: 'nowrap',
        }}>
          Hỏi AI về thị trường →
        </span>
      </div>
    )}
    <div id="ai-advisor-chat" style={{
      background: 'linear-gradient(160deg, #0f172a 0%, #1e293b 100%)',
      border: '1px solid #1e3a5f',
      borderRadius: '16px',
      overflow: 'hidden',
      marginBottom: '20px',
      fontFamily: "\'DM Sans\', sans-serif",
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 20px',
        borderBottom: expanded ? '1px solid #1e293b' : 'none',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        cursor: 'pointer',
      }} onClick={() => setExpanded(e => !e)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '18px' }}>💬</span>
          <span style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '14px' }}>
            AI Advisor — Tư vấn riêng
          </span>
          <span style={{
            background: tierBadge.bg, color: '#fff',
            fontSize: '11px', padding: '2px 8px', borderRadius: '20px', fontWeight: 600,
          }}>{tierBadge.label}</span>
        </div>
        <span style={{ fontSize: '12px', color: '#64748b' }}>{expanded ? '▲ Thu gọn' : '▼ Mở rộng'}</span>
      </div>

      {expanded && (
        <>
          {/* Messages */}
          <div style={{
            height: '380px', overflowY: 'auto', padding: '16px 20px',
            display: 'flex', flexDirection: 'column', gap: '12px',
            scrollbarWidth: 'thin', scrollbarColor: '#1e3a5f transparent',
          }} ref={containerRef}>
            {messages.length === 0 && !chatLoading && (
              <div style={{ textAlign: 'center', color: '#475569', fontSize: '13px', marginTop: '60px' }}>
                <div style={{ fontSize: '32px', marginBottom: '12px' }}>🤖</div>
                <div>Hỏi tôi về cổ phiếu, thị trường, hoặc danh mục của bạn</div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                {m.role === 'ai' && (
                  <div style={{
                    width: 28, height: 28, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '13px', flexShrink: 0, marginRight: '8px', marginTop: '2px',
                  }}>{m.isRescueQ ? '🩺' : '🤖'}</div>
                )}
                <div style={{ maxWidth: '78%' }}>
                  {/* FOMO badge */}
                  {m.role === 'ai' && m.meta?.emotional_state && m.meta.emotional_state !== 'neutral' && (
                    <div style={{ marginBottom: '6px' }}>
                      <div style={{
                        display: 'inline-flex', alignItems: 'center', gap: '5px',
                        padding: '3px 9px', borderRadius: '12px', fontSize: '11px', fontWeight: 500,
                        background: m.meta.emotional_state === 'panic'    ? 'rgba(245,158,11,0.25)' :
                          m.meta.emotional_state === 'avg_down' ? 'rgba(249,115,22,0.25)' :
                          'rgba(239,68,68,0.25)',
                        color: m.meta.emotional_state === 'panic'    ? '#fcd34d' :
                               m.meta.emotional_state === 'avg_down' ? '#fb923c' :
                               '#fca5a5',
                      }}>
                        ⚠️ {
          m.meta.emotional_state === 'panic'    ? 'Hoảng loạn detected' :
          m.meta.emotional_state === 'avg_down' ? 'Bình quân giá xuống detected' :
          'FOMO detected'
        }
                      </div>
                    </div>
                  )}
                  {/* Upgrade CTA */}
                  {m.role === 'ai' && m.meta?.tier_locked && (
                    <div style={{
                      marginBottom: '8px', padding: '8px 12px', borderRadius: '10px',
                      background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)',
                      fontSize: '12px', color: '#a5b4fc',
                    }}>
                      🔒 Bạn được sử dụng miễn phí 30 ngày, hãy nâng cấp gói{' '}
                      <strong style={{ color: '#818cf8' }}>Basic</strong> hoặc{' '}
                      <strong style={{ color: '#a855f7' }}>VIP</strong>{' '}
                      để được AI hỗ trợ kiểm soát cảm xúc và nâng tầm hiệu quả đầu tư.
                    </div>
                  )}
                  {/* Message bubble */}
                  {m.role === 'ai' ? (
                    <div style={{
                      padding: '10px 14px',
                      borderRadius: '4px 16px 16px 16px',
                      opacity: m.faded ? 0.5 : 1,
                      background: m.isRescueQ ? 'rgba(220,38,38,0.08)' : 'rgba(255,255,255,0.06)',
                      border: m.isRescueQ ? '1px solid rgba(220,38,38,0.25)' : 'none',
                      fontSize: '13px', lineHeight: '1.6', color: '#e2e8f0',
                      wordBreak: 'break-word',
                    }} dangerouslySetInnerHTML={{ __html: renderMarkdown(m.content) }} />
                  ) : (
                    <div style={{
                      padding: '10px 14px',
                      borderRadius: '16px 4px 16px 16px',
                      opacity: m.faded ? 0.5 : 1,
                      background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
                      fontSize: '13px', lineHeight: '1.6', color: '#e2e8f0',
                      whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                    }}>
                      {m.content}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '13px',
                }}>🤖</div>
                <div style={{ padding: '10px 14px', borderRadius: '4px 16px 16px 16px', background: 'rgba(255,255,255,0.06)', fontSize: '13px', color: '#64748b' }}>
                  Đang phân tích...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* === v2.2: Chip theo điểm nghẽn — TỐI ĐA 2, quy tắc cứng === */}
          {bnChips.length > 0 && (
            <div style={{ padding: '0 20px 10px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {bnChips.map((c, i) => (
                <button key={`bn-${i}`} onClick={() => sendMessage(c)} style={{
                  padding: '6px 12px', borderRadius: '20px',
                  border: '1px solid rgba(245,158,11,0.35)',
                  background: 'rgba(245,158,11,0.10)', color: '#fcd34d',
                  fontSize: '12px', cursor: 'pointer', fontWeight: 500,
                }}>{c}</button>
              ))}
            </div>
          )}

          {/* Quick prompts */}
          {messages.length === 0 && (
            <div style={{ padding: '0 20px 12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {QUICK.map((q, i) => (
                <button key={i} onClick={() => sendMessage(q)} style={{
                  padding: '6px 12px', borderRadius: '20px', border: '1px solid #1e3a5f',
                  background: 'rgba(255,255,255,0.04)', color: '#94a3b8',
                  fontSize: '12px', cursor: 'pointer',
                }}>{q}</button>
              ))}
            </div>
          )}

          {/* Rescue: nhập danh sách cổ phiếu */}
          {rescueMode && rescueStep === 0 && (
            <div style={{ padding: '12px 20px', borderTop: '1px solid #1e293b', background: 'rgba(220,38,38,0.04)' }}>
              <div style={{ fontSize: '13px', color: '#fca5a5', marginBottom: '10px', fontWeight: 600 }}>
                🩺 Nhập cổ phiếu đang kẹp lỗ:
              </div>
              {rescueStocks.map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                  <input placeholder="Mã CP (VD: VHM)"
                    value={s.ticker}
                    onChange={e => setRescueStocks(prev => prev.map((r,j) => j===i ? {...r, ticker: e.target.value.toUpperCase()} : r))}
                    style={{ flex: 2, background: 'rgba(255,255,255,0.05)', border: '1px solid #1e3a5f', borderRadius: '8px', padding: '8px 12px', color: '#e2e8f0', fontSize: '13px', outline: 'none' }} />
                  <input placeholder="% lỗ (VD: 35)"
                    value={s.lossP}
                    onChange={e => setRescueStocks(prev => prev.map((r,j) => j===i ? {...r, lossP: e.target.value} : r))}
                    style={{ flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid #1e3a5f', borderRadius: '8px', padding: '8px 12px', color: '#e2e8f0', fontSize: '13px', outline: 'none' }} />
                  {rescueStocks.length > 1 && (
                    <button onClick={() => setRescueStocks(prev => prev.filter((_,j) => j!==i))}
                      style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '18px' }}>×</button>
                  )}
                </div>
              ))}
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                <button onClick={() => setRescueStocks(p => [...p, { ticker: '', lossP: '' }])}
                  style={{ padding: '6px 12px', borderRadius: '8px', border: '1px solid #1e3a5f', background: 'transparent', color: '#64748b', fontSize: '12px', cursor: 'pointer' }}>
                  + Thêm mã
                </button>
                <button onClick={submitStocks} disabled={!rescueStocks.some(s => s.ticker.trim())}
                  style={{ padding: '6px 16px', borderRadius: '8px', border: 'none', background: '#dc2626', color: '#fff', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
                  Bắt đầu khám →
                </button>
                <button onClick={() => { setRescueMode(false); setRescueStep(0) }}
                  style={{ padding: '6px 12px', borderRadius: '8px', border: '1px solid #1e3a5f', background: 'transparent', color: '#64748b', fontSize: '12px', cursor: 'pointer' }}>
                  Hủy
                </button>
              </div>
            </div>
          )}

          {/* Khám sức khỏe button — chỉ hiện trong portfolio tab */}
          {activeTab === 'portfolio' && !rescueMode && (
            <div style={{ padding: '0 20px 12px' }}>
              <button onClick={startRescue} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                padding: '8px 16px', borderRadius: '10px', width: '100%',
                border: '1px solid rgba(220,38,38,0.4)', background: 'rgba(220,38,38,0.08)',
                color: '#fca5a5', fontSize: '13px', fontWeight: 600, cursor: 'pointer',
              }}>
                🩺 Khám sức khỏe danh mục kẹp
                <span style={{ fontSize: '11px', fontWeight: 400, color: '#ef4444' }}>
                  — AI đánh giá mức rủi ro từng vị thế, nêu các kịch bản
                </span>
              </button>
            </div>
          )}

          {/* Input */}
          <form onSubmit={e => {
              e.preventDefault()
              if (rescueMode && rescueStep > 0) { handleRescueAnswer(input) }
              else { sendMessage(input) }
            }}
            style={{ padding: '12px 20px', borderTop: '1px solid #1e293b', display: 'flex', gap: '10px' }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder={rescueMode && rescueStep > 0 ? "Nhập câu trả lời của bạn..." : "Hỏi về cổ phiếu, xu hướng thị trường..."}
              style={{
                flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid #1e3a5f',
                borderRadius: '10px', padding: '10px 14px', color: '#e2e8f0', fontSize: '13px', outline: 'none',
              }}
            />
            <button type="submit" disabled={chatLoading || !input.trim()} style={{
              padding: '10px 18px', borderRadius: '10px', border: 'none',
              background: chatLoading || !input.trim() ? '#1e3a5f' : 'linear-gradient(135deg, #2563eb, #7c3aed)',
              color: '#fff', fontSize: '13px', fontWeight: 600, cursor: chatLoading ? 'not-allowed' : 'pointer',
            }}>Gửi ▶</button>
          </form>
        </>
      )}
    </div>
    </>
  )
}
