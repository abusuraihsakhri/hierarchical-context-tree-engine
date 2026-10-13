"""HTTP regression tests for input rejection and restricted audit metadata."""
import os

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

os.environ.setdefault("AUDIT_SECRET_KEY", "test-suite-audit-key-2026")

from agents.api import app


def test_audit_logs_not_public(monkeypatch):
    monkeypatch.delenv("AUDIT_LOG_READ_KEY", raising=False)
    client = TestClient(app)
    assert client.get("/api/audit/logs").status_code == 403


def test_audit_logs_require_correct_key(monkeypatch):
    monkeypatch.setenv("AUDIT_LOG_READ_KEY", "read-key-for-test")
    client = TestClient(app)
    assert client.get("/api/audit/logs").status_code == 403
    assert client.get(
        "/api/audit/logs", headers={"X-Audit-Read-Key": "wrong"}
    ).status_code == 403
    response = client.get(
        "/api/audit/logs", headers={"X-Audit-Read-Key": "read-key-for-test"}
    )
    assert response.status_code == 200
    assert response.json()["verified"] is True


def test_sensitive_payload_rejected_without_server_error():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "TEST-01",
        "target_identifier": "KEY-01",
        "primary_metric": 1,
        "attributes": {"email": "patient@example.com"},
    })
    assert response.status_code == 422
    assert "patient@example.com" not in response.text
