"""Session `configOptions` (ACP-CONFIG-001/002/201/203, ACP-CONFIG-206..212).

`configOptions` has no `capabilities` marker of its own -- support is *inferred* from whether
`session/new`'s response carries a non-empty `configOptions` list at all. `Requirement.capability`
is therefore the documentation-only `"inferred:configOptions"` string (mirrors v1's
`ACP-MODES-001`/`ACP-CONFIG-001/002` pattern exactly -- see `tck.v1.requirements`/
`tck.v2.requirements` module docstrings); it is *not* looked up by `@pytest.mark.capability(...)`.
Each test instead performs its own `session/new` and manually `pytest.skip`s with the reason
"session/new returned no configOptions" when the field is absent/empty.

Must NOT assert that a `configId`'s value scheme means anything beyond schema validity, or that
`session/set_config_option`'s *new* value is reflected anywhere besides its own response/an
observed `config_option_update` (the spec lets the response report a different `currentValue`
than the one requested, `session-config-options.mdx:236`).

Only the `configOptions` items are schema-validated (against `SessionConfigOption`), and only by
the shape rows (`ACP-CONFIG-201`/`203`): an unrelated violation elsewhere in `session/new`'s result
is the whole-result rows' to report (`ACP-SESSION-001`), not a reason for every config row to
FAIL instead of SKIP.

`ACP-CONFIG-207..209` deliberately send requests a client must not (an unadvertised `configId`,
an undeclared value, a mismatched or unsupported value `type`): the same spec sentence fixes the
agent's answer (`-32602`, state unchanged), so the probes use `_tck_`-prefixed ids/values that no
real option can collide with.

None of these tests carries a `@pytest.mark.capability(...)` marker (there is nothing for the
autouse `_tck_capability_gate` to look up -- `capability="inferred:configOptions"` is
documentation-only), so each connects via `_helpers.v2_only_agent` -- the shared "manual
initialize + skip on VERSION-MISMATCH + login_if_needed" pattern -- instead of
`connected_agent(agent_launch)` directly, so a v1-only agent forced under
`--protocol-version 2` SKIPs with the `VERSION-MISMATCH:` marker instead of just "session/new
returned no configOptions" (`tests/v2/test_cli.py`'s `test_v1_conforming_agent_under_protocol_
version_2_is_blocked_by_version_mismatch` invariant).
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import Direction
from tck.v2.protocol import INVALID_PARAMS
from tck.v2.validation import validate_agent_message, validate_agent_response, validate_def_value

from ._helpers import (
    drain_quiet,
    iter_messages,
    new_session_result,
    obtain_resumable_session,
    quiet_period,
    set_config_option,
    v2_only_agent,
)

# Probe values for ACP-CONFIG-207..209; `_`-prefixed so no real option or value can collide.
_UNKNOWN_CONFIG_ID = "_tck_unknown_config"
_UNKNOWN_VALUE = "_tck_unknown_value"
_UNSUPPORTED_VALUE_TYPE = "_tck_unsupported"


async def _new_session_full_result(agent, cwd, *, timeout):
    """`session/new`'s whole result dict (not just `sessionId`) so callers can inspect
    `configOptions`. Not schema-validated: only the shape rows judge the `configOptions` items,
    and `ACP-SESSION-001` judges the rest of the result."""
    return await new_session_result(agent, cwd, timeout=timeout)


def _flatten_select_values(options: Any) -> list[Any]:
    """`SessionConfigSelectOptions` is `anyOf` a flat array of `{value, name, ...}` or a grouped
    array of `{groupId, name, options: [{value, ...}]}` -- flatten either shape down to the set
    of legal `value`s."""
    values: list[Any] = []
    for entry in options or []:
        if not isinstance(entry, dict):
            continue
        if "value" in entry:
            values.append(entry["value"])
        elif "options" in entry:
            for sub in entry["options"]:
                if isinstance(sub, dict) and "value" in sub:
                    values.append(sub["value"])
    return values


def _assert_config_options_shape_valid(config_options: list[Any]) -> None:
    """ACP-CONFIG-201's shape checks, factored out so ACP-CONFIG-203 (the `session/resume`
    carrier) can reuse them verbatim. An empty `configOptions` list is valid (it means none);
    the non-empty rule is per `select` option (and per group) below. Only the `configOptions`
    items are schema-validated, never the message that carries them."""
    assert isinstance(config_options, list), f"configOptions must be an array, got {config_options!r}"
    for option in config_options:
        assert isinstance(option, dict) and "configId" in option and "name" in option, (
            f"each configOptions entry needs at least configId/name: {option!r}"
        )
        issues = validate_def_value("SessionConfigOption", option)
        assert not issues, (
            f"config option {option['configId']!r} failed schema validation: {issues!r}"
        )
        option_type = option.get("type")
        if option_type == "boolean":
            assert isinstance(option.get("currentValue"), bool), (
                f"config option {option['configId']!r} is type=boolean but currentValue is "
                f"{option.get('currentValue')!r}"
            )
        elif option_type == "select":
            assert "currentValue" in option, (
                f"select config option {option['configId']!r} has no currentValue"
            )
            opts = option.get("options")
            assert isinstance(opts, list) and opts, (
                f"select config option {option['configId']!r} options must be a non-empty "
                f"array: {opts!r}"
            )
            is_flat = all(isinstance(o, dict) and "value" in o for o in opts)
            is_grouped = all(isinstance(o, dict) and "groupId" in o for o in opts)
            assert is_flat or is_grouped, (
                f"select config option {option['configId']!r} mixes flat and grouped option "
                f"shapes, never allowed: {opts!r}"
            )
            if is_grouped:
                empty = [g.get("groupId") for g in opts if not g.get("options")]
                assert not empty, (
                    f"select config option {option['configId']!r} has empty group(s) {empty!r}: "
                    "every group must contain at least one value"
                )
        # any other `type` is a custom/`_`-prefixed variant -- nothing further to check here.


@pytest.mark.requirement("ACP-CONFIG-201")
async def test_config_options_shape_is_valid(agent_launch, tmp_path):
    """ACP-CONFIG-201."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        result = await _new_session_full_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        config_options = result.get("configOptions")
        if not config_options:
            pytest.skip("session/new returned no configOptions")
        _assert_config_options_shape_valid(config_options)


