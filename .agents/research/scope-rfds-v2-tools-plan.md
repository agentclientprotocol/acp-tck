# Scope: backfilling four formerly-Active `rfds/v2/*` RFDs in v2 (terminal-output, diff-file-states, client-filesystem-terminal-capabilities, plan-variants)

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (target; checkout
`../agent-client-protocol-2`, HEAD verified), diffed against base `3961af94`: `docs/rfds/v2/{terminal-output,
diff-file-states,client-filesystem-terminal-capabilities,plan-variants}.mdx`, `docs/protocol/v2/draft/{tool-calls,
agent-plan,prompt-lifecycle,security}.mdx`, `docs/protocol/v2/migration.mdx` (non-draft, context only),
`schema/v2/schema{,.unstable}.json`, `schema/v2/meta.unstable.json`, `docs/docs.json`. acp-tck @ `ceef9a8`:
`src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`, `src/tck/v2/conformance/test_patches.py`,
`tests/fixtures/agents/v2/_base.py`. Reference SDKs not consulted: no rule here depends on runtime behaviour the spec
leaves implicit.
**Confidence:** high. All four RFDs were absorbed almost verbatim into the v2 draft docs/schema, so every agent-side
rule has a docs citation; the remaining judgement calls are only about lowercase "should" sentences.

## Answer

Essentially no RFD-specific work. At the target all four RFDs are **Draft** (`docs/docs.json`: group "Draft > v2";
they were "Active > v2" at base). Three are byte-identical to base; `plan-variants` only dropped the unstable `file`
plan type (RFD lines 28, 45, 59, 71, 81, 96). Every agent-side normative rule (bold MUST/SHOULD, or schema-enforced
wire shape) in them is also stated by the v2 draft docs or schema, so under "docs take precedence" those rules belong
to the doc audit of `tool-calls.mdx` / `agent-plan.mdx` / `prompt-lifecycle.mdx`, not to an RFD backfill. Most are
already covered by v2 rows (`ACP-PROMPT-002`, `ACP-PATCH-205/206/207`, `ACP-PERM-201/202`, `ACP-CLIENTCAP-202`,
`ACP-ENUM-201`) or ledger entries. The only RFD-only sentences are lowercase, agent-directed "should"s (signal names,
updating both terminal and tool-call status); none is an RFC 2119 keyword, and none is mechanically decidable, so I
propose no rows. Citing these Draft RFDs is **not** justified: the "Draft RFD only where nothing else states the
rule" condition is never met. A few docs-stated rules are uncovered (diff paths absolute, no commit metadata in
`git_patch`, SHOULD provide `patch`, SHOULD provide `command`). They go to the doc audit, which this report sizes
only so it is not lost.

## Requirements

Legend for "Coverage": row id, ledger citation (base line numbers, as in `v2.toml`), or **UNCOVERED (doc audit)**.
All RFD and doc paths are in the spec repo at `3ea94133`. Tool-calls lines 482-726 have the same numbers at base and
target (the only tool-calls hunks in this range keep their line counts).

### terminal-output.mdx (Draft RFD; unchanged since base)

