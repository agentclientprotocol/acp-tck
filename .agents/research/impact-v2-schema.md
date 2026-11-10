# v2 schema/validation mechanics impact: `schema/v2/{schema,meta}.unstable.json` `beac4ba` -> `3961af9`

**Sources checked:** agent-client-protocol @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (target) and `beac4ba96190018e9f6d82e148ff275084c5aa3e` (base), read via `git show` from `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`, not pulled. The base files are byte-identical to the vendored `src/tck/v2/schema/{schema,meta}.unstable.json` (checked with `cmp`). TCK working tree at `6121fe1`. Rust/Python SDKs not consulted, because every question here is about schema structure and the TCK's own code.
**Confidence:** high. The findings come from running the TCK's own code against the target schema: a scratch copy at `/tmp/v2chk/repo` with only the two vendored files swapped, plus scripts that resolve every pointer and compare base and target. Nothing in the repo was modified.

## Summary table

| id / item | classification | note |
|---|---|---|
| validation carve-out 1 (batching) | **now wrong** | Target root `anyOf` has no array branch. `validate_agent_message`/`validate_agent_response` still accept a non-empty array as valid. |
| validation carve-out 2 (no `null` result special case) | unchanged | Still true: none of the 21 `AgentResponse` result `$defs` accepts `null` at target (checked). |
| validation carve-out 3 (open-enum `"other"` fallback) | unchanged, still needed | Works for all 37 open unions at target, including the new `AvailableCommand`, `BackgroundWork` and `ToolCallContent.session`. |
| `_is_valid_request_id` / `validate_response_envelope` | **now wrong (too lax)** | Still accepts `id: null` on a *result* response. Target allows `null` only in the error branch. |
| request-id check on agent->client requests | **gap (pre-existing, now sharper)** | `validate_agent_message` never checks a request's `id`, so `null`/object/bool ids pass. |
| `protocol.py` method tables | unchanged mechanics; docstrings stale | New methods are picked up automatically with the right direction. The new `proxyMethods` meta key is ignored (correct for an agent TCK). |
| `protocol.TOOL_CALL_STATUS`, `TOOL_CALL_CONTENT_TYPE` | **must update** | Missing `paused` and `session`. `tests/v2/test_validation.py::test_enum_sets_match_the_schema` fails at target. |
| ACP-AUTH-202 | citation pointer dangling | `#/$defs/AuthCapabilities` -> `#/$defs/ClientAuthCapabilities` (shape is the same). |
| ACP-EXT-203 | citation pointer dangling | `#/$defs/ProtocolLevelNotification` is gone. Replacement below (also `test_extensibility.py:218`). |
| ACP-JSONRPC-001, ACP-JSONRPC-002 | citation pointer dangling | `#/anyOf/3/items` -> `#/$defs/AgentResponse` |
| ACP-BATCH-201, ACP-BATCH-207 | citation pointer dangling | Batch envelopes removed. Follows whatever the transport/batch researcher decides (likely retirement). |
| **ACP-TRANSPORT-201, ACP-INFO-BATCH-202** | **pointer resolves but silently re-targets** | `#/anyOf/2`, `#/anyOf/3` now resolve to `ProtocolLevel`/`Proxy`, not the batch branches. `test_registry` cannot catch this. |
| ACP-SCHEMA-001 | unchanged | `#/anyOf` still resolves and still means "root". Validation does not dispatch on the root. |
| ACP-SCHEMA-002 | citation-only (lines) | The rule is prose only (`extensibility.mdx:104,235-240` at target). No JSON-Pointer anchor exists. |
| ACP-CLIENTCAP-202 | citation wrong (pre-existing) | `meta.unstable.json:31-37` was already wrong at base (past EOF of the 31-line file). Target: `28-35` (clientMethods), `36-38` (protocolMethods). |
| ACP-PROMPT-205 | `schema.mdx` cite can be repointed | -> `#/$defs/SubagentUpdate/description` (name-stable). |
| ACP-CANCEL-201/202/204, ACP-FORK-201/202, ACP-AUTH-205 | `schema.mdx` cite: keep lines (DECISION NEEDED) | The prose lives only in *positional* `ClientRequest`/`ClientNotification` `anyOf` branches, which shifted (`session/new` went from 6 to 7, `session/fork` from 9 to 10). |
| Fixtures vs B5-B10 | **no fixture breaks** | All 103 `tests/v2/test_cli.py` tests pass against the target schema with today's code (8m49s run). No fixture emits the tightened shapes. |
| TCK `_meta: {"tck": true}` | **own traffic now uses an ACP-reserved key** | `extensibility.mdx:102`. Not a rule the TCK checks on agents, but it should be renamed. |

