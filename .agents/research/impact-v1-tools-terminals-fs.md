# v1 impact: tool-calls.mdx, terminals.mdx, file-system.mdx (beac4ba -> 3961af9)

**Sources checked:** agent-client-protocol (worktree `agent-client-protocol-2`) base `beac4ba96190`, target `3961af94fa62`; acp-rust-sdk @ `e75d6f19fabb` (2026-11-09); acp-python-sdk @ `8a9940744d0a` (2026-11-09, consulted, nothing load-bearing found); TCK registry/tests on branch `eugenethedev/update-spec` @ `200baba`.
**Confidence:** high for classifications of existing rows and for the `session` content gating. Medium for the two proposed ADVISORY permission rows. Their observable proxy, a file side effect, is my design, not something the spec defines.

## Answer

None of the existing rows that cite these three docs changes meaning. ACP-CLIENTCAP-001/002 and ACP-PROMPT-004 are **unchanged**: their cited lines and `$defs` pointers resolve to identical text. One existing row needs a **text and test change**: ACP-CLIENTCAP-007. The new unstable `session` `ToolCallContent` variant falls under the v1 `subagents` client-capability gate (`tool-calls.mdx:358`, `rfds/subagents.mdx:76-78,644-645`), and today's test only scans `sessionUpdate` kinds, so it would miss that content.

The new "Security" text in all three docs is almost entirely client-side or semantic. Two agent-side SHOULDs can be observed from the client: honouring a `reject_once` selection (`tool-calls.mdx:247`), and not treating an unrecognised outcome as approval (`tool-calls.mdx:249`). I propose them as optional ADVISORY rows ACP-PERM-001/002 (DECISION NEEDED). Everything else goes to the ledger (10 entries). One of those is a DECISION NEEDED: `line` is now documented 1-based, but the v1 schema still deliberately allows `0`.

The brief also names ACP-TOOL-*, ACP-PERM-*, ACP-TERMINAL-* and ACP-FS-*. **No such rows exist in the v1 registry.** v1's fs/terminal rules live in ACP-CLIENTCAP-001/002. ACP-CLIENTCAP-004/005 (notice/compaction) cite none of my docs. They are unaffected by them, and their own cited docs belong to other reports.

## Summary table

| Id | Classification | Note |
|----|----------------|------|
| ACP-CLIENTCAP-001 | unchanged | `file-system.mdx:10,29` text identical at target. The heading recase on line 8 keeps the line count. |
| ACP-CLIENTCAP-002 | unchanged | `terminals.mdx:10,26` identical at target. |
| ACP-PROMPT-004 | unchanged | `ToolCallLocation/properties/path` and `Diff/properties/path` are byte-identical. Only the sibling `line`/`oldText` descriptions changed. `overview.mdx:230` is unchanged. The test ignores non-`diff` content, so the new `session` variant does not affect it. |
| ACP-CLIENTCAP-004 | unchanged (by these docs) | Cites prompt-turn/initialization only. Left to those reports. |
| ACP-CLIENTCAP-005 | unchanged (by these docs) | Same as 004. |
| ACP-CLIENTCAP-007 | **changed text + test** (and a citation shift) | Extend it to `session` tool-call content. The RFD citation `:72-74` becomes `:76-78`, which `--fix` handles. **DECISION NEEDED:** extend 007 or add ACP-CLIENTCAP-008. I recommend extending 007. |
| ACP-PERM-001 (new) | new, ADVISORY | Agent does not carry out an operation after the client selects its `reject_once` option. **DECISION NEEDED** (add or ledger). I recommend adding it. |
| ACP-PERM-002 (new) | new, ADVISORY | Agent does not treat a `selected` outcome with an unrecognised `optionId` as approval. **DECISION NEEDED**. I recommend adding it. |
| LEDGER-TFS-01..10 | new ledger entries | See the ledger section. LEDGER-TFS-09 (`line` 1-based) is a **DECISION NEEDED**: ledger or INFORMATIONAL. I recommend the ledger. |

