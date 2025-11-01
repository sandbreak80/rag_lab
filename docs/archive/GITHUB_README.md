# 🤖 Ollama Local AI - Complete Setup for Apple Silicon

**One-command installation of a complete local AI development environment**

Run powerful AI models (Llama, Qwen, Gemma, DeepSeek) directly on your Mac with Apple Silicon. No API keys, no cloud services, no costs, 100% private.

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Apple%20Silicon-blue?logo=apple" alt="Platform">
  <img src="https://img.shields.io/badge/Models-8%20Included-green" alt="Models">
  <img src="https://img.shields.io/badge/Cost-%240-success" alt="Cost">
  <img src="https://img.shields.io/badge/Privacy-100%25%20Local-brightgreen" alt="Privacy">
</p>

---

## ⚡ One-Command Setup

```bash
git clone https://github.com/YOUR_USERNAME/ollama_local.git
cd ollama_local
./setup.sh
```

**That's it!** 30-60 minutes later, you'll have everything ready to go.

---

## 🎁 What You Get

### Software Installed
- ✅ **Visual Studio Code** - Apple Silicon optimized
- ✅ **Docker Desktop** - Latest version
- ✅ **Ollama** - Running in Docker

### 8 Production-Ready AI Models (~30GB)
| Model | Size | Best For |
|-------|------|----------|
| **llama3.1:8b** | 4.9GB | General purpose, coding, reasoning |
| **qwen2.5:7b** | 4.7GB | Multilingual, coding |
| **deepseek-r1:7b** | 4.7GB | Advanced reasoning, math |
| **gemma2:9b** | 5.4GB | High performance |
| **llama3.2:3b** | 2.0GB | Fast responses, lightweight |
| **qwen3:4b** | 2.5GB | Balanced performance |
| **nomic-embed-text** | 274MB | Embeddings for RAG |
| **llava:7b** | 4.7GB | Vision/image analysis |

### Code Examples
- ✅ **Interactive Chatbot** with conversation memory
- ✅ **RAG System** (document Q&A)
- ✅ **API Examples** in Python and Bash
- ✅ **Complete Documentation**

---

## 🚀 Quick Start

### After Installation

```bash
# Check everything is running
docker ps | grep ollama

# List available models
docker exec ollama ollama list

# Try interactive chat
docker exec -it ollama ollama run llama3.1:8b

# Run Python chatbot
cd examples
python3 chatbot.py

# Try RAG example
python3 rag_example.py
```

---

## 📋 Requirements

- 💻 **Mac with Apple Silicon** (M1, M2, M3, M4)
- 💾 **50GB free disk space**
- 🌐 **Internet connection** (for initial download)
- 🍎 **macOS** (any recent version)

**Recommended:** 16GB+ RAM for best performance

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [**SETUP.md**](SETUP.md) | Complete installation guide |
| [**QUICK_START_API.md**](QUICK_START_API.md) | Fast intro to the API |
| [**API_GUIDE.md**](API_GUIDE.md) | Complete API reference |
| [**examples/README.md**](examples/README.md) | Guide to all examples |
| [**PERSISTENCE_EXPLAINED.md**](PERSISTENCE_EXPLAINED.md) | How upgrades work |

---

## 🎯 What You Can Build

With this setup, you can create:

- 🤖 **Chatbots** - Customer support, personal assistants
- 📝 **Content Generators** - Blogs, emails, social media posts
- 💻 **Code Assistants** - Generate, explain, and debug code
- 📄 **Document Q&A** - Chat with your PDFs and documents
- 🔍 **Semantic Search** - Intelligent content discovery
- 📊 **Data Analysis Tools** - Explain patterns and insights
- 🌍 **Translation Services** - Multi-language support
- 🖼️ **Image Analysis** - Describe and analyze images
- 🧠 **Knowledge Bases** - RAG over your private data
- 🎨 **Creative Tools** - Writing assistance, brainstorming

---

## 💡 Example Usage

### Simple Text Generation

```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.1:8b",
    "prompt": "Explain Docker in simple terms",
    "stream": False
})

print(response.json()['response'])
```

### Chat with Context

```python
import requests

messages = [
    {"role": "system", "content": "You are a helpful coding assistant"},
    {"role": "user", "content": "How do I use Python requests?"}
]

response = requests.post('http://localhost:11434/api/chat', json={
    "model": "llama3.1:8b",
    "messages": messages,
    "stream": False
})

print(response.json()['message']['content'])
```

