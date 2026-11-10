# v1 impact: `docs/protocol/v1/draft/initialization.mdx` (beac4ba9 -> 3961af94)

**Sources checked:** agent-client-protocol (spec) worktree `agent-client-protocol-2`, base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a` (2026-11-10); files read via `git show <rev>:<path>`: `docs/protocol/v1/draft/initialization.mdx` (whole, both revs), `docs/protocol/v1/draft/agent-plan.mdx` (target + diff), `docs/protocol/v1/draft/session-list.mdx` (archive section only), `schema/v1/schema.unstable.json` and `schema/v1/meta.unstable.json` (target vs base, relevant `$defs`). acp-tck working tree on `eugenethedev/update-spec`: `src/tck/v1/requirements.py`, `src/tck/v1/__init__.py`, `src/tck/v1/conformance/{_helpers,test_initialize,test_client_capabilities,test_session_capabilities}.py`, `src/tck/common/plugin.py` (`capability_is_supported`), `spec-tracker/maps/v1.toml`, `spec-tracker/src/spec_tracker/impact.py` (`ref_closure`, core-def hits). Reference SDKs were not consulted: no requirement here depends on runtime behaviour the spec leaves implicit.
**Confidence:** high. The doc changes are mostly wording and new capability declarations, and the schema already had the "new" constraints at base. The one judgment-heavy item (stale "Unstable feature." text on SYSPROMPT rows) is cross-checked against both doc and schema.

## Answer

No existing initialization-backed requirement changes meaning, tier, or capability gate. The doc changes are wording (Rust `ContentBlock::X` names replaced by wire names, headings lowercased), documentation for capabilities that were already in the base schema (`clientCapabilities.plan`), and declarations of new unstable capabilities (`auth.status`, `sessionCapabilities.archive/status/title`) whose behaviour rules live in other docs and RFDs. `Implementation.name`/`version` being "required" only matches the doc to the schema, which already had `required: ["name","version"]` at base. So ACP-INIT-004 stays ADVISORY: `agentInfo` itself is still SHOULD/optional, and a present-but-incomplete `agentInfo` already fails ACP-INIT-001's schema check. The fallout is citation remaps (six of them in hunks that `spec-impact` will list for review), adding the new `plan` section to ACP-CLIENTCAP-006's citation, and removing the now-stale "Unstable feature." text from ACP-SYSPROMPT-001..003, because `systemPrompt` was stabilized in both doc and schema. The mock client should keep advertising `clientCapabilities: {}`, without `plan`. `SessionCapabilities` does not need to join `core_defs`, because the `$ref` closure already turns any change to it into an `AgentCapabilities` core hit.

## Summary table

| Id | Classification | Note |
|----|----------------|------|
| ACP-INIT-001 | unchanged | `:57` unchanged. `InitializeResponse` changed only in description URLs. |
| ACP-INIT-002 | unchanged | `:99` unchanged (only the heading above, `:95`, was re-cased). |
| ACP-INIT-003 | unchanged | `:97-101` unchanged. |
| ACP-INIT-004 | citation-only (mechanical shift) + optional citation addition | `:57,323` -> `:57,369`. Optionally add `:371,382` (`required` markers). Tier stays ADVISORY (DECISION NEEDED, recommend keep). |
| ACP-SCHEMA-001 | unchanged | Validates against the vendored schema root. New defs are picked up by the schema refresh. |
| ACP-SCHEMA-002 | unchanged | Doesn't cite this doc. `InitializeResponse` root keys unchanged. |
| ACP-PROMPT-001 | citation-only (in a changed hunk, Needs review) | `initialization.mdx:247` -> `:264`. Wording changed from `ContentBlock::Text` to `text`, same meaning. |
| ACP-PROMPT-002 | citation-only (mechanical shift) | `initialization.mdx:289` -> `:313`. |
| ACP-PROMPT-003 | citation-only (in a changed hunk, Needs review) | `:247` -> `:264`. The registry text is still accurate. |
| ACP-PROMPTCAP-001 | citation-only (in a changed hunk, Needs review) | `:249-253` -> `:266-270`. |
| ACP-PROMPTCAP-002 | citation-only (in a changed hunk, Needs review) | `:255-257` -> `:272-274`. |
| ACP-PROMPTCAP-003 | citation-only (in a changed hunk, Needs review) | `:259-261` -> `:276-278`. |
| ACP-CONFIG-003 | citation-only (in a changed hunk, Needs review; remap is risky) | `:172-181` -> `:189-198`. The new Plan section was inserted at base line 172. |
| ACP-AUTH-002 | unchanged | `:123-127` unchanged. |
| ACP-AUTH-006 | unchanged | `:123-127` unchanged. |
| ACP-AUTH-004 | unchanged | Doesn't cite this doc. Its gate `agentCapabilities.auth.logout` is unchanged and only gained a sibling `status`. Optionally cite `initialization.mdx:295-298`. |
| ACP-CLIENTCAP-001 | unchanged | Doesn't cite this doc. `FileSystemCapabilities` changed only in a description URL. |
| ACP-CLIENTCAP-002 | unchanged | Doesn't cite this doc. |
| ACP-CLIENTCAP-003 | unchanged | `:160-166` unchanged. |
| ACP-CLIENTCAP-004 | citation-only (mechanical shift) | `:211-217` -> `:228-234`. |
| ACP-CLIENTCAP-005 | citation-only (mechanical shift) | `:193-199` -> `:210-216`. |
| ACP-CLIENTCAP-006 | changed citation (addition) | Add `initialization.mdx:172-179`, the new doc home of `clientCapabilities.plan`. Text, tier, and test unchanged. |
| ACP-CLIENTCAP-007 | unchanged | Doesn't cite this doc. |
| ACP-SYSPROMPT-001/002/003 | changed text | Remove "Unstable feature." because `systemPrompt` is now stable (`initialization.mdx:340-346`, schema). Gate and tier unchanged. These rows cite `session-setup.mdx`, so coordinate with that doc's researcher. |
| (new candidate) ACP-LIST-003 | new, owned elsewhere | "Advertising `sessionCapabilities.archive` requires advertising `sessionCapabilities.list`" (unstable). It is stated in `session-list.mdx:229` and the schema, not in this doc. Listed so it isn't lost. |
| Ledger L1-L3 | new deliberate non-requirements (proposed) | L1 "support all peer-capability combinations", L2 "Agent SHOULD specify capabilities", L3 client-side initialization rules. |

## Requirements (rules in the target doc, by tier)

| # | Requirement | Tier | Citation (@ 3961af94fa62) | TCK row |
|---|-------------|------|---------------------------|---------|
| 1 | Client MUST call `initialize` before a session, with its latest version and capabilities. It SHOULD send name/version. | MUST/SHOULD (client) | `initialization.mdx:24-29` | ledger L3 |
| 2 | Agent MUST respond with the chosen version and its capabilities. It SHOULD send name/version. | MUST / SHOULD | `:57` | INIT-001 / INIT-004 |
| 3 | Same version if supported, otherwise the latest supported | MUST | `:99` | INIT-002, INIT-003 |
| 4 | Client SHOULD close on an unsupported version | SHOULD (client) | `:101` | ledger L3 |
| 5 | Support all combinations of peer capabilities | SHOULD | `:107` | ledger L1 |
| 6 | Treat omitted capabilities as UNSUPPORTED | MUST | `:109` | basis of CLIENTCAP-001..007, CONFIG-003, AUTH-002 |
| 7 | `plan` omitted/null: the agent uses the `plan` update instead of `plan_update`/`plan_removed` | descriptive here; MUST in `agent-plan.mdx:53` | `:174-179` | CLIENTCAP-006 |
| 8 | Boolean config options only when the client advertises them | descriptive here; MUST NOT in `session-config-options.mdx` | `:189-198` | CONFIG-003 |
| 9 | No compaction updates without `session.compaction` | "must not" (lower case) | `:210-216` | CLIENTCAP-005 |
| 10 | No `notice` without `session.notices` | "must not" (lower case) | `:228-234` | CLIENTCAP-004 |
| 11 | Agent SHOULD specify capabilities | SHOULD | `:246` | ledger L2 |
| 12 | Baseline `text` + `resource_link` prompt support | MUST | `:264` | PROMPT-001, PROMPT-003 |
| 13 | `image`/`audio`/`resource` only when advertised | MAY / capability:promptCapabilities.* | `:266-278` | PROMPTCAP-001..003 |
| 14 | `auth.status` declares `auth/status` + `auth/status_update` (Unstable) | capability:auth.status | `:300-305` | none (see Open questions) |
| 15 | Baseline `session/new`, `session/prompt`, `session/cancel`, `session/update` | MUST | `:313` | SESSION-001, PROMPT-001/002, CANCEL-* |
| 16 | `archive` / `status` / `title` capability declarations (Unstable) | capability:sessionCapabilities.{archive,status,title} | `:323-329`, `:348-360` | none (scoping question already open in spec-diff-v1.md) |
| 17 | `systemPrompt` capability, now stable | capability:sessionCapabilities.systemPrompt | `:340-346` | SYSPROMPT-001..003 |
| 18 | `Implementation.name`, `.version` required; `title` optional, omitted == null | schema-required inside the object | `:371-385` | INIT-001 (schema), INIT-004 |

## Details

### What changed in the doc (all hunks)

- Heading re-casing only: `:95`, `:117`, `:121`, `:133`, `:189`, `:208`, `:226`, `:244`, `:293`, `:311`, `:367`. Slugs are unchanged, so no inbound anchor breaks. All inbound `initialization#...` links at target point to `client-capabilities`, `agent-capabilities`, `prompt-capabilities`, `session-capabilities`, or `filesystem`. The last one was already a stale slug at base and comes from the generated `schema.mdx:4883` and the schema's `FileSystemCapabilities` description.
- New `#### Plan operations` section, `:172-187` (ParamField `:174-179`).
- Rust identifiers replaced by wire names: `:264`, `:269`, `:273`, `:277`.
- New `auth.status` ResponseField `:300-305` (Unstable).
- New `sessionCapabilities.archive` `:323-329`, `status` `:348-352`, and `title` `:354-360` (all Unstable).
- `systemPrompt` `:340-346`: the "**Unstable.**" prefix was dropped and the anchor changed from `#system-prompt-unstable` to `#system-prompt`.
- Implementation info: `name` `:371` and `version` `:382` gained `required`. `title` `:376-380` gained "Optional. Omitted and `null` are equivalent." The `<Info>` at `:387-389` still says this information "will be required" in future versions, which refers to `clientInfo`/`agentInfo` themselves.

