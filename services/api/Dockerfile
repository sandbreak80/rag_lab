FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY services/api/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY services/api/ /app/services/api/

# Set Python path for imports to work
ENV PYTHONPATH="/app:/app/services/api"

# Expose API port
EXPOSE 8080

# Start application
CMD ["python", "-m", "uvicorn", "services.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
