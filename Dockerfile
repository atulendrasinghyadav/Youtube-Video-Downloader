FROM python:3.11-slim

# Install ffmpeg (required by yt-dlp)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server script
COPY server.py .

# Expose the port
EXPOSE 5001

# Run the app with gunicorn, binding to the PORT env var provided by Render
CMD gunicorn -b 0.0.0.0:${PORT:-5001} --timeout 300 server:app
