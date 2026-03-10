/**
 * AI ADVISOR - SERVICE WORKER
 * Version: 1.0
 * 
 * Handles:
 * - Push notifications (Buy/Sell signals)
 * - Offline caching
 * - Background sync
 */

const CACHE_NAME = 'ai-advisor-v1.0';
const STATIC_CACHE = 'ai-advisor-static-v1.0';

// Assets to cache for offline support
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
];

// ============================================================
// INSTALL: Pre-cache static assets
// ============================================================
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ============================================================
// ACTIVATE: Cleanup old caches
// ============================================================
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== CACHE_NAME && key !== STATIC_CACHE)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// ============================================================
// FETCH: Serve from cache, fallback to network
// ============================================================
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  // Skip API calls - always go to network
  if (event.request.url.includes('/api/')) return;

  event.respondWith(
    caches.match(event.request)
      .then(cached => {
        if (cached) return cached;

        return fetch(event.request)
          .then(response => {
            // Cache successful responses for HTML/CSS/JS
            if (response.ok && !event.request.url.includes('chrome-extension')) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone));
            }
            return response;
          })
          .catch(() => {
            // Offline fallback for navigation
            if (event.request.mode === 'navigate') {
              return caches.match('/offline.html');
            }
          });
      })
  );
});

// ============================================================
// PUSH NOTIFICATION - Core handler
// ============================================================
self.addEventListener('push', (event) => {
  console.log('[SW] Push received');

  let data = {
    type: 'info',
    title: 'AI Advisor',
    body: 'Có thông báo mới',
    ticker: '',
    signal_type: '',
    url: '/dashboard',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
  };

  // Parse incoming push data
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }

  // Build notification based on signal type
  const notificationOptions = buildNotificationOptions(data);

  event.waitUntil(
    self.registration.showNotification(data.title, notificationOptions)
  );
});

// ============================================================
// BUILD NOTIFICATION - Style based on signal type
// ============================================================
function buildNotificationOptions(data) {
  const { type, ticker, signal_type } = data;

  let icon = '/icons/icon-192x192.png';
  let badge = '/icons/badge-72x72.png';
  let vibrate = [200, 100, 200]; // Default vibration
  let tag = `signal-${ticker}-${Date.now()}`;
  let actions = [];

  // --- BUY SIGNAL ---
  if (type === 'buy_signal') {
    vibrate = [300, 100, 300, 100, 300]; // Longer vibration for buy
    tag = `buy-${ticker}`;
    actions = [
      { action: 'view_signal', title: '📊 Xem Chi Tiết' },
      { action: 'dismiss', title: 'Bỏ Qua' }
    ];
  }

  // --- SELL SIGNAL ---
  else if (type === 'sell_signal') {
    vibrate = [500, 200, 500]; // Urgent vibration for sell
    tag = `sell-${ticker}`;
    actions = [
      { action: 'view_signal', title: '📊 Xem Chi Tiết' },
      { action: 'dismiss', title: 'Bỏ Qua' }
    ];
  }

  return {
    body: data.body,
    icon: icon,
    badge: badge,
    vibrate: vibrate,
    tag: tag,
    renotify: true,
    requireInteraction: type === 'sell_signal', // Sell = requires tap to dismiss
    silent: false,
    timestamp: Date.now(),
    actions: actions,
    data: {
      url: data.url || '/dashboard',
      type: data.type,
      ticker: data.ticker,
      signal_id: data.signal_id,
    }
  };
}

// ============================================================
// NOTIFICATION CLICK - Handle action buttons
// ============================================================
self.addEventListener('notificationclick', (event) => {
  const notification = event.notification;
  const action = event.action;
  const notifData = notification.data || {};

  notification.close();

  console.log('[SW] Notification clicked:', action, notifData);

  if (action === 'dismiss') return;

  // Determine target URL
  let targetUrl = notifData.url || '/dashboard';

  if (action === 'view_signal' || !action) {
    if (notifData.signal_id) {
      targetUrl = `/dashboard/signals/${notifData.signal_id}`;
    } else if (notifData.type === 'buy_signal') {
      targetUrl = '/dashboard/signals?type=buy';
    } else if (notifData.type === 'sell_signal') {
      targetUrl = '/dashboard/signals?type=sell';
    }
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(windowClients => {
        // Focus existing window if open
        for (const client of windowClients) {
          if (client.url.includes(self.location.origin) && 'focus' in client) {
            client.focus();
            client.navigate(targetUrl);
            return;
          }
        }
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
  );
});

// ============================================================
// NOTIFICATION CLOSE - Track dismissals
// ============================================================
self.addEventListener('notificationclose', (event) => {
  const data = event.notification.data || {};
  console.log('[SW] Notification closed:', data.type, data.ticker);
  // Could send analytics here via fetch in future
});

// ============================================================
// MESSAGE - Handle messages from app
// ============================================================
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
