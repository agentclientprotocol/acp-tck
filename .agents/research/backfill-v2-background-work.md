# What does the Active RFD `docs/rfds/v2/background-work.mdx` require of a v2 agent, and how well does the v2 suite cover it?

**Sources checked:** agent-client-protocol @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (TCK pin, 2026-11-10) via `git show`, compared with `upstream/main` @ `c392d7e9d1de01337b749c0070929933e9f6f09f` (2026-11-12, 8 commits later). acp-tck working tree on branch `eugenethedev/subagents` (uncommitted changes there were read as-is). Rust and Python SDKs were not checked: the question is about spec text and TCK coverage, not runtime behaviour.
**Confidence:** high for the spec mapping (every agent-side rule was traced to a draft-doc line). Medium for the gap priorities, because they depend on how often real agents advertise `capabilities.cancel` or report `background`.

## Answer

The RFD is **Active**: it sits in the `Active › v2` sidebar group at `docs/docs.json:233` at both revisions. Its text is byte-identical at the pin and at `upstream/main`. Phase 1 has landed (RFD `:388`), so the draft docs restate **every agent-side rule** the RFD makes: `prompt-lifecycle.mdx` (Background work, Failures, Cancellation), `tool-calls.mdx` (Status, Cancelling tool calls, Cancelling terminals, Requesting permission) and `session-setup.mdx` (fork, resume, close). The v2 **stable** `schema.json` also carries the wire shapes; only `BackgroundSubagent` is unstable-only. Under the policy the docs decide every tier, and **no rule in this RFD is RFD-only in a way that matters for tiering**. The only RFD-only sentences are descriptive examples (a cron job's lifecycle, adapter notes). No existing row or ledger entry cites the RFD, and no MANDATORY row rests on it. All background rows are `CAPABILITY capabilities.session` under the registry's session-baseline rule (`src/tck/v2/requirements.py:13-19`) or ADVISORY.

Coverage of the passive "background list" rules is good: ACP-STATE-206/207/208, ACP-RESUME-213, ACP-PATCH-210/211/212, ACP-CANCEL-209/213 and ACP-CLOSE-205. The main gaps:
- `tool_call/cancel` and `terminal/cancel` have no active test, and the ledger defers them with a reason that rests on a TCK choice and calls them "unstable" by mistake.
- ACP-PATCH-211 does not exempt tool calls that reference a listed terminal, so it can flag a conforming Codex-style agent.
- A few passive SKIP-able checks (re-send on list change, fork isolation, keeping the list across resume) are ledgered as "not elicitable" when a passive row would be possible.

## Requirements

Tiers below are the tier each rule *should* get under the policy (docs decide, and the session-baseline rule caps docs MUSTs on session methods at `CAPABILITY capabilities.session`). "pl" = `docs/protocol/v2/draft/prompt-lifecycle.mdx`, "tc" = `docs/protocol/v2/draft/tool-calls.mdx`, "ss" = `docs/protocol/v2/draft/session-setup.mdx`, "RFD" = `docs/rfds/v2/background-work.mdx` (Active RFD). All line numbers are at the pin.

| # | Requirement (agent side) | RFD | Draft docs / schema | Tier under policy | TCK status |
|---|---|---|---|---|---|
| R1 | An agent that reports `background` MUST include it on every `state_update` for the session (omitted/`null` = not reported) | RFD:192 | pl:204; `RunningStateUpdate/properties/background` (likewise Idle, RequiresAction, Unknown) | MUST → CAPABILITY `capabilities.session` | **Covered**: ACP-STATE-206 (one connection; see R1b) |
| R1b | The same, across resume: the resume snapshot "carries the `background` list like any other" | RFD:228 | ss:346 + pl:204 | MUST → CAPABILITY | **Not covered** (STATE-206 judges one connection; RESUME-213 does not check omission) |
| R2 | Each `terminal`/`tool_call`/`subagent` item is announced (`terminal_update` / `tool_call_update` / `subagent_update`) before the first snapshot that lists it; items reference entities of this session | RFD:62,194,196 | pl:184,206; `BackgroundWork` description | MUST → CAPABILITY | **Covered**: ACP-STATE-207 |
| R3 | A terminal's `exitStatus` / a tool call's final status is sent before the snapshot that removes it | RFD:194 | pl:206; `BackgroundWork` description | MUST → CAPABILITY | **Partial**: ACP-STATE-208 judges only removals in `idle` snapshots and leaves out subagents (justified, see Testability) |
| R4 | When background work starts or ends, the Agent SHOULD re-send the current state with the updated list | RFD:193 | pl:205 | SHOULD → ADVISORY | **Not covered**: ledger `v2.toml:184-187` (reason questionable, see Gaps) |
| R5 | Known follow-up foreground work: report `running` no later than the snapshot that removes the item | RFD:195 | pl:207 | SHOULD → ADVISORY | Ledgered `v2.toml:184-187`. Correct: what the agent knows is unobservable |
| R6 | Do not list work that foreground work waits on; MUST NOT also list a tool call whose only live work is a listed terminal | RFD:199,201 | pl:208 | MUST NOT → CAPABILITY | Ledgered `v2.toml:189-192` (unobservable). Correct, with an INFORMATIONAL idea in Gaps |
| R7 | A detached child is listed while not `idle` or while its own list is non-empty or unreported; an idle, quiet child is not listed | RFD:200 | pl:210 (no RFC keyword); `BackgroundSubagent` is **UNSTABLE**, unstable schema only | descriptive → ADVISORY, or CAPABILITY `inferred:subagents` if read as a MUST | Ledgered Deferred `v2.toml:194-197`. OK |
| R8 | SHOULD keep a continuing tool call non-final and list it; SHOULD NOT list self-started housekeeping | RFD:62,64 | pl:184,186 | SHOULD → ADVISORY | Ledgered `v2.toml:179-182` (unobservable). Correct |
| R9 | A final tool-call status is never reopened (a new tool call is started instead); statuses never go back to `pending` | RFD:62,81 | pl:184; tc:421,423 | MUST-strength descriptive → CAPABILITY | **Covered**: ACP-PATCH-210 (CAPABILITY), within the turn window |
| R10 | `paused` is a valid status; `pending`/`paused` tool calls are live and stay listed | RFD:68-87,198 | pl:181; tc:404-407; `ToolCallStatus`, `BackgroundWork` (tool_call branch) | schema | **Covered**: schema validation, plus STATE-208 (an idle that drops a non-final pending/paused item FAILs) |
| R11 | While a terminal is listed, SHOULD keep its output current when the process output is readable | RFD:56 | pl:180 | SHOULD → ADVISORY | Ledgered `v2.toml:174-177` (unobservable). Correct |
| R12 | `capabilities` on `tool_call_update` is a nullable patch; SHOULD stop advertising `cancel` once final | RFD:106-108 | tc:440; `ToolCallCapabilities` | SHOULD → ADVISORY | **Covered**: ACP-PATCH-212 |
| R13 | Same for terminals: SHOULD stop advertising `cancel` once `exitStatus` is reported | RFD:147 | tc:600; `TerminalCapabilities` | SHOULD → ADVISORY | **Covered**: ACP-PATCH-212 |
| R14 | `tool_call/cancel` on an advertised tool call: empty result once accepted, then a `tool_call_update` to a final status (normally `cancelled`; `completed`/`failed` if it finished first) | RFD:125 | tc:458; `CancelToolCallRequest`, `CancelToolCallResponse` | normative, no RFC keyword → CAPABILITY `inferred:toolCallCancel` | **Not covered**: ledger `v2.toml:657-660` "Deferred" (reason rests on a TCK choice) |
| R15 | `tool_call/cancel` → `-32602` if the tool call is unknown, already final, or not cancellable | RFD:126 | tc:459 | normative → CAPABILITY (the reachable part only) | **Not covered**: same ledger entry |
| R16 | Cancelling a tool call does not change the foreground state by itself | RFD:127 | tc:460 | normative → ADVISORY (hard to judge) | **Not covered**: same ledger entry |
| R17 | `terminal/cancel` on an advertised terminal: empty result once accepted, then a `terminal_update` setting `exitStatus` | RFD:164 | tc:604; `CancelTerminalRequest` | normative → CAPABILITY `inferred:terminalCancel` | **Not covered**: ledger `v2.toml:662-665` "Deferred" |
| R18 | `terminal/cancel` → `-32602` if the terminal is unknown, has exited, or is not cancellable | RFD:165 | tc:605 | normative → CAPABILITY (the reachable part only) | **Not covered**: same |
| R19 | `terminal/cancel` does not release the terminal and does not change the foreground state or the status of a referencing tool call | RFD:166-167 | tc:606 | normative → ADVISORY | **Not covered**: same |
| R20 | `session/cancel` does not cover work in the latest `background` list; it keeps running, and its permission requests are not affected | RFD:211,214 | pl:1173,1177; tc:268 | descriptive (no keyword) → ADVISORY/INFORMATIONAL | Ledgered `v2.toml:640-643` "Not elicitable" (questionable, see Gaps) |
| R21 | On `session/cancel`, MUST stop waiting for the cancelled foreground work's permission requests; SHOULD withdraw each with `$/cancel_request` | RFD:214 | pl:1177 | MUST → CAPABILITY / SHOULD → ADVISORY | **Covered**: ACP-CANCEL-209 (CAPABILITY), ACP-CANCEL-213 (ADVISORY) |
| R22 | MUST list background work before sending a permission request for it; SHOULD reference the listed item in `subject` | RFD:215 | tc:268 | MUST → CAPABILITY / SHOULD → ADVISORY | Ledgered `v2.toml:551-554` (unobservable). Correct |
| R23 | On an `error` stop reason, SHOULD finalize the failed work's unfinished tool calls; listed work, and tool calls that reference a listed terminal, keep running | RFD:217 | pl:998; tc:423 | SHOULD → ADVISORY | **Partial**: ACP-PATCH-211 judges error idles too, but lacks the terminal-reference exemption (see Discrepancies / Gap G2) |
| R24 | Before responding to `session/close`, MUST withdraw every pending permission request for the session with `$/cancel_request` | RFD:222 | ss:391 (docs add elicitations) | MUST → CAPABILITY | **Covered**: ACP-CLOSE-205 |
| R25 | `session/close` stops all background work; the Agent MAY send final updates before responding | RFD:220-223 | ss:391 | MUST-strength (stops) / MAY | Ledgered `v2.toml:413-416` (unobservable). Correct |
| R26 | A fork starts with no background work; its snapshots report `background: []` until it starts its own | RFD:226 | ss:49 | descriptive → CAPABILITY `inferred:background` or ADVISORY | Ledgered `v2.toml:388-391` (reason rests on the TCK's scenario, see Gaps) |
| R27 | Before the resume snapshot, send a current `terminal_update` / `tool_call_update` / `subagent_update` for each listed item that replay did not already deliver at its current state (all of them when there is no replay) | RFD:230 | ss:346 | MUST → CAPABILITY | **Partial**: ACP-RESUME-213 (replay omitted only; checks that an update *exists*, not that it is *current*) |
| R28 | Custom `background[].type` values begin with `_`; unknown non-underscore values are reserved | RFD:196 ("usual enum variant extension rules") | `BackgroundWork` `other` branch description; extensibility rules | MUST (extensibility) → CAPABILITY | **Not covered**: ACP-ENUM-201's site list does not include `background[].type` |

There are no RFD-only agent rules with normative force. The RFD-only remainder is descriptive or adapter-specific and needs no row or ledger entry:
- RFD:83-84: a recurring cron job stays `pending` until removed; a paused tool call ends when cancelled, failed or discarded.
- RFD:164: "for example with the signal used to stop it".
- RFD:275-283: the adapter table, `perTaskStopAffordance`, and "should send final updates on `session/close`". These address specific adapters, not the protocol.

## Details

### Stage and where the wire shapes live

- Stage: **Active** (`docs/docs.json:209-235` at the pin, group `Active` › `v2`). The same holds at `upstream/main:docs/docs.json:234`.
- RFD revision history: "Phase 1 landed: the schema changes are in the v2 schema … and the protocol docs describe the `background` list, `paused`, and both cancel methods" (RFD:388). The 2026-11-09 and 11-02 revisions (RFD:383-386) are also reflected in the draft docs (pl:184, tc:125, pl:1177, ss:391).
- Schema (`schema/v2/schema.json` and `schema.unstable.json`, both at the pin):
  - `background` property on `RunningStateUpdate`, `RequiresActionStateUpdate` and `IdleStateUpdate`, plus `UnknownStateUpdate` (unstable only): `type: ["array","null"]`, items `BackgroundWork`, `x-deserialize-default-on-error`.
  - `BackgroundWork`: `anyOf` on `type`. `terminal` → `BackgroundTerminal{terminalId, _meta}`; `tool_call` → `BackgroundToolCall{toolCallId, _meta}`; `subagent` → `BackgroundSubagent{sessionId, _meta}` (**UNSTABLE**, `schema.unstable.json` only); `other` fallback (any string except the known ones, `additionalProperties: true`).
  - `ToolCallStatus`: adds `paused` (`schema.json:500`).
  - `ToolCallUpdate.capabilities` → `ToolCallCapabilities{cancel: ToolCallCancelCapabilities|null, _meta}`. `TerminalUpdate.capabilities` → `TerminalCapabilities{cancel: TerminalCancelCapabilities|null, _meta}`.
  - Client → agent requests `CancelToolCallRequest{sessionId, toolCallId, _meta}` (`x-method: tool_call/cancel`) and `CancelTerminalRequest{sessionId, terminalId, _meta}` (`x-method: terminal/cancel`). Their responses carry only `_meta`. Both appear in the **stable** `meta.json:14-15` method table and in `schema.json`, with **no** `**UNSTABLE**` label (unlike `session/status` or `SubagentUpdate`).
- v2 has no `tool_call` sessionUpdate variant. The variants are `tool_call_update`, `tool_call_content_chunk`, `terminal_update`, `terminal_output_chunk`, `subagent_update`, etc. (`SessionUpdate` in the unstable schema). The RFD's "a `tool_call` or `tool_call_update`" (RFD:194) is therefore stale; the docs (pl:206) say `tool_call_update`.

### Upstream drift (pin → upstream/main)

- `background-work.mdx`: identical.
- `prompt-lifecycle.mdx`: +5 lines inserted at 144 (subagent `senderSessionId`). **Every pl citation at or after line 144 shifts by +5 at upstream** (pl:204 → 209, pl:206 → 211, pl:998 → 1003, pl:1173 → 1178, pl:1177 → 1182). No background text changed.
- `session-setup.mdx` (+4 at 509) and `tool-calls.mdx` (+5 at 753): both insertions come after every line cited here, so no shift.
- Adjacent, not in this RFD: `docs/rfds/subagents.mdx` at upstream adds that a child's `unknown` state "leaves the child's unfinished tool calls, terminals, and v2 `background` list as last reported. The Agent **MUST NOT** invent a final status for them" (upstream `subagents.mdx` ≈ :898-905). The `UnknownStateUpdate` description in the unstable schema gets the matching text. This touches R3 for children and belongs to the next spec update, not to this backfill.

## Testability notes

- **R1/R2/R3 (passive):** only observable for an agent that reports a list. STATE-206/207/208 correctly SKIP otherwise. STATE-208's restriction to `idle` removals is sound: pl:208 makes work that foreground work waits on "not listed", so an active snapshot can legitimately drop an unfinished item that foreground work re-attached. In `idle` there is no foreground work, so a dropped non-final item is a violation. Subagents are rightly not judged: a child has no final status, and RFD:371 says a child's `idle` "was never final".
  - Edge (hypothesis, not checked against an agent): STATE-207 counts only `session/update` announcements. A tool call first created by a permission `subject.toolCall` ("A first-seen `toolCallId` creates the tool call", `ToolCallPermissionSubject`) is not counted. Because tc:268 requires listing *before* the permission request, a conforming agent hits this only in odd orderings. It is not worth changing.
- **R14/R17 (active):** testable without breaking the client rule. When a tool call or terminal advertises `capabilities.cancel` (PATCH-212's tracker already detects this: `tracker.cancel_seen`), the TCK may send the cancel. Conforming: an empty result (or `-32602` if the work became final in a race), then a final `tool_call_update` or an `exitStatus` `terminal_update`. Violating: an error for an advertised, non-final item; no confirming update within the timeout; `-32601`.
- **R15/R18 error paths:** "unknown" and "not cancellable" can only be probed by sending the request against tc:456/602 (client MUST NOT), so they belong in the ledger. "Already final" is reachable legitimately only when the agent keeps advertising `cancel` after the final status (a PATCH-212 violation) or through a race. It is a cheap add-on to the R14 test: after the confirming final update, if `cancel` is *still* advertised, a second cancel must get `-32602`.
- **R16/R19:** "does not change foreground state by itself" can only be judged as "no `running` follows within a short window while idle", which an agent could legitimately break by acting on the result (RFD:127: "The Agent decides what, if anything, to tell the model"). That makes it INFORMATIONAL at most.
- **R20:** passive partial check: if the latest list before `session/cancel` is non-empty, record whether those items get `cancelled` status or `exitStatus` before the cancelled idle. This cannot prove a violation (work may end on its own), so INFORMATIONAL.
- **R26 fork:** passive check: if the source session's latest list was non-empty at fork time, no fork snapshot may list an item id that the fork itself did not announce. A conforming fork reports `[]` or omits the list (an agent may not report at all).

## Mapping to existing TCK rows, tests and ledger entries

| Row / entry | Spec rule | Status | Notes |
|---|---|---|---|
| ACP-STATE-206 (`requirements.py:482-498`; `test_background.py:89-109`) | R1 | Covered | Cites pl:188,203-204 + schema. CAPABILITY `capabilities.session`. Correct |
| ACP-STATE-207 (`:499-513`; `test_background.py:112-136`) | R2 | Covered | Cites pl:206,209. Correct. Announcement kinds match the docs, not the RFD's stale `tool_call` |
| ACP-STATE-208 (`:514-532`; `test_background.py:139-180`) | R3 | Partial (by design) | Idle-only and no subagents, both justified. Cites pl:206,208 |
| ACP-RESUME-213 (`:1459-1476`; `test_session_capabilities.py:581-620`) | R27 | Partial | Only `replayFrom` omitted; "current state" not judged |
| ACP-PATCH-209 (`:2683-2699`) | R22 (exclusion only) | n/a | Correctly excludes requests whose subject names a listed item |
| ACP-PATCH-210 (`:2701-2714`) | R9 | Covered | Turn window (`_drive_one_turn` via `run_prompt`). Post-idle background updates are not judged (hypothesis from reading `test_patches.py:303-308`; not traced further) |
| ACP-PATCH-211 (`:2716-2727`; `test_patches.py:325-354`) | R23 / tc:423 | **Partial, likely false positive** | Exempts tool calls *listed* in `background` but not tool calls that *reference a listed terminal*. Docs pl:216, pl:998, pl:1175, ss:391 and tc:587 all treat such a tool call as live, and RFD:56 explicitly allows it to "stay `in_progress` until the process exits, as Codex's command items do". ADVISORY, so the verdict is unaffected, but the report misleads |
| ACP-PATCH-212 (`:2729-2746`) | R12, R13 | Covered | Passive |
| ACP-CANCEL-209 / -213 | R21 | Covered | Mock client holds the foreground request (`_helpers.py:1410-1441`), never holds listed-work requests. Matches pl:1177 |
| ACP-CLOSE-205 | R24 | Covered | Cites ss:391 |
| ACP-ENUM-201 (`:2748-`) | R28 | Not covered | `background[].type` is not in its site list |
| ledger `v2.toml:174-177` (pl:180) | R11 | Correct | |
| ledger `v2.toml:179-182` (pl:184,186) | R8 | Correct | |
| ledger `v2.toml:184-187` (pl:205,207) | R4, R5 | Half-stale | R5 is correctly unobservable. R4's reason "the TCK cannot make an agent start background work" is the same situation STATE-206..208 handle with SKIP-able passive rows, so by `docs/requirements.md` ("a rule that becomes observable … belongs in a row that can SKIP") R4 deserves an ADVISORY row |
| ledger `v2.toml:189-192` (pl:208) | R6 | Correct | |
| ledger `v2.toml:194-197` (pl:210) | R7 | Correct (Deferred) | |
| ledger `v2.toml:388-391` (ss:49) | R26 | **Reason rests on a TCK choice** | "the session the TCK forks has no unfinished work" describes the TCK's scenario. The real blocker is that the agent decides whether it has background work. A passive SKIP-able check is possible (see Testability) |
| ledger `v2.toml:413-416` (ss:391) | R25 | Correct | |
| ledger `v2.toml:551-554` (tc:268) | R22 | Correct | |
| ledger `v2.toml:640-643` (pl:1173; tc:268) | R20 | Defensible, wording weak | "Not elicitable" is true for a hard check. An INFORMATIONAL passive record is possible but low value |
| ledger `v2.toml:657-660` (tc:458-460; `CancelToolCallRequest`) | R14-R16 | **Wrong label and a TCK-choice reason** | (a) "Deferred unstable method": the method is in the stable v2 `schema.json` and `meta.json:14` with no UNSTABLE label. (b) "gated per tool call by a dynamic `capabilities.cancel` the TCK cannot elicit": PATCH-212 already shows that the same dynamic capability is handled by a SKIP-able row, and "the TCK sends no cancel" (PATCH-212 text) is a TCK choice. Only the unknown / not-cancellable error paths legitimately stay in the ledger |
| ledger `v2.toml:662-665` (tc:604-606; `CancelTerminalRequest`) | R17-R19 | Same two problems | `meta.json:15` |

**No MANDATORY row rests only on this RFD.** No row or ledger entry cites `docs/rfds/v2/background-work.mdx` (`rg 'rfds/v2/background'` over `src spec-tracker tests docs` finds nothing). Every background-related row cites draft docs and schema, so the new RFD-labelling policy needs no relabelling here.

## Verdict and prioritized gaps

**Verdict:** the RFD adds no new tier obligations beyond what the draft docs already state, and the suite's passive coverage of the `background` list is sound and correctly tiered. What is missing: the two cancel methods (ledgered on a reason the policy no longer accepts), one ADVISORY false positive, and a handful of small passive checks.

1. **G1: `tool_call/cancel` happy path (R14, plus the R15 "already final" add-on).** New row, e.g. ACP-TOOLCANCEL-2xx (id area for the programmer to choose), CAPABILITY `inferred:toolCallCancel` (or `capabilities.session` per the session-baseline convention; a decision for the orchestrator), citing tc:442-459 and `#/$defs/CancelToolCallRequest`.
   - Test: drive a turn. On the first `tool_call_update` whose effective `capabilities.cancel` is an object and whose status is non-final, send `tool_call/cancel`. Assert either (a) result `{}`-shaped (no error) followed within the timeout by a `tool_call_update` with `completed`/`failed`/`cancelled` for that id, or (b) `-32602` and a final status already sent (race). SKIP when nothing advertises cancel.
   - Conforming fixture: advertises `cancel` on a long-running tool call, answers `{}`, then sends `status: cancelled` and clears `capabilities`.
   - Violating fixtures: one that answers `-32601`/`-32602` for an advertised in-progress call; one that answers `{}` but never sends a final status.
   - Replace ledger `v2.toml:657-660` with a narrower entry for the unknown / not-cancellable paths ("needs the client to break tc:456") and drop "unstable".
2. **G2: fix ACP-PATCH-211's exemption.** Also exempt a tool call whose effective `content` contains a `terminal` item whose `terminalId` is in a `background` list reported during the turn. Add pl:216 (and pl:998) to the citation.
   - Conforming fixture: Codex-style. Tool call `in_progress` with `{"type":"terminal","terminalId":"t1"}` content, `background: [{"type":"terminal","terminalId":"t1"}]` at idle. Must PASS.
   - Violating fixture: the existing `leaves_tool_call_in_progress.py` (unlisted, no terminal) must still FAIL.
3. **G3: `terminal/cancel` happy path (R17, plus the R18 "already exited" add-on).** Same shape as G1, citing tc:600-606 and `#/$defs/CancelTerminalRequest`. Assert `{}` then a `terminal_update` with non-null `exitStatus`. Optionally record (INFORMATIONAL) whether a referencing tool call's status changed (R19).
   - Conforming fixture: advertises `cancel` on a listed background terminal, confirms with `exitStatus: {signal: "SIGTERM"}`.
   - Violating fixture: answers `{}` and never sets `exitStatus`.
   - Narrow ledger `v2.toml:662-665` the same way.
4. **G4: R4 as an ADVISORY passive row.** When a listed `terminal`/`tool_call` item gets its final status or `exitStatus` while the session is idle, a `state_update` that drops it arrives within the quiet period. SKIP when no listed item finalizes while idle. Cite pl:205. Shrink ledger `v2.toml:184-187` to R5 only.
   - Conforming fixture: `reports_background_work.py` extended to finish its background item after the idle and re-send `idle` with `[]`.
   - Violating fixture: finishes the item after idle and never re-sends the state.
5. **G5: R1b, keep the list across resume.** Extend ACP-STATE-206 (or add a sibling) so that once a session reported a list, the resume snapshot on the new connection carries an array too. Cite ss:346 and pl:204.
   - Conforming fixture: `resume_lists_background_work.py`.
   - Violating fixture: reports lists live but omits `background` on the resume snapshot.
6. **G6: R26 fork isolation, a passive CAPABILITY/ADVISORY row.** If the source's latest list at fork time was non-empty, no fork snapshot lists an item the fork did not itself announce. SKIP otherwise. Rewrite the ledger reason at `v2.toml:388-391` either way, so it no longer rests on the TCK's scenario.
   - Conforming fixture: a fork-capable fixture with a background item that reports `[]` on the fork.
   - Violating fixture: copies the source's list into the fork's snapshot.
7. **G7: R28 enum site.** Add `state_update.background[].type` to ACP-ENUM-201's checked sites (`#/$defs/BackgroundWork` `other` branch).
   - Violating fixture: lists `{"type":"task", ...}`.
8. **G8 (lowest): INFORMATIONAL records** for R6 (a listed tool call whose content references a listed terminal) and R20 (listed items finalized between `session/cancel` and the cancelled idle). These record observations only; there is no conforming/violating pair beyond "observed / not observed".

## Discrepancies

- **RFD vs docs/schema, announcing update:** RFD:194 says "a `tool_call` or `tool_call_update`". pl:206 says `tool_call_update` only, and v2 `SessionUpdate` has no `tool_call` variant. The RFD is stale; the TCK follows the docs.
- **RFD vs docs, removal rule scope:** RFD:194 makes finalization conditional ("When a terminal exits or a tool call ends, … before the snapshot that removes it"). pl:206 states it unconditionally ("before the snapshot that removes it"). pl:208 lets foreground work re-attach an item. STATE-208's idle-only judgment is consistent with both readings.
- **RFD vs docs, launching tool call status:** RFD:56 explicitly allows the launching tool call to stay `in_progress` while its terminal is listed. pl:180 drops that sentence, but pl:216, pl:998, pl:1175 and ss:391 all treat "a tool call that references a listed terminal" as live. tc:423's exemption names only "tool calls in the session's `background` list". The docs are slightly inconsistent (tc:423 is narrower than the rest), and ACP-PATCH-211 follows the narrow tc:423 text.
- **RFD vs docs, small additions in the docs:** pl:1173 adds "The Agent MAY stop background activity it does not list". tc:457 and tc:603 add subagent `sessionId` targeting for the cancel methods. ss:391 extends the close withdrawal to elicitations. RFD:164's "e.g. with the signal used" is omitted. None conflicts.
- **Schema labelling vs TCK ledger:** `tool_call/cancel` and `terminal/cancel` are unlabelled stable-v2 methods (`schema.json`, `meta.json:14-15`), but the ledger files them under "deferred unstable methods".

## Open questions

- Gate convention for G1/G3: `capabilities.session` (session-baseline rule) or a new `inferred:toolCallCancel` / `inferred:terminalCancel`? The cancel methods are not in the seven-method baseline the registry header names (`requirements.py:13-17`), so either choice needs an orchestrator decision.
- Should tc:423's narrower exemption be reported upstream as a docs inconsistency, given pl:216/998/1175?
- The upstream subagents-RFD addition (`unknown` freezes a child's `background` list; MUST NOT invent final statuses) should be routed to the next spec-update audit, together with the +5 line shift in `prompt-lifecycle.mdx`.
