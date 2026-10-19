"""Session management: `session/resume` (ACP-SESSION-203, ACP-RESUME-201..209),
`session/list` (ACP-LIST-201..204), `session/close`'s own contract (ACP-CLOSE-201/203/204 --
`ACP-CLOSE-202` is covered by `test_cancel.py`'s `test_close_cancels_foreground_work`, see
`tck.v2.requirements`'s module docstring), `session/delete` (ACP-DELETE-201..203), the
`additionalDirectories` carrier on `session/new`/`session/resume` (ACP-ADDDIRS-201/202), the
two INFORMATIONAL MCP-server-acceptance probes (ACP-MCP-201/202), and the unstable
`session/fork` (ACP-FORK-201/202) and `systemPrompt` (ACP-SYSPROMPT-201/202) surfaces.

Every id here except `ACP-CLOSE-204`/`ACP-DELETE-203`/`ACP-MCP-201`/`ACP-MCP-202` is
`Tier.CAPABILITY`; see the requirements module for the exact capability path each uses. Those
four still carry a `@pytest.mark.capability(...)` marker purely for the SKIP gate even though
`Requirement.capability` is `None` (ADVISORY/INFORMATIONAL tier) -- the same independence used
throughout this registry (e.g. `ACP-CANCEL-204`).

`systemPrompt` is only probed on its positive paths: probing its error paths would need the TCK
to send an unadvertised mode or a non-text content block, both of which clients MUST NOT do.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

from tck.common.harness import TranscriptEntry
from tck.v2.validation import validate_agent_message, validate_agent_response

from ..protocol import INVALID_PARAMS, REQUEST_CANCELLED
from ._helpers import (
    close_session,
    connected_agent,
    delete_session,
    drain_quiet,
    iter_messages,
    list_sessions,
    new_session,
    obtain_resumable_session,
    quiet_period,
    resume_session,
    run_prompt,
    skip_if_auth_gated,
    update_of,
)

_HISTORY_KINDS = {"user_message", "agent_message", "agent_thought"}
_CHUNK_KINDS = {"user_message_chunk", "agent_message_chunk", "agent_thought_chunk"}
_REPLAYED_HISTORY_KINDS = _HISTORY_KINDS | _CHUNK_KINDS


def _session_update_messages(
    updates: list[tuple[int, TranscriptEntry]],
) -> list[tuple[tuple[int, int], dict[str, Any]]]:
    """Flatten `resume_session`'s `updates` into `((line_index, position_in_line), message)` for
    every `session/update` message, batch-carried ones included, in wire order."""
    flattened = []
    for line_index, entry in updates:
        for position, msg in enumerate(iter_messages(entry)):
            if msg.get("method") == "session/update":
                flattened.append(((line_index, position), msg))
    return flattened


def _update_for(msg: dict[str, Any], session_id: str) -> dict[str, Any] | None:
    """`msg`'s `update` payload if it is addressed to `session_id`, else `None`."""
    params = msg.get("params")
    if not isinstance(params, dict) or params.get("sessionId") != session_id:
        return None
    update = params.get("update")
    return update if isinstance(update, dict) else None


def _assert_resume_succeeded(entry: TranscriptEntry, what: str) -> dict[str, Any]:
    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"{what} did not succeed: {entry.text!r}"
    )
    return msg


# --- session/new / session/resume (ACP-SESSION-203, ACP-RESUME-201..209) ---


@pytest.mark.requirement("ACP-SESSION-203")
@pytest.mark.capability("capabilities.session")
async def test_session_new_mcp_servers_omitted_or_empty_are_equivalent(agent_launch, tmp_path):
    """ACP-SESSION-203."""
    async with connected_agent(agent_launch) as agent:
        omitted_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        assert omitted_id
        req_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": []}
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/new with mcpServers: [] did not succeed: {entry.text!r}"
        )


