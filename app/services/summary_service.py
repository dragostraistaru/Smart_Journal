import os
from datetime import date
from typing import List

import requests

from app.core.exceptions import ValidationError
from app.models.entry import Entry


def _build_prompt(entries: List[Entry], year: int, month: int) -> str:
    header = (
        f"You are an assistant that summarizes a user's journal entries for {year}-{month:02d}.\n"
        "Produce a concise, structured summary in Romanian with these sections:\n"
        "1) Temele principale (bullet points)\n2) Prezentare emotionala (short paragraph)\n3) Momente importante (bullet points)\n4) 2-3 sugestii practice.\n"
        "Use only the content from the entries, do not invent facts.\n\n"
    )

    body = "Entries:\n"
    for e in entries:
        body += f"- {e.entry_date.isoformat()} | {e.title}: {e.content}\n"

    footer = "\nGenerate the summary in Romanian. Keep it around 200-350 words."
    return header + body + footer


def generate_monthly_summary(entries: List[Entry], year: int, month: int) -> str:
    if len(entries) < 3:
        raise ValidationError("Sunt necesare cel puțin 3 intrări pentru a genera un rezumat.")

    prompt = _build_prompt(entries, year, month)

    ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    model = os.getenv("OLLAMA_MODEL", "llama2")

    payload = {"model": model, "prompt": prompt, "max_tokens": 1000}

    try:
        resp = requests.post(ollama_url, json=payload, timeout=60)
    except requests.RequestException as exc:
        raise RuntimeError(f"Eroare la conectarea la Ollama: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama error: {resp.status_code} {resp.text}")

    data = resp.json()
    # Ollama responses vary; try common keys
    text = None
    if isinstance(data, dict):
        text = data.get("response") or data.get("output") or data.get("text") or data.get("result")
        # sometimes wrapped
        if not text and "choices" in data:
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                text = first.get("text") or first.get("message") or first.get("output")

    if not text:
        # fallback to raw body
        text = resp.text

    return str(text)
