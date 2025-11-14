# groq_client.py
import requests
from django.conf import settings

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = "llama-3.1-8b-instant"
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

def groq_generate(prompt):
    """Send a prompt to Groq API and return text output."""
    response = requests.post(
        BASE_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
    )

    if response.status_code != 200:
        raise Exception(f"Groq Error: {response.text}")

    return response.json()["choices"][0]["message"]["content"]


