"""Full `acp-tck` runs against the conforming fixture agents: every row PASSes or SKIPs as
expected, and the verdict is CONFORMANT."""

from __future__ import annotations

import json

from .._expectations import (
    _ALL_IDS,
    _ALWAYS_SKIPPED_IDS,
    _BACKGROUND_OTHER_SKIP_IDS,
    _BACKGROUND_SKIP_IDS,
    _CHILD_CONTROL_IDS,
    _CHILD_REPLAY_WITHDRAWAL_IDS,
    _CONFORMING_EXPECTED_SKIPS,
    _MANDATORY_IDS,
    _RESUME_BACKGROUND_SKIP_IDS,
    _STALE_CANCEL_IDS,
    _V2_ONLY_SKIP_IDS,
)
from .._runner import FIXTURES_DIR_V2, _assert_conforming_baseline, _run_cli, _table_statuses


def test_v2_conforming_agent_passes_everything():
    """`conforming.py` advertises only the plain `session: {}` baseline -- no prompt-content
    capabilities, no `delete`/`archive`/`additionalDirectories`/`mcp`/`fork`/`systemPrompt` marker, no
    `configOptions`, no
    `authMethods`, and it never asks for permission or opts into `_send_rich_turn_updates`. So
    every capability row that needs more than that SKIPs rather than PASSes:
    `ACP-PROMPTCAP-001/002/003` ("not advertised"), `ACP-PERM-201..204`/`ACP-PERM-002` ("no
    permission request observed"), `ACP-DELETE-001..003/204/205`/`ACP-ARCHIVE-002..006,201`/`ACP-ADDDIRS-001/202`/`ACP-MCP-201/202`/
    `ACP-FORK-201..205`/`ACP-SYSPROMPT-001/202`/`ACP-CONFIG-001/002/201/203/206` (session-management
    extras absent), `ACP-AUTH-003/004/006` (no
    `authMethods`, no `--auth-method`/`--allow-logout`), and `ACP-ENUM-203`/
    `ACP-PATCH-204..212` (no rich turn updates, no permission request). `ACP-PATCH-201/203` and
    `ACP-ENUM-201` still PASS: the ordinary message-chunk/state-update traffic every turn already
    emits is enough to exercise them. `ACP-SESSION-203`/`ACP-RESUME-001/002/202/204..209`/
    `ACP-LIST-001..003/203..205`/`ACP-CLOSE-001`/`ACP-CLOSE-204` are gated on the baseline `capabilities.session` marker
    alone (present even as `{}`), so they PASS. `ACP-AUTH-002`/`005` PASS too -- each is judged
    against the absence of `authMethods`; `ACP-AUTH-001`/`206` SKIP instead of vacuously passing,
    since there is nothing to check uniqueness/type-shape of.

    Without a `--cancel-prompt` override, `conforming.py`'s short deterministic turns routinely
    resolve before the TCK can act on `session/cancel` at all, so `_CANCEL_RACE_SKIP_IDS`
    (including `ACP-CLOSE-002`/`203`, which drive the same race-prone close-mid-turn scenario)
    legitimately SKIP too ("cancellation not exercised") -- `ACP-CANCEL-205` (no direct response
    to the cancel notification itself) still PASSes regardless of that race, and
    `_ALWAYS_SKIPPED_IDS` SKIP unconditionally for any fixture. Every other id PASSes. See
    `conforming_full.py`'s own self-test below (with `--cancel-prompt __hang__`) for the "every
    exercisable id PASSes" fixture."""
    result = _run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2)
    _assert_conforming_baseline(result, "conforming.py")


