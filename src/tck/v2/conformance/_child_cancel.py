"""One driven turn that cancels a running child and then the parent: the evidence for
`ACP-SUBAGENT-016`, `-017` and `-202`, and for the child-item rows `ACP-TOOLCANCEL-203` and
`ACP-TERMCANCEL-203`.

`drive_child_cancel` sends the cancel prompt and follows the wire in order, tracking each announced
child (its `capabilities.cancel`, its latest state from its own `state_update` or the parent's
`subagent_update.state` mirror, and its tool calls and terminals). Then, in this order:

1. `tool_call/cancel` / `terminal/cancel` with the child's `sessionId` for the first child item
   that advertises `cancel` and is live (`_ItemProbe`, as `drive_item_cancel` does for the prompted
   session's items). The child need not advertise `cancel` itself (tool-calls.mdx:457,603).
2. `session/cancel` with the child's `sessionId`, only for a child that advertises
   `capabilities.cancel` and was last reported running (a client MUST NOT cancel one that does not;
   RFD:1069-1073). The child's own idle report after it settles it: `idle` with `stopReason:
   "cancelled"` is `confirmed`. Any other idle within `quiet_period(timeout)` of the cancel, with
   a stop reason the child could have reached on its own, means it ended first (`raced`: a cancel
   racing with ended work does not rewrite its outcome, RFD:1093-1095, so nothing is judged; the
   same race window as `ACP-CANCEL-*`). A later or implausible one is `not_cancelled`: the child
   finished by other means after the cancel. Silence for `timeout / 2` is `unconfirmed`. After a
   short quiet period the parent is checked for a cancelled `idle` the child's cancel must not
   have caused, and the other children's are recorded (not judged: the Agent may cancel its own
   delegated work, RFD:1071-1073).
3. `session/cancel` for the parent, so no work is left behind and the cascade can be judged: every
   descendant that was running and that the cancelled work waits on must reach `idle`. A
   descendant counts as waited on only when its parent's latest `state_update` reported a
   `background` list that does not name it *and* arrived after the descendant was announced: an
   agent announces a background item before listing it (prompt-lifecycle.mdx:206) and re-sends
   the state when the list changes only as a SHOULD (:205), so a descendant announced after the
   latest list may be background work no list names yet, and a list never reported leaves the
   TCK unable to tell (:204). Nothing is judged for those.

Every wait is bounded per step (`timeout` to find something to cancel, `timeout / 2` for each
response or state), never by one overall deadline that a long turn could exhaust, so a slow or
chatty agent is judged on what it did, not on the TCK running out of time. The parent turn's own
end is not judged here: a turn that never ends within the budget only leaves the cascade
unjudged (`ACP-CANCEL-*` own that).
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from typing import Any

from tck.common.harness import AgentProcess, AgentTimeout, Direction, TranscriptEntry

from ._helpers import (
    ItemCancel,
    PatchTracker,
    PromptTurn,
    _ItemProbe,
    answer_post_turn_requests,
    background_keys,
    is_active_state,
    iter_messages,
    quiet_period,
    race_plausible,
    run_prompt,
)


@dataclass
class _Child:
    parent: str
    announced_at: int
    """Transcript index of the child's first `subagent_update`."""
    cancel: bool = False
    state: dict[str, Any] | None = None
    """The latest snapshot reported for the child, by its own `state_update` or its mirror."""
    background: set[tuple[str, str]] | None = None
    """`background_keys` of the child's own latest `state_update`; `None` when not reported."""
    background_at: int = -1
    """Transcript index of that `state_update`."""
    tracker: PatchTracker = field(default_factory=PatchTracker)


