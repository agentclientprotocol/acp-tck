"""One driven turn that cancels a running child and then the parent: the evidence for
`ACP-SUBAGENT-016` and `-017`.

`drive_child_cancel` runs on the connection that advertised `clientCapabilities.subagents`, sends
the cancel prompt and follows the wire in order, tracking each announced child: its
`capabilities.cancel` and its latest state. v1 has no child-addressed `state_update`, so a
child's state is only the parent association's `subagent_update.state` (omitted keeps it, `null`
clears it). Then, in this order:

1. `session/cancel` with the child's `sessionId`, only for a child that advertises
   `capabilities.cancel` and was last reported running (a client MUST NOT cancel one that does
   not; RFD:1069-1073). The child's next idle snapshot settles it: `idle` with `stopReason:
   "cancelled"` is `confirmed`; any other idle means the child ended on its own first (`raced`: a
   cancel racing with ended work does not rewrite its outcome, RFD:1093-1095, so nothing is
   judged); silence for `timeout / 2` is `unconfirmed`. After a short quiet period the parent's
   prompt response and the other children's snapshots are checked for a cancellation the child's
   cancel must not have caused.
2. `session/cancel` for the parent, so no work is left behind.

Every wait is bounded per step (`timeout` to find something to cancel, `timeout / 2` for the
confirmation and for the parent's response), never by one overall deadline that a long turn could
exhaust, so a slow or chatty agent is judged on what it did, not on the TCK running out of time.
A parent turn that never ends within the budget is not judged here (`ACP-CANCEL-*` own that).
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from typing import Any

from tck.common.harness import AgentProcess, AgentTimeout, Direction, TranscriptEntry

from ._helpers import PromptTurn, quiet_period, run_prompt

_ACTIVE_STATES = frozenset({"running", "requires_action"})


@dataclass
class _Child:
    parent: str
    cancel: bool = False
    state: dict[str, Any] | None = None
    """The latest `subagent_update.state` snapshot, `None` when never reported or cleared."""


@dataclass
class ChildCancelRun:
    """The outcome of `drive_child_cancel`."""

    turn: PromptTurn | None = None
    """The parent's turn, or `None` when it did not end within the budget."""
    target: str | None = None
    """The child `session/cancel` was sent for, if any."""
    outcome: str = "none"
    """`none`: no child advertised `cancel` while reported running. `raced`: the child reported
    an idle snapshot that is not a cancellation, so it had ended first. `unconfirmed`: no idle
    snapshot within `timeout / 2`. `confirmed`: `idle` with `stopReason: "cancelled"`."""
    parent_cancelled: bool = False
    """The parent's prompt was answered `stopReason: "cancelled"` after the child cancel and
    before the TCK's own parent `session/cancel`."""
    cancelled_siblings: list[str] = field(default_factory=list)
    """Children that are neither the target nor its descendants and reported `idle`/`cancelled`
    in that same window."""


def _is_idle_cancelled(state: Any) -> bool:
    return isinstance(state, dict) and state.get("state") == "idle" and state.get("stopReason") == "cancelled"


def _stop_reason(turn: PromptTurn) -> Any:
    message = turn.response_entry.parsed
    result = message.get("result") if isinstance(message, dict) else None
    return result.get("stopReason") if isinstance(result, dict) else None


