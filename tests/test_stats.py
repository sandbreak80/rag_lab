#!/usr/bin/env python3
"""Test stats endpoint logic"""
import sys
sys.path.insert(0, 'src')

from advanced_search import AdvancedSearcher
import config

print("Initializing searcher...")
searcher = AdvancedSearcher()
search_mode = 'advanced'

print(f"Search mode: {search_mode}")
print(f"Searcher type: {type(searcher)}")

# Try to get collection
try:
    collection = None
    
    if hasattr(searcher, 'collection'):
        print("✅ Has direct collection attribute")
        collection = searcher.collection
    elif hasattr(searcher, 'hybrid_searcher'):
        print("✅ Has hybrid_searcher attribute")
        if hasattr(searcher.hybrid_searcher, 'vector_searcher'):
            print("✅ Has vector_searcher attribute")
            collection = searcher.hybrid_searcher.vector_searcher.collection
    elif hasattr(searcher, 'vector_searcher'):
        print("✅ Has vector_searcher attribute (direct)")
        collection = searcher.vector_searcher.collection
    
    if collection:
        count = collection.count()
        print(f"✅ Collection count: {count}")
        
        result = {
            'total_chunks': count,
            'embedding_model': config.EMBEDDING_MODEL,
            'chat_model': config.CHAT_MODEL,
            'vault_path': str(config.VAULT_PATH),
            'search_mode': search_mode
        }
        print(f"✅ Result: {result}")
    else:
        print("❌ No collection found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