## Requirements (new or changed only)

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| CLIENTCAP-007 (changed) | No `subagent_update`/`session_message`/`session_message_chunk` updates, and no `{"type":"session"}` item in any `tool_call`/`tool_call_update` `content` (or `session/request_permission` `toolCall.content`), unless `clientCapabilities.subagents` was advertised | MUST | `docs/rfds/subagents.mdx:76-78,644-645 @ 3961af94fa62` (RFD, Active, proposal); `docs/protocol/v1/draft/tool-calls.mdx:337-360 @ 3961af94fa62` (":358 Agents send it only when the Client advertises the `subagents` capability"); `schema/v1/schema.unstable.json#/$defs/ToolCallContent` (4th `oneOf`, `const: "session"`), `#/$defs/SessionReference` |
| ACP-PERM-001 | After the client answers `session/request_permission` by selecting the offered option whose `kind` is `reject_once`, the agent does not carry out the operation | SHOULD (ADVISORY) | `docs/protocol/v1/draft/tool-calls.mdx:231-234,247 @ 3961af94fa62`; `docs/protocol/v1/draft/security.mdx:12 @ 3961af94fa62` ("the Agent ... is responsible for honoring the user's decision") |
| ACP-PERM-002 | After the client answers with `{"outcome":"selected","optionId":<id not among the offered options>}`, the agent does not carry out the operation | SHOULD NOT (ADVISORY) | `docs/protocol/v1/draft/tool-calls.mdx:249 @ 3961af94fa62`; `schema/v1/schema.unstable.json#/$defs/SelectedPermissionOutcome` |

## Details

### What changed in the three docs (target line numbers)

- **file-system.mdx**: four heading recases (lines 8, 31, 78). New `## Security` at **121-126**. It holds two client SHOULDs: check paths against the session root set at time of use (125), and ask before writes to execution- or approval-controlling files (126). Line 123 says the client is responsible and that agent permission requests "do not replace the Client's own checks". No agent-side rule was added.
- **terminals.mdx**: heading recases, and a reword at line 104 with the same meaning. New `## Security` at **284-289**, client SHOULDs only. The client keeps `cwd` inside the root set and applies its own policy to the full `command`/`args`/`env`, and auto-approvers include `env` (288). The client neutralises control sequences in `terminal/output` (289).
- **tool-calls.mdx**:
  - Intro reworded (6-10). The `name` field text (42-49) only changes punctuation. Its SHOULDs already existed at base.
  - New "remembered decisions" paragraph (**238-242**). The Agent owns `allow_always`/`reject_always` decisions: it stores them, chooses their scope and lifetime, and applies them by not asking again. `kind` is a UI hint, and `name` describes the scope. This is descriptive, with no RFC keyword.
  - New `### Security` (**244-252**). Line 246 is a client rule. Line 247 holds two agent rules: a `name` must not contradict its `kind`, and the agent acts per the selected option's known `kind`. Line 248 covers automatic approval (client-side, per :194 "Clients MAY automatically allow or reject"). Line 249: agent must not treat an unrecognised outcome as approval. Line 250: agent performs only the approved operation and re-requests if the target changes. Line 251: agent states a remembered decision's scope in `name` and does not apply it beyond that. Line 252: agent does not switch to a lower-oversight mode or config without user action.
  - New `### Sessions (unstable)` (**337-360**). The `{"type":"session","sessionId":...}` content item is display-only, can appear several times per tool call, carries optional nullable `_meta`, and is sent "only when the Client advertises the `subagents` capability" (358). The referenced session "must already be known through ordinary session setup or a `subagent_update` announcement" (350-351). The RFD makes that a **MUST** (`rfds/subagents.mdx:636-638`).
  - `ToolCallLocation.line` is documented as "1-based" (**377-381**).
  - New closing sentence (**383**): "Locations are display metadata and do not grant file access. Clients **SHOULD NOT** automatically open locations outside the session's root set."

### Schema at target (`schema/v1/schema.unstable.json`)

