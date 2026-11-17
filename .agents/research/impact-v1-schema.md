# Impact research (v1): `schema/v1/schema.unstable.json` and `docs/protocol/v1/draft/schema.mdx`, `3961af94` -> `3ea94133`

**Sources checked:** agent-client-protocol @ base `3961af94fa62d2386d993cadf1afc8b146fc799a`, target
`3ea94133bb4e7cfdb1105df75660ff83e66acf62`. I read the files by ref (`git show <rev>:<path>`) from
`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`; that working tree is at `6ace4f6a` and I did
not touch it. Files read: `schema/v1/schema.unstable.json` (both revs, compared `$def` by `$def` with a script),
`schema/v1/meta.unstable.json` (diff), `schema/v1/schema.json` (byte-identical at both revs),
`docs/protocol/v1/draft/schema.mdx` (both revs), and at the target, to cross-check normative text,
`docs/protocol/v1/draft/{session-config-options,session-setup,prompt-turn,initialization,agent-plan,subagents}.mdx`
and `docs/rfds/get-auth-state.mdx`. TCK side: `src/tck/v1/{validation,protocol,requirements}.py`,
`src/tck/v1/conformance/{_helpers,test_plan,test_prompt,test_initialize,test_errors}.py`,
`spec-tracker/maps/v1.toml`, `tests/v1/*`, `tests/fixtures/agents/v1/*`. The vendored
`src/tck/v1/schema/schema.unstable.json` is byte-identical to the base.
**Confidence:** high. Every pointer cited in the registry, the ledger and the v1 code (99 of them) was resolved
mechanically at both revs. The `required`/`const`/hint sets were also diffed mechanically. The check for normative
text that appears only in the schema was done by hand against the target docs listed above.
I did not need the reference SDKs: no rule here depends on runtime behaviour the spec leaves implicit.

## Summary of the schema change (as it affects the TCK)

- **Removed `$def`:** `PlanFile`, and with it the `file` variant of `PlanUpdateContent` (a closed `oneOf` with
  discriminator `type`, and no fallback variant). At the target, a `plan_update` with `plan.type: "file"` is
  **schema-invalid**.
- **New `SessionUpdate` variants:** `prompt_suggestions_update` (`oneOf/16`) and `cursor_update` (`oneOf/17`). The
  subagent variants move from indices 16-18 to 18-20. The TCK cites no index in `SessionUpdate`. `SessionUpdate`
  has no fallback variant, so at the base these two kinds failed schema validation. At the target they validate.
- **New optional properties in agent-authored shapes:** `SessionCapabilities.options` (`SessionOptionsCapabilities | null`),
  `PlanMarkdown.path` (`string | null`) and `AuthAccount.description` (`string | null`). Each one widens the schema
  (the keys were already accepted, since nothing is `additionalProperties: false`). It also tightens it slightly:
  a wrong-typed value under one of these keys now fails.
- **New method `session/options`:** `SessionOptionsRequest`/`Response`, `ClientRequest` and `AgentResponse`
  variants, and `meta.unstable.json` `session_options`. The schema-driven maps in `validation.py` and `protocol.py`
  pick it up automatically.
- **New client-authored fields:** `configOptions` on `New`/`Load`/`Resume`/`ForkSessionRequest` and
  `ForkSessionRequest.cursorId`. None of them is validated by the TCK, since it validates only what the agent writes.
- **`SessionConfigOptionCategory` gains `speed`.** The `other` open string variant already accepted it, so
  validation does not change.
- **Description-only changes:** `AuthStatusResponse`, `AuthStatusUpdateNotification` (client-facing wording),
  `IdleStateUpdate` (link now points to `protocol/v1/draft/subagents#work-state`) and `UnknownStateUpdate` (adds
  "Unfinished tool calls and terminals stay as last reported. The Agent does not invent a final status"). The same
  rule is stated as a MUST NOT in `docs/protocol/v1/draft/subagents.mdx:415`.
