"""Extensibility conformance: `ACP-EXT-001`, `ACP-META-001`, `ACP-SCHEMA-002` (re-cited from v1,
unchanged) plus new hygiene rows `ACP-META-201`/`202`/`203`/`204`, `ACP-EXT-201`, `ACP-EXT-202`,
`ACP-EXT-203`, and the receiver rule `ACP-EXT-204` (unknown `initialize` fields are ignored).

`ACP-EXT-001`/`ACP-META-001` are connection-level rows with `capability=None`, matching their v1
registry entries; `ACP-META-001`'s test still carries the `capabilities.session` marker since it
drives an actual `session/prompt` turn. `ACP-EXT-201`/`ACP-EXT-203` need only one notification
exchange to probe, and `ACP-EXT-202` only `initialize`'s own result -- none of the three drive a
turn, so none carries a capability marker.

`ACP-META-201`, `ACP-META-202`, `ACP-META-204` and `ACP-SCHEMA-002` each drive a full
`session/new` + `session/prompt` exchange, so their tests carry
`@pytest.mark.capability("capabilities.session")` even though registry `capability` stays `None`
for them -- the marker only exists so the autouse skip gate doesn't run them against an agent
that never negotiated session support. `ACP-META-203` is CAPABILITY-tier on the same gate.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.v2 import SPEC, validation
from tck.v2.protocol import W3C_META_KEYS, is_namespaced_meta_key, judge_w3c_meta

from ._helpers import (
    connected_agent,
    first_response_within,
    iter_messages,
    new_session,
    quiet_period,
    run_prompt,
    skip_if_version_mismatch,
)

_PROMPT_TEXT = "hi"


@pytest.mark.requirement("ACP-EXT-001")
async def test_unknown_custom_method_receives_a_response(agent_launch):
    """ACP-EXT-001 (MANDATORY, `docs/protocol/v2/draft/extensibility.mdx:165,174,187,231`).
    *Some* response -- a result, or an error with any code -- must arrive for a `_`-prefixed
    custom method; the `-32601` code specifically is `ACP-JSONRPC-004`'s concern, not
    re-checked here."""
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


@pytest.mark.requirement("ACP-META-001")
@pytest.mark.capability("capabilities.session")
async def test_meta_field_on_prompt_is_accepted(agent_launch, tmp_path):
    """ACP-META-001 (ADVISORY, re-cited from v1 unchanged). A `session/prompt` carrying `_meta`
    is still accepted (a normal acceptance receipt arrives) and the turn still reaches a
    terminating idle `state_update` -- v2's response is only an acceptance receipt, so this
    checks the *turn*, not the response, unlike v1's version. Does not check the stopReason's
    validity; that's `ACP-STATE-203`'s unconditional concern."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            extra_params={
                "_meta": {
                    "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
                    "tck": True,
                }
            },
            timeout=agent_launch.default_timeout,
        )

    assert turn.message_id, (
        f"a session/prompt carrying _meta must still receive a normal acceptance receipt: "
        f"{turn.response_entry.text!r}"
    )
    assert turn.idle_update is not None, (
        "a session/prompt carrying _meta must still reach a terminating idle state_update"
    )


@pytest.mark.requirement("ACP-META-201")
@pytest.mark.capability("capabilities.session")
async def test_emitted_meta_is_object_or_null(agent_launch, tmp_path):
    """ACP-META-201 (ADVISORY, new). Every `_meta` the agent emits, anywhere in the transcript,
    is a JSON object or `null` -- never a string/array/number (every `_meta` site in the
    schema is typed `["object", "null"]`, e.g.
    `schema/v2/schema.unstable.json#/$defs/UpdateSessionNotification/properties/_meta`)."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )

    violations: list[Any] = []

    def _scan(node: Any) -> None:
        if isinstance(node, dict):
            if "_meta" in node and node["_meta"] is not None and not isinstance(node["_meta"], dict):
                violations.append(node["_meta"])
            for value in node.values():
                _scan(value)
        elif isinstance(node, list):
            for item in node:
                _scan(item)

    for entry in agent.transcript:
        if entry.direction is Direction.RECEIVED and isinstance(entry.parsed, (dict, list)):
            _scan(entry.parsed)

    assert not violations, f"_meta value(s) that are not an object or null: {violations!r}"


@pytest.mark.requirement("ACP-META-202")
@pytest.mark.capability("capabilities.session")
async def test_non_object_meta_on_prompt_is_treated_as_omitted(agent_launch, tmp_path):
    """ACP-META-202 (ADVISORY, `docs/protocol/v2/draft/extensibility.mdx:74`). `_meta` is an
    object with string keys and "receivers treat any other value as omitted", so a
    `session/prompt` whose `_meta` is a string is accepted and its turn reaches idle (the
    schema marks `PromptRequest._meta` `x-deserialize-default-on-error`). A client never sends
    a non-object `_meta`; the probe breaks that client rule on purpose because the spec defines
    the receiver's answer, and the value is `_tck`-prefixed to make the intent plain."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        turn = await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            extra_params={"_meta": "_tck/not-an-object"},
            timeout=agent_launch.default_timeout,
        )

    assert turn.message_id, (
        "a session/prompt whose _meta is not an object must be treated as if _meta were "
        f"omitted, but it was not accepted: {turn.response_entry.text!r}"
    )
    assert turn.idle_update is not None, (
        "a session/prompt whose _meta is not an object must still reach a terminating idle "
        "state_update"
    )


