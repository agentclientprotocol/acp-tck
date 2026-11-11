"""End-to-end CLI tests for `--protocol-version 2`: run `python -m tck --protocol-version 2 --
<fixture agent>` as a real subprocess and check the exit code plus the terminal
requirement-summary table. Mirrors `tests/v1/test_cli.py`.

Covers the conforming fixture PASSing everything, one test per defect fixture asserting its
exact FAIL set, and the version-mismatch scenario (a v1 fixture run under
`--protocol-version 2`). `_VERSION_TOLERANT_IDS`, a strict superset of `_NEGOTIATION_IDS`: the
eight connection-level `ACP-JSONRPC-*`/`ACP-TRANSPORT-*` rows are judged identically for an
honestly-negotiating v1 agent forced under `--protocol-version 2`, since their own tests never
drive a v2-shaped `session/prompt` turn (see
`test_v1_conforming_agent_under_protocol_version_2_is_blocked_by_version_mismatch` below).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURES_DIR_V2 = Path(__file__).parent.parent / "fixtures" / "agents" / "v2"
FIXTURES_DIR_V1 = Path(__file__).parent.parent / "fixtures" / "agents" / "v1"
CLI_SUBPROCESS_TIMEOUT = 60

_MANDATORY_IDS = {
    "ACP-INIT-001",
    "ACP-INIT-003",
    "ACP-INIT-201",
    "ACP-INIT-202",
    "ACP-INIT-203",
    "ACP-INIT-204",
    "ACP-INIT-205",
    "ACP-INIT-206",
    "ACP-INIT-207",
    "ACP-INIT-208",
    "ACP-INIT-209",
    "ACP-INIT-210",
    "ACP-INIT-211",
    "ACP-INIT-212",
    "ACP-INIT-213",
    "ACP-INIT-214",
    "ACP-SCHEMA-001",
    "ACP-TRANSPORT-201",
    "ACP-TRANSPORT-002",
    "ACP-TRANSPORT-203",
    "ACP-JSONRPC-001",
    "ACP-JSONRPC-002",
    "ACP-JSONRPC-003",
    "ACP-JSONRPC-004",
    "ACP-JSONRPC-202",
    "ACP-ERROR-202",
    "ACP-CANCEL-210",
    "ACP-CANCEL-211",
    "ACP-AUTH-201",
    "ACP-AUTH-202",
    "ACP-AUTH-206",
    "ACP-AUTH-207",
    "ACP-EXT-001",
    "ACP-EXT-204",
}
_CAPABILITY_IDS = {
    "ACP-ENUM-201",
    "ACP-ENUM-203",
    "ACP-META-203",
    "ACP-SESSION-001",
    "ACP-SESSION-002",
    "ACP-PROMPT-205",
    "ACP-PROMPT-201",
    "ACP-PROMPT-203",
    "ACP-STATE-201",
    "ACP-STATE-202",
    "ACP-STATE-203",
    "ACP-STATE-205",
    "ACP-STATE-206",
    "ACP-STATE-207",
    "ACP-STATE-208",
    "ACP-PROMPT-206",
    "ACP-PROMPT-207",
    "ACP-PROMPT-209",
    "ACP-PROMPT-211",
    "ACP-PROMPTCAP-001",
    "ACP-PROMPTCAP-002",
    "ACP-PROMPTCAP-003",
    "ACP-PROMPTCAP-201",
    "ACP-PERM-201",
    "ACP-PERM-202",
    "ACP-PERM-203",
    "ACP-PERM-002",
    "ACP-CLIENTCAP-201",
    "ACP-CLIENTCAP-202",
    "ACP-CANCEL-201",
    "ACP-CANCEL-202",
    "ACP-CANCEL-203",
    "ACP-CANCEL-205",
    "ACP-CANCEL-206",
    "ACP-CANCEL-207",
    "ACP-CANCEL-208",
    "ACP-CANCEL-209",
    "ACP-CANCEL-212",
    "ACP-CANCEL-214",
    "ACP-SESSION-203",
    "ACP-SESSION-204",
    "ACP-SESSION-208",
    "ACP-RESUME-201",
    "ACP-RESUME-202",
    "ACP-RESUME-203",
    "ACP-RESUME-204",
    "ACP-RESUME-205",
    "ACP-RESUME-206",
    "ACP-RESUME-207",
    "ACP-RESUME-208",
    "ACP-RESUME-209",
    "ACP-RESUME-210",
    "ACP-RESUME-211",
    "ACP-RESUME-212",
    "ACP-RESUME-213",
    "ACP-ERROR-201",
    "ACP-LIST-201",
    "ACP-LIST-202",
    "ACP-LIST-203",
    "ACP-LIST-204",
    "ACP-LIST-205",
    "ACP-LIST-206",
    "ACP-CLOSE-201",
    "ACP-CLOSE-202",
    "ACP-CLOSE-203",
    "ACP-CLOSE-205",
    "ACP-CLOSE-206",
    "ACP-DELETE-201",
    "ACP-DELETE-202",
    "ACP-DELETE-204",
    "ACP-DELETE-205",
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
    "ACP-ADDDIRS-201",
    "ACP-ADDDIRS-202",
    "ACP-ADDDIRS-203",
    "ACP-MCP-203",
    "ACP-FORK-201",
    "ACP-FORK-202",
    "ACP-FORK-203",
    "ACP-FORK-204",
    "ACP-FORK-205",
    "ACP-SYSPROMPT-201",
    "ACP-SYSPROMPT-202",
    "ACP-SYSPROMPT-002",
    "ACP-SYSPROMPT-003",
    "ACP-CONFIG-201",
    "ACP-CONFIG-202",
    "ACP-CONFIG-203",
    "ACP-CONFIG-204",
    "ACP-CONFIG-206",
    "ACP-CONFIG-207",
    "ACP-CONFIG-208",
    "ACP-CONFIG-209",
    "ACP-CONFIG-210",
    "ACP-COMMANDS-201",
    "ACP-AUTH-203",
    "ACP-AUTH-204",
    "ACP-AUTH-208",
    "ACP-AUTH-209",
    "ACP-PATCH-201",
    "ACP-PATCH-203",
    "ACP-PATCH-204",
    "ACP-PATCH-205",
    "ACP-PATCH-206",
    "ACP-PATCH-207",
    "ACP-PATCH-210",
}
_ADVISORY_IDS = {
    "ACP-INIT-215",
    "ACP-STATE-204",
    "ACP-CANCEL-204",
    "ACP-CANCEL-213",
    "ACP-JSONRPC-005",
    "ACP-BATCH-209",
    "ACP-DELETE-203",
    "ACP-CLOSE-204",
    "ACP-CLOSE-207",
    "ACP-CONFIG-211",
    "ACP-CONFIG-212",
    "ACP-SESSION-206",
    "ACP-SESSION-207",
    "ACP-RESUME-214",
    "ACP-RESUME-216",
    "ACP-MCP-204",
    "ACP-MCP-205",
    "ACP-AUTH-205",
    "ACP-AUTH-210",
    "ACP-PATCH-208",
    "ACP-PATCH-209",
    "ACP-PATCH-211",
    "ACP-PATCH-212",
    "ACP-META-001",
    "ACP-META-201",
    "ACP-META-202",
    "ACP-META-204",
    "ACP-ENUM-204",
    "ACP-EXT-201",
    "ACP-EXT-202",
    "ACP-EXT-203",
    "ACP-ERROR-001",
    "ACP-ERROR-203",
    "ACP-ERROR-204",
    "ACP-SHUTDOWN-001",
    "ACP-SCHEMA-002",
}
_INFORMATIONAL_IDS = {
    "ACP-INFO-CONCURRENT-201",
    "ACP-INFO-CANCEL-201",
    "ACP-MCP-201",
    "ACP-MCP-202",
    "ACP-STDERR-001",
    "ACP-INFO-PARSE-001",
    "ACP-INFO-INVALIDREQ-001",
}
_ALL_IDS = _MANDATORY_IDS | _CAPABILITY_IDS | _ADVISORY_IDS | _INFORMATIONAL_IDS

# `ACP-CANCEL-204` (an unconditional record-only probe for cancellation) never PASSes for *any*
# fixture; it always SKIPs -- except that `ACP-CANCEL-204` FAILs instead of
# SKIPping against a fixture that hangs forever on `session/cancel` (`cancel_no_idle.py` and its
# siblings): an uncaught `AgentTimeout` in shared setup is a FAIL, not a SKIP, so "always" here
# means "for any fixture that lets the turn reach a terminating idle", not literally always.
#
# `ACP-INIT-208` only judges a result that selects v1, which a v2-only fixture never returns (it
# rejects v1 with -32022), so it SKIPs for every `_base.py` fixture except the dual-stack ones.
_V2_ONLY_SKIP_IDS = {"ACP-INIT-208"}
_ALWAYS_SKIPPED_IDS = {"ACP-CANCEL-204"} | _V2_ONLY_SKIP_IDS

# CAPABILITY-tier cancel rows that need a turn to still be in flight when `session/cancel` is
# sent to be exercised at all -- against a fast fixture with no `--cancel-prompt` override the
# turn routinely resolves before the TCK can act, so these legitimately SKIP ("cancellation not
# exercised") rather than PASS. `ACP-CANCEL-205` (no direct response to the cancel notification
# itself) holds regardless of the race outcome, so it is not in this set. `ACP-CLOSE-202` shares
# `ACP-CANCEL-208`'s exact test (`test_close_cancels_foreground_work`), so it races the same way;
# `ACP-CLOSE-203` drives the same close-mid-turn scenario and SKIPs unless the turn ended
# `cancelled`. `ACP-PROMPT-209`/`ACP-CANCEL-214`/`ACP-INFO-CONCURRENT-201` need the first turn
# still active when the second prompt is read, so they SKIP for the same reason.
_CANCEL_RACE_SKIP_IDS = {
    "ACP-CANCEL-201",
    "ACP-CANCEL-202",
    "ACP-CANCEL-203",
    "ACP-CANCEL-206",
    "ACP-CANCEL-207",
    "ACP-CANCEL-208",
    "ACP-CANCEL-214",
    "ACP-ARCHIVE-201",
    "ACP-CLOSE-202",
    "ACP-CLOSE-203",
    "ACP-DELETE-204",
    "ACP-INFO-CONCURRENT-201",
    "ACP-PROMPT-209",
}

# The background-work rows judge only an agent that reports a `background` list, which no
# `_base.py` fixture does unless it opts into `report_background_work`
# (`reports_background_work.py` and the `background_*.py` defect fixtures).
_BACKGROUND_SKIP_IDS = {"ACP-STATE-206", "ACP-STATE-207", "ACP-STATE-208"}

# `ACP-RESUME-213` judges only a resume snapshot that lists background work, and SKIPs otherwise.
# Only a fixture with `background_on_resume` (`resume_lists_background_work.py` and its defect
# sibling) leaves live work at resume; no other fixture does, not even
# `reports_background_work.py`, whose turns finish their work before they end.
_RESUME_BACKGROUND_SKIP_IDS = {"ACP-RESUME-213"}

# `ACP-PROMPTCAP-001/002/003` SKIP whenever the agent doesn't advertise the corresponding
# `capabilities.session.prompt.*` marker, and `ACP-PERM-201`/`202` SKIP whenever a turn never
# actually triggers a `session/request_permission` (`ACP-PERM-203`/`002` also need a `tool_call`
# subject) -- both legitimate, expected SKIPs (not
# FAILs) for a fixture that neither advertises nor exercises them.
#
# A fixture that never opts into `_base.py`'s `_send_rich_turn_updates` (`emit_rich_turn_updates`
# defaults to `False`) never emits a tool_call_update/plan_update/terminal_update/
# terminal_output_chunk at all, and never asks for permission either -- so these all legitimately
# SKIP ("no <variant> observed") rather than PASS, exactly as they do for `conforming.py` itself
# (see `test_v2_conforming_agent_passes_everything` above).
_NOT_ADVERTISED_OR_EXERCISED_SKIP_IDS = {
    "ACP-JSONRPC-202",
    "ACP-ERROR-204",  # the fixture stays silent on a non-JSON line
    "ACP-PROMPTCAP-001",
    "ACP-PROMPTCAP-002",
    "ACP-PROMPTCAP-003",
    "ACP-PERM-201",
    "ACP-PERM-202",
    "ACP-PERM-203",
    "ACP-PERM-002",
    "ACP-ENUM-203",
    "ACP-ENUM-204",
    "ACP-META-203",
    "ACP-META-204",
    "ACP-PATCH-204",
    "ACP-PATCH-205",
    "ACP-PATCH-206",
    "ACP-PATCH-207",
    "ACP-PATCH-208",
    "ACP-PATCH-209",
    "ACP-PATCH-210",
    "ACP-PATCH-211",
    "ACP-PATCH-212",
    "ACP-STATE-205",
    "ACP-CANCEL-209",
    "ACP-CANCEL-213",
    "ACP-CLOSE-205",
    "ACP-PROMPT-207",
} | _BACKGROUND_SKIP_IDS | _RESUME_BACKGROUND_SKIP_IDS

# A fixture that advertises only the bare `capabilities: {"session": {}}}` baseline (or nothing
# session-related at all) legitimately SKIPs the session-management extras below -- `delete`,
# `additionalDirectories`, `mcp`, `fork`, `systemPrompt`, and `configOptions` (inferred from
# `session/new`'s own result, not a capability marker) -- exactly as it does for `conforming.py`
# itself (see
# `test_v2_conforming_agent_passes_everything` above). `ACP-SESSION-203`/`ACP-RESUME-*`/
# `ACP-LIST-*`/`ACP-CLOSE-201` are NOT in this set: they are gated on the baseline
# `capabilities.session` marker alone, present even as `{}`.
_SESSION_MGMT_EXTRAS_SKIP_IDS = {
    "ACP-DELETE-201",
    "ACP-DELETE-202",
    "ACP-DELETE-203",
    "ACP-DELETE-204",
    "ACP-DELETE-205",
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
    "ACP-ADDDIRS-201",
    "ACP-ADDDIRS-202",
    "ACP-ADDDIRS-203",
    "ACP-MCP-201",
    "ACP-MCP-202",
    "ACP-MCP-204",
    "ACP-MCP-205",
    "ACP-FORK-201",
    "ACP-FORK-202",
    "ACP-FORK-203",
    "ACP-FORK-204",
    "ACP-FORK-205",
    "ACP-SYSPROMPT-201",
    "ACP-SYSPROMPT-202",
    "ACP-SYSPROMPT-002",
    "ACP-SYSPROMPT-003",
    "ACP-CONFIG-201",
    "ACP-CONFIG-202",
    "ACP-CONFIG-203",
    "ACP-CONFIG-204",
    "ACP-CONFIG-206",
    "ACP-CONFIG-207",
    "ACP-CONFIG-208",
    "ACP-CONFIG-209",
    "ACP-CONFIG-210",
    "ACP-CONFIG-211",
    "ACP-CONFIG-212",
    "ACP-COMMANDS-201",
    "ACP-RESUME-210",  # neither `configOptions` nor `availableCommands` to carry over
}

# A fixture that advertises no `authMethods` and no `capabilities.auth.status`, run with no
# `--auth-method`/`--allow-logout`, legitimately SKIPs these ids: `ACP-AUTH-203`/`204`/`208`/`210`
# all need `authMethods` non-empty (`203` additionally needs `--allow-logout`); `ACP-AUTH-207`
# needs a `type: "terminal"` entry to appear on a dedicated connection advertising
# `capabilities.auth.terminal`; `ACP-AUTH-209` needs `capabilities.auth.status`.
# `ACP-AUTH-201`/`206` also SKIP here: with no `authMethods` advertised at all there is nothing
# to check uniqueness/type-shape of, and a MANDATORY/ADVISORY row SKIPping on "nothing to check"
# is more honest than a vacuous PASS. `ACP-AUTH-202`/`205` are NOT in this set: each is judged
# against the empty-`authMethods` case itself and PASSes.
_NO_AUTH_SKIP_IDS = {
    "ACP-AUTH-201",
    "ACP-AUTH-203",
    "ACP-AUTH-204",
    "ACP-AUTH-206",
    "ACP-AUTH-207",
    "ACP-AUTH-208",
    "ACP-AUTH-209",
    "ACP-AUTH-210",
}

_TABLE_ROW_RE = re.compile(r"^\s*(ACP-\S+)\s+(PASS|FAIL|SKIPPED|NOT TESTED)\b")


def _table_statuses(output: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for line in output.splitlines():
        match = _TABLE_ROW_RE.match(line)
        if match:
            statuses[match.group(1)] = match.group(2).replace("NOT TESTED", "NOT_TESTED")
    return statuses


def _table_notes(output: str) -> dict[str, str]:
    """Parse each summary-table row's trailing `(note)` text (empty if none), keyed by id."""
    notes: dict[str, str] = {}
    for line in output.splitlines():
        match = _TABLE_ROW_RE.match(line)
        if match:
            notes[match.group(1)] = line[match.end():].strip()
    return notes


