"""Stopping a subagent: ACP-SUBAGENT-016/017/202 and, for a child's own tool call or terminal,
ACP-TOOLCANCEL-203 and ACP-TERMCANCEL-203.

A child that advertises `capabilities.cancel` (`SubagentSessionCapabilities`) may be cancelled with
`session/cancel` carrying the child's `sessionId`; that cancels the child's current work, not its
parent or its siblings, and the child confirms with `idle` and `stopReason: "cancelled"`
(RFD:1069-1073,1089-1093). Cancelling a session's work also cancels the descendant work it waits on
(RFD:1075-1087). A child's tool call or terminal that advertises its own `cancel` is cancelled with
`tool_call/cancel` / `terminal/cancel` sent with the child's `sessionId`, whether or not the child
advertises `cancel` (tool-calls.mdx:457,603).

No `initialize` marker announces any of this (the per-child capability is not an `initialize`
capability), so each `Requirement.capability` is a documentation-only `inferred:` string
(`subagentCancel`, `subagents`, `toolCallCancel`, `terminalCancel`), the tests carry no
`@pytest.mark.capability(...)` marker and SKIP themselves when nothing was exercised. One driven
turn (`drive_child_cancel`: the cancel prompt, so a real agent still has a running child) serves
every row, made by the first test that asks and reused by the rest. The request goes only to a
child that advertises `cancel` and was last reported running, since a client MUST NOT cancel one
that does not; a cancel that races with work that has already ended does not rewrite its outcome,
so it is not judged (see `_child_cancel.py`). 016 judges the confirmation, 017 that the parent and
the siblings were left alone, so one defect fails one row.

The module and its tests are named without "cancel": the CLI self-tests select the cancellation
suite with `-k cancel`, and a defect fixture that hangs on `session/cancel` must not be judged here.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.plugin import register_active_process
from tck.v2.validation import validate_def_value

from ._child_cancel import ChildCancelRun, drive_child_cancel
from ._helpers import ItemCancel, new_session, v2_only_agent

_RUN_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one driven turn, in `config.stash`: `agent` and `run` once it completed, or `error`
(the exception it ended with) so every row sees the same outcome."""


