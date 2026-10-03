const map = L.map('map').setView([50.0570, 19.9460], 15);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL)'
}).addTo(map);

const KIND = { bin: { shape: 'circle', size: 18, label: 'Kosz' }, shelter: { shape: 'square', size: 22, label: 'Altana' } };
const POLL_MS = 2000;
const markers = {};
const eventLayer = L.layerGroup().addTo(map);
const routeLayers = { bin: L.layerGroup().addTo(map), shelter: L.layerGroup().addTo(map) };
const ROUTE_COLOR = { bin: '#2f6b3a', shelter: '#b8860b' };
let onRoute = {};  // point_id → przystanek na najbliższym kursie
let points = [];
let filter = 'all';
let version = null;
let detailId = null;
let chart = null;

const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pinHtml = p => `<span class="tf-pinwrap${p.fresh ? ' fresh' : ''}" aria-hidden="true">`
  + `<span class="tf-pin ${KIND[p.kind].shape} ${p.state}">${p.symbol}</span>`
  + (p.check_button ? '<span class="tf-badge">⚠</span>' : '') + '</span>';
const describe = p => `${KIND[p.kind].label}: ${p.name}, ${p.label}, ${p.reason}`
  + (p.fresh ? ', świeże zgłoszenie' : '') + (p.check_button ? `, sprawdź przycisk: ${p.check_reason}` : '');
const popup = p => `<b>${esc(p.name)}</b><br>${KIND[p.kind].label} · ${esc(p.area)}<br>`
  + `Stan: <b>${p.symbol} ${p.label}</b> — ${esc(p.reason)}<br>Poziom: ${p.level}% · wiarygodność przycisku: ${p.reliability}%`
  + (p.check_button ? `<br>⚠ Sprawdź przycisk: ${esc(p.check_reason)}` : '')
  + `<br><a href="/przycisk/${p.id}" target="_blank" rel="noopener">Otwórz przycisk ↗</a>`;

function renderMap() {
  for (const p of points) {
    const k = KIND[p.kind];
    const icon = L.divIcon({ className: '', iconSize: [k.size, k.size], html: pinHtml(p) });
    if (markers[p.id]) {
      markers[p.id].setIcon(icon).setPopupContent(popup(p));
      markers[p.id].getElement()?.setAttribute('title', describe(p));
    } else {
      markers[p.id] = L.marker([p.lat, p.lon], { icon, title: describe(p), alt: describe(p), keyboard: true })
        .bindPopup(popup(p)).on('click', () => openDetails(p.id)).addTo(map);
    }
  }
}

function renderList() {
  $('point-list').innerHTML = points
    .filter(p => filter === 'all' || p.kind === filter)
    .sort((a, b) => (b.state === 'bad') - (a.state === 'bad') || b.value - a.value)
    .map(p => `<li><button type="button" data-id="${p.id}" aria-label="${esc(describe(p))}. Pokaż szczegóły.">
        ${pinHtml(p)}
        <span class="name">${esc(p.name)}
          <small class="why">${esc(p.reason)}</small>
          ${onRoute[p.id] ? `<span class="tf-onroute">🚚 kurs ${onRoute[p.id].run}, przystanek ${onRoute[p.id].order}</span>` : ''}
          ${p.check_button ? `<small class="check">⚠ sprawdź przycisk: ${esc(p.check_reason)}</small>` : ''}
        </span>
        <span class="lvl">${p.value}%</span></button>
        <a class="tf-btnlink" href="/przycisk/${p.id}" target="_blank" rel="noopener" aria-label="Otwórz przycisk punktu ${esc(p.name)}" title="Otwórz przycisk">↗</a></li>`)
    .join('');
}

