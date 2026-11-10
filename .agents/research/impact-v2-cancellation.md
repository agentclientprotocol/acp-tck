# v2 impact: cancellation (`cancellation.mdx`, the cancellation parts of `prompt-lifecycle.mdx`, `tool_call/cancel`/`terminal/cancel`, `paused`, `CancelledPermissionOutcome`)

**Sources checked:** agent-client-protocol worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`, base `beac4ba96190` -> target `3961af94fa62` (read with `git show`/`git diff`, not modified). acp-rust-sdk @ `e75d6f19fabb` (2026-11-09), refreshed with `pull --ff-only`. Python SDK not checked, since the new rules are explicit in spec text and schema. TCK @ `200baba` (registry, `test_cancel.py`, `_helpers.py`, v2 fixtures).
**Confidence:** high for the classifications and the spec text. Medium for the proposed test designs, because they have not been prototyped against real agents.

## Answer

The main semantic change: on `session/cancel` the **client no longer MUST answer pending permission requests `cancelled`**. That rule is now a client MAY. Instead the **Agent MUST stop waiting for them** and SHOULD withdraw each one with `$/cancel_request`. The Agent MUST still send `idle(cancelled)`, and "cancellation can finish without receiving answers" (prompt-lifecycle.mdx:1177,1185-1189; cancellation.mdx:40-43; schema.mdx:599-601).

Effects on the TCK:
- `ACP-CANCEL-209`'s text and the `hold_permission` mode of `run_prompt` are out of date. The mode answers the held request immediately after `session/cancel`. That is still legal, but it makes the new MUST and the new SHOULD untestable.
- `ACP-INFO-CANCEL-202` ("MAY at best") is now backed by a SHOULD. It should become an ADVISORY row.
- The conforming `AsksPermissionAgent` fixture becomes non-conforming twice over. It waits for the permission answer before ending a cancelled turn. Its `session/close` path never sends the `$/cancel_request` that session-setup.mdx:391 now makes a MUST.
- `cancellation.mdx` gains client-observable agent MUSTs for `$/cancel_request` (still respond; ignore unknown or already-answered ids, never respond twice). The TCK has never sent `$/cancel_request`. I propose three new rows.
- `ACP-CANCEL-205` loses its `transports.mdx` citation, because the batch section was deleted. Repoint it to `overview.mdx`.

All other cancellation rows are unchanged in meaning and need only remapped citations. `ACP-CANCEL-204` needs a one-phrase text update.

For `tool_call/cancel`/`terminal/cancel` I recommend **deferring them to the ledger now** (DECISION NEEDED, see section D).

## Summary table

| Id | Classification | One-line note |
|----|----------------|---------------|
| ACP-CANCEL-201 | citation-only | Text still matches. New lines are pl:1093,1185-1192,1199, canc:41-44, schema.mdx:603-607. |
| ACP-CANCEL-202 | citation-only (unflagged id) | pl:803,1084-1087,1203; schema.mdx:615-617. Background-work updates after idle don't affect it, since only agent message/thought ids are checked. |
| ACP-CANCEL-203 | citation-only | pl:325,388,1004,1173,1194-1201; canc:59; `IdleStateUpdate/anyOf/4` is still the `cancelled` branch (index unchanged, description widened). pl:1173 now makes the pre-insertion `-32800` a MUST, which strengthens the row. |
| ACP-CANCEL-204 | changed text (tier unchanged) | The SHOULD now covers "tool call invocations **of the cancelled foreground work**". New lines pl:1179; schema.mdx:595-597. |
| ACP-CANCEL-205 | citation change, meaning moved (DECISION NEEDED, minor) | transports.mdx:78-79 was deleted with the batch section. Repoint to overview.mdx:13,151-153,227. |
| ACP-CANCEL-206 | citation-only | `CancelSessionNotification` has no structural change. The JSON example is now at pl:1161-1171. |
| ACP-CANCEL-207 | citation-only | pl:965; `IdleStateUpdate/anyOf/6` is unchanged. |
| ACP-CANCEL-208 | citation-only for this row, plus a new adjacent MUST | session-setup.mdx:389-395. The row's text still matches. The new MUST (cancel pending permissions with `$/cancel_request` before the close response) is proposed separately as N6. |
| ACP-CANCEL-209 | **changed text** (tier unchanged) | The client MUST it relied on is gone. The agent now MUST stop waiting. Recommend holding the request truly unanswered (DECISION NEEDED). |
| ACP-INFO-CANCEL-201 | changed text (tier unchanged; DECISION NEEDED, minor) | The "unknown sessionId not specified" clause is now wrong. session-setup.mdx:51 says "Agents ignore `session/cancel` for a session that isn't active". |
| ACP-INFO-CANCEL-202 | **retire, replaced by new ADVISORY N4** (DECISION NEEDED) | It was "MAY at best". Now it is a SHOULD (pl:1177; canc:40). |
| ACP-PROMPT-207 | citation-only | pl:325,346,388; canc:59. |
| ACP-CLOSE-202 (shares the CANCEL-208 test) | citation-only | session-setup.mdx:389-393; pl:374,1185-1188,1199. This id is owned by the session-setup audit. Noted only because it shares the test. |
| N1 ACP-CANCEL-210 | new, MANDATORY | `$/cancel_request` for an unknown request id gets no response and the connection keeps working. |
| N2 ACP-CANCEL-211 | new, MANDATORY | `$/cancel_request` for an already-answered request gets no second response. |
| N3 ACP-CANCEL-212 | new, CAPABILITY `capabilities.session` | A `session/prompt` withdrawn with `$/cancel_request` still gets exactly one response. |
| N4 ACP-CANCEL-213 | new, ADVISORY | On `session/cancel`, the agent sends `$/cancel_request` for its pending permission request. Replaces INFO-CANCEL-202. |
| N5 ACP-CANCEL-214 | new, CAPABILITY `capabilities.session` (coordinate with the prompt-lifecycle audit) | A held (not yet inserted) prompt covered by `session/cancel` is answered `-32800`. |
| N6 ACP-CLOSE-205 (or the next free CLOSE id) | new, CAPABILITY `capabilities.session` (coordinate with the session-setup audit) | Before the `session/close` response, the agent sends `$/cancel_request` for its pending permission request. |
| L1-L9 | ledger | See section E. |

Abbreviations: pl = `docs/protocol/v2/draft/prompt-lifecycle.mdx`, canc = `docs/protocol/v2/draft/cancellation.mdx`, schema.mdx = `docs/protocol/v2/draft/schema.mdx`, all at target `3961af94fa62`.

## Requirements (target text, by tier)

| # | Requirement | Tier | Citation (@ 3961af94fa62) |
|---|-------------|------|---------------------------|
| R1 | Receiver of `$/cancel_request` MUST still send a response for the original request | MUST | canc:20; schema.mdx:2534-2537 |
| R2 | Receivers MUST ignore `$/cancel_request` for an unknown or already-answered id, and MUST NOT send a second response | MUST | canc:24; schema.mdx:2539-2540 |
| R3 | A cancelled request is answered with the method's cancellation result (inserted prompt's `messageId`, `cancelled` permission outcome, elicitation `cancel`) or `-32800` | MUST (follows from R1 plus the enumeration) | canc:26-29 |
| R4 | Sender that stops waiting SHOULD send `$/cancel_request` | SHOULD | canc:31 |
| R5 | On `session/cancel` the Agent MUST stop waiting for the cancelled work's pending permission requests and treat them as not approved | MUST | pl:1177; canc:40; schema.mdx:599-600 |
| R6 | ...and SHOULD cancel each with `$/cancel_request` | SHOULD | pl:1177; canc:40; schema.mdx:600-601, 2240-2242 |
| R7 | Client MAY answer `cancelled` without waiting for `$/cancel_request` | MAY (client) | pl:1177; canc:40; `#/$defs/RequestPermissionOutcome` (`cancelled` branch description) |
| R8 | `session/cancel` covers foreground work and not-yet-inserted prompts received before it. The Agent MUST answer the covered prompts `-32800`. A prompt received after cancel is not covered. Listed background work is not covered. Agent MAY stop unlisted background activity | MUST / declarative / MAY | pl:1173, 384; `#/$defs/CancelSessionNotification` description |
| R9 | Agent SHOULD stop model requests and tool calls of the cancelled foreground work ASAP | SHOULD | pl:1179; schema.mdx:595-597 |
| R10 | Agent SHOULD ignore late responses or URL completions after cancellation completes | SHOULD | pl:1181-1183; canc:40-41 |
| R11 | Agent MUST send `idle` with `cancelled` if foreground work was active. It can finish without answers to abandoned requests. Nothing is required if no work was active | MUST | pl:1185-1192; canc:41-44; schema.mdx:603-607 |
| R12 | Agents MUST catch abort errors and report `cancelled`, not `error` | MUST | pl:1199; schema.mdx:612-613; `IdleStateUpdate/anyOf/4` |
| R13 | Updates after cancel MUST precede the cancelled idle | MUST | pl:1203; schema.mdx:615-617 |
| R14 | Internal cancellation SHOULD send the same response as for `$/cancel_request` | SHOULD | canc:54-57 |
| R15 | Agents ignore `session/cancel` for a non-active session | declarative (no keyword) | session-setup.mdx:51 |
| R16 | Before responding to `session/close`, the Agent MUST cancel every pending permission request and elicitation of the session with `$/cancel_request` | MUST, capability `capabilities.session` | session-setup.mdx:391 |
| R17 | `tool_call/cancel` / `terminal/cancel`: Client MUST NOT send unless the entity currently advertises `capabilities.cancel`. Agent answers `{}` on acceptance, then confirms with a final `tool_call_update` or an `exitStatus`. `-32602` if unknown, final, or not cancellable. Foreground state unchanged | MUST (client) / declarative (agent), gated per entity | tool-calls.mdx:425-460, 585-606; `#/$defs/CancelToolCallRequest`, `#/$defs/CancelTerminalRequest` |
| R18 | After a `cancelled` permission outcome the Agent MUST NOT proceed. A rejected or `cancelled` permission leaves its tool call `cancelled` or `failed`, not `pending` | MUST / declarative | tool-calls.mdx:340, 423 |

