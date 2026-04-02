"""
script_generator.py
Generates Facts & Trivia video script using Groq (free Llama 3).
Returns topic keywords so video background matches the script.
"""

import os
import re
import json
import requests
import random

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

TOPICS = [
    ("a mind-blowing science fact", ["science lab", "experiment chemistry", "physics quantum"]),
    ("a weird historical fact", ["ancient history", "medieval castle", "roman empire"]),
    ("a surprising animal fact", ["animals wildlife", "exotic animals", "jungle nature"]),
    ("an unbelievable space fact", ["space universe stars", "galaxy nebula", "planets solar system"]),
    ("a strange psychological fact", ["human brain mind", "psychology meditation", "neurons thinking"]),
    ("a fascinating food fact", ["food cooking kitchen", "exotic fruit market", "chef restaurant"]),
    ("an incredible human body fact", ["human body anatomy", "heartbeat pulse", "DNA biology"]),
    ("a surprising technology fact", ["technology futuristic", "computer circuit", "robot AI"]),
    ("a bizarre world record fact", ["world record crowd", "stadium people", "extreme sport"]),
    ("an amazing ocean deep sea fact", ["ocean underwater", "deep sea creatures", "coral reef fish"]),
]


def sanitize_json_string(raw: str) -> str:
    """Remove control characters that break JSON parsing."""
    # Strip markdown fences
    if "```" in raw:
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]

    # Remove all control characters except normal whitespace
    raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)

    # Replace literal newlines/tabs INSIDE JSON string values with a space
    # We do this by collapsing any whitespace between quotes
    raw = raw.strip()
    return raw


def generate_script(attempt: int = 0) -> dict:
    if attempt > 3:
        raise RuntimeError("Failed to generate valid script after 3 attempts")

    topic, video_queries = random.choice(TOPICS)

    prompt = (
        "You are a viral YouTube Shorts script writer.\n\n"
        f"Write a script about: {topic}\n\n"
        "REQUIREMENTS:\n"
        "- Exactly 150-170 words\n"
        "- Start with a hook: 'Most people don't know that...' or 'What if I told you...'\n"
        "- Short punchy sentences, max 10 words each\n"
        "- Add [PAUSE] after every sentence\n"
        "- Give 3-4 interesting follow-up details\n"
        "- End with: Follow for more mind-blowing facts every day!\n"
        "- Sound like a passionate human storyteller\n\n"
        "CRITICAL: Respond ONLY with a single-line JSON object. "
        "No newlines inside string values. No markdown. No backticks. "
        "All text must be on one continuous line.\n\n"
        'Example format: {"title":"Title here","script":"Script text all on one line [PAUSE] more text [PAUSE]","video_queries":["query1","query2","query3"],"hashtags":"#Facts #Shorts","description":"Short description"}\n\n'
        f'Now write about: {topic}\n'
        f'Use these video search terms: {video_queries}'
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"].strip()
    cleaned = sanitize_json_string(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse failed (attempt {attempt+1}): {e}")
        print(f"   Raw response: {cleaned[:200]}")
        return generate_script(attempt + 1)

    # Validate word count
    word_count = len(data["script"].replace("[PAUSE]", "").split())
    print(f"✅ Script generated: {data['title']} ({word_count} words)")

    if word_count < 120:
        print(f"⚠️  Script too short ({word_count} words), regenerating...")
        return generate_script(attempt + 1)

    # Ensure video_queries exists
    if "video_queries" not in data or not data["video_queries"]:
        data["video_queries"] = video_queries

    return data


if __name__ == "__main__":
    result = generate_script()
    print(json.dumps(result, indent=2))
