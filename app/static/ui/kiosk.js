// Panel kosza: poziom widoczny z daleka, termin odbioru, status zgłoszeń, przyciski „Zgłoś na miejscu” i dzienny kod QR.
// Odświeża się przy każdej zmianie danych, a po północy przeładowuje się z nowym kodem.
(() => {
  const { api, icon, esc, stateIcon } = window.TF;
  const box = document.getElementById('kiosk'), id = box.dataset.id;

  // ekran 1280×800 skalowany do wolnego miejsca: symulacja = okno minus nagłówek, ramka, podpis i pasek scenariusza;
  // tryb urządzenia (?urzadzenie=1) = całe okno. Układ panelu w środku zostaje ten sam.
  const scr = document.getElementById('panel-screen'), sim = document.getElementById('panel-sim');
  const fit = () => {
    let k = Math.min(innerWidth / 1280, innerHeight / 800);
    if (sim) {
      const bar = document.querySelector('.scenario'), bottom = bar ? bar.getBoundingClientRect().top - 12 : innerHeight;
      const top = sim.getBoundingClientRect().top + scrollY;
      const chromeW = scr.parentElement.offsetWidth - scr.offsetWidth, chromeH = sim.offsetHeight - scr.offsetHeight;
      k = Math.min((sim.clientWidth - 32 - chromeW) / 1280, (bottom - top - chromeH) / 800, 1.25);
    }
    scr.style.setProperty('--k', Math.max(.2, k).toFixed(4));
  };
  fit(); addEventListener('resize', fit); new ResizeObserver(() => requestAnimationFrame(fit)).observe(document.body);  // nagłówek, czcionki, pasek scenariusza
  const qr = qrcode(0, 'M'); qr.addData(box.dataset.qr); qr.make();
  const qrBox = document.getElementById('k-qr');
  qrBox.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 0, scalable: true });
  // scenariusz demo A: kod QR klikalny, bo w demo zastępuje aparat telefonu. Adres z dzisiejszym tokenem jest już w HTML panelu.
  const sc = window.TF.scenario();
  if (sc.on && sc.v === 'A') {
    const u = new URL(box.dataset.qr, location.href), href = u.pathname + u.search;
    window.TF.setScenario({ ...sc, qr: href });
    const a = Object.assign(document.createElement('a'), { href, className: 'kiosk-qr-code', innerHTML: qrBox.innerHTML });
    a.setAttribute('aria-label', 'Kod QR: otwórz zgłoszenie tego kosza (w demo zastępuje aparat)');
    a.addEventListener('click', e => { if ((window.TF.scenario().step || 0) === 0) { e.preventDefault(); window.TF.goStep(1); } });
    qrBox.replaceWith(a);
    a.nextElementSibling?.insertAdjacentHTML('beforeend', `<span class="kiosk-qr-tap">${icon('hand', 'i-sm')}Kliknij kod: w demo to skan aparatem</span>`);
  }
  // zegar ścienny (nie zegar demo); sprawdzanie co 30 s zamiast jednego długiego setTimeout przeżyje uśpienie ekranu
  const newCodeAt = Date.now() + ((+box.dataset.qrLeft || 86400) + 5) * 1000;
  setInterval(() => { if (Date.now() >= newCodeAt) location.reload(); }, 30000);
  const when = iso => {
    const d = new Date(iso), now = window.TF.now();
    const day = d.toDateString() === now.toDateString() ? 'dziś' : 'jutro';
    return `${day}, ${d.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}`;
  };
  const render = k => {
    const l = Math.max(0, Math.min(100, k.poziom)), lvl = window.TF.lvl(l);
    const g = document.getElementById('k-gauge');
    g.setAttribute('class', `kgauge lvl-${lvl}`); g.setAttribute('aria-label', `Zapełnienie ${l}%`);
    g.style.setProperty('--y', `${(113 * (1 - l / 100)).toFixed(1)}px`);
    document.getElementById('k-pct').textContent = k.poziom;
    const st = document.getElementById('k-state');
    if (k.zgloszenia_liczba) { st.className = 'kiosk-state reported'; st.innerHTML = `${stateIcon('report')}Zgłoszony przez mieszkańca`; }
    else { st.className = `kiosk-state ${lvl}`; st.innerHTML = `${stateIcon(lvl)}${window.TF.LVL[lvl]}`; }
    // termin tylko, gdy kosz jedzie na najbliższy kurs (API daje go tylko wtedy, J-08); inaczej uczciwie: gdy będzie potrzebny
    document.getElementById('k-next-l').textContent = k.nastepny_odbior ? 'Najbliższy odbiór' : 'Odbiór';
    document.getElementById('k-next').textContent = k.nastepny_odbior ? when(k.nastepny_odbior) : 'gdy będzie potrzebny';
    document.getElementById('k-fc').textContent = k.prognoza;  // „Do opróżnienia ok. HH:MM” z API (J-30)
    const msg = document.getElementById('k-msg');
    const minAgo = k.oprozniono ? Math.round((window.TF.now() - new Date(k.oprozniono)) / 60000) : null;
    if (k.zgloszenia_liczba && k.kierowca_w_drodze) {
      msg.className = 'kiosk-msg reported'; msg.innerHTML = `${icon('truck')}<div>${esc(k.zgloszenia[0]?.typ || 'Zgłoszenie')}: kierowca w drodze<small>Zgłoszeń: ${k.zgloszenia_liczba}. Dziękujemy!</small></div>`;
    } else if (k.zgloszenia_liczba) {
      msg.className = 'kiosk-msg reported'; msg.innerHTML = `${stateIcon('report')}<div>Zgłoszono: ${esc((k.zgloszenia[0]?.typ || 'problem').toLowerCase())}<small>${k.trasa?.na_trasie ? 'Kosz jest na liście kierowcy MPO.' : 'Zgłoszenie przyjęte, sprawdzimy przy kolejnym kursie.'} Zgłoszeń: ${k.zgloszenia_liczba}.</small></div>`;
    } else if (minAgo !== null && minAgo < 180) {
      msg.className = 'kiosk-msg done'; msg.innerHTML = `${stateIcon('ok')}<div>Opróżniono ${minAgo < 1 ? 'przed chwilą' : `${minAgo} min temu`}<small>Dziękujemy za zgłoszenia.</small></div>`;
    } else {
      msg.className = 'kiosk-msg'; msg.innerHTML = `${icon('circle-dot')}<div>Brak zgłoszeń<small>Widzisz problem? Naciśnij przycisk albo zeskanuj kod.</small></div>`;
    }
  };
  // offline: ekran zostaje przy ostatnim znanym stanie i mówi, z której godziny on jest
  let lastOk = null, offline = false;
  const setOnline = ok => {
    if (ok && offline) load();  // sieć wróciła: od razu świeże dane
    if (ok) lastOk = window.TF.now();  // poll bez zmian danych też potwierdza aktualny stan
    offline = !ok;
    document.getElementById('k-off').hidden = ok;
    if (!ok) document.getElementById('k-off-t').textContent = lastOk
      ? `Brak połączenia · stan z ${lastOk.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}` : 'Brak połączenia';
  };
  async function load() {
    try { render((await api(`/api/kosze/${id}`)).kosz); lastOk = window.TF.now(); setOnline(true); }
    catch (e) { setOnline(false); }
  }
  load(); window.TF.watch(load, 3000, setOnline);

  // ---------- przyciski „Zgłoś na miejscu” (token urządzenia panelu, bez QR) ----------
  const rep = document.getElementById('k-report');
  if (rep) {
    const more = document.getElementById('k-more'), moreBtn = rep.querySelector('[data-more]'), ack = document.getElementById('k-ack');
    const typBtns = rep.querySelectorAll('[data-typ]');
    let ackTimer;
    const showMore = open => { more.hidden = !open; moreBtn.setAttribute('aria-expanded', String(open)); };
    moreBtn.addEventListener('click', () => showMore(more.hidden));
    typBtns.forEach(b => b.addEventListener('click', async () => {
      typBtns.forEach(x => x.setAttribute('aria-disabled', 'true'));
      clearTimeout(ackTimer);
      try {
        const d = await api(`/api/kosze/${id}/przycisk`, { method: 'POST', body: { typ: b.dataset.typ, token: rep.dataset.token } });
        ack.className = 'kiosk-ack ok';
        ack.innerHTML = `${stateIcon('ok')}<div>${esc(d.komunikat)}<small>Status zgłoszenia widać obok.</small></div>`;
        showMore(false);
        load();
        if (window.TF.scenario().on) window.TF.scenarioNudge?.();  // scenariusz B: zgłoszenie wysłane, „Dalej” prowadzi do kierowcy
      } catch (x) {
        ack.className = 'kiosk-ack err'; ack.innerHTML = `${stateIcon('full')}<div>${esc(x.message)}</div>`;
      } finally {
        typBtns.forEach(x => x.removeAttribute('aria-disabled'));
        ackTimer = setTimeout(() => { ack.className = 'kiosk-ack'; ack.innerHTML = ''; }, 10000);
      }
    }));
  }
})();
