"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_authentication.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._expectations import _CAPABILITY_GATED_IDS, _MANDATORY_IDS
from .._runner import _fail_ids, _output_fail_ids, _run_cli, _table_statuses


def test_terminal_auth_unadvertised_fails_auth_002():
    """`terminal_auth_unadvertised.py` advertises `authMethods[*].type == "terminal"` even to a
    client that never advertised `clientCapabilities.auth.terminal` -- a MANDATORY (Req 23) FAIL."""
    result = _run_cli("terminal_auth_unadvertised.py", k="auth")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-AUTH-002") == "FAIL", result.stdout


def test_gated_by_auth_without_auth_method_skips_with_hint_and_is_not_conformant():
    """`gated_by_auth.py` requires `authenticate` before `session/new` succeeds. Without
    `--auth-method`, every session-dependent test SKIPs (not FAILs) with a message pointing at
    the flag, and the run is scored NOT CONFORMANT via `Verdict.blocked_by_auth` even though no
    MANDATORY test actually FAILed."""
    result = _run_cli("gated_by_auth.py", k="session")
    assert result.returncode != 0
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "blocked by authentication" in result.stdout, result.stdout
    assert "--auth-method" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-SESSION-001") == "SKIPPED", result.stdout
    assert statuses.get("ACP-SESSION-002") == "SKIPPED", result.stdout


def test_gated_by_auth_with_auth_method_succeeds():
    """The same fixture, scoped the same way, but with `--auth-method tck` -- the auto-
    authenticate step in `connected_agent` makes it behave like a normal conforming agent for
    every session-dependent test in scope. The overall exit code is *not* asserted here (see
    `test_hangs_until_cancel_agent_passes_cancel_requirements` for why): a `-k`-scoped run
    necessarily leaves every out-of-scope MANDATORY requirement NOT_TESTED, which by itself
    forces a non-conformant verdict regardless of whether authentication itself worked -- what
    this test checks is that the in-scope session tests PASS instead of SKIPPING."""
    result = _run_cli("gated_by_auth.py", k="session", auth_method="tck")

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "blocked by authentication" not in result.stdout, result.stdout


def test_login_that_never_answers_skips_auth_gated_and_blocks_the_verdict(tmp_path):
    """`gated_by_auth_login_never_answers.py` never answers `authenticate` (an interactive
    login that stays pending). `connected_agent`'s embedded login times out, which SKIPs with
    the `AUTH-GATED:` marker and a hint instead of FAILing, and blocks the verdict like any
    other auth gate."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "gated_by_auth_login_never_answers.py",
        k="test_session_new_succeeds_with_a_unique_session_id",
        auth_method="tck",
        report_json=str(report_path),
        startup_timeout="1",  # the login waits the startup timeout out
    )
    assert result.returncode != 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-SESSION-001") == "SKIPPED", result.stdout
    assert "blocked by authentication" in result.stdout, result.stdout

    report = json.loads(report_path.read_text())
    assert report["verdict"]["blocked_by_auth"] is True, report["verdict"]
    assert report["verdict"]["conformant"] is False, report["verdict"]
    by_id = {r["id"]: r for r in report["requirements"]}
    message = by_id["ACP-SESSION-001"]["tests"][0]["message"]
    assert "AUTH-GATED:" in message and "interactive" in message, message


def test_gated_by_auth_full_run_without_auth_method_is_not_conformant_and_blocked_by_auth(
    tmp_path,
):
    """A full (unscoped) run against `gated_by_auth.py` without `--auth-method`: every
    session-dependent test SKIPs with the auth hint, no MANDATORY requirement actually FAILs
    (everything reachable without a session -- `initialize`, JSON-RPC envelope/id echo, the
    schema-less parts of ACP-AUTH-001/002 -- still PASSes), and the run is scored NOT CONFORMANT
    solely via `Verdict.blocked_by_auth`. The JSON report's `verdict.blocked_by_auth` must be
    `true` and `verdict.conformant` `false`."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "gated_by_auth.py",
        cancel_prompt="__hang__",
        report_json=str(report_path),
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "blocked by authentication" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    mandatory_fails = {
        req_id for req_id in _MANDATORY_IDS if statuses.get(req_id) == "FAIL"
    }
    assert not mandatory_fails, f"unexpected MANDATORY FAILs: {mandatory_fails}\n{result.stdout}"

    report = json.loads(report_path.read_text())
    assert report["verdict"]["blocked_by_auth"] is True, report["verdict"]
    assert report["verdict"]["conformant"] is False, report["verdict"]


