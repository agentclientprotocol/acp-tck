# State: Address PR #10 follow-ups (1) subagent prompt options, (2) ACP-STATE-210, (3a) MCP ledger reasons, (4) -32602 cancel probes, in one PR
## Settings
mode: single · branch: pr10-follow-ups · reviews: on
## Decisions (final)
- M2 review: fix all five findings (S6 = 1+2, S7 = 3+4+5).
- Untracked Active/Preview RFDs (incl. the post-pin Subagents RFD rule) go in a separate PR; out of scope here.
- Out of this PR: MCP stub servers (3b); `--workers N` (5), skipped for now by the user.
- (1) Add `--subagent-prompt` (drives the subagents-connection turn; default None keeps today's text per version) and `--subagent-cancel-prompt` (replaces `--cancel-prompt` in the child-cancel turn: SUBAGENT-016/017, v2 202, TOOLCANCEL-203/TERMCANCEL-203; falls back to `--cancel-prompt` when unset). Runs stay independent one-shot turns (no chaining). No child despite a prompt stays SKIPPED. The `--subagent-prompt` turn gets one `--timeout` (whole-turn deadline, like root turns; no multiplier); README documents raising it and notes v1 CLIENTCAP-001..003 also judge that connection. Same slice fixes README `--timeout` wording (whole-turn deadline for prompt turns in v1 and v2, not per-response) and the v2 `run_prompt` docstring ("Every wait is bounded by `timeout`"). The drivers' existing `timeout * 3` stays. Research: followup-subagent-prompt.md.
- (2) New v2 row ACP-STATE-210 (ADVISORY, gated like 209): start-side half of prompt-lifecycle.mdx:205. Caveat in row text about visible housekeeping tool calls; judge only the first state_update after announcement; a listed tool call counts as listing its terminal. Reword 209 + docstrings; narrow ledger v2.toml:188-191 to :207. Research: followup-state-209-start-side.md.
- (3a) Reword all 7 MCP ledger reasons (v1.toml:127; v2.toml:267,363,445,450,465,521) as "Deferred" entries naming the real blocker; fix the two that wrongly say no MCP server exists. No code. Research: followup-mcp-stub.md.
- (4) Both halves of the v2 -32602 probes: TOOLCANCEL/TERMCANCEL-206 (unknown id rejected, CAPABILITY), 207 (code -32602, ADVISORY), 208 (live non-cancellable item rejected, CAPABILITY), 209 (code, ADVISORY). Gates inferred:toolCallCancel / inferred:terminalCancel, defined as "agent advertised `cancel` at any point in the driven turn". Delete ledger v2.toml:605-608, 615-618. Research: followup-not-cancellable-probes.md.
## Done
- Assessment of five follow-ups — reports in .agents/research/followup-*.md.
- S1 subagent prompt options — 9813646 — `--subagent-prompt`/`--subagent-cancel-prompt` (v1+v2, fallback to `--cancel-prompt`), `--timeout` wording fixed; new fixtures `exposes_subagent_on_request.py`; 1011 passed. M1 done.
- S2 ACP-STATE-210 — e2de37f — ADVISORY row gated like 209; fixtures starts_background_after_idle / background_start_not_resent; ledger narrowed to :207; 1014 passed. Unjudged paths (running next state, idle w/o list, item ends first) not unit-tested — flag for M2 review.
- S3 unknown-id probes — d315fb7 — TOOLCANCEL/TERMCANCEL-206 (CAPABILITY) + 207 (ADVISORY); `_FollowUpProbe` base (S4 subclasses it), per-kind cancel_seen gates; `cancel_missing_after_completion.py` now also FAILs both 207s (documented cascade); 1018 passed + spec-tracker 120. Ledger entries v2.toml:605-608/615-618 are single entries covering both halves → S4 deletes them.
- S4 not-cancellable probes — aa8049f — TOOLCANCEL/TERMCANCEL-208 (CAPABILITY) + 209 (ADVISORY); `_UncancellableProbe` with race grace (mutation-checked); opt-in fixture knob `uncancellable_work` (set in conforming_full); ledger entries deleted; no FAIL-set changes; 1025 passed + spec-tracker 120. Programmer's calls to surface in review: knob opt-in (avoids churn); a result for a finished-but-never-cancellable item FAILs 208; main probe may pick an item that gains cancel mid-flight (worst case SKIP raced). Not done (out of scope): child-session variant, unknown-session -32002 probe.
- S5 MCP ledger reasons — 42cd99a — 7 reasons reworded as "Deferred: <blocker>" (stdio-only stub, no tools, argv-only recording, no HTTP stub); v2 capability name fixed to `capabilities.session.mcp.http`; spec-tracker 120 passed. Not changed: section comment v2.toml:358 (optional per research). M2 slices done; .agents grep clean.
- Full suites at 42cd99a (orchestrator run): 1025 passed, spec-tracker 120 passed.
- M2 review — .agents/research/review-m2.md — 0 blockers, 1 should-fix (main probe can re-cancel follow-up's in-flight target → false FAIL TOOLCANCEL-201, confirmed), 4 nits (uncancellable target ignores main.tried; 210 lacks idle-omits-item FAIL test; 210 citation missing prompt-lifecycle.mdx:208; conforming_full docstring stale).
## Plan
- M1 Subagent prompt options: S1 (1).
- M2 v2 background-work rows + MCP ledger: S2 ACP-STATE-210; S3 unknown-id probes (206/207); S4 not-cancellable probes (208/209); S5 MCP ledger reasons (3a). One review for M2.
- Order: S1→S2→S3→S4→S5. Plan approved by the user.
## Next
- S6 (running): probe target exclusion, review findings 1+2. Then S7: nits 3+4+5. Then full suites.
## Open questions (waiting on the user)
- None.
