"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_cursors.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_cursor_defect_fixtures_fail_only_their_own_row():
    """Each fixture announces cursors only to a client that advertised `session.cursors`, so
    ACP-CLIENTCAP-009 stays PASS, and advertises `loadSession` and `fork`. Everything but the
    defective row PASSes or SKIPs (ACP-CURSOR-004 SKIPs when no replayed cursor is placeable). The run
    is scoped with `-k`, so its verdict is not asserted."""
    ids = [f"ACP-CURSOR-00{n}" for n in (1, 2, 3, 4)]
    for fixture, expected in (
        ("cursor_anchor_moves.py", "ACP-CURSOR-001"),
        ("cursor_first_update_no_anchor.py", "ACP-CURSOR-001"),
        ("cursor_anchor_unknown_entity.py", "ACP-CURSOR-002"),
        ("fork_ignores_cursor_id.py", "ACP-CURSOR-003"),
        ("unstable_cursor_ids.py", "ACP-CURSOR-004"),
    ):
        result = _run_cli(fixture, k="test_cursors or test_client_capabilities")
        assert _output_fail_ids(result.stdout) == {expected}, f"{fixture}:\n{result.stdout}"
        statuses = _table_statuses(result.stdout)
        assert statuses["ACP-CLIENTCAP-009"] == "PASS", f"{fixture}:\n{result.stdout}"
        for req_id in set(ids) - {expected}:
            assert statuses[req_id] in ("PASS", "SKIPPED"), f"{fixture} {req_id}:\n{result.stdout}"


def test_conforming_cursors_pass_non_vacuously_and_conforming_skips():
    """`conforming_full.py` announces cursors, replays them stably on `session/load` and rejects an
    unissued `cursorId` on `session/fork`, so all four ACP-CURSOR rows PASS (none SKIPs);
    `conforming.py` announces none and has no `fork`: 001/002 pass vacuously, 003 and 004 SKIP."""
    scope = "test_cursors"
    full = _table_statuses(_run_cli("conforming_full.py", k=scope).stdout)
    assert {full[f"ACP-CURSOR-00{n}"] for n in (1, 2, 3, 4)} == {"PASS"}, full
    plain = _table_statuses(_run_cli("conforming.py", k=scope).stdout)
    assert [plain[f"ACP-CURSOR-00{n}"] for n in (1, 2, 3, 4)] == ["PASS", "PASS", "SKIPPED", "SKIPPED"], plain
    # An agent that advertises `fork` but announces no cursor is probed all the same, and a
    # rejection is all it takes to PASS.
    unaware = _table_statuses(_run_cli("forks_without_cursors.py", k=scope).stdout)
    assert [unaware[f"ACP-CURSOR-00{n}"] for n in (1, 2, 3, 4)] == ["PASS", "PASS", "PASS", "SKIPPED"], unaware
