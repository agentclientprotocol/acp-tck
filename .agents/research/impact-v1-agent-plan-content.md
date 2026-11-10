# v1 spec update impact: `agent-plan.mdx` and `content.mdx` (beac4ba9 -> 3961af94)

**Sources checked:** agent-client-protocol (worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`) base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a` (2026-11-10). Read via `git show`/`git diff` only. acp-tck working tree at `200baba` (registry, conformance tests, `_helpers.py`, fixtures, `spec-tracker/maps/v1.toml`). Reference SDKs were **not** consulted: none of the rules below depends on runtime behaviour the spec leaves implicit. The one ambiguity (what "absolute" means for a URI) is a reading of RFC 3986/8089, not something SDK behaviour would settle.
**Confidence:** high for the classifications. Medium for the two proposed PLAN rows: the tier and URI-interpretation calls are flagged DECISION NEEDED.

## Summary table

| Id | Classification | Note |
|----|----------------|------|
| ACP-CLIENTCAP-006 | unchanged | `agent-plan.mdx:10,53` and `prompt-turn.mdx:25-26` still say the same thing at the same lines. spec-impact lists it only because the whole `prompt-turn.mdx` table hunk was rewritten and the `_meta` link in `PlanCapabilities` changed. The test still matches. |
| ACP-PROMPT-001 | unchanged (for these docs) | `content.mdx:31` is unchanged. Its `initialization.mdx:247` citation moves to `:264` at target. That belongs to the initialization researcher, and `--fix` remaps it. |
| ACP-PROMPT-002 | unchanged | Does not cite these docs. Validating against the schema now also covers `plan_update` shapes if the TCK ever advertises `plan` (see below). |
| ACP-PROMPT-003 | changed text + citation | content.mdx now states the resource-link MUST outright (`content.mdx:170`). The row's rationale ("`content.mdx:31` only mentions text but does not exclude `resource_link`") is out of date. The test needs no change. |
| ACP-PROMPTCAP-001 | unchanged | `content.mdx:54-56` has the same text at the same lines. `ImageContent`/`PromptCapabilities` changed only in descriptions. |
| ACP-PROMPTCAP-002 | unchanged | Does not cite content.mdx. Optionally add `content.mdx:87-89` for symmetry with 001/003 (not required). |
| ACP-PROMPTCAP-003 | unchanged | `content.mdx:122-125` has the same text at the same lines (123-125 is the note, 122 is blank, as at base). |
| ACP-PLAN-* / ACP-CONTENT-* | none exist | -- |
| **ACP-PLAN-001** (proposed) | new, MANDATORY (vacuous) | `plan_update` with `type:"file"` carries an absolute URI (`agent-plan.mdx:127`). Needs a connection that advertises `plan: {}`. |
| **ACP-PLAN-002** (proposed) | new, ADVISORY -- DECISION NEEDED | Once the client advertises `plan`, the agent sends plans via `plan_update`, not `plan` (`agent-plan.mdx:57`). |
| Ledger L1 | new non-requirement | The agent MUST send the complete entry list in each update (`:179`, `:181`). Unobservable. |
| Ledger L2 | new non-requirement | The agent SHOULD send `plan_removed` when a plan is cancelled (`:147`). Unobservable. |
| Ledger L3 | new non-requirement | Clients MUST ignore `plan_removed` for an unknown `planId` (`:147`). Client-side. |
| Ledger L4 | new non-requirement | Client replacement semantics (`:59`, `:179`, `:181`). Client-side. |

## Answer

Both docs' changes are almost entirely prose, headings and links. The schema `$defs` (`Plan*`, `PlanCapabilities`, `ContentBlock`, `ResourceLink`, `EmbeddedResource`, `ImageContent`, `AudioContent`, `TextContent`, `PromptCapabilities`) changed **only in `description` strings**: `_meta` doc links now point to `/protocol/v1/draft/extensibility`, Rust-style `[ContentBlock::Text]` became `` `text` ``, and the `ContentBlock` intro was trimmed. No structural changes. No existing row needs a tier or test change. ACP-PROMPT-003 needs its rationale and citation updated because content.mdx now states the resource-link MUST directly.

agent-plan.mdx adds agent-side rules. Only two of them can be observed from the client side, and only if the TCK's mock client advertises `clientCapabilities.plan`. **It never does today.** `connected_agent()` defaults to `clientCapabilities: {}` (`src/tck/v1/conformance/_helpers.py:46-52`), and every caller passes `{}` or nothing. Recommendation: keep the default at `{}`, because ACP-CLIENTCAP-006 depends on it and advertising `plan` everywhere would change agent behaviour in unrelated tests. Add one dedicated helper connection with `client_capabilities={"plan": {}}` for the new PLAN rows.

## Requirements (new agent-side rules at target)

| # | Requirement | Tier | Citation (agent-client-protocol @ 3961af94fa62) |
|---|-------------|------|----------|
| 1 | Agent MUST NOT send `plan_update`/`plan_removed` unless the client advertised `plan`. If `plan` is omitted it MUST fall back to `plan`. | MUST (pre-existing, = ACP-CLIENTCAP-006) | `docs/protocol/v1/draft/agent-plan.mdx:53` |
| 2 | When the client advertised `plan`, the agent SHOULD send plans with `plan_update` instead of `plan`. | SHOULD (new). Conditional on the *client* advertising `plan`. | `agent-plan.mdx:57`; `docs/rfds/plan-operations.mdx:51` (RFD, design intent) |
| 3 | Each `plan_update` replaces the whole plan with that `planId`, across types. | Definitional / client semantics | `agent-plan.mdx:59` |
| 4 | Plan file URIs MUST be absolute. | MUST (new) | `agent-plan.mdx:127`; `docs/rfds/plan-operations.mdx:63` |
| 5 | Agent SHOULD send `plan_removed` when a plan is cancelled (rejected/abandoned). A finished plan need not be removed. | SHOULD (new) | `agent-plan.mdx:147` |
| 6 | Clients MUST ignore `plan_removed` for an unknown `planId`. | MUST, client-side (new) | `agent-plan.mdx:147` |
| 7 | Item-based plans: the agent MUST send the complete entry list each update, and the client MUST replace that plan's contents. Empty `entries` empties the plan. Clients MAY hide an empty plan. | MUST (agent, unobservable) / MUST, MAY (client) | `agent-plan.mdx:181`; baseline `plan` equivalent at `:179` (pre-existing) |
| 8 | All Agents MUST support resource links when included in prompts. | MUST (restates the existing baseline) | `docs/protocol/v1/draft/content.mdx:170`; `initialization.mdx:264`; `schema/v1/schema.unstable.json#/$defs/ContentBlock` (resource_link variant description: "All agents MUST support resource links in prompts.", present at base too) |
| 9 | Clients SHOULD render text as Markdown. | SHOULD, client-side | `content.mdx:22` |

## Details

### ACP-CLIENTCAP-006 -- unchanged
- `agent-plan.mdx:10` and `:53` at target have exactly the base text. The diff touches neither line, and the hunk header line counts around them are unchanged.
- `prompt-turn.mdx:25-26` at target are still the `plan_update`/`plan_removed` rows ("Requires the Client's `plan` capability"). spec-impact flags it because the whole session-update table (`-14,21 +14,21`) was reformatted. The meaning has not moved.
- `#/$defs/PlanCapabilities`: only the `_meta` description changed.
- Optional enrichment: `initialization.mdx:173-178` (the new client "Plan operations" `ParamField`) is now the most direct statement that an omitted or `null` `plan` means "the Agent sends plans with the `plan` update instead". Adding it to the citation is optional. That doc belongs to another researcher.
- Test `test_no_plan_operation_without_client_capability` still matches.

### ACP-PROMPT-003 -- changed text + citation
- Old text (in part): "`content.mdx:31` only mentions text but does not exclude `resource_link`, which carries no prompt-capability requirement."
- Proposed text: "A prompt containing a `resource_link` content block alongside text resolves with a successful result whose `stopReason` is a defined value. All agents MUST support `resource_link` in prompts (`content.mdx:170`, `initialization.mdx:264`, and the `ContentBlock` resource_link variant description)."
- Proposed citation: `docs/protocol/v1/draft/content.mdx:170; docs/protocol/v1/draft/initialization.mdx:264; schema/v1/schema.unstable.json#/$defs/PromptCapabilities; schema/v1/schema.unstable.json#/$defs/ContentBlock`. Drop `content.mdx:31` from this row. It stays on ACP-PROMPT-001.
- Tier stays MANDATORY. Test (`src/tck/v1/conformance/test_prompt.py:71-89`) is unchanged.

### ACP-PROMPT-001, ACP-PROMPTCAP-001/002/003 -- unchanged
content.mdx hunks `-3,7 +3,7` and `-11,15 +11,15` keep line counts, and the only insertion (+2 lines) is at `:168-169`, after every cited line. So `:31`, `:54-56` and `:122-125` hold identical text at target. Tests send exactly the same blocks as before, and the block shapes did not change.

### Proposed ACP-PLAN-001 (new)
- **Tier:** MANDATORY. "Plan file URIs **MUST** be absolute." Pass is vacuous when the agent sends no file plan. This works like ACP-PROMPT-004, which is also MANDATORY-with-vacuous-pass for absolute paths.
- **Capability gate:** none in the `@pytest.mark.capability` sense. That marker gates on *agent*-advertised capabilities, and here the gate is the *client's* `plan` capability, which the TCK controls. The test simply connects with `client_capabilities={"plan": {}}`.
- **Text:** "When the client advertised `clientCapabilities.plan`, every `plan_update` whose `plan.type` is `"file"` carries an absolute `plan.uri`. Passes vacuously if the agent sends no file plan."
- **Citation:** `docs/protocol/v1/draft/agent-plan.mdx:127 @ 3961af94fa62`; `schema/v1/schema.unstable.json#/$defs/PlanFile`.
- **Observation:** use a connection with `plan: {}`, then `session/new`, then a prompt turn with a plan-eliciting prompt (e.g. "Make a step-by-step plan for refactoring this project, then start on it"), then a quiet period. Scan every received `session/update` with `sessionUpdate == "plan_update"` and `plan.type == "file"`. Schema validation already enforces that `uri` is present and a string (`PlanFile.required = [planId, uri]`), but the schema has **no** `format` on `uri`, so absoluteness has to be checked by hand.
- **DECISION NEEDED, the meaning of "absolute":** the spec doesn't define it. Recommendation: an RFC 3986 §4.3 absolute URI, meaning a scheme is present. For the `file` scheme, additionally require an RFC 8089 path-absolute (`file:///...` or `file://host/...`). So `plan.md`, `./plan.md`, `/tmp/plan.md` (no scheme) and `file:plan.md` all FAIL. The spec example is `file:///tmp/plan.md` (`agent-plan.mdx:120`). The alternative, "scheme present" only, would let `file:plan.md` pass. This is a hypothesis-level reading. Neither the spec nor the schema settles it.
- **Realism:** per the RFD's implementation table, neither the Claude Agent nor the Codex adapter sends `file` plans (`docs/rfds/plan-operations.mdx`, "Agent and Client implementations" table), so against real agents this will almost always pass vacuously.
- **Fixture:** `emits_relative_plan_file_uri.py`. When the client advertised `plan`, it sends `plan_update{plan:{type:"file", planId:"p", uri:"plan.md"}}` during the turn. It should trip only ACP-PLAN-001. It must not trip ACP-CLIENTCAP-006 (that test connects with `{}`, so the fixture must send nothing plan-related there) or ACP-PROMPT-002 (the shape is schema-valid).

### Proposed ACP-PLAN-002 (new) -- DECISION NEEDED on tier
- **Text:** "When the client advertised `clientCapabilities.plan`, the agent does not send the baseline `plan` update. It sends plans via `plan_update` instead. Passes vacuously if the agent sends no plans."
- **Citation:** `docs/protocol/v1/draft/agent-plan.mdx:57 @ 3961af94fa62`; `docs/protocol/v1/draft/initialization.mdx:173-178`.
- **Tier options:**
  - ADVISORY (recommended). The wording is **SHOULD**, and ADVISORY never affects the verdict.
  - INFORMATIONAL. Arguable because `PlanCapabilities` is marked **UNSTABLE** ("not part of the spec yet", `#/$defs/PlanCapabilities` description). An agent that hasn't adopted the unstable feature, and keeps sending `plan` to a client advertising `plan`, would show an advisory FAIL. That is technically correct but may be noisy.
  - Recommendation: ADVISORY, with the failure message noting that the agent may simply not implement unstable plan operations.
- **Observation:** same connection and scan as ACP-PLAN-001, so share one helper and one turn. FAIL if any `sessionUpdate == "plan"` arrives.
- **Fixture:** `sends_plan_despite_plan_capability.py`. It sends a baseline `plan` update even when the client advertised `plan`. It trips only ACP-PLAN-002, which is advisory, so the verdict stays CONFORMANT. `test_cli.py` should assert that.
- **Positive coverage:** consider extending `tests/fixtures/agents/v1/conforming_full.py` to send `plan_update{type:"items"}` when `plan` is advertised and nothing otherwise, so both rows get a non-vacuous PASS. No current fixture emits plans (`grep -i plan` over `conforming.py`/`_base.py` finds nothing).

### Ledger (`[[not_requirement]]` in `spec-tracker/maps/v1.toml`)
- **L1:** citation `docs/protocol/v1/draft/agent-plan.mdx:179,181 @ 3961af94fa62`. Statement: "The Agent MUST send a complete list of all plan entries, with their current status, in each `plan` update and in each item-based `plan_update`." Reason: unobservable. The TCK cannot know the agent's full internal plan, so a shorter list can't be told apart from a plan the agent legitimately shrank (`:185` allows removing entries).
- **L2:** citation `agent-plan.mdx:147 @ 3961af94fa62`. Statement: "Agents SHOULD send `plan_removed` when a plan is cancelled (rejected by the user or abandoned by the Agent)." Reason: unobservable. No protocol event marks a plan as rejected or abandoned, and `session/cancel` cancels a turn, not a plan (the RFD says a finished plan stays: `docs/rfds/plan-operations.mdx:185`).
- **L3:** citation `agent-plan.mdx:147 @ 3961af94fa62`. Statement: "Clients MUST ignore `plan_removed` for a `planId` they don't know." Reason: client-side rule.
- **L4:** citation `agent-plan.mdx:59,179,181 @ 3961af94fa62`. Statement: "Each `plan_update` replaces the whole plan with that `planId`, whatever its `type`. Clients MUST replace the plan completely, an empty `entries` array empties it, and Clients MAY hide it." Reason: client-side semantics. Agents may switch types or send `entries: []`, and the schema allows both (no `minItems` on `PlanItems.entries`). The TCK must not treat either as a defect.
- Not recommended for the ledger (pure prose or client rendering nobody would expect the TCK to test): `content.mdx:22` "Clients SHOULD render it as Markdown", `content.mdx:16` "Content from the Agent is untrusted", and `content.mdx:18` superset-of-MCP / optional image `uri` (already in `#/$defs/ImageContent.properties.uri`). Add `:22` as L5 only if the orchestrator wants every normative SHOULD accounted for.

## Testability notes
- Every proposed PLAN check depends on the TCK advertising `plan: {}`. Without that, the agent is *required* not to use plan operations, so nothing about them can be observed (except the violation that ACP-CLIENTCAP-006 already catches).
- Both PLAN rows depend on the agent choosing to plan at all (the plan SHOULD at `agent-plan.mdx:14` is soft), so vacuous PASS will be common against real agents. Treat a non-vacuous PASS as coming mainly from fixtures.
- Unknown `plan.type` values: the RFD says v1 `PlanUpdateContent` has no unknown-type fallback (`docs/rfds/plan-operations.mdx:74`). The schema's closed `oneOf` already makes such a message fail ACP-PROMPT-002's validation. No new row is needed.

## Discrepancies
- Minor wording only: content.mdx:18 says ACP's `ContentBlock` is "compatible with, and a superset of" MCP's, while the schema `ContentBlock` description says only "compatible with the Model Context Protocol (MCP)". Not a conflict.
- Otherwise none found. Docs, RFD (`plan-operations.mdx:51,57-59,63,69-70`) and schema agree, and nothing in the schema contradicts the new prose rules. The schema just doesn't encode "absolute".

## Open questions
- ACP-PROMPT-001/003 cite `initialization.mdx:247`, which is `:264` at target (also `:173-178` for the plan cap). That is for the initialization.mdx researcher / `spec-impact --fix`.
- Whether another researcher is also proposing an `ACP-PLAN` area id (e.g. from `prompt-turn.mdx`). The orchestrator should de-duplicate ids.
