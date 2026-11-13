# The mock-client prompt driver

Each version's conformance suite drives `session/prompt` through its own `run_prompt` in
`src/tck/v{1,2}/conformance/_helpers.py`. `run_prompt` acts as a minimal ACP client for the length of one turn:

- answers `session/request_permission` per a [policy](#permission-policies). A request carrying another
  session's ID (a subagent's) is answered the same way. What the trigger does to it differs by version. **v2**
  never holds it and does not cancel it: only the prompted session's foreground requests are answered `cancelled`
  once the trigger has fired. **v1** answers every request `cancelled` once the trigger has fired, whatever its
  `sessionId`;
- answers every other agent -> client request (`fs/*`, `terminal/*`, `elicitation/create`, ...) with `-32601`,
  because the mock client advertises no `fs`, `terminal` or elicitation capability, and records it in
  `PromptTurn.client_requests_seen`. Two v1 connections advertise one unrelated feature and nothing else, so
  those requests are still answered `-32601` there: the plan rows (`test_plan.py`, `plan`) and the subagent rows
  (`_subagents_connection.py`, `subagents`);
- records `session/update` notifications in wire order;
- optionally fires a trigger mid-turn (`on_cancel` sends `session/cancel`, `on_action` sends another request,
  for example `session/close`);
- raises `AgentTimeout` if the turn does not end within `timeout`.

The two versions are separate, non-shared implementations because their turn-end contracts differ. The code is the
exact contract; read `_helpers.py` before writing a new prompt test. This page records what the code guarantees.

## Turn end

**v1.** The `session/prompt` response *is* the turn's result and carries `stopReason`. `run_prompt` returns when
that response arrives. Every `session/update` it recorded was read before it, off the same stdout stream.