## Details

### A. Existing rows

**ACP-CANCEL-201: citation-only.** The text ("if foreground work was active when cancellation took effect, ... idle cancelled; a prompt cancelled before insertion (`-32800`) with no active state owes no idle") matches pl:1185-1192 and pl:390. New citation: `prompt-lifecycle.mdx:1093,1185-1192,1199; cancellation.mdx:41-44; schema.mdx:603-607`. The test still matches.

**ACP-CANCEL-202: citation-only** (one of the 13 unflagged ids). Base pl:731 maps to 803, 1004-1007 to 1084-1087, 1128 to 1203; schema.mdx 473-475 maps to 615-617. Background activity may emit updates after idle (pl:803, 1044). The test only looks for reuse of the turn's `agent_message*`/`agent_thought*` `messageId`s, so background `tool_call_update`/`terminal_update` traffic cannot trip it. The test still matches.

**ACP-CANCEL-203: citation-only.** pl 255 maps to 325, 312 to 388, 926 to 1004, 1094 to 1173 (rewritten, see below), 1119-1126 to 1194-1201; canc 53 maps to 59. The schema pointer `IdleStateUpdate/anyOf/4` still resolves to the `cancelled` branch (indices 0-7 are unchanged between base and target). Its description now also says "Work the agent stops for its own reasons uses another reason, such as `error` for an internal timeout". pl:1173 turns the base's conditional ("If the Agent cancels a prompt request before insertion, it answers ... `-32800`") into "The Agent **MUST** answer the covered prompts with `-32800`". That only reinforces the row's "`-32800` only before insertion" acceptance. The test still matches.

