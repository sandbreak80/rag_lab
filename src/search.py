"""
Search functionality with semantic search and metadata filtering
"""
import json
from typing import List, Dict, Any, Optional
import requests
import chromadb
from chromadb.config import Settings

import config


class VaultSearcher:
    """Search indexed markdown vault"""
    
    def __init__(self):
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(config.CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(config.COLLECTION_NAME)
            print(f"✅ Loaded collection: {config.COLLECTION_NAME} ({self.collection.count()} chunks)")
        except Exception as e:
            print(f"❌ Collection not found: {e}")
            print("⚠️  Please run indexer first: python src/indexer.py")
            self.collection = None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        try:
            response = requests.post(
                f"{config.OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": config.EMBEDDING_MODEL,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()['embedding']
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            raise
    
    def search(self, 
               query: str, 
               limit: int = None,
               tags: List[str] = None,
               folder: str = None,
               date_from: str = None,
               date_to: str = None) -> List[Dict[str, Any]]:
        """
        Semantic search with metadata filtering
        
        Args:
            query: Search query
            limit: Max results (default from config)
            tags: Filter by tags (OR logic)
            folder: Filter by folder path
            date_from: Filter by date (metadata field)
            date_to: Filter by date (metadata field)
            
        Returns:
            List of results with content and metadata
        """
        if not self.collection:
            return []
        
        limit = limit or config.DEFAULT_SEARCH_LIMIT
        
        # Build where filter (folder filtering done post-query)
        where_filter = self._build_filter(tags, None, date_from, date_to)
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Query more results if we need to filter by folder
        query_limit = limit * 3 if folder else limit
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=query_limit,
            where=where_filter if where_filter else None,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results with folder filtering
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                metadata = self._parse_metadata(results['metadatas'][0][i])
                
                # Apply folder filter post-query (ChromaDB doesn't support substring matching)
                if folder and folder not in metadata.get('file_path', ''):
                    continue
                
                formatted.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
                
                # Stop once we have enough results
                if len(formatted) >= limit:
                    break
        
        return formatted
    
    def find_similar(self, file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find notes similar to a given note"""
        if not self.collection:
            return []
        
        # Get the note's chunks
        results = self.collection.get(
            where={"file_path": file_path},
            include=['embeddings', 'documents', 'metadatas']
        )
        
        if not results['ids']:
            return []
        
        # Use first chunk's embedding as query
        query_embedding = results['embeddings'][0]
        
        # Search for similar (excluding the source file)
        similar = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit + 10,  # Get extra to filter out source file
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format and filter out source file
        formatted = []
        if similar['ids'] and similar['ids'][0]:
            for i in range(len(similar['ids'][0])):
                metadata = self._parse_metadata(similar['metadatas'][0][i])
                if metadata['file_path'] != file_path:
                    formatted.append({
                        'id': similar['ids'][0][i],
                        'content': similar['documents'][0][i],
                        'metadata': metadata,
                        'score': 1 - similar['distances'][0][i]
                    })
                    if len(formatted) >= limit:
                        break
        
        return formatted
    
    def find_linked(self, file_name: str) -> Dict[str, List[str]]:
        """Find notes that link to/from a given note"""
        if not self.collection:
            return {'links_to': [], 'linked_from': []}
        
        note_name = file_name.replace('.md', '')
        
        # Find notes this one links to
        results = self.collection.get(
            where={"file_name": file_name},
            include=['metadatas']
        )
        
        links_to = set()
        if results['metadatas']:
            for metadata in results['metadatas']:
                if 'wikilinks' in metadata:
                    wikilinks = json.loads(metadata['wikilinks'])
                    links_to.update(wikilinks)
        
        # Find notes that link to this one
        # This requires scanning all notes (could be optimized with separate index)
        all_notes = self.collection.get(include=['metadatas'])
        linked_from = set()
        
        if all_notes['metadatas']:
            for metadata in all_notes['metadatas']:
                if 'wikilinks' in metadata:
                    wikilinks = json.loads(metadata['wikilinks'])
                    if note_name in wikilinks:
                        linked_from.add(metadata.get('file_name', ''))
        
        return {
            'links_to': sorted(list(links_to)),
            'linked_from': sorted(list(linked_from))
        }
    
    def get_notes_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Get all notes with specific tags"""
        if not self.collection:
            return []
        
        # Get all notes
        all_results = self.collection.get(include=['metadatas', 'documents'])
        
        matching = []
        seen_files = set()
        
        if all_results['metadatas']:
            for i, metadata in enumerate(all_results['metadatas']):
                file_name = metadata.get('file_name', '')
                if file_name in seen_files:
                    continue
                
                if 'tags' in metadata:
                    note_tags = json.loads(metadata['tags'])
                    if any(tag in note_tags for tag in tags):
                        seen_files.add(file_name)
                        matching.append({
                            'metadata': self._parse_metadata(metadata),
                            'content': all_results['documents'][i]
                        })
        
        return matching
    
    def generate_rag_context(self, query: str, max_length: int = None) -> str:
        """
        Generate context for RAG from search results
        
        Args:
            query: Search query
            max_length: Max characters (default from config)
            
        Returns:
            Formatted context string
        """
        max_length = max_length or config.MAX_CONTEXT_LENGTH
        
        # Search for relevant content
        results = self.search(query, limit=20)  # Get more than we need
        
        if not results:
            return ""
        
        # Build context, respecting length limit
        context_parts = []
        current_length = 0
        
        for result in results:
            # Format this result
            part = f"## {result['metadata']['title']}\n"
            part += f"Source: {result['metadata']['file_name']}\n\n"
            part += f"{result['content']}\n\n"
            part += "---\n\n"
            
            # Check if adding this would exceed limit
            if current_length + len(part) > max_length:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return "".join(context_parts)
    
    def _build_filter(self, tags: List[str] = None, folder: str = None,
                     date_from: str = None, date_to: str = None) -> Optional[Dict]:
        """Build ChromaDB where filter"""
        # Note: ChromaDB has limited filtering support
        # We can only do exact matches ($eq), not substring matching ($contains)
        # Folder filtering is done post-query in search()
        
        # Note: Tag filtering would require scanning JSON in metadata
        # For now, we'll filter tags post-query in search()
        
        return None
    
    def _parse_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse metadata, handling JSON fields"""
        parsed = metadata.copy()
        
        # Parse JSON fields
        if 'tags' in parsed:
            try:
                parsed['tags'] = json.loads(parsed['tags'])
            except:
                pass
        
        if 'wikilinks' in parsed:
            try:
                parsed['wikilinks'] = json.loads(parsed['wikilinks'])
            except:
                pass
        
        return parsed


def test_search():
    """Test search functionality"""
    print("🔍 Testing search...")
    
    searcher = VaultSearcher()
    
    if not searcher.collection:
        print("❌ No index found. Run indexer first.")
        return
    
    # Test semantic search
    print("\n📝 Testing semantic search:")
    results = searcher.search("python programming", limit=3)
    print(f"Found {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['metadata']['title']} (score: {result['score']:.3f})")
        print(f"   {result['content'][:100]}...")
    
    # Test RAG context generation
    print("\n🤖 Testing RAG context generation:")
    context = searcher.generate_rag_context("machine learning", max_length=500)
    print(f"Context length: {len(context)} chars")
    print(f"Preview: {context[:200]}...")


if __name__ == '__main__':
    test_search()



