// Perspektywa kierowcy: trasa po priorytecie, karta kosza z akcjami jednym dotknięciem, nawigacja prowadzona w aplikacji (symulowany przejazd).
(() => {
  const { api, esc, gauge, fillBadge, frac, icon, toast } = window.TF;
  const POS_KEY = 'tf-pojazd';
  const DEPOT = [50.0702786, 20.0056628];
  const LEVELS = [0, 25, 50, 75, 100];
  const truckPos = () => { try { return JSON.parse(localStorage.getItem(POS_KEY)) || DEPOT; } catch (e) { return DEPOT; } };
  const saveTruck = p => { try { localStorage.setItem(POS_KEY, JSON.stringify(p)); } catch (e) { /* tryb prywatny */ } };
  const tiles = map => L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    { maxZoom: 19, className: 'tiles-soft', attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
  const truckIcon = () => L.divIcon({ className: '', html: `<span class="truck">${icon('truck')}</span>`, iconSize: [36, 36], iconAnchor: [18, 18] });
  const pin = (level, n) => L.divIcon({ className: 'pin', html: gauge(level) + (n ? `<span class="k-num">${n}</span>` : ''), iconSize: [24, 28], iconAnchor: [12, 28] });
  const fmtM = m => m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1).replace('.', ',')} km`;
  const fmtMin = m => m >= 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`;
  const hhmm = iso => new Date(iso).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });

  // ---------- lista trasy ----------
  const stopsEl = document.getElementById('k-stops');
  if (stopsEl && !document.getElementById('k-bin')) {
    const map = L.map('k-map', { zoomControl: false }).setView([50.0617, 19.9373], 14);
    L.control.zoom({ position: 'bottomright' }).addTo(map); map.attributionControl.setPrefix(false);
    tiles(map);
    const layer = L.layerGroup().addTo(map);
    let fitted = false;
    const row = (k, top) => `<li class="k-stop ${top ? 'top' : ''} ${k.zrobione ? 'done' : ''}"><a href="/kierowca/kosz/${k.id}">
      ${gauge(k.zrobione ? 0 : k.poziom)}<span class="k-stop-txt"><b>${esc(k.nazwa)}</b><span>${esc(k.adres)} · przystanek ${k.kolejnosc}</span>
      <span class="k-stop-tags">${k.zrobione ? `<span class="badge ok">${icon('check')}Opróżniony</span>` : fillBadge(k.poziom)}
        ${k.zgloszenia_liczba ? `<span class="badge brand">${icon('message-square-text')}Zgłoszenia: ${k.zgloszenia_liczba}</span>` : ''}
        ${k.w_drodze ? `<span class="badge progress">${icon('navigation')}Jadę</span>` : ''}</span></span>
      ${k.zrobione ? '' : `<b class="k-pct num">${k.poziom}%</b>`}${icon('chevron-right')}</a></li>`;
    const load = async () => {
      try {
        const d = await api('/api/trasa');
        const todo = d.przystanki.filter(k => !k.zrobione), done = d.przystanki.filter(k => k.zrobione);
        document.getElementById('k-run').textContent = `Kurs ${hhmm(d.kurs)} · ${d.pojazd} · ${String(d.km).replace('.', ',')} km`;
        document.getElementById('k-done').textContent = `${d.postep.zrobione} z ${d.postep.wszystkie}`;
        document.getElementById('k-left').textContent = todo.length ? `koszy opróżnionych · do końca ok. ${fmtMin(d.postep.pozostalo_min)}` : 'Trasa zakończona. Dobra robota!';
        document.getElementById('k-bar').style.setProperty('--p', (d.postep.zrobione / Math.max(1, d.postep.wszystkie)).toFixed(3));
        stopsEl.innerHTML = todo.length ? todo.map((k, i) => row(k, i === 0 && (k.zgloszenia_liczba || k.poziom >= 80))).join('')
          : `<li class="empty"><img src="/static/ui/ill/sukces.svg" alt="" width="140"><h3>Wszystko opróżnione</h3><p>Na tym kursie nie ma już koszy do odbioru.</p></li>`;
        document.getElementById('k-done-box').hidden = !done.length;
        document.getElementById('k-done-n').textContent = `(${done.length})`;
        document.getElementById('k-done-list').innerHTML = done.map(k => row(k, false)).join('');
        layer.clearLayers();
        if (d.linia.length > 1) L.polyline(d.linia, { color: '#5B3DF5', weight: 4, opacity: .75 }).addTo(layer);
        const COLOR = { ok: '#16A34A', warn: '#F59E0B', full: '#DC2626' };
        todo.slice(5).forEach(k => L.circleMarker([k.lat, k.lon], { radius: 6, weight: 2, color: '#fff', fillColor: COLOR[window.TF.lvl(k.poziom)], fillOpacity: 1 })
          .bindTooltip(`${k.nazwa} · ${k.poziom}%`).on('click', () => location.href = `/kierowca/kosz/${k.id}`).addTo(layer));
        todo.slice(0, 5).forEach((k, i) => L.marker([k.lat, k.lon], { icon: pin(k.poziom, i + 1), title: k.nazwa, zIndexOffset: 1000 - i })
          .on('click', () => location.href = `/kierowca/kosz/${k.id}`).addTo(layer));
        L.marker(truckPos(), { icon: truckIcon(), title: 'Twój pojazd', keyboard: false }).addTo(layer);
        if (!fitted && todo.length) { map.fitBounds(L.latLngBounds(todo.map(k => [k.lat, k.lon])).pad(0.08)); fitted = true; }
      } catch (e) {
        stopsEl.innerHTML = `<li class="k-stop"><div class="alert" style="flex:1">${icon('wifi-off')}<span>${esc(e.message)}</span></div></li>`;
      }
    };
    load(); window.TF.watch(load);
  }

  // ---------- karta kosza ----------
  const page = document.getElementById('k-bin');
  if (!page) return;
  const id = page.dataset.id, binLL = [+page.dataset.lat, +page.dataset.lon];
  const map = L.map('k-map', { zoomControl: false }).setView(binLL, 16);
  L.control.zoom({ position: 'bottomright' }).addTo(map); map.attributionControl.setPrefix(false);
  tiles(map);
  const truck = L.marker(truckPos(), { icon: truckIcon(), keyboard: false, title: 'Twój pojazd' }).addTo(map);
  let binMarker = null, routeLine = null;
  map.fitBounds(L.latLngBounds([truckPos(), binLL]).pad(0.2), { maxZoom: 17 });

  const render = k => {
    document.getElementById('k-head').innerHTML = `${gauge(k.poziom)}<div><h1>${esc(k.nazwa)}</h1><span>${esc(k.adres)} · ${esc(k.rodzaj)}</span>
      <div class="k-stop-tags">${fillBadge(k.poziom)}${frac(k.frakcja)}</div></div><b class="k-big num">${k.poziom}%</b>`;
    document.getElementById('k-reports').innerHTML = k.zgloszenia.length ? `<div class="k-reports">${k.zgloszenia.map(z =>
      `<div class="k-rep">${icon('message-square-text')}<div><b>Zgłoszenie mieszkańca: ${esc(z.typ)}</b>${z.komentarz ? `<q>${esc(z.komentarz)}</q>` : 'Bez komentarza.'}</div></div>`).join('')}</div>`
      : '<p class="hint">Brak zgłoszeń mieszkańców przy tym koszu.</p>';
    if (!page.querySelector('input[name=poziom]:checked')) {  // podpowiedź: najbliższy poziom do szacunku; kierowca może poprawić
      const near = LEVELS.reduce((a, b) => Math.abs(b - k.poziom) < Math.abs(a - k.poziom) ? b : a);
      page.querySelector(`input[name=poziom][value="${near}"]`).checked = true;
    }
    if (binMarker) binMarker.remove();
    binMarker = L.marker(binLL, { icon: pin(k.poziom), title: k.nazwa }).addTo(map);
    if (k.kierowca_w_drodze) page.querySelector('.k-go').classList.add('on');
  };
  const load = async () => {
    try { render((await api(`/api/kosze/${id}`)).kosz); }
    catch (e) { document.getElementById('k-head').innerHTML = `<div class="alert" style="flex:1">${icon('circle-alert')}<span>${esc(e.message)}</span></div>`; }
  };
  load();

  const post = (akcja, extra = {}) => api('/api/odbiory', { method: 'POST', body: { kosz: +id, akcja, ...extra } });

  // nawigacja w aplikacji: przebieg po ulicach z OSRM, pojazd jedzie po nim, podpowiedzi skrętów z kąta między odcinkami
  const bearing = (a, b) => Math.atan2(b[1] - a[1], (b[0] - a[0]) * 1.55) * 180 / Math.PI;
  const segLen = (a, b) => L.latLng(a).distanceTo(L.latLng(b));
  function turns(path) {
    const out = [];
    let acc = 0;
    for (let i = 1; i < path.length - 1; i++) {
      acc += segLen(path[i - 1], path[i]);
      let d = bearing(path[i], path[i + 1]) - bearing(path[i - 1], path[i]);
      d = ((d + 540) % 360) - 180;
      if (Math.abs(d) > 35 && segLen(path[i], path[i + 1]) > 15) out.push({ at: acc, dir: d > 0 ? 'w lewo' : 'w prawo', sharp: Math.abs(d) > 110 });
    }
    return out;
  }
  async function drive() {
    const nav = document.getElementById('k-navbar'), t = document.getElementById('k-nav-t'), s = document.getElementById('k-nav-s');
    nav.hidden = false; nav.classList.remove('arrived');
    const from = truckPos();
    let path;
    try { path = (await api(`/api/trasa/dojazd?do=${id}&od=${from[0]},${from[1]}`)).sciezka; }
    catch (e) { path = [from, binLL]; }
    if (routeLine) routeLine.remove();
    routeLine = L.polyline(path, { color: '#5B3DF5', weight: 6, opacity: .85 }).addTo(map);
    map.fitBounds(routeLine.getBounds().pad(0.15));
    const cum = [0]; for (let i = 1; i < path.length; i++) cum.push(cum[i - 1] + segLen(path[i - 1], path[i]));
    const total = cum[cum.length - 1], tr = turns(path);
    const dur = Math.min(16000, Math.max(6000, total * 3));  // symulacja: kilka sekund zamiast prawdziwego czasu jazdy
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const t0 = performance.now();
    await new Promise(done => {
      const step = now => {
        const p = reduce ? 1 : Math.min(1, (now - t0) / dur), dist = p * total;
        let i = cum.findIndex(c => c >= dist); if (i < 1) i = 1;
        const f = (dist - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]);
        const pos = [path[i - 1][0] + (path[i][0] - path[i - 1][0]) * f, path[i - 1][1] + (path[i][1] - path[i - 1][1]) * f];
        truck.setLatLng(pos);
        const next = tr.find(x => x.at > dist);
        t.textContent = next ? `Za ${fmtM(next.at - dist)} skręć ${next.dir}` : `Za ${fmtM(total - dist)} cel`;
        s.textContent = `Do kosza ${fmtM(total - dist)} · symulacja przejazdu`;
        if (p < 1) requestAnimationFrame(step); else done();
      };
      requestAnimationFrame(step);
    });
    saveTruck(binLL); truck.setLatLng(binLL);
    nav.classList.add('arrived');
    document.getElementById('k-nav-i').innerHTML = icon('map-pin');
    t.textContent = 'Jesteś na miejscu'; s.textContent = 'Opróżnij kosz i oznacz „Opróżniono”.';
  }

  page.querySelector('[data-akcja="jade"]').addEventListener('click', async e => {
    const b = e.currentTarget; b.setAttribute('aria-disabled', 'true');
    try { const d = await post('jade'); b.classList.add('on'); toast(d.komunikat); await drive(); }
    catch (x) { toast(x.message, 'err'); } finally { b.removeAttribute('aria-disabled'); }
  });
  page.querySelector('[data-akcja="oprozniono"]').addEventListener('click', async e => {
    const b = e.currentTarget; b.setAttribute('aria-disabled', 'true');
    const lvl = page.querySelector('input[name=poziom]:checked')?.value;
    const [lat, lon] = truckPos();
    try {
      const d = await post('oprozniono', { poziom: +lvl, lat, lon });
      toast(d.komunikat);
      page.querySelector('.k-actions').hidden = true; page.querySelector('.k-level').hidden = true;
      document.getElementById('k-doneok').hidden = false;
      load();
    } catch (x) { toast(x.message, 'err'); b.removeAttribute('aria-disabled'); }
  });
  const dlg = document.getElementById('k-problem');
  page.querySelector('[data-problem]').addEventListener('click', () => dlg.showModal());
  dlg.querySelector('[data-close]').addEventListener('click', () => dlg.close());
  dlg.querySelectorAll('[data-problem-kind]').forEach(b => b.addEventListener('click', async () => {
    try { const d = await post('problem', { problem: b.dataset.problemKind }); dlg.close(); toast(d.komunikat); }
    catch (x) { toast(x.message, 'err'); }
  }));
})();
