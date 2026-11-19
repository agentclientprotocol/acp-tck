"""Stopping a subagent: ACP-SUBAGENT-016/017/202/204 and, for a child's own tool call or terminal,
ACP-TOOLCANCEL-203 and ACP-TERMCANCEL-203; and closing the parent, ACP-SUBAGENT-203.

A child that advertises `capabilities.cancel` (`SubagentSessionCapabilities`) may be cancelled with
`session/cancel` carrying the child's `sessionId`; that cancels the child's current work, not its
parent or its siblings, and the child confirms with `idle` and `stopReason: "cancelled"` in its own
`state_update` (`subagents.mdx:386,398,400`; the mirror on the parent is a SHOULD, judged by
`ACP-SUBAGENT-201`), or reports `unknown` when it can no longer observe the child
(`subagents.mdx:401`: the row SKIPs). Cancelling a session's work also cancels the descendant work it waits on
(`subagents.mdx:405`). A child's tool call or terminal that advertises its own `cancel` is cancelled with
`tool_call/cancel` / `terminal/cancel` sent with the child's `sessionId`, whether or not the child
advertises `cancel` (tool-calls.mdx:457,603).

No `initialize` marker announces any of this (the per-child capability is not an `initialize`
capability), so each `Requirement.capability` is a documentation-only `inferred:` string
(`subagentCancel`, `subagents`, `toolCallCancel`, `terminalCancel`), the tests carry no
`@pytest.mark.capability(...)` marker and SKIP themselves when nothing was exercised. One driven
turn (`drive_child_cancel`: `--subagent-cancel-prompt`, else the cancel prompt, so a real agent
still has a running child) serves every row, made by the first test that asks and reused by the rest. The request goes only to a
child that advertises `cancel` and was last reported running, since a client MUST NOT cancel one
that does not; a cancel that races with work that has already ended does not rewrite its outcome,
so a child that ends otherwise within the race window (`quiet_period`, as for `ACP-CANCEL-*`) is not
judged, while one that finishes later without cancelling is (see `_child_cancel.py`). 016 judges
the confirmation, 017 that the parent was left alone (a stopped sibling is only recorded: the
Agent may cancel its own delegated work), so one defect fails one row. The turn holds the children's
permission requests, and 204 judges that a stopped child's are withdrawn and that its confirmation
did not wait for them (`_child_cancel.py`).

203 has its own connection: one turn of `--subagent-prompt` (else `hi`) whose child permission
requests are held, and `session/close` for the prompted session once the first arrives. Before the
close response the Agent cancels them with `$/cancel_request` (`subagents.mdx:427`), the
`ACP-CLOSE-205` scenario on a descendant's requests. It is gated on `capabilities.session`, which
makes `session/close` baseline.

The module and its tests are named without "cancel": the CLI self-tests select the cancellation
suite with `-k cancel`, and a defect fixture that hangs on `session/cancel` must not be judged here.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.harness import AgentTimeout
from tck.common.plugin import register_active_process
from tck.v2.validation import validate_def_value

from ._child_cancel import ChildCancelRun, drive_child_cancel, stopped_requests_kept
from ._helpers import (
    ChildPermissionHold,
    ItemCancel,
    announced_children,
    new_session,
    quiet_period,
    run_prompt,
    v2_only_agent,
)

_DEFAULT_PROMPT_TEXT = "hi"

_RUN_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one driven turn, in `config.stash`: `agent` and `run` once it completed, or `error`
(the exception it ended with) so every row sees the same outcome."""


async def _child_run(
    request: pytest.FixtureRequest, agent_launch, tmp_path, subagent_cancel_prompt_text: str
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
                agent, session_id, subagent_cancel_prompt_text, timeout=agent_launch.default_timeout
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
            f"child {run.target!r} ended on its own before the agent read session/cancel (within "
            "the race window): a cancel racing with ended work is not judged"
        )


