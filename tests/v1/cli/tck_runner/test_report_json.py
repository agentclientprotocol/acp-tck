"""End-to-end tests of `acp-tck` itself: the `--report-json` report."""

from __future__ import annotations

import json

from .._expectations import _ALL_IDS, _CANCEL_IDS, _CAPABILITY_GATED_IDS
from .._runner import _run_cli


def test_report_json_for_conforming_agent_is_conformant_with_cancel_skipped(tmp_path):
    report_path = tmp_path / "report.json"
    result = _run_cli("conforming.py", report_json=str(report_path))
    assert result.returncode == 0, result.stdout + result.stderr

    report = json.loads(report_path.read_text())
    assert report["verdict"]["conformant"] is True
    by_id = {r["id"]: r for r in report["requirements"]}
    skip_ids = _CANCEL_IDS | _CAPABILITY_GATED_IDS
    for req_id in skip_ids:
        assert by_id[req_id]["status"] == "SKIPPED", report
    for req_id in _ALL_IDS - skip_ids:
        assert by_id[req_id]["status"] == "PASS", (req_id, report)
    assert report["protocol_version"] == 1
    assert report["agent_info"] is not None
    assert set(report) == {
        "tck_version",
        "protocol_version",
        "schema_revision",
        "agent_command",
        "agent_info",
        "agent_capabilities",
        "started_at",
        "finished_at",
        "requirements",
        "verdict",
    }


def test_report_json_for_advisory_only_failure_is_still_conformant(tmp_path):
    report_path = tmp_path / "report.json"
    result = _run_cli("unknown_method_no_error.py", report_json=str(report_path))
    assert result.returncode == 0, result.stdout + result.stderr

    report = json.loads(report_path.read_text())
    assert report["verdict"]["conformant"] is True
    by_id = {r["id"]: r for r in report["requirements"]}
    assert by_id["ACP-JSONRPC-004"]["status"] == "FAIL"


def test_report_json_for_banner_on_stdout_includes_a_nonempty_transcript_on_failure(tmp_path):
    report_path = tmp_path / "report.json"
    result = _run_cli("banner_on_stdout.py", report_json=str(report_path))
    assert result.returncode != 0

    report = json.loads(report_path.read_text())
    assert report["verdict"]["conformant"] is False
    by_id = {r["id"]: r for r in report["requirements"]}
    failing = by_id["ACP-TRANSPORT-001"]
    assert failing["status"] == "FAIL"
    test_outcome = failing["tests"][0]
    assert test_outcome["status"] == "FAIL"
    assert test_outcome["transcript"], "expected a non-empty transcript on a FAIL outcome"
    assert isinstance(test_outcome["transcript"], list)
    assert {"dir", "t", "raw"} <= set(test_outcome["transcript"][0])


def test_report_json_for_exits_immediately_has_no_crash_and_all_mandatory_fail_or_not_tested(
    tmp_path,
):
    report_path = tmp_path / "report.json"
    result = _run_cli("exits_immediately.py", report_json=str(report_path))
    assert result.returncode != 0
    assert "INTERNALERROR" not in result.stdout + result.stderr

    assert report_path.exists(), "report must still be written even when every test fails"
    report = json.loads(report_path.read_text())
    assert report["verdict"]["conformant"] is False
    for requirement in report["requirements"]:
        if requirement["id"] == "ACP-AUTH-003":
            # Conditional on --tck-auth-method regardless of the agent's own behavior -- see
            # test_exits_immediately_fails_gracefully.
            assert requirement["status"] == "SKIPPED", requirement
        elif requirement["tier"] == "MANDATORY":
            assert requirement["status"] in ("FAIL", "NOT_TESTED"), requirement
