# Can the v2 suite switch wholesale from `schema.json` to `schema.unstable.json` without rewriting its checking logic?

**Sources checked:**
- agent-client-protocol (spec) @ `9af0e9f748db9f4cc4c410a7b212ead4f98ae78c` (2026-09-29, HEAD after `pull --ff-only`), compared against the vendored pin `d8805733cca4ef0d92e5135b50d5bfc2ea4fbdf3` (2026-09-24)
- acp-rust-sdk @ `b55cdc72e06f00b469f8739e57c44539d5dfcbf9` (2026-09-28), only to check which features the cross-check `testy` build turns on
- acp-tck working tree on `eugenethedev/v2-draft` @ `b15c7bd`
- Experiments ran in a scratch copy of the repo, never in the real tree (details under Testability notes)

**Confidence:** high. The structural diff was computed by script, and `uv run pytest tests/v2` was actually run against both candidate schema swaps.

## Answer

**The hypothesis holds.** At the vendored pin and at spec HEAD, `schema.unstable.json` is a strict structural superset of `schema.json`:
- The top-level `anyOf` has the same 7 branches in the same order.
- No `$def` is removed.
- No existing `required` list changes.
- Every change is an added optional property, an added union branch, or an added method.

`protocol.py` and `validation.py` parse the schema structurally, and nothing in them depends on stable-only shapes. Swapping in the unstable files mostly just works:
- **At HEAD** (`schema.unstable.json` + `meta.unstable.json`) with four new `SESSION_UPDATE_KIND` constants added, **all 114 `tests/v2` tests pass**.
- **At the vendored pin** (d880 unstable + d880 `meta.unstable.json`) with no code change, exactly 1 test fails: `test_enum_sets_match_the_schema`, because of the missing constants.

The real work is:
- one hand-copied constant set (`SESSION_UPDATE_KIND`);
- deleting the dual-schema carve-out in `find_unknown_root_keys`;
- `meta.json` → `meta.unstable.json`. This is required: otherwise `ACP-CLIENTCAP-202` and schema validation disagree on `mcp/message`;
- docs, docstrings and citations.

**Recommendation: refresh to spec HEAD in the same change.** The vendored d880 unstable schema has a `mcp/message` request/notification collision that `_request_and_notification_method_defs` would mis-dispatch. HEAD's MCP-over-ACP rework (`ef4613d`) removes that collision.

## Requirements

This row is about the spec's own statement of what the unstable schema *is*. It is not a new TCK requirement.

| # | Statement | Tier | Citation |
|---|-----------|------|----------|
| 1 | `v2/schema.unstable.json` is "v2 + unstable feature flags". `v2/schema.json` is "v2 without unstable feature flags". Likewise for `meta.unstable.json` / `meta.json` | n/a (provenance) | spec `schema-generator/src/main.rs:165-178,209-213` |
| 2 | Draft-only `SessionUpdate` variants (`plan_removed`, `notice`, `compaction_update`, `compaction_summary_chunk`) "are unstable and may change or be removed" | n/a (stability disclaimer) | spec `docs/protocol/v2/draft/prompt-lifecycle.mdx:30,35-37,39` |
| 3 | The unstable schema pairs with the `docs/protocol/v2/draft/*.mdx` docs, not `docs/protocol/v2/*.mdx`. Generated descriptions link to `/protocol/v2/draft/...` | n/a | spec `schema-generator/src/main.rs:229-241,276-277` |

Tier impact on existing TCK rows is covered under Details §3. No row changes tier.

## Details

### 1. Every reference to the schema files, `SCHEMA_REVISION`, or the stable/unstable split

