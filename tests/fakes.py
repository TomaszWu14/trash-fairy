"""Fałszywy opener dla app/http.py: odpowiedzi po fragmencie adresu, zapis wysłanych żądań, bez sieci."""
import io
import json
import urllib.error


class _Resp(io.BytesIO):
    def __init__(self, status, body):
        super().__init__(json.dumps(body).encode())
        self.status = status


class FakeOpener:
    def __init__(self, routes):
        """routes: {fragment_adresu: (status, body) | Exception | callable(req) -> (status, body)}."""
        self.routes, self.requests = routes, []

    def open(self, req, timeout=None):
        self.requests.append(req)
        for fragment, answer in self.routes.items():
            if fragment in req.full_url:
                if callable(answer) and not isinstance(answer, type):
                    answer = answer(req)
                if isinstance(answer, Exception):
                    raise answer
                status, body = answer
                if status >= 400:
                    raise urllib.error.HTTPError(req.full_url, status, "error", {}, io.BytesIO(json.dumps(body).encode()))
                return _Resp(status, body)
        raise urllib.error.URLError(f"brak trasy w FakeOpener: {req.full_url}")
