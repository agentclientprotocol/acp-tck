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
- Slice 28: PL "Prompt suggestions (unstable)" and "Session cursors (unstable)" STAY in the v2 left-out list (user, 2026-11-18); not core_doc sections.
- Milestone-2 fixes (user, 2026-11-18): fix EVERYTHING (S1-S10, N1-N18) in 3 slices by area, one commit each:
  FIX-SA (opus): S1, S4, S7, S8, N4, N5, N11, N12, N13, N14 — subagent/child-cancel harness, both versions where applicable.
  FIX-ROWS: S2, S3, S5, S6, N1, N2, N3, N6, N7, N8, N9, N15 (walker unit tests), N16 (repeat initial-config probes on session/fork when advertised), N18 (harden the 2 load-flaky CLI tests if the 1 s --timeout cause is confirmed).
  FIX-LEDGER: S9, S10, N10, N17.
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
- V2-SA3 — 0e649c6 — +SUBAGENT-018 ADVISORY / -019 CAPABILITY child probes (list, new, resume, delete, close last), +LIST-004, +SUBAGENT-205 (delayed mirror; 201 keeps missing/swapped), SUBAGENT-004 ext; 7 fixtures; suite green (1167). For review: error.mdx cite is :58 not :57; probes share the subagents connection.
- V2-SA4 — 4dfbf16 — +RESUME-223/-224/-225, +SUBAGENT-203 (cap.session), +SUBAGENT-204 (inferred:subagentCancel); run_prompt(hold_children=) + ChildPermissionHold, _child_cancel holds child requests; docs/mock-client.md section; 8 fixtures; CLI_SUBPROCESS_TIMEOUT 60->120 (conforming_full ~61 s); suite green (1189). For review: 204 also judges parent-cascade stops (gate narrower than judged); 016 PASS + 204 FAIL possible now; 202 may SKIP if parent waits on held child request; 225 judges only params.sessionId traffic; 224 doesn't judge update fields; U13c RFD line is :1268. Possibly flaky under load: test_mcp_unsupported_transport_fixtures_fail_mcp_203_only, test_permission_before_requires_action_judges_cancel_while_blocked. Follow-up: elicitation $/cancel_request on close/cancel.
- LEDGER v1 (25) — 1c1a02c — D10 rewords (error:37, transports, TC:250, get-auth-state 297/313, session-list:258 Deferred, status/set_title), +AuthAccount.description (:174-176)
- LEDGER v2 (26) — 6fe8518 — same rewords + SCO:390 (plan's :375) cites SS:56, session-list 162/248/249, security:81, TC:387, +SA:263, TC:753-756 extended (resolve half not observable beyond SUBAGENT-002)
- BACKFILL (27) — 311ef10 — v1 9 elicitation + agent-plan:53; v2 5 meta-patch + security:59; spec-tracker 120, full suite green (1189)
- DOCS (28) — c80a543 — stage wording Draft/Preview/Completed (docs, README, update-to-spec + check-specification skills), impact.py TRACKED_STAGES=("Preview",) (legacy Active still read), inferred list +promptSuggestions/subagents/subagentCancel/toolCallCancel/terminalCancel, rfd_audit=3ea94133 in both maps, v2 PL code += test_idempotency, SCO:585 reworded; spec-tracker 121, suite 1189. For review: test_session_options/test_initial_config/test_prompt_suggestions/test_cursors NOT added to core_doc code (their sections aren't core; accepted); map header comment 'rfd_audit absent until first full audit' now stale (nit).
- Review milestone 2 — review-area-slices.md — 0 blocker, 10 should-fix (S1-S10), 18 nits (N1-N18); suite green at c80a543 (1189). Fix plan pending the user.
- FIX-SA — 7ee8a00 — S1 (205 pairs n-th/n-th, stops at first diff), S4 partial (resume_reaction_start; in-flight traffic on the resumed session itself still opens the window early), S7+N4 both versions, S8 text (test already existed; failed-load assert added), N5, N11, N12 (stopped_requests_kept skips background subjects), N13, N14 (204 gate -> inferred:subagents); suite green (1198). One prior full run had 8 v2 test_cli load flakes (unprefixed_background_type, proceeds_after_cancelled_permission, accepts_relative_cwd, resume_205_judges_every_chunk_kind, permission_before_requires_action, noisy_stderr, reports_background_work, +1 lost) -> N18 in FIX-ROWS is now a real item. Follow-up: SUBAGENT-201 child_state_mirrors scans ahead (message count only).
- FIX-ROWS — 8765ae0 — S2 (replay window), S3 (008 baseline attribution; options_notifies_initial now FAILs only 007), S5, S6 (prompt first; 221 joins 5 cascade sets), N1-N3, N6-N9, N15 (test_cursor_rows.py x2), N16 (fork probes OPTIONS-004..006 + v1 -008; 7 fork fixtures), N18 root cause = CPU starvation (startup + subprocess cap): CLI_SUBPROCESS_TIMEOUT 300 both, CLI_STARTUP_TIMEOUT 5 default (4 never-answer tests keep 1); suite 1222 green BEFORE a last startup_timeout tweak (verified by the next slice's full run). For review: v2 ledger SCO:584 'not attributable' vs v1 008 baseline attribution; v2 OPTIONS-006 creates an extra source session when fork advertised.
## Next
Order (plan section 5): fix slice FIX-LEDGER -> id alignment -> cross-check refresh -> final review.
- Milestone 1 (re-vendor) DONE and reviewed. Milestone 2 (area slices) in progress: slices 1-28 done (ALL area slices) (plus R-FIX, typo fix, DEL204-FIX).
- Milestone-2 review DONE over 7254513..c80a543 (milestone-1 review covered 6bce0b3..7254513), report .agents/research/review-area-slices.md, decisions D1-D13,
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
