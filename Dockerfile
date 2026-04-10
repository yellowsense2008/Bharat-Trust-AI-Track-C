# ─── Production Dockerfile for FastAPI Voice API (Cloud Run) ────────────────
#
# Optimized for:
#  - Fast startup
#  - Small container size
#  - Cloud Run compatibility
#  - Non-root security
#
# Uses:
#  - python:3.11-slim
#  - gunicorn + uvicorn workers
#  - PORT injected by Cloud Run
# ───────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ─── Python runtime settings ───────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# pip performance flags
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Cloud Run injects PORT automatically
ENV PORT=8080

# ─── Install system dependencies ───────────────────────────────────────────
# ffmpeg → required for audio processing
# curl → useful for container debugging
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ─── Application working directory ─────────────────────────────────────────
WORKDIR /app

# ─── Install Python dependencies ───────────────────────────────────────────
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ─── Copy application source code ──────────────────────────────────────────
COPY app /app/app

# ─── Create writable runtime directories (Cloud Run uses /tmp) ─────────────
RUN mkdir -p /tmp/audio

# ─── Create non-root user ──────────────────────────────────────────────────
RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser:appuser /app /tmp

USER appuser

# ─── Expose container port ─────────────────────────────────────────────────
EXPOSE 8080

# ─── Start FastAPI using Gunicorn ──────────────────────────────────────────
# 1 worker is recommended for Cloud Run (horizontal scaling)
CMD ["sh", "-c", "exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 1 \
    --bind 0.0.0.0:${PORT} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -"]