### Schema at target (only the parts that matter)

- `Implementation.required` is `["name","version"]` at **both** base and target. Only the descriptions changed. `InitializeResponse.properties.agentInfo` is still `anyOf [Implementation, null]` with the "in future versions ... required" note, and `InitializeResponse.required` is still `["protocolVersion"]`.
- `ClientCapabilities.properties.plan` and `$defs/PlanCapabilities` exist at both revisions with identical shape, and both are still marked `**UNSTABLE**`.
- `SessionCapabilities` gained `archive`, `status`, and `title`, each `anyOf [<X>Capabilities, null]` with `x-deserialize-default-on-error`. The `systemPrompt` description lost its UNSTABLE banner, and so did `SessionSystemPromptCapabilities`, `SystemPrompt`, `SystemPromptMode`, `SessionSystemPromptModeCapabilities`, and `NewSessionRequest.properties.systemPrompt`. `SessionCapabilities.properties.archive.description` adds "Agents that advertise it MUST also advertise `sessionCapabilities.list`."
- `AgentAuthCapabilities` gained `status` (`anyOf [AuthStatusCapabilities, null]`, UNSTABLE).
- `PromptCapabilities`, `McpCapabilities`, `ClientSessionCapabilities`, `AgentCapabilities`, `ClientCapabilities`, `InitializeRequest/Response`, `LogoutCapabilities`, and `FileSystemCapabilities` changed only in descriptions: wire names instead of Rust paths, doc URLs now under `/protocol/v1/draft/`, punctuation.
- `meta.unstable.json` at target adds `session/archive`, `session/unarchive`, `session/status`, `session/set_title`, `auth/status` (agent methods) and `auth/status_update` (agent notification), so `tck.v1.protocol` will pick them up on refresh.

