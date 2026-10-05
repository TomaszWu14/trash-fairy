"""Pełny film demo (6–8 min): slajdy z lektorem + spokojne przejście przez aplikację krok po kroku.

Użycie:  python demo/film_pelny.py [--base URL]          (domyślnie http://127.0.0.1:5050; zmienia dane demo, resetuje je)
         python demo/film_pelny.py --lektor             (lista brakujących nagrań lektora w demo/lektor_pelny/<klucz>.mp3)
Wyjście: demo/demo_trash-fairy_pelne.mp4, demo/rozdzialy.txt (znaczniki czasu do opisu filmu), demo/podglad/pelny-NN.png.

Różnice wobec krótkiego filmu (build_all.py): bez przyspieszania, widoczny kursor płynnie dojeżdża do przycisku, pasek
„Krok x z y” scenariusza zostaje na ekranie, napis trwa co najmniej 4 s, kroki przechodzą przyciskiem „Dalej” aplikacji,
części łączy przenikanie. Wycinamy tylko ładowanie stron i długie czekanie (dojazd, analiza zdjęcia).
Slajdy to podgląd PDF (demo/podglad/slajd-NN.png z `build_all.py --tylko pdf`).
"""
import argparse
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_all import (CARDS, OUT, PREVIEW, X264, W, H, Take, card, cut, demo_photo, duration, ffmpeg,  # noqa: E402
                       log, mix, ok, reset)

MP4 = OUT / "demo_trash-fairy_pelne.mp4"
LEKTOR = OUT / "lektor_pelny"
FADE = 0.6  # przenikanie między częściami filmu (s)
MIN_HOLD = 4.0  # napis na ekranie co najmniej tyle sekund
WPS = 2.0  # słowa na sekundę lektora (zmierzone na nagraniach z demo/lektor): długość ujęcia, gdy brak nagrania

