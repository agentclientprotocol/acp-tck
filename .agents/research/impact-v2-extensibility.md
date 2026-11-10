# v2 impact audit: `docs/protocol/v2/draft/extensibility.mdx` (beac4ba -> 3961af9)

**Sources checked:** `agent-client-protocol` spec checkout `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2` @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (target), diffed against base `beac4ba96190018e9f6d82e148ff275084c5aa3e`. I read the whole target doc, the doc diff, the target `schema/v2/schema.unstable.json` (root `anyOf`, every `"other"` fallback branch base vs target, `AuthMethod`, `ReplayFrom`, `AvailableCommand`, `Command`, `_meta` descriptions, `IdleStateUpdate`, `ElicitationSchema`, `EmbeddedResourceResource`), `schema/v2/meta.unstable.json`, and the linked docs `error.mdx`, `overview.mdx` (150-275), `content.mdx:22`, `session-setup.mdx:540-560`, `session-config-options.mdx:234`, and the rust models `agent-client-protocol-schema/src/v2/agent.rs`. Rust SDK `acp-rust-sdk` @ `e75d6f19fabb` (2026-11-09). Python SDK `acp-python-sdk` @ `8a9940744d0a` (2026-11-09). TCK: `src/tck/v2/requirements.py`, `src/tck/v2/validation.py`, `src/tck/v2/protocol.py`, `src/tck/v2/conformance/test_{extensibility,enums,jsonrpc,client_capabilities,authentication,prompt}.py`, `tests/v2/test_cli.py`, `tests/v2/test_registry.py`, `spec-tracker/maps/v2.toml`.
**Confidence:** high for classification and line remaps (read directly from the target text and schema). Medium for the new-requirement tier calls: several rules use declarative wording with no RFC keyword, and those calls are marked DECISION NEEDED.

All target line references below are `docs/protocol/v2/draft/extensibility.mdx` @ 3961af94fa62 unless another file is named.

## Answer

Most of the extensibility diff is rewording and re-casing. Four changes matter to the TCK:

