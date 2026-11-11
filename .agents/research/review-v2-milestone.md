# Review: v2 milestone (v2 schema 2.0.0-alpha.9 @ beac4ba9 -> 2.0.0-alpha.14 @ 3961af94), commits 7c76250^..2b8fe8c

Scope: 7c76250, the v2 parts of 4d88f27 (S-X1), 50b6270 and eb4e899, and 20dbf62, bb3576d, 9f6b05d,
bac245c, 6d61343, b4b8f49, 7f3ec77, d3b7027, f57c833, b19fb8c, c1c3a82, af82df6, 6cb9f0c, 8e6af34,
c5c6b1d, cab3724, 0da593d, 5bb7bfb and 2b8fe8c. I skipped the `chore: record` commits, the v1-only
commits, d28f79b and c1d4e23.

Method: I read the diffs and the code around them. I checked every new or changed v2 citation
against `git show 3961af94:...` in `../agent-client-protocol-2`, and checked all 93 S-v2-17
ledger entries' cited lines. The vendored v2 `schema.unstable.json` and `meta.unstable.json` match
`3961af94:schema/v2/` byte for byte. I judged against the "Decisions (final)" in `.agents/state.md`
and did not reopen them.

Runs:
- `uv run pytest tests/v2/test_registry.py tests/v2/test_open_enums.py tests/v2/test_run_prompt.py tests/common -q`: 195 passed.
- `uv run acp-tck --protocol-version 2 --timeout 3 -k test_initialize -- python tests/fixtures/agents/v2/custom_method_no_response.py`, for S1.
- A throwaway auth-gated archive fixture outside the repo, for S4.
- `pyright` on `src/tck/v2/conformance/_helpers.py` and `tests/v2/test_cli.py`, for known item 1.

I did not run the full suite. Checkpoint 4 at 5bb7bfb was green.

`.agents/` grep: `grep -rnE '\.agents/(research|state\.md|prompt\.md)' src tests cross-check spec-tracker`
has **no hits**. A broader `\.agents` grep finds only `cross-check/run.sh:27-28`, which read
`.agents/skills/check-*-sdk/.repo`. That predates this milestone, and S-XC/V2-D31 is set to remove it.

Counts: 0 blockers, 7 should-fix, 12 nits.

## Findings (most severe first)

### S1. ACP-FORK-205 requires the fork to keep the source's `availableCommands`, which the cited text says may differ. Should-fix. Confirmed by reading.
- **Where:** `src/tck/v2/requirements.py:1930-1945` (FORK-205) and `src/tck/v2/conformance/test_session_capabilities.py:1946-1974`.
- **Defect:** the test FAILs unless the fork result has a non-empty `availableCommands` whenever the source's `session/new` had one. But `session-setup.mdx:140`, which the row cites, says "For a fork, `availableCommands` advertises commands available in the newly created session, not the source session". The `:108` MUST binds only lists the *new* session has. The row text itself admits the premise is inferred.
- **Failure scenario:** an agent offers context-bound commands (say `/continue-task`) on the source session. It correctly advertises none on a fresh fork. It gets a CAPABILITY FAIL and is NOT CONFORMANT.
- **Fix:** judge only `configOptions` at CAPABILITY. Drop the commands half, or make it ADVISORY or INFORMATIONAL.

### S2. ACP-SESSION-204 and ACP-LIST-205 require the exact `-32602` at CAPABILITY from a sentence with no RFC keyword, against C9. Should-fix. Confirmed by reading.
- **Where:** `requirements.py` (SESSION-204, about line 1162; LIST-205, about line 1509), `src/tck/v2/conformance/test_session.py:59` and `test_session_capabilities.py:702`.
- **Defect:** the cited sentences are declarative:
  - `session-setup.mdx:524`: "**MUST** be an absolute path. Agents reject a request with a relative `cwd` with `-32602`". The MUST binds the client's path.
  - `session-list.mdx:64-65`: "Must be an absolute path. Agents reject a relative path with `-32602`".
  - `error.mdx:48`: "... get `-32602`".

  C9 says: CAPABILITY asserts error versus success, and the exact code only where a MUST names it, with SHOULD codes in a separate ADVISORY row. Other rows in this milestone follow C9, for example AUTH-208/AUTH-210 and INIT-213 with its ADVISORY. LIST-205's own text says "Declarative ... no RFC keyword".
