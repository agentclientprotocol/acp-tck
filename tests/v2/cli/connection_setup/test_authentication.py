"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_authentication.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def test_login_method_not_found_fails_auth_003_only():
    """`login_method_not_found.py` advertises `authMethods` but answers `auth/login` with
    `-32601`, which an agent advertising `authMethods` MUST NOT do."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "login_method_not_found.py",
        protocol_version=2,
        k="authentication",
        auth_method="tck",
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-003"}, result.stdout


def test_gated_by_auth_without_auth_method_is_blocked_by_auth():
    """`gated_by_auth.py` always errors `session/new` with `-32000` unless `auth/login` with
    methodId `"tck"` has already succeeded on the connection. Without `--auth-method`, every
    session-dependent test SKIPs with the `AUTH-GATED:` marker (via `skip_if_auth_gated()`),
    which forces `verdict.blocked_by_auth == true` and exit code 1 -- even though zero
    requirements actually FAILed; they were simply never exercised. Mirrors v1's
    `gated_by_auth.py` self-test."""
    result = _run_cli(FIXTURES_DIR_V2, "gated_by_auth.py", protocol_version=2)
    assert result.returncode != 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), f"expected zero FAILs (the agent is merely never exercised): {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "blocked by auth" in result.stdout.lower() or "auth-gated" in result.stdout.lower(), result.stdout


def test_login_that_never_answers_skips_auth_gated_and_blocks_the_verdict(tmp_path):
    """`gated_by_auth_login_never_answers.py` never answers `auth/login` (an interactive login
    that stays pending). `connected_agent`'s embedded login times out, which SKIPs with the
    `AUTH-GATED:` marker and a hint instead of FAILing, and blocks the verdict like any other
    auth gate. Mirrors v1's self-test."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "gated_by_auth_login_never_answers.py",
        protocol_version=2,
        k="test_session_new_returns_unique_string_id",
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


