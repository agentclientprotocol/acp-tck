# v1 schema impact (base beac4ba9 -> target 3961af94): `$defs`, validation carve-outs, method tables, `x-deserialize-default-on-null`

**Sources checked:** agent-client-protocol (checkout `agent-client-protocol-2`, read via `git show`, not pulled) base `beac4ba96190018e9f6d82e148ff275084c5aa3e` -> target `3961af94fa62d2386d993cadf1afc8b146fc799a` (2026-11-10): `schema/v1/schema.unstable.json`, `schema/v1/meta.unstable.json`, `schema/v1/schema.json`, `agent-client-protocol-schema/src/{serde_util.rs,v1/agent.rs,v1/client.rs}`, `schema-generator/src/main.rs`, `docs/rfds/proxy-chains.mdx`, `docs/protocol/v1/draft/extensibility.mdx`. python-sdk @ `8a9940744d0afa0bb3d71b4e4df8f843b061bccf` (2026-11-09; its bindings are generated from `schema-v1.23.0`, `schema/VERSION`). acp-tck @ `200baba` (vendored files are byte-identical to base, checked with `cmp`).
**Confidence:** high. Structural diffs were computed by script (descriptions and titles stripped). The TCK derivation code was run against the target files, and the full `tests/v1` + `tests/common` suite (195 tests, incl. every v1 fixture end-to-end) passed in a scratch copy with the target schema and meta swapped in. The one DECISION NEEDED (null on hinted fields) is a policy call, not an evidence gap.

## Answer

Re-vendoring is mechanically safe. `tck.v1.protocol` and `tck.v1.validation` pick up all eight new methods correctly from the target files. No code assumes a fixed method set. `proxy/*` (new `meta.proxyMethods` key, new root `anyOf/3`, new `x-side: "proxy"`) is ignored by every derivation, which is correct: an agent under test sending `proxy/*` is still flagged by ACP-SCHEMA-001. All hand-written carve-outs in `validation.py` are still needed and still correct. The null-result carve-out now auto-covers `session/archive` and `session/unarchive`, and the resulting set matches the Rust crate's `default_on_null` inventory exactly. Every structural `$def` change is additive or relaxing, so no conforming agent flips from PASS to FAIL. Agents using two unstable features flip from a false FAIL to PASS: `auth/status_update` and `session` tool-call content. ACP-SCHEMA-001/002 stay accurate, and their citations resolve. The `x-deserialize-default-on-null` hints change no JSON Schema type, and no TCK test sends or asserts on null at those paths. But they make an existing strictness visible: ACP-AUTH-006 (MANDATORY) FAILs an agent whose terminal auth method has `args: null` or `env: null`, even though both reference receivers accept it. That is **DECISION NEEDED**. Docstring-only staleness: the comments in `validation.py` and `protocol.py` describing the schema as "three envelopes" and the meta file as "three dicts".

## Summary table

| Id | Classification | Note |
|---|---|---|
| ACP-SCHEMA-001 | unchanged | Text still accurate. `#/anyOf/0` is still `Agent` (Proxy was appended at index 3). Additive changes only. Agents using `auth/status_update` or `ToolCallContent{type:"session"}` stop getting a false FAIL. |
| ACP-SCHEMA-002 | unchanged | `extensibility.mdx:10-14,43` text identical at target (only `;`->`.` on line 13). Still no `additionalProperties: false` anywhere. `Error` still `{code,message,data}`. |
| ACP-AUTH-006 | unchanged text; **DECISION NEEDED** (validation policy) | Rejects `args: null`/`env: null` on `AuthMethodTerminal`. Target schema marks both `x-deserialize-default-on-null`, and Rust and Python receivers accept null. See D1. |
| ACP-LOAD-003 / ACP-LOAD-001 | unchanged | Null-result carve-out still needed (schema still `type: object` with no null). Rust `default_on_null` macro and its citation `serde_util.rs:30-38` still say the same thing at target. |
| ACP-JSONRPC-006 | unchanged | Pointer `#/anyOf/2/properties/params/anyOf/0` still resolves to `ProtocolLevel`'s `CancelRequestNotification` branch. |
| ACP-JSONRPC-002 | unchanged | `RequestId` and `Error` are structurally identical. The hand-written envelope check still matches. |
| ACP-SYSPROMPT-001..003 | unchanged (schema mechanics) | Stabilized `SystemPrompt*` shapes are identical in `schema.json` and `schema.unstable.json`, and identical to base. Wording/tier is the session-setup researcher's call. |
| ACP-SESSION-003, ACP-RESUME-001, ACP-ADDDIRS-001, ACP-AUTH-002 | unchanged | They cite hinted `$defs`, but the TCK sends concrete non-null values (`mcpServers: []`, string arrays). Hints don't affect them. |
| (new) | none proposed | No new observable agent-side schema rule. See ledger candidates L1, L2. |

