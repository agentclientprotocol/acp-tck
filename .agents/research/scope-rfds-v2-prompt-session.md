# Scope: testing the formerly-Active v2 RFDs `overview`, `prompt`, `required-session-methods`, `session-resume-replay` in v2

**Sources checked:** agent-client-protocol (`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`) @ target
`3ea94133bb4e7cfdb1105df75660ff83e66acf62`, diffed against base `3961af94`: `docs/rfds/v2/{overview,prompt,required-session-methods,session-resume-replay}.mdx`,
`docs/docs.json`, `docs/protocol/v2/draft/{prompt-lifecycle,session-setup,initialization,overview,transports,cancellation,elicitation,session-config-options}.mdx`,
`schema/v2/schema{,.unstable}.json` (`2.0.0-alpha.16`). acp-tck @ `ceef9a8`: `src/tck/v2/requirements.py`,
`spec-tracker/maps/v2.toml`, `src/tck/v2/conformance/test_patches.py`, `docs/requirements.md`, `docs/spec-updates.md`.
Reference SDKs not consulted: every rule below is stated in the v2 draft docs or schema, so there was no runtime gap to fill.
**Confidence:** high. Each RFD rule was matched line by line to a docs/schema statement at the target. The only judgment
calls are how to count the overview RFD's change list and whether to keep the Draft RFD as secondary context.

## Answer

The answer is close to zero TCK work. All four RFDs are **Draft** at the target. They sit under the `Draft > v2` group,
`docs/docs.json:200,208-226 @ 3ea94133`; at base they were under `Active > v2`, `docs/docs.json:211,217 @ 3961af94`.
Every agent-side normative rule they state is also stated by the v2 draft docs or the v2 schema at the target, so by the
docs-precedence rule each one belongs to the doc audit. None is RFD-only, so there are no RFD-only rows to add and no
RFD-only ledger entries. Citing these Draft RFDs is **not** justified under "cite Draft RFDs only where nothing else
states the rule".

The only RFD-driven change is citation cleanup. Two existing rows cite `docs/rfds/v2/prompt.mdx:88 (Active RFD)`:
`ACP-PROMPT-209` and `ACP-INFO-CONCURRENT-201`. Drop that secondary citation, because the docs state the rule at
`prompt-lifecycle.mdx:400-407`. If it is kept, relabel it `(Draft RFD)`.

Effort is **S**: 0 new rows, 0 fixtures, 2 citation edits. The docs-stated but uncovered rules found along the way are
listed below so the doc auditors can confirm they are already on their lists.

## Requirements

Abbreviations, all `docs/protocol/v2/draft/… @ 3ea94133`: PL = `prompt-lifecycle.mdx`, SS = `session-setup.mdx`,
INI = `initialization.mdx`, OV = `overview.mdx`, TR = `transports.mdx`, CN = `cancellation.mdx`, EL = `elicitation.mdx`,
SCO = `session-config-options.mdx`. Schema = `schema/v2/schema.unstable.json`. The "Docs tier" column is the tier the docs
give. These are not proposed RFD tiers: no RFD-only rule exists.

### `docs/rfds/v2/prompt.mdx` (Draft RFD; unchanged since base)

