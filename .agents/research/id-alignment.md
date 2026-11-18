# Id alignment for the spec update (ee2af8a..b4066fe): which new or changed ids need a rename?

**Sources checked:** acp-tck @ b4066fe (branch `eugenethedev/spec-update`), registries diffed against ee2af8a;
agent-client-protocol @ 3ea94133bb4e7cfdb1105df75660ff83e66acf62 (the registries' `SPEC_REVISION`, read with
`git show` from `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol`; see "Open questions" Q1 about
the skill's broken `.repo`).
**Confidence:** high. Every new or changed row was compared by text and citation in both registries (AST-parsed,
not grepped). The few judgment calls are the borderline pairs below, and they are flagged as the user's call.

## Answer

No renames are needed. All 24 ids added to both registries mean the same rule in both (same normative statement
at different lines of the v1 and v2 docs). None of the 3 v1-only additions (`CLIENTCAP-009`, `PLAN-004`,
`SUBAGENT-020`) is used by v2. All 36 v2-only additions are numbered `2xx` and have no v1 row to share an id
with. No new v2 row uses a `0xx` number that v1 lacks, v1 has no `2xx` ids, and no id means one rule in v1 and
another in v2. The ids that existed before and changed text (the `SUBAGENT-0xx` family in both versions, plus
`AUTH-004`, `CONFIG-001`, `ERROR-006`, `RESUME-002` in v2, and v1-only `CLIENTCAP-007`, `CONFIG-003`) still mean
the same rule as before. The deleted v1 `PLAN-001` is not reused anywhere, and the update does not reuse it.

The four borderline cases (`SUBAGENT-020`, `CLIENTCAP-009`, `PLAN-004`, and `RESUME-226` plus `SUBAGENT-204`,
which this review found) all come out as "keep". One cross-reference in row text is wrong (it is not a rename):
v2 `ACP-PLAN-003` says a wrongly typed `path` is `ACP-SCHEMA-001`'s, but v2 `SCHEMA-001` only covers `initialize`.
It is listed under T1 for separate approval.

## Summary table

| current id | version | proposed id | reason | files affected |
|---|---|---|---|---|
| none | | | No rename is needed (see "Confirmed aligned" and "No counterpart") | 0 |

Optional text fix (not a rename; approve on its own):

| # | id | version | change | files affected |
|---|---|---|---|---|
| T1 | ACP-PLAN-003 | v2 | in the row text and test docstring, change "a schema defect (`ACP-SCHEMA-001`'s)" to `ACP-PROMPT-002`'s | 2 |

## Per-rename details

There are no renames.

### T1 (optional text fix, not a rename): v2 `ACP-PLAN-003` points to the wrong row for schema defects

- The v2 row text (`src/tck/v2/requirements.py:4222`) and the test docstring
  (`src/tck/v2/conformance/test_patches.py:190`) say a non-string `path` is "a schema defect (`ACP-SCHEMA-001`'s)".
- v2 `ACP-SCHEMA-001` (`src/tck/v2/requirements.py:295`) only validates "messages the agent emits during the
  `initialize` exchange". The PLAN-003 test reads updates from `_drive_one_turn`
  (`test_patches.py:193`), and v2 `ACP-PROMPT-002` (`src/tck/v2/requirements.py:332`) validates every
  `session/update` of a prompt turn against the v2 schema. v1 `ACP-SUBAGENT-015` (`src/tck/v1/requirements.py:1768`)
  already uses `ACP-PROMPT-002` as the v2 schema row for the same purpose.
- Proposed: replace `ACP-SCHEMA-001` with `ACP-PROMPT-002` at those two places. No id, test marker, expectation,
  map or cross-check line changes.

## Confirmed aligned (shared ids, same rule in v1 and v2)

Each row below exists in both registries. "Same rule because" names the normative statement both versions make.
Differences in gate, tier or test strategy are allowed by rule B (`docs/requirements.md:15-22`).

| id | v1 (line) | v2 (line) | same rule because | allowed differences |
|---|---|---|---|---|
| CLIENTCAP-008 | 1393 | 1526 | Both docs say MUST NOT send `prompt_suggestions_update` unless `…session.promptSuggestions` was advertised (v1 `prompt-turn.mdx:35,364`; v2 `prompt-lifecycle.mdx:42,707`) | v1 MANDATORY, v2 CAPABILITY `capabilities.session`; v2 adds `session: {}` / `null` connections |
| PLAN-003 | 1931 | 4213 | Both say a markdown plan's string `path` is an absolute native path, not a URI (v1 `agent-plan.mdx:112-117`; v2 `agent-plan.mdx:104-109`) | v1 MANDATORY gated on `clientCapabilities.plan`, v2 CAPABILITY; see T1 |
| SUGGEST-001 | 1967 | 1570 | Same: a suggestion's `prompt` is valid as a `session/prompt` prompt, holding only text and resource links unless more was advertised (v1 `prompt-turn.mdx:398-405`; v2 `prompt-lifecycle.mdx:743-748`) | v1 drives `session/load`, v2 `session/resume` |
| SUGGEST-002 | 1988 | 1591 | No suggestion is empty or whitespace-only (v1 `prompt-turn.mdx:402`; v2 `prompt-lifecycle.mdx:745`) | tier/gate |
| SUGGEST-003 | 2002 | 1605 | Identical MUST: on an accepted `session/prompt`, replace or withdraw a non-empty list (v1 `prompt-turn.mdx:409`; v2 `prompt-lifecycle.mdx:755`) | v1 gate `inferred:promptSuggestions`, v2 `capabilities.session`; window wording |
| SUGGEST-004 | 2018 | 1622 | Identical SHOULD NOT: no suggestions in session replay (v1 `prompt-turn.mdx:425`; v2 `prompt-lifecycle.mdx:768`) | judged on load replay in v1, resume replay in v2 |
| CURSOR-001 | 2035 | 1640 | Same rule: a cursor's first update carries an anchor and the cursor never moves (v1 `prompt-turn.mdx:617-624`; v2 `prompt-lifecycle.mdx:947-954`) | load vs full-replay resume |
| CURSOR-002 | 2059 | 1664 | An anchor names an entity already reported (v1 `prompt-turn.mdx:652-657`; v2 `prompt-lifecycle.mdx:966-975`) | same |
| CURSOR-003 | 2080 | 1684 | Fork with a `cursorId` the agent did not issue is rejected with `-32602` (v1 `prompt-turn.mdx:698-701`; v2 `prompt-lifecycle.mdx:1017-1020`) | gate path |
| CURSOR-004 | 2098 | 1702 | SHOULD use the same `cursorId` for the same position in every load or replay (v1 `session-setup.mdx:155`; v2 `session-setup.mdx:340`, word for word apart from load/replay) | v1 matches cursors by position ordinal, v2 by identical anchor (test strategy only) |
| LIST-004 | 487 | 2787 | `session/list` never returns an announced child (v1 `subagents.mdx:430`; v2 `session-list.mdx:6`, `subagents.mdx:381`). Both rows already say "Shared id" | gate |
| OPTIONS-001 | 855 | 3647 | `session/options` with an absolute `cwd` succeeds and validates (v1 SCO `475,479-535`; v2 SCO `482,486-549`) | v2 hands result lists to other rows |
| OPTIONS-002 | 873 | 3667 | `session/options` MUST NOT create a session, send updates, or add to the list (v1 SCO `537`; v2 SCO `551`) | v2's docs add "or resume", and the v2 test adds a probe for it. This is a stricter v2 check of the same rule, so the id stays |
| OPTIONS-003 | 890 | 3691 | `session/options` with an unknown `sessionId` fails (v1 SCO `507`; v2 SCO `514`) | v2 also asserts `-32002` (v2 `error.mdx:54` makes it a MUST). A stricter assertion keeps the shared id (`docs/requirements.md:20-21`) |
| OPTIONS-004 | 929 | 3730 | A schema-invalid initial entry gets `-32602` (v1 SCO `563`; v2 SCO `578`, same sentence) | v2 adds a missing-`type` probe because v2 entries require `type` |
| OPTIONS-005 | 950 | 3753 | A duplicate `configId` gets `-32602` (v1 SCO `564`; v2 SCO `580`) | choice of probe option |
| OPTIONS-006 | 969 | 3773 | An entry that cannot be applied is ignored (v1 SCO `565`; v2 SCO `581`, same sentence) | v1 needs `configOptions.boolean` for the type probes |
| OPTIONS-007 | 993 | 3794 | SHOULD NOT send `config_option_update` for initial entries (v1 SCO `567`; v2 SCO `583` adds "on the requesting connection") | wording |
| OPTIONS-008 | 1011 | 3812 | SHOULD NOT send other entry-caused updates before the new/fork response (v1 SCO `568`; v2 SCO `584`). v1's example list also names `current_mode_update` | none of substance; confirms 426f87b |
| OPTIONS-009 | 908 | 3709 | `session/options` with a `sessionId` SHOULD NOT connect to MCP servers (v1 SCO `509`; v2 SCO `516`) | v1 uses a fresh connection, v2 the same one after close |
| OPTIONS-010 | 1032 | 3833 | INFORMATIONAL record of whether a valid initial value shows in the response | gate text |
| OPTIONS-011 | 1046 | 3846 | Setup response `configOptions` MUST contain the actual values (v1 SCO `566`; v2 SCO `582`) | v1 needs the boolean client cap for a second option |
| SUBAGENT-018 | 1845 | 740 | SHOULD reject a non-permitted request naming a child with `-32602` (v1 `subagents.mdx:428`, `error.mdx:57`; v2 `subagents.mdx:376,379-380`, `error.mdx:58`). Both rows already say "Shared id" | v2 also allows `tool_call/cancel` and `terminal/cancel`; v2 probes resume instead of load |
| SUBAGENT-019 | 1873 | 770 | close and delete "do not report success for a child" (v1 `subagents.mdx:428`; v2 `subagents.mdx:376,380`) | gate: v1 `…sessionCapabilities.close`, v2 `capabilities.session` (close is baseline) |

The pre-existing shared ids whose text changed were also compared, and they still match:

- `SUBAGENT-001` to `-009`, `-011` to `-014`, `-016`, `-017` (both registries). The edits are provenance changes
  ("draft docs state it"), test-scope notes, and per-version wire details (v2 has whole-message updates as well as
  chunks; v2 reports a child's state in `state_update`). In each pair the core sentence is identical.
- `SUBAGENT-001` is worth a note. v1 now also judges the rule that the announcement applies again on every load
  (`v1 subagents.mdx:517`), while v2 judges that part under `RESUME-209` and `RESUME-225`. Rule B's split clause
  covers this (`docs/requirements.md:21-22`). The shared core rule is "the announcing `subagent_update` precedes
  child traffic", so the shared id stands.
- v2 `AUTH-004`, `CONFIG-001`, `ERROR-006` and `RESUME-002` changed only in scope or SKIP details (logout error
  handling, `session/options` added to the probe or check set, a provenance note). The rule is unchanged, so v1's
  same-id rows still match.
- v1 `CLIENTCAP-007` and `CONFIG-003` changed. They have no v2 row with the same id, which was already so on main.

## No counterpart (version-only rows added in this update)

### v1-only (0xx numbers; v2 does not use the id)

| id | v1 line | why v2 has no same-id row |
|---|---|---|
| CLIENTCAP-009 | 1410 | The rule does not exist in v2. v1 `prompt-turn.mdx:584-589` says MUST NOT send `cursor_update` without `clientCapabilities.session.cursors`. v2 `prompt-lifecycle.mdx:916` says "No Client capability is required in v2". No collision: v2 has no `CLIENTCAP-009` (v2 has CLIENTCAP 003, 008, 202, 203). |
| PLAN-004 | 1951 | In v1 a legacy `file` plan is schema-invalid against a closed union, and this row is the v1 schema check on the plan connection. v2 has no single row for it: `plan_update` shapes are validated by v2 `PROMPT-002` (all updates of a turn), and `plan.type` is an open-enum site judged by v2 `ENUM-201` (`src/tck/v2/requirements.py:4836`). v1 `SUBAGENT-015` (`src/tck/v1/requirements.py:1768`) set the precedent for a v1-only schema row. v2 has no PLAN-004. Keep. |
| SUBAGENT-020 | 1892 | Borderline; recommend keep. v1's source is a subagents-specific reservation with no RFC keyword (v1 `subagents.mdx:380`: "A value that begins with `_` is implementation-specific, and other values are reserved for the protocol"), hence ADVISORY. v1 `extensibility.mdx` has no general enum MUST NOT. v2 judges the same values under two broader `2xx` rows. `ENUM-201` comes from v2's general MUST NOT (`v2 extensibility.mdx:238-243`) and covers many sites, including `state_update.state`. `STATE-203` covers the turn-ending idle's `stopReason` on the prompted session. Neither row restates SUBAGENT-020, and SUBAGENT-020 is not a split of either, so no rename fits: giving `SUBAGENT-020` to v2 would leave a v2 row stating part of `ENUM-201`'s rule, and moving `ENUM-201` to v1 would bring in sites and a MUST that v1 docs lack. No collision (v2 has no SUBAGENT-020). Optional: the v1 row's "v1 only" note could also name `ENUM-201`/`STATE-203` as the v2 analogues. |

### v2-only (2xx numbers; checked for v1 rules that would require a shared id)

| id | why v1 has no same rule |
|---|---|
| ADDDIRS-204 | "Agents that don't advertise the capability ignore the field" is in v2 `session-setup.mdx:528`. v1 `session-setup.mdx:363-392` has no such sentence. |
| AUTH-211 | "Logging out is idempotent ... SHOULD respond with the same empty result" is in v2 `authentication.mdx:273` only. v1 `authentication.mdx:218-232` lacks it. |
| CLIENTCAP-203, COMMANDS-202, PROMPTCAP-202, PROMPT-220 | Skills. v1 docs and schema at 3ea94133 have no skill command, capability or content block (the only "skill" mentions are prose, at v1 `session-setup.mdx:426,485`). |
| LIST-208 | v2 `session-list.mdx:162-165` has the SHOULD to send `session_info_update` on every metadata change, client-requested ones included. v1 `session-list.mdx:177-179` only says agents "can" send it, and v1 `set_title` comes only from the Draft RFD. |
| OPTIONS-201 | The unsupported-value-`type` MUST (v2 SCO `579`) and its conflict with `:581` exist only in v2. v1 SCO `563-568` has no such bullet. |
| PATCH-213..215 | `diff` `changes[]` and `git_patch` are v2 shapes. `git_patch` does not appear in v1 docs or schema. |
| PATCH-216 | `terminal_output_chunk`/`terminal_update` are v2 shapes. `terminal_output_chunk` does not appear in v1. |
| PROMPT-212..219 | `idempotencyKey` does not appear in v1 docs or schema. |
| RESUME-218..224 | `replay_complete` (and the `background` list behind 224) is v2-only. `replay_complete` does not appear in v1. |
| RESUME-225 | v1 states the same sentence ("The announcement rule applies again on every load or resume", v1 `subagents.mdx:517`), but v1 judges it inside `SUBAGENT-001`. v2 splits it into `SUBAGENT-001` (live), `RESUME-209` (replay) and `RESUME-225` (resume without replay). Rule B's split clause gives the parts `2xx` ids (`docs/requirements.md:21-22`). Keep. |
| RESUME-226 | Borderline; recommend keep. v1 has the same MUST: "Replayed child updates MUST keep their original `sessionId`, their known parent, and their order within each session" (v1 `subagents.mdx:531`; v2 `subagents.mdx:480`). v1 has no registry row for it, only a ledger entry calling it not observable (`spec-tracker/maps/v1.toml`, from plan 5.3: "`SA:531,535` ... not observable"). With no v1 row there is no id to share, so a 2xx number is permitted. If v1 later adds a row for this rule, the pair would need a shared non-`2xx` id. See Q3. |
| SUBAGENT-203 | The MUST to `$/cancel_request` descendants' requests before the close response is in v2 `subagents.mdx:427`. In v1, `subagents.mdx:477` leaves those requests to the Client and `:469` makes `$/cancel_request` optional. |
| SUBAGENT-204 | Mostly v2-only (v2 `subagents.mdx:417` MUST cancel with `$/cancel_request`; v1 `:469` "stays optional"). The second half, "does not wait for a child's pending requests to resolve before it reports the child's state", is word for word in v1 `subagents.mdx:471` and v2 `:421`. v1 has no row for that half, so there is nothing to share. Keep. See Q2. |
| SUBAGENT-205 | "Both copies of a transition" (v2 `subagents.mdx:351`) requires a child's own `state_update` stream. v1 reports child state only on `subagent_update.state`. |
| TOOLCANCEL-210/211, TERMCANCEL-210/211 | `tool_call/cancel` and `terminal/cancel` are v2 methods (no v1 TOOLCANCEL/TERMCANCEL families). |

The pre-existing v2 `2xx` rows whose text changed (`SUBAGENT-201`, `SUBAGENT-202`, `CANCEL-209`, `CANCEL-213`,
`COMMANDS-201`, `CONFIG-210`, `ENUM-201`, `META-203`, `PATCH-211`, `PROMPTCAP-201`, `RESUME-205`, `RESUME-209`) were
word-diffed against ee2af8a. The changes are provenance, scope and site-list edits. None makes a row restate a v1
row. (`SUBAGENT-202` is like `RESUME-226`: v1 docs state the cascade at v1 `subagents.mdx:454`, but v1 only has a
ledger entry for it, at `spec-tracker/maps/v1.toml:537-539`.)

## Deletions and freed ids

- v1 `ACP-PLAN-001` (an absolute `uri` on a `file` plan; removed from `src/tck/v1/requirements.py` at ee2af8a line 1517)
  is deleted. No reference remains outside `.agents/`. An `rg` over `src tests spec-tracker cross-check .github docs
  README.md` finds none, and v2 never had a PLAN-001.
- Reuse: forbidden in this change (guard 1, `docs/requirements.md:32-33`). A later change may reuse it for a new PLAN
  rule, as long as v2 does not use PLAN-001 for a different rule at that time (guard 2, `:34-35`). The new
  markdown-path rule correctly took `PLAN-003` instead of reusing 001.

## Requirements (id rules applied)

| # | Requirement | Tier | Citation |
|---|---|---|---|
| 1 | An id in both registries means the same protocol rule; tier and gate may differ per version | repo contract | `docs/requirements.md:15-17` |
| 2 | A `2xx` number is a v2 rule with no v1 counterpart; a v1 rule that v2 splits into parts gives the parts `2xx` ids | repo contract | `docs/requirements.md:18,20-22` |
| 3 | A stricter or narrower v2 assertion keeps the shared id | repo contract | `docs/requirements.md:20-21` |
| 4 | A freed number is not reused in the change that freed it, nor in a way that breaks rule B | repo contract | `docs/requirements.md:31-35` |
| 5 | Unaffected rows are never renumbered to close gaps | repo contract | `docs/requirements.md:37-38`; `docs/spec-updates.md:115` |

## Testability notes

These checks are mechanical and could become a meta-test or a spec-tracker check (design idea, not done here):

- (a) no `2xx` id in v1;
- (b) every v2 `0xx` id also exists in v1, which holds today (empty set);
- (c) a row whose text says "Shared id" exists in the other registry, and one that says "v1-only"/"v2-only" does
  not. The only hits today are false positives in prose about SDKs and schemas, in v1 `INIT-003` and v2
  `INIT-004`/`SCHEMA-001`.

Whether two same-id rows state the same rule cannot be checked mechanically. It needs the side-by-side reading done
here.

## Discrepancies

None between the registries' ids. One stale cross-reference in row text (T1).

## Open questions

- **Q1 (tooling).** `.claude/skills/check-specification/.repo` holds a truncated path,
  `/Users/eugene/Documents/JetBrains/projects/agent-client-protoco ` (missing `l`, trailing space). The skill's
  `git pull --ff-only` therefore failed. I did not fix `.repo` and did not pull. I read the pinned revision
  3ea94133 read-only from `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol` (origin
  `EugeneTheDev/agent-client-protocol`), which is the revision every citation is relative to. The user should
  correct `.repo`.
- **Q2 (v1 coverage, not ids).** The sentence "The Agent does not wait for a child's pending requests to resolve
  before it reports the child's state" (v1 `subagents.mdx:471`) has no v1 row and no v1 ledger entry; no text
  match was found in `spec-tracker/maps/v1.toml`. v2 tests it inside `SUBAGENT-204`. If this is a gap, the
  spec-tracker or the v1 subagent owner should handle it.
- **Q3 (cross-version consistency, not ids).** v1 ledgers as "not observable" two rules that v2 now tests:
  replayed child order and parent (v1 `SA:531` vs v2 `RESUME-226`) and the cancel cascade (v1 `SA:454` vs v2
  `SUBAGENT-202`). If v1 ever adds rows for them, rule B would call for a shared non-`2xx` id and the v2 rows would
  then need renaming. That decision is out of scope here.
- **Q4 (hypothesis, v2 coverage).** A child's idle `stopReason` reported in its own `state_update` may not be judged
  by any v2 row. `STATE-203` judges only "the idle that ends the turn", and `ENUM-201`'s site list does not name
  `stopReason`. Not verified against the test code.
