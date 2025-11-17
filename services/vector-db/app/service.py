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
    """Prometheus metrics endpoint"""
    metrics_bytes, content_type = metrics.get_prometheus_metrics()
    from flask import Response
    return Response(metrics_bytes, mimetype=content_type)

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
        "where": {"file_name": "example.md"},  // optional (legacy)
        "metadata_filters": {...}              // optional (new format)
    }
    """
    try:
        data = request.json

        query_embeddings = data.get('query_embeddings', [])
        n_results = data.get('n_results', DEFAULT_SEARCH_LIMIT)
        where = data.get('where', None)
        metadata_filters = data.get('metadata_filters', None)

        if not query_embeddings:
            return jsonify({'error': 'query_embeddings required'}), 400

        # Convert metadata_filters to ChromaDB where clause
        if metadata_filters and not where:
            where = _build_chroma_where_clause(metadata_filters)
            if where:
                print(f"🔍 Applying metadata filters: {where}")

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

def _build_chroma_where_clause(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert metadata filters to ChromaDB where clause format

    ChromaDB where clause format:
    - {"field": "value"} - exact match
    - {"field": {"$in": ["value1", "value2"]}} - OR match
    - {"$and": [{"field1": "value1"}, {"field2": "value2"}]} - AND multiple conditions
    """
    conditions = []

    # Document types filter
    if filters.get('documentTypes'):
        conditions.append({
            "$or": [
                {"type": {"$in": filters['documentTypes']}},
                {"file_type": {"$in": filters['documentTypes']}}
            ]
        })

    # Sources filter
    if filters.get('sources'):
        conditions.append({"source": {"$in": filters['sources']}})

    # Tags filter (check if any tag matches)
    if filters.get('tags'):
        # Note: ChromaDB might not support array contains, so this may need adjustment
        conditions.append({"tags": {"$in": filters['tags']}})

    # Date range filter
    if filters.get('dateRange'):
        date_range = filters['dateRange']
        if date_range.get('start'):
            conditions.append({
                "$or": [
                    {"created_at": {"$gte": date_range['start']}},
                    {"date": {"$gte": date_range['start']}}
                ]
            })
        if date_range.get('end'):
            conditions.append({
                "$or": [
                    {"created_at": {"$lte": date_range['end']}},
                    {"date": {"$lte": date_range['end']}}
                ]
            })

    # Authors filter
    if filters.get('authors'):
        conditions.append({"author": {"$in": filters['authors']}})

    # Combine all conditions with AND
    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}

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
            if embeddings is not None and len(embeddings) > 0:
                embeddings = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]
            response['embeddings'] = embeddings
            print(f"   ✅ Returning {len(embeddings) if embeddings else 0} embeddings")
        else:
            print(f"   ✅ Returning {len(result['documents'])} documents (no embeddings)")

        return jsonify(response)
    except Exception as e:
        metrics.increment('errors')
        import traceback
        print(f"❌ /get_all error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/list', methods=['GET'])
@timed(metrics, 'list_documents')
def list_documents():
    """
    List unique documents in the collection with pagination support

    Query Parameters:
        page: Page number (1-indexed, default: 1)
        page_size: Number of documents per page (default: 20, max: 100)

    Returns:
    {
        "documents": ["doc1.txt", "doc2.pdf", ...],
        "count": 2,
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5
    }
    """
    try:
        # Parse pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        # Validate pagination params
        page = max(1, page)  # Ensure page >= 1
        page_size = max(1, min(100, page_size))  # Clamp between 1 and 100

        # Get all metadatas to extract unique document IDs
        all_data = collection.get(include=['metadatas'])

        # Extract unique document_id or file_name from metadata
        unique_docs = set()
        if all_data['metadatas']:
            for meta in all_data['metadatas']:
                # Try document_id first, then file_name, then title
                doc_id = meta.get('document_id') or meta.get('file_name') or meta.get('title', 'unknown')
                if doc_id and doc_id != 'unknown':
                    unique_docs.add(doc_id)

        # Sort all documents
        documents_list = sorted(list(unique_docs))
        total = len(documents_list)

        # Calculate pagination
        total_pages = max(1, (total + page_size - 1) // page_size)  # Ceiling division
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # Slice the list for the requested page
        paginated_documents = documents_list[start_idx:end_idx]

        metrics.increment('lists')

        return jsonify({
            'documents': paginated_documents,
            'count': len(paginated_documents),  # Count of items in this page
            'total': total,  # Total number of documents
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        })
    except Exception as e:
        metrics.increment('errors')
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

