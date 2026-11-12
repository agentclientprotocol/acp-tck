"""Subagent announcement ordering, `session` content references and association integrity
(ACP-SUBAGENT-001..009).

There is no `initialize` marker for subagents in v2 -- support is baseline and *inferred* from the
agent's traffic, so `Requirement.capability` is the documentation-only `"inferred:subagents"`
string, the tests carry no `@pytest.mark.capability(...)` marker and SKIP themselves when the
agent shows no use of the feature (001: no child session appears; 002: no `session` tool-call
content item appears). Same encoding as `test_slash_commands.py`, hence the same `v2_only_agent`
connection.

The connection is one `session/new`, one prompt turn and a quiet period after it (child traffic
may trail the turn), judged in wire order over everything the agent sent. `session/resume`
replay is not part of it: `ACP-RESUME-209` judges that window, so one defect never FAILs both.
All tests judge the same connection, but a `session` content reference is not child traffic, so
an unknown reference FAILs only 002. 003..005 (self-parent, a client session announced as a child,
a reparented child) are disjoint by construction in `subagent_updates`, as is 006 (absolute
`cwd`/`additionalDirectories`), so one defect FAILs one row; each SKIPs when no `subagent_update`
appears (006: none carries a directory field). 007..009 judge `session_message` participants
and view links, SKIP when none appears, and are disjoint by construction in `session_messages`
(007 equal participants, 008 an outer session that is neither, 009 conflicting view references).
"""

from __future__ import annotations

import pytest

from tck.common.harness import TranscriptEntry

from ._helpers import (
    child_session_traffic,
    drain_quiet,
    new_session,
    quiet_period,
    run_prompt,
    session_content_references,
    session_messages,
    subagent_updates,
    v2_only_agent,
)

_PROMPT_TEXT = "hi"


async def _connection_transcript(agent_launch, tmp_path) -> tuple[list[TranscriptEntry], str]:
    """One `session/new`, one prompt turn and a quiet period; `(transcript, session_id)`."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
        await drain_quiet(agent, quiet_period(agent_launch.default_timeout))
        return list(agent.transcript), session_id


def _summary(problems: list[str]) -> str:
    return "; ".join(problems[:3]) + (
        f" (and {len(problems) - 3} more)" if len(problems) > 3 else ""
    )


@pytest.mark.requirement("ACP-SUBAGENT-001")
async def test_child_session_traffic_follows_its_announcement(agent_launch, tmp_path):
    """ACP-SUBAGENT-001. Over the whole connection -- turn and quiet period alike -- no
    `session/update`, agent -> client request or `session_message` participant names a session
    ID the client did not create before a `subagent_update` on a known session announced it.
    SKIPs when the agent sends no such ID at all."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    children, problems = child_session_traffic(transcript, {session_id})
    if not children:
        pytest.skip("the agent exposed no subagent: no session ID the client did not create")
    assert not problems, _summary(problems)


@pytest.mark.requirement("ACP-SUBAGENT-002")
async def test_session_content_names_a_known_session(agent_launch, tmp_path):
    """ACP-SUBAGENT-002. Every `session` tool-call content item names a session the client
    created or one an earlier `subagent_update` on a known session announced. SKIPs when no
    `session` content item appears."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    references, problems = session_content_references(transcript, {session_id})
    if not references:
        pytest.skip("the agent emitted no `session` tool-call content item")
    assert not problems, _summary(problems)


@pytest.mark.requirement("ACP-SUBAGENT-003")
async def test_subagent_update_never_makes_a_session_its_own_parent(agent_launch, tmp_path):
    """ACP-SUBAGENT-003. No `subagent_update` has the same `sessionId` as the session it is sent
    on. SKIPs when the agent sends no `subagent_update`."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.self_parented, _summary(found.self_parented)


@pytest.mark.requirement("ACP-SUBAGENT-004")
async def test_subagent_update_never_announces_a_client_created_session(agent_launch, tmp_path):
    """ACP-SUBAGENT-004. No `subagent_update` announces, as a child of another session, a session
    the client created with `session/new`. SKIPs when the agent sends no `subagent_update`."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.client_sessions_announced, _summary(found.client_sessions_announced)


@pytest.mark.requirement("ACP-SUBAGENT-005")
async def test_announced_child_keeps_its_one_parent(agent_launch, tmp_path):
    """ACP-SUBAGENT-005. A child announced on a known session is never announced again on a
    different session, which would reparent it (or close a cycle). SKIPs when the agent sends no
    `subagent_update`."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.updates:
        pytest.skip("the agent sent no `subagent_update`")
    assert not found.reparented, _summary(found.reparented)


@pytest.mark.requirement("ACP-SUBAGENT-006")
async def test_subagent_update_directories_are_absolute(agent_launch, tmp_path):
    """ACP-SUBAGENT-006. Every `subagent_update.cwd` and `additionalDirectories` entry is an
    absolute path. SKIPs when no `subagent_update` reports either."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    found = subagent_updates(transcript, {session_id})
    if not found.reported_directories:
        pytest.skip("no `subagent_update` reported `cwd` or `additionalDirectories`")
    assert not found.relative_paths, _summary(found.relative_paths)


@pytest.mark.requirement("ACP-SUBAGENT-007")
async def test_session_message_participants_differ(agent_launch, tmp_path):
    """ACP-SUBAGENT-007. When both `senderSessionId` and `recipientSessionId` of a
    `session_message` are known, they identify different sessions. SKIPs when the agent sends no
    `session_message`."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    found = session_messages(transcript, {session_id})
    if not found.count:
        pytest.skip("the agent sent no `session_message`")
    assert not found.same_participants, _summary(found.same_participants)


@pytest.mark.requirement("ACP-SUBAGENT-008")
async def test_session_message_outer_session_is_a_participant(agent_launch, tmp_path):
    """ACP-SUBAGENT-008. When both participants of a `session_message` are known and differ,
    `params.sessionId` is one of them. SKIPs when the agent sends no `session_message`."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    found = session_messages(transcript, {session_id})
    if not found.count:
        pytest.skip("the agent sent no `session_message`")
    assert not found.foreign_outer, _summary(found.foreign_outer)


@pytest.mark.requirement("ACP-SUBAGENT-009")
async def test_session_message_views_reference_each_other(agent_launch, tmp_path):
    """ACP-SUBAGENT-009. When both views of one message carry `senderMessageId` /
    `recipientMessageId`, each names the other's `messageId`. SKIPs when the agent sends no
    `session_message`."""
    transcript, session_id = await _connection_transcript(agent_launch, tmp_path)
    found = session_messages(transcript, {session_id})
    if not found.count:
        pytest.skip("the agent sent no `session_message`")
    assert not found.unlinked_views, _summary(found.unlinked_views)