@pytest.mark.requirement("ACP-RESUME-201")
@pytest.mark.capability("capabilities.session")
async def test_resume_a_resumable_session_succeeds(agent_launch, tmp_path):
    """ACP-RESUME-201."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (_agent, _session_id, entry, _resume_cwd):
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/resume of a resumable session did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/resume", msg)
        assert not issues, f"session/resume result failed schema validation: {issues!r}"


async def _add_history(agent, session_id, *, timeout, text: str | None = None):
    """Run one ordinary prompt turn on an *already-obtained* session (see
    `obtain_resumable_session`), so there is something to (optionally) replay on the resume call
    that follows. A direct `session/resume` of a just-created session is not guaranteed to
    succeed, so the resume tests add history to the already-obtained session and then issue a
    second, fresh `session/resume`.

    The prompt text carries a per-call nonce unless `text` is given: an agent that persists
    sessions may replay an earlier run's identical prompt under its own, different `messageId`."""
    if text is None:
        text = f"remember this {uuid.uuid4().hex}"
    return await run_prompt(agent, session_id, [{"type": "text", "text": text}], timeout=timeout)


@pytest.mark.requirement("ACP-RESUME-202")
@pytest.mark.capability("capabilities.session")
async def test_resume_with_replay_from_start_replays_before_responding(
    agent_launch, tmp_path, record_property
):
    """ACP-RESUME-202. Zero replayed updates is itself conforming (R5's retention escape
    hatch) -- recorded, never FAILed. Only replayed-history kinds count as trailing violations:
    a repeated state snapshot, command/info/config/usage updates and live `notice`s may all
    legitimately follow the response. Filtered to this session's own `sessionId`, so an update
    for another session obtained earlier by `obtain_resumable_session`'s probing is ignored."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        await _add_history(agent, session_id, timeout=agent_launch.default_timeout)
        response_entry, updates = await resume_session(
            agent,
            session_id,
            resume_cwd,
            replay_from={"type": "start"},
            timeout=agent_launch.default_timeout,
        )
        _assert_resume_succeeded(response_entry, "session/resume with replayFrom: start")
        record_property("acp_tck_resume_replayed_update_count", len(updates))
        trailing = await drain_quiet(agent, quiet_period(agent_launch.default_timeout))
        trailing_history = [
            msg
            for entry in trailing
            for msg in iter_messages(entry)
            if msg.get("method") == "session/update"
            and (update := _update_for(msg, session_id)) is not None
            and update.get("sessionUpdate") in _REPLAYED_HISTORY_KINDS
        ]
        assert not trailing_history, (
            "a replayed-history session/update for this session arrived after session/resume's "
            f"response instead of before it: {trailing_history!r}"
        )


@pytest.mark.requirement("ACP-RESUME-203")
@pytest.mark.capability("capabilities.session")
async def test_resume_without_replay_from_replays_no_history(agent_launch, tmp_path, record_property):
    """ACP-RESUME-203. Vacuous -- and recorded, never FAILed on that account -- for an agent
    that retains no history to replay. The mandatory current-state snapshot is not history."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        await _add_history(agent, session_id, timeout=agent_launch.default_timeout)
        response_entry, updates = await resume_session(
            agent, session_id, resume_cwd, timeout=agent_launch.default_timeout
        )
        _assert_resume_succeeded(response_entry, "session/resume with replayFrom omitted")
        history_updates = [
            update
            for _, entry in updates
            if (update := update_of(entry)) is not None
            and update.get("sessionUpdate") in _REPLAYED_HISTORY_KINDS
        ]
        record_property("acp_tck_resume_no_replay_history_update_count", len(history_updates))
        assert not history_updates, (
            "session/resume with replayFrom omitted MUST NOT replay conversation history "
            f"before responding, but observed: {history_updates!r}"
        )


