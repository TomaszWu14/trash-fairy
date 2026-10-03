// Szczegóły projektu: fakty (status, postęp, budżet, efekt) i cztery wykresy przed/po ze znacznikiem startu.
(() => {
  const TF = window.TF, { api, esc, icon, num, zl, C } = TF;
  const root = document.getElementById('proj');
  const STATUS = { planowany: ['neutral', 'Planowany'], w_realizacji: ['progress', 'W realizacji'], zakonczony: ['ok', 'Zakończony'] };
  const UNIT = { koszt: v => zl(v), wywozy: v => num(v), zapelnienie: v => `${num(v)}%`, czas_reakcji: v => `${num(v, 1)} h` };
  const fact = (ico, label, value, sub = '') => `<article class="card kpi"><header class="kpi-h">${icon(ico)}${label}</header>
    <p class="kpi-v num">${value}</p>${sub ? `<p class="kpi-sub">${sub}</p>` : ''}</article>`;
  (async () => {
    let p;
    try { p = await api(`/api/projekty/${encodeURIComponent(root.dataset.slug)}`); p = p.projekt || p; }
    catch (e) {
      if (e.kod === 'projekt_nie_istnieje' || e.kod === 404) { document.querySelectorAll('#proj > :not(.back):not(#p-missing)').forEach(x => x.hidden = true); document.getElementById('p-missing').hidden = false; }
      else TF.toast(e.message, 'err');
      return;
    }
    document.title = `${p.nazwa} · Trash Fairy`;
    const [cls, label] = STATUS[p.status] || ['neutral', p.status];
    document.getElementById('p-head').innerHTML = `<span class="p-ico">${icon(p.ikona || 'flag', 'i-lg')}</span>
      <div><p class="eyebrow">${esc(p.dzielnica)} · projekt</p><h1>${esc(p.nazwa)}</h1></div><span class="badge ${cls}">${label}</span>`;
    const used = p.budzet ? Math.round(100 * p.wykorzystano / p.budzet) : 0;
    document.getElementById('p-facts').innerHTML = fact('sparkles', 'Kluczowy efekt', esc(p.efekt_etykieta || '–'), 'liczony z danych odbiorów')
      + fact('flag', 'Postęp', `${num(p.postep_pct)}<small>%</small>`, `<span class="bar" style="display:block;margin-top:6px"><i style="--p:${(p.postep_pct / 100).toFixed(3)}"></i></span>`)
      + fact('banknote', 'Budżet', zl(p.budzet), `wykorzystano ${zl(p.wykorzystano)} (${used}%)`)
      + fact('calendar', 'Start', p.start ? new Date(p.start).toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' }) : '–', p.koniec ? `koniec: ${new Date(p.koniec).toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' })}` : '');
    const pp = p.przed_po || {}, months = pp.miesiace || [];
    const start = (pp.start || p.start || '').slice(0, 7);
    ['koszt', 'wywozy', 'zapelnienie', 'czas_reakcji'].forEach(k => {
      const el = document.getElementById(`pc-${k}`), vals = pp[k] || [];
      TF.chartEmpty(el, !vals.some(v => v != null && v !== 0), 'Ten projekt nie ma jeszcze danych przed i po.');
      if (!vals.length) return;
      const labels = months.map(TF.monthLabel), si = months.indexOf(start);
      TF.chart(el).setOption({
        animation: TF.anim, tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '–' : UNIT[k](v) },
        xAxis: { type: 'category', data: labels }, yAxis: { type: 'value', scale: k !== 'koszt', axisLabel: { formatter: v => k === 'koszt' ? `${num(v / 1000)} tys.` : num(v) } },
        series: [{ type: 'bar', barMaxWidth: 22, data: vals.map((v, i) => ({ value: v, itemStyle: { color: si >= 0 && i >= si ? C.brand : '#C9CFDC', borderRadius: [4, 4, 0, 0] } })),
                   markLine: si >= 0 ? { symbol: 'none', silent: true, lineStyle: { color: C.ink2, type: [4, 4] }, label: { formatter: 'start projektu', color: C.ink2, position: 'insideEndTop' }, data: [{ xAxis: labels[si] }] } : undefined }],
      });
    });
  })();
})();
