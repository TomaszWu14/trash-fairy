// Jeden motyw dla wszystkich wykresów (ECharts): paleta i typografia z tokens.css, polskie liczby, tooltipy z dokładnymi wartościami.
(() => {
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const C = window.TF.C = {
    ink: css('--ink'), ink2: css('--ink-2'), ink3: css('--ink-3'), line: css('--line'), brand: css('--brand'), soft: css('--brand-soft'),
    ok: css('--fill-ok'), warn: css('--fill-warn'), full: css('--fill-full'),
    series: [1, 2, 3, 4, 5, 6, 7, 8].map(i => css(`--chart-${i}`)),
    frac: { papier: css('--fr-papier'), metale_tworzywa: css('--fr-metale_tworzywa'), szklo: css('--fr-szklo'), bio: css('--fr-bio'), zmieszane: css('--fr-zmieszane') },
    font: css('--font'),
  };
  const axis = { axisLine: { lineStyle: { color: C.line } }, axisTick: { show: false }, axisLabel: { color: C.ink3, fontSize: 12 },
                 splitLine: { lineStyle: { color: C.line, type: [4, 4] } } };
  // ECharts (1 MB) ładowany po pierwszym malowaniu, gdy strona nie dołączyła go tagiem <script> (dashboard: Lighthouse)
  const afterLoad = () => new Promise(ok => document.readyState === 'complete' ? ok() : addEventListener('load', ok, { once: true }));
  window.TF.echarts = (window.echarts ? Promise.resolve() : afterLoad().then(() => new Promise((ok, fail) => {
    const s = Object.assign(document.createElement('script'), { src: document.documentElement.dataset.echarts, onload: ok, onerror: fail });
    document.head.append(s);
  }))).then(() => echarts.registerTheme('tf', theme));
  const theme = {
    color: C.series, backgroundColor: 'transparent',
    textStyle: { fontFamily: C.font, color: C.ink2 },
    grid: { left: 8, right: 12, top: 36, bottom: 8, containLabel: true },
    categoryAxis: { ...axis, splitLine: { show: false } }, valueAxis: { ...axis, axisLine: { show: false } },
    legend: { top: 0, left: 0, icon: 'roundRect', itemWidth: 10, itemHeight: 10, textStyle: { color: C.ink2, fontSize: 12 } },
    tooltip: { backgroundColor: C.ink, borderWidth: 0, padding: [8, 12], textStyle: { color: '#fff', fontSize: 13 },
               extraCssText: 'border-radius:10px;box-shadow:0 10px 30px rgb(13 17 38 / .25);' },
  };
  window.TF.chart = el => {
    const c = echarts.getInstanceByDom(el) || echarts.init(el, 'tf', { renderer: 'svg' });
    new ResizeObserver(() => c.resize()).observe(el);
    return c;
  };
  window.TF.anim = !matchMedia('(prefers-reduced-motion: reduce)').matches;

  // pusty stan wykresu: ilustracja + podpowiedź, co zmienić
  window.TF.chartEmpty = (el, on, msg = 'Zmień okres albo wyczyść filtry.') => {
    let box = el.querySelector('.chart-empty');
    if (!on) { box?.remove(); return; }
    if (!box) { box = document.createElement('div'); box.className = 'chart-empty'; el.append(box); }
    box.innerHTML = `<img src="/static/ui/ill/pusto.svg" alt=""><b>Brak danych dla tych filtrów</b><span>${msg}</span>`;
  };

  // sparkline: SVG bez biblioteki (12 punktów), ostatni punkt zaznaczony
  let gid = 0;
  window.TF.spark = (vals, w = 96, h = 32) => {
    const v = (vals || []).filter(x => x != null);
    if (v.length < 2) return '';
    const lo = Math.min(...v), hi = Math.max(...v), span = hi - lo || 1;
    const pts = v.map((x, i) => [i * (w - 4) / (v.length - 1) + 2, h - 3 - (x - lo) / span * (h - 8)]);
    const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
    const id = `sg${++gid}`, last = pts[pts.length - 1];
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${C.brand}" stop-opacity=".22"/><stop offset="1" stop-color="${C.brand}" stop-opacity="0"/></linearGradient></defs>
      <path d="${d} L${last[0].toFixed(1)} ${h} L2 ${h}Z" fill="url(#${id})"/><path class="l" d="${d}"/><circle cx="${last[0].toFixed(1)}" cy="${last[1].toFixed(1)}" r="2.5"/></svg>`;
  };
  window.TF.MONTHS = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru'];
  window.TF.monthLabel = ym => { const [y, m] = ym.split('-'); return `${window.TF.MONTHS[+m - 1]} ${y.slice(2)}`; };
  window.TF.zl = v => `${window.TF.num(v)} zł`;
})();
