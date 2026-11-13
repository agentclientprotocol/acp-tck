# acp-tck

A Test Compatibility Kit for the [Agent Client Protocol](https://agentclientprotocol.com) (ACP).
It launches an agent implementation as a stdio subprocess and drives it through the protocol to
check conformance, reporting which requirements pass, fail, are not applicable, or were never
exercised.

- `src/tck/common/` is the version-agnostic core; `src/tck/v1/` and `src/tck/v2/` (Draft) are
  self-contained per-version packages that never import each other.
- `src/tck/v{1,2}/requirements.py` is the source of truth for what each version checks.
- `spec-tracker/` and `cross-check/` are separate uv projects for maintenance tooling; read their
  READMEs before working on them.

## Docs

Read before changing code:

- [`docs/development.md`](docs/development.md): layout, setup, commands, CI, the vendored schema,
  and the plugin-shim footgun. Follow its [conventions](docs/development.md#conventions) (concise
  comments, `uv`-only exact pins).
- [`docs/testing.md`](docs/testing.md): running the repo's tests and how they work. Read before running or
  changing tests.
- [`docs/README.md`](docs/README.md): index of the contributor contracts (requirements, writing
  tests, the mock client, the harness, spec updates). Read the page covering what you change.
- [`README.md`](README.md): running the TCK, its options, and the report.

## Commands

```
uv sync --all-packages                                  # dev setup (plain `uv sync` drops spec-tracker)
uv run pytest                                           # all repo tests (parallel by default)
uv run acp-tck -- python tests/fixtures/agents/v1/conforming.py
uv run acp-tck --protocol-version 2 -- python tests/fixtures/agents/v2/conforming.py
```

## Working files in `.agents/`

Never reference anything under `.agents/` in the final code: not in comments, docstrings,
`Requirement` citations, tests, or scripts. Those files are deleted before the PR merges, so such
a reference would dangle. A temporary reference is fine while the work that needs it is in
progress, but it must be removed or replaced with a permanent upstream citation or plain
explanation by the time that work is done.
