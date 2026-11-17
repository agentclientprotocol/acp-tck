# What would it take to add the PR #10 follow-up "not cancellable `-32602` probes" (v2 `tool_call/cancel` / `terminal/cancel`), and how big is it?

**Sources checked:**
- agent-client-protocol @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (the repo's pin; the checkout's HEAD is `94d7666d`, 2026-11-02, but every spec citation below is read at the pin with `git show 3961af94:<path>`)
- acp-rust-sdk @ `6a4a95c` (2026-11-16, HEAD after `pull --ff-only`; not pinned to the spec revision)
- acp-python-sdk @ `4fed584` (2026-11-16, HEAD)
- acp-tck, branch `pr10-follow-ups` @ `f5d3aa3` (working tree clean)

**Confidence:** high on what the spec says and on the files to touch; medium on the LOC estimate and on the
fixture fallout. The fallout depends on two design choices (below) and on whole-suite runs I did not do.

## Answer

The draft docs, the schema descriptions and the Active background-work RFD all say the same thing: the Agent
"responds with `-32602` if the tool call is unknown, already final, or not cancellable" (`terminal/cancel`:
"unknown, has already exited, or is not cancellable"). None of them puts an RFC keyword on the agent's answer.
The only keyworded rule is the client's: it **MUST NOT** send either request unless the item currently advertises
`capabilities.cancel`. On the wire, cancellability is just the item's effective `capabilities.cancel`: an object
means cancellable, and omitted or `null` means "unsupported". There is no other flag. PR #10 covered only the
"already final" case (`-204`/`-205`). The "unknown" and "not cancellable" cases are deferred in the ledger
(`spec-tracker/maps/v2.toml:605-608,615-618`).

Following the existing `-204`/`-205` encoding, the follow-up would add four rows per method:
- an unknown-id rejection row (CAPABILITY, `inferred:toolCallCancel` / `inferred:terminalCancel`) and its
  `-32602` code row (ADVISORY);
- a not-cancellable rejection row (CAPABILITY, same gate) and its code row (ADVISORY).

That is 8 rows in total, `ACP-TOOLCANCEL-206..209` and `ACP-TERMCANCEL-206..209`. Splitting it this way gives:
- **Unknown-id half: small** (about 250-350 LOC). It is a race-free request for an invented id in the TCK's own
  session. Conforming fixtures already answer it `-32602`.
- **Not-cancellable half: medium** (about 450-550 LOC). It needs a new probe in `drive_item_cancel` with race
  handling, fixtures that emit a live item that does not advertise `cancel`, and changes to many `test_cli.py`
  expectations.
- **Both together: M, about 700-900 LOC.** It fits one PR next to small follow-ups that stay out of
  `test_item_controls.py`, `drive_item_cancel` and the item-cancel section of `tests/v2/test_cli.py`. Next to
  another medium change in that area, ship the unknown-id half alone.

## Requirements

| # | Requirement | Tier | Citation |
|---|---|---|---|
| 1 | Client MUST NOT send `tool_call/cancel` unless the tool call currently advertises `capabilities.cancel` (client rule; the probes break it on purpose) | MUST (binds the client, not testable on the agent) | spec `docs/protocol/v2/draft/tool-calls.mdx:456`; `schema/v2/schema.unstable.json#/$defs/CancelToolCallRequest` (description); `docs/rfds/v2/background-work.mdx:124` (Active RFD) |
| 2 | Same for `terminal/cancel` | MUST (client) | spec `tool-calls.mdx:602`; `#/$defs/CancelTerminalRequest`; `background-work.mdx:163` (Active RFD) |
| 3 | `tool_call/cancel` for an **unknown** tool call is rejected with an error, not answered with a result | CAPABILITY `inferred:toolCallCancel` (declarative docs sentence, no keyword; precedent `ACP-TOOLCANCEL-204`) | spec `tool-calls.mdx:459`; `background-work.mdx:126` (Active RFD, secondary) |
| 4 | ...and that error is `-32602` | ADVISORY (code in a declarative sentence, error-code policy) | `tool-calls.mdx:459` |
| 5 | `tool_call/cancel` for a live tool call that does **not** currently advertise `cancel` is rejected with an error | CAPABILITY `inferred:toolCallCancel` | `tool-calls.mdx:440,456,459` |
| 6 | ...and that error is `-32602` | ADVISORY | `tool-calls.mdx:459` |
| 7 | `terminal/cancel` for an unknown terminal is rejected with an error | CAPABILITY `inferred:terminalCancel` | `tool-calls.mdx:605`; `background-work.mdx:165` (Active RFD, secondary) |
| 8 | ...code `-32602` | ADVISORY | `tool-calls.mdx:605` |
| 9 | `terminal/cancel` for a running terminal that does not currently advertise `cancel` is rejected | CAPABILITY `inferred:terminalCancel` | `tool-calls.mdx:587,600,602,605` |
| 10 | ...code `-32602` | ADVISORY | `tool-calls.mdx:605` |

