"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_cursors.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def test_cursor_defect_fixtures_fail_only_their_own_row():
    """Each fixture advertises `fork` and announces cursors on every turn (v2 has no client
    capability for them). Everything but the defective row PASSes or SKIPs (ACP-CURSOR-004 SKIPs for
    the fixture whose replayed cursors carry no anchor, so none matches across the two replays). The
    run is scoped with `-k`, so its verdict is not asserted."""
    ids = [f"ACP-CURSOR-00{n}" for n in (1, 2, 3, 4)]
    for fixture, expected in (
        ("cursor_anchor_moves.py", "ACP-CURSOR-001"),
        ("replays_cursor_without_anchor.py", "ACP-CURSOR-001"),
        ("cursor_anchor_unknown_entity.py", "ACP-CURSOR-002"),
        ("replays_cursor_before_entity.py", "ACP-CURSOR-002"),
        ("fork_ignores_cursor_id.py", "ACP-CURSOR-003"),
        ("unstable_cursor_ids.py", "ACP-CURSOR-004"),
    ):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_cursors")
        statuses = _table_statuses(result.stdout)
        fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
        assert fails == {expected}, f"{fixture}:\n{result.stdout}"
        for req_id in set(ids) - {expected}:
            assert statuses[req_id] in ("PASS", "SKIPPED"), f"{fixture} {req_id}:\n{result.stdout}"


def test_conforming_cursors_pass_non_vacuously_and_conforming_skips():
    """`conforming_full.py` announces cursors, replays them with the same ids on a full resume and
    rejects an unissued `cursorId` on `session/fork`, so all four ACP-CURSOR rows PASS (none
    SKIPs). `conforming.py` announces none and advertises no `fork`: all four SKIP. An agent that
    advertises `fork` but announces no cursor is probed all the same (literal reading of the rule), so
    `forks_without_cursors.py` PASSes ACP-CURSOR-003 and SKIPs the other three."""
    scope = "test_cursors"
    full = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=scope).stdout)
    assert {full[f"ACP-CURSOR-00{n}"] for n in (1, 2, 3, 4)} == {"PASS"}, full
    plain = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k=scope).stdout)
    assert {plain[f"ACP-CURSOR-00{n}"] for n in (1, 2, 3, 4)} == {"SKIPPED"}, plain
    unaware = _table_statuses(
        _run_cli(FIXTURES_DIR_V2, "forks_without_cursors.py", protocol_version=2, k=scope).stdout
    )
    assert [unaware[f"ACP-CURSOR-00{n}"] for n in (1, 2, 3, 4)] == ["SKIPPED", "SKIPPED", "PASS", "SKIPPED"], unaware
