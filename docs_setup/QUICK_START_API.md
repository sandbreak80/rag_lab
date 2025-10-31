# 🎯 Quick Start: Building with Ollama API

## Yes! Ollama Exposes a Full REST API

**Endpoint:** `http://localhost:11434`  
**Port:** `11434` (exposed by Docker)  
**Format:** JSON REST API  
**Authentication:** None (local only)

---

## ⚡ 30-Second Test

```bash
# Simple text generation
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Say hello in 5 languages",
  "stream": false
}'
```

---

## 🚀 What You Can Build

### ✅ **You Have Everything You Need!**

1. **8 Production-Ready Models** (~30GB)
   - General purpose (llama3.1, gemma2)
   - Reasoning (deepseek-r1)
   - Fast responses (llama3.2, qwen3)
   - Embeddings (nomic-embed-text)
   - Vision (llava)

2. **Full REST API** on port 11434
   - `/api/generate` - Text generation
   - `/api/chat` - Conversations
   - `/api/embeddings` - Vector embeddings
   - `/api/tags` - List models
   - And more...

3. **Example Code** in `/examples/`
   - Python API examples
   - Bash/curl examples
   - Interactive chatbot
   - RAG (document Q&A)

---

## 📦 Included Examples

### 1. **Basic API Usage**
```bash
cd examples
./api_examples.sh        # Bash version
python3 api_examples.py  # Python version
```

**Shows:**
- Text generation
- Chat with context
- Embeddings
- Streaming responses

### 2. **Interactive Chatbot**
```bash
python3 chatbot.py
```

**Features:**
- Multi-turn conversations
- Conversation memory
- Custom system prompts
- Commands: /clear, /history, /quit

### 3. **RAG (Document Q&A)**
```bash
python3 rag_example.py
```

**Demonstrates:**
- Building a knowledge base
- Semantic search
- Context-aware answers
- Production-ready pattern

---

## 🎨 5-Minute Projects

### Project 1: Simple Text Generator

```python
import requests

def generate(prompt):
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    })
    return response.json()['response']

print(generate("Write a haiku about coding"))
```

### Project 2: Chatbot with Memory

```python
import requests

class Bot:
    def __init__(self):
        self.messages = []
    
    def chat(self, msg):
        self.messages.append({"role": "user", "content": msg})
        
        response = requests.post('http://localhost:11434/api/chat', json={
            "model": "llama3.1:8b",
            "messages": self.messages,
            "stream": False
        })
        
        reply = response.json()['message']['content']
        self.messages.append({"role": "assistant", "content": reply})
        return reply

bot = Bot()
print(bot.chat("Hello!"))
print(bot.chat("What did I say?"))  # Has context!
```

### Project 3: Semantic Search

```python
import requests
import numpy as np

def embed(text):
    response = requests.post('http://localhost:11434/api/embeddings', json={
        "model": "nomic-embed-text",
        "prompt": text
    })
    return response.json()['embedding']

def similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

# Build knowledge base
docs = ["Python is great", "Docker is powerful", "AI is amazing"]
doc_embeddings = [embed(d) for d in docs]

# Search
query = "Tell me about containers"
query_emb = embed(query)

scores = [similarity(query_emb, d_emb) for d_emb in doc_embeddings]
best = docs[scores.index(max(scores))]
print(f"Best match: {best}")
```

---

## 🌐 Production Use Cases

### Already Possible With Your Setup:

✅ **Chatbots** - Customer support, assistants  
✅ **Content Generation** - Blog posts, emails, docs  
✅ **Code Assistant** - Generate, explain, debug code  
✅ **Document Q&A** - Chat with PDFs, search docs  
✅ **Semantic Search** - Find similar content  
✅ **Summarization** - Condense long texts  
✅ **Translation** - Multi-language support  
✅ **Data Analysis** - Explain patterns, insights  
✅ **Image Analysis** - With llava model  
✅ **Knowledge Base** - RAG over your data  

---

## 📚 Documentation Structure

```
ollama_local/
├── README.md                    # Main documentation
├── API_GUIDE.md                 # Complete API reference
├── PERSISTENCE_EXPLAINED.md     # How data persistence works
│
├── pull_models.sh               # Download models
├── upgrade_ollama.sh            # Upgrade Ollama
├── check_model_updates.sh       # Update models
│
└── examples/
    ├── README.md                # Examples guide
    ├── api_examples.sh          # Bash examples
    ├── api_examples.py          # Python examples
    ├── chatbot.py               # Interactive chatbot
    └── rag_example.py           # RAG implementation
```

---

## 🎯 Your Next Steps

### Option 1: Learn the API
```bash
cd examples
./api_examples.sh          # See what's possible
python3 api_examples.py    # Python version
```

### Option 2: Interactive Experience
```bash
python3 chatbot.py         # Chat with AI
python3 chatbot.py --demo  # See demo conversation
```

### Option 3: Build Something
```bash
python3 rag_example.py     # Learn RAG pattern
# Then modify it for your use case!
```

### Option 4: Read Documentation
```bash
cat API_GUIDE.md           # Complete API docs
cat examples/README.md     # Example explanations
```

---

## 🔥 API Highlights

### 1. Text Generation
```python
requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.1:8b",
    "prompt": "Your prompt"
})
```

### 2. Chat (with context)
```python
requests.post('http://localhost:11434/api/chat', json={
    "model": "llama3.1:8b",
    "messages": [
        {"role": "user", "content": "Hello"}
    ]
})
```

### 3. Embeddings
```python
requests.post('http://localhost:11434/api/embeddings', json={
    "model": "nomic-embed-text",
    "prompt": "Your text"
})
```

### 4. Streaming
```python
requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.1:8b",
    "prompt": "Count to 10",
    "stream": True  # ← Real-time tokens
}, stream=True)
```

---

## 💡 Pro Tips

1. **Start small** - Use `llama3.2:3b` for testing
2. **Enable streaming** - Better user experience
3. **Cache embeddings** - Generate once, reuse
4. **Monitor memory** - 16GB = 1 large model at a time
5. **Check examples** - Copy and modify working code

---

## 🚨 Common Questions

**Q: Is the API ready to use?**  
✅ Yes! It's running on `http://localhost:11434`

**Q: Do I need to install anything?**  
✅ Just Python and `requests` library: `pip install requests`

**Q: Can I use it in production?**  
✅ Yes, but add authentication/rate-limiting

**Q: What models should I use?**  
- Quick queries: `llama3.2:3b`
- Complex tasks: `llama3.1:8b`
- Embeddings: `nomic-embed-text`

**Q: Is it fast enough?**  
✅ Yes! M2 chip handles 7-8B models well

**Q: Can I build a web app?**  
✅ Yes! See FastAPI/Flask examples in `API_GUIDE.md`

---

## 🎓 Learning Resources

1. **Start Here:** `examples/api_examples.sh`
2. **Python Basics:** `examples/api_examples.py`
3. **Chat App:** `examples/chatbot.py`
4. **Advanced:** `examples/rag_example.py`
5. **Full Docs:** `API_GUIDE.md`

---

## ✅ Summary

You have a **fully functional LLM API** with:

- ✅ 8 production models (30GB)
- ✅ REST API on port 11434
- ✅ Python & Bash examples
- ✅ Complete documentation
- ✅ RAG implementation
- ✅ Interactive chatbot
- ✅ Zero cost (runs locally)
- ✅ No external API calls
- ✅ Private & secure

**Start building now! 🚀**

```bash
cd /Users/bmstoner/code_projects/ollama_local/examples
python3 chatbot.py
```

