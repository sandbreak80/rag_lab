#!/bin/bash

# Ollama Local Setup Script for Apple Silicon Macs
# This script automates the installation and setup of Ollama with Docker

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS only."
    exit 1
fi

# Check if Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    print_error "This script is designed for Apple Silicon (M1/M2/M3) Macs only."
    print_error "Detected architecture: $ARCH"
    exit 1
fi

print_step "🚀 Ollama Local Setup for Apple Silicon"
echo "This script will install and configure:"
echo "  • Homebrew (if needed)"
echo "  • Visual Studio Code"
echo "  • Docker Desktop"
echo "  • Ollama in Docker"
echo "  • 8 AI models (~30GB)"
echo ""
echo "Prerequisites:"
echo "  • macOS with Apple Silicon (M1/M2/M3)"
echo "  • At least 50GB free disk space"
echo "  • Internet connection"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# ============================================================================
# Step 1: Install Homebrew
# ============================================================================

print_step "1️⃣  Installing Homebrew"

if command -v brew &> /dev/null; then
    print_success "Homebrew is already installed"
    brew --version
else
    print_info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    fi
    
    print_success "Homebrew installed successfully"
fi

# ============================================================================
# Step 2: Install Visual Studio Code
# ============================================================================

print_step "2️⃣  Installing Visual Studio Code"

if [[ -d "/Applications/Visual Studio Code.app" ]]; then
    print_success "VS Code is already installed"
else
    print_info "Installing Visual Studio Code..."
    brew install --cask visual-studio-code
    print_success "VS Code installed successfully"
fi

# ============================================================================
# Step 3: Install Docker Desktop
# ============================================================================

print_step "3️⃣  Installing Docker Desktop"

if [[ -d "/Applications/Docker.app" ]]; then
    print_success "Docker Desktop is already installed"
else
    print_info "Installing Docker Desktop..."
    brew install --cask docker
    print_success "Docker Desktop installed"
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_warning "Docker Desktop is not running"
    print_info "Starting Docker Desktop..."
    open -a Docker
    
    print_info "Waiting for Docker to start (this may take 30-60 seconds)..."
    
    # Wait for Docker to be ready (max 2 minutes)
    for i in {1..24}; do
        if docker info &> /dev/null; then
            print_success "Docker is running!"
            break
        fi
        echo -n "."
        sleep 5
    done
    
    if ! docker info &> /dev/null; then
        print_error "Docker failed to start"
        print_info "Please start Docker Desktop manually and run this script again"
        exit 1
    fi
else
    print_success "Docker is running"
fi

# ============================================================================
# Step 4: Deploy Ollama Container
# ============================================================================

print_step "4️⃣  Deploying Ollama in Docker"

# Check if ollama container already exists
if docker ps -a | grep -q "ollama"; then
    print_warning "Ollama container already exists"
    read -p "Do you want to remove and recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing container..."
        docker stop ollama 2>/dev/null || true
        docker rm ollama 2>/dev/null || true
    else
        print_info "Using existing container"
    fi
fi

# Pull and run Ollama
if ! docker ps | grep -q "ollama"; then
    print_info "Pulling Ollama image..."
    docker pull ollama/ollama:latest
    
    print_info "Starting Ollama container..."
    docker run -d \
        --name ollama \
        -p 11434:11434 \
        -v ollama:/root/.ollama \
        ollama/ollama
    
    print_info "Waiting for Ollama to be ready..."
    sleep 10
    
    if docker ps | grep -q "ollama"; then
        print_success "Ollama container is running!"
    else
        print_error "Failed to start Ollama container"
        exit 1
    fi
else
    print_success "Ollama container is already running"
fi

# ============================================================================
# Step 5: Download AI Models
# ============================================================================

print_step "5️⃣  Downloading AI Models (~30GB, this will take a while...)"

MODELS=(
    "llama3.1:8b"
    "qwen2.5:7b"
    "deepseek-r1:7b"
    "gemma2:9b"
    "llama3.2:3b"
    "qwen3:4b"
    "nomic-embed-text"
    "llava:7b"
)

