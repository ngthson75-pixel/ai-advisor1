/**
 * VIPDashboard.jsx
 * AI Advisor — VIP Premium Dashboard
 * Màu chủ đạo: Tím / ánh tím luxury
 * 
 * Cách dùng trong App.jsx:
 *   import VIPDashboard from './components/VIPDashboard'
 *   // Route: /vip hoặc render khi user.tier === 'vip' || 'pro'
 *   {user?.tier === 'vip' && <VIPDashboard user={user} token={token} />}
 * 
 * API cần có:
 *   GET /api/vip/signals          → VIP signals (VN30 filtered)
 *   GET /api/vip/signals/history  → Signal history
 *   POST /api/vip/signals/scan    → Trigger manual scan
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';

// ─── CONSTANTS ────────────────────────────────────────────────────────────────

const API_BASE = import.meta.env?.VITE_API_URL || 'https://ai-advisor1-backend.onrender.com/api';

const VN30_LIST = [
  'ACB','BCM','BID','BVH','CTG','FPT','GAS','GVR','HDB','HPG',
  'MBB','MSN','MWG','PLX','POW','SAB','SHB','SSB','SSI','STB',
  'TCB','TPB','VCB','VHM','VIB','VIC','VJC','VNM','VPB','VRE'
];

const PURPLE = {
  950: '#1a0533',
  900: '#2d0a5e',
  800: '#3d1278',
  700: '#5b21b6',
  600: '#7c3aed',
  500: '#8b5cf6',
  400: '#a78bfa',
  300: '#c4b5fd',
  200: '#ddd6fe',
  100: '#ede9fe',
  50:  '#f5f3ff',
};

const GOLD = '#d4a843';
const GOLD_LIGHT = '#f0c060';
const GREEN  = '#10b981';
const RED    = '#ef4444';
const ORANGE = '#f59e0b';
const DARK   = '#0d0118';

// ─── STYLES ───────────────────────────────────────────────────────────────────

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

  .vip-root {
    font-family: 'Sora', sans-serif;
    background: #0d0118;
    min-height: 100vh;
    color: #e2d9f3;
    position: relative;
    overflow-x: hidden;
  }

  /* Ambient background orbs */
  .vip-root::before {
    content: '';
    position: fixed;
    top: -20%;
    left: -10%;
    width: 60vw;
    height: 60vw;
    background: radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }
  .vip-root::after {
    content: '';
    position: fixed;
    bottom: -20%;
    right: -10%;
    width: 50vw;
    height: 50vw;
    background: radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }

  .vip-content { position: relative; z-index: 1; }

  /* ── HEADER ── */
  .vip-header {
    background: linear-gradient(135deg, rgba(45,10,94,0.95) 0%, rgba(29,7,53,0.98) 100%);
    border-bottom: 1px solid rgba(139,92,246,0.25);
    padding: 0 24px;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(20px);
  }
  .vip-header-inner {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
  }
  .vip-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 18px;
    font-weight: 700;
    color: #c4b5fd;
    text-decoration: none;
  }
  .vip-badge {
    background: linear-gradient(135deg, #7c3aed, #a78bfa);
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .vip-user-chip {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(139,92,246,0.12);
    border: 1px solid rgba(139,92,246,0.25);
    border-radius: 40px;
    padding: 6px 14px;
    font-size: 13px;
    color: #c4b5fd;
  }
  .vip-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed, #a78bfa);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    color: white;
  }
  .vip-live-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
    animation: pulse-dot 2s infinite;
  }
  @keyframes pulse-dot {
    0%,100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.5; transform: scale(1.4); }
  }

  /* ── HERO BANNER ── */
  .vip-hero {
    background: linear-gradient(135deg, #1a0533 0%, #2d0a5e 50%, #1a0533 100%);
    border-bottom: 1px solid rgba(139,92,246,0.2);
    padding: 32px 24px;
    position: relative;
    overflow: hidden;
  }
  .vip-hero::before {
    content: '👑';
    position: absolute;
    right: 40px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 120px;
    opacity: 0.06;
    pointer-events: none;
  }
  .vip-hero-inner {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    flex-wrap: wrap;
  }
  .vip-hero-title {
    font-size: 26px;
    font-weight: 800;
    background: linear-gradient(135deg, #c4b5fd 0%, #a78bfa 50%, ${GOLD_LIGHT} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 6px;
  }
  .vip-hero-sub {
    color: #9d8cba;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* ── STATS ROW ── */
  .vip-stats {
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px 24px 0;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
  }
  .vip-stat-card {
    background: linear-gradient(135deg, rgba(45,10,94,0.6) 0%, rgba(29,7,53,0.8) 100%);
    border: 1px solid rgba(139,92,246,0.2);
    border-radius: 16px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
  }
  .vip-stat-card:hover {
    border-color: rgba(139,92,246,0.5);
    transform: translateY(-2px);
  }
  .vip-stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(139,92,246,0.6), transparent);
  }
  .vip-stat-icon { font-size: 22px; margin-bottom: 10px; }
  .vip-stat-value {
    font-size: 28px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
    margin-bottom: 4px;
  }
  .vip-stat-label { font-size: 12px; color: #9d8cba; font-weight: 500; }
  .vip-stat-sub { font-size: 11px; color: #6b5a8a; margin-top: 4px; }

  /* ── MAIN LAYOUT ── */
  .vip-main {
    max-width: 1400px;
    margin: 24px auto;
    padding: 0 24px 60px;
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 24px;
  }
  @media (max-width: 1024px) {
    .vip-main { grid-template-columns: 1fr; }
  }

  /* ── TABS ── */
  .vip-tabs {
    display: flex;
    gap: 6px;
    background: rgba(29,7,53,0.8);
    border: 1px solid rgba(139,92,246,0.2);
    border-radius: 14px;
    padding: 6px;
    margin-bottom: 20px;
  }
  .vip-tab {
    flex: 1;
    padding: 10px 16px;
    border: none;
    border-radius: 10px;
    background: transparent;
    color: #9d8cba;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'Sora', sans-serif;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }
  .vip-tab.active-buy {
    background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.1));
    color: #10b981;
    border: 1px solid rgba(16,185,129,0.3);
  }
  .vip-tab.active-sell {
    background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.1));
    color: #ef4444;
    border: 1px solid rgba(239,68,68,0.3);
  }
  .vip-tab:hover:not(.active-buy):not(.active-sell) {
    background: rgba(139,92,246,0.1);
    color: #c4b5fd;
  }
  .vip-tab-count {
    background: rgba(139,92,246,0.25);
    color: #c4b5fd;
    font-size: 11px;
    padding: 1px 7px;
    border-radius: 10px;
    font-weight: 700;
  }

  /* ── SECTION HEADER ── */
  .vip-section-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }
  .vip-section-title {
    font-size: 16px;
    font-weight: 700;
    color: #c4b5fd;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .vip-section-title .vn30-badge {
    font-size: 10px;
    font-weight: 700;
    background: linear-gradient(135deg, #7c3aed, #a78bfa);
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    letter-spacing: 0.05em;
  }

  /* ── SIGNAL CARD ── */
  .vip-signal-card {
    background: linear-gradient(135deg, rgba(45,10,94,0.5) 0%, rgba(20,5,40,0.8) 100%);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 14px;
    transition: all 0.25s;
    position: relative;
    overflow: hidden;
    cursor: pointer;
  }
  .vip-signal-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px;
    height: 100%;
    border-radius: 3px 0 0 3px;
  }
  .vip-signal-card.buy::before  { background: linear-gradient(180deg, #10b981, #059669); }
  .vip-signal-card.sell::before { background: linear-gradient(180deg, #ef4444, #dc2626); }
  .vip-signal-card:hover {
    border-color: rgba(139,92,246,0.45);
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(124,58,237,0.15);
  }
  .vip-signal-card.expanded {
    border-color: rgba(139,92,246,0.5);
  }

  .vip-signal-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }
  .vip-signal-ticker {
    font-size: 22px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    color: white;
    letter-spacing: -0.02em;
  }
  .vip-vn30-star {
    font-size: 13px;
    background: linear-gradient(135deg, rgba(212,168,67,0.2), rgba(212,168,67,0.1));
    border: 1px solid rgba(212,168,67,0.4);
    color: ${GOLD_LIGHT};
    padding: 2px 8px;
    border-radius: 8px;
    font-weight: 600;
  }
  .vip-signal-action-badge {
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.05em;
  }
  .buy-badge  { background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.4); color: #10b981; }
  .sell-badge { background: rgba(239,68,68,0.15);  border: 1px solid rgba(239,68,68,0.4);  color: #ef4444; }

  .vip-signal-prices {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 14px 0;
  }
  .vip-price-item {
    background: rgba(139,92,246,0.06);
    border: 1px solid rgba(139,92,246,0.12);
    border-radius: 10px;
    padding: 10px 12px;
  }
  .vip-price-label { font-size: 10px; color: #9d8cba; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
  .vip-price-val {
    font-size: 15px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: white;
  }
  .vip-price-val.entry  { color: #a78bfa; }
  .vip-price-val.sl     { color: #ef4444; }
  .vip-price-val.tp     { color: #10b981; }

  .vip-signal-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 12px;
  }
  .vip-chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .vip-chip {
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid;
  }
  .chip-strategy { background: rgba(139,92,246,0.1); border-color: rgba(139,92,246,0.3); color: #c4b5fd; }
  .chip-rr  { background: rgba(212,168,67,0.1);  border-color: rgba(212,168,67,0.3);  color: ${GOLD_LIGHT}; }
  .chip-vn30 { background: rgba(212,168,67,0.15); border-color: rgba(212,168,67,0.4); color: ${GOLD_LIGHT}; font-weight: 700; }
  .chip-conf { background: rgba(16,185,129,0.1);  border-color: rgba(16,185,129,0.3); color: #10b981; }
  .chip-conf.med { background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.3); color: #f59e0b; }
  .chip-conf.low { background: rgba(239,68,68,0.1);  border-color: rgba(239,68,68,0.3);  color: #ef4444; }

  .vip-signal-time { font-size: 11px; color: #6b5a8a; }

  /* Expanded detail */
  .vip-signal-detail {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid rgba(139,92,246,0.15);
    animation: slideDown 0.2s ease;
  }
  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .vip-signal-reason {
    font-size: 13px;
    color: #b8a8d8;
    line-height: 1.7;
    background: rgba(139,92,246,0.05);
    border-left: 2px solid rgba(139,92,246,0.4);
    padding: 10px 14px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 12px;
  }

  /* ── CONFIDENCE BAR ── */
  .conf-bar-wrap { margin-bottom: 12px; }
  .conf-bar-label { display: flex; justify-content: space-between; font-size: 12px; color: #9d8cba; margin-bottom: 6px; }
  .conf-bar-track {
    height: 6px;
    background: rgba(139,92,246,0.1);
    border-radius: 4px;
    overflow: hidden;
  }
  .conf-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.8s ease;
  }

  /* ── RIGHT PANEL ── */
  .vip-panel {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .vip-panel-card {
    background: linear-gradient(135deg, rgba(45,10,94,0.5) 0%, rgba(20,5,40,0.8) 100%);
    border: 1px solid rgba(139,92,246,0.2);
    border-radius: 16px;
    padding: 20px;
  }
  .vip-panel-title {
    font-size: 14px;
    font-weight: 700;
    color: #c4b5fd;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(139,92,246,0.15);
  }

  /* VN30 grid */
  .vn30-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .vn30-ticker {
    font-size: 11px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    padding: 4px 8px;
    border-radius: 6px;
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.15);
    color: #9d8cba;
    transition: all 0.2s;
  }
  .vn30-ticker.has-signal {
    background: linear-gradient(135deg, rgba(212,168,67,0.15), rgba(212,168,67,0.08));
    border-color: rgba(212,168,67,0.4);
    color: ${GOLD_LIGHT};
    box-shadow: 0 0 8px rgba(212,168,67,0.1);
  }
  .vn30-ticker.has-signal.buy-signal { background: rgba(16,185,129,0.12); border-color: rgba(16,185,129,0.35); color: #10b981; }
  .vn30-ticker.has-signal.sell-signal { background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.35); color: #ef4444; }

  /* Telegram status */
  .tg-status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid rgba(139,92,246,0.1);
    font-size: 13px;
  }
  .tg-status-row:last-child { border-bottom: none; }
  .tg-status-label { color: #9d8cba; }
  .tg-status-val { color: #c4b5fd; font-weight: 600; }
  .tg-connected { color: #10b981; display: flex; align-items: center; gap: 6px; }
  .tg-disconnected { color: #6b5a8a; }

  /* ── BUTTONS ── */
  .vip-btn-refresh {
    padding: 9px 18px;
    background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(139,92,246,0.15));
    border: 1px solid rgba(139,92,246,0.4);
    color: #c4b5fd;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 7px;
    transition: all 0.2s;
    font-family: 'Sora', sans-serif;
  }
  .vip-btn-refresh:hover { background: rgba(139,92,246,0.3); border-color: rgba(139,92,246,0.6); color: white; }
  .vip-btn-refresh:disabled { opacity: 0.5; cursor: not-allowed; }

  .vip-btn-scan {
    padding: 9px 18px;
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    border: none;
    color: white;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 7px;
    transition: all 0.2s;
    font-family: 'Sora', sans-serif;
    box-shadow: 0 4px 16px rgba(124,58,237,0.3);
  }
  .vip-btn-scan:hover  { background: linear-gradient(135deg, #8b5cf6, #7c3aed); box-shadow: 0 6px 24px rgba(124,58,237,0.45); }
  .vip-btn-scan:disabled { opacity: 0.5; cursor: not-allowed; }

  /* ── EMPTY STATE ── */
  .vip-empty {
    text-align: center;
    padding: 60px 24px;
    color: #6b5a8a;
  }
  .vip-empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }
  .vip-empty-title { font-size: 16px; font-weight: 600; color: #9d8cba; margin-bottom: 8px; }
  .vip-empty-sub { font-size: 13px; line-height: 1.6; }

  /* ── LOADING ── */
  .vip-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 24px;
    gap: 16px;
    color: #9d8cba;
    font-size: 14px;
  }
  .vip-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(139,92,246,0.15);
    border-top-color: #8b5cf6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── TOAST ── */
  .vip-toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: linear-gradient(135deg, rgba(45,10,94,0.98), rgba(29,7,53,0.98));
    border: 1px solid rgba(139,92,246,0.4);
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 14px;
    color: #c4b5fd;
    z-index: 9999;
    animation: toastIn 0.3s ease;
    backdrop-filter: blur(20px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    max-width: 320px;
  }
  @keyframes toastIn {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── DISCLAIMER ── */
  .vip-disclaimer {
    max-width: 1400px;
    margin: 0 auto 0;
    padding: 0 24px 40px;
  }
  .vip-disclaimer-inner {
    background: rgba(239,68,68,0.04);
    border: 1px solid rgba(239,68,68,0.15);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 12px;
    color: #6b5a8a;
    line-height: 1.6;
  }
  .vip-disclaimer-inner strong { color: #9d8cba; }

  /* ── SCROLL ── */
  .vip-signals-list { max-height: 72vh; overflow-y: auto; padding-right: 4px; }
  .vip-signals-list::-webkit-scrollbar { width: 4px; }
  .vip-signals-list::-webkit-scrollbar-track { background: transparent; }
  .vip-signals-list::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.3); border-radius: 4px; }

  /* ── MOBILE ── */
  @media (max-width: 640px) {
    .vip-hero::before { display: none; }
    .vip-signal-prices { grid-template-columns: repeat(3,1fr); gap: 6px; }
    .vip-price-val { font-size: 13px; }
  }

  .spin-anim { animation: spin 0.8s linear infinite; }
`;

// ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

const fmt = (n) => n ? Number(n).toLocaleString('vi-VN') : '—';
const fmtTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString('vi-VN', { day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit' });
};
const isVN30 = (ticker) => VN30_LIST.includes((ticker || '').toUpperCase().trim());

const getConfColor = (conf) => {
  if (conf >= 70) return '#10b981';
  if (conf >= 50) return '#f59e0b';
  return '#ef4444';
};
const getConfClass = (conf) => {
  if (conf >= 70) return 'chip-conf';
  if (conf >= 50) return 'chip-conf med';
  return 'chip-conf low';
};

// ─── SUBCOMPONENTS ────────────────────────────────────────────────────────────

function ConfBar({ value }) {
  const color = getConfColor(value);
  return (
    <div className="conf-bar-wrap">
      <div className="conf-bar-label">
        <span>Độ tin cậy</span>
        <span style={{ color, fontWeight: 700 }}>{value}%</span>
      </div>
      <div className="conf-bar-track">
        <div className="conf-bar-fill" style={{ width: `${value}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }} />
      </div>
    </div>
  );
}

function SignalCard({ signal, onExpand, expanded }) {
  const isBuy  = signal.action === 'BUY' || !signal.action;
  const inVN30 = isVN30(signal.ticker);
  const conf   = signal.confidence || signal.strength || 0;

  return (
    <div
      className={`vip-signal-card ${isBuy ? 'buy' : 'sell'} ${expanded ? 'expanded' : ''}`}
      onClick={onExpand}
    >
      {/* Top row */}
      <div className="vip-signal-top">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="vip-signal-ticker">{signal.ticker}</span>
            {inVN30 && <span className="vip-vn30-star">⭐ VN30</span>}
          </div>
          <div style={{ fontSize: '12px', color: '#9d8cba' }}>
            {signal.strategy_type || signal.strategy || 'EMA Cross / Pullback'}
          </div>
        </div>
        <span className={`vip-signal-action-badge ${isBuy ? 'buy-badge' : 'sell-badge'}`}>
          {isBuy ? '▲ MUA' : '▼ BÁN'}
        </span>
      </div>

      {/* Prices */}
      <div className="vip-signal-prices">
        <div className="vip-price-item">
          <div className="vip-price-label">Giá vào</div>
          <div className="vip-price-val entry">{fmt(signal.entry_price)}</div>
        </div>
        <div className="vip-price-item">
          <div className="vip-price-label">Cắt lỗ</div>
          <div className="vip-price-val sl">{fmt(signal.stop_loss)}</div>
        </div>
        <div className="vip-price-item">
          <div className="vip-price-label">Chốt lời</div>
          <div className="vip-price-val tp">{fmt(signal.take_profit)}</div>
        </div>
      </div>

      {/* Footer chips */}
      <div className="vip-signal-footer">
        <div className="vip-chips">
          {inVN30 && <span className="vip-chip chip-vn30">VN30</span>}
          {signal.strategy_type && <span className="vip-chip chip-strategy">{signal.strategy_type}</span>}
          {signal.rr_ratio && <span className="vip-chip chip-rr">R/R {Number(signal.rr_ratio).toFixed(1)}x</span>}
          {conf > 0 && <span className={`vip-chip ${getConfClass(conf)}`}>{conf}%</span>}
        </div>
        <span className="vip-signal-time">{fmtTime(signal.created_at || signal.timestamp)}</span>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="vip-signal-detail">
          <ConfBar value={conf} />
          {signal.reasoning && (
            <div className="vip-signal-reason">💡 {signal.reasoning}</div>
          )}
          {signal.rsi && (
            <div style={{ fontSize: '12px', color: '#9d8cba', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
              {signal.rsi     && <span>RSI: <strong style={{ color: '#c4b5fd' }}>{Number(signal.rsi).toFixed(1)}</strong></span>}
              {signal.ema20   && <span>EMA20: <strong style={{ color: '#c4b5fd' }}>{fmt(signal.ema20)}</strong></span>}
              {signal.ema50   && <span>EMA50: <strong style={{ color: '#c4b5fd' }}>{fmt(signal.ema50)}</strong></span>}
              {signal.risk_pct   && <span>Risk: <strong style={{ color: '#ef4444' }}>-{signal.risk_pct}%</strong></span>}
              {signal.reward_pct && <span>Reward: <strong style={{ color: '#10b981' }}>+{signal.reward_pct}%</strong></span>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function VN30Panel({ signals }) {
  const signalMap = {};
  signals.forEach(s => {
    if (isVN30(s.ticker)) signalMap[s.ticker] = s.action === 'BUY' || !s.action ? 'buy' : 'sell';
  });

  return (
    <div className="vip-panel-card">
      <div className="vip-panel-title">
        <span>⭐</span>
        <span>Radar VN30</span>
        <span style={{ marginLeft: 'auto', fontSize: '11px', color: '#6b5a8a', fontWeight: 400 }}>{Object.keys(signalMap).length} có tín hiệu</span>
      </div>
      <div className="vn30-grid">
        {VN30_LIST.map(t => {
          const action = signalMap[t];
          return (
            <span key={t} className={`vn30-ticker ${action ? `has-signal ${action}-signal` : ''}`}>
              {t}
            </span>
          );
        })}
      </div>
      <div style={{ marginTop: '12px', display: 'flex', gap: '12px', fontSize: '11px', color: '#6b5a8a' }}>
        <span>🟢 MUA</span>
        <span>🔴 BÁN</span>
        <span style={{ color: '#4a3a6a' }}>⬜ Không có tín hiệu</span>
      </div>
    </div>
  );
}

function TelegramPanel({ user }) {
  const hasTg = !!(user?.telegram_chat_id);
  return (
    <div className="vip-panel-card">
      <div className="vip-panel-title">
        <span>✈️</span>
        <span>Telegram Notification</span>
      </div>
      <div className="tg-status-row">
        <span className="tg-status-label">Trạng thái</span>
        <span className={hasTg ? 'tg-connected' : 'tg-disconnected'}>
          {hasTg ? <><span>●</span> Đã kết nối</> : '✕ Chưa kết nối'}
        </span>
      </div>
      {hasTg && (
        <div className="tg-status-row">
          <span className="tg-status-label">Chat ID</span>
          <span className="tg-status-val" style={{ fontFamily: 'JetBrains Mono', fontSize: '12px' }}>
            {user.telegram_chat_id}
          </span>
        </div>
      )}
      <div className="tg-status-row">
        <span className="tg-status-label">Nhận tín hiệu</span>
        <span className="tg-status-val">{hasTg ? 'Tự động' : '—'}</span>
      </div>
      {!hasTg && (
        <div style={{ marginTop: '12px', padding: '12px', background: 'rgba(139,92,246,0.08)', borderRadius: '10px', fontSize: '12px', color: '#9d8cba', lineHeight: 1.6 }}>
          💬 Liên hệ admin để kết nối Telegram và nhận tín hiệu VIP ngay lập tức khi thị trường mở.
        </div>
      )}
    </div>
  );
}

function FilterPanel({ filters, setFilters, signalCount }) {
  return (
    <div className="vip-panel-card">
      <div className="vip-panel-title">
        <span>🔧</span>
        <span>Bộ lọc VIP</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px', color: '#b8a8d8', cursor: 'pointer' }}>
          <span>⭐ Chỉ VN30</span>
          <input
            type="checkbox"
            checked={filters.vn30Only}
            onChange={e => setFilters(f => ({ ...f, vn30Only: e.target.checked }))}
            style={{ accentColor: '#8b5cf6', width: 16, height: 16, cursor: 'pointer' }}
          />
        </label>
        <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px', color: '#b8a8d8', cursor: 'pointer' }}>
          <span>📊 Độ tin cậy ≥ 70%</span>
          <input
            type="checkbox"
            checked={filters.highConfOnly}
            onChange={e => setFilters(f => ({ ...f, highConfOnly: e.target.checked }))}
            style={{ accentColor: '#8b5cf6', width: 16, height: 16, cursor: 'pointer' }}
          />
        </label>
        <div style={{ fontSize: '11px', color: '#6b5a8a', paddingTop: '8px', borderTop: '1px solid rgba(139,92,246,0.1)' }}>
          Đang hiển thị <strong style={{ color: '#c4b5fd' }}>{signalCount}</strong> tín hiệu
        </div>
      </div>
    </div>
  );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export default function VIPDashboard({ user, token }) {
  const [signals,     setSignals]     = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState(null);
  const [scanning,    setScanning]    = useState(false);
  const [activeTab,   setActiveTab]   = useState('buy');
  const [expandedId,  setExpandedId]  = useState(null);
  const [toast,       setToast]       = useState(null);
  const [lastUpdate,  setLastUpdate]  = useState(null);
  const [filters,     setFilters]     = useState({ vn30Only: false, highConfOnly: false });
  const toastTimer = useRef(null);

  const showToast = useCallback((msg) => {
    setToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3500);
  }, []);

  const fetchSignals = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const res  = await fetch(`${API_BASE}/vip/signals`, { headers });
      const data = await res.json();
      if (data.success) {
        setSignals(data.signals || []);
        setLastUpdate(new Date());
      } else {
        // Fallback: load regular signals and filter VN30
        const res2  = await fetch(`${API_BASE}/signals`);
        const data2 = await res2.json();
        if (data2.success) {
          const vipFiltered = (data2.signals || []).filter(s => {
            const conf = s.confidence || s.strength || 0;
            return isVN30(s.ticker) || conf >= 70;
          });
          setSignals(vipFiltered);
          setLastUpdate(new Date());
        } else {
          setError('Không thể tải tín hiệu VIP');
        }
      }
    } catch (err) {
      // Try fallback
      try {
        const res2  = await fetch(`${API_BASE}/signals`);
        const data2 = await res2.json();
        if (data2.success) {
          const vipFiltered = (data2.signals || []).filter(s => isVN30(s.ticker) || (s.confidence || 0) >= 65);
          setSignals(vipFiltered);
          setLastUpdate(new Date());
        }
      } catch { setError('Lỗi kết nối server'); }
    } finally {
      setLoading(false);
    }
  }, [token]);

  const triggerScan = async () => {
    try {
      setScanning(true);
      showToast('⏳ Đang quét tín hiệu VIP... (~2-3 phút)');
      const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
      const res  = await fetch(`${API_BASE}/vip/signals/scan`, { method: 'POST', headers });
      const data = await res.json();
      if (data.success) {
        showToast('✅ Đang quét! Tự động refresh sau 3 phút.');
        setTimeout(fetchSignals, 180000);
      } else {
        showToast('⚠️ Quét thất bại, thử lại sau.');
      }
    } catch {
      showToast('⚠️ Lỗi khi gửi lệnh quét.');
    } finally {
      setScanning(false);
    }
  };

  useEffect(() => { fetchSignals(); }, [fetchSignals]);

  // Auto-refresh mỗi 5 phút
  useEffect(() => {
    const timer = setInterval(fetchSignals, 5 * 60 * 1000);
    return () => clearInterval(timer);
  }, [fetchSignals]);

  // Compute display signals
  const buySignals  = signals.filter(s => s.action === 'BUY' || !s.action);
  const sellSignals = signals.filter(s => s.action === 'SELL');
  const vn30Signals = signals.filter(s => isVN30(s.ticker));

  let displaySignals = activeTab === 'buy' ? buySignals : sellSignals;
  if (filters.vn30Only)     displaySignals = displaySignals.filter(s => isVN30(s.ticker));
  if (filters.highConfOnly) displaySignals = displaySignals.filter(s => (s.confidence || s.strength || 0) >= 70);

  const userInitial = (user?.full_name || user?.email || 'V').charAt(0).toUpperCase();

  return (
    <>
      <style>{css}</style>
      <div className="vip-root">
        <div className="vip-content">

          {/* ── HEADER ── */}
          <header className="vip-header">
            <div className="vip-header-inner">
              <div className="vip-logo">
                <span>👑</span>
                <span>AI Advisor</span>
                <span className="vip-badge">VIP</span>
              </div>
              <div className="vip-user-chip">
                <div className="vip-live-dot" />
                <div className="vip-avatar">{userInitial}</div>
                <span>{user?.full_name || user?.email || 'VIP Member'}</span>
              </div>
            </div>
          </header>

          {/* ── HERO ── */}
          <div className="vip-hero">
            <div className="vip-hero-inner">
              <div>
                <div className="vip-hero-title">👑 VIP Signal Dashboard</div>
                <div className="vip-hero-sub">
                  <span>🔵 VN30 · EMA Cross · Pullback</span>
                  <span style={{ color: '#4a3a6a' }}>•</span>
                  {lastUpdate && <span>Cập nhật: {fmtTime(lastUpdate.toISOString())}</span>}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button className="vip-btn-refresh" onClick={fetchSignals} disabled={loading}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className={loading ? 'spin-anim' : ''}>
                    <path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
                  </svg>
                  Refresh
                </button>
                <button className="vip-btn-scan" onClick={triggerScan} disabled={scanning}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className={scanning ? 'spin-anim' : ''}>
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                  </svg>
                  {scanning ? 'Đang quét...' : 'Quét VN30'}
                </button>
              </div>
            </div>
          </div>

          {/* ── STATS ── */}
          <div className="vip-stats">
            {[
              { icon: '⭐', val: vn30Signals.length,  label: 'VN30 có tín hiệu', sub: `/ ${VN30_LIST.length} mã`, color: GOLD_LIGHT },
              { icon: '📈', val: buySignals.length,   label: 'Tín hiệu MUA',     sub: 'Đang theo dõi', color: '#10b981' },
              { icon: '📉', val: sellSignals.length,  label: 'Tín hiệu BÁN',     sub: 'Chú ý cắt lỗ',  color: '#ef4444' },
              { icon: '🎯', val: signals.filter(s => (s.confidence || s.strength || 0) >= 70).length, label: 'Độ tin cậy cao', sub: '≥ 70%', color: '#8b5cf6' },
            ].map((s, i) => (
              <div key={i} className="vip-stat-card">
                <div className="vip-stat-icon">{s.icon}</div>
                <div className="vip-stat-value" style={{ color: s.color }}>{s.val}</div>
                <div className="vip-stat-label">{s.label}</div>
                <div className="vip-stat-sub">{s.sub}</div>
              </div>
            ))}
          </div>

          {/* ── MAIN ── */}
          <div className="vip-main">

            {/* LEFT — Signals */}
            <div>
              {/* Tabs */}
              <div className="vip-tabs">
                <button
                  className={`vip-tab ${activeTab === 'buy' ? 'active-buy' : ''}`}
                  onClick={() => setActiveTab('buy')}
                >
                  📈 Tín hiệu MUA
                  <span className="vip-tab-count">{buySignals.length}</span>
                </button>
                <button
                  className={`vip-tab ${activeTab === 'sell' ? 'active-sell' : ''}`}
                  onClick={() => setActiveTab('sell')}
                >
                  📉 Tín hiệu BÁN
                  <span className="vip-tab-count">{sellSignals.length}</span>
                </button>
              </div>

              {/* Section header */}
              <div className="vip-section-hdr">
                <div className="vip-section-title">
                  {activeTab === 'buy' ? '📈 Mua vào' : '📉 Bán ra'}
                  <span className="vn30-badge">VN30 ưu tiên</span>
                </div>
                <span style={{ fontSize: '12px', color: '#6b5a8a' }}>{displaySignals.length} tín hiệu</span>
              </div>

              {/* Signal list */}
              {loading ? (
                <div className="vip-loading">
                  <div className="vip-spinner" />
                  <span>Đang tải tín hiệu VIP...</span>
                </div>
              ) : error ? (
                <div className="vip-empty">
                  <div className="vip-empty-icon">⚠️</div>
                  <div className="vip-empty-title">Lỗi tải dữ liệu</div>
                  <div className="vip-empty-sub">{error}</div>
                </div>
              ) : displaySignals.length === 0 ? (
                <div className="vip-empty">
                  <div className="vip-empty-icon">{activeTab === 'buy' ? '📈' : '📉'}</div>
                  <div className="vip-empty-title">Chưa có tín hiệu {activeTab === 'buy' ? 'MUA' : 'BÁN'}</div>
                  <div className="vip-empty-sub">
                    Bấm "Quét VN30" để chạy scanner VIP<br />
                    hoặc chờ hệ thống tự động cập nhật.
                  </div>
                </div>
              ) : (
                <div className="vip-signals-list">
                  {displaySignals.map((sig, i) => (
                    <SignalCard
                      key={sig.id || i}
                      signal={sig}
                      expanded={expandedId === (sig.id || i)}
                      onExpand={() => setExpandedId(expandedId === (sig.id || i) ? null : (sig.id || i))}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* RIGHT — Panel */}
            <div className="vip-panel">
              <FilterPanel filters={filters} setFilters={setFilters} signalCount={displaySignals.length} />
              <VN30Panel signals={signals} />
              <TelegramPanel user={user} />
            </div>
          </div>

          {/* ── DISCLAIMER ── */}
          <div className="vip-disclaimer">
            <div className="vip-disclaimer-inner">
              <strong>⚠️ Lưu ý:</strong> Tín hiệu VIP là công cụ hỗ trợ quyết định, không phải tư vấn đầu tư.
              Mọi quyết định giao dịch là trách nhiệm của bạn. Đầu tư chứng khoán có rủi ro — bạn có thể mất một phần hoặc toàn bộ vốn.
              Tín hiệu ưu tiên VN30 (thanh khoản cao, rủi ro thấp hơn) nhưng không đảm bảo lợi nhuận.
            </div>
          </div>

        </div>

        {/* Toast */}
        {toast && <div className="vip-toast">{toast}</div>}
      </div>
    </>
  );
}
