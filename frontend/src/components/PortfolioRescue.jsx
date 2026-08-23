import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:10000/api'

// ── Helpers ───────────────────────────────────────────────────────
const fmt  = n => n?.toLocaleString('vi-VN') || '0'
const pct  = n => (n >= 0 ? '+' : '') + n.toFixed(1) + '%'
const loss_to_breakeven = lossP => {
  // e.g. -40% loss → need +66.7% to breakeven
  return ((1 / (1 + lossP/100)) - 1) * 100
}
const C = {
  navy:'#0d2b5e', blue:'#1a5fb4', red:'#dc2626', orange:'#ea580c',
  green:'#059669', gold:'#d97706', purple:'#7c3aed',
  bg:'#0f172a', card:'#1e293b', border:'#1e3a5f',
  text:'#e2e8f0', muted:'#64748b', light:'#f1f5f9',
}

// ── Triage questions ──────────────────────────────────────────────
const TRIAGE_QUESTIONS = [
  { id:'why',    q:'Tại sao bạn mua cổ phiếu này? (Nói ngắn gọn 1-2 câu)', placeholder:'VD: Nghe tip từ group, thấy chart đẹp, công ty tốt...' },
  { id:'thesis', q:'Lý do đó có còn đúng ở thời điểm hiện tại không?',      placeholder:'VD: Câu chuyện đã thay đổi / Vẫn đúng nhưng cần thời gian...' },
  { id:'rebuy',  q:'Nếu bạn không có cổ phiếu này, bạn có bỏ tiền mua nó ngay hôm nay không?', placeholder:'VD: Không vì... / Có vì...' },
]

// ── Phase indicators ──────────────────────────────────────────────
const PHASES = ['Nhập danh mục','Rà soát','Đánh giá rủi ro','Kịch bản','Cam kết']