async def _child_run(
    request: pytest.FixtureRequest, agent_launch, tmp_path, cancel_prompt_text: str
) -> ChildCancelRun:
    cache = request.config.stash.setdefault(_RUN_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "run" in cache:
        register_active_process(cache["agent"])
        return cache["run"]
    try:
        async with v2_only_agent(agent_launch, require_session=True) as agent:
            session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            run = await drive_child_cancel(
                agent, session_id, cancel_prompt_text, timeout=agent_launch.default_timeout
            )
            cache.update(agent=agent, run=run)
    except BaseException as exc:
        cache["error"] = exc
        raise
    return run


def _skip_unless_child_cancelled(run: ChildCancelRun) -> None:
    if run.target is None:
        pytest.skip("no child advertised capabilities.cancel while reported running during the driven turn")
    if run.outcome == "raced":
        pytest.skip(
            f"child {run.target!r} ended on its own before the agent read session/cancel: "
            "a cancel racing with ended work is not judged"
        )


@pytest.mark.requirement("ACP-SUBAGENT-016")
async def test_child_stop_is_confirmed_by_the_child(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-SUBAGENT-016 (CAPABILITY, `inferred:subagentCancel`). After `session/cancel` for a
    running child that advertises `capabilities.cancel`, the child reports `idle` with
    `stopReason: "cancelled"` (on its own session or mirrored on its parent association). SKIPs
    when no such child was running or it ended first."""
    run = await _child_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _skip_unless_child_cancelled(run)
    assert run.outcome == "confirmed", (
        f"session/cancel for child {run.target!r}, which advertised capabilities.cancel and was "
        "running, was not followed by an idle state_update with stopReason 'cancelled' for it "
        "within the timeout"
    )


@pytest.mark.requirement("ACP-SUBAGENT-017")
async def test_child_stop_leaves_parent_and_siblings(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-SUBAGENT-017 (CAPABILITY, `inferred:subagentCancel`). `session/cancel` for a child
    cancels that child's work, not its parent or its siblings: neither the parent nor another
    child (outside the cancelled child's own subtree) reports `idle`/`cancelled` because of it.
    SKIPs when no such child was running or it ended first."""
    run = await _child_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _skip_unless_child_cancelled(run)
    problems = []
    if run.parent_cancelled:
        problems.append("the parent reported idle/cancelled")
    if run.cancelled_siblings:
        problems.append(f"sibling(s) {run.cancelled_siblings!r} reported idle/cancelled")
    assert not problems, (
        f"after session/cancel for child {run.target!r}: {'; '.join(problems)}"
    )


@pytest.mark.requirement("ACP-SUBAGENT-202")
async def test_parent_stop_reaches_the_children_it_waits_on(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-SUBAGENT-202 (CAPABILITY, `inferred:subagents`). Cancelling the parent's turn also
    cancels a descendant it is waiting on: each descendant that was running when the TCK sent
    `session/cancel` and is not in its parent's latest `background` list reaches `idle`. SKIPs
    when the parent's turn did not end `cancelled`, or no such descendant was running (an agent
    that reports no `background` list leaves every child unclassified)."""
    run = await _child_run(request, agent_launch, tmp_path, cancel_prompt_text)
    if run.cascade_skip is not None:
        pytest.skip(run.cascade_skip)
    if not run.cascade_judged:
        pytest.skip(
            "no descendant was both running and known to be foreground (not in its parent's "
            "reported `background` list) when the parent was cancelled"
        )
    assert not run.cascade_unstopped, (
        f"the parent's turn ended cancelled but descendant(s) {run.cascade_unstopped!r}, running "
        "and not in a `background` list, did not reach idle within the timeout"
    )


def _judge_child_item(
    result: ItemCancel, child_id: str | None, noun: str, method: str, response_def: str, confirmation: str
) -> None:
    if result.outcome == "none":
        pytest.skip(f"no child's {noun} advertised capabilities.cancel while live during the driven turn")
    if result.outcome == "raced":
        pytest.skip(
            f"every child {noun} that advertised capabilities.cancel was already final when the "
            "agent read the request"
        )
    where = f"{noun} {result.item_id!r} of child {child_id!r}"
    assert result.outcome != "rejected", (
        f"{method} with the child's sessionId for {where}, which advertises capabilities.cancel "
        f"and had no final update, was answered with an error: {result.error!r}"
    )
    assert result.outcome != "unanswered", f"{method} for {where} got no response within the timeout"
    issues = validate_def_value(response_def, result.result)
    assert not issues, f"{method} result {result.result!r} is not a valid {response_def}: {issues!r}"
    assert result.outcome == "confirmed", (
        f"{method} for {where} was accepted, but {confirmation} did not follow within the timeout"
    )


@pytest.mark.requirement("ACP-TOOLCANCEL-203")
async def test_child_tool_call_request_is_accepted_and_confirmed(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TOOLCANCEL-203 (CAPABILITY, `inferred:toolCallCancel`). `tool_call/cancel` sent with
    the child's `sessionId` for a child tool call that advertises `capabilities.cancel` and is not
    final gets an empty result, then a `tool_call_update` to a final status, even when the child
    itself advertises no `cancel` (tool-calls.mdx:457-459). SKIPs when no child tool call
    advertises `cancel` while live."""
    run = await _child_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_child_item(
        run.tool_call,
        run.tool_call_child,
        "tool call",
        "tool_call/cancel",
        "CancelToolCallResponse",
        "a tool_call_update to a final status",
    )


@pytest.mark.requirement("ACP-TERMCANCEL-203")
async def test_child_terminal_request_is_accepted_and_confirmed(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TERMCANCEL-203 (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` sent with the
    child's `sessionId` for a child terminal that advertises `capabilities.cancel` and has no
    `exitStatus` gets an empty result, then a `terminal_update` that sets `exitStatus`, even when
    the child itself advertises no `cancel` (tool-calls.mdx:603-605). SKIPs when no child terminal
    advertises `cancel` while running."""
    run = await _child_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_child_item(
        run.terminal,
        run.terminal_child,
        "terminal",
        "terminal/cancel",
        "CancelTerminalResponse",
        "a terminal_update that sets exitStatus",
    )
