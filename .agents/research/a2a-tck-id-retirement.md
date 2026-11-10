# How does the A2A TCK handle requirement/test ids when a requirement is removed or changed?

**Sources checked:** `a2a-tck` (a2aproject/a2a-tck, local checkout `/Users/eugene/Documents/JetBrains/projects/a2a-tck`) @ `104a7b4ae0d83f65c075e3793e322953a830eaba` (2026-11-06, "build: require Python 3.15+..."), after `git pull --ff-only` ("Already up to date"). Targets A2A spec v1.0.1 (`specification/version.json:1-8`, commit `3303592`).
**Important limitation:** the local checkout is a shallow clone (6 commits). Per-commit history was therefore read read-only from GitHub with `gh api repos/a2aproject/a2a-tck/commits?path=tck/requirements` (all 35 commits touching `tck/requirements`, 2026-02-12 .. 2026-11-05). I did not unshallow the checkout. Commit SHAs below are 7-char prefixes; each resolves on GitHub.
**Source status:** this is the A2A TCK only. Everything below is design inspiration / prior art, not ACP behavior and not a requirement for this project.
**Confidence:** high for the current id scheme and the three concrete history examples (read from diffs and commit messages). Medium for "no other removals ever happened": I diffed `id="..."` lines in the patches of all 35 commits, which would miss an id defined in some other syntactic form, but the current tree has no id gaps either, which is consistent.

## Answer

The A2A TCK has **no retirement mechanism at all**. Ids are plain string literals in `RequirementSpec(id=...)` entries. The only integrity check is an import-time duplicate-id `ValueError`. When a requirement is removed or changed they simply edit or delete the entry in place, and no tombstone, deprecated status, or retired-id list exists. Their documented policy is only "if a requirement is removed, remove the entry and note it" (the "note it" goes in the commit message or the summary to the user). History shows three behaviors: ids are **renamed wholesale** in a single commit (`CORE-BLOCK` to `CORE-EXECUTION-MODE`, `REST-` to `HTTP_JSON-`), ids are **kept with a changed tier** (`CORE-MULTI-001/002` MUST to MAY, with new letter-suffixed siblings `001a/002a` for the new MUST), and, most relevant to your concern, **one id number was reused for a different requirement** (`AUTH-INTASK-001`). No stated cross-spec-version id-stability policy exists. The current tree has no numbering gaps.

## Requirements (what A2A TCK actually does; not ACP requirements)

| # | Observation | Citation (repo: a2a-tck) |
|---|-------------|--------------------------|
| 1 | Id format is `<AREA>-<SUBAREA>-<NNN>` (3-digit, zero-padded, numbering restarts per `<AREA>-<SUBAREA>`), e.g. `CORE-SEND-001`, `HTTP_JSON-ERR-002`. Prefix to source-file table in CONTRIBUTING; AGENTS.md lists a (stale) prefix summary. | `CONTRIBUTING.md` "Requirement ID conventions" table; `AGENTS.md:46-50`; ids in `tck/requirements/*.py` |
| 2 | Id is a free-form `id: str` field on a dataclass; no regex/format validation. | `tck/requirements/base.py:88-108` (class `RequirementSpec`, `id: str`) |
| 3 | Only registry integrity check: import-time duplicate-id `ValueError`. | `tck/requirements/registry.py:42-48` |
| 4 | Tests bind to an id by passing a string to `compatibility_collector.record(requirement_id, transport, level, passed, errors)`; there is no marker and no pytest-level binding. | `AGENTS.md` "Test Patterns"; `CONTRIBUTING.md` "Transport-specific tests" example |
| 5 | Unknown/orphan ids are tolerated, not rejected: the collector falls back to level `"MUST"`, and the aggregator leaves description/spec_url empty on `KeyError`. | `tests/compatibility/conftest.py:335-340`; `tck/reporting/aggregator.py:139-146` |
| 6 | No retired/deprecated/tombstone concept anywhere (no field, enum, list, doc). `rg -i 'retire\|deprecat\|renumber\|tombstone'` over tracked non-spec files finds nothing about requirement ids. Only unrelated hits (e.g. a protobuf API deprecation, ADR status vocabulary "Deprecated, Superseded" for ADRs, not requirements). | `tck/validators/proto_schema.py:40-54`; `docs/adrs/README.md:25` |
| 7 | Stated removal policy: "If a requirement is removed, remove the entry and note it." Modified: "update the existing entry." Audit step: "No requirements reference sections or content that was removed or renamed." | `.agents/skills/update-a2a-spec/SKILL.md` Step 5 and Step 9 |
| 8 | Older doc (apparently stale; references `check_spec_changes.py`, `tests/mandatory/`, which do not exist in the tree) says "Remove obsolete tests for removed specification features" and classifies "removed requirements" as breaking changes. | `docs/SPEC_UPDATE_WORKFLOW.md:59,80` |

