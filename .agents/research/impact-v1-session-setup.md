# Impact research (v1): `session-setup.mdx` and `session-modes.mdx`, `3961af94` -> `3ea94133`

**Sources checked:**
- agent-client-protocol, read by ref from `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`. Base `3961af94`, target `3ea94133`. That checkout's working tree is at `6ace4f6a`, so every read used `git show 3ea94133:<path>`. Files: `docs/protocol/v1/draft/session-setup.mdx` and `session-modes.mdx` in full; dependencies `prompt-turn.mdx:360-425,577-709`, `session-config-options.mdx:473-568`, `error.mdx:51-70`; `schema/v1/schema.unstable.json` `$defs` `NewSessionRequest`, `LoadSessionRequest`, `ResumeSessionRequest`, `ForkSessionRequest`, `SessionOptionsCapabilities`, `SessionOptionsRequest`/`Response`, `InitialSessionConfigOption`, `ClientSessionCapabilities`, `CursorUpdate`, `CursorId`; `docs/docs.json` for RFD stages.
- acp-tck: `src/tck/v1/requirements.py`, `spec-tracker/maps/v1.toml`, `src/tck/v1/conformance/test_session_capabilities.py`, `_helpers.py`, `test_client_capabilities.py`.
- acp-rust-sdk @ `6a4a95ca` (schema crate `=1.18.0`). It only has type and routing plumbing for `session/options`, `PromptSuggestionsUpdate` and cursors (`src/agent-client-protocol/src/schema/client_to_agent/requests.rs:24,91-92`, `tests/schema_1_18.rs:73`). It has no runtime behaviour for replay or for initial values, so it settles nothing here. The Python SDK was not consulted: it is the same kind of library, and no rule below depends on runtime behaviour the spec leaves implicit.

**Confidence:** high for the classification and line re-mapping (the doc diff is two pure insertions). Medium for the new cursor-replay rows: what counts as "the same position" across loads is my interpretation.

## Diff summary

`session-modes.mdx` is unchanged (empty diff). `session-setup.mdx` has two insertions and nothing else:
- `+150-157` (after base line 149), in "Loading a session":
  - prompt suggestions **SHOULD NOT** be replayed;
  - for cursors, the Agent **SHOULD** replay a `cursor_update` for each cursor it still accepts, and **SHOULD** keep `cursorId`s stable across loads;
  - the Client **SHOULD** rebuild its cursors;
  - message IDs may change across a load.
- `+454-457` (after base line 444): the new section "Initial config option values (unstable)". It is a summary and has no RFC keywords.

Line map, base -> target: lines `<=149` keep their number; lines `150-444` move by `+9`; lines `>=445` move by `+13`.

The intro (6-10), "Session ID" (458-468) and "Working directory" (470-487) are unchanged in text. "Unknown sessions" is linked from `session-setup.mdx:359` and changed only in `error.mdx`: `+57` adds the child-session rule, which belongs to the error/subagents researcher. `cursorId` on `session/fork` is specified in `prompt-turn.mdx:676-701` and the `ForkSessionRequest` schema, not in my docs. See Open questions.