## Answer

The schema refresh breaks less than the inventory suggests. With today's code, all 103 `tests/v2/test_cli.py` end-to-end tests pass against the target schema. The registry test fails only on the dangling pointers, and the enum-drift test fails on two hand-copied sets. Validation's method dispatch reads `$defs` (`AgentRequest`/`AgentNotification`/`AgentResponse`/`CancelRequestNotification`) by name, never the root `anyOf`. So shrinking the root `anyOf` from 7 entries to 4 does not affect it.

Three hand-written behaviours are now wrong at target, all because they are too permissive:
- They accept a non-empty JSON array.
- They accept `id: null` on a result response.
- They never type-check a request `id`.

Two citation hazards exist that `test_registry` cannot see. `#/anyOf/2` and `#/anyOf/3` (ACP-TRANSPORT-201, ACP-INFO-BATCH-202) still resolve, but now point at `ProtocolLevel`/`Proxy` instead of `AgentBatchCall`/`AgentBatchResponse`.

No fixture becomes schema-invalid from B5-B10.

The TCK's own `_meta` key `"tck"` is now an ACP-reserved name. This is a hygiene fix: no TCK check on agents covers `_meta` key names.

## Requirements

Requirement-level classification is in the summary table. This report proposes no new requirement ids, because the doc-level rules belong to other researchers. The changes needed in the validation module are listed below as implementation items.

| # | Item | Tier impact | Citation (target `3961af94fa62`) |
|---|------|-------------|----------------------------|
| 1 | Reject any JSON array at the root of an agent line | Feeds whatever replaces ACP-TRANSPORT-201 / BATCH-* (MUST) | `docs/protocol/v2/draft/transports.mdx:20,67`. The root `anyOf` has only object branches (`schema/v2/schema.unstable.json#/anyOf`). |
| 2 | Result response `id` must be integer or string; error response `id` may also be `null` | MUST (feeds JSONRPC-002 / SCHEMA-001 envelope checks) | `docs/protocol/v2/draft/overview.mdx:15-17`; `schema/v2/schema.unstable.json#/$defs/RequestId`; `#/$defs/AgentResponse` (result branch `$ref RequestId`; error branch inline `integer|string|null`) |
| 3 | Agent->client request `id` must be integer or string | MUST | `overview.mdx:15-16`; `schema/v2/schema.unstable.json#/$defs/AgentRequest` (`id` `$ref RequestId`) |
| 4 | `TOOL_CALL_STATUS += {"paused"}`, `TOOL_CALL_CONTENT_TYPE += {"session"}` | ACP-ENUM-201 (MANDATORY) value sets | `schema/v2/schema.unstable.json#/$defs/ToolCallStatus`, `#/$defs/ToolCallContent` |

## Details

### Task 1: carve-outs in `src/tck/v2/validation.py` against the target schema

**Root layout.** Base root `anyOf` had 7 entries: `Agent`, `Client`, `AgentBatchCall`, `AgentBatchResponse`, `ClientBatchCall`, `ClientBatchResponse`, `ProtocolLevel`. Target has 4: `Agent`, `Client`, `ProtocolLevel`, `Proxy`. `ProtocolLevel` was already a root entry at base (index 6). Only `$defs/ProtocolLevelNotification` was removed, and its content is now inline only in the root `ProtocolLevel` branch. The `Proxy` branch refs the new `$defs/ProxyRequest` / `ProxyResponse` / `ProxyNotification` (`proxy/initialize`, `proxy/successor`, `x-side: "proxy"`).

**Dispatch does not use the root, by position or by name.** Every schema read in `validation.py` goes through `load_schema()["$defs"]`:
- `validation.py:119-131`: `AgentRequest`, `AgentNotification`, `CancelRequestNotification`.
- `validation.py:139-153`: the `AgentResponse` result branch, selected by content, not position.
- `validation.py:396` and `:431`: `$defs` only.

