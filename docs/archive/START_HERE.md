# 🚀 START HERE - Markdown RAG MCP Server

## ✅ Setup Complete!

Your Docker-only development environment is ready to use.

---

## 🎯 Quick Start (Choose One)

### Option 1: VS Code Dev Container (Recommended) ⭐

```bash
# 1. Open in VS Code
code /Users/bmstoner/code_projects/ollama_local/markdown-rag-mcp

# 2. Click "Reopen in Container" when prompted
# Or press: Cmd+Shift+P → "Dev Containers: Reopen in Container"

# 3. Wait ~30 seconds for container to start

# 4. Terminal is now inside Docker - start coding!
python src/indexer.py
```

### Option 2: Docker Compose (Command Line)

```bash
# Start container
cd /Users/bmstoner/code_projects/ollama_local/markdown-rag-mcp
make up

# Enter container
make shell

# Inside container:
python src/indexer.py
```

---

## 📚 Essential Documentation

| Document | Purpose |
|----------|---------|
| **[DEV_PRACTICES.md](DEV_PRACTICES.md)** | **Start here!** Complete development guide |
| [README.md](README.md) | Project overview and features |
| [DOCKER_SETUP_COMPLETE.md](DOCKER_SETUP_COMPLETE.md) | What was built and how to use it |

---

## ⚡ Quick Commands (Makefile)

```bash
# Container management
make up          # Start container
make down        # Stop container
make shell       # Enter container
make logs        # View logs

# Operations
make index       # Index your Obsidian vault
make search      # Test search
make server      # Run MCP server

# Development
make format      # Format code (black)
make lint        # Lint code (pylint)
make test        # Run tests

# Help
make help        # Show all commands
```

---

## 🧪 Test Your Setup

```bash
# 1. Verify Docker is running
docker ps

# 2. Build and start (already built!)
make up

# 3. Check Ollama connection
make check-ollama

# 4. Enter container
make shell

# 5. Verify vault access
ls -la /vault

# 6. Index your vault
python src/indexer.py

# 7. Test search
python src/search.py
```

**If all steps work → Setup is complete! 🎉**

---

## 📦 What You Have

### Docker Setup ✅
- **Dockerfile** - Development container
- **docker-compose.yml** - Easy orchestration
- **Makefile** - Convenient commands
- **Image built** - Ready to run

### VS Code Integration ✅
- **.devcontainer/** - Dev Container config
- **.vscode/** - Editor settings
- **Extensions** - Auto-install in container

### Development Tools ✅
- Python 3.11
- Black (formatting)
- Pylint (linting)
- Pytest (testing)
- Jupyter (notebooks)
- IPython (interactive)

### Source Code ✅
- `src/config.py` - Configuration
- `src/parser.py` - Markdown parsing (tags, links, frontmatter)
- `src/indexer.py` - Vault indexing (ChromaDB + Ollama)
- `src/search.py` - Semantic search + RAG
- `src/server.py` - MCP server

### Documentation ✅
- **DEV_PRACTICES.md** - Development guide
- **README.md** - Project overview
- **DOCKER_SETUP_COMPLETE.md** - Setup details

---

## 🎯 Your Workflow

### Daily Development

```bash
# Open VS Code
code /Users/bmstoner/code_projects/ollama_local/markdown-rag-mcp

# Reopen in Container (Cmd+Shift+P)

# Make changes, then:
make format      # Format code
make test        # Run tests
git commit -m "feat: your change"
```

### Testing Changes

```bash
# Inside container (after "Reopen in Container" or "make shell"):

# Test indexer
python src/indexer.py

# Test search
python src/search.py

# Interactive development
ipython

# Run specific script
python examples/rag_example.py
```

---

## 🚨 Troubleshooting

### Container won't start
```bash
make logs
make down && make build && make up
```

### Can't access vault
```bash
# Check docker-compose.yml volume mount:
grep "Obsidian Vault" docker-compose.yml

# Verify path exists:
ls -la "/Users/bmstoner/Documents/Obsidian Vault"
```

### Ollama not reachable
```bash
# Check Ollama is running:
docker ps | grep ollama

# Test from host:
curl http://localhost:11434/api/tags

# Test from container:
make shell
curl http://host.docker.internal:11434/api/tags
```

### Need to rebuild
```bash
make nuke      # Delete everything
make build     # Rebuild image
make up        # Start container
```

---

## 🎓 Learning Path

1. **Read DEV_PRACTICES.md** (5 minutes)
   - Essential development rules
   - Docker-only workflow
   - Code standards

2. **Test Setup** (5 minutes)
   ```bash
   make up
   make check-ollama
   make index
   make search
   ```

3. **Try VS Code Dev Container** (5 minutes)
   - Open in VS Code
   - Reopen in Container
   - Explore the environment

4. **Read Source Code** (30 minutes)
   - Start with `src/config.py`
   - Then `src/parser.py`
   - Then `src/indexer.py`
   - Then `src/search.py`
   - Finally `src/server.py`

5. **Make a Change** (10 minutes)
   - Edit a file
   - Format: `make format`
   - Test: `make test`
   - Commit: `git commit -m "..."`

---

## 🔑 Key Rules

### ⚠️ RULE #1: Docker Only
**NEVER install dependencies locally. ALWAYS use Docker.**

### ✅ Always Format Before Commit
```bash
make format
```

### ✅ Test Your Changes
```bash
make test
```

### ✅ Write Clear Commit Messages
```bash
git commit -m "feat(indexer): add batch processing"
git commit -m "fix(search): handle empty queries"
git commit -m "docs(readme): update setup instructions"
```

---

## 💡 Pro Tips

1. **Use Makefile** - It's faster than typing docker commands
2. **VS Code Dev Container** - Best development experience
3. **Read DEV_PRACTICES.md** - Has all the answers
4. **Keep Docker running** - Faster startup
5. **Use `make shell`** - Quick container access

---

## 📊 Project Stats

- **Language**: Python 3.11
- **Lines of Code**: ~800 (source)
- **Dependencies**: 5 main (mcp, chromadb, pyyaml, requests, aiohttp)
- **Docker Image Size**: ~2GB
- **Build Time**: ~3 minutes (first time)
- **Startup Time**: ~5 seconds

---

## 🎉 You're Ready!

Your development environment is fully set up with:
- ✅ Docker containerization
- ✅ VS Code integration
- ✅ Complete tooling
- ✅ Comprehensive docs
- ✅ Best practices enforced

**Next Step:** Open VS Code and click "Reopen in Container"

---

## 🤝 Need Help?

1. Check [DEV_PRACTICES.md](DEV_PRACTICES.md)
2. Check [DOCKER_SETUP_COMPLETE.md](DOCKER_SETUP_COMPLETE.md)
3. Run `make help`
4. Check container logs: `make logs`

---

**Happy coding! 🚀 Remember: If you're not in Docker, you're doing it wrong! 🐳**