function renderEvents(events) {
  eventLayer.clearLayers();
  for (const e of events) {
    const label = `${e.name} · ${e.hours}${e.active ? ' (trwa)' : ''}`;
    L.circle([e.lat, e.lon], { radius: e.radius_m, color: '#c9a227', weight: 2, dashArray: '6 6',
                               fillColor: '#c9a227', fillOpacity: e.active ? 0.08 : 0.03, interactive: false }).addTo(eventLayer);
    L.marker([e.lat, e.lon], { icon: L.divIcon({ className: '', iconSize: [24, 24], html: '<span class="tf-evpin" aria-hidden="true">🎪</span>' }),
                               title: label, alt: label, keyboard: true, zIndexOffset: -500 })
      .bindPopup(`<b>${esc(e.name)}</b><br>${esc(e.venue)}<br>${e.hours}${e.active ? ' · <b>trwa</b>' : ''}<br>`
        + `Zasięg ${e.radius_m} m: kosze w okręgu zapełniają się szybciej`).addTo(eventLayer);
  }
}

function apply(data) {
  version = data.version;
  points = data.features.map(f => ({ ...f.properties, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }));
  renderMap();
  renderList();
  for (const s of ['bad', 'warn', 'ok']) $(`n-${s}`).textContent = data.summary[s];
  $('n-presses').textContent = data.summary.live_presses;
  $('n-reports').textContent = data.summary.live_reports;
  const bins = points.filter(p => p.kind === 'bin').length;
  $('n-total').textContent = `${bins} koszy ulicznych i ${points.length - bins} altan osiedlowych`;
  $('clock').textContent = data.clock.label;
  $('btn-advance').disabled = !data.clock.can_advance;
  renderEvents(data.events);
  const q = data.forecast_quality;
  $('quality').innerHTML = q
    ? `<span aria-hidden="true">📈</span> Trafność prognozy (ostatnie ${q.days} dni): średni błąd <b>${q.mae} p.p.</b>, `
      + `a przy stałej średniej <b>${q.naive_mae} p.p.</b>`
    : '';
  if (detailId) openDetails(detailId, false);
  loadRoutes();
}

// --- trasy (etap 4) ---

async function loadRoutes() {
  const data = await (await fetch('/api/routes')).json();
  onRoute = {};
  const depotIcon = L.divIcon({ className: '', iconSize: [26, 26], html: '<span class="tf-depot" aria-hidden="true">🏭</span>' });
  $('routes').innerHTML = data.fleets.map(f => `
    <div class="tf-route">
      <header><span class="tf-routesw ${f.kind}" aria-hidden="true"></span><b>${esc(f.label)}</b>
        <label><input type="checkbox" data-route="${f.kind}" ${map.hasLayer(routeLayers[f.kind]) ? 'checked' : ''}> na mapie</label></header>
      <p class="meta">Kurs ${f.run_label} · ${f.vehicle} · <b>${f.stops.length}</b> punktów · <b>${f.km} km</b>
        · kolejny kurs ${f.following_label}</p>
      ${f.stops.length ? `<ol>${f.stops.map(s => `<li>${esc(s.name)}<small>${esc(s.reason)}</small></li>`).join('')}</ol>`
                       : '<p class="tf-muted">Na ten kurs nie trzeba nikogo wysyłać.</p>'}
    </div>`).join('');
  for (const f of data.fleets) {
    const layer = routeLayers[f.kind];
    layer.clearLayers();
    if (!f.stops.length) continue;
    L.polyline(f.path, { color: ROUTE_COLOR[f.kind], weight: 4, opacity: 0.75, dashArray: f.kind === 'shelter' ? '10 6' : null })
      .addTo(layer);
    L.marker([data.depot.lat, data.depot.lon], { icon: depotIcon, title: data.depot.name, alt: data.depot.name, keyboard: false })
      .bindPopup(`<b>${esc(data.depot.name)}</b><br>start i koniec tras`).addTo(layer);
    for (const s of f.stops) {
      onRoute[s.id] = { run: f.run_label.slice(-5), order: s.order };
      L.marker([s.lat, s.lon], { icon: L.divIcon({ className: '', iconSize: [18, 18], iconAnchor: [-4, 22],
        html: `<span class="tf-stop ${f.kind}" aria-hidden="true">${s.order}</span>` }), interactive: false, keyboard: false }).addTo(layer);
    }
  }
  renderList();
}

document.addEventListener('change', e => {
  const kind = e.target.dataset?.route;
  if (!kind) return;
  e.target.checked ? routeLayers[kind].addTo(map) : map.removeLayer(routeLayers[kind]);
});