### Per-row notes

**ACP-INIT-004 (DECISION NEEDED: tier; recommendation: keep ADVISORY).** Someone could read "`name` ... required" (`:371`, `:382`) as making `agentInfo` mandatory. It doesn't. The surrounding sentence is still "Agents SHOULD provide" (`:369`), the `<Info>` at `:387-389` says it becomes required only in future versions, and the schema keeps `agentInfo` optional and nullable. "Required" applies only within a present object, and ACP-INIT-001's schema validation already enforces that (the schema had `required: ["name","version"]` at base, so this is not a new check). The test (`test_initialize.py::test_agent_info_present`) still matches. Citation: `initialization.mdx:57,369`. Optionally add `:371,382`.

**ACP-PROMPT-001 / ACP-PROMPT-003.** Line 247 became line 264. The new text says "`text` and `resource_link` content blocks" where the old text had `ContentBlock::Text`/`ContentBlock::ResourceLink`. The meaning is identical, and the schema's `PromptCapabilities.description` made the same substitution. PROMPT-003's registry text ("make Text and ResourceLink the baseline") is still accurate. No test change.

**ACP-PROMPTCAP-001..003.** The ranges shift by +17 (`266-270`, `272-274`, `276-278`). `spec-impact` flags them because one line in each range is a changed hunk (the wire-name substitution). Gates stay `boolean` paths under `agentCapabilities.promptCapabilities.*`, whose defaults are still `false`. No test change.

