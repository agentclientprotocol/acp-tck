# Must an archive-capable v1 agent support all three `archived` filter values?

**Sources checked:** agent-client-protocol (checkout `../agent-client-protocol-2`) @ 3961af94fa62d2386d993cadf1afc8b146fc799a (2026-11-10), read with `git show`. I did not run `git pull`, because the brief pins this revision. Rust and Python SDKs were not consulted: the spec text is sufficient.
**Confidence:** medium-high. The RFD states the rule outright. The normative doc and the schema do not, so the rule is stated outright only in the RFD (a Draft proposal).

## Answer

Ambiguous in the normative docs, clear in the RFD.

- The RFD (a Draft proposal) says: "Agents that advertise `archive` **MUST** support all three values."
- `session-list.mdx` and the schema never say this. They say an agent MUST reject a value "they don't support" with `-32602`.
- The `-32602` sentence has a clear job even if all three are mandatory. It covers the open enum's "other" values: `_`-prefixed extensions and future ACP values.
- The doc does say that advertising `archive` means the agent supports "the `archived` filter on `session/list`". That implies the whole filter, but it does not name the three values.
- There is no text anywhere that allows a subset. Neither the docs nor the schema contain a "may support only some values" statement, and the RFD forbids it.

`session-list.mdx:252` therefore most plausibly refers to values outside `exclude`, `include` and `only`. That reading is an inference, not a quoted statement.

## Requirements

| # | Requirement | Tier | Citation |
|---|---|---|---|
| 1 | An archive-capable agent supports all three values `exclude` (also the default), `include` and `only`. | MUST per the RFD only. The normative doc is silent on the exact set, so treat it as capability:archive, MUST-ish (see recommendation). | agent-client-protocol `docs/rfds/session-archive.mdx:112` (RFD, a Draft proposal) |
| 2 | An agent MUST reject an archived-filter value it does not support with `-32602`, and must not fall back to `exclude`. | MUST, capability:archive | `docs/protocol/v1/draft/session-list.mdx:252`; `schema/v1/schema.unstable.json:7370` (`SessionArchiveFilter` description); `docs/protocol/v1/draft/error.mdx:67` |
| 3 | `sessionCapabilities.archive` means the agent supports `session/archive`, `session/unarchive`, the `archived` filter on `session/list`, and `archived` on each listed session. | capability:archive | `session-list.mdx:229`; `schema/v1/schema.unstable.json:2826`, `:3002` |
| 4 | Deleted sessions are excluded from every filter value. | capability:archive (also needs `delete`) | `session-list.mdx:261`; RFD `:178` |

## Details (exact quotes)

- `docs/protocol/v1/draft/session-list.mdx:229`: "Agents that advertise `sessionCapabilities.archive` support `session/archive`, `session/unarchive`, the `archived` filter on `session/list`, and `archived` on each listed session."
- `session-list.mdx:244-250`: "The `archived` filter on `session/list` selects sessions by archive state:". This is followed by a table that maps "Omitted, `null`, or `exclude`" to only sessions not archived, `include` to archived and not archived, and `only` to only archived sessions.
- `session-list.mdx:252`: "Agents **MUST** reject a value they don't support with `-32602` rather than falling back to `exclude`. The filter combines with `cwd` and applies before pagination. Clients keep the same `cwd` and `archived` values when following `nextCursor`."
- `session-list.mdx:261`: "Deleted sessions are excluded from every filter value, and unarchiving does not restore them."
- `docs/protocol/v1/draft/error.mdx:67`: "An `archived` filter value the Agent does not support gets `-32602`." It uses the same wording as `session-list.mdx:252` and adds nothing.
- `schema/v1/schema.unstable.json:7348-7358` is the `ListSessionsRequest.archived` field. It is `anyOf [SessionArchiveFilter, null]`. The description says: "Omitted and `null` are equivalent and mean `exclude`."
- `schema/v1/schema.unstable.json:7369-7392` is `SessionArchiveFilter`. The description says: "Unknown values are preserved so they can be stored, proxied, or forwarded. An Agent MUST return `-32602` for a value it does not support rather than treating it as `exclude`."
  - The `anyOf` has the const strings `exclude`, `include` and `only`, plus a fourth "other" branch.
  - The "other" branch is a plain `string`, described as: "Custom or future archive filter. Values beginning with `_` are reserved for implementation-specific extensions. Unknown values that do not begin with `_` are reserved for future ACP variants."
  - So the "unsupported value" language is tied to this open enum.
