"""Extensibility conformance: ACP-EXT-001, ACP-EXT-002, ACP-META-001, ACP-SCHEMA-002."""

from __future__ import annotations

import contextlib
from typing import Any

import pytest

from tck.v1 import validation
from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.v1.protocol import STOP_REASONS

from ._helpers import connected_agent, new_session, quiet_period, run_prompt, skip_if_version_mismatch


@pytest.mark.requirement("ACP-EXT-001")
async def test_unknown_custom_method_receives_a_response(agent_launch):
    """ACP-EXT-001 (MANDATORY). Custom requests must get a response
    (extensibility.mdx:69, and JSON-RPC 2.0's request/response rule), separate from the
    "should" on which error *code* an unrecognised method gets (ACP-JSONRPC-004). Only asserts
    *some* response arrives for a `_`-prefixed method.

    Catches `AgentTimeout`/`AgentExited` explicitly so a non-responding agent fails with a
    protocol-level message rather than a bare harness exception."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("_tck/unknown")
        try:
            entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        except (AgentTimeout, AgentExited) as exc:
            pytest.fail(
                f"a `_`-prefixed custom method request must receive a response: {exc}",
                pytrace=False,
            )
        msg = entry.parsed
        assert isinstance(msg, dict) and ("result" in msg or "error" in msg), (
            f"a `_`-prefixed custom method request must receive a response, got {msg!r}"
        )


@pytest.mark.requirement("ACP-EXT-002")
async def test_unknown_custom_notification_is_ignored(agent_launch, tmp_path):
    """ACP-EXT-002 (ADVISORY). After an unrecognized `_`-prefixed notification, `session/new`
    still succeeds. A reply to the notification is ACP-JSONRPC-003's concern, not this test's."""
    async with connected_agent(agent_launch) as agent:
        await agent.send_notification("_tck/notify", {})
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        assert isinstance(session_id, str)


@pytest.mark.requirement("ACP-META-001")
async def test_prompt_meta_field_is_accepted(agent_launch, agent_initialize_result, tmp_path):
    """ACP-META-001 (ADVISORY). A `session/prompt` carrying `_meta` with a `traceparent` key
    (reserved for trace context) must be accepted and resolve normally.

    `skip_if_version_mismatch` first, since a v1-shaped `session/prompt` result can't be
    judged against an agent that never negotiated v1."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": "hello"}],
            extra_params={
                "_meta": {
                    "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
                    "tck": True,
                }
            },
            timeout=agent_launch.default_timeout,
        )

    msg = turn.response_entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"a session/prompt carrying _meta must still resolve normally: {turn.response_entry.text!r}"
    )
    stop_reason = msg["result"].get("stopReason")
    assert stop_reason in STOP_REASONS, f"unexpected stopReason with _meta present: {stop_reason!r}"


@pytest.mark.requirement("ACP-SCHEMA-002")
async def test_full_exchange_has_no_unknown_root_keys(agent_launch, agent_initialize_result, tmp_path):
    """ACP-SCHEMA-002 (ADVISORY -- implementations MUST NOT add custom root fields to a spec
    type, `_meta` is for custom data instead). The vendored schema has no
    `additionalProperties: false` anywhere, so mandatory schema validation (ACP-SCHEMA-001)
    can't catch this on its own -- `validation.find_unknown_root_keys` resolves each `$def`'s
    full property union (following `allOf`/`anyOf`/`oneOf`/`$ref`) and flags any key outside
    it, for every agent-emitted request/notification `params` and response `result`; error
    objects go through `validation.find_unknown_error_keys` (no `_meta` allowed there).

    Swept over the same initialize -> session/new -> session/prompt exchange as
    `test_initialize.py::test_full_exchange_validates_against_schema`, reusing its
    `method_by_id`-from-transcript trick and `skip_if_version_mismatch` guard, plus two
    requests that provoke errors: an unknown `_`-prefixed method and a `session/new` missing
    `cwd`. Neither reply is required here; their waits are bounded and a missing reply only
    means no error-object sample."""
    if agent_initialize_result.result is not None:
        skip_if_version_mismatch(agent_initialize_result.result)
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": "hello"}],
            timeout=agent_launch.default_timeout,
        )
        unknown_id = await agent.send_request("_tck/does_not_exist")
        with contextlib.suppress(AgentTimeout):
            await agent.wait_for_response(unknown_id, timeout=quiet_period(agent_launch.default_timeout))
        bad_id = await agent.send_request("session/new", {"mcpServers": []})  # missing required cwd
        with contextlib.suppress(AgentTimeout):
            await agent.wait_for_response(bad_id, timeout=agent_launch.default_timeout)

    method_by_id: dict[Any, str] = {}
    for entry in agent.transcript:
        msg = entry.parsed
        if entry.direction is Direction.SENT and isinstance(msg, dict) and "method" in msg and "id" in msg:
            method_by_id[msg["id"]] = msg["method"]

    response_defs = validation._response_method_defs()
    request_and_notification_defs = validation._request_and_notification_method_defs()

    unknown: list[str] = []
    for entry in agent.transcript:
        if entry.direction is not Direction.RECEIVED:
            continue
        msg = entry.parsed
        if not isinstance(msg, dict):
            continue

        method = msg.get("method")
        if isinstance(method, str):
            if method.startswith("_"):
                continue  # extension methods carry no fixed shape by design
            def_name = request_and_notification_defs.get(method)
            if def_name is not None:
                extras = validation.find_unknown_root_keys(def_name, msg.get("params"))
                if extras:
                    unknown.append(f"{method} params: {extras}")
            continue

        error = msg.get("error")
        if isinstance(error, dict):
            extras = validation.find_unknown_error_keys(error)
            if extras:
                unknown.append(f"error object (id={msg.get('id')!r}): {extras}")

        if "result" in msg:
            response_method = method_by_id.get(msg.get("id"))
            def_name = response_defs.get(response_method) if response_method is not None else None
            if def_name is not None:
                extras = validation.find_unknown_root_keys(def_name, msg.get("result"))
                if extras:
                    unknown.append(f"{response_method} result: {extras}")

    assert not unknown, f"unknown root-level key(s) found: {unknown!r}"
