# Orchestrator prompt: switch v2 verification to the draft (unstable) schema

You are the orchestrator. Do not do concrete task work yourself -- delegate research to
`researcher` subagents and code changes to `programmer` subagents (don't override their model
param). Your job: plan, brief, review results, integrate, and keep the user informed.

## Goal

ACP v2 is still Draft as a whole, yet `src/tck/v2/` validates agent traffic against the vendored
"stable" v2 schema (`src/tck/v2/schema/schema.json` + `meta.json`), using `schema.unstable.json`
only for the unknown-root-key check (`tck.v2.validation.find_unknown_root_keys`). Switch *all* v2
verification to the latest draft schema (`schema.unstable.json`, and likely `meta.unstable.json`),
remove the stable schema from v2, and document the choice (VENDORED.md, CLAUDE.md, requirement
text/citations, docs).

Working hypothesis to verify, not assume: this needs no rewrite of existing v2 checking logic --
only dropping the stable schema and adjusting loaders, requirement wording, docs, and a few tests
(e.g. the now-redundant unstable root-key carve-out and its self-tests).

## Process

1. Research first: a researcher maps every reference to the stable/unstable split, diffs the two
   schemas (and meta files, and the spec checkout HEAD vs the vendored commit), and assesses
   impact on requirements, fixtures, tests, and the cross-check baseline. Report to the user with
   findings + proposed slices + open questions *before* any implementation.
2. After user approval: implement in programmer-sized slices on the feature branch
   `eugenethedev/v2-draft` (the user created it; it's the main branch for this feature). Each
   slice must leave `uv run pytest` green.
3. Update `docs/cross-check.md` only if upstream-agent results actually change.

## Rules

- Keep `.agents/state.md` updated after every turn; keep it short (current phase, decisions,
  open questions, next step) so an orchestrator restart can resume from it.
- Intermediate findings may go in `.agents/research/*.md`, but never reference research docs in
  code, comments, or docs -- they're deleted when the feature is done.
- Follow CLAUDE.md conventions (concise comments, `uv` only, don't hand-edit vendored JSON).
