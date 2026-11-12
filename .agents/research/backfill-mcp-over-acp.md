# What does the Active RFD `mcp-over-acp` require of an agent, and how well does the TCK cover it (v1 and v2)?

**Sources checked:**
- `check-specification`: `agent-client-protocol` at **3961af94fa62d2386d993cadf1afc8b146fc799a** (the TCK pin, 2026-11-10) and `upstream/main` **c392d7e9d1de01337b749c0070929933e9f6f09f** (fetched 2026-11-12). Read only with `git show <rev>:<path>`. The checkout's working tree (HEAD 94d7666d) was not touched. Citations below are at 3961af94 unless stated.
- `check-rust-sdk`: `acp-rust-sdk` @ 91d368a (v5.2.0, 2026-11-10). `check-python-sdk`: `acp-python-sdk` @ da202e0 (2026-11-12). Both were `Already up to date`.
- TCK: `acp-tck` @ b1b951b with the dirty tree as given (no MCP-over-ACP files are modified).

**Confidence:** high on what the RFD, docs and schema say and on what the TCK has today (all grepped and read). Medium on two tier calls (R3 and R17). They are marked as judgment calls below.

**Difference between the two revisions:** none for this feature. `docs/rfds/mcp-over-acp.mdx` is byte-identical (`git diff --quiet` passes). The `Mcp*`/`MessageMcp*` defs in `schema/v{1,2}/schema.unstable.json` are unchanged. The only MCP-related edits in the range are unrelated `session/options` sentences ("SHOULD NOT connect to MCP servers"). The RFD's last upstream touches are 83626637 and ef4613d3, both already in 3961af94.

## Answer

The RFD is in the **Active** group at the pinned revision (`docs/docs.json:211` group `Active`, `:215` `rfds/mcp-over-acp`; at upstream/main `:212`/`:216`). Its wire shapes exist **only in `schema/v{1,2}/schema.unstable.json`**. Neither stable `schema.json` nor `meta.json` contains `mcp/message`, `MessageMcp*`, `McpServerAcp` or `McpAcpCapabilities`.

The protocol is agent-as-caller. The agent is the consumer that sends `mcp/message` requests to the client (the provider) and receives `mcp/message` notifications back. Everything the agent must do is behind the capability `agentCapabilities.mcpCapabilities.acp` (v1) or `capabilities.session.mcp.acp` (v2), plus one unconditional MUST that is already in the v2 docs.

**TCK coverage is essentially zero.**
- No row, test or fixture exercises an `acp` MCP server in either version.
- v1 has no `ACP-MCP-*` rows at all.
- v2's `ACP-MCP-203` probes `sse` and `_tck_unsupported_transport`, but never `acp`.
- There is no ledger entry for this RFD in `spec-tracker/maps/v{1,2}.toml`.
- Nothing in the TCK ever declares an `acp` server, so no agent is ever driven to send `mcp/message`.
- Several existing MCP ledger entries give reasons that rest on a TCK choice ("the TCK does not host an MCP server"), which this RFD's transport makes untrue (section "Mapping").

## Requirements

Tier column is the tier the policy gives. "Docs" means the draft protocol docs or the schema also state it (docs decide). "RFD-only" means capped at CAPABILITY or ADVISORY. All RFD citations are `docs/rfds/mcp-over-acp.mdx:<line>` (Active RFD, stage per `docs/docs.json:211`).