**Code (functional):**
- `src/tck/v2/protocol.py:24-28`: `SCHEMA_REVISION` and its docstring ("`schema/{schema,schema.unstable,meta}.json`").
- `src/tck/v2/protocol.py:113-119`: `load_meta()` reads `meta.json`.
- `src/tck/v2/protocol.py:122-125`: `load_schema()` reads `schema.json`.
- `src/tck/v2/protocol.py:128-136`: `load_unstable_schema()`. Its docstring says ACP-SCHEMA-001 stays on stable.
- `src/tck/v2/protocol.py:30,40,60-66`: comments citing `schema/v2/schema.json`.
- `src/tck/v2/protocol.py:73-92`: `SESSION_UPDATE_KIND`, hand-copied. **Must gain 4 values.**
- `src/tck/v2/validation.py:1-2`: module docstring names `schema.json`.
- `src/tck/v2/validation.py:28-36`: docstring point 4, the unstable root-key carve-out.
- `src/tck/v2/validation.py:48`: imports `load_unstable_schema`.
- `src/tck/v2/validation.py:74`: error text "vendored schema.json declares...".
- `src/tck/v2/validation.py:381-401`: `_allowed_root_properties` unions stable + unstable. Collapse it to a single schema.
- `src/tck/v2/__init__.py:13,35-36`: `SCHEMA_DIR`/`SCHEMA_REVISION` into `VersionSpec`. `schema_dir` is stored but never read by `tck.common` (`src/tck/common/version.py:27`, no other consumers).
- `src/tck/v2/requirements.py:32-35`: `SPEC_REVISION = SCHEMA_REVISION`. Every citation is pinned via `_cite`.
- `tests/v2/test_registry.py:18,225-226`: asserts `SCHEMA_REVISION` is in every citation. This self-updates.

**Requirement citations and text:**
- `src/tck/v2/requirements.py` has 56 occurrences of `schema/v2/schema.json` (e.g. `:51,105,124,138,149,...,1368,1379`), most with line numbers.
- `:361` cites `schema/v2/meta.json:16-21` for ACP-CLIENTCAP-202.
- `:133-138` is the ACP-SCHEMA-001 text ("validates against the vendored v2 schema") plus its citation `schema/v2/schema.json (top-level anyOf)`.

**Conformance docstrings citing `schema/v2/schema.json`:**
- `src/tck/v2/conformance/_helpers.py:57,203,338`
- `test_extensibility.py:97,182`
- `test_patches.py:76,122,150`
- `test_diagnostics.py:18`
- `test_authentication.py:113`
- `test_enums.py:12`

**Tests:**
- `tests/v2/test_validation.py:154,163,180` (`_consts_from_schema` reads `protocol.load_schema()`, so it follows the switch automatically).
- `tests/v2/test_cli.py:1966,1988,2008` (docstrings).
- `tests/v2/test_cli.py:2118-2147`: the two carve-out tests.

**Fixtures (docstrings only):**
- `tests/fixtures/agents/v2/_base.py:9,133`
- `unstable_capability_key.py:1-7`
- `unknown_capability_root_key.py:1-9`
- `unprefixed_custom_session_update.py:5-9`
- `tool_call_update_missing_id.py:6`
- `plan_missing_plan_id.py:5`
- `message_chunk_missing_message_id.py:5`
- `terminal_env_duplicate_names.py:4`

**Docs:**
- `src/tck/v2/schema/VENDORED.md` (whole file; `:11-18` describes the split; `:33-35` says `meta.unstable.json` is deliberately not vendored).
- `AGENTS.md:188-196` ("Vendored schema"; `CLAUDE.md` is a symlink to `AGENTS.md`).
- `README.md:8` calls v2 "(Draft)" but does not mention schema files.
- `src/tck/common/plugin.py:325,368` are comments about `schema.json`/`meta.json`. They concern v1/v2 initialize handling, need no change, and are optional wording touch-ups.

**Scripts:** `scripts/cross-check.sh` mentions only the Rust feature `unstable_protocol_v2`, which is unrelated to the schema file. `scripts/cross-check/python_v2_agent.py` and `scripts/cross-check-summary.py` have no schema references.

### 2. Structural diff

Method: every `description` was stripped, then the remaining schema content was deep-diffed. `_meta`/description changes on about 116 defs are only doc URLs (`/protocol/v2/` → `/protocol/v2/draft/`). They have no semantic effect.

**Vendored `schema.json` (d880) vs vendored `schema.unstable.json` (d880):**