@pytest.mark.requirement("ACP-SUBAGENT-016")
async def test_child_stop_is_confirmed_by_the_child(request, agent_launch, tmp_path, subagent_cancel_prompt_text):
    """ACP-SUBAGENT-016 (CAPABILITY, `inferred:subagentCancel`). After `session/cancel` for a
    running child that advertises `capabilities.cancel`, the child reports `idle` with
    `stopReason: "cancelled"` in a `state_update` on its own session; a mirror on the parent
    association alone does not confirm it (`subagents.mdx:400`; the mirror is a SHOULD, judged by
    `ACP-SUBAGENT-201`). SKIPs when no such child was running or it ended on its own within the
    race window, and when the child reported `unknown` after the request and no `idle` followed, or
    a non-cancelled one came straight after it: an Agent that can no longer observe the child
    reports `unknown` instead of a confirmation (`subagents.mdx:401`), so the cancellation is not
    observable. A later `running` or `requires_action` replaces `unknown` (`subagents.mdx:363`)."""
    run = await _child_run(request, agent_launch, tmp_path, subagent_cancel_prompt_text)
    _skip_unless_child_cancelled(run)
    if run.outcome == "unobservable":
        pytest.skip(
            f"cancellation not observable: child {run.target!r} reported `unknown` after "
            "session/cancel and no idle state_update, or only a non-cancelled one, followed (the "
            "Agent could no longer observe it)"
        )
    assert run.outcome != "not_cancelled", (
        f"session/cancel for child {run.target!r}, which advertised capabilities.cancel and was "
        "running, was followed by an idle state_update without stopReason 'cancelled' after the "
        "race window: the child finished by other means instead of stopping"
    )
    assert run.outcome == "confirmed", (
        f"session/cancel for child {run.target!r}, which advertised capabilities.cancel and was "
        "running, was not followed by an idle state_update with stopReason 'cancelled' on the "
        "child's own session within the timeout (a mirror on the parent alone does not confirm it)"
    )


@pytest.mark.requirement("ACP-SUBAGENT-017")
async def test_child_stop_leaves_the_parent_running(
    request, agent_launch, tmp_path, subagent_cancel_prompt_text, record_property
):
    """ACP-SUBAGENT-017 (CAPABILITY, `inferred:subagentCancel`). `session/cancel` for a child
    cancels that child's work, not its parent: the parent does not report `idle`/`cancelled`
    because of it. Siblings are not judged, since the per-child capability does not prevent the
    Agent from cancelling its own delegated work (`subagents.mdx:398`) and that is indistinguishable
    from a leaked cancel; a sibling that reports `idle`/`cancelled` is recorded as
    `acp_tck_cancelled_siblings`. SKIPs when no such child was running or it ended on its own
    within the race window."""
    run = await _child_run(request, agent_launch, tmp_path, subagent_cancel_prompt_text)
    _skip_unless_child_cancelled(run)
    if run.cancelled_siblings:
        record_property("acp_tck_cancelled_siblings", ", ".join(run.cancelled_siblings))
    assert not run.parent_cancelled, (
        f"after session/cancel for child {run.target!r}, the parent reported idle/cancelled"
    )


@pytest.mark.requirement("ACP-SUBAGENT-202")
async def test_parent_stop_reaches_the_children_it_waits_on(
    request, agent_launch, tmp_path, subagent_cancel_prompt_text
):
    """ACP-SUBAGENT-202 (CAPABILITY, `inferred:subagents`). Cancelling the parent's turn also
    cancels a descendant it is waiting on: each descendant that was running when the TCK sent
    `session/cancel` and is not in its parent's latest `background` list reaches `idle`. SKIPs
    when the parent's turn did not end `cancelled`, or no such descendant was running (an agent
    that reports no `background` list leaves every child unclassified)."""
    run = await _child_run(request, agent_launch, tmp_path, subagent_cancel_prompt_text)
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


@pytest.mark.requirement("ACP-SUBAGENT-204")
async def test_stopped_childrens_permission_requests_are_withdrawn(
    request, agent_launch, tmp_path, subagent_cancel_prompt_text, record_property
):
    """ACP-SUBAGENT-204 (CAPABILITY, `inferred:subagents`). In the driven turn every child
    permission request is held. For each child that reports its own `idle`/`cancelled` after a TCK
    cancellation covering it, each request it sent before that and the TCK had not answered by then
    is withdrawn with `$/cancel_request` before that `idle` or within `quiet_period` after it
    (`subagents.mdx:417`), unless its `subject` names an item in the child's latest `background`
    list as of that `idle` (prompt-lifecycle.mdx:1452; `stopped_requests_kept`). A cancelled child
    that settled within `quiet_period` after the TCK answered its held requests at `timeout / 2`
    waited for them (`subagents.mdx:421`). SKIPs when no held request was pending when its
    session was stopped and no cancelled child waited for its requests."""
    run = await _child_run(request, agent_launch, tmp_path, subagent_cancel_prompt_text)
    transcript = request.config.stash[_RUN_KEY]["agent"].transcript
    judged, kept = stopped_requests_kept(run, transcript, quiet_period(agent_launch.default_timeout))
    record_property("acp_tck_stopped_child_requests_judged", len(judged))
    waited = run.released and run.settled_after_release and run.outcome == "confirmed"
    if not judged and not waited:
        pytest.skip(
            "no held child session/request_permission was pending when a cancellation stopped its "
            "session, and no cancelled child waited for its requests"
        )
    assert not waited, (
        f"child {run.target!r} confirmed its cancellation right after the TCK answered its held "
        "permission requests: the Agent does not wait for a child's pending requests before it "
        "reports the child's state"
    )
    assert not kept, (
        f"pending permission request(s) {kept} (session, request id) of child sessions stopped by a "
        "cancellation were not withdrawn with $/cancel_request by the child's cancelled idle or "
        "shortly after it"
    )


