"""
voiceover.py
Generates MP3 voiceover using Microsoft Edge-TTS (completely free).
Rate set to -10% so 150-170 word scripts hit 40-48 seconds.
"""

import asyncio
import re
import os
import edge_tts

VOICE = "en-US-AndrewNeural"


def clean_script(script: str) -> str:
    """Remove stage directions for TTS"""
    script = re.sub(r"\[.*?\]", ", ", script)
    script = re.sub(r"\s+", " ", script).strip()
    return script


async def _generate(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="-10%", pitch="+0Hz")
    await communicate.save(output_path)


def generate_voiceover(script: str, output_path: str = "output/voiceover.mp3") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    clean_text = clean_script(script)
    asyncio.run(_generate(clean_text, output_path))
    print(f"✅ Voiceover saved: {output_path}")
    return output_path


if __name__ == "__main__":
    test = "Most people don't know that honey never expires. [PAUSE] Archaeologists found 3000 year old honey in Egyptian tombs. [PAUSE] It was still perfectly edible. [PAUSE] Honey has natural antibacterial properties. [PAUSE] Its low moisture content prevents bacteria from growing. [PAUSE] Ancient Egyptians used it to preserve food and treat wounds. [PAUSE] Even today, hospitals use medical grade honey on wounds. [PAUSE] A single jar of honey can outlast entire civilizations. [PAUSE] Follow for more mind-blowing facts every day!"
    generate_voiceover(test)
