// Widok C „Pokaz dla jury”. Dane z tych samych endpointów co panel dyspozytora; tu tylko prezentacja.
const POLL_MS = 2000;
const RANK = { full: 5, report: 4, near: 3, warn: 2, ok: 1 };
const LBL = { ok: 'w porządku', near: 'zapełnia się', full: 'do opróżnienia', report: 'zgłoszenie mieszkańca', warn: 'sprawdź przycisk' };  // słownik: decyzja 18
const DAYS = ['niedz.', 'pon.', 'wt.', 'śr.', 'czw.', 'pt.', 'sob.'];
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const plural = (n, one, few, many) => n === 1 ? one : ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100) ? few : many);
const hhmm = d => d.toTimeString().slice(0, 5);
const fmt = v => Number(v).toLocaleString('pl-PL');

let step = 3, version = null, now = null, points = [], routes = null, stopOf = {}, lastReport = null, prevFresh = new Set();

// --- mapa: OSM wyciszony filtrem CSS (CARTO wymaga już klucza API) → statyczny podkład SVG offline ---
const map = L.map('map', { zoomControl: false }).setView([50.0585, 19.958], 14);
L.control.zoom({ position: 'bottomright' }).addTo(map);
const OSM_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
const tiles = [['https://tile.openstreetmap.org/{z}/{x}/{y}.png', OSM_ATTR]];
function useTiles(i) {
  if (i >= tiles.length) {
    L.imageOverlay(window.BASEMAP_SVG, [[50.04095, 19.912], [50.07005, 19.992]], { attribution: OSM_ATTR }).addTo(map);
    return;
  }
  let errors = 0;
  const layer = L.tileLayer(tiles[i][0], { maxZoom: 19, attribution: tiles[i][1], className: 'tf-tiles' }).addTo(map);
  layer.on('tileerror', () => { if (++errors === 3) { map.removeLayer(layer); useTiles(i + 1); } });
}
useTiles(0);

const North = L.Control.extend({ onAdd: () => Object.assign(L.DomUtil.create('div', 'glass c-north'), {
  innerHTML: '<svg width="20" height="28" viewBox="0 0 20 28" role="img" aria-label="Północ"><path d="M10 2 L16 20 L10 16 L4 20 Z" fill="#0E1222"/>'
    + '<text x="10" y="27" text-anchor="middle" font-size="8" font-weight="700" fill="#0E1222">N</text></svg>' }) });
new North({ position: 'topright' }).addTo(map);
L.control.scale({ position: 'topright', imperial: false, maxWidth: 120 }).addTo(map);

const zoneLayer = L.layerGroup().addTo(map);
const routeLayer = L.layerGroup().addTo(map);
const markers = {};
const cluster = L.markerClusterGroup({
  showCoverageOnHover: false, spiderfyOnMaxZoom: true, maxClusterRadius: 70, disableClusteringAtZoom: 17,
  iconCreateFunction: c => {
    const kids = c.getAllChildMarkers().map(m => m.tf), lit = kids.filter(highlighted);
    // w krokach 1–2 kolor klastra = najgorszy z wyróżnionych, żeby czerwień nie zagłuszała predykcji
    const worst = (lit.length ? lit : kids).reduce((w, p) => RANK[p.look] > RANK[w] ? p.look : w, 'ok');
    const n = kids.length, size = n >= 20 ? 60 : n >= 9 ? 50 : 44;
    const dim = !lit.length;
    const orders = step === 3 ? kids.filter(p => stopOf[p.id]).map(p => stopOf[p.id]) : [];
    return L.divIcon({
      className: 'tf-icon', iconSize: [size, size],
      html: `<span class="cl cv-${worst}${dim ? ' dim' : ''}" role="img" aria-label="${n} punktów, najgorszy stan: ${LBL[worst]}">${n}`
        + `<span class="mk mk-sm st-${worst}"></span>${stopPill(orders)}</span>`,
    });
  },
}).addTo(map);

function stopPill(stops) {
  if (!stops.length) return '';
  const nums = stops.map(s => s.order).sort((a, b) => a - b);
  const label = nums.length === 1 ? nums[0] : `${nums[0]}–${nums[nums.length - 1]}`;
  return `<span class="stop${stops[0].kind === 'shelter' ? ' shelter' : ''}">${label}</span>`;
}

