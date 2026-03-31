"""
uploader.py
Sends video + metadata to Make.com webhook.
Make.com handles YouTube + Instagram uploads permanently.
"""

import os
import requests


def upload_all(video_path: str, title: str, description: str, hashtags: str) -> dict:

    webhook_url = os.environ.get("MAKE_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("MAKE_WEBHOOK_URL secret not set")

    print("📡 Sending video to Make.com (YouTube + Instagram)...")

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

    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Make.com error {resp.status_code}: {resp.text[:200]}")

    print("  ✅ Video sent to Make.com successfully!")
    print("  📺 YouTube uploading...")
    print("  📸 Instagram uploading...")

    return {
        "youtube":   "⏳ Processing via Make.com",
        "instagram": "⏳ Processing via Make.com",
    }
