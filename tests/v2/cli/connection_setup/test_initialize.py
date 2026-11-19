"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_initialize.py`: each runs
fixture agents through `acp-tck` and checks the summary table.

Also covers the version-mismatch scenario (a v1 fixture run under `--protocol-version 2`).
`_VERSION_TOLERANT_IDS`, a strict superset of `_NEGOTIATION_IDS`: the eight connection-level
`ACP-JSONRPC-*`/`ACP-TRANSPORT-*` rows are judged identically for an honestly-negotiating v1 agent
forced under `--protocol-version 2`, since their own tests never drive a v2-shaped
`session/prompt` turn (see
`test_v1_conforming_agent_under_protocol_version_2_is_blocked_by_version_mismatch` below).
"""

from __future__ import annotations

import json

from .._expectations import (
    _ADVISORY_IDS,
    _ALL_IDS,
    _ALWAYS_SKIPPED_IDS,
    _CAPABILITY_IDS,
    _INFORMATIONAL_IDS,
    _MANDATORY_IDS,
)
from .._runner import FIXTURES_DIR_V1, FIXTURES_DIR_V2, _negotiation_fails, _run_cli, _table_statuses


def test_echoes_any_version_fails_init_003_only():
    """`echoes_any_version.py` echoes any requested `protocolVersion` above 2, including the
    `65535` probe -- fails `ACP-INIT-003` (must select its own highest version, not echo).
    `ACP-INIT-201` PASSes: its equality check only applies when the `65535` probe selects a
    version <= 2. It advertises `capabilities: {"session": {}}` like `conforming.py`, so
    `ACP-SESSION-001/002` PASS -- `session/new` itself is unmodified and correct."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "echoes_any_version.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-003"}, result.stdout
    assert statuses.get("ACP-INIT-201") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_only_errors_on_v1_fails_init_202_only():
    """`v2_only_errors_on_v1.py` answers `initialize(1)` with `-32602` instead of `-32022` --
    fails only `ACP-INIT-202` (1 is well-formed; `-32602` is reserved for a malformed
    `protocolVersion`). `ACP-INIT-205` still PASSes on its `protocolVersion: 0` probe. It
    advertises `capabilities: {"session": {}}` like `conforming.py`, so `ACP-SESSION-001/002`
    PASS."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "v2_only_errors_on_v1.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-202"}, result.stdout
    assert statuses.get("ACP-INIT-205") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_only_honest_fails_init_202_and_205():
    """`v2_only_honest.py` selects 2 for every well-formed request, including 1 and 0 -- a
    version higher than requested, where `-32022` is required."""
    fails, statuses = _negotiation_fails("v2_only_honest.py")
    assert fails == {"ACP-INIT-202", "ACP-INIT-205"}, statuses


def test_unsupported_version_bad_data_fails_init_205_only():
    """`unsupported_version_bad_data.py`'s `-32022` lacks `data.supported`; `ACP-INIT-202` only
    judges the code, so it PASSes."""
    fails, statuses = _negotiation_fails("unsupported_version_bad_data.py")
    assert fails == {"ACP-INIT-205"}, statuses
    assert statuses.get("ACP-INIT-202") == "PASS", statuses


def test_accepts_string_version_fails_init_206_only():
    fails, statuses = _negotiation_fails("accepts_string_version.py")
    assert fails == {"ACP-INIT-206"}, statuses


def test_starts_session_after_mismatch_fails_init_207_and_error_005():
    """The `session/new` after `-32022` succeeds: `ACP-INIT-207` (session work began) and
    `ACP-ERROR-005` (the request was not answered `-32600`)."""
    fails, statuses = _negotiation_fails("starts_session_after_mismatch.py")
    assert fails == {"ACP-INIT-207", "ACP-ERROR-005"}, statuses
    assert statuses.get("ACP-INIT-205") == "PASS", statuses


def test_serves_before_initialize_fails_error_005_and_init_207():
    """Never refusing a request also lets the `session/new` after `-32022` succeed
    (`ACP-INIT-207`)."""
    fails, statuses = _negotiation_fails("serves_before_initialize.py")
    assert fails == {"ACP-INIT-207", "ACP-ERROR-005"}, statuses


def test_notifies_before_initialize_fails_init_210_only():
    fails, statuses = _negotiation_fails("notifies_before_initialize.py")
    assert fails == {"ACP-INIT-210"}, statuses


def test_no_retry_after_failed_initialize_fails_init_211_only():
    """It also answers `-32600` to a pre-initialize request, so `ACP-ERROR-005` PASSes."""
    fails, statuses = _negotiation_fails("no_retry_after_failed_initialize.py")
    assert fails == {"ACP-INIT-211"}, statuses
    assert statuses.get("ACP-ERROR-005") == "PASS", statuses


def test_rejects_repeated_initialize_fails_init_212_only():
    """A second `initialize` is rejected (`-32600`) before any other request: `ACP-INIT-212`
    FAILs, but a repeat after another request must be rejected too, so `ACP-INIT-213` PASSes."""
    fails, statuses = _negotiation_fails("rejects_repeated_initialize.py")
    assert fails == {"ACP-INIT-212"}, statuses
    assert statuses.get("ACP-INIT-213") == "PASS", statuses


def test_accepts_initialize_after_request_fails_init_213_only():
    """`ACP-INIT-215` SKIPs: there is no error whose code it could check."""
    fails, statuses = _negotiation_fails("accepts_initialize_after_request.py")
    assert fails == {"ACP-INIT-213"}, statuses
    assert statuses.get("ACP-INIT-215") == "SKIPPED", statuses
    assert statuses.get("ACP-INIT-212") == "PASS", statuses


def test_late_initialize_wrong_code_fails_init_215_only():
    """`-32602` instead of `-32600`: a rejection, so the MANDATORY `ACP-INIT-213` PASSes and
    only the ADVISORY code row fails."""
    fails, statuses = _negotiation_fails("late_initialize_wrong_code.py")
    assert fails == {"ACP-INIT-215"}, statuses
    assert statuses.get("ACP-INIT-213") == "PASS", statuses


def test_rejects_unparseable_newer_params_fails_init_214_only():
    fails, statuses = _negotiation_fails("rejects_unparseable_newer_params.py")
    assert fails == {"ACP-INIT-214"}, statuses


def test_dual_v2_shape_on_v1_fails_init_208_only():
    """`dual_v2_shape_on_v1.py` selects 1 for a v1 request (so `ACP-INIT-202` PASSes) but answers
    with v2's `info`/`capabilities`."""
    fails, statuses = _negotiation_fails("dual_v2_shape_on_v1.py")
    assert fails == {"ACP-INIT-208"}, statuses
    assert statuses.get("ACP-INIT-202") == "PASS", statuses


