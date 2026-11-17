# Impact research (v2): `overview.mdx` and `error.mdx`, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read with
`git show 3ea94133:<path>`; the checkout's HEAD is `6ace4f6a`, which differs from the target only in
`schema.mdx`/`tool-calls.mdx`), base `3961af94`. Files: `docs/protocol/v2/draft/overview.mdx`,
`docs/protocol/v2/draft/error.mdx` (whole docs, both revisions), `docs/protocol/v2/draft/subagents.mdx`
(Restricted methods, Configuration), `docs/protocol/v2/draft/session-config-options.mdx:482-576`,
`docs/rfds/subagents.mdx:1080-1100,1697` (Preview RFD), `docs/protocol/v1/draft/subagents.mdx:428`,
`docs/protocol/v1/draft/error.mdx:57`, `schema/v2/schema{,.unstable}.json`, `docs/docs.json` (stages).
TCK: `src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`, `src/tck/v2/conformance/test_errors.py`,
`test_subagents.py`. Reference SDKs not consulted: every rule below is stated by the docs.
**Confidence:** high for the classification and line maps (mechanical, from the diff); medium for the new
row's probe design (a design choice, see Decisions).

## What changed in the two docs

- `error.mdx`: one paragraph inserted at target lines 58-59 (child sessions are not unknown sessions;
  `-32602` SHOULD for any request naming a child other than the three cancel methods). Base lines >= 58
  shift by +2. Nothing else changed.
- `overview.mdx`: the `session/update` list (target 204-213) adds subagent sessions, unstable prompt
  suggestions and session cursors (listing only, no rule). The Unstable features table (target 257-269)
  adds `Session options` (263, Agent `session.options`), drops the `Subagents` row (now stable: `SubagentUpdate`
  is in v2 `schema.json` at target) and the `Unknown state` row (`UnknownStateUpdate` is in v2 `schema.json`
  at target), and narrows Plan operations to `markdown` plans (`PlanFile` is gone from both v2 schemas).
  Next steps gains a Subagents link (277). Base lines 210-251 shift by +4; table rows map individually.

Line map used below. `overview.mdx`: base <= 203 unchanged; base 218/221-227/233/235 -> 222/225-231/237/239;
table base 255-261 -> 259-262,264-266, base 263/264/266 -> 267/268/269. `error.mdx`: base <= 57 unchanged;
base 60/64/65/66/67/68 -> 62/66/67/68/69/70.

## Table: `docs/protocol/v2/draft/error.mdx`

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
| --- | --- | --- | --- |
| ACP-ERROR-005 | citation-only | `error.mdx:29,62` | `initialization.mdx:90` is another researcher's |
| ACP-INIT-213 | citation-only | `error.mdx:29,62` | idem `initialization.mdx:139` |
| ACP-INIT-215 | citation-only | `error.mdx:29,62` | |
| ACP-JSONRPC-002 | unchanged (error half) | `error.mdx:6-10` | overview half: see other table |
| ACP-JSONRPC-004 | unchanged | `error.mdx:44` | |
| ACP-SESSION-209 | unchanged | `error.mdx:48` | |
| ACP-LIST-205, ACP-LIST-003, ACP-LIST-207 | unchanged | `error.mdx:48` | |
| ACP-CLOSE-204 | unchanged | `error.mdx:54` | |
| ACP-CLOSE-003 | unchanged | `error.mdx:56` | probes closed / never-created ids, never a child, so the new child carve-out does not touch it |
| ACP-DELETE-002 | unchanged | `error.mdx:56` | same as CLOSE-003 |
| ACP-DELETE-205 | unchanged | `error.mdx:54,56` | |
| ACP-ARCHIVE-004 | citation-only | `error.mdx:68` | |
| ACP-ARCHIVE-005 | citation-only | `error.mdx:54,68` | |
| ACP-FORK-202 | unchanged | `error.mdx:54` | session-fork RFD stays Draft |
| ACP-FORK-203 | citation-only | `error.mdx:54,66` | |
| ACP-FORK-204 | citation-only | `error.mdx:66` | |
| ACP-CONFIG-207, ACP-CONFIG-208 | unchanged | `error.mdx:48` | |
| ACP-ENUM-204 | unchanged | `error.mdx:31` | |
| ACP-EXT-203 | unchanged | `error.mdx:44` | |
| ACP-ERROR-001 | unchanged (error half) | `error.mdx:6-10` | |
| ACP-ERROR-003, ACP-ERROR-004 | unchanged | `error.mdx:54-56` | probe nonce ids, not children |
| ACP-ERROR-006 | citation-only (+ optional probe extension, Decision 2) | `error.mdx:44,70` | overview half unchanged (`60,141-142`) |
| ACP-ERROR-008 | unchanged | `error.mdx:38` | |
| ACP-ERROR-204, ACP-INFO-PARSE-001 | unchanged | `error.mdx:28` | |
| ACP-INFO-INVALIDREQ-001 | unchanged | `error.mdx:29` | |
| ledger `error.mdx:38` (unrecognized code = generic failure) | unchanged text; **reason rests partly on a TCK choice** (Decision 3) | `error.mdx:38` | |
| ledger `error.mdx:65; ...` (`session/status`) | citation-only for this doc; **reason rests on a TCK choice** (Decision 4) | `error.mdx:67` | other parts cited (`session-list.mdx:250`, Draft RFD) belong to their researchers |
| ledger `error.mdx:67; ...` (`session/set_title`) | citation-only for this doc; **reason rests on a TCK choice** (Decision 4) | `error.mdx:69` | |

