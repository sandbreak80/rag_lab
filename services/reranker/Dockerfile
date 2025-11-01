FROM python:3.11-slim

WORKDIR /workspace

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY services/common /workspace/services/common

# Copy src files
COPY src /workspace/src

# Copy service code
COPY services/reranker/app /workspace/services/reranker/app

# Set Python path
ENV PYTHONPATH=/workspace:/workspace/services/common:/workspace/src

# Expose port
EXPOSE 8008

# Run service
CMD ["python", "/workspace/services/reranker/app/service.py"]