The only root reference is a cosmetic string in `_empty_batch_issue` (`validation.py:224`). The same holds for `protocol.py` (`:165`, `$defs` only). The `"$/cancel_request` lives under the third top-level single-message branch" comment (`validation.py:127`) is still true: `ProtocolLevel` is the 3rd root entry at target.

At target the dispatch maps re-derive automatically and correctly (checked):
- `_request_and_notification_method_defs()` = `{session/request_permission, elicitation/create, mcp/message}` requests, plus `{session/update, elicitation/complete, auth/status_update, $/cancel_request}` notifications.
- `_response_method_defs()` covers 21 methods, including `auth/status`, `session/{archive,unarchive,status,set_title}`, `tool_call/cancel`, `terminal/cancel`.
- The `proxy/*` methods are correctly absent, because they are not under `Agent*`.

**Carve-out 1 (batching): now wrong.**
- What the code does today:
  - `validate_agent_message` (`validation.py:244-250`) and `validate_agent_response` (`:479-485`) validate a non-empty list element by element and report nothing about the list itself.
  - Probe at target: `validate_agent_message([{valid session/update}])` returns `[]`.
  - `Draft202012Validator(target_root).is_valid([...])` returns `False`.
- What the target says: `transports.mdx:20` ("Each message is a single JSON-RPC request, notification, or response object") and `:65-67` ("Senders **MUST NOT** send a JSON array of messages...").
- Proposal (for whoever owns the batch redesign): any `list` becomes one root-level issue, e.g. `message must be a single JSON-RPC object (transports.mdx "No batches"), got array`. The empty-array special case, the `/<index>` prefixing and the batch half of the docstring are then obsolete.
- Callers that unwrap arrays today (`_helpers.py:574`, `:614`, `:968`; `test_extensibility.py:241` mentions `iter_messages`) belong to the batch/transport slice. Flag them to that researcher; I did not redesign them.

**Carve-out 2 (no `null` result special case): unchanged.** At target, none of the 21 `AgentResponse` result `$defs` validates `null` (checked with `_def_validator(name).is_valid(None)`). Ten of them have required fields: `InitializeResponse` (`protocolVersion`, `info`), `ListProvidersResponse`, `AuthStatusResponse` (`state`), `NewSessionResponse`, `ListSessionsResponse`, `ForkSessionResponse`, `SessionStatusResponse` (`status`), `SetSessionTitleResponse` (`title`), `SetSessionConfigOptionResponse`, `PromptResponse`. `ProxySuccessorResponse` is schema-less (any JSON) but lives under `ProxyResponse`, so it is never consulted.

**Carve-out 3 (open-enum `"other"` fallback): unchanged, still needed.**
- `_matches_open_fallback_branch` / `_discriminator_property` (`validation.py:403-446`) run unchanged on target. Every object-valued open union still yields a single const discriminator.
- New or changed object unions it now also covers correctly:
  - `AvailableCommand`: now a union (B5); discriminator `type`; the `other` branch requires `type`, `name`, `description`.
  - `BackgroundWork`: discriminator `type`.
  - `ToolCallContent`: gains a named `session` branch, so it now has 5 branches.
- Probes: `find_unknown_root_keys("AvailableCommand", {"name","description","bogus"})` gives `["bogus"]`. With `type: "_x"` it gives `[]`.
- B11 (the `AuthMethod`/`ReplayFrom` `other` branches lost their declared `_meta`/`description`) has no effect:
  - A `_`-prefixed discriminator skips the check anyway.
  - For a known discriminator, `_collect_root_properties` unions properties across all branches, so the named variants still contribute `description`.
  - `_meta` is always allowed (`validation.py:399`).
- String-only open enums (`AuthState`, `SessionStatus`, `SessionArchiveFilter`, etc.) have no discriminator, so the function returns `False`, which is correct.
- The `oneOf` added for elicitation scope (B6) is walked by `_collect_root_properties` (`validation.py:378`) and validated natively by jsonschema.

**Other hand-written behaviour.**
- **`_is_valid_request_id` (`validation.py:201-205`) is now wrong.** Its docstring says "`RequestId` is `null | integer | string`, same as v1". At target, `$defs/RequestId` is `integer | string`, and its description says "Unlike base JSON-RPC, it MUST NOT be `null`". `validate_response_envelope` (`:323`) applies it to both branches, so `{"id": null, "result": {}}` passes today (probe: `[]`). The full root schema rejects it, while `{"id": null, "error": {...}}` is accepted.
  - Fix: allow `null` only when `"error" in msg`.
  - Error text at `:327` also needs updating ("string, integer, or null").
  - Citation: `overview.mdx:15-17`; `#/$defs/AgentResponse` error branch `id` is inline `anyOf [int64, string, null]` (Appendix B "AgentResponse").
