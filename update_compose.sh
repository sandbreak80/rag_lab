#!/bin/bash
# Comprehensive update of docker-compose.test.yml
# 1. Add env_file to all services
# 2. Update volume mounts
# 3. Add PYTHONUNBUFFERED
# 4. Update commands for unbuffered output
# 5. Add flask-cors to all Flask services

echo "📝 Updating docker-compose.test.yml..."

cd /Users/bmstoner/code_projects/rag_lab

# Backup
cp docker-compose.test.yml docker-compose.test.yml.bak

# Use Python to do comprehensive updates
python3 << 'EOF'
import yaml
import sys

# Read file
with open('docker-compose.test.yml', 'r') as f:
    content = f.read()

# Services to update
services_to_update = [
    'chat-service',
    'api-gateway',
    'docling-service',
    'ingest-service',
    'knowledge-graph',
    'reranker',
    'web-search',
    'metrics-store'
]

# For each service, add env_file if missing
for service in services_to_update:
    # Find the service block
    service_start = content.find(f'  {service}:')
    if service_start == -1:
        continue

    # Find next service or end
    next_service = len(content)
    for other_service in ['  ' + s + ':' for s in services_to_update] + ['  react-ui:', '  playwright:', '  searxng:']:
        pos = content.find(other_service, service_start + 1)
        if pos != -1 and pos < next_service:
            next_service = pos

    service_block = content[service_start:next_service]
    original_block = service_block

    # Add env_file if missing
    if 'env_file:' not in service_block and 'environment:' in service_block:
        service_block = service_block.replace(
            '    environment:',
            '    env_file:\n      - config.env\n    environment:'
        )

    # Add PYTHONUNBUFFERED if missing
    if 'PYTHONUNBUFFERED' not in service_block and 'python' in service_block.lower():
        service_block = service_block.replace(
            '    environment:\n',
            '    environment:\n      - PYTHONUNBUFFERED=1\n'
        )

    # Update python command
    service_block = service_block.replace('python service.py', 'python -u service.py')

    # Add flask-cors
    if 'flask' in service_block and 'flask-cors' not in service_block:
        service_block = service_block.replace('flask requests', 'flask flask-cors requests')
        service_block = service_block.replace('flask flask requests', 'flask flask-cors requests')  # Handle both cases

    # Add restart policy if missing
    if 'restart:' not in service_block and 'command:' in service_block:
        # Find the command line
        cmd_pos = service_block.rfind('    command:')
        if cmd_pos != -1:
            # Find end of command line
            newline_pos = service_block.find('\n', cmd_pos)
            if newline_pos != -1:
                service_block = service_block[:newline_pos+1] + '    restart: unless-stopped\n' + service_block[newline_pos+1:]

    # Replace in content
    content = content.replace(original_block, service_block)

# Write back
with open('docker-compose.test.yml', 'w') as f:
    f.write(content)

print("✅ Updated docker-compose.test.yml")
EOF

echo "✅ docker-compose.test.yml updated!"
echo ""
echo "Changes made:"
echo "  - Added env_file: config.env to all services"
echo "  - Added PYTHONUNBUFFERED=1 for Python services"
echo "  - Changed python to python -u for unbuffered output"
echo "  - Added flask-cors to Flask services"
echo "  - Added restart: unless-stopped policies"
echo ""
echo "Backup saved to: docker-compose.test.yml.bak"

