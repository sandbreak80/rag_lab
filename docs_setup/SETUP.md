# 🚀 Ollama Local AI Setup for Apple Silicon

**Complete AI development environment running locally on your Mac**

One command to install everything: VS Code, Docker, Ollama, and 8 production-ready AI models.

---

## 📋 What You Get

✅ **Visual Studio Code** - Latest version for Apple Silicon  
✅ **Docker Desktop** - Container platform  
✅ **Ollama** - Local AI runtime  
✅ **8 AI Models** (~30GB) - Ready to use:
   - llama3.1:8b - General purpose, coding
   - qwen2.5:7b - Multilingual, coding
   - deepseek-r1:7b - Advanced reasoning
   - gemma2:9b - High performance
   - llama3.2:3b - Fast responses
   - qwen3:4b - Balanced performance
   - nomic-embed-text - Embeddings/RAG
   - llava:7b - Vision/image analysis

✅ **Working Examples** - Python code to get started  
✅ **Complete Documentation** - API guides and tutorials  
✅ **Zero Costs** - Everything runs locally  

---

## ⚡ Quick Install (One Command)

```bash
git clone <YOUR_REPO_URL>
cd ollama_local
./setup.sh
```

**That's it!** The script will:
1. Install Homebrew (if needed)
2. Install VS Code
3. Install Docker Desktop
4. Install Obsidian + Local REST API plugin
5. Deploy Ollama container
6. Download all 8 AI models
7. Create Obsidian vault at `~/obsidian_vault`
8. Install Node.js + Obsidian MCP server
9. Create integration examples (chat with notes!)
10. Install Python dependencies
11. Validate the setup
12. Run example tests

**Time:** 30-60 minutes (mostly downloading models)

---

## 📱 System Requirements

### Required
- 💻 **Mac with Apple Silicon** (M1, M2, M3, M4)
- 💾 **50GB free disk space** (30GB for models + overhead)
- 🌐 **Internet connection** (for initial download)
- 🍎 **macOS** (any recent version)

### Recommended
- 💾 **16GB+ RAM** (for running 7-9B models comfortably)
- 📶 **Fast internet** (downloading 30GB of models)

---

## 🛠️ Manual Installation (If You Prefer)

If you prefer to install components manually:

### Step 1: Install Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install VS Code
```bash
brew install --cask visual-studio-code
```

### Step 3: Install Docker Desktop
```bash
brew install --cask docker
open -a Docker  # Start Docker Desktop
```

### Step 4: Deploy Ollama
```bash
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  ollama/ollama
```

### Step 5: Download Models
```bash
./pull_models.sh
```

### Step 6: Install Python Dependencies
```bash
pip3 install --user requests numpy
```

### Step 7: Validate
```bash
docker exec ollama ollama list
python3 examples/chatbot.py --demo
```

---

## 🎯 Quick Start After Installation

### Test the Setup
```bash
# Check if everything is running
docker ps | grep ollama

# List available models
docker exec ollama ollama list

# Quick test
docker exec ollama ollama run llama3.1:8b "Say hello!"
```

### Try the Examples

#### 1. Interactive Chatbot
```bash
cd examples
python3 chatbot.py
```

#### 2. RAG (Document Q&A)
```bash
python3 rag_example.py
```

#### 3. API Examples
```bash
./api_examples.sh
python3 api_examples.py
```

### Open in VS Code
```bash
code .
```

---

## 📚 Documentation

Once installed, check out these guides:

| Document | Description |
|----------|-------------|
| **QUICK_START_API.md** | Fast intro to building with the API |
| **API_GUIDE.md** | Complete API reference with examples |
| **examples/README.md** | Guide to all code examples |
| **PERSISTENCE_EXPLAINED.md** | How upgrades work |
| **README.md** | Main documentation |

---

## 🔧 Maintenance Commands

### Upgrade Ollama
```bash
./upgrade_ollama.sh
```

### Check for Model Updates
```bash
./check_model_updates.sh
```

### Restart Ollama
```bash
docker restart ollama
```

### View Logs
```bash
docker logs ollama
```

---

## 🚨 Troubleshooting

### Docker Not Starting
```bash
# Open Docker Desktop manually
open -a Docker

# Wait 30 seconds, then try again
docker ps
```

### Models Not Downloading
```bash
# Check internet connection
# Check disk space: df -h
# Try pulling one model manually
docker exec ollama ollama pull llama3.1:8b
```

### Python Examples Not Working
```bash
# Install dependencies
pip3 install --user requests numpy

# Or use python3 -m pip
python3 -m pip install --user requests numpy
```

### Port Already in Use
```bash
# Check what's using port 11434
lsof -i :11434

# Stop the process or change Ollama port
```

### Out of Memory
```bash
# Use smaller models (3-4B)
docker exec -it ollama ollama run llama3.2:3b

# Close other applications
# Restart Docker Desktop
```

---

## 💡 What You Can Build

This setup enables you to build:

- 🤖 **Chatbots** - Customer support, personal assistants
- 📝 **Content Generators** - Blogs, emails, social media
- 💻 **Code Assistants** - Generate, explain, debug code
- 📄 **Document Q&A** - Chat with your PDFs and documents
- 🔍 **Semantic Search** - Find similar content intelligently
- 📊 **Data Analysis** - Explain patterns and insights
- 🌍 **Translation** - Multi-language support
- 🖼️ **Image Analysis** - Describe and analyze images
- 🧠 **Knowledge Bases** - RAG over your data
- 🎨 **Creative Tools** - Writing, brainstorming, ideation

---

## 📊 Project Structure

```
ollama_local/
├── 📘 SETUP.md                    ← You are here!
├── 📕 QUICK_START_API.md          ← Start building
├── 📗 API_GUIDE.md                ← Complete API docs
├── 📙 README.md                   ← Main documentation
├── 📄 PERSISTENCE_EXPLAINED.md    ← How it works
│
├── 🚀 setup.sh                    ← One-command installer
├── 🔧 pull_models.sh              ← Download models
├── ⬆️  upgrade_ollama.sh          ← Upgrade Ollama
├── 🔄 check_model_updates.sh      ← Update models
│
└── 💻 examples/
    ├── 📘 README.md               ← Examples guide
    ├── api_examples.sh            ← Bash examples
    ├── api_examples.py            ← Python examples
    ├── chatbot.py                 ← Interactive chatbot
    └── rag_example.py             ← RAG implementation
```

---

## 🔐 Privacy & Security

✅ **100% Local** - All processing on your Mac  
✅ **No Cloud API Calls** - Your data never leaves your machine  
✅ **No API Keys Required** - No signup, no tracking  
✅ **Offline Capable** - Works without internet (after setup)  
✅ **Open Source** - Transparent, auditable code  

---

## 🤝 Sharing This Project

### Option 1: Share via GitHub

```bash
# Create a repo and push
git init
git add .
git commit -m "Initial commit: Ollama local AI setup"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

Then share: `git clone <YOUR_REPO_URL> && cd ollama_local && ./setup.sh`

### Option 2: Share as ZIP

```bash
# Create a zip file
zip -r ollama_local.zip ollama_local/

# Share the zip file
# Recipient extracts and runs: ./setup.sh
```

### Option 3: Direct Download Script

Create a one-liner for recipients:

```bash
curl -fsSL <YOUR_RAW_SETUP_URL> | bash
```

---

## 💰 Cost Comparison

| Service | Cost | Privacy | Speed | This Setup |
|---------|------|---------|-------|------------|
| OpenAI GPT-4 | $10-100+/mo | ❌ Cloud | ⚡⚡⚡ | ✅ $0 |
| Anthropic Claude | $20-100+/mo | ❌ Cloud | ⚡⚡⚡ | ✅ $0 |
| Google Gemini | $0-50+/mo | ❌ Cloud | ⚡⚡⚡ | ✅ $0 |
| **Ollama Local** | **$0** | **✅ Local** | **⚡⚡** | **This!** |

**One-time setup, unlimited usage, zero ongoing costs.**

---

## 🎓 Learning Path

After installation, follow this path:

1. **Day 1:** Run `python3 examples/chatbot.py` - Get familiar
2. **Day 2:** Read `QUICK_START_API.md` - Understand the API
3. **Day 3:** Run `python3 examples/rag_example.py` - Learn RAG
4. **Day 4:** Read `API_GUIDE.md` - Deep dive
5. **Day 5:** Build your first app!

---

## 🆘 Getting Help

1. **Check Documentation** - Most answers are in the docs
2. **Run Examples** - See working code
3. **Review Logs** - `docker logs ollama`
4. **Test Components** - Verify each part works
5. **Check GitHub Issues** - Community solutions

---

## 🎉 Success Checklist

After running `./setup.sh`, verify:

- ✅ VS Code opens
- ✅ Docker Desktop is running
- ✅ `docker ps` shows ollama container
- ✅ `docker exec ollama ollama list` shows 8 models
- ✅ `curl http://localhost:11434` responds
- ✅ `python3 examples/chatbot.py --demo` works
- ✅ Models generate text successfully

---

## 📈 What's Next?

Now that you have a local AI setup:

1. **Explore Examples** - Try all example scripts
2. **Read API Docs** - Understand capabilities
3. **Build Something** - Start your first project
4. **Customize** - Add more models, tweak settings
5. **Share** - Help others set up their environment

---

## 🌟 Why This Setup?

- ✅ **Complete** - Everything you need in one package
- ✅ **Automated** - One command does it all
- ✅ **Production-Ready** - Real models, real examples
- ✅ **Well-Documented** - Comprehensive guides
- ✅ **Maintainable** - Easy to upgrade and update
- ✅ **Private** - Your data stays on your machine
- ✅ **Free** - No ongoing costs

---

## 📞 Installation Command

Share this with anyone who wants to set up:

```bash
git clone <YOUR_REPO_URL>
cd ollama_local
./setup.sh
```

**30-60 minutes later, they'll have a complete local AI development environment!**

---

**Ready to start? Run `./setup.sh` now!** 🚀