**ACP-CANCEL-204: changed text, tier stays INFORMATIONAL.** Proposed text: "...SHOULD stop all language model requests and all tool call invocations **of the cancelled foreground work** as soon as possible..." (pl:1179; schema.mdx:595-597). Listed background work is explicitly excluded (pl:1173). The test needs no change (it always SKIPs).

**ACP-CANCEL-205: citation change, meaning moved.** Base `transports.mdx:78-79` ("The receiver MUST NOT reply to a Notification, including a Notification within a batch") was deleted with the batch section. Target transports.mdx has no notification rule at all (lines 1-73). The remaining backing:
- overview.mdx:13 ("Notifications are one-way messages that don't expect a response")
- overview.mdx:151-153 (`session/cancel` "(no response expected)")
- overview.mdx:227 ("Notifications never receive responses (success or error)", was base :197)
- the schema pointers, which are unchanged and still resolve.

DECISION NEEDED (minor): drop the transports citation and cite `overview.mdx:13,151-153,227`. The text and tier (CAPABILITY) are unchanged. JSON-RPC 2.0 itself also forbids replying to notifications. `spec-impact --fix` cannot remap a deleted range, so this row will show up under "Needs review".

**ACP-CANCEL-206: citation-only.** `CancelSessionNotification` is still `{sessionId}` required plus `_meta`. Only its description changed, to "...and its prompts not yet inserted". The pl example moves from 1084-1092 to 1161-1171.

**ACP-CANCEL-207: citation-only.** Base pl:887 maps to 965. The wording is the same ("Custom stop reasons **MUST** begin with `_`. Unknown non-underscore stop reasons are reserved for future ACP variants."). `IdleStateUpdate/anyOf/6` is unchanged.

**ACP-CANCEL-208: citation-only for the row itself.** Base session-setup.mdx:360-366 maps to 389-395. What the row asserts still holds:
- the close cancels foreground work "as if `session/cancel`" (389-390);
- the cancelled idle comes before the close response (393);
- a prompt the close kept from insertion gets `-32800` (395, now "Closing also cancels pending `session/prompt` requests whose messages have not been inserted, including held prompts", which was "may also cancel" at base).

New in the same paragraph (391):
- MUST `$/cancel_request` every pending permission and elicitation before responding. Proposed as N6.
- Closing also stops listed background work.
- (395) "After the close response, the Agent sends no other messages for the session on that connection". That is a CLOSE-area candidate for the session-setup audit, not proposed here.

Since 389-395 overlaps hunks, `--fix` will flag the row. The new range is `session-setup.mdx:389-395`. The test's docstring reference `session-setup.mdx:366` should become `:395`.

