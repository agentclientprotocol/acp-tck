"""The v2 authentication surface: `authMethods` shape, the terminal-method client-capability
gate, the `auth/login`/`auth/logout`/`session/new` flow, and the open-enum `type` rule
(ACP-AUTH-001..006/206/208/210), plus the unstable `auth/status` query (ACP-AUTH-007/008).

v2 renames v1's `authenticate`/`logout` to `auth/login`/`auth/logout` and drops the separate
`agentCapabilities.auth.logout` marker. Ids shared with v1 name the same rule; the `2xx` ids are
v2-only rules.

Deliberately not asserted: that non-empty `authMethods` implies `session/new` fails with
`-32000` before authentication (a MAY, not a MUST); session state after `auth/logout`; that
`auth/login`/`auth/logout` themselves succeed (a real agent may legitimately reject
bad/expired credentials -- that SKIPs with a diagnosable reason instead of FAILing).

The `auth/login` probe for an unadvertised `methodId` (ACP-AUTH-208/210) deliberately breaks the
client rule to send only advertised ids: the spec defines the agent's answer
(`authentication.mdx:191`). It uses a `_tck`-prefixed id that cannot collide with an agent's own
and never targets a `terminal` id (a bold client MUST NOT, `authentication.mdx:176,217-218`).
"""

from __future__ import annotations

import contextlib

import pytest

from tck.common.plugin import current_allow_logout, current_auth_method_id, skip_if_login_times_out

from .. import SPEC
from ..protocol import (
    AUTH_STATES,
    AUTHENTICATION_REQUIRED,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    is_valid_open_enum_value,
)
from ..validation import validate_agent_response
from ._helpers import (
    advertises_session,
    connected_agent,
    new_session,
    skip_if_version_mismatch,
    validate_login_method_id,
)


@contextlib.asynccontextmanager
async def _initialized_agent(agent_launch, *, capabilities=None):
    """A fresh connection with a manual `initialize` (optional `capabilities` override), SKIPping
    with `VERSION-MISMATCH:` unless the agent negotiated v2. Kept local rather than shared,
    since these tests need `handshake=False` to control `auth/login` timing relative to their
    own SKIP checks. Yields `(agent, init_result)`.
    """
    async with connected_agent(agent_launch, handshake=False) as agent:
        params = SPEC.initialize_params()
        if capabilities is not None:
            params = {**params, "capabilities": capabilities}
        req_id = await agent.send_request("initialize", params)
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.startup_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"initialize did not succeed: {entry.text!r}"
        )
        skip_if_version_mismatch(msg["result"])
        yield agent, msg["result"]


@pytest.mark.requirement("ACP-AUTH-001")
async def test_auth_methods_have_unique_method_ids(agent_initialize_result):
    """ACP-AUTH-001 (MANDATORY: "Each `methodId` MUST be unique within the list",
    `authentication.mdx:51`). Schema-shape
    validation of `authMethods` is already covered by ACP-SCHEMA-001; this adds the
    id-uniqueness check schema validation alone can't express. Uses the cached
    `agent_initialize_result` rather than a second connection -- the handshake result is already on
    hand."""
    outcome = agent_initialize_result
    assert outcome.result is not None, f"initialize did not succeed: {outcome.error_message}"
    skip_if_version_mismatch(outcome.result)
    auth_methods = outcome.result.get("authMethods")
    if not auth_methods:
        # Nothing to check here -- record it as a SKIP, not a vacuous PASS.
        pytest.skip("agent advertises no authMethods")
    assert isinstance(auth_methods, list)
    method_ids = [method.get("methodId") for method in auth_methods if isinstance(method, dict)]
    assert len(method_ids) == len(set(method_ids)), f"authMethods methodIds are not unique: {method_ids!r}"


