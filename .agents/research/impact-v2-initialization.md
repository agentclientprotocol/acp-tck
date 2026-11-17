# Impact (v2): `docs/protocol/v2/draft/initialization.mdx`, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read with `git show 3ea94133:<path>`,
because the checkout's working tree is at `6ace4f6a`, which is past the target; `initialization.mdx`, `subagents.mdx` and `schema/v2/`
match the target except an unrelated `Diff.changes` hunk). Files: `docs/protocol/v2/draft/initialization.mdx` (whole, plus diff), linked
`prompt-lifecycle.mdx:703-768`, `slash-commands.mdx:167-259`, `content.mdx:14-26,233-252`, `extensibility.mdx:25-50`,
`session-config-options.mdx:482-585`, `subagents.mdx:6-14`, `schema/v2/schema{,.unstable}.json`, `docs/docs.json` (RFD stages). acp-tck:
`src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`, v2 conformance docstrings. I did not check the reference SDKs. The new text
is explicit, so no runtime behavior had to be inferred from them.
**Confidence:** high for the classifications and line maps (the diff is 3 pure insertions). Medium for the proposed new rows, which
overlap with the prompt-lifecycle, slash-commands and session-config-options researchers.

## What changed
The diff has three hunks, and all of them are insertions. No existing sentence changed.
- `+198..270` adds **Client `session` (unstable)**: `session.promptSuggestions{,.image,.audio,.embeddedContext}` and `session.commands{,.skill}`.
  `session` and `session.commands` are explicitly *not* support markers, so `{}` advertises nothing (200-204, 248-252).
- `+348..353` adds **Agent `session.options` (unstable)**: `session/options` plus `configOptions` on session setup requests.
- `+413..425` adds **Agent `session.prompt.skill` / `.skill.inline` (unstable)**, with a bold MUST at 417-418.

Line map (base -> target): <=197 same; 198-274 +73; 275-332 +80; >=333 +94.

**Cursors:** `initialization.mdx` defines no cursor capability. `extensibility.mdx:41 @ 3ea94133` says "No Client or Agent capability
is required in v2". `CursorCapabilities` (`fork` only) is a per-cursor object inside `CursorUpdate`
(`schema/v2/schema.unstable.json#/$defs/CursorCapabilities`).

**Subagents: still no real v2 marker. Keep `inferred:subagents`.**
- `subagents.mdx:8,10 @ 3ea94133`: "Exposing subagents is optional for Agents." and "Subagents need no capability."
- In both v2 schemas, `AgentCapabilities` and `SessionCapabilities` have no subagent key. `SessionCapabilities` keys at target are
  `prompt, mcp, delete, additionalDirectories, systemPrompt, fork, archive, status, options, title` (unstable), and the stable schema has
  the first five.
- `SubagentSessionCapabilities` (`cancel`) is referenced only from `SubagentUpdate.capabilities`. It is a per-child marker, not an
  `initialize` path, so the plugin's marker gate cannot use it.
- What changes is the **rationale**, not the gate. The rules are now in the draft docs, so the "RFD-only MUST, capped" wording in
  `ACP-SUBAGENT-*` and related rows should give way to "optional feature with no `initialize` marker (subagents.mdx:8,10)". The subagents
  researcher owns those rows.

## Existing registry rows citing initialization.mdx (26)
| id | classification | target citation (`initialization.mdx` part, @ 3ea94133) | note |
|---|---|---|---|
| ACP-INIT-001 | unchanged | :24,51 | |
| ACP-INIT-201 | unchanged | :110 | |
| ACP-INIT-003 | unchanged | :108,110 | |
| ACP-INIT-202 | unchanged | :108,110,112 | |
| ACP-INIT-205 | unchanged | :112-127 | |
| ACP-INIT-206 | unchanged | :108 | |
| ACP-INIT-207 | unchanged | :129 | |
| ACP-INIT-208 | unchanged | :110 | |
| ACP-ERROR-005 | unchanged (init part) | :90 | the error.mdx part belongs to that doc's researcher |
| ACP-INIT-210 | unchanged | :88,91 | |
| ACP-INIT-211 | unchanged | :92 | |
| ACP-INIT-212 | unchanged | :139 | |
| ACP-INIT-213 | unchanged (init part) | :139 | |
| ACP-INIT-214 | unchanged | :131 | |
| ACP-SCHEMA-001 | unchanged | whole doc | it validates against the re-vendored alpha.16 schema, so new keys validate |
| ACP-EXT-204 | unchanged | :156 | optional: also probe an unknown key under the new client `capabilities.session` (see D4) |
| ACP-INIT-004 | citation-only | 360 -> **:454** | |
| ACP-PROMPT-003 | citation-only | 308 -> **:388** | |
| ACP-PROMPTCAP-001 | citation-only | 306-331 -> **:386-411** | the range stops before the new `skill` fields |
| ACP-PROMPTCAP-002 | citation-only | 306-331 -> **:386-411** | |
| ACP-PROMPTCAP-003 | citation-only | 306-331 -> **:386-411** | |
| ACP-PROMPTCAP-201 | citation-only | 306-331 -> **:386-411** | text unchanged unless D3 extends it to `skill` |
| ACP-FORK-201 | citation-only | 269-273 -> **:342-346** | |
| ACP-SYSPROMPT-202 | citation-only | 298-304 -> **:378-384** | |
| ACP-CONFIG-002 | citation-only | 239-240 -> **:312-313** | |
| ACP-AUTH-007 | citation-only | 215-219 -> **:288-292** | |