## Requirements

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| R1 | Agent-authored messages validate against the vendored schema (unchanged, re-vendored) | MUST | `schema/v1/schema.unstable.json#/anyOf/0` @ 3961af94 |
| R2 | `proxy/initialize`/`proxy/successor` are exchanged only between a conductor and its proxies. An agent (the component that receives `initialize`) does not send them to a client. | RFD proposal (Draft), not a requirement | `docs/rfds/proxy-chains.mdx:235-236,304-305` @ 3961af94 |
| R3 | Receivers deserialize `null` at hinted fields as the default (empty list/map) | receiver hint, no sender rule | `schema/v1/schema.unstable.json#/$defs/AuthMethodTerminal/properties/args` (and the 15 other paths below); `agent-client-protocol-schema/src/v1/agent.rs:1131-1150` @ 3961af94 |

## Details

### 1. Structural `$def` changes and what they touch

Computed with descriptions/titles stripped. These are the 11 structural `$defs` plus root. The other 9 changed only by gaining the hint (section 3).

| `$def` | Change | Direction for agent output | TCK impact |
|---|---|---|---|
| (root) `anyOf` | +4th member `Proxy` (`ProxyRequest`/`ProxyResponse`/`ProxyNotification`) at index 3 | n/a | None. Validation never validates against the root. Pointers `#/anyOf/0` (ACP-SCHEMA-001) and `#/anyOf/2/...` (ACP-JSONRPC-006) are unchanged. Docstring `validation.py:5-7` ("three side-annotated envelopes") is stale. |
| `AgentNotification` | +`AuthStatusUpdateNotification` (`auth/status_update`, `x-side: client`) | relaxing | Now in `_request_and_notification_method_defs()`. Base flagged it as "not a known agent-authored ... method" (verified by probe), so SCHEMA-001 false-FAILed an agent using unstable auth status. Fixed by re-vendor. |
| `AgentResponse` | +`AuthStatusResponse`, `ArchiveSessionResponse`, `UnarchiveSessionResponse`, `SessionStatusResponse`, `SetSessionTitleResponse` | additive | Now in `_response_method_defs()`. The TCK never sends these methods, so no runtime effect. |
| `ClientRequest` | +the 5 matching requests | client-authored | Not validated (TCK never validates its own traffic). |
| `AgentAuthCapabilities` | +optional nullable `status` -> `AuthStatusCapabilities` | additive | `initialize` result. A previously untyped `auth.status` key is now type-checked (theoretical tightening, see below). |
| `SessionCapabilities` | +optional nullable `archive`, `status`, `title` (systemPrompt was already in unstable base) | additive | Same as above. No TCK capability gate references them. |
| `ListSessionsRequest` | +optional `archived` (`SessionArchiveFilter`) | client-authored | Not validated. Default filter semantics are the list researcher's area. |
| `SessionInfo` | +optional `archived: boolean\|null` | additive | `session/list` result. Nested, so SCHEMA-002 (root keys only) is unaffected. |
| `SessionMessage` | +optional `senderMessageId`, `recipientMessageId` | additive | `session/update` (unstable). |
| `SessionMessageChunk` | -`senderSessionId`, -`recipientSessionId` | relaxing (no `additionalProperties: false`) | An agent still sending them validates. They're nested under `update`, so SCHEMA-002 can't see them. |
| `SubagentUpdate` | +optional `cwd`, `additionalDirectories` | additive | `session/update` (unstable). |
| `ToolCallContent` (`oneOf` + `discriminator`) | +variant `{type: "session"} & SessionReference` | relaxing | Base rejected `{"type":"session","sessionId":..}` inside a `tool_call` (verified by probe). Target accepts it. False FAIL removed. |

"Theoretical tightening": a property newly declared at target is now type-checked where it used to be an unknown key the schema ignored. An agent that previously emitted, for example, `sessionCapabilities.status: "yes"` (a non-`_meta` custom key, already a SCHEMA-002 issue only if at a root) would now fail SCHEMA-001. This only affects agents already violating `extensibility.mdx:43`. No action needed.

Removed `$defs`: none. Enums the TCK hard-codes (`protocol.py:31-54`: `ErrorCode` values, `StopReason`) are identical at target.