- **Request ids are never checked (gap).**
  - In `validate_agent_message`, `is_request = "id" in msg` (`:282`), and only `params` is validated (`:308-310`).
  - Probe: `{"id": null, "method": "session/request_permission", ...}` gives only params issues, nothing on `/id`.
  - At target this is a MUST violation (`overview.mdx:15-16`; `AgentRequest.properties.id` -> `RequestId`).
  - Proposal: when `"id" in msg` and the method is a known request, add an `/id` issue unless the id is a non-bool int or a str.
- **`find_non_object_markers` / `_resolve_object_schema` (`:519-568`): unchanged and working.** At target they flag new boolean-instead-of-object markers: probe on `{"session": {"archive": true, "status": true, "title": true}, "auth": {"status": true}}` gives all four paths.
- Custom keywords `x-deserialize-default-on-null` (new) and the removed `x-deserialize-default-on-error` are ignored by jsonschema. `check_schema` still passes at target, since 65 of 67 `tests/v2` unit tests pass (see below).
- **Docstrings that go stale at target (mechanical):**
  - `validation.py:8-13` (point 1, batching).
  - `:202` (RequestId).
  - `:224`, `:256`, `:491` (batch wording).
  - `src/tck/v2/schema/VENDORED.md` step 5 (lists the 7-entry root layout; replace with `Agent` / `Client` / `ProtocolLevel` / `Proxy`) and "schema version `2.0.0-alpha.9`".
  - `protocol.py:27` (`2.0.0-alpha.9`).

### Task 2: `src/tck/v2/protocol.py` method tables from the new `meta.unstable.json`

Target meta (`schema/v2/meta.unstable.json`, 43 lines):
- `agentMethods` (`:3-27`) gains `session/archive`, `session/unarchive`, `session/status`, `session/set_title`, `tool_call/cancel`, `terminal/cancel`, `auth/status`.
- `clientMethods` (`:28-35`) gains `auth/status_update`.
- `protocolMethods` (`:36-38`) is unchanged.
- **New top-level key `proxyMethods`** (`:39-42`): `proxy/initialize`, `proxy/successor`.

Effects at target (computed in the scratch copy):
- `AGENT_METHODS` (`protocol.py:175`) and `CLIENT_METHODS` (`:179`) pick up the new methods automatically. Directions agree with the schema's `x-side` annotations:
  - the 7 new `agentMethods` have `x-side: agent` under `ClientRequest`;
  - `auth/status_update` has `x-side: client` under `AgentNotification`.
- No misclassification is possible from meta alone.
- `CLIENT_NOTIFICATIONS` = `{session/update, elicitation/complete, auth/status_update}`; `AGENT_NOTIFICATIONS` = `{session/cancel, mcp/message}`. This is unchanged; the docstring at `:187` already undercounts `mcp/message` (pre-existing nit).
- `proxyMethods` is **not read** by `protocol.py`. This is correct for an agent TCK. Per `overview.mdx:266`, proxy chains are "Conductors and proxies only". The RFD (`docs/rfds/proxy-chains.mdx:155`) says a conductor "appears to be an ordinary agent" to its client. A terminal agent or conductor talking to the TCK therefore should never send `proxy/*`. If one does, ACP-CLIENTCAP-202 FAILs it as an undefined client method, which is the right result.
- Stale docstrings:
  - `load_meta` (`:129-132`, "three flat dicts").
  - `KNOWN_METHODS` (`:193`, "all three inventories"; it now excludes `proxyMethods`, and nothing uses `KNOWN_METHODS` anyway: `rg` finds no consumer).
- **Fixed-set assumptions found:** only the hand-copied enum constants (`protocol.py:73-108`). At target:
  - `TOOL_CALL_STATUS` lacks `paused`;
  - `TOOL_CALL_CONTENT_TYPE` lacks `session`;
  - the other 7 sets match.