- `schema.mdx` is the generated rendering of the same changes. Its 30 hunks all mirror the JSON changes above.
  The large `Diff`/`ElicitationAcceptAction` hunks are misaligned insertions of the new `Cursor*` sections, not
  edits to those types.

## Table: schema pointers cited by registry rows (`src/tck/v1/requirements.py`)

Only the rows the inventory flagged are listed. The other 80+ pointers resolve unchanged at the target and are
**unchanged**.

| id | classification | target citation | note |
|---|---|---|---|
| ACP-PLAN-001 | **removed** (schema side; the `agent-plan.mdx` researcher owns the replacement) | `#/$defs/PlanFile` has no target. The replacement pointer is `schema/v1/schema.unstable.json#/$defs/PlanMarkdown/properties/path`, with `docs/protocol/v1/draft/agent-plan.mdx:113-117 @ 3ea94133` (`path` **MUST** be an absolute path) | `tests/v1/test_registry.py` fails on the dangling pointer as soon as the schema is re-vendored. The rule's object changes from a URI to a native absolute path, so the check should use `is_absolute_path` (already in `_helpers.py`), not `is_absolute_uri`. See Decision 1. |
| ACP-PROMPT-002 | unchanged text, **coverage change** | `#/$defs/SessionNotification` (resolves, closure changed) | At the base, an agent sending `cursor_update`/`prompt_suggestions_update` on the default connection FAILed here as schema-invalid. At the target it PASSes. That behaviour is still non-conformant (docs MUST NOT; see the new rows below), so the incidental coverage needs replacing. |
| ACP-SCHEMA-001 | unchanged text, coverage change | `#/anyOf/0` (resolves) | Same widening as ACP-PROMPT-002 (`test_initialize.py:160-192` sweep). |
| ACP-INIT-001 | unchanged | `#/$defs/InitializeResponse` | Tightened only for a wrong-typed `agentCapabilities.sessionCapabilities.options`, which now FAILs. That is correct per the schema. |
| ACP-AUTH-007 | unchanged | `#/$defs/AuthStatusResponse` (description text changed, client-facing only) | `accounts[].description` must now be `string|null`. |
| ACP-LOAD-001, ACP-RESUME-001, ACP-ADDDIRS-001, ACP-ERROR-002 | unchanged | `#/$defs/LoadSessionRequest`, `ResumeSessionRequest`, `NewSessionRequest[/properties/additionalDirectories]` | These request defs only gained client-authored `configOptions`, which the TCK does not send. The cited sub-pointers are byte-identical. |
| ACP-SESSION-001/002, ACP-LOAD-003, ACP-CONFIG-001/002/003, ACP-AUTH-005, ACP-ARCHIVE-001, ACP-JSONRPC-006 | unchanged | (pointers resolve byte-identical) | They are reached only through the `$ref` closure (`SessionConfigOptionCategory` `speed`, which the open `other` variant already accepted; `SessionCapabilities.options`). `SessionConfigOption/oneOf/1` still means the boolean variant. |
| ACP-SUBAGENT-001/006/015 | unchanged (schema side) | `#/$defs/SubagentUpdate[...]`, `#/$defs/StateUpdate` | Their closure changed through description-only edits to `Idle`/`UnknownStateUpdate`. The stage label and the docs-precedence move to `subagents.mdx` belong to the subagents researcher. |

## Table: `docs/protocol/v1/draft/schema.mdx` citations

| id | classification | target citation | note |
|---|---|---|---|
| ACP-SUBAGENT-001 | citation-only | `docs/protocol/v1/draft/schema.mdx:9709-9713 @ 3ea94133` | Text identical (base 8690-8715 = target 9690-9715). |
| ACP-SUBAGENT-005 | citation-only | `schema.mdx:9705-9707` | Same. |
| ACP-SUBAGENT-006 | citation-only | `schema.mdx:9741,9760` | Base 8735-8765 = target 9735-9765. |
| ACP-SUBAGENT-009 | citation-only | `schema.mdx:8150,8164` | `SessionMessage` section. Base 7240-7270 = target 8141-8171 (offset +901, not +1000). |
| ACP-SUBAGENT-016 | citation-only | `schema.mdx:9694` | Same as -001. |