@pytest.mark.requirement("ACP-RESUME-204")
@pytest.mark.capability("capabilities.session")
async def test_resume_replays_retained_user_message_with_same_message_id(agent_launch, tmp_path):
    """ACP-RESUME-204. Absence of the message from replay is itself conforming (R5) -- SKIPs
    this check rather than FAILing it. A replayed message only violates the requirement if its
    *content* matches this test's own nonce-carrying prompt but its `messageId` differs."""
    prompt_text = f"remember this {uuid.uuid4().hex}"
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        turn = await _add_history(
            agent, session_id, timeout=agent_launch.default_timeout, text=prompt_text
        )
        if turn.message_id is None:
            pytest.skip(
                "session/prompt response carried no usable messageId -- see ACP-PROMPT-201"
            )
        _response_entry, updates = await resume_session(
            agent,
            session_id,
            resume_cwd,
            replay_from={"type": "start"},
            timeout=agent_launch.default_timeout,
        )
        matching_updates = [
            update
            for _, entry in updates
            if (update := update_of(entry)) is not None
            and update.get("sessionUpdate") in ("user_message", "user_message_chunk")
        ]
        if not matching_updates:
            pytest.skip(
                "the retained user message was not replayed at all -- conforming per R5, "
                "nothing to check"
            )

        def _content_matches(update: dict[str, Any]) -> bool:
            content = update.get("content")
            if isinstance(content, list):
                return any(
                    isinstance(block, dict) and block.get("text") == prompt_text
                    for block in content
                )
            return isinstance(content, dict) and content.get("text") == prompt_text

        violations = [
            update
            for update in matching_updates
            if _content_matches(update) and update.get("messageId") != turn.message_id
        ]
        assert not violations, (
            f"replayed message(s) with content matching the original prompt carry a different "
            f"messageId than the original response's {turn.message_id!r}: {violations!r}"
        )


@pytest.mark.requirement("ACP-RESUME-205")
@pytest.mark.capability("capabilities.session")
async def test_resume_chunk_replay_preceded_by_whole_message_update(
    agent_launch, tmp_path, record_property
):
    """ACP-RESUME-205. Accepts any preceding same-kind, same-`messageId` whole-message update
    with a `content` array: `[]` (rebuild from the beginning) and full content (chunks append)
    are wire-indistinguishable. Vacuous -- recorded, never FAILed -- for an agent whose replay
    uses only whole-message updates (`_base.ConformingAgent`'s own case)."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        await _add_history(agent, session_id, timeout=agent_launch.default_timeout)
        _response_entry, updates = await resume_session(
            agent,
            session_id,
            resume_cwd,
            replay_from={"type": "start"},
            timeout=agent_launch.default_timeout,
        )
        replayed = [update for _, entry in updates if (update := update_of(entry)) is not None]
        chunk_count = 0
        for index, update in enumerate(replayed):
            kind = update.get("sessionUpdate")
            if kind not in _CHUNK_KINDS:
                continue
            chunk_count += 1
            message_id = update.get("messageId")
            whole_kind = kind[: -len("_chunk")]
            preceded = any(
                prior.get("sessionUpdate") == whole_kind
                and prior.get("messageId") == message_id
                and isinstance(prior.get("content"), list)
                for prior in replayed[:index]
            )
            assert preceded, (
                f"replayed {kind} for messageId {message_id!r} was not preceded by a matching "
                f"whole-message update (sessionUpdate={whole_kind!r} with a content array): "
                f"{replayed!r}"
            )
        record_property("acp_tck_resume_replayed_chunk_count", chunk_count)


@pytest.mark.requirement("ACP-RESUME-206")
@pytest.mark.capability("capabilities.session")
async def test_resume_sends_state_snapshot_before_responding(agent_launch, tmp_path):
    """ACP-RESUME-206. Checked once with `replayFrom` omitted and once with `start`, both after
    a history-producing turn. An idle snapshot may carry the last `stopReason`; that is context,
    not a new turn end, and is not judged here."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        await _add_history(agent, session_id, timeout=agent_launch.default_timeout)
        for replay_from in (None, {"type": "start"}):
            label = f"session/resume with replayFrom={replay_from!r}"
            response_entry, updates = await resume_session(
                agent,
                session_id,
                resume_cwd,
                replay_from=replay_from,
                timeout=agent_launch.default_timeout,
            )
            _assert_resume_succeeded(response_entry, label)
            ordered = [
                (order, update)
                for order, msg in _session_update_messages(updates)
                if (update := _update_for(msg, session_id)) is not None
            ]
            last_history = max(
                (
                    order
                    for order, update in ordered
                    if update.get("sessionUpdate") in _REPLAYED_HISTORY_KINDS
                ),
                default=None,
            )
            snapshots = [
                order for order, update in ordered if update.get("sessionUpdate") == "state_update"
            ]
            assert snapshots, (
                f"{label} responded without first sending a current-state state_update for "
                f"the session: {[update for _, update in ordered]!r}"
            )
            assert last_history is None or max(snapshots) > last_history, (
                f"{label}: the current-state state_update must follow every replayed history "
                f"update, but the last one preceded replay: {[update for _, update in ordered]!r}"
            )


