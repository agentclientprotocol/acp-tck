# State: update the TCK to the spec: both main full
## Settings
mode: single · branch: eugenethedev/spec-update (from main ee2af8a) · reviews: on
## Spec update scope
- versions: v1 and v2
- base: 3961af94fa62d2386d993cadf1afc8b146fc799a (pinned in both VENDORED.md)
- target: 3ea94133bb4e7cfdb1105df75660ff83e66acf62 (upstream/main, 2026-11-17)
- depth: full audit (requested `full`; also neither map has `rfd_audit`, so every tracked RFD is audited in full)
- spec checkout (the `.repo` one, used for `--spec-repo`): /Users/eugene/Documents/JetBrains/projects/agent-client-protocol
  (on the user's feature branch; never touch its working tree, read target files with `git show 3ea94133:<path>`)
- target-revision working tree: /Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2 (main, at 3ea94133)
## Decisions (final)
- Target stays 3ea94133 even though ../agent-client-protocol-2 moved to a later commit: re-vendor with `git show 3ea94133:<path>`, never `cp` from the working tree.
- Depth: full audit (user asked `full`; v2 schema alpha.14 -> alpha.16; no `rfd_audit` in either map).
- Upstream removed the RFD Active stage at target: tracked RFDs are only `subagents` (Preview) and `plan-operations` (Preview), both versions.
- Impact research grouped by area (one researcher per doc group, one per tracked RFD); common brief `.agents/research/impact-brief.md`.
- Plan: `.agents/research/plan-consolidated.md`. User accepted ALL recommended options for D1-D13 (2026-11-18):
  D1(a) delete PLAN-001, add PLAN-003 + PLAN-004; D2(a); D3(a); D4(a); D5 literal; D6 INFORMATIONAL; D7 as recommended;
  D8 all; D9 all; D10(a) now, (b) follow-up; D11 backfill slice INCLUDED (slice 27), row candidates follow-up;
  D12(a) mcp-over-acp deferred to a follow-up PR, transport RFD out of scope, no ledger entries for either; D13 all defaults.
- No "ignored RFDs" list exists in the maps; nothing to remove there (user asked; confirmed by grep).
## Done
- Step 2 inventory — ceef9a8 — .agents/research/spec-diff-v{1,2}.md
## Next
- Step 6 slices in plan order (section 5): R-V1 -> R-V2 -> area slices 1-28 -> id alignment (user approves each rename)
  -> cross-check refresh. One programmer at a time. Review per milestone (milestones: re-vendor; area slices; id
  alignment + cross-check).
- R-V1: in progress.
## Open questions (waiting on the user)
- none
