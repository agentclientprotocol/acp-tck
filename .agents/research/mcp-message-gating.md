# When may an agent send `mcp/message` (MCP-over-ACP), and how should the TCK gate it?

**Sources checked:** agent-client-protocol @ `9af0e9f` (2026-09-29, HEAD, includes `ef4613d` "make MCP-over-ACP request-scoped"); acp-rust-sdk @ `b55cdc7` (2026-09-28; pins `agent-client-protocol-schema =1.9.1`); acp-python-sdk @ `9d07d78` (2026-09-21); acp-tck @ `183ee5a` (branch `eugenethedev/v2-draft`). Vendored `src/tck/v2/schema/{schema,meta}.unstable.json` are byte-identical to upstream `schema/v2/*.unstable.json` @ `9af0e9f` (diffed).
**Confidence:** high on the wire facts (schema is unambiguous); medium on tiering — the only behavioral text is the MCP-over-ACP RFD (a proposal). The draft docs never mention the `acp` transport.

## Answer

1. **It is not v2-only. It is unstable-only.** `mcp/message` shows up in **both** the v1 and v2 *unstable* schema/meta and in **neither** stable schema. The TCK's v1 suite vendors only the stable v1 schema, so v1 does not know the method at all.
2. **The premise "client capability `mcp.acp`" is wrong.** No client capability for MCP-over-ACP exists; v2 `ClientCapabilities` has only `auth`, `elicitation`, `nes`, `positionEncodings`, `_meta`. The capability belongs to the **agent**: `capabilities.session.mcp.acp` in v2 and `agentCapabilities.mcpCapabilities.acp` in v1, both in the `initialize` *response*. It says the agent can consume `type: "acp"` MCP server declarations. The client-side gate is the **declaration** itself: the client puts `{"type":"acp","name","serverId"}` in `mcpServers` on session setup. `mcp/message` requests are addressed to a declared `serverId`.
3. **Direction and kind (draft schema):** `mcp/message` is a **request only in agent→client direction** (`AgentRequest`) and a **notification only in client→agent direction** (`ClientNotification`). An agent-sent `mcp/message` *notification* is not a defined message.
4. **No normative MUST/SHOULD says "agent MUST NOT send `mcp/message` unless a server was declared".** It is only implied: the schema describes `serverId` as "the declared ACP MCP server", and the RFD describes an agent→provider request to a declared server. The RFD also treats an unresolvable `serverId` as a *runtime* error the recipient answers (`-33001`), not as a sender violation.
5. **TCK today:** `ACP-CLIENTCAP-202` only checks method *names*, and `mcp/message` is now in `CLIENT_METHODS`. So both an agent `mcp/message` request and an agent `mcp/message` notification pass 202. The mock client never declares an ACP server (`new_session` omits `mcpServers`) and answers any such request with `-32601`.
6. **Recommendation:**
   - Add an INFORMATIONAL row: "no `mcp/message` request when no `acp` server was declared". It mirrors `ACP-CLIENTCAP-201`'s shape.
   - Make `ACP-CLIENTCAP-202` kind-aware, so an agent-sent `mcp/message` notification FAILs. This is schema-grounded.
   - `mcp/message` is the only draft-only agent→client method.

