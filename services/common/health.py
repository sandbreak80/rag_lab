"""
Health check utilities for microservices
"""
import time
import os
from datetime import datetime
from typing import Dict, Any, Callable, List
from enum import Enum

class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

class HealthCheck:
    """Health check manager for microservices"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = time.time()
        self.checks: List[Dict[str, Any]] = []

    def add_check(self, name: str, check_func: Callable[[], bool]):
        """Add a health check"""
        self.checks.append({
            'name': name,
            'func': check_func
        })

    def get_health(self) -> Dict[str, Any]:
        """Get current health status"""
        uptime = time.time() - self.start_time

        health = {
            'service': self.service_name,
            'status': HealthStatus.HEALTHY,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': uptime,
            'checks': {}
        }

        # Run all checks
        all_healthy = True
        for check in self.checks:
            try:
                result = check['func']()
                health['checks'][check['name']] = {
                    'status': 'pass' if result else 'fail',
                    'healthy': result
                }
                if not result:
                    all_healthy = False
            except Exception as e:
                health['checks'][check['name']] = {
                    'status': 'fail',
                    'healthy': False,
                    'error': str(e)
                }
                all_healthy = False

        # Set overall status
        if not all_healthy:
            health['status'] = HealthStatus.UNHEALTHY

        return health

    def is_healthy(self) -> bool:
        """Quick health check"""
        health = self.get_health()
        return health['status'] == HealthStatus.HEALTHY

    def get_version(self) -> Dict[str, str]:
        """Get service version info"""
        # Try to read VERSION file from project root
        version = "unknown"
        try:
            version_file = os.path.join('/workspace', 'VERSION')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    version = f.read().strip()
        except Exception:
            pass
        
        return {
            'service': self.service_name,
            'version': version,
            'timestamp': datetime.utcnow().isoformat()
        }

