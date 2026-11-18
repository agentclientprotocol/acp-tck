"""Cancelling a tool call or a terminal on its own: ACP-TOOLCANCEL-201/202/204-211 and
ACP-TERMCANCEL-201/202/204-211.

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
all twenty rows, made by the first test that asks and reused by the rest. The request is sent only
for an item that advertises `cancel` and is not final, since a client MUST NOT send it otherwise.
`-32602` is the documented answer for an item that is unknown, already final or not cancellable
(tool-calls.mdx:459,605), so one for an item the agent finalized or stopped advertising `cancel`
for around the request is a race and not judged; any other error, or `-32602` for an item that
stays live and advertising, is a rejection. `-201` judges the response, `-202` the confirming
update; a rejected request SKIPs `-202`, so one defect fails one row.

An agent that keeps advertising `cancel` after the item is final (a SHOULD, `ACP-PATCH-212`)
leaves the request legitimate to send, so the same run sends one more for the first such item.
`-204` judges that it is rejected with an error and not accepted; `-205` (ADVISORY) judges the
code, in separate rows because the sentence naming `-32602` carries no RFC keyword. Both SKIP
unless that situation occurs.

Once an item of a kind advertised `cancel` at any point in the turn, the run also sends one request
for an id no update announced: `-206` judges that it is rejected, `-207` (ADVISORY) the code. It
breaks the client rule at :456/:602, which the probe rules allow because :459/:605 define the
answer. An agent that never advertises `cancel` may not implement the method, and then its answer
is `-32601` (error.mdx:44), so the rows SKIP.

Under the same gate, the run sends one request for the first live item (not final, no `exitStatus`)
that does not currently advertise `cancel` and that the `-201` request did not go to: `-208` judges
that it is rejected, `-209` (ADVISORY) the code. Likewise the `-201` request never goes to an item
a further request went to, so no row judges the answer to a repeat request; a row left without a
target for that reason SKIPs and says so. The item may turn final as the request crosses; `-32602`
is still the answer. It may also start advertising `cancel` before the agent reads the request, so
a result that comes with such an advertisement is a race and SKIPs.

Once the `-201` request was accepted and the item is final (`-202`), the run sends the same request
again when the item no longer advertises `cancel`: `-210` judges that it is rejected, `-211`
(ADVISORY) the code. That request breaks the client rule at :456/:602 like the unknown-id probe, and
tool-calls.mdx:459,605 define its answer ("a request that the Client sends again after the first one
was accepted"). An item that still advertises `cancel` gets the already-final request instead
(`-204`), so no item is asked twice and `-210` SKIPs.

The module and its tests are named without "cancel": the CLI self-tests select the cancellation
suite with `-k cancel`, and a defect fixture that hangs on `session/cancel` must not be judged here.
"""

from __future__ import annotations

from typing import Any

import pytest

from tck.common.plugin import register_active_process
from tck.v2.protocol import INVALID_PARAMS
from tck.v2.validation import validate_def_value

from ._helpers import (
    FollowUpCancel,
    ItemCancel,
    ItemCancelRun,
    drive_item_cancel,
    new_session,
    v2_only_agent,
)

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
    if result.outcome == "claimed":
        pytest.skip(
            f"every {noun} that advertised capabilities.cancel while still live had already been "
            f"sent a further cancel request, which this row does not repeat"
        )
    if result.outcome == "raced":
        pytest.skip(
            f"every {noun} that advertised capabilities.cancel was already final, or had stopped "
            f"advertising it, when the agent read the request"
        )


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


def _judge_rejected(probe: FollowUpCancel, method: str, target: str, case: str, not_sent: str) -> None:
    """A further request (`-204`/`-206`/`-208`) must get an error. `target` names what it was for,
    `case` why the agent must reject it, `not_sent` why it was not made."""
    if probe.outcome == "none":
        pytest.skip(not_sent)
    assert probe.outcome != "unanswered", f"{method} for {target} got no response within the timeout"
    assert probe.outcome == "error", (
        f"{method} for {target} was answered with a result {probe.result!r}; the agent responds "
        f"with an error for {case}"
    )