**ACP-CONFIG-003 (Needs review; mechanical remap is unsafe).** Base `:172-181` covered the "Boolean Config Options" heading and ParamField. Base line 172 itself falls in hunk `-172,1 +172,18`, where the new Plan section was inserted. A mechanical remap may anchor at 172 and produce a range that starts in the Plan section. The correct target range is `:189-198` (heading `:189`, ParamField `:191-198`). No text, tier, or test change.

**ACP-CLIENTCAP-004 / -005.** Pure shifts (+17): `:228-234` (notices) and `:210-216` (compaction). They don't overlap a hunk, so `--fix` should handle them. Verify after it runs.

**ACP-PROMPT-002.** `:289` -> `:313` (the session-baseline MUST). Pure shift.

**ACP-CLIENTCAP-006 (changed citation).** The doc now documents the gate it relies on. Proposed addition: `docs/protocol/v1/draft/initialization.mdx:172-179`. The new sentence "Omitted or `null` means the Client does not advertise support, and the Agent sends plans with the `plan` update instead" (`:176-177`) restates the `agent-plan.mdx:53` MUST NOT plus MUST-fall-back. From the client side, "falls back to `plan`" adds nothing observable beyond "never sends `plan_update`/`plan_removed`". An agent may legitimately send no plan at all, so a positive fallback check can't be forced. The existing test (`test_client_capabilities.py:151-160`) remains the right assertion. Keep "Unstable feature" in the row text: the schema still marks `plan` UNSTABLE even though this doc no longer says so (see Discrepancies).

**ACP-SYSPROMPT-001/002/003 (changed text).** Each row's text ends "Unstable feature." At target, `initialization.mdx:340-346` drops "**Unstable.**", the anchor became `session-setup#system-prompt`, `session-setup.mdx:385` is now a plain "## System prompt" heading, and every `systemPrompt` schema def lost its UNSTABLE banner. Proposed change: drop "Unstable feature." from all three texts and the "(unstable)" in the `test_session_capabilities.py:459` section comment. Tier (CAPABILITY) and gate (`agentCapabilities.sessionCapabilities.systemPrompt`, object marker) are unchanged. These rows cite `session-setup.mdx`, so the session-setup researcher owns the citation remap. Only the stabilization fact comes from this doc.

