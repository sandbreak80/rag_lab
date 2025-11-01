FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY vector-db/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY vector-db/app/ /app/

# Copy common utilities
COPY common /workspace/services/common

# Set environment
ENV SERVICE_NAME=vector-db
ENV SERVICE_PORT=8005
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8005/health').raise_for_status()"

# Run service
CMD ["python", "service.py"]

