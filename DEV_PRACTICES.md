# Development Best Practices

## ⚠️ RULE #1: DOCKER-ONLY DEVELOPMENT

**NEVER install dependencies or run code locally. ALWAYS use Docker.**

This project uses containerized development to ensure:
- ✅ No pollution of your local system
- ✅ Consistent environment across all developers
- ✅ Easy onboarding (one command to start)
- ✅ No "works on my machine" issues

---

## 🐳 Getting Started

### Prerequisites
- Docker Desktop installed and running
- VS Code with Remote-Containers extension
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd markdown-rag-mcp
   ```

2. **Open in VS Code**
   ```bash
   code .
   ```

3. **Reopen in Container**
   - VS Code will prompt: "Reopen in Container" → Click it
   - Or: `Cmd/Ctrl + Shift + P` → "Dev Containers: Reopen in Container"
   - Wait for container to build (first time takes ~5 minutes)

4. **You're ready!**
   - Terminal is now inside the container
   - All extensions are installed
   - Python dependencies are ready

---

## 🚀 Development Workflow

### Starting Development

```bash
# Option 1: VS Code Dev Container (Recommended)
# Just open VS Code and use "Reopen in Container"

# Option 2: Docker Compose (Manual)
docker-compose up -d
docker-compose exec markdown-rag-mcp bash
```

### Running the Indexer

```bash
# Inside container
python src/indexer.py

# Force re-index
python src/indexer.py --force
```

### Running the MCP Server

```bash
# Inside container
python src/server.py
```

### Testing Search

```bash
# Inside container
python src/search.py
```

### Interactive Development

```bash
# IPython for testing
ipython

# Jupyter Notebook
jupyter notebook --allow-root --ip=0.0.0.0
```

---

## 📝 Code Standards

### Python Style Guide

**Follow PEP 8 with modifications:**
- Line length: 100 characters (not 79)
- Use Black for formatting
- Use type hints where helpful
- Docstrings for public functions

**Formatting (automatic):**
```bash
# Format single file
black src/indexer.py

# Format all files
black src/
```

**Linting:**
```bash
# Check code quality
pylint src/

# Check single file
pylint src/indexer.py
```

### Code Organization

```
src/
├── config.py          # Configuration (env vars, paths)
├── parser.py          # Markdown parsing logic
├── indexer.py         # Vault indexing
├── search.py          # Search functionality
└── server.py          # MCP server

tests/                 # Unit tests
examples/              # Example scripts
docs/                  # Documentation
```

**Principles:**
- ✅ Single Responsibility: Each module does one thing
- ✅ DRY: Don't Repeat Yourself
- ✅ Clear naming: `parse_markdown()` not `do_thing()`
- ✅ Small functions: <50 lines ideally
- ✅ Type hints: `def search(query: str) -> List[Result]:`

### Import Order

```python
# 1. Standard library
import os
from pathlib import Path

# 2. Third-party
import chromadb
from mcp.server import Server

# 3. Local modules
from parser import MarkdownParser
import config
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run with coverage
pytest --cov=src tests/

# Watch mode (re-run on file changes)
pytest-watch
```

### Writing Tests

```python
# tests/test_parser.py
import pytest
from src.parser import MarkdownParser

def test_parse_frontmatter():
    """Test YAML frontmatter parsing"""
    parser = MarkdownParser()
    content = """---
title: Test
tags: [python, test]
---
# Content
"""
    result = parser.parse_file(content)
    assert result['metadata']['title'] == 'Test'
    assert 'python' in result['tags']
```

**Test Coverage Goals:**
- Core logic: 80%+ coverage
- Edge cases: Test error paths
- Integration tests: Test full workflows

---

## 📦 Dependencies

### Adding New Dependencies

```bash
# 1. Add to requirements.txt
echo "new-package>=1.0.0" >> requirements.txt

# 2. Rebuild container
docker-compose down
docker-compose up -d --build

# 3. In VS Code: "Dev Containers: Rebuild Container"
```

### Updating Dependencies

```bash
# Update all packages
pip list --outdated
pip install --upgrade <package>

# Update requirements.txt
pip freeze > requirements.txt
```

---

## 🔄 Git Workflow

### Branch Strategy

```bash
# Feature branches
git checkout -b feature/semantic-search

# Bug fixes
git checkout -b fix/indexer-crash

# Documentation
git checkout -b docs/update-readme
```

### Commit Messages

**Format:**
```
type(scope): short description