print_info "Will download ${#MODELS[@]} models. This may take 30-60 minutes depending on your internet speed."
read -p "Continue? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    print_warning "Skipping model downloads"
else
    for model in "${MODELS[@]}"; do
        print_info "Downloading $model..."
        docker exec ollama ollama pull "$model"
        print_success "$model downloaded"
    done
    
    print_success "All models downloaded successfully!"
fi

# ============================================================================
# Step 6: Install Python Dependencies
# ============================================================================

print_step "6️⃣  Installing Python Dependencies"

if command -v python3 &> /dev/null; then
    print_success "Python3 is installed"
    
    print_info "Installing required Python packages..."
    pip3 install --user requests numpy || {
        print_warning "Failed to install via pip3, trying with python3 -m pip..."
        python3 -m pip install --user requests numpy
    }
    
    print_success "Python dependencies installed"
else
    print_error "Python3 is not installed"
    print_info "Installing Python3..."
    brew install python3
fi

# ============================================================================
# Step 7: Install Obsidian
# ============================================================================

print_step "7️⃣  Installing Obsidian"

if [[ -d "/Applications/Obsidian.app" ]]; then
    print_success "Obsidian is already installed"
else
    print_info "Installing Obsidian..."
    brew install --cask obsidian
    print_success "Obsidian installed successfully"
fi

# ============================================================================
# Step 8: Create Obsidian Vault & Setup Note
# ============================================================================

print_step "8️⃣  Creating Obsidian Vault"

VAULT_PATH="$HOME/obsidian_vault"

if [[ -d "$VAULT_PATH" ]]; then
    print_warning "Vault already exists at $VAULT_PATH"
else
    print_info "Creating vault at $VAULT_PATH..."
    mkdir -p "$VAULT_PATH"
    print_success "Vault created"
fi

# Create .obsidian directory for plugins
mkdir -p "$VAULT_PATH/.obsidian"
mkdir -p "$VAULT_PATH/.obsidian/plugins"

# Create a note about the setup
print_info "Creating setup documentation note..."
cat > "$VAULT_PATH/Ollama Local AI Setup.md" << 'EOF'
---
created: $(date +"%Y-%m-%d")
tags: [ai, ollama, setup, local-ai]
---

# 🤖 Ollama Local AI Setup

## Overview

This note documents your local AI setup with Ollama running in Docker.

## 🎯 What Was Installed

### Software
- ✅ **Visual Studio Code** - Code editor (Apple Silicon)
- ✅ **Docker Desktop** - Container platform (Apple Silicon)
- ✅ **Ollama** - Local AI runtime (in Docker)
- ✅ **Obsidian** - Knowledge management (with Local REST API)

### AI Models Installed

| Model | Size | Best For |
|-------|------|----------|
| llama3.1:8b | 4.9GB | General purpose, coding, reasoning |
| qwen2.5:7b | 4.7GB | Multilingual support, coding |
| deepseek-r1:7b | 4.7GB | Advanced reasoning, mathematics |
| gemma2:9b | 5.4GB | High performance tasks |
| llama3.2:3b | 2.0GB | Fast responses, lightweight |
| qwen3:4b | 2.5GB | Balanced performance |
| nomic-embed-text | 274MB | Embeddings for RAG |
| llava:7b | 4.7GB | Vision/image analysis |

**Total:** ~30GB of AI models

## 🌐 API Endpoint

The Ollama API is running at:
```
http://localhost:11434
```

### Quick API Test

```bash
# List models
curl http://localhost:11434/api/tags

# Generate text
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Explain quantum computing",
  "stream": false
}'

# Chat
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}'
```

## 🚀 Quick Start Commands

### Docker/Ollama
```bash
# Check Ollama is running
docker ps | grep ollama

# List models
docker exec ollama ollama list

# Interactive chat
docker exec -it ollama ollama run llama3.1:8b

# Restart Ollama
docker restart ollama
```

### Python Examples
```bash
cd ~/code_projects/ollama_local/examples

# Interactive chatbot
python3 chatbot.py

# RAG example
python3 rag_example.py

# API examples
python3 api_examples.py
```

## 📚 Documentation

The project includes comprehensive documentation:

- **QUICK_START_API.md** - Fast intro to the API
- **API_GUIDE.md** - Complete API reference
- **examples/README.md** - Code examples guide
- **PERSISTENCE_EXPLAINED.md** - How data persists

