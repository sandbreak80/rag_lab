#!/usr/bin/env python3
"""
Neural Vault - Educational RAG Lab
API-only Flask backend for React frontend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:5555"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

# Import routes
from api import chat, documents, settings, metrics, lab

# Register blueprints
app.register_blueprint(chat.bp, url_prefix='/api')
app.register_blueprint(documents.bp, url_prefix='/api')
app.register_blueprint(settings.bp, url_prefix='/api')
app.register_blueprint(metrics.bp, url_prefix='/api')
app.register_blueprint(lab.bp, url_prefix='/api')

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'web-api'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5555))
    app.run(host='0.0.0.0', port=port, debug=True)

