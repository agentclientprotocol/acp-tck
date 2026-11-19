"""Shared runner for the end-to-end CLI tests under `tests/v1/cli/`: `_run_cli` runs
`python -m tck -- <fixture agent>` as a real subprocess, and the parsers read the
terminal requirement-summary table.

A subprocess (not in-process `pytest.main`) is used deliberately: these tests run under
pytest, and pytest does not support a clean re-entrant `pytest.main()` call from within a
running session.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "agents" / "v1"
FIXTURES_DIR_V2 = Path(__file__).parents[2] / "fixtures" / "agents" / "v2"
CLI_SUBPROCESS_TIMEOUT = 300
"""Wall-clock cap on one `_run_cli` subprocess, only there to report a hung run. A full run takes
well under a minute, but its CPU work (the inner pytest, schema validation, one agent process per
connection) stretches several times over when the suite's workers outnumber the cores actually
free, so the cap leaves that headroom; a run that finishes costs nothing extra."""
CLI_STARTUP_TIMEOUT = "5"
"""`--startup-timeout` for `_run_cli`: the spawn of an agent process and its `initialize` answer,
paid once per connection. A fixture answers in tens of milliseconds, but under CPU starvation a
Python process start alone can approach a second, and a full run opens hundreds of connections.
It does not change any verdict, since every fixture that answers `initialize` answers it at once;
tests whose fixture never answers it pass `startup_timeout="1"` to stay fast."""


def _run_cli(
    fixture: str,
    *,
    fixture_dir: Path | None = None,
    protocol_version: int | None = None,
    k: str | None = None,
    timeout: str = "1",
    report_json: str | None = None,
    test_timeout: str | None = None,
    startup_timeout: str = CLI_STARTUP_TIMEOUT,
    cancel_prompt: str | None = None,
    subagent_prompt: str | None = None,
    subagent_cancel_prompt: str | None = None,
    auth_method: str | None = None,
    allow_logout: bool = False,
    close_grace: str | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "-m",
        "tck",
        "--timeout",
        timeout,
        "--startup-timeout",
        startup_timeout,
    ]
    if protocol_version is not None:
        cmd += ["--protocol-version", str(protocol_version)]
    if test_timeout is not None:
        cmd += ["--test-timeout", test_timeout]
    if k is not None:
        cmd += ["-k", k]
    if report_json is not None:
        cmd += ["--report-json", report_json]
    if cancel_prompt is not None:
        cmd += ["--cancel-prompt", cancel_prompt]
    if subagent_prompt is not None:
        cmd += ["--subagent-prompt", subagent_prompt]
    if subagent_cancel_prompt is not None:
        cmd += ["--subagent-cancel-prompt", subagent_cancel_prompt]
    if auth_method is not None:
        cmd += ["--auth-method", auth_method]
    if allow_logout:
        cmd += ["--allow-logout"]
    if close_grace is not None:
        cmd += ["--close-grace", close_grace]
    cmd += [
        "--",
        sys.executable,
        str((fixture_dir or FIXTURES_DIR) / fixture),
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_SUBPROCESS_TIMEOUT)


_TABLE_ROW_RE = re.compile(r"^\s*(ACP-\S+)\s+(PASS|FAIL|SKIPPED|NOT TESTED)\b")


def _table_statuses(output: str) -> dict[str, str]:
    """Parse `<id> <STATUS>` pairs out of the terminal summary table. The status label is not
    always one token -- `NOT TESTED` is two words (`plugin.py:675`) -- and a row can carry a
    trailing `  (note)` suffix (`_informational_note`), so match the known status labels by
    regex instead of assuming exactly two whitespace-split tokens; without this, `NOT TESTED`
    rows silently vanish from the parsed dict instead of being recorded, and every
    `statuses.get(x) == "PASS"` check elsewhere only works by accident (`None != "PASS"`)."""
    statuses: dict[str, str] = {}
    for line in output.splitlines():
        match = _TABLE_ROW_RE.match(line)
        if match:
            statuses[match.group(1)] = match.group(2).replace("NOT TESTED", "NOT_TESTED")
    return statuses


def _fail_ids(statuses: dict[str, str]) -> set[str]:
    return {req_id for req_id, status in statuses.items() if status == "FAIL"}


def _output_fail_ids(output: str) -> set[str]:
    return {req_id for req_id, status in _table_statuses(output).items() if status == "FAIL"}