- **`$schema`:** both use draft 2020-12, so `_validator_class()` (`validation.py:69-77`) is unaffected.
- **Top-level `anyOf`:** the same 7 titled branches in the same order (Agent, Client, AgentBatchCall, AgentBatchResponse, ClientBatchCall, ClientBatchResponse, ProtocolLevel). Only the inlined `result` lists inside `AgentBatchResponse`/`ClientBatchResponse` grow. Neither `protocol.py` nor `validation.py` reads the top-level `anyOf`; both read `$defs` envelopes.
- **`$defs`:** 0 removed, 89 added (NES, providers, fork, MCP-over-ACP, notices, compaction, plan file/markdown/removal, position encoding, `Usage`, ...). 14 common defs change semantically, and every change is additive:
  - **Capability objects:**
    - `AgentCapabilities` gains `nes`, `positionEncoding`, `providers`.
    - `ClientCapabilities` gains `nes`, `positionEncodings`.
    - `SessionCapabilities` gains `fork`.
    - `McpCapabilities` gains `acp`.
    - All are optional and nullable. `ProvidersCapabilities`, `SessionForkCapabilities` and `McpAcpCapabilities` are `{_meta}`-only objects with no `required`.
  - **`IdleStateUpdate`** gains optional `usage` → `Usage` (required: `totalTokens`, `inputTokens`, `outputTokens`).
  - **`SessionUpdate`** gains 4 named branches: `plan_removed`, `notice`, `compaction_update`, `compaction_summary_chunk`. The `other` fallback's `not` list grows to match.
  - **`PlanUpdateContent`** gains `file` and `markdown` branches. Both require `planId`, consistent with ACP-PATCH-205.
  - **`McpServer`** gains an `acp` branch, and its `other` fallback `not` list grows.
  - **Envelopes:**
    - `AgentRequest` + `mcp/connect`, `mcp/message`, `mcp/disconnect`.
    - `AgentNotification` + `mcp/message`.
    - `AgentResponse.result` + 8 responses.
    - `ClientRequest` + 8 requests.
    - `ClientNotification` + 8 notifications (`document/*`, `nes/accept|reject`, `mcp/message`).
    - `ClientResponse` + 3.
  - **Unchanged:** no `required` list changes and no `x-side`/`x-method` changes on any existing def. `StopReason`, `ToolKind`, `ToolCallStatus`, `PlanEntryPriority`, `PlanEntryStatus`, `StateUpdate`, `ToolCallContent`, `AuthMethod`, `ContentBlock` and `Error` are semantically identical.
- **Open-enum "other" fallback shape:** the same pattern (`title: "other"`, `not: {anyOf: [...consts]}`, `additionalProperties: true`). `_matches_open_fallback_branch` / `_discriminator_property` (`validation.py:404-447`) keep working. They exclude the new consts automatically.
- **Methods added in `meta.unstable.json` @ HEAD (`schema/v2/meta.unstable.json`):**
  - agentMethods + `providers/list|set|disable`, `session/fork`, `mcp/message`, `nes/start|suggest|accept|reject|close`, `document/didOpen|didChange|didClose|didSave|didFocus`.
  - clientMethods + `mcp/message` (`:34`).
  - protocolMethods: unchanged.

**Spec HEAD vs vendored pin:**
- `schema.json` and `meta.json`: byte-identical at HEAD. `cmp` confirms it.
- `schema.unstable.json` and `meta.unstable.json`: changed, by exactly one commit, `ef4613d feat(unstable): make MCP-over-ACP request-scoped` (2026-09-25).
  - **Removed** `mcp/connect`, `mcp/disconnect` and their `Connect*`/`Disconnect*` defs plus `McpConnectionId`. **Added** `McpError`, `McpRequestId`.
  - `MessageMcpRequest`/`MessageMcpNotification` replace `connectionId` with `serverId` + `requestId` in `required`.
  - The `x-side` values change: `MessageMcpRequest`/`MessageMcpResponse` go from `both` to `client`, and `MessageMcpNotification` from `both` to `agent`.
  - The **result**: at HEAD, `mcp/message` is agent→client *request only*, and client→agent *notification only*.
  - The meta diff removes `mcp_connect`/`mcp_disconnect` from `clientMethods`.

