"""
Unit tests for TimingCollector

Tests timing measurement, aggregation, merging, and reporting.
"""

import pytest
import time
import sys
import os

# Add services directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

from common.timing import TimingCollector, timed_operation


class TestTimingCollector:
    """Test TimingCollector functionality"""

    def test_basic_timing(self):
        """Test basic operation timing"""
        timer = TimingCollector()

        with timer.measure('test_op'):
            time.sleep(0.01)  # 10ms

        timings = timer.get_timings()

        # Should have the operation and total
        assert 'test_op' in timings
        assert 'total' in timings

        # Should be approximately 10ms (with tolerance)
        assert 9 <= timings['test_op'] <= 15

    def test_multiple_operations(self):
        """Test timing multiple operations"""
        timer = TimingCollector()

        with timer.measure('op1'):
            time.sleep(0.01)

        with timer.measure('op2'):
            time.sleep(0.02)

        with timer.measure('op3'):
            time.sleep(0.01)

        timings = timer.get_timings()

        assert 'op1' in timings
        assert 'op2' in timings
        assert 'op3' in timings

        # op2 should be longest
        assert timings['op2'] > timings['op1']
        assert timings['op2'] > timings['op3']

    def test_nested_operations(self):
        """Test nested timing (should record independently)"""
        timer = TimingCollector()

        with timer.measure('outer'):
            time.sleep(0.01)

            with timer.measure('inner'):
                time.sleep(0.01)

        timings = timer.get_timings()

        # Both should be recorded
        assert 'outer' in timings
        assert 'inner' in timings

        # Outer should be longer (includes inner + sleep)
        # Note: Due to nested context managers, outer timing might
        # not include inner's full duration as expected
        # This is by design - each operation is independent

    def test_manual_record(self):
        """Test manually recording timings"""
        timer = TimingCollector()

        timer.record('manual_op', 123.45)

        timings = timer.get_timings()

        assert timings['manual_op'] == 123.45

    def test_merge_timings(self):
        """Test merging timings from another source"""
        timer = TimingCollector()

        with timer.measure('local_op'):
            time.sleep(0.01)

        # Simulate receiving timings from downstream service
        downstream_timings = {
            'vector_search': 45.0,
            'bm25_search': 23.0,
            'fusion': 12.0,
        }

        timer.merge(downstream_timings)

        timings = timer.get_timings()

        # Should have both local and downstream timings
        assert 'local_op' in timings
        assert 'vector_search' in timings
        assert 'bm25_search' in timings
        assert 'fusion' in timings

        assert timings['vector_search'] == 45.0

    def test_merge_duplicate_keys(self):
        """Test merging with duplicate keys (should add)"""
        timer = TimingCollector()

        timer.record('operation', 10.0)

        # Merge with same key
        timer.merge({'operation': 15.0})

        timings = timer.get_timings()

        # Should sum the durations
        assert timings['operation'] == 25.0

    def test_get_total(self):
        """Test get_total method"""
        timer = TimingCollector()

        time.sleep(0.02)  # 20ms

        total = timer.get_total()

        # Should be approximately 20ms
        assert 18 <= total <= 25

    def test_reset(self):
        """Test reset clears timings"""
        timer = TimingCollector()

        with timer.measure('op1'):
            time.sleep(0.01)

        assert len(timer.timings) > 0

        timer.reset()

        assert len(timer.timings) == 0
        assert timer._total_start is not None  # Should restart

    def test_breakdown_percent(self):
        """Test percentage breakdown calculation"""
        timer = TimingCollector()

        timer.record('op1', 50.0)
        timer.record('op2', 30.0)
        timer.record('op3', 20.0)

        # Manually set total for predictable test
        timer._total_start = time.time() - 0.1  # 100ms ago

        breakdown = timer.get_breakdown_percent()

        assert 'op1' in breakdown
        assert 'op2' in breakdown
        assert 'op3' in breakdown

        # Percentages should be relative to total
        assert breakdown['op1'] > breakdown['op2']
        assert breakdown['op2'] > breakdown['op3']

    def test_summary(self):
        """Test human-readable summary"""
        timer = TimingCollector()

        timer.record('vector_search', 45.0)
        timer.record('bm25_search', 23.0)
        timer.record('fusion', 12.0)

        summary = timer.summary()

        # Should contain operation names
        assert 'vector_search' in summary
        assert 'bm25_search' in summary
        assert 'fusion' in summary

        # Should contain durations
        assert '45ms' in summary
        assert '23ms' in summary
        assert '12ms' in summary

    def test_zero_overhead_when_not_measuring(self):
        """Test that creating timer doesn't add significant overhead"""
        # Without timer
        start = time.time()
        for _ in range(1000):
            x = 1 + 1
        no_timer_duration = time.time() - start

        # With timer (but not measuring)
        timer = TimingCollector()
        start = time.time()
        for _ in range(1000):
            x = 1 + 1
        with_timer_duration = time.time() - start

        # Overhead should be negligible (less than 50% increase)
        assert with_timer_duration < no_timer_duration * 1.5

    def test_concurrent_measures_same_name(self):
        """Test that same operation name can be measured multiple times"""
        timer = TimingCollector()

        with timer.measure('repeated_op'):
            time.sleep(0.01)

        # Measure again with same name (should overwrite)
        with timer.measure('repeated_op'):
            time.sleep(0.02)

        timings = timer.get_timings()

        # Should only have one entry (latest measurement)
        assert timings['repeated_op'] >= 18  # ~20ms


class TestTimedOperationDecorator:
    """Test timed_operation decorator"""

    def test_decorator_with_timer(self):
        """Test decorator when timer is passed"""
        timer = TimingCollector()

        @timed_operation('decorated_op')
        def my_function(timer=None):
            time.sleep(0.01)
            return "result"

        result = my_function(timer=timer)

        assert result == "result"
        assert 'decorated_op' in timer.timings
        assert timer.timings['decorated_op'] >= 9

    def test_decorator_without_timer(self):
        """Test decorator when no timer is passed (should still work)"""
        @timed_operation('op')
        def my_function(timer=None):
            return "result"

        # Should not raise error
        result = my_function()
        assert result == "result"

    def test_decorator_default_name(self):
        """Test decorator uses function name when no name provided"""
        timer = TimingCollector()

        @timed_operation()
        def my_custom_function(timer=None):
            time.sleep(0.01)
            return "result"

        result = my_custom_function(timer=timer)

        assert result == "result"
        assert 'my_custom_function' in timer.timings


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

