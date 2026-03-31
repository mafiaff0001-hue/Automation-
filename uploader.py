"""
uploader.py
- Sends video to n8n webhook → YouTube only
- Uploads directly to Instagram from GitHub Actions
"""

import os
import time
import requests
from instagrapi import Client as InstaClient


# ── n8n Webhook (YouTube) ─────────────────────────────────────────────────────

def trigger_n8n(video_path: str, title: str, description: str, hashtags: str) -> dict:
    """Send video file to n8n — n8n uploads to YouTube"""

    webhook_url = os.environ.get("N8N_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("N8N_WEBHOOK_URL secret not set")

    print("📡 Sending video to n8n (YouTube)...")

    with open(video_path, "rb") as vf:
        resp = requests.post(
            webhook_url,
            data={
                "title":       title,
                "description": description,
                "hashtags":    hashtags,
            },
            files={"video": ("final_short.mp4", vf, "video/mp4")},
            timeout=300,
        )

    resp.raise_for_status()
    result = resp.json()
    print(f"  ✅ YouTube: {result.get('youtube', 'processing...')}")
    return result


# ── Instagram (direct from GitHub Actions) ───────────────────────────────────

def upload_to_instagram(video_path: str, description: str, hashtags: str) -> str:
    """Upload directly to Instagram Reels"""
    print("📤 Uploading to Instagram Reels...")

    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    if not username or not password:
        raise RuntimeError("INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD not set")

    cl = InstaClient()
    cl.delay_range = [2, 5]

    session_file = "ig_session.json"
    try:
        if os.path.exists(session_file):
            cl.load_settings(session_file)
        cl.login(username, password)
        cl.dump_settings(session_file)
    except Exception as e:
        raise RuntimeError(f"Instagram login failed: {e}")

    caption = f"{description}\n\n{hashtags}"
    media   = cl.clip_upload(video_path, caption=caption)
    url     = f"https://www.instagram.com/reel/{media.code}/"
    print(f"  ✅ Instagram: {url}")
    return url


# ── Upload All ────────────────────────────────────────────────────────────────

def upload_all(video_path: str, title: str, description: str, hashtags: str) -> dict:
    results = {}

    # YouTube via n8n
    try:
        n8n_result = trigger_n8n(video_path, title, description, hashtags)
        results["youtube"] = n8n_result.get("youtube")
    except Exception as e:
        print(f"  ⚠️  n8n (YouTube) failed: {e}")
        results["youtube"] = None

    time.sleep(3)

    # Instagram directly
    try:
        results["instagram"] = upload_to_instagram(video_path, description, hashtags)
    except Exception as e:
        print(f"  ⚠️  Instagram failed: {e}")
        results["instagram"] = None

    return results
    