**ACP-CANCEL-209: changed text.**
- Old: "...ends the work with an idle `stopReason: "cancelled"`; the client answers the pending request `cancelled`." This mirrored the base client MUST (base pl:1098-1101; base canc:33-34, 57).
- Target: that client MUST is gone. The client "MAY answer ... without waiting for `$/cancel_request`" (pl:1177; canc:40). The agent "MUST stop waiting for that work's pending `session/request_permission` requests and treat them as not approved" (pl:1177; schema.mdx:599-600). "Cancellation can finish without receiving answers to abandoned user-action requests" (pl:1188-1189).
- Proposed text: "Cancelling a turn blocked on the agent's own pending `session/request_permission` (the session last reported `requires_action`) ends the work with an idle `stopReason: "cancelled"` **without the client answering that request**. The TCK leaves it unanswered until the agent withdraws it with `$/cancel_request` or the turn-ending idle arrives, and only then answers it `cancelled`. SKIPPED when no permission request was pending when cancel was sent, or the session was not reported blocked."
- Citation: `prompt-lifecycle.mdx:1153,1177,1185-1189; cancellation.mdx:40-43; schema.mdx:599-607; schema/v2/schema.unstable.json#/$defs/RequestPermissionOutcome; schema/v2/schema.unstable.json#/$defs/CancelledPermissionOutcome`.
- The tier stays CAPABILITY on `capabilities.session`, because R5 and R11 are MUSTs.
- **DECISION NEEDED.** I recommend the strict variant. Otherwise R5 cannot be observed, and an agent that deadlocks waiting for an answer that no longer has to come would pass. The test change lives in `_helpers.run_prompt`, see section B.

**ACP-INFO-CANCEL-201: changed text, still INFORMATIONAL.** "No completion update is required" still holds (pl:1191-1192; canc:43-44). The clause "Behaviour for an unknown `sessionId` is not specified" is now wrong: session-setup.mdx:51 says "Agents ignore `session/cancel` for a session that isn't active". That sentence is declarative with no RFC keyword, and nothing but silence is observable, which CANCEL-205 already covers for the active case. So I recommend keeping the row INFORMATIONAL (DECISION NEEDED, minor) and having it also *record* behaviour for a never-created and for a closed `sessionId`. Proposed text: "Record (never assert) the agent's behaviour on `session/cancel` for an idle active session (no completion update required) and for a session that is not active (the agent ignores it)." Citation: `prompt-lifecycle.mdx:1157,1191-1192; cancellation.mdx:43-44; session-setup.mdx:51`.

**ACP-INFO-CANCEL-202: retire, replaced by N4** (DECISION NEEDED). The row's premise ("Not required (MAY at best)", "propagation is explicitly left to the agent", citing base canc:14,18,57) is gone. canc:63 now reads "The Agent sends `$/cancel_request` for the permission requests of the cancelled work". pl:1177 and canc:40 make it a SHOULD. The `INFO-` id prefix encodes the tier, so I recommend retiring the id and registering an ADVISORY `ACP-CANCEL-213` (N4) rather than re-tiering in place. If the orchestrator prefers keeping the id, change tier to ADVISORY and use the N4 text.

**ACP-PROMPT-207: citation-only.** Base pl:255 maps to 325, 276 to 346, 312 to 388; canc 53 maps to 59. The text matches pl:325 ("Once inserted, it **MUST NOT** return an error response, even if failure or request cancellation occurs") and pl:388. canc:28 now names the inserted-prompt success explicitly as `$/cancel_request`'s cancellation result. The cancelled-turn scenario could gain a `$/cancel_request` variant, see N3.

### B. Do `_helpers.py` and `test_cancel.py` still match?

- **The race gate `_skip_if_turn_end_race_not_exercised` still matches.** Race-plausible reasons (`end_turn`/`max_tokens`/`max_turn_requests`/`refusal`/`_x`/none) match pl:963's "own reasons" list. pl:963 now also says `error` is used "for anything else, such as an internal timeout". So an independent failure racing a cancel could in principle legitimately end `error`. The module's "`error` is never excused" stance rests on pl:1199, which is unchanged from base 1124, so this is not a new conflict. It is a pre-existing project choice; flagging it only.
- **`_skip_if_no_cancelled_idle_owed` still matches** (pl:390, 1191-1192).
- **`hold_permission` mode in `run_prompt` (`_helpers.py:1021-1031`) no longer matches the target.** It fires `session/cancel` and then, in the same `_handle_message` call, answers the held request `cancelled`. Under target text that is a legal client MAY. But it means:
  1. R5 ("MUST stop waiting") is never exercised: the answer is always on the wire.
  2. N4's `$/cancel_request` can only be seen if the agent happens to process `session/cancel` before the answer.
  3. The docstring cites base `prompt-lifecycle.mdx:1098-1100` as the reason, and that rule was deleted.

  Recommended change:
  - In hold mode, keep the request unanswered after `session/cancel`.
  - Answer it `{"outcome":"cancelled"}` when either an agent `$/cancel_request` whose `requestId` equals the held request's `id` arrives (tool-calls.mdx:326 says the client answers a `$/cancel_request`ed permission request `cancelled`), or the turn-ending idle arrives (a tidy, harmless late answer; agents SHOULD ignore late answers, pl:1181-1183).
  - Record the index of the `$/cancel_request` and whether it preceded the idle.
  - The non-hold path (answer `cancelled` once the trigger fired) stays as is. It is a legal MAY.
