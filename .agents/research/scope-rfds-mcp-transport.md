# Scope: fully testing the MCP-over-ACP and Streamable HTTP/WebSocket RFDs (v1 and v2)

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (target, checkout
`agent-client-protocol-2`), diffed against base `3961af94`: `docs/rfds/mcp-over-acp.mdx`,
`docs/rfds/streamable-http-websocket-transport.mdx`, `docs/docs.json`, `docs/protocol/v{1,2}/draft/{transports,
session-setup,initialization,overview,extensibility}.mdx`, `schema/v{1,2}/schema{,.unstable}.json`. TCK @ `ceef9a8`
(`src/tck/v{1,2}/requirements.py`, `spec-tracker/maps/v{1,2}.toml`, `src/tck/v{1,2}/conformance/_helpers.py`,
`src/tck/common/harness/`, `docs/{requirements,spec-updates,harness,mock-client}.md`). acp-python-sdk @ `4fed584`,
acp-rust-sdk @ `6a4a95c` (both `pull --ff-only`, already current), only to check that HTTP/WS servers exist.
**Confidence:** high on what the sources state and on coverage. Medium on the tier calls (the RFD uses lowercase
"must" throughout, and the TCK has no convention for that) and on the MCP 2026-07-28 `_meta` keys (they come from the
external MCP spec, which I did not read).

## Answer

- **Nothing normative changed between base and target.** Both RFD files and every MCP-over-ACP `$def`
  (`McpServerAcp`, `McpServerAcpId`, `McpRequestId`, `MessageMcp{Request,Response,Notification}`, `McpError`,
  `McpCapabilities`, v2 `McpAcpCapabilities`) are byte-identical in both versions. The only change is
  `docs/docs.json`: both pages moved from the removed "Active" group into "Draft" (`docs/docs.json:200-206 @ 3ea94133`).
  As Draft RFDs they are no longer tracked (`docs/spec-updates.md` "Tracked RFDs"), so testing them fully is optional.
  The old rule applies: cite them only where nothing else states the rule.
- **MCP-over-ACP is feasible in a stdio TCK.** The agent is the MCP *consumer*: `MessageMcpRequest` sits in
  `AgentRequest` (agent -> client) and `MessageMcpNotification` in `ClientNotification` (client -> agent), in both
  unstable schemas. So the TCK's mock client plays the provider over the existing stdio connection. Effort is **M**
  for both versions together: about 7-8 rows per version, 13-14 fixtures, one shared provider module and two
  mock-client hooks. Every row SKIPs unless the agent advertises `acp`.
- **Streamable HTTP/WebSocket is out of scope for a stdio TCK.** Every agent-side rule is a server-side HTTP/WS rule.
  Testing them needs a new HTTP/2+SSE and WebSocket client harness and an endpoint the operator supplies. The spec
  defines no way to locate a remote agent, and the docs still say stdio is the only defined transport
  (`transports.mdx:8` in both versions). A transport-only suite would be **L** (about 16 rows per version, about 10
  fixtures plus an HTTP/2+WS fixture server, three new dependencies). Running the whole suite over HTTP/WS would be
  **XL**. Recommendation: do not build it, and add no ledger entries for it (see Decisions).

## Summary table

| RFD / version | agent-side rules | covered | docs/schema-stated, uncovered | RFD-only testable | RFD-only ledger | effort |
|---|---|---|---|---|---|---|
| mcp-over-acp / v1 | 16 | 2 | 4 | 6 | 4 | M (8 rows + 1 optional, 7 fixtures, shared provider + 2 hooks) |
| mcp-over-acp / v2 | 17 | 4 | 4 | 5 | 4 | S-M given v1 (7 rows + 1 optional + 1 optional probe, 7 fixtures, reuses provider) |
| streamable-http-ws / v1 | 17 | 1 (ledger) | 0 | 16 (all need an HTTP/WS harness) | 0 today | L if built; recommend out of scope |
| streamable-http-ws / v2 | 17 | 1 (ledger) | 2 partial (batch body, `transports.mdx:67`) | 14 (plus the HTTP status half of 2) | 0 today | L if built; recommend out of scope |

