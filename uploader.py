"""
uploader.py
Sends video + metadata to Make.com webhook.
Make.com handles YouTube + Instagram uploads permanently.
"""

import os
import requests


def get_direct_video_url(video_path: str) -> str:
    """Upload video to file.io to get a public direct-download URL for Instagram."""
    print("  ☁️  Getting direct video URL for Instagram...")
    with open(video_path, "rb") as vf:
        resp = requests.post(
            "https://file.io/?expires=1h",
            files={"file": ("final_short.mp4", vf, "video/mp4")},
            timeout=120,
        )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"file.io upload failed: {data}")
    return data["link"]


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
