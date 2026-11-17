# Impact research: v1 `initialization.mdx`, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (2026-11-17), read with
`git show 3ea94133:<path>` from `../agent-client-protocol-2`. That checkout's HEAD is `6ace4f6a`, a descendant
whose extra commits touch only v2 files. Base `3961af94`. Files read: `docs/protocol/v1/draft/initialization.mdx`
(the whole doc, plus the base version for line mapping), and the sections it gates in `prompt-turn.mdx`
(update table 15-38, prompt suggestions 360-425, session cursors 577-590), `subagents.mdx` (36-63),
`session-setup.mdx` (454-456), `session-config-options.mdx` (473-568), `tool-calls.mdx:358`,
`schema/v1/schema.unstable.json` (`ClientSessionCapabilities`, `SessionCapabilities`,
`SessionOptionsCapabilities`, `PromptSuggestionsCapabilities`, `SessionCursorsCapabilities`,
`SubagentCapabilities`, `SessionOptionsRequest/Response`, `ForkSessionRequest`) and `docs/docs.json`, for RFD stages.
In the TCK: `src/tck/v1/requirements.py`, `spec-tracker/maps/v1.toml` and
`src/tck/v1/conformance/test_client_capabilities.py`.
**Reference SDKs:** not consulted. Every new rule from this doc is stated explicitly, so none relies on runtime
behaviour.
**Confidence:** high for the classification and the line mapping (every line was checked against the base and
target text). Medium for where the new rows belong, because the prompt-turn, subagents and session-config-options
researchers will see the same rules.

## Diff summary

There are two hunks, both additions:

- **+244-318:** three new client capabilities: `session.promptSuggestions` (with the opt-ins `image`, `audio`
  and `embeddedContext`), `session.cursors` and `subagents`. Each one ends "Agents must not send ... without this
  capability".
- **+424-429:** a new agent capability, `sessionCapabilities.options`. It covers `session/options` and
  `configOptions` on session setup.

Line mapping: base lines 1-243 are unchanged. Base 244-347 is now target 320-423 (+76). Base 348 onward is now
target +83.

RFD stages at the target: `session-options`, `prompt-suggestions` and `session-cursors` are **Draft**.
`subagents` and `plan-operations` are **Preview**. `get-auth-state`, `session-status` and `session-set-title` are
**Draft**.

## Existing rows and ledger entries citing `initialization.mdx`

| id / ledger | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-INIT-001 | unchanged | `initialization.mdx:57` | `InitializeResponse` changed only through the closure of the new `SessionOptionsCapabilities`. Re-vendoring covers it. |
| ACP-INIT-002 | unchanged | `:99` | |
| ACP-INIT-003 | unchanged | `:97-101` | |
| ACP-INIT-004 | citation-only | `:57,452` | Was `57,369`. |
| ACP-PROMPT-001 | citation-only | `:340` | Was `264`. |
| ACP-PROMPT-002 | citation-only | `:389` | Was `313`. |
| ACP-PROMPT-003 | citation-only | `:340` | Was `264`. |
| ACP-PROMPTCAP-001 | citation-only | `:342-346` | Was `266-270`. |
| ACP-PROMPTCAP-002 | citation-only | `:348-350` | Was `272-274`. |
| ACP-PROMPTCAP-003 | citation-only | `:352-354` | Was `276-278`. |
| ACP-AUTH-002 | unchanged | `:123-127` | |
| ACP-AUTH-006 | unchanged | `:123-127` | |
| ACP-AUTH-007 | citation-only | `:376-380` | Was `300-304`. Its `get-auth-state` RFD is still Draft, so the label stands. |
| ACP-CONFIG-003 | unchanged | `:189-198` | See follow-up F2 for `session/options` results. |
| ACP-CLIENTCAP-003 | unchanged | `:160-166` | |
| ACP-CLIENTCAP-004 | unchanged | `:228-234` | |
| ACP-CLIENTCAP-005 | unchanged | `:210-216` | |
| ACP-PLAN-002 | unchanged | `:172-179` | The plan section did not move. |
| ACP-CLIENTCAP-007 | **changed citation (source precedence)** | add `initialization.mdx:308-314` and `subagents.mdx:61` as primary sources | Text and tier (MANDATORY) are unchanged. The rule is now in the docs: `subagents.mdx:61` says **MUST NOT** for the three updates and gives the `session` tool-call content rule. Change `docs/rfds/subagents.mdx:76-78,644-645 (Active RFD)` to `(Preview RFD)` and keep it as secondary context only, or drop it. Its prompt-turn citation `prompt-turn.mdx:19-21,42` becomes `19-21,44` (base 42 is target 44). That belongs to the prompt-turn researcher, so confirm it there. The row does not cite this doc today, but this doc now restates its rule. |
| ledger `initialization.mdx:107` | unchanged | `:107` | The reason ("combinatorial") is a real constraint, not a TCK choice. Optional: refresh its example list of targeted connections (the subagents connection exists now). |
| ledger `initialization.mdx:246` | citation-only | `:322` | The reason ("not observable", via line 109) stands and does not rest on a TCK choice. |

