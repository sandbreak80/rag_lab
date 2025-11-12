# Vector DB Service - ChromaDB wrapper
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1

# Install build dependencies for compiling Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  g++ \
  curl \
  tini \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

# Copy application code
COPY app/ ./app/

# Use tini for proper signal handling
ENTRYPOINT ["tini", "--"]

# Start Flask app
CMD ["python", "-u", "app/service.py"]
