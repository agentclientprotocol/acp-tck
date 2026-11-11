"""Session management: `session/resume` (ACP-SESSION-203, ACP-RESUME-201..214, ACP-RESUME-216),
`session/list` (ACP-LIST-201..206), `session/close`'s own contract (ACP-CLOSE-201/203/204/206/207
-- `ACP-CLOSE-202` is covered by `test_cancel.py`'s `test_close_cancels_foreground_work`, see
`tck.v2.requirements`'s module docstring), `session/delete` (ACP-DELETE-201..205), `session/archive`/`session/unarchive` (ACP-ARCHIVE-002..006,
201), the
`additionalDirectories` carrier on `session/new`/`session/resume` (ACP-ADDDIRS-201..203), the
MCP-server rows (ACP-MCP-201..205), and the `session/fork` (ACP-FORK-201..205) and `systemPrompt`
(ACP-SYSPROMPT-201/202, and the error paths ACP-SYSPROMPT-002/003) surfaces.

Every id here except `ACP-RESUME-214`/`216`, `ACP-CLOSE-204`/`207`, `ACP-DELETE-203`,
`ACP-LIST-207`, `ACP-MCP-201`/`202`/`204`/`205` is
`Tier.CAPABILITY`; see the requirements module for the exact capability path each uses. Those
still carry a `@pytest.mark.capability(...)` marker purely for the SKIP gate even though
`Requirement.capability` is `None` (ADVISORY/INFORMATIONAL tier) -- the same independence used
throughout this registry (e.g. `ACP-CANCEL-204`).

`ACP-SYSPROMPT-002`/`003`, `ACP-ADDDIRS-203`, `ACP-LIST-205`/`206`/`207`, `ACP-ARCHIVE-004`/`005` and
`ACP-MCP-203`/`204` send input a client MUST NOT (an unsupported `systemPrompt` mode or non-text
block, a relative entry or `cwd` filter, a never-issued cursor, an unsupported `archived` filter
value, a never-created session, an unsupported transport, duplicate names) on purpose: the
spec defines the agent's answer to exactly those inputs, and the probes are `_`-prefixed or
otherwise unmistakably the TCK's.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction, TranscriptEntry
from tck.common.plugin import capability_is_supported
from tck.v2.validation import validate_agent_message, validate_agent_response

from ..protocol import AUTHENTICATION_REQUIRED, INVALID_PARAMS, REQUEST_CANCELLED, RESOURCE_NOT_FOUND
from ._helpers import (
    ACTIVE_STATES,
    BACKGROUND_ID_FIELDS,
    assert_unknown_session_error,
    close_session,
    connected_agent,
    delete_session,
    drain_quiet,
    iter_messages,
    list_sessions,
    background_keys,
    new_session,
    new_session_result,
    obtain_resumable_session,
    quiet_period,
    response_error,
    resume_session,
    run_prompt,
    same_dir,
    skip_if_auth_gated,
    skip_if_turn_end_race_not_exercised,
    update_of,
)

_HISTORY_KINDS = {"user_message", "agent_message", "agent_thought"}
_CHUNK_KINDS = {"user_message_chunk", "agent_message_chunk", "agent_thought_chunk"}
_REPLAYED_HISTORY_KINDS = _HISTORY_KINDS | _CHUNK_KINDS


def _session_update_messages(
    updates: list[tuple[int, TranscriptEntry]],
) -> list[tuple[tuple[int, int], dict[str, Any]]]:
    """Flatten `resume_session`'s `updates` into `((line_index, position_in_line), message)` for
    every `session/update` message, array-carried ones included, in wire order."""
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


# --- session/new / session/resume (ACP-SESSION-203, ACP-RESUME-201..216) ---


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


@pytest.mark.requirement("ACP-RESUME-211")
@pytest.mark.capability("capabilities.session")
async def test_resume_unknown_session_gets_resource_not_found(agent_launch, tmp_path):
    """ACP-RESUME-211. `session/resume` of a session the agent never created must not create
    it. The id carries a nonce, so an agent that persists sessions cannot know it. A session is
    created first so an auth-gated agent SKIPs instead of answering `-32000`."""
    unknown_id = f"tck-nonexistent-{uuid.uuid4().hex}"
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry, _updates = await resume_session(
            agent, unknown_id, tmp_path, timeout=agent_launch.default_timeout
        )
        assert_unknown_session_error(entry, "session/resume", unknown_id)


def _resume_updates_for(
    updates: list[tuple[int, TranscriptEntry]], session_id: str
) -> list[tuple[tuple[int, int], dict[str, Any]]]:
    """The `session/update` payloads `resume_session` collected for `session_id`, in wire order,
    each with its `(line_index, position_in_line)`."""
    return [
        (order, update)
        for order, msg in _session_update_messages(updates)
        if (update := _update_for(msg, session_id)) is not None
    ]


@pytest.mark.requirement("ACP-RESUME-210")
@pytest.mark.capability("capabilities.session")
async def test_resume_carries_the_lists_session_new_carried(agent_launch, tmp_path):
    """ACP-RESUME-210. The session is resumed on the connection that created it (the route
    `ACP-RESUME-201` tries first), so `session/new`'s own response is the evidence that it has
    options or commands. A resume that errors SKIPs here; `ACP-RESUME-216` judges that."""
    async with connected_agent(agent_launch) as agent:
        created = await new_session_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        expected = [
            name
            for name in ("configOptions", "availableCommands")
            if isinstance(created.get(name), list) and created[name]
        ]
        if not expected:
            pytest.skip("session/new carried neither configOptions nor availableCommands")
        entry, _updates = await resume_session(
            agent, created["sessionId"], tmp_path, timeout=agent_launch.default_timeout
        )
        msg = entry.parsed
        if not (isinstance(msg, dict) and isinstance(msg.get("result"), dict)):
            pytest.skip(f"session/resume of the just-created session did not succeed: {entry.text!r}")
        missing = [
            name
            for name in expected
            if not (isinstance(msg["result"].get(name), list) and msg["result"][name])
        ]
        assert not missing, (
            f"session/new carried {expected} but session/resume's result omits or empties "
            f"{missing}: {entry.text!r}"
        )


@pytest.mark.requirement("ACP-RESUME-212")
@pytest.mark.capability("capabilities.session")
async def test_resume_replay_has_no_historical_active_state_update(agent_launch, tmp_path):
    """ACP-RESUME-212. After a turn that reached idle, any `running`/`requires_action`
    `state_update` that is not the final one before the response (the snapshot) can only be a
    replayed historical state. A lone active update is the snapshot, which may report live
    work, so it is not judged."""
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
        states = [
            update
            for _, update in _resume_updates_for(updates, session_id)
            if update.get("sessionUpdate") == "state_update"
        ]
        replayed_active = [u for u in states[:-1] if u.get("state") in ACTIVE_STATES]
        assert not replayed_active, (
            f"session/resume replayed historical state_update(s) as current activity before "
            f"the snapshot: {states!r}"
        )


_BACKGROUND_UPDATE_KINDS = {
    "terminal": "terminal_update",
    "tool_call": "tool_call_update",
    "subagent": "subagent_update",
}


@pytest.mark.requirement("ACP-RESUME-213")
@pytest.mark.capability("capabilities.session")
async def test_resume_announces_background_items_before_the_snapshot(agent_launch, tmp_path):
    """ACP-RESUME-213. Resumes with `replayFrom` omitted, so replay cannot have delivered an
    item and each one needs an update of its own. The scenario only exists when the snapshot
    lists background work; otherwise the test SKIPs rather than passing vacuously. A turn runs
    first so work it left running is live at the resume."""
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (agent, session_id, _entry, resume_cwd):
        await _add_history(agent, session_id, timeout=agent_launch.default_timeout)
        response_entry, updates = await resume_session(
            agent, session_id, resume_cwd, timeout=agent_launch.default_timeout
        )
        _assert_resume_succeeded(response_entry, "session/resume")
        ordered = _resume_updates_for(updates, session_id)
        snapshots = [
            (order, update)
            for order, update in ordered
            if update.get("sessionUpdate") == "state_update"
        ]
        if not snapshots:
            pytest.skip("session/resume sent no current-state snapshot (ACP-RESUME-206 judges that)")
        snapshot_order, snapshot = snapshots[-1]
        listed = background_keys(snapshot)
        if not listed:
            pytest.skip("the resume snapshot lists no background work, so nothing is judged")
        unannounced = sorted(
            (kind, item_id)
            for kind, item_id in listed
            if not any(
                order < snapshot_order
                and update.get("sessionUpdate") == _BACKGROUND_UPDATE_KINDS[kind]
                and update.get(BACKGROUND_ID_FIELDS[kind]) == item_id
                for order, update in ordered
            )
        )
        assert not unannounced, (
            f"the resume snapshot lists background item(s) {unannounced} that no update sent "
            f"before it announced: {[update for _, update in ordered]!r}"
        )


@pytest.mark.requirement("ACP-RESUME-214")
@pytest.mark.capability("capabilities.session")
async def test_resume_sends_session_info_before_responding(agent_launch, tmp_path):
    """ACP-RESUME-214. Checked once with `replayFrom` omitted and once with `start`, both after
    a history-producing turn; with `start` the update must follow every replayed history
    update."""
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
            ordered = _resume_updates_for(updates, session_id)
            last_history = max(
                (
                    order
                    for order, update in ordered
                    if update.get("sessionUpdate") in _REPLAYED_HISTORY_KINDS
                ),
                default=None,
            )
            infos = [
                order for order, update in ordered if update.get("sessionUpdate") == "session_info_update"
            ]
            assert infos, (
                f"{label} responded without a session_info_update for the session: "
                f"{[update for _, update in ordered]!r}"
            )
            assert last_history is None or max(infos) > last_history, (
                f"{label}: the session_info_update must follow every replayed history update: "
                f"{[update for _, update in ordered]!r}"
            )


@pytest.mark.requirement("ACP-RESUME-216")
@pytest.mark.capability("capabilities.session")
async def test_resume_of_a_session_active_on_this_connection_succeeds(agent_launch, tmp_path):
    """ACP-RESUME-216. The session is created and resumed on one connection, with no turn in
    between: it is active, so resuming it again must work."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry, _updates = await resume_session(
            agent, session_id, tmp_path, timeout=agent_launch.default_timeout
        )
        _assert_resume_succeeded(entry, "session/resume of a session active on this connection")


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
    is guaranteed to be returned) is not asserted. Paths compare after normalization (the spec
    lets agents normalize). A session is also created in a subdirectory of the filter, so an
    agent that matches by prefix returns it. Records the entry count so an empty-array PASS is
    visibly vacuous in the report."""
    child = tmp_path / "child"
    child.mkdir()
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await new_session(agent, child, timeout=agent_launch.default_timeout)
        entry = await list_sessions(agent, cwd=tmp_path, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/list filtered by cwd did not succeed: {entry.text!r}"
        )
        sessions = msg["result"].get("sessions") or []
        record_property("acp_tck_list_filtered_by_cwd_entry_count", len(sessions))
        for session in sessions:
            assert isinstance(session, dict) and same_dir(session.get("cwd"), tmp_path), (
                f"session/list filtered by cwd={tmp_path!r} returned a session with a "
                f"different cwd (a subdirectory does not match): {session!r}"
            )


async def _relative_cwd_filter_error(agent_launch) -> tuple[Any, dict[str, Any] | None]:
    """`session/list` with a relative `cwd` filter; returns the response entry and its `error`
    object (`None` when the agent answered with anything else). Its `_tck_` prefix marks the
    path as the TCK's own."""
    async with connected_agent(agent_launch) as agent:
        entry = await list_sessions(
            agent, cwd="_tck_relative/dir", timeout=agent_launch.default_timeout
        )
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        return entry, error if isinstance(error, dict) else None


