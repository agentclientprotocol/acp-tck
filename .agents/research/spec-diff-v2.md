# ACP v2 (Draft) spec diff inventory: `beac4ba` -> `3961af9`

**Sources checked:** `agent-client-protocol` (spec checkout `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`, HEAD = `3961af94fa62d2386d993cadf1afc8b146fc799a`, not pulled per brief) diffed against base `beac4ba96190018e9f6d82e148ff275084c5aa3e` (v2 `SCHEMA_REVISION` pinned in `src/tck/v2/protocol.py:24`). 340 upstream commits in range (`git log --oneline base..target`). v2 schema version `2.0.0-alpha.9` -> `2.0.0-alpha.14` (`schema/v2/Cargo.toml`). Rust SDK / Python SDK / A2A TCK were not consulted (inventory only).
**Confidence:** high for what changed (git diff + `spec-impact` + a structural JSON diff of `schema/v2/schema.unstable.json` (ignoring string-valued `description`/`title` keywords)); not assessed here: what each change means for each requirement (next step).

## Answer

The v2 range is large and contains real wire changes, so a full v2 audit is warranted. The `spec-impact` run succeeded (exit 0, no `--fix`): 50 changed files (19 of 19 draft docs changed or added; none unchanged, none deleted; `security.mdx` is new), 47 `$defs` added, 2 removed, 112 of 125 registered v2 requirement ids touched, 0 ledger entries, and **a core hit on every core doc in the map**.

