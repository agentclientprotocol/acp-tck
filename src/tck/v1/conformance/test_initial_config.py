"""Initial config option values: ACP-OPTIONS-004..008, -010 and -011.

An agent that advertises `sessionCapabilities.options` accepts a `configOptions` list of
`{configId, value}` entries on `session/new` (and load/resume). Every row is gated on that
capability (the TCK may not send entries otherwise, `session-config-options.mdx:475`), and every
test judges its own fresh connection. The entries come from `session/options` of the same agent:
a select option with an alternative value for the rows that apply one, a real id for the duplicate
probe. Probes are `session/new` requests, repeated by ACP-OPTIONS-004..006 and -008 as
`session/fork` requests (of a plain session made on the same connection) when
`sessionCapabilities.fork` is advertised (a fork that fails even without entries is not probed);
ACP-OPTIONS-006 also repeats its unknown-id probe on `session/load` and `session/resume` when
advertised. `type: "boolean"` entries are only sent, and boolean options only seen, on a connection
that advertises `clientCapabilities.session.configOptions.boolean` (the docs and schema
descriptions call the gate `sessionCapabilities.configOptions.boolean`, a path that does not
exist).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tck.common.harness import Direction
from tck.common.plugin import capability_is_supported
from tck.v1.protocol import INVALID_PARAMS
from tck.v1.validation import validate_agent_response

from ._helpers import (
    connected_agent,
    drain,
    flatten_select_values,
    quiet_period,
    session_update_kind,
    skip_if_auth_gated,
    skip_if_auth_required,
)

_OPTIONS_PATH = "agentCapabilities.sessionCapabilities.options"
_FORK_PATH = "agentCapabilities.sessionCapabilities.fork"
_BOOLEAN_CLIENT = {"session": {"configOptions": {"boolean": {}}}}
_UNKNOWN_ID = "acp-tck-unknown-option"
_NOT_A_VALUE = "acp-tck-not-a-value"


def _error_code(entry) -> Any:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return error.get("code") if isinstance(error, dict) else None


def _result(entry) -> dict[str, Any] | None:
    msg = entry.parsed
    result = msg.get("result") if isinstance(msg, dict) else None
    return result if isinstance(result, dict) else None


async def _call(agent, method: str, params: dict[str, Any], *, timeout: float):
    req_id = await agent.send_request(method, params)
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    if method == "session/new":
        skip_if_auth_gated(entry)
    skip_if_auth_required(entry, method)
    return entry


async def _new_with_entries(agent, cwd: Path, entries: Any, *, timeout: float):
    return await _call(
        agent, "session/new", {"cwd": str(cwd), "mcpServers": [], "configOptions": entries}, timeout=timeout
    )


async def _fork_with_entries(agent, cwd: Path, source_id: str, entries: Any, *, timeout: float):
    params = {"sessionId": source_id, "cwd": str(cwd), "mcpServers": [], "configOptions": entries}
    return await _call(agent, "session/fork", params, timeout=timeout)


async def _source_session(agent, cwd: Path, *, timeout: float) -> str:
    """A plain `session/new` to fork from. Its failure FAILs the row: the agent cannot set up the
    session the fork probes need."""
    entry = await _call(agent, "session/new", {"cwd": str(cwd), "mcpServers": []}, timeout=timeout)
    result = _result(entry)
    session_id = result.get("sessionId") if result is not None else None
    assert isinstance(session_id, str), f"session/new for the session/fork probes failed: {entry.text!r}"
    return session_id


async def _setup_targets(agent, cwd: Path, init_result: Any, *, timeout: float) -> list[tuple[str, str | None]]:
    """`(method, source sessionId)` for each setup request the probes go to: `session/new`, and
    `session/fork` of a fresh session when `sessionCapabilities.fork` is advertised and a plain fork
    of that session succeeds. A fork that fails without entries is not the entries' fault, so it
    is left out rather than FAILing the probes."""
    targets: list[tuple[str, str | None]] = [("session/new", None)]
    if init_result is not None and capability_is_supported(init_result, _FORK_PATH):
        source_id = await _source_session(agent, cwd, timeout=timeout)
        params = {"sessionId": source_id, "cwd": str(cwd), "mcpServers": []}
        plain = await _call(agent, "session/fork", params, timeout=timeout)
        if _result(plain) is not None:
            targets.append(("session/fork", source_id))
    return targets


async def _setup_with_entries(agent, cwd: Path, target: tuple[str, str | None], entries: Any, *, timeout: float):
    method, source_id = target
    if method == "session/fork":
        return await _fork_with_entries(agent, cwd, source_id, entries, timeout=timeout)
    return await _new_with_entries(agent, cwd, entries, timeout=timeout)


async def _advertised_options(agent, cwd: Path, *, timeout: float) -> list[dict[str, Any]]:
    """The `configOptions` of `session/options {cwd}`, or `[]` when it did not answer with a list
    (ACP-OPTIONS-001 judges that)."""
    entry = await _call(agent, "session/options", {"cwd": str(cwd)}, timeout=timeout)
    result = _result(entry)
    options = result.get("configOptions") if result is not None else None
    return [o for o in options if isinstance(o, dict) and isinstance(o.get("id"), str)] if isinstance(options, list) else []


def _selects(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [o for o in options if o.get("type") != "boolean" and flatten_select_values(o.get("options"))]


def _with_alternative(options: list[dict[str, Any]]) -> tuple[dict[str, Any], Any] | None:
    """The first select option that has a value other than its current one, and that value."""
    for option in _selects(options):
        alternatives = [v for v in flatten_select_values(option.get("options")) if v != option.get("currentValue")]
        if alternatives:
            return option, alternatives[0]
    return None


def _state(options: Any) -> dict[Any, Any]:
    if not isinstance(options, list):
        return {}
    return {o.get("id"): o.get("currentValue") for o in options if isinstance(o, dict)}


def _value_problems(options: Any) -> list[str]:
    """Options whose `currentValue` is not valid for their type (a bool, or a listed value)."""
    problems = []
    for option in options if isinstance(options, list) else []:
        if not isinstance(option, dict):
            continue
        current = option.get("currentValue")
        if option.get("type") == "boolean":
            valid = isinstance(current, bool)
        else:
            valid = current in flatten_select_values(option.get("options"))
        if not valid:
            problems.append(f"{option.get('id')!r} has currentValue {current!r}")
    return problems


def _setup_failures(label: str, method: str, entry) -> list[str]:
    """What is wrong with `entry` as the answer to a setup request the agent must accept."""
    result = _result(entry)
    if result is None:
        return [f"{label}: {method} did not succeed: {entry.text!r}"]
    issues = validate_agent_response(method, entry.parsed)
    if issues:
        return [f"{label}: {method} result failed schema validation: {issues!r}"]
    problems = _value_problems(result.get("configOptions"))
    return [f"{label}: {p}" for p in problems]


async def _expect_invalid_params(agent, cwd: Path, probes, targets, *, timeout: float) -> list[str]:
    failures = []
    for target in targets:
        for label, entries in probes:
            entry = await _setup_with_entries(agent, cwd, target, entries, timeout=timeout)
            if _error_code(entry) != INVALID_PARAMS:
                failures.append(f"{label} on {target[0]} ({entries!r}): {entry.text!r}")
    return failures


@pytest.mark.requirement("ACP-OPTIONS-004")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_malformed_initial_entries_fail_with_invalid_params(agent_launch, agent_initialize_result, tmp_path):
    """ACP-OPTIONS-004. `session/new` (and `session/fork` when advertised) with an entry without
    `configId`, and with a `value` that is neither a string nor (with `type: "boolean"`) a boolean,
    must each fail with `-32602`: the probes break the client rule to send schema-valid entries
    because the docs define the answer."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        targets = await _setup_targets(agent, tmp_path, agent_initialize_result.result, timeout=timeout)
        failures = await _expect_invalid_params(
            agent,
            tmp_path,
            (
                ("no configId", [{"value": "x"}]),
                ("a value matching no entry shape", [{"configId": "x", "value": 42}]),
            ),
            targets,
            timeout=timeout,
        )
    assert not failures, "malformed initial configOptions must fail with -32602: " + "; ".join(failures)