Tier reasoning: the draft docs describe the behaviour, so they set the tier (`docs/requirements.md:53-58`). The RFD
is only secondary context, and the RFD-only cap does not apply. The docs sentence has no RFC keyword. The repo's
policy for that case is already shown by `ACP-TOOLCANCEL-204/205` (`src/tck/v2/requirements.py:3259-3293`),
`ACP-LIST-205/207` and `ACP-SESSION-204/209`:
- error versus success goes in a CAPABILITY/MANDATORY row;
- the code goes in a separate ADVISORY row (`docs/writing-tests.md:65-77`).

There is no `initialize` marker for either method, so the gate is the documentation-only `inferred:` string
(`docs/requirements.md:66-80`). The new rows can reuse the existing `inferred:toolCallCancel` /
`inferred:terminalCancel` gates.

## Details

### Spec text (quotes, at `3961af94`)

- `docs/protocol/v2/draft/tool-calls.mdx:440`: "`capabilities` is a nullable patch: omitted leaves it unchanged,
  `null` clears it, and an object replaces the whole previous value. Within it, an omitted or `null` `cancel` means
  unsupported, and `{}` advertises support. ... The Agent **SHOULD** stop advertising `cancel` once the tool call
  reaches a final status."
- `tool-calls.mdx:456`: "The Client **MUST NOT** send it unless the tool call currently advertises
  `capabilities.cancel`."
- `tool-calls.mdx:459`: "The Agent responds with `-32602` if the tool call is unknown, already final, or not
  cancellable."
- `tool-calls.mdx:587`: terminal `capabilities` has "the same shape and patch rules as on tool calls".
- `tool-calls.mdx:600`: "The Agent **SHOULD** stop advertising `cancel` once the terminal reports `exitStatus`."
- `tool-calls.mdx:602`: "The Client **MUST NOT** send it unless the terminal currently advertises
  `capabilities.cancel`."
- `tool-calls.mdx:605`: "The Agent responds with `-32602` if the terminal is unknown, has already exited, or is not
  cancellable."
- Schema descriptions `schema/v2/schema.unstable.json#/$defs/CancelToolCallRequest` and `#/$defs/CancelTerminalRequest`
  repeat both sentences word for word: "Clients MUST NOT send it unless ..." and "The Agent responds with `-32602`
  if ...".
- `docs/rfds/v2/background-work.mdx` is **Active**: it sits under `docs/docs.json:211` "Active" > v2, entry
  `rfds/v2/background-work` at `:233`.
  - `:124` and `:163`: client MUST NOT.
  - `:126`: "The Agent responds with `-32602` (Invalid params) if the tool call is unknown, already final, or not
    cancellable." `:165` is the terminal equivalent.
  - `:329` (design intent): "The Client needs to know whether the cancellation was accepted. For example, the work
    may already be finished, or may not be cancellable. A request lets the Agent reject it with `-32602`."
- The stable copy `docs/protocol/v2/tool-calls.mdx:458,603` says the same. Citations must use the draft tree.

### Wire shapes

- Request: `{"sessionId": <str>, "toolCallId": <str>, "_meta"?}`; `sessionId` and `toolCallId` are required
  (`#/$defs/CancelToolCallRequest`). The terminal request is the same with `terminalId`
  (`#/$defs/CancelTerminalRequest`).
- Cancellability signal: `ToolCallCapabilities` / `TerminalCapabilities` = `{cancel?, _meta?}`, nothing required.
  It is carried on `tool_call_update.capabilities` / `terminal_update.capabilities` with nullable-patch semantics.
  The TCK already tracks the effective value as `PatchTracker` `item.cancel`; see `_ItemProbe._live` /
  `_advertises_cancel`, `src/tck/v2/conformance/_helpers.py:2467-2489`.
