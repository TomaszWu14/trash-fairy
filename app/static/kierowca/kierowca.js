// PWA kierowcy: start zmiany → trasa → przystanek → podsumowanie.
// Migawka kursu w localStorage: po „Opróżniony” serwer planuje trasę od nowa (punkt z niej wypada), a kierowca ma mieć
// stałą numerację i trasę bez zasięgu. Nowe punkty z aktualnego planu pokazujemy jako różnicę („Nowy pilny punkt”).
const PREVIEW = !!window.KIEROWCA?.preview;  // ramka dla jury: zapisy wyłączone, osobna migawka
const UNDO_MS = 5000, POLL_MS = 30000, KEY = PREVIEW ? 'tf-kierowca-podglad' : 'tf-kierowca';
const LEVELS = [25, 50, 75, 100];
const ISSUES = { no_access: 'Nie da się podjechać', damaged: 'Kosz uszkodzony', blocked: 'Zablokowany dojazd', overflow: 'Odpady obok kosza' };
const STATE_LBL = { ok: 'w porządku', warn: 'zapełnia się', bad: 'do opróżnienia' };  // słownik: decyzja 18
const DAYS = ['niedz.', 'pon.', 'wt.', 'śr.', 'czw.', 'pt.', 'sob.'];
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const dec = v => String(v).replace('.', ',');
const I = {
  truck: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>',
  nav: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 11l18-8-8 18-2-8z"/></svg>',
  check: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>',
  block: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/></svg>',
  alert: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 3l10 18H2zM12 10v5M12 18h.01"/></svg>',
  cam: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3"/></svg>',
};

let live = null, online = navigator.onLine, kind = 'bin', pending = null, photo = null, map = null, queued = 0, needsLogin = false;
let snap = load();
let pos = null;  // położenie do flagi „daleko od kosza” (decyzja 28): bez zgody zapis i tak przechodzi
if (navigator.geolocation && !PREVIEW) navigator.geolocation.watchPosition(p => { pos = p.coords; }, () => {}, { enableHighAccuracy: true, maximumAge: 60000 });
const where = () => pos ? { lat: pos.latitude, lon: pos.longitude, accuracy_m: Math.round(pos.accuracy) } : {};
let screen = snap ? 'route' : 'start';
if (snap) kind = snap.kind;

function load() { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } }
function save() { try { snap ? localStorage.setItem(KEY, JSON.stringify(snap)) : localStorage.removeItem(KEY); } catch (e) { /* bez pamięci: działa do zamknięcia karty */ } }

const fleet = () => live?.fleets.find(f => f.kind === kind);
const status = s => snap.results[s.id]?.status;  // done | issue | skip | undefined
const nextStop = () => snap.stops.find(s => !status(s));
const count = st => snap.stops.filter(s => status(s) === st).length;
const newStops = () => {  // punkty z aktualnego planu, których nie ma w migawce
  const f = live?.fleets.find(x => x.kind === snap?.kind);
  if (!f || !snap) return [];
  const known = new Set(snap.stops.map(s => s.id));
  return f.stops.filter(s => !known.has(s.id));
};
const levelOf = s => LEVELS.reduce((best, l) => Math.abs(l - s.level) < Math.abs(best - s.level) ? l : best, LEVELS[0]);
const mk = s => `<span class="mk st-${s.fresh ? 'fresh' : s.state}" aria-hidden="true"></span>`;
const minutes = f => Math.round(f.stops.length * 3 + f.km * 3);  // szacunek: 3 min na przystanek + 20 km/h

// --- ekrany ---
function render(focus = false) {
  if (map) { map.remove(); map = null; }
  $('app').innerHTML = { start: viewStart, route: viewRoute, stop: viewStop, summary: viewSummary }[screen]();
  if (screen === 'route') drawMap();
  $('head-t').textContent = screen === 'stop' ? `Przystanek ${cur().order} / ${snap.stops.length}`
    : screen === 'route' ? `Kurs ${snap.run_label.slice(-5)} · ${dec(snap.km)} km` : 'Trasa · kierowca';
  if (focus) { $('app').focus(); window.scrollTo(0, 0); }
}
function go(s) { screen = s; render(true); }
const cur = () => snap.stops.find(s => s.id === snap.cur) || nextStop() || snap.stops[0];

