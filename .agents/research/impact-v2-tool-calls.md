# Impact: v2 `docs/protocol/v2/draft/tool-calls.mdx` (3961af94 -> 3ea94133)

**Sources checked:** agent-client-protocol @ `3ea94133` (read with `git show 3ea94133:<path>`; the checkout's HEAD is
`6ace4f6a`, see Open questions): `docs/protocol/v2/draft/tool-calls.mdx` (whole, 779 lines), diff 3961af94..3ea94133,
`docs/protocol/v2/draft/subagents.mdx:60-80,290-300,365-380`, `docs/protocol/v2/draft/extensibility.mdx:236-250`,
`docs/protocol/v2/draft/prompt-lifecycle.mdx:1452`, `docs/rfds/subagents.mdx` (Preview), `docs/rfds/v2/background-work.mdx`
(Draft) + diff, `docs/docs.json:221-243`, `schema/v2/schema.unstable.json` (`RequestPermissionSubject`, `Diff`, `DiffPatch`,
`DiffChange`, `TerminalUpdate`, `AbsolutePath`, `CancelToolCallRequest`), `schema/v2/schema.json` (`ToolCallContent`).
acp-tck: `src/tck/v2/requirements.py` (34 rows cite the doc), `spec-tracker/maps/v2.toml` (12 entries),
`src/tck/v2/conformance/test_item_controls.py`, `_helpers.py:2431-2700`, `src/tck/v2/open_enums.py`,
`tests/v2/test_open_enums.py:142`, `tests/fixtures/agents/v2/_base.py`. Reference SDKs not consulted: every changed
rule is stated explicitly in the docs.
**Confidence:** high for the classifications and line numbers. Medium for the tier picks flagged under Decisions.

**Line map.** Every hunk above line 752 replaces lines one for one, so every line number up to 752 is the same at the
target. Lines after 752 shift by +5 (`-752,0 +753,5`). No row or ledger entry cites a line after 742, so **no
tool-calls line citation needs renumbering**. Changed content: 326, 457, 459, 603, 605, 728-731, 749-751, new 753-756.

## Rows citing tool-calls.mdx

