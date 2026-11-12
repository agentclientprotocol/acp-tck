# Review: M4 (S4.1 2a06957, S4.2 c298410) + spot-check of S5.4 (d29fc6a, fce8678)

Reviewed in a detached worktree at c298410. Spec read at 3961af94 (`git show`). Full product suite at
c298410 with `-n auto`: **966 passed (317 s)**. Experiments used throwaway fixtures under `/tmp`, not
committed.

Counts: **0 blockers, 3 should-fix, 9 nits.**

## Should-fix

### S1. Child-cancel race excuse accepts any non-cancelled idle at any time, so a child that ignores its cancel SKIPs instead of FAILing ACP-SUBAGENT-016/017

- `src/tck/v1/conformance/_child_cancel.py:120-123`, `src/tck/v2/conformance/_child_cancel.py:184-187`
  (both set `outcome = "raced"` for the target's first idle that is not `cancelled`, for the whole
  `timeout / 2` window); `test_subagent_controls.py:74` (v1) / `:69` (v2) SKIP both rows on `raced`.
- **Defect:** RFD:1093-1095 excuses only a cancel that races with work that had *already ended*. The
  driver applies the excuse to any idle with any `stopReason` (or none) that arrives within `timeout / 2`.
  The prompt-turn cancel rows use a much narrower rule (`skip_if_turn_end_race_not_exercised`: only
  idles within `quiet_period(timeout)` with a race-plausible stop reason). This is the M5 S2 pattern
  carried over: an "any outcome is a race" excuse.
- **Failure scenario (confirmed by running, both versions):** I wrote a fixture that subclasses
  `cancellable_subagent.py`. Its `_cancel_child` sleeps 1.5 s and then reports `idle`/`end_turn`. In
  other words, the child ignores `session/cancel` and finishes its work on its own. With
  `--timeout 4 --cancel-prompt __hang__ -k test_subagent_controls`, v1 and v2 both report
  `ACP-SUBAGENT-016 SKIPPED` and `ACP-SUBAGENT-017 SKIPPED` ("ended on its own before the agent read
  session/cancel"). The same behaviour with a 1.5 s delay on the parent turn would FAIL the
  `ACP-CANCEL-*` rows.
- **Fix:** bound the excuse to a race window, as `test_cancel.py` does: only an idle within
  `quiet_period(timeout)` after the cancel counts, plus `race_plausible(stopReason)` if wanted. A later
  non-cancelled idle FAILs 016, and 017 is still judged. Add a violator fixture with a delayed
  `end_turn`. `child_ends_before_cancel.py` stays a SKIP because it answers immediately.
- Severity: should-fix. Confidence: confirmed by running.

### S2. ACP-SUBAGENT-202 false-FAILs a background child that was announced after the parent's latest snapshot

- `src/tck/v2/conformance/_child_cancel.py:213-223` (`_waited_on`) and `:297-303` (`cascade_targets`
  taken from the parent's latest `background` list at the moment the TCK sends its parent cancel).
- **Defect:** The driver treats "not in the parent's latest list" as foreground. But
  prompt-lifecycle.mdx:206 requires the announcement *before* the first snapshot that lists the
  item, and re-sending the state when the list changes is only a SHOULD (:205). So a child announced
  after the latest snapshot may be background work that no list names yet. The repo already says
  this twice:
  - the text removed from `ACP-STATE-209` in S5.4: "an announced item that no list names yet cannot
    be told from foreground work";
  - the v2 ledger entry at `spec-tracker/maps/v2.toml` (prompt-lifecycle.mdx:210): "a client cannot
    tell whether a `running` … child is detached work … or foreground work".
- **Failure scenario (confirmed by running):** I wrote a v2 fixture that subclasses
  `cancellable_subagent.py`. It adds a third child `-child-bg`, announced as running after the
  parent's `running` snapshot (`background: []`), and does not re-send state (it skips only the SHOULD
  at :205). It lists the child in the cancel-time idle snapshot and leaves it running. With
  `--timeout 2` the result is `ACP-SUBAGENT-202 FAIL`: "descendant(s) ['sess-0001-child-bg'],
  running and not in a `background` list, did not reach idle". That FAILs a CAPABILITY row for an
  agent that missed only a SHOULD.
- **Fix:** judge only descendants whose parent reported a `background` list *after* the
  descendant was announced, or after its latest `running` report. A child with no list since its
  announcement is unclassified, the same as "list never reported". Also, a descendant that appears
  in the post-cancel idle's own list could be exempted. Add the fixture above as a conforming case.
- The rest of 202's rule holds up: only foreground descendants are judged, and the row SKIPs when the
  parent never reports a list. prompt-lifecycle.mdx:204 makes an omitted list mean "unknown", so the
  SKIP is required by the docs and does not hide violations the docs let a client see. Most real
  agents will SKIP 202 for this reason.
- Severity: should-fix. Confidence: confirmed by running.

### S3. The new v2 ledger entry calls the general entity-ID reuse rule unobservable, but rows already judge observable cases of it

- `spec-tracker/maps/v2.toml:204-206` (prompt-lifecycle.mdx:67 + RFD:439-441).
- **Defect:** the reason says "reuse for a different entity cannot be told from a legitimate update".
  That is false for part of the rule:
  - `ACP-PATCH-203` FAILs two `session/prompt`s answered with the same `messageId`. These are two
    distinct user messages, which is reuse for a different entity. It cites :368, not :67.
  - `ACP-CANCEL-002` judges `messageId` reuse after a cancelled idle.
- The entry also overlaps the existing `terminalId` reuse entry (`v2.toml:592`).
- **Failure scenario:** a spec update that touches :67 sees the line ledgered as "deliberately
  untested" even though rows test part of it. That breaks the ledger's "not covered on purpose vs
  missed" purpose (docs/requirements.md:147-158), and the reason is untrue as written.
- **Fix:** narrow the statement and reason to the unobservable part, i.e. a repeated ID in an update
  that cannot be told from an upsert. Name `ACP-PATCH-203`/`ACP-CANCEL-002` as covering the observable
  cases, as the S10 entry does for `ACP-SUBAGENT-005`.
- Severity: should-fix (low). Confidence: confirmed by reading.

## Nits

### N1. The ACP-SUBAGENT-017 sibling half can FAIL an Agent that legitimately stops its own delegated work

- `_child_cancel.py:124-130` (v1) / `:188-194` (v2). RFD:1071-1073: the per-child capability "does
  not prevent the Agent from cancelling its own delegated work".
- **Scenario:** a parent model that reacts to one child's cancellation by stopping a sibling within
  `quiet_period` is FAILed. That is indistinguishable on the wire from a cancel that leaked.
- **Fix:** state the limitation in the row text, or judge only siblings whose cancelled idle arrives
  within a short window of the child cancel.
- Confidence: plausible.

### N2. The drivers' own cancels bypass `run_prompt`'s trigger, and `run_prompt`'s own fallback cancel is not excluded from 017

- **Permission answers.** `run_prompt` keeps answering permission requests per the `allow` policy
  after the driver's `session/cancel` for the child or the parent (v1 `_helpers.py` ~507-524; v2
  only answers `cancelled` once its own trigger has fired). That goes against the client MUST at
  RFD:1126-1128 and v1 prompt-turn.mdx:640. Only requests in flight at the cancel are affected.
