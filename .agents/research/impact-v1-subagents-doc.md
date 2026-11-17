# Impact research, v1: new `docs/protocol/v1/draft/subagents.mdx` (3961af94 -> 3ea94133)

**Sources checked:** spec repo `agent-client-protocol-2` @ `3ea94133` (files read with `git show 3ea94133:<path>`;
the checkout's HEAD `6ace4f6a` has no diff from the target in `docs/protocol/v1/draft/` or `docs/rfds/subagents.mdx`):
`docs/protocol/v1/draft/subagents.mdx` (whole, 550 lines), the linked parts of `prompt-turn.mdx`, `tool-calls.mdx`,
`initialization.mdx`, `error.mdx`, `schema.mdx` (SubagentUpdate, SubagentSessionCapabilities, SessionMessage,
SessionReference), `schema/v1/schema.unstable.json` (base and target), `docs/rfds/subagents.mdx` (base and target)
and its stage in `docs/docs.json`. TCK @ `ceef9a8`: `src/tck/v1/requirements.py`, `spec-tracker/maps/v1.toml`,
`src/tck/v1/conformance/{test_subagents,test_subagent_controls,_child_cancel,_subagents_connection,_helpers}.py`.
Reference SDKs not consulted: the doc settles every question below explicitly or leaves it unobservable.

**Stages at target:** the doc is under "Protocol > v1 > Draft: In Progress and May Change". `docs/rfds/subagents.mdx`
is **Preview** (was Active), so every RFD label `(Active RFD)` becomes `(Preview RFD)`. The RFD's revision history
says the v1 rules now live on the doc (`docs/rfds/subagents.mdx:1698 @ 3ea94133`), so docs precedence applies to every
subagent rule the doc states. `docs/rfds/session-fork.mdx` is **Draft**.

**Schema:** every subagent `$def` (`SubagentUpdate`, `StateUpdate`, `IdleStateUpdate`, `UnknownStateUpdate`,
`SessionMessage`, `SessionMessageChunk`, `SessionReference`, `SubagentSessionCapabilities`, `SubagentCapabilities`)
is structurally identical at base and target; only descriptions changed (doc links, and `UnknownStateUpdate` now
also says unfinished tool calls and terminals stay as last reported).

**Confidence:** high for the classification and the citations. Medium for the proposed new rows, which need user
decisions on tier, probe method and harness cost.

Citations below are `path:lines @ 3ea94133` unless marked base. `SA` = `docs/protocol/v1/draft/subagents.mdx`,
`RFD` = `docs/rfds/subagents.mdx` (Preview RFD at target).

## 1. Registry rows (`src/tck/v1/requirements.py`)

Tier rule applied: a doc MUST about what an agent that *exposes* subagents does is `CAPABILITY` behind
`inferred:subagents`. The `subagents` client capability is the TCK's own advertisement and does not opt the agent in
(`SA:10` "Exposing subagents is optional for Agents", `SA:63` "There is no Agent capability"). Rows that were
CAPABILITY only because of the RFD cap could now be MANDATORY instead (see D1). Every such row is marked "tier could
rise" below.

| id | classification | target citation | note |
|---|---|---|---|
| ACP-CLIENTCAP-007 | citation-only | `SA:61` (MUST NOT + `session` content), `SA:530` (replay to a non-subagents client), `initialization.mdx:308-313`, `prompt-turn.mdx:19-21,44`, `tool-calls.mdx:358`; RFD `76-78,663-664` (Preview RFD) as secondary or dropped | MANDATORY unchanged. Base `prompt-turn.mdx:42` is now `:44`. The `session` content clause has no RFC keyword in the doc (`SA:61` second sentence, `tool-calls.mdx:358`), see D9. |
| ACP-SUBAGENT-001 | changed text (+ possible scope change, D2) | `SA:90-97` (MUST, list includes fs/terminal/elicitation), `SA:212`, `SA:517` (rule applies again on every load or resume, ancestors first), `SA:531` (a child's `subagent_update` precedes its other replayed updates), `SA:533`, `SA:534` (recorded `session_message` participants replayed even when unavailable); `schema.mdx:9709-9715`; schema pointer unchanged; RFD `95-99,189-193,970-972,979-986,1018-1024` secondary | The text's "Stated by the draft docs' `SubagentUpdate` and the Subagents RFD (Active RFD)" and the three "(Active RFD)" replay justifications are now doc-stated (`SA:517,531,534`). Tier could rise (D1). |
| ACP-SUBAGENT-002 | changed text (citation, + discrepancy D3) | `SA:90,94` (MUST: announcement precedes a `session` content item that references the child), `tool-calls.mdx:349-352`; RFD `647-650` secondary | Now a doc MUST, not just "must already be known". The row's replay exemption cites the RFD (`RFD:649-650`). The doc gives no such exemption for `session` content (see C1/D3). Tier could rise (D1). |
| ACP-SUBAGENT-003 | changed text | `SA:144` ("cannot ... name its own outer session as the child"); RFD `165-169` secondary | No longer "Stated only by the Subagents RFD ... capped". Doc wording is "cannot" (no keyword), as was the RFD's. Tier could rise (D1). |
| ACP-SUBAGENT-004 | changed text | `SA:99-102` ("unique on the connection ... **MUST NOT** reuse it for an unrelated session"), `SA:144` (cycle); RFD `122-124,165-169` secondary | No longer RFD-only. Tier could rise (D1). |
| ACP-SUBAGENT-005 | changed text | `SA:88` (later updates "do not ... move the child to another parent"), `SA:144`, `SA:531` (replayed child updates keep "their known parent"); `schema.mdx:9705-9707`; RFD `165-169` secondary | "the RFD states the one-parent, no-cycle rule" becomes doc-stated. The judge already keeps `parents` across the `session/load` range (`_helpers.py:941-962`), so it covers `SA:531`'s "known parent" on this connection. Tier could rise (D1). |
| ACP-SUBAGENT-006 | citation-only | `SA:232` (MUST absolute); `schema.mdx:9741,9760`; schema pointers unchanged; RFD `302-308` secondary | Base `schema.mdx:8741,8760` -> `9741,9760`. The text already says "The draft docs state the rule". |
| ACP-SUBAGENT-007 | citation-only (label) | RFD `485-488` (Preview RFD) | **Not stated by the doc** (`SA:320-330` only says what each ID names, and `SA:278` that messages can go between "other known sessions"). Still RFD-only, CAPABILITY cap stands. |
| ACP-SUBAGENT-008 | citation-only (label) | RFD `485-489` (Preview RFD) | Not stated by the doc. Still RFD-only. |
| ACP-SUBAGENT-009 | citation-only (+ doc secondary) | RFD `466-475` (MUST at `471-473`, Preview RFD); `prompt-turn.mdx:98-102`; `schema.mdx:8150,8164`; add `SA:285` (SHOULD link the two views) | The MUST that both references agree is still RFD-only. The doc adds only the SHOULD to link the views. |
| ACP-SUBAGENT-011 | citation-only | `prompt-turn.mdx:108-113`, add `SA:286` (SHOULD NOT `user_message_chunk`); RFD `685-690` secondary | ADVISORY unchanged. |
| ACP-SUBAGENT-012 | citation-only | `prompt-turn.mdx:108-113`, add `SA:284` (SHOULD incoming view, sender = parent, "before the child's response to it"); RFD `669-676` secondary | ADVISORY unchanged. |
| ACP-SUBAGENT-013 | unchanged w.r.t. this doc | `prompt-turn.mdx:48-52`; RFD `461-464` (Preview RFD) | The doc does not restate it. Remapping prompt-turn belongs to the prompt-turn researcher. |
| ACP-SUBAGENT-014 | changed text | `SA:273` (SHOULD limit select values to the current one), `SA:272` and `SA:427` (no capability permits `set_config_option`; `cancel` is the only one); RFD `407-419` secondary | "Stated only by the Subagents RFD (Active RFD), so the row is ADVISORY" becomes "the draft docs state it as a SHOULD". ADVISORY unchanged. |
| ACP-SUBAGENT-015 | citation-only | schema pointers unchanged (structurally identical); add `SA:356-372,382` (state values, `error`); RFD `841-855` secondary | |
| ACP-SUBAGENT-016 | changed text + **test change (D4)** | `SA:423,435` (cancel only while `capabilities.cancel` is an object), `SA:449` (stop, send pending updates, confirm `idle` + `cancelled` on the parent's `subagent_update`), `SA:450` (report `unknown` if it can no longer observe), `SA:451` (late cancel does not change the outcome), `SA:379`; `schema.mdx:9694`; RFD `1113-1117,1133-1145` secondary | The confirmation is no longer RFD-only. `SA:449` has no RFC keyword, as before. Keep CAPABILITY `inferred:subagentCancel`. Test gap: `SA:450` allows `unknown` instead of a confirmation, which `_child_cancel.py` currently scores `unconfirmed` (FAIL). |
| ACP-SUBAGENT-017 | changed text | `SA:447` ("not the work of its parent or siblings ... The Agent can cancel work it delegated at any time"); RFD `1113-1117` secondary | No longer RFD-only. Sibling non-judgement now rests on `SA:447`. CAPABILITY unchanged. |
| ACP-CLIENTCAP-001/002/003 | optional citation addition | `SA:95,157` | They already judge `fs/*`, `terminal/*` and `elicitation/create` carrying a child's ID on the subagents connection, but cite no subagents source. `SA:157` ("pass through the same Client capabilities") backs that clause. MANDATORY unchanged. |

**Prompt-turn citation remaps seen while checking (prompt-turn researcher owns them):** base `prompt-turn.mdx:42`
-> `44`, `46-50` -> `48-52`, `96-100` -> `98-102`, `106-111` -> `108-113`. Base `schema.mdx:8694` -> `9694`,
`8705-8713` -> `9705-9715`, `8741,8760` -> `9741,9760`, `7249,7263` -> `8150,8164`.

## 2. Ledger entries (`spec-tracker/maps/v1.toml`, `# --- subagents ---` block)

The block header should become `# --- subagents (docs/protocol/v1/draft/subagents.mdx; docs/rfds/subagents.mdx, Preview RFD) ---`.

| base citation | classification | target citation | note |
|---|---|---|---|
| RFD `322-326` (dir differs before dependent traffic, MUST; SHOULD NOT share) | citation-only | `SA:253-254,256` | Reason sound. |
| RFD `381-382,387-390` (narrowest; reconnect values; gone dir) | citation-only | `SA:255,521` | Reason sound. |
| RFD `198-199,939-940` (no guessed parentage) | citation-only | `SA:152,533` | Reason sound. |
| RFD `203-206` (unexposed ops not moved; exposed child uses its ID) | citation-only | `SA:153-154` (`SA:462` restates "MUST NOT move" for pending requests) | Reason sound. |
| RFD `223-226` (automatic delivery) | citation-only | `SA:161` | Reason sound. |
| RFD `576-577` (each side only when observed) | citation-only, primary moves to **prompt-turn** | `prompt-turn.mdx:102-104`; RFD `584-585` secondary | Not stated in `SA`. prompt-turn states it for the Agent ("reports each side only when observed"). The "manufacture" half is RFD `584-585`. |
| RFD `831-841` (running/idle MUST, requires_action/stopReason SHOULD) | citation-only | `SA:374-376` | Reason sound. |
| `UnknownStateUpdate`; RFD `855-860` (report `unknown`) | citation-only | `SA:410`; schema pointer unchanged | Reason sound. `SA:414-415` are new, separate rules (N5). |
| RFD `1117-1121` (close cascades) | citation-only | `SA:475,478` | Reason sound. |
| RFD `1151-1153` (late response) | citation-only | `SA:470` | Reason's internal pointer ":1126-1128" (client MUST respond `cancelled`) becomes `SA:466`. |
| RFD `999-1001` (replay does not reissue requests) | citation-only | `SA:537` | Reason sound. |
| RFD `942-949` (replayed message: no invented IDs) | citation-only | `SA:534` | Reason's pointer ":945" becomes `SA:534` ("can still be replayed ... even when the other participant's association or history is unavailable"). |
| RFD `1024-1028` (no invented outcomes) | citation-only | `SA:520` | Reason sound. |
| RFD `1168-1170` (no fabricated exclusive cost) | **removed** | none | The RFD deleted its "Cost reporting without inferred aggregation" section (now "Cost covers descendant sessions", `RFD:1205-1228`). The doc states the opposite model (`SA:544`). Delete the entry and replace it with N11. |
| RFD `439-441` (`messageId` unique per transcript) | citation-only, docs primary | `SA:210`, `prompt-turn.mdx:46-48`, `schema.unstable.json#/$defs/SessionMessage/properties/messageId`; RFD `439-441` secondary | Reason sound. |
| RFD `361-363` (explicit `cwd` on child `terminal/create`, SHOULD; Deferred) | citation-only | `SA:265` | Its reason names a TCK limitation (mock client has no `terminal`), but it is marked "Deferred" and names the blocker and what unblocks it, which is the allowed form. No change. |

No other existing ledger reason in this block rests on a TCK choice.

## 3. New requirements (doc rules no row covers)

**R1. `ACP-SUBAGENT-0xx` (provisional `-018`): a non-permitted Client request for a child is rejected with `-32602`.**
- Text: for an announced child, a Client request that is not permitted for a child (anything but `session/cancel`
  while `capabilities.cancel` is an object, and responses) is answered with JSON-RPC error `-32602`. Names
  `session/close` and `session/delete`, "which do not report success for a child".
- Tier: ADVISORY (`SA:428` "**SHOULD** reject ... with `-32602`"). Optional split per the error-code policy: a
  CAPABILITY row that `session/close`/`session/delete` for a child is an error, not a success, because `SA:428` states
  "do not report success for a child" declaratively. Gates would be `agentCapabilities.sessionCapabilities.close` /
  `.delete` with a self-skip when no child was announced (D5).
- Citation: `SA:419-428`; `error.mdx:57` (same SHOULD; coordinate with the error.mdx researcher so there is one row);
  RFD `1093-1096` (Preview RFD) secondary.
- Probe: the request breaks the Client MUST NOT at `SA:419,425,475` (close). The [probe rules](../../docs/writing-tests.md#probes)
  allow that because `SA:428` defines the agent's answer to exactly this input. The row text and docstring must say so.
- Test: on the subagents connection, after its last quiet period, take a child announced on a known session. Send
  `session/close` (if `sessionCapabilities.close`) or `session/delete` (if `.delete`) with the child's `sessionId`, and
  assert an error with code `-32602`. Fallback when neither is advertised: `session/set_mode` or `session/prompt`
  (D5). SKIP when no child was announced or no probe method applies.
- Harness: `_subagents_connection._run` needs a final probe step, after everything the other rows judge, with the
  response stashed in `SubagentsConnection`. No mock-client change.

**R2. `ACP-SUBAGENT-0xx` (provisional `-019`): `session/list` does not return child sessions.**
- Tier: CAPABILITY, `capability="agentCapabilities.sessionCapabilities.list"` (real marker), with a self-skip when no
  child was announced. `SA:430` is declarative ("does not return child sessions"). The alternative is ADVISORY (D6).
- Citation: `SA:430`; RFD `1098-1100` (Preview RFD) secondary.
- Test: on the subagents connection after the turn (and load), call `session/list`, following `nextCursor` up to a
  small page cap. FAIL if any `sessions[].sessionId` equals a child announced on the connection. SKIP when no child
  was announced.
- Harness: one more step in `_subagents_connection._run`, gated on the list capability, with the pages stashed.

**R3. `ACP-SUBAGENT-0xx` (provisional `-020`): child state and stop-reason values are protocol values or `_`-prefixed.**
- Text: every `subagent_update.state.state` is `running`, `idle`, `requires_action`, `unknown` or begins with `_`. An
  idle `stopReason` is a v1 `StopReason`, `error`, or begins with `_`. Other values are reserved for the protocol. The
  schema's `other` variants accept any string, so `ACP-SUBAGENT-015` cannot catch this.
- Tier: ADVISORY (no RFC keyword). Precedent: `ACP-AUTH-008` (D7).
- Citation: `SA:365,380`; `schema/v1/schema.unstable.json#/$defs/StateUpdate`,
  `#/$defs/IdleStateUpdate` (the `other` variants' descriptions); RFD `916-921` secondary.
- Test: pure transcript check over the existing subagents connection. SKIP when no `subagent_update` carries a
  string `state.state`. No harness change.

**R4. `ACP-SUBAGENT-0xx` (provisional `-021`): forking a parent remaps copied session IDs.** (alternatively a Deferred
ledger entry, D8)
- Text: if forking a parent copies child history, the replay of the fork names no copied session by its original ID.
  No `session_message` participant and no `session` content item names the source session (the "forked root"), and
  no replayed `subagent_update` re-announces a child announced under the source tree with its original ID.
- Tier: CAPABILITY, `capability="agentCapabilities.sessionCapabilities.fork"`, also needing `loadSession`, with a
  self-skip when the fork's replay copies no child history (no `subagent_update`, `session_message` or `session`
  content). `SA:486` is a MUST.
- Citation: `SA:484-490`; RFD `1102-1107` secondary. `session/fork` itself is defined by the schema
  (`schema.mdx:706-721`) and the Draft `rfds/session-fork`.
- Test: on the subagents connection, after the turn that announced children: `session/fork` the parent, then
  `session/load` the fork, then judge the load range. Sessions outside the copied tree may still appear as
  unavailable participants (`SA:489`), so only the source root and children announced under it are judged.
- Harness: a fork + load step on the subagents connection (new). This is the most expensive proposal.

**Coverage extension, not a new row (D11):** `SA:517` applies the announcement rule to `session/resume` too. v1's
subagents connection only exercises `session/load`. An optional extension of `ACP-SUBAGENT-001`'s scope would add a
resume step, gated on `sessionCapabilities.resume`. Treat it as a follow-up.

## 4. New ledger entries

Each is agent-side, cited from the doc, and none rests on a TCK choice.

| # | citation | statement | reason |
|---|---|---|---|
| N1 | `SA:157` | Requests the Agent sends for a child pass the same Client capability and permission checks as the parent's, and the Agent does not use a child to get around a restriction the Client placed on the parent session (MUST NOT). | Not observable beyond capability gating: whether a child's activity circumvents a parent restriction depends on the Agent's internal routing and agent-local tools, which the client never sees. Capability-gated `fs/*`/`terminal/*`/`elicitation/create` with a child's ID are judged by ACP-CLIENTCAP-001..003. |
| N2 | `SA:269,522` | Agents report a child's configuration with `config_option_update` on the child after the announcement, on every change, and for a restored child after load or resume, when it is available (SHOULD). | Unobservable: whether a child's configuration is available, or changed, is known only to the agent. |
| N3 | `SA:285` | When the parent's conversation also records a message to a child, Agents report the outgoing view in the parent's transcript and link the two views (SHOULD). | Unobservable: whether the parent's conversation records the message is internal. Links that are reported are judged by ACP-SUBAGENT-009. |
| N4 | `SA:287`; `prompt-turn.mdx:115-118` | When the Agent has no evidence of who sent a message the child received, it omits `senderSessionId` and does not assume the parent (MUST NOT). | Unobservable: the agent's evidence is internal, and a message correctly attributed to the parent looks the same as an assumed one. |
| N5 | `SA:414-415`; `schema.unstable.json#/$defs/UnknownStateUpdate` | After reporting `unknown`, the Agent does not invent a final status for the child's unfinished tool calls or terminals (MUST NOT), and sends new `capabilities` if a capability is no longer available. | Not observable as a violation: a final status after `unknown` is correct once the agent learns the work ended (`SA:415`), and what it learned, and which capabilities remain available, is internal. |
| N6 | `SA:428` (first sentence) | The Agent ignores a `session/cancel` for a child that does not advertise `cancel`. | Not observable: the Agent may cancel delegated work at any time (`SA:447`) and a child may stop on its own, so an `idle`/`cancelled` after such a notification cannot be attributed to it. |
| N7 | `SA:454` | Cancelling a session's work also cancels the descendant work the cancelled work is waiting on, including a child that does not advertise `cancel`. | Unobservable: which descendants the cancelled work waits on is internal to the agent, and other descendants may legitimately keep running. |
| N8 | `SA:449-450` | On a child cancel the Agent stops the work and sends its pending updates before confirming, and reports `cancelled` only once it observes the work stopped, not on acceptance of a provider stop command. | Unobservable: which updates were pending, and when the provider actually stopped, are internal. Later updates for those tool calls are allowed (`SA:458`). The confirmation itself is judged by ACP-SUBAGENT-016. |
| N9 | `SA:518` | After a load or resume the Agent reports each child's current state when it can determine it (SHOULD). | Unobservable: whether the agent can determine a child's current state is internal. |
| N10 | `SA:528,536` | `session/load` also replays the associations and child history the Agent still has (SHOULD), and the Agent reports known gaps, for example with a notice (SHOULD). | Unobservable: what history the agent still has, and which gaps it knows of, are internal. |
| N11 | `SA:531,535` | Replayed child updates keep their original `sessionId` and their order within each session (MUST), all history selected for the replay is sent before the response (MUST), and recorded child state is not sent after the response as if it were current. | Not observable: replay may come from reconstructed transcripts rather than the original wire chunking, and the selection is internal. After the response, recorded child state cannot be told from live state. The known parent and announcement order are judged by ACP-SUBAGENT-005 and -001. |
| N12 | `SA:544`; `prompt-turn.mdx:736` | A session's reported cost includes its descendants' costs, and a root session's cost is the Agent's total for the whole tree. | Unobservable: the true cost is unknown to the client, and a descendant's cost may reach its ancestors later (`SA:544`), so no snapshot comparison proves a violation. |

R4 as a ledger entry instead (if the user declines the row): `SA:486`, "If forking a parent copies child history, the
Agent remaps the copied session IDs consistently in `session_message` participants and `session` content, including
references to the forked root (MUST)". Reason: "Deferred: observing it needs a `session/fork` of a parent with
announced children followed by a `session/load` of the fork. It would be unblocked by a fork + load step on the
subagents connection, gated on `sessionCapabilities.fork` and `loadSession`."

Not ledgered, because they bind the client, are pure MAYs, or are descriptive: `SA:133-138`, `161` (client half),
`226`, `263-264`, `271`, `273` (client half), `274`, `412`, `415` (client half), `419`, `424`, `456-458`, `466-468`,
`470` (single response), `475` (client), `484`, `494-496`, `500-513`, `534` (client half), `547`. `SA:462` ("MUST NOT
move to the parent") is covered by the existing `SA:153-154` entry.

## 5. Conflicts between doc and RFD

- **C1. Replayed `session` content.** `RFD:649-650` exempts a replayed reference to an unavailable session ("follows
  the historical replay rules"). The doc's announcement MUST lists `session` content items with no replay exemption
  (`SA:90,94`), says the rule "applies again on every load" (`SA:517`), and exempts only recorded `session_message`
  participants (`SA:534`). Docs win on a conflict, but this is silence rather than contradiction. See D3.
- **C2. Child item cancel methods.** `RFD:1081-1084` lets a child's tool call or terminal with its own
  `capabilities.cancel` enable `tool_call/cancel`/`terminal/cancel`, without version qualification. The v1 doc says
  `cancel` "enables `session/cancel` and nothing else" and every other request is not permitted (`SA:425,427`). Neither
  method exists in the v1 schema (`schema.unstable.json`, `schema.mdx` @ 3ea94133), so there is no v1 impact.
  Recorded only.
- **C3. "Live" qualifier.** The schema (`schema.mdx:9711`) and `RFD:97` scope the announcement rule to *live*
  messages. `SA:93` drops "live", but `SA:534` restores the replay carve-out for `session_message`. The effect is the
  same.
- **RFD-only rules that the doc does not restate** (not conflicts; the RFD researcher owns them): both IDs differ and
  the outer ID matches one (`RFD:485-489`, rows 007/008); references "MUST name each other" (`RFD:471-473`, row 009);
  "SHOULD supply each reference once they know it" (`RFD:471-472`); "SHOULD NOT report an outgoing view for a send ...
  failed" (`RFD:587-588`); "MUST NOT guess the session" for handles (`RFD:661`; `tool-calls.mdx:364-365` says it
  without a keyword); the idle `usage` field (`RFD:852-853`, in the schema, not in the doc).
- Cost: the doc and the RFD now agree (`SA:542-550`, `RFD:1205-1228`).

## 6. Decisions for the user

- **D1. Tier of doc-MUST subagent rows (001-006, 016, 017).** Recommend keeping CAPABILITY with
  `inferred:subagents` / `inferred:subagentCancel`. The rules bind only an agent that exposes subagents, and that
  opt-in is behavioural (`SA:10,63`). In verdict terms MANDATORY-with-SKIP is equivalent (a SKIPPED MANDATORY row does
  not break conformance). Only the rows' "stated only by the RFD ... capped" wording must change to "the draft docs
  state it; binds only an agent that exposes subagents". 007, 008 and 009 stay capped (still RFD-only).
- **D2. `ACP-SUBAGENT-001` after a load.** `SA:517` requires every ancestor of a child to be announced *during this
  load or resume* before live traffic for it. `_wire_messages_indexed` (`_helpers.py:676-720`) goes back to the `live`
  set after the load range, which counts announcements from the earlier turn. Recommend tightening, so that traffic
  after the load response is judged against the set scoped to the load exchange. The connection already drains before
  the load, so trailing child traffic from the turn is not misread. This changes the row text and the helper.
- **D3. `ACP-SUBAGENT-002` replay exemption (C1).** Recommend keeping it, citing `RFD:649-650` (Preview RFD) as the
  basis, recording the discrepancy in the row text, and treating a replayed `session` reference like the replayed
  `session_message` participants of `SA:534`. The alternative is to judge replayed references against announcements
  made within the load, which is stricter and follows a literal docs-win reading.
- **D4. `ACP-SUBAGENT-016` and `unknown`.** `SA:450` allows `unknown` instead of `idle`/`cancelled` when the agent
  loses sight of the child. Recommend a new `_child_cancel` outcome: a `unknown` snapshot after the cancel SKIPs
  ("cancellation not observable: the child reported `unknown`"), not FAIL. A later `idle`/`cancelled` still confirms.
- **D5. R1 shape.** Recommend one ADVISORY row (`-32602` for a non-permitted child request), probing `session/close`
  or `session/delete` when advertised (the doc names both, and a wrongly accepted probe is harmless at the end of the
  connection). Optional: a CAPABILITY companion row for "do not report success" on close/delete. Decide whether to
  fall back to `session/prompt`/`session/set_mode` when neither is advertised; recommend no, SKIP instead, because an
  accepted prompt starts child work. Coordinate with the `error.mdx:57` researcher so only one row exists.
- **D6. R2 tier.** CAPABILITY (gate `sessionCapabilities.list`, recommended, since the doc is declarative and the rule
  is unambiguous) vs ADVISORY (no RFC keyword).
- **D7. R3.** ADVISORY, following `ACP-AUTH-008`.
- **D8. R4.** A row (needs a new fork + load harness step) vs a Deferred ledger entry. Recommend the Deferred entry
  for this update, because the fork path has no other v1 coverage to build on.
- **D9. `ACP-CLIENTCAP-007` `session` content clause.** The doc states it without a keyword (`SA:61`,
  `tool-calls.mdx:358`), while the MUST NOT in the same paragraph covers the three update kinds. Recommend keeping
  MANDATORY: the doc presents it as part of the same capability gate, and `initialization.mdx:308-313` defines the
  capability as what the client handles.
- **D10. Cost ledger entry removal** (RFD `1168-1170`). Delete it and add N12. The rule no longer exists.
- **D11. Resume coverage for `ACP-SUBAGENT-001`** (`SA:512,517`). Recommend a follow-up, not this update.