1. **Unknown custom method -> `-32601` went from "should" to MUST** (`:202`). `error.mdx:44` says the same MUST for custom and standard methods alike. `ACP-JSONRPC-004` is registered ADVISORY *because* the wording was "should", so it should move to MANDATORY. DECISION NEEDED. Both reference SDKs already answer `-32601`.
2. **New MUST: a request that can't be fulfilled without understanding an unknown variant gets `-32602`** (`:62-65`). At target the schema makes this concrete for prompt content blocks, MCP transports and config value types. These are all new, client-observable rules with no registry row. I propose `ACP-ENUM-204` (prompt content block), plus two instances to coordinate with the session-setup and config owners.
3. **`_meta` rules are new** (`:74`, `:97-102`). A non-object `_meta` is treated as omitted. `traceparent`/`tracestate`/`baggage` MUST use W3C format. Unprefixed keys and `*.agentclientprotocol/` keys are reserved for ACP, and extension keys SHOULD be reverse-DNS prefixed. The schema `_meta` descriptions now say "Implementations MUST NOT assign meaning to keys they do not recognize" (#2701). I propose three new META rows. The TCK's own `ACP-META-001` probe sends an unprefixed `"tck"` key, which is now an ACP-reserved name. It should switch to a namespaced key.
4. **Unknown notifications: "SHOULD ignore ... whether it is custom or from a later ACP version"** (`:231`; `error.mdx:44`). There is now a SHOULD behind `ACP-EXT-203`, which is INFORMATIONAL only because the spec said "free to ignore". `ACP-EXT-203` also cites the removed `$defs/ProtocolLevelNotification` (B2), so it must be repointed in any case. I recommend ADVISORY. DECISION NEEDED.

The `validation.py` open-enum carve-out is still correct against the target schema (details below). Its module docstring point 1 (batching) is stale because of B1, and `test_enums.py`'s docstring list of closed sites is stale. Two hand-copied enum sets in `protocol.py` must gain `paused` and `session`, or `test_enum_sets_match_the_schema` fails after the schema is re-vendored. Everything else in my list only needs citations remapped.

## Summary table

| id | classification | one-line note |
|---|---|---|
| ACP-EXT-001 | changed text (only if JSONRPC-004 is promoted), else citation-only | Drop "`-32601` remains `ACP-JSONRPC-004`'s separate ADVISORY concern". Citation `:165,174,187,231`. |
| ACP-EXT-201 | citation-only | `:222` -> `:231`. Optional: also cite `error.mdx:44`. |
| ACP-EXT-202 | citation-only | `:239-245` -> `:253-261`. Optional test widening to nested capability objects. |
| ACP-EXT-203 | **changed tier + text + citation** (DECISION NEEDED) | Cited `$def` removed (B2). New SHOULD-ignore at `:231` means INFORMATIONAL -> ADVISORY. |
| ACP-EXT-204 | citation-only | `:49-50,148` -> `:51-52,157`. `initialization.mdx:134` -> `:156` belongs to the init owner. |
| ACP-META-001 | citation-only + test hygiene fix | `:66,89-93,95` -> `:72,74,97-102,104`. The probe's `"tck"` key is now ACP-reserved, so use a reverse-DNS key. |
| ACP-META-201 | unchanged | Pointer still resolves. Optional extra citation `:74`. |
| ACP-ENUM-201 | citation-only (+ required constant-set update) | `:226-231` -> `:235-240`. `TOOL_CALL_STATUS` += `paused`, `TOOL_CALL_CONTENT_TYPE` += `session`. Optional new site `AvailableCommand.type`. |
| ACP-ENUM-203 | citation-only | `:49-53,228,235` -> `:51-55,237,249`. Pointer resolves. The new `-32602` rule covers requests, not this response. |
| ACP-JSONRPC-004 | **changed tier ADVISORY -> MANDATORY** (DECISION NEEDED, recommend yes) | `:202` "it **MUST** respond with ... `-32601`" and `error.mdx:44`. |
| ACP-JSONRPC-005 | citation-only (extensibility part) | `:193-204` -> `:202-213`. The batch wording in its text is B1's / the transports owner's concern. |
| ACP-CLIENTCAP-202 | citation-only, but the `meta.unstable.json` lines need a manual fix | `:156,165` -> `:165,174`. `meta.unstable.json:31-37` was already wrong at base; target is `:28-38`. |
| ACP-AUTH-206 | citation-only | `:224-234` -> `:233-249`. B11 has no effect on this check. |
| ACP-STATE-203 | citation-only (+ pre-existing pointer oddity) | `:226-231` -> `:235-240`. `IdleStateUpdate/anyOf/7` is the `none` branch. The `other` fallback is `anyOf/6`. |
| ACP-SCHEMA-002 | citation-only | `:95,226-233` -> `:104,235-247`. Carve-out still sound. |
| ACP-ENUM-204 (new) | new, CAPABILITY `capabilities.session` | `session/prompt` with an unsupported `_`-typed content block -> `-32602`. |
| ACP-ENUM-205 (new) | new, ADVISORY | Embedded `resource` whose contents are neither text nor blob is rejected (closed site). |
| ACP-ENUM-206 (new, coordinate) | new, CAPABILITY `capabilities.session` | `session/new` with an unknown `_` MCP transport -> `-32602`. Owned jointly with session-setup. |
| ACP-ENUM-207 (new, coordinate) | new, CAPABILITY `inferred:configOptions` | `session/set_config_option` with an unknown `_` value `type` -> `-32602`. Owned jointly with config. |
| ACP-META-202 (new) | new, ADVISORY (DECISION NEEDED) | A non-object `_meta` on `session/prompt` is treated as omitted, so the prompt is accepted. |
| ACP-META-203 (new) | new, CAPABILITY `capabilities.session` (DECISION NEEDED) | Agent-emitted `traceparent`/`tracestate`/`baggage` `_meta` keys are W3C-formatted. |
| ACP-META-204 (new) | new, ADVISORY (DECISION NEEDED whether to add) | Agent-emitted `_meta` keys are namespaced: no unprefixed or `*.agentclientprotocol/` keys beyond the W3C three. |
| 12 ledger entries | new deliberate non-requirements | See "Ledger" below. |

## Requirements (target text, tiered)

| # | Requirement | Tier | Citation (@ 3961af94fa62) |
|---|---|---|---|
| 1 | Do not infer peer support from own schema/generated types/flags | MUST (unobservable -> ledger) | `extensibility.mdx:16-19` |
| 2 | Callers follow each feature's negotiation; omitted/`null` marker = unsupported | MUST (covered per feature, e.g. CLIENTCAP-201) | `:25` |
| 3 | Senders of informational additions don't depend on receiver behaviour | MUST NOT (unobservable -> ledger) | `:26` |
| 4 | Accept unknown fields and unknown discriminator values where the schema permits; closed stays closed | MUST | `:51-55` (EXT-204, ENUM-203) |
| 5 | Malformed recognized discriminator never falls through to the fallback | MUST NOT (ledger, see L3) | `:57-60`, `:159` |
| 6 | Request needing an unknown variant -> `-32602`, else degrade gracefully | **MUST (new)** | `:62-65` (ENUM-204/206/207) |
| 7 | `_meta` is a string-keyed object; any other value is treated as omitted | declarative (new) -> ADVISORY | `:74` (META-202) |
| 8 | Reserved `traceparent`/`tracestate`/`baggage` values use W3C format | **MUST (new; was "SHOULD be reserved")** | `:97-100` (META-203) |
| 9 | Unprefixed keys and `*.agentclientprotocol/` prefixes are reserved for ACP; extension keys reverse-DNS | reserved + SHOULD (new) | `:102`, `:259` (META-204) |
| 10 | No custom fields at the root of a spec type | MUST NOT (ADVISORY in TCK, SCHEMA-002) | `:104` |
| 11 | Metadata patch semantics (clients); intermediaries keep removals/clears | MUST (client/intermediary -> ledger) | `:106-153` |
| 12 | Ignore unrecognized properties; don't reject solely for them | MUST | `:157` (EXT-204) |
| 13 | Names starting with `$/` are reserved for protocol-level messages; all other non-`_` names reserved for ACP | reservation (new sentence) | `:165` (CLIENTCAP-202) |
| 14 | Custom request -> respond with the given `id` | MUST | `:187` (EXT-001) |
| 15 | Unrecognized custom method -> `-32601` | **MUST (was "should")** | `:202-213`; `error.mdx:44` (JSONRPC-004) |
| 16 | Ignore any unrecognized notification, custom or from a later ACP version | SHOULD (broadened) | `:231`; `error.mdx:44` (EXT-201, EXT-203) |
| 17 | Extensions MUST NOT define custom non-`_` values; implementations MUST NOT treat unknown non-`_` values as custom | MUST / MUST NOT | `:237-240` (ENUM-201, AUTH-206, STATE-203) |
| 18 | Closed sites: `ElicitationSchema.type`, embedded resource contents, select `options`, elicitation scope. Receivers reject values outside them. | declarative (new list) | `:242-247` (ENUM-205) |
| 19 | Preserve unknown values/payloads; generic display | SHOULD (ledger) | `:249` |
| 20 | Advertise extensions under `_meta` of capability objects; no custom capability names as properties of root/nested capability objects | SHOULD / MUST NOT | `:253-261` (EXT-202) |
| 21 | `capabilities.session: {_meta}` only if all seven baseline session methods are supported | MUST NOT | `:257` (enforced indirectly by every `capabilities.session`-gated row) |

## Details

### Target doc layout (for citations and the map)

| Section | Lines |
|---|---|
| (intro) | 6 |
| Experimental features and negotiation | 8-47 |
| > When a capability is required | 21-47 |
| > Validation | 49-68 |
| The `_meta` field | 70-104 |
| > Metadata patches | 106-153 |
| Unknown object fields | 155-161 |
| Extension methods | 163-170 |
| > Custom requests | 172-215 |
| > Custom notifications | 217-231 |
| Enum and tagged-union variants | 233-249 |
| Advertising custom capabilities | 251-286 |

**Map (`spec-tracker/maps/v2.toml:64-71`):** extensibility is listed as a whole-doc core entry with no `sections` key, so the heading re-casing breaks nothing. Every heading was re-cased (e.g. `The \`_meta\` Field` -> `The \`_meta\` field`, `Enum and Tagged-Union Variants` -> `Enum and tagged-union variants`). No new heading was added, because `Validation` already existed at base. Keep the doc whole-doc core. The `code` list (`test_extensibility.py`, `test_enums.py`, `validation.py`) is still right. If ENUM-204..207 land in a new module, add it there.

### Base -> target line remap for every citation into this doc

| base | target | content moved? |
|---|---|---|
| 49-50 | 51-52 | no |
| 49-53 | 51-55 | no |
| 66 | 72 | no. New `:74` (`_meta` value shape) sits right after. |
| 89-93 | 97-100 | **yes**: "SHOULD be reserved for W3C trace context" became "reserved, as in MCP ... values MUST use W3C format", plus new `:102` |
| 95 | 104 | no |
| 148 | 157 | no |
| 156 | 165 | **added**: `$/` reserved for protocol-level messages; all other names reserved for ACP |
| 165 | 174 | no |
| 178 | 187 | no |
| 193-204 | 202-213 | **yes**: "should respond" became "**MUST** respond" |
| 222 | 231 | **yes**: broadened to "any notification they don't recognize, whether it is custom or from a later ACP version" |
| 224-234 | 233-248 (section to 249) | **yes**: closed-site list added at 242-247 |
| 226-231 | 235-240 | no (bullets verbatim) |
| 226-233 | 235-247 | yes (233 rewritten as 242-247) |
| 228 | 237 | no |
| 235 | 249 | no |
| 239-245 | 253-261 | yes: naming-convention paragraph added at `:259`; `:261` reworded ("Both sides advertise ... under the same namespaced key ...") |

`spec-impact --fix` should remap these mechanically. Its "Needs review" list should include JSONRPC-004 (meaning changed), EXT-203 (dangling pointer) and CLIENTCAP-202 (stale JSON line range).

### Per-requirement detail

**ACP-EXT-001 (MANDATORY).** The MUST is unchanged (`:187`: "Upon receiving a custom request, implementations **MUST** respond accordingly with the provided `id`"). New citation is `extensibility.mdx:165,174,187,231`. The `overview.mdx:193` part belongs to the overview owner (the JSON-RPC error-handling block is now `overview.mdx:221-229`). If JSONRPC-004 is promoted, change the text's last sentence to "The `-32601` code specifically is `ACP-JSONRPC-004`'s separate concern", and make the same edit in the test docstring (`test_extensibility.py:42-45`). The test assertions stay.

**ACP-EXT-201 (ADVISORY).** The SHOULD is still there (`:231`). Citation `:222` -> `:231`, optionally plus `error.mdx:44` ("Notifications can't be answered, so receivers **SHOULD** ignore unknown ones"). The test is unchanged. The non-`_` "later ACP version" half is better owned by EXT-203 (below), so EXT-201 can stay scoped to `_` notifications.

**ACP-EXT-202 (ADVISORY).** The MUST NOT is unchanged (`:261`). Citation `:239-245` -> `:253-261`. It stays ADVISORY for the same reason as SCHEMA-002: an unrecognized key on `capabilities` could be a field from a newer ACP revision, so the TCK can't tell it apart from a vendor key. Optional widening: `:261` says "root capability object **or nested protocol-defined capability objects**" (this wording was already at base). The test checks only the root `AgentCapabilities` keys, and could also apply `find_unknown_root_keys` to each nested capability object (`session`, `session.prompt`, `auth`, ...). That would be test-only, with no registry text change beyond "or nested". The doc example now uses flat namespaced keys (`"com.example/workspace": true`) instead of a nested `"zed.dev": {...}` object (`:272-275`). That shape is what META-204 (proposed) would check.

**ACP-EXT-203 (INFORMATIONAL).** DECISION NEEDED. Recommendation: ADVISORY, with new text and citation.
- The citation `schema/v2/schema.unstable.json#/$defs/ProtocolLevelNotification` no longer resolves (B2), so `tests/v2/test_registry.py::test_schema_citation_pointers_resolve_in_the_vendored_schema` will fail.
- The "free to ignore" text now lives in the root `anyOf` `ProtocolLevel` entry, at `schema/v2/schema.unstable.json#/anyOf/2/properties/params/anyOf/0`. The `_POINTER_PATTERN` in `tests/v2/test_registry.py:318` accepts root pointers and `_resolve_pointer` handles array indexes, so this pointer would pass. Its weakness is that it is positional: root `anyOf` order is `Agent`, `Client`, `ProtocolLevel`, `Proxy`.
- The doc now has a SHOULD: `:231` "implementations **SHOULD** ignore any notification they don't recognize, whether it is custom or from a later ACP version"; `error.mdx:44` "receivers **SHOULD** ignore unknown ones". `:165` reserves `$/` names for protocol-level messages, so `$/does_not_exist` is exactly a "later ACP version" notification. The INFORMATIONAL rationale ("no conforming/non-conforming distinction") no longer holds. Ignoring is what both "free to ignore" (schema) and the SHOULD (doc) allow, so the two sources do not conflict.
- Proposed text: "An unrecognized non-`_` notification (a `$/`-prefixed protocol-level name, standing in for one from a later ACP version) gets no response and causes no crash (SHOULD ignore)."
- Proposed citation: `docs/protocol/v2/draft/extensibility.mdx:165,231; docs/protocol/v2/draft/error.mdx:44; schema/v2/schema.unstable.json#/anyOf/2/properties/params/anyOf/0`.
- Test change: replace `record_property` with assertions like EXT-201's (a reply is a FAIL, `AgentExited` is a FAIL, silence is a PASS). Optionally also probe a plain unknown name such as `session/tck_future`. Update `test_cli.py` (`_INFORMATIONAL_IDS` -> `_ADVISORY_IDS`) and the hard-coded tier lists in `tests/v2/test_registry.py`.
- A reply is already a MANDATORY violation under `ACP-JSONRPC-003` ("Notifications never receive a response"), but JSONRPC-003's own test does not send a `$/` probe. Retiring EXT-203 instead is defensible only if JSONRPC-003's test takes over the `$/` probe. I don't recommend that.

**ACP-EXT-204 (MANDATORY).** Unchanged. Citation `extensibility.mdx:51-52,157`. The init owner should remap `initialization.mdx:134` to `:156` ("Receivers **MUST** ignore unknown capability fields at every nesting level ... Unknown fields do not advertise support"). Test docstring: `extensibility.mdx:245` -> `:261`. The test probes (`tckFutureCapability`, etc.) are deliberately non-`_`, standing in for future ACP fields, and stay valid.

**ACP-META-001 (ADVISORY).** Unchanged in substance. New citation `:72,74,97-102,104`. Test hygiene: `test_extensibility.py:76-79` sends `_meta: {"traceparent": ..., "tck": True}`. `"tck"` is an unprefixed key, which `:102` now reserves for ACP. `:259` says extension keys use `com.example/<name>` form. The TCK already holds its own probe methods to the `_` rule (CLAUDE.md step 4), so it should send a reverse-DNS namespaced key here (e.g. `"<reverse-dns-of-a-domain-the-project-controls>/probe": true`). Which domain to use is a maintainer choice. Don't use `io.agentclientprotocol/`, which `:102` reserves. The `traceparent` value the test sends (`00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01`) is valid W3C, so it already satisfies the new MUST.

**ACP-META-201 (ADVISORY).** Unchanged. `#/$defs/UpdateSessionNotification/properties/_meta` resolves at target (`type: ["object","null"]`, `x-deserialize-default-on-error: true`). The new sentence at `:74` ("`_meta` is an object with string keys ... Receivers treat any other value as omitted") supports this sender-side check. Optionally add `extensibility.mdx:74` to the citation. The tier stays ADVISORY because receivers are told to tolerate a non-object value.

**ACP-ENUM-201 (CAPABILITY).** Citation `extensibility.mdx:235-240`. The tool-calls and agent-plan parts belong to their owners: tool-calls restates the rule at `tool-calls.mdx:76,372,419`. Required code follow-up from the schema refresh, not from the doc: in the hand-copied sets in `src/tck/v2/protocol.py:73-108`, `TOOL_CALL_STATUS` must gain `paused` (B12) and `TOOL_CALL_CONTENT_TYPE` must gain `session`. I derived the target constant sets from the schema. `SESSION_UPDATE_KIND`, `STATE_UPDATE_STATE`, `TOOL_KIND`, `PLAN_ENTRY_*` and `PERMISSION_OPTION_KIND` are unchanged. Otherwise `tests/v2/test_validation.py::test_enum_sets_match_the_schema` fails. Optional new site: `available_commands_update.availableCommands[*].type`. `AvailableCommand` is now an open tagged union with the defined constant `{"command"}` and an `other` fallback (B5). The agent emits it in ordinary turns, so it fits ENUM-201's "curated subset" design. It would need a new `AVAILABLE_COMMAND_TYPE` set plus a meta-test entry.

**ACP-ENUM-203 (CAPABILITY).** Unchanged. Citation `:51-55,237,249`, and `#/$defs/RequestPermissionOutcome/anyOf/2` resolves (the fallback is unchanged, still `required: ["outcome"]`). The new `-32602` MUST (`:62-65`) applies to *requests* the receiver can't fulfil. ENUM-203's `_tck/unknown` outcome is a *response* to the agent's request, so the test's "prompt not answered with `-32602`" assertion is still consistent. The fallback description still says "Agents that do not understand this outcome MUST NOT treat it as approval". That was already at base, and it is the permission owner's call.

**ACP-JSONRPC-004 (ADVISORY).** DECISION NEEDED. Recommendation: MANDATORY.
- Old: "An unknown method yields `-32601`. Spec wording is still 'should'."
- Target wording: `:202` "If the receiving end doesn't recognize the custom method name, it **MUST** respond with the standard 'Method not found' error". `error.mdx:44`: "A receiver that does not implement a method, or receives a capability-gated method it did not advertise, **MUST** respond with `-32601`. This applies to custom and standard methods alike."
- Proposed text: "A request for a method the agent does not implement (probed with a `_`-prefixed custom method) is answered with error code `-32601`."
- Proposed citation: `docs/protocol/v2/draft/extensibility.mdx:202-213; docs/protocol/v2/draft/error.mdx:42-44`.
- Reference implementations agree. Rust: an unclaimed request gets `Error::method_not_found()` (`src/agent-client-protocol/src/jsonrpc/incoming_actor.rs:624-641`), and `MatchDispatch::otherwise_ignore` does the same (`src/agent-client-protocol/src/util/typed.rs:413-421`). Python v2: `_`-prefixed requests with no `handle_extension_request` raise `RequestError.method_not_found` (`src/acp/experimental/v2/_router.py:66-73`), and so do unknown standard requests (`:62-64`); `-32601` is set at `src/acp/exceptions.py:25-26`.
- Test change: docstring only (`test_jsonrpc.py:106-108`). Keep the SKIP-on-timeout, since a missing reply is EXT-001's MANDATORY defect, and the SKIP stops a single defect from failing two rows.
- Self-test fallout:
  - `tests/v2/test_cli.py`: move the id from `_ADVISORY_IDS` (line 123) to `_MANDATORY_IDS`.
  - `test_v2_unknown_method_no_error_only_fails_the_advisory_requirement` (`:1866-1887`): its name, docstring and `all(req_id in _ADVISORY_IDS ...)` assertion must change.
  - The `unknown_method_no_error.py` fixture docstring ("ADVISORY-only") must change.
  - `tests/v2/test_registry.py`: update the hard-coded ADVISORY list around line 186.
  - `wrong_id_echo.py`'s expected FAIL set (`:1758-1765`) already includes it, so nothing changes there.
- Adjacent, not mine: the "capability-gated method it did not advertise -> `-32601`" half of `error.mdx:44` is a new observable rule. It belongs to the error.mdx owner.

**ACP-JSONRPC-005 (ADVISORY).** The extensibility citation `:193-204` -> `:202-213`. Its text "including an invalid or empty batch" and its second bound test (`test_batch.py:125`) are hit by B1, the batching removal. That belongs to the transports/batch owner.

**ACP-CLIENTCAP-202 (CAPABILITY).** Citation `extensibility.mdx:165,174`. `:165` now also says "Names starting with `$/` are reserved for protocol-level messages ... and all other names are reserved for ACP". That supports the test's rule that a method must be in `CLIENT_METHODS`, in `PROTOCOL_METHODS`, or start with `_`. Two follow-ups:
- `schema/v2/meta.unstable.json:31-37` was already wrong at base: the base file has 31 lines, with `clientMethods` at 21-27 and `protocolMethods` at 28-30. At target `clientMethods` is 28-35 and `protocolMethods` is 36-38. Cite `schema/v2/meta.unstable.json:28-38`. `spec-impact --fix` may not remap JSON line ranges (unverified), so do this by hand.
- `CLIENT_METHODS` (derived from meta) gains `auth/status_update` automatically. The new `proxyMethods` group is not read by `load_meta()`, which is correct because proxy methods are not agent->client. Test unchanged.

**ACP-AUTH-206 (MANDATORY).** Citation `extensibility.mdx:233-249`. The authentication part belongs to the auth owner. B11 (the `AuthMethod/anyOf/2` fallback lost its declared `_meta`/`description`) does not affect it: the fallback still has `required: [type, methodId, name]`, `additionalProperties: true`, and a `not` excluding `agent`/`terminal`. The test only checks `type` legality. `#/$defs/AuthMethod` resolves. Test unchanged.

**ACP-STATE-203 (CAPABILITY).** Citation `extensibility.mdx:235-240`. The prompt-lifecycle lines belong to that owner (the stop-reason open-enum rule is restated at `prompt-lifecycle.mdx:965`). There is a pre-existing oddity that is not caused by this diff. `#/$defs/IdleStateUpdate/anyOf/7` is the `"none"`-titled branch (no stop reason) at both base and target. The `"other"` fallback the row's text is about is `anyOf/6`. Recommend repointing to `anyOf/6`. It resolves either way, so no test fails.

**ACP-SCHEMA-002 (ADVISORY).** Citation `extensibility.mdx:104,235-247`. The new closed-site list (`:242-247`) matches the schema: none of `ElicitationSchema`, `EmbeddedResourceResource` or the select-options defs has an `"other"` branch, so the carve-out can never fire there. Test unchanged.

### `validation.py` open-enum carve-out vs. target rules and schema

I checked this by re-running the carve-out's algorithm (`_discriminator_property` and `_matches_open_fallback_branch`) over the target schema:

- Fallback branches still carry `title: "other"`. There are 38 at target and 33 at base. Added: `AuthState/4`, `AvailableCommand/1`, `BackgroundWork/3`, `SessionArchiveFilter/3`, `SessionStatus/2`. Renumbered: `ToolCallContent/3 -> /4`, `ToolCallStatus/5 -> /6`.
- For every object-typed union with an `"other"` branch, the named branches still each declare exactly one `const` property, and they agree. The algorithm finds the expected discriminator for `AuthMethod`, `AvailableCommand`, `AvailableCommandInput`, `BackgroundWork`, `ContentBlock`, `CreateElicitationRequest` (`mode`), `CreateElicitationResponse` (`action`), `DiffChange` (`operation`), `ElicitationPropertySchema`, `McpServer`, `PlanUpdateContent`, `ReplayFrom`, `RequestPermissionOutcome` (`outcome`), `RequestPermissionSubject`, `SessionConfigOption`, `SessionUpdate` (`sessionUpdate`), `SetSessionConfigOptionRequest`, `StateUpdate` (`state`) and `ToolCallContent`.
- `IdleStateUpdate` (which has a `none` branch) and `MultiSelectItems` (which has a `titled` branch) yield `None`, so the carve-out stays off for them. That is safe, and neither is a top-level params/result `$def`.
- **Rule fit.**
  - `:237-240`: only `_`-prefixed values are custom. The carve-out skips only `_`-prefixed values that are not a named const.
  - `:57-58`, `:159`: a malformed recognized discriminator must not fall through. The carve-out never fires for a named const, a missing/`null` value or a non-string value.
  - `:53`: receivers validate the fallback's required envelope fields. The carve-out skips only unknown-root-key detection. JSON-Schema validation (SCHEMA-001) still enforces the fallback's `required`, e.g. the new `AvailableCommand` fallback `required: [type, name, description]` (B5). At target every object fallback also carries a `not` clause excluding the known consts. For `AvailableCommand` and `BackgroundWork` the clause is new. It enforces the no-fall-through rule at schema level for emitted messages.
  - An unknown non-`_` discriminator still gets full unknown-key detection. That agrees with `:239`, because the agent may not define such values.
- **No code change needed.** Docstring fixes:
  - `validation.py` docstring point 1 (`:8-14`) describes batch arrays as valid top-level lines. That is B1's fallout, for the batch owner.
  - The `:127` comment ("`$/cancel_request` lives under the third top-level single-message branch, `ProtocolLevel`") is still true. `CancelRequestNotification` keeps `x-method: "$/cancel_request"` and `ProtocolLevel` is root `anyOf/2`, but the comment's reasoning is now independent of `ProtocolLevelNotification`.
  - `test_enums.py:3-4` says the schema is open everywhere "except `ElicitationSchemaType` and the JSON-RPC `jsonrpc` literal". The target doc names four closed sites (`:242-247`), so that sentence should be updated.

### Breaking changes (B1-B12) that touch my rows and fixtures

- **B2** -> EXT-203's pointer (above).
- **B5** -> optional ENUM-201 site. No v2 fixture emits `availableCommands` (I grepped `tests/fixtures/agents/v2/`), so no fixture breaks.
- **B11** -> AUTH-206: no effect.
- **B12** -> ENUM-201 constant sets: a required update.
- **B1** -> JSONRPC-005 text and `validation.py` docstring, for the batch owner.

Fixtures in my area:
- `unknown_method_no_error.py` and its `test_cli` assertions change if JSONRPC-004 is promoted.
- `unknown_capability_root_key.py` (EXT-202), `custom_auth_type_unprefixed.py` (AUTH-206) and `unknown_root_key.py` (SCHEMA-002) are unaffected.
- `message_split_across_multiple_lines.py:18` emits `_meta: {"tags": [...]}`, which is an unprefixed key. It sits on the JSON-RPC envelope, not on an ACP object, and comes after EOF. META-204, if adopted, should scan only ACP-object `_meta`, and then this fixture is unaffected.

### New requirement proposals

**ACP-ENUM-204.** Tier CAPABILITY, `capabilities.session`. That follows the session-baseline tiering rule; the underlying wording is MUST.
- Text: "A `session/prompt` whose `prompt` contains a content block with an unadvertised `_`-prefixed `type` is rejected with error `-32602`, and no turn starts."
- Citation: `docs/protocol/v2/draft/extensibility.mdx:62-65 @ 3961af94fa62; docs/protocol/v2/draft/content.mdx:22 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/ContentBlock/anyOf/5`. The fallback description reads: "Agents MUST reject a `session/prompt` request with a content block type they do not support with `-32602`". This sentence is new at target; base said only "ignore it or display it generically". `content.mdx:22` adds: "Agents reject others with `-32602`".
- Observe: send `session/prompt` with `[{"type":"text","text":"hi"}, {"type":"_tck/unsupported","data":1}]`. Expect a JSON-RPC error response with code `-32602`. FAIL on a result (`messageId`), on a different error code, or on a crash. The `_` prefix keeps the TCK within `:239`, and the agent cannot have advertised a `_tck/...` type.
- Coordinate with the content.mdx owner to avoid duplicating this row.
- Suggested fixture: `accepts_unknown_content_block.py`, which accepts the prompt and silently drops the block.
- The base conforming agent (`_base.py` `_prompt_rejection`) would need to reject unknown block types with `-32602`.

**ACP-ENUM-205.** Tier ADVISORY. The rule is declarative, "receivers reject values outside them", with no RFC keyword. The test carries the marker `capabilities.session.prompt.embeddedContext`, and the registry `capability` stays `None`, following the META-201 convention (no ADVISORY row sets `capability`).
- Text: "A prompt `resource` block whose `resource` is neither text nor blob contents is rejected (closed site), with `-32602`."
- Citation: `docs/protocol/v2/draft/extensibility.mdx:242-245 @ 3961af94fa62; docs/protocol/v2/draft/error.mdx:31 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/EmbeddedResourceResource`.
- Observe: send `{"type":"resource","resource":{"uri":"file:///tmp/tck.txt"}}` (no `text` or `blob`). Expect an error with `-32602`.
- Fixture: `accepts_contentless_embedded_resource.py`.
- Lower value than ENUM-204. Optional.

**ACP-ENUM-206** (coordinate with the session-setup owner, who will probably find this independently). Tier CAPABILITY, `capabilities.session`.
- Text: "`session/new` with an `mcpServers` entry whose `type` is an unsupported `_`-prefixed transport is rejected with `-32602`."
- Citation: `docs/protocol/v2/draft/session-setup.mdx:544 @ 3961af94fa62` ("Agents **MUST** reject a request with a transport they don't support with `-32602`, including a transport they did not advertise"); `extensibility.mdx:62-65`; `schema/v2/schema.unstable.json#/$defs/McpServer/anyOf/3`. Base allowed "ignore it or reject the server configuration".
- Observe: `mcpServers: [{"type":"_tck/unsupported","name":"tck"}]` -> error `-32602`.
- Fixture: `ignores_unknown_mcp_transport.py`.

**ACP-ENUM-207** (coordinate with the session-config-options owner). Tier CAPABILITY, `inferred:configOptions`.
- Text: "`session/set_config_option` with an advertised `configId` but an unsupported `_`-prefixed value `type` is rejected with `-32602`."
- Citation: `docs/protocol/v2/draft/session-config-options.mdx:234 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionRequest/anyOf/2`.
- Observe: take a `configId` from `session/new` and send `{"type":"_tck/unsupported","value":1}` -> `-32602`. SKIP when no `configOptions` are advertised.
- Fixture: `config_accepts_unknown_value_type.py`.

**ACP-META-202.** Tier ADVISORY. DECISION NEEDED: ADVISORY or MANDATORY. The text uses declarative "Receivers treat", with no RFC keyword. Existing TCK practice (`ACP-BATCH-203`) makes keyword-less rules ADVISORY.
- Text: "A `session/prompt` whose `_meta` is not an object (e.g. a string) is treated as if `_meta` were omitted: it is accepted and the turn proceeds."
- Citation: `docs/protocol/v2/draft/extensibility.mdx:74 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/PromptRequest/properties/_meta` (`x-deserialize-default-on-error: true`).
- Observe: `run_prompt(..., extra_params={"_meta": "tck"})`. Expect an acceptance receipt and a terminating idle, the same assertions as META-001. FAIL on `-32602`.
- Fixture: `rejects_malformed_meta.py` (validates `_meta` strictly and returns `-32602`).
- Note the SDK disagreement under Discrepancies: a Python-SDK agent would fail this today. That supports ADVISORY.

**ACP-META-203.** Tier CAPABILITY, `capabilities.session`. DECISION NEEDED. The wording is a plain MUST, and the row is CAPABILITY only because the sweep drives a turn, as ENUM-201 does. The alternative is MANDATORY scanning only the `initialize` result, which would almost never see one of these keys.
- Text: "Wherever the agent emits a `_meta` object containing a root `traceparent`, `tracestate` or `baggage` key, the value is in the corresponding W3C format."
- Citation: `docs/protocol/v2/draft/extensibility.mdx:97-100 @ 3961af94fa62`. At base this was only "SHOULD be reserved".
- Observe: sweep the transcript as META-201 does.
  - `traceparent` must be a string matching W3C Trace Context `version-traceid-parentid-flags`. That is lowercase hex `^[0-9a-f]{2}-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}`. Version `00` takes no suffix; a future version (not `ff`) may append `-...`. Trace-id and parent-id must not be all zeros.
  - `tracestate` and `baggage`: assert only that each is a string. Full list-member grammar checking is possible but out of proportion for this check. These format details come from W3C, not ACP; I did not fetch the W3C texts in this audit, so the regex is a hypothesis to confirm against https://www.w3.org/TR/trace-context/.
  - PASS is vacuous when no such key appears, so it should SKIP, as AUTH-206 does.
- Fixture: `malformed_traceparent.py` (adds `_meta: {"traceparent": "not-a-trace-id"}` to a `session/update`).

**ACP-META-204.** Tier ADVISORY. DECISION NEEDED: whether to add it at all.
- Text: "Every key of an agent-emitted `_meta` object on an ACP-defined object is either `traceparent`/`tracestate`/`baggage` or carries a `/`-terminated namespace prefix whose second label is not `agentclientprotocol`."
- Citation: `docs/protocol/v2/draft/extensibility.mdx:102,259 @ 3961af94fa62`. `:102` reads: unprefixed keys and `agentclientprotocol`-second-label prefixes are reserved for ACP, and "Extension keys **SHOULD** use a reverse-DNS prefix". ACP defines no unprefixed `_meta` keys of its own: I grepped the target draft docs and schema and found none besides the W3C three.
- Observe: sweep `_meta` on `initialize` `result.capabilities` and its nested objects, on params/result roots, and on `session/update` `params`/`update`.
- **Exclude** `_meta` inside content blocks or tool output. `:102` says MCP-reserved keys and prefixes keep their MCP meaning and Agents preserve them when forwarding MCP content, so forwarded MCP content can legitimately carry MCP's unprefixed keys.
- Risk: this would flag real agents that use bare vendor keys, as v1-era agents commonly did. That is a hypothesis; I did not check any real agent. ADVISORY never affects the verdict.
- Fixture: `unprefixed_meta_key.py` (`capabilities._meta: {"vendorThing": true}`).

### Ledger (deliberate non-requirements), all `docs/protocol/v2/draft/extensibility.mdx` @ 3961af94fa62 unless noted

| # | citation | statement | reason |
|---|---|---|---|
| L1 | `:16-19` | Implementations MUST NOT infer peer support from their own schema selection, generated types, or local feature flags. | Unobservable as such. Concrete instances are tested per feature (e.g. ACP-CLIENTCAP-201). |
| L2 | `:26` | Senders of informational additions MUST NOT depend on feature-specific presentation, acknowledgement, or action. | Unobservable (internal dependency). |
| L3 | `:57-60`, `:159` | A malformed value for a recognized discriminator MUST NOT be treated as an unknown variant. | Receiver side: indistinguishable on the wire from correct rejection at the agent-receive sites (both end in an error or a decline). Sender side: covered by schema `not` clauses via ACP-SCHEMA-001. |
| L4 | `schema/v2/schema.unstable.json#/$defs/PromptRequest/properties/_meta` (description, #2701); `:157` | Implementations MUST NOT assign meaning to `_meta` keys (or unknown properties) they do not recognize. | Unobservable internal interpretation. The one observable case (an unknown capability field advertises nothing) is ACP-EXT-204. |
| L5 | `:102` | Agents preserve MCP-reserved `_meta` keys and prefixes when forwarding MCP content. | Out of scope: needs a live MCP server fixture whose content flows back. |
| L6 | `:108-115` | Clients apply upsert `_meta` as a per-key patch and MUST NOT merge nested objects. | Client-side rule. |
| L7 | `:151` | Intermediaries that combine updates MUST keep removals and clears. | Intermediary rule, out of scope for an agent TCK. |
| L8 | `:215` | Extensions SHOULD advertise their custom capabilities. | Unobservable: the TCK cannot know which extensions an agent has. |
| L9 | `:231` (recognized half) | Implementations MAY expose and call custom requests. | MAY, nothing to assert. |
| L10 | `:240` | Implementations MUST NOT treat unknown non-underscore values as custom extensions. | Unobservable internal interpretation. |
| L11 | `:249` | Implementations SHOULD preserve unknown values and raw tagged-union payloads when storing/replaying/proxying/forwarding, and SHOULD display them generically. | Agent-side storage would need the client to send unknown variants that are later replayed. The agent-received sites either must reject (ContentBlock, McpServer) or are responses. Display is client-side. |
| L12 | `:261` | Both sides advertise an extension under the same namespaced key in the matching `_meta` location. | Extension-specific, unobservable without knowing the extension. |

## Testability notes

- Conforming vs non-conforming, by row:
  - JSONRPC-004: a non-`-32601` error or a success result is a FAIL. No reply is a SKIP (EXT-001 owns it).
  - ENUM-204/206/207: an acceptance, a different error code, or a crash is a FAIL. These are deterministic probes with no race.
  - META-202: rejection is a FAIL.
  - META-203/204: passive sweeps, vacuous (SKIP) when the agent never emits the keys.
  - EXT-203 (if ADVISORY): silence is a PASS; a reply or an exit is a FAIL. Same quiet-period mechanics as EXT-201.
- The ENUM-204/205/206/207 probes deliberately break client-side MUSTs. Examples: "Clients send only baseline content types" (`content.mdx:22`), "Clients MUST NOT call it otherwise and MUST only send an advertised `configId`" (the TCK sends an advertised `configId` with a bad type, which is allowed to probe). This is the same stance as existing negative probes (RESUME unknown cursor, malformed `protocolVersion`).
- Cannot be observed from the client side: everything in the ledger, plus whether an agent "understands" a variant. The `-32602` MUST is conditional on "can't be fulfilled without understanding". The TCK makes it unconditional by probing only sites where the schema or docs state an unconditional MUST-reject (ContentBlock, McpServer, config value type). It does not probe sites where graceful degradation is allowed, such as ToolCallContent or SessionUpdate, which are agent-emitted anyway.

## Discrepancies

1. **The Python SDK lags the spec on `_meta` tolerance (relevant to META-202).** Target spec: non-object `_meta` is treated as omitted (`extensibility.mdx:74`); the schema marks every `_meta` with `x-deserialize-default-on-error: true`. The Rust v2 models agree (`agent-client-protocol-schema/src/v2/agent.rs:60-64` @ 3961af9: `#[serde_as(deserialize_as = "DefaultOnError")]` on `meta`). The Python SDK v2 models declare `field_meta: Optional[Dict[str, Any]]` with no default-on-error validator: `src/acp/experimental/v2/schema.py:4943` (PromptRequest), and `grep 'field_validator(' ... | grep meta` gives 0 hits. A string `_meta` would therefore fail Pydantic validation there, presumably surfacing as an error response (inferred, not run). The Python v2 schema also still carries the pre-#2701 `_meta` description ("MUST NOT make assumptions about values"), i.e. it is generated from an older schema.
2. **"Free to ignore" (schema `ProtocolLevel` description) vs "SHOULD ignore" (`extensibility.mdx:231`, `error.mdx:44`) for `$/` notifications.** These are compatible: both permit ignoring, and the doc adds the recommendation. Not a real conflict, but it is why EXT-203's tier rationale must change.
3. **Pre-existing citation errors (not caused by this diff):** CLIENTCAP-202's `meta.unstable.json:31-37` was beyond the end of the base file. STATE-203's `IdleStateUpdate/anyOf/7` points at the `none` branch rather than the `other` fallback (`anyOf/6`).

## Open questions

- The `error.mdx:44` second half ("receives a capability-gated method it did not advertise MUST respond with `-32601`") is a new observable agent rule. It belongs to the error.mdx owner. It also bears on how the TCK probes unadvertised `session/*` extras.
- ENUM-206/207 overlap with the session-setup and session-config-options audits. The orchestrator should dedupe the ids, and ENUM-204 likewise with the content.mdx owner (content.mdx is not core and may have no owner).
- `session-setup.mdx:474,477` (system-prompt `mode` and content-block MUST-error rules) restate the unknown-variant rule for `systemPrompt`. They belong to the session-setup/SYSPROMPT owner.
- Which reverse-DNS namespace the TCK should use for its own `_meta` probe keys (META-001, and META-202 if it sends any key). Maintainer choice.
- `validation.py` docstring point 1 and `ACP-JSONRPC-005`'s batch half belong to the B1/transports owner.