@pytest.mark.requirement("ACP-RESUME-207")
@pytest.mark.capability("capabilities.session")
async def test_resume_with_unsupported_cursor_is_rejected(agent_launch, tmp_path):
    """ACP-RESUME-207. `_tck_unsupported_cursor` is schema-valid (the `other` branch of
    `ReplayFrom`) but no agent supports it."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        response_entry, _updates = await resume_session(
            agent,
            session_id,
            resume_cwd,
            replay_from={"type": "_tck_unsupported_cursor"},
            timeout=agent_launch.default_timeout,
        )
        msg = response_entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        assert isinstance(error, dict) and error.get("code") == INVALID_PARAMS, (
            "session/resume with an unsupported replayFrom cursor type must be rejected with "
            f"-32602, got: {response_entry.text!r}"
        )


@pytest.mark.requirement("ACP-RESUME-208")
@pytest.mark.capability("capabilities.session")
async def test_resume_with_malformed_replay_from_is_rejected(agent_launch, tmp_path):
    """ACP-RESUME-208. Each malformed value is sent on its own `session/resume`; every one must
    be rejected with `-32602`."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        wrong = []
        for malformed in ("start", {}, {"type": 5}):
            response_entry, _updates = await resume_session(
                agent,
                session_id,
                resume_cwd,
                replay_from=malformed,
                timeout=agent_launch.default_timeout,
            )
            msg = response_entry.parsed
            error = msg.get("error") if isinstance(msg, dict) else None
            if not (isinstance(error, dict) and error.get("code") == INVALID_PARAMS):
                wrong.append((malformed, response_entry.text))
        assert not wrong, (
            "session/resume with a malformed replayFrom must be rejected with -32602, got: "
            f"{wrong!r}"
        )


@pytest.mark.requirement("ACP-RESUME-209")
@pytest.mark.capability("capabilities.session")
async def test_resume_replay_updates_are_schema_valid(agent_launch, tmp_path, record_property):
    """ACP-RESUME-209. Covers every `session/update` read while waiting for the
    `session/resume` response -- replay and snapshot alike."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        await _add_history(agent, session_id, timeout=agent_launch.default_timeout)
        response_entry, updates = await resume_session(
            agent,
            session_id,
            resume_cwd,
            replay_from={"type": "start"},
            timeout=agent_launch.default_timeout,
        )
        _assert_resume_succeeded(response_entry, "session/resume with replayFrom: start")
        messages = [msg for _, msg in _session_update_messages(updates)]
        record_property("acp_tck_resume_update_count", len(messages))
        problems = []
        for msg in messages:
            issues = validate_agent_message(msg)
            if issues:
                problems.append((msg, issues))
            params = msg.get("params")
            if not isinstance(params, dict) or params.get("sessionId") != session_id:
                problems.append((msg, f"sessionId is not the resumed {session_id!r}"))
        assert not problems, (
            f"session/update(s) sent during session/resume are invalid: {problems!r}"
        )


# --- session/list (ACP-LIST-201..204) ---


@pytest.mark.requirement("ACP-LIST-201")
@pytest.mark.capability("capabilities.session")
async def test_list_sessions_succeeds_and_validates(agent_launch, tmp_path):
    """ACP-LIST-201."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await list_sessions(agent, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/list did not succeed: {entry.text!r}"
        )
        sessions = msg["result"].get("sessions")
        assert isinstance(sessions, list), f"result.sessions must be an array, got {sessions!r}"
        issues = validate_agent_response("session/list", msg)
        assert not issues, f"session/list result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-LIST-202")