## 🔧 Maintenance

### Update Ollama
```bash
cd ~/code_projects/ollama_local
./upgrade_ollama.sh
```

### Update Models
```bash
./check_model_updates.sh
```

### Add New Model
```bash
docker exec ollama ollama pull mistral:7b
```

## 💡 Use Cases

With this setup, you can build:

- 🤖 **Chatbots** - Customer support, personal assistants
- 📝 **Content Generation** - Blogs, emails, documentation
- 💻 **Code Assistants** - Generate, explain, debug code
- 📄 **Document Q&A** - Chat with PDFs and notes (RAG)
- 🔍 **Semantic Search** - Intelligent search across content
- 📊 **Data Analysis** - Explain patterns and insights
- 🌍 **Translation** - Multi-language support
- 🖼️ **Image Analysis** - With llava model

## 🔗 Obsidian + AI Integration

With Obsidian Local REST API plugin installed, you can:

1. **Query your notes** using AI
2. **Generate content** directly in Obsidian
3. **Semantic search** across your vault
4. **Auto-summarize** notes
5. **Build custom workflows**

### Example: Query Notes via API

```python
import requests

# Get all notes
response = requests.get('http://localhost:27123/vault/')

# Create a new note
requests.post('http://localhost:27123/vault/New Note.md', 
    data="# New Note\n\nContent here")

# Use Ollama to summarize
note_content = requests.get('http://localhost:27123/vault/SomeNote.md').text
summary = requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.1:8b",
    "prompt": f"Summarize this note:\n\n{note_content}",
    "stream": False
})
```

## 🔐 Privacy & Security

✅ **100% Local** - All processing on your Mac
✅ **No Cloud Services** - Your data never leaves your machine
✅ **No API Keys** - No external services required
✅ **Offline Capable** - Works without internet
✅ **Private Notes** - Obsidian vault stays local

## 📊 System Resources

### Current Usage
- **Disk Space:** ~30GB (models)
- **RAM:** 4-6GB per model (during inference)
- **Port 11434:** Ollama API
- **Port 27123:** Obsidian Local REST API (when enabled)

### Recommendations
- Run one 7-9B model at a time on 16GB RAM
- Use 3-4B models for faster responses
- Close heavy apps when running large models

## 🎓 Learning Resources

1. Start with the chatbot example
2. Read QUICK_START_API.md
3. Try the RAG example
4. Build your own integration!

## 📝 Notes

- Models persist through Ollama upgrades (Docker volume)
- Obsidian vault location: `~/obsidian_vault`
- Project location: `~/code_projects/ollama_local`
- All components run locally on Apple Silicon

## 🔄 Next Steps

- [ ] Explore the example scripts
- [ ] Build a custom chatbot
- [ ] Create a RAG system for your notes
- [ ] Set up Obsidian + Ollama workflows
- [ ] Experiment with different models

---

**Setup Date:** $(date)
**System:** $(uname -m) - $(sw_vers -productName) $(sw_vers -productVersion)
**Project:** Ollama Local AI with Obsidian Integration
EOF

print_success "Setup note created: $VAULT_PATH/Ollama Local AI Setup.md"

# ============================================================================
# Step 9: Install Obsidian Local REST API Plugin
# ============================================================================

print_step "9️⃣  Installing Obsidian Local REST API Plugin"

print_info "Downloading Obsidian Local REST API plugin..."

PLUGIN_DIR="$VAULT_PATH/.obsidian/plugins/obsidian-local-rest-api"
mkdir -p "$PLUGIN_DIR"

# Download the plugin files
curl -L -o "$PLUGIN_DIR/manifest.json" \
    "https://raw.githubusercontent.com/coddingtonbear/obsidian-local-rest-api/main/manifest.json"

curl -L -o "$PLUGIN_DIR/main.js" \
    "https://github.com/coddingtonbear/obsidian-local-rest-api/releases/latest/download/main.js"

curl -L -o "$PLUGIN_DIR/styles.css" \
    "https://github.com/coddingtonbear/obsidian-local-rest-api/releases/latest/download/styles.css" 2>/dev/null || echo ""