- **Failure scenario:** an agent rejects a relative `cwd` with `-32600`. It FAILs CAPABILITY and is NOT CONFORMANT.
- **Fix:** split each into a CAPABILITY rejection row and an ADVISORY exact-code row (as AUTH-208/210 do), or get the user to approve an explicit C9 exception.

### S3. ACP-CANCEL-209 (CAPABILITY) and ACP-CANCEL-213 never judge an agent that asks permission before reporting `requires_action`, which is the order the spec's own diagram uses. Should-fix. Confirmed by reading.
- **Where:** `src/tck/v2/conformance/test_cancel.py:369-382` (`_skip_unless_cancelled_while_blocked`), with hold mode at `src/tck/v2/conformance/_helpers.py:1340-1343`.
- **Defect:** hold mode sends `session/cancel` as soon as the first `session/request_permission` arrives, so `state_at_cancel` is the state just before the request. The gate requires `requires_action`.
- **Failure scenario:**
  - The diagram at `prompt-lifecycle.mdx:246-247` sends `session/request_permission` and then `state_update: requires_action`. An agent that follows it has `state_at_cancel == "running"` every time, so both rows SKIP and are never judged.
  - Agents that never report `requires_action` (it is only a SHOULD, `:153,174`) always SKIP too.
  - `AsksPermissionAgent` reports `requires_action` first, so no fixture shows this.
- **Fix:**
  - Once the request is held, wait a short peek for `requires_action` before cancelling.
  - Or drop the state gate in favour of the H2 `for_foreground` test, which already excludes background-work requests.

### S4. ACP-INIT-211/212 (MANDATORY) FAIL when the agent ignores an unknown `_tck/...` request, which is stricter than the rows. Should-fix. Confirmed by running.
- **Where:** `src/tck/v2/conformance/test_initialize.py:616` (`_assert_initialized`, through `_request_or_fail`), used by the INIT-211 and INIT-212 tests. The stale claim is in `tests/v2/test_cli.py` at about line 3821.
- **Defect:** the "connection is now initialized" probe sends `_tck/after_initialize` and FAILs on silence. The rows forbid only a "not initialized" (`-32600`) answer.
- **Failure scenario:** `custom_method_no_response.py` under `-k test_initialize` gives `ACP-INIT-211 FAIL` and `ACP-INIT-212 FAIL`, with every other INIT row PASS or SKIPPED. Those are two MANDATORY FAILs on rules the agent follows. The defect is EXT-001's.
  - The test_cli case for that fixture is scoped with `-k "test_extensibility or test_diagnostics"`. Its docstring says the {EXT-001, ERROR-001} set was "confirmed via an unscoped run", which stopped being true at bac245c.
- **Fix:**
  - Treat only a `-32600` reply as "not initialized", and silence as no evidence (SKIP or PASS).
  - Or probe with a standard method the agent advertises.
  - Correct the test_cli docstring.

### S5. ACP-ARCHIVE-005 gives auth-gated agents a CAPABILITY FAIL where they should SKIP `AUTH-GATED:`. Should-fix. Confirmed by running (throwaway fixture).
- **Where:** `test_session_capabilities.py:1393` (`test_archive_unknown_session_is_not_found`).
- **Defect:** it archives and unarchives a never-created id without a `session/new` first. An auth-gated agent may answer `-32000` (`authentication.mdx:193`). ERROR-201 and RESUME-211 create a session first so that such agents SKIP with `AUTH-GATED:`.
- **Failure scenario:** an archive-capable agent that requires login, run without `--auth-method`, reports `ACP-ARCHIVE-005 FAIL` ("expected -32002, got -32000"). The verdict is already blocked by auth, but the report and JSON blame the wrong row.
- **Fix:** call `await new_session(...)` first (it SKIPs on auth), as ERROR-201 does.