def _judge_code(probe: FollowUpCancel, method: str, target: str) -> None:
    """The ADVISORY code row (`-205`/`-207`/`-209`) of a further request."""
    if probe.outcome != "error":
        pytest.skip(f"{method} for {target} was not rejected -- see its rejection row")
    code = probe.error.get("code") if isinstance(probe.error, dict) else None
    assert code == INVALID_PARAMS, (
        f"{method} for {target} {probe.item_id!r} was rejected with {probe.error!r}; the agent "
        f"responds with -32602 (Invalid params)"
    )


def _judge_repeat_rejected(repeat: FollowUpCancel, noun: str, method: str) -> None:
    if repeat.outcome == "stale":
        pytest.skip(
            f"the {noun} cancelled by the main request still advertises capabilities.cancel, so "
            f"the already-final request for it is the repeat -- see the already-final row"
        )
    _judge_rejected(
        repeat,
        method,
        f"{noun} {repeat.item_id!r}, whose first {method} was accepted and which is now final,",
        f"a repeat request after the first was accepted and the {noun} reached a final state",
        f"no {noun} was cancelled by an accepted {method} and then confirmed final during the "
        f"driven turn",
    )


def _judge_stale_rejected(stale: FollowUpCancel, noun: str, method: str, state: str) -> None:
    _judge_rejected(
        stale,
        method,
        f"{noun} {stale.item_id!r}, which {state} but still advertises capabilities.cancel,",
        "an item that is already final",
        f"no {noun} {state} while still advertising capabilities.cancel during the driven turn",
    )


def _judge_unknown_rejected(unknown: FollowUpCancel, noun: str, method: str) -> None:
    _judge_rejected(
        unknown,
        method,
        f"the unknown {noun} id {unknown.item_id!r}",
        f"an unknown {noun}",
        f"no {noun} advertised capabilities.cancel during the driven turn, so the agent may not "
        f"implement {method}",
    )


def _judge_uncancellable_rejected(probe: FollowUpCancel, noun: str, method: str, cancel_seen: bool) -> None:
    if probe.outcome == "raced":
        pytest.skip(
            f"{noun} {probe.item_id!r} started advertising capabilities.cancel as {method} for it "
            f"crossed, so the agent could accept it"
        )
    if probe.outcome == "tried":
        pytest.skip(
            f"every {noun} live without advertising capabilities.cancel had already been sent "
            f"the main {method} request, which this row does not repeat"
        )
    if cancel_seen:
        not_sent = (
            f"no {noun} was live without advertising capabilities.cancel while the request could be "
            f"sent during the driven turn"
        )
    else:
        not_sent = (
            f"no {noun} advertised capabilities.cancel during the driven turn, so the agent may not "
            f"implement {method}"
        )
    _judge_rejected(
        probe,
        method,
        f"{noun} {probe.item_id!r}, live without advertising capabilities.cancel,",
        f"a {noun} that is not cancellable",
        not_sent,
    )


@pytest.mark.requirement("ACP-TOOLCANCEL-204")
async def test_final_tool_call_request_is_rejected(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TOOLCANCEL-204 (CAPABILITY, `inferred:toolCallCancel`). `tool_call/cancel` for a tool
    call with a final status that still advertises `capabilities.cancel` gets an error, not a
    result (tool-calls.mdx:459, declarative; the code is `ACP-TOOLCANCEL-205`). SKIPs unless a tool
    call is final while still advertising `cancel` during the driven turn."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_stale_rejected(
        run.tool_call_stale, "tool call", "tool_call/cancel", "has a final status"
    )


@pytest.mark.requirement("ACP-TOOLCANCEL-205")
async def test_final_tool_call_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TOOLCANCEL-205 (ADVISORY). The rejection of `tool_call/cancel` for an already-final
    tool call (`ACP-TOOLCANCEL-204`'s request) uses `-32602` (tool-calls.mdx:459). SKIPs when that
    request was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.tool_call_stale, "tool_call/cancel", "an already-final tool call")


