.PHONY: help build up down restart logs shell index search test format lint clean

# Default target
help:
	@echo "🤖 Markdown RAG MCP Server - Docker Commands"
	@echo ""
	@echo "Development:"
	@echo "  make build    - Build Docker image"
	@echo "  make up       - Start container"
	@echo "  make down     - Stop container"
	@echo "  make restart  - Restart container"
	@echo "  make logs     - View logs"
	@echo "  make shell    - Open shell in container"
	@echo ""
	@echo "Operations:"
	@echo "  make index          - Index vault"
	@echo "  make search         - Test search"
	@echo "  make study-any      - Study helper (any folder, interactive)"
	@echo "  make search-folder  - Quick folder search (see examples)"
	@echo "  make server         - Run MCP server"
	@echo "  make webapp         - Run Web UI (http://localhost:5555)"
	@echo ""
	@echo "Examples:"
	@echo "  make search-folder FOLDER='Green Belt' QUERY='prompt engineering'"
	@echo "  make search-folder FOLDER='Blue Belt' QUERY='responsible AI'"
	@echo ""
	@echo "Code Quality:"
	@echo "  make test     - Run tests"
	@echo "  make format   - Format code with black"
	@echo "  make lint     - Lint code with pylint"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean    - Remove containers and volumes"
	@echo "  make nuke     - Nuclear option: delete everything"

# Build Docker image
build:
	docker-compose build

# Start container
up:
	docker-compose up -d
	@echo "✅ Container started"
	@echo "💡 Use 'make shell' to enter container"

# Stop container
down:
	docker-compose down
	@echo "✅ Container stopped"

# Restart container
restart: down up

# View logs
logs:
	docker-compose logs -f markdown-rag-mcp

# Open shell in container
shell:
	docker-compose exec markdown-rag-mcp bash

# Index vault
index:
	docker-compose exec markdown-rag-mcp python src/indexer.py

# Force re-index
reindex:
	docker-compose exec markdown-rag-mcp python src/indexer.py --force

# Test search
search:
	docker-compose exec markdown-rag-mcp python src/search.py

# Blue Belt study helper (legacy - use study-any instead)
study:
	docker-compose exec markdown-rag-mcp python /workspace/examples/bluebelt_study_helper.py

# Flexible study helper (any folder)
study-any:
	docker-compose exec markdown-rag-mcp python /workspace/examples/study_helper.py

# Quick folder search (no LLM, fast)
search-folder:
	@if [ -z "$(FOLDER)" ] || [ -z "$(QUERY)" ]; then \
		echo "Usage: make search-folder FOLDER='Green Belt' QUERY='your question'"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make search-folder FOLDER='Green Belt' QUERY='prompt engineering'"; \
		echo "  make search-folder FOLDER='Blue Belt' QUERY='responsible AI'"; \
		echo "  make search-folder FOLDER='AI Task Team' QUERY='customer stories'"; \
		exit 1; \
	fi
	docker-compose exec markdown-rag-mcp python /workspace/examples/quick_folder_search.py "$(FOLDER)" "$(QUERY)"

# Run MCP server
server:
	docker-compose exec markdown-rag-mcp python src/server.py

# Run Web UI
webapp:
	docker-compose exec markdown-rag-mcp python src/webapp.py

# Run tests
test:
	docker-compose exec markdown-rag-mcp pytest

# Test with coverage
coverage:
	docker-compose exec markdown-rag-mcp pytest --cov=src tests/

# Format code
format:
	docker-compose exec markdown-rag-mcp black src/ tests/

# Lint code
lint:
	docker-compose exec markdown-rag-mcp pylint src/

# Clean up containers
clean:
	docker-compose down -v
	@echo "✅ Containers and volumes removed"

# Nuclear option: delete everything
nuke: clean
	docker system prune -af
	@echo "💥 Everything deleted"
	@echo "⚠️  Run 'make build && make up' to start fresh"

# Show container status
status:
	docker-compose ps

# Check Ollama connection
check-ollama:
	@echo "Checking Ollama connection..."
	@curl -s http://localhost:11434/api/tags | python3 -m json.tool || echo "❌ Ollama not reachable"

# Full setup from scratch
setup: build up index
	@echo "✅ Setup complete!"
	@echo "💡 Use 'make search' to test"



