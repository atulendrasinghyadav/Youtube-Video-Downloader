import { useState } from "react";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:5001";

function formatViews(n) {
  if (!n) return "N/A";
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(1) + "B";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toLocaleString();
}

export default function App() {
  const [url, setUrl] = useState("");
  const [info, setInfo] = useState(null);
  const [error, setError] = useState("");
  const [fetching, setFetching] = useState(false);
  const [downloading, setDownloading] = useState(null); // "video" | "audio" | null

  async function fetchInfo() {
    if (!url.trim()) return;
    setError("");
    setInfo(null);
    setFetching(true);
    try {
      const res = await fetch(`${API}/api/info`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to fetch info");
      setInfo(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setFetching(false);
    }
  }

  async function handleDownload(type) {
    setError("");
    setDownloading(type);
    try {
      const endpoint = type === "video" ? "/api/download/video" : "/api/download/audio";
      const ext = type === "video" ? "mp4" : "mp3";
      const mime = type === "video" ? "video/mp4" : "audio/mpeg";

      const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Download failed");
      }

      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(new Blob([blob], { type: mime }));
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${info?.title || "download"}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(blobUrl);
    } catch (e) {
      setError(e.message);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <svg viewBox="0 0 24 24" fill="currentColor" className="yt-icon">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </svg>
          <h1>YouTube Downloader</h1>
        </div>
        <p className="subtitle">Download videos &amp; audio in the best quality</p>
      </header>

      <main className="main">
        {/* URL Input */}
        <div className="input-card">
          <div className="input-row">
            <input
              type="text"
              className="url-input"
              placeholder="Paste YouTube URL here..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchInfo()}
            />
            <button
              className="fetch-btn"
              onClick={fetchInfo}
              disabled={fetching || !url.trim()}
            >
              {fetching ? <span className="spinner" /> : "Fetch Info"}
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="error-box">
            <span className="error-icon">⚠</span> {error}
          </div>
        )}

        {/* Video Info Card */}
        {info && (
          <div className="info-card">
            <div className="info-left">
              <img
                src={info.thumbnail}
                alt={info.title}
                className="thumbnail"
                onError={(e) => (e.target.style.display = "none")}
              />
            </div>
            <div className="info-right">
              <h2 className="video-title">{info.title}</h2>
              <div className="meta">
                <span className="meta-item">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"/></svg>
                  {info.duration}
                </span>
                <span className="meta-item">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                  {info.channel}
                </span>
                <span className="meta-item">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
                  {formatViews(info.views)} views
                </span>
              </div>

              <div className="download-btns">
                <button
                  className="dl-btn dl-video"
                  onClick={() => handleDownload("video")}
                  disabled={!!downloading}
                >
                  {downloading === "video" ? (
                    <><span className="spinner" /> Processing…</>
                  ) : (
                    <><span className="btn-icon">⬇</span> Download MP4</>
                  )}
                </button>
                <button
                  className="dl-btn dl-audio"
                  onClick={() => handleDownload("audio")}
                  disabled={!!downloading}
                >
                  {downloading === "audio" ? (
                    <><span className="spinner" /> Processing…</>
                  ) : (
                    <><span className="btn-icon">🎵</span> Download MP3</>
                  )}
                </button>
              </div>

              {downloading && (
                <p className="download-note">
                  ⏳ Downloading &amp; processing on the server — this may take a minute for longer videos. The file will auto-save when ready.
                </p>
              )}
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>For personal use only · Respect YouTube's Terms of Service</p>
      </footer>
    </div>
  );
}
