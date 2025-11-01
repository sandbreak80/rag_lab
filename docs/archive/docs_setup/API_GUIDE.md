# 🌐 Ollama API Documentation

## Overview

**YES!** Ollama exposes a full REST API on **port 11434** that you can use to build applications.

```
Endpoint: http://localhost:11434
Protocol: HTTP REST API
Format: JSON
Authentication: None (local only)
```

---

## 🔌 Available Endpoints

### 1. **Generate Completion** - `/api/generate`
Generate text from a prompt.

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

**Python:**
```python
import requests

response = requests.post('http://localhost:11434/api/generate', json={
    "model": "llama3.1:8b",
    "prompt": "Explain Docker in one sentence",
    "stream": False
})

print(response.json()['response'])
```

### 2. **Chat Completion** - `/api/chat`
Multi-turn conversation with context.

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}'
```

**Python:**
```python
response = requests.post('http://localhost:11434/api/chat', json={
    "model": "llama3.1:8b",
    "messages": [
        {"role": "system", "content": "You are a coding expert"},
        {"role": "user", "content": "Explain Python decorators"}
    ],
    "stream": False
})

print(response.json()['message']['content'])
```

### 3. **Generate Embeddings** - `/api/embeddings`
Generate vector embeddings (for RAG, semantic search).

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Docker containers are lightweight"
}'
```

**Python:**
```python
response = requests.post('http://localhost:11434/api/embeddings', json={
    "model": "nomic-embed-text",
    "prompt": "Machine learning is amazing"
})

embeddings = response.json()['embedding']  # Vector of floats
print(f"Embedding dimension: {len(embeddings)}")
```

### 4. **List Models** - `/api/tags`
List all available models.

```bash
curl http://localhost:11434/api/tags
```

**Python:**
```python
response = requests.get('http://localhost:11434/api/tags')
models = response.json()['models']

for model in models:
    print(f"{model['name']}: {model['size'] / (1024**3):.1f} GB")
```

### 5. **Show Model Info** - `/api/show`
Get detailed information about a model.

```bash
curl http://localhost:11434/api/show -d '{
  "name": "llama3.1:8b"
}'
```

### 6. **Pull Model** - `/api/pull`
Download a new model.

```bash
curl http://localhost:11434/api/pull -d '{
  "name": "llama3.1:8b",
  "stream": true
}'
```

### 7. **Delete Model** - `/api/delete`
Remove a model.

```bash
curl -X DELETE http://localhost:11434/api/delete -d '{
  "name": "llama3.1:8b"
}'
```

---

## 🎯 Common Use Cases

### 1. **Text Generation**
```python
def generate_text(prompt, model="llama3.1:8b"):
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()['response']

# Usage
result = generate_text("Write a poem about AI")
```

### 2. **Chatbot with Memory**
```python
class Chatbot:
    def __init__(self, model="llama3.1:8b"):
        self.model = model
        self.messages = []
    
    def chat(self, message):
        self.messages.append({"role": "user", "content": message})
        
        response = requests.post('http://localhost:11434/api/chat', json={
            "model": self.model,
            "messages": self.messages,
            "stream": False
        })
        
        reply = response.json()['message']['content']
        self.messages.append({"role": "assistant", "content": reply})
        return reply

# Usage
bot = Chatbot()
print(bot.chat("Hello!"))
print(bot.chat("What did I just say?"))  # Has context!
```

### 3. **Semantic Search / RAG**
```python
def get_embedding(text):
    response = requests.post('http://localhost:11434/api/embeddings', json={
        "model": "nomic-embed-text",
        "prompt": text
    })
    return response.json()['embedding']

def cosine_similarity(vec1, vec2):
    import numpy as np
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Build knowledge base
docs = [
    "Python is a programming language",
    "Docker containers are isolated",
    "AI models can generate text"
]
doc_embeddings = [get_embedding(doc) for doc in docs]

# Search
query = "Tell me about containers"
query_embedding = get_embedding(query)

similarities = [cosine_similarity(query_embedding, doc_emb) 
                for doc_emb in doc_embeddings]

best_match_idx = similarities.index(max(similarities))
print(f"Best match: {docs[best_match_idx]}")
```

### 4. **Streaming Responses**
```python
def stream_response(prompt, model="llama3.1:8b"):
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={"model": model, "prompt": prompt, "stream": True},
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            print(chunk.get('response', ''), end='', flush=True)

# Usage
stream_response("Count from 1 to 10")
```

### 5. **Vision Analysis**
```python
import base64

def analyze_image(image_path, question, model="llava:7b"):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": model,
        "prompt": question,
        "images": [image_data],
        "stream": False
    })
    
    return response.json()['response']

# Usage
answer = analyze_image("photo.jpg", "What's in this image?")
```

