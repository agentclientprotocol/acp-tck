"""Agent-plan conformance: ACP-PLAN-001/002.

Both rules only apply once the client advertised `clientCapabilities.plan`, which every other
connection in this suite leaves out (ACP-CLIENTCAP-006 depends on that). So each test opens its
own connection with `plan: {}`, runs one plan-flavoured prompt turn, waits a quiet period, and
scans every `session/update` the agent sent. Plans are unstable and optional (`agent-plan.mdx`
only says the agent SHOULD plan), so an agent that sends none passes vacuously.
"""

from __future__ import annotations

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction

from ._helpers import (
    connected_agent,
    is_absolute_uri,
    new_session,
    quiet_period,
    run_prompt,
    session_update_kind,
    skip_if_version_mismatch,
)

_PLAN_PROMPT_TEXT = "Make a step-by-step plan for refactoring this project, then start on it."


async def _updates_with_plan_capability(agent_launch, agent_initialize_result, tmp_path) -> list[dict]:
    """Every `session/update` `update` object the agent sent on a connection advertising
    `plan: {}`, over `session/new`, one prompt turn and a quiet period."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    async with connected_agent(agent_launch, client_capabilities={"plan": {}}) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PLAN_PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
        try:
            await agent.wait_for_message(
                lambda _entry: False, timeout=quiet_period(agent_launch.default_timeout)
            )
        except (AgentTimeout, AgentExited):
            pass
    return [
        entry.parsed["params"]["update"]
        for entry in agent.transcript
        if entry.direction is Direction.RECEIVED and session_update_kind(entry) is not None
    ]


@pytest.mark.requirement("ACP-PLAN-001")
async def test_plan_file_uri_is_absolute(agent_launch, agent_initialize_result, tmp_path):
    """ACP-PLAN-001. "Absolute" is the TCK's own reading (see `is_absolute_uri`); the spec does
    not define it."""
    updates = await _updates_with_plan_capability(agent_launch, agent_initialize_result, tmp_path)
    relative = []
    for update in updates:
        plan = update.get("plan")
        if (
            update.get("sessionUpdate") == "plan_update"
            and isinstance(plan, dict)
            and plan.get("type") == "file"
            and not is_absolute_uri(plan.get("uri"))
        ):
            relative.append(plan.get("uri"))
    assert not relative, f"ACP-PLAN-001: plan_update file uri is not absolute: {relative!r}"


@pytest.mark.requirement("ACP-PLAN-002")
async def test_plan_update_used_when_plan_capability_advertised(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-PLAN-002. The failure may only mean the agent does not implement the unstable plan
    operations."""
    updates = await _updates_with_plan_capability(agent_launch, agent_initialize_result, tmp_path)
    assert not any(update.get("sessionUpdate") == "plan" for update in updates), (
        "ACP-PLAN-002: baseline `plan` update sent although clientCapabilities.plan was "
        "advertised (agent may not implement the unstable plan operations)"
    )
