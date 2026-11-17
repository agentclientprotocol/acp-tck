# Impact research, v2: `docs/protocol/v2/draft/prompt-lifecycle.mdx` (3961af94 -> 3ea94133)

**Sources checked:** agent-client-protocol `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (target) vs `3961af94` (base), read by
`git show <rev>:<path>` from `../agent-client-protocol-2`. That checkout's HEAD has moved one commit past the target (`6ace4f6a`),
but that commit does not touch this doc, and the target file is byte-identical to the working tree. Files read: `prompt-lifecycle.mdx`
in full at both revisions, plus its diff; the relevant parts of `cancellation.mdx`, `subagents.mdx`, `session-setup.mdx`,
`initialization.mdx`, `schema.mdx`, `docs/docs.json`, and `schema/v2/schema.unstable.json` (`IdempotencyKey`, `PromptRequest`,
`PromptSuggestion*`, `Cursor*`, `ForkSessionRequest`, `ClientSessionCapabilities`). On the TCK side, acp-tck @ `18fad47`:
`src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`, `src/tck/v2/conformance/{_helpers,test_cancel,test_session_capabilities}.py`,
and the reports `scope-rfds-v2-prompt-session.md` and `impact-v2-extensibility.md`.
Line remaps were computed mechanically with `difflib` over the two file versions, and every range that touches a changed line
was checked by hand. I did not consult the reference SDKs: every new rule is stated explicitly in the docs or schema.
**Confidence:** high for the remaps and the classifications. Medium for the tiers of the declarative idempotency rules (Decisions
D2 and D3).

Abbreviations: PL = `docs/protocol/v2/draft/prompt-lifecycle.mdx`, CN = `cancellation.mdx`, SA = `subagents.mdx`,
SS = `session-setup.mdx`, all at `@ 3ea94133` unless marked base.

## Summary

- **Registry rows citing PL: 49.** 44 are citation-only. Of those, 7 also need an RFD citation dropped or relabelled:
  `SUBAGENT-009`, `-013`, `-201` (relabel); `STATE-209`, `-210`, `PROMPT-209`, `INFO-CONCURRENT-201` (drop).
  `CANCEL-209` gets an optional text note, and `ENUM-201` an extension. 4 have changed text: `SUBAGENT-011`, `-012`,
  `-202`, and `PATCH-211` (its text names an RFD). 1 has a changed tier (`CANCEL-213`, SHOULD -> MUST). None is
  removed.
- **Ledger entries citing PL: 9 (`citation`), plus 1 that mentions PL in its `reason`.** All are citation-only. The one
  that cites a changed line is `[0]` (`:372` was split). `[7]` carries an RFD label to refresh. `[80]`'s reason text
  mentions `prompt-lifecycle.mdx:67`, which is now `:70`.
- **New requirements: 16 proposed.** 9 are idempotency (N1-N9; N8 and N9 optional), 4 are prompt suggestions
  (N10-N13), and 3 are cursors (N14-N16). Plus 1 `ACP-ENUM-201` extension.
  **New ledger entries: 8.**
- **Offset table** (base line -> target): 1-15 +0, 41-53 +3, 64-70 +3, 72-136 +5, 138-141 +5, 143-181 +10, 183-319 +10,
  320-371 +16, 373-383 +18, 385-390 +25, 391-619 +83, 620-758 +150, 759-782 +271, 783-1140 +273 (the table rows
  1141-1157 changed only in padding, +273), 1158-1174 +273, 1175-1176 +275, 1178-1205 +275. Changed base lines:
  16-40, 54-63, 71, 137, 142, 182, 372, 384, 1015, 1031-1032, 1042, 1067, 1141-1157, 1177. New target blocks: 330-335
  (`idempotencyKey` param), 388-390, 402-409, 416-473 (Retrying a prompt), 703-769 (Prompt suggestions), 909-1029
  (Session cursors), 1054-1055, 1448-1449.

## Registry rows (`src/tck/v2/requirements.py`)

| id | classification | target citation (PL lines @ 3ea94133) | note |
|---|---|---|---|
| ACP-SUBAGENT-009 | citation-only | 133-137 | `docs/rfds/subagents.mdx` label Active -> **(Preview RFD)**, re-map owned by the subagents researcher. |
| ACP-SUBAGENT-011 | changed text (scope widened) | 142-147 | Base: "The task a parent gives a subagent". Target: "A message from a parent to a subagent, including the first one…". The row judges only the first task, which is a subset, so it stays valid. The rule is now also in SA:262-264 (docs govern; subagents researcher). RFD -> (Preview RFD), secondary. |
| ACP-SUBAGENT-012 | changed text (scope widened) | 142-147 | Same as 011 (SA:262). |
| ACP-SUBAGENT-013 | citation-only | 82-86 | Heading lost "(unstable)", which has no effect. RFD -> (Preview RFD). |
| ACP-SUBAGENT-201 | citation-only | 1288-1291 | Base `:1015` changed only to add a link to SA#work-state. RFD -> (Preview RFD). |
| ACP-SUBAGENT-202 | **changed text** | 218,220,1446,**1448** | New PL:1448 "Cancelling a session also cancels the child work that the cancelled work is waiting on" (and SA:400). The docs now state what the row calls RFD-only. Under docs precedence, drop the "stated by the Subagents RFD, so capped" wording, cite PL:1448 first, and keep the RFD as (Preview RFD) secondary. The text is declarative, so the tier stays CAPABILITY. The gate (`inferred:subagents` vs `capabilities.session`) is for the subagents researcher. |
| ACP-PROMPT-201 | citation-only | 339-341,357-360 | |
| ACP-PROMPT-203 | citation-only | 362,1076 | |
| ACP-STATE-201 | citation-only | 162,477-480,1346,1353-1355,1394-1399 | |
| ACP-STATE-202 | citation-only | 164,415,1059,1349,1387,1394-1397 | |
| ACP-STATE-203 | citation-only | 1059,1078,1209,1238 | |
| ACP-STATE-204 | citation-only | 164,1059,1209,1365 | |
| ACP-STATE-205 | citation-only | 163,1118,1348,1377-1378 | |
| ACP-STATE-206 | citation-only | 198,213-214 | |
| ACP-STATE-207 | citation-only | 216,219 | |
| ACP-STATE-208 | citation-only | 216,218 | |
| ACP-STATE-209 | citation-only + RFD | 215-216 | `docs/rfds/v2/background-work.mdx` is now **Draft**. PL:215 states the rule, so drop the RFD citation. |
| ACP-STATE-210 | citation-only + RFD | 162,194,196,215,218 | Same as 209. |
| ACP-PROMPT-207 | citation-only | 341,362,413 | |
| ACP-PROMPT-209 | citation-only + RFD | 400,402 | Base `:384` became 402-409. "Response stays pending" is at 402. Drop `docs/rfds/v2/prompt.mdx:88` (now Draft; PL:400 states it), agreeing with `scope-rfds-v2-prompt-session.md`. |
| ACP-PROMPT-211 | citation-only | 323,413 | |
| ACP-PROMPTCAP-201 | citation-only | 323,413 | |
| ACP-INFO-CONCURRENT-201 | citation-only + RFD | 400-404,1391-1392 | Drop the Draft RFD as for 209. |
| ACP-INFO-BACKGROUND-201 | citation-only | 218 | |
| ACP-INFO-BACKGROUND-202 | citation-only | 1446 | |
| ACP-CANCEL-001 | citation-only | 1366,1460-1467,1474 | |
| ACP-CANCEL-002 | citation-only | 1076,1357-1360,1478 | |
| ACP-CANCEL-203 | citation-only | 341,413,1277,1446,1469-1476 | |
| ACP-CANCEL-204 | citation-only | 1454 | |
| ACP-CANCEL-206 | citation-only | 1436-1444 | |
| ACP-CANCEL-207 | citation-only | 1238 | |
| ACP-CANCEL-209 | citation-only (optional text note) | 256-257,1426,1446,1452,1460-1464 | `:1153` -> 1426 (table padding only). `:1177` -> 1452 changed, but the MUST "stop waiting" is unchanged. New at 1452 (and CN:42): "Only the Agent knows which work a request belongs to, so it decides which requests these are." See D5. |
| ACP-JSONRPC-007 | citation-only | 341,404,413 | Base `:384` -> 404 (the `$/cancel_request` bullet: "best effort… An Agent that honors it answers with `-32800` and does not insert the message. Otherwise the prompt is inserted as usual"). This matches the row. |
| ACP-CANCEL-213 | **changed tier** | 1452 | Base PL:1177 said "**SHOULD** cancel each of them with `$/cancel_request`". Target PL:1452 says "**MUST** cancel each of them" (also CN:42). Proposal: ADVISORY -> CAPABILITY, `capabilities.session`. Update the text and the docstrings (`test_cancel.py:15,438` call it ADVISORY). See D1. The cancellation researcher may also own it (it cites `cancellation.mdx:40,63`). |
| ACP-CANCEL-214 | citation-only | 403,1446 | Base `:384` -> 403 ("`session/cancel` and `session/close` drop every prompt the Agent has not inserted. The Agent answers each of them with `-32800`"). Same rule. |
| ACP-INFO-CANCEL-201 | citation-only | 1430,1466-1467 | `:1157` -> 1430 (padding only). |
| ACP-RESUME-202 | citation-only | 644-654,696-699,1317,1357-1360 | |
| ACP-RESUME-204 | citation-only | 386 | |
| ACP-RESUME-206 | citation-only | 1328-1334 | The lifecycle-example row at 1415 now reads "Replay and `replay_complete`… -> snapshot -> response". That is consistent with the row (`replay_complete` belongs to session-setup). |
| ACP-RESUME-212 | citation-only | 1357-1360 | |
| ACP-RESUME-217 | citation-only | 214 | |
| ACP-CLOSE-002 | citation-only | 392,1460-1463,1474 | |
| ACP-CLOSE-204 | citation-only | 392 | |
| ACP-PATCH-201 | citation-only | 567 | |
| ACP-PATCH-203 | citation-only | 384 | No conflict with idempotency: the test sends no key. |
| ACP-PATCH-209 | citation-only | 163,184,1118,1347 | |
| ACP-PATCH-210 | citation-only | 194 | |
| ACP-PATCH-211 | changed text (RFD only) | 226,1271,1450 | `background-work.mdx:56` is now Draft. PL:226 states it ("A tool call that references a listed terminal is live"). Drop the RFD and the phrase "an Active RFD allows this explicitly". |
| ACP-ENUM-201 | citation-only + **extension** | 219, add 984 | See "ENUM-201 extension" under New requirements. |

## Ledger entries (`spec-tracker/maps/v2.toml`)

| entry (statement head) | classification | target citation | note |
|---|---|---|---|
| [0] responds once inserted, without waiting (`:325,372`) | citation-only, **cites a changed line** | PL:341,388 | Base `:372` was split into 388 (the "MUST NOT infer ordering" paragraph) and 390 (lost response, now pointing to idempotency). The reason still holds. |
| [1] held prompts inserted in order (`:382`) | citation-only | PL:400 | The reason ("no MUST/SHOULD… unbounded") does not rest on a TCK choice. Borderline: its second clause describes the TCK's means, but the first clause carries it. |
| [2] terminal output current (`:180`) | citation-only | PL:190 | |
| [3] keep non-final and list; no housekeeping (`:184,186`) | citation-only | PL:194,196 | |
| [4] follow-up `running` with removal (`:207`) | citation-only | PL:217 | |
| [5] foreground-waited not listed (`:208`) | citation-only | PL:218 | |
| [6] detached child listed (`:210`) | citation-only | PL:220 | Already "Deferred" with a real blocker. |
| [7] entity-ID reuse (`:67`; subagents RFD 439-441) | citation-only + RFD | PL:70 | RFD label Active -> Preview. PL:70 states the rule, so the RFD can go. The cursor-ID analogue is covered by the new N14. |
| [80] (tool-calls `terminalId`) reason text "`prompt-lifecycle.mdx:67`" | reason-text remap | PL:70 | `spec-impact --fix` may not rewrite `reason` text, so fix it by hand. |
| [91] ignore late answers (`:1109,1110,1181-1183`) | citation-only | PL:1382,1383,1456-1458 | |
| [92] background not covered by cancel (`:1173`) | citation-only | PL:1446 | |

No existing reason citing PL rests on a TCK choice.

## New requirements

All are `CAPABILITY` / `capabilities.session` unless noted. The registry convention puts every session/prompt and session/update
rule behind that gate, and PL:439 makes the idempotency key part of that marker. The three feature RFDs
(`rfds/v2/idempotency-keys`, `rfds/prompt-suggestions`, `rfds/session-cursors`) are all **Draft** (`docs/docs.json:226,236,238`)
and the docs state every rule, so none is cited. Idempotency is v2-only (no `idempotencyKey` in the v1 draft docs or schema),
hence `2xx`. Prompt suggestions and cursors also exist in v1 (`v1/draft/prompt-turn.mdx:364,584`), so the id-alignment step should
look for shared ids. Note that v1 gates cursors on a client capability and v2 does not, so that rule differs.

### Idempotency keys (`ACP-PROMPT-212..219`, provisional)

- **N1 `ACP-PROMPT-212`: retry of an inserted prompt.** Rule: re-sending a `session/prompt` with the same `idempotencyKey`
  on the same session gets a success whose `messageId` equals the original, and no second user message is inserted.
  - Citation: PL:439,451-452,455,457,465-466; `schema/v2/schema.unstable.json#/$defs/PromptRequest/properties/idempotencyKey`.
  - Test: `new_session`, then `run_prompt(..., extra_params={"idempotencyKey": <uuid4>})` and record M. A `-32602` here
    FAILs ("MUST support the key"). After the idle, send the same params raw with a new JSON-RPC `id`, wait for the
    response, then `quiet_period`. FAIL on an error, on `messageId != M`, or on any `user_message`/`user_message_chunk` for
    the session with a `messageId` other than M. A re-sent upsert for M is allowed.
  - Retention: on the same connection, the key must be recognized whether the message is retained (465) or not (466).
  - Harness: a small "send prompt, collect response and quiet window" helper. `run_prompt` would time out on a retry that
    starts no work.
