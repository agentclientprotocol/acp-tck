"""Session lifecycle conformance: ACP-SESSION-001..004."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from tck.v1.validation import validate_agent_response

from ._helpers import connected_agent, run_prompt, skip_if_auth_gated, skip_if_version_mismatch


@pytest.mark.requirement("ACP-SESSION-001")
async def test_session_new_succeeds_with_a_unique_session_id(agent_launch, tmp_path):
    """ACP-SESSION-001."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": []}
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, f"session/new did not succeed: {msg!r}"

        issues = validate_agent_response("session/new", msg)
        assert not issues, f"session/new result failed schema validation: {issues!r}"

        session_id = msg["result"].get("sessionId")
        assert isinstance(session_id, str) and session_id, (
            f"sessionId must be a non-empty string, got {session_id!r}"
        )


@pytest.mark.requirement("ACP-SESSION-002")
async def test_two_sessions_get_distinct_ids(agent_launch, tmp_path):
    """ACP-SESSION-002."""
    async with connected_agent(agent_launch) as agent:
        first_req = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": []}
        )
        first_entry = await agent.wait_for_response(first_req, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(first_entry)
        first_msg = first_entry.parsed
        assert isinstance(first_msg, dict) and isinstance(first_msg.get("result"), dict), (
            f"first session/new did not return a result object: {first_entry.text!r}"
        )
        first_id = first_msg["result"].get("sessionId")

        second_req = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": []}
        )
        second_entry = await agent.wait_for_response(second_req, timeout=agent_launch.default_timeout)
        second_msg = second_entry.parsed
        assert isinstance(second_msg, dict) and isinstance(second_msg.get("result"), dict), (
            f"second session/new did not return a result object: {second_entry.text!r}"
        )
        second_id = second_msg["result"].get("sessionId")

        assert first_id != second_id, f"two session/new calls returned the same sessionId: {first_id!r}"


# --- stdio MCP servers ---

_MCP_STUB = Path(__file__).with_name("_mcp_stub.py")


def _stdio_mcp_server(marker: Path) -> dict:
    """A stdio `McpServer` entry for the TCK's stub server. `command` must be an absolute path,
    which `sys.executable` is."""
    return {
        "name": "acp-tck-stub",
        "command": sys.executable,
        "args": [str(_MCP_STUB), str(marker)],
        "env": [],
    }


async def _new_session_with_stub_mcp(agent, cwd: Path, marker: Path, *, timeout: float):
    req_id = await agent.send_request(
        "session/new", {"cwd": str(cwd), "mcpServers": [_stdio_mcp_server(marker)]}
    )
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    skip_if_auth_gated(entry)
    return entry


@pytest.mark.requirement("ACP-SESSION-003")
async def test_session_new_accepts_a_stdio_mcp_server(agent_launch, agent_initialize_result, tmp_path):
    """ACP-SESSION-003. Checks version mismatch first: the result is judged against v1's schema."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        entry = await _new_session_with_stub_mcp(
            agent, tmp_path, tmp_path / "mcp-marker", timeout=agent_launch.default_timeout
        )
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/new with a stdio MCP server did not succeed: {entry.text!r}"
        )
        issues = validate_agent_response("session/new", msg)
        assert not issues, f"session/new result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-SESSION-004")
async def test_agent_connects_to_the_stdio_mcp_server(agent_launch, agent_initialize_result, tmp_path):
    """ACP-SESSION-004 (ADVISORY). Runs one prompt turn before looking for the stub's marker
    file, then keeps polling up to --tck-timeout, so an agent that connects lazily or in the
    background is not misreported."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    marker = tmp_path / "mcp-marker"
    async with connected_agent(agent_launch) as agent:
        entry = await _new_session_with_stub_mcp(
            agent, tmp_path, marker, timeout=agent_launch.default_timeout
        )
        msg = entry.parsed
        if not (isinstance(msg, dict) and isinstance(msg.get("result"), dict)):
            pytest.skip(
                "prerequisite not met: session/new with a stdio MCP server did not succeed "
                f"(see ACP-SESSION-003): {entry.text!r}"
            )
        await run_prompt(
            agent,
            msg["result"].get("sessionId"),
            [{"type": "text", "text": "hello"}],
            timeout=agent_launch.default_timeout,
        )
        loop = asyncio.get_running_loop()
        deadline = loop.time() + agent_launch.default_timeout
        while not marker.exists() and loop.time() < deadline:
            await asyncio.sleep(0.05)
    assert marker.exists(), (
        "agent never sent an MCP initialize request to the stdio MCP server it was given"
    )
