# ─── Stage: Production Image ───────────────────────────────────────────────────
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies required by faster-whisper / ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# 🔥 ADD THIS LINE
RUN chmod -R 755 /app
    
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

# Cloud Run injects $PORT at runtime (default 8080).
# Use shell form so the variable is expanded at container start time.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --log-level info