# Teksty lektora: klucz → tekst. Liczby tylko te, które są na slajdach (podglad/slajd-NN.png), słownie dla syntezy mowy.
TEKSTY = {
    "s01": "Trash Fairy to mózg odbioru odpadów dla Krakowa. Pomysł jest prosty: kosze opróżniamy wtedy, gdy tego potrzebują, "
           "a nie wtedy, gdy wypada termin w kalendarzu. W kilka minut pokażemy problem, rozwiązanie i całą aplikację krok po kroku.",
    "s02": "Dziś Kraków opróżnia kosze według harmonogramu. W harmonogramie MPO jest ponad dziewięć tysięcy koszy. "
           "W naszej symulacji, opartej na tym harmonogramie, ponad połowa przyjazdów była pusta: kosz nie wymagał jeszcze opróżnienia. "
           "A w tym samym czasie altany śmietnikowe były przepełnione łącznie przez trzysta trzydzieści osiem godzin.",
    "s03": "Rozwiązanie ma trzy części. Sygnały: prognoza zapełnienia, panel przy koszu z kodem QR i przyciskiem, a tam, gdzie się opłaca, "
           "czujniki. Reguły: jawne reguły w kodzie wybierają kosze i układają trasę. Dowód: położenie śmieciarki i zdjęcie kosza "
           "potwierdzają, że odbiór naprawdę się odbył.",
    "s04": "Wszyscy pracują na tych samych danych. Panel kosza pokazuje zapełnienie. Mieszkaniec zgłasza problem bez instalowania aplikacji. "
           "Kierowca dostaje priorytety, nawigację i potwierdza odbiór. Dyspozytor widzi mapę, pilne kosze i ekipy. "
           "Miasto ma dashboard z oszczędnościami i rekomendacjami. Do tego zgłaszanie dzikich wysypisk.",
    "s05": "Przepływ jest zawsze ten sam. Zgłoszenie przychodzi z kodu QR albo z przycisku na panelu. Reguła ustala stan i priorytet kosza. "
           "Na trasę trafiają tylko kosze, które tego potrzebują. Odbiór potwierdza położenie i zdjęcie, a wynik widzi i mieszkaniec, "
           "i miasto. Zobaczmy to w działającej aplikacji.",
    "k1": "Scenariusz pierwszy: przepełniony kosz. Od zgłoszenia mieszkanki do odbioru i wyniku dla miasta.",
    "a01": "Aplikacja ma wbudowany scenariusz demo. Losuje kosz i prowadzi przez kolejne kroki. Wybieramy wariant z kodem QR i kosz przy Rynku.",
    "a02": "To panel przy koszu, czyli dziesięciocalowy ekran. Pokazuje prognozę zapełnienia, kod QR i przyciski zgłoszenia. "
           "Prognoza nie wie jeszcze, że kosz właśnie się przepełnił. Mieszkanka to widzi.",
    "a03": "W demo kliknięcie kodu zastępuje aparat telefonu. Kod zmienia się codziennie, więc nie da się zgłaszać z domu ze starego zdjęcia.",
    "a04": "Telefon otwiera zgłoszenie dokładnie tego kosza. Bez logowania i bez instalowania aplikacji. Mieszkanka wybiera „Przepełniony” i wysyła.",
    "a05": "Zgłoszenie od razu dostaje numer i status. Mieszkanka wie, że ktoś je przyjął.",
    "a06": "Panel przy koszu też potwierdza zgłoszenie. Kolejni przechodnie widzą, że problem jest już zgłoszony, i nie muszą zgłaszać go drugi raz.",
    "a07": "Dyspozytor MPO widzi zgłoszenie na mapie na żywo. Kształt i kolor znacznika mówią, jak pełny jest kosz. "
           "Lista pilnych koszy podpowiada kolejność, ale o zmianie kursu zawsze decyduje człowiek.",
    "a08": "Kierowca dostaje trasę. Kosze ze zgłoszeniem mieszkańca są na górze listy, każdy z powodem, dlaczego jest na trasie.",
    "a09": "Karta kosza: adres, zapełnienie i historia. Przycisk „Jadę” uruchamia nawigację w aplikacji, bez przełączania do innych map.",
    "a10": "Na miejscu kierowca zaznacza, jak pełny był kosz, i może dołączyć zdjęcie. Potem „Opróżniono”.",
    "a11": "Odbiór potwierdzają położenie śmieciarki i zdjęcie kosza. To dowód wykonania usługi, a nie samo kliknięcie.",
    "a12": "Mieszkanka widzi na swoim telefonie: zrealizowane. Za trafne zgłoszenie dostaje punkty.",
    "a13": "A miasto widzi efekt w liczbach: odbiory, zgłoszenia i oszczędności wobec planu, dziennie, w miesiącu i w roku.",
    "k2": "Scenariusz drugi: przycisk na panelu. Dla osób bez smartfona.",
    "b01": "Nie każdy ma smartfon. Dlatego na panelu jest duży przycisk „Przepełniony”.",
    "b02": "Jedno naciśnięcie i zgłoszenie jest przyjęte. Panel od razu to pokazuje, a kosz trafia do dyspozytora i na listę kierowcy, "
           "tak jak w pierwszym scenariuszu.",
    "k3": "Scenariusz trzeci: dzikie wysypisko i decyzje dla miasta.",
    "c01": "Śmieci nie zawsze lądują w koszu. Mieszkaniec zgłasza dzikie wysypisko: miejsce na mapie, rodzaj odpadów i liczbę worków. "
           "W demo formularz jest wypełniony przykładem z ogródków działkowych.",
    "c02": "Dołącza zdjęcie i wysyła. Sztuczna inteligencja tylko opisuje zdjęcie. Status nadaje reguła w kodzie.",
    "c03": "Zgłoszenie ma numer i status. Widać opis zdjęcia i to, co się z nim dalej stanie.",
    "c04": "Dyspozytor widzi wysypisko na mapie, obok gorących obszarów zgłoszeń z ostatnich trzech miesięcy.",
    "c05": "W zakładce „Pilne” jednym kliknięciem dodaje kosz do najbliższego kursu. Kosz trafia na początek listy kierowcy. "
           "To decyzja człowieka, reguła tylko podpowiada.",
    "c06": "Ekipa MPO na swoim telefonie sprząta i oznacza wysypisko jako uprzątnięte.",
    "c07": "Mieszkaniec dostaje punkty za trafne zgłoszenie. Miasto może połączyć je z nagrodami.",
    "c08": "Na koniec dashboard. Rekomendacje liczą reguły w kodzie: gdzie zwiększyć pojemność koszy, gdzie postawić tablicę, "
           "a gdzie rozważyć fotopułapkę. Decyzję zawsze podejmuje miasto.",
    "s08": "Jak to działa w środku? Sygnały z paneli, telefonów, czujników, pogody i ruchu trafiają do aplikacji we Flasku. "
           "Jawne reguły ustalają stan i priorytet, a OR-Tools układa trasę. Sztuczna inteligencja, czyli Claude, tylko opisuje zdjęcia "
           "i nigdy nie decyduje. Dane są otwarte w standardzie Open311.",
    "s09": "Efekt w symulacji czterech tygodni: puste przyjazdy spadają z pięćdziesięciu siedmiu do dwudziestu siedmiu procent, "
           "przepełnienia altan z trzystu trzydziestu ośmiu godzin do zera, a odbiorów koszy jest o prawie jedną czwartą mniej. "
           "Dla całego Krakowa to szacunkowo od czterech do prawie ośmiu milionów złotych rocznie, przy dwunastu złotych za odbiór.",
    "s10": "Co dalej? Pilotaż na pięćdziesięciu koszach w Dzielnicy pierwszej, integracja z systemami MPO i czujniki tam, gdzie się opłacają. "
           "Kraków nie potrzebuje więcej koszy. Potrzebuje wróżki.",
}

