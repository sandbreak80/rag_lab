FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY app/ /app/

# Set environment
ENV PYTHONUNBUFFERED=1
ENV SERVICE_PORT=8019

EXPOSE 8019

CMD ["python", "service.py"]

