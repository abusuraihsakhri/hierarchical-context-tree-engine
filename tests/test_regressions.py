"""Regression coverage for integrity, pruning, caching, and the static interface."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import re

import pytest

os.environ.setdefault("AUDIT_SECRET_KEY", "test-suite-audit-key-2026")

from agents.base import AuditTrail, SecurityException
from agents.llm_factory import MockLLM
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from context_tree.pruning import AgePruner, CompositePruner, DepthPruner
from context_tree.subtree_cache import SubtreeCache


def test_audit_detects_signature_or_metadata_tampering():
    audit = AuditTrail("long-test-audit-secret-key")
    audit.log("actor", "tier", "CREATED", {"record": "one"})
    audit.log("actor", "tier", "UPDATED", {"record": "two"})
    assert audit.verify_integrity()
    audit.logs[-1]["event_type"] = "FORGED"
    assert not audit.verify_integrity()
    audit.logs[-1]["event_type"] = "UPDATED"
    assert audit.verify_integrity()
    audit.logs[-1]["current_hash"] = "f" * 64
    assert not audit.verify_integrity()


def test_audit_accessors_cannot_mutate_internal_ledger():
    audit = AuditTrail("long-test-audit-secret-key")
    result = audit.log("actor", "tier", "EVENT", {"record": 1})
    result["event_type"] = "FORGED"
    retrieved = audit.get_trail()
    retrieved[0]["current_hash"] = "forged"
    assert audit.verify_integrity()
    assert audit.get_trail()[0]["event_type"] == "EVENT"


def test_phi_guard_inspects_nested_payload_attributes():
    supervisor = SystemSupervisor()
    payload = SystemTaskPayload(
        task_id="T-1", target_identifier="K-1", primary_metric=12,
        attributes={"nested": {"email": "patient@example.com"}},
    )
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_cache_overwrite_does_not_evict_other_entries():
    cache = SubtreeCache(max_size=2)
    cache.put("a", {"data": 1})
    cache.put("b", {"data": 2})
    cache.put("a", {"data": 3})
    assert cache.get("a") == {"data": 3}
    assert cache.get("b") == {"data": 2}


def test_cache_defensive_copies_and_zero_ttl():
    cache = SubtreeCache(max_size=1)
    original = {"children": [1]}
    cache.put("a", original)
    original["children"].append(2)
    observed = cache.get("a")
    assert observed == {"children": [1]}
    observed["children"].append(9)
    assert cache.get("a") == {"children": [1]}
    cache.put("a", {"children": []}, ttl=0)
    assert cache.get("a") is None


def test_pruning_does_not_discard_undated_nodes_or_mutate_input():
    assert not AgePruner().should_prune({"node_id": "new"}, {"current_time": 1000})
    original = {
        "node_id": "root", "depth": 0,
        "children": [{"node_id": "too-deep", "depth": 5, "children": []}],
    }
    result = CompositePruner([DepthPruner(max_depth=2)]).prune_tree(original)
    assert result["children"] == []
    assert len(original["children"]) == 1


def test_mock_never_claims_scientific_verification():
    response = MockLLM().invoke("What is the state?")
    assert "No external model was called" in response
    assert "no independent verification" in response


def test_browser_script_is_valid_and_evaluates_locally():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is unavailable")
    html = (Path(__file__).resolve().parents[1] / "web/index.html").read_text()
    script = re.search(r"<script>([\s\S]*?)</script>", html)
    assert script, "Embedded app script not found"
    code = script.group(1)
    check = subprocess.run([node, "--check"], input=code, text=True, capture_output=True)
    assert check.returncode == 0, check.stderr

    harness = """
const vm = require("node:vm");
const assert = require("node:assert/strict");
const buttons = {};
const values = {
    task_id: "TEST-001", target_id: "KEY-001",
    primary_metric: "29.4", secondary_metric: "14.8",
    status_descriptor: "DISCORDANT_ANOMALY",
};
const controls = new Proxy({}, {
    get(store, id) {
        if (!store[id]) store[id] = {
            value: values[id] || "", checked: id === "is_critical",
            disabled: true, textContent: "",
            addEventListener(event, cb) { buttons[id + ":" + event] = cb; },
        };
        return store[id];
    }
});
vm.runInNewContext(SOURCE, {
    document: {getElementById(id) {return controls[id]}},
    Blob, URL, setTimeout,
});
buttons["run-button:click"]();
const result = JSON.parse(controls.outputConsole.textContent);
assert.equal(result.evaluation_mode, "LOCAL_UNSIGNED");
assert.equal(result.signed_audit_trail, false);
assert.equal(result.total_alerts, 3);
assert.equal(result.critical_alerts_count, 1);
assert.equal(controls["m-tasks"].textContent, "1");
assert.equal(controls["download-button"].disabled, false);
controls.primary_metric.value = "NaN";
buttons["run-button:click"]();
assert.match(controls.outputConsole.textContent, /Validation error/);
assert.equal(controls["m-tasks"].textContent, "1");
console.log("browser simulation passed");
"""
    check = subprocess.run(
        [node, "-e", "const SOURCE = " + json.dumps(code) + ";\n" + harness],
        capture_output=True, text=True,
    )
    assert check.returncode == 0, check.stderr
