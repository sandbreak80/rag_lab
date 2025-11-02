#!/usr/bin/env python3
"""
Update docker-compose.test.yml with:
1. env_file: config.env for all services
2. Proper volume mounts for persistence
3. PYTHONUNBUFFERED=1 for all Python services
4. python -u for unbuffered output
5. flask-cors for all Flask services
"""

import re

# Read the file
with open('docker-compose.test.yml', 'r') as f:
    content = f.read()

# Services that need updates
service_updates = {
    'chat-service': {
        'volumes_add': [],
        'env_remove': ['SEARCH_SERVICE_URL', 'LLM_SERVICE_URL', 'CHAT_MODEL']
    },
    'api-gateway': {
        'volumes_add': [],
        'env_remove': ['SEARCH_SERVICE_URL', 'CHAT_SERVICE_URL', 'VECTOR_DB_URL', 'EMBEDDING_SERVICE_URL']
    },
    'docling-service': {
        'volumes_add': [],
        'env_remove': []
    },
    'ingest-service': {
        'volumes_add': ['knowledge-graph:/kg-data'],
        'env_remove': ['DOCLING_SERVICE_URL', 'EMBEDDING_SERVICE_URL', 'VECTOR_DB_URL', 'UPLOAD_FOLDER']
    },
    'knowledge-graph': {
        'volumes_add': ['knowledge-graph:/kg-data'],
        'env_remove': ['KNOWLEDGE_GRAPH_URL']
    },
    'reranker': {
        'volumes_add': [],
        'env_remove': ['RERANKER_URL']
    },
    'web-search': {
        'volumes_add': [],
        'env_remove': ['SEARXNG_BASE_URL']
    },
    'metrics-store': {
        'volumes_add': [],
        'env_remove': []
    }
}

# Function to add env_file if missing
def add_env_file(service_block):
    if 'env_file:' not in service_block:
        # Find environment section
        env_match = re.search(r'(\s+)environment:', service_block)
        if env_match:
            indent = env_match.group(1)
            env_file_block = f"{indent}env_file:\n{indent}  - config.env\n{indent}environment:"
            service_block = service_block.replace(f"{indent}environment:", env_file_block)
    return service_block

# Function to add PYTHONUNBUFFERED
def add_unbuffered(service_block):
    if 'PYTHONUNBUFFERED' not in service_block and 'python' in service_block.lower():
        env_match = re.search(r'(\s+)environment:.*?\n((?:\s+- [^\n]+\n)*)', service_block, re.DOTALL)
        if env_match:
            indent = env_match.group(1)
            service_block = service_block.replace(
                f"{indent}environment:",
                f"{indent}environment:\n{indent}  - PYTHONUNBUFFERED=1"
            )
    return service_block

# Function to update python command
def update_python_command(service_block):
    service_block = service_block.replace('python service.py', 'python -u service.py')
    service_block = service_block.replace('pip install -q flask requests', 'pip install -q flask flask-cors requests')
    return service_block

# Function to add restart policy
def add_restart(service_block):
    if 'restart:' not in service_block and '    command:' in service_block:
        service_block = re.sub(
            r'(    command: [^\n]+\n)',
            r'\1    restart: unless-stopped\n',
            service_block
        )
    return service_block

# Process each service
for service_name in service_updates.keys():
    # Find service block
    pattern = f'  {service_name}:\n(.*?)(?=\n  [a-z-]+:|$)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        service_block = match.group(0)
        original_block = service_block

        # Apply transformations
        service_block = add_env_file(service_block)
        service_block = add_unbuffered(service_block)
        service_block = update_python_command(service_block)
        service_block = add_restart(service_block)

        # Replace in content
        content = content.replace(original_block, service_block)

# Write back
with open('docker-compose.test.yml', 'w') as f:
    f.write(content)

print("✅ Updated docker-compose.test.yml")
print("   - Added env_file: config.env to all services")
print("   - Added PYTHONUNBUFFERED=1 for Python services")
print("   - Changed python to python -u for unbuffered output")
print("   - Added flask-cors to pip install commands")
print("   - Added restart: unless-stopped policies")

