# Impact research, v1 core docs: overview, extensibility, transports, error (3961af94 -> 3ea94133)

**Sources checked:** spec repo `agent-client-protocol-2` at `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read with
`git show 3ea94133:<path>`; checkout HEAD `6ace4f6a` has no v1 draft-doc diff from it), base `3961af94`. Files:
`docs/protocol/v1/draft/{overview,extensibility,transports,error,subagents,session-setup,session-list,tool-calls,agent-plan,schema}.mdx`,
`docs/rfds/{subagents,mcp-over-acp,session-status,session-set-title}.mdx`, `schema/v1/schema.unstable.json`
(`Error`, `ErrorCode`, `MessageMcpNotification`, `McpCapabilities`, `CloseSessionRequest`, `SubagentUpdate`
byte-identical base vs target; `NewSessionRequest` changed: `configOptions` added, `required` still `[cwd, mcpServers]`),
`agent-client-protocol-schema/src/v1/{error,rpc}.rs` (unchanged). TCK: `src/tck/v1/requirements.py`,
`spec-tracker/maps/v1.toml`, `src/tck/v1/conformance/{_subagents_connection,_child_cancel,test_permissions}.py`.
Reference SDKs not consulted: the one new rule is explicit.
**Confidence:** high. `extensibility.mdx` and `transports.mdx` are byte-identical; `overview.mdx` gained 3 link-list
lines (225-227, no rule); `error.mdx` gained one paragraph (57) with one new SHOULD.

Line shifts at target: `overview.mdx` lines >= 225 move +3; `error.mdx` lines >= 57 move +2.

## overview.mdx

| Id / ledger | Classification | Target citation (@ 3ea94133) | Note |
|---|---|---|---|
| ACP-JSONRPC-002 | citation-only | `error.mdx:6-10; overview.mdx:238-242` | was overview 235-239; error.rs unchanged |
| ACP-JSONRPC-003 | citation-only (+ RFD stage) | `overview.mdx:242`; `rfds/mcp-over-acp.mdx:225,257 (Draft RFD)` | was overview 239. The RFD moved from Active to Draft, its cited lines are unchanged. Draft RFDs are cited only where nothing else states the rule, and `schema.mdx:285-302` now documents `mcp/message` as a notification with no `id` ("The outer envelope has no `id`", :301-302). Recommend replacing the RFD cite with `docs/protocol/v1/draft/schema.mdx:285-302`, or at least relabelling it `(Draft RFD)`. Tier stays MANDATORY (it comes from overview) |
| ACP-JSONRPC-005 | citation-only | `overview.mdx:238-242; extensibility.mdx:84-96` | was overview 235-239 |
| ACP-PROMPT-004 | citation-only | `overview.mdx:233; session-list.mdx:136-137` | was overview 230. See decision D3 (new agent-emitted `PlanMarkdown.path`) |
| ACP-EXT-001 | unchanged | `extensibility.mdx:47,56,69,84; overview.mdx:10-12` | |
| ledger `ToolCallLocation.line` is 1-based | citation-only | `tool-calls.mdx:382-386; overview.mdx:234` | was tool-calls 377-381 and overview 231. Reason still holds: target schema `ToolCallLocation.line` keeps `minimum: 0` |

The new lines 225-227 add links to prompt suggestions, session cursors and subagent sessions under `session/update`.
They state no rule, and the linked docs are other researchers' areas.

## extensibility.mdx (unchanged file)

| Id / ledger | Classification | Target citation | Note |
|---|---|---|---|
| ACP-JSONRPC-004 | unchanged | `error.mdx:41-43; extensibility.mdx:84-96` | |
| ACP-EXT-002 | unchanged | `extensibility.mdx:113` | `McpCapabilities.acp` and `MessageMcpNotification` are unchanged |
| ACP-META-001 | unchanged | `extensibility.mdx:10-14,37-43` | |
| ACP-SCHEMA-002 | unchanged | `extensibility.mdx:10-14,43` | It builds the allowed-keys union from the vendored schema, so the new agent-emitted defs (`PromptSuggestionsUpdate`, `CursorUpdate`, ...) are covered once the schema is re-vendored. No row change |
| ledger reverse-DNS naming (`:117`) | unchanged | `extensibility.mdx:117` | |
| ledger advertise custom capabilities (`:97,117`) | unchanged | `extensibility.mdx:97,117` | |

## transports.mdx (unchanged file)

| Id / ledger | Classification | Target citation | Note |
|---|---|---|---|
| ACP-TRANSPORT-001 | unchanged | `transports.mdx:20,21,23` | |
| ACP-TRANSPORT-002 | unchanged | `transports.mdx:6` | |
| ACP-SHUTDOWN-001 | unchanged | `transports.mdx:37` | |
| ACP-STDERR-001 | unchanged | `transports.mdx:22` | |
| ACP-INFO-PARSE-001 | unchanged | `error.mdx:28; transports.mdx:24` | |
| ACP-INFO-INVALIDREQ-001 | unchanged | `error.mdx:29; transports.mdx:24` | |
| ledger stdio SHOULD / custom transport MUST (`:10,45`) | unchanged citation; reason flagged | `transports.mdx:10,45` | The reason "the TCK only launches agents over stdio" leans on TCK scope. See D4 |

## error.mdx

| Id / ledger | Classification | Target citation | Note |
|---|---|---|---|
| ACP-ERROR-001 | unchanged | `error.mdx:9` | |
| ACP-ERROR-002 | unchanged | `error.mdx:31,45-47` | `NewSessionRequest` changed (`configOptions` added), but `cwd` is still required, so the probe is still invalid params |
| ACP-ERROR-003 | unchanged | `error.mdx:51-55` | Probes use never-created or closed ids, never a child, so the new :57 does not touch them |
| ACP-ERROR-004 | unchanged | `error.mdx:51-55` | same |
| ACP-ERROR-005 | citation-only | `error.mdx:29,61-63` | was 29,59-61 |
| ACP-ERROR-006 | unchanged | `error.mdx:30,41-43` | |
| ACP-ERROR-007 | unchanged | `error.mdx:31,45-47` | |
| ACP-ERROR-008 | unchanged | `error.mdx:37` | |
| ACP-LIST-003 | unchanged | `session-list.mdx:174; error.mdx:47` | |
| ACP-ARCHIVE-005 | citation-only | `session-list.mdx:260; error.mdx:69` | was error 67 |
| ACP-CLOSE-003 | citation-only (other doc) | `session-setup.mdx:356-359; error.mdx:55` | the error part is unchanged; the session-setup part moved from 347-350 (session-setup researcher's) |
| ACP-INFO-PARSE-001 / -INVALIDREQ-001 | unchanged | (above) | |
| ledger unknown error code (`:37`) | unchanged citation; reason flagged | `error.mdx:37` | The reason rests partly on a TCK choice ("the TCK's mock client sends only well-known codes"). See D2 |
| ledger `session/status` | citation-only | `session-list.mdx:259; error.mdx:68; rfds/session-status.mdx:126,130 (Draft RFD)` | was error 66; the RFD lines are unchanged (its hunk is at 134) |
| ledger `session/set_title` | citation-only | `rfds/session-set-title.mdx:178-179 (Draft RFD); error.mdx:70` | was error 68 |

Escalation check (areas that depend on "Unknown sessions"): `session-setup.mdx:359` links `#unknown-sessions` for
`session/close`. No existing probe (ERROR-003/004/008, CLOSE-003, ARCHIVE-005) names a child session, and no v1 test
sends anything but `session/cancel` to a child. Nothing existing changes.

