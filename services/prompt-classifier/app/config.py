"""
Configuration for Prompt Classifier Service
"""
import os

SERVICE_NAME = os.getenv('SERVICE_NAME', 'prompt-classifier')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8017))

