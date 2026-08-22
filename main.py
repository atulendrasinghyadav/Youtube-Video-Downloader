import yt_dlp
import certifi
import os
import ssl

# Fix SSL certificate verification on macOS
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context


def progress_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "N/A")
        speed = d.get("_speed_str", "N/A")
        eta = d.get("_eta_str", "N/A")
        print(f"\r  Downloading: {percent}  Speed: {speed}  ETA: {eta}", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\n  Download complete! Processing file...")


def download_video(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "%(title)s.%(ext)s",
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print("\nFetching video info...")
        info = ydl.extract_info(url, download=False)
        print(f"\nTitle   : {info.get('title', 'Unknown')}")
        print(f"Duration: {info.get('duration_string', 'Unknown')}")
        print(f"Channel : {info.get('channel', 'Unknown')}")
        view_count = info.get('view_count', 'Unknown')
        print(f"Views   : {view_count:,}" if isinstance(view_count, int) else f"Views   : {view_count}")

        confirm = input("\nProceed with download? (y/n): ").strip().lower()
        if confirm != "y":
            print("Download cancelled.")
            return

        ydl.download([url])
        print(f"\nSaved as: {info.get('title', 'video')}.mp4")


if __name__ == "__main__":
    print("=== YouTube Video Downloader ===")
    url = input("YouTube Video URL: ").strip()

    if not url:
        print("Error: No URL provided.")
    else:
        try:
            download_video(url)
        except yt_dlp.utils.DownloadError as e:
            print(f"\nDownload error: {e}")
        except KeyboardInterrupt:
            print("\nDownload cancelled by user.")
