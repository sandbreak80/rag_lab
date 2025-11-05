"""
Knowledge Graph Service - Document relationship management
Manages document relationships via wikilinks and tags
"""
from flask import Flask, request, jsonify
import sys
import os
import pickle
import requests
from pathlib import Path

# Add common and src to path
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/workspace/src')

from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

try:
    from knowledge_graph import KnowledgeGraph, KG_ALGORITHMS
    KG_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Knowledge graph import failed: {e}")
    KG_AVAILABLE = False

app = Flask(__name__)

# Get service port from environment
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8007))

# Initialize metrics
metrics = ServiceMetrics("graph-service")

# Initialize health checks
health = HealthCheck("graph-service")

# Knowledge graph (loaded on startup)
kg = None
kg_path = Path("/indices/knowledge_graph.pkl")

def load_knowledge_graph():
    """Load knowledge graph from disk"""
    global kg

    if not KG_AVAILABLE:
        print("⚠️  Knowledge graph module not available")
        return False

    if kg_path.exists():
        try:
            kg = KnowledgeGraph()
            kg.load(kg_path)
            print(f"✅ Loaded knowledge graph: {len(kg.graph.nodes())} nodes")
            return True
        except Exception as e:
            print(f"❌ Failed to load knowledge graph: {e}")
            return False
    else:
        print(f"⚠️  Knowledge graph not found at {kg_path}")
        # Create empty graph
        if KG_AVAILABLE:
            kg = KnowledgeGraph()
            print("✅ Created empty knowledge graph")
            return True
        return False