# plansze rozdziałów: (klucz lektora, tytuł, nadtytuł)
CHAPTERS = {"k1": ("Przepełniony kosz: od zgłoszenia do odbioru", "Scenariusz 1"),
            "k2": ("Przycisk na panelu kosza", "Scenariusz 2"),
            "k3": ("Dzikie wysypisko i decyzje dla miasta", "Scenariusz 3")}

# kursor: strzałka w nakładce top layer (nad okienkami), pozycja przeżywa przejście między stronami (sessionStorage);
# pasek scenariusza „Krok x z y” zostaje, napis siedzi nad nim (krótki film go chowa — tu nadpisujemy wysokość inline !important)
FULL_JS = """
(() => {
  const css = `#tf-cursor{position:fixed;inset:auto;margin:0;padding:0;border:0;background:transparent;overflow:visible;width:28px;height:28px;
      pointer-events:none;filter:drop-shadow(0 2px 4px rgba(0,0,0,.6))}
    #scenario-slot{display:block!important}
    #tf-cap{bottom:calc(var(--scenario-h, 0px) + 20px)!important;font-size:22px!important;max-width:1100px!important}`;
  const top = el => { try { if (el.matches(':popover-open')) el.hidePopover(); el.showPopover(); } catch (e) {} };
  const put = () => {
    if (document.getElementById('tf-cursor')) return;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const c = document.createElement('div'); c.id = 'tf-cursor'; c.popover = 'manual';
    c.innerHTML = '<svg viewBox="0 0 24 24" width="28" height="28"><path d="M4 2l16 10-7 1.5L9.5 21z" fill="#fff" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    document.body.appendChild(c);
    const pos = (sessionStorage.getItem('tf-cur') || '').split(',');
    if (pos.length === 2) { c.style.left = pos[0] + 'px'; c.style.top = pos[1] + 'px'; top(c); }
    setInterval(() => {  // pasek scenariusza: prawdziwa wysokość zamiast 0 z nakładki krótkiego filmu
      const bar = document.querySelector('#scenario-slot > .scenario');
      if (bar) document.body.style.setProperty('--scenario-h', bar.offsetHeight + 'px', 'important');
    }, 250);
  };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', put) : put();
  addEventListener('mousemove', e => {
    const c = document.getElementById('tf-cursor'); if (!c) return;
    c.style.left = (e.clientX - 3) + 'px'; c.style.top = (e.clientY - 2) + 'px'; top(c);
    try { sessionStorage.setItem('tf-cur', `${e.clientX - 3},${e.clientY - 2}`); } catch (er) {}
  }, true);
})();
"""


