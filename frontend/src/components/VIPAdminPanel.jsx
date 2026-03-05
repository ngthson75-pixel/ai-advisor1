/**
 * AI ADVISOR - VIP ADMIN PANEL
 * ==============================
 * File: src/components/VIPAdminPanel.jsx
 * Version: 1.0
 *
 * Trang quản lý VIP users dành cho Admin (Sơn).
 * Truy cập qua: /admin  hoặc mount vào route nội bộ.
 *
 * Tính năng:
 *  - Đăng nhập bằng ADMIN_KEY
 *  - Tạo tài khoản VIP cho khách mới
 *  - Bật / Tắt push notification per user
 *  - Gửi test push cho từng user
 *  - Ghi notes về deal / khách hàng
 */

import { useState, useEffect, useCallback } from 'react'

// ─────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────
// API URL — tự detect môi trường dựa theo hostname
const IS_STAGING = window.location.hostname.includes('staging')
const API = IS_STAGING
  ? 'https://ai-advisor1-staging.onrender.com'
  : (import.meta.env.VITE_API_URL || 'https://ai-advisor1-staging.onrender.com').replace(/\/api\/?$/, '')

// ─────────────────────────────────────────────
// STYLES (inline - không cần file riêng)
// ─────────────────────────────────────────────
const S = {
  page: {
    minHeight: '100vh',
    background: '#0f172a',
    color: '#f1f5f9',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    padding: '24px',
  },
  card: {
    background: '#1e293b',
    border: '1px solid #334155',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '20px',
  },
  input: {
    width: '100%',
    padding: '10px 14px',
    background: '#0f172a',
    border: '1px solid #475569',
    borderRadius: '8px',
    color: '#f1f5f9',
    fontSize: '14px',
    boxSizing: 'border-box',
  },
  btn: (color = '#3b82f6') => ({
    padding: '9px 16px',
    background: color,
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: '600',
    whiteSpace: 'nowrap',
  }),
  btnGhost: {
    padding: '9px 16px',
    background: 'transparent',
    color: '#94a3b8',
    border: '1px solid #475569',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  badge: (on) => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '3px 10px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '600',
    background: on ? 'rgba(34,197,94,0.15)' : 'rgba(100,116,139,0.2)',
    color: on ? '#4ade80' : '#64748b',
    border: `1px solid ${on ? 'rgba(34,197,94,0.3)' : 'rgba(100,116,139,0.3)'}`,
  }),
  label: {
    display: 'block',
    color: '#94a3b8',
    fontSize: '12px',
    marginBottom: '6px',
  },
  formGroup: { marginBottom: '14px' },
}

// ─────────────────────────────────────────────
// API HELPER
// ─────────────────────────────────────────────
function useApi(adminKey) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Admin-Key': adminKey,
  }

  const getUsers = () =>
    fetch(`${API}/api/admin/users`, { headers }).then(r => r.json())

  const createUser = (data) =>
    fetch(`${API}/api/admin/users/create`, {
      method: 'POST', headers, body: JSON.stringify(data),
    }).then(r => r.json())

  const togglePush = (id) =>
    fetch(`${API}/api/admin/users/${id}/toggle-push`, {
      method: 'POST', headers,
    }).then(r => r.json())

  const updateUser = (id, data) =>
    fetch(`${API}/api/admin/users/${id}`, {
      method: 'PATCH', headers, body: JSON.stringify(data),
    }).then(r => r.json())

  const testPush = (id) =>
    fetch(`${API}/api/admin/push/test/${id}`, {
      method: 'POST', headers,
    }).then(r => r.json())

  const broadcast = (data) =>
    fetch(`${API}/api/admin/push/broadcast`, {
      method: 'POST', headers, body: JSON.stringify(data),
    }).then(r => r.json())

  return { getUsers, createUser, togglePush, updateUser, testPush, broadcast }
}

