"""`initialize` handshake conformance: ACP-INIT-001, ACP-INIT-003, ACP-INIT-201..215,
ACP-SCHEMA-001 (see `tck.v2.requirements`'s module docstring for the id-namespacing decisions).

Version negotiation (initialization.mdx:108-112): the agent selects the highest version it
supports that is <= the requested one, rejects with `-32022` when there is none, and answers a
malformed `protocolVersion` with `-32602`. A failed `initialize` leaves the connection
uninitialized and can be retried, and `initialize` may be repeated before any other request
(initialization.mdx:90-92,135-141); the probes that do not depend on such state still run in
their own process, and the ones that do (`ACP-INIT-209`..`215`) deliberately reuse a connection
after a failed or repeated `initialize`.

`ACP-INIT-201`/`003`/`202`/`208` judge the negotiation outcome only, so they hold for a legacy
v1-only agent too and carry the `negotiation` marker (they still run if the main handshake is
rejected with `-32022`). `ACP-INIT-205`/`206`/`207` and `209`..`215` are obligations of agents
that implement v2 (a v1-only agent "may not accept a repeated `initialize`",
initialization.mdx:141), so they SKIP with `VERSION-MISMATCH:` unless the main handshake
selected 2 and carry no `negotiation` marker.
"""

from __future__ import annotations

import contextlib
from typing import Any

from tck.common.harness import AgentExited, AgentTimeout, Direction
from tck.v2 import SPEC
from tck.v2.protocol import (
    INVALID_PARAMS,
    INVALID_REQUEST,
    PROTOCOL_VERSION,
    UNSUPPORTED_PROTOCOL_VERSION,
)
from tck.v2.validation import find_non_object_markers, validate_agent_message, validate_agent_response

import pytest

from ._helpers import (
    connected_agent,
    drain_quiet,
    iter_messages,
    login_if_needed,
    new_session,
    quiet_period,
    run_prompt,
    skip_if_version_mismatch,
)

# A v1 `initialize` request: no `info` (the migration guide's "v1 request without Client
# identity"), v1's `clientCapabilities` name.
_V1_SHAPED_PARAMS = {"protocolVersion": 1, "clientCapabilities": {}}

# v2-only root keys of an `initialize` result; v1's are `agentInfo`/`agentCapabilities`.
_V2_ONLY_RESULT_KEYS = ("info", "capabilities")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _selected_version(msg: Any) -> int | None:
    """The integer `protocolVersion` a successful `initialize` reply selected, else `None`."""
    result = msg.get("result") if isinstance(msg, dict) else None
    version = result.get("protocolVersion") if isinstance(result, dict) else None
    return version if _is_int(version) else None


def _error_code(msg: Any) -> Any:
    error = msg.get("error") if isinstance(msg, dict) else None
    return error.get("code") if isinstance(error, dict) else None


