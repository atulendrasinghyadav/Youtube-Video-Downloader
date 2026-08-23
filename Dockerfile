# ── Stage 1: Build React frontend ────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (better layer caching)
COPY frontend/package*.json ./
RUN npm install

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Production Python image ─────────────────────────────────────────
FROM python:3.11-slim

# Install ffmpeg (required by yt-dlp for merging/converting)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask server
COPY server.py .

# Copy the built React app from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Run with gunicorn — Render injects $PORT automatically
CMD gunicorn -b 0.0.0.0:${PORT:-10000} --timeout 300 --workers 2 server:app