- **`run_prompt` docstring "Callers must serialize prompts per session; v2 leaves concurrent prompts unspecified"** is outdated. pl:382 says "Clients **MAY** send `session/prompt` in any state ... Agents **MUST NOT** reject a prompt only because foreground work is active". This belongs to the prompt-lifecycle audit (`ACP-INFO-CONCURRENT-201`). Noted for routing.
- `test_cancel.py` docstring line references (`:1109-1113,1124`, `:1094,1115-1117`, `session-setup.mdx:366`) and the `_helpers.py` ones (`:864`, `:314`, `:891`, `:1004-1007`, `:124,993`, `:1000-1002`) are base line numbers. They are cosmetic, but `--fix` does not touch code comments.
- `test_close_cancels_foreground_work`, `test_cancel_notification_receives_no_direct_response`, `test_cancel_with_meta_is_accepted`, `test_cancel_does_not_surface_as_a_generic_failure`, `test_cancel_resolves_with_a_cancelled_idle` and `test_no_cancelled_work_output_after_the_cancelled_idle` all still match target text.
- `test_cancel_during_pending_permission_request_behaviour` (INFO-CANCEL-202) is replaced by N4.

### C. New requirements

**N1 ACP-CANCEL-210: MANDATORY, no capability.**
- Text: "A `$/cancel_request` naming a request id the client never sent gets no response of any kind, and the agent keeps serving the connection."
- Citation: `docs/protocol/v2/draft/cancellation.mdx:24 @ 3961af94fa62; docs/protocol/v2/draft/schema.mdx:2539-2540 @ 3961af94fa62`; schema `#/$defs/CancelRequestNotification`.
- Tier: "Receivers **MUST** ignore". It is unconditional. The Protocol-Level note "free to ignore `$/` notifications" (schema.mdx:2516-2521) is consistent with it.
- Observation: after `initialize`, send `{"jsonrpc":"2.0","method":"$/cancel_request","params":{"requestId":"tck-never-sent-<uuid>"}}`. Within `quiet_period` there must be no response-shaped line (no `method`; especially none with `id` equal to that requestId). Then send a `_tck/...` probe request; any response proves liveness. Optionally repeat with an integer id (`RequestId` is string|integer).
- Fixture: `answers_cancel_request.py`, which replies to every `$/cancel_request` with an error (for example `-32602 "unknown request"`) carrying `id: requestId`. It also trips N2.
- Rust SDK agrees: an unknown id finds no slot and `cancel()` returns `false` (`src/agent-client-protocol/src/jsonrpc.rs:2632-2656`).

**N2 ACP-CANCEL-211: MANDATORY, no capability.**
- Text: "A `$/cancel_request` for a request the agent already answered produces no second response."
- Citation: `cancellation.mdx:22,24 @ 3961af94fa62; schema.mdx:2534-2540 @ 3961af94fa62`.
- Observation: use the main `initialize` request's id, which is already answered, so no capability is needed. Send `$/cancel_request{requestId: <that id>}` and assert no further message with that `id` within `quiet_period`. Then run a liveness probe.
- Fixture: the same `answers_cancel_request.py` (it answers `-32800` with the cancelled id), or a dedicated `re_answers_after_cancel.py` if one-fixture-per-id is wanted.

**N3 ACP-CANCEL-212: CAPABILITY `capabilities.session`.**
- Text: "A `session/prompt` the client withdraws with `$/cancel_request` still receives exactly one response: success with a string `messageId` (inserted), or an error. An error of `-32800` implies no user-message update was emitted for it."
- Citation: `cancellation.mdx:20,22,26-29,59 @ 3961af94fa62; prompt-lifecycle.mdx:325,384,388 @ 3961af94fa62; schema.mdx:2534-2537 @ 3961af94fa62`.
- Tier: R1 is a MUST. Only "still answered, exactly once" and "`-32800` only pre-insertion" are asserted. Another error code could be a "normal response" for a request the agent chose not to cancel (canc:22), so it is recorded but not failed.
- Observation: send `session/prompt` (cancel prompt), immediately send `$/cancel_request` with its id, wait up to `--timeout` for the response, then check for duplicates within `quiet_period`. Clean up with `session/cancel` and drain to idle if active. `$/cancel_request` on an inserted prompt does not stop its work (canc:35-38,59). No race SKIP is needed: either outcome is legal.
- Fixture: `drops_withdrawn_prompt.py`, which holds `__hang__` before insertion (like `cancel_before_insertion.py`) and on `$/cancel_request` silently discards it, sending no response. That trips N3 only (run with `--cancel-prompt __hang__`).

