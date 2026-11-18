# State: update the TCK to the spec: both main full
## Settings
mode: single · branch: eugenethedev/spec-update (from main ee2af8a) · reviews: on
## Spec update scope
- versions: v1 and v2
- base: 3961af94fa62d2386d993cadf1afc8b146fc799a (pinned in both VENDORED.md)
- target: 3ea94133bb4e7cfdb1105df75660ff83e66acf62 (upstream/main, 2026-11-17)
- depth: full audit (requested `full`; also neither map has `rfd_audit`, so every tracked RFD is audited in full)
- spec checkout (the `.repo` one, used for `--spec-repo`): /Users/eugene/Documents/JetBrains/projects/agent-client-protocol
  (on the user's feature branch; never touch its working tree, read target files with `git show 3ea94133:<path>`)
- target-revision working tree: /Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2 (main, at 3ea94133)
## Decisions (final)
- Target stays 3ea94133 even though ../agent-client-protocol-2 moved to a later commit: re-vendor with `git show 3ea94133:<path>`, never `cp` from the working tree.
- Depth: full audit (user asked `full`; v2 schema alpha.14 -> alpha.16; no `rfd_audit` in either map).
- Upstream removed the RFD Active stage at target: tracked RFDs are only `subagents` (Preview) and `plan-operations` (Preview), both versions.
- Impact research grouped by area (one researcher per doc group, one per tracked RFD); common brief `.agents/research/impact-brief.md`.
- Plan: `.agents/research/plan-consolidated.md`. User accepted ALL recommended options for D1-D13 (2026-11-18):
  D1(a) delete PLAN-001, add PLAN-003 + PLAN-004; D2(a); D3(a); D4(a); D5 literal; D6 INFORMATIONAL; D7 as recommended;
  D8 all; D9 all; D10(a) now, (b) follow-up; D11 backfill slice INCLUDED (slice 27), row candidates follow-up;
  D12(a) mcp-over-acp deferred to a follow-up PR, transport RFD out of scope, no ledger entries for either; D13 all defaults.
- Plan errata (from review-revendor.md): v2 ledger reword uses `SS:56` not `SS:54`; impact-v2-prompt-lifecycle.md has an off-by-one near PL:403-405 (CANCEL-214 -> :404, JSONRPC-007 -> 404-405). Programmers must verify every line number against 3ea94133 themselves.
- VENDORED.md keeps `git show <commit>:<path>` (fix slice drops the pointless HEAD step, aligns docs/spec-updates.md).
- AUTH-211: relax the common plugin to allow several `revokes` tests, run last in collection order (user, 2026-11-18).
- Pre-existing ACP-DELETE-204 fixture bug: fix in this PR as a small fixture-only slice + a test running DELETE-204 without the hang prompt (user).
- No "ignored RFDs" list exists in the maps; nothing to remove there (user asked; confirmed by grep).
## Done
- Step 2 inventory — ceef9a8 — .agents/research/spec-diff-v{1,2}.md
- R-V1 — 5495e0f — v1 vendored at 3ea94133, citations remapped, subagents -> Preview RFD, JSONRPC-003 off mcp-over-acp; PLAN-001 temporarily -> PlanUpdateContent; suite green (1031)
- R-V2 — 7254513 — v2 vendored at 3ea94133 (alpha.16), citations remapped (61 needs-review by hand, 187 code/test refs), Draft-RFD citations dropped, enum sets follow schema (ENUM-201 effect noted in commit), spec-tracker PL map test leaves prompt-suggestions/cursors sections out of core; suite green (1031)
- V1-PLAN — 1c04f52 — -PLAN-001 (+helper, fixture); +PLAN-003 (abs markdown path), +PLAN-004 (plan update shape), MANDATORY vacuous; suite green (1026)
- V2-PLAN — c7436a6 — +PLAN-003 v2 (CAPABILITY capabilities.session), ledger -agent-plan.mdx:119, base sends abs markdown plan; suite green (1027)
- Review milestone 1 — review-revendor.md — 0 blocker, 4 should-fix, 5 nit; all go to slice R-FIX
- R-FIX — 25c0272 — all 9 review findings fixed (29 RFD-SA pointers +44, CANCEL-214/JSONRPC-007 lines, ledger pointers, SUBAGENT-011 v1 aligned to v2, VENDORED.md step 1, spec-updates.md git show); suite green (1027)
- V1-GATES+SUGGEST — f421609 — +CLIENTCAP-008/-009, +SUGGEST-001..004 (003 CAPABILITY inferred:promptSuggestions, 004 ADVISORY), ledger +2 (PT:411,413), 6 fixtures + _suggests mixin; suite green (1029). DOCS slice must add inferred:promptSuggestions.
- V2-GATES — 25e3c20 — +CLIENTCAP-008 v2, +CLIENTCAP-203 (CAPABILITY capabilities.session), 2 fixtures
- V2-SUGGEST — 1f3a143 — +SUGGEST-001..003 (CAPABILITY), -004 ADVISORY (replay_complete..resume response window); ledger +2 (PL:754,756); suite green (1032)
- V1-CURSOR — 8b535fa — +CURSOR-001/-002 MANDATORY vacuous, -003 CAPABILITY fork (literal D5), -004 ADVISORY; ledger +2; suite green (1034)
- V2-CURSOR — a239149 — +CURSOR-001..004 (CAPABILITY cap.session / cap.session.fork / ADVISORY), ENUM-201 cursor anchor sites, ledger +4 (one Deferred: positive fork-at-cursor); _base.py rejects unissued cursorId by default; suite green (1040). CURSOR-001 also requires an anchor on the first replayed update after load (SS:156 'like a first update'); accepted.
- V1-OPT1 — a2a47c4 — +OPTIONS-001/-002/-003 CAPABILITY options, -009 ADVISORY, CONFIG-003 scans session/options (U1 noted); suite green (1042)
- V1-OPT2 — 586c37e — +OPTIONS-004/-005/-006/-011 CAPABILITY, -007/-008 ADVISORY, -010 INFORMATIONAL; ledger +5; suite green (1044). For review: OPTIONS-008 also flags config_option_update (overlaps -007; plan says 'other' updates); fork initial entries not probed.
- V2-OPT1 — 93b3b14 — +OPTIONS-001/-002/-003 (-32002, U5) CAPABILITY, -009 ADVISORY; ERROR-006 probes session/options; CONFIG-001/-210, COMMANDS-201, CLIENTCAP-203 scan session/options; suite green (1047)
- V2-OPT2 — 252d13a — +OPTIONS-004/-005/-006/-011 CAPABILITY, -007 ADVISORY, -010/-201 INFORMATIONAL (U6/U7); ledger +8; suite green (1049)
- typo fix — a00eef1 — v1 stdio MCP test names restored
- V2-SKILL — c270315 — COMMANDS-201 accepts skill (+ unique across commands/skills, U12 recorded on the custom-type branch), PROMPTCAP-201 probes skill, +COMMANDS-202 (inferred:skills), +PROMPTCAP-202, +PROMPT-220 ADVISORY; ledger +4; inferred:skills added to docs/requirements.md; suite green (1074)
- V2-IDEM — 5aa7c71 — +PROMPT-212..215/-217..219 CAPABILITY cap.session, -216 ADVISORY; ledger +3 and +1 Deferred ($/cancel_request variant, PL:405,458); fixture base records keys + persists history; 7 fixtures; suite green (1083, run by orchestrator)
- V2-REPLAY — 0ec3a61 — +RESUME-218..221 CAPABILITY, -222 ADVISORY; RESUME-205 all 7 chunk kinds; ledger +3, -SS:235 notices entry; _base.py sends replay_complete; SUGGEST-004 now PASSes on conforming_full; suite green (1093)
- V2-CAN — a8c38d8 — CANCEL-213 ADVISORY->CAPABILITY (quiet_period window in text), CANCEL-209 note; elicitation MUST restated as Deferred ledger entry (U10), section header/reasons reworded off TCK-choice; suite green (1093)
- V2-TOOL — 145356c — +PATCH-213/-214/-215 CAPABILITY, -216 ADVISORY, +TOOLCANCEL/TERMCANCEL-210 CAPABILITY (inferred gates), -211 ADVISORY; ENUM-201 subject.type; ledger -2 +3; TOOL/TERMCANCEL-203 cite subagents.mdx:374 primary; suite green (1111)
- V2-AUTH+DIRS — b07c1f7 — common plugin allows several `revokes` tests (docs/writing-tests.md); +AUTH-211 ADVISORY (revokes, SKIPs if re-login fails), AUTH-004 standalone path (-32601 only), +ADDDIRS-204 ADVISORY; ledger -SS:528 +AuthAccount.description; suite green (1116)
- DEL204-FIX — 98673e1 — AsksPermissionAgent now withdraws the pending permission before answering session/delete (close already did); new CLI test runs close/delete cancel rows without __hang__; plain v2 run on conforming_full is CONFORMANT; suite green (1117)
- V1-SA1 — 9137de7 — v1 subagent rows + CLIENTCAP-001..003/-007 cite subagents.mdx first (U13a in SUBAGENT-002); ledger +17, -1 cost, rewrites/re-points; suite green (1117)
- V1-SA2 — 2800a5a — SUBAGENT-001 post-load scope (only after a successful load), -012 sender-less message counts, -016 unknown-after-cancel SKIPs; 4 fixtures; suite green (1126)
- V1-SA3 — fd23cab — +SUBAGENT-018 ADVISORY (post-judging probes load/close/delete, U4), +SUBAGENT-019 CAPABILITY close(+delete), +LIST-004 CAPABILITY list, +SUBAGENT-020 ADVISORY; new exposes_subagent_full.py; suite green (1146)
- V2-SA1 — 8cb3a0e — v2 subagent rows + RESUME-002/-209 docs-first; ledger +13 (incl. 2 Deferred), -1 cost, 13 rewrites; suite green (1146)
- V2-SA2 — 08a671d — SUBAGENT-012 sender-less counts, -016 needs child's own idle, unknown-after-cancel SKIPs; 4 fixtures; suite green (1152)
## Next
Order (plan section 5): area slices 23-28 -> milestone-2 review -> fix slice(s) -> id alignment -> cross-check refresh -> final review.
- Milestone 1 (re-vendor) DONE and reviewed. Milestone 2 (area slices) in progress: slices 1-22 done (plus R-FIX, typo fix, DEL204-FIX).
- Slice 23 V2-SA3: STOPPED GRACEFULLY, NOT COMMITTED (user request, before an orchestrator restart). The working tree holds the
  complete implementation, uncommitted: SUBAGENT-018/-019/-205, LIST-004, SUBAGENT-004 extension. Handoff with details and
  decisions: `.agents/research/v2-sa3-handoff.md`. Modified: src/tck/v2/requirements.py, src/tck/v2/conformance/_helpers.py,
  src/tck/v2/conformance/test_subagents.py, tests/fixtures/agents/v2/exposes_subagent.py, tests/v2/test_cli.py,
  tests/v2/test_helpers.py, tests/v2/test_registry.py. New fixtures in tests/fixtures/agents/v2/: exposes_subagent_full.py,
  child_close_wrong_code.py, child_close_succeeds.py, child_delete_succeeds.py, lists_child_session.py,
  child_id_reused_for_new_session.py, late_child_state_mirror.py. Last results: test_helpers, test_registry and spec-tracker
  green; subagent part of test_cli had 1 failure that was fixed but not re-run; the full suite was NEVER run.
  FIRST ACTION on resume: spawn a programmer (single mode, tip a1dd1c8 plus this tree) to read the handoff, run the FULL suite in the
  foreground, fix what fails, and commit by explicit paths as `feat(v2): child-session probes, list and state-ordering rows`.
- Slice 24 V2-SA4 (plan 5.2 row 24; 1.2 ~lines 199-201, 206-207): +RESUME-223/-224/-225, +SUBAGENT-203 (CAPABILITY cap.session,
  pending child requests get $/cancel_request before the session/close response), +SUBAGENT-204 (CAPABILITY inferred:subagentCancel;
  harness change in _child_cancel.py, run_prompt hold mode). Needs replay_complete (0ec3a61) and CANCEL-213 (a8c38d8), both done.
- Slices 25/26 LEDGER-HYGIENE v1/v2: D10 rewords (plan 1.1 removed/rewritten table: error.mdx:37 / :38, transports.mdx:10,45, TC:250,
  get-auth-state.mdx:297/:313, session-list.mdx:258 Deferred, session/status + session/set_title reasons; v2 SCO:375 fan-out ->
  cite SS:56 NOT SS:54); +v1 AuthAccount.description entry if missing (v2 has it from b07c1f7). v2 extras: add an entry for
  `SA:263` (outgoing view + link SHOULD; v1 twin SA:285); extend the `TC:753,754` entry to cover TC:755-756 or say SUBAGENT-002 covers it.
- Slice 27 BACKFILL (D11, included): v1 elicitation 9 entries + agent-plan.mdx:53; v2 meta-patch 5 entries + security.mdx:59.
- Slice 28 DOCS + rfd_audit: remove "Active > v2" stage wording from docs/requirements.md and docs/spec-updates.md (no Active stage
  upstream; also check spec-tracker/src/spec_tracker/impact.py:915 wording); add `inferred:promptSuggestions` to the inferred list
  (`inferred:skills` already added); decide whether PL "Prompt suggestions (unstable)"/"Session cursors (unstable)" become core_doc
  sections (currently left out in spec-tracker/tests/test_maps_v2.py); core_doc `code` lists gain the new modules
  (test_prompt_suggestions, test_cursors, test_session_options/test_initial_config, test_idempotency); set
  `rfd_audit = "3ea94133bb4e7cfdb1105df75660ff83e66acf62"` at the top of both maps.
- Then milestone-2 review: one reviewer over the area-slice range 3039958..HEAD (product commits from 1c04f52 on), decisions D1-D13,
  plan sections 1-5. Show findings to the user; fixes become slices. Known items to hand the reviewer: v1 OPTIONS-008 also flags
  config_option_update (overlaps -007; plan meant "other" updates); session/fork initial config entries not probed (both versions);
  CURSOR-001 requires an anchor on the first replayed update (accepted); cursor fixtures exercise only message anchors.
- Then id alignment (plan 5.3): researcher inventory -> user approves EACH rename -> programmer applies everywhere.
- Then cross-check refresh (plan 5.4): expect new CAPABILITY failures for SDK agents (replay_complete, idempotency, CANCEL-213,
  CURSOR-003, file plans on ENUM-201); never bake a suspected TCK false positive into --expect.
- Finish: grep `.agents/(research|state.md|prompt.md)` in src tests cross-check spec-tracker (clean so far); remind the user to delete
  .agents/prompt.md, .agents/state.md, .agents/research/ before the PR merges. No push / PR unless asked.
## Working notes for programmers (put in every brief)
- Full suite ~10 min: run it in the FOREGROUND (timeout 600000); background runs force premature hand-backs.
- Commit only after a green full run; never stage `tck-iso-*` temp dirs; verify every citation at 3ea94133 via
  `git -C ../agent-client-protocol-2 show 3ea94133:<path>` (never read that working tree; never modify either spec checkout).
- No type checker/linter in CI (ruff not installed); Pyright IDE noise on fixtures/tests is expected.
- Orchestrator: commit state.md only while no programmer runs; commit it BEFORE launching a programmer, not in parallel.
## Settings questions answered by the user this session
- Worktrees assessed but NOT adopted: mode stays single. Only ledger/docs slices 25, 27-v1, 28 could overlap the code chain safely
  (~45-60 min saved); offer again only if the user asks.
## Open questions (waiting on the user)
- none