No ledger entry cites `schema.mdx`. All five rows also cite the RFD as `(Active RFD)`, which is now Preview. I leave
that relabelling to the subagents researcher.

## Table: ledger entries citing schema pointers (`spec-tracker/maps/v1.toml`)

| ledger citation | classification | target citation | note |
|---|---|---|---|
| `#/$defs/NewSessionRequest/properties/mcpServers; #/$defs/McpServerStdio/properties/args` ("`null` in a client-authored list field marked `x-deserialize-default-on-null`") | unchanged | both pointers byte-identical | Five more client-authored nodes now carry the hint: `configOptions` on `New`/`Load`/`Resume`/`ForkSessionRequest`, and `SessionOptionsRequest/properties/additionalDirectories`. The statement is generic, so it still holds. Adding the pointers is optional. The reason does not rest on a TCK choice. |
| `#/$defs/UnknownStateUpdate; docs/rfds/subagents.mdx:855-860 (Active RFD)` | unchanged pointer; **description changed** | pointer resolves | The added "does not invent a final status" sentence is a separate rule. It is documented in `subagents.mdx:415` and belongs to the subagents researcher. The stage label is now Preview. |
| `#/$defs/ToolCallLocation/properties/line`, `#/$defs/SessionStatusRequest`, `#/$defs/SetSessionTitleRequest` | unchanged | byte-identical | — |

## Carve-outs and schema-derived code (`src/tck/v1/validation.py`, `protocol.py`, `_helpers.py`)

v1 has no `open_enums.py`. Below is the equivalent code that hard-codes or derives values.

| item | still valid at target? | note |
|---|---|---|
| `result: null` for an all-optional object response (`_response_schema_permits_null`) | yes | No existing response `$def` gained a `required` field. The tolerated set grows from 11 to 12 with `SessionOptionsResponse`, which is all-optional. |
| `x-deserialize-default-on-null` honoured where the node carries it | yes | The docstring examples (`AuthMethodTerminal` `args`/`env`, `NewSessionRequest.mcpServers`) still carry the hint. No agent-authored node gained the hint. |
| `x-deserialize-skip-invalid-items` deliberately not honoured | yes | Two new agent-authored nodes carry it: `PromptSuggestionsUpdate/properties/suggestions` and `SessionOptionsResponse/properties/configOptions`. Following the existing policy, an invalid item there stays a violation. The docs (`prompt-turn.mdx:403`) frame the skipping as Client behaviour, which matches. |
| `$schema` dialect -> validator map | yes | Still 2020-12. |
| `_response_method_defs` / `_request_and_notification_method_defs` / `AGENT_METHODS` | yes | `session/options` is in both `meta.unstable.json` and `AgentResponse`, so the invariants in `tests/v1/test_validation.py:252-277` hold. |
| `STOP_REASONS`, `ERROR_CODES`, `AUTH_STATES` | yes | `StopReason`, `ErrorCode` and `AuthState` are unchanged. |
| `_SUBAGENT_SHAPE_KINDS`, `HISTORY_KINDS`, `_CHILD_OUTPUT_KINDS` | yes | Neither new kind is conversation content in the `HISTORY_KINDS` sense. Cursor replay rules are in `session-setup.mdx:152-156` (session-setup researcher). |
| `_GATED_METHODS` (ACP-ERROR-006) | yes | The row covers stable methods only. `session/options` is unstable, so it is correctly left out. |
| `test_plan.py` / `is_absolute_uri` / fixtures | **no** | `PlanFile`-based. `conforming_full.py:100` and `plan_turn_never_ends.py:29` emit a `type: "file"` plan, which is now schema-invalid. `emits_relative_plan_file_uri.py` and `tests/v1/test_plan_uri.py:80-84` test the removed rule. All of them need rework with the ACP-PLAN-001 replacement. |
| `x-deserialize-default-on-error` (not mentioned in the docstring) | unchanged policy | It is not honoured, so a wrong-typed `PlanMarkdown.path`, `AuthAccount.description` or `sessionCapabilities.options` FAILs where the reference receivers would fall back to the default. This predates this update. See Open questions. |

