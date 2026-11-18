# Review: milestone 1 (re-vendor 3961af94 -> 3ea94133), range 6bce0b3..7254513

Product commits reviewed: 5495e0f (v1), 7254513 (v2). I read every file at the commit with `git show 7254513:<path>`,
not from the working tree. The working tree has uncommitted V1-PLAN work in progress (`emits_file_plan.py`,
`test_plan_path.py`, ...), which is outside this range.

## Method

- Vendored files: `cmp` of `git show 3ea94133:schema/v{1,2}/{schema,meta}.unstable.json` against the vendored copies.
- Citations, by script: every `<doc>.mdx:<lines>` token in all 105 changed non-JSON files was aligned between base
  and head, and the cited text at 3961af94 was compared with the cited text at 3ea94133. 1021 pairs: 897 have
  identical text, and I read all 124 that differ. The same comparison ran over the 482 files the range did not
  touch (same lines at both revisions), and again over bare `:NNN` / `line NNN` pointers, resolved against the
  nearest preceding `.mdx` name. A separate grep found the `RFD:NNNN` shorthand.
- Row semantics: AST comparison of every `Requirement(...)` in both registries, all fields except `citation`.
- Code: a grep of the diff for changed lines that are not comments, docstrings or citation strings.
- Stages: computed from `docs/docs.json` at 3ea94133.
- Schema pointers: every pointer in v1/v2 src, tests and maps resolved against the head schema. Positional
  (`anyOf/N`) pointers were compared between the old and new schema.
- `uv run pytest` was not run. No finding depends on a test result.

## Verified clean

- All four vendored files are byte-identical to 3ea94133. `SCHEMA_REVISION` (v1, v2), `VENDORED.md` commit and date,
  and v2 `2.0.0-alpha.16` all agree.
- No row was added or removed: v1 108/108, v2 233/233. Tier and capability are unchanged on every row. The only
  `text` changes are: `(Active RFD)` -> `(Preview RFD)` on v1 SUBAGENT-001/2/3/4/7/8/13/14/16/17 and v2
  SUBAGENT-001/3/4/7/8/13/14/16/17/202 and RESUME-002/205/209; PATCH-211 drops "; an Active RFD allows this
  explicitly"; META-203 changes `:108-115` -> `:111-118`. No code-logic line changed except the three v2 enum sets.
- The v2 enum sets match the head schema exactly: `SessionUpdate` gains `cursor_update`,
  `prompt_suggestions_update` and `replay_complete`; `PlanUpdateContent` = {items, markdown};
  `AvailableCommand` = {command, skill}. No v2 fixture or test sends a `file` plan.
- All 124 v1 and 245 v2 schema pointers resolve. The positional pointers name the same node at both revisions.
- Stage labels: subagents and plan-operations are Preview. get-auth-state, proxy-chains, session-archive,
  session-fork, session-set-title, session-status, mcp-over-acp and `rfds/v2/*` are Draft. session-config-options
  is Completed. All 69 subagents labels are Preview. No "Active" stage wording is left in `src/`, `tests/` or
  `spec-tracker/maps` (the remaining hits are listed under Follow-ups).
- Dropped Draft-RFD citations: the remaining docs citations state the rule each row relies on. STATE-209 and
  STATE-210 are covered by PL:215 "SHOULD send a repeated `state_update`" and PL:218. PROMPT-209 and
  INFO-CONCURRENT-201 by PL:400 and 402. PATCH-211 by PL:226 "A tool call that references a listed terminal is
  live" and SS:476. FORK-206 by SS:50. TOOLCANCEL-206 and TERMCANCEL-206 by TC:456,459 and TC:602,605.
  JSONRPC-003 by `overview.mdx:242` (v1) and `:231` (v2); for v1 the plan's `schema.mdx:285-302` (`mcp/message`)
  was also added.
- spec-tracker `test_maps_v2.py`: the edit is justified. At target, "Session-directed messages" lost "(unstable)",
  and "Prompt suggestions (unstable)" (PL:703) and "Session cursors (unstable)" (PL:909) are new standalone `####`
  sections in "3. Agent reports output", alongside notices and compaction. The map comment was updated to match.
- The "Needs review" rows and entries from plan sections 1.1 and 1.2 (CLIENTCAP-007, SUBAGENT-011/012, CANCEL-209,
  -213, INFO-CANCEL-201, RESUME-202/205/206/213/217, CLOSE-205, ENUM-201, TOOLCANCEL/TERMCANCEL-204..209,
  SUBAGENT-201, ledger RFD-SA 584-585, PL:341,388, SS:57, SS:476, `cancellation.mdx:42,43`, `overview.mdx:269`,
  elicitation 225-228,236) each point at the text the row relies on. Apart from the findings below, the plan 1.3
  hand fixes I sampled were made (PT:40/851, `asks_permission` 140-151, `open_enums` 240-243, `protocol.py`,
  `test_extensibility`, `rejects_unknown_capability_fields` :160, `schema.mdx:990`, `content.mdx:24`,
  `cancellation.mdx:33`, `error.mdx:54,68`, `plugin.py` `initialization.mdx:112`, PL offsets, re-cite to PL:1452
  plus RFD-SA 1268).
