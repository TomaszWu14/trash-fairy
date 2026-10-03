const map = L.map('map').setView([50.0570, 19.9460], 15);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL)'
}).addTo(map);

const KIND = { bin: { shape: 'circle', size: 18, label: 'Kosz' }, shelter: { shape: 'square', size: 22, label: 'Altana' } };
const POLL_MS = 2000;
const markers = {};
let points = [];
let filter = 'all';
let version = null;

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
        .bindPopup(popup(p)).addTo(map);
    }
  }
}

function renderList() {
  $('point-list').innerHTML = points
    .filter(p => filter === 'all' || p.kind === filter)
    .sort((a, b) => (b.state === 'bad') - (a.state === 'bad') || b.value - a.value)
    .map(p => `<li><button type="button" data-id="${p.id}" aria-label="${esc(describe(p))}. Pokaż na mapie.">
        ${pinHtml(p)}
        <span class="name">${esc(p.name)}
          <small class="why">${esc(p.reason)}</small>
          ${p.check_button ? `<small class="check">⚠ sprawdź przycisk: ${esc(p.check_reason)}</small>` : ''}
        </span>
        <span class="lvl">${p.value}%</span></button>
        <a class="tf-btnlink" href="/przycisk/${p.id}" target="_blank" rel="noopener" aria-label="Otwórz przycisk punktu ${esc(p.name)}" title="Otwórz przycisk">↗</a></li>`)
    .join('');
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
}

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
  const m = markers[btn.dataset.id];
  map.setView(m.getLatLng(), 17);
  m.openPopup();
});

document.querySelectorAll('.tf-filter').forEach(b => b.addEventListener('click', () => {
  filter = b.dataset.kind;
  document.querySelectorAll('.tf-filter').forEach(x => x.setAttribute('aria-pressed', x === b));
  renderList();
}));

$('btn-advance').addEventListener('click', e => clockAction(e.currentTarget, '/api/clock/advance'));
$('btn-reset').addEventListener('click', e => clockAction(e.currentTarget, '/api/clock/reset'));

poll();