def test_missing_info_fails_init_004_and_schema_001_only():
    """`missing_info.py` omits the required `info` field entirely -- fails `ACP-INIT-004` (`info`
    is REQUIRED in v2) and `ACP-SCHEMA-001` (the same missing-required-property schema
    violation). `ACP-INIT-001` still PASSes: it only asserts `initialize` returned a non-error
    result (this fixture still does), never the result's shape. It advertises
    `capabilities: {"session": {}}` like `conforming.py`, so `ACP-SESSION-001/002` PASS."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "missing_info.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-004", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-INIT-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_boolean_session_capability_fails_init_204_and_schema_001_only():
    """`boolean_session_capability.py` advertises `capabilities.session: true` (a boolean, not an
    object marker) -- fails `ACP-SCHEMA-001` (schema violation) and `ACP-INIT-204` (capability
    markers must be objects). `ACP-INIT-001` still PASSes (non-error result only), and
    `ACP-SESSION-001`/`002` still PASS: the underlying `session/new` handler works fine and
    `capability_is_supported` treats `true` as advertised."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "boolean_session_capability.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-204", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-INIT-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


# The negotiation rows (`ACP-INIT-001`/`003`/`201`/`202`/`208`) assert only on the negotiation
# *outcome*, never on the result's v2 shape, so an agent that honestly negotiates down to 1 still
# PASSes them. `ACP-INIT-205`/`206`/`207` bind agents implementing v2 only, so they SKIP. The v2-only *shape* rows (`info` required, object-only capability markers, v2
# schema validity, plus the CAPABILITY-tier session rows) cannot be meaningfully judged against
# a result the agent never claimed was v2-shaped, so they SKIP with the `VERSION-MISMATCH:`
# marker instead of FAILing (see `tck.v2.requirements`'s "Version-mismatch-aware v2-shape rows"
# section).
# `ACP-STATE-204` (ADVISORY) and the INFORMATIONAL probes carry the same
# `@pytest.mark.capability("capabilities.session")` marker as every other row below, so the
# autouse version-mismatch gate (`tck.common.plugin`'s `_tck_capability_gate`) skips them with
# the same `VERSION-MISMATCH:` marker too -- include them here alongside the MANDATORY/
# CAPABILITY rows rather than carving out a separate, unchecked set.
#
# A second, disjoint category: `ACP-JSONRPC-001..005` (not 202, which judges agent-authored
# requests and so SKIPs `VERSION-MISMATCH:` like the rows above) are connection-level rows whose own tests
# never drive a full v2-shaped `session/prompt` turn at all (`test_jsonrpc.py`'s tests only use
# `initialize`/`session/new`/bare notifications). A v1 agent's ordinary handshake/session/
# notification traffic satisfies all five of these unchanged, so -- like the negotiation rows --
# they PASS rather than SKIP here. `ACP-TRANSPORT-001`/`002`/`203`, despite also being
# connection-level, do NOT belong in this set: `test_transport.py`'s own `_drive_full_exchange`
# calls `skip_if_version_mismatch` itself before ever gathering evidence (see that module's
# docstring), specifically so it never has to drive v2-only `run_prompt` machinery against a
# mismatched agent -- so they SKIP, not PASS. Confirmed empirically: a full run of
# `test_transport.py`/`test_jsonrpc.py`/`test_batch.py` against
# `tests/fixtures/agents/v1/conforming.py` under `--protocol-version 2` produces zero FAILs,
# exactly the five JSONRPC ids PASS, and every other new id (all of
# `ACP-TRANSPORT-*`/`ACP-BATCH-*`) SKIPs with `VERSION-MISMATCH:`.
_NEGOTIATION_IDS = {"ACP-INIT-001", "ACP-INIT-003", "ACP-INIT-201", "ACP-INIT-202", "ACP-INIT-208"}
# ACP-EXT-001/002/203 probe an ordinary `_`-/`$/`-prefixed custom method or notification
# exchange -- they never inspect `initialize`'s negotiated version or its `capabilities` shape at
# all, so they PASS regardless of which protocolVersion was negotiated.
# ACP-EXT-202 is NOT included here: it reads `result.capabilities` (the v2 field name) directly,
# which a v1-negotiated result simply doesn't have (v1 uses `agentCapabilities` instead), so it
# correctly `pytest.skip("initialize result has no capabilities object to check")`s on its own --
# a genuine skip, not the VERSION-MISMATCH marker, but still a skip either way (see
# `test_extensibility.py`'s module docstring for the full breakdown).
_VERSION_TOLERANT_IDS = _NEGOTIATION_IDS | {
    "ACP-JSONRPC-001",
    "ACP-JSONRPC-002",
    "ACP-JSONRPC-003",
    "ACP-JSONRPC-004",
    "ACP-JSONRPC-005",
    "ACP-EXT-001",
    "ACP-EXT-002",
    "ACP-EXT-203",
    # ACP-JSONRPC-006 and ACP-CANCEL-211: connection-level `$/cancel_request` probes with no capability marker;
    # a reply to a notification is non-conforming in v1 too, so a v1 agent is judged normally.
    "ACP-JSONRPC-006",
    "ACP-CANCEL-211",
    # ACP-INFO-PARSE-001/ACP-INFO-INVALIDREQ-001 (re-cited from v1, unchanged) carry no
    # `@pytest.mark.capability(...)` marker at all (test_informational.py's module docstring),
    # and their shared `_probe_connection_usable_after` helper swallows a `session/new` failure
    # -- including a version-mismatched/capability-unsupporting one -- into an "unusable"
    # behaviour string rather than letting it propagate, then only ever `record_property(...)`s
    # it, never asserts. So both PASS unconditionally, the same as the five JSONRPC ids above.
    "ACP-INFO-PARSE-001",
    "ACP-INFO-INVALIDREQ-001",
    # ACP-STDERR-001 (re-cited from v1, unchanged): also connection-level/no capability marker,
    # and its own `new_session(...)` call succeeds even against a v1-negotiated agent -- v1's
    # `conforming.py` implements `session/new` unconditionally at the wire level, with no
    # capability check of its own -- so this always PASSes regardless of negotiated version too.
    "ACP-STDERR-001",
    # ACP-ERROR-001/ACP-SHUTDOWN-001 (re-cited from v1, unchanged, `test_diagnostics.py`): same
    # story -- connection-level, no capability marker, and their own `session/new` (missing
    # `cwd`, or ordinary) calls succeed at the wire level against a v1-negotiated agent too.
    "ACP-ERROR-001",
    "ACP-SHUTDOWN-001",
}
_VERSION_MISMATCH_SKIP_IDS = (
    _MANDATORY_IDS | _CAPABILITY_IDS | _ADVISORY_IDS | _INFORMATIONAL_IDS
) - _VERSION_TOLERANT_IDS
assert _VERSION_TOLERANT_IDS | _VERSION_MISMATCH_SKIP_IDS == _ALL_IDS


