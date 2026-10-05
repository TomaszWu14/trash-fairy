"""Film demo ok. 3 min: najwięcej treści w najkrótszym czasie. Problem → rozwiązanie → 3 scenariusze → korzyści.

Użycie:  python demo/film_3min.py [--base URL]      (domyślnie http://127.0.0.1:5050; zmienia dane demo, resetuje je)
Wyjście: demo/demo_trash-fairy_3min.mp4 (+ podglad/3min-NN.png).

Różnice wobec pełnego filmu (film_pelny.py): lektor ×1,15 (atempo, bez zmiany wysokości głosu), kliknięcia idą w trakcie
mówienia (kolejna kwestia czeka tylko na koniec poprzedniej), bez plansz rozdziałów i slajdów 4–8, 10; scenariusz 2 (przycisk na panelu) to jedna scena AI. Nagrania lektora
z obu zestawów: „p:<klucz>” = demo/lektor_pelny/<klucz>.mp3, „k:NN” = demo/lektor/NN.mp3 (krótki film). Sceny AI z
demo/animacja/ (obraz + najazd kamery na wskazany punkt).
"""
import argparse
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_all import CARDS, OUT, PREVIEW, X264, W, H, card, cut, demo_photo, duration, ffmpeg, log, mix, ok, reset  # noqa: E402
from film_pelny import FullTake  # noqa: E402

MP4 = OUT / "demo_trash-fairy_3min.mp4"
TEMPO = 1.15  # „przyspiesz troszeczkę lektora”
FADE = 0.5
ANIM = OUT / "animacja"
SRC = {"p": OUT / "lektor_pelny", "k": OUT / "lektor"}


class FastVoice:
    """Klucz → (mp3 przyspieszone ×TEMPO, sekundy); pliki tymczasowe, bo źródła zostają nietknięte."""

    def __init__(self, tmp):
        self.tmp, self.cache = tmp, {}

    def clip(self, key):
        if key not in self.cache:
            kind, name = key.split(":")
            src = SRC[kind] / f"{name}.mp3"
            if not src.is_file():
                raise SystemExit(f"Brak nagrania lektora {src}")
            out = self.tmp / f"v-{kind}-{name}.mp3"
            ffmpeg("-i", src, "-filter:a", f"atempo={TEMPO}", out)
            self.cache[key] = (out, duration(out))
        return self.cache[key]


class FastTake(FullTake):
    """Lektor mówi, a w tym czasie kursor już klika. Przed przejściem na inną stronę i przed wycięciem czekania
    kwestia musi wybrzmieć (inaczej głos rozjechałby się z obrazem po cięciu)."""

    def __init__(self, browser, base, tmp, voice):
        super().__init__(browser, base, tmp, voice)
        self.busy = 0.0

    def hold(self, extra=0.25):
        left = self.busy - time.monotonic()
        if left > 0:
            self.page.wait_for_timeout(int((left + extra) * 1000))

    def say(self, key, caption, lead=0.6):
        self.hold(0.15)
        mp3, secs = self.voice.clip(key)
        self.page.evaluate("t => { sessionStorage.setItem('tf-cap', t); window.tfCap && window.tfCap(t); }", caption)
        self.caps.append((time.monotonic() - self.t0 + 0.1, mp3))
        self.busy = time.monotonic() + secs + 0.1
        self.page.wait_for_timeout(int(lead * 1000))  # pierwsze słowa, zanim kursor ruszy

    def waiting(self, fn):
        self.hold()
        super().waiting(fn)

    def go(self, path):
        self.hold()
        super().go(path)

    def dalej(self, url, ready=None):
        self.hold()
        super().dalej(url, ready)