No row is removed and no tier changes. The existing capability definitions (`session`, `auth.status`, `providers`, `delete`, `archive`,
`fork`, `status`, `title`, `additionalDirectories`, `systemPrompt`, `prompt.*`, `mcp.*`) keep their text, so the rows gated on them
elsewhere are not affected by this doc.

## Ledger entries citing initialization.mdx (`spec-tracker/maps/v2.toml`)
| citation | classification | target | note |
|---|---|---|---|
| :88,90 (in-flight request -> -32600) | unchanged | :88,90 | the reason does not rest on a TCK choice |
| :147 (SHOULD support all combinations) | unchanged | :147 | the reason is combinatorial scope, not a TCK choice |
| :200 (SHOULD specify capabilities) | citation-only | **:273** | the reason's "(line 149)" is still correct |

None of these reasons rests on a TCK choice.

## New requirements
Every new rule here is also stated, with a bold MUST, in a linked doc that has its own researcher. I name that doc as the primary
source and `initialization.mdx` as co-citation, so the orchestrator can merge duplicates.

1. **ACP-CLIENTCAP-2xx: no prompt suggestions without the client capability.** The agent sends no `session/update` with
   `sessionUpdate: "prompt_suggestions_update"` on a connection whose `initialize` did not supply `capabilities.session.promptSuggestions`.
   - Tier: CAPABILITY, gated on `capabilities.session` (precedent: ACP-CLIENTCAP-003).
   - Citation: `prompt-lifecycle.mdx:707` (MUST NOT); `initialization.mdx:206-215`; `extensibility.mdx:39`;
     `schema/v2/schema.unstable.json#/$defs/PromptSuggestionsUpdate`.
   - Test: the main connection already sends `capabilities: {}` (`src/tck/v2/__init__.py:23`). Scan the transcript over `session/new`,
     one prompt turn and a quiet period, the same way CLIENTCAP-003 scans for `elicitation/create`.
   - Optional second probe (D4): a connection with `capabilities: {"session": {}}`, which checks that `{}` advertises nothing (:200-204).
   - Harness: none. `agent_launch(capabilities=...)` already exists (`_helpers.py:86-88`).
   - Owner overlap: prompt-lifecycle. The rules on content types allowed in suggestions (`prompt-lifecycle.mdx:745-748`) need a connection
     that advertises `promptSuggestions`, and they belong to that researcher.
2. **ACP-CLIENTCAP-2xx: no `skill` command entries without the client capability.** No `availableCommands` entry with `type: "skill"`
   appears, neither in the `session/new` result nor in any `available_commands_update`, unless the client supplied
   `capabilities.session.commands.skill`.
   - Tier: CAPABILITY, gated on `capabilities.session`.
   - Citation: `slash-commands.mdx:171,175` (MUST NOT); `initialization.mdx:254-261`; `extensibility.mdx:40`;
     `schema/v2/schema.unstable.json#/$defs/AvailableCommand`.
   - Test: same scan on the main connection. Optional variant: `{"session": {"commands": {}}}` (:248-252).
   - Harness: none.
   - Owner overlap: slash-commands.
3. **ACP-SKILL-2xx: skill entries imply `session.prompt.skill`.** If the agent sends any `skill` entry, its `initialize` result advertises
   `capabilities.session.prompt.skill` as an object.
   - Tier: CAPABILITY, gated on `inferred:skills` (a new inferred gate, see D2). The marker under test cannot gate its own row.
   - Citation: `initialization.mdx:417-418` (MUST); `slash-commands.mdx:173`.
   - Test: a dedicated connection with `capabilities: {"session": {"commands": {"skill": {}}}}`, then `session/new` and a quiet period
     (optionally one prompt turn). Collect the `skill` entries. SKIP if there are none. Otherwise FAIL unless that connection's result has
     `session.prompt.skill` as an object.
   - Harness: none beyond the capabilities parameter. The mock client must tolerate `skill` entries, which it does because it validates
     against the unstable schema.
