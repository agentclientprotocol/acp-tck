# v1 spec-update impact: `docs/protocol/v1/draft/session-setup.mdx` (beac4ba9 -> 3961af94)

**Sources checked:** agent-client-protocol (worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`), base `beac4ba96190018e9f6d82e148ff275084c5aa3e`, target `3961af94fa62d2386d993cadf1afc8b146fc799a` (2026-11-10). Read through git only: `docs/protocol/v1/draft/session-setup.mdx` (whole file at target, plus the diff), `docs/protocol/v1/draft/error.mdx`, `docs/protocol/v1/draft/initialization.mdx:331-346`, `docs/rfds/client-system-prompt.mdx`, `schema/v1/schema.unstable.json` and `schema/v1/schema.json` (base and target), `agent-client-protocol-schema/src/serde_util.rs`, and commit `5a0a17b1`. TCK: `src/tck/v1/requirements.py`, `src/tck/v1/conformance/test_session.py`, `test_session_capabilities.py`, `_mcp_stub.py`, `src/tck/v1/validation.py`, `tests/fixtures/agents/v1/_base.py`, `spec-tracker/maps/v1.toml`, `spec-tracker/src/spec_tracker/impact.py` (`remap_range`). I did not consult the reference SDKs: no affected rule depends on runtime behavior the spec leaves implicit.
**Confidence:** high. The line mappings were checked against `-U0` hunks and the `remap_range` logic, and every schema claim was checked by a structural diff of `$defs`.

All target line citations below are `docs/protocol/v1/draft/session-setup.mdx:<lines> @ 3961af94fa62` unless stated otherwise.

## Summary table

| id | classification | note |
|---|---|---|
| ACP-SESSION-001 | unchanged | :73 -> :73 |
| ACP-SESSION-002 | unchanged | :73 -> :73 |
| ACP-SESSION-003 | citation-only (**Needs review**) | `476-501` overlaps hunks `-494`/`-497`: the nested `EnvVariable.name/value` ParamFields gained `required`. Manual remap: `468,476-501` -> `480,488-513`. The schema is unchanged (`env` was already required). |
| ACP-SESSION-004 | citation-only | :638 -> :650 (auto) |
| ACP-LOAD-001 | citation-only (**Needs review**, plus a free-text range) | `110-200` overlaps hunk `-139,9`: two bullets became paragraphs, meaning unchanged. Manual: `106,110-201`. The prose "`{}` result example at 191-200" is not a `path:lines` reference, so `--fix` will not touch it. Change it by hand to `192-201`. |
| ACP-LOAD-002 | citation-only (**Needs review**) | `136-142` overlaps hunk `-139,9`. It stays `136-142` (same text, now a paragraph). `191-192` -> `192-193` (auto). |
| ACP-LOAD-003 | citation-only | :194-200 -> :195-201 (auto). `serde_util.rs:30-38` is still the `default_on_null` macro doc at target (wording-only edit), so it still supports the claim. |
| ACP-RESUME-001 | citation-only | `239-244,266-277` -> `240-245,267-278` (auto) |
| ACP-RESUME-002 | citation-only | `266-269` -> `267-270` (auto) |
| ACP-CLOSE-001 | citation-only | `328-343` -> `329-344` (auto). The test is still correct. |
| ACP-CLOSE-002 | citation-only | `332-334` -> `333-335` (auto) |
| ACP-ADDDIRS-001 | citation-only (**Needs review**) | `351-380` overlaps hunk `-378` (a semicolon became a period). Manual: `354-383`. |
| ACP-SYSPROMPT-001 | changed text (wording only; tier and gate unchanged) | Drop "Unstable feature." Lines `411,415` -> `414,418` (auto). Keep the `schema.unstable.json` pointers. |
| ACP-SYSPROMPT-002 | changed text (wording only; tier and gate unchanged) | Drop "Unstable feature." Lines `412,418` -> `415,422` (auto). |
| ACP-SYSPROMPT-003 | changed text (wording only; tier and gate unchanged) | Drop "Unstable feature." Lines `415,418` -> `418,422` (auto). |
| ACP-AUTH-003 / ACP-AUTH-005 | unchanged (for this doc) | They cite :10 -> :10 |
| ACP-CLIENTCAP-005 | citation-only (**Needs review**) | `139-142` overlaps hunk `-139,9`. It stays `139-142` (the bullet became a paragraph, meaning unchanged). |
| **ACP-CLOSE-003** (new) | new, ADVISORY | `session/close` of an already-closed or never-created session SHOULD return the empty result (:347-350) |
| **ACP-SESSION-005** (new, optional) | new, ADVISORY | stdio MCP `args` reach the server verbatim, with no shell splitting or expansion (:658). Partly observable. |
| **ACP-SESSION-006** (new, optional) | new, ADVISORY | the value of a stdio MCP `env` entry never appears in agent-authored stdout traffic or in stderr (:660). Partly observable. |
| ledger L1-L6 | new deliberate non-requirements | workspace-root security (:473, :474), the remainder of MCP security (:660, :661), the empty `systemPrompt.content` MAY (:419), and the remainder of :658 if ACP-SESSION-005 is not adopted |
| spec map | address change | `sections = ["(intro)", "Session ID", "Working directory"]` |
| `validation.py` null-response carve-out | still holds | see Details section 6 |

No retirements. No tier changes are proposed, so there is no DECISION NEEDED on tier. There are two smaller decisions, D-A and D-B, at the end.

## Answer

Most of the doc's changes are editorial: sentence-cased headings, bullets turned into paragraphs, and a semicolon changed to a period. They shift line numbers and put five citations under "Needs review", but they do not change meaning. The normative changes are:

1. **`session/close` idempotency** (:347-350). The old `Agents MAY return an error if the session does not exist or is not currently active` is replaced by "Closing is idempotent ... the Agent **SHOULD** respond with the same empty result. Clients **SHOULD** treat a `-32002` response ... as a successful close." This is a new SHOULD a client can observe, so I propose ACP-CLOSE-003 (ADVISORY).
2. **System prompt stabilized.** The heading lost "(unstable)", the `**UNSTABLE**` banners are gone from the `SystemPrompt*` `$defs`, and those `$defs` are now in stable `schema.json`. The RFD says the Preview semantics were kept unchanged (`docs/rfds/client-system-prompt.mdx:368`). One new rule was added: clients MUST NOT send an empty `content` array, and agents MAY reject one with `-32602` (:419). The SYSPROMPT rows only need wording and line changes. They stay CAPABILITY-tier, gated on `agentCapabilities.sessionCapabilities.systemPrompt`. The empty-array MAY is permissive, so it goes to the ledger.
3. **New "Workspace root security" (:468-474) and "MCP servers > Security" (:654-662) subsections.** All of it is SHOULD-level. The client-side bullets need nothing from the TCK. Two agent-side MCP bullets are partly observable with the existing stub MCP server, so ACP-SESSION-005 and ACP-SESSION-006 are optional ADVISORY additions. The rest goes to the ledger.
4. **`env`/`headers`:** the only change is that the doc's nested `EnvVariable`/`HttpHeader` `name`/`value` ParamFields are now marked `required`. The schema already required them, and `McpServerStdio.env` and `McpServerHttp/Sse.headers` were already in `required` at base. The `x-deserialize-default-on-null` hints are schema-generator annotations on client-authored request fields. They have no effect on the TCK's validation, which only validates agent-authored messages and whose validator ignores unknown `x-` keywords.

## Requirements

| # | Requirement | Tier | Citation |
|---|---|---|---|
| 1 | `session/close` of a session that does not exist or is not active (for example, already closed) responds with the same empty result | SHOULD (ADVISORY). Applies only when `sessionCapabilities.close` is advertised, because the method is only callable then. | session-setup.mdx:347-349; error.mdx:55 @ 3961af94fa62 |
| 2 | Clients SHOULD treat `-32002` on `session/close` as a successful close | client-side SHOULD, not agent-testable | session-setup.mdx:349-350 |
| 3 | Clients MUST NOT send an empty `systemPrompt.content`, and Agents MAY reject one with `-32602` without creating, loading, resuming, or forking the session | client MUST plus agent MAY, so nothing to judge on the agent | session-setup.mdx:419; schema.unstable.json#/$defs/SystemPrompt/properties/content |
| 4 | An agent advertising systemPrompt MUST accept `text` blocks (`append` always supported) | capability:sessionCapabilities.systemPrompt (MUST) | :418; `#/$defs/SessionSystemPromptModeCapabilities` (description) |
| 5 | An unsupported mode MUST produce an error, not be treated as `append`/`override` | capability:sessionCapabilities.systemPrompt (MUST) | :415, :422 |
| 6 | An unsupported content block type MUST produce an error and MUST NOT create the session; `-32602` RECOMMENDED | capability:sessionCapabilities.systemPrompt (MUST) | :418, :422 |
| 7 | Agents SHOULD launch the stdio `command` with `args` as separate arguments, without a shell | SHOULD (ADVISORY) | :658 |
| 8 | Agents SHOULD NOT include `env`/`headers` values in session updates, errors, `_meta`, `session/list` results, replayed history, model context, or command lines, and SHOULD NOT log or persist them | SHOULD (ADVISORY), partly observable | :660 |
| 9 | Agents SHOULD send `headers` only to the configured origin | SHOULD; would need `mcpCapabilities.http`; out of scope | :661 |
| 10 | Agents SHOULD NOT treat model output, Agent content, or replayed history as granting access outside the root set | SHOULD; unobservable | :473 |
| 11 | Implementations enforcing the root set SHOULD check the resolved path at use time, compare by component, and fail closed | SHOULD; unobservable | :474 |
| 12 | Client-side SHOULDs: root-set contents (:472), stdio servers from workspace files (:659), credential storage (:662), trusted system-level content (:443) | client-side | as cited |

## Details

### 1. Line remaps and "Needs review" (for whoever runs `spec-impact --fix`)

`-U0` hunks in this doc: `-6`, `-47`, `-85`, `-89`, `-108`, `-139,9 +139,10`, `-208`, `-213`, `-237`, `-282`, `-288`, `-312`, `-346,2 +347,4`, `-349`, `-378`, `-382`, `-413`, `-415,0 +419` (insertion), `-453`, `-464 +468,9`, `-472`, `-474`, `-494`, `-497`, `-519`, `-539`, `-542`, `-568`, `-590`, `-593`, `-615`, `-640,0 +653,10`. Per `remap_range` (`spec-tracker/src/spec_tracker/impact.py:550-559`), a range that any hunk touches is left as written and listed under Needs review. Manual values for those ranges:

| row | base element | target | how |
|---|---|---|---|
| ACP-SESSION-003 | `476-501` | `488-513` | `--fix` maps `468` -> `480`. Target 488 is "All Agents **MUST** support connecting to MCP servers via stdio", and 513 is the closing `</ParamField>` of `env`. |
| ACP-LOAD-001 | `110-200` | `110-201` | `106` is unchanged (auto). Also hand-edit the prose "(`{}` result example at 191-200)" to "192-201". |
| ACP-LOAD-002 | `136-142` | `136-142` | the compaction paragraph is still 139-142 |
| ACP-CLIENTCAP-005 | `139-142` | `139-142` | same |
| ACP-ADDDIRS-001 | `351-380` | `354-383` | 354 "Agents that advertise `sessionCapabilities.additionalDirectories`...", 383 "Clients **MUST** only send `additionalDirectories`..." |

I checked by hand that the auto-remapped targets point at the same sentences. :414 is the "`mode` is required" line, :415 the `_`-reserved modes plus the MUST-error rule, :418 the text-only rule, and :422 the "cannot apply -> MUST return an error" rule. :73, :106, :192-193, :195-201, :240-245, :267-278, :329-344, :333-335, :480 and :650 also match.

Spec map (`spec-tracker/maps/v1.toml:70`): `sections = ["(intro)", "Session ID", "Working directory"]`. Only `Working Directory` changed. `Session ID` is already that case at target (:445), and `(intro)` is literal. Under the map's rules a section covers its subsections, so `Working directory` (:457-474) now also covers the new `### Workspace root security`. I recommend keeping that, since it is root-set scope and matches the entry's `reason`. To exclude it, use `"Working directory > (intro)"`. Anchors such as `#working-directory` are unaffected, because heading slugs are lowercased.

### 2. `session/close` idempotency, and the proposed ACP-CLOSE-003

Base (:346-347): `Agents MAY return an error if the session does not exist or is not currently active.` Target (:347-350):

> Closing is idempotent. If the session does not exist or is not active, for example because it was already closed, the Agent **SHOULD** respond with the same empty result. Clients **SHOULD** treat a `-32002` response to `session/close` as a successful close.

`error.mdx:55 @ 3961af94fa62` agrees: "Closing or deleting a session that does not exist still succeeds." `CloseSessionRequest` and `CloseSessionResponse` are structurally unchanged in the schema, and neither description mentions idempotency.

Proposed **ACP-CLOSE-003**:
- **Tier:** ADVISORY (the wording is SHOULD). Use `capability=None`, as for ACP-DELETE-002, and gate the test with `@pytest.mark.capability("agentCapabilities.sessionCapabilities.close")`. The module docstring of `test_session_capabilities.py` documents this pattern.
- **Text:** "`session/close` of a session that is no longer active (already closed on this connection) or never existed SHOULD succeed with the same empty result, not an error. A `-32002` answer is the documented legacy behavior clients tolerate. It is still flagged here, and its code is recorded."
- **Citation:** `docs/protocol/v1/draft/session-setup.mdx:347-350 @ 3961af94fa62; docs/protocol/v1/draft/error.mdx:55`.
- **Observation:** first test: `session/new`, then `session/close` (prerequisite: on error, SKIP with "see ACP-CLOSE-001"), then a second `session/close` with the same id. Assert `"result" in msg`. Optionally validate it as a `session/close` response; the existing null carve-out already accepts `null`. Second test, bound to the same id: close `"tck-never-created-session"` with no `session/new`, mirroring ACP-DELETE-002.
- **Fixture:** `close_not_idempotent.py`, which answers a second close or an unknown-id close with `-32002` + `data.sessionId`. It should trip only ACP-CLOSE-003. The conforming baseline already passes, because `tests/fixtures/agents/v1/_base.py:419-426` always replies `{}`.
- **ACP-CLOSE-001 and ACP-CLOSE-002 are unaffected:** they close an existing session, and their prerequisite SKIPs remain correct.

### 3. System prompt: stabilization and the SYSPROMPT rows

What changed:
- Heading `## System Prompt (unstable)` -> `## System prompt` (:385).
- `**UNSTABLE**` banners were removed from `SystemPrompt`, `SystemPromptMode`, `SessionSystemPrompt{,Mode,Override}Capabilities`, and `{New,Load,Resume}SessionRequest.systemPrompt`.
- All of these `$defs` were added to stable `schema/v1/schema.json` (absent at base).
- `ForkSessionRequest` is still unstable-only.
- None of the `SystemPrompt*` `$defs` changed structurally. `SystemPrompt.content` has no `minItems`, so the empty-array rule is prose only.
- New description text on `#/$defs/SystemPrompt/properties/content`: "Clients MUST NOT send an empty array. Agents MAY reject one with `-32602` without creating, loading, or resuming the session."
- The RFD moved to Completed "with the Preview semantics unchanged" (`docs/rfds/client-system-prompt.mdx:368`).

Proposed edits (text only; tier, capability and test assertions unchanged):
- **ACP-SYSPROMPT-001:** drop the trailing "Unstable feature." The rest still matches :418 and the `SessionSystemPromptModeCapabilities` description ("every agent advertising `sessionCapabilities.systemPrompt` supports it").
- **ACP-SYSPROMPT-002:** drop "Unstable feature." Recording rather than asserting the code is still right, because `-32602` is only RECOMMENDED (:422).
- **ACP-SYSPROMPT-003:** drop "Unstable feature."
- **Citations:** keep `schema/v1/schema.unstable.json#/$defs/...`. Do **not** switch them to `schema.json`. The project convention (CLAUDE.md, "How to add a requirement + test") and `tests/v1/test_registry.py:140-213` resolve v1 pointers against the vendored `schema.unstable.json` only. The pointers still resolve there, and the vendored file is the stable superset.
- **Test-side cosmetics:** `src/tck/v1/conformance/test_session_capabilities.py:459` has the comment `# --- systemPrompt (unstable) ---`. Drop "(unstable)". No assertion changes.
- **Tier: keep CAPABILITY, gated on `agentCapabilities.sessionCapabilities.systemPrompt` (object marker).** Stability never set the tier. The feature is still optional and only binding when advertised (`initialization.mdx:340-346 @ 3961af94fa62`: "Omitted or `null` both mean the Agent does not advertise support"). The rules being tested are MUSTs. No DECISION NEEDED.

### 4. MCP servers: `env`/`headers` and the Security subsection

- The schema already had `McpServerStdio.required = [name, command, args, env]`, `McpServerHttp/Sse.required` including `headers`, and `EnvVariable`/`HttpHeader.required = [name, value]`. Only `x-deserialize-default-on-null: true` was added on `args`/`env`/`headers` (commit `5a0a17b1`, "mark DefaultOnNull lists with an x-deserialize hint"). It documents an existing Rust receiver tolerance of `null` (`#[serde_as(deserialize_as = "DefaultOnNull")]`, e.g. `agent-client-protocol-schema/src/v1/agent.rs:1142-1150 @ 3961af94fa62`).
- Doc-side, the nested `name`/`value` ParamFields are now `required`.
- ACP-SESSION-003 already sends `env: []` (`test_session.py:70-78`), so its text and test still hold.

Proposed **ACP-SESSION-005** (optional):
- **Tier:** ADVISORY (SHOULD), `capability=None`.
- **Text:** "The agent passes a stdio MCP server's `args` to the launched process as separate argv entries, without shell splitting or expansion: an argument containing spaces, `$VAR` and `*` reaches the server verbatim."
- **Citation:** `docs/protocol/v1/draft/session-setup.mdx:658 @ 3961af94fa62`.
- **Observation:** extend `_mcp_stub.py` to write its `sys.argv[1:]` (JSON) into the marker file. Add an argument such as `"acp tck $ACP_TCK_UNSET_VAR *"`, then compare it after the ACP-SESSION-004-style prompt turn. If the stub never launched, SKIP with "see ACP-SESSION-004".
- **Safety:** use no `;`, `|`, backticks or `$(...)`, so a shell-using agent expands but executes nothing.
- **Limit:** a shell launch with correct quoting is indistinguishable from a direct exec. The observable property is "arguments reach the server verbatim", not literally "without a shell". The requirement text should say that.
- **Fixture:** `mcp_via_shell.py`, which launches with `shell=True` and `" ".join([...])`.

Proposed **ACP-SESSION-006** (optional):
- **Tier:** ADVISORY (SHOULD), `capability=None`.
- **Text:** "The value of a stdio MCP server `env` entry (a random canary) never appears in any line the agent writes to stdout (responses, errors, `session/update`, `_meta`, `session/list`, load replay) or to stderr."
- **Citation:** `docs/protocol/v1/draft/session-setup.mdx:660 @ 3961af94fa62`.
- **Observation:** send `env: [{"name": "ACP_TCK_CANARY", "value": "<uuid4>"}]` on `session/new` and run one prompt turn. If advertised, also call `session/list` and, if `loadSession`, `session/load` the session. Then search `agent.transcript` (received direction, raw bytes) and `agent.stderr_text()` for the canary. Report which channel leaked.
- **Optional extra:** the extended stub can also check that the canary is absent from its own argv. This covers the "command lines" clause only for the stub's own argv.
- **Unobservable parts:** model context, persistence, and logging other than stderr go to ledger L4.
- **Fixture:** `leaks_mcp_env.py`, which echoes the MCP config into `session/new`'s `_meta` or into stderr.

If the orchestrator prefers not to grow the MCP surface now, ledger both bullets instead (L3, and L4 covering all of :660).

### 5. Workspace root security and other new text

Workspace root security (:468-474): all SHOULD-level. The Agent bullets are internal policy that the TCK can only see by getting the model to try out-of-root access, which is unreliable and possibly unsafe. They go to the ledger (L1, L2). The Client bullet (:472) is a client-side rule and needs no ledger entry.

Other new or edited lines needing nothing:
- :6 intro rewording.
- :139-148 bullets turned into paragraphs. The compaction gating rule is unchanged and still matches ACP-CLIENTCAP-005.
- :381 punctuation.
- :416 punctuation.
- :502-513 / :547-558 / :598-609 nested `required`.

### 6. `src/tck/v1/validation.py` carve-outs

- **`session/load` null-response carve-out** (`_response_schema_permits_null`, `validation.py:153-166`, used at `:437-439`). It still holds. At target, `LoadSessionResponse`, `ResumeSessionResponse`, `CloseSessionResponse` and `NewSessionResponse` are structurally identical to base. `LoadSessionResponse` is still `type: object` with no `required`. The Rust crate still tolerates `null` for these payloads: `serde_util.rs:30-38` is still the `default_on_null` macro doc, and `serde_util.rs:120-135` at target lists `v1::LoadSessionResponse`, `ResumeSessionResponse` and `CloseSessionResponse` among the checked default-on-null types. The serde_util diff only adds cfg-aware field copying and more types (archive, auth-status). ACP-LOAD-003's citation `serde_util.rs:30-38` stays valid, and `--fix` does not remap non-doc citations.
- **`x-deserialize-default-on-null`:** the validator is `Draft202012Validator`, which ignores unknown `x-` keywords. `tck.v1.protocol`/`validation` only read `x-side`/`x-method`. Nothing in this doc's `$defs` that the TCK validates (agent-authored responses) gained the hint. No carve-out needed.
- There is no other session-setup carve-out in `validation.py`.

## Testability notes

- **ACP-CLOSE-003:** a conforming agent answers `{}` (or `null`, accepted by the carve-out) to a second close and to a never-created close. A non-conforming agent answers `-32002` or any other error. Because the requirement is ADVISORY, a real agent answering `-32002` shows as an ADVISORY FAIL and never changes the verdict. Expect some upstream agents in `cross-check` to do this, since base text allowed an error. The baseline may need an expected entry (follow-up for whoever owns cross-check).
- **SYSPROMPT rows:** no change to what is observable. "MUST NOT create the session" is still only observable through the error itself.
- **Empty `content` array:** both acceptance and `-32602` rejection conform. Sending it would also make the TCK break a client MUST NOT for no verdict, so it is not tested (L6). If data is wanted, an INFORMATIONAL `ACP-INFO-*` row could record the outcome, but I do not recommend it.
- **ACP-SESSION-005 / ACP-SESSION-006:** both depend on the agent actually launching the stub. Agents that connect lazily or never connect make them SKIP, as with ACP-SESSION-004.

## Proposed ledger entries (`[[not_requirement]]`)

| # | citation | statement | reason |
|---|---|---|---|
| L1 | `docs/protocol/v1/draft/session-setup.mdx:473 @ 3961af94fa62` | Agents SHOULD NOT treat model output, Agent content, or replayed history as granting access outside the root set; such access goes through a permission request. | Unobservable: needs the model to attempt out-of-root access, which a client-driven TCK cannot reliably or safely trigger. |
| L2 | `docs/protocol/v1/draft/session-setup.mdx:474 @ 3961af94fa62` | Implementations that enforce the root set SHOULD check the resolved path at use time, compare paths by component, and fail closed. | Unobservable: internal enforcement mechanics of the agent. |
| L3 | `docs/protocol/v1/draft/session-setup.mdx:658 @ 3961af94fa62` | Agents SHOULD launch a stdio MCP `command` with `args` as separate arguments, without a shell. | Only if ACP-SESSION-005 is not adopted. Otherwise drop this, or reword it to "the without-a-shell part cannot be distinguished from correct quoting". |
| L4 | `docs/protocol/v1/draft/session-setup.mdx:660 @ 3961af94fa62` | Agents SHOULD NOT put `env`/`headers` values into model context or command lines, nor log or persist them. | Unobservable from the client (model context, disk persistence, logs other than stderr). If ACP-SESSION-006 is not adopted, cover all of :660 with the reason "out of scope". |
| L5 | `docs/protocol/v1/draft/session-setup.mdx:661 @ 3961af94fa62` | Agents SHOULD send `headers` only to the configured origin. | Out of scope: needs an HTTP MCP test server with a cross-origin redirect probe, and only applies under `mcpCapabilities.http`. |
| L6 | `docs/protocol/v1/draft/session-setup.mdx:419 @ 3961af94fa62` | Clients MUST NOT send an empty `systemPrompt.content` array; Agents MAY reject one with `-32602`. | Client-side rule plus a permissive MAY: either agent response conforms, so there is nothing to judge, and probing would make the TCK break a client MUST NOT for no verdict. |

These client-side rules are not ledgered, because nobody would expect a TCK to test them: :443, :472, :659, :662, and :349-350 (clients treating `-32002` as success).

## Discrepancies

1. **`SystemPrompt` `$def` vs doc on fork.** The schema descriptions (`#/$defs/SystemPrompt`, `.../properties/content`) say "creating, loading, or resuming". The doc (:419, :422) adds "or forking". This is consistent with fork staying unstable while the shared `$def` is now stable. It does not affect the TCK, which never forks with a system prompt.
2. **Doc vs schema on `env` (pre-existing, unchanged).** The doc's stdio `env` ParamField (:502) is still not marked `required`, while `McpServerStdio.required` includes `env`. The doc's HTTP/SSE `headers` ParamFields are marked `required`. The TCK always sends `env`, so there is no impact. This is worth an upstream issue only.
3. **Empty-content rule is prose-only.** It is not expressed as `minItems: 1` in `SystemPrompt.content`. This is not a conflict, and the TCK does not validate client-authored messages anyway.
4. Close idempotency agrees across session-setup.mdx:347-350 and error.mdx:55. The schema is silent. None found beyond that.

## Decisions for the orchestrator

- **D-A (scope):** adopt ACP-SESSION-005/006 as ADVISORY rows, or ledger them (L3 plus all of :660 under L4). Recommendation: adopt ACP-CLOSE-003 in this update. Treat ACP-SESSION-005/006 as optional; they are cheap with the existing stub, but they are new test surface the inventory did not anticipate.
- **D-B (ACP-CLOSE-003 strictness):** recommendation: flag `-32002` as an ADVISORY FAIL, because the agent SHOULD return the empty result and the client-side tolerance does not excuse the agent. The alternative is to PASS on `-32002` and FAIL only on other errors, which contradicts the SHOULD text.

## Open questions (route elsewhere)

- `error.mdx:53-55` adds agent SHOULDs for `-32002` + `data.sessionId` on `session/load`/`session/resume` of a nonexistent session, and on `session/prompt`/`set_mode`/`set_config_option`. This bears on ACP-INFO-UNKNOWNSESSION-001 (which cites the `error.mdx:6 (stub)`) and possibly on new LOAD/RESUME rows. That belongs to whoever owns `error.mdx`.
- `x-deserialize-default-on-null` also landed on **agent-authored** `AuthMethodTerminal.args/env` (in the `initialize` response). An agent sending `null` there would fail vendored-schema validation even though Rust receivers accept it. That belongs to the authentication/initialization researcher (ACP-AUTH-002/006), who may want a carve-out like the response-null one.
- Pre-existing and untested, outside this diff's scope: the systemPrompt MUST-error rule on `session/load`/`session/resume` (:422) has no row. Possible future CAPABILITY rows, jointly gated on `loadSession` or `resume`.
