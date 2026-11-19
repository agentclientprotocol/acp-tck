"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_diagnostics.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import re

from .._runner import _fail_ids, _run_cli, _table_statuses


def test_noisy_stderr_and_parse_error_reply_agent_informational_notes():
    """`noisy_stderr_and_parse_error_reply.py` deterministically exercises two INFORMATIONAL
    probes' non-default branches: it logs every line to stderr (ACP-STDERR-001's byte count
    must be > 0) and replies `-32700`/`id: null` to malformed JSON instead of staying silent
    (ACP-INFO-PARSE-001's recorded behaviour must say so) -- proving the terminal table actually
    surfaces a recorded property as a note, not just that the always-PASS scaffolding runs."""
    result = _run_cli("noisy_stderr_and_parse_error_reply.py")
    assert result.returncode == 0, result.stdout + result.stderr

    assert "ACP-STDERR-001" in result.stdout
    assert "ACP-INFO-PARSE-001" in result.stdout
    assert "replied -32700 with id:null" in result.stdout, result.stdout
    assert "stderr byte(s)" in result.stdout, result.stdout
    for line in result.stdout.splitlines():
        if "ACP-STDERR-001" in line:
            match = re.search(r"(\d+) stderr byte\(s\)", line)
            assert match and int(match.group(1)) > 0, result.stdout


def test_invalid_params_internal_error_fails_error_002_advisory_only():
    result = _run_cli("invalid_params_internal_error.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-ERROR-002"}, result.stdout
