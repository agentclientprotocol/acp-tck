# State: Address PR #10 follow-ups (1) subagent prompt options, (2) ACP-STATE-210, (3a) MCP ledger reasons, (4) -32602 cancel probes, in one PR
## Settings
mode: single · branch: pr10-follow-ups · reviews: on
## Decisions (final)
- Untracked Active/Preview RFDs (incl. the post-pin Subagents RFD rule) go in a separate PR; out of scope here.
- Out of this PR: MCP stub servers (3b); `--workers N` (5), skipped for now by the user.
- (1) Add `--subagent-prompt` (drives the subagents-connection turn; default None keeps today's text per version) and `--subagent-cancel-prompt` (replaces `--cancel-prompt` in the child-cancel turn: SUBAGENT-016/017, v2 202, TOOLCANCEL-203/TERMCANCEL-203; falls back to `--cancel-prompt` when unset). Runs stay independent one-shot turns (no chaining). No child despite a prompt stays SKIPPED. The `--subagent-prompt` turn gets one `--timeout` (whole-turn deadline, like root turns; no multiplier); README documents raising it and notes v1 CLIENTCAP-001..003 also judge that connection. Same slice fixes README `--timeout` wording (whole-turn deadline for prompt turns in v1 and v2, not per-response) and the v2 `run_prompt` docstring ("Every wait is bounded by `timeout`"). The drivers' existing `timeout * 3` stays. Research: followup-subagent-prompt.md.
- (2) New v2 row ACP-STATE-210 (ADVISORY, gated like 209): start-side half of prompt-lifecycle.mdx:205. Caveat in row text about visible housekeeping tool calls; judge only the first state_update after announcement; a listed tool call counts as listing its terminal. Reword 209 + docstrings; narrow ledger v2.toml:188-191 to :207. Research: followup-state-209-start-side.md.
- (3a) Reword all 7 MCP ledger reasons (v1.toml:127; v2.toml:267,363,445,450,465,521) as "Deferred" entries naming the real blocker; fix the two that wrongly say no MCP server exists. No code. Research: followup-mcp-stub.md.
- (4) Both halves of the v2 -32602 probes: TOOLCANCEL/TERMCANCEL-206 (unknown id rejected, CAPABILITY), 207 (code -32602, ADVISORY), 208 (live non-cancellable item rejected, CAPABILITY), 209 (code, ADVISORY). Gates inferred:toolCallCancel / inferred:terminalCancel, defined as "agent advertised `cancel` at any point in the driven turn". Delete ledger v2.toml:605-608, 615-618. Research: followup-not-cancellable-probes.md.
## Done
- Assessment of five follow-ups — reports in .agents/research/followup-*.md.
## Plan
- M1 Subagent prompt options: S1 (1).
- M2 v2 background-work rows + MCP ledger: S2 ACP-STATE-210; S3 unknown-id probes (206/207); S4 not-cancellable probes (208/209); S5 MCP ledger reasons (3a). One review for M2.
- Order: S1→S2→S3→S4→S5. Plan approved by the user.
## Next
- S1 (programmer), once the user gives the go-ahead. Nothing started yet.
## Open questions (waiting on the user)
- Go-ahead to start S1.