- "Not cancellable" on the wire therefore means: the item is known to the client and live (tool call not
  `completed`/`failed`/`cancelled`; terminal with no object `exitStatus`), and its effective `capabilities.cancel` is
  absent or `null`. That covers both never advertised and advertised then cleared.

### Proposed rows (ids are free: TOOLCANCEL/TERMCANCEL use 201-205 today)

| Id | Tier / gate | Row text (short) | Citation |
|---|---|---|---|
| `ACP-TOOLCANCEL-206` | CAPABILITY, `inferred:toolCallCancel` | `tool_call/cancel` with the prompted session's `sessionId` and a `toolCallId` no update announced (`_tck_unknown_tool_call`) is rejected with an error, not a result. The probe breaks the client rule at :456 because :459 defines the answer. SKIPs unless a tool call advertised `cancel` during the driven turn. | `tool-calls.mdx:456,459`; `#/$defs/CancelToolCallRequest`; `background-work.mdx:126 (Active RFD)` secondary |
| `ACP-TOOLCANCEL-207` | ADVISORY | That rejection uses `-32602`. SKIPs when 206's probe was not made or not rejected. | `tool-calls.mdx:459` |
| `ACP-TOOLCANCEL-208` | CAPABILITY, `inferred:toolCallCancel` | `tool_call/cancel` for a live tool call of the prompted session whose effective `capabilities.cancel` is absent/`null` is rejected with an error. A result FAILs unless the item began advertising `cancel` before, or within `quiet_period` after, the response (race, SKIP). Same client-rule note. SKIPs unless (a) some tool call advertised `cancel` during the turn and (b) a live tool call without `cancel` was seen. | `tool-calls.mdx:440,456,459`; `#/$defs/CancelToolCallRequest` |
| `ACP-TOOLCANCEL-209` | ADVISORY | That rejection uses `-32602`. | `tool-calls.mdx:459` |
| `ACP-TERMCANCEL-206` | CAPABILITY, `inferred:terminalCancel` | unknown `terminalId` (`_tck_unknown_terminal`), as 206 | `tool-calls.mdx:602,605`; `#/$defs/CancelTerminalRequest`; `background-work.mdx:165 (Active RFD)` |
| `ACP-TERMCANCEL-207` | ADVISORY | code `-32602` | `tool-calls.mdx:605` |
| `ACP-TERMCANCEL-208` | CAPABILITY, `inferred:terminalCancel` | running terminal (no `exitStatus`) without `cancel`, as 208 | `tool-calls.mdx:587,600,602,605` |
| `ACP-TERMCANCEL-209` | ADVISORY | code `-32602` | `tool-calls.mdx:605` |

All are v2-only (`2xx`). An alternative is one rejection row and one code row per method covering both cases (4 rows).
I advise against it: an agent that is wrong in only one case would fail a row that reads as if it were wrong in
both. Separate rows keep "one defect, one row".

### Files to touch

Product:
- `src/tck/v2/requirements.py`: 8 rows next to `-204`/`-205` (around `:3259-3393`), about 160-180 LOC.
- `src/tck/v2/conformance/_helpers.py`:
  - `ItemCancelRun` (`:2436`): 4 new result fields (2 unknown, 2 not-cancellable), plus "ever advertised" flags
    per kind.
  - A `_UncancellableProbe` like `_StaleProbe` (`:2558`) that picks the first live, non-advertising item and judges
    a result against a later advertisement within `grace`.
  - The unknown-id request, sent once per kind after the main probes settle, while the process is still open.
  - Extend the `settled` condition (`:2726`).
  - About 120-170 LOC.
- `src/tck/v2/conformance/test_item_controls.py`: 8 tests plus two judge helpers like `_judge_stale_rejected` /
  `_judge_stale_code` (`:152-175`, which can probably be generalized). Rewrite the module docstring sentence at
  `:28-29` ("The other `-32602` cases ... are not probed"). About 90-120 LOC.
- `spec-tracker/maps/v2.toml`: delete the two `[[not_requirement]]` entries at `:605-608` and `:615-618`, which
  become requirements. Keep `:610-613` and `:620-623`.
- Docs:
  - `README.md:109-113`: the cancel-prompt paragraph, to note the extra requests.
  - `docs/mock-client.md:123-140`: add a bullet for the unknown-id and not-cancellable requests.
  - About 15-25 LOC.

