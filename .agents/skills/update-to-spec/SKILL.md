---
name: update-to-spec
description: Align the TCK (vendored schema, requirement registry, conformance tests, fixtures, cross-check baselines) with a newer ACP spec revision, as an orchestrated run.
disable-model-invocation: true
argument-hint: "[v1|v2|both] [spec-ref] [full]"
---

# Update to spec

Arguments: $ARGUMENTS

Invoke the `orchestrator` skill with the goal "update the TCK to the spec: $ARGUMENTS", and follow
it for this whole session. This skill adds only the steps that
are specific to a spec update. Everything about delegation, state, git, and finishing comes from
the orchestrator.

## 1. Scope

- **Versions:** `v1`, `v2`, or `both`. If none is given, ask.
- **Target:** the given spec ref. Otherwise use the spec repo's `main` HEAD after the
  `check-specification` refresh.
- **Base:** the commit pinned in `src/tck/v{1,2}/schema/VENDORED.md`. If the base and target are the
  same, say so and stop.
- `full` forces a full audit (see step 3).
- Record the versions, base, target, and depth in `state.md` along with the orchestrator settings.

## 2. Change inventory

Run one researcher (`sonnet`) per version. It writes `.agents/research/spec-diff-v<N>.md`:

- the output of `uv run --package spec-tracker spec-impact <base> <target> --version v<N>
  --spec-repo <spec checkout>`, where the checkout is the `check-specification` skill's;
- the matching `CHANGELOG.md` entries and RFD status changes;
- a one-line summary per changed area.

If the script doesn't exist yet, the researcher produces the same content by hand from
`git diff <base>..<target> -- docs/protocol/v<N> schema/v<N> docs/rfds` and says so in the report.
That content is:

- changed docs and `$defs`;
- the `$ref` closure of each changed `$def` (every definition that reaches it);
- the docs that link to changed sections;
- the requirement ids and ledger entries whose citations fall inside a change;
- the core docs that were touched.

The core docs and the ledger of deliberate non-requirements live in `spec-tracker/maps/v<N>.toml`
(ledger rules: [`docs/requirements.md`](../../../docs/requirements.md#the-ledger-of-deliberate-non-requirements)).

## 3. Depth

A diff alone misses behavior that changes transitively, for example a core rule that other docs
assume without linking to it. So choose the depth from the inventory:

- **Diff mode** (the default): only the affected docs from step 2 go to step 4.
- **Escalate** a touched core doc: re-check every area that depends on it, not just the hunks.
- **Full audit:** run it when `full` is given, when v2's schema version changes, or when the
  inventory is too broad to reason about piecemeal. Every doc of that version goes to step 4.

Tell the user which depth you chose and why before starting step 4.

## 4. Impact research

Run one researcher per affected doc, in parallel. Each brief contains:

- the doc path at the target revision;
- its diff hunks, if any;
- the registry rows and ledger entries that cite it;
- the docs it links to, and the docs that link to it.

The researcher reads the **whole** doc at the target, not just the hunks, and checks the rules the
doc depends on in those linked docs. It reports each requirement as one of:

- unchanged;
- citation-only change;
- changed text, tier, or capability gate;
- removed;
- new;
- new deliberate non-requirement (with its reason).

Consult the reference SDKs only where a requirement relies on runtime behavior the spec leaves
implicit, or where the new spec text is silent or ambiguous.

## 5. Plan

Show the user the requirement changes (add, change, retier, remove, ledger additions) and the
slice plan. Tier choices and removals are decisions: wait for the user's answers.

## 6. Slices

The contract for each slice is in [`docs/spec-updates.md`](../../../docs/spec-updates.md); the id
rules are in [`docs/requirements.md`](../../../docs/requirements.md). Run them in this order:

1. **Re-vendor, first and alone** ([details](../../../docs/spec-updates.md#re-vendor)). Remap the line
   citations with `spec-impact --fix` while the pin is still at the old revision, then re-vendor per
   `VENDORED.md` and fix what `tests/v<N>/test_registry.py` and `spec-tracker/tests/` flag (run the
   latter with `--spec-repo <spec checkout>`). No requirement semantics change in this slice.
2. **One slice per area:** registry rows, conformance tests, fixtures, the `test_cli.py`
   expectations, and the ledger additions for that area. Area slices pick provisional ids; step 3
   settles them.
3. **Final id alignment** ([details](../../../docs/spec-updates.md#id-alignment)), after all area
   slices and before the cross-check refresh. A researcher produces a read-only inventory of every v2
   `2xx` row against v1 and of every shared id, with a proposed rename and "same rule because..." for
   each. **The user approves each rename**; borderline pairs are the user's call. Then a programmer
   applies the renames everywhere: registries, markers, `test_cli.py`/`test_registry.py` sets, fixture
   docstrings, cross-check `--expect`, and `ci.yml`.
4. **Cross-check refresh** ([details](../../../docs/spec-updates.md#cross-check-refresh)): bump the
   SDK pins if needed, re-observe the baselines, and update the `--expect` lines in
   `cross-check/run.sh` and `ci.yml`, saying why each id moved. Never bake a suspected TCK false
   positive into `--expect`.

Then finish as the orchestrator skill says.