function viewStart() {
  if (!live) return `<p class="k-muted">${online ? 'Ładuję kurs…' : 'Brak zasięgu i brak pobranego kursu. Otwórz aplikację w bazie, gdzie jest sieć.'}</p>`;
  const f = fleet(), urgent = f.stops.filter(s => s.state === 'bad').length;
  return `
    <section class="k-card" aria-labelledby="run-h">
      <div class="k-row"><span class="k-ico">${I.truck}</span>
        <div><h1 class="k-title" id="run-h">Kurs ${f.run_label.slice(-5)}</h1><span class="k-sub">${esc(f.vehicle)} · ${esc(f.label)}</span></div></div>
      <div class="k-stats">
        <div><b>${f.stops.length}</b><span>punktów</span></div>
        <div><b>${dec(f.km)}</b><span>km</span></div>
        <div><b>${Math.floor(minutes(f) / 60)} h ${minutes(f) % 60}</b><span>min, szacunek</span></div>
      </div>
      <dl class="k-facts">
        <dt>Start i koniec</dt><dd>${esc(live.depot.name)}</dd>
        ${f.stops.length ? `<dt>Pierwszy przystanek</dt><dd>${esc(f.stops[0].name)}</dd>` : ''}
        <dt>Pilne na trasie</dt><dd>${urgent} ${urgent === 1 ? 'przepełniony' : 'przepełnionych'}</dd>
      </dl>
    </section>
    <section class="k-card"><div class="k-row">${mk({ state: 'ok' })}<div><b>Trasa zostaje w telefonie</b><br>
      <span class="k-sub">Po rozpoczęciu lista i kolejność działają bez zasięgu; opróżnienia wyślemy, gdy sieć wróci.</span></div></div></section>
    ${f.stops.length ? '<button type="button" class="k-btn k-btn-primary k-btn-xl" id="begin">Rozpocznij trasę</button>'
                     : '<p class="k-muted">Na ten kurs nie trzeba nikogo wysyłać.</p>'}`;
}

function viewRoute() {
  const next = nextStop(), fresh = newStops(), handled = snap.stops.length - snap.stops.filter(s => !status(s)).length;
  const rest = snap.stops.filter(s => s !== next);
  return `
    <div class="k-map"><div id="map" role="region" aria-label="Mapa trasy. Kolejność przystanków jest też na liście poniżej."></div>
      <span class="k-map-tag">${next ? `Przystanek ${next.order} / ${snap.stops.length}` : 'Trasa zakończona'} · ${handled} obsłużone</span></div>
    ${fresh.length ? `<div class="k-new" role="status"><span>Nowy pilny punkt na kursie · +${fresh.length}</span>
      <button type="button" id="add-new">Dodaj na koniec</button></div>` : ''}
    ${next ? `
    <section class="k-card next" aria-labelledby="next-h">
      <p class="k-eyebrow">Następny przystanek</p>
      <div class="k-row">${mk(next)}<div><h1 class="k-title" id="next-h">${esc(next.name)}</h1>
        <span class="k-sub">${STATE_LBL[next.state]}${next.fresh ? ', świeże zgłoszenie' : ''}</span></div></div>
      <div class="k-chips"><span>przewidywane <b>${next.level}%</b></span><span>${esc(next.reason)}</span></div>
      <div class="k-row">
        <a class="k-btn k-btn-primary" href="https://www.google.com/maps/dir/?api=1&destination=${next.lat},${next.lon}&travelmode=driving" target="_blank" rel="noopener">${I.nav}Nawiguj</a>
        <button type="button" class="k-btn" data-open="${next.id}">Jestem</button>
      </div>
    </section>` : `
    <section class="k-card"><h1 class="k-title">Wszystkie przystanki obsłużone</h1>
      <button type="button" class="k-btn k-btn-primary k-btn-xl" data-go="summary">Podsumowanie zmiany</button></section>`}
    <section class="k-card" aria-labelledby="list-h"><h2 class="k-eyebrow" id="list-h">Cała trasa</h2>
      <ul class="k-list">${rest.map(s => `<li>
        <span class="k-num ${status(s) || (snap.kind === 'shelter' ? 'shelter' : '')}" aria-hidden="true">${status(s) ? '' : s.order}</span>
        <span class="name"><b>${esc(s.name)}</b><small>${s.order}. ${statusText(s)}</small></span>
        <button type="button" class="k-btn" data-open="${s.id}" aria-label="Otwórz przystanek ${s.order}: ${esc(s.name)}">Otwórz</button></li>`).join('')}</ul>
    </section>
    <div class="k-bar"><button type="button" class="k-btn" data-go="summary">Zakończ trasę</button></div>`;
}
function statusText(s) {
  const r = snap.results[s.id];
  if (!r) return `przewidywane ${s.level}%`;
  return r.status === 'done' ? `opróżniony, zastany ${r.level}%` : r.status === 'issue' ? `problem: ${ISSUES[r.kind].toLowerCase()}` : 'pominięty';
}

