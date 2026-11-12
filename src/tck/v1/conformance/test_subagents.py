"""Subagent announcement ordering, `session` content references, association integrity, schema
validity and the SHOULDs around them (ACP-SUBAGENT-001..009, -011..015).

v1 gates subagents on the client: an agent may send `subagent_update`, `session_message`,
`session_message_chunk` and `session` tool-call content only to a client that advertised
`clientCapabilities.subagents` (`ACP-CLIENTCAP-007` judges that on the default connection, which
never advertises it). These rows judge what an agent that does expose a child sends once the
client *did* advertise it, so they run over their own connection, `_connection_transcript`:
`subagents: {}` and nothing else, `session/new`, one prompt turn, `session/load` of that session
when `loadSession` is advertised (replay is part of what the agent sends), and a quiet period
(child traffic may trail the turn). It is made once per run and every row judges the same
traffic, so an agent whose turns vary is judged on one turn by every row. The default connections
stay as they were (`subagents` is never advertised there).

There is no agent-side marker for subagents: the feature is *inferred* from the agent's traffic,
so `Requirement.capability` is the documentation-only `"inferred:subagents"` string, the tests
carry no `@pytest.mark.capability(...)` marker and SKIP themselves when the agent shows no use of
the feature (001: no child session appears; 002: no `session` tool-call content item appears;
015: no subagent message appears). A `session` content reference is not child traffic, so an
unknown reference FAILs only 002. 003..005 (self-parent, a client session announced as a child, a
reparented child) are disjoint by construction in `subagent_updates`, as is 006 (absolute
`cwd`/`additionalDirectories`), so one defect FAILs one row; each SKIPs when no `subagent_update`
appears (006: none carries a well-typed directory string; a malformed one is 015's). 007..009
judge `session_message` participants and view links and are disjoint by construction in
`session_messages`. 011..014 are ADVISORY (SHOULDs). An ADVISORY row has no `capability`, so each
SKIPs itself when the agent shows nothing to judge; 011/012 are disjoint by construction in
`child_task_reports`. v1 has no child-addressed `state_update`, so the v2-only mirroring row
(`ACP-SUBAGENT-201`) has no counterpart; a child's work state is only a parent's
`subagent_update.state`, whose shape 015 validates.

The mock client advertises neither `fs` nor `terminal` on this connection, so it answers any
such request `-32601` like on every other v1 connection.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, TranscriptEntry
from tck.common.plugin import capability_is_supported, register_active_process

from ._helpers import (
    child_config_selects,
    child_session_traffic,
    child_task_reports,
    connected_agent,
    new_session,
    quiet_period,
    run_prompt,
    session_content_references,
    session_message_streams,
    session_messages,
    skip_if_version_mismatch,
    subagent_shape_issues,
    subagent_updates,
)

_PROMPT_TEXT = "Summarize what you can help me with in this project."

_CONNECTION_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one connection, in `config.stash`: `agent`, `transcript` and `session_id` once it
completed, or `error` (the exception it ended with) so every row sees the same outcome."""


