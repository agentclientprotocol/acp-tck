"""End-to-end CLI tests for the `session/load` rows of `src/tck/v1/conformance/test_session_capabilities.py`:
each runs fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _run_cli, _table_statuses


def test_load_replays_after_response_fails_load_002_only():
    """`load_replays_after_response.py` advertises `loadSession` but answers `session/load`
    before replaying stored history instead of after -- ACP-LOAD-001 still PASSes (the response
    itself is valid), only the ordering requirement ACP-LOAD-002 FAILs."""
    result = _run_cli("load_replays_after_response.py", k="load")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-LOAD-001") == "PASS", result.stdout
    assert statuses.get("ACP-LOAD-002") == "FAIL", result.stdout


def test_load_returns_null_fails_load_003_advisory_only():
    """`load_returns_null.py` replays history correctly and advertises `loadSession`, but
    answers `session/load` with a literal `null` instead of `{}`. Mandatory schema validation
    tolerates `null` for this all-optional response, so ACP-LOAD-001/002 PASS; only the
    stricter ADVISORY ACP-LOAD-003 FAILs. The overall exit code is *not* asserted here (see
    `test_hangs_until_cancel_agent_passes_cancel_requirements` for why): a `-k`-scoped run
    necessarily leaves every MANDATORY requirement NOT_TESTED, which by itself forces a
    non-conformant verdict regardless of ACP-LOAD-003's own (ADVISORY, verdict-inert) status."""
    result = _run_cli("load_returns_null.py", k="load")

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-LOAD-001") == "PASS", result.stdout
    assert statuses.get("ACP-LOAD-002") == "PASS", result.stdout
    assert statuses.get("ACP-LOAD-003") == "FAIL", result.stdout


def test_advertises_load_but_errors_fails_load_001_and_verdict():
    """`advertises_load_but_errors.py` advertises `loadSession: true` but always errors on
    `session/load` -- a CAPABILITY-tier FAIL, which must flip the overall verdict to NOT
    CONFORMANT (unlike an ADVISORY-only failure)."""
    result = _run_cli("advertises_load_but_errors.py", k="load")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-LOAD-001") == "FAIL", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
