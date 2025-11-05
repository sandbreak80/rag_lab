"""
Configuration for Model Router Service
"""
import os

SERVICE_NAME = os.getenv('SERVICE_NAME', 'model-router')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', '8018'))

# Ollama configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://ollama:11434')

# Classifier configuration
PROMPT_CLASSIFIER_URL = os.getenv('PROMPT_CLASSIFIER_URL', 'http://prompt-classifier:8017')