// stan na mapie: zgłoszenie > przepełniony > sprawdź przycisk > zbliża się > ok
const look = p => p.fresh ? 'report' : p.state === 'bad' ? 'full' : p.check_button ? 'warn' : p.state === 'warn' ? 'near' : 'ok';
const runOf = kind => routes?.fleets.find(f => f.kind === kind);
const atRisk = p => {  // ta sama reguła co planer tras: bez najbliższego kursu przekroczy 85% przed kolejnym
  const f = runOf(p.kind);
  return p.state === 'warn' && p.crossing && f && new Date(p.crossing) < new Date(f.following_at);
};
const highlighted = p => step === 1 ? p.state === 'bad' : step === 2 ? atRisk(p) : true;

function markerIcon(p) {
  const dim = !highlighted(p);
  const pulse = ['full', 'report'].includes(p.look) && !dim;
  const label = p.look !== 'ok' || p.kind === 'shelter';
  return L.divIcon({
    className: 'tf-icon', iconSize: [28, 28],
    html: `<span class="mk st-${p.look}${p.kind === 'shelter' ? ' alt' : ''}${dim ? ' dim' : ''}">`
      + (pulse ? '<span class="pulse"></span>' : '')
      + (label && !dim ? `<span class="mk-lbl">${esc(p.name.replace(/^(Kosz|Altana) /, p.kind === 'shelter' ? 'Altana ' : ''))}</span>` : '')
      + (step === 3 && stopOf[p.id] ? stopPill([stopOf[p.id]]) : '') + '</span>',
  });
}

function renderMarkers() {
  for (const p of points) {
    const title = `${p.kind === 'shelter' ? 'Altana' : 'Kosz'} ${p.name}: ${LBL[p.look]}, ${p.value}%`;
    if (markers[p.id]) {
      markers[p.id].tf = p;
      markers[p.id].setIcon(markerIcon(p));
    } else {
      const m = L.marker([p.lat, p.lon], { icon: markerIcon(p), title, alt: title, keyboard: true });
      m.tf = p;
      m.bindPopup(() => `<b>${esc(m.tf.name)}</b><br>${LBL[m.tf.look]} · ${m.tf.value}%<br>${esc(m.tf.reason)}`
        + (m.tf.crossing ? `<br>85% ok. ${m.tf.crossing.slice(11, 16)}` : '') + (stopOf[m.tf.id] ? ` · przystanek ${stopOf[m.tf.id].order}` : '')
        + `<br><a href="/dyspozytor?point=${m.tf.id}">Szczegóły w panelu →</a> · <a href="/zglos/${m.tf.id}" target="_blank" rel="noopener">Zgłoś z telefonu ↗</a>`);
      markers[p.id] = m;
      cluster.addLayer(m);
    }
  }
  cluster.refreshClusters();
}

function renderZones(events) {
  zoneLayer.clearLayers();
  // tylko trwające, nie małe wydarzenia — inaczej centrum tonie w okręgach z Karnetu (pełna lista w panelu dyspozytora)
  for (const e of events.filter(e => e.active && e.scale !== 'small')) {
    L.circle([e.lat, e.lon], { radius: e.radius_m, color: '#C2570C', weight: 2, dashArray: '6 6', fillColor: '#C2570C',
                               fillOpacity: e.active ? 0.1 : 0.04, interactive: false }).addTo(zoneLayer);
    L.marker([e.lat + e.radius_m / 111320, e.lon], { interactive: false, keyboard: false,
      icon: L.divIcon({ className: 'tf-icon', iconSize: [0, 0], html: `<span class="zone-l">Wydarzenie · ${esc(e.name)}</span>` }) }).addTo(zoneLayer);
  }
}

// --- trasy po ulicach (OSRM z serwera, fallback: linia prosta) ---
function renderRoutes() {
  routeLayer.clearLayers();
  stopOf = {};
  for (const f of routes.fleets) for (const s of f.stops) stopOf[s.id] = { order: s.order, kind: f.kind };
  const d = routes.depot;
  L.marker([d.lat, d.lon], { keyboard: false, title: d.name, zIndexOffset: 1000,
    icon: L.divIcon({ className: 'tf-icon', iconSize: [40, 40], iconAnchor: [20, 20], html: '<span class="base"><i>'
      + '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>'
      + '</i><span>Baza MPO<br><small>ul. Nowohucka 1</small></span></span>' }) }).addTo(routeLayer);
  for (const f of routes.fleets) {
    if (!f.stops.length) continue;
    const g = f.geometry, color = f.kind === 'bin' ? '#0050B5' : '#8E2C8C';
    L.polyline(g.back, { color, weight: 2, dashArray: '3 6', opacity: 0.7, interactive: false }).addTo(routeLayer);
    L.polyline(g.out, { color: '#fff', weight: f.kind === 'bin' ? 10 : 8, lineJoin: 'round', interactive: false }).addTo(routeLayer);
    L.polyline(g.out, { color, weight: f.kind === 'bin' ? 5 : 4, dashArray: f.kind === 'bin' ? null : '10 6', interactive: false }).addTo(routeLayer);
    if (f.kind === 'bin') L.polyline(g.out, { color: '#fff', weight: 3, className: 'flow', interactive: false }).addTo(routeLayer);
  }
  const bin = runOf('bin'), shelter = runOf('shelter');
  $('lg-bin').textContent = `Kosze ${bin.run_label.slice(-5)}`;
  $('lg-shelter').textContent = `Altany ${shelter.run_label}`;
}