"Covered" means an existing row or ledger entry already accounts for the rule.

---

## 1. MCP-over-ACP (`docs/rfds/mcp-over-acp.mdx`, Draft at target, was Active)

The agent's role: in the direct client-agent topology the client (here, the TCK) is the provider, and the agent sends
`mcp/message` requests and receives `mcp/message` notifications. Rules that bind providers, proxies and intermediaries
are excluded because they are not agent-side: server-ID generation and lifetime (57-63), provider readiness (59),
binding error codes (178-188), discovery `supportedVersions` (192), notification stop and subscription
acknowledgement (227-233), honoring cancellation (251-255), proxy ID preservation (249, 271), and advertising only
when the downstream chain supports it (97). The RFD requires the same semantics in both versions (328).

The gates are real: v1 `agentCapabilities.mcpCapabilities.acp` (boolean, `schema/v1/schema.unstable.json#/$defs/McpCapabilities`);
v2 `capabilities.session.mcp.acp` (object, `docs/protocol/v2/draft/initialization.mdx:441-446`,
`schema/v2/schema.unstable.json#/$defs/McpCapabilities`).

### Agent-side rules

| # | Rule (RFD line) | v1 status | v2 status |
|---|---|---|---|
| A1 | Capability shape: v1 `acp: true`, v2 `acp: {}`; omitted (and `null` in v2) means not advertised (67-95) | schema-stated (`McpCapabilities.acp`); **covered** generically by ACP-SCHEMA-001 on `initialize` | docs+schema (`initialization.mdx:441-446`); **covered** by ACP-SCHEMA-001 |
| A2 | Reject an `acp` server the agent did not advertise | n/a: v1 docs, schema and RFD state no rejection rule | docs `session-setup.mdx:634` (was 545); **covered** by ACP-MCP-203 (`acp` probe) |
| A3 | Accept an `acp` declaration when advertised (implicit in 42-59; no normative sentence) | RFD-only, implicit → INFORMATIONAL row | same → INFORMATIONAL row (analogue of ACP-MCP-201/202) |
| A4 | `mcp/message` request: required non-null string `serverId`/`requestId`/`method`; `params` is an object or null, never an array (196-198) | schema-stated (`$defs/MessageMcpRequest`); uncovered: no flow makes the agent emit one. Once a flow exists, ACP-SCHEMA-001/002 validate it automatically | same |
| A5 | `serverId` addresses a declared server (103; schema: "The declared ACP MCP server receiving this request") | schema-stated (`MessageMcpRequest/properties/serverId`), uncovered | same |
| A6 | Fresh `requestId` for each operation, including an MRTR retry; never reuse an active ID for the same server on the same connection (196, 265) | RFD-only, testable | RFD-only, testable |
| A7 | Inner `params._meta` carries the required MCP 2026-07-28 metadata (`io.modelcontextprotocol/protocolVersion`, ...); outer `_meta` is ACP-only (11, 120-126, 198-202, 298) | RFD-only, testable | RFD-only for the required metadata. The separation half is schema-stated (`MessageMcpRequest/properties/_meta`: "This is ACP metadata, not the inner MCP message's `_meta`") |
| A8 | No MCP `initialize` handshake. After an inner `-32022` the agent does not fall back to `initialize` or an earlier revision (11, 190, 202) | RFD-only, testable | RFD-only, testable |
| A9 | Inner error codes are MCP codes, never ACP: an inner `-32000` must not trigger ACP authentication, and overload is never reported as auth-required (172, 188) | schema-stated (`$defs/McpError/properties/code`: "Never an ACP error code"), uncovered. The RFD adds the `-32000` example | same |
| A10 | Receiver ignores unknown carrier fields, prefers `result` when both keys are present, and treats null or invalid carrier `_meta` as absent (174) | schema-stated (`$defs/MessageMcpResponse` description), uncovered. Only "keeps working" is observable | same |
| A11 | A consumer must not deliver unknown or late notifications to a different operation (225) | RFD-only, **ledger** (unobservable) | same |
| A12 | An `mcp/message` notification gets no response, and a malformed one gets no synthetic reply (225, 257) | docs `overview.mdx:242` (was 239); **covered** by ACP-JSONRPC-003 and, for agents that do not advertise `acp`, ACP-EXT-002 | docs `overview.mdx:231`; **covered** by ACP-JSONRPC-003 and ACP-EXT-002 |
| A14 | MRTR: after `input_required`, a fresh request with `inputResponses`, the exact opaque `requestState` and its own metadata (263-267) | RFD-only, testable only through a model-driven `tools/call` | same |
| A15 | The transport must not parse retry state, auto-approve an elicitation, or replay side-effecting calls without the agent's policy (265) | RFD-only, **ledger** (internal policy) | same |
| A16 | Transport EOF starts cancellation, and the agent must not wait indefinitely on a future awaiting the disconnected peer (257) | RFD-only (v1 docs state no shutdown rule; ACP-SHUTDOWN-001 is INFORMATIONAL), testable | docs-stated generally (`transports.mdx:43` SHOULD exit); **covered** by ACP-SHUTDOWN-001. A probe with an `mcp/message` pending is optional |
| A17 | Bound buffering and outstanding work; never block unrelated dispatch on a slow consumer; fail explicitly instead of dropping events (259) | RFD-only, **ledger** (unsafe/unobservable) | same |
| A18 | Optional embedded HTTP adapter: batches, 405, header and Origin checks, loopback, no legacy fallback, no credentials in traces (273-292, 298) | RFD-only, **ledger** (the adapter's endpoint never crosses the ACP connection) | same |

These are excluded from the counts. A13: an agent MAY cancel an `mcp/message` with `$/cancel_request` and the outer
ID (237-249). Cancelling is a MAY, and the ID semantics are the docs' general `$/cancel_request` rule. A20: the
intermediary advertising rule (97) is not agent-side.

### Proposed rows (provisional ids: v1 `ACP-MCPACP-0xx`, v2 shares the ids under rule B; a v2-only rule would be `2xx`)

All rows use the real gate except INFORMATIONAL ones. Each test: advertise nothing extra; send `session/new` with
`mcpServers: [{"type":"acp","name":"tck-tools","serverId":"tck:<random>"}]`; serve `mcp/message` during `session/new`
and during one prompt turn; SKIP ("agent sent no `mcp/message`") when nothing arrived. Rule 59 lets the agent call the
server before it returns the session ID, so serving during `session/new` is required to avoid a deadlock.

| Row | Text (short) | Tier | Citation | Test / FAIL condition |
|---|---|---|---|---|
| A3 | Records whether `session/new` with an `acp` server succeeds when advertised, and whether any `mcp/message` followed | INFORMATIONAL | RFD 42-59 (Draft RFD) + `$defs/McpServerAcp` | never asserts |
| A4 | (no new row) bind the flow's transcript to ACP-SCHEMA-001/002 | existing | schema | schema validation of each agent `mcp/message` |
| A5 | Every `mcp/message` request names a declared `serverId` | ADVISORY (schema, no keyword) | `$defs/MessageMcpRequest/properties/serverId` | FAIL on an undeclared ID; the provider answers it with outer `-33001` |
| A6 | `requestId` unique per operation on the connection for a server | CAPABILITY or ADVISORY (decision 1) | RFD 196, 265 (Draft RFD) | FAIL on any repeat. SKIP with fewer than 2 requests. The provider delays replies slightly to make overlap likely |
| A7 | Inner `params._meta` is present with string `io.modelcontextprotocol/protocolVersion` (value `2026-07-28`), not carried in outer `_meta` | CAPABILITY or ADVISORY (decision 1) | RFD 11, 198, 202 (Draft RFD); v2 also `MessageMcpRequest/properties/_meta` | FAIL if missing, or present only in outer `_meta` |
| A8 | No inner `initialize` / `notifications/initialized`. After a carrier `-32022` reply, no retry with `initialize` or a different version on that server | ADVISORY (no keyword) | RFD 11, 190, 202 (Draft RFD) | passive check on every flow, plus an active probe: the provider answers the first request with `{"error":{"code":-32022,...}}` |
| A9 | An inner `-32000` (carrier) or outer `-33000` never surfaces as `-32000` on the agent's `session/new` / `session/prompt` | ADVISORY (schema, no keyword) | `$defs/McpError/properties/code`; RFD 172, 188 as context only if the user keeps it | baseline: the same request without the server succeeded. Probe: the provider answers every request with a carrier `-32000`. FAIL on a `-32000` reply. SKIP if no `mcp/message` arrived during that request |
| A10 | The agent stays usable after a carrier with both keys, an unknown field and `_meta: 5` | ADVISORY | `$defs/MessageMcpResponse` | FAIL if it exits or stops answering; a later `session/new` must succeed |
| A14 (optional) | MRTR retry uses a fresh `requestId` and echoes `requestState` exactly | ADVISORY | RFD 263-265 (Draft RFD) | needs a new `--mcp-tool-prompt` option and the provider returning `input_required` on `tools/call`. SKIPs unless the model calls the tool |
| A16 (v1 only) | With an `mcp/message` left unanswered, closing stdin still lets the agent exit within the grace period | ADVISORY (recommended; implementation guidance) | RFD 257 (Draft RFD) | the provider holds the reply, then the close ladder runs. FAIL if a signal was needed |

Ledger, per version, 4 entries citing `docs/rfds/mcp-over-acp.mdx:<line> (Draft RFD)`:
- A11 (225): "Not observable: which internal operation a notification reaches is invisible on the wire."
- A15 (265): "Not observable: the agent's retry and approval policy is internal."
- A17 (259): "Unsafe and not observable: proving the bounds needs flooding the agent, and queue growth is internal."
- A18 (273-292, 298): "Not observable: an embedded HTTP adapter's loopback endpoint, its URL and its credentials
  never cross the ACP connection."

None of these reasons rests on a TCK choice.

### Harness and fixtures

- **Shared provider (new, `src/tck/common/`, version-agnostic).** The JSON shapes are identical in v1 and v2 (RFD
  306). It answers `server/discover` (`supportedVersions: ["2026-07-28"]`), `tools/list` (one echo tool) and
  `tools/call`, and replies outer `-33001` for unknown server IDs. It records each request (outer ID, `serverId`,
  `requestId`, inner method, `_meta`, active overlap). Modes: normal, inner-error (`-32000`), unsupported-version
  (`-32022`), odd-carrier (A10), hold (A16), and optionally `input_required` (A14).
- **Mock-client hooks, per version.**
  1. A `new_session` variant that serves `mcp/message` (and answers other agent requests with `-32601`) while it waits
     for the response. Today `new_session` just waits (`src/tck/v1/conformance/_helpers.py:148-167`).
  2. `run_prompt` and `answer_post_turn_requests` route `mcp/message` to the provider instead of answering `-32601`.
  3. `docs/mock-client.md` must document both.
- **Fixtures, per version.** One conforming consumer (or an extension of `conforming_full.py`), plus defects:
  `reuses_mcp_request_id`, `omits_mcp_meta` (or puts it in outer `_meta`), `mcp_inner_initialize` (falls back after
  `-32022`), `mcp_inner_error_as_auth`, `mcp_undeclared_server_id`, `crashes_on_mcp_carrier_extras`, and for v1
  `hangs_on_eof_with_pending_mcp`. That is 7 for v1 and 6-7 for v2, plus the `test_cli.py` id sets.
- **Stop condition (granular-work).** This is two or three slices: the provider plus hooks, then the v1 rows, then the
  v2 rows. It is not one slice.

### Citation justification (Draft RFD)

- **Justified** for A3, A6, A7, A8, A14, A16 (v1) and the four ledger entries, because nothing else states them. v2's
  docs defer to the RFD for this feature (`overview.mdx:255` "Where the draft pages don't describe a feature yet, its
  RFD is the reference"; row `:266`; `initialization.mdx:441-446`; `session-setup.mdx:634`). v1 has only the schema
  types, so for v1 too the RFD is the only source. Label every citation `(Draft RFD)`.
- **Not justified** for A4/A5/A9/A10: the schema states them, so cite the schema pointers only.
- **Existing citations.** ACP-JSONRPC-003 cites `docs/rfds/mcp-over-acp.mdx:225,257 (Active RFD)` in v1
  (`requirements.py:86`) and v2 (`requirements.py:1554`). The docs (v1 `overview.mdx:242`, v2 `overview.mdx:231` at
  target) and `$defs/MessageMcpNotification` state the same rule, so the strict reading says drop the RFD citation.
  The alternative is to relabel it `(Draft RFD)`. ACP-EXT-002 and ACP-MCP-203 do not cite the RFD.
- **Ledger.** No existing ledger entry cites this RFD. The entries about the TCK's MCP stub (v1/v2 `session-setup`
  headers/origin; v2 `extensibility.mdx:102`, `content.mdx:18,20`, `elicitation.mdx:54`, `session-setup.mdx:549,607,626`)
  cite docs about stdio/http MCP servers. They stay as they are. An ACP-transport provider would remove the
  subprocess, but `content.mdx`/`extensibility.mdx:102` would still need the model to call a tool.

---

## 2. Streamable HTTP & WebSocket transport (`docs/rfds/streamable-http-websocket-transport.mdx`, Draft, was Active)

The agent (or its host) is the HTTP/WS **server**. Client rules are excluded: both profiles (17), cookies (49), WS
`initialize` first (289), `Acp-Protocol-Version` SHOULD (416). The "servers MAY support only WebSocket" rule (17, 364)
is a MAY. It still matters: HTTP and WS rows would need separate gates.

### Agent-side rules (same list for v1 and v2; the RFD targets v1 and leaves v2 reliability to future work, 68-88)

| # | Rule (RFD line) | Status |
|---|---|---|
| H1 | `initialize` POST without `Acp-Connection-Id` → 200 with JSON body and an `Acp-Connection-Id` response header (37, 55, 139-141, 308) | RFD-only |
| H2 | Every other accepted POST → 202, empty body; the response arrives on a GET stream, correlated by `id` (37, 55, 312) | RFD-only |
| H3 | Streamable HTTP MUST use HTTP/2 (39, 272) | RFD-only |
| H4 | GET with `Acp-Connection-Id` → connection-scoped SSE; adding `Acp-Session-Id` → session-scoped SSE (56, 270, 304-305) | RFD-only |
| H5 | Routing: `session/new`/`session/load` responses and non-session messages go on the connection stream; updates, agent requests and session-scoped responses go on the session stream (35, 339) | RFD-only |
| H6 | POST with a non-`application/json` Content-Type → 415 (267) | RFD-only |
| H7 | GET whose Accept lacks `text/event-stream` → 406 (268) | RFD-only |
| H8 | GET: missing connection ID → 400; unknown connection → 404; unknown session → 404 (270, 301-303) | RFD-only |
| H9 | POST: missing connection ID → 400; unknown connection → 404; session-scoped POST without `Acp-Session-Id` → 400 (269, 309-311) | RFD-only |
| H10 | DELETE with a connection ID terminates the connection and its sessions, returns 202 and closes the streams; without one → 400 (58, 259-262, 315-316) | RFD-only |
| H11 | JSON-array POST body → 400 plus a single `-32600`, `id: null`, nothing processed (271, 366) | v1: RFD-only. v2: the JSON-RPC half is docs-stated (`transports.mdx:67`) and covered on stdio by ACP-BATCH-209; the 400 is RFD-only |
| H12 | WS upgrade → 101 with `Acp-Connection-Id`; each upgrade is a new connection (43, 57, 284-289) | RFD-only |
| H13 | WS: one JSON-RPC message per text frame; binary frames ignored (293) | RFD-only |
| H14 | WS: an array frame gets a single `-32600`, `id: null`, nothing processed (293) | as H11 (v2 docs-stated half, `transports.mdx:67`) |
| H15 | WS: on disconnect the server cleans up the connection and its sessions (293) | RFD-only; conflicts with 74 (see Discrepancies) |
| H16 | Same JSON-RPC format and lifecycle as stdio (19, 62) | docs: custom transports MUST preserve them (v1 `transports.mdx:45`, v2 `:73`); **covered** by ledger (v1.toml:212 `transports.mdx:10,45`; v2.toml `transports.mdx:10,71,73`) |
| H17 | v1 expectation: sessions survive a disconnect and can be resumed on a new connection (74) | RFD-only, descriptive ("you can expect") |

### If it were built (not recommended)

- **Tier.** No `initialize` marker exists, because the transport is chosen before `initialize`. Use
  `inferred:streamableHttp` and `inferred:websocket` gates: the operator supplies a URL and the test SKIPs when that
  profile is not served, as the WS-only MAY requires. H3 and H6/H7 (their sentences carry MUST) → CAPABILITY. The
  keyword-less routing and status rules → ADVISORY by the ACP-MCP-204 convention, or CAPABILITY by decision 1.
- **Harness.**
  - A remote-connection abstraction beside `AgentProcess`: send, read, transcript; no stderr and no exit code.
  - `--agent-url` (and `--transport http|ws`), because the spec gives no way to launch or discover a remote agent.
  - An HTTP/2 client with an SSE parser (`httpx[http2]` plus `h2`; h2c with prior knowledge for `http://`).
  - A WebSocket client (`websockets`).
  - Report changes: `agent_command` becomes optional; the stdio-only rows (ACP-TRANSPORT-001/002/203) become N/A.
- **Fixtures.**
  - A conforming HTTP/2+WS fixture server bridging to the stdio `conforming.py`. It needs Hypercorn: uvicorn has no
    HTTP/2.
  - About 10 defect variants: initialize answered 202; missing connection header; 200 for an unknown connection;
    batch answered 501 (the Python SDK's current behavior); HTTP/1.1 only; session update on the connection stream;
    binary frame answered; array processed; DELETE leaves streams open; 404/400 swapped.
- **Size.** About 16 rows per version, sharing one driver in `src/tck/common/` → **L**. Running the existing suite
  over HTTP/WS means refactoring every helper off `AgentProcess` → **XL**.
- **Reference implementations.** The Python SDK ships an ASGI HTTP and WS server (`src/acp/http/server.py`,
  `src/acp/ws/server.py`) and the Rust SDK documents an HTTP transport (`md/http-transport.md`), so a real target
  exists.

### Why out of scope, and citation justification

- **Out of scope.** Both versions' docs say "The protocol currently defines one transport mechanism ... stdio" and
  that the remote transport "is being specified" (`transports.mdx:8`). The RFD is Draft and untracked, and it is still
  moving: five structural revisions in 2026 (422-431), with Phase 4 hardening (Origin, `Acp-Protocol-Version`,
  resumability) still to come (374). The Python reference already diverges (Discrepancies 5). The TCK is defined as a
  stdio launcher (`CLAUDE.md`, `docs/harness.md`).
- **Citations.** No row cites the RFD today. It would be justified only if a transport suite were built, because
  nothing else states these rules.
- **Existing ledger reasons.** The two "custom transports" entries (v1.toml:212-214; v2.toml `transports.mdx:10,71,73`)
  say "the TCK only launches agents over stdio". That is a TCK choice, which `docs/requirements.md` forbids as a
  reason. Reword them to name the real blocker, for example: "Deferred: no remote transport is defined by the docs; a
  custom transport needs an operator-supplied endpoint and a client for it." The same applies to v2.toml's
  `transports.mdx:61` (message order): "not observable on stdio" stops holding over HTTP/2's separate streams.

## Discrepancies

1. **`connectionId` in the body vs extensibility.** The RFD puts `connectionId` in the `initialize` result body
   (139, 232, 361). The docs forbid custom root fields (v1 `extensibility.mdx:43`, v2 `extensibility.mdx:107`), and
   `InitializeResponse` has no such property in either schema. Docs win: the header is the only carrier.
2. **No `initialized` message.** The RFD's lifecycle "`initialize` → `initialized` → messages" (62): neither schema
   defines `initialized`.
3. **`session/load` in v2.** The RFD resumes with `session/load` (35, 74, 244-255), but v2 has only `session/resume`
   (v2 unstable schema). Docs win for v2.
4. **Sessions on disconnect (inside the RFD).** WS disconnect "cleans up ... any associated sessions" (293) and
   DELETE terminates "all associated sessions" (315), yet "Sessions survive disconnects" (74). v2 docs: at the end of a
   connection, sessions stop being active (`transports.mdx:43`) but exist until the agent discards them
   (`session-setup.mdx:48`).
5. **Python SDK batch status.** `acp-python-sdk` `src/acp/http/server.py:259` answers a batch with 501. Since the
   2026-10-30 revision (424) the RFD requires 400 plus `-32600`.
6. **MCP-over-ACP.** No conflict between the RFD, the schema and the docs on agent-side rules. A2 (reject an
   unadvertised `acp`) is stated in v2's docs only. v1 states no rejection rule, so v1 has no ACP-MCP-203 analogue.
   That is a gap, not a conflict.

## Decisions for the user

1. **Lowercase "must" in RFD-only rules** (A6, A7; transport routing). The RFD never uses RFC 8174 uppercase for
   agent rules; the only uppercase MUST is at 174, and it binds senders/providers. Options:
   - CAPABILITY behind `acp`: affects the verdict for agents that advertise it.
   - ADVISORY: strict keyword reading, consistent with ACP-MCP-204.
   Recommendation: ADVISORY. The RFD is Draft and unstable, and its own text says the schema must be released and SDKs
   coordinated before publication (330).
2. **Build MCP-over-ACP rows now?** Recommendation: yes but low priority, as two or three slices (provider plus hooks,
   v1, v2). Real agents that advertise `acp` are likely rare, so expect mostly SKIPs. A14 (MRTR) should wait unless a
   `--mcp-tool-prompt` option is wanted.
3. **Streamable HTTP/WS.** Recommendation: out of scope, with no rows and no ledger entries. Sixteen "Deferred"
   entries per version for an untracked Draft RFD would be noise. Fix the two "custom transports" ledger reasons
   instead.
4. **ACP-JSONRPC-003's RFD citation (v1, v2).** Recommendation: drop it, since the docs state the rule. The
   alternative is to relabel it `(Draft RFD)`.

## Open questions

- **MCP 2026-07-28 required `_meta` keys.** The external MCP spec defines which keys A7 should require. Until someone
  checks it, the proposal only requires `io.modelcontextprotocol/protocolVersion`.
- **v1 "SHOULD connect to all MCP servers"** (`docs/protocol/v1/draft/session-setup.mdx` "Checking transport
  support", ACP-SESSION-004). Does it reach `acp` servers? There is no handshake to observe, and "sent any
  `mcp/message`" is a stretch. This is for the v1 doc audit.
- **Line moves for the doc audit** (citation-only): ACP-MCP-203 `session-setup.mdx:545,553` → `634,636`;
  ACP-JSONRPC-003 v1 `overview.mdx:239` → `242`, v2 `overview.mdx:227` → `231`.
- **`mcp/message` sent as a request to the agent.** The schema has no client -> agent `mcp/message` request. An
  optional probe would extend ACP-JSONRPC-004 or ACP-EXT-001: unknown method → `-32601`. No rule is specific to it.
