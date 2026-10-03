// Ekran „Zgłoś kosz”: maszyna stanów start → sending → sent | dup | far | limit | error | offline (+ nosignal jako baner).
// Cała zmiana stanów po stronie klienta, jedno POST /api/press. Teksty: docs/zgloszenie/design/ekran-zgloszenia.dc.html.
const Z = window.ZGLOS;
const UNDO_MS = 1500;          // okno na „Cofnij”, potem POST
const FAR_M = 150;             // ten sam próg co GEO_RADIUS_M na serwerze
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const OPTS = {
  full: { label: 'Pełny', sub: 'Nie mieści się więcej',
    icon: '<svg class="z-ico" viewBox="0 0 40 40" aria-hidden="true"><rect x="8.5" y="8.5" width="23" height="23" rx="3" transform="rotate(45 20 20)" fill="#F0A500"/><path d="M20 27V13.5M14.5 19L20 13.5l5.5 5.5" fill="none" stroke="#000" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>' },
  overflow: { label: 'Przepełniony, odpady obok', sub: 'Worki lub śmieci wokół kosza',
    icon: '<svg class="z-ico" viewBox="0 0 40 40" aria-hidden="true"><rect x="4" y="4" width="32" height="32" rx="5" fill="#C40000"/><path d="M20 10v13" stroke="#fff" stroke-width="4" stroke-linecap="round"/><circle cx="20" cy="29" r="2.6" fill="#fff"/></svg>' },
  damaged: { label: 'Uszkodzony', sub: 'Zepsuty, przewrócony, bez klapy',
    icon: '<svg class="z-ico" viewBox="0 0 40 40" aria-hidden="true"><path d="M20 3 L38 35 H2 Z" fill="var(--warn-fill)" stroke-linejoin="round"/><path d="M20 14v10" stroke="var(--warn-glyph)" stroke-width="3.5" stroke-linecap="round"/><circle cx="20" cy="29.5" r="2.3" fill="var(--warn-glyph)"/></svg>' },
};
const I = {
  warn: '<svg width="28" height="28" viewBox="0 0 40 40" aria-hidden="true"><path d="M20 3 L38 35 H2 Z" fill="var(--warn-fill)" stroke-linejoin="round"/><path d="M20 14v10" stroke="var(--warn-glyph)" stroke-width="3.5" stroke-linecap="round"/><circle cx="20" cy="29.5" r="2.3" fill="var(--warn-glyph)"/></svg>',
  pin: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0B5FD6" stroke-width="2.2" aria-hidden="true"><path d="M12 22s7-6.5 7-12a7 7 0 0 0-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>',
  clock: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  nowifi: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD34D" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M2 8.5a15 15 0 0 1 20 0M5 12a10 10 0 0 1 14 0M8.5 15.5a5 5 0 0 1 7 0M12 19h.01M3 3l18 18"/></svg>',
  spin: '<svg class="spin" width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-opacity=".3" stroke-width="3"/><path d="M12 3a9 9 0 0 1 9 9" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
  cam: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>',
  chat: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z"/></svg>',
  lock: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>',
  bubble: '<svg width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><path d="M5 9a5 5 0 0 1 5-5h20a5 5 0 0 1 5 5v15a5 5 0 0 1-5 5H15l-10 8V9z" fill="#5B2A9A"/><path d="M13 16.5l4.5 4.5 9-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  check: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--on-primary)" stroke-width="4" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>',
  people: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.8"/><path d="M16 14.2A5.5 5.5 0 0 1 21.5 20"/></svg>',
  star: (c, s = 24) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 L14 10 L22 12 L14 14 L12 22 L10 14 L2 12 L10 10 Z" fill="${c}"/></svg>`,
};
const PIN = {
  ok: '<svg class="z-pin" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="17" fill="#127A3E" stroke="#fff" stroke-width="3"/><path d="M12.5 20.5l5 5 10-11" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  near: '<svg class="z-pin" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><rect x="8" y="8" width="24" height="24" rx="3" transform="rotate(45 20 20)" fill="#F0A500" stroke="#fff" stroke-width="3"/><path d="M20 27V13.5M14.5 19L20 13.5l5.5 5.5" fill="none" stroke="#000" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  full: '<svg class="z-pin" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><rect x="4" y="4" width="32" height="32" rx="5" fill="#C40000" stroke="#fff" stroke-width="3"/><path d="M20 10v13" stroke="#fff" stroke-width="4" stroke-linecap="round"/><circle cx="20" cy="29" r="2.6" fill="#fff"/></svg>',
  report: '<svg class="z-pin" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><path d="M5 9a5 5 0 0 1 5-5h20a5 5 0 0 1 5 5v15a5 5 0 0 1-5 5H15l-10 8V9z" fill="#5B2A9A" stroke="#fff" stroke-width="2.5" stroke-linejoin="round"/><circle cx="13" cy="16.5" r="2.4" fill="#fff"/><circle cx="20" cy="16.5" r="2.4" fill="#fff"/><circle cx="27" cy="16.5" r="2.4" fill="#fff"/></svg>',
  warn: '<svg class="z-pin" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><path d="M20 3 L38 35 H2 Z" fill="#2F3A41" stroke="#fff" stroke-width="2.5" stroke-linejoin="round"/><path d="M20 14v10" stroke="#fff" stroke-width="3.5" stroke-linecap="round"/><circle cx="20" cy="29.5" r="2.3" fill="#fff"/></svg>',
};