async def _initialize_once(agent_launch, params: dict[str, Any]):
    """Send one `initialize` with `params` to a fresh process; return the reply entry."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", params)
        return await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)


def _skip_unless_v2_endpoint(agent_initialize_result) -> None:
    """INIT-205/206/207 bind agents that implement v2; a legacy v1-only agent is exempt."""
    assert agent_initialize_result.result is not None, (
        f"initialize did not succeed: {agent_initialize_result.error_message}"
    )
    skip_if_version_mismatch(agent_initialize_result.result)


def _unsupported_version_data_issues(error: dict[str, Any], requested: int) -> list[str]:
    """Problems with a `-32022` error's `data` (initialization.mdx:112): an object with
    non-null `requested` (the requested version) and `supported` (an array of versions). Since
    nothing in `supported` may be <= `requested` (the agent would have selected it), and the
    caller has seen this agent select 2, `supported` must also contain 2."""
    data = error.get("data")
    if not isinstance(data, dict):
        return [f"data must be an object, got {data!r}"]
    issues = []
    if not (_is_int(data.get("requested")) and data["requested"] == requested):
        issues.append(f"data.requested must be {requested}, got {data.get('requested')!r}")
    supported = data.get("supported")
    if not (isinstance(supported, list) and all(_is_int(v) for v in supported)):
        issues.append(f"data.supported must be an array of integer versions, got {supported!r}")
        return issues
    if any(v <= requested for v in supported):
        issues.append(
            f"data.supported {supported!r} lists a version <= {requested}, which the agent "
            "should have selected instead of rejecting"
        )
    if PROTOCOL_VERSION not in supported:
        issues.append(
            f"data.supported {supported!r} omits {PROTOCOL_VERSION}, which this agent selects "
            f"for a protocolVersion={PROTOCOL_VERSION} request"
        )
    return issues


@pytest.mark.requirement("ACP-INIT-001")
async def test_initialize_succeeds(agent_launch):
    """ACP-INIT-001. Only checks the basic handshake succeeds (non-error result); this holds
    even for an agent that negotiates down to a version other than 2, so unlike the v2-only
    shape checks below, this test never SKIPs on such a downgrade. (A `-32022` rejection of the
    main handshake SKIPs it via `tck.common.plugin`'s version-rejection gate.) Shape validation of
    the result lives in `ACP-SCHEMA-001`/`ACP-INIT-203`/`ACP-INIT-204` instead.
    """
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", SPEC.initialize_params())
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and "result" in msg, f"initialize did not succeed: {msg!r}"


@pytest.mark.requirement("ACP-INIT-201")
@pytest.mark.negotiation
async def test_selects_highest_supported_version_at_or_below_request(agent_launch):
    """ACP-INIT-201 (initialization.mdx:110). Two probes: request 2 (selects A) and request
    65535 (selects H, the agent's highest supported version). A MUST NOT exceed 2, and when
    H <= 2 the agent's highest version at or below 2 is H, so A MUST equal H. An error to the
    65535 probe is `ACP-INIT-003`'s concern; only the first half is judged then.

    A `-32022` to the request of 2 is correct for an agent with no version <= 2, unless the
    65535 probe then selects one."""
    entry_a = await _initialize_once(agent_launch, SPEC.initialize_params())
    entry_b = await _initialize_once(agent_launch, {**SPEC.initialize_params(), "protocolVersion": 65535})
    version_b = _selected_version(entry_b.parsed)

    if _error_code(entry_a.parsed) == UNSUPPORTED_PROTOCOL_VERSION:
        assert version_b is None or version_b > PROTOCOL_VERSION, (
            f"initialize(protocolVersion={PROTOCOL_VERSION}) was rejected with -32022, yet "
            f"initialize(protocolVersion=65535) selected {version_b!r}, a version <= "
            f"{PROTOCOL_VERSION}"
        )
        return

    msg_a = entry_a.parsed
    assert isinstance(msg_a, dict) and isinstance(msg_a.get("result"), dict), (
        f"initialize(protocolVersion={PROTOCOL_VERSION}) did not return a result object: "
        f"{entry_a.text!r}"
    )
    version_a = msg_a["result"].get("protocolVersion")
    assert _is_int(version_a), f"protocolVersion must be an integer, got {version_a!r}"
    assert version_a <= PROTOCOL_VERSION, (
        f"initialize(protocolVersion={PROTOCOL_VERSION}) selected {version_a!r}: a successful "
        "response MUST NOT select a version higher than the requested one"
    )
    if version_b is not None and version_b <= PROTOCOL_VERSION:
        assert version_a == version_b, (
            f"initialize(protocolVersion=65535) selected {version_b!r}, so that is the agent's "
            f"highest supported version, and a request for {PROTOCOL_VERSION} must select it "
            f"too -- got {version_a!r}"
        )


@pytest.mark.requirement("ACP-INIT-003")
@pytest.mark.negotiation
async def test_version_above_every_supported_one_selects_the_highest(agent_launch):
    """ACP-INIT-003 (reused from v1 -- see `tck.v2.requirements`'s module docstring). 65535 is
    an in-range `ProtocolVersion` (uint16) above every real version, so the agent MUST select its
    highest supported version: neither `-32602` nor `-32022` is allowed, the request must not be
    echoed, and the answer is at least what the same agent selects for a request of 2. When the
    reference request of 2 is rejected with `-32022`, only the reference comparison is
    skipped."""
    ref_entry = await _initialize_once(agent_launch, SPEC.initialize_params())
    ref_msg = ref_entry.parsed
    latest_supported = None
    if _error_code(ref_msg) != UNSUPPORTED_PROTOCOL_VERSION:
        assert isinstance(ref_msg, dict) and isinstance(ref_msg.get("result"), dict), (
            f"initialize(protocolVersion={PROTOCOL_VERSION}) did not return a result object: "
            f"{ref_entry.text!r}"
        )
        latest_supported = ref_msg["result"].get("protocolVersion")
        assert _is_int(latest_supported), (
            f"reference agent's protocolVersion is not an integer: {latest_supported!r}"
        )

    entry = await _initialize_once(agent_launch, {**SPEC.initialize_params(), "protocolVersion": 65535})
    msg = entry.parsed
    assert isinstance(msg, dict) and "result" in msg, (
        "initialize(protocolVersion=65535) must select the agent's highest supported version "
        f"(65535 is in range, so neither -32602 nor -32022 applies), got {msg!r}"
    )
    version = msg["result"].get("protocolVersion")
    assert _is_int(version), f"protocolVersion must be an integer, got {version!r}"
    assert version != 65535, (
        "protocolVersion must not echo the client's requested version 65535 verbatim -- it must "
        "be the agent's own highest supported version"
    )
    if latest_supported is not None:
        assert version >= latest_supported, (
            f"protocolVersion for a request of 65535 ({version!r}) must be at least the version "
            f"the same agent selects for a request of {PROTOCOL_VERSION} ({latest_supported!r})"
        )


@pytest.mark.requirement("ACP-INIT-202")
@pytest.mark.negotiation
async def test_v1_request_selects_v1_or_is_rejected_with_unsupported_version(agent_launch):
    """ACP-INIT-202 (initialization.mdx:108,110,112). A v1-shaped `initialize(1)` is answered
    either with a result selecting a version <= 1 (a dual-stack or v1 agent), or with `-32022`
    (a v2-only agent). Selecting 2 or higher, or any other error, FAILs. The `-32022` `data`
    shape is `ACP-INIT-205`'s concern."""
    entry = await _initialize_once(agent_launch, _V1_SHAPED_PARAMS)
    msg = entry.parsed
    assert isinstance(msg, dict), f"initialize(protocolVersion=1) reply is not an object: {entry.text!r}"
    if "result" in msg:
        version = msg["result"].get("protocolVersion") if isinstance(msg["result"], dict) else None
        assert _is_int(version), f"protocolVersion must be an integer, got {version!r}"
        assert version <= 1, (
            f"initialize(protocolVersion=1) selected {version!r}: a successful response MUST NOT "
            "select a version higher than the requested one -- an agent without v1 must reject "
            "with -32022 instead"
        )
        return
    code = _error_code(msg)
    assert code != INVALID_PARAMS, (
        "initialize(protocolVersion=1) was answered with -32602, but 1 is a well-formed, in-range "
        "version; -32602 is reserved for a malformed protocolVersion, and an unsupported one gets "
        f"-32022: {entry.text!r}"
    )
    assert code == UNSUPPORTED_PROTOCOL_VERSION, (
        "initialize(protocolVersion=1) must select a version <= 1 or be rejected with -32022, "
        f"got {entry.text!r}"
    )


@pytest.mark.requirement("ACP-INIT-205")
async def test_unsupported_version_error_carries_requested_and_supported(
    agent_launch, agent_initialize_result
):
    """ACP-INIT-205 (initialization.mdx:112-127). `initialize(0)` has no supported version at or
    below it unless the agent supports 0, so it MUST either select 0 or be rejected with
    `-32022` whose `data` carries `requested: 0` and the `supported` versions. Any `-32022` to a
    v1-shaped `initialize(1)` is held to the same `data` shape with `requested: 1`."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    issues: list[str] = []

    try:
        entry = await _initialize_once(agent_launch, {**SPEC.initialize_params(), "protocolVersion": 0})
    except (AgentExited, AgentTimeout) as exc:
        pytest.fail(
            f"initialize(protocolVersion=0) got no reply ({exc}); an unsupported version MUST be "
            "rejected with a -32022 response",
            pytrace=False,
        )
    selected = _selected_version(entry.parsed)
    if selected is not None:
        assert selected <= 0, (
            f"initialize(protocolVersion=0) selected {selected!r}: a successful response MUST "
            "NOT select a version higher than the requested one"
        )
    else:
        assert _error_code(entry.parsed) == UNSUPPORTED_PROTOCOL_VERSION, (
            "initialize(protocolVersion=0) must select 0 or be rejected with -32022, got "
            f"{entry.text!r}"
        )
        issues += [f"protocolVersion=0: {i}" for i in _unsupported_version_data_issues(entry.parsed["error"], 0)]

    try:
        v1_entry = await _initialize_once(agent_launch, _V1_SHAPED_PARAMS)
    except (AgentExited, AgentTimeout):
        v1_entry = None  # no reply to the v1 request is `ACP-INIT-202`'s FAIL
    if v1_entry is not None and _error_code(v1_entry.parsed) == UNSUPPORTED_PROTOCOL_VERSION:
        issues += [f"protocolVersion=1: {i}" for i in _unsupported_version_data_issues(v1_entry.parsed["error"], 1)]

    assert not issues, f"malformed -32022 error data: {issues!r}"


# `protocolVersion` values that are missing, non-integer, or outside uint16's 0..65535. `2.0` is
# deliberately absent: JSON Schema treats it as an integer.
_MALFORMED_PROTOCOL_VERSIONS: tuple[tuple[str, Any], ...] = (
    ("omitted", None),
    ('the string "2"', "2"),
    ("null", None),
    ("-1", -1),
    ("65536", 65536),
)


@pytest.mark.requirement("ACP-INIT-206")
async def test_malformed_protocol_version_gets_invalid_params(agent_launch, agent_initialize_result):
    """ACP-INIT-206 (initialization.mdx:108). A missing, non-integer, or out-of-range
    `protocolVersion` MUST receive `-32602` -- never a result, and not `-32022`, which is for
    well-formed versions the agent does not support."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    failures: list[str] = []
    for label, value in _MALFORMED_PROTOCOL_VERSIONS:
        params = dict(SPEC.initialize_params())
        if label == "omitted":
            del params["protocolVersion"]
        else:
            params["protocolVersion"] = value
        try:
            entry = await _initialize_once(agent_launch, params)
        except (AgentExited, AgentTimeout) as exc:
            failures.append(f"protocolVersion {label}: no reply ({type(exc).__name__})")
            continue
        if _error_code(entry.parsed) != INVALID_PARAMS:
            failures.append(f"protocolVersion {label}: {entry.text!r}")
    assert not failures, f"malformed protocolVersion not answered with -32602: {failures!r}"


@pytest.mark.requirement("ACP-INIT-207")
async def test_no_session_work_after_unsupported_version(agent_launch, agent_initialize_result, tmp_path):
    """ACP-INIT-207 (initialization.mdx:129). "A version-mismatch error does not initialize the
    connection": after `initialize(0)` is rejected with `-32022`, a `session/new` on the same
    connection must not succeed, and the agent must not start session work on its own. The TCK
    deliberately keeps the connection open (the client's SHOULD-close) to observe this. An error,
    silence, or the agent exiting all PASS. SKIPs when no `-32022` is observed."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    quiet = quiet_period(agent_launch.default_timeout)
    async with connected_agent(agent_launch, handshake=False) as agent:
        init_id = await agent.send_request("initialize", {**SPEC.initialize_params(), "protocolVersion": 0})
        try:
            entry = await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)
        except (AgentExited, AgentTimeout):
            entry = None  # no reply at all is `ACP-INIT-205`'s FAIL, not this row's
        if entry is None or _error_code(entry.parsed) != UNSUPPORTED_PROTOCOL_VERSION:
            pytest.skip("initialize(protocolVersion=0) was not rejected with -32022; nothing to check")
        mark = len(agent.transcript)
        new_id = await agent.send_request("session/new", {"cwd": str(tmp_path)})
        with contextlib.suppress(AgentExited):
            await drain_quiet(agent, quiet)

    violations: list[str] = []
    for line in agent.transcript[mark:]:
        if line.direction is not Direction.RECEIVED:
            continue
        for msg in iter_messages(line):
            method = msg.get("method")
            if isinstance(method, str) and method.startswith(("session/", "elicitation/")):
                violations.append(f"agent-initiated {method}: {line.text!r}")
            elif msg.get("id") == new_id and isinstance(msg.get("result"), dict) and "sessionId" in msg["result"]:
                violations.append(f"session/new succeeded: {line.text!r}")
    assert not violations, (
        f"the agent began session work on a connection it rejected with -32022: {violations!r}"
    )


@pytest.mark.requirement("ACP-INIT-208")
@pytest.mark.negotiation
async def test_v1_selection_uses_the_v1_response_shape(agent_launch):
    """ACP-INIT-208 (initialization.mdx:110: "MUST use the selected version's initialization
    response shape"). When a v1-shaped `initialize(1)` selects 1, the result must not carry
    v2's root `info`/`capabilities` (v1 names them `agentInfo`/`agentCapabilities`). SKIPs when
    the agent does not select 1."""
    entry = await _initialize_once(agent_launch, _V1_SHAPED_PARAMS)
    if _selected_version(entry.parsed) != 1:
        pytest.skip("initialize(protocolVersion=1) did not select 1; nothing to check")
    present = [key for key in _V2_ONLY_RESULT_KEYS if key in entry.parsed["result"]]
    assert not present, (
        f"initialize selected protocolVersion 1 but its result carries v2-only key(s) "
        f"{present!r}: {entry.text!r}"
    )


@pytest.mark.requirement("ACP-INIT-203")
async def test_info_is_required_and_well_formed(agent_launch):
    """ACP-INIT-203. `info` is REQUIRED in the v2 `initialize` result (unlike v1's optional
    `agentInfo`), and its `name`/`version` are strings.

    This is a v2-only shape requirement: an agent that honestly negotiates down to a version
    other than 2 never claimed to speak v2 in the first place, so its
    result cannot be judged against v2's own `info` requirement -- `skip_if_version_mismatch`
    SKIPs with the `VERSION-MISMATCH:` marker in that case instead of FAILing.
    """
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", SPEC.initialize_params())
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"initialize did not return a result object: {entry.text!r}"
        )
        skip_if_version_mismatch(msg["result"])
        info = msg["result"].get("info")
        assert isinstance(info, dict), f"info is required in v2 but missing/not an object: {info!r}"
        name = info.get("name")
        version = info.get("version")
        # The schema requires only strings (`Implementation`); emptiness is not judged.
        assert isinstance(name, str), f"info.name must be a string, got {name!r}"
        assert isinstance(version, str), f"info.version must be a string, got {version!r}"


@pytest.mark.requirement("ACP-INIT-204")
async def test_capabilities_markers_are_objects_not_booleans(agent_launch):
    """ACP-INIT-204. `capabilities`, when present, is an object whose object-typed marker
    properties (derived from `schema/v2/schema.unstable.json#/$defs/AgentCapabilities`, recursively)
    are themselves objects (or absent/`null`) -- never booleans. Non-object fields are not judged.

    Also a v2-only shape requirement, so `skip_if_version_mismatch` SKIPs it with the
    `VERSION-MISMATCH:` marker whenever the agent negotiated down to a version other than 2 --
    see `test_info_is_required_and_well_formed` (`ACP-INIT-203`) above for the rationale.
    """
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", SPEC.initialize_params())
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"initialize did not return a result object: {entry.text!r}"
        )
        skip_if_version_mismatch(msg["result"])
        capabilities = msg["result"].get("capabilities")
        if capabilities is None:
            return
        assert isinstance(capabilities, dict), (
            f"capabilities must be an object when present, got {capabilities!r}"
        )
        bad = find_non_object_markers("AgentCapabilities", capabilities)
        assert not bad, (
            "capability markers must be objects (or absent/null), never booleans or other "
            f"scalars, but got non-objects at: {bad!r} in {capabilities!r}"
        )


@pytest.mark.requirement("ACP-SCHEMA-001")
async def test_initialize_exchange_validates_against_schema(agent_launch, tmp_path):
    """ACP-SCHEMA-001. Extends beyond the `initialize` exchange alone to also drive a
    `session/new` + `session/prompt` turn on the same connection (mirrors
    `tck.v1.conformance.test_initialize.test_full_exchange_validates_against_schema`'s "full
    exchange" scope). `method_by_id` is derived by scanning the SENT transcript rather than
    threaded by hand, so it picks up `session/new`/`session/prompt` alongside `initialize` for
    free.

    The session/prompt-turn portion only runs when the negotiated result actually advertises
    `capabilities.session` (an object marker, checked manually here rather than via
    `@pytest.mark.capability(...)` -- this test manages its own connection instead of sharing
    the marker-gated `agent_initialize_result` fixture) -- an agent that never advertises
    `session` support has no `session/new`/`session/prompt` traffic to validate at all, and this
    row still validates whatever the bare `initialize` exchange produced.

    Validating against the *v2* schema is itself a v2-only shape requirement -- a v1-shaped
    result (`agentInfo` instead of `info`, etc.) from an agent that honestly negotiated down to
    a version other than 2 would otherwise misleadingly FAIL here even though the agent simply
    does not speak v2 yet, so `skip_if_version_mismatch` SKIPs with the `VERSION-MISMATCH:`
    marker in that case instead.
    """
    async with connected_agent(agent_launch, handshake=False) as agent:
        req_id = await agent.send_request("initialize", SPEC.initialize_params())
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"initialize did not return a result object: {entry.text!r}"
        )
        skip_if_version_mismatch(msg["result"])

        capabilities = msg["result"].get("capabilities")
        if isinstance(capabilities, dict) and capabilities.get("session") is not None:
            await login_if_needed(agent, timeout=agent_launch.default_timeout)
            session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            await run_prompt(
                agent,
                session_id,
                [{"type": "text", "text": "hi"}],
                timeout=agent_launch.default_timeout,
            )

    method_by_id: dict[Any, str] = {}
    for entry in agent.transcript:
        msg = entry.parsed
        if entry.direction is Direction.SENT and isinstance(msg, dict) and "method" in msg and "id" in msg:
            method_by_id[msg["id"]] = msg["method"]

    received = [entry for entry in agent.transcript if entry.direction is Direction.RECEIVED]

    # A received line may itself be an array (non-conformant, `ACP-TRANSPORT-201` judges it,
    # e.g. `emits_batch_updates.py`) -- flatten to individual message dicts before validating,
    # rather than hard-failing on the first list-shaped line.
    messages: list[dict[str, Any]] = []
    for entry in received:
        msg = entry.parsed
        if isinstance(msg, list):
            for item in msg:
                assert isinstance(item, dict), (
                    f"non-object array element from the agent: {item!r} in {entry.raw!r}"
                )
                messages.append(item)
        else:
            assert isinstance(msg, dict), f"non-object line from the agent: {entry.raw!r}"
            messages.append(msg)

    issues = []
    for msg in messages:
        if "method" in msg:
            issues.extend(validate_agent_message(msg))
            continue
        method = method_by_id.get(msg.get("id"))
        if method is not None:
            issues.extend(validate_agent_response(method, msg))
        else:
            issues.extend(validate_agent_message(msg))

    assert not issues, f"schema violations in agent output: {issues!r}"


# --- Initialization state: before, retry, repeat (initialization.mdx:86-92,135-141) ---

# `initialize` params that fail without initializing the connection. `-32022` comes from
# `protocolVersion: 0`, which no agent that ever selects 2 supports (see `ACP-INIT-205`).
_NO_PROTOCOL_VERSION = {k: v for k, v in SPEC.initialize_params().items() if k != "protocolVersion"}
_UNSUPPORTED_PROTOCOL_VERSION_PARAMS = {**SPEC.initialize_params(), "protocolVersion": 0}

# An unknown, `_`-prefixed request. The TCK's own probes keep to the extensibility rule even when
# they break a client rule (here: sending a request in a state the spec gives the agent an answer
# for), so the answer is `-32601` on an initialized connection and `-32600` on an uninitialized one.
_PROBE_METHOD = "_tck/after_initialize"


async def _request_or_fail(agent, launch, method: str, params: dict[str, Any] | None, what: str):
    """Send one request and return its reply entry; no reply (silence or exit) is a FAIL."""
    try:
        req_id = await agent.send_request(method, params)
        return await agent.wait_for_response(req_id, timeout=launch.default_timeout)
    except (AgentExited, AgentTimeout) as exc:
        pytest.fail(f"{what}: no reply ({type(exc).__name__})", pytrace=False)


def _is_error(entry) -> bool:
    return isinstance(entry.parsed, dict) and "error" in entry.parsed


@pytest.mark.requirement("ACP-INIT-209")
async def test_request_before_initialize_gets_invalid_request(
    agent_launch, agent_initialize_result, tmp_path
):
    """ACP-INIT-209 (error.mdx:29,60; initialization.mdx:90). `session/new` -- a standard
    method, so the only thing wrong with it is the connection state -- is sent on three
    connections: a fresh one, one after an `initialize` without `protocolVersion`, and one after
    `initialize(0)`. Each MUST answer `-32600`. A leg whose `initialize` is not rejected has no
    uninitialized connection to judge and is skipped. The "ignore notifications" half is
    silence, covered by `ACP-JSONRPC-003`."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    legs: tuple[tuple[str, dict[str, Any] | None], ...] = (
        ("on a fresh connection", None),
        ("after initialize without protocolVersion", _NO_PROTOCOL_VERSION),
        ("after initialize(protocolVersion=0)", _UNSUPPORTED_PROTOCOL_VERSION_PARAMS),
    )
    failures: list[str] = []
    for label, init_params in legs:
        async with connected_agent(agent_launch, handshake=False) as agent:
            if init_params is not None:
                init_entry = await _request_or_fail(agent, agent_launch, "initialize", init_params, label)
                if not _is_error(init_entry):
                    continue  # initialized after all: `ACP-INIT-205`/`206` judge that
            entry = await _request_or_fail(
                agent, agent_launch, "session/new", {"cwd": str(tmp_path)}, f"session/new {label}"
            )
        if _error_code(entry.parsed) != INVALID_REQUEST:
            failures.append(f"session/new {label}: {entry.text!r}")
    assert not failures, f"a request before initialization completes must get -32600: {failures!r}"


def _method_messages(agent, start: int = 0, stop: int | None = None) -> list[str]:
    """Raw text of every agent line in transcript positions `start`..`stop` that carries a
    `method` (a request or notification the agent initiated)."""
    return [
        line.text
        for line in agent.transcript[start:stop]
        if line.direction is Direction.RECEIVED
        and any("method" in msg for msg in iter_messages(line))
    ]


@pytest.mark.requirement("ACP-INIT-210")
async def test_agent_sends_nothing_while_uninitialized(agent_launch, agent_initialize_result):
    """ACP-INIT-210 (initialization.mdx:88,91). The agent MUST NOT send a request or notification
    before initialization completes. Three observations: nothing during a quiet period at
    startup and nothing before the first successful `initialize` response; nothing in a quiet
    period after an `initialize` without `protocolVersion`; and the same after `initialize(0)`.
    An agent that exits after a failed `initialize` PASSes that leg."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    quiet = quiet_period(agent_launch.default_timeout)
    violations: list[str] = []

    async with connected_agent(agent_launch, handshake=False) as agent:
        with contextlib.suppress(AgentExited):
            await drain_quiet(agent, quiet)
        init_id = await agent.send_request("initialize", SPEC.initialize_params())
        reply = await agent.wait_for_response(init_id, timeout=agent_launch.default_timeout)
    reply_index = next(i for i, line in enumerate(agent.transcript) if line is reply)
    violations += [
        f"before the initialize response: {text!r}" for text in _method_messages(agent, stop=reply_index)
    ]

    for label, params in (
        ("after initialize without protocolVersion", _NO_PROTOCOL_VERSION),
        ("after initialize(protocolVersion=0)", _UNSUPPORTED_PROTOCOL_VERSION_PARAMS),
    ):
        async with connected_agent(agent_launch, handshake=False) as agent:
            entry = await _request_or_fail(agent, agent_launch, "initialize", params, label)
            if not _is_error(entry):
                continue
            mark = len(agent.transcript)
            with contextlib.suppress(AgentExited):
                await drain_quiet(agent, quiet)
        violations += [f"{label}: {t!r}" for t in _method_messages(agent, mark)]

    assert not violations, f"the agent sent messages on an uninitialized connection: {violations!r}"


async def _assert_initialized(agent, launch, what: str) -> None:
    """The connection is initialized iff an unknown request gets its own error rather than
    `-32600` ("not initialized")."""
    entry = await _request_or_fail(agent, launch, _PROBE_METHOD, None, f"{_PROBE_METHOD} {what}")
    assert _error_code(entry.parsed) != INVALID_REQUEST, (
        f"{what}: an unknown request was answered -32600, as if the connection were not "
        f"initialized: {entry.text!r}"
    )


@pytest.mark.requirement("ACP-INIT-211")
async def test_failed_initialize_can_be_retried(agent_launch, agent_initialize_result):
    """ACP-INIT-211 (initialization.mdx:92). An `initialize` without `protocolVersion` fails with
    `-32602`; a corrected `initialize(2)` on the same connection then succeeds, and the connection
    is initialized (an unknown `_tck/...` request is not answered `-32600`). The retry is only
    tried after `-32602`, never after `-32022`, which asks the client to close the connection
    (initialization.mdx:129); an `initialize` that is not rejected with `-32602` leaves nothing
    to retry (`ACP-INIT-206` judges it) and SKIPs."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    async with connected_agent(agent_launch, handshake=False) as agent:
        first = await _request_or_fail(agent, agent_launch, "initialize", _NO_PROTOCOL_VERSION, "first initialize")
        if _error_code(first.parsed) != INVALID_PARAMS:
            pytest.skip("initialize without protocolVersion was not rejected with -32602; nothing to retry")
        retry = await _request_or_fail(agent, agent_launch, "initialize", SPEC.initialize_params(), "retried initialize")
        assert _selected_version(retry.parsed) == PROTOCOL_VERSION, (
            f"a corrected initialize after a failed one must succeed selecting {PROTOCOL_VERSION}, "
            f"got {retry.text!r}"
        )
        await _assert_initialized(agent, agent_launch, "after the retried initialize")


@pytest.mark.requirement("ACP-INIT-212")
async def test_initialize_repeated_before_other_requests_is_handled_like_the_first(
    agent_launch, agent_initialize_result
):
    """ACP-INIT-212 (initialization.mdx:139). After a successful `initialize(2)`, two repeated
    `initialize(2)` (each awaited before the next) get a result selecting 2. A following repeat
    without `protocolVersion` fails, and "A repeat that fails leaves the previous successful
    initialization in effect": an unknown `_tck/...` request is not answered `-32600`. A repeat
    that is not rejected leaves that last check nothing to judge (`ACP-INIT-206`) and ends the
    test there."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    async with connected_agent(agent_launch, handshake=False) as agent:
        for n in (1, 2, 3):
            entry = await _request_or_fail(
                agent, agent_launch, "initialize", SPEC.initialize_params(), f"initialize #{n}"
            )
            assert _selected_version(entry.parsed) == PROTOCOL_VERSION, (
                f"initialize #{n} (a repeat before any other request) must succeed selecting "
                f"{PROTOCOL_VERSION}, got {entry.text!r}"
            )
        failed = await _request_or_fail(
            agent, agent_launch, "initialize", _NO_PROTOCOL_VERSION, "failing repeat of initialize"
        )
        if not _is_error(failed):
            return
        await _assert_initialized(agent, agent_launch, "after a repeated initialize failed")


async def _initialize_after_request(agent_launch):
    """`initialize(2)`, an unknown `_tck/...` request (any outcome), then `initialize(2)`
    again; returns the last reply entry. The first `initialize` and the in-between request are
    awaited, so the repeat is unambiguously "after another request". No reply to the repeat
    is a FAIL; a missing reply to the in-between request is `ACP-JSONRPC-201`'s concern."""
    async with connected_agent(agent_launch, handshake=False) as agent:
        await _request_or_fail(agent, agent_launch, "initialize", SPEC.initialize_params(), "initialize")
        probe_id = await agent.send_request(_PROBE_METHOD)
        with contextlib.suppress(AgentExited, AgentTimeout):
            await agent.wait_for_response(probe_id, timeout=agent_launch.default_timeout)
        return await _request_or_fail(
            agent, agent_launch, "initialize", SPEC.initialize_params(), "initialize repeated after another request"
        )


@pytest.mark.requirement("ACP-INIT-213")
async def test_initialize_repeated_after_another_request_is_rejected(agent_launch, agent_initialize_result):
    """ACP-INIT-213 (error.mdx:29,60; initialization.mdx:139). An `initialize` sent after another
    request ("any request": here an unknown `_`-prefixed method, answered `-32601` by a
    conforming agent) MUST be rejected: a result FAILs. The TCK deliberately breaks the client's
    MUST NOT here, as `ACP-INIT-206` does with malformed versions. The exact code is
    `ACP-INIT-215`'s."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    entry = await _initialize_after_request(agent_launch)
    assert _is_error(entry), (
        f"an initialize repeated after another request must be rejected, got {entry.text!r}"
    )


@pytest.mark.requirement("ACP-INIT-215")
async def test_initialize_repeated_after_another_request_gets_invalid_request(
    agent_launch, agent_initialize_result
):
    """ACP-INIT-215 (ADVISORY; error.mdx:29,60). The rejection of an `initialize` repeated after
    another request carries `-32600`. A reply that is not an error is `ACP-INIT-213`'s FAIL and
    SKIPs here."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    try:
        entry = await _initialize_after_request(agent_launch)
    except pytest.fail.Exception:
        pytest.skip("no reply to the repeated initialize (ACP-INIT-213 judges it)")
    if not _is_error(entry):
        pytest.skip("the repeated initialize was not rejected (ACP-INIT-213 judges it)")
    assert _error_code(entry.parsed) == INVALID_REQUEST, (
        f"an initialize repeated after another request should be rejected with -32600, got {entry.text!r}"
    )


@pytest.mark.requirement("ACP-INIT-214")
async def test_unparseable_params_of_a_newer_version_request_are_ignored(
    agent_launch, agent_initialize_result
):
    """ACP-INIT-214 (initialization.mdx:131). `initialize(65535)` with `capabilities: 42` (not an
    object, so unparseable under the version the agent selects) MUST NOT be rejected: the agent
    ignores what it cannot parse and answers with a result. The selected version is
    `ACP-INIT-003`'s concern. Only `capabilities` is made unparseable: whether a missing or
    malformed required field such as `info` also counts is arguable."""
    _skip_unless_v2_endpoint(agent_initialize_result)
    params = {**SPEC.initialize_params(), "protocolVersion": 65535, "capabilities": 42}
    entry = await _initialize_once(agent_launch, params)
    assert isinstance(entry.parsed, dict) and "result" in entry.parsed, (
        "initialize requesting a newer version with unparseable `capabilities` must be answered "
        f"with a result, not rejected: {entry.text!r}"
    )