**v2.** The response is only an acceptance receipt (`{messageId}`), and the turn's outcome is learned from
`state_update` notifications for the prompted session (a child session's states never count). `run_prompt`
tracks whether the session is active (`running` or `requires_action`; it starts active if that was the last known
state). Once the response has been read:

- the first `idle` after an active state ends the turn, whatever its `stopReason` (that field is only SHOULD).
  An idle read *before* the response is a candidate that becomes final after `quiet_period(timeout)` with no
  active state; an active state voids it;
- an error response with no active state ends the turn after a short peek finds none. If work is active, the
  driver keeps waiting for the idle the agent still owes;
- fallback for agents that never report an active state: an `idle` carrying a `stopReason` ends the turn after
  `quiet_period(timeout)` with no active state after it and after the response.

`PromptTurn.terminated_by` records which path ended the turn (`idle`, `idle_without_active`, `error`).
A second prompt during a turn is sent raw, as `on_action`; callers serialize prompts per session.

## Permission policies

`session/request_permission` is answered per the `permission` argument. Options are picked by `kind`, never by
position or "first option".

| Policy | Answer |
| --- | --- |
| `allow` (default) | `allow_once`; else `allow_always` (recorded); else `reject_once` (recorded); else the unsatisfiable case below. |
| `reject_once` | `reject_once`; else the unsatisfiable case. |
| `unknown_option` | `selected` with an `optionId` the agent never offered (`_tck_unoffered_option`). |
| `unknown_outcome` (v2 only) | a custom `_`-prefixed outcome (`_tck_unknown`), legal because the outcome is an open enum. |
| `cancelled` | the `cancelled` outcome, without sending `session/cancel`. |

No policy ever selects a `reject_always`, and only `allow` ever falls back to `allow_always`, because an `*_always`
persists an approval or a standing deny in the operator's own agent. A fallback is recorded as the
`acp_tck_permission_fallback` test property and in `PromptTurn.permission_fallbacks`.

**Unsatisfiable policy.** When none of the policy's option kinds is offered, the mock client never picks another
option. As a conforming client does before answering a pending request `cancelled`, it sends `session/cancel` for
the prompted session first, then answers `cancelled`. It records a note in `PromptTurn.permission_cancels`, and the
turn drains like any cancelled turn. A test that depends on a specific option kind should SKIP when
`permission_cancels` is set (v1's `test_permissions.py` does); a missing `reject_once` is not a FAIL, since no rule
requires offering one.

A request of another session (a subagent's) never triggers that `session/cancel`: in v1 it would end the prompted
turn, and in v2 a client MUST NOT cancel a subagent that does not advertise `capabilities.cancel` (the driver does not
track which do). Such a request is answered `cancelled` without any `session/cancel` and recorded in
`PromptTurn.permission_fallbacks`, not `permission_cancels`.

**After a cancel.** Once the TCK has sent `session/cancel` for a request's session since the turn began, that
request is answered `cancelled`: a real client resolves a pending prompt that way rather than choosing for the user
(v1 prompt-turn.mdx:641; v2 prompt-lifecycle.mdx:1177; Subagents RFD, "Pending permission and elicitation requests").
This covers the driver's own trigger, and also a `session/cancel` that a driver such as `drive_child_cancel` sent for the
prompted session or for a child on the same connection, whichever session it names. A request of a session nobody
cancelled, such as a sibling's, is still answered per the policy, since cancelling one session does not resolve
another's requests. A cancel from an earlier turn does not count.

**Holding (v2 only).** `hold_permission=True` is a mode, not a policy, and needs a trigger. The trigger fires when the
first foreground `session/request_permission` arrives, and that request is left unanswered, because after
`session/cancel` the agent must stop waiting for it. It is answered `cancelled` only when the agent withdraws it
with `$/cancel_request`, when the turn ends (after a `quiet_period` wait for a late `$/cancel_request`), or when the
deadline passes with the turn still open. `PromptTurn.held_answered_on` records which, so a test can tell "ended once
answered" from "never ended".

## Background-work permission requests (v2 only)

A request whose `subject` names an item in the session's latest `state_update.background` list (a terminal, tool
call or subagent) is background work. `session/cancel` does not cover it, so `run_prompt` never holds it and never
resolves it as cancelled by the trigger: it is always answered per the policy. If the policy cannot be satisfied,
it is answered `cancelled` **without** `session/cancel`, so foreground work is not cancelled by a request that
does not belong to it. A `state_update` that omits `background` leaves no background items known. v1 has no
background list.

## Cancel races

Whether `session/cancel` lands while the turn is still in flight depends on how fast the agent finishes, which the
TCK cannot control. The driver and the tests keep that race from producing a false PASS or FAIL.

**Trigger timing.** The trigger fires on the first `session/update` (v1) or on the first transition to an active
state (v2), or once `cancel_wait` (default 0.5 s) elapses, whichever comes first. Right before firing, the driver
takes a short peek (`cancel_race_peek(timeout)`, between 50 ms and 500 ms) for a turn end already sitting in the
pipe. If one is there, it returns with `cancelled_at_index=None` as if cancel was never sent, so an agent that
finished first is not misreported as having ignored the cancel.

**Which outcomes SKIP** ("cancellation not exercised"; the tests decide, not the driver):

- v1: `cancelled_at_index is None`, or the response is a valid, non-`cancelled` `stopReason` that arrived within
  `quiet_period(timeout)` of the cancel.
- v2 (`skip_if_turn_end_race_not_exercised`): the trigger was never sent; or the prompt was answered with an error
  before the trigger was sent; or the turn-ending idle arrived within `quiet_period(timeout)` of the trigger with a
  stop reason the agent could plausibly have reached on its own (`end_turn`, `max_tokens`, `max_turn_requests`,
  `refusal`, a `_`-prefixed value, or none). `error` is never excused: reporting an abort as `error` is the defect
  the spec singles out.

Anything else is judged normally: `cancelled` passes; an error or a late non-`cancelled` stop reason fails.
`quiet_period(timeout)` is `timeout / 10` clamped to 0.5-2.0 s.
`--cancel-prompt TEXT` gives a real agent enough work to still be in flight when the trigger lands.

## Cancelling a single item (v2 only)

`ACP-TOOLCANCEL-*` and `ACP-TERMCANCEL-*` use `drive_item_cancel` instead of `run_prompt`'s trigger. It sends
`--cancel-prompt` (so those rows SKIP against an agent whose turn offers nothing cancellable; the default essay
prompt essentially never does) and reads the turn in wire order, tracking each tool call's and terminal's
`capabilities.cancel` with the patch rules. Then:

- for the first tool call and the first terminal that advertise `cancel` while not final, it sends `tool_call/cancel` /
  `terminal/cancel` (never for an item that does not currently advertise it) and waits `timeout / 2` for the response
  and the confirming final update. A `-32602` is not a rejection when the item's final update, or the agent's
  withdrawal of `cancel`, arrives before it or within `quiet_period(timeout)` after it; any other error is. The next
  live item is tried after such a race;
- for the first item that is final yet still advertises `cancel`, it sends one further request, which must be rejected
  (`-204`/`-205` rows);
- once nothing more is live (nothing new for `max(quiet_period(timeout), timeout / 4)`, `quiet_period(timeout)` after
  the turn's idle, or `timeout` since the prompt), it sends its own `session/cancel` for the turn.

Every wait is bounded per step, never by one overall deadline, so a turn that streams for a long time is judged on what
it advertised and not failed because the TCK ran out of time. The turn's own end is not judged (the `ACP-CANCEL-*` rows
own that): the driver gives the turn `timeout * 3` and ignores a timeout. Agent -> client requests that arrive after the
turn's idle (background work may ask for permission) are answered like `run_prompt` does: `session/request_permission`
per the `allow` policy (`cancelled` for a session the TCK cancelled), anything else `-32601`.

## Cancelling a subagent (`drive_child_cancel`)

`ACP-SUBAGENT-016`/`017` (v1 and v2), `ACP-SUBAGENT-202` and the child-item rows `ACP-TOOLCANCEL-203` /
`ACP-TERMCANCEL-203` (v2 only) share one driven turn of `--cancel-prompt` (`_child_cancel.py`), so a real agent needs
a prompt that makes it delegate to a child that can still be cancelled: one that advertises `capabilities.cancel`, or
whose tool call or terminal does. Otherwise the rows SKIP ("no child advertised `capabilities.cancel` while reported
running"). In v1 the connection advertises `subagents` and nothing else, and a child's state is only the parent's
`subagent_update.state`; v2 also reads each child's own `state_update`. The driver reads the turn in wire order,
tracking each announced child and its `cancel` capability, state, tool calls and terminals, then, each step bounded
(`timeout` to find something to cancel, `timeout / 2` for each response):

1. (v2) `tool_call/cancel` / `terminal/cancel` with the child's `sessionId` for the first child item that advertises
   `cancel` and is live, judged like `drive_item_cancel`. A request still awaiting its verdict when the rest of the run
   ends is waited for, not turned into a race.
2. `session/cancel` with the child's `sessionId`, only for a child that advertises `cancel` and was last reported
   running (a client MUST NOT cancel one that does not). The child's idle report settles it: `idle` with
   `stopReason: "cancelled"` confirms (016). Another idle within `quiet_period(timeout)` of the request, with a stop reason
   the child could have reached on its own, is the same race as for `ACP-CANCEL-*` (the child had ended first) and
   SKIPs 016/017; a later one FAILs 016 (the child finished instead of stopping). No idle within `timeout / 2` FAILs
   016. For `quiet_period(timeout)` after the child settles the driver watches the parent: an `idle`/`cancelled`
   (v2) or a `cancelled` prompt response (v1) FAILs 017. A sibling that reports `idle`/`cancelled` is only recorded
   (`acp_tck_cancelled_siblings`), since the Agent may cancel its own delegated work.
3. `session/cancel` for the parent, so nothing is left behind. In v2, once its turn ends `cancelled`, every descendant
   that was running and that the parent's work waits on must reach `idle` within `timeout / 2` (202). A descendant counts
   as waited on only if its parent reported a `background` list after announcing it that does not name it; a child
   announced after the parent's latest list, or a parent that reports no list, leaves it unjudged, because the agent may
   re-send the state when the list changes only as a SHOULD.

The turn's own end is not judged (`ACP-CANCEL-*` own that), and agent requests read after the parent's turn ends are
answered like `run_prompt` does.
