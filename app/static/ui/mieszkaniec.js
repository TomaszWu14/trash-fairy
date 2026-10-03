// Perspektywa mieszkańca: wybór kosza → zgłoszenie w 3 krokach (QR + położenie, problem, wyślij) → oś czasu statusu.
(() => {
  const { api, esc, gauge, fillBadge, frac, icon, toast } = window.TF;
  const RYNEK = [50.0617, 19.9373];  // położenie przyjęte w demo, gdy telefon nie podaje GPS
  const GEO_M = 150;
  const dist = (a, b) => {  // metry, haversine
    const R = 6371000, r = x => x * Math.PI / 180, dLat = r(b[0] - a[0]), dLon = r(b[1] - a[1]);
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(r(a[0])) * Math.cos(r(b[0])) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  };
  const tiles = map => L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    { maxZoom: 19, className: 'tiles-soft', attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
  const pin = level => L.divIcon({ className: 'pin', html: gauge(level), iconSize: [26, 30], iconAnchor: [13, 30] });
  const fmtM = m => m < 1000 ? `${m} m` : `${(m / 1000).toFixed(1).replace('.', ',')} km`;

  // ---------- wybór kosza ----------
  const list = document.getElementById('m-list');
  if (list) {
    const map = L.map('m-map', { zoomControl: false, attributionControl: true }).setView(RYNEK, 16);
    tiles(map);
    let here = RYNEK, me = L.marker(RYNEK, { icon: L.divIcon({ className: '', html: '<span class="pin-me"></span>', iconSize: [16, 16] }), keyboard: false }).addTo(map);
    const pins = L.layerGroup().addTo(map);
    const load = async () => {
      try {
        const { kosze } = await api(`/api/kosze?blisko=${here[0]},${here[1]}`);
        const near = kosze.slice(0, 6);
        pins.clearLayers();
        near.forEach(k => L.marker([k.lat, k.lon], { icon: pin(k.poziom), title: k.nazwa })
          .on('click', () => location.href = `/zglos/${k.id}`).addTo(pins));
        list.innerHTML = near.map(k => `<li class="m-row"><a href="/zglos/${k.id}">${gauge(k.poziom)}
          <span class="m-row-txt"><b>${esc(k.nazwa)}</b><span>${esc(k.adres)} · ${k.poziom}%</span></span>
          <span class="m-dist num">${fmtM(k.odleglosc_m)}</span>${icon('chevron-right', 'i-sm')}</a></li>`).join('');
        map.fitBounds(L.latLngBounds([here, ...near.map(k => [k.lat, k.lon])]).pad(0.15), { maxZoom: 17 });
      } catch (e) {
        list.innerHTML = `<li class="alert">${icon('wifi-off')}<span>${esc(e.message)}</span></li>`;
      }
    };
    load();
    document.querySelector('[data-locate]').addEventListener('click', () => {
      if (!navigator.geolocation) return toast('Ta przeglądarka nie udostępnia położenia.', 'err');
      navigator.geolocation.getCurrentPosition(p => {
        here = [p.coords.latitude, p.coords.longitude]; me.setLatLng(here);
        document.getElementById('m-pos').textContent = `Twoje położenie (dokładność ok. ${Math.round(p.coords.accuracy)} m).`;
        load();
      }, () => toast('Nie udało się pobrać położenia. Zostaje Rynek Główny.', 'err'), { enableHighAccuracy: true, timeout: 8000 });
    });
    const dlg = document.getElementById('scan-dialog');
    document.querySelector('[data-scan]').addEventListener('click', () => dlg.showModal());
    dlg.querySelector('[data-close]').addEventListener('click', () => dlg.close());
  }

  // ---------- formularz zgłoszenia ----------
  const form = document.getElementById('m-form');
  if (form) {
    const bin = [+form.dataset.lat, +form.dataset.lon];
    const qrOk = document.getElementById('chk-qr').classList.contains('ok');
    let pos = null, simulated = false;
    const next1 = form.querySelector('[data-next="2"]');
    const geoBox = document.getElementById('chk-geo'), geoTxt = document.getElementById('geo-txt');
    const setGeo = (p, acc, sim) => {
      const d = Math.round(dist(p, bin));
      const ok = d - Math.min(acc || 0, GEO_M) <= GEO_M;
      pos = { lat: p[0], lon: p[1], acc: acc || 0 }; simulated = sim;
      geoBox.classList.toggle('ok', ok); geoBox.classList.toggle('bad', !ok);
      geoBox.querySelector('.m-check-i').innerHTML = icon(ok ? 'check' : 'map-pin');
      geoTxt.textContent = sim ? 'Położenie symulowane: telefon przy koszu (demo).' : ok ? `Jesteś ${d} m od kosza.` : `Jesteś ${fmtM(d)} od kosza. Podejdź do ${GEO_M} m.`;
      next1.disabled = !(ok && qrOk);
    };
    form.querySelector('[data-geo]').addEventListener('click', () => {
      if (!navigator.geolocation) return toast('Ta przeglądarka nie udostępnia położenia.', 'err');
      geoTxt.textContent = 'Sprawdzamy położenie…';
      navigator.geolocation.getCurrentPosition(p => setGeo([p.coords.latitude, p.coords.longitude], p.coords.accuracy, false),
        () => { geoTxt.textContent = 'Brak dostępu do położenia. Włącz lokalizację albo użyj symulacji w demo.'; geoBox.classList.add('bad'); },
        { enableHighAccuracy: true, timeout: 8000 });
    });
    form.querySelector('[data-geo-sim]').addEventListener('click', () => setGeo([bin[0] + 0.00012, bin[1] + 0.00008], 10, true));
    if (window.TF.scenario().on && qrOk) setGeo([bin[0] + 0.00012, bin[1] + 0.00008], 10, true);  // scenariusz: telefon przy koszu

    const go = n => {
      form.querySelectorAll('.m-step').forEach(s => s.hidden = s.dataset.step !== String(n));
      form.querySelectorAll('.m-steps li').forEach(li => li.classList.toggle('on', +li.dataset.s <= n));
      if (n === 3) {
        const t = form.querySelector('input[name=typ]:checked');
        document.getElementById('sum-typ').textContent = t ? t.closest('.m-type').querySelector('b').textContent : '–';
        document.getElementById('sum-kom').textContent = form.komentarz.value.trim() || 'brak';
        document.getElementById('sum-foto').textContent = form.zdjecie.files[0]?.name || 'brak';
      }
      form.querySelector(`[data-step="${n}"] .m-legend, [data-step="${n}"] button`)?.focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    form.querySelectorAll('[data-next]').forEach(b => b.addEventListener('click', () => go(+b.dataset.next)));
    form.querySelectorAll('input[name=typ]').forEach(r => r.addEventListener('change', () => { document.getElementById('to-3').disabled = false; }));
    form.zdjecie.addEventListener('change', () => {
      const f = form.zdjecie.files[0];
      document.getElementById('m-photo-txt').innerHTML = f ? `Zdjęcie: ${esc(f.name)}` : 'Dodaj zdjęcie <span class="subtle">(opcjonalnie)</span>';
    });
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const err = document.getElementById('m-err'), send = document.getElementById('m-send');
      err.hidden = true; send.setAttribute('aria-disabled', 'true');
      const fd = new FormData();
      fd.append('kosz', form.dataset.bin); fd.append('typ', form.querySelector('input[name=typ]:checked')?.value || '');
      fd.append('qr', form.dataset.qr); fd.append('lat', pos?.lat ?? ''); fd.append('lon', pos?.lon ?? '');
      fd.append('dokladnosc', pos?.acc ?? ''); fd.append('komentarz', form.komentarz.value); fd.append('symulacja', simulated ? '1' : '');
      fd.append('klient', clientId());
      if (form.zdjecie.files[0]) fd.append('zdjecie', form.zdjecie.files[0]);
      try {
        const d = await api('/api/zgloszenia', { method: 'POST', body: fd });
        form.hidden = true;
        const ok = document.getElementById('m-success');
        document.getElementById('m-nr').textContent = d.numer;
        if (d.dolaczone) document.getElementById('m-success-txt').textContent = 'Ktoś już zgłosił ten kosz. Twoje zgłoszenie wzmocniło tamto i ma ten sam status.';
        document.getElementById('m-status-link').href = `/zgloszenie/${d.numer}`;
        ok.hidden = false; ok.querySelector('h1').focus?.();
        const s = window.TF.scenario(); if (s.on) window.TF.setScenario({ ...s, nr: d.numer });
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (x) {
        err.innerHTML = `${icon('circle-alert')}<span>${esc(x.message)}</span>`; err.hidden = false;
      } finally { send.removeAttribute('aria-disabled'); }
    });
  }
  function clientId() {  // losowy identyfikator telefonu: limit zgłoszeń po telefonie, nie po IP sali (decyzja 13)
    try { let id = localStorage.getItem('tf-klient'); if (!id) { id = crypto.randomUUID(); localStorage.setItem('tf-klient', id); } return id; }
    catch (e) { return ''; }
  }

  // ---------- status zgłoszenia ----------
  const st = document.getElementById('m-status');
  if (st) {
    const BADGE = { przyjete: ['brand', 'circle-dot', 'Przyjęte'], w_realizacji: ['progress', 'truck', 'W realizacji'], zrealizowane: ['ok', 'circle-check-big', 'Zrealizowane'] };
    const time = iso => iso ? new Date(iso).toLocaleString('pl-PL', { weekday: 'short', hour: '2-digit', minute: '2-digit' }) : null;
    const render = d => {
      const [cls, ico, label] = BADGE[d.status];
      document.getElementById('st-badge').className = `badge ${cls}`;
      document.getElementById('st-badge').innerHTML = `${icon(ico)}${label}`;
      const k = d.kosz;
      document.getElementById('st-bin').innerHTML = `${gauge(k.poziom)}<div class="m-bin-txt"><b>${esc(k.nazwa)}</b><span>${esc(k.adres)}</span>
        <div class="m-bin-tags">${fillBadge(k.poziom)}${frac(k.frakcja)}</div></div><b class="m-bin-pct num">${k.poziom}%</b>`;
      const order = ['przyjete', 'w_realizacji', 'zrealizowane'], at = order.indexOf(d.status);
      const desc = { przyjete: `${esc(d.typ)}${d.osob > 1 ? ` · zgłosiło ${d.osob} osób` : ''}`, w_realizacji: 'Kierowca MPO jedzie do kosza.',
                     zrealizowane: 'Kosz opróżniony. Dziękujemy!' };
      document.getElementById('st-steps').innerHTML = d.kroki.map((s, i) => `<li class="${i <= at ? 'done' : ''} ${i === at + 1 ? 'now' : ''}">
        <span class="tl-dot">${i <= at ? icon('check') : ''}</span><div><b>${s.etykieta}</b>
        <span>${s.o ? `${time(s.o)} · ${desc[s.id]}` : i === at + 1 ? (s.id === 'w_realizacji' ? 'Czekamy, aż kierowca ruszy do kosza.' : 'Po opróżnieniu zobaczysz tu godzinę.') : 'Jeszcze nie'}</span></div></li>`).join('');
      document.getElementById('st-note').textContent = d.status === 'zrealizowane' ? 'Zgłoszenie zamknięte.' : 'Status odświeża się sam co kilka sekund.';
    };
    const load = async () => {
      try { render(await api(`/api/zgloszenia/${encodeURIComponent(st.dataset.nr)}`)); }
      catch (e) { if (e.kod === 'zgloszenie_nie_istnieje') { st.hidden = true; document.getElementById('st-missing').hidden = false; } }
    };
    load(); window.TF.watch(load);
  }
})();