@pytest.mark.capability("capabilities.session")
async def test_list_sessions_filtered_to_no_match_returns_empty_array(agent_launch, tmp_path):
    """ACP-LIST-202."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        unused_cwd = tmp_path / "no-session-here"
        entry = await list_sessions(agent, cwd=unused_cwd, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/list with a non-matching cwd filter must not error: {entry.text!r}"
        )
        sessions = msg["result"].get("sessions")
        assert sessions == [], f"result.sessions must be [], got {sessions!r}"


@pytest.mark.requirement("ACP-LIST-203")
@pytest.mark.capability("capabilities.session")
async def test_list_sessions_filtered_by_cwd_matches_requested_cwd(agent_launch, tmp_path, record_property):
    """ACP-LIST-203. A per-entry check only -- the reverse direction (a session at that `cwd`
    is guaranteed to be returned) is not asserted. Records the entry count so an empty-array
    PASS is visibly vacuous in the report."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await list_sessions(agent, cwd=tmp_path, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/list filtered by cwd did not succeed: {entry.text!r}"
        )
        sessions = msg["result"].get("sessions") or []
        record_property("acp_tck_list_filtered_by_cwd_entry_count", len(sessions))
        for session in sessions:
            assert isinstance(session, dict) and session.get("cwd") == str(tmp_path), (
                f"session/list filtered by cwd={tmp_path!r} returned a session with a "
                f"different cwd: {session!r}"
            )


@pytest.mark.requirement("ACP-LIST-204")
@pytest.mark.capability("capabilities.session")
async def test_list_sessions_cwds_are_absolute(agent_launch, tmp_path, record_property):
    """ACP-LIST-204. Records the entry count so an empty-array PASS is visibly vacuous in the
    report."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await list_sessions(agent, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/list did not succeed: {entry.text!r}"
        )
        sessions = msg["result"].get("sessions") or []
        record_property("acp_tck_list_cwds_absolute_entry_count", len(sessions))
        for session in sessions:
            cwd = session.get("cwd") if isinstance(session, dict) else None
            assert isinstance(cwd, str) and os.path.isabs(cwd), (
                f"SessionInfo.cwd must be an absolute path, got {cwd!r}"
            )


# --- session/close (ACP-CLOSE-201/203/204 -- ACP-CLOSE-202 lives in test_cancel.py) ---


@pytest.mark.requirement("ACP-CLOSE-201")
@pytest.mark.capability("capabilities.session")
async def test_close_idle_session_succeeds(agent_launch, tmp_path):
    """ACP-CLOSE-201. `session/close` of a live, idle session (no foreground work in flight) --
    distinct from `ACP-CLOSE-202`'s cancellation side effect."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await close_session(agent, session_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/close of an idle session did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/close", msg)
        assert not issues, f"session/close result failed schema validation: {issues!r}"


def _transcript_index(agent, entry: TranscriptEntry) -> int:
    """Transcript index of the line carrying `entry` -- which may be a per-message copy of a
    batch line (`run_prompt` dispatches batch elements that way), so match by identity of the
    shared raw bytes rather than by object identity alone."""
    for index, candidate in enumerate(agent.transcript):
        if candidate is entry or (
            candidate.raw is entry.raw and candidate.timestamp == entry.timestamp
        ):
            return index
    raise AssertionError(f"entry not found in the transcript: {entry.text!r}")


