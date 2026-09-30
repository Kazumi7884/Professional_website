'use strict';
const cacheName = 'kaz-successor-__BUILD__';
const core = ['/', '/offline.html', '/v6/site.css', '/v6/theme.js', '/v6/site.js', '/search-index.json', '/favicon.ico'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(cacheName).then(cache => cache.addAll(core)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(names => Promise.all(names.filter(name => (name.startsWith('kaz-notebook-') || name.startsWith('kaz-successor-')) && name !== cacheName).map(name => caches.delete(name)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/__studio/') || url.pathname.startsWith('/api/')) return;
  event.respondWith((async () => {
    const cache = await caches.open(cacheName);
    try {
      const response = await fetch(request);
      if (response.ok && response.type === 'basic') {
        await cache.put(request, response.clone());
        const keys = await cache.keys();
        if (keys.length > 100) {
          const old = keys.find(key => !core.includes(new URL(key.url).pathname));
          if (old) await cache.delete(old);
        }
      }
      return response;
    } catch {
      return await cache.match(request) || (request.mode === 'navigate' ? await cache.match('/offline.html') : Response.error());
    }
  })());
});