def _meta_objects(node: Any) -> list[dict[str, Any]]:
    """Every non-null `_meta` object anywhere under `node`."""
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        meta = node.get("_meta")
        if isinstance(meta, dict):
            found.append(meta)
        for value in node.values():
            found.extend(_meta_objects(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_meta_objects(item))
    return found


async def _drive_exchange(agent_launch, tmp_path):
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )
    return agent


@pytest.mark.requirement("ACP-META-203")
@pytest.mark.capability("capabilities.session")
async def test_emitted_w3c_trace_meta_keys_are_well_formed(agent_launch, tmp_path):
    """ACP-META-203 (CAPABILITY, `docs/protocol/v2/draft/extensibility.mdx:97-100`). Wherever
    the agent emits a `_meta` object with a root `traceparent`, `tracestate` or `baggage` key,
    "their values MUST use the corresponding W3C format". `traceparent` is checked against the
    Trace Context grammar (`tck.v2.protocol.is_valid_traceparent`); `tracestate` and `baggage`
    only have to be strings, since their list-member grammars are out of proportion for this
    check. A `null` value is a metadata-patch removal, not a value, and is not judged. SKIPs when the
    agent emits none of the keys."""
    agent = await _drive_exchange(agent_launch, tmp_path)

    seen = 0
    problems: list[str] = []
    for entry in agent.transcript:
        if entry.direction is not Direction.RECEIVED:
            continue
        for msg in iter_messages(entry):
            for meta in _meta_objects(msg):
                meta_seen, meta_problems = judge_w3c_meta(meta)
                seen += meta_seen
                problems += meta_problems

    if seen == 0:
        pytest.skip("the agent emitted no traceparent/tracestate/baggage _meta key")
    assert not problems, f"malformed W3C trace-context _meta value(s): {problems!r}"


def _agent_authored_meta_objects(msg: dict[str, Any]) -> list[dict[str, Any]]:
    """The `_meta` objects `ACP-META-204` judges: the root `_meta` of a result or of request/
    notification params (plus `session/update`'s `update`), and every `_meta` under an
    `initialize` result's `capabilities`. Content blocks and tool output are skipped -- they may
    forward MCP content that keeps MCP's own keys."""
    roots: list[Any] = []
    found: list[dict[str, Any]] = []
    result = msg.get("result")
    params = msg.get("params")
    if isinstance(result, dict):
        roots.append(result)
        found.extend(_meta_objects(result.get("capabilities")))
    elif isinstance(params, dict):
        roots.append(params)
        if msg.get("method") == "session/update":
            roots.append(params.get("update"))
    for root in roots:
        if isinstance(root, dict) and isinstance(root.get("_meta"), dict):
            found.append(root["_meta"])
    return found