def scenario_a(t, photo):
    p = t.page
    t.go("/?scenariusz=A&kosz=18")
    p.wait_for_selector("#sc-pick[open]")
    t.tap("#sc-pick [data-go]", 0.1)
    t.waiting(lambda: (p.wait_for_url("**/panel/18"), p.wait_for_load_state("networkidle"), p.wait_for_timeout(400)))
    t.say("k:08", "Panel przy koszu: kod QR zmienia się codziennie", lead=1.2)
    t.tap("a.kiosk-qr-code", 0.1)
    t.waiting(lambda: (p.wait_for_load_state("networkidle"), p.wait_for_selector("#chk-qr.ok"), p.wait_for_timeout(300)))
    t.say("p:a04", "Zgłoszenie tego kosza: bez logowania, bez aplikacji", lead=2.5)
    t.tap(".m-type:has(input[value=przepelniony])", 0.4)
    t.tap("#m-send", 0.1)
    t.waiting(lambda: p.wait_for_selector("#m-success:not([hidden])"))
    nr = p.text_content("#m-nr").strip()
    ok(nr.startswith("TF-"), f"zgłoszenie {nr}")
    t.say("k:11", f"{nr}: numer i status od razu")
    t.dalej("**/panel/18")
    t.dalej("**/dyspozytor*", ".leaflet-container")
    t.say("k:13", "Dyspozytor: pilne kosze, trasy i ekipy na żywo", lead=1.0)
    t.dalej("**/kierowca", "#k-stops a[href$='/kierowca/kosz/18']")
    t.say("k:14", "Kierowca: zgłoszony kosz na górze listy, z powodem", lead=1.2)
    t.tap("#k-stops a[href$='/kierowca/kosz/18']", 0.1)
    t.waiting(lambda: (p.wait_for_load_state("networkidle"), t.loaded(), p.wait_for_timeout(400)))
    t.say("k:15", "„Jadę”: nawigacja w aplikacji", lead=1.0)
    t.tap("[data-akcja=jade]", 2.5)
    t.waiting(lambda: p.wait_for_selector("#k-navbar.arrived", timeout=60000))
    t.tap("label.k-lv:has(input[value='100'])", 0.2)
    with p.expect_file_chooser() as fc:
        t.tap(".k-photo-pick", 0.1)
    fc.value.set_files(str(photo))
    p.wait_for_timeout(900)
    t.tap("[data-akcja=oprozniono]", 0.1)
    t.waiting(lambda: p.wait_for_selector("#k-doneok:not([hidden])", timeout=30000))
    ok(True, "kierowca: Opróżniono")
    t.say("k:17", "Dowód odbioru: położenie śmieciarki i zdjęcie kosza")
    t.dalej(f"**/zgloszenie/{nr}")
    t.waiting(lambda: p.wait_for_function("document.getElementById('st-title')?.textContent.includes('Zrealizowane')", timeout=20000))
    t.say("k:18", "Mieszkanka widzi: zrealizowane, punkty za trafne zgłoszenie")
    t.dalej("**/dashboard", "#d-kpis")
    t.say("k:19", "Miasto: oszczędności wobec planu, odbiory, zgłoszenia")
    t.hold(0.6)


def scenario_c(t):
    p = t.page
    t.go("/?scenariusz=C&miejsce=0")
    p.wait_for_selector("#sc-pick[open]")
    t.tap("#sc-pick [data-go]", 0.1)
    t.waiting(lambda: (p.wait_for_url("**/wysypisko"), p.wait_for_load_state("networkidle"), p.wait_for_timeout(400)))
    t.say("k:21", "Dzikie wysypisko: miejsce na mapie, rodzaj odpadów, liczba worków", lead=1.5)
    t.scroll(".wd-demo-photo", 0.8)
    t.tap(".wd-demo-photo", 0.3)
    p.wait_for_function("document.getElementById('wd-zdjecie').files.length === 1")
    t.say("p:c02", "Zdjęcie: AI opisuje, reguła nadaje status", lead=1.5)
    t.tap("#wd-send", 0.1)
    t.waiting(lambda: p.wait_for_selector("#wd-ok:not([hidden])", timeout=60000))
    wd = p.text_content("#wd-nr").strip()
    ok(wd.startswith("WD-"), f"zgłoszenie {wd}")
    t.dalej(f"**/wysypisko/{wd}")
    t.dalej("**/dyspozytor*", ".leaflet-container")
    t.say("k:26", "„Dodaj do kursu”: decyzja człowieka", lead=0.8)
    t.tap("#dp-t-pilne", 0.6)
    t.tap(".dp-item .btn-add", 0.1)
    p.locator(".dp-added").first.wait_for(state="visible", timeout=8000)
    t.hold(0.8)
    t.dalej(f"**/wysypisko/{wd}?ekipa=1", "#wd-clear:not([hidden])")
    t.say("k:27", "Ekipa sprząta i oznacza „Uprzątnięte”", lead=1.2)
    t.tap("#wd-clear", 0.6)
    t.dalej("**/zglos", "#m-pts-sum b")
    pts = int("".join(ch for ch in p.text_content("#m-pts-sum b") if ch.isdigit()) or 0)
    ok(pts > 0, f"punkty mieszkańca: {pts}")
    t.scroll("#m-pts-h", 0.6)
    t.say("k:28", f"Mieszkaniec: {pts} pkt za trafne zgłoszenia")
    t.go("/dashboard")
    t.waiting(t.loaded)
    t.scroll(".recs", 1.0)
    t.say("p:c08", "Rekomendacje z reguł: od tablicy po fotopułapkę — decyduje miasto")
    t.hold(0.8)


