# v2 impact: `overview.mdx` (core sections) and `error.mdx` (new Errors page), `beac4ba` -> `3961af9`

**Sources checked:** agent-client-protocol spec checkout `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2` (not pulled, per brief), base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a`. Rust SDK `e75d6f19fabb97d389fd471e89b093bbb50ba547` (2026-11-09, pulled, already current). Python SDK `8a9940744d0afa0bb3d71b4e4df8f843b061bccf` (2026-11-09, pulled, already current). A2A TCK was not consulted.
**Confidence:** high for what the spec now says and for which rows break. Medium for the tier recommendations on the three INFORMATIONAL rows: the new page covers some of their premises but not all, and the SDKs only partly agree.

All target line numbers below are `@ 3961af94fa62`. "ov" = `docs/protocol/v2/draft/overview.mdx`, "err" = `docs/protocol/v2/draft/error.mdx`, "schema" = `schema/v2/schema.unstable.json`.

## Answer

`error.mdx` used to be a stub ("_Documentation coming soon_", base lines 1-6). It is now a normative page (err:1-68). Four things it adds directly hit the registry:

1. **Unknown session.** A session-scoped request naming a session that does not exist or is not active **MUST** get `-32002`, with `data.sessionId` set to the requested ID (err:54-56). This settles the premise of `ACP-INFO-UNKNOWNSESSION-001`, so that row should be retired and replaced by a CAPABILITY row.
2. **Unknown methods.** An unimplemented method, or a capability-gated method the agent did not advertise, **MUST** get `-32601` (err:44). `extensibility.mdx:202` now also says MUST. So `ACP-JSONRPC-004`'s "Spec wording is still 'should'" is false, and the unadvertised-standard-method case is a new observable rule.
3. **Parse and invalid-request errors.** The page now defines what `-32700` and `-32600` mean (err:28-29). It still states no receiver MUST for a non-JSON or non-envelope line, and the client is forbidden to send one (`transports.mdx:24`). So `ACP-INFO-PARSE-001` and `ACP-INFO-INVALIDREQ-001` can stay INFORMATIONAL, but their "still a stub" wording and citations are wrong.
4. **Typed error data.** `Error.data` is now `ErrorData | null` (`schema#/$defs/Error`, `#/$defs/ErrorData`). The `Other` fallback accepts any value, so the schema-level check of `ACP-ERROR-001` is unchanged, but its "byte-identical to v1" claim is false.

In `overview.mdx`, "Communication Model" now says request IDs **MUST** be a string or integer, never `null`. An error response may have `id: null` only when the ID could not be determined, and a sender **MUST NOT** reuse an ID that is still pending (ov:15-19). The batch paragraph is replaced by "ACP does not use batches" (ov:21). Every overview line the registry cites has moved, by +30 lines.

Two schema pointers are now dangling. `ACP-JSONRPC-001` and `ACP-JSONRPC-002` cite `schema#/anyOf/3/items`, but `anyOf/3` is now the `Proxy` branch and has no `items`, so `tests/v2/test_registry.py` will fail. The batch halves of `ACP-JSONRPC-001/003/005` must go with B1.

The v2 tests' asserted error codes all match the new code table. The one inconsistency is in the fixtures: `tests/fixtures/agents/v2/_base.py:484-485` answers an unknown `sessionId` on `session/prompt` with `-32602`, which is non-conforming at target. `error.mdx` should become a core doc in `spec-tracker/maps/v2.toml`.

## Summary table