- `ToolCallContent`: the only structural change in my area. A fourth `oneOf` branch `{type: const "session"}` with `allOf: [$ref SessionReference]`, under discriminator `type`.
- `SessionReference` (new): `required: ["sessionId"]`, `sessionId` is a `$ref SessionId`, `_meta` is `object|null`. The description repeats the display-only and must-already-be-known rules.
- `ToolCallLocation.line`: the description now reads "Optional 1-based line number within the file." It is still `type [integer,null], format uint32, minimum: 0`. Upstream commit `51551940` ("fix(unstable-v2): make ToolCallLocation.line 1-based (#2546)") says explicitly: "v1 docs and its schema description now say the line is 1-based, **without a schema change**." v2 moved to `minimum: 1` ("`0` is invalid"), and its deserializer drops `0` as no line.
- `CreateTerminalRequest`: `args`/`env` gained `x-deserialize-default-on-null: true`. This is a generator hint with no JSON Schema type change. Under `clientCapabilities: {}` the agent never sends this request, so it has no TCK impact.
- `RequestPermissionOutcome`: description only (`Cancelled` -> `cancelled`, and the link now points at the v1 draft). It is still **closed** (`cancelled` | `selected`). `PermissionOptionKind` is unchanged and closed (4 consts).
- Every other `ToolCall*`, `PermissionOption*`, `RequestPermission*`, `*Terminal*`, `*TextFile*` and `FileSystemCapabilities` `$def` changed in descriptions only. I checked this by comparing the `$defs` with `description`/`title` stripped.

### ACP-CLIENTCAP-007: proposed change

- Old text: "The agent MUST NOT send `subagent_update`, `session_message`, or `session_message_chunk` unless the client advertised `clientCapabilities.subagents` ..."
- Proposed text: the same, plus ", nor include `session` content (`{"type": "session"}`) in a tool call, tool call update, or permission request's `toolCall`". Keep "checked the same way as ACP-CLIENTCAP-004" and the vacuous-pass sentence.
- Citation: keep `prompt-turn.mdx` (another report owns it). Move `docs/rfds/subagents.mdx:72-74` to `:76-78` (`--fix` will do this). Add `docs/rfds/subagents.mdx:644-645` and `docs/protocol/v1/draft/tool-calls.mdx:358`, and keep or add `schema/v1/schema.unstable.json#/$defs/SessionReference`.
- Test change (`test_client_capabilities.py::test_no_subagent_update_without_client_capability`): today it collects only `session_update_kind`s. It must also walk `params.update.content[]` of every received `tool_call`/`tool_call_update`, and `params.toolCall.content[]` of every received `session/request_permission`, flagging any item with `type == "session"`. The shared helper `_session_update_kinds_with_no_client_capabilities` returns kinds only, so it needs to return, or also expose, the transcript entries.
- Why extend 007 rather than add 008: it is the same capability and the same RFD gate ("covered by the `subagents` Client capability like the rest of this RFD"), so a violation cannot be mis-attributed across capabilities. Choose 008 only if per-construct reporting is wanted. **DECISION NEEDED** (recommend: extend 007).
- Tier stays MANDATORY. The doc sentence carries no keyword, but the RFD's v1 rule is an explicit **MUST NOT** (`:76`), and 007 already rests on that RFD.
- Schema-refresh interaction: before the vendored schema is refreshed, a `session` item fails `ToolCallContent`'s closed `oneOf` in validation. After the refresh it validates, so only CLIENTCAP-007 catches it.

### ACP-PERM-001 / ACP-PERM-002 (new, proposed)

- **Tier: ADVISORY.** Line 247 is "SHOULD act on a selected option according to its known `kind`" and line 249 is "SHOULD NOT treat an outcome they don't recognize as approval". Neither ever fails the verdict.
- **Capability gate:** none. Sending `session/request_permission` is MAY (`tool-calls.mdx:138`), so both rows SKIP ("no permission request observed") when the agent never asks. Compare v2's ACP-PERM-201 vacuity.
- **Why only these two rows:** in v1 the agent executes tools itself (`security.mdx:12`), so the TCK cannot see the operation on the wire. With the TCK's `clientCapabilities: {}`, an agent that edits does so directly on disk in `cwd = tmp_path`, so a file side effect in `tmp_path` is observable.
- **Proposed method:**
  - Write a prompt that asks the agent to create a named file in `cwd`, e.g. `tck-permission-probe.txt`.
  - Answer the first `session/request_permission` with the response under test.
    - PERM-001: `selected` with the `optionId` whose `kind == "reject_once"`. SKIP if no such option is offered.
    - PERM-002: `selected` with `optionId: "_tck_unrecognized_option"`.
  - Answer any later permission request for the same turn with `cancelled`, or with reject again, so that a re-ask is not an approval path.
  - Let the turn end.
  - FAIL if the probe file exists in `tmp_path`.