Totals: 12 unchanged, 9 citation-only (8 rows and 1 ledger entry), 1 changed citation (ACP-CLIENTCAP-007),
0 removed.

## New requirements

**N1. ACP-CLIENTCAP-008 (provisional): no `prompt_suggestions_update` without `session.promptSuggestions`**

- **Text:** The agent MUST NOT send `prompt_suggestions_update` unless the client advertised
  `clientCapabilities.session.promptSuggestions`. Checked the same way as ACP-CLIENTCAP-004. Passes vacuously for
  an agent that never sends suggestions.
- **Tier:** MANDATORY.
- **Citation:** `prompt-turn.mdx:364` (**MUST NOT**); `initialization.mdx:246-256`;
  `schema/v1/schema.unstable.json#/$defs/PromptSuggestionsCapabilities`.
- **Test:** a copy of `test_no_notice_without_client_capability`. Use `_session_update_kinds_with_no_client_capabilities`
  and assert that `"prompt_suggestions_update"` is not among the kinds. The kinds cover `session/new`, one turn,
  `session/load` replay when advertised, and a quiet period. That connection advertises `clientCapabilities: {}`,
  so the rule holds there with no exceptions, replay included.
- **Harness:** nothing new.
- **Optional extension:** also judge the subagents connection, which does not advertise `promptSuggestions`.

**N2. ACP-CLIENTCAP-009 (provisional): no `cursor_update` without `session.cursors`**

- **Text:** The agent MUST NOT send `cursor_update` unless the client advertised `clientCapabilities.session.cursors`,
  live or during `session/load` replay.
- **Tier:** MANDATORY.
- **Citation:** `prompt-turn.mdx:584-588` (**MUST NOT**; "applies to both live updates and `session/load` replay");
  `initialization.mdx:291-296`; `schema/v1/schema.unstable.json#/$defs/SessionCursorsCapabilities`.
- **Test:** the same as N1, for the `cursor_update` kind.
- **Harness:** nothing new.

**N3. ACP-PROMPTSUG-001 (provisional; probably owned by the prompt-turn researcher, dedupe there)**

- **Text:** Prompt-suggestion content types are limited to what both sides advertise. With
  `session.promptSuggestions: {}` alone, every suggestion's `prompt` contains only `text` and `resource_link`
  blocks. With the `image`, `audio` and `embeddedContext` opt-ins all set to `{}`, an `image`, `audio` or
  `resource` block appears only if the agent's matching `promptCapabilities.*` is `true`.
- **Tier:** MANDATORY, with a vacuous pass when no suggestion is seen. This follows the precedent of
  ACP-CONFIG-003 and ACP-CLIENTCAP-006. The alternative is CAPABILITY `inferred:promptSuggestions` with a SKIP
  when no suggestion is seen. See decision D2.
- **Citation:** `prompt-turn.mdx:402-405` (**MUST**); `initialization.mdx:258-279`;
  `schema/v1/schema.unstable.json#/$defs/PromptSuggestionsCapabilities`.
- **Test:** two connections. The first advertises `{"session": {"promptSuggestions": {}}}` and the second also
  sets all three opt-ins. Each runs `session/new`, one prompt turn and a quiet period. Collect the
  `prompt_suggestions_update` items and check each block's `type` against the allowed set for that connection.
- **Harness:** the mock client must open connections with these advertisements. `connected_agent` already takes
  `client_capabilities`, so this is a new use of an existing helper, not a new mechanism.

**N4. ACP-OPTIONS-001 (provisional; overlaps the session-config-options researcher, dedupe there)**

- **Text:** When `sessionCapabilities.options` is advertised, `session/options` with an absolute `cwd` succeeds,
  and its result validates against `SessionOptionsResponse`.
- **Tier:** CAPABILITY.
- **Gate:** `agentCapabilities.sessionCapabilities.options`, an object marker. `capability_is_supported` already
  treats `{}` as supported.
