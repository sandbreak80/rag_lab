"""
Knowledge Graph: Build and traverse document relationships

Supports multiple construction algorithms:
- wikilinks: Explicit [[Document Name]] connections (fast, accurate)
- semantic: Embedding similarity connections (slow, implicit)
- entity: Named entity co-occurrence (medium, entities)
- hybrid: Combines all methods (slowest, most comprehensive)

Benefits:
- +2% recall on multi-hop queries
- Relationship discovery
- Context expansion
- Algorithm comparison for education
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict

import networkx as nx
import chromadb
from chromadb.config import Settings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import config

# KG Algorithm configurations
KG_ALGORITHMS = {
    "wikilinks": {
        "name": "Wikilink-based",
        "speed": "Fast (< 1s)",
        "accuracy": "High (explicit connections)",
        "cost": "Low (no embeddings)",
        "description": "Uses [[wikilinks]], tags, and folder hierarchy for explicit connections",
        "best_for": "Documents with explicit cross-references"
    },
    "semantic": {
        "name": "Semantic Similarity",
        "speed": "Slow (10-30s)",
        "accuracy": "High (implicit connections)",
        "cost": "High (requires embeddings)",
        "description": "Connects documents with similar embeddings (cosine > 0.7)",
        "best_for": "Discovering implicit topical relationships"
    },
    "entity": {
        "name": "Entity Co-occurrence",
        "speed": "Medium (5-15s)",
        "accuracy": "Medium (entity-based)",
        "cost": "Medium (simple NER)",
        "description": "Connects documents mentioning the same entities (people, orgs, places)",
        "best_for": "Tracking entities across documents"
    },
    "hybrid": {
        "name": "Hybrid (All Methods)",
        "speed": "Very Slow (30-60s)",
        "accuracy": "Highest (comprehensive)",
        "cost": "Highest (all methods)",
        "description": "Combines wikilinks, semantic similarity, and entity extraction",
        "best_for": "Maximum quality, research use cases"
    }
}


class KnowledgeGraph:
    """Lightweight knowledge graph from document relationships"""

    def __init__(self, graph_path: Path = None):
        """
        Initialize knowledge graph

        Args:
            graph_path: Path to saved graph (default: indices/knowledge_graph.pkl)
        """
        self.graph_path = graph_path or (config.INDICES_PATH / "knowledge_graph.pkl")
        self.graph = nx.DiGraph()

        # Load graph if exists
        if self.graph_path.exists():
            self._load_graph()
            print(f"✅ Loaded knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        else:
            print(f"⚠️  Knowledge graph not found at {self.graph_path}")
            print(f"   Run: python src/knowledge_graph.py --build")

    def _load_graph(self):
        """Load graph from disk"""
        with open(self.graph_path, 'rb') as f:
            data = pickle.load(f)
            self.graph = data['graph']

    def _save_graph(self):
        """Save graph to disk"""
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.graph_path, 'wb') as f:
            pickle.dump({'graph': self.graph}, f)
        print(f"💾 Saved knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def load(self, path: Path):
        """Public method to load graph from custom path"""
        self.graph_path = path
        self._load_graph()

    def save(self, path: Path = None):
        """Public method to save graph to custom path"""
        if path:
            self.graph_path = path
        self._save_graph()

    def build_graph(self, algorithm: str = "wikilinks"):
        """
        Build knowledge graph from ChromaDB collection

        Args:
            algorithm: Construction method ("wikilinks", "semantic", "entity", "hybrid")
        """
        if algorithm not in KG_ALGORITHMS:
            print(f"❌ Unknown algorithm: {algorithm}. Using 'wikilinks'.")
            algorithm = "wikilinks"

        print(f"\n🔨 Building Knowledge Graph with '{KG_ALGORITHMS[algorithm]['name']}' algorithm...")
        print(f"   Speed: {KG_ALGORITHMS[algorithm]['speed']}")
        print(f"   Best for: {KG_ALGORITHMS[algorithm]['best_for']}")

        # Initialize ChromaDB
        client = chromadb.PersistentClient(
            path=str(config.CHROMA_DB_PATH),
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            collection = client.get_collection(config.COLLECTION_NAME)
        except Exception as e:
            print(f"❌ Collection not found: {e}")
            return

        print(f"📄 Found {collection.count()} documents")

        # Get all documents with embeddings if needed
        include = ['metadatas']
        if algorithm in ['semantic', 'hybrid']:
            include.append('embeddings')

        all_docs = collection.get(include=include)

        if not all_docs['metadatas']:
            print("❌ No documents found")
            return

        # Build base graph structure (always needed)
        self._build_base_structure(all_docs['metadatas'])

        # Add algorithm-specific connections
        if algorithm == "wikilinks":
            self._add_wikilink_connections(all_docs['metadatas'])
        elif algorithm == "semantic":
            self._add_semantic_connections(all_docs['metadatas'], all_docs.get('embeddings', []))
        elif algorithm == "entity":
            self._add_entity_connections(all_docs['metadatas'])
        elif algorithm == "hybrid":
            self._add_wikilink_connections(all_docs['metadatas'])
            self._add_semantic_connections(all_docs['metadatas'], all_docs.get('embeddings', []))
            self._add_entity_connections(all_docs['metadatas'])

        # Save graph
        self._save_graph()

        print("✅ Knowledge graph built successfully!")
        self._print_stats()

    def _build_base_structure(self, metadatas: List[Dict]):
        """Build base document, folder, and tag nodes"""
        print("🔗 Building base structure...")

        files_by_name = {}
        folders = set()

        # Step 1: Add document nodes
        for metadata in metadatas:
            file_path = metadata.get('file_path', '')
            file_name = metadata.get('file_name', '')
            title = metadata.get('title', file_name)

            if file_name and file_name not in self.graph:
                self.graph.add_node(
                    file_name,
                    type='document',
                    title=title,
                    file_path=file_path
                )
                files_by_name[file_name] = file_path

            # Extract folder
            if '/' in file_path:
                folder = '/'.join(file_path.split('/')[:-1])
                folders.add(folder)

        print(f"  Added {self.graph.number_of_nodes()} document nodes")

        # Step 2: Add folder nodes
        for folder in folders:
            if folder and folder not in self.graph:
                self.graph.add_node(
                    folder,
                    type='folder',
                    title=folder.split('/')[-1]
                )

        print(f"  Added {len(folders)} folder nodes")

        # Step 3: Add folder-document relationships
        for metadata in metadatas:
            file_path = metadata.get('file_path', '')
            file_name = metadata.get('file_name', '')

            if '/' in file_path:
                folder = '/'.join(file_path.split('/')[:-1])
                if folder in self.graph and file_name in self.graph:
                    self.graph.add_edge(folder, file_name, relation='contains')

        # Step 4: Add tag nodes and connections
        tag_groups = defaultdict(list)
        for metadata in metadatas:
            file_name = metadata.get('file_name', '')
            tags_str = metadata.get('tags', '[]')

            try:
                tags = json.loads(tags_str) if isinstance(tags_str, str) else tags_str
            except:
                tags = []

            for tag in tags:
                tag_groups[tag].append(file_name)

        tag_edge_count = 0
        for tag, files in tag_groups.items():
            if len(files) > 1:
                tag_node = f"tag:{tag}"
                if tag_node not in self.graph:
                    self.graph.add_node(tag_node, type='tag', title=tag)

                for file_name in files:
                    if file_name in self.graph:
                        self.graph.add_edge(file_name, tag_node, relation='has_tag')
                        tag_edge_count += 1

        print(f"  Added {len(tag_groups)} tag nodes, {tag_edge_count} tag edges")

        return files_by_name

    def _add_wikilink_connections(self, metadatas: List[Dict]):
        """Add wikilink-based connections"""
        print("🔗 Adding wikilink connections...")

        files_by_name = {m.get('file_name'): m.get('file_path') for m in metadatas if m.get('file_name')}

        wikilink_count = 0
        for metadata in metadatas:
            file_name = metadata.get('file_name', '')
            wikilinks_str = metadata.get('wikilinks', '[]')

            try:
                wikilinks = json.loads(wikilinks_str) if isinstance(wikilinks_str, str) else wikilinks_str
            except:
                wikilinks = []

            for link in wikilinks:
                target_file = None
                if f"{link}.md" in files_by_name:
                    target_file = f"{link}.md"
                elif link in files_by_name:
                    target_file = link

                if target_file and target_file in self.graph:
                    self.graph.add_edge(file_name, target_file, relation='links_to')
                    wikilink_count += 1

        print(f"  Added {wikilink_count} wikilink edges")

    def _add_semantic_connections(self, metadatas: List[Dict], embeddings: List[List[float]]):
        """Add semantic similarity connections based on embeddings"""
        print("🔗 Adding semantic similarity connections...")

        if not embeddings or len(embeddings) == 0:
            print("  ⚠️  No embeddings available")
            return

        # Group embeddings by document
        doc_embeddings = {}
        for i, metadata in enumerate(metadatas):
            file_name = metadata.get('file_name', '')
            if file_name and i < len(embeddings):
                if file_name not in doc_embeddings:
                    doc_embeddings[file_name] = []
                doc_embeddings[file_name].append(embeddings[i])

        # Average embeddings per document
        doc_avg_embeddings = {}
        for file_name, emb_list in doc_embeddings.items():
            doc_avg_embeddings[file_name] = np.mean(emb_list, axis=0)

        # Calculate similarity matrix
        file_names = list(doc_avg_embeddings.keys())
        embedding_matrix = np.array([doc_avg_embeddings[fn] for fn in file_names])

        similarity_matrix = cosine_similarity(embedding_matrix)

        # Add edges for high similarity (>0.7 threshold)
        semantic_count = 0
        for i, file_a in enumerate(file_names):
            for j, file_b in enumerate(file_names):
                if i < j and similarity_matrix[i][j] > 0.7:
                    self.graph.add_edge(file_a, file_b,
                                      relation='similar_to',
                                      similarity=float(similarity_matrix[i][j]))
                    semantic_count += 1

        print(f"  Added {semantic_count} semantic similarity edges")

    def _add_entity_connections(self, metadatas: List[Dict]):
        """Add entity co-occurrence connections"""
        print("🔗 Adding entity co-occurrence connections...")

        # Simple entity extraction (capitalized words that appear multiple times)
        entity_docs = defaultdict(set)

        for metadata in metadatas:
            file_name = metadata.get('file_name', '')
            content = metadata.get('content', '')

            # Extract potential entities (sequences of capitalized words)
            import re
            entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)

            # Filter entities that appear at least 2 times
            entity_counts = defaultdict(int)
            for entity in entities:
                if len(entity) > 3:  # Ignore short words
                    entity_counts[entity] += 1

            for entity, count in entity_counts.items():
                if count >= 2:  # Entity appears multiple times
                    entity_docs[entity].add(file_name)

        # Add entity nodes and connections
        entity_count = 0
        entity_edge_count = 0

        for entity, docs in entity_docs.items():
            if len(docs) > 1:  # Entity appears in multiple documents
                entity_node = f"entity:{entity}"
                if entity_node not in self.graph:
                    self.graph.add_node(entity_node, type='entity', title=entity)
                    entity_count += 1

                for doc in docs:
                    if doc in self.graph:
                        self.graph.add_edge(doc, entity_node, relation='mentions')
                        entity_edge_count += 1

        print(f"  Added {entity_count} entity nodes, {entity_edge_count} entity edges")

    def find_related(self, file_name: str, max_hops: int = 2, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find documents related to a given document via graph traversal

        Args:
            file_name: Source document
            max_hops: Maximum traversal distance
            limit: Max results

        Returns:
            List of related documents with relationship info
        """
        if file_name not in self.graph:
            return []

        related = []
        visited = {file_name}

        # BFS traversal
        queue = [(file_name, 0, [])]  # (node, depth, path)

        while queue and len(related) < limit:
            current, depth, path = queue.pop(0)

            if depth >= max_hops:
                continue

            # Get neighbors
            for neighbor in self.graph.neighbors(current):
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                node_data = self.graph.nodes[neighbor]

                # Only include document nodes in results
                if node_data.get('type') == 'document':
                    edge_data = self.graph[current][neighbor]
                    related.append({
                        'file_name': neighbor,
                        'title': node_data.get('title', neighbor),
                        'file_path': node_data.get('file_path', ''),
                        'hops': depth + 1,
                        'relationship': edge_data.get('relation', 'related'),
                        'path': path + [current, neighbor]
                    })

                # Continue traversal
                queue.append((neighbor, depth + 1, path + [current]))

        return related[:limit]

    def find_by_folder(self, folder: str) -> List[str]:
        """Find all documents in a folder"""
        if folder not in self.graph:
            return []

        documents = []
        for neighbor in self.graph.neighbors(folder):
            node_data = self.graph.nodes[neighbor]
            if node_data.get('type') == 'document':
                documents.append(neighbor)

        return documents

    def find_by_tag(self, tag: str) -> List[str]:
        """Find all documents with a specific tag"""
        tag_node = f"tag:{tag}"
        if tag_node not in self.graph:
            return []

        documents = []
        # Find documents pointing to this tag
        for node in self.graph.nodes():
            if self.graph.has_edge(node, tag_node):
                node_data = self.graph.nodes[node]
                if node_data.get('type') == 'document':
                    documents.append(node)

        return documents

    def get_document_context(self, file_name: str) -> Dict[str, Any]:
        """
        Get full context for a document

        Returns folder, tags, linked documents, etc.
        """
        if file_name not in self.graph:
            return {}

        context = {
            'file_name': file_name,
            'folders': [],
            'tags': [],
            'links_to': [],
            'linked_from': [],
            'related': []
        }

        # Find folders
        for node in self.graph.nodes():
            if self.graph.has_edge(node, file_name):
                node_data = self.graph.nodes[node]
                if node_data.get('type') == 'folder':
                    context['folders'].append(node)

        # Find tags
        for neighbor in self.graph.neighbors(file_name):
            node_data = self.graph.nodes[neighbor]
            if node_data.get('type') == 'tag':
                context['tags'].append(node_data.get('title', ''))

        # Find links
        for neighbor in self.graph.neighbors(file_name):
            node_data = self.graph.nodes[neighbor]
            edge_data = self.graph[file_name][neighbor]
            if node_data.get('type') == 'document':
                if edge_data.get('relation') == 'links_to':
                    context['links_to'].append(neighbor)

        # Find backlinks
        for node in self.graph.nodes():
            if self.graph.has_edge(node, file_name):
                node_data = self.graph.nodes[node]
                if node_data.get('type') == 'document':
                    edge_data = self.graph[node][file_name]
                    if edge_data.get('relation') == 'links_to':
                        context['linked_from'].append(node)

        # Find related (1-hop)
        context['related'] = self.find_related(file_name, max_hops=1, limit=5)

        return context

    def _print_stats(self):
        """Print graph statistics"""
        print("\n📊 Graph Statistics:")

        # Count by type
        type_counts = defaultdict(int)
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', 'unknown')
            type_counts[node_type] += 1

        for node_type, count in sorted(type_counts.items()):
            print(f"  {node_type}: {count}")

        # Count by relation
        relation_counts = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            relation = data.get('relation', 'unknown')
            relation_counts[relation] += 1

        print(f"\n  Relationships:")
        for relation, count in sorted(relation_counts.items()):
            print(f"    {relation}: {count}")


