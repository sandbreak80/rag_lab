#!/usr/bin/env python3
"""
Quick search examples - no LLM needed, just retrieval
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from search import VaultSearcher


def search_and_display(searcher, query, limit=5):
    """Search and display results nicely"""
    print(f"\n{'='*60}")
    print(f"🔍 Query: {query}")
    print(f"{'='*60}")
    
    results = searcher.search(query, limit=limit)
    
    if not results:
        print("❌ No results found")
        return
    
    print(f"\n✅ Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['metadata']['title']}")
        print(f"   📄 File: {result['metadata']['file_name']}")
        print(f"   📊 Score: {result['score']:.3f}")
        print(f"   📝 Preview: {result['content'][:150]}...")
        print()


def main():
    """Quick search examples"""
    print("="*60)
    print("🔍 Quick Search Examples")
    print("="*60)
    
    searcher = VaultSearcher()
    
    if not searcher.collection:
        print("❌ No index found. Please run: python src/indexer.py")
        return
    
    # Example searches
    queries = [
        "AI prompting techniques and best practices",
        "AppDynamics observability and monitoring",
        "LangChain framework and agents",
        "transformer architecture and attention mechanism",
    ]
    
    for query in queries:
        search_and_display(searcher, query, limit=3)
    
    print("="*60)
    print("💡 TIP: Use these search results to find relevant notes,")
    print("   then read the full files in Obsidian!")
    print("="*60)


if __name__ == "__main__":
    main()


