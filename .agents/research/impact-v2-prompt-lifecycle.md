# v2 impact: `docs/protocol/v2/draft/prompt-lifecycle.mdx` (excluding Cancellation), `beac4ba` -> `3961af9`

**Sources checked:** agent-client-protocol worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2` @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (target), base `beac4ba96190018e9f6d82e148ff275084c5aa3e`. I read the whole target doc, all hunks, the target `schema/v2/schema.unstable.json` (`StateUpdate`, `*StateUpdate`, `BackgroundWork*`, `IdleStateUpdate`, `PromptResponse`, `ContentBlock`, `ToolCallStatus`, `RequestPermissionRequest`), the RFDs `docs/rfds/v2/background-work.mdx` and `docs/rfds/v2/prompt.mdx`, the cross-links in `session-setup.mdx`, `tool-calls.mdx`, `content.mdx` and `cancellation.mdx`, and the commits `26d7570a` (#2607) and `2da60af2` (#2627). In the TCK I read `src/tck/v2/requirements.py`, `src/tck/v2/conformance/{_helpers,test_prompt,test_patches,test_informational,test_session_capabilities}.py`, `tests/fixtures/agents/v2/_base.py`, `responds_after_idle.py` and `spec-tracker/maps/v2.toml`. I did not consult the Rust or Python SDKs: every question below is settled by explicit target text.
**Confidence:** high on the classifications and the `run_prompt` analysis, which follow explicit target text. Medium on the tiers proposed for new rows: three are flagged DECISION NEEDED.

All target citations are `docs/protocol/v2/draft/prompt-lifecycle.mdx:<lines> @ 3961af94fa62` unless stated otherwise. "PL" below abbreviates that doc.

## Answer

Most rows citing this doc only need their line numbers updated. Two rows lost their premise:

- **`ACP-PROMPT-208`.** The target now says the `idle` that ends the work "may arrive before or after" the prompt response, and "Clients MUST NOT infer ordering between them" (PL:372, added by #2607). That is exactly the ordering this row judges.
- **`ACP-INFO-CONCURRENT-201`.** Its cited sentence ("This does not require Agents to support prompts while work is active", base PL:1039-1040) was deleted. A new subsection says Clients MAY send `session/prompt` in any state and "Agents MUST NOT reject a prompt only because foreground work is active" (PL:382). Held prompts stay pending until inserted (PL:384).

Background work is new. It is an optional `background` snapshot list on `running`/`requires_action`/`idle`/`unknown`, and it brings three agent-side MUSTs a client can observe: once reported, the list is on every `state_update` (PL:204), items are announced before being listed (PL:206), and items are finalized before being removed (PL:206).

**`run_prompt`'s turn-end predicate still holds.** `idle` ends foreground work "even if background activity continues" (PL:154, 786, 1022-1023, 1044). `background` never changes what `idle` means: "quiet" is a separate client-side notion, `idle` plus `[]` (PL:214). Repeated snapshots are idempotent (PL:205, 1084-1090). So no logic change is required for the current callers, who serialize prompts. The docstring's citations and its "v2 leaves concurrent prompts unspecified" sentence are now wrong. One hardening is recommended (H1 below) for idles that arrive before the response.

## Summary table

| id | classification | note |
|---|---|---|
| ACP-PROMPT-201 | citation-only | 253-255,271-274 -> **323-325,341-344** |
| ACP-PROMPT-203 | citation-only | 276,731 -> **346,803** |
| ACP-PROMPT-205 | unchanged | schema-pointer citations still resolve; `BackgroundWork` items are now validated through `SessionUpdate` once the schema is re-vendored. The `schema.mdx:8397-8401` line citation is for the schema.mdx owner. |
| ACP-PROMPT-207 | citation-only (PL part) | 255,276,312 -> **325,346,388**. The `cancellation.mdx:53` part belongs to the cancellation researcher. |
| ACP-PROMPT-208 | **changed text / DECISION NEEDED** (recommend **retire** + ledger) | PL:372 explicitly allows the idle before the response and forbids clients from inferring order |
| ACP-STATE-201 | citation-only | 124,318-321,993,1000-1002,1042-1047 -> **152,394-397,1073,1080-1082,1121-1126**; optionally add 1046 |
| ACP-STATE-202 | citation-only | 126,314,714,996,1034,1042-1045 -> **154,390,786,1076,1114,1121-1124**; optionally add 1046 |
| ACP-STATE-203 | citation-only | 714,733,864,887 -> **786,805,936,965**; `IdleStateUpdate/anyOf/7` is still the `none` branch |
| ACP-STATE-204 | citation-only | 126,714,864,1012 -> **154,786,936,1092** |
| ACP-STATE-205 | citation-only | 125,773,995,1024-1025 -> **153,845,1075,1103-1105** |
| ACP-INFO-CONCURRENT-201 | **changed text + citation / DECISION NEEDED** | the cited text was deleted; prompts during active work are now defined (PL:382-384). Recommend keeping the id as a record of "inserted right away vs held", plus the new MUST row ACP-PROMPT-209. |
| ACP-PATCH-201 | citation-only | 406 -> **484** |
| ACP-PATCH-203 | citation-only | 298 -> **368** |
| ACP-PATCH-209 | citation-only | 125,773,994 -> **153,845,1074**; optional test refinement for background-work permission requests |
| ACP-RESUME-202 | citation-only (PL part) | 483-493,535-538,966,1004-1007 -> **561-571,613-617,1044,1084-1087**; optional test refinement for live foreground after the response |
| ACP-RESUME-204 | citation-only (PL part) | 300 -> **370** |
| ACP-RESUME-206 | citation-only (PL part) | 975-981 -> **1055-1061**. New `session-setup.mdx:346` MUST (background items before the snapshot) belongs to the session-setup researcher. |
| ACP-CLOSE-202 | citation-only (PL part) | 304 -> **374**. Its 1109-1112 and 1124 parts are in Cancellation (other researcher; they map to ~1185-1189 and 1199). |
| ACP-CLOSE-204 | citation-only (PL part) | 304 -> **374**; suggest also citing **384** (held prompts). Whether `session-setup.mdx:395`'s new MUST wording makes ADVISORY wrong is for the session-setup researcher. |
| ACP-CANCEL-207 (Stop reasons part only) | citation-only | 887 -> **965**, unchanged meaning. The row itself is the cancellation researcher's. |
| **ACP-PROMPT-209** | **new** (CAPABILITY, DECISION NEEDED on tier) | a prompt sent during active work is not rejected |
| **ACP-PROMPT-210** | **new** (ADVISORY, DECISION NEEDED) | held prompts are inserted in received order |
| **ACP-PROMPT-211** | **new** (CAPABILITY) | an unadvertised content type is rejected with `-32602` without insertion |
| **ACP-STATE-206** | **new** (CAPABILITY) | once `background` is reported, every later `state_update` carries it |
| **ACP-STATE-207** | **new** (CAPABILITY) | listed items were announced first |
| **ACP-STATE-208** | **new** (CAPABILITY, DECISION NEEDED on scope) | removed items were finalized first |
| ledger L1-L8 | new non-requirements | see "Ledger" |

Breaking-change table: none of B1-B12 hits these rows. B7 (`PromptRequest.prompt` `minItems: 1`) matches the new client MUST NOT at PL:311, and the TCK never sends `prompt: []` (grep of `src/tck/v2` finds none). The additive `background` field (Appendix B, `*StateUpdate`) is what the new STATE rows judge.

## Details

### What changed in the doc (non-cancellation, normative)

| Target lines | Change | Base |
|---|---|---|
| 176-216 "Background work" | **New section.** Terminals, tool calls and subagents as background work; `background` list on 4 states; snapshot / omitted-means-unreported / re-send / announce-before-list / finalize-before-remove / list-once rules; client uses | absent |
| 311 | Clients MUST NOT send empty `prompt`; Agents MAY reject with `-32602` | absent |
| 313 | **Agents MUST reject** content that is neither baseline nor advertised, or not understood, **with `-32602` without inserting it** | only the client-side MUST existed (base 243) |
| 372 | "The response has no fixed order relative to other session updates ... even the `idle` ... may arrive before or after it. Clients MUST NOT infer ordering" | base 302 had only "not an idle signal" |
| 380-384 "Prompts during active work" | **New.** Clients MAY prompt in any state; insert right away or hold; held prompts inserted in received order; MUST NOT reject only because active; held response pending until insertion; `-32800` on cancel/close | base 1039-1040 said Agents need not support it |
| 482-498 "Message IDs" | New heading over existing text. "a changed `messageId` indicates a new message" dropped; "(or empty for a new `messageId`)" added | base 406-420 |
| 69 | Chunk for an unseen ID creates the entity; the first update fixes timeline position (client rules) | absent |
| 998 | Listed background work is not part of failed work | added sentence |
| 1044 | "Each state may carry a `background` list" | added sentence |
| 1046 | Agents MUST still report `running`/`requires_action`/`idle` unless the Client advertised a custom state; Clients MUST NOT treat unknown states as idle | absent at base |
| 1119 | "For prompts sent while work is active, see ..." replaces the base 1039-1040 sentence | changed |

The rest of the diff is sentence-casing, semicolons split into sentences, and the Cancellation section (not mine).

### Existing rows: judgement against target text

- **PROMPT-201.** PL:323-325 (acceptance = insertion; respond successfully once inserted) and PL:341-344 (`messageId` required, non-null string). Same meaning; the test needs no change.
- **PROMPT-203.** PL:346 (MUST report the inserted message via `user_message`/chunks with the returned id). PL:803 (pending updates before idle) still backs "no later than the turn-ending idle". The test collects updates until both the idle and the response have been read, so the new any-order text (PL:372) does not affect it.
- **PROMPT-205.** It cites schema only. A target `state_update` may carry `background` items (`BackgroundTerminal`/`ToolCall`/`Subagent`, each requiring its id). A malformed list is a receiver tolerance (`x-deserialize-default-on-error`, PL:204), not a licence for agents to send one. `tck.v2.validation` validates strictly, so a malformed list FAILs here. That is consistent with the schema `type`, and I recommend keeping it. The `sessionId` attribution logic is unaffected: a subagent list item's `sessionId` sits inside `update`, not in `params.sessionId`.
- **PROMPT-207.** PL:388 is unchanged ("MUST return a JSON-RPC error response and MUST NOT emit user-message updates").
- **PROMPT-208: DECISION NEEDED.** Base support was PL:255 ("respond ... without waiting for foreground work to finish") plus PL:302. The target keeps the MUST at PL:325, but PL:372 now states the idle "may arrive before or after" the response and that "Clients MUST NOT infer ordering between them" (commit 26d7570a, #2607, "say the prompt response has no fixed order relative to updates"). The row's only evidence, wire order, is now declared meaningless by the spec. Options:
  - (a) **Recommended: retire `ACP-PROMPT-208`** and ledger PL:325's "without waiting" clause as unobservable (L1). Then `tests/fixtures/agents/v2/responds_after_idle.py` trips nothing. Delete it, or keep it as a "passes everything" fixture, and change `tests/v2/test_cli.py:1236-1240` (`test_responds_after_idle_fails_only_advisory_prompt_208`) and the ADVISORY id lists at `tests/v2/test_cli.py:120,1010,1170,1386,1486,1583`.
  - (b) Downgrade to INFORMATIONAL under a fresh id (tier change means a new id): record the order, never judge it.
  - (c) Keep it ADVISORY with a reworded text. Not recommended: the TCK would flag behaviour the spec explicitly permits.
- **STATE-201/202.** The MUSTs are restated at PL:152, 394-397, 1073, 1076, 1114 and 1121-1126. New PL:1046 adds that a custom state can't stand in for `running`/`idle`. That is already enforced, because `run_prompt` counts neither custom nor `unknown` states as active or idle. Adding 1046 to both citations is optional. Background reinforces STATE-202: an agent that stays `running` while only background work remains is non-conformant (PL:154).
- **STATE-203/204/205.** Text is unchanged (PL:936, 965, 786, 805, 1092; 153, 845, 1075, 1103-1105). The STATE-205 test's choice not to judge tool-call updates while blocked matches PL:178-184: background tool calls and terminals keep reporting.
- **INFO-CONCURRENT-201: DECISION NEEDED.** Its text ("Concurrency is explicitly out of scope") and both citations are obsolete. Target `docs/rfds/v2/prompt.mdx:88` now reads "Clients may send `session/prompt` while foreground work is active. Agents do not reject a prompt only because work is active". Recommendation:
  - Keep the id as INFORMATIONAL (tier unchanged) with new text: "Record (never assert) whether a prompt sent during active work is inserted right away or held, which PL:382 leaves to the Agent (as it does steering vs. next turn)."
  - New citation `docs/protocol/v2/draft/prompt-lifecycle.mdx:382-384 @ 3961af94fa62; docs/rfds/v2/prompt.mdx:88 @ 3961af94fa62`.
  - Move the assertable part to new **ACP-PROMPT-209**.
  - The current test sends B immediately after A. On a fast agent (and on `_base.py`, which finishes a turn synchronously) A is already idle, so the test never exercises "during active work". It should send B after A's `running`, as in PROMPT-209.
  - The `tests/v2/test_cli.py:466` PASS expectation stays.
  - Alternative: retire the id and let PROMPT-209's test record the hold/insert outcome as a property.
- **PATCH-201/203.** PL:484 and PL:368 are unchanged.
- **PATCH-209.** PL:153, 845 and 1074 are unchanged. Optional refinement: tool-calls.mdx:268 at target lets a permission request belong to listed background work, and PL:174 says the session may then stay `idle`. A request whose `subject` names an item in the latest `background` list should not count as evidence that `requires_action` was owed. That needs the tool-calls researcher's view.
- **RESUME-202.** Its PL parts (notices are live-only, PL:561-571 and 613-617; repeated snapshots, PL:1084-1087) are unchanged. Pre-existing hazard, now more likely with background work: after the resume response, an agent may legitimately start agent-initiated foreground work (`running` -> `agent_message` -> `idle`, PL:146-163). The trailing check would misread that `agent_message` as replayed history. Suggested refinement: ignore trailing message updates that follow a trailing `running`/`requires_action` for the session.
- **RESUME-204/206.** PL:370 and PL:1055-1061 are unchanged.
- **CLOSE-202/204.** PL:374 is unchanged. PL:384 adds that close answers held prompts `-32800`, which is consistent with CLOSE-204's two accepted outcomes.

### New requirements (agent-side, client-observable)

**ACP-PROMPT-209: CAPABILITY (`capabilities.session`), DECISION NEEDED on tier.**
- Text: "A `session/prompt` sent while the session's foreground work is active (after `running`/`requires_action` was observed for it) is not rejected. It is answered with a success carrying a `messageId` distinct from the first prompt's, or it stays pending (held) until a later `session/cancel` answers it `-32800`."
- Citation: `docs/protocol/v2/draft/prompt-lifecycle.mdx:382,384 @ 3961af94fa62`.
- Tier rationale: MUST NOT (PL:382). The MUST is about motive ("only because"), which a client can't see. But an identical baseline-text prompt the agent just accepted has no other plausible cause for rejection, so CAPABILITY is defensible. ADVISORY is the cautious alternative.
- Observation:
  1. Send A with `--cancel-prompt` text.
  2. On A's first active state, send B (`"hi"`).
  3. Wait a quiet period for B's response. Success -> PASS (inserted right away). Any error before step 4 -> FAIL; that includes `-32800`, because nothing asked for cancellation.
  4. No response yet -> B is held. Send `session/cancel`: B must now get `-32800` (PL:1173, which the cancellation researcher owns) or a success. Either -> PASS.
  5. SKIP ("not exercised") if A's idle was already read, or sitting in the pipe, before B was sent.
- Record the outcome ("inserted"/"held") under INFO-CONCURRENT-201.
- Do not drive B through `run_prompt` (see H3).
- Fixture: `rejects_prompt_while_busy.py`, which answers a prompt arriving while a `__hang__` turn is outstanding with an error such as `-32603 "busy"`.
- Note for the programmer: `_base.py` currently handles B immediately with reply, user_message, `running`, then `idle(end_turn)`, while A still "hangs". It would PASS, but it emits an idle while A's work is nominally active. It may need to hold B or steer without an extra idle.

**ACP-PROMPT-210: ADVISORY, DECISION NEEDED.**
- Text: "Prompts received during active work are inserted in the order received: the first `user_message`/`user_message_chunk` for the earlier prompt's `messageId` precedes the first one for the later prompt's."
- Citation: PL:382 ("Held prompts are inserted in the order they were received") and PL:69 (the first update fixes timeline position).
- Tier rationale: the sentence has no RFC 2119 keyword, and user-message receive order is only a proxy for insertion order. Recommend ADVISORY. Alternatively, don't register it.
- Observation: as PROMPT-209, but send B then C. Judge only prompts that were answered with success. Held ones cancelled `-32800` are not judged.
- Fixture: `inserts_held_prompts_out_of_order.py`.

**ACP-PROMPT-211: CAPABILITY (`capabilities.session`).**
- Text: "A prompt containing a content block whose type is neither baseline (`text`, `resource_link`) nor advertised in `capabilities.session.prompt` is rejected with `-32602`, and no user-message update is emitted for it."
- Citation: `docs/protocol/v2/draft/prompt-lifecycle.mdx:313 @ 3961af94fa62; docs/protocol/v2/draft/content.mdx:22 @ 3961af94fa62`.
- Tier rationale: explicit "Agents MUST reject ... with `-32602`, without inserting it" (PL:313, commit 25c127f3 #2601).
- Observation: pick the first of `image`/`audio`/`resource` whose capability the agent does not advertise; SKIP if it advertises all three. Send text plus that block on a fresh session. Expect an error with code `-32602` and no `user_message*` for the session within a quiet period.
- The probe knowingly breaks the client MUST at PL:313, in the same way as the existing malformed-traffic probes; say so in the test docstring.
- Fixture: `accepts_unadvertised_image.py`. Note that `_base.ConformingAgent._prompt_rejection` returns `None`, so the conforming fixture accepts everything today and must start rejecting unadvertised types.
- Dedupe: `initialization.mdx`/`content.mdx` researchers may propose the same row.

**ACP-STATE-206: CAPABILITY (`capabilities.session`).**
- Text: "Once any `state_update` for a session carries a concrete `background` array, every later `state_update` for that session on the connection carries a concrete array (not omitted, not `null`)."
- Citation: PL:204 and `schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/properties/background`.
- Tier rationale: "An Agent that reports background work MUST include `background` on every `state_update` for the session". The rule is conditional on the agent's own behaviour, so it is vacuous (SKIP) when no list is ever seen. Reading: `[]` counts as reporting ("`[]` means no background work is running"). The literal "every" would also cover updates before the first list, but the TCK can only judge from the first list onward.
- Observation: scan the turn's transcript, plus a quiet drain after it.
- Fixture: `background_list_dropped.py`, with `background: []` on `running` and none on `idle`.

**ACP-STATE-207: CAPABILITY (`capabilities.session`).**
- Text: "Every `background` item of type `terminal`/`tool_call`/`subagent` was announced earlier on the connection by a `terminal_update` with that `terminalId`, a `tool_call_update` with that `toolCallId`, or a `subagent_update` with that `sessionId`, for the same session."
- Citation: PL:206 and `schema/v2/schema.unstable.json#/$defs/BackgroundWork`.
- Tier rationale: explicit MUST. Items of unknown type are not judged (PL:209). It is vacuous when no item is ever listed.
- Fixture: `background_unannounced_item.py`.

