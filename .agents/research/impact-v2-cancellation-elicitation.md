# Impact (v2): `cancellation.mdx` (core) and `elicitation.mdx`, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read with `git show 3ea94133:<path>`;
the checkout's HEAD is `6ace4f6a`, but `git diff 3ea94133 HEAD` is empty for both docs and `prompt-lifecycle.mdx`),
diffed against `3961af94`. Read in full: `docs/protocol/v2/draft/cancellation.mdx`, `docs/protocol/v2/draft/elicitation.mdx`.
Checked dependencies: `prompt-lifecycle.mdx:184,1446-1467`, `session-setup.mdx:474-480`, `tool-calls.mdx:326`,
`subagents.mdx:411-420`, `schema/v2/schema.unstable.json` descriptions (`CancelSessionNotification`,
`RequestPermissionRequest`, `CancelledPermissionOutcome`, `CreateElicitationRequest`), `docs/docs.json`
(`rfds/request-cancellation` is **Completed**). TCK: `src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`,
`src/tck/v2/conformance/test_cancel.py`, `_helpers.py` (`run_prompt` hold mode), `tests/v2/test_registry.py`, `tests/v2/test_cli.py`.
Reference SDKs not consulted: the changed rules are explicit, and the remaining ambiguity (which requests "belong" to
the cancelled work) depends on how each agent is built, not on SDK behaviour.
**Confidence:** high for line maps and the tier change; medium for the elicitation coverage recommendation (a design choice).

## Hunks (both docs)

- `cancellation.mdx` +31-32 (new): Client **SHOULD** dismiss and answer `cancelled`/`cancel` on `$/cancel_request` for an
  unanswered permission or elicitation request. Applies to the client, so it gets no row and no ledger entry
  (`docs/requirements.md`, ledger is "Agent-side only").
- `cancellation.mdx:42` (was :40): **SHOULD -> MUST** cancel each pending permission request of the cancelled foreground
  work with `$/cancel_request`; new sentence "The Agent decides which requests belong to that work."
- `elicitation.mdx:225-228` (was 225-227): **SHOULD -> MUST** cancel a pending elicitation with `$/cancel_request` "when the
  Agent stops waiting for [it] because the work that needed it was cancelled"; "The Agent decides which elicitations the
  cancelled work no longer needs." `:231-233` new client SHOULD (dismiss, answer `cancel`), which binds the client.
- Same MUST in the fan-out: `prompt-lifecycle.mdx:1452` (was :1177, SHOULD), `subagents.mdx:417` (new doc), schema
  `CancelSessionNotification` and `RequestPermissionRequest` descriptions now say "MUST cancel ... with `$/cancel_request`".

Line shift: `cancellation.mdx` lines >= 31 at the base are +2; `elicitation.mdx` lines >= 228 at the base are +3 (< 225 unchanged).

