# 🧠 Obsidian + Ollama + MCP Integration Guide

**Complete guide to chatting with your Obsidian notes using local AI**

This guide explains how to use the full stack: **Obsidian → Local REST API → Ollama/MCP → AI Chat**

---

## 🎯 What You Have

After running `setup.sh`, you have a complete "chat with your notes" system:

### Components Installed

1. **Obsidian** - Your note-taking app
2. **Obsidian Local REST API Plugin** - Exposes notes via HTTP API
3. **Ollama** - Local AI models (8 models, ~30GB)
4. **Node.js** - JavaScript runtime
5. **Obsidian MCP Server** - Model Context Protocol bridge
6. **Integration Scripts** - Python tools to chat with notes

###  Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Your Setup                                             │
│                                                          │
│  ┌──────────────┐                                       │
│  │  Obsidian    │  Your notes                           │
│  │  Vault       │  ~/obsidian_vault                     │
│  └──────┬───────┘                                       │
│         │                                                │
│         │ Local REST API Plugin (port 27123)            │
│         ↓                                                │
│  ┌─────────────────────────────┐                        │
│  │  HTTP API                   │                        │
│  │  • Read notes               │                        │
│  │  • Write notes              │                        │
│  │  • Search notes             │                        │
│  └──────┬──────────────────────┘                        │
│         │                                                │
│         ├───────────────────┬────────────────────┐      │
│         │                   │                    │      │
│         ↓                   ↓                    ↓      │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────┐  │
│  │  Ollama AI   │    │  MCP Server  │    │ Python  │  │
│  │  (Docker)    │    │              │    │ Scripts │  │
│  │              │    │              │    │         │  │
│  │ 8 Models     │    │  Claude      │    │  Chat   │  │
│  │ port 11434   │    │  Desktop     │    │  Tools  │  │
│  └──────────────┘    └──────────────┘    └─────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Step 1: Enable Obsidian Plugin

**IMPORTANT:** You must enable the plugin before chatting with notes!

1. **Open Obsidian**
   ```bash
   open ~/obsidian_vault
   ```

2. **Open Settings** (⚙️ icon in bottom left)

3. **Go to Community Plugins** (left sidebar)

4. **Turn OFF "Safe mode"** (allows community plugins)

5. **You should see "Local REST API" in installed plugins**

6. **Toggle it ON** (switch to enable)

7. **Configure the plugin** (click gear icon):
   - **Enable**: ✅ On
   - **Port**: 27123 (default)
   - **Encryption Key**: (optional, leave empty for local use)
   - **CORS**: Allow all origins (for local development)

8. **Click "Test API"** to verify it works

✅ **API is now running on port 27123!**

### Step 2: Read the Setup Note

Obsidian vault contains a comprehensive setup note:

```bash
open ~/obsidian_vault/"Ollama Local AI Setup.md"
```

This note contains:
- Complete system documentation
- API examples
- Integration workflows
- Quick reference commands

### Step 3: Try the Examples

```bash
cd examples

# Chat with your notes
python3 obsidian_chat.py

# Summarize all notes
python3 summarize_notes.py

# Build semantic search knowledge base
python3 build_knowledge_base.py
```

---

## 💬 Examples Explained

### 1. **obsidian_chat.py** - Interactive Chat

Chat with your notes using AI:

```bash
python3 obsidian_chat.py
```

**How it works:**
1. You ask a question
2. Script searches your notes for relevant content
3. Sends question + context to Ollama
4. AI answers based on your notes

**Example session:**
```
You: What did I write about Docker?
AI: Based on your notes, you documented Docker as a 
     container platform that...

You: Summarize my project ideas
AI: Your vault contains several project ideas including...
```

### 2. **summarize_notes.py** - Auto-Summarize

Automatically summarize all notes:

```bash
python3 summarize_notes.py
```

**Output:**
```
1/10: Project Ideas.md
  Summary: This note contains 5 project ideas for...

2/10: Meeting Notes 2025-01-15.md
  Summary: Team discussed the new feature rollout...
```

### 3. **build_knowledge_base.py** - Semantic Search

Build embeddings for AI-powered search:

```bash
python3 build_knowledge_base.py
```

Creates `obsidian_knowledge_base.json` with:
- All note content
- Vector embeddings (768-dimensional)
- Enables semantic search (find by meaning, not keywords)

---

## 🔌 MCP Integration (Claude Desktop)

The MCP (Model Context Protocol) server allows Claude Desktop to access your notes.

### What is MCP?

MCP is a protocol that lets AI assistants (like Claude) access external data sources. Your setup includes the Obsidian MCP server.

### Configuration Location

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Contents:**
```json
{
  "mcpServers": {
    "obsidian": {
      "command": "node",
      "args": [
        "~/.config/mcp-servers/node_modules/@modelcontextprotocol/server-obsidian/dist/index.js",
        "--vault-path",
        "~/obsidian_vault"
      ]
    }
  }
}
```

### Using MCP with Claude

1. **Install Claude Desktop** (if you want to use it)
   - Download from: https://claude.ai/download

2. **Restart Claude Desktop**
   - MCP config is loaded on startup

3. **Claude can now access your notes!**
   - Ask: "What notes do I have about AI?"
   - Ask: "Summarize my project notes"
   - Ask: "Search my vault for Docker info"

**Note:** MCP requires the Local REST API plugin to be enabled!

---

## 🛠️ API Reference

### Obsidian Local REST API

**Base URL:** `http://localhost:27123`

#### List All Notes
```bash
curl http://localhost:27123/vault/
```