Longer explanation if needed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```bash
git commit -m "feat(search): add tag filtering support"
git commit -m "fix(indexer): handle empty markdown files"
git commit -m "docs(readme): add Docker setup instructions"
```

### Before Committing

```bash
# 1. Format code
black src/

# 2. Check linting
pylint src/

# 3. Run tests
pytest

# 4. Check what you're committing
git diff --staged

# 5. Commit
git commit -m "feat: your message"
```

---

## 🐛 Debugging

### VS Code Debugging

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Index Vault",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/src/indexer.py",
      "console": "integratedTerminal",
      "env": {
        "VAULT_PATH": "/vault"
      }
    }
  ]
}
```

### Print Debugging

```python
# Use rich for better output
from rich import print as rprint
from rich.pretty import pprint

rprint("[bold green]Debug info:[/bold green]")
pprint(my_complex_object)
```

### Container Debugging

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f markdown-rag-mcp

# Shell into container
docker-compose exec markdown-rag-mcp bash

# Check container resources
docker stats

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

---

## 📊 Performance

### Profiling

```bash
# Time a script
time python src/indexer.py

# Profile with cProfile
python -m cProfile -o profile.stats src/indexer.py
```

### Optimization Guidelines

1. **Index build time:**
   - Target: <10 seconds for 1000 notes
   - Use batch embedding (10 docs at a time)
   - Cache embeddings

2. **Search latency:**
   - Target: <500ms for queries
   - Use appropriate similarity thresholds
   - Limit result sets

3. **Memory usage:**
   - Monitor with `docker stats`
   - Chunk large files
   - Clear caches periodically

---

## 🔒 Security

### Best Practices

1. **Never commit secrets**
   - Use `.env` files (gitignored)
   - Use environment variables
   - No API keys in code

2. **Input validation**
   - Sanitize file paths
   - Validate metadata
   - Check file sizes

3. **Dependencies**
   - Regularly update packages
   - Check for vulnerabilities
   - Use pinned versions

### Security Scanning

```bash
# Scan for vulnerabilities
pip-audit

# Check for secrets in commits
git secrets --scan-history
```

---

## 📚 Documentation

### Code Documentation

```python
def search_vault(query: str, limit: int = 10) -> List[Result]:
    """
    Search the indexed vault using semantic similarity.
    
    Args:
        query: Natural language search query
        limit: Maximum number of results to return
        
    Returns:
        List of Result objects sorted by relevance
        
    Example:
        >>> results = search_vault("python programming", limit=5)
        >>> for result in results:
        ...     print(result.title)
    """
    pass
```

### Architecture Documentation

Update `docs/ARCHITECTURE.md` when making significant changes:
- Component diagrams
- Data flow
- Design decisions
- Trade-offs

---

## 🚨 Common Issues

### "Container won't start"

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs

# Rebuild
docker-compose down
docker-compose up -d --build
```

### "Can't connect to Ollama"

```bash
# Verify Ollama is running
docker ps | grep ollama

# Test connection
curl http://localhost:11434/api/tags

# Check Docker network
docker-compose exec markdown-rag-mcp curl http://host.docker.internal:11434/api/tags
```

### "Module not found"

```bash
# Verify you're in container
which python  # Should be /usr/local/bin/python

# Reinstall dependencies
pip install -r requirements.txt

# Check PYTHONPATH
echo $PYTHONPATH  # Should include /workspace/src
```

---

## 🎯 Definition of Done

Before marking a task complete:

- ✅ Code follows style guide
- ✅ Tests written and passing
- ✅ Documentation updated
- ✅ No linting errors
- ✅ Tested in Docker container
- ✅ Git commit message follows format
- ✅ PR reviewed (if applicable)

---

## 🤝 Getting Help

1. **Check this document first**
2. **Search issues on GitHub**
3. **Ask in team chat**
4. **Create GitHub issue with:**
   - What you tried
   - What you expected
   - What actually happened
   - Steps to reproduce

---

## 📝 Quick Reference

### Daily Commands

```bash
# Start work
code .  # Opens VS Code → "Reopen in Container"

# Run indexer
python src/indexer.py

# Run tests
pytest

# Format code
black src/

# Commit
git add .
git commit -m "feat: your change"
git push
```

### Emergency Commands

```bash
# Nuke everything and start fresh
docker-compose down -v
docker system prune -af
docker-compose up -d --build
```

---

**Remember: If you're not in a Docker container, you're doing it wrong!** 🐳