function viewStop() {
  const s = cur(), def = levelOf(s);
  return `
    <div class="k-row">${mk(s)}<div><h1 class="k-title">${esc(s.name)}</h1>
      <span class="k-sub">${snap.kind === 'shelter' ? 'altana osiedlowa' : 'kosz uliczny'} · ${STATE_LBL[s.state]}</span></div></div>
    <div class="k-chips"><span>przewidywane <b>${s.level}%</b></span><span>${esc(s.reason)}</span>${s.fresh ? '<span>świeże zgłoszenie mieszkańca</span>' : ''}</div>
    ${snap.results[s.id] ? `<p class="k-muted">Zapisano: ${statusText(s)}. Możesz zapisać ponownie.</p>` : ''}
    <fieldset class="k-levels"><legend>Poziom zastany przed opróżnieniem (domyślnie z prognozy)</legend><div>${LEVELS.map(l => `
      <label><input type="radio" name="level" value="${l}"${l === def ? ' checked' : ''}><span>${l}%</span></label>`).join('')}</div></fieldset>
    <label class="k-photo">${I.cam}<span id="photo-t">${photo ? `Zdjęcie: ${esc(photo.name)}` : 'Dodaj zdjęcie (opcjonalnie)'}</span>
      <input type="file" id="photo" accept="image/jpeg,image/png,image/webp" capture="environment"></label>
    <div class="k-actions">
      <button type="button" class="k-act k-act-ok" data-done="${s.id}">${I.check}<span><b>Opróżniony</b><small>zeruje szacunek, zamyka zgłoszenia</small></span></button>
      <button type="button" class="k-act" data-issue="no_access">${I.block}<span><b>Nie da się podjechać</b><small>zaparkowane auto, remont, zamknięta brama</small></span></button>
      <button type="button" class="k-act" id="problem" aria-expanded="false" aria-controls="problems">${I.alert}<span><b>Problem</b><small>uszkodzony · zablokowany dojazd · odpady obok</small></span></button>
      <div class="k-sub-acts" id="problems" hidden>${['damaged', 'blocked', 'overflow'].map(k => `
        <button type="button" class="k-btn" data-issue="${k}">${ISSUES[k]}</button>`).join('')}</div>
    </div>
    <div class="k-bar"><button type="button" class="k-btn" data-go="route">← Trasa</button>
      <button type="button" class="k-btn" data-skip="${s.id}">Pomiń →</button></div>`;
}

function viewSummary() {
  const tiles = [['done', 'opróżnionych'], ['issue', 'z problemem'], ['skip', 'pominiętych']];
  const left = snap.stops.filter(s => !status(s)).length;
  return `
    <h1 class="k-title">Podsumowanie zmiany</h1>
    <p class="k-muted">Kurs ${esc(snap.run_label)} · ${esc(snap.vehicle)} · plan ${dec(snap.km)} km</p>
    <section class="k-card"><div class="k-stats">${tiles.map(([k, l]) => `<div><b class="k-sum">${count(k)}</b><span>${l}</span></div>`).join('')}</div>
      <p class="k-muted">${left ? `Nieobsłużone: ${left}.` : 'Wszystkie przystanki obsłużone.'} ${queued ? `W kolejce do wysłania: ${queued}. Wyślemy, gdy wróci zasięg.` : 'Wszystko wysłane do dyspozytora.'}</p></section>
    <button type="button" class="k-btn k-btn-primary k-btn-xl" id="finish">Zakończ zmianę</button>
    <button type="button" class="k-btn" data-go="route">Wróć do trasy</button>`;
}

