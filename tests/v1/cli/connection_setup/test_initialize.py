"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_initialize.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._expectations import (
    _ALL_IDS,
    _CANCEL_IDS,
    _CAPABILITY_GATED_IDS,
    _CAPABILITY_IDS,
    _INFORMATIONAL_IDS,
    _MANDATORY_IDS,
    _SUBAGENT_ADVISORY_IDS,
)
from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def test_exits_immediately_fails_gracefully():
    result = _run_cli("exits_immediately.py")
    assert result.returncode != 0
    assert "INTERNALERROR" not in result.stdout
    assert "INTERNALERROR" not in result.stderr
    statuses = _table_statuses(result.stdout)
    for req_id in _MANDATORY_IDS:
        assert statuses.get(req_id) == "FAIL", f"{req_id} should FAIL when the agent never responds"
    # ACP-AUTH-003 is CAPABILITY-tier, not MANDATORY, so the loop above doesn't cover it --
    # assert its SKIP explicitly: it's conditional on --tck-auth-method regardless of the
    # agent's own behavior, and SKIPs even against a dead agent since the TCK never attempts
    # to connect for it without a configured auth method.
    assert statuses.get("ACP-AUTH-003") == "SKIPPED", "ACP-AUTH-003 should SKIP without --auth-method"


def test_version_mismatch_errors_fails_init_003_only():
    result = _run_cli("version_mismatch_errors.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-INIT-003") == "FAIL", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - {"ACP-INIT-003"} - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"