// --- kroki ---
const CAPTION = {
  1: () => { const n = points.filter(p => p.state === 'bad').length; return `Teraz: ${n} ${plural(n, 'punkt przepełniony', 'punkty przepełnione', 'punktów przepełnionych')}`; },
  2: () => { const n = points.filter(atRisk).length; return `${n} ${plural(n, 'punkt przekroczy', 'punkty przekroczą', 'punktów przekroczy')} 85% przed kolejnym kursem`; },
  3: () => {
    const f = runOf('bin');
    if (!f) return 'Trasa na najbliższy kurs';
    return `Kurs ${f.run_label.slice(-5)} · kolejność odbioru 1→${f.stops.length} · `
      + (f.geometry.approx ? 'przybliżenie w linii prostej' : 'przebieg po ulicach (OSRM)');
  },
  4: () => 'Przed i po: 4 tygodnie',
};

function setStep(n) {
  step = n;
  document.querySelectorAll('.step').forEach(b => {
    const k = Number(b.dataset.step);
    b.setAttribute('aria-pressed', k === n);
    b.querySelector('.bar').classList.toggle('on', k <= n);
  });
  $('cap-n').textContent = n;
  $('cap-t').textContent = CAPTION[n]();
  $('effect').hidden = n !== 4;
  n === 3 ? routeLayer.addTo(map) : map.removeLayer(routeLayer);
  renderMarkers();
}
document.querySelectorAll('.step').forEach(b => b.addEventListener('click', () => setStep(Number(b.dataset.step))));

function renderCards() {
  // karta 1 (decyzja 19): „przepełniony” tylko przy szacunku ≥ 100%, reszta stanu bad to „do opróżnienia”
  const badList = points.filter(p => p.state === 'bad'), over = badList.filter(p => p.value >= 100), risk = points.filter(atRisk).length;
  const bad = over.length, rest = badList.length - over.length;
  $('c1').textContent = (rest ? `+${rest} do opróżnienia przed kursem. ` : '')
    + (badList.length ? badList.slice(0, 3).map(p => p.name.replace(/^(Kosz|Altana) /, '')).join(', ') + (badList.length > 3 ? '…' : '')
                      : 'Teraz żaden punkt nie wymaga opróżnienia.');
  $('v1').textContent = bad;
  $('u1').textContent = plural(bad, 'przepełniony teraz', 'przepełnione teraz', 'przepełnionych teraz');
  $('v2').textContent = risk;
  $('u2').textContent = plural(risk, 'zagrożony', 'zagrożone', 'zagrożonych');
  const f = runOf('bin');
  if (f) {
    $('v3').textContent = `${String(f.km).replace('.', ',')} km`;
    $('u3').textContent = `${f.stops.length} pkt`;
    const run = new Date(f.run_at);
    const day = run.toDateString() === now.toDateString() ? 'Dziś' : 'Jutro';
    $('c3').textContent = `${day} ${hhmm(run)}, ${f.vehicle}. Altany: ${runOf('shelter').stops.length} pkt.`;
  }
  $('cap-t').textContent = CAPTION[step]();
}

