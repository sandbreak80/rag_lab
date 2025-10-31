#!/usr/bin/env python3
"""
Interactive Q&A with your Obsidian vault using RAG
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
from search import VaultSearcher
import config


def ask_question(searcher: VaultSearcher, question: str, num_contexts: int = 5):
    """
    Ask a question and get an answer based on your vault
    
    Args:
        searcher: VaultSearcher instance
        question: Your question
        num_contexts: Number of context chunks to use
        
    Returns:
        dict with answer, sources, and contexts
    """
    print(f"\n❓ Question: {question}")
    print("🔍 Searching vault...")
    
    # 1. Search for relevant context
    results = searcher.search(question, limit=num_contexts)
    
    if not results:
        return {
            "answer": "No relevant information found in your vault.",
            "sources": [],
            "contexts": []
        }
    
    print(f"✅ Found {len(results)} relevant chunks")
    
    # 2. Build context for LLM
    context_text = "# Relevant Information from Your Vault\n\n"
    sources = []
    
    for i, result in enumerate(results, 1):
        context_text += f"## Source {i}: {result['metadata']['title']}\n"
        context_text += f"File: {result['metadata']['file_name']}\n"
        context_text += f"Relevance: {result['score']:.3f}\n\n"
        context_text += f"{result['content']}\n\n"
        context_text += "---\n\n"
        
        sources.append({
            "title": result['metadata']['title'],
            "file": result['metadata']['file_name'],
            "score": result['score']
        })
    
    # 3. Create prompt for LLM
    prompt = f"""Based on the following information from my knowledge vault, please answer this question:

Question: {question}

{context_text}

Instructions:
- Answer the question using ONLY the information provided above
- If the information isn't sufficient, say so
- Cite which sources you used (by source number)
- Be concise but thorough

Answer:"""
    
    print("🤖 Generating answer with Ollama...")
    
    # 4. Get answer from Ollama
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": config.CHAT_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Lower temperature for factual answers
                    "num_predict": 500
                }
            },
            timeout=60
        )
        response.raise_for_status()
        answer = response.json()['response']
        
        print("✅ Answer generated\n")
        
        return {
            "answer": answer,
            "sources": sources,
            "contexts": [r['content'] for r in results],
            "prompt_length": len(prompt)
        }
        
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        return {
            "answer": f"Error: {e}",
            "sources": sources,
            "contexts": []
        }


def main():
    """Interactive Q&A session"""
    print("="*60)
    print("🧠 Ask Questions About Your Obsidian Vault")
    print("="*60)
    
    searcher = VaultSearcher()
    
    if not searcher.collection:
        print("❌ No index found. Please run: python src/indexer.py")
        return
    
    print(f"\n📚 Vault indexed: {searcher.collection.count()} chunks")
    print("\nType your questions below (or 'quit' to exit)")
    print("="*60)
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Ask the question
            result = ask_question(searcher, question, num_contexts=5)
            
            # Display answer
            print("\n" + "="*60)
            print("💡 ANSWER:")
            print("="*60)
            print(result['answer'])
            
            # Display sources
            print("\n" + "="*60)
            print("📚 SOURCES:")
            print("="*60)
            for i, source in enumerate(result['sources'], 1):
                print(f"{i}. {source['title']}")
                print(f"   File: {source['file']}")
                print(f"   Relevance: {source['score']:.3f}")
            
            print("\n" + "="*60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
