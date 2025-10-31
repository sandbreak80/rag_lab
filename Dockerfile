# Markdown RAG MCP Server - Development Container
FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    less \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install ALL Python dependencies from requirements.txt
# This includes: mcp, chromadb, pyyaml, requests, aiohttp, pytest, pytest-cov,
# pytest-playwright, playwright, flask, rank-bm25, networkx
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for UI testing)
RUN playwright install --with-deps chromium

# Additional development tools (not in requirements.txt)
RUN pip install --no-cache-dir \
    pytest-asyncio \
    black \
    pylint \
    ipython \
    jupyter

# Expose ports
# MCP server (if needed)
EXPOSE 8000
# Web UI
EXPOSE 5555

# Set Python path
ENV PYTHONPATH=/workspace/src

# Default command (can be overridden)
CMD ["sleep", "infinity"]



