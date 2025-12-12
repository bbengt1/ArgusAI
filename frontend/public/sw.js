/**
 * Service Worker for PWA (Story P4-1.5)
 *
 * Handles:
 * - Push events: Display rich notifications with thumbnails, actions, and deep links
 * - Notification click: Navigate to event details or handle actions
 * - Notification close: Optional analytics tracking
 * - Asset caching: Cache-first for static assets
 * - API caching: Network-first with cache fallback for API calls
 * - Offline support: Show offline page when network unavailable
 *
 * @see https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
 */

// Service worker version for cache busting
const SW_VERSION = '2.0.0';

// Cache names with version
const STATIC_CACHE_NAME = `static-v${SW_VERSION}`;
const API_CACHE_NAME = `api-v${SW_VERSION}`;
const IMAGE_CACHE_NAME = `images-v${SW_VERSION}`;

// Assets to precache on install
const PRECACHE_ASSETS = [
  '/',
  '/offline',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// URL patterns for caching strategies
const STATIC_PATTERNS = [
  /^\/_next\/static\//,  // Next.js static assets
  /^\/icons\//,          // App icons
  /\.(?:js|css|woff2?|ttf|eot)$/, // Static file types
];

const API_PATTERNS = [
  /^\/api\/v1\/events/,
  /^\/api\/v1\/cameras/,
];

const IMAGE_PATTERNS = [
  /\.(?:png|jpg|jpeg|gif|svg|webp|ico)$/,
];

/**
 * Install event - precache critical assets
 */
self.addEventListener('install', (event) => {
  console.log('[SW] Service worker installing, version:', SW_VERSION);

  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Precaching critical assets');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => {
        console.log('[SW] Precache complete, skipping waiting');
        return self.skipWaiting();
      })
      .catch((err) => {
        console.error('[SW] Precache failed:', err);
        // Still skip waiting even if precache fails
        return self.skipWaiting();
      })
  );
});

/**
 * Activate event - clean up old caches and take control
 */
self.addEventListener('activate', (event) => {
  console.log('[SW] Service worker activating, version:', SW_VERSION);

  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              // Delete caches that don't match current version
              return cacheName.startsWith('static-') && cacheName !== STATIC_CACHE_NAME ||
                     cacheName.startsWith('api-') && cacheName !== API_CACHE_NAME ||
                     cacheName.startsWith('images-') && cacheName !== IMAGE_CACHE_NAME;
            })
            .map((cacheName) => {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      }),
      // Take control of all clients immediately
      clients.claim(),
    ]).then(() => {
      // Notify all clients about the new version
      return clients.matchAll({ type: 'window' }).then((windowClients) => {
        windowClients.forEach((client) => {
          client.postMessage({
            type: 'SW_UPDATED',
            version: SW_VERSION,
          });
        });
      });
    })
  );
});

/**
 * Fetch event - handle caching strategies
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Determine caching strategy based on URL pattern
  const pathname = url.pathname;

  // API requests: Network-first with cache fallback
  if (API_PATTERNS.some((pattern) => pattern.test(pathname))) {
    event.respondWith(networkFirstWithCache(request, API_CACHE_NAME));
    return;
  }

  // Static assets: Cache-first with network fallback
  if (STATIC_PATTERNS.some((pattern) => pattern.test(pathname))) {
    event.respondWith(cacheFirstWithNetwork(request, STATIC_CACHE_NAME));
    return;
  }

  // Images: Cache-first with network fallback
  if (IMAGE_PATTERNS.some((pattern) => pattern.test(pathname))) {
    event.respondWith(cacheFirstWithNetwork(request, IMAGE_CACHE_NAME));
    return;
  }

  // HTML pages: Network-first with offline fallback
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }

  // Default: Try cache, then network
  event.respondWith(cacheFirstWithNetwork(request, STATIC_CACHE_NAME));
});

/**
 * Cache-first strategy with network fallback
 */
async function cacheFirstWithNetwork(request, cacheName) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    // Return cached response immediately
    // Optionally update cache in background (stale-while-revalidate)
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache-first fetch failed:', error);
    // Return a generic error response
    return new Response('Network error', { status: 503, statusText: 'Service Unavailable' });
  }
}

/**
 * Network-first strategy with cache fallback
 */