def test_v1_conforming_agent_under_protocol_version_2_is_blocked_by_version_mismatch(tmp_path):
    """The v1 conforming fixture speaks only protocol version 1, so under `--protocol-version 2`
    it honestly negotiates down to `1` for every fresh handshake (a legacy v1-only agent returns
    v1 to a v2 request). The negotiation rows (`ACP-INIT-001`/`003`/`201`/`202`/`208`) are judged normally against
    that honest negotiation and PASS -- an agent that does not yet speak v2 is not thereby
    "broken". Every v2-only shape row (`ACP-INIT-004`/`204`/`ACP-SCHEMA-001`,
    `ACP-SESSION-001`/`002`) SKIPs with the `VERSION-MISMATCH:` marker instead of FAILing, since
    a v1-shaped result cannot be judged against v2 shape rules. Zero FAILs anywhere, yet the run
    as a whole is still NOT CONFORMANT with `verdict.blocked_by_version_mismatch == true`, exit
    code 1, and a terminal hint -- the version-dependent requirements were never actually
    exercised against v2."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V1,
        "conforming.py",
        protocol_version=2,
        report_json=str(report_path),
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "blocked by version mismatch" in result.stdout, result.stdout
    assert "negotiated protocol version" in result.stdout.lower() or "did not negotiate" in result.stdout.lower(), result.stdout

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), f"expected zero FAILs (honest downgrade, not a defect): {result.stdout}"
    for req_id in _VERSION_TOLERANT_IDS:
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    for req_id in _VERSION_MISMATCH_SKIP_IDS:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"

    report = json.loads(report_path.read_text())
    assert report["verdict"]["blocked_by_version_mismatch"] is True, report["verdict"]
    assert report["verdict"]["conformant"] is False, report["verdict"]

    skip_results = [r for r in report["requirements"] if r["id"] in _VERSION_MISMATCH_SKIP_IDS]
    assert len(skip_results) == len(_VERSION_MISMATCH_SKIP_IDS)
    for r in skip_results:
        assert r["status"] == "SKIPPED", r
        if r["id"] in _ALWAYS_SKIPPED_IDS:
            # ACP-CANCEL-204 is an unconditional record-only SKIP (MAY, never
            # exercised regardless of version) -- they SKIP here for that reason, not
            # because of the version mismatch, so they carry no VERSION-MISMATCH: marker.
            continue
        if r["id"] == "ACP-EXT-202":
            # ACP-EXT-202 carries no `@pytest.mark.capability(...)` marker either (it reads
            # `result.capabilities` -- the v2 field name -- directly, rather than going through
            # the autouse capability gate), so it never produces the VERSION-MISMATCH: marker
            # text; it still genuinely SKIPs here, just via its own plain
            # `pytest.skip("initialize result has no capabilities object to check")`, since a
            # v1-negotiated result has no `capabilities` key at all (v1 uses `agentCapabilities`
            # instead) -- see `test_extensibility.py`'s module docstring.
            continue
        assert any("VERSION-MISMATCH:" in t["message"] for t in r["tests"]), r["tests"]

    pass_results = [r for r in report["requirements"] if r["id"] in _VERSION_TOLERANT_IDS]
    assert len(pass_results) == len(_VERSION_TOLERANT_IDS)
    for r in pass_results:
        assert r["status"] == "PASS", r
