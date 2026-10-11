# 05. Wymagania z kryteriami akceptacji

Wymagania opisują to, co aplikacja **robi dziś**, i każde ma test, który je sprawdza (`python -m pytest -q`).
Rzeczy, których nie ma, są w [07-ograniczenia.md](07-ograniczenia.md), a nie tutaj.
Kolumna „Gdzie” wskazuje kod i test.

## Zgłoszenia (mieszkaniec, panel na koszu)

| ID | Wymaganie | Kryterium akceptacji | Gdzie |
|---|---|---|---|
| ZG-01 | Mieszkaniec zgłasza problem z kosza tylko po zeskanowaniu kodu QR tego kosza. | Zgłoszenie z dzisiejszym tokenem kosza jest przyjęte (201). Bez tokenu albo z tokenem z innego dnia: 403 `brak_skanu_qr` i komunikat po polsku. Położenie telefonu nie jest sprawdzane. | `app/api_pl.py:24-50, 130-142`; `tests/test_qr_rotacja.py::test_report_accepts_todays_code_and_rejects_old_photo`, `tests/test_zglos.py::test_report_gate_is_bin_token_not_location` |
| ZG-02 | Kod QR zmienia się codziennie, z godziną tolerancji. | Token zmienia się o północy czasu warszawskiego. Wczorajszy działa jeszcze do 1:00, potem jest odrzucany. | `app/api_pl.py:24-50`; `test_qr_rotacja.py::test_token_changes_at_midnight_in_krakow`, `::test_yesterdays_code_works_only_in_first_hour_after_midnight` |
| ZG-03 | Fizyczny przycisk na panelu działa bez kodu QR, ale tylko z tokenem urządzenia. | Naciśnięcie z poprawnym tokenem panelu jest przyjęte. Bez tokenu: 403. Limit to 3 zgłoszenia na minutę z kosza. | `app/api_pl.py:106-126`; `test_qr_rotacja.py::test_panel_button_needs_device_token` |
| ZG-04 | Wiele naciśnięć jednego kosza w krótkim czasie to jedno zgłoszenie. | 30 naciśnięć w 15 min daje 1 zgłoszenie z licznikiem 30. Naciśnięcie po 15 min od pierwszego zakłada nowe zgłoszenie. | `app/reports.py:12, 49-76`; `tests/test_reports.py::test_30_presses_in_15_minutes_make_one_report`, `::test_press_after_15_minutes_from_first_starts_new_report` |
| ZG-05 | Zgłoszenie ma typ: przepełniony, odpady obok, uszkodzony, inne. | „Odpady obok” liczy się jak przepełnienie i jest oznaczony. „Uszkodzony” nie podnosi poziomu, ale oznacza kosz flagą. | `app/api_wspolne.py:23-28`, `app/state.py:166-213`; `test_zglos.py::test_overflow_counts_as_full_and_is_noted`, `::test_damaged_press_does_not_raise_level_but_flags_point` |
| ZG-06 | Limity chronią przed zalewem zgłoszeń. | Druga próba z tego samego telefonu do tego samego kosza w ciągu minuty: 429 z czasem ponowienia. Ponad 200 zgłoszeń na godzinę z jednego IP: 429. | `app/api_pl.py:30-31, 146-151`, `app/rate.py` |
| ZG-07 | Mieszkaniec widzi status swojego zgłoszenia. | Status przechodzi „przyjęte → w realizacji (kierowca kliknął „Jadę”) → zrealizowane” z dowodem odbioru. Nieznany numer pokazuje komunikat i link do nowego zgłoszenia. | `app/api_pl.py:170-193`, `templates/ui/zgloszenie.html`; `tests/test_mieszkaniec_ekrany.py` |

## Stan kosza i prognoza