@pytest.mark.requirement("ACP-LIST-205")
@pytest.mark.capability("capabilities.session")
async def test_list_sessions_rejects_relative_cwd_filter(agent_launch):
    """ACP-LIST-205. The `cwd` filter must be absolute and the spec says agents reject a relative
    one (`session-list.mdx:64-65`), so the probe sends a relative path on purpose. Only
    error-vs-result is asserted: the sentence naming `-32602` carries no RFC keyword, so the
    code is ACP-LIST-207's (ADVISORY) concern."""
    entry, error = await _relative_cwd_filter_error(agent_launch)
    assert error is not None, (
        f"session/list with a relative cwd filter should fail with an error, but did not: "
        f"{entry.text!r}"
    )


@pytest.mark.requirement("ACP-LIST-207")
@pytest.mark.capability("capabilities.session")
async def test_list_relative_cwd_filter_rejection_is_invalid_params(agent_launch):
    """ACP-LIST-207 (ADVISORY). The rejection of a relative `cwd` filter is `-32602`
    (`session-list.mdx:64-65`; no RFC keyword, hence ADVISORY). SKIPs when the probe was not
    rejected: that is ACP-LIST-205's failure, not a second one."""
    entry, error = await _relative_cwd_filter_error(agent_launch)
    if error is None:
        pytest.skip(f"session/list with a relative cwd filter was not rejected: {entry.text!r}")
    assert error.get("code") == INVALID_PARAMS, (
        f"session/list with a relative cwd filter was rejected with {error.get('code')!r}, "
        f"expected -32602 (Invalid params): {entry.text!r}"
    )


