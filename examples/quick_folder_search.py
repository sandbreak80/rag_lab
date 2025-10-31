#!/usr/bin/env python3
"""
Quick folder search - search only, no LLM (fast!)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from search import VaultSearcher


def search_in_folder(folder_filter: str, query: str, limit: int = 10):
    """Quick search within a specific folder"""
    searcher = VaultSearcher()
    
    print(f"\n🔍 Searching '{folder_filter}' for: {query}")
    print("="*60)
    
    # Get more results than needed
    results = searcher.search(query, limit=50)
    
    # Filter to specified folder
    folder_results = []
    for r in results:
        file_path = r['metadata'].get('file_path', '')
        if folder_filter.lower() in file_path.lower():
            folder_results.append(r)
            if len(folder_results) >= limit:
                break
    
    if not folder_results:
        print(f"❌ No results found in '{folder_filter}' folder!")
        print("\nTrying broader search...")
        
        # Show what WAS found
        print("\nTop results (not filtered):")
        for i, r in enumerate(results[:5], 1):
            folder = r['metadata'].get('folder', 'N/A')
            print(f"  {i}. {r['metadata']['file_name']} (folder: {folder})")
        return []
    
    print(f"✅ Found {len(folder_results)} results in '{folder_filter}':\n")
    
    for i, result in enumerate(folder_results, 1):
        print(f"{i}. {result['metadata']['title']}")
        print(f"   📄 File: {result['metadata']['file_name']}")
        print(f"   📊 Relevance: {result['score']:.3f}")
        print(f"   📝 Preview: {result['content'][:120]}...")
        print()
    
    return folder_results


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python quick_folder_search.py <folder> <query>")
        print()
        print("Examples:")
        print("  python quick_folder_search.py 'Green Belt' 'prompt engineering'")
        print("  python quick_folder_search.py 'Blue Belt' 'responsible AI'")
        print("  python quick_folder_search.py 'Projects' 'observability'")
        sys.exit(1)
    
    folder = sys.argv[1]
    query = ' '.join(sys.argv[2:])
    
    search_in_folder(folder, query)


if __name__ == "__main__":
    main()

