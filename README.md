# YouTube Video & Audio Downloader 🎥🎵

A full-stack application to download YouTube videos (MP4) and extract audio (MP3) in the highest possible quality. It includes both a modern React web interface and simple command-line scripts.

## Features
- **Web Interface:** Sleek, dark-themed UI to preview video metadata (thumbnail, duration, views) before downloading.
- **Video Download:** Downloads best video and best audio streams, merging them into a high-quality `.mp4`.
- **Audio Download:** Extracts the audio track and converts it to a 192kbps `.mp3`.
- **CLI Options:** Standalone Python scripts for quick terminal-based downloading.

## Tech Stack
- **Backend / CLI:** Python, Flask, `yt-dlp` (for extraction), `ffmpeg` (for media processing)
- **Frontend:** React, Vite, CSS

## Prerequisites
Before you begin, ensure you have the following installed on your machine:
1. **Python 3.x**
2. **Node.js & npm**
3. **FFmpeg** (Required by `yt-dlp` to merge video/audio and extract MP3s). 
   - *Mac (Homebrew):* `brew install ffmpeg`
   - *Windows:* Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or use `winget install ffmpeg`

---

## 🛠 Installation & Setup

### 1. Backend Setup (Python)
Open a terminal in the root directory of the project:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask backend server (runs on port 5001)
python server.py
```

### 2. Frontend Setup (React)
Open a **second terminal** and navigate to the `frontend` folder:

```bash
cd frontend

# Install Node modules
npm install

# Start the Vite development server
npm run dev
```
Open your browser and navigate to `http://localhost:5173`.

---

## 💻 Command-Line Usage (Optional)
If you prefer the terminal over the web UI, you can use the provided standalone scripts (make sure your virtual environment is activated):

- **For Video (MP4):**
  ```bash
  python main.py
  ```
- **For Audio (MP3):**
  ```bash
  python mp3downloader.py
  ```

---

## Disclaimer
*This tool is for personal use only. Please respect YouTube's Terms of Service and the copyright of content creators.*