### Generate Embeddings (for RAG)

```python
import requests

response = requests.post('http://localhost:11434/api/embeddings', json={
    "model": "nomic-embed-text",
    "prompt": "Machine learning is transforming technology"
})

embeddings = response.json()['embedding']  # 768-dimensional vector
```

---

## 🔧 Maintenance

### Upgrade Ollama
```bash
./upgrade_ollama.sh
```

### Update Models
```bash
./check_model_updates.sh
```

### Add More Models
```bash
docker exec ollama ollama pull mistral:7b
```

---

## 🌐 API Endpoint

Once running, the Ollama API is available at:

```
http://localhost:11434
```

**Available Endpoints:**
- `/api/generate` - Text generation
- `/api/chat` - Multi-turn conversations
- `/api/embeddings` - Vector embeddings
- `/api/tags` - List models
- `/api/show` - Model information

See [API_GUIDE.md](API_GUIDE.md) for complete documentation.

---

## 📊 Performance

On Apple Silicon (M2 Pro with 16GB RAM):

| Model Size | Response Time | Tokens/sec |
|------------|---------------|------------|
| 3-4B | ~1-2s | 30-40 |
| 7-9B | ~2-4s | 15-25 |

**Recommendation:** Run one 7-9B model at a time, or 2-3 smaller (3-4B) models.

---

## 🔐 Privacy & Security

✅ **100% Local Processing** - Your data never leaves your Mac  
✅ **No API Keys Required** - No signup, no tracking  
✅ **No Cloud Dependencies** - Works completely offline  
✅ **Open Source** - Transparent, auditable code  
✅ **No Telemetry** - Zero data collection  

---

## 💰 Cost Comparison

| Service | Monthly Cost | Privacy | This Setup |
|---------|--------------|---------|------------|
| OpenAI GPT-4 | $20-100+ | ❌ Cloud | ✅ **$0** |
| Anthropic Claude | $20-100+ | ❌ Cloud | ✅ **$0** |
| Google Gemini | $0-50+ | ❌ Cloud | ✅ **$0** |
| **Ollama Local** | **$0** | **✅ Local** | **✅ This!** |

**Unlimited usage. Zero ongoing costs.**

---

## 🎓 Learning Path

1. **Day 1:** Run `./setup.sh` and try the chatbot
2. **Day 2:** Read [QUICK_START_API.md](QUICK_START_API.md)
3. **Day 3:** Try the RAG example
4. **Day 4:** Read [API_GUIDE.md](API_GUIDE.md)
5. **Day 5:** Build your first app!

---

## 🐛 Troubleshooting

### Docker not starting?
```bash
open -a Docker
# Wait 30 seconds
docker ps
```

### Models not downloading?
```bash
# Check disk space
df -h

# Try pulling one model
docker exec ollama ollama pull llama3.1:8b
```

### Python examples failing?
```bash
pip3 install -r requirements.txt
```

See [SETUP.md](SETUP.md) for more troubleshooting tips.

---

## 🤝 Contributing

Contributions welcome! Feel free to:
- Add new examples
- Improve documentation
- Report issues
- Suggest features

---

## 📜 License

MIT License - feel free to use this in your own projects!

---

## ⭐ Star This Repo

If this helped you, please star the repo to help others discover it!

---

## 🙏 Acknowledgments

Built on top of these amazing projects:
- [Ollama](https://ollama.com/) - Local LLM runtime
- [Docker](https://www.docker.com/) - Container platform
- Model creators: Meta, Alibaba, Google, DeepSeek, and others

---

## 📞 Quick Links

- 📖 [Complete Setup Guide](SETUP.md)
- 🚀 [API Quick Start](QUICK_START_API.md)
- 📚 [API Documentation](API_GUIDE.md)
- 💻 [Code Examples](examples/)
- 🔄 [How Persistence Works](PERSISTENCE_EXPLAINED.md)

---

<p align="center">
  <strong>Ready to run AI models locally?</strong><br>
  <code>git clone https://github.com/YOUR_USERNAME/ollama_local.git && cd ollama_local && ./setup.sh</code>
</p>

<p align="center">
  Made with ❤️ for the local AI community
</p>