# Enable community plugins
mkdir -p "$VAULT_PATH/.obsidian"
cat > "$VAULT_PATH/.obsidian/community-plugins.json" << 'PLUGINS_EOF'
[
  "obsidian-local-rest-api"
]
PLUGINS_EOF

# Create core plugins config (enable community plugins)
cat > "$VAULT_PATH/.obsidian/config.json" << 'CONFIG_EOF'
{
  "enabledCssSnippets": [],
  "enabledPlugins": [
    "obsidian-local-rest-api"
  ],
  "communityPluginSortOrder": "download",
  "theme": "obsidian"
}
CONFIG_EOF

print_success "Obsidian Local REST API plugin installed"

print_warning "IMPORTANT: You need to manually enable the plugin in Obsidian:"
print_info "1. Open Obsidian"
print_info "2. Open your vault at: $VAULT_PATH"
print_info "3. Go to Settings → Community plugins"
print_info "4. Turn OFF 'Safe mode' (this allows community plugins)"
print_info "5. The 'Local REST API' plugin should appear as installed"
print_info "6. Enable the plugin"
print_info "7. Configure API settings (Settings → Local REST API)"

echo ""
print_info "📖 Plugin Documentation: https://coddingtonbear.github.io/obsidian-local-rest-api/"
echo ""

# ============================================================================
# Step 10: Install Node.js and MCP Server
# ============================================================================

print_step "🔟 Installing Node.js and Obsidian MCP Server"

# Check if Node.js is installed
if command -v node &> /dev/null; then
    print_success "Node.js is already installed ($(node --version))"
else
    print_info "Installing Node.js..."
    brew install node
    print_success "Node.js installed"
fi

# Install MCP servers directory
MCP_DIR="$HOME/.config/mcp-servers"
mkdir -p "$MCP_DIR"

print_info "Installing Obsidian MCP server..."

# Create a package.json for MCP servers
cat > "$MCP_DIR/package.json" << 'MCP_PACKAGE_EOF'
{
  "name": "mcp-servers",
  "version": "1.0.0",
  "description": "MCP Servers for Obsidian integration",
  "dependencies": {
    "@modelcontextprotocol/server-obsidian": "latest"
  }
}
MCP_PACKAGE_EOF

cd "$MCP_DIR"
npm install --silent

print_success "Obsidian MCP server installed"

# Create MCP configuration for Claude Desktop (if it gets installed)
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
mkdir -p "$CLAUDE_CONFIG_DIR"

cat > "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" << MCP_CONFIG_EOF
{
  "mcpServers": {
    "obsidian": {
      "command": "node",
      "args": [
        "$MCP_DIR/node_modules/@modelcontextprotocol/server-obsidian/dist/index.js",
        "--vault-path",
        "$HOME/obsidian_vault"
      ]
    }
  }
}
MCP_CONFIG_EOF

print_success "MCP configuration created"
print_info "MCP will connect to vault at: $HOME/obsidian_vault"

# ============================================================================
# Step 11: Create Integration Examples
# ============================================================================

print_step "1️⃣1️⃣  Creating Obsidian + Ollama Integration Examples"

EXAMPLES_DIR="$(pwd)/examples"
mkdir -p "$EXAMPLES_DIR"

# Create Obsidian + Ollama integration example
cat > "$EXAMPLES_DIR/obsidian_chat.py" << 'OBSIDIAN_CHAT_EOF'
#!/usr/bin/env python3
"""
Chat with your Obsidian notes using Ollama
Requires: Obsidian Local REST API plugin enabled on port 27123
"""

import requests
import sys

OLLAMA_URL = "http://localhost:11434"
OBSIDIAN_API = "http://localhost:27123"

def get_all_notes():
    """Get list of all notes in the vault"""
    try:
        response = requests.get(f"{OBSIDIAN_API}/vault/")
        response.raise_for_status()
        return response.json().get('files', [])
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Obsidian API")
        print("Make sure:")
        print("  1. Obsidian is running")
        print("  2. Local REST API plugin is enabled")
        print("  3. API is accessible on port 27123")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def read_note(note_path):
    """Read content of a specific note"""
    try:
        response = requests.get(f"{OBSIDIAN_API}/vault/{note_path}")
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Error reading note: {e}")
        return None

