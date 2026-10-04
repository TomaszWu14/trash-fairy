// Panel dyspozytora: mapa na żywo (pinezki stanów i klastry z mapa.js, gorące obszary, trasy, wysypiska), kafle, zakładki
// Pilne / Ekipy i trasy / Zgłoszenia. „Dodaj do kursu” = decyzja człowieka (POST /api/dyspozytor/dodaj), reguły tylko podpowiadają.
(() => {
  const TF = window.TF, { api, esc, icon, num, stateIcon, toast } = TF;
  const DEPOT_ICON = L.divIcon({ className: 'dp-depot', html: `<span>${icon('building-2')}</span><b>Baza MPO</b>`, iconSize: [112, 36], iconAnchor: [18, 18] });
  const dumpIcon = x => L.divIcon({ className: `tf-dump${x.status === 'uprzatniete' ? ' is-done' : ''}`, html: `<span>${icon(x.status === 'uprzatniete' ? 'check' : 'trash')}</span>`,
                                    iconSize: [30, 30], iconAnchor: [15, 30], tooltipAnchor: [0, -28] });
  const named = (m, label) => m.on('add', () => m.getElement()?.setAttribute('aria-label', label));
  const hhmm = iso => new Date(iso).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
  const dur = m => m >= 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`;
  const km = v => num(v, 1);
  const st = { seen: null, fitted: false, show: { bin: true, shelter: true }, last: null, focus: null };
  const sc = TF.scenario(), q = new URLSearchParams(location.search);
  st.focus = q.get('kosz') ? +q.get('kosz') : sc.on && sc.v !== 'C' ? +(sc.bin || TF.demoBin) : null;
  const focusDump = sc.on && sc.v === 'C' ? sc.wd : null;

  // ---------- mapa ----------
  const map = L.map('dp-map', { zoomControl: false, zoomSnap: 1 }).setView([50.058, 19.955], 14);  // zoom całkowity: bez szwów kafelków
  L.control.zoom({ position: 'bottomright' }).addTo(map); map.attributionControl.setPrefix(false);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, className: 'tiles-soft',
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
  const heat = L.layerGroup().addTo(map), routes = { bin: L.layerGroup().addTo(map), shelter: L.layerGroup().addTo(map) };
  const pins = (L.markerClusterGroup ? L.markerClusterGroup({ showCoverageOnHover: false, spiderfyOnMaxZoom: true, maxClusterRadius: z => z < 15 ? 56 : 36,
    iconCreateFunction: c => TF.clusterIcon(c.getChildCount(), TF.worstState(c.getAllChildMarkers().map(m => m.options.stan))) }) : L.layerGroup()).addTo(map);
  const dumps = L.layerGroup().addTo(map), marks = L.layerGroup().addTo(map);
  const byId = {};
  const panelPad = () => {  // panele pływają nad mapą: dopasowanie widoku omija je, na telefonie panele są pod mapą
    if (!matchMedia('(min-width: 1100px)').matches) return { paddingTopLeft: [16, 16], paddingBottomRight: [16, 16] };
    const p = document.querySelector('.dp-panel').getBoundingClientRect(), k = document.querySelector('.dp-kpis').getBoundingClientRect();
    return { paddingTopLeft: [p.width + 40, k.height + 40], paddingBottomRight: [60, 70] };
  };
  const showOnMap = (lat, lon, id) => {
    map.flyTo([lat, lon], Math.max(map.getZoom(), 17), { duration: .6 });
    const m = byId[id];
    if (m) map.once('moveend', () => { pins.zoomToShowLayer ? pins.zoomToShowLayer(m, () => m.openTooltip()) : m.openTooltip(); });
    if (!matchMedia('(min-width: 1100px)').matches) document.getElementById('dp-map').scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  function renderMap(d, mapa, wys, rek) {
    heat.clearLayers(); pins.clearLayers(); dumps.clearLayers(); marks.clearLayers(); Object.values(routes).forEach(l => l.clearLayers());
    const hot = mapa?.goraco || [], maxw = Math.max(1, ...hot.map(h => h[2]));
    // gorący obszar = kosze z ≥ 10% zgłoszeń najgorszego kosza z 90 dni (jak dawniej na dashboardzie)
    hot.filter(h => h[2] >= .1 * maxw).forEach(([lat, lon, w]) => L.circle([lat, lon], { radius: 60 + 140 * (w / maxw), weight: 1.5, dashArray: '4 4',
      className: 'mk-hot', fillOpacity: .12 + .22 * (w / maxw), interactive: false }).addTo(heat));
    d.floty.forEach(f => {
      if (f.linia.length > 1) L.polyline(f.linia, { className: `route-${f.rodzaj}`, weight: f.rodzaj === 'bin' ? 4 : 3.5, opacity: .85,
        dashArray: f.rodzaj === 'shelter' ? '8 8' : null, interactive: false }).addTo(routes[f.rodzaj]);
      if (!st.show[f.rodzaj]) map.removeLayer(routes[f.rodzaj]); else routes[f.rodzaj].addTo(map);
    });
    const reported = new Set(d.zgloszenia.filter(z => !z.zamkniete).map(z => z.kosz_id)), added = new Set(d.dodane);
    const list = (mapa?.kosze || []).map(k => {
      const label = TF.pinLabel(k.nazwa, k.zapelnienie) + (reported.has(k.id) && k.live ? ', zgłoszony' : '') + (added.has(k.id) ? ', dodany do kursu' : '');
      const m = L.marker([k.lat, k.lon], { icon: TF.mapPin(k.zapelnienie, { altana: k.rodzaj === 'shelter', zgloszenie: k.live && reported.has(k.id), etykieta: label }),
        stan: TF.lvl(k.zapelnienie) }).bindTooltip(`<b>${esc(k.nazwa)}</b><br>${esc(k.adres || '')} · ${num(k.zapelnienie)}%${added.has(k.id) ? '<br>Dodany do kursu przez dyspozytora' : ''}`);
      if (k.live) byId[k.id] = m;
      return m;
    });
    if (pins.addLayers) pins.addLayers(list); else list.forEach(m => pins.addLayer(m));
    (wys?.wysypiska || []).forEach(x => named(L.marker([x.lat, x.lon], { icon: dumpIcon(x), zIndexOffset: 800 }), `Dzikie wysypisko ${x.numer}: ${x.etykieta}`)
      .bindTooltip(`<b>Dzikie wysypisko ${esc(x.numer)}</b><br>${esc(x.etykieta)}${x.rodzaje?.length ? ` · ${esc(x.rodzaje.join(', '))}` : ''}`).addTo(dumps));
    (rek?.podrzucanie || []).forEach(x => L.circleMarker([x.lat, x.lon], { radius: 9, className: 'mk-drop', weight: 2.5, fillOpacity: .25 })
      .bindTooltip(`<b>Podrzucanie odpadów: ${esc(x.kosz)}</b><br>${esc(x.uzasadnienie)}`).addTo(dumps));
    L.marker([d.baza.lat, d.baza.lon], { icon: DEPOT_ICON, keyboard: false, title: d.baza.name }).addTo(marks);
    const f = st.focus && (mapa?.kosze || []).find(k => k.id === st.focus);
    if (f) L.circleMarker([f.lat, f.lon], { radius: 26, className: 'mk-focus', weight: 3, fill: false, interactive: false }).addTo(marks);
    const fd = focusDump && (wys?.wysypiska || []).find(x => x.numer === focusDump);
    if (fd) L.circleMarker([fd.lat, fd.lon], { radius: 26, className: 'mk-focus', weight: 3, fill: false, interactive: false }).addTo(marks);
    if (!st.fitted) {
      st.fitted = true;
      const live = (mapa?.kosze || []).filter(k => k.live).map(k => [k.lat, k.lon]);
      if (fd) map.setView([fd.lat, fd.lon], 15);
      else if (live.length) map.fitBounds(L.latLngBounds(live), panelPad());  // obszar demo czytelnie; baza MPO na wschodzie, linie tras do niej prowadzą
    }
  }

  // ---------- kafle ----------
  function renderKpis(k) {
    const set = (key, html) => { const el = document.querySelector(`[data-k="${key}"]`); if (el) el.innerHTML = html; };
    set('zagrozone', num(k.zagrozone)); set('przepelnione', num(k.przepelnione)); set('km', km(k.km));
    set('kurs', `kurs ${esc(k.kurs)} · ${num(k.punkty)} ${TF.plural(k.punkty, ['punkt', 'punkty', 'punktów'])}, kosze uliczne`);
    set('odbiory', `−${num(k.odbiory_mniej_pct)}%`);
    set('porownanie', `vs stały harmonogram, ${num(k.tygodnie)} tygodnie (<a href="/metodologia">metodologia</a>)`);
  }

  // ---------- Pilne ----------
  const PRIO = { krytyczne: ['full', 'Krytyczne'], wysokie: ['warn', 'Wysokie'] };
  function urgentItem(k, now) {
    const [cls, txt] = PRIO[k.priorytet], kurs = k.kurs;
    const span = Math.max(1, (new Date(k.kurs_o || 0) - now) / 60000);
    const when = k.juz ? `<b class="num">Powyżej 85% od ok. ${esc(k.prog)}</b>`
      : `<b class="num">85% ok. ${esc(k.prog)}</b><span>za ${dur(k.za_min)}</span>`;
    const pos = k.na_kursie ? `na trasie jako ${num(k.pozycja)}. z ${num(k.punktow)}` : 'poza trasą kursu';
    const act = k.dodany
      ? `<p class="dp-added">${icon('check', 'i-sm')}<span>Dodany do kursu ${esc(kurs)} · pierwszy na liście kierowcy</span></p>
         <button class="btn btn-ghost btn-sm" type="button" data-undo="${k.id}">${icon('rotate-ccw', 'i-sm')}Cofnij</button>`
      : `<button class="btn btn-sm btn-add" type="button" data-add="${k.id}">${icon('route', 'i-sm')}${k.na_kursie ? `Na początek kursu ${esc(kurs)}` : `Dodaj do kursu ${esc(kurs)}`}</button>`;
    const fill = k.juz ? 0 : Math.min(100, 100 * k.za_min / span);  // oś: teraz → kurs; od przekroczenia 85% kreskowane
    return `<li class="dp-item${k.dodany ? ' is-added' : ''}${k.id === st.focus ? ' is-focus' : ''}" data-id="${k.id}">
      <div class="dp-item-h"><span class="badge ${cls}">${stateIcon(cls)}${txt}</span>
        <button class="dp-name" type="button" data-show="${k.id}" data-lat="${k.lat}" data-lon="${k.lon}" title="Pokaż na mapie">${esc(k.nazwa)}</button>
        <b class="dp-pct num">${num(k.poziom)}%</b></div>
      <p class="dp-when">${when}</p>
      <div class="dp-axis" style="--x:${fill.toFixed(1)}%" aria-hidden="true"><i></i></div>
      <p class="dp-meta">Kolejny kurs dopiero <b>${esc(kurs)}</b> · ${pos}</p>
      <div class="dp-act">${act}</div></li>`;
  }
  function renderUrgent(d) {
    const box = document.getElementById('dp-pilne'), now = new Date(d.meta.zegar);
    document.getElementById('dp-n-pilne').textContent = d.pilne_liczba ? num(d.pilne_liczba) : '';
    box.innerHTML = d.pilne.length ? d.pilne.map(k => urgentItem(k, now)).join('')
      + (d.pilne_liczba > d.pilne.length ? `<li class="dp-more">i ${num(d.pilne_liczba - d.pilne.length)} kolejnych na trasie najbliższego kursu</li>` : '')
      : `<li class="dp-empty">${stateIcon('ok')}<span>Żaden kosz nie przekroczy 85% przed najbliższym kursem.</span></li>`;
  }

  // ---------- Ekipy i trasy ----------
  function renderFleets(d, rek) {
    document.getElementById('dp-trasy').innerHTML = d.floty.map(f => {
      const p = f.wszystkie ? f.zrobione / f.wszystkie : 0;
      return `<li class="dp-fleet"><div class="dp-fleet-h"><i class="lg-line${f.rodzaj === 'shelter' ? ' lg-dash' : ''}" aria-hidden="true"></i><b>${esc(f.etykieta)}</b>
        <label class="dp-chk"><input type="checkbox" data-fleet="${f.rodzaj}"${st.show[f.rodzaj] ? ' checked' : ''}>na mapie</label></div>
        <p class="dp-meta">Kurs <b>${esc(f.kurs)}</b> · ${esc(f.pojazd)}${f.pojazdy > 1 ? ` ×${f.pojazdy}` : ''} · <b>${num(f.punkty)}</b> ${TF.plural(f.punkty, ['punkt', 'punkty', 'punktów'])} · <b>${km(f.km)} km</b></p>
        <div class="dp-prog"><div class="bar"><i style="--p:${p.toFixed(3)}"></i></div><small class="num">${num(f.zrobione)} z ${num(f.wszystkie)} opróżnionych</small></div></li>`;
    }).join('');
    const approx = d.floty.filter(f => f.przyblizona).map(f => f.etykieta.toLowerCase());
    document.getElementById('dp-trasy-note').textContent = approx.length
      ? `Linie biegną po ulicach; ${approx.join(' i ')}: bez połączenia z serwerem tras, przybliżenie w linii prostej. Kilometry liczy reguła: linia prosta × 1,3.`
      : 'Linie biegną po ulicach (serwer tras na danych OpenStreetMap). Kilometry liczy reguła: linia prosta × 1,3.';
    const pe = rek?.punkty_ekip;
    document.getElementById('dp-crew').innerHTML = pe ? `<h3>${icon('users', 'i-sm')}Punkty ekipy ${esc(pe.trasa)}</h3>
      <p><b class="num">${num(pe.suma)}</b> pkt w ${num(pe.okres_dni)} dniach za potwierdzone sygnały (zdjęcia odbiorów, odpady obok kosza, wysypiska).</p>
      <p class="dp-note">${esc(pe.uwaga)}</p>` : '';
  }

  // ---------- Zgłoszenia na żywo ----------
  function feed(d, wys) {
    const bins = d.zgloszenia.map(z => ({ key: z.numer, o: z.o, ico: stateIcon('report'), t: z.nazwa, id: z.kosz_id,
      s: [z.typ, z.zrodlo, z.osob > 1 ? `${num(z.osob)} ${TF.plural(z.osob, ['osoba', 'osoby', 'osób'])}` : null].filter(Boolean).join(' · '),
      done: z.zamkniete, focus: z.kosz_id === st.focus }));
    const ws = (wys?.wysypiska || []).map(x => ({ key: x.numer, o: x.zgloszono, ico: `<span class="dp-dump">${icon('trash', 'i-sm')}</span>`,
      t: `Dzikie wysypisko ${x.numer}`, lat: x.lat, lon: x.lon, s: [x.etykieta, ...(x.rodzaje || [])].join(' · '),
      done: x.status === 'uprzatniete', focus: x.numer === focusDump }));
    return [...bins, ...ws].sort((a, b) => b.o.localeCompare(a.o)).slice(0, 15);
  }
  function renderFeed(d, wys) {
    const items = feed(d, wys), today = d.meta.zegar.slice(0, 10), coords = {};
    (TF._mapa?.kosze || []).forEach(k => { coords[k.id] = [k.lat, k.lon]; });
    document.getElementById('dp-n-zgl').textContent = items.filter(x => !x.done).length || '';
    document.getElementById('dp-zgl').innerHTML = items.length ? items.map(x => {
      const [lat, lon] = x.lat != null ? [x.lat, x.lon] : coords[x.id] || [];
      return `<li class="dp-ev${x.focus ? ' is-focus' : ''}"><time class="num" datetime="${esc(x.o)}">${x.o.slice(0, 10) === today ? '' : 'wczoraj '}${hhmm(x.o)}</time>${x.ico}
        <span class="dp-ev-t">${lat != null ? `<button class="dp-name" type="button" data-show="${x.id ?? ''}" data-lat="${lat}" data-lon="${lon}" title="Pokaż na mapie">${esc(x.t)}</button>` : `<b>${esc(x.t)}</b>`}<small>${esc(x.s)}</small></span>
        <span class="badge ${x.done ? 'ok' : 'report'}">${x.done ? `${icon('check')}Zamknięte` : 'Otwarte'}</span></li>`;
    }).join('') : `<li class="dp-empty">${stateIcon('ok')}<span>W ostatniej dobie nie było zgłoszeń.</span></li>`;
    // aria-live tylko dla nowych pozycji: pierwsze wczytanie i odświeżenia bez zmian nic nie czytają
    const keys = items.map(x => x.key);
    if (st.seen) {
      const fresh = items.filter(x => !st.seen.has(x.key));
      if (fresh.length) document.getElementById('dp-live').textContent = `Nowe zgłoszenie: ${fresh.map(x => `${x.t}, ${x.s}`).join('; ')}`;
    }
    st.seen = new Set([...(st.seen || []), ...keys]);
  }

  // ---------- zakładki (wzorzec ARIA tabs: strzałki, Home, End) ----------
  const tabs = [...document.querySelectorAll('.dp-tabs [role=tab]')];
  const select = (t, focus = false) => {
    tabs.forEach(x => { const on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1;
      document.getElementById(x.getAttribute('aria-controls')).hidden = !on; });
    if (focus) t.focus();
  };
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => select(t));
    t.addEventListener('keydown', e => {
      const j = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (j === undefined) return;
      e.preventDefault(); select(tabs[(j + tabs.length) % tabs.length], true);
    });
  });
  const startTab = q.get('zakladka') || (sc.on && sc.step > 0 ? 'zgloszenia' : null);
  if (startTab) select(tabs.find(t => t.id === { zgloszenia: 'dp-t-zgl', trasy: 'dp-t-trasy' }[startTab]) || tabs[0]);

  // ---------- akcje ----------
  document.querySelector('.dp-panel').addEventListener('click', async e => {
    const show = e.target.closest('[data-show]'), add = e.target.closest('[data-add]'), undo = e.target.closest('[data-undo]');
    if (show) return showOnMap(+show.dataset.lat, +show.dataset.lon, +show.dataset.show);
    const b = add || undo;
    if (!b) return;
    b.setAttribute('aria-disabled', 'true');
    try {
      const r = await api(`/api/dyspozytor/${add ? 'dodaj' : 'cofnij'}`, { method: 'POST', body: { kosz: +(b.dataset.add || b.dataset.undo) } });
      toast(r.komunikat);
      await load();
      document.querySelector(`.dp-item[data-id="${r.kosz}"] .dp-act .btn`)?.focus();  // fokus zostaje przy tym koszu
    } catch (err) { toast(err.message, 'err'); b.removeAttribute('aria-disabled'); }
  });
  document.querySelector('.dp-panel').addEventListener('change', e => {
    const k = e.target.dataset.fleet;
    if (!k) return;
    st.show[k] = e.target.checked;
    if (st.show[k]) routes[k].addTo(map); else map.removeLayer(routes[k]);
  });

  // ---------- ładowanie ----------
  let busy = false;
  async function load() {
    if (busy) return; busy = true;
    try {
      const [d, mapa, wys, rek] = await Promise.all([api('/api/dyspozytor'), api('/api/dashboard/wykresy/mapa').catch(() => null),
        api('/api/wysypiska').catch(() => null), api('/api/dashboard/rekomendacje').catch(() => null)]);  // bez warstw dodatkowych reszta działa
      TF._mapa = mapa;
      renderKpis(d.kafle); renderUrgent(d); renderFleets(d, rek); renderFeed(d, wys); renderMap(d, mapa, wys, rek);
    } catch (e) { toast(e.message, 'err'); }
    finally { busy = false; }
  }
  load();
  setInterval(() => { if (!document.hidden) load(); }, 10000);  // zgłoszenia na żywo co ~10 s
  TF.watch(() => load(), 4000);  // zgłoszenie, odbiór, przewinięcie zegara: od razu
})();