| # | Requirement (agent side) | Tier under policy | Citation |
|---|---|---|---|
| R1 | Capability shape. v1: `agentCapabilities.mcpCapabilities.acp` is a boolean, omission means false. v2: `capabilities.session.mcp.acp` is `{}`, or omitted/`null` for unsupported, never a boolean. | Schema shape rule, so follows the schema (existing generic rows) | RFD:65-99; v1 `schema.unstable.json#/$defs/McpCapabilities/properties/acp` (:2747); v2 `#/$defs/McpCapabilities/properties/acp` (:3377), `#/$defs/McpAcpCapabilities` (:3421); v2 `docs/protocol/v2/draft/initialization.mdx:347-352` |
| R2 | An agent that does not advertise `acp` MUST reject a `type: "acp"` server in a session-setup request with `-32602`. | v2: follows the docs MUST, same tier as `ACP-MCP-203` (CAPABILITY on `capabilities.session`). v1: INFORMATIONAL, spec silent on the agent's answer | v2 `docs/protocol/v2/draft/session-setup.mdx:545` ("MUST reject a request with a transport they don't support with `-32602`, including a transport they did not advertise"); v2 `McpServer` "other" variant description (`schema.unstable.json` :8325 region); v1: `McpServer` acp variant "Only available when the Agent capabilities indicate `mcp_capabilities.acp` is `true`" (v1 `schema.unstable.json` :7067) binds the client only; v1 `session-setup.mdx:476-482` and `:628-648` say nothing about rejecting |
| R3 | An agent that advertises `acp` accepts a well-formed declaration `{type:"acp", name, serverId}` in `session/new` (and resume/load/fork). The declaration is a reference, not an allocation, so nothing has to be launched. | CAPABILITY (v1 `agentCapabilities.mcpCapabilities.acp`, v2 `capabilities.session.mcp.acp`). **Judgment call:** no keyword states it. It is implied by the capability meaning "the Agent supports the `acp` MCP server transport". The alternative is INFORMATIONAL like `ACP-MCP-201/202` | RFD:42-63; v2 `initialization.mdx:347-352`; `#/$defs/McpServerAcp` (v1 :7172, v2 :8423; required `name`, `serverId`); v2 `session-setup.mdx:545` |
| R4 | The agent MAY invoke or discover the server before returning the session id. | MAY. A constraint on the TCK's provider, not a test | RFD:59 |
| R5 | Every `mcp/message` request the agent sends has required non-null strings `serverId`, `requestId`, `method`. `params` is an object or `null` or omitted (no positional arrays). Outer `_meta` is an object or `null`. | Shape follows the schema (generic schema validation); never triggered today | RFD:194-200; v1 `#/$defs/MessageMcpRequest` (:2247-2285, `x-side: client`); v2 same (:2703-2741) |
| R6 | `serverId` addresses only a server the client declared. An unknown id is an error at the final recipient (`-33001`). | CAPABILITY (RFD-only) | RFD:57,61,257 |
| R7 | `requestId` is fresh per operation, including each MRTR retry. It is never reused while active for the same server on the connection (a duplicate active id is `-32602`). It is the inner JSON-RPC id, not the outer id. | CAPABILITY (RFD-only) | RFD:24,133,184,196,265 |
| R8 | Inner `params._meta` carries `io.modelcontextprotocol/protocolVersion: "2026-07-28"` and `io.modelcontextprotocol/clientCapabilities` on each request. `clientInfo` appears in the RFD example but is not stated as required. The full MCP-side required set is in the external MCP 2026-07-28 spec (not checked). | CAPABILITY (RFD-only) | RFD:27,115-127,198,202; Rust SDK `md/mcp-over-acp.md` "Calling a server" |
| R9 | No MCP initialization handshake: the agent sends no inner `initialize` / `notifications/initialized` or connect/disconnect. With no mutual version it surfaces `UnsupportedProtocolVersion` (`-32022`) instead of falling back to `initialize` or an older revision. | CAPABILITY (RFD-only) | RFD:11,38,190,202,336 |
| R10 | Outcome carrier handling by the agent. The inner `error` branch is an MCP outcome, not an ACP error (an inner `-32000` must not trigger ACP auth). `result` may be any JSON value including `null`. If both keys are present, prefer `result`. Unknown outer fields are ignored. Carrier `_meta` that is `null` or invalid is treated as absent. An `isError` tool result stays a result. | CAPABILITY (RFD-only). Observable only after the agent calls a tool | RFD:156-174,188; v1 `#/$defs/MessageMcpResponse` (:8316-8360), `#/$defs/McpError` (:8362); v2 (:9519-9563, :9565) |
| R11 | Outer ACP errors (`-32602` malformed or duplicate, `-32800` cancelled, `-33000` limit, `-33001` unavailable, `-33002` backend failed) describe binding failures. The agent must not turn overload into an auth-required error. | CAPABILITY (RFD-only). Low observability | RFD:176-188 |
| R12 | Notifications to the agent. An `mcp/message` notification has no JSON-RPC id and gets **no response**. Unknown or late notifications must not be delivered to another operation. Malformed notifications get no synthetic reply. | "No response" half is CAPABILITY (RFD-only; the generic JSON-RPC silence rule exists but does not cover this defined method). "No cross-delivery" is not observable | RFD:225,227,257; v1 `#/$defs/MessageMcpNotification` (:8457-8495, `x-side: agent`); v2 (:9660-9698) |
| R13 | Subscription correlation. `subscriptions/listen` is one long-lived request. Its notifications carry `io.modelcontextprotocol/subscriptionId` equal to the listen `requestId`. | Not observable agent-side (internal routing). Provider rules | RFD:229-233 |
| R14 | MRTR. On `resultType: "input_required"` the agent retries with a fresh `requestId`, `inputResponses` and the exact opaque `requestState`. It must not parse the state, auto-approve an elicitation or replay side effects without policy. | CAPABILITY for the retry-shape part, once a retry is seen (a retry is not mandated). The "no auto-approval" part is policy-internal and not observable | RFD:261-267 |
| R15 | Cancellation. The agent MAY cancel an outstanding `mcp/message` with `$/cancel_request` carrying the **outer** request id of that hop (never the logical `requestId`). Cancelling one operation does not cancel siblings. | v2: ADVISORY, docs state the generic SHOULD that a sender who stops waiting sends `$/cancel_request`. v1: MAY only, no docs SHOULD | RFD:237-251; v2 `docs/protocol/v2/draft/cancellation.mdx:31`; v1 `cancellation.mdx` has no such SHOULD (:14-35) |
| R16 | The agent sends `mcp/message` only for a declaration the client made. A TCK run that declares nothing should see zero `mcp/message`. | CAPABILITY (RFD-only; the general negotiation MUST in `extensibility.mdx:21-25` is about peer capabilities, so only supports it by analogy) | RFD:42-63; v2 `docs/protocol/v2/draft/extensibility.mdx:21,25` |
| R17 | Docs-wide SHOULD: "Agents SHOULD connect to all MCP servers specified by the Client". For `acp` this means the agent sends at least one `mcp/message` (for example `server/discover` or `tools/list`) for a declared server during a turn. **Judgment call:** "connect" is ill-defined for `acp`, and discovery "is not a prerequisite". | ADVISORY (docs SHOULD) | v1 `session-setup.mdx:650`; v2 `session-setup.mdx:685`; RFD:190 |
| R18 | On `session/resume` and `session/fork`, `mcpServers` is the complete set, and agents SHOULD NOT restore earlier servers. The same applies to `acp` servers. | ADVISORY (docs SHOULD NOT), v2 only. Observable only if the agent calls a stale server | v2 `session-setup.mdx:549`; RFD:63 |
| R19 | Resource bounds: bounded notification buffering, frame sizes and outstanding work. Concrete limits are implementation policy. | Not observable (internal). RFD says limits are not wire constants | RFD:259,328,330 |

