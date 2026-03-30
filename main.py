"""
main.py
Full pipeline: Script → Voiceover → Video → Upload to all platforms
"""

import json
import os
import traceback
from datetime import datetime

from script_generator import generate_script
from voiceover import generate_voiceover
from video_creator import create_video
from uploader import upload_all

LOG_FILE = "output/run_log.json"


def log_run(data: dict):
    os.makedirs("output", exist_ok=True)
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            try:
                logs = json.load(f)
            except Exception:
                logs = []
    logs.append(data)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def run():
    print("\n" + "=" * 55)
    print("🚀  SHORTS AGENT — Pipeline Starting")
    print(f"⏰   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")
    print("=" * 55 + "\n")

    run_data = {"timestamp": datetime.now().isoformat(), "status": "failed"}

    try:
        # Step 1 — Generate script
        print("📝 Step 1/4: Generating script...")
        script_data = generate_script()
        run_data["title"] = script_data["title"]
        print(f"   Title  : {script_data['title']}")
        print(f"   Script : {script_data['script'][:80]}...\n")

        # Step 2 — Voiceover
        print("🎙️  Step 2/4: Generating voiceover...")
        voiceover_path = generate_voiceover(
            script_data["script"], output_path="output/voiceover.mp3"
        )
        print()

        # Step 3 — Video
        print("🎬 Step 3/4: Creating video...")
        video_path = create_video(
            script=script_data["script"],
            voiceover_path=voiceover_path,
            title=script_data["title"],
        )
        print()

        # Step 4 — Upload
        print("☁️  Step 4/4: Uploading to all platforms...")
        results = upload_all(
            video_path=video_path,
            title=script_data["title"],
            description=script_data["description"],
            hashtags=script_data["hashtags"],
        )

        run_data["status"]  = "success"
        run_data["uploads"] = results

        print("\n" + "=" * 55)
        print("✅  PIPELINE COMPLETE!")
        for platform, url in results.items():
            icon = {"youtube": "📺", "instagram": "📸", "rumble": "📹"}.get(platform, "🔗")
            status = url if url else "❌ Failed"
            print(f"   {icon}  {platform.capitalize():12} {status}")
        print("=" * 55 + "\n")

    except Exception as e:
        run_data["error"]     = str(e)
        run_data["traceback"] = traceback.format_exc()
        print(f"\n❌ Pipeline failed: {e}")
        traceback.print_exc()

    finally:
        log_run(run_data)

    return run_data


if __name__ == "__main__":
    run()
