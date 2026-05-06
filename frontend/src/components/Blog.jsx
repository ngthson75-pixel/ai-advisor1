import { useState, useEffect } from 'react'

// ============================================================
// BLOG DATA — Thêm bài mới vào đây
// Mỗi bài có: slug, title, excerpt, date, readTime, category,
//             keywords (SEO), content (HTML string)
// ============================================================
const BLOG_POSTS = [
  {
    slug: 'tai-sao-95-nha-dau-tu-nho-le-thua-lo',
    title: 'Tại sao 95% nhà đầu tư nhỏ lẻ thua lỗ — và cách thoát khỏi vòng lặp đó',
    excerpt: 'Không phải vì thiếu thông tin, không phải vì thị trường bất công. Lý do thực sự khiến hầu hết nhà đầu tư thua lỗ là thứ mà không ai muốn thừa nhận.',
    date: '2026-04-28',
    readTime: '6 phút',
    category: 'Tâm lý đầu tư',
    keywords: 'nhà đầu tư thua lỗ, tâm lý đầu tư, FOMO chứng khoán, kỷ luật đầu tư',
    content: `
      <p>Có một con số mà hầu hết người trong ngành đều biết nhưng ít ai nói thẳng: <strong>95% nhà đầu tư nhỏ lẻ thua lỗ trong dài hạn.</strong></p>
      <p>Không phải vì họ ngu. Không phải vì thị trường bất công với người nhỏ. Lý do thực sự nằm ở một chỗ khác hoàn toàn.</p>

      <h2>Não người không được thiết kế để đầu tư</h2>
      <p>Não bộ của chúng ta được tiến hóa để sinh tồn trong môi trường tự nhiên — không phải để giao dịch chứng khoán. Hai phản xạ tự nhiên nhất của não lại trở thành kẻ thù số một khi đầu tư:</p>
      <ul>
        <li><strong>FOMO (Fear of Missing Out):</strong> Khi thấy cổ phiếu tăng mạnh, não kích hoạt vùng reward — bạn cảm thấy cần phải mua ngay, dù biết đã muộn.</li>
        <li><strong>Panic Selling:</strong> Khi danh mục giảm, não kích hoạt phản xạ thoát khỏi nguy hiểm — bạn bán tháo dù biết đây có thể là đáy.</li>
      </ul>
      <p>Kết quả: mua đỉnh, bán đáy. Lặp đi lặp lại. Không phải vì thiếu kiến thức — mà vì cảm xúc luôn nhanh hơn logic.</p>

      <h2>Ba sai lầm phổ biến nhất</h2>
      <p><strong>1. Không có kế hoạch thoát từ trước.</strong> Hầu hết nhà đầu tư chỉ nghĩ đến lúc mua — không nghĩ đến lúc bán. Khi giá xuống, không có quy tắc nào để bám vào, chỉ có cảm xúc dẫn đường.</p>
      <p><strong>2. Không đặt stop-loss.</strong> "Để chờ nó hồi" là câu tự nhủ phổ biến nhất. Và thường là câu đắt nhất. Lỗ -10% cần tăng +11% để hòa vốn. Lỗ -30% cần tăng +43%.</p>
      <p><strong>3. Overtrading.</strong> Giao dịch quá nhiều không chỉ tốn phí — nó còn làm tăng cơ hội mắc sai lầm cảm xúc. Mỗi lệnh là một cơ hội để FOMO hoặc panic xen vào.</p>

      <h2>Giải pháp không phải là "kỷ luật hơn"</h2>
      <p>Nhiều người nghĩ: "Tôi cần kỷ luật hơn." Nhưng kỷ luật là tài nguyên hữu hạn — nó cạn kiệt khi thị trường biến động mạnh, khi bạn mệt mỏi, khi tin tức tiêu cực ập đến.</p>
      <p>Giải pháp bền vững là <strong>hệ thống hóa quyết định</strong> — xây dựng bộ quy tắc rõ ràng trước khi vào lệnh, để khi cảm xúc kéo đến, bạn đã có câu trả lời sẵn rồi.</p>
      <p>Đó là lý do AI Advisor được xây dựng: không thay bạn quyết định, mà giúp bạn quyết định tỉnh táo hơn — với tín hiệu có confidence score, stop-loss được tính sẵn, và AI Discipline Coach hỏi bạn 6 câu trước khi bấm lệnh.</p>

      <h2>Bắt đầu từ đâu?</h2>
      <p>Nếu bạn nhận ra mình đang trong vòng lặp mua đỉnh bán đáy, đây là 3 thứ cần làm ngay:</p>
      <ul>
        <li>Viết ra quy tắc stop-loss cho mỗi lệnh — trước khi vào, không phải sau khi lỗ</li>
        <li>Giới hạn số lệnh mỗi tuần — ít hơn nhưng chất lượng hơn</li>
        <li>Theo dõi cảm xúc khi giao dịch — FOMO hay logic đang dẫn đường?</li>
      </ul>
      <p>Thị trường không thiếu cơ hội. Thứ thiếu là hệ thống để nắm bắt chúng một cách nhất quán.</p>
    `
  },
  {
    slug: 'stop-loss-la-gi-huong-dan-dat-stop-loss-dung-cach',
    title: 'Stop-loss là gì? Hướng dẫn đặt stop-loss đúng cách cho nhà đầu tư Việt Nam',
    excerpt: 'Stop-loss không phải thất bại — đó là kỹ năng quan trọng nhất giúp bạn còn tiền để chiến tiếp. Hướng dẫn thực tế từ A đến Z.',
    date: '2026-04-21',
    readTime: '8 phút',
    category: 'Kỹ thuật cơ bản',
    keywords: 'stop loss là gì, cách đặt stop loss, stop loss chứng khoán, quản lý rủi ro đầu tư',
    content: `
      <p>Hỏi 10 nhà đầu tư thua lỗ nặng, đa số sẽ nói một điều giống nhau: <em>"Tôi không đặt stop-loss."</em></p>
      <p>Đây là bài viết giải thích stop-loss từ đầu — không phức tạp, không lý thuyết, chỉ những gì bạn cần biết để áp dụng ngay.</p>

      <h2>Stop-loss là gì?</h2>
      <p>Stop-loss (cắt lỗ) là mức giá mà bạn quyết định trước: <em>"Nếu cổ phiếu xuống đến đây, tôi sẽ bán và chấp nhận khoản lỗ này."</em></p>
      <p>Ví dụ đơn giản: Bạn mua VPB ở 18,000 đồng/cp. Bạn đặt stop-loss ở -10% = 16,200 đồng. Nếu giá xuống 16,200 — bạn bán ngay, không chờ, không hy vọng.</p>

      <h2>Tại sao cần stop-loss?</h2>
      <p>Toán học rất đơn giản:</p>
      <ul>
        <li>Lỗ -10% → cần tăng +11% để hòa vốn</li>
        <li>Lỗ -20% → cần tăng +25% để hòa vốn</li>
        <li>Lỗ -50% → cần tăng +100% để hòa vốn</li>
      </ul>
      <p>Càng để lỗ sâu, càng khó gỡ. Stop-loss giúp bạn thoát sớm khi còn có thể — và giữ lại vốn để tìm cơ hội tốt hơn.</p>

      <h2>Ba cách đặt stop-loss phổ biến</h2>
      <p><strong>1. Stop-loss theo %</strong><br/>Đơn giản nhất. Chọn mức lỗ tối đa bạn chấp nhận (thường 7-10%) và tính ra mức giá tương ứng.</p>
      <p><strong>2. Stop-loss theo vùng hỗ trợ kỹ thuật</strong><br/>Đặt stop-loss ngay dưới vùng hỗ trợ quan trọng. Nếu giá phá vỡ vùng hỗ trợ — xu hướng đã đổi, nên thoát.</p>
      <p><strong>3. Trailing stop-loss</strong><br/>Stop-loss tự động "kéo theo" khi giá tăng. Ví dụ: trailing -8%. Cổ phiếu tăng từ 18,000 lên 22,000 → stop-loss tự động lên 20,240. Lãi được bảo vệ tự động.</p>

      <h2>Quy tắc 2% — nguyên tắc vàng quản lý rủi ro</h2>
      <p>Trader chuyên nghiệp có một quy tắc: <strong>mỗi lệnh không risk quá 2% tổng vốn.</strong></p>
      <p>Tài khoản 100 triệu → tối đa lỗ 2 triệu/lệnh. Sai 10 lần liên tiếp vẫn còn 80% vốn để tiếp tục. Đây là lý do họ sống sót qua bear market.</p>

      <h2>Sai lầm phổ biến khi đặt stop-loss</h2>
      <ul>
        <li><strong>Đặt quá sát:</strong> Stop-loss ở -2-3% dễ bị "quét" bởi biến động bình thường</li>
        <li><strong>Dời stop-loss xuống khi giá tiếp cận:</strong> Đây là thói quen nguy hiểm nhất — phá vỡ mục đích của stop-loss</li>
        <li><strong>Không đặt ngay từ đầu:</strong> "Để xem đã" — và khi nhớ ra thì đã lỗ 20%</li>
      </ul>

      <h2>AI Advisor và stop-loss tự động</h2>
      <p>Mỗi tín hiệu trong AI Advisor đều kèm theo stop-loss được tính toán tự động dựa trên ATR (Average True Range) — phản ánh mức biến động thực tế của cổ phiếu, không phải con số cố định.</p>
      <p>Bạn không cần tự tính — chỉ cần thực thi đúng theo kế hoạch.</p>
    `
  },
  {
    slug: 'fomo-dau-tu-la-gi-cach-kiem-soat',
    title: 'FOMO trong đầu tư là gì? Cách nhận biết và kiểm soát cảm xúc khi thị trường tăng nóng',
    excerpt: 'FOMO khiến nhà đầu tư mua ở đỉnh, bán ở đáy. Đây là cơ chế hoạt động của nó và cách bạn có thể kiểm soát trước khi mất tiền.',
    date: '2026-04-14',
    readTime: '5 phút',
    category: 'Tâm lý đầu tư',
    keywords: 'FOMO là gì, FOMO đầu tư, kiểm soát cảm xúc đầu tư, tâm lý chứng khoán',
    content: `
      <p>FOMO — Fear of Missing Out — là nỗi sợ bỏ lỡ cơ hội. Trong đầu tư, nó là thứ khiến bạn mua cổ phiếu khi mọi người đang hưng phấn nhất — và thường là khi giá đã ở đỉnh.</p>

      <h2>FOMO hoạt động như thế nào trong não?</h2>
      <p>Khi thấy một cổ phiếu tăng mạnh, não kích hoạt vùng reward (dopamine). Bạn cảm thấy phấn khích, muốn tham gia. Đồng thời, vùng amygdala — xử lý nỗi sợ — kích hoạt nỗi sợ bỏ lỡ.</p>
      <p>Hai tín hiệu này cộng lại tạo ra cảm giác cấp bách: <em>"Phải mua ngay, nếu không sẽ bỏ lỡ."</em> Và quyết định được đưa ra trước khi phần lý trí của não kịp xử lý.</p>

      <h2>5 dấu hiệu bạn đang bị FOMO</h2>
      <ul>
        <li>Mua cổ phiếu vì thấy group hội nhóm đang hype, không có phân tích riêng</li>
        <li>Cảm giác "lần này khác" — lý do hóa cho việc bỏ qua quy tắc</li>
        <li>Vào lệnh nhanh mà không xem chart, không đặt stop-loss</li>
        <li>Tăng kích thước lệnh vì "chắc chắn lần này thắng"</li>
        <li>Không ngủ được vì lo giá tăng mà mình chưa mua</li>
      </ul>

      <h2>Tại sao FOMO đặc biệt nguy hiểm trong thị trường Việt Nam?</h2>
      <p>Thị trường Việt Nam có đặc điểm tâm lý bầy đàn mạnh — thông tin lan nhanh qua Zalo, Facebook, hội nhóm. Một cổ phiếu được "đánh lên" có thể thu hút dòng tiền rất nhanh, tạo momentum giả.</p>
      <p>FOMO mua vào đúng lúc "cá mập" đang xả hàng là kịch bản phổ biến nhất của nhà đầu tư thua lỗ.</p>

      <h2>Cách kiểm soát FOMO — thực tế</h2>
      <p><strong>1. Có checklist bắt buộc trước mỗi lệnh.</strong> 6 câu hỏi đơn giản: Tôi đã phân tích chưa? Đây có phải chiến lược của tôi không? Tôi đã đặt stop-loss chưa? Số tiền này tôi có thể mất không?...</p>
      <p><strong>2. Tạo khoảng dừng 24 giờ.</strong> Nếu sau 24 giờ vẫn muốn mua — đó không phải FOMO. Nếu hết muốn — cảm ơn quy tắc này đã cứu bạn.</p>
      <p><strong>3. Không xem hội nhóm khi thị trường đang tăng mạnh.</strong> Nguồn FOMO lớn nhất. Tắt notification, focus vào hệ thống của riêng mình.</p>
      <p>AI Discipline Coach trong AI Advisor được thiết kế để làm đúng điều này — tạo khoảng dừng bắt buộc và hỏi những câu khó trước khi bạn kịp bấm lệnh vì FOMO.</p>
    `
  }
]