| id | classification | target citation (tool-calls part) | note |
|---|---|---|---|
| ACP-SUBAGENT-002 | citation-only | `tool-calls.mdx:740-742` (+ add `754-756`) @ 3ea94133 | The RFD half `docs/rfds/subagents.mdx:636-638 (Active RFD)` becomes `:647-649 (Preview RFD)`. Docs precedence: `subagents.mdx:69,74 @ 3ea94133` now states the **MUST** (announce before a `session` content item references the child), so cite it first and keep the RFD as secondary context only. `:741`'s "must" is lowercase. Add `:754-756` ("adds a reference only if it can resolve the handle to a known session"): this row already judges that rule. Tier and gate unchanged. "Sessions (unstable)/Draft only" dropped at 728-731; TCK impact nil (`TOOL_CALL_CONTENT_TYPE` already has `session`, `protocol.py:109`). The subagents researcher may own the other halves. |
| ACP-PERM-201 | unchanged | `:209,244-278,356-374` | |
| ACP-PERM-202 | unchanged | `:302-303,357` | |
| ACP-PERM-203 | unchanged | `:340,423` | |
| ACP-PERM-002 | unchanged | `:346-347,423` | |
| ACP-PERM-204 | unchanged | `:348-349,423` | |
| ACP-INFO-BACKGROUND-202 | unchanged (tool-calls part) | `:268` | Its `prompt-lifecycle.mdx:1173` half belongs to that doc's researcher. |
| ACP-CANCEL-209 | unchanged (tool-calls part) | `:326` | `:326` now says the **Client SHOULD** dismiss and answer `cancelled` when the Agent sends `$/cancel_request`. The mock client already does this in hold mode (`_helpers.py:2016-2020`). The rule binds the client, so it needs no row or ledger entry. Adjacent: `prompt-lifecycle.mdx:1452 @ 3ea94133` now makes the Agent's `$/cancel_request` a **MUST**. That belongs to the prompt-lifecycle researcher; cite `:326` there as secondary. |
| ACP-PATCH-206 | unchanged | `:493-499,523-531` | |
| ACP-PATCH-207 | unchanged | `:536-537,566-570` | |
| ACP-PATCH-208 | unchanged | `:41-54,198-200,270-273` | |
| ACP-PATCH-209 | unchanged | `:209,268` | |
| ACP-PATCH-210 | unchanged | `:102-108,421,423` | |
| ACP-PATCH-211 | changed text + citation | `:423` | `docs/rfds/v2/background-work.mdx:56` is now a **Draft RFD** (same line). The draft docs the row already cites state the broader rule, so drop the RFD citation and the phrase "an Active RFD allows this explicitly" (Draft RFDs are cited only where nothing else states the rule). `:423` is unchanged, and the row's "docs are not uniform" note still holds. |
| ACP-PATCH-212 | unchanged | `:440,600` | |
| ACP-TOOLCANCEL-201 | unchanged | `:440,456,458` | |
| ACP-TOOLCANCEL-202 | unchanged | `:423,458` | |
| ACP-TOOLCANCEL-203 | citation-only | `:440,456-458` | `docs/rfds/subagents.mdx:1042-1045 (Active RFD)` becomes `:1081-1084 (Preview RFD)`. Docs precedence: cite `subagents.mdx:369,374 @ 3ea94133` (restricted methods: "Only while that tool call ... advertises its own `capabilities.cancel`. The child's `cancel` capability is not needed") first. `:457` now links that section instead of the RFD. |
| ACP-TOOLCANCEL-204 | unchanged (impl. note) | `:440,456,459` | The quoted sentence is still verbatim at `:459`. If N4 lands, `_StaleProbe` (`_helpers.py:2644`) should skip the main accepted item, so a repeat-request defect fails only N4. |
| ACP-TOOLCANCEL-205 | unchanged | `:459` | |
| ACP-TOOLCANCEL-206 | citation-only | `:456,459` | Drop `docs/rfds/v2/background-work.mdx:126`, now a Draft RFD (same line). `:459` states the rule. |
| ACP-TOOLCANCEL-207 | unchanged | `:459` | |
| ACP-TOOLCANCEL-208 | unchanged | `:440,456,459` | |
| ACP-TOOLCANCEL-209 | unchanged | `:459` | |
| ACP-TERMCANCEL-201 | unchanged | `:600-604` | `:603` changes only its link. |
| ACP-TERMCANCEL-202 | unchanged | `:604` | |
| ACP-TERMCANCEL-203 | citation-only | `:600-604` | Same as TOOLCANCEL-203: cite `subagents.mdx:369,374` first; the RFD citation becomes `:1081-1084 (Preview RFD)`. |
| ACP-TERMCANCEL-204 | unchanged (impl. note) | `:600,602,605` | Same `_StaleProbe` note as TOOLCANCEL-204. |
| ACP-TERMCANCEL-205 | unchanged | `:605` | |
| ACP-TERMCANCEL-206 | citation-only | `:602,605` | Drop `docs/rfds/v2/background-work.mdx:165`, now a Draft RFD (same line). |
| ACP-TERMCANCEL-207 | unchanged | `:605` | |
| ACP-TERMCANCEL-208 | unchanged | `:587,600,602,605` | |
| ACP-TERMCANCEL-209 | unchanged | `:605` | |
| ACP-ENUM-201 | changed (sites widened, Decision 1) | `:76,372,419,662,685-686,700-701` (unchanged) + add `:259-265` | Add `session/request_permission` `subject.type` as a site, legal set `{tool_call, command}` derived from `$defs/RequestPermissionSubject` (its `other` branch is the fallback, and it reserves `_` for extensions). The rule is `extensibility.mdx:242 @ 3ea94133` (MUST NOT define custom non-underscore values) plus `tool-calls.mdx:263` ("Custom or future subject types may appear"). Change: in `OpenEnumScan.scan_permission_request`, check `subject["type"]`. Delete the row's "`subject.type` is not checked" and the matching `open_enums.py:8` note. Flip `tests/v2/test_open_enums.py:142` (`{"type": "hologram"}` becomes a violation, `_hologram` stays legal). Add the schema pointer to the citation. The existing permission fixture's subject is `tool_call`, so the change needs no new fixture. History: the exclusion came in with `13c4f7a` with no recorded reason. The extensibility researcher owns the row's `extensibility.mdx` re-cite (`:238-243`); coordinate the text edit. |