---

## 🚀 Example Applications You Can Build

### 1. **Code Assistant**
- Code generation
- Code explanation
- Bug fixing
- Documentation generation

### 2. **Document Q&A (RAG)**
- Load documents → generate embeddings
- User asks question → find relevant docs
- Generate answer with context

### 3. **Content Generator**
- Blog posts
- Social media content
- Product descriptions
- Email templates

### 4. **Research Assistant**
- Summarize papers
- Extract key points
- Answer questions about documents

### 5. **Customer Support Bot**
- Answer FAQs
- Troubleshooting help
- Multi-language support

### 6. **Data Analysis Assistant**
- Explain data patterns
- Generate SQL queries
- Create visualizations (code)

### 7. **Personal Knowledge Base**
- Chat with your notes/documents
- Semantic search across files
- Intelligent note-taking

---

## 📦 Available Models & Their Best Uses

| Model | Size | Best For | Example Use Case |
|-------|------|----------|------------------|
| **llama3.1:8b** | 4.9GB | General purpose, reasoning | Chatbots, Q&A, coding |
| **qwen2.5:7b** | 4.7GB | Multilingual, coding | International apps, dev tools |
| **deepseek-r1:7b** | 4.7GB | Math, reasoning | Data analysis, logic problems |
| **gemma2:9b** | 5.4GB | High performance | Production chatbots |
| **llama3.2:3b** | 2.0GB | Fast responses | Quick queries, APIs |
| **qwen3:4b** | 2.5GB | Balanced | Mobile apps, edge devices |
| **nomic-embed-text** | 274MB | Embeddings | RAG, semantic search |
| **llava:7b** | 4.7GB | Vision | Image analysis, OCR |

---

## 🔧 API Parameters

### Generate/Chat Options

```json
{
  "model": "llama3.1:8b",          // Required
  "prompt": "Your prompt here",     // For generate
  "messages": [...],                // For chat
  "stream": false,                  // Enable streaming
  "temperature": 0.7,               // Creativity (0-2)
  "top_p": 0.9,                     // Nucleus sampling
  "top_k": 40,                      // Top-k sampling
  "num_predict": 100,               // Max tokens to generate
  "stop": ["\n", "User:"],          // Stop sequences
  "seed": 42,                       // For reproducibility
  "context": [...],                 // Previous context
  "format": "json"                  // Force JSON output
}
```

---

## 🌐 Integration Examples

### FastAPI Web Server

```python
from fastapi import FastAPI
import requests

app = FastAPI()

@app.post("/chat")
async def chat(message: str, model: str = "llama3.1:8b"):
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": model,
        "prompt": message,
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

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    response = requests.post('http://localhost:11434/api/generate', 
                            json=data)
    return jsonify(response.json())

# Run: flask run
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function generateText(prompt, model = 'llama3.1:8b') {
  const response = await axios.post('http://localhost:11434/api/generate', {
    model: model,
    prompt: prompt,
    stream: false
  });
  
  return response.data.response;
}

// Usage
generateText('Explain async/await').then(console.log);
```

---

## 🔒 Security Considerations

1. **Local Only**: Ollama API has no authentication
2. **Network Exposure**: Don't expose port 11434 to internet
3. **Reverse Proxy**: Use nginx/traefik if exposing publicly
4. **Rate Limiting**: Implement on your application layer
5. **Input Validation**: Sanitize user inputs
6. **Output Filtering**: Check for sensitive information

### Example: Add Authentication Layer

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/chat", dependencies=[Depends(verify_token)])
async def protected_chat(message: str):
    # Your Ollama API call here
    pass
```

---

## 📊 Performance Tips

1. **Choose the Right Model**
   - Small queries: Use 3-4B models
   - Complex tasks: Use 7-9B models
   
2. **Streaming**
   - Enable for better UX
   - Shows progress to users
   
3. **Context Management**
   - Limit message history
   - Summarize old conversations
   
4. **Caching**
   - Cache common queries
   - Store embeddings once
   
5. **Batch Processing**
   - Generate embeddings in batches
   - Process multiple requests in parallel

---

## 📚 Example Projects in This Repo

1. **`api_examples.py`** - Basic API usage examples
2. **`api_examples.sh`** - Curl-based examples
3. **`chatbot.py`** - Interactive chatbot with memory
4. **`rag_example.py`** - Document Q&A system
5. **More coming soon!**

---

## 🔗 Resources

- [Official Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Model Library](https://ollama.com/library)
- [LangChain Integration](https://python.langchain.com/docs/integrations/llms/ollama)
- [LlamaIndex Integration](https://docs.llamaindex.ai/en/stable/examples/llm/ollama/)

---

**Ready to build? Check out the examples in the `/examples` directory!**

