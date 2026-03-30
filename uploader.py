"""
uploader.py
Uploads to YouTube Shorts (Service Account), Instagram Reels, and Rumble
"""

import os
import json
import time
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from instagrapi import Client as InstaClient

# ── YouTube (Service Account) ────────────────────────────────────────────────

YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_client():
    """Build YouTube client using Service Account JSON from env"""
    sa_json = os.environ.get("YOUTUBE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise RuntimeError("YOUTUBE_SERVICE_ACCOUNT_JSON secret not set")

    sa_info = json.loads(sa_json)
    credentials = service_account.Credentials.from_service_account_info(
        sa_info, scopes=YT_SCOPES
    )
    return build("youtube", "v3", credentials=credentials)


def upload_to_youtube(video_path: str, title: str, description: str, hashtags: str) -> str:
    print("📤 Uploading to YouTube Shorts...")

    youtube = get_youtube_client()

    full_title       = f"{title} #Shorts"[:100]
    full_description = f"{description}\n\n{hashtags}\n\n#Shorts"

    body = {
        "snippet": {
            "title": full_title,
            "description": full_description,
            "tags": [t.replace("#", "") for t in hashtags.split()],
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media   = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload: {int(status.progress() * 100)}%")

    url = f"https://www.youtube.com/shorts/{response['id']}"
    print(f"  ✅ YouTube: {url}")
    return url


# ── Instagram ────────────────────────────────────────────────────────────────

def upload_to_instagram(video_path: str, description: str, hashtags: str) -> str:
    print("📤 Uploading to Instagram Reels...")

    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    if not username or not password:
        raise RuntimeError("INSTAGRAM_USERNAME / INSTAGRAM_PASSWORD not set")

    cl           = InstaClient()
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


# ── Rumble ───────────────────────────────────────────────────────────────────

def upload_to_rumble(video_path: str, title: str, description: str, hashtags: str) -> str:
    print("📤 Uploading to Rumble...")

    api_key  = os.environ.get("RUMBLE_API_KEY")
    username = os.environ.get("RUMBLE_USERNAME")
    if not api_key or not username:
        raise RuntimeError("RUMBLE_API_KEY / RUMBLE_USERNAME not set")

    full_description = f"{description}\n\n{hashtags}"
    tags = hashtags.replace("#", "").replace("  ", " ").strip()

    with open(video_path, "rb") as vf:
        resp = requests.post(
            "https://rumble.com/-upload-video.json",
            data={
                "api_key":     api_key,
                "title":       title[:80],
                "description": full_description[:2000],
                "tags":        tags[:200],
                "channel_id":  username,
                "visibility":  "public",
                "type":        "short",
            },
            files={"video": vf},
            timeout=300,
        )

    resp.raise_for_status()
    data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"Rumble upload failed: {data}")

    video_id = data.get("video_id") or data.get("id")
    url      = data.get("url") or f"https://rumble.com/v{video_id}.html"
    print(f"  ✅ Rumble: {url}")
    return url


# ── Upload All ───────────────────────────────────────────────────────────────

def upload_all(video_path: str, title: str, description: str, hashtags: str) -> dict:
    results = {}

    for name, fn, args in [
        ("youtube",   upload_to_youtube,   (video_path, title, description, hashtags)),
        ("instagram", upload_to_instagram, (video_path, description, hashtags)),
        ("rumble",    upload_to_rumble,    (video_path, title, description, hashtags)),
    ]:
        try:
            results[name] = fn(*args)
        except Exception as e:
            print(f"  ⚠️  {name.capitalize()} upload failed: {e}")
            results[name] = None
        time.sleep(3)

    return results