async def _connection_transcript(
    request: pytest.FixtureRequest, agent_launch, agent_initialize_result, tmp_path
) -> tuple[list[TranscriptEntry], str]:
    """`(transcript, session_id)` of one connection that advertised `subagents`: `session/new`,
    one prompt turn, `session/load` when `loadSession` is advertised, then a quiet period.

    Made by the first test that asks and reused by the rest, so a model-driven agent runs one
    turn and every row judges that same traffic. A SKIP or error that ended the connection is
    re-raised for each row. Each test registers the agent process, so a FAIL attaches its
    transcript. An agent that did not negotiate v1 SKIPs (`VERSION-MISMATCH:`): its subagent
    shapes are not v1's."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    cache = request.config.stash.setdefault(_CONNECTION_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "agent" in cache:
        register_active_process(cache["agent"])
        return list(cache["transcript"]), cache["session_id"]
    try:
        async with connected_agent(agent_launch, client_capabilities={"subagents": {}}) as agent:
            session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            await run_prompt(
                agent,
                session_id,
                [{"type": "text", "text": _PROMPT_TEXT}],
                timeout=agent_launch.default_timeout,
            )
            if init_result is not None and capability_is_supported(
                init_result, "agentCapabilities.loadSession", boolean=True
            ):
                load_id = await agent.send_request(
                    "session/load", {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []}
                )
                # A failed load is ACP-LOAD-001's finding; only the traffic seen is judged here.
                await agent.wait_for_response(load_id, timeout=agent_launch.default_timeout)
            try:
                await agent.wait_for_message(
                    lambda _entry: False, timeout=quiet_period(agent_launch.default_timeout)
                )
            except (AgentTimeout, AgentExited):
                pass
            cache.update(agent=agent, transcript=list(agent.transcript), session_id=session_id)
    except BaseException as exc:
        cache["error"] = exc
        raise
    return list(cache["transcript"]), cache["session_id"]


def _summary(problems: list[str]) -> str:
    return "; ".join(problems[:3]) + (
        f" (and {len(problems) - 3} more)" if len(problems) > 3 else ""
    )


@pytest.mark.requirement("ACP-SUBAGENT-001")
async def test_child_session_traffic_follows_its_announcement(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-001. Over the whole connection -- turn, replay and quiet period alike -- no
    `session/update`, agent -> client request (`fs/*` and `terminal/*` included) or
    `session_message` participant names a session ID the client did not create before a
    `subagent_update` on a known session announced it. SKIPs when the agent sends no such ID at
    all."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    children, problems = child_session_traffic(transcript, {session_id})
    if not children:
        pytest.skip("the agent exposed no subagent: no session ID the client did not create")
    assert not problems, _summary(problems)


@pytest.mark.requirement("ACP-SUBAGENT-002")
async def test_session_content_names_a_known_session(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-002. Every `session` tool-call content item names a session the client
    created or one an earlier `subagent_update` on a known session announced. SKIPs when no
    `session` content item appears."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    references, problems = session_content_references(transcript, {session_id})
    if not references:
        pytest.skip("the agent emitted no `session` tool-call content item")
    assert not problems, _summary(problems)


@pytest.mark.requirement("ACP-SUBAGENT-003")
async def test_subagent_update_never_makes_a_session_its_own_parent(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-003. No `subagent_update` has the same `sessionId` as the session it is sent
    on. SKIPs when the agent sends no `subagent_update`."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.self_parented, _summary(found.self_parented)


@pytest.mark.requirement("ACP-SUBAGENT-004")
async def test_subagent_update_never_announces_a_client_created_session(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-004. No `subagent_update` announces, as a child of another session, a session
    the client created with `session/new`. SKIPs when the agent sends no `subagent_update`."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.client_sessions_announced, _summary(found.client_sessions_announced)


@pytest.mark.requirement("ACP-SUBAGENT-005")
async def test_announced_child_keeps_its_one_parent(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-005. A child announced on a known session is never announced again on a
    different session, which would reparent it (or close a cycle). SKIPs when the agent sends no
    `subagent_update`."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.reparented, _summary(found.reparented)


@pytest.mark.requirement("ACP-SUBAGENT-006")
async def test_subagent_update_directories_are_absolute(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-006. Every `subagent_update.cwd` and `additionalDirectories` entry is an
    absolute path. SKIPs when no `subagent_update` reports a string for either (a value of the
    wrong type is `ACP-SUBAGENT-015`'s)."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = subagent_updates(transcript, {session_id})
    if not found.reported_directories:
        pytest.skip("no `subagent_update` reported `cwd` or `additionalDirectories`")
    assert not found.relative_paths, _summary(found.relative_paths)


@pytest.mark.requirement("ACP-SUBAGENT-007")
async def test_session_message_participants_differ(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-007. When both `senderSessionId` and `recipientSessionId` of a
    `session_message` are known, they identify different sessions. SKIPs when no
    `session_message` has both participants known."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = session_messages(transcript, {session_id})
    if not found.participants_judged:
        pytest.skip("no `session_message` had both `senderSessionId` and `recipientSessionId` known")
    assert not found.same_participants, _summary(found.same_participants)


@pytest.mark.requirement("ACP-SUBAGENT-008")
async def test_session_message_outer_session_is_a_participant(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-008. When both participants of a `session_message` are known and differ,
    `params.sessionId` is one of them. SKIPs when no `session_message` has both participants
    known."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = session_messages(transcript, {session_id})
    if not found.participants_judged:
        pytest.skip("no `session_message` had both `senderSessionId` and `recipientSessionId` known")
    assert not found.foreign_outer, _summary(found.foreign_outer)


@pytest.mark.requirement("ACP-SUBAGENT-009")
async def test_session_message_views_reference_each_other(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-009. When both views of one message carry `senderMessageId` /
    `recipientMessageId`, each names the other's `messageId`. SKIPs when no two such views are
    linked."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = session_messages(transcript, {session_id})
    if not found.links_judged:
        pytest.skip("no two linked `session_message` views both carried a reference")
    assert not found.unlinked_views, _summary(found.unlinked_views)


@pytest.mark.requirement("ACP-SUBAGENT-011")
async def test_child_task_is_not_a_user_message(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-011. An announced child has no `user_message_chunk` before its first agent
    output. SKIPs when no announced child produces agent output or has one."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = child_task_reports(transcript, {session_id})
    if not found.started and not found.user_message_tasks:
        pytest.skip("no announced child produced agent output")
    assert not found.user_message_tasks, _summary(found.user_message_tasks)


@pytest.mark.requirement("ACP-SUBAGENT-012")
async def test_child_task_is_an_incoming_session_message_before_its_output(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-012. An announced child's first agent output is preceded by an incoming
    `session_message` whose `senderSessionId` is its parent. A task reported as a user message is
    `ACP-SUBAGENT-011`'s. SKIPs when no announced child that was not told the task as a user
    message produces agent output."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = child_task_reports(transcript, {session_id})
    if not found.judged:
        pytest.skip("no announced child produced agent output without a user-message task")
    assert not found.unreported, _summary(found.unreported)


@pytest.mark.requirement("ACP-SUBAGENT-013")
async def test_session_message_participants_precede_the_first_chunk(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-013. A streamed `session_message` has a participant ID stored by its first
    chunk, unless none is ever supplied. SKIPs when no `session_message_chunk` appears."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = session_message_streams(transcript, {session_id})
    if not found.streamed:
        pytest.skip("the agent sent no `session_message_chunk`")
    assert not found.late_participants, _summary(found.late_participants)


@pytest.mark.requirement("ACP-SUBAGENT-014")
async def test_child_select_offers_only_its_current_value(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-014. A select option in a `config_option_update` for an announced child
    offers no value but the current one. SKIPs when no such select is reported."""
    transcript, session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    found = child_config_selects(transcript, {session_id})
    if not found.selects:
        pytest.skip("the agent reported no select config option for an announced child")
    assert not found.with_choices, _summary(found.with_choices)


@pytest.mark.requirement("ACP-SUBAGENT-015")
async def test_subagent_messages_validate_against_the_schema(
    request, agent_launch, agent_initialize_result, tmp_path
):
    """ACP-SUBAGENT-015. Every `subagent_update` (its `state` snapshot included),
    `session_message`, `session_message_chunk` and `session` tool-call content item validates
    against the v1 schema. SKIPs when the agent sends none."""
    transcript, _session_id = await _connection_transcript(
        request, agent_launch, agent_initialize_result, tmp_path
    )
    judged, problems = subagent_shape_issues(transcript)
    if not judged:
        pytest.skip("the agent sent no subagent message")
    assert not problems, _summary(problems)
