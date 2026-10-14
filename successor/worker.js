'use strict';
const cacheName = 'kaz-successor-__BUILD__';
const core = ['/', '/offline.html', '/v6/site.css', '/v6/theme.js', '/v6/site.js', '/search-index.json', '/favicon.ico'];
const publicPaths = new Set(__PUBLIC_PATHS__);
let cacheTasks = Promise.resolve();
self.addEventListener('install', event => {
  event.waitUntil(caches.open(cacheName).then(cache => cache.addAll(core)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(names => Promise.all(names.filter(name => (name.startsWith('kaz-notebook-') || name.startsWith('kaz-successor-')) && name !== cacheName).map(name => caches.delete(name)))).then(() => self.clients.claim()));
});
async function remember(request, response) {
  try {
    const cache = await caches.open(cacheName);
    await cache.put(request, response);
    const keys = await cache.keys();
    let excess = keys.length - 100;
    for (const key of keys) {
      const url = new URL(key.url);
      if (excess <= 0) break;
      if (!url.search && core.includes(url.pathname)) continue;
      if (await cache.delete(key)) excess--;
    }
  } catch { /* Storage denial or quota exhaustion must not break online reading. */ }
}
async function saved(request, url) {
  try {
    const cache = await caches.open(cacheName);
    return await cache.match(request) || await cache.match(url.pathname) ||
      (request.mode === 'navigate' ? await cache.match('/offline.html') : Response.error());
  } catch { return Response.error(); }
}
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || !publicPaths.has(url.pathname) || request.headers.has('Authorization')) return;
  event.respondWith((async () => {
    const controller = new AbortController();
    const timeout = request.mode === 'navigate' ? setTimeout(() => controller.abort(), 10000) : null;
    try {
      const response = await fetch(request, {signal: controller.signal});
      const policy = response.headers.get('Cache-Control') || '';
      const vary = response.headers.get('Vary') || '';
      if (response.ok && response.type === 'basic' && !url.search && !/no-store|private/i.test(policy) && !/cookie|authorization|\*/i.test(vary)) {
        const copy = response.clone();
        cacheTasks = cacheTasks.then(() => remember(request, copy));
        event.waitUntil(cacheTasks);
      }
      return response;
    } catch { return saved(request, url); }
    finally { if (timeout !== null) clearTimeout(timeout); }
  })());
});
