FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Docling
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY docling/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY docling/app/ /app/

# Copy common utilities
COPY common /workspace/services/common

# Set environment
ENV SERVICE_NAME=docling-service
ENV SERVICE_PORT=8004
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8004/health').raise_for_status()"

# Run service
CMD ["python", "service.py"]

