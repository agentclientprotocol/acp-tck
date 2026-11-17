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
## Done
## Next
- Step 2: change inventory, one researcher per version -> .agents/research/spec-diff-v{1,2}.md
## Open questions (waiting on the user)