@dataclass
class ChildCancelRun:
    """The outcome of `drive_child_cancel`."""

    turn: PromptTurn | None = None
    """The parent's turn, or `None` when it did not end within the budget."""
    target: str | None = None
    """The child `session/cancel` was sent for, if any."""
    outcome: str = "none"
    """`none`: no child advertised `cancel` while reported running. `raced`: the child reported
    an idle that is not a cancellation within the race window (`quiet_period`), with a stop reason
    it could have reached on its own, so it had ended first. `not_cancelled`: any other
    non-cancelled idle. `unconfirmed`: no idle within `timeout / 2`. `confirmed`: `idle` with
    `stopReason: "cancelled"`."""
    parent_cancelled: bool = False
    """The parent reported `idle`/`cancelled` after the child cancel and before the TCK's own
    parent `session/cancel`."""
    cancelled_siblings: list[str] = field(default_factory=list)
    """Children that are neither the target nor its descendants and reported `idle`/`cancelled`
    in that same window. Recorded, not judged (module docstring)."""
    cascade_judged: list[str] = field(default_factory=list)
    """Descendants that were running and waited on when the TCK cancelled the parent."""
    cascade_unstopped: list[str] = field(default_factory=list)
    """The `cascade_judged` ones that had not reached `idle` in time."""
    cascade_skip: str | None = None
    """Why the cascade was not judged, when it was not."""
    tool_call: ItemCancel = field(default_factory=ItemCancel)
    tool_call_child: str | None = None
    terminal: ItemCancel = field(default_factory=ItemCancel)
    terminal_child: str | None = None


def _is_idle_cancelled(state: Any) -> bool:
    return isinstance(state, dict) and state.get("state") == "idle" and state.get("stopReason") == "cancelled"


