#!/usr/bin/env python3
"""
AI Blue Belt Study Helper - focused search and Q&A
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests
from search import VaultSearcher
import config


def search_bluebelt_content(searcher, query: str, limit: int = 5):
    """Search ONLY Blue Belt content"""
    results = searcher.search(query, limit=50)
    
    # Filter to Blue Belt only
    bluebelt_results = []
    for r in results:
        file_path = r['metadata'].get('file_path', '')
        if 'Blue Belt' in file_path:
            bluebelt_results.append(r)
            if len(bluebelt_results) >= limit:
                break
    
    return bluebelt_results


def ask_bluebelt_question(searcher, question: str):
    """
    Ask a question specifically about Blue Belt content
    Uses faster llama3.2:3b model for better performance
    """
    print(f"\n❓ Question: {question}")
    print("🔍 Searching Blue Belt materials...")
    
    # Search Blue Belt content
    results = search_bluebelt_content(searcher, question, limit=5)
    
    if not results:
        print("❌ No relevant Blue Belt content found!")
        return None
    
    print(f"✅ Found {len(results)} relevant Blue Belt documents\n")
    
    # Build context
    context_text = "# AI Blue Belt Study Materials\n\n"
    sources = []
    
    for i, result in enumerate(results, 1):
        context_text += f"## Source {i}: {result['metadata']['title']}\n"
        context_text += f"Relevance: {result['score']:.3f}\n\n"
        context_text += f"{result['content']}\n\n"
        context_text += "---\n\n"
        
        sources.append({
            "title": result['metadata']['title'],
            "file": result['metadata']['file_name'],
            "score": result['score']
        })
    
    # Create prompt focused on studying
    prompt = f"""Based on these AI Blue Belt study materials, answer this study question:

Question: {question}

{context_text}

Instructions:
- Focus on what's important for the Blue Belt certification
- Provide clear, concise explanations suitable for studying
- Cite which sources you used (by source number)
- If multiple sources cover the topic, synthesize the information

Answer:"""
    
    print("🤖 Generating answer with Ollama (llama3.2:3b for speed)...")
    
    # Use faster model
    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "llama3.2:3b",  # Faster model
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 400  # Concise answers for studying
                }
            },
            timeout=90
        )
        response.raise_for_status()
        answer = response.json()['response']
        
        print("\n" + "="*60)
        print("💡 ANSWER:")
        print("="*60)
        print(answer)
        
        print("\n" + "="*60)
        print("📚 BLUE BELT SOURCES:")
        print("="*60)
        for i, src in enumerate(sources, 1):
            print(f"{i}. {src['title']}")
            print(f"   File: {src['file']}")
            print(f"   Relevance: {src['score']:.3f}")
        
        return {"answer": answer, "sources": sources}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def study_session():
    """Interactive Blue Belt study session"""
    print("="*60)
    print("🎓 AI BLUE BELT STUDY HELPER")
    print("="*60)
    
    searcher = VaultSearcher()
    
    if not searcher.collection:
        print("❌ No index found!")
        return
    
    print(f"\n📚 Vault indexed: {searcher.collection.count()} chunks")
    
    # Check bluebelt content
    all_data = searcher.collection.get()
    bluebelt_count = sum(1 for m in all_data['metadatas'] 
                         if 'Blue Belt' in m.get('file_path', ''))
    
    print(f"📘 Blue Belt chunks: {bluebelt_count} ({bluebelt_count/searcher.collection.count()*100:.1f}%)")
    print("\nType your study questions (or 'quit' to exit)")
    print("="*60)
    
    while True:
        try:
            question = input("\n📝 Your question: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Good luck on your Blue Belt!")
                break
            
            ask_bluebelt_question(searcher, question)
            
        except KeyboardInterrupt:
            print("\n\n👋 Good luck on your Blue Belt!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Single question mode
        question = " ".join(sys.argv[1:])
        searcher = VaultSearcher()
        ask_bluebelt_question(searcher, question)
    else:
        # Interactive study session
        study_session()


if __name__ == "__main__":
    main()

