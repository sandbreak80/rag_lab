#!/usr/bin/env python3
"""
Search specifically in the Blue Belt folder
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from search import VaultSearcher


def search_bluebelt(query: str, limit: int = 10):
    """Search only in Blue Belt content"""
    searcher = VaultSearcher()
    
    print("="*60)
    print(f"🔍 Searching Blue Belt content for: {query}")
    print("="*60)
    
    # Search with folder filter
    results = searcher.search(
        query, 
        limit=limit * 2,  # Get more to account for filtering
        folder_contains="Blue Belt"
    )
    
    if not results:
        print("\n❌ No results found in Blue Belt folder!")
        return
    
    print(f"\n✅ Found {len(results)} results:\n")
    
    for i, result in enumerate(results[:limit], 1):
        print(f"{i}. {result['metadata']['title']}")
        print(f"   📄 File: {result['metadata']['file_name']}")
        print(f"   📊 Score: {result['score']:.3f}")
        print(f"   📝 Preview: {result['content'][:150]}...")
        print()


def main():
    """Demo searches for bluebelt content"""
    queries = [
        "responsible AI principles",
        "transformer architecture and attention",
        "prompt engineering techniques",
        "LangChain agents and frameworks",
        "fine-tuning LLMs with HuggingFace",
    ]
    
    for query in queries:
        search_bluebelt(query, limit=3)
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Search for provided query
        query = " ".join(sys.argv[1:])
        search_bluebelt(query, limit=10)
    else:
        # Run demo
        main()

