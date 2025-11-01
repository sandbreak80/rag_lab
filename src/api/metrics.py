"""
Metrics API routes
"""
from flask import Blueprint, request, jsonify
import json
import os

bp = Blueprint('metrics', __name__)

# In-memory storage for metrics (in production, use a database)
METRICS_FILE = '/tmp/query_metrics.json'

def load_metrics():
    """Load metrics from file"""
    try:
        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, 'r') as f:
                return json.load(f)
        return []
    except:
        return []

def save_metrics(metrics):
    """Save metrics to file"""
    try:
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f)
    except:
        pass

@bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get query metrics history"""
    try:
        metrics = load_metrics()
        return jsonify({'metrics': metrics})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/metrics', methods=['POST'])
def log_metric():
    """Log a query metric"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('query'):
            return jsonify({'error': 'Query is required'}), 400
        
        metrics = load_metrics()
        metrics.append(data)
        
        # Keep only last 100 metrics
        if len(metrics) > 100:
            metrics = metrics[-100:]
        
        save_metrics(metrics)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/metrics', methods=['DELETE'])
def clear_metrics():
    """Clear all metrics"""
    try:
        save_metrics([])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
