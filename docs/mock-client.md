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
the request's session first, then answers `cancelled`. It records a note in `PromptTurn.permission_cancels`, and the
turn drains like any cancelled turn. A test that depends on a specific option kind should SKIP when
`permission_cancels` is set (v1's `test_permissions.py` does); a missing `reject_once` is not a FAIL, since no rule
requires offering one.

**After the trigger.** Once `session/cancel` (or the `on_action` request) has been sent, a permission request for
the prompted session is answered `cancelled`: a real client resolves a pending prompt that way rather than choosing
for the user.

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
