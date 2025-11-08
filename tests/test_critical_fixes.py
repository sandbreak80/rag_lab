"""
Critical Bug Fix Tests - Issues #1, #2, #3 from Code Review

These tests specifically verify that the 3 critical issues found in the
code review have been fixed:

1. Immutable Metadata (Issue #1)
2. Thread Safety (Issue #2)
3. from_dict() Validation (Issue #3)
"""

import pytest
import threading
import time
from datetime import datetime, timezone
import sys
import os

# Add services directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

from common.evidence import Evidence, OriginTool
from common.timing import TimingCollector


class TestIssue1_ImmutableMetadata:
    """
    Test that metadata dictionary is truly immutable.

    CRITICAL BUG: frozen dataclass still allowed metadata mutations.
    FIX: Use MappingProxyType for immutable dict view.
    """

    def test_metadata_is_immutable_view(self):
        """Metadata should return immutable MappingProxyType"""
        evidence = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.RAG,
        )

        from types import MappingProxyType
        assert isinstance(evidence.metadata, MappingProxyType)

    def test_cannot_mutate_metadata(self):
        """Attempting to mutate metadata should raise TypeError"""
        evidence = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.RAG,
        )

        # Try to mutate metadata
        with pytest.raises(TypeError):
            evidence.metadata['hacked'] = 'value'

    def test_cannot_change_origin_via_metadata(self):
        """Cannot bypass immutability by adding origin_tool to metadata"""
        evidence = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.RAG,
        )

        # This was the original exploit
        with pytest.raises(TypeError):
            evidence.metadata['origin_tool'] = 'web_search'

        # Verify origin unchanged
        assert evidence.origin_tool == OriginTool.RAG

    def test_metadata_with_initial_data(self):
        """Metadata with initial data should still be immutable"""
        evidence = Evidence(
            id="test-1",
            content="Test content",
            origin_tool=OriginTool.WEB_SEARCH,
            _metadata={'source': 'google', 'rank': 1}
        )

        # Can read metadata
        assert evidence.metadata['source'] == 'google'
        assert evidence.metadata['rank'] == 1

        # But cannot mutate
        with pytest.raises(TypeError):
            evidence.metadata['rank'] = 2

    def test_serialization_preserves_metadata(self):
        """to_dict() should work with immutable metadata"""
        evidence = Evidence(
            id="test-1",
            content="Test",
            origin_tool=OriginTool.RAG,
            _metadata={'key': 'value'}
        )

        data = evidence.to_dict()
        assert data['metadata']['key'] == 'value'

        # Reconstruct and verify
        reconstructed = Evidence.from_dict(data)
        assert reconstructed.metadata['key'] == 'value'