Tests and fixtures:
- `tests/v2/test_registry.py:234-243` (id list) and `:309-310` (ADVISORY list).
- `tests/v2/test_cli.py`:
  - add the ids to the CAPABILITY set (around `:180-187`) and the ADVISORY set (around `:233-234`);
  - new sets, e.g. `_UNKNOWN_CANCEL_IDS` and `_UNCANCELLABLE_CANCEL_IDS`, added to `_ITEM_CANCEL_IDS` (`:309-311`).
    That flows into the whole-suite skip sets at `:397`, `:628` and `:2906`; `:747` (`conforming_full`) needs
    them added explicitly or left out depending on the fixture choice below;
  - update every item-cancel expectation (`:4250-4380`; details under Testability);
  - add a parametrized defect test for the new fixtures.
  - About 100-150 LOC.
- `tests/fixtures/agents/v2/_base.py`: a way to emit a live tool call and a live terminal with **no**
  `capabilities` during a `__hang__` turn, finalized in `_finish_cancellable_work` (`:1245`). Use a distinct id
  prefix (e.g. `tool-fixed-`/`term-fixed-`) so the `startswith("tool-live-")` overrides in the defect fixtures keep
  working. The existing `_handle_tool_call_cancel` / `_handle_terminal_cancel` (`:1192-1227`) already answer
  `-32602` for any id not in `_open_*`, so unknown and not-cancellable ids need no handler change. About 30-45 LOC.
- New defect fixtures, one defect each, 25-40 LOC each, following `accepts_cancel_for_final_tool_call.py` and
  `final_tool_call_cancel_wrong_code.py`:
  1. `accepts_cancel_for_unknown_tool_call.py`: FAIL `TOOLCANCEL-206`, `-207` SKIP
  2. `accepts_cancel_for_unknown_terminal.py`: FAIL `TERMCANCEL-206`
  3. `unknown_tool_call_cancel_wrong_code.py` (`-32603`): FAIL `TOOLCANCEL-207`
  4. `unknown_terminal_cancel_wrong_code.py`: FAIL `TERMCANCEL-207`
  5. `accepts_cancel_for_uncancellable_tool_call.py`: FAIL `TOOLCANCEL-208`
  6. `accepts_cancel_for_uncancellable_terminal.py`: FAIL `TERMCANCEL-208`
  7. `uncancellable_tool_call_cancel_wrong_code.py`: FAIL `TOOLCANCEL-209`
  8. `uncancellable_terminal_cancel_wrong_code.py`: FAIL `TERMCANCEL-209`
  9. (optional, conforming) `advertises_cancel_as_request_crosses.py`: the "uncancellable" item starts advertising
     `cancel` just before the agent reads the request, then accepts; `-208` SKIPs as a race.
- Existing fixtures that change:
  - `tool_call_cancel_errors.py`: answers `-32603` to **every** `tool_call/cancel` (`:19-20`), so it would also
    FAIL `TOOLCANCEL-207` (and `-209`). Restrict the `-32603` to `tool-live-` ids to keep one defect.
  - `cancel_missing_after_completion.py`: answers `-32601`. Under the gate below it would FAIL the ADVISORY
    `-207`/`TERMCANCEL-207`. Either update the expectation in
    `test_missing_cancel_methods_are_not_hidden_by_the_race_excuse` (`test_cli.py:4320-4333`) or restrict the
    fixture.
  - `terminal_cancel_errors.py`, `withdraws_cancel_on_request.py` and `finalizes_after_rejecting_cancel.py` answer
    `-32602` to everything. They PASS the new rows, so only their expectations move.

## Testability notes

- **Unknown id** (206/207): deterministic and safe.
  - Send `{"sessionId": <prompted session>, "toolCallId": "_tck_unknown_tool_call"}`. Assert the id is not in the
    tracker first.
  - Use the live prompted session, so the agent cannot rightly answer `-32002` for an unknown session
    (`docs/protocol/v2/draft/error.mdx:54`, a MUST that applies to session-scoped requests).
  - No race is possible.
  - Send it inside the cached driven run while the agent is open: `drive_item_cancel` after settling, or
    `_item_cancel_run` (`test_item_controls.py:52-71`) before the `async with` exits. That way all rows share the
    one turn, like the existing eight.
  - Post-idle agent requests must still be answered the way `answer_post_turn_requests` does (`_helpers.py:2613`).
