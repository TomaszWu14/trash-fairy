// Service worker PWA kierowcy: powłoka offline + Background Sync kolejki opróżnień i problemów (IndexedDB).
self.TF_DB_NAME = 'trash-fairy-kierowca';
importScripts('/static/zglos/queue.js');
const CACHE = 'tf-kierowca-v2';
const SHELL = ['/kierowca', '/static/kierowca/kierowca.css', '/static/kierowca/kierowca.js', '/static/zglos/queue.js',
               '/static/kierowca/manifest.webmanifest', '/static/img/icon-192.png',
               '/static/vendor/leaflet/leaflet.css', '/static/vendor/leaflet/leaflet.js', '/static/fonts/fonts.css'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.allSettled(SHELL.map(u => c.add(u)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('tf-kierowca') && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api/')) return;  // API zawsze z sieci (migawka kursu jest w localStorage)
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put('/kierowca', c)); return r; })
      .catch(() => caches.match('/kierowca')));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {  // zasoby i kafelki: cache, potem sieć
    if (r.ok || r.type === 'opaque') { const c = r.clone(); caches.open(CACHE).then(x => x.put(e.request, c)); }
    return r;
  })));
});

// ta sama wysyłka co na stronie (kierowca.js: sendItem), bo SW nie widzi jej kodu
async function flush() {
  for (const it of await tfQueue.all()) {
    const body = new FormData();
    for (const [k, v] of Object.entries(it.fields)) body.append(k, v);
    if (it.photo) body.append('photo', it.photo, it.photoName || 'zdjecie.jpg');
    const r = await fetch(it.url, { method: 'POST', body });  // brak sieci = wyjątek, sync spróbuje później
    if (r.status === 401 || r.status === 403) break;  // sesja wygasła: zapisy czekają, strona poprosi o logowanie
    if (r.status >= 500) throw new Error('server');
    await tfQueue.remove(it.id);  // pozostałe 4xx (złe dane) nie ma sensu powtarzać
  }
  (await self.clients.matchAll({ type: 'window' })).forEach(c => c.postMessage({ type: 'tf-flushed' }));
}
self.addEventListener('sync', e => { if (e.tag === 'tf-kierowca') e.waitUntil(flush()); });
self.addEventListener('message', e => { if (e.data === 'tf-flush') e.waitUntil(flush().catch(() => {})); });
