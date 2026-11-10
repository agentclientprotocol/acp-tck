"""Error codes the agent returns for the cases `error.mdx` names (all ADVISORY):

- ACP-ERROR-003 (`session/prompt`) and ACP-ERROR-004 (`session/set_mode`,
  `session/set_config_option`, `session/load`, `session/resume`): a session the agent does not
  know gets `-32002` with `data.sessionId` set to the requested id. Each probe checks the code
  and `data.sessionId` and reports both problems together.
- ACP-ERROR-005: a request before `initialize` gets `-32600`.
- ACP-ERROR-006: an unadvertised stable capability-gated method gets `-32601`.
- ACP-ERROR-007: an unknown `modeId`, `configId` or select value gets `-32602`.
- ACP-ERROR-008: codes in the reserved ranges are ACP-defined ones.

A `-32000` reply (authentication required) SKIPs rather than fails where the agent may check
authentication first. Per-method gates follow the other suites: `loadSession`/`resume` by
capability marker, `modes`/`configOptions` by what `session/new` returned. The probes use
v1-shaped params, hence `skip_if_version_mismatch`.

Some probes break a client rule (sending before `initialize`, naming an unadvertised method or
an unknown mode) because the spec defines the agent's answer; ids and values the TCK invents are
`_tck`-prefixed.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import AgentTimeout, TranscriptEntry
from tck.common.plugin import capability_is_supported
from tck.v1.protocol import (
    AUTHENTICATION_REQUIRED,
    ERROR_CODES,
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    RESOURCE_NOT_FOUND,
)

from ._helpers import connected_agent, new_session, skip_if_auth_gated, skip_if_version_mismatch

_UNKNOWN_SESSION_ID = "tck-never-created-session"

# `error.mdx:37`: reserved for JSON-RPC and ACP.
_RESERVED_RANGES = ((-32768, -32000), (-32899, -32800))


async def _request(agent, method: str, params: dict[str, Any], *, timeout: float) -> TranscriptEntry:
    req_id = await agent.send_request(method, params)
    try:
        return await agent.wait_for_response(req_id, timeout=timeout)
    except AgentTimeout:
        pytest.fail(f"{method} got no reply within {timeout}s")


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


def _error_object(entry: TranscriptEntry) -> dict[str, Any] | None:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return error if isinstance(error, dict) else None


def _assert_error_code(entry: TranscriptEntry, method: str, expected: int, what: str) -> None:
    error = _error_object(entry)
    assert error is not None, f"{method} {what} should fail with {expected}, but did not return an error: {entry.text!r}"
    assert error.get("code") == expected, (
        f"{method} {what} should fail with {expected}, got {error.get('code')!r}: {entry.text!r}"
    )


# --- ACP-ERROR-005: request before initialize ---


@pytest.mark.requirement("ACP-ERROR-005")
async def test_request_before_initialize_gets_invalid_request(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-005 (ADVISORY). A valid `session/new` sent as the connection's first message,
    before `initialize`, gets `-32600`. Deliberately breaks the client rule that `initialize`
    comes first, because `error.mdx` defines the agent's answer. Nothing is asserted about the
    connection afterwards."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch, handshake=False) as agent:
        entry = await _request(
            agent,
            "session/new",
            {"cwd": str(tmp_path), "mcpServers": []},
            timeout=agent_launch.default_timeout,
        )
        _assert_error_code(entry, "session/new", INVALID_REQUEST, "sent before initialize")


# --- ACP-ERROR-006: unadvertised capability-gated methods ---

# (method, capability path, boolean gate); ordered so `close`/`delete`, which may end the
# session the other probes name, come last.
_GATED_METHODS = (
    ("session/load", "agentCapabilities.loadSession", True),
    ("session/list", "agentCapabilities.sessionCapabilities.list", False),
    ("session/resume", "agentCapabilities.sessionCapabilities.resume", False),
    ("session/close", "agentCapabilities.sessionCapabilities.close", False),
    ("session/delete", "agentCapabilities.sessionCapabilities.delete", False),
)


def _gated_params(method: str, session_id: str, cwd) -> dict[str, Any]:
    if method == "session/list":
        return {}
    if method in ("session/load", "session/resume"):
        return {"sessionId": session_id, "cwd": str(cwd), "mcpServers": []}
    return {"sessionId": session_id}


@pytest.mark.requirement("ACP-ERROR-006")
async def test_unadvertised_gated_methods_get_method_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-006 (ADVISORY). Every stable capability-gated method the agent did not advertise
    gets `-32601` when sent with well-formed params naming a real session (so a missing session
    is not an alternative explanation). The gate is inverted -- the test needs the methods
    that are *not* advertised -- so it is computed here instead of by a capability marker. SKIPs
    if all are advertised, or when no problem was found but a probe returned `-32000` (the
    agent may check authentication first); problems already found still FAIL."""
    _skip_on_version_mismatch(agent_initialize_result)
    init_result = agent_initialize_result.result
    if init_result is None:
        pytest.fail(f"cannot evaluate advertised capabilities: initialize failed: {agent_initialize_result.error_message}", pytrace=False)
    unadvertised = [
        method
        for method, path, boolean in _GATED_METHODS
        if not capability_is_supported(init_result, path, boolean=boolean)
    ]
    if not unadvertised:
        pytest.skip("every capability-gated method is advertised")
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        problems = []
        auth_required = []
        for method in unadvertised:
            entry = await _request(
                agent,
                method,
                _gated_params(method, session_id, tmp_path),
                timeout=agent_launch.default_timeout,
            )
            error = _error_object(entry)
            if error is None:
                problems.append(f"{method}: succeeded although not advertised")
            elif error.get("code") == AUTHENTICATION_REQUIRED:
                auth_required.append(method)
            elif error.get("code") != METHOD_NOT_FOUND:
                problems.append(f"{method}: expected -32601, got {error.get('code')!r}")
    assert not problems, "unadvertised methods should get -32601 -- " + "; ".join(problems)
    if auth_required:
        pytest.skip(f"{', '.join(auth_required)} returned -32000 (authentication required)")