**ACP-STATE-208: CAPABILITY (`capabilities.session`), DECISION NEEDED on scope.**
- Text: "When a `terminal`/`tool_call` item present in one concrete `background` list is absent from the next concrete list for the session, a `terminal_update` with non-null `exitStatus`, or a `tool_call_update` with status `completed`/`failed`/`cancelled`, arrived before the removing snapshot."
- Citation: PL:206 and `schema/v2/schema.unstable.json#/$defs/ToolCallStatus`.
- Scope problem: PL:208 says a terminal or tool call "that foreground work is waiting on is foreground work and is not listed". An item can therefore legitimately leave the list unfinished when foreground work adopts it, which is a tension with PL:206 (see Discrepancies). Recommendation: judge only removals in an `idle` snapshot, where nothing foreground can have adopted the item, and record the others.
- Subagent removals are not judged: a child is delisted when it goes idle, and no finalization is defined for it.
- Fixture: `background_removed_unfinished.py`.

Practical note on all three STATE rows: the TCK cannot make a real agent start background work, so these rows are vacuous for most agents and real only for agents that do background work (e.g. claude-agent-acp per RFD :281,385) and for fixtures. That is the same vacuous-SKIP pattern `ACP-PERM-201` uses.

Not proposed:
- PL:208's "MUST NOT also list a tool call whose only live work is a listed terminal" -> L5.
- PL:205's re-send SHOULD -> L4.
- `background[].type` custom values must begin with `_` (`BackgroundWork` `other` branch). That is an open-enum site, suggested to the ENUM-201 owner rather than a new row here.