@pytest.mark.requirement("ACP-LIST-206")
@pytest.mark.capability("capabilities.session")
async def test_list_sessions_rejects_never_issued_cursor(agent_launch, tmp_path):
    """ACP-LIST-206. Cursors are opaque, so the probe is a fabricated `_tck`-prefixed token no
    agent can have issued; never `""`, which is a valid cursor (session-list.mdx:154). A session
    exists first, so an agent that ignores the cursor has a first page to return."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await list_sessions(
            agent,
            cursor=f"_tck-never-issued-cursor-{uuid.uuid4().hex}",
            timeout=agent_launch.default_timeout,
        )
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        assert isinstance(error, dict), (
            f"session/list with a never-issued cursor should fail with -32602, but did not "
            f"return an error: {entry.text!r}"
        )
        assert error.get("code") == INVALID_PARAMS, (
            f"session/list with a never-issued cursor should fail with -32602, got "
            f"{error.get('code')!r}: {entry.text!r}"
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
    """Transcript index of the line carrying `entry` -- which may be a per-message copy of an
    array line (`run_prompt` dispatches array elements that way), so match by identity of the
    shared raw bytes rather than by object identity alone."""
    for index, candidate in enumerate(agent.transcript):
        if candidate is entry or (
            candidate.raw is entry.raw and candidate.timestamp == entry.timestamp
        ):
            return index
    raise AssertionError(f"entry not found in the transcript: {entry.text!r}")


async def _close_mid_turn(agent, session_id: str, cancel_prompt_text: str, *, timeout: float):
    """Prompt `session_id` with `cancel_prompt_text` and send `session/close` mid-turn. Returns
    `(turn, close_id)`; the close was only sent if `turn.action_sent_at_index` is not `None`."""
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
        timeout=timeout,
    )
    return turn, close_id


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
        turn, close_id = await _close_mid_turn(
            agent, session_id, cancel_prompt_text, timeout=agent_launch.default_timeout
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


def _assert_no_session_messages_after(agent, close_entry: TranscriptEntry, session_id: str) -> None:
    """Fail if the agent sent a `session/update` or an agent -> client request carrying
    `session_id` after the successful `session/close` response `close_entry`. Responses
    (earlier prompts') are not messages with a `method`, so they are exempt."""
    close_index = _transcript_index(agent, close_entry)
    late = []
    for entry in agent.transcript[close_index + 1 :]:
        if entry.direction is not Direction.RECEIVED:
            continue
        for message in iter_messages(entry):
            params = message.get("params")
            if (
                "method" in message
                and isinstance(params, dict)
                and params.get("sessionId") == session_id
            ):
                late.append(message.get("method"))
    assert not late, (
        f"the agent sent {late!r} for session {session_id!r} after its successful "
        "session/close response"
    )


@pytest.mark.requirement("ACP-CLOSE-206")
@pytest.mark.capability("capabilities.session")
async def test_idle_close_is_followed_by_no_session_messages(agent_launch, tmp_path):
    """ACP-CLOSE-206 for the close of an idle session. SKIPs when the close itself did not
    succeed (`ACP-CLOSE-201`'s finding)."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        entry = await close_session(agent, session_id, timeout=timeout)
        msg = entry.parsed
        if not (isinstance(msg, dict) and isinstance(msg.get("result"), dict)):
            pytest.skip(f"prerequisite not met: session/close did not succeed: {entry.text!r}")
        await drain_quiet(agent, quiet_period(timeout))
        _assert_no_session_messages_after(agent, entry, session_id)


@pytest.mark.requirement("ACP-CLOSE-206")
@pytest.mark.capability("capabilities.session")
async def test_mid_turn_close_is_followed_by_no_session_messages(
    agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-CLOSE-206 for a close that cancels work mid-turn. Same scenario and SKIP rules as
    `ACP-CLOSE-203`; a turn that never ends (`ACP-CLOSE-202`/`203`'s finding) also SKIPs here."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            turn, close_id = await _close_mid_turn(
                agent, session_id, cancel_prompt_text, timeout=timeout
            )
        except AgentTimeout:
            pytest.skip("prerequisite not met: the turn never ended -- see ACP-CLOSE-202")
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
            close_entry = await agent.wait_for_response(close_id, timeout=timeout)
        close_msg = close_entry.parsed
        if not (isinstance(close_msg, dict) and isinstance(close_msg.get("result"), dict)):
            pytest.skip(f"prerequisite not met: session/close did not succeed: {close_entry.text!r}")
        await drain_quiet(agent, quiet_period(timeout))
        _assert_no_session_messages_after(agent, close_entry, session_id)


def _assert_close_succeeded_idempotently(entry: TranscriptEntry, what: str) -> None:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    assert not isinstance(error, dict), (
        f"session/close of {what} should succeed with the empty result (closing is idempotent), "
        f"but returned error {error.get('code')!r}: {entry.text!r}"
    )
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/close of {what} did not return a result object: {entry.text!r}"
    )
    issues = validate_agent_response("session/close", msg)
    assert not issues, f"session/close result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-CLOSE-207")
@pytest.mark.capability("capabilities.session")
async def test_close_already_closed_session_succeeds(agent_launch, tmp_path):
    """ACP-CLOSE-207 (ADVISORY). A second `session/close` for the same id must answer like the
    first. The first close failing SKIPs (`ACP-CLOSE-201` judges it). `-32002` is an ADVISORY
    FAIL: clients tolerate it as success, but the agent SHOULD return the empty result."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        first = await close_session(agent, session_id, timeout=timeout)
        first_msg = first.parsed
        if not (isinstance(first_msg, dict) and isinstance(first_msg.get("result"), dict)):
            pytest.skip(
                f"prerequisite not met: the first session/close did not succeed: {first.text!r}"
            )
        second = await close_session(agent, session_id, timeout=timeout)
        _assert_close_succeeded_idempotently(second, "an already-closed session")


@pytest.mark.requirement("ACP-CLOSE-207")
@pytest.mark.capability("capabilities.session")
async def test_close_unknown_session_succeeds(agent_launch):
    """ACP-CLOSE-207 (ADVISORY). No `session/new` is sent: this id was never created on this
    connection (`session-setup.mdx:407` covers a session that does not exist)."""
    async with connected_agent(agent_launch) as agent:
        entry = await close_session(
            agent, f"tck-never-created-{uuid.uuid4().hex}", timeout=agent_launch.default_timeout
        )
        skip_if_auth_gated(entry)
        _assert_close_succeeded_idempotently(entry, "a never-created session")


@pytest.mark.requirement("ACP-CLOSE-204")
@pytest.mark.capability("capabilities.session")
async def test_prompt_pending_at_close_is_answered(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-CLOSE-204 (ADVISORY). Sends `session/prompt` and `session/close` back to back
    without awaiting the prompt's receipt. Every legal answer passes: `-32800` (closing
    prevented insertion), a success with a `messageId` (already inserted), or `-32002` (the
    agent processed the close first, so the session was no longer active; ordered delivery does
    not order processing). The order of the two responses is not judged -- prompt responses
    need not precede the close response."""
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
        not_active = isinstance(error, dict) and error.get("code") == RESOURCE_NOT_FOUND
        record_property(
            "acp_tck_close_pending_prompt_outcome",
            "inserted"
            if inserted
            else "cancelled"
            if cancelled
            else "not_active"
            if not_active
            else "other",
        )
        assert inserted or cancelled or not_active, (
            "a session/prompt pending when session/close arrived must be answered with -32800, "
            f"-32002 or a success carrying its messageId, got: {entry.text!r}"
        )


# --- session/delete (ACP-DELETE-201..205) ---


def _listed_ids(entry: TranscriptEntry) -> set[Any]:
    msg = entry.parsed
    sessions = (
        (msg.get("result") or {}).get("sessions") or [] if isinstance(msg, dict) else []
    )
    return {s.get("sessionId") for s in sessions if isinstance(s, dict)}


def _is_not_found(entry: TranscriptEntry) -> bool:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return isinstance(error, dict) and error.get("code") == RESOURCE_NOT_FOUND


def _delete_succeeded_or_gone(entry: TranscriptEntry) -> bool:
    """A delete result, or a `-32002` answer, which clients SHOULD treat as a successful delete
    (session-delete.mdx:92; error.mdx:56). `ACP-DELETE-203` is what judges the agent for it."""
    msg = entry.parsed
    return (isinstance(msg, dict) and isinstance(msg.get("result"), dict)) or _is_not_found(entry)


@pytest.mark.requirement("ACP-DELETE-201")
@pytest.mark.capability("capabilities.session.delete")
async def test_delete_existing_session_succeeds(agent_launch, tmp_path):
    """ACP-DELETE-201. Deletes a session that is active and idle on this connection: it exists
    for certain, and deleting an active session closes it first (session-delete.mdx:95). A
    `-32002` answer is not tolerated here, unlike the rows that use `session/delete` as setup:
    nothing has closed or discarded this session, so there is no "already gone" case to excuse."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await delete_session(agent, session_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/delete of an existing, active session did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/delete", msg)
        assert not issues, f"session/delete result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-DELETE-202")
