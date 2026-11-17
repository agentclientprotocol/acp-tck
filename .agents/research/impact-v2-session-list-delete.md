# Impact v2: `session-list.mdx` (with archive) and `session-delete.mdx`, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133` (read with `git show 3ea94133:<path>`; the checkout's HEAD
is `6ace4f6a`, and none of the files below differ between the two):
`docs/protocol/v2/draft/session-list.mdx`, `session-delete.mdx`, `error.mdx`, `session-setup.mdx`, `overview.mdx`,
`subagents.mdx`, `initialization.mdx`, `docs/rfds/session-archive.mdx` (Draft RFD), `docs/rfds/subagents.mdx`
(Preview RFD), `docs/rfds/session-set-title.mdx` (Draft RFD), `schema/v2/schema.unstable.json` (`SessionCapabilities`
property keys). TCK: `src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`,
`src/tck/v2/conformance/test_session_capabilities.py`, `test_subagents.py`, `_helpers.py`.
I did not need the reference SDKs. The new rule is explicit.
**Confidence:** high. `session-list.mdx` has one changed line (line 6, replaced in place, so no line shifts) and
`session-delete.mdx` is unchanged. The only real work is the line shifts in docs that co-cited rows point at
(`error.mdx`, `session-setup.mdx`, `overview.mdx`).

## Diffs

- `session-list.mdx:6`: appends "It does not return [child sessions](/protocol/v2/draft/subagents), which the Agent
  announces on their parent session." No other change, and every other line keeps its number.
- `session-delete.mdx`: no change.
- `session-archive.mdx` (Draft RFD, Draft at both revisions): a typo fix at :183 only. `:112` is unchanged.
- Shifts in co-cited docs: `error.mdx` gains 2 lines at 58-59, so `:65`->`:67` and `:66`->`:68`, while `:48,54,56`
  keep their numbers. `session-setup.mdx`: `:49`->`:50`, `:391`->`:476` (with changed text, see the ledger row),
  `:393`->`:478`, `:395`->`:480`. `overview.mdx:218`->`:222` (same text).
- Schema: none of `ListSessions*`, `SessionInfo`, `DeleteSession*`, `ArchiveSession*`, `UnarchiveSession*` or
  `SessionArchiveFilter` changed. `SessionCapabilities` only gains `options`.

## `docs/protocol/v2/draft/session-list.mdx`

| id / ledger citation | classification | target citation (@ 3ea94133) | note |
|---|---|---|---|
| ACP-LIST-001 | unchanged | `session-list.mdx:10,76,111` | |
| ACP-LIST-002 | unchanged | `:148` | |
| ACP-LIST-203 | unchanged | `:63-69` | |
| ACP-LIST-204 | citation-only change | `:118-120`; **`overview.mdx:222`** (was `:218`) | The overview text is identical. |
| ACP-LIST-205 | unchanged | `:64-65`; `error.mdx:48` | |
| ACP-LIST-003 | unchanged | `:157`; `error.mdx:48` | Test docstrings cite `:154` for the empty-string cursor, which is still correct. |
| ACP-LIST-207 | unchanged | `:64-65`; `error.mdx:48` | |
| ACP-RESUME-202 (co-cites) | unchanged for this doc | `:204-205` | Its `session-setup`/`prompt-lifecycle` lines belong to those docs' researchers. |
| ACP-ARCHIVE-002 | unchanged | `:245` | |
| ACP-ARCHIVE-003 | unchanged | `:222,237-241`; `rfds/session-archive.mdx:112 (Draft RFD)` | The label is still correct. The docs do not state "MUST support all three values", so the Draft RFD citation is still the only source and stays. |
| ACP-ARCHIVE-004 | citation-only change | `:243`; **`error.mdx:68`** (was `:66`) | |
| ACP-ARCHIVE-005 | citation-only change | `:251`; `error.mdx:54`, **`:68`** (was `:66`) | Also fix the prose citation in the `test_session_capabilities.py:1499` docstring (`error.mdx:54,66` -> `54,68`). |
| ACP-ARCHIVE-006 | unchanged | `:252`; `rfds/session-archive.mdx:112 (Draft RFD)` | |
| ACP-ARCHIVE-201 | citation-only change | `:247`; **`session-setup.mdx:478,480`** (was `:393,395`) | The session-setup text is unchanged. |
| ledger `setup:391; delete:95; list:247` (closing, deleting or archiving frees resources) | citation-only change for my lines; **co-cited text changed** | `session-setup.mdx:476`; `session-delete.mdx:95`; `session-list.mdx:247` | Line 476 now also says "Clients SHOULD dismiss ..." (a client rule) and "Closing also stops the session's child sessions, at any depth". Deleting and archiving act "as if `session/close`", so they now stop children too. Whether that becomes a row belongs to the session-setup and subagents researchers (see Open questions). The reason does not rest on a TCK choice. |
| ledger `list:158` (page sizes) | unchanged | `:158` | |
| ledger `list:162` (`session_info_update` SHOULD) | unchanged text; **reason flagged** | `:162` | See D2. |
| ledger `list:243` (filter combines with `cwd`, before pagination) | unchanged | `:243` | The reason is fine. Note that `_list_view` already sends `cwd` together with `archived`. |
| ledger `list:248` (unarchive never loads/resumes) | unchanged text; reason weak | `:248` | See D3. |
| ledger `list:249` (archive state persists) | unchanged text; **reason flagged** | `:249` | See D4. |
| ledger `error:65; list:250; rfds/session-status:126,130 (Draft RFD); SessionStatusRequest` | citation-only change | **`error.mdx:67`** (was `:65`); `session-list.mdx:250` unchanged | The session-status researcher owns the reason, which names TCK progress ("not yet tested"), as v1's D2 found. |

