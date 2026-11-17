# State: Assess PR #10 follow-ups (excluding the upstream Subagents RFD rule) for small/medium complexity, to pick a set for one PR
## Settings
mode: single · branch: pr10-follow-ups · reviews: on
## Decisions (final)
- Untracked Active/Preview RFDs (incl. the post-pin Subagents RFD rule) go in a separate PR; out of scope here.
- Follow-up (1): add both `--subagent-prompt` (drives the subagents-connection turn) and `--subagent-cancel-prompt` (replaces `--cancel-prompt` in the child-cancel turn: SUBAGENT-016/017, v2 202, TOOLCANCEL-203/TERMCANCEL-203), mirroring `--cancel-prompt` for root sessions. Runs stay independent one-shot turns (no chaining). `--subagent-cancel-prompt` falls back to `--cancel-prompt` when unset. The `--subagent-prompt` turn gets one `--timeout` (whole-turn deadline, like root turns; no multiplier); README documents raising it. Same slice fixes README `--timeout` wording (it is the whole-turn deadline for prompt turns in v1 and v2, not per-response) and the v2 `run_prompt` docstring ("Every wait is bounded by `timeout`"). The drivers' existing `timeout * 3` stays.
## Done
- Assessment of five follow-ups — reports in .agents/research/followup-*.md:
  - subagent-prompt: S (~200-300 LOC), scope B (subagents connection only)
  - state-209-start-side: S (~150-180 LOC), new ADVISORY row ACP-STATE-210
  - mcp-stub: scope (a) ledger rewording S (~20 lines, 7 entries); stdio stub b1 M; HTTP stub b2 M-L; b3 blocked; b4 out (Active RFD)
  - not-cancellable-probes: unknown-id half S (~250-350); not-cancellable half M (~450-550); both M (~700-900)
  - workers: M (~250-350), two slices (plugin aggregation, then CLI/deps/docs)
## Next
- User picks the PR scope and answers each item's design questions; then plan milestones/slices.
## Open questions (waiting on the user)
- Scope selection; per-item design questions (see reports).
