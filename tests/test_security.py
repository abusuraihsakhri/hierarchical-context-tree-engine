"""
Security and input validation tests for Hierarchical Context Tree Engine.
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("AUDIT_SECRET_KEY", "test-suite-audit-key-2026")

import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel
from context_tree.pruning import DepthPruner, CompositePruner, create_pruner
from context_tree.subtree_cache import SubtreeCache


class TestPHIGuard:
    """Test PHI detection and redaction."""

    def test_detects_ssn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")

    def test_detects_mrn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("MRN-12345678 medical record")

    def test_detects_phone(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Contact: (555) 123-4567")

    def test_detects_email(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_allows_clean_text(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient John Doe, SSN: 123-45-6789")
        assert "123-45-6789" not in result
        assert "REDACTED_IDENTIFIER" in result

    def test_empty_string_safe(self):
        PHIGuard.assert_no_phi("")

    def test_none_safe(self):
        PHIGuard.assert_no_phi(None)


class TestAuditTrail:
    """Test HMAC-SHA256 audit trail security."""

    def test_requires_secret_key(self):
        # Remove env var to test requirement
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with pytest.raises(SecurityException):
                AuditTrail()
        finally:
            if original:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_rejects_short_key(self):
        with pytest.raises(SecurityException):
            AuditTrail(secret_key="short")

    def test_audit_chain_integrity(self):
        trail = AuditTrail(secret_key="test-key-for-integrity-verification")
        trail.log("test", "tier1", "EVENT_1", {"data": "value1"})
        trail.log("test", "tier1", "EVENT_2", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_not_empty(self):
        trail = AuditTrail(secret_key="test-key-for-empty-check")
        trail.log("test", "tier1", "EVENT_1", {"data": "value1"})
        assert len(trail.get_trail()) == 1

    def test_audit_blocks_are_chained(self):
        trail = AuditTrail(secret_key="test-key-for-chain-verification")
        entry1 = trail.log("test", "tier1", "EVENT_1", {"data": "value1"})
        entry2 = trail.log("test", "tier1", "EVENT_2", {"data": "value2"})
        assert entry2["prev_hash"] == entry1["current_hash"]

    def test_audit_blocks_differ(self):
        trail = AuditTrail(secret_key="test-key-for-diff-check")
        entry1 = trail.log("test", "tier1", "EVENT_1", {"data": "value1"})
        entry2 = trail.log("test", "tier1", "EVENT_2", {"data": "value2"})
        assert entry1["current_hash"] != entry2["current_hash"]


class TestInputValidation:
    """Test input validation and bounds checking."""

    def test_rejects_nan_metric(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("nan"))

    def test_rejects_inf_metric(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=float("inf"))

    def test_rejects_huge_metric(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(task_id="T1", target_identifier="K1", primary_metric=1e10)

    def test_rejects_path_traversal_task_id(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(task_id="../etc/passwd", target_identifier="K1", primary_metric=10.0)

    def test_rejects_null_byte_in_task_id(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(task_id="task\x00malicious", target_identifier="K1", primary_metric=10.0)

    def test_valid_payload(self):
        p = SystemTaskPayload(task_id="TASK-001", target_identifier="KEY-01", primary_metric=25.0)
        assert p.task_id == "TASK-001"
        assert p.primary_metric == 25.0

    def test_max_length_enforced(self):
        with pytest.raises(ValueError):
            SystemTaskPayload(task_id="x" * 300, target_identifier="K1", primary_metric=10.0)


class TestPruningStrategies:
    """Test tree pruning strategies."""

    def test_depth_pruner(self):
        pruner = DepthPruner(max_depth=5)
        assert pruner.should_prune({"depth": 10}, {}) is True
        assert pruner.should_prune({"depth": 3}, {}) is False

    def test_composite_pruner(self):
        pruner = CompositePruner([DepthPruner(max_depth=5)])
        assert pruner.should_prune({"depth": 10}, {}) is True
        assert pruner.should_prune({"depth": 3}, {}) is False

    def test_create_pruner_factory(self):
        pruner = create_pruner("depth", {"max_depth": 3})
        assert pruner.should_prune({"depth": 5}, {}) is True

    def test_create_pruner_invalid(self):
        with pytest.raises(ValueError):
            create_pruner("invalid_strategy")

    def test_prune_tree_recursive(self):
        pruner = CompositePruner([DepthPruner(max_depth=2)])
        tree = {
            "node_id": "root",
            "depth": 0,
            "children": [
                {"node_id": "child1", "depth": 1, "children": []},
                {"node_id": "child2", "depth": 3, "children": []},
            ]
        }
        result = pruner.prune_tree(tree)
        assert len(result["children"]) == 1
        assert result["children"][0]["node_id"] == "child1"


class TestSubtreeCache:
    """Test subtree caching mechanism."""

    def test_cache_put_and_get(self):
        cache = SubtreeCache(max_size=10)
        cache.put("key1", {"data": "value1"})
        assert cache.get("key1") == {"data": "value1"}

    def test_cache_miss(self):
        cache = SubtreeCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_cache_expiration(self):
        cache = SubtreeCache(max_size=10, default_ttl=0.01)
        cache.put("key1", {"data": "value1"})
        import time
        time.sleep(0.02)
        assert cache.get("key1") is None

    def test_cache_invalidation(self):
        cache = SubtreeCache(max_size=10)
        cache.put("key1", {"data": "value1"})
        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None

    def test_cache_clear(self):
        cache = SubtreeCache(max_size=10)
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})
        assert cache.clear() == 2
        assert cache.get("key1") is None

    def test_cache_metrics(self):
        cache = SubtreeCache(max_size=10)
        cache.put("key1", {"data": "value1"})
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        metrics = cache.metrics()
        assert metrics["total_hits"] == 1
        assert metrics["total_misses"] == 1

    def test_cache_eviction(self):
        cache = SubtreeCache(max_size=2)
        cache.put("key1", {"data": "value1"})
        cache.put("key2", {"data": "value2"})
        cache.put("key3", {"data": "value3"})
        # key1 should be evicted (LRU)
        assert cache.get("key1") is None
