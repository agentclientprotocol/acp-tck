# Requirements

Every conformance assertion is backed by one `Requirement` in a version's registry
(`src/tck/v1/requirements.py`, `src/tck/v2/requirements.py`). The registry is the source of truth for what each
version covers; this page is the contract for how rows are named, tiered, cited and counted. To add a row and its
test, see [writing-tests.md](writing-tests.md).

## Ids

An id is `ACP-<AREA>-<NNN>`, for example `ACP-SESSION-001`. Each version has its own registry and its own set of
tests, so the same id can exist in both.

### Rule B: a shared id is a shared rule

- An id that exists in both v1 and v2 means the **same protocol rule**. Tier and capability gate are per version
  (v2's `capabilities.*` object markers differ from v1's `agentCapabilities.*` flags), so one id can carry a
  different tier or gate in each registry.
- A `2xx` number is a v2 rule with no v1 counterpart.
- A changed tier does not need a fresh id. Change the tier in place; the rule is the same.
- If v2 judges a narrower or different rule than v1 on the same topic, it gets its own id (a `2xx` number),
  not a shared one.

### Lifecycle

There is no retirement mechanism and no list of retired ids.

- When a spec change removes a requirement, delete its registry row, its test, its marker and its fixture
  expectations (`test_cli.py` id sets, fixture docstrings). Nothing is left behind.
- A removed number may be reused later for a new requirement **in the same area**, subject to two guards:
  1. Never reuse a number in the same change that freed it. A reader comparing the before and after of one
     change must never see an id whose meaning silently flipped.
  2. Never reuse a number in a way that breaks rule B (for example, a number that v1 still uses for a different
     rule).
- Ids are stable within a release. To compare across releases, compare rows by text, not by id.
- Never renumber unaffected rows to close gaps. An existing row changes id only when rule B demands it, and that
  happens in the id-alignment step of a spec update ([spec-updates.md](spec-updates.md)).

## Tiers

`tck.common.requirements.Tier`, shared by all versions:

| Tier | Meaning | Effect on the verdict |
| --- | --- | --- |
| `MANDATORY` | A spec MUST. | A FAIL or NOT_TESTED makes the run non-conformant. |
| `CAPABILITY` | Applies only when the agent advertises the capability in `initialize`; the row names the path in `capability`. | A FAIL makes the run non-conformant. SKIPPED (not advertised) and NOT_TESTED do not. |
| `ADVISORY` | A spec SHOULD. | Reported, never affects the verdict. |
| `INFORMATIONAL` | The spec is silent, or reference implementations disagree. The test records what it saw and asserts nothing about it. | Reported, never affects the verdict. |

`capability` is set if and only if the tier is `CAPABILITY`.

## Statuses

`tck.common.report.Status`: `PASS`, `FAIL`, `SKIPPED`, `NOT_TESTED`.

- A test produces `PASS`, `FAIL` or `SKIPPED`. A test that errors (setup or teardown exception, or an
  `AgentExited`/`AgentTimeout` propagating out) is `FAIL`; there is no separate error status.
- `NOT_TESTED` is only ever the aggregated status of a registered id that no test bound to during the run.
- Several tests bound to one requirement aggregate as: any FAIL wins; else any PASS; else any SKIPPED; no records
  is NOT_TESTED.

## Verdict

`Verdict.conformant` is true if and only if all of these hold:

- no `MANDATORY` row is FAIL or NOT_TESTED;
- no `CAPABILITY` row is FAIL;
- `blocked_by_auth` is false;
- `blocked_by_version_mismatch` is false.

`ADVISORY` and `INFORMATIONAL` rows never affect it.

The two block flags exist so that a run that never exercised its requirements cannot score as conformant:

- `blocked_by_auth` is set when any test SKIPs with a message containing `AUTH-GATED:`: the agent requires
  authentication before `session/new` and no `--auth-method` was given, or an embedded login never answered.
- `blocked_by_version_mismatch` is set when any test SKIPs with a message containing `VERSION-MISMATCH:`: the
  agent negotiated a different protocol version than the run targets, or rejected `initialize` with `-32022`.
  It fires in both directions (a v1-only agent under `--protocol-version 2`, a v2-only agent under v1).

See [writing-tests.md](writing-tests.md#skip-or-fail) for when a test may SKIP with each marker.

`--report-json PATH` writes the full run: `tck_version`, `protocol_version`, `schema_revision`, `agent_command`,
`agent_info`/`agent_capabilities`, timestamps, `requirements` (one entry per registry id with tier, capability,
text, citation and every bound test's outcome; FAIL outcomes carry a capped transcript) and `verdict`
(`conformant`, `blocked_by_auth`, `blocked_by_version_mismatch`, `tier_counts`). The exact aggregation rules are
in `src/tck/common/report.py` and `tests/common/test_report.py`.

## Citations

Every row cites the upstream spec that backs it and ends with `@ <spec commit>` (added by the version's `_cite`
helper from its `SCHEMA_REVISION`). Take the rule from the spec text, not from memory of the protocol.

- **Prose:** `docs/protocol/v1/draft/<doc>.mdx:<line>` or `docs/protocol/v2/draft/<doc>.mdx:<line>`, line numbers
  or ranges in the spec repo at the pinned commit. Always the draft tree, which pairs with the draft schema.
- **Schema:** a JSON Pointer by name path, `schema/v1/schema.unstable.json#/$defs/Name` (or `schema/v2/...`),
  never a line number.
- **Draft RFDs** (`docs/rfds/<name>.mdx:<line>`): only where nothing else states the rule. Label the citation
  `(Draft RFD)` in the row text and in any failure message that relies on it, because an RFD is a proposal.

`tests/v1/test_registry.py` and `tests/v2/test_registry.py` check that every citation carries the pinned spec
commit, that every schema pointer resolves in the vendored schema, and that no citation points outside the draft
tree or at the stable schema files. Line citations are re-mapped on a spec update; see
[spec-updates.md](spec-updates.md).

## The ledger of deliberate non-requirements

`spec-tracker/maps/v1.toml` and `v2.toml` each hold a ledger of spec rules the TCK deliberately does not test, one
`[[not_requirement]]` table per rule. The file header documents the format, and `spec-tracker/README.md`
describes the tooling. The ledger exists so that a spec update can tell "not covered on purpose" from "missed".

- **Agent-side only.** Record rules that bind the agent and that the TCK chooses not to test (unobservable from a
  client, unsafe, out of scope). Leave out rules that bind clients, intermediaries or UIs, and pure MAYs.
- **Cited, not inferred.** Each entry's `statement` restates the cited text in one sentence, and its `citation` has
  the same form as a requirement citation. Do not record a rule the spec does not state.
- `reason` says why the TCK does not test it.
- If a rule later becomes a requirement, add the row and delete its ledger entry in the same change.
