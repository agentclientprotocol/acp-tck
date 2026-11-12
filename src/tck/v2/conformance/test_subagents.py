"""Subagent announcement ordering (ACP-SUBAGENT-001).

There is no `initialize` marker for subagents in v2 -- support is baseline and *inferred* from the
agent's traffic, so `Requirement.capability` is the documentation-only `"inferred:subagents"`
string, the test carries no `@pytest.mark.capability(...)` marker and SKIPs itself when no child
session appears (same encoding as `test_slash_commands.py`, hence the same `v2_only_agent`
connection).

The connection is one `session/new`, one prompt turn and a quiet period after it (child traffic
may trail the turn), judged in wire order over everything the agent sent. `session/resume`
replay is not part of it: `ACP-RESUME-209` judges that window, so one defect never FAILs both.
"""

from __future__ import annotations

import pytest

from ._helpers import (
    child_session_traffic,
    drain_quiet,
    new_session,
    quiet_period,
    run_prompt,
    v2_only_agent,
)

_PROMPT_TEXT = "hi"


@pytest.mark.requirement("ACP-SUBAGENT-001")
async def test_child_session_traffic_follows_its_announcement(agent_launch, tmp_path):
    """ACP-SUBAGENT-001. Over the whole connection -- turn and quiet period alike -- no
    `session/update`, agent -> client request or `session_message` participant names a session
    ID the client did not create before a `subagent_update` on a known session announced it.
    SKIPs when the agent sends no such ID at all."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
        await drain_quiet(agent, quiet_period(agent_launch.default_timeout))
        children, problems = child_session_traffic(agent.transcript, {session_id})
        if not children:
            pytest.skip("the agent exposed no subagent: no session ID the client did not create")
        assert not problems, "; ".join(problems[:3]) + (
            f" (and {len(problems) - 3} more)" if len(problems) > 3 else ""
        )