class _Driver:
    def __init__(self, agent: AgentProcess, session_id: str, timeout: float) -> None:
        self.agent, self.session_id, self.timeout = agent, session_id, timeout
        self.window = timeout / 2
        self.quiet = quiet_period(timeout)
        self.silence = max(self.quiet, timeout / 4)
        self.children: dict[str, _Child] = {}
        self.parent_state: dict[str, Any] | None = None
        self.parent_state_at = -1
        self.result = ChildCancelRun()
        self.probes = {
            "tool_call": _ItemProbe("tool_call", "tool_call/cancel", "toolCallId", grace=self.quiet),
            "terminal": _ItemProbe("terminal", "terminal/cancel", "terminalId", grace=self.quiet),
        }
        self.probe_child: dict[str, str | None] = {"tool_call": None, "terminal": None}
        self.target_sent_index: int | None = None
        self.target_sent_at = 0.0
        self.target_settled_at: float | None = None
        self.parent_cancel_index: int | None = None
        self.parent_cancel_at = 0.0
        self.parent_ended_at: float | None = None
        self.cascade_targets: list[str] = []
        self.finishing = False
        self.turn_timed_out = False

    # --- reading the wire

    def ingest(self, index: int, entry: TranscriptEntry) -> None:
        if entry.direction is not Direction.RECEIVED:
            return
        for message in iter_messages(entry):
            params = message.get("params")
            if not isinstance(params, dict):
                continue
            sid = params.get("sessionId")
            if not isinstance(sid, str):
                continue
            if message.get("method") == "session/request_permission":
                if sid in self.children:
                    self.children[sid].tracker.apply("permission", params)
                continue
            update = params.get("update")
            if message.get("method") != "session/update" or not isinstance(update, dict):
                continue
            if sid != self.session_id and sid not in self.children:
                continue
            kind = update.get("sessionUpdate")
            if kind == "subagent_update":
                self._apply_subagent_update(index, sid, update)
            elif kind == "state_update":
                self._apply_state(index, sid, update)
            elif sid in self.children:
                self.children[sid].tracker.apply("update", update)
        for kind, probe in self.probes.items():
            child_id = self.probe_child[kind]
            if child_id is not None:
                probe.observe(index, entry, self.children[child_id].tracker)

    def _apply_subagent_update(self, index: int, parent: str, update: dict[str, Any]) -> None:
        child_id = update.get("sessionId")
        if not isinstance(child_id, str) or child_id == self.session_id:
            return
        child = self.children.setdefault(child_id, _Child(parent=parent, announced_at=index))
        if "capabilities" in update:
            capabilities = update["capabilities"]
            child.cancel = isinstance(capabilities, dict) and isinstance(capabilities.get("cancel"), dict)
        if "state" in update:
            self._report(index, child_id, update["state"])

    def _apply_state(self, index: int, sid: str, update: dict[str, Any]) -> None:
        if sid == self.session_id:
            self.parent_state, self.parent_state_at = update, index
            if (
                self.target_sent_index is not None
                and index > self.target_sent_index
                and self.parent_cancel_index is None
                and _is_idle_cancelled(update)
            ):
                self.result.parent_cancelled = True
            return
        self.children[sid].background = background_keys(update)
        self.children[sid].background_at = index
        self._report(index, sid, update)

    def _report(self, index: int, child_id: str, state: Any) -> None:
        child = self.children[child_id]
        child.state = state if isinstance(state, dict) else None
        if self.target_sent_index is None or index <= self.target_sent_index or child.state is None:
            return
        if child_id == self.result.target:
            if self.result.outcome == "none" and child.state.get("state") == "idle":
                self.result.outcome = self._settle(index, child.state)
                self.target_settled_at = asyncio.get_running_loop().time()
        elif (
            self.parent_cancel_index is None
            and _is_idle_cancelled(child.state)
            and not self._descends_from(child_id, self.result.target)
            and child_id not in self.result.cancelled_siblings
        ):
            self.result.cancelled_siblings.append(child_id)

    def _settle(self, index: int, state: dict[str, Any]) -> str:
        if _is_idle_cancelled(state):
            return "confirmed"
        assert self.target_sent_index is not None
        transcript = self.agent.transcript
        elapsed = transcript[index].timestamp - transcript[self.target_sent_index].timestamp
        raced = elapsed < self.quiet and race_plausible(state.get("stopReason"))
        return "raced" if raced else "not_cancelled"

    def _descends_from(self, child_id: str, ancestor: str | None) -> bool:
        seen: set[str] = set()
        while child_id in self.children and child_id not in seen:
            seen.add(child_id)
            child_id = self.children[child_id].parent
            if child_id == ancestor:
                return True
        return False

    # --- deciding what to send

    def _background_of(self, session_id: str) -> tuple[set[tuple[str, str]], int] | None:
        """The `background` list of the session's latest `state_update` and that update's
        transcript index; `None` when the session has no state yet or it reported no list."""
        if session_id == self.session_id:
            if self.parent_state is None:
                return None
            keys = background_keys(self.parent_state)
            return (keys, self.parent_state_at) if keys is not None else None
        child = self.children.get(session_id)
        if child is None or child.background is None:
            return None
        return child.background, child.background_at

    def _waited_on(self, child_id: str, seen: frozenset[str] = frozenset()) -> bool:
        """Whether the cancelled parent is waiting on `child_id`: its parent reported a
        `background` list after announcing it that does not name it, and the same holds for every
        ancestor up to the prompted session. Anything else leaves it unclassified (module
        docstring)."""
        if child_id in seen or child_id not in self.children:
            return False
        child = self.children[child_id]
        listing = self._background_of(child.parent)
        if listing is None or ("subagent", child_id) in listing[0] or listing[1] <= child.announced_at:
            return False
        return child.parent == self.session_id or self._waited_on(child.parent, seen | {child_id})

    def _candidate(self) -> str | None:
        """The first child that advertises `cancel` and was last reported active, and is not the
        child whose item cancel is in flight."""
        in_flight = {
            self.probe_child[kind]
            for kind, probe in self.probes.items()
            if probe.request_id is not None and not probe.done
        }
        for child_id, child in self.children.items():
            if (
                child.cancel
                and child.state is not None
                and is_active_state(child.state.get("state"))
                and child_id not in in_flight
            ):
                return child_id
        return None

    def _items_settled(self, search_over: bool) -> bool:
        for kind, probe in self.probes.items():
            child_id = self.probe_child[kind]
            tracker = self.children[child_id].tracker if child_id is not None else PatchTracker()
            if not (probe.done or (probe.idle(tracker) and search_over)):
                return False
        return True

    async def step(self, now: float, turn_done: bool, last_activity: float, started: float) -> bool:
        """One pass of decisions over what was read; `True` when the run is complete: nothing
        is left to send and no item request is still awaiting its verdict (each is bounded by
        `timeout / 2`, so a request in flight when the cascade ends is judged, not abandoned)."""
        if not self.finishing:
            self.finishing = await self._decide(now, turn_done, last_activity, started)
            return False
        for kind, probe in self.probes.items():
            child_id = self.probe_child[kind]
            if probe.in_flight() and child_id is not None:
                await probe.step(
                    self.agent, child_id, self.children[child_id].tracker, now, self.window
                )
        return not any(probe.in_flight() for probe in self.probes.values())

    async def _decide(self, now: float, turn_done: bool, last_activity: float, started: float) -> bool:
        for kind, probe in self.probes.items():
            if self.probe_child[kind] is None:
                for child_id, child in self.children.items():
                    if probe._live(child.tracker):
                        self.probe_child[kind] = child_id
                        break
            child_id = self.probe_child[kind]
            if child_id is not None:
                await probe.step(
                    self.agent, child_id, self.children[child_id].tracker, now, self.window
                )
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
        items_settled = self._items_settled(search_over)
        if self.parent_cancel_index is None:
            if turn_done and target_settled and items_settled:
                self.result.cascade_skip = (
                    "the parent's turn did not end within the budget, so the TCK never cancelled it"
                    if self.turn_timed_out
                    else "the parent's turn ended before the TCK sent session/cancel for it"
                )
                return True
            if not turn_done and target_settled and items_settled:
                await self.agent.send_notification("session/cancel", {"sessionId": self.session_id})
                self.parent_cancel_index = len(self.agent.transcript) - 1
                self.parent_cancel_at = now
                self.cascade_targets = [
                    child_id
                    for child_id, child in self.children.items()
                    if child.state is not None
                    and is_active_state(child.state.get("state"))
                    and self._waited_on(child_id)
                ]
            return False
        if turn_done and self.parent_ended_at is None:
            self.parent_ended_at = now
        if self.parent_ended_at is None:
            if now - self.parent_cancel_at > self.window:
                self.result.cascade_skip = "the parent's turn did not end after session/cancel"
                return True
            return False
        pending = [c for c in self.cascade_targets if not self._idle(c)]
        return not pending or now - self.parent_ended_at > self.window

    def _idle(self, child_id: str) -> bool:
        state = self.children[child_id].state
        return state is not None and state.get("state") == "idle"