class _Driver:
    def __init__(self, agent: AgentProcess, session_id: str, timeout: float) -> None:
        self.agent, self.session_id, self.timeout = agent, session_id, timeout
        self.window = timeout / 2
        self.quiet = quiet_period(timeout)
        self.silence = max(self.quiet, timeout / 4)
        self.children: dict[str, _Child] = {}
        self.result = ChildCancelRun()
        self.target_sent_index: int | None = None
        self.target_sent_at = 0.0
        self.target_settled_at: float | None = None
        self.parent_cancel_at: float | None = None

    def ingest(self, index: int, entry: TranscriptEntry) -> None:
        if entry.direction is not Direction.RECEIVED:
            return
        for message in _messages(entry):
            params = message.get("params")
            if message.get("method") != "session/update" or not isinstance(params, dict):
                continue
            sid, update = params.get("sessionId"), params.get("update")
            if not isinstance(sid, str) or not isinstance(update, dict):
                continue
            if update.get("sessionUpdate") != "subagent_update":
                continue
            if sid != self.session_id and sid not in self.children:
                continue
            child_id = update.get("sessionId")
            if not isinstance(child_id, str) or child_id == self.session_id:
                continue
            child = self.children.setdefault(child_id, _Child(parent=sid))
            if "capabilities" in update:
                capabilities = update["capabilities"]
                child.cancel = isinstance(capabilities, dict) and isinstance(capabilities.get("cancel"), dict)
            if "state" in update:
                self._report(index, child_id, update["state"])

    def _report(self, index: int, child_id: str, state: Any) -> None:
        child = self.children[child_id]
        child.state = state if isinstance(state, dict) else None
        if self.target_sent_index is None or index <= self.target_sent_index or child.state is None:
            return
        if child_id == self.result.target:
            if self.result.outcome == "none" and child.state.get("state") == "idle":
                self.result.outcome = "confirmed" if _is_idle_cancelled(child.state) else "raced"
                self.target_settled_at = asyncio.get_running_loop().time()
        elif (
            self.parent_cancel_at is None
            and _is_idle_cancelled(child.state)
            and not self._descends_from(child_id, self.result.target)
            and child_id not in self.result.cancelled_siblings
        ):
            self.result.cancelled_siblings.append(child_id)

    def _descends_from(self, child_id: str, ancestor: str | None) -> bool:
        seen: set[str] = set()
        while child_id in self.children and child_id not in seen:
            seen.add(child_id)
            child_id = self.children[child_id].parent
            if child_id == ancestor:
                return True
        return False

    def _candidate(self) -> str | None:
        """The first child that advertises `cancel` and was last reported active."""
        for child_id, child in self.children.items():
            if child.cancel and child.state is not None and child.state.get("state") in _ACTIVE_STATES:
                return child_id
        return None

    async def step(
        self, now: float, turn: PromptTurn | None, turn_done: bool, last_activity: float, started: float
    ) -> bool:
        """One pass of decisions over what was read; `True` when the run is complete."""
        if self.target_sent_index is None and not turn_done:
            target = self._candidate()
            if target is not None:
                await self.agent.send_notification("session/cancel", {"sessionId": target})
                self.target_sent_index = len(self.agent.transcript) - 1
                self.target_sent_at = now
                self.result.target = target
        search_over = (
            self.target_sent_index is not None
            or turn_done
            or now - started > self.timeout
            or now - last_activity > self.silence
        )
        if self.result.target is not None and self.result.outcome == "none":
            if now - self.target_sent_at > self.window:
                self.result.outcome = "unconfirmed"
                self.target_settled_at = now
        target_settled = search_over and (
            self.result.target is None
            or (
                self.target_settled_at is not None
                and (turn_done or now - self.target_settled_at >= self.quiet)
            )
        )
        if self.parent_cancel_at is None:
            if turn_done and turn is not None and self.target_sent_index is not None:
                self.result.parent_cancelled = _stop_reason(turn) == "cancelled"
            if turn_done and target_settled:
                return True
            if target_settled:
                await self.agent.send_notification("session/cancel", {"sessionId": self.session_id})
                self.parent_cancel_at = now
            return False
        return turn_done or now - self.parent_cancel_at > self.window


def _messages(entry: TranscriptEntry) -> list[dict[str, Any]]:
    parsed = entry.parsed
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    return []


async def drive_child_cancel(
    agent: AgentProcess, session_id: str, prompt_text: str, *, timeout: float
) -> ChildCancelRun:
    """Drive one turn of `prompt_text`, cancelling a running child and then the parent, as the
    module docstring describes. Raises only what the agent causes (`AgentExited`); a turn that
    does not end within the budget is `turn=None`."""
    loop = asyncio.get_running_loop()
    driver = _Driver(agent, session_id, timeout)
    cursor = len(agent.transcript)
    started = last_activity = loop.time()
    # Several times the per-response timeout: the waits above are bounded one by one and add up
    # to less, so the turn's own deadline never fires first in a normal run.
    turn_task = asyncio.ensure_future(
        run_prompt(agent, session_id, [{"type": "text", "text": prompt_text}], timeout=timeout * 3)
    )
    try:
        while True:
            turn_done = turn_task.done()
            turn: PromptTurn | None = None
            if turn_done and not turn_task.cancelled():
                error = turn_task.exception()
                if error is None:
                    turn = turn_task.result()
                elif not isinstance(error, AgentTimeout):
                    raise error
            while cursor < len(agent.transcript):
                driver.ingest(cursor, agent.transcript[cursor])
                cursor += 1
                last_activity = loop.time()
            if await driver.step(loop.time(), turn, turn_done, last_activity, started):
                break
            if turn_done:
                with contextlib.suppress(AgentTimeout):
                    await agent.read_line(timeout=0.05)
            else:
                await asyncio.sleep(0.01)
    finally:
        if not turn_task.done():
            turn_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await turn_task
    result = driver.result
    if turn_task.done() and not turn_task.cancelled() and turn_task.exception() is None:
        result.turn = turn_task.result()
    return result
