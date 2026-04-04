"""
video_creator.py
Downloads topic-matched Pexels stock video and assembles vertical Short.
Background video matches the script topic. Guaranteed 45s output.
"""

import os
import re
import random
import requests
import subprocess

PEXELS_API_KEY   = os.environ.get("PEXELS_API_KEY")
OUTPUT_DIR       = "output"
SHORT_W, SHORT_H = 1080, 1920
TAIL_PADDING     = 1.0   # seconds of silence added after voiceover ends

# Fallback queries if topic queries not provided
DEFAULT_QUERIES = [
    "nature amazing", "space universe stars", "science lab",
    "ocean underwater", "animals wildlife", "technology futuristic",
]


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr[-800:]}")
    return result


def get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def download_pexels_video(queries: list, output_path: str) -> str:
    """Try each query until a good video is found."""
    headers = {"Authorization": PEXELS_API_KEY}

    for query in queries:
        try:
            params = {"query": query, "per_page": 15, "orientation": "portrait"}
            r = requests.get("https://api.pexels.com/videos/search",
                             headers=headers, params=params, timeout=15)
            r.raise_for_status()
            videos = r.json().get("videos", [])
            if not videos:
                continue

            long_videos = [v for v in videos if v.get("duration", 0) >= 20]
            video = random.choice(long_videos) if long_videos else random.choice(videos)
            video_files = sorted(video["video_files"],
                                 key=lambda x: x.get("width", 0), reverse=True)
            video_url = video_files[0]["link"]

            print(f"  📥 Downloading stock video for '{query}' ({video.get('duration', '?')}s)...")
            dl = requests.get(video_url, timeout=120, stream=True)
            with open(output_path, "wb") as f:
                for chunk in dl.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  ✅ Stock video saved")
            return output_path
        except Exception as e:
            print(f"  ⚠️  Query '{query}' failed: {e}, trying next...")
            continue

    raise RuntimeError("All video queries failed")


def split_into_chunks(script: str, words_per_chunk: int = 4) -> list:
    text = re.sub(r"\[.*?\]", " ", script)
    text = re.sub(r"[\\':=\[\]{}|<>\"#@&*^%$!]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    return [" ".join(words[i:i+words_per_chunk])
            for i in range(0, len(words), words_per_chunk)]


def build_caption_filter(chunks: list, vo_duration: float) -> str:
    if not chunks:
        return "null"
    time_per_chunk = vo_duration / len(chunks)
    filters = []
    for i, chunk in enumerate(chunks):
        start = i * time_per_chunk
        end   = start + time_per_chunk
        safe  = re.sub(r"[^a-zA-Z0-9 .,!?;]", "", chunk).strip()
        if not safe:
            continue
        filters.append(
            f"drawtext=text='{safe}':"
            f"fontsize=72:fontcolor=white:"
            f"borderw=5:bordercolor=black:"
            f"x=(w-text_w)/2:y=(h*3/4):"
            f"enable='between(t,{start:.2f},{end:.2f})'"
        )
    return ",".join(filters) if filters else "null"


def create_video(script: str, voiceover_path: str, title: str,
                 video_queries: list = None) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Use topic-matched queries from script_generator, fallback to defaults
    queries = video_queries if video_queries else DEFAULT_QUERIES

    raw_path       = f"{OUTPUT_DIR}/raw_bg.mp4"
    looped_path    = f"{OUTPUT_DIR}/looped_bg.mp4"
    resized_path   = f"{OUTPUT_DIR}/resized_bg.mp4"
    captioned_path = f"{OUTPUT_DIR}/captioned.mp4"
    padded_audio   = f"{OUTPUT_DIR}/audio_padded.aac"
    final_path     = f"{OUTPUT_DIR}/final_short.mp4"

    print(f"🎬 Downloading topic-matched background video...")
    download_pexels_video(queries, raw_path)

    vo_duration = get_duration(voiceover_path)
    # Dynamic duration = actual voiceover length + short tail padding
    target_duration = round(vo_duration + TAIL_PADDING, 2)
    print(f"✂️  Voiceover: {vo_duration:.1f}s → Video duration: {target_duration:.1f}s")

    # Step 1: Pad voiceover by TAIL_PADDING seconds of silence
    run([
        "ffmpeg", "-y",
        "-i", voiceover_path,
        "-af", f"apad=pad_dur={TAIL_PADDING}",
        "-t", str(target_duration),
        "-c:a", "aac", "-b:a", "192k",
        padded_audio,
    ])
    print(f"  ✅ Audio padded to {get_duration(padded_audio):.1f}s")

    # Step 2: Loop background to target_duration
    bg_dur = get_duration(raw_path)
    if bg_dur < target_duration:
        loops = int(target_duration / bg_dur) + 2
        print(f"🔁 Looping background {loops}x...")
        run([
            "ffmpeg", "-y",
            "-stream_loop", str(loops),
            "-i", raw_path,
            "-t", str(target_duration),
            "-c", "copy",
            looped_path,
        ])
        source_path = looped_path
    else:
        source_path = raw_path

    # Step 3: Resize to 1080x1920
    print("📐 Resizing to vertical format...")
    run([
        "ffmpeg", "-y", "-i", source_path,
        "-t", str(target_duration),
        "-vf", (
            f"scale={SHORT_W}:{SHORT_H}:force_original_aspect_ratio=increase,"
            f"crop={SHORT_W}:{SHORT_H}"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an",
        resized_path,
    ])

    # Step 4: Burn in captions (synced to full voiceover duration)
    print("📝 Adding captions...")
    chunks = split_into_chunks(script, words_per_chunk=4)
    caption_filter = build_caption_filter(chunks, vo_duration)
    run([
        "ffmpeg", "-y", "-i", resized_path,
        "-vf", caption_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        captioned_path,
    ])

    # Step 5: Merge video + audio, both locked to target_duration
    print("🔊 Merging voiceover...")
    run([
        "ffmpeg", "-y",
        "-i", captioned_path,
        "-i", padded_audio,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "copy",
        "-t", str(target_duration),
        final_path,
    ])

    final_dur = get_duration(final_path)
    print(f"✅ Final video: {final_path} ({final_dur:.1f}s)")
    return final_path
