# Review: v1 milestone (spec beac4ba9 -> 3961af94), commits 61d40b5^..d28f79b

Scope: the product commits 61d40b5, 4d88f27 (v1 and v2 `_helpers.py`), a88a68b, 7ec493c, eb0dd31,
734ba0e, f8f5e41, 78e7af4, f8fd84a and d28f79b. I skipped 7c76250, c1d4e23 and the `chore: record`
commits.

Method: I read the diff and the surrounding code, checked every new or changed v1 citation against
`git show 3961af94:...` in `../agent-client-protocol-2`, and spot-checked about 25 ledger
citations. I checked byte for byte that the vendored v1 schema and meta files match upstream (they
do). I ran `uv run pytest -q tests/v1/test_run_prompt.py tests/v1/test_plan_uri.py
tests/v1/test_registry.py tests/common/test_plugin.py`: 77 passed. I did not run the full suite.
The product tree has no `.agents/` references, apart from the pre-existing `cross-check/run.sh:27-28`,
which belongs to S-XC.

Counts: 1 blocker, 4 should-fix, 5 nits.

## Findings (most severe first)

### B1. The `reject_once` policy can select `allow_always` (operator-safety regression of S-X1). Blocker. Confirmed by reading and by the unit test.
- **Where:** `src/tck/v1/conformance/_helpers.py:316-323`, `src/tck/v2/conformance/_helpers.py:799-806`, pinned by `tests/v1/test_run_prompt.py:128` and `tests/v2/test_run_prompt.py:235`.
- **Defect:** when no `reject_*` option is offered, `permission_outcome(..., "reject_once")` falls back to `candidates[0]`. That can be `allow_always` or `allow_once`.
- **Failure scenario:** ACP-PERM-001 runs by default against every agent. Suppose a real agent offers `[{kind: allow_always}, {kind: allow_once}]`, with no reject option because the client can cancel. The TCK selects `allow_always` and the agent stores a lasting approval for file writes in the operator's config. Only then does the test SKIP with "first option selected (no reject_once offered)". The SKIP verdict is right, but the harm is already done. This is the exact hazard S-X1 was written to remove. C4 allows `allow_always` only as the `allow` policy's recorded fallback, never for a reject policy.
- **Related:** the `reject_always` fallback (line 318) also persists a lasting decision: a standing deny that breaks the operator's workflow.
- **Fix:** for `reject_once`, when no `reject_once` is offered, answer `{"outcome": "cancelled"}` with a note. `cancelled` is always a valid outcome and stores nothing. Drop the `reject_always` and first-option fallbacks, or limit them to `reject_once`. Update both unit tests, both `PermissionPolicy` docstrings and the `test_permissions.py` module docstring.

### S1. ACP-DELETE-001 fails at CAPABILITY on the same `-32002` answer that DELETE-003 and ARCHIVE-006 count as success. Should-fix. Plausible (judgement call 3).
- **Where:** `src/tck/v1/conformance/test_session_capabilities.py:293-305`, `tests/v1/test_cli.py` (`test_delete_answering_not_found_still_runs_the_list_check`), `tests/fixtures/agents/v1/delete_answers_not_found.py`.
- **Defect:** in one run, a `-32002` answer to the delete is "a successful delete" for DELETE-003 and ARCHIVE-006 (`session-delete.mdx:87`), but a CAPABILITY FAIL for DELETE-001. The spec bounds the behavior at SHOULD: "deleting a session that never existed SHOULD succeed silently" (`:86`, already judged by ADVISORY DELETE-002), clients SHOULD treat `-32002` as success (`:87`), and `error.mdx:55` says closing or deleting a session that does not exist still succeeds.
- **Failure scenario:** an in-memory agent advertises `close`, `delete` and `list`, discards a session on close, and answers the later delete with `-32002`. It gets NOT CONFORMANT, from a SHOULD that clients are told to tolerate. The fixture shows the same pattern: its DELETE-003 PASS is trivial because `_base._handle_close` already pops the session.
- **Fix:** in DELETE-001, treat `-32002` after a close like DELETE-003 does (PASS, or SKIP with a note), and leave the SHOULD to DELETE-002. Then update the fixture docstring and the test_cli set to `{DELETE-002}`.
- **If you keep it:** state in the DELETE-001 text that `-32002` for a session the agent still stores is a FAIL. The text currently says nothing about it.