@pytest.mark.capability("capabilities.session.delete")
async def test_deleted_session_no_longer_listed(agent_launch, tmp_path):
    """ACP-DELETE-202. Closes the session first, then SKIPs when `session/list` does not report
    the closed session at all -- nothing to compare against. A `-32002` answer to the delete
    counts as a successful delete (the agent may have discarded the closed session,
    session-setup.mdx:52), so the listing is still judged; `ACP-DELETE-203` judges the SHOULD."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await close_session(agent, session_id, timeout=agent_launch.default_timeout)
        before_entry = await list_sessions(agent, timeout=agent_launch.default_timeout)
        if session_id not in _listed_ids(before_entry):
            pytest.skip("session/list does not report the closed session in the first place")

        delete_entry = await delete_session(agent, session_id, timeout=agent_launch.default_timeout)
        assert _delete_succeeded_or_gone(delete_entry), (
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
    succeed silently, not error. `-32002` is the deviation clients are told to tolerate
    (session-delete.mdx:92), but the agent SHOULD still succeed."""
    async with connected_agent(agent_launch) as agent:
        entry = await delete_session(agent, "tck-never-created", timeout=agent_launch.default_timeout)
        msg = entry.parsed
        if _is_not_found(entry):
            pytest.fail(
                "session/delete of an unknown sessionId answered -32002; clients treat that as a "
                "successful delete, but the agent SHOULD succeed silently "
                f"(session-delete.mdx:91, error.mdx:56): {entry.text!r}"
            )
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/delete of an unknown sessionId should succeed silently, but answered with "
            f"an error other than -32002, which is worse: {entry.text!r}"
        )


