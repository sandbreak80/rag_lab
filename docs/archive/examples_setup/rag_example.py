#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) Example
Demonstrates how to build a simple document Q&A system using Ollama embeddings
"""

import requests
import numpy as np
from typing import List, Tuple

OLLAMA_URL = "http://localhost:11434"

class SimpleRAG:
    """Simple RAG implementation using Ollama"""
    
    def __init__(self):
        self.documents = []
        self.embeddings = []
    
    def add_document(self, text: str):
        """Add a document to the knowledge base"""
        print(f"📄 Adding document: {text[:50]}...")
        
        # Generate embedding for the document
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text
            }
        )
        
        embedding = response.json()['embedding']
        self.documents.append(text)
        self.embeddings.append(embedding)
        print(f"✅ Added document #{len(self.documents)}")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Search for most relevant documents"""
        print(f"🔍 Searching for: {query}")
        
        # Generate embedding for the query
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": query
            }
        )
        
        query_embedding = response.json()['embedding']
        
        # Calculate similarities
        similarities = []
        for doc, doc_embedding in zip(self.documents, self.embeddings):
            similarity = self.cosine_similarity(query_embedding, doc_embedding)
            similarities.append((doc, similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def answer_question(self, question: str, model: str = "llama3.1:8b") -> str:
        """Answer a question using retrieved context"""
        print(f"💭 Question: {question}")
        print("-" * 60)
        
        # Retrieve relevant documents
        relevant_docs = self.search(question, top_k=3)
        
        print("📚 Retrieved context:")
        for i, (doc, score) in enumerate(relevant_docs, 1):
            print(f"  {i}. (score: {score:.3f}) {doc[:100]}...")
        print()
        
        # Build context from retrieved documents
        context = "\n\n".join([doc for doc, _ in relevant_docs])
        
        # Create prompt with context
        prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {question}

Answer:"""
        
        # Generate answer
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        answer = response.json()['response']
        print(f"🤖 Answer: {answer}")
        print()
        return answer

def main():
    """Demonstrate RAG with Ollama"""
    print("🚀 RAG (Retrieval-Augmented Generation) Example")
    print("=" * 60)
    print()
    
    # Initialize RAG system
    rag = SimpleRAG()
    
    # Add knowledge base documents
    print("📚 Building knowledge base...")
    print()
    
    documents = [
        "Docker is a platform for developing, shipping, and running applications in containers. Containers are lightweight, portable, and isolated environments.",
        "Ollama is a tool for running large language models locally. It supports models like Llama, Mistral, and Gemma on your own hardware.",
        "The MacBook Pro M2 has Apple Silicon with unified memory architecture. It provides excellent performance for machine learning workloads.",
        "Python is a high-level programming language known for its simplicity and readability. It's widely used in data science, web development, and automation.",
        "REST APIs use HTTP methods like GET, POST, PUT, and DELETE to perform operations. They communicate using JSON or XML data formats.",
        "Vector embeddings represent text as numerical vectors in high-dimensional space. Similar concepts have similar vectors.",
        "Kubernetes orchestrates containerized applications across multiple hosts. It handles deployment, scaling, and management automatically.",
        "Machine learning models require training data to learn patterns. The quality and quantity of data significantly impact model performance."
    ]
    
    for doc in documents:
        rag.add_document(doc)
    
    print()
    print("=" * 60)
    print()
    
    # Ask questions
    questions = [
        "What is Docker?",
        "How does Ollama work?",
        "What are vector embeddings?",
        "Tell me about the M2 chip"
    ]
    
    for question in questions:
        rag.answer_question(question, model="llama3.2:3b")
        print("=" * 60)
        print()

if __name__ == "__main__":
    main()

