# v2 (Draft) impact: session-list, session-delete, session/fork, and the new unstable session methods (alpha.9 -> alpha.14)

**Sources checked:** agent-client-protocol (worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`), base `beac4ba96190` -> target `3961af94fa62` (2026-11-10). Read whole at target: `docs/protocol/v2/draft/session-list.mdx`, `session-delete.mdx`. Also read: the relevant parts of `error.mdx`, `session-setup.mdx` ("Session lifecycle", "Closing active sessions"), `initialization.mdx:255-287`, `overview.mdx:256-259`, `schema.mdx` (session/fork section), the RFDs `session-status.mdx`, `session-archive.mdx`, `session-set-title.mdx`, `session-fork.mdx`, and the `$defs` at target in `schema/v2/schema.unstable.json`. TCK: `src/tck/v2/requirements.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `_helpers.py`, `tests/fixtures/agents/v2/_base.py`, `tests/v2/test_cli.py`. I did not consult the reference SDKs: these rules are agent-side wire behavior that the spec states directly, and the SDKs do not implement session storage, listing, or cursors.
**Confidence:** high for the classifications and citations. Medium for two tier calls (the invalid-cursor probe, and DELETE-201's prerequisite), both flagged DECISION NEEDED.

All target citations below are `@ 3961af94fa62`. "SL" means `docs/protocol/v2/draft/session-list.mdx` and "SD" means `docs/protocol/v2/draft/session-delete.mdx`.

## Answer

None of the 12 existing rows needs retiring. Six rows (LIST-201/202/204, RESUME-202, DELETE-203, FORK-201) are unchanged, or need only a citation remap. FORK-201 and FORK-202 should also be moved off the generated `schema.mdx` onto draft-doc and JSON-Pointer citations. The draft docs now define fork activity directly, at `session-setup.mdx:49` and `error.mdx:54`.

Three rows have stale text or a test that no longer matches the spec:
- **LIST-203**: the spec now allows path normalization, so an exact string comparison is too strict. Subdirectory and `additionalDirectories` sessions are now explicitly excluded.
- **DELETE-201**: its rationale ("deleting an active session is implementation-defined") is now false. SD:95 makes active deletion a MUST that acts like close. The close-first, never-prompted setup also risks a false FAIL, because an agent may legally discard such a session, after which `-32002` is tolerated.
- **DELETE-202**: the TCK, acting as a client, SHOULD treat `-32002` on delete as success.

New observable agent-side rules:
- relative `cwd` filter gets `-32602`;
- invalid cursor gets `-32602` (was a SHOULD, now a MUST);
- delete of an active session cancels its work like close;
- `session/resume` of a deleted session gets `-32002`;
- `session/fork` of an unknown session gets `-32002`;
- a whole "Archived sessions (unstable)" feature with several MUSTs.

There is also a harness bug: `_helpers._route_from_list` stops paginating on `nextCursor: ""`, which is now explicitly a valid cursor. For `session/archive`, `session/status`, and `session/set_title`, I recommend CAPABILITY rows now for archive and a minimal set for status and title (DECISION NEEDED; see section 4).

## Summary table

| id | classification | one-line note |
|---|---|---|
| ACP-LIST-201 | citation-only | `session-list.mdx:10,73,108` -> `:10,76,111`. Line 10 was reworded ("advertise `capabilities.session`"); same meaning. |
| ACP-LIST-202 | citation-only (unflagged) | `:145` -> `:148`; text unchanged. |
| ACP-LIST-203 | **changed text + test** | `:63-66` -> `:63-69`. Exact-dir match, MAY normalize, subdirs and `additionalDirectories` excluded. The test should compare with `_same_dir` and seed a subdirectory session. |
| ACP-LIST-204 | citation-only | `:115-117` -> `:118-120`; the `overview.mdx:188` part -> `overview.mdx:218` (that doc's owner should confirm). |
| ACP-RESUME-202 | citation-only (session-list part) | `session-list.mdx:197-198` -> `:204-205`, same sentence. The rest of the row is for the session-setup and prompt-lifecycle owners. |
| ACP-DELETE-201 | **changed text + test (DECISION NEEDED)** | Stale "implementation-defined" rationale. Recommend deleting an *active idle* session (it definitely exists) rather than close-then-delete. |
| ACP-DELETE-202 | **changed test (+citation)** | `:27-28,90,94` -> `:27-28,90,92`. Treat a `-32002` delete response as success (SD:92 client SHOULD), then judge only the listing. |
| ACP-DELETE-203 | unchanged (citation-only; unflagged) | `:91` unchanged. Also cite `error.mdx:56`. Keep FAIL on `-32002` (ADVISORY), with a note that clients tolerate it. Minor DECISION. |
| ACP-FORK-201 | citation-only, **manual repoint** | Drop `schema.mdx:614-624`. Cite `initialization.mdx:269-273`, `session-setup.mdx:49`, `#/$defs/ForkSessionResponse/properties/sessionId`. |
| ACP-FORK-202 | citation-only, **manual repoint** | Drop `schema.mdx:622-624`. Cite `session-setup.mdx:49`, `error.mdx:54`; the RFD cite may stay. Update the "Definitional prose" rider. |
| ACP-LIST-205 | **new**, CAPABILITY `capabilities.session` | A relative `cwd` filter is rejected with `-32602` (SL:64-65). |
| ACP-LIST-206 | **new**, CAPABILITY `capabilities.session` (DECISION NEEDED vs ADVISORY) | A never-issued cursor is rejected with `-32602` (SL:157, a MUST; was a SHOULD). |
| ACP-DELETE-204 | **new**, CAPABILITY `capabilities.session.delete` | Deleting a session with foreground work in flight cancels it as if closed: an idle `stopReason:"cancelled"` arrives before the delete response (SD:95). |
| ACP-DELETE-205 | **new**, CAPABILITY `capabilities.session.delete` | `session/resume` of a deleted session fails with `-32002` (SD:94, error.mdx:54-56). Coordinate with the error.mdx owner. |
| ACP-FORK-203 | **new**, CAPABILITY `capabilities.session.fork` | `session/fork` of a never-created session gets `-32002` (error.mdx:64). |
| ACP-FORK-204 | **new (optional, low priority)**, CAPABILITY `capabilities.session.fork` | Forking a closed but still-listed session succeeds; the source only has to exist (error.mdx:64). |
| ACP-ARCHIVE-201..207 | **new, DECISION NEEDED** (recommend now), CAPABILITY `capabilities.session.archive` | See section 4. |
| ACP-STATUS-201..203 | **new, DECISION NEEDED** (recommend minimal now, or defer), CAPABILITY `capabilities.session.status` | See section 4. |
| ACP-TITLE-201..203 | **new, DECISION NEEDED** (recommend minimal now, or defer), CAPABILITY `capabilities.session.title` | See section 4. |
| ledger x5 | new non-requirements | SL:158, SL:162, SL:243 ("before pagination"), SL:249 ("restarts"), SD:92 / SL:154-156 (client rules). See section 5. |
| harness | **bug** | `_helpers.py:415-417` treats `nextCursor: ""` as end-of-results, which violates SL:154. |

Retired: none.

## Requirements (new rules, tiered)

| # | Requirement | Tier | Citation |
|---|---|---|---|
| 1 | `session/list` with a relative `cwd` gets `-32602` | CAPABILITY `capabilities.session` (declarative "Agents reject"; error.mdx:48 generalizes) | SL:64-65; `docs/protocol/v2/draft/error.mdx:48` |
| 2 | An invalid `session/list` cursor gets `-32602` | CAPABILITY `capabilities.session` (MUST) | SL:157; error.mdx:48 |
| 3 | Deleting a session active on any connection cancels its work as if `session/close` had been called, then deletes it | CAPABILITY `capabilities.session.delete` (MUST) | SD:95; `session-setup.mdx:49,391,393` |
| 4 | Later requests for a deleted session, including `session/resume`, fail with `-32002` | CAPABILITY `capabilities.session.delete` (error.mdx:54 MUST) | SD:94; error.mdx:54-56; session-setup.mdx:47 |
| 5 | `session/fork` of a non-existent session gets `-32002`; the source need not be active | CAPABILITY `capabilities.session.fork` | error.mdx:64 |
| 6 | Archive feature MUSTs | CAPABILITY `capabilities.session.archive` | SL:218-252; error.mdx:66 |
| 7 | Clients SHOULD treat `-32002` on delete as success | client-side; the TCK honours it, no requirement | SD:92; error.mdx:56 |
| 8 | Empty-string `nextCursor` is valid; only omitted or `null` ends results | client-side; the TCK must honour it (harness bug) | SL:154; `#/$defs/ListSessionsResponse/properties/nextCursor` |

## Details

### 1. session-list.mdx: existing rows

The doc is not in `spec-tracker/maps/v2.toml` (neither is session-delete), so no section addresses need updating. The new "Archived sessions (unstable)" section (SL:218) is a standalone feature section. I recommend it **not** be core: other docs link to it explicitly (error.mdx:66, overview.mdx:257, initialization.mdx:266) rather than assume it.

- **ACP-LIST-201**: citation-only.
  - SL:10 at target: "Agents that advertise `capabilities.session` **MUST** support `session/list`." The base wording was "support the `session` method surface"; the meaning is the same.
  - Base :73 ("The Agent **MUST** respond with a list of sessions") is now :76.
  - Base :108 (`sessions` `required`) is now :111.
  - The only `ListSessionsResponse` change is description text: `nextCursor` gained "An empty string is a valid cursor". The `x-deserialize-default-on-error` hint was dropped, which is not structural.
  - The test is still correct. New citation: `session-list.mdx:10,76,111`.
- **ACP-LIST-202**: citation-only. The `:145` MUST ("return an empty `sessions` array") is now SL:148, unchanged. The test is still correct. The fixture `list_errors_when_empty.py` still trips it.
- **ACP-LIST-203**: changed text and test.
  - Target SL:63-69: "Must be an absolute path. Agents reject a relative path with `-32602`. Only sessions whose `cwd` is this same directory are returned. Sessions in subdirectories or with it in `additionalDirectories` don't match. Agents **MAY** normalize paths when comparing, for example ignoring a trailing separator." The schema `#/$defs/ListSessionsRequest/properties/cwd` carries the same text.
  - Proposed text: "When `session/list` is filtered by a real `cwd`, every returned `SessionInfo.cwd` names that same directory. Agents MAY normalize when comparing, so equality is judged after path normalization (for example a trailing separator). A session whose `cwd` is a subdirectory of the filter is never returned. (Per-entry only; the reverse direction is not asserted.)"
  - Test changes:
    1. Replace `session.get("cwd") == str(tmp_path)` with `_helpers._same_dir(session.get("cwd"), tmp_path)`. That helper already resolves paths, and pathlib drops trailing separators. Without this, an agent that echoes the stored cwd in a normalized form can false-FAIL.
    2. Before listing, also create a session at `tmp_path / "child"` (an existing directory), so the per-entry check actually exercises the new subdirectory exclusion.
    3. Optionally, when `capabilities.session.additionalDirectories` is advertised, also create a session at some other `cwd` with `additionalDirectories: [tmp_path]`, which must not be returned.
  - New citation: `session-list.mdx:63-69` plus `schema/v2/schema.unstable.json#/$defs/ListSessionsRequest/properties/cwd`.
  - Fixtures: `_base._handle_list_sessions` uses exact `==` on `cwd`, so it already excludes subdirectories. `resume_lists_foreign_session.py` still FAILs LIST-202/203.
- **ACP-LIST-204**: citation-only. "Always an absolute path" moved from SL:115-117 to SL:118-120, unchanged. `#/$defs/SessionInfo/properties/cwd` is still an `AbsolutePath`. The `overview.mdx:188` part is now `overview.mdx:218` ("All file paths in the protocol **MUST** be absolute ..."), but that doc belongs to another researcher.
- **ACP-RESUME-202** (session-list part only): citation-only. Base SL:197-198 ("Agents typically send this notification after the first meaningful exchange to auto-generate a title") is now SL:204-205, verbatim. SL:162 adds a SHOULD to send `session_info_update` "on each connection where the session is active", and SL:207 repeats it. Both are consistent with the row's "`session_info_update` ... may legitimately follow and are not judged". No test change from this doc.

### 2. session-delete.mdx: existing rows

The diff is in "Semantics" (SD:88-95). Two "implementation-defined" bullets (base :93-94) became normative:

- SD:92 "Clients **SHOULD** treat a `-32002` response to `session/delete` as a successful delete."
- SD:94 "Later requests for a deleted session, including `session/resume`, fail with `-32002`." This links to `error.mdx#unknown-sessions`, where error.mdx:54 is a MUST and :56 lists "`session/resume` of a session that does not exist or was deleted".
- SD:95 "If the session is active on any connection, the Agent **MUST** cancel its ongoing work and free its resources as if `session/close` had been called, then delete it."
- `session-setup.mdx:49` agrees: "Agents **SHOULD NOT** discard a session while it is active, except through `session/delete`, which closes it first."
- The heading-case changes ("Checking support", "Deleting a session") do not affect the TCK.

- **ACP-DELETE-201**: changed text and test. DECISION NEEDED.
  - The current text says the session "is closed first because deleting an active session is implementation-defined". That is false at target; SD:95 defines it. The current base cite :94 was exactly that sentence; at target :94 is the `-32002`-after-delete bullet.
  - There is a new false-FAIL risk. The test creates a session, never prompts it, closes it, then deletes it. `session-setup.mdx:47` lets an agent not store "a session that was never prompted", and :52 says retention after close is up to the agent. Such an agent may have discarded the session, so the delete targets a session that "does not exist". The agent then SHOULD succeed (SD:91), may answer `-32002`, and clients SHOULD treat that as success (SD:92, error.mdx:56). DELETE-201 would FAIL a conforming agent that only bent a SHOULD.
  - **Recommendation:** delete an *active, idle* session directly, with no close first. It certainly exists, so SD:78-86 ("On success, the Agent returns an empty result") plus SD:95 make success mandatory.
  - Proposed text: "`session/delete` of a session active and idle on this connection succeeds with a schema-valid empty-object result (deleting an active session closes it first, SD:95)."
  - Citation: `session-delete.mdx:35,57,78-86,95; session-setup.mdx:49; #/$defs/DeleteSessionResponse`.
  - Alternative: keep close-then-delete, but accept `-32002` as PASS when the closed session is no longer listed, and require `{}` only when it is still listed. This is more complex and still a weaker probe.
  - The `_base` fixture already returns `{}` for an active session. `advertises_delete_but_errors.py` still FAILs it.
- **ACP-DELETE-202**: changed test; citation update.
  - SD:90 ("Deleted sessions no longer appear in future `session/list` results") is unchanged.
  - Test change: when the delete response is a `-32002` error, proceed as if it succeeded (SD:92) and still judge the follow-up list. Any other error remains a cascade FAIL. The SKIP gate ("not listed in the first place") stays.
  - Under recommendation 201, also consider deleting the session while it is active rather than closed. The SKIP gate covers agents that don't list never-prompted sessions. Consider prompting it once first, so it is more likely to be stored and listed and the test is less often vacuous.
  - Drop `:94` from the citation (its meaning moved) and add `:92`: `session-delete.mdx:27-28,90,92`.
  - Fixture `advertises_delete_but_errors.py` returns `-32603`, so it still FAILs 201/202/203 exactly. The `test_cli.py:2292` expectation is unchanged.
- **ACP-DELETE-203** (ADVISORY): unchanged. The SD:91 SHOULD is verbatim at the same line. error.mdx:56 restates it ("Agents **SHOULD** still return success when ... deleting one that does not exist").
  - Minor DECISION: should a `-32002` reply PASS, since clients tolerate it? Recommendation: no. The agent-side SHOULD is to succeed, and ADVISORY never affects the verdict. Change only the failure message, so it says that `-32002` is the client-tolerated deviation and that other codes are worse.
  - Add `docs/protocol/v2/draft/error.mdx:56` to the citation.

### 3. session/fork: ACP-FORK-201/202 repoint

There is no `session-fork.mdx` draft doc. At target, the draft tree states fork rules in these places:

- `initialization.mdx:269-273`: "**Unstable.** The `session/fork` method is available. ... Supplying an empty object means the Agent supports forking sessions."
- `session-setup.mdx:49`: "a session is **active** from a successful `session/new`, `session/resume`, or, when supported, `session/fork` (for the new session) until `session/close` or the end of the connection."
- `error.mdx:54`: "A session is active once it is created, resumed, or forked on the connection".
- `error.mdx:64`: "`session/fork` of a session that does not exist gets `-32002` ... The source session only has to exist. It doesn't have to be active on the connection."
- `overview.mdx:256`: the optional-methods table row.
- In the generated `schema.mdx`, the fork section is now :753-771 (base :605-624). "Forks an existing session to create a new independent session" is :760, and "the forked session is active once the agent responds ... can prompt it without calling `session/resume` first" is :768-770.
- `#/$defs/ForkSessionResponse/properties/sessionId`: "Unique identifier for the newly created forked session." `ForkSessionRequest`/`ForkSessionResponse` changed only in descriptions and `x-deserialize-*` hints (inventory Appendix B), and the shapes are unchanged.
- `docs/rfds/session-fork.mdx:67` is unchanged in the range (no diff).

Changes to the rows:

- **ACP-FORK-201**: replace `docs/protocol/v2/draft/schema.mdx:614-624` with `docs/protocol/v2/draft/initialization.mdx:269-273; docs/protocol/v2/draft/session-setup.mdx:49; schema/v2/schema.unstable.json#/$defs/ForkSessionResponse/properties/sessionId`. Keep the existing `#/$defs/ForkSessionResponse` and `#/$defs/SessionCapabilities/properties/fork`. The text and test are unchanged. "Newly created" supports the "distinct from the source" assertion.
- **ACP-FORK-202**: replace `docs/protocol/v2/draft/schema.mdx:622-624` with `docs/protocol/v2/draft/session-setup.mdx:49; docs/protocol/v2/draft/error.mdx:54`. Keeping `docs/rfds/session-fork.mdx:67` is optional, since it is now redundant.
  - Update the rider "Definitional prose without an RFC keyword". It is still definitional (bold "**active**"), but it now lives in the draft docs. error.mdx:51-54 also makes the consequence normative: non-active sessions get `-32002`, so an active forked session must be accepted.
  - Text and test are unchanged. `fork_session_not_active.py` still FAILs exactly FORK-202.
- `spec-impact --fix` would only remap the `schema.mdx` line numbers mechanically. The repoint above has to be done by hand. Note that `schema.mdx` is generated, and the TCK's convention elsewhere prefers JSON-Pointer and draft-doc citations.

New fork rows:

- **ACP-FORK-203** (new): CAPABILITY, `capabilities.session.fork`.
  - Text: "`session/fork` of a `sessionId` the agent never created is answered with `-32002`."
  - Citation: `docs/protocol/v2/draft/error.mdx:54,64 @ 3961af94fa62`.
  - Observable: fork `"tck-never-created"` with `cwd = tmp_path` and expect `error.code == -32002`. The `data.sessionId` check belongs to whoever owns error.mdx:54's typed-data rule.
  - The **conforming `_base` fixture currently returns `-32602`** for an unknown source (`_base.py:417-419`) and must change to `-32002` with `data: {sessionId}`.
  - Suggested defect fixture: `fork_unknown_source_invalid_params.py` (keeps `-32602`; FAILs exactly FORK-203).
- **ACP-FORK-204** (new, optional, low priority): CAPABILITY, `capabilities.session.fork`.
  - Text: "`session/fork` of an existing session that is not active on the connection (created, then closed, and still listed by `session/list`) succeeds with a new `sessionId`."
  - Citation: `error.mdx:64; session-setup.mdx:52`.
  - SKIP when the closed session isn't listed (existence unknowable).
  - The `_base` fixture already supports it (`_closed_sessions`).
  - Suggested defect fixture: `fork_requires_active_source.py`.

Adjacent fork rules owned by the session-setup researcher (not judged here):
- `session-setup.mdx:49`: a fork starts with `background: []`.
- `:108,140`: the fork response MUST carry `configOptions`/`availableCommands`; fork commands are the new session's.
- `:416`: `additionalDirectories` not inherited.
- `:549`: `mcpServers` not inherited.
- `:478-481`: `systemPrompt` on fork.

### 4. New rows for list and delete, and the unstable methods

#### New rows for list and delete

- **ACP-LIST-205**: CAPABILITY, `capabilities.session`.
  - Text: "`session/list` with a relative `cwd` filter is rejected with `-32602`."
  - Citation: `docs/protocol/v2/draft/session-list.mdx:64-65; docs/protocol/v2/draft/error.mdx:48 @ 3961af94fa62`.
  - Tier: the sentence is a declarative "Agents reject", with no RFC keyword. It is the same kind of plain agent-behavior statement the registry already treats as CAPABILITY (DELETE-202's rider). error.mdx:48 ("Malformed parameters and unsupported values get `-32602`") backs it.
  - Probe: `{"cwd": "relative/dir"}`. The TCK breaks a client "Must be an absolute path" rule here, but the spec defines the rejection for exactly that input, which follows the precedent of ACP-RESUME-208's malformed-`replayFrom` probe. Note the probe fails schema validation (`AbsolutePath`), so the TCK must send it raw, not through a validating builder.
  - Fixture: **`_base` must add** the `-32602` check. Defect fixture: `list_accepts_relative_cwd.py`.
- **ACP-LIST-206**: CAPABILITY, `capabilities.session`. DECISION NEEDED: CAPABILITY or ADVISORY.
  - Text: "`session/list` with a `cursor` the agent never issued is rejected with `-32602`."
  - Citation: `session-list.mdx:157; error.mdx:48`. The rule moved from "Agents **SHOULD** return an error" to "Agents **MUST** return `-32602` if the cursor is invalid".
  - Probe: `cursor: "tck-invalid-cursor-<uuid4>"`. Never use `""`, which SL:154 makes a valid cursor.
  - The risk: cursors are opaque, and validity is agent-defined. An agent whose cursor encoding accepts any string (for example a lexicographic lower bound on session id) has no invalid cursors, and the probe would false-FAIL it. Recommendation: CAPABILITY. SL:72 defines a cursor as a token "from a previous response's `nextCursor`", so a fabricated, never-issued token is invalid under every reading. Typical encodings (base64 JSON, opaque ids) reject it. If the orchestrator wants zero false-FAIL risk, use ADVISORY.
  - Fixture: `_base` never issues cursors, so it **must** reject any non-null `cursor` with `-32602`. That does not affect `_route_from_list`, which only forwards an issued `nextCursor`. Defect fixture: `list_ignores_invalid_cursor.py`.
- **ACP-DELETE-204**: CAPABILITY, `capabilities.session.delete`.
  - Text: "`session/delete` of a session with foreground work in flight cancels that work as if `session/close` had been called: the idle `state_update` with `stopReason: \"cancelled\"` for that session arrives before the successful delete response."
  - Citation: `session-delete.mdx:95; session-setup.mdx:391,393 @ 3961af94fa62`. :393 is close's own MUST ordering, carried over by "as if `session/close` had been called".
  - Observable: mirror `test_cancel.py::test_close_cancels_foreground_work` and CLOSE-203. Start a `--cancel-prompt` turn and wait for `running`, then send `session/delete`. Use the same cancel-race SKIP ("cancellation not exercised") when the turn ends on its own.
  - It could be split into a "cancelled" row and an "ordering" row like CLOSE-202/203. One row is enough unless report legibility argues otherwise.
  - Fixture: **`_base._handle_delete_session` must change** to call `_finish_turn(session_id, "cancelled")` for a hanging session before replying, as `_handle_close_session` does. Its comment "no cancellation side effect" is now wrong. Defect fixture: `delete_does_not_cancel_active.py` (today's behavior).
- **ACP-DELETE-205**: CAPABILITY, `capabilities.session.delete`.
  - Text: "After a successful `session/delete`, `session/resume` of that `sessionId` (same `cwd`) is answered with `-32002`."
  - Citation: `session-delete.mdx:94; error.mdx:54-56; session-setup.mdx:47`. error.mdx:54 is the MUST, and :56 says "applies ... to `session/resume` of a session that does not exist or was deleted".
  - Observable: new session, delete (or close then delete), then resume with the same `cwd`. Expect `error.code == -32002`. A success result is FAIL.
  - Coordinate with the error.mdx researcher: they may propose a generic unknown-session row (and `data.sessionId`). This row is the delete-specific instance; dedupe if needed.
  - Fixture: **`_base._handle_resume_session` accepts any `sessionId`** on purpose, so that `obtain_resumable_session` routes succeed. It must keep a `_deleted` set and return `-32002` with `data: {sessionId}` for those ids only. Defect fixture: `resume_after_delete_succeeds.py`.

#### Unstable methods: CAPABILITY now, or ledger/deferral? DECISION NEEDED

What the spec says about each:

- **`session/archive` / `session/unarchive`** (RFD `docs/rfds/session-archive.mdx`, Draft) are specified **in the draft protocol doc itself** (SL:218-252), with several MUSTs. The schema `$defs` repeat them: `ArchiveSessionRequest`, `UnarchiveSessionRequest`, `SessionArchiveFilter`, `SessionInfo/properties/archived`, `SessionCapabilities/properties/archive`. initialization.mdx:261-267 and error.mdx:66 back them. This is the same footing as `session/fork` and `systemPrompt`, which the registry already covers as CAPABILITY.
- **`session/status`** and **`session/set_title`** have no draft-doc section. Their rules live in the RFDs, the schema `$def` descriptions (`SessionStatusRequest`/`Response`, `SessionStatus`, `SetSessionTitleRequest`/`Response`), and one bullet each in `error.mdx:65,67`. Their capability entries are in `initialization.mdx:275-287`.

Recommendation:
- Archive: register CAPABILITY rows now; it is specified in the draft doc.
- Status and title: register a minimal CAPABILITY set (schema-valid success, `-32002` for unknown, title `-32602` for empty), citing schema JSON-Pointers and `error.mdx:65,67`, not RFDs.
- If the orchestrator wants to bound this update, defer status and title as one ledger entry each instead. For example: "out of scope for this update: unstable, RFD-only (Draft); revisit when a draft doc section exists".
- None of these trips existing fixtures, since `_base` answers unknown methods with `-32601` and advertises none of the capabilities. Each needs `_base` support plus `test_cli.py` conforming-set updates and one defect fixture per row.

Proposed archive rows. All are CAPABILITY, `capabilities.session.archive`, and cite `@ 3961af94fa62`.

| proposed id | text | citation | observation | defect fixture |
|---|---|---|---|---|
| ACP-ARCHIVE-201 | `session/archive` then `session/unarchive` of an existing session each succeed with a schema-valid empty result | SL:222; `#/$defs/ArchiveSessionResponse`; `#/$defs/UnarchiveSessionResponse` | new session, archive, unarchive | `archive_errors.py` |
| ACP-ARCHIVE-202 | Every `SessionInfo` in a `session/list` result carries a boolean `archived` | SL:245 (MUST); `#/$defs/SessionInfo/properties/archived` | list after creating a session; record the count (vacuous PASS if empty) | `archive_omits_archived_flag.py` |
| ACP-ARCHIVE-203 | An archived session is absent from default `session/list` results and present (with `archived: true`) under `archived: "only"` and `"include"`; after unarchive it is back in the default results | SL:222,237-241 | prompt once, then list (SKIP if not listed), archive, then list three ways; unarchive, then list | `archive_still_listed.py` |
| ACP-ARCHIVE-204 | `session/archive` and `session/unarchive` of a never-created `sessionId` get `-32002` (not silent success) | SL:251; error.mdx:66; `#/$defs/ArchiveSessionRequest` | probe `tck-never-created` | `archive_unknown_succeeds.py` |
| ACP-ARCHIVE-205 | An unsupported `archived` filter value is rejected with `-32602`, not treated as `exclude` | SL:243 (MUST); `#/$defs/SessionArchiveFilter` (MUST) | `archived: "_tck_unsupported"`, which is schema-valid via the open-enum `other` branch (as with RESUME-207) | `archive_filter_falls_back.py` |
| ACP-ARCHIVE-206 | `session/archive` of a session with foreground work in flight cancels it as if closed: the idle `stopReason: "cancelled"` arrives before the archive response | SL:247; `#/$defs/ArchiveSessionRequest` ("MUST cancel any ongoing work"); session-setup.mdx:393 | same race-aware pattern as DELETE-204 | `archive_does_not_cancel.py` |
| ACP-ARCHIVE-207 (optional) | Archiving an archived session, and unarchiving a non-archived one, succeed | SL:251 | archive twice; unarchive a fresh session | `archive_not_idempotent.py` |

If `capabilities.session.delete` is also advertised, an eighth row could check SL:252: "Deleted sessions are excluded from every filter value". The RFD's :178 MUST says not to implement delete as archive. That row needs a two-capability gate; I recommend folding it into ARCHIVE-203 as a conditional sub-check, or skipping it.

Proposed status and title rows (if not deferred). All are CAPABILITY.

| proposed id | gate | text | citation | observation |
|---|---|---|---|---|
| ACP-STATUS-201 | `capabilities.session.status` | `session/status` of a session active on this connection succeeds with a schema-valid result (record `status`) | `#/$defs/SessionStatusRequest`; `#/$defs/SessionStatusResponse`; initialization.mdx:275-279 | new session, then status. Asserting `"open"` is **not** recommended: it is definitional (`#/$defs/SessionStatus` "in memory"), not a MUST. Record it instead. |
| ACP-STATUS-202 | `capabilities.session.status` | `session/status` of a never-created `sessionId` gets `-32002` with `data.sessionId` equal to the requested id | error.mdx:65; `#/$defs/SessionStatusRequest` | probe `tck-never-created` |
| ACP-STATUS-203 (optional, ADVISORY) | `capabilities.session.status` | An `open` result includes a schema-valid `state` | `#/$defs/SessionStatusResponse/properties/state` ("Agents SHOULD include it when `status` is `open`") | same probe as 201 |
| ACP-TITLE-201 | `capabilities.session.title` | `session/set_title` with a non-empty title on an existing session succeeds with a schema-valid result carrying a string `title` | `#/$defs/SetSessionTitleRequest`; `#/$defs/SetSessionTitleResponse` | new session, then set_title "TCK title" |
| ACP-TITLE-202 | `capabilities.session.title` | `session/set_title` of a never-created `sessionId` gets `-32002` | error.mdx:67; `#/$defs/SetSessionTitleRequest` | probe |
| ACP-TITLE-203 | `capabilities.session.title` | `session/set_title` with `title: ""` is rejected with `-32602` | error.mdx:67; `#/$defs/SetSessionTitleRequest/properties/title` ("rejects ... one that is empty after normalization, with `-32602`") | probe; `""` is schema-valid (plain `string`) |

The status "no side effects" MUST (`#/$defs/SessionStatusRequest`) is only partly observable. It needs a second connection and cross-connection persistence: status from connection B, then `session/prompt` from B must get `-32002`. I recommend leaving it out, or adding it to the ledger as impractical.

### 5. Ledger candidates (`[[not_requirement]]`)

| citation | statement | reason |
|---|---|---|
| `docs/protocol/v2/draft/session-list.mdx:158 @ 3961af94fa62` | Agents SHOULD enforce reasonable page sizes internally. | unobservable: no defined bound. |
| `docs/protocol/v2/draft/session-list.mdx:162 @ 3961af94fa62` | Agents SHOULD send `session_info_update` on each connection where the session is active whenever session metadata changes. | unobservable: the client cannot trigger or detect a metadata change (except via `session/set_title`, whose follow-up notification the RFD only makes MAY). |
| `docs/protocol/v2/draft/session-list.mdx:243 @ 3961af94fa62` | The `archived` filter combines with `cwd` and applies before pagination. | impractical: needs an agent holding more than one page of sessions in a TCK-owned `cwd`. (The `cwd` combination is partly exercised if ARCHIVE-203 passes `cwd`.) |
| `docs/protocol/v2/draft/session-list.mdx:249 @ 3961af94fa62` | Archive state persists across connections and restarts; closing, loading, or resuming does not change it. | out of scope for the restart part (the TCK does not restart agents). The cross-connection part could later be a row. |
| `docs/protocol/v2/draft/session-delete.mdx:92 @ 3961af94fa62` (and `session-list.mdx:154-156`) | Clients SHOULD treat `-32002` on `session/delete` as success; clients MUST treat only an omitted or `null` `nextCursor` as end of results, MUST NOT assume a fixed page size, and MUST treat cursors as opaque. | client-side rules. The TCK honours them in its own driving (DELETE-202 change; harness fix below) and asserts nothing about them. |

### 6. Harness bug (not a requirement)

`src/tck/v2/conformance/_helpers.py:415-417` (`_route_from_list`):

```python
cursor = result.get("nextCursor")
if not isinstance(cursor, str) or not cursor:
    break
```

`not cursor` ends pagination on `""`. Target SL:154 says "Only an omitted or `null` `nextCursor` ends the results. An empty string is a valid cursor", and the schema `#/$defs/ListSessionsResponse/properties/nextCursor` says "An empty string is a valid cursor, not the end of results". The fix is to break only when `cursor` is `None` or not a string. The `_LIST_ROUTE_MAX_PAGES` cap already guards against loops.

### 7. Wire changes (inventory B1-B12 and Appendix B) touching these rows

- `ListSessionsRequest.archived` and `SessionInfo.archived`: both are additive and optional (`boolean|null`). They don't affect existing rows. A non-archive agent omits them.
- `ForkSessionRequest`: `x-deserialize-default-on-null` hints only.
- `ListSessionsResponse.nextCursor`: lost a deserialize hint and gained description text; no structural change.
- No B-row breaks LIST, DELETE, or FORK schema validation, and the vendored-schema refresh needs no carve-out for them.

## Testability notes

- **LIST-205/206, FORK-203, ARCHIVE-204/205, STATUS-202, TITLE-202/203** are single request/response probes on unknown ids or bad params. They are cheap and deterministic. A conforming agent returns the stated error code. A non-conforming one returns a result or a different code.
- **DELETE-204 and ARCHIVE-206** need a long-running turn. Reuse `--cancel-prompt` and the CLOSE-202/203 race-aware pattern. Some real-agent runs SKIP as "cancellation not exercised".
- **DELETE-202, ARCHIVE-203, FORK-204** depend on the agent listing a TCK-created session. They SKIP when it doesn't, which is legal because retention is agent-defined (`session-setup.mdx:47,52`). Prompting the session once first makes listing more likely.
- **DELETE-205** works against any agent that implements delete. It needs no listing.
- **Unobservable:** freeing resources (SD:95 "free its resources"), soft or hard delete (SD:93), and restart persistence.

## Discrepancies

- **Delete of a non-existent session: "SHOULD succeed silently" (SD:91, error.mdx:56) vs. "Later requests for a deleted session ... fail with `-32002`" (SD:94).** These are consistent: :94 applies to *other* methods, and `session/delete` is the listed exception (error.mdx:56). A re-delete is still SHOULD-succeed. No conflict, but programmers should not read :94 as covering re-delete.
- **Unknown fork source:** the spec says `-32002` (error.mdx:64), but the TCK's own conforming fixture returns `-32602` (`_base.py:417-419`). That is a fixture defect, not a spec conflict.
- **DELETE-201's text vs. SD:95:** the registry text says "implementation-defined", but the target spec now defines the behavior. This is the stale rationale fixed in section 2.
- No spec vs. schema conflict found. The schema `$def` descriptions restate the SL archive MUSTs and SL:64-68 cwd text consistently.

## Open questions

- error.mdx owner: will there be a generic "unknown or non-active session gets `-32002` with `data.sessionId`" row? If so, DELETE-205, FORK-203, ARCHIVE-204, STATUS-202, and TITLE-202 could reuse its assertion helper, or be folded into it. Dedupe before numbering.
- session-setup owner: fork-specific setup rules (`session-setup.mdx:49` `background: []`, :108/:140 `configOptions`/`availableCommands` on the fork response, :416, :549) are not judged here.
- security.mdx owner: `security.mdx:58` (multi-user scoping of `session/list`/`session/delete`/`session/fork`) is not judged here.
- The overview.mdx owner should confirm LIST-204's `overview.mdx:188 -> :218` remap.