**The dispatch-table hazard at d880:** `_request_and_notification_method_defs` (`validation.py:119-139`) builds a `{method: def}` dict, iterating `AgentRequest` and then `AgentNotification`. In d880 unstable, `mcp/message` sits in both envelopes (verified by script), so the notification def silently overwrites the request def. An agent's `mcp/message` *request* would be validated against `MessageMcpNotification`. This happens to be harmless at d880 because the two shapes are near-identical, but it is structurally wrong. At HEAD there is no collision. With HEAD files, the derived tables are:
- `mcp/message` → `MessageMcpRequest`;
- `CLIENT_METHODS` = {`elicitation/complete`, `elicitation/create`, `mcp/message`, `session/request_permission`, `session/update`};
- `CLIENT_NOTIFICATIONS` = {`elicitation/complete`, `session/update`}.

These were verified by importing the swapped copy. `AGENT_NOTIFICATIONS`, `CLIENT_NOTIFICATIONS`, `AGENT_METHODS` and `KNOWN_METHODS` have no consumers outside `protocol.py` (grep), so their growth is inert.

### 3. Impact on requirements and dispatch

- **ACP-SCHEMA-001** (`requirements.py:129-139`, MANDATORY):
  - The text says "the vendored v2 schema", so it stays true. The citation `schema/v2/schema.json (top-level anyOf)` should become `schema/v2/schema.unstable.json (top-level anyOf)`, and `VENDORED.md:16-18` / `validation.py:34-36` must drop the "stays scoped to schema.json" claim.
  - Behavioral delta: the validation is now **stricter only for agents that emit unstable-named fields with wrong shapes**. Before, an unknown extra property was ignored because no schema uses `additionalProperties: false`. Now it is type-checked. Examples: `capabilities.providers: true`, `usage` on idle without `totalTokens`, `sessionUpdate: "notice"` without `severity`/`title`.
  - It is **looser for nothing**. Correctly shaped unstable content passed before via extra-props/`other`, and still passes.
- **ACP-SCHEMA-002 / ACP-EXT-202** (`requirements.py:1394-1405`, `:1349-1357`, ADVISORY): the behavior is identical. The allowed-key union across the two schemas equals the unstable schema's keys alone, because it is a superset. The carve-out code (`validation.py:381-401`) and docstring point 4 simply collapse. The requirement texts do not mention `schema.json`, so they need no change.
- **ACP-ENUM-202** (`test_enums.py:156-159`, ADVISORY): with the switch, `notice` / `plan_removed` / `compaction_update` / `compaction_summary_chunk` become *defined* values, so an agent emitting them no longer FAILs. This requires adding them to `SESSION_UPDATE_KIND`. `test_enum_sets_match_the_schema` (`tests/v2/test_validation.py:176-194`) enforces the addition automatically, since it reads `load_schema()`. No other enum set changes.
- **ACP-CLIENTCAP-202** (`requirements.py:350-364`, CAPABILITY): uses `CLIENT_METHODS` from meta.
  - If `meta.unstable.json` is **not** vendored, then `validate_agent_message` (unstable schema) treats an agent's `mcp/message` as known, while CLIENTCAP-202 (stable meta) FAILs it. That is an internal inconsistency, **so meta must switch too**.
  - After switching, `mcp/message` is allowed unconditionally. The spec presumably gates it on the client advertising `mcp.acp` plus an `acp`-type server. See Open questions.
  - The citation `schema/v2/meta.json:16-21` should become `schema/v2/meta.unstable.json:31-37` @ HEAD.