async function networkFirstWithCache(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch {
    console.log('[SW] Network failed, trying cache:', request.url);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Return error response if no cache
    return new Response(JSON.stringify({ error: 'Offline', message: 'No cached data available' }), {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

/**
 * Network-first strategy with offline page fallback
 */
async function networkFirstWithOffline(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch {
    console.log('[SW] Network failed for page, showing offline:', request.url);

    // Try to return cached version of the page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page
    const offlineResponse = await caches.match('/offline');
    if (offlineResponse) {
      return offlineResponse;
    }

    // Last resort: return a simple offline message
    return new Response(
      '<!DOCTYPE html><html><head><title>Offline</title></head><body><h1>You are offline</h1><p>Please check your internet connection.</p></body></html>',
      { headers: { 'Content-Type': 'text/html' } }
    );
  }
}

/**
 * Handle incoming push notifications
 * Displays rich notification with thumbnail, actions, and deep link data
 */
self.addEventListener('push', (event) => {
  console.log('[SW] Push event received');

  // Default notification options if payload parsing fails
  const defaultOptions = {
    title: 'ArgusAI',
    body: 'New event detected',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.svg',
  };

  let notificationData = defaultOptions;

  try {
    if (event.data) {
      const payload = event.data.json();
      console.log('[SW] Push payload:', payload);
      notificationData = payload;
    }
  } catch (err) {
    console.error('[SW] Error parsing push data:', err);
    // Fall back to text if JSON parsing fails
    try {
      notificationData.body = event.data?.text() || defaultOptions.body;
    } catch {
      // Use default
    }
  }

  const { title, ...options } = notificationData;

  // Build notification options
  const notificationOptions = {
    body: options.body || '',
    icon: options.icon || '/icons/icon-192.png',
    badge: options.badge || '/icons/badge-72.svg',
    // Image: Large thumbnail (displayed below body in supported browsers)
    ...(options.image && { image: options.image }),
    // Tag: Used for notification collapse/replacement
    ...(options.tag && { tag: options.tag }),
    // Renotify: Alert again even if same tag (for updates)
    renotify: options.renotify ?? true,
    // Require interaction: Keep notification visible until user interacts
    requireInteraction: options.requireInteraction ?? false,
    // Actions: Buttons displayed on notification
    actions: options.actions || [
      { action: 'view', title: 'View', icon: '/icons/view-24.svg' },
      { action: 'dismiss', title: 'Dismiss', icon: '/icons/dismiss-24.svg' },
    ],
    // Data: Custom data passed to click handler (event_id, url, etc.)
    data: options.data || {},
    // Silent: Don't vibrate/sound (false by default)
    silent: options.silent ?? false,
    // Timestamp: When the event occurred
    ...(options.timestamp && { timestamp: options.timestamp }),
  };

  console.log('[SW] Showing notification:', title, notificationOptions);

  event.waitUntil(
    self.registration.showNotification(title || 'ArgusAI', notificationOptions)
  );
});

/**
 * Handle notification click events
 * Opens the app and navigates to the event details page
 */
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification click:', event.action, event.notification.data);

  // Always close the notification
  event.notification.close();

  // Handle dismiss action - just close, no navigation
  if (event.action === 'dismiss') {
    console.log('[SW] Notification dismissed by user');
    // Could track dismissal analytics here if needed
    return;
  }

  // For 'view' action or body click, navigate to the URL
  const url = event.notification.data?.url || '/';
  const fullUrl = new URL(url, self.location.origin).href;

  console.log('[SW] Opening URL:', fullUrl);

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Check if app is already open in a tab
      for (const client of clientList) {
        // Check if this is our app (same origin)
        if (client.url.startsWith(self.location.origin)) {
          console.log('[SW] Found existing client, navigating and focusing');
          // Navigate to the event URL
          client.navigate(fullUrl);
          // Focus the tab
          return client.focus();
        }
      }

      // No existing tab found, open a new one
      console.log('[SW] No existing client, opening new window');
      return clients.openWindow(fullUrl);
    })
  );
});

/**
 * Handle notification close events (user dismissed without clicking)
 * Useful for analytics tracking
 */
self.addEventListener('notificationclose', (event) => {
  console.log('[SW] Notification closed:', event.notification.data);
  // Could track close analytics here if needed
  // For example, send to analytics endpoint
});

/**
 * Handle messages from the main app
 * Can be used for communication between app and service worker
 */
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  if (event.data?.type === 'GET_VERSION') {
    event.ports[0]?.postMessage({ version: SW_VERSION });
  }

  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data?.type === 'CLEAR_CACHES') {
    caches.keys().then((cacheNames) => {
      return Promise.all(cacheNames.map((cache) => caches.delete(cache)));
    }).then(() => {
      event.ports[0]?.postMessage({ success: true });
    });
  }
});
