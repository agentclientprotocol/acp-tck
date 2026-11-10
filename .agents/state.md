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
## Done
- v1 change inventory — .agents/research/spec-diff-v1.md
## Next
- Step 2: v2 inventory running -> .agents/research/spec-diff-v2.md
- Step 4: impact research per affected doc (v1 + v2)
## Open questions (waiting on the user)