// --- stan ekranu ---
const S = { screen: 'start', chosen: 'full', bin: null, pos: null, dist: null, result: null, retryAt: null, timer: null, queuedAt: null };
const clientId = (() => { try { let v = localStorage.getItem('tf-client-id'); if (!v) { v = crypto.randomUUID(); localStorage.setItem('tf-client-id', v); } return v; } catch (e) { return 'anon'; } })();
const hhmm = d => d.toTimeString().slice(0, 5);

// --- mini-mapa (Leaflet; podkład OSM z filtrem w ciemnym; offline: statyczny SVG) ---
let map, binMarker, youMarker, ring;
function initMap(b) {
  map = L.map('map', { zoomControl: false, attributionControl: true, scrollWheelZoom: false }).setView([b.lat, b.lon], 17);
  map.attributionControl.setPrefix(false);
  let errors = 0;
  const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
  tiles.on('tileerror', () => { if (++errors === 3) { map.removeLayer(tiles); L.imageOverlay(Z.basemap, [[50.04095, 19.912], [50.07005, 19.992]], { attribution: '© OpenStreetMap' }).addTo(map); } });
  for (const n of b.neighbors) {
    L.marker([n.lat, n.lon], { interactive: false, keyboard: false, icon: L.divIcon({ className: '', iconSize: [14, 14], html: `<span class="z-near ${n.state}"></span>` }) }).addTo(map);
  }
  binMarker = L.marker([b.lat, b.lon], { keyboard: false, zIndexOffset: 1000, icon: pinIcon(pinKind()) }).addTo(map);
}
const pinKind = () => (S.screen === 'sent' || S.screen === 'dup') ? 'report' : S.screen === 'nosignal' ? 'warn' : S.bin.state === 'bad' ? 'full' : S.bin.state === 'warn' ? 'near' : 'ok';
const pinIcon = kind => L.divIcon({ className: '', iconSize: [40, 40], iconAnchor: [20, 20], html: PIN[kind] + `<span class="z-pin-lbl">${esc(Z.name)}</span>` });

