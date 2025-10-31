"""
Hybrid Search: Combines vector search (semantic) with BM25 (keyword) for better recall

Key benefits:
- Vector search: Finds conceptually similar content
- BM25 search: Finds exact keyword matches
- Fusion: Combines both for comprehensive results
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings

import config
from search import VaultSearcher


class HybridSearcher:
    """Hybrid search combining vector embeddings and BM25 keyword search"""
    
    def __init__(self, bm25_index_path: Path = None):
        """
        Initialize hybrid searcher
        
        Args:
            bm25_index_path: Path to BM25 index file (default: indices/bm25_index.pkl)
        """
        # Initialize vector searcher
        self.vector_searcher = VaultSearcher()
        
        # BM25 index
        self.bm25_index_path = bm25_index_path or (config.INDICES_PATH / "bm25_index.pkl")
        self.bm25 = None
        self.bm25_docs = []
        self.bm25_metadata = []
        
        # Load BM25 index if exists
        if self.bm25_index_path.exists():
            self._load_bm25_index()
            print(f"✅ Loaded BM25 index: {len(self.bm25_docs)} documents")
        else:
            print(f"⚠️  BM25 index not found at {self.bm25_index_path}")
            print(f"   Run: python src/hybrid_search.py --build-index")
    
    def _load_bm25_index(self):
        """Load BM25 index from disk"""
        with open(self.bm25_index_path, 'rb') as f:
            data = pickle.load(f)
            self.bm25 = data['bm25']
            self.bm25_docs = data['docs']
            self.bm25_metadata = data['metadata']
    
    def _save_bm25_index(self):
        """Save BM25 index to disk"""
        self.bm25_index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.bm25_index_path, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'docs': self.bm25_docs,
                'metadata': self.bm25_metadata
            }, f)
        print(f"💾 Saved BM25 index: {len(self.bm25_docs)} documents")
    
    def build_bm25_index(self):
        """Build BM25 index from ChromaDB collection"""
        print("\n🔨 Building BM25 Index...")
        
        if not self.vector_searcher.collection:
            print("❌ ChromaDB collection not found. Run indexer first.")
            return
        
        # Get all documents from ChromaDB
        all_docs = self.vector_searcher.collection.get(
            include=['documents', 'metadatas']
        )
        
        if not all_docs['documents']:
            print("❌ No documents found in ChromaDB")
            return
        
        print(f"📄 Found {len(all_docs['documents'])} documents")
        
        # Tokenize documents for BM25
        print("🔤 Tokenizing documents...")
        tokenized_docs = []
        self.bm25_docs = []
        self.bm25_metadata = []
        
        for i, doc in enumerate(all_docs['documents']):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(all_docs['documents'])}")
            
            # Simple tokenization (lowercase, split on whitespace and punctuation)
            tokens = self._tokenize(doc)
            tokenized_docs.append(tokens)
            self.bm25_docs.append(doc)
            self.bm25_metadata.append(all_docs['metadatas'][i])
        
        # Build BM25 index
        print("📊 Building BM25 index...")
        self.bm25 = BM25Okapi(tokenized_docs)
        
        # Save index
        self._save_bm25_index()
        
        print("✅ BM25 index built successfully!")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25
        
        Converts to lowercase and splits on whitespace/punctuation
        """
        import re
        # Lowercase
        text = text.lower()
        # Split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def bm25_search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of results with scores
        """
        if not self.bm25:
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                results.append({
                    'content': self.bm25_docs[idx],
                    'metadata': self.bm25_metadata[idx],
                    'score': float(scores[idx]),
                    'search_type': 'bm25'
                })
        
        return results
    
    def hybrid_search(self, 
                     query: str, 
                     limit: int = 10,
                     vector_weight: float = 0.5,
                     bm25_weight: float = 0.5,
                     tags: List[str] = None,
                     folder: str = None) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and BM25 results
        
        Args:
            query: Search query
            limit: Max results to return
            vector_weight: Weight for vector search (0-1)
            bm25_weight: Weight for BM25 search (0-1)
            tags: Filter by tags
            folder: Filter by folder
            
        Returns:
            Merged and re-ranked results
        """
        # Normalize weights
        total_weight = vector_weight + bm25_weight
        vector_weight = vector_weight / total_weight
        bm25_weight = bm25_weight / total_weight
        
        # Perform both searches
        vector_results = self.vector_searcher.search(
            query, 
            limit=limit * 2,  # Get more for better fusion
            tags=tags,
            folder=folder
        )
        
        bm25_results = self.bm25_search(query, limit=limit * 2)
        
        # Apply filters to BM25 results
        if folder:
            bm25_results = [
                r for r in bm25_results 
                if folder in r['metadata'].get('file_path', '')
            ]
        
        if tags:
            bm25_results = [
                r for r in bm25_results
                if any(tag in r['metadata'].get('tags', '[]') for tag in tags)
            ]
        
        # Merge using Reciprocal Rank Fusion (RRF)
        merged = self._reciprocal_rank_fusion(
            vector_results, 
            bm25_results,
            vector_weight,
            bm25_weight
        )
        
        return merged[:limit]
    
    def _reciprocal_rank_fusion(self, 
                                vector_results: List[Dict],
                                bm25_results: List[Dict],
                                vector_weight: float = 0.5,
                                bm25_weight: float = 0.5,
                                k: int = 60) -> List[Dict[str, Any]]:
        """
        Merge results using Reciprocal Rank Fusion (RRF)
        
        RRF formula: score = sum(weight / (k + rank))
        
        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            vector_weight: Weight for vector results
            bm25_weight: Weight for BM25 results
            k: RRF constant (default: 60)
            
        Returns:
            Merged and sorted results
        """
        # Build document ID map (use content hash as ID)
        doc_scores = defaultdict(lambda: {'score': 0, 'doc': None, 'sources': []})
        
        # Add vector results
        for rank, result in enumerate(vector_results, 1):
            doc_id = self._get_doc_id(result)
            rrf_score = vector_weight / (k + rank)
            doc_scores[doc_id]['score'] += rrf_score
            doc_scores[doc_id]['doc'] = result
            doc_scores[doc_id]['sources'].append(f"vector(rank={rank})")
        
        # Add BM25 results
        for rank, result in enumerate(bm25_results, 1):
            doc_id = self._get_doc_id(result)
            rrf_score = bm25_weight / (k + rank)
            doc_scores[doc_id]['score'] += rrf_score
            if doc_scores[doc_id]['doc'] is None:
                doc_scores[doc_id]['doc'] = result
            doc_scores[doc_id]['sources'].append(f"bm25(rank={rank})")
        
        # Sort by combined score
        merged = []
        for doc_id, data in sorted(doc_scores.items(), key=lambda x: x[1]['score'], reverse=True):
            result = data['doc'].copy()
            result['hybrid_score'] = data['score']
            result['search_sources'] = data['sources']
            merged.append(result)
        
        return merged
    
    def _get_doc_id(self, result: Dict[str, Any]) -> str:
        """Get unique document ID from result"""
        # Use combination of file_path and chunk_index as ID
        metadata = result.get('metadata', {})
        file_path = metadata.get('file_path', '')
        chunk_idx = metadata.get('chunk_index', 0)
        return f"{file_path}:{chunk_idx}"