@pytest.mark.requirement("ACP-CLOSE-203")
@pytest.mark.capability("capabilities.session")
async def test_close_sends_cancelled_idle_before_responding(
    agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-CLOSE-203. Drives the same `session/close`-mid-turn scenario as `ACP-CLOSE-202`;
    SKIPs unless the turn actually ended `cancelled`, so a lost race or a missing cancellation
    (`ACP-CLOSE-202`'s own finding) is never judged as an ordering defect."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        close_id = None

        async def _close():
            nonlocal close_id
            close_id = await agent.send_request("session/close", {"sessionId": session_id})
            return close_id

        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": cancel_prompt_text}],
            on_action=_close,
            timeout=agent_launch.default_timeout,
        )
        if turn.action_sent_at_index is None:
            pytest.skip(
                "cancellation-via-close not exercised: the turn ended before session/close "
                "could be sent"
            )
        if turn.idle_update is None or turn.stop_reason != "cancelled":
            pytest.skip(
                "prerequisite not met: the turn did not end with stopReason 'cancelled' -- see "
                "ACP-CLOSE-202"
            )
        close_entry = turn.action_response
        if close_entry is None:
            close_entry = await agent.wait_for_response(
                close_id, timeout=agent_launch.default_timeout
            )
        close_msg = close_entry.parsed
        if not (isinstance(close_msg, dict) and isinstance(close_msg.get("result"), dict)):
            pytest.skip(
                f"session/close did not succeed, so the ordering rule does not apply: "
                f"{close_entry.text!r}"
            )
        idle_index = _transcript_index(agent, turn.idle_update)
        close_index = _transcript_index(agent, close_entry)
        assert close_index >= idle_index, (
            "session/close responded successfully before sending the cancelled idle "
            f"state_update for the work it cancelled: close response {close_entry.text!r} came "
            f"before idle {turn.idle_update.text!r}"
        )


@pytest.mark.requirement("ACP-CLOSE-204")
@pytest.mark.capability("capabilities.session")
async def test_prompt_pending_at_close_is_answered(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CLOSE-204 (ADVISORY). Sends `session/prompt` and `session/close` back to back
    without awaiting the prompt's receipt. Either legal answer passes: `-32800` (closing
    prevented insertion) or a success with a `messageId` (already inserted). The order of the
    two responses is not judged -- prompt responses need not precede the close response."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        prompt_id = await agent.send_request(
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": cancel_prompt_text}]},
        )
        await agent.send_request("session/close", {"sessionId": session_id})
        entry = await agent.wait_for_response(prompt_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        result = msg.get("result") if isinstance(msg, dict) else None
        error = msg.get("error") if isinstance(msg, dict) else None
        inserted = isinstance(result, dict) and isinstance(result.get("messageId"), str)
        cancelled = isinstance(error, dict) and error.get("code") == REQUEST_CANCELLED
        record_property(
            "acp_tck_close_pending_prompt_outcome",
            "inserted" if inserted else "cancelled" if cancelled else "other",
        )
        assert inserted or cancelled, (
            "a session/prompt pending when session/close arrived must be answered with -32800 "
            f"or a success carrying its messageId, got: {entry.text!r}"
        )


# --- session/delete (ACP-DELETE-201..203) ---


def _listed_ids(entry: TranscriptEntry) -> set[Any]:
    msg = entry.parsed
    sessions = (
        (msg.get("result") or {}).get("sessions") or [] if isinstance(msg, dict) else []
    )
    return {s.get("sessionId") for s in sessions if isinstance(s, dict)}


@pytest.mark.requirement("ACP-DELETE-201")
@pytest.mark.capability("capabilities.session.delete")
async def test_delete_existing_session_succeeds(agent_launch, tmp_path):
    """ACP-DELETE-201. Closes the session first: deleting an active session is
    implementation-defined."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await close_session(agent, session_id, timeout=agent_launch.default_timeout)
        entry = await delete_session(agent, session_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/delete of an existing session did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/delete", msg)
        assert not issues, f"session/delete result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-DELETE-202")
@pytest.mark.capability("capabilities.session.delete")
async def test_deleted_session_no_longer_listed(agent_launch, tmp_path):
    """ACP-DELETE-202. Closes the session first (see `ACP-DELETE-201`), then SKIPs when
    `session/list` does not report the closed session at all -- nothing to compare against."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await close_session(agent, session_id, timeout=agent_launch.default_timeout)
        before_entry = await list_sessions(agent, timeout=agent_launch.default_timeout)
        if session_id not in _listed_ids(before_entry):
            pytest.skip("session/list does not report the closed session in the first place")

        delete_entry = await delete_session(agent, session_id, timeout=agent_launch.default_timeout)
        delete_msg = delete_entry.parsed
        assert isinstance(delete_msg, dict) and isinstance(delete_msg.get("result"), dict), (
            f"session/delete did not succeed: {delete_entry.text!r}"
        )

        after_entry = await list_sessions(agent, timeout=agent_launch.default_timeout)
        after_ids = _listed_ids(after_entry)
        assert session_id not in after_ids, (
            f"deleted session {session_id!r} still appears in session/list: {after_ids!r}"
        )


@pytest.mark.requirement("ACP-DELETE-203")
@pytest.mark.capability("capabilities.session.delete")
async def test_delete_unknown_session_succeeds_silently(agent_launch, tmp_path):
    """ACP-DELETE-203 (ADVISORY). Deleting an already-deleted or never-created sessionId SHOULD
    succeed silently, not error."""
    async with connected_agent(agent_launch) as agent:
        entry = await delete_session(agent, "tck-never-created", timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/delete of an unknown sessionId should succeed silently: {entry.text!r}"
        )


# --- additionalDirectories (ACP-ADDDIRS-201/202) ---


@pytest.mark.requirement("ACP-ADDDIRS-201")
@pytest.mark.capability("capabilities.session.additionalDirectories")
async def test_new_session_with_additional_directory_accepted(agent_launch, tmp_path):
    """ACP-ADDDIRS-201."""
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "additionalDirectories": [str(extra_dir)]}
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/new with an absolute additionalDirectories entry did not succeed: "
            f"{entry.text!r}"
        )


