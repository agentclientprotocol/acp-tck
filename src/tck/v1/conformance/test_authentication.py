"""The authentication surface: `authMethods` shape, the terminal-method client-capability
gate, the `authenticate`/`session/new` flow, and `logout` (ACP-AUTH-001..006).

Deliberately not asserted here: that a non-empty `authMethods` implies `session/new` fails with
`-32000` before authentication (v1: MAY, not MUST -- `testy` itself does not enforce it), and
nothing about session state after `logout`.
"""

from __future__ import annotations

import pytest

from tck.common.plugin import current_allow_logout, current_auth_method_id
from tck.v1.protocol import AUTHENTICATION_REQUIRED
from tck.v1.validation import validate_against_def

from ._helpers import connected_agent, skip_if_version_mismatch, unusable_auth_method_reason


@pytest.mark.requirement("ACP-AUTH-001")
async def test_auth_methods_have_unique_ids(agent_initialize_result):
    """ACP-AUTH-001 (ADVISORY -- the schema only describes `id` as unique, it is not a MUST).
    Schema-shape validation is already covered by ACP-SCHEMA-001; this adds the id-uniqueness
    check schema validation can't express.

    Reads the cached `agent_initialize_result` instead of sending a second `initialize` --
    a repeat `initialize` is unspecified in v1 and a strict agent may reject it with -32600."""
    outcome = agent_initialize_result
    assert outcome.result is not None, f"initialize did not succeed: {outcome.error_message}"
    auth_methods = outcome.result.get("authMethods")
    if not auth_methods:
        return  # nothing to check -- vacuously true, per "authMethods (if present)"
    assert isinstance(auth_methods, list)
    # Entries without a string id are a shape problem, left to ACP-SCHEMA-001.
    ids = [
        method.get("id")
        for method in auth_methods
        if isinstance(method, dict) and isinstance(method.get("id"), str)
    ]
    assert len(ids) == len(set(ids)), f"authMethods ids are not unique: {ids!r}"


