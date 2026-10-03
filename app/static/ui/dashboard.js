// Dashboard miasta: filtry globalne (w adresie strony), KPI ze sparkline, wykresy ECharts, mapa, projekty, szczegóły w modalu.
(() => {
  const TF = window.TF, { api, esc, icon, num, zl, C } = TF;
  const form = document.getElementById('d-filters');
  const KPI_ICON = { koszt: 'banknote', wywozy: 'truck', zapelnienie: 'gauge', zgloszenia: 'message-square-text', czas_reakcji: 'timer',
                     oszczednosci: 'coins', co2: 'leaf' };
  const cache = {};
  const st = { charts: {} };

  // ---------- filtry ----------
  const params = () => {
    const f = new FormData(form), p = new URLSearchParams();
    const okres = f.get('okres');
    if (okres === 'zakres') { if (f.get('od')) p.set('od', f.get('od')); if (f.get('do')) p.set('do', f.get('do')); }
    else if (okres !== 'miesiac') p.set('okres', okres);
    ['dzielnica', 'frakcja', 'projekt'].forEach(k => f.get(k) && p.set(k, f.get(k)));
    return p;
  };
  const fromUrl = () => {
    const q = new URLSearchParams(location.search);
    const okres = q.get('od') || q.get('do') ? 'zakres' : (q.get('okres') || 'miesiac');
    form.querySelector(`input[name=okres][value=${okres}]`).checked = true;
    ['od', 'do', 'dzielnica', 'frakcja', 'projekt'].forEach(k => { const el = form.elements[k]; if (el && q.get(k)) el.value = q.get(k); });
  };
  const setFilter = (k, v) => { form.elements[k].value = form.elements[k].value === v ? '' : v; apply(); };
  function apply() {
    const p = params();
    history.replaceState(null, '', p.toString() ? `?${p}` : location.pathname);
    document.getElementById('f-range').hidden = form.querySelector('input[name=okres]:checked').value !== 'zakres';
    ['dzielnica', 'frakcja', 'projekt'].forEach(k => form.elements[k].classList.toggle('on', !!form.elements[k].value));
    document.getElementById('f-clear').hidden = !['dzielnica', 'frakcja', 'projekt', 'od', 'do'].some(k => p.get(k)) && !p.get('okres');
    load();
  }
  form.addEventListener('change', e => { if (e.target.name !== 'miara') apply(); });
  document.getElementById('f-clear').addEventListener('click', () => { form.reset(); apply(); });

  // ---------- KPI ----------
  const fmt = k => {
    const v = k.wartosc;
    if (v == null) return '–';
    if (k.jednostka === 'zł') return v >= 1e6 ? `${num(v / 1e6, 1)}<small>mln zł</small>` : v >= 1e4 ? `${num(v / 1000, 1)}<small>tys. zł</small>` : `${num(v)}<small>zł</small>`;
    if (k.jednostka === '%') return `${num(v)}<small>%</small>`;
    if (k.jednostka === 'h') return `${num(v, 1)}<small>h</small>`;
    if (k.jednostka === 'kg') return v >= 1000 ? `${num(v / 1000, 1)}<small>t</small>` : `${num(v)}<small>kg</small>`;
    return `${num(v)}${k.jednostka ? `<small>${esc(k.jednostka)}</small>` : ''}`;
  };
  const delta = k => {
    if (k.zmiana_pct == null) return '<span class="delta flat">bez porównania</span>';
    const up = k.zmiana_pct > 0, good = (k.lepiej_gdy === 'mniej') !== up;
    if (Math.abs(k.zmiana_pct) < 0.5) return `<span class="delta flat">bez zmian</span>`;
    return `<span class="delta ${good ? 'good' : 'bad'}">${icon(up ? 'trending-up' : 'trending-down')}${up ? '+' : '−'}${num(Math.abs(k.zmiana_pct), 1)}%</span>`;
  };
  function renderKpis(d) {
    document.getElementById('d-period').textContent = `${d.meta.etykieta || ''}${d.meta.od ? ` · ${new Date(d.meta.od).toLocaleDateString('pl-PL')} – ${new Date(d.meta.do).toLocaleDateString('pl-PL')}` : ''}`;
    document.getElementById('d-kpis').innerHTML = d.kpi.map(k => `<article class="card kpi rise kpi-${k.id}" title="${esc(k.opis || '')}">
      <header class="kpi-h">${icon(KPI_ICON[k.id] || 'circle-dot')}${esc(k.etykieta)}</header>
      <p class="kpi-v num">${fmt(k)}</p>${k.podpis ? `<p class="kpi-sub">${esc(k.podpis)}</p>` : ''}
      <div class="kpi-f">${delta(k)}${TF.spark(k.trend)}</div>${k.id === 'oszczednosci' && k.kursy != null ? `<p class="kpi-sub">${num(k.kursy)} kursów mniej niż w planie</p>` : ''}</article>`).join('');
    document.getElementById('d-kpis').insertAdjacentHTML('beforeend', '<p class="kpi-note">Zmiana wobec poprzedniego okresu tej samej długości. Wykresy: pełne miesiące.</p>');
  }

  // ---------- wykresy ----------
  const fullMonths = d => {  // bieżący miesiąc demo jest niepełny: pokazujemy tylko pełne miesiące
    const now = new Date(TF.clock || Date.now()), cur = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const n = d.miesiace?.[d.miesiace.length - 1] === cur && now.getDate() < 28 ? d.miesiace.length - 1 : d.miesiace?.length;
    const cut = {}; Object.keys(d).forEach(k => cut[k] = Array.isArray(d[k]) && d[k].length === d.miesiace.length ? d[k].slice(0, n) : d[k]);
    return cut;
  };
  const chart = id => st.charts[id] || (st.charts[id] = TF.chart(document.getElementById(`ch-${id}`)));
  const tip = { trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: C.line } } };

  function rKoszty(d) {
    d = fullMonths(d);
    const el = document.getElementById('ch-koszty'), empty = !d.miesiace?.length || d.rzeczywiste.every(v => !v);
    TF.chartEmpty(el, empty); if (empty) return chart('koszty').clear();
    const labels = d.miesiace.map(TF.monthLabel), w = d.miesiace.indexOf(d.wdrozenie);
    chart('koszty').setOption({
      animation: TF.anim, tooltip: { ...tip, valueFormatter: v => v == null ? '–' : zl(v) },
      legend: { data: ['Rzeczywiste', 'Plan (budżet)'] },
      xAxis: { type: 'category', data: labels, boundaryGap: false },
      yAxis: { type: 'value', scale: true, min: v => Math.floor(v.min * 0.92 / 5000) * 5000, axisLabel: { formatter: v => `${num(v / 1000)} tys.` } },
      series: [
        { name: 'Rzeczywiste', type: 'line', data: d.rzeczywiste, smooth: .3, symbol: 'circle', symbolSize: 6, lineStyle: { width: 3, color: C.brand },
          itemStyle: { color: C.brand }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(91,61,245,.22)' }, { offset: 1, color: 'rgba(91,61,245,0)' }]) },
          markLine: w >= 0 ? { symbol: 'none', silent: true, lineStyle: { color: C.ink2, type: [4, 4] }, label: { formatter: 'Wdrożenie Trash Fairy', color: C.ink2, fontWeight: 600, position: 'insideEndTop' },
                               data: [{ xAxis: labels[w] }] } : undefined },
        { name: 'Plan (budżet)', type: 'line', data: d.plan, smooth: .3, symbol: 'none', lineStyle: { width: 2, type: [6, 4], color: C.ink3 }, itemStyle: { color: C.ink3 } },
      ],
    }, true);
    cache.koszty = d;
  }
  function rFrakcje(d) {
    const el = document.getElementById('ch-frakcje'), rows = d.dane || d.frakcje || [], empty = !rows.some(r => r.masa_t > 0);
    TF.chartEmpty(el, empty); if (empty) return chart('frakcje').clear();
    const total = rows.reduce((a, r) => a + r.masa_t, 0), sel = form.elements.frakcja.value;
    const c = chart('frakcje');
    c.setOption({
      animation: TF.anim, tooltip: { trigger: 'item', formatter: p => `${p.name}<br><b>${num(p.value, 1)} t</b> · ${num(p.percent, 1)}%` },
      legend: { bottom: 0, top: 'auto', left: 'center' },
      graphic: [{ type: 'text', left: 'center', top: '38%', style: { text: `${num(total, 0)} t`, font: `800 22px ${C.font}`, fill: C.ink, textAlign: 'center' } },
                { type: 'text', left: 'center', top: '50%', style: { text: 'odpadów', font: `500 12px ${C.font}`, fill: C.ink3, textAlign: 'center' } }],
      series: [{ type: 'pie', radius: ['52%', '74%'], center: ['50%', '45%'], avoidLabelOverlap: true, label: { show: false }, padAngle: 2,
                 itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
                 emphasis: { scale: true, scaleSize: 6 },
                 data: rows.map(r => ({ name: r.etykieta, value: r.masa_t, key: r.frakcja, itemStyle: { color: C.frac[r.frakcja], opacity: sel && sel !== r.frakcja ? .3 : 1 } })) }],
    }, true);
    c.off('click'); c.on('click', p => setFilter('frakcja', p.data.key));
    cache.frakcje = rows;
  }
  function rDzielnice(d) {
    const el = document.getElementById('ch-dzielnice'), miara = document.querySelector('input[name=miara]:checked').value;
    const empty = !d.dzielnice?.length || !d.serie.some(s => s[miara].some(v => v));
    TF.chartEmpty(el, empty); if (empty) return chart('dzielnice').clear();
    const c = chart('dzielnice'), sel = form.elements.dzielnica.value;
    c.setOption({
      animation: TF.anim,
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => miara === 'koszt' ? zl(v) : `${num(v)} wywozów` },
      legend: {}, xAxis: { type: 'category', data: d.dzielnice, axisLabel: { interval: 0, color: C.ink2, fontWeight: 600 } },
      yAxis: { type: 'value', axisLabel: { formatter: v => miara === 'koszt' ? `${num(v / 1000)} tys.` : num(v) } },
      series: d.serie.map(s => ({ name: s.etykieta, type: 'bar', stack: 'f', barMaxWidth: 44, data: s[miara].map((v, i) => ({ value: v, itemStyle: { opacity: sel && sel !== d.dzielnice[i] ? .3 : 1 } })),
                                  itemStyle: { color: C.frac[s.frakcja], borderRadius: 0 }, emphasis: { focus: 'series' } })),
    }, true);
    c.off('click'); c.on('click', p => setFilter('dzielnica', p.name));
    cache.dzielnice = d;
  }
  document.querySelectorAll('input[name=miara]').forEach(r => r.addEventListener('change', () => cache.dzielnice && rDzielnice(cache.dzielnice)));
  function rZgloszenia(d) {
    d = fullMonths(d);
    const el = document.getElementById('ch-zgloszenia'), empty = !d.miesiace?.length || !d.liczba.some(v => v);
    TF.chartEmpty(el, empty); if (empty) return chart('zgloszenia').clear();
    chart('zgloszenia').setOption({
      animation: TF.anim, tooltip: tip, legend: {},
      xAxis: { type: 'category', data: d.miesiace.map(TF.monthLabel) },
      yAxis: [{ type: 'value', name: '', axisLabel: { formatter: v => num(v) } }, { type: 'value', axisLabel: { formatter: v => `${num(v)} h` }, splitLine: { show: false } }],
      series: [{ name: 'Zgłoszenia', type: 'bar', data: d.liczba, barMaxWidth: 18, itemStyle: { color: C.series[2], borderRadius: [4, 4, 0, 0] } },
               { name: 'Czas reakcji (h)', type: 'line', yAxisIndex: 1, data: d.czas_reakcji_h, smooth: .3, symbolSize: 6, lineStyle: { width: 3, color: C.brand },
                 itemStyle: { color: C.brand }, tooltip: { valueFormatter: v => v == null ? '–' : `${num(v, 1)} h` } }],
    }, true);
  }
  function rHeat(d) {
    const el = document.getElementById('ch-heatmapa'), rows = d.dane || [], max = Math.max(0, ...rows.map(r => r[2]));
    TF.chartEmpty(el, !max); if (!max) return chart('heatmapa').clear();
    const DNI = ['pon.', 'wt.', 'śr.', 'czw.', 'pt.', 'sob.', 'niedz.'];
    chart('heatmapa').setOption({
      animation: TF.anim, grid: { left: 8, right: 8, top: 8, bottom: 40, containLabel: true },
      tooltip: { formatter: p => `${DNI[p.value[1]]}, ${p.value[0]}:00–${p.value[0] + 1}:00<br><b>${num(p.value[2])} zgłoszeń</b>` },
      xAxis: { type: 'category', data: [...Array(24).keys()], splitArea: { show: false }, axisLabel: { interval: 2, color: C.ink3 } },
      yAxis: { type: 'category', data: DNI, inverse: true, axisLabel: { color: C.ink2, fontWeight: 600 } },
      visualMap: { min: 0, max, calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 10, itemHeight: 120,
                   inRange: { color: ['#F4F2FF', '#C9BCFF', '#8B6CFF', '#5B3DF5', '#2E1A9E'] }, textStyle: { color: C.ink3 }, text: ['więcej', 'mniej'] },
      series: [{ type: 'heatmap', data: rows.map(r => [r[1], r[0], r[2]]), itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 3 } }],
    }, true);
  }
  let map, mapLayer;
  function rMapa(d) {
    if (!map) {
      map = L.map('ch-mapa', { zoomControl: false, scrollWheelZoom: false }).setView([50.06, 19.96], 12);
      L.control.zoom({ position: 'bottomright' }).addTo(map); map.attributionControl.setPrefix(false);
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, className: 'tiles-soft', attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(map);
      mapLayer = L.layerGroup().addTo(map);
    }
    mapLayer.clearLayers();
    const kosze = d.kosze || [], hot = d.goraco || [], maxw = Math.max(1, ...hot.map(h => h[2]));
    TF.chartEmpty(document.getElementById('ch-mapa'), !kosze.length, 'Dla tych filtrów nie ma koszy na mapie.');
    hot.forEach(([lat, lon, w]) => L.circle([lat, lon], { radius: 120 + 380 * (w / maxw), stroke: false, fillColor: C.full, fillOpacity: .08 + .22 * (w / maxw), interactive: false }).addTo(mapLayer));
    const COL = { ok: C.ok, warn: C.warn, full: C.full };
    kosze.forEach(k => L.circleMarker([k.lat, k.lon], { radius: k.live ? 6 : 5, weight: 1.5, color: '#fff', fillColor: COL[TF.lvl(k.zapelnienie)], fillOpacity: 1 })
      .bindTooltip(`<b>${esc(k.nazwa)}</b><br>${esc(k.adres || '')}<br>${esc(TF.FRAKCJE[k.frakcja] || '')} · ${num(k.zapelnienie)}%`)
      .on('click', () => details('kosz', k)).addTo(mapLayer));
    if (kosze.length && !st.mapFitted) { map.fitBounds(L.latLngBounds(kosze.map(k => [k.lat, k.lon])).pad(0.05)); st.mapFitted = true; }
    cache.mapa = kosze;
  }

  // ---------- projekty ----------
  const STATUS = { planowany: ['neutral', 'Planowany'], w_realizacji: ['progress', 'W realizacji'], zakonczony: ['ok', 'Zakończony'] };
  function rProjekty(list) {
    const sel = form.elements.projekt;
    if (sel.options.length === 1) list.forEach(p => sel.add(new Option(p.nazwa, p.slug)));
    const box = document.getElementById('d-projects');
    if (!list.length) { box.innerHTML = '<div class="card empty"><img src="/static/ui/ill/pusto.svg" alt=""><h3>Brak projektów</h3></div>'; return; }
    box.innerHTML = list.map(p => {
      const [cls, label] = STATUS[p.status] || ['neutral', p.status], used = p.budzet ? p.wykorzystano / p.budzet : 0;
      return `<a class="card card-hover pcard rise" href="/dashboard/projekty/${encodeURIComponent(p.slug)}">
        <div class="pcard-h"><span class="p-ico">${icon(p.ikona || 'flag')}</span><div><b>${esc(p.nazwa)}</b><span>${esc(p.dzielnica)}</span></div></div>
        <div><span class="badge ${cls}">${label}</span></div>
        <div class="p-effect"><b class="num">${esc(p.efekt_etykieta || '–')}<small>kluczowy efekt</small></b>${TF.spark(p.trend, 88, 30)}</div>
        <div class="p-meta"><div><span>Postęp</span><b class="num">${num(p.postep_pct)}%</b></div><div class="bar"><i style="--p:${(p.postep_pct / 100).toFixed(3)}"></i></div>
          <div><span>Budżet: wykorzystano</span><b class="num">${zl(p.wykorzystano)} z ${zl(p.budzet)}</b></div><div class="bar budget"><i style="--p:${Math.min(1, used).toFixed(3)}"></i></div></div></a>`;
    }).join('');
  }

  // ---------- szczegóły (drill-down) ----------
  const dlg = document.getElementById('d-modal');
  dlg.querySelector('[data-close]').addEventListener('click', () => dlg.close());
  const table = (head, rows) => `<table class="dtable"><thead><tr>${head.map(h => `<th class="${h.n ? 'n' : ''}">${h.t}</th>`).join('')}</tr></thead>
    <tbody>${rows.map(r => `<tr>${r.map((c, i) => `<td class="${head[i].n ? 'n' : ''}">${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  function details(kind, item) {
    const h = document.getElementById('d-modal-h'), b = document.getElementById('d-modal-b');
    if (kind === 'koszty' && cache.koszty) {
      h.textContent = 'Koszty miesięczne: rzeczywiste i plan';
      const d = cache.koszty;
      b.innerHTML = table([{ t: 'Miesiąc' }, { t: 'Rzeczywiste', n: 1 }, { t: 'Plan', n: 1 }, { t: 'Różnica', n: 1 }],
        d.miesiace.map((m, i) => [TF.monthLabel(m) + (m === d.wdrozenie ? ' · wdrożenie' : ''), zl(d.rzeczywiste[i]), zl(d.plan[i]), zl(d.rzeczywiste[i] - d.plan[i])]));
    } else if (kind === 'frakcje' && cache.frakcje) {
      h.textContent = 'Masa odpadów według frakcji';
      const tot = cache.frakcje.reduce((a, r) => a + r.masa_t, 0) || 1;
      b.innerHTML = table([{ t: 'Frakcja' }, { t: 'Masa', n: 1 }, { t: 'Udział', n: 1 }],
        cache.frakcje.map(r => [`<span class="frac" data-f="${esc(r.frakcja)}">${esc(r.etykieta)}</span>`, `${num(r.masa_t, 1)} t`, `${num(100 * r.masa_t / tot, 1)}%`]));
    } else if (kind === 'kosz') {
      h.textContent = item.nazwa;
      b.innerHTML = table([{ t: 'Pole' }, { t: 'Wartość' }], [['Adres', esc(item.adres || '–')], ['Dzielnica', esc(item.dzielnica)],
        ['Frakcja', TF.frac(item.frakcja)], ['Zapełnienie teraz', `${TF.fillBadge(item.zapelnienie)} <b class="num">${num(item.zapelnienie)}%</b>`],
        ['Dane operacyjne', item.live ? 'na żywo (scenariusz demo)' : 'historia miejska (syntetyczna)']]);
    } else return;
    dlg.showModal();
  }
  document.querySelectorAll('[data-details]').forEach(b => b.addEventListener('click', () => details(b.dataset.details)));
  document.getElementById('d-print').addEventListener('click', () => window.print());

  // ---------- ładowanie ----------
  const NAMES = ['koszty', 'frakcje', 'dzielnice', 'zgloszenia', 'heatmapa', 'mapa'];
  const RENDER = { koszty: rKoszty, frakcje: rFrakcje, dzielnice: rDzielnice, zgloszenia: rZgloszenia, heatmapa: rHeat, mapa: rMapa };
  let seq = 0;
  async function load() {
    const my = ++seq, q = params().toString(), qs = q ? `?${q}` : '';
    try {
      const [kpi, ...charts] = await Promise.all([api(`/api/dashboard/kpi${qs}`), ...NAMES.map(n => api(`/api/dashboard/wykresy/${n}${qs}`))]);
      if (my !== seq) return;  // nowszy filtr wygrywa
      renderKpis(kpi);
      charts.forEach((d, i) => RENDER[NAMES[i]](d));
    } catch (e) {
      TF.toast(e.message, 'err');
    }
  }
  async function loadProjects() {
    try { const d = await api('/api/projekty'); rProjekty(d.projekty || d); } catch (e) { TF.toast(e.message, 'err'); }
  }
  async function loadDistricts() {  // lista dzielnic do filtra: zawsze pełna, niezależnie od filtrów w adresie
    try {
      const d = await api('/api/dashboard/wykresy/dzielnice'), sel = form.elements.dzielnica, keep = new URLSearchParams(location.search).get('dzielnica');
      d.dzielnice.forEach(n => sel.add(new Option(n, n)));
      if (keep) sel.value = keep;
    } catch (e) { /* filtr dzielnic zostaje pusty, reszta działa */ }
  }
  fromUrl(); loadDistricts().then(apply); loadProjects();
  TF.watch(() => load(), 5000);  // zdarzenie ze scenariusza (zgłoszenie, odbiór) od razu w liczbach
})();
