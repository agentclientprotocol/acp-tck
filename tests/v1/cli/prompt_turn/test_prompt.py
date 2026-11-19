"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_prompt.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._expectations import _CANCEL_IDS, _MANDATORY_IDS
from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_bad_stop_reason_fails_prompt_001_003_and_schema_001_only():
    """`bad_stop_reason.py` replies `stopReason: "done"` for any non-`__hang__` prompt, which
    directly breaks ACP-PROMPT-001, ACP-PROMPT-003 (the resource_link prompt also needs a valid
    `stopReason`), and ACP-SCHEMA-001. It does *not* hang for the cancel tests'
    prompt text either (only `__hang__` triggers that), so `session/cancel` always loses the
    race against its immediate (if invalid) reply -- ACP-CANCEL-001/002 SKIP as "cancellation
    not exercised" rather than cascading into a FAIL."""
    result = _run_cli("bad_stop_reason.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    expected_fails = {"ACP-PROMPT-001", "ACP-PROMPT-003", "ACP-SCHEMA-001"}
    for req_id in expected_fails:
        assert statuses.get(req_id) == "FAIL", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - expected_fails - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"


def test_update_wrong_session_fails_prompt_002_only():
    """`update_wrong_session.py` always attributes `session/update` to `sessionId: "other"`.
    ACP-PROMPT-001/PROMPT-003 only check the response, not update attribution, so they still
    PASS; ACP-PROMPT-002 (which does check it) FAILs. It doesn't hang for the cancel tests'
    prompt text, so `session/cancel` always loses the race and ACP-CANCEL-001/002 SKIP as
    "cancellation not exercised" -- an unexercised cancel can't exercise ACP-CANCEL-002's
    ordering check either, so the wrong-sessionId update it would otherwise have caught there
    goes unreported by that particular test (ACP-PROMPT-002 still reports it)."""
    result = _run_cli("update_wrong_session.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    expected_fails = {"ACP-PROMPT-002"}
    for req_id in expected_fails:
        assert statuses.get(req_id) == "FAIL", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - expected_fails - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"


def test_relative_tool_call_path_fails_prompt_004_only():
    result = _run_cli("relative_tool_call_path.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-PROMPT-004"}, result.stdout
