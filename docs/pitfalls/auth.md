# Pułapki: autoryzacja, tokeny, limity

Czytaj przed zmianą endpointów `POST`, tokenów QR/urządzeń, `app/residents.py`, `app/rate.py`, `SECRET_KEY`.

1. **Nie ma logowania ani ról** (od przebudowy UI: jedna rola „Przegląd jury”). Ochroną zapisu są tokeny HMAC i limity,
   więc każdy nowy endpoint zapisujący dane potrzebuje jednego z nich, inaczej pisze do niego cały internet.
2. **Wszystkie tokeny liczy się z `SECRET_KEY`** (`qr_token` w `app/api_pl.py`, `device_token` w `app/devices_api.py`,
   HMAC telefonu w `app/residents.py`, `app/wysypiska.py`). Bez `SECRET_KEY` w env jest fallback `dev-only-trash-fairy`
   i tokeny da się policzyć z publicznego kodu (aplikacja tylko loguje ostrzeżenie). Każdy prod musi mieć `SECRET_KEY`.
3. **Tokeny porównuj `hmac.compare_digest`**, nigdy `==` (wszystkie obecne miejsca tak robią).
4. **Token QR jest dzienny** (`kosz:<id>:<data>`) z oknem łaski `QR_GRACE_S`. Zmiana formatu unieważnia wydrukowane/
   wyświetlone kody na kioskach: zmieniaj tylko z okresem przejściowym.
5. **Limity muszą być w bazie** (`rate.hit(klucz, limit, okno_s)`), nie w pamięci: 2 workery Gunicorna podwoiłyby limit.
   Limit IP zgłoszeń podniesiono z 30 do 200/h, bo sala HackYeah wychodziła jednym IP (NAT).
6. **IP klienta tylko z `request.remote_addr` za `ProxyFix(x_for=1)`** (`app/__init__.py`): Coolify ma jedno proxy.
   Nie czytaj `X-Forwarded-For` ręcznie (klient może go podrobić); zmiana liczby proxy = zmiana `x_for`.
7. **Telefony tylko jako HMAC** (`app/residents.py`), SMS w trybie DEMO (Twilio Verify, SID w sesji). Nie zapisuj numeru
   jawnie ani w logach.
8. **Brak CSRF jest świadomy**: API `POST` przyjmuje JSON od własnego JS, bez sesji/ciasteczek dających uprawnienia.
   Jeśli dodasz logowanie przez ciasteczko sesji, endpointy zapisujące potrzebują ochrony CSRF (SameSite + token).
9. **Kierowca widzi kurs swojej floty** (`fleet` w `app/api_kierowca.py`, `kind == "bin"`/altany). Nowe pola w odpowiedzi
   kierowcy nie mogą zawierać danych mieszkańców (pseudonim, IP, telefon).
