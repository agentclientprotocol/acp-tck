# State: Subagents RFD coverage in the TCK
## Settings
mode: single · branch: eugenethedev/subagents (from main 13c4f7a) · reviews: on (one reviewer per finished milestone)
## Decisions (final)
- Research: .agents/research/subagents-coverage.md (RFD docs/rfds/subagents.mdx at upstream 95452a77; no subagent changes since TCK pin 3961af94). Gap ids P1–P11 refer to its gap list.
- Scope: all of M1–M4. P11 (`--subagent-prompt` option) is out of scope unless the user asks.
- Tiers: the lowercase/declarative rules (no reparenting/cycles, participant-ID consistency, child-only cancel, cascade cancel to awaited children) are MANDATORY.
- P2: add a NEW connection-wide announcement row (id shareable with v1); leave ACP-PROMPT-002 as is.
- All subagent rows other than the P1 fixes SKIP/N-A when the agent exposes no subagent.
## Plan
- M1 (v2 stale fixes): S1.1 fix ACP-RESUME-209 (accept children announced earlier) + ACP-RESUME-002 session filter + fixtures replays_subagent_history/replays_unannounced_child + fix spec-tracker/maps/v2.toml:197,:599 reasons.
- M2 (v2 gaps): S2.1 connection-wide announcement row (P2) · S2.2 `session` content names known session (P3) · S2.3 association integrity (P4) · S2.4 absolute cwd/additionalDirectories (P5) · S2.5 session_message consistency (P6) · S2.6 advisory rows (P7).
- M3 (v1): S3.1 subagents-advertising connection + v1 exposes_subagent + state snapshot schema check + ledger v1.toml:197-205,298-301 conversion · S3.2 v1 versions of P2–P7.
- M4: S4.1 active cancel tests v1+v2 (P9) · S4.2 ledger entries for unobservable agent-side rules (P10).
## Done
- Research — subagents-coverage.md — verdict: coverage not adequate.
## Next
- S1.1.
## Open questions (waiting on the user)
- none