- **Fallback cancel in v1.** When a permission request offers no allow option, `run_prompt` sends
  `session/cancel` for the *prompted* session, even when the request is a child's. The parent then
  ends `cancelled`, and 017 FAILs ("the parent's prompt was answered cancelled").
- **Fallback cancel in v2 (pre-existing on main 13c4f7a).** `_helpers.py:1959-1962` cancels the
  *request's* session, i.e. a child, whether or not that child advertises `cancel`. That is a client
  MUST NOT (RFD:1033-1036), and inside the child-cancel run a resulting sibling `idle`/`cancelled`
  FAILs 017.
- Low probability, because real permission requests normally include allow options. Recorded as a
  follow-up for whoever owns `run_prompt`.
- Confidence: plausible (read).

### N3. The v2 child-control defect test does not pin the PASS/SKIP sets its fixtures' docstrings claim

- `tests/v2/test_cli.py:4430-4441` asserts only that the intended row is the single FAIL. The v1 twin
  asserts every row. For example, `child_cancel_ignored.py`'s docstring claims 017 and 202 PASS; a
  regression to SKIP would go unnoticed.
- I ran all seven v2 fixtures, and the statuses currently match the docstrings
  (`child_cancel_cancels_parent`/`_sibling`: 202 SKIPPED).
- Confidence: confirmed by reading and running.

### N4. The v2 JSONRPC-003 helper docstring claims coverage that does not exist

- `src/tck/v2/conformance/test_jsonrpc.py:100-103` says "An exit after `session/cancel` is
  `ACP-CANCEL-*`'s concern". Since d29fc6a, an agent that crashes on an idle `session/cancel` no
  longer FAILs v2 JSONRPC-003. Only INFORMATIONAL `ACP-INFO-CANCEL-201` records it, and no CANCEL row
  judges it. This matches v1 and is probably intended, but the pointer should name `ACP-INFO-CANCEL-201`.
- Confidence: confirmed by reading.

### N5. The v1 S20 ledger entry is labelled "Deferred" but names no blocker

- `spec-tracker/maps/v1.toml:352-354`. The reason is unobservability plus "the heuristic goes beyond
  the cited text". docs/requirements.md:157-158 reserves "Deferred" for an entry that "names the real
  blocker".
- **Fix:** label it "Unobservable", or name what would unblock it.
- Confidence: confirmed by reading.

### N6. In v2, item probes started after the parent cancel are not awaited, and an in-flight one becomes "raced"

