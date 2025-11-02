"""
Knowledge Graph Service - Document relationship management
Manages document relationships via wikilinks and tags
"""
from flask import Flask, request, jsonify
import sys
import os
import pickle
from pathlib import Path

# Add common and src to path
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(0, '/workspace/src')

from config import *
from metrics import ServiceMetrics, timed
from health import HealthCheck

try:
    from knowledge_graph import KnowledgeGraph
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
        print("🔨 Building knowledge graph...")

        if not KG_AVAILABLE:
            return jsonify({'error': 'Knowledge graph module not available'}), 503

        # Get vector DB URL from environment
        vector_db_url = os.getenv('VECTOR_DB_URL', 'http://vector-db:8005')

        # Create new graph
        kg = KnowledgeGraph()

        # Build from vector database
        # Get all documents
        import requests
        response = requests.post(
            f"{vector_db_url}/get_all",
            json={},
            timeout=180
        )
        response.raise_for_status()
        data = response.json()

        documents = data.get('documents', [])
        metadatas = data.get('metadatas', [])

        if not metadatas:
            return jsonify({
                'success': False,
                'message': 'No metadata in vector database'
            }), 400

        print(f"📚 Processing {len(metadatas)} documents...")

        # Track files and relationships
        files_by_name = {}
        folders = set()
        tags_by_doc = {}

        # Step 1: Add document nodes
        for metadata in metadatas:
            file_name = metadata.get('file_name', '')
            if not file_name:
                continue

            if file_name not in files_by_name:
                file_path = metadata.get('file_path', '')
                title = metadata.get('title', file_name)

                # Add document node
                kg.graph.add_node(
                    file_name,
                    type='document',
                    title=title,
                    file_path=file_path
                )
                files_by_name[file_name] = file_path

                # Track folder
                if '/' in file_path:
                    folder = '/'.join(file_path.split('/')[:-1])
                    folders.add(folder)

                # Track tags
                tags_str = metadata.get('tags', '[]')
                try:
                    import json
                    tags = json.loads(tags_str) if isinstance(tags_str, str) else tags_str
                    if tags:
                        tags_by_doc[file_name] = tags
                except:
                    pass

        print(f"  Added {len(files_by_name)} document nodes")

        # Step 2: Add folder nodes
        for folder in folders:
            if folder and folder not in kg.graph:
                kg.graph.add_node(
                    folder,
                    type='folder',
                    title=folder.split('/')[-1]
                )

        print(f"  Added {len(folders)} folder nodes")

        # Step 3: Add folder-document edges
        edge_count = 0
        for metadata in metadatas:
            file_path = metadata.get('file_path', '')
            file_name = metadata.get('file_name', '')

            if file_name and '/' in file_path:
                folder = '/'.join(file_path.split('/')[:-1])
                if folder in kg.graph and file_name in kg.graph:
                    kg.graph.add_edge(folder, file_name, relation='contains')
                    edge_count += 1

        print(f"  Added {edge_count} folder containment edges")

        # Step 4: Add wikilink edges
        wikilink_count = 0
        for metadata in metadatas:
            file_name = metadata.get('file_name', '')
            wikilinks_str = metadata.get('wikilinks', '[]')

            try:
                import json
                wikilinks = json.loads(wikilinks_str) if isinstance(wikilinks_str, str) else wikilinks_str
            except:
                wikilinks = []

            for link in wikilinks:
                # Try to find target file
                target_file = None

                # Try exact match
                if f"{link}.md" in files_by_name:
                    target_file = f"{link}.md"
                elif link in files_by_name:
                    target_file = link

                if target_file and target_file in kg.graph and file_name in kg.graph:
                    kg.graph.add_edge(file_name, target_file, relation='links_to')
                    wikilink_count += 1

        print(f"  Added {wikilink_count} wikilink edges")

        # Step 5: Add tag nodes and edges
        tag_nodes = set()
        tag_edge_count = 0

        for file_name, tags in tags_by_doc.items():
            for tag in tags:
                tag_node = f"tag:{tag}"

                # Add tag node
                if tag_node not in kg.graph:
                    kg.graph.add_node(tag_node, type='tag', title=tag)
                    tag_nodes.add(tag_node)

                # Add edge
                if file_name in kg.graph:
                    kg.graph.add_edge(file_name, tag_node, relation='has_tag')
                    tag_edge_count += 1

        print(f"  Added {len(tag_nodes)} tag nodes, {tag_edge_count} tag edges")

        # Save graph
        kg.save(kg_path)

        metrics.increment('builds')

        stats = {
            'nodes': len(kg.graph.nodes()),
            'edges': len(kg.graph.edges()),
            'documents': len(files_by_name),
            'folders': len(folders),
            'tags': len(tag_nodes)
        }

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

if __name__ == '__main__':
    import os
    print("🚀 Knowledge Graph Service starting...")

    # Load knowledge graph
    load_knowledge_graph()

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

