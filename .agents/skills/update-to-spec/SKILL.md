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
- each RFD's stage at the base and at the target, the stage moves, and the tracked RFDs (see below) with whether
  each changed in `<base>..<target>`;
- a one-line summary per changed area.

**Tracked RFDs** ([policy](../../../docs/spec-updates.md#tracked-rfds)):

- **Stage:** the nearest enclosing sidebar group in the spec repo's `docs/docs.json` whose name is a stage (Draft,
  Active, Preview, Completed). RFDs nested under Active, such as the `rfds/v2/*` pages in "Active > v2", are Active,
  and tracked for v2 only.
- **Tracked:** RFDs that are Active or Preview at the target, which includes those that moved from Draft into
  Active or Preview within the range. Each is an affected doc in its own right.
- **Never tracked:** Completed RFDs, even ones that moved to Completed within the range (the doc diff covers
  their rules). Draft RFDs are not tracked either: cite them only where nothing else states the rule.
- Keep only those whose wire shapes are in that version's schema (stable or unstable) or that otherwise apply to
  that version.

`spec-impact` reads `docs/docs.json` at both revisions and reports the stage moves, the tracked RFDs, and whether the
version's map records a full RFD audit (`rfd_audit`). A stage move can happen with no change to the `.mdx`, so
the inventory must not rely on the file diff alone.

If the script doesn't exist yet, the researcher produces the same content by hand from
`git diff <base>..<target> -- docs/protocol/v<N> schema/v<N> docs/rfds docs/docs.json` and says so in the report.
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

- **Diff mode** (the default): only the affected docs from step 2 go to step 4. A tracked RFD that changed or moved
  stage is an affected doc.
- **Escalate** a touched core doc: re-check every area that depends on it, not just the hunks.
- **Full audit:** run it when `full` is given, when v2's schema version changes, or when the
  inventory is too broad to reason about piecemeal. Every doc of that version, **and every tracked RFD**, goes to
  step 4.
- **First run under the RFD policy:** if `spec-tracker/maps/v<N>.toml` has no `rfd_audit` key (no prior full RFD
  audit), every tracked RFD goes to step 4 in full, changed or not, whatever the mode. When that audit lands, set
  `rfd_audit = "<target commit>"` in the map.

Tell the user which depth you chose and why before starting step 4.

## 4. Impact research

Run one researcher per affected doc, in parallel; a tracked RFD gets its own researcher, never folded into a doc's.
Each brief contains:

- the doc path at the target revision (and, for an RFD, its stage there);
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

Rules for RFD-sourced requirements (details in [`docs/requirements.md`](../../../docs/requirements.md#tiers)):

- **Docs take precedence.** When the same behaviour or component is documented both in a tracked RFD and in the
  version's draft docs or schema, the docs govern: cite them as the primary source, take the row text and tier from
  them, cite the RFD only as secondary context, and on a conflict follow the docs and record the discrepancy (in the
  row text or the report).
- **Tier cap, for rules stated only in an RFD:** never `MANDATORY`. A MUST is `CAPABILITY` behind a real gate or an
  `inferred:<feature>` gate (the feature has no `initialize` marker); if no gate fits, it is `ADVISORY`. A SHOULD is
  `ADVISORY`.
- Label every RFD citation with the RFD's stage at the pinned revision, e.g. `(Active RFD)`, `(Completed RFD)`.
  For a Completed RFD prefer the docs that absorbed it.

A new deliberate non-requirement must not rest on a TCK choice such as "the TCK never advertises X". If the rule
becomes observable when the TCK changes its own behaviour, make it a row that can SKIP, or a ledger entry marked
"Deferred" with the real blocker. Do not copy a "not observable" reason from the other version's ledger without
re-deriving it: the two versions gate features differently.

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
   latter with `--spec-repo <spec checkout>`). Also refresh the stage labels of the cited RFDs against the
   stage moves in the inventory. No requirement semantics change in this slice.
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