| # | Agent-side rule (RFD) | Tier if a row | Docs/schema stating it @ target | Coverage |
|---|---|---|---|---|
| T1 | `terminalId` unique in the session, stable, MUST NOT be reused (RFD:31) | MUST | `tool-calls.mdx:495-497` | ledger `tool-calls.mdx:496,497` (unobservable) |
| T2 | `terminal` ToolCallContent is `{type, terminalId}`, display anchor only (RFD:37-46) | MUST (shape) | `tool-calls.mdx:484-493`; schema `$defs/Terminal` | `ACP-PROMPT-002` (schema validation of every `session/update`) |
| T3 | `terminal_update` keyed by required `terminalId`, other fields are patches (RFD:74-79) | MUST (shape) | `tool-calls.mdx:523-526`; `$defs/TerminalUpdate/required` | `ACP-PROMPT-002`, `ACP-PATCH-206` |
| T4 | Agents SHOULD include `command` on the first update when the terminal represents a command (RFD:83) | SHOULD | `tool-calls.mdx:528-529` | **UNCOVERED (doc audit)** |
| T5 | Supplied `cwd` MUST be absolute (RFD:84) | MUST | `tool-calls.mdx:530-531` (schema `AbsolutePath` is a plain string) | `ACP-PATCH-206` |
| T6 | `size` has required `cols`/`rows` (RFD:85) | MUST (shape) | `tool-calls.mdx:532-533`; `$defs/TerminalSize` (required, min 1) | `ACP-PROMPT-002` |
| T7 | `output.data` is RFC 4648 base64, a full replacement snapshot (RFD:86) | MUST | `tool-calls.mdx:536-540`; `$defs/TerminalOutput` | `ACP-PATCH-207` (+ `ACP-PROMPT-002`) |
| T8 | "Agents should use conventional platform signal names" (RFD:87, lowercase) | not RFC 2119 | Docs `tool-calls.mdx:546-548` are descriptive only ("Conventional POSIX signal names include…"). The schema description of `TerminalExitStatus.signal` keeps the lowercase "Agents should use" | none; see Testability |
| T9 | Top-level `_meta` patches by key (RFD:88) | shape | `tool-calls.mdx:549-551`; `extensibility.mdx:111` | schema/`ACP-PROMPT-002`; client-side semantics |
| T10 | "Agents should update both [terminal exit and tool-call status] when both states change" (RFD:90, lowercase) | not RFC 2119 | Docs `tool-calls.mdx:548` keep only "Terminal exit and tool call status are independent" | none; see Testability |
| T11 | `terminal_output_chunk` requires `terminalId`/`data`, each chunk independently base64 (RFD:114) | MUST | `tool-calls.mdx:566-570`; `$defs/TerminalOutputChunk` | `ACP-PATCH-207`, `ACP-PROMPT-002` |
| T12 | `command` permission subject: `command`, `cwd` required, `cwd` MUST be absolute (RFD:137) | MUST | `tool-calls.mdx:302-303`; `$defs/CommandPermissionSubject` | `ACP-PERM-201` (schema), `ACP-PERM-202` (absolute `cwd`) |
| T13 | An allow outcome authorizes the Agent to execute; it never asks the Client to (RFD:139) | descriptive | `tool-calls.mdx:306-307` | not a wire rule; any client-execution request would FAIL `ACP-CLIENTCAP-202` |
| T14 | Cross-version adapters MUST NOT map v1/v2 terminals by shape (RFD:164-169) | binds adapters | — | out of ledger scope (not agent-side) |
| T15 | Opt-in `terminal/cancel` (RFD:13) | — | `tool-calls.mdx:585-606` (Background Work) | `ACP-TERMCANCEL-*`; not this RFD |

The docs add agent rules the RFD lacks: `tool-calls.mdx:578-579` (SHOULD send all output before `exitStatus`;
ledger, Deferred) and `:600` (SHOULD stop advertising `cancel` after `exitStatus`; background-work territory).

### diff-file-states.mdx (Draft RFD; unchanged since base)

| # | Agent-side rule (RFD) | Tier if a row | Docs/schema @ target | Coverage |
|---|---|---|---|---|
| D1 | Diff carries a required `changes` array and an optional `patch` (RFD:50-51) | MUST (shape) | `tool-calls.mdx:612-613,643-650`; `$defs/Diff` | `ACP-PROMPT-002` |
| D2 | `patch` MUST be consistent with `changes` (RFD:73-75) | MUST | `tool-calls.mdx:615-617` ("describes only those paths and operations") | partly: ledger `tool-calls.mdx:622,653-661` (Deferred) covers "each patch path matches a `changes` entry" but does not cite 615-617 |
| D3 | `git_patch` paths absolute, incl. rename/copy lines, no `a/`/`b/` prefix (RFD:79-81) | MUST | `tool-calls.mdx:655-657,660` | ledger `tool-calls.mdx:622,653-661` (Deferred) |
| D4 | Commit metadata and email envelopes MUST NOT be included (RFD:84-85) | MUST | `tool-calls.mdx:661` | **UNCOVERED (doc audit)**; the line is inside the ledger's range, but the ledger statement does not mention it |
| D5 | Agents SHOULD provide `patch` whenever feasible (RFD:85, 146) | SHOULD | `tool-calls.mdx:617-618,648` | **UNCOVERED (doc audit)** |
| D6 | "The patch format should be `git_patch`" (RFD:77, lowercase) | — | Docs `tool-calls.mdx:653,662`: `git_patch` is the only ACP value, custom formats MUST begin with `_` | `ACP-ENUM-201` (`patch.format`) |
| D7 | Operations add/delete/modify/move/copy; move/copy carry `oldPath` + `path` (RFD:107-116) | MUST (shape) | `tool-calls.mdx:684-696`; `$defs/DiffChange`, `DiffPathPairChange.required` | `ACP-PROMPT-002`; `ACP-ENUM-201` (custom ops `_`) |
| D8 | "All paths in protocol payloads are absolute" (RFD:116) | MUST (docs: "absolute path") | `tool-calls.mdx:615,691,695` (schema `AbsolutePath` is a plain string, so validation does not catch it) | **UNCOVERED (doc audit)** |
| D9 | `fileType`/`mimeType` "should describe… when known" (RFD:118,125, lowercase) | optional | `tool-calls.mdx:698-707` | `ACP-ENUM-201` (`fileType` `_`), otherwise MAY |
| D10 | "Text modifications should normally use `patch`" (RFD:203-204, FAQ) | same as D5 | `tool-calls.mdx:617-618` | as D5 |

