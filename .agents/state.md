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
- Depth: full audit (user asked `full`; v2 schema alpha.14 -> alpha.16; no `rfd_audit` in either map).
- Upstream removed the RFD Active stage at target: tracked RFDs are only `subagents` (Preview) and `plan-operations` (Preview), both versions.
- Impact research grouped by area (one researcher per doc group, one per tracked RFD); common brief `.agents/research/impact-brief.md`.
## Done
- Step 2 inventory — ceef9a8 — .agents/research/spec-diff-v{1,2}.md
## Next
- Step 4 impact research running: v1 core, initialization, session-setup, session-list-delete, prompt-turn, content-plan-commands,
  config-options, tools-terminals-fs, auth-elicitation-security, subagents-doc, rfd-subagents, schema; rfd-plan-operations (v1+v2);
  v2 overview-error, extensibility, transports-security-content.
- Step 4 still to launch (20-agent concurrency cap) — report names `impact-v2-<slug>.md`: initialization, session-setup,
  session-list-delete, prompt-lifecycle, cancellation-elicitation, authentication, tool-calls, plan-commands-config,
  subagents-doc, rfd-subagents, schema.
- Side question from the user: scope of testing the formerly-Active, never-backfilled RFDs (13 rfds/v2/* minus background-work,
  mcp-over-acp beyond part 1, streamable-http-websocket-transport). 4 scope researchers running ->
  .agents/research/scope-rfds-{v2-prompt-session,v2-updates,v2-tools-plan,mcp-transport}.md. All are Draft at target.
## Open questions (waiting on the user)