**N4 ACP-CANCEL-213: ADVISORY. Replaces ACP-INFO-CANCEL-202.**
- Text: "When `session/cancel` cancels foreground work blocked on the agent's own pending `session/request_permission`, the agent withdraws that request with `$/cancel_request` (its `requestId` naming the agent's request)."
- Citation: `prompt-lifecycle.mdx:1177 @ 3961af94fa62; cancellation.mdx:40,63 @ 3961af94fa62; schema.mdx:599-601,2240-2242 @ 3961af94fa62`.
- Tier: SHOULD, so ADVISORY.
- Observation: the same scenario as CANCEL-209 in the strict hold mode. PASS if an agent `$/cancel_request{requestId: held.id}` arrives (before or after the idle, within `quiet_period` after it). FAIL if none arrives. SKIP under the same preconditions as CANCEL-209.
- Optional extra assertion: any agent-sent `$/cancel_request` names an id of an agent -> client request (canc:12). That sentence is definitional, with no keyword, so record it only.
- Fixture: `cancel_without_cancel_request.py`. It stops waiting and sends `idle(cancelled)` but never sends `$/cancel_request`. It trips N4 only.

**N5 ACP-CANCEL-214: CAPABILITY `capabilities.session`.** Coordinate with the prompt-lifecycle audit, which owns "Prompts during active work".
- Text: "A `session/prompt` received before `session/cancel` and still not inserted (no response, no user-message update) is answered `-32800` by the cancel. It is never left pending and never inserted afterwards."
- Citation: `prompt-lifecycle.mdx:1173,384 @ 3961af94fa62`; `#/$defs/CancelSessionNotification` description ("cancel a session's foreground work and its prompts not yet inserted").
- Tier: "The Agent **MUST** answer the covered prompts with `-32800`".
- Observation:
  1. Start a `__hang__`/cancel-prompt turn and wait for an active state.
  2. Send P2 without awaiting it.
  3. If P2 is answered or echoed before cancel can be sent, SKIP ("prompt inserted immediately, not held").
  4. Otherwise send `session/cancel`.
  5. Assert P2 gets a response. If it is an error, the code must be `-32800`.
  6. If it is a success arriving within the race window, SKIP (the agent may have inserted P2 just before reading cancel). A success after the window FAILs.

  Optionally record (do not assert) that a P3 sent *after* the cancel is not answered `-32800`. pl:1173 says so, but declaratively. Real agents that insert immediately will SKIP. That is fine.
- Fixture: `held_prompt_survives_cancel.py`. It holds P2 while running. On cancel it ends the turn `cancelled`, then after sleeping past the race window inserts P2 and runs it. Trips N5 only.

**N6 ACP-CLOSE-205 (next free CLOSE id): CAPABILITY `capabilities.session`.** Coordinate with the session-setup audit.
- Text: "When `session/close` lands while the agent's own `session/request_permission` for that session is pending, the agent sends `$/cancel_request` for it before the successful `session/close` response."
- Citation: `docs/protocol/v2/draft/session-setup.mdx:391 @ 3961af94fa62`.
- Tier: "Before responding to `session/close`, the Agent **MUST** cancel every pending permission request and elicitation ... with `$/cancel_request`".
- Observation: hold a permission request (as in CANCEL-209), send `session/close` instead of cancel, and assert a `$/cancel_request{requestId: held.id}` line precedes the close response. SKIP if no permission request was pending.
- Fixture: the current `AsksPermissionAgent._handle_close_session` behaviour (cancelled idle and close response, no `$/cancel_request`) becomes the non-conforming `close_keeps_permission_open.py`. The base class must be fixed.

### D. `tool_call/cancel`, `terminal/cancel`, `paused`, `CancelledPermissionOutcome`

