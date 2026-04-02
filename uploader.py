"""
uploader.py
Sends video metadata + direct URL to Make.com webhook.
Make.com downloads the video itself via HTTP module, then uploads to YouTube + Instagram.
"""

import os
import requests


def get_direct_video_url(video_path: str) -> str:
    """Upload video to catbox.moe — free, fast, works on GitHub Actions."""
    print("  ☁️  Uploading video to catbox.moe...")

    with open(video_path, "rb") as vf:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": ("final_short.mp4", vf, "video/mp4")},
            timeout=180,
        )

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"catbox.moe upload failed [{resp.status_code}]: {resp.text[:200]}")

    direct_url = resp.text.strip()
    if not direct_url.startswith("http"):
        raise RuntimeError(f"catbox.moe unexpected response: {direct_url[:200]}")

    print(f"  ✅ Direct video URL ready: {direct_url}")
    return direct_url


def upload_all(video_path: str, title: str, description: str, hashtags: str) -> dict:

    webhook_url = os.environ.get("MAKE_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("MAKE_WEBHOOK_URL secret not set")

    # Upload video to catbox first — Make will download it from there
    direct_video_url = get_direct_video_url(video_path)

    print("📡 Sending metadata to Make.com (YouTube + Instagram)...")

    # Send ONLY metadata + URL — no binary file attachment (avoids 413)
    resp = requests.post(
        webhook_url,
        json={
            "title":       title[:100],
            "description": description[:500],
            "hashtags":    hashtags,
            "video_url":   direct_video_url,
        },
        timeout=60,
    )

    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Make.com error {resp.status_code}: {resp.text[:200]}")

    print("  ✅ Metadata sent to Make.com successfully!")
    print("  📺 YouTube uploading...")
    print("  📸 Instagram uploading...")

    return {
        "youtube":   "⏳ Processing via Make.com",
        "instagram": "⏳ Processing via Make.com",
    }