### Ledger (new `[[not_requirement]]` entries)

| # | citation | statement | reason |
|---|---|---|---|
| L1 | PL:325 @ 3961af94fa62 | The Agent responds to `session/prompt` once inserted, without waiting for foreground work to finish. | Unobservable: PL:372 makes response-vs-idle order meaningless to clients. Only if PROMPT-208 is retired. |
| L2 | PL:180 | While a terminal is listed, the Agent SHOULD keep its output current when it can read it. | Unobservable: the client can't know whether output is readable. |
| L3 | PL:184,186 | The Agent SHOULD keep a background tool call non-final and listed, and SHOULD NOT list its own housekeeping. | Unobservable: depends on the Agent's knowledge and intent. |
| L4 | PL:205,207 | SHOULD re-send `state_update` when the list changes; SHOULD report `running` with the removal when follow-up work is known. | Out of scope: the TCK cannot provoke background work in a real agent, and timing and knowledge are unobservable. |
| L5 | PL:208 | MUST NOT list a tool call whose only live work is a listed terminal. | Unobservable: the client can't tell whether the tool call has other live work. |
| L6 | PL:382 | What inserting during active work means (steering vs. next turn) is up to the Agent. | Out of scope: explicitly Agent-defined; at most recorded by INFO-CONCURRENT-201. |
| L7 | PL:311 | Clients MUST NOT send an empty `prompt`; Agents MAY reject one with `-32602`. | Client-side rule plus a MAY; the TCK never sends `[]`. |
| L8 | PL:214,216 | Clients SHOULD wait a grace period before freeing resources on quiet; MAY treat unlisted unfinished items as abandoned; MUST NOT when `background` is unreported. | Client-side rules. |

