// Service worker ekranu „Zgłoś kosz”: powłoka offline + Background Sync kolejki zgłoszeń (IndexedDB).
importScripts('/static/zglos/queue.js');
const CACHE = 'tf-zglos-v2';
const SHELL = ['/static/zglos/zglos.css', '/static/zglos/zglos.js', '/static/zglos/queue.js', '/static/zglos/icon.svg',
               '/static/zglos/manifest.webmanifest', '/static/img/krakow-basemap.svg',
               '/static/vendor/leaflet/leaflet.css', '/static/vendor/leaflet/leaflet.js', '/static/fonts/fonts.css'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.allSettled(SHELL.map(u => c.add(u)))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api/')) return;  // API zawsze z sieci
  if (e.request.mode === 'navigate') {  // strona: sieć, a bez niej ostatnia zapisana kopia tego kosza
    e.respondWith(fetch(e.request).then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; })
      .catch(() => caches.match(e.request).then(r => r || caches.match('/zglos'))));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {  // zasoby: cache, potem sieć
    if (r.ok || r.type === 'opaque') caches.open(CACHE).then(c => c.put(e.request, r.clone()));
    return r;
  })));
});

// Background Sync: wyślij zakolejkowane zgłoszenia, powiadom otwarte karty o wyniku
async function flush() {
  const items = await tfQueue.all();
  for (const it of items) {
    let r, data;
    try {
      r = await fetch('/api/press', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(it.body) });
      data = await r.json();
    } catch (e) { throw e; }  // brak sieci: sync spróbuje później
    if (r.status < 500) await tfQueue.remove(it.id);  // 4xx nie ma sensu powtarzać; strona pokaże powód
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach(c => c.postMessage({ type: 'tf-sent', point_id: it.body.point_id, status: r.status, data, chosen: it.chosen }));
    if (r.status >= 500) throw new Error('server');
  }
}
self.addEventListener('sync', e => { if (e.tag === 'tf-report') e.waitUntil(flush()); });
self.addEventListener('message', e => { if (e.data === 'tf-flush') e.waitUntil(flush().catch(() => {})); });
