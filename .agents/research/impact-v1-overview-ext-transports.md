# v1 impact: `overview.mdx`, `extensibility.mdx`, `transports.mdx` (beac4ba -> 3961af94fa62)

**Sources checked:** agent-client-protocol (worktree `agent-client-protocol-2`), base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a` (read via `git show`/`git diff`, checkout not touched); acp-tck working tree on branch `eugenethedev/update-spec` (registry, conformance tests, `spec-tracker/maps/v1.toml`, fixtures). Reference SDKs not consulted: no requirement here depends on runtime behaviour the spec leaves implicit.
**Confidence:** high. All three diffs are small and fully read. Every cited line was checked at both revisions, and the "Conventions" claim was checked mechanically against the whole target schema.

All doc paths below are in the spec repo. "T:" means at target `3961af94fa62`, "B:" means at base `beac4ba`.

## Answer

None of the three docs changes the meaning of any registry row. Every rule the TCK tests is word-for-word the same or only reworded: stdio framing, UTF-8, stderr, the JSON-RPC error and notification rules, the `_` method reservation, the `-32601` "should", ignoring unknown notifications, `_meta`, and no custom root fields. `transports.mdx` lost 3 lines above the stdio section, so six citations shift by -3. `spec-impact --fix` handles that mechanically. The rest are unchanged or have editorial-only overlaps.

The new overview "Conventions" paragraph (camelCase keys, snake_case discriminator values) has no RFC 2119 keyword. It describes the schema and is already enforced through schema validation. Every property key in the target v1 schema is camelCase and every `const` discriminator value is snake_case, so no new row is needed.

The new extension naming guidance (reverse-DNS `com.example/<name>`, `_com.example/<name>`) is best handled as a ledger entry, not a test. The TCK's own probe names (`_tck/does_not_exist`, `_tck/unknown`, `_tck/notify`) and META-001's `_meta` key `"tck"` don't follow that guidance. They are still conforming, because the guidance isn't a MUST and probes only rely on the `_` prefix. Renaming them is an optional cleanup that needs a prefix choice (DECISION NEEDED).

## Summary table

| id | classification | note |
|----|----------------|------|
| ACP-TRANSPORT-001 | citation-only | `transports.mdx:23,24,26` -> `:20,21,23`. Text identical. Mechanical. |
| ACP-TRANSPORT-002 | unchanged | `transports.mdx:6` unchanged. |
| ACP-STDERR-001 | citation-only | `transports.mdx:25` -> `:22`. Mechanical. |
| ACP-SHUTDOWN-001 | citation-only | `transports.mdx:40` -> `:37` (diagram "Close stdin, terminate subprocess"). Mechanical. |
| ACP-INFO-PARSE-001 | citation-only | `transports.mdx:27` -> `:24`. Mechanical. |
| ACP-INFO-INVALIDREQ-001 | citation-only | `transports.mdx:27` -> `:24`. Mechanical. |
| ACP-JSONRPC-002 | unchanged | `overview.mdx:235-239` identical. The new line 241 links to the Errors page (see Open questions). |
| ACP-JSONRPC-003 | unchanged | `overview.mdx:239` identical. |
| ACP-JSONRPC-004 | unchanged | `extensibility.mdx:84-96` identical (v1 still says "should respond with ... -32601"). |
| ACP-JSONRPC-005 | unchanged | Both cited ranges identical. |
| ACP-EXT-001 | unchanged (spec-impact lists it, no action) | Line numbers are the same. `overview.mdx:12` and `extensibility.mdx:47` were reworded editorially with the same meaning. |
| ACP-EXT-002 | unchanged | `extensibility.mdx:113` identical. |
| ACP-META-001 | unchanged (spec-impact lists it, no action) | `extensibility.mdx:13` changed punctuation only. In `PromptRequest._meta`, only the docs URL changed. The test's `_meta` key `"tck"` doesn't follow the new naming guidance (optional cleanup, see below). |
| ACP-SCHEMA-002 | unchanged (spec-impact lists it, no action) | `extensibility.mdx:10-14,43`: line 13 punctuation only. `$defs/Error` is byte-identical at both revisions. |
| ACP-PROMPT-004 | unchanged (for the overview part) | `overview.mdx:230` identical. Its other citations belong to other researchers. |
| ACP-SCHEMA-001 | unchanged | Doesn't cite these docs. Listed because it is the row that already enforces "Conventions". |
| (new) Conventions, `overview.mdx:243-245` | no row, no ledger | Describes the schema with no keyword. Already enforced by ACP-SCHEMA-001. DECISION NEEDED (light): confirm "no action". |
| (new) extension naming, `extensibility.mdx:117` | new ledger entry (recommended) | Guidance, not a MUST. "A domain you control" can't be observed. DECISION NEEDED: ledger (recommended) or an INFORMATIONAL row. |
| (new) Streamable HTTP removal, `transports.mdx:8` | nothing | v1 had no Streamable HTTP rule before, and no row cited it. |

## Details

### transports.mdx

Diff: the transport list at B:8-11 became a single sentence at T:8: "one transport mechanism ... stdio ... A remote transport based on Streamable HTTP is being specified in the transport RFD". The `## _Streamable HTTP_` section at B:44-46 was removed. "Custom Transports" became "Custom transports" (T:41). No stdio bullet changed: T:16-24 is identical to B:19-27. Line 6 (UTF-8 MUST) and line 10 (SHOULD support stdio) are unchanged.