### S6. ACP-META-203 FAILs a `null` W3C key, which is a legal metadata-patch removal. Should-fix. Confirmed by reading.
- **Where:** `src/tck/v2/conformance/test_extensibility.py:203-215`.
- **Defect:** every `traceparent`/`tracestate`/`baggage` key found is judged, including a `null` value. On upsert updates `_meta` is a patch, and "A key set to `null` is removed" (`extensibility.mdx:108-115`). A null is not "present" with a value, which is what `:97` constrains.
- **Failure scenario:** an agent clears a stored trace id with `tool_call_update {_meta: {traceparent: null}}`. It gets a CAPABILITY FAIL ("traceparent=None"). The case is rare.
- **Fix:** skip `None` values (at least on patch-carrying updates), and add a unit case.

### S7. ACP-CONFIG-209 passes trivially on a session with one settable option. Should-fix. Confirmed by reading.
- **Where:** `src/tck/v2/conformance/test_session_config.py:433-486`.
- **Defect:** with one select or boolean option, only the unknown-`configId` probe runs. The follow-up no-op set then targets that same option (`follow_up = settable[0]`) with its *pre-probe* value. That overwrites exactly the damage the probe could have done to it.
- **Failure scenario:** an agent mistakenly applies an unknown-`configId` set to its only option, a common single "model" option. CONFIG-209 PASSes without having judged anything. The test's docstring warns against this very masking ("Setting the probed option itself would overwrite any damage").
- **Fix:** SKIP ("needs a second option to observe through") when `len(settable) == 1` and the session has no other observable option, as the invalid-value half already does.
- **Also (nit):** the code judges every probe whenever at least one was rejected. If probe 1 is rejected and probe 2 is accepted and mutates state, CONFIG-209 FAILs as well as CONFIG-208. The row text says unrejected probes are "not judged here".
- **Also (nit):** `msg.get("result", {}).get(...)` raises `AttributeError` on `"result": null`.

### N1. The v2 ACP-PROMPT-206 text says it replaces "v1's ADVISORY `ACP-PROMPT-003`". v1 PROMPT-003 is MANDATORY. Nit. Confirmed by reading.
- `src/tck/v2/requirements.py:518-533`. S-v1-5 made v1 PROMPT-003 MANDATORY (`src/tck/v1/requirements.py:301-302`). The stale sentence shows up in every report. See known item 6 for the tier.

### N2. The `providers/*` ledger entry claims "no TCK row exercises `providers/*`", but ACP-ERROR-202 probes `providers/list`. Nit. Confirmed by reading.
- `spec-tracker/maps/v2.toml:682-685`. ERROR-202 (`requirements.py:2888-2901`, `test_errors.py` `_OTHER_GATED`) cites `error.mdx:68` and sends `providers/list` without `capabilities.providers`. Keep only the `security.mdx:81` half (an agent-side SHOULD NOT; the ledger is fine for that) and fix the reason. See known item 9.

### N3. The AUTH-208 ledger statement adds a rule the spec does not contain. Nit. Confirmed by reading.
- `spec-tracker/maps/v2.toml:290-292`. `authentication.mdx:191` says only that the agent "responds with `-32602`". "Starts no login flow" is the programmer's inference, and the `-32602` half is already AUTH-208/210. Recommendation: delete the entry. A ledger entry should restate cited text, and spec-impact readers will take it as spec wording.

### N4. A `spec-tracker/maps/v2.toml` ledger reason mis-describes AUTH-202. Nit. Confirmed by reading.
- The entry for `initialization.mdx:147` says the TCK uses a single-capability connection "`auth.terminal: true` (ACP-AUTH-202)". In v2 that capability is the object marker `{}`, and the dedicated positive connection belongs to ACP-AUTH-207. AUTH-202 uses the default connection.

### N5. `background_keys` raises `TypeError` on an unhashable `type`, inside `run_prompt`. Nit. Confirmed by running.
- **Where:** `src/tck/v2/conformance/_helpers.py:868`, called from `run_prompt` at `:1312`.
- **Defect:** `BACKGROUND_ID_FIELDS.get(item.get("type"))`.
- **Failure scenario:**
  - `background: [{"type": ["tool_call"], ...}]` raises `cannot use 'list' as a dict key`. Every `run_prompt` row then FAILs with an opaque traceback, not a schema message. The harness promise is "never crashes on anything the agent sends".
  - Pre-existing and outside the range, the same applies to `state in ACTIVE_STATES` when `state` is a list.
- **Fix:** `isinstance(..., str)` guards, as `protocol.is_open_enum_value` already has.

