import os
import ssl
import re
import shutil
import tempfile
import threading
import certifi
from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
import yt_dlp

# Fix SSL on macOS (no-op on Linux/Render but harmless)
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context

# Flask serves the built React app as static files from frontend/dist/
app = Flask(__name__, static_folder="frontend/dist", static_url_path="")

# CORS only needed when running locally with a separate dev server
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


# ── yt-dlp base options (hardened for cloud servers) ──────────────────────────
YDL_BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "nocheckcertificate": False,
    # Use multiple player clients — tv/ios bypass more checks than web
    "extractor_args": {"youtube": ["player_client=tv,ios,web"]},
    # Mimic a real browser
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    # Rate-limit to look human (seconds between requests)
    "sleep_interval": 3,
    "max_sleep_interval": 6,
    "sleep_interval_requests": 1,
    # Retry aggressively
    "retries": 10,
    "fragment_retries": 10,
    # Prefer http2
    "downloader_args": {"default": ["--http2"]},
}

# ── Load cookies (copy to writable /tmp for Render Docker) ────────────────────
cookie_paths = ["/etc/secrets/cookies.txt", "cookies.txt"]
for cp in cookie_paths:
    if os.path.exists(cp):
        tmp_cookie = "/tmp/cookies.txt"
        shutil.copy2(cp, tmp_cookie)
        os.chmod(tmp_cookie, 0o600)
        YDL_BASE_OPTS["cookiefile"] = tmp_cookie
        print(f"[server] Loaded cookies from {cp} → {tmp_cookie}")
        break
else:
    print("[server] WARNING: No cookies.txt found — YouTube WILL block cloud IPs!")



def safe_filename(name):
    return re.sub(r"[^\w\s\-.]", "", name).strip()


def cleanup_later(path, delay=120):
    """Delete temp directory after a delay (gives browser time to finish download)."""
    def _do():
        import time
        time.sleep(delay)
        shutil.rmtree(path, ignore_errors=True)
    threading.Thread(target=_do, daemon=True).start()


# ── React Frontend (catch-all — must be defined BEFORE any error handlers) ───
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    """Serve React's index.html for all non-API routes (SPA support)."""
    # Let API routes fall through to their own handlers
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    # Serve actual static assets (JS, CSS, images) if they exist
    static_file = os.path.join(app.static_folder, path)
    if path and os.path.exists(static_file):
        return send_from_directory(app.static_folder, path)
    # For everything else, return index.html (React handles routing)
    return send_from_directory(app.static_folder, "index.html")


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
