// Szczegóły projektu: fakty (status, postęp, budżet, efekt) i cztery wykresy przed/po ze znacznikiem startu.
(() => {
  const TF = window.TF, { api, esc, icon, num, zl, C } = TF;
  const root = document.getElementById('proj');
  const back = document.querySelector('.back');  // powrót do dashboardu z tymi samymi filtrami
  if (back && document.referrer.startsWith(`${location.origin}/dashboard?`)) back.href = document.referrer;
  const STATUS = { planowany: ['neutral', 'Planowany'], w_realizacji: ['progress', 'W realizacji'], zakonczony: ['ok', 'Zakończony'] };
  const UNIT = { koszt: v => zl(v), wywozy: v => num(v), zapelnienie: v => `${num(v)}%`, czas_reakcji: v => `${num(v, 1)} h` };
  const METRIC = {  // miara efektu (PROJECT_METRICS, metric_value w app/dashboard.py) → tytuł, opis, format wartości
    wywozy: ['odbiory na dzień', 'średnio w miesiącu', v => num(v, 1)],
    puste_wywozy: ['puste odbiory', '% odbiorów przy zapełnieniu poniżej 50%', v => `${num(v, 1)}%`],
    udzial_zmieszanych: ['udział zmieszanych', '% masy odpadów', v => `${num(v, 1)}%`],
    km_na_wywoz: ['kilometry na jeden odbiór', '', v => `${num(v, 1)} km`],
    koszt_wywozu: ['koszt jednego odbioru', '', v => zl(v)],
    czas_reakcji: ['czas reakcji na zgłoszenie', 'średnio, godziny', v => `${num(v, 1)} h`],
  };
  const fact = (key, ico, label, value, sub = '') => `<article class="card kpi" data-help="projekt.${key}"><header class="kpi-h">${icon(ico)}${label}</header>
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
    document.getElementById('p-facts').innerHTML = fact('efekt', 'sparkles', 'Kluczowy efekt', esc(TF.effect(p)), p.efekt_wartosc == null ? 'efekt policzymy po wdrożeniu' : 'liczony z danych odbiorów')
      + fact('postep', 'flag', 'Postęp', `${num(p.postep_pct)}<small>%</small>`, `<span class="bar" style="display:block;margin-top:6px"><i style="--p:${(p.postep_pct / 100).toFixed(3)}"></i></span>`)
      + fact('budzet', 'banknote', 'Budżet', zl(p.budzet), `wykorzystano ${zl(p.wykorzystano)} (${used}%)`)
      + fact('start', 'calendar', 'Start', p.start ? new Date(p.start).toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' }) : '–', p.koniec ? `koniec: ${new Date(p.koniec).toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' })}` : '');
    // kluczowy efekt: miesięczna seria miary projektu (p.trend, ta sama co linia na karcie w dashboardzie) jako pierwszy, szeroki wykres
    const pp = TF.fullMonths({ ...(p.przed_po || {}), kluczowy: p.trend }), months = pp.miesiace || [];
    const [kt, ks, kf] = METRIC[p.miara] || ['Miara projektu', '', v => num(v, 1)], avg = pp.podsumowanie || {};
    document.getElementById('pk-h').textContent = `Kluczowy efekt: ${kt}`;
    document.getElementById('pk-s').textContent = [TF.effect(p), ks, avg.przed?.[p.miara] != null && avg.po?.[p.miara] != null
      ? `średnio przed: ${kf(avg.przed[p.miara])}, po: ${kf(avg.po[p.miara])}` : 'przed i po starcie projektu'].filter(Boolean).join(' · ');
    const why = pp.koszt_wyjasnienie, note = document.getElementById('pc-koszt-note');
    if (why && Math.abs(why.odbiory_pct) >= 5) { note.textContent = why.zdanie; note.hidden = false; }  // przy małej zmianie odbiorów to szum
    const start = (pp.start || p.start || '').slice(0, 7);
    const fmt = { ...UNIT, kluczowy: kf };
    ['kluczowy', 'koszt', 'wywozy', 'zapelnienie', 'czas_reakcji'].forEach(k => {
      const el = document.getElementById(`pc-${k}`), vals = pp[k] || [];
      TF.chartEmpty(el, !vals.some(v => v != null && v !== 0), 'Ten projekt nie ma jeszcze danych przed i po.');
      if (!vals.length) return;
      const labels = months.map(TF.monthLabel), si = months.indexOf(start);
      TF.chart(el).setOption({
        animation: TF.anim, tooltip: { trigger: 'axis', valueFormatter: v => v == null ? '–' : fmt[k](v) },
        xAxis: { type: 'category', data: labels }, yAxis: { type: 'value', axisLabel: { formatter: v => k === 'koszt' ? `${num(v / 1000)} tys.` : num(v, 1) } },
        series: [{ type: 'bar', barMaxWidth: k === 'kluczowy' ? 36 : 22, data: vals.map((v, i) => ({ value: v, itemStyle: { color: si >= 0 && i >= si ? C.brand : C.lineStrong, borderRadius: [4, 4, 0, 0] } })),
                   markLine: si >= 0 ? { symbol: 'none', silent: true, lineStyle: { color: C.ink2, type: [4, 4] }, label: { formatter: 'start projektu', color: C.ink2, fontWeight: 600, position: 'end' }, data: [{ xAxis: labels[si] }] } : undefined }],
      });
    });
  })();
})();