## New requirements

The docs, not the schema, are the primary source for each of these. The other doc researchers may propose the
same rows; the schema pointers here are their secondary citations. The two `CLIENTCAP` rows are listed because
the schema refresh **removes** the incidental FAIL that previously covered them.

1. **`ACP-CLIENTCAP-008`** (provisional). "The agent MUST NOT send `prompt_suggestions_update` unless the client
   advertised `clientCapabilities.session.promptSuggestions`." **MANDATORY**, no gate.
   - Citation: `docs/protocol/v1/draft/prompt-turn.mdx:364`; `docs/protocol/v1/draft/initialization.mdx:253-254`;
     `schema/v1/schema.unstable.json#/$defs/PromptSuggestionsUpdate`.
   - Test: same as ACP-CLIENTCAP-004, over a connection with `clientCapabilities: {}` (session/new, one prompt turn,
     `session/load` when advertised, quiet period). Assert no update has that kind. PASS is vacuous.
   - Harness: none new. Fixture: a non-conforming agent that emits the update unadvertised.
2. **`ACP-CLIENTCAP-009`** (provisional). "The agent MUST NOT send `cursor_update` unless the client advertised
   `clientCapabilities.session.cursors`, live or in `session/load` replay." **MANDATORY**, no gate.
   - Citation: `prompt-turn.mdx:584`; `initialization.mdx:294-295`; `session-setup.mdx:152`;
     `schema/v1/schema.unstable.json#/$defs/CursorUpdate`.
   - Test, harness and fixture: as for 1.
3. **ACP-PLAN-001 replacement** (id per Decision 1). "When the client advertised `clientCapabilities.plan`, every
   `plan_update` with `plan.type: "markdown"` and a non-null `plan.path` carries an absolute path." **MANDATORY**
   (docs MUST), with the same effective gating as today: the TCK opens its own `plan: {}` connection.
   - Citation: `agent-plan.mdx:113-117`; `schema/v1/schema.unstable.json#/$defs/PlanMarkdown/properties/path`;
     `docs/rfds/plan-operations.mdx` (Preview RFD) as secondary context only.
   - Test: reuse `_updates_with_plan_capability` and check `is_absolute_path(plan["path"])`. Omitted or `null`
     passes. The same driven connection should also validate every `plan_update`/`plan_removed` against
     `SessionUpdate`, so that a legacy `type: "file"` plan FAILs instead of being silently ignored. The subagent
     connection already does this (`_helpers.py:849-905`, judged under ACP-PROMPT-002/ACP-SCHEMA-001). See Decision 2.
   - Harness: none.
4. Optional cross-reference for the session-config-options researcher, not a new row: `ACP-CONFIG-003` (boolean
   options only when advertised) now also covers a `session/options` result. `session-config-options.mdx:535`
   says "same type and rules as on `NewSessionResponse`", and `#/$defs/SessionOptionsResponse` says the same. If
   rows for `session/options` are added, include its `configOptions` in the payloads CONFIG-003 collects.

The schema states nothing beyond these that a TCK can observe and the docs do not already state.

## New ledger entries

