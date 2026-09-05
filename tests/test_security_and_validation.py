"""
Security and Input Validation Tests for Who Icd11 Multilingual Auto Coder.
Tests for path traversal protection, input validation, audit integrity, and PHI guard.
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import AuditTrail, PHIGuard, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel


class TestPathTraversalProtection:
    """Test that batch file I/O cannot escape the working directory."""

    def test_safe_path_allows_subdirectory(self, tmp_path, monkeypatch):
        """Paths within the working directory should be allowed."""
        monkeypatch.chdir(tmp_path)
        from cli import _safe_resolve_path
        result = _safe_resolve_path("subdir/file.csv")
        assert result == (tmp_path / "subdir" / "file.csv").resolve()

    def test_safe_path_blocks_traversal(self, tmp_path, monkeypatch):
        """Paths resolving outside the working directory should be blocked."""
        monkeypatch.chdir(tmp_path)
        from cli import _safe_resolve_path
        with pytest.raises(ValueError, match="path traversal blocked"):
            _safe_resolve_path("../../etc/passwd")

    def test_safe_path_blocks_absolute_outside(self, tmp_path, monkeypatch):
        """Absolute paths outside cwd should be blocked."""
        monkeypatch.chdir(tmp_path)
        from cli import _safe_resolve_path
        with pytest.raises(ValueError, match="path traversal blocked"):
            _safe_resolve_path("/etc/passwd" if os.name != "nt" else "C:/Windows/system32/config/sam")

    def test_safe_path_requires_existent_input(self, tmp_path, monkeypatch):
        """Input files must exist when must_exist=True."""
        monkeypatch.chdir(tmp_path)
        from cli import _safe_resolve_path
        with pytest.raises(FileNotFoundError):
            _safe_resolve_path("nonexistent.csv", must_exist=True)


class TestInputValidation:
    """Test that input field length limits are enforced."""

    def test_task_id_too_long(self):
        """Task IDs exceeding 128 characters should be rejected."""
        with pytest.raises(Exception):  # ValidationError
            SystemTaskPayload(task_id="T" * 129, target_identifier="OK", primary_metric=10.0)

    def test_target_identifier_too_long(self):
        """Target identifiers exceeding 128 characters should be rejected."""
        with pytest.raises(Exception):
            SystemTaskPayload(task_id="OK", target_identifier="X" * 129, primary_metric=10.0)

    def test_status_descriptor_too_long(self):
        """Status descriptors exceeding 64 characters should be rejected."""
        with pytest.raises(Exception):
            SystemTaskPayload(task_id="OK", target_identifier="OK", primary_metric=10.0,
                              status_descriptor="D" * 65)

    def test_valid_input_passes(self):
        """Normal inputs within bounds should be accepted."""
        p = SystemTaskPayload(task_id="TASK-001", target_identifier="TARGET-01",
                              primary_metric=15.0, secondary_metric=5.0,
                              status_descriptor="NOMINAL")
        assert p.task_id == "TASK-001"
        assert len(p.task_id) < 128


class TestAuditIntegrity:
    """Test HMAC-SHA256 audit trail integrity verification."""

    def test_audit_trail_verifies_chain(self):
        """Audit trail with valid entries should pass integrity check."""
        trail = AuditTrail(secret_key="test-secret-key")
        trail.log("actor1", "supervisor", "TEST_EVENT", {"key": "value"})
        trail.log("actor2", "worker", "ANOTHER_EVENT", {"data": 123})
        assert trail.verify_integrity() is True

    def test_audit_trail_detects_tampering(self):
        """Tampered audit trail should fail integrity check."""
        trail = AuditTrail(secret_key="test-secret-key")
        trail.log("actor1", "supervisor", "TEST_EVENT", {"key": "value"})
        trail.log("actor2", "worker", "ANOTHER_EVENT", {"data": 123})
        # Tamper with an entry
        trail.logs[0]["payload_hash"] = "tampered_hash"
        assert trail.verify_integrity() is False

    def test_audit_trail_detects_chain_break(self):
        """Broken chain linkage should fail integrity check."""
        trail = AuditTrail(secret_key="test-secret-key")
        trail.log("actor1", "supervisor", "TEST_EVENT", {"key": "value"})
        trail.log("actor2", "worker", "ANOTHER_EVENT", {"data": 123})
        # Break the chain
        trail.logs[1]["prev_hash"] = "broken_link"
        assert trail.verify_integrity() is False

    def test_empty_trail_is_valid(self):
        """Empty audit trail should pass integrity check."""
        trail = AuditTrail(secret_key="test-secret-key")
        assert trail.verify_integrity() is True


class TestPHIGuard:
    """Test PHI outbound guard patterns."""

    def test_blocks_mrn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_blocks_ssn(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_blocks_phone(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call 555-123-4567")

    def test_blocks_email(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_blocks_dob(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_blocks_patient_name(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_allows_clean_text(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Task evaluation completed with status NOMINAL")

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Contact patient at 555-123-4567 or MRN-12345")
        assert "555-123-4567" not in result
        assert "MRN-12345" not in result
        assert "[REDACTED_IDENTIFIER]" in result
