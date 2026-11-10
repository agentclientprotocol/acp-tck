# State: update the TCK to the spec
## Settings
mode: single · branch: eugenethedev/update-spec · reviews: on
## Scope
- versions: both (v1, v2)
- base: beac4ba96190018e9f6d82e148ff275084c5aa3e (pinned in both VENDORED.md, 2026-10-19)
- target: 3961af94fa62d2386d993cadf1afc8b146fc799a (upstream main, 2026-11-10, 340 commits)
- spec checkout for spec-impact / spec-tracker tests: ../agent-client-protocol-2 (worktree on main tracking upstream/main).
  Note: check-specification's `.repo` points at ../agent-client-protocol, which is on a feature branch (eugenethedev/end-turn-token-rfd-update); same object store, so commit refs resolve in either.
- schema versions: v1 1.26.0 -> 1.30.0; v2 2.0.0-alpha.9 -> 2.0.0-alpha.14
- depth: v2 = full audit (schema version changed); v1 = diff mode with core escalation (inventory: schema change additive, no $defs removed; most doc hunks editorial). Escalated core docs re-read whole: error, session-setup, initialization, prompt-turn, overview, extensibility, transports
## Decisions (final)
- C1 unstable methods: SPLIT — rows now for session/archive+unarchive and auth/status (v1+v2); ledger/defer session/status, session/set_title, tool_call/cancel, terminal/cancel, proxy/*
- V2-D3 BATCH-209: ADVISORY (crashes_on_batch stays CONFORMANT). Background: upstream PR #2625 (2026-10-29) removed batching following MCP (added 2025-03-26, removed 2025-06-18): ambiguities telling call vs response batches apart, mixed arrays, batches before init, migration guide claim
- C4 permission choice: BY KIND (allow_once > allow_always (record property) > first) + per-test policy hook, v1+v2 (slice S-X1)
- C6 ledger: AGENT-SIDE ONLY (rules binding the agent the TCK deliberately doesn't test; omit client/intermediary/UI rules and pure MAYs)
- C2 null hint: ACCEPT NULL where schema node has x-deserialize-default-on-null (v1+v2, slice S-X3)
- C9 keyword-less error codes: CAPABILITY rows assert error-vs-success; exact code only where a MUST names it (v2 error.mdx:54 -32002, v2 list cursor); SHOULD codes -> separate ADVISORY
- C10 rule-breaking probes: ALLOWED where the spec defines the agent's answer; `_tck`-prefixed values; explain in docstring
- C5 auth hazards: (i) login timeout -> AUTH-GATED SKIP with hint (v1+v2); (ii) new marker `@pytest.mark.revokes("auth", reason=...)` in common plugin: marked tests moved to end, collection order otherwise kept; UsageError if >1 `revokes` test collected (design dependency ordering when a 2nd is needed); mark only tests that take away something other tests rely on (NOT archive/delete of own sessions); unit test + registry test that each logout test carries it + CLAUDE.md note; (iii) leave unknown-type --auth-method as is
- V2-D7: INIT-211/212/213 all MANDATORY; INIT-211 retries after -32602 only (never after -32022); INIT-213 MANDATORY asserts rejection, exact -32600 as separate ADVISORY (per C9); INIT-207 stays narrow
- V2-D16: STRICT CANCEL-209 — hold permission unanswered after session/cancel, expect idle(cancelled); on timeout answer `cancelled` once and wait briefly only to sharpen the FAIL message (verdict still FAIL); SHOULD half = new ADVISORY CANCEL-213 ($/cancel_request), INFO-CANCEL-202 retired; AsksPermissionAgent + asks_permission_ignores_cancel updated
- V2-D18: PROMPT-211 (`_tck_unknown` block) and PROMPTCAP-201 (unadvertised image/audio/resource) both CAPABILITY, assert -32602 + not inserted; no ADVISORY fallback clause
- ID CONVENTION = B (supersedes plan M5/V2-D1/V2-D2 reasoning): a shared id means the same protocol RULE across versions; tier and capability gate are per version. Consequences: v2 JSONRPC-004 retiered in place to MANDATORY (no JSONRPC-201); SHUTDOWN-001 keeps id; rewrite v2 requirements.py:7-13 docstring. Final separate slice S-ALIGN (after all area slices, before S-XC): align ALL ids in v1+v2 to rule B (same rule <-> same id; different rules never share an id)
- ID LIFECYCLE (general rule, all future updates): no retirement mechanism — removed rows/tests/fixture expectations are deleted (plan's "retire" == "remove"; C7 `_RETIRED` dropped); a removed number may be reused later for a new requirement in the same area; guard 1: never reuse a number in the same change that freed it; guard 2: never reuse in a way that breaks rule B; ids stable within a release, compare by text across releases. (A2A TCK: same delete-and-reuse practice, no guards — .agents/research/a2a-tck-id-retirement.md)
- S-ALIGN (this run; general step "final id-alignment slice" for every future update): area slices use provisional numbers for new rows; S-ALIGN (1) researcher inventory, read-only: every v2 2xx row vs v1 registry + every shared id, proposed renames with "same rule because..."; (2) USER APPROVES each rename (borderline pairs are user's call); (3) programmer applies renames everywhere (registries, markers, test_cli/test_registry sets, fixture docstrings, cross-check --expect). Never compact/renumber unaffected rows just to close gaps; existing rows change id only when rule B demands it. The 6 shared ids with differing tier/gate are FINE under B (no change). `2xx` = v2 rule with no v1 counterpart.
- S-DOCS (last pass, after S-ALIGN): create `docs/` at repo root for core contracts (id convention + lifecycle, and other contract material migrated out of AGENTS.md/CLAUDE.md and skills); README.md mentions and links docs/; AGENTS.md (CLAUDE.md is a symlink to it) and skills (.claude/skills -> .agents/skills, tracked) link to docs instead of stating contracts inline. update-to-spec skill gains the final id-alignment step (as a link to docs).
- V2-D19 (part): PERM-203 CAPABILITY (cancelled outcome -> tool call X never `completed`; driven by run_prompt(permission="cancelled")); PATCH-210 CAPABILITY (consistent with V2-D7: no regression to pending, no change after final); optional unknown-optionId probe shares v1 PERM-002's id under rule B
- C3 `_meta` key: KEEP "tck" (no rename; S-X2 dropped)
## Done
- S-v2-0 v2 re-vendor — 7c76250 — schema alpha.14 @ 3961af94; 115 auto + 107 needs-review cites resolved by hand; enum sets +paused/session; map re-cased; pytest 395 green, spec-tracker 115/0 skip. ~50 stale comment/docstring line cites in v2 tests/fixtures left for area slices (plan §6)
- S-X1 permission by kind + policy hook (v1+v2) — 4d88f27 — run_prompt(permission=allow|reject_once|unknown_option|cancelled); fallback recorded as acp_tck_permission_fallback; pytest 395 green
- S-v1-0 v1 re-vendor — 61d40b5 — schema at 3961af94, 40 auto + 13 hand cite fixes, map re-cased; pytest 365 green, spec-tracker 115/0 skip
- Impact research (25 reports) + consolidated plan — .agents/research/plan-spec-update.md (§4 decisions C1-C10, V1-D1..18, V2-D1..31; §8 slice plan)
- v1 change inventory — .agents/research/spec-diff-v1.md
- v2 change inventory — .agents/research/spec-diff-v2.md (breaking: batching removed, ProtocolLevelNotification + AuthCapabilities $defs removed, RequestId no null, AvailableCommand.type required, ...)
## Next
- Remaining plan §4 recommendations (C5, C7-C10, V1-D*, V2-D1/D2, D4-D31): USER IS REVIEWING — do not start area slices that depend on them until answered
- Nothing running. Discussing the judgment calls one by one in chat: C5 done; V2-D7 done; V2-D16 done; V2-D18 done; id convention B, id lifecycle, S-ALIGN, S-DOCS decided; V2-D19 done; remaining judgment call: V2-D31 (in discussion), V2-D16, V2-D18, V2-D19 part, V2-D31. Other ~45 recs: not yet accepted
- Then slices per plan §8: S-v1-0 -> S-X1 -> S-v1-1..7 -> S-v1-9 -> S-v2-0 -> S-X2..4 -> S-v2-1..17 -> optional -> S-XC; review per milestone (v1 milestone, v2 milestone)
## Open questions (waiting on the user)
- FYI: python-sdk checkout `git pull --ff-only` fails ("Cannot fast-forward to multiple branches"); sits at 8a99407 = origin/main. Not repaired.
