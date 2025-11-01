FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY embedding/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY embedding/app/ /app/

# Copy common utilities
COPY common /workspace/services/common

# Set environment
ENV SERVICE_NAME=embedding-service
ENV SERVICE_PORT=8006
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8006/health').raise_for_status()"

# Run service
CMD ["python", "service.py"]

