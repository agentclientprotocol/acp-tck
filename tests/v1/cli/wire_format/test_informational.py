"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_informational.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._expectations import _ALL_IDS, _CANCEL_IDS, _CAPABILITY_GATED_IDS, _INFORMATIONAL_IDS
from .._runner import _TABLE_ROW_RE, _run_cli, _table_statuses


def _table_notes(output: str) -> dict[str, str]:
    """Parse each summary-table row's trailing `(note)` text (empty if none), keyed by id."""
    notes: dict[str, str] = {}
    for line in output.splitlines():
        match = _TABLE_ROW_RE.match(line)
        if match:
            notes[match.group(1)] = line[match.end():].strip()
    return notes


def test_pushes_status_notifications_passes_everything():
    """`pushes_status_notifications.py` pushes an unprompted `_`-prefixed notification right
    after `initialize` and before handling every later line, so one lands in `ACP-JSONRPC-003`'s
    quiet period and ahead of every reply. A notification is not a reply, so the outcome must
    match `conforming.py`'s exactly -- including the `ACP-INFO-*` probes' recorded behaviour,
    which must not mistake the push for the agent's reply."""
    result = _run_cli("pushes_status_notifications.py")
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS | _INFORMATIONAL_IDS, result.stdout
    skip_ids = _CANCEL_IDS | _CAPABILITY_GATED_IDS
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in skip_ids else "PASS"
        assert status == expected, f"{req_id} is {status}, expected {expected}:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    notes = _table_notes(result.stdout)
    for req_id in ("ACP-INFO-PARSE-001", "ACP-INFO-INVALIDREQ-001"):
        assert notes[req_id].startswith("(silent;"), f"{req_id}: {notes[req_id]}"
    for req_id, note in notes.items():
        assert "_fixture/status_update" not in note, f"{req_id}: {note}"