def _run_cli(
    fixture_dir: Path,
    fixture: str,
    *,
    protocol_version: int | None,
    k: str | None = None,
    timeout: str = "1",
    startup_timeout: str = "1",
    report_json: str | None = None,
    cancel_prompt: str | None = None,
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
    if auth_method is not None:
        cmd += ["--auth-method", auth_method]
    if allow_logout:
        cmd += ["--allow-logout"]
    if close_grace is not None:
        cmd += ["--close-grace", close_grace]
    cmd += ["--", sys.executable, str(fixture_dir / fixture)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_SUBPROCESS_TIMEOUT)


def test_help_mentions_protocol_version_option():
    result = subprocess.run(
        [sys.executable, "-m", "tck", "--help"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "--protocol-version" in result.stdout


_CONFORMING_EXPECTED_SKIPS = {
    "ACP-JSONRPC-202",
    "ACP-ERROR-204",
    "ACP-PROMPTCAP-001",
    "ACP-PROMPTCAP-002",
    "ACP-PROMPTCAP-003",
    "ACP-PERM-201",
    "ACP-PERM-202",
    "ACP-PERM-203",
    "ACP-PERM-002",
    "ACP-DELETE-201",
    "ACP-DELETE-202",
    "ACP-DELETE-203",
    "ACP-DELETE-204",
    "ACP-DELETE-205",
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
    "ACP-ADDDIRS-201",
    "ACP-ADDDIRS-202",
    "ACP-ADDDIRS-203",
    "ACP-MCP-201",
    "ACP-MCP-202",
    "ACP-MCP-204",
    "ACP-MCP-205",
    "ACP-CONFIG-201",
    "ACP-CONFIG-202",
    "ACP-CONFIG-203",
    "ACP-CONFIG-204",
    "ACP-CONFIG-206",
    "ACP-CONFIG-207",
    "ACP-CONFIG-208",
    "ACP-CONFIG-209",
    "ACP-CONFIG-210",
    "ACP-CONFIG-211",
    "ACP-CONFIG-212",
    "ACP-COMMANDS-201",
    "ACP-RESUME-210",
    "ACP-FORK-201",
    "ACP-FORK-202",
    "ACP-FORK-203",
    "ACP-FORK-204",
    "ACP-FORK-205",
    "ACP-SYSPROMPT-201",
    "ACP-SYSPROMPT-202",
    "ACP-SYSPROMPT-002",
    "ACP-SYSPROMPT-003",
    "ACP-AUTH-201",
    "ACP-AUTH-203",
    "ACP-AUTH-204",
    "ACP-AUTH-206",
    "ACP-AUTH-207",
    "ACP-AUTH-208",
    "ACP-AUTH-209",
    "ACP-AUTH-210",
    "ACP-ENUM-203",
    "ACP-ENUM-204",
    "ACP-META-203",
    "ACP-META-204",
    "ACP-PATCH-204",
    "ACP-PATCH-205",
    "ACP-PATCH-206",
    "ACP-PATCH-207",
    "ACP-PATCH-208",
    "ACP-PATCH-209",
    "ACP-PATCH-210",
    "ACP-PATCH-211",
    "ACP-PATCH-212",
    "ACP-STATE-205",
    "ACP-CANCEL-209",
    "ACP-CANCEL-213",
    "ACP-CLOSE-205",
    "ACP-PROMPT-207",
} | _BACKGROUND_SKIP_IDS | _RESUME_BACKGROUND_SKIP_IDS | _CANCEL_RACE_SKIP_IDS | _ALWAYS_SKIPPED_IDS


def _assert_conforming_baseline(result: subprocess.CompletedProcess[str], fixture: str) -> None:
    """Assert `result` matches `conforming.py`'s own full-run outcome (see its test below):
    every id in `_CONFORMING_EXPECTED_SKIPS` SKIPs, every other id PASSes."""
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    for req_id, status in statuses.items():
        if req_id in _CONFORMING_EXPECTED_SKIPS:
            assert status == "SKIPPED", (
                f"{req_id} is {status}, expected SKIPPED (not advertised / no permission "
                f"request observed):\n{result.stdout}"
            )
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS for {fixture}:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_v2_conforming_agent_passes_everything():
    """`conforming.py` advertises only the plain `session: {}` baseline -- no prompt-content
    capabilities, no `delete`/`archive`/`additionalDirectories`/`mcp`/`fork`/`systemPrompt` marker, no
    `configOptions`, no
    `authMethods`, and it never asks for permission or opts into `_send_rich_turn_updates`. So
    every capability row that needs more than that SKIPs rather than PASSes:
    `ACP-PROMPTCAP-001/002/003` ("not advertised"), `ACP-PERM-201..203`/`ACP-PERM-002` ("no
    permission request observed"), `ACP-DELETE-201..205`/`ACP-ARCHIVE-002..006,201`/`ACP-ADDDIRS-201/202`/`ACP-MCP-201/202`/
    `ACP-FORK-201..205`/`ACP-SYSPROMPT-201/202`/`ACP-CONFIG-201..204,206` (session-management
    extras absent), `ACP-AUTH-203/204/207` (no
    `authMethods`, no `--auth-method`/`--allow-logout`), and `ACP-ENUM-203`/
    `ACP-PATCH-204..212` (no rich turn updates, no permission request). `ACP-PATCH-201/203` and
    `ACP-ENUM-201` still PASS: the ordinary message-chunk/state-update traffic every turn already
    emits is enough to exercise them. `ACP-SESSION-203`/`ACP-RESUME-201..209`/
    `ACP-LIST-201..206`/`ACP-CLOSE-201`/`ACP-CLOSE-204` are gated on the baseline `capabilities.session` marker
    alone (present even as `{}`), so they PASS. `ACP-AUTH-202`/`205` PASS too -- each is judged
    against the absence of `authMethods`; `ACP-AUTH-201`/`206` SKIP instead of vacuously passing,
    since there is nothing to check uniqueness/type-shape of.

    Without a `--cancel-prompt` override, `conforming.py`'s short deterministic turns routinely
    resolve before the TCK can act on `session/cancel` at all, so `_CANCEL_RACE_SKIP_IDS`
    (including `ACP-CLOSE-202`/`203`, which drive the same race-prone close-mid-turn scenario)
    legitimately SKIP too ("cancellation not exercised") -- `ACP-CANCEL-205` (no direct response
    to the cancel notification itself) still PASSes regardless of that race, and
    `_ALWAYS_SKIPPED_IDS` SKIP unconditionally for any fixture. Every other id PASSes. See
    `conforming_full.py`'s own self-test below (with `--cancel-prompt __hang__`) for the "every
    exercisable id PASSes" fixture."""
    result = _run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2)
    _assert_conforming_baseline(result, "conforming.py")


# What `conforming_full.py` still SKIPs besides `_ALWAYS_SKIPPED_IDS`: `ACP-AUTH-205` (only
# concerns the empty-`authMethods` case), `ACP-PROMPT-207` (it never rejects a prompt), and
# `ACP-CANCEL-209`/`213` and `ACP-CLOSE-205` (`__hang__` preempts its permission request, so none
# is pending at cancel or close; `asks_permission.py`'s self-test exercises them instead), and
# `ACP-META-203/204` (it emits no
# `_meta` at all; `emits_w3c_meta.py` exercises them), and `_BACKGROUND_SKIP_IDS` (it reports
# no background work; `reports_background_work.py` exercises them).
# `ACP-ERROR-204` SKIPs for every `_base.py` fixture that stays silent on a non-JSON line.
_FULL_EXPECTED_SKIPS = {
    "ACP-AUTH-205",
    "ACP-PROMPT-207",
    "ACP-PROMPTCAP-201",  # every prompt capability is advertised, so no negative case applies
    "ACP-CANCEL-209",
    "ACP-CANCEL-213",
    "ACP-CLOSE-205",
    "ACP-ERROR-204",
    "ACP-META-203",
    "ACP-META-204",
} | _BACKGROUND_SKIP_IDS | _RESUME_BACKGROUND_SKIP_IDS


def test_v2_conforming_full_agent_passes_everything():
    """`conforming_full.py` advertises `capabilities.session.prompt.{image,audio,
    embeddedContext}`, asks for permission with a `tool_call` subject on every turn
    (`AsksPermissionAgent`, `permission_tool_call=True`), opts into
    `_send_rich_turn_updates` (two message chunks sharing one `messageId`, one tool_call
    create+patch sharing one `toolCallId`, one plan_update with one `planId`), and advertises one
    `type: "agent"` authMethods entry (`methodId: "tck"`). Run with `--cancel-prompt __hang__
    --auth-method tck --allow-logout`, this exercises essentially every capability: every
    prompt-content/permission/client-capability id, `ACP-PATCH-201/203..212` and
    `ACP-ENUM-201/203`, `ACP-AUTH-203/204`, and every CAPABILITY-tier `ACP-CANCEL-*` id but
    `ACP-CANCEL-209` all PASS. The INFORMATIONAL probe PASSes too (an INFORMATIONAL test PASSes as
    long as it never hits an assertion failure or setup/teardown error -- it never asserts on the
    behaviour it probes, only records it).

    `conforming_full.py` also advertises a `type: "terminal"` auth method on any connection that
    advertises `capabilities.auth.terminal` (`ACP-AUTH-202` still PASSes since that descriptor
    never appears on the default connection this fixture also answers), and emits one
    `terminal_update` + one `terminal_output_chunk` per turn under the same
    `emit_rich_turn_updates` flag -- so `ACP-AUTH-207`/`ACP-PATCH-206`/`ACP-PATCH-207` all PASS
    too, instead of SKIPping "nothing to check"/"no <variant> observed".

    `_FULL_EXPECTED_SKIPS` still legitimately SKIP (see its comment), and `_ALWAYS_SKIPPED_IDS`
    (permanently unobservable record-only probes) SKIP regardless."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "conforming_full.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        auth_method="tck",
        allow_logout=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    expected_skips = _ALWAYS_SKIPPED_IDS | _FULL_EXPECTED_SKIPS
    for req_id, status in statuses.items():
        if req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS for conforming_full.py:\n{result.stdout}"
    assert statuses["ACP-INFO-CONCURRENT-201"] == "PASS", result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_v2_conforming_full_agent_without_allow_logout_only_skips_auth_203():
    """Acceptance criterion: the same `conforming_full.py --auth-method tck` run, but WITHOUT
    `--allow-logout`, must SKIP ONLY `ACP-AUTH-203` in addition to the baseline's own SKIPs
    (`_ALWAYS_SKIPPED_IDS` plus `ACP-AUTH-205`, per
    `test_v2_conforming_full_agent_passes_everything` above) -- every other id keeps the exact
    same status. `ACP-AUTH-204` still PASSes here since `--auth-method tck` alone is enough to
    exercise `auth/login`; only `auth/logout` (`ACP-AUTH-203`) requires the separate
    `--allow-logout` opt-in."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "conforming_full.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        auth_method="tck",
        allow_logout=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    expected_skips = _ALWAYS_SKIPPED_IDS | _FULL_EXPECTED_SKIPS | {"ACP-AUTH-203"}
    for req_id, status in statuses.items():
        if req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS without --allow-logout:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_asks_permission_fixture_passes_perm_201_but_skips_promptcap():
    """`asks_permission.py` isolates `ACP-PERM-201` from `conforming_full.py`'s broader
    capability set: it asks for permission on every turn but advertises no prompt-content
    capabilities at all, so `ACP-PERM-201` PASSes while `ACP-PROMPTCAP-001/002/003` still SKIP
    ("not advertised").

    Perf note: scoped with `-k` to `test_permission.py` (owns `ACP-PERM-201`) plus
    `test_prompt_capabilities.py` (owns `ACP-PROMPTCAP-001/002/003`) -- everything else is
    deselected (`NOT_TESTED`) rather than re-verified here. The exit code/overall verdict text
    are not asserted for the same reason as `test_calls_custom_method_passes_everything_it_can`
    above: `-k` scoping necessarily leaves every other MANDATORY id `NOT_TESTED`, which flips the
    verdict to NOT CONFORMANT by design regardless of how the exercised ids actually behave."""
    result = _run_cli(
        FIXTURES_DIR_V2, "asks_permission.py", protocol_version=2, k="test_permission or prompt_capabilities"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert statuses.get("ACP-PERM-201") == "PASS", result.stdout
    for req_id in ("ACP-PROMPTCAP-001", "ACP-PROMPTCAP-002", "ACP-PROMPTCAP-003"):
        assert statuses.get(req_id) == "SKIPPED", result.stdout


# --- prompt content capabilities, the permission flow, and the agent->client method rules --
# defect fixtures ---


def test_rejects_image_when_advertised_fails_promptcap_001_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "rejects_image_when_advertised.py", protocol_version=2, k="prompt_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PROMPTCAP-001"}, result.stdout
    assert statuses.get("ACP-PROMPTCAP-002") == "PASS", result.stdout
    assert statuses.get("ACP-PROMPTCAP-003") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_calls_elicitation_unadvertised_fails_clientcap_201_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "calls_elicitation_unadvertised.py", protocol_version=2, k="client_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLIENTCAP-201"}, result.stdout
    assert statuses.get("ACP-CLIENTCAP-202") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_sends_undefined_client_notification_fails_clientcap_202_only():
    """`run_prompt`'s driver records agent -> client *requests and notifications* alike on
    `PromptTurn.client_requests_seen`, so a notification using an undefined method name cannot
    silently escape `ACP-CLIENTCAP-202`'s check -- its own text claims "request/notification"
    coverage. `sends_undefined_client_notification.py` fires
    exactly that -- a notification, no `id`, method name `made_up/notify` -- and nothing else."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "sends_undefined_client_notification.py",
        protocol_version=2,
        k="client_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLIENTCAP-202"}, result.stdout
    assert statuses.get("ACP-CLIENTCAP-201") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_calls_fs_unadvertised_fails_clientcap_202_only():
    """`fs/read_text_file` is not a known v2 agent->client method at all (`fs/*`/`terminal/*`
    were removed from v2), so it also cascades into `ACP-SCHEMA-001`'s general "every agent
    message validates against the schema" check -- the same documented
    defect-cascades-into-schema-validation pattern as `ACP-INIT-204` (see
    `tck.v2.requirements`'s module docstring), not a separate bug."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "calls_fs_unadvertised.py",
        protocol_version=2,
        k="client_capabilities or initialize",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLIENTCAP-202", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-CLIENTCAP-201") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_calls_custom_method_passes_everything_it_can():
    """Positive control for the `_`-prefix open-enum rule on agent -> client methods, paired
    with `calls_fs_unadvertised.py`'s negative control. Advertises only the plain `session: {}}`
    baseline, so `ACP-PROMPTCAP-001/002/003`/`ACP-PERM-201` still SKIP -- this fixture is a
    control for `ACP-CLIENTCAP-201/202` specifically, not a full `conforming_full.py`-style
    all-PASS fixture. The exit code/overall verdict text are not asserted here: this run is
    `-k`-scoped, which necessarily leaves every other MANDATORY id NOT_TESTED, and NOT_TESTED
    MANDATORY ids do flip the verdict to NOT CONFORMANT by design (see
    `tests/v1/test_cli.py`'s `test_hangs_until_cancel_agent_passes_cancel_requirements` for the
    same precedent) -- that says nothing about whether *this* fixture's behaviour for the ids
    actually exercised is conforming, which is what the per-id statuses below check."""
    result = _run_cli(
        FIXTURES_DIR_V2, "calls_custom_method.py", protocol_version=2, k="client_capabilities"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert statuses.get("ACP-CLIENTCAP-201") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-202") == "PASS", result.stdout


def test_v2_report_json_reads_the_v2_shaped_initialize_result(tmp_path):
    """`--report-json` for a real v2 run must carry `protocol_version == 2` and read
    `agent_info`/`agent_capabilities` from the v2-renamed `info`/`capabilities` keys
    (`tck.common.version.VersionSpec.agent_info_field`/`agent_capabilities_field` -- see
    `tests/common/test_version.py` for the mechanism itself in isolation)."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2, "conforming.py", protocol_version=2, report_json=str(report_path)
    )
    assert result.returncode == 0, result.stdout + result.stderr

    report = json.loads(report_path.read_text())
    assert report["protocol_version"] == 2
    assert report["agent_info"] == {"name": "tck-fixture-conforming-v2", "version": "0.0.0"}
    assert report["agent_capabilities"] == {"session": {}}
    assert report["verdict"]["conformant"] is True


def test_v2_missing_agent_command_is_an_error():
    result = subprocess.run(
        [sys.executable, "-m", "tck", "--protocol-version", "2"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0


def test_default_protocol_version_still_runs_the_v1_suite_unchanged():
    """No `--protocol-version` given at all -- must run the v1 suite, against the v1 conforming
    fixture."""
    result = _run_cli(FIXTURES_DIR_V1, "conforming.py", protocol_version=None)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert "ACP-INIT-002" in result.stdout, "expected the v1 registry's ids, not v2's"


def test_explicit_protocol_version_1_matches_the_default():
    result = _run_cli(FIXTURES_DIR_V1, "conforming.py", protocol_version=1)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


# --- defect fixtures: each must FAIL exactly its intended requirement id(s) ---


def test_echoes_any_version_fails_init_003_only():
    """`echoes_any_version.py` echoes any requested `protocolVersion` above 2, including the
    `65535` probe -- fails `ACP-INIT-003` (must select its own highest version, not echo).
    `ACP-INIT-201` PASSes: its equality check only applies when the `65535` probe selects a
    version <= 2. It advertises `capabilities: {"session": {}}` like `conforming.py`, so
    `ACP-SESSION-001/002` PASS -- `session/new` itself is unmodified and correct."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "echoes_any_version.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-003"}, result.stdout
    assert statuses.get("ACP-INIT-201") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_only_errors_on_v1_fails_init_202_only():
    """`v2_only_errors_on_v1.py` answers `initialize(1)` with `-32602` instead of `-32022` --
    fails only `ACP-INIT-202` (1 is well-formed; `-32602` is reserved for a malformed
    `protocolVersion`). `ACP-INIT-205` still PASSes on its `protocolVersion: 0` probe. It
    advertises `capabilities: {"session": {}}` like `conforming.py`, so `ACP-SESSION-001/002`
    PASS."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "v2_only_errors_on_v1.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-202"}, result.stdout
    assert statuses.get("ACP-INIT-205") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def _negotiation_fails(fixture: str) -> tuple[set[str], dict[str, str]]:
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="initialize or extensibility")
    assert result.returncode != 0, result.stdout
    statuses = _table_statuses(result.stdout)
    return {req_id for req_id, status in statuses.items() if status == "FAIL"}, statuses


def test_v2_only_honest_fails_init_202_and_205():
    """`v2_only_honest.py` selects 2 for every well-formed request, including 1 and 0 -- a
    version higher than requested, where `-32022` is required."""
    fails, statuses = _negotiation_fails("v2_only_honest.py")
    assert fails == {"ACP-INIT-202", "ACP-INIT-205"}, statuses


def test_unsupported_version_bad_data_fails_init_205_only():
    """`unsupported_version_bad_data.py`'s `-32022` lacks `data.supported`; `ACP-INIT-202` only
    judges the code, so it PASSes."""
    fails, statuses = _negotiation_fails("unsupported_version_bad_data.py")
    assert fails == {"ACP-INIT-205"}, statuses
    assert statuses.get("ACP-INIT-202") == "PASS", statuses


def test_accepts_string_version_fails_init_206_only():
    fails, statuses = _negotiation_fails("accepts_string_version.py")
    assert fails == {"ACP-INIT-206"}, statuses


def test_starts_session_after_mismatch_fails_init_207_and_209():
    """The `session/new` after `-32022` succeeds: `ACP-INIT-207` (session work began) and
    `ACP-INIT-209` (the request was not answered `-32600`)."""
    fails, statuses = _negotiation_fails("starts_session_after_mismatch.py")
    assert fails == {"ACP-INIT-207", "ACP-INIT-209"}, statuses
    assert statuses.get("ACP-INIT-205") == "PASS", statuses


def test_serves_before_initialize_fails_init_209_and_207():
    """Never refusing a request also lets the `session/new` after `-32022` succeed
    (`ACP-INIT-207`)."""
    fails, statuses = _negotiation_fails("serves_before_initialize.py")
    assert fails == {"ACP-INIT-207", "ACP-INIT-209"}, statuses


def test_notifies_before_initialize_fails_init_210_only():
    fails, statuses = _negotiation_fails("notifies_before_initialize.py")
    assert fails == {"ACP-INIT-210"}, statuses


def test_no_retry_after_failed_initialize_fails_init_211_only():
    """It also answers `-32600` to a pre-initialize request, so `ACP-INIT-209` PASSes."""
    fails, statuses = _negotiation_fails("no_retry_after_failed_initialize.py")
    assert fails == {"ACP-INIT-211"}, statuses
    assert statuses.get("ACP-INIT-209") == "PASS", statuses


def test_rejects_repeated_initialize_fails_init_212_only():
    """A second `initialize` is rejected (`-32600`) before any other request: `ACP-INIT-212`
    FAILs, but a repeat after another request must be rejected too, so `ACP-INIT-213` PASSes."""
    fails, statuses = _negotiation_fails("rejects_repeated_initialize.py")
    assert fails == {"ACP-INIT-212"}, statuses
    assert statuses.get("ACP-INIT-213") == "PASS", statuses


def test_accepts_initialize_after_request_fails_init_213_only():
    """`ACP-INIT-215` SKIPs: there is no error whose code it could check."""
    fails, statuses = _negotiation_fails("accepts_initialize_after_request.py")
    assert fails == {"ACP-INIT-213"}, statuses
    assert statuses.get("ACP-INIT-215") == "SKIPPED", statuses
    assert statuses.get("ACP-INIT-212") == "PASS", statuses


def test_late_initialize_wrong_code_fails_init_215_only():
    """`-32602` instead of `-32600`: a rejection, so the MANDATORY `ACP-INIT-213` PASSes and
    only the ADVISORY code row fails."""
    fails, statuses = _negotiation_fails("late_initialize_wrong_code.py")
    assert fails == {"ACP-INIT-215"}, statuses
    assert statuses.get("ACP-INIT-213") == "PASS", statuses


def test_rejects_unparseable_newer_params_fails_init_214_only():
    fails, statuses = _negotiation_fails("rejects_unparseable_newer_params.py")
    assert fails == {"ACP-INIT-214"}, statuses


def test_dual_v2_shape_on_v1_fails_init_208_only():
    """`dual_v2_shape_on_v1.py` selects 1 for a v1 request (so `ACP-INIT-202` PASSes) but answers
    with v2's `info`/`capabilities`."""
    fails, statuses = _negotiation_fails("dual_v2_shape_on_v1.py")
    assert fails == {"ACP-INIT-208"}, statuses
    assert statuses.get("ACP-INIT-202") == "PASS", statuses


def test_rejects_unknown_capability_fields_fails_ext_204_only():
    fails, statuses = _negotiation_fails("rejects_unknown_capability_fields.py")
    assert fails == {"ACP-EXT-204"}, statuses


def test_conforming_dual_agent_passes_everything():
    """`conforming_dual.py` selects v1 (with a v1-shaped result) for a v1 request and rejects 0
    with `supported: [1, 2]`: the positive control for `ACP-INIT-202`'s result path and
    `ACP-INIT-208`, which PASS instead of SKIPping. Otherwise identical to `conforming.py`."""
    result = _run_cli(FIXTURES_DIR_V2, "conforming_dual.py", protocol_version=2)
    assert result.returncode == 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, result.stdout
    expected_skips = _CONFORMING_EXPECTED_SKIPS - _V2_ONLY_SKIP_IDS
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in expected_skips else "PASS"
        assert status == expected, f"{req_id} is {status}, expected {expected}:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_no_session_capability_agent_is_conformant(tmp_path):
    """`no_session_capability.py` advertises `capabilities: {}` and answers `session/*` with
    `-32601`. Only `initialize` is unconditional in v2, so every MANDATORY row PASSes (falling
    back to `_`-prefixed probes where it would otherwise use a session) or SKIPs for lack of
    evidence, and every session row SKIPs "not advertised"."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "no_session_capability.py",
        protocol_version=2,
        report_json=str(report_path),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    # ACP-JSONRPC-202 SKIPs: without `capabilities.session` no prompt turn can elicit requests.
    # ACP-AUTH-201/206/207 SKIP: this fixture advertises no `authMethods` to check.
    no_pass = {"ACP-AUTH-201", "ACP-AUTH-206", "ACP-AUTH-207", "ACP-JSONRPC-202"} | _V2_ONLY_SKIP_IDS
    for req_id in _MANDATORY_IDS - no_pass:
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert statuses.get("ACP-JSONRPC-202") == "SKIPPED", result.stdout
    report = json.loads(report_path.read_text())
    by_id = {r["id"]: r for r in report["requirements"]}
    for req_id in ("ACP-SESSION-001", "ACP-ENUM-203", "ACP-PROMPT-201", "ACP-CONFIG-201"):
        assert by_id[req_id]["status"] == "SKIPPED", by_id[req_id]
        assert all("not advertised" in t["message"] for t in by_id[req_id]["tests"]), by_id[req_id]


def test_login_method_not_found_fails_auth_204_only():
    """`login_method_not_found.py` advertises `authMethods` but answers `auth/login` with
    `-32601`, which an agent advertising `authMethods` MUST NOT do."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "login_method_not_found.py",
        protocol_version=2,
        k="authentication",
        auth_method="tck",
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-204"}, result.stdout


def test_missing_info_fails_init_203_and_schema_001_only():
    """`missing_info.py` omits the required `info` field entirely -- fails `ACP-INIT-203` (`info`
    is REQUIRED in v2) and `ACP-SCHEMA-001` (the same missing-required-property schema
    violation). `ACP-INIT-001` still PASSes: it only asserts `initialize` returned a non-error
    result (this fixture still does), never the result's shape. It advertises
    `capabilities: {"session": {}}` like `conforming.py`, so `ACP-SESSION-001/002` PASS."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "missing_info.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-203", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-INIT-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_boolean_session_capability_fails_init_204_and_schema_001_only():
    """`boolean_session_capability.py` advertises `capabilities.session: true` (a boolean, not an
    object marker) -- fails `ACP-SCHEMA-001` (schema violation) and `ACP-INIT-204` (capability
    markers must be objects). `ACP-INIT-001` still PASSes (non-error result only), and
    `ACP-SESSION-001`/`002` still PASS: the underlying `session/new` handler works fine and
    `capability_is_supported` treats `true` as advertised."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "boolean_session_capability.py",
        protocol_version=2,
        k="initialize or (test_session and not capabilities and not config)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-INIT-204", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-INIT-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert statuses.get("ACP-SESSION-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_duplicate_session_id_fails_session_002_only():
    """`duplicate_session_id.py` always returns the same `sessionId` -- fails only the CAPABILITY
    `ACP-SESSION-002`, which alone must still flip the verdict to NOT CONFORMANT."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "duplicate_session_id.py",
        protocol_version=2,
        k="test_session and not capabilities and not config",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SESSION-002"}, result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


# --- prompt-turn defect fixtures ---


def test_bad_stop_reason_fails_state_203_only():
    """`bad_stop_reason.py`'s defect (every non-`__hang__` prompt -- including the dedicated
    cancel-test prompt -- resolves immediately with an invalid `stopReason: "done"`) cascades
    into every `run_prompt`-driven cancel check: the terminating idle never says `"cancelled"`,
    and `"done"` is not a recognised `StopReason` the TCK's race heuristic would excuse as "the
    agent simply finished on its own" (mirrors v1's `bad_stop_reason.py` cascading into
    `ACP-CANCEL-001`). `ACP-CLOSE-202` shares `ACP-CANCEL-208`'s exact test, so it FAILs
    alongside it too."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "bad_stop_reason.py",
        protocol_version=2,
        k="(test_prompt and not capabilities) or cancel",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {
        "ACP-STATE-203",
        "ACP-CANCEL-201",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CANCEL-208",
        "ACP-CLOSE-202",
    }, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_vendor_stop_reason_passes_everything():
    """Positive control for the `_`-prefix open-enum rule: every ordinary turn ends with
    `stopReason: "_tck/throttled"`, which `ACP-STATE-203` accepts. Advertises only the bare
    `session: {}` baseline, so `_NOT_ADVERTISED_OR_EXERCISED_SKIP_IDS`,
    `_SESSION_MGMT_EXTRAS_SKIP_IDS` and `_NO_AUTH_SKIP_IDS` SKIP. Its cancel-test turns finish on
    their own right after cancel is sent; a `_`-prefixed stop reason inside the race window is a
    plausible own finish, so `_CANCEL_RACE_SKIP_IDS` SKIP ("cancellation not exercised") rather
    than FAIL."""
    result = _run_cli(FIXTURES_DIR_V2, "vendor_stop_reason.py", protocol_version=2)
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    expected_skips = (
        _NOT_ADVERTISED_OR_EXERCISED_SKIP_IDS
        | _ALWAYS_SKIPPED_IDS
        | _SESSION_MGMT_EXTRAS_SKIP_IDS
        | _NO_AUTH_SKIP_IDS
        | _CANCEL_RACE_SKIP_IDS
    )
    for req_id, status in statuses.items():
        if req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_no_running_update_fails_state_201_only():
    result = _run_cli(
        FIXTURES_DIR_V2,
        "no_running_update.py",
        protocol_version=2,
        k="test_prompt and not capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-STATE-201"}, result.stdout
    # The fallback idle still ends the turn: its stopReason is judged, but no active state was.
    assert statuses.get("ACP-STATE-202") == "SKIPPED", result.stdout
    assert statuses.get("ACP-STATE-203") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_no_idle_after_running_fails_every_run_prompt_dependent_id():
    """`no_idle_after_running.py` never sends a terminating idle: every test that drives a turn
    through `run_prompt` independently hits `AgentTimeout` and FAILs. This includes
    `ACP-CLIENTCAP-201/202` (both observe a turn via `run_prompt`), `ACP-PERM-201` (never gets
    the chance to legitimately SKIP "no permission observed" -- it times out instead), the
    `ACP-PROMPT-206`, every `run_prompt`-driven `ACP-CANCEL-*` row (they never see a
    terminating idle either) plus `ACP-CLOSE-202` (shares `ACP-CANCEL-208`'s test),
    `ACP-CANCEL-204` (INFORMATIONAL, but an uncaught `AgentTimeout` is a FAIL, not a SKIP),
    except `ACP-CANCEL-213`/`ACP-CLOSE-205`, which SKIP when the turn never ends,
    `ACP-CLOSE-203` (its close-mid-turn run times out the same way),
    `ACP-TRANSPORT-201/002/203` (`test_transport.py`'s own `_drive_full_exchange` drives one
    ordinary `run_prompt` turn to gather evidence, which times out here too), `ACP-RESUME-
    202..206`/`209` (their own tests drive a `run_prompt` turn via `_session_with_history` to have
    something to replay, which also never resolves -- `ACP-RESUME-201` is unaffected, no prompt
    turn needed, and `ACP-CLOSE-202` FAILs alongside `ACP-CANCEL-208` since they share the same
    test), and `ACP-PATCH-209` (its test drives a `run_prompt` turn expecting a permission
    request mid-turn, incidentally selected by this fixture's `-k` pattern via
    `test_permission.py`). Every other `run_prompt`-driven id in `test_enums.py`
    (`ACP-ENUM-201`) and `test_extensibility.py` (`ACP-META-001/201`/`ACP-SCHEMA-002`) FAILs
    too, for the same reason -- so `-k` is widened to also select those two modules.
    `ACP-PROMPTCAP-001/002/003` are unaffected -- they SKIP on the capability-marker check before
    ever calling `run_prompt`, since this fixture advertises `capabilities: {"session": {}}}`
    only.

    Uses an even smaller `--timeout` (`0.5`) than the other CLI self-tests -- this fixture never
    responds at all, so the cascade is deterministic regardless of how short the wait is; a
    shorter wait just means the TCK gives up sooner. Scoped with `-k` to the modules that
    actually contribute a FAIL (plus `test_initialize.py` for the shared `ACP-SCHEMA-001`
    check) -- everything else is deselected (`NOT_TESTED`) rather than re-verified here."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "no_idle_after_running.py",
        protocol_version=2,
        timeout="0.5",
        k=(
            "(test_prompt and not capabilities) or initialize or client_capabilities or "
            "permission or cancel or session_capabilities or transport or enums or "
            "extensibility or patches"
        ),
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {
        "ACP-PROMPT-205",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-206",
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-CANCEL-209",
        "ACP-CLIENTCAP-201",
        "ACP-CLIENTCAP-202",
        "ACP-PERM-201",
        "ACP-CANCEL-201",
        "ACP-CANCEL-202",
        "ACP-CANCEL-203",
        "ACP-CANCEL-205",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CANCEL-208",
        "ACP-CANCEL-204",
        "ACP-CLOSE-202",
        "ACP-CLOSE-203",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
        "ACP-TRANSPORT-201",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
        "ACP-ENUM-201",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-META-202",
        "ACP-META-203",
        "ACP-META-204",
    }, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_idle_before_running_passes_everything():
    """`idle_before_running.py` sends a legal, unsolicited "session-ready" idle before any
    `session/prompt` is ever issued -- must not be mistaken for a turn terminator. Advertises
    only the bare `session: {}` baseline and never exercises the permission flow, so
    `ACP-PROMPTCAP-001/002/003`/`ACP-PERM-201` legitimately SKIP rather than PASS -- see
    `_NOT_ADVERTISED_OR_EXERCISED_SKIP_IDS`. Like `conforming.py`, its ordinary turns resolve
    fast with no `--cancel-prompt` override, so `_CANCEL_RACE_SKIP_IDS` legitimately SKIP too
    (cancellation not exercised), and `_ALWAYS_SKIPPED_IDS` SKIP unconditionally.

    `_SESSION_MGMT_EXTRAS_SKIP_IDS` SKIP too, since this fixture predates them and advertises
    only the bare `session: {}}` baseline. `_NO_AUTH_SKIP_IDS` SKIP too, since this fixture
    advertises no `authMethods` and the run passes no `--auth-method`."""
    result = _run_cli(FIXTURES_DIR_V2, "idle_before_running.py", protocol_version=2)
    assert result.returncode == 0, result.stdout + result.stderr

    expected_skips = (
        _NOT_ADVERTISED_OR_EXERCISED_SKIP_IDS
        | _CANCEL_RACE_SKIP_IDS
        | _ALWAYS_SKIPPED_IDS
        | _SESSION_MGMT_EXTRAS_SKIP_IDS
        | _NO_AUTH_SKIP_IDS
    )
    statuses = _table_statuses(result.stdout)
    for req_id, status in statuses.items():
        if req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_echo_wrong_message_id_fails_prompt_203_and_resume_204():
    """`echo_wrong_message_id.py` echoes a `"wrong-" + messageId` on the live `user_message`
    update -- FAILs `ACP-PROMPT-203` directly (the echoed `messageId` must match the response's).
    The same mismatched id is what gets stored and later replayed on `session/resume`, so
    `ACP-RESUME-204`'s own check (the replayed `user_message`'s `messageId` must include the
    original prompt response's `messageId`) also FAILs -- a second, independent manifestation of
    the same underlying defect, not a new bug."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "echo_wrong_message_id.py",
        protocol_version=2,
        k="(test_prompt and not capabilities) or session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PROMPT-203", "ACP-RESUME-204"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_missing_message_id_fails_prompt_201_and_schema_001_and_skips_prompt_203():
    """Perf note: scoped with `-k` to `test_prompt.py` (owns `ACP-PROMPT-201/203`) plus
    `test_initialize.py` (owns the shared `ACP-SCHEMA-001` full-exchange schema scan). Also
    genuinely cascades into `ACP-META-001` (`test_extensibility.py`: its own first assertion,
    `turn.message_id` truthy, fails outright since the acceptance receipt carries none) and
    `ACP-PATCH-203` (`test_patches.py`: two prompts both get `messageId: ""`, so they are not
    *distinct* ids) -- confirmed via an unscoped run; `-k` widened to select those two modules
    too. Everything else is deselected (`NOT_TESTED`) rather than re-verified here."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "missing_message_id.py",
        protocol_version=2,
        k="(test_prompt and not capabilities) or initialize or extensibility or patches",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {
        "ACP-PROMPT-201",
        "ACP-SCHEMA-001",
        "ACP-META-001",
        "ACP-META-202",
        "ACP-PATCH-203",
    }, result.stdout
    assert statuses.get("ACP-PROMPT-203") == "SKIPPED", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_update_wrong_session_fails_every_run_prompt_dependent_id():
    """`update_wrong_session.py` misattributes every `session/update` to `sessionId: "other"`:
    the same cascade shape as `no_idle_after_running.py` (see that test's docstring for why
    `ACP-CLIENTCAP-201/202`/`ACP-PERM-201`/`ACP-PROMPT-206`/every `run_prompt`-driven
    `ACP-CANCEL-*` row but `213` (plus `ACP-CLOSE-202`, sharing `ACP-CANCEL-208`'s test)/
    `ACP-TRANSPORT-201/002/203` are included here too), since `run_prompt` never recognizes a
    matching terminating idle either. Also FAILs `ACP-RESUME-202..206`/`209` (their own tests drive a
    `run_prompt` turn via `_session_with_history` first, which never resolves either) and
    `ACP-PATCH-209` (same "permission" `-k` substring incidence explained on
    `no_idle_after_running.py`'s test above) -- and, for the same reason, every other
    `run_prompt`-driven id: `ACP-ENUM-201`, `ACP-META-001/201`, `ACP-SCHEMA-002`, and the
    rest of the `ACP-PATCH-2xx` family -- confirmed identical to `no_idle_after_running.py`'s own
    FAIL set via an unscoped run, since both fixtures never send a terminating idle at all. `-k`
    widened to match."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "update_wrong_session.py",
        protocol_version=2,
        timeout="0.5",
        k=(
            "(test_prompt and not capabilities) or initialize or client_capabilities or "
            "permission or cancel or session_capabilities or transport or enums or "
            "extensibility or patches"
        ),
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {
        "ACP-PROMPT-205",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-206",
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-CANCEL-209",
        "ACP-CLIENTCAP-201",
        "ACP-CLIENTCAP-202",
        "ACP-PERM-201",
        "ACP-CANCEL-201",
        "ACP-CANCEL-202",
        "ACP-CANCEL-203",
        "ACP-CANCEL-205",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CANCEL-208",
        "ACP-CANCEL-204",
        "ACP-CLOSE-202",
        "ACP-CLOSE-203",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
        "ACP-TRANSPORT-201",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
        "ACP-ENUM-201",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-META-202",
        "ACP-META-203",
        "ACP-META-204",
    }, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


# --- turn-lifecycle, insertion-boundary, and subagent fixtures ---


def _fails(statuses: dict[str, str]) -> set[str]:
    return {req_id for req_id, status in statuses.items() if status == "FAIL"}


def test_reports_background_work_agent_passes_everything():
    """`reports_background_work.py` is `conforming.py` plus a `background` list on every
    `state_update` and one background tool call per turn, so `_BACKGROUND_SKIP_IDS` PASS. That
    tool call's two `tool_call_update`s also give `ACP-PATCH-204`/`208`/`210`/`211` something to
    judge, so they PASS too; every other id matches `conforming.py`."""
    result = _run_cli(FIXTURES_DIR_V2, "reports_background_work.py", protocol_version=2)
    assert result.returncode == 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    exercised = _BACKGROUND_SKIP_IDS | {"ACP-PATCH-204", "ACP-PATCH-208", "ACP-PATCH-210", "ACP-PATCH-211"}
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in _CONFORMING_EXPECTED_SKIPS - exercised else "PASS"
        assert status == expected, f"{req_id} is {status}, expected {expected}:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def _background_statuses(fixture: str) -> tuple[dict[str, str], str]:
    """Run only `test_background.py` against `fixture`; the background rows' statuses and stdout."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_background")
    statuses = _table_statuses(result.stdout)
    return {r: statuses.get(r) for r in sorted(_BACKGROUND_SKIP_IDS)}, result.stdout


def test_background_list_dropped_fails_only_state_206():
    """The idle omits `background` after earlier snapshots carried it. With no list on an idle,
    no idle removal is judged, so `ACP-STATE-208` SKIPs."""
    statuses, stdout = _background_statuses("background_list_dropped.py")
    assert statuses == {
        "ACP-STATE-206": "FAIL", "ACP-STATE-207": "PASS", "ACP-STATE-208": "SKIPPED"
    }, stdout


def test_background_unannounced_item_fails_only_state_207():
    statuses, stdout = _background_statuses("background_unannounced_item.py")
    assert statuses == {
        "ACP-STATE-206": "PASS", "ACP-STATE-207": "FAIL", "ACP-STATE-208": "PASS"
    }, stdout


def test_background_removed_unfinished_fails_only_state_208():
    statuses, stdout = _background_statuses("background_removed_unfinished.py")
    assert statuses == {
        "ACP-STATE-206": "PASS", "ACP-STATE-207": "PASS", "ACP-STATE-208": "FAIL"
    }, stdout


_PROMPT_K = "test_prompt and not capabilities"
_PERMISSION_FLOW_K = (
    "(test_prompt and not capabilities) or test_permission or patches or cancel"
)


def test_idle_without_stop_reason_fails_only_advisory_state_204():
    """The stop reason is SHOULD: an idle without one ends the turn, `ACP-STATE-203` SKIPs (no
    value to judge), and only the ADVISORY `ACP-STATE-204` FAILs -- still CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "idle_without_stop_reason.py", protocol_version=2)
    assert result.returncode == 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-STATE-204"}, result.stdout
    assert statuses["ACP-STATE-201"] == "PASS", result.stdout
    assert statuses["ACP-STATE-202"] == "PASS", result.stdout
    assert statuses["ACP-STATE-203"] == "SKIPPED", result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_rejects_prompt_while_busy_fails_only_prompt_209():
    """A second prompt sent during a `__hang__` turn gets `-32603`: `ACP-PROMPT-209` FAILs,
    `ACP-CANCEL-214` SKIPs (nothing was held) and `ACP-INFO-CONCURRENT-201` records it. Scoped
    with `-k` to the three tests sharing the scenario."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "rejects_prompt_while_busy.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        k="during_active_work or held_prompt or concurrent_prompt",
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-209"}, result.stdout
    assert statuses["ACP-CANCEL-214"] == "SKIPPED", result.stdout
    assert statuses["ACP-INFO-CONCURRENT-201"] == "PASS", result.stdout


def test_held_prompt_survives_cancel_fails_only_cancel_214():
    """The held prompt is inserted after `session/cancel` instead of being answered `-32800`:
    `ACP-CANCEL-214` FAILs, `ACP-PROMPT-209` PASSes (it was held, not rejected). `--timeout 2`
    keeps the fixture's 1 s pause past the race window and within the wait for the response."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "held_prompt_survives_cancel.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        timeout="2",
        k="during_active_work or held_prompt or concurrent_prompt",
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-214"}, result.stdout
    assert statuses["ACP-PROMPT-209"] == "PASS", result.stdout
    assert statuses["ACP-INFO-CONCURRENT-201"] == "PASS", result.stdout


def test_inserts_cancelled_held_prompt_fails_only_cancel_214():
    """The held prompt is answered `-32800` by `session/cancel` but then inserted anyway (a user
    message under a new `messageId` follows): `ACP-CANCEL-214` FAILs, `ACP-PROMPT-209` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "inserts_cancelled_held_prompt.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        k="during_active_work or held_prompt or concurrent_prompt",
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-214"}, result.stdout
    assert statuses["ACP-PROMPT-209"] == "PASS", result.stdout


def test_exposes_subagent_passes_everything():
    """Announced child-session traffic (including the child's own `running`/`idle`) is legal
    and must not end or start the parent's turn: same outcome as `conforming.py`."""
    result = _run_cli(FIXTURES_DIR_V2, "exposes_subagent.py", protocol_version=2)
    _assert_conforming_baseline(result, "exposes_subagent.py")


def test_unannounced_child_update_fails_prompt_205_only():
    result = _run_cli(FIXTURES_DIR_V2, "unannounced_child_update.py", protocol_version=2, k=_PROMPT_K)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-205"}, result.stdout


def test_requires_action_no_running_fails_state_205_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "requires_action_no_running.py", protocol_version=2, k=_PERMISSION_FLOW_K
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-STATE-205"}, result.stdout
    assert statuses["ACP-PATCH-209"] == "PASS", result.stdout


def test_permission_flow_positive_controls_fail_nothing():
    """`asks_permission.py` (`requires_action` -> `running` -> `idle`), `requires_action_then_idle.py`
    (`requires_action` -> `idle`, no resume) and `starts_blocked.py` (`requires_action` first, no
    preliminary `running`) are all legal traces, and each idles `cancelled` when cancelled while
    blocked on its held permission request (`ACP-CANCEL-209`)."""
    for fixture in ("asks_permission.py", "requires_action_then_idle.py", "starts_blocked.py"):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_PERMISSION_FLOW_K)
        statuses = _table_statuses(result.stdout)
        assert _fails(statuses) == set(), f"{fixture}:\n{result.stdout}"
        for req_id in (
            "ACP-STATE-201",
            "ACP-STATE-202",
            "ACP-STATE-205",
            "ACP-PATCH-209",
            "ACP-PERM-201",
            "ACP-CANCEL-209",
            "ACP-CANCEL-213",
            "ACP-CLOSE-205",
        ):
            assert statuses[req_id] == "PASS", f"{fixture} {req_id}:\n{result.stdout}"


def test_asks_permission_ignores_cancel_fails_cancel_209_only():
    """It withdraws the held request (`ACP-CANCEL-213` PASSes) but resumes `end_turn` on the
    `cancelled` answer."""
    result = _run_cli(FIXTURES_DIR_V2, "asks_permission_ignores_cancel.py", protocol_version=2, k="cancel")
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-209"}, result.stdout
    assert statuses["ACP-CANCEL-213"] == "PASS", result.stdout


def test_cancel_waits_for_permission_answer_fails_cancel_209_and_213_only():
    """Under the strict hold the turn ends only once the TCK answers the held request at the
    deadline: `ACP-CANCEL-209` FAILs saying so, and no `$/cancel_request` FAILs
    `ACP-CANCEL-213`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "cancel_waits_for_permission_answer.py", protocol_version=2, k="cancel"
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-209", "ACP-CANCEL-213"}, result.stdout
    assert "only after the TCK answered its held session/request_permission" in result.stdout


def test_cancel_without_cancel_request_fails_advisory_cancel_213_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "cancel_without_cancel_request.py", protocol_version=2, k="cancel"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-213"}, result.stdout
    assert statuses["ACP-CANCEL-209"] == "PASS", result.stdout
    assert statuses["ACP-CLOSE-205"] == "PASS", result.stdout


def test_close_keeps_permission_open_fails_close_205_only():
    result = _run_cli(FIXTURES_DIR_V2, "close_keeps_permission_open.py", protocol_version=2, k="cancel")
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CLOSE-205"}, result.stdout
    for req_id in ("ACP-CANCEL-208", "ACP-CANCEL-209", "ACP-CANCEL-213", "ACP-CLOSE-202"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"


def test_answers_cancel_request_fails_cancel_210_211_212_only():
    """Answering a `$/cancel_request` for an unknown or answered id breaks 210/211; the withdrawn
    prompt, already answered, gets that error as a second response (212)."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_cancel_request.py", protocol_version=2)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-210", "ACP-CANCEL-211", "ACP-CANCEL-212"}, result.stdout


def test_drops_withdrawn_prompt_fails_cancel_212_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "drops_withdrawn_prompt.py", protocol_version=2, k="cancel",
        cancel_prompt="__hang__",
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-212"}, result.stdout


def test_asks_permission_twice_passes_both_jsonrpc_202_halves():
    """`asks_permission_twice.py` has two permission requests pending at once with distinct ids,
    so the reuse half of `ACP-JSONRPC-202` is observable (two requests held) and PASSes, as does
    the id-type half."""
    result = _run_cli(
        FIXTURES_DIR_V2, "asks_permission_twice.py", protocol_version=2, k="jsonrpc or permission"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses["ACP-JSONRPC-202"] == "PASS", result.stdout
    assert statuses["ACP-PERM-201"] == "PASS", result.stdout


def test_asks_permission_reused_id_fails_jsonrpc_202_only():
    result = _run_cli(
        FIXTURES_DIR_V2,
        "asks_permission_reused_id.py",
        protocol_version=2,
        k="jsonrpc or permission or cancel",
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-JSONRPC-202"}, result.stdout


def test_asks_permission_null_id_fails_jsonrpc_202_and_perm_201_only():
    """A `null` request id is both the `ACP-JSONRPC-202` defect and a schema violation of the
    request itself, which `ACP-PERM-201` validates."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "asks_permission_null_id.py",
        protocol_version=2,
        k="jsonrpc or permission or cancel",
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-JSONRPC-202", "ACP-PERM-201"}, result.stdout


def test_error_after_echo_fails_prompt_207_and_cancel_203_only():
    """Answering an already-echoed prompt with `-32800` after cancel violates the insertion
    boundary: `ACP-PROMPT-207` (error after a user-message update), `ACP-CANCEL-203` (`-32800`
    is only for a prompt cancelled before insertion), and `ACP-CANCEL-212` (its withdrawn prompt
    ignores `$/cancel_request`, and the TCK's follow-up `session/cancel` gets the same `-32800`
    after the echo). The cancelled idle itself is correct, so `ACP-CANCEL-201` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2, "error_after_echo.py", protocol_version=2, k="cancel", cancel_prompt="__hang__"
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-207", "ACP-CANCEL-203", "ACP-CANCEL-212"}, result.stdout
    assert statuses["ACP-CANCEL-201"] == "PASS", result.stdout
    assert statuses["ACP-CANCEL-208"] == "PASS", result.stdout


def test_cancel_before_insertion_is_conforming():
    """A prompt cancelled (or closed) before insertion, with no foreground work started, is
    answered `-32800` and owes no idle: `ACP-CANCEL-203`/`208` and `ACP-PROMPT-207` PASS, and the
    rows that need a cancelled idle SKIP."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "cancel_before_insertion.py",
        protocol_version=2,
        k="cancel",
        cancel_prompt="__hang__",
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    # `ACP-CANCEL-212`: the held prompt ignores `$/cancel_request`, and the TCK's follow-up
    # `session/cancel` gets it answered `-32800`.
    for req_id in (
        "ACP-CANCEL-203", "ACP-CANCEL-205", "ACP-CANCEL-208", "ACP-CANCEL-212", "ACP-CLOSE-202",
        "ACP-PROMPT-207",
    ):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"
    for req_id in ("ACP-CANCEL-201", "ACP-CANCEL-202", "ACP-CANCEL-206", "ACP-CANCEL-207"):
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"


# --- cancellation, transport, JSON-RPC envelope, and batching defect fixtures ---


def test_cancel_no_idle_fails_every_cancel_dependent_id():
    """`cancel_no_idle.py` hangs on *every* prompt (not just the dedicated cancel-test one) and
    silently ignores `session/cancel` -- so every test that drives a turn through `run_prompt` at
    all times out with an uncaught `AgentTimeout`, a FAIL (not a SKIP -- see `AGENTS.md`
    "Statuses"), the same broad cascade shape as `no_idle_after_running.py`/
    `update_wrong_session.py` above. `ACP-CANCEL-208`/`ACP-CLOSE-202`/`ACP-CLOSE-203` are the
    exception: `session/close` still rescues the hanging turn via `ConformingAgent`'s inherited
    default handler, so they PASS. Also FAILs `ACP-RESUME-202..206`/`209`
    (their own tests drive a `run_prompt` turn via `_session_with_history` first, which never
    resolves either since this fixture hangs on *every* prompt) and `ACP-PATCH-209` (same
    "permission" `-k` substring incidence explained on `no_idle_after_running.py`'s test above)
    -- and, for the same reason, so does every other `run_prompt`-driven id: `ACP-ENUM-201`,
    `ACP-META-001/201`, `ACP-SCHEMA-002`, and the rest of the `ACP-PATCH-2xx` family. `-k`
    widened to match."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "cancel_no_idle.py",
        protocol_version=2,
        timeout="0.5",
        k=(
            "(test_prompt and not capabilities) or initialize or client_capabilities or "
            "permission or cancel or session_capabilities or transport or enums or "
            "extensibility or patches"
        ),
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-TRANSPORT-201",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-CANCEL-201",
        "ACP-CANCEL-202",
        "ACP-CANCEL-203",
        "ACP-CANCEL-205",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CLIENTCAP-201",
        "ACP-CLIENTCAP-202",
        "ACP-PERM-201",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-205",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-CANCEL-209",
        "ACP-CANCEL-204",
        "ACP-PROMPT-206",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
        "ACP-ENUM-201",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-META-202",
        "ACP-META-203",
        "ACP-META-204",
    }, result.stdout
    assert statuses.get("ACP-CANCEL-208") == "PASS", result.stdout
    assert statuses.get("ACP-CLOSE-202") == "PASS", result.stdout
    assert statuses.get("ACP-CLOSE-203") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_cancel_returns_error_fails_cancel_203_and_208_only():
    """`cancel_returns_error.py` withholds `session/prompt`'s own acceptance receipt entirely for
    *every* turn, not just the dedicated cancel-test one, until `session/cancel` arrives -- so
    every id whose own test drives an ordinary (non-cancelling) `run_prompt` turn never even gets
    that far and FAILs with a timeout: `ACP-SCHEMA-001`, `ACP-TRANSPORT-201/002/203`,
    `ACP-CLIENTCAP-201/202`, `ACP-PERM-201`, `ACP-PROMPT-201/203/205`, `ACP-STATE-201/202/203`,
    `ACP-PROMPT-206`, and `ACP-PROMPT-211` (its rejected probe prompt is never answered either).
    On top of that cascade, cancelling itself resolves the
    prompt with a JSON-RPC error instead of a terminating idle -- FAILs `ACP-CANCEL-203` (the
    error itself) and `ACP-CANCEL-208`/`ACP-CLOSE-202`/`ACP-CLOSE-203` (a `session/close` sent
    instead has nothing registered to rescue either, since `_handle_prompt` never adds the
    session to `_hanging_sessions`); for the same reason the ADVISORY `ACP-CLOSE-204` FAILs in the
    cascade run -- the prompt pending at close is never answered. `ACP-CANCEL-201`/`202`/`206`/`207` SKIP,
    deferring to `ACP-CANCEL-203` -- the turn never reaches a terminating idle at all. Also FAILs
    `ACP-RESUME-202..206`/`209` (their own tests drive a `run_prompt` turn via `_session_with_history`
    first, which never resolves either since this fixture withholds its acceptance receipt on
    every turn). The same cascade also catches every other `run_prompt`-driven id -- `ACP-
    ENUM-201` (`test_enums.py`), `ACP-META-001/201`/`ACP-SCHEMA-002` (`test_extensibility.py`),
    and the whole `ACP-PATCH-2xx` family (`test_patches.py`) -- `-k` widened to select those
    three modules too.

    Perf note: split into two `_run_cli` invocations instead of one broad-`-k` run.
    `test_cancel.py` itself (`cancel_result`) needs `--tck-timeout 1` -- at `0.5` its own
    `run_prompt(on_cancel=True, cancel_wait=0.5)` races the fixed `cancel_wait` against the
    read-response deadline and spuriously FAILs `ACP-CANCEL-201/202/206/207` instead of SKIPping
    them (confirmed empirically). The rest of the cascade (`cascade_result`) never gets a response
    at all regardless of timeout, so it can run at a much smaller `--tck-timeout 0.5` safely."""
    cancel_result = _run_cli(
        FIXTURES_DIR_V2, "cancel_returns_error.py", protocol_version=2, k="cancel"
    )
    cascade_result = _run_cli(
        FIXTURES_DIR_V2,
        "cancel_returns_error.py",
        protocol_version=2,
        timeout="0.5",
        k=(
            "(test_prompt and not capabilities) or initialize or client_capabilities or "
            "test_permission or session_capabilities or transport or enums or extensibility or "
            "patches"
        ),
    )
    assert cancel_result.returncode != 0
    assert cascade_result.returncode != 0

    cancel_statuses = _table_statuses(cancel_result.stdout)
    cascade_statuses = _table_statuses(cascade_result.stdout)
    cancel_fails = {req_id for req_id, status in cancel_statuses.items() if status == "FAIL"}
    cascade_fails = {req_id for req_id, status in cascade_statuses.items() if status == "FAIL"}
    assert cancel_fails == {
        "ACP-CANCEL-203",
        "ACP-CANCEL-208",
        "ACP-CLOSE-202",
        "ACP-CLOSE-203",
    }, cancel_result.stdout
    assert cascade_fails == {
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-TRANSPORT-201",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-CLIENTCAP-201",
        "ACP-CLIENTCAP-202",
        "ACP-PERM-201",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-205",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-PROMPT-206",
        "ACP-PROMPT-211",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
        "ACP-CLOSE-203",
        "ACP-CLOSE-204",
        "ACP-ENUM-201",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-META-202",
        "ACP-META-203",
        "ACP-META-204",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
    }, cascade_result.stdout
    for req_id in ("ACP-CANCEL-201", "ACP-CANCEL-202", "ACP-CANCEL-206", "ACP-CANCEL-207"):
        assert cancel_statuses.get(req_id) == "SKIPPED", f"{req_id}: {cancel_result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in cancel_result.stdout, cancel_result.stdout
    assert "VERDICT: NOT CONFORMANT" in cascade_result.stdout, cascade_result.stdout


def test_cancel_wrong_stop_reason_fails_201_203_206_207_only():
    """`cancel_wrong_stop_reason.py` hangs on *every* prompt (not just the dedicated cancel-test
    one), so every id whose own test drives an ordinary (non-cancelling) `run_prompt` turn times
    out too, the same broad cascade shape as `cancel_no_idle.py` above: `ACP-SCHEMA-001`,
    `ACP-TRANSPORT-201/002/203`, `ACP-CLIENTCAP-201/202`, `ACP-PERM-201`,
    `ACP-PROMPT-201/203/205`, `ACP-STATE-201/202/203`, and `ACP-PROMPT-206`. For the
    cancel scenario itself -- a deliberate 1.2s delay clears the TCK's own race window (see the
    fixture's own module docstring; needs `--timeout 2` for that delay to fit comfortably inside
    the wait) before resolving with `stopReason: "end_turn"` instead of `"cancelled"` -- FAILs
    `ACP-CANCEL-201`/`203`/`207` and `ACP-CANCEL-206` (the `_meta`-carrying scenario hits the same
    overridden handler). `ACP-CANCEL-202`/`208` SKIP/PASS respectively, deferring to the rows
    above; `ACP-CLOSE-203` PASSes (closing still rescues the turn as `cancelled`). Also FAILs
    `ACP-RESUME-202..206`/`209` (their own tests drive a `run_prompt` turn via
    `_session_with_history` first, which hangs the same way). The same cascade also catches
    every other `run_prompt`-driven id -- `ACP-ENUM-201`, `ACP-META-001/201`/
    `ACP-SCHEMA-002`, and the whole `ACP-PATCH-2xx` family -- `-k` widened to select those three
    modules too.

    Perf note: split into two `_run_cli` invocations instead of one broad-`-k` run
    at `--tck-timeout 2` for everything. Only `test_cancel.py` itself (`cancel_result`) needs the
    full `2` to let the fixture's deliberate 1.2s post-cancel delay clear the TCK's own race
    window; the rest of the cascade (`cascade_result`) never gets a response at all regardless of
    timeout (this fixture hangs on every prompt), so it runs at a much smaller `--tck-timeout
    0.5` safely (confirmed empirically to reproduce the identical FAIL set)."""
    cancel_result = _run_cli(
        FIXTURES_DIR_V2, "cancel_wrong_stop_reason.py", protocol_version=2, timeout="2", k="cancel"
    )
    cascade_result = _run_cli(
        FIXTURES_DIR_V2,
        "cancel_wrong_stop_reason.py",
        protocol_version=2,
        timeout="0.5",
        k=(
            "(test_prompt and not capabilities) or initialize or client_capabilities or "
            "test_permission or session_capabilities or transport or enums or extensibility or "
            "patches"
        ),
    )
    assert cancel_result.returncode != 0
    assert cascade_result.returncode != 0

    cancel_statuses = _table_statuses(cancel_result.stdout)
    cascade_statuses = _table_statuses(cascade_result.stdout)
    cancel_fails = {req_id for req_id, status in cancel_statuses.items() if status == "FAIL"}
    cascade_fails = {req_id for req_id, status in cascade_statuses.items() if status == "FAIL"}
    assert cancel_fails == {
        "ACP-CANCEL-201",
        "ACP-CANCEL-203",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
    }, cancel_result.stdout
    assert cascade_fails == {
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-TRANSPORT-201",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-CLIENTCAP-201",
        "ACP-CLIENTCAP-202",
        "ACP-PERM-201",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-205",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-PROMPT-206",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
        "ACP-ENUM-201",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-META-202",
        "ACP-META-203",
        "ACP-META-204",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
    }, cascade_result.stdout
    assert cancel_statuses.get("ACP-CANCEL-202") == "SKIPPED", cancel_result.stdout
    assert cancel_statuses.get("ACP-CANCEL-208") == "PASS", cancel_result.stdout
    assert cancel_statuses.get("ACP-CLOSE-203") == "PASS", cancel_result.stdout
    assert "VERDICT: NOT CONFORMANT" in cancel_result.stdout, cancel_result.stdout
    assert "VERDICT: NOT CONFORMANT" in cascade_result.stdout, cascade_result.stdout


def test_crashes_on_batch_fails_only_the_advisory_array_rows():
    """`crashes_on_batch.py` exits the moment it sees any JSON array on stdin -- otherwise fully
    conforming. FAILs the ADVISORY rows whose tests send an array (`ACP-BATCH-209`,
    `ACP-JSONRPC-005`). It never writes an array, so the MANDATORY `ACP-TRANSPORT-201` (which
    shares the probe) PASSes, and the run stays CONFORMANT: the receiver clause of the
    no-batches rule carries no RFC 2119 keyword, so a crash is only an advisory finding."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "crashes_on_batch.py",
        protocol_version=2,
        timeout="2",
        cancel_prompt="__hang__",
    )
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209", "ACP-JSONRPC-005"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-201") == "PASS", result.stdout
    assert all(req_id in _ADVISORY_IDS for req_id in fails), result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_ignores_batch_fails_only_batch_209():
    """`ignores_batch.py` answers `[]` with the single `-32600` object but silently drops every
    non-empty array (the Python SDK 1.0.0 shape). FAILs only the ADVISORY `ACP-BATCH-209`: the
    connection survives (`ACP-JSONRPC-005`) and nothing it writes is an array
    (`ACP-TRANSPORT-201`), so the run stays CONFORMANT."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "ignores_batch.py",
        protocol_version=2,
        timeout="2",
        cancel_prompt="__hang__",
    )
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209"}, result.stdout
    assert statuses.get("ACP-JSONRPC-005") == "PASS", result.stdout
    assert statuses.get("ACP-TRANSPORT-201") == "PASS", result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_answers_batch_with_array_fails_batch_209_and_transport_201():
    """`answers_batch_with_array.py` keeps the JSON-RPC 2.0 batching ACP v2 removed: it
    dispatches an array's elements and answers with an array. FAILs `ACP-BATCH-209` (elements
    processed) and, because it wrote an array, the MANDATORY `ACP-TRANSPORT-201` -- so the run
    is NOT CONFORMANT. `ACP-JSONRPC-005` PASSes: the connection survives."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "answers_batch_with_array.py",
        protocol_version=2,
        k="test_batch or test_transport or test_jsonrpc",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209", "ACP-TRANSPORT-201"}, result.stdout
    assert statuses.get("ACP-JSONRPC-005") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


# --- transport/JSON-RPC negative-control fixtures (mirror the v1 fixtures of the same name, on
# top of v2's own `_base.py` -- honest duplication, not shared machinery) ---


def test_v2_banner_on_stdout_fails_transport_201_and_schema_001_only():
    """`banner_on_stdout.py` prints a human banner line to stdout before behaving like a
    conforming agent -- violates `ACP-TRANSPORT-201` ("every stdout line is a valid ACP
    message"). The banner line also shows up in the full-exchange schema scan
    (`ACP-SCHEMA-001`), which fails the same way `test_initialize.py`'s scan does for any
    non-object line it can't attribute to a method/response. The banner is plain ASCII, so it
    does not additionally violate `ACP-TRANSPORT-002`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "banner_on_stdout.py", protocol_version=2, k="transport or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-201", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_invalid_utf8_fails_transport_002_201_and_schema_001():
    """`invalid_utf8.py` writes one line of invalid UTF-8 bytes to stdout before behaving like a
    conforming agent -- the dedicated negative control for `ACP-TRANSPORT-002`. A line that
    isn't decodable text isn't valid JSON either, so it also fails `ACP-TRANSPORT-201` and the
    full-exchange schema scan (`ACP-SCHEMA-001`), same cascade shape as `banner_on_stdout.py`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "invalid_utf8.py", protocol_version=2, k="transport or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-002", "ACP-TRANSPORT-201", "ACP-SCHEMA-001"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_garbage_after_response_fails_transport_201_and_schema_001_only():
    """`garbage_after_response.py` is conforming for the whole exchange, then -- after stdin
    closes -- writes one line of plain-text (ASCII) garbage to stdout before exiting. Only
    catchable via `AgentProcess.close()`'s post-close stdout drain. Fails `ACP-TRANSPORT-201`
    (the garbage line is not valid JSON) and `ACP-SCHEMA-001` (the drained garbage line is still
    on `agent.transcript` when the schema scan runs after `connected_agent`'s `__aexit__`).
    `ACP-TRANSPORT-002` still PASSes: the garbage is plain ASCII."""
    result = _run_cli(
        FIXTURES_DIR_V2, "garbage_after_response.py", protocol_version=2, k="transport or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-201", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_message_split_across_multiple_lines_fails_transport_203():
    """A JSON-RPC message split over three physical stdout lines must fail the dedicated
    embedded-newline requirement as well as generic framing and schema validation."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "message_split_across_multiple_lines.py",
        protocol_version=2,
        k="transport or initialize",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-201", "ACP-TRANSPORT-203", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_wrong_id_echo_fails_id_dependent_requirements():
    """`wrong_id_echo.py` mangles every response id -- violates `ACP-JSONRPC-001`. Breaking id
    correlation for literally every request/response pair in the connection cascades into
    almost every other requirement (each of whose own test can no longer find its own response
    at all, and either FAILs via a mismatched-shape assertion or hits `AgentTimeout`) --
    unscoped, this fixture FAILs all 106 ids, which is the intended, correct verdict shape for
    an agent this broken, not a TCK bug -- so this self-test scopes the run to `-k jsonrpc`
    (mirroring v1's own precedent for the identical problem) rather than paying the cost of an
    unscoped run across the whole suite. Scoped, the only requirements actually exercised are
    the six `ACP-JSONRPC-*` ids (001..005, 202) plus `ACP-TRANSPORT-201` (`test_transport.py`'s
    own full-exchange test matches the `-k jsonrpc` substring via its function name) --
    everything else is deselected (`NOT_TESTED`). `ACP-JSONRPC-202` FAILs too: its tests need a
    working `session/new` to elicit requests, and (like `ACP-JSONRPC-003`/`005`) hit the
    unmatched response."""
    result = _run_cli(FIXTURES_DIR_V2, "wrong_id_echo.py", protocol_version=2, k="jsonrpc")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {
        "ACP-JSONRPC-001",
        "ACP-JSONRPC-002",
        "ACP-JSONRPC-003",
        "ACP-TRANSPORT-201",
        "ACP-JSONRPC-004",
        "ACP-JSONRPC-005",
        "ACP-JSONRPC-202",
    }, result.stdout
    assert statuses.get("ACP-JSONRPC-001") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-002") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-003") == "FAIL", result.stdout
    assert statuses.get("ACP-TRANSPORT-201") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-004") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-005") == "FAIL", result.stdout
    for req_id in _ALL_IDS - fails:
        assert statuses.get(req_id) == "NOT_TESTED", (
            f"{req_id} is {statuses.get(req_id)}, expected NOT_TESTED (deselected by -k "
            f"jsonrpc):\n{result.stdout}"
        )
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_answers_notifications_fails_jsonrpc_003_only():
    """`answers_notifications.py` unconditionally replies to the `session/cancel` notification
    with a bogus error response (`{"id": null, "error": ...}`) -- violates `ACP-JSONRPC-003`
    (notifications never receive a response). Nothing else about it is non-conforming; the
    reply's `id: null` is legal on an error, so `ACP-JSONRPC-002` is unaffected."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_notifications.py", protocol_version=2, k="jsonrpc")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-003"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_pushes_status_notifications_passes_everything():
    """`pushes_status_notifications.py` pushes an unsolicited `_`-prefixed notification right
    after `initialize` and before handling every later message, including ahead of an array's
    rejection. So they land both in the quiet period of `ACP-JSONRPC-003`/`ACP-EXT-201` and
    between a request and its reply (`ACP-BATCH-209`, `ACP-JSONRPC-001`/`005`). A notification
    is not a reply, so the outcome must match `conforming.py`'s exactly -- including the
    INFORMATIONAL probes' recorded behaviour, which must not mistake a push for the reply."""
    result = _run_cli(FIXTURES_DIR_V2, "pushes_status_notifications.py", protocol_version=2)
    _assert_conforming_baseline(result, "pushes_status_notifications.py")

    notes = _table_notes(result.stdout)
    for req_id in ("ACP-INFO-PARSE-001", "ACP-INFO-INVALIDREQ-001"):
        assert notes[req_id].startswith("(silent"), f"{req_id}: {notes[req_id]}"
    for req_id, note in notes.items():
        assert "_fixture/status_update" not in note, f"{req_id}: {note}"


def test_v2_pushes_status_and_answers_notifications_fails_no_reply_rows_only():
    """`pushes_status_and_answers_notifications.py` pushes the same status notification, then
    also replies to the notification. The leading notification must not hide the reply behind
    it: every "a notification gets no response" row still FAILs."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "pushes_status_and_answers_notifications.py",
        protocol_version=2,
        k="test_jsonrpc or test_extensibility",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-003", "ACP-EXT-201", "ACP-EXT-203"}, result.stdout


def test_v2_pushes_status_and_processes_array_elements_fails_batch_209_only():
    """`pushes_status_and_processes_array_elements.py` pushes the same status notifications, but
    instead of rejecting an array it dispatches the elements and answers each on its own line
    (a push between them). Skipping the pushes must not hide element processing: `ACP-BATCH-209`
    FAILs. Nothing it writes is an array, so `ACP-TRANSPORT-201` PASSes, as do
    `ACP-JSONRPC-001` and `ACP-JSONRPC-005`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "pushes_status_and_processes_array_elements.py",
        protocol_version=2,
        k="test_batch or test_jsonrpc",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209"}, result.stdout
    for req_id in ("ACP-TRANSPORT-201", "ACP-JSONRPC-001", "ACP-JSONRPC-005"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"


def test_v2_result_and_error_fails_jsonrpc_002_and_schema_001_only():
    """`result_and_error.py`'s `initialize` response illegally carries both `result` and
    `error` -- violates `ACP-JSONRPC-002` (exactly one of `result`/`error`) and, via the same
    envelope check, `ACP-SCHEMA-001`. `ACP-INIT-001` still PASSes: that check only asserts
    `"result" in msg`, which remains true even though `error` is also illegally present."""
    result = _run_cli(
        FIXTURES_DIR_V2, "result_and_error.py", protocol_version=2, k="jsonrpc or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-002", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-INIT-001") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_unknown_method_no_error_only_fails_the_advisory_requirement():
    """`unknown_method_no_error.py` replies to unknown methods with an empty success result
    instead of `-32601`. Should only trip the MANDATORY `ACP-JSONRPC-004` (unknown method ->
    `-32601` is a MUST); it does reply, so `ACP-EXT-001` is not tripped. `ACP-BATCH-209`'s probes never
    expect an unknown-method reply, so this fixture does not fail it.
    The exit code/overall verdict text are not asserted here: this run is `-k`-scoped, which
    necessarily leaves every other MANDATORY id NOT_TESTED, and NOT_TESTED MANDATORY ids flip
    the verdict to NOT CONFORMANT by design -- that says nothing about whether *this* fixture's
    behaviour for the ids actually exercised is conforming, which is what the per-id statuses
    below check."""
    result = _run_cli(
        FIXTURES_DIR_V2, "unknown_method_no_error.py", protocol_version=2, k="jsonrpc or batch"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-004"}, result.stdout
    assert statuses.get("ACP-BATCH-209") == "PASS", result.stdout


def test_v2_emits_batch_updates_fails_transport_201_only():
    """Batching every pair of a turn's own spontaneous `session/update` notifications into
    single JSON-RPC array lines violates `ACP-TRANSPORT-201` (MANDATORY: ACP has no batches) and
    nothing else: `run_prompt` and the other scans still unpack an array line, so every other id
    gets the verdict it would on separate lines. Same shape as `conforming_full.py`'s own
    self-test above -- run with `--cancel-prompt __hang__` so every CAPABILITY-tier
    `ACP-CANCEL-*` id is actually exercised, not just skipped by a race.
    This fixture advertises only the bare `capabilities.session.prompt.*` baseline (no
    session-management extras, no `authMethods`), so `_SESSION_MGMT_EXTRAS_SKIP_IDS`/
    `_NO_AUTH_SKIP_IDS` legitimately SKIP too, exactly as they do for `conforming.py` itself.
    """
    result = _run_cli(
        FIXTURES_DIR_V2, "emits_batch_updates.py", protocol_version=2, cancel_prompt="__hang__"
    )
    assert result.returncode != 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    # This fixture never opts into `_send_rich_turn_updates` either, so the tool_call/plan/
    # terminal-dependent ids legitimately SKIP as they do for `conforming.py`/
    # `vendor_stop_reason.py`/`idle_before_running.py` above. Unlike those three, though, this
    # fixture is built on `AsksPermissionAgent` (it asks for permission mid-turn, same as
    # `conforming_full.py`), so the permission-dependent `ACP-ENUM-203`/`ACP-PATCH-209` PASS
    # here rather than SKIP -- only the tool-call rows (`ACP-PATCH-208`/`210..212`, and
    # `ACP-PERM-203`/`002`, which need a `tool_call` subject) still SKIP.
    _RICH_TURN_SKIP_IDS = {
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-META-203",
        "ACP-META-204",
    }
    # Like `conforming_full.py`: it never rejects a prompt, and `__hang__` preempts the
    # permission request `ACP-CANCEL-209`/`213` and `ACP-CLOSE-205` need pending.
    expected_skips = (
        _ALWAYS_SKIPPED_IDS
        | _SESSION_MGMT_EXTRAS_SKIP_IDS
        | _NO_AUTH_SKIP_IDS
        | _RICH_TURN_SKIP_IDS
        | _BACKGROUND_SKIP_IDS
        | _RESUME_BACKGROUND_SKIP_IDS
        | {
            "ACP-PROMPT-207",
            "ACP-PROMPTCAP-201",  # every prompt capability is advertised
            "ACP-CANCEL-209",
            "ACP-CANCEL-213",
            "ACP-CLOSE-205",
            "ACP-ERROR-204",
        }
    )
    for req_id, status in statuses.items():
        if req_id == "ACP-TRANSPORT-201":
            assert status == "FAIL", f"{req_id} is {status}, expected FAIL:\n{result.stdout}"
        elif req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", (
                f"{req_id} is {status}, expected PASS for emits_batch_updates.py:\n{result.stdout}"
            )
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


# --- session management -- defect fixtures ---


def test_resume_replays_when_not_asked_fails_resume_203_only():
    """`resume_replays_when_not_asked.py` replays the session's full retained history on every
    `session/resume`, even when `replayFrom` is omitted/`null` -- FAILs exactly `ACP-RESUME-203`
    (the "MUST NOT replay when not asked" rule). `ACP-RESUME-201` (resume itself still succeeds)
    and `ACP-RESUME-202`/`204`..`209` (the replay-`{"type": "start"}` scenarios, the snapshot and
    cursor checks, answered identically to `conforming_full.py`) are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_replays_when_not_asked.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-203"}, result.stdout
    for req_id in (
        "ACP-RESUME-201",
        "ACP-RESUME-202",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
        "ACP-RESUME-209",
    ):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_responds_before_replay_fails_resume_202_only():
    """`resume_responds_before_replay.py` answers `session/resume` before replaying stored
    history (reversed order vs. the spec's requirement) -- FAILs exactly `ACP-RESUME-202`.
    `ACP-RESUME-204`'s own test reads only up to the response before checking replayed
    `messageId`s, so with the replay now arriving *after* the response it never observes any
    replayed update at all and legitimately SKIPs rather than PASSing or FAILing.
    `ACP-RESUME-201`/`203`/`205`..`209` are unaffected: the state snapshot still precedes the
    response."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_responds_before_replay.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-202"}, result.stdout
    assert statuses.get("ACP-RESUME-204") == "SKIPPED", result.stdout
    for req_id in (
        "ACP-RESUME-201",
        "ACP-RESUME-203",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
        "ACP-RESUME-209",
    ):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_replay_missing_message_id_fails_resume_204_and_209_only():
    """`resume_replay_missing_message_id.py` replays correctly (before responding, only when
    asked) but strips `messageId` from every replayed `session/update` -- FAILs exactly
    `ACP-RESUME-204` and `ACP-RESUME-209` (a message update without `messageId` is
    schema-invalid). `ACP-RESUME-201`/`202`/`203`/`205`..`208` are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_replay_missing_message_id.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-204", "ACP-RESUME-209"}, result.stdout
    for req_id in (
        "ACP-RESUME-201",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
    ):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_always_errors_all_resume_rows_skip_together():
    """`resume_always_errors.py` advertises `capabilities.session: {}` but always errors on
    `session/resume` with a plain `-32603`, never `-32601` (Method not found, which
    `obtain_resumable_session` treats as a hard FAIL). All three of
    `obtain_resumable_session`'s routes (create-then-resume, close-then-resume, list-then-resume)
    end in the same `session/resume` call, so all three are exhausted identically here, and
    every test that routes through it -- `ACP-RESUME-201..209` and `ACP-ADDDIRS-202` -- must
    SKIP together with the same "no resumable session obtainable" reason, never hard-FAIL:
    `ACP-RESUME-202..209` must call `obtain_resumable_session` first rather than building their
    own session directly (`_session_with_history`), or they would hard-FAIL on this fixture's
    `session/resume` error, producing a false NOT CONFORMANT for an agent the TCK itself admits
    it could not obtain a resumable session from."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_always_errors.py",
        protocol_version=2,
        k="session_capabilities",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    # `ACP-RESUME-216` (ADVISORY) FAILs any error on resuming an active session, where the other
    # resume rows SKIP on one.
    assert fails == {"ACP-RESUME-216"}, f"expected only ACP-RESUME-216, got {fails}: {result.stdout}"
    for req_id in (
        "ACP-RESUME-201",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
        "ACP-ADDDIRS-202",
    ):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"


def test_resume_lists_foreign_session_is_never_resumed():
    """`resume_lists_foreign_session.py` lists only a session under a foreign `cwd` (ignoring the
    `cwd` filter -- FAILs `ACP-LIST-202`/`203`) and resumes only that session. The list route
    must skip it, so no route succeeds and every resume-dependent row SKIPs; resuming it would
    PASS them instead, and the TCK would then prompt into the operator's session."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_lists_foreign_session.py",
        protocol_version=2,
        k="session_capabilities",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-202", "ACP-LIST-203", "ACP-RESUME-216"}, result.stdout
    for req_id in (
        "ACP-RESUME-201",
        "ACP-RESUME-202",
        "ACP-RESUME-203",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
    ):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"
    assert "session/list has no session created in the TCK's own cwd" in result.stdout


def test_resume_no_state_snapshot_fails_resume_206_only():
    """`resume_no_state_snapshot.py` never sends the current-state `state_update` before
    answering `session/resume` -- FAILs exactly `ACP-RESUME-206`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "resume_no_state_snapshot.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-206"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def _resume_statuses(fixture: str, **kwargs: str) -> tuple[dict[str, str], str]:
    """Run only `test_session_capabilities.py` against `fixture`: every row's status, and stdout."""
    result = _run_cli(
        FIXTURES_DIR_V2, fixture, protocol_version=2, k="session_capabilities", **kwargs
    )
    return _table_statuses(result.stdout), result.stdout


def test_resume_replays_state_updates_fails_resume_212_only():
    """`resume_replays_state_updates.py` records and replays every `state_update`, so a replayed
    `running` precedes the snapshot."""
    statuses, stdout = _resume_statuses("resume_replays_state_updates.py")
    assert _fails(statuses) == {"ACP-RESUME-212"}, stdout


def test_resume_no_session_info_fails_resume_214_only():
    statuses, stdout = _resume_statuses("resume_no_session_info.py")
    assert _fails(statuses) == {"ACP-RESUME-214"}, stdout


def test_resume_omits_config_options_fails_resume_210_only():
    """The omitted list leaves `ACP-CONFIG-203` nothing to validate, so it SKIPs."""
    statuses, stdout = _resume_statuses("resume_omits_config_options.py")
    assert _fails(statuses) == {"ACP-RESUME-210"}, stdout


def test_resume_omits_available_commands_fails_resume_210_only():
    statuses, stdout = _resume_statuses("resume_omits_available_commands.py")
    assert _fails(statuses) == {"ACP-RESUME-210"}, stdout


def test_resume_rejects_unprompted_active_session_fails_resume_216_only():
    """Resume works for a prompted or closed session, so every other row runs; only the resume of
    a just-created session errors, and `ACP-RESUME-210`'s version of it has nothing to judge."""
    statuses, stdout = _resume_statuses("resume_rejects_unprompted_active_session.py")
    assert _fails(statuses) == {"ACP-RESUME-216"}, stdout


def test_resume_lists_background_work_passes_resume_213():
    """The positive control: the snapshot lists an unfinished background tool call and a
    `tool_call_update` announces it first, so `ACP-RESUME-213` PASSes, not SKIPs."""
    statuses, stdout = _resume_statuses("resume_lists_background_work.py")
    assert _fails(statuses) == set(), stdout
    assert statuses["ACP-RESUME-213"] == "PASS", stdout


def test_resume_background_without_updates_fails_resume_213_only():
    statuses, stdout = _resume_statuses("resume_background_without_updates.py")
    assert _fails(statuses) == {"ACP-RESUME-213"}, stdout


def test_resume_ignores_unknown_cursor_fails_resume_207_only():
    """`resume_ignores_unknown_cursor.py` resumes without replay on an unsupported cursor type
    instead of rejecting it -- FAILs exactly `ACP-RESUME-207`; malformed values are still
    rejected, so `ACP-RESUME-208` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_ignores_unknown_cursor.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-207"}, result.stdout
    assert statuses.get("ACP-RESUME-208") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_accepts_malformed_cursor_fails_resume_208_only():
    """`resume_accepts_malformed_cursor.py` treats a malformed `replayFrom` as omitted -- FAILs
    exactly `ACP-RESUME-208`; unsupported well-formed cursors are still rejected, so
    `ACP-RESUME-207` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_accepts_malformed_cursor.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-208"}, result.stdout
    assert statuses.get("ACP-RESUME-207") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_list_errors_when_empty_fails_list_202_only():
    """`list_errors_when_empty.py` errors instead of returning `{"sessions": []}` whenever the
    (possibly `cwd`-filtered) result set would be empty -- FAILs exactly `ACP-LIST-202`.
    `ACP-LIST-201`/`203`/`204` are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2, "list_errors_when_empty.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-202"}, result.stdout
    for req_id in ("ACP-LIST-201", "ACP-LIST-203", "ACP-LIST-204"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_close_no_cancel_idle_fails_cancel_208_and_close_202_203_only():
    """`close_no_cancel_idle.py` keeps `ConformingAgent`'s default hang behaviour (hangs only on
    the literal `__hang__` sentinel), so the defect is bounded and only observable when driven
    with `--cancel-prompt __hang__`: `session/close` on a still-hanging prompt replies to the
    close normally but resolves the pending turn with `stopReason: "end_turn"` instead of
    `"cancelled"`, after a deliberate delay past the TCK's race window. FAILs exactly
    `ACP-CANCEL-208`/`ACP-CLOSE-202` (both dual-bound to `test_close_cancels_foreground_work`)
    and `ACP-CLOSE-203`, whose own close-mid-turn run times out the same way (the delayed idle
    lands past `--timeout`). Every other id, including plain `ACP-CANCEL-201..207` (which use
    `session/cancel`, not `session/close`) and `ACP-CLOSE-201` (closing an already-idle
    session), is unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "close_no_cancel_idle.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        k="cancel or session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CANCEL-208", "ACP-CLOSE-202", "ACP-CLOSE-203"}, result.stdout
    assert statuses.get("ACP-CLOSE-201") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_close_responds_before_idle_fails_close_203_and_206_only():
    """`close_responds_before_idle.py` answers `session/close` before sending the cancelled idle
    for the work it cancelled -- FAILs `ACP-CLOSE-203`, and `ACP-CLOSE-206` too, since that idle
    is a `session/update` after the close response. The turn still ends `cancelled`, so
    `ACP-CLOSE-202`/`ACP-CANCEL-208` PASS."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "close_responds_before_idle.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        k="cancel or session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLOSE-203", "ACP-CLOSE-206"}, result.stdout
    for req_id in ("ACP-CLOSE-201", "ACP-CLOSE-202", "ACP-CANCEL-208"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_returns_source_id_fails_fork_201_only():
    """`fork_returns_source_id.py` answers `session/fork` with the source session's own id --
    FAILs `ACP-FORK-201` and `ACP-FORK-204` (which also needs a new id); `ACP-FORK-202` SKIPs (no
    forked session to prompt)."""
    result = _run_cli(FIXTURES_DIR_V2, "fork_returns_source_id.py", protocol_version=2, k="fork")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-201", "ACP-FORK-204"}, result.stdout
    assert statuses.get("ACP-FORK-202") == "SKIPPED", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_session_not_active_fails_fork_202_only():
    """`fork_session_not_active.py` returns a fresh forked id but rejects prompts on it --
    FAILs exactly `ACP-FORK-202`."""
    result = _run_cli(FIXTURES_DIR_V2, "fork_session_not_active.py", protocol_version=2, k="fork")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-202"}, result.stdout
    assert statuses.get("ACP-FORK-201") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_rejects_append_fails_sysprompt_201_only():
    """`system_prompt_rejects_append.py` advertises `session.systemPrompt` but rejects an
    `append` prompt -- FAILs exactly `ACP-SYSPROMPT-201`; `override` is not advertised, so
    `ACP-SYSPROMPT-202` SKIPs."""
    result = _run_cli(
        FIXTURES_DIR_V2, "system_prompt_rejects_append.py", protocol_version=2, k="system_prompt"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-201"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-202") == "SKIPPED", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_rejects_override_fails_sysprompt_202_only():
    """`system_prompt_rejects_override.py` advertises `session.systemPrompt.mode.override` but
    rejects an `override` prompt -- FAILs exactly `ACP-SYSPROMPT-202`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "system_prompt_rejects_override.py", protocol_version=2, k="system_prompt"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-202"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-201") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def _sysprompt_test_statuses(report_path) -> dict[str, str]:
    """`{test function name: status}` for every test bound to an `ACP-SYSPROMPT-002/003` row."""
    report = json.loads(report_path.read_text())
    return {
        test["nodeid"].rsplit("::", 1)[-1]: test["status"]
        for req in report["requirements"]
        if req["id"] in ("ACP-SYSPROMPT-002", "ACP-SYSPROMPT-003")
        for test in req["tests"]
    }


def test_system_prompt_accepts_unsupported_mode_fails_sysprompt_002_only(tmp_path):
    """`system_prompt_accepts_unsupported_mode.py` applies an unsupported `systemPrompt.mode`
    instead of returning an error -- FAILs exactly `ACP-SYSPROMPT-002`, on both `session/new` and
    `session/resume`; `ACP-SYSPROMPT-003` PASSes."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "system_prompt_accepts_unsupported_mode.py",
        protocol_version=2,
        k="system_prompt",
        report_json=str(report_path),
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-002"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-003") == "PASS", result.stdout
    assert _sysprompt_test_statuses(report_path) == {
        "test_new_session_with_unsupported_system_prompt_mode_errors": "FAIL",
        "test_resume_with_unsupported_system_prompt_mode_errors": "FAIL",
        "test_new_session_with_non_text_system_prompt_content_errors": "PASS",
        "test_resume_with_non_text_system_prompt_content_errors": "PASS",
    }
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_resume_accepts_non_text_fails_sysprompt_003_only(tmp_path):
    """`system_prompt_resume_accepts_non_text.py` refuses a non-text `systemPrompt` block on
    `session/new` but resumes the session anyway -- FAILs exactly `ACP-SYSPROMPT-003`, through its
    `session/resume` probe only; `ACP-SYSPROMPT-002` PASSes."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "system_prompt_resume_accepts_non_text.py",
        protocol_version=2,
        k="system_prompt",
        report_json=str(report_path),
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-003"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-002") == "PASS", result.stdout
    assert _sysprompt_test_statuses(report_path) == {
        "test_new_session_with_unsupported_system_prompt_mode_errors": "PASS",
        "test_resume_with_unsupported_system_prompt_mode_errors": "PASS",
        "test_new_session_with_non_text_system_prompt_content_errors": "PASS",
        "test_resume_with_non_text_system_prompt_content_errors": "FAIL",
    }
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_without_persistence_skips_the_resume_probes(tmp_path):
    """`system_prompt_no_persistence.py` refuses unsupported prompts but cannot resume a session
    on a fresh process, so the resume probes SKIP ("cannot judge") instead of passing vacuously
    on the `-32002` it would answer anyway. No FAIL."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "system_prompt_no_persistence.py",
        protocol_version=2,
        k="system_prompt",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert _sysprompt_test_statuses(report_path) == {
        "test_new_session_with_unsupported_system_prompt_mode_errors": "PASS",
        "test_resume_with_unsupported_system_prompt_mode_errors": "SKIPPED",
        "test_new_session_with_non_text_system_prompt_content_errors": "PASS",
        "test_resume_with_non_text_system_prompt_content_errors": "SKIPPED",
    }
    report = json.loads(report_path.read_text())
    messages = [
        test["message"]
        for req in report["requirements"]
        if req["id"] in ("ACP-SYSPROMPT-002", "ACP-SYSPROMPT-003")
        for test in req["tests"]
        if test["status"] == "SKIPPED"
    ]
    assert messages and all("cannot judge" in message for message in messages), messages


def test_advertises_delete_but_errors_fails_delete_201_202_and_203():
    """`advertises_delete_but_errors.py` advertises `capabilities.session.delete` but always
    errors on `session/delete` -- FAILs `ACP-DELETE-201` (delete itself must succeed) and
    `ACP-DELETE-202` (cascades: the deleted session can't be observed gone). The ADVISORY
    `ACP-DELETE-203` also FAILs (the same underlying probe). `-32603` is not the tolerated
    `-32002`, so `ACP-DELETE-205` SKIPs (its prerequisite, a successful delete, is missing) and
    `ACP-DELETE-204` SKIPs on the race gate or the missing delete result."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "advertises_delete_but_errors.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-DELETE-201", "ACP-DELETE-202", "ACP-DELETE-203"}, result.stdout
    for req_id in ("ACP-DELETE-204", "ACP-DELETE-205"):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_list_matches_subdirectories_fails_list_203_only():
    """`list_matches_subdirectories.py` matches the `cwd` filter by prefix, so the subdirectory
    session `ACP-LIST-203` creates comes back under the parent filter -- FAILs exactly
    `ACP-LIST-203`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "list_matches_subdirectories.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-203"}, result.stdout
    assert statuses.get("ACP-LIST-202") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_list_accepts_relative_cwd_fails_list_205_only():
    """`list_accepts_relative_cwd.py` accepts a relative `cwd` filter instead of `-32602` --
    FAILs exactly `ACP-LIST-205`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "list_accepts_relative_cwd.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-205"}, result.stdout
    assert statuses.get("ACP-LIST-206") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_list_ignores_invalid_cursor_fails_list_206_only():
    """`list_ignores_invalid_cursor.py` returns the first page for a never-issued cursor
    instead of `-32602` -- FAILs exactly `ACP-LIST-206`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "list_ignores_invalid_cursor.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-206"}, result.stdout
    assert statuses.get("ACP-LIST-205") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_delete_does_not_cancel_active_fails_delete_204_only():
    """`delete_does_not_cancel_active.py` deletes a session but leaves its hanging `__hang__`
    turn running, so `ACP-DELETE-204` (run with `--cancel-prompt __hang__`) times out waiting
    for the cancelled idle -- FAILs exactly `ACP-DELETE-204`. Deleting an idle session
    (`ACP-DELETE-201`) is unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "delete_does_not_cancel_active.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-DELETE-204"}, result.stdout
    for req_id in ("ACP-DELETE-201", "ACP-DELETE-202", "ACP-DELETE-205"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_after_delete_succeeds_fails_delete_205_only():
    """`resume_after_delete_succeeds.py` still resumes a deleted session instead of `-32002` --
    FAILs exactly `ACP-DELETE-205`; the session does leave `session/list`
    (`ACP-DELETE-202` PASSes)."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_after_delete_succeeds.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-DELETE-205"}, result.stdout
    assert statuses.get("ACP-DELETE-202") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


_ARCHIVE_IDS = (
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
)


def _archive_run(fixture: str, *, expected_fails: set[str], expected_skips: set[str] = frozenset()):
    """Run `fixture` against the session-capability rows with `--cancel-prompt __hang__` (so
    `ACP-ARCHIVE-201` is exercised), assert the exact FAIL set, that the other archive ids PASS
    except `expected_skips`, and return `(statuses, stdout)`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        fixture,
        protocol_version=2,
        cancel_prompt="__hang__",
        k="session_capabilities",
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == expected_fails, result.stdout
    for req_id in _ARCHIVE_IDS:
        if req_id in expected_fails:
            continue
        expected = "SKIPPED" if req_id in expected_skips else "PASS"
        assert statuses.get(req_id) == expected, f"{req_id}: {result.stdout}"
    if expected_fails:  # a `-k`-scoped run is NOT CONFORMANT regardless (unbound MANDATORY ids)
        assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    return statuses, result.stdout


def test_conforming_full_passes_every_archive_row():
    """`conforming_full.py` advertises `archive` and `delete` and lists fresh sessions, so every
    archive row PASSes (`ACP-ARCHIVE-201` with `--cancel-prompt __hang__`)."""
    _archive_run("conforming_full.py", expected_fails=set())


def test_archive_omits_archived_flag_fails_archive_002_only():
    _archive_run("archive_omits_archived_flag.py", expected_fails={"ACP-ARCHIVE-002"})


def test_archive_still_listed_fails_archive_003_only():
    _archive_run("archive_still_listed.py", expected_fails={"ACP-ARCHIVE-003"})


def test_archive_rejecting_include_and_only_fails_the_views_that_need_them():
    """`archive_rejects_include_and_only.py` answers `-32602` for `include`/`only`:
    `ACP-ARCHIVE-002` (its `only` check), `-003` and `-006` each need one of those views."""
    _statuses, out = _archive_run(
        "archive_rejects_include_and_only.py",
        expected_fails={"ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-006"},
    )
    assert "docs/rfds/session-archive.mdx:112" in out, out


def test_archive_filter_falling_back_fails_archive_004_only():
    _archive_run("archive_filter_falls_back.py", expected_fails={"ACP-ARCHIVE-004"})


def test_archive_unknown_succeeding_fails_archive_005_only():
    _archive_run("archive_unknown_succeeds.py", expected_fails={"ACP-ARCHIVE-005"})


def test_archive_unknown_wrong_code_fails_archive_005_only():
    """`archive_unknown_wrong_code.py` fails an unknown session with `-32602`: an error, but not
    the `-32002` the docs name."""
    _statuses, out = _archive_run("archive_unknown_wrong_code.py", expected_fails={"ACP-ARCHIVE-005"})
    assert "expected code -32002" in out, out


def test_archive_not_idempotent_fails_archive_005_only():
    _archive_run("archive_not_idempotent.py", expected_fails={"ACP-ARCHIVE-005"})


def test_archive_not_cancelling_fails_archive_201_only():
    """`archive_does_not_cancel.py` archives without cancelling a hanging `__hang__` turn, so the
    cancelled idle never arrives and the TCK's wait times out."""
    _archive_run("archive_does_not_cancel.py", expected_fails={"ACP-ARCHIVE-201"})


def test_delete_archiving_instead_fails_archive_006_only():
    """`delete_archives_instead.py` hides a deleted session from the default view only, so
    `ACP-DELETE-202` and `-205` still PASS."""
    statuses, _out = _archive_run("delete_archives_instead.py", expected_fails={"ACP-ARCHIVE-006"})
    assert statuses.get("ACP-DELETE-202") == "PASS", statuses
    assert statuses.get("ACP-DELETE-205") == "PASS", statuses


def test_archive_agent_listing_nothing_skips_the_view_comparisons_not_passes_them():
    """`archive_lists_nothing_unprompted.py` never lists a fresh session, so `ACP-ARCHIVE-002`,
    `-003` and `-006` SKIP rather than PASS vacuously; the rest still PASS."""
    _archive_run(
        "archive_lists_nothing_unprompted.py",
        expected_fails=set(),
        expected_skips={"ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-006"},
    )


def test_answers_unadvertised_archive_fails_error_202_only():
    """`answers_unadvertised_archive.py` serves `session/archive`/`session/unarchive` without
    advertising `session.archive` -- MANDATORY, so the verdict is NOT CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_unadvertised_archive.py", protocol_version=2, k=_ERROR_K)
    statuses = _table_statuses(result.stdout)
    fails = {r for r, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-ERROR-202"}, result.stdout
    assert "session/archive" in result.stdout, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_unknown_source_invalid_params_fails_fork_203_only():
    """`fork_unknown_source_invalid_params.py` answers a fork of an unknown source with `-32602`
    instead of `-32002` -- FAILs exactly `ACP-FORK-203`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "fork_unknown_source_invalid_params.py", protocol_version=2, k="fork"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-203"}, result.stdout
    for req_id in ("ACP-FORK-201", "ACP-FORK-202", "ACP-FORK-204"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


@pytest.mark.parametrize(
    "fixture", ["fork_omits_config_options.py", "fork_omits_available_commands.py"]
)
def test_fork_omitting_a_list_session_new_carried_fails_fork_205_only(fixture):
    """`fork_omits_config_options.py`/`fork_omits_available_commands.py` carry both lists on
    `session/new` but drop one from the `session/fork` response -- FAILs exactly `ACP-FORK-205`."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="fork")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-205"}, result.stdout
    for req_id in ("ACP-FORK-201", "ACP-FORK-202"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_requires_active_source_fails_fork_204_only():
    """`fork_requires_active_source.py` forks only active sessions and answers a closed (still
    listed) source with `-32002` -- FAILs exactly `ACP-FORK-204`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "fork_requires_active_source.py", protocol_version=2, k="fork"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-204"}, result.stdout
    assert statuses.get("ACP-FORK-203") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_config_set_omits_changed_option_fails_config_202_only():
    """`config_set_omits_changed_option.py` advertises two independent `configOptions` entries
    but `session/set_config_option` replies with a list missing the option it just changed --
    FAILs exactly `ACP-CONFIG-202`. `ACP-CONFIG-201`/`203`/`204`/`206` are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2, "config_set_omits_changed_option.py", protocol_version=2, k="session_config"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CONFIG-202"}, result.stdout
    for req_id in ("ACP-CONFIG-201", "ACP-CONFIG-203", "ACP-CONFIG-204", "ACP-CONFIG-206"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


_CONFIG_K = "session_config"
_CONFIG_RULE_IDS = {f"ACP-CONFIG-{n}" for n in (201, 202, 203, 204, 206, 207, 208, 209, 210, 211, 212)}


def _config_fixture_run(fixture: str, k: str = _CONFIG_K) -> tuple[set[str], dict[str, str], str]:
    fails, statuses, out = _fails_for(fixture, k)
    return fails, statuses, out


def test_config_set_unknown_id_accepted_fails_config_207_only():
    """The fixture answers an unadvertised `configId` with success; it has one option, so
    `ACP-CONFIG-209` cannot probe an invalid value and SKIPs."""
    fails, statuses, out = _config_fixture_run("config_set_unknown_id_accepted.py")
    assert fails == {"ACP-CONFIG-207"}, out
    assert statuses.get("ACP-CONFIG-208") == "PASS", out
    assert statuses.get("ACP-CONFIG-209") == "SKIPPED", out


def test_config_set_invalid_value_wrong_code_fails_config_208_only():
    fails, statuses, out = _config_fixture_run("config_set_invalid_value_wrong_code.py")
    assert fails == {"ACP-CONFIG-208"}, out
    assert statuses.get("ACP-CONFIG-207") == "PASS", out
    assert statuses.get("ACP-CONFIG-209") == "PASS", out


def test_config_set_invalid_value_mutates_fails_config_209_only():
    fails, statuses, out = _config_fixture_run("config_set_invalid_value_mutates.py")
    assert fails == {"ACP-CONFIG-209"}, out
    assert statuses.get("ACP-CONFIG-207") == "PASS", out
    assert statuses.get("ACP-CONFIG-208") == "PASS", out


def test_config_duplicate_select_values_fails_config_210_only():
    fails, statuses, out = _config_fixture_run("config_duplicate_select_values.py")
    assert fails == {"ACP-CONFIG-210"}, out
    assert statuses.get("ACP-CONFIG-201") == "PASS", out
    assert statuses.get("ACP-CONFIG-204") == "PASS", out


def test_config_set_no_update_notification_fails_config_211_only():
    """No update at all, so there is nothing for `ACP-CONFIG-212` to order: it SKIPs."""
    fails, statuses, out = _config_fixture_run("config_set_no_update_notification.py")
    assert fails == {"ACP-CONFIG-211"}, out
    assert statuses.get("ACP-CONFIG-212") == "SKIPPED", out


def test_config_update_after_response_fails_config_212_only():
    fails, statuses, out = _config_fixture_run("config_update_after_response.py")
    assert fails == {"ACP-CONFIG-212"}, out
    assert statuses.get("ACP-CONFIG-211") == "PASS", out


def test_conforming_full_passes_every_config_rule():
    """`conforming_full.py` advertises a select and a boolean option, so 207..212 all PASS."""
    result = _run_cli(
        FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=_CONFIG_K
    )
    statuses = _table_statuses(result.stdout)
    for req_id in _CONFIG_RULE_IDS:
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"


_COMMANDS_K = "slash_commands"


def test_commands_name_with_whitespace_fails_commands_201_only():
    fails, _statuses, out = _fails_for("commands_name_with_whitespace.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-201"}, out
    assert "whitespace" in out, out


def test_commands_duplicate_names_fails_commands_201_only():
    fails, _statuses, out = _fails_for("commands_duplicate_names.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-201"}, out
    assert "not unique" in out, out


def test_commands_untyped_in_update_fails_commands_201():
    fails, _statuses, out = _fails_for("commands_untyped_in_update.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-201"}, out
    assert "AvailableCommand" in out, out


def test_conforming_full_passes_commands_201():
    result = _run_cli(
        FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=_COMMANDS_K
    )
    assert _table_statuses(result.stdout).get("ACP-COMMANDS-201") == "PASS", result.stdout


# --- authentication (`ACP-AUTH-201..210`) -- self-tests ---


def test_gated_by_auth_without_auth_method_is_blocked_by_auth():
    """`gated_by_auth.py` always errors `session/new` with `-32000` unless `auth/login` with
    methodId `"tck"` has already succeeded on the connection. Without `--auth-method`, every
    session-dependent test SKIPs with the `AUTH-GATED:` marker (via `skip_if_auth_gated()`),
    which forces `verdict.blocked_by_auth == true` and exit code 1 -- even though zero
    requirements actually FAILed; they were simply never exercised. Mirrors v1's
    `gated_by_auth.py` self-test."""
    result = _run_cli(FIXTURES_DIR_V2, "gated_by_auth.py", protocol_version=2)
    assert result.returncode != 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), f"expected zero FAILs (the agent is merely never exercised): {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "blocked by auth" in result.stdout.lower() or "auth-gated" in result.stdout.lower(), result.stdout


def test_login_that_never_answers_skips_auth_gated_and_blocks_the_verdict(tmp_path):
    """`gated_by_auth_login_never_answers.py` never answers `auth/login` (an interactive login
    that stays pending). `connected_agent`'s embedded login times out, which SKIPs with the
    `AUTH-GATED:` marker and a hint instead of FAILing, and blocks the verdict like any other
    auth gate. Mirrors v1's self-test."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "gated_by_auth_login_never_answers.py",
        protocol_version=2,
        k="test_session_new_returns_unique_string_id",
        auth_method="tck",
        report_json=str(report_path),
    )
    assert result.returncode != 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-SESSION-001") == "SKIPPED", result.stdout
    assert "blocked by authentication" in result.stdout, result.stdout

    report = json.loads(report_path.read_text())
    assert report["verdict"]["blocked_by_auth"] is True, report["verdict"]
    assert report["verdict"]["conformant"] is False, report["verdict"]
    by_id = {r["id"]: r for r in report["requirements"]}
    message = by_id["ACP-SESSION-001"]["tests"][0]["message"]
    assert "AUTH-GATED:" in message and "interactive" in message, message


def test_gated_by_auth_with_auth_method_is_conformant():
    """The same `gated_by_auth.py` fixture, run with `--auth-method tck`: `connected_agent`'s
    auto-login step (`_helpers.py`) authenticates before any session-dependent test ever calls
    `session/new`, so the gate never fires and the run is fully CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "gated_by_auth.py", protocol_version=2, auth_method="tck")
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_terminal_auth_unadvertised_fails_auth_202_only():
    """`terminal_auth_unadvertised.py` advertises a `type: "terminal"` authMethods entry on every
    connection, including the default one that never advertises `capabilities.auth.terminal` --
    FAILs exactly `ACP-AUTH-202`. It has no `args`/`env` fields at all, so it cannot also trip
    `ACP-AUTH-207` (which only runs when a terminal entry actually appears on the dedicated
    terminal-capable connection -- and this fixture happens to also advertise it there, but with
    a well-formed descriptor)."""
    result = _run_cli(FIXTURES_DIR_V2, "terminal_auth_unadvertised.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-202"}, result.stdout
    for req_id in ("ACP-AUTH-201", "ACP-AUTH-206", "ACP-AUTH-207"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_duplicate_method_id_fails_auth_201_only():
    """`duplicate_method_id.py` advertises two `authMethods` entries sharing the same
    `methodId` -- FAILs exactly `ACP-AUTH-201`, which is MANDATORY (`authentication.mdx:51`), so
    the run is NOT CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "duplicate_method_id.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-201"}, result.stdout
    for req_id in ("ACP-AUTH-202", "ACP-AUTH-206"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_custom_auth_type_unprefixed_fails_auth_206_only():
    """`custom_auth_type_unprefixed.py` advertises an authMethods entry whose `type` is
    `"sso"` -- neither a defined value nor `_`-prefixed -- FAILs exactly `ACP-AUTH-206`
    (MANDATORY, new in v2)."""
    result = _run_cli(FIXTURES_DIR_V2, "custom_auth_type_unprefixed.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-206"}, result.stdout
    for req_id in ("ACP-AUTH-201", "ACP-AUTH-202"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_advertises_auth_but_logout_errors_fails_auth_203_only_with_allow_logout():
    """`advertises_auth_but_logout_errors.py` implements `auth/login` normally but always errors
    on `auth/logout`. Run with `--auth-method tck --allow-logout` (both required to actually
    exercise `auth/logout` at all) -- FAILs exactly `ACP-AUTH-203`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "advertises_auth_but_logout_errors.py",
        protocol_version=2,
        k="authentication",
        auth_method="tck",
        allow_logout=True,
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-203"}, result.stdout
    assert statuses.get("ACP-AUTH-204") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_advertises_auth_but_logout_errors_skips_auth_203_without_allow_logout():
    """The same fixture, without `--allow-logout`: `auth/logout` is never called at all, so
    `ACP-AUTH-203` SKIPs (its documented, diagnosable reason) rather than FAILing. Scoped with
    `-k authentication`, so the exit code/overall verdict text are not asserted (scoping leaves
    other MANDATORY ids `NOT_TESTED`, which flips the verdict by design)."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "advertises_auth_but_logout_errors.py",
        protocol_version=2,
        k="authentication",
        auth_method="tck",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert statuses.get("ACP-AUTH-203") == "SKIPPED", result.stdout


def test_terminal_env_duplicate_names_fails_auth_207_only():
    """`terminal_env_duplicate_names.py` only advertises its `type: "terminal"` authMethods entry
    to a connection that itself advertises `capabilities.auth.terminal` -- so it never trips
    `ACP-AUTH-202` (the default connection sees no `authMethods` at all) -- but that entry's
    `env` array has two entries sharing the same `name`, FAILing exactly `ACP-AUTH-207`
    (MANDATORY, new in v2). `ACP-AUTH-201`/`206` bind to `agent_initialize_result`, which
    connects with the default (no `auth.terminal`) capabilities, so they see no `authMethods` at
    all and SKIP rather than PASS."""
    result = _run_cli(FIXTURES_DIR_V2, "terminal_env_duplicate_names.py", protocol_version=2, k="authentication")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-AUTH-207"}, result.stdout
    assert statuses.get("ACP-AUTH-202") == "PASS", result.stdout
    for req_id in ("ACP-AUTH-201", "ACP-AUTH-206"):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def _auth_fixture_run(fixture: str, **kwargs):
    """`-k authentication` run; returns `(fails, statuses, stdout, result)`."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="authentication", **kwargs)
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    return fails, statuses, result.stdout, result


def test_login_advertised_agent_method_invalid_params_fails_auth_204_only():
    """`login_advertised_agent_method_invalid_params.py` answers `-32602` to `auth/login` for its
    advertised `type: "agent"` method: FAILs exactly `ACP-AUTH-204`. An unadvertised id is still
    rejected `-32602`, so `ACP-AUTH-208`/`210` PASS."""
    fails, statuses, out, result = _auth_fixture_run(
        "login_advertised_agent_method_invalid_params.py", auth_method="tck"
    )
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-204"}, out
    assert "-32602" in out, out
    for req_id in ("ACP-AUTH-208", "ACP-AUTH-210"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {out}"


def test_login_accepts_unadvertised_method_fails_auth_208_only():
    """`login_accepts_unadvertised_method.py` answers `{}` for an unadvertised `methodId`: FAILs
    exactly `ACP-AUTH-208`; `ACP-AUTH-210` SKIPs (nothing was rejected, so no code to judge)."""
    fails, statuses, out, result = _auth_fixture_run("login_accepts_unadvertised_method.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-208"}, out
    assert statuses.get("ACP-AUTH-210") == "SKIPPED", out


def test_login_unadvertised_method_wrong_code_fails_auth_210_advisory_only():
    """`login_unadvertised_method_wrong_code.py` rejects the unadvertised id with `-32000`:
    `ACP-AUTH-208` PASSes, `ACP-AUTH-210` FAILs, and being ADVISORY it leaves the run's
    exit code at 0 apart from the scoping (`-k authentication` leaves MANDATORY ids unexercised),
    so only the per-id statuses are asserted."""
    fails, statuses, out, _result = _auth_fixture_run("login_unadvertised_method_wrong_code.py")
    assert fails == {"ACP-AUTH-210"}, out
    assert statuses.get("ACP-AUTH-208") == "PASS", out


def test_auth_status_auth_required_fails_auth_209_only():
    """`auth_status_auth_required.py` answers `auth/status` with `-32000`."""
    fails, _statuses, out, result = _auth_fixture_run("auth_status_auth_required.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-209"}, out
    assert "-32000" in out, out


def test_auth_status_missing_state_fails_auth_209_only():
    fails, _statuses, out, result = _auth_fixture_run("auth_status_missing_state.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-209"}, out


def test_auth_status_unreserved_state_fails_auth_209_only():
    """`state: "logged_in"` is schema-valid (open enum) but neither defined nor `_`-prefixed."""
    fails, _statuses, out, result = _auth_fixture_run("auth_status_unreserved_state.py")
    assert result.returncode != 0
    assert fails == {"ACP-AUTH-209"}, out
    assert "logged_in" in out, out


def test_auth_status_is_judged_unauthenticated_even_with_auth_method():
    """`gated_by_auth_with_status.py` is unauthenticated until `auth/login`: ACP-AUTH-209 PASSes
    both without `--auth-method` and with `--auth-method tck`, whose login the `auth/status`
    test never performs. Scoped with `-k auth_status` to that test only."""
    for auth_method in (None, "tck"):
        result = _run_cli(
            FIXTURES_DIR_V2,
            "gated_by_auth_with_status.py",
            protocol_version=2,
            k="auth_status",
            auth_method=auth_method,
        )
        assert _table_statuses(result.stdout).get("ACP-AUTH-209") == "PASS", result.stdout


# --- patch/upsert semantics, open enums, extensibility/hygiene -- defect fixtures ---


def test_tool_call_update_missing_id_fails_patch_204_and_schema_001():
    """`tool_call_update_missing_id.py` emits one `tool_call_update` with no `toolCallId` --
    FAILs `ACP-PATCH-204` directly, and cascades into `ACP-SCHEMA-001` since `ToolCallUpdate`
    schema-requires `toolCallId` (`schema/v2/schema.unstable.json#/$defs/ToolCallUpdate`). It overrides
    `_send_rich_turn_updates`, which `_base.py` calls on *every* turn, so it also cascades into
    `ACP-PROMPT-205` (CAPABILITY -- schema-validates every `session/update` a driven turn
    observes) -- confirmed via an unscoped run; `-k` is widened to `test_prompt` too so this
    self-test's own asserted FAIL set matches an unscoped run's."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "tool_call_update_missing_id.py",
        protocol_version=2,
        k="test_patches or initialize or (test_prompt and not capabilities)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PATCH-204", "ACP-SCHEMA-001", "ACP-PROMPT-205"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_plan_missing_plan_id_fails_patch_205_and_schema_001():
    """`plan_missing_plan_id.py` emits one `plan_update` whose `plan` object has no `planId` --
    FAILs `ACP-PATCH-205` directly, and cascades into `ACP-SCHEMA-001` since `PlanItems`
    schema-requires `planId` (`schema/v2/schema.unstable.json#/$defs/PlanItems`). Same
    `_send_rich_turn_updates`-on-every-turn cascade as the sibling test above also FAILs
    `ACP-PROMPT-205` unscoped; `-k` widened to match."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "plan_missing_plan_id.py",
        protocol_version=2,
        k="test_patches or initialize or (test_prompt and not capabilities)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PATCH-205", "ACP-SCHEMA-001", "ACP-PROMPT-205"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_message_chunk_missing_message_id_fails_patch_201_and_schema_001():
    """`message_chunk_missing_message_id.py` emits one `agent_message_chunk` with no
    `messageId` -- FAILs `ACP-PATCH-201` directly, and cascades into `ACP-SCHEMA-001` since
    `ContentChunk` schema-requires `messageId` (`schema/v2/schema.unstable.json#/$defs/ContentChunk`).
    Same `_send_rich_turn_updates`-on-every-turn cascade as the two sibling tests above also
    FAILs `ACP-PROMPT-205` unscoped; `-k` widened to match."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "message_chunk_missing_message_id.py",
        protocol_version=2,
        k="test_patches or initialize or (test_prompt and not capabilities)",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PATCH-201", "ACP-SCHEMA-001", "ACP-PROMPT-205"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


# Wide enough to catch a tool-call fixture's cascades into the prompt, cancel, background and
# open-enum rows.
_TOOL_CALL_K = "test_permission or patches or background or test_enums or test_prompt or cancel"


@pytest.mark.parametrize(
    ("fixture", "failing_id"),
    [
        ("duplicate_permission_option_id.py", "ACP-PERM-202"),
        ("permission_command_relative_cwd.py", "ACP-PERM-202"),
        ("proceeds_after_cancelled_permission.py", "ACP-PERM-203"),
        ("perm_unknown_option_is_approval.py", "ACP-PERM-002"),
        ("tool_call_chunk_first.py", "ACP-PATCH-208"),
        ("permission_without_requires_action.py", "ACP-PATCH-209"),
        ("tool_call_reopens_after_final.py", "ACP-PATCH-210"),
        ("leaves_tool_call_in_progress.py", "ACP-PATCH-211"),
        ("advertises_cancel_after_final.py", "ACP-PATCH-212"),
    ],
)
def test_tool_call_defect_fails_its_row_only(fixture: str, failing_id: str):
    """Each tool-call defect fixture trips exactly its own row (see its docstring)."""
    fails, statuses, stdout = _fails_for(fixture, _TOOL_CALL_K)
    assert fails == {failing_id}, stdout
    if fixture == "proceeds_after_cancelled_permission.py":
        assert statuses["ACP-PERM-002"] == "PASS", stdout
    if fixture == "perm_unknown_option_is_approval.py":
        assert statuses["ACP-PERM-203"] == "PASS", stdout


def test_permission_for_background_work_needs_no_requires_action(tmp_path):
    """`asks_permission_for_background_work.py` asks permission for its listed background tool
    call while the session stays `running`/`idle`. That request is not for foreground work, so
    `ACP-PATCH-209` SKIPs instead of FAILing, and the permission rows judge it normally."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "asks_permission_for_background_work.py",
        protocol_version=2,
        k=_TOOL_CALL_K,
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    for req_id in (
        "ACP-PERM-201",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PATCH-208",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-STATE-206",
        "ACP-STATE-207",
        "ACP-STATE-208",
    ):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    (patch_209,) = by_id["ACP-PATCH-209"]["tests"]
    assert patch_209["status"] == "SKIPPED"
    assert "background work" in patch_209["message"], patch_209


def _enum_201_run(fixture: str):
    return _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_enums")


def test_unprefixed_custom_session_update_fails_enum_201_only():
    """`unprefixed_custom_session_update.py` sends one `session/update` with
    `sessionUpdate: "surprise"` (neither a defined constant nor `_`-prefixed) -- FAILs
    `ACP-ENUM-201` only. The `SessionUpdate` `$def`'s own `"other"`-titled fallback branch only
    requires `sessionUpdate` to be a string, so this does NOT cascade into `ACP-SCHEMA-001`."""
    result = _enum_201_run("unprefixed_custom_session_update.py")
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_prefixed_custom_session_update_passes_enum_201():
    """Positive control for the rule above: `_tck_custom_update` is `_`-prefixed, so
    `ACP-ENUM-201` PASSes."""
    result = _enum_201_run("prefixed_custom_session_update.py")
    assert _fails(_table_statuses(result.stdout)) == set(), result.stdout
    assert _table_statuses(result.stdout).get("ACP-ENUM-201") == "PASS", result.stdout


def test_unprefixed_custom_state_fails_enum_201_only():
    """`unprefixed_custom_state.py` sends `state_update{state: "busy"}` mid-turn, then a normal
    idle. The unrecognised state never ends the turn, so the turn still completes (no timeout
    cascade); the full suite FAILs only `ACP-ENUM-201`."""
    result = _run_cli(FIXTURES_DIR_V2, "unprefixed_custom_state.py", protocol_version=2)
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_unprefixed_custom_permission_kind_fails_enum_201_only():
    """`unprefixed_custom_permission_kind.py` offers a permission option with `kind: "sorcery"`
    -- schema-valid via `PermissionOptionKind`'s `other` branch, so only `ACP-ENUM-201` FAILs."""
    result = _run_cli(FIXTURES_DIR_V2, "unprefixed_custom_permission_kind.py", protocol_version=2)
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_prefixed_custom_permission_kind_passes_enum_201():
    """Positive control: `_tck_custom_kind` is `_`-prefixed, so `ACP-ENUM-201` PASSes -- and
    really checked, since this fixture does ask for permission."""
    result = _enum_201_run("prefixed_custom_permission_kind.py")
    assert _fails(_table_statuses(result.stdout)) == set(), result.stdout
    assert _table_statuses(result.stdout).get("ACP-ENUM-201") == "PASS", result.stdout


def test_unprefixed_chunk_content_type_fails_enum_201_only():
    """`unprefixed_chunk_content_type.py` sends a `tool_call_content_chunk` whose single `content`
    object has `type: "sorcery"`. The chunk's `content` is one object, so this guards the sweep
    reading it as such; the schema's `other` branch accepts it, so only `ACP-ENUM-201` FAILs."""
    result = _enum_201_run("unprefixed_chunk_content_type.py")
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout


def test_unprefixed_diff_operation_fails_enum_201_only():
    """`unprefixed_diff_operation.py` sends `diff` content with a change `operation` of
    `"teleport"` -- schema-valid via `DiffChange`'s `other` branch, so only `ACP-ENUM-201` FAILs."""
    result = _enum_201_run("unprefixed_diff_operation.py")
    assert result.returncode != 0
    assert _fails(_table_statuses(result.stdout)) == {"ACP-ENUM-201"}, result.stdout


def _extensibility_run(fixture: str):
    return _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_extensibility")


def test_answers_unknown_protocol_notification_fails_ext_203_only():
    """`answers_unknown_protocol_notification.py` replies to an unrecognized `$/` notification
    (SHOULD be ignored): `ACP-EXT-203` FAILs; the `_`-prefixed notification of `ACP-EXT-201` is
    left alone."""
    result = _extensibility_run("answers_unknown_protocol_notification.py")
    assert _fails(_table_statuses(result.stdout)) == {"ACP-EXT-203"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-EXT-201") == "PASS", result.stdout


def test_rejects_malformed_meta_fails_meta_202_only():
    """`rejects_malformed_meta.py` answers a prompt with a non-object `_meta` with `-32602`
    instead of treating it as omitted: `ACP-META-202` FAILs, `ACP-META-001` (object `_meta`)
    still PASSes."""
    result = _extensibility_run("rejects_malformed_meta.py")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-META-202"}, result.stdout
    assert statuses.get("ACP-META-001") == "PASS", result.stdout


def test_malformed_traceparent_fails_meta_203_only():
    """`malformed_traceparent.py` emits `_meta: {"traceparent": "not-a-trace-id"}`:
    `ACP-META-203` FAILs. The key itself is a reserved W3C one, so `ACP-META-204` PASSes."""
    result = _extensibility_run("malformed_traceparent.py")
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-META-203"}, result.stdout
    assert statuses.get("ACP-META-204") == "PASS", result.stdout


def test_unprefixed_meta_key_fails_meta_204_only():
    """`unprefixed_meta_key.py` advertises `capabilities._meta: {"vendorThing": true}`:
    only the ADVISORY `ACP-META-204` FAILs, so the verdict stays CONFORMANT."""
    result = _extensibility_run("unprefixed_meta_key.py")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-META-204"}, result.stdout
    assert statuses.get("ACP-META-203") == "SKIPPED", result.stdout


def test_emits_w3c_meta_passes_meta_203_and_204():
    """Positive control: valid W3C trace keys and reverse-DNS namespaced keys really are
    observed, so both rows PASS rather than SKIP."""
    result = _extensibility_run("emits_w3c_meta.py")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses.get("ACP-META-203") == "PASS", result.stdout
    assert statuses.get("ACP-META-204") == "PASS", result.stdout


def test_accepts_contentless_embedded_resource_fails_enum_204_only():
    """`accepts_contentless_embedded_resource.py` advertises `embeddedContext` but accepts a
    `resource` block with neither `text` nor `blob`: only the ADVISORY `ACP-ENUM-204` FAILs;
    an ordinary resource block is still accepted (`ACP-PROMPTCAP-003`)."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "accepts_contentless_embedded_resource.py",
        protocol_version=2,
        k="test_enums or prompt_capabilities",
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-ENUM-204"}, result.stdout
    assert statuses.get("ACP-PROMPTCAP-003") == "PASS", result.stdout


def test_custom_method_no_response_fails_ext_001_and_error_001():
    """`custom_method_no_response.py` silently swallows every `_`-prefixed custom method
    request instead of responding at all -- FAILs `ACP-EXT-001` (MANDATORY) directly. It also
    cascades into the ADVISORY `ACP-ERROR-001` (`test_diagnostics.py`): that probe sends its own
    `_`-prefixed unknown method and, getting no reply at all instead of a `-32601` with a
    non-empty one-line `message`, FAILs the "error message is well-formed" check outright
    (confirmed via an unscoped run; `ACP-BATCH-209`'s array probes are rejected whole, never
    dispatched per element, so it is unaffected here). `-k` widened to `test_diagnostics` to match."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "custom_method_no_response.py",
        protocol_version=2,
        k="test_extensibility or test_diagnostics",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-EXT-001", "ACP-ERROR-001"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


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


def test_unknown_root_key_fails_schema_002_only():
    """`unknown_root_key.py` adds `unknownRootKey` to the `initialize` result's root -- FAILs
    `ACP-SCHEMA-002` (ADVISORY) only; the vendored schema itself never sets
    `additionalProperties: false`, so this is not caught by `ACP-SCHEMA-001`/`ACP-INIT-001`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "unknown_root_key.py", protocol_version=2, k="test_extensibility or initialize"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SCHEMA-002"}, result.stdout


def test_unknown_capability_root_key_fails_ext_202():
    """`unknown_capability_root_key.py` adds `capabilities.vendorFeature`, which has no home in
    the schema -- `ACP-EXT-202` must still FAIL for a genuinely unrecognized `capabilities`
    root key."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "unknown_capability_root_key.py",
        protocol_version=2,
        k="test_extensibility or initialize",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-EXT-202"}, result.stdout


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


# --- error codes (`ACP-ERROR-201..204`, `ACP-RESUME-211`) -- defect fixtures ---

_ERROR_K = "test_errors or resume_unknown_session"


def _fails_for(fixture: str, k: str) -> tuple[set[str], dict[str, str], str]:
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=k)
    statuses = _table_statuses(result.stdout)
    return {r for r, status in statuses.items() if status == "FAIL"}, statuses, result.stdout


def test_unknown_session_wrong_code_fails_error_201_only():
    """`unknown_session_wrong_code.py` answers a prompt for a never-created or closed session with
    `-32602`; resume still answers `-32002`, so `ACP-RESUME-211` PASSes."""
    fails, statuses, out = _fails_for("unknown_session_wrong_code.py", _ERROR_K)
    assert fails == {"ACP-ERROR-201"}, out
    assert statuses.get("ACP-RESUME-211") == "PASS", out
    assert statuses.get("ACP-ERROR-202") == "PASS", out


def test_unknown_session_no_data_fails_error_201_and_resume_211():
    """`unknown_session_no_data.py` answers `-32002` without `data.sessionId`; the two rows share
    one assertion, so both FAIL."""
    fails, _statuses, out = _fails_for("unknown_session_no_data.py", _ERROR_K)
    assert fails == {"ACP-ERROR-201", "ACP-RESUME-211"}, out


def test_resume_accepts_unknown_session_fails_resume_211_only():
    fails, statuses, out = _fails_for("resume_accepts_unknown_session.py", _ERROR_K)
    assert fails == {"ACP-RESUME-211"}, out
    assert statuses.get("ACP-ERROR-201") == "PASS", out


def test_set_config_option_accepts_unknown_session_fails_error_201_only():
    """With `configOptions` advertised, the `set_config_option` probe runs and FAILs while the two
    `session/prompt` probes' own checks hold (the fixture's prompt handler is conforming)."""
    fails, statuses, out = _fails_for("set_config_option_accepts_unknown_session.py", _ERROR_K)
    assert fails == {"ACP-ERROR-201"}, out
    assert "session/set_config_option" in out, out


def test_answers_unadvertised_delete_fails_error_202_only():
    """`answers_unadvertised_delete.py` serves `session/delete` without advertising
    `session.delete` -- MANDATORY, so the verdict is NOT CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_unadvertised_delete.py", protocol_version=2, k=_ERROR_K)
    statuses = _table_statuses(result.stdout)
    fails = {r for r, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-ERROR-202"}, result.stdout
    assert "session/delete" in result.stdout, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_reserved_range_custom_code_fails_error_203_only():
    fails, statuses, out = _fails_for("reserved_range_custom_code.py", _ERROR_K)
    assert fails == {"ACP-ERROR-203"}, out
    assert "-32050" in out, out


def test_parse_error_wrong_code_fails_error_204_only():
    fails, _statuses, out = _fails_for("parse_error_wrong_code.py", "test_errors or test_informational")
    assert fails == {"ACP-ERROR-204"}, out
    assert "expected code -32700" in out, out


def test_parse_error_non_null_id_fails_error_204_only():
    fails, _statuses, out = _fails_for("parse_error_non_null_id.py", "test_errors or test_informational")
    assert fails == {"ACP-ERROR-204"}, out
    assert "expected id null" in out, out


def test_no_session_capability_agent_passes_unadvertised_probes():
    """`no_session_capability.py` answers every `session/*` method with `-32601`, so
    `ACP-ERROR-202` PASSes with the whole `session/*` baseline unadvertised; the session-scoped
    rows SKIP."""
    fails, statuses, out = _fails_for("no_session_capability.py", _ERROR_K)
    assert fails == set(), out
    assert statuses.get("ACP-ERROR-202") == "PASS", out
    assert statuses.get("ACP-ERROR-201") == "SKIPPED", out
    assert statuses.get("ACP-RESUME-211") == "SKIPPED", out


# --- version mismatch: a v1 agent run under --protocol-version 2 ---

# The negotiation rows (`ACP-INIT-001`/`003`/`201`/`202`/`208`) assert only on the negotiation
# *outcome*, never on the result's v2 shape, so an agent that honestly negotiates down to 1 still
# PASSes them. `ACP-INIT-205`/`206`/`207` bind agents implementing v2 only, so they SKIP. The v2-only *shape* rows (`info` required, object-only capability markers, v2
# schema validity, plus the CAPABILITY-tier session rows) cannot be meaningfully judged against
# a result the agent never claimed was v2-shaped, so they SKIP with the `VERSION-MISMATCH:`
# marker instead of FAILing (see `tck.v2.requirements`'s "Version-mismatch-aware v2-shape rows"
# section).
# `ACP-STATE-204` (ADVISORY) and the INFORMATIONAL probes carry the same
# `@pytest.mark.capability("capabilities.session")` marker as every other row below, so the
# autouse version-mismatch gate (`tck.common.plugin`'s `_tck_capability_gate`) skips them with
# the same `VERSION-MISMATCH:` marker too -- include them here alongside the MANDATORY/
# CAPABILITY rows rather than carving out a separate, unchecked set.
#
# A second, disjoint category: `ACP-JSONRPC-001..005` (not 202, which judges agent-authored
# requests and so SKIPs `VERSION-MISMATCH:` like the rows above) are connection-level rows whose own tests
# never drive a full v2-shaped `session/prompt` turn at all (`test_jsonrpc.py`'s tests only use
# `initialize`/`session/new`/bare notifications). A v1 agent's ordinary handshake/session/
# notification traffic satisfies all five of these unchanged, so -- like the negotiation rows --
# they PASS rather than SKIP here. `ACP-TRANSPORT-002`/`201`/`203`, despite also being
# connection-level, do NOT belong in this set: `test_transport.py`'s own `_drive_full_exchange`
# calls `skip_if_version_mismatch` itself before ever gathering evidence (see that module's
# docstring), specifically so it never has to drive v2-only `run_prompt` machinery against a
# mismatched agent -- so they SKIP, not PASS. Confirmed empirically: a full run of
# `test_transport.py`/`test_jsonrpc.py`/`test_batch.py` against
# `tests/fixtures/agents/v1/conforming.py` under `--protocol-version 2` produces zero FAILs,
# exactly the five JSONRPC ids PASS, and every other new id (all of
# `ACP-TRANSPORT-*`/`ACP-BATCH-*`) SKIPs with `VERSION-MISMATCH:`.
_NEGOTIATION_IDS = {"ACP-INIT-001", "ACP-INIT-003", "ACP-INIT-201", "ACP-INIT-202", "ACP-INIT-208"}
# ACP-EXT-001/201/203 probe an ordinary `_`-/`$/`-prefixed custom method or notification
# exchange -- they never inspect `initialize`'s negotiated version or its `capabilities` shape at
# all, so they PASS regardless of which protocolVersion was negotiated.
# ACP-EXT-202 is NOT included here: it reads `result.capabilities` (the v2 field name) directly,
# which a v1-negotiated result simply doesn't have (v1 uses `agentCapabilities` instead), so it
# correctly `pytest.skip("initialize result has no capabilities object to check")`s on its own --
# a genuine skip, not the VERSION-MISMATCH marker, but still a skip either way (see
# `test_extensibility.py`'s module docstring for the full breakdown).
_VERSION_TOLERANT_IDS = _NEGOTIATION_IDS | {
    "ACP-JSONRPC-001",
    "ACP-JSONRPC-002",
    "ACP-JSONRPC-003",
    "ACP-JSONRPC-004",
    "ACP-JSONRPC-005",
    "ACP-EXT-001",
    "ACP-EXT-201",
    "ACP-EXT-203",
    # ACP-CANCEL-210/211: connection-level `$/cancel_request` probes with no capability marker;
    # a reply to a notification is non-conforming in v1 too, so a v1 agent is judged normally.
    "ACP-CANCEL-210",
    "ACP-CANCEL-211",
    # ACP-INFO-PARSE-001/ACP-INFO-INVALIDREQ-001 (re-cited from v1, unchanged) carry no
    # `@pytest.mark.capability(...)` marker at all (test_informational.py's module docstring),
    # and their shared `_probe_connection_usable_after` helper swallows a `session/new` failure
    # -- including a version-mismatched/capability-unsupporting one -- into an "unusable"
    # behaviour string rather than letting it propagate, then only ever `record_property(...)`s
    # it, never asserts. So both PASS unconditionally, the same as the five JSONRPC ids above.
    "ACP-INFO-PARSE-001",
    "ACP-INFO-INVALIDREQ-001",
    # ACP-STDERR-001 (re-cited from v1, unchanged): also connection-level/no capability marker,
    # and its own `new_session(...)` call succeeds even against a v1-negotiated agent -- v1's
    # `conforming.py` implements `session/new` unconditionally at the wire level, with no
    # capability check of its own -- so this always PASSes regardless of negotiated version too.
    "ACP-STDERR-001",
    # ACP-ERROR-001/ACP-SHUTDOWN-001 (re-cited from v1, unchanged, `test_diagnostics.py`): same
    # story -- connection-level, no capability marker, and their own `session/new` (missing
    # `cwd`, or ordinary) calls succeed at the wire level against a v1-negotiated agent too.
    "ACP-ERROR-001",
    "ACP-SHUTDOWN-001",
}
_VERSION_MISMATCH_SKIP_IDS = (
    _MANDATORY_IDS | _CAPABILITY_IDS | _ADVISORY_IDS | _INFORMATIONAL_IDS
) - _VERSION_TOLERANT_IDS
assert _VERSION_TOLERANT_IDS | _VERSION_MISMATCH_SKIP_IDS == _ALL_IDS


def test_v1_conforming_agent_under_protocol_version_2_is_blocked_by_version_mismatch(tmp_path):
    """The v1 conforming fixture speaks only protocol version 1, so under `--protocol-version 2`
    it honestly negotiates down to `1` for every fresh handshake (a legacy v1-only agent returns
    v1 to a v2 request). The negotiation rows (`ACP-INIT-001`/`003`/`201`/`202`/`208`) are judged normally against
    that honest negotiation and PASS -- an agent that does not yet speak v2 is not thereby
    "broken". Every v2-only shape row (`ACP-INIT-203`/`204`/`ACP-SCHEMA-001`,
    `ACP-SESSION-001`/`002`) SKIPs with the `VERSION-MISMATCH:` marker instead of FAILing, since
    a v1-shaped result cannot be judged against v2 shape rules. Zero FAILs anywhere, yet the run
    as a whole is still NOT CONFORMANT with `verdict.blocked_by_version_mismatch == true`, exit
    code 1, and a terminal hint -- the version-dependent requirements were never actually
    exercised against v2."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V1,
        "conforming.py",
        protocol_version=2,
        report_json=str(report_path),
    )
    assert result.returncode != 0, result.stdout + result.stderr
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    assert "blocked by version mismatch" in result.stdout, result.stdout
    assert "negotiated protocol version" in result.stdout.lower() or "did not negotiate" in result.stdout.lower(), result.stdout

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), f"expected zero FAILs (honest downgrade, not a defect): {result.stdout}"
    for req_id in _VERSION_TOLERANT_IDS:
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    for req_id in _VERSION_MISMATCH_SKIP_IDS:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"

    report = json.loads(report_path.read_text())
    assert report["verdict"]["blocked_by_version_mismatch"] is True, report["verdict"]
    assert report["verdict"]["conformant"] is False, report["verdict"]

    skip_results = [r for r in report["requirements"] if r["id"] in _VERSION_MISMATCH_SKIP_IDS]
    assert len(skip_results) == len(_VERSION_MISMATCH_SKIP_IDS)
    for r in skip_results:
        assert r["status"] == "SKIPPED", r
        if r["id"] in _ALWAYS_SKIPPED_IDS:
            # ACP-CANCEL-204 is an unconditional record-only SKIP (MAY, never
            # exercised regardless of version) -- they SKIP here for that reason, not
            # because of the version mismatch, so they carry no VERSION-MISMATCH: marker.
            continue
        if r["id"] == "ACP-EXT-202":
            # ACP-EXT-202 carries no `@pytest.mark.capability(...)` marker either (it reads
            # `result.capabilities` -- the v2 field name -- directly, rather than going through
            # the autouse capability gate), so it never produces the VERSION-MISMATCH: marker
            # text; it still genuinely SKIPs here, just via its own plain
            # `pytest.skip("initialize result has no capabilities object to check")`, since a
            # v1-negotiated result has no `capabilities` key at all (v1 uses `agentCapabilities`
            # instead) -- see `test_extensibility.py`'s module docstring.
            continue
        assert any("VERSION-MISMATCH:" in t["message"] for t in r["tests"]), r["tests"]

    pass_results = [r for r in report["requirements"] if r["id"] in _VERSION_TOLERANT_IDS]
    assert len(pass_results) == len(_VERSION_TOLERANT_IDS)
    for r in pass_results:
        assert r["status"] == "PASS", r


def test_resume_sends_notice_passes_resume_202_and_init_204():
    """`resume_sends_notice.py` sends a live `notice` update right after `session/resume` and
    advertises `providers`. The draft allows both, so
    `ACP-RESUME-202` and `ACP-INIT-204` PASS and nothing FAILs."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_sends_notice.py",
        protocol_version=2,
        k="session_capabilities or initialize",
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert not fails, result.stdout
    assert statuses.get("ACP-RESUME-202") == "PASS", result.stdout
    assert statuses.get("ACP-INIT-204") == "PASS", result.stdout


def test_accepts_unknown_content_type_fails_prompt_211_only():
    """`accepts_unknown_content_type.py` accepts a `_tck_unknown` block; unadvertised
    `image`/`audio`/`resource` blocks are still rejected, so `ACP-PROMPTCAP-201` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2, "accepts_unknown_content_type.py", protocol_version=2, k="test_prompt"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-211"}, result.stdout
    assert statuses.get("ACP-PROMPTCAP-201") == "PASS", result.stdout


def test_accepts_unadvertised_content_fails_promptcap_201_only():
    """`accepts_unadvertised_content.py` advertises no prompt capability but accepts `image`,
    `audio` and `resource` blocks; the unknown `_tck_unknown` block is still rejected, so
    `ACP-PROMPT-211` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2, "accepts_unadvertised_content.py", protocol_version=2, k="test_prompt"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPTCAP-201"}, result.stdout
    assert statuses.get("ACP-PROMPT-211") == "PASS", result.stdout


def test_rejects_content_with_wrong_code_fails_prompt_211_and_promptcap_201():
    result = _run_cli(
        FIXTURES_DIR_V2, "rejects_content_with_wrong_code.py", protocol_version=2, k="test_prompt"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-211", "ACP-PROMPTCAP-201"}, result.stdout


def test_echoes_rejected_content_fails_prompt_211_and_promptcap_201():
    """`echoes_rejected_content.py` answers `-32602` but inserted the prompt first (echo plus
    `running`); the turn it started is closed, so the other prompt rows are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2, "echoes_rejected_content.py", protocol_version=2, k="test_prompt"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-211", "ACP-PROMPTCAP-201"}, result.stdout


# --- session setup, close, MCP (`ACP-SESSION-204/206..208`, `ACP-CLOSE-204/206/207`,
# `ACP-ADDDIRS-203`, `ACP-MCP-203..205`) -- defect fixtures ---

_SETUP_K = "test_session"


def test_accepts_relative_cwd_fails_session_204_only():
    fails, _statuses, out = _fails_for("accepts_relative_cwd.py", _SETUP_K)
    assert fails == {"ACP-SESSION-204"}, out


def test_adddirs_accepts_relative_fails_adddirs_203_only():
    fails, statuses, out = _fails_for("adddirs_accepts_relative.py", _SETUP_K)
    assert fails == {"ACP-ADDDIRS-203"}, out
    assert statuses.get("ACP-ADDDIRS-201") == "PASS", out
    assert statuses.get("ACP-ADDDIRS-202") == "PASS", out


def test_mcp_unsupported_transport_fixtures_fail_mcp_203_only():
    """One fixture per probe: `sse` accepted, or a `_`-prefixed custom type accepted."""
    for fixture in ("accepts_sse_mcp.py", "accepts_custom_mcp_transport.py"):
        fails, _statuses, out = _fails_for(fixture, _SETUP_K)
        assert fails == {"ACP-MCP-203"}, f"{fixture}:\n{out}"


def test_accepts_duplicate_mcp_names_fails_mcp_204_advisory_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "accepts_duplicate_mcp_names.py", protocol_version=2, k=_SETUP_K
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-MCP-204"}, result.stdout
    assert statuses.get("ACP-MCP-203") == "PASS", result.stdout


def test_permission_before_new_response_fails_session_206_only():
    fails, statuses, out = _fails_for("permission_before_new_response.py", _SETUP_K)
    assert fails == {"ACP-SESSION-206"}, out
    assert statuses.get("ACP-SESSION-207") == "PASS", out


def test_config_notified_before_new_response_fails_session_207_only():
    """The response carries the same `configOptions`, so `ACP-SESSION-208` PASSes."""
    fails, statuses, out = _fails_for("config_notified_before_new_response.py", _SETUP_K)
    assert fails == {"ACP-SESSION-207"}, out
    assert statuses.get("ACP-SESSION-208") == "PASS", out


def test_commands_only_in_early_notification_fails_session_207_and_208():
    fails, _statuses, out = _fails_for("commands_only_in_early_notification.py", _SETUP_K)
    assert fails == {"ACP-SESSION-207", "ACP-SESSION-208"}, out


def test_updates_after_close_fails_close_206_only():
    fails, statuses, out = _fails_for("updates_after_close.py", "session_capabilities")
    assert fails == {"ACP-CLOSE-206"}, out
    assert statuses.get("ACP-CLOSE-201") == "PASS", out


def test_close_twice_errors_fails_close_207_advisory_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "close_twice_errors.py", protocol_version=2, k="session_capabilities"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CLOSE-207"}, result.stdout
    assert statuses.get("ACP-CLOSE-201") == "PASS", result.stdout


def test_closes_before_prompt_passes_close_204_with_not_active_outcome(tmp_path):
    """`closes_before_prompt.py` answers a prompt sent just before a close `-32002`, since it
    processed the close first. A legal outcome: `ACP-CLOSE-204` PASSes and records `not_active`."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "closes_before_prompt.py",
        protocol_version=2,
        k="test_prompt_pending_at_close_is_answered",
        cancel_prompt="__close_first__",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CLOSE-204") == "PASS", result.stdout
    assert _fails(statuses) == set(), result.stdout
    by_id = {r["id"]: r for r in json.loads(report_path.read_text())["requirements"]}
    assert "not_active" in json.dumps(by_id["ACP-CLOSE-204"]), by_id["ACP-CLOSE-204"]


def test_leaks_mcp_credentials_fixtures_fail_mcp_205_advisory_only():
    """One fixture per leak channel: env values in `_meta` (stdout), stderr, the stub's command
    line, and header values in `_meta`. The other MCP rows still PASS."""
    for fixture in (
        "leaks_mcp_env_meta.py",
        "leaks_mcp_env_stderr.py",
        "leaks_mcp_env_argv.py",
        "leaks_mcp_header_meta.py",
    ):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SETUP_K)
        statuses = _table_statuses(result.stdout)
        assert _fails(statuses) == {"ACP-MCP-205"}, f"{fixture}:\n{result.stdout}"
        for req_id in ("ACP-MCP-201", "ACP-MCP-202", "ACP-MCP-203", "ACP-MCP-204"):
            assert statuses.get(req_id) == "PASS", f"{fixture} {req_id}:\n{result.stdout}"
