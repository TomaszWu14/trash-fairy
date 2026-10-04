from . import db

# Wszystkie znaczniki czasu w czasie demo (zegar scenariusza), naiwne datetime.
# Wyjątek: Press.wall_at to prawdziwy czas UTC, potrzebny do limitu naciśnięć na IP.


class Point(db.Model):
    """Kosz uliczny (kind='bin') albo altana osiedlowa (kind='shelter')."""
    id = db.Column(db.Integer, primary_key=True)
    osm_id = db.Column(db.String(32), unique=True, nullable=False)
    kind = db.Column(db.String(10), nullable=False)
    area = db.Column(db.String(20), nullable=False)  # Rynek / Kazimierz / Grzegórzki
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    osm_tags = db.Column(db.JSON, nullable=False, default=dict)
    base_rate = db.Column(db.Float, nullable=False)  # średnie tempo zapełniania, % na godzinę
    overloaded = db.Column(db.Boolean, nullable=False, default=False)  # celowo przeciążona altana (demo)
    # live=True: 72 punkty silnika demo (symulacja, prognoza, trasy, porównanie). live=False: punkty panelu miasta
    # (app/city_import.py) — tylko historia syntetyczna, silnik demo ich nie widzi (Point.live_query()).
    live = db.Column(db.Boolean, nullable=False, default=True)
    district = db.Column(db.String(30))  # dzielnica Krakowa, np. „Stare Miasto”
    fraction = db.Column(db.String(20), nullable=False, default="zmieszane")  # app/history.py: FRACTIONS
    address = db.Column(db.String(160))
    snapshot_fill = db.Column(db.Integer)  # tylko punkty miasta: zapełnienie % w chwili DEMO_NOW z generatora historii

    @classmethod
    def live_query(cls):
        """Punkty silnika demo. Każde zapytanie silnika iterujące po punktach idzie przez tę metodę."""
        return cls.query.filter(cls.live.is_(True))

    @classmethod
    def live_or_404(cls, point_id):
        return cls.live_query().filter_by(id=point_id).first_or_404()


class Pickup(db.Model):
    """Odbiór historyczny (syntetyczny, app/history.py). Odbiory na żywo to Emptying — panel łączy oba (UNION)."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, index=True)
    fraction = db.Column(db.String(20), nullable=False)
    mass_kg = db.Column(db.Float, nullable=False)
    cost_pln = db.Column(db.Float, nullable=False)
    km = db.Column(db.Float, nullable=False)  # przejazd przypisany do odbioru (CO₂, koszt)
    fill_pct = db.Column(db.Integer, nullable=False)  # zapełnienie w chwili odbioru
    on_demand = db.Column(db.Boolean, nullable=False, default=False)
    far_m = db.Column(db.Integer)  # odległość telefonu ekipy od kosza przy potwierdzeniu (jak Emptying.far_m); None = brak


class ReportHistory(db.Model):
    """Zgłoszenie historyczne (syntetyczne). Zgłoszenia na żywo to Report — panel łączy oba (UNION)."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime)
    kind = db.Column(db.String(20), nullable=False)  # przepelniony / uszkodzony / odpady_obok / inne


class Project(db.Model):
    """Projekt miejski w dzielnicy. Efekt (effect_label/effect_value) liczony z historii przed/po starcie."""
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    district = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # planowany / w_realizacji / zakonczony
    progress_pct = db.Column(db.Integer, nullable=False)
    budget_pln = db.Column(db.Float, nullable=False)
    spent_pln = db.Column(db.Float, nullable=False)
    start = db.Column(db.Date, nullable=False)
    end = db.Column(db.Date, nullable=False)
    metric = db.Column(db.String(30), nullable=False)  # miara efektu: app/history.py PROJECT_METRICS
    effect_label = db.Column(db.String(120), nullable=False)
    effect_value = db.Column(db.Float)  # None = za wcześnie (planowany)
    icon = db.Column(db.String(30), nullable=False)  # nazwa ikony Lucide


class Press(db.Model):
    """Pojedyncze naciśnięcie przycisku. Scalanie w zgłoszenia: app/reports.py."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False)
    ip = db.Column(db.String(45))
    wall_at = db.Column(db.DateTime, index=True)  # None = naciśnięcie z symulacji
    source = db.Column(db.String(10), nullable=False, default="button")  # button / qr
    kind = db.Column(db.String(10))  # full / overflow / damaged (None = fizyczny przycisk, czyli „pełny”)
    resident_id = db.Column(db.Integer, db.ForeignKey("resident.id"), index=True)  # None = anonimowe
    report_id = db.Column(db.Integer, db.ForeignKey("report.id"), index=True)
    note = db.Column(db.String(280))  # komentarz mieszkańca z nowego formularza zgłoszenia
    photo_id = db.Column(db.Integer)  # PhotoAnalysis.id zdjęcia dołączonego do zgłoszenia


class StopIssue(db.Model):
    """Kierowca na przystanku: nie da się podjechać albo problem z koszem (PWA /kierowca)."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, index=True)
    kind = db.Column(db.String(12), nullable=False)  # no_access / damaged / blocked / overflow
    note = db.Column(db.String(200))