| ID | Wymaganie | Kryterium akceptacji | Gdzie |
|---|---|---|---|
| ST-01 | Każdy kosz ma stan z progami i powodem słownym. | Wartość > 85% daje „do opróżnienia” (!), ≥ 60% „zapełnia się” (↑), poniżej „w porządku” (✓). Każdy stan ma symbol, opis i powód, np. „zgłoszenie: 3× naciśnięty, wiarygodność 80%”. | `app/state.py:20-51, 235-240` (słownik `STATES`, :39-43); `test_reports.py::test_level_state_thresholds` |
| ST-02 | Świeże wiarygodne zgłoszenie od razu zmienia stan kosza. | Zgłoszenie sprzed ≤ 15 min z wagą ≥ 0,7 daje „Do opróżnienia” i powód „zgłoszenie”. | `app/state.py:22, 222-224`; `test_reports.py::test_fresh_report_turns_point_red_with_reason` |
| ST-03 | Waga zgłoszenia zależy od historii przycisku. | Wiarygodność to odsetek trafnych z ostatnich 10 zgłoszeń, na start 70%. 7 nietrafnych z 10 daje 30% i flagę „sprawdź przycisk”. | `app/reports.py:14-37`; `test_reports.py::test_reliability_last_10_and_default`, `::test_7_false_of_10_gives_30_percent_and_flag` |
| ST-04 | Reguły antyspamowe osłabiają podejrzane zgłoszenia. | Zgłoszenie < 2 h po opróżnieniu przy poziomie < 30% liczy się w połowie. Wzorzec trolla (≥ 3 fałszywe o tej porze w 14 dni) daje ×0,5. Puści sąsiedzi w 100 m dają ×0,7. Zgłoszenie potwierdzone przez zarejestrowanego mieszkańca nie jest osłabiane. | `app/state.py:23-36, 67-86`; `test_reports.py::test_report_right_after_emptying_at_low_level_is_weak`, `tests/test_residents.py::test_troll_pattern_same_hour_false_reports`, `::test_neighbors_empty_weakens_only_unconfirmed` |
| ST-05 | Prognoza podaje godzinę przekroczenia 85% w horyzoncie 24 h, z przedziałem. | Dla znanego profilu godzina przekroczenia zgadza się z wyliczeniem. Przedział liczony jest z wolnego (p20) i szybkiego (p80) tempa. | `app/forecast.py:20-21, 47-134`; `tests/test_forecast.py::test_known_profile_gives_expected_crossing_time`, `::test_interval_from_slow_and_fast_rates` |
| ST-06 | Wydarzenia w pobliżu przyspieszają prognozę. | Małe wydarzenie: 200 m, ×1,3. Średnie: 400 m, ×1,6. Duże: 800 m, ×2,0. Efekt trwa do godziny po końcu wydarzenia. | `app/events.py:14-34`; `test_forecast.py::test_event_multiplier_radius_and_hour_after`, `::test_event_raises_forecast` |
| ST-07 | Prognoza jest lepsza od naiwnej średniej. | MAE na ostatnim tygodniu (dane spoza nauki) jest niższe niż dla średniej naiwnej. Na seedzie: 2,4 kontra 7,1 p.p. | `app/forecast.py:149-177`; `test_forecast.py::test_forecast_beats_naive_average` |

## Trasa i kierowca

| ID | Wymaganie | Kryterium akceptacji | Gdzie |
|---|---|---|---|
| TR-01 | Na kurs trafiają kosze, które nie doczekają kolejnego kursu. | Kurs zabiera kosz, który jest „Do opróżnienia” albo przekroczy 85% przed kolejnym kursem. Kosz, który przekroczy próg dopiero po kolejnym kursie, zostaje pominięty. | `app/routes.py:66-75`; `tests/test_routes.py::test_selects_full_point`, `::test_selects_point_crossing_before_following_run`, `::test_skips_point_crossing_after_following_run` |
| TR-02 | Bezpiecznik: żaden kosz nie czeka w nieskończoność. | Kosz bez odbioru przez 3 dni, a altana przez 7 dni, trafia na kurs niezależnie od prognozy. | `app/routes.py:26-31`; `test_routes.py::test_safety_3_days_for_bins_and_7_for_shelters` |
| TR-03 | Każdy pominięty kosz ma powód. | Lista kierowcy pokazuje pominięte kosze z powodem, np. „opróżniony 3 h temu” albo „bezpiecznik za 2 dni”. | `app/routes.py:78-91`; `test_routes.py::test_skip_reason_explains_points_left_for_later`, `tests/test_kierowca.py::test_trasa_lists_skipped_bins_with_reasons` |
| TR-04 | Trasa odwiedza każdy wybrany kosz raz i mieści się w pojemności pojazdów. | Start i koniec są w bazie. Każdy punkt jest odwiedzony dokładnie raz. Przekroczenie pojemności dzieli trasę na pojazdy (najwyżej 3). | `app/routes.py:94-137`; `test_routes.py::test_route_visits_each_point_once_from_depot`, `::test_capacity_splits_route_into_vehicles_and_visits_each_point_once` |
| TR-05 | Kierowca zamyka zgłoszenia opróżnieniem. | „Opróżniono” przyjmuje tylko poziom 0/25/50/75/100. Rozstrzyga otwarte zgłoszenia: poziom ≥ 75% oznacza trafne. Stan kosza wraca do zera. | `app/api_kierowca.py:16, 131-158`, `app/reports.py:79-90`; `tests/test_photos.py::test_crew_emptying_resolves_reports_and_resets_estimate`, `::test_crew_emptying_validates_level` |
| TR-06 | Kierowca zgłasza problem na przystanku. | Problem (brak dojazdu, uszkodzony, zastawiony, przepełniony) oznacza kosz flagą widoczną do opróżnienia, najwyżej 12 h. Zły rodzaj problemu daje 400. | `app/api_kierowca.py:17-18`, `app/state.py:26-28, 209-213`; `test_kierowca.py::test_stop_issue_flags_point_until_emptying`, `::test_stop_issue_rejects_bad_input` |
| TR-07 | Odbiór daleko od kosza jest zapisany, ale oznaczony. | Opróżnienie dalej niż 150 m od kosza jest zapisane z flagą i trafia do anomalii na dashboardzie. | `app/api_kierowca.py:144-147`, `app/dashboard.py:23`; `test_kierowca.py::test_far_emptying_is_saved_with_flag_and_counts_as_progress` |
| TR-08 | Dyspozytor dokłada kosz do kursu. | „Dodaj do kursu” stawia kosz na początku trasy. Drugie kliknięcie nic nie zmienia. „Cofnij” albo opróżnienie zamyka decyzję. | `app/routes.py:34-49, 172-175`, `app/dyspozytor_api.py:133-142`; `tests/test_dyspozytor.py::test_add_puts_bin_first_on_route_and_is_idempotent`, `::test_undo_and_emptying_close_the_decision` |