### N6. ACP-ARCHIVE-201 (and ACP-DELETE-204, which it copies) never reaches its documented "archive error SKIPs" branch. Nit. Confirmed by reading.
- `test_session_capabilities.py:1441` checks the archive error only after it has asserted `stop_reason == "cancelled"`. An agent that rejects archiving an active session FAILs on the stop reason or the timeout. The FAIL is defensible (`session-list.mdx:247`), but the docstring and row text are wrong.

### N7. The B1 kind-not-offered fallback also fires for background-work permission requests. Nit. Confirmed by reading.
- **Where:** `_helpers.py:1347-1361`.
- **Defect:** f57c833 guarded the hold and cancelled branches with `for_foreground`, but not this fallback. A background request lacking the policy's kind triggers `session/cancel` of the foreground work. `cancelled_at_index` is set, and the request is answered `cancelled`, although cancel does not cover it (`prompt-lifecycle.mdx:1173,1177`).
- **Fix:** for a background request, answer `cancelled` without `session/cancel`, or SKIP.

### N8. ACP-CANCEL-213 can PASS on a `$/cancel_request` sent after the TCK already answered the held request at the deadline. Nit. Confirmed by reading.
- `_helpers.py:1380` records `held_cancel_request_index` whatever `held_answered_on` is. CANCEL-209 still FAILs, and the row is ADVISORY. Record the index only while `held_answered_on is None`.

### N9. PROMPTCAP-201's negative gate treats `image: true` as advertised and SKIPs. Nit. Plausible.
- **Where:** `src/tck/v2/conformance/test_prompt_capabilities.py`, the `capability_is_supported(...)` call in `test_unadvertised_content_block_is_rejected_without_insertion`.
- **Defect:** v2 `PromptCapabilities.{image,audio,embeddedContext}` are `$ref | null` with `x-deserialize-default-on-error`, so a client reads `true` as not advertised.
- **Failure scenario:** an agent advertising `image: true` that accepts image blocks SKIPs where it should FAIL.
- **Fix:** gate on `isinstance(value, dict)`.

### N10. ACP-COMMANDS-201's scan calls `params.get` without checking that `params` is a dict. Nit. Confirmed by reading.
- In `src/tck/v2/conformance/test_slash_commands.py`, a `session/update` with array or missing `params` gives an `AttributeError` FAIL, not a message about the real defect.

### N11. Docstring drift. Nit. Confirmed by reading.
- `src/tck/v2/conformance/test_initialize.py:679` cites the never-registered `ACP-JSONRPC-201`. Under rule B it is JSONRPC-004, and the missing reply is EXT-001's concern.
- `tests/fixtures/agents/v2/reserved_range_custom_code.py:2-4` lists only `-32000/-32002/-32022` as ACP codes in `-32768..-32000`, leaving out `-32700` and `-32600..-32603`.
- The known stale "ENUM-202" remains in `prefixed/unprefixed_custom_session_update.py`.
- `tests/fixtures/agents/v2/config_set_unknown_id_accepted.py` defines an unused `_DEBUG_OPTION`.

### N12. Several new fixtures' "FAILs exactly X" claims are checked only under `-k` scope. Nit. Plausible.
- **Where:** `tests/v2/test_cli.py`:
  - `_negotiation_fails` (`k="initialize or extensibility"`)
  - `_ERROR_K`
  - `_extensibility_run` / `_enum_201_run`
  - the config, archive, resume and background runners.
- **Why it matters:** S4 is one cross-row trip this hid. S-v2-15 already noted `unprefixed_chunk_content_type`/`unprefixed_diff_operation`.
- **Also:** the new auth self-tests assert `returncode != 0` on `-k authentication` runs. That is always true, because scoping leaves MANDATORY ids NOT_TESTED. The exact FAIL sets carry the real check.
- **Fix:** either word the docstrings as "within <scope>", or add an occasional unscoped sweep.

Not reported, as settled by C4: under the `allow` policy, the "first option" fallback can select `reject_always` (`_helpers.py:963-965`). That persists a standing deny. Record it as a follow-up if the user wants C4 revisited.

## Verdicts on the known items