def _pick_settable_option(config_options: list[Any]) -> tuple[dict[str, Any], str, Any]:
    """Pick the first configOptions entry this suite knows how to `session/set_config_option`,
    returning `(option, set_type, new_value)`. Skips if `config_options[0]` is a custom type this
    suite has no wire encoding for. Plain function, not `async def`: it never awaits anything."""
    target = config_options[0]
    if target.get("type") == "boolean":
        return target, "boolean", not target.get("currentValue")
    if target.get("type") == "select":
        legal_values = _flatten_select_values(target.get("options"))
        remaining = [value for value in legal_values if value != target.get("currentValue")]
        if not remaining:
            pytest.skip(f"config option {target['configId']!r} has no alternative value to switch to")
        return target, "id", remaining[0]
    pytest.skip(f"config option {target['configId']!r} has an unrecognized/custom type {target.get('type')!r}")
    raise AssertionError("unreachable")  # pytest.skip always raises


@pytest.mark.requirement("ACP-CONFIG-002")
async def test_set_config_option_returns_the_complete_list(agent_launch, tmp_path, record_property):
    """ACP-CONFIG-002. SKIPs rather than ever speculatively calling `session/set_config_option`
    when `session/new` advertised no `configOptions` at all -- there would be nothing legitimate
    to set.

    Asserts only array + schema validity + the changed `configId` being present. Recorded, never
    asserted: whether every originally-advertised id is still there (a change may remove
    dependent options) and whether the changed entry echoes the sent value (an agent may
    reflect a dependent adjustment instead)."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        result = await _new_session_full_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        config_options = result.get("configOptions")
        if not config_options:
            pytest.skip("session/new returned no configOptions")
        session_id = result["sessionId"]
        original_ids = {
            option["configId"]
            for option in config_options
            if isinstance(option, dict) and "configId" in option
        }
        target, set_type, new_value = _pick_settable_option(config_options)

        entry = await set_config_option(
            agent,
            session_id,
            target["configId"],
            type=set_type,
            value=new_value,
            timeout=agent_launch.default_timeout,
        )
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/set_config_option did not succeed: {entry.text!r}"
        )
        returned = msg["result"].get("configOptions")
        assert isinstance(returned, list), (
            f"session/set_config_option result.configOptions must be an array, got {returned!r}"
        )
        issues = validate_agent_response("session/set_config_option", msg)
        assert not issues, f"session/set_config_option result failed schema validation: {issues!r}"
        returned_ids = {option.get("configId") for option in returned if isinstance(option, dict)}
        record_property("acp_tck_config_set_keeps_all_ids", original_ids <= returned_ids)
        changed = next(
            (o for o in returned if isinstance(o, dict) and o.get("configId") == target["configId"]),
            None,
        )
        assert changed is not None, (
            f"session/set_config_option's returned list is missing the changed option "
            f"{target['configId']!r} entirely: {returned!r}"
        )
        record_property(
            "acp_tck_config_option_echoes_sent_value", changed.get("currentValue") == new_value
        )


@pytest.mark.requirement("ACP-CONFIG-203")
async def test_resume_config_options_shape_is_valid_when_present(agent_launch, tmp_path):
    """ACP-CONFIG-203. A new carrier in v2 -- v1's `session/load` had no analogous field.

    The first connection only establishes that `configOptions` are offered at all (and keeps the
    `VERSION-MISMATCH:` skip). The resume itself goes through `obtain_resumable_session`, whose
    successful probe response is the one validated -- so a resume error SKIPs exactly as it
    does for `ACP-RESUME-001`. Shape only: a resume that omits `configOptions` SKIPs here and is
    `ACP-RESUME-210`'s to FAIL."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        result = await _new_session_full_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        if not result.get("configOptions"):
            pytest.skip("session/new returned no configOptions")
    async with obtain_resumable_session(
        agent_launch, tmp_path, timeout=agent_launch.default_timeout
    ) as (_agent, _session_id, response_entry, _resume_cwd):
        msg = response_entry.parsed
        config_options = msg["result"].get("configOptions")
        if config_options is None:
            pytest.skip("session/resume result carried no configOptions to validate")
        _assert_config_options_shape_valid(config_options)