# What `conforming_full.py` still SKIPs besides `_ALWAYS_SKIPPED_IDS`: `ACP-AUTH-005` (only
# concerns the empty-`authMethods` case), `ACP-PROMPT-207` (it never rejects a prompt), and
# `ACP-CANCEL-209`/`213` and `ACP-CLOSE-205` (`__hang__` preempts its permission request, so none
# is pending at cancel or close; `asks_permission.py`'s self-test exercises them instead), and
# `ACP-META-203/204` (it emits no
# `_meta` at all; `emits_w3c_meta.py` exercises them), and `_BACKGROUND_SKIP_IDS` (it reports
# no background work; `reports_background_work.py` exercises them).
# `ACP-ERROR-204` SKIPs for every `_base.py` fixture that stays silent on a non-JSON line.
# `ACP-SUBAGENT-001..014`/`-201` SKIP: it exposes no subagent (`exposes_subagent.py` exercises them),
# and so do `_CHILD_CONTROL_IDS` (`cancellable_subagent.py` exercises them).
_FULL_EXPECTED_SKIPS = {
    "ACP-ADDDIRS-204",  # advertises additionalDirectories
    "ACP-SUBAGENT-001",
    "ACP-SUBAGENT-002",
    "ACP-SUBAGENT-003",
    "ACP-SUBAGENT-004",
    "ACP-SUBAGENT-005",
    "ACP-SUBAGENT-006",
    "ACP-SUBAGENT-007",
    "ACP-SUBAGENT-008",
    "ACP-SUBAGENT-009",
    "ACP-SUBAGENT-011",
    "ACP-SUBAGENT-012",
    "ACP-SUBAGENT-013",
    "ACP-SUBAGENT-014",
    "ACP-SUBAGENT-201",
    "ACP-SUBAGENT-205",
    "ACP-SUBAGENT-206",
    "ACP-SUBAGENT-207",
    "ACP-SUBAGENT-018",
    "ACP-SUBAGENT-019",
    "ACP-LIST-004",
    "ACP-AUTH-005",
    "ACP-PROMPT-207",
    "ACP-PROMPTCAP-201",  # every prompt capability is advertised, so no negative case applies
    "ACP-CANCEL-209",
    "ACP-CANCEL-213",
    "ACP-CLOSE-205",
    "ACP-ERROR-204",
    "ACP-META-203",
    "ACP-META-204",
    "ACP-FORK-206",  # no listed work at fork time
    "ACP-RESUME-222",  # no agent request during a resume (`requests_before_replay_complete.py` sends one)
} | _STALE_CANCEL_IDS | _BACKGROUND_SKIP_IDS | _RESUME_BACKGROUND_SKIP_IDS | _BACKGROUND_OTHER_SKIP_IDS | _CHILD_CONTROL_IDS | _CHILD_REPLAY_WITHDRAWAL_IDS