## Requirements

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| R1 | `mcp/message` exists only in the unstable (draft/RFD) surface, in both v1 and v2 | fact (not a tier) | agent-client-protocol `schema/v1/meta.unstable.json:15,43`; `schema/v2/meta.unstable.json:13,34`; absent from `schema/v1/meta.json`, `schema/v2/meta.json` |
| R2 | Agent→client `mcp/message` is a **request** (`AgentRequest` → `MessageMcpRequest`, `x-side: client`) | MUST (schema shape) | `schema/v2/schema.unstable.json:536,581` (`#/$defs/AgentRequest`), `:2968-3005` (`#/$defs/MessageMcpRequest`, `x-side` at `:3005`) |
| R3 | Client→agent `mcp/message` is a **notification** (`ClientNotification` → `MessageMcpNotification`, `x-side: agent`); no agent→client `mcp/message` notification is defined | MUST (schema shape) | `schema/v2/schema.unstable.json:9591,9682` (`#/$defs/ClientNotification`), `:10049` (`#/$defs/MessageMcpNotification`); `#/$defs/AgentNotification` (`:5542`) has no `mcp/message` branch; RFD `docs/rfds/mcp-over-acp.mdx:31-36` |
| R4 | Request params: required `serverId`, `requestId`, `method`; optional `params` (object/null), `_meta` | MUST (schema) | `#/$defs/MessageMcpRequest/required`; RFD `:196-200` |
| R5 | `serverId` names "the declared ACP MCP server receiving this request" | implied only (schema description, no RFC 2119 keyword) | `schema/v2/schema.unstable.json:2973` (`#/$defs/MessageMcpRequest/properties/serverId`) |
| R6 | Capability is agent-side: v2 `capabilities.session.mcp.acp` (object marker, `{}` = supported, omitted/null = not advertised); v1 `agentCapabilities.mcpCapabilities.acp` (bool, default false) | capability:`capabilities.session.mcp.acp` (agent's own claim) | `#/$defs/SessionCapabilities/properties/mcp` (`:3403`), `#/$defs/McpCapabilities/properties/acp` (`:3571`), `#/$defs/McpAcpCapabilities` (`:3615`); RFD `:65-95`; v1: `schema/v1/schema.unstable.json:2684` |
| R7 | The client checks the agent's `acp` MCP capability, then declares `{"type":"acp","name","serverId"}` in a session setup request | RFD proposal (lowercase prose); draft docs only have MUST-verify for stdio/HTTP | RFD `:42-55`; `#/$defs/McpServer` `acp` branch `:8084-8090`, `#/$defs/McpServerAcp` `:8209`; docs `docs/protocol/v2/draft/session-setup.mdx:450` (stdio/HTTP only) |
| R8 | An agent may invoke/discover a declared server **before** returning the session ID, i.e. during `session/new` | MAY (RFD) | RFD `:59` |
| R9 | An unresolvable `serverId` gets the binding error `-33001`, returned by the final recipient | RFD proposal | RFD `:61,180-186,257` |
| R10 | Callers use a fresh `requestId` per operation and "must not reuse an active ID for the same server" | RFD, lowercase "must" | RFD `:196` |
| R11 | Peers MUST treat omitted capabilities as UNSUPPORTED | MUST (general) | `docs/protocol/v2/draft/initialization.mdx:108` |
| R12 | Custom methods must be `_`-prefixed (the basis of `ACP-CLIENTCAP-202`) | MUST | `docs/protocol/v2/draft/extensibility.mdx:43,52` (as cited by the TCK) |

No rule in the draft **docs** (`docs/protocol/v2/draft/*.mdx`) mentions the `acp` transport or `mcp/message`. `session-setup.mdx:340` lists only `session.mcp.stdio`/`session.mcp.http` "and any extension-specific transport capabilities". The RFD and the generated `schema.mdx` are the only sources.

## Details

### Q1: Is it v2-only?

No. Here is where it appears:

- **Spec:**
  - v1 unstable meta has `mcp_message` in both `agentMethods` (`schema/v1/meta.unstable.json:15`) and `clientMethods` (`:43`). v1 unstable schema defines `MessageMcpRequest` (`schema/v1/schema.unstable.json:2178`) and `McpCapabilities.acp` (bool, `:2684`).
  - v2 unstable is the same: `schema/v2/meta.unstable.json:13,34`.
  - Both stable metas (`schema/v1/meta.json`, `schema/v2/meta.json`) lack it.
  - The Rust models gate it behind `#[cfg(feature = "unstable_mcp_over_acp")]` (`agent-client-protocol-schema/src/v2/client.rs:2483-2484`, `src/v2/agent.rs:5406-5407`; feature in `agent-client-protocol-schema/Cargo.toml:44`). The v1 variants mirror this (`src/v1/client.rs:2797`, `src/v1/agent.rs:5135`).
  - RFD `docs/rfds/mcp-over-acp.mdx:65-95` defines the capability for both "ACP v1" and "draft ACP v2". `:306,328`: "Both ACP v1 and draft v2 must exercise the same binding semantics."
  - The generated docs list it for both: `docs/protocol/v1/draft/schema.mdx:385,2059` and `docs/protocol/v2/draft/schema.mdx:416,1846`.
- **Rust SDK (`b55cdc7`):**
  - Exposes it for v1 (`src/agent-client-protocol/src/schema/mcp.rs:3-15`) and v2 (`src/schema/v2_impls.rs:266-272,320,351,361,383`) under `unstable_mcp_over_acp`.
  - It is on the **pre-`ef4613d` stateful model**: `mcp/connect`, `mcp/disconnect`, `connectionId`, and requests and notifications in both directions. See `md/mcp-bridge.md:10,96-99,135-143` and `Cargo.toml:38` (`agent-client-protocol-schema = "=1.9.1"`).
- **Python SDK (`9d07d78`):**
  - Exposes it for v1 (`src/acp/meta.py:15,44`, alongside `mcp_connect`/`mcp_disconnect`) and experimental v2 (`src/acp/experimental/v2/meta.py:13,35`).
  - It is also on the legacy `connection_id` model (`src/acp/agent/connection.py:313-334`).
  - The agent side can send both a request (`mcp_message`) and a notification (`notify_mcp`) to the client.
  - Neither SDK's agent-side send path checks any capability. The SDKs gate on declarations: the Rust bridge only opens connections for `McpServer::Acp` entries in session setup (`md/mcp-bridge.md:86-99`).
- **TCK v1:**
  - Vendors only stable `schema.json`/`meta.json` @ `6d08f41` (`src/tck/v1/schema/VENDORED.md:9`), so `mcp/message` is not in v1 `CLIENT_METHODS` (`src/tck/v1/protocol.py:112`).
  - v1 has no general "undefined agent→client method" row. The closest are `ACP-CLIENTCAP-001/002/003` (`src/tck/v1/requirements.py:618-649`).
  - A v1 agent emitting `mcp/message` during `ACP-SCHEMA-001`'s full exchange (`src/tck/v1/conformance/test_initialize.py:142`) would be flagged "not a known agent-authored request/notification method" (`src/tck/v1/validation.py:260`). Its request would get `-32601` from v1 `run_prompt` (`src/tck/v1/conformance/_helpers.py:367-372`).
  - This is consistent with v1 stable, and nothing needs to change in v1 unless v1 moves to the unstable schema, which would be a separate decision.

### Q2: What the spec says

Wire shapes at `9af0e9f`, request agent→client (RFD `:103-131`):

```json
{"jsonrpc":"2.0","id":20,"method":"mcp/message",
 "params":{"serverId":"project-tools:7a72","requestId":"mcp-request:a11f",
           "method":"tools/call","params":{"name":"echo","arguments":{...},"_meta":{...}}}}
```

The response is `MessageMcpResponse`: exactly one of `{"result": <any>}` or `{"error": McpError}`, with `additionalProperties: false`. Inner MCP errors travel inside a *successful* outer response (RFD `:135-174`). Outer ACP errors cover binding failures only: `-32602`, `-32800`, `-33000`, `-33001` (server registration unavailable), `-33002` (RFD `:180-186`).

The notification goes client→agent and carries the same `serverId`/`requestId`/`method`/`params` with no `id` (RFD `:204-227`). The schema has it only in `ClientNotification`. RFD `:31-34`: "An agent-to-provider request … A provider-to-agent notification". RFD `:38`: "There are no provider-originated MCP requests."

On gating and timing:

- The client checks the agent capability, then declares the server (RFD `:42`).
- "The provider must be ready to serve requests when it publishes the declaration. An agent may invoke tools or discover the server before returning the ACP session ID." (RFD `:59`)
- "If no provider can resolve the ID, the final recipient returns the binding's server-unavailable error." (RFD `:61`) and "Unknown servers … receive errors" (RFD `:257`).

The RFD therefore models an unknown `serverId` as a runtime error path, not a forbidden send. That is natural in proxy chains, where the agent cannot know which hop owns an ID.

**Implication for a direct client↔agent connection with no `acp` declaration:** the agent cannot legitimately know any `serverId`. Sending `mcp/message` is then nonsensical, but no MUST/SHOULD forbids it.

**Implication of the agent capability:** `capabilities.session.mcp.acp` is the agent's claim that it *consumes* declarations. Nothing requires an agent to advertise it before sending `mcp/message`. The client MUST NOT (by R11 spirit and RFD `:42`) declare `type: "acp"` servers to an agent that did not advertise it. So in practice "no advertisement ⇒ no declaration ⇒ no `mcp/message`", but only as a chain of implications.

### Q3: How the TCK currently treats it

**`ACP-CLIENTCAP-202`** (`src/tck/v2/requirements.py:365-379`; test `src/tck/v2/conformance/test_client_capabilities.py:54-69`):
- It checks `m in CLIENT_METHODS | PROTOCOL_METHODS or m.startswith("_")` on method names only, for requests and notifications alike.
- `CLIENT_METHODS` comes from `meta.unstable.json` `clientMethods` (`src/tck/v2/protocol.py:169`), which now includes `mcp/message` (`meta.unstable.json:34`).
- So an agent's `mcp/message` request **and** an agent's `mcp/message` notification both PASS. Its citation `meta.unstable.json:31-37` now spans the `mcp_message` line.

**Mock client:**
- `initialize` sends `capabilities: {}` (`src/tck/v2/__init__.py:23`). No client MCP capability exists to advertise.
- `new_session` omits `mcpServers` entirely (`src/tck/v2/conformance/_helpers.py:199-204`), so no `acp` server is ever declared.
- `run_prompt` answers `session/request_permission` normally (`:900`). Any other agent request, `mcp/message` included, gets `-32601` and is recorded in `client_requests_seen` (`:914-922`). Other agent notifications are only recorded (`:925-928`).
- A client that does not implement the binding answering `-32601` is ordinary JSON-RPC. The RFD-exact answer for an unknown server would be `-33001`, but the mock client is not under test, so this is fine.

**`ACP-SCHEMA-001`** (full exchange, `src/tck/v2/conformance/test_initialize.py:224-290`):
- `validate_agent_message` is kind-aware. An agent-sent `mcp/message` *notification* matches only `(mcp/message, is_request=True)` in the `AgentRequest` map, so it is reported as "a request but was sent without an id" (`src/tck/v2/validation.py:295-306`).
- That catches the wrong-kind case, but only if it happens during that one test's turn.
- An agent `mcp/message` *request* with valid params passes SCHEMA-001.

**Existing capability-gated "MUST NOT send X" rows to mirror:**
- `ACP-CLIENTCAP-201` (elicitation; `requirements.py:352-363`, test `test_client_capabilities.py:40-51`, fixture `tests/fixtures/agents/v2/calls_elicitation_unadvertised.py`, CLI assertion `tests/v2/test_cli.py:508-509`).
- v1 predecessors: `ACP-CLIENTCAP-001/002/003` (`src/tck/v1/requirements.py:618-649`).

## Recommendation

**(a) New row, INFORMATIONAL:**
- **id:** `ACP-MCPACP-201`, or `ACP-CLIENTCAP-203` to sit beside 201/202.
- **tier:** `Tier.INFORMATIONAL`.
- **capability:** `"capabilities.session"`, same as 201/202. Do **not** gate on `capabilities.session.mcp.acp`: the rule concerns undeclared servers, and an agent that does not advertise `acp` is the case most worth recording.
- **Why INFORMATIONAL:** the only text is an RFD proposal plus a schema *description*, with no RFC 2119 keyword. The RFD itself defines an error path for unknown IDs. Upgrading to ADVISORY would be a defensible judgment call (the TCK's J-style), but there is no SHOULD to cite.
- **text:** "With a mock client that declares no `type: \"acp\"` MCP server in session setup, no `mcp/message` request is observed during a prompt turn. `serverId` must name a declared ACP MCP server; with none declared, the agent has no server to address. Recorded only: the draft specifies this solely via the MCP-over-ACP RFD and the schema's `serverId` description."
- **citation:**
  - `schema/v2/schema.unstable.json#/$defs/MessageMcpRequest/properties/serverId`
  - `schema/v2/schema.unstable.json#/$defs/McpServerAcp`
  - `schema/v2/schema.unstable.json#/$defs/McpCapabilities/properties/acp`
  - `docs/rfds/mcp-over-acp.mdx:31-34,42,59,61`
- **test:** add to `test_client_capabilities.py` and reuse `_agent_to_client_methods_seen`. Filter `turn.client_requests_seen` for `method == "mcp/message" and "id" in parsed`, and assert the list is empty. INFORMATIONAL means the result is reported and never affects the verdict.
- **fixture:** `tests/fixtures/agents/v2/calls_undeclared_mcp_server.py`, a copy of the conforming baseline.
  - During the turn it sends `{"jsonrpc":"2.0","id":"tck-mcp-1","method":"mcp/message","params":{"serverId":"undeclared","requestId":"r1","method":"tools/list"}}`, reads the `-32601`, then idles with `end_turn`.
  - It is schema-valid, so SCHEMA-001 and CLIENTCAP-202 PASS.
  - The CLI test asserts the new row is FAIL, the verdict stays conformant, and 201/202 PASS.

**(b) Tighten `ACP-CLIENTCAP-202` to be kind-aware:**
- The schema defines `mcp/message` agent→client as a request only (R2, R3). An agent notification with that name is not a defined agent→client notification. The extensibility MUST already backing 202 covers this, so 202 should check `(method, is_request)` rather than the name alone.
- Concretely:
  - A request must be in `CLIENT_METHODS - CLIENT_NOTIFICATIONS`, or be `_`-prefixed.
  - A notification must be in `CLIENT_NOTIFICATIONS | PROTOCOL_METHODS`, or be `_`-prefixed.
  - `CLIENT_NOTIFICATIONS` already exists: `src/tck/v2/protocol.py:179` = `AgentNotification` methods ∩ `CLIENT_METHODS`, which excludes `mcp/message`.
  - The test needs `"id" in entry.parsed` alongside the method.
- Add `tests/fixtures/agents/v2/sends_mcp_message_notification.py`. It sends an id-less `mcp/message` during the turn. Expected: FAIL 202 and FAIL SCHEMA-001, like the existing `test_cli.py:550` fixture pair.
- Update 202's text and citation: add `#/$defs/AgentRequest` and `#/$defs/AgentNotification`, with a note that `mcp/message` is request-only in this direction.

**(c) Other draft-only agent→client methods:** I diffed the stable and unstable v2 `AgentRequest`/`AgentNotification` envelopes. `mcp/message` (`MessageMcpRequest`) is the **only** draft-only agent→client method. There are no draft-only agent→client notifications. The other draft-only methods are all client→agent: `providers/*`, `session/fork`, `nes/*`, `document/*`, and the `mcp/message` notification. So no parallel gap exists for other methods. The legacy `mcp/connect`/`mcp/disconnect` are **not** in the draft; 202 already FAILs an agent that sends them.

## Testability notes

- **Observable:** agent→client `mcp/message` requests and notifications during a TCK-driven turn. `run_prompt` records both.
- **Conforming:** no `mcp/message` of either kind, since the TCK declares no server.
- **Non-conforming:**
  - A request to any `serverId` makes the INFORMATIONAL row FAIL (report-only).
  - An id-less `mcp/message` from the agent fails 202 (after the fix) and SCHEMA-001.
- **Session/new blind spot:** RFD `:59` allows `mcp/message` *during* `session/new`, before the response. The new row, like 201/202, only observes the prompt turn. An agent that probes during `session/new` would not be seen unless `new_session` records agent-originated traffic. Acceptable, but note it in the docstring.
- **Positive path (not recommended now):** a capability-gated positive test (declare an `acp` server when `session.mcp.acp` is advertised, then expect the agent to call it) is not deterministic. Whether the agent calls a tool depends on its model. At most, one could assert that `session/new` with an `acp` declaration succeeds. See Open questions.

## Discrepancies

1. **Orchestrator premise vs. schema.** There is no client capability `mcp.acp`. The capability is the agent's `capabilities.session.mcp.acp` (v2) or `agentCapabilities.mcpCapabilities.acp` (v1). `ClientCapabilities` (v2 unstable) has no MCP field.
2. **SDKs vs. draft schema.**
   - Both reference SDKs implement the **older stateful binding**, which `ef4613d` replaced: `mcp/connect`/`mcp/disconnect`, `connectionId`, and requests and notifications in **both** directions. Rust: `src/schema/v2_impls.rs:320,351,361,383`, pinned to schema crate 1.9.1. Python: `src/acp/agent/connection.py:313-334`.
   - The draft at `9af0e9f` allows only agent→client requests and client→agent notifications, keyed by `serverId`+`requestId`.
   - SDK-built agents that use MCP-over-ACP will emit messages the draft does not define, for example `mcp/connect`. They only do this when a server is declared, and the TCK never declares one, so cross-check baselines should be unaffected.
   - The RFD itself says the SDKs/schema must be released and coordinated before publication (`:330`).
3. **RFD vs. draft docs.** The RFD defines the `acp` transport, but `docs/protocol/v2/draft/session-setup.mdx:336-481` only describes stdio/HTTP. Its client-side "MUST verify capabilities" (`:450`) names only stdio/HTTP.

## Open questions

- What must an agent that does **not** advertise `session.mcp.acp` do when it receives a `type: "acp"` declaration in `session/new` (reject? ignore?). This would be a capability-conditional negative test on the agent's request handling. The Rust polyfill "rejects any native declaration that is nevertheless supplied" (`acp-rust-sdk md/mcp-bridge.md:83-84`), but that is SDK behavior, not spec.
- Should `new_session` (v2) record and answer agent-originated requests that arrive before the `session/new` response, given RFD `:59`? This is a harness question.
- Draft-only `session/update` variants (`compaction_summary_chunk`, `compaction_update`, `notice`, `plan_removed`) exist. Whether any is gated by a *client* capability, and so needs a "MUST NOT send unless advertised" row, was not investigated.
- Should v1 ever validate against `schema/v1/schema.unstable.json`? Out of scope; it only matters if an agent under v1 uses MCP-over-ACP.
