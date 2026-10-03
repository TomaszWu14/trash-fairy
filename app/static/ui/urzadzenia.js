// Urządzenia na koszach: KPI, filtry (w adresie strony), karty wg pilności, masterdane w modalu. Dane z /api/urzadzenia.
(() => {
  const TF = window.TF, { api, esc, icon, num } = TF;
  const form = document.getElementById('u-filters'), list = document.getElementById('u-list');
  const ST = {  // status → plakietka: kolor + ikona + słowo (nigdy sam kolor)
    brak_sygnalu: ['full', 'wifi-off'], bateria_krytyczna: ['full', 'battery-warning'], autotest: ['warn', 'wrench'],
    wymiana_30: ['warn', 'battery-low'], ok: ['ok', 'check'],
  };
  const BATT = { ok: 'Dobra', warn: 'Niska', full: 'Krytyczna' };
  const date = iso => new Date(iso).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short', year: 'numeric' });
  const dt = iso => iso ? new Date(iso).toLocaleString('pl-PL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '–';
  const badge = d => { const [c, i] = ST[d.status] || ST.ok; return `<span class="badge ${c}">${icon(i)}${esc(d.status_etykieta)}</span>`; };
  const battery = d => `<div class="batt-row"><span class="batt lvl-${d.bateria_poziom}" role="img" aria-label="Bateria ${d.bateria_pct}%, ${BATT[d.bateria_poziom].toLowerCase()}">
      <i style="--p:${(d.bateria_pct / 100).toFixed(3)}"></i></span><b class="num">${d.bateria_pct}%</b>${d.bateria_poziom === 'ok' ? '' : `<span class="batt-l lvl-${d.bateria_poziom}">${BATT[d.bateria_poziom]}</span>`}</div>`;
  const left = d => d.dni_do_wymiany === 0 ? 'Wymiana baterii teraz' : `Wymiana za <b class="num">${num(d.dni_do_wymiany)}</b> ${d.dni_do_wymiany === 1 ? 'dzień' : 'dni'}`;

  // ---------- filtry ----------
  const params = () => { const f = new FormData(form), p = new URLSearchParams(); ['typ', 'dzielnica', 'status'].forEach(k => f.get(k) && p.set(k, f.get(k))); return p; };
  const fromUrl = () => {
    const q = new URLSearchParams(location.search);
    const t = form.querySelector(`input[name=typ][value="${CSS.escape(q.get('typ') || '')}"]`); if (t) t.checked = true;
    form.dataset.status = q.get('status') || ''; form.dataset.dzielnica = q.get('dzielnica') || '';
  };
  function apply() {
    const p = params();
    history.replaceState(null, '', p.toString() ? `?${p}` : location.pathname);
    form.elements.dzielnica.classList.toggle('on', !!form.elements.dzielnica.value);
    document.getElementById('u-clear').hidden = !p.toString();
    load();
  }
  form.addEventListener('change', apply);
  document.getElementById('u-clear').addEventListener('click', () => clearAll());
  const clearAll = () => { form.reset(); form.dataset.status = ''; form.querySelectorAll('input[name=status]').forEach(r => r.checked = !r.value); apply(); };

  function renderChips(statusy, sel) {
    const all = statusy.reduce((a, s) => a + s.liczba, 0);
    document.getElementById('u-chips').innerHTML = [{ status: '', etykieta: 'Każdy status', liczba: all }, ...statusy].map(s => {
      const [c, i] = s.status ? ST[s.status] : ['neutral', 'filter'];
      return `<label class="chip-f${s.liczba ? '' : ' zero'}" data-c="${c}"><input type="radio" name="status" value="${s.status}"${s.status === sel ? ' checked' : ''}>
        <span>${icon(i, 'i-sm')}${esc(s.status === 'ok' ? 'Sprawne' : s.etykieta)}<b class="num">${num(s.liczba)}</b></span></label>`;
    }).join('');
  }
  function fillDistricts(names, sel) {
    const el = form.elements.dzielnica;
    if (!el.dataset.filled) { el.length = 1; names.forEach(n => el.add(new Option(n, n))); el.dataset.filled = '1'; }
    el.value = sel || ''; el.classList.toggle('on', !!el.value);
  }

  // ---------- KPI ----------
  function renderKpis(k) {
    const tiles = [
      ['signal', 'Urządzenia aktywne', `${num(k.aktywne)}<small>/ ${num(k.lacznie)}</small>`, `${num(k.wg_typu.panel || 0)} paneli · ${num(k.wg_typu.czujnik || 0)} czujników`, ''],
      ['battery-low', 'Baterie do wymiany w 30 dni', num(k.do_wymiany_30_dni), k.do_wymiany_30_dni ? 'zaplanuj wymianę z trasą kierowcy' : 'żadna bateria nie kończy się w miesiącu', k.do_wymiany_30_dni ? 'warn' : ''],
      ['wifi-off', 'Bez sygnału > 48 h', num(k.bez_sygnalu), k.bez_sygnalu ? 'sprawdź na miejscu: zasilanie lub antena' : 'wszystkie urządzenia się zgłaszają', k.bez_sygnalu ? 'full' : ''],
      ['activity', 'Odczyty w ostatniej dobie', num(k.odczyty_24h), 'sygnały życia, pomiary i naciśnięcia', ''],
      ['battery-full', 'Średnia bateria', k.srednia_bateria == null ? '–' : `${num(k.srednia_bateria)}<small>%</small>`, 'wszystkie urządzenia w filtrze', ''],
    ];
    document.getElementById('u-kpis').innerHTML = tiles.map(([i, h, v, sub, tone]) => `<article class="card kpi rise${tone ? ` kpi-${tone}` : ''}">
      <header class="kpi-h">${icon(i)}${h}</header><p class="kpi-v num">${v}</p><p class="kpi-sub">${sub}</p></article>`).join('');
  }

  // ---------- karty ----------
  const card = d => `<button type="button" class="card card-hover u-card rise" data-id="${d.id}" data-st="${d.status}" aria-label="${esc(d.kosz.nazwa)}: ${esc(d.status_etykieta)}, bateria ${d.bateria_pct}%. Pokaż masterdane">
      <div class="u-top"><span class="u-ico t-${d.typ}">${icon(d.ikona)}</span>
        <div class="u-name"><b>${esc(d.kosz.nazwa)}</b><span>${d.typ === 'panel' ? 'Panel e-papier' : 'Czujnik zapełnienia'} · ${esc(d.kosz.adres || d.kosz.dzielnica || '')}</span></div></div>
      <div class="u-status">${badge(d)}</div>
      ${battery(d)}
      <p class="u-left">${icon('calendar', 'i-sm')}<span>${left(d)} · ${date(d.wymiana_data)}</span></p>
      <div class="u-foot"><div><span class="subtle">Ostatni odczyt</span><b>${esc(d.ostatni_odczyt.opis)}</b><span class="subtle">${TF.ago(d.ostatni_odczyt.czas)}</span></div>
        <div class="u-spark" title="Odczyty dziennie w 6 pełnych dniach; razem z dzisiejszymi: ${num(d.odczyty_7d)}">${TF.spark(d.odczyty_dni.slice(0, -1), 88, 30)}<span class="subtle num">${num(d.odczyty_7d)} odczytów / 7 dni</span></div></div>
    </button>`;
  const OK_VISIBLE = 12;  // sprawne zwinięte: lista ma prowadzić do problemów, nie do 95 zielonych kart
  let showAll = false, last = [];
  function renderList(items) {
    last = items;
    if (!items.length) {
      list.innerHTML = `<div class="card empty"><img src="/static/ui/ill/pusto.svg" alt=""><h3>Brak urządzeń dla tych filtrów</h3>
        <p>Zmień typ, dzielnicę albo status.</p><button class="btn btn-sm" type="button" data-clear>${icon('x', 'i-sm')}Wyczyść filtry</button></div>`;
      return;
    }
    const alert = items.filter(d => d.status !== 'ok'), ok = items.filter(d => d.status === 'ok');
    const group = (title, sub, arr) => arr.length ? `<section class="u-group"><div class="section-head"><div><h2>${title} <span class="u-count num">${num(arr.length)}</span></h2><p>${sub}</p></div></div>
      <div class="u-grid">${arr.map(card).join('')}</div></section>` : '';
    const more = ok.length - OK_VISIBLE;
    list.innerHTML = group('Wymaga uwagi', 'Najpilniejsze na górze: brak sygnału, krytyczna bateria, autotest, wymiana w 30 dni', alert)
      + group('Sprawne', 'Od najbliższej wymiany baterii', showAll || more <= 0 ? ok : ok.slice(0, OK_VISIBLE))
      + (!showAll && more > 0 ? `<button class="btn u-more" type="button" data-more>${icon('chevron-down', 'i-sm')}Pokaż pozostałe sprawne (${num(more)})</button>` : '');
  }
  list.addEventListener('click', e => {
    if (e.target.closest('[data-clear]')) return clearAll();
    if (e.target.closest('[data-more]')) { showAll = true; return renderList(last); }
    const c = e.target.closest('.u-card[data-id]'); if (c) open(c.dataset.id);
  });

  // ---------- masterdane ----------
  const dlg = document.getElementById('u-modal');
  dlg.querySelector('[data-close]').addEventListener('click', () => dlg.close());
  dlg.addEventListener('close', () => { const q = new URLSearchParams(location.search); q.delete('urzadzenie'); history.replaceState(null, '', q.toString() ? `?${q}` : location.pathname); });
  dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
  const dl = rows => `<dl class="u-dl">${rows.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
  let chart;
  async function open(id) {
    const h = document.getElementById('u-modal-h'), b = document.getElementById('u-modal-b');
    h.textContent = 'Wczytuję…'; document.getElementById('u-modal-id').textContent = ''; b.innerHTML = '<span class="skel" style="height:220px;display:block"></span>';
    if (!dlg.open) dlg.showModal();
    const q = new URLSearchParams(location.search); q.set('urzadzenie', id); history.replaceState(null, '', `?${q}`);
    try {
      const { urzadzenie: d } = await api(`/api/urzadzenia/${encodeURIComponent(id)}`), u = d.urzadzenie, k = d.kosz;
      h.textContent = k.nazwa;
      document.getElementById('u-modal-id').textContent = `${u.typ} · ${u.numer_seryjny} · ${k.dzielnica || ''}`;
      const RODZAJ = { bin: 'Kosz uliczny', shelter: 'Altana śmietnikowa', container: 'Pojemnik do segregacji' };
      b.innerHTML = `<div class="u-mh">${badge(d)}${battery(d)}</div>
        <div class="u-cols">
          <section><h3>${icon('trash-2', 'i-sm')}Kosz</h3>${dl([['Identyfikator', `<span class="num">#${k.id}</span>`], ['Nazwa', esc(k.nazwa)], ['Adres', esc(k.adres || '–')],
            ['Dzielnica', esc(k.dzielnica || '–')], ['Frakcja', TF.frac(k.frakcja)], ['Rodzaj', esc(RODZAJ[k.rodzaj] || k.rodzaj)],
            ['Pojemność', k.pojemnosc_l ? `<span class="num">${num(k.pojemnosc_l)} l</span>` : '–']])}</section>
          <section><h3>${icon(d.ikona, 'i-sm')}Urządzenie</h3>${dl([['Typ', esc(u.typ)], ['Model', esc(u.model)], ['Numer seryjny', `<code>${esc(u.numer_seryjny)}</code>`],
            ['Firmware', `<span class="num">${esc(u.firmware)}</span>`], ['Zainstalowano', date(u.zainstalowano)],
            ['Żywotność baterii', `<span class="num">${num(u.zywotnosc_baterii_dni)} dni</span> <span class="subtle">(założenie demo)</span>`],
            ['Pojemność baterii', `<span class="num">${num(u.pojemnosc_baterii_mah)} mAh</span>`],
            ['Przewidywana wymiana', `${date(u.przewidywana_wymiana)} <span class="subtle">· za ${num(d.dni_do_wymiany)} dni</span>`],
            ['Interwał odczytów', `co ${num(u.interwal_odczytow_min)} min`], ['Ostatni sygnał', `${dt(u.ostatni_sygnal)} <span class="subtle">· ${TF.ago(u.ostatni_sygnal)}</span>`],
            ['Ostatni autotest', `${dt(u.ostatni_autotest)} · ${u.autotest_ok === false ? '<b class="t-bad">nieudany</b>' : 'udany'}`]])}</section>
        </div>
        <section class="u-chart"><div class="chart-h"><div><h3>Odczyty z 7 dni</h3><p>${d.typ === 'panel' ? 'Sygnały życia co godzinę i naciśnięcia przycisku' : 'Pomiary zapełnienia co 15 minut'}; ostatni słupek: dziś do teraz</p></div>
          <b class="num">${num(d.odczyty_7d)}</b></div><div class="u-chart-b" id="u-chart" role="img" aria-label="Liczba odczytów dziennie: ${d.seria.odczyty.join(', ')}"></div></section>
        <div class="u-actions"><a class="btn btn-sm" href="/panel/${k.id}">${icon('monitor', 'i-sm')}Panel kosza</a>
          <span class="subtle">Dane syntetyczne. Bateria czujnika liczona z wieku i tempa zużycia.</span></div>`;
      chart = TF.chart(document.getElementById('u-chart'));
      const C = TF.C, max = Math.max(...d.seria.odczyty);
      chart.setOption({
        animation: TF.anim, grid: { left: 4, right: 4, top: 12, bottom: 4, containLabel: true },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => `${num(v)} odczytów` },
        xAxis: { type: 'category', data: d.seria.dni.map(x => new Date(x).toLocaleDateString('pl-PL', { weekday: 'short', day: 'numeric' })) },
        yAxis: { type: 'value', axisLabel: { formatter: v => num(v) } },
        series: [{ type: 'bar', barMaxWidth: 36, data: d.seria.odczyty.map((v, i) => ({ value: v, itemStyle: { color: i === d.seria.odczyty.length - 1 ? C.soft : C.brand, borderColor: C.brand, borderWidth: i === d.seria.odczyty.length - 1 ? 1 : 0, borderRadius: [6, 6, 0, 0] } })),
                   label: { show: true, position: 'top', color: C.ink2, fontSize: 11, formatter: p => p.value ? num(p.value) : '0' } }],
      }, true);
      if (!max) TF.chartEmpty(document.getElementById('u-chart'), true, 'Urządzenie nie przesłało odczytów w tym tygodniu.');
    } catch (e) {
      h.textContent = 'Nie udało się wczytać';
      b.innerHTML = `<div class="alert">${icon('circle-alert')}<span>${esc(e.message)}</span></div>`;
    }
  }

  // ---------- ładowanie ----------
  let seq = 0;
  async function load() {
    const my = ++seq, q = params().toString();
    try {
      const d = await api(`/api/urzadzenia${q ? `?${q}` : ''}`);
      if (my !== seq) return;
      fillDistricts(d.meta.dzielnice, d.meta.filtry.dzielnica);
      renderChips(d.statusy, d.meta.filtry.status || '');
      document.getElementById('u-clear').hidden = !q;
      document.getElementById('u-sub').textContent = `Stan na ${dt(d.meta.teraz)} · panele z przyciskiem i czujniki pilotażu w Nowej Hucie`;
      renderKpis(d.kpi);
      renderList(d.urzadzenia);
    } catch (e) {
      if (my !== seq) return;
      list.innerHTML = `<div class="card empty"><img src="/static/ui/ill/pusto.svg" alt=""><h3>Nie udało się wczytać urządzeń</h3><p>${esc(e.message)}</p>
        <button class="btn btn-sm" type="button" id="u-retry">${icon('refresh-cw', 'i-sm')}Spróbuj ponownie</button></div>`;
      document.getElementById('u-retry').addEventListener('click', load);
    }
  }
  fromUrl();
  if (form.dataset.status) form.insertAdjacentHTML('beforeend', `<input type="hidden" name="status" value="${esc(form.dataset.status)}" data-init>`);
  if (form.dataset.dzielnica) form.elements.dzielnica.add(new Option(form.dataset.dzielnica, form.dataset.dzielnica, true, true));
  const deep = new URLSearchParams(location.search).get('urzadzenie');  // link do masterdanych konkretnego kosza
  load().then(() => { form.querySelector('[data-init]')?.remove(); if (deep) open(deep); });
  TF.watch(() => load(), 5000);
})();
