# spec-tracker

Maintenance tooling that keeps the TCK aligned with the upstream ACP spec as it changes. It is not
part of the shipped `tck` package.

A uv workspace member of the repo root: it depends on `acp-tck` (for the requirement registries and
pinned `SCHEMA_REVISION`s), never the other way round, and shares the root `uv.lock` and `.venv`.
Use `uv sync --all-packages` locally; plain `uv sync` removes this member from the venv. Add
dependencies with `uv add --package spec-tracker ...`.

`maps/` holds the spec maps, `src/spec_tracker/` the map loader, citation helpers and the
`spec-impact` CLI, and `tests/` their tests plus checks of the maps against the spec.

Everything that reads the spec takes a local clone of the spec repo as `--spec-repo PATH`, with no
default. It only reads revisions through git, so the clone's branch and working tree don't matter.

## Spec maps

Each `maps/vN.toml` lists the core docs (and sections) whose rules other docs assume without
linking to them, the core schema `$defs`, the TCK code implementing those rules, and a ledger of
deliberate non-requirements. The file header documents the format. A change to a core doc or `$def`
means re-checking every area that depends on it, not just the changed lines.

## spec-impact

```
uv run --package spec-tracker spec-impact <base> <target> --version vN --spec-repo PATH [--fix]
```

Prints a Markdown report of what a spec diff touches: changed files and sections, hits on the
map's core docs and `$defs`, the schema `$ref` closure, docs linking to changed docs, and the
requirement ids and ledger entries whose citations fall in a changed region.

With `--fix` it instead remaps the `.mdx` line citations in `src/tck/vN/requirements.py` and
`maps/vN.toml` from base to target, in place. It is not idempotent, so it refuses unless `<base>`
is the pinned `SCHEMA_REVISION`: run it before the pin bump.

The `/update-to-spec` skill drives a whole spec update with this tool; follow it rather than
refreshing by hand.

## Tests and CI

```
uv run --package spec-tracker pytest spec-tracker/tests --spec-repo PATH
```

Without `--spec-repo`, or when the clone lacks a pinned revision, the spec-doc checks SKIP locally
(check the skip count) and FAIL under `CI=true`. The CI `test` job runs these after the root suite,
against a fetch of each pinned revision.
