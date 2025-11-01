"""
Shared metrics and monitoring utilities
"""
import time
import functools
from typing import Callable, Any
from collections import defaultdict
from threading import Lock

class ServiceMetrics:
    """Simple metrics collector for microservices"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}
        self._lock = Lock()

    def increment(self, metric: str, value: int = 1):
        """Increment a counter"""
        with self._lock:
            self.counters[metric] += value

    def record_time(self, metric: str, duration_ms: float):
        """Record a timing"""
        with self._lock:
            self.timers[metric].append(duration_ms)
            # Keep only last 1000 measurements
            if len(self.timers[metric]) > 1000:
                self.timers[metric] = self.timers[metric][-1000:]

    def set_gauge(self, metric: str, value: float):
        """Set a gauge value"""
        with self._lock:
            self.gauges[metric] = value

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

