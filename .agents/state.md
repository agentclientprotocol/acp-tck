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
- Step 6 slices in plan order (section 5): R-V1 -> R-V2 -> area slices 1-28 -> id alignment (user approves each rename)
  -> cross-check refresh. One programmer at a time. Review per milestone (milestones: re-vendor; area slices; id
  alignment + cross-check).
- Milestone 1 (re-vendor) DONE and reviewed.
- Slice 16 V2-TOOL: in progress. Programmers must run the full suite in the FOREGROUND (timeout 600000, ~8.5 min); background runs force premature hand-backs.
- Pre-existing (also on main ee2af8a): plain `acp-tck --protocol-version 2` on v2 conforming_full FAILs ACP-DELETE-204 — fixture answers session/delete before the cancelled idle when a permission request is pending. Not a regression; reported to the user; candidate fix slice.
- For V2-REPLAY (slice 14): once `_base.py` sends `replay_complete`, drop the explicit `replay_complete` from `replays_suggestions.py` and remove SUGGEST-004 from `_FULL_EXPECTED_SKIPS` in tests/v2/test_cli.py. Left over from R-V1/R-V2 for later slices: cost entry, "stated only by the Subagents RFD" text (V1-SA1/V2-SA1); v2 ledger `agent-plan.mdx:119` (V2-PLAN); TOOLCANCEL/TERMCANCEL-2xx not re-judged vs changed tool-calls.mdx 456-459/600-605 text (V2-TOOL); whether PL prompt-suggestions/cursors sections become core_doc sections (DOCS slice 28).
- For LEDGER-HYGIENE v2: add v2 `SA:263` (outgoing view + link, SHOULD; v1 twin `SA:285`) entry; extend the `TC:753,754` entry to cover `TC:755-756` or note SUBAGENT-002 covers it.
- User asked about parallelizing with worktrees; I assessed (only ledger/docs slices 25, 27-v1, 28 could overlap, ~45-60 min saved); no change made, mode stays single unless the user says otherwise.
## Open questions (waiting on the user)
- none