| # | RFD rule (RFD line) | Docs tier | Docs/schema statement | Existing coverage |
|---|---|---|---|---|
| P1 | MUST respond successfully once inserted, without waiting for foreground work (45) | MUST | PL:341 | ledger `v2.toml:168-171` (unobservable) |
| P2 | MUST NOT send a successful response before insertion (45) | MUST | PL:339,341 | none (doc audit; looks unobservable, since insertion is internal) |
| P3 | Response carries `messageId`, a non-null string (45, 360) | MUST | PL:356-359; Schema `PromptResponse/required` | ACP-PROMPT-201 |
| P4 | Rejection before insertion is a JSON-RPC error, with no user-message update (45) | MUST | PL:413 | ACP-PROMPT-207, ACP-PROMPT-211 |
| P5 | A locally handled command inserts a live-only user message (47, 397-399) | declarative | PL:343,386; SS:294-295 | ledger `v2.toml:501-504` (unsafe) |
| P6 | Distinct `messageId` per accepted submission, even with identical content (72) | MUST | PL:384 | ACP-PATCH-203 (its test sends identical text, `test_patches.py:108-131`) |
| P7 | A user-message ID MUST NOT be reused for a different submission; IDs are unique per entity type (72) | MUST NOT | PL:68-70 | ACP-PATCH-203 (partial) |
| P8 | All updates and chunks for the message use the returned ID (74, 159) | MUST | PL:362 | ACP-PROMPT-203 |
| P9 | Each inserted user message is reported via `user_message`/`user_message_chunk` (86) | MUST | PL:362 | ACP-PROMPT-203 |
| P10 | A prompt sent during active work is not rejected; it is inserted, or held and inserted in order (88) | declarative | PL:400-405 | ACP-PROMPT-209, ACP-INFO-CONCURRENT-201; ledger `v2.toml:173-176` |
| P11 | Retaining history is not required (160) | non-req | PL:386; SS:241-244 | RESUME-204/202 treat absence as conforming |
| P12 | A retained message that is replayed reuses the returned ID (161) | MUST | PL:386; SS:292-294 | ACP-RESUME-204 |
| P13 | Chunked replay of a user message is preceded by `user_message` with `content: []` (186) | MUST | SS:307-312 | ACP-RESUME-205 |
| P14 | New session defaults to idle; resume sends a state snapshot after replay and before the response, even without replay (261-263) | MUST | PL:1322-1330; SS:344-346 | ACP-RESUME-206 |
| P15 | Starting foreground work reports `running`/`requires_action`; resumed progress reports `running`; ending reports `idle` (264-267) | MUST/SHOULD | PL:162-164,1346-1349 | ACP-STATE-201, -202, -205 |
| P16 | Background permissions and elicitations do not change idle (268-270) | declarative | PL:184 | none (doc audit) |
| P17 | A local command handled from idle reports an active state and then `idle` (273-274) | declarative | PL:1421 | ledger `v2.toml:501-504` |
| P18 | Cancellation ends foreground work with `idle(cancelled)`; the cancelled stop reason is required (276, 285) | MUST | PL:1365-1366; CN:42-45 | ACP-CANCEL-001 |
| P19 | Pending permissions are resolved on cancel (275) | MUST | CN:42; PL:1453 | ACP-CANCEL-209, ACP-CANCEL-213 |
| P20 | Cancel individual elicitations the work no longer needs (276-278, **should**) | **MUST** in docs | EL:225-228 | doc audit (tightened by #2852; see Discrepancies) |
| P21 | Held / not-yet-inserted prompts get `-32800` on cancel (279-280) | declarative | PL:404 | ACP-CANCEL-214 |
| P22 | Ignore late answers after cancellation completes (280-281) | SHOULD | PL:1457; CN:42 | ledger `v2.toml:650-652` |
| P23 | Repeated or resume snapshots cause no new cancellation; cancelling idle work needs no completion update (281-282) | declarative | PL:1357-1360,1430; CN:45 | ACP-INFO-CANCEL-201 |
| P24 | A failure after insertion MUST report `idle` and SHOULD carry `stopReason: "error"` plus an `error` object (291, 313) | MUST/SHOULD | PL:1242-1262 | ledger `v2.toml:320-321` (auth case only); general case: doc audit |
| P25 | After insertion, never answer `session/prompt` with an error; `$/cancel_request` gets `-32800` only before insertion (318) | MUST NOT | PL:341,413 | ACP-PROMPT-207, ACP-JSONRPC-007 |
| P26 | The idle update follows all updates of the work that ended (322) | MUST | PL:1076 | ACP-CANCEL-002 (cancel path) |
| P27 | Before a failure idle, give unfinished tool calls a terminal status (`failed`) (322) | SHOULD | PL:1271 | none (doc audit; needs a provoked failure) |
| P28 | `error` exists only on the `error` stop reason; it is a JSON-RPC error object (313-314) | schema | Schema `IdleStateUpdate`/`StopReason`, `Error`; PL:1263-1267 | schema validation in ACP-PROMPT-002 |

Totals: 28 rules. 21 are covered by docs plus an existing row or ledger entry. 7 are docs-stated but uncovered (P2, P16,
P20, P24-general, P27, and the partial P7/P26 aspects). 0 are RFD-only.

### `docs/rfds/v2/session-resume-replay.mdx` (Draft RFD; changed since base)

| # | RFD rule (RFD line) | Docs tier | Docs/schema statement | Existing coverage |
|---|---|---|---|---|
| R1 | `replayFrom` omitted or `null` means no history replay (38, 107) | MUST NOT | SS:181-186 | ACP-RESUME-002 |
| R2 | `{type:"start"}` replays all retained history before responding (49-51) | MUST | SS:214-216 | ACP-RESUME-202 |
| R3 | An unsupported cursor type is rejected with `-32602`, never substituted (53-56) | MUST | SS:218-221 | ACP-RESUME-207 |
| R4 | A malformed cursor is rejected with `-32602` (56-57) | declarative | SS:222 | ACP-RESUME-208 |
| R5 | Retention is optional; a retained user message keeps its insertion ID (59-61) | MUST | SS:241-244,292-294 | ACP-RESUME-204 |
| R6 | Replay uses the live update shapes and may send current state only (63) | MAY | SS:226-228 | ACP-RESUME-209 (schema validation) |
| R7 | **New since base (RFD line 65):** chunked rebuild of any entity starts with the chunked field emptied (message, `session_message`, tool-call content, terminal output, compaction summary) | MUST | SS:307-321 (table) | ACP-RESUME-205 covers only user/agent/thought message chunks; the four new entity kinds are a **doc-audit** extension |
| R8 | SHOULD preserve agent/thought message IDs, `toolCallId`, `terminalId`, `planId` across replay (67) | SHOULD | SS:297 | ledger `v2.toml:412-415` (citation `:289` must be re-mapped to `:297`) |
| R9 | Cursors are inclusive (71-73) | declarative | SS:196-197 | non-testable for `start` (no observable consequence) |
| R10 | Replay applies top-level `_meta` as a patch; stale keys are removed via `null` or `_meta: null` (96-99) | declarative | SS:330-335 | none (doc audit) |

Totals: 10 rules. 8 are covered (R1-R6, R8, R9 as a non-requirement). 2 are docs-stated but uncovered: the R7 extension
and R10. 0 are RFD-only.

### `docs/rfds/v2/required-session-methods.mdx` (Draft RFD; unchanged since base)

| # | RFD rule (RFD line) | Docs tier | Docs/schema statement | Existing coverage |
|---|---|---|---|---|
| S1 | With `capabilities.session`, MUST support `session/new`, `list`, `resume`, `close`, `prompt`, `cancel`, `update` (38-47) | declarative ("supplying `{}` means …supports") | INI:274-279,304-306; OV:60 | ACP-SESSION-001, ACP-LIST-001, ACP-RESUME-001, ACP-CLOSE-001, ACP-PROMPT-201/-002, ACP-CANCEL-*; the registry docstring (`requirements.py:13-19`) already gates the whole surface on `capabilities.session` |
| S2 | No `session.list`/`resume`/`close`/`load` markers in v2; `session/load` removed (49-52, 85) | schema | Schema `SessionCapabilities` (properties: `_meta, additionalDirectories, archive, delete, fork, mcp, options, prompt, status, systemPrompt, title`); no `LoadSessionRequest` | not an agent obligation (an extra key is an unknown field) |
| S3 | The remaining optional capabilities keep gating their features (54-64) | MAY | INI:308-310 and below | PROMPTCAP-, MCP-, DELETE-, ADDDIRS-, FORK- rows |
| S4 | Agents advertising config options support `session/set_config_option` (66-67, lowercase "must") | MUST | SCO:249; INI:312-313 | ACP-CONFIG-002 (`inferred:configOptions`) |

Totals: 4 rules. 4 covered (S2 as a non-requirement). 0 uncovered. 0 RFD-only.

### `docs/rfds/v2/overview.mdx` (Draft RFD; changed since base)

This is a tracking RFD. Its agent-side normative content is the "v2 Changes" list (lines 59-102). Each item links to a
docs page, to another v2 RFD (counted in that RFD's section, or out of scope here), or to a schema shape. Grouped:

| # | Item (RFD line) | Docs/schema statement | Existing coverage |
|---|---|---|---|
| O1 | No batches; reject an array with `-32600` (74) | TR:65-67; OV:21 | ACP-TRANSPORT-001, ACP-BATCH-209, ACP-JSONRPC-005 |
| O2 | A non-empty `authMethods` MUST implement `auth/login` + `auth/logout` (89) | OV:60 | ACP-AUTH-003, ACP-AUTH-004 (`inferred:authMethods`) |
| O3 | Baseline session methods when `session` is present (93) | = S1 | see S1 |
| O4 | `session/load` removed; `replayFrom` on resume (94) | = S2/R1-R2 | see S2, R1-R2 |
| O5 | `messageId` prompt receipt; `state_update`; error stop reason; `unknown` state (71-73) | = P1-P28; PL:1319 | see prompt section |
| O6 | Reject `initialize` with `-32022` plus `data` (82) | INI (`-32022` section) | ACP-INIT-205, ACP-INIT-207 |
| O7 | Required `info`; object-shaped capability markers (87-88, 96) | INI; Schema | ACP-INIT-004, ACP-INIT-204 |
| O8 | Optional `mcpServers`; typed MCP configs; `session.mcp.stdio` (85, 97-101) | SS; Schema | ACP-SESSION-203, ACP-MCP-201/-204 |
| O9 | Initial `configOptions`/`availableCommands` in setup responses (81) | SS (Initial Session State) | ACP-SESSION-208, ACP-RESUME-210 |
| O10 | Open enums; `_` prefix for custom values (75) | extensibility.mdx; PL:1238 | ACP-CANCEL-207, ACP-ENUM-201 |
| O11 | Message IDs on chunks; domain-specific ID names; `type` on config values; `groupId`; `usage_update.cost` patch; `cancelled` status; `plan_update` (63-70, 76, 83-84, 102) | Schema; PL:567 | schema-validation rows (ACP-PROMPT-002, ACP-SESSION-001, ACP-RESUME-209), ACP-PATCH-*, ACP-RESUME-205 |
| O12 | **New since base (78):** `replay_complete` marks the end of replay | SS:216,344-346,360ff | **none** (doc audit, session-setup) |
| O13 | **New since base (80):** `idempotencyKey` on `session/prompt` (MUST support; `-32602` for a malformed key) | PL:419-471 | **none** (doc audit, prompt-lifecycle; owned by the idempotency-keys work) |
| O14 | **New since base (49, 79):** subagents are baseline in v2 without a capability | `subagents.mdx` (v2 draft) | owned by the subagents doc audit |
| O15 | Background work (77) | PL (Background work) | ACP-STATE-206..210, TOOLCANCEL-, TERMCANCEL- (background-work RFD, out of scope) |
| O16 | "Agents should expose mode-like state through config options" (60, lowercase) | Schema (no modes API) | non-normative design note; no row |

Totals: 16 items. 13 are covered by docs plus rows (counting O3-O5 via their own RFD sections, O14-O15 via other owners,
and O16 as non-normative). 2 are docs-stated but uncovered (O12, O13). 0 are RFD-only.

## Details

**What changed since base.** All four RFDs moved from Active to Draft. Upstream removed the Active stage (inventory
`spec-diff-v2.md:10`, commit `199fa7d1`). The text changes:

- `overview.mdx`: the "Current Active RFDs" heading became "RFDs targeting v2" (27-29). The diff adds the Replay Complete
  and Idempotency Keys RFDs (44-45), the subagents-in-v2-Preview paragraph (49), and change-list items for `unknown`
  (72), `replay_complete` (78), subagents (79) and `idempotencyKey` (80), plus revision entries (140-144).
- `session-resume-replay.mdx`: the diff adds the MUST at line 65, which extends the chunk primer to every chunked entity,
  plus revision entries (116-117) and a typo fix (77).
- `prompt.mdx` and `required-session-methods.mdx`: no text changes (`git diff --stat 3961af94..3ea94133 -- docs/rfds/v2/`).

**Proposed changes (all citation hygiene, size S):**

1. `ACP-PROMPT-209`: drop `docs/rfds/v2/prompt.mdx:88 (Active RFD)`. PL:400-405 states the rule (re-map the base lines
   `prompt-lifecycle.mdx:382,384` as the doc audit does). If kept, it must read `(Draft RFD)`.
2. `ACP-INFO-CONCURRENT-201`: same change.
3. No new rows, fixtures or harness/mock-client behaviour.

**If the orchestrator still wants an RFD-tier sweep:** nothing qualifies. A candidate would need to be stated only in one
of these RFDs, and none is. The closest, `prompt.mdx:264-265` ("Reporting later user-action waits is recommended"),
`prompt.mdx:276-278` (cancel individual elicitations) and `session-resume-replay.mdx:96-99` (replay `_meta` patch), are
each stated by PL:163, EL:225-228 and SS:330-335.

## Testability notes

These are not needed for RFD rows. For the doc auditors' uncovered items:

- **R7 extension** (SS:307-321, MUST). This is observable the same way as ACP-RESUME-205. During replay, a
  `session_message_chunk`, `tool_call_content_chunk`, `terminal_output_chunk` or `compaction_summary_chunk` for an ID must
  be preceded, inside the replay window, by the matching `session_message`/`tool_call_update`/`terminal_update`/
  `compaction_update` with the emptied field (`content: []`, `output: {data: ""}`, `summary: []`) or full content. The
  check is vacuous when no such chunks are replayed. Size: widen RESUME-205, or add one row; 0 new fixtures beyond the
  existing replay fixtures, though a conforming v2 fixture would need to replay tool-call/terminal chunks to exercise it.
- **R10** (SS:330-335). It is conditional on "when the Client may already hold metadata", which the agent cannot know from
  the wire. It is likely a ledger entry (not observable as pass/fail).
- **P2 / P16 / P24-general / P27.** Insertion timing and agent-internal failure are not provokable by a client. P24 and
  P27 likely go to the ledger with a "Not triggerable" reason, like `v2.toml:320-321`. P16 needs background work that
  requests permission while idle, which is not provokable.
- **O12 `replay_complete`, O13 `idempotencyKey`.** Both are observable and new MUSTs in the docs. They belong to the
  session-setup and prompt-lifecycle doc researchers and are not scoped here.

## Discrepancies

These are RFD vs docs; the docs win in each case.

1. **Elicitation cancellation strength.** `prompt.mdx:276-278` says agents "should cancel individual elicitations". The
   target docs say MUST (EL:225-228; tightened upstream in #2852 per `spec-diff-v2.md:13`).
2. **Which permissions cancel resolves.** `prompt.mdx:275` says cancellation "resolves pending session-scoped
   permissions". The docs limit this to permission requests of the cancelled foreground work, cancelled with
   `$/cancel_request`, and leave background-work permissions unaffected (CN:42; PL:1453). The RFD wording is broader.
3. **Retry safety.** `prompt.mdx:167,391-393` ("Clients must not … assume retrying cannot create a second submission";
   "This proposal does not promise automatic deduplication") predates the docs' `idempotencyKey` (PL:419-471), which makes
   a retry with a key safe. This is not a direct contradiction (it still holds without a key), but the RFD is superseded.
4. **Resume ordering.** `prompt.mdx:262-263` and `session-resume-replay.mdx:49-51` end replay with the state snapshot.
   The docs insert `replay_complete` before the snapshot (SS:344-346). This is an addition, not a conflict.
5. **Session-baseline strength.** `required-session-methods.mdx:38-39` uses MUST. The docs state it declaratively
   ("Supplying `{}` means the Agent supports …", INI:276-279,304-306). The effective TCK tier is the same either way:
   CAPABILITY behind `capabilities.session`.
6. **RFD revision note with no body text.** `session-resume-replay.mdx:116` records "Said what a resume without replay
   leaves out", but that text appears only in the docs (SS:188-191), not in the RFD body. This is informational only.
7. **Stale list.** `required-session-methods.mdx:54-64` lists the remaining optional session capabilities without
   `systemPrompt`, `archive`, `options`, `status` and `title`, which the schema now has. This is informational only.

## Open questions

- `docs/spec-updates.md:42-43` and `docs/requirements.md` ("Citations") still say "`rfds/v2/*` in 'Active > v2' is
  Active". At the target there is no Active stage and `rfds/v2/*` sits under `Draft > v2`. These contributor docs need a
  wording update; route it to whichever slice updates the docs.
- Ledger `v2.toml:412-415` cites `session-setup.mdx:289 @ 3961af94`. At the target the rule is at SS:297 (doc-audit
  re-map).
- Whether RFD-only coverage of the other `rfds/v2/*` Draft RFDs is worth a separate pass. This report suggests the same
  outcome for any v2 RFD whose content the docs have absorbed; it was not verified for the other 11.
