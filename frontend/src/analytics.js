/**
 * AI ADVISOR — GA4 Analytics Helper
 * File: src/analytics.js
 *
 * Import vào bất kỳ component nào:
 *   import { track } from '../analytics'
 *   track('event_name', { param1: value1 })
 */

export function track(eventName, params = {}) {
  try {
    if (typeof window.gtag === 'function') {
      window.gtag('event', eventName, {
        ...params,
        app_version: '3.3',
      })
    }
  } catch (e) { /* silent — không bao giờ crash app */ }
}

/**
 * ═══════════════════════════════════════════════
 * EVENT CATALOG — toàn bộ events đang track
 * ═══════════════════════════════════════════════
 *
 * ── AUTH (App.jsx) ──────────────────────────────
 * login                { user_tier, is_vip }
 * session_restore      { user_tier }
 * logout               { user_tier }
 *
 * ── NAVIGATION (App.jsx) ────────────────────────
 * tab_view             { tab_name, user_tier }
 * upgrade_click        { source, user_tier, days_left? }
 *
 * ── IIS (IISTest.jsx) ────────────────────────────
 * iis_modal_shown      { user_tier, trigger }
 * iis_modal_skipped    { user_tier }
 * iis_test_started     { user_tier }
 * iis_test_completed   { iis_score, iis_level, iis_method, user_tier }
 * iis_result_viewed    { iis_score, iis_level, user_tier }
 * iis_retest_started   { prev_score, user_tier }
 *
 * ── AI CHAT (AIPortfolioManager.jsx) ────────────
 * ai_chat_sent         { user_tier, emotion_detected, has_iis, tab_context }
 * ai_chat_error        { user_tier, error_type }
 * ai_quick_question    { question_preview, user_tier }
 *
 * ── PORTFOLIO (AIPortfolioManager.jsx) ──────────
 * portfolio_stock_add  { ticker, user_tier }
 * portfolio_stock_del  { ticker, user_tier }
 * portfolio_cash_set   { user_tier }
 *
 * ── SIGNALS (SignalsModule.jsx) ──────────────────
 * signals_tab_view     { tab, signal_count, user_tier }
 * signals_refresh      { user_tier, trigger }
 */