### 2. Method tables (`src/tck/v1/protocol.py`)

`meta.unstable.json` diff: `agentMethods` +`session/archive`, `session/unarchive`, `session/status`, `session/set_title`, `auth/status`. `clientMethods` +`auth/status_update`. New top-level key `proxyMethods: {proxy/initialize, proxy/successor}`.

Derived at target, by running the TCK's own functions against the target files:
- `AGENT_METHODS` = 23 (base 18 + 5 new). `AGENT_NOTIFICATIONS` = `{mcp/message, session/cancel}` (unchanged).
- `CLIENT_METHODS` = 13 (+`auth/status_update`). `CLIENT_NOTIFICATIONS` = `{auth/status_update, elicitation/complete, session/update}`.
- `PROTOCOL_METHODS` = `{$/cancel_request}` (unchanged).
- `proxyMethods` is read by nothing (`protocol.py:108-117` index only the three named keys). That is the right outcome, since proxy methods are not part of the agent-under-test surface. It also means a future meta key would be silently ignored too. Optional hardening: a unit test asserting `set(load_meta())` equals the expected key set, so the next new key gets looked at.
- Invariants in `tests/v1/test_validation.py:251-266` hold at target: every agent method has a response def or is a notification, and every client method has a params def.
- `x-side` values at target: `agent`, `client`, `protocol`, **`proxy`** (new). No TCK code filters on `x-side`: grep finds it only in docstrings (`validation.py:9,14,16`). `InitializeProxyRequest`/`Response` are `allOf: [$ref InitializeRequest/Response]` with their own `x-method: proxy/initialize`. They sit outside `AgentRequest`/`AgentResponse`, so they can't leak into the `initialize` mapping (verified: no `proxy/` key in either derived map).
- No hard-coded method in the v1 suite collides with a new method. The suite sends only `initialize`, `authenticate`, `logout`, `session/{new,prompt,cancel,close,delete,list,set_config_option}`, `$/cancel_request`, and `_tck/*` probes.
- An agent emitting `proxy/successor` is flagged under SCHEMA-001 as an unknown agent-authored method (probe-verified). That matches the RFD: agents receive `initialize`, are terminal, and the conductor answers an agent's `proxy/successor` with `-32600` (`docs/rfds/proxy-chains.mdx:235-236,305`). The RFD is a Draft proposal. If it ever changed, this would be the place to revisit.
- Docstring `protocol.py:61-62` ("three flat ... dicts") is stale: there are now four, including `proxyMethods`.

### 3. Hand-written carve-outs in `src/tck/v1/validation.py`

| Carve-out | Where | Status at target | Evidence |
|---|---|---|---|
| `null` result accepted for all-optional object responses (the "`session/load` null quirk", generalized) | `validation.py:153-165,437-439` | **Still needed, still correct.** The schema still has no `null` for these. The derived set at target is `authenticate, logout, providers/disable, providers/set, session/archive, session/close, session/delete, session/load, session/resume, session/set_mode, session/unarchive`. This is exactly the agent-implemented responses in Rust's `for_each_defaultable_payload` (`agent-client-protocol-schema/src/serde_util.rs:128-158` @ 3961af94: Authenticate/Logout/LoadSession/ResumeSession/CloseSession/DeleteSession/SetSessionMode + ArchiveSession/UnarchiveSession + SetProvider/DisableProvider). `session/status` and `session/set_title` responses have required fields, so they are correctly excluded on both sides. | scripted derivation; `serde_util.rs:30-38` macro doc unchanged in meaning (punctuation only) |
| Null/absent `params` validated as `{}` | `validation.py:274` | Unchanged, still fine. Envelopes changed only by added members. | diff |
| `_`-prefixed methods skipped | `validation.py:256-258` | Unchanged. #2534 ("ExtNotification can be sent by either side") is consistent. | CHANGELOG |
| `$/cancel_request` looked up by def name `CancelRequestNotification` | `validation.py:111-114` | Def still exists, `x-method: $/cancel_request`, `x-side: protocol`. | scripted check |
| `AgentResponse` result branch selected by content | `validation.py:124-129` | Still works (derivation output above). | scripted |
| Hand-written error envelope (int `code`, str `message`) | `validation.py:168-196` | `Error` unchanged: props `code,data,message`, required `code,message`. `ErrorCode` description-only. | scripted |
| `RequestId` = null\|int\|string | `validation.py:199-203` | Unchanged. | scripted |
| SCHEMA-002 premise "no `additionalProperties: false` anywhere" | `validation.py:321-364`, `requirements.py:1017-1033` | Still true at target (0 occurrences). | scripted |
| `Error` has no `_meta` | `validation.py:388-396` | Still true. `extensibility.mdx:13-14` @ 3961af94 still says so. | doc |
| `$schema` dialect mapping | `validation.py:33-35` | Still draft 2020-12. The unknown `x-deserialize-default-on-null` keyword passes `check_schema` (suite green). | scripted, suite run |
| `AuthMethodTerminal` validated directly because `AuthMethod`'s `anyOf` accepts a malformed terminal entry as `agent` (ACP-AUTH-006) | `test_authentication.py:163-170` | Still needed. Probe: a terminal method with `args: null` passes `InitializeResponse` validation but fails `AuthMethodTerminal`. | probe |