**Excluded as not agent-side** (bind the provider, a proxy, or an HTTP adapter): serverId generation and uniqueness (`McpServerAcp.serverId` "Providers MUST NOT reuse", v1 :7172 and v2 :8423), provider readiness, claim/forward routing, `-33001`/`-33002`/`-32022` emission, `server/discover` `supportedVersions`, MRTR-state integrity, the HTTP adapter and native-tool re-export (RFD:269-292). Cite: RFD:57-61,190-192,202,300.

## Details

**Direction and method.** `mcp/message` is one method in both directions. The meta tables list it in both `agentMethods` (notification, `x-side: agent`) and `clientMethods` (request, `x-side: client`): v1 `meta.unstable.json:15,38`, v2 `meta.unstable.json:13,31`. The agent sends the **request** (`MessageMcpRequest`; response is `MessageMcpResponse`). The agent receives the **notification** (`MessageMcpNotification`). The RFD says (RFD:36) to dispatch by message kind and direction. After this repo's own load of both schemas, `AGENT_NOTIFICATIONS` for v1 and v2 is `['mcp/message','session/cancel']` and `mcp/message` is in `CLIENT_METHODS`.

**Wire shapes (identical between v1 and v2 except the capability and metadata wording).**
- Request params: `{serverId, requestId, method, params?: object|null, _meta?: object|null}`, required `serverId`, `requestId`, `method`.
- Response result: `{ "result": <any JSON incl. null>, "_meta"? }` or `{ "error": {code:int, message:string, data?}, "_meta"? }`. Exactly one key. `anyOf`, so a receiver tolerates both and prefers `result`.
- Notification params: same fields as the request params.
- Declaration: `McpServer` variant `{type:"acp", name, serverId, _meta?}`.
- Capability: v1 `mcpCapabilities.acp: boolean` (default false). v2 `session.mcp.acp: McpAcpCapabilities|null` (`{}` means supported).
- v1 stable `McpServer` is `http|sse|stdio`. v2 stable is `http|stdio|other`, where `other` is "Custom or future transport ... Agents MUST reject a request with a transport they do not support with `-32602`" (v2 `schema.json`). So in v2 an `acp` declaration reaches a non-supporting agent through the stable "other" arm, and the MUST in R2 applies.

