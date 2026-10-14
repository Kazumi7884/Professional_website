const {readFileSync} = require('node:fs');
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const origin = 'https://example.test';
const paths = ['/', '/offline.html', '/v6/site.css', '/v6/site.js', '/v6/theme.js', '/search-index.json', '/favicon.ico', ...Array.from({length: 120}, (_, i) => `/page/${i}/`)];
const source = readFileSync(__dirname + '/worker.js', 'utf8').replace('__PUBLIC_PATHS__', JSON.stringify(paths));
function setup(options = {}) {
  const handlers = {}, entries = new Map(options.entries || []), pending = [];
  let timer;
  const key = request => new URL(typeof request === 'string' ? request : request.url, origin).href;
  const cache = {
    addAll: async () => {},
    put: options.put || (async (request, response) => entries.set(key(request), response)),
    match: async request => entries.get(key(request)),
    keys: async () => [...entries.keys()].map(url => ({url})),
    delete: async request => entries.delete(key(request))
  };
  const response = new Response('FRESH', {headers: options.responseHeaders});
  Object.defineProperty(response, 'type', {value: 'basic'});
  vm.runInNewContext(source, {URL, Headers, Response, AbortController,
    setTimeout: options.manualTimer ? callback => {timer = callback; return 1;} : setTimeout,
    clearTimeout: options.manualTimer ? () => {} : clearTimeout,
    self: {location: {origin}, addEventListener: (name, handler) => handlers[name] = handler},
    caches: {open: options.open || (async () => cache)},
    fetch: options.fetch || (async () => response)});
  const request = (path = '/', headers = {}, mode = 'navigate') => {
    let result;
    handlers.fetch({request: {url: new URL(path, origin).href, method: 'GET', headers: new Headers(headers), mode}, respondWith: value => result = value, waitUntil: value => pending.push(value)});
    return result;
  };
  return {request, entries, pending, expire: () => timer()};
}
test('quota denial keeps successful online content', async () => {
  const h = setup({put: async () => {throw Error('QuotaExceededError');}});
  assert.equal(await (await h.request()).text(), 'FRESH'); await Promise.all(h.pending);
});
test('cache storage denial keeps successful online content', async () => {
  const h = setup({open: async () => {throw Error('SecurityError');}});
  assert.equal(await (await h.request()).text(), 'FRESH'); await Promise.all(h.pending);
});
test('online response does not wait for cache writes', async () => {
  let finish; const h = setup({put: () => new Promise(resolve => finish = resolve)});
  assert.equal(await (await h.request()).text(), 'FRESH'); finish(); await Promise.all(h.pending);
});
test('private, no-store and cookie-varying responses are not cached', async () => {
  for (const headers of [{'Cache-Control': 'private'}, {'Cache-Control': 'no-store'}, {Vary: 'Cookie'}, {Vary: 'Authorization'}, {Vary: '*'}]) {
    const h = setup({responseHeaders: headers}); await h.request(); await Promise.all(h.pending); assert.equal(h.entries.size, 0);
  }
});
test('authorization, API, studio and unlisted paths bypass the worker', () => {
  const h = setup();
  for (const path of ['/api/private', '/__studio/api/posts', '/admin/']) assert.equal(h.request(path), undefined);
  assert.equal(h.request('/', {Authorization: 'Bearer example-test-token'}), undefined);
});
test('query variants never consume offline storage', async () => {
  const h = setup(); for (let i = 0; i < 110; i++) await h.request('/?q=' + i); await Promise.all(h.pending); assert.equal(h.entries.size, 0);
});
test('oversized cache is reduced to the real 100-entry bound', async () => {
  const entries = Array.from({length: 115}, (_, i) => [origin + '/page/' + i + '/', new Response('old')]);
  entries.push([origin + '/', new Response('home')]); const h = setup({entries});
  await h.request('/page/119/'); await Promise.all(h.pending); assert.equal(h.entries.size, 100); assert(h.entries.has(origin + '/'));
});
test('offline navigation uses the saved canonical page for query URLs', async () => {
  const h = setup({entries: [[origin + '/', new Response('HOME')]], fetch: async () => {throw Error('offline');}});
  assert.equal(await (await h.request('/?q=notes')).text(), 'HOME');
});
test('unknown saved navigation uses the offline document', async () => {
  const h = setup({entries: [[origin + '/offline.html', new Response('OFFLINE')]], fetch: async () => {throw Error('offline');}});
  assert.equal(await (await h.request('/page/1/')).text(), 'OFFLINE');
});
test('stalled navigation aborts and returns cached content', async () => {
  const h = setup({manualTimer: true, entries: [[origin + '/', new Response('HOME')]], fetch: (_request, {signal}) => new Promise((_resolve, reject) => signal.addEventListener('abort', () => reject(Error('timeout'))))});
  const pending = h.request(); h.expire(); assert.equal(await (await pending).text(), 'HOME');
});
