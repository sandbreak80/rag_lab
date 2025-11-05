"""
Configuration for Prompt Enhancer Service
"""
import os

SERVICE_NAME = os.getenv('SERVICE_NAME', 'prompt-enhancer')
SERVICE_PORT = int(os.getenv('SERVICE_PORT', 8018))

