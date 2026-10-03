const map = L.map('map').setView([50.0570, 19.9460], 15);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL)'
}).addTo(map);

const KIND = { bin: { shape: 'circle', size: 18, label: 'Kosz' }, shelter: { shape: 'square', size: 22, label: 'Altana' } };
const markers = {};
let points = [];
let filter = 'all';

const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pinHtml = p => `<span class="tf-pin ${KIND[p.kind].shape} ${p.state}" aria-hidden="true">${p.symbol}</span>`;
const describe = p => `${KIND[p.kind].label}: ${p.name}, ${p.level}%, ${p.label}`;

function renderMap() {
  for (const p of points) {
    const k = KIND[p.kind];
    const icon = L.divIcon({ className: '', iconSize: [k.size, k.size], html: pinHtml(p) });
    markers[p.id] = L.marker([p.lat, p.lon], { icon, title: describe(p), alt: describe(p), keyboard: true })
      .bindPopup(`<b>${esc(p.name)}</b><br>${k.label} · ${esc(p.area)}<br>Zapełnienie: <b>${p.level}%</b> (${p.symbol} ${p.label})`)
      .addTo(map);
  }
}

function renderList() {
  const list = document.getElementById('point-list');
  list.innerHTML = points
    .filter(p => filter === 'all' || p.kind === filter)
    .sort((a, b) => b.level - a.level)
    .map(p => `<li><button type="button" data-id="${p.id}" aria-label="${esc(describe(p))}. Pokaż na mapie.">
        ${pinHtml(p)}
        <span class="name">${esc(p.name)}<small>${KIND[p.kind].label} · ${esc(p.area)} · ${p.label}</small></span>
        <span class="lvl">${p.level}%</span></button></li>`)
    .join('');
}

function renderSummary() {
  const count = s => points.filter(p => p.state === s).length;
  for (const s of ['bad', 'warn', 'ok']) document.getElementById(`n-${s}`).textContent = count(s);
  const bins = points.filter(p => p.kind === 'bin').length;
  document.getElementById('n-total').textContent = `${bins} koszy ulicznych i ${points.length - bins} altan osiedlowych`;
}

document.getElementById('point-list').addEventListener('click', e => {
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

fetch('/api/points').then(r => r.json()).then(fc => {
  points = fc.features.map(f => ({ ...f.properties, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] }));
  renderMap();
  renderList();
  renderSummary();
});
