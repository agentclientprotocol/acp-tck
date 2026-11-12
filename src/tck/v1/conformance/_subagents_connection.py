"""The one connection that advertises `clientCapabilities.subagents`, shared by `test_subagents.py`
(every `ACP-SUBAGENT-*` row) and `test_client_capabilities.py` (`ACP-CLIENTCAP-001`..`003` also
judge what an agent sends on it).

`subagents: {}` and nothing else, `session/new`, one prompt turn, a quiet drain, `session/load` of
that session when `loadSession` is advertised (replay is part of what the agent sends) and a
second quiet period (child traffic may trail the turn). It is made once per run and every row
judges the same traffic, so an agent whose turns vary is judged on one turn by every row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction, TranscriptEntry
from tck.common.plugin import capability_is_supported, register_active_process

from ._helpers import connected_agent, new_session, quiet_period, run_prompt, skip_if_version_mismatch

_PROMPT_TEXT = "Summarize what you can help me with in this project."

_CONNECTION_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one connection, in `config.stash`: `agent`, `transcript`, `session_id` and `replay`
once it completed, or `error` (the exception it ended with) and the `transcript` read until then,
so every row sees the same outcome."""


@dataclass(frozen=True)
class SubagentsConnection:
    transcript: list[TranscriptEntry]
    session_id: str
    replay: tuple[int, int] | None
    """The `[start, end)` transcript range of the `session/load` exchange, `None` when none was
    sent. `end` is just after the response, or where the wait for it stopped (a load that never
    answers or an agent that exited): a failed load is `ACP-LOAD-001`'s finding, and only the
    traffic seen is judged here."""


async def _drain(agent, seconds: float) -> None:
    try:
        await agent.wait_for_message(lambda _entry: False, timeout=seconds)
    except (AgentTimeout, AgentExited):
        pass


async def subagents_connection(
    request: pytest.FixtureRequest, agent_launch, agent_initialize_result, tmp_path
) -> SubagentsConnection:
    """The connection described in the module docstring.

    Made by the first test that asks and reused by the rest. A SKIP or error that ended the
    connection is re-raised for each row. Each test registers the agent process, so a FAIL
    attaches its transcript. An agent that did not negotiate v1 SKIPs (`VERSION-MISMATCH:`): its
    subagent shapes are not v1's. The turn before `session/load` is drained first, so child
    traffic that trails it is not read as part of the load exchange."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    cache = request.config.stash.setdefault(_CONNECTION_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "agent" not in cache:
        try:
            async with connected_agent(
                agent_launch, client_capabilities={"subagents": {}}
            ) as agent:
                try:
                    await _run(agent, agent_launch, init_result, tmp_path, cache)
                except BaseException:
                    cache["transcript"] = list(agent.transcript)
                    raise
        except BaseException as exc:
            cache["error"] = exc
            raise
    register_active_process(cache["agent"])
    return SubagentsConnection(list(cache["transcript"]), cache["session_id"], cache["replay"])


async def _run(agent, agent_launch, init_result, tmp_path, cache: dict[str, Any]) -> None:
    timeout = agent_launch.default_timeout
    session_id = await new_session(agent, tmp_path, timeout=timeout)
    await run_prompt(agent, session_id, [{"type": "text", "text": _PROMPT_TEXT}], timeout=timeout)
    replay = None
    if init_result is not None and capability_is_supported(
        init_result, "agentCapabilities.loadSession", boolean=True
    ):
        await _drain(agent, quiet_period(timeout))
        load_id = await agent.send_request(
            "session/load", {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []}
        )
        start = len(agent.transcript) - 1
        try:
            await agent.wait_for_response(load_id, timeout=timeout)
        except (AgentTimeout, AgentExited):
            pass  # ACP-LOAD-001's finding; judge the traffic seen
        replay = (start, len(agent.transcript))
    await _drain(agent, quiet_period(timeout))
    cache.update(
        agent=agent, transcript=list(agent.transcript), session_id=session_id, replay=replay
    )


async def subagents_connection_received(
    request: pytest.FixtureRequest, agent_launch, agent_initialize_result, tmp_path
) -> list[TranscriptEntry]:
    """Every line the agent sent on the subagents connection, for the rows (`ACP-CLIENTCAP-*`)
    that judge it only for what the agent sent and not for the subagent rules. A connection that
    did not complete (a skipped version mismatch, a failed turn) is the subagent rows' to
    report: the lines read until then still count, and an unusable connection counts none."""
    try:
        connection = await subagents_connection(request, agent_launch, agent_initialize_result, tmp_path)
        transcript = connection.transcript
    except (Exception, pytest.skip.Exception):
        cache = request.config.stash.get(_CONNECTION_KEY, {})
        transcript = cache.get("transcript", [])
    return [entry for entry in transcript if entry.direction is Direction.RECEIVED]