1. **Pyright errors.** All but one are annotation noise; I re-ran pyright at the tip, so the line numbers have moved.
   - `_helpers.py:469`: `result` is a dict whenever `sessions` is a list. Noise.
   - `_helpers.py:1733`: `response` is non-None whenever `response_index` is. Noise.
   - `tests/v2/test_cli.py:1486`: a missing id becomes `None`, which still fails the equality asserts properly. Noise.
   - `tests/v2/test_cli.py:2627`: no caller passes `allow_logout` through `**kwargs: str`. Noise.
   - `tests/v2/test_cli.py:3057`: a `frozenset` default for a `set` annotation. Noise.
   - `_helpers.py:868` (`Unknown | None` as a dict key) points at a real crash, though not the one pyright names: an unhashable `type` raises `TypeError` (N5).
2. **META-203 traceparent grammar.** Correct against W3C Trace Context Level 1:
   - lowercase hex fields of 2, 32, 16 and 2 digits;
   - version `ff` invalid;
   - all-zero trace-id and parent-id invalid;
   - version `00` exactly 55 characters;
   - a later version may add content only after a `-` at index 55.

   Accepting future versions is lenient, so it cannot false-FAIL. The `extensibility.mdx:97-100` citation matches, and `tests/v2/test_open_enums.py:143-164` covers the grammar. The real problem is `null` values (S6).
3. **Cascade FAILs from fixtures with a broken `run_prompt`** (META-202/203/204, RESUME-212/213/214, the six S-v2-15 rows): **keep FAIL.**
   - The documented status model is that a test erroring with `AgentTimeout` propagating out is a FAIL. The pre-existing cascades already follow it, for example `no_idle_after_running.py` and `cancel_no_idle.py`.
   - A never-idle agent is already NOT CONFORMANT through its MANDATORY PROMPT/STATE rows, so the cascade changes no verdict.
   - SKIP-on-setup-failure would need a shared helper and would risk hiding real FAILs.
   - Consistent rule to adopt: a row FAILs when an agent defect stops its setup. It SKIPs only when a precondition is legitimately absent: capability not advertised, race inconclusive, feature not observed, or a step another row judges failed by design (as FORK-205 does when the fork errors). Optionally, prefix setup-turn failure messages ("setup turn never reached idle") so the cause is obvious.
4. **CONFIG-209 redesign.** Sound in principle: observing through a *different* option avoids the masking. Two holes remain: the single-option case is vacuous (S7), and a judged-but-accepted probe causes a double FAIL (the S7 nit).
5. **DELETE-201 strict on `-32002`.** **Agree.**
   - The session was just created on this connection, so it is active by definition (`error.mdx:54`, `session-setup.mdx:49`).
   - A `-32002` ("does not exist or is not active") is therefore false. It also suggests that the `:95` MUST (cancel, free, delete) was not followed.
   - `session-delete.mdx:92` tells *clients* to tolerate `-32002`. That supports S1's carve-out for sessions that are already gone, not an agent misreporting a live one.
   - C9 (CAPABILITY asserts error versus success) gives the same answer.
6. **PROMPT-206 versus v1 PROMPT-003.** Same rule (`resource_link` is baseline). v2 CAPABILITY gated on `capabilities.session` is the right equivalent of v1 MANDATORY, since without `session` there is no `session/prompt`. The citations (`initialization.mdx:308`, `content.mdx:178`) are correct. Only the row text is stale (N1). Under rule B, S-ALIGN should give it v1's id, PROMPT-003.
7. **`conforming_full` advertises `capabilities.cancel` with no handler.** Nit-level and acceptable for now: the TCK never sends `tool_call/cancel` or `terminal/cancel` (deferred, C1), and PATCH-212 needs the cap advertised. But the "conforming" fixture would answer `-32601` where `tool-calls.mdx:458-459,604-605` require `{}` or `-32602`. That turns into a FAIL as soon as a cancel row lands. Add a trivial `{}`/`-32602` handler in `_base`, or a docstring note.
8. **v2 PERM-002 CAPABILITY versus v1 ADVISORY.** Correct.
   - v2 `tool-calls.mdx:346-347` is a MUST ("MUST treat the request as not approved").
   - v1 `tool-calls.mdx:249` is a SHOULD NOT.
   - The tier is per version under rule B. Both are the same rule, so sharing the id is right.
   - The "never `completed`" proxy is weak but honest (fork note: an agent that leaves the call `in_progress` PASSes; `:423` is only a SHOULD).