@pytest.mark.requirement("ACP-SUBAGENT-203")
@pytest.mark.capability("capabilities.session")
async def test_closing_the_parent_withdraws_child_permission_requests(
    agent_launch, tmp_path, subagent_prompt_text, record_property
):
    """ACP-SUBAGENT-203. A turn whose child permission requests are held, with `session/close` for
    the prompted session sent when the first arrives (else after `timeout / 2`): every request of
    an announced descendant that arrived before the close response, and that the TCK had not
    answered by then, needs a `$/cancel_request` naming it before that response
    (`subagents.mdx:427`). SKIPs when no child request was held when the close was sent, the
    close did not succeed, or the turn never ended (the close-cancels-work rows judge that)."""
    timeout = agent_launch.default_timeout
    hold = ChildPermissionHold()
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        session_id = await new_session(agent, tmp_path, timeout=timeout)

        async def _close():
            return await agent.send_request("session/close", {"sessionId": session_id})

        try:
            turn = await run_prompt(
                agent,
                session_id,
                [{"type": "text", "text": subagent_prompt_text or _DEFAULT_PROMPT_TEXT}],
                on_action=_close,
                hold_children=hold,
                cancel_wait=timeout / 2,
                timeout=timeout,
            )
        except AgentTimeout:
            pytest.skip("the turn never ended after session/close -- see ACP-CANCEL-208/CLOSE-002")
        close_at = turn.action_sent_at_index
        if close_at is None or not any(held.index < close_at for held in hold.requests):
            pytest.skip("no child session/request_permission was held when session/close was sent")
        close_entry = turn.action_response
        if close_entry is None:
            close_id = agent.transcript[close_at].parsed["id"]
            try:
                close_entry = await agent.wait_for_response(close_id, timeout=timeout)
            except AgentTimeout:
                pytest.skip("session/close was never answered -- not a successful close")
        close_index = agent.transcript.index(close_entry)
        if not (isinstance(close_entry.parsed, dict) and "result" in close_entry.parsed):
            pytest.skip(f"session/close did not succeed: {close_entry.text!r}")
        descendants = set(announced_children(agent.transcript, {session_id}))
        judged = [
            held
            for held in hold.requests
            if held.index < close_index
            and held.session_id in descendants
            and (held.answered_on == "cancel_request" or held.answered_at is None or held.answered_at > close_index)
        ]
    record_property("acp_tck_child_requests_pending_at_close", len(judged))
    if not judged:
        pytest.skip("no held request belonged to an announced descendant of the closed session")
    kept = [
        (held.session_id, held.request_id)
        for held in judged
        if held.withdrawn_at is None or held.withdrawn_at > close_index
    ]
    assert not kept, (
        f"session/close was answered before the agent sent $/cancel_request for the pending "
        f"permission request(s) {kept} (session, request id) of the closed session's descendants"
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
    request, agent_launch, tmp_path, subagent_cancel_prompt_text
):
    """ACP-TOOLCANCEL-203 (CAPABILITY, `inferred:toolCallCancel`). `tool_call/cancel` sent with
    the child's `sessionId` for a child tool call that advertises `capabilities.cancel` and is not
    final gets an empty result, then a `tool_call_update` to a final status, even when the child
    itself advertises no `cancel` (tool-calls.mdx:457-459). SKIPs when no child tool call
    advertises `cancel` while live."""
    run = await _child_run(request, agent_launch, tmp_path, subagent_cancel_prompt_text)
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
    request, agent_launch, tmp_path, subagent_cancel_prompt_text
):
    """ACP-TERMCANCEL-203 (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` sent with the
    child's `sessionId` for a child terminal that advertises `capabilities.cancel` and has no
    `exitStatus` gets an empty result, then a `terminal_update` that sets `exitStatus`, even when
    the child itself advertises no `cancel` (tool-calls.mdx:603-605). SKIPs when no child terminal
    advertises `cancel` while running."""
    run = await _child_run(request, agent_launch, tmp_path, subagent_cancel_prompt_text)
    _judge_child_item(
        run.terminal,
        run.terminal_child,
        "terminal",
        "terminal/cancel",
        "CancelTerminalResponse",
        "a terminal_update that sets exitStatus",
    )