### `spec-tracker/maps/v2.toml` section addresses (target casing)

Replace the `sections` list at `spec-tracker/maps/v2.toml:38-54` with:
`"(intro)"`, `"Session updates > (intro)"`, `"Session updates > Entity IDs"`, `"Foreground and background work"` (this now covers the new `Background work` subsection, which should be core: it is restated by tool-calls.mdx:125,268,423,587, session-setup.mdx:49,346,391 and cancellation), `"Prompt lifecycle > (intro)"`, `"1. User message"`, `"2. Prompt accepted"` (covers `Insertion and ordering`, `Prompts during active work`, `Prompts that are never inserted`, all core: restated by session-setup.mdx:395 and the RFD), `"3. Agent reports output > (intro)"`, **`"3. Agent reports output > Message IDs"`** (new; should be core: the message upsert rules are relied on by replay and the PATCH rows), `"4. Report completion > (intro)"`, `"5. Tool invocation and status reporting"`, `"6. Continue conversation"`, `"Stop reasons"`, `"Failures"`, `"Session states"`, `"Cancellation"`.

Re-case the comment's excluded list too: `Session notices`, `Session compaction`, `Session usage updates`, `End-turn token usage (unstable)`; `Session-directed messages (unstable)` is unchanged. Headings verified via `grep -n '^#'` at target.