- **N2 `ACP-PROMPT-213`: malformed key rejected.** Rule: a key that is `""`, 256 characters long, or not a string (`42`) is
  answered with `-32602`, and nothing is inserted (no user-message update and no active state within a short quiet
  period). The agent must not treat it as omitted.
  - Citation: PL:333,441; `#/$defs/IdempotencyKey` (`minLength` 1, `maxLength` 255).
  - The probe breaks the schema on purpose, as `ACP-PROMPT-211` does. Reuse the rejection helper at `_helpers.py:2922`.
  - Optional positive edge: a 255-character key is accepted.
- **N3 `ACP-PROMPT-214`: reused key with a different prompt.** Rule: after N1's M, sending the same key with different text
  gets either M or `-32602`, never a second insertion. After a `-32602`, re-sending the original prompt with the key
  still gets M.
  - Citation: PL:444,457.
  - The probe breaks the client MUST NOT at PL:444 on purpose, because PL:457 defines the agent's answer.
- **N4 `ACP-PROMPT-215`: retry of a held prompt.** Rule: in the `ACP-PROMPT-209` scenario, send P2 with key K twice
  back-to-back during active work. Both requests get the same outcome: both succeed with the same `messageId`, or both
  get `-32800` after the TCK's `session/cancel`. At most one user message is inserted for P2. A mixed outcome FAILs.
  - SKIPs: as `ACP-PROMPT-209` (the first work may have ended).
  - Citation: PL:400-404,453,1446.
  - Harness: extend `prompt_during_active_work` to send two raw requests.
