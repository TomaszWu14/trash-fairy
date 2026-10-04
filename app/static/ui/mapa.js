// Wspólne pinezki map wariantu A (kierowca, dashboard). Dołączać po leaflet.js i app.js, z mapa.css.
// API (stałe, używa go kilka ekranów):
//   TF.mapPin(stan, { numer, zgloszenie, altana, etykieta, maly }) → L.divIcon
//     stan: 'ok' | 'warn' | 'full' | 'report' | 'sensor' albo poziom 0–100 (TF.lvl); kształt + znak jak TF.stateIcon.
//     numer: kolejność na trasie w pierścieniu w kolorze stanu (kształt stanu w rogu); zgloszenie: dymek …;
//     altana: podwójna obwódka; etykieta: aria-label („Kosz Rynek 18, 92%, pełny”, patrz TF.pinLabel); maly: 16 px zamiast 32, bez cienia, przygaszony (tło za numerami).
//   TF.clusterIcon(n, najgorszyStan, etykieta?) → L.divIcon: liczba w pierścieniu w kolorze najgorszego stanu + jego kształt.
//   TF.worstState(['ok', 'full', …]) → najgorszy stan; TF.pinLabel(nazwa, poziom) → „Kosz Rynek 18, 92%, pełny”.
// Tooltip wiąże wywołujący: marker.bindTooltip(etykieta). Kolory tylko z tokenów (klasy .si-* z app.css, mapa.css).
(() => {
  const TF = window.TF;
  const RANK = { ok: 0, warn: 1, sensor: 2, report: 3, full: 4 };
  const NAME = { ok: 'w porządku', warn: 'zapełnia się', full: 'pełny', report: 'zgłoszenie mieszkańca', sensor: 'ostrzeżenie czujnika' };
  // obwódka altany: ten sam kształt co stan, większy (viewBox 32, symbol stanu 64% w środku)
  const OUT = { ok: '<circle cx="16" cy="16" r="14.6"/>', warn: '<path d="M16 1.2 30.8 16 16 30.8 1.2 16z"/>',
                full: '<rect x="1.6" y="1.6" width="28.8" height="28.8" rx="6"/>', report: '<circle cx="16" cy="16" r="14.6"/>',
                sensor: '<path d="M16 1.4 31 29.6H1z"/>' };
  const stanOf = s => typeof s === 'number' ? TF.lvl(s) : s in RANK ? s : 'ok';
  let Icon;  // L.divIcon z aria-label na elemencie markera (Leaflet nadaje mu role="button" i tabindex)
  const make = o => new (Icon ||= L.DivIcon.extend({
    createIcon(old) {
      const el = L.DivIcon.prototype.createIcon.call(this, old);
      if (this.options.label) el.setAttribute('aria-label', this.options.label);
      return el;
    },
  }))(o);

  TF.worstState = list => list.map(stanOf).reduce((a, b) => RANK[b] > RANK[a] ? b : a, 'ok');
  TF.pinLabel = (nazwa, poziom) => `${nazwa}, ${Math.round(poziom)}%, ${NAME[TF.lvl(poziom)]}`;

  TF.mapPin = (stan, o = {}) => {
    const k = stanOf(stan), num = o.numer != null && o.numer !== '';
    const size = num ? (o.altana ? 40 : 36) : o.maly ? 16 : o.altana ? 36 : 32;
    const body = num ? `<span class="pin-ring"><b>${TF.esc(o.numer)}</b></span>${TF.stateIcon(k, 'pin-st')}`
      : (o.altana ? `<svg class="pin-out" viewBox="0 0 32 32" aria-hidden="true">${OUT[k]}</svg>` : '') + TF.stateIcon(k, 'pin-shape');
    return make({
      className: `tf-pin si-${k}${num ? ' is-num' : ''}${o.maly && !num ? ' is-sm' : ''}${o.altana ? ' is-alt' : ''}`,
      html: body + (o.zgloszenie ? TF.stateIcon('report', 'pin-rep') : ''),
      iconSize: [size, size], iconAnchor: [size / 2, size / 2], tooltipAnchor: [size / 2, 0], label: o.etykieta,
    });
  };

  TF.clusterIcon = (n, najgorszy = 'ok', etykieta) => {
    const k = stanOf(najgorszy), size = n >= 100 ? 48 : 42;
    return make({
      className: `tf-pin tf-cluster si-${k}`, html: `<span class="pin-ring"><b>${TF.num(n)}</b></span>${TF.stateIcon(k, 'pin-st')}`,
      iconSize: [size, size], iconAnchor: [size / 2, size / 2], tooltipAnchor: [size / 2, 0],
      label: etykieta || `Grupa: ${TF.num(n)} ${TF.plural(n, ['kosz', 'kosze', 'koszy'])}, najgorszy stan: ${NAME[k]}`,
    });
  };
})();
