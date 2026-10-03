FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_APP=app PORT=8080
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:%s/health' % os.environ.get('PORT', '8080'))"

# seed pomija import, jeśli baza ma już punkty
# port z env PORT (domyślnie 8080 — na serwerze 8000 jest zajęty)
CMD flask seed && gunicorn --bind 0.0.0.0:${PORT} --workers 2 --preload app.wsgi:app