// --- krok 4: przed i po (te same liczby co w panelu, bez upiększania) ---
async function loadComparison() {
  const c = await (await fetch('/api/comparison')).json();
  const sum = (v, k) => v.bin[k] + v.shelter[k];
  const card = (title, key, unit, why) => {
    const a = sum(c.fixed, key), b = sum(c.fairy, key), pct = a ? Math.round(100 * (b - a) / a) : 0;
    return { html: `<div class="c-eff"><h3>${title}</h3><b class="${pct <= 0 ? 'better' : 'worse'}">${pct > 0 ? '+' : pct < 0 ? '−' : '±'}${Math.abs(pct)} %</b>`
      + `<p>Stały harmonogram: <strong>${fmt(Math.round(a))}${unit}</strong></p><p>Trash Fairy: <strong>${fmt(Math.round(b))}${unit}</strong></p>`
      + (why ? `<p class="why">${why}</p>` : '') + '</div>', pct };
  };
  // dwie uczciwe liczby zamiast uśrednionego „−16%” (decyzja 41): każda przy swoim problemie
  const empty = `<div class="c-eff"><h3>Puste przyjazdy do koszy</h3><b class="better">${c.fixed.bin.empty_share}% → ${c.fairy.bin.empty_share}%</b>`
    + `<p>Ta sama czystość ulic, o połowę mniej jazdy do pustych koszy.</p>`
    + `<p class="why">Godziny przepełnienia koszy bez zmian (${fmt(c.fixed.bin.overflow_hours)} → ${fmt(c.fairy.bin.overflow_hours)} h): oszczędzamy, nie pogarszając.</p></div>`;
  const shelters = `<div class="c-eff"><h3>Przepełnione altany</h3><b class="better">${fmt(c.fixed.shelter.overflow_hours)} h → ${fmt(c.fairy.shelter.overflow_hours)} h</b>`
    + `<p>Koniec worków domowych wynoszonych z altan do koszy ulicznych.</p></div>`;
  const km = card('Kilometry tras', 'km', ' km', 'Więcej km, bo częściej jeździmy do przeciążonych altan.');
  const visits = card('Wizyty przy punktach', 'visits', '',
    `Puste przyjazdy do koszy: ${c.fixed.bin.empty_share}% → ${c.fairy.bin.empty_share}%.`);
  $('effect-grid').innerHTML = empty + shelters + km.html + visits.html;
  $('v4').textContent = `${c.fixed.bin.empty_share}% → ${c.fairy.bin.empty_share}%`;
  $('c4').textContent = `pustych przyjazdów · altany ${fmt(c.fixed.shelter.overflow_hours)} → ${fmt(c.fairy.shelter.overflow_hours)} h przepełnień`;
}

