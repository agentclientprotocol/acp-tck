"""Prompt-turn conformance: ACP-PROMPT-201/203/205..208 and ACP-STATE-201..205.

All are `capabilities.session`-gated. `ACP-PROMPT-208` and `ACP-STATE-204` are ADVISORY on the
registry (`capability=None`); their tests still carry the marker for the SKIP gate.

The STATE rows judge `run_prompt`'s turn terminator (see its docstring): `terminated_by` says
whether the turn ended with an idle after an active state, with the confirmed no-active-state
fallback idle, or with an error response and no foreground work.
"""

from __future__ import annotations

import pytest

from tck.common.harness import Direction
from tck.v2.protocol import STOP_REASONS, is_valid_open_enum_value
from tck.v2.validation import validate_agent_message

from ._helpers import connected_agent, iter_messages, new_session, run_prompt

_PROMPT_TEXT = "hi"

_USER_MESSAGE_KINDS = frozenset({"user_message", "user_message_chunk"})
_AGENT_OUTPUT_KINDS = frozenset(
    {"agent_message", "agent_message_chunk", "agent_thought", "agent_thought_chunk"}
)


async def _drive_one_turn(agent_launch, tmp_path, blocks=None, **kwargs):
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        return await run_prompt(
            agent,
            session_id,
            blocks or [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
            **kwargs,
        )


def _session_updates(turn):
    """The inner `update` objects of `turn`'s `session/update`s for the prompted session."""
    result = []
    for _, entry in turn.updates:
        params = entry.parsed.get("params") if isinstance(entry.parsed, dict) else None
        if not isinstance(params, dict) or params.get("sessionId") != turn.session_id:
            continue
        update = params.get("update")
        if isinstance(update, dict):
            result.append(update)
    return result


def _record_turn(record_property, turn) -> None:
    record_property("acp_tck_terminated_by", turn.terminated_by)
    record_property("acp_tck_active_seen", turn.active_seen)
    record_property("acp_tck_stop_reason", turn.stop_reason)


@pytest.mark.requirement("ACP-PROMPT-201")
@pytest.mark.capability("capabilities.session")
async def test_prompt_response_is_an_acceptance_receipt_with_a_message_id(agent_launch, tmp_path):
    """ACP-PROMPT-201. The `session/prompt` response is a non-error result whose `messageId` is
    a non-empty string (non-empty is a TCK strengthening; `MessageId` is a plain string)."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    msg = turn.response_entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/prompt did not return a result object: {turn.response_entry.text!r}"
    )
    assert isinstance(turn.message_id, str) and turn.message_id, (
        f"session/prompt result.messageId must be a non-empty string, got "
        f"{msg['result'].get('messageId')!r}"
    )


@pytest.mark.requirement("ACP-PROMPT-203")
@pytest.mark.capability("capabilities.session")
async def test_agent_echoes_the_inserted_user_message(agent_launch, tmp_path):
    """ACP-PROMPT-203. A `user_message`/`user_message_chunk` update for the prompted session
    carries the response's `messageId`, no later than the turn-ending idle. SKIPs without a
    usable `messageId` (`ACP-PROMPT-201` FAILs that)."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    if not (isinstance(turn.message_id, str) and turn.message_id):
        pytest.skip("session/prompt response carried no usable messageId -- see ACP-PROMPT-201")
    echoed = any(
        update.get("sessionUpdate") in _USER_MESSAGE_KINDS
        and update.get("messageId") == turn.message_id
        for update in _session_updates(turn)
    )
    assert echoed, (
        f"no user_message/user_message_chunk update echoed messageId {turn.message_id!r} for "
        f"session {turn.session_id!r}"
    )


@pytest.mark.requirement("ACP-STATE-201")
@pytest.mark.capability("capabilities.session")
async def test_active_state_precedes_the_turn_ending_idle(agent_launch, tmp_path, record_property):
    """ACP-STATE-201. The idle that ends the turn follows a `running` or `requires_action` for
    the session. FAILs when the turn could only be ended by the fallback (a stopReason-bearing
    idle with no active state before it); SKIPs when the prompt was rejected with no foreground
    work (no state transition is owed)."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    _record_turn(record_property, turn)
    if turn.terminated_by == "error":
        pytest.skip("the prompt was rejected with no foreground work -- no turn-ending idle")
    assert turn.terminated_by == "idle", (
        "the turn ended with an idle carrying a stopReason, but no state_update "
        "{state: 'running'|'requires_action'} for this session preceded it"
    )


@pytest.mark.requirement("ACP-STATE-202")
@pytest.mark.capability("capabilities.session")
async def test_idle_ends_active_foreground_work(agent_launch, tmp_path, record_property):
    """ACP-STATE-202. Once the session reported an active state, an idle for it arrives within
    the turn's `--timeout` -- also when the prompt was rejected after work had started
    (`run_prompt` keeps waiting for the idle; never reaching it is an `AgentTimeout` FAIL).
    SKIPs when no active state was observed."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    _record_turn(record_property, turn)
    if not turn.active_seen:
        pytest.skip("no foreground work observed: no running/requires_action for this session")
    assert turn.idle_update is not None, (
        "an active state was observed, but no idle state_update ended the work"
    )


@pytest.mark.requirement("ACP-STATE-203")
@pytest.mark.capability("capabilities.session")
async def test_turn_ending_stop_reason_is_valid(agent_launch, tmp_path, record_property):
    """ACP-STATE-203. When the turn-ending idle carries a non-null `stopReason`, it is one of the
    defined constants or begins with `_`. A missing/`null` one SKIPs (SHOULD; `ACP-STATE-204`)."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    _record_turn(record_property, turn)
    if turn.idle_update is None:
        pytest.skip("the prompt was rejected with no foreground work -- no turn-ending idle")
    if turn.stop_reason is None:
        pytest.skip("no stopReason reported on the turn-ending idle (SHOULD) -- see ACP-STATE-204")
    assert is_valid_open_enum_value(turn.stop_reason, STOP_REASONS), (
        f"turn-ending idle's stopReason is not a defined constant or a `_`-prefixed extension: "
        f"{turn.stop_reason!r}"
    )


@pytest.mark.requirement("ACP-STATE-204")
@pytest.mark.capability("capabilities.session")
async def test_turn_ending_idle_carries_a_stop_reason(agent_launch, tmp_path, record_property):
    """ACP-STATE-204 (ADVISORY). The idle that ends the turn carries a non-null `stopReason`."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    _record_turn(record_property, turn)
    if turn.idle_update is None:
        pytest.skip("the prompt was rejected with no foreground work -- no turn-ending idle")
    assert turn.stop_reason is not None, (
        "the turn-ending idle state_update carries no stopReason"
    )


@pytest.mark.requirement("ACP-STATE-205")
@pytest.mark.capability("capabilities.session")
async def test_running_is_reported_before_progress_resumes(agent_launch, tmp_path):
    """ACP-STATE-205. After `requires_action` for the session, no agent message/thought update
    for the session arrives before the next `running` or `idle` for it: model output counts as
    progress resuming, which must be reported as `running` first. Tool-call updates are not
    judged (background activity may continue while blocked). SKIPs without `requires_action`."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    if not turn.requires_action_seen:
        pytest.skip("no requires_action observed for this session during the turn")
    blocked = False
    for update in _session_updates(turn):
        kind = update.get("sessionUpdate")
        if kind == "state_update":
            state = update.get("state")
            if state == "requires_action":
                blocked = True
            elif state in ("running", "idle"):
                blocked = False
        elif blocked and kind in _AGENT_OUTPUT_KINDS:
            pytest.fail(
                f"a {kind!r} update arrived after requires_action without a state_update "
                f"{{state: 'running'}} first: {update!r}"
            )


@pytest.mark.requirement("ACP-PROMPT-205")
@pytest.mark.capability("capabilities.session")
async def test_updates_validate_and_carry_a_known_session_id(agent_launch, tmp_path):
    """ACP-PROMPT-205. Every `session/update` during the turn validates against the v2 schema
    and carries the prompted `sessionId` or that of a child session already announced, in wire
    order, by a `subagent_update` on a known session (nested children included). Child traffic
    before its announcement FAILs. Vacuous pass when the turn emits no updates."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
        turn_lines = {line_index for line_index, _ in turn.updates}
        known = {session_id}
        for line_index, entry in enumerate(agent.transcript):
            if entry.direction is not Direction.RECEIVED:
                continue
            for msg in iter_messages(entry):
                if msg.get("method") != "session/update":
                    continue
                params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
                carried = params.get("sessionId")
                if line_index in turn_lines:
                    issues = validate_agent_message(msg)
                    assert not issues, f"session/update failed schema validation: {issues!r}"
                    assert carried in known, (
                        f"session/update carried sessionId {carried!r}, which is neither the "
                        f"prompted session {session_id!r} nor a child announced earlier via "
                        f"subagent_update (known: {sorted(known)!r})"
                    )
                update = params.get("update")
                if (
                    carried in known
                    and isinstance(update, dict)
                    and update.get("sessionUpdate") == "subagent_update"
                    and isinstance(update.get("sessionId"), str)
                ):
                    known.add(update["sessionId"])


@pytest.mark.requirement("ACP-PROMPT-206")
@pytest.mark.capability("capabilities.session")
async def test_resource_link_content_block_is_accepted(agent_launch, tmp_path):
    """ACP-PROMPT-206. A `text` + `resource_link` prompt is accepted and the turn ends -- both
    block types are baseline for an agent advertising `session`."""
    turn = await _drive_one_turn(
        agent_launch,
        tmp_path,
        [
            {"type": "text", "text": "have a look at this"},
            {"type": "resource_link", "uri": "file:///tmp/tck-example.txt", "name": "example.txt"},
        ],
    )
    msg = turn.response_entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"a prompt with a resource_link block must succeed: {turn.response_entry.text!r}"
    )


