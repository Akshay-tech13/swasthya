"""Calls the Claude API. Returns None on ANY problem, so the demo never breaks."""
import os

import requests

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5-5"


def ask_ai(prompt):
    """ask_ai(prompt) -> str | None. Key comes from the AI_API_KEY environment variable."""
    key = os.environ.get("AI_API_KEY")
    if not key:
        return None
    try:
        resp = requests.post(
            API_URL,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": MODEL, "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]},
            timeout=8,
        )
        resp.raise_for_status()
        for block in resp.json().get("content", []):
            if block.get("type") == "text" and block.get("text"):
                return block["text"].strip()
        return None
    except Exception:
        return None


if __name__ == "__main__":
    print("Reply (None is OK if no key or no internet):", ask_ai("Say hello in 5 words."))
