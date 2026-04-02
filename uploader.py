"""
uploader.py
Sends video + metadata to Make.com webhook.
Make.com handles YouTube + Instagram uploads permanently.
"""

import os
import requests


def get_direct_video_url(video_path: str) -> str:
    """Upload video to 0x0.st — works on GitHub Actions, returns direct MP4 URL."""
    print("  ☁️  Getting direct video URL for Instagram...")

    with open(video_path, "rb") as vf:
        resp = requests.post(
            "https://0x0.st",
            files={"file": ("final_short.mp4", vf, "video/mp4")},
            data={"expires": "24"},
            timeout=180,
        )

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"0x0.st upload failed [{resp.status_code}]: {resp.text[:200]}")

    direct_url = resp.text.strip()
    if not direct_url.startswith("http"):
        raise RuntimeError(f"0x0.st unexpected response: {direct_url[:200]}")

    return direct_url


def upload_all(video_path: str, title: str, description: str, hashtags: str) -> dict:

    webhook_url = os.environ.get("MAKE_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("MAKE_WEBHOOK_URL secret not set")

    # Get a public direct URL so Instagram can download the video
    direct_video_url = get_direct_video_url(video_path)
    print(f"  ✅ Direct video URL ready: {direct_video_url}")

    print("📡 Sending video to Make.com (YouTube + Instagram)...")

    with open(video_path, "rb") as vf:
        resp = requests.post(
            webhook_url,
            data={
                "title":       title[:100],
                "description": description[:500],
                "hashtags":    hashtags,
                "video_url":   direct_video_url,
            },
            files={"video": ("final_short.mp4", vf, "video/mp4")},
            timeout=300,
        )

    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Make.com error {resp.status_code}: {resp.text[:200]}")

    print("  ✅ Video sent to Make.com successfully!")
    print("  📺 YouTube uploading...")
    print("  📸 Instagram uploading...")

    return {
        "youtube":   "⏳ Processing via Make.com",
        "instagram": "⏳ Processing via Make.com",
    }