## `docs/protocol/v2/draft/session-delete.mdx`

| id / ledger citation | classification | target citation (@ 3ea94133) | note |
|---|---|---|---|
| ACP-DELETE-001 | citation-only change | `session-delete.mdx:35,57,78-86,95`; **`session-setup.mdx:50`** (was `:49`) | The session-setup text is unchanged. |
| ACP-DELETE-003 | unchanged | `:27-28,90,92` | |
| ACP-DELETE-002 | unchanged | `:91`; `error.mdx:56` | It probes a never-created id, so the new child-session exception (`subagents.mdx:380`, `error.mdx:58-59`) does not touch it. |
| ACP-DELETE-204 | citation-only change | `:95`; **`session-setup.mdx:478,480`** (was `:393,395`) | |
| ACP-DELETE-205 | unchanged | `:92,94`; `error.mdx:54,56` | |
| (no ledger entry cites only this doc) | | | `:93` ("may implement soft delete or hard delete") is a pure MAY, so it is not ledger material. |

## New requirements

1. **Provisional `ACP-LIST-2xx` (or `ACP-SUBAGENT-2xx`, see D1): `session/list` does not return child sessions.**
   - Text: "No `SessionInfo.sessionId` in a `session/list` result is the ID of a child session the agent announced
     with `subagent_update` on this connection. A Client learns of children only from `subagent_update`."
   - Citation: `docs/protocol/v2/draft/session-list.mdx:6; docs/protocol/v2/draft/subagents.mdx:381` @ 3ea94133.
     Secondary, optional: `docs/rfds/subagents.mdx:1098-1100 (Preview RFD)`. The docs state the rule twice, so the
     docs govern and the tier is not capped.
   - Tier: **CAPABILITY**. The sentence is declarative, with no RFC keyword. It is the same kind of plain statement
     of what the method returns as `ACP-DELETE-003` (`:90`), which the TCK holds at CAPABILITY.
   - Gate: there are two conditions. `capabilities.session` makes `session/list` MUST-supported (`:10`), and an
     announced child is the `inferred:subagents` condition. Recommended:
     `capability="inferred:subagents"`, matching the other subagent rows. The test self-SKIPs when no child was
     announced. `capabilities.session` is already enforced by the shared connection
     (`v2_only_agent(require_session=True)`, `_helpers.py:590-603`). The alternative is
     `capability="capabilities.session"` with a self-SKIP on "no child", like `ACP-ARCHIVE-006`. See D1.
   - Test approach: reuse `test_subagents.py`'s one shared connection (`_connection_transcript`: `session/new`, one
     prompt turn with `--subagent-prompt`, quiet period). Before the context manager closes the agent, while the root
     session is still active, send `session/list` with `params: {}`. Follow `nextCursor` for a bounded number of
     pages, as `_list_view`/`_route_from_list` do. Record the result in the stash. The test collects the child IDs
     with the existing `child_session_traffic(...)` / `subagent_update` parsing. It SKIPs when there are no
     children, FAILs when any listed `sessionId` is a child ID, and FAILs when `session/list` errors (that is the
     `ACP-LIST-001` concern, so arguably it should SKIP and point there). A per-entry negative check only, bounded by
     the pages read.
   - Harness needs: one change to the shared `_connection_transcript`. It must issue the `session/list` call(s)
     before leaving `v2_only_agent`, and cache the list results apart from (or appended after) the judged transcript.
     The list call comes after the quiet period, so it does not perturb the rows that judge turn and quiet-period
     traffic. Still, check that no row treats "any traffic after the quiet period" as a violation. The mock client
     needs nothing new.
   - Ownership: `subagents.mdx:381` states the same rule, so the v2 subagents researcher may propose it too. File
     one row only.

