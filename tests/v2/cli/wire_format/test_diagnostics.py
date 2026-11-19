"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_diagnostics.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def test_error_message_with_newline_fails_error_001_only():
    """`error_message_with_newline.py` appends an embedded newline to the `-32601` error
    message only -- FAILs `ACP-ERROR-001` (ADVISORY) only."""
    result = _run_cli(
        FIXTURES_DIR_V2, "error_message_with_newline.py", protocol_version=2, k="test_diagnostics"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-ERROR-001"}, result.stdout


def test_never_exits_on_stdin_close_fails_shutdown_001_only():
    """`never_exits_on_stdin_close.py` needs SIGTERM/SIGKILL to actually terminate -- FAILs
    `ACP-SHUTDOWN-001` (ADVISORY) only. `--close-grace` is kept small so this self-test doesn't
    pay the default grace period at every rung of the shutdown ladder."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "never_exits_on_stdin_close.py",
        protocol_version=2,
        k="test_diagnostics",
        close_grace="0.2",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SHUTDOWN-001"}, result.stdout


def test_noisy_stderr_and_parse_error_reply_fails_nothing():
    """`noisy_stderr_and_parse_error_reply.py` logs every raw line to stderr and replies with an
    explicit `-32700` to malformed JSON instead of staying silent -- self-test only, exercising
    the non-default branches of `ACP-STDERR-001`/`ACP-INFO-PARSE-001` (both INFORMATIONAL,
    never asserted on the probed behaviour itself) and `ACP-ERROR-204`'s PASS path (a `-32700`
    reply with `id: null`), so this fixture FAILs nothing."""
    result = _run_cli(FIXTURES_DIR_V2, "noisy_stderr_and_parse_error_reply.py", protocol_version=2)
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert statuses.get("ACP-STDERR-001") == "PASS", result.stdout
    assert statuses.get("ACP-INFO-PARSE-001") == "PASS", result.stdout
    assert statuses.get("ACP-ERROR-204") == "PASS", result.stdout
