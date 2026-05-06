import os
import sys
import queue as queue_mod
from pathlib import Path
import yt_dlp
from yt_dlp.utils import DownloadError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Use local ffmpeg if present, otherwise rely on system PATH
_local_ffmpeg = os.path.join(SCRIPT_DIR, 'ffmpeg.exe')
FFMPEG_LOCATION = SCRIPT_DIR if os.path.isfile(_local_ffmpeg) else None

QUALITY_FORMATS = {
    'best':  'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
    '720p':  'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720][ext=mp4]/best[height<=720]',
    '480p':  'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480][ext=mp4]/best[height<=480]',
    'audio': 'bestaudio[ext=m4a]/bestaudio/best',
}


def get_video_info(url: str) -> dict:
    """Return metadata for a YouTube URL without downloading."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        'title': info.get('title', 'Unknown'),
        'duration': info.get('duration', 0),
        'thumbnail': info.get('thumbnail', ''),
        'uploader': info.get('uploader', ''),
        'view_count': info.get('view_count', 0),
    }


def download_video(url: str, output_path: str, quality: str, progress_queue=None) -> str:
    """
    Download a YouTube video/audio and return the basename of the saved file.
    Sends progress dicts to `progress_queue` if provided.
    """
    os.makedirs(output_path, exist_ok=True)

    format_selector = QUALITY_FORMATS.get(quality, QUALITY_FORMATS['best'])
    result_filename: list[str] = []

    def progress_hook(d):
        if d['status'] == 'downloading' and progress_queue is not None:
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100) if total else 0
            speed = d.get('speed', 0)
            speed_str = f'{speed / 1024 / 1024:.1f} MB/s' if speed else '...'
            eta = d.get('eta', 0)
            progress_queue.put({
                'type': 'progress',
                'progress': percent,
                'speed': speed_str,
                'eta': eta,
                'message': f'Downloading… {percent}%',
            })
        elif d['status'] == 'finished':
            if d.get('filename'):
                result_filename.append(d['filename'])
            if progress_queue is not None:
                progress_queue.put({'type': 'progress', 'progress': 95, 'message': 'Processing…'})

    ydl_opts = {
        'format': format_selector,
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4' if quality != 'audio' else None,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
    }
    if FFMPEG_LOCATION:
        ydl_opts['ffmpeg_location'] = FFMPEG_LOCATION

    if quality == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            prepared = ydl.prepare_filename(info)

        if quality == 'audio':
            final = os.path.splitext(prepared)[0] + '.mp3'
        else:
            final = os.path.splitext(prepared)[0] + '.mp4'

        return os.path.basename(final)

    except DownloadError as e:
        raise RuntimeError(str(e)) from e
