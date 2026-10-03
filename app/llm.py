"""Jedyna brama do AI (CLAUDE.md): ask() i ask_json(). Model i klucz z env.

AI tylko opisuje i rozpoznaje — decyzje podejmują reguły w kodzie. Każdy błąd (brak klucza, sieć, limit,
odmowa modelu, zły JSON) zamieniamy na LLMError z komunikatem dla człowieka; wywołujący pokazuje
komunikat i ostatni wynik z bazy, nigdy 500.
"""
import base64
import json
import os

import anthropic

DEFAULT_MODEL = "claude-opus-5"
# serwerowy fallback po odmowie filtra bezpieczeństwa — wspierany przez Opus 5 i Fable 5.1
FALLBACK_MODELS = {"claude-opus-5", "claude-fable-5-1"}
TIMEOUT_S = 60


class LLMError(Exception):
    """Komunikat nadaje się do pokazania użytkownikowi."""


def model():
    return os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)


def available():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def image_block(data, media_type):
    return {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                        "data": base64.standard_b64encode(data).decode("ascii")}}


def _create(system, content, output_config, max_tokens):
    if not available():
        raise LLMError("Analiza AI niedostępna: brak klucza ANTHROPIC_API_KEY.")
    client = anthropic.Anthropic(timeout=TIMEOUT_S)
    kwargs = {}
    if model() in FALLBACK_MODELS:
        kwargs = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    try:
        response = client.beta.messages.create(
            model=model(), max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": content}],
            output_config=output_config, **kwargs,
        )
    except anthropic.AuthenticationError:
        raise LLMError("Analiza AI niedostępna: nieprawidłowy klucz API.")
    except anthropic.RateLimitError:
        raise LLMError("Analiza AI chwilowo niedostępna (limit zapytań). Spróbuj za minutę.")
    except anthropic.APIConnectionError:
        raise LLMError("Analiza AI niedostępna: brak połączenia z API.")
    except anthropic.APIStatusError as e:
        raise LLMError(f"Analiza AI niedostępna (błąd API {e.status_code}).")
    if response.stop_reason == "refusal":
        raise LLMError("Model odmówił analizy tego materiału.")
    text = next((b.text for b in response.content if b.type == "text"), "")
    if not text:
        raise LLMError("Model nie zwrócił odpowiedzi.")
    return text


def ask(prompt, system=None, max_tokens=4000):
    """Tekst → tekst (np. raport dla dyspozytora). Model dostaje gotowe liczby i niczego nie liczy."""
    return _create(system, prompt, {"effort": "medium"}, max_tokens)


def ask_json(prompt, schema, system=None, images=(), max_tokens=4000):
    """Tekst (+ obrazy jako bloki z image_block) → dict zgodny ze schematem JSON (structured outputs)."""
    content = [*images, {"type": "text", "text": prompt}]
    text = _create(system, content, {"effort": "low", "format": {"type": "json_schema", "schema": schema}}, max_tokens)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise LLMError("Model zwrócił niepoprawny JSON.")