class KeyVoice:
    """Nagrania demo/lektor_pelny/<klucz>.mp3; brak pliku = ujęcie trwa tyle, ile przeczytanie tekstu (ostrzeżenie w logu)."""

    def clip(self, key):
        path = LEKTOR / f"{key}.mp3"
        if path.is_file():
            return path, duration(path)
        log(f"  UWAGA: brak nagrania {path.name} — ujęcie bez głosu")
        return None, len(TEKSTY[key].split()) / WPS


class FullTake(Take):
    def __init__(self, browser, base, tmp, voice):
        super().__init__(browser, base, tmp, None)
        self.voice, self.mx, self.my = voice, 640, 360
        self.ctx.add_init_script(FULL_JS)  # po nakładce krótkiego filmu: jej style są wcześniej w <head>, więc te wygrywają

    def mow(self, key, caption, after=0.8):
        """Napis + lektor, potem chwila ciszy; dopiero wtedy kolejna akcja (najpierw mówimy, potem klikamy)."""
        mp3, secs = self.voice.clip(key)
        self.page.evaluate("t => { sessionStorage.setItem('tf-cap', t); window.tfCap && window.tfCap(t); }", caption)
        if mp3:
            self.caps.append((time.monotonic() - self.t0 + 0.2, mp3))
        self.page.wait_for_timeout(int(max(MIN_HOLD, secs + 0.2 + after) * 1000))

    def tap(self, sel, pause=0.6):
        """Kursor płynnie dojeżdża do elementu (ok. 0,7 s), kliknięcie z kółkiem, chwila na reakcję strony."""
        p = self.page
        loc = p.locator(sel).first
        loc.scroll_into_view_if_needed()
        p.wait_for_timeout(300)
        b = loc.bounding_box()
        x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        n = 30
        for i in range(1, n + 1):
            k = i / n
            k = k * k * (3 - 2 * k)  # wygładzenie: start i koniec wolniej
            p.mouse.move(self.mx + (x - self.mx) * k, self.my + (y - self.my) * k)
            p.wait_for_timeout(18)
        self.mx, self.my = x, y
        p.wait_for_timeout(250)
        loc.click()
        p.wait_for_timeout(int(pause * 1000))

    def dalej(self, url, ready=None):
        """Krok scenariusza przyciskiem „Dalej” z paska aplikacji; ładowanie nowej strony wycinamy."""
        p = self.page
        p.evaluate("() => { try { sessionStorage.removeItem('tf-cap'); } catch (e) {} window.tfCap && window.tfCap(''); }")
        self.tap('[data-sc="next"]', 0.3)
        self.waiting(lambda: (p.wait_for_url(url), p.wait_for_load_state("networkidle"),
                              ready and p.wait_for_selector(ready), self.loaded(), p.wait_for_timeout(600)))

    def loaded(self):
        """Szare szkielety ładowania (.skel) znikają, zanim kadr trafi do filmu."""
        self.page.wait_for_function("!document.querySelector('main .skel')", timeout=30000)

    def scroll(self, sel, secs=1.2):
        self.page.locator(sel).first.evaluate("e => e.scrollIntoView({behavior: 'smooth', block: 'center'})")
        self.page.wait_for_timeout(int(secs * 1000))