| id | classification | one-line note |
|---|---|---|
| ACP-JSONRPC-001 | changed text + citation | Drop the batch half (B1). Repoint the dangling `#/anyOf/3/items` to `#/$defs/AgentResponse`, plus `#/$defs/RequestId` (whose description now says the receiver "MUST reply with the same value") and ov:15-17. MANDATORY unchanged. |
| ACP-JSONRPC-002 | changed text + citation | Repoint the dangling pointer. Add the id typing rule: a result `id` is a string or integer, never null. An error `id` may also be null (B4). Overview 195-196 -> 225-226. Add err:6-10. Validation must change. |
| ACP-JSONRPC-003 | changed text + citation | Drop "including a notification inside a batch". The ACP MUST it cited (`transports.mdx:76-79`, base) was deleted with the batch section, so the basis is now ov:227 plus JSON-RPC 2.0 via ov:10. MANDATORY unchanged. |
| ACP-JSONRPC-004 | changed tier (not assigned to me, but err:44 hits it) | **DECISION NEEDED:** now MUST in both err:44 and extensibility.mdx:202. Recommend retiring it for a new MANDATORY `ACP-JSONRPC-201`. Coordinate with the extensibility researcher. |
| ACP-JSONRPC-005 | changed text + citation | Drop "including an invalid or empty batch". ov:191-197 -> ov:221-229. Still ADVISORY: no statement anywhere says the connection must survive. |
| ACP-ERROR-001 | changed text + citation | Remove the "byte-identical to v1" claim. Add err:6-10. ov:193-197 -> ov:221-229. Stays ADVISORY. Only the test docstring changes. |
| ACP-LIST-204 | citation-only (overview part), meaning widened | ov:188 -> ov:218. The rule now adds "native syntax of the Agent's machine, not URIs". The `os.path.isabs` assertion already rejects URIs. An optional text tweak is suggested. |
| ACP-EXT-001 | citation-only (overview part) | ov:193 -> ov:223. |
| ACP-CANCEL-205 | citation-only (overview part) plus one removed citation | ov:197 -> ov:227. `transports.mdx:78-79` (base) was batch text and is deleted, so drop it. The schema pointer still resolves to `CancelSessionNotification`. |
| ACP-INFO-UNKNOWNSESSION-001 | **retired** -> new `ACP-ERROR-201` | **DECISION NEEDED** (recommend retiring). err:54-56 makes the unknown-session `-32002` + `data.sessionId` a MUST. |
| ACP-INFO-PARSE-001 | changed text + citation, tier kept | **DECISION NEEDED** (recommend keeping INFORMATIONAL). The "still a stub" claim is false. Cite err:28 and transports.mdx:24. Optionally add ADVISORY `ACP-ERROR-204`. |
| ACP-INFO-INVALIDREQ-001 | changed text + citation, tier kept | **DECISION NEEDED** (recommend keeping INFORMATIONAL). Cite err:29 and transports.mdx:24. The SDKs disagree: Rust answers `-32600`, Python stays silent. |
| new ACP-JSONRPC-201 | new (replaces 004) | MANDATORY: an unknown `_`-prefixed method gets `-32601`. |
| new ACP-JSONRPC-202 | new | MANDATORY: every agent-authored request's `id` is a string or integer, never null, and is not reused while pending. |
| new ACP-ERROR-201 | new (replaces INFO-UNKNOWNSESSION-001) | CAPABILITY `capabilities.session`: `-32002` + `data.sessionId` for a session-scoped request on a never-created or closed session. |
| new ACP-ERROR-202 | new | MANDATORY: a standard capability-gated method the agent did not advertise gets `-32601`. |
| new ACP-ERROR-203 | new | ADVISORY: error codes in the reserved ranges are only the ones ACP defines. |
| new ACP-ERROR-204 | new, optional | ADVISORY, conditional: if the agent answers a non-JSON line, the answer is `-32700` with `id: null`. |
| ledger x5 | new non-requirements | See "Ledger entries". |

## Requirements

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| 1 | Request IDs are a string or an integer, never `null`. Error responses use `id: null` only when the request ID could not be determined. | MUST | ov:15-17; `schema#/$defs/RequestId`; `schema#/$defs/AgentResponse/anyOf/1/properties/id` |
| 2 | A sender must not reuse an ID while a request with that ID is still awaiting a response. | MUST | ov:19; `schema#/$defs/RequestId` (description) |
| 3 | The receiver replies with the same `id` value. | MUST | `schema#/$defs/RequestId` (description); ov:233 (envelope follows JSON-RPC 2.0) |
| 4 | A success has `result`, an error has `error` with `code` and `message`, and notifications never get a response. | MUST (JSON-RPC 2.0 by reference) | ov:223-227; err:6-10 |
| 5 | Unknown method, or a capability-gated method not advertised, gets `-32601` (custom and standard alike). | MUST | err:44; extensibility.mdx:202 |
| 6 | Receivers ignore unknown notifications. | SHOULD | err:44; extensibility.mdx:231 |
| 7 | A session-scoped request for a non-existent or non-active session gets `-32002` with `data.sessionId` set to the requested ID. Applies to `session/prompt`, `session/set_config_option`, and `session/resume` of a non-existent or deleted session. | MUST (capability: `capabilities.session`; set_config_option only where config options are advertised) | err:54-56; session-setup.mdx:47,51; `schema#/$defs/SessionNotFoundErrorData` |
| 8 | `session/close` of a non-existent or non-active session, and `session/delete` of a non-existent one, still succeed. | SHOULD (capability) | err:56; session-setup.mdx:407-410 |
| 9 | Requests other than `initialize` before init get `-32600`, and notifications are ignored. A repeated `initialize` after another request gets `-32600`. | MUST | err:58-60; initialization.mdx:90 (owned by the initialization audit) |
| 10 | Implementation-specific error codes avoid -32768..-32000 and -32899..-32800. | SHOULD | err:38 |
| 11 | Receivers treat an unrecognized error code as a generic failure. | MUST (receiver-side; see ledger) | err:38 |
| 12 | `-32022` data is `UnsupportedProtocolVersionErrorData {requested, supported}`. | MUST (owned by the initialization audit) | `schema#/$defs/UnsupportedProtocolVersionErrorData`; initialization.mdx:112 |
| 13 | File paths are absolute, in the native syntax of the agent's machine, and are not URIs. | MUST | ov:218 |
| 14 | An agent with a non-empty `authMethods` implements both `auth/login` and `auth/logout`. | MUST (capability: inferred `authMethods`) | ov:60 (owned by the authentication audit) |

