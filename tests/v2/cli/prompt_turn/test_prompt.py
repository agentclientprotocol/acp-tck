"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_prompt.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._expectations import (
    _ALWAYS_SKIPPED_IDS,
    _BACKGROUND_OTHER_SKIP_IDS,
    _BACKGROUND_SKIP_IDS,
    _CANCEL_RACE_SKIP_IDS,
    _CHILD_CONTROL_IDS,
    _CHILD_REPLAY_WITHDRAWAL_IDS,
    _ITEM_CANCEL_IDS,
    _NO_AUTH_SKIP_IDS,
    _RESUME_BACKGROUND_SKIP_IDS,
    _SESSION_MGMT_EXTRAS_SKIP_IDS,
)
from .._runner import FIXTURES_DIR_V2, _PERMISSION_FLOW_K, _fails, _fails_for, _run_cli, _table_statuses


# `ACP-PROMPTCAP-001/002/003` SKIP whenever the agent doesn't advertise the corresponding
# `capabilities.session.prompt.*` marker, and `ACP-PERM-201`/`202` SKIP whenever a turn never
# actually triggers a `session/request_permission` (`ACP-PERM-203`/`204`/`002` also need a `tool_call`
# subject) -- both legitimate, expected SKIPs (not
# FAILs) for a fixture that neither advertises nor exercises them.
#
# A fixture that never opts into `_base.py`'s `_send_rich_turn_updates` (`emit_rich_turn_updates`
# defaults to `False`) never emits a tool_call_update/plan_update/terminal_update/
# terminal_output_chunk at all, and never asks for permission either -- so these all legitimately
# SKIP ("no <variant> observed") rather than PASS, exactly as they do for `conforming.py` itself
# (see `test_v2_conforming_agent_passes_everything` above).
_NOT_ADVERTISED_OR_EXERCISED_SKIP_IDS = {
    "ACP-PROMPT-218",  # the fixture keeps no session across processes
    "ACP-SUBAGENT-001",  # the fixture exposes no subagent
    "ACP-SUBAGENT-002",  # nor any `session` content
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
    "ACP-JSONRPC-202",
    "ACP-ERROR-204",  # the fixture stays silent on a non-JSON line
    "ACP-PROMPTCAP-001",
    "ACP-PROMPTCAP-002",
    "ACP-PROMPTCAP-003",
    "ACP-PROMPTCAP-202",
    "ACP-PERM-201",
    "ACP-PERM-202",
    "ACP-PERM-203",
    "ACP-PERM-002",
    "ACP-PERM-204",
    "ACP-ENUM-203",
    "ACP-ENUM-204",
    "ACP-META-203",
    "ACP-META-204",
    "ACP-PATCH-204",
    "ACP-PATCH-205",
    "ACP-PLAN-003",
    "ACP-PATCH-206",
    "ACP-PATCH-207",
    "ACP-PATCH-208",
    "ACP-PATCH-209",
    "ACP-PATCH-210",
    "ACP-PATCH-211",
    "ACP-PATCH-212",
    "ACP-PATCH-213",
    "ACP-PATCH-214",
    "ACP-PATCH-215",
    "ACP-PATCH-216",
    "ACP-STATE-205",
    "ACP-CANCEL-209",
    "ACP-CANCEL-213",
    "ACP-CLOSE-205",
    "ACP-PROMPT-207",
    "ACP-SUGGEST-001",  # the fixture sends no suggestion
    "ACP-SUGGEST-002",
    "ACP-SUGGEST-003",
    "ACP-SUGGEST-004",
    "ACP-RESUME-222",  # the fixture sends no request during a resume
    "ACP-CURSOR-001",  # the fixture announces no cursor
    "ACP-CURSOR-002",
    "ACP-CURSOR-003",  # ... and advertises no `fork`
    "ACP-CURSOR-004",
    "ACP-OPTIONS-001",  # the fixture advertises no `session.options`
    "ACP-OPTIONS-002",
    "ACP-OPTIONS-003",
    "ACP-OPTIONS-009",
    "ACP-OPTIONS-004",
    "ACP-OPTIONS-005",
    "ACP-OPTIONS-006",
    "ACP-OPTIONS-007",
    "ACP-OPTIONS-008",
    "ACP-OPTIONS-010",
    "ACP-OPTIONS-011",
    "ACP-OPTIONS-201",
} | _BACKGROUND_SKIP_IDS | _RESUME_BACKGROUND_SKIP_IDS | _BACKGROUND_OTHER_SKIP_IDS | _ITEM_CANCEL_IDS | _CHILD_CONTROL_IDS | _CHILD_REPLAY_WITHDRAWAL_IDS


