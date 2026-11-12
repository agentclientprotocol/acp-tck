# Review: M3 (v1 ACP-SUBAGENT-001..009, 011..015; ledger)

Range: `bcf97e7..dfe13a0` (one product commit, dfe13a0). Read in a detached worktree at dfe13a0. Spec read with
`git show 3961af94:...` in the spec checkout (no pull).

## What I ran

- Unscoped `python -m tck --timeout 1 --startup-timeout 1 -- python tests/fixtures/agents/v1/<f>` for all 26
  subagent-related v1 fixtures. Every violator FAILs exactly its intended row, with no other FAIL anywhere in the
  registry. `exposes_subagent.py` and `replays_subagent_history.py` are CONFORMANT with every `ACP-SUBAGENT-*` row
  PASS and `ACP-CLIENTCAP-007` PASS. `emits_subagent_update_unadvertised.py` and `session_content_without_subagents.py`
  FAIL only `ACP-CLIENTCAP-007`. Unlike v2, `unannounced_child_update.py` does not double-FAIL `ACP-PROMPT-002`.
- `uv run pytest -n auto tests/v1/test_cli.py -k "subagent or session_message or exposes or replays_subagent"`:
  29 passed. `tests/v1/test_registry.py tests/common/test_capability_markers.py`: 16 passed.
- Probes of the v1 helpers on hand-built transcripts (A, B, C below).

## Findings

### 1. should-fix: `session/load` replay is judged with the live "known" set, so 001 can false-PASS (and, once scoped, false-FAIL)
`src/tck/v1/conformance/_helpers.py:609-635` (`_wire_messages`), `:638-683` (`child_session_traffic`),
`:686-727` (`session_content_references`); row text `src/tck/v1/requirements.py:1127-1157`.

