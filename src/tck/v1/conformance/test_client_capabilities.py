"""Client-capability negative tests: ACP-CLIENTCAP-001..007.

The mock client (`_helpers.run_prompt`) advertises `clientCapabilities: {}` during every prompt
turn in this suite -- no `fs`, no `terminal`, no elicitation mode. During *any* prompt turn the
agent MUST NOT call `fs/read_text_file`, `fs/write_text_file`, any `terminal/*` method, or
`elicitation/create` (Reqs 29, 30, 32) -- these are all client-controlled MUST NOTs, and the TCK
controls the advertisement, so they are directly observable negative tests, not something a
real client could get wrong.

Implemented as three separate tests sharing one helper -- a single test bound to all three ids
would mis-attribute a violation of one capability to all three. Each test sends its own prompt
turn and filters `PromptTurn.client_requests_seen` (every agent -> client request `run_prompt`
had to answer, replying `-32601` to anything but `session/request_permission`) by method prefix.

PASS is vacuous for an agent that never needs any client tool at all -- Reqs 29/30/32 only
forbid *calling* the unadvertised capability, they do not require an agent to try and be
refused.

ACP-CLIENTCAP-004..007 cover client-gated `session/update` kinds rather than requests (notices,
compaction, plan operations, subagent updates). These may be sent outside a prompt turn too, and
compaction also during `session/load` replay, so each test scans the whole connection's
transcript (see `_session_update_kinds_with_no_client_capabilities`), again one id per test.
"""

from __future__ import annotations

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.common.plugin import capability_is_supported

from ._helpers import connected_agent, new_session, quiet_period, run_prompt, session_update_kind

# Each test uses its own capability-shaped prompt: a shared fs-flavoured prompt would give the
# terminal/elicitation tests little chance of ever provoking the behaviour they guard.
_FS_PROMPT_TEXT = "Read the file README.md in the current directory and summarize it."
_TERMINAL_PROMPT_TEXT = "Run `ls -la` in a shell and show me the output."
_ELICITATION_PROMPT_TEXT = "Before you continue, ask me which of two options I'd prefer."


async def _methods_called_with_no_client_capabilities(agent_launch, tmp_path, prompt_text: str) -> list[str]:
    async with connected_agent(agent_launch, client_capabilities={}) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": prompt_text}],
            timeout=agent_launch.default_timeout,
        )
    return [
        entry.parsed.get("method")
        for entry in turn.client_requests_seen
        if isinstance(entry.parsed, dict)
    ]


@pytest.mark.requirement("ACP-CLIENTCAP-001")
async def test_no_unadvertised_clientcap_fs_call(agent_launch, tmp_path):
    """ACP-CLIENTCAP-001 (Req 29). See module docstring."""
    methods_seen = await _methods_called_with_no_client_capabilities(agent_launch, tmp_path, _FS_PROMPT_TEXT)
    fs_calls = [m for m in methods_seen if isinstance(m, str) and m.startswith("fs/")]
    assert not fs_calls, f"ACP-CLIENTCAP-001: fs/* called without fs advertised: {fs_calls!r}"


@pytest.mark.requirement("ACP-CLIENTCAP-002")
async def test_no_unadvertised_clientcap_terminal_call(agent_launch, tmp_path):
    """ACP-CLIENTCAP-002 (Req 30). See module docstring."""
    methods_seen = await _methods_called_with_no_client_capabilities(
        agent_launch, tmp_path, _TERMINAL_PROMPT_TEXT
    )
    terminal_calls = [m for m in methods_seen if isinstance(m, str) and m.startswith("terminal/")]
    assert not terminal_calls, (
        f"ACP-CLIENTCAP-002: terminal/* called without terminal advertised: {terminal_calls!r}"
    )


