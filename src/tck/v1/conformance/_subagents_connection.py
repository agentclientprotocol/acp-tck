"""The one connection that advertises `clientCapabilities.subagents`, shared by `test_subagents.py`
(every `ACP-SUBAGENT-*` row) and `test_client_capabilities.py` (`ACP-CLIENTCAP-001`..`003` also
judge what an agent sends on it).

`subagents: {}` and nothing else, `session/new`, one prompt turn (`--subagent-prompt`, else a short
built-in text), a quiet drain, `session/load` of that session when `loadSession` is advertised
(replay is part of what the agent sends) and a second quiet period (child traffic may trail the turn). It is made once per run and every row
judges the same traffic, so an agent whose turns vary is judged on one turn by every row.

The transcript the rows judge is snapshotted before a last, probe phase (`ChildProbes`): when the
turn announced a child, a `session/list` (paginated, bounded) and the Client-initiated requests the
docs say an Agent rejects for a child (`session/load`, `session/close`, `session/delete`, each only
when advertised). The probes run after the snapshot, so their traffic never reaches another row's
evidence. They deliberately break a Client MUST NOT, because the docs define the Agent's answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction, TranscriptEntry
from tck.common.plugin import capability_is_supported, register_active_process

from ._helpers import (
    announced_children,
    connected_agent,
    new_session,
    quiet_period,
    run_prompt,
    skip_if_version_mismatch,
)

_DEFAULT_PROMPT_TEXT = "Summarize what you can help me with in this project."

_CONNECTION_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one connection, in `config.stash`: `agent`, `transcript`, `session_id` and `replay`
once it completed, or `error` (the exception it ended with) and the `transcript` read until then,
so every row sees the same outcome."""


_MAX_CHILDREN_PROBED = 2
"""How many announced children (first announced first) receive the mutating probes."""
_MAX_LIST_PAGES = 10
"""How many `session/list` pages are followed through `nextCursor`."""


@dataclass(frozen=True)
class ChildProbe:
    """One mutating request naming an announced child, and the reply: the JSON-RPC response
    object, or `None` when none arrived (the agent exited or did not answer in time)."""

    method: str
    child: str
    response: dict[str, Any] | None

    @property
    def error_code(self) -> Any:
        error = self.response.get("error") if self.response else None
        return error.get("code") if isinstance(error, dict) else None

    @property
    def errored(self) -> bool:
        return bool(self.response) and isinstance(self.response.get("error"), dict)

    @property
    def succeeded(self) -> bool:
        return bool(self.response) and "result" in self.response and "error" not in self.response


@dataclass(frozen=True)
class ChildProbes:
    """What the probe phase learned. `children` is every announced child; `methods` the probe
    methods the agent advertised; `probes` the requests sent for the first few children (none
    when the agent stopped answering during `session/list`); `listed` the session IDs
    `session/list` returned over the pages followed, `None` when it was not sent or its first
    page was not a list result."""

    children: tuple[str, ...] = ()
    probes: tuple[ChildProbe, ...] = ()
    listed: frozenset[str] | None = None
    methods: tuple[str, ...] = ()


@dataclass(frozen=True)
class SubagentsConnection:
    transcript: list[TranscriptEntry]
    session_id: str
    replay: tuple[int, int] | None
    """The `[start, end)` transcript range of the `session/load` exchange, `None` when none was
    sent. `end` is just after the response, or where the wait for it stopped (a load that never
    answers or an agent that exited): a failed load is `ACP-LOAD-001`'s finding, and only the
    traffic seen is judged here."""
    probes: ChildProbes = ChildProbes()
    """The probe phase's findings, made after `transcript` was read."""


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
    prompt_text = request.config.getoption("tck_subagent_prompt") or _DEFAULT_PROMPT_TEXT
    if "error" in cache:
        raise cache["error"]
    if "agent" not in cache:
        try:
            async with connected_agent(
                agent_launch, client_capabilities={"subagents": {}}
            ) as agent:
                try:
                    await _run(agent, agent_launch, init_result, tmp_path, prompt_text, cache)
                except BaseException:
                    cache["transcript"] = list(agent.transcript)
                    raise
        except BaseException as exc:
            cache["error"] = exc
            raise
    register_active_process(cache["agent"])
    return SubagentsConnection(
        list(cache["transcript"]), cache["session_id"], cache["replay"], cache["probes"]
    )


async def _run(
    agent, agent_launch, init_result, tmp_path, prompt_text: str, cache: dict[str, Any]
) -> None:
    timeout = agent_launch.default_timeout
    session_id = await new_session(agent, tmp_path, timeout=timeout)
    await run_prompt(agent, session_id, [{"type": "text", "text": prompt_text}], timeout=timeout)
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
    transcript = list(agent.transcript)
    probes = await _probe_children(agent, init_result, tmp_path, timeout, transcript, session_id)
    cache.update(
        agent=agent, transcript=transcript, session_id=session_id, replay=replay, probes=probes
    )


async def _ask(agent, method: str, params: dict[str, Any], timeout: float) -> dict[str, Any] | None:
    """Send a request and return the response object, or `None` when the agent exited, did not
    answer within `timeout` or sent a non-object reply."""
    try:
        request_id = await agent.send_request(method, params)
        entry = await agent.wait_for_response(request_id, timeout=timeout)
    except (AgentTimeout, AgentExited):
        return None
    return entry.parsed if isinstance(entry.parsed, dict) else None


async def _probe_children(
    agent, init_result, tmp_path, timeout: float, transcript: list[TranscriptEntry], session_id: str
) -> ChildProbes:
    """The probe phase described in the module docstring, over the children `transcript`
    announced. It stops asking once the agent stops answering."""
    children = announced_children(transcript, {session_id})
    if not children or init_result is None:
        return ChildProbes()

    def advertised(path: str, *, boolean: bool = False) -> bool:
        return capability_is_supported(init_result, path, boolean=boolean)

    listed: set[str] | None = None
    answering = True
    if advertised("agentCapabilities.sessionCapabilities.list"):
        cursor = None
        seen_cursors: set[str] = set()
        for _page in range(_MAX_LIST_PAGES):
            reply = await _ask(agent, "session/list", {} if cursor is None else {"cursor": cursor}, timeout)
            answering = reply is not None
            result = reply.get("result") if reply else None
            sessions = result.get("sessions") if isinstance(result, dict) else None
            if not isinstance(sessions, list):
                break
            listed = (listed or set()) | {
                item["sessionId"]
                for item in sessions
                if isinstance(item, dict) and isinstance(item.get("sessionId"), str)
            }
            cursor = result.get("nextCursor")
            if not isinstance(cursor, str) or cursor in seen_cursors:
                break
            seen_cursors.add(cursor)

    methods: list[tuple[str, dict[str, Any]]] = []
    if advertised("agentCapabilities.loadSession", boolean=True):
        methods.append(("session/load", {"cwd": str(tmp_path), "mcpServers": []}))
    if advertised("agentCapabilities.sessionCapabilities.close"):
        methods.append(("session/close", {}))
    if advertised("agentCapabilities.sessionCapabilities.delete"):
        methods.append(("session/delete", {}))
    probes: list[ChildProbe] = []
    for child in children[:_MAX_CHILDREN_PROBED]:
        for method, extra in methods:
            if not answering:
                break
            response = await _ask(agent, method, {"sessionId": child, **extra}, timeout)
            probes.append(ChildProbe(method, child, response))
            answering = response is not None
    return ChildProbes(
        tuple(children),
        tuple(probes),
        None if listed is None else frozenset(listed),
        tuple(method for method, _extra in methods),
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
