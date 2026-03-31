"""
uploader.py
- YouTube + Instagram: via Activepieces webhook (permanent, free forever)
- Sends video file + metadata to Activepieces
- Activepieces handles uploading to all platforms
"""

import os
import time
import requests


def upload_all(video_path: str, title: str, description: str, hashtags: str) -> dict:
    """Send video to Activepieces webhook — it uploads to YouTube + Instagram"""

    webhook_url = os.environ.get("ACTIVEPIECES_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("ACTIVEPIECES_WEBHOOK_URL secret not set")

    print("📡 Sending video to Activepieces (YouTube + Instagram)...")

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
        raise RuntimeError(f"Activepieces webhook error {resp.status_code}: {resp.text[:200]}")

    print("  ✅ Video sent to Activepieces successfully!")
    print("  📺 YouTube — uploading via Activepieces...")
    print("  📸 Instagram — uploading via Activepieces...")

    return {
        "youtube":   "⏳ Processing via Activepieces",
        "instagram": "⏳ Processing via Activepieces",
    }