def test_v2_conforming_full_agent_passes_everything():
    """`conforming_full.py` advertises `capabilities.session.prompt.{image,audio,
    embeddedContext}`, asks for permission with a `tool_call` subject on every turn
    (`AsksPermissionAgent`, `permission_tool_call=True`), opts into
    `_send_rich_turn_updates` (two message chunks sharing one `messageId`, one tool_call
    create+patch sharing one `toolCallId`, one plan_update with one `planId`), and advertises one
    `type: "agent"` authMethods entry (`methodId: "tck"`). Run with `--cancel-prompt __hang__
    --auth-method tck --allow-logout`, this exercises essentially every capability: every
    prompt-content/permission/client-capability id, `ACP-PATCH-201/203..216` and
    `ACP-ENUM-201/203`, `ACP-AUTH-003/004`, and every CAPABILITY-tier `ACP-CANCEL-*` id but
    `ACP-CANCEL-209` all PASS. The INFORMATIONAL probe PASSes too (an INFORMATIONAL test PASSes as
    long as it never hits an assertion failure or setup/teardown error -- it never asserts on the
    behaviour it probes, only records it).

    `conforming_full.py` also advertises a `type: "terminal"` auth method on any connection that
    advertises `capabilities.auth.terminal` (`ACP-AUTH-002` still PASSes since that descriptor
    never appears on the default connection this fixture also answers), and emits one
    `terminal_update` + one `terminal_output_chunk` per turn under the same
    `emit_rich_turn_updates` flag -- so `ACP-AUTH-006`/`ACP-PATCH-206`/`ACP-PATCH-207` all PASS
    too, instead of SKIPping "nothing to check"/"no <variant> observed". Its `__hang__` turn also
    leaves a tool call and a terminal open that advertise `capabilities.cancel` and implements
    `tool_call/cancel`/`terminal/cancel` for them (`cancellable_work`), so
    `ACP-TOOLCANCEL-201/202` and `ACP-TERMCANCEL-201/202` PASS (its items stop advertising `cancel`
    once final, so the `-204/205` already-final rows SKIP). It also sets `uncancellable_work`
    (a live tool call and terminal without `cancel`), so the unknown-id and not-cancellable
    requests are sent and `-206-209` PASS as well; this run is their only whole-suite PASS-side
    coverage, so do not add them to `_FULL_EXPECTED_SKIPS`.

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


def test_v2_conforming_full_agent_without_allow_logout_only_skips_auth_004():
    """Acceptance criterion: the same `conforming_full.py --auth-method tck` run, but WITHOUT
    `--allow-logout`, must SKIP ONLY `ACP-AUTH-004`/`211` in addition to the baseline's own SKIPs
    (`_ALWAYS_SKIPPED_IDS` plus `ACP-AUTH-005`, per
    `test_v2_conforming_full_agent_passes_everything` above) -- every other id keeps the exact
    same status. `ACP-AUTH-003` still PASSes here since `--auth-method tck` alone is enough to
    exercise `auth/login`; only `auth/logout` (`ACP-AUTH-004`) requires the separate
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
    expected_skips = _ALWAYS_SKIPPED_IDS | _FULL_EXPECTED_SKIPS | {"ACP-AUTH-004", "ACP-AUTH-211"}
    for req_id, status in statuses.items():
        if req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", f"{req_id} is {status}, expected PASS without --allow-logout:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_v2_conforming_full_agent_default_cancel_prompt_passes_close_and_delete_cancel():
    """Without `--cancel-prompt __hang__` (the whole-suite run above passes it, which preempts the
    permission request) `conforming_full.py`'s default cancel turn ends blocked on a pending
    `session/request_permission`. `session/close` and `session/delete` must withdraw it and send
    the cancelled idle before answering, so `ACP-CLOSE-002/203/205` and `ACP-DELETE-204` PASS
    (not SKIP, not FAIL): the permission request is always pending when the trigger lands."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "conforming_full.py",
        protocol_version=2,
        k="test_close_cancels_foreground_work or test_close_sends_cancelled_idle_before_responding "
        "or test_close_withdraws_the_pending_permission_request or test_delete_cancels_foreground_work",
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    for req_id in ("ACP-CLOSE-002", "ACP-CLOSE-203", "ACP-CLOSE-205", "ACP-DELETE-204"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


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
    # ACP-AUTH-001/006/206 SKIP: this fixture advertises no `authMethods` to check.
    no_pass = {"ACP-AUTH-001", "ACP-AUTH-206", "ACP-AUTH-006", "ACP-JSONRPC-202"} | _V2_ONLY_SKIP_IDS
    for req_id in _MANDATORY_IDS - no_pass:
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert statuses.get("ACP-JSONRPC-202") == "SKIPPED", result.stdout
    report = json.loads(report_path.read_text())
    by_id = {r["id"]: r for r in report["requirements"]}
    for req_id in ("ACP-SESSION-001", "ACP-ENUM-203", "ACP-PROMPT-201", "ACP-CONFIG-201"):
        assert by_id[req_id]["status"] == "SKIPPED", by_id[req_id]
        assert all("not advertised" in t["message"] for t in by_id[req_id]["tests"]), by_id[req_id]
