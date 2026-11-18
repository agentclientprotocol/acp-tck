"""Client-capability negative tests: ACP-CLIENTCAP-003 (elicitation MUST NOT be requested in an
unadvertised mode), ACP-CLIENTCAP-202 (every agent -> client method seen during a turn is a
defined v2 method or `_`-prefixed) -- v2's collapse of v1's `ACP-CLIENTCAP-001/002`, since v2
removed `fs/*`/`terminal/*` entirely, so calling them just FAILs as undefined methods -- and the
two client-gated `session/update`/setup content rules, ACP-CLIENTCAP-008 (no
`prompt_suggestions_update` without `session.promptSuggestions`) and ACP-CLIENTCAP-203 (no `skill`
command entry without `session.commands.skill`).

All rows are `Tier.CAPABILITY`/`capabilities.session` per the session-baseline tiering rule
(see `tck.v2.requirements`), even though the underlying rules are unconditional MUSTs. The mock
client advertises `capabilities: {}` (no elicitation mode) for every turn here. The two gated-content
rows also judge connections that advertise a client-capability object without the gating field
(`promptSuggestions: null`, `session: {}`; `commands.skill: null`, `commands: {}`): omitting a field
and setting it to `null` both mean "not advertised", and an empty parent object advertises nothing.
Each connection runs a `session/new`, a prompt turn and a quiet period, and the whole transcript is
scanned: these updates may arrive at any time, not only inside the turn.
"""

from __future__ import annotations

import pytest

from tck.common.harness import Direction
from tck.v2.protocol import CLIENT_METHODS, PROTOCOL_METHODS

from ._helpers import (
    connected_agent,
    drain_quiet,
    iter_messages,
    new_session,
    new_session_result,
    quiet_period,
    run_prompt,
)

_PROMPT_TEXT = "hi"

_KNOWN_CLIENT_SIDE_METHODS = CLIENT_METHODS | PROTOCOL_METHODS


async def _agent_to_client_methods_seen(agent_launch, tmp_path) -> list[str | None]:
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
    return [
        entry.parsed.get("method")
        for entry in turn.client_requests_seen
        if isinstance(entry.parsed, dict)
    ]


@pytest.mark.requirement("ACP-CLIENTCAP-003")
@pytest.mark.capability("capabilities.session")
async def test_no_unadvertised_elicitation_call(agent_launch, tmp_path):
    """ACP-CLIENTCAP-003 (`elicitation.mdx:56`: agents MUST NOT request an elicitation mode the
    client has not advertised). PASS is vacuous for an agent that never uses elicitation at
    all."""
    methods_seen = await _agent_to_client_methods_seen(agent_launch, tmp_path)
    elicitation_calls = [m for m in methods_seen if m == "elicitation/create"]
    assert not elicitation_calls, (
        f"ACP-CLIENTCAP-003: elicitation/create called without an elicitation mode advertised: "
        f"{elicitation_calls!r}"
    )


@pytest.mark.requirement("ACP-CLIENTCAP-202")
@pytest.mark.capability("capabilities.session")
async def test_no_undefined_client_methods(agent_launch, tmp_path):
    """ACP-CLIENTCAP-202. Every agent -> client request/notification method observed during a
    prompt turn is one of v2's defined client-side methods (`CLIENT_METHODS`) or a
    bidirectional protocol-level method (`PROTOCOL_METHODS`, e.g. `$/cancel_request`), or begins
    with `_` (custom extension methods, Req 42)."""
    methods_seen = await _agent_to_client_methods_seen(agent_launch, tmp_path)
    undefined = [
        m
        for m in methods_seen
        if isinstance(m, str) and m not in _KNOWN_CLIENT_SIDE_METHODS and not m.startswith("_")
    ]
    assert not undefined, (
        f"ACP-CLIENTCAP-202: undefined agent -> client method(s) observed: {undefined!r}"
    )


async def _update_kinds_and_commands(
    agent_launch, tmp_path, capabilities_variants: list[dict]
) -> tuple[list[str], list[dict]]:
    """Run a `session/new`, a prompt turn and a quiet period once per `capabilities` variant, and
    return the `sessionUpdate` kind of every `session/update` the agent sent, plus every entry of
    every command list it sent (a setup result's `availableCommands` or an
    `available_commands_update`), over all the connections."""
    kinds: list[str] = []
    commands: list[dict] = []
    for capabilities in capabilities_variants:
        async with connected_agent(agent_launch, capabilities=capabilities) as agent:
            timeout = agent_launch.default_timeout
            created = await new_session_result(agent, tmp_path, timeout=timeout)
            await run_prompt(
                agent,
                created["sessionId"],
                [{"type": "text", "text": _PROMPT_TEXT}],
                timeout=timeout,
            )
            await drain_quiet(agent, quiet_period(timeout))
        for entry in agent.transcript:
            if entry.direction is not Direction.RECEIVED:
                continue
            for message in iter_messages(entry):
                params = message.get("params")
                update = params.get("update") if isinstance(params, dict) else None
                if message.get("method") == "session/update" and isinstance(update, dict):
                    kinds.append(str(update.get("sessionUpdate")))
                    listed = update.get("availableCommands")
                elif "method" not in message and isinstance(message.get("result"), dict):
                    listed = message["result"].get("availableCommands")
                else:
                    continue
                if isinstance(listed, list):
                    commands.extend(c for c in listed if isinstance(c, dict))
    return kinds, commands


@pytest.mark.requirement("ACP-CLIENTCAP-008")
@pytest.mark.capability("capabilities.session")
async def test_no_prompt_suggestions_without_client_capability(agent_launch, tmp_path):
    """ACP-CLIENTCAP-008. See module docstring. What an agent sends once
    `session.promptSuggestions` *is* advertised is judged by `test_prompt_suggestions.py`."""
    kinds, _ = await _update_kinds_and_commands(
        agent_launch,
        tmp_path,
        [{}, {"session": {"promptSuggestions": None}}, {"session": {}}],
    )
    assert "prompt_suggestions_update" not in kinds, (
        "ACP-CLIENTCAP-008: prompt_suggestions_update sent without "
        "capabilities.session.promptSuggestions advertised"
    )


@pytest.mark.requirement("ACP-CLIENTCAP-203")
@pytest.mark.capability("capabilities.session")
async def test_no_skill_command_entries_without_client_capability(agent_launch, tmp_path):
    """ACP-CLIENTCAP-203. See module docstring. Reads every command list the agent sends: a
    `session/new` (or any other) result's `availableCommands` and each `available_commands_update`.
    What an agent sends once `session.commands.skill` *is* advertised is a later row's."""
    _, commands = await _update_kinds_and_commands(
        agent_launch,
        tmp_path,
        [{}, {"session": {"commands": {"skill": None}}}, {"session": {"commands": {}}}],
    )
    skills = [command for command in commands if command.get("type") == "skill"]
    assert not skills, (
        f"ACP-CLIENTCAP-203: skill entries {skills!r} sent without "
        "capabilities.session.commands.skill advertised"
    )