## New requirements

**N1. Provisional `ACP-SUBAGENT-018` (or `ACP-ERROR-009`, see D1): a request naming an announced child gets `-32602`.**
- Text: a Client-initiated request other than `session/cancel` that names a child session the agent announced with
  `subagent_update` gets error `-32602`. The child is not an unknown session, so `-32002` is wrong. A success is also
  wrong: `session/close` and `session/delete` do not report success for a child. Only SHOULD.
- Tier: ADVISORY (SHOULD), `capability=None`; the test SKIPs itself when no child is announced.
- Citation: `docs/protocol/v1/draft/error.mdx:57; docs/protocol/v1/draft/subagents.mdx:419-428;
  docs/rfds/subagents.mdx:1093-1096 (Preview RFD)`. The docs govern; the RFD is secondary. The rule is new in this
  range (RFD revision history, `rfds/subagents.mdx:1697`, "2026-11-17 ... in both versions").
- Test approach: run on a connection that advertises `clientCapabilities.subagents: {}`. After a child is announced on
  a known session and the parent's turn has ended or been cancelled, send:
  - `session/close {sessionId: <child>}` when `sessionCapabilities.close` is advertised. For an ordinary unknown
    session the expected answer would be success, so this probe tells "treated as unknown" apart from "treated as a
    child". `subagents.mdx:428` names it explicitly.
  - `session/load {sessionId: <child>, cwd, mcpServers: []}` when `loadSession` is advertised. For an unknown session
    the answer would be `-32002`, so this probe discriminates too.

  Expect `-32602`. Success, `-32002`, `-32601` or another code is an ADVISORY FAIL; `-32000` SKIPs (as in ERROR-003).
  SKIP when no child is announced or neither capability is advertised. The association outlives the child's work
  (`subagents.mdx:148`), so probing after the turn is valid. These probes break `subagents.mdx:419` ("Clients MUST NOT
  send...") on purpose. That is justified the same way as ACP-PERM-002 and the `mcp/message` probes: the spec defines
  the agent's answer to exactly this input.
- Harness needs: no new mock-client capability; it only sends requests. The probe must run after the transcript that
  the other `ACP-SUBAGENT-*` rows judge has been captured, because a misbehaving agent may close or reload the child.
  Options: a post-judging phase on the `_child_cancel` driven connection, which already tracks announced children and
  cancels the parent last; or a dedicated connection that prompts until the first announcing `subagent_update`. Do not
  append the probe to `_subagents_connection`'s judged transcript.

No other new rules: the overview hunk is links only, and extensibility and transports are unchanged.

## New ledger entries

None.

## Decisions for the user

- **D1 (overlap and id):** `subagents.mdx:428` states the same SHOULD, so the subagents.mdx researcher will likely
  propose this row too. Recommendation: one row, citing both docs. Use the `ACP-SUBAGENT-*` family, since the evidence
  and the SKIP depend on the subagents connection. It is probably a shared id with v2, where the RFD applies the rule
  "in both versions"; the v2 researcher should confirm.
- **D1b (probe set):** recommend `session/close` and `session/load`, each gated, because they discriminate against
  the unknown-session answers. `session/prompt` would be ungated, but it risks starting real work on a child, and
  `session/set_mode` / `set_config_option` cannot tell "child" from "unknown mode/value", since both are `-32602`.
  Recommend against those two.
- **D2 (existing ledger `error.mdx:37`, reason rests on a TCK choice):** the clause "the TCK's mock client sends only
  well-known codes" is a TCK choice. The rule could become observable: the permission probe could answer
  `session/request_permission` with an error carrying an unrecognised code. Recommendation: in this update, rewrite the
  reason to name the real blocker. Suggested wording: "Deferred: 'generic failure' has no defined wire shape. The only
  observable consequences, the agent crashing or proceeding as if approved, need an agent-to-client request answered
  with an error, which only the model-driven permission probe produces." Then decide separately whether to add a row
  later (it would be MANDATORY under the tier rule; this rule did not change in this range).
- **D3 (new agent-emitted path, overview MUST):** `PlanMarkdown.path` is new and must be absolute (`agent-plan.mdx`
  hunk; also covered by `overview.mdx:233`). Recommendation: let the agent-plan area own it by re-targeting
  `ACP-PLAN-001` from the removed `PlanFile.uri`. Do not extend ACP-PROMPT-004, so one defect never FAILs two rows.
- **D4 (existing ledger `transports.mdx:10,45`):** low stakes. Recommend rewording the reason away from TCK scope:
  "Unobservable over stdio: an agent reached over stdio supports stdio by construction, and ACP does not specify
  custom transports, so no generic client can drive one."
- **D5 (ACP-JSONRPC-003 RFD cite):** replace `mcp-over-acp.mdx (Active RFD)` with `schema.mdx:285-302`
  (recommended), or relabel it `(Draft RFD)`.

## Discrepancies

- **Which child requests get `-32602`.** `error.mdx:57` says "any other request that names a child" (anything but
  `session/cancel`). `subagents.mdx:419` scopes "not permitted" to requests that change a child or its runtime, but
  its table (:425) lists "every other request". `rfds/subagents.mdx:1088-1089` says read-only operations "retain their
  normal protocol semantics". So a read-only unstable request such as `session/status` naming a child is ambiguous.
  This does not affect N1's probes: `close` and `load` are named as not permitted in every source.