## Details

### Exact target line map, overview.mdx (base -> target)

| Content | base | target |
|---|---|---|
| "Communication Model" heading (not sentence-cased) | 8 | 8 |
| RequestId non-null, error `id: null` | (new) | 15-17 |
| no ID reuse while pending | (new) | 19 |
| no batches (was "ACP follows JSON-RPC 2.0 batch behavior") | 15-17 | 21 |
| Agent > Baseline methods: `authMethods` / `auth/*` rule | 56 | 60 |
| Agent > Optional methods (`session/set_config_option`, `session/delete`) | (new) | 124-143 |
| Request cancellation (`$/cancel_request`) | (new) | 212-214 |
| absolute paths | 188 | 218 |
| line numbers 1-based | 189 | 219 |
| Error handling section | 191-197 | 221-229 |
| "All methods follow standard JSON-RPC 2.0 error handling" | 193 | 223 |
| result / error bullets | 195-196 | 225-226 |
| notifications never receive responses | 197 | 227 |
| link to Errors page | (new) | 229 |
| envelope fields follow JSON-RPC 2.0 | 201 | 233 |
| omit vs `null` equivalence | (new) | 235 |
| enum fallbacks | 203 | 237 |

Wording change at ov:60. The base said an agent returning "one or more **valid** entries in `authMethods`" MUST implement both auth methods. The target says "a **non-empty** `authMethods` list". So an agent listing only unknown-type entries is now also bound. The target also adds "The `session/*` methods require `capabilities.session`."

### error.mdx at target (whole page)

- err:6-10: the error object is `code` (integer), `message` ("a short human-readable description"), and optional `data` "whose shape depends on the code". Example at err:12-22 is `-32002` with `data: {sessionId}`.
- err:26-36: code table with -32700, -32600 (adds "a request other than `initialize` arrived before initialization, or `initialize` was repeated after another request"), -32601, -32602, -32603, -32800, -32000, -32002, -32022.
- err:38: unrecognized code -> generic failure (MUST). Reserved ranges for implementation-specific codes (SHOULD).
- err:42-44 Unknown methods. err:46-50 Invalid parameters. err:52-56 Unknown sessions. err:58-60 Requests before initialization. err:62-68 Unstable features (`session/fork`, `session/status`, `session/archive`/`unarchive`, `session/set_title` use `-32002`; `providers/*` without the capability get `-32601`).

### Schema changes relevant here

- `#/$defs/RequestId`: `anyOf` was `[null, int64, string]` and is now `[int64, string]`. The description now carries the "MUST NOT be null", echo-MUST and no-reuse-MUST text.
- `#/$defs/AgentResponse/anyOf/0/properties/id` (Result): `$ref RequestId`, so non-null. `#/$defs/AgentResponse/anyOf/1/properties/id` (Error): an inline `anyOf [int64, string, null]`. Both branches require `id`. `ClientResponse` is the same.
- `#/$defs/Error/properties/data`: was untyped and is now `anyOf [ErrorData, null]`. `#/$defs/ErrorData` is `anyOf [UnsupportedProtocolVersionErrorData, SessionNotFoundErrorData, {title: Other}]`. The unconstrained `Other` branch means **schema validation accepts any `data`**, so the `data.sessionId` MUST is a doc-only rule the TCK must check by hand.
- `#/$defs/SessionNotFoundErrorData`: `{sessionId: SessionId (required), _meta?}`.
- `#/$defs/UnsupportedProtocolVersionErrorData`: `{requested: ProtocolVersion, supported: ProtocolVersion[] (both required), _meta?}`.
- `#/$defs/ErrorCode`: same constants. The descriptions changed: `-32002` is now "such as a session" instead of "such as a file", and `-32022` now names its data type. `ErrorCode` is already a core `$def`.
- Root `anyOf`: was 7 entries and is now 4 (`Agent`, `Client`, `ProtocolLevel`, `Proxy`). Any `#/anyOf/N` citation needs review: `#/anyOf/3/items` no longer resolves, and `#/anyOf/2` and `#/anyOf/3` now resolve to different things. `ACP-TRANSPORT-201` is affected the same way (transports audit).

### Per-row details