## Ledger entries citing tool-calls.mdx

| citation | classification | target citation | note |
|---|---|---|---|
| `:268` (background permission) | unchanged | `:268` | |
| `:385` (name vs kind) | unchanged | `:385` | |
| `:387` (perform only approved op) | unchanged | `:387` | |
| `:376-380,388` (remembered decisions) | unchanged | same | |
| `:389` (oversight) | unchanged | `:389` | |
| `:466` (preserve unknown content) | unchanged | `:466` | |
| `:496,497` (terminalId reuse) | unchanged | same | |
| `:578,579` (output before exitStatus) | unchanged text; **reason rests on a TCK choice** | same | "possible but not yet built" names no blocker. See Decision 4 (promote to an ADVISORY row, N8). |
| `:622,653-661` (git_patch paths) | **removed** (promoted to N1/N2) | `:615-617,622,653-660,690-696` | The same reason problem as above. N1 and N2 cover the statement entirely, so delete the entry in the slice that adds them. |
| `:460` (tool cancel and foreground state) | unchanged | `:460` | |
| `:606` (terminal cancel effects) | unchanged | `:606` | |
| `prompt-lifecycle.mdx:1173; tool-calls.mdx:268` | unchanged (tool-calls part) | `:268` | The prompt-lifecycle line moves; that is its researcher's job. |

## New requirements (provisional ids)

All passive diff checks run over the one-turn drive `test_patches.py` already uses (`_drive_one_turn`). They walk every
tool-call content item: in a `tool_call_update` `content` array, in a chunk's single `content`, and in a
`subject.toolCall.content` (the walker is like `_helpers.py:729-747`). Each SKIPs when no `diff` item appears. They
are **CAPABILITY `capabilities.session`**: a docs MUST, placed under the v2 session-baseline rule like ACP-PATCH-206.
For `AbsolutePath` (POSIX `/…`, a Windows drive path or a UNC path) reuse `is_absolute_path` (`_helpers.py:770`). The
mock client needs no new behaviour for N1-N3. The fixtures are already compliant: `_base.py:1026-1030` emits an
absolute path and a `diff --git` text.

- **N1 `ACP-PATCH-213`** (CAPABILITY, `capabilities.session`). Every `diff` content item's `changes[].path` and every
  present `changes[].oldPath` is an absolute path, and no `path` value appears in more than one entry of `changes`.
  `AbsolutePath` is a bare string, so schema validation (ACP-PROMPT-002) lets a relative path through.
  Cite `tool-calls.mdx:615,622,690-696 @ 3ea94133`, `$defs/DiffChange`, `$defs/AbsolutePath`.
  Negative fixture: a `modify` with `path: "src/a.txt"` and no `patch`, so only N1 fails. Uniqueness is declarative
  (Decision 3).
- **N2 `ACP-PATCH-214`** (CAPABILITY, `capabilities.session`). For a `patch` with `format: "git_patch"`, every path on
  a `---`, `+++`, `rename from/to` or `copy from/to` line of `patch.text` is absolute, or `/dev/null` on `---`/`+++`.
  Each path is compared after Git-unquoting and after stripping the trailing TAB Git appends to paths that contain
  spaces. Absolute rules out the `a/`/`b/` prefix. Each such non-`/dev/null` path equals some entry's `path` or
  `oldPath` ("describes only those paths and operations"). Do not judge the `diff --git` header, which is ambiguous
  with spaces (`:674-676`). Formats other than `git_patch` are not judged (`:662`).
  Cite `tool-calls.mdx:615-617,653-660 @ 3ea94133`, `$defs/DiffPatch`.
  Negative fixture: Git-default `a/…`/`b/…` paths with absolute `changes`.