4. **ACP-SKILL-2xx: a skill block is rejected when not advertised.** When `session.prompt.skill` is not an object, a prompt containing
   `{"type":"skill","name":"_tck_skill"}` plus text is answered with `-32602` and is not inserted.
   - Tier: CAPABILITY, gated on `capabilities.session` (runtime negative gate, as in PROMPTCAP-201).
   - Citation: `content.mdx:24`; `slash-commands.mdx:255`; `initialization.mdx:413-417`; `#/$defs/SkillReference`.
   - Test: the same probe and quiet-period check as PROMPTCAP-201. It breaks the client MUST NOT (slash-commands:255) on purpose. See D3.
5. **ACP-SKILL-2xx: skill placement and name resolution** (primary: slash-commands; listed here for completeness). These run on
   connection 3 when a `skill` entry was listed:
   - (a) With `prompt.skill` advertised, a prompt that starts with a `skill` block naming a listed skill and continues with text is
     accepted. Gate: `capabilities.session.prompt.skill`. Citation: :413-418, slash-commands:236-238,253.
   - (b) With `prompt.skill` but no `inline`, a prompt with text first and then the `skill` block gets `-32602`. Citation: :416-417,
     :421-424, slash-commands:238,255.
   - (c) With `inline` advertised, the same out-of-first-position prompt is accepted. Gate: `...prompt.skill.inline`.
   - (d) With `prompt.skill` advertised, a `skill` block whose `name` is not listed gets `-32602`.
   - All four SKIP when no `skill` entry was listed. A listed name is needed so that (b) cannot pass only because the name was unresolvable.
6. **ACP-OPTIONS-2xx: the `session.options` marker is honored** (primary: session-config-options).
   - (a) `session/options` with the same workspace params as `session/new` (`cwd`) returns a result that validates as
     `SessionOptionsResponse`, not an error.
   - (b) `session/new` with `configOptions` containing an entry with an unknown `configId` succeeds: the entry is ignored, not rejected.
   - Tier: CAPABILITY, gated on `capabilities.session.options`.
   - Citation: `initialization.mdx:348-353`; `session-config-options.mdx:482,486,581`; `(Draft RFD) rfds/session-options` only as context,
     because the docs state the rule.
   - Harness: none. Use the ACP-FORK-201 shape.

## New ledger entries
None from `initialization.mdx`. Every new agent-side rule in it can be observed by a row that can SKIP. Two kinds of rule are left out
on purpose:
- The descriptive "may include" lines (:223-237) are MAY or client-side.
- The rules on suggestion content types are prompt-lifecycle's to classify.

## Decisions for the user
- **D1, tier for new rows 1 and 2.** Recommend CAPABILITY on `capabilities.session`, following the ACP-CLIENTCAP-003 precedent: the rule
  binds every agent, but observing it needs a session. The alternative is MANDATORY. Note that `initialization.mdx` itself uses a
  lowercase "must"; the bold MUST/MUST NOT comes from the linked docs.
- **D2, gate for new row 3.** Recommend `inferred:skills` (CAPABILITY). This adds a new inferred feature to the list in
  `docs/requirements.md`. The alternative is MANDATORY that SKIPs when the condition never arises (the ACP-AUTH-006 precedent).
- **D3, the unadvertised-skill negative.** Recommend a separate row, new row 4, rather than adding `skill` to ACP-PROMPTCAP-201. A failure
  on the unstable `skill` type would otherwise taint the row for the stable types, and the citations differ.
- **D4, probes where `{}` is not a marker.** Recommend adding the cheap second connections (`session: {}`, `session.commands: {}`) to new
  rows 1 and 2. Optionally, ACP-EXT-204 could also probe an unknown key under `capabilities.session`.
- **D5, subagents.** Keep `inferred:subagents`. Refresh the rationale text and RFD labels (`(Active RFD)` becomes `(Preview RFD)`) in the
  subagent rows, and cite `subagents.mdx` first. The subagents researcher owns this.

## Follow-ups (not caused by this update)
- `src/tck/common/plugin.py:446` cites "v2 draft initialization.mdx:100" for `-32022`. The rule is at :112, and :100 is "agree on a
  protocol version". This comment was already stale before this update.
- `spec-tracker/maps/v2.toml:82-89` `core_doc` `code` list: add any new test module that implements rows 1-6.
