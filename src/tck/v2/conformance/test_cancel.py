"""Cancellation conformance: ACP-CANCEL-201..209, ACP-INFO-CANCEL-201/202.

`ACP-CLOSE-202` is also bound to `test_close_cancels_foreground_work` below, alongside its own
`ACP-CANCEL-208` id -- see `tck.v2.requirements` for why this is a deliberate reuse rather than
a duplicate probe.

v2 confirms cancellation with a `state_update {state: "idle", stopReason: "cancelled"}`, not
the `session/prompt` response (only an acceptance receipt; prompt-lifecycle.mdx:1109-1113,1124).
A prompt cancelled before insertion is instead answered `-32800`, and then owes an idle only if
foreground work was active (:1094,1115-1117). `ACP-CANCEL-204` is INFORMATIONAL (promptness has
no wire signal) and always SKIPs after recording what it saw; `ACP-INFO-CANCEL-201/202` record
behaviour without asserting. Everything else is CAPABILITY on `capabilities.session`.

**The race, and the honest-SKIP pattern**: `run_prompt(..., on_cancel=True)` fires
`session/cancel` on the first transition to an active state (or after `cancel_wait`).
`_skip_if_turn_end_race_not_exercised` treats these as **not exercised**, not a defect:

1. the trigger was never sent (the turn ended first);
2. the prompt was answered with an error before the trigger was sent;
3. the turn-ending idle arrives within `quiet_period(...)` of the trigger with a stop reason the
   agent could plausibly have reached on its own: `end_turn`/`max_tokens`/`max_turn_requests`/
   `refusal`, a `_`-prefixed one, or none at all (stopReason is only SHOULD).

`error` is never excused: reporting an abort as `error` is exactly the defect the spec singles
out (:1124). Reserved non-`_` values and late plausible ones are judged too.

`ACP-CANCEL-201`/`207` share one test: a single `stopReason == "cancelled"` check evidences both
the "MUST send a cancelled idle" rule and the "no illegal substitute value" rule.

`ACP-CANCEL-209` holds the agent's own `session/request_permission` unanswered while sending
`session/cancel`, so the agent is blocked on the TCK when cancel lands: no race window applies.
"""

from __future__ import annotations

import pytest

from tck.common.harness import AgentTimeout, Direction

from ..protocol import REQUEST_CANCELLED, STOP_REASONS
from ._helpers import (
    connected_agent,
    is_response_line,
    iter_messages,
    new_session,
    probe_behaviour,
    quiet_period,
    run_prompt,
)

# Stop reasons an agent may have reached on its own just before reading the trigger.
_RACE_PLAUSIBLE_STOP_REASONS = frozenset({"end_turn", "max_tokens", "max_turn_requests", "refusal"})
_AGENT_OUTPUT_KINDS = frozenset(
    {"agent_message", "agent_message_chunk", "agent_thought", "agent_thought_chunk"}
)


def _race_plausible(stop_reason) -> bool:
    return (
        stop_reason is None
        or stop_reason in _RACE_PLAUSIBLE_STOP_REASONS
        or (isinstance(stop_reason, str) and stop_reason.startswith("_"))
    )


def _response_error(turn) -> dict | None:
    msg = turn.response_entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return error if isinstance(error, dict) else None


def _user_message_echoed(turn) -> bool:
    for _, entry in turn.updates:
        params = entry.parsed.get("params") if isinstance(entry.parsed, dict) else None
        if not isinstance(params, dict) or params.get("sessionId") != turn.session_id:
            continue
        update = params.get("update")
        if isinstance(update, dict) and update.get("sessionUpdate") in (
            "user_message",
            "user_message_chunk",
        ):
            return True
    return False


def _skip_if_turn_end_race_not_exercised(
    agent,
    turn,
    record_property,
    *,
    race_window: float,
    trigger_at_index: int | None,
    trigger_method: str,
    verb: str,
    property_prefix: str,
) -> None:
    """Shared race gate for the `session/cancel`- and `session/close`-triggered rows. See the
    module docstring. Only ever SKIPs or returns; never asserts."""
    if trigger_at_index is None:
        pytest.skip(f"{verb} not exercised: the turn ended before {trigger_method} could be sent")
    record_property(f"acp_tck_{property_prefix}_state_at_trigger", turn.state_at_cancel)
    if _response_error(turn) is not None and turn.response_index < trigger_at_index:
        pytest.skip(
            f"{verb} not exercised: session/prompt was rejected before {trigger_method} was sent"
        )
    if turn.idle_update is None:
        return  # error response with no foreground work: judged by the caller
    stop_reason = turn.stop_reason
    if stop_reason == "cancelled" or not _race_plausible(stop_reason):
        return
    trigger_timestamp = agent.transcript[trigger_at_index].timestamp
    elapsed_ms = (turn.idle_update.timestamp - trigger_timestamp) * 1000
    record_property(f"acp_tck_{property_prefix}_race_window_ms", f"{race_window * 1000:.0f}")
    if elapsed_ms < race_window * 1000:
        record_property(f"acp_tck_{property_prefix}_race_ms", f"{elapsed_ms:.0f}")
        pytest.skip(
            f"{verb} not exercised: idle arrived {elapsed_ms:.0f} ms after {trigger_method} "
            f"(within the race window) with stopReason {stop_reason!r} -- the agent may simply "
            "have finished before reading it"
        )


