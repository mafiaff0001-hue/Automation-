"""
video_creator.py
Downloads free Pexels stock video and assembles vertical Short using FFmpeg
"""

import os
import random
import requests
import subprocess

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

VIDEO_QUERIES = [
    "nature amazing",
    "space universe stars",
    "science lab",
    "ocean underwater",
    "animals wildlife",
    "technology futuristic",
    "earth aerial drone",
    "human brain mind",
    "ancient history",
    "deep sea creatures",
]

OUTPUT_DIR  = "output"
SHORT_W, SHORT_H = 1080, 1920   # Vertical 9:16


def download_pexels_video(query: str, output_path: str) -> str:
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {"query": query, "per_page": 10, "orientation": "portrait"}

    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers, params=params, timeout=15
    )
    r.raise_for_status()
    videos = r.json().get("videos", [])
    if not videos:
        raise ValueError(f"No Pexels videos for: {query}")

    video     = random.choice(videos)
    video_files = sorted(video["video_files"], key=lambda x: x.get("width", 0), reverse=True)
    video_url = video_files[0]["link"]

    print(f"  📥 Downloading stock video...")
    dl = requests.get(video_url, timeout=120, stream=True)
    with open(output_path, "wb") as f:
        for chunk in dl.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  ✅ Stock video saved: {output_path}")
    return output_path


def create_video(script: str, voiceover_path: str, title: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    query         = random.choice(VIDEO_QUERIES)
    raw_path      = f"{OUTPUT_DIR}/raw_bg.mp4"
    trimmed_path  = f"{OUTPUT_DIR}/trimmed_bg.mp4"
    captioned_path = f"{OUTPUT_DIR}/captioned.mp4"
    final_path    = f"{OUTPUT_DIR}/final_short.mp4"

    print(f"🎬 Downloading background video ({query})...")
    download_pexels_video(query, raw_path)

    # Get voiceover duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", voiceover_path],
        capture_output=True, text=True
    )
    duration = float(probe.stdout.strip()) + 1.5

    print(f"✂️  Trimming & resizing to {duration:.1f}s vertical...")
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_path,
        "-t", str(duration),
        "-vf", (
            f"scale={SHORT_W}:{SHORT_H}:force_original_aspect_ratio=increase,"
            f"crop={SHORT_W}:{SHORT_H}"
        ),
        "-c:v", "libx264", "-preset", "fast", "-an",
        trimmed_path,
    ], check=True, capture_output=True)

    print("📝 Adding captions...")
    clean = script.replace("[PAUSE]", "").replace("'", "\\'").replace(":", "\\:").strip()
    # Show caption in bottom third, white text with black border
    filter_str = (
        f"drawtext=text='{clean[:180]}':"
        f"fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-250:"
        f"borderw=4:bordercolor=black:font='Arial Bold':"
        f"fix_bounds=true:line_spacing=8"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", trimmed_path,
        "-vf", filter_str,
        "-c:a", "copy",
        captioned_path,
    ], check=True, capture_output=True)

    print("🔊 Merging voiceover...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", captioned_path,
        "-i", voiceover_path,
        "-c:v", "copy", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        final_path,
    ], check=True, capture_output=True)

    print(f"✅ Final video: {final_path}")
    return final_path
