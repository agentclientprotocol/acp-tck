"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_permissions.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._expectations import _CANCEL_IDS, _MANDATORY_IDS
from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_asks_permission_agent_passes_everything():
    """`asks_permission.py` sends `session/request_permission` before resolving every prompt --
    the mock client (`run_prompt`) must answer it for any prompt/transport/schema test to ever
    resolve at all."""
    result = _run_cli("asks_permission.py")
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} is {statuses.get(req_id)}, expected PASS:\n{result.stdout}"


def test_honors_permission_agent_passes_both_permission_probes():
    """`honors_permission.py` asks permission for the probe file and creates it only after
    `allow-once`: the TCK's `reject_once` and unknown-option answers both leave no file."""
    result = _run_cli("honors_permission.py", timeout="5", k="permission or reject or unrecognised")
    assert result.returncode != 0  # scoped run: other ids are NOT_TESTED
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-PERM-001") == "PASS", result.stdout
    assert statuses.get("ACP-PERM-002") == "PASS", result.stdout


def test_agent_without_a_reject_option_skips_perm_001_and_never_fails():
    """`perm_without_reject_option.py` offers only allow options: the TCK cancels the turn rather
    than select one, so ACP-PERM-001 SKIPs and nothing FAILs."""
    result = _run_cli("perm_without_reject_option.py", timeout="5", k="permission or reject or unrecognised")
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-PERM-001") == "SKIPPED", result.stdout
    assert statuses.get("ACP-PERM-002") == "PASS", result.stdout
    assert _output_fail_ids(result.stdout) == set(), result.stdout


def test_only_reject_always_offered_is_never_selected(tmp_path):
    """`perm_only_reject_always.py` offers only `reject_always` on every prompt. The default
    `allow` policy cancels the turn and answers `cancelled` instead of selecting it (recorded as
    the fallback note); ACP-PERM-001 SKIPs and nothing FAILs within this scope. (`test_errors` is
    left out: the `asks_permission.py` base ignores unknown session ids, an ACP-ERROR-003 FAIL
    of its own.)"""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "perm_only_reject_always.py",
        timeout="5",
        k="(permission or reject or unrecognised or test_prompt or cancel) and not test_errors",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    assert statuses.get("ACP-PERM-001") == "SKIPPED", result.stdout
    assert statuses.get("ACP-PROMPT-001") == "PASS", result.stdout
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    notes = {test["properties"].get("acp_tck_permission_fallback") for test in by_id["ACP-PROMPT-001"]["tests"]}
    assert notes == {"agent offered no allow_once, allow_always or reject_once option"}, notes


def test_perm_ignores_reject_fails_both_permission_ids_advisory_only():
    """`perm_ignores_reject.py` creates the file whatever the client answered -- two ADVISORY
    FAILs, so the run stays CONFORMANT."""
    result = _run_cli("perm_ignores_reject.py", timeout="5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert _output_fail_ids(result.stdout) == {"ACP-PERM-001", "ACP-PERM-002"}, result.stdout


def test_perm_unknown_option_is_approval_fails_perm_002_advisory_only():
    """`perm_unknown_option_is_approval.py` honours `reject_once` but approves on an unknown
    `optionId` -- only ACP-PERM-002 FAILs (ADVISORY)."""
    result = _run_cli("perm_unknown_option_is_approval.py", timeout="5")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert _output_fail_ids(result.stdout) == {"ACP-PERM-002"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-PERM-001") == "PASS", result.stdout