- **N5 `ACP-PROMPT-216` (ADVISORY, see D3): keys stay private.** Rule: the key string (a uuid4, so a match is
  unambiguous) never appears in any agent message on the connection. The check covers every `session/update`, the
  `session/list` result, and the replay of `session/resume` with `replayFrom: {"type":"start"}`.
  - Citation: PL:459.
  - Test: piggyback on N1's connection, adding one `session/list` call and one resume.
- **N6 `ACP-PROMPT-217` (see D2): key scoped to the session.** Rule: the same key and text in a second session is a new
  submission. That prompt succeeds and a `user_message`/chunk for its returned `messageId` arrives on the second session.
  Don't compare the IDs, because IDs are only unique per session.
  - Citation: PL:461.
  - Optional fork variant: behind `capabilities.session.fork` (461 names `session/fork` explicitly).
- **N7 `ACP-PROMPT-218`: key recognized across connections while the message is retained.** Rule: prompt with K on
  connection A and record M. Then, in a fresh process, run `initialize` and `session/resume` with `replayFrom: start`.
  If the replay carries user message M, the message is retained (SS: full replay of retained history), so re-sending
  with K must get M with no new insertion.
  - SKIPs: when the cross-connection resume fails, or when M is not replayed (not retained, so the key MAY be forgotten,
    PL:467).
  - Citation: PL:465,467,471.
  - Harness: a two-process flow in one test. `obtain_resumable_session` route (3) shows how to resume across processes.
