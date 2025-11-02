#!/usr/bin/env python3
"""
Comprehensive docker-compose.test.yml update script
Adds env_file, PYTHONUNBUFFERED, flask-cors, and restart policies to ALL services
"""

import re

# Read the file
with open('docker-compose.test.yml', 'r') as f:
    lines = f.readlines()

output = []
i = 0
in_service = False
current_service = None
has_env_file = False
has_environment = False
has_pythonunbuffered = False
env_section_start = -1

while i < len(lines):
    line = lines[i]

    # Detect service start (2 spaces, name, colon)
    if re.match(r'^  [a-z][a-z0-9-]+:$', line):
        in_service = True
        current_service = line.strip().rstrip(':')
        has_env_file = False
        has_environment = False
        has_pythonunbuffered = False
        env_section_start = -1

    # Detect section ends
    if in_service and (line.startswith('  ') and not line.startswith('    ')):
        in_service = False

    # Check for env_file
    if in_service and 'env_file:' in line:
        has_env_file = True

    # Check for environment section
    if in_service and re.match(r'^    environment:', line):
        has_environment = True
        env_section_start = len(output)

        # If no env_file yet, add it before environment
        if not has_env_file:
            output.append('    env_file:\n')
            output.append('      - config.env\n')
            has_env_file = True

    # Check for PYTHONUNBUFFERED
    if in_service and 'PYTHONUNBUFFERED' in line:
        has_pythonunbuffered = True

    # Add PYTHONUNBUFFERED if we're at first env var and don't have it
    if (in_service and has_environment and not has_pythonunbuffered and
        re.match(r'^      - [A-Z]', line)):
        output.append('      - PYTHONUNBUFFERED=1\n')
        has_pythonunbuffered = True

    # Update commands
    if 'python service.py' in line and 'python -u' not in line:
        line = line.replace('python service.py', 'python -u service.py')

    if 'pip install -q flask requests' in line and 'flask-cors' not in line:
        line = line.replace('flask requests', 'flask flask-cors requests')

    if 'pip install -q flask' in line and 'flask-cors' not in line and 'flask flask' not in line:
        line = line.replace('pip install -q flask', 'pip install -q flask flask-cors')

    # Add restart policy before next service or end
    if (in_service and 'command:' in line and i + 1 < len(lines) and
        (lines[i+1].startswith('  ') and not lines[i+1].startswith('    ') or
         lines[i+1].strip().startswith('depends_on:'))):
        output.append(line)
        if i + 1 < len(lines) and 'restart:' not in lines[i+1]:
            output.append('    restart: unless-stopped\n')
        i += 1
        continue

    output.append(line)
    i += 1

# Write back
with open('docker-compose.test.yml', 'w') as f:
    f.writelines(output)

print("✅ Updated docker-compose.test.yml:")
print("   - Added env_file: config.env to services missing it")
print("   - Added PYTHONUNBUFFERED=1 to Python services")
print("   - Updated python to python -u for unbuffered output")
print("   - Added flask-cors to Flask services")
print("   - Added restart: unless-stopped policies")

