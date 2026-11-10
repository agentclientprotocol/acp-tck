# v2 impact audit: `tool-calls.mdx` + `agent-plan.mdx` (`beac4ba` -> `3961af9`)

**Sources checked:** agent-client-protocol (checkout `agent-client-protocol-2`, not pulled per brief) base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a` (2026-11-10): `docs/protocol/v2/draft/tool-calls.mdx` and `docs/protocol/v2/draft/agent-plan.mdx` read whole at target, plus full diffs; the related sections of `prompt-lifecycle.mdx` ("Foreground and background work", "Background work", "5. Tool invocation", the state-transition table) and `extensibility.mdx` "Enum and tagged-union variants"; `$defs` of target/base `schema/v2/schema.unstable.json`; RFD diffs `docs/rfds/plan-operations.mdx`, `docs/rfds/v2/plan-variants.mdx` (proposals only). TCK at `HEAD` (`200baba`): `src/tck/v2/requirements.py`, `src/tck/v2/protocol.py`, `src/tck/v2/conformance/{test_permission,test_patches,test_enums,_helpers}.py`, `tests/v2/test_validation.py`, `tests/fixtures/agents/v2/*`. Rust/Python SDKs: not consulted. Every rule judged here is explicit in the spec text, so no SDK runtime behaviour was needed.
**Confidence:** high for classifications and line mappings (read directly from target text and schema); medium for the new-requirement tier proposals (several rules use indicative wording with no RFC 2119 keyword, so they are marked DECISION NEEDED).

All target line numbers below are `@ 3961af94fa62`.

## Answer

No registered requirement citing these two docs is retired, and none needs a tier change. All 8 rows assigned (`ACP-PERM-201`, `ACP-PATCH-204..209`, `ACP-ENUM-201`) still hold at target. Three need text or test changes. `ACP-ENUM-201` must pick up `paused` (`ToolCallStatus`) and `session` (`ToolCallContent.type`); `tests/v2/test_validation.py::test_enum_sets_match_the_schema` will fail on the schema refresh until the hand-copied sets in `src/tck/v2/protocol.py` are updated. `ACP-PATCH-209` should exclude permission requests for listed background work. `ACP-PATCH-208` should count a permission `subject.toolCall` as the first report of a `toolCallId`. The rest only need citation remaps.

B8 (`ToolCallLocation.line` min 1) and B9 (`TerminalExitStatus.exitCode` int64) hit **no** fixture and no test. No v2 fixture emits `locations` or `exitStatus`. Both are enforced automatically through schema validation (`ACP-PROMPT-205`, `ACP-PERM-201`) once the schema is re-vendored.

There are new observable agent-side MUSTs, and I propose ids for them:
- `optionId` must be unique within a request, and a `command` subject's `cwd` must be absolute (proposed `ACP-PERM-202`).
- After a `cancelled` outcome the agent must not proceed (proposed `ACP-PERM-203`).

There are also several SHOULD or indicative rules on tool-call status and capabilities (`ACP-PATCH-210..212`, ADVISORY). A set of pre-existing but unregistered diff, plan and enum-site rules is offered as optional scope.

## Summary table

| Id | Classification | One-line note |
|----|----------------|---------------|
| ACP-PERM-201 | citation-only change | `tool-calls.mdx:201` -> `209`; `236-263` -> `244-266,275-278`; `337-355` -> `356-374`. The schema shape is unchanged (`required` is the same). The `236-263` range now has two new paragraphs inside it (`268`, `270-273`), so `--fix` will list it under "Needs review". New sibling rules go into proposed `ACP-PERM-202`. |
| ACP-PATCH-204 | unchanged (optional text touch-up) | Schema pointers all resolve. `ToolCallUpdate.required` and `ToolCallContentChunk.required` are unchanged. The `exitCode` loosening (B9) is irrelevant because the test never inspects `exitStatus`. Optional: the text's "an update for a previously-unseen id is itself the create" now also applies to a chunk (`tool-calls.mdx:198-200`) and a permission subject (`270-273`). |
| ACP-PATCH-205 | citation-only change | `agent-plan.mdx:143` -> `147`. Same text. |
| ACP-PATCH-206 | citation-only change | `tool-calls.mdx:413-419` -> `493-499`; `439-447` -> `523-531`. The new `size` field and `capabilities` are schema-only. |
| ACP-PATCH-207 | citation-only change | `448-449` -> `536-537`; `478-482` -> `566-570`. |
| ACP-PATCH-208 | citation-only change + test refinement recommended | `42-55` -> `41-54`. Same SHOULDs. The test ignores the new "first report" paths (a permission `subject.toolCall` and a `tool_call_content_chunk` can now create a tool call), which can cause a false ADVISORY FAIL. |
| ACP-PATCH-209 | changed text (scope narrowed) | `tool-calls.mdx:201` -> `209`. New `268` plus `prompt-lifecycle.mdx:174,845`: a request for background activity does not need `requires_action`. The test should skip such requests. ADVISORY, so the verdict is not affected. |
| ACP-ENUM-201 | changed text (site list) | `tool-calls.mdx:77,353,380` -> `76,372,419`; `agent-plan.mdx:160,172` -> `164,176`. `paused`/`session` must be added to the `protocol.py` sets, which the meta-test forces. Pre-existing bug: `tool_call_content_chunk.content` is never checked. Recommended new sites listed below. |
| ACP-PERM-202 | **new** (CAPABILITY) | Permission `options[].optionId` unique within the request (`tool-calls.mdx:357`, new MUST). A `command` subject's `cwd` is absolute (`302-303`, MUST; `AbsolutePath` is a plain string in the schema, so validation can't catch it). |
| ACP-PERM-203 | **new** (DECISION NEEDED: CAPABILITY recommended) | After a `cancelled` outcome to a request whose `subject` is `tool_call` X, X is never later reported `completed` (`tool-calls.mdx:340,423`). |
| ACP-PATCH-210 | **new** (DECISION NEEDED: ADVISORY recommended) | Tool-call status is monotonic: never back to `pending`, no change after a final status (`tool-calls.mdx:421,423`). |
| ACP-PATCH-211 | **new** (ADVISORY) | When the turn's idle arrives, the turn's unlisted tool calls have a final status (`tool-calls.mdx:423`, SHOULD). |
| ACP-PATCH-212 | **new** (ADVISORY) | The agent stops advertising `capabilities.cancel` once a tool call is final or a terminal reports `exitStatus` (`tool-calls.mdx:440,600`, SHOULD). Overlaps the cancellation researcher's scope. |
| (optional) ACP-DIFF-201, ACP-PLAN-201, ACP-PATCH-213, ACP-PATCH-214 | new, low priority | Pre-existing or unstable rules that were never registered: `git_patch` paths, file-plan URI, output before `exitStatus`, `session` reference known. See details. |
| ledger | 9 entries | Unobservable or client-side rules (see "Ledger"). |

Cross-references, owned by other researchers and only noted here:
- `ACP-CANCEL-209` and `ACP-ENUM-203` both depend on permission-outcome text. The client-side rule changed from "Client **MUST** respond with `cancelled`" (base `tool-calls.mdx:311`) to "a permission request cancelled with `$/cancel_request` ... is answered with the `"cancelled"` outcome" (target `326`). That is the cancellation doc's concern.
- `tool_call/cancel` and `terminal/cancel` request semantics (`tool-calls.mdx:442-460,600-606`) belong to the cancellation researcher.
- The background-list MUSTs (`prompt-lifecycle.mdx:188-216`) belong to the prompt-lifecycle researcher.
- The `extensibility.mdx:226-231` part of `ACP-ENUM-201`'s citation (now around `233-240`) belongs to the extensibility researcher.

## Requirements

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| 1 | `session/request_permission` params: `sessionId`, `title`, and `options` (minItems 1) are required; each option requires `optionId`/`name`/`kind` | CAPABILITY `capabilities.session` (existing PERM-201) | `schema/v2/schema.unstable.json#/$defs/RequestPermissionRequest`, `#/$defs/PermissionOption`; `tool-calls.mdx:244-266,275-278,356-374` |
| 2 | `optionId` **MUST** be unique within the request | MUST -> CAPABILITY (proposed PERM-202) | `tool-calls.mdx:357`; `#/$defs/PermissionOption/properties/optionId` description |
| 3 | `command` subject: `command` and `cwd` are required, and `cwd` **MUST** be absolute | MUST -> CAPABILITY (proposed PERM-202) | `tool-calls.mdx:302-303`; `#/$defs/CommandPermissionSubject` |
| 4 | After a `cancelled` outcome the Agent **MUST NOT** proceed; an unmatched `optionId` **MUST** be treated as not approved; an unknown outcome **MUST NOT** be treated as approval | MUST; observable only through a `tool_call` subject (proposed PERM-203) | `tool-calls.mdx:340,346-349` |
| 5 | If a tool call's permission request is rejected or `cancelled`, the agent reports the tool call `cancelled`/`failed` rather than leaving it `pending` | indicative (no keyword) | `tool-calls.mdx:423` |
| 6 | Custom tool kinds / statuses / permission option kinds **MUST** begin with `_` | MUST -> CAPABILITY (existing ENUM-201) | `tool-calls.mdx:76,419,372` |
| 7 | Custom plan priorities / entry statuses / plan content types **MUST** begin with `_` | MUST -> CAPABILITY (ENUM-201; `plan.type` not yet checked) | `agent-plan.mdx:164,176,145` |
| 8 | Custom diff `operation`, `fileType`, and `patch.format` **MUST** begin with `_` | MUST, new at target (ENUM-201 candidate sites) | `tool-calls.mdx:685-686,700-701,662` |
| 9 | Every plan content variant **MUST** carry a `planId` | MUST -> CAPABILITY (existing PATCH-205) | `agent-plan.mdx:147` |
| 10 | Terminal `cwd` **MUST** be absolute when supplied; `terminalId` required | MUST -> CAPABILITY (existing PATCH-206) | `tool-calls.mdx:493-499,523-531` |
| 11 | Each terminal `data` value is independently base64 | MUST -> CAPABILITY (existing PATCH-207) | `tool-calls.mdx:536-537,566-570` |
| 12 | `title` **SHOULD** be on the first report of a `toolCallId`; `name` **SHOULD NOT** change | SHOULD -> ADVISORY (existing PATCH-208) | `tool-calls.mdx:41-54` |
| 13 | Blocked foreground work **SHOULD** report `requires_action`; requests for background activity may leave the session `idle` | SHOULD -> ADVISORY (existing PATCH-209) | `tool-calls.mdx:209,268`; `prompt-lifecycle.mdx:153,174,845,1074` |
| 14 | Statuses never go back to `pending`; `completed`/`failed`/`cancelled` are final; work after a final status goes on a new tool call | indicative (proposed PATCH-210) | `tool-calls.mdx:421,423` |
| 15 | When foreground work ends, the agent **SHOULD** give that work's unfinished tool calls a final status (tool calls listed in `background` are excluded) | SHOULD (proposed PATCH-211) | `tool-calls.mdx:423` |
| 16 | The agent **SHOULD** stop advertising `cancel` once a tool call is final or a terminal reports `exitStatus` | SHOULD (proposed PATCH-212) | `tool-calls.mdx:440,600`; `#/$defs/ToolCallCapabilities`, `#/$defs/TerminalCapabilities` descriptions |
| 17 | `ToolCallLocation.line` >= 1 (`0` invalid) | schema (B8), enforced by PROMPT-205/PERM-201 | `tool-calls.mdx:768-772`; `#/$defs/ToolCallLocation/properties/line` |
| 18 | `TerminalSize.cols`/`rows` in 1..65535 and required when `size` is present | schema, enforced by PROMPT-205 | `tool-calls.mdx:532-535`; `#/$defs/TerminalSize` |

## Details

### Existing rows

**ACP-PERM-201: citation-only.**
- Target citation: `docs/protocol/v2/draft/tool-calls.mdx:209,244-266,275-278,356-374` plus the unchanged schema pointers.
- `RequestPermissionRequest.required` = `[sessionId,title,options]` at both base and target. `PermissionOption.required` = `[optionId,name,kind]` at target. Appendix B shows only description changes for these two defs.
- The `236-263` base range gained two paragraphs inside it at target: the background-work request rule (`268`) and the subject-application rule (`270-273`). Neither is a PERM-201 concern. I recommend citing around them as shown rather than `244-278`.
- The `subject` changes (the `ToolCallPermissionSubject._meta` add, and the `cancelled` text) are additive or client-side.
- The test (`test_permission.py:21-55`) still matches: schema validation plus idle after a `selected` answer.
- Fixtures `asks_permission.py`, `conforming_full.py`, `prefixed_custom_permission_kind.py` and `unprefixed_custom_permission_kind.py` already use unique `optionId`s (`_base.py:756-760` and the two fixture overrides), so they stay conforming under the proposed PERM-202.

**ACP-PATCH-204: unchanged.** The schema pointers resolve at target (`ToolCallUpdate`, `ToolCallId`, `ToolCallContentChunk`, `TerminalOutput`, `TerminalExitStatus`).
- `TerminalExitStatus.exitCode` went from `uint32`/`minimum: 0` to `int64` (B9). PATCH-204's test never looks at `exitStatus`, so nothing to do. The schema loosening just stops `ACP-PROMPT-205` from flagging negative exit codes.
- Optional text improvement: the requirement text says "an update for a previously-unseen `toolCallId` is itself the create". At target a `tool_call_content_chunk` (`tool-calls.mdx:198-200`) and a permission `subject.toolCall` (`270-273`) can also create a tool call. The assertion itself does not change.
- Optional doc citation to add: `tool-calls.mdx:37-39,102-110,183-200`.

**ACP-PATCH-205: citation-only.** `agent-plan.mdx:147` ("Every plan content variant, including custom or future variants, **MUST** carry a `planId`."). Unchanged.
- `plan_removed` also requires `planId` (`#/$defs/PlanRemoved`, `required: ["planId"]`). Presence is already schema-checked by PROMPT-205. Extending PATCH-205 to check that `plan_removed.planId` is non-empty is optional and low value.

**ACP-PATCH-206 / ACP-PATCH-207: citation-only.** Text and tests still match: `terminalId` required, `cwd` absolute when supplied, chunk and snapshot base64 standalone.
- New `size` (`TerminalSize`, `cols`/`rows` required, 1..65535) and `capabilities` on `terminal_update` are schema-validated by PROMPT-205.
- New client-side text (`576-581`: clients SHOULD ignore invalid base64; agents SHOULD send output before `exitStatus`) does not change PATCH-207. Base64 validity is still the agent's MUST through "Its required `data` is RFC 4648 base64-encoded bytes" (`536-537`, `566-567`).

**ACP-PATCH-208: citation-only, test refinement recommended.**
- `tool-calls.mdx:41-54` keeps both SHOULDs ("include the title the first time they report a `toolCallId`", and `name` "**SHOULD NOT** change it later except to correct metadata").
- The base paragraph "For `name` specifically, omission leaves ... `null` clears it" was dropped. Target `102-108` now says `null` "reset[s] the field to its default". The test already ignores `null` names.
- New first-report paths: a `tool_call_content_chunk` for an unseen id creates the tool call (`198-200`), and a permission `subject.toolCall` with a first-seen id creates it (`270-273`). The test (`test_patches.py:224-258`) treats only the first `tool_call_update` as the first report.
- Two consequences:
  1. An agent that introduces `call_1` through a permission `subject.toolCall` with a `title`, then sends `tool_call_update{call_1, status}` without one, is reported FAIL (a false ADVISORY FAIL).
  2. An agent whose first report is a chunk (which can't carry a title) is not flagged, although by the letter of the rule it missed the SHOULD.
- Recommendation: merge, in wire order, `tool_call_update`s, chunks, and `session/request_permission` `params.subject.toolCall` where `subject.type == "tool_call"`. Judge the title on the first of those. Whether a chunk-first report should FAIL is a minor DECISION NEEDED; my recommendation is FAIL, since it follows the letter of `42-43` and the row is ADVISORY anyway.

**ACP-PATCH-209: changed text (scope narrowed).**
- Citations: `tool-calls.mdx:209`; prompt-lifecycle base `125,773,994` -> target `153,845,1074` (the prompt-lifecycle researcher may refine these).
- New rule: "A permission request for listed background work **SHOULD** reference the listed item in `subject`, by `toolCallId` or `terminalId`. The Agent **MUST** list that work before sending the request" (`tool-calls.mdx:268`). Also: "If it belongs only to independent background activity, the session may remain `idle`" (`prompt-lifecycle.mdx:174`, `845`).
- So a permission request whose `subject` references (by `toolCall.toolCallId`, or the `command` subject's `toolCallId`/`terminalId`) an item in the most recent `background` list on a `state_update` does not need `requires_action`.
- Proposed text: "When the agent sends `session/request_permission` for the prompted session during a turn, other than one whose `subject` references an item in the latest reported `background` list, it reports `state_update.state == "requires_action"` for that session at some point in the turn (SHOULD)."
- Test change: collect `background` from the turn's `state_update`s (in wire order), drop requests whose subject ids match a listed item, and SKIP if none remain. ADVISORY, so the verdict is unaffected. Today's fixtures never emit `background` or `subject`, so test_cli expectations are unchanged.

**ACP-ENUM-201: changed text (site list).**
1. **Constant sets (required, or the meta-test goes red):** at target, `ToolCallStatus` consts = `{pending,in_progress,paused,completed,failed,cancelled}` and `ToolCallContent.type` consts = `{content,diff,terminal,session}`. `src/tck/v2/protocol.py:76` and `:107` must add `paused` and `session`, or `tests/v2/test_validation.py:176-196` fails after the schema re-vendor. The other sets the test checks are unchanged at target: `ToolKind`, `PlanEntryPriority`, `PlanEntryStatus`, `PermissionOptionKind`, `StateUpdate.state`, and `SessionUpdate.sessionUpdate`. `SessionUpdate` already contains `plan_removed` and the rest. I diffed the const sets directly.
2. **Citations:** `tool-calls.mdx:76` (tool kind), `372` (permission option kind), `419` (status; the base hunk `-380,1 +419,42` will be "Needs review"); `agent-plan.mdx:164,176`. The extensibility part is owned elsewhere (now around `extensibility.mdx:233-240`).
3. **Pre-existing test bug (follow-up, not caused by the spec change):** `test_enums.py:118-121` does `for block in update.get("content") or []` for both `tool_call_update` and `tool_call_content_chunk`. A chunk's `content` is a single object (`#/$defs/ToolCallContentChunk/properties/content` -> `ToolCallContent`), so iterating it yields key strings and the chunk's `type` is never checked. A chunk with `content.type: "sorcery"` passes today.
4. **Recommended new sites.** Each has an explicit "Custom ... **MUST** begin with `_`" rule and a fallback branch in the schema. Each would need a new hand-copied set plus a meta-test line:
   - `plan_update.plan.type`: `PlanUpdateContent` consts `{items,file,markdown}`; `agent-plan.mdx:145`. Pre-existing rule.
   - Diff `changes[].operation`: `DiffChange` discriminator `operation`, consts `{add,delete,modify,move,copy}`; `tool-calls.mdx:685-686`. New MUST.
   - Diff `changes[].fileType`: `DiffFileType` `{text,binary,directory,symlink}`; `700-701`. New MUST.
   - Diff `patch.format`: `DiffPatchFormat` `{git_patch}`; `662`. New MUST.
   - Permission `subject.type`: `RequestPermissionSubject` `{tool_call,command}`. Only the general extensibility rule applies; `tool-calls.mdx:263` says "Custom or future subject types may appear" with no explicit `_` rule.
   - A `tool_call` subject's nested `toolCall.kind`/`.status`/`.content[].type`: applied "exactly like a `tool_call_update`", `270-273`.
   - Not mine: `state_update.background[].type` (`BackgroundWork`), owned by the prompt-lifecycle researcher.

   DECISION NEEDED on how many to add. I recommend all of them except `subject.type`, because the doc gives an explicit MUST for each. Keep the "curated, non-exhaustive" wording.

### New requirements

**ACP-PERM-202 (CAPABILITY, `capabilities.session`)**
- Text: "Within each `session/request_permission` the agent sends, `options[].optionId` values are pairwise distinct, and a `subject` with `type: "command"` carries an absolute `cwd`. SKIPPED when no permission request is observed."
- Citation: `docs/protocol/v2/draft/tool-calls.mdx:302-303,357 @ 3961af94fa62`; `schema/v2/schema.unstable.json#/$defs/CommandPermissionSubject`.
- Tier: both rules are bold **MUST**s, and the method only exists under `capabilities.session`, the same tiering rule as PERM-201.
- Why not fold into PERM-201: both violations are schema-valid (`AbsolutePath` is `{"type":"string"}`, and no `uniqueItems` applies to option ids). A separate id lets a fixture trip it alone.
- Observation: scan `turn.client_requests_seen`, the same evidence PERM-201 uses, and check `os.path.isabs`-style absoluteness the way PATCH-206 does.
- Fixture: `duplicate_permission_option_id.py`, an `AsksPermissionAgent` whose `_permission_options()` returns two options with `optionId: "allow-once"` and different kinds. Expected to FAIL only PERM-202. Note that `run_prompt` picks the first `allow_*`, so the turn still completes. Optional second fixture: `permission_command_relative_cwd.py`.

**ACP-PERM-203 (DECISION NEEDED: CAPABILITY recommended, `capabilities.session`)**
- Text: "When the client answers a `session/request_permission` whose `subject` is `{type: "tool_call", toolCall: {toolCallId: X}}` with a `cancelled` outcome, the agent never afterwards reports X with `status: "completed"` (on a `tool_call_update` or on a later subject's `toolCall`). SKIPPED when no such request is observed."
- Citation: `tool-calls.mdx:340` ("After a `cancelled` outcome, the Agent **MUST NOT** proceed with the operation") and `423` ("If a tool call's permission request is rejected or answered with `cancelled`, the Agent reports the tool call as `cancelled` or `failed` rather than leaving it `pending`") `@ 3961af94fa62`.
- Why CAPABILITY: the rule is a MUST. Reporting the very tool call the permission was for as `completed` contradicts both `340` and `423`, so there is little false-FAIL risk.
- Why not stricter: also requiring a final `cancelled`/`failed` status before idle is only the indicative `423`. I recommend leaving that to PATCH-211 (ADVISORY).
- How to drive it: "Clients also send `cancelled` when ... the Client declines it by policy" (`340`), so answering `cancelled` is a legitimate client behaviour. `run_prompt` needs a mode that answers permission requests with `{"outcome":"cancelled"}` without having sent `session/cancel`.
- Optional second probe under the same id: answer `selected` with an `optionId` not offered ("If `optionId` doesn't match an offered option, the Agent **MUST** treat the request as not approved", `346-347`), with the same "not completed" assertion.
- Fixture: `proceeds_after_cancelled_permission.py`. It sends `tool_call_update{X, pending}`, asks permission with `subject.tool_call` X, and on any outcome sends `tool_call_update{X, completed}`, then a normal idle.
- Caveat: today's `AsksPermissionAgent` ends the turn with `idle(cancelled)` on a `cancelled` answer. The spec does not say which stop reason a by-policy decline should give. Do not assert on it.

**ACP-PATCH-210 (DECISION NEEDED: ADVISORY recommended)**
- Text: "Per `toolCallId`, the reported `status` never returns to `pending` after any other status, and never changes after `completed`/`failed`/`cancelled`."
- Citation: `tool-calls.mdx:421` ("Statuses never go back to `pending`") and `423` ("`completed`, `failed`, and `cancelled` are final. If work goes on after its tool call is final, the Agent reports it on a new tool call."). Also `prompt-lifecycle.mdx:184` ("The Agent does not reopen a tool call that has a final status. It starts a new one instead."), owned by the prompt-lifecycle researcher.
- Tier: these are definitional invariants with no RFC 2119 keyword, so I recommend ADVISORY. The argument for CAPABILITY is that clients rely on finality.
- Observation: track the effective status per id in wire order. Remember `status: null` resets to the default `pending` (`102-107`), so a `null` after a non-pending status is also a regression.
- Fixture: `tool_call_reopens_after_final.py` (sends `completed`, then `in_progress` for the same id).

**ACP-PATCH-211 (ADVISORY)**
- Text: "When the idle state_update ending a turn arrives, every tool call reported for the prompted session during that turn has a final status, unless it appears in that idle's (or the latest) `background` list."
- Citation: `tool-calls.mdx:423` ("When foreground work ends, ... the Agent **SHOULD** give each of that work's unfinished tool calls a final status. Tool calls in the session's `background` list are not part of that work.").
- Tier: SHOULD, so ADVISORY.
- Observation: the effective status at the idle line. If `background` is not reported at all, still judge it: the agent "**SHOULD** keep that tool call `pending`, `in_progress`, or `paused` and list it" (`prompt-lifecycle.mdx:184`), so an unlisted unfinished tool call misses a SHOULD either way.
- Fixture: `leaves_tool_call_in_progress.py`.
- Note: `_base.py:544-562`'s rich turn already finishes its tool call `completed`, so `conforming_full.py` passes.

**ACP-PATCH-212 (ADVISORY; flag overlap with the cancellation researcher)**
- Text: "Once a tool call's effective status is final, or a terminal's effective `exitStatus` is concrete, its effective `capabilities.cancel` is absent or `null`. Effective means after applying the nullable-patch rule: omitted leaves it unchanged, `null` clears it, an object replaces it."
- Citation: `tool-calls.mdx:440` and `600`; `#/$defs/ToolCallCapabilities`, `#/$defs/TerminalCapabilities`.
- Gotcha: an agent that sets `status: "completed"` without touching `capabilities` keeps advertising `cancel`. Real agents are likely to trip this.
- Fixture: `advertises_cancel_after_final.py`.

**Optional, low priority (pre-existing or Draft-only rules that were never registered):**
- **ACP-DIFF-201 (CAPABILITY, pre-existing MUSTs):** for any `diff` content item with `patch.format == "git_patch"`:
  - every path in the `---`/`+++`/`rename from|to`/`copy from|to` lines is absolute or `/dev/null`;
  - no path has an `a/`/`b/` prefix;
  - each patch path appears in `changes` (`path` or `oldPath`).

  Citation: `tool-calls.mdx:615-617,652-661`. Rarely observable in a "hi" turn; fixture `diff_relative_patch_paths.py`. "Each `path` value appears in at most one entry of `changes`" (`622`, new, indicative) could join it as ADVISORY.
- **ACP-PLAN-201 (CAPABILITY):** a `file` plan's `uri` is an absolute URI (has a scheme). Citation: `agent-plan.mdx:119` (MUST, pre-existing, unstable variant).
- **ACP-PATCH-213 (ADVISORY):** no `terminal_output_chunk` for a terminal after its `exitStatus` became concrete. Citation: `tool-calls.mdx:578` ("Agents **SHOULD** send all output before a concrete `exitStatus`").
- **ACP-PATCH-214 (ADVISORY or INFORMATIONAL; DECISION NEEDED):** a `type: "session"` tool-call content item's `sessionId` is one the client created, or was announced by an earlier `subagent_update`. Citation: `tool-calls.mdx:740-742`. The wording is a lowercase "must", in a Draft-only section. This is the same shape of check `ACP-PROMPT-205` already does for child `sessionId`s.

### Ledger (deliberate non-requirements)

| Citation @ 3961af94fa62 | Statement | Reason |
|---|---|---|
| `tool-calls.mdx:268` | Agent **MUST** list background work before sending a permission request for it; **SHOULD** reference it in `subject` | Unobservable: whether a request belongs to background work is agent-internal. Cross-ref to the prompt-lifecycle background-list rows. |
| `tool-calls.mdx:349` | Agents that do not understand an outcome **MUST NOT** treat it as approval | Mostly unobservable. Survival is covered by ENUM-203, and the observable part through a `tool_call` subject is covered by proposed PERM-203. |
| `tool-calls.mdx:385,387-389` | Agent security SHOULDs (option `name` vs `kind`, act per `kind`, re-request on target change, scope of remembered decisions, no oversight-reducing switch) | Semantic or agent-internal; unobservable. |
| `tool-calls.mdx:376-380` | Agent owns remembered decisions (scope, duration) | Agent-internal. |
| `tool-calls.mdx:466` | Implementations **SHOULD** preserve unknown content payloads when storing/replaying/proxying | Needs an agent that echoes client-originated unknown content; out of scope for the agent-under-test. |
| `tool-calls.mdx:496-497` | `terminalId` **MUST NOT** be reused for a different terminal | Unobservable ("different terminal" is agent-internal). |
| `tool-calls.mdx:456,602` | Client **MUST NOT** send `tool_call/cancel`/`terminal/cancel` unless advertised | Client-side rule. It binds the TCK's own probes; owned by the cancellation researcher. |
| `agent-plan.mdx:139` | Agents **SHOULD** send `plan_removed` when a plan is cancelled; Clients **MUST** ignore unknown `planId` | Agent part unobservable (cancellation intent is internal); client part client-side. |
| `agent-plan.mdx:186` | Agent **MUST** send the complete entry list in each `items` update | Unobservable: the client can't know the true entry set. |

Client-only prose with no agent obligation (`76`, `264`, `379`, `384`, `386`, `419`, `421` first sentence, `576`, `583`, `618-620`, `726`, `774`; `agent-plan.mdx:71,184`) is skipped as pure client-side.

### B-list hits

- **B8** (`ToolCallLocation.line` min 0 -> 1; `0` invalid, `tool-calls.mdx:768-772`): no v2 fixture emits `locations`. I grepped `tests/fixtures/agents/v2/` for `locations`/`"line"` and found nothing. No test or `test_cli.py` expectation is affected. Enforcement is automatic through PROMPT-205 (updates) and PERM-201 (a subject's `toolCall.locations`) after the re-vendor. An optional pin fixture is `tool_call_location_line_zero.py`, which FAILs `ACP-PROMPT-205`.
  - Note: the target schema marks `line` with `x-deserialize-default-on-error: true`, meaning a lenient receiver may default it. `tck.v2.validation` ignores that keyword and validates strictly. That is correct for judging the emitter; I did not check whether the spec documents the keyword's meaning.
- **B9** (`exitCode` int64): loosened; no fixture emits `exitStatus`; no impact.
- **B12** (`paused`; `CancelledPermissionOutcome`): `paused` must be added to `TOOL_CALL_STATUS` (see ENUM-201). The `cancelled` outcome wire shape is unchanged; it only gained optional `_meta`. `run_prompt`'s `{"outcome":"cancelled"}` (`_helpers.py:1025`) stays valid.
- `ToolCallContent` + `session`: must be added to `TOOL_CALL_CONTENT_TYPE` (`protocol.py:107`).

### Spec-map sections

Neither doc is in `spec-tracker/maps/v2.toml` (the only mention is a `reason` string at line 62), so there are no section addresses to re-case. The headings at target, for reference:
- `tool-calls.mdx`: `Reporting`, `Updating`, `Streaming content`, `Requesting permission` > `Permission options` / `Security`, `Status` > `Cancelling tool calls`, `Content` > `Regular content` / `Display-only terminals` > `Cancelling terminals` / `Diffs` / `Sessions (unstable)`, `Following the Agent`.
- `agent-plan.mdx`: `Creating plans` > `Item-based plans`, `Unstable plan operations` > `Markdown plans` / `File plans`, `Removing plans`, `Extensibility`, `Plan entries`, `Updating plans` > `Dynamic planning`.

Recommendation: keep both docs non-core. They are feature pages whose foreground-state rules are restated from `prompt-lifecycle.mdx` (already core). `Status` is the only candidate for core, because the status-finality rules (PATCH-210/211) and `paused` touch background work, but it is not needed.

## Testability notes

- Everything here is vacuous (SKIP) against agents that don't emit the relevant variant. As `test_patches.py:10-15` notes, real v2 SDK agents mostly don't, so the fixtures carry the PASS evidence.
- PERM-203 needs a new `run_prompt` answering mode: decline by policy with `cancelled`, without `session/cancel`. Without it the rule is unobservable.
- PATCH-208, PATCH-209 and ENUM-201 refinements need wire-order merging of `turn.updates` and `turn.client_requests_seen`, so a permission `subject.toolCall` is processed where it was received. `prompt-lifecycle`/`tool-calls.mdx:270-272` say subjects apply "in the order it was received relative to `session/update` notifications".
- PATCH-210/211/212 need a per-id patch-state tracker implementing the upsert rules: omitted = unchanged, `null` = reset to default (`pending` for status, cleared for `capabilities`), concrete = replace. Fields are listed at `tool-calls.mdx:102-110,440,523-526`.
- Expected `tests/v2/test_cli.py` deltas: none from citation remaps. New fixtures add new expected FAIL sets. The `protocol.py` set update is needed only to keep `tests/v2/test_validation.py` green.

## Discrepancies

- **Schema description vs doc on `ToolCallUpdate` null semantics:** the `#/$defs/ToolCallUpdate` description says "`null` clears or unsets the value". The doc (`tool-calls.mdx:104`) says "reset the field to its default", and the defaults include `status: pending` and `kind: other` (`105-108`). These agree for clients, but a status regression check (PATCH-210) must treat `status: null` as a reset to `pending`. Minor; not a conflict.
- **Status names:** `prompt-lifecycle.mdx:181` says "`pending` and `paused` tool calls are still live", and `tool-calls.mdx:404-407` defines `paused`. They are consistent.
- Otherwise none found between doc and schema for the rows judged. SDKs were not consulted.

## Open questions

1. Tier decisions: PERM-203 (CAPABILITY vs ADVISORY) and PATCH-210 (ADVISORY vs CAPABILITY). Also: how many new ENUM-201 sites to add.
2. Is the optional low-priority batch (DIFF-201, PLAN-201, PATCH-213, PATCH-214) in scope for this spec update, or deferred? These rules are mostly pre-existing, not introduced in this range.
3. PATCH-212 overlaps `tool_call/cancel`/`terminal/cancel`. The cancellation researcher should confirm ownership.
4. Pre-existing ENUM-201 test bug (chunk `content` never checked): fix it in the same slice as the `paused`/`session` set update?
