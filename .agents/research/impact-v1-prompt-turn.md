# v1 impact: `docs/protocol/v1/draft/prompt-turn.mdx` (base beac4ba9 -> target 3961af94)

**Sources checked:** agent-client-protocol (worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`), base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a` (read via `git show`/`git diff`, checkout untouched). acp-tck working tree on `eugenethedev/update-spec` @ `200baba`. Reference SDKs not consulted: no affected requirement depends on runtime behaviour the spec leaves implicit, and the new text is not ambiguous on any agent-side rule the TCK can observe.
**Confidence:** high. Every registry row citing the doc was checked line by line at both revisions. The doc's only substantive changes are in the unstable subagent area, which the TCK never advertises, and in `Cost.currency`, which the TCK does not assert on.

## Answer

No registry row changes text, tier, or capability gate, and none is retired. Nine rows cite this doc. All are unchanged or citation-only: the line numbers after line ~40 shift by +22 to +27, and the cited text is byte-identical apart from heading case. The cancellation section (`## Cancellation`) did not change at all. `Stop reasons` changed only its heading, and `$defs/StopReason`, `PromptResponse`, `SessionNotification`, `SessionUpdate`, `ContentBlock`, `UsageUpdate`, `Cost`, `CancelNotification` and `ContentChunk` are structurally identical at target (descriptions only). The schema changes that `ACP-PROMPT-002`'s validation reaches are all additive or loosening: `SessionMessage` +2 optional props, `SessionMessageChunk` -2 optional props with no `additionalProperties: false`, `SubagentUpdate` +2 optional props, and `ToolCallContent` +`session` variant. So no previously valid update becomes invalid. `run_prompt`'s turn-end and cancel assumptions still hold. I propose no new requirements. There are two optional ledger entries for unstable-subagent rules the TCK cannot reach. Two code comments outside `requirements.py` carry stale line numbers, and `spec-impact --fix` will not remap them.

New map section addresses: `sections = ["Session updates", "Stop reasons", "Cancellation"]`. `Session updates` (H2, target line 10) still covers `Session-directed messages (unstable)` (H3, line 40). `Cancellation` (line 625) is unchanged. The new `#### Message IDs` (line 268) sits under `The prompt turn lifecycle > 3. Agent reports output`, outside the core sections, which is fine because it is an unchanged MAY with only a new heading.

## Summary table

| Id | Classification | Note |
|----|----------------|------|
| ACP-PROMPT-001 | citation-only | `prompt-turn.mdx:503` -> `:530`. The MUST is unchanged. `StopReason`/`PromptResponse` are structurally unchanged. |
| ACP-PROMPT-002 | unchanged | Cites no prompt-turn line. The schema closure under `SessionNotification` only widened, so the test still holds. |
| ACP-CANCEL-001 | citation-only | `:618,625` -> `:645,652`. The text is identical. |
| ACP-CANCEL-002 | citation-only | `:38,629` -> `:38,656`. The text is identical. |
| ACP-LOAD-002 | unchanged (for this doc) | `prompt-turn.mdx:38` did not move. Its session-setup citations belong to another researcher. |
| ACP-CLOSE-002 | citation-only (prompt-turn half) | `:618,625,629` -> `:645,652,656`. The session-setup half belongs to another researcher. |
| ACP-CLIENTCAP-004 | citation-only | `:266-269` -> `:293-296`. Only the heading case changed. `$defs/Notice` belongs to another researcher. |
| ACP-CLIENTCAP-005 | citation-only | `:328-333` -> `:355-360`. Only the heading case changed. The session-setup/compaction `$defs` belong to another researcher. |
| ACP-CLIENTCAP-006 | unchanged (for this doc) | `:25-26` did not move. The rows were only re-padded, so `spec-impact` lists them under the table hunk. `PlanCapabilities`/agent-plan belong to another researcher. |
| ACP-CLIENTCAP-007 | citation-only | `prompt-turn.mdx:19-21,42` did not move. Row 19 gained "working directories", which does not change the meaning. The RFD citation `docs/rfds/subagents.mdx:72-74` -> `:76-78` because 4 lines were inserted at RFD hunk `-16,12 +16,16`. The inventory's "cited lines untouched" is true of the content, but the line numbers did shift. `SubagentCapabilities` is unchanged. |
| (new) | none proposed | See Details §4. |
| (ledger) | 2 optional entries | The delegated-task SHOULD (`:106-111`) and the absoluteness of `SubagentUpdate.cwd`/`additionalDirectories`. Both need `clientCapabilities.subagents`, which the TCK never advertises. |

Code references outside `requirements.py` that `spec-impact --fix` does **not** remap (it only rewrites `requirements.py` and `maps/v1.toml`, `spec-tracker/README.md:34`):
- `src/tck/v1/conformance/_helpers.py:302` cites `prompt-turn.mdx:614`, which becomes `:641` (the Client MUST answer pending permission requests `cancelled`; the text is unchanged).
- `tests/fixtures/agents/v1/asks_permission.py:3` cites `prompt-turn.mdx:108-119`, which becomes `:133-144` (the permission block of the mermaid diagram; unchanged).
- `_helpers.py:190` cites `:38`. It did not move, so no action is needed.
- `spec-tracker/tests/test_citations.py:39,46` and `spec-tracker/src/spec_tracker/citations.py:5` use `prompt-turn.mdx:578-590,598` only as parser test data, not as real citations. I recommend leaving them alone, unless the spec-tracker suite resolves them against a pinned revision. If it does, that is the spec-tracker owner's call.

## Requirements

| # | Requirement | Tier | Citation (target) |
|---|-------------|------|-------------------|
| 1 | Agent MUST respond to `session/prompt` with a `StopReason` when the turn ends. | MUST | `docs/protocol/v1/draft/prompt-turn.mdx:530` |
| 2 | After cancellation, the agent MUST respond with the `cancelled` stop reason. | MUST | `prompt-turn.mdx:645` |
| 3 | Agents MUST catch abort exceptions and return `cancelled`, not an error. | MUST | `prompt-turn.mdx:652` |
| 4 | Post-cancel updates MAY be sent but MUST come before the prompt response. | MUST | `prompt-turn.mdx:656` |
| 5 | Client MUST answer pending `session/request_permission` with `cancelled` after `session/cancel` (a client rule the TCK's mock client follows). | MUST (client) | `prompt-turn.mdx:641` |
| 6 | MUST NOT send `notice` without `clientCapabilities.session.notices`. | MUST | `prompt-turn.mdx:293-296` |
| 7 | MUST NOT send `compaction_update`/`compaction_summary_chunk` without `session.compaction`, live or replay. | MUST | `prompt-turn.mdx:355-360` |
| 8 | `subagent_update`/`session_message`/`session_message_chunk` require the Client's `subagents` capability. | MUST (via RFD `docs/rfds/subagents.mdx:76-78`) | `prompt-turn.mdx:19-21,42` |
| 9 | NEW: Agents SHOULD report a parent's task to a subagent (including the first) as an incoming `session_message` in the child's transcript with `senderSessionId` = parent, and SHOULD NOT report it as `user_message_chunk`. | SHOULD, capability:`clientCapabilities.subagents` (unstable) | `prompt-turn.mdx:106-111`; RFD `docs/rfds/subagents.mdx:648-664` (proposal) |
| 10 | NEW wording: participant IDs go on `session_message` only. Chunks carry only content. Include the participants on the first `session_message`, before the first chunk, when available (lowercase prose). | prose, capability:`subagents` | `prompt-turn.mdx:46-50`; `schema/v1/schema.unstable.json#/$defs/SessionMessageChunk` |
| 11 | NEW: `senderMessageId`/`recipientMessageId` link the two views. "Clients must not link views by equal IDs alone" is a client rule. | MAY (agent) / client rule | `prompt-turn.mdx:96-100`; `#/$defs/SessionMessage/properties/senderMessageId`, `.../recipientMessageId` |
| 12 | CHANGED semantics: `null` on a participant ID now *clears* it (previously it retained a known value). This is a client-side interpretation rule. | prose | `prompt-turn.mdx:95`; `#/$defs/SessionMessage/properties/senderSessionId` |
| 13 | CHANGED: `Cost.currency` is the unit of `amount`, either ISO 4217 or another unit such as `"credits"` (a widening; the type is still `string`). | prose | `prompt-turn.mdx:526`; `#/$defs/Cost/properties/currency` |
| 14 | NEW schema: `SubagentUpdate.cwd` "Must be an absolute path", and each entry of `additionalDirectories` "must be absolute". | lowercase must, capability:`subagents` | `#/$defs/SubagentUpdate/properties/cwd`, `#/$defs/SubagentUpdate/properties/additionalDirectories` |

## Details

### 1. Row-by-row verification

- **ACP-PROMPT-001** (`requirements.py:250-265`). Base `:503` and target `:530` are the same sentence. The heading changed from `### 4. Check for Completion` to `### 4. Check for completion` (target line 528). `StopReason` has the same values (structural diff empty). `test_prompt.py:24-41` asserts `stopReason in STOP_REASONS`, which is still correct. Action: remap the line only.
- **ACP-PROMPT-002** (`requirements.py:266-281`). Its prompt-turn content is unchanged. It validates every `session/update` with `validate_agent_message`. Structurally changed defs reachable from `SessionNotification`: `SessionMessage` (+`senderMessageId`, +`recipientMessageId`, both optional and nullable), `SessionMessageChunk` (-`senderSessionId`, -`recipientSessionId`), `SubagentUpdate` (+`cwd`, +`additionalDirectories`, optional and nullable), `ToolCallContent` (+`session` variant -> new `$defs/SessionReference`). None of these defs sets `additionalProperties: false`, so an agent that still puts `senderSessionId` on a chunk remains schema-valid. No previously valid message becomes invalid. Action: none, apart from the vendored-schema refresh.
- **ACP-CANCEL-001** (`requirements.py:318-326`). The text at base `:618`/`:625` is identical to target `:645`/`:652`. The whole `## Cancellation` section (target 625-658) has no diff hunk. `test_cancel.py:68-93` is unchanged. Action: remap the line only.
- **ACP-CANCEL-002** (`requirements.py:327-340`). `:38` is unchanged. Base `:629` maps to target `:656`, which is identical. `HISTORY_KINDS` (`_helpers.py:183-190`) still matches "content or tool call updates". Action: remap the line only.
- **ACP-LOAD-002** cites `prompt-turn.mdx:38`, which is unchanged.
- **ACP-CLOSE-002** cites `prompt-turn.mdx:618,625,629`, which becomes `645,652,656`. The X2/X3 meaning is the same.
- **ACP-CLIENTCAP-004/005**: the MUST NOT sentences are byte-identical (`:293-296`, `:355-360`). Only the headings changed (`#### Session notices`, `#### Session compaction`).
- **ACP-CLIENTCAP-006**: lines 25-26 are identical except for column padding. `spec-impact` reports them because they sit inside the re-padded table hunk `-14,21 +14,21`. Keep the row as is.
- **ACP-CLIENTCAP-007**: line 19's description changed from "parent-owned metadata and work state" to "parent-owned metadata, working directories, and work state". Rows 20-21 changed padding only, and line 42 is unchanged. The test (`test_client_capabilities.py:163-176`) still checks the same three kinds. The fixture `emits_subagent_update_unadvertised.py` still sends a schema-valid `subagent_update` (`sessionId` plus `title`). The RFD citation moves from `72-74` to `76-78`. `spec-impact --fix` handles `.mdx` citations in `requirements.py`, so it should remap this one, because the RFD diff has a hunk above it. Verify after running it.

### 2. `run_prompt` assumptions (`src/tck/v1/conformance/_helpers.py:285-450`)

- Turn end is the `session/prompt` response carrying `stopReason`, which still matches `:530` and `:542`.
- Cancel: the helper sends `session/cancel` as a notification (`CancelNotification` is structurally unchanged). It answers later permission requests with `{"outcome":{"outcome":"cancelled"}}`, which matches the unchanged client MUST at `:641`. It expects the response `stopReason: "cancelled"` (`:645`, `:652`), and expects post-cancel updates only before the response (`:656`). All of these are unchanged.
- The mock client advertises `clientCapabilities: {}`, so the reshaped `session_message`/`session_message_chunk` traffic is unreachable for a conforming agent.

### 3. Changed text in the doc (all non-normative for a client-driven TCK, or capability-gated on the unadvertised `subagents`)

- Lines 46-50: participants moved from "any update" to `session_message` only. This matches the schema removing them from `SessionMessageChunk`.
- Lines 52-84: the example is now two notifications (`session_message` with the participants, then `session_message_chunk` with content).
- Line 95: the participant-ID patch rule changed. Omission means unchanged and `null` *clears* the ID. Base line 81 said "Omitted or `null` ... leave previously known identities intact". The schema descriptions changed in the same way (upstream commit `b51ded35`).
- Lines 96-100: new `senderMessageId`/`recipientMessageId`, and "Clients must not link views by equal IDs alone".
- Lines 106-111: new delegated-task SHOULD/SHOULD NOT (upstream commit `14560463`).
- Line 268: new `#### Message IDs` heading. The MAY sentence at 270 is the same as base 243 (`;` became `.`).
- Line 526: currency widened (upstream commit `effce045`).
- Everything else is sentence-cased headings and `;` -> `.` punctuation. Line 567 changed "leverage" to "use", and line 501 changed "utilization" to "usage".

### 4. New requirements: none proposed

- **Delegated-task SHOULD (`:106-111`)** would be ADVISORY with the capability gate `clientCapabilities.subagents`, but it is not observable. The TCK would have to advertise the unstable `subagents` client capability and then provoke an agent into spawning a subagent. No prompt can do that deterministically, and an agent that never delegates would pass vacuously. Advertising `subagents` would also change the CLIENTCAP-007 precondition for the whole run. **DECISION NEEDED** (low stakes). I recommend a ledger entry, not a requirement.
- **`SubagentUpdate.cwd`/`additionalDirectories` must be absolute**: these fields are only ever sent when the TCK has advertised `subagents`, which it never does. If an agent sends one anyway, ACP-CLIENTCAP-007 already FAILs. I do **not** recommend extending ACP-PROMPT-004 to cover them. Ledger entry is optional.
- **Currency**: this is a widening with no agent obligation, so there is nothing to test.
- **Participant-ID/message-ID rules**: these are client-side interpretation rules, or MAY on the agent side. Skip them as prose.

### 5. Proposed ledger entries (optional, for `spec-tracker/maps/v1.toml` `[[not_requirement]]`)

```
citation  = "docs/protocol/v1/draft/prompt-turn.mdx:106-111 @ 3961af94fa62"
statement = "Agents SHOULD report a parent's task to a subagent as an incoming session_message in the child's transcript (senderSessionId = parent) and SHOULD NOT report it as a user_message_chunk."
reason    = "Not observable: needs the unstable clientCapabilities.subagents, which the TCK never advertises, and an agent that actually delegates, which no prompt can force."

citation  = "schema/v1/schema.unstable.json#/$defs/SubagentUpdate/properties/cwd @ 3961af94fa62"
statement = "A subagent_update's cwd and each additionalDirectories entry must be absolute paths."
reason    = "Out of scope: subagent_update is only legitimate when clientCapabilities.subagents is advertised, which the TCK never does; any subagent_update the TCK sees already fails ACP-CLIENTCAP-007."
```

(Check how the ledger expects a schema pointer citation to be phrased. The map header says "same form as a requirement citation", which allows `schema.unstable.json#/$defs/...`.)

## Testability notes

- All affected rows keep their current assertions. A conforming agent behaves exactly as before.
- Everything new in this doc sits behind `clientCapabilities.subagents`. A client-driven TCK that advertises `{}` can only observe it as "must not be sent", which is CLIENTCAP-007 and already covered.
- Schema refresh: the vendored v1 schema picks up the new optional properties. `validation.py` carve-outs are not affected by these defs. Other researchers own the `ToolCallContent`/`SessionReference` addition, which comes from `tool-calls.mdx` (upstream `b3f6123f`).

## Discrepancies

- **Soft tension, doc vs schema, on chunk/participant ordering.** The doc says to include participants on the first `session_message` "when available, before the first chunk of a streamed message" (`prompt-turn.mdx:48-49`). The schema says `session_message` upserts "can arrive before, between, or after its chunks" (`#/$defs/SessionMessageChunk` description). Read together, these are a recommendation for when IDs are known, plus permission for late arrival. This does not affect the TCK.
- **Doc vs RFD.** The RFD's delegated-task SHOULD adds "before the child's response to it" and a second SHOULD to report and link the outgoing view in the parent (`docs/rfds/subagents.mdx:652-656`). The doc carries only the first SHOULD, with no ordering clause (`prompt-turn.mdx:106-109`). The RFD is a proposal, and this does not affect the TCK.
- **Inventory imprecision.** `.agents/research/spec-diff-v1.md` says CLIENTCAP-007's RFD "cited lines untouched". The content is untouched, but the lines moved from 72-74 to 76-78.

## Open questions

- Should `HISTORY_KINDS` (used by ACP-CANCEL-002 and the LOAD/RESUME rows) include `session_message`/`session_message_chunk` (and `compaction_*`) as "content" updates? This is moot while the TCK never advertises `subagents`/`compaction`, so it can be deferred.
- The tool-calls researcher should check whether the new `ToolCallContent` `session` variant (`#/$defs/SessionReference`) is gated on `subagents`. It is reachable from `tool_call`/`tool_call_update`, which the TCK *does* receive.
- `spec-tracker` test fixtures quote `prompt-turn.mdx:578-590,598` (base `Stop Reasons` block, target 605-617,625). The spec-tracker owner should decide whether those test strings need to track the pin.
