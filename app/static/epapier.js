// Symulator ekranu e-papierowego: polling co 1 s; zmiana state_key = pełne odświeżenie z mignięciem (1,5 s),
// zmiana values_key = podmiana wyłącznie okna częściowego 24,344–776,432 (bez mignięcia).
const POLL_MS = 2000, FLASH_MS = 1500;  // prawdziwy e-papier i tak odświeża się kilka sekund
const $ = id => document.getElementById(id);
let stateKey = null, valuesKey = null, busy = false;
const STATE_LABEL = { calm: '1 · spokój', confirm: '2 · zgłoszono', enroute: '3 · ekipa w drodze', emptied: '4 · opróżniono',
                      overflow: '5 · przepełniony', fault: '6 · usterka', night: '7 · tryb nocny' };

function log(kind, text) {
  const t = new Date().toTimeString().slice(0, 8);
  $('log').insertAdjacentHTML('beforeend', `<span class="${kind}">${t} · ${kind === 'full' ? 'PEŁNE odświeżenie' : kind === 'partial' ? 'okno częściowe' : 'przycisk'} · ${text}</span>`);
  while ($('log').children.length > 9) $('log').children[1].remove();
}

async function poll() {
  if (!busy) {
    try {
      const d = await (await fetch(`/api/epapier/${EP.pointId}`)).json();
      $('status').textContent = `stan: ${STATE_LABEL[d.state] || d.state}`;
      if (d.state_key !== stateKey) {
        const first = stateKey === null;
        stateKey = d.state_key; valuesKey = d.values_key;
        first ? swapFull() : await fullRefresh(d.state);
      } else if (d.values_key !== valuesKey) {
        valuesKey = d.values_key;
        $('part').src = `/epapier/${EP.pointId}.png?part=1&v=${Date.now()}`;
        log('partial', 'zmiana wartości (zapełnienie / czas / liczba osób)');
      }
    } catch (e) { /* chwilowy brak sieci */ }
  }
  setTimeout(poll, POLL_MS);
}

function swapFull() {
  const v = Date.now();
  $('full').src = `/epapier/${EP.pointId}.png?v=${v}`;
  $('part').src = `/epapier/${EP.pointId}.png?part=1&v=${v}`;
}

async function fullRefresh(state) {
  busy = true;
  $('flash').classList.remove('on'); void $('flash').offsetWidth; $('flash').classList.add('on');
  log('full', `nowy stan: ${STATE_LABEL[state] || state}`);
  await new Promise(r => setTimeout(r, FLASH_MS * 0.7));  // obraz zmienia się „pod” ostatnim mignięciem
  swapFull();
  await new Promise(r => setTimeout(r, FLASH_MS * 0.3));
  $('flash').classList.remove('on');
  busy = false;
}

$('press').addEventListener('click', async e => {
  const btn = e.currentTarget;
  btn.disabled = true; btn.classList.add('down');
  log('button', 'naciśnięcie fizycznego przycisku → POST /api/press');
  try {
    const r = await fetch('/api/press', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ point_id: EP.pointId, source: 'button' }) });
    const d = await r.json();
    if (!r.ok) log('button', d.message);
  } catch (err) { log('button', 'brak połączenia'); }
  setTimeout(() => { btn.disabled = false; btn.classList.remove('down'); }, 600);
});

poll();
