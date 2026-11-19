"""Agent-plan conformance: ACP-PLAN-002/003/004.

All three rules only apply once the client advertised `clientCapabilities.plan`, which every other
connection in this suite leaves out (ACP-CLIENTCAP-006 depends on that). So each test opens its
own connection with `plan: {}`, runs one plan-flavoured prompt turn, waits a quiet period, and
scans every `session/update` the agent sent. Plans are unstable and optional (`agent-plan.mdx`
only says the agent SHOULD plan), so an agent that sends none passes vacuously. A turn that
outlasts `--timeout` is cancelled and judged on the updates seen so far: a slow turn is not a
plan defect.
"""

from __future__ import annotations

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.v1.validation import validate_against_def

from ._helpers import (
    connected_agent,
    is_absolute_path,
    new_session,
    quiet_period,
    run_prompt,
    session_update_kind,
    skip_if_version_mismatch,
)

_PLAN_PROMPT_TEXT = "Make a step-by-step plan for refactoring this project. Do not start on it yet."


async def _updates_with_plan_capability(agent_launch, agent_initialize_result, tmp_path) -> list[dict]:
    """Every `session/update` `update` object the agent sent on a connection advertising
    `plan: {}`, over `session/new`, one prompt turn and a quiet period."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    async with connected_agent(agent_launch, client_capabilities={"plan": {}}) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        try:
            await run_prompt(
                agent,
                session_id,
                [{"type": "text", "text": _PLAN_PROMPT_TEXT}],
                timeout=agent_launch.default_timeout,
            )
        except AgentTimeout:
            await agent.send_notification("session/cancel", {"sessionId": session_id})
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


@pytest.mark.requirement("ACP-PLAN-003")
async def test_markdown_plan_path_is_an_absolute_native_path(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-PLAN-003. Only a string `path` is judged: `null` and omission mean no file, and a
    non-string `path` is `ACP-PLAN-004`'s."""
    updates = await _updates_with_plan_capability(agent_launch, agent_initialize_result, tmp_path)
    not_absolute = []
    for update in updates:
        plan = update.get("plan")
        if (
            update.get("sessionUpdate") == "plan_update"
            and isinstance(plan, dict)
            and plan.get("type") == "markdown"
            and isinstance(plan.get("path"), str)
            and not is_absolute_path(plan["path"])
        ):
            not_absolute.append(plan["path"])
    assert not not_absolute, (
        f"ACP-PLAN-003: markdown plan path is not an absolute native path: {not_absolute!r} "
        "(a relative path or a URI such as `file:///...` is not one)"
    )


@pytest.mark.requirement("ACP-PLAN-004")
async def test_plan_updates_validate_against_the_schema(agent_launch, agent_initialize_result, tmp_path):
    """ACP-PLAN-004. Judges the whole `update` of every `plan_update` and `plan_removed`; the
    baseline `plan` update is not this row's."""
    updates = await _updates_with_plan_capability(agent_launch, agent_initialize_result, tmp_path)
    problems = [
        f"{update!r}: {issue.message}"
        for update in updates
        if update.get("sessionUpdate") in ("plan_update", "plan_removed")
        for issue in validate_against_def("SessionUpdate", update)
    ]
    assert not problems, "ACP-PLAN-004: plan update does not match the schema: " + "; ".join(problems)