#### Read a Note
```bash
curl http://localhost:27123/vault/MyNote.md
```

#### Create/Update Note
```bash
curl -X POST http://localhost:27123/vault/NewNote.md \
  -d "# New Note\n\nContent here"
```

#### Search Notes
```bash
curl -X POST http://localhost:27123/search/simple/ \
  -H "Content-Type: application/json" \
  -d '{"query": "docker"}'
```

### Ollama API

**Base URL:** `http://localhost:11434`

See [API_GUIDE.md](API_GUIDE.md) for complete Ollama API documentation.

---

## 🎨 Use Cases

### 1. **Personal Research Assistant**

```python
# Ask questions about your research notes
python3 obsidian_chat.py
> "What are the key points from my AI research?"
> "Find notes about machine learning"
```

### 2. **Project Documentation**

```python
# Auto-generate project summaries
python3 summarize_notes.py
```

### 3. **Knowledge Base Search**

```python
# Build semantic search index
python3 build_knowledge_base.py

# Then search by meaning, not keywords
```

### 4. **Meeting Notes Analysis**

```python
# Analyze patterns across meeting notes
"What are common themes in my meeting notes?"
"Summarize action items from last week"
```

### 5. **Writing Assistant**

```python
# Get help with your writing
"Improve the clarity of my draft about X"
"Find similar notes to this topic"
```

---

## 🔧 Troubleshooting

### "Cannot connect to Obsidian API"

**Fix:**
1. Ensure Obsidian is running
2. Check plugin is enabled (Settings → Community Plugins)
3. Verify port 27123: `lsof -i :27123`
4. Try clicking "Test API" in plugin settings

### "Cannot connect to Ollama"

**Fix:**
```bash
# Check if Ollama is running
docker ps | grep ollama

# If not running, start it
docker start ollama

# Test API
curl http://localhost:11434/api/tags
```

### "No notes found"

**Fix:**
1. Add some notes to `~/obsidian_vault`
2. Make sure notes are `.md` files
3. Check vault path in scripts

### "Module not found" Error

**Fix:**
```bash
# Install Python dependencies
pip3 install requests numpy

# Or use requirements.txt
pip3 install -r requirements.txt
```

### MCP Not Working

**Fix:**
1. Restart Claude Desktop
2. Check config file exists:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
3. Ensure Node.js is installed: `node --version`
4. Verify MCP server installed:
   ```bash
   ls ~/.config/mcp-servers/node_modules/@modelcontextprotocol/server-obsidian
   ```

---

## 📊 Performance Tips

### 1. **Use Smaller Models for Quick Queries**

```python
# In scripts, change model to:
model="llama3.2:3b"  # Faster
# instead of:
model="llama3.1:8b"  # More capable but slower
```

### 2. **Limit Context Length**

```python
# Only send relevant excerpts
content[:2000]  # First 2000 characters
```

### 3. **Cache Embeddings**

```python
# Run once, reuse results
python3 build_knowledge_base.py  # Creates cached embeddings
```

### 4. **Close Heavy Apps**

When running large models, close:
- Web browsers with many tabs
- Video editing software
- Other Docker containers

---

## 🔐 Privacy & Security

✅ **Everything runs locally:**
- Notes stay on your Mac
- AI processing happens on your Mac
- No data sent to cloud services
- No API keys required

✅ **Network access:**
- Obsidian API: localhost only (127.0.0.1)
- Ollama API: localhost only
- Not exposed to internet

✅ **Data safety:**
- Your notes never leave your machine
- AI can't access files outside vault
- All processing is private

---

## 📚 Next Steps

### Customize the Scripts

The Python scripts are fully customizable:

1. **Change AI models** - Edit model names
2. **Adjust prompts** - Modify how questions are asked
3. **Filter notes** - Only search certain folders
4. **Add features** - Extend functionality

### Build Your Own Tools

Use the examples as templates:

```python
import requests

# Read your notes
notes = requests.get('http://localhost:27123/vault/').json()

# Process with AI
for note in notes['files']:
    content = requests.get(f'http://localhost:27123/vault/{note}').text
    # Do something with AI...
```

### Integrate with Other Tools

- **Zapier/n8n**: Automate workflows
- **Alfred/Raycast**: Quick note search
- **Custom UI**: Build a web interface
- **Cron Jobs**: Schedule note processing

---

## 🎓 Learning Resources

1. **Obsidian Local REST API Docs**
   - https://coddingtonbear.github.io/obsidian-local-rest-api/

2. **Ollama API Docs**
   - See [API_GUIDE.md](API_GUIDE.md)

3. **Model Context Protocol**
   - https://modelcontextprotocol.io/

4. **Example Code**
   - Check `examples/` directory
   - All scripts are well-commented

---

## ✅ Quick Reference

### Commands

```bash
# Open vault
open ~/obsidian_vault

# Chat with notes
python3 examples/obsidian_chat.py

# Summarize notes
python3 examples/summarize_notes.py

# Build KB
python3 examples/build_knowledge_base.py

# Check Ollama
docker ps | grep ollama

# Check API
curl http://localhost:27123/vault/
curl http://localhost:11434/api/tags
```

### Ports

- **27123** - Obsidian Local REST API
- **11434** - Ollama AI API

### Paths

- **Vault:** `~/obsidian_vault`
- **Scripts:** `~/code_projects/ollama_local/examples`
- **MCP Config:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **MCP Server:** `~/.config/mcp-servers`

---

**You now have a complete "AI + Notes" system running locally!** 🎉

Start by enabling the Obsidian plugin, then try `python3 obsidian_chat.py` to chat with your notes.

