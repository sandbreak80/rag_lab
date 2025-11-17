#!/usr/bin/env python3
"""
NVIDIA GPU Metrics Exporter for Prometheus
Exposes nvidia-smi metrics in Prometheus format
"""
import subprocess
import re
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
gpu_temperature = Gauge('nvidia_gpu_temperature_celsius', 'GPU temperature in Celsius', ['gpu', 'name'])
gpu_utilization = Gauge('nvidia_gpu_utilization_percent', 'GPU utilization percentage', ['gpu', 'name'])
gpu_memory_used = Gauge('nvidia_gpu_memory_used_bytes', 'GPU memory used in bytes', ['gpu', 'name'])
gpu_memory_total = Gauge('nvidia_gpu_memory_total_bytes', 'GPU memory total in bytes', ['gpu', 'name'])
gpu_power_draw = Gauge('nvidia_gpu_power_draw_watts', 'GPU power draw in watts', ['gpu', 'name'])
gpu_power_limit = Gauge('nvidia_gpu_power_limit_watts', 'GPU power limit in watts', ['gpu', 'name'])
gpu_clock_graphics = Gauge('nvidia_gpu_clock_graphics_mhz', 'GPU graphics clock in MHz', ['gpu', 'name'])
gpu_clock_memory = Gauge('nvidia_gpu_clock_memory_mhz', 'GPU memory clock in MHz', ['gpu', 'name'])
gpu_fan_speed = Gauge('nvidia_gpu_fan_speed_percent', 'GPU fan speed percentage', ['gpu', 'name'])
gpu_processes = Gauge('nvidia_gpu_processes_count', 'Number of processes using GPU', ['gpu', 'name'])

# Error counter
nvidia_smi_errors = Counter('nvidia_smi_errors_total', 'Total number of nvidia-smi errors')


def run_nvidia_smi(query_format):
    """Run nvidia-smi with specified query format"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=' + query_format, '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.error(f"nvidia-smi failed: {result.stderr}")
            nvidia_smi_errors.inc()
            return None
        return result.stdout.strip().split('\n')
    except subprocess.TimeoutExpired:
        logger.error("nvidia-smi timeout")
        nvidia_smi_errors.inc()
        return None
    except FileNotFoundError:
        logger.error("nvidia-smi not found")
        nvidia_smi_errors.inc()
        return None
    except Exception as e:
        logger.error(f"Error running nvidia-smi: {e}")
        nvidia_smi_errors.inc()
        return None


def collect_gpu_metrics():
    """Collect all GPU metrics from nvidia-smi"""
    # Get GPU names and indices
    gpu_info = run_nvidia_smi('index,name')
    if not gpu_info:
        return

    gpus = []
    for line in gpu_info:
        if ',' in line:
            index, name = line.split(',', 1)
            gpus.append((index.strip(), name.strip()))

    if not gpus:
        logger.warning("No GPUs found")
        return

    # Collect metrics for each GPU
    metrics = {
        'temperature': run_nvidia_smi('index,name,temperature.gpu'),
        'utilization': run_nvidia_smi('index,name,utilization.gpu'),
        'memory_used': run_nvidia_smi('index,name,memory.used'),
        'memory_total': run_nvidia_smi('index,name,memory.total'),
        'power_draw': run_nvidia_smi('index,name,power.draw'),
        'power_limit': run_nvidia_smi('index,name,power.limit'),
        'clock_graphics': run_nvidia_smi('index,name,clocks.current.graphics'),
        'clock_memory': run_nvidia_smi('index,name,clocks.current.memory'),
        'fan_speed': run_nvidia_smi('index,name,fan.speed'),
    }

    # Parse and set metrics
    for gpu_idx, gpu_name in gpus:
        for metric_type, lines in metrics.items():
            if not lines:
                continue

            for line in lines:
                if ',' in line:
                    parts = line.split(',')
                    if len(parts) >= 3 and parts[0].strip() == gpu_idx:
                        value_str = parts[2].strip()
                        try:
                            value = float(value_str)

                            if metric_type == 'temperature':
                                gpu_temperature.labels(gpu=gpu_idx, name=gpu_name).set(value)
                            elif metric_type == 'utilization':
                                gpu_utilization.labels(gpu=gpu_idx, name=gpu_name).set(value)
                            elif metric_type == 'memory_used':
                                # Convert MB to bytes
                                gpu_memory_used.labels(gpu=gpu_idx, name=gpu_name).set(value * 1024 * 1024)
                            elif metric_type == 'memory_total':
                                # Convert MB to bytes
                                gpu_memory_total.labels(gpu=gpu_idx, name=gpu_name).set(value * 1024 * 1024)
                            elif metric_type == 'power_draw':
                                gpu_power_draw.labels(gpu=gpu_idx, name=gpu_name).set(value)
                            elif metric_type == 'power_limit':
                                gpu_power_limit.labels(gpu=gpu_idx, name=gpu_name).set(value)
                            elif metric_type == 'clock_graphics':
                                gpu_clock_graphics.labels(gpu=gpu_idx, name=gpu_name).set(value)
                            elif metric_type == 'clock_memory':
                                gpu_clock_memory.labels(gpu=gpu_idx, name=gpu_name).set(value)
                            elif metric_type == 'fan_speed':
                                gpu_fan_speed.labels(gpu=gpu_idx, name=gpu_name).set(value)
                        except ValueError:
                            logger.warning(f"Could not parse value '{value_str}' for {metric_type}")
                            continue

    # Count processes per GPU
    processes = run_nvidia_smi('index,name,processes.count')
    if processes:
        for line in processes:
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 3:
                    gpu_idx = parts[0].strip()
                    gpu_name = parts[1].strip()
                    try:
                        count = int(parts[2].strip())
                        gpu_processes.labels(gpu=gpu_idx, name=gpu_name).set(count)
                    except ValueError:
                        continue


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint"""

    def do_GET(self):
        if self.path == '/metrics':
            # Collect fresh metrics
            collect_gpu_metrics()

            # Generate Prometheus format
            output = generate_latest()
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(output)
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logger.info(format % args)


def main():
    """Start the metrics server"""
    import os
    port = int(os.getenv('METRICS_PORT', '9401'))
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    logger.info(f"Starting NVIDIA GPU metrics exporter on port {port}")
    logger.info("Metrics available at http://0.0.0.0:{}/metrics".format(port))
    server.serve_forever()


if __name__ == '__main__':
    main()