def test_gated_by_auth_full_run_with_auth_method_is_fully_conformant():
    """The same full (unscoped) run, but with `--auth-method tck`: the auto-authenticate step
    in `connected_agent` makes `gated_by_auth.py` behave exactly like `conforming_full.py` minus
    the extra capabilities it doesn't advertise (`loadSession`, `sessionCapabilities`,
    `promptCapabilities`, `auth.logout`, `modes`/`configOptions`) -- every one of those SKIPs as
    "not advertised", every other MANDATORY/ADVISORY requirement PASSes, and the overall exit
    code is 0/CONFORMANT. `--cancel-prompt __hang__` is needed for the same reason
    `conforming_full.py`'s own self-test needs it: `_base.py`'s hang-on-`__hang__` behavior is
    unconditional, so ACP-CANCEL-001/002 need that exact prompt text to exercise the race
    instead of SKIPping as "cancellation not exercised"."""
    result = _run_cli("gated_by_auth.py", cancel_prompt="__hang__", auth_method="tck")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert "NOT TESTED" not in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    # ACP-AUTH-005 (AUTH-A1) legitimately SKIPs too: it only concerns an agent advertising no
    # authMethods, and `gated_by_auth.py` advertises one -- inapplicability, not a gap.
    capability_gated = _CAPABILITY_GATED_IDS - {"ACP-AUTH-003"} | {"ACP-AUTH-005"}
    for req_id in capability_gated:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (not advertised):\n{result.stdout}"
    for req_id, status in statuses.items():
        if req_id in capability_gated:
            continue
        assert status == "PASS", f"{req_id} is {status}, expected PASS:\n{result.stdout}"


def test_terminal_auth_bad_shape_fails_auth_006_only():
    """`terminal_auth_bad_shape.py` advertises a terminal method with a string `args` only to a
    client that enabled `auth.terminal`. The schema's lax `AuthMethod` union alone would accept
    it as an `agent` method; ACP-AUTH-006 validates it as the terminal variant it claims to be."""
    result = _run_cli("terminal_auth_bad_shape.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-AUTH-006"}, result.stdout
    assert statuses.get("ACP-AUTH-002") == "PASS", result.stdout


_AUTH_005_SCOPE = "not_gated_when_no_auth_methods or test_session_new_succeeds"


def test_auth_005_fails_on_minus_32000_without_auth_methods():
    result = _run_cli("auth_required_without_methods.py", k=_AUTH_005_SCOPE)
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-AUTH-005") == "FAIL", result.stdout
    assert statuses.get("ACP-SESSION-001") == "FAIL", result.stdout


def test_auth_005_leaves_other_session_new_errors_to_session_001():
    result = _run_cli("session_new_internal_error.py", k=_AUTH_005_SCOPE)
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-AUTH-005") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "FAIL", result.stdout


def _skip_message(report: dict, req_id: str) -> str:
    by_id = {r["id"]: r for r in report["requirements"]}
    (test,) = by_id[req_id]["tests"]
    assert test["status"] == "SKIPPED", by_id[req_id]
    return test["message"]


def test_auth_method_naming_a_terminal_method_skips_without_authenticating(tmp_path):
    """`terminal_auth_unadvertised.py` advertises a `terminal` method (id `term`) that its
    `authenticate` would accept. A client must not pass a terminal method to `authenticate`, so
    `--auth-method term` SKIPs session-dependent tests (blocked by auth) rather than using it."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "terminal_auth_unadvertised.py",
        k="test_session_new_succeeds or test_authenticate_then",
        auth_method="term",
        report_json=str(report_path),
    )
    assert "blocked by authentication" in result.stdout, result.stdout

    report = json.loads(report_path.read_text())
    assert "terminal auth method" in _skip_message(report, "ACP-SESSION-001")
    assert "terminal auth method" in _skip_message(report, "ACP-AUTH-003")


def test_auth_method_not_advertised_skips_without_authenticating(tmp_path):
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "gated_by_auth.py",
        k="test_session_new_succeeds or test_authenticate_then",
        auth_method="nope",
        report_json=str(report_path),
    )
    assert "blocked by authentication" in result.stdout, result.stdout

    report = json.loads(report_path.read_text())
    for req_id in ("ACP-SESSION-001", "ACP-AUTH-003"):
        assert "not one of the ids advertised" in _skip_message(report, req_id)


def test_auth_status_auth_required_fails_auth_007_only():
    """`auth_status_auth_required.py` answers `auth/status` with `-32000`; ACP-AUTH-008 SKIPs
    for want of a `state` to judge."""
    result = _run_cli("auth_status_auth_required.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-AUTH-007"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-AUTH-008") == "SKIPPED", result.stdout
    assert "-32000" in result.stdout, result.stdout


def test_auth_status_missing_state_fails_auth_007_only():
    result = _run_cli("auth_status_missing_state.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-AUTH-007"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-AUTH-008") == "SKIPPED", result.stdout


def test_auth_status_unreserved_state_fails_auth_008_advisory_only():
    """`auth_status_unreserved_state.py` answers `state: "logged_in"`: schema-valid (ACP-AUTH-007
    PASSes) but an ADVISORY failure, so the run stays CONFORMANT."""
    result = _run_cli("auth_status_unreserved_state.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _output_fail_ids(result.stdout) == {"ACP-AUTH-008"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-AUTH-007") == "PASS", result.stdout


def test_auth_status_is_judged_unauthenticated_even_with_auth_method():
    """`gated_by_auth_with_status.py` is unauthenticated until `authenticate`: ACP-AUTH-007/008
    PASS against it both without `--auth-method` and with `--auth-method tck`, whose
    auto-`authenticate` the `auth/status` tests skip. Scoped with `-k` to those tests only."""
    for auth_method in (None, "tck"):
        result = _run_cli(
            "gated_by_auth_with_status.py", k="auth_status", auth_method=auth_method
        )
        statuses = _table_statuses(result.stdout)
        assert statuses.get("ACP-AUTH-007") == "PASS", result.stdout
        assert statuses.get("ACP-AUTH-008") == "PASS", result.stdout