- **Mock client** (`conformance/_helpers.py:768-773,899-928`): it answers `session/request_permission` and returns `-32601` for any other agent→client request while recording it. It advertises `capabilities: {}` and sends no `acp`-type MCP server, so a conforming agent has no reason to send `mcp/message`. **No change is needed.** Unstable client→agent methods (`nes/*`, `document/*`, `providers/*`, `session/fork`) are never sent by the TCK, so nothing new is exercised.
- **Other citations:** about 70 citation/docstring references cite `schema/v2/schema.json:<line>`. Upstream `schema.json` is byte-identical at HEAD, so these stay **accurate as citations of upstream** after a `SCHEMA_REVISION` bump. They would all be **wrong** if rewritten to point at `schema.unstable.json`, because line numbers shift a lot:

  | Def | `schema.json` line | `schema.unstable.json` @ HEAD line |
  |-----|--------------------|------------------------------------|
  | `StopReason` | 4869 | 6298 |
  | `Error` | 4127 | 5452 |
  | `AgentCapabilities` | 3123 | 3315 |
  | `CancelRequestNotification` | 7001 | 10123 |

  The user needs to decide this (see Open questions).

### 4. `tests/v2` and fixtures

**Experiment A** (vendored d880 `schema.unstable.json` copied over `schema.json`, d880 `meta.unstable.json` over `meta.json`, no code change): `1 failed, 113 passed`. The only failure was `test_enum_sets_match_the_schema` (the 4 extra SessionUpdate consts).

**Experiment B** (HEAD `schema.unstable.json` → `schema.json`, HEAD `meta.unstable.json` → `meta.json`, 4 consts added to `SESSION_UPDATE_KIND`): **`114 passed`** in 341 s.

So every fixture's expected FAIL/PASS set in `tests/v2/test_cli.py` is unchanged. In particular, `unprefixed_custom_session_update.py` uses `"surprise"`, `sends_undefined_client_notification.py` uses `made_up/notify`, and `custom_auth_type_unprefixed.py` uses `"sso"`; none of these collides with a new unstable name.

**Tests and fixtures specific to the carve-out** (commits `6e29654`, `b15c7bd`):
- `tests/fixtures/agents/v2/unstable_capability_key.py` + `tests/v2/test_cli.py:2118-2130` (`test_unstable_capability_key_passes_ext_202`). It still passes, but its premise ("only the unstable schema defines it") becomes trivial: `providers` is now just a known `AgentCapabilities` field. **Obsolete as a carve-out test.** Delete it, or keep it reworded as a plain regression ("an RFD-typed capability field is not an extension").
- `tests/fixtures/agents/v2/unknown_capability_root_key.py` + `tests/v2/test_cli.py:2133-2147` (`test_unknown_capability_root_key_fails_ext_202`). It is still meaningful (a genuinely unknown key FAILs ACP-EXT-202), but its docstrings reference "either the stable ... or the Draft unstable schema". **Keep, reword.**
- `6e29654` also added `load_unstable_schema` and the union in `_allowed_root_properties`. Both are deleted by the switch.

### 5. Cross-check baselines

- **`docs/cross-check.md` does not exist in the repo.** There is no `docs/` directory. `AGENTS.md:94-97` references it, so that reference is stale. The actual baseline lives in `scripts/cross-check.sh` `--expect` lines (`testy_v2=` empty, and `python_v2_agent=ACP-BATCH-201,ACP-BATCH-202,ACP-INIT-003,ACP-INIT-201,ACP-INIT-202,ACP-JSONRPC-001,ACP-JSONRPC-003`).
- **`testy` v2:** built `--no-default-features --features unstable_protocol_v2` (`scripts/cross-check.sh:75-80`). In rust-sdk, `unstable` is a *separate* feature (`src/agent-client-protocol-test/Cargo.toml:13-15`), so this build does not emit unstable-feature fields. It is validated against a superset with no new required fields on existing defs, so **no change is expected**.
- **`python_v2_agent.py`:** grep finds no usage/notice/providers/fork/nes/plan_removed/positionEncoding fields, so **no change is expected**.
- **Not verified:** cross-check was not run (it needs cargo builds). The expectation rests on superset reasoning plus the feature flags above.

## Testability notes

