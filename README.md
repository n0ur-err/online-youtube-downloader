# L1GHT Video Downloader — Web Edition

A self-hosted web app for downloading YouTube videos and audio, powered by **yt-dlp** and **Flask**.

## Folder structure

```
video-downloader-web/
├── server.py          # Flask web server & API
├── downloader.py      # yt-dlp download logic
├── requirements.txt   # Python dependencies
├── start.bat          # Windows launcher
├── start.sh           # Linux / macOS launcher
├── static/
│   └── index.html     # Single-page web frontend
└── downloads/         # Created automatically — downloaded files land here
```

## Quick start

### Windows
```bat
start.bat
```

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

Then open **http://localhost:5000** in your browser.

## Requirements

- Python 3.9+
- **ffmpeg** — either:
  - Copy `ffmpeg.exe` / `ffmpeg` into this folder, **or**
  - Install system-wide: `apt install ffmpeg` / `brew install ffmpeg`

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/info` | Fetch video metadata (no download) |
| `POST` | `/api/download` | Start a download, returns `job_id` |
| `GET`  | `/api/progress/<job_id>` | SSE stream of download progress |
| `GET`  | `/api/file/<filename>` | Retrieve a completed download |

## Deploying online

You can host this on any VPS or PaaS that supports Python:

1. **Railway / Render / Fly.io** — push the folder as a Python app, set `PORT` env var.
2. **VPS (Ubuntu)** — install nginx as a reverse proxy in front of `gunicorn`:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 server:app
   ```
3. Set the `PORT` environment variable to change the default port (5000).

## Notes

- Downloaded files are auto-deleted after **1 hour** to save disk space.
- Only YouTube URLs are accepted for security reasons.
- For personal use only — respect copyright laws and YouTube's Terms of Service.
