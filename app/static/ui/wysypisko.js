// Dzikie wysypisko: miejsce (GPS, dotknięcie mapy, środek mapy, demo) → rodzaj → liczba → zdjęcie → Wyślij; status zgłoszenia
// („Twoje punkty” na /zglos rysuje mieszkaniec.js). Mapa pokazuje tylko pinezkę zgłaszającego: bez koszy i bez cudzych zgłoszeń.
(() => {
  const { api, esc, icon, stateIcon } = window.TF;
  const fmt = v => v.toFixed(5).replace('.', ',');
  const when = iso => iso ? new Date(iso).toLocaleString('pl-PL', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
  // status: klasa plakietki + ikona; etykieta zawsze tekstem (kolor nie jest jedynym nośnikiem)
  const ST = { uprzatniete: ['ok', stateIcon('ok')], zweryfikowane: ['ok', icon('shield-check')], potwierdzone: ['brand', icon('users')],
               w_toku: ['brand', icon('loader-circle')], do_weryfikacji: ['neutral', icon('circle-help')] };
  const BIG = { uprzatniete: stateIcon('ok', 'i-xl'), zweryfikowane: icon('shield-check', 'i-xl'), potwierdzone: icon('users', 'i-xl'),
                w_toku: icon('loader-circle', 'i-xl'), do_weryfikacji: icon('circle-help', 'i-xl') };  // ikona 56 px przy H1 statusu
  const badge = d => { const [cls, ico] = ST[d.status] || ST.do_weryfikacji; return `<span class="badge ${cls}">${ico}${esc(d.etykieta)}</span>`; };
  // ten sam identyfikator telefonu co zgłoszenia koszy (mieszkaniec.js): limit po telefonie, nie po IP sali. Ekipa MPO ma osobny
  // (tf-ekipa): w demo to ta sama przeglądarka, a uprzątnięcie z telefonu zgłaszającego nie daje punktów (samopotwierdzenie)
  const clientId = (crew = false) => {
    const k = crew ? 'tf-ekipa' : 'tf-klient';
    try { let id = localStorage.getItem(k); if (!id) { id = crypto.randomUUID(); localStorage.setItem(k, id); } return id; }
    catch (e) { return crew ? 'ekipa-demo' : ''; }
  };
  const sc = window.TF.scenario(), inScenario = sc.on && sc.v === 'C';

  // ---------- formularz ----------
  const form = document.getElementById('wd-form');
  if (form) {
    const crew = form.dataset.ekipa === '1';
    const [S, W, N, E] = form.dataset.krakow.split(',').map(Number);
    const inKrakow = p => p.lat >= S && p.lat <= N && p.lon >= W && p.lon <= E;
    const where = document.querySelector('#wd-where span');
    const send = document.getElementById('wd-send'), why = document.getElementById('wd-why');
    const qty = document.getElementById('wd-qty'), unknown = document.getElementById('wd-nie-wiem');
    const steps = form.querySelectorAll('[data-step]');
    let pos = null, pin = null;

    const qtyOk = () => /^\d+$/.test(qty.value) && +qty.value >= 1 && +qty.value <= 100;
    const reason = () => !pos ? 'Zaznacz miejsce na mapie'
      : !inKrakow(pos) ? 'Wybierz miejsce w granicach Krakowa'
      : !form.querySelector('input[name=rodzaj]:checked') ? 'Wybierz, co leży'
      : !unknown.checked && !qtyOk() ? 'Podaj liczbę od 1 do 100 albo zaznacz „Nie wiem”' : '';
    const sync = () => {  // aria-disabled, nie disabled: przycisk zostaje w kolejności Tab, a powód jest obok niego
      const r = reason();
      why.hidden = !r; why.querySelector('span').textContent = r;
      if (r) send.setAttribute('aria-disabled', 'true'); else send.removeAttribute('aria-disabled');
    };

    const map = L.map('wd-map', { zoomControl: false }).setView([50.0617, 19.9373], 13);
    L.control.zoom({ position: 'bottomright' }).addTo(map); map.attributionControl.setPrefix(false);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      { maxZoom: 19, className: 'tiles-soft', attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
    const pinIcon = L.divIcon({ className: 'wd-pin', html: icon('map-pin'), iconSize: [36, 36], iconAnchor: [18, 34] });
    // celownik środka mapy znika, gdy pinezka stoi na środku (inaczej dwa znaczniki jeden pod drugim)
    const centered = () => map.getContainer().classList.toggle('has-pin',
      !!pin && map.latLngToContainerPoint(pin.getLatLng()).distanceTo(map.getSize().divideBy(2)) < 24);
    const setPin = (lat, lon, how, zoom) => {
      pos = { lat, lon };
      if (!pin) {
        pin = L.marker([lat, lon], { icon: pinIcon, draggable: true, keyboard: false, title: 'Miejsce zgłoszenia' }).addTo(map);
        pin.on('dragend', () => { const ll = pin.getLatLng(); setPin(ll.lat, ll.lng, 'pinezka przesunięta na mapie'); });
      } else pin.setLatLng([lat, lon]);
      if (zoom) map.setView([lat, lon], zoom);
      centered();
      where.innerHTML = `Wybrane miejsce: <b class="num">${fmt(lat)}, ${fmt(lon)}</b> · ${esc(how)}${inKrakow(pos) ? '' : '. To miejsce jest poza Krakowem.'}`;
      sync();
    };
    map.on('click', e => setPin(e.latlng.lat, e.latlng.lng, 'pinezka na mapie'));
    map.on('move', centered);
    document.getElementById('wd-center').addEventListener('click', () => { const c = map.getCenter(); setPin(c.lat, c.lng, 'środek mapy'); });
    const demo = document.getElementById('wd-demo');
    demo.addEventListener('click', () => setPin(+demo.dataset.lat, +demo.dataset.lon, `${demo.dataset.label} (przykład demo)`, 17));
    document.getElementById('wd-gps').addEventListener('click', () => {
      if (!navigator.geolocation) { where.textContent = 'Ten telefon nie udostępnia położenia. Zaznacz miejsce na mapie.'; return; }
      where.textContent = 'Szukam położenia…';
      navigator.geolocation.getCurrentPosition(
        p => setPin(p.coords.latitude, p.coords.longitude, `z GPS, dokładność ok. ${Math.round(p.coords.accuracy)} m`, 17),
        () => { where.textContent = 'Nie udało się odczytać położenia (brak zgody albo sygnału). Zaznacz miejsce na mapie.'; },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
    });
    if (crew) {  // kierowca: domyślnie pozycja śmieciarki z aplikacji kierowcy (kierowca.js, klucz tf-pojazd = [lat, lon])
      try {
        const t = JSON.parse(localStorage.getItem('tf-pojazd'));
        if (Array.isArray(t) && t.every(Number.isFinite)) setPin(t[0], t[1], 'pozycja śmieciarki', 16);
      } catch (e) { /* brak pozycji: kierowca zaznacza na mapie */ }
    }

    steps.forEach(b => b.addEventListener('click', () => {
      qty.value = Math.min(100, Math.max(1, (parseInt(qty.value, 10) || 0) + +b.dataset.step)); sync();
    }));
    unknown.addEventListener('change', () => { qty.disabled = unknown.checked; steps.forEach(b => { b.disabled = unknown.checked; }); sync(); });
    qty.addEventListener('input', sync);
    form.querySelectorAll('input[name=rodzaj]').forEach(c => c.addEventListener('change', sync));
    form.zdjecie.addEventListener('change', () => {
      const f = form.zdjecie.files[0];
      document.getElementById('wd-photo-txt').textContent = f ? `Zdjęcie: ${f.name}` : 'Dodaj zdjęcie';
    });
    sync();

    // scenariusz demo C: formularz wypełniony przykładem (miejsce z losowania, bio + tworzywa, ok. 20 worków) i przykładowe zdjęcie na życzenie
    if (inScenario && !crew) {
      const m = sc.miejsce;
      if (m) setPin(m.lat, m.lon, `${m.nazwa} (scenariusz demo)`, 17);
      ['bio', 'tworzywa'].forEach(v => { const c = form.querySelector(`input[name=rodzaj][value="${v}"]`); if (c) c.checked = true; });
      qty.value = 20;
      const more = form.querySelector('.m-more'), photo = form.querySelector('.m-photo');
      if (more && photo) {
        more.open = true;
        photo.insertAdjacentHTML('afterend', `<button class="btn btn-sm wd-demo-photo" type="button">${icon('camera')}Dołącz przykładowe zdjęcie (demo)</button>`);
        const b = more.querySelector('.wd-demo-photo');
        b.addEventListener('click', async () => {
          try {  // rysunek worków z repo (app/static/ui/demo), opisany jako przykład; trafia do formularza jak zdjęcie z aparatu
            const blob = await (await fetch(window.TF.icons.replace('icons.svg', 'demo/wysypisko-przyklad.jpg'))).blob();
            const dt = new DataTransfer(); dt.items.add(new File([blob], 'przyklad-demo-wysypisko.jpg', { type: 'image/jpeg' }));
            form.zdjecie.files = dt.files; form.zdjecie.dispatchEvent(new Event('change'));
            b.innerHTML = `${icon('check')}Dołączono przykładowe zdjęcie`; b.setAttribute('aria-disabled', 'true');
          } catch (x) { window.TF.toast('Nie udało się dołączyć przykładowego zdjęcia.', 'err'); }
        });
      }
      sync();
    }

    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (reason() || send.getAttribute('aria-disabled') === 'true') return;  // Enter w polu: bez wysyłki, powód widać obok
      const err = document.getElementById('wd-err');
      err.hidden = true; send.setAttribute('aria-disabled', 'true');
      const fd = new FormData();
      fd.append('lat', pos.lat); fd.append('lon', pos.lon);
      form.querySelectorAll('input[name=rodzaj]:checked').forEach(c => fd.append('rodzaj', c.value));
      fd.append('ilosc', unknown.checked ? 'nie_wiem' : qty.value);
      fd.append('komentarz', form.komentarz.value); fd.append('klient', clientId());
      fd.append(crew ? 'zrodlo' : 'konto', crew ? 'ekipa' : 'demo');
      if (form.zdjecie.files[0]) fd.append('zdjecie', form.zdjecie.files[0]);
      try {
        const d = await api('/api/wysypiska', { method: 'POST', body: fd, signal: AbortSignal.timeout?.(90000) });
        if (!crew) {
          try {
            const mine = JSON.parse(localStorage.getItem('tf-moje') || '[]').filter(m => m?.nr !== d.numer);
            localStorage.setItem('tf-moje', JSON.stringify([{ nr: d.numer, kosz: 'Dzikie wysypisko', o: window.TF.now().toISOString() }, ...mine].slice(0, 5)));
          } catch (x) { /* tryb prywatny: numer i tak jest na ekranie */ }
        }
        form.hidden = true;
        const ok = document.getElementById('wd-ok');
        document.getElementById('wd-nr').textContent = d.numer;
        document.getElementById('wd-ok-badge').innerHTML = badge(d);
        document.getElementById('wd-ok-txt').textContent = [
          d.dolaczone ? 'Ktoś już zgłosił to miejsce, Twoje zgłoszenie je potwierdza.' : '',
          crew ? 'Wysypisko trafia do dyspozytora MPO.' : d.zdjecie ? 'Punkty dostaniesz po weryfikacji zdjęcia.'
            : 'Ekipa MPO sprawdzi miejsce. Bez zdjęcia zgłoszenie nie daje punktów.'].filter(Boolean).join(' ');
        document.getElementById('wd-link').href = `/wysypisko/${d.numer}${crew ? '?ekipa=1' : ''}`;
        ok.hidden = false; ok.querySelector('h1').focus?.();
        if (inScenario && !crew) { window.TF.setScenario({ ...window.TF.scenario(), wd: d.numer }); window.TF.scenarioNudge?.(); }
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (x) {
        err.innerHTML = `${icon('circle-alert')}<span>${esc(x.message)}</span>`; err.hidden = false;
      } finally { sync(); }
    });
  }

  // ---------- status zgłoszenia ----------
  const st = document.getElementById('wd-status');
  if (st) {
    const clear = document.getElementById('wd-clear');
    const fact = (t, v) => v ? `<dt>${t}</dt><dd>${v}</dd>` : '';
    const title = document.getElementById('wd-st-h'), ico = document.getElementById('wd-st-ico');
    const render = w => {
      if (title.dataset.status !== w.status) {  // podmiana tylko przy zmianie: czytnik ogłasza nowy status, nie każde odświeżenie
        const [cls] = ST[w.status] || ST.do_weryfikacji;
        ico.className = `m-st-ico ${cls}`; ico.innerHTML = BIG[w.status] || BIG.do_weryfikacji;
        title.textContent = w.etykieta; title.dataset.status = w.status;
      }
      document.getElementById('wd-st-why').textContent = w.uzasadnienie;
      const s = w.miejsce;
      document.getElementById('wd-st-facts').innerHTML = [
        fact('Rodzaj', esc(w.rodzaje.join(', '))),
        fact('Ile', w.ilosc ? `ok. ${w.ilosc} worków lub sztuk` : 'nie wiadomo'),
        fact('Miejsce', `<span class="num">${fmt(w.lat)}, ${fmt(w.lon)}</span>`),
        fact('Zgłoszono', esc(when(w.zgloszono))),
        fact('Zgłoszenia', w.zgloszen > 1 ? `${w.zgloszen}, niezależnych (inne telefony i konta): ${w.potwierdzenia}` : ''),
        fact('Uprzątnięto', esc(when(w.uprzatnieto))),
        fact('To miejsce', s?.poziom ? `${esc(s.etykieta)}. ${esc(s.powod)}` : ''),
        fact('Komentarz', esc(w.komentarz || '')),
      ].join('');
      const ai = w.ai;
      document.getElementById('wd-st-ai').innerHTML = (w.zdjecie ? `<img class="wd-photo" src="${w.zdjecie}" alt="Zdjęcie zgłoszonego wysypiska">` : '') + (ai ? `
        <details class="ai"><summary><span class="badge neutral">${icon('camera')}Opis zdjęcia od AI</span>
          <span class="ai-more">Pokaż${icon('chevron-down', 'i-sm')}</span></summary>
          <dl class="ai-d"><div><dt>Odpady poza pojemnikiem</dt><dd>${ai.widac_odpady ? 'tak' : 'nie'}</dd></div>
            <div><dt>Worki lub sztuki</dt><dd>ok. ${ai.worki}</dd></div>
            ${ai.rodzaje.length ? `<div><dt>Rodzaje</dt><dd>${esc(ai.rodzaje.join(', '))}</dd></div>` : ''}
            <div><dt>Pewność</dt><dd>${Math.round(ai.pewnosc * 100)}%</dd></div><div><dt>Opis</dt><dd>${esc(ai.opis)}</dd></div></dl>
          <p class="ai-note">AI tylko opisuje zdjęcie. Status ustala reguła: widać odpady poza pojemnikiem i pewność od 70%.
            ${ai.zdjecie_publiczne ? '' : 'Na zdjęciu są osoby lub tablice, więc nie pokazujemy go publicznie.'}</p></details>` : '');
      if (clear) clear.hidden = w.status === 'uprzatniete';
      document.getElementById('wd-st-note').textContent = w.status === 'uprzatniete' ? 'Zgłoszenie zamknięte. Dziękujemy!' : 'Status odświeża się sam co kilka sekund.';
    };
    let timer = null;
    const load = async () => {
      try { render((await api(`/api/wysypiska/${encodeURIComponent(st.dataset.nr)}`)).wysypisko); }
      catch (e) {
        if (e.kod === 'wysypisko_nie_istnieje') { st.hidden = true; document.getElementById('wd-missing').hidden = false; clearInterval(timer); }
      }
    };
    clear?.addEventListener('click', async () => {
      try {
        const d = await api(`/api/wysypiska/${encodeURIComponent(st.dataset.nr)}/uprzatnieto`, { method: 'POST', body: { klient: clientId(st.dataset.ekipa === '1') } });
        window.TF.toast(d.komunikat);
        if (inScenario) window.TF.scenarioNudge?.();
      }
      catch (e) { window.TF.toast(e.message, 'err'); }
      load();
    });
    load(); timer = setInterval(() => { if (!document.hidden) load(); }, 5000);
  }
})();