def build_graph():
    """Build knowledge graph from command line"""
    print("🚀 Building Knowledge Graph")
    kg = KnowledgeGraph()
    kg.build_graph()


def test_knowledge_graph():
    """Test knowledge graph"""
    print("🧪 Testing Knowledge Graph\n")

    kg = KnowledgeGraph()

    if kg.graph.number_of_nodes() == 0:
        print("❌ Knowledge graph is empty. Build it first:")
        print("   python src/knowledge_graph.py --build")
        return

    # Test 1: Find documents in Blue Belt folder
    print("📁 Test 1: Blue Belt Folder")
    blue_belt_folder = "Generative Artificial Intelligence - Blue Belt"
    docs = kg.find_by_folder(blue_belt_folder)
    print(f"Found {len(docs)} documents in Blue Belt folder")
    if docs:
        print(f"  Examples: {docs[:3]}")

    # Test 2: Find related documents
    print("\n🔗 Test 2: Related Documents")
    if docs:
        test_doc = docs[0]
        related = kg.find_related(test_doc, max_hops=2, limit=5)
        print(f"Documents related to '{test_doc}':")
        for r in related:
            print(f"  - {r['title']} ({r['hops']} hops, {r['relationship']})")

    # Test 3: Find by tag
    print("\n🏷️  Test 3: Documents by Tag")
    tags = ['ai', 'prompt', 'training']
    for tag in tags:
        docs_with_tag = kg.find_by_tag(tag)
        if docs_with_tag:
            print(f"Tag '{tag}': {len(docs_with_tag)} documents")

    # Test 4: Get document context
    print("\n📋 Test 4: Document Context")
    if docs:
        test_doc = docs[0]
        context = kg.get_document_context(test_doc)
        print(f"Context for '{test_doc}':")
        print(f"  Folders: {context['folders']}")
        print(f"  Tags: {context['tags']}")
        print(f"  Links to: {len(context['links_to'])} documents")
        print(f"  Linked from: {len(context['linked_from'])} documents")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--build':
        build_graph()
    else:
        test_knowledge_graph()

