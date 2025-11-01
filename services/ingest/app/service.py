"""
Ingest Service - Document upload and processing orchestration
Handles file uploads and coordinates parsing, embedding, and indexing
"""
from flask import Flask, request, jsonify
import requests
import sys
import os
from pathlib import Path
import tempfile
import json
from typing import Dict, Any, List
from werkzeug.utils import secure_filename

# Add common and parent src to path - COMMON FIRST to avoid conflicts!
sys.path.insert(0, '/workspace/services/common')
sys.path.insert(1, '/workspace/src')

# Import from common - use explicit imports to avoid module caching issues
from config import (
    MAX_UPLOAD_SIZE, UPLOAD_FOLDER, SUPPORTED_EXTENSIONS,
    DOCLING_SERVICE_URL, EMBEDDING_SERVICE_URL, VECTOR_DB_URL,
    KNOWLEDGE_GRAPH_URL,
    AGENTIC_CHUNKING_ENABLED, AGENTIC_TARGET_CHUNK_SIZE, AGENTIC_MAX_CHUNK_SIZE,
    CHUNK_SIZE, CHUNK_OVERLAP, SERVICE_PORT
)
from metrics import ServiceMetrics, timed
from health import HealthCheck

# Import parsers from existing code
from parser import MarkdownParser
try:
    from agentic_chunker import AgenticChunker
    AGENTIC_AVAILABLE = True
except:
    AGENTIC_AVAILABLE = False

try:
    from entity_extractor import EntityExtractor
    ENTITY_EXTRACTION_AVAILABLE = True
except:
    ENTITY_EXTRACTION_AVAILABLE = False

app = Flask(__name__)

# Configure upload using imported config
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)

# Initialize metrics
metrics = ServiceMetrics("ingest-service")

# Initialize health checks
health = HealthCheck("ingest-service")

# Initialize parsers
markdown_parser = MarkdownParser()
if AGENTIC_AVAILABLE and AGENTIC_CHUNKING_ENABLED:
    agentic_chunker = AgenticChunker(
        target_chunk_size=AGENTIC_TARGET_CHUNK_SIZE,
        max_chunk_size=AGENTIC_MAX_CHUNK_SIZE
    )
    print("🤖 Agentic chunking enabled")
else:
    agentic_chunker = None
    print("📏 Simple chunking enabled")

# Initialize entity extractor
if ENTITY_EXTRACTION_AVAILABLE:
    entity_extractor = EntityExtractor()
    print("🔍 Entity extraction enabled")
else:
    entity_extractor = None
    print("❌ Entity extraction disabled")

# Ensure upload directory exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def check_services():
    """Check if required services are available"""
    services = {
        'docling': DOCLING_SERVICE_URL,
        'embedding': EMBEDDING_SERVICE_URL,
        'vector_db': VECTOR_DB_URL
    }

    for name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code != 200:
                return False
        except:
            return False
    return True

