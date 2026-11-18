"""Initial config option values: ACP-OPTIONS-004..007, -010, -011 and -201.

An agent that advertises `capabilities.session.options` accepts a `configOptions` list of
`{configId, type, value}` entries on `session/new` (and resume, and fork when supported). Every row
is gated on that capability (the TCK may not send entries otherwise, `session-config-options.mdx:482`)
and every test judges its own fresh connection. The entries come from `session/options` of the same
agent: a select option with an alternative value for the rows that apply one, a real id for the
duplicate probe. Probes are `session/new` requests; ACP-OPTIONS-006 repeats its unknown-id probe on
`session/resume`. `session/fork` is not probed. Boolean options need no client capability in v2.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tck.v2.protocol import INVALID_PARAMS
from tck.v2.validation import validate_agent_response

from ._helpers import (
    config_state,
    config_updates,
    connected_agent,
    drain_quiet,
    flatten_select_values,
    quiet_period,
    skip_if_auth_gated,
    skip_if_auth_required,
)

_OPTIONS_PATH = "capabilities.session.options"
_UNKNOWN_ID = "_tck_unknown_config"
_NOT_A_VALUE = "_tck_unknown_value"
_UNSUPPORTED_TYPE = "_tck_unsupported"


def _error_code(entry) -> Any:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return error.get("code") if isinstance(error, dict) else None


def _result(entry) -> dict[str, Any] | None:
    msg = entry.parsed
    result = msg.get("result") if isinstance(msg, dict) else None
    return result if isinstance(result, dict) else None


def _id_entry(config_id: str, value: Any) -> dict[str, Any]:
    return {"configId": config_id, "type": "id", "value": value}


async def _call(agent, method: str, params: dict[str, Any], *, timeout: float):
    req_id = await agent.send_request(method, params)
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    if method == "session/new":
        skip_if_auth_gated(entry)
    skip_if_auth_required(entry, method)
    return entry


async def _new_with_entries(agent, cwd: Path, entries: Any, *, timeout: float):
    return await _call(agent, "session/new", {"cwd": str(cwd), "configOptions": entries}, timeout=timeout)


async def _advertised_options(agent, cwd: Path, *, timeout: float) -> list[dict[str, Any]]:
    """The `configOptions` of `session/options {cwd}`, or `[]` when it did not answer with a list
    (ACP-OPTIONS-001 judges that)."""
    entry = await _call(agent, "session/options", {"cwd": str(cwd)}, timeout=timeout)
    result = _result(entry)
    options = result.get("configOptions") if result is not None else None
    if not isinstance(options, list):
        return []
    return [o for o in options if isinstance(o, dict) and isinstance(o.get("configId"), str)]


def _selects(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [o for o in options if o.get("type") == "select" and flatten_select_values(o.get("options"))]


def _with_alternative(options: list[dict[str, Any]]) -> tuple[dict[str, Any], Any] | None:
    """The first select option that has a value other than its current one, and that value."""
    for option in _selects(options):
        alternatives = [v for v in flatten_select_values(option.get("options")) if v != option.get("currentValue")]
        if alternatives:
            return option, alternatives[0]
    return None


def _value_problems(options: Any) -> list[str]:
    """Options whose `currentValue` is not valid for their type (a bool, or a listed value). Options
    of any other type are not judged."""
    problems = []
    for option in options if isinstance(options, list) else []:
        if not isinstance(option, dict):
            continue
        current = option.get("currentValue")
        if option.get("type") == "boolean":
            valid = isinstance(current, bool)
        elif option.get("type") == "select":
            valid = current in flatten_select_values(option.get("options"))
        else:
            continue
        if not valid:
            problems.append(f"{option.get('configId')!r} has currentValue {current!r}")
    return problems


def _setup_failures(label: str, method: str, entry) -> list[str]:
    """What is wrong with `entry` as the answer to a setup request the agent must accept."""
    result = _result(entry)
    if result is None:
        return [f"{label}: {method} did not succeed: {entry.text!r}"]
    issues = validate_agent_response(method, entry.parsed)
    if issues:
        return [f"{label}: {method} result failed schema validation: {issues!r}"]
    return [f"{label}: {p}" for p in _value_problems(result.get("configOptions"))]


async def _expect_invalid_params(agent, cwd: Path, probes, *, timeout: float) -> list[str]:
    failures = []
    for label, entries in probes:
        entry = await _new_with_entries(agent, cwd, entries, timeout=timeout)
        if _error_code(entry) != INVALID_PARAMS:
            failures.append(f"{label} ({entries!r}): {entry.text!r}")
    return failures


@pytest.mark.requirement("ACP-OPTIONS-004")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_malformed_initial_entries_fail_with_invalid_params(agent_launch, tmp_path):
    """ACP-OPTIONS-004. `session/new` with an entry without `configId`, one without `type`, one of
    `type: "id"` whose `value` is not a string and one of `type: "boolean"` whose `value` is not a
    boolean must each fail with `-32602`: the probes break the client rule to send schema-valid
    entries because the docs define the answer."""
    async with connected_agent(agent_launch) as agent:
        failures = await _expect_invalid_params(
            agent,
            tmp_path,
            (
                ("no configId", [{"type": "id", "value": "x"}]),
                ("no type", [{"configId": "x", "value": "x"}]),
                ("a value that does not match type id", [{"configId": "x", "type": "id", "value": 42}]),
                ("a value that does not match type boolean", [{"configId": "x", "type": "boolean", "value": "yes"}]),
            ),
            timeout=agent_launch.default_timeout,
        )
    assert not failures, "malformed initial configOptions must fail with -32602: " + "; ".join(failures)


@pytest.mark.requirement("ACP-OPTIONS-005")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_duplicate_initial_entries_fail_with_invalid_params(agent_launch, tmp_path):
    """ACP-OPTIONS-005. The same entry twice on `session/new` must fail with `-32602`. A real
    select option of `session/options` at its current value is used when there is one, otherwise a
    synthetic id: the rule has no exception for unknown ids."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        options = _selects(await _advertised_options(agent, tmp_path, timeout=timeout))
        if options:
            entry_params = _id_entry(options[0]["configId"], options[0]["currentValue"])
        else:
            entry_params = _id_entry(f"_tck_duplicate_{uuid.uuid4().hex}", "x")
        failures = await _expect_invalid_params(
            agent, tmp_path, (("the same configId twice", [dict(entry_params), dict(entry_params)]),), timeout=timeout
        )
    assert not failures, "duplicate initial configOptions must fail with -32602: " + "; ".join(failures)


