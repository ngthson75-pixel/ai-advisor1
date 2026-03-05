/**
 * AI ADVISOR - PWA NOTIFICATION MANAGER v2
 * ==========================================
 * File: src/components/PWANotificationManager.jsx
 * Version: 2.0 — VIP-aware, JWT binding
 *
 * THAY ĐỔI SO VỚI v1:
 *  - Gắn userId thật từ JWT khi subscribe (thay vì 'anonymous')
 *  - Gửi Authorization header khi save subscription
 *  - Admin-controlled: push chỉ hoạt động khi admin bật
 *  - Hiển thị trạng thái "Chờ admin kích hoạt" nếu user chưa được bật
 *
 * SỬ DỤNG (App.jsx):
 *   import PWANotificationManager from './components/PWANotificationManager'
 *   <PWANotificationManager userId={user?.id} token={jwtToken} isPushEnabled={user?.is_push_enabled} />
 */

import { useState, useEffect, useCallback } from 'react'

// ─────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────
const _isStaging = typeof window !== 'undefined' && window.location.hostname.includes('staging')
const API_BASE = _isStaging
  ? 'https://ai-advisor1-staging.onrender.com'
  : (import.meta.env.VITE_API_URL || 'https://ai-advisor1-staging.onrender.com').replace(/\/api\/?$/, '')
const STORAGE_KEY_SUB       = 'ai_advisor_push_sub_v2'
const STORAGE_KEY_DISMISSED = 'ai_advisor_push_dismissed_v2'

// ─────────────────────────────────────────────
// UTILS
// ─────────────────────────────────────────────

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64  = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  return Uint8Array.from([...rawData].map(c => c.charCodeAt(0)))
}

function isPushSupported() {
  return 'serviceWorker' in navigator &&
         'PushManager'   in window    &&
         'Notification'  in window
}

async function registerServiceWorker() {
  try {
    const reg = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
      updateViaCache: 'none',
    })
    console.log('[PWA v2] SW registered')
    return reg
  } catch (err) {
    console.error('[PWA v2] SW failed:', err)
    return null
  }
}

async function fetchVapidKey() {
  try {
    const res  = await fetch(`${API_BASE}/api/push/vapid-public-key`)
    if (!res.ok) throw new Error('VAPID key not available')
    const data = await res.json()
    return data.publicKey
  } catch (err) {
    console.error('[PWA v2] VAPID key error:', err)
    return null
  }
}

// ─────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────

/**
 * @param {number|string} userId        - Real user ID từ VIP auth
 * @param {string}        token         - JWT Bearer token
 * @param {boolean}       isPushEnabled - Từ API /auth/me — admin đã bật chưa
 */