def _skip_if_cancel_not_exercised(agent, turn, record_property, *, race_window: float) -> None:
    _skip_if_turn_end_race_not_exercised(
        agent,
        turn,
        record_property,
        race_window=race_window,
        trigger_at_index=turn.cancelled_at_index,
        trigger_method="session/cancel",
        verb="cancellation",
        property_prefix="cancel",
    )


def _skip_if_no_cancelled_idle_owed(turn) -> None:
    """After the race gate: an error response with no turn-ending idle owes no cancelled idle
    itself. `-32800` with no active state is a pre-insertion cancel (:1094,1115-1117); any other
    error is `ACP-CANCEL-203`'s finding."""
    error = _response_error(turn)
    if error is None or turn.idle_update is not None:
        return
    if error.get("code") == REQUEST_CANCELLED:
        pytest.skip(
            "cancelled before insertion with no foreground work active -- no idle required"
        )
    pytest.skip("the turn ended via a JSON-RPC error, not an idle state_update -- see ACP-CANCEL-203")


async def _run_cancel_turn(agent_launch, tmp_path, cancel_prompt_text, **kwargs):
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": cancel_prompt_text}],
            on_cancel=True,
            timeout=agent_launch.default_timeout,
            **kwargs,
        )
        return agent, turn


@pytest.mark.requirement("ACP-CANCEL-201", "ACP-CANCEL-207")
@pytest.mark.capability("capabilities.session")
async def test_cancel_resolves_with_a_cancelled_idle(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CANCEL-201/207. When `session/cancel` lands on active foreground work, the idle that
    ends it carries exactly `stopReason: "cancelled"` -- not another defined value, not an
    unprefixed substitute."""
    agent, turn = await _run_cancel_turn(agent_launch, tmp_path, cancel_prompt_text)
    _skip_if_cancel_not_exercised(
        agent, turn, record_property, race_window=quiet_period(agent_launch.default_timeout)
    )
    _skip_if_no_cancelled_idle_owed(turn)
    assert turn.stop_reason == "cancelled", (
        f"expected stopReason 'cancelled' on the idle after session/cancel, got "
        f"{turn.stop_reason!r}"
    )


@pytest.mark.requirement("ACP-CANCEL-203")
@pytest.mark.capability("capabilities.session")
async def test_cancel_does_not_surface_as_a_generic_failure(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CANCEL-203. Cancellation is not surfaced as a generic failure. An error response is
    conforming only as `-32800` for a prompt cancelled before insertion (no user-message update
    emitted); any other code, or `-32800` after insertion, FAILs. A turn-ending idle must not
    carry another defined stop reason (e.g. `error`, `end_turn`) instead of `cancelled`."""
    agent, turn = await _run_cancel_turn(agent_launch, tmp_path, cancel_prompt_text)
    _skip_if_cancel_not_exercised(
        agent, turn, record_property, race_window=quiet_period(agent_launch.default_timeout)
    )
    error = _response_error(turn)
    if error is not None:
        assert error.get("code") == REQUEST_CANCELLED, (
            f"cancellation surfaced as a JSON-RPC error other than -32800 on session/prompt: "
            f"{error!r}"
        )
        assert not _user_message_echoed(turn), (
            "session/prompt was answered -32800 after its user message was inserted (a "
            "user-message update was emitted); once inserted it must succeed"
        )
    if turn.idle_update is not None:
        assert turn.stop_reason == "cancelled" or turn.stop_reason not in STOP_REASONS, (
            f"after session/cancel, the turn ended with stopReason {turn.stop_reason!r} instead "
            "of 'cancelled'"
        )


@pytest.mark.requirement("ACP-CANCEL-202")
@pytest.mark.capability("capabilities.session")
async def test_no_cancelled_work_output_after_the_cancelled_idle(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CANCEL-202. Updates for the cancelled work precede its cancelled idle: within
    `quiet_period` after it, no agent message/thought update for the session reuses a
    `messageId` seen during the cancelled turn. Repeated idle snapshots, `unknown`, and new work
    are allowed. SKIPs unless the turn resolved as `cancelled`.

    Only `AgentTimeout` ends the wait: an agent that exits right after the idle must not PASS
    by having its exit swallowed."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": cancel_prompt_text}],
            on_cancel=True,
            timeout=agent_launch.default_timeout,
        )
        _skip_if_cancel_not_exercised(
            agent, turn, record_property, race_window=quiet_period(agent_launch.default_timeout)
        )
        if turn.idle_update is None or turn.stop_reason != "cancelled":
            pytest.skip(
                "prerequisite not met: the turn did not resolve with stopReason 'cancelled' -- "
                "see ACP-CANCEL-201/207"
            )

        def _output_entity(msg):
            """`(entity type, messageId)` of an agent message/thought update for the session.
            Ids are unique per entity type, so a thought and a message may share one."""
            params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
            update = params.get("update")
            if (
                msg.get("method") == "session/update"
                and params.get("sessionId") == session_id
                and isinstance(update, dict)
                and update.get("sessionUpdate") in _AGENT_OUTPUT_KINDS
            ):
                return update["sessionUpdate"].removesuffix("_chunk"), update.get("messageId")
            return None

        turn_entities = set()
        for _, entry in turn.updates:
            if isinstance(entry.parsed, dict) and (entity := _output_entity(entry.parsed)):
                turn_entities.add(entity)

        def _reuses_turn_message(entry) -> bool:
            return any(_output_entity(msg) in turn_entities for msg in iter_messages(entry))

        with pytest.raises(AgentTimeout):
            late = await agent.wait_for_message(
                _reuses_turn_message, timeout=quiet_period(agent_launch.default_timeout)
            )
            pytest.fail(f"cancelled work's output arrived after its cancelled idle: {late.text!r}")