def scenario_a(t, photo):
    p = t.page
    t.go("/?scenariusz=A&kosz=18")
    p.wait_for_selector("#sc-pick[open]")
    t.mow("a01", "Scenariusz demo: wariant z kodem QR, kosz przy Rynku")
    t.tap("#sc-pick [data-go]", 0.2)
    t.waiting(lambda: (p.wait_for_url("**/panel/18"), p.wait_for_load_state("networkidle"), p.wait_for_timeout(600)))
    t.mow("a02", "Panel przy koszu: prognoza, kod QR, przyciski zgłoszenia")
    t.mow("a03", "Kod QR zmienia się codziennie")
    t.tap("a.kiosk-qr-code", 0.2)
    t.waiting(lambda: (p.wait_for_load_state("networkidle"), p.wait_for_selector("#chk-qr.ok"), p.wait_for_timeout(500)))
    t.mow("a04", "Zgłoszenie tego kosza: bez logowania, bez aplikacji", after=0.3)
    t.tap(".m-type:has(input[value=przepelniony])", 0.8)
    t.tap("#m-send", 0.2)
    t.waiting(lambda: p.wait_for_selector("#m-success:not([hidden])"))
    nr = p.text_content("#m-nr").strip()
    ok(nr.startswith("TF-"), f"zgłoszenie {nr}")
    t.mow("a05", f"Zgłoszenie {nr}: numer i status od razu")
    t.dalej("**/panel/18")
    t.mow("a06", "Panel kosza potwierdza zgłoszenie")
    t.dalej("**/dyspozytor*", ".leaflet-container")
    t.mow("a07", "Dyspozytor: mapa na żywo, pilne kosze, decyzja człowieka", after=1.5)
    t.dalej("**/kierowca", "#k-stops a[href$='/kierowca/kosz/18']")
    ok(p.locator("#k-stops a[href$='/kierowca/kosz/18']").count() > 0, "kosz 18 na liście kierowcy")
    t.mow("a08", "Kierowca: zgłoszone kosze na górze listy, z powodem")
    t.tap("#k-stops a[href$='/kierowca/kosz/18']", 0.2)
    t.waiting(lambda: (p.wait_for_load_state("networkidle"), p.wait_for_timeout(600)))
    t.mow("a09", "„Jadę”: nawigacja w aplikacji", after=0.3)
    t.tap("[data-akcja=jade]", 5.0)  # pierwsze sekundy jazdy zostają w filmie
    t.waiting(lambda: p.wait_for_selector("#k-navbar.arrived", timeout=60000))
    t.mow("a10", "Na miejscu: poziom w koszu, zdjęcie, „Opróżniono”", after=0.3)
    t.tap("label.k-lv:has(input[value='100'])", 0.8)
    with p.expect_file_chooser() as fc:
        t.tap(".k-photo-pick", 0.2)
    fc.value.set_files(str(photo))
    p.wait_for_timeout(1500)
    t.tap("[data-akcja=oprozniono]", 0.2)
    t.waiting(lambda: p.wait_for_selector("#k-doneok:not([hidden])", timeout=30000))
    ok(True, "kierowca: Opróżniono")
    t.mow("a11", "Dowód odbioru: położenie śmieciarki i zdjęcie kosza")
    t.dalej(f"**/zgloszenie/{nr}")
    t.waiting(lambda: p.wait_for_function("document.getElementById('st-title')?.textContent.includes('Zrealizowane')", timeout=20000))
    ok(True, "status u mieszkańca: zrealizowane")
    t.mow("a12", "Mieszkanka widzi: zrealizowane, punkty za trafne zgłoszenie")
    t.dalej("**/dashboard", "#d-kpis")
    t.mow("a13", "Miasto: odbiory, zgłoszenia, oszczędności wobec planu", after=1.5)


def scenario_b(t):
    p = t.page
    t.go("/?scenariusz=B&kosz=7")
    p.wait_for_selector("#sc-pick[open]")
    p.wait_for_timeout(800)
    t.tap("#sc-pick [data-go]", 0.2)
    t.waiting(lambda: (p.wait_for_url("**/panel/7"), p.wait_for_load_state("networkidle"), p.wait_for_timeout(600)))
    t.mow("b01", "Bez smartfona: przycisk „Przepełniony” na panelu", after=0.3)
    t.tap('[data-typ="przepelniony"]', 0.2)
    t.waiting(lambda: p.wait_for_selector("#k-ack.ok", timeout=8000))
    ok(True, "panel: zgłoszenie z przycisku")
    t.mow("b02", "Jedno naciśnięcie: zgłoszenie przyjęte, kosz idzie na trasę", after=1.2)


