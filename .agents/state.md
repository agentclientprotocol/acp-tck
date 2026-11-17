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
## Done
- Step 2 inventory — ceef9a8 — .agents/research/spec-diff-v{1,2}.md
## Next
- Step 4 impact research DONE: 27 reports in .agents/research/impact-*.md (13 v1 incl. plan-operations, 14 v2).
- Step 5 running: one researcher consolidates all reports -> .agents/research/plan-consolidated.md (deduped changes,
  decisions, slice plan). Then present it to the user and wait for decisions.
- Side question DONE (scope of formerly-Active, never-backfilled RFDs; all Draft at target), reports scope-rfds-*.md:
  13 rfds/v2/* -> 0 RFD-sourced rows (all doc-stated; doc gaps go to doc audit). mcp-over-acp remainder -> M per version
  (~7-8 rows, 6-7 fixtures each, shared MCP provider module, mock client answers mcp/message), Draft-RFD citation justified
  for RFD-only rules. streamable-http-websocket-transport -> recommend out of scope (needs HTTP/WS harness, L-XL).
  Awaiting the user's call on whether to include mcp-over-acp in this PR.
## Open questions (waiting on the user)
