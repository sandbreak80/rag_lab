# Dependencies Documentation

## Overview

This document lists all dependencies required for the Markdown RAG MCP Server, including their purpose and version requirements.

## Python Dependencies

All Python dependencies are defined in `requirements.txt` and automatically installed during Docker build.

### Core RAG System

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | >=0.9.0 | Model Context Protocol implementation |
| `chromadb` | >=0.4.18 | Vector database for embeddings storage |
| `pyyaml` | >=6.0 | YAML parsing for Markdown frontmatter |
| `requests` | >=2.31.0 | HTTP client for Ollama API |
| `aiohttp` | >=3.9.0 | Async HTTP support |

### Advanced RAG Features

| Package | Version | Purpose |
|---------|---------|---------|
| `rank-bm25` | >=0.2.2 | BM25 keyword search for hybrid retrieval |
| `networkx` | >=3.0 | Knowledge graph construction and traversal |

### Web UI

| Package | Version | Purpose |
|---------|---------|---------|
| `flask` | >=3.0.0 | Web framework for chat interface |

### Testing

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.4.3 | Test framework |
| `pytest-cov` | >=4.1.0 | Code coverage reporting |
| `pytest-playwright` | >=0.4.3 | Playwright integration for UI tests |
| `playwright` | >=1.40.0 | Browser automation for UI testing |

### Development Tools (Not in requirements.txt)

These are installed separately in the Dockerfile:

| Package | Purpose |
|---------|---------|
| `pytest-asyncio` | Async test support |
| `black` | Code formatting |
| `pylint` | Code linting |
| `ipython` | Interactive Python shell |
| `jupyter` | Notebook support |

## System Dependencies

Installed via apt-get in Dockerfile:

| Package | Purpose |
|---------|---------|
| `git` | Version control |
| `curl` | HTTP requests |
| `vim` | Text editor |
| `less` | File viewer |
| `wget` | File downloads |
| `gnupg` | Cryptographic operations |

## Playwright Browser Dependencies

Playwright requires additional system packages for browser automation. These are automatically installed via:

```bash
playwright install --with-deps chromium
```

This installs:
- Chromium browser
- Required system libraries (libglib, libx11, etc.)

## External Services

### Required

| Service | Purpose | Default URL |
|---------|---------|-------------|
| Ollama | LLM inference and embeddings | `http://host.docker.internal:11434` |

### Models Required in Ollama

| Model | Purpose | Config Variable |
|-------|---------|-----------------|
| `nomic-embed-text` | Document embeddings | `EMBEDDING_MODEL` |
| `llama3.2:3b` | Chat and query expansion | `CHAT_MODEL` |

## Docker Build Process

The Dockerfile ensures all dependencies are installed in the correct order:

1. **System packages** (apt-get)
2. **Python packages** (pip from requirements.txt)
3. **Playwright browsers** (playwright install)
4. **Development tools** (additional pip installs)

### Build Command

```bash
docker-compose build
```

### Rebuild After Dependency Changes

If you modify `requirements.txt`, rebuild the image:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Verifying Installation

### Check Python Packages

```bash
docker-compose exec markdown-rag-mcp pip list
```

### Check Playwright

```bash
docker-compose exec markdown-rag-mcp playwright --version
```

### Run Tests

```bash
# Unit tests (no browser required)
docker-compose exec markdown-rag-mcp pytest tests/ --ignore=tests/test_webapp_ui.py -v

# UI tests (requires Playwright)
docker-compose exec markdown-rag-mcp pytest tests/test_webapp_ui.py -v
```

## Troubleshooting

### Missing Dependencies After Container Restart

**Problem**: Dependencies installed with `pip install` are lost after container restart.

**Cause**: Dependencies were installed in the running container, not baked into the Docker image.

**Solution**: Always rebuild the Docker image after modifying `requirements.txt`:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Playwright Browser Not Found

**Problem**: `playwright._impl._errors.Error: Executable doesn't exist`

**Cause**: Playwright browsers not installed in the Docker image.

**Solution**: Rebuild with the updated Dockerfile that includes `playwright install --with-deps chromium`.

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'X'`

**Cause**: Package missing from `requirements.txt` or Docker image not rebuilt.

**Solution**:
1. Add package to `requirements.txt`
2. Rebuild Docker image
3. Restart container

## CI/CD Considerations

For automated testing and deployment:

1. **Always use Docker** - Ensures consistent environment
2. **Cache Docker layers** - Speed up builds by caching dependency installation
3. **Pin versions** - Use exact versions in production (e.g., `flask==3.0.2` instead of `flask>=3.0.0`)
4. **Separate test dependencies** - Consider splitting `requirements.txt` into `requirements-base.txt` and `requirements-dev.txt`

## Dependency Updates

To update dependencies:

1. Update version in `requirements.txt`
2. Test locally:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   make test
   ```
3. Commit changes to both `requirements.txt` and `Dockerfile` if needed
4. Update this documentation if adding new dependencies

## Security

- **Regular updates**: Keep dependencies updated for security patches
- **Vulnerability scanning**: Use tools like `safety` or `pip-audit`
- **Minimal base image**: Using `python:3.11-slim` reduces attack surface
- **No root user in production**: Consider adding non-root user for production deployments

## Performance Considerations

- **Image size**: Current image ~2GB (includes Playwright browsers)
- **Build time**: ~5-10 minutes for full build with all dependencies
- **Runtime memory**: ~500MB base + embeddings/models in memory
- **Disk space**: ChromaDB indices can grow large with many documents

## License Compliance

All dependencies are open-source with permissive licenses:
- Most use MIT or Apache 2.0 licenses
- Check `pip show <package>` for specific license information
- Ensure compliance with your organization's policies

