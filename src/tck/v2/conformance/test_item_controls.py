"""Cancelling a tool call or a terminal on its own: ACP-TOOLCANCEL-201/202, ACP-TERMCANCEL-201/202.

A tool call (or terminal) that advertises `capabilities.cancel` may be cancelled with
`tool_call/cancel` (`terminal/cancel`) without cancelling the session's other work. The agent
answers `{}` once it accepted, then confirms with a final `tool_call_update` (a `terminal_update`
that sets `exitStatus`) (tool-calls.mdx:440,456-459,600-605).

There is no `initialize` marker for either method; an agent opts in by advertising `cancel` on an
item, so `Requirement.capability` is the documentation-only `inferred:toolCallCancel` /
`inferred:terminalCancel` string, the tests carry no `@pytest.mark.capability(...)` marker and
SKIP themselves when no item advertises `cancel` while live (same encoding as `test_subagents.py`,
hence `v2_only_agent`).

One driven turn (`drive_item_cancel`: the cancel prompt, so a real agent is still working) serves
all four rows, made by the first test that asks and reused by the rest. The request is sent only
for an item that advertises `cancel` and is not final, since a client MUST NOT send it otherwise;
the error paths (`-32602` for an unknown, final or non-cancellable item, tool-calls.mdx:459,605)
need that rule broken, so they are not tested. `-32602` after the item's own final update is the
agent saying `already final` (a race) and is not judged. `-201` judges the response, `-202` the
confirming update; a rejected request SKIPs `-202`, so one defect fails one row.

The module and its tests are named without "cancel": the CLI self-tests select the cancellation
suite with `-k cancel`, and a defect fixture that hangs on `session/cancel` must not be judged here.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.plugin import register_active_process
from tck.v2.validation import validate_def_value

from ._helpers import ItemCancel, ItemCancelRun, drive_item_cancel, new_session, v2_only_agent

_RUN_KEY = pytest.StashKey[dict[str, Any]]()
"""The run's one driven turn, in `config.stash`: `agent` and `run` once it completed, or `error`
(the exception it ended with) so every row sees the same outcome."""


async def _item_cancel_run(
    request: pytest.FixtureRequest, agent_launch, tmp_path, cancel_prompt_text: str
) -> ItemCancelRun:
    cache = request.config.stash.setdefault(_RUN_KEY, {})
    if "error" in cache:
        raise cache["error"]
    if "run" in cache:
        register_active_process(cache["agent"])
        return cache["run"]
    try:
        async with v2_only_agent(agent_launch, require_session=True) as agent:
            session_id = await new_session(agent, tmp_path, timeout=agent_launch.default_timeout)
            run = await drive_item_cancel(
                agent, session_id, cancel_prompt_text, timeout=agent_launch.default_timeout
            )
            cache.update(agent=agent, run=run)
    except BaseException as exc:
        cache["error"] = exc
        raise
    return run


def _skip_unless_exercised(result: ItemCancel, noun: str) -> None:
    if result.outcome == "none":
        pytest.skip(f"no {noun} advertised capabilities.cancel while still live during the driven turn")
    if result.outcome == "raced":
        pytest.skip(f"every {noun} that advertised capabilities.cancel was already final when the agent read the request")


def _judge_accepted(result: ItemCancel, noun: str, method: str, response_def: str) -> None:
    _skip_unless_exercised(result, noun)
    assert result.outcome != "rejected", (
        f"{method} for {noun} {result.item_id!r}, which advertises capabilities.cancel and had no "
        f"final update, was answered with an error: {result.error!r}"
    )
    assert result.outcome != "unanswered", (
        f"{method} for {noun} {result.item_id!r} got no response within the timeout"
    )
    issues = validate_def_value(response_def, result.result)
    assert not issues, f"{method} result {result.result!r} is not a valid {response_def}: {issues!r}"


def _judge_confirmed(result: ItemCancel, noun: str, method: str, confirmation: str) -> None:
    _skip_unless_exercised(result, noun)
    if result.outcome in ("rejected", "unanswered"):
        pytest.skip(f"{method} was not accepted -- see its acceptance row")
    assert result.outcome == "confirmed", (
        f"{method} for {noun} {result.item_id!r} was accepted, but {confirmation} did not follow "
        f"within the timeout"
    )


@pytest.mark.requirement("ACP-TOOLCANCEL-201")
async def test_tool_call_request_is_accepted(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TOOLCANCEL-201 (CAPABILITY, `inferred:toolCallCancel`). `tool_call/cancel` for a tool
    call that advertises `capabilities.cancel` and is not final gets an empty result, not an
    error (tool-calls.mdx:440,456,458). SKIPs when no tool call advertises `cancel` while live."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_accepted(run.tool_call, "tool call", "tool_call/cancel", "CancelToolCallResponse")


@pytest.mark.requirement("ACP-TOOLCANCEL-202")
async def test_stopped_tool_call_reaches_a_final_status(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TOOLCANCEL-202 (CAPABILITY, `inferred:toolCallCancel`). After accepting
    `tool_call/cancel`, the agent gives the tool call a final status with a `tool_call_update`
    (tool-calls.mdx:458). SKIPs when no cancel was accepted."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_confirmed(
        run.tool_call, "tool call", "tool_call/cancel", "a tool_call_update to a final status"
    )


@pytest.mark.requirement("ACP-TERMCANCEL-201")
async def test_terminal_request_is_accepted(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TERMCANCEL-201 (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` for a
    terminal that advertises `capabilities.cancel` and has no `exitStatus` gets an empty result,
    not an error (tool-calls.mdx:600-604). SKIPs when no terminal advertises `cancel` while
    running."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_accepted(run.terminal, "terminal", "terminal/cancel", "CancelTerminalResponse")


@pytest.mark.requirement("ACP-TERMCANCEL-202")
async def test_stopped_terminal_reports_exit_status(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TERMCANCEL-202 (CAPABILITY, `inferred:terminalCancel`). After accepting
    `terminal/cancel`, the agent sets the terminal's `exitStatus` with a `terminal_update`
    (tool-calls.mdx:604). SKIPs when no cancel was accepted."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_confirmed(
        run.terminal, "terminal", "terminal/cancel", "a terminal_update that sets exitStatus"
    )
