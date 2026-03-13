// ============================================
// AI Advisor — GA4 Analytics Utility
// File: src/analytics.js
// ============================================
// Thay G-XXXXXXXXXX bằng Measurement ID thật của bạn
const GA_MEASUREMENT_ID = 'G-00979J51RB'

// ── Initialize GA4 ──────────────────────────
export const initGA = () => {
  // Inject gtag script
  const script1 = document.createElement('script')
  script1.async = true
  script1.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`
  document.head.appendChild(script1)

  // Init dataLayer
  window.dataLayer = window.dataLayer || []
  window.gtag = function () { window.dataLayer.push(arguments) }
  window.gtag('js', new Date())
  window.gtag('config', GA_MEASUREMENT_ID, {
    // Ẩn thông tin nhạy cảm
    anonymize_ip: true,
    // Tắt auto page_view vì React SPA tự handle
    send_page_view: false,
  })

  console.log('✅ GA4 initialized:', GA_MEASUREMENT_ID)
}

// ── Page View ───────────────────────────────
// Gọi mỗi khi user chuyển trang/tab
export const trackPageView = (pageName) => {
  if (!window.gtag) return
  window.gtag('event', 'page_view', {
    page_title: pageName,
    page_location: window.location.href,
  })
}

// ── User Login ──────────────────────────────
// Gọi khi user đăng nhập thành công
// → Biết được ai đang active và tần suất login
export const trackLogin = (userId, userName) => {
  if (!window.gtag) return
  // Set user ID để track individual users
  window.gtag('config', GA_MEASUREMENT_ID, {
    user_id: userId,
  })
  window.gtag('event', 'login', {
    method: 'email',
    user_id: userId,
    user_name: userName,
  })
}

// ── Tab Navigation ──────────────────────────
// Gọi khi user click tab Signals hoặc Portfolio
// → Biết feature nào được dùng nhiều hơn
export const trackTabView = (tabName) => {
  if (!window.gtag) return
  window.gtag('event', 'tab_view', {
    tab_name: tabName,           // 'signals' | 'portfolio'
    page_title: `Tab: ${tabName}`,
  })
  // Cũng track như page view để thấy trong GA4 reports
  trackPageView(`Tab: ${tabName}`)
}

// ── Signal Tab View ─────────────────────────
// Gọi khi user click tab MUA / BÁN trong SignalsModule
export const trackSignalTabView = (tabName) => {
  if (!window.gtag) return
  window.gtag('event', 'signal_tab_view', {
    tab_name: tabName,           // 'buy' | 'sell'
  })
}

// ── Signal Click ────────────────────────────
// Gọi khi user click vào 1 signal cụ thể
// → Biết signal nào được quan tâm nhất
export const trackSignalClick = (ticker, action, confidence) => {
  if (!window.gtag) return
  window.gtag('event', 'signal_click', {
    ticker: ticker,              // VD: 'VCB', 'VNM'
    action: action,              // 'buy' | 'sell'
    confidence_score: confidence, // 0-100
  })
}

// ── Signal View (Impression) ─────────────────
// Gọi khi danh sách signals load xong
// → Biết user có thấy signals không (khác với click)
export const trackSignalsLoaded = (signalCount) => {
  if (!window.gtag) return
  window.gtag('event', 'signals_loaded', {
    signal_count: signalCount,
  })
}

// ── Portfolio Interact ───────────────────────
// Gọi khi user tương tác với AI Portfolio Manager
// → Biết feature bị "chôn" có ai dùng không
export const trackPortfolioAction = (actionType) => {
  if (!window.gtag) return
  window.gtag('event', 'portfolio_interact', {
    action_type: actionType,     // 'add_stock' | 'analyze' | 'chat' | 'view_risk'
  })
}

// ── Market Risk View ─────────────────────────
// Gọi khi user mở Market Risk dashboard
export const trackMarketRiskView = () => {
  if (!window.gtag) return
  window.gtag('event', 'market_risk_view', {
    page_title: 'Market Risk Dashboard',
  })
}

// ── Refresh Signals ──────────────────────────
// Gọi khi user bấm refresh signals thủ công
// → User chủ động = engaged user
export const trackSignalRefresh = () => {
  if (!window.gtag) return
  window.gtag('event', 'signal_refresh', {
    trigger: 'manual',
  })
}

// ── Error Tracking ───────────────────────────
// Gọi khi có lỗi API hoặc lỗi quan trọng
export const trackError = (errorType, errorMessage) => {
  if (!window.gtag) return
  window.gtag('event', 'app_error', {
    error_type: errorType,
    error_message: errorMessage,
  })
}