## Details

### 1. Id scheme

- Format `AREA-SUBAREA-NNN`; examples in the current registry: `CORE-SEND-001`, `CORE-MULTI-006`, `PUSH-DELIVER-003`, `AUTH-INTASK-006`, `HTTP_JSON-URL-002`, `BIND-CUSTOM-002`. 129 registered ids (my count of `id="..."` in `tck/requirements/*.py`), spread over 11 files. Areas: CORE, DM, STREAM, PUSH, CARD, AUTH, GRPC, JSONRPC, HTTP_JSON, INTEROP, VER, BIND.
- Defined in `tck/requirements/<area>.py` as `RequirementSpec(...)` entries collected into per-file lists, then concatenated in `ALL_REQUIREMENTS` (`tck/requirements/registry.py:28-40`) with an O(1) lookup `get_requirement_by_id` (`registry.py:~150`).
- The id does not encode the spec section; `section="7.6.1"` is a separate field. So a spec renumbering does not force an id change.
- Doc drift: `AGENTS.md:49` says core ids are `CORE-OPS-*`, but no `CORE-OPS-` id exists (`rg CORE-OPS` hits only that line). Actual core ids are `CORE-SEND/STREAM/GET/LIST/CANCEL/CAP/ERR/HIST/MULTI/EXECUTION-MODE`. Also `CONTRIBUTING.md` examples `CORE-FEAT-001` / `JSONRPC-FEAT-001` and `.agents/skills/learn-requirement/SKILL.md` `HTTP_JSON-REST-001` are illustrative and not real ids.
- The original PRD planned a different scheme (`REQ-3.1.1`, section-derived: `PRD/PRD.md:357,388`), never used; the real registry commit (036889e, 2026-02-26, "Populate requirement registry with 111 specification requirements") already used the area scheme. Backlog task files also mention planned ids that never shipped (`CORE-BLOCK-001/002` as validators, `CARD-REQ-001`, `PUSH-DELETE-001` in `backlog/tasks/task-11.2*.md:39-40` and `task-11.6*.md:25,31`; shipped ids are `CARD-STRUCT-001` / `PUSH-DEL-001`). These are planning-doc drift, silent renames with no alias.

### 2. Concrete examples of removal / change (from git history via GitHub API)

| Commit | Date | What happened to ids | Mechanism |
|--------|------|----------------------|-----------|
| `ce63cb0` "Rename REST- requirement IDs to HTTP_JSON- for consistent terminology" | 2026-03-02 | 16 ids `REST-URL-001/002, REST-SVC-001/002, REST-QP-001, REST-ERR-001/002, REST-SSE-001, ...` renamed to `HTTP_JSON-*` with the same numbers. Old ids not retained. | Pure in-place rename in one commit; one-line commit message, no alias. |
| `dd3f1f6` "update A2A spec to commit dec790a and align TCK" | 2026-03-06 | `CORE-MULTI-001` and `CORE-MULTI-002` **kept their ids** but MUST changed to MAY (the meaning narrowed). The new MUST obligations got **new letter-suffixed ids** `CORE-MULTI-001a` and `CORE-MULTI-002a` (`tck/requirements/core_operations.py:525,547,570,592`). | Id kept, tier edited in place; split-off sibling gets `NNNa` suffix instead of a new number. Commit message documents each (`CORE-MULTI-001: MUST -> MAY`, `001a: new MUST`...). |
| `a8d52e7` "update A2A spec to commit 0833a5f" | 2026-03-12 | `CORE-BLOCK-001/002` deleted and replaced by `CORE-EXECUTION-MODE-001/002` (`core_operations.py:386,413`). Commit message: "Rename CORE-BLOCK requirements to CORE-EXECUTION-MODE" (spec renamed `blocking` to `return_immediately`). | Rename of the area slug, numbers preserved; old ids gone, no alias. |
| `a8d52e7` (same commit) | 2026-03-12 | **Id number reused with a different meaning.** `AUTH-INTASK-001` was "Agent transitions to auth_required state for secondary credentials" (SHOULD, section 7.5). The same commit rewrote that entry in place to "Agent MUST use a Task to track operation requiring authorization" (MUST, section 7.6.1) and added `AUTH-INTASK-002..006` for the other new spec bullets. Commit message: "Replace AUTH-INTASK-001 (SHOULD) with 6 detailed In-Task Authorization requirements (4 MUST, 2 SHOULD)". Diff of `tck/requirements/auth.py` shows the `id="AUTH-INTASK-001"` line as unchanged context, with `section`, `title`, `level`, `description` replaced. Current entry: `tck/requirements/auth.py:85-96`. | In-place overwrite, meaning changed, id unchanged; the old "transitions to auth_required" idea now lives as `AUTH-INTASK-002` (a MUST), so the id-to-meaning mapping shifted for anyone holding old results. |

