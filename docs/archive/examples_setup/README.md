# 📚 Ollama API Examples

Interactive examples demonstrating how to build applications with the Ollama API.

## 🚀 Quick Start

### Prerequisites

```bash
# Python examples require:
pip install requests numpy

# All examples require Ollama to be running:
docker ps | grep ollama
```

---

## 📝 Available Examples

### 1. **Basic API Examples** (`api_examples.sh` & `api_examples.py`)

**Demonstrates:**
- Listing models
- Text generation
- Chat completion
- Generating embeddings
- Streaming responses
- Model information

**Run:**
```bash
# Bash version
./api_examples.sh

# Python version
python3 api_examples.py
```

---

### 2. **Interactive Chatbot** (`chatbot.py`)

**Features:**
- Multi-turn conversations
- Conversation history
- Custom system prompts
- Commands: /clear, /history, /quit

**Run:**
```bash
# Interactive mode
python3 chatbot.py

# Demo mode
python3 chatbot.py --demo
```

**Example:**
```
Choose model (default: llama3.1:8b): 
Enter system prompt: You are a helpful coding assistant

You: How do I create a Python class?
Bot: [Detailed explanation with example...]

You: Can you show me inheritance?
Bot: [Continues conversation with context...]
```

---

### 3. **RAG (Retrieval-Augmented Generation)** (`rag_example.py`)

**Demonstrates:**
- Building a knowledge base
- Semantic search with embeddings
- Context-aware question answering
- Document retrieval

**Run:**
```bash
python3 rag_example.py
```

**How it works:**
```
1. Load documents into knowledge base
2. Generate embeddings for each document
3. User asks a question
4. Find most relevant documents (semantic search)
5. Use relevant context to generate accurate answer
```

**Example Output:**
```
🔍 Searching for: What is Docker?
📚 Retrieved context:
  1. (score: 0.847) Docker is a platform for developing...
  2. (score: 0.621) Containers are lightweight...

🤖 Answer: Docker is a platform that allows you to...
```

---

## 🎯 Common Use Cases

### Text Generation
```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.1:8b",
    "prompt": "Explain quantum computing",
    "stream": False
})

print(response.json()['response'])
```

### Chat with Context
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"},
]

response = requests.post('http://localhost:11434/api/chat', json={
    "model": "llama3.1:8b",
    "messages": messages,
    "stream": False
})

print(response.json()['message']['content'])
```

### Generate Embeddings
```python
response = requests.post('http://localhost:11434/api/embeddings', json={
    "model": "nomic-embed-text",
    "prompt": "Machine learning is amazing"
})

embeddings = response.json()['embedding']  # 768-dimensional vector
```

---

## 🔧 Building Your Own Application

### 1. Choose Your Model

| Model | Best For | Speed | Quality |
|-------|----------|-------|---------|
| llama3.2:3b | Quick responses | ⚡⚡⚡ | ⭐⭐⭐ |
| qwen3:4b | Balanced | ⚡⚡ | ⭐⭐⭐⭐ |
| llama3.1:8b | Complex tasks | ⚡ | ⭐⭐⭐⭐⭐ |
| qwen2.5:7b | Multilingual | ⚡ | ⭐⭐⭐⭐ |
| deepseek-r1:7b | Reasoning/Math | ⚡ | ⭐⭐⭐⭐⭐ |

### 2. Basic Structure

```python
import requests

OLLAMA_URL = "http://localhost:11434"

def generate(prompt, model="llama3.1:8b"):
    """Generate text from a prompt"""
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()['response']

def chat(messages, model="llama3.1:8b"):
    """Multi-turn conversation"""
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={"model": model, "messages": messages, "stream": False}
    )
    return response.json()['message']['content']