def test_v2_only_agent_under_protocol_version_1_is_blocked_by_version_mismatch():
    """`v2_only_honest.py` (`tests/fixtures/agents/v2/`) always answers `initialize` with
    `protocolVersion: 2`, regardless of what a v1 client requests -- the mirror image
    of v2's `test_v1_conforming_agent_under_protocol_version_2_is_blocked_by_
    version_mismatch`. `_tck_capability_gate` (`tck.common.plugin`) is version-agnostic: it fires
    whenever the negotiated `protocolVersion` does not equal this run's own, in either
    direction, so every `CAPABILITY`-tier id here SKIPs with the `VERSION-MISMATCH:` marker
    and zero CAPABILITY FAILs occur -- proving `Verdict.blocked_by_version_mismatch` itself is
    symmetric, not "always `False` for a v1 run".

    v1's own MANDATORY/ADVISORY tests that judge a result's *shape* against v1's rules
    (`ACP-INIT-002`/`004`, `ACP-ERROR-003`..`008`, `ACP-META-001`, `ACP-PROMPT-001`/`003`/`004`,
    `ACP-SCHEMA-001`/`002`, `ACP-SESSION-003`/`004`/`006`) call their
    own `skip_if_version_mismatch` twin (`tck.v1.conformance._helpers`) right after obtaining
    the `initialize` result, mirroring v2's `test_initialize.py`/`test_batch.py`/
    `test_transport.py` pattern -- so they SKIP with the `VERSION-MISMATCH:` marker here too,
    exactly like the CAPABILITY-tier ids, and the run has zero FAILs despite being blocked."""
    result = _run_cli(
        "v2_only_honest.py", fixture_dir=FIXTURES_DIR_V2, protocol_version=1
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "blocked by version mismatch" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    for req_id in _CAPABILITY_IDS | {
        "ACP-INIT-002",
        "ACP-INIT-004",
        "ACP-ERROR-003",
        "ACP-ERROR-004",
        "ACP-ERROR-005",
        "ACP-ERROR-006",
        "ACP-ERROR-007",
        "ACP-ERROR-008",
        "ACP-META-001",
        "ACP-PROMPT-001",
        "ACP-PROMPT-003",
        "ACP-PROMPT-004",
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-SESSION-003",
        "ACP-SESSION-004",
        "ACP-SESSION-006",
        "ACP-LIST-003",
        "ACP-AUTH-008",
        "ACP-PLAN-002",
        "ACP-PLAN-003",
        "ACP-PLAN-004",
        "ACP-PERM-001",
        "ACP-PERM-002",
    } | _SUBAGENT_ADVISORY_IDS:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"


def test_v2_only_agent_rejecting_v1_with_32022_is_blocked_by_version_mismatch(tmp_path):
    """A spec-conforming v2-only agent (`tests/fixtures/agents/v2/conforming.py`) rejects the v1
    `initialize` with `-32022` and leaves the connection uninitialized, so no v1 requirement --
    including the `ACP-INIT-*` negotiation rows, whose v1 rule ("respond with the latest version
    it supports") the v2 draft supersedes for agents implementing v2 -- can be judged. Every id
    SKIPs with the `VERSION-MISMATCH:` marker (`tck.common.plugin`'s version-rejection gate) and
    the run is blocked, not a wall of FAILs."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "conforming.py", fixture_dir=FIXTURES_DIR_V2, protocol_version=1, report_json=str(report_path)
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "VERDICT: NOT CONFORMANT (blocked by version mismatch)" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _ALL_IDS <= set(statuses), result.stdout
    assert set(statuses.values()) == {"SKIPPED"}, result.stdout

    report = json.loads(report_path.read_text())
    assert report["verdict"]["blocked_by_version_mismatch"] is True, report["verdict"]
    for requirement in report["requirements"]:
        assert all("-32022" in t["message"] and "VERSION-MISMATCH:" in t["message"] for t in requirement["tests"]), requirement


def test_router_requires_info_passes_everything():
    """`router_requires_info.py` models a dual-version protocol *router*: it selects v2 for any
    requested version >= 2, including the ACP-INIT-003 probe's 65535, and validates the params
    as a v2 `InitializeRequest`, whose `info` is REQUIRED. Since the probe carries `info`,
    ACP-INIT-003 PASSes; the fixture is otherwise identical to `conforming.py` (advertises
    `agentCapabilities: {}`, no modes/configOptions/authMethods), so the same SKIP/PASS split
    applies."""
    result = _run_cli("router_requires_info.py")
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS | _INFORMATIONAL_IDS, (
        f"requirement table missing/extra ids: {result.stdout}"
    )
    skip_ids = _CANCEL_IDS | _CAPABILITY_GATED_IDS
    for req_id in skip_ids:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised/unadvertised):\n{result.stdout}"
    for req_id, status in statuses.items():
        if req_id in skip_ids:
            continue
        assert status == "PASS", f"{req_id} is {status}, expected PASS for router_requires_info.py:\n{result.stdout}"
    assert "NOT TESTED" not in result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_echoes_any_version_fails_init_003_only():
    """`echoes_any_version.py` echoes the client's requested `protocolVersion` verbatim for
    *every* request, including the unsupported 65535 one -- the pattern ACP-INIT-003 exists to
    catch (see `test_initialize.py`). ACP-INIT-002 still PASSes (a v1 request is correctly
    echoed 1)."""
    result = _run_cli("echoes_any_version.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-INIT-003") == "FAIL", result.stdout
    assert statuses.get("ACP-INIT-002") == "PASS", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - {"ACP-INIT-003"} - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"


def test_result_and_error_fails_init_001_and_schema_001():
    """`result_and_error.py`'s `initialize` response carries both `result` and `error`, which
    also fails ACP-JSONRPC-002 (that requirement's evidence includes the `initialize` response
    itself, not just a probe reply) in addition to ACP-INIT-001 and ACP-SCHEMA-001."""
    result = _run_cli("result_and_error.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-INIT-001") == "FAIL", result.stdout
    assert statuses.get("ACP-SCHEMA-001") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-002") == "FAIL", result.stdout
    _failing = {"ACP-INIT-001", "ACP-SCHEMA-001", "ACP-JSONRPC-002"}
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - _failing - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"