- **Defect:** `known` only grows over the whole transcript. A child announced live stays known through the
  `session/load` window, and nothing marks that window. The row says it judges "during `session/load` replay", but
  the replay rule is different from the live rule:
  - RFD:933-935: "Replayed child updates MUST ... Child announcements precede child traffic."
  - RFD:981-987: "The Client need not retain an earlier session tree. ... the Agent establishes the child's
    complete ancestor chain in parent-before-child order during this load/resume."
  - v2's `ACP-RESUME-209` (M1 decision) applies exactly this, "even if an earlier turn announced it".
  - The cited doc text is about *live* traffic only (`schema.mdx:8710-8711`: "before any live child traffic or live
    message naming the child"), and 001 cites no replay lines.
- **Failure scenario (false PASS):** a v1 agent announces a child in the turn. On `session/load` it replays the
  child's `agent_message_chunk` without replaying the `subagent_update`. 001 PASSes. The v2 counterpart rule FAILs
  the same behaviour. Probe A: live announce + chunk, then a load window with only the child chunk →
  `child_session_traffic(...) == ({'c'}, [])`.
- **The other direction, which a fix must handle:** the RFD exempts historical addresses from the announcement rule
  during replay.
  - RFD:942-948: a recorded directed message "may still be replayed with its available participant metadata ... when
    the other participant's association ... is unavailable. A historical address is not an announcement".
  - RFD:638-639: "A replayed reference to a session that is not available follows the historical replay rules".
  - Today the carried-over `known` set masks this. But an agent that rebuilds history from provider transcripts
    (RFD:960-961) can replay a `session_message` that names a child it never exposed live (exposure is optional,
    RFD:201-203). 001 (or 002, for a `session` reference) then FAILs a CAPABILITY row for allowed behaviour.
- **Fix options** (needs an orchestrator decision, because no v1 decision exists):
  - (a) Scope known children to the load exchange for traffic inside it, as RESUME-209 does. Exempt replayed
    `session_message` participants and `session` references inside that window. Drain the quiet period *before*
    sending `session/load`: `exposes_subagent.py`'s post-turn child chunk would otherwise land in the window, the
    same issue M2 fixed for RESUME-209.
  - (b) Drop the replay claim from 001's text and leave replay to a v1 LOAD-side row.
- **Confidence:** confirmed by running (probe A) and by reading the RFD.

### 2. nit: 015 validates whole tool-call and permission messages, so a non-subagent defect can FAIL both 015 and `ACP-PROMPT-002`
`src/tck/v1/conformance/_helpers.py:730-768`

- **Defect:** a `tool_call`/`tool_call_update` update, or a `session/request_permission` request, that carries a
  `session` item is validated in full. So a defect in any of its other fields counts too: `status`, `kind`, or the
  permission `options`.
- **Failure scenario:** an agent whose tool calls always carry an invalid `status` FAILs `ACP-PROMPT-002` on the
  default connection. It also FAILs `ACP-SUBAGENT-015` on the subagents connection, through its spawn tool call that
  carries a `session` item. That is one defect in two rows. Probe B: `tool_call_update` with `status: "bogus"` and a
  `session` item gives a 015 problem at `/update`.
- **Impact:** the row text says it judges the whole message, and the verdict is unchanged, because PROMPT-002 is
  MANDATORY and FAILs anyway. Only the report is noisier.
- **Fix:** for these two carriers, validate only the `session` items against `#/$defs/ToolCallContent`
  (`SessionReference`).
- **Confidence:** confirmed by running.

### 3. nit: a `session/load` that never answers FAILs all 14 subagent rows
`src/tck/v1/conformance/test_subagents.py:96-103`

- **Defect:** the comment says "A failed load is ACP-LOAD-001's finding; only the traffic seen is judged here". But
  an `AgentTimeout` from `wait_for_response(load_id, ...)` is not caught. It is cached and re-raised in every row.
- **Failure scenario:** an agent whose load hangs, even one that exposes no subagent, gets FAIL on 001-009/015 (and on
  the ADVISORY rows) instead of SKIP. The verdict is already NOT CONFORMANT through `ACP-LOAD-001`, so the only effect
  is 14 misattributed FAILs. `test_client_capabilities.py:110-116` has the same pattern.
- **Fix:** catch `AgentTimeout` on the load wait and go on to the quiet period.
- **Confidence:** confirmed by reading.

### 4. nit: `docs/mock-client.md` says the subagent connection is "the one exception" to "no capabilities"
`docs/mock-client.md:10-12`

- `src/tck/v1/conformance/test_plan.py:37` already advertises `{"plan": {}}`, so the claim is false.
- **Confidence:** confirmed by reading.

### 5. nit: a fixture docstring points at a name that does not exist in v1
`tests/fixtures/agents/v1/exposes_subagent.py:17`

- It cites "`_SUBAGENT_EXERCISED_IDS` in `tests/v1/test_cli.py`". v1 defines `_SUBAGENT_IDS`. Only v2's test_cli has
  `_SUBAGENT_EXERCISED_IDS`.
- **Confidence:** confirmed by grep.

### 6. nit: 009's row text overstates the third-session case
`src/tck/v1/requirements.py:1301-1325`; `_helpers.py:942-972`

- **Defect:** the text says conflicting references FAIL "including when the referenced view's own sender or
  recipient is a third session". The check compares only the back-reference `messageId`.
- **Probe C:** outgoing view `(p, m1)` → `recipientMessageId: m2`. Incoming view `(c, m2)` has
  `senderSessionId: x` and `senderMessageId: m1`. Result: `links_judged=1`, no violation. The reference resolves in
  `x`'s transcript, so the views do not name each other.
- In practice 001 FAILs the unknown `x` first, so this is a wording issue. The code is the same as v2's.
- **Confidence:** confirmed by running.

### 7. nit: failure messages of RFD-only rows carry no stage label
`src/tck/v1/conformance/_helpers.py` (messages of 003/004/005/007/008/009/014)

- `docs/requirements.md` "Citations" requires the label "in the row text and in any failure message that relies on
  it". The 003 message ("announces that same session as its own child") and the others carry no "(Active RFD)".
- v2's helpers have the same gap, which M2 did not flag.
- **Confidence:** confirmed by grep.

### 8. nit: the v1 subagent helpers have no unit tests
`tests/v1/` has no counterpart of `tests/v2/test_helpers.py`.

- The 24 fixtures cover the main paths. These edges are exercised by nothing in v1:
  - grouped select options (014);
  - the cycle branch of 005;
  - a nested announcement sent on a not-yet-announced child;
  - Windows/UNC paths in `is_absolute_path`;
  - `null`-clears in `_patched`;
  - a `session` reference inside `session/request_permission` combined with a malformed `toolCall`.
- **Confidence:** confirmed by reading.

## Checked and correct

- **v1 carriers:**
  - Permission: `session_content_references` and `subagent_shape_issues` read `params.toolCall.content`. That matches
    v1 `RequestPermissionRequest` (`toolCall: ToolCallUpdate`), so M2's carrier bug does not recur.
  - v1 `SessionUpdate` has no `tool_call_content_chunk`. The kinds are checked against the vendored schema, and no
    helper looks for one.
  - 014 handles v1 `SessionConfigSelectOptions` both flat and grouped (`SessionConfigSelectGroup.options`) and skips
    `boolean`.
- **001 and `fs/*`/`terminal/*`:**
  - `schema.mdx:8709-8713` ("any live child traffic") and RFD:95-99 ("filesystem, and terminal requests where
    supported by the protocol version") support judging the announcement for any request with a child `sessionId`.
  - The row says correctly that whether such a request may be sent at all is not judged on this connection.
  - `child_fs_request_before_announce.py` FAILs only 001, unscoped.
- **Tiers, gates and citations at 3961af94:**
  - These lines all say what the rows claim: `schema.mdx:8705-8707,8709-8713,8741,8760,7249,7263`,
    `tool-calls.mdx:349-351`, `prompt-turn.mdx:46-50,96-100,106-111`, and RFD
    `:95-99,122-124,165-169,189-193,298-308,392-419,461-481,466-475,636-638,648-664,815-829`.
  - MUST rows are CAPABILITY/`inferred:subagents`. SHOULD rows (011-014) are ADVISORY with `capability=None`. Docs
    are cited first where they state the rule.
  - No `@pytest.mark.capability` is used, and the marker guard passes.
- **Rule B:**
  - 001-009 and 011-014 state the same rules as v2. The differences are only the v1 carrier and kind
    (`user_message_chunk`; `fs/*`/`terminal/*` "where supported").
  - 010 is not reused, and 201 has no v1 row.
  - 015 has no v2 row. It overlaps no other v1 schema row on the same connection: `ACP-PROMPT-002` and
    `ACP-SCHEMA-001` run on their own connections, which do not advertise `subagents`. Finding 2 is the only
    cross-connection overlap.
- **No vacuous PASS:**
  - Every SKIP condition counts what was actually judged: 006 `reported_directories`, 007/008
    `participants_judged`, 009 `links_judged`, 012 `judged`, 013 `streamed`, 014 `selects`, 015 `judged`.
  - For every row, a non-empty problem list implies the judged count is non-zero (for 001, a problem implies a
    non-client session ID is in `children`), so no SKIP can hide a violation.
  - `session_message_without_participants.py` SKIPs 007-009, and `child_task_as_user_message.py` SKIPs 012
    (test_cli asserts both).
- **CLIENTCAP-007:** only `test_subagents.py:88` advertises `subagents`. `exposes_subagent.py` gates all child
  traffic on `"subagents" in self._client_capabilities`, and CLIENTCAP-007 PASSes for it and for every violator.
- **Shared cached connection:**
  - It is made once per process (`config.stash`). A cached `Skipped` (AUTH-GATED / VERSION-MISMATCH) re-raises as
    a SKIP in every row.
  - Wire order includes requests, and responses are skipped.
- **Ledger:**
  - The three "TCK never advertises" v1 entries are deleted in the same change that adds 002, 006 and 011/012, and
    no v1 entry still rests on that choice.
  - `docs/docs.json` at 3961af94 puts get-auth-state, session-status, session-set-title and proxy-chains under
    "Draft", and subagents under "Active". All 18 labels are right, and no RFD citation in either ledger is
    unlabelled.
- **No `.agents/` references** in src/, tests/, docs/, README.md or spec-tracker/maps/.

## Opinion on the deferred follow-ups

- **S11 (child fs/terminal/elicitation request on a connection that advertises none): worth adding, cheaply, but not
  as a new SUBAGENT row.**
  - The binding rule is the docs MUST behind `ACP-CLIENTCAP-001..003`: no `fs/*`/`terminal/*`/`elicitation/create`
    unless the client advertised it. Docs take precedence, so widen those MANDATORY rows to also scan the subagents
    connection, which advertises none of the three, rather than add an RFD-capped CAPABILITY row for RFD:210-217.
  - Value is modest. It catches only agents that use these methods from children alone, because other violators
    already FAIL on the default connection.
  - Side effect: `child_fs_request_before_announce.py` would then FAIL CLIENTCAP-001 as well. Those are two real
    defects, so that is acceptable, but its expected set changes.
- **S20 heuristic: not worth a verdict-affecting row.** "When the v1 Agent observes ..." (RFD:831-832) cannot be
  known, so any FAIL would be a guess. At most, add an INFORMATIONAL row recording whether children that produced
  output got `running`/`idle` snapshots. The `state` shape is already covered by 015.
- **S9 (explicit `cwd` on a child `terminal/create`): agree it is untestable now.** The mock client implements no
  terminal. Under the ledger rules it should still be recorded, as a `[[not_requirement]]` marked "Deferred" that
  names the real blocker: the mock client has no terminal implementation, not "the TCK doesn't advertise it". It is
  not in `v1.toml` and not on the P10 list, so fold it into S4.2.

## Adjacent (pre-existing, not M3)

- `docs/mock-client.md:6-7` says a subagent's permission request "is never held and is not cancelled by the
  trigger". v1's `run_prompt` (`_helpers.py:507-516`) answers *every* permission request `cancelled` once the trigger
  has fired, whatever its `sessionId`. This line is context in the M3 diff, not changed by it. It is likely a v2-only
  statement.