# Health checks
health.add_check("services_available", check_services)
health.add_check("upload_folder_writable", lambda: UPLOAD_FOLDER.is_dir() and os.access(UPLOAD_FOLDER, os.W_OK))

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify(health.get_health())

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Metrics endpoint"""
    return jsonify(metrics.get_stats())

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def parse_markdown(file_path: Path) -> Dict[str, Any]:
    """Parse markdown file"""
    try:
        parsed = markdown_parser.parse_file(file_path)
        return {
            'success': True,
            'content': parsed['content'],
            'metadata': {
                'title': parsed['title'],
                'file_name': parsed['file_name'],
                'tags': parsed.get('tags', []),
                'wikilinks': parsed.get('wikilinks', [])
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_text(file_path: Path) -> Dict[str, Any]:
    """Parse text file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        return {
            'success': True,
            'content': content,
            'metadata': {
                'title': file_path.stem,
                'file_name': file_path.name,
                'tags': [],
                'wikilinks': []
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_pdf(file_path: Path) -> Dict[str, Any]:
    """Parse PDF via Docling service"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/pdf')}
            response = requests.post(
                f"{DOCLING_SERVICE_URL}/parse",
                files=files,
                timeout=600  # 10 minutes for large PDFs
            )
            response.raise_for_status()

        result = response.json()
        if result.get('success'):
            return {
                'success': True,
                'content': result['markdown'],
                'metadata': {
                    'title': result['metadata'].get('title', file_path.stem),
                    'file_name': file_path.name,
                    'num_pages': result['metadata'].get('num_pages', 0),
                    'parser': result['metadata'].get('parser', 'unknown'),
                    'tags': [],
                    'wikilinks': []
                }
            }
        else:
            return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

def chunk_content(content: str, metadata: Dict) -> List[Dict]:
    """Chunk content using agentic or simple chunking"""
    chunks = []

    if agentic_chunker:
        # Agentic chunking
        chunk_objects = agentic_chunker.chunk_markdown(content, metadata)
        for i, chunk_obj in enumerate(chunk_objects):
            chunks.append({
                'text': chunk_obj.text,
                'index': i,
                'method': 'agentic'
            })
    else:
        # Simple chunking
        simple_chunks = markdown_parser.chunk_content(
            content,
            chunk_size=CHUNK_SIZE,
            overlap=CHUNK_OVERLAP
        )
        for i, text in enumerate(simple_chunks):
            chunks.append({
                'text': text,
                'index': i,
                'method': 'simple'
            })

    return chunks

def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    """Generate embeddings for chunks"""
    texts = [chunk['text'] for chunk in chunks]

    # Batch embed
    response = requests.post(
        f"{EMBEDDING_SERVICE_URL}/embed/batch",
        json={'texts': texts},
        timeout=120
    )
    response.raise_for_status()

    result = response.json()
    embeddings = result['embeddings']

    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk['embedding'] = embedding

    return chunks

def store_in_vector_db(chunks: List[Dict], metadata: Dict) -> Dict:
    """Store chunks in vector database"""
    ids = [f"{metadata['file_name']}_{chunk['index']}" for chunk in chunks]
    documents = [chunk['text'] for chunk in chunks]
    embeddings = [chunk['embedding'] for chunk in chunks]
    metadatas = [
        {
            'file_name': metadata['file_name'],
            'title': metadata['title'],
            'chunk_index': chunk['index'],
            'chunking_method': chunk['method'],
            'tags': json.dumps(metadata.get('tags', [])),
            'wikilinks': json.dumps(metadata.get('wikilinks', []))
        }
        for chunk in chunks
    ]

    response = requests.post(
        f"{VECTOR_DB_URL}/add",
        json={
            'ids': ids,
            'documents': documents,
            'embeddings': embeddings,
            'metadatas': metadatas
        },
        timeout=60
    )
    response.raise_for_status()

    return response.json()

def add_to_knowledge_graph(metadata: Dict) -> Dict:
    """Add document and entities to knowledge graph"""
    try:
        # Prepare document node
        doc_id = metadata.get('file_name', 'unknown')
        doc_title = metadata.get('title', doc_id)
        
        # Extract entities if present
        entities = metadata.get('entities', {})
        
        # Build request payload
        payload = {
            'document_id': doc_id,
            'document_title': doc_title,
            'tags': metadata.get('tags', []),
            'wikilinks': metadata.get('wikilinks', []),
            'entities': entities
        }
        
        # Send to knowledge graph service
        response = requests.post(
            f"{KNOWLEDGE_GRAPH_URL}/add_document",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"   Added to knowledge graph: {result.get('nodes_created', 0)} nodes, {result.get('edges_created', 0)} edges")
        return result
        
    except Exception as e:
        print(f"   Warning: Failed to add to knowledge graph: {e}")
        # Don't fail the whole upload if KG fails
        return {'success': False, 'error': str(e)}

@app.route('/upload', methods=['POST'])
@timed(metrics, 'upload_process')
def upload_file():
    """
    Upload and process a file

    Form data:
    - file: File to upload (PDF, MD, TXT)

    Returns:
    {
        "success": true,
        "file_name": "document.pdf",
        "chunks_created": 15,
        "processing_time_ms": 1234
    }
    """
    try:
        # Validate file
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not supported. Allowed: {", ".join(SUPPORTED_EXTENSIONS)}'
            }), 400

        metrics.increment('upload_requests')

        # Save file
        filename = secure_filename(file.filename)
        file_path = UPLOAD_FOLDER / filename
        file.save(str(file_path))

        metrics.increment('files_uploaded')
        metrics.set_gauge('last_upload_size_mb', file_path.stat().st_size / (1024 * 1024))

        # Step 1: Parse document
        metrics.increment('parse_started')
        if filename.endswith('.pdf'):
            parse_result = parse_pdf(file_path)
            metrics.increment('pdf_parsed')
        elif filename.endswith('.md') or filename.endswith('.markdown'):
            parse_result = parse_markdown(file_path)
            metrics.increment('markdown_parsed')
        else:  # .txt
            parse_result = parse_text(file_path)
            metrics.increment('text_parsed')

        if not parse_result['success']:
            metrics.increment('parse_errors')
            return jsonify({
                'error': f"Parse failed: {parse_result.get('error', 'Unknown error')}"
            }), 500

        content = parse_result['content']
        metadata = parse_result['metadata']

        # Extract entities if enabled
        if entity_extractor:
            title = metadata.get('title', filename)
            entities = entity_extractor.extract_entities(content, title)
            if entities:
                # Store entities in metadata (dict format)
                metadata['entities'] = entities
                # Count total entities
                total_entities = sum(len(v) for v in entities.values())
                metrics.increment('entities_extracted', total_entities)
                print(f"   Extracted {total_entities} entities across {len(entities)} categories")

        # Step 2: Chunk content
        metrics.increment('chunking_started')
        chunks = chunk_content(content, metadata)
        metrics.increment('chunks_created', len(chunks))

        # Step 3: Generate embeddings
        metrics.increment('embedding_started')
        chunks = embed_chunks(chunks)
        metrics.increment('embeddings_generated', len(chunks))

        # Step 4: Store in vector DB
        metrics.increment('storage_started')
        store_result = store_in_vector_db(chunks, metadata)
        metrics.increment('storage_completed')

        # Step 5: Add to knowledge graph
        if metadata.get('entities') or metadata.get('tags') or metadata.get('wikilinks'):
            kg_result = add_to_knowledge_graph(metadata)
            if kg_result.get('success', False):
                metrics.increment('knowledge_graph_updates')

        # Cleanup uploaded file (optional, keep for debugging)
        # file_path.unlink()

        metrics.increment('upload_success')

        return jsonify({
            'success': True,
            'file_name': filename,
            'chunks_created': len(chunks),
            'metadata': metadata
        })

    except Exception as e:
        metrics.increment('upload_errors')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/upload/url', methods=['POST'])
@timed(metrics, 'upload_url_process')
def upload_from_url():
    """
    Upload file from URL

    Body:
    {
        "url": "https://example.com/document.pdf"
    }
    """
    try:
        data = request.json
        url = data.get('url', '')

        if not url:
            return jsonify({'error': 'url required'}), 400

        metrics.increment('url_upload_requests')

        # Download file
        response = requests.get(url, timeout=120)
        response.raise_for_status()

        # Determine filename from URL or Content-Disposition
        filename = url.split('/')[-1]
        if not allowed_file(filename):
            return jsonify({'error': f'File type not supported'}), 400

        # Save to temp file
        filename = secure_filename(filename)
        file_path = UPLOAD_FOLDER / filename
        file_path.write_bytes(response.content)

        # Process like normal upload
        # (reuse upload logic - could refactor into shared function)
        if filename.endswith('.pdf'):
            parse_result = parse_pdf(file_path)
        elif filename.endswith('.md') or filename.endswith('.markdown'):
            parse_result = parse_markdown(file_path)
        else:
            parse_result = parse_text(file_path)

        if not parse_result['success']:
            return jsonify({'error': f"Parse failed: {parse_result.get('error')}"}), 500

        chunks = chunk_content(parse_result['content'], parse_result['metadata'])
        chunks = embed_chunks(chunks)
        store_in_vector_db(chunks, parse_result['metadata'])

        metrics.increment('url_upload_success')

        return jsonify({
            'success': True,
            'file_name': filename,
            'chunks_created': len(chunks),
            'source': 'url'
        })

    except Exception as e:
        metrics.increment('url_upload_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/list', methods=['GET'])
def list_files():
    """List uploaded files"""
    try:
        files = []
        for file_path in UPLOAD_FOLDER.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    'name': file_path.name,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': stat.st_mtime
                })

        return jsonify({
            'files': files,
            'count': len(files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Ingest Service starting...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📊 Max file size: {MAX_UPLOAD_SIZE / (1024*1024):.0f}MB")
    print(f"📄 Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
    print(f"🤖 Agentic chunking: {AGENTIC_AVAILABLE and AGENTIC_CHUNKING_ENABLED}")

    # Start server
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

