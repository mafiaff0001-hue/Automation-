"""
uploader.py
- YouTube: via n8n webhook (secure, permanent)
- Instagram: via instagrapi with session caching (no repeated logins)
"""

import os
import time
import requests
from instagrapi import Client as InstaClient


# ── YouTube via n8n ───────────────────────────────────────────────────────────

def upload_to_youtube_via_n8n(video_path: str, title: str, description: str, hashtags: str) -> str:
    webhook_url = os.environ.get("N8N_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("N8N_WEBHOOK_URL secret not set")

    print("📡 Sending video to n8n for YouTube upload...")

    with open(video_path, "rb") as vf:
        resp = requests.post(
            webhook_url,
            data={
                "title":       title[:100],
                "description": description[:500],
                "hashtags":    hashtags,
            },
            files={"video": ("final_short.mp4", vf, "video/mp4")},
            timeout=300,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"n8n webhook error {resp.status_code}: {resp.text[:200]}")

    result = resp.json()
    url = result.get("youtube", "uploaded")
    print(f"  ✅ YouTube: {url}")
    return url


# ── Instagram via instagrapi ──────────────────────────────────────────────────

def upload_to_instagram(video_path: str, description: str, hashtags: str) -> str:
    print("📤 Uploading to Instagram Reels...")

    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    if not username or not password:
        raise RuntimeError("INSTAGRAM credentials not set")

    cl = InstaClient()
    cl.delay_range = [3, 7]  # human-like delays

    session_file = "ig_session.json"

    # Try cached session first to avoid repeated logins
    logged_in = False
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.login(username, password)
            logged_in = True
            print("  📱 Used cached Instagram session")
        except Exception:
            logged_in = False

    # Fresh login if session failed
    if not logged_in:
        try:
            cl.login(username, password)
            cl.dump_settings(session_file)
            print("  📱 Fresh Instagram login successful")
        except Exception as e:
            raise RuntimeError(f"Instagram login failed: {e}")

    caption = f"{description}\n\n{hashtags}"
    media   = cl.clip_upload(video_path, caption=caption)
    url     = f"https://www.instagram.com/reel/{media.code}/"
    print(f"  ✅ Instagram: {url}")

    # Save updated session for next run
    cl.dump_settings(session_file)
    return url


# ── Upload All ────────────────────────────────────────────────────────────────

def upload_all(video_path: str, title: str, description: str, hashtags: str) -> dict:
    results = {}

    # YouTube via n8n
    try:
        results["youtube"] = upload_to_youtube_via_n8n(
            video_path, title, description, hashtags
        )
    except Exception as e:
        print(f"  ⚠️  YouTube failed: {e}")
        results["youtube"] = None

    time.sleep(3)

    # Instagram direct
    try:
        results["instagram"] = upload_to_instagram(
            video_path, description, hashtags
        )
    except Exception as e:
        print(f"  ⚠️  Instagram failed: {e}")
        results["instagram"] = None

    return results