def scenario_c(t):
    p = t.page
    t.go("/?scenariusz=C&miejsce=0")
    p.wait_for_selector("#sc-pick[open]")
    p.wait_for_timeout(800)
    t.tap("#sc-pick [data-go]", 0.2)
    t.waiting(lambda: (p.wait_for_url("**/wysypisko"), p.wait_for_load_state("networkidle"), p.wait_for_timeout(600)))
    t.mow("c01", "Dzikie wysypisko: miejsce, rodzaj odpadów, liczba worków", after=0.3)
    t.scroll(".wd-demo-photo")
    t.tap(".wd-demo-photo", 0.8)
    p.wait_for_function("document.getElementById('wd-zdjecie').files.length === 1")
    t.mow("c02", "Zdjęcie: AI opisuje, reguła decyduje", after=0.3)
    t.tap("#wd-send", 0.2)
    t.waiting(lambda: p.wait_for_selector("#wd-ok:not([hidden])", timeout=60000))
    wd = p.text_content("#wd-nr").strip()
    ok(wd.startswith("WD-"), f"zgłoszenie {wd}")
    t.dalej(f"**/wysypisko/{wd}")
    t.mow("c03", f"Zgłoszenie {wd}: numer, status, opis zdjęcia")
    t.dalej("**/dyspozytor*", ".leaflet-container")
    t.mow("c04", "Dyspozytor: wysypisko i gorące obszary zgłoszeń", after=0.5)
    t.tap("#dp-t-pilne", 1.0)
    t.mow("c05", "„Dodaj do kursu”: decyzja człowieka", after=0.2)
    t.tap(".dp-item .btn-add", 0.2)
    p.locator(".dp-added").first.wait_for(state="visible", timeout=8000)
    p.wait_for_timeout(2500)
    t.dalej(f"**/wysypisko/{wd}?ekipa=1", "#wd-clear:not([hidden])")
    t.mow("c06", "Ekipa MPO: „Oznacz jako uprzątnięte”", after=0.3)
    t.tap("#wd-clear", 2.0)
    t.dalej("**/zglos", "#m-pts-sum b")
    pts = int("".join(ch for ch in p.text_content("#m-pts-sum b") if ch.isdigit()) or 0)
    ok(pts > 0, f"punkty mieszkańca: {pts}")
    t.scroll("#m-pts-h")
    t.mow("c07", f"Mieszkaniec: {pts} pkt za trafne zgłoszenia")
    t.go("/dashboard")
    t.waiting(t.loaded)
    t.scroll(".recs", 1.5)
    t.mow("c08", "Rekomendacje z reguł: od tablicy po fotopułapkę — decyduje miasto", after=1.5)


def lektor_list():
    LEKTOR.mkdir(parents=True, exist_ok=True)
    missing = [k for k in TEKSTY if not (LEKTOR / f"{k}.mp3").is_file()]
    log(f"Lektor pełnego filmu: {len(TEKSTY)} tekstów, brak nagrań: {len(missing)}")
    for k in missing:
        log(f"  {k}.mp3: {TEKSTY[k]}")


def zoom_still(png, secs, out):
    """Slajd albo plansza: powolne przybliżenie 1,00 → 1,04 (obraz nie stoi martwy przez 20 s)."""
    fr = int(secs * 30)
    ffmpeg("-loop", 1, "-framerate", 30, "-t", f"{secs:.2f}", "-i", png, "-vf",
           f"scale=3840:-1,zoompan=z='1+0.04*on/{fr}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps=30", *X264, out)