## Zdjęcia i AI

| ID | Wymaganie | Kryterium akceptacji | Gdzie |
|---|---|---|---|
| AI-01 | AI tylko opisuje zdjęcie, o statusie decyduje reguła, AI nigdy nie odrzuca zgłoszenia. | „Zweryfikowane AI”, gdy kosz widoczny, stan zgodny z typem zgłoszenia i pewność ≥ 0,7. W przeciwnym razie „Do weryfikacji”. Zgłoszenie jest przyjęte w każdym przypadku. | `app/photos.py:92-121`; `tests/test_kierowca.py::test_ai_ok_photo_lowers_priority_but_never_rejects` |
| AI-02 | Brak klucza albo błąd API nie psuje aplikacji. | Bez klucza i przy błędzie API aplikacja pokazuje komunikat i ostatni dobry wynik, nigdy 500. Niepoprawna odpowiedź AI jest odrzucana, a wtedy działają reguły. | `app/llm.py:97-142`; `test_photos.py::test_llm_without_key_gives_message_not_exception`, `::test_api_error_shows_message_and_last_result`, `tests/test_ai_safety.py::test_invalid_ai_reply_falls_back_to_rules` |
| AI-03 | Zdjęcie jest walidowane i oczyszczone z danych osobowych. | Plik ≤ 8 MB i ≤ 40 Mpx, typ rozpoznany po sygnaturze (JPEG, PNG, WebP). EXIF z GPS usuwany przed zapisem. Plik kasowany po 7 dniach, wynik analizy zostaje. | `app/photos.py:17, 94, 124-176, 240-249`; `test_photos.py::test_validate_by_magic_bytes_and_size`, `::test_cleanup_removes_photo_files_after_7_days_but_keeps_analysis` |
| AI-04 | Tekst z zewnątrz nie może sterować AI. | Tekst zewnętrzny jest odgrodzony i obcięty. Wydarzenie wstrzyknięte przez AI nie przekroczy mnożnika z reguł. Odpowiedź AI z kodem HTML jest escapowana. | `app/llm.py:41-46`; `tests/test_ai_safety.py` (7 testów) |

## Wysypiska, miasto, dane otwarte