@pytest.mark.requirement("ACP-CONFIG-001")
async def test_select_config_option_current_value_is_declared(agent_launch, tmp_path):
    """ACP-CONFIG-001."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        result = await _new_session_full_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        config_options = result.get("configOptions")
        if not config_options:
            pytest.skip("session/new returned no configOptions")
        select_options = [
            option for option in config_options if isinstance(option, dict) and option.get("type") == "select"
        ]
        if not select_options:
            pytest.skip("no select-type configOptions to check")
        for option in select_options:
            legal_values = _flatten_select_values(option.get("options"))
            assert option.get("currentValue") in legal_values, (
                f"config option {option['configId']!r} currentValue {option.get('currentValue')!r} "
                f"is not among its declared options {legal_values!r}"
            )


@pytest.mark.requirement("ACP-CONFIG-206")
async def test_config_option_update_is_complete_if_observed(agent_launch, tmp_path, record_property):
    """ACP-CONFIG-206. Conditional and vacuous (recorded, never FAILed) when no
    `config_option_update` is ever observed during the run. Whether the update still carries
    every originally-advertised id is recorded, not asserted: the current state may drop
    options."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        result = await _new_session_full_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        config_options = result.get("configOptions")
        if not config_options:
            pytest.skip("session/new returned no configOptions")
        session_id = result["sessionId"]
        original_ids = {
            option["configId"]
            for option in config_options
            if isinstance(option, dict) and "configId" in option
        }
        target, set_type, new_value = _pick_settable_option(config_options)

        entry = await set_config_option(
            agent,
            session_id,
            target["configId"],
            type=set_type,
            value=new_value,
            timeout=agent_launch.default_timeout,
        )
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/set_config_option did not succeed: {entry.text!r}"
        )

        # `wait_for_response` (inside `set_config_option`) may already have buffered a
        # same-timing `config_option_update` into `agent.pending()`; a short quiet drain then
        # catches one sent just after the response too.
        observed = agent.pending() + await drain_quiet(agent, quiet_period(agent_launch.default_timeout))
        update_msgs = [
            msg
            for entry in observed
            for msg in iter_messages(entry)
            if msg.get("method") == "session/update"
            and ((msg.get("params") or {}).get("update") or {}).get("sessionUpdate")
            == "config_option_update"
        ]
        record_property("acp_tck_config_option_update_observed", bool(update_msgs))
        if not update_msgs:
            return  # vacuous -- conforming, nothing further to check
        keeps_all_ids = True
        for update_msg in update_msgs:
            returned = update_msg["params"]["update"].get("configOptions")
            assert isinstance(returned, list), (
                f"config_option_update.configOptions must be an array, got {returned!r}"
            )
            issues = validate_agent_message(update_msg)
            assert not issues, f"config_option_update failed schema validation: {issues!r}"
            returned_ids = {o.get("configId") for o in returned if isinstance(o, dict)}
            keeps_all_ids = keeps_all_ids and original_ids <= returned_ids
        record_property("acp_tck_config_option_update_keeps_all_ids", keeps_all_ids)


