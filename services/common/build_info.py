#!/usr/bin/env python3
"""
Build information module - Exposes version and build numbers
"""

import os
from datetime import datetime
from pathlib import Path

# Try to read BUILD_INFO from project root
BUILD_INFO_PATH = Path(__file__).parent.parent.parent / 'BUILD_INFO'

def parse_build_info():
    """Parse BUILD_INFO file and return as dict"""
    build_info = {
        'build_number': os.getenv('BUILD_NUMBER', 'dev'),
        'build_date': os.getenv('BUILD_DATE', datetime.utcnow().isoformat() + 'Z'),
        'build_tag': os.getenv('BUILD_TAG', 'v1.0.0-dev'),
        'git_commit': os.getenv('GIT_COMMIT', 'unknown'),
        'environment': os.getenv('ENVIRONMENT', 'development')
    }

    # Try to read from BUILD_INFO file if it exists
    if BUILD_INFO_PATH.exists():
        try:
            with open(BUILD_INFO_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        if key in build_info:
                            build_info[key] = value
        except Exception as e:
            print(f"Warning: Could not read BUILD_INFO: {e}")

    return build_info

def get_service_version(service_name: str) -> dict:
    """
    Get version info for a specific service

    Returns:
        {
            'service': str,
            'version': str,
            'build_number': str,
            'build_date': str,
            'build_tag': str,
            'environment': str
        }
    """
    build_info = parse_build_info()

    # Try to get service-specific version from BUILD_INFO
    service_version_key = f"{service_name.upper().replace('-', '_')}_VERSION"
    service_version = os.getenv(service_version_key, '1.0.0')

    return {
        'service': service_name,
        'version': service_version,
        'build_number': build_info['build_number'],
        'build_date': build_info['build_date'],
        'build_tag': build_info['build_tag'],
        'git_commit': build_info['git_commit'],
        'environment': build_info['environment']
    }

def get_full_version_string(service_name: str) -> str:
    """
    Get full version string for logging

    Example: "chat-service v1.0.0 (build 20251105.1)"
    """
    info = get_service_version(service_name)
    return f"{service_name} {info['build_tag']} (build {info['build_number']})"

# Pre-parsed build info (singleton)
_BUILD_INFO = parse_build_info()

def get_build_info() -> dict:
    """Get cached build info"""
    return _BUILD_INFO.copy()

