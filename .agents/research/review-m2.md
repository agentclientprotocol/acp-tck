# Review: M2 (v2 ACP-SUBAGENT-001..014)

Range reviewed: `b9021ac^..2839220`. The brief gives `c042418^..2839220`, but `c042418^` *is* `b9021ac`, so I widened
the range by one commit to include 001. Product commits: b9021ac, f9f9b99, 28a0f22, 08f59b4, 28eb901. I skipped the
`chore:`, `docs:` and spec-tracker commits. I read the spec at pin `3961af94` with `git show` in the spec checkout. I
did not pull it, because I don't run git commands that write.

## What I ran

- `uv run pytest -n auto tests/v2/test_cli.py -k "subagent or session_message or session_content or child"`:
  22 passed. This includes `test_exposes_subagent_passes_everything` and
  `test_replays_subagent_history_passes_everything`.
- Full unscoped `acp-tck --protocol-version 2` runs against all 17 M2 violator fixtures. Each one FAILs exactly its
  intended row. `unannounced_child_update.py` FAILs exactly `{ACP-PROMPT-002, ACP-SUBAGENT-001}`. No row outside the
  `-k` scope fails.
- Small probes of the helpers through `tests/v2/test_helpers.py`'s `_traffic`/`_update` builders. The results are
  quoted under each finding.

## Findings

### 1. blocker: `session_content_references` reads a `toolCall` field that v2 permission requests don't have
`src/tck/v2/conformance/_helpers.py:738-741`

- **Defect:** for `session/request_permission` the helper reads `params.toolCall.content`. In v2 there is no top-level
  `toolCall` (`RequestPermissionRequest` properties at 3961af94: `sessionId, title, description, subject, options,
  _meta`). The tool call sits at `params.subject.toolCall` when `subject.type == "tool_call"`
  (`#/$defs/ToolCallPermissionSubject`). `permission_subject_keys` in the same file already reads it from there.
- **Failure scenario:** a v2 agent asks permission for a spawn. The RFD names this case at `subagents.mdx:631`:
  "a spawn that needed permission". The permission's `subject.toolCall.content` holds
  `{"type":"session","sessionId":"ghost"}` for a session that was never announced. `ACP-SUBAGENT-002` never sees the
  reference, so it SKIPs ("no `session` tool-call content item"), or PASSes if some other reference exists.
- **Probe:** a schema-valid request of that shape gives `session_content_references(...) == ([], [])`.
- **Also affected:**
  - The row text (`requirements.py:374`, "a `session/request_permission` request's `toolCall.content`") describes the
    wrong path.
  - The unit tests (`tests/v2/test_helpers.py:377,392,433`) use the v1-shaped `params.toolCall`, so they lock the bug
    in.
- **Confidence:** confirmed by running and by reading the schema.

### 2. should-fix: `ACP-SUBAGENT-010` is v2-only but has a shared-range number
`src/tck/v2/requirements.py:537`

- **Defect:** the rule is "a child's own `state_update` is mirrored on the parent's `subagent_update.state`". It has
  no v1 counterpart. RFD `subagents.mdx:745-749`: "V2 work-state notifications use this child-addressed stream and are
  mirrored on the parent association; v1 reports work state through the association". So under rule B
  (docs/requirements.md "A `2xx` number is a v2 rule with no v1 counterpart") it should be `ACP-SUBAGENT-2xx`.
- **Failure scenario:** M3 (S3.2) adds the v1 versions of P2-P7 with shared ids. v1 then either has no 010 while 011+
  are shared, or reuses 010 for a different rule. Either way it breaks "a shared id is a shared rule". Renumbering is
  cheap now, before any v1 row or release exists.
- I checked the others: 001-009 and 011-014 all apply in both versions (the RFD's v1 paths: `subagents` capability,
  v1 `user_message_chunk`, v1 config options).
- **Confidence:** confirmed by reading.

### 3. should-fix: several rows PASS when nothing was judged
`src/tck/v2/conformance/test_subagents.py:149,160,172,207`

The brief asks for no vacuous PASS. These rows PASS even though nothing was judged:

- **007 and 008** SKIP only when `count == 0`, and `count` counts every `session_message` upsert
  (`_helpers.py:893`). If an agent never supplies both participants, nothing is judged, yet both rows PASS. Probe: one
  participant-less `session_message` gives `count=1`, no problems, so PASS.
- **009** PASSes whenever any `session_message` exists, even if no view carries a reference back. Real agents
  commonly report only the observed side (prompt-lifecycle.mdx:132 "The Agent reports each side only when observed").
  In that case 009 shows PASS ("views name each other") although nothing was compared. Probe: a single outgoing view
  without references gives PASS.
- **012:** `child_task_reports.started` (`_helpers.py:1070`) also counts children whose task was a `user_message`.
  The row says those children are "not judged here", yet 012 PASSes when they are the only children.
  - Confirmed: the full run of `child_task_as_user_message.py` reports `ACP-SUBAGENT-012 PASS`.
  - The verdict is unaffected (007-009 are CAPABILITY, so PASS and SKIP both count as conformant; 012 is ADVISORY).
  - But the report claims coverage that did not happen, and 007-009's row texts promise a SKIP only "when none
    appears".
- **Fix:** count judged items (pairs with both participants for 007/008, reciprocal references for 009, tasked-or-not
  children excluding user-message ones for 012) and SKIP on zero. Or state the vacuous PASS in the row text, as
  `ACP-PROMPT-002` does.
- **Confidence:** confirmed by running.

### 4. nit: `session_messages` ignores a forward reference to a view whose sender is someone else
`src/tck/v2/conformance/_helpers.py:934`

