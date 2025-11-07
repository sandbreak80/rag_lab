#!/usr/bin/env python3
"""
Docker Health Check Exporter
Exposes Docker container health check status as Prometheus metrics
"""
import docker
import time
from prometheus_client import start_http_server, Gauge
import os

# Initialize Docker client
client = docker.from_env()

# Create Prometheus gauge for health status
# 0 = no healthcheck, 1 = starting, 2 = healthy, 3 = unhealthy
container_health_status = Gauge(
    'container_health_status',
    'Docker container health check status (0=none, 1=starting, 2=healthy, 3=unhealthy)',
    ['name', 'id', 'image']
)

def get_health_status_value(status):
    """Convert health status string to numeric value"""
    status_map = {
        'none': 0,
        'starting': 1,
        'healthy': 2,
        'unhealthy': 3
    }
    return status_map.get(status.lower(), 0)

def collect_container_health():
    """Collect health status from all containers"""
    try:
        containers = client.containers.list(all=False)  # Only running containers
        
        for container in containers:
            # Get container details
            name = container.name
            container_id = container.short_id
            image = container.image.tags[0] if container.image.tags else container.image.short_id
            
            # Get health status
            health = container.attrs.get('State', {}).get('Health', {})
            if health:
                status = health.get('Status', 'none')
            else:
                status = 'none'
            
            # Set metric
            health_value = get_health_status_value(status)
            container_health_status.labels(name=name, id=container_id, image=image).set(health_value)
            
            print(f"✅ {name}: {status} (value={health_value})")
    
    except Exception as e:
        print(f"❌ Error collecting container health: {e}")

def main():
    """Main loop"""
    port = int(os.getenv('SERVICE_PORT', 9099))
    
    print(f"🚀 Docker Health Exporter starting on port {port}")
    print(f"📊 Metrics available at http://localhost:{port}/metrics")
    
    # Start Prometheus HTTP server
    start_http_server(port)
    
    # Collect metrics every 15 seconds
    while True:
        print(f"\n🔍 Collecting container health status...")
        collect_container_health()
        time.sleep(15)

if __name__ == '__main__':
    main()

