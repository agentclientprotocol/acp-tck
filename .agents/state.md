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
- v2 change inventory — .agents/research/spec-diff-v2.md (breaking: batching removed, ProtocolLevelNotification + AuthCapabilities $defs removed, RequestId no null, AvailableCommand.type required, ...)
## Next
- Step 4 impact research. Reports go to .agents/research/impact-v<N>-<area>.md; shared briefs in /tmp/tckbrief/common-v{1,2}.md (regenerate from the v1 one if /tmp was wiped).
  - v1 (12): error, session-setup, initialization, prompt-turn, overview-ext-transports, session-list-delete, config-modes-commands, tools-terminals-fs, agent-plan-content, auth-cancel-elicitation, security (done), schema; config-modes-commands done; agent-plan-content done; prompt-turn done; overview-ext-transports done; initialization done; session-list-delete done; session-setup done; auth-cancel-elicitation done; error done; tools-terminals-fs done (flags harness safety: v1 mock client picks FIRST permission option, could persist allow_always — check v2 helper too)
  - v2 (13): initialization done; prompt-lifecycle done; cancellation done; transports done; overview-error done; session-setup done; extensibility done; tool-calls-plan done; config-commands done; list-delete-fork done; auth-elicitation done; content-security done, schema running (all launched)
- Step 5: consolidate into requirement-change table + slice plan, ask user for tier/retirement decisions
## Open questions (waiting on the user)
- FYI: python-sdk checkout `git pull --ff-only` fails ("Cannot fast-forward to multiple branches"); sits at 8a99407 = origin/main. Not repaired.
