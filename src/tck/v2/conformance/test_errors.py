"""Error codes the agent returns for the cases `error.mdx` names:

- ACP-ERROR-201 (CAPABILITY, `capabilities.session`): a session-scoped request naming a session
  that is not active gets `-32002` with `data.sessionId` set to the requested id. Probes
  `session/prompt` for a never-created and for a closed session, and `session/set_config_option`
  for a never-created one. (`session/resume` of an unknown id is `ACP-RESUME-211`, judged by the
  same `_helpers.assert_unknown_session_error`.)
- ACP-ERROR-202 (MANDATORY): a standard method gated on a capability the agent did not advertise
  gets `-32601`.
- ACP-ERROR-203 (ADVISORY): codes in the reserved ranges are ACP-defined ones.
- ACP-ERROR-204 (ADVISORY): if a non-JSON line is answered, the answer is `-32700` with `id: null`.

The MUSTs name their codes, so they are asserted. A `-32000` reply to an unknown-session probe is
not excused: the probes run after `session/new` (and `auth/login`, if `--auth-method` was given),
so authentication has already happened.

Some probes break a client rule (naming an unadvertised method, a non-JSON line) because the spec
defines the agent's answer; ids the TCK invents are `_tck`-prefixed or `tck-` ids that no agent can
have created.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, TranscriptEntry
from tck.common.plugin import capability_is_supported
from tck.v2 import SPEC
from tck.v2.protocol import (
    AUTHENTICATION_REQUIRED,
    ERROR_CODES,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
)

from ._helpers import (
    advertises_session,
    assert_unknown_session_error,
    close_session,
    connected_agent,
    new_session,
    next_reply_line,
    quiet_period,
    set_config_option,
    skip_if_auth_gated,
    skip_if_version_mismatch,
)

_UNKNOWN_SESSION_ID = "tck-never-created-session"
_PROMPT = [{"type": "text", "text": "hi"}]

# `error.mdx:38`: reserved for JSON-RPC and ACP.
_RESERVED_RANGES = ((-32768, -32000), (-32899, -32800))


async def _request(agent, method: str, params: dict[str, Any] | None, *, timeout: float) -> TranscriptEntry:
    req_id = await agent.send_request(method, params)
    try:
        return await agent.wait_for_response(req_id, timeout=timeout)
    except AgentTimeout:
        pytest.fail(f"{method} got no reply within {timeout}s")


def _error_object(entry: TranscriptEntry) -> dict[str, Any] | None:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return error if isinstance(error, dict) else None


# --- ACP-ERROR-201: unknown session ---


@pytest.mark.requirement("ACP-ERROR-201")
@pytest.mark.capability("capabilities.session")
async def test_prompt_never_created_session_gets_resource_not_found(agent_launch, tmp_path):
    """ACP-ERROR-201. `session/prompt` for a `sessionId` the agent never created."""
    async with connected_agent(agent_launch) as agent:
        await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        entry = await _request(
            agent,
            "session/prompt",
            {"sessionId": _UNKNOWN_SESSION_ID, "prompt": _PROMPT},
            timeout=agent_launch.default_timeout,
        )
        assert_unknown_session_error(entry, "session/prompt", _UNKNOWN_SESSION_ID)


@pytest.mark.requirement("ACP-ERROR-201")
@pytest.mark.capability("capabilities.session")
async def test_prompt_closed_session_gets_resource_not_found(agent_launch, tmp_path):
    """ACP-ERROR-201. A session is active only until it is closed, so `session/prompt` naming a
    session this connection already closed gets the same error. A `session/close` that fails
    SKIPs (ACP-CLOSE-201 judges close itself)."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        close_entry = await close_session(agent, session_id, timeout=agent_launch.default_timeout)
        close_msg = close_entry.parsed
        if not (isinstance(close_msg, dict) and "result" in close_msg):
            pytest.skip(f"session/close did not succeed, so no closed session to probe: {close_entry.text!r}")
        entry = await _request(
            agent,
            "session/prompt",
            {"sessionId": session_id, "prompt": _PROMPT},
            timeout=agent_launch.default_timeout,
        )
        assert_unknown_session_error(entry, "session/prompt", session_id)