def build_index():
    """Build BM25 index from command line"""
    print("🚀 Building BM25 Index for Hybrid Search")
    searcher = HybridSearcher()
    searcher.build_bm25_index()


def test_hybrid_search():
    """Test hybrid search"""
    print("🧪 Testing Hybrid Search\n")
    
    searcher = HybridSearcher()
    
    if not searcher.bm25:
        print("❌ BM25 index not found. Build it first:")
        print("   python src/hybrid_search.py --build-index")
        return
    
    # Test queries
    test_queries = [
        "Help me study for AI bluebelt",
        "What is prompt engineering?",
        "AppDynamics observability",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        # Vector only
        print("\n📊 Vector Search Only:")
        vector_results = searcher.vector_searcher.search(query, limit=3)
        for i, r in enumerate(vector_results, 1):
            print(f"{i}. {r['metadata']['title']} (score: {r['score']:.3f})")
        
        # BM25 only
        print("\n🔤 BM25 Search Only:")
        bm25_results = searcher.bm25_search(query, limit=3)
        for i, r in enumerate(bm25_results, 1):
            print(f"{i}. {r['metadata']['title']} (score: {r['score']:.3f})")
        
        # Hybrid
        print("\n🔀 Hybrid Search (Combined):")
        hybrid_results = searcher.hybrid_search(query, limit=5)
        for i, r in enumerate(hybrid_results, 1):
            sources = ', '.join(r.get('search_sources', []))
            print(f"{i}. {r['metadata']['title']}")
            print(f"   Score: {r.get('hybrid_score', 0):.4f} | Sources: {sources}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--build-index':
        build_index()
    else:
        test_hybrid_search()

