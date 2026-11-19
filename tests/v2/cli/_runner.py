"""Shared runner for the end-to-end CLI tests under `tests/v2/cli/`: `_run_cli` runs
`python -m tck --protocol-version 2 -- <fixture agent>` as a real subprocess, and the parsers read the
terminal requirement-summary table.

A subprocess (not in-process `pytest.main`) is used deliberately: these tests run under
pytest, and pytest does not support a clean re-entrant `pytest.main()` call from within a
running session.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from ._expectations import _ALL_IDS, _CONFORMING_EXPECTED_SKIPS


FIXTURES_DIR_V2 = Path(__file__).parents[2] / "fixtures" / "agents" / "v2"
FIXTURES_DIR_V1 = Path(__file__).parents[2] / "fixtures" / "agents" / "v1"
CLI_SUBPROCESS_TIMEOUT = 300
"""Wall-clock cap on one `_run_cli` subprocess, only there to report a hung run. A full run takes
about a minute, but its CPU work (the inner pytest, schema validation, one agent process per
connection) stretches several times over when the suite's workers outnumber the cores actually
free, so the cap leaves that headroom; a run that finishes costs nothing extra."""
CLI_STARTUP_TIMEOUT = "5"
"""`--startup-timeout` for `_run_cli`: the spawn of an agent process and its `initialize` answer,
paid once per connection. A fixture answers in tens of milliseconds, but under CPU starvation a
Python process start alone can approach a second, and a full run opens hundreds of connections.
It does not change any verdict, since every fixture that answers `initialize` answers it at once;
tests whose fixture never answers it pass `startup_timeout="1"` to stay fast."""

_TABLE_ROW_RE = re.compile(r"^\s*(ACP-\S+)\s+(PASS|FAIL|SKIPPED|NOT TESTED)\b")


def _table_statuses(output: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in output.splitlines():
        match = _TABLE_ROW_RE.match(line)
        if match:
            statuses[match.group(1)] = match.group(2).replace("NOT TESTED", "NOT_TESTED")
    return statuses


def _run_cli(
    fixture_dir: Path,
    fixture: str,
    *,
    protocol_version: int | None,
    k: str | None = None,
    timeout: str = "1",
    startup_timeout: str = CLI_STARTUP_TIMEOUT,
    report_json: str | None = None,
    cancel_prompt: str | None = None,
    subagent_prompt: str | None = None,
    subagent_cancel_prompt: str | None = None,
    auth_method: str | None = None,
    allow_logout: bool = False,
    close_grace: str | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "tck", "--timeout", timeout, "--startup-timeout", startup_timeout]
    if protocol_version is not None:
        cmd += ["--protocol-version", str(protocol_version)]
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
    cmd += ["--", sys.executable, str(fixture_dir / fixture)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_SUBPROCESS_TIMEOUT)


def _assert_conforming_baseline(
    result: subprocess.CompletedProcess[str], fixture: str, exercised: set[str] = frozenset()
) -> None:
    """Assert `result` matches `conforming.py`'s own full-run outcome (see its test below):
    every id in `_CONFORMING_EXPECTED_SKIPS` SKIPs, except those in `exercised`, which PASS like
    every other id."""
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    for req_id, status in statuses.items():
        if req_id in _CONFORMING_EXPECTED_SKIPS - exercised:
            assert status == "SKIPPED", (
                f"{req_id} is {status}, expected SKIPPED (not advertised / no permission "
                f"request observed):\n{result.stdout}"
            )
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS for {fixture}:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def _negotiation_fails(fixture: str) -> tuple[set[str], dict[str, str]]:
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="initialize or extensibility")
    assert result.returncode != 0, result.stdout
    statuses = _table_statuses(result.stdout)
    return {req_id for req_id, status in statuses.items() if status == "FAIL"}, statuses


def _fails(statuses: dict[str, str]) -> set[str]:
    return {req_id for req_id, status in statuses.items() if status == "FAIL"}


def _full_run(fixture: str, tmp_path, **kwargs) -> tuple[dict[str, str], dict[str, dict], str]:
    """The whole suite against `fixture`: every row's status, each row's report entry by id, and
    stdout."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2, fixture, protocol_version=2, report_json=str(report_path), **kwargs
    )
    statuses = _table_statuses(result.stdout)
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    return statuses, by_id, result.stdout


def _recorded(by_id: dict[str, dict], req_id: str) -> dict[str, str]:
    (test,) = by_id[req_id]["tests"]
    return test["properties"]


_PERMISSION_FLOW_K = (
    "(test_prompt and not capabilities) or test_permission or patches or cancel"
)


def _resume_statuses(fixture: str, **kwargs: str) -> tuple[dict[str, str], str]:
    """Run only `test_session_capabilities.py` against `fixture`: every row's status, and stdout."""
    result = _run_cli(
        FIXTURES_DIR_V2, fixture, protocol_version=2, k="session_capabilities", **kwargs
    )
    return _table_statuses(result.stdout), result.stdout


# Wide enough to catch a tool-call fixture's cascades into the prompt, cancel, background and
# open-enum rows.
_TOOL_CALL_K = "test_permission or patches or background or test_enums or test_prompt or cancel"


def _fails_for(fixture: str, k: str) -> tuple[set[str], dict[str, str], str]:
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=k)
    statuses = _table_statuses(result.stdout)
    return {r for r, status in statuses.items() if status == "FAIL"}, statuses, result.stdout
