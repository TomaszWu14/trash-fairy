// Trash Fairy: tryb „Podpowiedzi”. Ikonka „i” przy każdym [data-help] i przewodnik po stronie. Treści: podpowiedzi.json.
// Klucz bez treści = brak ikonki + console.warn. Miejsce ikonki: data-help-at="after|heading|corner" (domyślnie wg typu elementu).
(() => {
  const TF = window.TF = window.TF || {};
  const KEY = 'tf-podpowiedzi', root = document.documentElement;
  const CTRL = 'button, a, input, select, textarea, label, fieldset, summary, [role=radiogroup], [role=group]';
  const phone = () => matchMedia('(max-width: 640px)').matches;
  const vis = el => !!el && el.getClientRects().length > 0;
  const hosts = new WeakMap(), icons = new WeakMap(), tips = new Map(), warned = new Set();
  let TXT = {}, n = 0, tip = null, tour = null, queued = 0, offer = null;
  const get = k => { try { return localStorage.getItem(k); } catch (_) { return null; } };
  const put = (k, v) => { try { localStorage.setItem(k, v); } catch (_) { /* tryb prywatny: stan tylko do przeładowania */ } };
  let on = get(KEY) !== '0';  // bez localStorage: wł.
  // powitanie i propozycja przewodnika: nie dla automatów (Playwright ma navigator.webdriver), chyba że adres ma ?powitanie=1
  const forced = new URLSearchParams(location.search).get('powitanie') === '1', human = forced || !navigator.webdriver;

  TF.help = { ready: false };
  // id strony: <body data-page> albo ścieżka bez numerów i slugów: "/" → start, "/kierowca/kosz/18" → kierowca_kosz
  TF.help.page = () => document.body.dataset.page || location.pathname.split('/').filter(s => /^[a-z]+$/.test(s)).join('_') || 'start';
  const steps = () => (TXT._przewodniki?.[TF.help.page()] || []).filter(s => vis(document.querySelector(s.sel)));

  function inject(host) {
    const key = host.dataset.help, t = TXT[key];
    if (!t || key.startsWith('_')) {
      if (!warned.has(key)) { warned.add(key); console.warn(`Podpowiedzi: brak treści dla „${key}” w podpowiedzi.json`); }
      return;
    }
    if (icons.get(host)?.isConnected) return;
    const id = `help-tip-${++n}`, btn = document.createElement('button'), box = document.createElement('div');
    btn.type = 'button'; btn.className = 'help-i'; btn.innerHTML = TF.icon('info');
    for (const [a, v] of [['aria-label', `Podpowiedź: ${t.tytul}`], ['aria-expanded', 'false'], ['aria-controls', id], ['aria-describedby', id]]) btn.setAttribute(a, v);
    const part = (k, v) => v ? `<p><span class="help-k">${k}</span>${TF.esc(v)}</p>` : '';
    box.id = id; box.className = 'help-tip'; box.hidden = true; box.setAttribute('role', 'tooltip');
    box.innerHTML = `<p class="help-t">${TF.esc(t.tytul)}</p>${part('Do czego służy', t.cel)}`
      + `${part(t.jak_czytac ? 'Jak czytać' : 'Przykład', t.jak_czytac || t.przyklad)}${part('Skąd to się bierze', t.zrodlo)}`;
    document.body.append(box);
    // kontrolka → zaraz po niej; kontener → koniec pierwszego nagłówka h1–h3, bez nagłówka → prawy górny róg
    const h = host.querySelector('h1, h2, h3'), head = h && !host.contains(h.closest('a, button, summary')) ? h : null;
    const at = host.dataset.helpAt || (host.matches(CTRL) ? 'after' : head ? 'heading' : 'corner');
    const into = at === 'after' ? host.parentElement : at === 'heading' && head ? head : host;
    const bad = into?.closest('a, button, summary');  // przycisk w przycisku albo w linku jest niedozwolony
    if (bad) bad.after(btn);
    else if (at === 'after') host.after(btn);
    else {
      if (into === host) {
        btn.classList.add('at-corner');
        if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
      }
      // ul/ol/dl i grupa <div> w <dl> mogą mieć tylko li/dt/dd: ikonka z rogu siedzi w ostatnim li/dd (pozycja nadal wg hosta)
      const slot = into === host && (host.matches('ul, ol') ? host.querySelector(':scope > li:last-of-type')
        : host.matches('dl, dl > div') ? host.querySelector(':scope > dd:last-of-type, :scope > div:last-of-type > dd:last-of-type') : null);
      (slot || into).append(btn);
    }
    hosts.set(btn, host); icons.set(host, btn); tips.set(box, btn);
  }

  function scan() {
    document.querySelectorAll('[data-help]').forEach(inject);
    for (const [box, btn] of tips) if (!btn.isConnected) { if (tip?.box === box) tip = null; box.remove(); tips.delete(box); }
    const tb = document.querySelector('.help-tour');
    if (tb) tb.hidden = !on || !steps().length;
    document.querySelectorAll('[data-start-tour]').forEach(b => { b.hidden = !on || !steps().length; });
  }

  // chmurka obok prostokąta r: pod spodem, a gdy brak miejsca, nad nim; na telefonie CSS robi z niej panel na dole
  function place(box, r) {
    if (phone()) { box.style.left = box.style.top = ''; return; }
    const m = 8, w = box.offsetWidth, h = box.offsetHeight;
    const top = r.bottom + m + h <= innerHeight - m || r.top - m - h < m ? r.bottom + m : r.top - m - h;
    box.style.left = `${Math.max(m, Math.min(r.left - 12, innerWidth - w - m))}px`;
    box.style.top = `${Math.max(m, Math.min(top, innerHeight - h - m))}px`;
  }
  // mały host (pole, przycisk, kafelek) w całości nad/pod chmurką, żeby jej nie zasłaniała; duży kontener → sama ikonka
  const anchor = t => {
    const b = t.btn.getBoundingClientRect(), h = t.host.getBoundingClientRect();
    return h.height > 160 ? b : { left: b.left, top: Math.min(b.top, h.top), bottom: Math.max(b.bottom, h.bottom) };
  };

  function reflow() {
    if (tip) place(tip.box, anchor(tip));
    if (!tour) return;
    // null = krok bez elementu (powitanie: brak na tej stronie albo ukryty) → chmurka na środku; odłączony = treść przerysowana w JS
    const el = tour.el?.isConnected === false ? (tour.el = document.querySelector(tour.s[tour.i].sel)) : tour.el;
    if (!el) {
      if (!phone()) Object.assign(tour.box.style, { left: `${(innerWidth - tour.box.offsetWidth) / 2}px`, top: `${(innerHeight - tour.box.offsetHeight) / 2}px` });
      else tour.box.style.left = tour.box.style.top = '';
      return;
    }
    const r = el.getBoundingClientRect(), p = 6;
    Object.assign(tour.hl.style, { left: `${r.left - p}px`, top: `${r.top - p}px`, width: `${r.width + 2 * p}px`, height: `${r.height + 2 * p}px` });
    place(tour.box, { left: r.left + 12, top: r.top - p, bottom: r.bottom + p });
  }

  function openTip(btn) {
    closeTip();
    tip = { btn, box: document.getElementById(btn.getAttribute('aria-controls')), host: hosts.get(btn) };
    tip.box.hidden = false; btn.setAttribute('aria-expanded', 'true');
    reflow();
    if (phone()) {  // panel na dole nie może zasłonić pola, którego dotyczy
      const r = anchor(tip), limit = innerHeight - tip.box.offsetHeight - 12;
      if (r.bottom > limit) scrollBy(0, r.bottom - limit);
    }
  }
  function closeTip(focus) {
    if (!tip) return;
    tip.box.hidden = true; tip.btn.setAttribute('aria-expanded', 'false');
    if (focus) tip.btn.focus();
    tip = null;
  }

  // przewodnik po stronie (domyślnie) albo powitanie (welcome = true: kroki bez filtra, nazwa w nagłówku chmurki, done po końcu)
  function startTour(s = steps(), welcome = false, done = null) {
    if (!s.length) return;
    closeTip(); endTour();
    if (!welcome) seen();
    const mk = cls => Object.assign(document.createElement('div'), { className: cls });
    tour = { s, i: 0, welcome, done, bg: mk('tour-bg'), hl: mk('tour-hl'), box: mk('tour') };
    tour.box.tabIndex = -1;
    for (const [a, v] of [['role', 'dialog'], ['aria-modal', 'true'], ['aria-labelledby', 'tour-t']]) tour.box.setAttribute(a, v);
    tour.box.addEventListener('click', e => {
      if (e.target.closest('a')) return tour?.done?.();  // link w kroku powitania: zapisz „widziane”, przeglądarka przejdzie dalej
      const a = e.target.closest('[data-tour]')?.dataset.tour;
      if (a === 'end') endTour(true); else if (a) step(tour.i + (a === 'next' ? 1 : -1), a);
    });
    document.body.append(tour.bg, tour.hl, tour.box);
    step(0);
  }
  function step(i, via) {
    const t = tour, s = t.s[i], last = i === t.s.length - 1, b = (a, cls, html) => `<button type="button" class="btn btn-sm ${cls}" data-tour="${a}">${html}</button>`;
    const el = s.sel && document.querySelector(s.sel), hero = t.welcome && i === 0;  // krok 1 powitania: znak marki i większy tytuł
    t.i = i; t.el = vis(el) ? el : null;
    const link = s.link && s.link !== location.pathname ? `<p class="tour-l"><a class="link" href="${s.link}">${TF.esc(s.link_tekst)}${TF.icon('arrow-right', 'i-sm')}</a></p>` : '';
    t.box.innerHTML = `<div class="tour-top"><p class="tour-n">${t.welcome ? `${TF.icon('sparkles', 'i-sm')}Powitanie · ` : ''}Krok ${i + 1} z ${t.s.length}</p>
      <span class="tour-dots" aria-hidden="true">${t.s.map((_, j) => `<i${j <= i ? ' class="on"' : ''}></i>`).join('')}</span></div>
      ${hero ? `<img class="tour-logo" src="${TF.icons.replace('icons.svg', 'logo.svg')}" alt="" width="56" height="56">` : ''}
      <h2 id="tour-t">${TF.esc(s.tytul)}</h2><p class="tour-x">${TF.esc(s.tekst)}</p>${link}
      <div class="tour-act">${i ? b('prev', 'btn-ghost', `${TF.icon('arrow-left')}Wstecz`) : ''}
      ${last ? b('end', 'btn-primary', `${TF.icon('check')}Zakończ`) : b('end', 'btn-ghost', t.welcome ? 'Pomiń' : 'Zakończ') + b('next', 'btn-primary', `Dalej${TF.icon('arrow-right')}`)}</div>`;
    t.hl.hidden = !t.el; t.bg.classList.toggle('dim', !t.el); t.box.classList.toggle('tour-mid', !t.el); t.box.classList.toggle('tour-hero', hero);
    const behavior = matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    if (t.el && !phone()) t.el.scrollIntoView({ block: 'center', behavior });
    else if (t.el && !t.el.closest('.topbar')) {  // telefon: element tuż pod przyklejonym nagłówkiem, nad panelem na dole (zapas 60vh w help.css)
      const head = Math.max(0, document.querySelector('.topbar')?.getBoundingClientRect().bottom || 0);
      scrollTo({ top: scrollY + t.el.getBoundingClientRect().top - head - 12, behavior });
    }
    reflow();
    (via && t.box.querySelector(`[data-tour="${via}"]`) || t.box).focus({ preventScroll: true });
  }
  function endTour(focus) {
    if (!tour) return;
    const t = tour;
    t.bg.remove(); t.hl.remove(); t.box.remove(); tour = null;
    if (t.done) t.done(focus);
    else if (focus) document.querySelector('.help-tour')?.focus();
  }

  // ---------- powitanie: przewodnik po całej aplikacji (_powitanie), samo przy pierwszej wizycie, potem z przycisku w nagłówku ----------
  const quiet = () => !human || document.body.classList.contains('kiosk-device') || TF.scenario?.().on || !!document.querySelector('dialog[open]');
  // mieszkaniec wchodzi tu z kodu QR albo linku i ma zgłosić szybko: powitanie tylko z przycisku w nagłówku
  const NO_AUTO = new Set(['zglos_kosz', 'zgloszenie', 'wysypisko', 'wysypisko_status']);
  function welcome() {
    const y = scrollY;
    offer?.remove(); offer = null;  // propozycja przewodnika wraca po powitaniu
    startTour(TXT._powitanie || [], true, focus => {
      put('tf-powitanie', '1');
      scrollTo(0, y);
      if (focus) document.querySelector('.help-welcome:not([hidden]), [data-show-welcome]:not([hidden])')?.focus({ preventScroll: true });
      setTimeout(maybeOffer, 400);
    });
  }

  // ---------- propozycja przewodnika: niemodalna karta przy pierwszej wizycie na stronie z przewodnikiem ('tf-strony' = odwiedzone) ----------
  const pages = () => (get('tf-strony') || '').split(',').filter(Boolean);
  function seen() {
    const p = TF.help.page(), all = pages();
    if (!all.includes(p)) put('tf-strony', [...all, p].join(','));
    offer?.remove(); offer = null;
  }
  function maybeOffer() {
    const k = steps().length;
    // strony mieszkańca z QR/linku: karta na dole telefonu zasłaniałaby „Wyślij zgłoszenie”; przewodnik nadal z ikony mapy w nagłówku
    if (!on || !k || tour || offer || quiet() || (!forced && (pages().includes(TF.help.page()) || NO_AUTO.has(TF.help.page())))) return;
    offer = document.createElement('section');
    offer.className = 'tour-offer';
    offer.setAttribute('aria-labelledby', 'tour-offer-t');
    offer.innerHTML = `<span class="tour-offer-ico">${TF.icon('map')}</span>
      <div class="tour-offer-txt"><p class="tour-offer-t" id="tour-offer-t">Pierwszy raz tutaj?</p>
        <p>Pokażemy w ${k} ${TF.plural(k, ['kroku', 'krokach', 'krokach'])}, co jest na tej stronie.</p></div>
      <div class="tour-offer-act"><button type="button" class="btn btn-ghost btn-sm" data-offer="no">Nie teraz</button>
        <button type="button" class="btn btn-primary btn-sm" data-offer="go">${TF.icon('play', 'i-sm')}Pokaż</button></div>`;
    offer.addEventListener('click', e => {
      const a = e.target.closest('[data-offer]')?.dataset.offer;
      if (a === 'go') startTour();
      else if (a) { seen(); document.querySelector('.help-tour')?.focus(); }
    });
    const skip = document.querySelector('body > a.sr-only');  // w kolejności Tab zaraz po „Przejdź do treści”
    if (skip) skip.after(offer); else document.body.prepend(offer);
  }

  function apply() {
    root.classList.toggle('help-off', !on);
    const tg = document.querySelector('.help-toggle');
    if (tg) { tg.hidden = false; tg.setAttribute('aria-pressed', String(on)); tg.querySelector('b').textContent = on ? 'wł.' : 'wył.'; tg.title = tg.textContent; }
    if (!on) { closeTip(); endTour(); offer?.remove(); offer = null; }
    scan();
  }

  // przechwytywanie: klik w „i” nie uruchamia klikalnej karty, w której ikonka siedzi
  document.addEventListener('click', e => {
    const i = e.target.closest?.('.help-i');
    if (i) { e.stopPropagation(); return tip?.btn === i ? closeTip() : openTip(i); }
    if (tip && !tip.box.contains(e.target)) closeTip();
    if (e.target.closest?.('.help-tour, [data-start-tour]')) startTour();
    if (e.target.closest?.('.help-welcome, [data-show-welcome]')) welcome();
    if (e.target.closest?.('.help-toggle')) {
      on = !on;
      try { localStorage.setItem(KEY, on ? '1' : '0'); } catch (_) { /* tryb prywatny: stan tylko do przeładowania */ }
      apply();
      TF.toast?.(on ? 'Podpowiedzi włączone.' : 'Podpowiedzi wyłączone. Włączysz je tym samym przyciskiem w nagłówku.');
    }
  }, true);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && (tour || tip)) { e.preventDefault(); return tour ? endTour(true) : closeTip(true); }
    if (e.key === 'Escape' && offer?.contains(document.activeElement)) { seen(); return document.querySelector('.help-tour')?.focus(); }
    if (e.key !== 'Tab' || !tour) return;
    const f = [...tour.box.querySelectorAll('button, a')], a = document.activeElement;  // Tab nie ucieka poza chmurkę przewodnika
    if (!tour.box.contains(a) || (e.shiftKey ? a === f[0] || a === tour.box : a === f.at(-1))) { e.preventDefault(); (e.shiftKey ? f.at(-1) : f[0]).focus(); }
  });

  document.addEventListener('DOMContentLoaded', async () => {
    try { TXT = await (await fetch(TF.icons.replace('icons.svg', 'podpowiedzi.json'))).json(); }
    catch (e) { console.warn('Podpowiedzi: nie udało się wczytać treści', e); return; }
    apply();
    const main = document.querySelector('main');  // dashboard i trasa kierowcy renderują treść w JS
    if (main) new MutationObserver(() => { queued ||= requestAnimationFrame(() => { queued = 0; scan(); }); }).observe(main, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-help'] });
    addEventListener('scroll', reflow, { capture: true, passive: true });
    addEventListener('resize', reflow);
    if (TXT._powitanie?.length) document.querySelectorAll('.help-welcome, [data-show-welcome]').forEach(b => { b.hidden = false; });
    // najpierw powitanie (pierwsza wizyta w aplikacji), potem propozycja przewodnika; chwila zwłoki: listy i mapy renderują się w JS
    if (TXT._powitanie?.length && !quiet() && (forced || (on && !get('tf-powitanie') && !NO_AUTO.has(TF.help.page())))) welcome();
    else setTimeout(maybeOffer, 1200);
    TF.help.welcome = welcome;
    TF.help.ready = true;
  });
})();