Docs-only rules the RFD lacks: `tool-calls.mdx:622` (each `path` at most once; ledger, Deferred) and `:622-623` (a
move/copy that also edits is a single entry).

### client-filesystem-terminal-capabilities.mdx (Draft RFD; unchanged since base)

| # | Rule (RFD) | Tier if a row | Docs/schema @ target | Coverage |
|---|---|---|---|---|
| C1 | v2 has no `fs/read_text_file`, `fs/write_text_file`, `terminal/{create,output,release,wait_for_exit,kill}` (RFD:46-54), so v2 Agents do not call them (RFD:82) | MUST (method inventory) | `schema/v2/meta.unstable.json` client-method inventory (only `terminal/cancel`, agent-side, at :25); `prompt-lifecycle.mdx:1169` ("v2 does not define Client file-system or terminal-execution capabilities") | `ACP-CLIENTCAP-202` (undefined agent->client method FAILs) |
| C2 | No `clientCapabilities.fs` / top-level `terminal` (RFD:43-44) | client shape | `$defs/ClientCapabilities` @ target: only `_meta`, `auth`, `elicitation` (+ unstable `session`) | client-side; no agent rule |
| C3 | Agents "no longer have to check these capabilities" (RFD:58) | descriptive | — | none (not a requirement) |
| C4 | Adapter normalisation/rejection rules (RFD:79-81) | binds adapters | — | out of ledger scope |
| C5 | `capabilities.auth.terminal` is kept (RFD:60) | — | authentication docs | auth rows; not this RFD |

### plan-variants.mdx (Draft RFD; `file` dropped since base)

| # | Rule (RFD) | Tier if a row | Docs/schema @ target | Coverage |
|---|---|---|---|---|
| P1 | v2 plans use `plan_update`; v1 `sessionUpdate: "plan"` is gone (RFD:53-54). Since 2026-10-27 it is just an unknown update (RFD:98) | MUST (shape) | `agent-plan.mdx:10,16`; `$defs/SessionUpdate` (no `plan` const, stable and unstable) | `ACP-ENUM-201`: an unprefixed unknown `sessionUpdate` value FAILs |
| P2 | Every plan content variant, including unknown ones, MUST carry `planId` (RFD:57,83) | MUST | `agent-plan.mdx:139` (`:147` at base); `$defs/PlanUpdateContent` (`other` branch requires `planId`) | `ACP-PATCH-205` (+ `ACP-PROMPT-002`) |
| P3 | Only `items` is stable; `markdown`/`plan_removed` stay unstable (RFD:55,59,81) | descriptive | `agent-plan.mdx:12,67-77`; stable `schema.json` has only `items`, unstable adds `markdown`/`plan_removed` | no agent rule (docs: "Agents cannot assume that these plans will be rendered") |
| P4 | Custom plan types begin with `_` (RFD:56,73, via enum-variant-extension) | MUST | `agent-plan.mdx:137` | `ACP-ENUM-201` |
| P5 | No `ClientCapabilities.plan`; `plan_update` needs no capability (RFD:58,61) | descriptive | `agent-plan.mdx:73` | no agent rule |

## Details

### Per-RFD summary

