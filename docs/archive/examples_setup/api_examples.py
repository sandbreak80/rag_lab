#!/usr/bin/env python3
"""
Ollama API Examples
Demonstrates how to interact with the Ollama API programmatically
"""

import requests
import json

# Base URL for Ollama API
OLLAMA_URL = "http://localhost:11434"

def list_models():
    """List all available models"""
    print("📦 Available Models:")
    print("=" * 60)
    
    response = requests.get(f"{OLLAMA_URL}/api/tags")
    models = response.json()['models']
    
    for model in models:
        name = model['name']
        size_gb = model['size'] / (1024**3)
        param_size = model['details'].get('parameter_size', 'N/A')
        print(f"  • {name:30} {size_gb:>5.1f} GB  {param_size}")
    
    print()
    return models

def generate_completion(model, prompt, stream=False):
    """Generate a completion from a prompt"""
    print(f"🤖 Generating completion with {model}...")
    print(f"📝 Prompt: {prompt}")
    print("-" * 60)
    
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
    )
    
    result = response.json()
    print(result['response'])
    print()
    return result

def chat_completion(model, messages):
    """Chat-style conversation with context"""
    print(f"💬 Chat with {model}...")
    print("-" * 60)
    
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    
    result = response.json()
    print(f"Assistant: {result['message']['content']}")
    print()
    return result

def generate_embeddings(text):
    """Generate embeddings for text (useful for RAG, semantic search)"""
    print(f"🔢 Generating embeddings...")
    print(f"Text: {text[:50]}...")
    print("-" * 60)
    
    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={
            "model": "nomic-embed-text",
            "prompt": text
        }
    )
    
    result = response.json()
    embeddings = result['embedding']
    print(f"Embedding vector length: {len(embeddings)}")
    print(f"First 5 values: {embeddings[:5]}")
    print()
    return embeddings

def streaming_example(model, prompt):
    """Example of streaming responses (real-time token generation)"""
    print(f"🌊 Streaming response from {model}...")
    print(f"📝 Prompt: {prompt}")
    print("-" * 60)
    print("Response: ", end="", flush=True)
    
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )
    
    full_response = ""
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            token = chunk.get('response', '')
            print(token, end="", flush=True)
            full_response += token
            
            if chunk.get('done'):
                break
    
    print("\n")
    return full_response

def vision_example(image_path, prompt):
    """Example using vision model (llava) with images"""
    print(f"👁️ Vision analysis with llava:7b...")
    print(f"Image: {image_path}")
    print(f"Question: {prompt}")
    print("-" * 60)
    
    # Read image and encode to base64
    import base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llava:7b",
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }
    )
    
    result = response.json()
    print(result['response'])
    print()
    return result

def check_health():
    """Check if Ollama service is running"""
    try:
        response = requests.get(f"{OLLAMA_URL}/")
        print("✅ Ollama service is running")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Ollama service is not accessible")
        return False

def main():
    """Run example demonstrations"""
    print("🚀 Ollama API Examples")
    print("=" * 60)
    print()
    
    # Check if service is running
    if not check_health():
        print("Please start Ollama: docker start ollama")
        return
    
    print()
    
    # 1. List models
    models = list_models()
    
    # 2. Simple completion
    generate_completion(
        "llama3.2:3b",
        "Write a haiku about programming",
        stream=False
    )
    
    # 3. Chat completion
    chat_completion(
        "llama3.1:8b",
        [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "What are the benefits of Docker?"}
        ]
    )
    
    # 4. Generate embeddings
    generate_embeddings(
        "Docker containers provide isolated environments for applications"
    )
    
    # 5. Streaming response
    streaming_example(
        "qwen3:4b",
        "Explain quantum entanglement in one sentence"
    )
    
    # Note: Vision example requires an actual image file
    # vision_example("image.jpg", "What's in this image?")

if __name__ == "__main__":
    main()