function updateMap() {
  if (!map) return;
  binMarker.setIcon(pinIcon(pinKind()));
  if (ring) { map.removeLayer(ring); ring = null; }
  if (S.screen === 'far') {
    ring = L.layerGroup([
      L.circle([S.bin.lat, S.bin.lon], { radius: FAR_M, color: '#0E1222', weight: 2, dashArray: '6 6', fillColor: '#0E1222', fillOpacity: .06, interactive: false }),
      L.marker([S.bin.lat - FAR_M / 111320 * .7, S.bin.lon], { interactive: false, keyboard: false, icon: L.divIcon({ className: '', iconSize: [0, 0], html: '<span class="z-ring-lbl" style="transform:translate(-50%,-50%);display:inline-block">150 m</span>' }) }),
    ]).addTo(map);
    if (S.pos) map.fitBounds(L.latLngBounds([[S.bin.lat, S.bin.lon], [S.pos.lat, S.pos.lon]]).pad(.4));
  }
  if (S.pos) {
    const icon = L.divIcon({ className: '', iconSize: [18, 18], iconAnchor: [9, 9], html: '<span class="z-you" style="display:block"></span><span class="z-you-lbl">Ty</span>' });
    youMarker ? youMarker.setLatLng([S.pos.lat, S.pos.lon]) : (youMarker = L.marker([S.pos.lat, S.pos.lon], { interactive: false, keyboard: false, icon }).addTo(map));
  }
  setTimeout(() => map.invalidateSize(), 220);  // wysokość mapy zmienia się ze stanem
}

// --- geolokalizacja: brak zgody nie blokuje (location: null) ---
function locate() {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(p => {
    S.pos = { lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy };
    S.dist = Math.round(distM(S.pos.lat, S.pos.lon, S.bin.lat, S.bin.lon));
    $('dist-txt').textContent = `Jesteś ok. ${S.dist < 1000 ? S.dist + ' m' : (S.dist / 1000).toFixed(1).replace('.', ',') + ' km'} od kosza`;
    $('dist').hidden = false;
    // ta sama reguła co serwer: odległość minus dokładność GPS (max 150 m), żeby słaby GPS w kamienicy nie blokował
    const far = S.dist - Math.min(S.pos.acc || 0, FAR_M) > FAR_M;
    if (far && S.screen === 'start' && !Z.jury) setScreen('far');  // jury klika z sali, więc dla niego nie blokujemy
    else if (!far && S.screen === 'far') setScreen('start');
    else updateMap();
  }, () => { /* bez lokalizacji: wysyłamy bez niej */ }, { enableHighAccuracy: true, timeout: 8000, maximumAge: 30000 });
}
function distM(a, b, c, d) { const R = 6371000, r = Math.PI / 180, x = (c - a) * r, y = (d - b) * r * Math.cos((a + c) / 2 * r); return R * Math.sqrt(x * x + y * y); }

// --- renderowanie arkusza ---
function setScreen(s) { S.screen = s; document.body.dataset.screen = s; render(); updateMap(); }

function optButton(id, disabled) {
  const o = OPTS[id];
  return `<button type="button" class="z-opt ${id}" data-kind="${id}" ${disabled ? 'disabled' : ''}>${o.icon}<span><b>${o.label}</b><small>${o.sub}</small></span></button>`;
}
const privacy = () => `<span class="z-privacy">${I.lock}Zapisujemy tylko czas i miejsce zgłoszenia. Bez konta i numeru telefonu.</span>`;
const extras = () => `<div class="z-grid2"><button type="button" class="z-ghost thin" id="btn-photo">${I.cam}Dodaj zdjęcie</button><button type="button" class="z-ghost thin" id="btn-comment">${I.chat}Komentarz</button></div>`;
const lead = () => `<div class="z-lead"><h2>Co widzisz?</h2><span class="z-muted">Jedno dotknięcie wysyła zgłoszenie.</span></div>`;

