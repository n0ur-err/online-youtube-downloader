import os
import sys
import json
import uuid
import queue
import threading
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from downloader import download_video, get_video_info

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Active download jobs: job_id -> { status, queue, filename }
jobs = {}
jobs_lock = threading.Lock()

ALLOWED_HOSTS = ('youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com')


def _is_valid_youtube_url(url: str) -> bool:
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and parsed.hostname in ALLOWED_HOSTS
    except Exception:
        return False


def _cleanup_old_files():
    """Remove downloads older than 1 hour to free disk space."""
    now = time.time()
    for fname in os.listdir(DOWNLOADS_DIR):
        fpath = os.path.join(DOWNLOADS_DIR, fname)
        try:
            if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > 3600:
                os.remove(fpath)
        except OSError:
            pass


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/info', methods=['POST'])
def info():
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    if not _is_valid_youtube_url(url):
        return jsonify({'error': 'Only YouTube URLs are supported'}), 400
    try:
        video_info = get_video_info(url)
        return jsonify(video_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    quality = data.get('quality', 'best')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    if not _is_valid_youtube_url(url):
        return jsonify({'error': 'Only YouTube URLs are supported'}), 400
    if quality not in ('best', '720p', '480p', 'audio'):
        quality = 'best'

    _cleanup_old_files()

    job_id = str(uuid.uuid4())
    progress_queue = queue.Queue()

    with jobs_lock:
        jobs[job_id] = {
            'status': 'pending',
            'queue': progress_queue,
            'filename': None,
        }

    def run():
        try:
            filename = download_video(url, DOWNLOADS_DIR, quality, progress_queue)
            with jobs_lock:
                jobs[job_id]['status'] = 'done'
                jobs[job_id]['filename'] = filename
            progress_queue.put({'type': 'done', 'filename': filename})
        except Exception as e:
            with jobs_lock:
                jobs[job_id]['status'] = 'error'
            progress_queue.put({'type': 'error', 'message': str(e)})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': job_id})


@app.route('/api/progress/<job_id>')
def progress(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    def generate():
        q = job['queue']
        while True:
            try:
                data = q.get(timeout=30)
                yield f'data: {json.dumps(data)}\n\n'
                if data.get('type') in ('done', 'error'):
                    break
            except queue.Empty:
                yield f'data: {json.dumps({"type": "keepalive"})}\n\n'

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@app.route('/api/file/<path:filename>')
def download_file(filename):
    # Sanitize to prevent path traversal
    safe_name = os.path.basename(filename)
    return send_from_directory(DOWNLOADS_DIR, safe_name, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