class Report(db.Model):
    """Zgłoszenie: naciśnięcia jednego punktu w oknie 15 minut od pierwszego naciśnięcia."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    first_at = db.Column(db.DateTime, nullable=False)
    last_at = db.Column(db.DateTime, nullable=False)
    presses = db.Column(db.Integer, nullable=False, default=1)
    weight = db.Column(db.Float, nullable=False)  # wiarygodność przycisku w chwili zgłoszenia
    hit = db.Column(db.Boolean)  # None = otwarte; po opróżnieniu: trafne / fałszywe
    resolved_at = db.Column(db.DateTime)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)  # potwierdzone przez zarejestrowanego mieszkańca


class Emptying(db.Model):
    """Opróżnienie punktu przez ekipę MPO, z poziomem zastanym przed opróżnieniem."""
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False, index=True)
    level = db.Column(db.Integer, nullable=False)  # 0/25/50/75/100
    source = db.Column(db.String(10))  # None = symulacja, "crew" = zapis z PWA kierowcy lub panelu
    far_m = db.Column(db.Integer)  # odległość telefonu od kosza minus dokładność GPS (None = bez położenia)


class Forecast(db.Model):
    """Szereg czasowy poziomu zapełnienia punktu.

    source='sim'  — symulacja (historia + 24 h „przyszłości” odsłanianej przewijaniem zegara),
    source='pred' — prognoza (etap 3).
    """
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False)
    at = db.Column(db.DateTime, nullable=False)
    level = db.Column(db.Float, nullable=False)  # %, może przekroczyć 100 (przepełnienie)
    source = db.Column(db.String(8), nullable=False, default="sim")

    __table_args__ = (db.Index("ix_forecast_point_at", "point_id", "at"),)


class Event(db.Model):
    """Wydarzenie, które zwiększa tempo zapełniania koszy w promieniu zależnym od skali tłumu."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    scale = db.Column(db.String(10), nullable=False)  # small / medium / large
    source = db.Column(db.String(10), nullable=False, default="manual")  # manual / karnet (etap 6)


class PhotoAnalysis(db.Model):
    """Zdjęcie od ekipy MPO i wynik analizy Claude Vision (koncepcja, sekcja 5).

    Zdjęcie usuwamy po 7 dniach (photo_path → None), wynik analizy zostaje.
    """
    id = db.Column(db.Integer, primary_key=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False, index=True)
    at = db.Column(db.DateTime, nullable=False)  # czas zegara demo
    wall_at = db.Column(db.DateTime, nullable=False)  # prawdziwy czas UTC (retencja zdjęć)
    photo_path = db.Column(db.String(255))
    media_type = db.Column(db.String(20))
    crew_level = db.Column(db.Integer)  # poziom kliknięty przez ekipę
    status = db.Column(db.String(10), nullable=False, default="pending")  # pending / done / error
    error = db.Column(db.String(255))
    fill_level = db.Column(db.Integer)
    overflow_outside = db.Column(db.Boolean)
    misuse = db.Column(db.JSON)  # ["household_bag", ...]
    damage = db.Column(db.Boolean)
    confidence = db.Column(db.Float)
    note = db.Column(db.String(500))
    source = db.Column(db.String(10), nullable=False, default="crew")  # crew / demo / resident (zdjęcie ze zgłoszenia)
    bin_visible = db.Column(db.Boolean)  # tylko zdjęcia mieszkańców: kosz widoczny na zdjęciu
    condition = db.Column(db.String(20))  # w_porzadku / pelny / odpady_obok / uszkodzony
    people = db.Column(db.Boolean)  # osoby lub tablice rejestracyjne na zdjęciu → zdjęcie niepubliczne


class FairyReport(db.Model):
    """Raport „Wróżka podpowiada”: fakty policzone w kodzie + tekst od Claude (cache na wypadek błędu API)."""
    id = db.Column(db.Integer, primary_key=True)
    at = db.Column(db.DateTime, nullable=False)  # czas zegara demo
    facts = db.Column(db.JSON, nullable=False)
    sections = db.Column(db.JSON, nullable=False)  # [{"title", "text"}]
    model = db.Column(db.String(60), nullable=False)
    unknown_numbers = db.Column(db.JSON, nullable=False, default=list)  # liczby w tekście, których nie ma w faktach


class Resident(db.Model):
    """Uczestnik programu „Przyjaciele Wróżki”. Bez danych osobowych: pseudonim + hash telefonu."""
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(40), unique=True, nullable=False)
    phone_hash = db.Column(db.String(64), unique=True, nullable=False)
    district = db.Column(db.String(20), nullable=False)
    verified = db.Column(db.Boolean, nullable=False, default=False)
    code = db.Column(db.String(6))  # kod „SMS” (w demo pokazywany na ekranie)
    source = db.Column(db.String(10), nullable=False, default="live")  # live / demo