Line remap (offset -3 for B:12-43, i.e. after the first hunk and before the second):

| row | B | T | target text |
|-----|---|---|-------------|
| TRANSPORT-001 | 23,24,26 | 20,21,23 | "Messages are individual JSON-RPC ..." / "delimited by newlines ... MUST NOT contain embedded newlines" / "agent MUST NOT write anything to its stdout that is not a valid ACP message" |
| STDERR-001 | 25 | 22 | "agent MAY write UTF-8 strings to its standard error" |
| INFO-PARSE-001, INFO-INVALIDREQ-001 | 27 | 24 | "client MUST NOT write anything to the agent's stdin that is not a valid ACP message" |
| SHUTDOWN-001 | 40 | 37 | `Client->>Agent Process: Close stdin, terminate subprocess` |

None of these cited lines falls inside a hunk, so spec-impact doesn't list them as affected. `--fix` should remap them; check the result after running it. Tests `test_transport.py`, `test_diagnostics.py` and `test_informational.py` need no change.

There are no dangling anchors. `#streamable-http` is no longer linked from any doc at T, and the only inbound link into this doc is `security.mdx:61` -> `#custom-transports` (new, see map notes).

### overview.mdx

Diff: headings recased (Message flow, Baseline/Optional methods, Error handling, Next steps), bullet rewording at T:12-13, and a `set_mode` schema anchor fix at T:103. There are also three additions:
- T:241: "See [Errors](/protocol/v1/draft/error) for the error codes ACP uses and when to use them."
- T:243-245: new `## Conventions`: "Unless explicitly defined otherwise in the schema, ACP-defined JSON object property keys use `camelCase`. String values carried by discriminator fields use `snake_case`. The JSON-RPC envelope fields (...) follow the JSON-RPC 2.0 specification."
- T:257-264: "Next steps" now links Security first.

The cited ranges 10-12, 230, 235-239 and 239 have the same numbers at T. Only T:12 changed, and only editorially: "Methods are request-response pairs that expect a result or error."

**Conventions analysis.** The paragraph has no MUST/SHOULD/MAY. It describes how ACP-defined keys and values are spelled, and an agent can only "use" ACP-defined keys by emitting the schema's keys. I scanned every `properties` map and every string `const` under every `$def` in T `schema/v1/schema.unstable.json`. The results:
- Non-camelCase property keys: **none**. `_meta` matches `_?camelCase`, so the "unless explicitly defined otherwise" escape is never needed.
- String `const` values on `action`, `mode`, `outcome`, `sessionUpdate`, `state`, `stopReason` and `type` (57 values): **all snake_case**.
- The schema's `discriminator.propertyName` keywords are `type`, `sessionUpdate` and `outcome`, all covered.

So an agent that writes `session_id` for `sessionId`, or `AgentMessageChunk` for `agent_message_chunk`, already fails ACP-SCHEMA-001: either a required key is missing or a `const`/enum doesn't match. If it adds a stray non-camelCase key alongside the right one, that is a custom field, governed by the "no custom root fields" rule (ACP-SCHEMA-002) and not by Conventions. Recommendation: no new requirement and no ledger entry. The rule isn't deliberately untested; it is tested through the schema. DECISION NEEDED (light): confirm.