No other new requirements. `session-delete.mdx` is unchanged, and the archive section is unchanged at the target.

## New ledger entries

None.

## Cross-references (rules owned by other docs' researchers, not filed here)

- `subagents.mdx:380` and `error.mdx:58-59`: agents SHOULD reject `session/delete` (and `session/close`) of a child
  with `-32602`, and these "do not report success for a child". This is an exception next to `session-delete.mdx:91`.
  It would be ADVISORY, behind `capabilities.session.delete` plus a child self-SKIP.
- `session-setup.mdx:476`: closing stops child sessions at any depth. Through `session-delete.mdx:95` and
  `session-list.mdx:247`, delete and archive of an active parent do too.

## Decisions for the user

- **D1. Gate and family for the new child-listing row.** Recommendation: `ACP-LIST-2xx` with
  `capability="inferred:subagents"`. It lives in `test_subagents.py` because it needs that shared connection. The
  id-alignment step can pair it with v1's equivalent, which the v1 researcher left to the subagents researcher.
- **D2. Ledger `session-list.mdx:162` reason rests on a TCK choice.** It says the only client-driven metadata change,
  `session/set_title`, "is deferred" (a TCK backlog fact). It also says the follow-up is "only a MAY in the RFD", but
  `:162` (docs) says agents SHOULD send `session_info_update` for metadata changes "including changes requested by a
  Client". Docs govern over the Draft RFD's MAY (`rfds/session-set-title.mdx:156`). This is a discrepancy, and the
  current reason is built on the weaker source. The rule is observable when the agent advertises
  `capabilities.session.title` (`initialization.mdx:361-366`): call `session/set_title` on the active session and
  expect a `session_info_update` on it. Recommendation: rewrite the reason as "Deferred: observable only through
  `session/set_title` on an agent advertising `session.title`. The TCK has no `session/set_title` support (unstable
  method, Draft RFD). Agent-generated title changes cannot be triggered or detected." Optionally add an ADVISORY row
  later that SKIPs without `session.title`.
- **D3. Ledger `session-list.mdx:248` (unarchive never loads/resumes): the reason understates observability.** There
  is a positive check: archive closes the session (`:247`), and after unarchive a `session/prompt` on it must get
  `-32002`, because it is not active on the connection (`error.mdx:54`, a MUST). A success shows the session was
  loaded. Recommendation: keep it Deferred for this update (the text is unchanged), but rewrite the reason to name
  this probe, or add a CAPABILITY row (`capabilities.session.archive`) later. Low priority.
- **D4. Ledger `session-list.mdx:249` (archive state persists) rests on a TCK choice** ("the TCK does not restart
  agents"). This mirrors v1's D1. The "closing, loading or resuming does not change it" half is observable on one
  connection. Archive the session, which closes it, then `session/resume` it. Agents MAY reject that (`:248`), so a
  rejection SKIPs. If the resume is accepted, the session must still appear under `archived: "only"`. Recommendation:
  mark the entry "Deferred" with the real blocker for the persistence half (no harness support for restarting the
  agent mid-test, and an ephemeral store gives an inconclusive result). Optionally add a SKIPpable CAPABILITY row for
  the resume half. Low priority.

## Discrepancies

- `session-list.mdx:162` (SHOULD notify, including Client-requested changes) vs `rfds/session-set-title.mdx:156`
  (Draft RFD: MAY notify, and only if the session is loaded). The docs govern. This affects only the ledger reason (D2).
- Otherwise none found. `session-list.mdx:6` and `subagents.mdx:381` agree, and the subagents RFD (Preview) agrees
  at `:1098-1100`.

## Open questions

- Should "deleting or archiving an active parent stops its child sessions" (`session-setup.mdx:476` with
  `session-delete.mdx:95` / `session-list.mdx:247`) get delete/archive rows? Route it to the session-setup or
  subagents researcher alongside any `session/close` child-stopping row.