def test_bad_stop_reason_fails_state_203_only():
    """`bad_stop_reason.py`'s defect (every non-`__hang__` prompt -- including the dedicated
    cancel-test prompt -- resolves immediately with an invalid `stopReason: "done"`) cascades
    into every `run_prompt`-driven cancel check: the terminating idle never says `"cancelled"`,
    and `"done"` is not a recognised `StopReason` the TCK's race heuristic would excuse as "the
    agent simply finished on its own" (mirrors v1's `bad_stop_reason.py` cascading into
    `ACP-CANCEL-001`). `ACP-CLOSE-002` shares `ACP-CANCEL-208`'s exact test, so it FAILs
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
        "ACP-CANCEL-001",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CANCEL-208",
        "ACP-CLOSE-002",
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
    `ACP-CLIENTCAP-003/202` (both observe a turn via `run_prompt`), `ACP-PERM-201` (never gets
    the chance to legitimately SKIP "no permission observed" -- it times out instead), the
    `ACP-PROMPT-003`, every `run_prompt`-driven `ACP-CANCEL-*` row (they never see a
    terminating idle either) plus `ACP-CLOSE-002` (shares `ACP-CANCEL-208`'s test),
    `ACP-CANCEL-204` (INFORMATIONAL, but an uncaught `AgentTimeout` is a FAIL, not a SKIP),
    except `ACP-CANCEL-213`/`ACP-CLOSE-205`, which SKIP when the turn never ends,
    `ACP-CLOSE-203` (its close-mid-turn run times out the same way),
    `ACP-TRANSPORT-001/002/203` (`test_transport.py`'s own `_drive_full_exchange` drives one
    ordinary `run_prompt` turn to gather evidence, which times out here too), `ACP-RESUME-
    202..206`/`209` (their own tests drive a `run_prompt` turn via `_session_with_history` to have
    something to replay, which also never resolves -- `ACP-RESUME-001` is unaffected, no prompt
    turn needed, and `ACP-CLOSE-002` FAILs alongside `ACP-CANCEL-208` since they share the same
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
        "ACP-PROMPT-002",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-003",
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-CANCEL-209",
        "ACP-CLIENTCAP-003",
        "ACP-CLIENTCAP-008",
        "ACP-CLIENTCAP-202",
        "ACP-CLIENTCAP-203",
        "ACP-PROMPT-220",
        "ACP-SUGGEST-001",
        "ACP-SUGGEST-002",
        "ACP-SUGGEST-003",
        "ACP-SUGGEST-004",
        "ACP-PERM-201",
        "ACP-CANCEL-001",
        "ACP-CANCEL-002",
        "ACP-CANCEL-203",
        "ACP-CANCEL-205",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CANCEL-208",
        "ACP-CANCEL-204",
        "ACP-CLOSE-002",
        "ACP-CLOSE-203",
        "ACP-RESUME-202",
        "ACP-RESUME-002",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-217",
        "ACP-RESUME-218",
        "ACP-RESUME-219",
        "ACP-RESUME-220",
        "ACP-RESUME-221",
        "ACP-RESUME-222",
        "ACP-RESUME-223",
        "ACP-RESUME-224",
        "ACP-RESUME-225",
        "ACP-RESUME-226",
        "ACP-RESUME-214",
        "ACP-TRANSPORT-001",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PLAN-003",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PERM-204",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
        "ACP-PATCH-213",
        "ACP-PATCH-214",
        "ACP-PATCH-215",
        "ACP-PATCH-216",
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
    *distinct* ids) -- within this `-k`, which selects those two modules too. Everything else is deselected (`NOT_TESTED`) rather than re-verified here."""
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
    `ACP-CLIENTCAP-003/202`/`ACP-PERM-201`/`ACP-PROMPT-003`/every `run_prompt`-driven
    `ACP-CANCEL-*` row but `213` (plus `ACP-CLOSE-002`, sharing `ACP-CANCEL-208`'s test)/
    `ACP-TRANSPORT-001/002/203` are included here too), since `run_prompt` never recognizes a
    matching terminating idle either. Also FAILs `ACP-RESUME-002`/`202`/`204`..`206`/`209` (their own tests drive a
    `run_prompt` turn via `_session_with_history` first, which never resolves either) and
    `ACP-PATCH-209` (same "permission" `-k` substring incidence explained on
    `no_idle_after_running.py`'s test above) -- and, for the same reason, every other
    `run_prompt`-driven id: `ACP-ENUM-201`, `ACP-META-001/201`, `ACP-SCHEMA-002`, and the
    rest of the `ACP-PATCH-2xx` family -- the same FAIL set as `no_idle_after_running.py`'s within
    this scope, since both fixtures never send a terminating idle at all."""
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
        "ACP-PROMPT-002",
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-003",
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-CANCEL-209",
        "ACP-CLIENTCAP-003",
        "ACP-CLIENTCAP-008",
        "ACP-CLIENTCAP-202",
        "ACP-CLIENTCAP-203",
        "ACP-PROMPT-220",
        "ACP-SUGGEST-001",
        "ACP-SUGGEST-002",
        "ACP-SUGGEST-003",
        "ACP-SUGGEST-004",
        "ACP-PERM-201",
        "ACP-CANCEL-001",
        "ACP-CANCEL-002",
        "ACP-CANCEL-203",
        "ACP-CANCEL-205",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
        "ACP-CANCEL-208",
        "ACP-CANCEL-204",
        "ACP-CLOSE-002",
        "ACP-CLOSE-203",
        "ACP-RESUME-202",
        "ACP-RESUME-002",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-217",
        "ACP-RESUME-218",
        "ACP-RESUME-219",
        "ACP-RESUME-220",
        "ACP-RESUME-221",
        "ACP-RESUME-222",
        "ACP-RESUME-223",
        "ACP-RESUME-224",
        "ACP-RESUME-225",
        "ACP-RESUME-226",
        "ACP-RESUME-214",
        "ACP-TRANSPORT-001",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-PATCH-201",
        "ACP-PATCH-203",
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PLAN-003",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-209",
        "ACP-PERM-202",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PERM-204",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
        "ACP-PATCH-213",
        "ACP-PATCH-214",
        "ACP-PATCH-215",
        "ACP-PATCH-216",
        "ACP-ENUM-201",
        "ACP-META-001",
        "ACP-META-201",
        "ACP-META-202",
        "ACP-META-203",
        "ACP-META-204",
    }, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


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


def test_requires_action_no_running_fails_state_205_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "requires_action_no_running.py", protocol_version=2, k=_PERMISSION_FLOW_K
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-STATE-205"}, result.stdout
    assert statuses["ACP-PATCH-209"] == "PASS", result.stdout


def test_error_after_echo_fails_prompt_207_and_cancel_203_only():
    """Answering an already-echoed prompt with `-32800` after cancel violates the insertion
    boundary: `ACP-PROMPT-207` (error after a user-message update), `ACP-CANCEL-203` (`-32800`
    is only for a prompt cancelled before insertion), and `ACP-JSONRPC-007` (its withdrawn prompt
    ignores `$/cancel_request`, and the TCK's follow-up `session/cancel` gets the same `-32800`
    after the echo). The cancelled idle itself is correct, so `ACP-CANCEL-001` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2, "error_after_echo.py", protocol_version=2, k="cancel", cancel_prompt="__hang__"
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-207", "ACP-CANCEL-203", "ACP-JSONRPC-007"}, result.stdout
    assert statuses["ACP-CANCEL-001"] == "PASS", result.stdout
    assert statuses["ACP-CANCEL-208"] == "PASS", result.stdout


def test_sends_skill_in_agent_message_fails_prompt_220_only():
    """The ADVISORY row FAILs on an agent message chunk holding a `skill` block."""
    fails, _statuses, out = _fails_for("sends_skill_in_agent_message.py", "test_no_skill_block_outside_user_messages")
    assert fails == {"ACP-PROMPT-220"}, out
    assert "agent_message_chunk" in out, out


def test_conforming_agents_pass_prompt_220():
    for fixture in ("conforming.py", "conforming_full.py"):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_no_skill_block_outside_user_messages")
        assert _table_statuses(result.stdout).get("ACP-PROMPT-220") == "PASS", f"{fixture}:\n{result.stdout}"


def test_accepts_unknown_content_type_fails_prompt_211_only():
    """`accepts_unknown_content_type.py` accepts a `_tck_unknown` block; unadvertised
    `image`/`audio`/`resource` blocks are still rejected, so `ACP-PROMPTCAP-201` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2, "accepts_unknown_content_type.py", protocol_version=2, k="test_prompt"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-211"}, result.stdout
    assert statuses.get("ACP-PROMPTCAP-201") == "PASS", result.stdout


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
