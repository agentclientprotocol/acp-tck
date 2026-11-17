# Common brief: impact research for the spec update 3961af94 -> 3ea94133

You are one of several impact researchers (step 4 of `.claude/skills/update-to-spec/SKILL.md`; read that
step, `docs/spec-updates.md` and `docs/requirements.md` "Tiers", "Citations" and "The ledger of deliberate
non-requirements" first). Your own prompt names your docs, version(s) and report path.

## Revisions and checkouts
- Base `3961af94fa62d2386d993cadf1afc8b146fc799a` (current pin), target `3ea94133bb4e7cfdb1105df75660ff83e66acf62`.
- Target working tree (read-only): `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`.
- Diffs: `git -C /Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2 diff 3961af94..3ea94133 -- <path>`.
  Never modify either spec checkout. The other checkout (`../agent-client-protocol`) is on an unrelated branch.
- Inventories: `.agents/research/spec-diff-v1.md`, `.agents/research/spec-diff-v2.md` (hunks, `$def` closure,
  link fan-out, affected ids, RFD stages).

## Key facts from the inventory
- Upstream removed the RFD "Active" stage. At the target, the only Active/Preview RFDs are `docs/rfds/subagents.mdx`
  (Preview, was Active) and `docs/rfds/plan-operations.mdx` (Preview, was Draft). Everything formerly Active
  (`rfds/v2/*`, `mcp-over-acp`, `streamable-http-websocket-transport`) is now Draft.
- New draft docs `docs/protocol/v{1,2}/draft/subagents.mdx`: subagents is now documented, so for subagent rules the
  docs govern and the RFD is secondary context (docs-precedence rule). v2 subagents types are now in v2's stable schema.
- v2 schema `2.0.0-alpha.14` -> `2.0.0-alpha.16`. v1 stable `schema.json` unchanged.
- The TCK cites only the `draft/` trees.

## What to do
1. Read the **whole** doc(s) at the target, not just the hunks. Check the rules they depend on in the docs they link
   to and the docs that link to them (the inventory's link fan-out lists these).
2. Collect the registry rows (`src/tck/v<N>/requirements.py`) and ledger entries (`spec-tracker/maps/v<N>.toml`)
   that cite your doc(s); `grep -n '<doc file name>'` finds them. Also look at the tests that implement those rows
   (`src/tck/v<N>/conformance/`) when a changed rule might change what the test must check.
3. Classify every existing requirement and ledger entry citing your doc(s) as one of: unchanged; citation-only change
   (give the new line numbers at the target); changed text, tier or capability gate; removed; and list every **new**
   requirement and every **new deliberate non-requirement** (with its reason) the target text introduces.
4. Apply the tier rules: MUST -> MANDATORY (or CAPABILITY behind the feature's gate), SHOULD -> ADVISORY. RFD-only
   rules are never MANDATORY (CAPABILITY behind a real or `inferred:` gate, else ADVISORY). Label every RFD citation
   with its stage at the target, e.g. `(Preview RFD)`, `(Draft RFD)`. Cite Draft RFDs only where nothing else states
   the rule.
5. A new ledger reason must not rest on a TCK choice ("the TCK never advertises X"). If the rule becomes observable
   when the TCK changes its own behaviour, propose a SKIPpable row, or a ledger entry marked "Deferred" with the real
   blocker. Also flag any **existing** ledger reason citing your doc(s) that rests on a TCK choice. Do not copy a "not
   observable" reason from the other version's ledger without re-deriving it.
6. Consult the reference SDKs (`check-rust-sdk`, `check-python-sdk` skills) only where a requirement relies on
   runtime behaviour the spec leaves implicit, or where the new text is silent or ambiguous.
7. For each proposed new or changed row, say concretely how a test would observe it (which request the TCK sends,
   what it checks, what SKIPs it) and whether the mock client/harness needs new behaviour. Do not write code.

## Report format
- Header: sources checked (revision, files), confidence.
- One table per doc: id or ledger citation | classification | target citation (`path:lines @ 3ea94133`) | note.
- "New requirements" list: proposed area/id family (provisional, e.g. `ACP-OPTIONS-2xx`), text, tier, gate,
  citation, test approach, harness needs.
- "New ledger entries": citation, statement, reason.
- "Decisions for the user": tier choices, removals and ambiguities, each with your recommendation.
- Keep it concise. Your final message: <=12 lines summarising counts (unchanged / citation-only / changed /
  removed / new / new ledger) and the decisions, plus the report path.