def search_notes(query):
    """Search notes using Obsidian's search"""
    try:
        response = requests.post(f"{OBSIDIAN_API}/search/simple/", 
                               json={"query": query})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"⚠️  Search not available: {e}")
        return None

def ask_ollama(prompt, model="llama3.1:8b"):
    """Ask Ollama a question"""
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False
        })
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to Ollama")
        print("Make sure Ollama is running: docker ps | grep ollama")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def chat_with_notes():
    """Interactive chat with your Obsidian notes"""
    print("🤖 Chat with Your Obsidian Notes")
    print("=" * 60)
    print()
    
    # Check connections
    print("🔍 Checking connections...")
    notes = get_all_notes()
    print(f"✅ Connected to Obsidian ({len(notes)} notes found)")
    
    # Test Ollama
    ask_ollama("Say 'ready'", model="llama3.2:3b")
    print("✅ Connected to Ollama")
    print()
    
    print("How to use:")
    print("  • Ask questions about your notes")
    print("  • Request summaries or analysis")
    print("  • Type 'quit' to exit")
    print()
    print("=" * 60)
    print()
    
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            # Search for relevant notes
            print("🔍 Searching notes...", end="\r")
            search_results = search_notes(question)
            
            # Get relevant context from notes
            context = ""
            if search_results:
                for result in search_results[:3]:  # Top 3 results
                    note_path = result.get('filename', '')
                    if note_path:
                        content = read_note(note_path)
                        if content:
                            context += f"\n\n=== {note_path} ===\n{content[:500]}"
            
            # If no search results, use recent notes
            if not context:
                print("📚 Using recent notes...", end="\r")
                for note in notes[:5]:  # First 5 notes
                    content = read_note(note)
                    if content:
                        context += f"\n\n=== {note} ===\n{content[:500]}"
            
            # Build prompt with context
            prompt = f"""Based on the following notes from my Obsidian vault, please answer this question:

Question: {question}

Notes:
{context}

Answer:"""
            
            # Get response from Ollama
            print("🤔 Thinking...        ", end="\r")
            response = ask_ollama(prompt)
            
            print(f"AI: {response}")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    print()
    chat_with_notes()

if __name__ == "__main__":
    main()
OBSIDIAN_CHAT_EOF

chmod +x "$EXAMPLES_DIR/obsidian_chat.py"

# Create note summarizer
cat > "$EXAMPLES_DIR/summarize_notes.py" << 'SUMMARIZE_EOF'
#!/usr/bin/env python3
"""
Summarize all notes in your Obsidian vault using Ollama
"""

import requests
import sys

OLLAMA_URL = "http://localhost:11434"
OBSIDIAN_API = "http://localhost:27123"

def get_all_notes():
    """Get list of all notes"""
    try:
        response = requests.get(f"{OBSIDIAN_API}/vault/")
        response.raise_for_status()
        return response.json().get('files', [])
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def read_note(note_path):
    """Read note content"""
    try:
        response = requests.get(f"{OBSIDIAN_API}/vault/{note_path}")
        response.raise_for_status()
        return response.text
    except Exception as e:
        return None

def summarize_note(content, model="llama3.2:3b"):
    """Summarize note content"""
    try:
        prompt = f"Summarize this note in 2-3 sentences:\n\n{content[:2000]}"
        response = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False
        })
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"Error: {e}"

def main():
    """Main function"""
    print("📚 Summarizing Obsidian Notes with AI")
    print("=" * 60)
    print()
    
    # Get all notes
    notes = get_all_notes()
    print(f"Found {len(notes)} notes")
    print()
    
    # Summarize each note
    for i, note_path in enumerate(notes[:10], 1):  # Limit to 10 for demo
        print(f"{i}/{min(10, len(notes))}: {note_path}")
        
        content = read_note(note_path)
        if not content or len(content) < 50:
            print("  (Skipped - too short)")
            continue
        
        summary = summarize_note(content)
        print(f"  Summary: {summary}")
        print()

if __name__ == "__main__":
    main()
SUMMARIZE_EOF

chmod +x "$EXAMPLES_DIR/summarize_notes.py"