@pytest.mark.requirement("ACP-DELETE-204")
@pytest.mark.capability("capabilities.session.delete")
async def test_delete_cancels_foreground_work(
    agent_launch, tmp_path, cancel_prompt_text, record_property
):
    """ACP-DELETE-204. Same scenario and race rules as `ACP-CLOSE-202`/`203`, with
    `session/delete` as the mid-turn trigger: deleting an active session cancels its work as if
    `session/close` had been called (session-delete.mdx:95), so the turn ends with a `cancelled`
    idle that arrives before the delete response. If the delete kept the prompt from being
    inserted, the prompt is answered `-32800` (session-setup.mdx:395); any other error FAILs. A
    turn that never ends FAILs through the harness timeout, so a delete rejected without
    cancelling the work FAILs here (the cancel-then-delete MUST, session-delete.mdx:95). The
    ordering is judged only against a delete that succeeded (or answered `-32002`); the one
    case it SKIPs is a delete error after the work was cancelled anyway (`ACP-DELETE-201` owns
    the delete's own success)."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        delete_id = None

        async def _delete():
            nonlocal delete_id
            delete_id = await agent.send_request("session/delete", {"sessionId": session_id})
            return delete_id

        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": cancel_prompt_text}],
            on_action=_delete,
            timeout=timeout,
        )
        skip_if_turn_end_race_not_exercised(
            agent,
            turn,
            record_property,
            race_window=quiet_period(timeout),
            trigger_at_index=turn.action_sent_at_index,
            trigger_method="session/delete",
            verb="cancellation-via-delete",
            property_prefix="delete_cancel",
        )
        error = response_error(turn)
        if error is not None:
            assert error.get("code") == REQUEST_CANCELLED, (
                f"session/delete answered the in-flight session/prompt with an error other than "
                f"-32800: {error!r}"
            )
        if turn.idle_update is None:
            return  # prompt cancelled before insertion: no foreground work, no idle owed
        assert turn.stop_reason == "cancelled", (
            f"expected stopReason 'cancelled' after session/delete on a session with in-flight "
            f"work, got {turn.stop_reason!r}"
        )
        delete_entry = turn.action_response
        if delete_entry is None:
            delete_entry = await agent.wait_for_response(delete_id, timeout=timeout)
        if not _delete_succeeded_or_gone(delete_entry):
            pytest.skip(
                "prerequisite not met: session/delete did not succeed, so the ordering rule "
                f"does not apply (see ACP-DELETE-201): {delete_entry.text!r}"
            )
        idle_index = _transcript_index(agent, turn.idle_update)
        delete_index = _transcript_index(agent, delete_entry)
        assert delete_index >= idle_index, (
            "session/delete responded before sending the cancelled idle state_update for the "
            f"work it cancelled: delete response {delete_entry.text!r} came before idle "
            f"{turn.idle_update.text!r}"
        )


@pytest.mark.requirement("ACP-DELETE-205")
@pytest.mark.capability("capabilities.session.delete")
async def test_resume_of_deleted_session_is_not_found(agent_launch, tmp_path):
    """ACP-DELETE-205. A deleted session is gone: `session/resume` of it gets `-32002` with
    `data.sessionId` (session-delete.mdx:94, error.mdx:54,56). A `-32002` answer to the delete
    itself counts as a successful delete (session-delete.mdx:92), so the resume is still judged;
    any other delete error SKIPs (that is `ACP-DELETE-201`'s finding)."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        delete_entry = await delete_session(agent, session_id, timeout=timeout)
        if not _delete_succeeded_or_gone(delete_entry):
            pytest.skip(
                "prerequisite not met: session/delete did not succeed (see ACP-DELETE-201): "
                f"{delete_entry.text!r}"
            )
        entry, _updates = await resume_session(agent, session_id, tmp_path, timeout=timeout)
        assert_unknown_session_error(entry, "session/resume", session_id)


# --- session/archive and session/unarchive (unstable; ACP-ARCHIVE-002..006, 201) ---

_ARCHIVE_PATH = "capabilities.session.archive"
_ARCHIVE_UNKNOWN_SESSION_ID = "tck-never-created-session"
# An `archived` filter value no agent supports: `_`-prefixed values are the implementation-extension
# space (`schema/v2/schema.unstable.json#/$defs/SessionArchiveFilter`), so the probe does not squat
# on a value ACP may define later.
_UNSUPPORTED_ARCHIVE_FILTER = "_tck_unsupported"
_MAX_LIST_PAGES = 10
_ARCHIVE_FILTER_RFD = (
    " (Draft RFD docs/rfds/session-archive.mdx:112: an agent that advertises `archive` MUST "
    "support all three `archived` values, `exclude`, `include` and `only`)"
)


async def _list_view(agent, cwd, archived, *, timeout: float) -> list[dict[str, Any]]:
    """Every `SessionInfo` from `session/list` for `cwd` (and `archived`, unless `None`), following
    `nextCursor` for up to `_MAX_LIST_PAGES` pages. Asserts each page succeeds."""
    sessions: list[dict[str, Any]] = []
    cursor = None
    for _ in range(_MAX_LIST_PAGES):
        entry = await list_sessions(agent, cwd=cwd, cursor=cursor, archived=archived, timeout=timeout)
        msg = entry.parsed
        result = msg.get("result") if isinstance(msg, dict) else None
        assert isinstance(result, dict), (
            f"session/list (archived={archived!r}) did not succeed: {entry.text!r}"
            + (_ARCHIVE_FILTER_RFD if archived in ("include", "only") else "")
        )
        page = result.get("sessions")
        assert isinstance(page, list), f"session/list result.sessions is not an array: {result!r}"
        sessions += [info for info in page if isinstance(info, dict)]
        cursor = result.get("nextCursor")
        if not isinstance(cursor, str):
            break
    return sessions


def _view_ids(sessions: list[dict[str, Any]]) -> list[Any]:
    return [info.get("sessionId") for info in sessions]


async def _archive_call(agent, method: str, session_id: str, *, timeout: float) -> TranscriptEntry:
    req_id = await agent.send_request(method, {"sessionId": session_id})
    return await agent.wait_for_response(req_id, timeout=timeout)


def _has_result(entry: TranscriptEntry) -> bool:
    msg = entry.parsed
    return isinstance(msg, dict) and isinstance(msg.get("result"), dict)


def _assert_archive_succeeded(entry: TranscriptEntry, method: str, what: str) -> None:
    assert _has_result(entry), f"{method} of {what} did not succeed: {entry.text!r}"
    issues = validate_agent_response(method, entry.parsed)
    assert not issues, f"{method} result failed schema validation: {issues!r}"


async def _delete_quietly(agent, session_id: str, init_result, *, timeout: float) -> None:
    """Best-effort cleanup so the test does not leave a session in a real agent's store. The
    outcome is ignored: `ACP-DELETE-*` judge `session/delete`."""
    if init_result is None or not capability_is_supported(init_result, "capabilities.session.delete"):
        return
    with contextlib.suppress(AgentTimeout, AgentExited):
        await delete_session(agent, session_id, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-002")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_listed_sessions_carry_boolean_archived(agent_launch, agent_initialize_result, tmp_path):
    """ACP-ARCHIVE-002. Lists with a `cwd` filter, so the pages hold only this test's session.
    Checks the default view, then (if `session/archive` works; `ACP-ARCHIVE-003` judges it) the
    `only` view, so an agent that sets the flag only on unarchived sessions is caught."""
    init_result = agent_initialize_result.result
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            listed = await _list_view(agent, tmp_path, None, timeout=timeout)
            if not listed:
                pytest.skip("session/list returned no session to inspect")
            missing = _view_ids([info for info in listed if not isinstance(info.get("archived"), bool)])
            assert not missing, f"listed sessions without a boolean `archived`: {missing!r}"

            archived = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            if _has_result(archived):
                only = await _list_view(agent, tmp_path, "only", timeout=timeout)
                missing = _view_ids([info for info in only if not isinstance(info.get("archived"), bool)])
                assert not missing, (
                    f"sessions listed under archived=only without a boolean `archived`: {missing!r}"
                )
        finally:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-003")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_and_unarchive_round_trip(agent_launch, agent_initialize_result, tmp_path):
    """ACP-ARCHIVE-003. Checks membership in the default, `include` and `only` views (all pages,
    filtered by `cwd`); the `archived` flag itself is `ACP-ARCHIVE-002`'s. An agent that does not
    list the fresh session at all SKIPs: the views cannot be compared."""
    init_result = agent_initialize_result.result
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            if session_id not in _view_ids(await _list_view(agent, tmp_path, None, timeout=timeout)):
                pytest.skip("the new session is not listed by session/list, so archive views cannot be compared")

            archived = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            _assert_archive_succeeded(archived, "session/archive", "an existing session")
            default_ids = _view_ids(await _list_view(agent, tmp_path, None, timeout=timeout))
            assert session_id not in default_ids, (
                f"archived session {session_id!r} still appears in the default session/list view: "
                f"{default_ids!r}"
            )
            only = await _list_view(agent, tmp_path, "only", timeout=timeout)
            include = await _list_view(agent, tmp_path, "include", timeout=timeout)
            for view, name in ((only, "only"), (include, "include")):
                assert session_id in _view_ids(view), (
                    f"archived session {session_id!r} is missing from archived={name}: {_view_ids(view)!r}"
                )

            unarchived = await _archive_call(agent, "session/unarchive", session_id, timeout=timeout)
            _assert_archive_succeeded(unarchived, "session/unarchive", "an archived session")
            default_ids = _view_ids(await _list_view(agent, tmp_path, None, timeout=timeout))
            assert session_id in default_ids, (
                f"unarchived session {session_id!r} is missing from the default session/list view: "
                f"{default_ids!r}"
            )
            include_ids = _view_ids(await _list_view(agent, tmp_path, "include", timeout=timeout))
            assert session_id in include_ids, (
                f"unarchived session {session_id!r} is missing from archived=include: {include_ids!r}"
            )
            only_ids = _view_ids(await _list_view(agent, tmp_path, "only", timeout=timeout))
            assert session_id not in only_ids, (
                f"unarchived session {session_id!r} still appears under archived=only: {only_ids!r}"
            )
        finally:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-004")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_unsupported_archived_filter_gets_invalid_params(agent_launch):
    """ACP-ARCHIVE-004. The spec names the code (`-32602`) as a MUST, so a different error is a
    FAIL too, as is a result (the agent fell back to `exclude`). The probe value is
    `_`-prefixed (see `_UNSUPPORTED_ARCHIVE_FILTER`). `-32000` SKIPs."""
    async with connected_agent(agent_launch) as agent:
        entry = await list_sessions(
            agent, archived=_UNSUPPORTED_ARCHIVE_FILTER, timeout=agent_launch.default_timeout
        )
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        if isinstance(error, dict) and error.get("code") == AUTHENTICATION_REQUIRED:
            pytest.skip("session/list returned -32000 (authentication required)")
        assert isinstance(error, dict), (
            f"session/list with an unsupported archived filter must fail with -32602, but did not "
            f"return an error: {entry.text!r}"
        )
        assert error.get("code") == INVALID_PARAMS, (
            f"session/list with an unsupported archived filter must fail with -32602, got "
            f"{error.get('code')!r}: {entry.text!r}"
        )


@pytest.mark.requirement("ACP-ARCHIVE-005")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_and_unarchive_are_idempotent(agent_launch, agent_initialize_result, tmp_path):
    """ACP-ARCHIVE-005. Archive twice, then unarchive twice: each call must succeed. The first
    archive failing SKIPs (`ACP-ARCHIVE-003` judges it)."""
    init_result = agent_initialize_result.result
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        try:
            first = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            if not _has_result(first):
                pytest.skip(
                    "prerequisite not met: the first session/archive did not succeed "
                    f"(see ACP-ARCHIVE-003): {first.text!r}"
                )
            again = await _archive_call(agent, "session/archive", session_id, timeout=timeout)
            _assert_archive_succeeded(again, "session/archive", "an already-archived session")
            unarchived = await _archive_call(agent, "session/unarchive", session_id, timeout=timeout)
            _assert_archive_succeeded(unarchived, "session/unarchive", "an archived session")
            again = await _archive_call(agent, "session/unarchive", session_id, timeout=timeout)
            _assert_archive_succeeded(again, "session/unarchive", "a not-archived session")
        finally:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)


@pytest.mark.requirement("ACP-ARCHIVE-005")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_unknown_session_is_not_found(agent_launch, tmp_path):
    """ACP-ARCHIVE-005. Unlike `session/delete`, these do not succeed silently for a session that
    does not exist: `-32002` with `data.sessionId` (session-list.mdx:251, error.mdx:54,66). A
    session is created first, so an auth-gated agent SKIPs `AUTH-GATED:` instead of failing on
    `-32000`; the probed id is still one no agent can have created."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        for method in ("session/archive", "session/unarchive"):
            entry = await _archive_call(
                agent, method, _ARCHIVE_UNKNOWN_SESSION_ID, timeout=agent_launch.default_timeout
            )
            assert_unknown_session_error(entry, method, _ARCHIVE_UNKNOWN_SESSION_ID)


@pytest.mark.requirement("ACP-ARCHIVE-006")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_deleted_session_is_absent_under_every_archived_filter(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ARCHIVE-006. Closes the gap `ACP-DELETE-202` leaves (it checks only the default view):
    an agent that implements delete as archive hides the session there but not under
    `include`/`only`. Needs `capabilities.session.delete` too, which `@pytest.mark.capability`
    cannot express as a second gate, so it SKIPs here. As for `ACP-DELETE-202`, a `-32002` answer
    to the delete counts as success. An agent that does not list the fresh session before the
    delete SKIPs, as `ACP-ARCHIVE-003` does: its disappearance would otherwise be vacuous."""
    init_result = agent_initialize_result.result
    if init_result is None or not capability_is_supported(init_result, "capabilities.session.delete"):
        pytest.skip("capability 'capabilities.session.delete' not advertised by the agent under test")
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        listed_before = _view_ids(await _list_view(agent, tmp_path, "include", timeout=timeout))
        if session_id not in listed_before:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)
            pytest.skip("the new session is not listed by session/list, so its deletion cannot be observed")
        delete_entry = await delete_session(agent, session_id, timeout=timeout)
        if not _delete_succeeded_or_gone(delete_entry):
            pytest.skip(
                "prerequisite not met: session/delete did not succeed (see ACP-DELETE-201): "
                f"{delete_entry.text!r}"
            )
        for archived in ("exclude", "include", "only"):
            listed = _view_ids(await _list_view(agent, tmp_path, archived, timeout=timeout))
            assert session_id not in listed, (
                f"deleted session {session_id!r} still appears under archived={archived!r}: {listed!r}"
            )


