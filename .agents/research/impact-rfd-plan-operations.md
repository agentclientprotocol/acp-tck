# Impact: tracked RFD `docs/rfds/plan-operations.mdx` (full audit, v1 and v2)

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (target) and diff
`3961af94..3ea94133`, read with `git show 3ea94133:<path>` (the working tree is at `6ace4f6a`. RFD and both
`agent-plan.mdx` files are identical there, v2 schemas differ only in `DiffContent.changes`). Files:
`docs/rfds/plan-operations.mdx`, `docs/docs.json:242-243`, `docs/protocol/v{1,2}/draft/agent-plan.mdx`,
`docs/protocol/v1/draft/initialization.mdx:172-179`, `docs/protocol/v1/draft/prompt-turn.mdx:24-26`, the plan
`$defs` in `schema/v1/schema.unstable.json`, `schema/v2/schema.unstable.json` and `schema/v2/schema.json`. TCK:
`src/tck/v{1,2}/requirements.py`, `spec-tracker/maps/v{1,2}.toml`, `src/tck/v1/conformance/test_plan.py`,
`test_client_capabilities.py`, `src/tck/v2/protocol.py`, `open_enums.py`, `conformance/test_patches.py`.
I did not check the reference SDKs: no rule here depends on runtime behaviour that the spec leaves implicit.
**Confidence:** high. Every agent-side normative rule in the RFD is also stated in the version's draft docs or
schema, so the docs-precedence rule settles the tiers.

**Stage:** Preview at the target (`docs/docs.json:242-243`, group "Preview"). It was Draft at the base.

## Which wire shapes are in which version

| Shape | v1 | v2 |
|---|---|---|
| `plan_update` / `PlanUpdate`, `PlanUpdateContent`, `PlanItems`, `PlanId` | unstable only | **stable** (baseline, `items` only, plus an open `other` branch) |
| `PlanMarkdown` (`content` required, `path` optional) | unstable. `path`: `string \| null` | unstable. `path`: `AbsolutePath \| null` (`AbsolutePath` is a plain `string` with the description "native syntax ... It is not a URI") |
| `plan_removed` / `PlanRemoved` | unstable only | unstable only |
| `PlanFile` (`type: "file"`, `uri`) | **removed** in this range | **removed** in this range |
| `ClientCapabilities.plan` / `PlanCapabilities` | unstable only. Omitted or `null` both mean not advertised | **absent** (no capability) |
| Unknown plan `type` | closed `oneOf` (`items`, `markdown`). No fallback, so any other value is schema-invalid | open `anyOf` `other` branch (requires `type` and `planId`) |

Required fields are the same in both versions: `PlanItems` `[planId, entries]`, `PlanMarkdown` `[planId, content]`,
`PlanRemoved` `[planId]`.

Gating therefore differs. v1 plan operations depend on a client capability that the TCK controls. v2 has no gate:
markdown and `plan_removed` are simply unstable variants (RFD `:81`, v2 `agent-plan.mdx:73-77`).

## RFD rules at the target and where each is owned

| RFD line(s) | Rule | Binds | v1 | v2 |
|---|---|---|---|---|
| 34 | Every plan variant carries a required `planId`, with optional `_meta` | agent | doc-stated `v1/agent-plan.mdx:55` + schema | doc-stated `v2/agent-plan.mdx:10,58,139` + schema |
| 36, 72 | `plan_removed` carries only `planId` | agent (shape) | doc-stated `:123-137` + schema | doc-stated `:115-129` + schema |
| 38, 48 | v1: send `plan_update`/`plan_removed` only if the Client advertised `plan` (omitted or `null` means not advertised). Otherwise fall back to `plan` "for structured checklists" | agent | doc-stated `:53` (MUST NOT / MUST), `initialization.mdx:176-177`, schema `ClientCapabilities.plan` | n/a (no capability, RFD `:81`) |
| 50 | When `plan` is advertised, Agents SHOULD send plans with `plan_update` | agent | doc-stated `:57` | n/a |
| 56 | Each `plan_update` replaces the whole plan with that `planId`, whatever its `type` | client semantics | doc-stated `:59` | doc-stated `:176` |
| 57 | Clients track plans by ID | client | out of scope | out of scope |
| 58 | `items`: Agent sends the complete list. Empty `entries` empties the plan. Clients MAY hide it | agent / client | doc-stated `:171,173` (MUST) | doc-stated `:178` (MUST) |
| 62 | `content` is required and holds the whole plan | agent | doc-stated `:108` + schema `required` | doc-stated `:100` + schema `required` |
| 64 | `path` MUST be absolute. Omitted and `null` are equivalent | agent | doc-stated `:112-117` | doc-stated `:104-109`, schema `AbsolutePath` |
| 66 | `content` is the plan to display. Clients render it and need not read the file | client | doc-stated `:119` | doc-stated `:111` |
| 68 | `content` is a snapshot. When the plan changes the Agent sends another `plan_update` | agent, no keyword | covered by doc `:169` (SHOULD report updates) | covered by doc `:174` |
| 74 | Agents SHOULD send `plan_removed` when a plan is cancelled | agent | doc-stated `:139` | doc-stated `:131` |
| 75 | Clients MUST ignore `plan_removed` for an unknown `planId` | client | out of scope | out of scope |
| 79 | v1 has no unknown-type fallback. A new v1 plan type needs its own capability | schema / spec design | schema (closed `oneOf`) | n/a |
| 81-83 | v2: markdown and `plan_removed` need no capability. Agents *can* first send `items` with `entries: []` | permission / MAY | n/a | doc-stated `:73-77,133` |
| 103 | Preview does not stabilize the feature. It stays behind `unstable_plan_operations` | context | matches schema | matches schema |
| 196 | `path` is an absolute path, not a URI, like tool-call locations and diffs | interpretation | context for `:117` | context for `:109` (matches `AbsolutePath`) |