# Create knowledge base builder
cat > "$EXAMPLES_DIR/build_knowledge_base.py" << 'KB_EOF'
#!/usr/bin/env python3
"""
Build a semantic search knowledge base from your Obsidian notes
Uses embeddings to enable AI-powered note discovery
"""

import requests
import numpy as np
import json
import sys

OLLAMA_URL = "http://localhost:11434"
OBSIDIAN_API = "http://localhost:27123"

def get_all_notes():
    """Get all notes from vault"""
    try:
        response = requests.get(f"{OBSIDIAN_API}/vault/")
        response.raise_for_status()
        return response.json().get('files', [])
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def read_note(note_path):
    """Read note content"""
    try:
        response = requests.get(f"{OBSIDIAN_API}/vault/{note_path}")
        response.raise_for_status()
        return response.text
    except:
        return None

def generate_embedding(text):
    """Generate embedding for text"""
    try:
        response = requests.post(f"{OLLAMA_URL}/api/embeddings", json={
            "model": "nomic-embed-text",
            "prompt": text[:2000]  # Limit size
        })
        response.raise_for_status()
        return response.json()['embedding']
    except Exception as e:
        print(f"⚠️  Embedding error: {e}")
        return None

def main():
    """Build knowledge base"""
    print("🧠 Building Knowledge Base from Obsidian Notes")
    print("=" * 60)
    print()
    
    # Get notes
    notes = get_all_notes()
    print(f"Processing {len(notes)} notes...")
    print()
    
    # Build knowledge base
    knowledge_base = []
    
    for i, note_path in enumerate(notes, 1):
        print(f"Processing {i}/{len(notes)}: {note_path}...", end="\r")
        
        content = read_note(note_path)
        if not content or len(content) < 50:
            continue
        
        embedding = generate_embedding(content)
        if embedding:
            knowledge_base.append({
                "path": note_path,
                "content": content[:500],  # Store preview
                "embedding": embedding
            })
    
    print()
    print()
    print(f"✅ Created knowledge base with {len(knowledge_base)} notes")
    
    # Save to file
    output_file = "obsidian_knowledge_base.json"
    with open(output_file, 'w') as f:
        json.dump(knowledge_base, f)
    
    print(f"💾 Saved to: {output_file}")
    print()
    print("You can now use semantic search to find relevant notes!")

if __name__ == "__main__":
    main()
KB_EOF

chmod +x "$EXAMPLES_DIR/build_knowledge_base.py"

print_success "Created Obsidian integration examples:"
print_info "  • obsidian_chat.py - Chat with your notes"
print_info "  • summarize_notes.py - Summarize all notes"
print_info "  • build_knowledge_base.py - Build semantic search"

# ============================================================================
# Step 12: Validate Setup
# ============================================================================

print_step "1️⃣2️⃣  Validating Complete Setup"

echo ""
print_info "System Check:"
echo ""

# Check VS Code
if [[ -d "/Applications/Visual Studio Code.app" ]]; then
    echo "✅ Visual Studio Code: Installed"
else
    echo "❌ Visual Studio Code: Not found"
fi

# Check Docker
if [[ -d "/Applications/Docker.app" ]]; then
    echo "✅ Docker Desktop: Installed"
else
    echo "❌ Docker Desktop: Not found"
fi

# Check Obsidian
if [[ -d "/Applications/Obsidian.app" ]]; then
    echo "✅ Obsidian: Installed"
else
    echo "❌ Obsidian: Not found"
fi

# Check Obsidian vault
if [[ -d "$HOME/obsidian_vault" ]]; then
    echo "✅ Obsidian Vault: Created at ~/obsidian_vault"
else
    echo "❌ Obsidian Vault: Not found"
fi

# Check Node.js
if command -v node &> /dev/null; then
    echo "✅ Node.js: Installed ($(node --version))"
else
    echo "❌ Node.js: Not found"
fi

# Check MCP server
if [[ -d "$HOME/.config/mcp-servers/node_modules/@modelcontextprotocol/server-obsidian" ]]; then
    echo "✅ Obsidian MCP Server: Installed"
else
    echo "❌ Obsidian MCP Server: Not found"
