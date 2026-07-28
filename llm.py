import json
import os

import requests
from dotenv import load_dotenv


load_dotenv()

# Ollama configuration
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
_OLLAMA_TIMEOUT_S = float(os.getenv("OLLAMA_TIMEOUT_S", "120"))


def _ollama_generate(prompt: str, temperature: float, response_format: str | None = None) -> str:
    """
    Low-level helper to call the local Ollama HTTP API.
    """
    try:
        payload: dict = {
            "model": _OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if response_format is not None:
            # Ollama supports structured output via "format": "json"
            payload["format"] = response_format

        resp = requests.post(
            f"{_OLLAMA_URL}/api/generate",
            json=payload,
            timeout=(5, _OLLAMA_TIMEOUT_S),
        )
        resp.raise_for_status()
        data = resp.json()
        return (data.get("response") or "").strip()
    except requests.Timeout:
        return (
            "[ERROR] Ollama request timed out. The model might be too slow or not responding. "
            "Try a smaller/faster model or increase OLLAMA_TIMEOUT_S in .env"
        )
    except requests.ConnectionError:
        return (
            "[ERROR] Cannot connect to Ollama server. "
            "Make sure Ollama is running: 'ollama serve' "
            f"Expected at: {_OLLAMA_URL}"
        )
    except requests.RequestException as exc:
        return f"[ERROR] Ollama request failed: {exc}"


def generate_text(prompt: str, temperature: float = 0.7) -> str:
    """
    Simple wrapper around local Ollama text generation.
    """
    return _ollama_generate(prompt, temperature=temperature)


def generate_json(prompt: str, temperature: float = 0.3) -> dict:
    """
    Ask Ollama to return a JSON object. We still parse from text to be robust.

    On errors, return a safe default JSON structure so downstream code
    (like the SalesManagerAgent) can continue to run.
    """
    raw = _ollama_generate(prompt, temperature=temperature, response_format="json")

    def _try_parse(text: str) -> dict | None:
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    # 1) direct parse
    parsed = _try_parse(raw)
    if parsed is not None:
        return parsed

    # 2) strip common code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
        parsed = _try_parse(cleaned)
        if parsed is not None:
            return parsed

    # 3) extract first {...} block
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = raw[start : end + 1]
        parsed = _try_parse(candidate)
        if parsed is not None:
            return parsed

    # Fallback – return raw text wrapped
    return {"_raw": raw}