Result: the RFD has **no RFD-only agent-side normative rule** in either version. Every rule a TCK row could carry
is doc-stated, so it belongs to the `agent-plan.mdx` researchers. Docs and RFD agree on every rule (see
Discrepancies).

## Classification: existing rows and ledger entries citing the RFD

Only one TCK artefact cites `plan-operations.mdx`. `grep` returns 0 hits in `src/tck/v2/requirements.py`,
`spec-tracker/maps/v1.toml` and `spec-tracker/maps/v2.toml`.

### v1

| id / ledger | classification | target citation | note |
|---|---|---|---|
| `ACP-PLAN-001` (`requirements.py:1520-1534`) | **removed** (from the RFD's side) | none. RFD `:63` "Plan file URIs **MUST** be absolute" was deleted. `PlanFile` and `type: "file"` were deleted from the v1 unstable schema and from `agent-plan.mdx` | The rule's subject no longer exists anywhere. The doc researcher decides whether the row is deleted or reused for the new `path` rule (doc `:117`). If it is reused, the secondary RFD citation becomes `docs/rfds/plan-operations.mdx:64,196 (Preview RFD)`, and `:196` settles "absolute" as a filesystem path, **not** a URI, so `is_absolute_uri` is the wrong check. A `file:///...` value in `path` is non-conforming. |

Other v1 rows do not cite the RFD but implement RFD rules. They are doc-sourced, so they are listed here for
completeness only:

- `ACP-CLIENTCAP-006` (MANDATORY, doc `:10,53`): matches RFD `:38,48`. Optional secondary citation
  `docs/rfds/plan-operations.mdx:38,48 (Preview RFD)`.
- `ACP-PLAN-002` (ADVISORY, doc `:57`): matches RFD `:50`. Optional secondary citation `:50 (Preview RFD)`.
- v1 ledger entries `agent-plan.mdx:179,181` (complete list) and `:147` (`plan_removed` SHOULD) match RFD
  `:58` and `:74`. They are doc-cited and their targets are `:171,173` and `:139`. The doc researcher owns them.

### v2

No rows or ledger entries cite the RFD. These v2 artefacts are related and doc-sourced:

- Ledger `agent-plan.mdx:119` "Plan file URIs MUST be absolute." The rule was removed at the target, in both
  doc and RFD. Its reason ("Deferred: ... a passive check of it is not yet built") rests on a TCK choice, as
  brief step 5 notes, but the entry is going away anyway. The doc researcher owns the deletion and the
  replacement `path` rule (`:109`).
- Ledger `:139` (`plan_removed` SHOULD) moves to `:131`. Ledger `:186` (complete list) moves to `:178`. Both are
  doc-owned.
- `ACP-PATCH-205` (`planId` on every plan, including unknown types) is doc-owned and matches RFD `:34` and v2
  doc `:139`.

## Code impact found during the audit (not a requirement change)

- **v2 `src/tck/v2/protocol.py:113`:** `PLAN_CONTENT_TYPE = frozenset({"items", "file", "markdown"})` still lists
  `"file"`. At the target, `file` is no longer a defined plan type in v2 (unstable or stable). So a v2 agent that
  sends `type: "file"` is sending a non-underscore unknown value, reserved for future ACP variants (v2 doc
  `:137`), and `ACP-ENUM-201` should FAIL it. Today the TCK accepts it. Drop `"file"` in the re-vendor or the
  plan-area slice.
- **v1:** `type: "file"` is now schema-invalid (closed `oneOf`). Several pieces still use it:
  `tests/fixtures/agents/v1/emits_relative_plan_file_uri.py`, `tests/fixtures/agents/v1/plan_turn_never_ends.py`
  (sends `type: "file"`, `uri: file:///tmp/plan.md`), `is_absolute_uri` in
  `src/tck/v1/conformance/_helpers.py:196`, and `tests/v1/test_plan_uri.py`. All of these follow from the
  `ACP-PLAN-001` decision. `plan_turn_never_ends.py` must switch to a valid shape (for example `items` or
  `markdown`) whatever is decided.

## New requirements

None from this RFD, in either version. Every candidate is doc-stated (table above). Do not add RFD-sourced
rows for the `path` rule, `planId`, `content`, the v1 gate, the v1 SHOULD, or `plan_removed`.

For the doc researchers, here is how a `path` row could be observed (it would be doc-sourced, with the RFD as
secondary context only):

- **v1:** on the existing `plan: {}` connection in `test_plan.py`, scan `plan_update` with
  `plan.type == "markdown"` and a non-null `path`, then FAIL unless `is_absolute_path` holds
  (`_helpers.py:903`). The check passes vacuously when no such update appears. It fits the existing
  `ACP-PLAN-*` MANDATORY-with-vacuous-pass pattern.
- **v2:** a passive scan of every `plan_update` during a turn, using `is_absolute_path`
  (`v2/conformance/_helpers.py:770`), alongside `ACP-PATCH-205`/`206`.
- No mock-client or harness changes are needed in either version.

## New ledger entries

None from this RFD. I considered two candidates and rejected both:

- RFD `:68` "`content` is a snapshot. When the plan changes, the Agent sends another `plan_update`". It has no
  RFC 2119 keyword and is covered by the docs' "Updating plans" SHOULD (v1 `:169`, v2 `:174`). Under
  docs-precedence it belongs to the doc ledger or rows if anywhere, not to an RFD entry.
- RFD `:62` "`content` ... holds the whole plan". This is doc-stated in substance (v1 `:59,108`, v2 `:100,176`)
  and the schema enforces `required`. "Whole" is unobservable, but recording it is a doc-researcher call.

## Discrepancies

None of substance. A wording difference: RFD `:38,48` limits the v1 fallback to `plan` to "structured
checklists", and RFD `:114` describes Codex falling back to Agent messages for markdown plans. v1 doc `:53` says
unconditionally "the Agent **MUST** fall back to the existing `plan` update", and `initialization.mdx:176-177`
says the Agent "sends plans with the `plan` update instead". The docs govern. No TCK row tests the positive
fallback, and it is unobservable anyway: the TCK cannot know that the agent had a plan it chose to send as
messages.

## Decisions for the user

1. **`ACP-PLAN-001` (v1).** Its RFD and doc rule and its schema subject are all removed. Recommendation: delete
   the row and its URI fixture, test and helper, and let the agent-plan researcher propose a doc-sourced `path`
   row, either a reused or a new id. If the id is reused, cite `docs/rfds/plan-operations.mdx:64,196 (Preview RFD)`
   as secondary context and check an absolute *filesystem path*, not a URI.
2. **Optional secondary RFD citations** on `ACP-CLIENTCAP-006` (`:38,48`) and `ACP-PLAN-002` (`:50`), labelled
   `(Preview RFD)`. Recommendation: skip them. The docs fully state both rules, and an extra RFD citation only
   adds a line to remap on the next update.
3. **v2 `PLAN_CONTENT_TYPE`:** remove `"file"` (see Code impact). This is a code fix, with no requirement
   change.

## Open questions (route elsewhere)

- No v1 row schema-validates `plan_update`/`plan_removed` payloads on the `plan: {}` connection, because
  `ACP-SCHEMA-001` only covers the basic exchange, which advertises no `plan`. So a markdown plan without
  `content`, a missing `planId`, or a v1 `type: "file"` or `_custom` plan type goes unchecked. Subagents have an
  equivalent shape row (`ACP-SUBAGENT-015`). This is doc- and schema-sourced, so it is for the v1 agent-plan
  researcher.
- v1 doc `:53`, second sentence ("MUST fall back to the existing `plan` update"), is neither a row nor a ledger
  entry. A ledger entry is probably right ("not observable": the TCK cannot know the agent has a plan). This is
  for the v1 agent-plan researcher.
- `ACP-PATCH-205` is gated `capabilities.session`, although plan updates have no such gate in v2. This is
  pre-existing and doc-owned, noted only.
