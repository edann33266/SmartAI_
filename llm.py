import json
import os
from dotenv import load_dotenv

load_dotenv()

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _gemini_generate(prompt: str, temperature: float, want_json: bool = False) -> str:
    if not _GEMINI_API_KEY:
        return "[ERROR] GEMINI_API_KEY is not set. Add it to your .env file or host environment variables."

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_GEMINI_API_KEY)

        config = types.GenerateContentConfig(temperature=temperature)
        if want_json:
            config.response_mime_type = "application/json"

        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        return (response.text or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"[ERROR] Gemini request failed: {exc}"


def generate_text(prompt: str, temperature: float = 0.7) -> str:
    """
    Generate plain text via Gemini.
    """
    return _gemini_generate(prompt, temperature=temperature, want_json=False)


def generate_json(prompt: str, temperature: float = 0.3) -> dict:
    """
    Ask Gemini to return a JSON object. Parses defensively.
    On errors, returns {"_raw": ...} so callers (e.g. SalesManagerAgent)
    can fall back gracefully instead of crashing.
    """
    raw = _gemini_generate(prompt, temperature=temperature, want_json=True)

    def _try_parse(text: str) -> dict | None:
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    parsed = _try_parse(raw)
    if parsed is not None:
        return parsed

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
        parsed = _try_parse(cleaned)
        if parsed is not None:
            return parsed

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start : end + 1]
        parsed = _try_parse(candidate)
        if parsed is not None:
            return parsed

    return {"_raw": raw}
