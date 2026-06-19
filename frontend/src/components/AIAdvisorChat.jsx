import { useState, useEffect, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

export default function AIAdvisorChat({ userId, userTier = 'free', onOpenIIS }) {
  const [messages, setMessages]         = useState([])
  const [input, setInput]               = useState('')
  const [chatLoading, setChatLoading]   = useState(false)
  const [expanded, setExpanded]         = useState(true)
  const [histLoaded, setHistLoaded]     = useState(false)
  const chatEndRef = useRef(null)

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
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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

  const QUICK = ['Thị trường hôm nay thế nào?', 'Cổ phiếu nào nên xem xét?', 'Danh mục của tôi có ổn không?']

  const tierBadge = userTier === 'vip'
    ? { label: '💎 VIP', bg: '#7c3aed' }
    : userTier === 'basic'
    ? { label: '✅ Basic', bg: '#059669' }
    : { label: 'FREE', bg: '#334155' }

  return (
    <div style={{
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
          }}>
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
                  }}>🤖</div>
                )}
                <div style={{ maxWidth: '78%' }}>
                  {/* FOMO badge */}
                  {m.role === 'ai' && m.meta?.emotional_state && m.meta.emotional_state !== 'neutral' && (
                    <div style={{ marginBottom: '6px' }}>
                      <div style={{
                        display: 'inline-flex', alignItems: 'center', gap: '5px',
                        padding: '3px 9px', borderRadius: '12px', fontSize: '11px', fontWeight: 500,
                        background: m.meta.emotional_state === 'panic' ? 'rgba(245,158,11,0.25)' : 'rgba(239,68,68,0.25)',
                        color: m.meta.emotional_state === 'panic' ? '#fcd34d' : '#fca5a5',
                      }}>
                        ⚠️ {m.meta.emotional_state === 'panic' ? 'Panic detected' : 'FOMO detected'}
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
                  <div style={{
                    padding: '10px 14px',
                    borderRadius: m.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                    opacity: m.faded ? 0.5 : 1,
                    background: m.role === 'user'
                      ? 'linear-gradient(135deg, #2563eb, #1d4ed8)'
                      : 'rgba(255,255,255,0.06)',
                    fontSize: '13px', lineHeight: '1.6', color: '#e2e8f0',
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  }}>
                    {m.content}
                  </div>
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

          {/* Input */}
          <form onSubmit={e => { e.preventDefault(); sendMessage(input) }}
            style={{ padding: '12px 20px', borderTop: '1px solid #1e293b', display: 'flex', gap: '10px' }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Hỏi về cổ phiếu, xu hướng thị trường..."
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
  )
}