**Example exchange the TCK would have to serve** (RFD:101-170, 206-223): the agent sends `{"id":20,"method":"mcp/message","params":{"serverId":"project-tools:7a72","requestId":"mcp-request:a11f","method":"tools/call","params":{"name":"echo","arguments":{...},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{},...}}}}`. The provider answers `{"id":20,"result":{"result":{"resultType":"complete","content":[...],"isError":false}}}` or `{"id":20,"result":{"error":{"code":-32602,...}}}`. Progress arrives as an id-less `mcp/message` notification with the same `serverId` and `requestId`.

**Reference implementations.**
- Rust SDK (`md/mcp-over-acp.md`, `src/agent-client-protocol/src/mcp_server/*`) implements the current request-scoped RFD for both the provider and the caller: `MessageMcpRequest::new(server_id, request_id, method)`, fresh logical id per operation, inner `_meta` with `protocolVersion` and `clientCapabilities`, and the `Result`/`Error` split with "inner `-32000` is not ACP authentication-required". It agrees with the RFD (feature flags `unstable_mcp_over_acp`, plus `unstable_protocol_v2` for v2).
- Python SDK is **behind**: `tests/test_v2_runtime.py:406-411` and `src/acp/router.py:147-149` use `MessageMcpNotification(connection_id=...)`, the pre-request-scoped draft. It is not usable as a reference for this shape. See Discrepancies.

## Mapping to the TCK

### Coverage matrix