def test_gated_by_auth_with_auth_method_is_conformant():
    """The same `gated_by_auth.py` fixture, run with `--auth-method tck`: `connected_agent`'s
    auto-login step (`_helpers.py`) authenticates before any session-dependent test ever calls
    `session/new`, so the gate never fires and the run is fully CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "gated_by_auth.py", protocol_version=2, auth_method="tck")
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_terminal_auth_unadvertised_fails_auth_002_only():
    """`terminal_auth_unadvertised.py` advertises a `type: "terminal"` authMethods entry on every
    connection, including the default one that never advertises `capabilities.auth.terminal` --
    FAILs exactly `ACP-AUTH-002` within its `-k` scope. It has no `args`/`env` fields at all, so it cannot also trip
    `ACP-AUTH-006` (which only runs when a terminal entry actually appears on the dedicated
    terminal-capable connection -- and this fixture happens to also advertise it there, but with
    a well-formed descriptor)."""
    result = _run_cli(FIXTURES_DIR_V2, "terminal_auth_unadvertised.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-002"}, result.stdout
    for req_id in ("ACP-AUTH-001", "ACP-AUTH-206", "ACP-AUTH-006"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_duplicate_method_id_fails_auth_001_only():
    """`duplicate_method_id.py` advertises two `authMethods` entries sharing the same
    `methodId` -- FAILs exactly `ACP-AUTH-001` within its `-k` scope, which is MANDATORY (`authentication.mdx:51`), so
    the run is NOT CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "duplicate_method_id.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-001"}, result.stdout
    for req_id in ("ACP-AUTH-002", "ACP-AUTH-206"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_custom_auth_type_unprefixed_fails_auth_206_only():
    """`custom_auth_type_unprefixed.py` advertises an authMethods entry whose `type` is
    `"sso"` -- neither a defined value nor `_`-prefixed -- FAILs exactly `ACP-AUTH-206` within its `-k` scope
    (MANDATORY, new in v2)."""
    result = _run_cli(FIXTURES_DIR_V2, "custom_auth_type_unprefixed.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-206"}, result.stdout
    for req_id in ("ACP-AUTH-001", "ACP-AUTH-002"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_advertises_auth_but_logout_errors_fails_auth_004_only_with_allow_logout():
    """`advertises_auth_but_logout_errors.py` implements `auth/login` normally but always errors
    on `auth/logout`. Run with `--auth-method tck --allow-logout` (both required to actually
    exercise `auth/logout` at all) -- FAILs exactly `ACP-AUTH-004` within its `-k` scope."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "advertises_auth_but_logout_errors.py",
        protocol_version=2,
        k="authentication",
        auth_method="tck",
        allow_logout=True,
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-004"}, result.stdout
    assert statuses.get("ACP-AUTH-003") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_advertises_auth_but_logout_errors_skips_auth_004_without_allow_logout():
    """The same fixture, without `--allow-logout`: `auth/logout` is never called at all, so
    `ACP-AUTH-004` SKIPs (its documented, diagnosable reason) rather than FAILing. Scoped with
    `-k authentication`, so the exit code/overall verdict text are not asserted (scoping leaves
    other MANDATORY ids `NOT_TESTED`, which flips the verdict by design)."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "advertises_auth_but_logout_errors.py",
        protocol_version=2,
        k="authentication",
        auth_method="tck",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert statuses.get("ACP-AUTH-004") == "SKIPPED", result.stdout


def test_logout_not_idempotent_fails_auth_211_only():
    """`logout_not_idempotent.py` answers a second `auth/logout` (no authenticated state left)
    with an error. Run with `--auth-method tck --allow-logout`, only the ADVISORY `ACP-AUTH-211`
    FAILs; `ACP-AUTH-004` PASSes, since the TCK's login gives the first logout state to end. The
    second revoking test logs in again after the first one's logout and still works."""
    fails, statuses, out, _ = _auth_fixture_run(
        "logout_not_idempotent.py", auth_method="tck", allow_logout=True
    )
    assert fails == {"ACP-AUTH-211"}, out
    assert statuses.get("ACP-AUTH-004") == "PASS", out


def test_logout_not_idempotent_skips_logout_rows_without_a_tck_login():
    """Without `--auth-method` the fixture's first logout has no state to end and errors: the
    standalone path of `ACP-AUTH-004` SKIPs on any error but `-32601`, and `ACP-AUTH-211` SKIPs
    since the first logout did not succeed."""
    fails, statuses, out, _ = _auth_fixture_run("logout_not_idempotent.py", allow_logout=True)
    assert fails == set(), out
    assert statuses.get("ACP-AUTH-004") == "SKIPPED", out
    assert statuses.get("ACP-AUTH-211") == "SKIPPED", out


def test_logout_method_not_found_fails_auth_004_standalone():
    """`-32601` on the standalone logout still FAILs `ACP-AUTH-004` (the MUST to implement it)."""
    fails, statuses, out, _ = _auth_fixture_run("logout_method_not_found.py", allow_logout=True)
    assert fails == {"ACP-AUTH-004"}, out
    assert statuses.get("ACP-AUTH-211") == "SKIPPED", out


def test_terminal_env_duplicate_names_fails_auth_006_only():
    """`terminal_env_duplicate_names.py` only advertises its `type: "terminal"` authMethods entry
    to a connection that itself advertises `capabilities.auth.terminal` -- so it never trips
    `ACP-AUTH-002` (the default connection sees no `authMethods` at all) -- but that entry's
    `env` array has two entries sharing the same `name`, FAILing exactly `ACP-AUTH-006`
    (MANDATORY, new in v2). `ACP-AUTH-001`/`206` bind to `agent_initialize_result`, which
    connects with the default (no `auth.terminal`) capabilities, so they see no `authMethods` at
    all and SKIP rather than PASS."""
    result = _run_cli(FIXTURES_DIR_V2, "terminal_env_duplicate_names.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-006"}, result.stdout
    assert statuses.get("ACP-AUTH-002") == "PASS", result.stdout
    for req_id in ("ACP-AUTH-001", "ACP-AUTH-206"):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def _auth_fixture_run(fixture: str, **kwargs):
    """`-k authentication` run; returns `(fails, statuses, stdout, result)`."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="authentication", **kwargs)
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    return fails, statuses, result.stdout, result


def test_login_advertised_agent_method_invalid_params_fails_auth_003_only():
    """`login_advertised_agent_method_invalid_params.py` answers `-32602` to `auth/login` for its
    advertised `type: "agent"` method: FAILs exactly `ACP-AUTH-003` within its `-k` scope. An unadvertised id is still
    rejected `-32602`, so `ACP-AUTH-208`/`210` PASS."""
    fails, statuses, out, result = _auth_fixture_run(
        "login_advertised_agent_method_invalid_params.py", auth_method="tck"
    )
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-003"}, out
    assert "-32602" in out, out
    for req_id in ("ACP-AUTH-208", "ACP-AUTH-210"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {out}"


def test_login_accepts_unadvertised_method_fails_auth_208_only():
    """`login_accepts_unadvertised_method.py` answers `{}` for an unadvertised `methodId`: FAILs
    exactly `ACP-AUTH-208`; `ACP-AUTH-210` SKIPs (nothing was rejected, so no code to judge)."""
    fails, statuses, out, result = _auth_fixture_run("login_accepts_unadvertised_method.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-208"}, out
    assert statuses.get("ACP-AUTH-210") == "SKIPPED", out


def test_login_unadvertised_method_wrong_code_fails_auth_210_advisory_only():
    """`login_unadvertised_method_wrong_code.py` rejects the unadvertised id with `-32000`:
    `ACP-AUTH-208` PASSes, `ACP-AUTH-210` FAILs, and being ADVISORY it leaves the run's
    exit code at 0 apart from the scoping (`-k authentication` leaves MANDATORY ids unexercised),
    so only the per-id statuses are asserted."""
    fails, statuses, out, _result = _auth_fixture_run("login_unadvertised_method_wrong_code.py")
    assert fails == {"ACP-AUTH-210"}, out
    assert statuses.get("ACP-AUTH-208") == "PASS", out


def test_auth_status_auth_required_fails_auth_007_only():
    """`auth_status_auth_required.py` answers `auth/status` with `-32000`; with no `state` to judge,
    `ACP-AUTH-008` SKIPs."""
    fails, statuses, out, result = _auth_fixture_run("auth_status_auth_required.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-007"}, out
    assert statuses.get("ACP-AUTH-008") == "SKIPPED", out
    assert "-32000" in out, out


def test_auth_status_missing_state_fails_auth_007_only():
    fails, statuses, out, result = _auth_fixture_run("auth_status_missing_state.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-007"}, out
    assert statuses.get("ACP-AUTH-008") == "SKIPPED", out


def test_auth_status_unreserved_state_fails_auth_008_only():
    """`state: "logged_in"` is schema-valid (open enum, so `ACP-AUTH-007` PASSes) but neither
    defined nor `_`-prefixed."""
    fails, statuses, out, result = _auth_fixture_run("auth_status_unreserved_state.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-008"}, out
    assert statuses.get("ACP-AUTH-007") == "PASS", out
    assert "logged_in" in out, out


def test_auth_status_is_judged_unauthenticated_even_with_auth_method():
    """`gated_by_auth_with_status.py` is unauthenticated until `auth/login`: ACP-AUTH-007/008 PASS
    both without `--auth-method` and with `--auth-method tck`, whose login the `auth/status`
    tests never perform. Scoped with `-k auth_status` to those tests only."""
    for auth_method in (None, "tck"):
        result = _run_cli(
            FIXTURES_DIR_V2,
            "gated_by_auth_with_status.py",
            protocol_version=2,
            k="auth_status",
            auth_method=auth_method,
        )
        statuses = _table_statuses(result.stdout)
        assert statuses.get("ACP-AUTH-007") == "PASS", result.stdout
        assert statuses.get("ACP-AUTH-008") == "PASS", result.stdout
