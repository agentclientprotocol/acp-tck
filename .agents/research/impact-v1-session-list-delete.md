# Impact research (v1): `session-list.mdx`, `session-delete.mdx`, and the `ACP-ARCHIVE-*` rows

**Sources checked:** agent-client-protocol, base `3961af94` and target `3ea94133`, via `git show`/`git diff` in
`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`. Files: `docs/protocol/v1/draft/session-list.mdx`,
`docs/protocol/v1/draft/session-delete.mdx`, `docs/protocol/v1/draft/error.mdx`, `docs/rfds/session-archive.mdx`,
`docs/protocol/v1/draft/subagents.mdx` (linked rules only), `docs/protocol/v1/draft/session-setup.mdx` (the hunk
behind the `#loading-sessions` link), `docs/docs.json` (RFD stages), `schema/v1/schema.unstable.json`, compared `$def`
by `$def`. acp-tck: `src/tck/v1/requirements.py`, `spec-tracker/maps/v1.toml`. I did not consult the SDKs because no
rule here changed.
**Confidence:** high. Both docs are byte-identical between base and target. The only RFD change is a typo. Every
schema `$def` these rows cite is unchanged, and the one changed `$def` (`SessionCapabilities`) only gains `options`.

## Summary of upstream changes that touch these rows

