# State: v2 -> draft (unstable) schema switch

Branch: `eugenethedev/v2-draft` (feature branch). Prompt: `.agents/prompt.md`.

## Rules (user)
- ONE programmer at a time, NO worktrees, work + commit on current branch, NEVER push.

## Status: FEATURE COMPLETE, wrapping up (not pushed)
Commits on top of main: 5a271ab, 3530bde, 1314e09, c378cf6, 71de2c2, 183ee5a (README).
Full suite green (294 at 71de2c2; 183ee5a docs-only). Cross-check: all 4 upstream agents match
`--expect` baselines, identical to main (only schema_revision differs).
mcp/message: user decided to disregard (RFD-only behaviour).

## Final step
- Fix python_v2_agent FAIL-reason comment in `scripts/cross-check.sh` -- DONE `17a13a5`. ORCHESTRATOR WORK COMPLETE.
- `.agents/research/*` NOT deleted (user didn't ask); user closes out.
