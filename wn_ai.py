"""Wordnest - one place for all AI calls.

Order of providers:
  1. Google Gemini   (cloud; set GEMINI_API_KEY)
  2. Ollama          (your own computer; set OLLAMA_URL, e.g. http://localhost:11434, and OLLAMA_MODEL)
If neither answers, callers fall back to simple rule-based checks, so the site never breaks.
"""
import base64
import json

import requests

from wn_auth import secret


def providers():
    out = []
    if secret("GEMINI_API_KEY"):
        out.append("gemini")
    if secret("OLLAMA_URL"):
        out.append("ollama")
    return out


def status_text():
    p = providers()
    if not p:
        return "AI: off (rule checks only). Add GEMINI_API_KEY or OLLAMA_URL in secrets."
    names = {"gemini": "Gemini", "ollama": f"Ollama ({secret('OLLAMA_MODEL', 'qwen2.5:7b')})"}
    return "AI: ON · " + " → ".join(names[x] for x in p)


def _gemini(system, prompt, audio=None):
    key = secret("GEMINI_API_KEY")
    model = secret("GEMINI_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash"
    parts = [{"text": prompt}]
    if audio:
        data, mime = audio
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}})
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                      headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=60)
    data = r.json()
    if r.status_code != 200:
        msg = (data.get("error") or {}).get("message", f"HTTP {r.status_code}") if isinstance(data, dict) else r.status_code
        raise RuntimeError(f"Gemini: {str(msg)[:160]}")
    cand = (data.get("candidates") or [{}])[0]
    if (data.get("promptFeedback") or {}).get("blockReason") or cand.get("finishReason") in (
            "SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST"):
        return {"_safety_block": True}
    return json.loads(cand["content"]["parts"][0]["text"])


def _ollama(system, prompt):
    url = secret("OLLAMA_URL").rstrip("/")
    model = secret("OLLAMA_MODEL", "qwen2.5:7b") or "qwen2.5:7b"
    r = requests.post(f"{url}/api/chat", timeout=180, json={
        "model": model, "stream": False, "format": "json", "options": {"temperature": 0},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
    if r.status_code != 200:
        raise RuntimeError(f"Ollama: HTTP {r.status_code} {r.text[:120]}")
    return json.loads(r.json()["message"]["content"])


def generate_json(system, prompt, audio=None):
    """Ask the first working AI for a JSON answer. Returns (dict or None, engine name, list of errors)."""
    errors = []
    for p in providers():
        if audio and p != "gemini":
            continue  # only Gemini can listen to audio
        try:
            out = _gemini(system, prompt, audio) if p == "gemini" else _ollama(system, prompt)
            if isinstance(out, dict):
                return out, p, errors
            errors.append(f"{p}: unexpected answer")
        except Exception as e:  # network, quota, bad JSON
            errors.append(str(e)[:200] if str(e) else f"{p}: {type(e).__name__}")
    return None, None, errors


def transcribe(audio_bytes, mime="audio/wav"):
    """Turn a recorded voice answer into text (Gemini only). Returns text or None."""
    out, _, _ = generate_json("You transcribe interview answers. Return JSON {\"text\": \"...\"} with the exact words spoken, "
                              "in the language spoken. Do not add anything.",
                              "Transcribe this recording.", audio=(audio_bytes, mime))
    if out and not out.get("_safety_block"):
        return str(out.get("text", "")).strip() or None
    return None