### S2. The ARCHIVE-003/006 citations don't back their assumption that `include` and `only` are supported. Should-fix, pending the user's decision. Confirmed by reading (judgement call 6).
- **Where:** `src/tck/v1/requirements.py:546` (ARCHIVE-003, cites `session-list.mdx:231,244-250`) and `:595` (ARCHIVE-006, cites `:261`). The behavior is in `_list_sessions` (`test_session_capabilities.py`), which asserts that every page succeeds.
- **Defect:** the cited doc never says all three filter values must be supported. `session-list.mdx:252` ("MUST reject a value they don't support with `-32602`") actually reads as if a subset is possible. Only the Draft RFD `docs/rfds/session-archive.mdx:112` says "MUST support all three values", and neither row cites it.
- **Failure scenario:** an agent rejects `archived: "only"` with `-32602`. It follows the doc's MUST and still gets a CAPABILITY FAIL on ARCHIVE-003, and on ARCHIVE-006 for `include`. A reader following the citation finds no rule that it broke.
- **Fix:** add `docs/rfds/session-archive.mdx:112` to both citations and labels (the researcher's recommendation; PLAN-001 and AUTH-007 already cite RFDs the same way). Or, if the user chooses the fallback, SKIP on `-32602` for `include` and `only`.

### S3. PLAN-001 (MANDATORY) can FAIL on a turn timeout caused by its own open-ended prompt. Should-fix. Plausible.
- **Where:** `src/tck/v1/conformance/test_plan.py:26` and `:37-42`.
- **Defect:** the prompt is "Make a step-by-step plan for refactoring this project, then start on it." `run_prompt` has a single overall deadline equal to `--timeout` (default 30 s, `_helpers.py:432`), and the call is not guarded.
- **Failure scenario:** a real LLM agent plans, then "starts on it" with tool calls, which `run_prompt` approves with `allow_once`. The turn runs past 30 s, `AgentTimeout` propagates, and the run reports a MANDATORY FAIL of ACP-PLAN-001 and NOT CONFORMANT. A slow turn is not a plan-URI defect. The same applies to PLAN-002 (ADVISORY). The agent also keeps doing open-ended work in `tmp_path` after the connection closes.
- **Fix:** drop "then start on it" (for example, "Make a step-by-step plan for refactoring this project; do not start yet."). Also catch `AgentTimeout` around `run_prompt` in `_updates_with_plan_capability` and judge the updates seen so far, since PLAN-001 is passive.

### S4. `tool_call/cancel` and `terminal/cancel` are ledgered in v1, which does not define them. Should-fix. Confirmed by reading (judgement call 7).
- **Where:** `spec-tracker/maps/v1.toml:331-339`.
- **Defect:** v1 `meta.unstable.json` at 3961af94 has neither method; only `schema/v2/meta.unstable.json:23-24` does. The cited `rfds/subagents.mdx:1041-1045` is mainly a client allowlist ("Clients MUST NOT invoke an unadvertised mutation") plus a description of a capability. It is not a rule that binds a v1 agent, so both entries break C6 (agent-side rules only) and the C1 intent (deferred methods of this version).
- **Failure scenario:** a future v1 `spec-impact` run treats these as covered v1 rules. A maintainer reading the v1 ledger concludes that v1 has a cancel contract to revisit.
- **Fix:** delete both v1 entries and ledger the deferral in v2 (S-v2-17), where the methods exist.

### N1. ACP-ERROR-006 drops FAILs it has already found when a later probe answers `-32000`. Nit. Confirmed by reading.
- **Where:** `src/tck/v1/conformance/test_errors.py:345-346`.
- **Failure scenario:** `session/load` (unadvertised) succeeds, which is a real problem, and then `session/list` returns `-32000`. `pytest.skip` throws away the collected `problems`, so the row reads SKIPPED instead of FAIL. The case is unlikely, since `new_session` succeeded first.
- **Fix:** record the `-32000` methods, continue, and SKIP only if `problems` is empty and every probe was `-32000`.

### N2. ACP-ERROR-008 and ACP-AUTH-008 hard-code value sets that the schema defines. Nit. Confirmed by reading.
- **Where:** `test_errors.py:46-57` (`_ACP_DEFINED_CODES`) and `test_authentication.py:201` (`_AUTH_STATES`).
- **Failure scenario:** the `ErrorCode` description says ACP-specific errors live in `-32000..-32099`. After a schema refresh adds a code there (or a new `AuthState` const), an agent that correctly uses it gets an ADVISORY FAIL until someone notices. CLAUDE.md says these tables should self-update from the vendored schema.
- **Fix:** derive both sets from the `const` members of `$defs/ErrorCode` and `$defs/AuthState`, in `tck.v1.protocol` or `validation`.

### N3. ACP-ARCHIVE-006 can PASS vacuously. Nit. Plausible.
- **Where:** `test_session_capabilities.py:613-641`.
- **Failure scenario:** some agents list a session only after its first prompt. Against such an agent, a "delete hides the session only from the default view" defect still PASSes, because the session was never listed. ARCHIVE-003 SKIPs in the same situation.
- **Fix:** list with `archived: "include"` before deleting, and SKIP if the session is absent, as ARCHIVE-003 does.

### N4. A test_cli docstring is stale. Nit. Confirmed by reading.
- **Where:** `tests/v1/test_cli.py:267`.
- **Defect:** `test_conforming_agent_passes_everything` says "the four ADVISORY ids" and lists LOAD-003, DELETE-002, ERROR-004 and ERROR-007. `_CAPABILITY_GATED_IDS` (a few lines above) has nine, adding LIST-003, CLOSE-003, AUTH-008 and PERM-001/002. The assertion is correct. Only the prose misleads whoever next edits the sets.
- **Fix:** drop the count and point to `_CAPABILITY_GATED_IDS`.

### N5. A few agent-side SHOULDs are neither tested nor ledgered (C6 completeness). Nit. Plausible.
- `docs/rfds/get-auth-state.mdx:291`: the agent SHOULD advertise `auth.status`.
- `get-auth-state.mdx:303`: agents SHOULD list their accounts and mark the active ones. Only the secrets MUST is ledgered.
- The config SHOULDs already noted in state.md (`session-config-options.mdx:235`, `:462-471`).
- **Fix:** add these to the ledger in the cleanup slice, or record why they are left out.

## Judgement calls

1. **ERROR-005 has no `-32000` SKIP. Agree.** Before `initialize`, nothing about authentication has been negotiated, `error.mdx:61` names `-32600`, and the row is ADVISORY. ERROR-003, 004 and 006 run after initialize and auto-authenticate, so `-32000` is a plausible "checked auth first" answer there.
2. **ERROR-008 treats the whole reserved range as ACP-owned. Agree.** `error.mdx:37` reserves both ranges "for JSON-RPC and ACP" and says implementation-specific codes SHOULD avoid them, which overrides JSON-RPC's "-32000..-32099 implementation-defined".
   - Not isolable, agreed: every sampled site has its own exact-code row (unknown method is JSONRPC-004, missing `cwd` is ERROR-002, unknown session is ERROR-003).
   - See N2 about deriving the set from the schema.
3. **`delete_answers_not_found.py` FAILs DELETE-001/002 while DELETE-003 PASSes. Partly disagree,** see S1. DELETE-002 FAIL and DELETE-003 PASS are right. The CAPABILITY FAIL of DELETE-001 on a `-32002` answer is not.
4. **PERM-001/002 SKIP after a fallback answer. Disagree,** see B1. The SKIP is correct. The problem is the answer already sent, which can grant `allow_always`. ACP-PERM-002 (`unknown_option`) never falls back, so it is safe.
5. **PLAN-001 reads "absolute" through `is_absolute_uri`. Agree.**
   - An RFC 3986 scheme of at least two characters (so `C:\x` is not a URI), plus an RFC 8089 absolute path for `file:`. The unit cases in `tests/v1/test_plan_uri.py:21-46` match this reading.
   - The field is named `uri`, so a bare `/tmp/plan.md` failing is defensible.
   - Small suggestion: because this is a MANDATORY FAIL resting on the TCK's own reading, have the failure message (`test_plan.py:70`) name the reading ("RFC 3986 scheme; `file:` needs an absolute path").
6. **ARCHIVE-003/006 when an agent rejects `include` or `only`.** Noted as S2. Today the citation does not back the FAIL. Adding the RFD cite settles it either way the user decides.
7. **`tool_call/cancel` and `terminal/cancel` in the v1 ledger. Disagree,** see S4.
8. **`_gate_unadvertised` answers `-32601` for every unadvertised gated method. No silent meaning change found.**
   - The `tests/v1/test_cli.py` diff only adds expectations. The one widened set, `conforming_full` now SKIPping ERROR-006, follows from the inverted gate (it advertises every gated method), and `conforming.py` still covers ERROR-006's PASS path.
   - Every conformance-suite send of `session/load`, `list`, `resume`, `close`, `delete`, `archive` or `auth/status` outside the capability tests sits behind a `capability_is_supported` check (`test_prompt.py:137`, `test_session.py:186-193`, `test_session_config.py:310-318`, `test_client_capabilities.py:112`).
   - Footgun for future fixture authors: the gate runs in `_reject_request`, before `_handle_request`. A fixture that serves a method by overriding `_handle_request` without advertising it now gets `-32601`; it has to override `_method_advertised`, as `implements_unadvertised_list.py` does. The class docstring covers this, which is enough.
   - Leaving the stable, gated `logout` out of the gate and out of ERROR-006 is correct, since probing it could revoke the operator's credentials. The ERROR-006 text could say so in a few words.

## Other checks, nothing found
- **Citations:** these resolve at 3961af94 to text that says what the row claims: ERROR-003..008, CLOSE-003, SESSION-006, LIST-003, DELETE-003, PROMPT-003, CLIENTCAP-007 (incl. `tool-calls.mdx:358` and `rfds/subagents.mdx:76-78,644-645`), PLAN-001/002, PERM-001/002, AUTH-007/008, ARCHIVE-001..006 (apart from S2), the SYSPROMPT-001..003 text, INFO-PARSE/INVALIDREQ, and JSONRPC-002/004.
  - Tiers match the plan and the decisions: C9 for ARCHIVE-004 (exact `-32602`, a MUST names it) and ARCHIVE-005 (error versus success only); V1-D6 and V1-D8 for the ADVISORY FAILs.
- **Comment line cites** in touched v1 files are current: `prompt-turn.mdx:641`, `:38`, `:133-144`, `session-delete.mdx:87,90`, `error.mdx:37,67`, `transports.mdx:22`, `authentication.mdx:153,187-188`, `extensibility.mdx:13-14`. `common/plugin.py:358` cites v2 `initialization.mdx:100`, which is v2 milestone scope.
- **Fixture docstrings** match their exact `test_cli.py` FAIL/PASS sets, for every new v1 fixture read: archive x6, auth_status x3 + gated_by_auth_with_status, close_not_idempotent, delete_answers_not_found, implements_unadvertised_list, legacy_server_error_code, serves_before_initialize, set_unknown_session_accepts. The fixture-based CLI tests compare against exact FAIL sets, not subsets.
- **Plugin shim:** `_tck_record_properties` is a fixture, resolved by name, and both it and `record_test_property` use `tck.common.plugin`'s own globals, so the `vars()` copy is safe.
- **Cross-imports:** no v1/v2 cross-imports.
- **Follow-up, v2 scope:** `src/tck/v2/conformance/test_informational.py:107` says ACP-INFO-UNKNOWNSESSION-001 is "reused from v1", which is no longer true. S-v2-3 removes it anyway.