def push_in(png, secs, out, fx=0.5, fy=0.5, zoom=0.25):
    """Obraz → ujęcie: najazd kamery 1 → 1+zoom na punkt (fx, fy) z wygładzeniem (scena „żyje”, zamiast stać)."""
    fr = int(secs * 30)
    z = f"1+{zoom}*(on/{fr})*(on/{fr})*(3-2*on/{fr})"
    ffmpeg("-loop", 1, "-framerate", 30, "-t", f"{secs:.2f}", "-i", png, "-vf",
           f"scale=4096:-1,zoompan=z='{z}':x='iw*{fx}-iw/zoom/2':y='ih*{fy}-ih/zoom/2':d=1:s={W}x{H}:fps=30", *X264, out)


# sceny AI: (plik w demo/animacja, punkt najazdu x, y, przybliżenie); brak pliku = scena pominięta
SCENY = {"qr": ("mieszkanka-qr.png", 0.48, 0.42, 0.3), "przycisk": ("mieszkanka-panel.png", 0.42, 0.47, 0.5)}


def build(base):
    from playwright.sync_api import Error as PwError, sync_playwright
    slides = {k: PREVIEW / f"slajd-{k}.png" for k in ("01", "02", "03", "09")}
    if not all(s.is_file() for s in slides.values()):
        raise SystemExit("Brak podglądu slajdów — najpierw: python demo/build_all.py --tylko pdf")
    with tempfile.TemporaryDirectory() as td, sync_playwright() as pw:
        tmp = Path(td)
        voice = FastVoice(tmp)
        chrome = pw.chromium.launch()
        card(chrome, tmp / "end.png", *CARDS[3][1:3], big=True)
        photo = demo_photo(tmp / "kosz.jpg")
        req = chrome.new_context().request
        reset(req, base)
        takes = {}
        try:
            for name, run in (("A", lambda t: scenario_a(t, photo)), ("C", scenario_c)):
                log(f"Nagranie scenariusza {name}")
                t = FastTake(chrome, base, tmp / name, voice)
                try:
                    run(t)
                except PwError as e:
                    t.finish()
                    raise SystemExit(f"{name}: {str(e).splitlines()[0]}")
                takes[name] = t.finish()
        finally:
            reset(req, base, strict=False)
            chrome.close()

        segs, clips = [], []

        def still(png, key, extra=0.8, minimum=3.0, scene=None):
            mp3, secs = voice.clip(key) if key else (None, 0)
            segs.append(tmp / f"seg{len(segs):02d}.mp4")
            secs = max(minimum, secs + extra)
            if scene:
                push_in(png, secs, segs[-1], *scene)
            else:
                push_in(png, secs, segs[-1], zoom=0.03)
            if mp3:
                clips.append((len(segs) - 1, 0.35, mp3))

        def ai(name, key):
            f, *focus = SCENY[name]
            if (ANIM / f).is_file():
                still(ANIM / f, key, scene=focus)
            else:
                log(f"  UWAGA: brak sceny AI {f} — pomijam")

        def scene(name):
            segs.append(tmp / f"seg{len(segs):02d}.mp4")
            clips.extend((len(segs) - 1, s, mp3) for s, mp3 in cut(*takes[name], segs[-1], 10 ** 6))

        still(slides["01"], "k:01")
        still(slides["02"], "k:05", extra=1.5, minimum=6.5)  # liczby są na slajdzie, a słownie wracają na slajdzie korzyści
        still(slides["03"], "p:s03")
        ai("qr", "k:07")
        scene("A")
        ai("przycisk", "p:b02")  # scenariusz 2 (przycisk na panelu) w jednej scenie: obraz mówi więcej niż nagranie panelu
        scene("C")
        still(slides["09"], "p:s09")
        still(tmp / "end.png", "k:04", extra=1.2)

        durs = [duration(s) for s in segs]
        starts = [sum(durs[:i]) - i * FADE for i in range(len(segs))]
        ins = sum((["-i", s] for s in segs), [])
        fl, prev = [], "[0:v]"
        for i in range(1, len(segs)):
            fl.append(f"{prev}[{i}:v]xfade=transition=fade:duration={FADE}:offset={starts[i]:.3f}[v{i}]")
            prev = f"[v{i}]"
        film = tmp / "film.mp4"
        ffmpeg(*ins, "-filter_complex", ";".join(fl), "-map", prev, *X264, "-movflags", "+faststart", film)
        mix(film, [(starts[i] + s, mp3) for i, s, mp3 in clips], MP4, duration(film))
    total = duration(MP4)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    for k in range(int(total // 10) + 1):
        ffmpeg("-ss", f"{min(k * 10 + 2, total - 1):.2f}", "-i", MP4, "-frames:v", 1, "-vf", "scale=960:-1", PREVIEW / f"3min-{k:02d}.png")
    log(f"Film: {MP4} ({total:.0f} s = {int(total // 60)}:{int(total % 60):02d}, {len(clips)} klipów lektora ×{TEMPO})")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:5050")
    build(ap.parse_args().base.rstrip("/"))


if __name__ == "__main__":
    sys.exit(main())