- **Gate:** probe only when the agent showed the feature. If it never advertises `cancel`, it may not implement the
  method, and then `error.mdx:44` makes `-32601` the MUST answer. That conflicts with `:459` (see Discrepancies), so
  the spec does not settle what the answer is, and the probe rules forbid sending (`docs/writing-tests.md:61-63`).
  - Recommended gate: "some item of that kind advertised `cancel` at any point in the driven turn", tracked as an
    "ever advertised" flag.
  - Do **not** reuse `ItemCancel.outcome != "none"` ("advertised while live"). It is nondeterministic for
    `completes_before_cancel.py` (`test_cli.py:4296`; its docstring says the driver "usually" sees the final update
    first), which would make that test flaky.
  - With the recommended gate, `completes_before_cancel.py` deterministically PASSes 206/207, and its "all
    SKIPPED" assertion must change.
- **Not cancellable** (208/209):
  - Candidate: the first item that is live and not advertising `cancel`.
  - Conforming: an error (and for 209, `-32602`).
  - Non-conforming: a result, or no response within `timeout / 2`. That is the same bar as `-204`
    (`test_item_controls.py:152-165`).
  - Race: the agent may start advertising `cancel` while the request is in flight. A result that comes with an
    advertisement on that item before the response, or within `quiet_period` after it, is legitimate, so SKIP. This
    mirrors the `-32602` grace in `_ItemProbe.step` (`_helpers.py:2528-2540`).
  - An item that turns final around the request gets `-32602` either way, so it causes no judging problem.
- **Ordering and safety:**
  - Send the not-cancellable request only while the kind's main probe has nothing in flight, as `_StaleProbe` does
    (`_helpers.py:2595`).
  - If a defective agent accepts and cancels a foreground tool call, the turn may end before the main probe finds
    its cancellable item. The main rows then SKIP rather than false-PASS, and 208 FAILs.
  - Real work is touched only inside the TCK's throwaway session, during a turn the TCK cancels anyway.
  - Background terminals survive `session/cancel` (`background-work.mdx:333`), so stopping one is effectively
    cleanup.
- **How often it fires:**
  - Against real agents, 208 fires often: most tool calls carry no `cancel`, so any agent that advertises it on some
    item will usually also have a live one without it.
  - 206 fires whenever the gate holds.
  - With the default essay prompt, nothing advertises `cancel` and everything SKIPs, as today.
- **Fixture coverage (PASS side):** decide whether `conforming_full.py` emits the live non-cancellable items.
  - If it does, 208/209 PASS there, and the `:747` skip set and any `__hang__` whole-suite expectations must be
    re-checked.
  - If not, a dedicated conforming fixture covers PASS. Either way, 206/207 PASS on `conforming_full.py` and
    `keeps_cancel_after_final.py` with no fixture change.
- **Expectations that move in `test_cli.py`:**
  - `test_cancellable_items_pass_the_cancel_rows` (`:4249`) and
    `test_agent_that_keeps_advertising_cancel_gets_a_further_request` (`:4257`).
  - `test_legitimate_invalid_params_is_not_a_rejection` (`:4296-4317`): all SKIPPED becomes the unknown rows PASS.
  - `test_items_that_finish_first_...` (`:4290`).
  - `test_missing_cancel_methods_...` (`:4320`).
  - `test_item_cancel_defect_fails_its_row_only` (`:4355-4380`) and `test_already_final_cancel_defect_...`
    (`:4262-4283`): new default statuses.
  - `test_long_streaming_turn_...` (`:4348`) stays all SKIPPED, because nothing advertises.
- **Unobservable:** whether an agent that accepted a not-cancellable request actually stopped anything does not
  matter. The result alone is the defect.

## Discrepancies

