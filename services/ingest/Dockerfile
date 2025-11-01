FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY services/ingest/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY services/ingest/app/ /app/

# Copy common utilities and source code
COPY services/common /workspace/services/common
COPY src /workspace/src

# Create upload directory
RUN mkdir -p /uploads

# Set environment
ENV SERVICE_NAME=ingest-service
ENV SERVICE_PORT=8001
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health').raise_for_status()"

# Run service
CMD ["python", "service.py"]

