"""`session/new` conformance: ACP-SESSION-001/002 (see `tck.v2.requirements`'s module docstring
for the id-namespacing decision -- reused from v1, but `Tier.CAPABILITY` here, gated on
`capabilities.session`, since v2's session surface is opt-in), the relative-`cwd` rejection
(ACP-SESSION-204/209) and the initial-state rules (ACP-SESSION-206..208).

`ACP-SESSION-206`/`207` are ADVISORY (SHOULD NOT / SHOULD); their tests still carry a
`@pytest.mark.capability(...)` marker purely for the SKIP gate, as `ACP-CLOSE-204` does.
"""

from __future__ import annotations

from typing import Any

from tck.common.harness import AgentProcess, Direction
from tck.v2.validation import validate_agent_response

import pytest

from ..protocol import INVALID_PARAMS
from ._helpers import connected_agent, iter_messages, new_session, skip_if_auth_gated


@pytest.mark.requirement("ACP-SESSION-001")
@pytest.mark.capability("capabilities.session")
async def test_session_new_returns_unique_string_id(agent_launch, tmp_path):
    """ACP-SESSION-001. `session/new` with an absolute `cwd` and no `mcpServers` succeeds with a
    non-empty string `sessionId`, and the response validates against the v2 schema.
    """
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/new", {"cwd": str(tmp_path)})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
            f"session/new did not return a result object: {entry.text!r}"
        )
        session_id = msg["result"].get("sessionId")
        assert isinstance(session_id, str) and session_id, (
            f"sessionId must be a non-empty string, got {session_id!r}"
        )
        issues = validate_agent_response("session/new", msg)
        assert not issues, f"session/new result failed schema validation: {issues!r}"


@pytest.mark.requirement("ACP-SESSION-002")
@pytest.mark.capability("capabilities.session")
async def test_session_new_ids_are_unique(agent_launch, tmp_path):
    """ACP-SESSION-002. Two `session/new` calls on one connection return distinct `sessionId`s."""
    async with connected_agent(agent_launch) as agent:
        first_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        second_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        assert first_id != second_id, (
            f"two session/new calls returned the same sessionId: {first_id!r}"
        )


async def _relative_cwd_response(agent_launch) -> tuple[Any, dict[str, Any] | None]:
    """`session/new` with a relative `cwd`; returns the response entry and its `error` object (or
    `None` when the agent answered with anything else). Skips an auth-gated agent."""
    async with connected_agent(agent_launch) as agent:
        req_id = await agent.send_request("session/new", {"cwd": "tck-relative-dir"})
        entry = await agent.wait_for_response(req_id, timeout=agent_launch.default_timeout)
        skip_if_auth_gated(entry)
        msg = entry.parsed
        error = msg.get("error") if isinstance(msg, dict) else None
        return entry, error if isinstance(error, dict) else None


@pytest.mark.requirement("ACP-SESSION-204")
@pytest.mark.capability("capabilities.session")
async def test_session_new_with_relative_cwd_is_rejected(agent_launch):
    """ACP-SESSION-204. Sends a relative `cwd` on purpose: the spec defines the agent's answer to
    exactly this input (`session-setup.mdx:524`). Only error-vs-result is asserted: the sentence
    naming `-32602` carries no RFC keyword, so the code is ACP-SESSION-209's (ADVISORY)
    concern."""
    entry, error = await _relative_cwd_response(agent_launch)
    assert error is not None, (
        f"session/new with a relative cwd must be rejected with an error, got: {entry.text!r}"
    )


@pytest.mark.requirement("ACP-SESSION-209")
@pytest.mark.capability("capabilities.session")
async def test_session_new_relative_cwd_rejection_is_invalid_params(agent_launch):
    """ACP-SESSION-209 (ADVISORY). The rejection of a relative `cwd` is `-32602`
    (`session-setup.mdx:524`; no RFC keyword, hence ADVISORY). SKIPs when the probe was not
    rejected: that is ACP-SESSION-204's failure, not a second one."""
    entry, error = await _relative_cwd_response(agent_launch)
    if error is None:
        pytest.skip(f"session/new with a relative cwd was not rejected: {entry.text!r}")
    assert error.get("code") == INVALID_PARAMS, (
        f"session/new with a relative cwd was rejected with {error.get('code')!r}, expected "
        f"-32602 (Invalid params): {entry.text!r}"
    )