def _config_state(options: Any) -> dict[Any, Any]:
    """`{configId: currentValue}` of a `configOptions` list, for before/after comparisons."""
    return {
        option["configId"]: option.get("currentValue")
        for option in options or []
        if isinstance(option, dict) and "configId" in option
    }


async def _advertised_config(agent, cwd, *, timeout) -> tuple[str, list[Any]]:
    """`session/new`, returning `(sessionId, configOptions)`; SKIPs when no options are advertised."""
    result = await _new_session_full_result(agent, cwd, timeout=timeout)
    config_options = result.get("configOptions")
    if not isinstance(config_options, list) or not config_options:
        pytest.skip("session/new returned no configOptions")
    return result["sessionId"], config_options


def _settable_options(config_options: list[Any]) -> list[dict[str, Any]]:
    """Options of a type this suite knows how to set (`select`/`boolean`), in advertised order."""
    return [
        option
        for option in config_options
        if isinstance(option, dict)
        and isinstance(option.get("configId"), str)
        and option.get("type") in ("select", "boolean")
    ]


def _no_op_value(option: dict[str, Any]) -> tuple[str, Any]:
    """`(type, value)` that sets `option` to the value it already has."""
    if option["type"] == "boolean":
        return "boolean", option.get("currentValue")
    return "id", option.get("currentValue")


def _error_code(entry) -> Any:
    msg = entry.parsed
    error = msg.get("error") if isinstance(msg, dict) else None
    return error.get("code") if isinstance(error, dict) else None


def _is_error(entry) -> bool:
    msg = entry.parsed
    return isinstance(msg, dict) and isinstance(msg.get("error"), dict)


@pytest.mark.requirement("ACP-CONFIG-207")
async def test_unknown_config_id_is_rejected_with_invalid_params(agent_launch, tmp_path):
    """ACP-CONFIG-207. Sends a `configId` the session never advertised on purpose
    (`_tck_unknown_config`): the spec defines the agent's answer, `-32602`."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        session_id, _options = await _advertised_config(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        entry = await set_config_option(
            agent,
            session_id,
            _UNKNOWN_CONFIG_ID,
            type="id",
            value=_UNKNOWN_VALUE,
            timeout=agent_launch.default_timeout,
        )
        assert _error_code(entry) == INVALID_PARAMS, (
            f"session/set_config_option with an unadvertised configId must be rejected with "
            f"-32602, got: {entry.text!r}"
        )


def _invalid_value_probes(config_options: list[Any]) -> list[tuple[str, dict[str, Any], str, Any]]:
    """`(label, option, type, value)` per invalid-value probe the session's option types allow:
    undeclared select value, `boolean` for a select, `id` for a boolean, unsupported value type."""
    probes: list[tuple[str, dict[str, Any], str, Any]] = []
    settable = _settable_options(config_options)
    select = next((o for o in settable if o["type"] == "select"), None)
    boolean = next((o for o in settable if o["type"] == "boolean"), None)
    if select is not None:
        probes.append(("undeclared select value", select, "id", _UNKNOWN_VALUE))
        probes.append(("boolean value for a select", select, "boolean", True))
    if boolean is not None:
        probes.append(("id value for a boolean", boolean, "id", _UNKNOWN_VALUE))
    if settable:
        probes.append(("unsupported value type", settable[0], _UNSUPPORTED_VALUE_TYPE, 1))
    return probes


@pytest.mark.requirement("ACP-CONFIG-208")
async def test_invalid_config_value_is_rejected_with_invalid_params(agent_launch, tmp_path):
    """ACP-CONFIG-208. Sends values a client must not on purpose (an undeclared select value, a
    mismatched or unsupported value `type`): the spec defines the agent's answer, `-32602`.
    Probes needing an option type the session lacks are skipped. Failures are reported together."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        session_id, config_options = await _advertised_config(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        probes = _invalid_value_probes(config_options)
        if not probes:
            pytest.skip("no select/boolean configOption to send an invalid value to")
        failures = []
        for label, option, value_type, value in probes:
            entry = await set_config_option(
                agent,
                session_id,
                option["configId"],
                type=value_type,
                value=value,
                timeout=agent_launch.default_timeout,
            )
            if _error_code(entry) != INVALID_PARAMS:
                failures.append(f"{label} ({option['configId']!r}): {entry.text!r}")
        assert not failures, "invalid set_config_option values must be rejected with -32602: " + "; ".join(
            failures
        )


