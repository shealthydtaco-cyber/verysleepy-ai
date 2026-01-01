# brain.py

import requests
from config import OLLAMA_URL, BRAIN_MODEL

def think(user_text, extra_context="", max_tokens=120):
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    prompt = f"""
{system_prompt}

Context:
{extra_context}

User:
{user_text}
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": BRAIN_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.6,
                "num_ctx": 2048,
                "num_predict": max_tokens,
                "top_p": 0.9
            }
        }
    )

    return response.json()["response"]