### extensibility.mdx

Diff: intro reworded (T:6) and headings recased. In the examples, `zed.dev/debugMode` became `com.example/debugMode` (T:31), and the method names became `_com.example/workspace/buffers` (T:62) and `_com.example/file_opened` (T:106). The advertising example changed from a vendor-nested `"zed.dev": {workspace, fileNotifications}` to flat prefixed keys `"com.example/workspace": true`, `"com.example/fileNotifications": true` (T:127-130).

New text at T:117: "Implementations **SHOULD** use the `_meta` field in capability objects to advertise support for extensions and their methods. To avoid collisions with other extensions, follow [MCP's naming convention](...): prefix extension names with dot-separated labels in reverse-DNS order of a domain you control, followed by `/`. For example, use `com.example/<name>` for `_meta` keys, including capability entries, and `_com.example/<name>` for custom methods."

The cited ranges 10-14, 37-43, 47, 56, 69, 84-96 and 113 keep the same numbers. Only 13 (`;` -> `. For`) and 47 (sentence merged, same meaning: `_` names are reserved so they can't clash with future methods) changed. The MUST at T:69, the "should" at T:84, the SHOULD at T:113 and the MUST NOT at T:43 are verbatim. The schema adds no key-naming constraint: no `propertyNames` anywhere, and `_meta` descriptions changed only their docs URL (`/protocol/extensibility` -> `/protocol/v1/draft/extensibility`). `test_extensibility.py` assertions still match.

**Naming convention: proposed ledger entry (recommended).**
- citation: `docs/protocol/v1/draft/extensibility.mdx:117 @ 3961af94fa62`
- statement: Extension names should carry a reverse-DNS prefix of a domain the implementer controls, followed by `/`: `com.example/<name>` for `_meta` keys (including capability entries) and `_com.example/<name>` for custom method names.
- reason: collision-avoidance guidance with no RFC 2119 keyword of its own (the paragraph's SHOULD covers *using `_meta` to advertise*, not the naming). Domain ownership can't be observed. A syntax check can't tell reverse-DNS from forward-DNS (`example.com/` vs `com.example/`). A check would mostly flag legacy unprefixed keys that interoperate fine.

Alternative, if the orchestrator prefers visibility: INFORMATIONAL row `ACP-EXT-003`, no capability gate.
- Text: "Custom `_meta` keys and `_`-prefixed method names that the agent authors carry a `label(.label)*/` prefix; reported, never asserted."
- What it checks: keys of every `_meta` object the agent emits, excluding the reserved `traceparent`/`tracestate`/`baggage` (T:37-41), plus `method` of any agent-to-client `_` request or notification.
- Passes vacuously when there are none.
- Fixture: `unprefixed_meta_key.py`, which advertises `agentCapabilities._meta: {"workspace": true}`.

I recommend the ledger. INFORMATIONAL would be noise for agents that predate the guidance.

### TCK's own probe names vs. the new guidance

Current names:
- v1 methods: `_tck/does_not_exist` (`test_jsonrpc.py:93,135`, `test_extensibility.py:109`, `test_diagnostics.py:28`), `_tck/unknown` (`test_extensibility.py:27`), `_tck/notify` (`test_extensibility.py:46`, `test_jsonrpc.py:157`).
- v1 `_meta` key `"tck"` (`test_extensibility.py:69`).
- v2 uses the same names plus `_tck/ping` and `_tck/notify_only`.
- Fixture-internal methods: `_tck/env`, `_tck/big`, `_fixture/status_update`.

`tck/` is a one-label prefix, not a reverse-DNS domain, so these don't follow T:117. They remain conforming, because the only binding rule is the `_` prefix (T:47, T:56), and what the unknown-method tests need is a name nobody implements, which `_tck/...` provides. The fixtures `unknown_method_no_error.py:15` and `silent_on_unknown_method.py:15` whitelist known names, so a probe rename wouldn't break them.

DECISION NEEDED (cosmetic, does not block this update):
- **A.** Keep `_tck/...`.
- **B. (mild recommendation)** Rename in one cross-version pass (v1 and v2 together, since v2 draft has the same guidance), and update CLAUDE.md "How to add a requirement" step 4 to name the prefix. Pick a prefix the project controls:
  - Do **not** use `com.example` (documentation-reserved, and it's what the spec examples use).
  - Do **not** use any prefix whose second label is `agentclientprotocol`: v2 draft reserves those for ACP itself (`docs/protocol/v2/draft/extensibility.mdx:102 @ 3961af94fa62`), even though the TCK lives at `github.com/agentclientprotocol/acp-tck` (`docs/libraries/testing.mdx:6-7`).
  - The choice of domain belongs to the project owner.
  - Also note that v2 draft reserves *unprefixed* `_meta` keys for ACP (same line 102), so `"tck": True` in v2's `test_extensibility.py:78` / `test_cancel.py:326` sits in reserved space there. That is a v2 concern; route it to the v2 researcher.

Unrelated: `_tck_unsupported` in `test_session_capabilities.py:505` is a `systemPrompt.mode` value, not an extension name, and is out of scope here.

### Spec map entries (`spec-tracker/maps/v1.toml:33-56`)

- All three `path`s exist at T. No `sections` key means whole-doc core, which is still correct; heading recasing can't break them.
- `code` paths all exist. Optional, pre-existing gaps (not caused by this diff):
  - transports could add `src/tck/v1/conformance/test_informational.py` (INFO-PARSE/INVALIDREQ cite transports:24).
  - overview could add `src/tck/v1/conformance/test_prompt.py` (PROMPT-004 cites overview:230).
  - extensibility could add `src/tck/v1/conformance/test_jsonrpc.py` (JSONRPC-004/005 cite extensibility:84-96).
- `reason` staleness:
  - transports `reason` says "no other doc links here". That is no longer true: `security.mdx:61 @ 3961af94fa62` links `#custom-transports`. Suggest dropping that clause.
  - overview `reason` could mention the new key/discriminator naming conventions.
  - extensibility `reason` could mention the extension naming convention.
- Ledger: currently empty. Add the naming-convention entry above if accepted.

Optional ledger candidates from whole-doc review. All are pre-existing and unchanged, so priority is low:
- `transports.mdx:10` "Agents and clients SHOULD support stdio whenever possible". The TCK only drives stdio, so this is vacuous for any agent it can run.
- `transports.mdx:43-45` custom transports MAY/MUST/SHOULD. Out of scope, since the TCK is stdio only.
- `extensibility.mdx:97` and the first sentence of `:117` (SHOULD advertise custom capabilities in `_meta`). Unobservable, because the client can't know which extensions an agent has unless it uses them.

## Testability notes

- The transport, extensibility and JSON-RPC rows keep their current tests unchanged. Re-running the v1 suite after the citation remap is enough.
- Conventions: observable only through schema conformance (ACP-SCHEMA-001). A dedicated casing check would only duplicate it.
- Naming convention: only the syntax is observable (a prefix of dot-separated labels followed by `/`). Reverse order and domain ownership aren't. Custom method names are observable only if the agent sends agent-to-client `_` traffic, which a generic run rarely triggers.

## Discrepancies

None found between the doc text and the schema. The schema is fully consistent with the new Conventions paragraph: no exceptions, so the "unless explicitly defined otherwise" escape isn't used. The ACP text paraphrases MCP's convention. I did not check MCP's own `_meta` naming rules (for example, which prefixes MCP reserves); treat any claim about them as a hypothesis.

## Open questions

- `overview.mdx:241` now points to the new `error.mdx`. Whoever owns `error.mdx` should check whether it tightens any rule behind ACP-JSONRPC-002/004 or ACP-ERROR-*. For example, v1 `extensibility.mdx:84` still says "should" for `-32601`, while v2 draft says MUST (`docs/protocol/v2/draft/extensibility.mdx:202`).
- v2: the reserved unprefixed `_meta` keys and the `agentclientprotocol` second-label reservation (`docs/protocol/v2/draft/extensibility.mdx:102`) affect v2's `"tck"` `_meta` key and any probe-prefix choice. Route to the v2 researcher.
- Pre-existing scope note, not caused by this diff: ACP-SCHEMA-002 checks only top-level `params`/`result` keys, but "MUST NOT add custom fields at the root of a type" (`extensibility.mdx:43`) applies to nested spec types too.