def build(base):
    from playwright.sync_api import Error as PwError, sync_playwright
    slides = {k: PREVIEW / f"slajd-{k[1:]}.png" for k in ("s01", "s02", "s03", "s04", "s05", "s08", "s09", "s10")}
    if not all(s.is_file() for s in slides.values()):
        raise SystemExit("Brak podglądu slajdów — najpierw: python demo/build_all.py --tylko pdf")
    voice = KeyVoice()
    with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
        tmp = Path(td)
        chrome = pw.chromium.launch()
        for k, (title, sub) in CHAPTERS.items():
            card(chrome, tmp / f"{k}.png", title, sub)
        card(chrome, tmp / "end.png", *CARDS[3][1:3], big=True)
        photo = demo_photo(tmp / "kosz.jpg")
        req = chrome.new_context().request
        log("Reset danych demo…")
        reset(req, base)
        takes = {}
        try:
            for name, run in (("A", lambda t: scenario_a(t, photo)), ("B", scenario_b), ("C", scenario_c)):
                log(f"Nagranie scenariusza {name}")
                t = FullTake(chrome, base, tmp / name, voice)
                try:
                    run(t)
                except PwError as e:
                    t.finish()
                    raise SystemExit(f"{name}: {str(e).splitlines()[0]}")
                takes[name] = t.finish()
        finally:
            reset(req, base, strict=False)
            chrome.close()

        segs, clips, chapters = [], [], []  # clips: (indeks części, sekunda w części, mp3)

        def still(png, key, extra=1.4, title=None):
            mp3, secs = voice.clip(key) if key else (None, 0)
            segs.append(tmp / f"seg{len(segs):02d}.mp4")
            zoom_still(png, max(4.0, secs + extra), segs[-1])
            if mp3:
                clips.append((len(segs) - 1, 0.5, mp3))
            if title:
                chapters.append((len(segs) - 1, title))

        def scene(name):
            segs.append(tmp / f"seg{len(segs):02d}.mp4")
            clips.extend((len(segs) - 1, s, mp3) for s, mp3 in cut(*takes[name], segs[-1], 10 ** 6))

        still(slides["s01"], "s01", title="Trash Fairy")
        still(slides["s02"], "s02", title="Problem")
        still(slides["s03"], "s03", title="Rozwiązanie")
        still(slides["s04"], "s04")
        still(slides["s05"], "s05")
        for k, sc in (("k1", "A"), ("k2", "B"), ("k3", "C")):
            still(tmp / f"{k}.png", k, 1.0, title=" — ".join(reversed(CHAPTERS[k])))
            scene(sc)
        still(slides["s08"], "s08", title="Architektura")
        still(slides["s09"], "s09", title="Korzyści")
        still(slides["s10"], "s10", title="Co dalej")
        still(tmp / "end.png", None)

        durs = [duration(s) for s in segs]
        starts = [sum(durs[:i]) - i * FADE for i in range(len(segs))]
        ins = sum((["-i", s] for s in segs), [])
        fl, prev = [], "[0:v]"
        for i in range(1, len(segs)):
            fl.append(f"{prev}[{i}:v]xfade=transition=fade:duration={FADE}:offset={starts[i]:.3f}[v{i}]")
            prev = f"[v{i}]"
        film = tmp / "film.mp4"
        ffmpeg(*ins, "-filter_complex", ";".join(fl), "-map", prev, *X264, "-movflags", "+faststart", film)
        total = duration(film)
        mix(film, [(starts[i] + s, mp3) for i, s, mp3 in clips], MP4, total)
    total = duration(MP4)
    (OUT / "rozdzialy.txt").write_text("".join(f"{int(starts[i] // 60)}:{int(starts[i] % 60):02d} {t}\n" for i, t in chapters),
                                       encoding="utf-8")
    PREVIEW.mkdir(parents=True, exist_ok=True)
    n = int(total // 20)
    for k in range(n + 1):
        ffmpeg("-ss", f"{min(k * 20 + 2, total - 1):.2f}", "-i", MP4, "-frames:v", 1, "-vf", "scale=960:-1", PREVIEW / f"pelny-{k:02d}.png")
    log(f"Film: {MP4} ({total / 60:.1f} min, {len(clips)} klipów lektora), rozdziały: {OUT / 'rozdzialy.txt'}, klatki: podglad/pelny-*.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:5050")
    ap.add_argument("--lektor", action="store_true", help="tylko lista brakujących nagrań lektora")
    a = ap.parse_args()
    if a.lektor:
        return lektor_list()
    build(a.base.rstrip("/"))


if __name__ == "__main__":
    sys.exit(main())
