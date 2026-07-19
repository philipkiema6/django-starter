// Minimal PWA service worker: runtime-caches static assets and falls back to an offline
// page for navigations when the network is unavailable. Served at the site root (see
// apps/web/views.py::service_worker) rather than at /static/sw.js, since a service worker's
// default scope is the directory it's served from — /static/ would only cover static assets.
const CACHE_NAME = "app-cache-v1";
const OFFLINE_URL = "/offline/";

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.add(OFFLINE_URL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }

  if (request.mode === "navigate") {
    // Network-first for page loads; fall back to the cached offline page when unreachable.
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
    return;
  }

  const url = new URL(request.url);
  if (url.pathname.startsWith("/static/")) {
    // Cache-first for static assets: instant repeat loads, and available offline once fetched.
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) {
          return cached;
        }
        return fetch(request).then((response) => {
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, responseClone));
          }
          return response;
        });
      })
    );
  }
});