### 4. `x-deserialize-default-on-null` hints

Added by upstream #2569 (`5a0a17b1`, 2026-10-27), with a generator test (#2571, `212870d6`) that fails if a Rust `DefaultOnNull` field lacks the hint (`schema-generator/src/main.rs:1100-1118` @ 3961af94). The Rust `DefaultOnNull` deserialization **predates base** (`agent-client-protocol-schema/src/v1/agent.rs:721,726,809,813,...` @ beac4ba9). The hint only makes existing Rust receiver behavior machine-readable. The #2571 commit message says generated parsers (the TypeScript SDK) read it to accept null. JSON Schema types are unchanged at every path (verified: identical apart from the hint).

16 paths in `schema.unstable.json` (14 in `schema.json`, which lacks `ForkSessionRequest`):

| Path | Required? | Authored by | Validated by TCK? |
|---|---|---|---|
| `CreateTerminalRequest.args` (array), `.env` (array) | optional | **agent** (`terminal/create`) | yes, SCHEMA-001 sweep (`validate_agent_message`) |
| `AuthMethodTerminal.args` (array), `.env` (object) | optional | **agent** (`initialize` result) | yes: ACP-AUTH-006 (direct `AuthMethodTerminal` check); INIT-001/SCHEMA-001 do **not** catch it (anyOf leak) |
| `McpServerHttp.headers`, `McpServerSse.headers`, `McpServerStdio.args`, `.env` | required | client | no |
| `New/LoadSessionRequest.mcpServers` (required), `.additionalDirectories`; `Resume/ForkSessionRequest.mcpServers`, `.additionalDirectories` (optional) | mixed | client | no |

Does the TCK send or assert on null at any of these? **No.** Grep over `src/tck/v1`, `tests/v1`, `tests/fixtures/agents/v1`, `tests/common` finds no `None`/`null` for `mcpServers|additionalDirectories|args|env|headers`. The suite sends `mcpServers: []` and concrete arrays (ACP-SESSION-003, ACP-RESUME-001, ACP-ADDDIRS-001).

Would TCK validation reject null where a reference receiver accepts it? **Yes, for the two agent-authored defs** (probe against the target schema):
- `validate_against_def("AuthMethodTerminal", {..., "args": null, "env": null})` -> `/args: None is not of type 'array'`, `/env: None is not of type 'object'`. ACP-AUTH-006 (MANDATORY) FAILs.
- `validate_agent_message(terminal/create with args: null, env: null)` -> two type errors. ACP-SCHEMA-001 would FAIL. In practice this is only reachable from an agent that already calls `terminal/create` without the capability: the v1 suite never advertises `terminal`, so ACP-CLIENTCAP-002 fails first.

Receivers: Rust accepts null (`DefaultOnNull` at `agent-client-protocol-schema/src/v1/agent.rs:1142,1148` [`AuthMethodTerminal`, struct at 1131] and `v1/client.rs:2749,2754` [`CreateTerminalRequest`, struct at 2743] @ 3961af94). Python accepts null (`Optional[...] = None`: `src/acp/schema.py:969,973` [`AuthMethodTerminal`], `:2838,2842` [`CreateTerminalRequest`] @ python-sdk 8a99407). Rust serializers never emit null here (`skip_serializing_if = "Vec::is_empty"`), and no doc text tells senders null is acceptable. `authentication.mdx`, `terminals.mdx` and `session-setup.mdx` @ 3961af94 don't mention null for these fields.

