# Impact: v2 schema (`schema/v2/schema.unstable.json`, `docs/protocol/v2/draft/schema.mdx`), 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol, read by ref at `3961af94` (base) and `3ea94133` (target) from
`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2` (`git show`/`git diff` only). Note: that checkout's
HEAD is now `6ace4f6a` (#2858, one commit past the target, see Decision 4). Files: `schema/v2/schema.unstable.json`,
`schema/v2/meta.unstable.json`, `docs/protocol/v2/draft/schema.mdx`, plus target `session-config-options.mdx`,
`prompt-lifecycle.mdx`, `session-setup.mdx`, `slash-commands.mdx`, `initialization.mdx`, `authentication.mdx` and
`docs/rfds/get-auth-state.mdx` for doc coverage. TCK: `src/tck/v2/{requirements,validation,protocol}.py`,
`spec-tracker/maps/v2.toml`, `tests/v2/test_validation.py`, `src/tck/v2/conformance/test_slash_commands.py`,
`spec-tracker/src/*/impact.py`. The vendored file is byte-identical to the base (`cmp`).
**Confidence:** high. Every cited pointer was resolved by script at both revisions, every `$def` was diffed (structure
and description separately), and the `validation.py` carve-outs were re-checked by script against the target schema.

## Summary

- **Pointers:** 158 distinct `schema.unstable.json#...` pointers in `requirements.py` and `v2.toml`. **0 broken** at the
  target. 17 resolve to content that changed. All positional pointers (`IdleStateUpdate/anyOf/4,6`,
  `RequestPermissionOutcome/anyOf/2`, `ReplayFrom/anyOf/1`, `SystemPromptMode/anyOf/0`,
  `ClientNotification/.../anyOf/0/anyOf/0`) still point at the same branch. The last one is still titled
  `CancelSessionNotification`.
- **`validation.py` carve-outs (docstring points 1-5): all still hold.** No refresh-induced invalidation (details below).
- **Validation of agent output changes in 7 places.** None adds a required field to an existing shape. The changes come
  from new named union branches (which now validate strictly instead of falling into `other`), from new typed optional
  fields, and from the removed `PlanFile` branch.
- **New normative schema text:** 36 new sentences with RFC keywords. All but one are also stated in a target draft doc,
  so the doc researchers own them. The exception is `AuthAccount.description` "MUST NOT contain credentials", which is
  schema-only (plus the Draft RFD).
- **New method:** only `session/options` (`meta.unstable.json` adds `session_options`). It is documented at
  `session-config-options.mdx:479-585` and `initialization.mdx:348-354` @ 3ea94133, so no method lacks doc coverage.
- **Counts:** 27 unchanged (23 pointer rows, 4 `schema.mdx` rows), 5 citation-only (`schema.mdx` rows), 1 changed
  text (ACP-COMMANDS-201), 0 removed, 0 new rows owned here, 1 amended ledger entry (none new). There are also 3 prose
  line-number fixes that `--fix` will not make.

## Table 1: rows and ledger entries citing changed schema pointers

| id / ledger | classification | target citation | note |
|---|---|---|---|
| ACP-INIT-204 | unchanged | `#/$defs/SessionCapabilities` | Gains `options` (`SessionOptionsCapabilities\|null`). `PromptCapabilities` gains `skill` -> `inline`. `find_non_object_markers` walks the schema, so it judges these new markers automatically. No code or fixture change. |
| ACP-PROMPT-002 | unchanged | `#/$defs/SessionUpdate`, `#/$defs/SubagentUpdate` | New named variants `replay_complete`, `prompt_suggestions_update`, `cursor_update`. `SubagentUpdate` lost its UNSTABLE banner and gained a docs link. Validation picks the variants up by itself. |
| ACP-SUBAGENT-001, ACP-SUBAGENT-201 | unchanged (schema side) | `#/$defs/SubagentUpdate` | Description change only (banner removed, link to `/protocol/v2/draft/subagents`). The docs-precedence switch and the RFD label belong to the subagents-doc researcher. |
| ACP-STATE-201 | unchanged | `#/$defs/StateUpdate` | Banner removed from the `unknown` branch only. |
| ACP-STATE-207, ACP-RESUME-213, ACP-ENUM-201 | unchanged (schema side) | `#/$defs/BackgroundWork` | Banner removed only. ENUM-201's behaviour moves through `protocol.py` sets, which `impact-v2-extensibility.md` covers. |
| ACP-PROMPT-211 | unchanged | `#/$defs/ContentBlock` | Gains a named `skill` branch (`SkillReference`, `name` required). The `_tck_unknown` probe is still unknown. |
| ACP-PROMPTCAP-001/002/003 | unchanged | `#/$defs/PromptCapabilities` | Gains `skill`. The rows judge `image`, `audio` and `embeddedContext` only. |
| ACP-PROMPTCAP-201 | unchanged | `#/$defs/PromptCapabilities`, `#/$defs/ContentBlock` | The analogous `skill` negative probe is a new rule stated by the docs (cross-ref X3). Whether to extend this row or add a new one is for the plan-commands-config researcher. |
| ACP-CANCEL-205 | unchanged | `#/$defs/ClientNotification/properties/params/anyOf/0/anyOf/0` | Same branch. Its description changed SHOULD -> MUST for `$/cancel_request` of pending permission requests. That rule is not this row's: ACP-CANCEL-209/213 belong to the cancellation researcher. |
| ACP-JSONRPC-001, ACP-JSONRPC-002, ACP-ERROR-204 | unchanged | `#/$defs/AgentResponse` | Gains a `SessionOptionsResponse` result branch. The envelope layout is the same. |
| ACP-JSONRPC-202 | unchanged | `#/$defs/AgentRequest` | Description of `session/request_permission` changed SHOULD -> MUST (same rule as the CANCEL-205 note). |
| ACP-RESUME-001 | unchanged | `#/$defs/ResumeSessionRequest` | New optional `configOptions` (client-sent). |
| ACP-CONFIG-201 | unchanged | `#/$defs/SessionConfigOptionCategory` | Adds the `speed` const. `category` stays open, so `validate_def_value("SessionConfigOption")` behaves the same. |
| **ACP-COMMANDS-201** | **changed text** | `#/$defs/AvailableCommand` | The row says "`type` discriminator (`command`, or a `_`-prefixed custom type)". At the target, `skill` is also defined (`AvailableCommand/anyOf/1` -> `Skill`: `name` and `description` required, `path` is `AbsolutePath\|null`). The `other` branch now excludes `skill`, so a malformed `skill` entry FAILs validation instead of falling back. Uniqueness is now "across commands and skills" (`Skill.name`; `slash-commands.mdx:187-188`). The test already checks it list-wide, so no code change is needed. The row's and test docstring's "without the leading `/`" still holds per `slash-commands.mdx:101`, although the schema's `name` description dropped that phrase (Discrepancy D1). Doc citations belong to the plan-commands-config researcher. |
| ACP-AUTH-007 | unchanged | `#/$defs/AuthStatusResponse` | `state` description reworded; it binds clients only. Related: `AuthAccount` gains a `description` property (`string\|null`), so an `accounts[]` entry with a non-string `description` now FAILs this row's `AuthStatusResponse` validation. That is correct at the target. |
| ACP-PATCH-205 | unchanged | `#/$defs/PlanUpdateContent` | The `file` branch is removed. The `other` branch still requires `planId` (it moved from `anyOf/3` to `anyOf/2`; no citation uses the index). A `type: "file"` plan is now schema-valid through `other` but FAILs ENUM-201 once `PLAN_CONTENT_TYPE` drops `file` (`impact-v2-extensibility.md`). The plan doc rules belong to `impact-rfd-plan-operations.md` and the plan researcher. |
| ledger `v2.toml:692` (`#/$defs/UnknownStateUpdate`; subagents RFD) | unchanged (schema side) | `#/$defs/UnknownStateUpdate` | Banner removed. A new sentence says unfinished tool calls and terminals "stay as last reported" and that the Agent "does not invent a final status" (no RFC keyword). The RFD re-cite belongs to the rfd-subagents researcher. |
| ledger `v2.toml:354` (`#/$defs/AuthStatusUpdateNotification`) | unchanged (schema side) | same | Same client-only rewording as `AuthStatusResponse`. |
| ledger `v2.toml:740` (`#/$defs/ProxyRequest`) | unchanged | same | It is in the `$ref` closure only through `ClientCapabilities`. Its own definition is unchanged. |

## Table 2: rows and ledger entries citing `docs/protocol/v2/draft/schema.mdx`

`schema.mdx` is generated from the unstable schema. The lines added to it mirror exactly the new description text listed
under "Normative text" below, and contain nothing beyond it.

| id / ledger | classification | target citation @ 3ea94133 | note |
|---|---|---|---|
| ACP-SUBAGENT-005 | citation-only | `schema.mdx:11552-11556` (was 10189-10193) | Same text. |
| ACP-SUBAGENT-006 | citation-only | `schema.mdx:11603,11619` (was 10238,10254) | Same text. |
| ACP-SUBAGENT-009 | citation-only | `schema.mdx:9413,9427` (was 8237,8251) | Same text. |
| ACP-SUBAGENT-016 | citation-only | `schema.mdx:11545` (was 10178) | Same text. |
| ACP-AUTH-005 | citation-only | `schema.mdx:990` (was 954) | Same text. |
| ACP-CANCEL-001 / -002 / -204 | unchanged | `schema.mdx:603-607`, `615-617`, `595-597` | The SHOULD -> MUST hunk is at line 600, between the cited ranges. |
| ACP-AUTH-007 | unchanged | `schema.mdx:143-144` | |
| ledger `v2.toml:329` | unchanged | `schema.mdx:144` | |
| **prose (not auto-fixed)** | citation-only, manual | `schema.mdx:990` | `spec-impact --fix` rewrites only `citation =` lines and `citation=` keywords (`spec-tracker/src/*/impact.py:659-704`). Fix these by hand: the `spec-tracker/maps/v2.toml:326` `reason` ("`schema.mdx:954`") and the `src/tck/v2/conformance/test_authentication.py:216` docstring. |

## `validation.py` carve-outs against the target schema

| point | check at target | result |
|---|---|---|
| 1 No batching | root keys outside `$defs` are identical at base and target | holds |
| 2 No nullable `*Response` | every method `*Response` is `type: object`, including the new `SessionOptionsResponse`. The non-object `*Response` names are the same 7 envelopes at both revisions. | holds |
| 3 Open-fallback discriminator | all 38 base unions with an `other` branch keep their discriminator (`_discriminator_property` result unchanged). New unions: `CursorAnchor` (`type`), `InitialSessionConfigOption` (`type`), `CursorAnchorPosition` (plain enum, `None`). None loses its single-const discriminator. | holds |
| 4 `RequestId` never null | `RequestId` unchanged | holds |
| 5 `x-deserialize-default-on-null` | 12 -> 16 nodes, all new ones on client-sent fields (`New/Fork/ResumeSessionRequest.configOptions`, `SessionOptionsRequest.additionalDirectories`). `x-deserialize-skip-invalid-items` 28 -> 31 (`SessionOptionsResponse.configOptions`/`availableCommands`, `PromptSuggestionsUpdate.suggestions`). That hint stays not honored, which matches the docstring. | holds, self-updating |

`_request_and_notification_method_defs` and `_response_method_defs` select by content and `x-method`. They pick up
`session/options` (`SessionOptionsResponse`, `x-method: session/options`) automatically. No method `$def` lost its
`x-method`. The `tests/v2/test_validation.py` fixtures (`AuthMethod`, `AuthMethodTerminal`, `AgentCapabilities`,
`InitializeResponse`) are all on unchanged defs. Only `test_enum_sets_match_the_schema` will go red, and that is the
`protocol.py` sets already covered by `impact-v2-extensibility.md`.

## Shape changes that change validation of agent output

| site | base behaviour | target behaviour | rows that see it |
|---|---|---|---|
| `AvailableCommand` `type: "skill"` | fell into `other` (required `name`, `description`) | `Skill`: `name` and `description` required, `path` `AbsolutePath\|null`. A relative `path` FAILs. `other` excludes `skill`. | COMMANDS-201, SCHEMA-level whole-message rows |
| `ContentBlock` `type: "skill"` | `other` | `SkillReference`, `name` required | any row validating `user_message`/chunk content (e.g. in replay) |
| `SessionUpdate` `replay_complete` / `prompt_suggestions_update` / `cursor_update` | `other` (schema-valid, ENUM-flagged) | named. `prompt_suggestions_update` needs `suggestions[]` with each `prompt` `minItems: 1`. `cursor_update` needs `cursorId`. `CursorUpdate.anchor`, if present, must match `CursorAnchor`. | PROMPT-002 and every passive `session/update` validator |
| `PlanUpdateContent` `type: "file"` | `PlanFile` | `other` (schema-valid, still needs `planId`) | PATCH-205, ENUM-201 |
| `PlanMarkdown.path` | unknown key, ignored | `AbsolutePath\|null`. A relative or non-string path FAILs. | any `plan_update` validation |
| `AuthAccount.description` | unknown key, ignored | `string\|null` | AUTH-007 |
| `AgentCapabilities.session.options`, `session.prompt.skill(.inline)` | unknown keys, ignored | object-or-null markers | INIT-204, SCHEMA-001 |

No existing `required` list gained a member. The only `required` differences are the union branches renumbered by the
insertions.

## Normative text in schema descriptions: doc coverage

The new agent-binding sentences (client-only ones are omitted), with where the target docs state them. "Owner" is the
researcher whose doc governs.

| # | schema text (`#/$defs/...`) | doc @ 3ea94133 | owner |
|---|---|---|---|
| X1 | `SessionOptionsRequest`: MUST NOT create or resume a session, send `session/update`, add a `session/list` entry or change a session. SHOULD NOT connect to MCP servers. Unknown `sessionId` gets `-32002`. | `session-config-options.mdx:514,516,551` | plan-commands-config (config) |
| X2 | `New/Fork/ResumeSessionRequest.configOptions`: malformed entries or duplicate `configId` fail with `-32602`. MUST ignore unknown `configId`, a mismatched `type` or a disallowed value. SHOULD NOT send `config_option_update` for them. | `session-config-options.mdx:572-585` (the doc also adds "unsupported value `type` MUST fail `-32602`", line 579) | same |
| X3 | `SkillReference.name`: MUST reject the prompt with `-32602` if the name is unresolvable. MUST treat each block as an explicit invocation. | `slash-commands.mdx:254-255` (also the capability-position rule) | plan-commands-config / content |
| X4 | `Skill` / `AvailableCommand` / `CommandsCapabilities`: send `skill` entries only if the Client advertised `session.commands.skill`. A sender MUST advertise `session.prompt.skill`. Names unique across commands and skills. | `slash-commands.mdx:171,173,187-188,210` | plan-commands-config |
| X5 | `PromptRequest.idempotencyKey`: Agents advertising `capabilities.session` MUST support it. Any value outside 1-255 chars gets `-32602` and MUST NOT be treated as omitted. | `prompt-lifecycle.mdx:439,441` | prompt-lifecycle |
| X6 | `SessionUpdate`/`PromptSuggestionsUpdate`/`PromptSuggestion`: send only if the Client advertised `session.promptSuggestions`. Content-type limits. No empty or whitespace-only prompt. SHOULD NOT replay. | `prompt-lifecycle.mdx:707,745-748`; `session-setup.mdx:236` | prompt-lifecycle / session-setup |
| X7 | `CursorUpdate`: the first update MUST include `anchor`. The Agent MUST NOT change it afterwards. `ForkSessionRequest.cursorId`: any other ID gets `-32602`, with no fallback. | `prompt-lifecycle.mdx:949,999` | prompt-lifecycle |
| X8 | `ReplayComplete`: sent once per `replayFrom` resume, after the last replayed update and before the response. Not sent without `replayFrom`. | `session-setup.mdx:360ff` | session-setup |
| X9 | `CancelSessionNotification` / `RequestPermissionRequest`: MUST (was SHOULD) cancel pending permission requests with `$/cancel_request` | `cancellation.mdx` hunk (inventory) | cancellation-elicitation |
| **X10** | **`AuthAccount.description`: "MUST NOT contain credentials."** | **not in `authentication.mdx`**. Also stated in `docs/rfds/get-auth-state.mdx:175` (interface comment) and `:309` ("Agents MUST NOT include secrets"), both Draft RFD. | **this report** (ledger, below) |

The X1, X5 and X6 gates are observable with the current mock client: it advertises no `capabilities.session.*`, the
same pattern as ACP-CLIENTCAP-003. I list them only so the orchestrator can confirm each owner has a proposal.

## New requirements

None owned by this report. Every new agent rule the schema states is also in a draft doc (X1-X9), so the doc governs.

## New ledger entries

No new entry. One existing entry should be amended:

- **Amend** the `v2.toml` entry "`auth/status` `accounts` MUST NOT include secrets." (base citation
  `docs/rfds/get-auth-state.mdx:303 (Draft RFD)`). New citation:
  `schema/v2/schema.unstable.json#/$defs/AuthAccount/properties/description; docs/rfds/get-auth-state.mdx:175,309 (Draft RFD)`.
  - Statement: "`auth/status` `accounts` entries MUST NOT include secrets; in particular `description` MUST NOT
    contain credentials."
  - Reason: unchanged ("Not observable: the TCK cannot tell a secret from a display label"). It is a real limitation,
    not a TCK choice.
  - The schema is now the primary source and the RFD is secondary. The rule stays a ledger entry because it is
    unobservable. The v2 authentication researcher may already be re-citing this entry; if so, merge.

## Decisions for the user

1. **ACP-COMMANDS-201 text (changed text, tier unchanged).** Recommendation: change "`command`, or a `_`-prefixed
   custom type" to "`command`, `skill` (unstable), or a `_`-prefixed custom type", and say the uniqueness spans
   commands and skills. Keep the leading-`/` note, since the doc still says it.
2. **AuthAccount credentials rule.** Recommendation: amend the existing ledger entry as above. Do not add a row.
3. **Positional-pointer policy (no action needed).** The new union branches shifted the `other` indices
   (`SessionUpdate` 23 -> 26, `ContentBlock` 5 -> 6, `AvailableCommand` 1 -> 2, `PlanUpdateContent` 3 -> 2). No TCK
   citation or code uses those indices, and the code selects `other` by title. Recommendation: none; the current
   practice is already safe.
4. **Re-vendor source (blocker for the re-vendor slice).** The spec checkout has moved one commit past the target
   (`6ace4f6a`, #2858). That commit adds `minItems: 1` and "Agents MUST include at least one entry" to `Diff.changes`
   in `schema.unstable.json` and `schema.mdx`. The `cp` commands in `VENDORED.md` would vendor `6ace4f6a`, not
   `3ea94133`. Recommendation: vendor with `git show 3ea94133:schema/v2/{schema,meta}.unstable.json`, or decide to
   move the target to `6ace4f6a`. Moving it would add one schema change, which affects any row validating `diff`
   content.

## Discrepancies

- **D1.** The `AvailableCommand.name` description dropped "without the leading `/`". `slash-commands.mdx:101` keeps it.
  Neither uses an RFC keyword, so there is no tier effect. Follow the docs.
- **D2.** The `New/Fork/ResumeSessionRequest.configOptions` descriptions list malformed entries and duplicates as
  `-32602`. The doc (`session-config-options.mdx:579`) adds "an entry with a value `type` the Agent does not support
  MUST fail with `-32602`", which the schema states only on the `InitialSessionConfigOption` `other` branch, and only
  for `session/set_config_option`. Follow the docs.

## Open questions

- `validation.py` honors `x-deserialize-default-on-null` but not `x-deserialize-default-on-error`. The new fields
  (`AuthAccount.description`, `PlanMarkdown.path`, `Skill.path`, the capability markers) carry default-on-error, so a
  wrong-typed value FAILs validation while reference receivers would default it. This is consistent with the existing
  stance that the agent authored the value, but the docstring does not say so. It is not refresh-induced; the
  orchestrator may want the docstring to state it.
