"""Subagent announcement ordering and `session` content references (ACP-SUBAGENT-001/002).

There is no `initialize` marker for subagents in v2 -- support is baseline and *inferred* from the
agent's traffic, so `Requirement.capability` is the documentation-only `"inferred:subagents"`
string, the tests carry no `@pytest.mark.capability(...)` marker and SKIP themselves when the
agent shows no use of the feature (001: no child session appears; 002: no `session` tool-call
content item appears). Same encoding as `test_slash_commands.py`, hence the same `v2_only_agent`
connection.

The connection is one `session/new`, one prompt turn and a quiet period after it (child traffic
may trail the turn), judged in wire order over everything the agent sent. `session/resume`
replay is not part of it: `ACP-RESUME-209` judges that window, so one defect never FAILs both.
Both tests judge the same connection, but a `session` content reference is not child traffic, so
an unknown reference FAILs only 002.
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