@pytest.mark.requirement("ACP-ARCHIVE-201")
@pytest.mark.capability(_ARCHIVE_PATH)
async def test_archive_cancels_foreground_work(
    agent_launch, agent_initialize_result, tmp_path, cancel_prompt_text, record_property
):
    """ACP-ARCHIVE-201. Same scenario and race rules as `ACP-DELETE-204`, with `session/archive`
    as the mid-turn trigger: archiving an active session cancels its work as if `session/close`
    had been called (session-list.mdx:247), so the turn ends with a `cancelled` idle that arrives
    before the archive response. If the archive kept the prompt from being inserted, the prompt is
    answered `-32800` (session-setup.mdx:395); any other error FAILs. A turn that never ends
    FAILs through the harness timeout, so an archive rejected without cancelling the work FAILs
    here (an active session is archivable, session-list.mdx:247). The ordering is judged only
    against an archive that succeeded; the one case it SKIPs is an archive error after the work
    was cancelled anyway (`ACP-ARCHIVE-003` owns the archive's own success)."""
    init_result = agent_initialize_result.result
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        archive_id = None

        async def _archive():
            nonlocal archive_id
            archive_id = await agent.send_request("session/archive", {"sessionId": session_id})
            return archive_id

        try:
            turn = await run_prompt(
                agent,
                session_id,
                [{"type": "text", "text": cancel_prompt_text}],
                on_action=_archive,
                timeout=timeout,
            )
            skip_if_turn_end_race_not_exercised(
                agent,
                turn,
                record_property,
                race_window=quiet_period(timeout),
                trigger_at_index=turn.action_sent_at_index,
                trigger_method="session/archive",
                verb="cancellation-via-archive",
                property_prefix="archive_cancel",
            )
            error = response_error(turn)
            if error is not None:
                assert error.get("code") == REQUEST_CANCELLED, (
                    f"session/archive answered the in-flight session/prompt with an error other "
                    f"than -32800: {error!r}"
                )
            if turn.idle_update is None:
                return  # prompt cancelled before insertion: no foreground work, no idle owed
            assert turn.stop_reason == "cancelled", (
                f"expected stopReason 'cancelled' after session/archive on a session with "
                f"in-flight work, got {turn.stop_reason!r}"
            )
            archive_entry = turn.action_response
            if archive_entry is None:
                archive_entry = await agent.wait_for_response(archive_id, timeout=timeout)
            if not _has_result(archive_entry):
                pytest.skip(
                    "prerequisite not met: session/archive did not succeed, so the ordering "
                    f"rule does not apply (see ACP-ARCHIVE-003): {archive_entry.text!r}"
                )
            idle_index = _transcript_index(agent, turn.idle_update)
            archive_index = _transcript_index(agent, archive_entry)
            assert archive_index >= idle_index, (
                "session/archive responded before sending the cancelled idle state_update for "
                f"the work it cancelled: archive response {archive_entry.text!r} came before "
                f"idle {turn.idle_update.text!r}"
            )
        finally:
            await _delete_quietly(agent, session_id, init_result, timeout=timeout)


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


@pytest.mark.requirement("ACP-ADDDIRS-203")
@pytest.mark.capability("capabilities.session.additionalDirectories")
async def test_new_session_with_relative_additional_directory_rejected(agent_launch, tmp_path):
    """ACP-ADDDIRS-203. Sends a relative entry on purpose, since the capability is advertised
    and the spec defines the agent's answer to it (`session-setup.mdx:443`): `-32602`."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new",
            {"cwd": str(tmp_path), "additionalDirectories": ["tck-relative-dir"]},
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        assert isinstance(error, dict) and error.get("code") == INVALID_PARAMS, (
            "session/new with a relative additionalDirectories entry must be rejected with "
            f"-32602, got: {entry.text!r}"
        )


# --- MCP servers (ACP-MCP-201/202 INFORMATIONAL, ACP-MCP-203..205) ---


def _notice_seen(agent, session_id: Any) -> bool:
    """Whether the agent sent a `notice` `session/update` for `session_id`."""
    for entry in agent.transcript:
        if entry.direction is not Direction.RECEIVED:
            continue
        for message in iter_messages(entry):
            params = message.get("params")
            if message.get("method") == "session/update" and isinstance(params, dict):
                update = params.get("update")
                if (
                    params.get("sessionId") == session_id
                    and isinstance(update, dict)
                    and update.get("sessionUpdate") == "notice"
                ):
                    return True
    return False


@pytest.mark.requirement("ACP-MCP-201")
@pytest.mark.capability("capabilities.session.mcp.stdio")
async def test_new_session_with_stdio_mcp_server_recorded(agent_launch, tmp_path, record_property):
    """ACP-MCP-201 (INFORMATIONAL). Never asserts on the outcome -- see the requirements module
    docstring's judgment-call note. Also records whether a `notice` for the new session was seen
    after an accepted request (`session-setup.mdx:685`: an agent that continues without a failed
    server SHOULD tell the user, for example with a notice).

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
        if accepted:
            session_id = msg["result"].get("sessionId")
            await drain_quiet(agent, quiet_period(agent_launch.default_timeout))
            record_property(
                "acp_tck_mcp_stdio_notice_after_accepted", _notice_seen(agent, session_id)
            )


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


def _stdio_server(name: str = "tck-stdio", **extra: Any) -> dict[str, Any]:
    return {
        "type": "stdio",
        "name": name,
        "command": "/bin/nonexistent-tck-mcp-server",
        "args": [],
        **extra,
    }


@pytest.mark.requirement("ACP-MCP-203")
@pytest.mark.capability("capabilities.session")
async def test_new_session_with_unsupported_mcp_transport_is_rejected(agent_launch, tmp_path):
    """ACP-MCP-203. Two probes on one connection, each must get `-32602`: v1's `sse`, which
    the spec names (`session-setup.mdx:545`), and `_tck_unsupported_transport`, which no agent
    supports (`_`-prefixed types are implementation-specific, `:553`). Both break the client
    rule to send only advertised transports on purpose: the spec defines the agent's answer to
    exactly these inputs. A success or another code on either FAILs; both are reported."""
    probes = {
        "sse": {
            "type": "sse",
            "name": "tck-sse",
            "url": "http://127.0.0.1:1/tck-sse",
            "headers": [],
        },
        "_tck_unsupported_transport": {
            "type": "_tck_unsupported_transport",
            "name": "tck-unsupported",
        },
    }
    problems = []
    async with connected_agent(agent_launch) as agent:
        for transport, server in probes.items():
            req_id = await agent.send_request(
                "session/new", {"cwd": str(tmp_path), "mcpServers": [server]}
            )
            entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
            skip_if_auth_gated(entry)
            msg = entry.parsed
            error = msg.get("error") if isinstance(msg, dict) else None
            if not (isinstance(error, dict) and error.get("code") == INVALID_PARAMS):
                problems.append(f"{transport!r}: expected -32602, got {entry.text!r}")
    assert not problems, (
        "session/new with an MCP server of an unsupported transport must be rejected with "
        f"-32602: {'; '.join(problems)}"
    )