- `docs/rfds/session-archive.mdx:79` (RFD): "`{}` means the Agent **MUST** support both methods, the `archived` list filter, and archive-state reporting; omission or `null` means unsupported."
- `docs/rfds/session-archive.mdx:112` (RFD): "Agents that advertise `archive` **MUST** support all three values. The filter is an open string enum: ... An Agent rejects any value it does not support with `Invalid params` (`-32602`) rather than falling back to the default, so a Client never silently receives the wrong view."
- `docs/rfds/session-archive.mdx:207` (RFD, rationale): "Native stores differ: Codex lists one side at a time, while others list both together, so Agents need adapter work for at least one of the values either way." This shows the authors knew that some agents find a value awkward, and still chose "MUST support all three".
- RFD status: the RFD is listed under the "Draft" group in `docs/docs.json:197-207`. It was last revised on 2026-10-30 (`docs/rfds/session-archive.mdx:225`). It is a proposal, not an accepted requirement.
- Where the feature is gated: the v1 doc heading is "Archived sessions (unstable)" (`session-list.mdx:227`), and the schema marks every archive item **UNSTABLE**.

## Testability notes

- Both ARCHIVE-003 and ARCHIVE-006 can be observed from the client side. The conforming result is a list response under each of `exclude`, `include` and `only`. A non-conforming agent returns `-32602` for `include` or `only`, or silently treats an unsupported value as `exclude`.
- ARCHIVE-004 reading: send a probe such as `_tck_unknown` or a non-`_` unknown string, and expect `-32602`.
  - This works under either reading of :252, because an unknown value is certainly "unsupported".
  - Do not use `include` or `only` as the probe, since the RFD says an archive-capable agent supports them.

## Discrepancies

- RFD says all three are MUST (`docs/rfds/session-archive.mdx:112`). `session-list.mdx:252` and the schema description at `:7370` say only "a value they don't support". The doc and schema never repeat the RFD sentence.
- This is a gap in the normative text, not a flat contradiction. A reasonable agent author could read "a value they don't support" as permitting a subset. The RFD says that reading is wrong.
- `session-list.mdx:229` and the schema capability description at `:2826`/`:3002` only say that the filter is supported. They do not enumerate the values.

## Recommendation for ARCHIVE-003 / ARCHIVE-006

- Keep the strict reading as a FAIL for a rejection of `include` or `only` with `-32602`, unless the project has already decided to follow the normative doc only. Reasons:
  - The only explicit statement is the RFD's MUST.
  - Nothing in the doc or schema permits a subset.
  - A real agent that rejects `include` or `only` is the failure mode the RFD's MUST was written to prevent.
  - SKIP would hide it.
- Make the failure message cite the RFD (`docs/rfds/session-archive.mdx:112`) and say it is a Draft proposal.
- If the orchestrator wants the most cautious posture, the alternative is to SKIP only when `include` or `only` returns `-32602`, with a reason like "agent rejects an archived filter value; RFD requires all three, normative doc is silent". That would be a downgrade of strictness to hedge on the Draft status. I do not recommend it as the default, but it is defensible because the RFD is not normative.
- Registry citation: cite `session-list.mdx:229` and `:244-252` for the filter, and treat the RFD sentence as the backing for "all three". The RFD is a Draft proposal, so also consider ADVISORY or CAPABILITY rather than MANDATORY tiering.

## Open questions

- Should `docs/protocol/v1/draft/session-list.mdx` say outright that all three values are required? That is an upstream clarification issue, not a TCK question.
- Does the v2 draft doc (`docs/protocol/v2/draft/`) state it more clearly? I did not check this; v2 was out of scope.