@pytest.mark.requirement("ACP-AUTH-206")
async def test_auth_method_type_is_a_defined_or_prefixed_value(agent_initialize_result):
    """ACP-AUTH-206 (MANDATORY, new in v2). Every `authMethods[*].type` is `"agent"`,
    `"terminal"`, or begins with `_` -- the general open-enum extensibility rule applied to this
    field (`docs/protocol/v2/draft/authentication.mdx:118-120`)."""
    outcome = agent_initialize_result
    assert outcome.result is not None, f"initialize did not succeed: {outcome.error_message}"
    skip_if_version_mismatch(outcome.result)
    auth_methods = outcome.result.get("authMethods") or []
    if not auth_methods:
        # A vacuous PASS is more misleading than a SKIP for a MANDATORY row (SKIPPED doesn't
        # block conformance; FAIL/NOT_TESTED do).
        pytest.skip("agent advertises no authMethods")
    defined = frozenset({"agent", "terminal"})
    for method in auth_methods:
        if not isinstance(method, dict):
            continue
        type_value = method.get("type")
        assert is_valid_open_enum_value(type_value, defined), (
            f"authMethods entry has an unrecognized, non-`_`-prefixed type: {method!r}"
        )


@pytest.mark.requirement("ACP-AUTH-002")
async def test_no_terminal_auth_method_without_client_capability(agent_launch):
    """ACP-AUTH-002 (MANDATORY: "Agents MUST NOT advertise a `terminal` method unless this
    capability is present", `authentication.mdx:149-151`). Connects with no
    `capabilities.auth.terminal` (the default v2 handshake omits it entirely) and asserts no
    `authMethods[*].type == "terminal"` is advertised."""
    async with _initialized_agent(agent_launch) as (agent, init_result):
        auth_methods = init_result.get("authMethods") or []
        terminal_methods = [
            method for method in auth_methods if isinstance(method, dict) and method.get("type") == "terminal"
        ]
        assert not terminal_methods, (
            "agent advertised authMethods[*].type == 'terminal' without the client advertising "
            f"capabilities.auth.terminal: {terminal_methods!r}"
        )


@pytest.mark.requirement("ACP-AUTH-006")
async def test_terminal_auth_method_descriptor_shape(agent_launch):
    """ACP-AUTH-006 (MANDATORY). On a dedicated connection that
    *does* advertise `capabilities.auth.terminal: {}`, every `type: "terminal"` entry's `args`
    (if present) is an array of strings, `env` (if present) is an array of well-formed
    `EnvVariable` objects, and `env` names are unique within that descriptor ("Names MUST be
    unique", `schema/v2/schema.unstable.json#/$defs/AuthMethodTerminal`). Conditional on at least one
    terminal entry actually appearing -- SKIPs otherwise, since there is nothing to check."""
    async with _initialized_agent(agent_launch, capabilities={"auth": {"terminal": {}}}) as (agent, init_result):
        auth_methods = init_result.get("authMethods") or []
        terminal_methods = [
            method for method in auth_methods if isinstance(method, dict) and method.get("type") == "terminal"
        ]
        if not terminal_methods:
            pytest.skip("agent advertises no type=='terminal' authMethods entry; nothing to check")
        for method in terminal_methods:
            args = method.get("args")
            if args is not None:
                assert isinstance(args, list) and all(isinstance(a, str) for a in args), (
                    f"terminal authMethods entry's args must be an array of strings: {method!r}"
                )
            env = method.get("env")
            if env is not None:
                assert isinstance(env, list), f"terminal authMethods entry's env must be an array: {method!r}"
                names = []
                for var in env:
                    assert (
                        isinstance(var, dict)
                        and isinstance(var.get("name"), str)
                        and isinstance(var.get("value"), str)
                    ), f"env entry is not a well-formed EnvVariable (name/value both required strings): {var!r}"
                    names.append(var["name"])
                assert len(names) == len(set(names)), f"terminal authMethods entry's env names are not unique: {names!r}"


