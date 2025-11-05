"""
Configuration for Prompt Categorizer Service
"""
import os

SERVICE_NAME = os.getenv('SERVICE_NAME', 'prompt-categorizer')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '8017'))

# Ollama configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')
CATEGORIZER_MODEL = os.getenv('CATEGORIZER_MODEL', 'llama3.2:3b')