## `docs/protocol/v2/draft/cancellation.mdx`

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-PROMPT-207 | citation-only | `cancellation.mdx:61` (was :59) | |
| ACP-CANCEL-001 | citation-only | `cancellation.mdx:43-46` (was :41-44) | |
| ACP-CANCEL-203 | citation-only | `cancellation.mdx:61` (was :59) | |
| ACP-CANCEL-209 | citation-only | `cancellation.mdx:20,33,42-45` (was :20,31,40-43); `prompt-lifecycle.mdx:1452` (was :1177, the prompt-lifecycle researcher remaps the other lines) | Text still correct: MUST stop waiting is unchanged. The TCK's answer of `cancelled` after a `$/cancel_request` now matches the new client SHOULD (`cancellation.mdx:31`). Optional: cite :31 for it. Test docstring `test_cancel.py:409` "cancellation.mdx:31" -> `:33`. |
| ACP-JSONRPC-006 | unchanged | `cancellation.mdx:24` | |
| ACP-CANCEL-211 | unchanged | `cancellation.mdx:22,24` | |
| ACP-JSONRPC-007 | citation-only | `cancellation.mdx:20,22,24,26-29,61` (was ...,59) | docstring refs `test_cancel.py:564,567` (:20,24 / :22) unchanged |
| **ACP-CANCEL-213** | **changed tier** | `prompt-lifecycle.mdx:1452`; `cancellation.mdx:42,65` (was :40,63); `schema/v2/schema.unstable.json#/$defs/CancelRequestNotification` (optionally add `#/$defs/CancelSessionNotification`, whose description now states the MUST) | SHOULD -> MUST in the docs (not RFD-only), so ADVISORY -> **CAPABILITY, `capabilities.session`**, the same gate as ACP-CANCEL-209 and ACP-CLOSE-205. See "Changed row" below. |
| ACP-INFO-CANCEL-201 | citation-only | `cancellation.mdx:45-46` (was :43-44) | |
| ACP-CANCEL-214 | not citing this doc | n/a | The brief says -214 cites these lines, but it cites only `prompt-lifecycle.mdx:384,1173` and `CancelSessionNotification`, so this doc's change does not affect it. The prompt-lifecycle researcher owns its line remap. |
| ledger `cancellation.mdx:12` (match only the sender's requests) | unchanged | `cancellation.mdx:12` | |
| ledger `cancellation.mdx:31` (sender that stops waiting SHOULD send `$/cancel_request`) | citation-only | `cancellation.mdx:33` | Statement still true in general. Reason still holds ("beyond the permission-request cases ACP-CANCEL-213 and ACP-CLOSE-205 observe"). It does not rest on a TCK choice. |
| ledger `cancellation.mdx:54,56` (internal cancellation) | citation-only | `cancellation.mdx:56,58` | |
| ledger `cancellation.mdx:40,41; prompt-lifecycle.mdx:...` (ignore late answers) | citation-only | `cancellation.mdx:42,43` (prompt-lifecycle part: target :1456-1458, prompt-lifecycle researcher) | Reason's "the client rule" is now stated explicitly at `cancellation.mdx:31`; optionally cite it. |
| `[[core_doc]]` entry for this path | unchanged | n/a | reason text still accurate |

## `docs/protocol/v2/draft/elicitation.mdx`

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-CLIENTCAP-003 | unchanged | `elicitation.mdx:56-57,59` | |
| ledger `:54` (MCP capability not copied) | unchanged | `:54` | already a "Deferred" entry that names a real blocker |
| ledger `:56-57` | unchanged | `:56-57` | |
| ledger `:67-74,76-77` | unchanged | `:67-74,76-77` | |
| ledger `:157-163,186-187,255-256,268` | citation-only | `:157-163,186-187,258-259,271` | |
| ledger `:197` | unchanged | `:197` | |
| ledger `:211-216` | unchanged | `:211-216` | |
| **ledger `:225-227,233; session-setup.mdx:391`** | **changed text** | `elicitation.mdx:225-228,236; session-setup.mdx:476` | New statement: "When the Agent stops waiting for a pending elicitation because the work that needed it was cancelled, it MUST cancel that request with `$/cancel_request` (the Agent decides which elicitations the cancelled work no longer needs), and before responding to `session/close` it MUST cancel every pending elicitation scoped to that session." The reason must name the real blocker; see Decision 2. |

## Changed row: ACP-CANCEL-213

- **Tier:** CAPABILITY, `capability="capabilities.session"`. The test already carries `@pytest.mark.capability("capabilities.session")`.
- **Text (proposed):** "When `session/cancel` cancels work blocked on the agent's own pending `session/request_permission` (held
  unanswered, as in `ACP-CANCEL-209`), the agent MUST withdraw that request with `$/cancel_request` naming its id, before or
  shortly after the cancelled idle (the TCK holds it that long before answering it itself). Same SKIPs as `ACP-CANCEL-209`."
- **Test:** no logic change. `run_prompt` already waits `confirm_window` after the idle for a trailing `$/cancel_request`
  before it answers `turn_end` (`_helpers.py:2091-2100`). After the TCK answers, the request is no longer pending, and the
  MUST covers only pending requests (`prompt-lifecycle.mdx:1452` "pending ... requests"). So the bounded window is principled,
  not arbitrary. The spec sets no ordering against the idle (`prompt-lifecycle.mdx:1463-1464`: cancellation can finish
  without answers).
- **Collateral edits:** `test_cancel.py:15` and the `:438` docstring ("ACP-CANCEL-213 is ADVISORY"); `tests/v2/test_registry.py`
  ADVISORY pin (`:294`) and the CAPABILITY set (`:134` is in a list that should be checked); `tests/v2/test_cli.py:2176`
  `test_cancel_without_cancel_request_fails_advisory_cancel_213_only` (rename it; the run is now non-conformant, so assert
  `returncode != 0` like `:2188`). The expected-SKIP lists at `test_cli.py:216,415,652,768` do not depend on the tier.
- **Residual false-FAIL risk ("The Agent decides"):** the TCK infers membership. A held request counts as foreground when
  its `subject` is not in the latest `background` list (`_helpers.py:1954-1957`). If an agent's request belongs to
  *unlisted* background activity, the agent may legitimately leave it pending and FAIL here. The risk is narrow:
  `prompt-lifecycle.mdx:196` says user-visible background work is represented as a listed tool call, and a turn that ended
  `cancelled` has no other foreground work the request could belong to. Recommend recording this in the row text or
  docstring instead of adding a SKIP.

## New requirements

None are required. One is optional (Decision 2): a SKIPpable row for the elicitation MUST.

