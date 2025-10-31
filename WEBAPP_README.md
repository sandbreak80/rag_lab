# 🌐 Web UI for RAG Chat

## Quick Start

**Open in your browser:** http://localhost:5000

## Features

✅ **Beautiful Chat Interface** - Modern, responsive design with smooth animations  
✅ **Real-time Streaming** - Watch AI responses appear word-by-word  
✅ **Source Citations** - See which notes were used with relevance scores  
✅ **Loading Indicators** - Know when the system is thinking  
✅ **Mobile Responsive** - Works on any device  

## Starting the Web UI

### Method 1: Direct Command
```bash
docker-compose exec markdown-rag-mcp bash -c "cd /workspace/src && python webapp.py &"
```

### Method 2: Using Makefile
```bash
make webapp
```

### Method 3: Auto-start on Container Launch

Add to `docker-compose.yml`:
```yaml
command: bash -c "cd /workspace/src && python webapp.py"
```

## Accessing the UI

Once started, open: **http://localhost:5000**

## Example Questions

Try asking:
- "Who is Lisa Bobbert?"
- "What are the best practices for prompt engineering?"
- "Tell me about AppDynamics observability features"
- "How does the attention mechanism work in transformers?"
- "What Cisco AI principles should I follow?"

## How It Works

1. **You ask a question** in the chat box
2. **System searches** your vault for relevant notes (RAG retrieval)
3. **Top 3-5 most relevant chunks** are selected
4. **Context is sent to Ollama** with your question
5. **AI generates an answer** based ONLY on your notes
6. **Answer streams in real-time** with source citations

## API Endpoints

### Get Stats
```bash
curl http://localhost:5000/api/stats
```

Returns:
```json
{
  "total_chunks": 1141,
  "embedding_model": "nomic-embed-text",
  "chat_model": "llama3.1:8b",
  "vault_path": "/vault"
}
```

### Search
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI prompting", "limit": 5}'
```

### Ask Question (Streaming)
```bash
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is prompt engineering?", "num_contexts": 3}'
```

## Architecture

```
┌─────────────┐
│   Browser   │
│ (Your UI)   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│   Flask     │
│   webapp.py │
└──────┬──────┘
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌─────────────┐      ┌─────────────┐
│  VaultSearcher│      │   Ollama    │
│  (ChromaDB)  │      │   (LLM)     │
└──────┬───────┘      └─────────────┘
       │
       ▼
┌─────────────┐
│Your Obsidian│
│   Vault     │
└─────────────┘
```

## Port Configuration

- **Default:** Port 5000
- **Change:** Edit `src/webapp.py` line 160:
  ```python
  app.run(host='0.0.0.0', port=5000, debug=False)
  ```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port in webapp.py
```

### Can't Connect
```bash
# Check if webapp is running
curl http://localhost:5000/api/stats

# Check container logs
docker-compose logs markdown-rag-mcp | tail -50
```

### Ollama Timeouts
- Responses may take 30-120 seconds for complex questions
- Using smaller models (`llama3.2:3b`) will be faster
- Increase timeout in `webapp.py` if needed

### No Results Found
```bash
# Re-index your vault
make reindex

# Or manually
docker-compose exec markdown-rag-mcp python src/indexer.py --force
```

## Stopping the Web UI

```bash
# Find the process
docker-compose exec markdown-rag-mcp bash -c "pgrep -f webapp.py"

# Kill it
docker-compose exec markdown-rag-mcp bash -c "pkill -f webapp.py"
```

## Customization

### Change Theme Colors

Edit `src/templates/index.html`:
- Line 15: Background gradient
- Line 86: User message color
- Line 91: Assistant message color
- Line 136: Button color

### Adjust Number of Context Chunks

Edit `src/templates/index.html` line 188:
```javascript
body: JSON.stringify({question, num_contexts: 3})  // Change 3 to desired number
```

### Change Model

Edit `docker-compose.yml`:
```yaml
environment:
  - CHAT_MODEL=llama3.2:3b  # Faster, smaller model
```

## Production Deployment

⚠️ **This is a development server!**

For production, use a proper WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 src.webapp:app
```

Or use nginx as a reverse proxy.

## Security Notes

- Web UI runs on your local machine only
- No authentication (fine for local use)
- Your vault is mounted read-only
- No data leaves your machine
- All processing is local

## Performance

- **Search:** < 1 second
- **LLM Response:** 30-120 seconds (depends on model)
- **Streaming:** Real-time word-by-word
- **Concurrent Users:** 1 (development server)

## What's Next?

- Add conversation history
- Support multiple vaults
- Add advanced filters (tags, dates, etc.)
- Export conversations
- Add authentication
- Deploy with gunicorn/nginx

Enjoy chatting with your knowledge vault! 🚀

