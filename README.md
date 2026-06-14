# 🎬 AI Shorts Agent — Fully Automated Video Publisher

An end-to-end AI pipeline that **automatically generates, produces, and publishes** YouTube Shorts and Instagram Reels — twice daily — with zero manual intervention.

---

## 🚀 What It Does

Every day at **4:30 AM and 8:30 PM IST**, a GitHub Actions workflow:

1. **Generates a script** — Uses Groq (Llama 3.3 70B) to write a viral-style facts script with hook, body, and CTA
2. **Creates a voiceover** — Microsoft Edge-TTS converts the script to natural speech (MP3)
3. **Assembles the video** — Downloads topic-matched stock footage from Pexels API, resizes to 1080×1920 vertical format, burns in animated captions using FFmpeg
4. **Publishes automatically** — Uploads to catbox.moe for CDN hosting, then triggers a Make.com webhook that pushes the final video to YouTube and Instagram simultaneously

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| AI Script Generation | Groq API (Llama 3.3 70B) |
| Text-to-Speech | Microsoft Edge-TTS |
| Stock Video | Pexels API |
| Video Processing | FFmpeg (resize, loop, caption burn-in, audio merge) |
| File Hosting | catbox.moe |
| Automation Orchestration | Make.com (webhook → YouTube + Instagram upload) |
| CI/CD & Scheduling | GitHub Actions (cron: 2x daily) |
| Language | Python 3.11 |

---

## 🏗️ Architecture

```
GitHub Actions (cron trigger)
        │
        ▼
script_generator.py  ──►  Groq API (Llama 3.3)
        │                  Returns: title, script, hashtags, video_queries
        ▼
voiceover.py  ──►  Edge-TTS  ──►  output/voiceover.mp3
        │
        ▼
video_creator.py
    ├── Pexels API  ──►  topic-matched stock video
    ├── FFmpeg      ──►  resize to 1080×1920
    ├── FFmpeg      ──►  burn captions (synced to voiceover)
    └── FFmpeg      ──►  merge audio + video  ──►  final_short.mp4
        │
        ▼
uploader.py
    ├── catbox.moe  ──►  direct video URL
    └── Make.com webhook  ──►  YouTube + Instagram
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/ai-shorts-agent.git
cd ai-shorts-agent
pip install -r requirements.txt
```

### 2. Set GitHub Secrets
Go to `Settings → Secrets and variables → Actions` and add:

| Secret | Description |
|---|---|
| `GROQ_API_KEY` | Free API key from [console.groq.com](https://console.groq.com) |
| `PEXELS_API_KEY` | Free API key from [pexels.com/api](https://www.pexels.com/api/) |
| `MAKE_WEBHOOK_URL` | Your Make.com scenario webhook URL |

### 3. Run manually
```bash
python main.py
```

Or trigger via **GitHub Actions → Run workflow**.

---

## 📁 Project Structure

```
├── main.py               # Pipeline orchestrator
├── script_generator.py   # Groq LLM script generation
├── voiceover.py          # Edge-TTS audio synthesis
├── video_creator.py      # FFmpeg video assembly + captions
├── uploader.py           # catbox.moe + Make.com webhook
├── requirements.txt
└── .github/
    └── workflows/
        └── daily.yml     # GitHub Actions cron schedule
```

---

## 🔑 Key Features

- **Fully serverless** — runs entirely on GitHub Actions, no server cost
- **Topic-aware video matching** — script topics map to relevant Pexels search queries
- **Robust retry logic** — JSON sanitization and up to 8 LLM retry attempts
- **Dynamic video duration** — video length matches actual voiceover, not hardcoded
- **Run logging** — every pipeline run saved to `output/run_log.json` as GitHub artifact

---

## 📦 Dependencies

```
requests
edge-tts
groq
```
FFmpeg installed separately via apt (handled in GitHub Actions workflow).

---

## 📄 License

MIT