@pytest.mark.requirement("ACP-AUTH-003")
async def test_login_then_session_new_succeeds(agent_launch, tmp_path):
    """ACP-AUTH-003 (CAPABILITY, `capability="inferred:authMethods"`; v1's `authenticate` is
    renamed `auth/login`). SKIPs unless `authMethods`
    is non-empty and `--tck-auth-method` was given (the TCK cannot guess a `methodId`), or if
    `validate_login_method_id` rejects an unadvertised/terminal id.

    `auth/login` succeeding is not a hard requirement -- an agent may legitimately reject
    bad/expired credentials, which SKIPs with a diagnosable reason instead of failing. But
    `-32601` FAILs: an agent advertising `authMethods` MUST implement `auth/login`
    (authentication.mdx:51-53), and so does `-32602` for an advertised `type: "agent"` entry
    (`authentication.mdx:191`: `-32602` is for an id that is not an advertised login method; a
    custom `_`-prefixed type may legitimately answer it, so that SKIPs). After a successful login, a `session/new` on the same connection
    (only when `capabilities.session` is advertised) must not fail with `-32000`.

    The `--tck-auth-method` check happens inside `_initialized_agent`, after the
    version-mismatch check has already had a chance to fire, so a version-mismatched agent
    SKIPs with `VERSION-MISMATCH:` rather than an unrelated reason."""
    async with _initialized_agent(agent_launch) as (agent, init_result):
        method_id = current_auth_method_id()
        if method_id is None:
            pytest.skip("no --tck-auth-method given; cannot exercise the auth/login flow")

        auth_methods = init_result.get("authMethods") or []
        if not auth_methods:
            pytest.skip("agent advertises no authMethods; nothing to authenticate against")
        method = validate_login_method_id(auth_methods, method_id)

        login_id = await agent.send_request("auth/login", {"methodId": method_id})
        with skip_if_login_times_out("auth/login", method_id, agent_launch.default_timeout):
            login_entry = await agent.wait_for_response(login_id, timeout=agent_launch.default_timeout)
        login_msg = login_entry.parsed
        if not (isinstance(login_msg, dict) and isinstance(login_msg.get("result"), dict)):
            error = login_msg.get("error") if isinstance(login_msg, dict) else None
            code = error.get("code") if isinstance(error, dict) else None
            assert code != METHOD_NOT_FOUND, (
                "agent advertises authMethods but answered auth/login with -32601 (Method not "
                f"found): {login_entry.text!r}"
            )
            assert not (code == INVALID_PARAMS and method.get("type") == "agent"), (
                f"auth/login for the advertised type 'agent' method {method_id!r} was answered "
                "-32602 (Invalid params), which is for an id that is not an advertised login "
                f"method: {login_entry.text!r}"
            )
            pytest.skip(f"auth/login with methodId={method_id!r} failed: {error or login_entry.text!r}")

        if not advertises_session(init_result):
            return
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        assert isinstance(session_id, str) and session_id


@pytest.mark.requirement("ACP-AUTH-005")
async def test_session_new_not_gated_when_no_auth_methods_advertised(agent_launch, tmp_path):
    """ACP-AUTH-005 (ADVISORY; `schema.mdx:954` is a MAY). If `initialize` advertises no
    `authMethods` at all, `session/new` must not fail with `-32000` -- there would be no
    defined remedy. SKIPs when the agent does advertise auth methods (that case is
    ACP-AUTH-003's territory), or does not advertise `capabilities.session`."""
    async with _initialized_agent(agent_launch) as (agent, init_result):
        auth_methods = init_result.get("authMethods") or []
        if auth_methods:
            pytest.skip("agent advertises authMethods; AUTH-005 only concerns the empty case")
        if not advertises_session(init_result):
            pytest.skip("capability 'capabilities.session' not advertised by the agent under test")

        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        assert isinstance(session_id, str)


_UNADVERTISED_METHOD_ID = "_tck_unadvertised_method"


async def _login_with_unadvertised_method(agent_launch) -> dict | None:
    """Send `auth/login` with a `methodId` that is not advertised, on a fresh connection that has
    not logged in. SKIPs when no `authMethods` are advertised (or one is the probe id). Returns
    the parsed response (`None` if it was not a JSON object)."""
    async with _initialized_agent(agent_launch) as (agent, init_result):
        auth_methods = init_result.get("authMethods") or []
        if not auth_methods:
            pytest.skip("agent advertises no authMethods; auth/login is not advertised")
        advertised = {m.get("methodId") for m in auth_methods if isinstance(m, dict)}
        if _UNADVERTISED_METHOD_ID in advertised:
            pytest.skip(f"agent advertises the probe methodId {_UNADVERTISED_METHOD_ID!r}")
        login_id = await agent.send_request("auth/login", {"methodId": _UNADVERTISED_METHOD_ID})
        entry = await agent.wait_for_response(login_id, timeout=agent_launch.default_timeout)
        return entry.parsed if isinstance(entry.parsed, dict) else None