@pytest.mark.requirement("ACP-AUTH-002")
async def test_no_terminal_auth_method_without_client_capability(agent_launch):
    """ACP-AUTH-002. Connects with `clientCapabilities: {}` explicitly (no `auth.terminal`)
    and asserts no `authMethods[*].type == "terminal"` is advertised."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", {"protocolVersion": 1, "clientCapabilities": {}})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"initialize did not succeed: {entry.text!r}"
        )
        auth_methods = msg["result"].get("authMethods") or []
        terminal_methods = [
            method for method in auth_methods if isinstance(method, dict) and method.get("type") == "terminal"
        ]
        assert not terminal_methods, (
            "agent advertised authMethods[*].type == 'terminal' without the client advertising "
            f"clientCapabilities.auth.terminal: {terminal_methods!r}"
        )


@pytest.mark.requirement("ACP-AUTH-003")
async def test_authenticate_then_session_new_succeeds(agent_launch, tmp_path):
    """ACP-AUTH-003 (CAPABILITY, `capability="inferred:authMethods"`). Only exercised when
    `authMethods` is non-empty AND `--tck-auth-method` names one of its non-terminal entries --
    SKIPs otherwise, since the TCK cannot guess a valid `methodId`, v1 never requires a testable
    auth flow to exist, and a client must not `authenticate` with a `terminal` method.

    `authenticate` succeeding is never asserted -- a real agent may legitimately reject
    bad/expired/cancelled credentials, so an `authenticate` error SKIPs with a distinct reason.
    When it does return a result, the one hard assertion is that a subsequent `session/new` on
    the same connection does not fail with `-32000`."""
    method_id = current_auth_method_id()
    if method_id is None:
        pytest.skip("no --tck-auth-method given; cannot exercise the authenticate flow")

    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", {"protocolVersion": 1, "clientCapabilities": {}})
        init_entry = await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)
        init_msg = init_entry.parsed
        assert isinstance(init_msg, dict) and isinstance(init_msg.get("result"), dict), (
            f"initialize did not succeed: {init_entry.text!r}"
        )
        auth_methods = init_msg["result"].get("authMethods") or []
        if not auth_methods:
            pytest.skip("agent advertises no authMethods; nothing to authenticate against")
        reason = unusable_auth_method_reason(auth_methods, method_id)
        if reason is not None:
            pytest.skip(f"not calling authenticate: {reason}")

        auth_id = await agent.send_request("authenticate", {"methodId": method_id})
        auth_entry = await agent.wait_for_response(auth_id, timeout=agent_launch.default_timeout)
        auth_msg = auth_entry.parsed
        if not (isinstance(auth_msg, dict) and isinstance(auth_msg.get("result"), dict)):
            detail = (auth_msg.get("error") if isinstance(auth_msg, dict) else None) or auth_entry.text
            pytest.skip(f"authenticate with methodId={method_id!r} failed: {detail!r}")
        session_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": []}
        )
        session_entry = await agent.wait_for_response(session_id, timeout=agent_launch.default_timeout)
        session_msg = session_entry.parsed
        # Only "not -32000" is assertable here -- full success shape is already covered
        # elsewhere (ACP-SESSION-001 etc.) for the non-auth-gated path.
        error = session_msg.get("error") if isinstance(session_msg, dict) else None
        assert not (isinstance(error, dict) and error.get("code") == AUTHENTICATION_REQUIRED), (
            f"session/new failed with -32000 (authentication required) after a successful "
            f"authenticate: {session_entry.text!r}"
        )


@pytest.mark.requirement("ACP-AUTH-005")
async def test_session_new_not_gated_when_no_auth_methods_advertised(agent_launch, tmp_path):
    """ACP-AUTH-005 (ADVISORY). If `initialize` advertises no `authMethods` at all,
    `session/new` must not fail with `-32000` -- there would be no defined remedy. Any other
    `session/new` outcome PASSes here; whether it succeeded is ACP-SESSION-001's concern. SKIPs
    when the agent does advertise auth methods (that case is ACP-AUTH-003's territory)."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", {"protocolVersion": 1, "clientCapabilities": {}})
        init_entry = await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)
        init_msg = init_entry.parsed
        assert isinstance(init_msg, dict) and isinstance(init_msg.get("result"), dict), (
            f"initialize did not succeed: {init_entry.text!r}"
        )
        auth_methods = init_msg["result"].get("authMethods") or []
        if auth_methods:
            pytest.skip("agent advertises authMethods; this only concerns the empty case")

        session_id = await agent.send_request(
            "session/new", {"cwd": str(tmp_path), "mcpServers": []}
        )
        entry = await agent.wait_for_response(session_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        assert not (isinstance(error, dict) and error.get("code") == AUTHENTICATION_REQUIRED), (
            "session/new failed with -32000 (authentication required) although initialize "
            f"advertised no authMethods: {entry.text!r}"
        )


@pytest.mark.requirement("ACP-AUTH-006")
async def test_terminal_auth_capability_initialize_validates(agent_launch):
    """ACP-AUTH-006. The only handshake in the suite that advertises `auth.terminal: true`, so
    the only place a conforming agent's `terminal` auth methods are ever schema-validated.
    Never launches the terminal flow, and never passes such a method to `authenticate`.

    `AuthMethod`'s `type` is its discriminator, but the schema's `anyOf` also accepts a
    malformed `type: "terminal"` entry as an `agent` method, so each such entry is validated
    against `AuthMethodTerminal` itself as well. Only the result is judged; the response
    envelope is ACP-JSONRPC-002's concern."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request(
            "initialize",
            {"protocolVersion": 1, "clientCapabilities": {"auth": {"terminal": True}}},
        )
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"initialize did not succeed: {entry.text!r}"
        )
        skip_if_version_mismatch(msg["result"])
        issues: list = validate_against_def("InitializeResponse", msg["result"])
        auth_methods = msg["result"].get("authMethods")
        for index, method in enumerate(auth_methods if isinstance(auth_methods, list) else []):
            if isinstance(method, dict) and method.get("type") == "terminal":
                issues.extend(
                    (f"authMethods/{index}", issue)
                    for issue in validate_against_def("AuthMethodTerminal", method)
                )
        assert not issues, (
            f"initialize result with auth.terminal advertised failed schema validation: {issues!r}"
        )


@pytest.mark.requirement("ACP-AUTH-004")
@pytest.mark.capability("agentCapabilities.auth.logout")
async def test_logout_succeeds(agent_launch):
    """ACP-AUTH-004. If `--tck-auth-method` was given, `connected_agent`'s handshake has
    already authenticated, so `logout` runs on that authenticated connection; otherwise it's
    called standalone. Only its own success is checked, nothing about session state after.

    SKIPs unless `--allow-logout`/`--tck-allow-logout` was given, since calling `logout` for
    real may revoke the operator's own credentials -- mirrors v2's `ACP-AUTH-203`."""
    if not current_allow_logout():
        pytest.skip(
            "logout not exercised: pass --allow-logout (it may revoke the operator's credentials)"
        )
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("logout", {})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"logout did not succeed with an object result: {entry.text!r}"
        )
