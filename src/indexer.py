"""
Vault indexer - scans markdown files and builds vector index
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import chromadb
from chromadb.config import Settings

from parser import MarkdownParser
from agentic_chunker import AgenticChunker
import config


class VaultIndexer:
    """Index a markdown vault and build vector store"""
    
    def __init__(self, vault_path: Path = None):
        self.vault_path = Path(vault_path or config.VAULT_PATH)
        self.indices_path = Path(config.INDICES_PATH)
        self.parser = MarkdownParser()
        
        # Initialize agentic chunker if enabled
        if config.AGENTIC_CHUNKING_ENABLED:
            self.agentic_chunker = AgenticChunker(
                target_chunk_size=config.AGENTIC_TARGET_CHUNK_SIZE,
                max_chunk_size=config.AGENTIC_MAX_CHUNK_SIZE
            )
            print(f"🤖 Agentic chunking: ENABLED (target={config.AGENTIC_TARGET_CHUNK_SIZE}, max={config.AGENTIC_MAX_CHUNK_SIZE})")
        else:
            self.agentic_chunker = None
            print(f"📏 Simple chunking: ENABLED (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(config.CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"📊 ChromaDB collection: {config.COLLECTION_NAME}")
        print(f"📦 Current documents: {self.collection.count()}")
    
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
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in vault"""
        files = []
        for ext in config.SUPPORTED_EXTENSIONS:
            files.extend(self.vault_path.rglob(f"*{ext}"))
        return sorted(files)
    
    def index_vault(self, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Index entire vault
        
        Args:
            force_reindex: If True, delete existing index and rebuild
            
        Returns:
            Statistics about indexing
        """
        print("\n" + "="*60)
        print("📚 INDEXING VAULT")
        print("="*60)
        
        start_time = time.time()
        
        if force_reindex:
            print("🗑️  Deleting existing index...")
            self.client.delete_collection(config.COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
        
        # Find all markdown files
        print(f"\n📁 Scanning vault: {self.vault_path}")
        files = self.find_markdown_files()
        print(f"📄 Found {len(files)} markdown files")
        
        if not files:
            print("⚠️  No markdown files found!")
            return {"files": 0, "chunks": 0, "time": 0}
        
        # Index files
        stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'chunks_created': 0,
            'errors': 0,
            'total_files': len(files)
        }
        
        print("\n🔄 Processing files...")
        for i, file_path in enumerate(files, 1):
            try:
                # Show progress MORE frequently
                print(f"  Progress: {i}/{len(files)} ({i*100//len(files)}%) - {file_path.name}")
                
                # Parse file
                parsed = self.parser.parse_file(file_path)
                if not parsed or not parsed['content'].strip():
                    stats['files_skipped'] += 1
                    print(f"    ⏭️  Skipped (empty)")
                    continue
                
                # Chunk content (agentic or simple)
                if self.agentic_chunker:
                    # Use agentic chunking
                    chunk_objects = self.agentic_chunker.chunk_markdown(
                        parsed['content'],
                        parsed
                    )
                    print(f"    📦 {len(chunk_objects)} chunks (agentic)")
                    
                    # Index each chunk
                    for chunk_obj in chunk_objects:
                        self._index_agentic_chunk(parsed, chunk_obj)
                        stats['chunks_created'] += 1
                else:
                    # Use simple chunking
                    chunks = self.parser.chunk_content(
                        parsed['content'],
                        chunk_size=config.CHUNK_SIZE,
                        overlap=config.CHUNK_OVERLAP
                    )
                    print(f"    📦 {len(chunks)} chunks (simple)")
                    
                    # Index each chunk
                    for chunk_idx, chunk in enumerate(chunks):
                        self._index_chunk(parsed, chunk, chunk_idx, len(chunks))
                        stats['chunks_created'] += 1
                
                stats['files_processed'] += 1
                print(f"    ✅ Indexed")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                stats['errors'] += 1
                # Continue processing other files
                continue
        
        elapsed = time.time() - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("✅ INDEXING COMPLETE")
        print("="*60)
        print(f"📄 Files processed: {stats['files_processed']}")
        print(f"⏭️  Files skipped: {stats['files_skipped']}")
        print(f"📦 Chunks created: {stats['chunks_created']}")
        print(f"❌ Errors: {stats['errors']}")
        print(f"⏱️  Time: {elapsed:.1f}s")
        print(f"⚡ Speed: {stats['files_processed']/elapsed:.1f} files/sec")
        print("="*60 + "\n")
        
        stats['time'] = elapsed
        return stats
    
    def _index_agentic_chunk(self, parsed: Dict[str, Any], chunk_obj):
        """Index a single agentic chunk"""
        # ChunkWithContext has: text, metadata (dict), semantic_units (list)
        chunk_meta = chunk_obj.metadata if isinstance(chunk_obj.metadata, dict) else {}
        
        # Generate unique ID
        chunk_idx = chunk_meta.get('chunk_index', 0)
        doc_id = f"{Path(parsed['file_path']).stem}_{chunk_idx}"
        
        # Prepare metadata (combine parsed metadata with chunk metadata)
        metadata = {
            'file_path': parsed['file_path'],
            'file_name': parsed['file_name'],
            'title': parsed['title'],
            'chunk_index': chunk_idx,
            'modified_time': parsed['modified_time'],
            'chunking_method': 'agentic',
        }
        
        # Add agentic chunk metadata
        if 'sections' in chunk_meta:
            sections = chunk_meta['sections']
            if isinstance(sections, list):
                metadata['sections'] = json.dumps(sections)
        if 'unit_types' in chunk_meta:
            unit_types = chunk_meta['unit_types']
            if isinstance(unit_types, list):
                metadata['unit_types'] = json.dumps(unit_types)
        if 'num_units' in chunk_meta:
            metadata['num_units'] = chunk_meta['num_units']
        
        # Add tags as metadata
        if parsed.get('tags'):
            metadata['tags'] = json.dumps(parsed['tags'])
        
        # Add wikilinks
        if parsed.get('wikilinks'):
            metadata['wikilinks'] = json.dumps(parsed['wikilinks'])
        
        # Generate embedding
        embedding = self.generate_embedding(chunk_obj.text)
        
        # Add to collection
        self.collection.add(
            ids=[doc_id],
            documents=[chunk_obj.text],
            metadatas=[metadata],
            embeddings=[embedding]
        )
    
    def _index_chunk(self, parsed: Dict[str, Any], chunk: str, 
                     chunk_idx: int, total_chunks: int):
        """Index a single chunk (simple chunking)"""
        # Generate unique ID
        doc_id = f"{Path(parsed['file_path']).stem}_{chunk_idx}"
        
        # Prepare metadata
        metadata = {
            'file_path': parsed['file_path'],
            'file_name': parsed['file_name'],
            'title': parsed['title'],
            'chunk_index': chunk_idx,
            'total_chunks': total_chunks,
            'modified_time': parsed['modified_time'],
            'chunking_method': 'simple',
        }
        
        # Add tags as metadata
        if parsed['tags']:
            metadata['tags'] = json.dumps(parsed['tags'])
        
        # Add wikilinks
        if parsed['wikilinks']:
            metadata['wikilinks'] = json.dumps(parsed['wikilinks'])
        
        # Add custom metadata from frontmatter
        for key, value in parsed['metadata'].items():
            if key not in ['tags', 'tag', 'title'] and isinstance(value, (str, int, float, bool)):
                metadata[f"meta_{key}"] = str(value)
        
        # Generate embedding
        embedding = self.generate_embedding(chunk)
        
        # Add to collection
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[metadata]
        )
    
    def update_file(self, file_path: Path):
        """Update index for a single file"""
        print(f"🔄 Updating: {file_path.name}")
        
        # Remove existing chunks for this file
        stem = file_path.stem
        try:
            # Query for existing chunks
            results = self.collection.get(
                where={"file_name": file_path.name}
            )
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"  Removed {len(results['ids'])} old chunks")
        except Exception as e:
            print(f"  Warning: {e}")
        
        # Re-index file
        parsed = self.parser.parse_file(file_path)
        if parsed and parsed['content'].strip():
            chunks = self.parser.chunk_content(
                parsed['content'],
                chunk_size=config.CHUNK_SIZE,
                overlap=config.CHUNK_OVERLAP
            )
            
            for chunk_idx, chunk in enumerate(chunks):
                self._index_chunk(parsed, chunk, chunk_idx, len(chunks))
            
            print(f"  ✅ Indexed {len(chunks)} chunks")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        count = self.collection.count()
        
        # Get unique files
        all_data = self.collection.get()
        unique_files = set()
        if all_data['metadatas']:
            unique_files = set(m.get('file_name', '') for m in all_data['metadatas'])
        
        return {
            'total_chunks': count,
            'unique_files': len(unique_files),
            'collection_name': config.COLLECTION_NAME,
            'vault_path': str(self.vault_path)
        }


def main():
    """Main indexing function"""
    import sys
    
    print("🚀 Markdown RAG Indexer")
    print(f"📁 Vault: {config.VAULT_PATH}")
    
    if not config.VAULT_PATH.exists():
        print(f"❌ Vault path does not exist: {config.VAULT_PATH}")
        sys.exit(1)
    
    indexer = VaultIndexer()
    
    # Check if re-indexing
    force = '--force' in sys.argv or '--reindex' in sys.argv
    
    if force:
        print("⚠️  Force re-index requested")
    
    # Index vault
    stats = indexer.index_vault(force_reindex=force)
    
    # Show final stats
    print("\n📊 Index Statistics:")
    final_stats = indexer.get_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    main()