@pytest.mark.requirement("ACP-TERMCANCEL-204")
async def test_exited_terminal_request_is_rejected(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TERMCANCEL-204 (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` for a
    terminal that reported `exitStatus` and still advertises `capabilities.cancel` gets an error,
    not a result (tool-calls.mdx:605, declarative; the code is `ACP-TERMCANCEL-205`). SKIPs unless
    a terminal has exited while still advertising `cancel` during the driven turn."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_stale_rejected(run.terminal_stale, "terminal", "terminal/cancel", "has exited")


@pytest.mark.requirement("ACP-TERMCANCEL-205")
async def test_exited_terminal_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TERMCANCEL-205 (ADVISORY). The rejection of `terminal/cancel` for an exited terminal
    (`ACP-TERMCANCEL-204`'s request) uses `-32602` (tool-calls.mdx:605). SKIPs when that request
    was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.terminal_stale, "terminal/cancel", "an exited terminal")


@pytest.mark.requirement("ACP-TOOLCANCEL-206")
async def test_unknown_tool_call_request_is_rejected(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TOOLCANCEL-206 (CAPABILITY, `inferred:toolCallCancel`). `tool_call/cancel` for a
    `toolCallId` no update announced gets an error, not a result (tool-calls.mdx:459, declarative;
    the code is `ACP-TOOLCANCEL-207`). The probe breaks the client rule at :456 because :459
    defines the answer. SKIPs unless some tool call advertised `cancel` during the driven turn."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_unknown_rejected(run.tool_call_unknown, "tool call", "tool_call/cancel")


@pytest.mark.requirement("ACP-TOOLCANCEL-207")
async def test_unknown_tool_call_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TOOLCANCEL-207 (ADVISORY). The rejection of `tool_call/cancel` for an unknown tool call
    (`ACP-TOOLCANCEL-206`'s request) uses `-32602` (tool-calls.mdx:459). SKIPs when that request
    was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.tool_call_unknown, "tool_call/cancel", "an unknown tool call")


@pytest.mark.requirement("ACP-TERMCANCEL-206")
async def test_unknown_terminal_request_is_rejected(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TERMCANCEL-206 (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` for a
    `terminalId` no update announced gets an error, not a result (tool-calls.mdx:605, declarative;
    the code is `ACP-TERMCANCEL-207`). The probe breaks the client rule at :602 because :605
    defines the answer. SKIPs unless some terminal advertised `cancel` during the driven turn."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_unknown_rejected(run.terminal_unknown, "terminal", "terminal/cancel")


@pytest.mark.requirement("ACP-TERMCANCEL-207")
async def test_unknown_terminal_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TERMCANCEL-207 (ADVISORY). The rejection of `terminal/cancel` for an unknown terminal
    (`ACP-TERMCANCEL-206`'s request) uses `-32602` (tool-calls.mdx:605). SKIPs when that request
    was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.terminal_unknown, "terminal/cancel", "an unknown terminal")


@pytest.mark.requirement("ACP-TOOLCANCEL-208")
async def test_uncancellable_tool_call_request_is_rejected(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TOOLCANCEL-208 (CAPABILITY, `inferred:toolCallCancel`). `tool_call/cancel` for a tool
    call that is not final and does not advertise `capabilities.cancel` gets an error, not a
    result (tool-calls.mdx:440,459, declarative; the code is `ACP-TOOLCANCEL-209`). The probe
    breaks the client rule at :456 because :459 defines the answer. SKIPs unless some tool call
    advertised `cancel` during the driven turn and such a tool call was live, or when it started
    advertising `cancel` as the request crossed."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_uncancellable_rejected(
        run.tool_call_uncancellable, "tool call", "tool_call/cancel", run.tool_call_cancel_seen
    )


@pytest.mark.requirement("ACP-TOOLCANCEL-209")
async def test_uncancellable_tool_call_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TOOLCANCEL-209 (ADVISORY). The rejection of `tool_call/cancel` for a live tool call that
    does not advertise `cancel` (`ACP-TOOLCANCEL-208`'s request) uses `-32602`
    (tool-calls.mdx:459). SKIPs when that request was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.tool_call_uncancellable, "tool_call/cancel", "a tool call that is not cancellable")


@pytest.mark.requirement("ACP-TERMCANCEL-208")
async def test_uncancellable_terminal_request_is_rejected(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TERMCANCEL-208 (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` for a
    terminal that has no `exitStatus` and does not advertise `capabilities.cancel` gets an error,
    not a result (tool-calls.mdx:587,605, declarative; the code is `ACP-TERMCANCEL-209`). The probe
    breaks the client rule at :602 because :605 defines the answer. SKIPs unless some terminal
    advertised `cancel` during the driven turn and such a terminal was running, or when it started
    advertising `cancel` as the request crossed."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_uncancellable_rejected(
        run.terminal_uncancellable, "terminal", "terminal/cancel", run.terminal_cancel_seen
    )


@pytest.mark.requirement("ACP-TERMCANCEL-209")
async def test_uncancellable_terminal_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TERMCANCEL-209 (ADVISORY). The rejection of `terminal/cancel` for a running terminal
    that does not advertise `cancel` (`ACP-TERMCANCEL-208`'s request) uses `-32602`
    (tool-calls.mdx:605). SKIPs when that request was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.terminal_uncancellable, "terminal/cancel", "a terminal that is not cancellable")


@pytest.mark.requirement("ACP-TOOLCANCEL-210")
async def test_repeat_tool_call_request_is_rejected(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TOOLCANCEL-210 (CAPABILITY, `inferred:toolCallCancel`). `tool_call/cancel` sent again
    for a tool call whose first request was accepted and which has since reached a final status
    gets an error, not a result (tool-calls.mdx:459, declarative; the code is
    `ACP-TOOLCANCEL-211`). The probe breaks the client rule at :456 because :459 defines the answer
    to exactly this request. SKIPs unless the `-201` request was accepted and confirmed, or the
    tool call still advertises `cancel` (`-204`'s request is then the repeat)."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_repeat_rejected(run.tool_call_repeat, "tool call", "tool_call/cancel")


@pytest.mark.requirement("ACP-TOOLCANCEL-211")
async def test_repeat_tool_call_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TOOLCANCEL-211 (ADVISORY). The rejection of a repeated `tool_call/cancel`
    (`ACP-TOOLCANCEL-210`'s request) uses `-32602` (tool-calls.mdx:459). SKIPs when that request
    was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.tool_call_repeat, "tool_call/cancel", "a repeated request for a final tool call")


@pytest.mark.requirement("ACP-TERMCANCEL-210")
async def test_repeat_terminal_request_is_rejected(request, agent_launch, tmp_path, cancel_prompt_text):
    """ACP-TERMCANCEL-210 (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` sent again
    for a terminal whose first request was accepted and which has since reported `exitStatus` gets
    an error, not a result (tool-calls.mdx:605, declarative; the code is `ACP-TERMCANCEL-211`). The
    probe breaks the client rule at :602 because :605 defines the answer to exactly this request.
    SKIPs unless the `-201` request was accepted and confirmed, or the terminal still advertises
    `cancel` (`-204`'s request is then the repeat)."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_repeat_rejected(run.terminal_repeat, "terminal", "terminal/cancel")


@pytest.mark.requirement("ACP-TERMCANCEL-211")
async def test_repeat_terminal_request_gets_invalid_params(
    request, agent_launch, tmp_path, cancel_prompt_text
):
    """ACP-TERMCANCEL-211 (ADVISORY). The rejection of a repeated `terminal/cancel`
    (`ACP-TERMCANCEL-210`'s request) uses `-32602` (tool-calls.mdx:605). SKIPs when that request
    was not made or not rejected."""
    run = await _item_cancel_run(request, agent_launch, tmp_path, cancel_prompt_text)
    _judge_code(run.terminal_repeat, "terminal/cancel", "a repeated request for an exited terminal")