1. **`-32601` vs `-32602` for an agent with no cancel support.** `docs/protocol/v2/draft/error.mdx:44`: "A
   receiver that does not implement a method, or receives a capability-gated method it did not advertise,
   **MUST** respond with `-32601`." `tool-calls.mdx:459,605` says `-32602` for "unknown ... or not cancellable".
   - The spec does not say whether an agent that never advertises `cancel` "implements" `tool_call/cancel`.
   - The Rust SDK chose `-32602`. An initialized v2 agent with no handler answers both methods `-32602`:
     `src/agent-client-protocol/src/role/acp.rs:49-51` and `:358-380` (`unhandled_v2_entity_cancel`: "the spec
     answers a request for an unknown or non-cancellable one with `-32602` (Invalid params), not `-32601`"), and
     `:424-427`, at acp-rust-sdk `6a4a95c`, added in `d13e36b` "default v2 entity cancel to -32602 (#482)".
   - The Python SDK at `4fed584` has no `tool_call/cancel` / `terminal/cancel` handling (`rg` finds nothing).
   - The proposed gate sidesteps the conflict by not probing agents that never advertise `cancel`.
   - The TCK's own fixtures answer `-32601` without `cancellable_work` (`_base.py:113`). That is consistent with
     `error.mdx:44`, but not with the Rust SDK's choice.
2. **`-32002` vs `-32602` for an unknown id.** `error.mdx:35` defines `-32002` as "A referenced resource, such as a
   session, does not exist." An agent could plausibly answer `-32002` for an unknown `toolCallId`. The specific
   sentence `tool-calls.mdx:459` names `-32602`. Only the ADVISORY code row would flag it, so no verdict impact.
3. **Normative strength.** Docs, schema and RFD agree on the content. None uses a keyword on the agent's answer;
   only the client's MUST NOT is keyworded. No conflict, but that is why the code rows are ADVISORY.

## Open questions

1. **Gate definition.** "Advertised `cancel` at any point in the turn" (recommended, deterministic) or "advertised
   while live" (the existing 201 gate, racy for `completes_before_cancel.py`)? This needs an orchestrator or
   programmer decision.
2. **PASS-side fixture.** Should `conforming_full.py` emit live non-cancellable items, which touches its
   whole-suite expectations, or should a new dedicated conforming fixture do it?
3. **Scope split.** Ship the unknown-id rows (S) now and the not-cancellable rows (M) separately? The unknown-id
   half has no race and no fixture-emission change.
4. **Unknown-session case (adjacent, not in scope).** `tool_call/cancel` with an unknown `sessionId` should get
   `-32002` with `data.sessionId` under `error.mdx:54` (a MUST). That would be another probe. Route it separately
   if wanted.
5. **Child-session variant.** A not-cancellable child item with the child's `sessionId`, in
   `test_subagent_controls.py`, is not proposed. It adds little over 208.
6. Fixtures should probably stay as they are (`-32601` without `cancellable_work`) even though the Rust SDK
   answers `-32602`. Nothing in the proposed rows depends on that choice.

## Risks

- **Fixture fallout.** Every `cancellable_work` fixture now also gets the unknown-id requests. Fixtures that
  override `_handle_*_cancel` wholesale will trip the new ADVISORY code rows:
  - known in `test_item_controls` scope: `tool_call_cancel_errors.py` and `cancel_missing_after_completion.py`;
  - possibly in whole-suite runs of `child_tool_call_cancel_errors.py` and siblings, if their prompted session
    advertises `cancel` (not verified).
  - The programmer must run the full `uv run pytest` and reconcile every exact FAIL set.
- **Driver complexity.** `drive_item_cancel` is already intricate: `settled` logic, grace windows, post-idle reads.
  A third probe class adds another path that can stall `settled` or race with `session/cancel`. Keep it behind
  "main probe not in flight" and include it in `settled`.
- **Tier challenge.** CAPABILITY for a declarative docs sentence follows repo precedent (`ACP-TOOLCANCEL-204`,
  `ACP-LIST-205`), but a reviewer could argue ADVISORY. Keep the encoding consistent with `-204`.
- **CLI test runtime.** Each new defect fixture adds a `__hang__` run (about 1-3 s at `--timeout 1`); 8 fixtures
  add roughly 10-25 s of parallel CI work.

## Complexity estimate

- **Unknown-id only (4 rows): S**, about 250-350 LOC (rows about 80, helper about 40, tests about 50, 4 fixtures
  about 120, test_cli/registry about 50, ledger/docs about 15). No race logic, and the base fixture needs no change.
- **Not-cancellable only (4 rows): M**, about 450-550 LOC (rows about 80, new probe about 100, tests about 50,
  `_base.py` about 40, 4-5 fixtures about 150, test_cli about 80, docs about 10). Most of the risk is in the race
  rule and the expectation churn.
- **Both: M**, about 700-900 LOC across about 6 product/doc files and about 12-14 test/fixture files.

It fits one PR with a few other small follow-ups if those stay out of `drive_item_cancel`, `test_item_controls.py`
and the item-cancel section of `tests/v2/test_cli.py`. Pairing it with another medium follow-up in that area would
make the PR hard to review. In that case, ship only the unknown-id half alongside.