// --- porównanie „przed i po” (etap 4) ---

async function loadComparison() {
  const c = await (await fetch('/api/comparison')).json();
  const rows = [
    ['visits', 'wizyty', ''], ['km', 'kilometry', ' km'], ['empty_share', 'puste przyjazdy (<50%)', '%'],
    ['overflow_hours', 'godziny przepełnienia', ' h'],
  ];
  const fmt = v => Number(v).toLocaleString('pl-PL');
  const diff = (a, b) => {
    const d = b - a;
    if (Math.abs(d) < 1e-9) return '<td>bez zmian</td>';
    const pct = a ? ` (${d > 0 ? '+' : ''}${Math.round(100 * d / a)}%)` : '';
    return `<td class="${d < 0 ? 'better' : 'worse'}">${d > 0 ? '+' : '−'}${fmt(Math.abs(Math.round(d * 10) / 10))}${pct}</td>`;
  };
  const group = (key, title) => `<tr class="grp"><td colspan="4">${title}</td></tr>` + rows.map(([k, label, unit]) =>
    `<tr><td>${label}</td><td>${fmt(c.fixed[key][k])}${unit}</td><td>${fmt(c.fairy[key][k])}${unit}</td>${diff(c.fixed[key][k], c.fairy[key][k])}</tr>`).join('');
  const b = c.fixed.bin, fb = c.fairy.bin, s = c.fixed.shelter, fs = c.fairy.shelter;
  $('compare').innerHTML = `
    <table class="tf-cmp">
      <caption class="sr-only" style="position:absolute;left:-9999px">Porównanie stałego harmonogramu z Trash Fairy w ostatnich ${c.weeks} tygodniach</caption>
      <thead><tr><th scope="col"></th><th scope="col">stały</th><th scope="col">wróżka</th><th scope="col">różnica</th></tr></thead>
      <tbody>${group('bin', 'Kosze uliczne')}${group('shelter', 'Altany osiedlowe')}</tbody>
    </table>
    <p class="tf-verdict">Kosze: <b>${fmt(b.visits - fb.visits)} wizyt mniej</b> w ${c.weeks} tygodnie, bez dodatkowych godzin przepełnienia.
      Altany: przepełnienia <b>${fmt(s.overflow_hours)} h → ${fmt(fs.overflow_hours)} h</b> dzięki częstszym kursom tam, gdzie trzeba.</p>
    <p class="tf-muted tf-small">Ten sam przebieg zapełniania dla obu wariantów. Wróżka decyduje tylko na podstawie własnej prognozy, bez przycisków.</p>`;
}

loadComparison();

// --- szczegóły punktu (ekran 2) ---

const hhmm = iso => iso ? iso.slice(11, 16) : '–';

async function openDetails(id, focus = true) {
  detailId = id;
  const d = await (await fetch(`/api/points/${id}`)).json();
  if (detailId !== id) return;  // użytkownik zdążył kliknąć inny punkt
  $('overview').hidden = true;
  $('details').hidden = false;
  $('d-pin').innerHTML = pinHtml(d);
  $('d-name').textContent = d.name;
  $('d-meta').textContent = `${KIND[d.kind].label} · ${d.area}`;
  $('d-state').textContent = `${d.symbol} ${d.label}: ${d.reason}`;
  $('d-facts').innerHTML = [
    ['Szacowany poziom', `${d.level}%`],
    ['Przekroczenie 85%', d.crossing_label ?? 'nie w ciągu 24 h'],
    ['Wiarygodność przycisku', `${d.reliability}%`],
    ['Opróżnienia (48 h)', d.emptyings.map(e => `${hhmm(e.at)} (${e.level}%)`).join(', ') || 'brak'],
    ['Naciśnięcia (48 h)', String(d.presses.length)],
  ].concat(d.check_button ? [['⚠ Sprawdź przycisk', d.check_reason]] : [])
    .map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('');
  $('d-button').href = `/przycisk/${d.id}`;
  renderChart(d);
  if (focus) {
    $('btn-back').focus();
    map.setView(markers[id].getLatLng(), Math.max(map.getZoom(), 16));
  }
}

