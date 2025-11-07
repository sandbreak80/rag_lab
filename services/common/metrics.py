"""
Shared metrics and monitoring utilities
Supports both custom metrics and Prometheus format
"""
import time
import functools
from typing import Callable, Any
from collections import defaultdict
from threading import Lock

# Prometheus client (optional dependency)
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("⚠️  prometheus_client not installed. Prometheus metrics disabled.")

class ServiceMetrics:
    """
    Metrics collector for microservices
    Supports both custom metrics and Prometheus format
    """

    def __init__(self, service_name: str, enable_prometheus: bool = True):
        self.service_name = service_name
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}
        self._lock = Lock()

        # Prometheus support
        self.prometheus_enabled = enable_prometheus and PROMETHEUS_AVAILABLE
        if self.prometheus_enabled:
            self.registry = CollectorRegistry()
            self.prom_counters = {}
            self.prom_histograms = {}
            self.prom_gauges = {}
            print(f"✅ Prometheus metrics enabled for {service_name}")

    def increment(self, metric: str, value: int = 1):
        """Increment a counter"""
        with self._lock:
            self.counters[metric] += value

        # Update Prometheus counter
        if self.prometheus_enabled:
            if metric not in self.prom_counters:
                self.prom_counters[metric] = Counter(
                    f'{self.service_name}_{metric}',
                    f'{metric} count',
                    registry=self.registry
                )
            self.prom_counters[metric].inc(value)

    def record_time(self, metric: str, duration_ms: float):
        """Record a timing"""
        with self._lock:
            self.timers[metric].append(duration_ms)
            # Keep only last 1000 measurements
            if len(self.timers[metric]) > 1000:
                self.timers[metric] = self.timers[metric][-1000:]

        # Update Prometheus histogram (convert ms to seconds)
        if self.prometheus_enabled:
            if metric not in self.prom_histograms:
                self.prom_histograms[metric] = Histogram(
                    f'{self.service_name}_{metric}_seconds',
                    f'{metric} duration in seconds',
                    registry=self.registry
                )
            self.prom_histograms[metric].observe(duration_ms / 1000.0)

    def set_gauge(self, metric: str, value: float):
        """Set a gauge value"""
        with self._lock:
            self.gauges[metric] = value

        # Update Prometheus gauge
        if self.prometheus_enabled:
            if metric not in self.prom_gauges:
                self.prom_gauges[metric] = Gauge(
                    f'{self.service_name}_{metric}',
                    f'{metric} gauge',
                    registry=self.registry
                )
            self.prom_gauges[metric].set(value)

    def get_stats(self) -> dict:
        """Get current stats"""
        with self._lock:
            stats = {
                'service': self.service_name,
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'timers': {}
            }

            # Calculate timer statistics
            for metric, times in self.timers.items():
                if times:
                    sorted_times = sorted(times)
                    stats['timers'][metric] = {
                        'count': len(times),
                        'avg': sum(times) / len(times),
                        'min': min(times),
                        'max': max(times),
                        'p50': sorted_times[len(times) // 2],
                        'p95': sorted_times[int(len(times) * 0.95)],
                        'p99': sorted_times[int(len(times) * 0.99)],
                    }

            return stats

    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.counters.clear()
            self.timers.clear()
            self.gauges.clear()

    def get_prometheus_metrics(self):
        """
        Generate Prometheus-format metrics
        Returns: (metrics_bytes, content_type) tuple
        """
        if not self.prometheus_enabled:
            return b"# Prometheus metrics not available\n", "text/plain"

        return generate_latest(self.registry), CONTENT_TYPE_LATEST

    def get_metrics(self):
        """Alias for get_stats() for consistency"""
        return self.get_stats()


def timed(metrics: ServiceMetrics, metric_name: str):
    """Decorator to time function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics.record_time(metric_name, duration_ms)
                metrics.increment(f"{metric_name}_count")

        return wrapper
    return decorator


def counted(metrics: ServiceMetrics, metric_name: str):
    """Decorator to count function calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            metrics.increment(metric_name)
            return func(*args, **kwargs)

        return wrapper
    return decorator

