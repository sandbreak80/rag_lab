# 🤖 Markdown RAG MCP Server

**Universal Markdown RAG with Semantic Search + Metadata Filtering**

A Model Context Protocol (MCP) server that provides intelligent search and retrieval over any markdown vault (Obsidian, Notion exports, etc.) using local AI via Ollama.

---

## ⚠️ Development Environment: Docker Only!

**This project enforces containerized development. DO NOT install dependencies locally.**

✅ **Benefits:**
- Clean host system (no pollution)
- Consistent environment
- One-command setup
- Works on any machine

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [VS Code](https://code.visualstudio.com/)
- [Remote-Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- [Ollama](http://localhost:11434) running with models installed

### Setup (2 minutes)

1. **Clone and Open**
   ```bash
   git clone <repo-url>
   cd markdown-rag-mcp
   code .
   ```

2. **Reopen in Container**
   - VS Code will prompt: "Reopen in Container" → **Click it**
   - Wait ~3 minutes for first build
   - ☕ Grab coffee

3. **Index Your Vault**
   ```bash
   # Terminal is now inside container!
   python src/indexer.py
   ```

4. **Test Search**
   ```bash
   python src/search.py
   ```

**That's it!** 🎉

---

## 🎯 Features

### Core Capabilities

- ✅ **Semantic Search** - Find notes by meaning, not just keywords
- ✅ **RAG (Retrieval-Augmented Generation)** - Ask questions, get AI answers
- ✅ **Metadata Filtering** - Search by tags, folders, dates
- ✅ **Link Awareness** - Parse and track wikilinks `[[like this]]`
- ✅ **Universal Markdown** - Works with any markdown vault
- ✅ **Ollama Integration** - Local AI, no API keys needed
- ✅ **MCP Protocol** - Works with Claude Desktop, Cursor, etc.

### MCP Tools

| Tool | Description |
|------|-------------|
| `search_notes` | Semantic search with optional filtering |
| `ask_vault` | RAG-based Q&A over your notes |
| `find_similar` | Find notes similar to a given note |
| `find_linked` | Get wikilink connections |
| `summarize_topic` | AI summary of all notes on a topic |
| `get_vault_stats` | Index statistics |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           MCP Server (Claude/Cursor)            │
└─────────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐   ┌───▼────┐   ┌──▼────┐
   │ Search │   │  RAG   │   │ Index │
   └────┬───┘   └───┬────┘   └──┬────┘
        │           │            │
        └───────────┼────────────┘
                    │
          ┌─────────▼──────────┐
          │   ChromaDB         │
          │   (Vector Store)   │
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │   Ollama           │
          │   • nomic-embed    │
          │   • llama3.1:8b    │
          └────────────────────┘
```

**Key Components:**
- **Parser** - Extracts markdown, frontmatter, tags, links
- **Indexer** - Builds vector index using Ollama embeddings
- **Searcher** - Semantic + metadata search
- **Server** - MCP protocol implementation

---

## 📦 Project Structure

```
markdown-rag-mcp/
├── 🐳 Docker Setup
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .devcontainer/
│       └── devcontainer.json
│
├── 🐍 Source Code
│   ├── src/
│   │   ├── config.py         # Configuration
│   │   ├── parser.py          # Markdown parsing
│   │   ├── indexer.py         # Vault indexing
│   │   ├── search.py          # Search engine
│   │   └── server.py          # MCP server
│
├── 📚 Documentation
│   ├── README.md              # This file
│   ├── DEV_PRACTICES.md       # Development guide
│   └── docs/
│
├── 🧪 Tests
│   └── tests/
│
├── 📊 Data (gitignored, in Docker volumes)
│   └── indices/               # Vector store
│
└── ⚙️ Configuration
    ├── requirements.txt
    ├── .gitignore
    └── .vscode/
```

---

## 🔧 Usage

### Inside Container (Dev)

```bash
# Index vault
python src/indexer.py

# Force re-index
python src/indexer.py --force

# Test search
python src/search.py

# Run MCP server
python src/server.py
```

### With Docker Compose (Standalone)

```bash
# Start container
docker-compose up -d

# Run indexer
docker-compose exec markdown-rag-mcp python src/indexer.py

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### With Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "markdown-rag": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/Users/bmstoner/Documents/Obsidian Vault:/vault:ro",
        "-v",
        "markdown-rag-indices:/workspace/indices",
        "-e",
        "VAULT_PATH=/vault",
        "-e",
        "OLLAMA_BASE_URL=http://host.docker.internal:11434",
        "markdown-rag-mcp:latest",
        "python",
        "src/server.py"
      ]
    }
  }
}
```

---

## ⚙️ Configuration

Set via environment variables (in `docker-compose.yml` or `.devcontainer/devcontainer.json`):

| Variable | Default | Description |
|----------|---------|-------------|
| `VAULT_PATH` | `/vault` | Path to markdown vault |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama API URL |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `CHAT_MODEL` | `llama3.1:8b` | Chat model for RAG |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `DEFAULT_SEARCH_LIMIT` | `10` | Max search results |

---

## 📖 Development

### Read This First!
**[DEV_PRACTICES.md](DEV_PRACTICES.md)** - Complete development guide

### Daily Workflow

```bash
# 1. Open VS Code → Reopen in Container
code .

# 2. Make changes
# (Edit code in VS Code)

# 3. Format
black src/

# 4. Test
pytest

# 5. Commit
git commit -m "feat: your change"
```

### Key Commands

```bash
# Format code
black src/

# Lint
pylint src/

# Run tests
pytest

# Type check
mypy src/

# Interactive Python
ipython
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src tests/

# Specific test
pytest tests/test_parser.py::test_parse_frontmatter
```

---

## 🚨 Troubleshooting

### Container won't start
```bash
docker-compose logs
docker-compose down && docker-compose up -d --build
```

### Can't connect to Ollama
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Test from container
docker-compose exec markdown-rag-mcp \
  curl http://host.docker.internal:11434/api/tags
```

### Index not found
```bash
# Build index
python src/indexer.py

# Or force rebuild
python src/indexer.py --force
```

---

## 📊 Performance

**Typical benchmarks (M2 Pro, 16GB):**
- Index 1000 notes: ~30 seconds
- Search query: <500ms
- RAG generation: 2-5 seconds
- Memory usage: ~2GB

**For 5000+ notes:**
- Use batch indexing
- Consider index sharding
- Monitor with `docker stats`

---

## 🤝 Contributing

1. Read [DEV_PRACTICES.md](DEV_PRACTICES.md)
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes (in Docker container!)
4. Format + test: `black src/ && pytest`
5. Commit: `git commit -m "feat: description"`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **Ollama** - Local AI runtime
- **ChromaDB** - Vector database
- **MCP** - Model Context Protocol
- **Obsidian** - Inspiration for markdown vaults

---

## 🔗 Links

- [Ollama](https://ollama.ai)
- [MCP Documentation](https://modelcontextprotocol.io)
- [ChromaDB](https://www.trychroma.com/)

---

<p align="center">
  <strong>🐳 Remember: Docker-only development!</strong><br>
  <sub>Keep your system clean, keep your team happy</sub>
</p>