_LIST_UPDATE_FIELDS = {
    "config_option_update": "configOptions",
    "available_commands_update": "availableCommands",
}


async def _new_session_with_early_traffic(
    agent: AgentProcess, cwd: Any, *, timeout: float
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    """`session/new`, returning `(sessionId, result, early)`: `early` is every message the agent
    sent between the request and the response, in wire order, that carries the new `sessionId`
    in its `params` (a `session/update` or an agent -> client request)."""
    start = len(agent.transcript)
    req_id = await agent.send_request("session/new", {"cwd": str(cwd)})
    entry = await agent.wait_for_response(req_id, timeout=timeout)
    skip_if_auth_gated(entry)
    msg = entry.parsed
    assert isinstance(msg, dict) and isinstance(msg.get("result"), dict), (
        f"session/new did not return a result object: {entry.text!r}"
    )
    result = msg["result"]
    session_id = result.get("sessionId")
    assert isinstance(session_id, str) and session_id, (
        f"session/new result.sessionId must be a non-empty string, got {session_id!r}"
    )
    end = next(
        (i for i, candidate in enumerate(agent.transcript) if candidate is entry),
        len(agent.transcript),
    )
    early = []
    for candidate in agent.transcript[start:end]:
        if candidate.direction is not Direction.RECEIVED:
            continue
        for message in iter_messages(candidate):
            params = message.get("params")
            if (
                "method" in message
                and isinstance(params, dict)
                and params.get("sessionId") == session_id
            ):
                early.append(message)
    return session_id, result, early


@pytest.mark.requirement("ACP-SESSION-206")
@pytest.mark.capability("capabilities.session")
async def test_no_session_scoped_request_before_session_new_response(agent_launch, tmp_path):
    """ACP-SESSION-206 (ADVISORY). Any agent -> client request naming the new session, read
    before the `session/new` response, FAILs. It is left unanswered: the client cannot show it."""
    async with connected_agent(agent_launch) as agent:
        session_id, _result, early = await _new_session_with_early_traffic(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        requests = [message for message in early if "id" in message]
        assert not requests, (
            f"the agent sent session-scoped request(s) for {session_id!r} before the "
            f"session/new response: {[(m.get('method'), m.get('id')) for m in requests]!r}"
        )


def _early_updates(early: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [
        message["params"]["update"]
        for message in early
        if message.get("method") == "session/update"
        and isinstance(message["params"].get("update"), dict)
        and message["params"]["update"].get("sessionUpdate") == kind
    ]


@pytest.mark.requirement("ACP-SESSION-207")
@pytest.mark.capability("capabilities.session")
async def test_no_config_or_commands_update_before_session_new_response(agent_launch, tmp_path):
    """ACP-SESSION-207 (ADVISORY). Initial `configOptions`/`availableCommands` belong in the
    response. A `state_update` before it is allowed and not judged."""
    async with connected_agent(agent_launch) as agent:
        _session_id, _result, early = await _new_session_with_early_traffic(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        sent = [kind for kind in _LIST_UPDATE_FIELDS if _early_updates(early, kind)]
        assert not sent, (
            f"the agent notified {sent!r} before the session/new response instead of putting "
            "the lists in it"
        )


@pytest.mark.requirement("ACP-SESSION-208")
@pytest.mark.capability("capabilities.session")
async def test_list_notified_before_session_new_response_is_in_the_response(
    agent_launch, tmp_path, record_property
):
    """ACP-SESSION-208. The latest non-empty `config_option_update`/`available_commands_update`
    read before the response means the session has that list, so the response must carry it
    (a setup response replaces the client's lists). Vacuous -- recorded, never FAILed -- when
    no such notification precedes the response."""
    async with connected_agent(agent_launch) as agent:
        _session_id, result, early = await _new_session_with_early_traffic(
            agent, tmp_path, timeout=agent_launch.default_timeout
        )
        checked = []
        for kind, field in _LIST_UPDATE_FIELDS.items():
            updates = _early_updates(early, kind)
            if not updates:
                continue
            notified = updates[-1].get(field)
            if not isinstance(notified, list) or not notified:
                continue
            checked.append(field)
            in_response = result.get(field)
            assert isinstance(in_response, list) and in_response, (
                f"a non-empty {field} was notified before the session/new response, but the "
                f"response carries {in_response!r}"
            )
        record_property("acp_tck_session_early_lists_checked", ",".join(checked) or "none")
