"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_prompt_suggestions.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_prompt_suggestion_defect_fixtures_fail_only_their_own_row():
    """Each fixture sends suggestions only to a client that advertised `promptSuggestions`, so
    ACP-CLIENTCAP-008 stays PASS. Everything but the defective row PASSes or SKIPs (ACP-SUGGEST-004
    SKIPs without `loadSession`). The run is scoped with `-k`, so its verdict is not asserted."""
    for fixture, expected in (
        ("suggests_image_block.py", "ACP-SUGGEST-001"),
        ("suggests_blank_prompt.py", "ACP-SUGGEST-002"),
        ("stale_suggestions.py", "ACP-SUGGEST-003"),
        ("replays_suggestions.py", "ACP-SUGGEST-004"),
    ):
        result = _run_cli(fixture, k="test_prompt_suggestions or test_client_capabilities")
        assert _output_fail_ids(result.stdout) == {expected}, f"{fixture}:\n{result.stdout}"
        statuses = _table_statuses(result.stdout)
        assert statuses["ACP-CLIENTCAP-008"] == "PASS", f"{fixture}:\n{result.stdout}"
        for req_id in {"ACP-SUGGEST-001", "ACP-SUGGEST-002", "ACP-SUGGEST-003", "ACP-SUGGEST-004"} - {expected}:
            assert statuses[req_id] in ("PASS", "SKIPPED"), f"{fixture} {req_id}:\n{result.stdout}"


def test_conforming_suggestions_pass_non_vacuously_and_conforming_skips():
    """`conforming_full.py` sends and withdraws suggestions and advertises `loadSession`, so all four
    ACP-SUGGEST rows PASS (none SKIPs); `conforming.py` sends none: 001/002 pass vacuously, 003 and
    004 SKIP."""
    scope = "test_prompt_suggestions"
    full = _table_statuses(_run_cli("conforming_full.py", k=scope).stdout)
    assert {full[f"ACP-SUGGEST-00{n}"] for n in (1, 2, 3, 4)} == {"PASS"}, full
    plain = _table_statuses(_run_cli("conforming.py", k=scope).stdout)
    assert [plain[f"ACP-SUGGEST-00{n}"] for n in (1, 2, 3, 4)] == ["PASS", "PASS", "SKIPPED", "SKIPPED"], plain
