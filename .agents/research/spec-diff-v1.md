# ACP v1 spec change inventory: `beac4ba96190` -> `3961af94fa62`

**Sources checked:** `agent-client-protocol` (checkout `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`, HEAD `3961af94fa62d2386d993cadf1afc8b146fc799a`, committed 2026-11-10; not pulled, as instructed). Base `beac4ba96190018e9f6d82e148ff275084c5aa3e` (pinned `SCHEMA_REVISION`, `src/tck/v1/protocol.py:24`). 340 upstream commits in range. Scope read: `docs/protocol/v1/draft/`, `schema/v1/`, `docs/rfds/`, plus `docs/docs.json` for RFD stage placement.
**Confidence:** high for the inventory (tool output plus my own structural schema diff); medium for the "wording vs. normative" classification of doc hunks (skimmed diffs, not analysed).

## Answer

`spec-impact` ran cleanly (exit 0, full output in Appendix A). v1 schema went 1.26.0 -> 1.30.0. The change is large in line count (22 draft docs touched, 370 doc hunks, 184 `$defs` "changed", 28 added, 0 removed, 50 of 72 registered requirements touched) but most of it is editorial: a plain-language pass that sentence-cased headings, rewrote prose, replaced Rust identifiers (`ContentBlock::Text`) with wire names, and rewrote schema description links to `/protocol/v1/draft/...`. Of the 184 changed `$defs` in `schema.unstable.json`, only 11 have real structural changes and 9 more only gained an `x-deserialize-default-on-null` hint; 121 changed only by link rewrite and 42 by wording.

The substantive changes are:
1. **Client system prompt stabilized** (RFD Draft -> Preview 2026-10-30 -> Completed 2026-11-06; schema 1.30.0): `systemPrompt` request field, `sessionCapabilities.systemPrompt` and the `SystemPrompt*` `$defs` are now in stable `schema.json`; "(unstable)" labels were removed from docs. New normative detail: clients MUST NOT send an empty `content` array; agents MAY reject with `-32602`.
2. **New unstable methods/capabilities**: `session/status`, `session/set_title`, `session/archive`, `session/unarchive` (+ `archived` list filter and `SessionInfo.archived`), `auth/status` + `auth/status_update`, `proxy/initialize` + `proxy/successor`.
3. **Unstable subagent/session-message reshaping**: `SessionMessageChunk` lost `senderSessionId`/`recipientSessionId`; `SessionMessage` gained `senderMessageId`/`recipientMessageId`; `SubagentUpdate` gained `cwd`/`additionalDirectories`; new `session` `ToolCallContent` variant (`SessionReference`).
4. **Newly written `error.mdx`** (was "Documentation coming soon"): error code table, MUST/SHOULD rules for unknown sessions (`-32002` + `data.sessionId`), `-32602`, `-32601`, `-32600` before init. Close/delete are idempotent (`-32002` on `session/close`/`session/delete` is to be treated as success by clients; agents SHOULD return empty result).
5. **New `security.mdx`** plus "Security" subsections (file-system, terminals, tool-calls permissions, session-setup roots/MCP, authentication launch safety): all SHOULD-level and client-side/unobservable behaviors.
6. Smaller normative additions: `overview.mdx` "Conventions" (camelCase keys, snake_case discriminator strings); `plan` client capability documented in `initialization.mdx`; plan_update/plan_removed rules; `ToolCallLocation.line` now documented 1-based; `Cost.currency` may be non-ISO unit; `session/list` invalid cursor -> `-32602`; extensibility naming convention (`com.example/...`).

Recommendation (detail at the end): v1 can be handled in **diff mode**, but with core-doc escalation of `initialization.mdx`, `session-setup.mdx` (whole doc, not just the two mapped sections), `prompt-turn.mdx`, `overview.mdx`, `extensibility.mdx`, `transports.mdx`, plus the new `error.mdx`, and the spec map's section addresses need updating first (see Findings).

## Requirements
Not applicable (inventory task). Registered ids touched are listed in section 3 and Appendix A section 6.

## Details

### 1. spec-impact output
Command run exactly as specified (no `--fix`):
`uv run --package spec-tracker spec-impact beac4ba96190018e9f6d82e148ff275084c5aa3e 3961af94fa62d2386d993cadf1afc8b146fc799a --version v1 --spec-repo /Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`
Exit code 0; stderr only had uv venv-recreation noise (note: uv re-created the root `.venv`; no tracked file changed, `git status` clean). Full verbatim stdout is in **Appendix A** at the end of this file (1144 lines). Headline from its Summary:

- Changed files: 52 (22 draft docs, 5 schema files, 25 RFDs); doc hunks: 370.
- `$defs`: 28 added, 0 removed, 184 changed; $ref closure: 12.
- Links into changed docs: 456 (mostly `schema.mdx` -> `extensibility.mdx`).
- Affected entries: 50 requirements, 0 ledger entries (the v1 ledger is empty).
- Core hit: yes -- transports, overview, extensibility, initialization (whole docs); session-setup `(intro)` and `Working Directory`; prompt-turn `Session Updates` and `Stop Reasons`; `$defs` ErrorCode, SessionUpdate, ContentBlock, AgentCapabilities, ClientCapabilities.
- Not affected (22 of 72 ids): ACP-CANCEL-001/002, CLIENTCAP-002/003, CLOSE-002, DELETE-002/003, EXT-002, INFO-INVALIDREQ-001, INFO-PARSE-001, INIT-002/003, JSONRPC-001/003/004/005, RESUME-002, SESSION-004, SHUTDOWN-001, STDERR-001, TRANSPORT-001/002. (Unaffected by *citation overlap* only; e.g. TRANSPORT-* belong to a core doc that did change, and CLOSE-002/DELETE-* sit next to new idempotency text, see section 3.)

Tool caveat: the map's section addresses are matched case-sensitively and the doc headings were sentence-cased in the target (`Stop Reasons` -> `Stop reasons`, `Session Updates` -> `Session updates`, `Working Directory` -> `Working directory`). The tool printed three notes in Core hits: "section address 'Working Directory' / 'Session Updates' / 'Stop Reasons' matches no heading" at target. `maps/v1.toml` section addresses (`Session ID`, `Working Directory`, `Session Updates`, `Stop Reasons`, `Cancellation`) must be re-cased for the target tree (`Session ID` and `Cancellation` still match; `Working Directory`, `Session Updates`, `Stop Reasons` do not). Core hits were still computed on the base side, so they are correct for this run.

### 2. Changelog and RFD status

#### `schema/v1/CHANGELOG.md` entries 1.26.0 -> 1.30.0 (`schema/v1/CHANGELOG.md` at target, lines 10-67; version bump in `schema/v1/Cargo.toml` 1.26.0 -> 1.30.0)

```
## [1.30.0] - 2026-11-09
### Added
- (schema) stabilize client system prompt (#2765)

## [1.29.1] - 2026-11-02
### Other
- reconcile v1.15 spec text, unstable RFDs and the proxy-chains RFD (#2743)

## [1.29.0] - 2026-10-31
### Added
- (unstable) add session/archive and session/unarchive methods (#2736)
- (unstable) add proxy/initialize and proxy/successor (#2737)
- (unstable) add session/status method (#2735)
- (unstable) add auth/status method and auth/status_update notification (#2732)
- (unstable) add session/set_title method (#2734)
### Other
- (rfd) move client system prompt to preview (#2739)
- (schema) plain-language pass over spec pages and schema descriptions (#2730)

## [1.28.0] - 2026-10-30
### Added
- (unstable) report subagent working directories (#2593)
### Fixed
- (schema) allow non-ISO currency units such as credits (#2621)

## [1.27.0] - 2026-10-27
### Added
- (unstable) link session message views and keep identity off chunks (#2465)
### Fixed
- (unstable) null clears session_message participant IDs and message references (#2555)
- (unstable-v2) make ToolCallLocation.line 1-based (#2546)
### Other
- (schema) mark DefaultOnNull lists with an x-deserialize hint (#2569)
- (schema) note that titled multi-select items omit type, as in MCP (#2538)
- (schema) ExtNotification can be sent by either side (#2534)
- (schema) include -32800's range in the reserved error codes (#2531)
- (schema) write versioned doc links in source and drop the generator's link rewriting (#2525)
- (schema) use wire names instead of Rust identifiers in schema descriptions (#2520)
- (schema) write the error pages for v1 and v2 (#2504)
- (deps) bump the minor group with 9 updates (#2437)
```
(Condensed; URLs and PR links elided. Verbatim text: `git -C <spec> diff beac4ba..3961af9 -- schema/v1/CHANGELOG.md`.) Note the changelog's "(unstable-v2) make ToolCallLocation.line 1-based" also appears in v1 draft docs/schema description ("Optional 1-based line number"), i.e. it is a v1 wording change too.

#### RFD stage changes affecting v1 (sources: `docs/docs.json` group membership base vs target; `docs/rfds/updates.mdx` at target lines 9-60; `docs/rfds/about.mdx:35-66` defines the stages)

