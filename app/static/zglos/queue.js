// Kolejka zgłoszeń offline w IndexedDB. Ten sam plik ładuje strona (<script>) i service worker (importScripts),
// żeby Background Sync wysłał zgłoszenie także po zamknięciu aplikacji.
// osobna baza na aplikację (self.TF_DB_NAME ustawione przed załadowaniem), żeby SW zgłoszeń nie wysyłał kolejki kierowcy
const TF_DB = self.TF_DB_NAME || 'trash-fairy', TF_STORE = 'queue';
function tfDb() {
  return new Promise((ok, err) => {
    const r = indexedDB.open(TF_DB, 1);
    r.onupgradeneeded = () => r.result.createObjectStore(TF_STORE, { keyPath: 'id', autoIncrement: true });
    r.onsuccess = () => ok(r.result);
    r.onerror = () => err(r.error);
  });
}
function tfTx(mode, fn) {
  return tfDb().then(db => new Promise((ok, err) => {
    const tx = db.transaction(TF_STORE, mode), req = fn(tx.objectStore(TF_STORE));
    tx.oncomplete = () => ok(req && req.result);
    tx.onerror = () => err(tx.error);
  }));
}
const tfQueue = {
  add: item => tfTx('readwrite', s => s.add(item)),
  all: () => tfTx('readonly', s => s.getAll()),
  remove: id => tfTx('readwrite', s => s.delete(id)),
  clear: () => tfTx('readwrite', s => s.clear()),
};
