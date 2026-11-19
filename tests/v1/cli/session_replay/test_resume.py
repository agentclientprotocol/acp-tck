"""End-to-end CLI tests for the `session/resume` rows of `src/tck/v1/conformance/test_session_capabilities.py`:
each runs fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _run_cli, _table_statuses


def test_resume_replays_history_fails_resume_002_only():
    """`resume_replays_history.py` advertises `sessionCapabilities.resume` but replays stored
    history before answering `session/resume`, which resume MUST NOT do -- ACP-RESUME-001 still
    PASSes, only ACP-RESUME-002 FAILs."""
    result = _run_cli("resume_replays_history.py", k="resume")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-RESUME-001") == "PASS", result.stdout
    assert statuses.get("ACP-RESUME-002") == "FAIL", result.stdout