function render() {
  const b = S.bin, o = OPTS[S.chosen], sheet = $('sheet');
  const disabledAll = S.screen === 'far' || S.screen === 'limit';
  const opts = kindsHtml => `<div class="z-opts">${kindsHtml}</div>`;
  const list = (mode) => opts(Object.keys(OPTS).map(id => (id === S.chosen && mode) ? mode : optButton(id, disabledAll || !!mode)).join(''));
  let html = '';
  if (S.screen === 'nosignal') {
    html += `<div class="z-note warn" role="note">${I.warn}<span class="txt"><strong>Przycisk na koszu chwilowo nie działa</strong><span class="z-muted">Zgłoszenie przez telefon działa normalnie i trafia do dyspozytora.</span></span></div>`;
  }
  if (S.screen === 'far') {
    html += `<div class="z-note col" role="note"><span style="display:flex;gap:12px">${I.pin}<span class="txt"><strong>Jesteś ok. ${S.dist} m od tego kosza</strong><span class="z-muted">Zgłoszenia przyjmujemy z odległości do 150 m, żeby trafiły do właściwego kosza. Podejdź bliżej albo wybierz kosz obok siebie.</span></span></span>
      <span class="z-grid2"><button type="button" class="z-btn sm" id="btn-relocate">Odśwież lokalizację</button><a class="z-ghost" href="/zglos" style="display:flex;align-items:center;justify-content:center;text-decoration:none">Kosze w pobliżu</a></span></div>`;
  }
  if (S.screen === 'limit') {
    html += `<div class="z-note" role="note">${I.clock}<span class="txt"><strong>Dziękujemy za Twoją pomoc</strong><span class="z-muted">Z tego telefonu wysłano kilka zgłoszeń w krótkim czasie. Kolejne możesz wysłać o <strong style="color:var(--text)">${esc(S.retryAt || '')}</strong>.</span></span></div>`;
  }
  if (S.screen === 'offline') {
    html += `<div class="z-toast" role="status">${I.nowifi}<span><strong>Brak zasięgu.</strong> Zgłoszenie jest zapisane w telefonie.</span></div>`;
  }
  if (['start', 'nosignal'].includes(S.screen)) html += lead();

  if (S.screen === 'sending') {
    html += list(`<div class="z-sending" role="status"><span class="row">${I.spin}<span>Wysyłamy: ${o.label}</span><button type="button" class="z-undo" id="btn-undo">Cofnij</button></span><span class="z-prog"><span id="prog"></span></span></div>`);
    html += privacy();
  } else if (S.screen === 'offline') {
    html += list(`<div class="z-queued" role="status"><b>${o.label} · w kolejce od ${S.queuedAt}</b><span class="z-muted">Wyślemy, gdy wróci zasięg. Możesz zamknąć aplikację.</span></div>`);
  } else if (S.screen === 'error') {
    html += list(`<div class="z-error" role="alert"><span><b>${o.label} · nie udało się wysłać</b><br>To problem po naszej stronie. Zgłoszenie czeka w telefonie.</span><button type="button" class="z-btn md" id="btn-retry">Spróbuj ponownie</button></div>`);
  } else if (S.screen === 'sent' || S.screen === 'dup') {
    html += doneHtml();
  } else {
    html += list(null);
    if (!disabledAll) html += extras() + privacy();
  }
  sheet.innerHTML = html;
  bind();
  if (S.screen === 'sending') requestAnimationFrame(() => requestAnimationFrame(() => { const p = $('prog'); if (p) p.style.width = '100%'; }));
}

