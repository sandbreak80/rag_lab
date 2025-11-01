FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY services/knowledge-graph/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY services/knowledge-graph/app/ /app/

# Copy common utilities and src
COPY services/common /workspace/services/common
COPY src /workspace/src

# Set environment
ENV SERVICE_NAME=graph-service
ENV SERVICE_PORT=8007
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8007

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8007/health').raise_for_status()"

# Run service
CMD ["python", "service.py"]