- `tests/v2/test_validation.py::test_enum_sets_match_the_schema` fails at target (first assertion, `:185`), as designed. Until fixed, ACP-ENUM-201 would wrongly FAIL an agent that emits `status: "paused"` or tool-call content `type: "session"`. These are mechanical updates; the semantics belong to the tool-calls researcher.
- The method-table consumer is `test_client_capabilities.py:15,21` (ACP-CLIENTCAP-202). At target an agent emitting `auth/status_update` no longer FAILs CLIENTCAP-202. Whether that notification must be gated on the agent advertising `auth.status` (`overview.mdx:260` "Negotiation: Agent `auth.status`") is an authentication-doc question (see Open questions).

### Task 3: `RequestId` drops `null`

- **Validation:** wrong in two places; see Task 1, "Other hand-written behaviour".
- **Harness (version-agnostic):** never produces a null request id. `send_request` (`src/tck/common/harness/process.py:196-208`) substitutes an auto-increment int when `id is None`, so `id=None` cannot be sent through it. No v2 test sends `"id": null` raw (`rg` over `src/tck/v2`).
- **Mock client:** echoes whatever id the agent used. In `_helpers.py:1031-1044`, `{"id": msg["id"], "result": ...}` replies to `session/request_permission` and `-32601` errors to others. If an agent sends a request with `id: null`, the TCK answers with a null-id *result*, which is itself invalid at target. This only happens after the agent has already violated a MUST, and the TCK never validates its own traffic (`CLAUDE.md`, "Vendored schema"), so it misjudges nobody. Optional hardening: answer such a request with an error and add the Task 1 request-id check, so the agent's violation is reported.
- **Fixtures emitting null ids:**
  - `_base.py:164,181`, `rejects_batch.py:23`, `noisy_stderr_and_parse_error_reply.py:33`: `id: null` on **error** responses (`-32600`/`-32700`). Still valid at target.
  - `answers_notifications.py:23` and `pushes_status_and_answers_notifications.py:24`: `{"id": null, "result": null}`. Invalid at target on two counts (null id on a result, plus a `null` result). Both fixtures are deliberately non-conforming for ACP-JSONRPC-003, and their CLI tests are `-k`-scoped (`tests/v2/test_cli.py:1784`, `-k jsonrpc`). Tightening `_is_valid_request_id` could add an envelope issue in any test that runs `validate_response_envelope` over unsolicited responses. Re-check `test_cli.py:1780-1830` after the change, though the expected FAIL set is unlikely to move, since JSONRPC-003 already FAILs.

### Task 4: v2 registry rows citing schema JSON-Pointers

I ran the `tests/v2/test_registry.py` extraction regex over every registry citation and every `.py` under `src/tck/v2`, `tests/v2` and `tests/fixtures/agents/v2`, against base and target: 267 pointers. All resolve at base. At target, these do not:

| Source | Pointer (base) | Proposed replacement at target |
|---|---|---|
| ACP-AUTH-202 (`requirements.py:1438`) | `#/$defs/AuthCapabilities` | `schema/v2/schema.unstable.json#/$defs/ClientAuthCapabilities`. The structure is identical (`terminal` -> `TerminalAuthCapabilities`, `_meta`). Optionally add `#/$defs/ClientCapabilities/properties/auth`, whose description now says it "Determines which authentication method types the agent may include in its `InitializeResponse`". |
| ACP-EXT-203 (`requirements.py:1763`) **and** `test_extensibility.py:218` docstring | `#/$defs/ProtocolLevelNotification` | The "free to ignore" text now lives only in the root branch: `schema/v2/schema.unstable.json#/anyOf/2/properties/params/anyOf/0` (root `anyOf/2` is titled `ProtocolLevel` at target). This is positional; see the hazard below. Recommend pairing it with `docs/protocol/v2/draft/schema.mdx:2512-2520` ("Protocol Level" section: "...free to ignore the notification") and `docs/protocol/v2/draft/extensibility.mdx:165` ("Names starting with `$/` are reserved for protocol-level messages"). A name-stable alternative is `#/$defs/CancelRequestNotification`, but it does not carry the "free to ignore" sentence. |
| ACP-JSONRPC-001, ACP-JSONRPC-002 | `#/anyOf/3/items` | `schema/v2/schema.unstable.json#/$defs/AgentResponse`. Name-stable; `Result` and `Error` branches, both requiring `id`; `result` and `error` are disjoint. |
| ACP-BATCH-201 | `#/anyOf/{2,3,4,5}/minItems` | No replacement; the batch envelopes are gone. Defer to the transport/batch researcher (B1 inverts this row). |
| ACP-BATCH-207 | `#/anyOf/4/items` | Same as ACP-BATCH-201. |

