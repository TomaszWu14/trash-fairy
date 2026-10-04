// Perspektywa mieszkańca: skan kodu QR z panelu → zgłoszenie na jednym ekranie (problem → Wyślij) → oś czasu statusu.
// Bez mapy i listy cudzych koszy: mieszkaniec widzi tylko kosz, przy którym stoi, i swoje zgłoszenia (localStorage tf-moje).
(() => {
  const { api, esc, gauge, fillBadge, frac, icon, stateIcon } = window.TF;
  // status zgłoszenia: klasa plakietki + gotowa ikona (zgłoszenie = dymek, zrobione = koło ✓, w drodze = śmieciarka)
  const BADGE = { przyjete: ['report', stateIcon('report'), 'Przyjęte'], w_realizacji: ['progress', icon('truck'), 'W realizacji'], zrealizowane: ['ok', stateIcon('ok'), 'Zrealizowane'] };
  const MINE = 'tf-moje', MINE_MAX = 5;
  const readMine = () => { try { const m = JSON.parse(localStorage.getItem(MINE)); return Array.isArray(m) ? m : []; } catch (e) { return []; } };
  const saveMine = (nr, kosz) => {
    try { localStorage.setItem(MINE, JSON.stringify([{ nr, kosz, o: window.TF.now().toISOString() }, ...readMine().filter(m => m.nr !== nr)].slice(0, MINE_MAX))); }
    catch (e) { /* tryb prywatny: zgłoszenie i tak ma numer na ekranie sukcesu */ }
  };

  // ---------- start: skan QR + „Twoje zgłoszenia” ----------
  const mineBox = document.getElementById('m-mine');
  if (mineBox) {
    const dlg = document.getElementById('scan-dialog');
    document.querySelector('[data-scan]').addEventListener('click', () => dlg.showModal());
    dlg.querySelector('[data-close]').addEventListener('click', () => dlg.close());
    const mine = readMine().filter(m => /^(TF|WD)-\d+$/.test(m?.nr || ''));  // WD = dzikie wysypisko (wysypisko.js)
    document.getElementById('m-mine-empty').hidden = mine.length > 0;
    const day = iso => { const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleString('pl-PL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }); };
    mineBox.innerHTML = mine.map(m => `<li class="m-row"><a href="${m.nr.startsWith('WD') ? '/wysypisko/' : '/zgloszenie/'}${m.nr}">
      <span class="m-row-txt"><b class="num">${m.nr}</b><span>${esc(m.kosz)}${day(m.o) ? ` · ${day(m.o)}` : ''}</span></span>
      <span class="m-row-st" data-nr="${m.nr}"></span>${icon('chevron-right', 'i-sm')}</a></li>`).join('');
    mineBox.querySelectorAll('[data-nr]').forEach(async el => {
      try {
        if (el.dataset.nr.startsWith('WD')) {
          const w = (await api(`/api/wysypiska/${el.dataset.nr}`)).wysypisko;
          el.innerHTML = `<span class="badge ${['uprzatniete', 'zweryfikowane'].includes(w.status) ? 'ok' : 'neutral'}">${esc(w.etykieta)}</span>`;
          return;
        }
        const [cls, ico, label] = BADGE[(await api(`/api/zgloszenia/${el.dataset.nr}`)).status] || BADGE.przyjete;
        el.innerHTML = `<span class="badge ${cls}">${ico}${label}</span>`;
      } catch (e) { /* numer sprzed resetu demo: bez plakietki, strona statusu powie, że go nie ma */ }
    });
  }

  // ---------- formularz zgłoszenia: jeden ekran ----------
  const form = document.getElementById('m-form');
  if (form) {
    const qrOk = form.dataset.qrOk === '1';
    const send = document.getElementById('m-send'), why = document.getElementById('m-why');
    const reason = () => !qrOk ? 'Zeskanuj kod QR z panelu tego kosza'
      : !form.querySelector('input[name=typ]:checked') ? 'Wybierz, co jest nie tak' : '';
    const sync = () => {  // aria-disabled, nie disabled: przycisk zostaje w kolejności Tab, a powód jest obok niego
      const r = reason();
      why.hidden = !r; why.querySelector('span').textContent = r;
      if (r) send.setAttribute('aria-disabled', 'true'); else send.removeAttribute('aria-disabled');
    };
    sync();
    form.querySelectorAll('input[name=typ]').forEach(r => r.addEventListener('change', sync));
    form.zdjecie.addEventListener('change', () => {
      const f = form.zdjecie.files[0];
      document.getElementById('m-photo-txt').textContent = f ? `Zdjęcie: ${f.name}` : 'Dodaj zdjęcie';
    });
    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (reason() || send.getAttribute('aria-disabled') === 'true') return;  // Enter w polu: bez wysyłki, powód widać obok
      const err = document.getElementById('m-err');
      err.hidden = true; send.setAttribute('aria-disabled', 'true');
      const fd = new FormData();
      fd.append('kosz', form.dataset.bin); fd.append('typ', form.querySelector('input[name=typ]:checked').value);
      fd.append('qr', form.dataset.qr); fd.append('komentarz', form.komentarz.value); fd.append('klient', clientId());
      fd.append('konto', 'demo');  // mieszkanka demo z nagłówka: punkty za trafne zgłoszenie (/api/mieszkaniec/punkty)
      if (form.zdjecie.files[0]) fd.append('zdjecie', form.zdjecie.files[0]);
      try {
        const d = await api('/api/zgloszenia', { method: 'POST', body: fd, signal: AbortSignal.timeout?.(90000) });
        saveMine(d.numer, form.dataset.name);
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
      } finally { sync(); }
    });
  }
  function clientId() {  // losowy identyfikator telefonu: limit zgłoszeń po telefonie, nie po IP sali (decyzja 13)
    try { let id = localStorage.getItem('tf-klient'); if (!id) { id = crypto.randomUUID(); localStorage.setItem('tf-klient', id); } return id; }
    catch (e) { return ''; }
  }

  // ---------- status zgłoszenia ----------
  const st = document.getElementById('m-status');
  if (st) {
    const time = iso => iso ? new Date(iso).toLocaleString('pl-PL', { weekday: 'short', hour: '2-digit', minute: '2-digit' }) : null;
    const render = d => {
      const [cls, ico, label] = BADGE[d.status] || BADGE.przyjete;
      document.getElementById('st-badge').className = `badge ${cls}`;
      document.getElementById('st-badge').innerHTML = `${ico}${label}`;
      const k = d.kosz;
      document.getElementById('st-bin').innerHTML = `${gauge(k.poziom)}<div class="m-bin-txt"><b>${esc(k.nazwa)}</b><span>${esc(k.adres)}</span>
        <div class="m-bin-tags">${fillBadge(k.poziom)}${frac(k.frakcja)}</div></div><b class="m-bin-pct num">${k.poziom}%</b>`;
      document.getElementById('st-ai').innerHTML = d.ai ? `<div class="m-ai"><b>Zdjęcie w zgłoszeniu</b>${window.TF.aiBlock(d.ai)}</div>` : '';
      const order = ['przyjete', 'w_realizacji', 'zrealizowane'], at = order.indexOf(d.status);
      const desc = { przyjete: `${esc(d.typ)}${d.osob > 1 ? ` · ${TF.plural(d.osob, ['zgłosiła', 'zgłosiły', 'zgłosiło'])} ${d.osob} ${TF.plural(d.osob, ['osoba', 'osoby', 'osób'])}` : ''}`, w_realizacji: 'Kierowca MPO jedzie do kosza.',
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