**ACP-JSONRPC-001** (MANDATORY, `src/tck/v2/requirements.py:731-744`)
- Text proposed: "A response's `id` echoes the request `id` exactly (integer and string ids), whether it is a result or an error."
- Citation proposed: `docs/protocol/v2/draft/overview.mdx:15-17,233; schema/v2/schema.unstable.json#/$defs/RequestId; schema/v2/schema.unstable.json#/$defs/AgentResponse`.
- Test: `test_jsonrpc.py:36-54` still matches unchanged. Remove the `ACP-JSONRPC-001` marker from `test_batch.py:196` (the batch test is retired under B1 by the transports audit).
- Fixture: `wrong_id_echo.py` is still valid.

**ACP-JSONRPC-002** (MANDATORY, `:745-755`)
- Text proposed: "A response carries exactly one of `result`/`error` and an `id` that is a string or integer. Only an error response may carry `id: null`. An error object has an integer `code` and a string `message`."
- Citation proposed: `overview.mdx:15-17,225-226; error.mdx:6-10; schema#/$defs/AgentResponse`.
- Validation: `tck.v2.validation._is_valid_request_id` (`validation.py:201-205`, docstring "same as v1") must reject `None` for result responses. `validate_response_envelope` (`:314-347`) must apply null-only-on-error. The test itself (`test_jsonrpc.py:64-83`) needs no change.
- Side effect to check: `answers_notifications.py:23` and `pushes_status_and_answers_notifications.py:24` write `{"id": null, "result": null}`. That is now invalid both for its `id` and for `result: null`. If any test validates unsolicited agent lines through `validate_agent_message`, those fixtures' expected FAIL sets in `tests/v2/test_cli.py` may grow beyond `ACP-JSONRPC-003`. Easiest fix: make them reply with `{"id": null, "error": {...}}`, which is still a response to a notification and still trips only `ACP-JSONRPC-003`.

**ACP-JSONRPC-003** (MANDATORY, `:756-768`)
- Text proposed: "Notifications never receive a response, success or error. Messages the agent itself initiates (they carry `method`) are not responses."
- Citation proposed: `overview.mdx:10,227; error.mdx:44` (the base `transports.mdx:76-79` "MUST NOT reply to a Notification" text is gone).
- Tier stays MANDATORY. ov:227 states it flatly, and ov:10 incorporates JSON-RPC 2.0 §4.1 ("The Server MUST NOT reply to a Notification"). This is now an inherited MUST, not an ACP-worded one.
- Tests: remove the marker from `test_batch.py:74`. `test_jsonrpc.py:86-102` is unchanged.

**ACP-JSONRPC-005** (ADVISORY, `:776-787`)
- Text proposed: "After an erroneous request the connection remains usable." Whether a JSON-array line counts as "erroneous request" evidence is for the transports audit.
- Citation: `overview.mdx:221-229` plus its extensibility half (other owner).
- Remove the `test_batch.py:125` marker if the batch test is retired. `test_jsonrpc.py:121-140` is unchanged.

**ACP-ERROR-001** (ADVISORY, `:1767-1777`)
- Text proposed: "A JSON-RPC error's `message` is a non-empty, single-line string, and its optional `data` is well-formed JSON."
- Citation proposed: `schema#/$defs/Error; error.mdx:6-10; overview.mdx:221-229`.
- Basis for ADVISORY: `#/$defs/Error/properties/message` says "should be limited to a concise single sentence", and err:9 says "a short human-readable description". No MUST, so the tier is unchanged.
- Test: update the `test_diagnostics.py:17` docstring ("`error.mdx` is still a stub").
- Observation: the test sends `session/new` with `{}` whether or not `capabilities.session` is advertised. At target, a session-less agent MUST answer `-32601` (err:44). That is still an error with a message, so the test stays valid.

**ACP-LIST-204** (CAPABILITY, `:1103-1110`)
- Overview half: `:188` -> `overview.mdx:218`. The session-list half is not mine; `session-list.mdx:119` at target says "Always an absolute path."
- Optional text tweak: "...is an absolute path in the agent's native syntax (not a URI)". `os.path.isabs` on the TCK host (the same machine as the stdio agent) already returns False for `file:///...`, so the test needs no change.

**ACP-EXT-001** (MANDATORY, `:1677-1690`): overview half `:193` -> `:223`. The extensibility half is not mine, but note that extensibility.mdx:187 now has "MUST respond accordingly with the provided `id`".

**ACP-CANCEL-205** (CAPABILITY, `:557-570`): `overview.mdx:197` -> `:227`. Drop `transports.mdx:78-79` (deleted batch text). Optionally add `session-setup.mdx:51` ("Agents ignore `session/cancel` for a session that isn't active"). The `test_cancel.py:293` docstring "Batch elements are checked individually" is harmless but stale.