def _assert_no_user_message_on_error(turn) -> None:
    msg = turn.response_entry.parsed
    if not (isinstance(msg, dict) and "error" in msg):
        pytest.skip("the prompt was accepted -- ACP-PROMPT-203 judges its user-message echo")
    echoes = [u for u in _session_updates(turn) if u.get("sessionUpdate") in _USER_MESSAGE_KINDS]
    assert not echoes, (
        f"session/prompt was answered with an error ({msg['error']!r}), but a user-message "
        f"update was emitted for the submission: {echoes!r}"
    )


@pytest.mark.requirement("ACP-PROMPT-207")
@pytest.mark.capability("capabilities.session")
async def test_rejected_prompt_emits_no_user_message(agent_launch, tmp_path):
    """ACP-PROMPT-207. If `session/prompt` is answered with an error, no user-message update was
    emitted for it (an inserted message must get a successful response). SKIPs on success."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    _assert_no_user_message_on_error(turn)


@pytest.mark.requirement("ACP-PROMPT-207")
@pytest.mark.capability("capabilities.session")
async def test_cancelled_prompt_error_emits_no_user_message(agent_launch, tmp_path, cancel_prompt_text):
    """ACP-PROMPT-207, on a cancelled turn, where an error response is most likely: an error
    (e.g. `-32800` before insertion) implies no user-message update for the submission."""
    turn = await _drive_one_turn(
        agent_launch, tmp_path, [{"type": "text", "text": cancel_prompt_text}], on_cancel=True
    )
    _assert_no_user_message_on_error(turn)


@pytest.mark.requirement("ACP-PROMPT-208")
@pytest.mark.capability("capabilities.session")
async def test_prompt_response_precedes_the_turn_ending_idle(agent_launch, tmp_path):
    """ACP-PROMPT-208 (ADVISORY). The successful response arrives no later than the turn-ending
    idle: the agent responds once the message is inserted, not when work finishes. Wire order is
    only a proxy for insertion timing, hence ADVISORY. SKIPs on an error response."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    msg = turn.response_entry.parsed
    if not (isinstance(msg, dict) and isinstance(msg.get("result"), dict)):
        pytest.skip("session/prompt did not succeed -- see ACP-PROMPT-201")
    assert turn.idle_index is not None
    assert turn.response_index <= turn.idle_index, (
        "the session/prompt response arrived after the turn-ending idle -- a successful prompt "
        "response is an insertion receipt, not a completion signal"
    )