// --- mapa (Leaflet, przebieg OSRM z migawki) ---
function drawMap() {
  map = L.map('map', { zoomControl: false });
  const attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
  const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, className: 'tf-tiles', attribution }).addTo(map);
  let errors = 0;  // bez zasięgu i bez kafelków w cache: statyczny podkład SVG obszaru demo
  tiles.on('tileerror', () => { if (++errors === 3) { map.removeLayer(tiles);
    L.imageOverlay('/static/img/krakow-basemap.svg', [[50.04095, 19.912], [50.07005, 19.992]], { attribution }).addTo(map); } });
  const color = getComputedStyle(document.documentElement).getPropertyValue(snap.kind === 'shelter' ? '--route2' : '--route').trim();
  if (snap.geometry?.out?.length) L.polyline(snap.geometry.out, { color, weight: 5, opacity: .85, interactive: false }).addTo(map);
  const next = nextStop();
  for (const s of snap.stops) {
    const st = status(s), isNext = s === next;
    L.marker([s.lat, s.lon], { keyboard: false, interactive: false, zIndexOffset: isNext ? 1000 : 0,
      icon: L.divIcon({ className: '', iconSize: isNext ? [38, 38] : [30, 30],
        html: `<span class="k-pin ${isNext ? 'next' : st || ''}" aria-hidden="true">${st === 'done' ? '✓' : st === 'issue' ? '!' : s.order}</span>` }) }).addTo(map);
  }
  const focus = snap.stops.filter(s => !status(s)).slice(0, 6);
  map.fitBounds(L.latLngBounds((focus.length ? focus : snap.stops).map(s => [s.lat, s.lon])), { padding: [36, 36], maxZoom: 17 });
}

// --- akcje: zapis lokalnie od razu, wysyłka po 5 s (Cofnij), kolejka IndexedDB gdy brak sieci ---
function act(s, result, item, msg) {
  if (PREVIEW) {  // jury widzi całą aplikację, ale nikt z sali nie zafałszuje danych
    $('toast').innerHTML = '<span>W podglądzie zapisy są wyłączone. Zaloguj się jako <b>driver_bin</b>, żeby zapisać.</span>';
    $('toast').hidden = false;
    setTimeout(() => { $('toast').hidden = true; }, 4000);
    return;
  }
  if (pending) commit();
  snap.results[s.id] = result;
  snap.cur = null;
  save();
  photo = null;
  pending = { id: s.id, item, timer: setTimeout(commit, UNDO_MS) };
  $('toast').innerHTML = `<span>${esc(msg)}</span><button type="button" id="undo">Cofnij</button>`;
  $('toast').hidden = false;
  go(nextStop() ? 'route' : 'summary');
}
async function commit() {
  if (!pending) return;
  const { item, timer } = pending;
  clearTimeout(timer);
  pending = null;
  $('toast').hidden = true;
  if (item) { await tfQueue.add(item); flush(); }
  updateNet();
}
function undo() {
  if (!pending) return;
  clearTimeout(pending.timer);
  delete snap.results[pending.id];
  snap.cur = pending.id;
  pending = null;
  save();
  $('toast').hidden = true;
  go('stop');
}

async function sendAll() {  // ta sama wysyłka co w sw.js (flush), gdy strona nie ma service workera
  for (const it of await tfQueue.all()) {
    const body = new FormData();
    for (const [k, v] of Object.entries(it.fields)) body.append(k, v);
    if (it.photo) body.append('photo', it.photo, it.photoName || 'zdjecie.jpg');
    const r = await fetch(it.url, { method: 'POST', body });
    if (r.status === 401 || r.status === 403) { needsLogin = true; return; }  // sesja wygasła: zapis zostaje w kolejce
    if (r.status >= 500) throw new Error('server');
    await tfQueue.remove(it.id);
  }
}
async function flush() {
  const sw = navigator.serviceWorker?.controller;
  if (sw) {
    sw.postMessage('tf-flush');
    try { await (await navigator.serviceWorker.ready).sync?.register('tf-kierowca'); } catch (e) { /* bez Background Sync: wyślemy po „online” */ }
  } else {
    try { await sendAll(); } catch (e) { /* brak sieci: spróbujemy po zdarzeniu online */ }
  }
  updateNet();
}

async function updateNet() {
  try { queued = (await tfQueue.all()).length; } catch (e) { queued = 0; }
  const net = $('net');
  net.classList.toggle('queue', online && queued > 0);
  net.classList.toggle('off', !online || (needsLogin && queued > 0));
  $('net-t').innerHTML = needsLogin && queued ? `<a href="/logowanie?next=/kierowca">Zaloguj się ponownie</a> · ${queued} czeka`
    : esc(!online ? `Offline${queued ? ` · ${queued} w kolejce` : ''}` : queued ? `${queued} w kolejce` : 'Online · zsynchronizowano');
}