- No `.agents/` references in product files.

## Findings (most severe first)

### 1. should-fix: `RFD:NNNN` shorthand pointers into the Subagents RFD were not remapped (29 occurrences)

- Where:
  - `src/tck/v1/conformance/_child_cancel.py:12,15,20`
  - `src/tck/v1/conformance/test_subagent_controls.py:7,112`
  - `src/tck/v2/conformance/_child_cancel.py:14,17,22`
  - `src/tck/v2/conformance/test_subagent_controls.py:7,8,105`
  - `tests/v1/test_cli.py:1795`, `tests/v2/test_cli.py:4803`
  - v1 fixtures: `child_ends_before_cancel.py:5`, `child_cancel_cancels_parent.py:3`,
    `child_ignores_cancel_then_ends.py:5`, `cancellable_subagent.py:9,12`, `child_cancel_stops_sibling_too.py:4`,
    `child_cancel_ignored.py:3`
  - v2 fixtures: the same set, plus `parent_cancel_leaves_child_running.py:3` and
    `announces_background_child_after_snapshot.py:5` (the latter was touched by 7254513 but kept `RFD:1075-1087`).
- Defect: these docstrings cite `RFD:1069-1073`, `1071-1073`, `1075-1087`, `1089-1093`, `1089-1095` and `1093-1095`.
  At 3ea94133 those lines are the "Restricted session methods" section ("Client-initiated methods that modify a
  child session ... allowlist"), not child cancellation.
- Evidence: old 1069-1095 equals new 1113-1139 byte for byte (`diff` of the two blocks is empty), so the offset
  is a uniform +44. `impact-v1-rfd-subagents.md` already gives `1113-1117,1133-1139` for the row citations, and
  those rows were updated. The `RFD:` form matches neither the `spec-impact` regex nor the plan 1.3 list, so
  every one was missed.
- Failure scenario: a contributor checking SUBAGENT-016/017 or the child-cancel driver against the cited lines
  reads the restricted-methods rules and concludes the code has no support, or "fixes" it toward the wrong rule.
- Fix: add 44 to each pointer (1069-1073 -> 1113-1117, 1071-1073 -> 1115-1117, 1075-1087 -> 1119-1131,
  1089-1093 -> 1133-1137, 1089-1095 -> 1133-1139, 1093-1095 -> 1137-1139).
- Confidence: confirmed by reading.

### 2. should-fix: ACP-CANCEL-214 cites a blank line (`prompt-lifecycle.mdx:403`)

- Where: `src/tck/v2/requirements.py:1448`; the same pointer is in `src/tck/v2/conformance/test_cancel.py:569,630`
  and `tests/fixtures/agents/v2/_base.py:319`.
- Defect: at 3ea94133, PL:403 is empty. The rule the row relies on ("`session/cancel` and `session/close` drop
  every prompt the Agent has not inserted. The Agent answers each of them with `-32800`") is on PL:404.
- Evidence: `git show 3ea94133:docs/protocol/v2/draft/prompt-lifecycle.mdx`: line 402 "A held prompt's response
  stays pending ... two ways:", 403 blank, 404 the `session/cancel` bullet, 405 the `$/cancel_request` bullet. The
  bad number comes from `impact-v2-prompt-lifecycle.md:77`, whose numbering is one too low in this block.
- Failure scenario: the row's only prose citation for its MUST is an empty line. `test_registry.py` does not check
  line content, so nothing catches it.
- Fix: `:403` -> `:404` in all four places.
- Confidence: confirmed by reading.

### 3. should-fix: ACP-JSONRPC-007 cites only the `session/cancel` bullet; the `$/cancel_request` rule moved to PL:405

- Where: `src/tck/v2/requirements.py:1415` (`prompt-lifecycle.mdx:341,404,413`).
- Defect: old `:384` covered both "withdraw it with `$/cancel_request`" and the `session/cancel` fallback. At target
  these are separate bullets, 404 (`session/cancel`) and 405 (`$/cancel_request` "is best effort ... An Agent that
  honors it answers with `-32800` and does not insert the message. Otherwise the prompt is inserted as usual"). The
  row needs both, and the plan's description of 404 (from the same off-by-one research table, line 75) is the text
  of 405.
- Failure scenario: a maintainer checking the row's "success (inserted) or `-32800`" outcome against PL:404 finds
  only the `session/cancel` rule, not the `$/cancel_request` rule that defines it.
- Fix: `341,404-405,413`.
- Confidence: confirmed by reading.

### 4. should-fix: a ledger reason pointer is stale, and the plan's reword of that entry repeats the wrong line

- Where: `spec-tracker/maps/v2.toml:515` (the SCO:390 fan-out entry): "the agent's choice (session-setup.mdx:54)".
- Defect: two bullets were inserted above it. At target SS:54 is "Closing a session ends it on the connection
  but doesn't discard it". The multi-connection rule ("Whether a session can be active on more than one
  connection at once is up to the Agent") is now SS:56.
- Evidence: the `diff` of v2 session-setup shows inserts at 35 and 53. The plan section 1.2 row "`SCO:375` fan-out
  | reword: ... multi-connection activity is optional (`SS:54`)" uses target numbering elsewhere, so the later
  slice will carry the wrong line forward.
- Failure scenario: a reviewer following the pointer reads the close semantics and cannot find the
  "agent's choice" premise the deferral rests on.
- Fix: `session-setup.mdx:56` now, and tell the orchestrator that the plan 1.2 reword should say `SS:56`.
- Confidence: confirmed by reading.

### 5. nit: v2 ledger reason pointers left at base numbering while their v1 twins were hand-fixed

- Where:
  - `spec-tracker/maps/v2.toml:705`: "client rule at :1126-1128". Now RFD-SA 1173-1175, which v1
    `v1.toml:369` already uses.
  - `spec-tracker/maps/v2.toml:715`: "(:945)". Now RFD-SA 982, which v1 `v1.toml:379` already uses.
  - `spec-tracker/maps/v2.toml:431`: "client MUST at line 441". Now SS:526; the entry's own citation moved
    443 -> 528.
- Defect: at target, RFD-SA 1126-1128 and 945 hold unrelated text, and SS:441 is no longer the client MUST.
- Note: plan 1.2 rewrites or deletes all three entries in later slices (V2-SA1, and the ADDDIRS-204 promotion), so
  this matters only if those slices slip. It is cheap to fix now for consistency with v1.
- Confidence: confirmed by reading.

### 6. nit: `docs/mock-client.md:76` still cites base line numbers

- Defect: "(v1 prompt-turn.mdx:641; v2 prompt-lifecycle.mdx:1177; ...)" should be 851 and 1452, the same values the
  code comments it describes were changed to. The file is not in the range and not on the plan 1.3 list.
- Failure scenario: the contract doc points readers at PT:641 and PL:1177, which no longer state the
  cancelled-permission rule.
- Confidence: confirmed by reading.

### 7. nit: `tests/fixtures/agents/v2/_base.py:590`: "(session-setup.mdx:110, 134)"

- Defect: 108 -> 110 was fixed, but 134 is "  }" inside the JSON example. The intended paragraph ("`configOptions`
  and `availableCommands` are optional ...") is SS:138. It was already stale at base, where 134 was a closing
  code fence and 136 the paragraph.
- Fix: `110, 138`.
- Confidence: confirmed by reading.

### 8. nit: v1 and v2 ACP-SUBAGENT-011 cite different RFD ranges for the same rule

- Where: `src/tck/v1/requirements.py:1369` cites `docs/rfds/subagents.mdx:667-690`;
  `src/tck/v2/requirements.py:556` cites `667-676,685-690`.
- Defect: the v1 range also takes in the new 678-683 paragraph ("When the Agent has no evidence of the sender, it
  reports the incoming view without `senderSessionId` and **MUST NOT** assume the parent"). That paragraph is a
  different rule, and V1-SA1/V2-SA2 handle it later.
- Fix: use `667-676,685-690` in v1 too, so both versions cite the same thing until the SA slices.
- Confidence: confirmed by reading.

### 9. nit (scope): `VENDORED.md` procedure rewritten in both versions

- Where: `src/tck/v1/schema/VENDORED.md:13-29`, `src/tck/v2/schema/VENDORED.md:16-32`.
- Defect: replacing `cp` with `git show <commit>:...` was not part of the milestone goal. It is a reasonable change,
  but it leaves "Refreshing" step 1 ("Confirm the spec repo checkout's current HEAD") pointless, since reading by ref
  ignores HEAD. `docs/spec-updates.md:83` still says "copy the two `.unstable.json` files".
- Fix: drop or reword step 1 in both `VENDORED.md` files, or move this change to the docs slice.
- Confidence: confirmed by reading.

## Counts

blocker 0, should-fix 4, nit 5.

## Follow-ups and open questions (not defects in this range)

- `spec-tracker/src/spec_tracker/impact.py:213` docstring still says "`Active > v2` pages are Active". Slice 28 (docs)
  lists `docs/requirements.md:131,134` and `docs/spec-updates.md:43`, but not `impact.py`.
- `impact-v2-prompt-lifecycle.md` lines 75 and 77 number the PL:402-405 block one too low (findings 2 and 3). Any
  later slice that reuses its table for this block, such as PROMPT-215's `PL:400-404`, should re-check against
  3ea94133.
- The known leftovers listed in the brief (ACP-PLAN-001 pointing at `PlanUpdateContent` and stale
  `agent-plan.mdx:127` / `plan-operations.mdx:63`; the cost entry RFD-SA 1168-1170, which now holds unrelated v1
  text; v2 `agent-plan.mdx:119`; SHOULD/MUST drift at PL:1452, `cancellation.mdx:42` and elicitation 226, all
  owned by later slices) were seen and are not flagged.
