"""Regression coverage for input safety, truthful browser output, and batch integrity."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.api import app
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from cli import main


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_metrics_rejected(bad):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="TEST", target_identifier="DEMO", primary_metric=bad)


@pytest.mark.parametrize("key", ["task_id", "target_identifier"])
def test_empty_identifiers_rejected(key):
    values = {"task_id": "T", "target_identifier": "K", "primary_metric": 1.0}
    values[key] = ""
    with pytest.raises(ValidationError):
        SystemTaskPayload(**values)


def test_phi_in_free_form_metadata_blocked():
    payload = SystemTaskPayload(
        task_id="SYNTHETIC", target_identifier="DEMO", primary_metric=1.0,
        attributes={"metadata": "Patient MRN-123456"},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_audit_trail_returns_defensive_snapshot():
    trail = AuditTrail(secret_key="synthetic-test-secret")
    trail.log("agent", "worker", "TEST_EVENT", {"synthetic": True})
    snapshot = trail.get_trail()
    snapshot[0]["current_hash"] = "modified"
    assert trail.verify_integrity()
    assert trail.get_trail()[0]["current_hash"] != "modified"


def test_bad_api_payload_returns_validation_error():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "DEMO", "target_identifier": "SYNTHETIC",
        "primary_metric": 2.0, "attributes": {"note": "MRN-123456"},
    })
    assert response.status_code == 422
    assert "personal identifier" in response.json()["detail"].lower()


def test_api_key_authentication_when_configured(monkeypatch):
    monkeypatch.setenv("AUDIT_API_KEY", "synthetic-secret")
    client = TestClient(app)
    assert client.get("/api/audit/logs").status_code == 401
    assert client.get("/api/audit/logs", headers={"X-API-Key": "invalid"}).status_code == 401
    assert client.get("/api/audit/logs", headers={"X-API-Key": "synthetic-secret"}).status_code == 200


def test_batch_rejects_overwriting_input(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    csv_file = Path("test.csv")
    original = "task_id,target_identifier,primary_metric\nONE,DEMO,2\n"
    csv_file.write_text(original, encoding="utf8")
    assert main(["batch", "-i", "test.csv", "-o", "test.csv"]) == 1
    assert csv_file.read_text(encoding="utf8") == original


def test_batch_requires_schema(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("test.csv").write_text("x,y\n1,2\n", encoding="utf8")
    assert main(["batch", "-i", "test.csv", "-o", "result.csv"]) == 1
    assert not Path("result.csv").exists()


def test_browser_preview_never_fabricates_hmac_or_icd_codes():
    html = (Path(__file__).resolve().parents[1] / "web" / "index.html").read_text("utf8")
    assert "LOCAL_THRESHOLD_PREVIEW_NOT_ICD11_CODING" in html
    assert "HMAC_SHA256_e83f9" not in html
    assert "fetch('/api/audit'" not in html
