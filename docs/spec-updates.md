# Updating to a new spec revision

The contract for bringing the TCK in line with a newer ACP spec. The `/update-to-spec` skill drives a whole update
as an orchestrated run; follow it rather than refreshing by hand. This page says what each step must achieve.
The tooling is documented in [`spec-tracker/README.md`](../spec-tracker/README.md) (spec maps, `spec-impact`) and
[`cross-check/README.md`](../cross-check/README.md) (upstream agent baselines); this page does not repeat them.

## Shape of an update

1. **Scope.** Which versions (`v1`, `v2`, or both), the target spec ref, and the base, which is the commit pinned in
   `src/tck/v{1,2}/schema/VENDORED.md`. Same base and target means there is nothing to do.
2. **Change inventory**, per version: the `spec-impact` report for base..target (changed docs and `$defs`, the
   `$ref` closure of each changed `$def`, docs that link to changed sections, requirement ids and ledger entries
   whose citations fall inside a change, and core docs touched), plus the matching changelog entries and RFD status
   changes. The inventory also records each RFD's stage at the base and at the target, and lists the
   [tracked RFDs](#tracked-rfds) with which of them changed or moved stage.
3. **Depth.** A diff alone misses behavior that changes transitively, such as a core rule that other docs assume
   without linking to it. Default to diff mode: only the affected docs go on to impact research. Escalate when a core
   doc changes (re-check every area that depends on it, not just the hunks). Run a full audit (every doc of that
   version) when asked, when v2's schema version changes, or when the inventory is too broad to reason about
   piecemeal. Tracked RFDs belong to the affected docs in diff mode when they changed or moved stage, and to every full audit.
4. **Impact research**, per affected doc (a tracked RFD is a doc in its own right): read the whole doc at the target, plus the docs it relies on, and classify
   each requirement as unchanged, citation-only change, changed text/tier/gate, removed, new, or new deliberate
   non-requirement. Consult the reference SDKs only where a requirement relies on runtime behavior the spec leaves
   implicit.
5. **Plan.** The requirement changes (add, change, retier, remove, ledger additions) and the slice plan. Tier choices
   and removals are decisions: get them confirmed before implementing.
6. **Slices**, in this order:
   1. [re-vendor](#re-vendor), first and alone;
   2. one slice per area (registry rows, tests, fixtures, `test_cli.py` expectations, ledger additions);
   3. the [final id-alignment step](#id-alignment);
   4. the [cross-check refresh](#cross-check-refresh).

Id handling follows [requirements.md](requirements.md#lifecycle): removals are deletions, and an area slice that
adds a row picks a provisional number that the id-alignment step settles.

## Tracked RFDs

Besides the protocol docs, a spec update tracks RFDs that already govern agent behaviour.

**Stage.** An RFD's stage is the nearest enclosing sidebar group in the spec repo's `docs/docs.json` whose name is a
stage: Draft, Active, Preview or Completed. RFDs nested under Active, such as the `rfds/v2/*` pages in
"Active > v2", are Active, and tracked for v2 only.

**Tracked set:**

- tracked: RFDs that are Active or Preview at the target, which includes those that moved from Draft into Active or
  Preview within the update range;
- never tracked: Completed RFDs, even ones that moved to Completed within the range, because the doc diff covers
  their rules;
- only those whose wire shapes are in that version's schema (stable or unstable), or that apply to that version.

The inventory records each RFD's stage at the base and at the target, so a move made only in `docs/docs.json` is
seen. `spec-impact` reads both and reports the stage moves and the tracked RFDs.

**Handling.** A tracked RFD gets its own impact researcher when it changed or moved stage (diff mode) and is part of
every full audit, with nearly the weight of a doc.

- **Docs take precedence.** When the same behaviour or component is documented both in a tracked RFD and in the
  version's draft docs or schema, the docs govern: the row cites them as the primary source and takes its text and
  tier from them, the RFD is secondary context, and on a conflict the docs win and the discrepancy is recorded. See
  [requirements.md](requirements.md#tiers).
- **Tier cap.** A rule stated only in an RFD is never `MANDATORY`: a MUST is `CAPABILITY` behind a real or
  `inferred:` gate (`ADVISORY` if no gate fits), a SHOULD is `ADVISORY`.
- **First run.** The first update under this policy audits every tracked RFD in full once, changed or not, because
  RFDs that changed earlier were never audited. The spec map's `rfd_audit` key (`spec-tracker/maps/v<N>.toml`) holds
  the spec commit of the last full RFD audit; while it is missing, audit them all. Set it when that audit lands.

Draft RFDs keep the old handling: cite one only where nothing else states the rule.

Each researcher also checks that no ledger `reason` rests on a TCK choice ([ledger rules](requirements.md#the-ledger-of-deliberate-non-requirements)).

## Re-vendor

First and alone: this slice changes no requirement semantics.

1. **Remap citations first, with the pin still at the old revision.**
   `uv run --package spec-tracker spec-impact <old-pin> <new-pin> --version vN --spec-repo <spec checkout> --fix`
   rewrites the `.mdx` line numbers in `requirements.py` and `spec-tracker/maps/vN.toml` in place (line numbers
   only, never the pin) and prints "Needs review" first, listing citations inside changed regions that it left as
   written. It is not idempotent and refuses unless `<old-pin>` equals the current `SCHEMA_REVISION`, so bumping the
   pin first blocks it. Fix the "Needs review" citations by hand against the new text.
2. **Vendor** the schema per `src/tck/v{1,2}/schema/VENDORED.md`: copy the two `.unstable.json` files, update the
   commit and date there, and update `SCHEMA_REVISION` in `src/tck/v{1,2}/protocol.py`. Do not hand-edit the vendored
   JSON.
3. **Fix what the checks flag.** Run `tests/v{1,2}/test_registry.py` and `tests/v{1,2}/test_validation.py`
   (a changed schema shape, or a hand-written carve-out in a `validation.py` docstring that a refresh could
   invalidate). Run the spec-tracker tests with `--spec-repo <spec checkout>`; without it the spec-doc checks skip.
   Schema pointers into renamed or removed `$defs` fail the registry test.
4. **Refresh RFD stage labels.** For every RFD citation in `requirements.py` and the maps, compare its `(<Stage> RFD)`
   label with the RFD's stage at the new pin (the `spec-impact` stage moves list them) and correct it. A cited RFD
   that moved to Completed is relabelled `(Completed RFD)`; re-check whether the docs now state its rule and, if so,
   move the docs citation first.

## Ledger step

Within each area slice, add ledger entries for newly seen agent-side rules the TCK deliberately does not test, and
delete the entry for any rule that became a requirement. The entry rules are in
[requirements.md](requirements.md#the-ledger-of-deliberate-non-requirements).

## Id alignment

After all area slices, and before the cross-check refresh, run a final id-alignment step. It keeps rule B true
after area slices that picked provisional numbers independently per version.

1. **Inventory, read-only.** List every v2 `2xx` row against the v1 registry, and every shared id, with the reason
   they are the same rule ("same rule because ..."). Propose renames: a `2xx` row that restates a v1 rule takes the
   v1 id; a shared id that no longer means the same rule is split.
2. **The user approves each rename.** Borderline pairs are the user's call.
3. **Apply the renames everywhere:** both registries, test markers, the id sets in `tests/v{1,2}/test_cli.py` and
   `test_registry.py`, fixture docstrings, prose mentions in code and tests, the `--expect` lines in
   `cross-check/run.sh`, and the mirrored lines in `.github/workflows/ci.yml`. Re-run the blast-radius grep
   afterwards, once the last area slice has landed.

Never renumber unaffected rows to close gaps.

## Cross-check refresh

Last, because a changed requirement set can move what the upstream agents score.

- To bump an upstream SDK, follow "SDK pins" in `cross-check/README.md`: edit `cross-check/sdk-pins.sh` (the SHA is
  what the release tag points at), `uv add --project cross-check agent-client-protocol==<tag>` for Python, then
  re-run.
- Run `cross-check/run.sh` and re-observe each agent's MANDATORY FAILs. Update the `--expect` / `--expect-flaky`
  lines in `cross-check/run.sh` and the mirrored lines in `.github/workflows/ci.yml` from what you saw, and say
  why each id moved.
- **Never bake a suspected TCK false positive into `--expect`.** If an upstream agent fails a row you believe it
  should pass, investigate against the spec first: fix the TCK, or record the deliberate known limitation with its
  explanation above the `--expect` lines. A baseline that hides a TCK bug defeats the check.

Then run the full suites (`uv run pytest`, the spec-tracker tests, the cross-check tests) before finishing.