async function refresh() {
  try {
    const r = await fetch(PREVIEW ? '/api/kierowca/kurs?podglad=1' : '/api/kierowca/kurs');  // tylko kurs floty z loginu (decyzja 2)
    if (r.status === 401) {
      if (!snap) { location.href = '/logowanie?next=/kierowca'; return; }
      needsLogin = true;  // z zapisanym kursem pracujemy dalej offline, zapisy czekają na ponowne logowanie
      throw new Error('401');
    }
    if (!r.ok) throw new Error(r.status);
    const before = newStops().length;
    const d = await r.json();
    live = { depot: d.depot, now: d.now, fleets: [d.fleet] };
    kind = d.fleet.kind;
    needsLogin = false;
    if (snap && snap.kind !== kind) { snap = null; save(); screen = 'start'; }  // inny login na tym telefonie
    online = true;
    const now = new Date(live.now);
    $('clock').textContent = `${DAYS[now.getDay()]} ${live.now.slice(11, 16)}`;
    if (screen === 'start' || (screen === 'route' && newStops().length !== before)) render();
  } catch (e) {
    online = false;
    if (screen === 'start' && !live) render();
  }
  updateNet();
}

// --- zdarzenia ---
document.addEventListener('click', e => {
  const t = e.target.closest('button, a');
  if (!t) return;
  if (t.id === 'undo') return undo();
  if (t.id === 'begin') {
    const f = fleet();
    snap = { kind, label: f.label, vehicle: f.vehicle, run_label: f.run_label, km: f.km, geometry: f.geometry,
             stops: f.stops.map(s => ({ ...s })), results: {}, cur: null };
    save();
    return go('route');
  }
  if (t.id === 'add-new') {
    for (const s of newStops()) snap.stops.push({ ...s, order: snap.stops.length + 1 });
    save();
    return render();
  }
  if (t.dataset.open) { snap.cur = Number(t.dataset.open); photo = null; return go('stop'); }
  if (t.dataset.go) return go(t.dataset.go);
  if (t.id === 'problem') {
    const open = t.getAttribute('aria-expanded') !== 'true';
    t.setAttribute('aria-expanded', open);
    $('problems').hidden = !open;
    return;
  }
  const s = screen === 'stop' ? cur() : null;
  if (t.dataset.done && s) {
    const level = Number(document.querySelector('input[name=level]:checked').value);
    return act(s, { status: 'done', level }, { url: '/api/emptying', fields: { point_id: s.id, level, ...where() }, photo, photoName: photo?.name },
               `Opróżniony: ${s.name} (${level}%)`);
  }
  if (t.dataset.issue && s) {
    const k = t.dataset.issue;
    return act(s, { status: 'issue', kind: k }, { url: '/api/stop-issue', fields: { point_id: s.id, kind: k, ...where() }, photo, photoName: photo?.name },
               `${ISSUES[k]}: ${s.name}`);
  }
  if (t.dataset.skip && s) return act(s, { status: 'skip' }, { url: '/api/stop-issue', fields: { point_id: s.id, kind: 'skip' } }, `Pominięto: ${s.name}`);  // pominięcie widzi dyspozytor (decyzja 30)
  if (t.id === 'finish') { commit(); snap = null; save(); return go('start'); }
});
document.addEventListener('change', e => {
  if (e.target.id !== 'photo') return;
  photo = e.target.files[0] || null;
  $('photo-t').textContent = photo ? `Zdjęcie: ${photo.name}` : 'Dodaj zdjęcie (opcjonalnie)';
});
document.addEventListener('visibilitychange', () => { if (document.hidden) commit(); });  // zamknięcie aplikacji nie gubi zapisu
addEventListener('online', () => { online = true; flush(); });
addEventListener('offline', () => { online = false; updateNet(); });
navigator.serviceWorker?.addEventListener('message', e => { if (e.data?.type === 'tf-flushed') updateNet(); });

if ('serviceWorker' in navigator && !PREVIEW) navigator.serviceWorker.register('/kierowca/sw.js', { scope: '/kierowca' }).catch(() => {});
render();
refresh();
flush();
setInterval(refresh, POLL_MS);
