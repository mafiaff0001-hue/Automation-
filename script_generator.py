"""
script_generator.py
Generates Facts & Trivia video script using Groq (free Llama 3).
Returns topic keywords so video background matches the script.
"""

import os
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


def generate_script() -> dict:
    topic, video_queries = random.choice(TOPICS)

    prompt = f"""You are a viral YouTube Shorts script writer creating mini-documentary style content.

Write a script about: {topic}

STRICT REQUIREMENTS:
- Exactly 150-170 words (this is non-negotiable — count carefully)
- Start with a powerful hook: "Most people don't know that..." or "What if I told you..." or "This will change how you see the world..."
- Tell it like a story — build suspense, give specific facts with numbers/dates/names
- Short punchy sentences — max 10 words each
- Add [PAUSE] after every sentence
- Give 3-4 interesting follow-up details to expand the story
- End with: "Follow for more mind-blowing facts every day!"
- Sound like a passionate human, not a robot

Respond ONLY in this exact JSON format, no markdown, no backticks:
{{
  "title": "catchy title under 60 chars",
  "script": "full 150-170 word script with [PAUSE] after every sentence",
  "video_queries": ["{video_queries[0]}", "{video_queries[1]}", "{video_queries[2]}"],
  "hashtags": "#Facts #DidYouKnow #Shorts #Trivia #LearnSomethingNew #Viral #FYP #Amazing #MindBlown #Knowledge",
  "description": "one line description under 100 chars"
}}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 1000,
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"].strip()
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    data = json.loads(content)

    # Validate word count — regenerate once if too short
    word_count = len(data["script"].replace("[PAUSE]", "").split())
    print(f"✅ Script generated: {data['title']} ({word_count} words)")

    if word_count < 120:
        print("⚠️  Script too short, regenerating...")
        return generate_script()

    return data


if __name__ == "__main__":
    result = generate_script()
    print(json.dumps(result, indent=2))