@pytest.mark.requirement("ACP-CONFIG-209")
async def test_rejected_config_set_leaves_configuration_unchanged(agent_launch, tmp_path):
    """ACP-CONFIG-209. Sends the probes of `ACP-CONFIG-207`/`208` (an unadvertised `configId`,
    and when a second settable option exists an invalid value for the first), each followed by a
    valid no-op set of a *different* option whose returned list is compared with the previous
    one. Setting the probed option itself would overwrite any damage the probe did, so a session
    whose only option is the follow-up's has nothing to observe through and SKIPs. Only rejected
    probes are judged: after an accepted one (`207`/`208`'s FAIL) the baseline is re-taken. SKIPs
    if a `config_option_update` arrived before a follow-up: the agent may change its own
    configuration (`session-config-options.mdx:459-463`)."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        session_id, config_options = await _advertised_config(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        settable = _settable_options(config_options)
        if not settable:
            pytest.skip("no select/boolean configOption to set")
        follow_up = settable[-1]
        if not any(
            isinstance(option, dict) and option.get("configId") != follow_up["configId"]
            for option in config_options
        ):
            pytest.skip("needs a second option to observe through: the only option is the follow-up's")
        timeout = agent_launch.default_timeout

        probes = [(_UNKNOWN_CONFIG_ID, "id", _UNKNOWN_VALUE)]
        if len(settable) > 1:
            probes.append((settable[0]["configId"], "id", _UNKNOWN_VALUE))

        state = _config_state(config_options)
        rejected = 0
        changed: dict[Any, Any] = {}
        for config_id, probe_type, probe_value in probes:
            start = len(agent.transcript)
            probe = await set_config_option(
                agent, session_id, config_id, type=probe_type, value=probe_value, timeout=timeout
            )
            # Before the follow-up: the valid no-op set may legitimately notify.
            if _config_updates(agent.transcript[start:], session_id):
                pytest.skip("config_option_update observed after a probe; the agent changed its own state")
            value_type, value = _no_op_value(follow_up)
            entry = await set_config_option(
                agent, session_id, follow_up["configId"], type=value_type, value=value, timeout=timeout
            )
            msg = entry.parsed
            result = msg.get("result") if isinstance(msg, dict) else None
            returned = result.get("configOptions") if isinstance(result, dict) else None
            if not isinstance(returned, list):
                pytest.skip(f"the follow-up no-op set did not return a list (ACP-CONFIG-002): {entry.text!r}")
            # An option the reply omits is `ACP-CONFIG-002`'s concern, not a state change.
            after = _config_state(returned)
            if _is_error(probe):
                rejected += 1
                changed.update(
                    {k: (state.get(k, "<absent>"), v) for k, v in after.items() if state.get(k, object()) != v}
                )
            state = {**state, **after}
        if not rejected:
            pytest.skip("the agent accepted every probe (ACP-CONFIG-207/208 judge that)")
        assert not changed, (
            f"configuration changed after rejected probes (configId: (before, after)): {changed!r}"
        )


@pytest.mark.requirement("ACP-CONFIG-210")
async def test_select_values_are_unique_within_an_option(agent_launch, tmp_path):
    """ACP-CONFIG-210. Passive, on `session/new`'s `configOptions`."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        _session_id, config_options = await _advertised_config(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        select_options = [
            option for option in config_options if isinstance(option, dict) and option.get("type") == "select"
        ]
        if not select_options:
            pytest.skip("no select-type configOptions to check")
        for option in select_options:
            values = _flatten_select_values(option.get("options"))
            duplicates = sorted({v for v in values if values.count(v) > 1}, key=repr)
            assert not duplicates, (
                f"config option {option.get('configId')!r} declares value(s) {duplicates!r} more "
                f"than once (across groups included): {values!r}"
            )