- **N3 `ACP-PATCH-215`** (CAPABILITY, `capabilities.session`). A `git_patch` `patch.text` has no surrounding commit
  metadata or email envelope: its first line begins `diff --git `. Optionally it also has no trailing `-- ` signature
  line followed by a Git version after the last hunk; that heuristic is weaker, because a removed line `- ` renders as
  `-- `.
  Cite `tool-calls.mdx:653-654,661 @ 3ea94133`.
  Negative fixture: a text that starts `From <sha> Mon Sep 17 00:00:00 2001\nFrom: …\nSubject: …\n---\n` followed by an
  otherwise valid absolute diff.
- **N4 `ACP-TOOLCANCEL-210`** (CAPABILITY, `inferred:toolCallCancel`; rejection judged like 204/206/208).
  - Rule: `tool_call/cancel` sent again for a tool call whose first `tool_call/cancel` was accepted, after that tool
    call reported a final status, is rejected with an error, not a result.
  - Cite `tool-calls.mdx:456,458-459 @ 3ea94133`, `$defs/CancelToolCallRequest`.
  - Test: in `drive_item_cancel`, add a follow-up `_RepeatProbe` per kind. Once the main probe's outcome is
    `confirmed` (the 202 final update arrived), it re-sends the request for `main.result.item_id`. An error PASSes. A
    result, or no response within half the per-response timeout, FAILs.
  - The rule cannot race: a final status is final (ACP-PATCH-210), and the spec names this exact request. When the
    agent cleared `cancel` on the final update, the repeat breaks the client rule at `:456`. The probe rules allow
    that because `:459` defines the answer.
  - SKIPs when the main cancel was not confirmed.
  - Update the module docstring, `test_item_controls.py:38-40` ("no row judges the answer to a repeat request"), and
    make `_StaleProbe` skip the main item.
  - Fixtures: the conforming fixture already answers `-32602` for an id that is no longer open (`_base.py:112-122`).
    Negative fixture: one that answers `{}` to a repeat for an id it accepted before and clears `cancel` on the final
    update, so 204 is not hit.
- **N5 `ACP-TOOLCANCEL-211`** (ADVISORY). The rejection in N4 uses `-32602`. Cite `:459`. Same split as 205/207/209:
  the sentence naming the code carries no RFC keyword.
- **N6 `ACP-TERMCANCEL-210`** (CAPABILITY, `inferred:terminalCancel`). `terminal/cancel` sent again after an accepted
  one, once the terminal reported `exitStatus`, is rejected with an error. Cite `tool-calls.mdx:602,604-605 @ 3ea94133`
  and `$defs/CancelTerminalRequest`. Test and fixtures mirror N4, triggered by the 202 `exitStatus`.
- **N7 `ACP-TERMCANCEL-211`** (ADVISORY). N6's code is `-32602`. Cite `:605`.
- **N8 `ACP-PATCH-216`** (ADVISORY, optional, Decision 4). No `terminal_output_chunk` arrives for a `terminalId` while
  its effective `exitStatus` is concrete. Passive, same drive. SKIPs when no terminal reports `exitStatus`. Cite
  `tool-calls.mdx:578-579`. It replaces ledger `:578,579`.

## New ledger entries

- `docs/protocol/v2/draft/tool-calls.mdx:528-529 @ 3ea94133`
  - Statement: Agents SHOULD provide a terminal's `command` on its first update when applicable.
  - Reason: Not decidable. The docs give no criterion for when a command does not apply or is not yet known, so a
    first `terminal_update` without `command` cannot be told from a legitimate one. ACP-PATCH-208 likewise does not
    judge the `name` SHOULD, which is conditioned on "when it is available".