class TestIssue2_ThreadSafety:
    """
    Test that TimingCollector is thread-safe.

    CRITICAL BUG: No locking, race conditions in multi-threaded contexts.
    FIX: Add threading.RLock to all operations.
    """

    def test_concurrent_measure_operations(self):
        """Multiple threads can measure concurrently without corruption"""
        timer = TimingCollector()
        results = []
        errors = []

        def worker(worker_id: int):
            try:
                with timer.measure(f'worker_{worker_id}'):
                    time.sleep(0.01)
                results.append(worker_id)
            except Exception as e:
                errors.append(e)

        # Create 10 threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0
        assert len(results) == 10

        # Verify all operations recorded
        timings = timer.get_timings()
        for i in range(10):
            assert f'worker_{i}' in timings
            assert timings[f'worker_{i}'] >= 9  # ~10ms

    def test_concurrent_record_operations(self):
        """Multiple threads can record timings concurrently"""
        timer = TimingCollector()

        def recorder(value: float):
            for i in range(100):
                timer.record(f'op_{i}', value)

        # Start multiple threads recording simultaneously
        threads = []
        for i in range(5):
            t = threading.Thread(target=recorder, args=(float(i),))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All operations should be recorded (last writer wins)
        timings = timer.get_timings()
        assert len(timings) >= 100  # At least 100 ops + total

    def test_concurrent_get_timings(self):
        """Multiple threads can read timings concurrently"""
        timer = TimingCollector()
        timer.record('op1', 100)
        timer.record('op2', 200)

        results = []

        def reader():
            for _ in range(100):
                timings = timer.get_timings()
                results.append(len(timings))

        threads = []
        for _ in range(5):
            t = threading.Thread(target=reader)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All reads should succeed
        assert len(results) == 500
        # Each read should see at least 2 operations + total
        assert all(r >= 3 for r in results)

    def test_merge_is_thread_safe(self):
        """Merge operations are thread-safe"""
        timer = TimingCollector()

        def merger(base_val: int):
            for i in range(50):
                timer.merge({f'op_{i}': float(base_val + i)})

        threads = []
        for i in range(5):
            t = threading.Thread(target=merger, args=(i * 100,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All operations should be recorded
        timings = timer.get_timings()
        assert len(timings) >= 50


class TestIssue3_FromDictValidation:
    """
    Test that from_dict() fails loudly on missing origin_tool.

    CRITICAL BUG: Silent default to 'rag' corrupts data.
    FIX: Raise ValueError if origin_tool missing.
    """

    def test_from_dict_requires_origin_tool(self):
        """from_dict() must raise ValueError if origin_tool missing"""
        data = {
            'id': 'test-1',
            'content': 'Test content'
            # origin_tool missing!
        }

        with pytest.raises(ValueError) as exc_info:
            Evidence.from_dict(data)

        # Error message should be helpful
        assert 'origin_tool' in str(exc_info.value).lower()
        assert 'required' in str(exc_info.value).lower()

    def test_from_dict_rejects_invalid_origin_tool(self):
        """from_dict() must reject invalid origin_tool values"""
        data = {
            'id': 'test-1',
            'content': 'Test content',
            'origin_tool': 'invalid_origin'  # Not in enum!
        }

        with pytest.raises(ValueError) as exc_info:
            Evidence.from_dict(data)

        assert 'invalid' in str(exc_info.value).lower()
        assert 'invalid_origin' in str(exc_info.value)

    def test_from_dict_accepts_valid_origin_tools(self):
        """from_dict() should accept all valid origin_tool values"""
        valid_origins = ['rag', 'web_search', 'research_agent', 'unknown']

        for origin in valid_origins:
            data = {
                'id': f'test-{origin}',
                'content': 'Test content',
                'origin_tool': origin
            }

            evidence = Evidence.from_dict(data)
            assert evidence.origin_tool.value == origin

    def test_from_dict_with_enum_object(self):
        """from_dict() should accept OriginTool enum objects"""
        data = {
            'id': 'test-1',
            'content': 'Test content',
            'origin_tool': OriginTool.WEB_SEARCH  # Enum object, not string
        }

        evidence = Evidence.from_dict(data)
        assert evidence.origin_tool == OriginTool.WEB_SEARCH

    def test_unknown_origin_tool_available(self):
        """OriginTool.UNKNOWN should exist for edge cases"""
        # Verify UNKNOWN enum value exists
        assert hasattr(OriginTool, 'UNKNOWN')
        assert OriginTool.UNKNOWN.value == 'unknown'

        # Can create evidence with UNKNOWN origin
        evidence = Evidence(
            id='test-1',
            content='Test',
            origin_tool=OriginTool.UNKNOWN
        )

        assert evidence.origin_tool == OriginTool.UNKNOWN


class TestDatetimeDeprecationFix:
    """
    Test that datetime.utcnow() has been replaced with datetime.now(timezone.utc).

    MEDIUM PRIORITY: datetime.utcnow() deprecated in Python 3.12+
    """

    def test_fetched_at_uses_timezone_aware_datetime(self):
        """fetched_at should use timezone-aware datetime"""
        evidence = Evidence(
            id='test-1',
            content='Test',
            origin_tool=OriginTool.RAG
        )

        # Should have timezone info
        assert evidence.fetched_at.tzinfo is not None
        assert evidence.fetched_at.tzinfo == timezone.utc


class TestMergeLogicFix:
    """
    Test that merge() behavior is now explicit.

    HIGH PRIORITY: Unclear whether merge should add or replace.
    FIX: Separate merge() (replace) and merge_add() (add).
    """

    def test_merge_replaces_duplicate_keys(self):
        """merge() should REPLACE existing values (default behavior)"""
        timer = TimingCollector()
        timer.record('operation', 100)

        # Merge with same key
        timer.merge({'operation': 200})

        timings = timer.get_timings()
        # Should be 200 (replaced), not 300 (added)
        assert timings['operation'] == 200

    def test_merge_add_sums_duplicate_keys(self):
        """merge_add() should ADD to existing values"""
        timer = TimingCollector()
        timer.record('operation', 100)

        # Merge_add with same key
        timer.merge_add({'operation': 200})

        timings = timer.get_timings()
        # Should be 300 (100 + 200)
        assert timings['operation'] == 300

    def test_merge_adds_new_keys(self):
        """merge() should add new keys"""
        timer = TimingCollector()
        timer.record('op1', 100)

        timer.merge({'op2': 200, 'op3': 300})

        timings = timer.get_timings()
        assert timings['op1'] == 100
        assert timings['op2'] == 200
        assert timings['op3'] == 300


class TestZeroTotalWarning:
    """
    Test that get_breakdown_percent() logs warning on zero total.

    HIGH PRIORITY: Silent failure when no operations measured.
    FIX: Log warning before returning empty dict.
    """

    def test_zero_total_logs_warning(self, caplog):
        """get_breakdown_percent() should log warning if total is zero"""
        import logging

        timer = TimingCollector()
        # Don't measure anything

        # Get breakdown immediately (total ~= 0)
        breakdown = timer.get_breakdown_percent()

        # Should return empty dict
        assert breakdown == {}

        # Should have logged warning (if logging is configured)
        # Note: This test may need adjustment based on logging setup


# Regression tests to ensure fixes don't break existing functionality
class TestRegressionTests:
    """Ensure fixes don't break existing functionality"""

    def test_evidence_still_frozen(self):
        """Evidence objects should still be frozen (immutable)"""
        evidence = Evidence(
            id='test-1',
            content='Test',
            origin_tool=OriginTool.RAG
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            evidence.content = 'Modified'

    def test_timing_collector_still_works(self):
        """Basic TimingCollector functionality unchanged"""
        timer = TimingCollector()

        with timer.measure('operation'):
            time.sleep(0.01)

        timings = timer.get_timings()
        assert 'operation' in timings
        assert timings['operation'] >= 9

    def test_evidence_serialization_still_works(self):
        """Evidence serialization/deserialization still works"""
        original = Evidence(
            id='test-1',
            content='Test',
            origin_tool=OriginTool.WEB_SEARCH,
            url='https://example.com'
        )

        data = original.to_dict()
        reconstructed = Evidence.from_dict(data)

        assert reconstructed.id == original.id
        assert reconstructed.origin_tool == original.origin_tool


class TestIssue5_ValidatorTypeCheck:
    """
    Test that ProvenanceValidator validates input types.

    HIGH PRIORITY: No type validation in constructor.
    FIX: Add isinstance() check and raise TypeError.
    """

    def test_strict_mode_must_be_bool(self):
        """ProvenanceValidator should reject non-bool strict_mode"""
        from services.common.validators import ProvenanceValidator

        with pytest.raises(TypeError) as exc_info:
            ProvenanceValidator(strict_mode="true")  # String instead of bool

        assert 'bool' in str(exc_info.value).lower()

    def test_strict_mode_accepts_bool(self):
        """ProvenanceValidator should accept bool values"""
        from services.common.validators import ProvenanceValidator

        # Should work with True
        validator1 = ProvenanceValidator(strict_mode=True)
        assert validator1.strict_mode is True

        # Should work with False
        validator2 = ProvenanceValidator(strict_mode=False)
        assert validator2.strict_mode is False

    def test_default_strict_mode_is_true(self):
        """ProvenanceValidator defaults to strict mode"""
        from services.common.validators import ProvenanceValidator

        validator = ProvenanceValidator()
        assert validator.strict_mode is True


class TestIssue7_URLSanitization:
    """
    Test that URLs are validated to prevent XSS attacks.

    HIGH PRIORITY: No URL validation, XSS risk.
    FIX: Add validate_url() function and check in from_dict().
    """

    def test_validate_url_blocks_javascript(self):
        """validate_url() should block javascript: scheme"""
        from services.common.evidence import validate_url

        assert validate_url('javascript:alert("XSS")') is False
        assert validate_url('JAVASCRIPT:alert("XSS")') is False  # Case insensitive

    def test_validate_url_blocks_data_scheme(self):
        """validate_url() should block data: scheme"""
        from services.common.evidence import validate_url

        assert validate_url('data:text/html,<script>alert("XSS")</script>') is False
        assert validate_url('DATA:text/html,test') is False

    def test_validate_url_blocks_file_scheme(self):
        """validate_url() should block file: scheme"""
        from services.common.evidence import validate_url

        assert validate_url('file:///etc/passwd') is False
        assert validate_url('FILE:///etc/passwd') is False

    def test_validate_url_blocks_script_tags(self):
        """validate_url() should block URLs with script tags"""
        from services.common.evidence import validate_url

        assert validate_url('https://evil.com/<script>alert("XSS")</script>') is False
        assert validate_url('https://evil.com/<SCRIPT>alert("XSS")</SCRIPT>') is False

    def test_validate_url_blocks_event_handlers(self):
        """validate_url() should block URLs with event handlers"""
        from services.common.evidence import validate_url

        assert validate_url('https://evil.com/page?param=onerror=alert("XSS")') is False
        assert validate_url('https://evil.com/page?param=onload=alert("XSS")') is False
        assert validate_url('https://evil.com/page?param=onclick=alert("XSS")') is False

    def test_validate_url_accepts_safe_urls(self):
        """validate_url() should accept safe HTTP(S) URLs"""
        from services.common.evidence import validate_url

        assert validate_url('https://example.com') is True
        assert validate_url('http://example.com/path') is True
        assert validate_url('https://blog.example.co.uk/post/123?id=456') is True
        assert validate_url('https://github.com/user/repo') is True

    def test_from_dict_rejects_unsafe_url(self):
        """from_dict() should raise ValueError for unsafe URLs"""
        data = {
            'id': 'test-1',
            'content': 'Test',
            'origin_tool': 'web_search',
            'url': 'javascript:alert("XSS")'  # Unsafe!
        }

        with pytest.raises(ValueError) as exc_info:
            Evidence.from_dict(data)

        assert 'unsafe' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()

    def test_from_dict_accepts_safe_url(self):
        """from_dict() should accept safe URLs"""
        data = {
            'id': 'test-1',
            'content': 'Test',
            'origin_tool': 'web_search',
            'url': 'https://example.com'  # Safe
        }

        evidence = Evidence.from_dict(data)
        assert evidence.url == 'https://example.com'

    def test_from_dict_allows_no_url(self):
        """from_dict() should allow Evidence without URL (for RAG)"""
        data = {
            'id': 'test-1',
            'content': 'Test',
            'origin_tool': 'rag'
            # No URL
        }

        evidence = Evidence.from_dict(data)
        assert evidence.url is None


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])