@pytest.mark.requirement("ACP-OPTIONS-005")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_duplicate_initial_entries_fail_with_invalid_params(agent_launch, agent_initialize_result, tmp_path):
    """ACP-OPTIONS-005. The same entry twice on `session/new` (and `session/fork` when advertised)
    must fail with `-32602`. A real non-boolean option of `session/options` at its current value is
    used when there is one, otherwise a synthetic id: the rule has no exception for unknown ids."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        options = _selects(await _advertised_options(agent, tmp_path, timeout=timeout))
        if options:
            entry_params = {"configId": options[0]["id"], "value": options[0]["currentValue"]}
        else:
            entry_params = {"configId": f"acp-tck-duplicate-{uuid.uuid4().hex}", "value": "x"}
        targets = await _setup_targets(agent, tmp_path, agent_initialize_result.result, timeout=timeout)
        failures = await _expect_invalid_params(
            agent,
            tmp_path,
            (("the same configId twice", [dict(entry_params), dict(entry_params)]),),
            targets,
            timeout=timeout,
        )
    assert not failures, "duplicate initial configOptions must fail with -32602: " + "; ".join(failures)


@pytest.mark.requirement("ACP-OPTIONS-006")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_inapplicable_initial_entries_are_ignored(agent_launch, agent_initialize_result, tmp_path):
    """ACP-OPTIONS-006. Entries the agent cannot apply must not fail setup, and the options keep a
    valid value: an unknown `configId` and, for a select option, a value it does not list, on
    `session/new`; the unknown id again on `session/load` and `session/resume` of that session
    when advertised. On a connection advertising `session.configOptions.boolean`, also a boolean
    entry for a select option and a string value for a boolean option. Every `session/new` probe is
    repeated on `session/fork` when advertised."""
    init_result = agent_initialize_result.result or {}
    timeout = agent_launch.default_timeout
    failures: list[str] = []
    session_id = None

    async def probe(agent, probes, watched: dict[str, Any] | None) -> None:
        nonlocal session_id
        for target in await _setup_targets(agent, tmp_path, init_result, timeout=timeout):
            for label, entries in probes:
                entry = await _setup_with_entries(agent, tmp_path, target, entries, timeout=timeout)
                problems = _setup_failures(f"{label} on {target[0]}", target[0], entry)
                result = _result(entry)
                if target[0] == "session/new" and result is not None and isinstance(result.get("sessionId"), str):
                    session_id = session_id or result["sessionId"]
                if label.startswith("a value") and not problems and watched is not None:
                    if _state(result.get("configOptions")).get(watched["id"]) == _NOT_A_VALUE:
                        problems.append(f"{label} on {target[0]}: {watched['id']!r} took the value that was sent")
                failures.extend(problems)

    async with connected_agent(agent_launch) as agent:
        selects = _selects(await _advertised_options(agent, tmp_path, timeout=timeout))
        probes = [("an unknown configId", [{"configId": _UNKNOWN_ID, "value": "x"}])]
        if selects:
            probes.append(
                ("a value the option does not list", [{"configId": selects[0]["id"], "value": _NOT_A_VALUE}])
            )
        await probe(agent, probes, selects[0] if selects else None)
        if session_id is not None:
            unknown_entry = [{"configId": _UNKNOWN_ID, "value": "x"}]
            if capability_is_supported(init_result, "agentCapabilities.loadSession", boolean=True):
                params = {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": [], "configOptions": unknown_entry}
                entry = await _call(agent, "session/load", params, timeout=timeout)
                failures += _setup_failures("an unknown configId", "session/load", entry)
            if capability_is_supported(init_result, "agentCapabilities.sessionCapabilities.resume"):
                params = {"sessionId": session_id, "cwd": str(tmp_path), "mcpServers": [], "configOptions": unknown_entry}
                entry = await _call(agent, "session/resume", params, timeout=timeout)
                failures += _setup_failures("an unknown configId", "session/resume", entry)
    async with connected_agent(agent_launch, client_capabilities=_BOOLEAN_CLIENT) as agent:
        options = await _advertised_options(agent, tmp_path, timeout=timeout)
        mismatched = []
        if selects := _selects(options):
            mismatched.append(
                ("a boolean entry for a select option", [{"configId": selects[0]["id"], "type": "boolean", "value": True}])
            )
        if booleans := [o for o in options if o.get("type") == "boolean"]:
            mismatched.append(
                ("a string value for a boolean option", [{"configId": booleans[0]["id"], "value": _NOT_A_VALUE}])
            )
        if mismatched:
            await probe(agent, mismatched, None)
    assert not failures, "inapplicable initial configOptions entries must be ignored, not rejected: " + "; ".join(
        failures
    )


@dataclass(frozen=True)
class _Exchange:
    option: dict[str, Any]
    value: Any
    response: dict[str, Any]
    before: list
    """Transcript entries from the request to the response, response included."""
    after: list
    """Entries received in the quiet period after the response."""


async def _initial_value_exchange(agent_launch, tmp_path) -> _Exchange:
    """`session/new` with an alternative value for a select option of `session/options`, SKIPping
    when there is no such option or setup fails (ACP-OPTIONS-006 judges that)."""
    exchange = await _value_exchange(agent_launch, tmp_path, fork=False)
    if isinstance(exchange, str):
        pytest.skip(exchange)
    return exchange


async def _value_exchange(agent_launch, tmp_path, *, fork: bool) -> _Exchange | str:
    """`session/new` (or, with `fork`, `session/fork` of a plain session made and left quiet
    first) with an alternative value for a select option of `session/options`, or why it could
    not be made: there is no such option, or setup failed (ACP-OPTIONS-006 judges that)."""
    timeout = agent_launch.default_timeout
    method = "session/fork" if fork else "session/new"
    async with connected_agent(agent_launch) as agent:
        picked = _with_alternative(await _advertised_options(agent, tmp_path, timeout=timeout))
        if picked is None:
            return "session/options lists no select option with an alternative value"
        option, value = picked
        entries = [{"configId": option["id"], "value": value}]
        if fork:
            source_id = await _source_session(agent, tmp_path, timeout=timeout)
            await drain(agent, quiet_period(timeout))
        start = len(agent.transcript)
        if fork:
            entry = await _fork_with_entries(agent, tmp_path, source_id, entries, timeout=timeout)
        else:
            entry = await _new_with_entries(agent, tmp_path, entries, timeout=timeout)
        result = _result(entry)
        if result is None:
            return f"{method} with an initial entry did not succeed (see ACP-OPTIONS-006): {entry.text!r}"
        end = _index_of(agent, entry, start)
        await drain(agent, quiet_period(timeout))
        return _Exchange(option, value, result, agent.transcript[start : end + 1], agent.transcript[end + 1 :])


async def _kinds_without_entries(agent_launch, tmp_path, *, fork: bool) -> set[str]:
    """The update kinds a plain `session/new` (or `session/fork`, made like `_value_exchange`'s)
    sends for its session on a fresh connection, from the request through a quiet period after
    its response: kinds that do not come from initial entries. Kinds sent after the response count
    too: applying entries delays the response, so an update the plain request sends just after it
    may come before it when entries are applied. Empty when the request fails."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        if fork:
            source_id = await _source_session(agent, tmp_path, timeout=timeout)
            await drain(agent, quiet_period(timeout))
            params = {"sessionId": source_id, "cwd": str(tmp_path), "mcpServers": []}
        else:
            params = {"cwd": str(tmp_path), "mcpServers": []}
        start = len(agent.transcript)
        entry = await _call(agent, "session/fork" if fork else "session/new", params, timeout=timeout)
        session_id = (_result(entry) or {}).get("sessionId")
        if not isinstance(session_id, str):
            return set()
        await drain(agent, quiet_period(timeout))
        return set(_update_kinds(agent.transcript[start:], session_id))


def _index_of(agent, entry, start: int) -> int:
    """The transcript index (at or after `start`) of `entry`, a response the TCK just awaited."""
    return next(i for i in range(len(agent.transcript) - 1, start - 1, -1) if agent.transcript[i] is entry)


def _update_kinds(entries: list, session_id: str | None = None) -> list[str]:
    return [
        kind
        for e in entries
        if e.direction is Direction.RECEIVED and (kind := session_update_kind(e, session_id)) is not None
    ]


@pytest.mark.requirement("ACP-OPTIONS-007")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_no_config_option_update_for_initial_entries(agent_launch, tmp_path):
    """ACP-OPTIONS-007 (ADVISORY). No `config_option_update` between the `session/new` request
    carrying an initial entry and a quiet period after its response."""
    exchange = await _initial_value_exchange(agent_launch, tmp_path)
    updates = [k for k in _update_kinds(exchange.before + exchange.after) if k == "config_option_update"]
    assert not updates, (
        f"{len(updates)} config_option_update notification(s) for the initial entry on "
        f"{exchange.option['id']!r}; the setup response carries the resulting values"
    )


@pytest.mark.requirement("ACP-OPTIONS-008")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_no_update_before_the_setup_response_for_initial_entries(agent_launch, agent_initialize_result, tmp_path):
    """ACP-OPTIONS-008 (ADVISORY). No `session/update` for the new session before the `session/new`
    response, when the request carried an initial entry, other than `config_option_update`
    (ACP-OPTIONS-007's) and kinds a plain `session/new` also sends, before or after its response
    (not caused by the entry). Repeated on `session/fork` when advertised; a fork that cannot be
    made with the entry is left unjudged (ACP-OPTIONS-006's)."""
    exchanges = [("session/new", await _initial_value_exchange(agent_launch, tmp_path))]
    init_result = agent_initialize_result.result
    if init_result is not None and capability_is_supported(init_result, _FORK_PATH):
        fork_exchange = await _value_exchange(agent_launch, tmp_path, fork=True)
        if isinstance(fork_exchange, _Exchange):
            exchanges.append(("session/fork", fork_exchange))
    problems = []
    for method, exchange in exchanges:
        session_id = exchange.response.get("sessionId")
        kinds = set(_update_kinds(exchange.before, session_id)) - {"config_option_update"}
        if kinds:
            kinds -= await _kinds_without_entries(agent_launch, tmp_path, fork=method == "session/fork")
        if kinds:
            problems.append(f"session/update {sorted(kinds)!r} sent before the {method} response for an initial entry")
    assert not problems, "; ".join(problems)


@pytest.mark.requirement("ACP-OPTIONS-010")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_records_whether_a_valid_initial_value_shows_in_the_response(
    agent_launch, tmp_path, record_property
):
    """ACP-OPTIONS-010 (INFORMATIONAL). Records, never asserts, whether the sent alternative value
    is the `currentValue` the setup response reports for its option."""
    exchange = await _initial_value_exchange(agent_launch, tmp_path)
    shown = _state(exchange.response.get("configOptions")).get(exchange.option["id"], "<absent>")
    record_property("acp_tck_initial_value_sent", exchange.value)
    record_property("acp_tck_initial_value_in_response", shown)
    record_property("acp_tck_initial_value_applied", shown == exchange.value)


@pytest.mark.requirement("ACP-OPTIONS-011")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_setup_response_reports_the_values_the_session_has(agent_launch, tmp_path):
    """ACP-OPTIONS-011. After `session/new` with an initial entry, a no-op `session/set_config_option`
    of a different option returns the same `(id, currentValue)` pairs as the setup response. The
    connection advertises `session.configOptions.boolean` so a second option is likelier to
    exist. A `config_option_update` after the response SKIPs: the agent changed its own state."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch, client_capabilities=_BOOLEAN_CLIENT) as agent:
        options = await _advertised_options(agent, tmp_path, timeout=timeout)
        picked = _with_alternative(options)
        if picked is None:
            pytest.skip("session/options lists no select option with an alternative value")
        option, value = picked
        select_ids = {o["id"] for o in _selects(options)}
        others = [
            o for o in options if o["id"] != option["id"] and (o.get("type") == "boolean" or o["id"] in select_ids)
        ]
        if not others:
            pytest.skip("needs a second option to observe through: the only settable option is the entry's own")
        new_start = len(agent.transcript)
        entry = await _new_with_entries(agent, tmp_path, [{"configId": option["id"], "value": value}], timeout=timeout)
        result = _result(entry)
        reported = _state(result.get("configOptions")) if result is not None else {}
        follow_up = next((o for o in others if o["id"] in reported), None)
        if result is None or follow_up is None or not isinstance(result.get("sessionId"), str):
            pytest.skip(f"session/new did not report a second option to observe through (see ACP-OPTIONS-006): {entry.text!r}")
        params: dict[str, Any] = {
            "sessionId": result["sessionId"],
            "configId": follow_up["id"],
            "value": reported[follow_up["id"]],
        }
        if follow_up.get("type") == "boolean":
            params["type"] = "boolean"
        start = _index_of(agent, entry, new_start)
        set_entry = await _call(agent, "session/set_config_option", params, timeout=timeout)
        returned = (_result(set_entry) or {}).get("configOptions")
        if not isinstance(returned, list):
            pytest.skip(f"the no-op session/set_config_option did not return a list (see ACP-CONFIG-002): {set_entry.text!r}")
        if "config_option_update" in _update_kinds(agent.transcript[start:]):
            pytest.skip("config_option_update observed after setup; the agent changed its own state")
    after = _state(returned)
    changed = {k: (reported[k], after[k]) for k in reported if k in after and after[k] != reported[k]}
    assert not changed, (
        "the setup response reported values the session did not have (configId: (reported, actual)): "
        f"{changed!r}"
    )
