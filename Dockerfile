# Markdown RAG MCP Server - Development Container
FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    less \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    black \
    pylint \
    ipython \
    jupyter

# Expose MCP server port (if needed for HTTP mode)
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/workspace/src

# Default command (can be overridden)
CMD ["python", "-m", "ipython"]



