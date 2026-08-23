import pytest
from app.services.job_manager import JobManager


def test_valid_transitions():
    assert JobManager.can_transition("UPLOADED", "VALIDATING")
    assert JobManager.can_transition("VALIDATING", "PROCESSING")
    assert JobManager.can_transition("PROCESSING", "READY")
    assert JobManager.can_transition("READY", "PREVIEW")
    assert JobManager.can_transition("PREVIEW", "CONFIRMED")
    assert JobManager.can_transition("CONFIRMED", "PRINTING")
    assert JobManager.can_transition("PRINTING", "COMPLETED")


def test_invalid_transitions():
    assert not JobManager.can_transition("UPLOADED", "COMPLETED")
    assert not JobManager.can_transition("COMPLETED", "UPLOADED")
    assert not JobManager.can_transition("READY", "PRINTING")


def test_failure_transitions():
    assert JobManager.can_transition("PROCESSING", "FAILED")
    assert JobManager.can_transition("FAILED", "UPLOADED")
    assert JobManager.can_transition("FAILED", "MANUAL_REVIEW")