**Breaking / registry-breaking wire changes (details in "Breaking wire changes" below):**
1. **JSON-RPC batching removed from v2** (changelog alpha.11 #2625): the four `*BatchCall`/`*BatchResponse` root `anyOf` entries are gone; `transports.mdx` now says senders MUST NOT send arrays and receivers reject with a single `-32600`, `id: null`. Directly contradicts the whole `ACP-BATCH-2xx` family and `ACP-INFO-BATCH-*`.
2. **`$defs/ProtocolLevelNotification` removed** (cited by `ACP-EXT-203` at `src/tck/v2/requirements.py:1763`) and **`$defs/AuthCapabilities` removed / renamed `ClientAuthCapabilities`** (cited by `ACP-AUTH-202` at `requirements.py:1438`). Both citations become dangling JSON pointers, which `tests/v2/test_registry.py` checks.
3. **`RequestId` no longer allows `null`** (alpha.10 #2499); only error responses may carry `id: null` (alpha.11 #2634).
4. **`AvailableCommand` is now a tagged union**: `type: "command"` is required (alpha.10 #2494).
5. **Elicitation**: `requestedSchema` now requires `type` and `properties`; exactly one scope (`oneOf`); content values accept any JSON value.
6. **Tightened constraints**: `PromptRequest.prompt` `minItems: 1`; select options/groups `minItems: 1`; `ToolCallLocation.line` minimum 0 -> 1; `ResourceLink.size` now unsigned (uint64, min 0).
7. **Loosened**: `TerminalExitStatus.exitCode` int64 (was uint32, min 0); `Annotations.lastModified` lost `format: date-time`; `Cost.currency` lost its `^[A-Z]{3}$` pattern.
8. New behavioural rules in docs (not schema): initialization-phase gating (`-32600` for non-`initialize` requests before init completes; `initialize` may be repeated), `$/cancel_request` rules, prompt-insertion rules ("Prompts during active work"), foreground/background work model, an `error.mdx` page with an error-code table and typed error data.

**Additive / capability-gated (unstable)**: methods `auth/status`, `auth/status_update` (notification), `session/archive`, `session/unarchive`, `session/set_title`, `session/status`, `proxy/initialize`, `proxy/successor`, `tool_call/cancel`, `terminal/cancel` (31 x-method entries vs 21; **no method removed or renamed**); `ToolCallStatus` gains `paused`; `background` list on `running`/`requires_action`/`idle`/`unknown` state updates; `ToolCallContent` gains a `session` variant; client system prompt stabilized (doc/RFD status only, no unstable-schema structural change).

**Tool caveats the next step must know** (see "Tooling caveats"): the draft docs underwent a sentence-case heading pass, so the map's `sections` addresses no longer resolve at target and hunk-to-section attribution is noisy; ~1238 doc hunks are mostly plain-language rewraps, not rule changes.

## Requirements
Not applicable: this is a change inventory, not a requirements answer. Tiering and per-requirement semantics are the next step.

| # | Item | Tier | Citation |
|---|------|------|----------|
| - | n/a (inventory only) | n/a | n/a |

## Details

### 1. `spec-impact` output
Command run (no `--fix`), exit status 0, stderr empty:
`uv run --package spec-tracker spec-impact beac4ba96190018e9f6d82e148ff275084c5aa3e 3961af94fa62d2386d993cadf1afc8b146fc799a --version v2 --spec-repo /Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`

The full, unedited output (2210 lines) is reproduced in **Appendix A** at the end of this file. Headline numbers from its `## Summary`: 50 changed files (19 draft docs, 6 schema files, 25 RFDs), 1238 doc hunks, `$defs` 47 added / 2 removed / 181 changed (closure 5), 580 links into changed docs, 112 affected requirements, 0 ledger entries, core hit **yes, escalate**.

### 2. Changelog `schema/v2/CHANGELOG.md` (alpha.10 -> alpha.14)
Source: `schema/v2/CHANGELOG.md` at `3961af9` (lines 10-147 of the target file; the diff base..target adds exactly these 138 lines). Verbatim:

## [2.0.0-alpha.14](https://github.com/agentclientprotocol/agent-client-protocol/compare/schema-v2.0.0-alpha.13...schema-v2.0.0-alpha.14) - 2026-11-09

### Added

- *(schema)* stabilize client system prompt ([#2765](https://github.com/agentclientprotocol/agent-client-protocol/pull/2765))

## [2.0.0-alpha.13](https://github.com/agentclientprotocol/agent-client-protocol/compare/schema-v2.0.0-alpha.12...schema-v2.0.0-alpha.13) - 2026-11-02

### Other

- reconcile v1.15 spec text, unstable RFDs and the proxy-chains RFD ([#2743](https://github.com/agentclientprotocol/agent-client-protocol/pull/2743))

## [2.0.0-alpha.12](https://github.com/agentclientprotocol/agent-client-protocol/compare/schema-v2.0.0-alpha.11...schema-v2.0.0-alpha.12) - 2026-10-31

### Added

- *(unstable-v2)* add background work to v2 ([#2738](https://github.com/agentclientprotocol/agent-client-protocol/pull/2738))
- *(unstable)* add session/archive and session/unarchive methods ([#2736](https://github.com/agentclientprotocol/agent-client-protocol/pull/2736))
- *(unstable)* add proxy/initialize and proxy/successor ([#2737](https://github.com/agentclientprotocol/agent-client-protocol/pull/2737))
- *(unstable)* add session/status method ([#2735](https://github.com/agentclientprotocol/agent-client-protocol/pull/2735))
- *(unstable)* add auth/status method and auth/status_update notification ([#2732](https://github.com/agentclientprotocol/agent-client-protocol/pull/2732))
- *(unstable)* add session/set_title method ([#2734](https://github.com/agentclientprotocol/agent-client-protocol/pull/2734))

### Other

- *(rfd)* move client system prompt to preview ([#2739](https://github.com/agentclientprotocol/agent-client-protocol/pull/2739))
- *(schema)* plain-language pass over spec pages and schema descriptions ([#2730](https://github.com/agentclientprotocol/agent-client-protocol/pull/2730))

## [2.0.0-alpha.11](https://github.com/agentclientprotocol/agent-client-protocol/compare/schema-v2.0.0-alpha.10...schema-v2.0.0-alpha.11) - 2026-10-30

### Added

- *(unstable-v2)* remove JSON-RPC batching from v2 ([#2625](https://github.com/agentclientprotocol/agent-client-protocol/pull/2625))
- *(unstable-v2)* add schema types for defined error data ([#2605](https://github.com/agentclientprotocol/agent-client-protocol/pull/2605))
- *(unstable-v2)* accept other JSON values in elicitation content ([#2595](https://github.com/agentclientprotocol/agent-client-protocol/pull/2595))
- *(unstable)* report subagent working directories ([#2593](https://github.com/agentclientprotocol/agent-client-protocol/pull/2593))

### Fixed

- *(unstable-v2)* encode the at-least-one-value rule for select options ([#2662](https://github.com/agentclientprotocol/agent-client-protocol/pull/2662))
- *(unstable-v2)* match MCP's ISO 8601 lastModified ([#2661](https://github.com/agentclientprotocol/agent-client-protocol/pull/2661))
- *(unstable)* use AbsolutePath for subagent cwd and additionalDirectories ([#2660](https://github.com/agentclientprotocol/agent-client-protocol/pull/2660))
- *(unstable-v2)* require type and properties on elicitation requestedSchema ([#2645](https://github.com/agentclientprotocol/agent-client-protocol/pull/2645))
- *(unstable-v2)* allow null error response ids in the generated schema ([#2634](https://github.com/agentclientprotocol/agent-client-protocol/pull/2634))
- *(schema)* allow non-ISO currency units such as credits ([#2621](https://github.com/agentclientprotocol/agent-client-protocol/pull/2621))
- *(unstable-v2)* make usage_update cost a patch field ([#2617](https://github.com/agentclientprotocol/agent-client-protocol/pull/2617))
- *(schema)* mark SessionInfo.additionalDirectories as default-on-null ([#2571](https://github.com/agentclientprotocol/agent-client-protocol/pull/2571))

### Other

- *(schema)* adopt MCP's icon fetch rules ([#2728](https://github.com/agentclientprotocol/agent-client-protocol/pull/2728))
- *(schema)* reject duplicate stdio env names ([#2693](https://github.com/agentclientprotocol/agent-client-protocol/pull/2693))
- *(schema)* align max_turn_requests wording with the docs ([#2717](https://github.com/agentclientprotocol/agent-client-protocol/pull/2717))
- *(schema)* Clients ignore config options of unknown type ([#2712](https://github.com/agentclientprotocol/agent-client-protocol/pull/2712))
- *(schema)* auth methods trigger is a non-empty authMethods list ([#2710](https://github.com/agentclientprotocol/agent-client-protocol/pull/2710))
- *(schema)* initialize can be repeated before other requests ([#2711](https://github.com/agentclientprotocol/agent-client-protocol/pull/2711))
- *(schema)* an unknown plan type still replaces the plan ([#2703](https://github.com/agentclientprotocol/agent-client-protocol/pull/2703))
- *(schema)* resource links are readable by the receiver ([#2706](https://github.com/agentclientprotocol/agent-client-protocol/pull/2706))
- *(schema)* define annotation semantics ([#2704](https://github.com/agentclientprotocol/agent-client-protocol/pull/2704))
- *(schema)* _meta docs forbid assigning meaning to unrecognized keys ([#2701](https://github.com/agentclientprotocol/agent-client-protocol/pull/2701))
- *(schema)* document omission rules for setup-response configOptions ([#2696](https://github.com/agentclientprotocol/agent-client-protocol/pull/2696))
- *(schema)* MCP transport headers take precedence over Client headers ([#2694](https://github.com/agentclientprotocol/agent-client-protocol/pull/2694))
- *(schema)* cancel_request names a request its sender issued ([#2687](https://github.com/agentclientprotocol/agent-client-protocol/pull/2687))
- *(schema)* align the session/close schema doc with the spec ([#2682](https://github.com/agentclientprotocol/agent-client-protocol/pull/2682))
- *(schema)* an empty-string session/list cursor is valid ([#2673](https://github.com/agentclientprotocol/agent-client-protocol/pull/2673))
- *(schema)* ignore cancel_request for unknown or answered requests ([#2672](https://github.com/agentclientprotocol/agent-client-protocol/pull/2672))
- *(unstable)* clean up the SystemPrompt.mode description ([#2668](https://github.com/agentclientprotocol/agent-client-protocol/pull/2668))
- *(schema)* new entities start at protocol defaults, not Client defaults ([#2652](https://github.com/agentclientprotocol/agent-client-protocol/pull/2652))
- *(schema)* git_patch paths match changes, including on Windows ([#2650](https://github.com/agentclientprotocol/agent-client-protocol/pull/2650))
- *(schema)* align close's prompt rule and call pending prompts held ([#2648](https://github.com/agentclientprotocol/agent-client-protocol/pull/2648))
- *(schema)* Clients must not send an empty prompt ([#2647](https://github.com/agentclientprotocol/agent-client-protocol/pull/2647))
- *(schema)* require a boundary after a command name ([#2646](https://github.com/agentclientprotocol/agent-client-protocol/pull/2646))
- *(schema)* require session/resume cwd to match the session ([#2640](https://github.com/agentclientprotocol/agent-client-protocol/pull/2640))
- *(schema)* SessionInfo.additionalDirectories doesn't allow null ([#2638](https://github.com/agentclientprotocol/agent-client-protocol/pull/2638))
- *(schema)* allow a normal response after $/cancel_request ([#2636](https://github.com/agentclientprotocol/agent-client-protocol/pull/2636))
- *(unstable-v2)* scope end-turn Usage fields to the completed work ([#2630](https://github.com/agentclientprotocol/agent-client-protocol/pull/2630))
- *(schema)* define AbsolutePath syntax and reject relative cwd ([#2629](https://github.com/agentclientprotocol/agent-client-protocol/pull/2629))
- *(schema)* state request ID rules for a bidirectional connection ([#2622](https://github.com/agentclientprotocol/agent-client-protocol/pull/2622))
- *(schema)* drop the v1 exclusion note from the v2 refusal stop reason ([#2619](https://github.com/agentclientprotocol/agent-client-protocol/pull/2619))
- *(schema)* resume mcpServers is the complete Client-provided set ([#2614](https://github.com/agentclientprotocol/agent-client-protocol/pull/2614))
- *(schema)* require session/resume cwd to match the session ([#2612](https://github.com/agentclientprotocol/agent-client-protocol/pull/2612))
- *(schema)* define session/list cwd matching ([#2609](https://github.com/agentclientprotocol/agent-client-protocol/pull/2609))
- *(schema)* specify slash command names and invocation ([#2598](https://github.com/agentclientprotocol/agent-client-protocol/pull/2598))
- *(schema)* clarify authMethods obligations, terminal gating and auth/login errors ([#2589](https://github.com/agentclientprotocol/agent-client-protocol/pull/2589))
- *(schema)* define declining a permission request and unknown option IDs ([#2582](https://github.com/agentclientprotocol/agent-client-protocol/pull/2582))
- *(schema)* let cancelled cover stops the user chose through the Agent ([#2576](https://github.com/agentclientprotocol/agent-client-protocol/pull/2576))

## [2.0.0-alpha.10](https://github.com/agentclientprotocol/agent-client-protocol/compare/schema-v2.0.0-alpha.9...schema-v2.0.0-alpha.10) - 2026-10-27

### Added

- *(unstable-v2)* add optional terminal size to terminal_update ([#2550](https://github.com/agentclientprotocol/agent-client-protocol/pull/2550))
- *(unstable-v2)* make ResourceLink.size unsigned and define unknown tool kinds ([#2521](https://github.com/agentclientprotocol/agent-client-protocol/pull/2521))
- *(unstable-v2)* add _meta to DiffPatch, ToolCallPermissionSubject, Icon and the cancelled outcome ([#2517](https://github.com/agentclientprotocol/agent-client-protocol/pull/2517))
- *(unstable-v2)* disallow null request IDs ([#2499](https://github.com/agentclientprotocol/agent-client-protocol/pull/2499))
- *(unstable-v2)* add type discriminator to available commands ([#2494](https://github.com/agentclientprotocol/agent-client-protocol/pull/2494))
- *(unstable)* link session message views and keep identity off chunks ([#2465](https://github.com/agentclientprotocol/agent-client-protocol/pull/2465))
- *(unstable-v2)* define version mismatch errors ([#2412](https://github.com/agentclientprotocol/agent-client-protocol/pull/2412))

### Fixed

- *(unstable-v2)* parse nextCursor and listed session directories strictly ([#2567](https://github.com/agentclientprotocol/agent-client-protocol/pull/2567))
- *(unstable-v2)* don't clear replacement lists on a malformed value ([#2568](https://github.com/agentclientprotocol/agent-client-protocol/pull/2568))
- *(unstable-v2)* keep optional fields of unknown variants verbatim ([#2561](https://github.com/agentclientprotocol/agent-client-protocol/pull/2561))
- *(unstable-v2)* reject a non-object elicitation schema root type ([#2558](https://github.com/agentclientprotocol/agent-client-protocol/pull/2558))
- *(unstable)* null clears session_message participant IDs and message references ([#2555](https://github.com/agentclientprotocol/agent-client-protocol/pull/2555))
- *(unstable-v2)* make ToolCallLocation.line 1-based ([#2546](https://github.com/agentclientprotocol/agent-client-protocol/pull/2546))
- *(unstable-v2)* make terminal exitCode a signed integer ([#2545](https://github.com/agentclientprotocol/agent-client-protocol/pull/2545))
- *(schema)* require exactly one elicitation scope in v2 ([#2498](https://github.com/agentclientprotocol/agent-client-protocol/pull/2498))

### Other

- *(schema)* state null handling for every optional v2 field ([#2570](https://github.com/agentclientprotocol/agent-client-protocol/pull/2570))
- *(schema)* mark DefaultOnNull lists with an x-deserialize hint ([#2569](https://github.com/agentclientprotocol/agent-client-protocol/pull/2569))
- *(schema)* fix broken v2 doc anchors ([#2565](https://github.com/agentclientprotocol/agent-client-protocol/pull/2565))
- *(schema)* put the text-content Markdown rule on the content page ([#2562](https://github.com/agentclientprotocol/agent-client-protocol/pull/2562))
- *(schema)* use one description for every v2 _meta field ([#2560](https://github.com/agentclientprotocol/agent-client-protocol/pull/2560))
- *(schema)* define config option defaults via currentValue and state select invariants ([#2557](https://github.com/agentclientprotocol/agent-client-protocol/pull/2557))
- *(schema)* document the elicitation form-schema subset and unrenderable forms ([#2556](https://github.com/agentclientprotocol/agent-client-protocol/pull/2556))
- *(schema)* say permission tool_call subjects apply as tool_call_update upserts ([#2554](https://github.com/agentclientprotocol/agent-client-protocol/pull/2554))
- *(schema)* specify v2 diff baseline, path uniqueness and patch conflicts ([#2547](https://github.com/agentclientprotocol/agent-client-protocol/pull/2547))
- *(schema)* define tool call field defaults and null resets in v2 ([#2544](https://github.com/agentclientprotocol/agent-client-protocol/pull/2544))
- *(schema)* define switch_mode as changing the mode config option in v2 ([#2543](https://github.com/agentclientprotocol/agent-client-protocol/pull/2543))
- *(schema)* note that titled multi-select items omit type, as in MCP ([#2538](https://github.com/agentclientprotocol/agent-client-protocol/pull/2538))
- *(schema)* ExtNotification can be sent by either side ([#2534](https://github.com/agentclientprotocol/agent-client-protocol/pull/2534))
- *(schema)* include -32800's range in the reserved error codes ([#2531](https://github.com/agentclientprotocol/agent-client-protocol/pull/2531))
- *(schema)* write versioned doc links in source and drop the generator's link rewriting ([#2525](https://github.com/agentclientprotocol/agent-client-protocol/pull/2525))
- *(schema)* define which stop reason applies to v2 cancellations ([#2523](https://github.com/agentclientprotocol/agent-client-protocol/pull/2523))
- *(schema)* mark required v2 fields in the docs and rename ClientAuthCapabilities ([#2522](https://github.com/agentclientprotocol/agent-client-protocol/pull/2522))
- *(schema)* use wire names instead of Rust identifiers in schema descriptions ([#2520](https://github.com/agentclientprotocol/agent-client-protocol/pull/2520))
- *(schema)* define Client handling of unknown v2 session states and tool statuses ([#2510](https://github.com/agentclientprotocol/agent-client-protocol/pull/2510))
- *(schema)* define timeline placement for v2 entities ([#2509](https://github.com/agentclientprotocol/agent-client-protocol/pull/2509))
- *(schema)* define session/cancel as cancelling foreground work in v2 ([#2508](https://github.com/agentclientprotocol/agent-client-protocol/pull/2508))
- *(schema)* write the error pages for v1 and v2 ([#2504](https://github.com/agentclientprotocol/agent-client-protocol/pull/2504))
- *(schema)* define receiver behavior for unknown v2 variants ([#2500](https://github.com/agentclientprotocol/agent-client-protocol/pull/2500))
- *(schema)* define when session/set_config_option is available in v2 ([#2497](https://github.com/agentclientprotocol/agent-client-protocol/pull/2497))
- *(deps)* bump the minor group with 9 updates ([#2437](https://github.com/agentclientprotocol/agent-client-protocol/pull/2437))


### 3. RFD status changes (`docs/rfds/`, `docs/rfds/v2/`)
RFD files carry no status frontmatter; status is the sidebar group in `docs/docs.json` (Draft / Active / Preview / Completed). Group moves from `git diff base..target -- docs/docs.json` (`docs/docs.json:191-270` at target):

| RFD | Change | Evidence |
|-----|--------|----------|
| `rfds/client-system-prompt` | Draft -> Completed (stabilized; changelog alpha.12 "move client system prompt to preview", alpha.14 "stabilize client system prompt"). New announcement `docs/announcements/client-system-prompt-stabilized.mdx` ("moved to Completed", published Nov 6 2026). Registry ids touching it: `ACP-SYSPROMPT-201/202`. | `docs/docs.json` Completed list; announcement |
| `rfds/subagents` | Draft -> Active (+468/-45 lines of RFD text) | `docs/docs.json` Active list |
| `rfds/mcp-over-acp` | Draft -> Active (file itself unchanged in range) | `docs/docs.json` Active list |
| `rfds/diff-delete` | **Removed** (file deleted, dropped from Draft list) | `git diff --name-status` D |
| `rfds/session-status`, `rfds/session-set-title`, `rfds/session-archive` | **New**, Draft | A; Draft list |
| `rfds/v2/background-work` | **New**, Active (v2 group, last item) | A; v2 group |
| `rfds/streamable-http-websocket-transport` | still Active (+10/-6) | |
| `rfds/get-auth-state` (+174/-54), `rfds/proxy-chains` (+90/-24), `rfds/plan-operations` (+47/-9) | still Draft, content revised (auth/status; `proxy/initialize` + `proxy/successor`; plan ops) | |
| `rfds/elicitation`, `rfds/message-id`, `rfds/updates` | Completed/other, minor edits (3, 2, 53 lines) | |
| `rfds/v2/overview` (+30/-6), `prompt`, `message-updates`, `meta-patches`, `plan-variants`, `diff-file-states`, `enum-variant-extension`, `required-session-methods`, `session-resume-replay`, `terminal-output`, `tool-call-updates` | still Active; text edits. `v2/overview` now lists the v2 breaking changes explicitly, incl. "Do not use JSON-RPC 2.0 batches ... receivers reject an array with `-32600`" and "Reject `initialize` with `-32022` ..." | `docs/rfds/v2/overview.mdx` diff |

Unchanged-set: the Preview group is empty at target (`"group": "Preview", "pages": []`).
RFD content is a design proposal, not a requirement; cite the draft docs/schema for requirements. Note `docs/rfds/v2/*.mdx` and `docs/rfds/session-fork.mdx` are cited by some v2 requirements (e.g. `ACP-INFO-CONCURRENT-201` -> `docs/rfds/v2/prompt.mdx:88`, `ACP-FORK-202` -> `docs/rfds/session-fork.mdx:67`).

### 4. One-line summary per changed area

Legend: **core** = doc/def listed in `spec-tracker/maps/v2.toml`. Ids come from the `spec-impact` section 6 (line/$def overlap) plus citation lookup against `src/tck/v2/requirements.py`.

**Docs (`docs/protocol/v2/draft/`)**

| Doc | Core? | What changed (one line) | Registry ids touched |
|-----|-------|-------------------------|----------------------|
| `prompt-lifecycle.mdx` (+203/-132) | **core (sections)** | New "Background work" section and `background` list on state updates; "Prompts during active work"/"Prompts that are never inserted"/"Insertion and ordering" subsections (Clients MAY send `session/prompt` in any state; held prompts); "Message IDs" subsection; foreground/background rewrite; stop-reason, cancellation and session-state text edited; "Cancellation" section shortened (-1131,4 +1205,0). Heading case changed (Sentence case). | PROMPT-201/203/205/207/208, STATE-201/203/204/205 (STATE-202 unflagged), CANCEL-201/203/204/207/209, INFO-CANCEL-201, INFO-CONCURRENT-201, RESUME-202/204, CLOSE-202/204, PATCH-201/203 |
| `extensibility.mdx` (+59/-45) | **core (whole doc)** | Rewording of capability-required rules, `_meta` rules ("forbid assigning meaning to unrecognized keys", alpha.11 #2701), patches, extension methods, open enum variants (+6 lines at "Enum and Tagged-Union Variants"), custom-capabilities text trimmed | CLIENTCAP-202, JSONRPC-004/005, AUTH-206, ENUM-201/203, EXT-001/201/202/203(removed def)/(204 unflagged), META-001/201, STATE-203, SCHEMA-002 |
| `initialization.mdx` (+102/-34) | **core (whole doc)** | New "Before initialization completes" rules; "Repeating initialization"; version negotiation text (`protocolVersion` read first, `-32602` for malformed); `authMethods` obligations (non-empty -> must implement `auth/login` + `auth/logout`); capabilities text reflowed; new `auth.status`, `session.archive`, `session.fork`, `session.status` capability entries; "Agents that advertise config options MUST also support `session/set_config_option`" | INIT-001/003/201-207 (INIT-208 unflagged), SCHEMA-001, PROMPT-206, PROMPTCAP-001/002/003, SYSPROMPT-202, EXT-204 (unflagged) |
| `session-setup.mdx` (+124/-70) | **core (sections)** | New "Session lifecycle" ("active" session definition), initial-state guidance (`configOptions`/`availableCommands` in setup responses; MUST NOT send `null`), "Replay contents", "Current-state synchronization" restructure, close/cancel text, workspace roots, MCP section edits. Heading case changed. | SESSION-001/002/203, RESUME-201..209, CLOSE-201/202/204 (203 unflagged), ADDDIRS-201/202, SYSPROMPT-201/202, MCP-201/202, CONFIG-203, CANCEL-208 |
| `overview.mdx` (+81/-27) | **core (sections)** | Adds "Message flow", "Optional methods" lists, "Request cancellation", "Error handling", "Conventions" text; request IDs MUST be string or integer, never null; no ID reuse while pending; absolute-path rule restated; `authMethods`/`auth/*` baseline rule | JSONRPC-001/002/003/005, LIST-204, CANCEL-205, EXT-001, ERROR-001 |
| `transports.mdx` (+22/-56) | **core (whole doc)** | **Batch section replaced by "No batches"** (MUST NOT send arrays; reject `-32600`, `id: null`); new "Shutdown" (stdin close ends connection), "Message timing", "Message order", expanded "Custom transports" | BATCH-201..208, INFO-BATCH-201/202, JSONRPC-001/002/003, TRANSPORT-201 (TRANSPORT-002/203, SHUTDOWN-001, STDERR-001 unflagged), CANCEL-205 |
| `error.mdx` (+64/-2) | no | Was a 2-line stub; now the Errors page: error object shape, error-code table, typed `data` (`-32002` session-not-found data, `-32022` version data), "Requests before initialization" | INFO-UNKNOWNSESSION-001, INFO-PARSE-001, INFO-INVALIDREQ-001 (cite whole doc) |
| `cancellation.mdx` (+26/-18) | no | `$/cancel_request` rewrite: receiver MUST still send a response; MUST ignore unknown/answered IDs; session/cancel permission-request handling; "Internal cancellation" | PROMPT-207, CANCEL-201/203/209, INFO-CANCEL-201/202 |
| `tool-calls.mdx` (+230/-59) | no | `paused` status and background work/capabilities (`tool_call/cancel`, `terminal/cancel`), permission request `subject`/options text and `cancelled` outcome semantics, tool-kind rules (custom kinds MUST start `_`), terminal size, streaming-content section | PERM-201, PATCH-206/207/208/209, ENUM-201 |
| `schema.mdx` (+3495/-1431; generated) | no | Regenerated from schema: new method sections (`auth/status`, `session/archive`, `session/set_title`, `session/status`, proxy, `tool_call/cancel`, `terminal/cancel`) and updated descriptions | PROMPT-205, CANCEL-201/202/204, FORK-201/202, AUTH-205 |
| `session-config-options.mdx` (+115/-38) | no | "Setting a config option" (client/agent) rewrites, ConfigOption/select text edits; changelog alpha.10/11 mention `currentValue` defaults and the select at-least-one-value rule (doc text not re-read) | CONFIG-201/202/204/206 |
| `session-list.mdx` (+70/-24) | no | New "Archived sessions (unstable)" section (`archived` filter, `session.archive` capability); cursor rules (empty-string cursor valid; `-32602` for invalid cursor); metadata updates | LIST-201/203/204 (202 unflagged), RESUME-202 |
| `session-delete.mdx` (+6/-5) | no | "Semantics": clients SHOULD treat `-32002` on delete as success; delete of active session acts like close | DELETE-201/202 (203 unflagged) |
| `authentication.mdx` (+28/-22) | no | `authMethods` obligations, terminal "Launch safety" subsection, `ClientAuthCapabilities` rename, logout/active-session text | AUTH-202/204/206/207 |
| `elicitation.mdx` (+53/-23) | no | Support-check rewording, scope exactly-one, form-schema subset, "Session cancellation", URL security | CLIENTCAP-201 |
| `agent-plan.mdx` (+23/-17) | no | Plan operation sections reworded; "Removing plans" added (unstable) | PATCH-205, ENUM-201 |
| `content.mdx` (+26/-18) | no | Text Markdown rule moved onto the content page; annotation semantics; resource-link readability | none cite it |
| `slash-commands.mdx` (+23/-10) | no | Command names/invocation specified ("boundary after a command name"); `type: "command"` discriminator | none cite it |
| `security.mdx` (**new**, 81 lines) | no (not in map) | New security guidance page (trust model, rendering, URIs, credentials, prompt injection, intermediaries, transports) | none |

**Schema (`schema/v2/schema.unstable.json`, vendored by the TCK) `$defs` groups** (from a structural JSON diff ignoring `description`/`title`; full output in Appendix B):

| Group | Change | Core `$def`? | Ids |
|-------|--------|--------------|-----|
| Root `anyOf` | 7 -> 4 entries: batch call/response arrays removed (**breaking**); `ProtocolLevel` is now a top-level object; new `Proxy` side | root | BATCH-20x, INFO-BATCH-202, TRANSPORT-201, JSONRPC-001/002 |
| `RequestId`, `AgentResponse`/`ClientResponse` error-id | `RequestId` loses `null`; error-response `id` is now `integer|string|null` inline (**breaking**) | | JSONRPC-*, ERROR-001 |
| `ProtocolLevelNotification` (removed), `AuthCapabilities` (removed, now `ClientAuthCapabilities`) | dangling citations | | EXT-203, AUTH-202 |
| Error types | `Error.data` -> `ErrorData`; added `ErrorData`, `SessionNotFoundErrorData`, `UnsupportedProtocolVersionErrorData`; `ErrorCode` only description changed (still includes `-32022`) | `ErrorCode` (description only) | INIT-205, ERROR-001 |
| Capabilities | added `ClientAuthCapabilities`, `AuthStatusCapabilities`, `SessionArchiveCapabilities`, `SessionStatusCapabilities`, `SessionTitleCapabilities`, `TerminalCapabilities`, `TerminalCancelCapabilities`, `ToolCallCapabilities`, `ToolCallCancelCapabilities`; `AgentCapabilities`/`SessionCapabilities` gain `archive`, `status`, `title` (`SessionCapabilities`); `AgentAuthCapabilities` gains `status` | `AgentCapabilities`, `ClientCapabilities` | INIT-204, AUTH-202/203, FORK-201 |
| Session updates / state | `background` (array of `BackgroundWork`) on `running`/`requires_action`/`idle`/`unknown`; `ToolCallStatus` + `paused`; `ToolCallContent` + `session`; `TerminalUpdate` + `size`/`capabilities`; `ToolCallUpdate` + `capabilities`; `RequestPermissionOutcome.cancelled` now `CancelledPermissionOutcome` (`_meta`); `SessionMessage` + `senderMessageId`/`recipientMessageId`, `SessionMessageChunk` loses sender/recipient session IDs; `SubagentUpdate` + `cwd`/`additionalDirectories`; added `BackgroundWork`, `BackgroundSubagent/Terminal/ToolCall`, `SessionReference`, `TerminalSize` | `SessionUpdate` (via closure), `ContentBlock` (description only) | STATE-201/203/204/205, PATCH-201/204/205, ENUM-203, CANCEL-207/209, PROMPT-205/203 |
| Content | `ResourceLink.size` uint64 min 0; `Annotations.lastModified` no `date-time` format; `AvailableCommand` -> tagged union with `type: "command"` (`Command` def added) (**breaking**) | `ContentBlock` (descr.) | PROMPT-206, PROMPTCAP-001/002/003 |
| Prompt / elicitation | `PromptRequest.prompt` `minItems: 1`; `ElicitationSchema` requires `type`,`properties`; elicitation mode scope `oneOf`; `ElicitationContentValue` accepts any value | | PROMPT-206, CLIENTCAP-201 |
| Session setup/list | `ListSessionsRequest.archived`, `SessionInfo.archived`; `default-on-null` hints on `mcpServers`/`additionalDirectories`/`args`/`env`/`headers`; select `minItems: 1`; `ToolCallLocation.line` min 1; `TerminalExitStatus.exitCode` int64; `Cost.currency` pattern dropped | | SESSION-203, RESUME-20x, LIST-201/203, ADDDIRS-20x, MCP-201/202, CONFIG-201/202/204/206 |
| New methods (all additive, gated) | `auth/status`, `auth/status_update`, `session/archive`, `session/unarchive`, `session/set_title`, `session/status`, `proxy/initialize`, `proxy/successor`, `tool_call/cancel`, `terminal/cancel` | | none registered |
| Unflagged by structural diff (description-only edits) | 181 `$defs` show a diff in `spec-impact`, but only 53 differ structurally; the other ~128 are description edits (alpha.10-12 plain-language/wire-name passes) | | |

### 5. Breaking wire changes (prominent list)

Checked in a structural diff of `schema/v2/schema.unstable.json` (base `beac4ba` vs target `3961af9`), plus the changelog.

| # | Change | Kind | Where (target) |
|---|--------|------|----------------|
| B1 | JSON-RPC batching removed; arrays rejected with `-32600`, `id: null` | removed feature / behavior reversal | `docs/protocol/v2/draft/transports.mdx:65-67`; root `anyOf` entries 2-5 removed; changelog alpha.11 #2625; `docs/rfds/v2/overview.mdx` |
| B2 | `$defs/ProtocolLevelNotification` removed | removed `$def` | `schema/v2/schema.unstable.json` (no such `$def`); cited by `ACP-EXT-203` |
| B3 | `$defs/AuthCapabilities` removed, replaced by `ClientAuthCapabilities` (`ClientCapabilities.auth.$ref` repointed) | renamed `$def` (wire shape of the object unchanged as far as this diff shows) | changelog alpha.10 #2522; cited by `ACP-AUTH-202` |
| B4 | `RequestId` drops `null`; error-response `id` allows `null` inline | changed type | changelog alpha.10 #2499, alpha.11 #2634; `overview.mdx` "request IDs MUST be a string or an integer, never `null`" |
| B5 | `AvailableCommand` requires `type` (`"command"`); unknown variants require `type`,`name`,`description` | changed required-ness / tagged union | `schema.unstable.json#/$defs/AvailableCommand`; changelog alpha.10 #2494 |
| B6 | `ElicitationSchema` now requires `type` and `properties`; scope is `oneOf` (exactly one of session/request) | changed required-ness | changelog alpha.10 #2498, alpha.11 #2645 |
| B7 | `PromptRequest.prompt` `minItems: 1`; select option lists and groups `minItems: 1` | tightened | `#/$defs/PromptRequest/properties/prompt`; changelog alpha.11 #2647, #2662 |
| B8 | `ToolCallLocation.line` minimum 0 -> 1 (1-based); `ResourceLink.size` int64 -> uint64 min 0 | tightened | changelog alpha.10 #2546, #2521 |
| B9 | `TerminalExitStatus.exitCode` uint32/min 0 -> int64; `Annotations.lastModified` `date-time` format removed; `Cost.currency` pattern removed; `ElicitationContentValue` accepts any JSON | loosened | changelog alpha.10 #2545, alpha.11 #2661, #2621, #2595 |
| B10 | `SessionMessageChunk` loses `senderSessionId`/`recipientSessionId`; `SessionInfo.additionalDirectories` no longer allows null (alpha.11 #2638) | removed fields (unstable, session-messaging) | changelog alpha.10 #2465 |
| B11 | `AuthMethod` unknown ("other") variant loses declared `_meta` and `description` properties; `ReplayFrom` unknown variant loses `_meta` | property removed from schema (additionalProperties still true) | `#/$defs/AuthMethod/anyOf/2` (note: `description` was an optional string on that variant; the known `agent`/`terminal` variants are unaffected per the diff), `#/$defs/ReplayFrom/anyOf/1` |
| B12 | `ToolCallStatus` gains `paused` (open enum, so additive); `RequestPermissionOutcome.cancelled` extracted to `CancelledPermissionOutcome` | additive/refactor | `#/$defs/ToolCallStatus` |

**No method was renamed or removed.** Ten methods/notifications were added (see above). No `required` array changes beyond B5, B6.

Behavioral (non-schema) rule changes to watch, not exhaustive: initialization gating and repeated `initialize` (`initialization.mdx` "Before initialization completes", "Repeating initialization"); `$/cancel_request` (`cancellation.mdx`); prompt insertion ("Prompts during active work": Clients MAY send `session/prompt` in any state; `prompt-lifecycle.mdx`); foreground/background work; session "active" definition (`session-setup.mdx` "Session lifecycle"); `-32002` on delete; the Shutdown section (`transports.mdx`).

### 6. Docs under `docs/protocol/v2/draft/` at target (audit scope)

All 19 docs below are in the draft tree at target (`git ls-tree 3961af9 docs/protocol/v2/draft/`). **All 19 were modified or added in the range; none unchanged; none deleted; 1 new (`security.mdx`).** Lines = line count at target; +/- = `git diff --numstat base target`. "Core" = listed in `spec-tracker/maps/v2.toml`. Citing ids are those whose `citation` mentions the doc (regenerated programmatically from `src/tck/v2/requirements.py` `REGISTRY`, so the count includes ids whose cited lines the tool considered unaffected).

| doc | status | lines | +/- | core in map | citing ids (count) |
|---|---|---|---|---|---|
| `agent-plan.mdx` | modified | 190 | +23/-17 | no | 2: ACP-PATCH-205, ACP-ENUM-201 |
| `authentication.mdx` | modified | 281 | +28/-22 | no | 4: ACP-AUTH-202, ACP-AUTH-204, ACP-AUTH-206, ACP-AUTH-207 |
| `cancellation.mdx` | modified | 91 | +26/-18 | no | 6: ACP-PROMPT-207, ACP-CANCEL-201, ACP-CANCEL-203, ACP-CANCEL-209, ACP-INFO-CANCEL-201, ACP-INFO-CANCEL-202 |
| `content.mdx` | modified | 229 | +26/-18 | no | 0: - |
| `elicitation.mdx` | modified | 271 | +53/-23 | no | 1: ACP-CLIENTCAP-201 |
| `error.mdx` | modified | 68 | +64/-2 | no | 3: ACP-INFO-UNKNOWNSESSION-001, ACP-INFO-PARSE-001, ACP-INFO-INVALIDREQ-001 |
| `extensibility.mdx` | modified | 286 | +59/-45 | yes | 13: ACP-STATE-203, ACP-CLIENTCAP-202, ACP-JSONRPC-004, ACP-JSONRPC-005, ACP-AUTH-206, ACP-ENUM-201, ACP-ENUM-203, ACP-EXT-001, ACP-META-001, ACP-EXT-201, ACP-EXT-202, ACP-EXT-204, ACP-SCHEMA-002 |
| `initialization.mdx` | modified | 380 | +102/-34 | yes | 16: ACP-INIT-001, ACP-INIT-201, ACP-INIT-003, ACP-INIT-202, ACP-INIT-205, ACP-INIT-206, ACP-INIT-207, ACP-INIT-208, ACP-INIT-203, ACP-SCHEMA-001, ACP-PROMPT-206, ACP-PROMPTCAP-001, ACP-PROMPTCAP-002, ACP-PROMPTCAP-003, ACP-SYSPROMPT-202, ACP-EXT-204 |
| `overview.mdx` | modified | 275 | +81/-27 | yes | 8: ACP-CANCEL-205, ACP-JSONRPC-001, ACP-JSONRPC-002, ACP-JSONRPC-003, ACP-JSONRPC-005, ACP-LIST-204, ACP-EXT-001, ACP-ERROR-001 |
| `prompt-lifecycle.mdx` | modified | 1205 | +203/-132 | yes | 26: ACP-PROMPT-201, ACP-PROMPT-203, ACP-STATE-201, ACP-STATE-202, ACP-STATE-203, ACP-STATE-204, ACP-STATE-205, ACP-PROMPT-207, ACP-PROMPT-208, ACP-INFO-CONCURRENT-201, ACP-CANCEL-201, ACP-CANCEL-202, ACP-CANCEL-203, ACP-CANCEL-204, ACP-CANCEL-206, ACP-CANCEL-207, ACP-CANCEL-209, ACP-INFO-CANCEL-201, ACP-RESUME-202, ACP-RESUME-204, ACP-RESUME-206, ACP-CLOSE-202, ACP-CLOSE-204, ACP-PATCH-201, ACP-PATCH-203, ACP-PATCH-209 |
| `schema.mdx` | modified | 11414 | +3495/-1431 | no | 7: ACP-PROMPT-205, ACP-CANCEL-201, ACP-CANCEL-202, ACP-CANCEL-204, ACP-FORK-201, ACP-FORK-202, ACP-AUTH-205 |
| `security.mdx` | added | 81 | +81/-0 | no | 0: - |
| `session-config-options.mdx` | modified | 463 | +115/-38 | no | 4: ACP-CONFIG-201, ACP-CONFIG-202, ACP-CONFIG-204, ACP-CONFIG-206 |
| `session-delete.mdx` | modified | 95 | +6/-5 | no | 3: ACP-DELETE-201, ACP-DELETE-202, ACP-DELETE-203 |
| `session-list.mdx` | modified | 252 | +70/-24 | no | 5: ACP-RESUME-202, ACP-LIST-201, ACP-LIST-202, ACP-LIST-203, ACP-LIST-204 |
| `session-setup.mdx` | modified | 697 | +124/-70 | yes | 23: ACP-SESSION-001, ACP-SESSION-002, ACP-CANCEL-208, ACP-RESUME-201, ACP-RESUME-202, ACP-RESUME-203, ACP-RESUME-204, ACP-RESUME-205, ACP-RESUME-206, ACP-RESUME-207, ACP-RESUME-208, ACP-RESUME-209, ACP-CLOSE-201, ACP-CLOSE-202, ACP-CLOSE-203, ACP-CLOSE-204, ACP-ADDDIRS-201, ACP-ADDDIRS-202, ACP-SYSPROMPT-201, ACP-SYSPROMPT-202, ACP-MCP-201, ACP-MCP-202, ACP-CONFIG-203 |
| `slash-commands.mdx` | modified | 162 | +23/-10 | no | 0: - |
| `tool-calls.mdx` | modified | 774 | +230/-59 | no | 6: ACP-PERM-201, ACP-PATCH-206, ACP-PATCH-207, ACP-PATCH-208, ACP-PATCH-209, ACP-ENUM-201 |
| `transports.mdx` | modified | 73 | +22/-56 | yes | 17: ACP-CANCEL-205, ACP-TRANSPORT-201, ACP-TRANSPORT-002, ACP-TRANSPORT-203, ACP-JSONRPC-001, ACP-JSONRPC-003, ACP-BATCH-201, ACP-BATCH-202, ACP-BATCH-203, ACP-BATCH-204, ACP-BATCH-205, ACP-BATCH-206, ACP-BATCH-207, ACP-BATCH-208, ACP-INFO-BATCH-201, ACP-SHUTDOWN-001, ACP-STDERR-001 |

New docs: `security.mdx` (+81; not in the map, cited by no id). Deleted docs: none. Non-draft side effects worth knowing: `docs/docs.json` now lists `protocol/v2/security` and `protocol/v2/error` in both the stable and draft v2 groups (and the same for v1). `docs/protocol/v2/migration.mdx` exists in the stable v2 tree (not under `draft/`, not diffed here; the v2 RFD overview now points to it as the home for smaller v2 breaking changes).
Heavy docs for the audit: `schema.mdx` (11414 lines, generated; audit via the schema instead), `prompt-lifecycle.mdx` (1205), `tool-calls.mdx` (774), `session-setup.mdx` (697), `session-config-options.mdx` (463).
Registry ids that cite none of the docs above (cite schema/RFD only) are not listed here.

### 7. Tooling caveats (read before trusting Appendix A)

1. **Map sections no longer resolve at target.** The draft docs now use sentence-case headings (e.g. `Session Updates` -> `Session updates`, `Prompt Lifecycle` -> `Prompt lifecycle`, `Creating a Session` -> `Creating a session`, `Resuming Sessions`, `Closing Active Sessions`, `Working Directory`, `Agent > Baseline Methods` -> `Baseline methods`, `Error Handling` -> `Error handling`). `spec-impact` section 3 prints `note:` lines for each unmatched `sections` address in `spec-tracker/maps/v2.toml` (prompt-lifecycle, session-setup, overview). `Session Updates > (intro)`, `Foreground and Background Work`, etc. all need re-casing in `maps/v2.toml`. Hunk-to-section attribution for the base side uses old casing, target side new casing, so the same section appears twice in Appendix A. The sentence-case pass is why so many hunks are single-line.
2. **New prompt-lifecycle subsections not classified in the map**: `Background work`, `Insertion and ordering`, `Prompts during active work`, `Prompts that are never inserted`, `Message IDs`. The map's comment says "everything except standalone feature subsections", so someone must decide whether each is core. `security.mdx` is likewise unclassified.
3. **13 ids are listed as unaffected only because no hunk overlaps their cited base line numbers**, not because their docs are stable: `ACP-INIT-208, ACP-STATE-202, ACP-CANCEL-202, ACP-TRANSPORT-002, ACP-TRANSPORT-203, ACP-LIST-202, ACP-CLOSE-203, ACP-DELETE-203, ACP-FORK-202, ACP-PATCH-209, ACP-EXT-204, ACP-SHUTDOWN-001, ACP-STDERR-001`. Their cited docs all changed and line numbers have shifted (every doc has hunks above those lines), so they still need `--fix` remapping and a re-read. `ACP-FORK-202` cites `schema.mdx:622-624` (generated doc, +3495 lines).
4. **`--fix` was not run.** `spec-impact --fix` refuses unless base is the pinned `SCHEMA_REVISION` (it is `beac4ba…`), so it is runnable before the pin bump.
5. `$defs` "changed: 181" overstates: only 53 differ after ignoring descriptions/titles (Appendix B).
6. The stable `schema/v2/schema.json` also changed (+1099/-748) and `meta.json`/`meta.unstable.json` changed; the TCK vendors the `*.unstable.json` pair only. The stable schema change is dominated by client-system-prompt stabilization and the same description passes (hypothesis; not diffed structurally).

## Testability notes
Out of scope for this inventory. Observation for the next step: the removal of batching (B1) inverts what a conforming agent does (previously it had to answer a batch; now it must reject an array with one `-32600`/`id: null` response), so `src/tck/v2/conformance/test_batch.py` and fixtures such as `tests/fixtures/agents/v2/crashes_on_batch.py`/`emits_batch_updates.py` are directly in the blast radius.

## Discrepancies
None found at inventory level (docs, schema and changelog agree on batching removal, `RequestId` change, `paused`, new methods). Not examined: SDK behavior (Rust/Python SDKs were not checked). One inconsistency to note: the map/registry citation style (line numbers into `.mdx`) is invalidated by the heading and content reflow; use `--fix` before the pin bump.

## Open questions
- Which of the new prompt-lifecycle subsections and `security.mdx` should be added to `spec-tracker/maps/v2.toml` as core? (Orchestrator/maintainer decision.)
- Do the Rust/Python SDKs already implement batch rejection (`-32600`, `id: null`), initialization gating and `$/cancel_request` semantics? (Route to a researcher with `check-rust-sdk`/`check-python-sdk`.)
- For each of B1-B12 and the behavioral rule changes: which registered ids are invalidated, re-tiered, or need new ids? (Next step: v2 audit.)
- Are `proxy/*`, `session/status`, `session/archive`, `session/set_title`, `auth/status`, `tool_call/cancel`, `terminal/cancel` worth capability-gated TCK coverage, or out of scope (all unstable/Draft RFDs)?

---

## Appendix B. Structural diff of `schema/v2/schema.unstable.json` (description/title ignored)

Generated with a throwaway script (JSON walk of base vs target). Added `$defs` (47) and removed (2) are listed in Appendix A section 4. `ADD`/`DEL`/`CHG` paths are within the `$def`; JSON truncated to 300 chars.

~~~text
top keys base/target ['$schema', 'title', 'anyOf', '$defs'] ['$schema', 'title', 'anyOf', '$defs']
root(non-defs) diffs:
CHG /anyOf: [{"type": "object", "properties": {"jsonrpc": {"type": "string", "enum": ["2.0"]}}, "required": ["jsonrpc"], "anyOf": [{"allOf": [{"$ref": "#/$defs/AgentRequest"}]}, {"allOf": [{"$ref": "#/$defs/AgentResponse"}]}, {"allOf": [{"$ref": "#/$defs/AgentNotification"}]}]}, {"type": "object", "properties":  ->  [{"type": "object", "properties": {"jsonrpc": {"type": "string", "enum": ["2.0"]}}, "required": ["jsonrpc"], "anyOf": [{"allOf": [{"$ref": "#/$defs/AgentRequest"}]}, {"allOf": [{"$ref": "#/$defs/AgentResponse"}]}, {"allOf": [{"$ref": "#/$defs/AgentNotification"}]}]}, {"type": "object", "properties":

ADDED ['ArchiveSessionRequest', 'ArchiveSessionResponse', 'AuthAccount', 'AuthState', 'AuthStatusCapabilities', 'AuthStatusRequest', 'AuthStatusResponse', 'AuthStatusUpdateNotification', 'BackgroundSubagent', 'BackgroundTerminal', 'BackgroundToolCall', 'BackgroundWork', 'CancelTerminalRequest', 'CancelTerminalResponse', 'CancelToolCallRequest', 'CancelToolCallResponse', 'CancelledPermissionOutcome', 'ClientAuthCapabilities', 'Command', 'ErrorData', 'InitializeProxyRequest', 'InitializeProxyResponse', 'ProxyNotification', 'ProxyRequest', 'ProxyResponse', 'ProxySuccessorNotification', 'ProxySuccessorRequest', 'ProxySuccessorResponse', 'SessionArchiveCapabilities', 'SessionArchiveFilter', 'SessionNotFoundErrorData', 'SessionReference', 'SessionStatus', 'SessionStatusCapabilities', 'SessionStatusRequest', 'SessionStatusResponse', 'SessionTitleCapabilities', 'SetSessionTitleRequest', 'SetSessionTitleResponse', 'TerminalCancelCapabilities', 'TerminalCapabilities', 'TerminalSize', 'ToolCallCancelCapabilities', 'ToolCallCapabilities', 'UnarchiveSessionRequest', 'UnarchiveSessionResponse', 'UnsupportedProtocolVersionErrorData']
REMOVED ['AuthCapabilities', 'ProtocolLevelNotification']

### AgentAuthCapabilities
   ADD /properties/status: {"anyOf": [{"$ref": "#/$defs/AuthStatusCapabilities"}, {"type": "null"}], "x-deserialize-default-on-error": true}

### AgentNotification
   CHG /properties/params/anyOf/0/anyOf: [{"allOf": [{"$ref": "#/$defs/UpdateSessionNotification"}]}, {"allOf": [{"$ref": "#/$defs/CompleteElicitationNotification"}]}, {"allOf": [{"$ref": "#/$defs/ExtNotification"}]}]  ->  [{"allOf": [{"$ref": "#/$defs/UpdateSessionNotification"}]}, {"allOf": [{"$ref": "#/$defs/CompleteElicitationNotification"}]}, {"allOf": [{"$ref": "#/$defs/AuthStatusUpdateNotification"}]}, {"allOf": [{"$ref": "#/$defs/ExtNotification"}]}]

### AgentResponse
   CHG /anyOf/0/properties/result/anyOf: [{"allOf": [{"$ref": "#/$defs/InitializeResponse"}]}, {"allOf": [{"$ref": "#/$defs/LoginAuthResponse"}]}, {"allOf": [{"$ref": "#/$defs/ListProvidersResponse"}]}, {"allOf": [{"$ref": "#/$defs/SetProviderResponse"}]}, {"allOf": [{"$ref": "#/$defs/DisableProviderResponse"}]}, {"allOf": [{"$ref": "#/$de  ->  [{"allOf": [{"$ref": "#/$defs/InitializeResponse"}]}, {"allOf": [{"$ref": "#/$defs/LoginAuthResponse"}]}, {"allOf": [{"$ref": "#/$defs/ListProvidersResponse"}]}, {"allOf": [{"$ref": "#/$defs/SetProviderResponse"}]}, {"allOf": [{"$ref": "#/$defs/DisableProviderResponse"}]}, {"allOf": [{"$ref": "#/$de
   DEL /anyOf/1/properties/id/allOf: [{"$ref": "#/$defs/RequestId"}]
   ADD /anyOf/1/properties/id/anyOf: [{"type": "integer", "format": "int64"}, {"type": "string"}, {"type": "null"}]

### Annotations
   DEL /properties/lastModified/format: "date-time"

### AuthMethod
   DEL /anyOf/2/properties/_meta: {"type": ["object", "null"], "x-deserialize-default-on-error": true, "additionalProperties": true}
   DEL /anyOf/2/properties/description: {"type": ["string", "null"], "x-deserialize-default-on-error": true}

### AuthMethodTerminal
   ADD /properties/args/x-deserialize-default-on-null: true
   ADD /properties/env/x-deserialize-default-on-null: true

### AvailableCommand
   ADD /anyOf: [{"type": "object", "properties": {"type": {"type": "string", "const": "command"}}, "required": ["type"], "allOf": [{"$ref": "#/$defs/Command"}]}, {"type": "object", "properties": {"type": {"type": "string"}, "name": {"type": "string"}, "description": {"type": "string"}}, "required": ["type", "name"
   DEL /properties: {"name": {"type": "string"}, "description": {"type": "string"}, "input": {"anyOf": [{"$ref": "#/$defs/AvailableCommandInput"}, {"type": "null"}], "x-deserialize-default-on-error": true}, "_meta": {"type": ["object", "null"], "x-deserialize-default-on-error": true, "additionalProperties": true}}
   DEL /required: ["name", "description"]
   DEL /type: "object"

### AvailableCommandsUpdate
   DEL /properties/availableCommands/x-deserialize-default-on-error: true

### ClientCapabilities
   CHG /properties/auth/anyOf/0/$ref: "#/$defs/AuthCapabilities"  ->  "#/$defs/ClientAuthCapabilities"

### ClientRequest
   CHG /properties/params/anyOf/0/anyOf: [{"allOf": [{"$ref": "#/$defs/InitializeRequest"}]}, {"allOf": [{"$ref": "#/$defs/LoginAuthRequest"}]}, {"allOf": [{"$ref": "#/$defs/ListProvidersRequest"}]}, {"allOf": [{"$ref": "#/$defs/SetProviderRequest"}]}, {"allOf": [{"$ref": "#/$defs/DisableProviderRequest"}]}, {"allOf": [{"$ref": "#/$defs/Lo  ->  [{"allOf": [{"$ref": "#/$defs/InitializeRequest"}]}, {"allOf": [{"$ref": "#/$defs/LoginAuthRequest"}]}, {"allOf": [{"$ref": "#/$defs/ListProvidersRequest"}]}, {"allOf": [{"$ref": "#/$defs/SetProviderRequest"}]}, {"allOf": [{"$ref": "#/$defs/DisableProviderRequest"}]}, {"allOf": [{"$ref": "#/$defs/Lo

### ClientResponse
   DEL /anyOf/1/properties/id/allOf: [{"$ref": "#/$defs/RequestId"}]
   ADD /anyOf/1/properties/id/anyOf: [{"type": "integer", "format": "int64"}, {"type": "string"}, {"type": "null"}]

### ConfigOptionUpdate
   DEL /properties/configOptions/x-deserialize-default-on-error: true

### Cost
   DEL /properties/currency/pattern: "^[A-Z]{3}$"

### CreateElicitationRequest
   DEL /anyOf/2/anyOf: [{"allOf": [{"$ref": "#/$defs/ElicitationSessionScope"}]}, {"allOf": [{"$ref": "#/$defs/ElicitationRequestScope"}]}]
   ADD /anyOf/2/oneOf: [{"allOf": [{"$ref": "#/$defs/ElicitationSessionScope"}]}, {"allOf": [{"$ref": "#/$defs/ElicitationRequestScope"}]}]

### DiffPatch
   ADD /properties/_meta: {"type": ["object", "null"], "x-deserialize-default-on-error": true, "additionalProperties": true}

### ElicitationContentValue
   CHG /anyOf: [{"type": "string"}, {"type": "integer", "format": "int64"}, {"type": "number", "format": "double"}, {"type": "boolean"}, {"type": "array", "items": {"type": "string"}}]  ->  [{"type": "string"}, {"type": "integer", "format": "int64"}, {"type": "number", "format": "double"}, {"type": "boolean"}, {"type": "array", "items": {"type": "string"}}, {}]

### ElicitationFormMode
   DEL /anyOf: [{"allOf": [{"$ref": "#/$defs/ElicitationSessionScope"}]}, {"allOf": [{"$ref": "#/$defs/ElicitationRequestScope"}]}]
   ADD /oneOf: [{"allOf": [{"$ref": "#/$defs/ElicitationSessionScope"}]}, {"allOf": [{"$ref": "#/$defs/ElicitationRequestScope"}]}]

### ElicitationSchema
   DEL /properties/properties/default: {}
   DEL /properties/type/default: "object"
   DEL /properties/type/x-deserialize-default-on-error: true
   ADD /required: ["type", "properties"]

### ElicitationUrlMode
   DEL /anyOf: [{"allOf": [{"$ref": "#/$defs/ElicitationSessionScope"}]}, {"allOf": [{"$ref": "#/$defs/ElicitationRequestScope"}]}]
   ADD /oneOf: [{"allOf": [{"$ref": "#/$defs/ElicitationSessionScope"}]}, {"allOf": [{"$ref": "#/$defs/ElicitationRequestScope"}]}]

### Error
   ADD /properties/data/anyOf: [{"$ref": "#/$defs/ErrorData"}, {"type": "null"}]

### ForkSessionRequest
   ADD /properties/additionalDirectories/x-deserialize-default-on-null: true
   ADD /properties/mcpServers/x-deserialize-default-on-null: true

### Icon
   ADD /properties/_meta: {"type": ["object", "null"], "x-deserialize-default-on-error": true, "additionalProperties": true}

### IdleStateUpdate
   ADD /properties/background: {"type": ["array", "null"], "items": {"$ref": "#/$defs/BackgroundWork"}, "x-deserialize-default-on-error": true}

### ListSessionsRequest
   ADD /properties/archived: {"anyOf": [{"$ref": "#/$defs/SessionArchiveFilter"}, {"type": "null"}]}

### ListSessionsResponse
   DEL /properties/nextCursor/x-deserialize-default-on-error: true

### McpServerHttp
   ADD /properties/headers/x-deserialize-default-on-null: true

### McpServerStdio
   ADD /properties/args/x-deserialize-default-on-null: true
   ADD /properties/env/x-deserialize-default-on-null: true

### NewSessionRequest
   ADD /properties/additionalDirectories/x-deserialize-default-on-null: true
   ADD /properties/mcpServers/x-deserialize-default-on-null: true

### PlanItems
   DEL /properties/entries/x-deserialize-default-on-error: true

### PromptRequest
   ADD /properties/prompt/minItems: 1

### ReplayFrom
   DEL /anyOf/1/properties/_meta: {"type": ["object", "null"], "x-deserialize-default-on-error": true, "additionalProperties": true}

### RequestId
   CHG /anyOf: [{"type": "null"}, {"type": "integer", "format": "int64"}, {"type": "string"}]  ->  [{"type": "integer", "format": "int64"}, {"type": "string"}]

### RequestPermissionOutcome
   ADD /anyOf/0/allOf: [{"$ref": "#/$defs/CancelledPermissionOutcome"}]

### RequiresActionStateUpdate
   ADD /properties/background: {"type": ["array", "null"], "items": {"$ref": "#/$defs/BackgroundWork"}, "x-deserialize-default-on-error": true}

### ResourceLink
   CHG /properties/size/format: "int64"  ->  "uint64"
   ADD /properties/size/minimum: 0

### ResumeSessionRequest
   ADD /properties/additionalDirectories/x-deserialize-default-on-null: true
   ADD /properties/mcpServers/x-deserialize-default-on-null: true

### RunningStateUpdate
   ADD /properties/background: {"type": ["array", "null"], "items": {"$ref": "#/$defs/BackgroundWork"}, "x-deserialize-default-on-error": true}

### SessionCapabilities
   ADD /properties/archive: {"anyOf": [{"$ref": "#/$defs/SessionArchiveCapabilities"}, {"type": "null"}], "x-deserialize-default-on-error": true}
   ADD /properties/status: {"anyOf": [{"$ref": "#/$defs/SessionStatusCapabilities"}, {"type": "null"}], "x-deserialize-default-on-error": true}
   ADD /properties/title: {"anyOf": [{"$ref": "#/$defs/SessionTitleCapabilities"}, {"type": "null"}], "x-deserialize-default-on-error": true}

### SessionConfigSelectGroup
   ADD /properties/options/minItems: 1

### SessionConfigSelectOptions
   ADD /anyOf/0/minItems: 1
   ADD /anyOf/1/minItems: 1

### SessionInfo
   DEL /properties/additionalDirectories/x-deserialize-default-on-error: true
   ADD /properties/additionalDirectories/x-deserialize-default-on-null: true
   DEL /properties/additionalDirectories/x-deserialize-skip-invalid-items: true
   ADD /properties/archived: {"type": ["boolean", "null"], "x-deserialize-default-on-error": true}

### SessionMessage
   ADD /properties/recipientMessageId: {"anyOf": [{"$ref": "#/$defs/MessageId"}, {"type": "null"}], "x-deserialize-default-on-error": true}
   ADD /properties/senderMessageId: {"anyOf": [{"$ref": "#/$defs/MessageId"}, {"type": "null"}], "x-deserialize-default-on-error": true}

### SessionMessageChunk
   DEL /properties/recipientSessionId: {"anyOf": [{"$ref": "#/$defs/SessionId"}, {"type": "null"}], "x-deserialize-default-on-error": true}
   DEL /properties/senderSessionId: {"anyOf": [{"$ref": "#/$defs/SessionId"}, {"type": "null"}], "x-deserialize-default-on-error": true}

### SetSessionConfigOptionResponse
   DEL /properties/configOptions/x-deserialize-default-on-error: true

### SubagentUpdate
   ADD /properties/additionalDirectories: {"type": ["array", "null"], "items": {"$ref": "#/$defs/AbsolutePath"}}
   ADD /properties/cwd: {"anyOf": [{"$ref": "#/$defs/AbsolutePath"}, {"type": "null"}]}

### TerminalExitStatus
   CHG /properties/exitCode/format: "uint32"  ->  "int64"
   DEL /properties/exitCode/minimum: 0

### TerminalUpdate
   ADD /properties/capabilities: {"anyOf": [{"$ref": "#/$defs/TerminalCapabilities"}, {"type": "null"}], "x-deserialize-default-on-error": true}
   ADD /properties/size: {"anyOf": [{"$ref": "#/$defs/TerminalSize"}, {"type": "null"}], "x-deserialize-default-on-error": true}

### ToolCallContent
   CHG /anyOf: [{"type": "object", "properties": {"type": {"type": "string", "const": "content"}}, "required": ["type"], "allOf": [{"$ref": "#/$defs/Content"}]}, {"type": "object", "properties": {"type": {"type": "string", "const": "diff"}}, "required": ["type"], "allOf": [{"$ref": "#/$defs/Diff"}]}, {"type": "obj  ->  [{"type": "object", "properties": {"type": {"type": "string", "const": "content"}}, "required": ["type"], "allOf": [{"$ref": "#/$defs/Content"}]}, {"type": "object", "properties": {"type": {"type": "string", "const": "diff"}}, "required": ["type"], "allOf": [{"$ref": "#/$defs/Diff"}]}, {"type": "obj

### ToolCallLocation
   CHG /properties/line/minimum: 0  ->  1

### ToolCallPermissionSubject
   ADD /properties/_meta: {"type": ["object", "null"], "x-deserialize-default-on-error": true, "additionalProperties": true}

### ToolCallStatus
   CHG /anyOf: [{"type": "string", "const": "pending"}, {"type": "string", "const": "in_progress"}, {"type": "string", "const": "completed"}, {"type": "string", "const": "failed"}, {"type": "string", "const": "cancelled"}, {"type": "string"}]  ->  [{"type": "string", "const": "pending"}, {"type": "string", "const": "in_progress"}, {"type": "string", "const": "paused"}, {"type": "string", "const": "completed"}, {"type": "string", "const": "failed"}, {"type": "string", "const": "cancelled"}, {"type": "string"}]

### ToolCallUpdate
   ADD /properties/capabilities: {"anyOf": [{"$ref": "#/$defs/ToolCallCapabilities"}, {"type": "null"}], "x-deserialize-default-on-error": true}

### UnknownStateUpdate
   ADD /properties/background: {"type": ["array", "null"], "items": {"$ref": "#/$defs/BackgroundWork"}, "x-deserialize-default-on-error": true}

structurally changed defs: 53
~~~

## Appendix A. Full `spec-impact` output (unedited)

Verbatim stdout of the command in section 1 (162 KB). Between the fences, everything is tool output.

~~~markdown
# Spec impact (v2): `beac4ba96190` -> `3961af94fa62`

Base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a`. Scope: `docs/protocol/v2/draft/`, `schema/v2/`, `docs/rfds/`.

## 1. Changed files

- modified: `docs/protocol/v2/draft/agent-plan.mdx`
- modified: `docs/protocol/v2/draft/authentication.mdx`
- modified: `docs/protocol/v2/draft/cancellation.mdx`
- modified: `docs/protocol/v2/draft/content.mdx`
- modified: `docs/protocol/v2/draft/elicitation.mdx`
- modified: `docs/protocol/v2/draft/error.mdx`
- modified: `docs/protocol/v2/draft/extensibility.mdx`
- modified: `docs/protocol/v2/draft/initialization.mdx`
- modified: `docs/protocol/v2/draft/overview.mdx`
- modified: `docs/protocol/v2/draft/prompt-lifecycle.mdx`
- modified: `docs/protocol/v2/draft/schema.mdx`
- added: `docs/protocol/v2/draft/security.mdx`
- modified: `docs/protocol/v2/draft/session-config-options.mdx`
- modified: `docs/protocol/v2/draft/session-delete.mdx`
- modified: `docs/protocol/v2/draft/session-list.mdx`
- modified: `docs/protocol/v2/draft/session-setup.mdx`
- modified: `docs/protocol/v2/draft/slash-commands.mdx`
- modified: `docs/protocol/v2/draft/tool-calls.mdx`
- modified: `docs/protocol/v2/draft/transports.mdx`
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
- modified: `schema/v2/CHANGELOG.md`
- modified: `schema/v2/Cargo.toml`
- modified: `schema/v2/meta.json`
- modified: `schema/v2/meta.unstable.json`
- modified: `schema/v2/schema.json`
- modified: `schema/v2/schema.unstable.json`

## 2. Doc hunks -> sections

Base-side sections for removed or modified text, target-side for pure additions.

### `docs/protocol/v2/draft/agent-plan.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-8,1 +8,1` (base): `(intro)`
- `-14,1 +14,1` (base): `Creating Plans`
- `-18,1 +18,1` (base): `Creating Plans > Item-Based Plans`
- `-67,1 +67,1` (base): `Unstable Plan Operations`
- `-79,1 +79,1` (base): `Unstable Plan Operations > Markdown Plans`
- `-99,1 +99,1` (base): `Unstable Plan Operations > File Plans`
- `-121,1 +121,1` (base): `Removing Plans`
- `-138,0 +139,4` (target): `Removing plans`
- `-141,1 +145,1` (base): `Extensibility`
- `-145,1 +149,1` (base): `Plan Entries`
- `-160,1 +164,1` (base): `Plan Entries`
- `-165,1 +169,1` (base): `Plan Entries`
- `-172,1 +176,1` (base): `Plan Entries`
- `-176,1 +180,1` (base): `Updating Plans`
- `-180,1 +184,3` (base): `Updating Plans`
- `-182,1 +188,1` (base): `Updating Plans > Dynamic Planning`
- `-184,1 +190,1` (base): `Updating Plans > Dynamic Planning`

### `docs/protocol/v2/draft/authentication.mdx` (modified)

- `-44,1 +44,1` (base): `Advertising Authentication`
- `-51,2 +51,1` (base): `Advertising Authentication`
- `-54,1 +53,1` (base): `Advertising Authentication`
- `-84,2 +83,1` (base): `Advertising Authentication`
- `-90,1 +88,1` (base): `Advertising Authentication > Authentication method types`
- `-123,1 +121,1` (base): `Advertising Authentication > Authentication method types`
- `-153,2 +151,1` (base): `Advertising Authentication > Authentication method types`
- `-179,1 +176,1` (base): `Agent-handled authentication`
- `-181,0 +179,2` (target): `Agent-handled authentication`
- `-192,2 +191,5` (base): `Agent-handled authentication`
- `-205,1 +207,1` (base): `Terminal authentication`
- `-207,2 +209,1` (base): `Terminal authentication`
- `-214,1 +215,1` (base): `Terminal authentication`
- `-218,0 +220,6` (target): `Terminal authentication > Launch safety`
- `-238,1 +245,1` (base): `Logging Out`
- `-241,2 +248,1` (base): `Logging Out`
- `-267,1 +273,1` (base): `Active Sessions`
- `-274,1 +280,1` (base): `Active Sessions`

### `docs/protocol/v2/draft/cancellation.mdx` (modified)

- `-10,1 +10,1` (base): ``$/cancel_request` Notification`
- `-12,1 +12,1` (base): ``$/cancel_request` Notification`
- `-14,1 +14,1` (base): ``$/cancel_request` Notification`
- `-20,3 +20,1` (base): ``$/cancel_request` Notification`
- `-24,1 +22,1` (base): ``$/cancel_request` Notification`
- `-26,1 +24,10` (base): ``$/cancel_request` Notification`
- `-33,2 +40,1` (base): ``$/cancel_request` Notification`
- `-41,1 +47,1` (base): `Internal Cancellation`
- `-45,2 +51,2` (base): `Internal Cancellation`
- `-50,1 +56,1` (base): `Internal Cancellation`
- `-53,1 +59,1` (base): `Internal Cancellation`
- `-55,1 +61,1` (base): `Example: Cascading Cancellation Flow`
- `-57,1 +63,1` (base): `Example: Cascading Cancellation Flow`
- `-77,1 +83,3` (base): `Example: Cascading Cancellation Flow`

### `docs/protocol/v2/draft/content.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-14,1 +14,1` (base): `Content Types`
- `-16,1 +16,1` (base): `Content Types`
- `-18,1 +18,1` (base): `Content Types`
- `-20,1 +20,1` (base): `Content Types`
- `-22,1 +22,1` (base): `Content Types > Text Content`
- `-24,1 +24,7` (base): `Content Types > Text Content`
- `-44,1 +50,1` (base): `Content Types > Image Content`
- `-57,2 +63,2` (base): `Content Types > Image Content`
- `-77,1 +83,1` (base): `Content Types > Audio Content`
- `-90,2 +96,2` (base): `Content Types > Audio Content`
- `-106,1 +112,1` (base): `Content Types > Embedded Resource`
- `-126,2 +132,2` (base): `Content Types > Embedded Resource`
- `-168,1 +174,3` (base): `Content Types > Resource Link`
- `-170,1 +178,1` (base): `Content Types > Resource Link`

### `docs/protocol/v2/draft/elicitation.mdx` (modified)

- `-8,1 +8,1` (base): `(intro)`
- `-50,1 +50,1` (base): `Checking support`
- `-53,0 +54,2` (target): `Checking support`
- `-56,0 +59,2` (target): `Checking support`
- `-60,1 +64,1` (base): `Creating an elicitation`
- `-63,1 +67,2` (base): `Creating an elicitation`
- `-67,1 +72,6` (base): `Creating an elicitation`
- `-73,1 +83,1` (base): `Creating an elicitation > Foreground State`
- `-119,3 +129,24` (base): `Creating an elicitation > Form mode`
- `-132,1 +163,1` (base): `Creating an elicitation > Form mode`
- `-154,1 +185,1` (base): `Creating an elicitation > URL mode`
- `-166,4 +197,5` (base): `Responses`
- `-185,1 +217,1` (base): `Responses > URL completion`
- `-187,4 +219,1` (base): `Responses > URL completion` | `Session Cancellation`
- `-203,0 +233,2` (target): `Session cancellation`
- `-221,1 +252,1` (base): `URL security`
- `-237,2 +268,1` (base): `URL security`

### `docs/protocol/v2/draft/error.mdx` (modified)

- `-2,1 +2,1` (base): `(intro)`
- `-6,1 +6,63` (base): `(intro)`

### `docs/protocol/v2/draft/extensibility.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-8,1 +8,1` (base): `Experimental Features and Negotiation`
- `-21,1 +21,1` (base): `Experimental Features and Negotiation > When a Capability Is Required`
- `-25,1 +25,1` (base): `Experimental Features and Negotiation > When a Capability Is Required`
- `-33,1 +33,3` (base): `Experimental Features and Negotiation > When a Capability Is Required`
- `-35,2 +37,2` (base): `Experimental Features and Negotiation > When a Capability Is Required`
- `-57,3 +59,7` (base): `Experimental Features and Negotiation > Validation`
- `-64,1 +70,1` (base): `The `_meta` Field`
- `-67,0 +74,2` (target): `The `_meta` field`
- `-83,1 +91,1` (base): `The `_meta` Field`
- `-89,1 +97,4` (base): `The `_meta` Field`
- `-91,3 +102,1` (base): `The `_meta` Field`
- `-97,1 +106,1` (base): `The `_meta` Field > Metadata Patches`
- `-112,2 +121,2` (base): `The `_meta` Field > Metadata Patches`
- `-124,3 +133,3` (base): `The `_meta` Field > Metadata Patches`
- `-135,2 +144,2` (base): `The `_meta` Field > Metadata Patches`
- `-140,1 +149,1` (base): `The `_meta` Field > Metadata Patches`
- `-142,1 +151,1` (base): `The `_meta` Field > Metadata Patches`
- `-146,1 +155,1` (base): `Unknown Object Fields`
- `-154,1 +163,1` (base): `Extension Methods`
- `-156,1 +165,1` (base): `Extension Methods`
- `-163,1 +172,1` (base): `Extension Methods > Custom Requests`
- `-171,1 +180,1` (base): `Extension Methods > Custom Requests`
- `-193,1 +202,1` (base): `Extension Methods > Custom Requests`
- `-208,1 +217,1` (base): `Extension Methods > Custom Notifications`
- `-215,1 +224,1` (base): `Extension Methods > Custom Notifications`
- `-222,1 +231,1` (base): `Extension Methods > Custom Notifications`
- `-224,1 +233,1` (base): `Enum and Tagged-Union Variants`
- `-233,1 +242,6` (base): `Enum and Tagged-Union Variants`
- `-237,1 +251,1` (base): `Advertising Custom Capabilities`
- `-241,1 +255,1` (base): `Advertising Custom Capabilities`
- `-245,1 +259,3` (base): `Advertising Custom Capabilities`
- `-257,4 +273,2` (base): `Advertising Custom Capabilities`
- `-272,1 +286,1` (base): `Advertising Custom Capabilities`

### `docs/protocol/v2/draft/initialization.mdx` (modified)

- `-82,1 +82,1` (base): `(intro)`
- `-84,1 +84,11` (base): `(intro)`
- `-94,1 +104,1` (base): `Protocol version > Version Negotiation`
- `-97,0 +108,2` (target): `Protocol version > Version negotiation`
- `-117,1 +129,3` (base): `Protocol version > Version Negotiation`
- `-120,0 +135,8` (target): `Protocol version > Version negotiation > Repeating initialization`
- `-125,1 +147,1` (base): `Capabilities`
- `-127,1 +149,1` (base): `Capabilities`
- `-129,2 +151,2` (base): `Capabilities`
- `-144,1 +166,1` (base): `Capabilities > Client Capabilities`
- `-147,1 +169,2` (base): `Capabilities > Client Capabilities`
- `-149,1 +172,1` (base): `Capabilities > Client Capabilities > Terminal Authentication`
- `-175,1 +198,1` (base): `Capabilities > Agent Capabilities`
- `-180,5 +203,4` (base): `Capabilities > Agent Capabilities`
- `-192,0 +215,7` (target): `Capabilities > Agent capabilities`
- `-195,1 +224,1` (base): `Capabilities > Agent Capabilities`
- `-200,1 +229,1` (base): `Capabilities > Agent Capabilities > Session Capabilities`
- `-209,0 +239,3` (target): `Capabilities > Agent capabilities > Session capabilities`
- `-228,0 +261,28` (target): `Capabilities > Agent capabilities > Session capabilities`
- `-239,3 +299,3` (base): `Capabilities > Agent Capabilities > Session Capabilities`
- `-246,1 +306,1` (base): `Capabilities > Agent Capabilities > Session Prompt Capabilities`
- `-248,1 +308,1` (base): `Capabilities > Agent Capabilities > Session Prompt Capabilities`
- `-253,1 +313,1` (base): `Capabilities > Agent Capabilities > Session Prompt Capabilities`
- `-259,1 +319,1` (base): `Capabilities > Agent Capabilities > Session Prompt Capabilities`
- `-268,1 +328,1` (base): `Capabilities > Agent Capabilities > Session Prompt Capabilities`
- `-273,1 +333,1` (base): `Capabilities > Agent Capabilities > Session MCP Capabilities`
- `-286,0 +347,7` (target): `Capabilities > Agent capabilities > Session MCP capabilities`
- `-291,1 +358,1` (base): `Implementation Information`
- `-295,1 +362,1` (base): `Implementation Information`
- `-297,1 +364,1` (base): `Implementation Information`
- `-301,2 +368,3` (base): `Implementation Information`
- `-305,1 +373,1` (base): `Implementation Information`

### `docs/protocol/v2/draft/overview.mdx` (modified)

- `-12,2 +12,2` (base): `Communication Model`
- `-15,3 +15,3` (base): `Communication Model`
- `-19,1 +19,5` (base): `Message Flow`
- `-27,1 +31,1` (base): `Message Flow`
- `-45,2 +49,2` (base): `Message Flow`
- `-54,1 +58,1` (base): `Agent > Baseline Methods`
- `-56,1 +60,1` (base): `Agent > Baseline Methods`
- `-119,0 +124,21` (target): `Agent > Optional methods`
- `-126,2 +151,3` (base): `Agent > Notifications`
- `-134,1 +160,1` (base): `Client > Baseline Methods`
- `-147,1 +173,1` (base): `Client > Optional Methods`
- `-185,0 +212,4` (target): `Request cancellation`
- `-188,1 +218,1` (base): `Argument requirements`
- `-191,1 +221,1` (base): `Error Handling`
- `-198,0 +229,2` (target): `Error handling`
- `-202,0 +235,2` (target): `Conventions`
- `-207,1 +241,1` (base): `Extensibility`
- `-213,9 +247,29` (base): `Extensibility` | `Next Steps`

### `docs/protocol/v2/draft/prompt-lifecycle.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-8,1 +8,1` (base): `(intro)`
- `-12,1 +12,1` (base): `Session Updates`
- `-16,25 +16,25` (base): `Session Updates`
- `-44,1 +44,1` (base): `Session Updates`
- `-46,2 +46,1` (base): `Session Updates`
- `-64,1 +63,1` (base): `Session Updates > Entity IDs`
- `-66,1 +65,1` (base): `Session Updates > Entity IDs`
- `-68,1 +67,3` (base): `Session Updates > Entity IDs`
- `-76,3 +77,5` (base): `Session Updates > Session-directed messages (unstable)`
- `-80,1 +83,2` (base): `Session Updates > Session-directed messages (unstable)`
- `-89,1 +93,1` (base): `Session Updates > Session-directed messages (unstable)`
- `-92,1 +96,15` (base): `Session Updates > Session-directed messages (unstable)`
- `-99,1 +117,1` (base): `Session Updates > Session-directed messages (unstable)`
- `-103,1 +121,1` (base): `Session Updates > Session-directed messages (unstable)`
- `-109,4 +127,7` (base): `Session Updates > Session-directed messages (unstable)`
- `-116,1 +137,8` (base): `Foreground and Background Work`
- `-148,1 +176,11` (base): `Prompt Lifecycle`
- `-150,1 +188,1` (base): `Prompt Lifecycle`
- `-152,1 +190,31` (base): `Prompt Lifecycle`
- `-208,1 +276,1` (base): `Prompt Lifecycle > 1. User Message`
- `-237,1 +305,1` (base): `Prompt Lifecycle > 1. User Message`
- `-240,1 +308,1` (base): `Prompt Lifecycle > 1. User Message`
- `-243,1 +311,3` (base): `Prompt Lifecycle > 1. User Message`
- `-251,1 +321,1` (base): `Prompt Lifecycle > 2. Prompt Accepted`
- `-255,1 +325,1` (base): `Prompt Lifecycle > 2. Prompt Accepted`
- `-273,1 +343,1` (base): `Prompt Lifecycle > 2. Prompt Accepted`
- `-298,1 +368,1` (base): `Prompt Lifecycle > 2. Prompt Accepted`
- `-302,1 +372,1` (base): `Prompt Lifecycle > 2. Prompt Accepted`
- `-304,1 +374,1` (base): `Prompt Lifecycle > 2. Prompt Accepted`
- `-309,0 +380,6` (target): `Prompt lifecycle > 2. Prompt accepted > Prompts during active work`
- `-316,1 +392,1` (base): `Prompt Lifecycle > 3. Agent Reports Output`
- `-405,0 +482,2` (target): `Prompt lifecycle > 3. Agent reports output > Message IDs`
- `-408,1 +486,1` (base): `Prompt Lifecycle > 3. Agent Reports Output`
- `-410,1 +488,1` (base): `Prompt Lifecycle > 3. Agent Reports Output`
- `-420,1 +498,1` (base): `Prompt Lifecycle > 3. Agent Reports Output`
- `-442,1 +520,1` (base): `Prompt Lifecycle > 3. Agent Reports Output`
- `-483,1 +561,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Notices`
- `-488,1 +566,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Notices`
- `-520,2 +598,2` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Notices`
- `-525,2 +603,2` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Notices`
- `-532,1 +610,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Notices`
- `-542,1 +620,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-550,1 +628,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-578,4 +656,3` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-593,1 +670,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-659,2 +736,2` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-663,1 +740,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-669,1 +746,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-671,1 +748,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-675,6 +752,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-683,1 +755,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-685,1 +757,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Compaction`
- `-687,1 +759,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Usage Updates`
- `-710,1 +782,1` (base): `Prompt Lifecycle > 3. Agent Reports Output > Session Usage Updates`
- `-712,1 +784,1` (base): `Prompt Lifecycle > 4. Report Completion`
- `-735,1 +807,1` (base): `Prompt Lifecycle > 4. Report Completion > End-Turn Token Usage (Unstable)`
- `-762,1 +834,1` (base): `Prompt Lifecycle > 4. Report Completion > End-Turn Token Usage (Unstable)`
- `-769,1 +841,1` (base): `Prompt Lifecycle > 5. Tool Invocation and Status Reporting`
- `-793,1 +865,1` (base): `Prompt Lifecycle > 5. Tool Invocation and Status Reporting`
- `-856,1 +928,1` (base): `Prompt Lifecycle > 6. Continue Conversation`
- `-862,1 +934,1` (base): `Stop Reasons`
- `-864,1 +936,1` (base): `Stop Reasons`
- `-881,1 +953,5` (base): `Stop Reasons`
- `-887,1 +963,3` (base): `Stop Reasons`
- `-918,1 +996,1` (base): `Failures`
- `-920,1 +998,1` (base): `Failures`
- `-929,1 +1007,1` (base): `Failures`
- `-931,1 +1009,1` (base): `Session States`
- `-939,1 +1017,1` (base): `Session States`
- `-963,1 +1041,1` (base): `Session States`
- `-966,1 +1044,3` (base): `Session States`
- `-968,1 +1048,1` (base): `Session States > Initial State and Synchronization`
- `-983,1 +1063,1` (base): `Session States > State Transitions`
- `-1015,1 +1095,1` (base): `Session States > Waiting for User Action`
- `-1032,1 +1112,1` (base): `Session States > Work Boundaries and Local Commands`
- `-1039,2 +1119,1` (base): `Session States > Work Boundaries and Local Commands`
- `-1049,1 +1128,1` (base): `Session States > Lifecycle Examples`
- `-1082,1 +1161,1` (base): `Cancellation`
- `-1094,1 +1173,1` (base): `Cancellation`
- `-1096,1 +1175,1` (base): `Cancellation`
- `-1098,4 +1177,1` (base): `Cancellation`
- `-1103,1 +1179,1` (base): `Cancellation`
- `-1116,2 +1192,1` (base): `Cancellation`
- `-1131,4 +1205,0` (base): `Cancellation`

### `docs/protocol/v2/draft/schema.mdx` (modified)

- `-24,2 +24,2` (base): `Agent > auth/login`
- `-33,1 +33,1` (base): `Agent > auth/login`
- `-43,2 +43,2` (base): `Agent > auth/login > LoginAuthRequest`
- `-53,2 +53,2` (base): `Agent > auth/login > LoginAuthRequest`
- `-74,2 +74,2` (base): `Agent > auth/login > LoginAuthResponse`
- `-86,2 +86,2` (base): `Agent > auth/logout`
- `-100,2 +100,2` (base): `Agent > auth/logout > LogoutAuthRequest`
- `-110,2 +110,2` (base): `Agent > auth/logout > LogoutAuthRequest`
- `-127,2 +127,2` (base): `Agent > auth/logout > LogoutAuthResponse`
- `-133,0 +134,74` (target): `Agent > auth/logout > LogoutAuthResponse` | `Agent > auth/status` | `Agent > auth/status > AuthStatusRequest` | `Agent > auth/status > AuthStatusResponse`
- `-138,1 +212,1` (base): `Agent > initialize`
- `-143,0 +218,3` (target): `Agent > initialize`
- `-162,2 +239,2` (base): `Agent > initialize > InitializeRequest`
- `-195,2 +272,2` (base): `Agent > initialize > InitializeResponse`
- `-205,1 +282,1` (base): `Agent > initialize > InitializeResponse`
- `-248,3 +325,8` (base): `Agent > mcp/message > MessageMcpNotification`
- `-255,2 +337,2` (base): `Agent > mcp/message > MessageMcpNotification`
- `-258,5 +340,1` (base): `Agent > mcp/message > MessageMcpNotification`
- `-265,5 +343,1` (base): `Agent > mcp/message > MessageMcpNotification`
- `-296,2 +370,2` (base): `Agent > providers/disable > DisableProviderRequest`
- `-320,2 +394,2` (base): `Agent > providers/disable > DisableProviderResponse`
- `-350,2 +424,2` (base): `Agent > providers/list > ListProvidersRequest`
- `-371,2 +445,2` (base): `Agent > providers/list > ListProvidersResponse`
- `-406,2 +480,2` (base): `Agent > providers/set > SetProviderRequest`
- `-443,2 +517,65` (base): `Agent > providers/set > SetProviderResponse`
- `-453,1 +590,1` (base): `Agent > session/cancel`
- `-455,2 +592,2` (base): `Agent > session/cancel`
- `-459,1 +596,6` (base): `Agent > session/cancel`
- `-481,1 +623,1` (base): `Agent > session/cancel > CancelSessionNotification`
- `-491,2 +633,2` (base): `Agent > session/cancel > CancelSessionNotification`
- `-498,1 +640,1` (base): `Agent > session/cancel > CancelSessionNotification`
- `-506,2 +648,2` (base): `Agent > session/close`
- `-513,3 +655,7` (base): `Agent > session/close > CloseSessionRequest`
- `-522,2 +668,2` (base): `Agent > session/close > CloseSessionRequest`
- `-534,2 +680,2` (base): `Agent > session/close > CloseSessionRequest`
- `-554,2 +700,2` (base): `Agent > session/close > CloseSessionResponse`
- `-580,2 +726,2` (base): `Agent > session/delete > DeleteSessionRequest`
- `-600,2 +746,2` (base): `Agent > session/delete > DeleteSessionResponse`
- `-645,2 +791,2` (base): `Agent > session/fork > ForkSessionRequest`
- `-669,1 +815,1` (base): `Agent > session/fork > ForkSessionRequest`
- `-671,5 +817,1` (base): `Agent > session/fork > ForkSessionRequest`
- `-697,2 +839,2` (base): `Agent > session/fork > ForkSessionResponse`
- `-707,1 +849,1` (base): `Agent > session/fork > ForkSessionResponse`
- `-712,0 +855,5` (target): `Agent > session/fork > ForkSessionResponse`
- `-735,2 +882,2` (base): `Agent > session/list > ListSessionsRequest`
- `-739,0 +887,12` (target): `Agent > session/list > ListSessionsRequest`
- `-742,0 +902,3` (target): `Agent > session/list > ListSessionsRequest`
- `-745,0 +908,6` (target): `Agent > session/list > ListSessionsRequest`
- `-758,2 +926,2` (base): `Agent > session/list > ListSessionsResponse`
- `-766,1 +934,2` (base): `Agent > session/list > ListSessionsResponse`
- `-785,1 +954,1` (base): `Agent > session/new`
- `-801,2 +970,2` (base): `Agent > session/new > NewSessionRequest`
- `-822,5 +991,1` (base): `Agent > session/new > NewSessionRequest`
- `-850,2 +1015,2` (base): `Agent > session/new > NewSessionResponse`
- `-860,1 +1025,1` (base): `Agent > session/new > NewSessionResponse`
- `-865,0 +1031,5` (target): `Agent > session/new > NewSessionResponse`
- `-884,2 +1054,2` (base): `Agent > session/prompt`
- `-891,1 +1061,1` (base): `Agent > session/prompt`
- `-913,2 +1083,2` (base): `Agent > session/prompt > PromptRequest`
- `-922,1 +1092,1` (base): `Agent > session/prompt > PromptRequest`
- `-928,1 +1098,1` (base): `Agent > session/prompt > PromptRequest`
- `-930,1 +1100,1` (base): `Agent > session/prompt > PromptRequest`
- `-933,0 +1104,3` (target): `Agent > session/prompt > PromptRequest`
- `-943,1 +1116,1` (base): `Agent > session/prompt > PromptResponse`
- `-958,2 +1131,2` (base): `Agent > session/prompt > PromptResponse`
- `-997,2 +1170,2` (base): `Agent > session/resume > ResumeSessionRequest`
- `-1013,0 +1187,4` (target): `Agent > session/resume > ResumeSessionRequest`
- `-1016,0 +1194,4` (target): `Agent > session/resume > ResumeSessionRequest`
- `-1021,1 +1202,1` (base): `Agent > session/resume > ResumeSessionRequest`
- `-1036,5 +1217,1` (base): `Agent > session/resume > ResumeSessionRequest`
- `-1042,1 +1219,1` (base): `Agent > session/resume > ResumeSessionRequest`
- `-1066,2 +1243,2` (base): `Agent > session/resume > ResumeSessionResponse`
- `-1076,1 +1253,1` (base): `Agent > session/resume > ResumeSessionResponse`
- `-1081,0 +1259,5` (target): `Agent > session/resume > ResumeSessionResponse`
- `-1092,0 +1275,6` (target): `Agent > session/set_config_option > SetSessionConfigOptionRequest`
- `-1099,2 +1287,2` (base): `Agent > session/set_config_option > SetSessionConfigOptionRequest`
- `-1154,0 +1343,3` (target): `Agent > session/set_config_option > SetSessionConfigOptionRequest`
- `-1182,2 +1373,2` (base): `Agent > session/set_config_option > SetSessionConfigOptionResponse`
- `-1192,1 +1383,2` (base): `Client`
- `-1194,1 +1386,1` (base): `Client`
- `-1196,3 +1388,1` (base): `Client`
- `-1200,2 +1390,1` (base): `Client` | `Client > elicitation/complete`
- `-1203,1 +1392,1` (base): `Client > elicitation/complete`
- `-1205,1 +1394,2` (base): `Client > elicitation/complete`
- `-1207,1 +1397,1` (base): `Client > elicitation/complete > CompleteElicitationNotification`
- `-1209,1 +1399,1` (base): `Client > elicitation/complete > CompleteElicitationNotification`
- `-1211,1 +1401,11` (base): `Client > elicitation/complete > CompleteElicitationNotification`
- `-1219,4 +1419,2` (base): `Client > elicitation/complete > CompleteElicitationNotification`
- `-1227,2 +1425,2` (base): `Client > elicitation/complete > CompleteElicitationNotification`
- `-1229,0 +1428,2` (target): `Agent > session/set_title > SetSessionTitleRequest`
- `-1231,8 +1431,4` (base): `Client > elicitation/complete > CompleteElicitationNotification` | `Client > elicitation/create` | `Client > elicitation/create > CreateElicitationRequest`
- `-1240,1 +1436,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1242,3 +1438,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1246,6 +1440,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1253,2 +1442,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1256,1 +1444,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1258,1 +1446,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1260,1 +1448,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1264,4 +1452,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1272,8 +1458,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1281,1 +1461,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1283,9 +1463,0` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1294,1 +1466,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1296,1 +1469,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1298,2 +1471,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1301,1 +1473,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1303,5 +1475,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1309,2 +1477,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1312,1 +1479,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1314,2 +1481,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1317,3 +1483,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1321,1 +1485,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1323,7 +1487,3` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1331,2 +1491,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1334,1 +1493,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1336,2 +1495,4` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1339,1 +1500,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1341,2 +1501,0` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1344,2 +1503,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1347,2 +1505,0` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1350,1 +1507,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1352,1 +1509,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1354,1 +1511,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1356,1 +1513,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1358,2 +1515,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1361,1 +1518,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1363,5 +1520,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1369,2 +1522,4` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1372,1 +1527,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1374,1 +1528,0` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1375,0 +1530,3` (target): `Agent > session/status > SessionStatusResponse`
- `-1377,5 +1534,4` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1383,6 +1538,0` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1389,0 +1540,2` (target): `Agent > session/status > SessionStatusResponse`
- `-1391,2 +1543,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1396,10 +1547,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1407,1 +1550,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1409,2 +1552,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1412,3 +1554,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1416,1 +1556,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1418,1 +1558,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1420,1 +1560,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1422,2 +1562,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1425,1 +1564,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1427,5 +1566,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1433,2 +1568,5` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1436,1 +1574,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1438,2 +1576,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1441,3 +1578,4` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1445,1 +1583,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1447,6 +1584,0` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1454,2 +1586,2` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1458,1 +1590,1` (base): `Client > elicitation/create > CreateElicitationRequest`
- `-1460,1 +1592,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1462,1 +1594,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1464,1 +1596,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1466,1 +1598,3` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1470,4 +1604,2` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1479,1 +1611,2` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1481,2 +1614,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1484,1 +1616,3` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1486,6 +1620,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1493,2 +1622,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1496,2 +1624,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1499,1 +1626,4` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1501,3 +1631,2` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1505,2 +1634,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1508,2 +1636,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1511,1 +1638,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1513,3 +1640,4` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1517,1 +1645,8` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1520,2 +1655,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1523,3 +1657,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1527,3 +1659,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1531,1 +1661,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1533,2 +1663,4` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1536,3 +1668,1` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1542,2 +1672,2` (base): `Client > elicitation/create > CreateElicitationResponse`
- `-1545,2 +1675,1` (base): `Client > elicitation/create > CreateElicitationResponse` | `Client > mcp/message`
- `-1548,1 +1677,3` (base): `Client > mcp/message`
- `-1550,1 +1681,1` (base): `Client > mcp/message`
- `-1552,1 +1683,1` (base): `Client > mcp/message`
- `-1554,1 +1685,1` (base): `Client > mcp/message > MessageMcpRequest`
- `-1556,1 +1687,3` (base): `Client > mcp/message > MessageMcpRequest`
- `-1558,1 +1691,4` (base): `Client > mcp/message > MessageMcpRequest`
- `-1564,9 +1700,7` (base): `Client > mcp/message > MessageMcpRequest`
- `-1574,6 +1708,2` (base): `Client > mcp/message > MessageMcpRequest`
- `-1581,6 +1711,2` (base): `Client > mcp/message > MessageMcpRequest`
- `-1589,7 +1715,1` (base): `Client > mcp/message > MessageMcpResponse`
- `-1597,4 +1717,1` (base): `Client > mcp/message > MessageMcpResponse`
- `-1602,1 +1719,1` (base): `Client > mcp/message > MessageMcpResponse`
- `-1604,2 +1721,1` (base): `Client > mcp/message > MessageMcpResponse`
- `-1607,1 +1723,4` (base): `Client > mcp/message > MessageMcpResponse`
- `-1609,6 +1728,1` (base): `Client > mcp/message > MessageMcpResponse`
- `-1616,1 +1729,0` (base): `Client > mcp/message > MessageMcpResponse`
- `-1619,2 +1732,1` (base): `Client > mcp/message > MessageMcpResponse`
- `-1622,1 +1734,1` (base): `Client > mcp/message > MessageMcpResponse`
- `-1624,6 +1736,3` (base): `Client > mcp/message > MessageMcpResponse`
- `-1631,2 +1740,2` (base): `Client > mcp/message > MessageMcpResponse`
- `-1634,2 +1743,1` (base): `Client > mcp/message > MessageMcpResponse` | `Client > session/request_permission`
- `-1637,1 +1745,1` (base): `Client > session/request_permission`
- `-1639,3 +1747,1` (base): `Client > session/request_permission`
- `-1643,2 +1749,1` (base): `Client > session/request_permission`
- `-1646,1 +1751,1` (base): `Client > session/request_permission`
- `-1648,1 +1753,1` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1650,1 +1755,1` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1652,1 +1757,1` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1654,1 +1759,3` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1662,2 +1769,2` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1668,2 +1775,2` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1671,3 +1778,3` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1676,3 +1783,659` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1680,2 +2443,2` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1683,2 +2446,2` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1686,1 +2449,3` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1689,2 +2453,0` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1692,2 +2455,35` (base): `Client > session/request_permission > RequestPermissionRequest`
- `-1695,0 +2492,5` (target): `Proxy > proxy/successor > ProxySuccessorRequest`
- `-1697,1 +2498,3` (base): `Client > session/request_permission > RequestPermissionResponse`
- `-1699,1 +2502,47` (base): `Client > session/request_permission > RequestPermissionResponse`
- `-1707,2 +2556,2` (base): `Client > session/request_permission > RequestPermissionResponse`
- `-1713,2 +2562,3` (base): `Client > session/request_permission > RequestPermissionResponse`
- `-1717,2 +2567,1` (base): `Client > session/request_permission > RequestPermissionResponse` | `Client > session/update`
- `-1720,1 +2569,1` (base): `Client > session/update`
- `-1722,3 +2571,2` (base): `Client > session/update`
- `-1726,4 +2574,195` (base): `Client > session/update`
- `-1731,1 +2770,1` (base): `Client > session/update`
- `-1733,1 +2772,4` (base): `Client > session/update > UpdateSessionNotification`
- `-1735,1 +2777,1` (base): `Client > session/update > UpdateSessionNotification`
- `-1737,1 +2779,1` (base): `Client > session/update > UpdateSessionNotification`
- `-1739,1 +2781,1` (base): `Client > session/update > UpdateSessionNotification`
- `-1747,2 +2789,2` (base): `Client > session/update > UpdateSessionNotification`
- `-1753,20 +2795,2` (base): `Client > session/update > UpdateSessionNotification` | `Protocol Level` | `Protocol Level > $/cancel_request`
- `-1774,1 +2798,1` (base): `Protocol Level > $/cancel_request`
- `-1776,1 +2800,3` (base): `Protocol Level > $/cancel_request`
- `-1778,1 +2804,1` (base): `Protocol Level > $/cancel_request`
- `-1780,3 +2806,4` (base): `Protocol Level > $/cancel_request`
- `-1784,2 +2811,1` (base): `Protocol Level > $/cancel_request`
- `-1787,1 +2813,1` (base): `Protocol Level > $/cancel_request`
- `-1789,1 +2815,1` (base): `Protocol Level > $/cancel_request > CancelRequestNotification`
- `-1791,1 +2817,2` (base): `Protocol Level > $/cancel_request > CancelRequestNotification`
- `-1793,1 +2820,3` (base): `Protocol Level > $/cancel_request > CancelRequestNotification`
- `-1801,2 +2830,2` (base): `Protocol Level > $/cancel_request > CancelRequestNotification`
- `-1807,2 +2836,7` (base): `Protocol Level > $/cancel_request > CancelRequestNotification`
- `-1809,0 +2844,2` (target): `AuthAccount`
- `-1811,1 +2847,1` (base): `AbsolutePath`
- `-1813,1 +2849,7` (base): `AbsolutePath`
- `-1815,1 +2857,1` (base): `AbsolutePath`
- `-1817,1 +2859,3` (base): `AgentAuthCapabilities`
- `-1819,1 +2863,1` (base): `AgentAuthCapabilities`
- `-1821,3 +2865,1` (base): `AgentAuthCapabilities`
- `-1825,1 +2867,1` (base): `AgentAuthCapabilities`
- `-1827,1 +2869,11` (base): `AgentAuthCapabilities`
- `-1831,2 +2883,2` (base): `AgentAuthCapabilities`
- `-1836,0 +2889,5` (target): `AuthMethod`
- `-1838,1 +2895,1` (base): `AgentCapabilities`
- `-1840,1 +2897,15` (base): `AgentCapabilities`
- `-1842,2 +2913,2` (base): `AgentCapabilities`
- `-1845,1 +2916,2` (base): `AgentCapabilities`
- `-1847,1 +2919,1` (base): `AgentCapabilities`
- `-1849,1 +2921,1` (base): `AgentCapabilities`
- `-1853,2 +2925,2` (base): `AgentCapabilities`
- `-1859,2 +2931,2` (base): `AgentCapabilities`
- `-1862,4 +2934,1` (base): `AgentCapabilities`
- `-1868,2 +2937,9` (base): `AgentCapabilities`
- `-1871,1 +2947,2` (base): `AgentCapabilities`
- `-1873,1 +2950,2` (base): `AgentCapabilities`
- `-1875,2 +2953,9` (base): `AgentCapabilities`
- `-1877,0 +2963,2` (target): `AuthMethod`
- `-1879,2 +2966,5` (base): `AgentCapabilities`
- `-1882,5 +2972,3` (base): `AgentCapabilities`
- `-1890,1 +2978,2` (base): `AgentMessage`
- `-1892,1 +2981,1` (base): `AgentMessage`
- `-1894,5 +2983,1` (base): `AgentMessage`
- `-1900,5 +2985,1` (base): `AgentMessage`
- `-1912,5 +2993,2` (base): `AgentMessage`
- `-1918,1 +2996,1` (base): `AgentMessage`
- `-1921,2 +2999,5` (base): `AgentMessage`
- `-1924,2 +3005,5` (base): `AgentMessage`
- `-1928,1 +3012,1` (base): `AgentThought`
- `-1930,1 +3014,1` (base): `AgentThought`
- `-1932,5 +3016,1` (base): `AgentThought`
- `-1938,5 +3018,9` (base): `AgentThought`
- `-1950,5 +3034,2` (base): `AgentThought`
- `-1956,1 +3037,1` (base): `AgentThought`
- `-1959,5 +3040,2` (base): `AgentThought`
- `-1964,0 +3043,2` (target): `AuthMethodTerminal`
- `-1966,5 +3046,1` (base): `Annotations`
- `-1972,1 +3048,12` (base): `Annotations`
- `-1974,4 +3061,1` (base): `Annotations`
- `-1979,1 +3063,1` (base): `Annotations`
- `-1981,6 +3065,1` (base): `Annotations`
- `-1988,1 +3067,1` (base): `Annotations`
- `-1990,1 +3069,1` (base): `Annotations`
- `-1991,0 +3071,2` (target): `AuthState`
- `-1993,7 +3073,0` (base): `Annotations`
- `-2000,0 +3075,3` (target): `AuthState`
- `-2003,5 +3080,3` (base): `AudioContent`
- `-2009,1 +3084,3` (base): `AudioContent`
- `-2011,4 +3088,2` (base): `AudioContent`
- `-2016,1 +3091,3` (base): `AudioContent`
- `-2019,5 +3095,0` (base): `AudioContent`
- `-2025,1 +3097,1` (base): `AudioContent`
- `-2027,4 +3099,1` (base): `AudioContent`
- `-2032,1 +3101,1` (base): `AuthCapabilities`
- `-2034,1 +3103,1` (base): `AuthCapabilities`
- `-2036,3 +3105,1` (base): `AuthCapabilities`
- `-2046,2 +3113,2` (base): `AuthCapabilities`
- `-2051,9 +3117,0` (base): `AuthCapabilities`
- `-2062,1 +3120,1` (base): `AuthMethod`
- `-2064,1 +3122,1` (base): `AuthMethod`
- `-2070,3 +3128,2` (base): `AuthMethod`
- `-2078,2 +3135,2` (base): `AuthMethod`
- `-2084,2 +3141,2` (base): `AuthMethod`
- `-2087,2 +3144,5` (base): `AuthMethod`
- `-2090,4 +3150,5` (base): `AuthMethod`
- `-2095,2 +3156,23` (base): `AuthMethod`
- `-2099,1 +3181,2` (base): `AuthMethod`
- `-2102,1 +3185,6` (base): `AuthMethod`
- `-2108,2 +3196,1` (base): `AuthMethod`
- `-2111,1 +3198,6` (base): `AuthMethod`
- `-2117,2 +3209,2` (base): `AuthMethod`
- `-2123,8 +3215,2` (base): `AuthMethod`
- `-2133,1 +3219,1` (base): `AuthMethod`
- `-2140,1 +3226,1` (base): `AuthMethod`
- `-2146,3 +3232,4` (base): `AuthMethod`
- `-2152,17 +3238,0` (base): `AuthMethod`
- `-2170,1 +3240,1` (base): `AuthMethod`
- `-2181,3 +3251,1` (base): `AuthMethodAgent`
- `-2185,1 +3253,1` (base): `AuthMethodAgent`
- `-2193,2 +3261,2` (base): `AuthMethodAgent`
- `-2199,2 +3267,2` (base): `AuthMethodAgent`
- `-2202,2 +3270,20` (base): `AuthMethodAgent`
- `-2205,2 +3291,2` (base): `AuthMethodAgent`
- `-2209,1 +3295,1` (base): `AuthMethodId`
- `-2211,1 +3297,1` (base): `AuthMethodId`
- `-2213,1 +3299,1` (base): `AuthMethodId`
- `-2215,1 +3301,1` (base): `AuthMethodTerminal`
- `-2217,1 +3303,4` (base): `AuthMethodTerminal`
- `-2219,5 +3308,10` (base): `AuthMethodTerminal`
- `-2231,2 +3325,2` (base): `AuthMethodTerminal`
- `-2237,5 +3331,2` (base): `AuthMethodTerminal`
- `-2243,4 +3334,27` (base): `AuthMethodTerminal`
- `-2248,2 +3362,2` (base): `AuthMethodTerminal`
- `-2251,2 +3365,2` (base): `AuthMethodTerminal`
- `-2255,3 +3369,2` (base): `AvailableCommand`
- `-2259,1 +3372,4` (base): `AvailableCommand`
- `-2261,1 +3377,1` (base): `AvailableCommand`
- `-2265,2 +3381,2` (base): `AvailableCommand`
- `-2271,5 +3387,2` (base): `AvailableCommand`
- `-2277,2 +3390,2` (base): `AvailableCommand`
- `-2281,1 +3394,2` (base): `AvailableCommandInput`
- `-2283,1 +3397,2` (base): `AvailableCommandInput`
- `-2285,1 +3400,1` (base): `AvailableCommandInput`
- `-2287,2 +3402,2` (base): `AvailableCommandInput`
- `-2294,2 +3409,2` (base): `AvailableCommandInput`
- `-2300,2 +3415,2` (base): `AvailableCommandInput`
- `-2304,1 +3419,1` (base): `AvailableCommandInput`
- `-2311,1 +3426,1` (base): `AvailableCommandInput`
- `-2317,4 +3432,2` (base): `AvailableCommandInput`
- `-2325,1 +3438,1` (base): `AvailableCommandInput`
- `-2336,20 +3448,0` (base): `AvailableCommandsUpdate`
- `-2366,2 +3459,2` (base): `BlobResourceContents`
- `-2379,0 +3473,3` (target): `BlobResourceContents`
- `-2398,4 +3494,2` (base): `BooleanPropertySchema`
- `-2424,0 +3519,47` (target): `CancelledPermissionOutcome` | `ClientAuthCapabilities`
- `-2440,2 +3581,2` (base): `ClientCapabilities`
- `-2446,1 +3587,1` (base): `ClientCapabilities`
- `-2451,1 +3592,1` (base): `ClientCapabilities`
- `-2459,1 +3600,1` (base): `ClientCapabilities`
- `-2463,0 +3605,34` (target): `Command`
- `-2474,2 +3649,2` (base): `CommandPermissionSubject`
- `-2538,2 +3713,8` (base): `CompactionSummaryChunk`
- `-2541,5 +3722,1` (base): `CompactionSummaryChunk`
- `-2548,5 +3725,1` (base): `CompactionSummaryChunk`
- `-2572,1 +3745,1` (base): `CompactionUpdate`
- `-2576,1 +3749,1` (base): `CompactionUpdate`
- `-2604,2 +3777,2` (base): `ConfigOptionUpdate`
- `-2624,2 +3797,2` (base): `Content`
- `-2638,3 +3810,0` (base): `ContentBlock`
- `-2648,2 +3818,2` (base): `ContentBlock`
- `-2659,1 +3829,2` (base): `ContentBlock`
- `-2665,2 +3836,2` (base): `ContentBlock`
- `-2672,0 +3844,3` (target): `ContentBlock`
- `-2693,2 +3867,2` (base): `ContentBlock`
- `-2700,0 +3875,3` (target): `ContentBlock`
- `-2716,0 +3894,2` (target): `ContentBlock`
- `-2733,2 +3912,2` (base): `ContentBlock`
- `-2740,0 +3920,3` (target): `ContentBlock`
- `-2759,1 +3941,1` (base): `ContentBlock`
- `-2767,2 +3949,2` (base): `ContentBlock`
- `-2774,0 +3957,3` (target): `ContentBlock`
- `-2777,0 +3963,3` (target): `ContentBlock`
- `-2780,0 +3969,3` (target): `ContentBlock`
- `-2783,0 +3975,3` (target): `ContentBlock`
- `-2789,0 +3984,5` (target): `ContentBlock`
- `-2792,0 +3992,3` (target): `ContentBlock`
- `-2818,2 +4020,2` (base): `ContentBlock`
- `-2825,0 +4028,3` (target): `ContentBlock`
- `-2846,1 +4051,3` (base): `ContentBlock`
- `-2872,2 +4079,3` (base): `ContentChunk`
- `-2885,1 +4093,1` (base): `ContentChunk`
- `-2899,2 +4107,2` (base): `Cost`
- `-2909,4 +4117,2` (base): `Cost`
- `-2932,2 +4138,2` (base): `Diff`
- `-2947,2 +4153,2` (base): `Diff`
- `-2965,2 +4171,2` (base): `DiffChange`
- `-2972,1 +4178,1` (base): `DiffChange`
- `-2974,1 +4180,1` (base): `DiffChange`
- `-2978,1 +4184,1` (base): `DiffChange`
- `-2980,1 +4186,1` (base): `DiffChange`
- `-3155,5 +4361,9` (base): `DiffPatch`
- `-3181,1 +4391,2` (base): `DiffPatchFormat`
- `-3242,1 +4453,1` (base): `ElicitationAcceptAction`
- `-3243,0 +4455,3` (target): `ElicitationAcceptAction`
- `-3256,4 +4470,2` (base): `ElicitationCapabilities`
- `-3274,1 +4486,1` (base): `ElicitationCapabilities`
- `-3304,0 +4517,8` (target): `ElicitationContentValue`
- `-3317,4 +4537,2` (base): `ElicitationFormCapabilities`
- `-3374,1 +4592,1` (base): `ElicitationFormMode`
- `-3391,2 +4609,2` (base): `ElicitationPropertySchema`
- `-3403,4 +4621,2` (base): `ElicitationPropertySchema`
- `-3458,1 +4674,1` (base): `ElicitationPropertySchema`
- `-3485,4 +4701,2` (base): `ElicitationPropertySchema`
- `-3537,4 +4751,2` (base): `ElicitationPropertySchema`
- `-3589,4 +4801,2` (base): `ElicitationPropertySchema`
- `-3629,4 +4839,2` (base): `ElicitationPropertySchema`
- `-3720,1 +4928,1` (base): `ElicitationRequestScope`
- `-3736,4 +4944,2` (base): `ElicitationSchema`
- `-3750,1 +4956,1` (base): `ElicitationSchema`
- `-3752,3 +4957,0` (base): `ElicitationSchema`
- `-3768,5 +4971,2` (base): `ElicitationSchema`
- `-3789,1 +4989,1` (base): `ElicitationSessionScope`
- `-3820,4 +5020,2` (base): `ElicitationUrlCapabilities`
- `-3879,1 +5077,1` (base): `ElicitationUrlMode`
- `-3895,2 +5093,2` (base): `EmbeddedResource`
- `-3902,0 +5101,3` (target): `EmbeddedResource`
- `-3921,2 +5122,2` (base): `EmbeddedResourceResource`
- `-3928,0 +5130,3` (target): `EmbeddedResourceResource`
- `-3950,2 +5154,2` (base): `EmbeddedResourceResource`
- `-3963,0 +5168,3` (target): `EmbeddedResourceResource`
- `-3985,4 +5192,2` (base): `EnumOption`
- `-4016,2 +5221,2` (base): `EnvVariable`
- `-4043,2 +5248,2` (base): `Error`
- `-4046,4 +5251,8` (base): `Error`
- `-4052,2 +5261,2` (base): `Error`
- `-4060,2 +5269,3` (base): `ErrorCode`
- `-4083,2 +5293,1` (base): `ErrorCode`
- `-4099,1 +5308,1` (base): `ErrorCode`
- `-4104,2 +5313,2` (base): `ErrorCode`
- `-4111,0 +5321,51` (target): `ErrorData`
- `-4123,1 +5383,1` (base): `ErrorStopReason`
- `-4130,1 +5390,1` (base): `ExtNotification`
- `-4146,1 +5406,1` (base): `ExtResponse`
- `-4162,2 +5422,2` (base): `HttpHeader`
- `-4182,0 +5443,8` (target): `Icon`
- `-4184,0 +5453,3` (target): `Icon`
- `-4192,0 +5464,2` (target): `Icon`
- `-4195,1 +5468,3` (base): `Icon`
- `-4201,0 +5477,3` (target): `Icon`
- `-4244,2 +5522,2` (base): `IdleStateUpdate`
- `-4248,0 +5527,11` (target): `IdleStateUpdate`
- `-4253,1 +5542,1` (base): `IdleStateUpdate`
- `-4265,1 +5554,1` (base): `IdleStateUpdate`
- `-4299,1 +5588,1` (base): `IdleStateUpdate`
- `-4311,3 +5600,1` (base): `IdleStateUpdate`
- `-4325,1 +5612,5` (base): `IdleStateUpdate`
- `-4345,1 +5636,1` (base): `IdleStateUpdate`
- `-4353,1 +5644,1` (base): `IdleStateUpdate`
- `-4405,2 +5696,2` (base): `ImageContent`
- `-4412,0 +5704,3` (target): `ImageContent`
- `-4425,0 +5720,2` (target): `ImageContent`
- `-4442,2 +5738,2` (base): `Implementation`
- `-4450,1 +5746,1` (base): `Implementation`
- `-4453,1 +5749,1` (base): `Implementation`
- `-4457,0 +5754,2` (target): `Implementation`
- `-4474,4 +5772,2` (base): `IntegerPropertySchema`
- `-4573,2 +5869,2` (base): `McpAcpCapabilities`
- `-4590,2 +5886,2` (base): `McpCapabilities`
- `-4601,1 +5897,1` (base): `McpCapabilities`
- `-4603,1 +5899,1` (base): `McpCapabilities`
- `-4608,1 +5904,1` (base): `McpCapabilities`
- `-4610,1 +5906,1` (base): `McpCapabilities`
- `-4615,1 +5911,1` (base): `McpCapabilities`
- `-4617,1 +5913,1` (base): `McpCapabilities`
- `-4628,2 +5924,2` (base): `McpError`
- `-4636,1 +5932,1` (base): `McpError`
- `-4639,1 +5935,1` (base): `McpError`
- `-4657,2 +5953,2` (base): `McpHttpCapabilities`
- `-4694,2 +5990,2` (base): `McpServer`
- `-4701,1 +5997,2` (base): `McpServer`
- `-4733,2 +6030,2` (base): `McpServer`
- `-4765,2 +6062,2` (base): `McpServer`
- `-4778,1 +6075,2` (base): `McpServer`
- `-4799,1 +6097,2` (base): `McpServer`
- `-4832,2 +6131,2` (base): `McpServerAcp`
- `-4872,2 +6171,2` (base): `McpServerHttp`
- `-4879,1 +6178,2` (base): `McpServerHttp`
- `-4901,2 +6201,2` (base): `McpServerStdio`
- `-4914,1 +6214,2` (base): `McpServerStdio`
- `-4932,2 +6233,2` (base): `McpStdioCapabilities`
- `-4968,4 +6269,2` (base): `MultiSelectItems`
- `-5005,0 +6305,2` (target): `MultiSelectItems`
- `-5010,4 +6311,2` (base): `MultiSelectItems`
- `-5035,4 +6334,2` (base): `MultiSelectPropertySchema`
- `-5089,1 +6386,1` (base): `Notice`
- `-5096,1 +6393,3` (base): `Notice`
- `-5098,1 +6397,1` (base): `Notice`
- `-5153,4 +6452,2` (base): `NumberPropertySchema`
- `-5202,2 +6499,2` (base): `PermissionOption`
- `-5215,1 +6512,1` (base): `PermissionOption`
- `-5271,2 +6568,2` (base): `PlanEntry`
- `-5367,2 +6664,2` (base): `PlanFile`
- `-5399,2 +6696,2` (base): `PlanItems`
- `-5430,2 +6727,2` (base): `PlanMarkdown`
- `-5457,2 +6754,2` (base): `PlanRemoved`
- `-5477,2 +6774,2` (base): `PlanUpdate`
- `-5500,2 +6797,2` (base): `PlanUpdateContent`
- `-5534,2 +6831,2` (base): `PlanUpdateContent`
- `-5567,2 +6864,2` (base): `PlanUpdateContent`
- `-5595,1 +6892,2` (base): `PlanUpdateContent`
- `-5626,2 +6924,2` (base): `PromptAudioCapabilities`
- `-5637,2 +6935,2` (base): `PromptCapabilities`
- `-5646,1 +6944,1` (base): `PromptCapabilities`
- `-5654,2 +6952,2` (base): `PromptCapabilities`
- `-5661,1 +6959,1` (base): `PromptCapabilities`
- `-5663,1 +6961,1` (base): `PromptCapabilities`
- `-5670,1 +6968,1` (base): `PromptCapabilities`
- `-5673,1 +6971,1` (base): `PromptCapabilities`
- `-5678,1 +6976,1` (base): `PromptCapabilities`
- `-5680,1 +6978,1` (base): `PromptCapabilities`
- `-5697,2 +6995,2` (base): `PromptEmbeddedContextCapabilities`
- `-5716,2 +7014,2` (base): `PromptImageCapabilities`
- `-5751,2 +7049,2` (base): `ProviderCurrentConfig`
- `-5791,2 +7089,2` (base): `ProviderInfo`
- `-5828,2 +7126,2` (base): `ProvidersCapabilities`
- `-5850,2 +7148,2` (base): `ReplayFrom`
- `-5877,8 +7174,0` (base): `ReplayFrom`
- `-5907,2 +7197,2` (base): `ReplayFromStart`
- `-5916,7 +7206,1` (base): `RequestId`
- `-5924,1 +7208,3` (base): `RequestId`
- `-5928,4 +7213,0` (base): `RequestId`
- `-5933,1 +7215,1` (base): `RequestId`
- `-5937,1 +7219,1` (base): `RequestId`
- `-5947,1 +7229,3` (base): `RequestPermissionOutcome`
- `-5949,4 +7233,4` (base): `RequestPermissionOutcome`
- `-5957,0 +7242,8` (target): `RequestPermissionOutcome`
- `-5967,0 +7260,3` (target): `RequestPermissionOutcome`
- `-5972,2 +7267,2` (base): `RequestPermissionOutcome`
- `-6025,5 +7320,9` (base): `RequestPermissionSubject`
- `-6030,0 +7330,5` (target): `RequestPermissionSubject`
- `-6046,2 +7350,2` (base): `RequestPermissionSubject`
- `-6114,2 +7418,2` (base): `RequiresActionStateUpdate`
- `-6118,0 +7423,11` (target): `RequiresActionStateUpdate`
- `-6123,1 +7438,1` (base): `ResourceLink`
- `-6131,2 +7446,2` (base): `ResourceLink`
- `-6138,0 +7454,3` (target): `ResourceLink`
- `-6141,0 +7460,3` (target): `ResourceLink`
- `-6144,0 +7466,3` (target): `ResourceLink`
- `-6147,0 +7472,3` (target): `ResourceLink`
- `-6153,0 +7481,5` (target): `ResourceLink`
- `-6156,0 +7489,3` (target): `ResourceLink`
- `-6198,2 +7533,2` (base): `RunningStateUpdate`
- `-6202,0 +7538,11` (target): `RunningStateUpdate`
- `-6215,2 +7561,2` (base): `SelectedPermissionOutcome`
- `-6230,2 +7576,2` (base): `SessionAdditionalDirectoriesCapabilities`
- `-6240,2 +7586,26` (base): `SessionAdditionalDirectoriesCapabilities`
- `-6246,0 +7617,34` (target): `SessionArchiveFilter`
- `-6255,1 +7659,1` (base): `SessionCancelCapabilities`
- `-6263,2 +7667,2` (base): `SessionCancelCapabilities`
- `-6290,2 +7694,2` (base): `SessionCapabilities`
- `-6299,1 +7703,1` (base): `SessionCapabilities`
- `-6305,0 +7710,12` (target): `SessionCapabilities`
- `-6310,1 +7726,1` (base): `SessionCapabilities`
- `-6321,1 +7737,1` (base): `SessionCapabilities`
- `-6328,1 +7744,1` (base): `SessionCapabilities`
- `-6335,1 +7751,1` (base): `SessionCapabilities`
- `-6340,1 +7756,1` (base): `SessionCapabilities`
- `-6345,1 +7761,4` (base): `SessionCapabilities`
- `-6347,1 +7766,5` (base): `SessionCapabilities`
- `-6349,0 +7773,14` (target): `SessionCapabilities`
- `-6386,2 +7823,2` (base): `SessionConfigOption`
- `-6393,0 +7831,3` (target): `SessionConfigOption`
- `-6399,0 +7840,3` (target): `SessionConfigOption`
- `-6417,1 +7860,1` (base): `SessionConfigOption`
- `-6424,1 +7867,2` (base): `SessionConfigOption`
- `-6457,1 +7901,1` (base): `SessionConfigOption`
- `-6525,1 +7969,1` (base): `SessionConfigSelect`
- `-6532,1 +7976,2` (base): `SessionConfigSelect`
- `-6545,2 +7990,2` (base): `SessionConfigSelectGroup`
- `-6558,1 +8003,1` (base): `SessionConfigSelectGroup`
- `-6571,2 +8016,2` (base): `SessionConfigSelectOption`
- `-6578,0 +8024,3` (target): `SessionConfigSelectOption`
- `-6619,2 +8067,2` (base): `SessionDeleteCapabilities`
- `-6642,2 +8090,2` (base): `SessionForkCapabilities`
- `-6653,2 +8101,2` (base): `SessionId`
- `-6670,2 +8118,2` (base): `SessionInfo`
- `-6682,0 +8131,11` (target): `SessionInfo`
- `-6691,0 +8151,3` (target): `SessionInfo`
- `-6695,0 +8158,2` (target): `SessionInfo`
- `-6705,1 +8169,1` (base): `SessionInfoUpdate`
- `-6717,1 +8181,1` (base): `SessionInfoUpdate`
- `-6721,1 +8185,1` (base): `SessionInfoUpdate`
- `-6756,1 +8220,1` (base): `SessionMessage`
- `-6760,1 +8224,1` (base): `SessionMessage`
- `-6766,1 +8230,1` (base): `SessionMessage`
- `-6770,0 +8235,8` (target): `SessionMessage`
- `-6773,1 +8245,12` (base): `SessionMessage`
- `-6776,1 +8259,4` (base): `SessionMessage`
- `-6786,0 +8273,3` (target): `SessionMessageChunk`
- `-6792,1 +8281,4` (base): `SessionMessageChunk`
- `-6794,1 +8286,1` (base): `SessionMessageChunk`
- `-6803,2 +8295,19` (base): `SessionMessageChunk`
- `-6806,2 +8315,2` (base): `SessionMessageChunk`
- `-6810,1 +8319,68` (base): `SessionSystemPromptCapabilities`
- `-6815,0 +8392,19` (target): `SessionStatusCapabilities` | `SessionSystemPromptCapabilities`
- `-6827,2 +8422,2` (base): `SessionSystemPromptCapabilities`
- `-6836,1 +8431,1` (base): `SessionSystemPromptCapabilities`
- `-6842,4 +8436,0` (base): `SessionSystemPromptModeCapabilities`
- `-6857,2 +8448,2` (base): `SessionSystemPromptModeCapabilities`
- `-6866,1 +8457,1` (base): `SessionSystemPromptModeCapabilities`
- `-6873,0 +8465,20` (target): `SessionSystemPromptOverrideCapabilities` | `SessionTitleCapabilities`
- `-6878,1 +8489,1` (base): `SessionSystemPromptOverrideCapabilities`
- `-6880,2 +8491,2` (base): `SessionSystemPromptOverrideCapabilities`
- `-6889,2 +8500,2` (base): `SessionSystemPromptOverrideCapabilities`
- `-6913,2 +8524,3` (base): `SessionUpdate`
- `-6926,1 +8538,1` (base): `SessionUpdate`
- `-6947,1 +8559,1` (base): `SessionUpdate`
- `-6951,1 +8563,1` (base): `SessionUpdate`
- `-6976,2 +8588,3` (base): `SessionUpdate`
- `-6989,1 +8602,1` (base): `SessionUpdate`
- `-7010,1 +8623,1` (base): `SessionUpdate`
- `-7014,1 +8627,1` (base): `SessionUpdate`
- `-7039,2 +8652,3` (base): `SessionUpdate`
- `-7052,1 +8666,1` (base): `SessionUpdate`
- `-7073,1 +8687,1` (base): `SessionUpdate`
- `-7077,1 +8691,1` (base): `SessionUpdate`
- `-7115,2 +8729,2` (base): `SessionUpdate`
- `-7119,0 +8734,11` (target): `SessionUpdate`
- `-7135,2 +8760,2` (base): `SessionUpdate`
- `-7139,0 +8765,11` (target): `SessionUpdate`
- `-7147,1 +8783,1` (base): `SessionUpdate`
- `-7159,1 +8795,1` (base): `SessionUpdate`
- `-7195,1 +8831,1` (base): `SessionUpdate`
- `-7207,3 +8843,1` (base): `SessionUpdate`
- `-7221,1 +8855,5` (base): `SessionUpdate`
- `-7241,1 +8879,1` (base): `SessionUpdate`
- `-7249,1 +8887,1` (base): `SessionUpdate`
- `-7300,2 +8938,2` (base): `SessionUpdate`
- `-7304,0 +8943,11` (target): `SessionUpdate`
- `-7323,4 +8972,18` (base): `SessionUpdate`
- `-7341,0 +9005,6` (target): `SessionUpdate`
- `-7365,2 +9034,3` (base): `SessionUpdate`
- `-7391,1 +9061,1` (base): `SessionUpdate`
- `-7395,1 +9065,1` (base): `SessionUpdate`
- `-7398,0 +9069,7` (target): `SessionUpdate`
- `-7405,0 +9083,4` (target): `SessionUpdate`
- `-7430,0 +9112,4` (target): `SessionUpdate`
- `-7433,0 +9119,4` (target): `SessionUpdate`
- `-7449,1 +9138,1` (base): `SessionUpdate`
- `-7453,1 +9142,1` (base): `SessionUpdate`
- `-7456,0 +9146,7` (target): `SessionUpdate`
- `-7471,0 +9168,7` (target): `SessionUpdate`
- `-7487,3 +9190,3` (base): `SessionUpdate`
- `-7518,2 +9221,2` (base): `SessionUpdate`
- `-7545,2 +9248,2` (base): `SessionUpdate`
- `-7568,2 +9271,2` (base): `SessionUpdate`
- `-7591,2 +9294,2` (base): `SessionUpdate`
- `-7614,1 +9317,1` (base): `SessionUpdate`
- `-7618,1 +9321,1` (base): `SessionUpdate`
- `-7646,2 +9349,2` (base): `SessionUpdate`
- `-7653,1 +9356,4` (base): `SessionUpdate`
- `-7683,1 +9389,3` (base): `SessionUpdate`
- `-7685,1 +9393,1` (base): `SessionUpdate`
- `-7717,1 +9425,1` (base): `SessionUpdate`
- `-7721,1 +9429,1` (base): `SessionUpdate`
- `-7750,2 +9458,8` (base): `SessionUpdate`
- `-7753,5 +9467,1` (base): `SessionUpdate`
- `-7760,5 +9470,1` (base): `SessionUpdate`
- `-7786,1 +9492,1` (base): `SessionUpdate`
- `-7790,1 +9496,1` (base): `SessionUpdate`
- `-7793,0 +9500,9` (target): `SessionUpdate`
- `-7800,0 +9516,8` (target): `SessionUpdate`
- `-7805,1 +9528,1` (base): `SessionUpdate`
- `-7818,1 +9541,1` (base): `SessionUpdate`
- `-7826,1 +9549,1` (base): `SessionUpdate`
- `-7846,1 +9569,1` (base): `SessionUpdate`
- `-7850,1 +9573,1` (base): `SessionUpdate`
- `-7856,1 +9579,1` (base): `SessionUpdate`
- `-7860,0 +9584,8` (target): `SessionUpdate`
- `-7863,1 +9594,12` (base): `SessionUpdate`
- `-7866,1 +9608,4` (base): `SessionUpdate`
- `-7885,1 +9630,4` (base): `SessionUpdate`
- `-7887,1 +9635,1` (base): `SessionUpdate`
- `-7896,6 +9643,0` (base): `SessionUpdate`
- `-7986,2 +9728,2` (base): `StateUpdate`
- `-7990,0 +9733,11` (target): `StateUpdate`
- `-8006,2 +9759,2` (base): `StateUpdate`
- `-8010,0 +9764,11` (target): `StateUpdate`
- `-8018,1 +9782,1` (base): `StateUpdate`
- `-8030,1 +9794,1` (base): `StateUpdate`
- `-8066,1 +9830,1` (base): `StateUpdate`
- `-8078,3 +9842,1` (base): `StateUpdate`
- `-8092,1 +9854,5` (base): `StateUpdate`
- `-8112,1 +9878,1` (base): `StateUpdate`
- `-8120,1 +9886,1` (base): `StateUpdate`
- `-8171,2 +9937,2` (base): `StateUpdate`
- `-8175,0 +9942,11` (target): `StateUpdate`
- `-8194,4 +9971,18` (base): `StateUpdate`
- `-8212,0 +10004,6` (target): `StateUpdate`
- `-8267,4 +10064,2` (base): `StringMultiSelectItems`
- `-8292,4 +10087,2` (base): `StringPropertySchema`
- `-8347,1 +10140,1` (base): `StringPropertySchema`
- `-8369,1 +10162,1` (base): `SubagentSessionCapabilities`
- `-8378,2 +10171,5` (base): `SubagentSessionCapabilities`
- `-8383,1 +10179,1` (base): `SubagentSessionCapabilities`
- `-8398,1 +10194,1` (base): `SubagentUpdate`
- `-8401,1 +10197,1` (base): `SubagentUpdate`
- `-8403,1 +10199,1` (base): `SubagentUpdate`
- `-8406,1 +10202,1` (base): `SubagentUpdate`
- `-8411,1 +10207,1` (base): `SubagentUpdate`
- `-8413,0 +10210,2` (target): `SubagentUpdate`
- `-8416,1 +10214,1` (base): `SubagentUpdate`
- `-8430,1 +10228,1` (base): `SubagentUpdate`
- `-8434,1 +10232,1` (base): `SubagentUpdate`
- `-8437,0 +10236,9` (target): `SubagentUpdate`
- `-8444,0 +10252,8` (target): `SubagentUpdate`
- `-8449,1 +10264,1` (base): `SubagentUpdate`
- `-8459,1 +10274,1` (base): `SubagentUpdate`
- `-8467,1 +10282,1` (base): `SubagentUpdate`
- `-8474,4 +10288,0` (base): `SystemPrompt`
- `-8483,1 +10294,1` (base): `SystemPrompt`
- `-8491,2 +10302,2` (base): `SystemPrompt`
- `-8500,1 +10311,1` (base): `SystemPrompt`
- `-8503,2 +10314,4` (base): `SystemPrompt`
- `-8510,4 +10323,2` (base): `SystemPrompt`
- `-8519,4 +10329,0` (base): `SystemPromptMode`
- `-8525,1 +10332,1` (base): `SystemPromptMode`
- `-8567,1 +10374,1` (base): `Terminal`
- `-8575,3 +10382,2` (base): `Terminal`
- `-8600,2 +10406,43` (base): `TerminalAuthCapabilities`
- `-8604,0 +10452,7` (target): `TerminalCapabilities`
- `-8620,3 +10474,2` (base): `TerminalExitStatus`
- `-8628,4 +10481,2` (base): `TerminalExitStatus`
- `-8658,3 +10509,2` (base): `TerminalOutput`
- `-8682,3 +10532,3` (base): `TerminalOutputChunk`
- `-8698,0 +10549,35` (target): `TerminalSize`
- `-8703,1 +10588,1` (base): `TerminalUpdate`
- `-8715,1 +10600,1` (base): `TerminalUpdate`
- `-8719,1 +10604,1` (base): `TerminalUpdate`
- `-8722,0 +10608,7` (target): `TerminalUpdate`
- `-8734,0 +10627,7` (target): `TerminalUpdate`
- `-8750,2 +10649,2` (base): `TextCommandInput`
- `-8770,2 +10669,2` (base): `TextContent`
- `-8777,0 +10677,3` (target): `TextContent`
- `-8793,2 +10695,2` (base): `TextResourceContents`
- `-8800,0 +10703,3` (target): `TextResourceContents`
- `-8822,4 +10727,2` (base): `TitledMultiSelectItems`
- `-8833,0 +10737,48` (target): `ToolCallCancelCapabilities` | `ToolCallCapabilities`
- `-8852,2 +10803,2` (base): `ToolCallContent`
- `-8875,2 +10826,2` (base): `ToolCallContent`
- `-8890,2 +10841,2` (base): `ToolCallContent`
- `-8908,3 +10859,2` (base): `ToolCallContent`
- `-8924,0 +10875,27` (target): `ToolCallContent`
- `-8955,3 +10932,3` (base): `ToolCallContentChunk`
- `-8965,2 +10942,3` (base): `ToolCallContentChunk`
- `-8999,2 +10977,2` (base): `ToolCallLocation`
- `-9006,1 +10984,2` (base): `ToolCallLocation`
- `-9008,1 +10987,1` (base): `ToolCallLocation`
- `-9023,5 +11002,9` (base): `ToolCallPermissionSubject`
- `-9028,0 +11012,5` (target): `ToolCallPermissionSubject`
- `-9042,2 +11030,2` (base): `ToolCallStatus`
- `-9049,0 +11038,5` (target): `ToolCallStatus`
- `-9068,0 +11062,2` (target): `ToolCallStatus`
- `-9078,1 +11073,1` (base): `ToolCallUpdate`
- `-9084,1 +11079,1` (base): `ToolCallUpdate`
- `-9094,1 +11089,1` (base): `ToolCallUpdate`
- `-9098,1 +11093,1` (base): `ToolCallUpdate`
- `-9101,0 +11097,7` (target): `ToolCallUpdate`
- `-9108,0 +11111,4` (target): `ToolCallUpdate`
- `-9130,0 +11137,4` (target): `ToolCallUpdate`
- `-9133,0 +11144,4` (target): `ToolCallUpdate`
- `-9146,1 +11160,1` (base): `ToolKind`
- `-9183,1 +11197,3` (base): `ToolKind`
- `-9195,1 +11211,1` (base): `ToolKind`
- `-9213,1 +11229,31` (base): `UnknownStateUpdate`
- `-9219,4 +11265,13` (base): `UnknownStateUpdate`
- `-9231,1 +11286,1` (base): `Usage`
- `-9239,2 +11294,2` (base): `Usage`
- `-9246,1 +11301,3` (base): `Usage`
- `-9252,1 +11309,3` (base): `Usage`
- `-9258,1 +11317,1` (base): `Usage`
- `-9264,1 +11323,1` (base): `Usage`
- `-9270,1 +11329,3` (base): `Usage`
- `-9276,1 +11337,1` (base): `Usage`
- `-9292,2 +11353,2` (base): `UsageUpdate`
- `-9299,1 +11360,4` (base): `UsageUpdate`
- `-9318,1 +11382,1` (base): `UserMessage`
- `-9321,2 +11385,2` (base): `UserMessage`
- `-9336,1 +11400,1` (base): `UserMessage`
- `-9340,1 +11404,1` (base): `UserMessage`

### `docs/protocol/v2/draft/security.mdx` (added)

- `-0,0 +1,81` (target): `(intro)` | `Trust Model` | `Rendering Agent content` | `URIs and remote resources` | `Credentials` | `Prompt injection` | `Intermediaries` | `Transports` | `Feature guidance` | `Residual risk` | `Unstable features`

### `docs/protocol/v2/draft/session-config-options.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-8,1 +8,1` (base): `Initial State`
- `-87,1 +87,1` (base): `Initial State`
- `-93,1 +93,1` (base): `Initial State > ConfigOption`
- `-107,1 +107,1` (base): `Initial State > ConfigOption`
- `-112,1 +112,1` (base): `Initial State > ConfigOption`
- `-121,1 +121,4` (base): `Initial State > ConfigOption`
- `-124,1 +127,6` (base): `Initial State > ConfigOption`
- `-127,1 +135,1` (base): `Initial State > ConfigOptionValue`
- `-141,1 +149,1` (base): `Initial State > Grouped Select Options`
- `-144,3 +152,3` (base): `Initial State > Grouped Select Options`
- `-166,1 +174,1` (base): `Initial State > Boolean Config Options`
- `-180,1 +188,1` (base): `Option Categories`
- `-189,1 +197,1` (base): `Option Categories`
- `-202,1 +210,1` (base): `Option Ordering`
- `-212,1 +220,1` (base): `Default Values and Graceful Degradation`
- `-214,1 +222,1` (base): `Default Values and Graceful Degradation`
- `-220,1 +228,1` (base): `Default Values and Graceful Degradation`
- `-222,1 +230,1` (base): `Setting a Config Option`
- `-225,0 +234,4` (target): `Setting a config option`
- `-258,3 +270,3` (base): `Setting a Config Option > From the Client`
- `-289,0 +302,2` (target): `Setting a config option > From the Client`
- `-295,1 +309,2` (base): `Setting a Config Option > From the Client`
- `-299,1 +314,2` (base): `Setting a Config Option > From the Client`
- `-305,0 +322,1` (target): `Setting a config option > From the Client`
- `-311,1 +328,2` (base): `Setting a Config Option > From the Client`
- `-315,1 +333,2` (base): `Setting a Config Option > From the Client`
- `-317,0 +337,24` (target): `Setting a config option > From the Client`
- `-325,4 +368,3` (base): `Setting a Config Option > From the Client`
- `-333,1 +375,5` (base): `Setting a Config Option > From the Agent`
- `-346,0 +393,2` (target): `Setting a config option > From the Agent`
- `-352,1 +400,2` (base): `Setting a Config Option > From the Agent`
- `-356,1 +405,2` (base): `Setting a Config Option > From the Agent`
- `-362,0 +413,1` (target): `Setting a config option > From the Agent`
- `-368,1 +419,2` (base): `Setting a Config Option > From the Agent`
- `-372,1 +424,19` (base): `Setting a Config Option > From the Agent`
- `-374,0 +445,7` (target): `Setting a config option > From the Agent`
- `-384,1 +461,1` (base): `Setting a Config Option > From the Agent`

### `docs/protocol/v2/draft/session-delete.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-33,1 +33,1` (base): `Checking Support`
- `-59,1 +59,1` (base): `Deleting a Session`
- `-91,0 +92,1` (target): `Semantics`
- `-93,2 +94,2` (base): `Semantics`

### `docs/protocol/v2/draft/session-list.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-8,1 +8,1` (base): `(intro)`
- `-10,1 +10,1` (base): `(intro)`
- `-45,1 +45,1` (base): `Listing Sessions`
- `-64,2 +64,5` (base): `Listing Sessions`
- `-87,2 +90,2` (base): `Listing Sessions`
- `-120,4 +123,3` (base): `Listing Sessions`
- `-142,1 +144,2` (base): `Listing Sessions`
- `-151,3 +154,4` (base): `Pagination`
- `-156,1 +160,1` (base): `Updating Session Metadata`
- `-158,1 +162,4` (base): `Updating Session Metadata`
- `-170,2 +177,2` (base): `Updating Session Metadata`
- `-178,1 +185,1` (base): `Updating Session Metadata`
- `-189,1 +196,1` (base): `Updating Session Metadata`
- `-200,1 +207,2` (base): `Interaction with Other Session Methods`
- `-202,1 +210,3` (base): `Interaction with Other Session Methods`
- `-206,0 +217,36` (target): `Interaction with other session methods` | `Archived sessions (unstable)`

### `docs/protocol/v2/draft/session-setup.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-10,1 +10,1` (base): `(intro)`
- `-40,1 +40,1` (base): `(intro)`
- `-45,1 +45,13` (base): `Creating a Session`
- `-84,1 +96,1` (base): `Initial Session State`
- `-90,0 +103,2` (target): `Initial session state`
- `-94,1 +108,1` (base): `Initial Session State`
- `-112,0 +127,1` (target): `Initial session state`
- `-121,1 +136,1` (base): `Initial Session State`
- `-123,1 +138,1` (base): `Initial Session State`
- `-127,1 +142,1` (base): `Resuming Sessions`
- `-129,2 +144,2` (base): `Resuming Sessions`
- `-167,1 +182,1` (base): `Resuming Sessions`
- `-169,1 +184,1` (base): `Resuming Sessions`
- `-194,2 +209,1` (base): `Resuming Sessions`
- `-202,0 +217,16` (target): `Resuming sessions > Replay contents`
- `-206,10 +236,1` (base): `Resuming Sessions`
- `-265,1 +286,1` (base): `Resuming Sessions`
- `-268,6 +289,5` (base): `Resuming Sessions`
- `-276,1 +296,1` (base): `Resuming Sessions`
- `-283,1 +303,1` (base): `Resuming Sessions`
- `-313,1 +333,1` (base): `Resuming Sessions`
- `-317,1 +337,1` (base): `Resuming Sessions > Current-State Synchronization`
- `-325,0 +346,2` (target): `Resuming sessions > Current-state synchronization`
- `-336,1 +358,6` (base): `Closing Active Sessions`
- `-338,2 +365,4` (base): `Closing Active Sessions`
- `-362,1 +391,1` (base): `Closing Active Sessions`
- `-366,1 +395,1` (base): `Closing Active Sessions`
- `-378,2 +407,4` (base): `Closing Active Sessions`
- `-381,1 +412,1` (base): `Additional Workspace Roots`
- `-385,2 +416,1` (base): `Additional Workspace Roots`
- `-409,1 +439,1` (base): `Additional Workspace Roots`
- `-413,1 +443,3` (base): `System Prompt (unstable)`
- `-443,1 +475,1` (base): `System Prompt (unstable)`
- `-445,0 +478,1` (target): `System prompt`
- `-483,1 +516,1` (base): `Session ID`
- `-487,1 +520,1` (base): `Working Directory`
- `-491,1 +524,1` (base): `Working Directory`
- `-495,0 +529,2` (target): `Working directory`
- `-498,1 +533,9` (base): `MCP Servers`
- `-502,1 +545,5` (base): `MCP Servers`
- `-504,1 +551,1` (base): `MCP Servers > Transport Types`
- `-506,1 +553,1` (base): `MCP Servers > Transport Types`
- `-508,1 +555,1` (base): `MCP Servers > Transport Types > Stdio Transport`
- `-534,1 +581,1` (base): `MCP Servers > Transport Types > Stdio Transport`
- `-537,1 +584,1` (base): `MCP Servers > Transport Types > Stdio Transport`
- `-560,1 +607,3` (base): `MCP Servers > Transport Types > HTTP Transport`
- `-577,2 +626,1` (base): `MCP Servers > Transport Types > HTTP Transport`
- `-581,1 +629,1` (base): `MCP Servers > Transport Types > HTTP Transport`
- `-584,1 +632,1` (base): `MCP Servers > Transport Types > HTTP Transport`
- `-601,4 +648,0` (base): `MCP Servers > Transport Types > HTTP Transport`
- `-610,1 +654,1` (base): `MCP Servers > Checking Transport Support`
- `-641,1 +685,1` (base): `MCP Servers > Checking Transport Support`
- `-643,0 +688,10` (target): `MCP servers > Checking transport support` | `MCP servers > Security`

### `docs/protocol/v2/draft/slash-commands.mdx` (modified)

- `-12,1 +12,1` (base): `Advertising commands > Initial commands`
- `-23,0 +24,1` (target): `Advertising commands > Initial commands`
- `-37,3 +38,3` (base): `Advertising commands > Initial commands`
- `-42,1 +43,1` (base): `Advertising commands > Initial commands`
- `-57,0 +59,1` (target): `Advertising commands > Notifications`
- `-65,0 +68,1` (target): `Advertising commands > Notifications`
- `-69,0 +73,1` (target): `Advertising commands > Notifications`
- `-86,0 +91,6` (target): `Advertising commands > AvailableCommand`
- `-88,1 +98,2` (base): `Advertising commands > AvailableCommand`
- `-98,0 +110,2` (target): `Advertising commands > AvailableCommand`
- `-107,1 +120,1` (base): `Advertising commands > AvailableCommandInput`
- `-111,1 +124,1` (base): `Dynamic updates`
- `-134,1 +147,1` (base): `Running commands`
- `-140,1 +153,1` (base): `Running commands`

### `docs/protocol/v2/draft/tool-calls.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`
- `-8,1 +8,1` (base): `(intro)`
- `-12,3 +12,2` (base): `(intro)`
- `-49,1 +48,1` (base): `Reporting`
- `-70,1 +69,1` (base): `Reporting`
- `-77,1 +76,1` (base): `Reporting`
- `-105,4 +104,7` (base): `Reporting`
- `-116,3 +117,0` (base): `Reporting`
- `-125,0 +125,2` (target): `Reporting`
- `-156,1 +157,1` (base): `Streaming Content`
- `-197,1 +198,8` (base): `Streaming Content`
- `-199,1 +207,1` (base): `Requesting Permission`
- `-256,2 +264,2` (base): `Requesting Permission`
- `-259,0 +268,7` (target): `Requesting permission`
- `-289,1 +304,1` (base): `Requesting Permission`
- `-292,1 +307,1` (base): `Requesting Permission`
- `-311,1 +326,1` (base): `Requesting Permission`
- `-324,0 +340,2` (target): `Requesting permission`
- `-327,4 +344,6` (base): `Requesting Permission`
- `-333,1 +352,1` (base): `Requesting Permission > Permission Options`
- `-338,1 +357,1` (base): `Requesting Permission > Permission Options`
- `-356,0 +376,15` (target): `Requesting permission > Permission options` | `Requesting permission > Security`
- `-362,2 +396,2` (base): `Status`
- `-369,0 +404,5` (target): `Status`
- `-380,1 +419,42` (base): `Status`
- `-386,1 +466,1` (base): `Content`
- `-388,1 +468,1` (base): `Content > Regular Content`
- `-402,1 +482,1` (base): `Content > Display-only Terminals`
- `-414,1 +494,1` (base): `Content > Display-only Terminals`
- `-428,0 +509,4` (target): `Content > Display-only terminals`
- `-447,0 +532,4` (target): `Content > Display-only terminals`
- `-451,1 +539,1` (base): `Content > Display-only Terminals`
- `-453,1 +541,1` (base): `Content > Display-only Terminals`
- `-459,1 +547,1` (base): `Content > Display-only Terminals`
- `-481,1 +569,1` (base): `Content > Display-only Terminals`
- `-484,2 +572,37` (base): `Content > Display-only Terminals`
- `-493,3 +616,8` (base): `Content > Diffs`
- `-520,2 +648,2` (base): `Content > Diffs`
- `-527,1 +655,1` (base): `Content > Diffs`
- `-529,1 +657,1` (base): `Content > Diffs`
- `-532,2 +660,3` (base): `Content > Diffs`
- `-539,1 +668,9` (base): `Content > Diffs`
- `-548,1 +685,3` (base): `Content > Diffs`
- `-560,1 +699,3` (base): `Content > Diffs`
- `-564,1 +705,2` (base): `Content > Diffs`
- `-583,0 +726,27` (target): `Content > Diffs` | `Content > Sessions (unstable)`
- `-586,1 +755,1` (base): `Following the Agent`
- `-600,3 +769,3` (base): `Following the Agent`
- `-603,0 +773,2` (target): `Following the Agent`

### `docs/protocol/v2/draft/transports.mdx` (modified)

- `-8,4 +8,1` (base): `(intro)`
- `-23,2 +20,1` (base): `stdio`
- `-45,1 +41,7` (base): `Message Timing`
- `-49,1 +51,1` (base): `Message Timing`
- `-57,47 +59,11` (base): `JSON-RPC Batch Messages` | `_Streamable HTTP_` | `Custom Transports`
- `-107,1 +73,1` (base): `Custom Transports`


## 3. Core hits

- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `(intro)`): `-6,1 +6,1`, `-8,1 +8,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Session Updates > (intro)`): `-12,1 +12,1`, `-16,25 +16,25`, `-44,1 +44,1`, `-46,2 +46,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Session Updates > Entity IDs`): `-64,1 +63,1`, `-66,1 +65,1`, `-68,1 +67,3`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Foreground and Background Work`): `-116,1 +137,8`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Prompt Lifecycle > (intro)`): `-148,1 +176,11`, `-150,1 +188,1`, `-152,1 +190,31`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `1. User Message`): `-208,1 +276,1`, `-237,1 +305,1`, `-240,1 +308,1`, `-243,1 +311,3`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `2. Prompt Accepted`): `-251,1 +321,1`, `-255,1 +325,1`, `-273,1 +343,1`, `-298,1 +368,1`, `-302,1 +372,1`, `-304,1 +374,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `3. Agent Reports Output > (intro)`): `-316,1 +392,1`, `-408,1 +486,1`, `-410,1 +488,1`, `-420,1 +498,1`, `-442,1 +520,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `4. Report Completion > (intro)`): `-712,1 +784,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `5. Tool Invocation and Status Reporting`): `-769,1 +841,1`, `-793,1 +865,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `6. Continue Conversation`): `-856,1 +928,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Stop Reasons`): `-862,1 +934,1`, `-864,1 +936,1`, `-881,1 +953,5`, `-887,1 +963,3`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Failures`): `-918,1 +996,1`, `-920,1 +998,1`, `-929,1 +1007,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Session States`): `-931,1 +1009,1`, `-939,1 +1017,1`, `-963,1 +1041,1`, `-966,1 +1044,3`, `-968,1 +1048,1`, `-983,1 +1063,1`, `-1015,1 +1095,1`, `-1032,1 +1112,1`, `-1039,2 +1119,1`, `-1049,1 +1128,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Cancellation`): `-1082,1 +1161,1`, `-1094,1 +1173,1`, `-1096,1 +1175,1`, `-1098,4 +1177,1`, `-1103,1 +1179,1`, `-1116,2 +1192,1`, `-1131,4 +1205,0`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/extensibility.mdx` (whole doc): `-6,1 +6,1`, `-8,1 +8,1`, `-21,1 +21,1`, `-25,1 +25,1`, `-33,1 +33,3`, `-35,2 +37,2`, `-57,3 +59,7`, `-64,1 +70,1`, `-67,0 +74,2`, `-83,1 +91,1`, `-89,1 +97,4`, `-91,3 +102,1`, `-97,1 +106,1`, `-112,2 +121,2`, `-124,3 +133,3`, `-135,2 +144,2`, `-140,1 +149,1`, `-142,1 +151,1`, `-146,1 +155,1`, `-154,1 +163,1`, `-156,1 +165,1`, `-163,1 +172,1`, `-171,1 +180,1`, `-193,1 +202,1`, `-208,1 +217,1`, `-215,1 +224,1`, `-222,1 +231,1`, `-224,1 +233,1`, `-233,1 +242,6`, `-237,1 +251,1`, `-241,1 +255,1`, `-245,1 +259,3`, `-257,4 +273,2`, `-272,1 +286,1`; code: `src/tck/v2/conformance/test_extensibility.py`, `src/tck/v2/conformance/test_enums.py`, `src/tck/v2/validation.py`
- `docs/protocol/v2/draft/initialization.mdx` (whole doc): `-82,1 +82,1`, `-84,1 +84,11`, `-94,1 +104,1`, `-97,0 +108,2`, `-117,1 +129,3`, `-120,0 +135,8`, `-125,1 +147,1`, `-127,1 +149,1`, `-129,2 +151,2`, `-144,1 +166,1`, `-147,1 +169,2`, `-149,1 +172,1`, `-175,1 +198,1`, `-180,5 +203,4`, `-192,0 +215,7`, `-195,1 +224,1`, `-200,1 +229,1`, `-209,0 +239,3`, `-228,0 +261,28`, `-239,3 +299,3`, `-246,1 +306,1`, `-248,1 +308,1`, `-253,1 +313,1`, `-259,1 +319,1`, `-268,1 +328,1`, `-273,1 +333,1`, `-286,0 +347,7`, `-291,1 +358,1`, `-295,1 +362,1`, `-297,1 +364,1`, `-301,2 +368,3`, `-305,1 +373,1`; code: `src/tck/common/plugin.py`, `src/tck/v2/conformance/test_initialize.py`, `src/tck/v2/conformance/test_prompt_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Creating a Session`): `-45,1 +45,13`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Initial Session State`): `-84,1 +96,1`, `-94,1 +108,1`, `-121,1 +136,1`, `-123,1 +138,1`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Resuming Sessions`): `-127,1 +142,1`, `-129,2 +144,2`, `-167,1 +182,1`, `-169,1 +184,1`, `-194,2 +209,1`, `-206,10 +236,1`, `-265,1 +286,1`, `-268,6 +289,5`, `-276,1 +296,1`, `-283,1 +303,1`, `-313,1 +333,1`, `-317,1 +337,1`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Closing Active Sessions`): `-336,1 +358,6`, `-338,2 +365,4`, `-362,1 +391,1`, `-366,1 +395,1`, `-378,2 +407,4`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Session ID`): `-483,1 +516,1`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Working Directory`): `-487,1 +520,1`, `-491,1 +524,1`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/overview.mdx` (section `Agent > Baseline Methods`): `-54,1 +58,1`, `-56,1 +60,1`; code: `src/tck/v2/conformance/test_jsonrpc.py`, `src/tck/v2/validation.py`
- `docs/protocol/v2/draft/overview.mdx` (section `Argument requirements`): `-188,1 +218,1`; code: `src/tck/v2/conformance/test_jsonrpc.py`, `src/tck/v2/validation.py`
- `docs/protocol/v2/draft/overview.mdx` (section `Error Handling`): `-191,1 +221,1`; code: `src/tck/v2/conformance/test_jsonrpc.py`, `src/tck/v2/validation.py`
- `docs/protocol/v2/draft/overview.mdx` (section `Conventions`): `-202,0 +235,2`; code: `src/tck/v2/conformance/test_jsonrpc.py`, `src/tck/v2/validation.py`
- `docs/protocol/v2/draft/transports.mdx` (whole doc): `-8,4 +8,1`, `-23,2 +20,1`, `-45,1 +41,7`, `-49,1 +51,1`, `-57,47 +59,11`, `-107,1 +73,1`; code: `src/tck/common/harness`, `src/tck/v2/conformance/test_transport.py`, `src/tck/v2/conformance/test_batch.py`, `src/tck/v2/validation.py`
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `Session Updates > (intro)` at target: section address 'Session Updates > (intro)' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `Session Updates > Entity IDs` at target: section address 'Session Updates > Entity IDs' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `Foreground and Background Work` at target: section address 'Foreground and Background Work' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `Prompt Lifecycle > (intro)` at target: section address 'Prompt Lifecycle > (intro)' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `1. User Message` at target: section address '1. User Message' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `2. Prompt Accepted` at target: section address '2. Prompt Accepted' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `3. Agent Reports Output > (intro)` at target: section address '3. Agent Reports Output > (intro)' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `4. Report Completion > (intro)` at target: section address '4. Report Completion > (intro)' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `5. Tool Invocation and Status Reporting` at target: section address '5. Tool Invocation and Status Reporting' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `6. Continue Conversation` at target: section address '6. Continue Conversation' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `Stop Reasons` at target: section address 'Stop Reasons' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/prompt-lifecycle.mdx` section `Session States` at target: section address 'Session States' matches no heading; headings: ['Session updates', 'Entity IDs', 'Session-directed messages (unstable)', 'Foreground and background work', 'Background work', 'Prompt lifecycle', '1. User message', '2. Prompt accepted', 'Insertion and ordering', 'Prompts during active work', 'Prompts that are never inserted', '3. Agent reports output', 'Message IDs', 'Session notices', 'Session compaction', 'Session usage updates', '4. Report completion', 'End-turn token usage (unstable)', '5. Tool invocation and status reporting', '6. Continue conversation', 'Stop reasons', 'Failures', 'Session states', 'Initial state and synchronization', 'State transitions', 'Waiting for user action', 'Work boundaries and local commands', 'Lifecycle examples', 'Cancellation']
- note: `docs/protocol/v2/draft/session-setup.mdx` section `Creating a Session` at target: section address 'Creating a Session' matches no heading; headings: ['Session lifecycle', 'Creating a session', 'Initial session state', 'Resuming sessions', 'Replay contents', 'Current-state synchronization', 'Closing active sessions', 'Additional workspace roots', 'System prompt', 'Session ID', 'Working directory', 'Workspace root security', 'MCP servers', 'Transport types', 'Stdio transport', 'HTTP transport', 'Checking transport support', 'Security']
- note: `docs/protocol/v2/draft/session-setup.mdx` section `Initial Session State` at target: section address 'Initial Session State' matches no heading; headings: ['Session lifecycle', 'Creating a session', 'Initial session state', 'Resuming sessions', 'Replay contents', 'Current-state synchronization', 'Closing active sessions', 'Additional workspace roots', 'System prompt', 'Session ID', 'Working directory', 'Workspace root security', 'MCP servers', 'Transport types', 'Stdio transport', 'HTTP transport', 'Checking transport support', 'Security']
- note: `docs/protocol/v2/draft/session-setup.mdx` section `Resuming Sessions` at target: section address 'Resuming Sessions' matches no heading; headings: ['Session lifecycle', 'Creating a session', 'Initial session state', 'Resuming sessions', 'Replay contents', 'Current-state synchronization', 'Closing active sessions', 'Additional workspace roots', 'System prompt', 'Session ID', 'Working directory', 'Workspace root security', 'MCP servers', 'Transport types', 'Stdio transport', 'HTTP transport', 'Checking transport support', 'Security']
- note: `docs/protocol/v2/draft/session-setup.mdx` section `Closing Active Sessions` at target: section address 'Closing Active Sessions' matches no heading; headings: ['Session lifecycle', 'Creating a session', 'Initial session state', 'Resuming sessions', 'Replay contents', 'Current-state synchronization', 'Closing active sessions', 'Additional workspace roots', 'System prompt', 'Session ID', 'Working directory', 'Workspace root security', 'MCP servers', 'Transport types', 'Stdio transport', 'HTTP transport', 'Checking transport support', 'Security']
- note: `docs/protocol/v2/draft/session-setup.mdx` section `Working Directory` at target: section address 'Working Directory' matches no heading; headings: ['Session lifecycle', 'Creating a session', 'Initial session state', 'Resuming sessions', 'Replay contents', 'Current-state synchronization', 'Closing active sessions', 'Additional workspace roots', 'System prompt', 'Session ID', 'Working directory', 'Workspace root security', 'MCP servers', 'Transport types', 'Stdio transport', 'HTTP transport', 'Checking transport support', 'Security']
- note: `docs/protocol/v2/draft/overview.mdx` section `Agent > Baseline Methods` at target: section address 'Agent > Baseline Methods' matches no heading; headings: ['Communication Model', 'Message flow', 'Agent', 'Baseline methods', 'Optional methods', 'Notifications', 'Client', 'Baseline methods', 'Optional methods', 'Notifications', 'Request cancellation', 'Argument requirements', 'Error handling', 'Conventions', 'Extensibility', 'Unstable features', 'Next steps']
- note: `docs/protocol/v2/draft/overview.mdx` section `Error Handling` at target: section address 'Error Handling' matches no heading; headings: ['Communication Model', 'Message flow', 'Agent', 'Baseline methods', 'Optional methods', 'Notifications', 'Client', 'Baseline methods', 'Optional methods', 'Notifications', 'Request cancellation', 'Argument requirements', 'Error handling', 'Conventions', 'Extensibility', 'Unstable features', 'Next steps']

## 4. Schema

`$defs` compared between base and target `schema/v2/schema.unstable.json` (`(root)` = everything outside `$defs`).

- Added: `ArchiveSessionRequest`, `ArchiveSessionResponse`, `AuthAccount`, `AuthState`, `AuthStatusCapabilities`, `AuthStatusRequest`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `BackgroundSubagent`, `BackgroundTerminal`, `BackgroundToolCall`, `BackgroundWork`, `CancelTerminalRequest`, `CancelTerminalResponse`, `CancelToolCallRequest`, `CancelToolCallResponse`, `CancelledPermissionOutcome`, `ClientAuthCapabilities`, `Command`, `ErrorData`, `InitializeProxyRequest`, `InitializeProxyResponse`, `ProxyNotification`, `ProxyRequest`, `ProxyResponse`, `ProxySuccessorNotification`, `ProxySuccessorRequest`, `ProxySuccessorResponse`, `SessionArchiveCapabilities`, `SessionArchiveFilter`, `SessionNotFoundErrorData`, `SessionReference`, `SessionStatus`, `SessionStatusCapabilities`, `SessionStatusRequest`, `SessionStatusResponse`, `SessionTitleCapabilities`, `SetSessionTitleRequest`, `SetSessionTitleResponse`, `TerminalCancelCapabilities`, `TerminalCapabilities`, `TerminalSize`, `ToolCallCancelCapabilities`, `ToolCallCapabilities`, `UnarchiveSessionRequest`, `UnarchiveSessionResponse`, `UnsupportedProtocolVersionErrorData`
- Removed: `AuthCapabilities`, `ProtocolLevelNotification`
- Changed: `(root)`, `AbsolutePath`, `AgentAuthCapabilities`, `AgentCapabilities`, `AgentMessage`, `AgentNotification`, `AgentRequest`, `AgentResponse`, `AgentThought`, `Annotations`, `AudioContent`, `AuthMethod`, `AuthMethodAgent`, `AuthMethodTerminal`, `AvailableCommand`, `AvailableCommandInput`, `AvailableCommandsUpdate`, `BlobResourceContents`, `BooleanPropertySchema`, `CancelRequestNotification`, `CancelSessionNotification`, `ClientCapabilities`, `ClientNotification`, `ClientRequest`, `ClientResponse`, `CloseSessionRequest`, `CloseSessionResponse`, `CommandPermissionSubject`, `CompactionSummaryChunk`, `CompactionUpdate`, `CompleteElicitationNotification`, `ConfigOptionUpdate`, `Content`, `ContentBlock`, `ContentChunk`, `Cost`, `CreateElicitationRequest`, `CreateElicitationResponse`, `DeleteSessionRequest`, `DeleteSessionResponse`, `Diff`, `DiffChange`, `DiffPatch`, `DiffPatchFormat`, `DisableProviderRequest`, `DisableProviderResponse`, `ElicitationAcceptAction`, `ElicitationCapabilities`, `ElicitationContentValue`, `ElicitationFormCapabilities`, `ElicitationFormMode`, `ElicitationPropertySchema`, `ElicitationRequestScope`, `ElicitationSchema`, `ElicitationSessionScope`, `ElicitationUrlCapabilities`, `ElicitationUrlMode`, `EmbeddedResource`, `EnumOption`, `EnvVariable`, `Error`, `ErrorCode`, `ErrorStopReason`, `ExtNotification`, `ExtResponse`, `ForkSessionRequest`, `ForkSessionResponse`, `HttpHeader`, `Icon`, `IdleStateUpdate`, `ImageContent`, `Implementation`, `InitializeRequest`, `InitializeResponse`, `IntegerPropertySchema`, `ListProvidersRequest`, `ListProvidersResponse`, `ListSessionsRequest`, `ListSessionsResponse`, `LoginAuthRequest`, `LoginAuthResponse`, `LogoutAuthRequest`, `LogoutAuthResponse`, `McpAcpCapabilities`, `McpCapabilities`, `McpError`, `McpHttpCapabilities`, `McpServer`, `McpServerAcp`, `McpServerHttp`, `McpServerStdio`, `McpStdioCapabilities`, `MessageMcpNotification`, `MessageMcpRequest`, `MessageMcpResponse`, `MultiSelectItems`, `MultiSelectPropertySchema`, `NewSessionRequest`, `NewSessionResponse`, `Notice`, `NumberPropertySchema`, `PermissionOption`, `PlanEntry`, `PlanFile`, `PlanItems`, `PlanMarkdown`, `PlanRemoved`, `PlanUpdate`, `PlanUpdateContent`, `PromptAudioCapabilities`, `PromptCapabilities`, `PromptEmbeddedContextCapabilities`, `PromptImageCapabilities`, `PromptRequest`, `PromptResponse`, `ProviderCurrentConfig`, `ProviderInfo`, `ProvidersCapabilities`, `ReplayFrom`, `ReplayFromStart`, `RequestId`, `RequestPermissionOutcome`, `RequestPermissionRequest`, `RequestPermissionResponse`, `RequiresActionStateUpdate`, `ResourceLink`, `ResumeSessionRequest`, `ResumeSessionResponse`, `RunningStateUpdate`, `SelectedPermissionOutcome`, `SessionAdditionalDirectoriesCapabilities`, `SessionCancelCapabilities`, `SessionCapabilities`, `SessionConfigOption`, `SessionConfigSelect`, `SessionConfigSelectGroup`, `SessionConfigSelectOption`, `SessionConfigSelectOptions`, `SessionDeleteCapabilities`, `SessionForkCapabilities`, `SessionId`, `SessionInfo`, `SessionInfoUpdate`, `SessionMessage`, `SessionMessageChunk`, `SessionSystemPromptCapabilities`, `SessionSystemPromptModeCapabilities`, `SessionSystemPromptOverrideCapabilities`, `SetProviderRequest`, `SetProviderResponse`, `SetSessionConfigOptionRequest`, `SetSessionConfigOptionResponse`, `StateUpdate`, `StringMultiSelectItems`, `StringPropertySchema`, `SubagentSessionCapabilities`, `SubagentUpdate`, `SystemPrompt`, `SystemPromptMode`, `Terminal`, `TerminalAuthCapabilities`, `TerminalExitStatus`, `TerminalOutput`, `TerminalOutputChunk`, `TerminalUpdate`, `TextCommandInput`, `TextContent`, `TextResourceContents`, `TitledMultiSelectItems`, `ToolCallContent`, `ToolCallContentChunk`, `ToolCallLocation`, `ToolCallPermissionSubject`, `ToolCallStatus`, `ToolCallUpdate`, `ToolKind`, `UnknownStateUpdate`, `UpdateSessionNotification`, `Usage`, `UsageUpdate`, `UserMessage`
- `$ref` closure (5 defs that transitively reference a changed def):
  - `DiffPathChange` -> `AbsolutePath`
  - `DiffPathPairChange` -> `AbsolutePath`
  - `EmbeddedResourceResource` -> `BlobResourceContents`, `TextResourceContents`
  - `RequestPermissionSubject` -> `AbsolutePath`, `Annotations`, `AudioContent`, `BlobResourceContents`, `CommandPermissionSubject`, `Content`, `ContentBlock`, `Diff` and 20 more
  - `SessionUpdate` -> `AbsolutePath`, `AgentMessage`, `AgentThought`, `Annotations`, `AudioContent`, `AvailableCommand`, `AvailableCommandInput`, `AvailableCommandsUpdate` and 75 more
- Core `$defs` hit: `ErrorCode` (changed directly); `SessionUpdate` (via $ref closure of `AbsolutePath`, `AgentMessage`, `AgentThought`, `Annotations`, `AudioContent`, `AvailableCommand`, `AvailableCommandInput`, `AvailableCommandsUpdate` and 75 more); `ContentBlock` (changed directly); `AgentCapabilities` (changed directly); `ClientCapabilities` (changed directly)

## 5. Link fan-out

Docs under `docs/protocol/v2/draft/` at target that link to a changed doc.

### `docs/protocol/v2/draft/agent-plan.mdx`

- `docs/protocol/v2/draft/extensibility.mdx:37` `#unstable-plan-operations` (changed section)
- `docs/protocol/v2/draft/overview.mdx:204`
- `docs/protocol/v2/draft/overview.mdx:263` `#unstable-plan-operations` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:32`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:33` `#removing-plans` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:456`
- `docs/protocol/v2/draft/schema.mdx:6560` `#plan-entries` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6591` `#plan-entries` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6621` `#plan-entries` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9215`

### `docs/protocol/v2/draft/authentication.mdx`

- `docs/protocol/v2/draft/error.mdx:34`
- `docs/protocol/v2/draft/initialization.mdx:180`
- `docs/protocol/v2/draft/initialization.mdx:354`
- `docs/protocol/v2/draft/overview.mdx:82` `#logging-out` (changed section)
- `docs/protocol/v2/draft/security.mdx:67` `#launch-safety` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:10`

### `docs/protocol/v2/draft/cancellation.mdx`

- `docs/protocol/v2/draft/authentication.mdx:191`
- `docs/protocol/v2/draft/elicitation.mdx:227`
- `docs/protocol/v2/draft/error.mdx:33`
- `docs/protocol/v2/draft/extensibility.mdx:165`
- `docs/protocol/v2/draft/overview.mdx:214`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:325`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:384`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:388`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1173`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1177`
- `docs/protocol/v2/draft/schema.mdx:2542`
- `docs/protocol/v2/draft/schema.mdx:2548`
- `docs/protocol/v2/draft/tool-calls.mdx:326`

### `docs/protocol/v2/draft/content.mdx`

- `docs/protocol/v2/draft/initialization.mdx:243`
- `docs/protocol/v2/draft/initialization.mdx:310`
- `docs/protocol/v2/draft/overview.mdx:201`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:315`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:675`
- `docs/protocol/v2/draft/schema.mdx:3821`
- `docs/protocol/v2/draft/tool-calls.mdx:470`

### `docs/protocol/v2/draft/elicitation.mdx`

- `docs/protocol/v2/draft/authentication.mdx:179`
- `docs/protocol/v2/draft/cancellation.mdx:44` `#session-cancellation` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:34` `#checking-support` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:194`
- `docs/protocol/v2/draft/overview.mdx:179`
- `docs/protocol/v2/draft/overview.mdx:190` `#url-completion` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:174`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1177` `#session-cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1796` `#url-completion` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1825`
- `docs/protocol/v2/draft/schema.mdx:1845`
- `docs/protocol/v2/draft/security.mdx:71` `#user-interaction-requirements` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:71` `#url-security` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:391` `#session-cancellation` (changed section)

### `docs/protocol/v2/draft/error.mdx`

- `docs/protocol/v2/draft/elicitation.mdx:59` `#unknown-methods` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:90` `#requests-before-initialization` (changed section)
- `docs/protocol/v2/draft/overview.mdx:229`
- `docs/protocol/v2/draft/schema.mdx:8301` `#unknown-sessions` (changed section)
- `docs/protocol/v2/draft/session-delete.mdx:94` `#unknown-sessions` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:51` `#unknown-sessions` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:410` `#unknown-sessions` (changed section)

### `docs/protocol/v2/draft/extensibility.mdx`

- `docs/protocol/v2/draft/agent-plan.mdx:77` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/content.mdx:22` `#advertising-custom-capabilities` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:156` `#unknown-object-fields` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:158` `#advertising-custom-capabilities` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:162` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/overview.mdx:247`
- `docs/protocol/v2/draft/overview.mdx:251` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/overview.mdx:274`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:44` `#enum-and-tagged-union-variants` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:120` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:313` `#advertising-custom-capabilities` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:495` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:565` `#enum-and-tagged-union-variants` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:567` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:624` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:737` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:839` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:56`
- `docs/protocol/v2/draft/schema.mdx:77`
- `docs/protocol/v2/draft/schema.mdx:113`
- `docs/protocol/v2/draft/schema.mdx:130`
- `docs/protocol/v2/draft/schema.mdx:168`
- `docs/protocol/v2/draft/schema.mdx:189`
- `docs/protocol/v2/draft/schema.mdx:242`
- `docs/protocol/v2/draft/schema.mdx:275`
- `docs/protocol/v2/draft/schema.mdx:331`
- `docs/protocol/v2/draft/schema.mdx:373`
- `docs/protocol/v2/draft/schema.mdx:397`
- `docs/protocol/v2/draft/schema.mdx:427`
- `docs/protocol/v2/draft/schema.mdx:448`
- `docs/protocol/v2/draft/schema.mdx:483`
- `docs/protocol/v2/draft/schema.mdx:520`
- `docs/protocol/v2/draft/schema.mdx:559`
- `docs/protocol/v2/draft/schema.mdx:583`
- `docs/protocol/v2/draft/schema.mdx:636`
- `docs/protocol/v2/draft/schema.mdx:683`
- `docs/protocol/v2/draft/schema.mdx:703`
- `docs/protocol/v2/draft/schema.mdx:729`
- `docs/protocol/v2/draft/schema.mdx:749`
- `docs/protocol/v2/draft/schema.mdx:794`
- `docs/protocol/v2/draft/schema.mdx:842`
- `docs/protocol/v2/draft/schema.mdx:885`
- `docs/protocol/v2/draft/schema.mdx:929`
- `docs/protocol/v2/draft/schema.mdx:973`
- `docs/protocol/v2/draft/schema.mdx:1018`
- `docs/protocol/v2/draft/schema.mdx:1086`
- `docs/protocol/v2/draft/schema.mdx:1134`
- `docs/protocol/v2/draft/schema.mdx:1173`
- `docs/protocol/v2/draft/schema.mdx:1246`
- `docs/protocol/v2/draft/schema.mdx:1290`
- `docs/protocol/v2/draft/schema.mdx:1376`
- `docs/protocol/v2/draft/schema.mdx:1422`
- `docs/protocol/v2/draft/schema.mdx:1455`
- `docs/protocol/v2/draft/schema.mdx:1500`
- `docs/protocol/v2/draft/schema.mdx:1527`
- `docs/protocol/v2/draft/schema.mdx:1583`
- `docs/protocol/v2/draft/schema.mdx:1607`
- `docs/protocol/v2/draft/schema.mdx:1645`
- `docs/protocol/v2/draft/schema.mdx:1668`
- `docs/protocol/v2/draft/schema.mdx:1705`
- `docs/protocol/v2/draft/schema.mdx:1728`
- `docs/protocol/v2/draft/schema.mdx:1772`
- `docs/protocol/v2/draft/schema.mdx:1813`
- `docs/protocol/v2/draft/schema.mdx:1856`
- `docs/protocol/v2/draft/schema.mdx:2060`
- `docs/protocol/v2/draft/schema.mdx:2158`
- `docs/protocol/v2/draft/schema.mdx:2200`
- `docs/protocol/v2/draft/schema.mdx:2221`
- `docs/protocol/v2/draft/schema.mdx:2263`
- `docs/protocol/v2/draft/schema.mdx:2308`
- `docs/protocol/v2/draft/schema.mdx:2348`
- `docs/protocol/v2/draft/schema.mdx:2440`
- `docs/protocol/v2/draft/schema.mdx:2489`
- `docs/protocol/v2/draft/schema.mdx:2559`
- `docs/protocol/v2/draft/schema.mdx:2593`
- `docs/protocol/v2/draft/schema.mdx:2626`
- `docs/protocol/v2/draft/schema.mdx:2688` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2726` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2749`
- `docs/protocol/v2/draft/schema.mdx:2792`
- `docs/protocol/v2/draft/schema.mdx:2833`
- `docs/protocol/v2/draft/schema.mdx:2886`
- `docs/protocol/v2/draft/schema.mdx:2928`
- `docs/protocol/v2/draft/schema.mdx:2996`
- `docs/protocol/v2/draft/schema.mdx:3037`
- `docs/protocol/v2/draft/schema.mdx:3116`
- `docs/protocol/v2/draft/schema.mdx:3138`
- `docs/protocol/v2/draft/schema.mdx:3212`
- `docs/protocol/v2/draft/schema.mdx:3264`
- `docs/protocol/v2/draft/schema.mdx:3288`
- `docs/protocol/v2/draft/schema.mdx:3308`
- `docs/protocol/v2/draft/schema.mdx:3328`
- `docs/protocol/v2/draft/schema.mdx:3359`
- `docs/protocol/v2/draft/schema.mdx:3384`
- `docs/protocol/v2/draft/schema.mdx:3412`
- `docs/protocol/v2/draft/schema.mdx:3462`
- `docs/protocol/v2/draft/schema.mdx:3497`
- `docs/protocol/v2/draft/schema.mdx:3532`
- `docs/protocol/v2/draft/schema.mdx:3553`
- `docs/protocol/v2/draft/schema.mdx:3584`
- `docs/protocol/v2/draft/schema.mdx:3620`
- `docs/protocol/v2/draft/schema.mdx:3652`
- `docs/protocol/v2/draft/schema.mdx:3719`
- `docs/protocol/v2/draft/schema.mdx:3751` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:3780`
- `docs/protocol/v2/draft/schema.mdx:3800`
- `docs/protocol/v2/draft/schema.mdx:3839`
- `docs/protocol/v2/draft/schema.mdx:3870`
- `docs/protocol/v2/draft/schema.mdx:3915`
- `docs/protocol/v2/draft/schema.mdx:3952`
- `docs/protocol/v2/draft/schema.mdx:4023`
- `docs/protocol/v2/draft/schema.mdx:4083`
- `docs/protocol/v2/draft/schema.mdx:4110`
- `docs/protocol/v2/draft/schema.mdx:4141`
- `docs/protocol/v2/draft/schema.mdx:4174`
- `docs/protocol/v2/draft/schema.mdx:4366`
- `docs/protocol/v2/draft/schema.mdx:4473`
- `docs/protocol/v2/draft/schema.mdx:4540`
- `docs/protocol/v2/draft/schema.mdx:4624`
- `docs/protocol/v2/draft/schema.mdx:4704`
- `docs/protocol/v2/draft/schema.mdx:4754`
- `docs/protocol/v2/draft/schema.mdx:4804`
- `docs/protocol/v2/draft/schema.mdx:4842`
- `docs/protocol/v2/draft/schema.mdx:4947`
- `docs/protocol/v2/draft/schema.mdx:5023`
- `docs/protocol/v2/draft/schema.mdx:5096`
- `docs/protocol/v2/draft/schema.mdx:5125`
- `docs/protocol/v2/draft/schema.mdx:5157`
- `docs/protocol/v2/draft/schema.mdx:5195`
- `docs/protocol/v2/draft/schema.mdx:5224`
- `docs/protocol/v2/draft/schema.mdx:5337`
- `docs/protocol/v2/draft/schema.mdx:5360`
- `docs/protocol/v2/draft/schema.mdx:5394`
- `docs/protocol/v2/draft/schema.mdx:5402`
- `docs/protocol/v2/draft/schema.mdx:5410`
- `docs/protocol/v2/draft/schema.mdx:5425`
- `docs/protocol/v2/draft/schema.mdx:5448`
- `docs/protocol/v2/draft/schema.mdx:5525`
- `docs/protocol/v2/draft/schema.mdx:5699`
- `docs/protocol/v2/draft/schema.mdx:5741`
- `docs/protocol/v2/draft/schema.mdx:5775`
- `docs/protocol/v2/draft/schema.mdx:5872`
- `docs/protocol/v2/draft/schema.mdx:5889`
- `docs/protocol/v2/draft/schema.mdx:5956`
- `docs/protocol/v2/draft/schema.mdx:5993`
- `docs/protocol/v2/draft/schema.mdx:6033`
- `docs/protocol/v2/draft/schema.mdx:6065`
- `docs/protocol/v2/draft/schema.mdx:6134`
- `docs/protocol/v2/draft/schema.mdx:6174`
- `docs/protocol/v2/draft/schema.mdx:6204`
- `docs/protocol/v2/draft/schema.mdx:6236`
- `docs/protocol/v2/draft/schema.mdx:6272`
- `docs/protocol/v2/draft/schema.mdx:6314`
- `docs/protocol/v2/draft/schema.mdx:6337`
- `docs/protocol/v2/draft/schema.mdx:6397`
- `docs/protocol/v2/draft/schema.mdx:6455`
- `docs/protocol/v2/draft/schema.mdx:6502`
- `docs/protocol/v2/draft/schema.mdx:6571`
- `docs/protocol/v2/draft/schema.mdx:6667`
- `docs/protocol/v2/draft/schema.mdx:6699`
- `docs/protocol/v2/draft/schema.mdx:6730`
- `docs/protocol/v2/draft/schema.mdx:6757`
- `docs/protocol/v2/draft/schema.mdx:6777`
- `docs/protocol/v2/draft/schema.mdx:6800`
- `docs/protocol/v2/draft/schema.mdx:6834`
- `docs/protocol/v2/draft/schema.mdx:6867`
- `docs/protocol/v2/draft/schema.mdx:6927`
- `docs/protocol/v2/draft/schema.mdx:6955`
- `docs/protocol/v2/draft/schema.mdx:6998`
- `docs/protocol/v2/draft/schema.mdx:7017`
- `docs/protocol/v2/draft/schema.mdx:7052`
- `docs/protocol/v2/draft/schema.mdx:7092`
- `docs/protocol/v2/draft/schema.mdx:7129`
- `docs/protocol/v2/draft/schema.mdx:7151`
- `docs/protocol/v2/draft/schema.mdx:7200`
- `docs/protocol/v2/draft/schema.mdx:7247`
- `docs/protocol/v2/draft/schema.mdx:7270`
- `docs/protocol/v2/draft/schema.mdx:7325`
- `docs/protocol/v2/draft/schema.mdx:7353`
- `docs/protocol/v2/draft/schema.mdx:7421`
- `docs/protocol/v2/draft/schema.mdx:7449`
- `docs/protocol/v2/draft/schema.mdx:7536`
- `docs/protocol/v2/draft/schema.mdx:7564`
- `docs/protocol/v2/draft/schema.mdx:7589`
- `docs/protocol/v2/draft/schema.mdx:7613`
- `docs/protocol/v2/draft/schema.mdx:7670`
- `docs/protocol/v2/draft/schema.mdx:7697`
- `docs/protocol/v2/draft/schema.mdx:7826`
- `docs/protocol/v2/draft/schema.mdx:7993`
- `docs/protocol/v2/draft/schema.mdx:8019`
- `docs/protocol/v2/draft/schema.mdx:8070`
- `docs/protocol/v2/draft/schema.mdx:8093`
- `docs/protocol/v2/draft/schema.mdx:8121`
- `docs/protocol/v2/draft/schema.mdx:8187` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8226` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8286`
- `docs/protocol/v2/draft/schema.mdx:8312`
- `docs/protocol/v2/draft/schema.mdx:8342`
- `docs/protocol/v2/draft/schema.mdx:8405`
- `docs/protocol/v2/draft/schema.mdx:8425`
- `docs/protocol/v2/draft/schema.mdx:8451`
- `docs/protocol/v2/draft/schema.mdx:8479`
- `docs/protocol/v2/draft/schema.mdx:8503`
- `docs/protocol/v2/draft/schema.mdx:8528`
- `docs/protocol/v2/draft/schema.mdx:8565` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8592`
- `docs/protocol/v2/draft/schema.mdx:8629` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8656`
- `docs/protocol/v2/draft/schema.mdx:8693` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8732`
- `docs/protocol/v2/draft/schema.mdx:8763`
- `docs/protocol/v2/draft/schema.mdx:8941`
- `docs/protocol/v2/draft/schema.mdx:8977`
- `docs/protocol/v2/draft/schema.mdx:9038`
- `docs/protocol/v2/draft/schema.mdx:9067` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9144` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9194`
- `docs/protocol/v2/draft/schema.mdx:9224`
- `docs/protocol/v2/draft/schema.mdx:9251`
- `docs/protocol/v2/draft/schema.mdx:9274`
- `docs/protocol/v2/draft/schema.mdx:9297`
- `docs/protocol/v2/draft/schema.mdx:9323` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9352`
- `docs/protocol/v2/draft/schema.mdx:9393`
- `docs/protocol/v2/draft/schema.mdx:9431` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9464`
- `docs/protocol/v2/draft/schema.mdx:9498` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9575` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9635`
- `docs/protocol/v2/draft/schema.mdx:9731`
- `docs/protocol/v2/draft/schema.mdx:9762`
- `docs/protocol/v2/draft/schema.mdx:9940`
- `docs/protocol/v2/draft/schema.mdx:9976`
- `docs/protocol/v2/draft/schema.mdx:10067`
- `docs/protocol/v2/draft/schema.mdx:10090`
- `docs/protocol/v2/draft/schema.mdx:10174`
- `docs/protocol/v2/draft/schema.mdx:10234` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10305`
- `docs/protocol/v2/draft/schema.mdx:10385`
- `docs/protocol/v2/draft/schema.mdx:10409`
- `docs/protocol/v2/draft/schema.mdx:10428`
- `docs/protocol/v2/draft/schema.mdx:10450`
- `docs/protocol/v2/draft/schema.mdx:10477`
- `docs/protocol/v2/draft/schema.mdx:10512`
- `docs/protocol/v2/draft/schema.mdx:10536`
- `docs/protocol/v2/draft/schema.mdx:10562`
- `docs/protocol/v2/draft/schema.mdx:10606` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10652`
- `docs/protocol/v2/draft/schema.mdx:10672`
- `docs/protocol/v2/draft/schema.mdx:10698`
- `docs/protocol/v2/draft/schema.mdx:10730`
- `docs/protocol/v2/draft/schema.mdx:10752`
- `docs/protocol/v2/draft/schema.mdx:10774`
- `docs/protocol/v2/draft/schema.mdx:10806`
- `docs/protocol/v2/draft/schema.mdx:10829`
- `docs/protocol/v2/draft/schema.mdx:10862`
- `docs/protocol/v2/draft/schema.mdx:10889`
- `docs/protocol/v2/draft/schema.mdx:10946`
- `docs/protocol/v2/draft/schema.mdx:10980`
- `docs/protocol/v2/draft/schema.mdx:11007`
- `docs/protocol/v2/draft/schema.mdx:11095` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11240`
- `docs/protocol/v2/draft/schema.mdx:11270`
- `docs/protocol/v2/draft/schema.mdx:11297`
- `docs/protocol/v2/draft/schema.mdx:11356`
- `docs/protocol/v2/draft/schema.mdx:11406` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/security.mdx:43` `#enum-and-tagged-union-variants` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:136`
- `docs/protocol/v2/draft/session-list.mdx:198` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:315` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:114` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:551` `#metadata-patches` (changed section)

### `docs/protocol/v2/draft/initialization.mdx`

- `docs/protocol/v2/draft/authentication.mdx:7`
- `docs/protocol/v2/draft/content.mdx:63` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/content.mdx:96` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/content.mdx:132` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/elicitation.mdx:27` `#client-capabilities` (changed section)
- `docs/protocol/v2/draft/error.mdx:36` `#version-negotiation` (changed section)
- `docs/protocol/v2/draft/error.mdx:60` `#before-initialization-completes` (changed section)
- `docs/protocol/v2/draft/error.mdx:68` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:35` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/overview.mdx:67`
- `docs/protocol/v2/draft/overview.mdx:255` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/overview.mdx:271`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:10`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:313` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:313`
- `docs/protocol/v2/draft/schema.mdx:35`
- `docs/protocol/v2/draft/schema.mdx:223`
- `docs/protocol/v2/draft/schema.mdx:231`
- `docs/protocol/v2/draft/schema.mdx:264`
- `docs/protocol/v2/draft/schema.mdx:2615` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:3573` `#client-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6944` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:7686` `#session-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11259` `#version-negotiation` (changed section)
- `docs/protocol/v2/draft/session-delete.mdx:8`
- `docs/protocol/v2/draft/session-list.mdx:10`
- `docs/protocol/v2/draft/session-setup.mdx:8`

### `docs/protocol/v2/draft/overview.mdx`

- `docs/protocol/v2/draft/initialization.mdx:6` `#client` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:6` `#agent` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:6` `#agent` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:6` `#client` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:6` `#agent` (changed section)

### `docs/protocol/v2/draft/prompt-lifecycle.mdx`

- `docs/protocol/v2/draft/agent-plan.mdx:8` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/authentication.mdx:243` `#failures` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:33` `#cancellation` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:38` `#state-transitions` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:59` `#cancellation` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:59` `#stop-reasons` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:59` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:63` `#cancellation` (changed section)
- `docs/protocol/v2/draft/content.mdx:10` `#1-user-message` (changed section)
- `docs/protocol/v2/draft/content.mdx:11` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/elicitation.mdx:86` `#waiting-for-user-action` (changed section)
- `docs/protocol/v2/draft/elicitation.mdx:221` `#cancellation` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:36` `#session-notices` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:36` `#session-compaction` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:38` `#end-turn-token-usage-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:97` `#1-user-message` (changed section)
- `docs/protocol/v2/draft/overview.mdx:152` `#cancellation` (changed section)
- `docs/protocol/v2/draft/overview.mdx:199` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/overview.mdx:207` `#session-compaction` (changed section)
- `docs/protocol/v2/draft/overview.mdx:209` `#session-notices` (changed section)
- `docs/protocol/v2/draft/overview.mdx:262` `#session-directed-messages-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:264` `#end-turn-token-usage-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:265` `#session-states` (changed section)
- `docs/protocol/v2/draft/overview.mdx:273`
- `docs/protocol/v2/draft/schema.mdx:619` `#cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:625` `#cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1067`
- `docs/protocol/v2/draft/schema.mdx:1075` `#1-user-message` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1123` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2329` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2337` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/schema.mdx:3344` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:5536` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:5544` `#stop-reasons` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6386` `#session-notices` (changed section)
- `docs/protocol/v2/draft/schema.mdx:7238` `#cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:7432` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:7547` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8513` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8743` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8774` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8785` `#stop-reasons` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8952` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8988` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9717` `#session-states` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9742` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9773` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9784` `#stop-reasons` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9951` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9987` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11251` `#background-work` (changed section)
- `docs/protocol/v2/draft/security.mdx:80` `#session-directed-messages-unstable` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:219` `#session-compaction` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:228` `#session-notices` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:284` `#entity-ids` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:289` `#entity-ids` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:340` `#session-states` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:346` `#background-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:390` `#cancellation` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:391` `#background-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:395` `#prompts-during-active-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:395` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:685` `#session-notices` (changed section)
- `docs/protocol/v2/draft/slash-commands.mdx:6`
- `docs/protocol/v2/draft/slash-commands.mdx:149` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/slash-commands.mdx:156` `#work-boundaries-and-local-commands` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:6`
- `docs/protocol/v2/draft/tool-calls.mdx:8` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:125` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:209` `#waiting-for-user-action` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:268` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:268` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:326` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:344` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:423` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:423` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:587` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:750` `#session-directed-messages-unstable` (changed section)

### `docs/protocol/v2/draft/schema.mdx`

- `docs/protocol/v2/draft/authentication.mdx:153` `#authmethod` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:29` `#errorcode` (changed section)
- `docs/protocol/v2/draft/elicitation.mdx:270` `#elicitation%2Fcreate` (changed section)
- `docs/protocol/v2/draft/overview.mdx:64` `#initialize` (changed section)
- `docs/protocol/v2/draft/overview.mdx:72` `#auth%2Flogin` (changed section)
- `docs/protocol/v2/draft/overview.mdx:79` `#auth%2Flogout` (changed section)
- `docs/protocol/v2/draft/overview.mdx:87` `#session%2Fnew` (changed section)
- `docs/protocol/v2/draft/overview.mdx:95` `#session%2Fprompt` (changed section)
- `docs/protocol/v2/draft/overview.mdx:103` `#session%2Flist` (changed section)
- `docs/protocol/v2/draft/overview.mdx:110` `#session%2Fresume` (changed section)
- `docs/protocol/v2/draft/overview.mdx:118` `#session%2Fclose` (changed section)
- `docs/protocol/v2/draft/overview.mdx:129` `#session%2Fset_config_option` (changed section)
- `docs/protocol/v2/draft/overview.mdx:139` `#session%2Fdelete` (changed section)
- `docs/protocol/v2/draft/overview.mdx:149` `#session%2Fcancel` (changed section)
- `docs/protocol/v2/draft/overview.mdx:165` `#session%2Frequest_permission` (changed section)
- `docs/protocol/v2/draft/overview.mdx:177` `#elicitation%2Fcreate` (changed section)
- `docs/protocol/v2/draft/overview.mdx:187` `#elicitation%2Fcomplete` (changed section)
- `docs/protocol/v2/draft/overview.mdx:196` `#session%2Fupdate` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:42` `#sessionupdate` (changed section)

### `docs/protocol/v2/draft/security.mdx`

- `docs/protocol/v2/draft/content.mdx:16` `#rendering-agent-content` (changed section)
- `docs/protocol/v2/draft/content.mdx:16` `#uris-and-remote-resources` (changed section)
- `docs/protocol/v2/draft/content.mdx:30` `#rendering-agent-content` (changed section)
- `docs/protocol/v2/draft/overview.mdx:270`

### `docs/protocol/v2/draft/session-config-options.mdx`

- `docs/protocol/v2/draft/initialization.mdx:239` `#setting-a-config-option` (changed section)
- `docs/protocol/v2/draft/overview.mdx:133` `#from-the-client` (changed section)
- `docs/protocol/v2/draft/overview.mdx:206` `#from-the-agent` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:35` `#from-the-agent` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1279` `#setting-a-config-option` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11198`
- `docs/protocol/v2/draft/session-list.mdx:164` `#from-the-agent` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:108`
- `docs/protocol/v2/draft/tool-calls.mdx:69`

### `docs/protocol/v2/draft/session-delete.mdx`

- `docs/protocol/v2/draft/error.mdx:56`
- `docs/protocol/v2/draft/extensibility.mdx:33`
- `docs/protocol/v2/draft/initialization.mdx:256`
- `docs/protocol/v2/draft/overview.mdx:141`
- `docs/protocol/v2/draft/session-list.mdx:42`
- `docs/protocol/v2/draft/session-setup.mdx:47`

### `docs/protocol/v2/draft/session-list.mdx`

- `docs/protocol/v2/draft/error.mdx:66` `#archived-sessions-unstable` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:266` `#archived-sessions-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:105`
- `docs/protocol/v2/draft/overview.mdx:257` `#archived-sessions-unstable` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:36` `#updating-session-metadata` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:443`

### `docs/protocol/v2/draft/session-setup.mdx`

- `docs/protocol/v2/draft/elicitation.mdx:233` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/error.mdx:50` `#system-prompt` (changed section)
- `docs/protocol/v2/draft/error.mdx:54` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/error.mdx:56` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:300` `#system-prompt` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:380`
- `docs/protocol/v2/draft/overview.mdx:90` `#creating-a-session` (changed section)
- `docs/protocol/v2/draft/overview.mdx:113` `#resuming-sessions` (changed section)
- `docs/protocol/v2/draft/overview.mdx:121` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/overview.mdx:272`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:10`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:46` `#replay-contents` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:215` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:306` `#session-id` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:370` `#resuming-sessions` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:374` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:752` `#replay-contents` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1060` `#current-state-synchronization` (changed section)
- `docs/protocol/v2/draft/schema.mdx:956`
- `docs/protocol/v2/draft/schema.mdx:962` `#creating-a-session` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1007` `#creating-a-session` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1235` `#current-state-synchronization` (changed section)
- `docs/protocol/v2/draft/schema.mdx:5977` `#mcp-servers` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8104` `#session-id` (changed section)
- `docs/protocol/v2/draft/security.mdx:38` `#workspace-root-security` (changed section)
- `docs/protocol/v2/draft/security.mdx:52` `#system-prompt` (changed section)
- `docs/protocol/v2/draft/security.mdx:66` `#workspace-root-security` (changed section)
- `docs/protocol/v2/draft/security.mdx:68` `#security` (changed section)
- `docs/protocol/v2/draft/security.mdx:79` `#workspace-root-security` (changed section)
- `docs/protocol/v2/draft/session-config-options.mdx:10`
- `docs/protocol/v2/draft/session-config-options.mdx:375` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/session-delete.mdx:95` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:162` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:207` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:216` `#resuming-sessions` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:247` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/slash-commands.mdx:12` `#initial-session-state` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:774` `#workspace-root-security` (changed section)
- `docs/protocol/v2/draft/transports.mdx:43` `#session-lifecycle` (changed section)

### `docs/protocol/v2/draft/slash-commands.mdx`

- `docs/protocol/v2/draft/overview.mdx:205` `#advertising-commands` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:34`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:327` `#running-commands` (changed section)
- `docs/protocol/v2/draft/security.mdx:27`
- `docs/protocol/v2/draft/session-setup.mdx:108`

### `docs/protocol/v2/draft/tool-calls.mdx`

- `docs/protocol/v2/draft/content.mdx:12`
- `docs/protocol/v2/draft/overview.mdx:169` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/overview.mdx:202`
- `docs/protocol/v2/draft/overview.mdx:203` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:28` `#streaming-content` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:29` `#reporting` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:30` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:31` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:174` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:180` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:181` `#status` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:893` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:924`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1175` `#status` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1634` `#cancelling-terminals` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1694` `#cancelling-tool-calls` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2244` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2252` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/schema.mdx:4130` `#content` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10439` `#cancelling-terminals` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10763` `#cancelling-tool-calls` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10792` `#content` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10969` `#following-the-agent` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11025` `#status` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11081`
- `docs/protocol/v2/draft/schema.mdx:11160` `#reporting` (changed section)
- `docs/protocol/v2/draft/security.mdx:69` `#security` (changed section)
- `docs/protocol/v2/draft/security.mdx:70` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/security.mdx:70` `#diffs` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:219` `#display-only-terminals` (changed section)

### `docs/protocol/v2/draft/transports.mdx`

- `docs/protocol/v2/draft/overview.mdx:21` `#no-batches` (changed section)
- `docs/protocol/v2/draft/security.mdx:62` `#custom-transports` (changed section)

### `docs/rfds/get-auth-state.mdx`

- `docs/protocol/v2/draft/initialization.mdx:216`
- `docs/protocol/v2/draft/overview.mdx:260`

### `docs/rfds/plan-operations.mdx`

- `docs/protocol/v2/draft/overview.mdx:263`

### `docs/rfds/proxy-chains.mdx`

- `docs/protocol/v2/draft/overview.mdx:266`
- `docs/protocol/v2/draft/schema.mdx:2390`
- `docs/protocol/v2/draft/schema.mdx:2425`
- `docs/protocol/v2/draft/schema.mdx:2474`

### `docs/rfds/session-archive.mdx`

- `docs/protocol/v2/draft/overview.mdx:257`
- `docs/protocol/v2/draft/session-list.mdx:220`

### `docs/rfds/session-set-title.mdx`

- `docs/protocol/v2/draft/initialization.mdx:282`
- `docs/protocol/v2/draft/overview.mdx:259`

### `docs/rfds/session-status.mdx`

- `docs/protocol/v2/draft/initialization.mdx:276`
- `docs/protocol/v2/draft/overview.mdx:258`
- `docs/protocol/v2/draft/session-list.mdx:250`

### `docs/rfds/streamable-http-websocket-transport.mdx`

- `docs/protocol/v2/draft/transports.mdx:8`

### `docs/rfds/subagents.mdx`

- `docs/protocol/v2/draft/overview.mdx:262`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:142` `#delegated-tasks` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:182`
- `docs/protocol/v2/draft/tool-calls.mdx:457`
- `docs/protocol/v2/draft/tool-calls.mdx:603`
- `docs/protocol/v2/draft/tool-calls.mdx:731`


## 6. Affected entries

- ACP-INIT-001: `#/$defs/InitializeResponse`: `InitializeResponse` changed
- ACP-INIT-201: `#/$defs/InitializeResponse/properties/protocolVersion`: `InitializeResponse` changed
- ACP-INIT-003: `docs/protocol/v2/draft/initialization.mdx:117` overlaps hunk `-117,1 +129,3`
- ACP-INIT-202: `docs/protocol/v2/draft/initialization.mdx:117` overlaps hunk `-117,1 +129,3`
- ACP-INIT-205: `#/$defs/ErrorCode`: `ErrorCode` changed
- ACP-INIT-206: `docs/protocol/v2/draft/initialization.mdx:117` overlaps hunk `-117,1 +129,3`
- ACP-INIT-207: `docs/protocol/v2/draft/initialization.mdx:117` overlaps hunk `-117,1 +129,3`
- ACP-INIT-203: `#/$defs/InitializeResponse/properties/info`: `InitializeResponse` changed; `#/$defs/InitializeResponse/required`: `InitializeResponse` changed; `#/$defs/Implementation`: `Implementation` changed
- ACP-INIT-204: `#/$defs/AgentCapabilities`: `AgentCapabilities` changed; `#/$defs/SessionCapabilities`: `SessionCapabilities` changed
- ACP-SCHEMA-001: cites all of `docs/protocol/v2/draft/initialization.mdx`, which changed; `#/anyOf`: `(root)` changed
- ACP-SESSION-001: `#/$defs/NewSessionRequest/required`: `NewSessionRequest` changed; `#/$defs/NewSessionResponse/required`: `NewSessionResponse` changed
- ACP-SESSION-002: `#/$defs/SessionId`: `SessionId` changed
- ACP-PROMPT-205: `docs/protocol/v2/draft/schema.mdx:8397-8401` overlaps hunk `-8398,1 +10194,1`, `-8401,1 +10197,1`; `#/$defs/UpdateSessionNotification/required`: `UpdateSessionNotification` changed; `#/$defs/SessionUpdate`: `SessionUpdate` in $ref closure of `AbsolutePath`, `AgentMessage`, `AgentThought`, `Annotations`, `AudioContent`, `AvailableCommand`, `AvailableCommandInput`, `AvailableCommandsUpdate` and 75 more; `#/$defs/SubagentUpdate`: `SubagentUpdate` changed
- ACP-PROMPT-201: `docs/protocol/v2/draft/prompt-lifecycle.mdx:253-255` overlaps hunk `-255,1 +325,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:271-274` overlaps hunk `-273,1 +343,1`; `#/$defs/PromptResponse/required`: `PromptResponse` changed
- ACP-PROMPT-203: `#/$defs/UserMessage`: `UserMessage` changed; `#/$defs/ContentChunk`: `ContentChunk` changed
- ACP-STATE-201: `#/$defs/StateUpdate`: `StateUpdate` changed
- ACP-STATE-203: `docs/protocol/v2/draft/prompt-lifecycle.mdx:864` overlaps hunk `-864,1 +936,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:887` overlaps hunk `-887,1 +963,3`; `#/$defs/IdleStateUpdate/properties/stopReason`: `IdleStateUpdate` changed; `#/$defs/IdleStateUpdate/anyOf/7`: `IdleStateUpdate` changed
- ACP-STATE-204: `docs/protocol/v2/draft/prompt-lifecycle.mdx:864` overlaps hunk `-864,1 +936,1`; `#/$defs/IdleStateUpdate`: `IdleStateUpdate` changed
- ACP-STATE-205: `#/$defs/RequiresActionStateUpdate`: `RequiresActionStateUpdate` changed
- ACP-PROMPT-206: `docs/protocol/v2/draft/initialization.mdx:248` overlaps hunk `-248,1 +308,1`; `#/$defs/PromptRequest/properties/prompt`: `PromptRequest` changed; `#/$defs/ResourceLink`: `ResourceLink` changed
- ACP-PROMPT-207: `docs/protocol/v2/draft/prompt-lifecycle.mdx:255` overlaps hunk `-255,1 +325,1`; `docs/protocol/v2/draft/cancellation.mdx:53` overlaps hunk `-53,1 +59,1`
- ACP-PROMPT-208: `docs/protocol/v2/draft/prompt-lifecycle.mdx:255` overlaps hunk `-255,1 +325,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:302` overlaps hunk `-302,1 +372,1`
- ACP-PROMPTCAP-001: `docs/protocol/v2/draft/initialization.mdx:246-271` overlaps hunk `-246,1 +306,1`, `-248,1 +308,1`, `-253,1 +313,1`, `-259,1 +319,1`, `-268,1 +328,1`; `#/$defs/PromptCapabilities`: `PromptCapabilities` changed; `#/$defs/ImageContent`: `ImageContent` changed
- ACP-PROMPTCAP-002: `docs/protocol/v2/draft/initialization.mdx:246-271` overlaps hunk `-246,1 +306,1`, `-248,1 +308,1`, `-253,1 +313,1`, `-259,1 +319,1`, `-268,1 +328,1`; `#/$defs/PromptCapabilities`: `PromptCapabilities` changed; `#/$defs/AudioContent`: `AudioContent` changed
- ACP-PROMPTCAP-003: `docs/protocol/v2/draft/initialization.mdx:246-271` overlaps hunk `-246,1 +306,1`, `-248,1 +308,1`, `-253,1 +313,1`, `-259,1 +319,1`, `-268,1 +328,1`; `#/$defs/PromptCapabilities`: `PromptCapabilities` changed; `#/$defs/EmbeddedResource`: `EmbeddedResource` changed
- ACP-PERM-201: `docs/protocol/v2/draft/tool-calls.mdx:236-263` overlaps hunk `-256,2 +264,2`, `-259,0 +268,7`; `docs/protocol/v2/draft/tool-calls.mdx:337-355` overlaps hunk `-338,1 +357,1`; `#/$defs/RequestPermissionRequest/required`: `RequestPermissionRequest` changed; `#/$defs/RequestPermissionRequest/properties/options`: `RequestPermissionRequest` changed; `#/$defs/PermissionOption/required`: `PermissionOption` changed
- ACP-CLIENTCAP-201: `docs/protocol/v2/draft/elicitation.mdx:187` overlaps hunk `-187,4 +219,1`; `#/$defs/CreateElicitationRequest`: `CreateElicitationRequest` changed
- ACP-CLIENTCAP-202: `docs/protocol/v2/draft/extensibility.mdx:156` overlaps hunk `-156,1 +165,1`
- ACP-INFO-CONCURRENT-201: `docs/rfds/v2/prompt.mdx:88` overlaps hunk `-88,1 +88,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:1039-1040` overlaps hunk `-1039,2 +1119,1`
- ACP-INFO-UNKNOWNSESSION-001: cites all of `docs/protocol/v2/draft/error.mdx`, which changed
- ACP-CANCEL-201: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1109-1117` overlaps hunk `-1116,2 +1192,1`
- ACP-CANCEL-203: `docs/protocol/v2/draft/prompt-lifecycle.mdx:255` overlaps hunk `-255,1 +325,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:1094` overlaps hunk `-1094,1 +1173,1`; `docs/protocol/v2/draft/cancellation.mdx:53` overlaps hunk `-53,1 +59,1`; `#/$defs/IdleStateUpdate/anyOf/4`: `IdleStateUpdate` changed
- ACP-CANCEL-204: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1103` overlaps hunk `-1103,1 +1179,1`; `docs/protocol/v2/draft/schema.mdx:458-459` overlaps hunk `-459,1 +596,6`
- ACP-CANCEL-205: `docs/protocol/v2/draft/transports.mdx:78-79` overlaps hunk `-57,47 +59,11`; `#/$defs/ClientNotification/properties/params/anyOf/0/anyOf/0`: `ClientNotification` changed; `#/$defs/CancelSessionNotification`: `CancelSessionNotification` changed
- ACP-CANCEL-206: `#/$defs/CancelSessionNotification`: `CancelSessionNotification` changed
- ACP-CANCEL-207: `docs/protocol/v2/draft/prompt-lifecycle.mdx:887` overlaps hunk `-887,1 +963,3`; `#/$defs/IdleStateUpdate/anyOf/6`: `IdleStateUpdate` changed
- ACP-CANCEL-208: `docs/protocol/v2/draft/session-setup.mdx:360-366` overlaps hunk `-362,1 +391,1`, `-366,1 +395,1`
- ACP-CANCEL-209: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1098-1101` overlaps hunk `-1098,4 +1177,1`; `docs/protocol/v2/draft/cancellation.mdx:33-37` overlaps hunk `-33,2 +40,1`; `#/$defs/RequestPermissionOutcome`: `RequestPermissionOutcome` changed
- ACP-INFO-CANCEL-201: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1115-1117` overlaps hunk `-1116,2 +1192,1`
- ACP-INFO-CANCEL-202: `docs/protocol/v2/draft/cancellation.mdx:14` overlaps hunk `-14,1 +14,1`; `docs/protocol/v2/draft/cancellation.mdx:57` overlaps hunk `-57,1 +63,1`
- ACP-TRANSPORT-201: `docs/protocol/v2/draft/transports.mdx:23-24` overlaps hunk `-23,2 +20,1`; `#/anyOf/2`: `(root)` changed; `#/anyOf/3`: `(root)` changed
- ACP-JSONRPC-001: `docs/protocol/v2/draft/transports.mdx:76-81` overlaps hunk `-57,47 +59,11`; `#/anyOf/3/items`: `(root)` changed
- ACP-JSONRPC-002: `#/anyOf/3/items`: `(root)` changed
- ACP-JSONRPC-003: `docs/protocol/v2/draft/transports.mdx:76-79` overlaps hunk `-57,47 +59,11`
- ACP-JSONRPC-004: `docs/protocol/v2/draft/extensibility.mdx:193-204` overlaps hunk `-193,1 +202,1`
- ACP-JSONRPC-005: `docs/protocol/v2/draft/overview.mdx:191-197` overlaps hunk `-191,1 +221,1`; `docs/protocol/v2/draft/extensibility.mdx:193-204` overlaps hunk `-193,1 +202,1`
- ACP-BATCH-201: `docs/protocol/v2/draft/transports.mdx:69-71` overlaps hunk `-57,47 +59,11`; `#/anyOf/2/minItems`: `(root)` changed; `#/anyOf/3/minItems`: `(root)` changed; `#/anyOf/4/minItems`: `(root)` changed; `#/anyOf/5/minItems`: `(root)` changed
- ACP-BATCH-202: `docs/protocol/v2/draft/transports.mdx:78-79` overlaps hunk `-57,47 +59,11`; `docs/protocol/v2/draft/transports.mdx:82-84` overlaps hunk `-57,47 +59,11`
- ACP-BATCH-203: `docs/protocol/v2/draft/transports.mdx:85-87` overlaps hunk `-57,47 +59,11`
- ACP-BATCH-204: `docs/protocol/v2/draft/transports.mdx:74-77` overlaps hunk `-57,47 +59,11`
- ACP-BATCH-205: `docs/protocol/v2/draft/transports.mdx:80-81` overlaps hunk `-57,47 +59,11`
- ACP-BATCH-206: `docs/protocol/v2/draft/transports.mdx:72-73` overlaps hunk `-57,47 +59,11`
- ACP-BATCH-207: `docs/protocol/v2/draft/transports.mdx:59-63` overlaps hunk `-57,47 +59,11`; `#/anyOf/4/items`: `(root)` changed
- ACP-BATCH-208: `docs/protocol/v2/draft/transports.mdx:94-97` overlaps hunk `-57,47 +59,11`
- ACP-INFO-BATCH-201: `docs/protocol/v2/draft/transports.mdx:67-68` overlaps hunk `-57,47 +59,11`
- ACP-INFO-BATCH-202: `#/anyOf/2`: `(root)` changed; `#/anyOf/3`: `(root)` changed
- ACP-SESSION-203: `#/$defs/NewSessionRequest/properties/mcpServers`: `NewSessionRequest` changed; `#/$defs/NewSessionRequest/required`: `NewSessionRequest` changed
- ACP-RESUME-201: `docs/protocol/v2/draft/session-setup.mdx:129-130` overlaps hunk `-129,2 +144,2`; `#/$defs/ResumeSessionRequest`: `ResumeSessionRequest` changed; `#/$defs/ResumeSessionResponse`: `ResumeSessionResponse` changed
- ACP-RESUME-202: `docs/protocol/v2/draft/session-setup.mdx:123` overlaps hunk `-123,1 +138,1`; `docs/protocol/v2/draft/session-setup.mdx:212-215` overlaps hunk `-206,10 +236,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:483-493` overlaps hunk `-483,1 +561,1`, `-488,1 +566,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:966` overlaps hunk `-966,1 +1044,3`
- ACP-RESUME-203: `docs/protocol/v2/draft/session-setup.mdx:164-169` overlaps hunk `-167,1 +182,1`, `-169,1 +184,1`
- ACP-RESUME-204: `docs/protocol/v2/draft/session-setup.mdx:261-266` overlaps hunk `-265,1 +286,1`; `#/$defs/PromptResponse/properties/messageId`: `PromptResponse` changed
- ACP-RESUME-205: `docs/protocol/v2/draft/session-setup.mdx:279-292` overlaps hunk `-283,1 +303,1`
- ACP-RESUME-206: `#/$defs/ResumeSessionResponse`: `ResumeSessionResponse` changed
- ACP-RESUME-207: `#/$defs/ResumeSessionRequest/properties/replayFrom`: `ResumeSessionRequest` changed; `#/$defs/ReplayFrom/anyOf/1`: `ReplayFrom` changed
- ACP-RESUME-208: `#/$defs/ResumeSessionRequest/properties/replayFrom`: `ResumeSessionRequest` changed
- ACP-RESUME-209: `docs/protocol/v2/draft/session-setup.mdx:192-195` overlaps hunk `-194,2 +209,1`; `#/$defs/UpdateSessionNotification`: `UpdateSessionNotification` changed
- ACP-LIST-201: `docs/protocol/v2/draft/session-list.mdx:10` overlaps hunk `-10,1 +10,1`; `#/$defs/ListSessionsResponse`: `ListSessionsResponse` changed
- ACP-LIST-203: `docs/protocol/v2/draft/session-list.mdx:63-66` overlaps hunk `-64,2 +64,5`
- ACP-LIST-204: `docs/protocol/v2/draft/overview.mdx:188` overlaps hunk `-188,1 +218,1`
- ACP-CLOSE-201: `docs/protocol/v2/draft/session-setup.mdx:338-340` overlaps hunk `-338,2 +365,4`; `docs/protocol/v2/draft/session-setup.mdx:360-376` overlaps hunk `-362,1 +391,1`, `-366,1 +395,1`; `#/$defs/CloseSessionRequest`: `CloseSessionRequest` changed; `#/$defs/CloseSessionResponse`: `CloseSessionResponse` changed
- ACP-CLOSE-202: `docs/protocol/v2/draft/session-setup.mdx:360-364` overlaps hunk `-362,1 +391,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:304` overlaps hunk `-304,1 +374,1`
- ACP-CLOSE-204: `docs/protocol/v2/draft/session-setup.mdx:366` overlaps hunk `-366,1 +395,1`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:304` overlaps hunk `-304,1 +374,1`
- ACP-DELETE-201: `docs/protocol/v2/draft/session-delete.mdx:94` overlaps hunk `-93,2 +94,2`; `#/$defs/DeleteSessionResponse`: `DeleteSessionResponse` changed
- ACP-DELETE-202: `docs/protocol/v2/draft/session-delete.mdx:94` overlaps hunk `-93,2 +94,2`
- ACP-ADDDIRS-201: `docs/protocol/v2/draft/session-setup.mdx:383-411` overlaps hunk `-385,2 +416,1`, `-409,1 +439,1`; `#/$defs/NewSessionRequest/properties/additionalDirectories`: `NewSessionRequest` changed
- ACP-ADDDIRS-202: `docs/protocol/v2/draft/session-setup.mdx:385-386` overlaps hunk `-385,2 +416,1`; `docs/protocol/v2/draft/session-setup.mdx:409` overlaps hunk `-409,1 +439,1`; `#/$defs/ResumeSessionRequest/properties/additionalDirectories`: `ResumeSessionRequest` changed
- ACP-FORK-201: `#/$defs/ForkSessionResponse`: `ForkSessionResponse` changed; `#/$defs/SessionCapabilities/properties/fork`: `SessionCapabilities` changed
- ACP-SYSPROMPT-201: `docs/protocol/v2/draft/session-setup.mdx:441-445` overlaps hunk `-443,1 +475,1`; `#/$defs/SystemPromptMode/anyOf/0`: `SystemPromptMode` changed
- ACP-SYSPROMPT-202: `docs/protocol/v2/draft/initialization.mdx:238-244` overlaps hunk `-239,3 +299,3`; `#/$defs/SessionSystemPromptModeCapabilities`: `SessionSystemPromptModeCapabilities` changed
- ACP-MCP-201: `docs/protocol/v2/draft/session-setup.mdx:508-558` overlaps hunk `-508,1 +555,1`, `-534,1 +581,1`, `-537,1 +584,1`; `#/$defs/McpServerStdio`: `McpServerStdio` changed
- ACP-MCP-202: `docs/protocol/v2/draft/session-setup.mdx:560-608` overlaps hunk `-560,1 +607,3`, `-577,2 +626,1`, `-581,1 +629,1`, `-584,1 +632,1`, `-601,4 +648,0`; `#/$defs/McpServerHttp`: `McpServerHttp` changed
- ACP-CONFIG-201: `docs/protocol/v2/draft/session-config-options.mdx:93-146` overlaps hunk `-93,1 +93,1`, `-107,1 +107,1`, `-112,1 +112,1`, `-121,1 +121,4`, `-124,1 +127,6`, `-127,1 +135,1`, `-141,1 +149,1`, `-144,3 +152,3`; `#/$defs/SessionConfigOption`: `SessionConfigOption` changed; `#/$defs/SessionConfigSelectOptions`: `SessionConfigSelectOptions` changed; `#/$defs/SessionConfigSelectOption`: `SessionConfigSelectOption` changed; `#/$defs/SessionConfigSelectGroup`: `SessionConfigSelectGroup` changed; `#/$defs/SessionConfigSelect`: `SessionConfigSelect` changed
- ACP-CONFIG-202: `docs/protocol/v2/draft/session-config-options.mdx:324-329` overlaps hunk `-325,4 +368,3`; `#/$defs/SetSessionConfigOptionResponse`: `SetSessionConfigOptionResponse` changed
- ACP-CONFIG-203: `docs/protocol/v2/draft/session-setup.mdx:94` overlaps hunk `-94,1 +108,1`; `docs/protocol/v2/draft/session-setup.mdx:313-315` overlaps hunk `-313,1 +333,1`; `#/$defs/ResumeSessionResponse/properties/configOptions`: `ResumeSessionResponse` changed
- ACP-CONFIG-204: `docs/protocol/v2/draft/session-config-options.mdx:116-125` overlaps hunk `-121,1 +121,4`, `-124,1 +127,6`; `docs/protocol/v2/draft/session-config-options.mdx:214` overlaps hunk `-214,1 +222,1`; `#/$defs/SessionConfigSelect`: `SessionConfigSelect` changed
- ACP-CONFIG-206: `docs/protocol/v2/draft/session-config-options.mdx:331-386` overlaps hunk `-333,1 +375,5`, `-346,0 +393,2`, `-352,1 +400,2`, `-356,1 +405,2`, `-362,0 +413,1`, `-368,1 +419,2`, `-372,1 +424,19`, `-374,0 +445,7`, `-384,1 +461,1`; `#/$defs/ConfigOptionUpdate`: `ConfigOptionUpdate` changed
- ACP-AUTH-201: `#/$defs/AuthMethod`: `AuthMethod` changed
- ACP-AUTH-202: `docs/protocol/v2/draft/authentication.mdx:151-154` overlaps hunk `-153,2 +151,1`; `#/$defs/AuthMethodTerminal`: `AuthMethodTerminal` changed; `#/$defs/AuthCapabilities`: `AuthCapabilities` removed; `#/$defs/TerminalAuthCapabilities`: `TerminalAuthCapabilities` changed
- ACP-AUTH-203: `#/$defs/LogoutAuthRequest`: `LogoutAuthRequest` changed; `#/$defs/LogoutAuthResponse`: `LogoutAuthResponse` changed; `#/$defs/AgentAuthCapabilities`: `AgentAuthCapabilities` changed
- ACP-AUTH-204: `docs/protocol/v2/draft/authentication.mdx:51-54` overlaps hunk `-51,2 +51,1`, `-54,1 +53,1`; `#/$defs/LoginAuthRequest/required`: `LoginAuthRequest` changed; `#/$defs/LoginAuthResponse`: `LoginAuthResponse` changed
- ACP-AUTH-205: `docs/protocol/v2/draft/schema.mdx:785` overlaps hunk `-785,1 +954,1`
- ACP-AUTH-206: `docs/protocol/v2/draft/extensibility.mdx:224-234` overlaps hunk `-224,1 +233,1`, `-233,1 +242,6`; `#/$defs/AuthMethod`: `AuthMethod` changed
- ACP-AUTH-207: `#/$defs/AuthMethodTerminal/properties/env`: `AuthMethodTerminal` changed; `#/$defs/EnvVariable`: `EnvVariable` changed
- ACP-PATCH-201: `#/$defs/ContentChunk`: `ContentChunk` changed; `#/$defs/UserMessage`: `UserMessage` changed; `#/$defs/AgentMessage`: `AgentMessage` changed; `#/$defs/AgentThought`: `AgentThought` changed
- ACP-PATCH-203: `docs/protocol/v2/draft/prompt-lifecycle.mdx:298` overlaps hunk `-298,1 +368,1`
- ACP-PATCH-204: `#/$defs/ToolCallUpdate`: `ToolCallUpdate` changed; `#/$defs/ToolCallContentChunk`: `ToolCallContentChunk` changed; `#/$defs/TerminalOutput`: `TerminalOutput` changed; `#/$defs/TerminalExitStatus`: `TerminalExitStatus` changed
- ACP-PATCH-205: `#/$defs/PlanUpdateContent`: `PlanUpdateContent` changed
- ACP-PATCH-206: `docs/protocol/v2/draft/tool-calls.mdx:413-419` overlaps hunk `-414,1 +494,1`
- ACP-PATCH-207: `docs/protocol/v2/draft/tool-calls.mdx:478-482` overlaps hunk `-481,1 +569,1`
- ACP-PATCH-208: `docs/protocol/v2/draft/tool-calls.mdx:42-55` overlaps hunk `-49,1 +48,1`
- ACP-ENUM-201: `docs/protocol/v2/draft/tool-calls.mdx:77` overlaps hunk `-77,1 +76,1`; `docs/protocol/v2/draft/tool-calls.mdx:380` overlaps hunk `-380,1 +419,42`; `docs/protocol/v2/draft/agent-plan.mdx:160` overlaps hunk `-160,1 +164,1`; `docs/protocol/v2/draft/agent-plan.mdx:172` overlaps hunk `-172,1 +176,1`
- ACP-ENUM-203: `#/$defs/RequestPermissionOutcome/anyOf/2`: `RequestPermissionOutcome` changed
- ACP-EXT-001: `docs/protocol/v2/draft/extensibility.mdx:156` overlaps hunk `-156,1 +165,1`; `docs/protocol/v2/draft/extensibility.mdx:222` overlaps hunk `-222,1 +231,1`
- ACP-META-001: `docs/protocol/v2/draft/extensibility.mdx:89-93` overlaps hunk `-89,1 +97,4`, `-91,3 +102,1`
- ACP-META-201: `#/$defs/UpdateSessionNotification/properties/_meta`: `UpdateSessionNotification` changed
- ACP-EXT-201: `docs/protocol/v2/draft/extensibility.mdx:222` overlaps hunk `-222,1 +231,1`
- ACP-EXT-202: `docs/protocol/v2/draft/extensibility.mdx:239-245` overlaps hunk `-241,1 +255,1`, `-245,1 +259,3`
- ACP-EXT-203: `#/$defs/ProtocolLevelNotification`: `ProtocolLevelNotification` removed
- ACP-ERROR-001: `#/$defs/Error`: `Error` changed
- ACP-SCHEMA-002: `docs/protocol/v2/draft/extensibility.mdx:226-233` overlaps hunk `-233,1 +242,6`
- ACP-INFO-PARSE-001: cites all of `docs/protocol/v2/draft/error.mdx`, which changed
- ACP-INFO-INVALIDREQ-001: cites all of `docs/protocol/v2/draft/error.mdx`, which changed

## Summary

- Changed files: 50 (19 draft docs, 6 schema files, 25 RFDs); doc hunks: 1238.
- `$defs`: 47 added, 2 removed, 181 changed; closure: 5.
- Links into changed docs: 580.
- Affected entries: 112 requirements, 0 ledger entries.
- Core hit: **yes, escalate** (`docs/protocol/v2/draft/prompt-lifecycle.mdx` > `(intro)`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Session Updates > (intro)`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Session Updates > Entity IDs`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Foreground and Background Work`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Prompt Lifecycle > (intro)`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `1. User Message`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `2. Prompt Accepted`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `3. Agent Reports Output > (intro)`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `4. Report Completion > (intro)`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `5. Tool Invocation and Status Reporting`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `6. Continue Conversation`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Stop Reasons`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Failures`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Session States`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Cancellation`; `docs/protocol/v2/draft/extensibility.mdx`; `docs/protocol/v2/draft/initialization.mdx`; `docs/protocol/v2/draft/session-setup.mdx` > `Creating a Session`; `docs/protocol/v2/draft/session-setup.mdx` > `Initial Session State`; `docs/protocol/v2/draft/session-setup.mdx` > `Resuming Sessions`; `docs/protocol/v2/draft/session-setup.mdx` > `Closing Active Sessions`; `docs/protocol/v2/draft/session-setup.mdx` > `Session ID`; `docs/protocol/v2/draft/session-setup.mdx` > `Working Directory`; `docs/protocol/v2/draft/overview.mdx` > `Agent > Baseline Methods`; `docs/protocol/v2/draft/overview.mdx` > `Argument requirements`; `docs/protocol/v2/draft/overview.mdx` > `Error Handling`; `docs/protocol/v2/draft/overview.mdx` > `Conventions`; `docs/protocol/v2/draft/transports.mdx`; `$defs/ErrorCode`; `$defs/SessionUpdate`; `$defs/ContentBlock`; `$defs/AgentCapabilities`; `$defs/ClientCapabilities`)

~~~
