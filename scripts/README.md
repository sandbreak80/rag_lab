# RAG Lab Scripts

Utility scripts for managing the RAG Lab application.

## Quick Start

### Build and Start Everything

```bash
./scripts/build-and-start.sh
```

This script will:
1. Check Docker is running
2. Stop any existing containers
3. Build the React frontend
4. Build all Docker images
5. Start Ollama service
6. Pull required Ollama models (llama3.2:3b, nomic-embed-text)
7. Start all other services
8. Check service health
9. Display service URLs

### Stop All Services

```bash
./scripts/stop.sh
```

### Clean Build (Remove All Data)

```bash
./scripts/build-and-start.sh --clean
```

⚠️ **WARNING:** This will delete all data including:
- Vector embeddings
- Uploaded documents
- BM25 indices
- Knowledge graph
- Metrics

## Individual Scripts

### Pull Ollama Models

```bash
./scripts/pull-ollama-models.sh
```

Pulls required Ollama models:
- **llama3.2:3b** - Chat/LLM model (~2GB)
- **nomic-embed-text** - Embedding model (~274MB)

Optional models (for testing):
- llama3.2:1b - Smallest, fastest
- llama3.1:8b - Medium, balanced
- mistral:7b - Alternative chat model

### Check Status

```bash
docker compose ps
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ollama
docker compose logs -f api-gateway
docker compose logs -f frontend
```

### Restart a Service

```bash
docker compose restart [service-name]

# Examples:
docker compose restart ollama
docker compose restart frontend
docker compose restart api-gateway
```

## Service URLs

After starting, the following services will be available:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | React UI |
| **API Gateway** | http://localhost:8000 | Main API endpoint |
| **Ollama** | http://localhost:11434 | LLM service |
| **SearXNG** | http://localhost:8080 | Web search |
| Vector DB | http://localhost:8005 | ChromaDB |
| Embedding Service | http://localhost:8006 | Text embeddings |
| Search Service | http://localhost:8002 | RAG search |
| Chat Service | http://localhost:8003 | Chat/LLM |
| Ingest Service | http://localhost:8001 | Document ingestion |
| Docling Service | http://localhost:8004 | PDF processing |
| Knowledge Graph | http://localhost:8007 | Graph relationships |
| Reranker | http://localhost:8008 | Result reranking |
| Web Search | http://localhost:8009 | Web search wrapper |
| Metrics Store | http://localhost:8011 | Performance metrics |

## Configuration

Edit `config.env` to change settings:

```bash
# Change chat model
CHAT_MODEL=llama3.2:3b

# Change embedding model
EMBEDDING_MODEL=nomic-embed-text

# Enable/disable features
ENABLE_KNOWLEDGE_GRAPH=true
ENABLE_RERANKING=false
ENABLE_WEB_SEARCH=true
```

## Troubleshooting

### Ollama not starting

```bash
# Check Ollama logs
docker compose logs -f ollama

# Restart Ollama
docker compose restart ollama
```

### Frontend not building

```bash
# Rebuild frontend
cd frontend
npm install
npm run build
cd ..

# Restart frontend container
docker compose restart frontend
```

### Services not healthy

```bash
# Check all service status
docker compose ps

# Check specific service logs
docker compose logs -f [service-name]

# Restart unhealthy service
docker compose restart [service-name]
```

### Port conflicts

If ports are already in use, edit `docker-compose.yml` to change port mappings:

```yaml
ports:
  - "3001:80"  # Change 3000 to 3001 for frontend
```

### Out of disk space

```bash
# Remove unused Docker resources
docker system prune -a

# Remove all volumes (⚠️ deletes all data)
docker compose down -v
```

## Development

### Run tests

```bash
# API tests
python tests/test_api_unit.py

# Integration tests
python tests/test_integration.py

# UI tests (requires services running)
docker compose --profile testing up playwright-tests
```

### Watch logs during development

```bash
# All services
docker compose logs -f

# Multiple specific services
docker compose logs -f api-gateway chat-service ollama
```

## GPU Support

To enable GPU support for Ollama (NVIDIA GPUs only):

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Uncomment GPU section in `docker-compose.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

3. Restart services:

```bash
docker compose down
docker compose up -d
```

## Clean Uninstall

To completely remove the RAG Lab:

```bash
# Stop and remove all containers and volumes
docker compose down -v

# Remove Docker images
docker compose down --rmi all

# Remove project directory
cd ..
rm -rf rag_lab
```

## Support

For issues, check:
- [GitHub Issues](https://github.com/sandbreak80/rag_lab/issues)
- [Documentation](../docs/)
- Service logs: `docker compose logs -f [service-name]`

