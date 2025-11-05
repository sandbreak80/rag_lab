FROM vllm/vllm-openai:latest

# Set environment variables
ENV HF_HOME=/root/.cache/huggingface
ENV VLLM_WORKER_MULTIPROC_METHOD=spawn

# Expose OpenAI-compatible API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# vLLM will be started by docker-compose command