### `run_prompt` (`src/tck/v2/conformance/_helpers.py:829-1129`): does the predicate still match?

1. **Idle with background work running.** Yes, an agent can and must go `idle` while background work continues: "When foreground work ends, the Agent MUST report `idle`, even if background activity continues" (PL:154). `idle` means "No foreground work is active. Background activity may continue." (PL:1022-1023). The `IdleStateUpdate` schema description says the same. `background` does not redefine `idle`. "Quiet" (`idle` plus `background: []`) is a separate client notion (PL:214), and a turn driver must not wait for it. **No change.**
2. **Repeated snapshots.** Agents SHOULD re-send the current state when the list changes (PL:205). Repeats are not transitions, and a repeated `idle` is not a new completion (PL:205, 1084-1090). Inside a turn, a repeated `running` keeps `active=True`, which is correct. A repeated `idle` from the previous turn, read during the next `run_prompt` before its `running`, at most becomes `provisional` and is voided by the `running` (existing logic, `_helpers.py:1004-1014`). **No change.**
3. **`unknown`/custom states.** PL:1038 and 1046 still say a later standard state replaces `unknown`, and unrecognized states are never idle. The helper records them and neither starts nor ends a turn on them. **No change.**
4. **Prompts during active work and idle-before-response (the real gap).** PL:372 allows the idle to precede the response. PL:382-384 lets an agent hold a prompt, leaving its response pending, until earlier foreground work ends. Today the first idle after active is captured even if it precedes the response (`_helpers.py:1008-1012`), and `_try_end` finalizes as soon as the response arrives (`:945-951`). If the session was active when the prompt was sent, or agent-initiated work started first (more likely now with background follow-ups, PL:146-163 and 207), the helper can end the turn at the *earlier* work's idle. The held prompt's own `running`/`idle` then leaks into the next step. All current callers serialize prompts and seed from an idle state, so this does not misjudge any existing test.

