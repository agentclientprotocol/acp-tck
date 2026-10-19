"""Advisory/informational diagnostics: ACP-ERROR-001, ACP-ERROR-002, ACP-SHUTDOWN-001,
ACP-STDERR-001."""

from __future__ import annotations

import json

import pytest

from tck.common.harness import AgentTimeout
from tck.v1.protocol import AUTHENTICATION_REQUIRED, INVALID_PARAMS, PROTOCOL_VERSION

from ._helpers import connected_agent, skip_if_auth_gated, skip_if_version_mismatch


@pytest.mark.requirement("ACP-ERROR-001")
async def test_error_messages_are_non_empty_single_line(agent_launch):
    """ACP-ERROR-001 (ADVISORY -- the schema says `message` "should be limited to a concise
    single sentence"). Samples the error replies to an unrecognised method and a `session/new`
    missing `cwd`. An agent silent on the unknown method contributes no sample from it: that
    silence is ACP-EXT-001's defect, not this row's."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request(
            "initialize", {"protocolVersion": PROTOCOL_VERSION, "clientCapabilities": {}}
        )
        await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)

        unknown_id = await agent.send_request("_tck/does_not_exist")
        try:
            unknown_entry = await agent.wait_for_response(
                unknown_id, timeout=agent_launch.default_timeout
            )
        except AgentTimeout:
            unknown_entry = None

        bad_id = await agent.send_request("session/new", {"mcpServers": []})  # missing required cwd
        bad_entry = await agent.wait_for_response(bad_id, timeout=agent_launch.default_timeout)

    for what, entry in (("_tck/does_not_exist", unknown_entry), ("session/new (missing cwd)", bad_entry)):
        if entry is None:
            continue
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        if not isinstance(error, dict):
            continue  # no error to inspect; ACP-JSONRPC-002/004 own whether that's acceptable
        message = error.get("message")
        if not isinstance(message, str):
            continue  # envelope shape is ACP-JSONRPC-002's concern, not this test's
        assert message != "", f"{what}: error.message must not be empty"
        assert "\n" not in message, f"{what}: error.message must not contain a newline: {message!r}"
        data = error.get("data")
        if data is not None:
            # only confirms it's JSON-shaped; structure isn't asserted
            json.dumps(data)


@pytest.mark.requirement("ACP-ERROR-002")
async def test_invalid_params_yield_invalid_params_error(agent_launch, agent_initialize_result):
    """ACP-ERROR-002 (ADVISORY). `session/new` without the required `cwd` should get `-32602`.
    Runs after `connected_agent`'s optional `--tck-auth-method` authentication; a `-32000`
    still SKIPs, since checking auth before params is not wrong. `cwd` being required is a v1
    shape, hence `skip_if_version_mismatch`."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/new", {"mcpServers": []})  # missing required cwd
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    code = error.get("code") if isinstance(error, dict) else None
    if code == AUTHENTICATION_REQUIRED:
        pytest.skip("session/new returned -32000 (authentication required) before checking params")
    assert code == INVALID_PARAMS, (
        f"session/new without cwd should fail with -32602 (Invalid params): {entry.text!r}"
    )


@pytest.mark.requirement("ACP-SHUTDOWN-001")
async def test_agent_exits_promptly_after_stdin_close(agent_launch, tmp_path):
    """ACP-SHUTDOWN-001 (INFORMATIONAL -- the spec defines no shutdown timing, only that the
    client closes stdin and then terminates the subprocess). Relies on
    `connected_agent`'s close() ladder and `AgentProcess.exited_on_stdin_close` to report whether
    it exited on the first rung."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/new", {"cwd": str(tmp_path), "mcpServers": []})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)

    assert agent.exited_on_stdin_close, (
        "agent did not exit within the grace period after stdin closed; it needed SIGTERM/"
        "SIGKILL to terminate (informational -- the spec does not mandate shutdown timing)"
    )


@pytest.mark.requirement("ACP-STDERR-001")
async def test_stderr_byte_count_is_recorded(agent_launch, tmp_path, record_property):
    """ACP-STDERR-001 (INFORMATIONAL -- the agent MAY log UTF-8 to stderr, transports.mdx:25).
    Surfaces how chatty an agent is on stderr during an ordinary exchange, for a human reading
    the report. FAILs only if `initialize`/`session/new` gets no response at all."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/new", {"cwd": str(tmp_path), "mcpServers": []})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)

    stderr_bytes = len(agent.stderr_text().encode("utf-8"))
    record_property("acp_tck_stderr_bytes", stderr_bytes)