| RFD | Base stage -> target stage | Schema/doc effect on v1 |
|---|---|---|
| `client-system-prompt` | Draft -> Preview (2026-10-30, #2739) -> **Completed (2026-11-06, #2765)** | Promoted unstable -> stable: `systemPrompt` on `NewSessionRequest`/`LoadSessionRequest`/`ResumeSessionRequest`, `SessionCapabilities.systemPrompt`, `SystemPrompt`, `SystemPromptMode`, `SessionSystemPrompt{,Mode,Override}Capabilities` now in `schema/v1/schema.json` (and `**UNSTABLE**` banner removed in `schema.unstable.json`). `ForkSessionRequest` is not in the stable schema, so fork+systemPrompt stays unstable. New `docs/announcements/client-system-prompt-stabilized.mdx` listed in docs.json. |
| `subagents` | Draft -> **Active** (#2478; no `updates.mdx` entry) | Still unstable (`subagent_update`, `session_message`, `session_message_chunk`, new `session` tool-call content). RFD text grew ~500 lines. |
| `mcp-over-acp` | Draft -> **Active** (#2478) | No schema delta beyond description rewording (`McpServerAcp`, `McpCapabilities.acp`). |
| `session-status` | **new**, Draft (2026-10-26, #986) | unstable `session/status`, `SessionStatus`, `sessionCapabilities.status` |
| `session-set-title` | **new**, Draft (2026-10-26, #1987) | unstable `session/set_title`, `sessionCapabilities.title` |
| `session-archive` | **new**, Draft (2026-10-28, #2161) | unstable `session/archive`/`unarchive`, `archived` filter, `sessionCapabilities.archive` |
| `get-auth-state` | Draft -> Draft (rewritten, +228 lines) | unstable `auth/status`, `auth/status_update`, `agentCapabilities.auth.status`, `AuthAccount`/`AuthState` (schema added in 1.29.0) |
| `proxy-chains` | Draft -> Draft (reconciled, #2743) | unstable `proxy/initialize`, `proxy/successor` and `Proxy*` types in schema `schema.unstable.json` root `anyOf` |
| `diff-delete` | Draft -> **Removed** (2026-10-29, #2637) | Never reached the schema; no v1 effect. |
| `plan-operations`, `message-id`, `elicitation`, `streamable-http-websocket-transport` | modified, stage unchanged | Text edits only (check `agent-plan.mdx` below for `plan_update` rule additions). |
| `docs/rfds/v2/*` (incl. new `background-work`) | v2-only | Out of scope for v1. |

No other RFD moved between stages in the range; only `client-system-prompt` was promoted into a stable v1 surface.

#### Independent schema findings (my own `$defs` diff, base vs target, descriptions/titles stripped)

`schema/v1/schema.json` (stable): 5 `$defs` added (`SystemPrompt`, `SystemPromptMode`, `SessionSystemPromptCapabilities`, `SessionSystemPromptModeCapabilities`, `SessionSystemPromptOverrideCapabilities`); 4 structural changes (`NewSessionRequest`, `LoadSessionRequest`, `ResumeSessionRequest` gain optional nullable `systemPrompt`; `SessionCapabilities` gains optional nullable `systemPrompt`); 5 with only an added `x-deserialize-default-on-null: true` hint on array/object fields (`AuthMethodTerminal.args/env`, `CreateTerminalRequest.args/env`, `McpServerHttp.headers`, `McpServerSse.headers`, `McpServerStdio.args/env`) plus the same hint on `NewSessionRequest/LoadSessionRequest/ResumeSessionRequest` `mcpServers`/`additionalDirectories`; no removals; root unchanged. 134 more `$defs` changed in descriptions/links only.

`schema/v1/schema.unstable.json`: 28 added; 0 removed; 11 structural; 9 hint-only; 42 wording; 121 link-only.
- Added: `ArchiveSessionRequest/Response`, `UnarchiveSessionRequest/Response`, `SessionArchiveCapabilities`, `SessionArchiveFilter`; `AuthAccount`, `AuthState`, `AuthStatusCapabilities`, `AuthStatusRequest/Response`, `AuthStatusUpdateNotification`; `InitializeProxyRequest/Response`, `ProxyRequest/Response/Notification`, `ProxySuccessorRequest/Response/Notification`; `SessionReference`; `SessionStatus`, `SessionStatusCapabilities`, `SessionStatusRequest/Response`; `SessionTitleCapabilities`, `SetSessionTitleRequest/Response`.
- Structural: `AgentAuthCapabilities` (+`status`), `AgentNotification`/`AgentResponse`/`ClientRequest` (new members), root `anyOf` (+proxy message group), `ListSessionsRequest` (+`archived`), `SessionCapabilities` (+`archive`, `status`, `title`, `systemPrompt`), `SessionInfo` (+`archived`), `SessionMessage` (+`senderMessageId`, `recipientMessageId`), `SessionMessageChunk` (-`senderSessionId`, -`recipientSessionId`), `SubagentUpdate` (+`cwd`, +`additionalDirectories`), `ToolCallContent` (+`session` variant).
- Wording changes worth a human look (all in core or requirement-cited `$defs`): `ErrorCode` (description: -32800 range; `-32002` "A given resource, such as a session or file"), `ContentBlock` (superset-of-MCP statement, `uri` on image), `PromptCapabilities`/`PromptRequest` (Rust identifiers -> `text`/`resource_link`), `SessionUpdate` (notice/compaction gating now by wire capability names), `ToolCallLocation.line` ("1-based"), `Diff.oldText`, `Implementation` (dash/apostrophe only), `Cost.currency` (non-ISO units allowed), `SystemPrompt.content` (empty array rule), `RequestPermissionOutcome` (`Cancelled` -> `cancelled`).

### 3. One-line summary per changed area

Core = listed in `spec-tracker/maps/v1.toml`. "Ids" = registered ids touched per Appendix A section 6.

#### Docs (`docs/protocol/v1/draft/`)
| Doc | Core? | Summary | Registered ids touched |
|---|---|---|---|
| `transports.mdx` | **core (whole)** | Streamable HTTP section removed; text now says one transport (stdio) and links the transport RFD; heading recased. No stdio rule changed. | none (citation-wise) |
| `overview.mdx` | **core (whole)** | Heading recasing, prose; added "Conventions" (camelCase keys, snake_case discriminators), link to new Errors page; `Next steps` links Security. | ACP-EXT-001 (lines 10-12) |
| `extensibility.mdx` | **core (whole)** | Prose; `zed.dev` examples -> `com.example/...`; new naming guidance (MCP reverse-DNS convention) for `_meta` keys and custom methods. | ACP-EXT-001, ACP-META-001, ACP-SCHEMA-002 |
| `initialization.mdx` | **core (whole)** | Added client `plan` capability section; agent `auth.status`, `session.archive`/`status`/`title` capability docs (unstable); `systemPrompt` no longer "Unstable"; `Implementation.name/version` marked required; Rust ids -> wire names. | ACP-PROMPT-001/003, ACP-PROMPTCAP-001..003, ACP-CONFIG-003 |
| `session-setup.mdx` | **core (sections `(intro)`, `Session ID`, `Working Directory` only)** | `System prompt` stabilized (empty `content` array rule); `session/close` idempotency (agent SHOULD return empty result; client SHOULD treat `-32002` as success); new "Workspace root security" and "MCP servers > Security" SHOULDs; `env/headers` params `required`; heading recasing renames `Working Directory` section. | ACP-SESSION-003, ACP-LOAD-001/002, ACP-ADDDIRS-001 |
| `prompt-turn.mdx` | **core (sections `Session Updates`, `Stop Reasons`, `Cancellation`)** | Table prose; session-directed-message text reshaped (participants on `session_message` only; message-id links; initial subagent task SHOULD be an incoming `session_message`); `Message IDs` heading added; `Cost.currency` non-ISO. Stop-reason text unchanged except heading. | ACP-CLIENTCAP-006/007 |
| `error.mdx` | not core in map (new content) | **New**: error code table (-32700/-32600/-32601/-32602/-32603/-32800/-32000/-32002), unknown-session `-32002` + `data.sessionId` (SHOULD), `-32600` before init (SHOULD), `-32602` rules, unstable-method error rules. Supersedes the premise of an existing INFO requirement. | ACP-INFO-UNKNOWNSESSION-001 (and candidates ACP-ERROR-*) |
| `security.mdx` | not core (new doc, no inbound normative links) | **New**: trust model, rendering/URI/credential/prompt-injection/intermediary guidance; all SHOULD/MAY, client/agent-internal; plus per-feature "Security" subsections. | none |
| `authentication.mdx` | no | New "Launch safety" SHOULDs (terminal auth), prose; `Logging out`/`Active sessions` heading recase. | ACP-AUTH-003, ACP-AUTH-004 |
| `cancellation.mdx` | no | Prose; `$/cancel_request` example responses now name `session/prompt` `cancelled` stop reason and `session/request_permission` `cancelled` outcome. | ACP-JSONRPC-006, ACP-JSONRPC-007 |
| `content.mdx` | no | Intro rewritten; superset-of-MCP statement; adds sentence "All Agents MUST support resource links when included in prompts" (restates baseline); security links. | (via `$defs`) |
| `file-system.mdx` | no | New "Security" SHOULDs (client checks paths against root set). | none |
| `terminals.mdx` | no | New "Security" SHOULDs; prose. | none |
| `tool-calls.mdx` | no | Permission-option "Security" SHOULDs; remembered-decision wording; unstable `session` content type; `line` is 1-based; locations display-only. | ACP-PROMPT-004 (via `$defs`) |
| `agent-plan.mdx` | no | `plan` capability: when advertised agent SHOULD use `plan_update`; `plan_update` replaces whole plan across types; plan file URIs MUST be absolute; `plan_removed` SHOULD on cancel, clients MUST ignore unknown `planId`; empty `entries` empties plan. | ACP-CLIENTCAP-006 (via `PlanCapabilities`) |
| `session-config-options.mdx` | no | Type names aligned to schema (`SessionConfigOption`...); fuller examples (categories); default-value wording now "`currentValue` is the value used until changed". | ACP-CONFIG-001/002/003 |
| `session-list.mdx` | no | `-32602` for invalid cursor (SHOULD); new unstable "Archived sessions" section. | ACP-LIST-001/002 |
| `session-delete.mdx` | no | Added: clients SHOULD treat `-32002` from `session/delete` as success. | ACP-DELETE-001 (and nearby DELETE-002/003 semantics) |
| `session-modes.mdx` | no | Anchor fix only (`session%2Fset_mode`). | ACP-MODES-002 |
| `elicitation.mdx`, `slash-commands.mdx` | no | Punctuation/prose only. | none |
| `schema.mdx` | generated reference | Regenerated: new method sections for session/archive|unarchive|status|set_title, auth/status(+update), proxy/*; all changed `$defs`. | see schema rows |
| `docs/protocol/v1/*.mdx` (stable tree) | n/a to TCK | Mirrors the above for the stable doc tree (systemPrompt stabilized there); the TCK cites the draft tree. | n/a |

#### Schema `$defs` groups (`schema/v1/schema.unstable.json`, plus `schema.json` where noted)
| Group | Core `$def`? | Summary | Registered ids touched |
|---|---|---|---|
| System prompt (`SystemPrompt`, `SystemPromptMode`, `SessionSystemPrompt*Capabilities`, `New/Load/ResumeSessionRequest.systemPrompt`, `SessionCapabilities.systemPrompt`) | AgentCapabilities (via SessionCapabilities) | **Stabilized**: now in `schema.json`; wording drops Rust names, adds empty-array rule. | ACP-SYSPROMPT-001/002/003 (their `requirements.py` text still says "Unstable feature" and cites `schema.unstable.json`) |
| New session methods (`session/status`, `set_title`, `archive`, `unarchive`) + capabilities, `ListSessionsRequest.archived`, `SessionInfo.archived` | AgentCapabilities (SessionCapabilities extended) | Added, unstable, capability-gated; optional for agents. | ACP-LIST-001 (`ListSessionsRequest`/`SessionInfo` changed) |
| Auth status (`auth/status`, `auth/status_update`, `AuthAccount`, `AuthState`, `AuthStatusCapabilities`, `AgentAuthCapabilities.status`) | AgentCapabilities (via AuthCapabilities) | Added, unstable. | ACP-AUTH-004 (`AgentAuthCapabilities` changed) |
| Proxy (`proxy/initialize`, `proxy/successor`, `Proxy*`) | none | Added, unstable, new root `anyOf` member; intended for intermediaries, not an agent-under-test surface. | ACP-SCHEMA-001 (root `anyOf/0` changed) |
| Subagent/session messaging (`SessionMessage`, `SessionMessageChunk`, `SubagentUpdate`, `SessionReference`, `ToolCallContent.session`) | SessionUpdate, ContentBlock (related) | Unstable reshaping; breaking for unstable consumers (chunk identity fields removed). | ACP-CLIENTCAP-007 (RFD citation) |
| `x-deserialize-default-on-null` hints (`McpServer*`, `CreateTerminalRequest`, `AuthMethodTerminal`, `New/Load/Resume/ForkSessionRequest`) | none | Schema-generator hint only: null on these array/object fields deserializes to the default. No JSON Schema type change (validators unaffected), but documents null tolerance. | ACP-SESSION-003, ACP-LOAD-001, ACP-RESUME-001, ACP-AUTH-002/006, ACP-ADDDIRS-001 |
| Error (`ErrorCode`, `Error`, `McpError`, `ErrorStopReason`) | **ErrorCode** | Description-only: -32800 range, `-32002` also for sessions. No code values changed. | ACP-JSONRPC-002, ACP-ERROR-001/002, ACP-SCHEMA-002 |
| Content & prompt (`ContentBlock`, `PromptCapabilities`, `PromptRequest`, `ImageContent`, `AudioContent`, `EmbeddedResource`, `ResourceLink`) | **ContentBlock** | Description/link-only. | ACP-PROMPT-001/003, ACP-PROMPTCAP-001..003 |
| Session updates (`SessionUpdate`, `Notice`, `Compaction*`, `UsageUpdate`/`Cost`, `ToolCallLocation`, `Diff`, `PlanCapabilities`, `Plan*`) | **SessionUpdate** | Description-only except as above (`line` 1-based; `Cost.currency` free-form unit). | ACP-PROMPT-002/004, ACP-CLIENTCAP-004/005/006 |
| Capabilities (`AgentCapabilities`, `ClientCapabilities`, `FileSystemCapabilities`, `McpCapabilities`, `SessionCapabilities`, ...) | **AgentCapabilities, ClientCapabilities** | `AgentCapabilities`/`ClientCapabilities` link-only; sub-objects as above. | ACP-LOAD-001, ACP-CLIENTCAP-001 |
| Everything else (terminals, fs, elicitation, config options, modes, list/delete/close, initialize, auth) | none | Link/wording-only. | ACP-INIT-001/004, ACP-SESSION-001/002, ACP-LOAD-003, ACP-RESUME-001, ACP-DELETE-001, ACP-CLOSE-001, ACP-MODES-001/002, ACP-CONFIG-001..003, ACP-AUTH-001/003/005 |

#### Other findings relevant to the next step
- `src/tck/v1/requirements.py` citations are line-numbered `.mdx` ranges; `spec-impact --fix` must remap them before the pin bump (the tool refuses otherwise).
- `maps/v1.toml` core `sections` need re-casing (see section 1 caveat). Also consider whether the new `error.mdx` should become a core doc (cross-cutting rules for `-32002`/`-32602`/`-32601`/`-32600` that session-setup, session-list, session-delete, session-modes, config-options restate with links). Whole map is otherwise still valid: all listed paths still exist.
- Close/delete idempotency text (`session-setup.mdx` "Closing a session", `session-delete.mdx` Semantics, `error.mdx` "Unknown sessions") is new normative behavior around registered ids ACP-CLOSE-001/002 and ACP-DELETE-001..003 although their cited line ranges did not overlap hunks other than via moved lines. A researcher should read it against those ids.
- `error.mdx` now specifies what `ACP-INFO-UNKNOWNSESSION-001` records as unspecified: that requirement (`src/tck/v1/requirements.py:1080-1089`, tier INFORMATIONAL, citation `error.mdx:6 (stub)`) says "v1 does not specify one", but the new `error.mdx` "Unknown sessions" section says an agent SHOULD respond `-32002` with `data.sessionId` for an unknown session on `session/prompt`. Its premise and tier are stale, not just the citation. The same page likely also affects on ACP-ERROR-001/002, ACP-INFO-INVALIDREQ-001, ACP-JSONRPC-* error rules.
- SYSPROMPT requirements: now stable; their `Unstable feature` wording and `schema.unstable.json` citations can move to `schema.json`. Next step should also decide whether stable status changes their tier (they are still capability-gated: `agentCapabilities.sessionCapabilities.systemPrompt`).
- Vendoring: `src/tck/v1/schema/schema.unstable.json` and `meta.unstable.json` are to be re-vendored; the vendored `schema/VENDORED.md` carries the revision. 5 schema files changed upstream (`schema.json`, `schema.unstable.json`, `meta.unstable.json`, `CHANGELOG.md`, `Cargo.toml`); `meta.unstable.json` diff is 14 lines (method-table additions for new methods).
- `tck.v1.validation` carve-outs (e.g. `session/load` null response quirk) were not re-evaluated here.

## Testability notes
Out of scope for an inventory. One structural note for triage: nearly all new MUST/SHOULD text in `security.mdx` and the "Security" subsections concerns client rendering/approval behavior or agent-internal handling and is unobservable from a client-side TCK; the observable additions are the error-code rules in `error.mdx`, close/delete idempotency, empty `systemPrompt.content` rejection (`-32602`, MAY), and the stabilized `systemPrompt` surface.

## Discrepancies
- Docs vs. map: heading recasing makes three `maps/v1.toml` core section addresses unmatched at target (tool notes in Appendix A section 3).
- `requirements.py:1080-1089` ACP-INFO-UNKNOWNSESSION-001 (INFORMATIONAL, "v1 does not specify one", cites `error.mdx:6 (stub)`, which in base was "_Documentation coming soon_") now contradicts upstream: `error.mdx` "Unknown sessions" specifies `-32002` + `data.sessionId` as a SHOULD. Spec-impact reports a hunk overlap `-6,1 +6,63`.
- No spec-vs-schema conflict spotted at inventory depth. Not checked: Rust/Python SDK behavior (not requested).

## Open questions
- Should `error.mdx` be added to the v1 spec map as a core doc? (Orchestrator/programmer decision.)
- Should the v1 TCK start exercising any of the new unstable methods (`session/status`, `set_title`, `archive`) as CAPABILITY tests? They are capability-gated and optional; this is scoping, not research.
- Whether a stabilized `systemPrompt` changes tier or the "Unstable" labelling in requirements/tests (route to the requirement-semantics research step).
- `docs/rfds/subagents.mdx` and `mcp-over-acp.mdx` moved Draft -> Active; semantics of "Active" are visibility only (`docs/rfds/about.mdx:57`), so no schema promotion is implied.

## Recommendation: diff mode or full audit?

**Diff mode is viable**, with escalation. Reasons: (a) the schema delta is additive: 0 `$defs` removed, no existing field removed from the stable schema, and the only stable-surface change is the `systemPrompt` promotion plus `x-deserialize` hints, so no existing registered requirement's wire shape is invalidated; (b) of 370 doc hunks the large majority are heading recasing, prose, and link rewrites; (c) the genuinely normative new text is concentrated in a few places (below). A full audit is not justified, but the tracker's own "core hit: escalate" must be honored because the map is broad and a plain-language pass touched every core doc.

Escalate (re-read whole doc against dependent areas, not just hunks):
1. `error.mdx` (new, not in map): error semantics for -32002/-32602/-32601/-32600 against ACP-ERROR-*, ACP-INFO-*, ACP-JSONRPC-002, ACP-SESSION-*, CLOSE/DELETE/LIST.
2. `session-setup.mdx` (whole doc, not just mapped sections): system prompt stabilization, close idempotency, additionalDirectories null/omit wording, MCP security.
3. `initialization.mdx`: new `plan` client capability, `Implementation` required fields, capability additions, prompt capability wording.
4. `prompt-turn.mdx`: session-directed message reshaping (unstable), usage/cost currency, otherwise editorial; `overview.mdx` (new Conventions); `extensibility.mdx` (naming convention, SHOULD-level only); `transports.mdx` (Streamable HTTP section removed, no stdio rule change, likely no action).
5. Core `$defs`: `ErrorCode` (description only), `SessionUpdate`/`ContentBlock` (wording only), `AgentCapabilities`/`ClientCapabilities` (link only; the real changes are in `SessionCapabilities`/`AgentAuthCapabilities`, which are not core `$defs` -- consider adding `SessionCapabilities` to `core_defs`).

Prerequisite chores: re-case the three map section addresses; run `spec-impact --fix` before bumping `SCHEMA_REVISION`; re-vendor schema files.

## Appendix A: full `spec-impact` output (verbatim)

    # Spec impact (v1): `beac4ba96190` -> `3961af94fa62`
    
    Base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a`. Scope: `docs/protocol/v1/draft/`, `schema/v1/`, `docs/rfds/`.
    
    ## 1. Changed files
    
    - modified: `docs/protocol/v1/draft/agent-plan.mdx`
    - modified: `docs/protocol/v1/draft/authentication.mdx`
    - modified: `docs/protocol/v1/draft/cancellation.mdx`
    - modified: `docs/protocol/v1/draft/content.mdx`
    - modified: `docs/protocol/v1/draft/elicitation.mdx`
    - modified: `docs/protocol/v1/draft/error.mdx`
    - modified: `docs/protocol/v1/draft/extensibility.mdx`
    - modified: `docs/protocol/v1/draft/file-system.mdx`
    - modified: `docs/protocol/v1/draft/initialization.mdx`
    - modified: `docs/protocol/v1/draft/overview.mdx`
    - modified: `docs/protocol/v1/draft/prompt-turn.mdx`
    - modified: `docs/protocol/v1/draft/schema.mdx`
    - added: `docs/protocol/v1/draft/security.mdx`
    - modified: `docs/protocol/v1/draft/session-config-options.mdx`
    - modified: `docs/protocol/v1/draft/session-delete.mdx`
    - modified: `docs/protocol/v1/draft/session-list.mdx`
    - modified: `docs/protocol/v1/draft/session-modes.mdx`
    - modified: `docs/protocol/v1/draft/session-setup.mdx`
    - modified: `docs/protocol/v1/draft/slash-commands.mdx`
    - modified: `docs/protocol/v1/draft/terminals.mdx`
    - modified: `docs/protocol/v1/draft/tool-calls.mdx`
    - modified: `docs/protocol/v1/draft/transports.mdx`
    - modified: `docs/rfds/client-system-prompt.mdx`
    - removed: `docs/rfds/diff-delete.mdx`
    - modified: `docs/rfds/elicitation.mdx`
    - modified: `docs/rfds/get-auth-state.mdx`
    - modified: `docs/rfds/message-id.mdx`
    - modified: `docs/rfds/plan-operations.mdx`
    - modified: `docs/rfds/proxy-chains.mdx`
    - added: `docs/rfds/session-archive.mdx`
    - added: `docs/rfds/session-set-title.mdx`
    - added: `docs/rfds/session-status.mdx`
    - modified: `docs/rfds/streamable-http-websocket-transport.mdx`
    - modified: `docs/rfds/subagents.mdx`
    - modified: `docs/rfds/updates.mdx`
    - added: `docs/rfds/v2/background-work.mdx`
    - modified: `docs/rfds/v2/diff-file-states.mdx`
    - modified: `docs/rfds/v2/enum-variant-extension.mdx`
    - modified: `docs/rfds/v2/message-updates.mdx`
    - modified: `docs/rfds/v2/meta-patches.mdx`
    - modified: `docs/rfds/v2/overview.mdx`
    - modified: `docs/rfds/v2/plan-variants.mdx`
    - modified: `docs/rfds/v2/prompt.mdx`
    - modified: `docs/rfds/v2/required-session-methods.mdx`
    - modified: `docs/rfds/v2/session-resume-replay.mdx`
    - modified: `docs/rfds/v2/terminal-output.mdx`
    - modified: `docs/rfds/v2/tool-call-updates.mdx`
    - modified: `schema/v1/CHANGELOG.md`
    - modified: `schema/v1/Cargo.toml`
    - modified: `schema/v1/meta.unstable.json`
    - modified: `schema/v1/schema.json`
    - modified: `schema/v1/schema.unstable.json`
    
    ## 2. Doc hunks -> sections
    
    Base-side sections for removed or modified text, target-side for pure additions.
    
    ### `docs/protocol/v1/draft/agent-plan.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-8,1 +8,1` (base): `(intro)`
    - `-12,1 +12,1` (base): `Creating Plans`
    - `-51,1 +51,1` (base): `Plan Operations`
    - `-57,1 +57,5` (base): `Plan Operations > Item-Based Plans`
    - `-83,1 +87,1` (base): `Plan Operations > Markdown Plans`
    - `-103,1 +107,1` (base): `Plan Operations > File Plans`
    - `-123,1 +127,3` (base): `Plan Operations > Removing Plans`
    - `-141,1 +147,3` (base): `Plan Entries`
    - `-159,1 +167,1` (base): `Plan Entries`
    - `-167,1 +175,1` (base): `Updating Plans`
    - `-173,1 +181,3` (base): `Updating Plans > Dynamic Planning`
    - `-175,1 +185,1` (base): `Updating Plans > Dynamic Planning`
    
    ### `docs/protocol/v1/draft/authentication.mdx` (modified)
    
    - `-44,1 +44,1` (base): `Advertising Authentication`
    - `-153,1 +153,1` (base): `Protocol-driven authentication`
    - `-178,1 +178,1` (base): `Terminal authentication`
    - `-180,1 +180,1` (base): `Terminal authentication`
    - `-185,1 +185,1` (base): `Terminal authentication`
    - `-190,1 +190,7` (base): `Logging Out`
    - `-218,1 +224,1` (base): `Active Sessions`
    
    ### `docs/protocol/v1/draft/cancellation.mdx` (modified)
    
    - `-10,1 +10,1` (base): ``$/cancel_request` Notification`
    - `-12,1 +12,1` (base): ``$/cancel_request` Notification`
    - `-14,1 +14,1` (base): ``$/cancel_request` Notification`
    - `-21,1 +21,1` (base): ``$/cancel_request` Notification`
    - `-26,1 +26,1` (base): ``$/cancel_request` Notification`
    - `-28,1 +28,1` (base): `Internal Cancellation`
    - `-32,2 +32,2` (base): `Internal Cancellation`
    - `-40,1 +40,1` (base): `Example: Cascading Cancellation Flow`
    - `-42,1 +42,1` (base): `Example: Cascading Cancellation Flow`
    
    ### `docs/protocol/v1/draft/content.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-14,1 +14,1` (base): `Content Types`
    - `-16,1 +16,1` (base): `Content Types`
    - `-18,1 +18,1` (base): `Content Types`
    - `-20,1 +20,1` (base): `Content Types > Text Content`
    - `-22,1 +22,1` (base): `Content Types > Text Content`
    - `-42,1 +42,1` (base): `Content Types > Image Content`
    - `-75,1 +75,1` (base): `Content Types > Audio Content`
    - `-104,1 +104,1` (base): `Content Types > Embedded Resource`
    - `-166,1 +166,1` (base): `Content Types > Resource Link`
    - `-169,0 +170,2` (target): `Content types > Resource link`
    
    ### `docs/protocol/v1/draft/elicitation.mdx` (modified)
    
    - `-60,1 +60,1` (base): `Creating an elicitation`
    - `-111,1 +111,1` (base): `Creating an elicitation > Form mode`
    - `-145,2 +145,2` (base): `Responses`
    
    ### `docs/protocol/v1/draft/error.mdx` (modified)
    
    - `-2,1 +2,1` (base): `(intro)`
    - `-6,1 +6,63` (base): `(intro)`
    
    ### `docs/protocol/v1/draft/extensibility.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-8,1 +8,1` (base): `The `_meta` Field`
    - `-13,1 +13,1` (base): `The `_meta` Field`
    - `-31,1 +31,1` (base): `The `_meta` Field`
    - `-45,1 +45,1` (base): `Extension Methods`
    - `-47,1 +47,1` (base): `Extension Methods`
    - `-54,1 +54,1` (base): `Extension Methods > Custom Requests`
    - `-62,1 +62,1` (base): `Extension Methods > Custom Requests`
    - `-99,1 +99,1` (base): `Extension Methods > Custom Notifications`
    - `-106,1 +106,1` (base): `Extension Methods > Custom Notifications`
    - `-115,1 +115,1` (base): `Advertising Custom Capabilities`
    - `-117,1 +117,1` (base): `Advertising Custom Capabilities`
    - `-128,4 +128,2` (base): `Advertising Custom Capabilities`
    - `-138,1 +136,1` (base): `Advertising Custom Capabilities`
    
    ### `docs/protocol/v1/draft/file-system.mdx` (modified)
    
    - `-8,1 +8,1` (base): `Checking Support`
    - `-31,1 +31,1` (base): `Reading Files`
    - `-78,1 +78,1` (base): `Writing Files`
    - `-119,0 +120,7` (target): `Writing files` | `Security`
    
    ### `docs/protocol/v1/draft/initialization.mdx` (modified)
    
    - `-95,1 +95,1` (base): `Protocol version > Version Negotiation`
    - `-117,1 +117,1` (base): `Capabilities > Client Capabilities`
    - `-121,1 +121,1` (base): `Capabilities > Client Capabilities > Terminal Authentication`
    - `-133,1 +133,1` (base): `Capabilities > Client Capabilities > File System`
    - `-172,1 +172,18` (base): `Capabilities > Client Capabilities > Boolean Config Options`
    - `-191,1 +208,1` (base): `Capabilities > Client Capabilities > Session Compaction`
    - `-209,1 +226,1` (base): `Capabilities > Client Capabilities > Session Notices`
    - `-227,1 +244,1` (base): `Capabilities > Agent Capabilities`
    - `-247,1 +264,1` (base): `Capabilities > Agent Capabilities > Prompt capabilities`
    - `-252,1 +269,1` (base): `Capabilities > Agent Capabilities > Prompt capabilities`
    - `-256,1 +273,1` (base): `Capabilities > Agent Capabilities > Prompt capabilities`
    - `-260,1 +277,1` (base): `Capabilities > Agent Capabilities > Prompt capabilities`
    - `-276,1 +293,1` (base): `Capabilities > Agent Capabilities > Authentication Capabilities`
    - `-282,0 +300,7` (target): `Capabilities > Agent capabilities > Authentication capabilities`
    - `-287,1 +311,1` (base): `Capabilities > Agent Capabilities > Session Capabilities`
    - `-298,0 +323,8` (target): `Capabilities > Agent capabilities > Session capabilities`
    - `-309,3 +341,3` (base): `Capabilities > Agent Capabilities > Session Capabilities`
    - `-315,0 +348,14` (target): `Capabilities > Agent capabilities > Session capabilities`
    - `-321,1 +367,1` (base): `Implementation Information`
    - `-325,1 +371,1` (base): `Implementation Information`
    - `-327,1 +373,1` (base): `Implementation Information`
    - `-331,2 +377,3` (base): `Implementation Information`
    - `-335,1 +382,1` (base): `Implementation Information`
    
    ### `docs/protocol/v1/draft/overview.mdx` (modified)
    
    - `-12,2 +12,2` (base): `Communication Model`
    - `-15,1 +15,1` (base): `Message Flow`
    - `-23,1 +23,1` (base): `Message Flow`
    - `-49,1 +49,1` (base): `Agent > Baseline Methods`
    - `-82,1 +82,1` (base): `Agent > Optional Methods`
    - `-103,1 +103,1` (base): `Agent > Optional Methods`
    - `-123,1 +123,1` (base): `Client > Baseline Methods`
    - `-136,1 +136,1` (base): `Client > Optional Methods`
    - `-233,1 +233,1` (base): `Error Handling`
    - `-240,0 +241,6` (target): `Error handling` | `Conventions`
    - `-243,1 +249,1` (base): `Extensibility`
    - `-249,1 +255,1` (base): `Extensibility`
    - `-251,1 +257,1` (base): `Next Steps`
    - `-253,5 +259,6` (base): `Next Steps`
    
    ### `docs/protocol/v1/draft/prompt-turn.mdx` (modified)
    
    - `-10,1 +10,1` (base): `Session Updates`
    - `-14,21 +14,21` (base): `Session Updates`
    - `-46,3 +46,5` (base): `Session Updates > Session-directed messages (unstable)`
    - `-50,1 +52,2` (base): `Session Updates > Session-directed messages (unstable)`
    - `-59,1 +62,1` (base): `Session Updates > Session-directed messages (unstable)`
    - `-62,1 +65,15` (base): `Session Updates > Session-directed messages (unstable)`
    - `-69,1 +86,1` (base): `Session Updates > Session-directed messages (unstable)`
    - `-72,1 +89,1` (base): `Session Updates > Session-directed messages (unstable)`
    - `-78,4 +95,7` (base): `Session Updates > Session-directed messages (unstable)`
    - `-86,1 +106,6` (base): `The Prompt Turn Lifecycle`
    - `-88,1 +113,1` (base): `The Prompt Turn Lifecycle`
    - `-133,1 +158,1` (base): `The Prompt Turn Lifecycle > 1. User Message`
    - `-176,1 +201,1` (base): `The Prompt Turn Lifecycle > 2. Agent Processing`
    - `-180,1 +205,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output`
    - `-243,1 +268,3` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output`
    - `-264,1 +291,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Notices`
    - `-303,2 +330,2` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Notices`
    - `-316,1 +343,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Notices`
    - `-326,1 +353,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Compaction`
    - `-341,1 +368,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Compaction`
    - `-372,1 +399,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Compaction`
    - `-384,1 +411,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Compaction`
    - `-452,1 +479,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Compaction`
    - `-472,1 +499,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Compaction`
    - `-474,1 +501,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Compaction`
    - `-476,1 +503,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Usage Updates`
    - `-499,1 +526,1` (base): `The Prompt Turn Lifecycle > 3. Agent Reports Output > Session Usage Updates`
    - `-501,1 +528,1` (base): `The Prompt Turn Lifecycle > 4. Check for Completion`
    - `-517,1 +544,1` (base): `The Prompt Turn Lifecycle > 5. Tool Invocation and Status Reporting`
    - `-540,1 +567,1` (base): `The Prompt Turn Lifecycle > 5. Tool Invocation and Status Reporting`
    - `-572,1 +599,1` (base): `The Prompt Turn Lifecycle > 6. Continue Conversation`
    - `-578,1 +605,1` (base): `Stop Reasons`
    
    ### `docs/protocol/v1/draft/schema.mdx` (modified)
    
    - `-17,0 +18,74` (target): `Agent` | `Agent > auth/status` | `Agent > auth/status > AuthStatusRequest` | `Agent > auth/status > AuthStatusResponse`
    - `-27,1 +101,1` (base): `Agent > authenticate`
    - `-228,1 +302,1` (base): `Agent > mcp/message > MessageMcpNotification`
    - `-431,0 +506,63` (target): `Agent > providers/set > SetProviderResponse` | `Agent > session/archive` | `Agent > session/archive > ArchiveSessionRequest` | `Agent > session/archive > ArchiveSessionResponse`
    - `-444,1 +581,1` (base): `Agent > session/cancel`
    - `-631,5 +768,1` (base): `Agent > session/fork > ForkSessionRequest`
    - `-637,1 +770,1` (base): `Agent > session/fork > ForkSessionRequest`
    - `-703,0 +837,12` (target): `Agent > session/list > ListSessionsRequest`
    - `-790,3 +935,1` (base): `Agent > session/load > LoadSessionRequest`
    - `-794,3 +937,1` (base): `Agent > session/load > LoadSessionRequest`
    - `-843,1 +984,1` (base): `Agent > session/new`
    - `-880,5 +1021,1` (base): `Agent > session/new > NewSessionRequest`
    - `-965,1 +1102,1` (base): `Agent > session/prompt > PromptRequest`
    - `-971,1 +1108,1` (base): `Agent > session/prompt > PromptRequest`
    - `-973,1 +1110,1` (base): `Agent > session/prompt > PromptRequest`
    - `-1062,3 +1199,1` (base): `Agent > session/resume > ResumeSessionRequest`
    - `-1066,3 +1201,1` (base): `Agent > session/resume > ResumeSessionRequest`
    - `-1243,0 +1377,218` (target): `Agent > session/set_mode > SetSessionModeResponse` | `Agent > session/set_title` | `Agent > session/set_title > SetSessionTitleRequest` | `Agent > session/set_title > SetSessionTitleResponse` | `Agent > session/status` | `Agent > session/status > SessionStatusRequest` | `Agent > session/status > SessionStatusResponse` | `Agent > session/unarchive` | `Agent > session/unarchive > UnarchiveSessionRequest` | `Agent > session/unarchive > UnarchiveSessionResponse`
    - `-1251,0 +1603,51` (target): `Client` | `Client > auth/status_update` | `Client > auth/status_update > AuthStatusUpdateNotification`
    - `-1759,3 +2161,3` (base): `Client > mcp/message > MessageMcpResponse`
    - `-1805,1 +2207,1` (base): `Client > session/request_permission`
    - `-1912,1 +2314,1` (base): `Client > terminal/create`
    - `-2210,0 +2613,154` (target): `Proxy` | `Proxy > proxy/initialize` | `Proxy > proxy/initialize > InitializeProxyRequest` | `Proxy > proxy/initialize > InitializeProxyResponse` | `Proxy > proxy/successor` | `Proxy > proxy/successor > ProxySuccessorNotification` | `Proxy > proxy/successor > ProxySuccessorRequest` | `Proxy > proxy/successor > ProxySuccessorResponse`
    - `-2283,0 +2840,11` (target): `AgentAuthCapabilities`
    - `-2400,0 +2968,56` (target): `AuthAccount`
    - `-2459,1 +3082,1` (base): `AuthMethod`
    - `-2494,1 +3117,1` (base): `AuthMethod`
    - `-2525,1 +3148,1` (base): `AuthMethodAgent`
    - `-2547,1 +3170,1` (base): `AuthMethodTerminal`
    - `-2562,16 +3185,75` (base): `AuthMethodTerminal`
    - `-2829,1 +3511,1` (base): `ClientSessionCapabilities`
    - `-2893,1 +3575,1` (base): `CompactionSummaryChunk`
    - `-2922,1 +3604,1` (base): `CompactionUpdate`
    - `-3010,3 +3691,0` (base): `ContentBlock`
    - `-3019,2 +3698,2` (base): `ContentBlock`
    - `-3240,1 +3919,2` (base): `Cost`
    - `-3289,1 +3969,1` (base): `Diff`
    - `-3452,2 +4132,2` (base): `ElicitationPropertySchema`
    - `-3846,1 +4526,1` (base): `ElicitationSessionScope`
    - `-4108,2 +4788,3` (base): `ErrorCode`
    - `-4131,2 +4812,1` (base): `ErrorCode`
    - `-4147,1 +4827,2` (base): `ErrorCode`
    - `-4176,1 +4857,1` (base): `ExtNotification`
    - `-4192,1 +4873,1` (base): `ExtResponse`
    - `-4265,1 +4946,1` (base): `IdleStateUpdate`
    - `-4278,1 +4959,1` (base): `IdleStateUpdate`
    - `-4438,1 +5119,1` (base): `Implementation`
    - `-4441,1 +5122,1` (base): `Implementation`
    - `-4580,1 +5261,1` (base): `McpCapabilities`
    - `-4586,1 +5267,1` (base): `McpCapabilities`
    - `-4592,1 +5273,1` (base): `McpCapabilities`
    - `-4604,2 +5285,2` (base): `McpError`
    - `-4612,1 +5293,1` (base): `McpError`
    - `-4615,1 +5296,1` (base): `McpError`
    - `-4959,0 +5641,2` (target): `MultiSelectItems`
    - `-5042,1 +5725,1` (base): `Notice`
    - `-5574,2 +6257,2` (base): `PromptCapabilities`
    - `-5598,1 +6281,1` (base): `PromptCapabilities`
    - `-5606,1 +6289,1` (base): `PromptCapabilities`
    - `-5613,1 +6296,1` (base): `PromptCapabilities`
    - `-5765,1 +6448,1` (base): `RequestPermissionOutcome`
    - `-5811,1 +6494,1` (base): `RequiresActionStateUpdate`
    - `-5877,1 +6560,1` (base): `RunningStateUpdate`
    - `-5922,0 +6606,58` (target): `SessionArchiveCapabilities` | `SessionArchiveFilter`
    - `-5931,1 +6672,1` (base): `SessionCancelCapabilities`
    - `-5954,1 +6695,1` (base): `SessionCapabilities`
    - `-5980,0 +6722,12` (target): `SessionCapabilities`
    - `-6021,1 +6774,1` (base): `SessionCapabilities`
    - `-6026,1 +6779,8` (base): `SessionCapabilities`
    - `-6030,0 +6791,14` (target): `SessionCapabilities`
    - `-6349,2 +7123,2` (base): `SessionId`
    - `-6378,0 +7153,11` (target): `SessionInfo`
    - `-6398,1 +7183,1` (base): `SessionInfoUpdate`
    - `-6451,1 +7236,1` (base): `SessionMessage`
    - `-6457,1 +7242,1` (base): `SessionMessage`
    - `-6461,0 +7247,8` (target): `SessionMessage`
    - `-6464,1 +7257,12` (base): `SessionMessage`
    - `-6467,1 +7271,4` (base): `SessionMessage`
    - `-6477,0 +7285,3` (target): `SessionMessageChunk`
    - `-6483,1 +7293,1` (base): `SessionMessageChunk`
    - `-6494,6 +7303,0` (base): `SessionMessageChunk`
    - `-6557,0 +7362,30` (target): `SessionReference`
    - `-6577,1 +7411,38` (base): `SessionSystemPromptCapabilities`
    - `-6582,0 +7454,19` (target): `SessionStatusCapabilities` | `SessionSystemPromptCapabilities`
    - `-6609,4 +7498,0` (base): `SessionSystemPromptModeCapabilities`
    - `-6640,0 +7527,20` (target): `SessionSystemPromptOverrideCapabilities` | `SessionTitleCapabilities`
    - `-6645,1 +7551,1` (base): `SessionSystemPromptOverrideCapabilities`
    - `-6647,2 +7553,2` (base): `SessionSystemPromptOverrideCapabilities`
    - `-7085,1 +7991,1` (base): `SessionUpdate`
    - `-7121,1 +8027,1` (base): `SessionUpdate`
    - `-7169,1 +8075,1` (base): `SessionUpdate`
    - `-7213,1 +8119,11` (base): `SessionUpdate`
    - `-7219,1 +8135,1` (base): `SessionUpdate`
    - `-7223,0 +8140,9` (target): `SessionUpdate`
    - `-7228,1 +8153,1` (base): `SessionUpdate`
    - `-7242,1 +8167,1` (base): `SessionUpdate`
    - `-7251,1 +8176,1` (base): `SessionUpdate`
    - `-7270,1 +8195,1` (base): `SessionUpdate`
    - `-7276,1 +8201,1` (base): `SessionUpdate`
    - `-7280,0 +8206,8` (target): `SessionUpdate`
    - `-7283,1 +8216,12` (base): `SessionUpdate`
    - `-7286,1 +8230,4` (base): `SessionUpdate`
    - `-7305,1 +8252,1` (base): `SessionUpdate`
    - `-7316,6 +8262,0` (base): `SessionUpdate`
    - `-7337,2 +8278,2` (base): `StateUpdate`
    - `-7350,1 +8291,1` (base): `StateUpdate`
    - `-7368,1 +8309,1` (base): `StateUpdate`
    - `-7384,1 +8325,1` (base): `StateUpdate`
    - `-7506,1 +8447,1` (base): `StateUpdate`
    - `-7525,1 +8466,1` (base): `StateUpdate`
    - `-7740,1 +8681,1` (base): `SubagentSessionCapabilities`
    - `-7754,1 +8695,1` (base): `SubagentSessionCapabilities`
    - `-7769,1 +8710,1` (base): `SubagentUpdate`
    - `-7773,1 +8714,1` (base): `SubagentUpdate`
    - `-7777,1 +8718,1` (base): `SubagentUpdate`
    - `-7782,0 +8724,2` (target): `SubagentUpdate`
    - `-7794,1 +8737,11` (base): `SubagentUpdate`
    - `-7800,1 +8753,1` (base): `SubagentUpdate`
    - `-7804,0 +8758,9` (target): `SubagentUpdate`
    - `-7809,1 +8771,1` (base): `SubagentUpdate`
    - `-7820,1 +8782,1` (base): `SubagentUpdate`
    - `-7829,1 +8791,1` (base): `SubagentUpdate`
    - `-7836,4 +8797,0` (base): `SystemPrompt`
    - `-7845,2 +8803,1` (base): `SystemPrompt`
    - `-7863,1 +8820,1` (base): `SystemPrompt`
    - `-7867,0 +8825,3` (target): `SystemPrompt`
    - `-7872,4 +8832,2` (base): `SystemPrompt`
    - `-7881,4 +8838,0` (base): `SystemPromptMode`
    - `-7887,1 +8841,1` (base): `SystemPromptMode`
    - `-8157,1 +9111,1` (base): `ToolCallContent`
    - `-8195,0 +9150,27` (target): `ToolCallContent`
    - `-8224,1 +9205,1` (base): `ToolCallLocation`
    - `-8378,1 +9359,1` (base): `UnknownStateUpdate`
    - `-8386,1 +9367,1` (base): `UnknownStateUpdate`
    
    ### `docs/protocol/v1/draft/security.mdx` (added)
    
    - `-0,0 +1,74` (target): `(intro)` | `Trust Model` | `Rendering Agent content` | `URIs and remote resources` | `Credentials` | `Prompt injection` | `Intermediaries` | `Transports` | `Feature guidance` | `Residual risk`
    
    ### `docs/protocol/v1/draft/session-config-options.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-15,1 +15,1` (base): `Initial State`
    - `-87,1 +87,1` (base): `Initial State`
    - `-93,1 +93,1` (base): `Initial State > ConfigOption`
    - `-107,1 +107,1` (base): `Initial State > ConfigOption`
    - `-112,1 +112,1` (base): `Initial State > ConfigOption`
    - `-123,1 +123,4` (base): `Initial State > ConfigOption`
    - `-126,1 +129,1` (base): `Initial State > ConfigOption`
    - `-129,1 +132,1` (base): `Initial State > ConfigOptionValue`
    - `-143,1 +146,1` (base): `Initial State > Grouped Select Options`
    - `-165,1 +168,1` (base): `Initial State > Grouped Select Options`
    - `-167,2 +170,2` (base): `Initial State > Grouped Select Options`
    - `-171,1 +174,1` (base): `Initial State > Boolean Config Options`
    - `-208,1 +211,1` (base): `Option Categories`
    - `-230,1 +233,1` (base): `Option Ordering`
    - `-240,1 +243,1` (base): `Default Values and Graceful Degradation`
    - `-242,1 +245,1` (base): `Default Values and Graceful Degradation`
    - `-248,1 +251,1` (base): `Default Values and Graceful Degradation`
    - `-250,1 +253,1` (base): `Setting a Config Option`
    - `-311,0 +315,2` (target): `Setting a config option > From the Client`
    - `-314,1 +319,12` (base): `Setting a Config Option > From the Client`
    - `-318,0 +335,1` (target): `Setting a config option > From the Client`
    - `-321,1 +338,29` (base): `Setting a Config Option > From the Client`
    - `-329,4 +374,3` (base): `Setting a Config Option > From the Client`
    - `-350,0 +395,2` (target): `Setting a config option > From the Agent`
    - `-353,1 +399,12` (base): `Setting a Config Option > From the Agent`
    - `-357,0 +415,1` (target): `Setting a config option > From the Agent`
    - `-360,1 +418,29` (base): `Setting a Config Option > From the Agent`
    - `-374,1 +460,1` (base): `Relationship to Session Modes`
    
    ### `docs/protocol/v1/draft/session-delete.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-33,1 +33,1` (base): `Checking Support`
    - `-54,1 +54,1` (base): `Deleting a Session`
    - `-86,0 +87,1` (target): `Semantics`
    
    ### `docs/protocol/v1/draft/session-list.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-8,1 +8,1` (base): `(intro)`
    - `-35,1 +35,1` (base): `Checking Support`
    - `-66,1 +66,1` (base): `Listing Sessions`
    - `-141,1 +141,1` (base): `Listing Sessions`
    - `-144,1 +144,1` (base): `Listing Sessions`
    - `-173,2 +173,2` (base): `Pagination`
    - `-177,1 +177,1` (base): `Updating Session Metadata`
    - `-199,1 +199,1` (base): `Updating Session Metadata`
    - `-219,1 +219,1` (base): `Interaction with Other Session Methods`
    - `-221,1 +221,1` (base): `Interaction with Other Session Methods`
    - `-225,0 +226,36` (target): `Interaction with other session methods` | `Archived sessions (unstable)`
    
    ### `docs/protocol/v1/draft/session-modes.mdx` (modified)
    
    - `-83,1 +83,1` (base): `Setting the current mode > From the Client`
    
    ### `docs/protocol/v1/draft/session-setup.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-47,1 +47,1` (base): `Creating a Session`
    - `-85,1 +85,1` (base): `Loading Sessions`
    - `-89,1 +89,1` (base): `Loading Sessions > Checking Support`
    - `-108,1 +108,1` (base): `Loading Sessions > Loading a Session`
    - `-139,9 +139,10` (base): `Loading Sessions > Loading a Session`
    - `-208,1 +209,1` (base): `Resuming Sessions`
    - `-213,1 +214,1` (base): `Resuming Sessions > Checking Support`
    - `-237,1 +238,1` (base): `Resuming Sessions > Resuming a Session`
    - `-282,1 +283,1` (base): `Closing Active Sessions`
    - `-288,1 +289,1` (base): `Closing Active Sessions > Checking Support`
    - `-312,1 +313,1` (base): `Closing Active Sessions > Closing a Session`
    - `-346,2 +347,4` (base): `Closing Active Sessions > Closing a Session`
    - `-349,1 +352,1` (base): `Additional Workspace Roots`
    - `-378,1 +381,1` (base): `Additional Workspace Roots`
    - `-382,1 +385,1` (base): `System Prompt (unstable)`
    - `-413,1 +416,1` (base): `System Prompt (unstable)`
    - `-415,0 +419,1` (target): `System prompt`
    - `-453,1 +457,1` (base): `Working Directory`
    - `-464,1 +468,9` (base): `MCP Servers`
    - `-472,1 +484,1` (base): `MCP Servers > Transport Types`
    - `-474,1 +486,1` (base): `MCP Servers > Transport Types > Stdio Transport`
    - `-494,1 +506,1` (base): `MCP Servers > Transport Types > Stdio Transport`
    - `-497,1 +509,1` (base): `MCP Servers > Transport Types > Stdio Transport`
    - `-519,1 +531,1` (base): `MCP Servers > Transport Types > HTTP Transport`
    - `-539,1 +551,1` (base): `MCP Servers > Transport Types > HTTP Transport`
    - `-542,1 +554,1` (base): `MCP Servers > Transport Types > HTTP Transport`
    - `-568,1 +580,1` (base): `MCP Servers > Transport Types > SSE Transport`
    - `-590,1 +602,1` (base): `MCP Servers > Transport Types > SSE Transport`
    - `-593,1 +605,1` (base): `MCP Servers > Transport Types > SSE Transport`
    - `-615,1 +627,1` (base): `MCP Servers > Checking Transport Support`
    - `-640,0 +653,10` (target): `MCP servers > Checking transport support` | `MCP servers > Security`
    
    ### `docs/protocol/v1/draft/slash-commands.mdx` (modified)
    
    - `-73,1 +73,1` (base): `Dynamic updates`
    
    ### `docs/protocol/v1/draft/terminals.mdx` (modified)
    
    - `-8,1 +8,1` (base): `Checking Support`
    - `-28,1 +28,1` (base): `Executing Commands`
    - `-104,1 +104,1` (base): `Executing Commands`
    - `-113,1 +113,1` (base): `Embedding in Tool Calls`
    - `-142,1 +142,1` (base): `Getting Output`
    - `-191,1 +191,1` (base): `Waiting for Exit`
    - `-228,1 +228,1` (base): `Killing Commands`
    - `-251,1 +251,1` (base): `Killing Commands > Building a Timeout`
    - `-264,1 +264,1` (base): `Releasing Terminals`
    - `-282,0 +283,7` (target): `Releasing terminals` | `Security`
    
    ### `docs/protocol/v1/draft/tool-calls.mdx` (modified)
    
    - `-6,1 +6,1` (base): `(intro)`
    - `-8,1 +8,1` (base): `(intro)`
    - `-10,1 +10,1` (base): `(intro)`
    - `-44,1 +44,1` (base): `Creating`
    - `-136,1 +136,1` (base): `Requesting Permission`
    - `-216,1 +216,1` (base): `Requesting Permission > Permission Options`
    - `-237,0 +238,16` (target): `Requesting permission > Permission options` | `Requesting permission > Security`
    - `-261,1 +277,1` (base): `Content > Regular Content`
    - `-320,0 +337,25` (target): `Content > Sessions (unstable)`
    - `-323,1 +364,1` (base): `Following the Agent`
    - `-337,3 +378,3` (base): `Following the Agent`
    - `-340,0 +382,2` (target): `Following the Agent`
    
    ### `docs/protocol/v1/draft/transports.mdx` (modified)
    
    - `-8,4 +8,1` (base): `(intro)`
    - `-44,5 +41,1` (base): `_Streamable HTTP_` | `Custom Transports`
    
    
    ## 3. Core hits
    
    - `docs/protocol/v1/draft/transports.mdx` (whole doc): `-8,4 +8,1`, `-44,5 +41,1`; code: `src/tck/common/harness`, `src/tck/v1/conformance/test_transport.py`, `src/tck/v1/conformance/test_diagnostics.py`
    - `docs/protocol/v1/draft/overview.mdx` (whole doc): `-12,2 +12,2`, `-15,1 +15,1`, `-23,1 +23,1`, `-49,1 +49,1`, `-82,1 +82,1`, `-103,1 +103,1`, `-123,1 +123,1`, `-136,1 +136,1`, `-233,1 +233,1`, `-240,0 +241,6`, `-243,1 +249,1`, `-249,1 +255,1`, `-251,1 +257,1`, `-253,5 +259,6`; code: `src/tck/v1/conformance/test_jsonrpc.py`, `src/tck/v1/validation.py`
    - `docs/protocol/v1/draft/extensibility.mdx` (whole doc): `-6,1 +6,1`, `-8,1 +8,1`, `-13,1 +13,1`, `-31,1 +31,1`, `-45,1 +45,1`, `-47,1 +47,1`, `-54,1 +54,1`, `-62,1 +62,1`, `-99,1 +99,1`, `-106,1 +106,1`, `-115,1 +115,1`, `-117,1 +117,1`, `-128,4 +128,2`, `-138,1 +136,1`; code: `src/tck/v1/conformance/test_extensibility.py`, `src/tck/v1/validation.py`
    - `docs/protocol/v1/draft/initialization.mdx` (whole doc): `-95,1 +95,1`, `-117,1 +117,1`, `-121,1 +121,1`, `-133,1 +133,1`, `-172,1 +172,18`, `-191,1 +208,1`, `-209,1 +226,1`, `-227,1 +244,1`, `-247,1 +264,1`, `-252,1 +269,1`, `-256,1 +273,1`, `-260,1 +277,1`, `-276,1 +293,1`, `-282,0 +300,7`, `-287,1 +311,1`, `-298,0 +323,8`, `-309,3 +341,3`, `-315,0 +348,14`, `-321,1 +367,1`, `-325,1 +371,1`, `-327,1 +373,1`, `-331,2 +377,3`, `-335,1 +382,1`; code: `src/tck/common/plugin.py`, `src/tck/v1/conformance/test_initialize.py`, `src/tck/v1/conformance/test_prompt_capabilities.py`, `src/tck/v1/conformance/_helpers.py`
    - `docs/protocol/v1/draft/session-setup.mdx` (section `(intro)`): `-6,1 +6,1`; code: `src/tck/v1/conformance/test_session.py`, `src/tck/v1/conformance/_helpers.py`
    - `docs/protocol/v1/draft/session-setup.mdx` (section `Working Directory`): `-453,1 +457,1`; code: `src/tck/v1/conformance/test_session.py`, `src/tck/v1/conformance/_helpers.py`
    - `docs/protocol/v1/draft/prompt-turn.mdx` (section `Session Updates`): `-10,1 +10,1`, `-14,21 +14,21`, `-46,3 +46,5`, `-50,1 +52,2`, `-59,1 +62,1`, `-62,1 +65,15`, `-69,1 +86,1`, `-72,1 +89,1`, `-78,4 +95,7`; code: `src/tck/v1/conformance/test_prompt.py`, `src/tck/v1/conformance/test_cancel.py`, `src/tck/v1/conformance/_helpers.py`
    - `docs/protocol/v1/draft/prompt-turn.mdx` (section `Stop Reasons`): `-578,1 +605,1`; code: `src/tck/v1/conformance/test_prompt.py`, `src/tck/v1/conformance/test_cancel.py`, `src/tck/v1/conformance/_helpers.py`
    - note: `docs/protocol/v1/draft/session-setup.mdx` section `Working Directory` at target: section address 'Working Directory' matches no heading; headings: ['Creating a session', 'Loading sessions', 'Checking support', 'Loading a session', 'Resuming sessions', 'Checking support', 'Resuming a session', 'Closing active sessions', 'Checking support', 'Closing a session', 'Additional workspace roots', 'System prompt', 'Session ID', 'Working directory', 'Workspace root security', 'MCP servers', 'Transport types', 'Stdio transport', 'HTTP transport', 'SSE transport', 'Checking transport support', 'Security']
    - note: `docs/protocol/v1/draft/prompt-turn.mdx` section `Session Updates` at target: section address 'Session Updates' matches no heading; headings: ['Session updates', 'Session-directed messages (unstable)', 'The prompt turn lifecycle', '1. User message', '2. Agent processing', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Check for completion', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Cancellation']
    - note: `docs/protocol/v1/draft/prompt-turn.mdx` section `Stop Reasons` at target: section address 'Stop Reasons' matches no heading; headings: ['Session updates', 'Session-directed messages (unstable)', 'The prompt turn lifecycle', '1. User message', '2. Agent processing', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Check for completion', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Cancellation']
    
    ## 4. Schema
    
    `$defs` compared between base and target `schema/v1/schema.unstable.json` (`(root)` = everything outside `$defs`).
    
    - Added: `ArchiveSessionRequest`, `ArchiveSessionResponse`, `AuthAccount`, `AuthState`, `AuthStatusCapabilities`, `AuthStatusRequest`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `InitializeProxyRequest`, `InitializeProxyResponse`, `ProxyNotification`, `ProxyRequest`, `ProxyResponse`, `ProxySuccessorNotification`, `ProxySuccessorRequest`, `ProxySuccessorResponse`, `SessionArchiveCapabilities`, `SessionArchiveFilter`, `SessionReference`, `SessionStatus`, `SessionStatusCapabilities`, `SessionStatusRequest`, `SessionStatusResponse`, `SessionTitleCapabilities`, `SetSessionTitleRequest`, `SetSessionTitleResponse`, `UnarchiveSessionRequest`, `UnarchiveSessionResponse`
    - Removed: none
    - Changed: `(root)`, `AgentAuthCapabilities`, `AgentCapabilities`, `AgentNotification`, `AgentRequest`, `AgentResponse`, `Annotations`, `AudioContent`, `AuthCapabilities`, `AuthMethodAgent`, `AuthMethodTerminal`, `AuthenticateRequest`, `AuthenticateResponse`, `AvailableCommand`, `AvailableCommandsUpdate`, `BlobResourceContents`, `BooleanConfigOptionCapabilities`, `BooleanPropertySchema`, `CancelNotification`, `CancelRequestNotification`, `ClientCapabilities`, `ClientNotification`, `ClientRequest`, `ClientSessionCapabilities`, `CloseSessionRequest`, `CloseSessionResponse`, `CompactionSummaryChunk`, `CompactionUpdate`, `CompleteElicitationNotification`, `ConfigOptionUpdate`, `Content`, `ContentBlock`, `ContentChunk`, `Cost`, `CreateElicitationRequest`, `CreateElicitationResponse`, `CreateTerminalRequest`, `CreateTerminalResponse`, `CurrentModeUpdate`, `DeleteSessionRequest`, `DeleteSessionResponse`, `Diff`, `DisableProviderRequest`, `DisableProviderResponse`, `ElicitationCapabilities`, `ElicitationContentValue`, `ElicitationFormCapabilities`, `ElicitationPropertySchema`, `ElicitationSchema`, `ElicitationSessionScope`, `ElicitationUrlCapabilities`, `EmbeddedResource`, `EnumOption`, `EnvVariable`, `ErrorCode`, `ExtNotification`, `ExtRequest`, `ExtResponse`, `FileSystemCapabilities`, `ForkSessionRequest`, `ForkSessionResponse`, `HttpHeader`, `IdleStateUpdate`, `ImageContent`, `Implementation`, `InitializeRequest`, `InitializeResponse`, `IntegerPropertySchema`, `KillTerminalRequest`, `KillTerminalResponse`, `ListProvidersRequest`, `ListProvidersResponse`, `ListSessionsRequest`, `ListSessionsResponse`, `LoadSessionRequest`, `LoadSessionResponse`, `LogoutCapabilities`, `LogoutRequest`, `LogoutResponse`, `McpCapabilities`, `McpError`, `McpServer`, `McpServerAcp`, `McpServerHttp`, `McpServerSse`, `McpServerStdio`, `MessageMcpNotification`, `MessageMcpRequest`, `MessageMcpResponse`, `MultiSelectItems`, `MultiSelectPropertySchema`, `NewSessionRequest`, `NewSessionResponse`, `Notice`, `NumberPropertySchema`, `PermissionOption`, `Plan`, `PlanCapabilities`, `PlanEntry`, `PlanEntryPriority`, `PlanEntryStatus`, `PlanFile`, `PlanItems`, `PlanMarkdown`, `PlanRemoved`, `PlanUpdate`, `PromptCapabilities`, `PromptRequest`, `PromptResponse`, `ProviderCurrentConfig`, `ProviderInfo`, `ProvidersCapabilities`, `ReadTextFileRequest`, `ReadTextFileResponse`, `ReleaseTerminalRequest`, `ReleaseTerminalResponse`, `RequestPermissionOutcome`, `RequestPermissionRequest`, `RequestPermissionResponse`, `RequiresActionStateUpdate`, `ResourceLink`, `ResumeSessionRequest`, `ResumeSessionResponse`, `RunningStateUpdate`, `SelectedPermissionOutcome`, `SessionAdditionalDirectoriesCapabilities`, `SessionCancelCapabilities`, `SessionCapabilities`, `SessionCloseCapabilities`, `SessionConfigOption`, `SessionConfigOptionsCapabilities`, `SessionConfigSelectGroup`, `SessionConfigSelectOption`, `SessionDeleteCapabilities`, `SessionForkCapabilities`, `SessionId`, `SessionInfo`, `SessionInfoUpdate`, `SessionListCapabilities`, `SessionMessage`, `SessionMessageChunk`, `SessionMode`, `SessionModeState`, `SessionNotification`, `SessionResumeCapabilities`, `SessionSystemPromptCapabilities`, `SessionSystemPromptModeCapabilities`, `SessionSystemPromptOverrideCapabilities`, `SessionUpdate`, `SetProviderRequest`, `SetProviderResponse`, `SetSessionConfigOptionRequest`, `SetSessionConfigOptionResponse`, `SetSessionModeRequest`, `SetSessionModeResponse`, `StateUpdate`, `StopReason`, `StringMultiSelectItems`, `StringPropertySchema`, `SubagentSessionCapabilities`, `SubagentUpdate`, `SystemPrompt`, `SystemPromptMode`, `Terminal`, `TerminalExitStatus`, `TerminalOutputRequest`, `TerminalOutputResponse`, `TextContent`, `TextResourceContents`, `TitledMultiSelectItems`, `ToolCall`, `ToolCallContent`, `ToolCallLocation`, `ToolCallStatus`, `ToolCallUpdate`, `ToolKind`, `UnknownStateUpdate`, `UnstructuredCommandInput`, `Usage`, `UsageUpdate`, `WaitForTerminalExitRequest`, `WaitForTerminalExitResponse`, `WriteTextFileRequest`, `WriteTextFileResponse`
    - `$ref` closure (12 defs that transitively reference a changed def):
      - `AuthMethod` -> `AuthMethodAgent`, `AuthMethodTerminal`
      - `AvailableCommandInput` -> `UnstructuredCommandInput`
      - `ClientResponse` -> `CreateElicitationResponse`, `CreateTerminalResponse`, `ElicitationContentValue`, `ErrorCode`, `ExtResponse`, `KillTerminalResponse`, `McpError`, `MessageMcpResponse` and 9 more
      - `ElicitationAcceptAction` -> `ElicitationContentValue`
      - `ElicitationFormMode` -> `BooleanPropertySchema`, `ElicitationPropertySchema`, `ElicitationSchema`, `ElicitationSessionScope`, `EnumOption`, `IntegerPropertySchema`, `MultiSelectItems`, `MultiSelectPropertySchema` and 5 more
      - `ElicitationUrlMode` -> `ElicitationSessionScope`, `SessionId`
      - `EmbeddedResourceResource` -> `BlobResourceContents`, `TextResourceContents`
      - `Error` -> `ErrorCode`
      - `ErrorStopReason` -> `ErrorCode`
      - `PlanUpdateContent` -> `PlanEntry`, `PlanEntryPriority`, `PlanEntryStatus`, `PlanFile`, `PlanItems`, `PlanMarkdown`
      - `SessionConfigSelect` -> `SessionConfigSelectGroup`, `SessionConfigSelectOption`
      - `SessionConfigSelectOptions` -> `SessionConfigSelectGroup`, `SessionConfigSelectOption`
    - Core `$defs` hit: `ErrorCode` (changed directly); `SessionUpdate` (changed directly); `ContentBlock` (changed directly); `AgentCapabilities` (changed directly); `ClientCapabilities` (changed directly)
    
    ## 5. Link fan-out
    
    Docs under `docs/protocol/v1/draft/` at target that link to a changed doc.
    
    ### `docs/protocol/v1/draft/agent-plan.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:184` `#plan-operations` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:220`
    - `docs/protocol/v1/draft/prompt-turn.mdx:24`
    - `docs/protocol/v1/draft/prompt-turn.mdx:25` `#plan-operations` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:26` `#removing-plans` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:244`
    - `docs/protocol/v1/draft/schema.mdx:5901`
    - `docs/protocol/v1/draft/schema.mdx:5950` `#plan-entries` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:5981` `#plan-entries` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:6002` `#plan-entries` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:7775`
    
    ### `docs/protocol/v1/draft/authentication.mdx`
    
    - `docs/protocol/v1/draft/error.mdx:34`
    - `docs/protocol/v1/draft/initialization.mdx:129`
    - `docs/protocol/v1/draft/initialization.mdx:296` `#logging-out` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:307`
    - `docs/protocol/v1/draft/overview.mdx:97` `#logging-out` (changed section)
    - `docs/protocol/v1/draft/security.mdx:66` `#launch-safety` (changed section)
    - `docs/protocol/v1/draft/session-setup.mdx:10`
    
    ### `docs/protocol/v1/draft/cancellation.mdx`
    
    - `docs/protocol/v1/draft/error.mdx:33`
    - `docs/protocol/v1/draft/schema.mdx:2794`
    - `docs/protocol/v1/draft/schema.mdx:2800`
    
    ### `docs/protocol/v1/draft/content.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:254`
    - `docs/protocol/v1/draft/initialization.mdx:266`
    - `docs/protocol/v1/draft/overview.mdx:218`
    - `docs/protocol/v1/draft/prompt-turn.mdx:195`
    - `docs/protocol/v1/draft/prompt-turn.mdx:416`
    - `docs/protocol/v1/draft/schema.mdx:3701`
    - `docs/protocol/v1/draft/tool-calls.mdx:279`
    
    ### `docs/protocol/v1/draft/elicitation.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:168`
    - `docs/protocol/v1/draft/overview.mdx:196`
    - `docs/protocol/v1/draft/overview.mdx:207` `#url-completion` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:1659` `#url-completion` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:1688`
    - `docs/protocol/v1/draft/security.mdx:70`
    
    ### `docs/protocol/v1/draft/error.mdx`
    
    - `docs/protocol/v1/draft/overview.mdx:241`
    - `docs/protocol/v1/draft/session-setup.mdx:350` `#unknown-sessions` (changed section)
    
    ### `docs/protocol/v1/draft/extensibility.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:115` `#advertising-custom-capabilities` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:255`
    - `docs/protocol/v1/draft/overview.mdx:263`
    - `docs/protocol/v1/draft/schema.mdx:52`
    - `docs/protocol/v1/draft/schema.mdx:73`
    - `docs/protocol/v1/draft/schema.mdx:120`
    - `docs/protocol/v1/draft/schema.mdx:141`
    - `docs/protocol/v1/draft/schema.mdx:176`
    - `docs/protocol/v1/draft/schema.mdx:212`
    - `docs/protocol/v1/draft/schema.mdx:263`
    - `docs/protocol/v1/draft/schema.mdx:280`
    - `docs/protocol/v1/draft/schema.mdx:313`
    - `docs/protocol/v1/draft/schema.mdx:358`
    - `docs/protocol/v1/draft/schema.mdx:382`
    - `docs/protocol/v1/draft/schema.mdx:412`
    - `docs/protocol/v1/draft/schema.mdx:433`
    - `docs/protocol/v1/draft/schema.mdx:468`
    - `docs/protocol/v1/draft/schema.mdx:502`
    - `docs/protocol/v1/draft/schema.mdx:541`
    - `docs/protocol/v1/draft/schema.mdx:565`
    - `docs/protocol/v1/draft/schema.mdx:600`
    - `docs/protocol/v1/draft/schema.mdx:636`
    - `docs/protocol/v1/draft/schema.mdx:656`
    - `docs/protocol/v1/draft/schema.mdx:682`
    - `docs/protocol/v1/draft/schema.mdx:702`
    - `docs/protocol/v1/draft/schema.mdx:747`
    - `docs/protocol/v1/draft/schema.mdx:795`
    - `docs/protocol/v1/draft/schema.mdx:835`
    - `docs/protocol/v1/draft/schema.mdx:870`
    - `docs/protocol/v1/draft/schema.mdx:913`
    - `docs/protocol/v1/draft/schema.mdx:958`
    - `docs/protocol/v1/draft/schema.mdx:1003`
    - `docs/protocol/v1/draft/schema.mdx:1044`
    - `docs/protocol/v1/draft/schema.mdx:1096`
    - `docs/protocol/v1/draft/schema.mdx:1134`
    - `docs/protocol/v1/draft/schema.mdx:1177`
    - `docs/protocol/v1/draft/schema.mdx:1222`
    - `docs/protocol/v1/draft/schema.mdx:1253`
    - `docs/protocol/v1/draft/schema.mdx:1313`
    - `docs/protocol/v1/draft/schema.mdx:1350`
    - `docs/protocol/v1/draft/schema.mdx:1373`
    - `docs/protocol/v1/draft/schema.mdx:1416`
    - `docs/protocol/v1/draft/schema.mdx:1449`
    - `docs/protocol/v1/draft/schema.mdx:1494`
    - `docs/protocol/v1/draft/schema.mdx:1521`
    - `docs/protocol/v1/draft/schema.mdx:1567`
    - `docs/protocol/v1/draft/schema.mdx:1591`
    - `docs/protocol/v1/draft/schema.mdx:1635`
    - `docs/protocol/v1/draft/schema.mdx:1676`
    - `docs/protocol/v1/draft/schema.mdx:1709`
    - `docs/protocol/v1/draft/schema.mdx:1915`
    - `docs/protocol/v1/draft/schema.mdx:2010`
    - `docs/protocol/v1/draft/schema.mdx:2045`
    - `docs/protocol/v1/draft/schema.mdx:2077`
    - `docs/protocol/v1/draft/schema.mdx:2103`
    - `docs/protocol/v1/draft/schema.mdx:2133`
    - `docs/protocol/v1/draft/schema.mdx:2228`
    - `docs/protocol/v1/draft/schema.mdx:2254`
    - `docs/protocol/v1/draft/schema.mdx:2293`
    - `docs/protocol/v1/draft/schema.mdx:2334`
    - `docs/protocol/v1/draft/schema.mdx:2379`
    - `docs/protocol/v1/draft/schema.mdx:2415`
    - `docs/protocol/v1/draft/schema.mdx:2438`
    - `docs/protocol/v1/draft/schema.mdx:2465`
    - `docs/protocol/v1/draft/schema.mdx:2488`
    - `docs/protocol/v1/draft/schema.mdx:2530`
    - `docs/protocol/v1/draft/schema.mdx:2553`
    - `docs/protocol/v1/draft/schema.mdx:2577`
    - `docs/protocol/v1/draft/schema.mdx:2600`
    - `docs/protocol/v1/draft/schema.mdx:2695`
    - `docs/protocol/v1/draft/schema.mdx:2744`
    - `docs/protocol/v1/draft/schema.mdx:2811`
    - `docs/protocol/v1/draft/schema.mdx:2831`
    - `docs/protocol/v1/draft/schema.mdx:2871`
    - `docs/protocol/v1/draft/schema.mdx:2929`
    - `docs/protocol/v1/draft/schema.mdx:2955`
    - `docs/protocol/v1/draft/schema.mdx:2990`
    - `docs/protocol/v1/draft/schema.mdx:3041`
    - `docs/protocol/v1/draft/schema.mdx:3075`
    - `docs/protocol/v1/draft/schema.mdx:3113`
    - `docs/protocol/v1/draft/schema.mdx:3144`
    - `docs/protocol/v1/draft/schema.mdx:3182`
    - `docs/protocol/v1/draft/schema.mdx:3257`
    - `docs/protocol/v1/draft/schema.mdx:3274`
    - `docs/protocol/v1/draft/schema.mdx:3302`
    - `docs/protocol/v1/draft/schema.mdx:3322`
    - `docs/protocol/v1/draft/schema.mdx:3342`
    - `docs/protocol/v1/draft/schema.mdx:3370`
    - `docs/protocol/v1/draft/schema.mdx:3389`
    - `docs/protocol/v1/draft/schema.mdx:3429`
    - `docs/protocol/v1/draft/schema.mdx:3506`
    - `docs/protocol/v1/draft/schema.mdx:3661`
    - `docs/protocol/v1/draft/schema.mdx:3681`
    - `docs/protocol/v1/draft/schema.mdx:3718`
    - `docs/protocol/v1/draft/schema.mdx:3746`
    - `docs/protocol/v1/draft/schema.mdx:3780`
    - `docs/protocol/v1/draft/schema.mdx:3811`
    - `docs/protocol/v1/draft/schema.mdx:3856`
    - `docs/protocol/v1/draft/schema.mdx:3885`
    - `docs/protocol/v1/draft/schema.mdx:3912`
    - `docs/protocol/v1/draft/schema.mdx:3938`
    - `docs/protocol/v1/draft/schema.mdx:3962`
    - `docs/protocol/v1/draft/schema.mdx:4002`
    - `docs/protocol/v1/draft/schema.mdx:4063`
    - `docs/protocol/v1/draft/schema.mdx:4149`
    - `docs/protocol/v1/draft/schema.mdx:4227`
    - `docs/protocol/v1/draft/schema.mdx:4279`
    - `docs/protocol/v1/draft/schema.mdx:4331`
    - `docs/protocol/v1/draft/schema.mdx:4371`
    - `docs/protocol/v1/draft/schema.mdx:4478`
    - `docs/protocol/v1/draft/schema.mdx:4562`
    - `docs/protocol/v1/draft/schema.mdx:4635`
    - `docs/protocol/v1/draft/schema.mdx:4661`
    - `docs/protocol/v1/draft/schema.mdx:4687`
    - `docs/protocol/v1/draft/schema.mdx:4718`
    - `docs/protocol/v1/draft/schema.mdx:4747`
    - `docs/protocol/v1/draft/schema.mdx:4861`
    - `docs/protocol/v1/draft/schema.mdx:4869`
    - `docs/protocol/v1/draft/schema.mdx:4877`
    - `docs/protocol/v1/draft/schema.mdx:4894`
    - `docs/protocol/v1/draft/schema.mdx:4923`
    - `docs/protocol/v1/draft/schema.mdx:5083`
    - `docs/protocol/v1/draft/schema.mdx:5114`
    - `docs/protocol/v1/draft/schema.mdx:5148`
    - `docs/protocol/v1/draft/schema.mdx:5236`
    - `docs/protocol/v1/draft/schema.mdx:5253`
    - `docs/protocol/v1/draft/schema.mdx:5338`
    - `docs/protocol/v1/draft/schema.mdx:5369`
    - `docs/protocol/v1/draft/schema.mdx:5405`
    - `docs/protocol/v1/draft/schema.mdx:5437`
    - `docs/protocol/v1/draft/schema.mdx:5476`
    - `docs/protocol/v1/draft/schema.mdx:5516`
    - `docs/protocol/v1/draft/schema.mdx:5542`
    - `docs/protocol/v1/draft/schema.mdx:5568`
    - `docs/protocol/v1/draft/schema.mdx:5608`
    - `docs/protocol/v1/draft/schema.mdx:5652`
    - `docs/protocol/v1/draft/schema.mdx:5677`
    - `docs/protocol/v1/draft/schema.mdx:5803`
    - `docs/protocol/v1/draft/schema.mdx:5850`
    - `docs/protocol/v1/draft/schema.mdx:5912`
    - `docs/protocol/v1/draft/schema.mdx:5940`
    - `docs/protocol/v1/draft/schema.mdx:5961`
    - `docs/protocol/v1/draft/schema.mdx:6035`
    - `docs/protocol/v1/draft/schema.mdx:6072`
    - `docs/protocol/v1/draft/schema.mdx:6103`
    - `docs/protocol/v1/draft/schema.mdx:6130`
    - `docs/protocol/v1/draft/schema.mdx:6154`
    - `docs/protocol/v1/draft/schema.mdx:6181`
    - `docs/protocol/v1/draft/schema.mdx:6211`
    - `docs/protocol/v1/draft/schema.mdx:6237`
    - `docs/protocol/v1/draft/schema.mdx:6277`
    - `docs/protocol/v1/draft/schema.mdx:6333`
    - `docs/protocol/v1/draft/schema.mdx:6370`
    - `docs/protocol/v1/draft/schema.mdx:6407`
    - `docs/protocol/v1/draft/schema.mdx:6471`
    - `docs/protocol/v1/draft/schema.mdx:6511`
    - `docs/protocol/v1/draft/schema.mdx:6577`
    - `docs/protocol/v1/draft/schema.mdx:6602`
    - `docs/protocol/v1/draft/schema.mdx:6626`
    - `docs/protocol/v1/draft/schema.mdx:6683`
    - `docs/protocol/v1/draft/schema.mdx:6708`
    - `docs/protocol/v1/draft/schema.mdx:6822`
    - `docs/protocol/v1/draft/schema.mdx:6863`
    - `docs/protocol/v1/draft/schema.mdx:6969`
    - `docs/protocol/v1/draft/schema.mdx:7018`
    - `docs/protocol/v1/draft/schema.mdx:7044`
    - `docs/protocol/v1/draft/schema.mdx:7092`
    - `docs/protocol/v1/draft/schema.mdx:7115`
    - `docs/protocol/v1/draft/schema.mdx:7143`
    - `docs/protocol/v1/draft/schema.mdx:7194`
    - `docs/protocol/v1/draft/schema.mdx:7219`
    - `docs/protocol/v1/draft/schema.mdx:7320`
    - `docs/protocol/v1/draft/schema.mdx:7352`
    - `docs/protocol/v1/draft/schema.mdx:7385`
    - `docs/protocol/v1/draft/schema.mdx:7407`
    - `docs/protocol/v1/draft/schema.mdx:7467`
    - `docs/protocol/v1/draft/schema.mdx:7487`
    - `docs/protocol/v1/draft/schema.mdx:7513`
    - `docs/protocol/v1/draft/schema.mdx:7541`
    - `docs/protocol/v1/draft/schema.mdx:7565`
    - `docs/protocol/v1/draft/schema.mdx:7589`
    - `docs/protocol/v1/draft/schema.mdx:7619`
    - `docs/protocol/v1/draft/schema.mdx:7649`
    - `docs/protocol/v1/draft/schema.mdx:7679`
    - `docs/protocol/v1/draft/schema.mdx:7732`
    - `docs/protocol/v1/draft/schema.mdx:7784`
    - `docs/protocol/v1/draft/schema.mdx:7815`
    - `docs/protocol/v1/draft/schema.mdx:7842`
    - `docs/protocol/v1/draft/schema.mdx:7865`
    - `docs/protocol/v1/draft/schema.mdx:7890`
    - `docs/protocol/v1/draft/schema.mdx:7913`
    - `docs/protocol/v1/draft/schema.mdx:7936`
    - `docs/protocol/v1/draft/schema.mdx:7962`
    - `docs/protocol/v1/draft/schema.mdx:8118`
    - `docs/protocol/v1/draft/schema.mdx:8565`
    - `docs/protocol/v1/draft/schema.mdx:8590`
    - `docs/protocol/v1/draft/schema.mdx:8736`
    - `docs/protocol/v1/draft/schema.mdx:8814`
    - `docs/protocol/v1/draft/schema.mdx:8895`
    - `docs/protocol/v1/draft/schema.mdx:8915`
    - `docs/protocol/v1/draft/schema.mdx:8947`
    - `docs/protocol/v1/draft/schema.mdx:8970`
    - `docs/protocol/v1/draft/schema.mdx:8998`
    - `docs/protocol/v1/draft/schema.mdx:9023`
    - `docs/protocol/v1/draft/schema.mdx:9081`
    - `docs/protocol/v1/draft/schema.mdx:9104`
    - `docs/protocol/v1/draft/schema.mdx:9137`
    - `docs/protocol/v1/draft/schema.mdx:9164`
    - `docs/protocol/v1/draft/schema.mdx:9201`
    - `docs/protocol/v1/draft/schema.mdx:9259`
    - `docs/protocol/v1/draft/schema.mdx:9384`
    - `docs/protocol/v1/draft/schema.mdx:9408`
    - `docs/protocol/v1/draft/schema.mdx:9461`
    - `docs/protocol/v1/draft/session-list.mdx:155`
    - `docs/protocol/v1/draft/session-list.mdx:210`
    
    ### `docs/protocol/v1/draft/file-system.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:143`
    - `docs/protocol/v1/draft/overview.mdx:142` `#reading-files` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:150` `#writing-files` (changed section)
    - `docs/protocol/v1/draft/security.mdx:12`
    - `docs/protocol/v1/draft/security.mdx:69` `#security` (changed section)
    - `docs/protocol/v1/draft/tool-calls.mdx:10`
    
    ### `docs/protocol/v1/draft/initialization.mdx`
    
    - `docs/protocol/v1/draft/agent-plan.mdx:10` `#client-capabilities` (changed section)
    - `docs/protocol/v1/draft/authentication.mdx:7`
    - `docs/protocol/v1/draft/content.mdx:55` `#prompt-capabilities` (changed section)
    - `docs/protocol/v1/draft/content.mdx:88` `#prompt-capabilities` (changed section)
    - `docs/protocol/v1/draft/content.mdx:124` `#prompt-capabilities` (changed section)
    - `docs/protocol/v1/draft/elicitation.mdx:27` `#client-capabilities` (changed section)
    - `docs/protocol/v1/draft/file-system.mdx:10` `#client-capabilities` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:56`
    - `docs/protocol/v1/draft/overview.mdx:260`
    - `docs/protocol/v1/draft/prompt-turn.mdx:8`
    - `docs/protocol/v1/draft/prompt-turn.mdx:193` `#prompt-capabilities` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:193`
    - `docs/protocol/v1/draft/schema.mdx:103`
    - `docs/protocol/v1/draft/schema.mdx:157`
    - `docs/protocol/v1/draft/schema.mdx:165`
    - `docs/protocol/v1/draft/schema.mdx:201`
    - `docs/protocol/v1/draft/schema.mdx:2860` `#agent-capabilities` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:3418` `#client-capabilities` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:4883` `#filesystem` (unknown anchor)
    - `docs/protocol/v1/draft/schema.mdx:6266` `#prompt-capabilities` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:6697` `#session-capabilities` (changed section)
    - `docs/protocol/v1/draft/session-delete.mdx:8`
    - `docs/protocol/v1/draft/session-list.mdx:10`
    - `docs/protocol/v1/draft/session-setup.mdx:8`
    - `docs/protocol/v1/draft/terminals.mdx:10` `#client-capabilities` (changed section)
    
    ### `docs/protocol/v1/draft/overview.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:6` `#client` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:6` `#agent` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:6` `#client` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:6` `#agent` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:1993` `#client` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:2060` `#client` (changed section)
    - `docs/protocol/v1/draft/session-setup.mdx:6` `#client` (changed section)
    - `docs/protocol/v1/draft/session-setup.mdx:6` `#agent` (changed section)
    
    ### `docs/protocol/v1/draft/prompt-turn.mdx`
    
    - `docs/protocol/v1/draft/agent-plan.mdx:8` `#3-agent-reports-output` (changed section)
    - `docs/protocol/v1/draft/cancellation.mdx:26` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/cancellation.mdx:42` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/content.mdx:10` `#1-user-message` (changed section)
    - `docs/protocol/v1/draft/content.mdx:11` `#3-agent-reports-output` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:221` `#session-compaction` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:239` `#session-notices` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:78` `#1-user-message` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:115` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:215` `#3-agent-reports-output` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:223` `#session-notices` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:224` `#session-compaction` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:262`
    - `docs/protocol/v1/draft/schema.mdx:583` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:589` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:1077`
    - `docs/protocol/v1/draft/schema.mdx:1085` `#1-user-message` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:1123` `#4-check-for-completion` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:2274` `#3-agent-reports-output` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:2282` `#3-agent-reports-output` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:6450` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:7575` `#3-agent-reports-output` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:8495` `#stop-reasons` (changed section)
    - `docs/protocol/v1/draft/session-setup.mdx:139` `#session-compaction` (changed section)
    - `docs/protocol/v1/draft/session-setup.mdx:144` `#session-notices` (changed section)
    - `docs/protocol/v1/draft/session-setup.mdx:334` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/slash-commands.mdx:6`
    - `docs/protocol/v1/draft/tool-calls.mdx:6`
    - `docs/protocol/v1/draft/tool-calls.mdx:8` `#3-agent-reports-output` (changed section)
    - `docs/protocol/v1/draft/tool-calls.mdx:196` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/tool-calls.mdx:212` `#cancellation` (unchanged section)
    - `docs/protocol/v1/draft/tool-calls.mdx:359` `#session-directed-messages-unstable` (changed section)
    
    ### `docs/protocol/v1/draft/schema.mdx`
    
    - `docs/protocol/v1/draft/authentication.mdx:130` `#authmethod` (changed section)
    - `docs/protocol/v1/draft/cancellation.mdx:22` `#errorcode` (changed section)
    - `docs/protocol/v1/draft/elicitation.mdx:193` `#elicitation%2Fcreate` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:53` `#initialize` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:61` `#authenticate` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:68` `#session%2Fnew` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:76` `#session%2Fprompt` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:86` `#session%2Fload` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:94` `#logout` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:103` `#session%2Fset_mode` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:113` `#session%2Fcancel` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:128` `#session%2Frequest_permission` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:140` `#fs%2Fread_text_file` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:148` `#fs%2Fwrite_text_file` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:156` `#terminal%2Fcreate` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:164` `#terminal%2Foutput` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:171` `#terminal%2Frelease` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:179` `#terminal%2Fwait_for_exit` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:187` `#terminal%2Fkill` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:194` `#elicitation%2Fcreate` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:204` `#elicitation%2Fcomplete` (unchanged section)
    - `docs/protocol/v1/draft/overview.mdx:213` `#session%2Fupdate` (unchanged section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:36` `#sessionupdate` (changed section)
    - `docs/protocol/v1/draft/session-modes.mdx:83` `#session%2Fset_mode` (changed section)
    
    ### `docs/protocol/v1/draft/security.mdx`
    
    - `docs/protocol/v1/draft/content.mdx:16` `#rendering-agent-content` (changed section)
    - `docs/protocol/v1/draft/content.mdx:16` `#uris-and-remote-resources` (changed section)
    - `docs/protocol/v1/draft/content.mdx:22` `#rendering-agent-content` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:259`
    
    ### `docs/protocol/v1/draft/session-config-options.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:203`
    - `docs/protocol/v1/draft/prompt-turn.mdx:29` `#from-the-agent` (changed section)
    - `docs/protocol/v1/draft/session-modes.mdx:8`
    
    ### `docs/protocol/v1/draft/session-delete.mdx`
    
    - `docs/protocol/v1/draft/error.mdx:55`
    - `docs/protocol/v1/draft/initialization.mdx:318`
    - `docs/protocol/v1/draft/session-list.mdx:63`
    
    ### `docs/protocol/v1/draft/session-list.mdx`
    
    - `docs/protocol/v1/draft/error.mdx:67` `#archived-sessions-unstable` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:328` `#archived-sessions-unstable` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:30` `#updating-session-metadata` (changed section)
    
    ### `docs/protocol/v1/draft/session-modes.mdx`
    
    - `docs/protocol/v1/draft/overview.mdx:106` `#setting-the-current-mode` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:222` `#from-the-agent` (unchanged section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:28` `#from-the-agent` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:804`
    - `docs/protocol/v1/draft/schema.mdx:967`
    - `docs/protocol/v1/draft/schema.mdx:1053`
    - `docs/protocol/v1/draft/schema.mdx:1231`
    - `docs/protocol/v1/draft/schema.mdx:1335`
    - `docs/protocol/v1/draft/schema.mdx:3927`
    - `docs/protocol/v1/draft/schema.mdx:7309`
    - `docs/protocol/v1/draft/schema.mdx:7881`
    - `docs/protocol/v1/draft/session-config-options.mdx:11`
    - `docs/protocol/v1/draft/session-config-options.mdx:462`
    - `docs/protocol/v1/draft/session-config-options.mdx:473`
    - `docs/protocol/v1/draft/session-list.mdx:179`
    
    ### `docs/protocol/v1/draft/session-setup.mdx`
    
    - `docs/protocol/v1/draft/error.mdx:49` `#system-prompt` (changed section)
    - `docs/protocol/v1/draft/error.mdx:55` `#closing-active-sessions` (changed section)
    - `docs/protocol/v1/draft/file-system.mdx:50` `#session-id` (unchanged section)
    - `docs/protocol/v1/draft/file-system.mdx:96` `#session-id` (unchanged section)
    - `docs/protocol/v1/draft/file-system.mdx:125` `#workspace-root-security` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:249` `#loading-sessions` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:342` `#system-prompt` (changed section)
    - `docs/protocol/v1/draft/initialization.mdx:393`
    - `docs/protocol/v1/draft/overview.mdx:71` `#creating-a-session` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:88` `#loading-sessions` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:261`
    - `docs/protocol/v1/draft/prompt-turn.mdx:8`
    - `docs/protocol/v1/draft/prompt-turn.mdx:38` `#loading-sessions` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:188` `#session-id` (unchanged section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:491` `#loading-sessions` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:894` `#loading-sessions` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:902` `#loading-sessions` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:986`
    - `docs/protocol/v1/draft/schema.mdx:992` `#creating-a-session` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:1033` `#creating-a-session` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:5322` `#mcp-servers` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:7126` `#session-id` (unchanged section)
    - `docs/protocol/v1/draft/security.mdx:37` `#workspace-root-security` (changed section)
    - `docs/protocol/v1/draft/security.mdx:51` `#system-prompt` (changed section)
    - `docs/protocol/v1/draft/security.mdx:65` `#workspace-root-security` (changed section)
    - `docs/protocol/v1/draft/security.mdx:67` `#security` (changed section)
    - `docs/protocol/v1/draft/session-config-options.mdx:17`
    - `docs/protocol/v1/draft/session-list.mdx:225` `#loading-sessions` (changed section)
    - `docs/protocol/v1/draft/session-list.mdx:256` `#closing-active-sessions` (changed section)
    - `docs/protocol/v1/draft/session-modes.mdx:17`
    - `docs/protocol/v1/draft/terminals.mdx:54` `#session-id` (unchanged section)
    - `docs/protocol/v1/draft/terminals.mdx:288` `#workspace-root-security` (changed section)
    - `docs/protocol/v1/draft/tool-calls.mdx:383` `#workspace-root-security` (changed section)
    
    ### `docs/protocol/v1/draft/slash-commands.mdx`
    
    - `docs/protocol/v1/draft/overview.mdx:221` `#advertising-commands` (unchanged section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:27`
    - `docs/protocol/v1/draft/security.mdx:27`
    - `docs/protocol/v1/draft/session-list.mdx:179`
    
    ### `docs/protocol/v1/draft/terminals.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:154`
    - `docs/protocol/v1/draft/overview.mdx:158`
    - `docs/protocol/v1/draft/schema.mdx:2319`
    - `docs/protocol/v1/draft/schema.mdx:2400`
    - `docs/protocol/v1/draft/schema.mdx:2450`
    - `docs/protocol/v1/draft/schema.mdx:2515`
    - `docs/protocol/v1/draft/schema.mdx:2562`
    - `docs/protocol/v1/draft/schema.mdx:8884`
    - `docs/protocol/v1/draft/schema.mdx:9128`
    - `docs/protocol/v1/draft/security.mdx:12`
    - `docs/protocol/v1/draft/security.mdx:69` `#security` (changed section)
    - `docs/protocol/v1/draft/tool-calls.mdx:333`
    
    ### `docs/protocol/v1/draft/tool-calls.mdx`
    
    - `docs/protocol/v1/draft/content.mdx:12`
    - `docs/protocol/v1/draft/overview.mdx:132` `#requesting-permission` (changed section)
    - `docs/protocol/v1/draft/overview.mdx:219`
    - `docs/protocol/v1/draft/prompt-turn.mdx:22` `#creating` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:23` `#updating` (unchanged section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:595`
    - `docs/protocol/v1/draft/schema.mdx:2209` `#requesting-permission` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:2217` `#requesting-permission` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:3951` `#content` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:9012`
    - `docs/protocol/v1/draft/schema.mdx:9067` `#content` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:9190` `#following-the-agent` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:9220` `#status` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:9248` `#updating` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:9301` `#creating` (changed section)
    - `docs/protocol/v1/draft/security.mdx:68` `#security` (changed section)
    - `docs/protocol/v1/draft/session-modes.mdx:178` `#requesting-permission` (changed section)
    - `docs/protocol/v1/draft/terminals.mdx:115`
    
    ### `docs/protocol/v1/draft/transports.mdx`
    
    - `docs/protocol/v1/draft/security.mdx:61` `#custom-transports` (changed section)
    
    ### `docs/rfds/get-auth-state.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:301`
    
    ### `docs/rfds/proxy-chains.mdx`
    
    - `docs/protocol/v1/draft/schema.mdx:2645`
    - `docs/protocol/v1/draft/schema.mdx:2680`
    - `docs/protocol/v1/draft/schema.mdx:2729`
    
    ### `docs/rfds/session-archive.mdx`
    
    - `docs/protocol/v1/draft/session-list.mdx:229`
    
    ### `docs/rfds/session-set-title.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:355`
    
    ### `docs/rfds/session-status.mdx`
    
    - `docs/protocol/v1/draft/initialization.mdx:349`
    - `docs/protocol/v1/draft/session-list.mdx:259`
    
    ### `docs/rfds/streamable-http-websocket-transport.mdx`
    
    - `docs/protocol/v1/draft/transports.mdx:8`
    
    ### `docs/rfds/subagents.mdx`
    
    - `docs/protocol/v1/draft/prompt-turn.mdx:103` `#session-directed-messages` (changed section)
    - `docs/protocol/v1/draft/prompt-turn.mdx:111` `#delegated-tasks` (changed section)
    - `docs/protocol/v1/draft/schema.mdx:4953` `#current-work-state` (unchanged section)
    - `docs/protocol/v1/draft/schema.mdx:8319` `#current-work-state` (unchanged section)
    - `docs/protocol/v1/draft/tool-calls.mdx:340`
    
    
    ## 6. Affected entries
    
    - ACP-JSONRPC-002: `#/$defs/Error`: `Error` in $ref closure of `ErrorCode`
    - ACP-JSONRPC-006: `docs/protocol/v1/draft/cancellation.mdx:12-14` overlaps hunk `-12,1 +12,1`, `-14,1 +14,1`; `#/anyOf/2/properties/params/anyOf/0`: `(root)` changed; `#/$defs/CancelRequestNotification`: `CancelRequestNotification` changed
    - ACP-JSONRPC-007: `docs/protocol/v1/draft/cancellation.mdx:16-22` overlaps hunk `-21,1 +21,1`; `#/$defs/CancelRequestNotification`: `CancelRequestNotification` changed; `#/$defs/ErrorCode`: `ErrorCode` changed
    - ACP-INIT-001: `#/$defs/InitializeResponse`: `InitializeResponse` changed
    - ACP-INIT-004: `#/$defs/Implementation`: `Implementation` changed
    - ACP-SCHEMA-001: `#/anyOf/0`: `(root)` changed
    - ACP-SESSION-001: `#/$defs/NewSessionResponse`: `NewSessionResponse` changed
    - ACP-SESSION-002: `#/$defs/NewSessionResponse`: `NewSessionResponse` changed
    - ACP-SESSION-003: `docs/protocol/v1/draft/session-setup.mdx:476-501` overlaps hunk `-494,1 +506,1`, `-497,1 +509,1`; `#/$defs/McpServer`: `McpServer` changed; `#/$defs/McpServerStdio`: `McpServerStdio` changed
    - ACP-PROMPT-001: `docs/protocol/v1/draft/initialization.mdx:247` overlaps hunk `-247,1 +264,1`; `#/$defs/PromptResponse`: `PromptResponse` changed; `#/$defs/StopReason`: `StopReason` changed
    - ACP-PROMPT-002: `#/$defs/SessionNotification`: `SessionNotification` changed
    - ACP-PROMPT-003: `docs/protocol/v1/draft/initialization.mdx:247` overlaps hunk `-247,1 +264,1`; `#/$defs/PromptCapabilities`: `PromptCapabilities` changed
    - ACP-PROMPT-004: `#/$defs/ToolCallLocation/properties/path`: `ToolCallLocation` changed; `#/$defs/Diff/properties/path`: `Diff` changed
    - ACP-LOAD-001: `docs/protocol/v1/draft/session-setup.mdx:110-200` overlaps hunk `-139,9 +139,10`; `#/$defs/AgentCapabilities/properties/loadSession`: `AgentCapabilities` changed; `#/$defs/LoadSessionResponse`: `LoadSessionResponse` changed; `#/$defs/LoadSessionRequest`: `LoadSessionRequest` changed
    - ACP-LOAD-002: `docs/protocol/v1/draft/session-setup.mdx:136-142` overlaps hunk `-139,9 +139,10`
    - ACP-LOAD-003: `#/$defs/LoadSessionResponse`: `LoadSessionResponse` changed
    - ACP-RESUME-001: `#/$defs/ResumeSessionRequest`: `ResumeSessionRequest` changed; `#/$defs/ResumeSessionResponse`: `ResumeSessionResponse` changed
    - ACP-LIST-001: `#/$defs/ListSessionsRequest`: `ListSessionsRequest` changed; `#/$defs/ListSessionsResponse`: `ListSessionsResponse` changed; `#/$defs/SessionInfo`: `SessionInfo` changed
    - ACP-LIST-002: `#/$defs/ListSessionsRequest/properties/cwd`: `ListSessionsRequest` changed
    - ACP-DELETE-001: `#/$defs/DeleteSessionRequest`: `DeleteSessionRequest` changed; `#/$defs/DeleteSessionResponse`: `DeleteSessionResponse` changed
    - ACP-CLOSE-001: `#/$defs/CloseSessionRequest`: `CloseSessionRequest` changed; `#/$defs/CloseSessionResponse`: `CloseSessionResponse` changed
    - ACP-ADDDIRS-001: `docs/protocol/v1/draft/session-setup.mdx:351-380` overlaps hunk `-378,1 +381,1`; `#/$defs/NewSessionRequest/properties/additionalDirectories`: `NewSessionRequest` changed
    - ACP-SYSPROMPT-001: `#/$defs/SystemPrompt`: `SystemPrompt` changed; `#/$defs/SessionSystemPromptModeCapabilities`: `SessionSystemPromptModeCapabilities` changed
    - ACP-SYSPROMPT-002: `#/$defs/SystemPromptMode`: `SystemPromptMode` changed
    - ACP-SYSPROMPT-003: `#/$defs/SystemPrompt/properties/content`: `SystemPrompt` changed
    - ACP-MODES-001: `#/$defs/SessionModeState`: `SessionModeState` changed; `#/$defs/SessionMode`: `SessionMode` changed
    - ACP-MODES-002: `docs/protocol/v1/draft/session-modes.mdx:83-122` overlaps hunk `-83,1 +83,1`; `#/$defs/SetSessionModeRequest`: `SetSessionModeRequest` changed; `#/$defs/SetSessionModeResponse`: `SetSessionModeResponse` changed; `#/$defs/CurrentModeUpdate`: `CurrentModeUpdate` changed
    - ACP-CONFIG-001: `docs/protocol/v1/draft/session-config-options.mdx:118-127` overlaps hunk `-123,1 +123,4`, `-126,1 +129,1`; `docs/protocol/v1/draft/session-config-options.mdx:242` overlaps hunk `-242,1 +245,1`; `#/$defs/SessionConfigOption`: `SessionConfigOption` changed; `#/$defs/SessionConfigSelect`: `SessionConfigSelect` in $ref closure of `SessionConfigSelectGroup`, `SessionConfigSelectOption`
    - ACP-CONFIG-002: `docs/protocol/v1/draft/session-config-options.mdx:328-333` overlaps hunk `-329,4 +374,3`; `#/$defs/SetSessionConfigOptionRequest`: `SetSessionConfigOptionRequest` changed; `#/$defs/SetSessionConfigOptionResponse`: `SetSessionConfigOptionResponse` changed
    - ACP-CONFIG-003: `docs/protocol/v1/draft/initialization.mdx:172-181` overlaps hunk `-172,1 +172,18`; `#/$defs/SessionConfigOption/oneOf/1`: `SessionConfigOption` changed
    - ACP-PROMPTCAP-001: `docs/protocol/v1/draft/initialization.mdx:249-253` overlaps hunk `-252,1 +269,1`; `#/$defs/PromptCapabilities`: `PromptCapabilities` changed; `#/$defs/ImageContent`: `ImageContent` changed
    - ACP-PROMPTCAP-002: `docs/protocol/v1/draft/initialization.mdx:255-257` overlaps hunk `-256,1 +273,1`; `#/$defs/PromptCapabilities`: `PromptCapabilities` changed; `#/$defs/AudioContent`: `AudioContent` changed
    - ACP-PROMPTCAP-003: `docs/protocol/v1/draft/initialization.mdx:259-261` overlaps hunk `-260,1 +277,1`; `#/$defs/PromptCapabilities`: `PromptCapabilities` changed; `#/$defs/EmbeddedResource`: `EmbeddedResource` changed
    - ACP-AUTH-001: `#/$defs/AuthMethodAgent/properties/id`: `AuthMethodAgent` changed; `#/$defs/AuthMethodTerminal/properties/id`: `AuthMethodTerminal` changed
    - ACP-AUTH-002: `#/$defs/AuthMethodTerminal`: `AuthMethodTerminal` changed
    - ACP-AUTH-003: `docs/protocol/v1/draft/authentication.mdx:136-167` overlaps hunk `-153,1 +153,1`; `#/$defs/AuthenticateRequest`: `AuthenticateRequest` changed; `#/$defs/AuthenticateResponse`: `AuthenticateResponse` changed
    - ACP-AUTH-004: `docs/protocol/v1/draft/authentication.mdx:190-213` overlaps hunk `-190,1 +190,7`; `#/$defs/AgentAuthCapabilities`: `AgentAuthCapabilities` changed; `#/$defs/LogoutCapabilities`: `LogoutCapabilities` changed; `#/$defs/LogoutRequest`: `LogoutRequest` changed
    - ACP-AUTH-005: `#/$defs/InitializeResponse/properties/authMethods`: `InitializeResponse` changed
    - ACP-AUTH-006: `#/$defs/AuthMethod`: `AuthMethod` in $ref closure of `AuthMethodAgent`, `AuthMethodTerminal`; `#/$defs/AuthMethodTerminal`: `AuthMethodTerminal` changed
    - ACP-CLIENTCAP-001: `#/$defs/FileSystemCapabilities`: `FileSystemCapabilities` changed
    - ACP-CLIENTCAP-004: `#/$defs/Notice`: `Notice` changed
    - ACP-CLIENTCAP-005: `docs/protocol/v1/draft/session-setup.mdx:139-142` overlaps hunk `-139,9 +139,10`; `#/$defs/CompactionUpdate`: `CompactionUpdate` changed; `#/$defs/CompactionSummaryChunk`: `CompactionSummaryChunk` changed
    - ACP-CLIENTCAP-006: `docs/protocol/v1/draft/prompt-turn.mdx:25-26` overlaps hunk `-14,21 +14,21`; `#/$defs/PlanCapabilities`: `PlanCapabilities` changed
    - ACP-CLIENTCAP-007: `docs/protocol/v1/draft/prompt-turn.mdx:19-21` overlaps hunk `-14,21 +14,21`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
    - ACP-EXT-001: `docs/protocol/v1/draft/extensibility.mdx:47` overlaps hunk `-47,1 +47,1`; `docs/protocol/v1/draft/overview.mdx:10-12` overlaps hunk `-12,2 +12,2`
    - ACP-META-001: `docs/protocol/v1/draft/extensibility.mdx:10-14` overlaps hunk `-13,1 +13,1`; `#/$defs/PromptRequest/properties/_meta`: `PromptRequest` changed
    - ACP-ERROR-001: `#/$defs/Error/properties/message`: `Error` in $ref closure of `ErrorCode`
    - ACP-ERROR-002: `#/$defs/ErrorCode`: `ErrorCode` changed; `#/$defs/NewSessionRequest`: `NewSessionRequest` changed
    - ACP-SCHEMA-002: `docs/protocol/v1/draft/extensibility.mdx:10-14` overlaps hunk `-13,1 +13,1`; `#/$defs/Error`: `Error` in $ref closure of `ErrorCode`
    - ACP-INFO-UNKNOWNSESSION-001: `docs/protocol/v1/draft/error.mdx:6` overlaps hunk `-6,1 +6,63`
    
    ## Summary
    
    - Changed files: 52 (22 draft docs, 5 schema files, 25 RFDs); doc hunks: 370.
    - `$defs`: 28 added, 0 removed, 184 changed; closure: 12.
    - Links into changed docs: 456.
    - Affected entries: 50 requirements, 0 ledger entries.
    - Core hit: **yes, escalate** (`docs/protocol/v1/draft/transports.mdx`; `docs/protocol/v1/draft/overview.mdx`; `docs/protocol/v1/draft/extensibility.mdx`; `docs/protocol/v1/draft/initialization.mdx`; `docs/protocol/v1/draft/session-setup.mdx` > `(intro)`; `docs/protocol/v1/draft/session-setup.mdx` > `Working Directory`; `docs/protocol/v1/draft/prompt-turn.mdx` > `Session Updates`; `docs/protocol/v1/draft/prompt-turn.mdx` > `Stop Reasons`; `$defs/ErrorCode`; `$defs/SessionUpdate`; `$defs/ContentBlock`; `$defs/AgentCapabilities`; `$defs/ClientCapabilities`)