- `docs/protocol/v2/draft/tool-calls.mdx:617-618,648 @ 3ea94133`
  - Statement: Agents SHOULD provide `patch` whenever feasible.
  - Reason: Not decidable. "Whenever feasible" is the agent's judgement. The docs themselves omit `patch` for binary
    and symlink changes (`:709-724`), and `fileType` is optional, so a diff without `patch` cannot be judged a miss.
- `docs/protocol/v2/draft/tool-calls.mdx:753-754 @ 3ea94133`
  - Statement: Because `content` on `tool_call_update` replaces the whole array, an Agent that sends new content
    includes its session references again.
  - Reason: Not decidable. A later `content` array without an earlier reference may deliberately drop a display-only
    link, and the TCK cannot tell a forgotten reference from a dropped one.
- `docs/protocol/v2/draft/tool-calls.mdx:749-751 @ 3ea94133`
  - Statement: A message a parent sends a child is reported as a session-directed message, not through a tool call.
  - Reason: Not decidable. A tool call may legitimately report the sending operation (`subagents.mdx:292`), and
    whether it stands in for the message is agent intent.
  - Coordinate with the v2 subagents researcher so this ends up as one entry. This entry is optional: the sentence is
    descriptive, with no RFC keyword.

No reason above rests on a TCK choice.

## Decisions for the user

1. **ENUM-201 `subject.type`: row, not ledger.** Recommend widening, since the value is agent-emitted and mechanically
   decidable. Confirm that the original exclusion (`13c4f7a`) had no reason I could not find.
2. **Repeat cancel (`:459`, `:605`): new rows N4-N7, rather than widening 204/208.** Recommend new rows. The trigger
   (a repeat after acceptance) is a distinct probe with no race, and the current design deliberately never repeats
   (`test_item_controls.py:38-40`). The tiers follow the existing 204/205 encoding: rejection CAPABILITY, code
   ADVISORY.
3. **Diff rules D3/D4/D8: rows N1-N3, and delete ledger `:622,653-661`.** Recommend rows. They are MUSTs that the
   wire decides, at the same cost as ACP-PATCH-206. Sub-choice: "each `path` appears in at most one entry" (`:622`)
   is declarative. Keep it in N1 (recommended: it is a structural invariant), or move it to its own ADVISORY row.
   Optional: fold the uncovered `locations[].path` absolute rule (`:769-770`, `$defs/ToolCallLocation`) into N1 or a
   sibling row. It is pre-existing, neither covered nor ledgered.
4. **Ledger `:578,579` names no blocker.** Its reason is "possible but not yet built", which rests on a TCK choice.
   Recommend promoting it to the ADVISORY row N8. The alternative is rewording it as Deferred, but there is no real
   blocker to name.
5. **Terminal `command` SHOULD and `patch` SHOULD: ledger (recommended), or ADVISORY rows.** A row would flag the
   legitimate cases.
6. **PATCH-211, TOOLCANCEL-206, TERMCANCEL-206: drop the now-Draft background-work RFD citations.** Recommended,
   because the docs state each rule. The alternative is relabelling them `(Draft RFD)`.

## Open questions

- The checkout's HEAD (`6ace4f6a`) is past the target. It adds "Agents **MUST** include at least one entry in
  `changes`" at `tool-calls.mdx:615`, and touches `schema.json` and `schema.unstable.json`. This is out of range for
  this update. Flag it for the next one, where it would extend N1.
- `$defs/CancelToolCallRequest`'s description at the target lacks the new repeat sentence. The schema is less
  detailed, not in conflict.
- `prompt-lifecycle.mdx:1452` gives the agent a new MUST to send `$/cancel_request` on `session/cancel`. That belongs
  to the prompt-lifecycle researcher; it may change ACP-CANCEL-209.
