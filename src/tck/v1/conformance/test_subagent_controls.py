"""Stopping a subagent: ACP-SUBAGENT-016/017.

A child that advertises `capabilities.cancel` (`SubagentSessionCapabilities`) may be cancelled with
`session/cancel` carrying the child's `sessionId`; that cancels the child's current work, not its
parent or its siblings, and the child confirms with `idle` and `stopReason: "cancelled"` through
its state snapshot, which in v1 is the parent association's `subagent_update.state`
(RFD:1069-1073,1089-1093).

No `initialize` marker announces the per-child capability, so each `Requirement.capability` is the
documentation-only `inferred:subagentCancel` string, the tests carry no
`@pytest.mark.capability(...)` marker and SKIP themselves when nothing was exercised. Subagent
traffic reaches only a client that advertised `clientCapabilities.subagents`, so the driven turn
runs on its own connection that does (`subagents: {}` and nothing else, as
`_subagents_connection.py` does). One driven turn (`drive_child_cancel`: the cancel prompt, so a
real agent still has a running child) serves both rows, made by the first test that asks and
reused by the rest. The request goes only to a child that advertises `cancel` and was last
reported running, since a client MUST NOT cancel one that does not; a cancel that races with work
that has already ended does not rewrite its outcome, so it is not judged (see `_child_cancel.py`).
016 judges the confirmation, 017 that the parent and the siblings were left alone, so one defect
fails one row. The v2-only rows (`ACP-SUBAGENT-202`, the child tool call and terminal cancels)
have no v1 counterpart: v1 has no `background` list to tell which children the parent waits on, and
the tool call and terminal cancel methods are v2's.

The module and its tests are named without "cancel": the CLI self-tests select the cancellation
suite with `-k cancel`, and a defect fixture that hangs on `session/cancel` must not be judged here.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.plugin import register_active_process

from ._child_cancel import ChildCancelRun, drive_child_cancel
from ._helpers import connected_agent, new_session, skip_if_version_mismatch

_RUN_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one driven turn, in `config.stash`: `agent` and `run` once it completed, or `error`
(the exception it ended with) so every row sees the same outcome."""


async def _child_run(
    request: pytest.FixtureRequest, agent_launch, agent_initialize_result, tmp_path, cancel_prompt_text: str
) -> ChildCancelRun:
    """An agent that did not negotiate v1 SKIPs (`VERSION-MISMATCH:`): its subagent shapes are not
    v1's. The first test that asks makes the run, a SKIP or error that ended it is re-raised for
    each row, and each test registers the agent process so a FAIL attaches its transcript."""
    init_result = agent_initialize_result.result
    if init_result is not None:
        skip_if_version_mismatch(init_result)
    cache = request.config.stash.setdefault(_RUN_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "run" not in cache:
        try:
            async with connected_agent(agent_launch, client_capabilities={"subagents": {}}) as agent:
                session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
                run = await drive_child_cancel(
                    agent, session_id, cancel_prompt_text, timeout=agent_launch.default_timeout
                )
                cache.update(agent=agent, run=run)
        except BaseException as exc:
            cache["error"] = exc
            raise
    register_active_process(cache["agent"])
    return cache["run"]


def _skip_unless_child_cancelled(run: ChildCancelRun) -> None:
    if run.target is None:
        pytest.skip("no child advertised capabilities.cancel while reported running during the driven turn")
    if run.outcome == "raced":
        pytest.skip(
            f"child {run.target!r} ended on its own before the agent read session/cancel: "
            "a cancel racing with ended work is not judged"
        )


@pytest.mark.requirement("ACP-SUBAGENT-016")
async def test_child_stop_is_confirmed_by_the_child(
    request, agent_launch, agent_initialize_result, tmp_path, cancel_prompt_text
):
    """ACP-SUBAGENT-016 (CAPABILITY, `inferred:subagentCancel`). After `session/cancel` for a
    running child that advertises `capabilities.cancel`, the parent's snapshot of the child
    (`subagent_update.state`) becomes `idle` with `stopReason: "cancelled"`. SKIPs when no such
    child was running or it ended first."""
    run = await _child_run(request, agent_launch, agent_initialize_result, tmp_path, cancel_prompt_text)
    _skip_unless_child_cancelled(run)
    assert run.outcome == "confirmed", (
        f"session/cancel for child {run.target!r}, which advertised capabilities.cancel and was "
        "running, was not followed by a subagent_update whose state is idle with stopReason "
        "'cancelled' within the timeout"
    )


@pytest.mark.requirement("ACP-SUBAGENT-017")
async def test_child_stop_leaves_parent_and_siblings(
    request, agent_launch, agent_initialize_result, tmp_path, cancel_prompt_text
):
    """ACP-SUBAGENT-017 (CAPABILITY, `inferred:subagentCancel`). `session/cancel` for a child
    cancels that child's work, not its parent or its siblings: the parent's prompt is not answered
    `cancelled` and no other child (outside the cancelled child's own subtree) is reported
    `idle`/`cancelled` because of it. SKIPs when no such child was running or it ended first."""
    run = await _child_run(request, agent_launch, agent_initialize_result, tmp_path, cancel_prompt_text)
    _skip_unless_child_cancelled(run)
    problems = []
    if run.parent_cancelled:
        problems.append("the parent's prompt was answered with stopReason 'cancelled'")
    if run.cancelled_siblings:
        problems.append(f"sibling(s) {run.cancelled_siblings!r} were reported idle/cancelled")
    assert not problems, (
        f"after session/cancel for child {run.target!r}: {'; '.join(problems)}"
    )
