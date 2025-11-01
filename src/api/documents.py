"""
Documents API routes
"""
from flask import Blueprint, request, jsonify
import requests
import os

bp = Blueprint('documents', __name__)

@bp.route('/documents', methods=['GET'])
def get_documents():
    """Get list of documents"""
    try:
        # Try to get from vector DB stats
        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')
        response = requests.get(f"{vector_db_url}/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            documents = stats.get('unique_files', [])
            return jsonify({'documents': documents})
        
        return jsonify({'documents': []})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Forward to ingest service
        ingest_url = os.getenv('INGEST_SERVICE_URL', 'http://ingest-service:8001')
        
        files = {'file': (file.filename, file.stream, file.content_type)}
        response = requests.post(
            f"{ingest_url}/upload",
            files=files,
            timeout=300  # 5 minutes for large files
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Upload failed'}), response.status_code
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        # Get stats from vector DB
        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')
        response = requests.get(f"{vector_db_url}/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            
            # Get knowledge graph stats
            try:
                kg_url = os.getenv('KNOWLEDGE_GRAPH_URL', 'http://knowledge-graph:8007')
                kg_response = requests.get(f"{kg_url}/stats", timeout=5)
                if kg_response.status_code == 200:
                    kg_stats = kg_response.json()
                    stats['knowledge_graph_nodes'] = kg_stats.get('nodes', 0)
                    stats['knowledge_graph_edges'] = kg_stats.get('edges', 0)
            except:
                stats['knowledge_graph_nodes'] = 0
                stats['knowledge_graph_edges'] = 0
            
            # Format for frontend
            return jsonify({
                'chunks': stats.get('total_chunks', 0),
                'documents': stats.get('unique_files', []),
                'unique_tags': len(stats.get('unique_tags', [])),
                'bm25_index_size': stats.get('bm25_index_size', 0),
                'knowledge_graph_nodes': stats.get('knowledge_graph_nodes', 0),
                'knowledge_graph_edges': stats.get('knowledge_graph_edges', 0),
            })
        
        return jsonify({
            'chunks': 0,
            'documents': [],
            'unique_tags': 0,
            'bm25_index_size': 0,
            'knowledge_graph_nodes': 0,
            'knowledge_graph_edges': 0,
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
