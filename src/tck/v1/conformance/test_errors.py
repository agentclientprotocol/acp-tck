"""Error codes for session-scoped requests naming a session the agent does not know:
ACP-ERROR-003 (`session/prompt`) and ACP-ERROR-004 (`session/set_mode`,
`session/set_config_option`, `session/load`, `session/resume`).

Both are ADVISORY: `error.mdx` says the agent SHOULD answer `-32002` with `data.sessionId` set to
the requested id. Each probe checks the code and `data.sessionId` and reports both problems
together. A `-32000` reply (authentication required) SKIPs rather than fails. Per-method gates
follow the other suites: `loadSession`/`resume` by capability marker, `modes`/`configOptions` by
what `session/new` returned. The probes use v1-shaped params, hence `skip_if_version_mismatch`.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import AgentTimeout, TranscriptEntry
from tck.v1.protocol import AUTHENTICATION_REQUIRED, RESOURCE_NOT_FOUND

from ._helpers import connected_agent, new_session, skip_if_auth_gated, skip_if_version_mismatch

_UNKNOWN_SESSION_ID = "tck-never-created-session"


async def _request(agent, method: str, params: dict[str, Any], *, timeout: float) -> TranscriptEntry:
    req_id = await agent.send_request(method, params)
    try:
        return await agent.wait_for_response(req_id, timeout=timeout)
    except AgentTimeout:
        pytest.fail(f"{method} for an unknown session got no reply within {timeout}s")


def _skip_on_version_mismatch(agent_initialize_result) -> None:
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)


def _assert_unknown_session_error(entry: TranscriptEntry, method: str, session_id: str) -> None:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    if isinstance(error, dict) and error.get("code") == AUTHENTICATION_REQUIRED:
        pytest.skip(f"{method} returned -32000 (authentication required) before checking the session")
    if not isinstance(error, dict):
        pytest.fail(
            f"{method} for an unknown session should fail with -32002 and "
            f"data.sessionId={session_id!r}, but did not return an error: {entry.text!r}"
        )
    problems = []
    if error.get("code") != RESOURCE_NOT_FOUND:
        problems.append(f"expected code -32002, got {error.get('code')!r}")
    data = error.get("data")
    if not isinstance(data, dict):
        problems.append(f"expected error.data to be an object with sessionId, got {data!r}")
    elif data.get("sessionId") != session_id:
        problems.append(f"expected data.sessionId={session_id!r}, got {data.get('sessionId')!r}")
    assert not problems, f"{method} for an unknown session: {'; '.join(problems)} ({entry.text!r})"


async def _new_session_result(agent, cwd, *, timeout: float) -> dict[str, Any]:
    req_id = await agent.send_request("session/new", {"cwd": str(cwd), "mcpServers": []})
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    skip_if_auth_gated(entry)
    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/new did not return a result object: {entry.text!r}"
    )
    return msg["result"]


# --- ACP-ERROR-003: session/prompt ---


@pytest.mark.requirement("ACP-ERROR-003")
async def test_prompt_never_created_session_gets_resource_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-003 (ADVISORY). `session/prompt` for a `sessionId` the agent never created
    gets `-32002` with `data.sessionId` set to that id."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await _request(
            agent,
            "session/prompt",
            {"sessionId": _UNKNOWN_SESSION_ID, "prompt": [{"type": "text", "text": "hi"}]},
            timeout=agent_launch.default_timeout,
        )
        _assert_unknown_session_error(entry, "session/prompt", _UNKNOWN_SESSION_ID)


@pytest.mark.requirement("ACP-ERROR-003")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.close")
async def test_prompt_closed_session_gets_resource_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-003 (ADVISORY). A session is active only until it is closed, so a
    `session/prompt` naming a session this connection already closed gets the same
    `-32002` + `data.sessionId` error. A `session/close` that fails SKIPs (ACP-CLOSE-001
    judges close itself)."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        close_id = await agent.send_request("session/close", {"sessionId": session_id})
        close_entry = await agent.wait_for_response(close_id, timeout=agent_launch.default_timeout)
        close_msg = close_entry.parsed
        if not (isinstance(close_msg, dict) and "result" in close_msg):
            pytest.skip(f"session/close did not succeed, so no closed session to probe: {close_entry.text!r}")
        entry = await _request(
            agent,
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": "hi"}]},
            timeout=agent_launch.default_timeout,
        )
        _assert_unknown_session_error(entry, "session/prompt", session_id)


# --- ACP-ERROR-004: set_mode, set_config_option, load, resume ---


@pytest.mark.requirement("ACP-ERROR-004")
async def test_set_mode_unknown_session_gets_resource_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-004 (ADVISORY). `session/set_mode` for an unknown session, with a mode id the
    agent advertised so the session is the only thing wrong. Gated on `session/new` returning
    `modes`."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        result = await _new_session_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        modes = result.get("modes")
        if not isinstance(modes, dict):
            pytest.skip("session/new returned no modes")
        mode_ids = [
            mode.get("id")
            for mode in modes.get("availableModes") or []
            if isinstance(mode, dict) and isinstance(mode.get("id"), str)
        ]
        if not mode_ids:
            pytest.skip("session/new returned no available modes to name")
        entry = await _request(
            agent,
            "session/set_mode",
            {"sessionId": _UNKNOWN_SESSION_ID, "modeId": mode_ids[0]},
            timeout=agent_launch.default_timeout,
        )
        _assert_unknown_session_error(entry, "session/set_mode", _UNKNOWN_SESSION_ID)


@pytest.mark.requirement("ACP-ERROR-004")
async def test_set_config_option_unknown_session_gets_resource_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-004 (ADVISORY). `session/set_config_option` for an unknown session, setting an
    advertised option to its current value so the session is the only thing wrong. Gated on
    `session/new` returning `configOptions`."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        result = await _new_session_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        option = next(
            (
                opt
                for opt in result.get("configOptions") or []
                if isinstance(opt, dict) and isinstance(opt.get("id"), str) and "currentValue" in opt
            ),
            None,
        )
        if option is None:
            pytest.skip("session/new returned no configOptions to name")
        params: dict[str, Any] = {
            "sessionId": _UNKNOWN_SESSION_ID,
            "configId": option["id"],
            "value": option["currentValue"],
        }
        if option.get("type") == "boolean":
            params["type"] = "boolean"
        entry = await _request(
            agent, "session/set_config_option", params, timeout=agent_launch.default_timeout
        )
        _assert_unknown_session_error(entry, "session/set_config_option", _UNKNOWN_SESSION_ID)


@pytest.mark.requirement("ACP-ERROR-004")
@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)
async def test_load_unknown_session_gets_resource_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-004 (ADVISORY). `session/load` of a session that does not exist must not
    create it."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        entry = await _request(
            agent,
            "session/load",
            {"sessionId": _UNKNOWN_SESSION_ID, "cwd": str(tmp_path), "mcpServers": []},
            timeout=agent_launch.default_timeout,
        )
        _assert_unknown_session_error(entry, "session/load", _UNKNOWN_SESSION_ID)


@pytest.mark.requirement("ACP-ERROR-004")
@pytest.mark.capability("agentCapabilities.sessionCapabilities.resume")
async def test_resume_unknown_session_gets_resource_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-004 (ADVISORY). `session/resume` of a session that does not exist must not
    create it."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        entry = await _request(
            agent,
            "session/resume",
            {"sessionId": _UNKNOWN_SESSION_ID, "cwd": str(tmp_path), "mcpServers": []},
            timeout=agent_launch.default_timeout,
        )
        _assert_unknown_session_error(entry, "session/resume", _UNKNOWN_SESSION_ID)
