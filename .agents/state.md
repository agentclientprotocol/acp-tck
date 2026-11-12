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
## Next
- S3.1 (M3).
## Follow-ups (not scheduled)
- `session` refs and child traffic during load/resume replay not judged by SUBAGENT rows (RESUME-209 owns replay).
- S37 converse (listed child idle with empty own background) could be a row; touches STATE-206/207/208.
- Upstream drift past pin (upstream/main c392d7e9): subagents RFD adds "`unknown` freezes the child's background list; MUST NOT invent final statuses" -> next spec update.
- Earlier commits carry Claude-Session trailers; user may want them stripped before PR.
## Open questions (waiting on the user)
- Approve S0.3 per-file proposal.