**ACP-INFO-UNKNOWNSESSION-001** (INFORMATIONAL, `:517-527`): **retire. DECISION NEEDED** (recommend retiring). Its stated premise ("error code (if any) is unspecified") is false at target. It is replaced by `ACP-ERROR-201`, with a new id because the tier changes, per the `requirements.py:7-13` convention. `tests/v2/test_cli.py:467` asserts its PASS for `conforming_full.py` and must move to `ACP-ERROR-201`.

**ACP-INFO-PARSE-001** (INFORMATIONAL, `:1815-1824`)
- **DECISION NEEDED. Recommend keeping it INFORMATIONAL**, for three reasons:
  - err:28 only defines what `-32700` means. There is no ACP MUST to reply.
  - The probe itself breaks a client MUST NOT (`transports.mdx:24`: "The client MUST NOT write anything to the agent's stdin that is not a valid ACP message").
  - The schema says `id: null` is "such as for a parse error" (`#/$defs/AgentResponse/anyOf/1/properties/id`), which describes the shape if a reply is sent.
- Text proposed: "Behaviour on a malformed (non-JSON) stdin line is recorded, never asserted. err:28 defines `-32700` for this case and the schema allows `id: null` for it, but no rule obliges a reply, and the probe itself violates the client-side `transports.mdx:24`."
- Citation: `error.mdx:28; transports.mdx:24; schema#/$defs/AgentResponse`.
- Both SDKs reply with `-32700` and `id: null` and keep the connection open: Rust `src/agent-client-protocol/src/jsonrpc/transport_actor.rs:9-24`, test `tests/jsonrpc_error_handling.rs:270-327`; Python `src/acp/_jsonrpc.py:9-15,27-28`, `src/acp/_transport.py:71-79`. That agreement supports the optional conditional ADVISORY `ACP-ERROR-204` below.

**ACP-INFO-INVALIDREQ-001** (INFORMATIONAL, `:1825-1836`)
- **DECISION NEEDED. Recommend keeping it INFORMATIONAL**: the same client-MUST-NOT premise applies, and the SDKs disagree. Rust answers `{"foo":"bar"}` with `-32600` and `id: null` (`transport_actor.rs:34-41` plus `incoming_actor.rs:406-407`, which answers anything that is not response-shaped). Python's `Connection._process_message` (`src/acp/connection.py:159-181`) drops a message with no `method` and no `id` silently.
- Text: replace "still 'Documentation coming soon'" with "err:29 defines `-32600` for this case, but no rule obliges a reply, the probe violates `transports.mdx:24`, and reference SDKs disagree (reply vs. silence)".
- Citation: `error.mdx:29; transports.mdx:24`.

**ACP-JSONRPC-004** (ADVISORY, `:769-775`; cites extensibility only)
- **DECISION NEEDED.** Its text "Spec wording is still 'should'" is false: base extensibility said "should respond", while target extensibility.mdx:202 says "**MUST** respond with the standard 'Method not found' error", and err:44 repeats it.
- Recommend retiring it and adding `ACP-JSONRPC-201` (MANDATORY, same test `test_jsonrpc.py:105-118`). The `pytest.skip` on no-reply can stay, since replying at all is `ACP-EXT-001`.
- Coordinate with whoever audits extensibility.mdx so only one of you proposes it.

### Proposed new requirements

**ACP-JSONRPC-201**
- Tier: MANDATORY (replaces ACP-JSONRPC-004).
- Text: "An unknown `_`-prefixed method request receives a `-32601` (Method not found) error."
- Citation: `docs/protocol/v2/draft/error.mdx:44; docs/protocol/v2/draft/extensibility.mdx:202 @ 3961af94fa62`.
- Observation: the existing `_tck/does_not_exist` probe.
- Fixture: the existing `unknown_method_no_error.py`. Its expectation moves from a 004 FAIL to a 201 FAIL, and the verdict flips to NOT CONFORMANT.

**ACP-JSONRPC-202**
- Tier: MANDATORY. Gate: none (connection-level). It SKIPs when the agent sends no request during the test.
- Text: "Every request the agent sends to the client has an `id` that is a string or an integer, never `null`, and the agent never reuses an `id` while an earlier request with it is still awaiting the client's response."
- Citation: `docs/protocol/v2/draft/overview.mdx:15-19 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/RequestId`.
- How a client TCK observes it:
  - Passively, on agent -> client requests (`session/request_permission` in the permission and cancel tests, and anything `run_prompt` records).
  - The id-type half is a validation addition: `tck.v2.validation`'s request path (`validation.py:281-312`) never checks `id` today.
  - The reuse half needs at least two overlapping agent requests. The TCK can hold one permission request unanswered, as `ACP-CANCEL-209` does, but an agent only sends a second one when it chooses to. Expect mostly SKIPs from real agents.
- Alternative: register only the id-type half and ledger the reuse half (see ledger). Recommend registering both halves under one id with an explicit SKIP reason.
- Fixtures: `asks_permission_null_id.py` (an `AsksPermissionAgent` that sends `id: null`); optionally `asks_permission_reused_id.py` (two overlapping permission requests sharing an id).