@pytest.mark.requirement("ACP-META-204")
@pytest.mark.capability("capabilities.session")
async def test_agent_authored_meta_keys_are_namespaced(agent_launch, tmp_path):
    """ACP-META-204 (ADVISORY, `docs/protocol/v2/draft/extensibility.mdx:102,259`). Unprefixed
    `_meta` keys, and keys whose reverse-DNS prefix has `agentclientprotocol` as its second
    label, are reserved for ACP; ACP defines no unprefixed key beyond the W3C `traceparent`/
    `tracestate`/`baggage`. So every key of an agent-authored `_meta` (positions in
    `_agent_authored_meta_objects`) is one of those three or `<reverse-dns>/<name>`. Only
    agent-authored objects are judged: the TCK's own probe `_meta` goes the other way. SKIPs
    when the agent emits no `_meta` at those positions."""
    agent = await _drive_exchange(agent_launch, tmp_path)

    seen = 0
    offending: set[str] = set()
    for entry in agent.transcript:
        if entry.direction is not Direction.RECEIVED:
            continue
        for msg in iter_messages(entry):
            for meta in _agent_authored_meta_objects(msg):
                for key in meta:
                    seen += 1
                    if key in W3C_META_KEYS or is_namespaced_meta_key(key):
                        continue
                    offending.add(key)

    if seen == 0:
        pytest.skip("the agent emitted no _meta keys at the positions this row judges")
    assert not offending, (
        f"agent-authored _meta key(s) {sorted(offending)!r} are not a reverse-DNS-prefixed "
        "`<prefix>/<name>` (unprefixed and `*.agentclientprotocol/` keys are reserved for ACP)"
    )


@pytest.mark.requirement("ACP-EXT-201")
async def test_unrecognized_custom_notification_produces_no_response(agent_launch):
    """ACP-EXT-201 (ADVISORY). An unrecognized `_`-prefixed *notification* sent to the agent
    produces no response and no crash (SHOULD-ignore, `docs/protocol/v2/draft/extensibility.mdx:231`)
    -- the v2 analogue of v1's `answers_notifications.py` defect pattern, generalised to any
    custom notification rather than specifically `session/cancel`. Only a reply fails this
    (`_helpers.is_response_line`), not the agent's own notifications or requests."""
    async with connected_agent(agent_launch) as agent:
        await agent.send_notification("_tck/ping", {"hello": "world"})
        try:
            entry = await first_response_within(agent, quiet_period(agent_launch.default_timeout))
        except AgentExited:
            pytest.fail("agent exited after receiving an unrecognized custom notification")
        if entry is None:
            return  # no reply -- exactly what SHOULD-ignore predicts
        pytest.fail(
            f"agent responded to an unrecognized `_`-prefixed notification (should be ignored "
            f"silently): {entry.text!r}"
        )


