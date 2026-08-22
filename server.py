import os
import ssl
import re
import shutil
import tempfile
import threading
import certifi
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp

# Fix SSL on macOS
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

YDL_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "nocheckcertificate": False,
}


def safe_filename(name):
    return re.sub(r'[^\w\s\-.]', '', name).strip()


def cleanup_later(path, delay=120):
    """Delete temp directory after a delay (gives browser time to finish download)."""
    def _do():
        import time
        time.sleep(delay)
        shutil.rmtree(path, ignore_errors=True)
    threading.Thread(target=_do, daemon=True).start()


# ── /api/info ────────────────────────────────────────────────────────────────
@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        with yt_dlp.YoutubeDL(YDL_BASE_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            "title":     info.get("title", "Unknown"),
            "duration":  info.get("duration_string", "Unknown"),
            "channel":   info.get("channel", "Unknown"),
            "views":     info.get("view_count", 0),
            "thumbnail": info.get("thumbnail", ""),
        })
    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── /api/download/video ───────────────────────────────────────────────────────
@app.route("/api/download/video", methods=["POST"])
def download_video():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    tmpdir = tempfile.mkdtemp()
    try:
        opts = {
            **YDL_BASE_OPTS,
            "format": "bestvideo+bestaudio/best",
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        mp4_files = [f for f in os.listdir(tmpdir) if f.endswith(".mp4")]
        if not mp4_files:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return jsonify({"error": "MP4 file not found after download"}), 500

        filepath = os.path.join(tmpdir, mp4_files[0])
        filesize = os.path.getsize(filepath)
        dl_name = safe_filename(info.get("title", "video")) + ".mp4"
        cleanup_later(tmpdir)

        def generate():
            with open(filepath, "rb") as f:
                while chunk := f.read(1024 * 64):
                    yield chunk

        return Response(
            stream_with_context(generate()),
            mimetype="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{dl_name}"',
                "Content-Length": str(filesize),
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return jsonify({"error": str(e)}), 500


# ── /api/download/audio ───────────────────────────────────────────────────────
@app.route("/api/download/audio", methods=["POST"])
def download_audio():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400

    tmpdir = tempfile.mkdtemp()
    try:
        opts = {
            **YDL_BASE_OPTS,
            "format": "bestaudio/best",
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        mp3_files = [f for f in os.listdir(tmpdir) if f.endswith(".mp3")]
        if not mp3_files:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return jsonify({"error": "MP3 file not found after download"}), 500

        filepath = os.path.join(tmpdir, mp3_files[0])
        filesize = os.path.getsize(filepath)
        dl_name = safe_filename(info.get("title", "audio")) + ".mp3"
        cleanup_later(tmpdir)

        def generate():
            with open(filepath, "rb") as f:
                while chunk := f.read(1024 * 64):
                    yield chunk

        return Response(
            stream_with_context(generate()),
            mimetype="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{dl_name}"',
                "Content-Length": str(filesize),
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