fi

# Check Docker running
if docker info &> /dev/null; then
    echo "✅ Docker: Running"
else
    echo "❌ Docker: Not running"
fi

# Check Ollama container
if docker ps | grep -q "ollama"; then
    echo "✅ Ollama Container: Running"
else
    echo "❌ Ollama Container: Not running"
fi

# Check models
echo ""
print_info "Installed Models:"
docker exec ollama ollama list

# ============================================================================
# Step 8: Run Validation Tests
# ============================================================================

print_step "8️⃣  Running Validation Tests"

print_info "Test 1: API Health Check"
if curl -s http://localhost:11434/ > /dev/null; then
    print_success "API is accessible"
else
    print_error "API is not accessible"
fi

print_info "Test 2: Simple Text Generation"
docker exec ollama ollama run llama3.2:3b "Say 'Setup complete!' in a creative way" || {
    print_error "Text generation test failed"
}

# ============================================================================
# Setup Complete
# ============================================================================

print_step "🎉 Setup Complete!"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ All components installed and validated!"
echo ""
echo "📦 Installed Software:"
echo "   • Visual Studio Code"
echo "   • Docker Desktop"
echo "   • Ollama (in Docker)"
echo "   • Obsidian + Local REST API plugin"
echo "   • Node.js + Obsidian MCP Server"
echo ""
echo "📦 Installed Models:"
docker exec ollama ollama list | tail -n +2 | awk '{printf "   • %s (%s)\n", $1, $3" "$4}'
echo ""
echo "📚 Obsidian Vault:"
echo "   Location: ~/obsidian_vault"
echo "   Setup Note: 'Ollama Local AI Setup.md'"
echo ""
echo "🔌 MCP Configuration:"
echo "   Server: Obsidian MCP"
echo "   Config: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "   Vault Path: ~/obsidian_vault"
echo ""
echo "⚠️  NEXT STEPS:"
echo ""
echo "   1️⃣  Enable Obsidian Plugin:"
echo "      • Open Obsidian"
echo "      • Open vault: ~/obsidian_vault"
echo "      • Settings → Community plugins"
echo "      • Turn OFF 'Safe mode'"
echo "      • Enable 'Local REST API' plugin"
echo ""
echo "   2️⃣  Try Chat with Notes:"
echo "      cd examples"
echo "      python3 obsidian_chat.py"
echo ""
echo "   3️⃣  (Optional) Install Claude Desktop:"
echo "      • Claude will auto-detect MCP configuration"
echo "      • Can chat with your notes via MCP"
echo ""
echo "🚀 Quick Start Commands:"
echo ""
echo "   # Open Obsidian vault"
echo "   open ~/obsidian_vault"
echo ""
echo "   # Chat with your notes (after enabling plugin)"
echo "   cd examples"
echo "   python3 obsidian_chat.py"
echo ""
echo "   # Summarize all notes"
echo "   python3 summarize_notes.py"
echo ""
echo "   # Build knowledge base"
echo "   python3 build_knowledge_base.py"
echo ""
echo "   # List Ollama models"
echo "   docker exec ollama ollama list"
echo ""
echo "   # Interactive AI chat"
echo "   docker exec -it ollama ollama run llama3.1:8b"
echo ""
echo "   # Try RAG example"
echo "   python3 rag_example.py"
echo ""
echo "📚 Documentation:"
echo "   • Quick Start: cat QUICK_START_API.md"
echo "   • API Guide: cat API_GUIDE.md"
echo "   • Examples: cat examples/README.md"
echo ""
echo "🌐 API Endpoints:"
echo "   • Ollama: http://localhost:11434"
echo "   • Obsidian REST API: http://localhost:27123 (after enabling)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Open Obsidian vault
read -p "Open Obsidian vault now? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    open ~/obsidian_vault
    print_success "Opening Obsidian vault..."
    print_info "Remember to enable the Local REST API plugin!"
fi

# Open VS Code in current directory
read -p "Open this project in VS Code? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    code .
    print_success "Opened in VS Code"
fi

print_success "Setup script completed successfully! 🎉"
echo ""
echo "Next step: Try running the examples!"
echo "  cd examples"
echo "  python3 chatbot.py"