@pytest.mark.requirement("ACP-MCP-204")
@pytest.mark.capability("capabilities.session.mcp.stdio")
async def test_new_session_with_duplicate_mcp_server_names_is_rejected(agent_launch, tmp_path):
    """ACP-MCP-204 (ADVISORY). Two stdio servers sharing a `name` (`session-setup.mdx:547`), which
    breaks the client rule that names be unique on purpose. The command does not exist, so an
    agent that does not reject the request has nothing real to launch."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new",
            {
                "cwd": str(tmp_path),
                "mcpServers": [_stdio_server("tck-duplicate"), _stdio_server("tck-duplicate")],
            },
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        assert isinstance(error, dict) and error.get("code") == INVALID_PARAMS, (
            f"session/new with duplicate MCP server names must be rejected with -32602, "
            f"got: {entry.text!r}"
        )


_MCP_STUB = Path(__file__).with_name("_mcp_stub.py")
_CANARY_ENV_NAME = "ACP_TCK_CANARY"
_STUB_GRACE_SECONDS = 3.0


async def _best_effort(awaitable) -> None:
    """Await `awaitable` and ignore how it ends: other requirements judge these exchanges, this
    only wants the traffic they produce."""
    try:
        await awaitable
    except AgentTimeout:
        pass


async def _drive_and_scan_for_canary(
    agent_launch, tmp_path, server: dict[str, Any], canary: str, marker: Path | None
) -> list[str]:
    """Create a session with `server`, then run one prompt turn, `session/list` and a
    `session/resume` of the same session with the same server (replaying from the start), and
    return where `canary` showed up: any stdout line the agent wrote, its stderr, and the stdio
    stub's command line. The prompt text never contains the canary, so an agent that
    legitimately repeats the user's words cannot trip this."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": [server]}
        )
        entry = await agent.wait_for_response(req_id, timeout=timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        if not (isinstance(msg, dict) and isinstance(msg.get("result"), dict)):
            pytest.skip(
                f"prerequisite not met: session/new with an MCP server did not succeed "
                f"(see ACP-MCP-201/202): {entry.text!r}"
            )
        session_id = msg["result"].get("sessionId")
        await _best_effort(
            run_prompt(agent, session_id, [{"type": "text", "text": "hello"}], timeout=timeout)
        )
        await _best_effort(list_sessions(agent, cwd=tmp_path, timeout=timeout))
        await _best_effort(
            resume_session(
                agent,
                session_id,
                tmp_path,
                replay_from={"type": "start"},
                mcp_servers=[server],
                timeout=timeout,
            )
        )
        if marker is not None:
            # Give a stub the agent launches in the background a moment to write its marker.
            loop = asyncio.get_running_loop()
            deadline = loop.time() + min(timeout, _STUB_GRACE_SECONDS)
            while not marker.exists() and loop.time() < deadline:
                await asyncio.sleep(0.05)
    # Checked after the context closes, so late-written stdout/stderr is already captured.
    needle = canary.encode()
    leaks = []
    for transcript_entry in agent.transcript:
        if transcript_entry.direction is Direction.RECEIVED and needle in transcript_entry.raw:
            leaks.append(f"stdout line: {transcript_entry.text!r}")
    if canary in agent.stderr_text():
        leaks.append("stderr")
    if marker is not None and marker.exists():
        try:
            argv = json.loads(marker.read_text()).get("argv", [])
        except (ValueError, AttributeError):
            argv = []
        if any(canary in str(arg) for arg in argv):
            leaks.append(f"the stub MCP server's command line: {argv!r}")
    return leaks


@pytest.mark.requirement("ACP-MCP-205")
@pytest.mark.capability("capabilities.session.mcp.stdio")
async def test_mcp_env_value_is_never_echoed(agent_launch, tmp_path):
    """ACP-MCP-205 (ADVISORY). A random canary in a stdio MCP server's `env` (the server is the
    TCK's stub, which records its command line) must appear in none of the agent's stdout lines
    or its stderr, nor in the stub's command line, across a prompt turn, `session/list` and a
    `session/resume` with the same server (`session-setup.mdx:695`). The stub is only checked if
    the agent launched it within a short grace period. Model context, logging beyond stderr and
    persistence are not observable and not covered."""
    canary = f"tck-canary-{uuid.uuid4().hex}"
    marker = tmp_path / "mcp-marker"
    server = {
        "type": "stdio",
        "name": "acp-tck-stub",
        "command": sys.executable,
        "args": [str(_MCP_STUB), str(marker)],
        "env": [{"name": _CANARY_ENV_NAME, "value": canary}],
    }
    leaks = await _drive_and_scan_for_canary(agent_launch, tmp_path, server, canary, marker)
    assert not leaks, f"the MCP env value {canary!r} leaked into: {'; '.join(leaks)}"


@pytest.mark.requirement("ACP-MCP-205")
@pytest.mark.capability("capabilities.session.mcp.http")
async def test_mcp_header_value_is_never_echoed(agent_launch, tmp_path):
    """ACP-MCP-205 (ADVISORY). Same scan as the stdio env test, for a canary in an http MCP
    server's `headers` (an unreachable URL: there is no server to connect to)."""
    canary = f"tck-canary-{uuid.uuid4().hex}"
    server = {
        "type": "http",
        "name": "tck-http",
        "url": "http://127.0.0.1:1/tck-nonexistent",
        "headers": [{"name": "Authorization", "value": f"Bearer {canary}"}],
    }
    leaks = await _drive_and_scan_for_canary(agent_launch, tmp_path, server, canary, None)
    assert not leaks, f"the MCP header value {canary!r} leaked into: {'; '.join(leaks)}"


# --- session/fork (ACP-FORK-201..205, unstable) ---


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


@pytest.mark.requirement("ACP-FORK-203")
@pytest.mark.capability("capabilities.session.fork")
async def test_fork_of_unknown_session_is_not_found(agent_launch, tmp_path):
    """ACP-FORK-203. A source the agent never created gets `-32002` with `data.sessionId`
    (error.mdx:54,64). The id is `_tck`-prefixed so it cannot collide with a stored session."""
    unknown_id = "_tck_never_created_session"
    async with connected_agent(agent_launch) as agent:
        entry = await _fork_session(
            agent, unknown_id, tmp_path, timeout=agent_launch.default_timeout
        )
        assert_unknown_session_error(entry, "session/fork", unknown_id)


@pytest.mark.requirement("ACP-FORK-204")
@pytest.mark.capability("capabilities.session.fork")
async def test_fork_of_closed_listed_session_succeeds(agent_launch, tmp_path):
    """ACP-FORK-204. The fork source only has to exist, not be active (error.mdx:64). SKIPs
    when `session/list` does not report the closed session: whether it still exists is then up to
    the agent (session-setup.mdx:52)."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        source_id = await new_session(agent, tmp_path, timeout=timeout)
        close_entry = await close_session(agent, source_id, timeout=timeout)
        close_msg = close_entry.parsed
        if not (isinstance(close_msg, dict) and isinstance(close_msg.get("result"), dict)):
            pytest.skip(f"prerequisite not met: session/close did not succeed: {close_entry.text!r}")
        listing = await list_sessions(agent, cwd=tmp_path, timeout=timeout)
        if source_id not in _listed_ids(listing):
            pytest.skip("session/list does not report the closed session in the first place")
        entry = await _fork_session(agent, source_id, tmp_path, timeout=timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/fork of a closed, still-listed session did not succeed: {entry.text!r}"
        )
        forked_id = msg["result"].get("sessionId")
        assert isinstance(forked_id, str) and forked_id and forked_id != source_id, (
            f"session/fork must return a new sessionId distinct from the source {source_id!r}, "
            f"got {forked_id!r}"
        )


@pytest.mark.requirement("ACP-FORK-205")
@pytest.mark.capability("capabilities.session.fork")
async def test_fork_carries_the_config_options_session_new_carried(agent_launch, tmp_path):
    """ACP-FORK-205. Forks on the connection that created the source, so `session/new`'s own
    response is the evidence the session has options. Only presence and non-emptiness are
    judged. `availableCommands` is not: a fork's commands are the new session's own
    (`session-setup.mdx:140`). A fork that errors SKIPs here; `ACP-FORK-201`/`202` judge that."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        created = await new_session_result(agent, tmp_path, timeout=timeout)
        if not (isinstance(created.get("configOptions"), list) and created["configOptions"]):
            pytest.skip("session/new carried no configOptions")
        entry = await _fork_session(agent, created["sessionId"], tmp_path, timeout=timeout)
        msg = entry.parsed
        if not (isinstance(msg, dict) and isinstance(msg.get("result"), dict)):
            pytest.skip(f"session/fork of the just-created session did not succeed: {entry.text!r}")
        options = msg["result"].get("configOptions")
        assert isinstance(options, list) and options, (
            f"session/new carried configOptions but session/fork's result omits or empties "
            f"them: {entry.text!r}"
        )


# --- systemPrompt (ACP-SYSPROMPT-201/202, 002/003) ---


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


# ACP-SYSPROMPT-002/003 deliberately send what a client MUST NOT (an unadvertised mode, a
# non-text block): the spec defines the agent's answer to exactly those inputs, so they are
# legitimate probes (session-setup.mdx:474,477,481). For `session/new`, "MUST NOT create the
# session" is only observable as the error itself; for `session/resume` the session already
# exists, so the tests also check that it was not resumed: a `session/prompt` on that id must
# not succeed.

_UNSUPPORTED_MODE_PROMPT = {
    "mode": "_tck_unsupported",
    "content": [{"type": "text", "text": "You are being exercised by the ACP TCK."}],
}


def _non_text_content_prompt(cwd: Path) -> dict[str, Any]:
    return {
        "mode": "append",
        "content": [{"type": "resource_link", "uri": (cwd / "rules.md").as_uri(), "name": "rules.md"}],
    }


async def _assert_prompt_not_accepted(agent, session_id: str, what: str, *, timeout: float) -> None:
    """A refused session must not accept turns: an error to `session/prompt` is fine."""
    turn = await run_prompt(agent, session_id, [{"type": "text", "text": "hello"}], timeout=timeout)
    reply = turn.response_entry.parsed
    assert not (isinstance(reply, dict) and "result" in reply), (
        f"{what} returned an error, but the session was set up anyway: session/prompt on "
        f"{session_id!r} succeeded: {turn.response_entry.text!r}"
    )


async def _assert_new_session_refused(
    agent_launch, tmp_path, record_property, *, system_prompt, what: str, kind: str
) -> None:
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "systemPrompt": system_prompt}
        )
        entry = await agent.wait_for_response(req_id, timeout=timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("error"), dict), (
            f"session/new with {what} must return an error, got: {entry.text!r}"
        )
        record_property(f"acp_tck_sysprompt_{kind}_new_error_code", msg["error"].get("code"))
        # An error carries no session; if the agent returned an id anyway, it must not be live.
        result = msg.get("result")
        session_id = result.get("sessionId") if isinstance(result, dict) else None
        if isinstance(session_id, str) and session_id:
            await _assert_prompt_not_accepted(
                agent, session_id, f"session/new with {what}", timeout=timeout
            )


