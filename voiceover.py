"""
voiceover.py
Generates MP3 voiceover using Microsoft Edge-TTS (completely free)
"""

import asyncio
import re
import os
import edge_tts

VOICE = "en-US-AndrewNeural"   # Energetic male voice
# VOICE = "en-US-AriaNeural"   # Clear female voice
# VOICE = "en-GB-RyanNeural"   # British male


def clean_script(script: str) -> str:
    """Remove stage directions for TTS"""
    script = re.sub(r"\[.*?\]", ", ", script)
    script = re.sub(r"\s+", " ", script).strip()
    return script


async def _generate(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="+10%", pitch="+0Hz")
    await communicate.save(output_path)


def generate_voiceover(script: str, output_path: str = "output/voiceover.mp3") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    clean_text = clean_script(script)
    asyncio.run(_generate(clean_text, output_path))
    print(f"✅ Voiceover saved: {output_path}")
    return output_path


if __name__ == "__main__":
    test = "Did you know honey never expires? [PAUSE] Archaeologists found 3000-year-old honey in Egyptian tombs and it was still perfectly edible! [PAUSE] Follow for more amazing facts!"
    generate_voiceover(test)
