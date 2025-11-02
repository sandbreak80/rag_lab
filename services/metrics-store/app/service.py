#!/usr/bin/env python3
"""
Metrics Storage Service - Persistent performance metrics for lab analysis
Stores query performance data in SQLite for historical analysis
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
import sys

# Add parent directory to path for common imports
sys.path.insert(0, '/workspace')
from services.common.config import *
from services.common.metrics import ServiceMetrics, timed

app = Flask(__name__)
CORS(app)

# Configuration
SERVICE_NAME = os.getenv('SERVICE_NAME', 'metrics-store')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8011))
DB_PATH = os.getenv('METRICS_DB_PATH', '/data/metrics/metrics.db')

# Ensure database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Metrics
metrics = ServiceMetrics(SERVICE_NAME)

# Database schema
SCHEMA = """
CREATE TABLE IF NOT EXISTS query_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    
    -- RAG Configuration
    model TEXT,
    temperature REAL,
    top_k INTEGER,
    use_query_expansion INTEGER,
    use_bm25 INTEGER,
    use_hybrid INTEGER,
    use_graph INTEGER,
    use_reranking INTEGER,
    use_web_search INTEGER,
    
    -- Performance Metrics
    total_latency_ms REAL,
    search_latency_ms REAL,
    llm_latency_ms REAL,
    embedding_latency_ms REAL,
    rerank_latency_ms REAL,
    web_search_latency_ms REAL,
    
    -- Quality Metrics (if available)
    precision REAL,
    recall REAL,
    f1_score REAL,
    
    -- Result Metrics
    chunks_returned INTEGER,
    tokens_used INTEGER,
    sources_count INTEGER,
    
    -- Additional Data (JSON)
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_timestamp ON query_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_model ON query_metrics(model);
CREATE INDEX IF NOT EXISTS idx_config ON query_metrics(use_query_expansion, use_bm25, use_hybrid, use_graph, use_reranking);
"""

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")

# Initialize on startup
init_db()

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    try:
        # Check database connectivity
        conn = get_db()
        cursor = conn.execute("SELECT COUNT(*) FROM query_metrics")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'service': SERVICE_NAME,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': {
                    'status': 'pass',
                    'healthy': True,
                    'total_records': count
                }
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': SERVICE_NAME,
            'error': str(e)
        }), 503

@app.route('/metrics', methods=['GET'])
def get_service_metrics():
    """Get service metrics"""
    return jsonify(metrics.get_stats())

@app.route('/store', methods=['POST'])
@timed(metrics, 'store_metric')
def store_metric():
    """
    Store a query metric
    
    Request body:
    {
        "query": "What is RAG?",
        "config": {
            "model": "llama3.2:3b",
            "temperature": 0.7,
            "top_k": 5,
            "use_query_expansion": true,
            ...
        },
        "performance": {
            "total_latency_ms": 1234,
            "search_latency_ms": 234,
            "llm_latency_ms": 1000,
            ...
        },
        "results": {
            "chunks_returned": 5,
            "tokens_used": 500,
            "sources_count": 3
        },
        "metadata": {}  // Optional additional data
    }
    """
    try:
        data = request.json
        
        query = data.get('query', '')
        config = data.get('config', {})
        performance = data.get('performance', {})
        results = data.get('results', {})
        metadata = data.get('metadata', {})
        
        conn = get_db()
        cursor = conn.execute("""
            INSERT INTO query_metrics (
                timestamp, query,
                model, temperature, top_k,
                use_query_expansion, use_bm25, use_hybrid, use_graph, use_reranking, use_web_search,
                total_latency_ms, search_latency_ms, llm_latency_ms, embedding_latency_ms, 
                rerank_latency_ms, web_search_latency_ms,
                chunks_returned, tokens_used, sources_count,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            query,
            config.get('model'),
            config.get('temperature'),
            config.get('top_k'),
            int(config.get('use_query_expansion', False)),
            int(config.get('use_bm25', False)),
            int(config.get('use_hybrid', False)),
            int(config.get('use_graph', False)),
            int(config.get('use_reranking', False)),
            int(config.get('use_web_search', False)),
            performance.get('total_latency_ms'),
            performance.get('search_latency_ms'),
            performance.get('llm_latency_ms'),
            performance.get('embedding_latency_ms'),
            performance.get('rerank_latency_ms'),
            performance.get('web_search_latency_ms'),
            results.get('chunks_returned'),
            results.get('tokens_used'),
            results.get('sources_count'),
            json.dumps(metadata)
        ))
        
        metric_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        metrics.increment('metrics_stored')
        
        return jsonify({
            'success': True,
            'metric_id': metric_id
        })
        
    except Exception as e:
        metrics.increment('store_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['POST'])
@timed(metrics, 'query_metrics')
def query_metrics():
    """
    Query stored metrics with filters
    
    Request body:
    {
        "filters": {
            "model": "llama3.2:3b",
            "use_hybrid": true,
            "start_date": "2025-11-01",
            "end_date": "2025-11-02"
        },
        "limit": 100,
        "offset": 0
    }
    """
    try:
        data = request.json or {}
        filters = data.get('filters', {})
        limit = data.get('limit', 100)
        offset = data.get('offset', 0)
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if 'model' in filters:
            where_clauses.append("model = ?")
            params.append(filters['model'])
        
        if 'use_query_expansion' in filters:
            where_clauses.append("use_query_expansion = ?")
            params.append(int(filters['use_query_expansion']))
        
        if 'use_bm25' in filters:
            where_clauses.append("use_bm25 = ?")
            params.append(int(filters['use_bm25']))
        
        if 'use_hybrid' in filters:
            where_clauses.append("use_hybrid = ?")
            params.append(int(filters['use_hybrid']))
        
        if 'use_graph' in filters:
            where_clauses.append("use_graph = ?")
            params.append(int(filters['use_graph']))
        
        if 'use_reranking' in filters:
            where_clauses.append("use_reranking = ?")
            params.append(int(filters['use_reranking']))
        
        if 'start_date' in filters:
            where_clauses.append("timestamp >= ?")
            params.append(filters['start_date'])
        
        if 'end_date' in filters:
            where_clauses.append("timestamp <= ?")
            params.append(filters['end_date'])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Execute query
        conn = get_db()
        cursor = conn.execute(f"""
            SELECT * FROM query_metrics
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])
        
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'query': row['query'],
                'config': {
                    'model': row['model'],
                    'temperature': row['temperature'],
                    'top_k': row['top_k'],
                    'use_query_expansion': bool(row['use_query_expansion']),
                    'use_bm25': bool(row['use_bm25']),
                    'use_hybrid': bool(row['use_hybrid']),
                    'use_graph': bool(row['use_graph']),
                    'use_reranking': bool(row['use_reranking']),
                    'use_web_search': bool(row['use_web_search'])
                },
                'performance': {
                    'total_latency_ms': row['total_latency_ms'],
                    'search_latency_ms': row['search_latency_ms'],
                    'llm_latency_ms': row['llm_latency_ms'],
                    'embedding_latency_ms': row['embedding_latency_ms'],
                    'rerank_latency_ms': row['rerank_latency_ms'],
                    'web_search_latency_ms': row['web_search_latency_ms']
                },
                'results': {
                    'chunks_returned': row['chunks_returned'],
                    'tokens_used': row['tokens_used'],
                    'sources_count': row['sources_count']
                },
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            })
        
        conn.close()
        
        return jsonify({
            'results': results,
            'count': len(results),
            'offset': offset,
            'limit': limit
        })
        
    except Exception as e:
        metrics.increment('query_errors')
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
@timed(metrics, 'get_stats')
def get_stats():
    """Get aggregate statistics"""
    try:
        conn = get_db()
        
        # Total queries
        cursor = conn.execute("SELECT COUNT(*) FROM query_metrics")
        total_queries = cursor.fetchone()[0]
        
        # Average latency
        cursor = conn.execute("""
            SELECT 
                AVG(total_latency_ms) as avg_latency,
                MIN(total_latency_ms) as min_latency,
                MAX(total_latency_ms) as max_latency
            FROM query_metrics
        """)
        latency_stats = cursor.fetchone()
        
        # Model usage
        cursor = conn.execute("""
            SELECT model, COUNT(*) as count
            FROM query_metrics
            GROUP BY model
            ORDER BY count DESC
        """)
        model_usage = [{'model': row['model'], 'count': row['count']} for row in cursor.fetchall()]
        
        # Feature usage
        cursor = conn.execute("""
            SELECT 
                SUM(use_query_expansion) as query_expansion,
                SUM(use_bm25) as bm25,
                SUM(use_hybrid) as hybrid,
                SUM(use_graph) as graph,
                SUM(use_reranking) as reranking,
                SUM(use_web_search) as web_search
            FROM query_metrics
        """)
        feature_usage = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'total_queries': total_queries,
            'latency': {
                'average_ms': latency_stats['avg_latency'],
                'min_ms': latency_stats['min_latency'],
                'max_ms': latency_stats['max_latency']
            },
            'model_usage': model_usage,
            'feature_usage': {
                'query_expansion': feature_usage['query_expansion'],
                'bm25': feature_usage['bm25'],
                'hybrid': feature_usage['hybrid'],
                'graph': feature_usage['graph'],
                'reranking': feature_usage['reranking'],
                'web_search': feature_usage['web_search']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_metrics():
    """Clear all metrics (use with caution!)"""
    try:
        conn = get_db()
        conn.execute("DELETE FROM query_metrics")
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'All metrics cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 Starting {SERVICE_NAME} on port {SERVICE_PORT}")
    print(f"📊 Metrics database: {DB_PATH}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

