# State: Subagents RFD coverage in the TCK
## Settings
mode: single · branch: eugenethedev/subagents (from main 13c4f7a) · reviews: on (one reviewer per finished milestone)
## Decisions (final)
- Research: .agents/research/subagents-coverage.md (RFD docs/rfds/subagents.mdx at upstream 95452a77; no subagent changes since TCK pin 3961af94). Gap ids P1–P11 refer to its gap list.
- Scope: all of M1–M4. P11 (`--subagent-prompt` option) is out of scope unless the user asks.
- Tiers: SUPERSEDED earlier 'MANDATORY' answer. Active/Preview RFD-only rules are never MANDATORY (CAPABILITY or ADVISORY only). Exact tier/gate for RFD-only subagent rows: OPEN (see questions).
- RFD policy (user): the spec-update process tracks RFDs at Active or Preview (not Completed: those are in the docs), plus RFDs that moved into Active+ in the update range, with near-doc weight (own impact researcher). Draft RFDs keep today's 'only where nothing else states the rule' handling.
- Overlap: if the draft docs/schema state the MUST, the row may be MANDATORY (docs decide; v1 ACP-CLIENTCAP-007 stays MANDATORY). Only rules stated solely in an Active/Preview RFD are capped at CAPABILITY/ADVISORY.
- Ledger reasons must not rest on TCK self-choices ('the TCK never advertises X'); such rules become N/A-capable rows.
- P2: add a NEW connection-wide announcement row (id shareable with v1); leave ACP-PROMPT-002 as is.
- All subagent rows other than the P1 fixes SKIP/N-A when the agent exposes no subagent.
## Plan
- M1 (v2 stale fixes): S1.1 fix ACP-RESUME-209 (accept children announced earlier) + ACP-RESUME-002 session filter + fixtures replays_subagent_history/replays_unannounced_child + fix spec-tracker/maps/v2.toml:197,:599 reasons.
- M2 (v2 gaps): S2.1 connection-wide announcement row (P2) · S2.2 `session` content names known session (P3) · S2.3 association integrity (P4) · S2.4 absolute cwd/additionalDirectories (P5) · S2.5 session_message consistency (P6) · S2.6 advisory rows (P7).
- M3 (v1): S3.1 subagents-advertising connection + v1 exposes_subagent + state snapshot schema check + ledger v1.toml:197-205,298-301 conversion · S3.2 v1 versions of P2–P7.
- M0 (process, new): S0.1 update update-to-spec skill + docs/requirements.md (+ docs/spec-updates.md) for the RFD policy above; relabel subagents citations from '(Draft RFD)' to the RFD's real stage (S1.1 used 'Draft RFD').
- M4: S4.1 active cancel tests v1+v2 (P9) · S4.2 ledger entries for unobservable agent-side rules (P10).
## Done
- Research — subagents-coverage.md — verdict: coverage not adequate.
- S1.1 — d899514 — RESUME-209 accepts announced children (connection-wide known set), RESUME-002 scoped to resumed session; fixtures replays_subagent_history (+), replays_unannounced_child (-); v2.toml:197,:599 reasons rewritten as 'Deferred'; pytest 716 passed, spec-tracker 110+5 skip. Follow-up: live child traffic during a replay-requested resume FAILs RESUME-205 (RFD only allows it on no-replay) — decide later.
## Next
- M1 review (range 26e3859..d899514).
- After the tier answer: S0.1, then M2.
## Open questions (waiting on the user)
- Tier/gate for RFD-only subagent rows. Proposal: CAPABILITY with documentation-only gate `inferred:subagents` (precedent: v2 `inferred:configOptions`), i.e. SKIP unless the agent exposed a child (v1: and the TCK advertised `subagents`); SHOULDs ADVISORY.
