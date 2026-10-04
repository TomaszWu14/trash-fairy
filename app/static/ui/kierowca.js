// Perspektywa kierowcy: trasa po priorytecie, karta kosza z akcjami jednym dotknięciem, nawigacja prowadzona w aplikacji (symulowany przejazd).
(() => {
  const TF = window.TF, { api, esc, gauge, fillBadge, frac, icon, toast, stateIcon, lvl, mapPin, pinLabel } = TF;  // pinezki: mapa.js
  const POS_KEY = 'tf-pojazd';
  const DEPOT = [50.0702786, 20.0056628];
  const LEVELS = [0, 25, 50, 75, 100];
  const truckPos = () => { try { return JSON.parse(localStorage.getItem(POS_KEY)) || DEPOT; } catch (e) { return DEPOT; } };
  const saveTruck = p => { try { localStorage.setItem(POS_KEY, JSON.stringify(p)); } catch (e) { /* tryb prywatny */ } };
  const tiles = map => L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    { maxZoom: 19, className: 'tiles-soft', attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
  const truckIcon = () => L.divIcon({ className: '', html: `<span class="truck">${icon('truck')}</span>`, iconSize: [36, 36], iconAnchor: [18, 18] });
  // tyle pierwszych pozycji listy ma numer na mapie (telefon: 5); dalsze to małe kształty stanu (czytelne na zoomie miasta)
  const numbered = () => matchMedia('(max-width: 640px)').matches ? 5 : 8;
  // znacznik jak pinezka na mapie: numer kolejności w pierścieniu w kolorze stanu, kształt stanu, dymek zgłoszenia
  const ord = (k, n) => `<span class="tf-pin is-num si-${lvl(k.poziom)} k-ord" aria-hidden="true"><span class="pin-ring"><b>${n}</b></span>${stateIcon(lvl(k.poziom), 'pin-st')}</span>`;  // zgłoszenia: plakietka w wierszu
  const fmtM = m => m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1).replace('.', ',')} km`;
  const fmtMin = m => m >= 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`;  // bez łamania „3 h | 46 min”
  // „dlaczego tu”: powód z reguły priorytetu (api_pl.powod); pełny kosz ma już kolor i ikonę w samym powodzie
  const WHY = [['Zdjęcie', 'neutral', 'camera'], ['zgłosz', 'report', 'message-square-text'], ['Pełny', 'full', 'circle-alert'], ['Prognoza', 'warn', 'trending-up']];
  const why = k => {
    const [, cls, ico] = WHY.find(([t]) => (k.powod || '').includes(t)) || [null, 'neutral', 'route'];
    return `<span class="badge ${cls}" title="Dlaczego na tej pozycji">${icon(ico)}${esc(k.powod || '')}</span>`;
  };
  const hhmm = iso => new Date(iso).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });

  // ---------- lista trasy ----------
  const stopsEl = document.getElementById('k-stops');
  if (stopsEl && !document.getElementById('k-bin')) {
    const map = L.map('k-map', { zoomControl: false }).setView([50.0617, 19.9373], 14);
    L.control.zoom({ position: 'bottomright' }).addTo(map); map.attributionControl.setPrefix(false);
    tiles(map);
    const layer = L.layerGroup().addTo(map);
    let fitted = false;
    let scrolled = false;
    const sc = TF.scenario(), focusBin = sc.on ? +(sc.bin || TF.demoBin) : null;  // scenariusz demo: kosz z kroku 3 podświetlony
    const row = (k, top, n) => `<li class="k-stop ${top ? 'top' : ''} ${k.zrobione ? 'done' : ''}"><a href="/kierowca/kosz/${k.id}">
      ${k.zrobione ? `<span class="tf-pin si-ok k-ord" aria-hidden="true">${stateIcon('ok', 'pin-shape')}</span>` : ord(k, n)}<span class="k-stop-txt"><b>${n ? `<span class="sr-only">${n}. </span>` : ''}${esc(k.nazwa)}</b><span>${esc(k.adres)}</span>
      <span class="k-stop-tags">${k.zrobione ? `<span class="badge ok">${icon('check')}Opróżniony</span>` : `${k.dyspozytor ? `<span class="badge brand">${icon('radar')}Dodany przez dyspozytora</span>` : ''}${why(k)}`}
        ${k.w_drodze ? `<span class="badge progress">${icon('navigation')}Jadę</span>` : ''}</span></span>
      ${k.zrobione ? '' : `<b class="k-pct num">${k.poziom}%</b>`}${icon('chevron-right')}</a></li>`;
    const load = async () => {
      try {
        const [d, dp] = await Promise.all([api('/api/trasa'), api('/api/dyspozytor/dodane').catch(() => ({ dodane: [] }))]);
        const added = new Set(dp.dodane);  // decyzja dyspozytora („Dodaj do kursu”): te kosze na górze listy, reszta w kolejności priorytetu
        d.przystanki.forEach(k => { k.dyspozytor = added.has(k.id); });
        const todo = d.przystanki.filter(k => !k.zrobione).sort((a, b) => b.dyspozytor - a.dyspozytor), done = d.przystanki.filter(k => k.zrobione);
        document.getElementById('k-run').textContent = `Kurs ${hhmm(d.kurs)} · ${d.pojazd} · ${String(d.km).replace('.', ',')} km`;
        document.getElementById('k-done').textContent = `${d.postep.zrobione} z ${d.postep.wszystkie}`;
        document.getElementById('k-left').textContent = todo.length ? `koszy opróżnionych · do końca ok. ${fmtMin(d.postep.pozostalo_min)}` : 'Trasa zakończona. Dobra robota!';
        document.getElementById('k-bar').style.setProperty('--p', (d.postep.zrobione / Math.max(1, d.postep.wszystkie)).toFixed(3));
        stopsEl.innerHTML = todo.length ? todo.map((k, i) => row(k, (i === 0 && (k.zgloszenia_liczba || k.poziom >= 80)) || k.dyspozytor || k.id === focusBin, i + 1)).join('')
          : `<li class="empty"><img src="/static/ui/ill/sukces.svg" alt="" width="140"><h3>Wszystko opróżnione</h3><p>Na tym kursie nie ma już koszy do odbioru.</p></li>`;
        document.getElementById('k-done-box').hidden = !done.length;
        document.getElementById('k-done-n').textContent = `(${done.length})`;
        document.getElementById('k-done-list').innerHTML = done.map(k => row(k, false)).join('');
        if (!scrolled && focusBin) { scrolled = true; stopsEl.querySelector(`.k-stop a[href="/kierowca/kosz/${focusBin}"]`)?.scrollIntoView({ block: 'nearest' }); }
        const skip = d.pominiete || [], more = (d.pominiete_liczba || 0) - skip.length;  // „dlaczego nie na trasie” (routes.skip_reason)
        document.getElementById('k-skip-box').hidden = !skip.length;
        document.getElementById('k-skip-n').textContent = `(${d.pominiete_liczba})`;
        document.getElementById('k-skip-list').innerHTML = skip.map(k => `<li><a href="/kierowca/kosz/${k.id}"><b>${esc(k.nazwa)}</b>
          <b class="num">${k.poziom}%</b><span>${esc(k.powod)}</span></a></li>`).join('')
          + (more > 0 ? `<li class="hint">i ${more} mniej pełnych</li>` : '');
        layer.clearLayers();
        // linia trasy w tle (kolejność optymalizatora), pinezki na pierwszym planie; numer = pozycja na liście, nie kolejność jazdy
        if (d.linia.length > 1) L.polyline(d.linia, { className: 'route-bin', weight: 3, opacity: .5 }).addTo(layer);
        const NUMBERED = numbered();
        todo.forEach((k, i) => {  // pierwsze pozycje z numerem i na wierzchu, dalsze mniejsze; dymek zgłoszenia tylko na małych (numer ma go w wierszu)
          const n = i + 1, top = n <= NUMBERED, label = `${top ? `${n}. na liście: ` : ''}${pinLabel(k.nazwa, k.poziom)}${k.zgloszenia_liczba ? ', zgłoszony' : ''}`;
          L.marker([k.lat, k.lon], { icon: mapPin(k.poziom, { numer: top ? n : null, maly: !top, zgloszenie: !top && k.zgloszenia_liczba > 0, altana: k.rodzaj === 'altana', etykieta: label }),
            zIndexOffset: top ? 2000 - n : (k.poziom >= 80 ? 500 : 0) }).bindTooltip(esc(label)).on('click', () => location.href = `/kierowca/kosz/${k.id}`).addTo(layer);
        });
        L.marker(truckPos(), { icon: truckIcon(), title: 'Twój pojazd', keyboard: false }).addTo(layer);
        if (!fitted && todo.length) { map.fitBounds(L.latLngBounds(todo.slice(0, NUMBERED).map(k => [k.lat, k.lon])).pad(0.25), { maxZoom: 17 }); fitted = true; }  // najbliższe przystanki, nie całe miasto
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
  // pojazd daleko (np. w bazie): mapa na koszu, nie na całym mieście; dojazd pokazuje „Jadę”
  if (map.distance(truckPos(), binLL) < 2500) map.fitBounds(L.latLngBounds([truckPos(), binLL]).pad(0.2), { maxZoom: 17 });

  const render = k => {
    document.getElementById('k-head').innerHTML = `${gauge(k.poziom)}<div><h1>${esc(k.nazwa)}</h1><span>${esc(k.adres)} · ${esc(k.rodzaj)}</span>
      <div class="k-stop-tags">${fillBadge(k.poziom)}${frac(k.frakcja)}</div></div><b class="k-big num">${k.poziom}%</b>
      ${k.trasa?.powod ? '' : `<p class="k-fc" data-help="kierowca_kosz.trasa">${icon('trending-up', 'i-sm')}${esc(k.prognoza)}</p>`}
      ${k.trasa?.powod ? `<p class="k-fc">${icon(k.trasa.na_trasie ? 'route' : 'clock', 'i-sm')}<span data-help="kierowca_kosz.trasa" data-help-at="after"><b>${k.trasa.na_trasie ? 'Na trasie najbliższego kursu' : 'Poza najbliższym kursem'}:</b> ${esc(k.trasa.powod)}</span></p>` : ''}`;
    const nRep = k.zgloszenia_liczba || 0;  // liczba naciśnięć/zgłoszeń z reguły; ta sama co na liście trasy
    // z komentarzem albo zdjęciem: osobno; same naciśnięcia tego samego rodzaju: jeden wpis z liczbą i godziną ostatniego
    const rich = k.zgloszenia.filter(z => z.komentarz || z.ai), plain = {};
    k.zgloszenia.filter(z => !z.komentarz && !z.ai).forEach(z => {
      const g = plain[z.typ] ||= { n: 0, o: z.o };
      g.n += z.osob || 1; if (z.o > g.o) g.o = z.o;
    });
    const rep = (title, body, ai) => `<div class="k-rep">${icon('message-square-text')}<div><b>${esc(title)}</b>${body}${window.TF.aiBlock(ai)}</div></div>`;
    document.getElementById('k-reports').innerHTML = nRep ? `<div class="k-reports">${[
      ...rich.map(z => rep(`Zgłoszenie mieszkańca: ${z.typ}`, z.komentarz ? `<q>${esc(z.komentarz)}</q>` : 'Bez komentarza.', z.ai)),
      ...Object.entries(plain).map(([typ, g]) => rep(g.n > 1 ? `${typ}: ${g.n} ${TF.plural(g.n, ['zgłoszenie', 'zgłoszenia', 'zgłoszeń'])}` : `Zgłoszenie mieszkańca: ${typ}`,
        `${g.n > 1 ? 'Ostatnie' : 'Wysłane'} o ${hhmm(g.o)}, bez komentarza.`)),
    ].join('')}</div>` : '<p class="hint">Brak zgłoszeń mieszkańców przy tym koszu.</p>';
    doneMsg = nRep ? `Zamknięto ${nRep} ${TF.plural(nRep, ['zgłoszenie', 'zgłoszenia', 'zgłoszeń'])} mieszkańców.`
      : 'Kosz wraca do kolejki; kolejny odbiór wyliczy plan.';
    if (document.getElementById('k-doneok').hidden) document.getElementById('k-done-msg').textContent = doneMsg;
    if (!page.querySelector('input[name=poziom]:checked')) {  // podpowiedź: najbliższy poziom do szacunku; kierowca może poprawić
      const near = LEVELS.reduce((a, b) => Math.abs(b - k.poziom) < Math.abs(a - k.poziom) ? b : a);
      page.querySelector(`input[name=poziom][value="${near}"]`).checked = true;
    }
    if (binMarker) binMarker.remove();
    const label = pinLabel(k.nazwa, k.poziom);
    binMarker = L.marker(binLL, { icon: mapPin(k.poziom, { zgloszenie: nRep > 0, altana: k.rodzaj === 'altana', etykieta: label }), zIndexOffset: 1000 })
      .bindTooltip(esc(label)).addTo(map);
    if (k.kierowca_w_drodze) page.querySelector('.k-go').classList.add('on');
    kind = k.rodzaj; required = k.wymaga_zdjecia;
    document.getElementById('k-photo-req').textContent = required ? 'Wymagane w pilotażu. Tylko kosz: bez ludzi i tablic.'
      : 'Opcjonalnie, dowód odbioru. Tylko kosz: bez ludzi i tablic.';
    proof(k.zdjecie_odbioru);
  };
  const load = async () => {
    try { render((await api(`/api/kosze/${id}`)).kosz); }
    catch (e) { document.getElementById('k-head').innerHTML = `<div class="alert" style="flex:1">${icon('circle-alert')}<span>${esc(e.message)}</span></div>`; }
  };
  load(); window.TF.watch(load);  // np. wynik analizy AI zdjęcia przychodzi kilka sekund po zgłoszeniu

  const post = (akcja, extra = {}) => api('/api/odbiory', { method: 'POST', body: { kosz: +id, akcja, ...extra } });

  // dowód odbioru: opcjonalne zdjęcie kosza (w pilotażu obowiązkowe); status liczy reguła po analizie zdjęcia
  let required = false, kind = '', shot = null, proofPoll = null, doneMsg = '';
  const photoIn = document.getElementById('k-photo-in'), prev = document.getElementById('k-photo-prev'), pick = page.querySelector('.k-photo-pick');
  photoIn.addEventListener('change', () => {
    shot = photoIn.files[0] || null;
    if (!shot) return;
    const img = document.getElementById('k-photo-img');
    if (img.src) URL.revokeObjectURL(img.src);
    img.src = URL.createObjectURL(shot);
    prev.hidden = false; pick.hidden = true;
  });
  document.getElementById('k-photo-del').addEventListener('click', () => {
    shot = null; photoIn.value = ''; prev.hidden = true; pick.hidden = false; pick.focus();
  });
  const PROOF = { potwierdzone: ['ok', 'shield-check'], do_weryfikacji: ['neutral', 'circle-help'], w_toku: ['brand', 'loader-circle'] };
  function proof(z) {
    const el = document.getElementById('k-proof');
    if (!z || document.getElementById('k-doneok').hidden) return;
    const [cls, ico] = PROOF[z.status] || PROOF.do_weryfikacji;
    el.hidden = false;
    el.innerHTML = `<span class="badge ${cls}">${icon(ico)}${esc(z.etykieta)}</span>${z.status === 'do_weryfikacji' ? '<small>Zdjęcie sprawdzi dyspozytor.</small>' : ''}`;
    clearTimeout(proofPoll);
    if (z.status === 'w_toku') proofPoll = setTimeout(load, 3000);  // analiza w tle trwa kilka sekund
  }

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
    routeLine = L.polyline(path, { className: kind === 'altana' ? 'route-shelter' : 'route-bin', weight: 6, opacity: .9 }).addTo(map);
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
    const level = page.querySelector('input[name=poziom]:checked')?.value;
    const [lat, lon] = truckPos();
    if (required && !shot) { toast('W pilotażu odbiór wymaga zdjęcia kosza.', 'err'); b.removeAttribute('aria-disabled'); pick.focus(); return; }
    try {
      const fd = new FormData();
      Object.entries({ kosz: id, akcja: 'oprozniono', poziom: level, lat, lon }).forEach(([k, v]) => fd.append(k, v));
      if (shot) fd.append('zdjecie', shot);
      const d = await api('/api/odbiory', { method: 'POST', body: fd, signal: AbortSignal.timeout?.(60000) });
      // sukces bez toastu: panel #k-doneok (aria-live) mówi to samo i nie zasłania „Następny”
      ['.k-actions', '.k-level', '.k-photo', '#k-reports'].forEach(sel => { page.querySelector(sel).hidden = true; });  // zgłoszenia: podsumowanie w #k-done-msg
      document.getElementById('k-doneok').hidden = false;
      proof(d.zdjecie);
      next();
      load();
    } catch (x) { toast(x.message, 'err'); b.removeAttribute('aria-disabled'); }
  });
  // „Następny kosz”: w scenariuszu demo prowadzi do kolejnego kroku, poza nim otwiera kartę kolejnego kosza z trasy
  function next() {
    const a = document.getElementById('k-next'), s = TF.scenario();
    if (s.on) {
      a.firstChild.textContent = 'Dalej w scenariuszu';
      a.onclick = e => { e.preventDefault(); TF.goStep((s.step || 0) + 1); };
      TF.scenarioNudge?.();
      return;
    }
    api('/api/trasa').then(t => {
      const n = t.przystanki.find(k => !k.zrobione && String(k.id) !== id);
      if (n) { a.href = `/kierowca/kosz/${n.id}`; a.firstChild.textContent = `Następny: ${n.nazwa}`; } else a.firstChild.textContent = 'Wróć do trasy';
    }).catch(() => {});  // błąd: zostaje link do listy
  }

  const dlg = document.getElementById('k-problem');
  page.querySelector('[data-problem]').addEventListener('click', () => dlg.showModal());
  dlg.querySelector('[data-close]').addEventListener('click', () => dlg.close());
  dlg.querySelectorAll('[data-problem-kind]').forEach(b => b.addEventListener('click', async () => {
    const [lat, lon] = truckPos();  // położenie pojazdu jak przy odbiorze
    try { const d = await post('problem', { problem: b.dataset.problemKind, lat, lon }); dlg.close(); toast(d.komunikat); }
    catch (x) { toast(x.message, 'err'); }
  }));
})();