function doneHtml() {
  const r = S.result, b = S.bin, dup = S.screen === 'dup';
  const others = r.others_count;
  const othersTxt = dup ? (others ? `Ty i ${others} ${plural(others, 'inna osoba zgłosiła', 'inne osoby zgłosiły', 'innych osób zgłosiło')} ten kosz.` : 'Zgłoszenie już było w drodze do dyspozytora.')
                        : (others ? `${others} ${plural(others, 'inna osoba też to zgłosiła', 'inne osoby też to zgłosiły', 'innych osób też to zgłosiło')}.` : 'Jesteś pierwszą osobą, która to zgłosiła.');
  const member = b.member
    ? `<div class="z-member"><span class="ic">${I.star('#2A1A63')}</span><span><strong>+10 pkt po potwierdzeniu przez ekipę</strong><br><small>${esc(b.member.nick)} · ${esc(b.member.district)}</small></span></div>`
    : `<div class="z-join">${I.star('#7B5FD0', 28)}<span>Zgłaszasz częściej? Dołącz do <strong>Przyjaciół Wróżki</strong> i zbieraj punkty.</span><a href="/program">Więcej</a></div>`;
  return `<div class="z-done">
    <div class="z-done-head">${I.bubble}<div><h2>${dup ? 'Wróżka już wie!' : 'Dziękujemy. Dyspozytor widzi zgłoszenie.'}</h2><span class="z-muted">${dup ? `Twoje naciśnięcie dołączyliśmy do zgłoszenia z ${esc(r.merged_with_at)}.` : 'Zgłoszenie podniosło priorytet tego kosza na trasie.'}</span></div></div>
    <div class="z-eta"><span><span class="z-muted">Przewidywany odbiór</span><b>ok. ${esc(r.eta)}</b></span><span class="lbl">Twoje zgłoszenie:<br>${OPTS[S.chosen].label}</span></div>
    <ol class="z-steps" aria-label="Status zgłoszenia" id="steps">
      <li><span class="z-dot done">${I.check}</span><b>Przyjęte</b><small>${esc(r.accepted_at)}</small></li>
      <li><span class="z-dot now"></span><b>Zaplanowane</b><small>${esc(r.route)}</small></li>
      <li class="todo"><span class="z-dot"></span><b>Opróżnione</b><small>po kursie</small></li>
    </ol>
    <span class="z-others">${I.people}${othersTxt}</span>
    ${member}
    <button type="button" class="z-btn" id="btn-status">Śledź status</button>
    <div class="z-grid2" style="margin-top:-4px"><a class="z-ghost" href="/zglos" style="display:flex;align-items:center;justify-content:center;text-decoration:none">Kosze w okolicy</a><button type="button" class="z-ghost" id="btn-again">Zgłoś inny kosz</button></div>
  </div>`;
}
const plural = (n, one, few, many) => n === 1 ? one : ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100) ? few : many);

function bind() {
  document.querySelectorAll('.z-opt:not(:disabled)').forEach(b => b.addEventListener('click', () => pick(b.dataset.kind)));
  $('btn-undo')?.addEventListener('click', () => { clearTimeout(S.timer); setScreen(S.bin.button_offline ? 'nosignal' : 'start'); });
  $('btn-retry')?.addEventListener('click', () => send());
  $('btn-relocate')?.addEventListener('click', locate);
  $('btn-again')?.addEventListener('click', () => { location.href = '/zglos'; });
  $('btn-status')?.addEventListener('click', trackStatus);
  $('btn-photo')?.addEventListener('click', e => {  // w demo zdjęcia analizuje ekipa (/ekipa); zdjęcie od mieszkańca jest w ROADMAPA
    e.currentTarget.insertAdjacentHTML('afterend', '<span class="z-muted" role="status" style="grid-column:1/-1;font-size:14px;line-height:20px">Zdjęcia w demo dodaje ekipa MPO przy opróżnieniu. Twoje zgłoszenie i tak trafi do dyspozytora.</span>');
    e.currentTarget.disabled = true;
  });
  $('btn-comment')?.addEventListener('click', () => { const c = prompt('Krótki komentarz dla ekipy (opcjonalnie):'); if (c) S.comment = c.slice(0, 200); });
}

// --- przepływ: dotknięcie → 1,5 s na „Cofnij” → POST ---
function pick(kind) {
  S.chosen = kind;
  setScreen('sending');
  clearTimeout(S.timer);
  S.timer = setTimeout(send, UNDO_MS);
}

async function send() {
  const body = { point_id: Z.pointId, kind: S.chosen, source: 'qr', client_id: clientId, created_at: new Date().toISOString() };
  if (S.pos && !Z.jury) Object.assign(body, { lat: S.pos.lat, lon: S.pos.lon, accuracy_m: Math.round(S.pos.acc) });
  if (Z.jury) body.jury = true;  // kosz jury: limit po telefonie, nie po IP sali
  if (S.comment) body.comment = S.comment;
  if (!navigator.onLine) return queue(body);
  let r, data;
  try {
    r = await fetch('/api/press', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: AbortSignal.timeout(8000) });
    data = await r.json();
  } catch (e) {
    return navigator.onLine ? setScreen('error') : queue(body);
  }
  handle(r.status, data);
}

