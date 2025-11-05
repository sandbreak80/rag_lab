"""
Vector Database Service - ChromaDB wrapper
Provides vector storage and similarity search
"""
from flask import Flask, request, jsonify
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
import sys
import os

# Add common to path
sys.path.insert(0, '/workspace/services/common')
from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

app = Flask(__name__)

# Initialize metrics
metrics = ServiceMetrics("vector-db")

# Initialize health checks
health = HealthCheck("vector-db")

# Initialize ChromaDB client
client = None
collection = None

def init_chromadb():
    """Initialize ChromaDB"""
    global client, collection

    try:
        client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        print(f"✅ ChromaDB initialized: {COLLECTION_NAME}")
        print(f"📦 Current documents: {collection.count()}")
        return True
    except Exception as e:
        print(f"❌ ChromaDB init error: {e}")
        return False

# Add health checks
health.add_check("chromadb", lambda: client is not None and collection is not None)
health.add_check("collection_accessible", lambda: collection.count() >= 0)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_stats())

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        count = collection.count()

        # Get unique files
        all_data = collection.get(include=['metadatas'])
        unique_files = set()
        if all_data['metadatas']:
            unique_files = set(m.get('file_name', '') for m in all_data['metadatas'])

        stats = {
            'total_chunks': count,
            'unique_files': len(unique_files),
            'collection_name': COLLECTION_NAME,
            'embedding_model': EMBEDDING_MODEL
        }

        metrics.set_gauge('total_chunks', count)
        metrics.set_gauge('unique_files', len(unique_files))

        return jsonify(stats)
    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/add', methods=['POST'])
@timed(metrics, 'add_documents')
def add_documents():
    """
    Add documents to the collection

    Body:
    {
        "ids": ["doc1", "doc2"],
        "documents": ["text1", "text2"],
        "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
        "metadatas": [{"key": "value"}, ...]
    }
    """
    try:
        data = request.json

        ids = data.get('ids', [])
        documents = data.get('documents', [])
        embeddings = data.get('embeddings', [])
        metadatas = data.get('metadatas', [])

        if not ids or not documents or not embeddings:
            return jsonify({'error': 'ids, documents, and embeddings required'}), 400

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas if metadatas else None
        )

        metrics.increment('documents_added', len(ids))

        return jsonify({
            'status': 'success',
            'added': len(ids)
        })
    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
@timed(metrics, 'search')
def search():
    """
    Vector similarity search

    Body:
    {
        "query_embeddings": [[0.1, 0.2, ...]],
        "n_results": 10,
        "where": {"file_name": "example.md"}  // optional
    }
    """
    try:
        data = request.json

        query_embeddings = data.get('query_embeddings', [])
        n_results = data.get('n_results', DEFAULT_SEARCH_LIMIT)
        where = data.get('where', None)

        if not query_embeddings:
            return jsonify({'error': 'query_embeddings required'}), 400

        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

        metrics.increment('searches')

        return jsonify(results)
    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['POST'])
@timed(metrics, 'delete_documents')
def delete_documents():
    """
    Delete documents

    Body:
    {
        "ids": ["doc1", "doc2"]
    }
    or
    {
        "where": {"file_name": "example.md"}
    }
    """
    try:
        data = request.json

        ids = data.get('ids', None)
        where = data.get('where', None)

        if not ids and not where:
            return jsonify({'error': 'ids or where required'}), 400

        if ids:
            collection.delete(ids=ids)
            deleted = len(ids)
        else:
            # First get ids matching where clause
            results = collection.get(where=where)
            if results['ids']:
                collection.delete(ids=results['ids'])
                deleted = len(results['ids'])
            else:
                deleted = 0

        metrics.increment('documents_deleted', deleted)

        return jsonify({
            'status': 'success',
            'deleted': deleted
        })
    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/get_all', methods=['POST'])
@timed(metrics, 'get_all_documents')
def get_all_documents():
    """
    Get all documents from the collection

    Body (optional):
    {
        "include_embeddings": true  // Default: false
    }

    Returns:
    {
        "documents": [...],
        "metadatas": [...],
        "embeddings": [...],  // Only if include_embeddings=true
        "ids": [...]
    }
    """
    try:
        data = request.json or {}
        include_embeddings = data.get('include_embeddings', False)

        print(f"📥 /get_all request: include_embeddings={include_embeddings}")

        # Build include list
        include = ['documents', 'metadatas']
        if include_embeddings:
            include.append('embeddings')

        print(f"   Fetching with include={include}")

        # Get all documents
        result = collection.get(include=include)

        response = {
            'documents': result['documents'],
            'metadatas': result['metadatas'],
            'ids': result['ids'],
            'count': len(result['documents'])
        }

        # Add embeddings if requested
        if include_embeddings:
            embeddings = result.get('embeddings', [])
            # Convert NumPy arrays to lists for JSON serialization
            if embeddings and len(embeddings) > 0:
                embeddings = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]
            response['embeddings'] = embeddings
            print(f"   ✅ Returning {len(embeddings)} embeddings")
        else:
            print(f"   ✅ Returning {len(result['documents'])} documents (no embeddings)")

        return jsonify(response)
    except Exception as e:
        metrics.increment('errors')
        import traceback
        print(f"❌ /get_all error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/get', methods=['POST'])
@timed(metrics, 'get_documents')
def get_documents():
    """
    Get documents by filter

    Body:
    {
        "where": {"file_name": "example.md"}
    }
    """
    try:
        data = request.json
        where = data.get('where', None)

        results = collection.get(
            where=where,
            include=['documents', 'metadatas', 'embeddings']
        )

        metrics.increment('gets')

        return jsonify(results)
    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_collection():
    """Reset/clear the collection"""
    try:
        global collection

        # Delete and recreate
        client.delete_collection(COLLECTION_NAME)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        metrics.increment('resets')

        return jsonify({'status': 'success', 'message': 'Collection reset'})
    except Exception as e:
        metrics.increment('errors')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Vector DB Service starting...")
    print(f"📊 Collection: {COLLECTION_NAME}")
    print(f"💾 Path: {CHROMA_DB_PATH}")

    # Initialize ChromaDB
    if not init_chromadb():
        print("❌ Failed to initialize ChromaDB")
        sys.exit(1)

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

