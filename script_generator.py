"""
script_generator.py
Generates Facts & Trivia video script using Groq (free Llama 3)
"""

import os
import json
import requests
import random

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

TOPICS = [
    "a mind-blowing science fact",
    "a weird historical fact",
    "a surprising animal fact",
    "an unbelievable space fact",
    "a strange psychological fact",
    "a fascinating food fact",
    "an incredible human body fact",
    "a surprising technology fact",
    "a bizarre world record fact",
    "an amazing ocean deep sea fact",
]


def generate_script() -> dict:
    topic = random.choice(TOPICS)

    prompt = f"""You are a viral YouTube Shorts and TikTok script writer.

Write a 45-60 second script about: {topic}

Rules:
- Start with a HOOK (first 3 seconds must grab attention, e.g. "Did you know...")
- Keep sentences SHORT and punchy
- Add [PAUSE] markers between sentences for natural pacing
- End with: "Follow for more amazing facts!"
- Total script: 80-120 words max

Respond ONLY in this exact JSON format (no markdown, no backticks):
{{
  "title": "catchy title under 60 chars",
  "script": "full script with [PAUSE] markers",
  "hashtags": "#Facts #DidYouKnow #Shorts #Trivia #LearnSomethingNew #Viral #FYP #Amazing #MindBlown #Knowledge",
  "description": "one line description under 100 chars"
}}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 600,
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"].strip()
    # Strip markdown fences if present
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    data = json.loads(content)
    print(f"✅ Script generated: {data['title']}")
    return data


if __name__ == "__main__":
    result = generate_script()
    print(json.dumps(result, indent=2))