9. **S-v2-17 ledger.** The `providers/*` entry is half wrong (N2), and the AUTH-208 entry should go (N3). The other entries I checked are agent-side, cited correctly and not covered by a row. For the 8 candidates:
   - **TC:348-349, unknown outcome on a `tool_call` subject: requirement-now** (CAPABILITY, `capabilities.session`).
     - It is an agent MUST.
     - The probe is a *legal* client message (a `_tck`-prefixed custom outcome; the text says "Custom or future outcomes may appear").
     - It is observable exactly as PERM-002/PERM-203 are, through `run_prompt(permission=...)`.
   - **TC:578-579, output after `exitStatus` (PATCH-213): ledger-ok.** It is a SHOULD, and V2-D19 deferred it.
   - **TC:653-661, `git_patch` paths (DIFF-201): ledger-ok for this release**, deferred by V2-D19. The rules are MUSTs, so keep them on the next update's list.
   - **agent-plan.mdx:119, file-plan URI absolute (PLAN-201): ledger-ok**, deferred by V2-D19. v1 checks the same rule as MANDATORY PLAN-001 (V1-D12 "also binds v2 later"). When it lands, it should share PLAN-001 under rule B.
   - **session-setup.mdx:443, unadvertised `additionalDirectories` ignored: ledger-ok.** It is declarative. A C10 probe would be allowed, but the client MUST at `:441` means no conforming client sends the field, so it has little value.
   - **session-list.mdx:248, unarchive does not make the session active: ledger-ok.** The observable result (a prompt after unarchive gets `-32002`) is the general `error.mdx:54` MUST. If wanted later, it is a cheap extra probe in the archive tests.
   - **session-setup.mdx:49, fork snapshot `background: []`: ledger-ok.** It is declarative, and nearly always vacuous: it only bites when the source has live background work.
   - **`Icon.src` `https:`/`data:`: ledger-ok.** `Icon` appears only in `ResourceLink.icons`, which agents rarely emit, so a passive check would almost always be vacuous. The existing entry says this.
10. **ARCHIVE-001 not registered, and the ERROR-202 extension.** Both correct.
    - `session.archive` sits inside `capabilities.session`, and creating that object advertises all seven baseline methods, `session/list` included (`extensibility.mdx:259`, `initialization.mdx:205`). So "archive implies list" cannot fail in v2.
    - Mirroring v1's 002..006 split keeps rule B ids, which is fine.
    - ERROR-202's archive and unarchive probes are backed by the `error.mdx:44` MUST. The exact `-32002` in ARCHIVE-005 is backed by the `:54` MUST, which matches C9.

## Checked and clean

- **Re-vendor (7c76250):** byte-identical schema and meta; `VENDORED.md`, `SCHEMA_REVISION` and the new enum values (`paused`, `session`) match the schema.
- **50b6270 (v2 part):** every `x-deserialize-default-on-null` node is covered.
- **eb4e899 (v2 part):** follows C5.
- **Citations:** these say what their rows claim:
  - BATCH-209, TRANSPORT-201, JSONRPC-002/004/202, ERROR-201..204, RESUME-211, INIT-209..215, EXT-203
  - META-202/204, ENUM-201's new sites, ENUM-204
  - CANCEL-209..214, CLOSE-204..207, PROMPT-209/211, PROMPTCAP-201, STATE-206..208
  - SESSION-206..208, ADDDIRS-203, MCP-201/203..205, SYSPROMPT-002/003, RESUME-210/212..216
  - LIST-205/206, DELETE-201..205, FORK-203..205, CONFIG-201..212, COMMANDS-201
  - AUTH-201..210, PERM-202/203/002, PATCH-208..212, ARCHIVE-002..006/201
- **Tests:**
  - CANCEL-214 and DELETE-204 race handling never excuses `error`.
  - The `prompt_during_active_work` classification is sound.
  - H2 (background permissions never held) is correctly implemented.
  - `PatchTracker`'s patch semantics match `tool-calls.mdx:102-108,440`.
  - The SYSPROMPT control resume prevents a vacuous PASS.
  - META-204 cannot be tripped by the TCK's own `_meta`.
- **Fixtures:** every new fixture's docstring matches its `tests/v2/test_cli.py` set, within each test's `-k` scope (see N12).