function handle(status, data) {
  if (status === 200 && data.ok) { S.result = data; dequeue(); return setScreen(data.status === 'merged' ? 'dup' : 'sent'); }
  if (status === 403 && data.reason === 'too_far') { S.dist = data.distance_m ?? S.dist; return setScreen('far'); }
  if (status === 429) { S.retryAt = data.retry_at; return setScreen('limit'); }
  setScreen('error');
}

// kolejka offline: IndexedDB (zgłoszenie nie ginie po zamknięciu aplikacji) + Background Sync w service workerze;
// bez SW/Sync wysyłamy po zdarzeniu `online`
async function queue(body) {
  S.queuedAt = hhmm(new Date());
  try { await tfQueue.clear(); await tfQueue.add({ body, chosen: S.chosen, queuedAt: S.queuedAt }); } catch (e) { /* bez IndexedDB: tylko pamięć */ }
  setScreen('offline');
  try {  // `ready` nie rozwiązuje się bez SW, więc czekamy najwyżej 3 s
    const reg = await Promise.race([navigator.serviceWorker.ready, new Promise((_, rej) => setTimeout(rej, 3000))]);
    await reg.sync.register('tf-report');
  } catch (e) { /* brak SW albo Background Sync: wyśle zdarzenie online */ }
}
async function dequeue() { try { await tfQueue.clear(); } catch (e) { /* nic */ } }
async function flushQueue() {
  let items = [];
  try { items = await tfQueue.all(); } catch (e) { return; }
  const q = items.find(i => i.body.point_id === Z.pointId);
  if (!q) return;
  S.chosen = q.chosen; S.queuedAt = q.queuedAt;
  if (S.screen !== 'offline') setScreen('offline');
  if (!navigator.onLine) return;
  if (navigator.serviceWorker?.controller) navigator.serviceWorker.controller.postMessage('tf-flush');
  else send();
}
window.addEventListener('online', flushQueue);
navigator.serviceWorker?.addEventListener('message', e => {  // wynik wysyłki z kolejki przez SW
  const m = e.data;
  if (m?.type === 'tf-sent' && m.point_id === Z.pointId) { S.chosen = m.chosen || S.chosen; handle(m.status, m.data || {}); }
});

async function trackStatus() {
  const btn = $('btn-status');
  btn.disabled = true;
  try {
    const st = await (await fetch(`/api/zglos/status/${S.result.report_id}`)).json();
    const li = $('steps').children;
    if (st.emptied_at) { li[1].querySelector('.z-dot').className = 'z-dot done'; li[1].querySelector('.z-dot').innerHTML = I.check; li[2].className = ''; li[2].querySelector('.z-dot').className = 'z-dot done'; li[2].querySelector('.z-dot').innerHTML = I.check; li[2].querySelector('small').textContent = st.emptied_at; $('steps').style.setProperty('--done', '66.8%'); }
    btn.textContent = st.emptied_at ? `Opróżniono ${st.emptied_at}` : st.planned ? `Zaplanowane · ${st.run_label}` : 'Przyjęte · czeka na kurs';
  } catch (e) { btn.textContent = 'Brak połączenia. Spróbuj za chwilę.'; }
  finally { setTimeout(() => { btn.disabled = false; }, 1500); }
}

// --- start ---
async function init() {
  try {
    S.bin = await (await fetch(`/api/zglos/${Z.pointId}`)).json();
  } catch (e) {
    $('sheet').innerHTML = `<div class="z-error" role="alert"><b>Nie udało się pobrać danych kosza</b><span>Sprawdź połączenie i odśwież stronę.</span></div>`;
    return;
  }
  const b = S.bin;
  $('p-addr').textContent = `${b.address} · ${b.type} ${b.capacity_l} l`;
  $('p-fill').textContent = `${b.fill_pct} %`;
  $('p-eta').textContent = `ok. ${b.next_pickup}`;
  $('p-bar').style.width = `${Math.min(100, b.fill_pct)}%`;
  initMap(b);
  setScreen(b.button_offline ? 'nosignal' : 'start');
  flushQueue();
  locate();
  if ('serviceWorker' in navigator) navigator.serviceWorker.register(Z.sw, { scope: '/zglos' }).catch(() => { /* bez SW strona działa normalnie */ });
}
init();