@pytest.mark.requirement("ACP-OPTIONS-006")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_inapplicable_initial_entries_are_ignored(agent_launch, tmp_path):
    """ACP-OPTIONS-006. Entries the agent cannot apply must not fail setup, and the options keep a
    valid value: an unknown `configId`, a `type: "boolean"` entry for a select option, a
    `type: "id"` entry for a boolean option and, for a select option, a value it does not list, on
    `session/new`; the unknown id again on `session/resume` of that session."""
    timeout = agent_launch.default_timeout
    failures: list[str] = []
    session_id = None
    async with connected_agent(agent_launch) as agent:
        options = await _advertised_options(agent, tmp_path, timeout=timeout)
        selects = _selects(options)
        probes: list[tuple[str, list[dict[str, Any]]]] = [("an unknown configId", [_id_entry(_UNKNOWN_ID, "x")])]
        if selects:
            probes.append(("a value the option does not list", [_id_entry(selects[0]["configId"], _NOT_A_VALUE)]))
            probes.append(
                (
                    "a boolean entry for a select option",
                    [{"configId": selects[0]["configId"], "type": "boolean", "value": True}],
                )
            )
        if booleans := [o for o in options if o.get("type") == "boolean"]:
            probes.append(("an id entry for a boolean option", [_id_entry(booleans[0]["configId"], _NOT_A_VALUE)]))
        for label, entries in probes:
            entry = await _new_with_entries(agent, tmp_path, entries, timeout=timeout)
            problems = _setup_failures(label, "session/new", entry)
            result = _result(entry)
            if result is not None and isinstance(result.get("sessionId"), str):
                session_id = session_id or result["sessionId"]
            if label.startswith("a value") and not problems:
                shown = config_state(result.get("configOptions")).get(selects[0]["configId"])
                if shown == _NOT_A_VALUE:
                    problems.append(f"{label}: {selects[0]['configId']!r} took the value that was sent")
            failures += problems
        if session_id is not None:
            params = {"sessionId": session_id, "cwd": str(tmp_path), "configOptions": [_id_entry(_UNKNOWN_ID, "x")]}
            entry = await _call(agent, "session/resume", params, timeout=timeout)
            failures += _setup_failures("an unknown configId", "session/resume", entry)
    assert not failures, "inapplicable initial configOptions entries must be ignored, not rejected: " + "; ".join(
        failures
    )


@dataclass(frozen=True)
class _Exchange:
    option: dict[str, Any]
    value: Any
    response: dict[str, Any]
    entries: list
    """Transcript entries from the request through the quiet period after the response."""