- **Citation:** `initialization.mdx:424-429`; `session-config-options.mdx:475,479-492`;
  `schema/v1/schema.unstable.json#/$defs/SessionOptionsRequest`;
  `schema/v1/schema.unstable.json#/$defs/SessionOptionsResponse`.
- **Test:** send `session/options {"cwd": <tmp_path>}` and check the result with `validate_agent_response`. The
  response map is derived from the schema, so `session/options` should resolve after re-vendoring. Verify that.
  The test SKIPs when the capability is not advertised.
- **Harness:** nothing new.

**N5. ACP-OPTIONS-002 (provisional; same ownership note as N4)**

- **Text:** When `sessionCapabilities.options` is advertised, `session/new` with `configOptions` succeeds, and the
  response's `configOptions` hold the session's actual values. The request echoes the `id` and `currentValue` of
  each select option from `session/options`, and an empty list is the minimal form.
- **Tier:** CAPABILITY, with the same gate as N4.
- **Citation:** `initialization.mdx:424-429`; `session-setup.mdx:456`; `session-config-options.mdx:539-563` (the
  MUST rules on `-32602`, ignored entries and the response values).
- **Test and harness:** the detailed error-path rows (`-32602` for duplicates or invalid shapes) are for the
  session-config-options researcher to specify.
- **What this doc adds:** only the gate and "both are available".

## New ledger entries

None. The new text in `initialization.mdx` adds no agent-side rule that cannot be observed or tested. Every
agent-side rule above is a client-controlled MUST NOT, or an advertised-capability rule. Client-side text, such as
the client "applies the restrictions on what it sends for a child session" (`:310-311`), is out of ledger scope.

## Discrepancies (record; route to the session-config-options researcher)

1. **Wrong capability path.** `session-config-options.mdx:535,541` gates boolean options on
   `sessionCapabilities.configOptions.boolean`. That path does not exist:
   - The agent's `SessionCapabilities` has no `configOptions` property in the schema.
   - The real gate is the client's `clientCapabilities.session.configOptions.boolean`, defined at
     `initialization.mdx:191-198` and in the schema at `ClientSessionCapabilities.configOptions`.

   The docs, read with the schema, settle it. Follow `initialization.mdx` and the schema.
2. **Fork coverage is inconsistent.**
   - `session-config-options.mdx:475` lists `configOptions` on `session/new`, `session/load` and
     `session/resume` only.
   - `session-config-options.mdx:541` and `session-setup.mdx:456` add `session/fork` "when supported".
   - The schema's `ForkSessionRequest` has `configOptions`.
   - `initialization.mdx:426` says only "session setup requests".

   This matters only if a row tests fork.

## Decisions for the user

- **D1. Tiers for N1 and N2: MANDATORY.** Both are docs-stated client-controlled MUST NOTs, the same pattern as
  ACP-CLIENTCAP-004..007, and they apply to Draft-only features. **Recommend MANDATORY, with a vacuous pass.**
- **D2. Tier and gate for N3.** Choose between MANDATORY with a vacuous pass (precedent) and CAPABILITY
  `inferred:promptSuggestions` with a SKIP when no suggestion is seen. **Recommend MANDATORY.** It is a docs MUST,
  and the TCK controls the advertisement. The cost is two extra connections.
- **D3. ACP-CLIENTCAP-007 sources.** Make `subagents.mdx:61` and `initialization.mdx:308-314` the primary sources.
  Keep the RFD as `(Preview RFD)` secondary context, or drop it. **Recommend relabelling and keeping it as
  secondary context.** It also backs the `session` tool-call content part, which `subagents.mdx:61` now states
  too, so dropping it is also safe.
- **D4. Ownership of N3, N4 and N5.** **Recommend** these be owned by the prompt-turn and session-config-options
  researchers. This report gives only the gate and the minimal availability checks. The orchestrator should
  dedupe them against those reports.

## Follow-ups (not this doc)

- **F1.** The `session.cursors` rules that go beyond the gate are in prompt-turn's scope: cursor anchoring, and
  `-32602` for an unknown `cursorId` on `session/fork` (`prompt-turn.mdx:617-680`). So are the suggestion rules:
  validity, the ban on whitespace-only text, replacement on prompt, and the SHOULD NOT for replay
  (`prompt-turn.mdx:402-425`).
- **F2.** ACP-CONFIG-003 (boolean gating) could extend to `session/options` results when `options` is advertised
  (`session-config-options.mdx:535`). Route this to the session-config-options researcher.