@pytest.mark.requirement("ACP-CLIENTCAP-003")
async def test_no_unadvertised_clientcap_elicitation_call(agent_launch, tmp_path):
    """ACP-CLIENTCAP-003 (Req 32). See module docstring."""
    methods_seen = await _methods_called_with_no_client_capabilities(
        agent_launch, tmp_path, _ELICITATION_PROMPT_TEXT
    )
    elicitation_calls = [m for m in methods_seen if m == "elicitation/create"]
    assert not elicitation_calls, (
        f"ACP-CLIENTCAP-003: elicitation/create called without an elicitation mode advertised: "
        f"{elicitation_calls!r}"
    )


async def _session_update_kinds_with_no_client_capabilities(
    agent_launch, agent_initialize_result, tmp_path
) -> list[str]:
    """Every `sessionUpdate` kind the agent sent over one connection with `clientCapabilities:
    {}`: `session/new`, one prompt turn, `session/load` of that session when `loadSession` is
    advertised (to cover replay), then a quiet period for anything sent outside a turn."""
    init_result = agent_initialize_result.result
    async with connected_agent(agent_launch, client_capabilities={}) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": "Summarize what you can help me with in this project."}],
            timeout=agent_launch.default_timeout,
        )
        if init_result is not None and capability_is_supported(
            init_result, "agentCapabilities.loadSession", boolean=True
        ):
            load_id = await agent.send_request(
                "session/load", {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": []}
            )
            # A failed load is ACP-LOAD-001's finding; only the updates seen are judged here.
            await agent.wait_for_response(load_id, timeout=agent_launch.default_timeout)
        try:
            await agent.wait_for_message(
                lambda _entry: False, timeout=quiet_period(agent_launch.default_timeout)
            )
        except (AgentTimeout, AgentExited):
            pass
    return [
        kind
        for entry in agent.transcript
        if entry.direction is Direction.RECEIVED and (kind := session_update_kind(entry)) is not None
    ]


@pytest.mark.requirement("ACP-CLIENTCAP-004")
async def test_no_notice_without_client_capability(agent_launch, agent_initialize_result, tmp_path):
    """ACP-CLIENTCAP-004. See module docstring."""
    kinds = await _session_update_kinds_with_no_client_capabilities(
        agent_launch, agent_initialize_result, tmp_path
    )
    assert "notice" not in kinds, (
        "ACP-CLIENTCAP-004: notice sent without clientCapabilities.session.notices advertised"
    )


@pytest.mark.requirement("ACP-CLIENTCAP-005")
async def test_no_compaction_update_without_client_capability(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-CLIENTCAP-005. See module docstring; covers `session/load` replay too."""
    kinds = await _session_update_kinds_with_no_client_capabilities(
        agent_launch, agent_initialize_result, tmp_path
    )
    sent = sorted({k for k in kinds if k in ("compaction_update", "compaction_summary_chunk")})
    assert not sent, (
        f"ACP-CLIENTCAP-005: {sent!r} sent without clientCapabilities.session.compaction advertised"
    )


@pytest.mark.requirement("ACP-CLIENTCAP-006")
async def test_no_plan_operation_without_client_capability(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-CLIENTCAP-006. See module docstring. The baseline `plan` update stays allowed."""
    kinds = await _session_update_kinds_with_no_client_capabilities(
        agent_launch, agent_initialize_result, tmp_path
    )
    sent = sorted({k for k in kinds if k in ("plan_update", "plan_removed")})
    assert not sent, f"ACP-CLIENTCAP-006: {sent!r} sent without clientCapabilities.plan advertised"


@pytest.mark.requirement("ACP-CLIENTCAP-007")
async def test_no_subagent_update_without_client_capability(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-CLIENTCAP-007. See module docstring."""
    kinds = await _session_update_kinds_with_no_client_capabilities(
        agent_launch, agent_initialize_result, tmp_path
    )
    sent = sorted(
        {k for k in kinds if k in ("subagent_update", "session_message", "session_message_chunk")}
    )
    assert not sent, (
        f"ACP-CLIENTCAP-007: {sent!r} sent without clientCapabilities.subagents advertised"
    )
