# State: build the spec-impact tooling described in .agents/skills/update-to-spec/SKILL.md
## Settings
mode: single · branch: orchestrator-skills · reviews: off
## Decisions (final)
- Per-version `src/tck/v{1,2}/spec_map.toml`: core docs list + ledger of deliberate non-requirements
  (`[[not_requirement]]` with `citation`, `statement`, `reason`), ledger starts empty.
- Registry tests validate spec-map citations/core docs like requirement citations.
- Core docs list: chosen by a researcher per version (reports below), not hand-picked.
- Script: `scripts/spec-impact.py <base> <target> --version vN [--spec-repo PATH] [--fix]`, stdlib only.
## Plan
- M1 spec maps: S1 spec_map.toml x2 + loader + registry-test checks.
- M2 script: S2 report mode (+ tests on a synthetic git repo); S3 `--fix` line-citation remap.
  Adjust update-to-spec/SKILL.md if the interface differs.
## Done
## Next
- Researchers: core docs v1 → .agents/research/core-docs-v1.md; v2 → .agents/research/core-docs-v2.md
- Then S1.
## Open questions (waiting on the user)