**Pointers that still resolve but now mean something else.** `test_registry` cannot catch these:

| Row | Pointer | Base target | Target now resolves to |
|---|---|---|---|
| ACP-TRANSPORT-201 | `#/anyOf/2`, `#/anyOf/3` | `AgentBatchCall`, `AgentBatchResponse` | `ProtocolLevel`, `Proxy` |
| ACP-INFO-BATCH-202 | `#/anyOf/2`, `#/anyOf/3` | same | same |

Both rows' texts are batch-based and need re-deciding by the transport researcher. If ACP-TRANSPORT-201 survives as "every stdout line is a single JSON-RPC object", cite `schema/v2/schema.unstable.json#/anyOf` (every root branch is `type: object`) plus `transports.mdx:20,23,67`.

I checked every other positional pointer by comparing branch title and const between base and target. All still hit the same branch: `IdleStateUpdate/anyOf/{4,6,7}`, `ClientNotification/properties/params/anyOf/0/anyOf/0` (`CancelSessionNotification`), `ReplayFrom/anyOf/1`, `SystemPromptMode/anyOf/0`, `RequestPermissionOutcome/anyOf/2`.

Design idea (TCK-internal, not from any upstream source): have `test_registry` reject bare root positional pointers (`#/anyOf/<n>`), or require a `(Title)` annotation and assert it equals the branch's `title`. This would catch the silent re-targeting.

**ACP-SCHEMA-\* rows.**
- ACP-SCHEMA-001 (`#/anyOf`): still resolves and still means "the root message schema". No change is needed for this report's scope.
- ACP-SCHEMA-002 (`extensibility.mdx:95,226-233`): cannot become a pointer. "MUST NOT add any custom fields at the root of a type" is prose only; the schema declares no `additionalProperties: false` anywhere, and no `$def` description contains it. Target lines: `extensibility.mdx:104` (root-field ban) and `:233-240` (enum/tagged-union `_` rules). The carve-out the row describes is consistent with `extensibility.mdx:51-60` ("validate the fallback's required envelope fields"; a malformed *recognized* discriminator "MUST NOT fall through"). The code keeps this: a missing, `null` or unprefixed discriminator does not get the skip. The extensibility researcher owns the semantics.

**Rows citing `schema.mdx` lines.** `schema.mdx` is generated from schema descriptions, so each cited passage has a JSON source. But most method-level prose lives only in *positional* envelope branches, not in the named `$def`:

| Row | Base `schema.mdx` cite | Target `schema.mdx` lines | JSON source at target | Name-stable? |
|---|---|---|---|---|
| ACP-PROMPT-205 | 8397-8401 | 10193-10200 | `#/$defs/SubagentUpdate/description` | **Yes.** Recommend repointing to `schema/v2/schema.unstable.json#/$defs/SubagentUpdate/description` and dropping the `schema.mdx` cite; the row already cites `#/$defs/SubagentUpdate`. |
| ACP-CANCEL-201 | 461-465 | 603-607 | `#/$defs/ClientNotification/properties/params/anyOf/0/anyOf/0/description` (branch titled `CancelSessionNotification`) | No. Positional, and `$defs/CancelSessionNotification/description` lacks the MUST text. |
| ACP-CANCEL-202 | 473-475 | 615-617 | same branch | No |
| ACP-CANCEL-204 | 458-459 | 595-597 (text changed: "...of the cancelled foreground work as soon as possible") | same branch | No |
| ACP-FORK-201 | 614-624 | 754-770 | `#/$defs/ClientRequest/properties/params/anyOf/0/anyOf/10/description` (index was 9 at base) | No; the index already shifted |
| ACP-FORK-202 | 622-624 | 768-770 | same | No |
| ACP-AUTH-205 | 785 | 954 (now "`auth_required` (`-32000`)") | `#/$defs/ClientRequest/properties/params/anyOf/0/anyOf/7/description` (index was 6 at base) | No; the index already shifted |

**DECISION NEEDED (recommendation):** keep `schema.mdx` line citations for the CANCEL/FORK/AUTH-205 rows and let `spec-impact --fix` remap them. Repointing to positional `ClientRequest`/`ClientNotification` branches would swap a remappable line citation for a pointer that silently re-targets whenever a method is inserted. This range already moved `session/new` from index 6 to 7 and `session/fork` from 9 to 10. Repoint only ACP-PROMPT-205.