- `session-list.mdx`, `session-delete.mdx`: no diff (`git diff --stat 3961af94..3ea94133` is empty for both).
- `docs/rfds/session-archive.mdx`: one typo fix at line 183 ("How will things will play out" becomes "How will things
  play out"). Line 112 (cited) is unchanged. The stage is Draft at both revisions (`docs/docs.json` @ 3ea94133). The
  `rfds/session-list` and `rfds/session-delete` RFDs are Completed.
- `schema/v1/schema.unstable.json`: `ListSessionsRequest`, `ListSessionsResponse`, `SessionInfo`,
  `DeleteSessionRequest`/`Response`, `ArchiveSessionRequest`/`Response`, `UnarchiveSessionRequest`/`Response`,
  `SessionArchiveFilter`, `SessionListCapabilities`, `SessionDeleteCapabilities`, `SessionArchiveCapabilities` and
  `AgentCapabilities` are all unchanged. `SessionCapabilities` changed only by adding `properties.options` (the
  `session/options` capability). `properties.archive` is identical, so the inventory's flag on ACP-ARCHIVE-001 is
  closure noise.
- `docs/protocol/v1/draft/error.mdx`: a 2-line "Draft only" paragraph inserted at 57-58 (child sessions) shifts the
  "Unstable features" list by +2. `error.mdx:67` (cited by ACP-ARCHIVE-005) is now `:69`, and `error.mdx:66` (cited
  by the session-status ledger entry) is now `:68`. `error.mdx:47` is unchanged.

## `docs/protocol/v1/draft/session-list.mdx`

| id / ledger citation | classification | target citation (@ 3ea94133) | note |
|---|---|---|---|
| ACP-PROMPT-004 (its `session-list.mdx:136-137` part) | unchanged | `session-list.mdx:136-137` | `SessionInfo` unchanged. The other cited docs (overview.mdx and the `ToolCallLocation`/`Diff` schema pointers) are outside this brief. |
| ACP-LIST-001 | unchanged | `session-list.mdx:82,94`, schema pointers | |
| ACP-LIST-002 | unchanged | `session-list.mdx:84-87,166` | |
| ACP-LIST-003 | unchanged | `session-list.mdx:174`; `error.mdx:47` | error.mdx:47 did not move. |
| ACP-ARCHIVE-001 | unchanged | `session-list.mdx:229`; `#/$defs/SessionCapabilities/properties/archive` | `SessionCapabilities` only gained `options`. The `archive` property is identical. |
| ACP-ARCHIVE-002 | unchanged | `session-list.mdx:254` | |
| ACP-ARCHIVE-003 | unchanged | `session-list.mdx:231,244-250`; `docs/rfds/session-archive.mdx:112 (Draft RFD)` | The RFD changed only at line 183 (typo). The stage stays Draft. |
| ACP-ARCHIVE-004 | unchanged | `session-list.mdx:252` | |
| ACP-ARCHIVE-005 | citation-only change | `session-list.mdx:260`; **`error.mdx:69`** (was `:67`) | Shifted by the error.mdx:57-58 insertion. The text is unchanged. |
| ACP-ARCHIVE-006 | unchanged | `session-list.mdx:261`; `docs/rfds/session-archive.mdx:112 (Draft RFD)` | Same as ARCHIVE-003. |
| ledger `session-list.mdx:175` (page sizes) | unchanged | `:175` | |
| ledger `session-list.mdx:221` (list has no side effects) | unchanged | `:221` | |
| ledger `session-list.mdx:252` (filter before pagination) | unchanged | `:252` | |
| ledger `session-list.mdx:258` (archive state persists) | unchanged text; **reason flagged** | `:258` | See decision D1. |
| ledger `session-list.mdx:256` (archive of a loaded session acts as close) | unchanged | `:256` | The reason is "Deferred" and names a real blocker (race-prone in-flight prompt). |
| ledger `session-list.mdx:259; error.mdx:66; rfds/session-status.mdx:126,130 (Draft RFD); SessionStatusRequest` | citation-only change | `session-list.mdx:259`; **`error.mdx:68`** (was `:66`) | `session-status.mdx` is still a Draft RFD with untouched lines (inventory). The session-status researcher may also own this entry. Reason flagged lightly, see D2. |

## `docs/protocol/v1/draft/session-delete.mdx`

| id / ledger citation | classification | target citation (@ 3ea94133) | note |
|---|---|---|---|
| ACP-DELETE-001 | unchanged | `session-delete.mdx:69-81,85,87,90`; schema pointers | |
| ACP-DELETE-002 | unchanged | `session-delete.mdx:86` | See the cross-reference below on child sessions. The row probes a never-created id, so the new child exception does not affect it. |
| ACP-DELETE-003 | unchanged | `session-delete.mdx:85,87,90` | |
| (no ledger entries cite session-delete.mdx) | | | Nothing new to add: lines 88-90 are "implementation-defined"/"may", which are pure MAYs, not ledger material. |

## New requirements

None from these docs, which did not change.

New rules elsewhere at the target name `session/list` and `session/delete` directly. They are stated in
`subagents.mdx`/`error.mdx`, so the subagents and error.mdx researchers own them. I did not propose them here to
avoid double-filing:

- `docs/protocol/v1/draft/subagents.mdx:430 @ 3ea94133`: "`session/list` does not return child sessions." This is a
  docs rule with no keyword. It would be a CAPABILITY row gated on `sessionCapabilities.list` plus
  `inferred:subagents` (the test must self-SKIP unless the agent announced a child via `subagent_update`).
- `subagents.mdx:428` and `error.mdx:57`: agents SHOULD reject `session/delete` (and `session/close`) naming a child
  with `-32602`, and "do not report success for a child". This is an exception to the delete-succeeds-silently
  SHOULD (`session-delete.mdx:86`, `error.mdx:55`). It is ADVISORY, behind `sessionCapabilities.delete` and
  `inferred:subagents`.

## New ledger entries

None.

## Decisions for the user

- **D1. The ledger entry `session-list.mdx:258` rests partly on a TCK choice.** Its reason ("Out of scope for now:
  needs a two-process test ...") is not marked "Deferred". Persistence across connections and restarts becomes
  observable if the harness restarts the agent: archive, terminate, relaunch, list with `archived: "only"`. "Loading
  or resuming does not change it" is also observable on one connection: archive (which closes the session, line 256),
  then `session/load`/`session/resume` if advertised. A rejection is allowed (line 257) and SKIPs. If the call is
  accepted, the session must still be listed under `only`. Recommendation: relabel the reason "Deferred" and name the
  real blocker. That blocker is that the harness cannot yet restart the agent process mid-test, and an agent with an
  ephemeral store gives an inconclusive result. Optionally add a SKIPpable CAPABILITY row
  (`sessionCapabilities.archive` + `.list` + `loadSession`/`resume`) for the single-connection load/resume half. The
  line has no MUST/SHOULD, so it would be CAPABILITY like ARCHIVE-003 (an unconditional docs statement behind the
  feature's gate). This is low priority: the text is unchanged in this update.
- **D2. The session-status ledger entry's reason** ("Deferred unstable method: `session/status` is not yet tested")
  names TCK progress rather than an observability blocker. Its "MUST NOT have side effects" half is genuinely
  unobservable. The `saved` status and the `-32002` + `data.sessionId` answer are observable whenever the agent
  advertises `sessionCapabilities.status`. Recommendation: leave the wording to the session-status researcher. Here,
  only the citation fix `error.mdx:66` -> `:68` is required.
- **D3. (FYI, pre-existing, not caused by this update.)** ACP-ARCHIVE-005 says the error code "is not asserted", but
  `error.mdx:69` states `-32002` for archive/unarchive of a missing session. The general unknown-session rule
  (`error.mdx:53`) is SHOULD. No change is needed for this update. If wanted, a separate ADVISORY check on the code
  could follow later.

No test or harness changes are needed for these docs in this update. The only edits are the two `error.mdx`
line-number fixes (ACP-ARCHIVE-005 and the session-status ledger entry) and the pin bump on all citations.