- **Defect:** the link check skips the conflict when the referenced view's own sender is set to a third session.
- **Failure scenario:** outgoing view `(p, m1)` names `recipientMessageId: m2`. View `(c, m2)` has
  `senderSessionId: x` and `senderMessageId: m9`. Both views carry references and they do not name each other, which
  violates RFD :472 "When both views carry references, they MUST name each other". 009 PASSes anyway. Probe: empty
  `unlinked_views`.
- It is an unlikely shape, so this is a nit.
- **Confidence:** confirmed by running.

### 5. nit: a malformed `additionalDirectories` FAILs both 006 and `ACP-PROMPT-002`
`src/tck/v2/conformance/_helpers.py:837`

- **Defect:** a non-list `additionalDirectories` (or a non-string `cwd`) is judged as a "relative path". The schema
  already rejects it.
- **Failure scenario:** one schema defect inside a turn FAILs both 006 and PROMPT-002. `_patched` in the same file
  leaves malformed values to PROMPT-002, so the helper treats malformed input inconsistently. Outside the turn, 006 is
  the only check, so the overlap is defensible. If it is kept, say so in the row.
- **Confidence:** confirmed by reading.

### 6. nit: two comments still describe the pre-M2 state
- **`tests/fixtures/agents/v2/exposes_subagent.py:12`:** the docstring says the fixture must PASS
  "`ACP-SUBAGENT-001..009`". It now also exercises and PASSes 010-014, plus PERM-201/202, PATCH-204/208/210/211,
  JSONRPC-202 and ENUM-203 (`_SUBAGENT_EXERCISED_IDS`).
- **`tests/v2/test_cli.py:666`:** the comment says "`ACP-SUBAGENT-001/002` SKIP", but the set below it lists
  001-014.
- **Confidence:** confirmed by reading.

### 7. nit: each of the 14 tests runs its own prompt turn
`src/tck/v2/conformance/test_subagents.py:51-63`

- **Defect:** every test calls `_connection_transcript` on a fresh connection.
- **Failure scenario:** against a real model-driven agent, that is 14 independent turns. A child spawned in one turn
  and not in another gives mixed SKIP/PASS/FAIL across rows that the docstrings call one connection ("All tests judge
  the same connection"). The "one defect FAILs one row" disjointness holds only within one turn. The run also costs
  about 14 times the time.
- This doesn't matter for the deterministic fixtures.
- **Confidence:** plausible.

## Checked and correct

- **Tiers, gates and citations (001-014) against 3961af94:**
  - Every line range says what the row claims: RFD :95-99/189-193, :122-124, :165-169, :298-308, :392-419,
    :461-481, :636-638, :648-664, :765-774; `tool-calls.mdx:740-742`; `schema.mdx:8237,8251,10189-10193,10238,10254`;
    `prompt-lifecycle.mdx:77-81,128-132,137-142,1015-1018`.
  - The RFD sits in the "Active" group of `docs/docs.json`, so the "(Active RFD)" labels are right.
  - MUST rows are CAPABILITY/`inferred:subagents`; SHOULD rows are ADVISORY with `capability=None`.
  - Where docs or schema state a rule, they are cited first (001, 002, 005, 006, 009 secondary; 010-013).
  - No test carries `@pytest.mark.capability`.
- **Wire-order logic (`_wire_messages` and the 001-006, 010, 011 and 014 helpers):**
  - Announcements count only on a known outer session, and are applied after the message itself, so a reference in
    the announcing message is not yet known.
  - A nested announcement sent before its parent's announcement correctly FAILs 001 (probe).
  - Reparenting and cycles: `parents` stays acyclic, because the first parent is always known before its child.
  - Mirror subsequence matching handles either order and repeats.
  - Trailing child traffic inside the quiet period is judged. I found no false FAIL for a conforming agent beyond the
    findings above.
- **Disjointness:**
  - 003/004/005 are disjoint through the elif chain.
  - 007/008 are disjoint (equal vs different participants).
  - 011/012 are disjoint, because a user-message task marks the child as tasked. Finding 3 is a side effect of that.
  - The full runs above confirm one FAIL per fixture.
- **Outcome changes to existing rows:**
  - PERM-201/202: valid child permission request, and `run_prompt` answers every session's request
    (`_helpers.py:1897-1935`).
  - PATCH-204/208/210/211: completed, titled `tool_call_update` on the parent.
  - JSONRPC-202 (string id) and ENUM-203 (fixture survives a `_` outcome) now PASS for `exposes_subagent.py`, and
    correctly so.
  - The RESUME-209 drain (`test_session_capabilities.py:432-434`) is correct. Without it, the post-turn child chunk
    falls into the resume window, where `known` is scoped to the exchange.
  - `unannounced_child_update.py` double-FAILing PROMPT-002 and SUBAGENT-001 is inherent in the final
    "PROMPT-002 unchanged" decision.
- **Ledger:**
  - The `tool-calls.mdx:740-742` entry is deleted in the same change that adds 002.
  - The S37 reason (`spec-tracker/maps/v2.toml:201`) is true against `prompt-lifecycle.mdx:210`. It does not rest on
    a TCK choice, and its "Deferred ... not a row yet" matches the existing "possible but not yet built" entries.
  - No other v2 ledger entry covers 001-014's rules.
- **No `.agents/` references** in src/, tests/, spec-tracker/ or docs/.

## Open question (escalated, not a finding)

The research's open question 1 asks which tier applies to declarative or lowercase RFD rules. `state.md` records no
answer. The rows affected:

- 003 and the cycle half of 005: "cannot reparent ..., refer to itself, or create a cycle".
- 007/008: "must remain consistent ... they identify different sessions", lowercase.

All of them were implemented as CAPABILITY (MUST-equivalent). That is plausible, but under the tier cap a non-MUST
RFD-only rule would be ADVISORY. The orchestrator or user should confirm.