- **Citation:** `schema/v1/schema.unstable.json#/$defs/AuthAccount/properties/description;
  docs/rfds/get-auth-state.mdx:175 (Draft RFD)`.
  **Statement:** "An `auth/status` account's `description` MUST NOT contain credentials."
  **Reason:** "Not observable: the TCK cannot tell a credential from display text."
  This is the only agent-side normative text in the changed schema that no draft doc states. It could instead be
  merged into the existing entry "`auth/status` `accounts` MUST NOT include secrets" (`v1.toml:167-169`, which cites
  `get-auth-state.mdx:303`, now line 309) by adding the schema pointer first. See Decision 3.

## Normative schema text checked against the docs (all covered except the item above)

The following are stated in the docs too, and the docs govern: `SessionOptionsRequest` (MUST NOT create a session,
SHOULD NOT connect to MCP; `session-config-options.mdx:509,537`); initial `configOptions` (-32602, MUST ignore,
response MUST reflect, SHOULD NOT notify; `:563-568`); `ForkSessionRequest.cursorId` -32602 with no fallback
(`prompt-turn.mdx:680`); `CursorUpdate` anchor MUST and MUST NOT, and `CursorId` uniqueness (`prompt-turn.mdx`
section at 577ff); `PromptSuggestion.prompt` content rules, whitespace rule and `minItems: 1`, plus the replay
SHOULD NOT (`prompt-turn.mdx:402-404,425`, `session-setup.mdx:150`); the `PlanMarkdown.path` absolute rule (the docs
make it a MUST, the schema only says "The absolute path"); the `UnknownStateUpdate` no-invented-status rule
(`subagents.mdx:415`).

## Discrepancies (schema vs docs)

- `SessionOptionsRequest.sessionId`: the schema says Clients send it only when the Agent supports `session/load` or
  `session/resume`. `session-config-options.mdx:507` adds `session/fork` (`sessionCapabilities.fork`). This is a
  client-side rule, so it has no TCK impact. The docs govern.
- The intro at `session-config-options.mdx:475` lists only new/load/resume for initial values, while `:541` and
  `session-setup.mdx:456` (and the schema's `ForkSessionRequest.configOptions`) include fork. This is a docs-internal
  inconsistency with no impact.

## Decisions for the user

1. **ACP-PLAN-001: keep the id with changed text, or delete it and add a new id?** The old rule (file URI absolute)
   is gone, and the new one (markdown `path` absolute) is the same intent, "a plan's file reference is absolute",
   on a different field and syntax. *Recommendation:* delete the row and add `ACP-PLAN-003`. The reasons: rule B and
   the lifecycle rule ("compare rows by text") favour a fresh id when the checked object changes, and number 001
   must not be reused in this same change. This only decides the id. The agent-plan researcher may prefer to keep it.
2. **Validate `plan_update`/`plan_removed` shape on the plan connection?** At the target, a legacy `file` plan is
   schema-invalid, but no test sweeps that connection. *Recommendation:* yes, under ACP-PROMPT-002/ACP-SCHEMA-001,
   mirroring the subagent precedent. `conforming_full.py` must then drop its file plan.
3. **AuthAccount `description` ledger:** add a separate entry, or fold it into the existing "MUST NOT include
   secrets" entry. *Recommendation:* fold it in, putting the schema pointer first, because the schema governs over a
   Draft RFD and the reason is identical.
4. **ACP-CLIENTCAP-008/009 tier:** MANDATORY (docs MUST NOT on unstable features, the same as CLIENTCAP-004..007).
   *Recommendation:* MANDATORY, for consistency with the existing rows.

## Open questions

- Not caused by this update, but this update makes it visible: `x-deserialize-default-on-error` is not honoured and
  the `validation.py` docstring does not say so. Should the docstring record it as a deliberate non-carve-out,
  alongside `x-deserialize-skip-invalid-items`? This needs a `validation.py` owner, not research.
- Pre-existing gap: the shapes of capability-gated updates (`plan_update`, `notice`, `compaction_*`) are never
  schema-validated, because the connections that advertise those capabilities are not swept. This is wider than
  Decision 2.