// ── Main component ────────────────────────────────────────────────
export default function PortfolioRescue({ userId, userTier = 'free' }) {
  const [phase,    setPhase]   = useState(0) // 0-4
  const [positions,setPos]     = useState([{ ticker:'', qty:'', avgPrice:'', curPrice:'' }])
  const [triageIdx,setTriIdx]  = useState(0)  // which position being triaged
  const [answers,  setAnswers] = useState({}) // {ticker: {why, thesis, rebuy}}
  const [verdicts, setVerd]    = useState({}) // {ticker: {verdict, plan, message}}
  const [loading,  setLoading] = useState(false)
  const [commits,  setCommits] = useState({}) // {ticker: 'full'|'partial'|'hold'}
  const [done,     setDone]    = useState(false)

  // ── Computed per position ────────────────────────────────────────
  const enriched = positions.filter(p => p.ticker && p.avgPrice && p.curPrice).map(p => {
    const avg = parseFloat(p.avgPrice.replace(/,/g,''))
    const cur = parseFloat(p.curPrice.replace(/,/g,''))
    const qty = parseInt(p.qty) || 0
    const lossP  = ((cur - avg) / avg) * 100
    const lossAmt = (cur - avg) * qty
    const beP    = loss_to_breakeven(lossP)
    const totalVal = cur * qty
    return { ...p, avg, cur, qty, lossP, lossAmt, beP, totalVal }
  })

  const totalLoss    = enriched.reduce((s,p) => s + p.lossAmt, 0)
  const totalValue   = enriched.reduce((s,p) => s + p.totalVal, 0)
  const worstMother  = enriched.sort((a,b) => a.lossP - b.lossP)[0]

  // ── Add / remove position rows ───────────────────────────────────
  const addRow    = () => setPos(p => [...p, { ticker:'', qty:'', avgPrice:'', curPrice:'' }])
  const removeRow = i  => setPos(p => p.filter((_,j) => j !== i))
  const updateRow = (i, field, val) => setPos(p => p.map((r,j) => j===i ? {...r,[field]:val} : r))

  // ── Call AI for verdict ──────────────────────────────────────────
  const fetchVerdicts = async () => {
    setLoading(true)
    const results = {}
    for (const pos of enriched) {
      const ans = answers[pos.ticker] || {}
      const prompt = `
Portfolio Rescue — Phân tích vị thế kẹp:
Cổ phiếu: ${pos.ticker}
Lỗ: ${pos.lossP.toFixed(1)}% | Số tiền lỗ: ${fmt(Math.abs(pos.lossAmt))} VNĐ
Cần tăng ${pos.beP.toFixed(1)}% để hòa vốn

User trả lời 3 câu hỏi:
1. Tại sao mua: "${ans.why || 'Không trả lời'}"
2. Thesis còn đúng không: "${ans.thesis || 'Không trả lời'}"
3. Có mua lại ngay hôm nay không: "${ans.rebuy || 'Không trả lời'}"

Hãy phân tích và đưa ra:
1. VERDICT — mức rủi ro của vị thế: "RỦI RO CAO" | "CẦN RÀ SOÁT" | "TRONG NGƯỠNG"
2. LÝ DO (2-3 câu dựa trên dữ liệu: mức lỗ, % cần để hòa vốn, luận điểm ban đầu còn đúng không)
3. KỊCH BẢN (1-2 câu nêu các lựa chọn user có thể cân nhắc kèm hệ quả, KHÔNG chọn hộ)
4. LỜI NHẮN (câu ngắn, không phán xét)

QUAN TRỌNG: KHÔNG đưa ra khuyến nghị mua/bán. Chỉ đối chiếu với ngưỡng rủi ro
và luận điểm mà chính user đã nêu. Quyết định thuộc về user.

Format JSON: {"verdict":"...","reason":"...","plan":"...","message":"..."}`

      try {
        const r = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, message: prompt, user_tier: userTier, mode: 'rescue' }),
        })
        const d = await r.json()
        const text = d.response || ''
        const jsonMatch = text.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          results[pos.ticker] = JSON.parse(jsonMatch[0])
        } else {
          results[pos.ticker] = { verdict:'CẦN RÀ SOÁT', reason: text.slice(0,200), plan:'Đối chiếu vị thế này với ngưỡng rủi ro bạn đã đặt.', message:'Quyết định thuộc về bạn.' }
        }
      } catch {
        results[pos.ticker] = { verdict:'CẦN RÀ SOÁT', reason:'Không thể phân tích tự động.', plan:'Hãy trao đổi với advisor của bạn.', message:'Mọi hành trình bắt đầu từ một bước nhỏ.' }
      }
    }
    setVerd(results)
    setLoading(false)
    setPhase(3)
  }

  // ── Styles ───────────────────────────────────────────────────────
  const S = {
    wrap:  { background: C.bg, minHeight:'100vh', fontFamily:"'DM Sans',sans-serif", color: C.text, padding:'0' },
    inner: { maxWidth: 860, margin:'0 auto', padding:'24px 16px' },
    card:  { background: C.card, border:`1px solid ${C.border}`, borderRadius:12, padding:'20px', marginBottom:16 },
    input: { background:'rgba(255,255,255,0.05)', border:`1px solid ${C.border}`, borderRadius:8, padding:'10px 12px', color: C.text, fontSize:14, width:'100%', outline:'none', boxSizing:'border-box' },
    btn:   (col='#1a5fb4',dis=false) => ({ padding:'10px 20px', borderRadius:8, border:'none', background: dis?'#1e293b':col, color: dis?C.muted:'#fff', fontSize:14, fontWeight:600, cursor: dis?'not-allowed':'pointer', opacity: dis?0.6:1 }),
    phase: (active,done) => ({ flex:1, textAlign:'center', padding:'8px 4px', borderBottom:`3px solid ${done?C.green:active?C.blue:C.border}`, color: done?C.green:active?C.text:C.muted, fontSize:12, fontWeight: active?700:400 }),
    verdict_color: v => v==='RỦI RO CAO'?C.red: v==='CẦN RÀ SOÁT'?C.orange: C.green,
  }

  // ── PHASE 0: Input positions ─────────────────────────────────────
  const Phase0 = () => (
    <div>
      <div style={{ textAlign:'center', marginBottom:24 }}>
        <div style={{ fontSize:36, marginBottom:8 }}>🚑</div>
        <div style={{ fontSize:22, fontWeight:700, color:C.text, marginBottom:8 }}>Giải Phóng Danh Mục Kẹp</div>
        <div style={{ fontSize:14, color:C.muted, maxWidth:520, margin:'0 auto' }}>
          Nhập các cổ phiếu bạn đang kẹp lỗ. AI sẽ đánh giá mức rủi ro từng mã và nêu các kịch bản để bạn cân nhắc.
        </div>
      </div>

      <div style={S.card}>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 80px 130px 130px 40px', gap:8, marginBottom:8 }}>
          {['Mã CP','Số lượng','Giá mua (VNĐ)','Giá hiện tại',''].map((h,i) => (
            <div key={i} style={{ fontSize:12, color:C.muted, fontWeight:600 }}>{h}</div>
          ))}
        </div>
        {positions.map((p,i) => {
          const avg = parseFloat(p.avgPrice.replace(/,/g,'')) || 0
          const cur = parseFloat(p.curPrice.replace(/,/g,'')) || 0
          const lP  = avg > 0 ? ((cur-avg)/avg*100) : 0
          return (
            <div key={i} style={{ display:'grid', gridTemplateColumns:'1fr 80px 130px 130px 40px', gap:8, marginBottom:8, alignItems:'center' }}>
              <input style={{...S.input, textTransform:'uppercase', fontWeight:700}} value={p.ticker}
                placeholder="VHM" onChange={e => updateRow(i,'ticker',e.target.value.toUpperCase())} />
              <input style={S.input} value={p.qty} placeholder="1000" onChange={e => updateRow(i,'qty',e.target.value)} />
              <input style={S.input} value={p.avgPrice} placeholder="50,000" onChange={e => updateRow(i,'avgPrice',e.target.value)} />
              <div style={{ position:'relative' }}>
                <input style={{...S.input, paddingRight: avg>0?36:12}} value={p.curPrice}
                  placeholder="30,000" onChange={e => updateRow(i,'curPrice',e.target.value)} />
                {avg > 0 && cur > 0 && (
                  <span style={{ position:'absolute', right:8, top:'50%', transform:'translateY(-50%)', fontSize:11, fontWeight:700, color: lP<0?C.red:C.green }}>
                    {pct(lP)}
                  </span>
                )}
              </div>
              <button onClick={() => removeRow(i)} style={{ background:'none', border:'none', color:C.muted, cursor:'pointer', fontSize:18 }}>×</button>
            </div>
          )
        })}
        <button onClick={addRow} style={{ ...S.btn('#1e3a5f'), marginTop:8, fontSize:13 }}>+ Thêm cổ phiếu</button>
      </div>

      {enriched.length > 0 && (
        <div style={{ ...S.card, background:'rgba(220,38,38,0.08)', border:`1px solid rgba(220,38,38,0.3)` }}>
          <div style={{ fontSize:13, color:C.muted, marginBottom:12 }}>Tổng thiệt hại danh mục</div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:16 }}>
            <div>
              <div style={{ fontSize:28, fontWeight:800, color:C.red }}>{fmt(Math.abs(totalLoss))}</div>
              <div style={{ fontSize:12, color:C.muted }}>VNĐ đang kẹp</div>
            </div>
            <div>
              <div style={{ fontSize:28, fontWeight:800, color:C.orange }}>{enriched.length}</div>
              <div style={{ fontSize:12, color:C.muted }}>mã cần xem xét</div>
            </div>
            {worstMother && (
              <div>
                <div style={{ fontSize:28, fontWeight:800, color:C.red }}>{worstMother.beP.toFixed(0)}%</div>
                <div style={{ fontSize:12, color:C.muted }}>cần tăng để hòa vốn {worstMother.ticker}</div>
              </div>
            )}
          </div>
        </div>
      )}

      <div style={{ textAlign:'right' }}>
        <button style={S.btn(C.blue, enriched.length===0)}
          disabled={enriched.length===0} onClick={() => setPhase(1)}>
          Bắt đầu thẩm vấn →
        </button>
      </div>
    </div>
  )

  // ── PHASE 1: Triage interview ────────────────────────────────────
  const Phase1 = () => {
    const pos = enriched[triageIdx]
    if (!pos) return null
    const ans = answers[pos.ticker] || {}
    const [local, setLocal] = useState({ why: ans.why||'', thesis: ans.thesis||'', rebuy: ans.rebuy||'' })
    const done = local.why.length > 5 && local.thesis.length > 5 && local.rebuy.length > 5

    const save = () => {
      const newAns = { ...answers, [pos.ticker]: local }
      setAnswers(newAns)
      if (triageIdx < enriched.length - 1) {
        setTriIdx(i => i + 1)
        setLocal({ why:'', thesis:'', rebuy:'' })
      } else {
        fetchVerdicts()
        setPhase(2)
      }
    }

    return (
      <div>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:20 }}>
          <div>
            <div style={{ fontSize:13, color:C.muted }}>Thẩm vấn {triageIdx+1}/{enriched.length}</div>
            <div style={{ fontSize:24, fontWeight:800, color:C.text }}>{pos.ticker}</div>
          </div>
          <div style={{ textAlign:'right' }}>
            <div style={{ fontSize:28, fontWeight:800, color:C.red }}>{pct(pos.lossP)}</div>
            <div style={{ fontSize:12, color:C.muted }}>lỗ · {fmt(Math.abs(pos.lossAmt))} VNĐ</div>
          </div>
        </div>

        {/* Asymmetry callout */}
        <div style={{ ...S.card, background:'rgba(220,38,38,0.08)', border:`1px solid rgba(220,38,38,0.25)`, marginBottom:20 }}>
          <div style={{ fontSize:13, color:C.muted, marginBottom:8 }}>📊 Toán học của vị thế này</div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
            <div>
              <span style={{ fontSize:20, fontWeight:700, color:C.red }}>{pct(pos.lossP)}</span>
              <span style={{ fontSize:12, color:C.muted, marginLeft:8 }}>đã mất</span>
            </div>
            <div>
              <span style={{ fontSize:20, fontWeight:700, color:C.orange }}>+{pos.beP.toFixed(1)}%</span>
              <span style={{ fontSize:12, color:C.muted, marginLeft:8 }}>cần để hòa vốn</span>
            </div>
          </div>
          <div style={{ fontSize:12, color:C.muted, marginTop:8, fontStyle:'italic' }}>
            Lỗ 40% → cần tăng 67% để hòa. Cổ phiếu VN30 tốt tăng trung bình 15-20%/năm.
          </div>
        </div>

        <div style={{ fontSize:14, color:'#94a3b8', marginBottom:16, fontStyle:'italic' }}>
          🤖 Hãy trả lời trung thực — không có câu trả lời đúng sai. AI cần sự thật để giúp bạn.
        </div>

        {TRIAGE_QUESTIONS.map((q,i) => (
          <div key={q.id} style={{ ...S.card, marginBottom:12 }}>
            <div style={{ fontSize:14, fontWeight:600, color:C.text, marginBottom:10 }}>
              {i+1}. {q.q}
            </div>
            <textarea
              rows={3} placeholder={q.placeholder}
              value={local[q.id]}
              onChange={e => setLocal(l => ({...l,[q.id]:e.target.value}))}
              style={{ ...S.input, resize:'vertical', lineHeight:1.6 }}
            />
          </div>
        ))}

        <div style={{ display:'flex', justifyContent:'space-between' }}>
          <button style={S.btn('#334155')} onClick={() => triageIdx > 0 ? setTriIdx(i=>i-1) : setPhase(0)}>
            ← Quay lại
          </button>
          <button style={S.btn(C.blue, !done)} disabled={!done} onClick={save}>
            {triageIdx < enriched.length-1 ? `Tiếp theo: ${enriched[triageIdx+1]?.ticker} →` : 'Phân tích AI →'}
          </button>
        </div>
      </div>
    )
  }

  // ── PHASE 2: Loading ────────────────────────────────────────────
  const Phase2 = () => (
    <div style={{ textAlign:'center', padding:'80px 20px' }}>
      <div style={{ fontSize:48, marginBottom:16, animation:'pulse 1.5s infinite' }}>🔍</div>
      <div style={{ fontSize:18, fontWeight:700, color:C.text, marginBottom:8 }}>AI đang phân tích từng vị thế...</div>
      <div style={{ fontSize:14, color:C.muted }}>Đang đánh giá luận điểm, tính toán chi phí cơ hội và dựng các kịch bản</div>
    </div>
  )

  // ── PHASE 3: Verdicts ───────────────────────────────────────────
  const Phase3 = () => (
    <div>
      <div style={{ textAlign:'center', marginBottom:24 }}>
        <div style={{ fontSize:24, fontWeight:800, color:C.text }}>Đánh giá rủi ro</div>
        <div style={{ fontSize:14, color:C.muted }}>Dựa trên câu trả lời của bạn và dữ liệu thị trường</div>
      </div>

      {enriched.map(pos => {
        const v = verdicts[pos.ticker] || {}
        const vc = S.verdict_color(v.verdict)
        return (
          <div key={pos.ticker} style={{ ...S.card, borderLeft:`4px solid ${vc}`, marginBottom:16 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:12 }}>
              <div>
                <div style={{ fontSize:20, fontWeight:800 }}>{pos.ticker}</div>
                <div style={{ fontSize:13, color:C.muted }}>{pct(pos.lossP)} · {fmt(Math.abs(pos.lossAmt))} VNĐ</div>
              </div>
              <div style={{ background:`${vc}22`, border:`1px solid ${vc}`, borderRadius:8, padding:'4px 12px', fontSize:13, fontWeight:700, color:vc }}>
                {v.verdict || 'Đang phân tích...'}
              </div>
            </div>

            {v.reason && (
              <div style={{ fontSize:14, color:'#94a3b8', marginBottom:10, lineHeight:1.7 }}>
                📋 {v.reason}
              </div>
            )}
            {v.plan && (
              <div style={{ background:'rgba(255,255,255,0.04)', borderRadius:8, padding:'10px 14px', marginBottom:10, fontSize:14, color:C.text }}>
                🎯 <strong>Kế hoạch:</strong> {v.plan}
              </div>
            )}
            {v.message && (
              <div style={{ fontSize:13, color:'#fbbf24', fontStyle:'italic' }}>
                💬 "{v.message}"
              </div>
            )}

            {/* Opportunity cost */}
            <div style={{ marginTop:12, padding:'10px 14px', background:'rgba(26,95,180,0.1)', borderRadius:8, fontSize:13, color:'#93c5fd' }}>
              💡 <strong>Chi phí cơ hội:</strong> {fmt(Math.abs(pos.lossAmt))} VNĐ đang kẹp ở {pos.ticker} ({pct(pos.lossP)}) —
              nếu freed và đầu tư vào VN30 signal tốt nhất hiện tại với RR 1:3, tiềm năng +{(Math.abs(pos.lossP)*0.5).toFixed(0)}% trong 2-3 tháng.
            </div>
          </div>
        )
      })}

      <div style={{ display:'flex', justifyContent:'flex-end' }}>
        <button style={S.btn(C.blue)} onClick={() => setPhase(4)}>
          Xây kế hoạch cam kết →
        </button>
      </div>
    </div>
  )

  // ── PHASE 4: Commit plan ────────────────────────────────────────
  const Phase4 = () => {
    const allCommitted = enriched.every(p => commits[p.ticker])

    const commitAndFinish = async () => {
      // Save to backend
      try {
        await fetch(`${API_BASE}/portfolio-rescue/commit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, positions: enriched.map(p => ({
            ticker: p.ticker, loss_pct: p.lossP, loss_amt: p.lossAmt,
            verdict: verdicts[p.ticker]?.verdict, commit: commits[p.ticker],
          }))})
        })
      } catch {}
      setDone(true)
    }

    if (done) return (
      <div style={{ textAlign:'center', padding:'60px 20px' }}>
        <div style={{ fontSize:48, marginBottom:16 }}>🎯</div>
        <div style={{ fontSize:24, fontWeight:800, color:C.text, marginBottom:12 }}>Cam kết đã được ghi nhận</div>
        <div style={{ fontSize:14, color:C.muted, maxWidth:480, margin:'0 auto', lineHeight:1.8, marginBottom:24 }}>
          Đây là quyết định khó nhưng đúng đắn. Danh mục của bạn sẽ được giải phóng dần.
          AI-Advisor sẽ nhắc bạn sau 7 ngày để kiểm tra tiến độ.
        </div>
        <div style={{ ...S.card, textAlign:'left', maxWidth:480, margin:'0 auto' }}>
          <div style={{ fontSize:14, fontWeight:600, marginBottom:12, color:C.gold }}>📋 Kế hoạch của bạn tuần này:</div>
          {enriched.map(p => (
            <div key={p.ticker} style={{ display:'flex', justifyContent:'space-between', padding:'8px 0', borderBottom:`1px solid ${C.border}` }}>
              <span style={{ fontWeight:600 }}>{p.ticker}</span>
              <span style={{ color: commits[p.ticker]==='full'?C.red: commits[p.ticker]==='partial'?C.orange:C.green, fontSize:13, fontWeight:600 }}>
                {commits[p.ticker]==='full' ? '🔴 Cắt toàn bộ' : commits[p.ticker]==='partial' ? '🟠 Cắt 30-50%' : '🟢 Giữ + đặt SL mới'}
              </span>
            </div>
          ))}
        </div>
      </div>
    )

    return (
      <div>
        <div style={{ textAlign:'center', marginBottom:24 }}>
          <div style={{ fontSize:24, fontWeight:800 }}>Kế hoạch cam kết</div>
          <div style={{ fontSize:14, color:C.muted }}>Chọn kịch bản bạn CAM KẾT thực hiện trong tuần này</div>
        </div>

        <div style={{ ...S.card, background:'rgba(245,158,11,0.08)', border:`1px solid rgba(245,158,11,0.3)`, marginBottom:20 }}>
          <div style={{ fontSize:13, color:'#fbbf24', lineHeight:1.8 }}>
            ⚠️ <strong>Lưu ý quan trọng:</strong> Cam kết không có nghĩa là làm một lúc.
            Một kịch bản có thể chia thành nhiều ngày. Quan trọng là tuân thủ đúng
            điều bạn đã tự đặt ra.
          </div>
        </div>

        {enriched.map(pos => {
          const v = verdicts[pos.ticker] || {}
          const vc = S.verdict_color(v.verdict)
          return (
            <div key={pos.ticker} style={{ ...S.card, marginBottom:12 }}>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:14 }}>
                <div>
                  <span style={{ fontSize:18, fontWeight:800 }}>{pos.ticker}</span>
                  <span style={{ marginLeft:10, fontSize:13, color:vc, fontWeight:600 }}>→ {v.verdict}</span>
                </div>
                <div style={{ fontSize:13, color:C.red, fontWeight:600 }}>{pct(pos.lossP)}</div>
              </div>

              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:8 }}>
                {[
                  { id:'full',    label:'🔴 Cắt toàn bộ', desc:`Giải phóng ${fmt(pos.totalVal)} VNĐ`, color:'rgba(220,38,38,0.15)', border:'rgba(220,38,38,0.4)' },
                  { id:'partial', label:'🟠 Cắt 30-50%',  desc:`Giải phóng ~${fmt(pos.totalVal*0.4)} VNĐ`, color:'rgba(234,88,12,0.15)', border:'rgba(234,88,12,0.4)' },
                  { id:'hold',    label:'🟢 Giữ + SL mới', desc:'Đặt SL cứng, không dời', color:'rgba(5,150,105,0.1)', border:'rgba(5,150,105,0.3)' },
                ].map(opt => (
                  <button key={opt.id} onClick={() => setCommits(c => ({...c,[pos.ticker]:opt.id}))}
                    style={{ padding:'12px 8px', borderRadius:8, border:`2px solid ${commits[pos.ticker]===opt.id ? opt.border : C.border}`,
                      background: commits[pos.ticker]===opt.id ? opt.color : 'transparent',
                      cursor:'pointer', textAlign:'center', transition:'all .15s' }}>
                    <div style={{ fontSize:13, fontWeight:700, color:C.text, marginBottom:4 }}>{opt.label}</div>
                    <div style={{ fontSize:11, color:C.muted }}>{opt.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )
        })}

        <div style={{ ...S.card, marginTop:8 }}>
          <div style={{ fontSize:14, color:C.muted, lineHeight:1.8 }}>
            💬 Sau khi thực hiện cam kết, hãy quay lại đây để ghi nhận.
            AI-Advisor sẽ nhắc bạn qua Telegram sau 7 ngày.
            <strong style={{ color:C.text }}> Mọi hành trình tốt hơn bắt đầu từ một hành động nhỏ hôm nay.</strong>
          </div>
        </div>

        <div style={{ display:'flex', justifyContent:'space-between' }}>
          <button style={S.btn('#334155')} onClick={() => setPhase(3)}>← Xem lại đánh giá</button>
          <button style={S.btn(C.green, !allCommitted)} disabled={!allCommitted} onClick={commitAndFinish}>
            ✅ Xác nhận cam kết
          </button>
        </div>
      </div>
    )
  }

  // ── Render ───────────────────────────────────────────────────────
  return (
    <div style={S.wrap}>
      <div style={S.inner}>
        {/* Phase bar */}
        <div style={{ display:'flex', marginBottom:24, borderBottom:`1px solid ${C.border}` }}>
          {PHASES.map((p,i) => (
            <div key={p} style={S.phase(i===phase, i<phase)}>{i < phase ? '✓ ' : ''}{p}</div>
          ))}
        </div>

        {phase === 0 && <Phase0 />}
        {phase === 1 && <Phase1 />}
        {phase === 2 && <Phase2 />}
        {phase === 3 && <Phase3 />}
        {phase === 4 && <Phase4 />}

        {/* v2.2 — disclaimer pháp lý bắt buộc */}
        <div style={{
          marginTop: 28, paddingTop: 16,
          borderTop: `1px solid ${C.border}`,
          fontSize: 11, color: C.muted,
          lineHeight: 1.7, textAlign: 'center',
        }}>
          Công cụ hỗ trợ quyết định — không phải tư vấn đầu tư.
          Quyết định và trách nhiệm thuộc về nhà đầu tư.
        </div>
      </div>
    </div>
  )
}
