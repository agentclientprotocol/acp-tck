# State: Subagents RFD coverage in the TCK (+ RFD process fix, background-work and mcp-over-acp backfills)
## Settings
mode: single · branch: eugenethedev/subagents (from main 13c4f7a) · reviews: on (one reviewer per finished milestone)
## Commit messages
- Plain conventional messages, NO attribution trailers (no `Claude-Session:`). Commits up to fae0c9d-era have them.
## Verification cadence
- `-n auto` on every product `uv run pytest` (until S0.3 makes it the default). Full suite ~5-6.5 min parallel (38.5 min serial).
- Programmers run the FULL product suite per slice, plus spec-tracker tests; reviewer per milestone.
## Decisions (final)
- Research: .agents/research/subagents-coverage.md (RFD docs/rfds/subagents.mdx at upstream 95452a77; identical at TCK pin 3961af94). Gap ids P1–P11.
- Scope: M1–M6. P11 (`--subagent-prompt`) out of scope unless asked.
- Tiers: Active/Preview RFD-only rules are never MANDATORY. RFD-only MUST (incl. lowercase/declarative binding rules: no reparenting/cycles, participant consistency, child-only cancel, cascade cancel) = Tier.CAPABILITY with documentation-only gate `inferred:<feature>` (subagents: `inferred:subagents`; test self-SKIPs, never `@pytest.mark.capability`); if no gate fits = ADVISORY. RFD-only SHOULD = ADVISORY.
- Docs precedence (user): when a tracked RFD and the version's draft docs/schema describe the same behaviour, the docs govern (primary citation, text, tier; RFD secondary; conflicts recorded). Applied to both versions. v1 ACP-CLIENTCAP-007 stays MANDATORY.
- RFD tracking: stage = nearest enclosing stage group in docs/docs.json ('Active > v2' = Active, v2 only); tracked = Active/Preview at target + moved into them in range; Completed never tracked. Each tracked RFD gets its own impact researcher; first update under the policy audits all tracked RFDs (marker `rfd_audit` in spec-tracker/maps/v<N>.toml). Labels: RFD stage at the pin, e.g. "(Active RFD)".
- Ledger reasons must not rest on TCK self-choices.
- No backfill of the other 13 `rfds/v2/*`. M5 (background-work) and M6 (mcp-over-acp P1 only) are in scope.
- P2: ACP-PROMPT-002 unchanged; new shared-id family ACP-SUBAGENT-0xx (v2-only rows 2xx, e.g. ACP-SUBAGENT-201; 010 is a retired gap, never reuse).
- Cancel rows gate: `inferred:toolCallCancel` / `inferred:terminalCancel`.
- Don't invent requirements from shape descriptions without a binding statement (e.g. no session_message_chunk identity row).
## Plan
- M3 (v1): S3.1 `subagents: {}`-advertising v1 connection + v1 exposes_subagent (child traffic only when advertised, so CLIENTCAP-007 holds) + v1 versions of shared rows 001–009, 011–014 (research P8) + v1 `state` snapshot schema check + convert v1 'never advertises' ledger entries (~v1.toml:201-209, 302-305) + stage labels on ledger RFD citations (get-auth-state, session-status, session-set-title, proxy-chains). May split into S3.1/S3.2.
- M5 (v2 background-work): S5.1 PATCH-211 exemption for tool calls referencing a listed terminal · S5.2 tool_call/cancel + terminal/cancel happy paths + fix v2.toml ~661-669 ledger · S5.3 ADVISORY re-send state on background change, background across resume, fork isolation, ENUM-201 background[].type, ledger rewording (v2.toml ~188-191, 392-395, 644-647). Source: backfill-v2-background-work.md.
- M6 (mcp-over-acp P1): S6.1 `acp` probe in v2 ACP-MCP-203 + mcp/message notification-silence row (v2 CAP session.mcp.acp; v1 CAP mcpCapabilities.acp). Source: backfill-mcp-over-acp.md.
- M4: S4.1 active child cancel tests v1+v2 (P9) · S4.2 ledger entries for unobservable agent-side rules (P10).
- S0.3 (proposed, awaiting user approval): isolate acp-tck's own pytest run from repo config (pytest.ini per conformance dir; today it resolves ../../../../pyproject.toml) + root `addopts = ["-n","auto"]` + new docs/testing.md single source + per-file cleanup of literal `uv run pytest` (list given in chat: AGENTS.md keeps command + link; development.md sections move; writing-tests/spec-updates reminders link; ci.yml drops -n auto; programmer.md/reviewer.md/orchestrator SKILL reminders without commands; spec-tracker/cross-check READMEs unchanged).
## Done
- Research — subagents-coverage.md.
- M1: S1.1 d899514, S1.2 c25547e (RESUME-209 known children scoped to resume exchange; RESUME-002/204/205 scoped to resumed session; fixtures replays_subagent_history, replays_unannounced_child, replays_child_before_announce). Review: review-m1.md.
- M0: S0.1 dbaafc1, S0.2 3e80423 + 69729e4 (RFD policy in update-to-spec skill, docs/requirements.md, docs/spec-updates.md; spec-impact "7. RFD stages"; researcher.md wording; relabels; inferred: docs + guard tests/common/test_capability_markers.py). Review: review-m0.md.
- Backfill research: backfill-v2-background-work.md, backfill-mcp-over-acp.md.
- M2 (v2 ACP-SUBAGENT-001..009, 011..014, 201): S2.1 b9021ac, S2.2 f9f9b99, S2.3 28a0f22, S2.5 08f59b4, S2.6 28eb901, S2.7 2714a68 (review fixes: permission subject.toolCall carrier, 010->201, no vacuous PASS, shared cached connection per process in test_subagents.py). Full suite at 2714a68: 801 passed (308 s); spec-tracker 115/5. Review: review-m2.md.
- M3: S3.1 dfe13a0 — v1 `subagents: {}` connection (cached per process; session/new, turn, session/load replay if loadSession, quiet drain); v1 ACP-SUBAGENT-001..009 (CAP inferred:subagents), 011..014 (ADVISORY), v1-only 015 (CAP: schema validity of subagent messages incl. state snapshot; S6; accepted as 015 — rule B only reserves 2xx for v2-only, so 015 must never mean another rule in v2); 001 also judges child-ID fs/*/terminal/*; 3 'never advertises' v1 ledger entries -> rows; 18 ledger RFD citations labelled (Draft RFD); 24 v1 fixtures (exposes_subagent, replays_subagent_history, 22 violators). Full suite 830 passed (290 s); spec-tracker 115/5.
- M3 review — .agents/research/review-m3.md — 0 blockers, 1 should-fix (v1 001 known children not scoped to session/load replay -> false PASS), 7 nits. Orchestrator decision: scope known children to the load exchange like v2 RESUME-209 (same rule), exempting replayed session_message participants (RFD:942-948) and replayed `session` refs (RFD:638-639); drain before load; cite replay lines.
- M5: S5.1 5e5941b (PATCH-211 exempts tool calls referencing a listed terminal; docs discrepancy tool-calls.mdx:423 recorded; fixtures references_background_terminal (+), leaves_terminal_tool_call_in_progress (-)); S5.2 2978360 (v2-only ACP-TOOLCANCEL-201/202, ACP-TERMCANCEL-201/202, CAP inferred:toolCallCancel/terminalCancel, test_item_controls.py, `drive_item_cancel`, `_base` opt-in cancellable_work in conforming_full; 4 violators + completes_before_cancel race fixture; ledger: removed 2 wrong 'deferred unstable' entries, added narrower -32602/foreground entries). Full suite 838 passed (309 s).
## Next
- S3.2 (M3 review fixes): finding 1 as decided; nits 2-8 (015 judges only subagent-specific parts so no double FAIL with PROMPT-002; load timeout -> per-row SKIP not cached FAIL; mock-client.md 'one exception' + v1 permission-cancel line; exposes_subagent.py:17 stale ref; 009 row text; '(Active RFD)' in failure messages v1+v2; v1 helper unit tests); S11: extend MANDATORY ACP-CLIENTCAP-001..003 to the subagents connection (docs precedence).
- Then S5.3 (rest of M5), M5 full suite + review, M6, M4.
- S4.2 must add a 'Deferred' v1 ledger entry for S9 (child terminal/create cwd; blocker: mock client implements no terminal). S20: at most INFORMATIONAL; skip.
## Follow-ups (not scheduled)
- v1 S11 row (child-ID fs/terminal/elicitation request on a connection advertising none) and S20 heuristic row; S9 (child terminal/create cwd) untestable with the mock client answering -32601.
- `session` refs and child traffic during load/resume replay not judged by SUBAGENT rows (RESUME-209 owns replay).
- S37 converse (listed child idle with empty own background) could be a row; touches STATE-206/207/208.
- Upstream drift past pin (upstream/main c392d7e9): subagents RFD adds "`unknown` freezes the child's background list; MUST NOT invent final statuses" -> next spec update.
- Earlier commits carry Claude-Session trailers; user may want them stripped before PR.
## Open questions (waiting on the user)
- Approve S0.3 per-file proposal.
