"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_prompt_suggestions.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def test_prompt_suggestion_defect_fixtures_fail_only_their_own_row():
    """Each fixture sends suggestions only to a client that advertised `promptSuggestions`, so
    ACP-CLIENTCAP-008 stays PASS. Everything but the defective row PASSes (ACP-SUGGEST-004 too: the
    fixtures send suggestions live and only `replays_suggestions.py` repeats one after
    `replay_complete`). The run is scoped
    with `-k`, so its verdict is not asserted."""
    for fixture, expected in (
        ("suggests_image_block.py", "ACP-SUGGEST-001"),
        ("suggests_blank_prompt.py", "ACP-SUGGEST-002"),
        ("stale_suggestions.py", "ACP-SUGGEST-003"),
        ("replays_suggestions.py", "ACP-SUGGEST-004"),
    ):
        result = _run_cli(
            FIXTURES_DIR_V2,
            fixture,
            protocol_version=2,
            k="test_prompt_suggestions or test_client_capabilities",
        )
        statuses = _table_statuses(result.stdout)
        fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
        assert fails == {expected}, f"{fixture}:\n{result.stdout}"
        assert statuses["ACP-CLIENTCAP-008"] == "PASS", f"{fixture}:\n{result.stdout}"
        for req_id in {"ACP-SUGGEST-001", "ACP-SUGGEST-002", "ACP-SUGGEST-003"} - {expected}:
            assert statuses[req_id] == "PASS", f"{fixture} {req_id}:\n{result.stdout}"
        if expected != "ACP-SUGGEST-004":
            assert statuses["ACP-SUGGEST-004"] == "PASS", f"{fixture}:\n{result.stdout}"


def test_conforming_suggestions_pass_non_vacuously_and_conforming_skips():
    """`conforming_full.py` sends and withdraws suggestions, so ACP-SUGGEST-001..003 PASS (none SKIPs).
    ACP-SUGGEST-004 PASSes too: the fixture base ends a replay with `replay_complete`, so the window
    to the resume response is bounded. `conforming.py` sends none: all four SKIP."""
    scope = "test_prompt_suggestions"
    full = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=scope).stdout)
    assert [full[f"ACP-SUGGEST-00{n}"] for n in (1, 2, 3, 4)] == ["PASS", "PASS", "PASS", "PASS"], full
    plain = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k=scope).stdout)
    assert {plain[f"ACP-SUGGEST-00{n}"] for n in (1, 2, 3, 4)} == {"SKIPPED"}, plain