async def _assert_resume_refused(
    agent_launch, tmp_path, record_property, *, system_prompt, what: str, kind: str
) -> None:
    """Create a session on one connection, then resume it on a fresh one with a `systemPrompt`
    the agent cannot apply (session-setup.mdx:481). The reply must be an error (its code is
    recorded, not asserted: `-32602` is only RECOMMENDED), and a `session/prompt` on that id must
    then not succeed.

    A control step comes first, on its own connection that is closed before the probe's: the
    same resume without a `systemPrompt` must succeed. An agent that cannot restore a session
    across connections would otherwise refuse the probe for the wrong reason (`-32002`) and pass
    vacuously, so a failed control SKIPs."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)
    async with connected_agent(agent_launch) as agent:
        control, _updates = await resume_session(agent, session_id, tmp_path, timeout=timeout)
        skip_if_auth_gated(control)
        control_msg = control.parsed
        if not (isinstance(control_msg, dict) and "result" in control_msg):
            pytest.skip(
                "cannot judge: the agent did not resume the session without a systemPrompt "
                f"either: {control.text!r}"
            )
    async with connected_agent(agent_launch) as agent:
        entry, _updates = await resume_session(
            agent, session_id, tmp_path, system_prompt=system_prompt, timeout=timeout
        )
        skip_if_auth_gated(entry)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("error"), dict), (
            f"session/resume with {what} must return an error, got: {entry.text!r}"
        )
        record_property(f"acp_tck_sysprompt_{kind}_resume_error_code", msg["error"].get("code"))
        await _assert_prompt_not_accepted(
            agent, session_id, f"session/resume with {what}", timeout=timeout
        )


@pytest.mark.requirement("ACP-SYSPROMPT-002")
@pytest.mark.capability("capabilities.session.systemPrompt")
async def test_new_session_with_unsupported_system_prompt_mode_errors(
    agent_launch, tmp_path, record_property
):
    """ACP-SYSPROMPT-002. Uses a `_`-prefixed mode, which is reserved for implementation-specific
    use, so no agent can legitimately claim to support the TCK's. Breaks the client rule to use
    only an advertised mode on purpose: the spec defines the agent's answer."""
    await _assert_new_session_refused(
        agent_launch,
        tmp_path,
        record_property,
        system_prompt=_UNSUPPORTED_MODE_PROMPT,
        what="an unsupported systemPrompt mode",
        kind="mode",
    )


@pytest.mark.requirement("ACP-SYSPROMPT-002")
@pytest.mark.capability("capabilities.session.systemPrompt")
async def test_resume_with_unsupported_system_prompt_mode_errors(
    agent_launch, tmp_path, record_property
):
    """ACP-SYSPROMPT-002 for `session/resume`. `session/resume` is baseline once
    `capabilities.session` is advertised, which `systemPrompt` implies. Breaks the client rule
    to use only an advertised mode on purpose, as for `session/new`."""
    await _assert_resume_refused(
        agent_launch,
        tmp_path,
        record_property,
        system_prompt=_UNSUPPORTED_MODE_PROMPT,
        what="an unsupported systemPrompt mode",
        kind="mode",
    )


@pytest.mark.requirement("ACP-SYSPROMPT-003")
@pytest.mark.capability("capabilities.session.systemPrompt")
async def test_new_session_with_non_text_system_prompt_content_errors(
    agent_launch, tmp_path, record_property
):
    """ACP-SYSPROMPT-003. Breaks the client rule to send only text blocks on purpose: the spec
    defines the agent's answer."""
    await _assert_new_session_refused(
        agent_launch,
        tmp_path,
        record_property,
        system_prompt=_non_text_content_prompt(tmp_path),
        what="a non-text systemPrompt content block",
        kind="content",
    )


@pytest.mark.requirement("ACP-SYSPROMPT-003")
@pytest.mark.capability("capabilities.session.systemPrompt")
async def test_resume_with_non_text_system_prompt_content_errors(
    agent_launch, tmp_path, record_property
):
    """ACP-SYSPROMPT-003 for `session/resume`. Breaks the client rule to send only text blocks on
    purpose, as for `session/new`."""
    await _assert_resume_refused(
        agent_launch,
        tmp_path,
        record_property,
        system_prompt=_non_text_content_prompt(tmp_path),
        what="a non-text systemPrompt content block",
        kind="content",
    )