**Changes the helper must make:**
- **Required (comments only):**
  - Update stale citations. Docstring `:864` -> 936. `:314` -> 390. `:314,891` -> 390,969. `:1004-1007` -> 1084-1087. `ACTIVE_STATES` `:124,993` -> 152,1073 and `:1000-1002` -> 1080-1082.
  - `:1098-1100` (the hold_permission `cancelled` answer) cites base Cancellation text that was rewritten: at target, PL:1177 makes the client's `cancelled` answer a MAY. Hand that to the cancellation researcher.
  - Replace "Callers must serialize prompts per session; v2 leaves concurrent prompts unspecified" with: v2 lets clients prompt in any state (PL:382), but `run_prompt` cannot attribute an idle to a held prompt, so callers serialize prompts per session.
- **Recommended hardening (H1):** when the first idle-after-active arrives *before* the prompt's response, treat it as a candidate. Don't finalize on the response. Finalize after `quiet_period(timeout)` past the response if no new active state arrives. If one does, discard the candidate and wait for the next idle-after-active. This costs latency only for agents that idle before responding. If PROMPT-208 is kept, its fixture still FAILs, with `idle_index` pointing at the first idle.
- **H2 (cancellation researcher's call):** after the trigger, the mock client answers every prompted-session permission request `cancelled`. PL:1177 says requests for work in the latest `background` list are not affected. Consider answering normally when `subject` names a listed item.
- **H3:** tests that prompt during active work (proposed PROMPT-209/210) should drive the second prompt with raw `send_request` plus a dedicated wait, not with `run_prompt`.
- `last_known_state` and `PromptTurn` need no new fields for the current rows. The new STATE-206..208 tests can read `turn.states` (which already holds every `state_update` dict, `background` included) and `turn.updates`.

## Testability notes

- PROMPT-209: a conforming agent answers B with success or holds it until cancel; a non-conforming one errors on B while A is active. A race where A idles before B is sent is SKIP, not PASS.
- PROMPT-211: a conforming agent answers `-32602` and emits no user message; non-conforming means a success, another code, or a user-message echo. It is unobservable when the agent advertises all three optional types.
- STATE-206..208 are fully observable from the `session/update` stream, but only when the agent does background work. Expect SKIP on most real agents.
- Nothing in PL:382 bounds how long a prompt may be held. PROMPT-209 stays bounded because it ends the hold with `session/cancel`, which owes the held prompt `-32800` (PL:1173).

## Discrepancies

1. **PL:206 vs PL:208.** PL:206 says the Agent MUST finalize (`exitStatus` or a final tool status) before the snapshot that removes an item. PL:208 says an item foreground work is waiting on "is not listed", which implies it can be delisted unfinished when foreground adopts it. The background-work RFD (`docs/rfds/v2/background-work.mdx:194,201`) has the same pair of rules and does not reconcile them. Hence the STATE-208 scope recommendation.
2. **PL:325 vs PL:372.** These are not a strict contradiction. PL:325 forbids *waiting* for work to finish before responding, and PL:372 says wire order carries no meaning. Together they leave PL:325 with no client-observable evidence (the PROMPT-208 decision).
3. **Schema `x-deserialize-default-on-error` on `background` vs strict TCK validation.** The receiver rule (PL:204) is tolerance. Agents are still bound by the schema `type`. Not a real conflict, only noted.

## Open questions

- PROMPT-208 retire vs. INFORMATIONAL (and what happens to the `responds_after_idle.py` fixture). Orchestrator or maintainer.
- PROMPT-209 tier (CAPABILITY vs ADVISORY), PROMPT-210 registration and tier, STATE-208 scope.
- INFO-CONCURRENT-201: keep the id with new text, or retire it.
- Dedupe PROMPT-211 against the initialization/content researchers. `session-setup.mdx:346` (resume background-item MUST) and `:395` (CLOSE-204 tier) belong to the session-setup researcher. The PATCH-209 background-permission refinement involves the tool-calls researcher (tool-calls.mdx:268). The `background[].type` open-enum site goes to the ENUM-201 owner. H2 goes to the cancellation researcher.
