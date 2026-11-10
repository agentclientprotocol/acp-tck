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
- C3 `_meta` key: KEEP "tck" (no rename; S-X2 dropped)
## Done
- Impact research (25 reports) + consolidated plan — .agents/research/plan-spec-update.md (§4 decisions C1-C10, V1-D1..18, V2-D1..31; §8 slice plan)
- v1 change inventory — .agents/research/spec-diff-v1.md
- v2 change inventory — .agents/research/spec-diff-v2.md (breaking: batching removed, ProtocolLevelNotification + AuthCapabilities $defs removed, RequestId no null, AvailableCommand.type required, ...)
## Next
- Remaining plan §4 recommendations (C5, C7-C10, V1-D*, V2-D1/D2, D4-D31): USER IS REVIEWING — do not start area slices that depend on them until answered
- Running now (no pending decisions): S-v1-0 re-vendor, then S-X1, then S-v2-0
- Then slices per plan §8: S-v1-0 -> S-X1 -> S-v1-1..7 -> S-v1-9 -> S-v2-0 -> S-X2..4 -> S-v2-1..17 -> optional -> S-XC; review per milestone (v1 milestone, v2 milestone)
## Open questions (waiting on the user)
- FYI: python-sdk checkout `git pull --ff-only` fails ("Cannot fast-forward to multiple branches"); sits at 8a99407 = origin/main. Not repaired.