const CATEGORIES = ['Tất cả', 'Tâm lý đầu tư', 'Kỹ thuật cơ bản', 'Quản lý rủi ro', 'Thị trường']

// ============================================================
// BLOG LIST PAGE
// ============================================================
function BlogList({ onSelectPost }) {
  const [activeCategory, setActiveCategory] = useState('Tất cả')

  const filtered = activeCategory === 'Tất cả'
    ? BLOG_POSTS
    : BLOG_POSTS.filter(p => p.category === activeCategory)

  return (
    <div style={{ minHeight: '100vh', background: '#0a0e17', color: '#e2e8f0' }}>
      {/* Header */}
      <header style={{ borderBottom: '1px solid #1e293b', padding: '0 24px' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
          <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#00d4aa', boxShadow: '0 0 8px #00d4aa88' }} />
            <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 15 }}>AI Advisor</span>
          </a>
          <a href="/" style={{ color: '#64748b', fontSize: 13, textDecoration: 'none' }}>← Quay lại app</a>
        </div>
      </header>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px' }}>
        {/* Hero */}
        <div style={{ marginBottom: 48, textAlign: 'center' }}>
          <div style={{ display: 'inline-block', background: '#00d4aa18', border: '1px solid #00d4aa44', color: '#00d4aa', fontSize: 11, fontWeight: 600, padding: '4px 12px', borderRadius: 20, letterSpacing: '0.06em', marginBottom: 16 }}>
            KIẾN THỨC ĐẦU TƯ
          </div>
          <h1 style={{ fontSize: 'clamp(28px,5vw,42px)', fontWeight: 700, color: '#f1f5f9', lineHeight: 1.2, marginBottom: 16 }}>
            Blog AI Advisor
          </h1>
          <p style={{ color: '#64748b', fontSize: 16, maxWidth: 560, margin: '0 auto' }}>
            Kiến thức thực chiến về tâm lý đầu tư, quản lý rủi ro và kỷ luật giao dịch — không lý thuyết suông.
          </p>
        </div>

        {/* Category Filter */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 40 }}>
          {CATEGORIES.map(cat => (
            <button key={cat} onClick={() => setActiveCategory(cat)} style={{
              padding: '7px 16px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
              background: activeCategory === cat ? '#00d4aa18' : '#0f1623',
              border: activeCategory === cat ? '1px solid #00d4aa' : '1px solid #1e293b',
              color: activeCategory === cat ? '#00d4aa' : '#64748b',
            }}>
              {cat}
            </button>
          ))}
        </div>

        {/* Post Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(320px,1fr))', gap: 24 }}>
          {filtered.map((post, i) => (
            <article key={post.slug} onClick={() => onSelectPost(post)} style={{
              background: '#0f1623', border: '1px solid #1e293b', borderRadius: 12,
              padding: 24, cursor: 'pointer', transition: 'all 0.2s',
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = '#00d4aa44'; e.currentTarget.style.transform = 'translateY(-2px)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = '#1e293b'; e.currentTarget.style.transform = 'none' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                <span style={{ background: '#00d4aa18', color: '#00d4aa', fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20 }}>
                  {post.category}
                </span>
                <span style={{ color: '#334155', fontSize: 11 }}>{post.readTime}</span>
              </div>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9', lineHeight: 1.5, marginBottom: 10 }}>{post.title}</h2>
              <p style={{ color: '#64748b', fontSize: 13, lineHeight: 1.7, marginBottom: 16 }}>{post.excerpt}</p>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ color: '#334155', fontSize: 12 }}>
                  {new Date(post.date).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                </span>
                <span style={{ color: '#00d4aa', fontSize: 12, fontWeight: 500 }}>Đọc tiếp →</span>
              </div>
            </article>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid #1e293b', padding: '24px', marginTop: 64, textAlign: 'center' }}>
        <p style={{ color: '#334155', fontSize: 12 }}>© 2026 AI Advisor · <em>Công cụ hỗ trợ quyết định, không phải tư vấn đầu tư</em></p>
      </footer>
    </div>
  )
}

// ============================================================
// BLOG POST PAGE
// ============================================================
function BlogPost({ post, onBack }) {
  useEffect(() => {
    window.scrollTo(0, 0)
    document.title = `${post.title} | AI Advisor Blog`
  }, [post])

  return (
    <div style={{ minHeight: '100vh', background: '#0a0e17', color: '#e2e8f0' }}>
      {/* Header */}
      <header style={{ borderBottom: '1px solid #1e293b', padding: '0 24px', position: 'sticky', top: 0, background: '#0a0e17', zIndex: 10 }}>
        <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
          <a href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#00d4aa', boxShadow: '0 0 8px #00d4aa88' }} />
            <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: 15 }}>AI Advisor</span>
          </a>
          <button onClick={onBack} style={{ background: 'none', border: '1px solid #1e293b', color: '#64748b', fontSize: 13, padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontFamily: 'inherit' }}>
            ← Blog
          </button>
        </div>
      </header>

      {/* Article */}
      <article style={{ maxWidth: 760, margin: '0 auto', padding: '48px 24px 80px' }}>
        {/* Meta */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
          <span style={{ background: '#00d4aa18', color: '#00d4aa', fontSize: 11, fontWeight: 600, padding: '4px 12px', borderRadius: 20, border: '1px solid #00d4aa44' }}>
            {post.category}
          </span>
          <span style={{ color: '#334155', fontSize: 13 }}>
            {new Date(post.date).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })}
          </span>
          <span style={{ color: '#334155', fontSize: 13 }}>· {post.readTime} đọc</span>
        </div>

        {/* Title */}
        <h1 style={{ fontSize: 'clamp(24px,4vw,34px)', fontWeight: 700, color: '#f1f5f9', lineHeight: 1.3, marginBottom: 20 }}>
          {post.title}
        </h1>

        {/* Excerpt */}
        <p style={{ fontSize: 17, color: '#94a3b8', lineHeight: 1.8, marginBottom: 40, paddingBottom: 40, borderBottom: '1px solid #1e293b' }}>
          {post.excerpt}
        </p>

        {/* Content */}
        <div className="blog-content" dangerouslySetInnerHTML={{ __html: post.content }} />

        {/* CTA */}
        <div style={{ marginTop: 56, padding: 32, background: 'linear-gradient(135deg, #00d4aa0d, #0f1623)', border: '1px solid #00d4aa22', borderRadius: 16, textAlign: 'center' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#00d4aa', letterSpacing: '0.08em', marginBottom: 12 }}>AI ADVISOR</div>
          <h3 style={{ fontSize: 20, fontWeight: 700, color: '#f1f5f9', marginBottom: 10 }}>
            Không thay bạn quyết định — giúp bạn quyết định tỉnh táo hơn
          </h3>
          <p style={{ color: '#64748b', fontSize: 14, marginBottom: 24 }}>
            Tín hiệu BUY/SELL với stop-loss tự động · AI Risk Shield · Discipline Coach
          </p>
          <a href="/" style={{
            display: 'inline-block', padding: '12px 28px',
            background: 'linear-gradient(135deg, #00d4aa, #00b894)', borderRadius: 10,
            color: '#0a0e17', fontWeight: 700, fontSize: 15, textDecoration: 'none',
          }}>
            Thử miễn phí →
          </a>
        </div>

        {/* Back */}
        <button onClick={onBack} style={{ marginTop: 40, background: 'none', border: 'none', color: '#64748b', fontSize: 14, cursor: 'pointer', fontFamily: 'inherit' }}>
          ← Xem tất cả bài viết
        </button>
      </article>

      {/* Blog content styles */}
      <style>{`
        .blog-content { font-size: 16px; line-height: 1.85; color: #cbd5e1; }
        .blog-content h2 { font-size: 22px; font-weight: 600; color: #f1f5f9; margin: 40px 0 16px; }
        .blog-content p { margin-bottom: 20px; }
        .blog-content ul { padding-left: 20px; margin-bottom: 20px; }
        .blog-content li { margin-bottom: 10px; color: #94a3b8; }
        .blog-content strong { color: #e2e8f0; font-weight: 600; }
        .blog-content em { color: #94a3b8; font-style: italic; }
      `}</style>
    </div>
  )
}

// ============================================================
// MAIN EXPORT
// ============================================================
export default function Blog() {
  const [selectedPost, setSelectedPost] = useState(null)

  // Check URL for direct post link: /blog/slug
  useEffect(() => {
    const path = window.location.pathname
    const match = path.match(/^\/blog\/(.+)$/)
    if (match) {
      const post = BLOG_POSTS.find(p => p.slug === match[1])
      if (post) setSelectedPost(post)
    }
  }, [])

  const handleSelectPost = (post) => {
    setSelectedPost(post)
    window.history.pushState({}, '', `/blog/${post.slug}`)
  }

  const handleBack = () => {
    setSelectedPost(null)
    window.history.pushState({}, '', '/blog')
  }

  if (selectedPost) return <BlogPost post={selectedPost} onBack={handleBack} />
  return <BlogList onSelectPost={handleSelectPost} />
}