| ID | Wymaganie | Kryterium akceptacji | Gdzie |
|---|---|---|---|
| WD-01 | Zgłoszenie dzikiego wysypiska jest walidowane. | Miejsce poza Krakowem, brak rodzaju albo ilość spoza 1–100 dają 400 z komunikatem. Błędny JSON nigdy nie daje 500. | `app/wysypiska_api.py:34-63`; `tests/test_wysypiska.py::test_validation`, `::test_validation_json_never_500` |
| WD-02 | Drugie zgłoszenie tego samego wysypiska nie tworzy duplikatu. | Zgłoszenie do 50 m od otwartego wysypiska z ostatnich 72 h dołącza do niego. Gdy przychodzi z innego telefonu, zwiększa liczbę potwierdzeń. | `app/wysypiska.py:137-161`; `test_wysypiska.py::test_duplicate_within_50_m_joins_and_confirms` |
| MI-01 | Dashboard pokazuje koszt wobec planu z uczciwym punktem odniesienia. | Plan to średnia dzienna sprzed wdrożenia × indeks grupy kontrolnej. Oszczędności = (plan − odbiory) × koszt wizyty + (plan − km) × koszt km. Kafel reaguje na filtry. | `app/dashboard.py:236-291`; `tests/test_oszczednosci.py::test_savings_tile_fields_and_consistency`, `::test_savings_tile_follows_filters` |
| MI-02 | Dane syntetyczne są oznaczone, a akcje z pokazu liczą się od razu. | Odpowiedzi API mają etykietę danych demonstracyjnych. Opróżnienie z aplikacji kierowcy liczy się na dashboardzie od razu, a symulowane nie. | `app/dashboard_api.py`; `tests/test_dashboard.py::test_kpi_shape_and_synthetic_label`, `::test_live_emptying_counts_immediately`, `::test_simulated_emptying_does_not_count` |
| MI-03 | Rekomendacje inwestycyjne wynikają z danych z 4 tygodni. | Kompaktor: kosz przepełniony w > 50% dni i ≥ 2 opróżnienia dziennie. Większy pojemnik: przepełniony w ≥ 20% dni. Rzadszy odbiór: < 20% opróżnień przy poziomie ≥ 50%. | `app/recommendations.py:11-60`; `tests/test_rekomendacje.py::test_ladder_thresholds` |
| MI-04 | Eksport CSV respektuje filtry dashboardu i jest bezpieczny dla Excela. | CSV z BOM, separator `;`. Te same filtry co na ekranie. Nazwy zaczynające się od `=` nie są wykonywane jako formuły. | `app/dashboard_api.py:497-538`; `test_dashboard.py::test_csv_export_uses_dashboard_filters` |
| OD-01 | Otwarte API udostępnia dane bez danych osobowych. | GeoJSON koszy, CSV danych miesięcznych i Open311 (tylko odczyt) nie zawierają IP, notatek ani identyfikatorów mieszkańców. Złe parametry dają 400. | `app/open_api.py`; `tests/test_open_api.py::test_open_data_csv_has_bom_source_and_no_personal_fields`, `::test_open311_filters_validation` |

## Wymagania niefunkcjonalne

| ID | Wymaganie | Kryterium akceptacji | Gdzie |
|---|---|---|---|
| NF-01 | Prywatność: minimum danych. | IP naciśnięcia kasowane po 24 h. Telefon zapisywany tylko jako HMAC. Na ekranie e-papieru nie ma danych osobowych. | `app/privacy.py`, `app/residents.py:48-59`; `tests/test_prywatnosc.py::test_old_ips_are_forgotten`, `tests/test_epapier.py::test_no_personal_data_on_screen` |
| NF-02 | Integracje nie blokują pracy. | OSRM, pogoda i ruch mają limit czasu 2–4 s. Przy błędzie aplikacja używa ostatniej wartości albo neutralnej (linia prosta, ×1,0). | `app/osrm.py:15, 53-54`, `app/weather.py:57-69`, `app/traffic.py:55-70`; `tests/test_osrm.py`, `tests/test_weather.py`, `tests/test_traffic.py` |
| NF-03 | Błędy zwracają polski komunikat, a nie stronę serwera. | 404 na stronie to polska strona HTML, a na `/api/*` JSON. Złe filtry dashboardu dają 400 z komunikatem. | `app/__init__.py:101-118`; `test_zglos.py::test_404_is_polish_html_and_api_stays_json`, `test_dashboard.py::test_bad_filters_give_polish_error` |
| NF-04 | Dostępność WCAG 2.1 AA w obu motywach. | Kolor nigdy nie jest jedynym nośnikiem informacji (stan ma też symbol i tekst). Deklaracja na `/dostepnosc`. | `templates/dostepnosc.html`; `tests/test_prywatnosc.py::test_accessibility_and_privacy_pages` |
| NF-05 | Wyniki są powtarzalne. | Symulacja i generator historii są deterministyczne (stały seed). Porównanie daje te same liczby przy każdym uruchomieniu. | `app/simulation.py`, `app/history.py`; `tests/test_simulation.py::test_simulation_is_deterministic`, `tests/test_routes.py::test_comparison_is_deterministic_and_saves_visits` |
