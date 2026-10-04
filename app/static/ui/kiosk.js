// Panel na koszu: poziom widoczny z daleka, termin odbioru, status zgłoszeń, kod QR do zgłoszenia. Odświeża się przy każdej zmianie danych.
(() => {
  const { api, icon, esc } = window.TF;
  const box = document.getElementById('kiosk'), id = box.dataset.id;
  const STATE = { ok: ['check', 'W porządku'], warn: ['trending-up', 'Zapełnia się'], full: ['circle-alert', 'Pełny'] };
  const qr = qrcode(0, 'M'); qr.addData(box.dataset.qr); qr.make();
  document.getElementById('k-qr').innerHTML = qr.createSvgTag({ cellSize: 4, margin: 0, scalable: true });
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
    if (k.zgloszenia_liczba) { st.className = 'kiosk-state reported'; st.innerHTML = `${icon('message-square-text')}Zgłoszony przez mieszkańca`; }
    else { const [ico, label] = STATE[lvl]; st.className = `kiosk-state ${lvl}`; st.innerHTML = `${icon(ico)}${label}`; }
    document.getElementById('k-next').textContent = when(k.nastepny_odbior);
    document.getElementById('k-fc').textContent = k.prognoza;
    const msg = document.getElementById('k-msg');
    const minAgo = k.oprozniono ? Math.round((window.TF.now() - new Date(k.oprozniono)) / 60000) : null;
    if (k.zgloszenia_liczba && k.kierowca_w_drodze) {
      msg.className = 'kiosk-msg reported'; msg.innerHTML = `${icon('truck')}<div>${esc(k.zgloszenia[0]?.typ || 'Zgłoszenie')}: kierowca w drodze<small>Zgłoszeń: ${k.zgloszenia_liczba}. Dziękujemy!</small></div>`;
    } else if (k.zgloszenia_liczba) {
      msg.className = 'kiosk-msg reported'; msg.innerHTML = `${icon('message-square-text')}<div>Zgłoszono: ${esc((k.zgloszenia[0]?.typ || 'problem').toLowerCase())}<small>Kosz jest na liście kierowcy MPO. Zgłoszeń: ${k.zgloszenia_liczba}.</small></div>`;
    } else if (minAgo !== null && minAgo < 180) {
      msg.className = 'kiosk-msg done'; msg.innerHTML = `${icon('circle-check-big')}<div>Opróżniono ${minAgo < 1 ? 'przed chwilą' : `${minAgo} min temu`}<small>Dziękujemy za zgłoszenia.</small></div>`;
    } else {
      msg.className = 'kiosk-msg'; msg.innerHTML = `${icon('circle-dot')}<div>Brak zgłoszeń<small>Widzisz problem? Zeskanuj kod poniżej.</small></div>`;
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
})();