@pytest.mark.requirement("ACP-ADDDIRS-202")
@pytest.mark.capability("capabilities.session.additionalDirectories")
async def test_resume_session_with_additional_directory_accepted(agent_launch, tmp_path):
    """ACP-ADDDIRS-202."""
    extra_dir = tmp_path / "extra"
    extra_dir.mkdir()
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        response_entry, _updates = await resume_session(
            agent,
            session_id,
            resume_cwd,
            additional_directories=[str(extra_dir)],
            timeout=agent_launch.default_timeout,
        )
        msg = response_entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/resume with an absolute additionalDirectories entry did not succeed: "
            f"{response_entry.text!r}"
        )


# --- MCP servers (ACP-MCP-201/202, INFORMATIONAL) ---


@pytest.mark.requirement("ACP-MCP-201")
@pytest.mark.capability("capabilities.session.mcp.stdio")
async def test_new_session_with_stdio_mcp_server_recorded(agent_launch, tmp_path, record_property):
    """ACP-MCP-201 (INFORMATIONAL). Never asserts on the outcome -- see the requirements module
    docstring's judgment-call note.

    Includes the `type: "stdio"` discriminator `$defs/McpServer`'s `anyOf` requires: without it,
    a conforming agent answers `-32602` for a request the TCK itself malformed, recording a
    misleading `accepted=False` that looks like a finding about the agent under test."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new",
            {
                "cwd": str(tmp_path),
                "mcpServers": [
                    {
                        "type": "stdio",
                        "name": "tck-stdio",
                        "command": "/bin/nonexistent-tck-mcp-server",
                        "args": [],
                    }
                ],
            },
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        accepted = isinstance(msg, dict) and isinstance(msg.get("result"), dict)
        record_property("acp_tck_mcp_stdio_session_new_accepted", accepted)


@pytest.mark.requirement("ACP-MCP-202")
@pytest.mark.capability("capabilities.session.mcp.http")
async def test_new_session_with_http_mcp_server_recorded(agent_launch, tmp_path, record_property):
    """ACP-MCP-202 (INFORMATIONAL). Never asserts on the outcome.

    Includes the `type: "http"` discriminator `$defs/McpServer`'s `anyOf` requires -- see
    `test_new_session_with_stdio_mcp_server_recorded`'s docstring for why this matters."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new",
            {
                "cwd": str(tmp_path),
                "mcpServers": [
                    {
                        "type": "http",
                        "name": "tck-http",
                        "url": "http://127.0.0.1:1/tck-nonexistent",
                    }
                ],
            },
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        accepted = isinstance(msg, dict) and isinstance(msg.get("result"), dict)
        record_property("acp_tck_mcp_http_session_new_accepted", accepted)


# --- session/fork (ACP-FORK-201/202, unstable) ---