def embed(text):
    """Generate embeddings"""
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    return response.json()['embedding']
```

### 3. Add Error Handling

```python
def safe_generate(prompt, model="llama3.1:8b"):
    """Generate with error handling"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60
        )
        response.raise_for_status()
        return response.json()['response']
    except requests.exceptions.ConnectionError:
        return "Error: Ollama service not available"
    except requests.exceptions.Timeout:
        return "Error: Request timed out"
    except Exception as e:
        return f"Error: {str(e)}"
```

---

## 💡 Project Ideas

### Beginner

1. **Simple Q&A Bot** - Answer user questions
2. **Text Summarizer** - Summarize long articles
3. **Code Explainer** - Explain code snippets
4. **Writing Assistant** - Help with grammar and style

### Intermediate

5. **Document Chat** - Chat with your PDFs/documents
6. **Code Generator** - Generate code from descriptions
7. **Language Translator** - Multi-language translation
8. **Meeting Summarizer** - Summarize transcripts

### Advanced

9. **Research Assistant** - Multi-document analysis
10. **Custom Knowledge Base** - RAG with your data
11. **AI Agent** - Chain multiple AI calls
12. **Semantic Search Engine** - Search across documents

---

## 🌐 Integration Examples

### FastAPI Server

```python
from fastapi import FastAPI
import requests

app = FastAPI()

@app.post("/generate")
async def generate(prompt: str, model: str = "llama3.1:8b"):
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return {"response": response.json()['response']}

# Run: uvicorn server:app --reload
```

### Flask Web App

```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    response = requests.post('http://localhost:11434/api/chat', json=data)
    return jsonify(response.json())

# Run: flask run
```

### Gradio UI

```python
import gradio as gr
import requests

def chat(message, history):
    messages = [{"role": "user", "content": message}]
    response = requests.post('http://localhost:11434/api/chat', json={
        "model": "llama3.1:8b",
        "messages": messages,
        "stream": False
    })
    return response.json()['message']['content']

demo = gr.ChatInterface(chat)
demo.launch()

# Run: python gradio_app.py
```

---

## 📊 Performance Tips

1. **Use smaller models for quick queries**
   - `llama3.2:3b` for simple tasks
   - `llama3.1:8b` for complex reasoning

2. **Enable streaming for better UX**
   ```python
   response = requests.post(..., json={"stream": True}, stream=True)
   for line in response.iter_lines():
       # Process each token as it arrives
   ```

3. **Cache embeddings**
   - Generate once, store in database
   - Significantly faster than regenerating

4. **Manage context length**
   - Longer context = slower responses
   - Summarize old messages in conversations

5. **Batch similar requests**
   - Process multiple prompts together
   - Parallel embedding generation

---

## 🔒 Security Best Practices

1. **Don't expose Ollama port to internet**
2. **Validate user inputs** - Prevent injection attacks
3. **Rate limiting** - Prevent abuse
4. **Monitor resource usage** - Prevent DoS
5. **Sanitize outputs** - Check for sensitive data

---

## 🐛 Troubleshooting

### "Connection refused"
```bash
# Check if Ollama is running
docker ps | grep ollama

# If not running, start it
docker start ollama
```

### "Model not found"
```bash
# List available models
docker exec ollama ollama list

# Pull the model if needed
docker exec ollama ollama pull llama3.1:8b
```

### Slow responses
- Use a smaller model (3-4B parameters)
- Reduce context length
- Check system resources (Activity Monitor)
- Close other heavy applications

### Out of memory
```bash
# Use smaller models
# Models under 4B work best on 16GB RAM
docker exec ollama ollama run llama3.2:3b
```

---

## 📚 Additional Resources

- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Complete API Guide](../API_GUIDE.md)
- [Main README](../README.md)
- [Persistence Explained](../PERSISTENCE_EXPLAINED.md)

---

## 🎓 Learning Path

1. **Start with**: `api_examples.sh` - Understand the basics
2. **Then try**: `api_examples.py` - Python integration
3. **Build**: `chatbot.py` - Interactive experience
4. **Advanced**: `rag_example.py` - Production-ready patterns
5. **Create**: Your own application!

---

## 💬 Need Help?

- Check the [API Guide](../API_GUIDE.md) for detailed documentation
- Review error messages carefully
- Ensure Ollama is running: `docker ps`
- Verify models are available: `docker exec ollama ollama list`

---

**Happy building! 🚀**

