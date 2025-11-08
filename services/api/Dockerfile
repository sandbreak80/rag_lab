FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/common/ ./services/common/
COPY services/api/ ./services/api/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run application
CMD ["python", "-m", "services.api.app"]

