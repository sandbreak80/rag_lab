#!/usr/bin/env python3
"""
Metrics Storage Service - Persistent performance metrics for lab analysis
Stores query performance data in SQLite for historical analysis
Also collects system metrics (CPU, RAM) and Docker stats in real-time
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime, timedelta
import sys
import threading
import time
import psutil
import subprocess

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

-- System Metrics (like 'top')
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu_percent REAL,
    memory_percent REAL,
    memory_used_mb REAL,
    memory_total_mb REAL,
    disk_usage_percent REAL,
    disk_read_mb REAL,
    disk_write_mb REAL,
    network_sent_mb REAL,
    network_recv_mb REAL,
    load_avg_1m REAL,
    load_avg_5m REAL,
    load_avg_15m REAL
);

CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp);

-- Docker Container Stats
CREATE TABLE IF NOT EXISTS docker_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    container_name TEXT NOT NULL,
    container_id TEXT,
    cpu_percent REAL,
    memory_percent REAL,
    memory_used_mb REAL,
    memory_limit_mb REAL,
    network_rx_mb REAL,
    network_tx_mb REAL,
    block_read_mb REAL,
    block_write_mb REAL,
    pids INTEGER
);

CREATE INDEX IF NOT EXISTS idx_docker_timestamp ON docker_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_docker_container ON docker_stats(container_name);
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

# Background metric collection
def collect_system_metrics():
    """Background thread to collect system metrics every 5 seconds"""
    print("🔄 Starting system metrics collection thread...")

    # Store previous network/disk counters for delta calculations
    prev_network = psutil.net_io_counters()
    prev_disk = psutil.disk_io_counters()

    while True:
        try:
            time.sleep(5)  # Collect every 5 seconds

            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Disk
            disk = psutil.disk_usage('/')
            curr_disk = psutil.disk_io_counters()
            disk_read_mb = (curr_disk.read_bytes - prev_disk.read_bytes) / 1024 / 1024
            disk_write_mb = (curr_disk.write_bytes - prev_disk.write_bytes) / 1024 / 1024
            prev_disk = curr_disk

            # Network
            curr_network = psutil.net_io_counters()
            network_sent_mb = (curr_network.bytes_sent - prev_network.bytes_sent) / 1024 / 1024
            network_recv_mb = (curr_network.bytes_recv - prev_network.bytes_recv) / 1024 / 1024
            prev_network = curr_network

            # Load average (Unix-like systems)
            try:
                load_avg = os.getloadavg()
            except (AttributeError, OSError):
                load_avg = (0, 0, 0)

            # Store in database
            conn = get_db()
            conn.execute("""
                INSERT INTO system_metrics (
                    timestamp, cpu_percent, memory_percent, memory_used_mb, memory_total_mb,
                    disk_usage_percent, disk_read_mb, disk_write_mb,
                    network_sent_mb, network_recv_mb,
                    load_avg_1m, load_avg_5m, load_avg_15m
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                cpu_percent,
                memory.percent,
                memory.used / 1024 / 1024,
                memory.total / 1024 / 1024,
                disk.percent,
                disk_read_mb,
                disk_write_mb,
                network_sent_mb,
                network_recv_mb,
                load_avg[0],
                load_avg[1],
                load_avg[2]
            ))
            conn.commit()

            # Clean up old data (keep only last 10 minutes)
            cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
            conn.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff,))
            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ Error collecting system metrics: {e}")