class PointAward(db.Model):
    """Punkty za trafne zgłoszenie (jedna nagroda na mieszkańca, punkt i dzień)."""
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("resident.id"), nullable=False, index=True)
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey("report.id"))
    at = db.Column(db.DateTime, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(10), nullable=False)  # bin / shelter


class DumpReport(db.Model):
    """Zgłoszenie dzikiego wysypiska (app/wysypiska.py): położenie jest treścią zgłoszenia, nie ma kosza.

    parent_id: zgłoszenie dołączone do otwartego wysypiska (50 m, 72 h). Wiersz bez parent_id to samo wysypisko:
    na nim liczymy potwierdzenia, status AI i uprzątnięcie. Zdjęcie bez EXIF usuwamy po 7 dniach (photo_path → None),
    media_type zostaje jako ślad, że zdjęcie było (punkty)."""
    id = db.Column(db.Integer, primary_key=True)
    at = db.Column(db.DateTime, nullable=False, index=True)  # zegar demo
    wall_at = db.Column(db.DateTime, nullable=False)  # prawdziwy czas UTC (retencja zdjęć, analiza w toku)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    kinds = db.Column(db.JSON, nullable=False, default=list)  # klucze wysypiska.KINDS
    qty = db.Column(db.Integer)  # szacunek worków/sztuk 1–100; None = „nie wiem”
    note = db.Column(db.String(280))
    photo_path = db.Column(db.String(255))
    media_type = db.Column(db.String(20))
    ai = db.Column(db.JSON)  # opis zdjęcia od AI: {"status": "pending"|"done"|"error", ...}; None = bez zdjęcia
    status = db.Column(db.String(16), nullable=False, default="do_weryfikacji")  # reguła: w_toku / zweryfikowane / do_weryfikacji
    source = db.Column(db.String(10), nullable=False, default="resident")  # resident / crew
    client = db.Column(db.String(64))  # HMAC identyfikatora telefonu (niezależność potwierdzeń)
    resident_id = db.Column(db.Integer, index=True)  # bez klucza obcego: reset demo kasuje mieszkańców
    parent_id = db.Column(db.Integer, index=True)
    confirmations = db.Column(db.Integer, nullable=False, default=1)  # niezależne zgłoszenia (różne telefony), tylko wysypisko
    cleared_at = db.Column(db.DateTime)  # „Uprzątnięte” przez ekipę (zegar demo), tylko wysypisko
    cleared_by = db.Column(db.String(32))  # HMAC telefonu, który oznaczył „Uprzątnięte” (bez punktów za własne zgłoszenie)


class Device(db.Model):
    """Fizyczny przycisk z wyświetlaczem e-papierowym przy punkcie (stan symulowany w demo)."""
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), primary_key=True)
    last_heartbeat = db.Column(db.DateTime, nullable=False)  # czas zegara demo
    battery = db.Column(db.Integer, nullable=False)  # %
    last_selftest = db.Column(db.DateTime)
    selftest_ok = db.Column(db.Boolean, nullable=False, default=True)


class DemoClock(db.Model):
    """Zegar scenariusza demo (jeden wiersz). W bazie, bo gunicorn ma kilka procesów."""
    id = db.Column(db.Integer, primary_key=True)
    now = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime)  # prawdziwy czas UTC ostatniej akcji w demo (auto-reset po bezczynności)


class Counter(db.Model):
    """Liczniki limitów (SMS, AI, logowanie) wspólne dla wszystkich workerów Gunicorna: okno stałe, klucz + początek okna."""
    key = db.Column(db.String(120), primary_key=True)
    window_start = db.Column(db.Integer, primary_key=True)  # sekundy epoki, początek okna
    count = db.Column(db.Integer, nullable=False, default=0)


class DeviceInfo(db.Model):
    """Masterdane urządzenia na koszu (DANE SYNTETYCZNE, app/devices.py). Panel e-papierowy: sygnał, bateria i autotest
    nadal w Device; czujnik zapełnienia (pilotaż Nowa Huta): sygnał i autotest tutaj, bateria z wieku (devices.battery)."""
    point_id = db.Column(db.Integer, db.ForeignKey("point.id"), primary_key=True)
    kind = db.Column(db.String(10), nullable=False)  # panel / czujnik
    model = db.Column(db.String(60), nullable=False)
    serial = db.Column(db.String(20), unique=True, nullable=False)
    installed_at = db.Column(db.DateTime, nullable=False)
    firmware = db.Column(db.String(12), nullable=False)
    drain = db.Column(db.Float, nullable=False, default=1.0)  # tempo zużycia baterii względem założenia (1 = nominalne)
    loss = db.Column(db.Float, nullable=False, default=0.0)  # udział odczytów zgubionych w transmisji
    last_seen = db.Column(db.DateTime)  # tylko czujnik; panel: Device.last_heartbeat
    selftest_ok = db.Column(db.Boolean)  # tylko czujnik; panel: Device.selftest_ok