- **Secondary signal (do not use alone):** a `tool_call_update` with `status: "completed"` for the rejected `toolCallId`. The spec does not say which status a rejected tool call gets (hypothesis: `failed`, or no further update), so status alone could give a false FAIL.
- **Harness note:** `run_prompt` always selects the *first* option (`_helpers.py:300-301,402-413`). These rows need a per-test permission policy hook. That is a programmer decision, not a protocol question.
- **PERM-002 caveat:** the TCK deliberately sends a non-conforming client response, since `SelectedPermissionOutcome.optionId` should name an offered option. Treat it like the other robustness probes. The v1 outcome enum is closed, so an unknown-`optionId` `selected` is the only schema-valid way to send an "unrecognised outcome". A schema-invalid `outcome` value is a separate, uglier probe. I do not recommend it.
- **Suggested fixtures:**
  - `perm_ignores_reject.py`: requests permission with allow_once/reject_once options, then writes `tck-permission-probe.txt` into its cwd whatever the outcome. It trips PERM-001 and PERM-002.
  - `perm_unknown_option_is_approval.py`: honours `reject_once`, but treats any `optionId` it doesn't know as allow. It trips PERM-002 only.
- **DECISION NEEDED** (add or ledger). I recommend adding both as ADVISORY. They are the only agent-side permission SHOULDs with a clean, deterministic fixture and a real-agent signal that is not a model-semantics judgement. If the orchestrator prefers no model-provoked tests here, ledger them with the reason "requires the agent to choose to request permission; signal is a side effect, not wire traffic."

## Ledger entries (deliberate non-requirements)

Format follows `spec-tracker/maps/v1.toml:18-22` (`citation`, `statement`, `reason`). Every citation ends `@ 3961af94fa62`.

| Key | Citation | Statement | Reason |
|-----|----------|-----------|--------|
| LEDGER-TFS-01 | `docs/protocol/v1/draft/file-system.mdx:121-126` | Clients check `fs/*` paths against the session root set at time of use and ask before writes to execution- or approval-controlling files; agent permission requests don't replace those checks. | Client-side. The TCK is the client and answers `fs/*` with `-32601`. |
| LEDGER-TFS-02 | `docs/protocol/v1/draft/terminals.mdx:284-289` | Clients keep terminal `cwd` inside the root set, apply their own policy to full `command`/`args`/`env` (auto-approvers include `env`), and neutralise control sequences in `terminal/output`. | Client-side. |
| LEDGER-TFS-03 | `docs/protocol/v1/draft/tool-calls.mdx:246,248` | Clients describe the operation from `kind`/`locations`/content, present `title` as Agent-authored, show commands/paths in full; automatic approval does not rely only on `title` or option `name`. | Client-side. See open question 1 on the TCK's own auto-approval. |
| LEDGER-TFS-04 | `docs/protocol/v1/draft/tool-calls.mdx:247` (first clause) | Agents do not give a permission option a `name` that contradicts its `kind`. | Needs a natural-language judgement of `name`. Not mechanically decidable. |
| LEDGER-TFS-05 | `docs/protocol/v1/draft/tool-calls.mdx:250` | Agents perform only the approved operation and request again if the command or resolved target changes. | Agent-internal. The operation is not on the wire in v1. |
| LEDGER-TFS-06 | `docs/protocol/v1/draft/tool-calls.mdx:238-242,251` | The Agent owns remembered (`allow_always`/`reject_always`) decisions, states their scope in the option `name`, and does not apply them beyond it. | Scope and lifetime are agent-defined and stated in free text, so unobservable. Probing it would mean selecting `allow_always`, which may persist on the operator's machine (unsafe). |
| LEDGER-TFS-07 | `docs/protocol/v1/draft/tool-calls.mdx:252` | Agents do not switch to a mode or configuration that reduces user oversight without user action. | Whether a mode "reduces oversight" is semantic. Agents may legitimately change modes themselves. |
| LEDGER-TFS-08 | `docs/protocol/v1/draft/tool-calls.mdx:383` | Locations are display metadata and grant no file access; Clients do not auto-open locations outside the root set. | Client-side. The agent-side counterpart is in the session-setup report (`session-setup.mdx:473`). |
| LEDGER-TFS-09 | `docs/protocol/v1/draft/tool-calls.mdx:377-381`; `docs/protocol/v1/draft/overview.mdx:231`; `schema/v1/schema.unstable.json#/$defs/ToolCallLocation/properties/line` | `ToolCallLocation.line` is 1-based. | Not enforced. The v1 schema deliberately keeps `minimum: 0` (upstream `51551940`), the statement has no RFC keyword, and the v2 SDK tolerates `0` as "no line". **DECISION NEEDED:** ledger (recommended) or INFORMATIONAL ACP-PROMPT-005 ("no `locations[].line` of `0`"), which would be observable and fixture-able. |
| LEDGER-TFS-10 | `docs/protocol/v1/draft/tool-calls.mdx:349-351`; `docs/rfds/subagents.mdx:636-638` | A `session` tool-call reference names a session already known through session setup or a prior `subagent_update`. | Applies only when the client advertises `subagents`, which the TCK never does. Provoking subagent spawns is model-driven, and the feature is unstable. Revisit if a `subagents`-advertising test is added. |

