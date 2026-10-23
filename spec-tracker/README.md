# spec-tracker

Maintenance tooling that keeps the TCK aligned with the upstream ACP spec as it changes. It is not
part of the shipped `tck` package.

## Project layout

A uv workspace member of the repo root. It depends on `acp-tck` (for the requirement registries
and pinned `SCHEMA_REVISION`s), never the other way round, and shares the root `uv.lock` and
`.venv`. Run `uv sync --all-packages` for local development: plain `uv sync` is exact and removes
this member from the venv (`uv run --package spec-tracker ...` puts it back).

- `maps/v{1,2}.toml`: the per-version spec maps (below).
- `src/spec_tracker/`: the map loader (`spec_map`), schema pointer and citation helpers
  (`citations`), spec checkout discovery (`spec_repo`), and the `spec-impact` CLI (`impact`).
- `tests/`: unit tests, plus checks of the maps against the spec at the pinned revision.

Add dependencies with `uv add --package spec-tracker ...` (exact `==` pins).

## Spec maps

Each `maps/vN.toml` lists, for one protocol version:

- the core docs whose rules other docs assume without linking to them, optionally narrowed to
  sections (by heading title or `A > B` heading path, with `(intro)` for the text before a
  heading's first child);
- the core schema `$defs`;
- the `code` paths in the TCK that implement each core doc's cross-cutting rules;
- the ledger of deliberate non-requirements (`[[not_requirement]]`).

The file header documents the format. A change to a core doc or `$def` means re-checking every area
that depends on it, not just the changed lines.

## spec-impact

```
uv run --package spec-tracker spec-impact <base> <target> --version vN [--spec-repo PATH] [--fix]
```

Prints a Markdown report of what a spec diff touches: changed files and the sections each hunk
falls in, hits on the map's core docs and `$defs`, the schema `$ref` closure, docs linking to
changed docs, and the requirement ids and ledger entries whose citations fall in a changed region.

With `--fix` it instead remaps the `.mdx` line citations in `src/tck/vN/requirements.py` and
`maps/vN.toml` from base to target line numbers, in place. It is not idempotent, so it refuses
unless `<base>` is the version's pinned `SCHEMA_REVISION`: run it before the pin bump. See the
module docstring for details.

The `/update-to-spec` skill drives a whole spec update with this tool; follow it rather than
refreshing by hand.

## Spec checkout

The spec-doc checks and `spec-impact` read a local clone of the spec repo: `--spec-repo`
(`spec-impact` only), else `$ACP_SPEC_REPO`, else the path in the `check-specification` skill's
`.repo` file. They only read
revisions through git, so the checkout's branch and working tree don't matter.

## Tests and CI

```
uv run --package spec-tracker pytest spec-tracker/tests
```

Locally, a missing spec checkout or revision SKIPs the spec-doc checks. Under CI (`CI=true`) they
fail instead, since a missing checkout means the fetch step broke. The CI `test` job runs these
after the root suite, once it has fetched the spec repo at each pinned `SCHEMA_REVISION` into
`ACP_SPEC_REPO`.
