"""`session/options` conformance: ACP-OPTIONS-001..003 and ACP-OPTIONS-009.

`session/options` (unstable) returns the config options a session would start with, without
creating or resuming one. Every row is gated on `capabilities.session.options` (the TCK may not
call the method otherwise, `session-config-options.mdx:482`) and judges its own fresh connection,
so none depends on another row's outcome. The rows that rest on the method working SKIP, not pass
vacuously, when a plain `session/options {cwd}` is not answered with a result (ACP-OPTIONS-001
judges that). The result's own lists are also judged by ACP-CONFIG-001/210, ACP-COMMANDS-201 and
ACP-CLIENTCAP-203.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from tck.common.harness import Direction
from tck.common.plugin import capability_is_supported
from tck.v2.protocol import RESOURCE_NOT_FOUND
from tck.v2.validation import validate_agent_response

from ._helpers import (
    close_session,
    connected_agent,
    drain_quiet,
    iter_messages,
    list_sessions,
    new_session,
    quiet_period,
    run_prompt,
    skip_if_auth_gated,
    skip_if_auth_required,
    skip_if_version_mismatch,
    stdio_mcp_server,
)

_OPTIONS_PATH = "capabilities.session.options"
_MAX_LIST_PAGES = 10


async def _options(agent, params: dict[str, Any], *, timeout: float):
    """The transcript entry answering `session/options` with `params`."""
    req_id = await agent.send_request("session/options", params)
    return await agent.wait_for_response(req_id, timeout=timeout)


def _succeeded(entry) -> bool:
    return isinstance(entry.parsed, dict) and isinstance(entry.parsed.get("result"), dict)


def _error(entry) -> dict[str, Any] | None:
    error = entry.parsed.get("error") if isinstance(entry.parsed, dict) else None
    return error if isinstance(error, dict) else None


async def _require_working_method(agent, cwd: Path, *, timeout: float) -> None:
    """SKIP unless a plain `session/options {cwd}` succeeds (ACP-OPTIONS-001 judges it)."""
    entry = await _options(agent, {"cwd": str(cwd)}, timeout=timeout)
    skip_if_auth_required(entry, "session/options")
    if not _succeeded(entry):
        pytest.skip(
            f"prerequisite not met: session/options {{cwd}} did not succeed (see ACP-OPTIONS-001): {entry.text!r}"
        )


async def _listed_ids(agent, cwd: Path, *, timeout: float) -> set[Any] | None:
    """The `sessionId`s `session/list` returns for `cwd` (following `nextCursor`, bounded), or
    `None` when a page was not answered with a list: ACP-LIST-001 judges that."""
    ids: set[Any] = set()
    cursor = None
    for _ in range(_MAX_LIST_PAGES):
        entry = await list_sessions(agent, cwd=cwd, cursor=cursor, timeout=timeout)
        result = entry.parsed.get("result") if isinstance(entry.parsed, dict) else None
        sessions = result.get("sessions") if isinstance(result, dict) else None
        if not isinstance(sessions, list):
            return None
        ids.update(info.get("sessionId") for info in sessions if isinstance(info, dict))
        cursor = result.get("nextCursor")
        if not isinstance(cursor, str):
            break
    return ids


def _updates_since(agent, start: int) -> list[str]:
    """Text of every `session/update` received after transcript index `start`."""
    return [
        entry.text
        for entry in agent.transcript[start:]
        if entry.direction is Direction.RECEIVED
        and any(message.get("method") == "session/update" for message in iter_messages(entry))
    ]


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
        assert _succeeded(entry), (
            f"session/options did not succeed although the agent advertises {_OPTIONS_PATH}: {entry.text!r}"
        )
        issues = validate_agent_response("session/options", entry.parsed)
        assert not issues, f"session/options result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-OPTIONS-002")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_session_options_creates_resumes_and_notifies_nothing(agent_launch, tmp_path):
    """ACP-OPTIONS-002. The connection holds a session the TCK created and closed, then waits a
    quiet period. A plain `session/options {cwd}` must send no `session/update` between the request
    and a quiet period after its response, and a `session/list` for the same `cwd` must show no
    session it did not show before, apart from the closed one (an agent may persist it late); if
    `session/list` fails, only the notification half is judged. Then
    `session/options` with the closed session's `sessionId` must send no update either and must not
    resume it: a following `session/prompt` for that id must still get `-32002`. An agent that
    fails that call (it may have discarded the closed session) leaves this half unjudged."""
    timeout = agent_launch.default_timeout
    problems: list[str] = []
    async with connected_agent(agent_launch) as agent:
        await _require_working_method(agent, tmp_path, timeout=timeout)
        session_id = await new_session(agent, tmp_path, timeout=timeout)
        closed = _succeeded(await close_session(agent, session_id, timeout=timeout))
        await drain_quiet(agent, quiet_period(timeout))  # late setup traffic is not session/options'
        before = await _listed_ids(agent, tmp_path, timeout=timeout)

        start = len(agent.transcript)
        entry = await _options(agent, {"cwd": str(tmp_path)}, timeout=timeout)
        assert _succeeded(entry), f"session/options stopped succeeding: {entry.text!r}"
        await drain_quiet(agent, quiet_period(timeout))
        if updates := _updates_since(agent, start):
            problems.append(f"session/options was followed by session/update notifications: {updates!r}")
        if before is not None:
            after = await _listed_ids(agent, tmp_path, timeout=timeout)
            created = (after or set()) - before - {session_id}  # the TCK's own session may be persisted late
            if created:
                problems.append(f"session/options added entries to session/list: {sorted(map(str, created))!r}")

        if closed:
            start = len(agent.transcript)
            entry = await _options(agent, {"cwd": str(tmp_path), "sessionId": session_id}, timeout=timeout)
            if _succeeded(entry):
                await drain_quiet(agent, quiet_period(timeout))
                if updates := _updates_since(agent, start):
                    problems.append(
                        f"session/options with a sessionId was followed by session/update notifications: {updates!r}"
                    )
                req_id = await agent.send_request(
                    "session/prompt", {"sessionId": session_id, "prompt": [{"type": "text", "text": "hi"}]}
                )
                prompt = await agent.wait_for_response(req_id, timeout=timeout)
                error = _error(prompt)
                if error is None or error.get("code") != RESOURCE_NOT_FOUND:
                    problems.append(
                        "session/options with the sessionId of a closed session resumed it: a session/prompt "
                        f"for that id was not answered -32002: {prompt.text!r}"
                    )
    assert not problems, "; ".join(problems)


@pytest.mark.requirement("ACP-OPTIONS-003")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_session_options_for_an_unknown_session_is_not_found(
    agent_launch, tmp_path, record_property
):
    """ACP-OPTIONS-003. A `sessionId` the agent never issued must be answered with `-32002`. The
    id the error carries in `data.sessionId` is recorded, not asserted: `error.mdx`'s Unstable
    features list omits `session/options`."""
    timeout = agent_launch.default_timeout
    unknown = "acp-tck-unknown-session"
    async with connected_agent(agent_launch) as agent:
        await _require_working_method(agent, tmp_path, timeout=timeout)
        entry = await _options(agent, {"cwd": str(tmp_path), "sessionId": unknown}, timeout=timeout)
    error = _error(entry)
    assert error is not None and error.get("code") == RESOURCE_NOT_FOUND, (
        f"session/options for a sessionId the agent never issued must fail with -32002: {entry.text!r}"
    )
    data = error.get("data")
    record_property(
        "acp_tck_options_unknown_session_data_session_id",
        data.get("sessionId") == unknown if isinstance(data, dict) else None,
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
    """ACP-OPTIONS-009 (ADVISORY). One connection creates a session with the stub stdio MCP server
    (SKIP unless `session.mcp.stdio` is advertised), runs one prompt and waits for the stub's marker
    (SKIP if the agent never connects, see ACP-SESSION-006), closes the session and deletes the
    marker, then asks `session/options` for that session (SKIP if it cannot answer: it no longer has
    the session); the marker must not reappear within a quiet period."""
    init_result = agent_initialize_result.result
    if init_result is None or not capability_is_supported(init_result, "capabilities.session.mcp.stdio"):
        pytest.skip("capabilities.session.mcp.stdio is not advertised, so the TCK may not send the stub MCP server")
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
                f"(see ACP-MCP-201/202): {entry.text!r}"
            )
        session_id = result["sessionId"]
        await run_prompt(agent, session_id, [{"type": "text", "text": "hello"}], timeout=timeout)
        if not await _wait_for_file(marker, timeout):
            pytest.skip("the agent never connected to the stub MCP server (see ACP-SESSION-006)")
        if not _succeeded(await close_session(agent, session_id, timeout=timeout)):
            pytest.skip("session/close did not succeed (see ACP-CLOSE-001)")
        marker.unlink(missing_ok=True)
        entry = await _options(agent, {"cwd": str(tmp_path), "sessionId": session_id}, timeout=timeout)
        skip_if_auth_required(entry, "session/options")
        if not _succeeded(entry):
            pytest.skip(
                f"the agent cannot answer session/options for the closed session: {entry.text!r}"
            )
        await drain_quiet(agent, quiet_period(timeout))
    assert not marker.exists(), (
        "session/options with a sessionId connected to the session's MCP server (the stub's marker reappeared)"
    )
