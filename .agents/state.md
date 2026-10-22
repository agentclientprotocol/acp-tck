# State: build the spec-impact tooling described in .agents/skills/update-to-spec/SKILL.md
## Settings
mode: single · branch: orchestrator-skills · reviews: off
## Decisions (final)
- Per-version `src/tck/v{1,2}/spec_map.toml`: core docs list + ledger of deliberate non-requirements
  (`[[not_requirement]]` with `citation`, `statement`, `reason`), ledger starts empty.
- Registry tests validate spec-map citations/core docs like requirement citations.
- Core docs: from `.agents/research/core-docs-v{1,2}.md` recommendations, section-scoped where they
  recommend it; `error.mdx` is core in NEITHER version.
- Core entries: doc + optional `sections` (heading titles; whole doc when omitted) + optional `code`
  (TCK paths implementing the cross-cutting rule; registry test checks they exist).
- Core schema `$defs` list per version also escalates: ErrorCode, SessionUpdate, ContentBlock,
  AgentCapabilities, ClientCapabilities (only those present in that version's schema).
- Script must normalize stable-tree links (`/protocol/v1/<page>`) to the draft tree, and remap
  `schema.mdx` line citations too.
- Script: `scripts/spec-impact.py <base> <target> --version vN [--spec-repo PATH] [--fix]`, stdlib only.
## Plan
- M1 spec maps: S1 spec_map.toml x2 + loader + registry-test checks.
- M2 script: S2 report mode (+ tests on a synthetic git repo); S3 `--fix` line-citation remap.
  Adjust update-to-spec/SKILL.md if the interface differs.
## Done
- Core-docs research — 4a9df3c — reports core-docs-v1.md, core-docs-v2.md
## Next
- S1 (programmer running).
## Open questions (waiting on the user)
