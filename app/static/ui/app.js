// Trash Fairy: wspólne pomocniki UI i scenariusz demo. Progi zapełnienia = _ui.html (lvl).
(() => {
  const TF = window.TF = window.TF || {};
  const nf = new Intl.NumberFormat('pl-PL');
  const nf1 = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 1 });

  TF.esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  TF.num = (v, d = 0) => v == null ? '–' : (d ? nf1 : nf).format(d ? v : Math.round(v));
  TF.icon = (name, cls = '') => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true"><use href="${TF.icons}#${name}"/></svg>`;
  TF.lvl = l => l >= 80 ? 'full' : l >= 50 ? 'warn' : 'ok';
  TF.LVL = { ok: 'W porządku', warn: 'Zapełnia się', full: 'Pełny' };
  // stan = kształt + znak (icons.svg st-*): ok koło ✓, warn romb ↑, full kwadrat !, report dymek …, sensor trójkąt ! (= _ui.html state_icon)
  TF.stateIcon = (k, cls = '') => `<svg class="i si si-${k} ${cls}" viewBox="0 0 24 24" aria-hidden="true"><use href="${TF.icons}#st-${k}"/></svg>`;
  TF.fillBadge = l => { const k = TF.lvl(l); return `<span class="badge ${k}">${TF.stateIcon(k)}${TF.LVL[k]}</span>`; };
  TF.gauge = (level, cls = '') => {
    const l = Math.max(0, Math.min(100, level || 0));
    return `<svg class="gauge lvl-${TF.lvl(l)} ${cls}" viewBox="0 0 48 56" style="--lvl:${(l / 100).toFixed(3)}" role="img" aria-label="Zapełnienie ${Math.round(l)}%">
      <rect class="g-lid" x="4" y="2" width="40" height="6" rx="3"/><path class="g-body" d="M7 12h34l-3.2 38.6A4 4 0 0 1 33.8 54H14.2a4 4 0 0 1-4-3.4z"/>
      <path class="g-fill" d="M7.6 19h32.8l-2.6 31.6A4 4 0 0 1 33.8 54H14.2a4 4 0 0 1-4-3.4z"/><rect class="g-shine" x="13" y="16" width="3" height="30" rx="1.5"/></svg>`;
  };
  TF.FRAKCJE = { papier: 'Papier', metale_tworzywa: 'Metale i tworzywa', szklo: 'Szkło', bio: 'Bio', zmieszane: 'Zmieszane' };
  TF.frac = f => `<span class="frac" data-f="${TF.esc(f)}">${TF.esc(TF.FRAKCJE[f] || f)}</span>`;
  TF.ago = iso => {
    if (!iso) return '';
    const min = Math.round((TF.now() - new Date(iso)) / 60000);
    if (min < 1) return 'przed chwilą';
    if (min < 60) return `${min} min temu`;
    const h = Math.round(min / 60);
    return h < 24 ? `${h} godz. temu` : new Date(iso).toLocaleDateString('pl-PL', { day: 'numeric', month: 'long' });
  };
  TF.clock = null;  // zegar demo (ISO) z ostatniej odpowiedzi API; czasy liczymy względem niego
  TF.now = () => TF.clock ? new Date(TF.clock) : new Date();

  // fetch z jednym formatem błędu {"blad", "kod"}; sieć i 5xx → ludzki komunikat
  TF.api = async (url, opts = {}) => {
    let r;
    try {
      r = await fetch(url, { signal: AbortSignal.timeout?.(15000), headers: { Accept: 'application/json', ...(opts.body && !(opts.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}) }, ...opts,
                             body: opts.body && !(opts.body instanceof FormData) ? JSON.stringify(opts.body) : opts.body });
    } catch (e) {
      throw Object.assign(new Error('Brak połączenia. Sprawdź internet i spróbuj ponownie.'), { kod: 'siec' });
    }
    const data = await r.json().catch(() => ({}));
    if (data?.meta?.zegar) TF.clock = data.meta.zegar;
    if (!r.ok) throw Object.assign(new Error(data.blad || data.message || 'Coś poszło nie tak po naszej stronie. Spróbuj za chwilę.'), { kod: data.kod || r.status, data });
    return data;
  };

  // polska odmiana: 1 zgłoszenie, 2–4 zgłoszenia (bez 12–14), 5+ zgłoszeń
  TF.plural = (n, [one, few, many]) => n === 1 ? one : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)) ? few : many;
  // aria-disabled blokuje też Enter i spację (pointer-events: none działa tylko na mysz i dotyk): bez podwójnych wysyłek
  document.addEventListener('click', e => {
    if (e.target.closest?.('[aria-disabled="true"]')) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);

  TF.toast = (msg, kind = 'ok') => {
    const box = document.getElementById('toasts');
    if (!box) return;
    const t = document.createElement('div');
    t.className = `toast ${kind === 'err' ? 'err' : ''}`;
    t.innerHTML = `${TF.stateIcon(kind === 'err' ? 'full' : 'ok')}<span>${TF.esc(msg)}</span>`;
    box.append(t);
    setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, kind === 'err' ? 10000 : 6000);  // błąd dłużej: trzeba go przeczytać
  };

  // okienko strony (<dialog>: fokus w środku, Esc zamyka) zamiast window.confirm; zwraca element do wypełnienia
  TF.dialog = (id, html) => {
    let d = document.getElementById(id);
    if (!d) {
      d = Object.assign(document.createElement('dialog'), { id, className: 'modal' });
      d.setAttribute('aria-labelledby', `${id}-h`);
      document.body.append(d);
      d.addEventListener('click', e => { if (e.target === d || e.target.closest('[data-close]')) d.close(); });  // klik w tło też zamyka
    }
    d.innerHTML = html;
    return d;
  };
  TF.confirm = ({ title, text, ok, icon = 'check' }) => new Promise(done => {
    const d = TF.dialog('tf-confirm', `<div class="modal-h"><h2 id="tf-confirm-h">${TF.esc(title)}</h2>
      <button class="btn btn-ghost btn-sm" type="button" data-close aria-label="Zamknij">${TF.icon('x')}</button></div>
      <div class="modal-b"><p class="muted">${TF.esc(text)}</p></div>
      <div class="modal-f"><button class="btn" type="button" data-close>Anuluj</button>
        <button class="btn btn-primary" type="button" data-ok>${TF.icon(icon)}${TF.esc(ok)}</button></div>`);
    let yes = false;
    d.querySelector('[data-ok]').onclick = () => { yes = true; d.close(); };
    d.addEventListener('close', () => done(yes), { once: true });
    d.showModal(); d.querySelector('[data-ok]').focus();
  });

  // licznik KPI przy wejściu: cyfry tabularne, blok o stałej wysokości, więc liczenie nie przesuwa układu
  TF.countUp = (el, to, fmt = v => TF.num(v)) => {
    el.innerHTML = fmt(to);
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || !isFinite(to) || !to) return;
    const t0 = performance.now(), dur = 700;
    const step = t => { const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.innerHTML = fmt(p < 1 ? to * e : to); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  };

  // polling zmian: jedna funkcja dla wszystkich perspektyw; wywołuje cb, gdy wersja danych się zmieni.
  // onState(ok) dostaje wynik każdej próby: kiosk pokazuje „Stan z HH:MM”, gdy sieci nie ma
  TF.watch = (cb, ms = 3000, onState = null) => {
    let v = null, busy = false;
    const tick = async () => {
      if (document.hidden || busy) return;  // wolna sieć: bez nakładania się zapytań co kilka sekund
      busy = true;
      try { const d = await TF.api('/api/zmiany'); if (v !== null && d.wersja !== v) cb(d); v = d.wersja; onState?.(true); }
      catch (e) { onState?.(false); /* następna próba za chwilę */ }
      finally { busy = false; }
    };
    tick(); return setInterval(tick, ms);
  };

  // analiza AI zdjęcia ze zgłoszenia: plakietka + rozwijane szczegóły. Status liczy reguła w kodzie (photos.verification)
  const AI = { zweryfikowane: ['ok', 'shield-check'], do_weryfikacji: ['neutral', 'circle-help'], w_toku: ['brand', 'loader-circle'] };
  TF.aiOpen = false;
  document.addEventListener('toggle', e => { if (e.target.matches?.('details.ai')) TF.aiOpen = e.target.open; }, true);
  TF.aiBlock = ai => {
    if (!ai) return '';
    const [cls, ico] = AI[ai.status] || AI.do_weryfikacji;
    const row = (t, v) => v == null || v === '' ? '' : `<div><dt>${t}</dt><dd>${TF.esc(v)}</dd></div>`;
    return `<details class="ai"${TF.aiOpen ? ' open' : ''}><summary><span class="badge ${cls}">${TF.icon(ico)}${TF.esc(ai.etykieta)}</span>
      <span class="ai-more">Pokaż analizę AI${TF.icon('chevron-down', 'i-sm')}</span></summary>
      <dl class="ai-d">${row('Stan na zdjęciu', ai.stan)}${row('Pewność', ai.pewnosc == null ? null : `${Math.round(ai.pewnosc * 100)}%`)}${row('Uzasadnienie', ai.uzasadnienie)}</dl>
      <p class="ai-note">AI opisuje tylko zdjęcie. Status ustala reguła: kosz widoczny, stan zgodny z typem zgłoszenia, pewność od 70%.
        ${ai.zdjecie_publiczne === false && ai.pewnosc != null ? 'Na zdjęciu są osoby lub tablice, więc nie pokazujemy go publicznie.' : ''}</p></details>`;
  };

  // efekt projektu: planowany bez wyniku dostaje krótkie „Start MM.RRRR” zamiast zdania
  TF.effect = p => p.efekt_wartosc == null && p.start ? `Start ${p.start.slice(5, 7)}.${p.start.slice(0, 4)}` : (p.efekt_etykieta || '–');

  TF.resetDemo = async (btn) => {
    const ok = await TF.confirm({ title: 'Przywrócić dane demo?', icon: 'rotate-ccw', ok: 'Przywróć dane',
      text: 'Zgłoszenia i odbiory z ostatnich minut znikną dla wszystkich oglądających. Przywracanie trwa do 15 sekund.' });
    if (!ok) return;
    const label = btn?.innerHTML;
    if (btn) { btn.setAttribute('aria-disabled', 'true'); btn.innerHTML = `${TF.icon('loader-circle', 'spin')}Przywracam dane… (do 15 s)`; }
    try {
      await TF.api('/api/demo/reset', { method: 'POST', signal: AbortSignal.timeout?.(90000) });  // reset na Postgresie ~13 s
      sessionStorage.removeItem('tf-scenariusz');
      try { localStorage.removeItem('tf-pojazd'); localStorage.removeItem('tf-moje'); } catch (_) { /* tryb prywatny */ }  // śmieciarka wraca do bazy, zgłoszenia z pokazu znikają
      TF.toast('Dane demo przywrócone do stanu początkowego.');
      setTimeout(() => location.reload(), 1200);
    } catch (e) { TF.toast(e.message, 'err'); if (btn) { btn.removeAttribute('aria-disabled'); btn.innerHTML = label; } }
  };

  // ---------- scenariusz demo: trzy warianty, losowane w okienku na stronie startowej ----------
  // stan w sessionStorage: { on, step, v: 'A'|'B'|'C', bin, binName, miejsce: {nazwa, lat, lon}, qr (adres z kodu panelu), nr (TF-…), wd (WD-…) }
  TF.scenario = () => { try { return JSON.parse(sessionStorage.getItem('tf-scenariusz')) || {}; } catch (e) { return {}; } };
  TF.setScenario = s => { try { sessionStorage.setItem('tf-scenariusz', JSON.stringify(s)); } catch (e) { /* tryb prywatny */ } };
  const S = () => TF.scenario(), bin = () => S().bin || TF.demoBin, binName = () => S().binName || `Kosz nr ${bin()}`;
  const panel = () => `/panel/${bin()}`, driverList = () => '/kierowca', card = () => `/kierowca/kosz/${bin()}`, dash = () => '/dashboard';
  const ON_LIST = { url: driverList, t: 'Kosz trafia na trasę kierowcy',
    d: () => `Kosze ze zgłoszeniem mieszkańca idą na górę listy, od najpełniejszego. ${binName()} jest podświetlony. Kliknij go albo „Dalej”.` };
  const EMPTY = { url: card, t: 'Kierowca opróżnia kosz', d: 'Najpierw „Jadę”, na miejscu „Opróżniono”. Zdjęcie kosza jest opcjonalne.', act: true };
  const CITY = { url: dash, t: 'Miasto widzi efekt', d: 'Zgłoszenie i odbiór są już w liczbach dashboardu.' };
  const DISPATCH = { url: () => '/dyspozytor?zakladka=zgloszenia', t: 'Dyspozytor widzi zgłoszenie',
    d: () => `Zakładka „Zgłoszenia” odświeża się sama: ${binName()} jest podświetlony i zaznaczony na mapie. „Dodaj do kursu” to decyzja człowieka.` };
  // act: krok czeka na akcję (wysłanie, przycisk, „Opróżniono”), więc „Dalej” jest drugorzędne, dopóki strona nie wywoła TF.scenarioNudge()
  TF.SCENARIOS = {
    A: { nazwa: 'Przepełniony kosz: kod QR', ikona: 'qr-code', kroki: [
      { url: panel, t: 'Mieszkaniec stoi przy koszu', d: 'Kliknij kod QR na panelu: w demo zastępuje aparat telefonu.', act: true },
      { url: () => S().qr || `/zglos/${bin()}`, t: 'Mieszkaniec zgłasza przepełnienie', d: 'Wybierz „Przepełniony” i wyślij. Bez logowania i bez sprawdzania położenia.', act: true },
      { url: panel, t: 'Panel kosza pokazuje zgłoszenie', d: 'Ekran przy koszu potwierdza: zgłoszone, kosz jest na liście kierowcy.' },
      DISPATCH, ON_LIST, EMPTY,
      { url: () => S().nr ? `/zgloszenie/${S().nr}` : '/zglos', t: 'Mieszkaniec widzi, że zrobione', d: 'Status: zrealizowane. Trafne zgłoszenie daje punkty w „Twoich punktach”.' },
      CITY] },
    B: { nazwa: 'Przepełniony kosz: przycisk na panelu', ikona: 'monitor', kroki: [
      { url: panel, t: 'Mieszkaniec naciska przycisk przy koszu', d: 'Naciśnij czerwony „Przepełniony”. Przycisk nie wymaga telefonu, a panel od razu pokaże zgłoszenie.', act: true },
      DISPATCH, ON_LIST, EMPTY,
      { url: panel, t: 'Panel pokazuje „Opróżniono”', d: 'Ekran przy koszu mówi przechodniom, że kosz jest pusty i od kiedy.' },
      CITY] },
    C: { nazwa: 'Dzikie wysypisko', ikona: 'map-pin', kroki: [
      { url: () => '/wysypisko', t: 'Mieszkaniec zgłasza dzikie wysypisko',
        d: () => `Formularz wypełniliśmy przykładem: ${S().miejsce?.nazwa || 'miejsce w Krakowie'}. Dołącz przykładowe zdjęcie i wyślij.`, act: true },
      { url: () => S().wd ? `/wysypisko/${S().wd}` : '/wysypisko', t: 'Zgłoszenie ma numer i status', d: 'AI tylko opisuje zdjęcie. Status nadaje reguła w kodzie.' },
      { url: () => '/dyspozytor?zakladka=zgloszenia', t: 'Dyspozytor widzi wysypisko', d: 'Pinezka na mapie i wpis w „Zgłoszeniach” są podświetlone. Status nadaje reguła w kodzie, AI tylko opisuje zdjęcie.' },
      { url: () => S().wd ? `/wysypisko/${S().wd}?ekipa=1` : '/wysypisko?ekipa=1', t: 'Ekipa MPO sprząta', d: 'Kliknij „Oznacz jako uprzątnięte”. To telefon ekipy, nie zgłaszającego.', act: true },
      { url: () => '/zglos', t: 'Mieszkaniec dostaje punkty', d: 'Karta „Twoje punkty”: punkty za uprzątnięte wysypisko ze zdjęciem.' }] },
  };
  const steps = () => TF.SCENARIOS[S().v]?.kroki || TF.SCENARIOS.A.kroki;
  TF.goStep = i => { TF.setScenario({ ...S(), step: i, on: true }); location.href = steps()[i].url(); };
  TF.startScenario = pick => { TF.setScenario({ ...pick, step: 0, on: true }); location.href = steps()[0].url(); };
  // po udanej akcji na stronie (wysłane, „Opróżniono”, „Uprzątnięte”): „Dalej” staje się przyciskiem głównym
  TF.scenarioNudge = () => document.querySelector('[data-sc="next"]')?.classList.add('btn-primary', 'nudge');

  // adres porównywany z krokiem: ścieżka + tryb ekipy (status wysypiska ma dwa kroki na tej samej ścieżce)
  const key = u => { const x = new URL(u, location.href); return x.pathname + (x.searchParams.get('ekipa') === '1' ? '?ekipa=1' : ''); };
  function renderScenario() {
    const s = S(), slot = document.getElementById('scenario-slot');
    if (!s.on || !slot) return;
    if (s.bin) document.querySelector('.switcher a[href^="/panel/"]')?.setAttribute('href', panel());  // „Panel kosza” w nagłówku = kosz scenariusza
    const all = steps(), here = key(location.href);
    let i = Math.min(s.step || 0, all.length - 1);
    // kliknięcie w samej aplikacji (kosz na liście, przełącznik perspektyw) też przesuwa scenariusz: najpierw kolejne kroki, potem wcześniejsze
    if (key(all[i].url()) !== here) {
      const j = [...all.keys()].slice(i + 1).concat([...all.keys()].slice(0, i).reverse()).find(j => key(all[j].url()) === here);
      if (j !== undefined) { i = j; TF.setScenario({ ...s, step: i }); }
    }
    const st = all[i], last = i === all.length - 1, txt = typeof st.d === 'function' ? st.d() : st.d;
    slot.innerHTML = `<div class="scenario" role="region" aria-label="Scenariusz demo">
      <span class="scenario-step">Krok ${i + 1} z ${all.length}</span>
      <div class="scenario-text"><b>${TF.esc(st.t)}</b>${TF.esc(txt)}</div>
      <div class="scenario-dots" aria-hidden="true">${all.map((_, j) => `<i class="${j <= i ? 'on' : ''}"></i>`).join('')}</div>
      ${i > 0 ? `<button class="btn btn-ghost btn-sm" data-sc="prev">${TF.icon('arrow-left')}Wstecz</button>` : ''}
      ${last ? `<button class="btn btn-primary btn-sm" data-sc="end">${TF.icon('check')}Zakończ</button>`
             : `<button class="btn btn-sm${st.act ? '' : ' btn-primary'}" data-sc="next">Dalej${TF.icon('arrow-right')}</button>`}
      <button class="btn btn-ghost btn-sm" data-sc="close" aria-label="Zamknij scenariusz">${TF.icon('x')}</button></div>`;
    // pasek jest fixed na dole: rezerwujemy pod treścią tyle miejsca, ile zajmuje, żeby nic pod nim nie znikało
    const bar = slot.firstElementChild, pad = () => document.body.style.setProperty('--scenario-h', `${bar.offsetHeight}px`);
    document.body.classList.add('has-scenario'); pad(); new ResizeObserver(pad).observe(bar);
    slot.onclick = e => {
      const a = e.target.closest('[data-sc]')?.dataset.sc;
      if (a === 'next') TF.goStep(i + 1);
      if (a === 'prev') TF.goStep(i - 1);
      if (a === 'end' || a === 'close') { TF.setScenario({ ...s, on: false }); slot.innerHTML = ''; document.body.classList.remove('has-scenario'); if (a === 'end') location.href = '/'; }
    };
  }

  // ---------- okienko „Zacznij scenariusz demo”: losuje wariant i kosz uliczny (A, B) albo miejsce wysypiska (C) ----------
  // preset z adresu (/?scenariusz=A&kosz=18, /?scenariusz=C&miejsce=0) daje ten sam przebieg w testach i w nagraniu
  const rand = a => a[Math.floor(Math.random() * a.length)];
  const json = id => { try { return JSON.parse(document.getElementById(id)?.textContent || '[]'); } catch (e) { return []; } };
  function openPicker(preset = {}) {
    const places = json('sc-miejsca');  // brak listy: tylko A i B
    // kosze z serwera (ui.scenario_bins): losujemy tylko te, które po zgłoszeniu na pewno trafią na trasę kierowcy
    const bins = json('sc-kosze'), pool = bins.filter(b => b.losuj);
    if (!pool.length) pool.push({ id: TF.demoBin, nazwa: `Kosz nr ${TF.demoBin}` });
    const vs = Object.keys(TF.SCENARIOS).filter(v => v !== 'C' || places.length);
    let fixedBin = bins.find(b => b.id === +preset.kosz), fixedPlace = preset.miejsce != null ? places[+preset.miejsce] : null;
    let pick = {};
    const target = v => v === 'C' ? { miejsce: fixedPlace || rand(places) }
      : (b => ({ bin: b.id, binName: b.nazwa }))(fixedBin || (pick.bin && pick.v !== 'C' ? { id: pick.bin, nazwa: pick.binName } : rand(pool)));
    const d = TF.dialog('sc-pick', `<div class="modal-h"><h2 id="sc-pick-h">Scenariusz demo</h2>
        <button class="btn btn-ghost btn-sm" type="button" data-close aria-label="Zamknij">${TF.icon('x')}</button></div>
      <div class="modal-b sc-b">
        <div class="sc-res" aria-live="polite"><span class="eyebrow">Wylosowano</span><b class="sc-res-t"></b><span class="sc-res-w"></span></div>
        <fieldset class="sc-vars"><legend class="label">Albo wybierz wariant</legend>
          ${vs.map(v => { const x = TF.SCENARIOS[v], n = x.kroki.length;
            return `<label class="sc-var"><input type="radio" name="sc-v" value="${v}"><span class="sc-var-ico">${TF.icon(x.ikona)}</span>
              <span class="sc-var-t"><b>${v}. ${TF.esc(x.nazwa)}</b><small>${n} ${TF.plural(n, ['krok', 'kroki', 'kroków'])}</small></span></label>`; }).join('')}
        </fieldset>
      </div>
      <div class="modal-f"><button class="btn" type="button" data-roll>${TF.icon('refresh-cw')}Losuj ponownie</button>
        <button class="btn btn-primary" type="button" data-go>${TF.icon('play')}Zacznij</button></div>`);
    const show = () => {
      d.querySelector(`input[value="${pick.v}"]`).checked = true;
      d.querySelector('.sc-res-t').textContent = `${pick.v}. ${TF.SCENARIOS[pick.v].nazwa}`;
      d.querySelector('.sc-res-w').innerHTML = pick.v === 'C' ? `${TF.icon('map-pin', 'i-sm')}${TF.esc(pick.miejsce.nazwa)}`
        : `${TF.icon('trash-2', 'i-sm')}${TF.esc(pick.binName)}`;
    };
    const set = v => { pick = { v, ...target(v) }; show(); };
    set(vs.includes(preset.v) ? preset.v : rand(vs));
    d.querySelector('.sc-vars').onchange = e => set(e.target.value);
    d.querySelector('[data-roll]').onclick = () => { pick = {}; fixedBin = fixedPlace = null; set(rand(vs)); };  // nowy wariant i nowy kosz albo miejsce (bez presetu z adresu)
    d.querySelector('[data-go]').onclick = () => TF.startScenario(pick);
    d.showModal(); d.querySelector('[data-go]').focus();
  }
  TF.openScenarioPicker = openPicker;

  // motyw: ciemny (domyślny) / jasny; base.html ustawia go przed CSS, tu przełącznik, zapis i zdarzenie 'tf-motyw' (wykresy)
  const syncThemeBtn = () => document.querySelectorAll('.theme-toggle').forEach(b => {
    const dark = document.documentElement.dataset.theme !== 'light';
    b.setAttribute('aria-pressed', dark);
    b.querySelector('use')?.setAttribute('href', `${TF.icons}#${dark ? 'moon' : 'sun'}`);
  });
  TF.setTheme = t => {
    const h = document.documentElement;
    h.dataset.theme = t;
    try { localStorage.setItem('tf-motyw', t); } catch (_) { /* tryb prywatny */ }
    document.querySelector('meta[name=theme-color]')?.setAttribute('content', getComputedStyle(h).getPropertyValue(t === 'light' ? '--surface' : '--bg').trim());
    syncThemeBtn();
    document.dispatchEvent(new CustomEvent('tf-motyw', { detail: t }));
  };
  // wydruk zawsze w jasnym (przeglądarki nie drukują tła): bez zapisu wyboru
  let printTheme = null;
  addEventListener('beforeprint', () => { printTheme = document.documentElement.dataset.theme; document.documentElement.dataset.theme = 'light'; });
  addEventListener('afterprint', () => { if (printTheme) document.documentElement.dataset.theme = printTheme; });

  document.addEventListener('DOMContentLoaded', () => {
    syncThemeBtn();
    document.querySelectorAll('.theme-toggle').forEach(b => b.addEventListener('click', () =>
      TF.setTheme(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light')));
    renderScenario();
    document.querySelectorAll('[data-reset-demo]').forEach(b => b.addEventListener('click', () => TF.resetDemo(b)));
    document.querySelectorAll('[data-start-scenario]').forEach(b => b.addEventListener('click', () => openPicker()));
    const q = new URLSearchParams(location.search);
    if (q.get('scenariusz') && document.querySelector('[data-start-scenario]')) {
      openPicker({ v: q.get('scenariusz').toUpperCase(), kosz: q.get('kosz'), miejsce: q.get('miejsce') });
    }
  });
})();