## Table: `docs/protocol/v1/draft/session-setup.mdx`

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-SESSION-001 | unchanged | `session-setup.mdx:73` | |
| ACP-SESSION-002 | unchanged | `session-setup.mdx:73` | |
| ACP-SESSION-003 | citation-only | `session-setup.mdx:493,501-526` | was 480,488-513 |
| ACP-SESSION-004 | citation-only | `session-setup.mdx:663` | was 650 |
| ACP-SESSION-006 | citation-only | `session-setup.mdx:673` | was 660 |
| ACP-LOAD-001 | citation-only | `session-setup.mdx:106,110-210` (`{}` result example at 201-210) | was 106,110-201 (192-201). The range now also covers the new 150-157 text, which is why the inventory flagged a hunk overlap. The rule is unchanged. `LoadSessionRequest` gains an optional `configOptions`, which the test does not send. `LoadSessionResponse` changes only through `SessionConfigOptionCategory` (+`speed`), which re-vendoring picks up. |
| ACP-LOAD-002 | citation-only | `session-setup.mdx:136-142,201-202` | was 136-142,192-193. Do **not** widen `HISTORY_KINDS` to `cursor_update` (see Decisions D3). |
| ACP-LOAD-003 | citation-only | `session-setup.mdx:204-210` | was 195-201 |
| ACP-RESUME-001 | citation-only | `session-setup.mdx:249-254,276-287` | was 240-245,267-278 |
| ACP-RESUME-002 | citation-only | `session-setup.mdx:276-279` | was 267-270 |
| ACP-CLOSE-001 | citation-only | `session-setup.mdx:338-353` | was 329-344 |
| ACP-CLOSE-002 | citation-only (this doc's part) | `session-setup.mdx:342-344` | was 333-335. The row's `prompt-turn.mdx:645,652,656` part is the prompt-turn researcher's to re-map (prompt-turn shifted). |
| ACP-CLOSE-003 | citation-only | `session-setup.mdx:356-359`; `error.mdx:55` is unchanged | was 347-350 |
| ACP-ADDDIRS-001 | citation-only | `session-setup.mdx:363-392` | was 354-383 |
| ACP-SYSPROMPT-001 | citation-only | `session-setup.mdx:423,427` | was 414,418 |
| ACP-SYSPROMPT-002 | citation-only | `session-setup.mdx:424,431` | was 415,422 |
| ACP-SYSPROMPT-003 | citation-only | `session-setup.mdx:427,431` | was 418,422 |
| ACP-AUTH-003 | unchanged (this doc's part) | `session-setup.mdx:10` | |
| ACP-AUTH-005 | unchanged (this doc's part) | `session-setup.mdx:10` | |
| ACP-CLIENTCAP-005 | unchanged (this doc's part) | `session-setup.mdx:139-142` | |
| ledger `session-setup.mdx:473-474` | citation-only | `session-setup.mdx:486-487` | The reason (unobservable) does not rest on a TCK choice. Keep it. |
| ledger `session-setup.mdx:658` | citation-only | `session-setup.mdx:671` | The reason (indistinguishable) is fine. |
| ledger `session-setup.mdx:660` | citation-only | `session-setup.mdx:673` | The reason (unobservable) is fine. |
| ledger `session-setup.mdx:661` | citation-only | `session-setup.mdx:674` | Already marked "Deferred", and it names a real blocker (no HTTP MCP stub). It complies with the rule. |
| core_doc `session-setup.mdx` sections `(intro)`, `Session ID`, `Working directory` | unchanged | intro 6-10, Session ID 458-468, Working directory 470-487 | The section names and text are the same. |

## Table: `docs/protocol/v1/draft/session-modes.mdx`

| id | classification | target citation | note |
|---|---|---|---|
| ACP-MODES-001 | unchanged | `session-modes.mdx:17,49-75` | The doc and `SessionModeState`/`SessionMode` are unchanged. |
| ACP-MODES-002 | unchanged | `session-modes.mdx:83-122` (`currentModeId` at 118) | The `SetSessionMode*` and `CurrentModeUpdate` defs are unchanged. |

No ledger entries cite `session-modes.mdx`, and the target text introduces none.

## New requirements

All tiers here come from the docs. The related RFDs are all **Draft** at the target (`rfds/session-options`, `rfds/session-cursors`, `rfds/prompt-suggestions`, `rfds/session-fork`), so they are neither needed nor cited.

1. **`ACP-LOAD-0xx` (provisional): prompt suggestions not replayed.**
   - **Text:** the Agent does not send `prompt_suggestions_update` for the session inside the `session/load` exchange (before the load response). One sent after the response is allowed.
   - **Tier and gate:** ADVISORY, `capability=None`. The test is gated by `@pytest.mark.capability("agentCapabilities.loadSession", boolean=True)`, the same pattern as ACP-LOAD-003.
   - **Citation:** `session-setup.mdx:150`; `prompt-turn.mdx:425` (the same SHOULD NOT, restated).
   - **Test:** connect with `clientCapabilities: {session: {promptSuggestions: {}}}`. Run `session/new` and one prompt turn, then wait a quiet period, because suggestions usually arrive after the prompt response (`prompt-turn.mdx:415`). If no `prompt_suggestions_update` was seen live, SKIP with "agent sent no prompt suggestions" (D2). Otherwise send `session/load` on the same connection and FAIL if any `prompt_suggestions_update` for the session appears before the response.
   - **Harness:** none. `connected_agent(client_capabilities=...)` already exists.
   - **Dedupe:** the prompt-turn researcher may propose the same rule from `:425`. There should be one row, citing both lines.

2. **`ACP-LOAD-0xx` (provisional): live cursors are replayed.**
   - **Text:** every `cursorId` the Agent announced live on the session is replayed as a `cursor_update` inside the `session/load` exchange, carrying `anchor`, when both of these hold:
     - its last update had non-empty `capabilities`;
     - it was not cleared before the load.
   - **Tier and gate:** ADVISORY, gated as in row 1.
   - **Citation:** `session-setup.mdx:152,154`; `prompt-turn.mdx:703-709` (load does not invalidate a cursor; Agents SHOULD accept a cursor while they retain its history and SHOULD clear its capabilities when they stop).
   - **Test:**
     - connect with `clientCapabilities: {session: {cursors: {}}}`;
     - run `session/new` and two prompt turns (the first prompt of a session has no cursor position, `prompt-turn.mdx:663`);
     - wait a quiet period, then record live cursor ids and capabilities, applying patch semantics;
     - SKIP when no cursor has non-empty capabilities;
     - `session/load`, and check that each such id appears in a replayed `cursor_update` with a non-null `anchor`.
   - **Harness:** none beyond a small helper that folds `cursor_update` patches.
   - **Caveat:** whether the Agent "still accepts" a cursor is internal to it. The row treats "the Agent retained and replayed the history" plus "the cursor was never cleared" as "still accepts". That reading comes from combining `:154` with `prompt-turn.mdx:705-709`. See D1.

3. **`ACP-LOAD-0xx` (provisional): stable cursor IDs across loads.**
   - **Text:** two `session/load`s of the same session replay the same `cursorId` for the same position.
   - **Tier and gate:** ADVISORY, gated as in row 1.
   - **Citation:** `session-setup.mdx:155`.
   - **Test:** same setup as row 2, then load twice. Key each replayed cursor by (`anchor.type`, `anchor.position`, ordinal of the anchored entity among the replayed entities of that type). Do not use the entity ID, because message IDs may change across a load (`:157`). FAIL if any key maps to a different `cursorId` in the two loads. SKIP when the first load replays no cursor.
   - **Harness:** none.

4. **`ACP-OPTIONS-2xx` (provisional): setup accepts initial `configOptions`.**
   - **Text:** when `sessionCapabilities.options` is advertised, `session/new` with a `configOptions` list succeeds with a schema-valid response that includes `configOptions`. The same holds for `session/load` and `session/resume` of an existing session, each also gated on its own capability.
   - **Tier and gate:** CAPABILITY, `capability="agentCapabilities.sessionCapabilities.options"`.
   - **Citation:** `session-setup.mdx:456`; `session-config-options.mdx:475,541,559,566`; `schema/v1/schema.unstable.json#/$defs/SessionOptionsCapabilities` ("`{}` means the agent ... accepts initial config option values on session setup requests"); `#/$defs/NewSessionRequest/properties/configOptions`; `#/$defs/InitialSessionConfigOption`.
   - **Test:**
     - take a `select` option and an allowed non-current value from a plain `session/new` response, or from `session/options`;
     - send it as `{configId, value}` (no `type: "boolean"` entries, because the TCK does not advertise `sessionCapabilities.configOptions.boolean`);
     - assert success and schema validity;
     - record, but do **not** assert, whether `currentValue` equals the sent value, because a value the runtime refuses MUST be ignored (`session-config-options.mdx:565`);
     - SKIP when the agent exposes no `select` option.
   - **Harness:** none.
   - **Ownership:** the normative MUSTs for initial values (`-32602` for malformed or duplicate entries, unknown or disallowed entries ignored, the response reflecting actual values, no `config_option_update`) are stated in `session-config-options.mdx:563-568` and belong to that doc's researcher. This doc's `:456` is only a summary, so cite it as secondary on their rows. Merge row 4 into that family if they already propose it.

## New ledger entries

None. The only new rules in my docs that I do not propose as rows are not agent-side rules:
- `session-setup.mdx:156`: the Client SHOULD rebuild its cursors (client-side).
- `session-setup.mdx:157`: descriptive text about what a Client does.

Neither belongs in the ledger. If D1 is decided as "ledger, not row", the entry would be:

| citation | statement | reason |
|---|---|---|
| `session-setup.mdx:154` | The Agent SHOULD send a `cursor_update` during `session/load` for each cursor in the loaded history that it still accepts. | Unobservable: which cursors the Agent still accepts is internal to it, and it may stop accepting any cursor at any time (`prompt-turn.mdx:707`). |

## Decisions for the user

- **D1. Row 2: row or ledger?** The rule hinges on "still accepts", which is agent-internal. Recommendation: keep it as an ADVISORY row using the "never cleared" proxy. A false FAIL costs nothing on the verdict, and the proxy follows from the docs' own SHOULDs (`prompt-turn.mdx:705-709`). Choose the ledger entry above if you want no interpretive rows.
- **D2. Rows 1-3: SKIP or vacuous PASS when the agent never emits the feature?** CLIENTCAP-004/005 PASS vacuously. Those are MUST NOTs, where never emitting really is conforming. Recommendation: SKIP here. These are positive or comparative SHOULDs, and a PASS would wrongly suggest the agent's replay behaviour was exercised. This is a `pytest.skip` on behaviour, so there is no `inferred:` capability (the rows are ADVISORY).
- **D3. ACP-LOAD-002 and cursors.** `session-setup.mdx:152` calls cursors "part of the replayed history", so one could add `cursor_update` to the kinds that must not follow the load response. Recommendation: **no**. A `cursor_update` after the response can be a legitimate live update, such as clearing capabilities (`prompt-turn.mdx:707-709`), so it cannot be judged. Also, `HISTORY_KINDS` is shared with RESUME-002 and CANCEL-002. Keep LOAD-002 unchanged apart from its citation.
- **D4. Row 4 ownership.** Recommendation: the session-config-options researcher owns the `ACP-OPTIONS` family and cites `session-setup.mdx:456` as secondary. This report proposes only the "setup accepts `configOptions`" row, for dedupe.

## Discrepancies

- **Fork in the `configOptions` list.** `session-config-options.mdx:475` lists new/load/resume for accepting `configOptions`. `session-setup.mdx:456`, `session-config-options.mdx:541` and the `ForkSessionRequest.configOptions` schema also include `session/fork` ("when supported"). This is minor. Follow the fuller list. v1 has no fork coverage, so nothing changes yet.
- **`SessionOptionsRequest.sessionId` precondition.** The schema description says Clients MUST only send it when `loadSession` or `sessionCapabilities.resume` is supported. `session-config-options.mdx:507` also allows `sessionCapabilities.fork`. This is a docs-vs-schema mismatch in the session-config-options researcher's area, and only affects the client side.
- **Schema wording differs per request.** The schema `NewSessionRequest.configOptions` description includes "SHOULD NOT send other `session/update` ... before it responds", but `Load`/`ResumeSessionRequest` omit it. The docs (`session-config-options.mdx:568`) scope that rule to `session/new` and `session/fork`, so the two agree. There is no conflict.

## Open questions (route elsewhere)

- **`cursorId` on `session/fork`.** The Agent MUST reject with `-32602` a cursor that is unissued, no longer accepted, or does not support fork, and MUST NOT fall back (`prompt-turn.mdx:676-701`; `ForkSessionRequest.cursorId`). This is not in session-setup or session-modes; route it to the prompt-turn researcher. v1 currently has no `session/fork` rows at all.
- **Pre-existing gap.** `session-setup.mdx:144-148` (notices SHOULD NOT be replayed, unchanged since base) has neither a row nor a ledger entry. It would be tested exactly like row 1, with `clientCapabilities.session.notices`. It is worth adding alongside row 1 for consistency, or ledgering. This is outside this update's diff.
- **`prompt-turn.mdx:652-653` in replay.** This MUST requires that the anchored entity be reported before the cursor and that it be in the same session. `session-setup.mdx:154` restates it for replay ("follows the replayed entity it is anchored to"). Any prompt-turn row for it should also cover `session/load` replay and cite `session-setup.mdx:154`.
- **Capability gating during replay.** The `session.promptSuggestions` and `session.cursors` MUST NOTs (`prompt-turn.mdx:364,584-588`) also apply to replay. If prompt-turn/initialization add CLIENTCAP rows for them, the existing CLIENTCAP-004/005 pattern (which includes a load) covers replay. Cite `session-setup.mdx:150,152` there as secondary.