async def _fork_session(agent, session_id: str, cwd: Any, *, timeout: float) -> TranscriptEntry:
    req_id = await agent.send_request("session/fork", {"sessionId": session_id, "cwd": str(cwd)})
    return await agent.wait_for_response(req_id, timeout=timeout)


@pytest.mark.requirement("ACP-FORK-201")
@pytest.mark.capability("capabilities.session.fork")
async def test_fork_session_returns_a_new_session(agent_launch, tmp_path):
    """ACP-FORK-201."""
    async with connected_agent(agent_launch) as agent:
        source_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await _fork_session(agent, source_id, tmp_path, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/fork of an existing session did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/fork", msg)
        assert not issues, f"session/fork result failed schema validation: {issues!r}"
        forked_id = msg["result"].get("sessionId")
        assert isinstance(forked_id, str) and forked_id and forked_id != source_id, (
            f"session/fork must return a new sessionId distinct from the source {source_id!r}, "
            f"got {forked_id!r}"
        )


@pytest.mark.requirement("ACP-FORK-202")
@pytest.mark.capability("capabilities.session.fork")
async def test_forked_session_can_be_prompted_without_resume(agent_launch, tmp_path):
    """ACP-FORK-202. SKIPs when the fork itself did not produce a usable new id -- that is
    `ACP-FORK-201`'s finding."""
    async with connected_agent(agent_launch) as agent:
        source_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await _fork_session(agent, source_id, tmp_path, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        result = msg.get("result") if isinstance(msg, dict) else None
        forked_id = result.get("sessionId") if isinstance(result, dict) else None
        if not isinstance(forked_id, str) or not forked_id or forked_id == source_id:
            pytest.skip("prerequisite not met: session/fork gave no new sessionId -- see ACP-FORK-201")
        turn = await run_prompt(
            agent,
            forked_id,
            [{"type": "text", "text": "hello from the fork"}],
            timeout=agent_launch.default_timeout,
        )
        prompt_msg = turn.response_entry.parsed
        assert isinstance(prompt_msg, dict) and "error" not in prompt_msg, (
            f"session/prompt on the forked session was rejected: {turn.response_entry.text!r}"
        )
        assert turn.message_id is not None, (
            f"session/prompt on the forked session returned no messageId: "
            f"{turn.response_entry.text!r}"
        )
        assert turn.idle_update is not None, "the forked session's turn never reached idle"


# --- systemPrompt (ACP-SYSPROMPT-201/202, unstable) ---


async def _new_session_with_system_prompt(agent, cwd: Any, mode: str, *, timeout: float):
    system_prompt = {
        "mode": mode,
        "content": [{"type": "text", "text": "You are being exercised by the ACP TCK."}],
    }
    req_id = await agent.send_request(
        "session/new", {"cwd": str(cwd), "systemPrompt": system_prompt}
    )
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    skip_if_auth_gated(entry)
    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/new with a {mode!r} systemPrompt did not succeed: {entry.text!r}"
    )
    session_id = msg["result"].get("sessionId")
    assert isinstance(session_id, str) and session_id, (
        f"session/new with a {mode!r} systemPrompt returned no sessionId: {entry.text!r}"
    )


@pytest.mark.requirement("ACP-SYSPROMPT-201")
@pytest.mark.capability("capabilities.session.systemPrompt")
async def test_new_session_with_append_system_prompt_accepted(agent_launch, tmp_path):
    """ACP-SYSPROMPT-201. `append` needs no marker beyond `session.systemPrompt` itself."""
    async with connected_agent(agent_launch) as agent:
        await _new_session_with_system_prompt(
            agent, tmp_path, "append", timeout=agent_launch.default_timeout
        )


@pytest.mark.requirement("ACP-SYSPROMPT-202")
@pytest.mark.capability("capabilities.session.systemPrompt.mode.override")
async def test_new_session_with_override_system_prompt_accepted(agent_launch, tmp_path):
    """ACP-SYSPROMPT-202."""
    async with connected_agent(agent_launch) as agent:
        await _new_session_with_system_prompt(
            agent, tmp_path, "override", timeout=agent_launch.default_timeout
        )