No commit in the 35-commit history deleted a requirement outright without a successor. Every removal I found was a rename or a rewrite in place.

### 3. Reuse and gaps

- **Reuse:** yes, one clear case (`AUTH-INTASK-001`, above). `CORE-MULTI-001/002` are same-id-changed-tier (semantic narrowing) rather than reuse for something unrelated.
- **Gaps:** none in the current tree. I checked every `AREA-SUBAREA` group (51 groups in the current registry): each is contiguous 1..N, with no duplicates. Because removals are done by rename/overwrite, there is no mechanism that would leave a gap. The letter-suffix ids (`001a`, `002a`) are the only non-numeric ids.
- **Dangling references:** 5 registered ids are never referenced outside `tck/requirements/` (`CORE-MULTI-004`, `CORE-LIST-002`, `AUTH-SCOPE-002/003`, `CORE-CANCEL-003`; probably exercised through the generic parametrized runner, which uses `ids=lambda r: r.id` rather than literal strings, so this is not necessarily an orphan). There is no unit test that cross-checks test-referenced ids against the registry (unit tests under `tests/unit/requirements/` are about expected-error declarations and released-spec bindings only), so a stale id string in a test would not fail the build.

### 4. Stability policy across spec versions

None stated. Searched README, AGENTS, CONTRIBUTING, docs/, ADRs for "stable/stability/reuse/renumber/retire". Nothing about id immutability. De facto practice: ids track the spec's *topic area*, are edited in place when the spec changes (`.agents/skills/update-a2a-spec/SKILL.md` Step 5), and the TCK targets a single spec version at a time (`specification/version.json`; no per-version id sets). Reports are keyed by id (`tck/reporting/aggregator.py`), so id reuse silently corrupts historical comparisons; the A2A TCK does not guard against that.

## Testability notes

Not applicable in the sense of ACP conformance. For this project, the relevant takeaways (A2A TCK-derived design ideas, to weigh against ACP's own marker-based binding and registry meta-tests in `tests/v*/test_registry.py`):

- A2A TCK shows what happens without a retirement mechanism: id reuse (`AUTH-INTASK-001`), silent renames (`REST-` to `HTTP_JSON-`, `CORE-BLOCK` to `CORE-EXECUTION-MODE`), and planning docs that drift from shipped ids, with no check catching any of it.
- Letter-suffix ids (`001a`) are a cheap way to add a sibling obligation next to an existing id without renumbering, at the cost of breaking numeric contiguity assumptions. This is one option, not a recommendation.
- Their tolerance of unknown ids (level fallback `"MUST"` at `tests/compatibility/conftest.py:338-340`) is the opposite of ACP's registry meta-test strictness; ACP's approach (fail if a test references an unregistered id) is stricter and would catch the same drift.
- Whether ACP should keep a retired-id list, forbid reuse via a test, or alias renamed ids is a design decision the A2A TCK gives no precedent for; it never implemented any of them.

## Discrepancies

- `AGENTS.md:49` documents `CORE-OPS-*` ids that do not exist in the registry.
- `docs/SPEC_UPDATE_WORKFLOW.md` describes scripts and directories (`check_spec_changes.py`, `util_scripts/`, `tests/mandatory/`, `current_spec/`) absent from the tree, so it is stale relative to `.agents/skills/update-a2a-spec/SKILL.md`, which is the current workflow.
- The two update docs agree in spirit ("remove obsolete tests/entries") and neither defines id handling.

## Open questions

- Whether upstream A2A discussions (GitHub issues/PRs, e.g. #258, #231, #236) debated id stability: not checked, since the question was narrow and the repo files state no policy. Route to a follow-up if wanted (`gh api` on issues).
- The shallow checkout cannot show pre-2026-09 history locally. If the orchestrator wants reproducible `git log -S` citations, the user would need to approve `git fetch --unshallow` on the A2A checkout. I did not do it.