- **N8 `ACP-PROMPT-219` (optional, see D4): an error leaves the key unrecorded.** Rule: a prompt with K and a
  `_tck_unknown` block gets `-32602` (otherwise SKIP; `ACP-PROMPT-211` judges that). A valid prompt with K then succeeds
  and is inserted.
  - Citation: PL:451,456.
- **N9 (optional, see D4): `$/cancel_request` with a key.** Rule: in N4's scenario, after the two P2 requests, send
  `$/cancel_request` for the first. If the agent honors it (answers `-32800`), the other pending request for K is also
  answered `-32800`, and P2 is not inserted.
  - SKIPs: when the agent does not honor it.
  - Citation: PL:403-404,458.

### Prompt suggestions

- **N10 `ACP-CLIENTCAP-2xx`: no suggestions without the client capability.** This confirms the extensibility report's
  proposal. Rule: with the default `capabilities: {}`, no `prompt_suggestions_update` is seen over `session/new`, a prompt
  turn, and a quiet period.
  - Citation: PL:42,707; `initialization.mdx:207-213`; `#/$defs/PromptSuggestionsUpdate` (description: "Agents MUST only
    send this update when the Client advertised…"). `extensibility.mdx:39` is secondary.
  - Test: reuse the `ACP-CLIENTCAP-003` transcript. Optional second launch with `{"session": {"promptSuggestions": null}}`
    (PL:707: `null` means not advertised).
  - Shared id: v1 has the same rule (`prompt-turn.mdx:364`), so take a shared non-`2xx` id if v1 adds it.
- **N11 `ACP-SUGGEST-2xx`: suggestion content.** Rule: with the client advertising `session.promptSuggestions: {}`, every
  suggestion's `prompt` contains only `text`/`resource_link` blocks and is not made only of empty or whitespace-only text.
  Schema validation already enforces `minItems: 1`.
  - SKIPs: when no suggestion is sent.
  - Citation: PL:743,745-748; `#/$defs/PromptSuggestion/properties/prompt`.
  - Harness: `connected_agent(capabilities={"session": {"promptSuggestions": {}}})`, which already exists.
  - Optional: a second launch advertising `image`/`audio`/`embeddedContext` to check the agent-side half (each type is
    also advertised in the agent's `session.prompt`).
- **N12 `ACP-SUGGEST-2xx`: an accepted prompt outdates the list.** Rule: with the capability advertised, if the latest list
  before the TCK sends the second prompt is non-empty, a `prompt_suggestions_update` arrives after that prompt is sent.
  Judged before the second turn's idle, or within `quiet_period` after it.
  - SKIPs: when no non-empty list is current before the second prompt.
  - Citation: PL:755 (acceptance = insertion, PL:339).
  - The window is a TCK choice, because the spec states no deadline (see D6).
- **N13 `ACP-SUGGEST-2xx` (ADVISORY): not replayed.** Rule: with the capability advertised on both connections, after a
  turn that produced suggestions, `session/resume` with `replayFrom: start` delivers no `prompt_suggestions_update` for the
  session before the resume response.
  - Citation: PL:768 ("A resumed session starts with an empty list, and the Agent may send a new update after
    `session/resume` completes"); schema description.
  - SKIPs: when no suggestion was sent.

### Session cursors (`ACP-CURSOR-2xx`, provisional)

- **N14 `ACP-CURSOR-2xx`: the anchor is set once and never moves.** Rule: per (session, `cursorId`) on the connection, the
  first `cursor_update` carries a non-null `anchor`. Later ones omit it, send `null`, or repeat an identical anchor.
  - Reset the tracking at a full replay (`session/resume` with `replayFrom`). SS:341 lets "a replayed cursor… carry a
    different anchor than it had before".
  - SKIPs: when no `cursor_update` is sent.
  - Citation: PL:947,949,952; `#/$defs/CursorUpdate`.
  - No harness change: there is no client capability in v2 (PL:923-926).
- **N15 `ACP-CURSOR-2xx`: the anchor names an entity already reported on that session.** Rule: for a session created by
  `session/new` on this connection, a first `cursor_update` whose `anchor.type` is one of the six defined types names an
  entity of that type and ID reported earlier on the same session. The mapping:
  - `user_message`, `agent_message`, `agent_thought`, `session_message` (or their chunks) by `messageId`;
  - `tool_call_update`/`tool_call_content_chunk` by `toolCallId`;
  - `compaction_update`/`compaction_summary_chunk` by `compactionId`.

  Not judged: custom anchor types, and resumed sessions (PL:995 allows anchors to entities a resumed Client does not hold).
  - Citation: PL:966-975,982-983.
- **N16 `ACP-CURSOR-2xx`: unknown `cursorId` rejected.** Gate: `capabilities.session.fork`. Rule: `session/fork` with a
  `cursorId` the agent never issued for that session (a fabricated `cur_tck_never_issued`) gets `-32602`. A success
  (forking anyway, as if omitted) FAILs.
  - Optional sub-probes when the agent announced cursors: a cursor from session A used on session B; the source's cursor
    used on the fork's new session (PL:1019 "does not inherit them"); a cursor whose `capabilities` lack `fork`.
  - Citation: PL:999,1017-1020; `#/$defs/ForkSessionRequest/properties/cursorId`.
  - The probe breaks the client MUSTs at PL:997-998 on purpose. See D7.
- **ENUM-201 extension: confirmed.** Add `cursor_update`'s `anchor.type` and `anchor.position` as open-enum sites.
  - Citation: PL:984 ("`type` and `position` accept custom and future values", linking to the extensibility enum rule);
    `#/$defs/CursorAnchor`, `#/$defs/CursorAnchorPosition`.
  - Also agree with adding `cursor_update`, `prompt_suggestions_update` and `replay_complete` to `SESSION_UPDATE_KIND`
    (PL:41-43).

## New ledger entries

1. PL:149-152. "When the Agent has no evidence of who sent a message the child received, it omits `senderSessionId` and
   MUST NOT assume the parent, and links two views only when it can establish they are the same message."
   - Reason: unobservable, because what the agent knows about a message's sender is internal.
   - Dedupe: SA:265 states the same rule (subagents researcher).
2. PL:469. "Agents SHOULD store the key in the same step as the message."
   - Reason: unobservable, because a restart that loses both cannot be told from no retention, which PL:467 permits.
3. PL:466. "For a prompt whose message the Agent does not retain, such as a locally handled command, the Agent MUST
   recognize the key while the session stays active on a connection."
   - Reason: unsafe. The only named non-retained case is a locally handled command, and invoking an agent's commands has
     side effects the TCK cannot predict (as the `slash-commands.mdx:149,157-160` entry). A same-connection retry of any
     inserted prompt is judged by ACP-PROMPT-212.
4. PL:455. "A retry gets the original `messageId` and nothing else; the Agent doesn't start a second round of work for
   the message."
   - Reason: not decidable. Foreground work after a retry may continue work that stopped unfinished, which PL:455 leaves
     to the Agent, or may be unrelated. The no-second-insertion half is ACP-PROMPT-212.
5. PL:754. "Agents MUST predict a list from the conversation as it stands when they send it, and MUST discard a
   prediction if the conversation changed before it was sent."
   - Reason: unobservable, because when a prediction was computed is internal. The observable consequence after a prompt
     is judged by the PL:755 row.
6. PL:756. "Agents SHOULD replace or withdraw the list when it stops applying for another reason."
   - Reason: unobservable. Whether a list still applies is the Agent's judgement, and the named case (foreground work
     started without a prompt) cannot be caused by a client.
7. PL:1024,1026-1027. "Agents SHOULD accept a cursor for as long as they retain the history at its position, and SHOULD
   send a `cursor_update` clearing its `capabilities` when they stop accepting it."
   - Reason: unobservable. Retention is internal, and the Agent "can stop accepting a cursor at any time" (PL:1026), so a
     rejected cursor proves no violation.
8. PL:999 (positive half). "With a valid cursor the Agent MUST NOT act at a different position: the fork's history is
   the source's history before the cursor (PL:1001-1002)."
   - Reason: Deferred. Checking it needs the agent to retain and replay the fork. The v2 docs and schema
     (`ForkSessionRequest.cursorId`, PL, SS) also do not say whether a fork keeps the source's entity IDs, so the TCK
     cannot match the fork's replay to the anchor.

Dedupe note: PL:1055 ("its `cost` includes the costs of its descendants") is restated in SA:494, which adds "A descendant's
cost can reach its ancestors later". That rule belongs to the subagents researcher. If it is ledgered, the reason is that the
timing is unbounded and cost reporting is optional.

Not ledgered, because they are client- or intermediary-side: PL:440,442,444,471 (client key rules), 473 (intermediary), 751,
760-765 (client suggestion rules), 954-957 and 992-998 (client cursor rules), 1448's first sentence (the client sends
`session/cancel` to a child only with `cancel`; `_child_cancel.py` already obeys it).

## Decisions for the user

- **D1. Retier `ACP-CANCEL-213` from ADVISORY to CAPABILITY.** The upstream text changed SHOULD -> MUST (PL:1452, CN:42).
  The current window ("before or shortly after the cancelled idle", `quiet_period`) becomes a verdict-affecting deadline
  the spec does not state. **Recommend** retiering and keeping the window. Expect cross-check movement.
- **D2. Tier of the declarative idempotency behaviours.** These are N6 (session scope, PL:461) and the table at
  PL:451-453 behind N1 and N4. They carry no RFC keyword, but they define what "MUST support the key" (PL:439) means.
  **Recommend** CAPABILITY.
- **D3. N5 (keys not echoed, PL:459).** This is declarative ("doesn't echo"). It is not a MUST, so per the
  `ACP-SUBAGENT-013` precedent **recommend** ADVISORY.
- **D4. Optional rows N8 and N9.** Both are observable and spec-defined, but they are low value and N9 depends on optional
  request cancellation. N8 sends the same key with a different prompt, which the PL:444 client MUST NOT forbids, but the
  agent's answer is defined. **Recommend** adding N8 and deferring N9 (or making N9 a branch of N4's test).
