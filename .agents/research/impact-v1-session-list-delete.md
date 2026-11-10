# v1 impact: `session-list.mdx`, `session-delete.mdx`, and the new unstable session methods (`session/archive`, `session/unarchive`, `session/set_title`, `session/status`)

**Sources checked:** agent-client-protocol (worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`) base `beac4ba96190` -> target `3961af94fa62` (read via `git show`/`git diff`, checkout not modified); rust-sdk @ `e75d6f19fabb` (2026-11-09); python-sdk @ `8a9940744d0a` (2026-11-09, schema tag `schema-v1.23.0`). TCK registry/tests at branch `eugenethedev/update-spec` (HEAD `200baba`).
**Confidence:** high for the classification of existing rows (the text changes are small and line-checked); medium for the proposed new rows (tier choices for unkeyworded or RFD-only statements are judgment calls, marked DECISION NEEDED).

All doc line numbers below are at target `3961af94fa62` unless marked "base".

## Answer

None of the existing ACP-LIST-*/ACP-DELETE-* rows change meaning. ACP-LIST-001/002 and ACP-DELETE-002 keep their cited lines. ACP-DELETE-001/003 only need a mechanical line move (`session-delete.mdx:89` -> `:90`), because a new bullet was inserted at line 87. One prose comment in the test file also cites `:89`, and `spec-impact --fix` will not move it. The new normative agent-side text in the assigned docs is:

1. `session-list.mdx:174`: an invalid cursor SHOULD get `-32602`. This is a new ADVISORY row (ACP-LIST-003).
2. The new "Archived sessions (unstable)" section, `session-list.mdx:227-261`. It has several observable MUSTs, all gated on `sessionCapabilities.archive`.

The new `session-delete.mdx:87` is a client-side SHOULD (treat `-32002` from `session/delete` as success). It is a ledger entry, plus an optional tweak to ACP-DELETE-003's prerequisite handling. `session/set_title` and `session/status` have no v1 protocol doc of their own. Their normative text lives in schema descriptions and in `error.mdx:66,68`, and `initialization.mdx:349,355` links them only to Draft RFDs. My recommendation: add the archive rows now, add a minimal 1-2 row smoke set for `set_title` and `status` (or defer them, see DECISION NEEDED D5), and put the hard-to-observe rest in the ledger.

## Summary table

| id | classification | note |
|----|----------------|------|
| ACP-LIST-001 | unchanged | Cited lines 82 and 94 are unchanged. The `ListSessionsRequest`/`SessionInfo` `$defs` gained only an optional nullable `archived` and a `_meta` doc-link change, and schema validation updates itself on refresh. |
| ACP-LIST-002 | unchanged | Lines 84-87 and 166 are unchanged. `ListSessionsRequest.properties.cwd` is unchanged; spec-impact flags it only because its parent `$def` changed. |
| ACP-PROMPT-004 | unchanged | Cites `session-list.mdx:136-137` (`cwd` "Always an absolute path"). Identical at target. |
| ACP-DELETE-001 | citation-only change | `session-delete.mdx:69-81,89` -> `69-81,90`. Line 89 at base ("deleting an active session is implementation-defined") is line 90 at target, so `--fix` remaps it. **Also fix by hand** the comment in `src/tck/v1/conformance/test_session_capabilities.py:226`, which cites `session-delete.mdx:89`. |
| ACP-DELETE-002 | unchanged | Line 86 (SHOULD succeed silently) is unchanged. The new line 87 is a client-side tolerance rule, not a relaxation of the agent rule, so ADVISORY FAIL on `-32002` stays correct. See D2. |
| ACP-DELETE-003 | citation-only change | `session-delete.mdx:85,89` -> `85,90` (mechanical). Optional test tweak: treat a `-32002` delete response as success and still run the list check (D3). An archive-aware check belongs in the new ACP-ARCHIVE-006, not here. |
| ACP-LIST-003 | **new** (ADVISORY) | `session/list` with an invalid `cursor` SHOULD get `-32602` (`session-list.mdx:174`). |
| ACP-ARCHIVE-001 | **new** (CAPABILITY: `sessionCapabilities.archive`) | Advertising `archive` also requires advertising `list` (MUST, `session-list.mdx:229`). |
| ACP-ARCHIVE-002 | **new** (CAPABILITY: archive) | Every listed `SessionInfo` carries a boolean `archived` (MUST, `:254`). |
| ACP-ARCHIVE-003 | **new** (CAPABILITY: archive) | Archive and unarchive round-trip: schema-valid empty results, and the session moves between the default (`exclude`) and `only` views (`:231,244-250`). |
| ACP-ARCHIVE-004 | **new** (CAPABILITY: archive) | An unsupported `archived` filter value gets `-32602`, not an `exclude` fallback (MUST, `:252`). |
| ACP-ARCHIVE-005 | **new** (CAPABILITY: archive) | Archive and unarchive are idempotent and succeed (`:260`). Archive/unarchive of a nonexistent session is an error, not a silent success (`:260`, `error.mdx:67`). The `-32002` code tier is D4. |
| ACP-ARCHIVE-006 | **new** (CAPABILITY: archive + delete + list) | A deleted session is absent under every filter value, including `include`/`only` (`:261`). |
| ACP-ARCHIVE-007 | **new, deferrable** (CAPABILITY: archive) | Archiving a loaded session with an in-flight prompt cancels it (`:256`; schema MUST). Mirrors ACP-CLOSE-002. |
| ACP-TITLE-001 | **new, or defer (D5)** (CAPABILITY: `sessionCapabilities.title`) | `session/set_title` on the connection's own session succeeds with a schema-valid result carrying a string `title`. |
| ACP-TITLE-002 | **new, or defer (D5)** (CAPABILITY: title) | An empty `title` gets `-32602`; a nonexistent session is an error (`-32002`). |
| ACP-SESSIONSTATUS-001 | **new, or defer (D5)** (CAPABILITY: `sessionCapabilities.status`) | `session/status` on the connection's own active session returns a schema-valid result with `status: "open"`. |
| ACP-SESSIONSTATUS-002 | **new, or defer (D5)** (ADVISORY) | `session/status` of a never-created id gets `-32002` with `data.sessionId`. ADVISORY because sources disagree (see Discrepancies). |
| ledger L1 | new deliberate non-requirement | `session-delete.mdx:87`: clients SHOULD treat `-32002` from `session/delete` as success. Client-side rule. |
| ledger L2 | new deliberate non-requirement | `session-list.mdx:252`: the filter applies before pagination, and clients keep the same `cwd`/`archived` while paging. Unobservable / client-side. |
| ledger L3 | new deliberate non-requirement | `session-list.mdx:258`: archive state persists across connections and restarts, and close/load/resume do not change it. Out of scope for now. |
| ledger L4 | new deliberate non-requirement | `SetSessionTitleRequest`: after success the agent SHOULD NOT replace the title with an auto-generated one. Not reliably observable. |
| ledger L5 | new deliberate non-requirement | `SessionStatusRequest`: `session/status` MUST NOT have side effects. Not fully observable. |

No existing rows are retired.

## Requirements

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| 1 | `session/list` with `{}` returns the first page; Agent MUST respond with sessions list | capability:`sessionCapabilities.list` (existing LIST-001) | `docs/protocol/v1/draft/session-list.mdx:82,94` @ 3961af94fa62 |
| 2 | Empty `sessions` array when nothing matches | capability:list (existing LIST-002) | `session-list.mdx:166` |
| 3 | Invalid cursor -> `-32602` | SHOULD | `session-list.mdx:174`; restated without a keyword at `error.mdx:47` |
| 4 | Deleted sessions vanish from list | capability:delete (existing DELETE-003) | `session-delete.mdx:85` |
| 5 | Unknown/already-deleted delete succeeds silently | SHOULD (existing DELETE-002) | `session-delete.mdx:86` |
| 6 | Client treats `-32002` from delete as success | client-side SHOULD (ledger) | `session-delete.mdx:87` |
| 7 | `archive` advertised => `list` advertised | MUST, capability:archive | `session-list.mdx:229`; `schema/v1/schema.unstable.json#/$defs/SessionCapabilities/properties/archive` |
| 8 | Filter semantics `exclude` (default/omitted/null) / `include` / `only` | capability:archive (definitional, no keyword) | `session-list.mdx:244-250`; `#/$defs/SessionArchiveFilter` |
| 9 | Unsupported filter value -> `-32602`, never an `exclude` fallback | MUST, capability:archive | `session-list.mdx:252`; `#/$defs/SessionArchiveFilter` (description) |
| 10 | Boolean `archived` on every listed session | MUST, capability:archive | `session-list.mdx:254`; `#/$defs/SessionInfo/properties/archived` |
| 11 | Archive hides, unarchive returns; both take only `sessionId` and return an empty result | capability:archive (definitional) | `session-list.mdx:231`; `#/$defs/ArchiveSessionResponse`, `#/$defs/UnarchiveSessionResponse` |
| 12 | Archiving a loaded session cancels work and frees it as if closed; `close` capability not required | capability:archive (MUST in schema, no keyword in doc) | `session-list.mdx:256`; `#/$defs/ArchiveSessionRequest` ("the Agent MUST cancel any ongoing work") |
| 13 | Unarchive never loads/resumes; client SHOULD unarchive before load/resume; Agent MAY reject load/resume of archived | client SHOULD / agent MAY (nothing to assert) | `session-list.mdx:257` |
| 14 | Archive state persists across connections/restarts; close/load/resume don't change it | capability:archive (ledger L3 for now) | `session-list.mdx:258` |
| 15 | Archived session reports `saved` from `session/status` | capability:archive + status | `session-list.mdx:259` |
| 16 | Archive of archived / unarchive of unarchived succeeds; nonexistent -> `-32002` | capability:archive (no keyword) | `session-list.mdx:260`; `error.mdx:67`; `#/$defs/ArchiveSessionRequest`, `#/$defs/UnarchiveSessionRequest` |
| 17 | Deleted sessions excluded from every filter value; unarchive does not restore them | capability:archive (+delete) | `session-list.mdx:261` |
| 18 | `set_title`: `title` required string; empty-after-normalization -> `-32602`; nonexistent session -> `-32002`; session need not be loaded | capability:`sessionCapabilities.title` | `#/$defs/SetSessionTitleRequest`, `#/$defs/SetSessionTitleRequest/properties/title`; `error.mdx:68` |
| 19 | `set_title` response carries the stored `title` (required) | capability:title | `#/$defs/SetSessionTitleResponse` |
| 20 | After `set_title` succeeds, agent SHOULD NOT auto-replace the title | SHOULD (ledger L4) | `#/$defs/SetSessionTitleRequest` (description) |
| 21 | `session/status` MUST NOT have side effects | MUST, capability:status (ledger L5) | `#/$defs/SessionStatusRequest` |
| 22 | `session/status` of an unknown session -> `-32002` with `data.sessionId` | capability:status; RFD contradicts (see Discrepancies) | `error.mdx:66`; `#/$defs/SessionStatusRequest` |
| 23 | `SessionStatusResponse.status` required, `open` / `saved` / open string | capability:status | `#/$defs/SessionStatusResponse`, `#/$defs/SessionStatus` |

## Details

### What changed in the assigned docs (base -> target)

`session-list.mdx`:
- Heading re-casing ("Checking support", "Listing sessions", "Updating session metadata", "Interaction with other session methods"), plus wording rewrites on lines 6, 8, 173, 199, 221. These are editorial.
- Lines 141 and 144: `MAY`/`MUST NOT` became bold `**MAY**`/`**MUST NOT**` (additionalDirectories). The keywords were already there, so this is not a semantic change, and no registry row cites these lines.
- Line 174: "Agents **SHOULD** return an error if the cursor is invalid" became "Agents **SHOULD** return `-32602` if the cursor is invalid". The error code is the new part.
- Lines 226-261 are new: "Archived sessions (unstable)".

`session-delete.mdx`:
- Line 6 reworded; headings re-cased (33, 54).
- Line 87 is new: "Clients **SHOULD** treat a `-32002` response to `session/delete` as a successful delete." All later lines shift by +1, so base 87/88/89 are now 88/89/90.

Related cross-doc text: `error.mdx:47` says an invalid `session/list` cursor gets `-32602`. `error.mdx:55` says "Closing or deleting a session that does not exist still succeeds." `error.mdx:63-68` is the "Unstable features" section with the error codes for status, archive, and set_title. `initialization.mdx:323-329,348-360` documents the new `archive`/`status`/`title` capability markers, all marked "**Unstable.**". `session-setup.mdx:347-350` has the parallel idempotent-close plus client `-32002` tolerance rule for `session/close`.

### Schema `$defs` at target (relevant shapes)

- `ListSessionsRequest`: new optional `archived: SessionArchiveFilter | null`. It is UNSTABLE, and omitted or `null` means `exclude`.
- `SessionInfo`: new optional `archived: boolean | null`. It is UNSTABLE, and agents advertising `archive` MUST include it on every listed session. Required fields are unchanged (`sessionId`, `cwd`).
- `ListSessionsResponse`, `DeleteSessionRequest`, `DeleteSessionResponse`: only the `_meta` doc link changed (`/protocol/extensibility` -> `/protocol/v1/draft/extensibility`). There is no shape change.
- `SessionArchiveFilter`: `anyOf` const `exclude` | `include` | `only` | open `string` ("other"; `_`-prefixed values are implementation extensions, other unknown values are reserved for ACP). "An Agent MUST return `-32602` for a value it does not support rather than treating it as `exclude`."
- `SessionCapabilities`: new `archive` (`SessionArchiveCapabilities | null`), `status` (`SessionStatusCapabilities | null`), and `title` (`SessionTitleCapabilities | null`). All three are UNSTABLE object markers with only `_meta`. The `systemPrompt` description lost its UNSTABLE banner, which is someone else's slice.
- `ArchiveSessionRequest` / `UnarchiveSessionRequest`: `{sessionId (required), _meta?}`. `ArchiveSessionResponse` / `UnarchiveSessionResponse`: `{_meta?}`.
- `SetSessionTitleRequest`: `{sessionId, title: string}`, both required. `title` is non-null, and the description says an empty-after-normalization title gets `-32602`. `SetSessionTitleResponse`: `{title: string (required), _meta?}`.
- `SessionStatusRequest`: `{sessionId}`. `SessionStatusResponse`: `{status: SessionStatus (required), _meta?}`. `SessionStatus` is `open` | `saved` | open `string`.

Every new method `$def` has `x-side: "agent"` and an `x-method`. So after the schema refresh, `tck.v1.validation.validate_agent_response("session/archive" | "session/unarchive" | "session/set_title" | "session/status", msg)` works with no hand edits (see the `src/tck/v1/validation.py` module docstring on deriving from `x-method`).

### Reference SDK status (context for the defer decision)

- Rust SDK: all four methods are wired behind unstable features `unstable_session_archive`, `unstable_session_status`, and `unstable_session_set_title` (rust-sdk @ e75d6f1 `src/agent-client-protocol/src/schema/client_to_agent/requests.rs:1-4,23-26,69-91`; feature forwarding in `src/agent-client-protocol/Cargo.toml:58,61,69,72`).
- Python SDK: no occurrences of these methods or types in `*.py` (python-sdk @ 8a99407, schema tag `schema-v1.23.0`), so it has not adopted them yet.
- TCK precedent cuts both ways. The unstable `systemPrompt` got CAPABILITY rows (ACP-SYSPROMPT-001..003) while it was still UNSTABLE at base. The unstable `session/fork` has no rows and is not advertised by `tests/fixtures/agents/v1/conforming_full.py:26-43`.

### Proposed new rows

Citations use the target revision; write them as `path:lines @ 3961af94fa62` per the project convention (`_cite` adds the revision).

**ACP-LIST-003** (ADVISORY, test gated by `@pytest.mark.capability("agentCapabilities.sessionCapabilities.list")`, like ACP-DELETE-002)
- Text: "`session/list` with a `cursor` the agent never issued SHOULD fail with `-32602` (Invalid params)."
- Citation: `docs/protocol/v1/draft/session-list.mdx:174; docs/protocol/v1/draft/error.mdx:47`.
- Tier: SHOULD at line 174, so ADVISORY.
- Observation: send `session/list {"cursor": "tck-invalid-cursor\u0000"}` (or any string that a real opaque token is very unlikely to be). Expect an error with `code == -32602`. A success result is a FAIL (the agent ignored the cursor). A different error code is also a FAIL, since the SHOULD names the code; recording it instead would be the lenient option. SKIP on `-32000`, as ACP-ERROR-002 does.
- Caveat: the TCK cannot prove a fabricated cursor is invalid, because cursors are opaque (`:173`). This is part of why ADVISORY is right.
- Fixture impact: `tests/fixtures/agents/v1/_base.py:404-411` (`_handle_list`) ignores `cursor` entirely, so the conforming baseline (`conforming_full.py`) would FAIL this row. The baseline must reject unknown cursors with `-32602`. Suggested non-conforming fixture: `list_ignores_bad_cursor.py`, which returns the first page for any cursor.

**ACP-ARCHIVE-001** (CAPABILITY, `agentCapabilities.sessionCapabilities.archive`)
- Text: "An agent advertising `sessionCapabilities.archive` also advertises `sessionCapabilities.list`."
- Citation: `session-list.mdx:229; schema/v1/schema.unstable.json#/$defs/SessionCapabilities/properties/archive`.
- Tier: MUST.
- Observation: initialize result only. No session is needed.
- Fixture: `archive_without_list.py` advertises `{archive: {}}` without `list`.

**ACP-ARCHIVE-002** (CAPABILITY, archive)
- Text: "With `archive` advertised, every `SessionInfo` in a `session/list` result carries a boolean (non-null) `archived`."
- Citation: `session-list.mdx:254; schema/v1/schema.unstable.json#/$defs/SessionInfo/properties/archived`.
- Tier: MUST.
- Observation: create a session in `tmp_path`, then `session/list {"cwd": tmp}`. Each entry needs `isinstance(info.get("archived"), bool)`. It passes vacuously only if the list is empty; a test can force at least one entry. It is stronger to also check `archived: "include"` so that archived entries are covered.
- Fixture: `archive_omits_archived_flag.py`.

**ACP-ARCHIVE-003** (CAPABILITY, archive)
- Text: "`session/archive` then `session/unarchive` on an existing session both succeed with schema-valid results. After archive, the session is absent from default `session/list` results and present (with `archived: true`) under `archived: \"only\"`. After unarchive, it is back in default results with `archived: false`."
- Citation: `session-list.mdx:231,244-250; schema/v1/schema.unstable.json#/$defs/ArchiveSessionResponse; schema/v1/schema.unstable.json#/$defs/UnarchiveSessionResponse; schema/v1/schema.unstable.json#/$defs/SessionArchiveFilter`.
- Tier: the statements have no RFC keyword but define what the capability means. That matches the precedent of ACP-DELETE-003, which is CAPABILITY for the unkeyworded "Deleted sessions no longer appear" (`session-delete.mdx:85`).
- Observation: use `cwd`-filtered lists over all pages, the same paging loop as ACP-DELETE-003 (`test_session_capabilities.py:316-331`).
- The session is active when archived. Archiving closes it (`:256`), and that does not require `close`, so no close-first dance is needed (unlike `_close_then_delete`).
- Clean up afterwards: delete the session when `delete` is advertised. These tests write to a real agent's persistent session store.
- Fixture: `archive_still_listed.py`, where archive returns `{}` but the session keeps showing in default lists.

**ACP-ARCHIVE-004** (CAPABILITY, archive)
- Text: "`session/list` with an `archived` filter value the agent does not support (e.g. `_tck_unsupported`) fails with `-32602`, rather than returning the default (`exclude`) view."
- Citation: `session-list.mdx:252; schema/v1/schema.unstable.json#/$defs/SessionArchiveFilter`.
- Tier: MUST.
- Probe value: use a `_`-prefixed value, which is the implementation-extension space, so the TCK does not squat on a reserved future ACP value. The TCK already holds its probes to the `_` rule (CLAUDE.md "How to add a requirement", step 4).
- Caveat: an agent could in theory support that exact `_tck_*` value. This is negligible.
- Fixture: `archive_filter_falls_back.py`, which treats unknown values as `exclude`.

**ACP-ARCHIVE-005** (CAPABILITY, archive)
- Text: "Archiving an already-archived session and unarchiving a not-archived session both succeed. `session/archive`/`session/unarchive` of a never-created `sessionId` fail with an error (not silent success)."
- Citation: `session-list.mdx:260; docs/protocol/v1/draft/error.mdx:67; schema/v1/schema.unstable.json#/$defs/ArchiveSessionRequest; schema/v1/schema.unstable.json#/$defs/UnarchiveSessionRequest`.
- Tier: CAPABILITY, same unkeyworded-definitional reasoning as ARCHIVE-003. `error.mdx:67` explicitly says "Unlike `session/delete`, they don't succeed silently."
- Whether to also assert `code == -32002` is D4.
- Fixture: `archive_unknown_succeeds.py`.

**ACP-ARCHIVE-006** (CAPABILITY, archive. The test also needs `delete` and `list` and SKIPs without them, the way ACP-DELETE-003 handles `list`)
- Text: "After a successful `session/delete`, the deleted session appears under no `archived` filter value (`exclude`, `include`, `only`)."
- Citation: `session-list.mdx:261`. The RFD's sharper "MUST NOT implement `session/delete` as an archive" (`docs/rfds/session-archive.mdx:178`) is a Draft proposal; cite it as rationale only.
- Observation: create, delete (close first when `close` is advertised, as `_close_then_delete` does), then list with each filter value.
- This closes a gap: ACP-DELETE-003 only checks the default view, so delete-as-archive passes it today.
- Fixture: `delete_archives_instead.py`, where delete hides the session from the default view but `include` still shows it.

**ACP-ARCHIVE-007** (CAPABILITY, archive. Deferrable: it is the most complex of the set)
- Text: "`session/archive` of a session with an in-flight `session/prompt` resolves that prompt with `stopReason: \"cancelled\"`, and the archive succeeds."
- Citation: `session-list.mdx:256; schema/v1/schema.unstable.json#/$defs/ArchiveSessionRequest` (the schema says MUST; the doc states it without a keyword).
- Observation: reuse the race-aware ACP-CLOSE-002 pattern (`test_session_capabilities.py:359` onward), with `run_prompt`'s `on_action` sending `session/archive`.
- Fixture: `archive_leaves_prompt_running.py`.

**ACP-TITLE-001** (CAPABILITY, `agentCapabilities.sessionCapabilities.title`)
- Text: "`session/set_title` with a non-empty title on a session created on this connection succeeds with a schema-valid result whose `title` is a string."
- Citation: `docs/protocol/v1/draft/initialization.mdx:354-360; schema/v1/schema.unstable.json#/$defs/SetSessionTitleRequest; schema/v1/schema.unstable.json#/$defs/SetSessionTitleResponse`.
- Do not assert equality with the sent title, because the agent MAY normalize it (`#/$defs/SetSessionTitleRequest/properties/title`). A plain ASCII title with no surrounding whitespace should round-trip in practice, but that is not required.
- Optional strengthening, ADVISORY or a separate id: when `list` is advertised, a later `session/list` shows `title` equal to the returned value. This is inferred from "The Agent responds only after it has stored the title" (`#/$defs/SetSessionTitleRequest`) and stated directly only in the Draft RFD (`docs/rfds/session-set-title.mdx:174`). Label it as proposal-backed if added.
- Fixture: `set_title_returns_empty.py`, which returns `{}` without `title`.

**ACP-TITLE-002** (CAPABILITY, title)
- Text: "`session/set_title` with `title: \"\"` fails with `-32602`, and `session/set_title` for a never-created `sessionId` fails with an error (`-32002`)."
- Citation: `docs/protocol/v1/draft/error.mdx:68; schema/v1/schema.unstable.json#/$defs/SetSessionTitleRequest; schema/v1/schema.unstable.json#/$defs/SetSessionTitleRequest/properties/title`.
- An empty string is empty after any normalization, so it is a deterministic probe.
- Same code-tier question as D4. Consider splitting it into two ids if the orchestrator prefers one assertion per id.
- Fixture: `set_title_accepts_empty.py`.

**ACP-SESSIONSTATUS-001** (CAPABILITY, `agentCapabilities.sessionCapabilities.status`)
- Text: "`session/status` for a session created (and not closed) on this connection succeeds with a schema-valid `SessionStatusResponse` whose `status` is `open`."
- Citation: `docs/protocol/v1/draft/initialization.mdx:348-352; schema/v1/schema.unstable.json#/$defs/SessionStatusResponse; schema/v1/schema.unstable.json#/$defs/SessionStatus`.
- `open` is "has the session in memory", and `saved` is "does not have it in memory". A session active on the requesting connection is in memory, so `saved` would be self-contradictory.
- That step is an inference: no source says "active implies open" in so many words. If the orchestrator wants zero inference, assert schema validity only and record the value.
- The area name avoids clashing with `auth/status`, which is someone else's slice.
- Fixture: `status_reports_saved_for_active.py`.

**ACP-SESSIONSTATUS-002** (ADVISORY, test gated by the status capability)
- Text: "`session/status` for a never-created `sessionId` fails with `-32002` and `data.sessionId` equal to the requested id."
- Citation: `docs/protocol/v1/draft/error.mdx:66; schema/v1/schema.unstable.json#/$defs/SessionStatusRequest`.
- Tier: ADVISORY, not CAPABILITY, because the Draft RFD lets an agent that cannot cheaply tell `saved` from unknown "return `saved` for any session it does not have in memory" (`docs/rfds/session-status.mdx:132`). An agent following the RFD would get an unfair CAPABILITY FAIL. See Discrepancies.
- Fixture: `status_unknown_returns_open.py`. Returning `open` for an unknown id is wrong under every source.

### Proposed ledger entries (`spec-tracker/maps/v1.toml` `[[not_requirement]]`)

| # | citation | statement | reason |
|---|----------|-----------|--------|
| L1 | `docs/protocol/v1/draft/session-delete.mdx:87 @ 3961af94fa62` | Clients SHOULD treat a `-32002` response to `session/delete` as a successful delete. | Client-side rule; the TCK tests agents. (It may still shape how the TCK interprets agent responses, see D3.) |
| L2 | `docs/protocol/v1/draft/session-list.mdx:252 @ 3961af94fa62` | The `archived` filter combines with `cwd` and applies before pagination; clients keep the same `cwd`/`archived` when following `nextCursor`. | "Before pagination" is not observable without knowing the agent's page size; the cursor-consistency half is a client-side rule. Add only if ARCHIVE rows are added. |
| L3 | `docs/protocol/v1/draft/session-list.mdx:258 @ 3961af94fa62` | Archive state persists across connections and restarts; closing, loading, or resuming a session does not change it. | Out of scope for now: it needs a two-process test against the agent's real persistent store, and load/resume of an archived session MAY be rejected (`:257`), which makes the close/load half inconclusive. Revisit if ARCHIVE rows prove stable. |
| L4 | `schema/v1/schema.unstable.json#/$defs/SetSessionTitleRequest @ 3961af94fa62` | After a successful `session/set_title`, the Agent SHOULD NOT replace the title with one it generates automatically. | Not reliably observable: when an agent generates titles is internal, and a clean window proves nothing. |
| L5 | `schema/v1/schema.unstable.json#/$defs/SessionStatusRequest @ 3961af94fa62` | `session/status` MUST NOT have side effects (no load/resume/create/close/change, no attaching the connection). | Not fully observable from the client; only negative evidence such as "no `session/update` after status" is available. |

Deliberately left out of the ledger:
- `session-list.mdx:229` "Clients MUST NOT use any of them unless advertised". The TCK obeys it through `@pytest.mark.capability`.
- `session-list.mdx:257` agent MAY reject load/resume of an archived session. A MAY has nothing to assert.
- The `SessionStatus` "Clients MUST treat unknown as saved". Client-side.
- `session-list.mdx:175` "SHOULD enforce reasonable page sizes". Pre-existing, unchanged text; not part of this diff.

## Testability notes

- All archive, title, and status tests mutate the agent's persistent session store (create, archive, retitle). Use a `tmp_path` cwd and a `cwd` filter, as ACP-DELETE-003 does, so only the test's own sessions are seen. Delete afterwards when `delete` is advertised. Without `delete`, a real agent keeps a "TCK" session in the operator's history; that is already true for existing session tests.
- `capability_is_supported` (object marker; present and non-null) is the right gate for `archive`/`title`/`status`. All three are `{}`-style markers (`#/$defs/SessionArchiveCapabilities`, `SessionTitleCapabilities`, `SessionStatusCapabilities`).
- Conforming baseline: `tests/fixtures/agents/v1/_base.py` dispatches unknown methods to `-32601` (`:163-164`) and `conforming_full.py:26-43` lists `sessionCapabilities` by hand. Any new rows therefore need `_base.py` handlers for `session/archive`, `session/unarchive`, `session/set_title`, `session/status`, plus `archived` filtering and `SessionInfo.archived` in `_handle_list`, cursor validation for LIST-003, and the new markers in `conforming_full.py`. Otherwise their PASS path is never exercised (the `tests/v1/test_cli.py` exact-set assertions will show this).
- If `archive` is added to `conforming_full.py`, the baseline must also emit `archived` on every listed session, or the new ARCHIVE-002 FAILs against the baseline.
- ACP-DELETE-002 against a real agent that returns `-32002` (following the generic `error.mdx:53` rule): ADVISORY FAIL, which is correct per `session-delete.mdx:86`. The failure message could mention that `-32002` is tolerated by clients (`:87`) but is still a SHOULD miss.

## Discrepancies

1. **`session/status` of an unknown session.**
   - `error.mdx:66` and `#/$defs/SessionStatusRequest` both say an unknown session "gets `-32002`" with `data.sessionId`, with no exception.
   - The Draft RFD states MUST `-32002` (`docs/rfds/session-status.mdx:126`), but also says an agent that cannot cheaply distinguish "**MAY** return `saved` for any session it does not have in memory" (`:132`).
   - Neither reference SDK shows runtime behavior: rust-sdk only has types, and python-sdk does not have the method.
   - This is why SESSIONSTATUS-002 is proposed ADVISORY.
2. **Archiving an active session: keyword strength and wording.**
   - `session-list.mdx:256` states the behavior without a keyword and says "If the session is loaded".
   - `#/$defs/ArchiveSessionRequest` says "If the session is active, the Agent MUST cancel any ongoing work…".
   - The RFD also says MUST (`docs/rfds/session-archive.mdx:172`).
   - "Loaded" vs "active" are likely meant the same; note it but do not block on it.
3. **Delete of a nonexistent session.**
   - `error.mdx:55` states without a keyword that "Closing or deleting a session that does not exist still succeeds".
   - `session-delete.mdx:86` makes it a SHOULD, and `:87` tells clients to tolerate `-32002`.
   - ACP-DELETE-002 follows the keyworded source (ADVISORY), which remains right.
4. **Archive filter support.**
   - The Draft RFD says agents advertising `archive` "MUST support all three values" (`docs/rfds/session-archive.mdx:112`).
   - The v1 doc only says the capability means the agent supports "the `archived` filter" (`session-list.mdx:229`) and lists the three values (`:246-250`).
   - This is consistent in effect, with no conflict. ARCHIVE-003 exercises `only`; it could also exercise `include`.
5. **`session/status` and `session/set_title` have no v1 protocol doc.** `initialization.mdx:349,355` links them to Draft RFDs. Their normative text exists only in schema descriptions and in `error.mdx:66,68`. Citations for TITLE-*/SESSIONSTATUS-* must therefore rely on schema `$defs` plus `error.mdx`, never on the RFD alone.

## DECISIONS NEEDED

- **D1 (scope of the unstable methods).** Recommendation:
  - Add ACP-ARCHIVE-001..006 now. Their rules sit in a v1 draft protocol doc (`session-list.mdx:227-261`) that this update touches, with explicit MUSTs and deterministic probes.
  - Defer ARCHIVE-007 to a follow-up slice (race test).
  - Add the ledger entries L1-L3.
  - Alternative: defer all archive rows and record one ledger entry per method with reason "unstable; deferred". Precedent for deferral: `session/fork` has no rows. Precedent for adding: ACP-SYSPROMPT-* were added while `systemPrompt` was UNSTABLE.
- **D2 (ACP-DELETE-002).** Recommendation: unchanged. Keep ADVISORY and keep failing on any error, including `-32002`, because the agent rule at `:86` did not change and `:87` is a client tolerance. Optionally improve the failure message.
- **D3 (ACP-DELETE-003 prerequisite).** Recommendation: when `session/delete` returns `-32002`, proceed to the list check instead of SKIPping. This follows `session-delete.mdx:87`, gives a real verdict on whether the session vanished, and changes no requirement text. Keep ACP-DELETE-001 strict: the session existed, so the defined response is the empty result (`session-delete.mdx:73-81`, `error.mdx:55`).
- **D4 (error-code strictness for unkeyworded "gets `-32002`").** This applies to archive/unarchive and set_title of nonexistent sessions. Recommendation: the CAPABILITY row asserts "is an error, not success", which `error.mdx:67` makes explicit for archive. The exact `-32002` code is asserted either as a separate ADVISORY row or only recorded. This mirrors how the generic unknown-session rule is only a SHOULD (`error.mdx:53`) and how ACP-SYSPROMPT-002 records rather than asserts a recommended code. The alternative is to assert `-32002` inside the CAPABILITY row.
- **D5 (`set_title` / `status`).** Recommendation: either add the minimal rows ACP-TITLE-001/002 and ACP-SESSIONSTATUS-001/002 (ADVISORY for 002), or defer both to a later update with a "deferred, unstable, no protocol doc" ledger entry each. I lean slightly to deferring. Their only v1 normative text is schema descriptions, their RFDs are Draft and in one case contradict the schema (Discrepancy 1), and the Python SDK has not adopted them. Adding them is cheap and low-risk, though, if the orchestrator wants coverage of everything the refreshed schema validates.

## Open questions

- Does `spec-impact --fix` also rewrite line citations in test comments and docstrings? `src/tck/v1/conformance/test_session_capabilities.py:226` cites `session-delete.mdx:89`, which should become `:90`. If it does not, the programmer must fix it by hand. Route to whoever owns spec-tracker.
- `error.mdx` (the new home of the `-32002`/`-32602` rules cited above) and `ACP-INFO-UNKNOWNSESSION-001` (which cites `error.mdx:6 (stub)`) belong to another researcher's slice. The `-32002` general rule at `error.mdx:53` may let that informational row become an ADVISORY one.
- `initialization.mdx:363` still says "`load_session` capability" while the schema now says `loadSession`. This is editorial and in another slice.