def _config_updates(entries: list[Any], session_id: str) -> list[dict[str, Any]]:
    """Every `config_option_update` `session/update` for `session_id` among received `entries`."""
    return [
        message
        for entry in entries
        if entry.direction is Direction.RECEIVED
        for message in iter_messages(entry)
        if message.get("method") == "session/update"
        and isinstance(message.get("params"), dict)
        and message["params"].get("sessionId") == session_id
        and isinstance(message["params"].get("update"), dict)
        and message["params"]["update"].get("sessionUpdate") == "config_option_update"
    ]


async def _state_changing_set(agent_launch, agent, tmp_path):
    """Set an option to a different value and return `(response_state, before_updates,
    after_updates)`: the response's `{configId: currentValue}` and the `config_option_update`
    messages for the session that arrived before the response, or in the quiet drain after it.
    SKIPs when the call changed nothing (a duplicate notification is only owed for a change)."""
    session_id, config_options = await _advertised_config(
        agent, tmp_path, timeout=agent_launch.default_timeout
    )
    target, set_type, new_value = _pick_settable_option(config_options)
    before = _config_state(config_options)
    start = len(agent.transcript)
    entry = await set_config_option(
        agent,
        session_id,
        target["configId"],
        type=set_type,
        value=new_value,
        timeout=agent_launch.default_timeout,
    )
    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/set_config_option did not succeed: {entry.text!r}"
    )
    returned = msg["result"].get("configOptions")
    assert isinstance(returned, list), (
        f"session/set_config_option result.configOptions must be an array, got {returned!r}"
    )
    await drain_quiet(agent, quiet_period(agent_launch.default_timeout))
    transcript = agent.transcript
    end = next((i for i in range(start, len(transcript)) if transcript[i] is entry), len(transcript))
    state = _config_state(returned)
    if state == before:
        pytest.skip("session/set_config_option changed nothing")
    return (
        state,
        _config_updates(transcript[start:end], session_id),
        _config_updates(transcript[end + 1 :], session_id),
    )


@pytest.mark.requirement("ACP-CONFIG-211")
async def test_state_changing_set_is_accompanied_by_config_option_update(agent_launch, tmp_path):
    """ACP-CONFIG-211 (ADVISORY). A set that changed the configuration is also notified, before
    the response or in the quiet drain after it. Only the requesting connection is observable."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        _state, early, late = await _state_changing_set(agent_launch, agent, tmp_path)
        assert early or late, (
            "session/set_config_option changed the configuration but no config_option_update "
            "was sent on the requesting connection"
        )


@pytest.mark.requirement("ACP-CONFIG-212")
async def test_config_option_update_precedes_the_set_response(agent_launch, tmp_path):
    """ACP-CONFIG-212 (ADVISORY). Judged on updates carrying the response's state: a later update
    with different state may be a legitimate subsequent change. SKIPs when none matches."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        state, early, late = await _state_changing_set(agent_launch, agent, tmp_path)

        def matches(message: dict[str, Any]) -> bool:
            return _config_state(message["params"]["update"].get("configOptions")) == state

        if not any(matches(m) for m in early + late):
            pytest.skip("no config_option_update carrying the response's state was observed")
        assert any(matches(m) for m in early), (
            "the config_option_update duplicating the set change arrived only after the "
            "session/set_config_option response"
        )