// ─────────────────────────────────────────────
// COMPONENT: Login Gate
// ─────────────────────────────────────────────
function LoginGate({ onLogin }) {
  const [key, setKey] = useState('')
  const [err, setErr]  = useState('')
  const [loading, setLoading] = useState(false)
  const [showKey, setShowKey] = useState(false)

  const tryLogin = async () => {
    if (!key.trim()) return
    setLoading(true)
    setErr('')
    try {
      const res = await fetch(`${API}/api/admin/users`, {
        headers: { 'X-Admin-Key': key },
      })
      if (res.ok) {
        onLogin(key)
      } else {
        setErr('Admin key không đúng. Vui lòng kiểm tra lại.')
      }
    } catch {
      setErr('Không kết nối được server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ ...S.page, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ ...S.card, width: '100%', maxWidth: '380px' }}>
        <h2 style={{ margin: '0 0 4px', fontSize: '20px' }}>🔐 Admin Panel</h2>
        <p style={{ color: '#64748b', fontSize: '13px', margin: '0 0 20px' }}>
          AI Advisor — VIP User Management
        </p>
        <div style={S.formGroup}>
          <label style={S.label}>Admin Key</label>
          <div style={{ position: 'relative' }}>
            <input
              type={showKey ? 'text' : 'password'}
              style={{ ...S.input, paddingRight: '40px' }}
              placeholder="Nhập admin key..."
              value={key}
              onChange={e => setKey(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && tryLogin()}
            />
            <button
              onClick={() => setShowKey(v => !v)}
              style={{
                position: 'absolute', right: '10px', top: '50%',
                transform: 'translateY(-50%)',
                background: 'none', border: 'none',
                color: '#64748b', cursor: 'pointer', fontSize: '16px',
                padding: '4px',
              }}
              title={showKey ? 'Ẩn' : 'Hiện'}
            >
              {showKey ? '🙈' : '👁️'}
            </button>
          </div>
        </div>
        {err && <p style={{ color: '#f87171', fontSize: '13px', margin: '0 0 12px' }}>{err}</p>}
        <button
          style={{ ...S.btn(), width: '100%', padding: '12px' }}
          onClick={tryLogin}
          disabled={loading}
        >
          {loading ? 'Đang xác thực...' : '🔑 Đăng Nhập'}
        </button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
// COMPONENT: Create User Modal
// ─────────────────────────────────────────────
function CreateUserModal({ api, onClose, onSuccess }) {
  const [form, setForm] = useState({
    email: '', full_name: '', phone: '',
    tier: 'vip', notes: '', password: '',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr]         = useState('')

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async () => {
    if (!form.email) { setErr('Email là bắt buộc'); return }
    setLoading(true); setErr('')
    try {
      const data = await api.createUser(form)
      if (data.success) {
        setResult(data)
        onSuccess()
      } else {
        setErr(data.error || 'Lỗi không xác định')
      }
    } catch {
      setErr('Lỗi kết nối server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, padding: '20px',
    }}>
      <div style={{ ...S.card, width: '100%', maxWidth: '480px', margin: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>➕ Tạo Tài Khoản VIP</h3>
          <button style={S.btnGhost} onClick={onClose}>✕</button>
        </div>

        {!result ? (
          <>
            {[
              { key: 'email',     label: 'Email *',          type: 'email',    placeholder: 'khach@email.com' },
              { key: 'full_name', label: 'Họ và tên',        type: 'text',     placeholder: 'Nguyễn Văn A' },
              { key: 'phone',     label: 'Số điện thoại',    type: 'text',     placeholder: '0912345678' },
              { key: 'password',  label: 'Mật khẩu (để trống = tự tạo)', type: 'text', placeholder: 'Auto-generate nếu trống' },
            ].map(({ key, label, type, placeholder }) => (
              <div key={key} style={S.formGroup}>
                <label style={S.label}>{label}</label>
                <input
                  style={S.input} type={type}
                  placeholder={placeholder}
                  value={form[key]} onChange={set(key)}
                />
              </div>
            ))}

            <div style={S.formGroup}>
              <label style={S.label}>Tier</label>
              <select style={{ ...S.input }} value={form.tier} onChange={set('tier')}>
                <option value="vip">VIP (299k/tháng)</option>
                <option value="pro">Pro (499k/tháng)</option>
                <option value="free">Free (trial)</option>
              </select>
            </div>

            <div style={S.formGroup}>
              <label style={S.label}>Ghi chú nội bộ (deal, nguồn, v.v.)</label>
              <textarea
                style={{ ...S.input, minHeight: '72px', resize: 'vertical' }}
                placeholder="VD: Khách từ Telegram, deal 3 tháng, giá 800k..."
                value={form.notes} onChange={set('notes')}
              />
            </div>

            {err && <p style={{ color: '#f87171', fontSize: '13px', margin: '0 0 12px' }}>{err}</p>}

            <div style={{ display: 'flex', gap: '10px' }}>
              <button style={{ ...S.btn(), flex: 1 }} onClick={submit} disabled={loading}>
                {loading ? 'Đang tạo...' : '✅ Tạo Tài Khoản'}
              </button>
              <button style={S.btnGhost} onClick={onClose}>Hủy</button>
            </div>
          </>
        ) : (
          /* ── Success: Hiện credentials để gửi khách ── */
          <div>
            <div style={{
              background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)',
              borderRadius: '8px', padding: '16px', marginBottom: '16px',
            }}>
              <p style={{ color: '#4ade80', fontWeight: '700', margin: '0 0 12px' }}>
                ✅ Tạo tài khoản thành công!
              </p>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 8px' }}>
                📋 Thông tin đăng nhập gửi cho khách:
              </p>
              <div style={{
                background: '#0f172a', borderRadius: '8px', padding: '14px',
                fontFamily: 'monospace', fontSize: '13px',
              }}>
                <div style={{ color: '#94a3b8' }}>🌐 URL: <span style={{ color: '#f1f5f9' }}>https://ai-advisor.vn</span></div>
                <div style={{ color: '#94a3b8', marginTop: '4px' }}>📧 Email: <span style={{ color: '#60a5fa' }}>{result.credentials.email}</span></div>
                <div style={{ color: '#94a3b8', marginTop: '4px' }}>🔑 Pass: <span style={{ color: '#fbbf24' }}>{result.credentials.password}</span></div>
              </div>
              <p style={{ color: '#64748b', fontSize: '11px', margin: '10px 0 0' }}>
                ⚠️ Nhắc khách đổi mật khẩu sau khi đăng nhập lần đầu.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                style={{ ...S.btn('#10b981'), flex: 1 }}
                onClick={() => {
                  const text = `URL: https://ai-advisor.vn\nEmail: ${result.credentials.email}\nPass: ${result.credentials.password}`
                  navigator.clipboard.writeText(text)
                }}
              >
                📋 Copy Thông Tin
              </button>
              <button style={S.btnGhost} onClick={onClose}>Đóng</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
// COMPONENT: User Row
// ─────────────────────────────────────────────
function UserRow({ user, api, onRefresh }) {
  const [loading, setLoading]   = useState(false)
  const [editing, setEditing]   = useState(false)
  const [notes, setNotes]       = useState(user.notes || '')
  const [feedback, setFeedback] = useState('')

  const doToggle = async () => {
    setLoading(true)
    const data = await api.togglePush(user.id)
    setFeedback(data.message || '')
    setTimeout(() => setFeedback(''), 3000)
    onRefresh()
    setLoading(false)
  }

  const doTestPush = async () => {
    setLoading(true)
    const data = await api.testPush(user.id)
    setFeedback(data.success
      ? `✅ Test sent: ${data.stats?.sent ?? 0} device(s)`
      : `❌ ${data.error}`
    )
    setTimeout(() => setFeedback(''), 4000)
    setLoading(false)
  }

  const saveNotes = async () => {
    await api.updateUser(user.id, { notes })
    setEditing(false)
    onRefresh()
  }

  const fmt = (iso) => iso
    ? new Date(iso).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
    : '—'

  return (
    <div style={{
      ...S.card,
      marginBottom: '12px',
      borderLeft: `3px solid ${user.is_push_enabled ? '#4ade80' : '#475569'}`,
    }}>
      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
        {/* Avatar */}
        <div style={{
          width: '40px', height: '40px', borderRadius: '50%',
          background: '#3b82f6', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: '18px', flexShrink: 0,
        }}>
          {(user.full_name || user.email)[0].toUpperCase()}
        </div>

        {/* Info */}
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: '700', fontSize: '15px' }}>
            {user.full_name || '(Chưa có tên)'}
          </div>
          <div style={{ color: '#60a5fa', fontSize: '13px' }}>{user.email}</div>
          {user.phone && (
            <div style={{ color: '#94a3b8', fontSize: '12px' }}>📞 {user.phone}</div>
          )}
        </div>

        {/* Status badges */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={S.badge(user.is_active)}>
            {user.is_active ? '● Active' : '● Inactive'}
          </span>
          <span style={{
            ...S.badge(user.tier === 'vip' || user.tier === 'pro'),
            background: user.tier === 'pro'
              ? 'rgba(251,191,36,0.15)'
              : user.tier === 'vip'
              ? 'rgba(59,130,246,0.15)'
              : 'rgba(100,116,139,0.15)',
            color: user.tier === 'pro' ? '#fbbf24'
                 : user.tier === 'vip' ? '#60a5fa' : '#94a3b8',
          }}>
            {user.tier.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Stats row */}
      <div style={{
        display: 'flex', gap: '20px', flexWrap: 'wrap',
        marginTop: '14px', paddingTop: '14px',
        borderTop: '1px solid #334155',
        fontSize: '12px', color: '#94a3b8',
      }}>
        <div>📱 Thiết bị: <strong style={{ color: user.push_devices > 0 ? '#4ade80' : '#f87171' }}>{user.push_devices}</strong></div>
        <div>🔔 Push: <strong style={{ color: user.is_push_enabled ? '#4ade80' : '#64748b' }}>
          {user.is_push_enabled ? 'Đang bật' : 'Đang tắt'}
        </strong></div>
        <div>📅 Tạo: {fmt(user.created_at)}</div>
        <div>🕐 Đăng nhập: {fmt(user.last_login_at)}</div>
      </div>

      {/* Notes */}
      {editing ? (
        <div style={{ marginTop: '12px' }}>
          <textarea
            style={{ ...S.input, minHeight: '60px', marginBottom: '8px' }}
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Ghi chú về khách hàng..."
          />
          <div style={{ display: 'flex', gap: '8px' }}>
            <button style={S.btn('#10b981')} onClick={saveNotes}>💾 Lưu</button>
            <button style={S.btnGhost} onClick={() => setEditing(false)}>Hủy</button>
          </div>
        </div>
      ) : user.notes ? (
        <div
          style={{
            marginTop: '10px', padding: '8px 12px',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '6px', fontSize: '12px', color: '#94a3b8',
            cursor: 'pointer',
          }}
          onClick={() => setEditing(true)}
          title="Click để sửa"
        >
          📝 {user.notes}
        </div>
      ) : null}

      {/* Feedback */}
      {feedback && (
        <div style={{
          marginTop: '10px', padding: '8px 12px',
          background: 'rgba(59,130,246,0.1)', borderRadius: '6px',
          fontSize: '12px', color: '#60a5fa',
        }}>
          {feedback}
        </div>
      )}

      {/* Action buttons */}
      <div style={{
        display: 'flex', gap: '8px', flexWrap: 'wrap',
        marginTop: '14px', paddingTop: '14px',
        borderTop: '1px solid #334155',
      }}>
        <button
          style={S.btn(user.is_push_enabled ? '#64748b' : '#10b981')}
          onClick={doToggle}
          disabled={loading}
        >
          {user.is_push_enabled ? '🔕 Tắt Push' : '🔔 Bật Push'}
        </button>

        <button
          style={S.btn('#6366f1')}
          onClick={doTestPush}
          disabled={loading || !user.is_push_enabled || user.push_devices === 0}
          title={user.push_devices === 0 ? 'Chưa có thiết bị subscribe' : 'Gửi test notification'}
        >
          🧪 Test Push
        </button>

        <button
          style={S.btnGhost}
          onClick={() => setEditing(true)}
        >
          ✏️ Ghi chú
        </button>
      </div>

      {user.push_devices === 0 && (
        <p style={{ color: '#f59e0b', fontSize: '11px', margin: '8px 0 0' }}>
          ⚠️ Chưa có thiết bị nào. Khách cần login và bật thông báo trên app trước.
        </p>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────
// COMPONENT: Broadcast Modal
// ─────────────────────────────────────────────
function BroadcastModal({ api, onClose }) {
  const [form, setForm]     = useState({ title: '', body: '', url: '/dashboard' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const send = async () => {
    if (!form.title || !form.body) return
    setLoading(true)
    const data = await api.broadcast(form)
    setResult(data)
    setLoading(false)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, padding: '20px',
    }}>
      <div style={{ ...S.card, width: '100%', maxWidth: '420px', margin: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>📣 Broadcast Push</h3>
          <button style={S.btnGhost} onClick={onClose}>✕</button>
        </div>

        {!result ? (
          <>
            <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 16px' }}>
              Gửi thông báo đến TẤT CẢ VIP users đang bật push.
            </p>
            {[
              { k: 'title', label: 'Tiêu đề', placeholder: '📊 Tín hiệu mới...' },
              { k: 'body',  label: 'Nội dung', placeholder: 'VCB: Entry 89,500 | SL: 85,000 | TP: 96,600' },
              { k: 'url',   label: 'URL khi click', placeholder: '/dashboard' },
            ].map(({ k, label, placeholder }) => (
              <div key={k} style={S.formGroup}>
                <label style={S.label}>{label}</label>
                <input style={S.input} placeholder={placeholder} value={form[k]} onChange={set(k)} />
              </div>
            ))}
            <div style={{ display: 'flex', gap: '10px' }}>
              <button style={{ ...S.btn('#ef4444'), flex: 1 }} onClick={send} disabled={loading}>
                {loading ? 'Đang gửi...' : '📣 Gửi Broadcast'}
              </button>
              <button style={S.btnGhost} onClick={onClose}>Hủy</button>
            </div>
          </>
        ) : (
          <div>
            <p style={{ color: '#4ade80', fontWeight: '700' }}>✅ Đã gửi!</p>
            <div style={{ background: '#0f172a', borderRadius: '8px', padding: '14px', fontSize: '13px' }}>
              <div>📤 Sent: <strong>{result.stats?.sent ?? 0}</strong></div>
              <div>❌ Failed: <strong>{result.stats?.failed ?? 0}</strong></div>
              <div>🗑️ Removed: <strong>{result.stats?.removed ?? 0}</strong></div>
            </div>
            <button style={{ ...S.btnGhost, marginTop: '14px', width: '100%' }} onClick={onClose}>
              Đóng
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────
export default function VIPAdminPanel() {
  const [adminKey, setAdminKey]       = useState(() => sessionStorage.getItem('admin_key') || '')
  const [users, setUsers]             = useState([])
  const [loading, setLoading]         = useState(false)
  const [showCreate, setShowCreate]   = useState(false)
  const [showBroadcast, setShowBroadcast] = useState(false)
  const [search, setSearch]           = useState('')

  const api = useApi(adminKey)

  const loadUsers = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getUsers()
      if (data.success) setUsers(data.users)
    } finally {
      setLoading(false)
    }
  }, [adminKey])

  useEffect(() => {
    if (adminKey) {
      sessionStorage.setItem('admin_key', adminKey)
      loadUsers()
    }
  }, [adminKey])

  if (!adminKey) {
    return <LoginGate onLogin={setAdminKey} />
  }

  const filtered = users.filter(u =>
    u.email.includes(search) ||
    (u.full_name || '').toLowerCase().includes(search.toLowerCase()) ||
    (u.notes || '').toLowerCase().includes(search.toLowerCase())
  )

  const pushEnabled  = users.filter(u => u.is_push_enabled).length
  const withDevices  = users.filter(u => u.push_devices > 0).length

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '22px' }}>🛡️ VIP Admin Panel</h1>
          <p style={{ color: '#64748b', fontSize: '13px', margin: '4px 0 0' }}>AI Advisor — Quản lý tài khoản VIP</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button style={S.btn('#ef4444')} onClick={() => setShowBroadcast(true)}>
            📣 Broadcast Push
          </button>
          <button style={S.btn('#10b981')} onClick={() => setShowCreate(true)}>
            ➕ Tạo VIP Account
          </button>
          <button style={S.btnGhost} onClick={loadUsers}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', marginBottom: '20px' }}>
        {[
          { label: 'Tổng Users',   value: users.length,  color: '#60a5fa' },
          { label: 'Push Bật',     value: pushEnabled,   color: '#4ade80' },
          { label: 'Có Thiết Bị',  value: withDevices,   color: '#fbbf24' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ ...S.card, padding: '16px 20px', marginBottom: 0, flex: '1 1 120px' }}>
            <div style={{ fontSize: '24px', fontWeight: '800', color }}>{value}</div>
            <div style={{ color: '#64748b', fontSize: '12px', marginTop: '4px' }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Search */}
      <div style={{ marginBottom: '16px' }}>
        <input
          style={S.input}
          placeholder="🔍 Tìm theo email, tên, ghi chú..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* User List */}
      {loading ? (
        <div style={{ textAlign: 'center', color: '#64748b', padding: '40px' }}>Đang tải...</div>
      ) : filtered.length === 0 ? (
        <div style={{ ...S.card, textAlign: 'center', color: '#64748b', padding: '40px' }}>
          {users.length === 0
            ? '👋 Chưa có VIP user nào. Nhấn "Tạo VIP Account" để bắt đầu.'
            : 'Không tìm thấy kết quả.'}
        </div>
      ) : (
        filtered.map(user => (
          <UserRow
            key={user.id}
            user={user}
            api={api}
            onRefresh={loadUsers}
          />
        ))
      )}

      {/* Modals */}
      {showCreate && (
        <CreateUserModal
          api={api}
          onClose={() => setShowCreate(false)}
          onSuccess={loadUsers}
        />
      )}
      {showBroadcast && (
        <BroadcastModal
          api={api}
          onClose={() => setShowBroadcast(false)}
        />
      )}
    </div>
  )
}