export default function PWANotificationManager({ userId, token, isPushEnabled }) {
  const [swReg,       setSwReg]       = useState(null)
  const [permission,  setPermission]  = useState(
    typeof Notification !== 'undefined' ? Notification.permission : 'default'
  )
  const [isSubscribed,  setIsSubscribed]  = useState(false)
  const [showBanner,    setShowBanner]    = useState(false)
  const [showPending,   setShowPending]   = useState(false)  // Chờ admin bật
  const [loading,       setLoading]       = useState(false)
  const [supported,     setSupported]     = useState(false)

  // ── Init ─────────────────────────────────────
  useEffect(() => {
    if (!isPushSupported()) return
    setSupported(true)
    initPWA()
  }, [])

  // Khi userId thay đổi (user vừa login), re-link subscription
  useEffect(() => {
    if (userId && isSubscribed) {
      relinkSubscription()
    }
  }, [userId])

  const initPWA = async () => {
    const reg = await registerServiceWorker()
    setSwReg(reg)
    if (!reg) return

    const existing = await reg.pushManager.getSubscription()
    if (existing) {
      setIsSubscribed(true)
      setPermission('granted')
      return
    }

    // Hiển thị banner nếu chưa dismiss
    const dismissed      = localStorage.getItem(STORAGE_KEY_DISMISSED)
    const dismissedAt    = dismissed ? parseInt(dismissed) : 0
    const daysSince      = (Date.now() - dismissedAt) / 86400000

    if (!dismissed || daysSince > 7) {
      setTimeout(() => {
        // Chỉ hiển thị nếu user đã login
        if (userId) setShowBanner(true)
      }, 3500)
    }
  }

  // Re-link subscription với userId thật (trường hợp subscribe khi chưa login)
  const relinkSubscription = async () => {
    if (!swReg) return
    const sub = await swReg.pushManager.getSubscription()
    if (!sub) return

    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    }
    await fetch(`${API_BASE}/api/push/subscribe`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        userId: String(userId),
        subscription: sub.toJSON(),
      }),
    })
    console.log('[PWA v2] Re-linked subscription to user', userId)
  }

  // ── Subscribe flow ────────────────────────────
  const subscribe = useCallback(async () => {
    if (!swReg) return
    setLoading(true)

    try {
      // 1. Xin quyền
      const permResult = await Notification.requestPermission()
      setPermission(permResult)
      if (permResult !== 'granted') { setShowBanner(false); return }

      // 2. VAPID key
      const vapidKey = await fetchVapidKey()
      if (!vapidKey) throw new Error('No VAPID key')

      // 3. Subscribe
      const subscription = await swReg.pushManager.subscribe({
        userVisibleOnly:      true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      })

      // 4. Save lên server với userId thật + JWT
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      }
      await fetch(`${API_BASE}/api/push/subscribe`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          userId:       String(userId || 'anonymous'),
          subscription: subscription.toJSON(),
        }),
      })

      // 5. Cache locally
      localStorage.setItem(STORAGE_KEY_SUB, JSON.stringify({
        userId:       String(userId),
        subscribedAt: Date.now(),
      }))

      setIsSubscribed(true)
      setShowBanner(false)

      // Nếu admin chưa bật push → hiện pending message
      if (!isPushEnabled) {
        setShowPending(true)
        setTimeout(() => setShowPending(false), 6000)
      }

      console.log('[PWA v2] ✅ Subscribed, userId:', userId)

    } catch (err) {
      console.error('[PWA v2] Subscribe error:', err)
    } finally {
      setLoading(false)
    }
  }, [swReg, userId, token, isPushEnabled])

  const dismissBanner = () => {
    localStorage.setItem(STORAGE_KEY_DISMISSED, Date.now().toString())
    setShowBanner(false)
  }

  const unsubscribe = async () => {
    if (!swReg) return
    const sub = await swReg.pushManager.getSubscription()
    if (sub) {
      await sub.unsubscribe()
      await fetch(`${API_BASE}/api/push/unsubscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: sub.endpoint }),
      })
    }
    localStorage.removeItem(STORAGE_KEY_SUB)
    setIsSubscribed(false)
  }

  // ── Render guards ─────────────────────────────
  if (!supported) return null
  if (!userId)    return null   // Chỉ hiện với logged-in user

  // ── Đã subscribe — hiện indicator nhỏ ─────────
  if (isSubscribed) {
    return (
      <>
        {/* Bell indicator */}
        <div
          title={isPushEnabled ? 'Thông báo đang hoạt động' : 'Chờ admin kích hoạt'}
          onClick={unsubscribe}
          style={{
            position:     'fixed',
            bottom:       '16px',
            right:        '16px',
            width:        '36px',
            height:       '36px',
            borderRadius: '50%',
            background:   isPushEnabled ? 'rgba(34,197,94,0.15)' : 'rgba(251,191,36,0.15)',
            border:       `1.5px solid ${isPushEnabled ? 'rgba(34,197,94,0.4)' : 'rgba(251,191,36,0.4)'}`,
            display:      'flex',
            alignItems:   'center',
            justifyContent: 'center',
            cursor:       'pointer',
            zIndex:       100,
            fontSize:     '16px',
          }}
        >
          {isPushEnabled ? '🔔' : '⏳'}
        </div>

        {/* Pending notification */}
        {showPending && (
          <div style={{
            position:     'fixed',
            bottom:       '62px',
            right:        '16px',
            background:   '#1e293b',
            border:       '1px solid rgba(251,191,36,0.4)',
            borderRadius: '10px',
            padding:      '12px 16px',
            fontSize:     '12px',
            color:        '#fbbf24',
            maxWidth:     '260px',
            zIndex:       100,
          }}>
            ⏳ Thiết bị đã đăng ký. Chờ admin kích hoạt tín hiệu cho tài khoản của bạn.
          </div>
        )}
      </>
    )
  }

  // ── Permission denied ─────────────────────────
  if (permission === 'denied') return null

  // ── Banner prompt ─────────────────────────────
  if (!showBanner) return null

  return (
    <div style={{
      position:   'fixed',
      bottom:     '0',
      left:       '0',
      right:      '0',
      zIndex:     9999,
      padding:    '0 16px 16px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
      <div style={{
        background:    'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        border:        '1px solid rgba(59,130,246,0.3)',
        borderRadius:  '16px',
        padding:       '20px',
        boxShadow:     '0 -4px 32px rgba(0,0,0,0.4)',
        display:       'flex',
        flexDirection: 'column',
        gap:           '14px',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div style={{ fontSize: '28px', lineHeight: 1, flexShrink: 0, marginTop: '2px' }}>🔔</div>
          <div style={{ flex: 1 }}>
            <div style={{ color: '#f1f5f9', fontSize: '16px', fontWeight: '700', marginBottom: '4px' }}>
              Bật thông báo tín hiệu
            </div>
            <div style={{ color: '#94a3b8', fontSize: '13px', lineHeight: '1.5' }}>
              Nhận ngay khi có tín hiệu{' '}
              <span style={{ color: '#4ade80', fontWeight: 600 }}>MUA</span> và{' '}
              <span style={{ color: '#f87171', fontWeight: 600 }}>BÁN</span>{' '}
              mới — kể cả khi app đang đóng.
            </div>
          </div>
        </div>

        {/* Chips */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            { icon: '🟢', label: 'Tín hiệu MUA mới',    color: '#4ade80' },
            { icon: '🔴', label: 'Tín hiệu BÁN / SL',   color: '#f87171' },
            { icon: '💰', label: 'Chốt lời đạt TP',     color: '#fbbf24' },
          ].map(({ icon, label, color }) => (
            <div key={label} style={{
              display:      'flex',
              alignItems:   'center',
              gap:          '5px',
              background:   'rgba(255,255,255,0.05)',
              borderRadius: '20px',
              padding:      '4px 10px',
              fontSize:     '12px',
              color,
            }}>
              <span>{icon}</span><span>{label}</span>
            </div>
          ))}
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={subscribe}
            disabled={loading}
            style={{
              flex:            1,
              background:      loading
                ? 'rgba(59,130,246,0.5)'
                : 'linear-gradient(135deg, #3b82f6, #2563eb)',
              color:           'white',
              border:          'none',
              borderRadius:    '10px',
              padding:         '12px',
              fontSize:        '14px',
              fontWeight:      '700',
              cursor:          loading ? 'not-allowed' : 'pointer',
              display:         'flex',
              alignItems:      'center',
              justifyContent:  'center',
              gap:             '6px',
            }}
          >
            {loading ? '⏳ Đang kích hoạt...' : '🔔 Bật Thông Báo'}
          </button>
          <button
            onClick={dismissBanner}
            style={{
              background:   'rgba(255,255,255,0.05)',
              color:        '#64748b',
              border:       '1px solid rgba(255,255,255,0.08)',
              borderRadius: '10px',
              padding:      '12px 14px',
              fontSize:     '13px',
              cursor:       'pointer',
              whiteSpace:   'nowrap',
            }}
          >
            Để Sau
          </button>
        </div>

        <p style={{ color: '#475569', fontSize: '11px', margin: 0, textAlign: 'center' }}>
          Chỉ gửi tín hiệu VIP. Không spam. Tắt bất cứ lúc nào.
        </p>
      </div>
    </div>
  )
}