Not ledgered, because it is pure prose or covered elsewhere: the `name` SHOULDs at `tool-calls.mdx:48-49` (unchanged since base), terminal `release` display SHOULD `terminals.mdx:282` (client, unchanged), and `tool-calls.mdx:358-360` "task reported as a session-directed message" (an RFD SHOULD, in the prompt-turn/subagents report's scope).

## Testability notes

- CLIENTCAP-007 extension: fully observable, and deterministic with a fixture. A conforming agent under `{}` never emits `type: "session"` content. Suggested fixture: `session_content_without_subagents.py` emits one `tool_call` whose `content` includes `{"type":"session","sessionId":<its own session id>}`. Reusing its own session id keeps "must already be known" satisfied, so only the gate trips. It should trip only ACP-CLIENTCAP-007, after the schema refresh.
- PERM-001/002: observable only if the agent asks permission and the operation has a file side effect in `cwd`. Otherwise SKIP, not PASS. They are race-free, because the decision is synchronous on the permission response.
- Everything in the ledger is unobservable from the client position, or is a rule on the TCK's own behaviour.

## Discrepancies

1. `ToolCallLocation.line`: the doc and schema description say "1-based" (`tool-calls.mdx:378`, `overview.mdx:231`), while the schema has `minimum: 0`. This is deliberate upstream (`51551940` commit message). v2 uses `minimum: 1`.
2. `session` reference "must already be known": lowercase "must" in the doc (`tool-calls.mdx:350`), **MUST** in the RFD (`rfds/subagents.mdx:636`). The RFD is Active, so it is a proposal, not a requirement.
3. The `session` gating sentence in the doc (`tool-calls.mdx:358`) has no RFC keyword. The RFD's v1 gate is **MUST NOT** (`rfds/subagents.mdx:76`) and is extended to `session` content at `:644-645`. I followed the RFD for the tier, consistent with the existing 007.
4. Minor link inconsistency: `file-system.mdx:10,50,96` link to `/protocol/v1/initialization` and `/protocol/v1/session-setup` (non-draft), while the new text links the draft tree. This predates the base and has no TCK impact.

## Open questions

1. **TCK mock-client permission policy (follow-up, not in my scope):** `run_prompt` selects the *first* offered option (`src/tck/v1/conformance/_helpers.py:300-301,411`). The new text says the agent stores `allow_always` decisions with an agent-chosen scope and lifetime (`tool-calls.mdx:238-242`). If the first option is `allow_always`, a TCK run could leave a persistent approval in the operator's real agent config. The Rust reference client selects by `kind` and prefers `allow_once`: "never by position or name" (`acp-rust-sdk: src/agent-client-protocol/examples/yolo_one_shot_client.rs:56-82` @ `e75d6f19`). I suggest the orchestrator route a harness change: prefer `allow_once`, then `allow_always` only if nothing else, by `kind`. Check v2's `_helpers.py` too.
2. Whether ACP-CLIENTCAP-007's prompt-turn citations change is for the prompt-turn report. I only touched the RFD and tool-calls parts.
