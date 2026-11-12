"""Permission requests: ACP-PERM-201..204 and ACP-PERM-002.

All are `Tier.CAPABILITY`, `capability="capabilities.session"` -- see `tck.v2.requirements`'s
module docstring for the tiering rule. Each SKIPs when the agent's turn sends no
`session/request_permission` at all (sending one is only MAY), and ACP-PERM-203/204/002 also when
no request carries a `tool_call` subject: the denied operation is observable only as that tool
call's status.

ACP-PERM-002 shares v1's id (the same rule): it answers `selected` with an `optionId` the agent
never offered (`_tck_unoffered_option`). That breaks the client rule that `optionId` names an
offered option, which is allowed here because the spec defines the agent's answer: not
approved (`tool-calls.mdx:346-347`).

ACP-PERM-204 answers a `_`-prefixed custom outcome (`_tck_unknown`). That is a legal client
answer (the outcome is an open enum), and an agent that does not understand it must not treat
it as approval (`tool-calls.mdx:348-349`).
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from tck.v2.validation import validate_agent_message

from ._helpers import (
    PermissionPolicy,
    connected_agent,
    new_session,
    run_prompt,
    session_events,
    tool_call_report,
)

_PROMPT_TEXT = "hi"


async def _drive_one_turn(agent_launch, tmp_path, permission: PermissionPolicy = "allow"):
    async with connected_agent(agent_launch) as agent:
        session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
        return await run_prompt(
            agent,
            session_id,
            [{"type": "text", "text": _PROMPT_TEXT}],
            permission=permission,
            timeout=agent_launch.default_timeout,
        )


def _permission_params(turn) -> list[dict[str, Any]]:
    """The params of every `session/request_permission` observed during `turn`."""
    result = []
    for _, entry in turn.permission_requests:
        params = entry.parsed.get("params") if isinstance(entry.parsed, dict) else None
        result.append(params if isinstance(params, dict) else {})
    return result


@pytest.mark.requirement("ACP-PERM-201")
@pytest.mark.capability("capabilities.session")
async def test_request_permission_shape_and_turn_completes(agent_launch, tmp_path):
    """ACP-PERM-201. Any `session/request_permission` request observed during the turn
    validates against the v2 schema (required `sessionId`/`title`/`options`, at least one
    option, each with `optionId`/`name`/`kind`). Once the mock client answers with a `selected`
    outcome (`run_prompt` prefers an `allow_*` option), the turn still reaches an idle.
    """
    turn = await _drive_one_turn(agent_launch, tmp_path)
    permission_requests = [
        entry
        for entry in turn.client_requests_seen
        if isinstance(entry.parsed, dict)
        and entry.parsed.get("method") == "session/request_permission"
    ]
    if not permission_requests:
        pytest.skip("no permission request observed during this turn")

    for entry in permission_requests:
        issues = validate_agent_message(entry.parsed)
        assert not issues, f"session/request_permission failed schema validation: {issues!r}"

    assert turn.idle_update is not None, (
        "a session/request_permission was answered with a selected outcome, but the turn "
        "ended with an error response instead of an idle state_update"
    )


@pytest.mark.requirement("ACP-PERM-202")
@pytest.mark.capability("capabilities.session")
async def test_request_permission_option_ids_unique_and_command_cwd_absolute(agent_launch, tmp_path):
    """ACP-PERM-202. In every `session/request_permission` observed during the turn, the
    `options[].optionId` values are pairwise distinct (`tool-calls.mdx:357`), and a `command`
    subject's `cwd` is an absolute path (:302-303). Both are schema-valid when broken
    (`AbsolutePath` is a plain string), so they are checked here."""
    turn = await _drive_one_turn(agent_launch, tmp_path)
    requests = _permission_params(turn)
    if not requests:
        pytest.skip("no permission request observed during this turn")
    for params in requests:
        options = params.get("options")
        option_ids = [
            option.get("optionId")
            for option in (options if isinstance(options, list) else [])
            if isinstance(option, dict) and "optionId" in option
        ]
        duplicates = sorted({repr(i) for i in option_ids if option_ids.count(i) > 1})
        assert not duplicates, (
            f"session/request_permission offers the optionId(s) {', '.join(duplicates)} more "
            f"than once: {options!r}"
        )
        subject = params.get("subject")
        if isinstance(subject, dict) and subject.get("type") == "command":
            cwd = subject.get("cwd")
            assert not isinstance(cwd, str) or os.path.isabs(cwd), (
                f"a command permission subject's cwd must be an absolute path, got {cwd!r}"
            )


async def _assert_denied_tool_call_not_completed(agent_launch, tmp_path, policy: PermissionPolicy) -> None:
    """Answer every permission request per `policy` (which denies it) and assert that no tool
    call named by a `tool_call` subject is reported `completed` afterwards, by a
    `tool_call_update` or a later subject."""
    turn = await _drive_one_turn(agent_launch, tmp_path, permission=policy)
    denied: set[str] = set()
    for _, kind, payload in session_events(turn):
        report = tool_call_report(kind, payload)
        if report is None:
            continue
        tool_call_id, source, fields = report
        if tool_call_id in denied:
            assert fields.get("status") != "completed", (
                f"tool call {tool_call_id!r} was reported completed (via a {source}) after its "
                f"permission request was answered with policy {policy!r}"
            )
        if source == "permission subject":
            denied.add(tool_call_id)
    if not denied:
        pytest.skip("no permission request with a tool_call subject observed during this turn")


# Named without "cancel": the CLI self-tests select the cancellation suite with `-k cancel`.
@pytest.mark.requirement("ACP-PERM-203")
@pytest.mark.capability("capabilities.session")
async def test_declined_permission_tool_call_not_completed(agent_launch, tmp_path):
    """ACP-PERM-203. The mock client declines every permission request by policy with the
    `cancelled` outcome (no `session/cancel`; tool-calls.mdx:340). After that, the agent must
    not proceed, so the subject's tool call is never reported `completed` (:340,423). The stop
    reason a declined turn ends with is not judged."""
    await _assert_denied_tool_call_not_completed(agent_launch, tmp_path, "cancelled")


@pytest.mark.requirement("ACP-PERM-002")
@pytest.mark.capability("capabilities.session")
async def test_unknown_option_is_not_approval(agent_launch, tmp_path):
    """ACP-PERM-002. The mock client answers every permission request `selected` with an
    `optionId` the agent never offered. The agent must treat it as not approved
    (`tool-calls.mdx:346-347`), so the subject's tool call is never reported `completed`
    (:423)."""
    await _assert_denied_tool_call_not_completed(agent_launch, tmp_path, "unknown_option")


@pytest.mark.requirement("ACP-PERM-204")
@pytest.mark.capability("capabilities.session")
async def test_unknown_outcome_is_not_approval(agent_launch, tmp_path):
    """ACP-PERM-204. The mock client answers every permission request with the custom outcome
    `_tck_unknown`. An agent that does not understand it must not treat it as approval
    (`tool-calls.mdx:348-349`), so the subject's tool call is never reported `completed`
    (:423)."""
    await _assert_denied_tool_call_not_completed(agent_launch, tmp_path, "unknown_outcome")