| Req | v1 | v2 | What exists |
|---|---|---|---|
| R1 capability shape | covered (generic) | covered (generic) | v1 `ACP-SCHEMA-001` validates the initialize result against the unstable schema (`src/tck/v1/requirements.py:195-199`). v2 `ACP-INIT-204` derives every object-typed marker from the schema at any depth, so `session.mcp.acp: true` fails (`src/tck/v2/requirements.py:276-293`), plus `ACP-SCHEMA-001` (:295). I did not run a dedicated `acp` defect fixture; "covered" is by construction |
| R2 unadvertised `acp` rejected | **not covered** (v1 INFORMATIONAL gap) | **partial** | v2 `ACP-MCP-203` (`requirements.py:2113-2128`; test `test_session_capabilities.py:1740-1773`) probes only `sse` and `_tck_unsupported_transport`. It never sends `type:"acp"`. The conforming base fixture rejects anything but advertised `stdio`/`http` (`tests/fixtures/agents/v2/_base.py:480-493`), so an `acp`-aware agent that forgot to advertise passes |
| R3 advertised `acp` accepted | not covered | not covered | No row. `ACP-MCP-201/202` (INFORMATIONAL) cover stdio and http only |
| R4 | n/a | n/a | MAY. The TCK needs a provider stub. Its mock client currently answers every agent-to-client request with `-32601` (`src/tck/v2/conformance/_helpers.py:1182,1454`) |
| R5 request shape | partial | partial | Method inventory is checked (`ACP-CLIENTCAP-202`, v2 `requirements.py:775-790`; `mcp/message` is a known client method, so it passes). The schema validator knows `MessageMcpRequest` (`tests/v1/test_validation.py:272-288`; v2 vendors the identical schema). No run ever makes an agent send one |
| R6, R7, R8, R9 | not covered | not covered | |
| R10, R11 | not covered | not covered | |
| R12 notification silence | not covered | not covered | `ACP-EXT-002/203` (v2 `requirements.py:2895-2945`) cover only unrecognized `_`/`$/` notifications. `mcp/message` is a *defined* agent method, so those rows do not apply to it. A non-silent `mcp/message` handler would pass every existing row |
| R13, R19 | not covered, no ledger entry | not covered, no ledger entry | Candidates for ledger entries (below) |
| R14 MRTR retry | not covered | not covered | |
| R15 cancel withdrawal | not covered | not covered | |
| R16 no unprompted `mcp/message` | not covered | not covered | |
| R17 connect SHOULD | not covered (v1 `ACP-SESSION-004` is stdio only) | not covered (v2 has no equivalent; `ACP-MCP-201` is stdio, INFORMATIONAL) | |
| R18 resume set | n/a | not covered; stdio part is in the ledger (see below) | |

Search evidence: `rg -i 'mcp/message|serverId|McpAcp|mcp.acp|"acp"'` over `src/`, `tests/`, `spec-tracker/`, `docs/` finds only the vendored schema, `protocol.py` method tables, `tests/v1/test_validation.py:272-288`, and `tests/fixtures/agents/v2/accepts_custom_mcp_transport.py` (which does not involve `acp`). There is no `acp`-related fixture in `tests/fixtures/agents/v{1,2}/`. The vendored schemas under `src/tck/v{1,2}/schema/` equal the 3961af94 ones exactly.

### Stale or wrong checks

