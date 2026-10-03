// Trash Fairy: wspólne pomocniki UI i scenariusz demo. Progi zapełnienia = _ui.html (lvl).
(() => {
  const TF = window.TF = window.TF || {};
  const nf = new Intl.NumberFormat('pl-PL');
  const nf1 = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 1 });

  TF.esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  TF.num = (v, d = 0) => v == null ? '–' : (d ? nf1 : nf).format(d ? v : Math.round(v));
  TF.icon = (name, cls = '') => `<svg class="i ${cls}" viewBox="0 0 24 24" aria-hidden="true"><use href="${TF.icons}#${name}"/></svg>`;
  TF.lvl = l => l >= 80 ? 'full' : l >= 50 ? 'warn' : 'ok';
  TF.LVL = { ok: ['W porządku', 'check'], warn: ['Zapełnia się', 'trending-up'], full: ['Pełny', 'circle-alert'] };
  TF.fillBadge = l => { const k = TF.lvl(l), [t, i] = TF.LVL[k]; return `<span class="badge ${k}">${TF.icon(i)}${t}</span>`; };
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
      r = await fetch(url, { headers: { Accept: 'application/json', ...(opts.body && !(opts.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}) }, ...opts,
                             body: opts.body && !(opts.body instanceof FormData) ? JSON.stringify(opts.body) : opts.body });
    } catch (e) {
      throw Object.assign(new Error('Brak połączenia. Sprawdź internet i spróbuj ponownie.'), { kod: 'siec' });
    }
    const data = await r.json().catch(() => ({}));
    if (data?.meta?.zegar) TF.clock = data.meta.zegar;
    if (!r.ok) throw Object.assign(new Error(data.blad || data.message || 'Coś poszło nie tak po naszej stronie. Spróbuj za chwilę.'), { kod: data.kod || r.status, data });
    return data;
  };

  TF.toast = (msg, kind = 'ok') => {
    const box = document.getElementById('toasts');
    if (!box) return;
    const t = document.createElement('div');
    t.className = `toast ${kind === 'err' ? 'err' : ''}`;
    t.innerHTML = `${TF.icon(kind === 'err' ? 'circle-alert' : 'circle-check-big')}<span>${TF.esc(msg)}</span>`;
    box.append(t);
    setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, 3600);
  };

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
    let v = null;
    const tick = async () => {
      if (document.hidden) return;
      try { const d = await TF.api('/api/zmiany'); if (v !== null && d.wersja !== v) cb(d); v = d.wersja; onState?.(true); }
      catch (e) { onState?.(false); /* następna próba za chwilę */ }
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
    if (btn) btn.setAttribute('aria-disabled', 'true');
    try {
      await TF.api('/api/demo/reset', { method: 'POST' });
      sessionStorage.removeItem('tf-scenariusz');
      TF.toast('Dane demo przywrócone do stanu początkowego.');
      setTimeout(() => location.reload(), 700);
    } catch (e) { TF.toast(e.message, 'err'); if (btn) btn.removeAttribute('aria-disabled'); }
  };

  // ---------- scenariusz demo: 6 kroków jednej historii ----------
  const bin = () => TF.demoBin;
  TF.SCENARIO = [
    { url: () => `/zglos/${bin()}?qr=${TF.demoQr}`, t: 'Mieszkaniec zgłasza przepełnienie', d: 'Telefon jest przy koszu (położenie symulowane). Wybierz „Przepełniony” i wyślij.' },
    { url: () => `/panel/${bin()}`, t: 'Panel na koszu pokazuje zgłoszenie', d: 'Ekran przy koszu potwierdza: zgłoszone, kierowca dostał informację.' },
    { url: () => '/kierowca', t: 'Kosz trafia na trasę kierowcy', d: 'Jest na górze listy, bo ma zgłoszenie mieszkańca. Kliknij go.' },
    { url: () => `/kierowca/kosz/${bin()}`, t: 'Kierowca opróżnia kosz', d: 'Najpierw „Jadę”, na miejscu „Opróżniono”.' },
    { url: () => { const s = TF.scenario(); return s.nr ? `/zgloszenie/${s.nr}` : `/panel/${bin()}`; }, t: 'Mieszkaniec widzi, że zrobione', d: 'Oś czasu zgłoszenia: przyjęte, w realizacji, zrealizowane.' },
    { url: () => '/dashboard', t: 'Miasto widzi efekt', d: 'Zgłoszenie i odbiór są już w liczbach dashboardu.' },
  ];
  TF.scenario = () => { try { return JSON.parse(sessionStorage.getItem('tf-scenariusz')) || {}; } catch (e) { return {}; } };
  TF.setScenario = s => { try { sessionStorage.setItem('tf-scenariusz', JSON.stringify(s)); } catch (e) { /* tryb prywatny */ } };
  TF.startScenario = () => { TF.setScenario({ step: 0, on: true }); location.href = TF.SCENARIO[0].url(); };
  TF.goStep = i => { const s = { ...TF.scenario(), step: i, on: true }; TF.setScenario(s); location.href = TF.SCENARIO[i].url(); };

  function renderScenario() {
    const s = TF.scenario(), slot = document.getElementById('scenario-slot');
    if (!s.on || !slot) return;
    const i = s.step || 0, st = TF.SCENARIO[i], last = i === TF.SCENARIO.length - 1;
    slot.innerHTML = `<div class="scenario" role="region" aria-label="Scenariusz demo">
      <span class="scenario-step">Krok ${i + 1} z ${TF.SCENARIO.length}</span>
      <div class="scenario-text"><b>${st.t}</b>${st.d}</div>
      <div class="scenario-dots" aria-hidden="true">${TF.SCENARIO.map((_, j) => `<i class="${j <= i ? 'on' : ''}"></i>`).join('')}</div>
      ${i > 0 ? `<button class="btn btn-ghost btn-sm" data-sc="prev">${TF.icon('arrow-left')}Wstecz</button>` : ''}
      ${last ? `<button class="btn btn-sm" data-sc="end">${TF.icon('check')}Zakończ</button>`
             : `<button class="btn btn-sm" data-sc="next">Dalej${TF.icon('arrow-right')}</button>`}
      <button class="btn btn-ghost btn-sm" data-sc="close" aria-label="Zamknij scenariusz">${TF.icon('x')}</button></div>`;
    slot.onclick = e => {
      const a = e.target.closest('[data-sc]')?.dataset.sc;
      if (a === 'next') TF.goStep(i + 1);
      if (a === 'prev') TF.goStep(i - 1);
      if (a === 'end' || a === 'close') { TF.setScenario({ ...s, on: false }); slot.innerHTML = ''; if (a === 'end') location.href = '/'; }
    };
  }

  document.addEventListener('DOMContentLoaded', () => {
    renderScenario();
    document.querySelectorAll('[data-reset-demo]').forEach(b => b.addEventListener('click', () => TF.resetDemo(b)));
    document.querySelectorAll('[data-start-scenario]').forEach(b => b.addEventListener('click', TF.startScenario));
  });
})();
