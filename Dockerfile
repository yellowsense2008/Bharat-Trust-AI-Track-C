FROM python:3.11-slim

WORKDIR /app

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run uses PORT env var
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}