@pytest.mark.requirement("ACP-AUTH-208")
async def test_login_with_unadvertised_method_id_is_rejected(agent_launch):
    """ACP-AUTH-208 (CAPABILITY, `capability="inferred:authMethods"`). `auth/login` with a
    `methodId` that is not advertised is rejected with an error, not answered with a result
    (`authentication.mdx:191`). The probe breaks the client rule to send only an advertised id on
    purpose: the spec defines the agent's answer. Only error-vs-result is asserted: the sentence
    naming `-32602` carries no RFC keyword, so the code is ACP-AUTH-210's (ADVISORY) concern."""
    msg = await _login_with_unadvertised_method(agent_launch)
    assert msg is not None and isinstance(msg.get("error"), dict), (
        f"auth/login with an unadvertised methodId was not rejected with an error: {msg!r}"
    )


@pytest.mark.requirement("ACP-AUTH-210")
async def test_unadvertised_method_id_rejection_code_is_invalid_params(agent_launch):
    """ACP-AUTH-210 (ADVISORY). The rejection of `auth/login` for an unadvertised `methodId` is
    `-32602` (`authentication.mdx:191`; no RFC keyword, hence ADVISORY). SKIPs when the probe was
    not rejected: that is ACP-AUTH-208's failure, not a second one."""
    msg = await _login_with_unadvertised_method(agent_launch)
    error = msg.get("error") if msg is not None else None
    if not isinstance(error, dict):
        pytest.skip(f"auth/login with an unadvertised methodId was not rejected: {msg!r}")
    assert error.get("code") == INVALID_PARAMS, (
        f"auth/login with an unadvertised methodId was rejected with {error.get('code')!r}, "
        f"expected -32602 (Invalid params): {msg!r}"
    )


async def _fresh_auth_status(agent_launch) -> tuple[dict | None, str]:
    """Send `auth/status` on a fresh connection that never logs in (even with `--auth-method`:
    `_initialized_agent` runs a manual `initialize` on a `handshake=False` connection, so no
    login step). Returns the parsed response and its raw text. `auth/status` is a pure query
    that never changes the agent's authentication."""
    async with _initialized_agent(agent_launch) as (agent, _init_result):
        req_id = await agent.send_request("auth/status", {})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        return (msg if isinstance(msg, dict) else None), entry.text


@pytest.mark.requirement("ACP-AUTH-007")
@pytest.mark.capability("capabilities.auth.status")
async def test_auth_status_succeeds_before_login(agent_launch, agent_initialize_result):
    """ACP-AUTH-007 (CAPABILITY, `capability="capabilities.auth.status"`; unstable). `auth/status`
    right after `initialize`, with no `auth/login`, returns a result that validates as
    `AuthStatusResponse`. An error is a FAIL, `-32000` (auth-gated) and `-32601` (advertised, yet
    not found) above all. Not run through `skip_if_auth_gated`: the method exists to be
    answerable while unauthenticated."""
    assert agent_initialize_result.result is not None, (
        f"initialize did not succeed: {agent_initialize_result.error_message}"
    )
    skip_if_version_mismatch(agent_initialize_result.result)
    msg, text = await _fresh_auth_status(agent_launch)
    error = msg.get("error") if msg is not None else None
    if isinstance(error, dict):
        code = error.get("code")
        if code == AUTHENTICATION_REQUIRED:
            raise AssertionError(
                "auth/status was rejected with -32000 (authentication required) before logging "
                f"in; it is how a client learns whether authentication is needed: {text!r}"
            )
        if code == METHOD_NOT_FOUND:
            raise AssertionError(f"auth/status was advertised but answered -32601: {text!r}")
        raise AssertionError(f"auth/status returned an error instead of a result: {text!r}")
    assert msg is not None and "result" in msg, f"auth/status returned no result: {text!r}"
    issues = validate_agent_response("auth/status", msg)
    assert not issues, f"auth/status result failed AuthStatusResponse validation: {issues!r}"