1. **`ACP-MCP-203` text and test are incomplete, not wrong.** Its text says "v1's `sse`, which the spec names explicitly" and the reserved probe. The docs sentence it cites (`session-setup.mdx:545`) says "including a transport they did not advertise", and `acp` is the one in-tree transport that is real, unstable and unadvertised by most agents. This is the practical failure mode (an SDK parses `acp` but the agent does not advertise it).
2. **v2 `src/tck/v2/protocol.py:265`** docstring for `AGENT_NOTIFICATIONS` says "(`session/cancel`)". The set also holds `mcp/message` (v1's docstring at `protocol.py:127-128` is right). Cosmetic.
3. **v1 has no registry rows for MCP transports** (`ACP-MCP-*` is v2-only; v1 rows are `ACP-SESSION-003/004/006`). Not an error, but under Rule B an `acp` rule that exists in both versions should share an id.

### Ledger entries, none for this RFD, and reasons that break the policy

There is no `[[not_requirement]]` for `mcp-over-acp` in `spec-tracker/maps/v1.toml` or `v2.toml`. Nothing in them cites `docs/rfds/mcp-over-acp.mdx`. Candidates after R1-R19 are classified: R4, R13 (agent side), R19 and "no cross-delivery" in R12 are unobservable internal routing or resource accounting. R14's auto-approve half is policy-internal. These are legitimate ledger entries with reasons that do not rest on a TCK choice.

Existing MCP entries whose `reason` rests on a TCK choice, and which the `acp` transport makes testable **when the agent advertises it** (so the reason is wrong as a statement of why the rule is untestable):

| Ledger entry | Reason as written | Problem |
|---|---|---|
| `v2.toml:255-258` (extensibility.mdx:102, preserve MCP-reserved `_meta`) | "needs a live MCP server whose content flows back to the client, which the TCK does not host" | TCK choice. An `acp` provider stub hosts one over the existing connection |
| `v2.toml:351-354` (elicitation.mdx:54, no copy of Client capability object to the MCP server) | "needs a TCK-supplied MCP server that reports what it was offered" | TCK choice. With `acp`, the agent's per-request `io.modelcontextprotocol/clientCapabilities` (R8) is directly observable. Re-examine after the R8 row exists |
| `v2.toml:433-436` (resume/fork `mcpServers` complete set) | "the TCK's MCP stub has no bounded way to show that an agent did not launch it" | TCK choice (the stub). The real blocker is "the agent must call a stale server", which is only visible through the agent's model-driven tool use |
| `v2.toml:439-442` (stdio `cwd`/`env`/header ownership) | "the TCK's MCP stub records only the `argv`..." | TCK choice (stub design). Not an `acp` matter, listed because it is the same pattern |
| `v2.toml:455-458` and `v1.toml:121-124` (headers only to the configured origin) | "needs ... an HTTP MCP test server ... which the TCK does not host" | TCK choice. Not an `acp` matter |
| `v2.toml:509-512` (content.mdx:18,20, forward MCP tool output) | "Not observable: the TCK cannot feed MCP tool output to the agent" | Wrong for an agent advertising `acp`, since the provider stub can return arbitrary tool output over `mcp/message`. The agent's emitted content is then judgeable |

These belong to the owners of those docs (core-doc researchers). I flag them here because the RFD changes their observability. Do not rewrite them without checking the capability gate: they stay non-testable for agents that do not advertise `acp`, but "does not advertise it" is the real reason, not "the TCK does not host".

## Testability notes

**What a test needs.** To exercise anything past R1/R2, the TCK client must become a provider: it advertises nothing extra, but it declares `{type:"acp", name, serverId}` in `session/new`, and it must answer `mcp/message` requests (including `server/discover`, `tools/list`, `tools/call`) with valid carriers, even if they arrive before the `session/new` response (R4). That is a small MCP 2026-07-28 provider stub plus mock-client routing. Today any agent request gets `-32601`.

**Observability by requirement**
- R1, R2: fully observable at `initialize` and `session/new`, no model involved.
- R3: observable (the response to a well-formed declaration). The only risk is an agent that fails for an unrelated reason.
- R12 (silence on notifications): fully observable without any tool call. The TCK sends unsolicited, late-after-final-result and malformed (missing `method`) `mcp/message` notifications, then checks that the agent writes no response (no `id: null` error) and that a following ordinary request still succeeds. Works against any agent advertising `acp`, including real LLM agents.
- R5-R11, R14, R15, R17: observable **only if the agent decides to call the server**. For a real agent this takes a prompt such as "call the `echo` tool from server X". That is how `ACP-SESSION-004` already works for stdio (one prompt turn, lazy connect). The tests must SKIP, with a stated reason, when no `mcp/message` was sent, and must never FAIL for not calling (calling is not a MUST). A violating or conforming scripted fixture, however, calls deterministically.
- R10 and R11 additionally need the provider to return `{error:{code:-32000,...}}`, `{result:null}`, both-keys, unknown fields and `_meta:5`. The observation is "the turn still ends with a stop reason, not an ACP auth-required error or crash", which is weak but real.
- R13, R19 and the cross-delivery half of R12 are internal to the agent (routing tables, bounded queues): untestable from the client side.
- R15: the provider holds one request open, the TCK sends `session/cancel`, and a conforming agent sends `$/cancel_request` naming the outer id (v2 docs SHOULD, so ADVISORY). A violating one sends nothing (ADVISORY, so only reported) or names the logical `requestId` (RFD:249; CAPABILITY).

**Conforming vs violating.** A conforming agent for R2 rejects an unadvertised `acp` declaration with `-32602`. A violating one accepts it. For R6-R9 a violating agent addresses an undeclared `serverId`, reuses an active `requestId`, omits `params._meta` version/capabilities, or sends `initialize`.

## Verdict

- **v1:** no coverage of this RFD, and there are no docs-stated agent rules for it (the draft docs prose says nothing about `acp`; only generated schema text does). Everything is RFD-only, so the capped tiers apply: CAPABILITY behind `agentCapabilities.mcpCapabilities.acp`, INFORMATIONAL for the unadvertised-transport answer.
- **v2:** no coverage of the RFD, and one docs MUST (R2) is only partly covered by a generic probe. The feature is registered in the v2 draft docs as an Unstable feature (`overview.mdx:261`, `initialization.mdx:347-352`), so it should not be left without rows.

### Prioritized gap list

Ids below are suggestions only; use Rule B alignment (a rule that exists in both versions shares an id, v2-only rules get `2xx`).

**v2**

1. **P1, extend `ACP-MCP-203` with an `acp` probe** (R2). Send `{type:"acp", name:"tck-acp", serverId:"tck-acp-1"}` in `session/new`; expect `-32602`. SKIP that probe when `capabilities.session.mcp.acp` is advertised (the agent supports it, so R3 applies instead). Tier stays CAPABILITY on `capabilities.session`, as the existing row. *Conforming fixture:* the existing `conforming.py` (rejects non-advertised types). *Violating fixture:* new `accepts_unadvertised_acp_mcp.py`, a subclass overriding `_mcp_transport_rejection` to let `acp` through (pattern of `accepts_custom_mcp_transport.py`). Add it to the expected-fail sets in `tests/v2/test_cli.py` near the defect-fixture block (:4358-4399).
2. **P1, notification silence** (R12). New CAPABILITY row gated `capabilities.session.mcp.acp`: the TCK sends an unsolicited `mcp/message` notification (unknown `serverId`), a late one, and a malformed one; the agent emits nothing in return and still answers a following request. *Conforming:* new `conforming_mcp_acp.py` (advertises `session.mcp.acp: {}`, ignores the notifications). *Violating:* `answers_mcp_notification.py` (replies with an error response).
3. **P2, provider stub + R3 acceptance row.** CAPABILITY gated `capabilities.session.mcp.acp`: `session/new` with a well-formed `acp` declaration succeeds with a schema-valid result (and `session/resume`). *Violating:* `rejects_advertised_acp_mcp.py` (advertises `acp` but answers `-32602`).
4. **P2, request-shape rows** (R5-R9), one CAPABILITY row or a small group, gated the same, SKIP when no `mcp/message` request is seen after a scripted prompt. Checks: declared `serverId`; fresh `requestId` string, never reused while active; inner `_meta` carries `protocolVersion` `"2026-07-28"` and `clientCapabilities`; no inner `initialize`. *Conforming:* `conforming_mcp_acp.py` sends `server/discover` then `tools/call`, and two concurrent calls with distinct ids. *Violating:* `mcp_message_undeclared_server.py`, `mcp_message_reuses_active_request_id.py`, `mcp_message_missing_meta.py`, `mcp_message_sends_initialize.py`.
5. **P3, outcome-handling row** (R10, R11): provider returns inner `-32000`, `result: null`, both-keys, and an unknown-field carrier; the turn must still end normally. *Violating:* `inner_error_becomes_auth_required.py`.
6. **P3, MRTR retry shape** (R14): provider answers the first `tools/call` with `resultType:"input_required"` and a `requestState`; if the agent retries, the retry has a fresh `requestId`, `inputResponses` and the exact state. *Violating:* `mrtr_retry_reuses_request_id.py`.
7. **P3, ADVISORY rows:** R15 cancellation withdrawal (v2 docs `cancellation.mdx:31`; violating fixture `never_cancels_mcp_request.py`, and a CAPABILITY variant `cancel_uses_logical_request_id.py`), and R17 "connects to a declared acp server" analogue of `ACP-SESSION-004` (violating `ignores_acp_mcp_server.py`).
8. **Ledger:** add entries for R13, R19 and the cross-delivery half of R12 (citing RFD lines and the reason "internal routing / resource accounting, not on the wire"). Route the six reason problems in the table above to the owners of those docs.

**v1** (all RFD-only; no docs prose; gate `agentCapabilities.mcpCapabilities.acp`)

1. **P2, R12 notification silence** (same design as v2 #2, same fixtures with v1 capability shape: `mcpCapabilities.acp: true`).
2. **P2, R3 acceptance and R5-R9 request shape** (same designs as v2 #3-4; v1 declaration shape is the same `{type:"acp", name, serverId}`).
3. **P3, R2 as INFORMATIONAL:** record how the agent answers an unadvertised `acp` declaration in v1 (docs silent). No violating fixture is possible, because nothing is asserted.
4. **P3, R17 ADVISORY** (parity with `ACP-SESSION-004`, docs `session-setup.mdx:650`), R10/R11/R14 as in v2 #5-6.
5. R15 in v1 is MAY only, so record it as INFORMATIONAL at most or leave it out. There is no docs SHOULD in v1.

## Discrepancies

1. **Python SDK vs RFD:** Python SDK (da202e0) still uses `connection_id` for `MessageMcpNotification` (`tests/test_v2_runtime.py:406-411`; `src/acp/router.py:147-149`). The RFD (ef4613d3) replaced the connection model with server-addressed, request-scoped messages (RFD:336). The Rust SDK matches the RFD. The Python SDK cannot be used as a reference for this feature.
2. **v1 docs vs v2 docs:** only v2 states the agent-side reject rule for unsupported transports (`session-setup.mdx:545`). v1 prose does not. The v1 schema description only restricts clients. So R2 is a MUST in v2 and unspecified in v1.
3. **RFD wording vs docs, cancellation:** the RFD says a caller "can" cancel (RFD:237), while v2 `cancellation.mdx:31` states a SHOULD for any sender that stops waiting. These agree in effect but give different tiers (v2 ADVISORY; v1 MAY).
4. **Stage label:** `docs/rfds/mcp-over-acp.mdx` frontmatter has no stage. The stage comes only from `docs/docs.json` (group "Active", also at upstream/main). A row relying on this RFD should label it `(Active RFD)` per `docs/requirements.md:118-121`.
5. **Spec vs schema vs SDK on `clientInfo`:** the RFD example sends `io.modelcontextprotocol/clientInfo`; the Rust SDK doc lists only `protocolVersion` and `clientCapabilities` as the included `_meta` keys. Whether `clientInfo` is required is defined by MCP 2026-07-28 (external, not checked), so R8 asserts only the two keys the RFD names as required (RFD:198,202).

## Open questions

- **Required inner `_meta` keys** per the MCP 2026-07-28 spec (is `clientInfo` required?). Route to a researcher with access to the MCP spec, or keep R8 to the two named keys.
- **Should an agent that receives an `mcp/message` request (id present) from a client answer `-32601`?** RFD:36 says to dispatch by message kind and direction, but the schema only defines agent-received notifications. The RFD is silent on the agent-side answer. Could be a P3 INFORMATIONAL probe.
- **Tier of R3 and R17** (see judgment calls). The orchestrator should confirm with the user whether an advertised-but-rejecting agent is CAPABILITY or INFORMATIONAL, matching the `ACP-MCP-201/202` precedent.
- **Prompting real agents to call the tool.** Whether the TCK should drive tool calls through a prompt (non-deterministic) or restrict those rows to scripted fixtures is a design decision for the orchestrator.
- **Ledger reasons for the six MCP entries** in the table above belong to the core-doc owners. Not changed here.