# Health checks
health.add_check("kg_loaded", lambda: kg is not None)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    stats = metrics.get_stats()
    if kg and hasattr(kg, 'graph'):
        stats['graph_nodes'] = len(kg.graph.nodes())
        stats['graph_edges'] = len(kg.graph.edges())
    return jsonify(stats)

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get graph statistics"""
    try:
        if not kg:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        stats = {
            'nodes': len(kg.graph.nodes()),
            'edges': len(kg.graph.edges()),
            'node_types': {}
        }

        # Count node types
        for node, data in kg.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/nodes', methods=['GET'])
def list_nodes():
    """List all nodes (optionally filtered by type)"""
    try:
        if not kg:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        node_type = request.args.get('type', None)
        limit = request.args.get('limit', 100, type=int)

        nodes = []
        for node, data in kg.graph.nodes(data=True):
            if node_type is None or data.get('type') == node_type:
                nodes.append({
                    'id': node,
                    'type': data.get('type', 'unknown'),
                    'attributes': {k: v for k, v in data.items() if k != 'type'}
                })
                if len(nodes) >= limit:
                    break

        return jsonify({
            'nodes': nodes,
            'count': len(nodes),
            'total': len(kg.graph.nodes())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/related/<doc_id>', methods=['GET'])
@timed(metrics, 'find_related')
def find_related(doc_id):
    """Find related documents"""
    try:
        if not kg:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        limit = request.args.get('limit', 10, type=int)
        max_hops = request.args.get('max_hops', 2, type=int)

        metrics.increment('find_related_requests')

        # Find related nodes (correct parameter name is 'limit', not 'max_results')
        related = kg.find_related(doc_id, max_hops=max_hops, limit=limit)

        metrics.increment('find_related_success')

        return jsonify({
            'doc_id': doc_id,
            'related': related,
            'count': len(related)
        })
    except Exception as e:
        metrics.increment('find_related_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/add', methods=['POST'])
@timed(metrics, 'add_node')
def add_node():
    """Add a node to the graph"""
    try:
        if not kg:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        data = request.json
        node_id = data.get('node_id', '')
        node_type = data.get('node_type', 'document')
        attributes = data.get('attributes', {})

        if not node_id:
            return jsonify({'error': 'node_id required'}), 400

        kg.graph.add_node(node_id, type=node_type, **attributes)

        metrics.increment('nodes_added')

        return jsonify({
            'status': 'success',
            'node_id': node_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_edge', methods=['POST'])
@timed(metrics, 'add_edge')
def add_edge():
    """Add an edge to the graph"""
    try:
        if not kg:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        data = request.json
        source = data.get('source', '')
        target = data.get('target', '')
        edge_type = data.get('edge_type', 'links_to')

        if not source or not target:
            return jsonify({'error': 'source and target required'}), 400

        kg.graph.add_edge(source, target, type=edge_type)

        metrics.increment('edges_added')

        return jsonify({
            'status': 'success',
            'source': source,
            'target': target
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_document', methods=['POST'])
@timed(metrics, 'add_document')
def add_document():
    """Add a document with entities to the knowledge graph"""
    try:
        if not kg:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        data = request.json
        doc_id = data.get('document_id', '')
        doc_title = data.get('document_title', doc_id)
        tags = data.get('tags', [])
        wikilinks = data.get('wikilinks', [])
        entities = data.get('entities', {})

        if not doc_id:
            return jsonify({'error': 'document_id required'}), 400

        nodes_created = 0
        edges_created = 0

        # Add document node
        if doc_id not in kg.graph:
            kg.graph.add_node(doc_id, type='document', title=doc_title)
            nodes_created += 1
            metrics.increment('nodes_added')

        # Add tag nodes and edges
        for tag in tags:
            tag_node = f"tag:{tag}"
            if tag_node not in kg.graph:
                kg.graph.add_node(tag_node, type='tag', title=tag)
                nodes_created += 1
                metrics.increment('nodes_added')

            kg.graph.add_edge(doc_id, tag_node, type='has_tag')
            edges_created += 1
            metrics.increment('edges_added')

        # Add wikilink edges (if target exists)
        for link in wikilinks:
            target_file = f"{link}.md" if not link.endswith('.md') else link
            if target_file in kg.graph:
                kg.graph.add_edge(doc_id, target_file, type='links_to')
                edges_created += 1
                metrics.increment('edges_added')

        # Add entity nodes and edges
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                entity_node = f"{entity_type}:{entity}"
                if entity_node not in kg.graph:
                    kg.graph.add_node(entity_node, type=entity_type, title=entity)
                    nodes_created += 1
                    metrics.increment('nodes_added')

                kg.graph.add_edge(doc_id, entity_node, type='mentions')
                edges_created += 1
                metrics.increment('edges_added')

        # Save graph after updates
        kg.save(kg_path)
        metrics.increment('saves')

        return jsonify({
            'success': True,
            'document_id': doc_id,
            'nodes_created': nodes_created,
            'edges_created': edges_created
        })

    except Exception as e:
        metrics.increment('add_document_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save_graph():
    """Save knowledge graph to disk"""
    try:
        if not kg:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        kg.save(kg_path)

        metrics.increment('saves')

        return jsonify({'status': 'success', 'path': str(kg_path)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/build', methods=['POST'])
@timed(metrics, 'build_graph')
def build_graph():
    """Build knowledge graph from vector database"""
    global kg

    try:
        # Get algorithm from request (default to wikilinks)
        data = request.get_json() or {}
        algorithm = data.get('algorithm', 'wikilinks')

        print(f"🔨 Building knowledge graph with algorithm: {algorithm}...")

        if not KG_AVAILABLE:
            return jsonify({'error': 'Knowledge graph module not available'}), 503

        # Get vector DB URL from environment
        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')

        # Determine if we need embeddings for this algorithm
        need_embeddings = algorithm in ['semantic', 'hybrid']

        # Fetch all documents from vector-db service
        print(f"📥 Fetching documents from {vector_db_url}/get_all...")
        print(f"   Algorithm: {algorithm}, Requesting embeddings: {need_embeddings}")
        response = requests.post(
            f"{vector_db_url}/get_all",
            json={'include_embeddings': need_embeddings},
            timeout=180
        )
        response.raise_for_status()
        data = response.json()

        metadatas = data.get('metadatas', [])
        documents = data.get('documents', [])
        embeddings = data.get('embeddings', []) if need_embeddings else None

        print(f"📚 Fetched {len(metadatas)} documents")
        if need_embeddings:
            print(f"   Embeddings: {len(embeddings) if embeddings else 0}")

        # Add document content to metadatas for entity extraction
        for i, metadata in enumerate(metadatas):
            if i < len(documents):
                metadata['content'] = documents[i]

        if not metadatas:
            return jsonify({
                'success': False,
                'message': 'No documents in vector database'
            }), 400

        # Create new graph
        kg = KnowledgeGraph()

        # Build using the selected algorithm with provided data
        kg.build_graph(algorithm=algorithm, metadatas=metadatas, embeddings=embeddings)

        metrics.increment('builds')

        # Get stats
        stats = {
            'nodes': kg.graph.number_of_nodes(),
            'edges': kg.graph.number_of_edges(),
        }

        # Count node types
        doc_nodes = [n for n in kg.graph.nodes() if kg.graph.nodes[n].get('type') == 'document']
        tag_nodes = [n for n in kg.graph.nodes() if kg.graph.nodes[n].get('type') == 'tag']
        entity_nodes = [n for n in kg.graph.nodes() if kg.graph.nodes[n].get('type') == 'entity']
        folder_nodes = [n for n in kg.graph.nodes() if kg.graph.nodes[n].get('type') == 'folder']

        stats.update({
            'documents': len(doc_nodes),
            'tags': len(tag_nodes),
            'entities': len(entity_nodes),
            'folders': len(folder_nodes),
            'algorithm': algorithm
        })

        print("✅ Knowledge graph built successfully!")
        print(f"   Nodes: {stats['nodes']}, Edges: {stats['edges']}")

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        metrics.increment('build_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_knowledge_graph():
    """Reset the knowledge graph to empty state"""
    try:
        global kg

        print("🔄 Resetting knowledge graph...")

        # Create new empty knowledge graph
        if KG_AVAILABLE:
            kg = KnowledgeGraph()

            # Save empty graph to disk
            kg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(kg_path, 'wb') as f:
                pickle.dump(kg, f)

            print("✅ Knowledge graph reset successfully")

            metrics.increment('resets')

            return jsonify({
                'success': True,
                'message': 'Knowledge graph reset',
                'stats': {
                    'nodes': 0,
                    'edges': 0
                }
            })
        else:
            return jsonify({'error': 'Knowledge graph not available'}), 503

    except Exception as e:
        metrics.increment('errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/algorithms', methods=['GET'])
def get_algorithms():
    """Get available KG construction algorithms"""
    try:
        if not KG_AVAILABLE:
            return jsonify({'error': 'Knowledge graph not available'}), 503

        return jsonify({
            'algorithms': KG_ALGORITHMS,
            'default': 'wikilinks'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    print("🚀 Knowledge Graph Service starting...")

    # Load knowledge graph
    load_knowledge_graph()

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

