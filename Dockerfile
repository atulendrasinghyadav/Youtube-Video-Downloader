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

# Run the app with gunicorn (timeout set to 5 mins for large downloads)
CMD ["gunicorn", "-b", "0.0.0.0:5001", "--timeout", "300", "server:app"]
