"""`session/options` conformance: ACP-OPTIONS-001..003 and ACP-OPTIONS-009.

`session/options` (unstable) returns the config options a session would start with, without
creating or resuming one. Every row is gated on `agentCapabilities.sessionCapabilities.options`
(the TCK may not call the method otherwise, `session-config-options.mdx:475`) and judges its own
fresh connection, so none depends on another row's outcome. The rows that rest on the method
working SKIP, not pass vacuously, when a plain `session/options {cwd}` is not answered with a
result (ACP-OPTIONS-001 judges that).
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

import pytest

from tck.common.harness import Direction
from tck.common.plugin import capability_is_supported
from tck.v1.validation import validate_agent_response

from ._helpers import (
    connected_agent,
    drain,
    quiet_period,
    run_prompt,
    session_update_kind,
    skip_if_auth_gated,
    skip_if_auth_required,
    skip_if_version_mismatch,
    stdio_mcp_server,
)

_OPTIONS_PATH = "agentCapabilities.sessionCapabilities.options"
_MAX_LIST_PAGES = 10


async def _options(agent, params: dict[str, Any], *, timeout: float):
    """The transcript entry answering `session/options` with `params`."""
    req_id = await agent.send_request("session/options", params)
    return await agent.wait_for_response(req_id, timeout=timeout)


def _succeeded(entry) -> bool:
    return isinstance(entry.parsed, dict) and isinstance(entry.parsed.get("result"), dict)


async def _require_working_method(agent, cwd: Path, *, timeout: float) -> None:
    """SKIP unless a plain `session/options {cwd}` succeeds (ACP-OPTIONS-001 judges it)."""
    entry = await _options(agent, {"cwd": str(cwd)}, timeout=timeout)
    skip_if_auth_required(entry, "session/options")
    if not _succeeded(entry):
        pytest.skip(f"prerequisite not met: session/options {{cwd}} did not succeed (see ACP-OPTIONS-001): {entry.text!r}")


async def _listed_ids(agent, cwd: Path, *, timeout: float) -> set[Any] | None:
    """The `sessionId`s `session/list` returns for `cwd` (following `nextCursor`, bounded), or
    `None` when a page was not answered with a list: ACP-LIST-001 judges that."""
    ids: set[Any] = set()
    cursor = None
    for _ in range(_MAX_LIST_PAGES):
        params: dict[str, Any] = {"cwd": str(cwd)}
        if cursor is not None:
            params["cursor"] = cursor
        req_id = await agent.send_request("session/list", params)
        entry = await agent.wait_for_response(req_id, timeout=timeout)
        result = entry.parsed.get("result") if isinstance(entry.parsed, dict) else None
        sessions = result.get("sessions") if isinstance(result, dict) else None
        if not isinstance(sessions, list):
            return None
        ids.update(info.get("sessionId") for info in sessions if isinstance(info, dict))
        cursor = result.get("nextCursor")
        if not isinstance(cursor, str):
            break
    return ids


@pytest.mark.requirement("ACP-OPTIONS-001")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_session_options_succeeds_with_a_valid_result(agent_launch, agent_initialize_result, tmp_path):
    """ACP-OPTIONS-001. A fresh connection, no session: `session/options {cwd}` must succeed and
    its result validate as `SessionOptionsResponse`. `-32000` SKIPs."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        entry = await _options(agent, {"cwd": str(tmp_path)}, timeout=agent_launch.default_timeout)
        skip_if_auth_required(entry, "session/options")
        msg = entry.parsed
        assert _succeeded(entry), (
            f"session/options did not succeed although the agent advertises {_OPTIONS_PATH}: {entry.text!r}"
        )
        issues = validate_agent_response("session/options", msg)
        assert not issues, f"session/options result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-OPTIONS-002")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_session_options_sends_no_update_and_lists_no_session(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-OPTIONS-002. No `session/update` may arrive between the request and a quiet period after
    its response (the connection has no session, so any is caused by the call). When `list` is
    advertised, `session/list` for the same `cwd` must show no session it did not show before; if
    `session/list` itself fails, only the notification half is judged."""
    init_result = agent_initialize_result.result
    timeout = agent_launch.default_timeout
    list_advertised = init_result is not None and capability_is_supported(
        init_result, "agentCapabilities.sessionCapabilities.list"
    )
    async with connected_agent(agent_launch) as agent:
        await _require_working_method(agent, tmp_path, timeout=timeout)
        before = await _listed_ids(agent, tmp_path, timeout=timeout) if list_advertised else None
        start = len(agent.transcript)
        entry = await _options(agent, {"cwd": str(tmp_path)}, timeout=timeout)
        assert _succeeded(entry), f"session/options stopped succeeding: {entry.text!r}"
        await drain(agent, quiet_period(timeout))
        updates = [
            e.text
            for e in agent.transcript[start:]
            if e.direction is Direction.RECEIVED and session_update_kind(e) is not None
        ]
        assert not updates, f"session/options was followed by session/update notifications: {updates!r}"
        if before is not None:
            after = await _listed_ids(agent, tmp_path, timeout=timeout)
            created = (after or set()) - before
            assert not created, f"session/options added entries to session/list: {sorted(map(str, created))!r}"


@pytest.mark.requirement("ACP-OPTIONS-003")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_session_options_for_an_unknown_session_is_an_error(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-OPTIONS-003. A client may send `sessionId` only to an agent that supports `loadSession`
    or `resume`, so the probe SKIPs on any other. A `sessionId` the agent never issued must be
    answered with an error, not a result; the docs name `-32002` but no keyword, so the code is
    not asserted."""
    init_result = agent_initialize_result.result
    if init_result is None or not (
        capability_is_supported(init_result, "agentCapabilities.loadSession", boolean=True)
        or capability_is_supported(init_result, "agentCapabilities.sessionCapabilities.resume")
    ):
        pytest.skip("neither loadSession nor sessionCapabilities.resume is advertised, so the agent may not be sent a sessionId")
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        await _require_working_method(agent, tmp_path, timeout=timeout)
        entry = await _options(
            agent,
            {"cwd": str(tmp_path), "sessionId": f"acp-tck-unknown-{uuid.uuid4().hex}"},
            timeout=timeout,
        )
        msg = entry.parsed
        assert isinstance(msg, dict) and "error" in msg and "result" not in msg, (
            f"session/options for a sessionId the agent never issued must fail, not return a result: {entry.text!r}"
        )


async def _wait_for_file(path: Path, timeout: float) -> bool:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not path.exists() and loop.time() < deadline:
        await asyncio.sleep(0.05)
    return path.exists()


@pytest.mark.requirement("ACP-OPTIONS-009")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_session_options_with_a_session_id_does_not_connect_mcp_servers(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-OPTIONS-009 (ADVISORY). Connection 1 creates a session with the stub stdio MCP server,
    runs one prompt and waits for the stub's marker (SKIP if the agent never connects, see
    ACP-SESSION-004). Connection 2, a fresh process, asks `session/options` for that session after
    the marker is deleted (SKIP if it cannot answer for it: the agent does not persist sessions);
    the marker must not reappear within a quiet period."""
    init_result = agent_initialize_result.result
    if init_result is None or not (
        capability_is_supported(init_result, "agentCapabilities.loadSession", boolean=True)
        or capability_is_supported(init_result, "agentCapabilities.sessionCapabilities.resume")
    ):
        pytest.skip("neither loadSession nor sessionCapabilities.resume is advertised, so the agent may not be sent a sessionId")
    timeout = agent_launch.default_timeout
    marker = tmp_path / "mcp-marker"
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": [stdio_mcp_server(marker)]}
        )
        entry = await agent.wait_for_response(req_id, timeout=timeout)
        skip_if_auth_gated(entry)
        result = entry.parsed.get("result") if isinstance(entry.parsed, dict) else None
        if not isinstance(result, dict) or not isinstance(result.get("sessionId"), str):
            pytest.skip(
                "prerequisite not met: session/new with a stdio MCP server did not succeed "
                f"(see ACP-SESSION-003): {entry.text!r}"
            )
        session_id = result["sessionId"]
        await run_prompt(agent, session_id, [{"type": "text", "text": "hello"}], timeout=timeout)
        if not await _wait_for_file(marker, timeout):
            pytest.skip("the agent never connected to the stub MCP server (see ACP-SESSION-004)")
    marker.unlink(missing_ok=True)
    async with connected_agent(agent_launch) as agent:
        entry = await _options(agent, {"cwd": str(tmp_path), "sessionId": session_id}, timeout=timeout)
        skip_if_auth_required(entry, "session/options")
        if not _succeeded(entry):
            pytest.skip(
                "the agent cannot answer session/options for the session from a fresh process "
                f"(it does not persist sessions): {entry.text!r}"
            )
        await drain(agent, quiet_period(timeout))
    assert not marker.exists(), (
        "session/options with a sessionId connected to the session's MCP server (the stub's marker reappeared)"
    )
