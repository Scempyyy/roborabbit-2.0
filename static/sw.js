// Roborabbit PWA Service Worker
const CACHE_NAME = 'roborabbit-cyber-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', (e) => {
  // Pass-through for live API calls and WebSocket streaming
  if (e.request.url.includes('/api/') || e.request.url.includes('/ws/')) {
    return;
  }
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