// --- prawa kolumna ---
function renderQr() {
  const url = (window.PUBLIC_URL || location.origin) + '/zglos/18?jury=1';  // zawsze kosz 18 (decyzja 13)
  const qr = qrcode(0, 'M');
  qr.addData(url);
  qr.make();
  $('qr').innerHTML = qr.createSvgTag({ cellSize: 4, margin: 0, scalable: true });
  $('jury-url').href = url;
  $('jury-url').textContent = url.replace(/^https?:\/\//, '');
  $('qr-warn').hidden = !(['localhost', '127.0.0.1'].includes(location.hostname) && !window.PUBLIC_URL);
}

function renderLastReport() {
  const fresh = points.filter(p => p.fresh);
  const appeared = fresh.find(p => !prevFresh.has(p.id));
  if (appeared) lastReport = appeared.name;
  prevFresh = new Set(fresh.map(p => p.id));
  $('last-report').textContent = `Ostatnie: ${lastReport ?? 'jeszcze nikt'}`;
}

const URGENCY = [[3, 'crit', 'Krytyczne'], [6, 'high', 'Wysokie'], [24, 'mid', 'Średnie'], [Infinity, 'low', 'Niskie']];
const dur = ms => { const m = Math.max(0, Math.round(ms / 60000)); return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${m % 60} min`; };

function renderRisk() {
  const top = points.filter(p => p.state !== 'bad' && p.crossing).sort((a, b) => a.crossing.localeCompare(b.crossing)).slice(0, 3);
  if (!top.length) { $('risk').innerHTML = '<li class="foot">Żaden punkt nie przekroczy 85% w ciągu 24 h.</li>'; return; }
  $('risk').innerHTML = top.map(p => {
    const cross = new Date(p.crossing), hours = (cross - now) / 3.6e6, [, cls, label] = URGENCY.find(([h]) => hours < h);
    const f = runOf(p.kind), run = new Date(f.run_at), end = new Date(f.following_at);
    const onRoute = stopOf[p.id];
    const span = Math.max(end - now, cross - now, run - now) || 1, pos = t => Math.min(100, Math.max(0, 100 * (t - now) / span));
    const pickup = onRoute ? run : end;  // bez przystanku najbliższy możliwy odbiór to kolejny kurs
    const gap = pickup - cross;
    return `<li>
      <span class="row"><span class="tag tag-${cls}">${label}</span><span class="name">${esc(p.name)}</span></span>
      <span class="row"><span class="when">85% ok. ${hhmm(cross)}</span><span class="in">za ${dur(cross - now)}</span></span>
      <span class="tl" role="img" aria-label="Oś czasu: teraz, ${onRoute ? `odbiór ${hhmm(run)}, ` : ''}próg 85% o ${hhmm(cross)}">
        ${gap > 0 ? `<span class="tl-risk" style="left:${pos(cross)}%;right:${100 - pos(pickup)}%"></span>` : ''}
        ${onRoute ? `<span class="tl-plan" style="left:${pos(run)}%"></span>` : ''}
        <span class="tl-85" style="left:${pos(cross)}%"></span></span>
      <span class="tl-ends" aria-hidden="true"><span>teraz</span><span>kolejny kurs ${f.following_label}</span></span>
      <span class="foot">${gap > 0 ? `Bez odbioru ${dur(gap)} powyżej 85% · ` : 'Odbiór przed progiem · '}`
      + `${onRoute ? `<strong>w trasie ${hhmm(run)}, przystanek ${onRoute.order}</strong>` : 'poza najbliższym kursem'}</span>
    </li>`;
  }).join('');
}

// --- dane i polling (ten sam mechanizm co panel dyspozytora) ---
async function apply(data) {
  version = data.version;
  now = new Date(data.clock.now);
  points = data.features.map(f => ({ ...f.properties, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }));
  points.forEach(p => { p.look = look(p); });
  if (!version || !map._fitted) {  // raz: obszar demo + baza MPO
    map.fitBounds(L.latLngBounds(points.map(p => [p.lat, p.lon])).extend([50.0702786, 20.0056628]), { paddingTopLeft: [16, 110], paddingBottomRight: [190, 90] });
    map._fitted = true;
  }
  $('clock').textContent = `${DAYS[now.getDay()]} ${now.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit' })} · ${hhmm(now)}`;
  $('clock').setAttribute('datetime', data.clock.now);
  $('btn-advance').disabled = !data.clock.can_advance;
  renderZones(data.events);
  renderLastReport();
  const refresh = () => { renderMarkers(); renderCards(); renderRisk(); };
  if (routes) refresh();  // zgłoszenie z /jury widać od razu; trasa (OSRM bywa wolny) dochodzi chwilę później
  routes = await (await fetch('/api/routes')).json();
  renderRoutes();
  refresh();
}

// świeżość danych: po 3 nieudanych pollach baner „brak połączenia” (tekst + kształt, nie sam kolor)
let fails = 0, lastOk = null;
function markFresh(ok) {
  fails = ok ? 0 : fails + 1;
  if (ok) lastOk = new Date();
  const off = fails >= 3, t = lastOk ? lastOk.toTimeString().slice(0, 8) : '–';
  $('fresh').classList.toggle('off', off);
  $('fresh-t').textContent = off ? `Brak połączenia · dane z ${t}` : `Aktualizacja ${t}`;
}

async function poll() {
  try {
    const r = await fetch(`/api/changes?since=${encodeURIComponent(version ?? '')}`);
    if (!r.ok) throw new Error(r.status);
    const data = await r.json();
    markFresh(true);
    if (data.changed) await apply(data);
  } catch (e) { markFresh(false); }  // chwilowy brak sieci — spróbujemy za 2 s
  setTimeout(poll, POLL_MS);
}

async function clockAction(btn, url) {
  btn.disabled = true;
  try { await apply(await (await fetch(url, { method: 'POST' })).json()); }
  finally { btn.disabled = false; }
}
$('btn-advance').addEventListener('click', e => clockAction(e.currentTarget, '/api/clock/advance'));
// Reset kasuje zgłoszenia z demo: tylko dyspozytor, potwierdzenie na stronie zamiast confirm() (decyzja 5)
function armReset(btn, run) {
  if (!btn) return;
  let armed = null;
  const label = btn.innerHTML;
  btn.addEventListener('click', () => {
    if (!armed) {
      btn.textContent = 'Skasuje zgłoszenia z demo. Kliknij ponownie';
      armed = setTimeout(() => { armed = null; btn.innerHTML = label; }, 4000);
      return;
    }
    clearTimeout(armed); armed = null; btn.innerHTML = label; run();
  });
}
armReset($('btn-reset'), () => clockAction($('btn-reset'), '/api/clock/reset'));

if (matchMedia('(max-width: 767px)').matches) $('legend').open = false;  // na telefonie legenda nie zasłania mapy
renderQr();
loadComparison();
setStep(3);
poll();