**ACP-AUTH-004.** The gate `agentCapabilities.auth.logout` is unchanged. `AgentAuthCapabilities` gained only the sibling `status`. Optional citation addition: `initialization.mdx:295-298`.

**ACP-SCHEMA-001/002.** Neither cites this doc. The new capability properties are additive and nullable. SCHEMA-002 checks only root keys of spec objects, and `InitializeResponse`'s root `properties` are unchanged, so no new false-positive risk.

### New-requirement candidate (owned by session-list; listed so it isn't lost)

- **Proposed id:** ACP-LIST-003 (or whatever the session-list researcher picks).
- **Tier:** CAPABILITY, gated on `agentCapabilities.sessionCapabilities.archive` (object marker). The statement is a MUST that applies only when archive is advertised.
- **Text:** "An agent that advertises `sessionCapabilities.archive` also advertises `sessionCapabilities.list`."
- **Citation:** `docs/protocol/v1/draft/session-list.mdx:229 @ 3961af94fa62`; `schema/v1/schema.unstable.json#/$defs/SessionCapabilities/properties/archive`.
- **Observable:** from the `initialize` result alone, with no method calls.
- **Fixture:** the conforming agent advertising `sessionCapabilities: {archive: {}}` without `list`.
- It is an unstable feature. Whether v1 starts testing the new unstable capabilities is already an open scoping question (`spec-diff-v1.md`, Open questions). This doc only links to the rule and does not state it.

No other new agent-side, client-observable requirement comes from this doc. `auth.status`, `session.status`, and `session.title` declare availability only. Their behaviour rules live in RFDs (`/rfds/get-auth-state`, `/rfds/session-status`, `/rfds/session-set-title`), and `initialization.mdx` links to those RFDs rather than to draft docs.

### Proposed ledger entries (`[[not_requirement]]`)

These rules all existed at base. They are proposed because the ledger is empty, this doc is core, and someone might expect the TCK to test them.

- **L1.** citation `docs/protocol/v1/draft/initialization.mdx:107 @ 3961af94fa62`. Statement: "Clients and Agents SHOULD support all possible combinations of their peer's capabilities." Reason: out of scope. The space of capability combinations is combinatorial. The TCK exercises the empty set (`{}`) plus targeted single-capability connections such as `auth.terminal: true`.
- **L2.** citation `docs/protocol/v1/draft/initialization.mdx:246 @ 3961af94fa62`. Statement: "The Agent SHOULD specify whether it supports the following capabilities." Reason: unobservable. Omission is defined as unsupported (`:109`), so an agent that omits a capability is indistinguishable from one that sets it to false or null.
- **L3.** citation `docs/protocol/v1/draft/initialization.mdx:24-29,97,101,119 @ 3961af94fa62`. Statement: "The Client MUST initialize with its latest supported version and its capabilities before creating a session, SHOULD send `clientInfo`, SHOULD specify its capabilities, and SHOULD close the connection if it doesn't support the Agent's version." Reason: client-side rules. The TCK is the client, so they constrain the harness, not the agent under test. These could be split into separate entries if the ledger prefers one rule per entry.

### Mock client: does `plan` change what it should advertise?

No. Every v1 handshake sends `clientCapabilities: {}`: `connected_agent()` defaults to `{}` (`src/tck/v1/conformance/_helpers.py:46-53`), and the session-scoped `agent_initialize_result` uses `_initialize_params()` (`src/tck/v1/__init__.py:17-18`). With `plan` omitted, the spec requires agents to use only the baseline `plan` update (`agent-plan.mdx:53`, `initialization.mdx:176-177`). ACP-CLIENTCAP-006 depends on the client not advertising `plan`, so adding it would make that requirement untestable. If a future test needs `plan_update` traffic, for example to check "Plan file URIs MUST be absolute" (`agent-plan.mdx:127`), it should open its own connection with `connected_agent(..., client_capabilities={"plan": {}})`, as the AUTH-006 terminal test does. That belongs to the agent-plan researcher.

