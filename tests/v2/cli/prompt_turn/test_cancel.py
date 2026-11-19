"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_cancel.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _TOOL_CALL_K, _fails, _fails_for, _run_cli, _table_statuses


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


def test_cancel_without_cancel_request_fails_cancel_213_only():
    """`ACP-CANCEL-213` is CAPABILITY (a MUST upstream), so its FAIL makes the run non-conformant."""
    result = _run_cli(
        FIXTURES_DIR_V2, "cancel_without_cancel_request.py", protocol_version=2, k="cancel"
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CANCEL-213"}, result.stdout
    assert statuses["ACP-CANCEL-209"] == "PASS", result.stdout
    assert statuses["ACP-CLOSE-205"] == "PASS", result.stdout


def test_close_keeps_permission_open_fails_close_205_only():
    result = _run_cli(FIXTURES_DIR_V2, "close_keeps_permission_open.py", protocol_version=2, k="cancel")
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CLOSE-205"}, result.stdout
    for req_id in ("ACP-CANCEL-208", "ACP-CANCEL-209", "ACP-CANCEL-213", "ACP-CLOSE-002"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"


def test_answers_cancel_request_fails_jsonrpc_006_007_and_cancel_211_only():
    """Answering a `$/cancel_request` for an unknown or answered id breaks 210/211; the withdrawn
    prompt, already answered, gets that error as a second response (212)."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_cancel_request.py", protocol_version=2)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-JSONRPC-006", "ACP-CANCEL-211", "ACP-JSONRPC-007"}, result.stdout


def test_drops_withdrawn_prompt_fails_jsonrpc_007_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "drops_withdrawn_prompt.py", protocol_version=2, k="cancel",
        cancel_prompt="__hang__",
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-JSONRPC-007"}, result.stdout


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
    # `ACP-JSONRPC-007`: the held prompt ignores `$/cancel_request`, and the TCK's follow-up
    # `session/cancel` gets it answered `-32800`.
    for req_id in (
        "ACP-CANCEL-203", "ACP-CANCEL-205", "ACP-CANCEL-208", "ACP-JSONRPC-007", "ACP-CLOSE-002",
        "ACP-PROMPT-207",
    ):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"
    for req_id in ("ACP-CANCEL-001", "ACP-CANCEL-002", "ACP-CANCEL-206", "ACP-CANCEL-207"):
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"


def test_cancel_no_idle_fails_every_cancel_dependent_id():
    """`cancel_no_idle.py` hangs on *every* prompt (not just the dedicated cancel-test one) and
    silently ignores `session/cancel` -- so every test that drives a turn through `run_prompt` at
    all times out with an uncaught `AgentTimeout`, a FAIL (not a SKIP -- see
    `docs/requirements.md` "Statuses"), the same broad cascade shape as `no_idle_after_running.py`/
    `update_wrong_session.py` above. `ACP-CANCEL-208`/`ACP-CLOSE-002`/`ACP-CLOSE-203` are the
    exception: `session/close` still rescues the hanging turn via `ConformingAgent`'s inherited
    default handler, so they PASS. Also FAILs `ACP-RESUME-002`/`202`/`204`..`206`/`209`
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
        "ACP-TRANSPORT-001",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
        "ACP-CANCEL-001",
        "ACP-CANCEL-002",
        "ACP-CANCEL-203",
        "ACP-CANCEL-205",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
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
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-002",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-CANCEL-209",
        "ACP-CANCEL-204",
        "ACP-PROMPT-003",
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
    assert statuses.get("ACP-CANCEL-208") == "PASS", result.stdout
    assert statuses.get("ACP-CLOSE-002") == "PASS", result.stdout
    assert statuses.get("ACP-CLOSE-203") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_cancel_returns_error_fails_cancel_203_and_208_only():
    """`cancel_returns_error.py` withholds `session/prompt`'s own acceptance receipt entirely for
    *every* turn, not just the dedicated cancel-test one, until `session/cancel` arrives -- so
    every id whose own test drives an ordinary (non-cancelling) `run_prompt` turn never even gets
    that far and FAILs with a timeout: `ACP-SCHEMA-001`, `ACP-TRANSPORT-001/002/203`,
    `ACP-CLIENTCAP-003/202`, `ACP-PERM-201`, `ACP-PROMPT-002/201/203`, `ACP-STATE-201/202/203`,
    `ACP-PROMPT-003`, and `ACP-PROMPT-211` (its rejected probe prompt is never answered either).
    On top of that cascade, cancelling itself resolves the
    prompt with a JSON-RPC error instead of a terminating idle -- FAILs `ACP-CANCEL-203` (the
    error itself) and `ACP-CANCEL-208`/`ACP-CLOSE-002`/`ACP-CLOSE-203` (a `session/close` sent
    instead has nothing registered to rescue either, since `_handle_prompt` never adds the
    session to `_hanging_sessions`); for the same reason the ADVISORY `ACP-CLOSE-204` FAILs in the
    cascade run -- the prompt pending at close is never answered. `ACP-CANCEL-001`/`002`/`206`/`207` SKIP,
    deferring to `ACP-CANCEL-203` -- the turn never reaches a terminating idle at all. Also FAILs
    `ACP-RESUME-002`/`202`/`204`..`206`/`209` (their own tests drive a `run_prompt` turn via `_session_with_history`
    first, which never resolves either since this fixture withholds its acceptance receipt on
    every turn). The same cascade also catches every other `run_prompt`-driven id -- `ACP-
    ENUM-201` (`test_enums.py`), `ACP-META-001/201`/`ACP-SCHEMA-002` (`test_extensibility.py`),
    and the whole `ACP-PATCH-2xx` family (`test_patches.py`) -- `-k` widened to select those
    three modules too.

    Perf note: split into two `_run_cli` invocations instead of one broad-`-k` run.
    `test_cancel.py` itself (`cancel_result`) needs `--tck-timeout 1` -- at `0.5` its own
    `run_prompt(on_cancel=True, cancel_wait=0.5)` races the fixed `cancel_wait` against the
    read-response deadline and spuriously FAILs `ACP-CANCEL-001/002/206/207` instead of SKIPping
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
        "ACP-CLOSE-002",
        "ACP-CLOSE-203",
    }, cancel_result.stdout
    assert cascade_fails == {
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-TRANSPORT-001",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
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
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-002",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-PROMPT-003",
        "ACP-PROMPT-211",
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
    }, cascade_result.stdout
    for req_id in ("ACP-CANCEL-001", "ACP-CANCEL-002", "ACP-CANCEL-206", "ACP-CANCEL-207"):
        assert cancel_statuses.get(req_id) == "SKIPPED", f"{req_id}: {cancel_result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in cancel_result.stdout, cancel_result.stdout
    assert "VERDICT: NOT CONFORMANT" in cascade_result.stdout, cascade_result.stdout


def test_cancel_wrong_stop_reason_fails_cancel_001_203_206_207_only():
    """`cancel_wrong_stop_reason.py` hangs on *every* prompt (not just the dedicated cancel-test
    one), so every id whose own test drives an ordinary (non-cancelling) `run_prompt` turn times
    out too, the same broad cascade shape as `cancel_no_idle.py` above: `ACP-SCHEMA-001`,
    `ACP-TRANSPORT-001/002/203`, `ACP-CLIENTCAP-003/202`, `ACP-PERM-201`,
    `ACP-PROMPT-002/201/203`, `ACP-STATE-201/202/203`, and `ACP-PROMPT-003`. For the
    cancel scenario itself -- a deliberate 1.2s delay clears the TCK's own race window (see the
    fixture's own module docstring; needs `--timeout 2` for that delay to fit comfortably inside
    the wait) before resolving with `stopReason: "end_turn"` instead of `"cancelled"` -- FAILs
    `ACP-CANCEL-001`/`203`/`207` and `ACP-CANCEL-206` (the `_meta`-carrying scenario hits the same
    overridden handler). `ACP-CANCEL-002`/`208` SKIP/PASS respectively, deferring to the rows
    above; `ACP-CLOSE-203` PASSes (closing still rescues the turn as `cancelled`). Also FAILs
    `ACP-RESUME-002`/`202`/`204`..`206`/`209` (their own tests drive a `run_prompt` turn via
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
        "ACP-CANCEL-001",
        "ACP-CANCEL-203",
        "ACP-CANCEL-206",
        "ACP-CANCEL-207",
    }, cancel_result.stdout
    assert cascade_fails == {
        "ACP-SCHEMA-001",
        "ACP-SCHEMA-002",
        "ACP-TRANSPORT-001",
        "ACP-TRANSPORT-002",
        "ACP-TRANSPORT-203",
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
        "ACP-PROMPT-201",
        "ACP-PROMPT-203",
        "ACP-PROMPT-002",
        "ACP-STATE-201",
        "ACP-STATE-202",
        "ACP-STATE-203",
        "ACP-STATE-204",
        "ACP-STATE-205",
        "ACP-PROMPT-207",
        "ACP-PROMPT-003",
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
    }, cascade_result.stdout
    assert cancel_statuses.get("ACP-CANCEL-002") == "SKIPPED", cancel_result.stdout
    assert cancel_statuses.get("ACP-CANCEL-208") == "PASS", cancel_result.stdout
    assert cancel_statuses.get("ACP-CLOSE-203") == "PASS", cancel_result.stdout
    assert "VERDICT: NOT CONFORMANT" in cancel_result.stdout, cancel_result.stdout
    assert "VERDICT: NOT CONFORMANT" in cascade_result.stdout, cascade_result.stdout


def test_close_no_cancel_idle_fails_cancel_208_and_close_002_203_only():
    """`close_no_cancel_idle.py` keeps `ConformingAgent`'s default hang behaviour (hangs only on
    the literal `__hang__` sentinel), so the defect is bounded and only observable when driven
    with `--cancel-prompt __hang__`: `session/close` on a still-hanging prompt replies to the
    close normally but resolves the pending turn with `stopReason: "end_turn"` instead of
    `"cancelled"`, after a deliberate delay past the TCK's race window. FAILs exactly
    `ACP-CANCEL-208`/`ACP-CLOSE-002` (both dual-bound to `test_close_cancels_foreground_work`)
    and `ACP-CLOSE-203`, whose own close-mid-turn run times out the same way (the delayed idle
    lands past `--timeout`). Every other id, including plain `ACP-CANCEL-001/002/203..207` (which use
    `session/cancel`, not `session/close`) and `ACP-CLOSE-001` (closing an already-idle
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
    assert fails == {"ACP-CANCEL-208", "ACP-CLOSE-002", "ACP-CLOSE-203"}, result.stdout
    assert statuses.get("ACP-CLOSE-001") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_permission_before_requires_action_judges_cancel_while_blocked():
    """`permission_before_requires_action.py` sends its permission request before
    `requires_action` (the spec diagram's order), so the held request is cancelled while the
    session is still `running`. `ACP-CANCEL-209`/`213` are judged and PASS; nothing FAILs."""
    fails, statuses, stdout = _fails_for("permission_before_requires_action.py", _TOOL_CALL_K)
    assert fails == set(), stdout
    for req_id in ("ACP-CANCEL-209", "ACP-CANCEL-213", "ACP-PATCH-209", "ACP-PERM-201"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"