## Table: `docs/protocol/v2/draft/overview.mdx`

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
| --- | --- | --- | --- |
| ACP-CANCEL-205 | citation-only | `overview.mdx:13,151-153,231` | |
| ACP-JSONRPC-001 | citation-only | `overview.mdx:15-17,237` | |
| ACP-JSONRPC-002 | citation-only | `overview.mdx:15-17,229-230` | |
| ACP-JSONRPC-003 | citation-only | `overview.mdx:10,231` | it also cites `docs/rfds/mcp-over-acp.mdx` as "(Active RFD)": now **Draft**; the docs line states the rule, so the MANDATORY tier stands. The label refresh is the mcp-over-acp researcher's |
| ACP-JSONRPC-202 | unchanged | `overview.mdx:15-19` | |
| ACP-JSONRPC-005 | citation-only | `overview.mdx:225-231` | |
| ACP-BATCH-209 | unchanged | `overview.mdx:21` | |
| ACP-LIST-204 | citation-only | `overview.mdx:222` | |
| ACP-EXT-001 | citation-only | `overview.mdx:227` | |
| ACP-ERROR-001 | citation-only | `overview.mdx:227-231` | |
| ACP-ERROR-006 | unchanged (overview half) | `overview.mdx:60,141-142` | |
| ledger `overview.mdx:235` (null = omitted) | citation-only | `overview.mdx:239` | reason ("out of scope as a generic probe") is a scope reason, not a TCK choice; keep |
| ledger `overview.mdx:266; ...` (proxy chains) | citation-only | `overview.mdx:269` | proxy-chains RFD stays Draft; reason stands |

No row or ledger entry cited the removed table rows (base 262 Subagents, 265 Unknown state) or the
`file` plan wording (base 263). Removed requirements: none. Changed text/tier/gate: none.

## New requirements

1. **Provisional `ACP-SUBAGENT-0xx` (shared id with v1; see Decision 1).**
   - Text: "A Client-initiated request that names an announced child session and is not `session/cancel`,
     `tool_call/cancel` or `terminal/cancel` is rejected with `-32602` (SHOULD). The child is not an unknown
     session, so `-32002` is a FAIL, as is a success, which also means `session/close` and `session/delete`
     do not report success for a child."
   - Tier: **ADVISORY** (SHOULD in the docs). Gate: none (ADVISORY rows carry no `capability`); the test
     SKIPs itself when no child is announced. Not RFD-only, so no cap question.
   - Citation: `docs/protocol/v2/draft/error.mdx:58; docs/protocol/v2/draft/subagents.mdx:369,376,379-380;
     docs/rfds/subagents.mdx:1093-1096 (Preview RFD)`.
   - Test approach: its own connection (the shared `_connection_transcript` in `test_subagents.py` closes its
     agent and other rows judge that transcript, so probing on it would perturb them). `session/new`, one prompt
     turn with `--subagent-prompt`, quiet period, then pick the first child announced by `subagent_update` on a
     known session (`subagent_updates` helper). While the root session is still active (no `session/close`;
     `subagents.mdx:379` limits naming a child to that window; after the turn ends is fine and avoids racing
     live child work), send, each with the child's `sessionId`:
     `session/prompt` (text "hi"), `session/resume` (TCK `cwd`), `session/set_config_option` setting an option
     the child reported in `config_option_update` to its **current** value (only when one was reported; any
     other `configId`/value would make `-32602` ambiguous; `subagents.mdx:251` says even the current value is
     not permitted), and `session/close` last (destructive on a non-conforming agent). Judge each reply:
     `-32602` passes; a result, `-32002`, any other error, or no reply FAILs (ADVISORY), with the method named.
     Do not probe `session/delete` unless `capabilities.session.delete` is advertised (otherwise `-32601`
     from ACP-ERROR-006 is the correct answer, and gated-method rules take precedence); do not probe read-only
     methods (Discrepancy 1). If `session/prompt` is wrongly accepted, the test must not wait on that turn.
     SKIP: no child announced. `-32000` SKIPs as in other rows.
   - Harness / mock client: no new behaviour; the child-id bookkeeping exists (`subagent_updates`). Costs one
     more model-driven turn, like `test_subagent_controls.py`'s `_child_run`.
   - Overlap: the subagents-doc researcher sees the same rule at `subagents.mdx:380`. One row, one owner;
     cite both.