@pytest.mark.requirement("ACP-ERROR-201")
@pytest.mark.capability("capabilities.session")
async def test_set_config_option_unknown_session_gets_resource_not_found(agent_launch, tmp_path):
    """ACP-ERROR-201. `session/set_config_option` for a never-created session, setting an
    advertised option to its current value so the session is the only thing wrong. Gated on
    `session/new` returning `configOptions`."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/new", {"cwd": str(tmp_path)})
        new_entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(new_entry)
        msg = new_entry.parsed
        result = msg.get("result") if isinstance(msg, dict) else None
        assert isinstance(result, dict), f"session/new did not return a result object: {new_entry.text!r}"
        option = next(
            (
                opt
                for opt in result.get("configOptions") or []
                if isinstance(opt, dict)
                and isinstance(opt.get("configId"), str)
                and "currentValue" in opt
                and opt.get("type") in ("boolean", "select")
            ),
            None,
        )
        if option is None:
            pytest.skip("session/new returned no boolean or select configOptions to name")
        entry = await set_config_option(
            agent,
            _UNKNOWN_SESSION_ID,
            option["configId"],
            type="boolean" if option["type"] == "boolean" else "id",
            value=option["currentValue"],
            timeout=agent_launch.default_timeout,
        )
        assert_unknown_session_error(entry, "session/set_config_option", _UNKNOWN_SESSION_ID)


# --- ACP-ERROR-202: unadvertised capability-gated methods ---

# The baseline methods all hang on `capabilities.session`; the others each have their own marker.
_SESSION_BASELINE = ("session/new", "session/list", "session/resume", "session/close", "session/prompt")
_OTHER_GATED = (
    ("session/delete", "capabilities.session.delete"),
    ("session/fork", "capabilities.session.fork"),
    ("providers/list", "capabilities.providers"),
)


def _gated_params(method: str, session_id: str, cwd) -> dict[str, Any]:
    if method in ("session/list", "providers/list"):
        return {}
    if method == "session/new":
        return {"cwd": str(cwd)}
    if method in ("session/resume", "session/fork"):
        return {"sessionId": session_id, "cwd": str(cwd)}
    if method == "session/prompt":
        return {"sessionId": session_id, "prompt": _PROMPT}
    return {"sessionId": session_id}


@pytest.mark.requirement("ACP-ERROR-202")
async def test_unadvertised_gated_methods_get_method_not_found(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-ERROR-202. Every standard method gated on a capability the agent did not advertise
    gets `-32601`: the `session/*` baseline without `capabilities.session`, `session/delete`
    without `session.delete`, `session/fork` without `session.fork`, `providers/list` without
    `providers`. The gate is inverted -- the test needs what is *not* advertised -- so it is
    computed here instead of by a capability marker. Params are well-formed and name a real
    session when the agent offers sessions at all, so a missing session is not an alternative
    explanation. SKIPs if everything probed is advertised."""
    init_result = agent_initialize_result.result
    if init_result is None:
        pytest.fail(
            f"cannot evaluate advertised capabilities: initialize failed: {agent_initialize_result.error_message}",
            pytrace=False,
        )
    skip_if_version_mismatch(init_result)
    has_session = advertises_session(init_result)
    unadvertised = [] if has_session else list(_SESSION_BASELINE)
    unadvertised += [
        method for method, path in _OTHER_GATED if not capability_is_supported(init_result, path)
    ]
    if not unadvertised:
        pytest.skip("every probed capability-gated method is advertised")
    async with connected_agent(agent_launch) as agent:
        session_id = (
            await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            if has_session
            else _UNKNOWN_SESSION_ID
        )
        problems = []
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
            elif error.get("code") != METHOD_NOT_FOUND:
                note = " (authentication required)" if error.get("code") == AUTHENTICATION_REQUIRED else ""
                problems.append(f"{method}: expected -32601, got {error.get('code')!r}{note}")
    assert not problems, "unadvertised methods should get -32601 -- " + "; ".join(problems)


# --- ACP-ERROR-203: reserved-range codes are ACP-defined ---


def _in_reserved_range(code: int) -> bool:
    return any(low <= code <= high for low, high in _RESERVED_RANGES)


@pytest.mark.requirement("ACP-ERROR-203")
async def test_reserved_range_codes_are_acp_defined(agent_launch, agent_initialize_result):
    """ACP-ERROR-203. Samples the error replies to an unrecognised method and, when
    `capabilities.session` is advertised, a `session/new` missing `cwd` and a `session/prompt`
    for an unknown session; every code in `-32768..-32000` or `-32899..-32800` must be one of
    `ErrorCode`'s named members. A probe the agent leaves unanswered contributes no sample
    (ACP-EXT-001 and ACP-JSONRPC-004 judge that); passes vacuously if no probe yields an error."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    probes: list[tuple[str, dict[str, Any] | None]] = [("_tck/does_not_exist", None)]
    if advertises_session(init_result):
        probes += [
            ("session/new", {}),  # missing required cwd
            ("session/prompt", {"sessionId": _UNKNOWN_SESSION_ID, "prompt": _PROMPT}),
        ]
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


# --- ACP-ERROR-204: the answer to a non-JSON line ---


@pytest.mark.requirement("ACP-ERROR-204")
async def test_parse_error_reply_is_minus_32700_with_null_id(agent_launch, agent_initialize_result):
    """ACP-ERROR-204. After a normal `initialize`, sends a line that is not JSON at all. Silence
    or an exit SKIPs: the spec requires no reply and the probe breaks the client rule against
    non-JSON input (ACP-INFO-PARSE-001 records what happened). A reply must be an error response
    with code `-32700` and `id: null`."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", SPEC.initialize_params())
        await agent.wait_for_response(init_id, timeout=agent_launch.startup_timeout)

        await agent.send_raw(b"{not valid json at all")
        try:
            entry = await next_reply_line(agent, quiet_period(agent_launch.default_timeout))
        except AgentTimeout:
            pytest.skip("agent did not answer the non-JSON line (no rule requires a reply)")
        except AgentExited:
            pytest.skip("agent exited on the non-JSON line (no rule requires a reply)")
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    assert isinstance(error, dict), f"the answer to a non-JSON line should be an error response: {entry.text!r}"
    problems = []
    if error.get("code") != PARSE_ERROR:
        problems.append(f"expected code -32700, got {error.get('code')!r}")
    if msg.get("id", "<absent>") is not None:
        problems.append(f"expected id null, got {msg.get('id', '<absent>')!r}")
    assert not problems, f"answer to a non-JSON line: {'; '.join(problems)} ({entry.text!r})"