async def drive_child_cancel(
    agent: AgentProcess, session_id: str, prompt_text: str, *, timeout: float
) -> ChildCancelRun:
    """Drive one turn of `prompt_text`, cancelling a child item, then a running child, then the
    parent, as the module docstring describes. Raises only what the agent causes (`AgentExited`);
    a turn that does not end within the budget is `turn=None` and leaves the cascade unjudged."""
    loop = asyncio.get_running_loop()
    driver = _Driver(agent, session_id, timeout)
    cursor = since = len(agent.transcript)
    started = last_activity = loop.time()
    answer_from: int | None = None
    # Several times the per-response timeout: the waits above are bounded one by one and add up
    # to less, so the turn's own deadline never fires first in a normal run.
    turn_task = asyncio.ensure_future(
        run_prompt(agent, session_id, [{"type": "text", "text": prompt_text}], timeout=timeout * 3)
    )
    try:
        while True:
            turn_done = turn_task.done()
            if turn_done and not turn_task.cancelled():
                error = turn_task.exception()
                if error is not None and not isinstance(error, AgentTimeout):
                    raise error
                driver.turn_timed_out = error is not None
            if turn_done and answer_from is None:
                answer_from = len(agent.transcript)
            while cursor < len(agent.transcript):
                if answer_from is not None and cursor >= answer_from:
                    await answer_post_turn_requests(agent, agent.transcript[cursor], since=since)
                driver.ingest(cursor, agent.transcript[cursor])
                cursor += 1
                last_activity = loop.time()
            if await driver.step(loop.time(), turn_done, last_activity, started):
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
    _judge_cascade(driver, result)
    for kind, probe in driver.probes.items():
        setattr(result, kind, probe.result)
        setattr(result, f"{kind}_child", driver.probe_child[kind])
    return result


def _judge_cascade(driver: _Driver, result: ChildCancelRun) -> None:
    if result.cascade_skip is not None or driver.parent_cancel_index is None:
        return
    if result.turn is None:
        result.cascade_skip = "the parent's turn did not end within the budget"
        return
    if result.turn.stop_reason != "cancelled":
        result.cascade_skip = (
            f"the parent's turn ended with {result.turn.stop_reason!r}, not 'cancelled' "
            "(the work ended before the cancel landed)"
        )
        return
    result.cascade_judged = list(driver.cascade_targets)
    result.cascade_unstopped = [c for c in driver.cascade_targets if not driver._idle(c)]