| RFD (stage @ target) | Agent-side rules | Covered by docs + existing rows/ledger | Docs-stated, uncovered (doc audit) | RFD-only testable | RFD-only ledger | Effort |
|---|---|---|---|---|---|---|
| terminal-output (Draft) | 13 (T1-T13; T14-T15 out of scope) | 10 (T1-T3, T5-T7, T9, T11-T13) | 1 (T4) | 0 | 0 (T8, T10 are lowercase; see below) | **S, effectively nil**: 0 rows, 0 fixtures |
| diff-file-states (Draft) | 10 (D1-D10) | 6 (D1, D3, D6, D7, D9, D10 via D5), with D2 partial | 3 (D4, D5, D8), plus D2's citation | 0 | 0 | **nil**: 0 rows, 0 fixtures |
| client-fs-terminal-caps (Draft) | 1 agent rule (C1); C2-C5 not agent-side | 1 (C1 -> `ACP-CLIENTCAP-202`) | 0 (optionally add `prompt-lifecycle.mdx:1169` to `CLIENTCAP-202`'s citation) | 0 | 0 | **nil** |
| plan-variants (Draft) | 2 agent rules (P1, P2) + P4 inherited; P3, P5 descriptive | 3 (P1, P2, P4) | 0 | 0 | 0 | **nil** |

For context only, not this task: the docs-stated gaps (T4, D2 citation, D4, D5, D8) would take the doc audit about
2-3 new rows (one passive diff-shape CAPABILITY row for D8+D4, MANDATORY-capped-to-`capabilities.session` like
`ACP-PATCH-206`; one ADVISORY row or ledger entry each for T4 and D5). Fixtures: 2 negative ones (relative
`changes[].path`; a `git_patch` with a `From <sha>`/`Subject:` envelope), on top of the positive diff already emitted
by `tests/fixtures/agents/v2/_base.py:976-1095` (`_send_rich_turn_updates`). If D3 is promoted from its Deferred
ledger entry at the same time, add one fixture with `a/`/`b/` prefixes.

### Harness and mock-client needs

None for any of these. Every rule is a passive check of agent-emitted `session/update` content during the one-turn
drive `test_patches.py` already uses (`_drive_one_turn`, e.g. `ACP-PATCH-206` at `test_patches.py:183-203`). v2
terminals are agent-owned and display-only, so the mock client needs no terminal or fs capability. There is nothing
for it to implement: v2 defines no client-side terminal/fs methods (C1).

## Testability notes

- **T8 (signal names), lowercase "should":** not proposed. Docs `tool-calls.mdx:546-548` explicitly allow
  "platform-specific names", so no check can tell a bad name from a platform's own. If the user wants visibility, an
  `INFORMATIONAL` record of observed `exitStatus.signal` values is the most it supports. It would cite the schema
  description `$defs/TerminalExitStatus/properties/signal`, not the RFD.
- **T10 (update both statuses), lowercase "should":** not proposed. Whether the tool call's state "changed" is
  internal to the agent. The observable parts (tool calls referencing listed terminals reaching a final status) are
  already judged under the docs by `ACP-PATCH-211`, `ACP-STATE-208/209`.
- **T4 / D5 (doc audit):** "when applicable" / "whenever feasible" is the agent's call. A passive check could flag
  a first `terminal_update` with no `command`, or a `modify` of `fileType: "text"` with no `patch`, but a FAIL could
  be legitimate. That points to ledger entries ("not decidable") or at most `ADVISORY`. The doc audit should decide.
- **D4 / D8 (doc audit):** mechanically decidable from the wire. Absolute paths: `os.path.isabs`-style check, the
  same as `ACP-PATCH-206` (note `AbsolutePath` allows native Windows paths, `tool-calls.mdx:660`). Envelope: the
  `patch.text` must start with `diff --git` and contain only diff sections. Both are vacuous (SKIP) against agents
  that emit no diff in a short turn, which is why the existing ledger entry is "Deferred".

## Discrepancies

None that change a tier. The docs win in every case:

- terminal-output RFD:87 and RFD:90 address Agents with a lowercase "should" (signal names; update both statuses).
  The docs (`tool-calls.mdx:546-548`) turn the first into a neutral description and drop the second. The schema
  description of `TerminalExitStatus.signal` keeps "Agents should use the conventional platform signal name".
- The docs are stricter or more detailed than diff-file-states: `tool-calls.mdx:622-623` (unique `path` per entry,
  single entry for move+edit), `:660` (native absolute path after unquoting), `:662,686,701` (custom values `_`).
  These are additions, not conflicts.
- plan-variants at base still listed `file` among the unstable operations. Both the target RFD and the target
  `agent-plan.mdx` drop it, so they agree at the target.

## Open questions

Adjacent items for the doc-audit researchers of `tool-calls.mdx` / `agent-plan.mdx` (not decided here):

1. Ledger `agent-plan.mdx:119` ("Plan file URIs MUST be absolute", Deferred because of the `file` variant) is
   obsolete at the target, since `file` was removed (`agent-plan.mdx` diff). Its successor rule is
   `agent-plan.mdx:109` ("`path` MUST be an absolute path" on unstable `markdown` plans). It is a new passive-check
   candidate, gated like `ACP-PATCH-205`.
2. `ACP-PATCH-205` cites `agent-plan.mdx:147` (base); at the target the rule is at `:139`. Ledger `agent-plan.mdx:139`
   and `:186` also move (to `:131` and `:178`).
3. The ledger statement for `tool-calls.mdx:622,653-661` does not cite `:615-617` (D2) or mention `:661` (D4). Either
   widen it or promote it to a row, as above.
4. Uncovered SHOULDs T4 (`tool-calls.mdx:528-529`) and D5 (`:617-618`): ledger or `ADVISORY`.
5. Optionally add `prompt-lifecycle.mdx:1169` to `ACP-CLIENTCAP-202`'s citation as the prose statement that v2 has no
   client fs/terminal methods. `docs/protocol/v2/migration.mdx:57-58,817-822` says it more explicitly, but it is
   outside the citable `draft/` tree.