**D1 -- DECISION NEEDED: null at hinted agent-authored fields.**
- Option A (strict, current behavior): keep failing `args: null`/`env: null`. Justification: the wire type is still `array`/`object`, and the hint is receiver-side only.
- Option B (recommended): make MANDATORY validation hint-aware. Drop a jsonschema error when `error.validator == "type"`, `error.instance is None` and `error.schema.get("x-deserialize-default-on-null")`. This is verified feasible: the error's `schema` carries the hint, e.g. `absolute_schema_path ['properties','args','type']`. Optionally record it under an ADVISORY ("send `[]`/omit, don't send null"), mirroring ACP-LOAD-003. Rationale: it is the same "send `{}`, tolerate `null`" situation the TCK already accepted for payload-level null (`validation.py:153-163`). Here upstream has made the tolerance machine-readable in the schema, and both reference receivers interoperate. B is schema-derived, so it self-updates on refresh like the rest of `validation.py`. If adopted, add it to the module docstring's carve-out list, and note in ACP-AUTH-006's text that null counts as omission. The tier stays MANDATORY.

## Testability notes

- Re-vendor check: in a scratch copy with the target `schema.unstable.json`/`meta.unstable.json`, `tests/v1` + `tests/common` gave 195 passed, 0 failed (`python -m pytest tests/v1 tests/common`, PYTHONPATH pointed at the copy; `test_cli` subprocesses use `sys.executable -m tck`, so they inherited it). The `test_registry` JSON-pointer resolution also passes against the target. No fixture's FAIL/PASS set changes.
- Suggested unit tests for the programmer after re-vendoring: (a) `auth/status_update` params validate, and `proxy/successor` from the agent is flagged; (b) `tool_call` with `{type:"session", sessionId}` content validates; (c) the null-result set includes `session/archive`/`unarchive` and excludes `session/status`/`set_title`; (d) if D1=B, `AuthMethodTerminal` with `args: null` passes and with `args: "x"` fails; (e) optional: `set(load_meta())` equals `{version, agentMethods, clientMethods, protocolMethods, proxyMethods}`.
- A defect fixture for D1 is only meaningful under Option A: a v1 agent advertising a terminal auth method with `args: null` when `auth.terminal` is offered. Under Option B it would instead be a conforming fixture with that shape (and the ADVISORY FAIL, if added).

## Ledger candidates (deliberate non-requirements)

- **L1** -- citation `schema/v1/schema.unstable.json#/$defs/NewSessionRequest/properties/mcpServers` (and the other client-authored hinted paths) @ 3961af94: "Agents tolerate `null` for client-authored list fields marked `x-deserialize-default-on-null`." Reason: client-side wire rule (the schema type is array, so a TCK sending null would itself emit schema-invalid traffic); a receiver hint, not a normative agent MUST. Python's `McpServerHttp.headers`/`McpServerStdio` and `LoadSessionRequest.mcpServers` are non-Optional (`src/acp/schema.py:1900,1923,3724`), so the reference SDKs disagree anyway.
- **L2** -- citation `docs/rfds/proxy-chains.mdx:235-236,304-305` @ 3961af94: "The TCK does not exercise `proxy/initialize`/`proxy/successor`." Reason: out of scope (intermediary-only, Draft RFD). An agent sending them is still caught by ACP-SCHEMA-001 as an unknown method.

## Discrepancies

- Rust vs Python on client-authored hinted fields: Rust accepts null on all 16 paths (`DefaultOnNull`). Python (bindings from schema 1.23.0) accepts null only where the field is `Optional` (agent-authored `AuthMethodTerminal`/`CreateTerminalRequest`, and `additionalDirectories`), not for required `mcpServers`/`headers`/stdio `args`/`env`. It does not read `x-deserialize-default-on-null` at all: `scripts/gen_schema.py:160-174` reads only `default-on-error`/`skip-invalid-items`. This doesn't affect the TCK unless D1 is extended to client-authored paths, which it shouldn't be.
- Schema type vs hint: the JSON Schema type says `array`, while the hint says receivers treat null as default. They don't conflict formally. This is the root of D1.
- Stale TCK docstrings (no behavior impact): `src/tck/v1/validation.py:5-7` (three root envelopes, now four) and `src/tck/v1/protocol.py:61-62` (three meta dicts, now four).

## Open questions

- D1 (above): orchestrator/user decision.
- `ListSessionsRequest.archived` defaults to excluding archived sessions (`session-list.mdx:248` @ 3961af94). This could matter to list tests that expect a just-created session to appear, but only if the agent archives sessions on its own. Route to the list/delete researcher.
- Whether the v1 suite should add CAPABILITY tests for `session/status`, `session/set_title`, `session/archive`, `auth/status`: scoping, already raised by the inventory.