# --- ACP-ERROR-007: unknown mode / config option / value ---


async def _session_with_result(agent, tmp_path, *, timeout: float) -> tuple[str, dict[str, Any]]:
    result = await _new_session_result(agent, tmp_path, timeout=timeout)
    session_id = result.get("sessionId")
    assert isinstance(session_id, str), f"session/new result has no string sessionId: {result!r}"
    return session_id, result


@pytest.mark.requirement("ACP-ERROR-007")
async def test_set_mode_unknown_mode_gets_invalid_params(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-007 (ADVISORY). `session/set_mode` on a real session with a `_tck`-prefixed
    `modeId` the agent never advertised gets `-32602`. Gated on `session/new` returning
    `modes`. Deliberately names an unadvertised mode, which a client must not do, because
    `error.mdx` defines the agent's answer."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        session_id, result = await _session_with_result(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        if not isinstance(result.get("modes"), dict):
            pytest.skip("session/new returned no modes")
        entry = await _request(
            agent,
            "session/set_mode",
            {"sessionId": session_id, "modeId": "_tck_unknown_mode"},
            timeout=agent_launch.default_timeout,
        )
        _assert_error_code(entry, "session/set_mode", INVALID_PARAMS, "with an unknown modeId")


@pytest.mark.requirement("ACP-ERROR-007")
async def test_set_config_option_unknown_config_id_gets_invalid_params(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-007 (ADVISORY). `session/set_config_option` on a real session with a
    `_tck`-prefixed `configId` the agent never advertised gets `-32602`. Gated on `session/new`
    returning `configOptions`. Breaks the client rule against naming an unadvertised option,
    since `error.mdx` defines the agent's answer."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        session_id, result = await _session_with_result(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        if not result.get("configOptions"):
            pytest.skip("session/new returned no configOptions")
        entry = await _request(
            agent,
            "session/set_config_option",
            {"sessionId": session_id, "configId": "_tck_unknown_config", "value": "_tck_unknown_value"},
            timeout=agent_launch.default_timeout,
        )
        _assert_error_code(
            entry, "session/set_config_option", INVALID_PARAMS, "with an unknown configId"
        )


@pytest.mark.requirement("ACP-ERROR-007")
async def test_set_config_option_unsupported_value_gets_invalid_params(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-007 (ADVISORY). `session/set_config_option` on a real `select` option with a
    `_tck`-prefixed value the option does not offer gets `-32602`. Gated on `session/new`
    returning a select option. Breaks the client rule against sending an unoffered value,
    since `error.mdx` defines the agent's answer."""
    _skip_on_version_mismatch(agent_initialize_result)
    async with connected_agent(agent_launch) as agent:
        session_id, result = await _session_with_result(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        option = next(
            (
                opt
                for opt in result.get("configOptions") or []
                if isinstance(opt, dict)
                and isinstance(opt.get("id"), str)
                and opt.get("type") in (None, "select")
            ),
            None,
        )
        if option is None:
            pytest.skip("session/new returned no select configOptions")
        entry = await _request(
            agent,
            "session/set_config_option",
            {"sessionId": session_id, "configId": option["id"], "value": "_tck_unknown_value"},
            timeout=agent_launch.default_timeout,
        )
        _assert_error_code(
            entry, "session/set_config_option", INVALID_PARAMS, "with an unsupported value"
        )


# --- ACP-ERROR-008: reserved-range codes are ACP-defined ---


def _in_reserved_range(code: int) -> bool:
    return any(low <= code <= high for low, high in _RESERVED_RANGES)


@pytest.mark.requirement("ACP-ERROR-008")
async def test_reserved_range_codes_are_acp_defined(agent_launch, agent_initialize_result, tmp_path):
    """ACP-ERROR-008 (ADVISORY). Samples the error replies to an unrecognised method, a
    `session/new` missing `cwd` and a `session/prompt` for an unknown session; every code in
    `-32768..-32000` or `-32899..-32800` must be one of `ErrorCode`'s named members. A probe
    the agent leaves unanswered contributes no sample (ACP-EXT-001 and ACP-JSONRPC-004 judge
    that); passes vacuously if no probe yields an error."""
    _skip_on_version_mismatch(agent_initialize_result)
    probes = (
        ("_tck/does_not_exist", None),
        ("session/new", {"mcpServers": []}),  # missing required cwd
        (
            "session/prompt",
            {"sessionId": _UNKNOWN_SESSION_ID, "prompt": [{"type": "text", "text": "hi"}]},
        ),
    )
    samples: list[tuple[str, Any]] = []
    async with connected_agent(agent_launch) as agent:
        for method, params in probes:
            req_id = await agent.send_request(method, params)
            try:
                entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
            except AgentTimeout:
                continue
            error = _error_object(entry)
            if error is not None:
                samples.append((method, error.get("code")))
    offenders = [
        f"{method} -> {code}"
        for method, code in samples
        if isinstance(code, int)
        and not isinstance(code, bool)
        and _in_reserved_range(code)
        and code not in ERROR_CODES
    ]
    assert not offenders, (
        "error codes in a range reserved for JSON-RPC and ACP must be ACP-defined; "
        "implementation-specific errors should use codes outside it: " + "; ".join(offenders)
    )