@pytest.mark.requirement("ACP-AUTH-008")
@pytest.mark.capability("capabilities.auth.status")
async def test_auth_status_state_is_defined_or_underscore_prefixed(
    agent_launch, agent_initialize_result
):
    """ACP-AUTH-008 (CAPABILITY, `capability="capabilities.auth.status"`; unstable). The `state`
    of an unauthenticated `auth/status` result is a defined `AuthState` value or `_`-prefixed
    (other strings are reserved for future ACP variants). SKIPs when the call yields no string
    `state`: that is ACP-AUTH-007's failure, not a second one."""
    assert agent_initialize_result.result is not None, (
        f"initialize did not succeed: {agent_initialize_result.error_message}"
    )
    skip_if_version_mismatch(agent_initialize_result.result)
    msg, text = await _fresh_auth_status(agent_launch)
    result = msg.get("result") if msg is not None else None
    state = result.get("state") if isinstance(result, dict) else None
    if not isinstance(state, str):
        pytest.skip(f"auth/status returned no string state to judge: {text!r}")
    assert is_valid_open_enum_value(state, AUTH_STATES), (
        f"auth/status state {state!r} is neither a defined value ({sorted(AUTH_STATES)}) nor "
        f"`_`-prefixed; other strings are reserved for future ACP variants: {text!r}"
    )


@pytest.mark.requirement("ACP-AUTH-004")
@pytest.mark.revokes("auth", reason="auth/logout may drop credentials other tests rely on")
async def test_logout_succeeds(agent_launch):
    """ACP-AUTH-004 (CAPABILITY, `capability="inferred:authMethods"`, since v2 has no
    `agentCapabilities.auth.logout` marker). SKIPs when
    the agent advertises no `authMethods`, or unless `--allow-logout`/`--tck-allow-logout` was
    given, since a real `auth/logout` may revoke the operator's own credentials.

    If `--tck-auth-method` was given, logs in first (gated by the same `validate_login_method_id`
    check as ACP-AUTH-003, so an unadvertised/terminal id SKIPs rather than sending a
    spec-forbidden `auth/login`). Only `auth/logout`'s own success (a schema-valid object
    result) is checked -- nothing about session state after logout."""
    async with _initialized_agent(agent_launch) as (agent, init_result):
        auth_methods = init_result.get("authMethods") or []
        if not auth_methods:
            pytest.skip("agent advertises no authMethods; nothing to log out of")
        if not current_allow_logout():
            pytest.skip(
                "auth/logout not exercised: pass --allow-logout (it may revoke the operator's "
                "credentials)"
            )

        method_id = current_auth_method_id()
        if method_id is not None:
            validate_login_method_id(auth_methods, method_id)
            login_id = await agent.send_request("auth/login", {"methodId": method_id})
            with skip_if_login_times_out("auth/login", method_id, agent_launch.default_timeout):
                login_entry = await agent.wait_for_response(login_id, timeout=agent_launch.default_timeout)
            login_msg = login_entry.parsed
            if not (isinstance(login_msg, dict) and isinstance(login_msg.get("result"), dict)):
                detail = (login_msg.get("error") if isinstance(login_msg, dict) else None) or login_entry.text
                pytest.skip(f"auth/login with methodId={method_id!r} failed: {detail!r}")

        logout_id = await agent.send_request("auth/logout", {})
        logout_entry = await agent.wait_for_response(logout_id, timeout=agent_launch.default_timeout)
        logout_msg = logout_entry.parsed
        assert isinstance(logout_msg, dict) and isinstance(logout_msg.get("result"), dict), (
            f"auth/logout did not succeed with an object result: {logout_entry.text!r}"
        )