No other new agent rule in either doc. The overview's new table row (263) only restates the gate for
`session/options`, whose agent-side consequence is the existing `error.mdx:44` MUST (Decision 2).

## New ledger entries

None proposed from these two docs. (The adjacent `subagents.mdx:380` clause "The Agent ignores a
`session/cancel` for a child that does not advertise `cancel`" is the subagents-doc researcher's; it is
observable, so a SKIPpable row rather than a ledger entry if anyone takes it.)

## Discrepancies

1. **Read-only requests on a child.** `docs/rfds/subagents.mdx:1088-1091` (Preview RFD): "Read-only operations
   retain their normal protocol semantics and capability requirements". The docs say every other request is
   not permitted (`subagents.mdx:376`: "`session/prompt`, ..., and every other request | Not permitted") and
   `error.mdx:58` says "any other request that names a child" gets `-32602`. Docs govern; the proposed probe
   uses only mutating methods so the verdict does not depend on this.
2. **`session/options` unknown session.** The v2 unstable schema
   (`#/$defs/SessionOptionsRequest/properties/sessionId`) says "A session the Agent does not know gets
   `-32002`", but `error.mdx`'s Unstable features list (66-70) does not mention `session/options`, and
   `error.mdx:54`'s "not active on the connection" clause does not fit it (an existing inactive session returns
   what `session/resume` would). For the session-config-options researcher.

## Decisions for the user

1. **Id family for the new child `-32602` row.** The same SHOULD is in v1 (`docs/protocol/v1/draft/error.mdx:57`,
   `docs/protocol/v1/draft/subagents.mdx:428`; the RFD changelog `docs/rfds/subagents.mdx:1697` says "in both
   versions"). Recommendation: one shared `ACP-SUBAGENT-0xx` id (Rule B), owned by the subagents slice, ADVISORY
   in both versions.
2. **Extend ACP-ERROR-006 with `session/options`** (gated on `capabilities.session.options`, now listed at
   `overview.mdx:263`; `session-config-options.mdx:482`). The MANDATORY `-32601` rule (`error.mdx:44`) already
   covers it. Recommendation: yes, add it to `_OTHER_GATED` with `{"cwd": <tck cwd>}` params, if the
   session-config-options slice agrees; otherwise leave ERROR-006 as is (citation-only).
3. **Ledger `error.mdx:38` reason** ends "and the TCK's mock client sends only well-known codes", a TCK choice.
   Recommendation: drop that clause and keep the entry on "how an agent treats an unknown code in a client's
   error reply has no defined wire effect", which is the real reason; optionally mark a Deferred robustness probe
   (mock client answers a `session/request_permission` with an unknown code, agent keeps the connection usable).
4. **Ledger `session/status` (`error.mdx:67`) and `session/set_title` (`error.mdx:69`) entries** are "Deferred"
   with the blocker "not yet tested", a TCK choice. Their `-32002` halves are observable behind
   `capabilities.session.status` / `capabilities.session.title`, and `error.mdx:54`'s MUST applies (CAPABILITY).
   Pre-existing, not caused by this diff. Recommendation: keep them for this update with only the line refresh,
   and record a follow-up to turn the `-32002` halves into SKIPpable CAPABILITY rows.