def collect_docker_stats():
    """Background thread to collect Docker container stats every 5 seconds"""
    print("🐳 Starting Docker stats collection thread...")

    while True:
        try:
            time.sleep(5)  # Collect every 5 seconds

            # Get Docker stats using subprocess (docker stats --no-stream --format json)
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', '{{json .}}'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                timestamp = datetime.utcnow().isoformat()
                conn = get_db()

                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue

                    try:
                        stat = json.loads(line)

                        # Parse percentage strings (e.g., "12.34%")
                        cpu_percent = float(stat.get('CPUPerc', '0%').rstrip('%'))
                        memory_percent = float(stat.get('MemPerc', '0%').rstrip('%'))

                        # Parse memory usage (e.g., "123.4MiB / 1.5GiB")
                        mem_usage_str = stat.get('MemUsage', '0MiB / 0MiB')
                        mem_parts = mem_usage_str.split(' / ')
                        memory_used_mb = parse_size_to_mb(mem_parts[0]) if len(mem_parts) > 0 else 0
                        memory_limit_mb = parse_size_to_mb(mem_parts[1]) if len(mem_parts) > 1 else 0

                        # Parse network I/O (e.g., "1.2MB / 3.4MB")
                        net_io_str = stat.get('NetIO', '0B / 0B')
                        net_parts = net_io_str.split(' / ')
                        network_rx_mb = parse_size_to_mb(net_parts[0]) if len(net_parts) > 0 else 0
                        network_tx_mb = parse_size_to_mb(net_parts[1]) if len(net_parts) > 1 else 0

                        # Parse block I/O (e.g., "5.6MB / 7.8MB")
                        block_io_str = stat.get('BlockIO', '0B / 0B')
                        block_parts = block_io_str.split(' / ')
                        block_read_mb = parse_size_to_mb(block_parts[0]) if len(block_parts) > 0 else 0
                        block_write_mb = parse_size_to_mb(block_parts[1]) if len(block_parts) > 1 else 0

                        # PIDs
                        pids = int(stat.get('PIDs', 0))

                        conn.execute("""
                            INSERT INTO docker_stats (
                                timestamp, container_name, container_id,
                                cpu_percent, memory_percent, memory_used_mb, memory_limit_mb,
                                network_rx_mb, network_tx_mb, block_read_mb, block_write_mb, pids
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            timestamp,
                            stat.get('Name', 'unknown'),
                            stat.get('ID', ''),
                            cpu_percent,
                            memory_percent,
                            memory_used_mb,
                            memory_limit_mb,
                            network_rx_mb,
                            network_tx_mb,
                            block_read_mb,
                            block_write_mb,
                            pids
                        ))
                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        print(f"⚠️  Error parsing Docker stat line: {e}")
                        continue

                conn.commit()

                # Clean up old data (keep only last 10 minutes)
                cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
                conn.execute("DELETE FROM docker_stats WHERE timestamp < ?", (cutoff,))
                conn.commit()
                conn.close()

        except subprocess.TimeoutExpired:
            print("⚠️  Docker stats command timed out")
        except FileNotFoundError:
            print("⚠️  Docker command not found (not running in Docker environment?)")
            time.sleep(30)  # Wait longer if Docker isn't available
        except Exception as e:
            print(f"❌ Error collecting Docker stats: {e}")

def parse_size_to_mb(size_str):
    """Parse size string (e.g., '123.4MiB', '1.5GiB', '500kB') to MB"""
    size_str = size_str.strip()

    # Extract number and unit
    import re
    match = re.match(r'([\d.]+)([A-Za-z]+)', size_str)
    if not match:
        return 0

    value = float(match.group(1))
    unit = match.group(2).upper()

    # Convert to MB
    conversions = {
        'B': 1 / 1024 / 1024,
        'KB': 1 / 1024,
        'KIB': 1 / 1024,
        'MB': 1,
        'MIB': 1,
        'GB': 1024,
        'GIB': 1024,
        'TB': 1024 * 1024,
        'TIB': 1024 * 1024
    }

    return value * conversions.get(unit, 1)

# Start background threads
system_thread = threading.Thread(target=collect_system_metrics, daemon=True)
docker_thread = threading.Thread(target=collect_docker_stats, daemon=True)
system_thread.start()
docker_thread.start()

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

@app.route('/system/current', methods=['GET'])
@timed(metrics, 'get_system_current')
def get_system_current():
    """Get current system metrics (last 10 minutes)"""
    try:
        conn = get_db()

        # Get all system metrics from last 10 minutes
        cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        cursor = conn.execute("""
            SELECT * FROM system_metrics
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (cutoff,))

        rows = cursor.fetchall()

        metrics_data = []
        for row in rows:
            metrics_data.append({
                'timestamp': row['timestamp'],
                'cpu_percent': row['cpu_percent'],
                'memory_percent': row['memory_percent'],
                'memory_used_mb': row['memory_used_mb'],
                'memory_total_mb': row['memory_total_mb'],
                'disk_usage_percent': row['disk_usage_percent'],
                'disk_read_mb': row['disk_read_mb'],
                'disk_write_mb': row['disk_write_mb'],
                'network_sent_mb': row['network_sent_mb'],
                'network_recv_mb': row['network_recv_mb'],
                'load_avg_1m': row['load_avg_1m'],
                'load_avg_5m': row['load_avg_5m'],
                'load_avg_15m': row['load_avg_15m']
            })

        conn.close()

        return jsonify({
            'metrics': metrics_data,
            'count': len(metrics_data),
            'window_minutes': 10
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/docker/current', methods=['GET'])
@timed(metrics, 'get_docker_current')
def get_docker_current():
    """Get current Docker container stats (last 10 minutes)"""
    try:
        conn = get_db()

        # Get all Docker stats from last 10 minutes
        cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        cursor = conn.execute("""
            SELECT * FROM docker_stats
            WHERE timestamp >= ?
            ORDER BY timestamp ASC, container_name ASC
        """, (cutoff,))

        rows = cursor.fetchall()

        # Group by container
        containers = {}
        for row in rows:
            container_name = row['container_name']
            if container_name not in containers:
                containers[container_name] = []

            containers[container_name].append({
                'timestamp': row['timestamp'],
                'cpu_percent': row['cpu_percent'],
                'memory_percent': row['memory_percent'],
                'memory_used_mb': row['memory_used_mb'],
                'memory_limit_mb': row['memory_limit_mb'],
                'network_rx_mb': row['network_rx_mb'],
                'network_tx_mb': row['network_tx_mb'],
                'block_read_mb': row['block_read_mb'],
                'block_write_mb': row['block_write_mb'],
                'pids': row['pids']
            })

        conn.close()

        return jsonify({
            'containers': containers,
            'container_count': len(containers),
            'total_datapoints': len(rows),
            'window_minutes': 10
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/system/summary', methods=['GET'])
@timed(metrics, 'get_system_summary')
def get_system_summary():
    """Get summary statistics for system metrics (last 10 minutes)"""
    try:
        conn = get_db()

        cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        cursor = conn.execute("""
            SELECT
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                AVG(disk_read_mb) as avg_disk_read,
                AVG(disk_write_mb) as avg_disk_write,
                AVG(network_sent_mb) as avg_network_sent,
                AVG(network_recv_mb) as avg_network_recv,
                AVG(load_avg_1m) as avg_load_1m
            FROM system_metrics
            WHERE timestamp >= ?
        """, (cutoff,))

        row = cursor.fetchone()
        conn.close()

        return jsonify({
            'avg_cpu_percent': row['avg_cpu'],
            'max_cpu_percent': row['max_cpu'],
            'avg_memory_percent': row['avg_memory'],
            'max_memory_percent': row['max_memory'],
            'avg_disk_read_mb_per_sample': row['avg_disk_read'],
            'avg_disk_write_mb_per_sample': row['avg_disk_write'],
            'avg_network_sent_mb_per_sample': row['avg_network_sent'],
            'avg_network_recv_mb_per_sample': row['avg_network_recv'],
            'avg_load_1m': row['avg_load_1m'],
            'window_minutes': 10
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/docker/summary', methods=['GET'])
@timed(metrics, 'get_docker_summary')
def get_docker_summary():
    """Get summary statistics for Docker containers (last 10 minutes)"""
    try:
        conn = get_db()

        cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        cursor = conn.execute("""
            SELECT
                container_name,
                AVG(cpu_percent) as avg_cpu,
                MAX(cpu_percent) as max_cpu,
                AVG(memory_percent) as avg_memory,
                MAX(memory_percent) as max_memory,
                AVG(memory_used_mb) as avg_memory_used_mb,
                AVG(pids) as avg_pids
            FROM docker_stats
            WHERE timestamp >= ?
            GROUP BY container_name
            ORDER BY avg_cpu DESC
        """, (cutoff,))

        rows = cursor.fetchall()

        containers = []
        for row in rows:
            containers.append({
                'container_name': row['container_name'],
                'avg_cpu_percent': row['avg_cpu'],
                'max_cpu_percent': row['max_cpu'],
                'avg_memory_percent': row['avg_memory'],
                'max_memory_percent': row['max_memory'],
                'avg_memory_used_mb': row['avg_memory_used_mb'],
                'avg_pids': row['avg_pids']
            })

        conn.close()

        return jsonify({
            'containers': containers,
            'count': len(containers),
            'window_minutes': 10
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 Starting {SERVICE_NAME} on port {SERVICE_PORT}")
    print(f"📊 Metrics database: {DB_PATH}")
    app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False)