- Provisional `ACP-CANCEL-2xx`: "When `session/cancel` cancels work blocked on the agent's own pending session-scoped
  `elicitation/create` (held unanswered), the agent MUST withdraw it with `$/cancel_request` naming its id, before or
  shortly after the cancelled idle." CAPABILITY, `capabilities.session`. Citation: `elicitation.mdx:225-228`;
  `cancellation.mdx:42-45`; `schema/v2/schema.unstable.json#/$defs/CancelRequestNotification`.
  - Test: mirror ACP-CANCEL-213. On a dedicated connection whose mock client advertises
    `capabilities.elicitation: {"form": {}, "url": {}}`, prompt, hold the first session-scoped `elicitation/create` for that
    session, send `session/cancel`, then look for a `$/cancel_request` naming it until idle + `confirm_window`. Answer it
    `{"action": "cancel"}` on withdrawal or at turn end. SKIP when no elicitation was pending at cancel, when the turn never
    ends, or when the agent does not advertise `capabilities.session`. A companion "stops waiting" check like ACP-CANCEL-209
    has no explicit elicitation MUST, only `prompt-lifecycle.mdx:1463-1464` "can finish without receiving answers", so
    do not add one.
  - Harness needs: (1) a mock-client option that advertises elicitation modes per connection (today `capabilities: {}`, see
    `test_client_capabilities.py:8`); (2) `run_prompt` hold mode generalised from `session/request_permission` to
    `elicitation/create`, with a `cancel` answer; (3) a trigger. No prompt reliably makes an agent elicit. The realistic
    route is the TCK's stdio MCP stub issuing an MCP elicitation during a tool call, which an agent that forwards
    elicitation turns into ACP `elicitation/create` (this also unblocks ledger `:54`). The fallback is a user-supplied
    prompt option. Expect SKIP on most agents.
  - The `session/close` half (cancel every pending scoped elicitation before the close response, `session-setup.mdx:476`)
    could become an ACP-CLOSE-205 analogue on the same harness.

## New ledger entries

None. The elicitation MUST stays in the existing (restated) entry above unless Decision 2 picks the row. Not ledgered:
the new client SHOULDs (`cancellation.mdx:31`, `elicitation.mdx:231-233`, `session-setup.mdx:476` "Clients SHOULD
dismiss"), because they bind the client. The "Agent decides which requests belong" clauses are discretion, not obligations.

## Existing ledger reasons resting on a TCK choice (flag)

- `spec-tracker/maps/v2.toml:358` section comment "(coverage deferred: the TCK never advertises an elicitation mode)" is
  exactly the forbidden form. The entries under it mostly name a real blocker ("an agent cannot be made to elicit"), but
  that blocker applies equally to permission requests, which the TCK covers with SKIPpable rows. For `:56-57`, `:67-77`,
  `:197`, `:211-216` and `:225-228`, the honest reason is "Deferred: needs a mock client advertising elicitation modes and
  holding `elicitation/create`, plus a trigger (an MCP-stub-forwarded elicitation); not built". Recommend rewording the
  comment and those reasons to name that blocker. Leave `:157-163,...` as is ("Not observable", semantic/out-of-band).

## Discrepancies

1. **Schema vs docs (elicitation):** `CreateElicitationRequest` description at the target still says "Agents SHOULD cancel
   pending elicitations no longer needed by cancelled work" (`schema/v2/schema.unstable.json#/$defs/CreateElicitationRequest`;
   source `agent-client-protocol-schema/src/v2/elicitation.rs:1584`, `docs/protocol/v2/draft/schema.mdx:2041`), while
   `elicitation.mdx:225-228` says MUST. The permission descriptions were updated to MUST, but this one was missed upstream.
   Per docs precedence, the docs govern (MUST). Record it in the row text or ledger statement if the TCK cites the schema.
2. **Minor:** `cancellation.mdx:14` "Cancellation remains optional as it might not be implementable" sits beside the new
   MUST at :42. Read together, :14 concerns *reacting* to a received `$/cancel_request` (:16-20), and sending one is
   always implementable, so they do not conflict for the TCK's purposes.

## Decisions for the user

1. **ACP-CANCEL-213 tier:** ADVISORY -> CAPABILITY on `capabilities.session` (recommended, consistent with -209 and
   CLOSE-205), or MANDATORY with no gate. Recommend CAPABILITY: the rule only exists for agents that run prompt turns.
2. **Elicitation MUST coverage:** (a) keep it in the ledger, with the restated statement and a "Deferred" reason that names
   the harness blocker (recommended for this spec update: building elicitation support is a separate feature and would
   SKIP on most agents), or (b) add the SKIPpable `ACP-CANCEL-2xx` row and harness work now. If (a), file the row and the
   MCP-stub trigger as a follow-up.
3. **"The Agent decides" clause:** accept the narrow false-FAIL risk on -213 for requests tied to unlisted background
   activity, and document it in the row (recommended). The alternative, SKIP whenever the agent stays idle with the request
   still pending, would turn the row into a no-op.
4. **Reword the elicitation ledger section comment and its "Deferred" reasons** (`v2.toml:358` ff.) so they no longer rest
   on "the TCK never advertises an elicitation mode" (recommended, even if Decision 2 is (a)).

## Open questions (route elsewhere)

- `subagents.mdx:417` restates the MUST per session, including descendants' requests. That belongs to the subagents researcher.
- `prompt-lifecycle.mdx:1452` also carries this MUST and is cited by -209 and -213. The prompt-lifecycle researcher should
  apply the same remap and check that it does not propose a conflicting tier.