- `src/tck/v2/conformance/_child_cancel.py:305-313` (the loop ends on the cascade alone) and `:367-369`
  (a tried probe still at `none` becomes `raced`).
- **Scenario:** a child item turns cancellable during the cascade, the TCK sends `tool_call/cancel`,
  and the run ends before the reply. TOOLCANCEL-203 SKIPs as "already final", so a missing response
  is hidden.
- **Also:** at `:290-292`, when `run_prompt`'s `timeout * 3` deadline fires before the parent cancel,
  the skip reason says "the parent's turn ended before the TCK sent session/cancel". That message is
  misleading.
- Confidence: plausible.

### N7. The v1 child-cancel driver does not answer agent requests read after the parent turn ends

- `src/tck/v1/conformance/_child_cancel.py:228-230` reads lines with `read_line` after `turn_done`
  but never replies. v2 uses `answer_post_turn_requests`.
- **Scenario:** a child that asks permission after the parent's turn ended blocks for the rest of
  the 016 window and is judged `unconfirmed`.
- Confidence: plausible.

### N8. The docs don't mention the child-cancel rows

- The README `--cancel-prompt` section (README.md:102-) lists only the `ACP-TOOLCANCEL/TERMCANCEL`
  use. `ACP-SUBAGENT-016/017/202` and the child-item rows also need a prompt that makes the agent
  delegate to a cancellable child, or they SKIP.
- `docs/mock-client.md` mentions `drive_child_cancel` only in passing. It does not describe the
  child `session/cancel`, the 017 window or the cascade judgement.
- Confidence: confirmed by reading.

### N9. Timing fragility in the S5.4 race fixtures

- `races_cancel_with_completion.py` and `cancel_missing_after_completion.py` give the TCK 0.25 s to
  send its request (`--timeout 1`). If the TCK reads the final updates before it sends, the
  outcome is `none`:
  - `test_legitimate_invalid_params_is_not_a_rejection` (`tests/v2/test_cli.py:4305`) then fails on
    its skip-message assertion;
  - `test_missing_cancel_methods_are_not_hidden_by_the_race_excuse` gets SKIP instead of FAIL.
- I could not reproduce it: 3 runs with 32 `yes` CPU hogs on 16 cores all passed.
- The `-32602` grace logic in `_ItemProbe` (`_helpers.py:2474-2500`) is otherwise sound:
  - a raced `-32602` needs a final update or a withdrawal within `quiet_period`;
  - `-32601` and other codes FAIL;
  - `window` and `grace` don't interfere.
- Confidence: plausible, not reproduced.

## Checked and found sound

- **Tiers, gates, citations.** Every new or changed row's tier, gate and citation matches the spec at
  3961af94:
  - RFD:1042-1045, 1069-1073, 1075-1087, 1089-1095, 1413-1425;
  - tool-calls.mdx:440,456-459,600-605;
  - prompt-lifecycle.mdx:208,210,1173;
  - v1/v2 schema.mdx `cancel` lines 8694/10178.
- **`inferred:subagentCancel`.** The separate gate is justified. Per-child `cancel` is its own opt-in
  (like `inferred:toolCallCancel`), and 202 rightly stays on `inferred:subagents` because an omitted
  per-child `cancel` does not waive the cascade (RFD:1083-1084).
- **Ids and markers.** Rule B ids are correct (016/017 shared, 202/203/204/205 v2-only). There is no
  `@pytest.mark.capability` on the `inferred:` tests.
- **The 204/205 split** matches AUTH-208/210.
- **Who gets `session/cancel` (child-cancel drivers):**
  - only a child that advertises `cancel` and was last reported active, and only while the parent
    turn is live;
  - the parent only while its turn is live.
  - Each run uses its own connection, which is closed afterwards, so nothing leaks into other tests.
- **017's window** runs from after the child cancel to before the TCK's parent cancel. Read-order
  races only shrink it, so they can cause a false PASS but never a false FAIL.
- **M5 driver bugs.** There is no overall-deadline FAIL: an AgentTimeout from the turn is swallowed
  and every wait is bounded per step. The cached errors are only agent-caused (AgentExited,
  `session/new`), the same as other modules.
- **PATCH-211 exemption** (only a terminal that is in the idle's own list and has not exited), the
  **FORK-206** judge-before-skip, the **EXT-002** `mcp/message` probe (v1 and v2; skipped when `acp`
  is advertised; `boolean=True` is right for the v1 boolean schema), and the **v2 JSONRPC-003**
  exit-as-no-reply change: all correct.
- **S4.2 ledger.** Every citation range matches the RFD text at the pin, and no entry duplicates a row
  apart from S3. Several entries point to the rows covering their observable halves (005, 006, 001,
  016). The v1 S9 Deferred entry names a real blocker: the mock client implements no `terminal`.
- **Cross-version imports and `.agents/` references:** none in product files.