- The switch itself is verified by the existing suite: `test_enum_sets_match_the_schema` catches enum drift, and `test_cli.py` pins every fixture's FAIL set. Experiment B shows the suite is green.
- The new strictness of ACP-SCHEMA-001 is testable with a new fixture, for example one emitting `sessionUpdate: "notice"` without `title`. That should FAIL the prompt-turn schema check at `test_prompt.py:203`. It is optional, and only worth adding if the user wants the switch's behavioral delta pinned.
- A "defined-value" regression for ACP-ENUM-202 is also optional: a fixture emitting a correctly shaped `notice` should PASS ACP-ENUM-202. Before the switch it would have FAILed.
- Unstable client→agent surfaces (`nes/*`, `providers/*`, `session/fork`, `document/*`) remain completely unexercised. The switch only changes which agent *output* is recognized.

## Discrepancies

- **Spec docs vs schema pairing:** the unstable schema is generated with `/protocol/v2/draft/` doc links (`schema-generator/src/main.rs:229-241`), and upstream keeps a separate `docs/protocol/v2/draft/*.mdx` tree. All TCK prose citations point at `docs/protocol/v2/*.mdx`, the non-draft tree. Normative diffs between the two trees:
  - *Additive:* notices, compaction, plan removal/file/markdown, NES capability prose.
  - *Removed from draft:* `initialization.mdx:116-117` "Extension-specific capabilities belong in `_meta`." ACP-EXT-202 cites `extensibility.mdx:93,126-149`, which is identical in both trees, so ACP-EXT-202's basis survives. `migration.mdx` has no draft counterpart.
  - This report did not audit whether any other existing requirement's prose citation differs in the draft tree (see Open questions).
- **Stability semantics:** upstream explicitly labels the draft-only variants as unstable and "may change or be removed" (`docs/protocol/v2/draft/prompt-lifecycle.mdx:39`). Validating against them means an agent built against a *different* upstream revision of an unstable feature can FAIL MANDATORY ACP-SCHEMA-001 on a shape mismatch. Example: an agent still sending d880-era `mcp/connect` would be an unknown method under HEAD. The stable schema never produced that failure.

## Open questions

1. **Vendor `meta.unstable.json`?** Yes. Otherwise ACP-CLIENTCAP-202 and schema validation disagree on `mcp/message`.
2. **Refresh to spec HEAD at the same time?** Recommended. HEAD removes the d880 `mcp/message` request/notification collision that the method-keyed dispatch table cannot represent, and stable `schema.json`/`meta.json` are unchanged at HEAD anyway. Optional hardening: key `_request_and_notification_method_defs` by (method, request|notification) so a future bidirectional method cannot be mis-dispatched.
3. **Local file naming:**
   - (a) Keep the upstream names (`schema.unstable.json`, `meta.unstable.json`) and change the 2 paths in `protocol.py`. This makes provenance obvious. **Recommended.**
   - (b) Copy them to `schema.json`/`meta.json` so no code paths change, but the name then lies about the content.
4. **What to do with the ~70 `schema/v2/schema.json:<line>` citations:**
   - (a) Keep them: they are accurate citations of upstream stable `schema.json` at the (bumped) revision, since it is byte-identical.
   - (b) Rewrite them to `schema.unstable.json` line numbers: a large mechanical slice, and every line changes.
   - (c) Rewrite them to def-name citations (`$defs/X`) to stop line drift.
5. **Should prose citations move to `docs/protocol/v2/draft/*.mdx`**, to match the unstable schema? This needs a per-requirement audit of the draft-tree diffs, which is out of scope here and should be routed to a researcher.
6. **Should `mcp/message` from the agent be capability-gated** (only when the client advertised `mcp.acp` and passed an `acp`-type server)? After the switch, ACP-CLIENTCAP-202 accepts it unconditionally. A possible new capability-negative requirement; needs spec research on `docs/rfds/mcp-over-acp.mdx` and the draft docs.
7. **Stale `AGENTS.md:94-97` reference to a nonexistent `docs/cross-check.md`.** This is unrelated to the switch. Fix it separately or together.
