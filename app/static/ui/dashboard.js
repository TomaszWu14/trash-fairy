// Dashboard miasta: filtry globalne (w adresie strony), KPI ze sparkline, wykresy ECharts, projekty, szczegóły w modalu.
// Mapa koszy na żywo jest w panelu dyspozytora (/dyspozytor).
(() => {
  const TF = window.TF, { api, esc, icon, num, zl, C } = TF;
  const form = document.getElementById('d-filters');
  const KPI_ICON = { koszt: 'banknote', wywozy: 'truck', zapelnienie: 'gauge', zgloszenia: 'message-square-text', czas_reakcji: 'timer',
                     oszczednosci: 'coins', co2: 'leaf', sla_2h: 'clock', anomalie: 'locate-fixed' };
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
    (form.querySelector(`input[name=okres][value="${CSS.escape(okres)}"]`) || form.querySelector('input[name=okres][value=miesiac]')).checked = true;
    ['od', 'do', 'dzielnica', 'frakcja', 'projekt'].forEach(k => { const el = form.elements[k]; if (el && q.get(k)) el.value = q.get(k); });
  };
  const setFilter = (k, v) => { form.elements[k].value = form.elements[k].value === v ? '' : v; apply(); };
  function apply() {
    const p = params();
    history.replaceState(null, '', p.toString() ? `?${p}` : location.pathname);
    document.querySelectorAll('[data-export]').forEach(a => { a.href = `/api/eksport/${a.dataset.export}.csv${p.toString() ? `?${p}` : ''}`; });
    document.getElementById('f-range').hidden = form.querySelector('input[name=okres]:checked').value !== 'zakres';
    ['dzielnica', 'frakcja', 'projekt'].forEach(k => form.elements[k].classList.toggle('on', !!form.elements[k].value));
    document.getElementById('f-clear').hidden = !['dzielnica', 'frakcja', 'projekt', 'od', 'do'].some(k => p.get(k)) && !p.get('okres');
    load();
  }
  form.addEventListener('change', e => { if (e.target.name !== 'miara') apply(); });
  document.getElementById('f-clear').addEventListener('click', () => { form.reset(); apply(); });

  // ---------- KPI ----------
  const fmt = (k, v = k.wartosc) => {  // jednostkę wybiera wartość docelowa: licznik nie przeskakuje z „zł” na „tys. zł”
    const t = k.wartosc;
    if (v == null) return '–';
    if (k.jednostka === 'zł') return t >= 1e6 ? `${num(v / 1e6, 1)}<small>mln zł</small>` : t >= 1e4 ? `${num(v / 1000, 1)}<small>tys. zł</small>` : `${num(v)}<small>zł</small>`;
    if (k.jednostka === '%') return `${num(v)}<small>%</small>`;
    if (k.jednostka === 'h') return `${num(v, 1)}<small>h</small>`;
    if (k.jednostka === 'kg') return t >= 1000 ? `${num(v / 1000, 1)}<small>t</small>` : `${num(v)}<small>kg</small>`;
    return `${num(v)}${k.jednostka ? `<small>${esc(k.jednostka)}</small>` : ''}`;
  };
  const delta = k => {
    if (k.zmiana_pct == null) return '<span class="delta flat">bez porównania</span>';
    const up = k.zmiana_pct > 0, good = (k.lepiej_gdy === 'mniej') !== up;
    if (Math.abs(k.zmiana_pct) < 0.5) return `<span class="delta flat">bez zmian</span>`;
    const word = `${good ? 'lepiej' : 'gorzej'} niż w poprzednim okresie`;
    return `<span class="delta ${good ? 'good' : 'bad'}" title="${word}">${icon(up ? 'trending-up' : 'trending-down')}${up ? '+' : '−'}${num(Math.abs(k.zmiana_pct), 1)}%<span class="sr-only">, ${word}</span></span>`;
  };
  const plain = (k, v) => k.jednostka === '%' ? `${num(v)}%` : k.jednostka === 'h' ? `${num(v, 1)} h` : num(v);
  const sub = (k, meta) => k.podpis ? `<p class="kpi-sub">${esc(k.podpis)}</p>`
    : k.przed_wdrozeniem != null ? `<p class="kpi-sub" title="${esc(meta.przed_wdrozeniem?.etykieta || '')}">przed wdrożeniem: śr. ${plain(k, k.przed_wdrozeniem)}</p>` : '';
  // oszczędności: zł z wybranego okresu, przeliczenie liniowe i rozwijane „Jaki to plan?” (pola z /api/dashboard/kpi)
  const short = v => v == null ? '–' : v >= 1e4 ? `${num(v / 1000, 1)} tys.` : v < 10 ? v.toLocaleString('pl-PL', { maximumFractionDigits: 2 }) : num(v);  // zł w nagłówku
  const savingsTile = (k, n) => {
    const per = !!k.kosze, s = k.skladniki || {}, st = k.stawki || {};
    const rows = [['Dziennie', k.dziennie], ['Miesiąc', k.miesiac], ['Rok', k.rok]];
    const opis = esc(k.plan_opis || '').replace('szczegóły: /metodologia#koszt-odbioru', 'szczegóły: <a href="/metodologia#koszt-odbioru">jak liczymy koszt odbioru</a>');
    return `<article class="card kpi rise kpi-oszczednosci" data-help="dashboard.kpi_oszczednosci">
      <div class="sv-main"><header class="kpi-h">${icon('coins')}${esc(k.etykieta)}</header>
        <p class="kpi-v num" data-kpi="oszczednosci">${fmt(k)}</p>${k.podpis ? `<p class="kpi-sub">${esc(k.podpis)}</p>` : ''}
        <div class="kpi-f kpi-f-big">${delta(k)}${TF.spark(k.trend.slice(0, n), 220, 72)}</div></div>
      <div class="sv-side"><table class="sv-t"><caption class="sr-only">Oszczędności w złotych, przeliczenie liniowe</caption>
        <thead><tr><td aria-hidden="true">zł</td><th scope="col">Razem</th>${per ? '<th scope="col">Na 1 kosz</th>' : ''}</tr></thead>
        <tbody>${rows.map(([l, v]) => `<tr><th scope="row">${l}</th><td class="num">${short(v)}</td>${per ? `<td class="num">${short(v / k.kosze)}</td>` : ''}</tr>`).join('')}</tbody></table>
      <p class="sv-note">Przeliczenie liniowe z wybranego okresu${per ? `, ${num(k.kosze)} ${TF.plural(k.kosze, ['kosz', 'kosze', 'koszy'])}` : ''} · dane demonstracyjne</p></div>
      <details class="sv-plan"><summary>${icon('circle-help', 'i-sm')}Jaki to plan?${icon('chevron-down', 'i-sm')}</summary>
        <dl class="sv-dl"><div><dt>Plan</dt><dd class="num">${num(k.plan?.odbiory)} odbiorów · ${num(k.plan?.km)} km</dd></div>
          <div><dt>Faktycznie</dt><dd class="num">${num(k.faktycznie?.odbiory)} odbiorów · ${num(k.faktycznie?.km)} km</dd></div>
          <div><dt>Oszczędność</dt><dd class="num">${num(k.odbiory_mniej)} odb. × ${num(st.odbior_zl)} zł = ${zl(s.odbiory_zl)} · ${num(k.km_mniej, 1)} km × ${num(st.km_zl)} zł = ${zl(s.km_zl)}</dd></div></dl>
        <p>${opis}</p></details></article>`;
  };
  const BIG = ['co2', 'wywozy', 'anomalie'];  // rząd efektów obok oszczędności: wyższy kafel, szeroka linia trendu
  function renderKpis(d) {
    document.getElementById('d-period').textContent = `${d.meta.etykieta || ''}${d.meta.od ? ` · ${new Date(d.meta.od).toLocaleDateString('pl-PL')} – ${new Date(d.meta.do).toLocaleDateString('pl-PL')}` : ''}`;
    const n = TF.fullMonths(d.meta).miesiace?.length;  // sparkline bez niepełnego bieżącego miesiąca
    const osz = d.kpi.find(k => k.id === 'oszczednosci'), vsPlan = (v, unit = '') => v == null ? null
      : `${num(Math.abs(v))}${unit} ${v >= 0 ? 'mniej' : 'więcej'} niż w planie`;  // podpis z tych samych liczb co „Jaki to plan?”
    const PLAN_SUB = { co2: vsPlan(osz?.km_mniej, ' km'), wywozy: vsPlan(osz?.odbiory_mniej) };
    d.kpi.forEach(k => { if (!k.podpis && k.przed_wdrozeniem == null && PLAN_SUB[k.id]) k.podpis = PLAN_SUB[k.id]; });
    document.getElementById('d-kpis').innerHTML = d.kpi.map(k => k.id === 'oszczednosci' ? savingsTile(k, n) : `<article class="card kpi rise kpi-${k.id}" data-help="dashboard.kpi_${esc(k.id)}" title="${esc(k.opis || '')}">
      <header class="kpi-h">${icon(KPI_ICON[k.id] || 'circle-dot')}${esc(k.etykieta)}</header>
      <p class="kpi-v num" data-kpi="${esc(k.id)}">${fmt(k)}</p>${sub(k, d.meta)}
      ${BIG.includes(k.id) ? `<div class="kpi-f kpi-f-big">${delta(k)}${TF.spark(k.trend.slice(0, n), 220, 72)}</div>` : `<div class="kpi-f">${delta(k)}${TF.spark(k.trend.slice(0, n))}</div>`}</article>`).join('');
    const pw = d.meta.przed_wdrozeniem;
    document.getElementById('d-kpis').insertAdjacentHTML('beforeend', `<p class="kpi-note">Zmiana wobec poprzedniego okresu tej samej długości. Wykresy i linie trendu: pełne miesiące.${pw ? ` „Przed wdrożeniem”: ${esc(pw.etykieta)}.` : ''}</p>`);
    if (!counted) d.kpi.forEach(k => k.wartosc != null && TF.countUp(document.querySelector(`[data-kpi="${k.id}"]`), k.wartosc, v => fmt(k, v)));
    counted = true;  // tylko przy wejściu: odświeżenia pollingiem nie liczą od zera
  }
  let counted = false;

  // ---------- wykresy ----------
  const fullMonths = TF.fullMonths;  // charts.js: bez niepełnego bieżącego miesiąca
  const chart = id => st.charts[id] || (st.charts[id] = TF.chart(document.getElementById(`ch-${id}`)));
  const tip = { trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: C.line } } };

  function rKoszty(d) {
    d = fullMonths(d);
    const el = document.getElementById('ch-koszty'), empty = !d.miesiace?.length || d.rzeczywiste.every(v => !v);
    TF.chartEmpty(el, empty); if (empty) return chart('koszty').clear();
    const labels = d.miesiace.map(TF.monthLabel), w = d.miesiace.indexOf(d.wdrozenie);
    chart('koszty').setOption({
      animation: TF.anim, tooltip: { ...tip, valueFormatter: v => v == null ? '–' : zl(v) }, grid: { right: 24 },
      legend: { data: ['Rzeczywiste', 'Plan (budżet)'] },
      xAxis: { type: 'category', data: labels, boundaryGap: false },
      yAxis: { type: 'value', scale: true, min: v => Math.floor(v.min * 0.92 / 5000) * 5000, axisLabel: { formatter: v => `${num(v / 1000)} tys.` } },
      series: [
        { name: 'Rzeczywiste', type: 'line', data: d.rzeczywiste, smooth: .3, symbol: 'circle', symbolSize: 6, lineStyle: { width: 3, color: C.brand },
          itemStyle: { color: C.brand }, areaStyle: { opacity: .25, color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: C.brand }, { offset: 1, color: C.surface }]) },
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
      graphic: [{ type: 'text', left: 'center', top: '38%', style: { text: `${num(total, 0)} t`, font: `700 22px ${C.display}`, fill: C.ink, textAlign: 'center' } },
                { type: 'text', left: 'center', top: '50%', style: { text: 'odpadów', font: `500 13px ${C.font}`, fill: C.ink3, textAlign: 'center' } }],
      series: [{ type: 'pie', radius: ['52%', '74%'], center: ['50%', '45%'], avoidLabelOverlap: true, label: { show: false }, padAngle: 2,
                 itemStyle: { borderRadius: 6, borderColor: C.surface, borderWidth: 2 },
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
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: v => miara === 'koszt' ? zl(v) : `${num(v)} ${TF.plural(Math.round(v), ['odbiór', 'odbiory', 'odbiorów'])}` },
      legend: {}, grid: { top: 56 }, xAxis: { type: 'category', data: d.dzielnice, axisLabel: { interval: 0, color: C.ink2, fontWeight: 600, rotate: el.clientWidth < 560 ? 40 : 0 } },
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
      series: [{ name: 'Zgłoszenia', type: 'bar', data: d.liczba, barMaxWidth: 18, itemStyle: { color: C.soft, borderColor: C.brand, borderWidth: 1, borderRadius: [4, 4, 0, 0] } },
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
      tooltip: { formatter: p => `${DNI[p.value[1]]}, ${p.value[0]}:00–${p.value[0] + 1}:00<br><b>${num(p.value[2])} ${TF.plural(p.value[2], ['zgłoszenie', 'zgłoszenia', 'zgłoszeń'])}</b>` },
      xAxis: { type: 'category', data: [...Array(24).keys()], splitArea: { show: false }, axisLabel: { interval: 2, color: C.ink3 } },
      yAxis: { type: 'category', data: DNI, inverse: true, axisLabel: { color: C.ink2, fontWeight: 600 } },
      visualMap: { min: 0, max, calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 10, itemHeight: 120,
                   inRange: { color: [C.soft, C.brand] }, textStyle: { color: C.ink3 }, text: ['więcej', 'mniej'] },  // więcej = mocniejszy akcent w obu motywach
      series: [{ type: 'heatmap', data: rows.map(r => [r[1], r[0], r[2]]), itemStyle: { borderColor: C.surface, borderWidth: 2, borderRadius: 3 } }],
    }, true);
  }
  // ---------- jakość obsługi i kolejka napraw (tabele, bez ECharts) ----------
  const pct = (v, nd = 1) => v == null ? '–' : `${num(v, nd)}%`;
  const when = iso => new Date(iso).toLocaleString('pl-PL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  function rJakosc(d) {
    const rows = d.dzielnice || [], box = document.getElementById('ch-jakosc');
    const L = [`Zgłoszenia w ≤ ${d.norma_h} h`, 'Anomalie ekipy', 'Trafność przycisków (symulacja)'];  // data-l: etykieta kolumny w kartach na telefonie
    box.innerHTML = `<table class="dtable q-table"><thead><tr><th scope="col">Dzielnica</th><th scope="col">${L[0]}</th>
      <th scope="col" class="n">${L[1]}</th><th scope="col" class="n">${L[2]}<span aria-hidden="true">*</span></th></tr></thead><tbody>${rows.map(r => `<tr>
      <th scope="row">${esc(r.dzielnica)}</th>
      <td data-l="${L[0]}"><div class="q-sla"><b class="num">${pct(r.sla_2h_pct)}</b><div class="bar" aria-hidden="true"><i style="--p:${((r.sla_2h_pct || 0) / 100).toFixed(3)}"></i></div></div>
        <small>z ${num(r.sla_ocenione)} ${TF.plural(r.sla_ocenione, ['zgłoszenia', 'zgłoszeń', 'zgłoszeń'])}</small></td>
      <td class="n" data-l="${L[1]}"><b class="num">${num(r.anomalie)}</b><small>${pct(r.anomalie_pct, 1)} z ${num(r.wywozy)} ${TF.plural(r.wywozy, ['odbioru', 'odbiorów', 'odbiorów'])}</small></td>
      <td class="n" data-l="${L[2]}*">${r.trafnosc_pct == null ? '<small>brak danych</small>' : `<b class="num">${pct(r.trafnosc_pct)}</b><small>z ${num(r.trafnosc_rozstrzygniete)} sprawdzeń w symulacji</small>`}</td></tr>`).join('')}</tbody></table>`;
    document.getElementById('q-note').textContent = `Dane demonstracyjne. Norma: odbiór w ≤ ${d.norma_h} h od zgłoszenia (liczone zgłoszenia zamknięte albo otwarte dłużej niż ${d.norma_h} h). `
      + `Anomalia: odbiór potwierdzony dalej niż ${d.prog_m} m od kosza. * ${d.trafnosc_zrodlo}`;
  }
  function rNaprawy(d) {
    const list = d.naprawy || [], box = document.getElementById('ch-naprawy'), count = document.getElementById('rq-count');
    const late = list.filter(x => x.po_terminie).length;
    count.hidden = !list.length;
    count.className = `badge ${late ? 'full' : 'neutral'}`;
    count.textContent = late ? `${num(list.length)} · ${num(late)} po terminie` : `${num(list.length)} w kolejce`;
    if (!list.length) {
      box.innerHTML = `<div class="empty rq-empty"><img src="/static/ui/ill/sukces.svg" alt=""><h3>Brak uszkodzeń do naprawy</h3>
        <p>Zgłoszenie „Uszkodzony” od mieszkańca pojawi się tutaj z terminem ${num(d.meta?.sla_h || 24)} h.</p></div>`;
      return;
    }
    box.innerHTML = `<ul class="rq-list">${list.map(x => `<li class="rq-item${x.po_terminie ? ' late' : ''}">
      <span class="rq-ico">${icon('wrench')}</span>
      <div class="rq-main"><b>${esc(x.kosz)}</b><span>${esc(x.adres)}${x.adres ? ' · ' : ''}${esc(x.dzielnica || '')}</span>
        <span>Zgłoszono ${esc(when(x.zgloszono))} · termin ${esc(when(x.termin))}</span>
        ${x.komentarz ? `<q>${esc(x.komentarz)}</q>` : ''}</div>
      <span class="badge ${x.po_terminie ? 'full' : 'ok'}">${icon(x.po_terminie ? 'triangle-alert' : 'clock')}${esc(x.status)}</span></li>`).join('')}</ul>`;
  }

  // ---------- rekomendacje z danych (reguły: recommendations.py, dumping.py, wysypiska.py, crew_points.py) ----------
  const REC = [['compactor', 'full'], ['bigger', 'warn'], ['less_often', 'ok'], ['shelter_intervention', null]];
  const LADDER = [['tablica', 'Tablica i edukacja', 'newspaper'], ['kontrola', 'Straż Miejska', 'shield-check'], ['fotopulapka', 'Fotopułapka', 'camera']];
  const LVL_ST = { tablica: 'warn', kontrola: 'full', fotopulapka: 'full' };
  const day = iso => new Date(iso).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' });
  const rkHead = (ico, t, sub, big = '') => `<header class="rk-h"><span class="rk-ico">${icon(ico)}</span><div><h3>${t}</h3><p>${sub}</p></div>${big}</header>`;
  const rkBig = (n, word) => `<b class="rk-big num">${num(n)}<small>${word}</small></b>`;
  const rkEmpty = (t, ico = 'info') => `<p class="rk-empty">${icon(ico, 'i-sm')}${t}</p>`;
  function rRek(r, w) {
    const box = document.getElementById('d-recs');
    if (!r) { box.innerHTML = `<div class="card empty rk-fail"><img src="/static/ui/ill/pusto.svg" alt=""><h3>Nie udało się wczytać rekomendacji</h3><p>Spróbujemy ponownie przy następnej zmianie danych.</p></div>`; return; }
    cache.rek = r;
    const recs = r.rekomendacje || [], okna = r.meta.okna_dni || {};
    const cap = `<article class="card rk" data-help="dashboard.rek_pojemnosc">${rkHead('package', 'Pojemność i częstotliwość', `Zapełnienie przy odbiorach z ${num(okna.rekomendacje)} dni`, rkBig(recs.length, TF.plural(recs.length, ['kosz', 'kosze', 'koszy'])))}
      ${recs.length ? `<ul class="rk-list">${REC.map(([kind, s]) => {
        const xs = recs.filter(x => x.rodzaj === kind), x = xs[0];
        return x ? `<li>${s ? TF.stateIcon(s, 'rk-st') : `<span class="rk-st rk-alt">${icon('building-2', 'i-sm')}</span>`}<div><b>${esc(x.etykieta)}<span class="rk-c num">${num(xs.length)}</span></b>
          <small>${xs.length > 1 ? 'np. ' : ''}${esc(x.kosz)}: ${esc(x.powod)}</small><small class="rk-eff">${esc(x.efekt)}</small></div></li>` : '';
      }).join('')}</ul>` : rkEmpty('Żaden kosz nie wymaga zmiany pojemności ani częstotliwości odbioru.', 'circle-check-big')}</article>`;
    const sites = r.podrzucanie || [], lv = r.meta.poziomy_podrzucania || {}, pr = r.meta.progi_podrzucania || {};
    const dump = `<article class="card rk" data-help="dashboard.rek_podrzucanie">${rkHead('flag', 'Miejsca podrzucania odpadów', `Odpady obok koszy z ${num(okna.podrzucanie)} dni · reakcja rośnie z liczbą sygnałów`, rkBig(sites.length, TF.plural(sites.length, ['miejsce', 'miejsca', 'miejsc'])))}
      <ol class="rk-ladder" aria-label="Drabinka reakcji">${LADDER.map(([k, t, ico], i) => `<li class="${lv[k] ? 'on' : ''}"><small>Krok ${i + 1} · od ${num(pr[k])} sygnałów</small>
        <span>${icon(ico, 'i-sm')}${t}</span><b class="num">${num(lv[k] || 0)}<small> ${TF.plural(lv[k] || 0, ['miejsce', 'miejsca', 'miejsc'])}</small></b></li>`).join('')}</ol>
      ${sites.length ? `<ul class="rk-list">${sites.slice(0, 3).map(x => `<li>${TF.stateIcon(LVL_ST[x.poziom] || 'warn', 'rk-st')}<div><b>${esc(x.kosz)}</b>
        <small>${esc(x.dzielnica)} · ${esc(x.poziom_etykieta)}</small><small>${esc(x.uzasadnienie)} Zdjęcia: ${num(x.zdjecia)}.</small></div></li>`).join('')}</ul>`
        : rkEmpty(`W ${num(okna.podrzucanie)} dniach nie było sygnałów odpadów obok koszy.`, 'circle-check-big')}
      <p class="rk-note">Kontrolę Straży Miejskiej i fotopułapkę zleca gmina, nie system.</p></article>`;
    const wl = w?.wysypiska || [], open = wl.filter(x => x.status !== 'uprzatniete'), days = w?.okres_dni ?? 90;
    const places = (w?.miejsca || []).filter(s => s.poziom);
    // pusta karta (zero wysypisk / zero punktów): bez kafli „0 / 0 / 0” i wielkiego „0”, niższa, nie rozciąga się do sąsiada
    const wild = `<article class="card rk${wl.length ? '' : ' rk-compact'}" data-help="dashboard.rek_wysypiska">${rkHead('trash', 'Dzikie wysypiska', `Zgłoszenia mieszkańców i ekip MPO z ${num(days)} dni`)}
      ${wl.length ? `<div class="rk-stats"><div><b class="num">${num(open.length)}</b><span>otwarte</span></div><div><b class="num">${num(wl.length - open.length)}</b><span>uprzątnięte</span></div>
        <div><b class="num">${num(places.length)}</b><span>${TF.plural(places.length, ['miejsce', 'miejsca', 'miejsc'])} z drabinką</span></div></div>` : ''}
      ${wl.length ? `<ul class="rk-list">${wl.slice(0, 3).map(x => `<li>${x.status === 'uprzatniete' ? TF.stateIcon('ok', 'rk-st') : `<span class="rk-st rk-dump">${icon('trash', 'i-sm')}</span>`}
        <div><b>${esc(x.numer)} · ${esc(x.etykieta)}</b><small>${esc((x.rodzaje || []).join(', ') || 'rodzaj nieznany')}${x.ilosc ? ` · ${num(x.ilosc)} worków lub sztuk` : ''} · ${day(x.zgloszono)}</small></div></li>`).join('')}</ul>`
        : rkEmpty(w ? `W ${num(days)} dniach nikt nie zgłosił dzikiego wysypiska.` : 'Nie udało się wczytać wysypisk.')}
      <p class="rk-note">Położenie z pinezki albo GPS, bez danych osobowych; uprzątnięcie potwierdza ekipa.</p></article>`;
    const p = r.punkty_ekip || {}, poz = p.pozycje || [];
    const crew = `<article class="card rk${p.suma ? '' : ' rk-compact'}" data-help="dashboard.rek_punkty">${rkHead('users', 'Punkty ekip', `Trasa ${esc(p.trasa || '–')} · ${num(p.okres_dni)} dni`, p.suma ? rkBig(p.suma, 'pkt') : '')}
      ${poz.length ? `<ul class="rk-list">${poz.slice(0, 3).map(x => `<li><span class="rk-pts num">+${num(x.punkty)}</span><div><b>${esc(x.kosz)}</b><small>${esc(x.opis)} · ${day(x.data)}</small></div></li>`).join('')}</ul>`
        : rkEmpty('Brak punktów w tym okresie: ekipa dostaje je tylko za potwierdzone sygnały.')}
      <details class="rk-rules"><summary>Za co są punkty${icon('chevron-down', 'i-sm')}</summary>
        <ul>${(p.zasady || []).map(z => `<li><b class="num">+${num(z.punkty)}</b><span>${esc(z.za)}</span></li>`).join('')}</ul></details>
      <p class="rk-note">${esc(p.uwaga || 'O premii decyduje regulamin MPO.')}</p></article>`;
    box.innerHTML = cap + dump + wild + crew;
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
        <div class="p-effect"><b class="num">${esc(TF.effect(p))}<small>${p.efekt_wartosc == null ? 'efekt po wdrożeniu' : 'kluczowy efekt'}</small></b>${TF.spark(p.trend, 88, 30)}</div>
        <div class="p-meta"><div><span>Postęp</span><b class="num">${num(p.postep_pct)}%</b></div><div class="bar"><i style="--p:${(p.postep_pct / 100).toFixed(3)}"></i></div>
          <div><span>Budżet: wykorzystano</span><b class="num">${zl(p.wykorzystano)} z ${zl(p.budzet)}</b></div><div class="bar budget"><i style="--p:${Math.min(1, used).toFixed(3)}"></i></div></div></a>`;
    }).join('');
  }

  // ---------- szczegóły (drill-down) ----------
  const dlg = document.getElementById('d-modal');
  dlg.querySelector('[data-close]').addEventListener('click', () => dlg.close());
  const table = (head, rows) => `<table class="dtable"><thead><tr>${head.map(h => `<th class="${h.n ? 'n' : ''}">${h.t}</th>`).join('')}</tr></thead>
    <tbody>${rows.map(r => `<tr>${r.map((c, i) => `<td class="${head[i].n ? 'n' : ''}">${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  function details(kind) {
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
    } else if (kind === 'anomalie' && cache.anomalie) {
      h.textContent = `Anomalie ekipy: odbiory dalej niż ${cache.anomalie.prog_m} m od kosza`;
      const list = cache.anomalie.lista;
      b.innerHTML = list.length ? `${table([{ t: 'Kosz' }, { t: 'Dzielnica' }, { t: 'Data' }, { t: 'Odległość', n: 1 }],
        list.map(a => [`<b>${esc(a.kosz)}</b><br><small>${esc(a.adres || '')}</small>`, esc(a.dzielnica || ''), esc(when(a.data)), `${num(a.odleglosc_m)} m`]))}
        <p class="q-note">Najnowsze ${num(list.length)} w wybranym okresie. Dane demonstracyjne.</p>`
        : '<div class="empty"><img src="/static/ui/ill/sukces.svg" alt=""><h3>Brak anomalii w tym okresie</h3></div>';
    } else if (kind === 'rekomendacje' && cache.rek) {
      h.textContent = 'Rekomendacje z danych: wszystkie kosze';
      const list = cache.rek.rekomendacje || [];
      b.innerHTML = list.length ? `${table([{ t: 'Kosz' }, { t: 'Rekomendacja' }, { t: 'Powód' }, { t: 'Efekt' }],
        list.map(x => [`<b>${esc(x.kosz)}</b><br><small>${esc(x.dzielnica || '')}${x.adres ? ` · ${esc(x.adres)}` : ''}</small>`, esc(x.etykieta), esc(x.powod), esc(x.efekt)]))}
        <p class="q-note">Reguły z app/recommendations.py, okno ${num(cache.rek.meta.okna_dni?.rekomendacje)} dni. Dane demonstracyjne.</p>`
        : '<div class="empty"><img src="/static/ui/ill/sukces.svg" alt=""><h3>Brak rekomendacji dla tych filtrów</h3></div>';
    } else return;
    dlg.showModal();
  }
  document.querySelectorAll('[data-details]').forEach(b => b.addEventListener('click', () => details(b.dataset.details)));
  document.getElementById('d-print').addEventListener('click', () => window.print());

  // ---------- ładowanie ----------
  const NAMES = ['koszty', 'frakcje', 'dzielnice', 'zgloszenia', 'heatmapa', 'jakosc', 'anomalie'];
  const NO_ECHARTS = ['jakosc', 'anomalie'];
  const RENDER = { koszty: rKoszty, frakcje: rFrakcje, dzielnice: rDzielnice, zgloszenia: rZgloszenia, heatmapa: rHeat,
                   jakosc: rJakosc, anomalie: d => { cache.anomalie = d; } };
  let seq = 0;
  async function load() {
    const my = ++seq, q = params().toString(), qs = q ? `?${q}` : '';
    try {
      const [kpi, naprawy, rek, wys, ...charts] = await Promise.all([api(`/api/dashboard/kpi${qs}`), api(`/api/naprawy${qs}`),
        api(`/api/dashboard/rekomendacje${qs}`).catch(() => null), api('/api/wysypiska').catch(() => null),  // bez nich reszta działa
        ...NAMES.map(n => api(`/api/dashboard/wykresy/${n}${qs}`))]);
      if (my !== seq) return;  // nowszy filtr wygrywa
      cache.wys = wys;
      // odświeżenie przebudowuje karty: rozwinięte „Jaki to plan?” i „Za co są punkty” zostają otwarte
      const open = [...document.querySelectorAll('#d-kpis details[open], #d-recs details[open]')].map(x => x.className);
      renderKpis(kpi);
      rRek(rek, wys);
      document.querySelectorAll('#d-kpis details, #d-recs details').forEach(x => { if (open.includes(x.className)) x.open = true; });
      rNaprawy(naprawy);
      NO_ECHARTS.forEach(n => RENDER[n](charts[NAMES.indexOf(n)]));  // tabele nie czekają na ECharts
      try { await TF.echarts; } catch (_) {
        TF.echarts = TF.loadEcharts();  // kolejna zmiana danych albo filtr spróbuje wczytać wykresy jeszcze raz
        throw new Error('Nie udało się wczytać wykresów. Sprawdź połączenie, spróbujemy ponownie.');
      }
      charts.forEach((d, i) => !NO_ECHARTS.includes(NAMES[i]) && RENDER[NAMES[i]](d));
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