- **`tool_call/cancel` / `terminal/cancel` (DECISION NEEDED). Recommendation: ledger them as deferred now, no requirements.** Reasons:
  1. The gate is **per entity and dynamic** (`tool_call_update.capabilities.cancel` / `terminal_update.capabilities.cancel`, tool-calls.mdx:427-440,587-600), not an `initialize` path. `Requirement` forces `Tier.CAPABILITY` to carry an `initialize`-result path (`src/tck/common/requirements.py:39-42`), so such rows would have to gate on `capabilities.session` and SKIP at runtime.
  2. A client-driven TCK has no reliable way to make an agent emit a cancellable tool call or terminal. Only agents with background or long tool work do, and only for certain prompts. Real-agent coverage would be near-zero SKIP.
  3. The `-32602` paths (unknown, final, not cancellable; tool-calls.mdx:459,605) can only be probed by violating the client MUST NOT ("unless ... currently advertises `capabilities.cancel`", tool-calls.mdx:456,602). The TCK holds its own probe traffic to the rules.
  4. Both come from the v2 background-work RFD (`docs/rfds/v2/background-work.mdx`, Active).

  If coverage is wanted later, the observable agent-side rows would be:
  - after an advertised `tool_call/cancel`, a schema-valid `{}` result and then a `tool_call_update` with a final status (`cancelled`/`completed`/`failed`), with no state transition caused by it;
  - after `terminal/cancel`, `{}` and then a `terminal_update` with `exitStatus`.

  These would be CAPABILITY (`capabilities.session`) with a dynamic SKIP, plus fixtures that advertise `cancel` on a `__hang__` tool call.
- **`ToolCallStatus.paused`: no cancellation row is affected.** But the hand-copied `TOOL_CALL_STATUS` (`src/tck/v2/protocol.py:76`) lacks `paused`. Without the update, `ACP-ENUM-201` would flag a conforming `paused` as an unknown unprefixed value. `tests/v2/test_validation.py:185` will catch it after the schema vendor. This is owned by the tool-calls/enum audit.
- **`RequestPermissionOutcome.cancelled` -> `CancelledPermissionOutcome`** (adds optional `_meta`). It is a refactor only. The TCK's `{"outcome":"cancelled"}` is still valid, and the TCK never validates its own client traffic. CANCEL-209's pointer `#/$defs/RequestPermissionOutcome` still resolves. Optionally add `#/$defs/CancelledPermissionOutcome`.

### E. Ledger (deliberate non-requirements, `[[not_requirement]]`)

| # | citation (@ 3961af94fa62) | statement | reason |
|---|---------------------------|-----------|--------|
| L1 | `prompt-lifecycle.mdx:1175` | Client SHOULD preemptively mark the cancelled work's non-finished tool calls `cancelled` | client-side rule |
| L2 | `prompt-lifecycle.mdx:1177`; `cancellation.mdx:40` | Client MAY answer a cancelled work's permission request `cancelled` without waiting for `$/cancel_request` | client-side permission |
| L3 | `prompt-lifecycle.mdx:1181-1183,1109-1110`; `cancellation.mdx:40-41` | After cancellation completes, the Agent SHOULD ignore late responses or URL completions rather than resume the work | unobservable: "ignored" can't be told apart from "used without visible effect". Probing it needs a non-`cancelled` late answer, which contradicts the client rule once the agent has sent `$/cancel_request` |
| L4 | `cancellation.mdx:31` | A sender that stops waiting SHOULD send `$/cancel_request` (agent as sender, for its own timeouts) | no client-side trigger to make the agent abandon its own request, beyond the session-cancel case N4 covers |
| L5 | `cancellation.mdx:49-57` | On internal cancellation (context limit, internal timeout) the executing party SHOULD send the same response as for `$/cancel_request` | not elicitable from a client-driven TCK |
| L6 | `prompt-lifecycle.mdx:1173,1177`; `tool-calls.mdx:268` | `session/cancel` does not cover listed background work or its permission requests; Agent MAY stop unlisted background activity | not elicitable (needs an agent that reports `background`); defer with background-work coverage |
| L7 | `cancellation.mdx:12` | Receivers match `$/cancel_request` only against requests received from that sender | unobservable beyond N1/N2: misapplying it to the agent's own outgoing request has no reliable wire symptom |
| L8 | `tool-calls.mdx:425-460,585-606`; `#/$defs/CancelToolCallRequest`; `#/$defs/CancelTerminalRequest` | Per-entity `tool_call/cancel`/`terminal/cancel` contract | deferred (section D): per-entity dynamic gate, not elicitable, error paths need client-rule violations |
| L9 | `prompt-lifecycle.mdx:1179` (=`ACP-CANCEL-204`) | Already registered as INFORMATIONAL | no ledger entry needed; listed only so it is not double-entered |

### F. Fixture and `test_cli.py` impact

- `_base.py` `AsksPermissionAgent` (used by `asks_permission.py`, `conforming_full.py`, `emits_batch_updates.py`, `requires_action_no_running.py`, `requires_action_then_idle.py`, `starts_blocked.py`, `*_custom_permission_kind.py`) must become conforming under the target:
  - In `_handle_cancel`, if `_pending_permission` belongs to the session: send `$/cancel_request{requestId: perm_id}`, clear the pending request, and send `idle(cancelled)` (R5, R6, R11). Ignore the late answer.
  - In `_handle_close_session`, send `$/cancel_request` before the idle and the response (N6).

  Without this, the strict CANCEL-209 times out, which FAILs the conforming baselines. `requires_action_then_idle.py` inherits the fix.
