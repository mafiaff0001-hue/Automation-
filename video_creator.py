"""
video_creator.py
Downloads free Pexels stock video and assembles vertical Short using FFmpeg.
Fixes: special character escaping, minimum 30s duration with video looping.
"""

import os
import re
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
SHORT_W, SHORT_H = 1080, 1920
MIN_DURATION = 30.0  # minimum 30 seconds


def download_pexels_video(query: str, output_path: str) -> str:
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {"query": query, "per_page": 15, "orientation": "portrait"}

    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers, params=params, timeout=15
    )
    r.raise_for_status()
    videos = r.json().get("videos", [])

    # Filter videos that are at least 15 seconds long
    long_videos = [v for v in videos if v.get("duration", 0) >= 15]
    video = random.choice(long_videos) if long_videos else random.choice(videos)

    video_files = sorted(video["video_files"], key=lambda x: x.get("width", 0), reverse=True)
    video_url = video_files[0]["link"]

    print(f"  📥 Downloading stock video ({video.get('duration', '?')}s)...")
    dl = requests.get(video_url, timeout=120, stream=True)
    with open(output_path, "wb") as f:
        for chunk in dl.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  ✅ Stock video saved")
    return output_path


def get_duration(path: str) -> float:
    """Get duration of a media file using ffprobe"""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(probe.stdout.strip())
    except Exception:
        return 0.0


def clean_caption(text: str) -> str:
    """Safely escape text for FFmpeg drawtext filter"""
    # Remove stage directions
    text = re.sub(r"\[.*?\]", " ", text)
    # Remove all special characters that break FFmpeg
    text = re.sub(r"[\\':=\[\]{}|<>]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Limit length
    return text[:120]


def create_video(script: str, voiceover_path: str, title: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    query        = random.choice(VIDEO_QUERIES)
    raw_path     = f"{OUTPUT_DIR}/raw_bg.mp4"
    looped_path  = f"{OUTPUT_DIR}/looped_bg.mp4"
    resized_path = f"{OUTPUT_DIR}/resized_bg.mp4"
    captioned_path = f"{OUTPUT_DIR}/captioned.mp4"
    final_path   = f"{OUTPUT_DIR}/final_short.mp4"

    print(f"🎬 Downloading background video ({query})...")
    download_pexels_video(query, raw_path)

    # Get voiceover duration — target at least 30s
    vo_duration = get_duration(voiceover_path)
    target_duration = max(vo_duration + 1.5, MIN_DURATION)
    print(f"✂️  Target duration: {target_duration:.1f}s")

    # Loop video if shorter than target duration
    bg_duration = get_duration(raw_path)
    if bg_duration < target_duration:
        loops = int(target_duration / bg_duration) + 2
        print(f"🔁 Looping background video {loops}x to reach {target_duration:.1f}s...")
        loop_cmd = [
            "ffmpeg", "-y",
            "-stream_loop", str(loops),
            "-i", raw_path,
            "-t", str(target_duration),
            "-c", "copy",
            looped_path,
        ]
        subprocess.run(loop_cmd, check=True, capture_output=True)
        source_path = looped_path
    else:
        source_path = raw_path

    # Resize to vertical 1080x1920
    print(f"📐 Resizing to vertical format...")
    subprocess.run([
        "ffmpeg", "-y", "-i", source_path,
        "-t", str(target_duration),
        "-vf", (
            f"scale={SHORT_W}:{SHORT_H}:force_original_aspect_ratio=increase,"
            f"crop={SHORT_W}:{SHORT_H}"
        ),
        "-c:v", "libx264", "-preset", "fast", "-an",
        resized_path,
    ], check=True, capture_output=True)

    # Add captions safely
    print("📝 Adding captions...")
    caption_text = clean_caption(script)
    filter_str = (
        f"drawtext=text='{caption_text}':"
        f"fontcolor=white:fontsize=46:"
        f"x=(w-text_w)/2:y=h-280:"
        f"borderw=4:bordercolor=black:"
        f"fix_bounds=true:line_spacing=8"
    )
    subprocess.run([
        "ffmpeg", "-y", "-i", resized_path,
        "-vf", filter_str,
        "-c:a", "copy",
        captioned_path,
    ], check=True, capture_output=True)

    # Merge voiceover — pad audio/video to match durations
    print("🔊 Merging voiceover...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", captioned_path,
        "-i", voiceover_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        final_path,
    ], check=True, capture_output=True)

    final_dur = get_duration(final_path)
    print(f"✅ Final video: {final_path} ({final_dur:.1f}s)")
    return final_path
