"""
Configuration for Research Agent
"""
import os

SERVICE_NAME = os.getenv('SERVICE_NAME', 'research-agent')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8015))
INGEST_SERVICE_URL = os.getenv('INGEST_SERVICE_URL', 'http://ingest-service:8001')
DB_PATH = os.getenv('DB_PATH', '/data/research_agent.db')