`schema.mdx` grew by 3495 lines, so verify that `--fix` lands on the target lines above. The semantic re-judging of CANCEL-204's changed text belongs to the cancellation researcher.

**ACP-CLIENTCAP-202's `schema/v2/meta.unstable.json:31-37`** is matched by spec-tracker's `_LINE_REF` regex (`spec-tracker/src/spec_tracker/citations.py:67-70`; also `spec-tracker/tests/test_citations.py:40,48`). It was already wrong at base: the base file has 31 lines, and `clientMethods` is at `21-27`. Replace it by hand with `schema/v2/meta.unstable.json:28-35` (clientMethods) plus `:36-38` (protocolMethods). Do not trust a mechanical remap of an out-of-range citation. The `test_citations.py` fixture string that mentions it is a parser test and need not change.

### Task 5: fixtures vs tightened constraints (B5-B10)

**Empirical result:** I ran `tests/v2/test_cli.py` (103 tests) against the target schema and meta, with today's code and fixtures, in a scratch copy (`/tmp/v2chk/repo`, run with `PYTHONPATH` pointing at the copy). The result was **103 passed** in 528.99s. No fixture's expected FAIL/PASS set changes because of the schema alone.

Static confirmation per item (`rg` over `tests/fixtures/agents/v2/`):

| Item | Fixtures emitting the shape | Verdict |
|---|---|---|
| B5 `AvailableCommand.type` required | none (no `availableCommands` / `available_commands_update` anywhere) | no fix |
| B6 `ElicitationSchema` requires `type`/`properties`; scope `oneOf` | `calls_elicitation_unadvertised.py:26-32` sends url-mode with `sessionId` only and no `requestedSchema` | Valid at target (probe `[]`). `ElicitationSessionScope` requires `sessionId` and `ElicitationRequestScope` requires `requestId`, so exactly one matches. |
| B7 `PromptRequest.prompt` minItems 1 | client-side; the TCK never sends `prompt: []` (`rg`) | n/a |
| B7 select `options` / group minItems 1 | `config_set_omits_changed_option.py:27-31`, `conforming_full.py:55-59`: three options each | no fix |
| B8 `ToolCallLocation.line` >= 1, `ResourceLink.size` >= 0 | none emit `locations` or `size`; the TCK's own `resource_link` (`test_prompt.py:238`) has no `size` | no fix |
| B9 (loosened) | n/a | no fix |
| B10 `SessionMessageChunk` sender/recipient ids, `SessionInfo.additionalDirectories` null | none (`rg senderSessionId`, `additionalDirectories` only as a capability marker in `conforming_full.py:43`) | no fix |

The only fixture-adjacent breakage at target is the unit tests:
- `tests/v2/test_registry.py::test_schema_citation_pointers_resolve_in_the_vendored_schema`: the Task 4 pointers.
- `tests/v2/test_validation.py::test_enum_sets_match_the_schema`: `paused`, `session`.

65 of 67 `tests/v2` unit tests pass at target. Batch-related unit tests (`test_validation.py:29-48`) still pass at target only because the batch code path is hand-written. They become wrong once Task 1's carve-out 1 is removed.

### Task 6: the TCK's own probe traffic against the new reservations

Target `docs/protocol/v2/draft/extensibility.mdx`:
- `:97-100`: `traceparent`, `tracestate` and `baggage` are reserved root `_meta` keys. "When present, their values **MUST** use the corresponding W3C format." At base this was a SHOULD-reserve with no format MUST (base `:89`).
- `:102`: "Other unprefixed `_meta` keys, and keys whose prefix has `agentclientprotocol` as its second label..., are reserved for ACP. ... Extension keys **SHOULD** use a reverse-DNS prefix the implementer controls."
- `:165` (new): "Names starting with `$/` are reserved for protocol-level messages ..., and all other names are reserved for ACP." The `_` prefix is reserved for custom extensions.
- `:259`: naming convention `com.example/<name>` for `_meta` keys and `_com.example/<name>` for custom methods and enum values ("follow MCP's naming convention"; no RFC keyword).

Findings:

| TCK traffic | Where | Status at target |
|---|---|---|
| `_meta: {"traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01", ...}` | `test_extensibility.py:76-78` (ACP-META-001) | **OK.** A valid W3C `traceparent` (version `00`, 32-hex trace-id, 16-hex parent-id, 2-hex flags), so it meets the new MUST. |
| `_meta: {..., "tck": true}` | `test_extensibility.py:78` (ACP-META-001); `test_cancel.py:326` (ACP-CANCEL-206, via `_helpers.py:926-927`) | **Uses an ACP-reserved key** (`:102`) and misses the reverse-DNS SHOULD. The TCK does **not** hold agents to this rule: ACP-META-201 checks only that `_meta` is an object or null (`test_extensibility.py:95-125`), and no test inspects `_meta` key names. So the TCK is not breaking a rule it enforces, but it is sending a key it has no right to define. Recommendation: rename to a reverse-DNS key the project controls. The project owner picks the domain; I did not find one in upstream sources. |
| `$/does_not_exist` notification | `test_extensibility.py:222` (ACP-EXT-203) | Sends a name in the `$/` reserved space (`:165`). No MUST forbids this. It is a deliberate probe that simulates a future protocol-level message, and that is the only way to observe EXT-203. Defensible; maybe note the intent in the test docstring. CLIENTCAP-202 would FAIL an *agent* that sent an undefined `$/` method, so mention this asymmetry when the docstring is touched. |
| `_tck/does_not_exist`, `_tck/unknown`, `_tck/ping`, `_tck/notify`, `_tck/notify_only`, enum `_tck/unknown`, cursor `_tck_unsupported_cursor` | `test_jsonrpc.py:33`, `test_extensibility.py:47,136`, `test_diagnostics.py:25`, `test_enums.py:193`, `test_batch.py:53,85,302`, `test_session_capabilities.py:352`, `test_transport.py:43` | **OK** under the MUST-level rule (`_` prefix, `:165`, `:237`). They do not follow the `:259` `_com.example/<name>` convention, which is not RFC-keyworded. Optional rename. |
| Fixture `_meta: {"tags": [...]}` | `tests/fixtures/agents/v2/message_split_across_multiple_lines.py:18` | Agent-side unprefixed key, and the fixture is non-conforming by design anyway. Cosmetic; no test checks it. |

## Testability notes

- Root-array rejection, null-id-on-result and request-id type are all observable on stdout and can be asserted with the existing validation entry points once tightened. Which requirement id carries each (TRANSPORT-201, JSONRPC-002, SCHEMA-001, or new) is for the transport/JSON-RPC researcher.
- A conforming agent at target never writes `[`-prefixed lines and never uses `id: null` except on an error for an undeterminable request. A non-conforming fixture for item 3 would send `session/request_permission` with `id: null`. No current fixture does this.
- The pointer-hazard check (positional root pointers) is a registry meta-test idea, not an agent requirement.

## Discrepancies

- **Registry vs spec (pre-existing):** the ACP-CLIENTCAP-202 citation `meta.unstable.json:31-37` did not match the base file (clientMethods `21-27`). At target it is `28-35`.
- **TCK vs target schema:**
  - `validation.py:202` claims `RequestId` includes `null`; the target says it MUST NOT.
  - The `validation.py:8-13` batch claim contradicts `transports.mdx:65-67` and the root `anyOf`.
- Spec docs, schema and changelog otherwise agree on everything checked here (direction annotations, the RequestId change, the reserved `_meta` keys).

## Open questions

1. Must `auth/status_update` be gated on the agent advertising `auth.status` (`overview.mdx:260`)? If so, an agent emitting it without the capability should FAIL something. At target, CLIENTCAP-202 accepts it. Route to the authentication researcher.
2. New observable MUST at `extensibility.mdx:97`: agent-emitted `traceparent`/`tracestate`/`baggage` values must be W3C-formatted. Candidate requirement for the extensibility researcher; not proposed here, to avoid duplication.
3. Which reverse-DNS prefix should the TCK use for its own `_meta` keys (and optionally its custom methods)? Project-owner decision.
4. Batch redesign (carve-out 1, BATCH-*, TRANSPORT-201, INFO-BATCH-202, the `_helpers.py` array unwrapping, and the `test_validation.py:29-48` batch unit tests): owned by the transport/batch researcher. This report only establishes that validation does not depend on root positions and that the array path is now wrong.