@pytest.mark.requirement("ACP-EXT-202")
async def test_extensions_are_advertised_under_capabilities_meta(agent_launch):
    """ACP-EXT-202 (ADVISORY). Any vendor extension the agent advertises lives under
    `initialize` -> `result.capabilities._meta`, not as a new root key of `capabilities` itself
    (`docs/protocol/v2/draft/extensibility.mdx:253-261`) -- checked via a *nested* application of
    `find_unknown_root_keys` against the `AgentCapabilities` `$def`, rather than the
    whole-response root-level check `ACP-SCHEMA-002` already performs.

    Manual `initialize` (no session follows, so no `login_if_needed` call either -- nothing
    session-dependent comes after it) plus `skip_if_version_mismatch`: `AgentCapabilities`' own
    shape is v2-specific, so a v1-only agent forced under `--protocol-version 2` cannot be
    honestly judged against it."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", SPEC.initialize_params())
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.startup_timeout)

    msg = entry.parsed
    if not (isinstance(msg, dict) and isinstance(msg.get("result"), dict)):
        pytest.skip("initialize did not succeed; nothing to check here (ACP-INIT-001 owns this)")
    skip_if_version_mismatch(msg["result"])
    capabilities = msg["result"].get("capabilities")
    if not isinstance(capabilities, dict):
        pytest.skip("initialize result has no capabilities object to check")

    extras = validation.find_unknown_root_keys("AgentCapabilities", capabilities)
    assert not extras, (
        f"initialize result.capabilities has unrecognized root key(s) {extras!r} -- vendor "
        "extensions must be advertised under capabilities._meta instead"
    )


@pytest.mark.requirement("ACP-EXT-204")
async def test_unknown_initialize_fields_are_ignored(agent_launch):
    """ACP-EXT-204 (MANDATORY; initialization.mdx:156, extensibility.mdx:51-52,157). `initialize` with
    unknown fields at the `capabilities` root, under `capabilities.auth`, and in `info` must not
    be rejected, and "Unknown fields do not advertise support": `auth.tckFutureAuthMode` is not
    `auth.terminal`, so no `type: "terminal"` auth method may appear. The names are deliberately
    not `_`-prefixed: they stand in for fields of a future ACP revision (a `_` name would be a
    custom capability, which extensibility.mdx:261 forbids at these positions)."""
    params = SPEC.initialize_params()
    params = {
        **params,
        "info": {**params["info"], "tckFutureField": 1},
        "capabilities": {"tckFutureCapability": {}, "auth": {"tckFutureAuthMode": {}}},
    }
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", params)
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)

    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"initialize with unknown capability/info fields must not be rejected: {entry.text!r}"
    )
    skip_if_version_mismatch(msg["result"])
    terminal = [
        method
        for method in msg["result"].get("authMethods") or []
        if isinstance(method, dict) and method.get("type") == "terminal"
    ]
    assert not terminal, (
        "an unknown capabilities.auth field advertised terminal auth support: "
        f"{terminal!r}"
    )


@pytest.mark.requirement("ACP-EXT-203")
async def test_unrecognized_protocol_level_notification_produces_no_response(agent_launch):
    """ACP-EXT-203 (ADVISORY). An unrecognized `$/`-prefixed protocol-level notification sent to
    the agent produces no response and no crash (SHOULD-ignore,
    `docs/protocol/v2/draft/extensibility.mdx:165,231`, `docs/protocol/v2/draft/error.mdx:44`):
    `$/` names are reserved for protocol-level messages, so `$/does_not_exist` stands in for one
    from a later ACP version. The schema's `ProtocolLevel` description ("free to ignore") agrees.
    The probe uses a name no ACP version defines, which a client would never send. Like
    `ACP-EXT-201`, only a reply fails this (`_helpers.is_response_line`), not the agent's own
    notifications or requests."""
    async with connected_agent(agent_launch) as agent:
        await agent.send_notification("$/does_not_exist", {})
        try:
            entry = await first_response_within(agent, quiet_period(agent_launch.default_timeout))
        except AgentExited:
            pytest.fail("agent exited after receiving an unrecognized `$/`-prefixed notification")
        if entry is None:
            return  # no reply -- exactly what SHOULD-ignore predicts
        pytest.fail(
            f"agent responded to an unrecognized `$/`-prefixed notification (should be ignored "
            f"silently): {entry.text!r}"
        )


@pytest.mark.requirement("ACP-SCHEMA-002")
@pytest.mark.capability("capabilities.session")
async def test_full_exchange_has_no_unknown_root_keys(agent_launch, tmp_path):
    """ACP-SCHEMA-002 (ADVISORY, re-cited from v1; needs a v2 carve-out --
    `tck.v2.validation.find_unknown_root_keys` already skips detection for any object matched by
    an open `"other"`-titled fallback branch, since an unknown/`_`-prefixed variant is by
    construction not "a type that's part of the specification",
    `docs/protocol/v2/draft/extensibility.mdx:104`). Swept over an ordinary
    initialize -> session/new -> session/prompt exchange, same trick as v1's version of this
    test: derive `method_by_id` from the SENT transcript to resolve each response's own method.
    Unwraps every transcript line via `iter_messages` rather than requiring
    `isinstance(entry.parsed, dict)`: a message delivered inside an array line (itself an
    `ACP-TRANSPORT-201` violation) must not silently escape this scan."""
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            timeout=agent_launch.default_timeout,
        )

    method_by_id: dict[Any, str] = {}
    for entry in agent.transcript:
        if entry.direction is not Direction.SENT:
            continue
        for msg in iter_messages(entry):
            if "method" in msg and "id" in msg:
                method_by_id[msg["id"]] = msg["method"]

    response_defs = validation._response_method_defs()
    request_and_notification_defs = validation._request_and_notification_method_defs()

    unknown: list[str] = []
    for entry in agent.transcript:
        if entry.direction is not Direction.RECEIVED:
            continue
        for msg in iter_messages(entry):
            method = msg.get("method")
            if isinstance(method, str):
                if method.startswith("_") or method.startswith("$/"):
                    continue  # extension/protocol methods carry no fixed shape by design
                is_request = "id" in msg
                def_name = request_and_notification_defs.get(
                    (method, is_request)
                ) or request_and_notification_defs.get((method, not is_request))
                if def_name is not None:
                    extras = validation.find_unknown_root_keys(def_name, msg.get("params"))
                    if extras:
                        unknown.append(f"{method} params: {extras}")
                continue

            if "result" in msg:
                response_method = method_by_id.get(msg.get("id"))
                def_name = response_defs.get(response_method) if response_method is not None else None
                if def_name is not None:
                    extras = validation.find_unknown_root_keys(def_name, msg.get("result"))
                    if extras:
                        unknown.append(f"{response_method} result: {extras}")

    assert not unknown, f"unknown root-level key(s) found: {unknown!r}"