- `asks_permission_ignores_cancel.py`: its defect ("treats `cancelled` like any answer, resumes `end_turn`") must be re-expressed for the strict flow. The simplest version keeps waiting on `session/cancel` (the old base behaviour). That FAILs CANCEL-209 (timeout) and N4. Alternatively it sends `$/cancel_request` and, on the `cancelled` answer, resumes `end_turn`. That FAILs CANCEL-209 only and keeps its "exactly CANCEL-209" purpose. I recommend the latter, and adding `cancel_waits_for_permission_answer.py` for the former.
- New fixtures: `answers_cancel_request.py` (N1/N2), `drops_withdrawn_prompt.py` (N3), `cancel_without_cancel_request.py` (N4), `held_prompt_survives_cancel.py` (N5), `close_keeps_permission_open.py` (N6).
- `tests/v2/test_cli.py`:
  - INFO-CANCEL-202 appears at :149, :163 and :961. Replace it with N4.
  - Per-fixture FAIL sets for `cancel_no_idle.py`: it FAILs INFO-CANCEL-202 via timeout. N4 would FAIL the same way, and so would N3/N5 if they rely on cancel. Re-derive the set.
  - `_FULL_EXPECTED_SKIPS` (:423) still holds for CANCEL-209. N4 and N6 SKIP the same way under `__hang__`.

## Testability notes

- N1/N2 are cheap, deterministic and capability-free. A conforming agent is silent. A non-conforming one sends an error or result naming the id, or dies. "Ignore" beyond silence plus liveness is unobservable.
- N3 is race-free: both outcomes are legal, and only "answered exactly once" plus "`-32800` implies no echo" are judged.
- The strict CANCEL-209 and N4 replace a hold-then-answer race with an honest wait. An agent that needs the answer to finish is now distinguishable (it times out and FAILs). An agent that sends `$/cancel_request` is visible regardless of ordering.
- N5 and N6 SKIP against agents that insert immediately or never ask permission. That is expected, not a defect.
- Unobservable: promptness (CANCEL-204), ignoring late answers (L3), internal cancellation (L5), background-work coverage (L6).

## Discrepancies

- None between docs, schema descriptions and the Rust SDK on the new rules. Rust `session/v2.rs:872-940` restates "stops waiting ... should cancel each of them with `$/cancel_request`", "a client may also answer ... without waiting", and "before it responds, the agent cancels every pending permission request and elicitation ... with `$/cancel_request`". `jsonrpc.rs:2632-2656` ignores unknown ids.
- One soft tension inside the spec: the Protocol-Level text (schema.mdx:2516-2521) says a receiver "is free to ignore" `$/` notifications, while canc:20 says "**MUST** still send a response for the original request". These are consistent: ignoring the cancel means sending the normal response. N3 asserts only the response, not the cancellation.
- The `error` race note in section B: pl:963 vs the TCK's never-excuse-`error` choice. This is a project design point, not a spec conflict.

## Open questions

- Ownership overlaps to route: N5 and the outdated "serialize prompts" note (prompt-lifecycle audit, `ACP-INFO-CONCURRENT-201`); N6, CLOSE-202 and the "no messages after close response" MUST at session-setup.mdx:395 (session-setup audit); `TOOL_CALL_STATUS` + `paused` (tool-calls/enum audit); `ACP-EXT-203`'s removed `ProtocolLevelNotification` pointer (extensibility audit); elicitation "Session cancellation" (elicitation audit), which has parallel `$/cancel_request` rules that N4/N6 could extend to elicitations.
- Map (`spec-tracker/maps/v2.toml`): `cancellation.mdx` is not core. Its `$/cancel_request` contract is now assumed without restating by prompt-lifecycle (:384 held-prompt withdrawal), session-setup (:391), tool-calls (:326) and elicitation. I recommend adding it as a core doc (whole doc), with code `src/tck/v2/conformance/_helpers.py` and `src/tck/v2/conformance/test_cancel.py`.
- Sentence-cased prompt-lifecycle section addresses relevant here:
  - `"Cancellation"` is unchanged.
  - `"Stop Reasons"` -> `"Stop reasons"`.
  - `"2. Prompt Accepted"` -> `"2. Prompt accepted"`. Its new subsections "Insertion and ordering", "Prompts during active work" and "Prompts that are never inserted" are covered by it. They should stay core, since cancel coverage of held prompts depends on them.
  - `"Session States"` -> `"Session states"`.
  - `"Foreground and Background Work"` -> `"Foreground and background work"`. It now covers "Background work", which should be core because cancel and close coverage depend on the `background` list.
  - `"Prompt Lifecycle > (intro)"` -> `"Prompt lifecycle > (intro)"`.
  - The prompt-lifecycle audit owns the final list.
- Python SDK was not checked. Check it if the orchestrator wants SDK confirmation for N1-N3.