@pytest.mark.requirement("ACP-CANCEL-204")
@pytest.mark.capability("capabilities.session")
async def test_cancel_stops_work_promptly(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CANCEL-204 (INFORMATIONAL -- "as soon as possible" has no wire-observable signal).
    Runs the `ACP-CANCEL-201` scenario, records whether cancel was exercised, and always SKIPs."""
    _, turn = await _run_cancel_turn(agent_launch, tmp_path, cancel_prompt_text)
    record_property("acp_tck_cancel_sent", turn.cancelled_at_index is not None)
    record_property("acp_tck_stop_reason", turn.stop_reason)
    pytest.skip(
        "ACP-CANCEL-204 is unobservable from a client-only TCK: the promptness of 'as soon as "
        "possible' cancellation has no wire-level signal to check"
    )


@pytest.mark.requirement("ACP-CANCEL-205")
@pytest.mark.capability("capabilities.session")
async def test_cancel_notification_receives_no_direct_response(
    agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-CANCEL-205. `session/cancel` is a notification; no response-shaped message (no
    `method`) other than the prompt's own (possibly delayed) response may follow it, up to the
    turn-ending idle. Batch elements are checked individually."""
    agent, turn = await _run_cancel_turn(agent_launch, tmp_path, cancel_prompt_text)
    if turn.cancelled_at_index is None:
        pytest.skip("cancellation not exercised: the turn ended before session/cancel could be sent")

    prompt_response_id = None
    if isinstance(turn.response_entry.parsed, dict):
        prompt_response_id = turn.response_entry.parsed.get("id")
    end_index = len(agent.transcript) if turn.idle_index is None else turn.idle_index + 1
    for entry in agent.transcript[turn.cancelled_at_index + 1 : end_index]:
        if entry.direction is not Direction.RECEIVED:
            continue
        for msg in iter_messages(entry):
            if "method" in msg:
                continue  # an agent -> client request/notification, not a response
            if prompt_response_id is not None and msg.get("id") == prompt_response_id:
                continue
            pytest.fail(
                f"agent sent a response-shaped message attributable to the session/cancel "
                f"notification: {msg!r}"
            )


@pytest.mark.requirement("ACP-CANCEL-206")
@pytest.mark.capability("capabilities.session")
async def test_cancel_with_meta_is_accepted(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CANCEL-206. A `session/cancel` that also carries `_meta` is honoured exactly like a
    bare one."""
    agent, turn = await _run_cancel_turn(
        agent_launch, tmp_path, cancel_prompt_text, cancel_meta={"tck": True}
    )
    _skip_if_cancel_not_exercised(
        agent, turn, record_property, race_window=quiet_period(agent_launch.default_timeout)
    )
    _skip_if_no_cancelled_idle_owed(turn)
    assert turn.stop_reason == "cancelled", (
        f"expected stopReason 'cancelled' after a _meta-carrying session/cancel, got "
        f"{turn.stop_reason!r}"
    )


@pytest.mark.requirement("ACP-CANCEL-208", "ACP-CLOSE-202")
@pytest.mark.capability("capabilities.session")
async def test_close_cancels_foreground_work(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CANCEL-208 / ACP-CLOSE-202. `session/close` on a session with an in-flight turn
    cancels that work as `session/cancel` would: the idle ending it carries `cancelled`. If the
    close kept the prompt from being inserted, the prompt is answered `-32800`
    (session-setup.mdx:366) -- any other error FAILs. `ACP-CLOSE-202` reuses this exact
    evidence; `ACP-CLOSE-201` covers `session/close`'s own result on an idle session."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)

        async def _close():
            return await agent.send_request("session/close", {"sessionId": session_id})

        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": cancel_prompt_text}],
            on_action=_close,
            timeout=agent_launch.default_timeout,
        )
        _skip_if_turn_end_race_not_exercised(
            agent,
            turn,
            record_property,
            race_window=quiet_period(agent_launch.default_timeout),
            trigger_at_index=turn.action_sent_at_index,
            trigger_method="session/close",
            verb="cancellation-via-close",
            property_prefix="close_cancel",
        )
        error = _response_error(turn)
        if error is not None:
            assert error.get("code") == REQUEST_CANCELLED, (
                f"session/close answered the in-flight session/prompt with an error other than "
                f"-32800: {error!r}"
            )
        if turn.idle_update is not None:
            assert turn.stop_reason == "cancelled", (
                f"expected stopReason 'cancelled' after session/close on a session with "
                f"in-flight work, got {turn.stop_reason!r}"
            )


@pytest.mark.requirement("ACP-CANCEL-209")
@pytest.mark.capability("capabilities.session")
async def test_cancel_while_blocked_on_permission(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CANCEL-209. Cancelling while the turn is blocked on the agent's own permission
    request (`requires_action` reported, the request still unanswered) ends the work with an
    idle carrying `stopReason: "cancelled"`. The TCK sends `session/cancel`, then answers the
    held request `cancelled`. SKIPs if no permission request was pending when cancel was sent,
    or if the session was not reported blocked (the request may then belong to work that could
    finish on its own)."""
    agent, turn = await _run_cancel_turn(
        agent_launch,
        tmp_path,
        cancel_prompt_text,
        hold_permission=True,
        cancel_wait=agent_launch.default_timeout / 4,
    )
    record_property("acp_tck_state_at_cancel", turn.state_at_cancel)
    if turn.held_permission is None:
        pytest.skip("no session/request_permission was pending when session/cancel was sent")
    if turn.state_at_cancel != "requires_action":
        pytest.skip(
            f"the session was {turn.state_at_cancel!r}, not requires_action, when its permission "
            "request was held -- cancellation while blocked not exercised"
        )
    assert turn.idle_update is not None, (
        f"the turn ended with an error response instead of an idle: {turn.response_entry.text!r}"
    )
    assert turn.stop_reason == "cancelled", (
        f"expected stopReason 'cancelled' after cancelling a turn blocked on a permission "
        f"request, got {turn.stop_reason!r}"
    )


@pytest.mark.requirement("ACP-INFO-CANCEL-201")
@pytest.mark.capability("capabilities.session")
async def test_cancel_with_no_foreground_work_behaviour(agent_launch, tmp_path, record_property):
    """ACP-INFO-CANCEL-201 (INFORMATIONAL). `session/cancel` for a session with no prompt in
    flight: no completion update is required; records whether the agent replies, stays silent,
    or exits. Never asserts."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await agent.send_notification("session/cancel", {"sessionId": session_id})

        behaviour = await probe_behaviour(
            agent.wait_for_message(
                is_response_line, timeout=quiet_period(agent_launch.default_timeout)
            ),
            lambda entry: f"sent a response-shaped message: {entry.text!r}",
        )

    record_property("behaviour", behaviour)


@pytest.mark.requirement("ACP-INFO-CANCEL-202")
@pytest.mark.capability("capabilities.session")
async def test_cancel_during_pending_permission_request_behaviour(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-INFO-CANCEL-202 (INFORMATIONAL). Holds the agent's permission request while sending
    `session/cancel` (as `ACP-CANCEL-209` does) and records whether the agent also sent
    `$/cancel_request` for it -- MAY at best -- plus the stop reason. Never asserts."""
    _, turn = await _run_cancel_turn(
        agent_launch,
        tmp_path,
        cancel_prompt_text,
        hold_permission=True,
        cancel_wait=agent_launch.default_timeout / 4,
    )
    record_property("acp_tck_permission_held", turn.held_permission is not None)
    cancel_requests = [
        entry.text
        for entry in turn.client_requests_seen
        if isinstance(entry.parsed, dict) and entry.parsed.get("method") == "$/cancel_request"
    ]
    record_property("acp_tck_cancel_requests_seen", cancel_requests)
    record_property("acp_tck_stop_reason", turn.stop_reason)