The harness never sends `clientInfo` in v1 handshakes (only a v2-shaped `info` in the INIT-003 probe). That satisfies the spec, because the client rule is SHOULD (`:29`, `:369`) and the schema keeps `clientInfo` optional. No change is required.

### Should `SessionCapabilities` join `core_defs` in `spec-tracker/maps/v1.toml`?

Recommendation: no, it's redundant. `impact.py:761-767` counts a core def as hit when it is changed directly *or* when it is in `schema.closure`. `ref_closure` (`impact.py:385-404`) puts every def that transitively `$ref`s a changed def into the closure. `AgentCapabilities` refs `SessionCapabilities`, `AgentAuthCapabilities`, and `PromptCapabilities` (via `allOf`/`anyOf`), so any change to them, or to anything they reference, already shows up as an `AgentCapabilities` core hit "via $ref closure of SessionCapabilities". The same holds for `ClientCapabilities` -> `PlanCapabilities`/`ClientSessionCapabilities`. Adding `SessionCapabilities` would only produce a second core-hit line for the same change. Add it only if the map should *name* it as core for documentation reasons, and accept the duplicate report line.

## Testability notes

- None of the classified rows needs a test change except the SYSPROMPT docstring/comment wording (cosmetic).
- The new capability declarations (`auth.status`, `session.archive/status/title`) are observable only as gates. Validation of any `auth/status_update` an agent sends, or of `session/status` responses if the TCK ever calls it, comes automatically from the schema refresh through ACP-SCHEMA-001 or the per-test validators.
- `title` "Omitted and `null` are equivalent" (`:377-378`) is a client-interpretation rule. The schema already allows `null`, so there is nothing to assert agent-side.

## Discrepancies

1. **`plan` stability.** `initialization.mdx:172-179` documents `clientCapabilities.plan` with no "**Unstable.**" marker, while the target schema marks both `ClientCapabilities.properties.plan` and `$defs/PlanCapabilities` `**UNSTABLE**`. `agent-plan.mdx` at target has no "unstable" text either. The other unstable capabilities in this doc (`auth.status`, `archive`, `status`, `title`) are marked Unstable in both doc and schema. Effect on the TCK: none for the tier (CLIENTCAP-006 is a MUST NOT either way). Keep CLIENTCAP-006's "Unstable feature" wording, because the schema is authoritative for this.
2. **`load_session` vs `loadSession`.** The doc's `<Note>` at `:363` still says "top-level `load_session` capability" (a Rust identifier). The schema's `SessionCapabilities.description` was corrected to `loadSession` in this same revision. This is cosmetic and doesn't affect the TCK. The gate `agentCapabilities.loadSession` is correct.
3. **"required" vs "will be required".** `:371`/`:382` mark `name`/`version` required, while `:387-389` says "in future versions ... this information will be required." These are consistent once you see that the first is about fields inside a present object and the second is about the object itself. Both agree with the schema. Listed only because a reader may take them as a conflict (see the INIT-004 decision).
4. **Stale anchor in the generated schema docs.** `FileSystemCapabilities` links `initialization#filesystem`, but the heading slug is `file-system` (at both revisions). This has no TCK impact.

## Open questions

- **ACP-LIST-003 candidate** (archive requires list): route to the session-list researcher and the existing scoping question on new unstable capabilities.
- **`auth/status_update` without the `auth.status` capability:** is an unsolicited notification a violation? `initialization.mdx:300-305` only says the notification "is available". Settling this needs the RFD `docs/rfds/get-auth-state.mdx` and the authentication researcher.
- **SYSPROMPT-001..003 text edit:** confirm with the session-setup researcher, who owns those rows' `session-setup.mdx` citations, so the two reports don't diverge.
- **Plan file URIs MUST be absolute (`agent-plan.mdx:127`):** a candidate for extending ACP-PROMPT-004 or a new row. It needs a connection that advertises `plan: {}`. Route to the agent-plan researcher.