**ACP-ERROR-201**
- Tier: CAPABILITY, gate `capabilities.session`. Replaces ACP-INFO-UNKNOWNSESSION-001.
- Text: "A `session/prompt` naming a session that does not exist, or one that was closed on this connection, is answered with `-32002` whose `data.sessionId` equals the requested `sessionId`."
- Citation: `docs/protocol/v2/draft/error.mdx:54-56; docs/protocol/v2/draft/session-setup.mdx:49-51 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/SessionNotFoundErrorData`.
- Observation: two probes, (a) prompt `tck-does-not-exist`, as the current INFORMATIONAL test already does, and (b) `session/new` -> `session/close` -> `session/prompt` on that id. Check `error.code == -32002` and `error.data.sessionId == requested`. An auth-gated agent is handled by creating a session first, as today.
- Extension probes, possibly on the same id or split out (an orchestrator call; flag the overlap with the session-setup and session-config audits):
  - `session/resume` of a never-created id, also MUST via err:56 and session-setup.mdx:47.
  - `session/set_config_option` on an unknown session, only when some session advertised `configOptions`.
- Fixture changes:
  - `_base.py:484-485` must answer `-32002` with `data: {"sessionId": ...}`, which needs a `data` argument on `_error` (`_base.py:686`).
  - `_base.py`'s resume "deliberately accepts any `sessionId`" (comment at `:482-483`) would fail the resume extension probe.
  - `_base.py:417-418` answers fork of an unknown source with `-32602`, but err:64 says `-32002`. That belongs to the fork audit.
  - Add a defect fixture, `unknown_session_invalid_params.py` (keeps today's `-32602`), and optionally `unknown_session_no_data.py` (`-32002` without `data`).

**ACP-ERROR-202**
- Tier: MANDATORY. Gate: none; it is conditional on *non*-advertisement, so each probe SKIPs when the corresponding capability is advertised.
- Text: "A standard ACP method gated on a capability the agent did not advertise is answered with `-32601`."
- Citation: `docs/protocol/v2/draft/error.mdx:44,68; docs/protocol/v2/draft/overview.mdx:60,141-142 @ 3961af94fa62`.
- Observation: safe probes, each sent only when the agent did not advertise the gate:
  - `session/new` (gate `capabilities.session`);
  - `session/delete` with a bogus id (gate `capabilities.session.delete`);
  - `session/fork` (gate `session.fork`);
  - `providers/list` (gate `providers`).
- Do **not** probe `auth/*`: its gate is `authMethods`, not a capability, and calling it is a client MUST NOT (ov:60).
- Fixture impact: `conforming.py` advertises only `{"session": {}}`, but `_base.py:225-226` answers `session/delete` anyway. The base must gate `session/delete` on `session.delete` the way it gates fork (`:227`). Add defect fixture `answers_unadvertised_delete.py`. `no_session_capability.py` already conforms for the `session/new` probe.

**ACP-ERROR-203**
- Tier: ADVISORY.
- Text: "Every error `code` the agent returns that falls in -32768..-32000 or -32899..-32800 is one ACP defines (`ErrorCode` constants)."
- Citation: `docs/protocol/v2/draft/error.mdx:38 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/ErrorCode`.
- Observation: check the error responses the TCK already provokes. Cheapest: the `ACP-ERROR-001` probes plus the ERROR-201/202 probes.
- Caveat: the reserved range may gain future ACP codes; that is acceptable for an ADVISORY row.
- Fixture: `reserved_range_custom_code.py` (answers the unknown method with `-32050`). That also trips JSONRPC-201, so use a different trigger, for example the invalid-params `session/new`.

**ACP-ERROR-204** (optional; DECISION NEEDED, lean yes)
- Tier: ADVISORY, conditional. It SKIPs when the agent is silent or exits.
- Text: "If the agent answers a non-JSON stdin line, the answer is a single error response with `code: -32700` and `id: null`."
- Citation: `docs/protocol/v2/draft/error.mdx:28 @ 3961af94fa62; schema/v2/schema.unstable.json#/$defs/AgentResponse` (Error branch `id` description).
- Observation: the existing `ACP-INFO-PARSE-001` probe, bound to both ids.
- Fixture: `parse_error_wrong_code.py` (answers `-32600` or a non-null id). `noisy_stderr_and_parse_error_reply.py` already PASSes it.

### Ledger entries (new deliberate non-requirements)

1. `docs/protocol/v2/draft/error.mdx:38 @ 3961af94fa62`
   - Statement: Receivers MUST treat an unrecognized error code as a generic failure.
   - Reason: unobservable. As a receiver, the agent sees only the mock client's own error replies, and "treated as a generic failure" has no wire signal beyond liveness.
2. `docs/protocol/v2/draft/overview.mdx:60 @ 3961af94fa62`
   - Statement: If `authMethods` is omitted or empty, Clients MUST NOT call `auth/login` or `auth/logout`.
   - Reason: client-side rule (the TCK obeys it itself; see `--auth-method`).
3. `docs/protocol/v2/draft/error.mdx:56 @ 3961af94fa62`
   - Statement: Clients SHOULD treat a `-32002` response to `session/close` or `session/delete` as success.
   - Reason: client-side rule. The agent-side SHOULD on the same line is `ACP-DELETE-203`, plus a possible new close row (see Open questions).
4. `docs/protocol/v2/draft/overview.mdx:235 @ 3961af94fa62`
   - Statement: For an optional field whose schema allows `null`, omitting it and sending `null` are equivalent.
   - Reason: out of scope as a generic probe. Receiver-side equivalence is covered field by field (`ACP-RESUME-203`, `ACP-SESSION-203`). The sender-side "omit rather than send null" is enforced by schema validation of agent output.
5. (Only if the orchestrator prefers not to register the reuse half of `ACP-JSONRPC-202`.) `docs/protocol/v2/draft/overview.mdx:19 @ 3961af94fa62`
   - Statement: A sender MUST NOT reuse an ID while a request with that ID is still awaiting a response.
   - Reason: mostly unobservable. It needs the agent to have two requests outstanding at once, which a client cannot force.

### Asserted error codes in `src/tck/v2/conformance/` vs the new page

Checked with grep over every `*_ERROR`/`-32xxx` use:

- **Consistent with the new page:**
  - `-32601`: `test_jsonrpc.py:118` and `test_authentication.py:179`, against err:30,44.
  - `-32800`: `test_cancel.py:143,198,373` and `test_session_capabilities.py:607`, against err:33 and cancellation.mdx:59.
  - `-32022` / `-32602` in `test_initialize.py`, against err:31,36 and initialization.mdx:108-112. The `_unsupported_version_data_issues` checks at `:78-102` match `UnsupportedProtocolVersionErrorData`'s required `requested`/`supported`.
  - `-32602` for resume cursor and `replayFrom`: `test_session_capabilities.py:357,382`, against err:31,48 and session-setup.mdx:213-215.
  - `-32000` auth gating in `_helpers.py:186`, against err:34.
  - `-32602` tolerance in `test_enums.py:181`.
- **Batch `-32600`/`-32700` assertions in `test_batch.py`:** retire with B1 (transports audit). The new single-`-32600`/`id: null` rule for arrays (`transports.mdx:67`) matches err:29.
- **No test asserts the wrong code**, but none asserts `-32002` at all yet. The inconsistency is in the fixture: `_base.py:485` (and `:418` for fork) uses `-32602` where the target requires `-32002`.

### Map recommendation (`spec-tracker/maps/v2.toml`)

- **`overview.mdx`**
  - `sections` at target: `["Communication Model", "Agent > Baseline methods", "Argument requirements", "Error handling", "Conventions"]`.
  - "Communication Model" is new to the core list. It kept Title Case at ov:8, so use exactly that. It now holds the request-ID rules every exchange depends on, which makes it core.
  - "Agent > Baseline methods" needs the path because "Client > Baseline methods" also exists (ov:160).
  - Not core: "Message flow" (non-normative steps), "Agent > Optional methods" (feature-gated pointers), "Request cancellation" (a one-line pointer to cancellation.mdx), "Unstable features" (an index table), "Extensibility" (a pointer).
  - Add `src/tck/v2/conformance/test_diagnostics.py` to `code` (ACP-ERROR-001).
- **`error.mdx`: yes, make it core, as the whole doc (omit `sections`).** Reason: the error-code table and the unknown-method, unknown-session and before-initialization rules that initialization.mdx:90, session-setup.mdx:51,410, session-delete.mdx:94 and elicitation.mdx:59 link to and restate.
  - The "Unstable features" section restates per-feature `-32002`/`-32601` rules the TCK tests (fork). Keeping it in makes those changes visible too.
  - Suggested `code`: `src/tck/v2/conformance/test_jsonrpc.py`, `src/tck/v2/conformance/test_diagnostics.py`, `src/tck/v2/conformance/test_informational.py` (or wherever ERROR-201 lands), `src/tck/v2/validation.py`, `src/tck/v2/protocol.py` (error-code constants).
- **`core_defs`:** consider adding `RequestId` and `Error` next to `ErrorCode`. Both are envelope types every response depends on, and both changed in this range. Low-stakes **DECISION NEEDED**.

## Testability notes

- **ERROR-201:** fully observable. A conforming agent returns `{"code": -32002, "data": {"sessionId": "<requested>"}}`. A non-conforming one returns `-32602` (as today's fixture does), `-32002` with no or wrong `data`, a success, or nothing. The schema cannot catch a missing `data` because `ErrorData` has an `Other` branch, so the test must check it explicitly.
- **ERROR-202:** observable per probe. Only send a probe when the gate is *not* advertised. A session-less agent answering `session/new` with `-32000` (auth) instead of `-32601` would FAIL. That is correct per err:44, since an unadvertised method has no auth surface.
- **JSONRPC-202:** passive. Coverage depends on the agent sending requests at all. Report SKIP explicitly when none are seen, so a vacuous PASS is not reported.
- **JSONRPC-002 null-id tightening:** passive across every response to a TCK request. A result with `id: null` can't match a TCK request id anyway, so in practice `wait_for_response` will time out first. The validation change mostly matters for transcript-wide validators.
- **PARSE-001 / INVALIDREQ-001:** keep them record-only. The TCK's probe line itself breaks `transports.mdx:24`, so no agent can be held to a behaviour on it beyond, optionally, the shape of a reply it chose to send (ERROR-204).
- **err:38 "generic failure", and the client-side halves of ov:60 and err:56:** not observable from the agent side (see ledger).

## Discrepancies

1. **Fixture vs spec:** `tests/fixtures/agents/v2/_base.py:484-485` answers an unknown `sessionId` on `session/prompt` with `-32602`. err:54 says MUST `-32002` + `data.sessionId`. Likewise `_base.py:417-418` (fork, err:64), and the resume leniency at `_base.py:482-483` (err:56). The "conforming" fixtures are non-conforming at target.
2. **Spec vs spec (wording strength, not a conflict):** session-setup.mdx:51 says "Otherwise the Agent responds with `-32002`" with no MUST and no `data`. err:54 adds MUST and `data.sessionId`. Treat err:54 as authoritative; the two do not contradict.
3. **Python SDK vs Rust SDK vs spec, on null request ids:**
   - Spec: v2 request IDs must not be null (ov:15).
   - Rust rejects a v2 request with `id: null` with `-32600` and `id: null` (`src/agent-client-protocol/src/jsonrpc/protocol_compat.rs:639-644`, `raw_id.rs:127-130`, test `protocol_compat.rs:2124-2147`).
   - Python's connection still treats `null` as a valid request id (`src/acp/connection.py:43-46`).
   - This only matters if the TCK ever sends a null-id request. It shouldn't (client MUST NOT, ov:15), so nothing is proposed.
4. **Python SDK vs Rust SDK, on a structurally invalid envelope:** Rust answers `-32600`/`null`, Python is silent (see INVALIDREQ-001 above). The spec defines the code (err:29) but no obligation.
5. **Python SDK vs spec on arrays** (transports scope, noted only): Python silently drops a non-empty JSON array (`src/acp/_jsonrpc.py:18-24`, `src/acp/_transport.py:80-81`). `transports.mdx:67` says receivers reject one with a single `-32600`. Rust follows the spec (`transport_actor.rs:27-33`).
6. **Registry text vs spec:** `ACP-JSONRPC-004`, `ACP-ERROR-001`, `ACP-INFO-UNKNOWNSESSION-001`, `ACP-INFO-PARSE-001` and `ACP-INFO-INVALIDREQ-001` all make claims ("still 'should'", "byte-identical", "still a stub") that are false at target.

## Open questions

- **Ownership overlaps** to route. Whoever audits these docs should agree with or absorb the corresponding proposals here:
  - extensibility.mdx: `ACP-JSONRPC-004` -> `-201`.
  - session-setup.mdx: the resume-of-unknown-session probe, and a possible new ADVISORY row "`session/close` of an unknown or already-closed session succeeds" (err:56, session-setup.mdx:407-410). No close row covers that today.
  - session-config-options.mdx: the set_config_option unknown-session probe.
  - fork: fixture `-32602` -> `-32002`.
  - initialization.mdx: err:58-60 pre-init gating.
  - authentication.mdx: ov:60 "non-empty" wording; add ov:60 to `ACP-AUTH-204`'s citation.
- **Cancellation audit:** `ACP-INFO-CANCEL-201` says "Behaviour for an unknown `sessionId` is not specified". session-setup.mdx:51 now says "Agents ignore `session/cancel` for a session that isn't active". Route to the cancellation/prompt-lifecycle audit.
- **Transports audit:** `ACP-TRANSPORT-201` cites `schema#/anyOf/2`, `#/anyOf/3`. These still resolve but now mean `ProtocolLevel`/`Proxy`, so the citation is wrong though not dangling.
- Whether `answers_notifications.py` / `pushes_status_and_answers_notifications.py` should switch to an error-shaped bogus reply, so the JSONRPC-002 validation tightening can't add unintended FAILs (see the JSONRPC-002 details).
