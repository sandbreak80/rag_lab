FROM python:3.10-slim

WORKDIR /workspace

# Install dependencies
COPY services/api/requirements.txt /workspace/services/api/
RUN pip install --no-cache-dir -r /workspace/services/api/requirements.txt

# Copy application code
COPY services/api/ /workspace/services/api/
COPY services/common/ /workspace/services/common/

# Set Python path
ENV PYTHONPATH=/workspace:/workspace/services/api:/workspace/services/common

# Expose API port
EXPOSE 8080

# Start application
CMD ["python", "-m", "uvicorn", "services.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
