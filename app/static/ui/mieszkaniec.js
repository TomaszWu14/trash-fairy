// Perspektywa mieszkańca: skan kodu QR z panelu → zgłoszenie na jednym ekranie (problem → Wyślij) → oś czasu statusu.
// Bez mapy i listy cudzych koszy: mieszkaniec widzi tylko kosz, przy którym stoi, i swoje zgłoszenia (localStorage tf-moje).
(() => {
  const TF = window.TF;
  const { api, esc, gauge, fillBadge, frac, icon, stateIcon } = TF;
  // status zgłoszenia: klasa plakietki + gotowa ikona (zgłoszenie = dymek, zrobione = koło ✓, w drodze = śmieciarka)
  const BADGE = { przyjete: ['report', stateIcon('report'), 'Przyjęte'], w_realizacji: ['progress', icon('truck'), 'W realizacji'], zrealizowane: ['ok', stateIcon('ok'), 'Zrealizowane'] };
  // dzikie wysypisko na liście „Twoje zgłoszenia”: te same klasy i ikony co status w wysypisko.js
  const WD = { uprzatniete: ['ok', stateIcon('ok')], zweryfikowane: ['ok', icon('shield-check')], potwierdzone: ['brand', icon('users')],
               w_toku: ['brand', icon('loader-circle')], do_weryfikacji: ['neutral', icon('circle-help')] };
  const when = iso => { const d = new Date(iso); return !iso || isNaN(d) ? '' : d.toLocaleString('pl-PL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }); };
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
    // symulowany skan: kosz trwającego scenariusza, inaczej losowy z panelem i pewny trasy (lista z serwera, dzisiejsze tokeny)
    let bins = [];
    try { bins = JSON.parse(document.getElementById('scan-bins').textContent); } catch (e) { /* zostaje kosz z HTML */ }
    const pool = bins.filter(b => b.losuj).length ? bins.filter(b => b.losuj) : bins;
    const sim = document.getElementById('scan-sim'), roll = document.getElementById('scan-roll');
    const pick = b => { if (!b) return; sim.href = `/zglos/${b.id}?qr=${encodeURIComponent(b.qr)}`; document.getElementById('scan-sim-n').textContent = b.id; };
    const sc = TF.scenario(), scBin = sc.on && bins.find(b => b.id === +sc.bin);
    let cur = null;
    const rollBin = () => { const rest = pool.filter(b => b !== cur); cur = rest[Math.floor(Math.random() * rest.length)] || cur; pick(cur); };
    if (scBin) pick(scBin);
    else if (pool.length) { rollBin(); roll.hidden = pool.length < 2; roll.addEventListener('click', rollBin); }
    const mine = readMine().filter(m => /^(TF|WD)-\d+$/.test(m?.nr || ''));  // WD = dzikie wysypisko (wysypisko.js)
    document.getElementById('m-mine-empty').hidden = mine.length > 0;
    // wiersz: miejsce, pod nim plakietka statusu + numer i czas (bez ucinania, zawija się na wąskim ekranie)
    mineBox.innerHTML = mine.map(m => `<li><a class="m-row" href="${m.nr.startsWith('WD') ? '/wysypisko/' : '/zgloszenie/'}${m.nr}">
      <span class="m-row-txt"><b>${esc(m.kosz)}</b><span class="m-row-meta"><span class="m-row-st" data-nr="${m.nr}"></span>
      <span><span class="num">${m.nr}</span>${when(m.o) ? ` · ${when(m.o)}` : ''}</span></span></span>${icon('chevron-right', 'i-sm m-row-chev')}</a></li>`).join('');
    mineBox.querySelectorAll('[data-nr]').forEach(async el => {
      try {
        if (el.dataset.nr.startsWith('WD')) {
          const w = (await api(`/api/wysypiska/${el.dataset.nr}`)).wysypisko;
          const [cls, ico] = WD[w.status] || WD.do_weryfikacji;
          el.innerHTML = `<span class="badge ${cls}">${ico}${esc(w.etykieta)}</span>`;
          return;
        }
        const [cls, ico, label] = BADGE[(await api(`/api/zgloszenia/${el.dataset.nr}`)).status] || BADGE.przyjete;
        el.innerHTML = `<span class="badge ${cls}">${ico}${label}</span>`;
      } catch (e) { /* numer sprzed resetu demo: bez plakietki, strona statusu powie, że go nie ma */ }
    });
  }

  // ---------- start: „Twoje punkty” (konto demo z nagłówka; liczby i zasady z /api/mieszkaniec/punkty) ----------
  const pts = document.getElementById('m-points');
  if (pts) {
    const $ = id => document.getElementById(id);
    api('/api/mieszkaniec/punkty').then(p => {
      $('m-pts-sum').innerHTML = `<b class="num">${p.punkty}</b><span>${TF.plural(p.punkty, ['punkt', 'punkty', 'punktów'])}</span>`;
      $('m-pts-empty').hidden = p.ostatnie.length > 0;
      $('m-pts-badges').innerHTML = p.odznaki.map(b => `<span class="badge brand" title="${esc(b.opis)}">${icon('sparkles')}${esc(b.nazwa)}</span>`).join('');
      $('m-pts-list').innerHTML = p.ostatnie.map(x => `<li class="m-row"><span class="m-row-txt"><b>${esc(x.powod)}</b>
        <span>${x.numer ? `<span class="num">${esc(x.numer)}</span> · ` : ''}${esc(when(x.o))}</span></span><b class="m-row-pts num${x.punkty ? '' : ' off'}">${x.punkty ? `+${x.punkty}` : '0'} pkt</b></li>`).join('');
      $('m-pts-rules').innerHTML = (p.zasady || []).map(z => `<li><b class="m-rule-n num">+${z.punkty}</b><span>${esc(z.za)}</span></li>`).join('');
      const left = n => n.brakuje ? `Brakuje <span class="num">${n.brakuje}</span> pkt` : `${icon('check', 'i-sm')}Próg osiągnięty`;
      const next = p.nagrody.find(n => n.brakuje > 0);  // jedna nagroda z paskiem, reszta w „Wszystkie nagrody”
      $('m-pts-next').innerHTML = next ? `<div class="m-reward"><div class="m-reward-h"><b>${esc(next.nazwa)}</b><span class="num">${next.prog} pkt</span></div>
        <progress max="${next.prog}" value="${p.punkty}" aria-label="${esc(next.nazwa)}: ${p.punkty} z ${next.prog} pkt"></progress>
        <span class="m-reward-left">${left(next)}</span></div>`
        : `<p class="m-reward-left">${icon('check', 'i-sm')}Wszystkie progi nagród osiągnięte</p>`;
      $('m-pts-all-t').textContent = `Wszystkie nagrody (${p.nagrody.length})`;
      $('m-pts-rewards').innerHTML = p.nagrody.map(n => `<li class="m-row"><span class="m-row-txt"><b>${esc(n.nazwa)}</b>
        <span class="m-reward-left">${left(n)}</span></span><b class="m-reward-p num">${n.prog} pkt</b></li>`).join('');
      $('m-pts-note').textContent = p.uwaga;
    }).catch(() => { $('m-pts-sum').textContent = 'Nie udało się wczytać punktów. Spróbuj za chwilę.'; });
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
        document.getElementById('m-status-link').href = `/zgloszenie/${d.numer}`;
        ok.hidden = false; ok.querySelector('h1').focus?.();
        // co dalej: tylko z API (trasa kosza, punkty za trafne zgłoszenie); błąd = zostaje zdanie z HTML
        Promise.all([api(`/api/kosze/${form.dataset.bin}`), api(`/api/zgloszenia/${d.numer}`)]).then(([{ kosz: k }, z]) => {
          document.getElementById('m-success-txt').textContent = `${d.dolaczone ? 'Ktoś już zgłosił ten kosz, Twoje zgłoszenie je wzmocniło. ' : ''}${
            k.trasa?.na_trasie ? 'Kosz jest na liście kierowcy MPO na najbliższy kurs.' : 'Ekipa MPO sprawdzi kosz przy kolejnym kursie.'}`;
          const n = z.punkty?.za_trafne, chip = document.getElementById('m-success-pts');
          if (n) { chip.innerHTML = `${icon('coins', 'i-sm')}<span class="num">+${n} pkt po potwierdzeniu przez ekipę</span>`; chip.hidden = false; }
        }).catch(() => {});
        const s = TF.scenario(); if (s.on) { TF.setScenario({ ...s, nr: d.numer }); TF.scenarioNudge?.(); }  // J-53: wyróżnij „Dalej”
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
    const $ = id => document.getElementById(id);
    // J-29: godzina bez dnia tygodnia; data tylko, gdy to inny dzień niż zegar demo albo poprzedni krok; ta sama godzina co krok wcześniej = bez godziny
    const day = iso => new Date(iso).toDateString();
    const stamp = (iso, prev) => {
      const t = new Date(iso).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
      const other = day(iso) !== day(prev || TF.now());
      return other ? `${new Date(iso).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' })}, ${t}` : t;
    };
    const ICO = { przyjete: stateIcon('report', 'i-xl'), w_realizacji: icon('truck', 'i-xl'), zrealizowane: stateIcon('ok', 'i-xl') };
    // TF.watch odpala load() przy każdej zmianie w demo: podmieniamy tylko to, co się zmieniło (czytnik nie powtarza statusu, fokus zostaje)
    const put = (id, html) => { const el = $(id); if (el.tfHtml !== html) { el.tfHtml = html; el.innerHTML = html; } };
    let last = '';
    const render = d => {
      const sig = JSON.stringify(d); if (sig === last) return; last = sig;
      const [cls, , label] = BADGE[d.status] || BADGE.przyjete;
      if ($('st-title').dataset.status !== d.status) {
        $('st-ico').className = `m-st-ico ${cls}`; $('st-ico').innerHTML = ICO[d.status] || ICO.przyjete;
        $('st-title').textContent = label; $('st-title').dataset.status = d.status;
      }
      put('st-lead', esc(`${d.typ}${d.osob > 1 ? ` · ${TF.plural(d.osob, ['zgłosiła', 'zgłosiły', 'zgłosiło'])} ${d.osob} ${TF.plural(d.osob, ['osoba', 'osoby', 'osób'])}` : ''}`));
      const k = d.kosz;
      put('st-bin', `${gauge(k.poziom)}<div class="m-bin-txt"><b>${esc(k.nazwa)}</b><span>${esc(k.adres)}</span>
        <div class="m-bin-tags">${fillBadge(k.poziom)}${frac(k.frakcja)}</div></div><span class="m-bin-now"><b class="m-bin-pct num">${k.poziom}%</b><span>teraz</span></span>`);
      put('st-ai', d.ai ? `<div class="m-ai"><b>Zdjęcie w zgłoszeniu</b>${TF.aiBlock(d.ai)}</div>` : '');
      const order = ['przyjete', 'w_realizacji', 'zrealizowane'], at = order.indexOf(d.status);
      // dowód pod krokiem „Zrealizowane”: bez powtórzenia tego słowa (J-32), potwierdzony zielony, brak zdjęcia szary
      const proofTxt = (d.dowod?.etykieta || '').replace(/^Zrealizowane,\s*/, ''), ok = d.dowod?.potwierdzone;
      const proof = proofTxt ? `<span class="m-proof${ok ? '' : ' off'}">${icon(ok ? 'shield-check' : 'info', 'i-sm')}${esc(proofTxt[0].toUpperCase() + proofTxt.slice(1))}</span>
        ${d.dowod.zdjecie ? `<a class="m-proof-img" href="${esc(d.dowod.zdjecie)}" target="_blank" rel="noopener"><img src="${esc(d.dowod.zdjecie)}" alt="Zdjęcie kosza od ekipy po opróżnieniu" loading="lazy" width="96" height="72"></a>` : ''}` : '';
      const desc = { przyjete: 'Zgłoszenie trafiło do kierowcy MPO.', w_realizacji: at > 1 ? 'Kierowca MPO ruszył do kosza.' : 'Kierowca MPO jedzie do kosza.',
                     zrealizowane: 'Kosz opróżniony. Dziękujemy!' };
      let prev = null;
      put('st-steps', d.kroki.map((s, i) => {
        let txt = i === at + 1 ? (s.id === 'w_realizacji' ? 'Czekamy, aż kierowca ruszy do kosza.' : 'Po opróżnieniu zobaczysz tu godzinę.') : 'Jeszcze nie';
        if (s.o) {
          const same = prev && s.o.slice(0, 16) === prev.slice(0, 16);  // ta sama minuta co krok wcześniej
          txt = `${same ? '' : `<span class="num">${stamp(s.o, prev)}</span> · `}${desc[s.id]}`; prev = s.o;
        }
        return `<li class="${i <= at ? 'done' : ''} ${i === at + 1 ? 'now' : ''}"><span class="tl-dot">${i <= at ? icon('check') : ''}</span>
          <div><b>${s.etykieta}</b><span>${txt}</span>${s.id === 'zrealizowane' && s.o ? proof : ''}</div></li>`;
      }).join(''));
      // punkty za trafne zgłoszenie (kontrakt API: punkty = {za_trafne, przyznane}); brak pola = nic nie pokazujemy
      const p = d.punkty, n = typeof p?.przyznane === 'number' && p.przyznane > 0 ? p.przyznane : p?.za_trafne;
      const chip = !n ? '' : p.przyznane ? `+${n} pkt przyznane` : d.status !== 'zrealizowane' ? `+${n} pkt po potwierdzeniu przez ekipę` : '';
      $('st-pts').hidden = !chip; put('st-pts', chip ? `${icon('coins', 'i-sm')}<span class="num">${chip}</span>` : '');
      $('st-note').hidden = d.status === 'zrealizowane';
    };
    const load = async () => {
      try { render(await api(`/api/zgloszenia/${encodeURIComponent(st.dataset.nr)}`)); }
      catch (e) { if (e.kod === 'zgloszenie_nie_istnieje') { st.hidden = true; document.getElementById('st-missing').hidden = false; } }
    };
    load(); window.TF.watch(load);
  }
})();
