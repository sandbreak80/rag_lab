"""
Timing Collector - Per-operation timing instrumentation

This module provides a simple, consistent way to measure and aggregate
timing data across all services. Critical for complete waterfall charts.

Design Goals:
- Zero overhead when not measuring
- Context manager for easy use
- Aggregatable across service boundaries
- Compatible with existing metrics systems
"""

import time
import threading
from contextlib import contextmanager
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TimingCollector:
    """
    Thread-safe timing collector for operations.
    
    THREAD SAFETY: Uses RLock to prevent race conditions in multi-threaded
    contexts (e.g., Flask with threading). Safe for concurrent access.

    Usage:
        timer = TimingCollector()

        with timer.measure('operation_name'):
            do_work()

        timings = timer.get_timings()
        # {'operation_name': 123.45, 'total': 123.45}
    """

    timings: Dict[str, float] = field(default_factory=dict)
    _start_times: Dict[str, float] = field(default_factory=dict)
    _total_start: Optional[float] = None
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def __post_init__(self):
        """Start total timer on initialization"""
        with self._lock:
            self._total_start = time.time()

    @contextmanager
    def measure(self, operation: str):
        """
        Context manager for timing operations (thread-safe).

        Args:
            operation: Name of the operation being timed

        Example:
            with timer.measure('vector_search'):
                results = search_vectors(query)
        """
        start = time.time()
        
        # Store start time (thread-safe)
        with self._lock:
            self._start_times[operation] = start

        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            # Record timing (thread-safe)
            with self._lock:
                self.timings[operation] = duration_ms

    def record(self, operation: str, duration_ms: float):
        """
        Manually record a timing (thread-safe).

        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
        """
        with self._lock:
            self.timings[operation] = duration_ms

    def get_timings(self) -> Dict[str, float]:
        """
        Get all recorded timings, including total (thread-safe).

        Returns:
            Dictionary of operation names to durations in milliseconds
        """
        with self._lock:
            timings = self.timings.copy()

            # Add total time if we have a start
            if self._total_start:
                timings['total'] = (time.time() - self._total_start) * 1000

            return timings

    def get_total(self) -> float:
        """Get total elapsed time in milliseconds (thread-safe)"""
        with self._lock:
            if self._total_start:
                return (time.time() - self._total_start) * 1000
            return 0.0

    def reset(self):
        """Clear all timings (thread-safe)"""
        with self._lock:
            self.timings.clear()
            self._start_times.clear()
            self._total_start = time.time()

    def merge(self, other_timings: Dict[str, float]):
        """
        Merge timings from another source (thread-safe).
        
        NOTE: If operation exists in both, this REPLACES the value.
        For parallel operations that should be added, use merge_add().

        Args:
            other_timings: Dictionary of operation names to durations
        """
        with self._lock:
            for operation, duration in other_timings.items():
                # Replace mode (default): downstream service timing is authoritative
                self.timings[operation] = duration
    
    def merge_add(self, other_timings: Dict[str, float]):
        """
        Merge timings by ADDING durations for duplicate keys (thread-safe).
        
        Use this for parallel operations where total time is sum of parts.

        Args:
            other_timings: Dictionary of operation names to durations
        """
        with self._lock:
            for operation, duration in other_timings.items():
                if operation in self.timings:
                    self.timings[operation] += duration
                else:
                    self.timings[operation] = duration

    def get_breakdown_percent(self) -> Dict[str, float]:
        """
        Get percentage breakdown of timings (thread-safe).

        Returns:
            Dictionary of operation names to percentage of total time
        """
        total = self.get_total()
        if total == 0:
            import logging
            logging.warning("TimingCollector has zero total time - no operations measured")
            return {}

        with self._lock:
            breakdown = {}
            for operation, duration in self.timings.items():
                if operation != 'total':
                    breakdown[operation] = round((duration / total) * 100, 1)

            return breakdown

    def summary(self) -> str:
        """Get human-readable summary of timings"""
        timings = self.get_timings()
        total = timings.get('total', 0)

        lines = [f"⏱️  Total: {total:.0f}ms"]

        # Sort by duration descending
        sorted_ops = sorted(
            [(k, v) for k, v in timings.items() if k != 'total'],
            key=lambda x: x[1],
            reverse=True
        )

        for operation, duration in sorted_ops:
            percent = (duration / total * 100) if total > 0 else 0
            lines.append(f"  • {operation}: {duration:.0f}ms ({percent:.1f}%)")

        return '\n'.join(lines)


# Decorator for timing functions
def timed_operation(operation_name: str = None):
    """
    Decorator to automatically time a function.

    Usage:
        @timed_operation('my_operation')
        def my_function():
            ...

    Note: This requires passing a TimingCollector to the function
    or accessing one from context.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to find timer in kwargs
            timer = kwargs.get('timer')

            if timer and isinstance(timer, TimingCollector):
                op_name = operation_name or func.__name__
                with timer.measure(op_name):
                    return func(*args, **kwargs)
            else:
                # No timer, just run function
                return func(*args, **kwargs)

        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    import time

    # Example 1: Basic usage
    print("Example 1: Basic timing")
    timer = TimingCollector()

    with timer.measure('operation_a'):
        time.sleep(0.1)

    with timer.measure('operation_b'):
        time.sleep(0.05)

    print(timer.summary())
    print()

    # Example 2: Nested operations
    print("Example 2: Nested operations")
    timer2 = TimingCollector()

    with timer2.measure('total_operation'):
        with timer2.measure('step_1'):
            time.sleep(0.05)

        with timer2.measure('step_2'):
            time.sleep(0.03)

        with timer2.measure('step_3'):
            time.sleep(0.02)

    print(timer2.summary())
    print()

    # Example 3: Merging timings from services
    print("Example 3: Merging service timings")
    gateway_timer = TimingCollector()

    with gateway_timer.measure('gateway_overhead'):
        time.sleep(0.01)

    # Simulate receiving timings from search service
    search_timings = {
        'vector_search': 45.0,
        'bm25_search': 23.0,
        'hybrid_fusion': 12.0,
    }
    gateway_timer.merge(search_timings)

    print(gateway_timer.summary())
    print()

    # Example 4: Breakdown percentages
    print("Example 4: Percentage breakdown")
    breakdown = gateway_timer.get_breakdown_percent()
    for operation, percent in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
        print(f"  {operation}: {percent}%")

    print("\n✅ TimingCollector tests complete!")