- **D5. `ACP-CANCEL-209`/`213` and "only the Agent knows which work a request belongs to"** (PL:1452). The rows infer
  that a permission request during the prompted turn that does not reference a listed background item belongs to the
  cancelled foreground work. **Recommend** keeping that inference, which already held at base, and noting the new
  sentence in the row text.
- **D6. N12's deadline.** PL:755 names no time limit. **Recommend** CAPABILITY, judged by the end of the second turn
  plus `quiet_period`. The alternative is ADVISORY.
- **D7. N16 against agents without cursor support.** PL:999 makes `-32602` mandatory for any `cursorId` the agent did not
  issue. That means a fork-capable agent built on an older schema, which ignores the field and forks the whole session,
  FAILs. **Recommend** CAPABILITY on `capabilities.session.fork`, as the text says.
- **D8. RFD citations to drop.** These are `rfds/v2/prompt.mdx:88` (PROMPT-209, INFO-CONCURRENT-201) and
  `rfds/v2/background-work.mdx` (STATE-209, STATE-210, PATCH-211, and PATCH-211's text). They are now Draft and the docs
  state the rules. Subagents RFD citations become (Preview RFD); re-mapping those lines and adding the SA citations
  belongs to the subagents researcher. **Recommend** dropping the Draft ones.

## Follow-ups (not rows)

- **Stale base line numbers in code docstrings and comments.** No test checks these. They appear in `test_background.py`,
  `test_cancel.py`, `test_patches.py`, `_helpers.py`, `_child_cancel.py`, `test_prompt*.py`, `test_informational.py`,
  `test_session_capabilities.py`, `tests/v2/test_run_prompt.py`, `tests/fixtures/agents/v2/*.py`, and some bare `(:NNN)`
  forms. Apply the offset table. The changed spots are `:1177` -> 1452, `:384` -> 402-404, and `:382-384` -> 400-404.
- **`spec-tracker/maps/v2.toml:42` comment.** The heading is now "Session-directed messages", with no "(unstable)". The
  new standalone subsections "Prompt suggestions (unstable)" and "Session cursors (unstable)" are outside the core
  sections (inclusion-only list), which is fine. "Retrying a prompt" falls under the core "2. Prompt accepted".
- **Cross-check.** The upstream SDK agents probably don't support `idempotencyKey` or `$/cancel_request` on cancel yet.
  N1-N7, N16 and D1 may move baselines. I have not verified this: the SDKs were not consulted.