function closeDetails() {
  const id = detailId;
  detailId = null;
  $('details').hidden = true;
  $('overview').hidden = false;
  document.querySelector(`#point-list button[data-id="${id}"]`)?.focus();
}

function renderChart(d) {
  const labels = d.series.map(s => s.label);
  const past = d.series.map(s => (s.future ? null : s.est));
  const nowIdx = past.findLastIndex(v => v !== null);
  const future = d.series.map((s, i) => (s.future || i === nowIdx ? s.est : null));
  const band = key => d.series.map((s, i) => (s.future || i === nowIdx ? s[key] : null));
  const emptiedAt = new Set(d.emptyings.map(e => e.at.slice(0, 13)));
  const emptyMarks = d.series.map(s => (emptiedAt.has(s.at.slice(0, 13)) ? 0 : null));
  const data = {
    labels,
    datasets: [
      { label: 'Przedział (p20–p80)', data: band('high'), borderWidth: 0, pointRadius: 0, backgroundColor: 'rgba(124,58,237,.12)', fill: '+1' },
      { label: 'dolna granica', data: band('low'), borderWidth: 0, pointRadius: 0, fill: false },
      { label: 'Szacunek', data: past, borderColor: '#2f3b2a', borderWidth: 2, pointRadius: 0, spanGaps: false },
      { label: 'Prognoza', data: future, borderColor: '#7c3aed', borderWidth: 2, borderDash: [6, 4], pointRadius: 0 },
      { label: 'Próg 85%', data: labels.map(() => d.threshold), borderColor: '#c53030', borderWidth: 1, borderDash: [2, 3], pointRadius: 0 },
      { label: 'Opróżnienie', data: emptyMarks, pointStyle: 'triangle', pointRadius: 7, backgroundColor: '#c9a227', borderColor: '#8a6d12', showLine: false },
    ],
  };
  const options = {
    responsive: true, maintainAspectRatio: false, animation: false,
    interaction: { mode: 'index', intersect: false },
    scales: {
      y: { min: 0, max: 120, ticks: { callback: v => `${v}%` } },
      x: { ticks: { maxTicksLimit: 9, autoSkip: true } },
    },
    plugins: {
      legend: { labels: { boxWidth: 12, filter: item => item.text !== 'dolna granica' } },
      tooltip: { filter: item => item.raw !== null && item.dataset.label !== 'dolna granica' },
    },
  };
  if (chart) chart.destroy();
  chart = new Chart($('d-chart'), { type: 'line', data, options });
  $('d-chart-summary').textContent = `Wykres: szacunek z ostatnich 48 h i prognoza na 24 h. Teraz ${d.level}%. `
    + (d.crossing_label ? `Próg 85%: ${d.crossing_label}. ` : 'Bez przekroczenia 85% w ciągu 24 h. ')
    + `Opróżnienia: ${d.emptyings.length}.`;
}

$('btn-back').addEventListener('click', closeDetails);
document.addEventListener('keydown', e => { if (e.key === 'Escape' && detailId) closeDetails(); });

async function poll() {
  try {
    const r = await fetch(`/api/changes?since=${encodeURIComponent(version ?? '')}`);
    const data = await r.json();
    if (data.changed) apply(data);
  } catch (e) { /* chwilowy brak sieci — spróbujemy za 2 s */ }
  setTimeout(poll, POLL_MS);
}

async function clockAction(btn, url) {
  btn.disabled = true;
  try { apply(await (await fetch(url, { method: 'POST' })).json()); }
  finally { btn.disabled = false; }
}

$('point-list').addEventListener('click', e => {
  const btn = e.target.closest('button[data-id]');
  if (!btn) return;
  openDetails(Number(btn.dataset.id));
});

document.querySelectorAll('.tf-filter').forEach(b => b.addEventListener('click', () => {
  filter = b.dataset.kind;
  document.querySelectorAll('.tf-filter').forEach(x => x.setAttribute('aria-pressed', x === b));
  renderList();
}));

$('btn-advance').addEventListener('click', e => clockAction(e.currentTarget, '/api/clock/advance'));
$('btn-reset').addEventListener('click', e => clockAction(e.currentTarget, '/api/clock/reset'));

poll();
