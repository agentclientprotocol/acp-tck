"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_idempotency.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import pytest

from .._runner import FIXTURES_DIR_V2, _fails, _run_cli, _table_statuses


_IDEMPOTENCY_IDS = {f"ACP-PROMPT-{n}" for n in range(212, 220)}


def _idempotency_run(fixture: str) -> tuple[set[str], dict[str, str], str]:
    """Run only `test_idempotency.py` (with `--cancel-prompt __hang__`, which `ACP-PROMPT-215`
    needs) and return the FAIL set, every status and the output."""
    result = _run_cli(
        FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_idempotency", cancel_prompt="__hang__"
    )
    statuses = _table_statuses(result.stdout)
    return _fails(statuses), statuses, result.stdout


def test_conforming_agents_pass_idempotency_rows():
    """`conforming_full.py` persists sessions with their history and keys, so a fresh process
    resumes the session, replays the message and still recognizes the key: all eight rows PASS,
    `ACP-PROMPT-218` included. `conforming.py` keeps nothing across processes, so only
    `ACP-PROMPT-218` SKIPs."""
    fails, statuses, out = _idempotency_run("conforming_full.py")
    assert not fails and {statuses[i] for i in _IDEMPOTENCY_IDS} == {"PASS"}, out
    fails, statuses, out = _idempotency_run("conforming.py")
    assert not fails, out
    assert statuses["ACP-PROMPT-218"] == "SKIPPED", out
    assert {statuses[i] for i in _IDEMPOTENCY_IDS - {"ACP-PROMPT-218"}} == {"PASS"}, out


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("retry_inserts_second_message.py", {"ACP-PROMPT-212", "ACP-PROMPT-214"}),
        ("reused_key_rejected_then_forgotten.py", {"ACP-PROMPT-214"}),
        ("accepts_malformed_idempotency_key.py", {"ACP-PROMPT-213"}),
        ("held_retry_rejected_as_duplicate.py", {"ACP-PROMPT-215"}),
        ("echoes_idempotency_key.py", {"ACP-PROMPT-216"}),
        ("key_scoped_across_sessions.py", {"ACP-PROMPT-217"}),
        ("forgets_key_across_connections.py", {"ACP-PROMPT-218"}),
        ("rejected_prompt_records_key.py", {"ACP-PROMPT-219"}),
    ],
)
def test_idempotency_defect_fixtures_fail_only_their_rows(fixture, failing):
    """Each idempotency fixture has one defect and FAILs exactly the rows it names; every other
    idempotency row PASSes or, for `ACP-PROMPT-218` on a fixture that keeps no session across
    processes, SKIPs."""
    fails, statuses, out = _idempotency_run(fixture)
    assert fails == failing, out
    for req_id in _IDEMPOTENCY_IDS - failing:
        assert statuses[req_id] in {"PASS", "SKIPPED"}, f"{req_id}:\n{out}"
    assert statuses["ACP-PROMPT-215"] != "SKIPPED", out


def test_idempotency_held_retry_row_skips_without_a_held_prompt():
    """Without `--cancel-prompt` the short turn ends before the second prompt is read, so
    `ACP-PROMPT-215` SKIPs ("not exercised") instead of passing vacuously."""
    result = _run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k="test_idempotency")
    assert _table_statuses(result.stdout)["ACP-PROMPT-215"] == "SKIPPED", result.stdout
