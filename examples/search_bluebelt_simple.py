#!/usr/bin/env python3
"""
Simple: Search Blue Belt content by post-filtering results
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
    
    # Get more results than needed, then filter
    results = searcher.search(query, limit=50)
    
    # Filter to only Blue Belt content
    bluebelt_results = []
    for r in results:
        file_path = r['metadata'].get('file_path', '')
        folder = r['metadata'].get('folder', '')
        
        # Check if in Blue Belt folder
        if 'Blue Belt' in file_path or 'Blue Belt' in folder:
            bluebelt_results.append(r)
            if len(bluebelt_results) >= limit:
                break
    
    if not bluebelt_results:
        print("\n❌ No results found in Blue Belt folder!")
        print("\nTrying broader search...")
        
        # Show what WAS found
        print("\nTop results (not in Blue Belt):")
        for i, r in enumerate(results[:3], 1):
            print(f"  {i}. {r['metadata']['file_name']} (score: {r['score']:.3f})")
        return
    
    print(f"\n✅ Found {len(bluebelt_results)} Blue Belt results:\n")
    
    for i, result in enumerate(bluebelt_results, 1):
        print(f"{i}. {result['metadata']['title']}")
        print(f"   📄 File: {result['metadata']['file_name']}")
        print(f"   📊 Score: {result['score']:.3f}")
        print(f"   📝 Preview: {result['content'][:150]}...")
        print()
    
    return bluebelt_results


def main():
    """Test bluebelt search"""
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        search_bluebelt(query, limit=10)
    else:
        # Demo queries
        print("Testing Blue Belt-specific searches:\n")
        
        queries = [
            "study AI bluebelt certification",
            "responsible AI principles Cisco",
            "transformer attention mechanism",
            "prompt engineering techniques",
            "LangChain agents",
        ]
        
        for query in queries:
            results = search_bluebelt(query, limit=3)
            print("\n" + "="*60 + "\n")
            if not results:
                break


if __name__ == "__main__":
    main()