async def _initial_value_exchange(agent_launch, tmp_path) -> _Exchange:
    """`session/new` with an alternative value for a select option of `session/options`, SKIPping
    when there is no such option or setup fails (ACP-OPTIONS-006 judges that)."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        picked = _with_alternative(await _advertised_options(agent, tmp_path, timeout=timeout))
        if picked is None:
            pytest.skip("session/options lists no select option with an alternative value")
        option, value = picked
        start = len(agent.transcript)
        entry = await _new_with_entries(agent, tmp_path, [_id_entry(option["configId"], value)], timeout=timeout)
        result = _result(entry)
        if result is None:
            pytest.skip(f"session/new with an initial entry did not succeed (see ACP-OPTIONS-006): {entry.text!r}")
        await drain_quiet(agent, quiet_period(timeout))
        return _Exchange(option, value, result, agent.transcript[start:])


@pytest.mark.requirement("ACP-OPTIONS-007")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_no_config_option_update_for_initial_entries(agent_launch, tmp_path):
    """ACP-OPTIONS-007 (ADVISORY). No `config_option_update` for the new session from the request
    until a quiet period after the response, when the request carried an initial entry."""
    exchange = await _initial_value_exchange(agent_launch, tmp_path)
    session_id = exchange.response.get("sessionId")
    updates = config_updates(exchange.entries, session_id)
    assert not updates, f"config_option_update sent for an initial entry: {updates!r}"


@pytest.mark.requirement("ACP-OPTIONS-010")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_records_whether_a_valid_initial_value_shows_in_the_response(
    agent_launch, tmp_path, record_property
):
    """ACP-OPTIONS-010 (INFORMATIONAL). Records, never asserts, whether the sent alternative value
    is the `currentValue` the setup response reports for its option."""
    exchange = await _initial_value_exchange(agent_launch, tmp_path)
    shown = config_state(exchange.response.get("configOptions")).get(exchange.option["configId"], "<absent>")
    record_property("acp_tck_initial_value_sent", exchange.value)
    record_property("acp_tck_initial_value_in_response", shown)
    record_property("acp_tck_initial_value_applied", shown == exchange.value)


@pytest.mark.requirement("ACP-OPTIONS-011")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_setup_response_reports_the_values_the_session_has(agent_launch, tmp_path):
    """ACP-OPTIONS-011. After `session/new` with an initial entry and a quiet period, a no-op
    `session/set_config_option` of a different option returns the same `(configId, currentValue)`
    pairs as the setup response. A `config_option_update` before that call SKIPs: the agent changed
    its own state (the call's own update is expected)."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        options = await _advertised_options(agent, tmp_path, timeout=timeout)
        picked = _with_alternative(options)
        if picked is None:
            pytest.skip("session/options lists no select option with an alternative value")
        option, value = picked
        others = [
            o for o in options if o["configId"] != option["configId"] and o.get("type") in ("select", "boolean")
        ]
        if not others:
            pytest.skip("needs a second option to observe through: the only settable option is the entry's own")
        start = len(agent.transcript)
        entry = await _new_with_entries(agent, tmp_path, [_id_entry(option["configId"], value)], timeout=timeout)
        result = _result(entry)
        reported = config_state(result.get("configOptions")) if result is not None else {}
        follow_up = next((o for o in others if o["configId"] in reported), None)
        if result is None or follow_up is None or not isinstance(result.get("sessionId"), str):
            pytest.skip(f"session/new did not report a second option to observe through (see ACP-OPTIONS-006): {entry.text!r}")
        await drain_quiet(agent, quiet_period(timeout))
        if config_updates(agent.transcript[start:], result["sessionId"]):
            pytest.skip("config_option_update observed after setup; the agent changed its own state")
        set_entry = await _call(
            agent,
            "session/set_config_option",
            {
                "sessionId": result["sessionId"],
                "configId": follow_up["configId"],
                "type": "boolean" if follow_up.get("type") == "boolean" else "id",
                "value": reported[follow_up["configId"]],
            },
            timeout=timeout,
        )
        returned = (_result(set_entry) or {}).get("configOptions")
        if not isinstance(returned, list):
            pytest.skip(f"the no-op session/set_config_option did not return a list (see ACP-CONFIG-002): {set_entry.text!r}")
    after = config_state(returned)
    changed = {k: (reported[k], after[k]) for k in reported if k in after and after[k] != reported[k]}
    assert not changed, (
        "the setup response reported values the session did not have (configId: (reported, actual)): "
        f"{changed!r}"
    )


@pytest.mark.requirement("ACP-OPTIONS-201")
@pytest.mark.capability(_OPTIONS_PATH)
async def test_records_how_an_unsupported_initial_value_type_is_handled(
    agent_launch, tmp_path, record_property
):
    """ACP-OPTIONS-201 (INFORMATIONAL). Records, never asserts, whether `session/new` with an entry of
    value `type` `_tck_unsupported` (schema-valid through the open `other` branch) was rejected
    (the code) or ignored (a session was created). The docs contradict themselves on it, so no
    outcome is a failure."""
    timeout = agent_launch.default_timeout
    async with connected_agent(agent_launch) as agent:
        options = await _advertised_options(agent, tmp_path, timeout=timeout)
        config_id = options[0]["configId"] if options else _UNKNOWN_ID
        entry = await _new_with_entries(
            agent,
            tmp_path,
            [{"configId": config_id, "type": _UNSUPPORTED_TYPE, "value": "x"}],
            timeout=timeout,
        )
    code = _error_code(entry)
    if code is not None:
        outcome = f"rejected with {code}"
    elif _result(entry) is not None:
        outcome = "ignored"
    else:
        outcome = "unrecognized answer"
    record_property("acp_tck_options_unsupported_type_outcome", outcome)
