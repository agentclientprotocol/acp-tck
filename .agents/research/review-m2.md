# Review: M2 (PR #10 follow-ups), `ca66fe2..42cd99a`

Commits reviewed: `e2de37f` (S2, ACP-STATE-210), `d315fb7` (S3, TOOLCANCEL/TERMCANCEL-206/207), `aa8049f` (S4,
TOOLCANCEL/TERMCANCEL-208/209), `42cd99a` (S5, MCP ledger). I skipped the `chore: record` commits.

**Counts:** blocker 0, should-fix 1, nit 4.

I checked all the spec citations against the pin `3961af94` with `git show`. These lines say what the rows claim:
`tool-calls.mdx:440,456,458,459,587,600,602,604,605`, `prompt-lifecycle.mdx:152,184,186,205,207,208` and
`background-work.mdx:126,165,193`. The tiers follow `docs/requirements.md` and the
`-204`/`-205` precedent: a CAPABILITY rejection row with an `inferred:` gate, plus a separate ADVISORY code row. The ids are
v2-only `2xx` and the next free numbers. The two deferred `[[not_requirement]]` entries are deleted in S4, the
same change that adds the rows. The `:205,207` entry is narrowed to `:207` in S2. Nothing in the product code or the tests cites `.agents/`,
and nothing crosses between v1 and v2. S5 rewords all seven MCP reasons as "Deferred" and names the real blocker,
as `requirements.md:154-156` allows. It also corrects the v2 capability path to `capabilities.session.mcp.http`. I
found nothing wrong in S5.

## Findings

### 1. The main item-cancel probe re-targets the item the not-cancellable probe has in flight, so ACP-TOOLCANCEL-201 can false-FAIL

- **Where:** `src/tck/v2/conformance/_helpers.py:2527-2537` (`_ItemProbe.step` picks from `_live(tracker)` and
  ignores the follow-ups). It interacts with `_helpers.py:2604-2613` and `:2686-2689`.
- **Defect:** follow-ups wait while the main probe is in flight, but the main probe does not wait for them.
  `_UncancellableProbe` can send `tool_call/cancel` for item X while X has no `cancel`. If X then gains `cancel`
  while that request is in flight, the main probe sends a second `tool_call/cancel` for the same X. The main row
  then judges the agent's answer to a duplicate request that the TCK itself caused.
- **Failure scenario (confirmed by running):** I used a throwaway fixture, `/tmp/m2review/dup_cancel.py`, outside the repo. It subclasses
  `_base.ConformingAgent` with `cancellable_work` and `uncancellable_work`:
  - A cancellable tool call ends at once. The gate holds and the main probe is not done.
  - When the not-cancellable request for `tool-fixed-0001` arrives, the agent advertises `cancel` on it and
    accepts.
  - It answers the second request for the same item `-32602` ("already being cancelled") while the item still
    advertises `cancel` and has not finished.

  Result with `-k test_item_controls --cancel-prompt __hang__ --timeout 1`:
  - `ACP-TOOLCANCEL-201 FAIL`, with `ItemCancel(outcome='rejected', item_id='tool-fixed-0001', error={'code': -32602,
    'message': 'already being cancelled'})`;
  - `ACP-TOOLCANCEL-208 SKIPPED` (raced).

  Without the extra probe, the single main request would have been accepted. The programmers' note 5 says the
  worst case is that the main row SKIPs. That is true only when the duplicate gets a result, or a `-32602` with a
  prompt final update or a withdrawal. A `-32602` while the item stays live and advertised is judged `rejected`.
  This happens with real agents whose first, short cancellable item ends before the main probe reaches it.
- **Suggested direction:** keep the main probe off an item that a follow-up has in flight. The cheapest version
  excludes `_UncancellableProbe.result.item_id` from `_live` until that probe is done. The symmetric half is
  finding 2.
- **Severity:** should-fix. **Confidence:** confirmed by running. The failure needs an agent that answers a
  duplicate cancel with `-32602`, which is defensible behaviour.

### 2. The not-cancellable probe can target the item the main probe already cancelled, so a 202 defect cascades into 208

- **Where:** `src/tck/v2/conformance/_helpers.py:2675-2690` (`_UncancellableProbe._target` does not exclude
  `self.main.tried`).
- **Defect:** an agent may accept the main cancel for X, stop advertising `cancel` at once (`capabilities: null`)
  and finalize X slowly. If the final update misses `timeout / 2`, the main probe is `unconfirmed` (202 FAIL) and
  done. X is then "live without `cancel`", so the not-cancellable request goes to X.
- **Failure scenario (plausible, by reading):** the agent answers the repeated cancel for an item it is already
  cancelling with `{}`, an idempotent accept. `ACP-TOOLCANCEL-208` then FAILs next to `-202`: one defect, two
  CAPABILITY rows. A conforming agent answers `-32602` there, and `withdraws_cancel_on_request.py` already relies on
  this re-targeting to PASS 208/209. So this is only a cascade, but the fixture tests would not show it.
- **Severity:** nit. **Confidence:** plausible, by reading.

### 3. Some ACP-STATE-210 branches have no test: the main "idle that omits K" FAIL and every unjudged path (programmers' note 1)

- **Where:** `src/tck/v2/conformance/test_background.py:276-289`, and `tests/v2/test_cli.py:1740-1762`.
- **Defect:** the negative fixture `background_start_not_resent.py` only reaches the end-of-loop "no `state_update`
  followed" FAIL (`:285-287`). Nothing covers these paths:
  - the row's main FAIL case, an `idle` whose list does not name K;
  - the false-FAIL guards that keep real agents safe: a non-idle next state (`:282`), an idle with no list, and K
    ending before any snapshot (`:266-268`).
- **Failure scenario:** suppose a later edit drops the `else: unjudged |= pending` branch or the `pending = set()`
  reset. Every agent whose next snapshot after an idle-time announcement is `running` would then FAIL 210, and no
  CLI test would go red. Two hook overrides would cover it:
  - a conforming one that announces the item and then sends `running`;
  - a defect one that re-sends an idle that omits the item.
- **Answer to note 1:** it is a real gap, but in regression protection, not a current defect. The branch logic is
  correct as written.
- **Severity:** nit. **Confidence:** confirmed by reading.

### 4. The ACP-STATE-210 citation omits `prompt-lifecycle.mdx:208`, which its text relies on

- **Where:** `src/tck/v2/requirements.py`, ACP-STATE-210 `citation`, which cites `:152,184,186,205`.
- **Defect:** the row text says a tool call and its terminal "stand for each other" in the list. That comes from
  `:208` ("Process-backed work is listed as its terminal"). The test docstring cites `:208`, but the row does not.
- **Failure scenario:** a spec update that moves or changes `:208` would not flag 210 for re-review.
- **Severity:** nit. **Confidence:** confirmed by reading.

### 5. The `conforming_full` whole-suite docstring is stale for 206-209

- **Where:** `tests/v2/test_cli.py`, the `test_v2_conforming_full_agent_passes_everything` docstring (around
  `:776-800`).
- **Defect:** it still lists only `-201/202` PASS and `-204/205` SKIP. The expected-skip set now leaves out
  206-209, so they must PASS there, and `uncancellable_work=True` is not mentioned.
- **Failure scenario:** a maintainer who reads the docstring adds 206-209 to that skip set "to match" and loses the
  only whole-suite PASS-side coverage of 208/209.
- **Severity:** nit. **Confidence:** confirmed by reading.

## Judgement on the programmers' flagged points

1. **210 unjudged paths:** a real coverage gap; see finding 3 (nit). The logic matches the decisions: only the
   first `state_update` after the announcement is judged, and a listed tool call counts as listing its terminal
   (`_is_listed`, `test_background.py:92-105`).
2. **`cancel_missing_after_completion.py` and its 207 cascade:** sound. The fixture advertises `cancel` but does not
   implement either method. `-32601` for an unknown id therefore contradicts `:459/:605` for an agent that showed
   the feature. That is the same defect, and only the ADVISORY rows FAIL. The docstring lists the cascade, as
   `docs/writing-tests.md` ("any intended cascade") requires. Narrowing the fixture would hide a real consequence.
3. **`uncancellable_work` is opt-in:** fine. PASS-side coverage comes from `conforming_full.py`, both in the
   `-k` run (`test_cancellable_items_pass_the_cancel_rows`) and in the whole suite, since its skip set leaves out
   206-209. The defect fixtures set the knob, and `uncancellable_work_only.py` covers the gate. The only cost is
   that no main-row defect fixture also has a live item without `cancel`, so findings 1 and 2 are not exercised.
4. **A result for an item that finished but never advertised `cancel` FAILs 208:** sound. `tool-calls.mdx:459/605`
   name `-32602` for both "already final" and "not cancellable". With no `cancel` advertised, neither the
   "work finished first" leniency of `:458` nor the client rule applies. One weak point:
   `uncancellable_finishes_first.py` has the agent answer `-32602`, so it only shows that an error is not a false
   FAIL. No fixture shows that a result after the final update FAILs. That path is the default one, so this is low risk.
5. **The main probe may target an item that gains `cancel` mid-flight:** worse than the note says. It can be a
   CAPABILITY false FAIL; see finding 1 (should-fix, confirmed).
6. **Race grace:** I found no false FAIL beyond the inherent one, an advertisement that arrives later than
   `quiet_period(timeout)` (at least 0.5 s) after the response. The wire order covers advertisements the agent
   emitted before it read the request: `observe` runs after the send, so a late read still sets `gained`. The
   false-PASS side is bounded too. An agent that accepts every cancel and whose items gain `cancel` right after
   announcement gets a 208 SKIP rather than a PASS, and 206 still FAILs it. `uncancellable_becomes_cancellable.py`
   puts the terminal's advertisement 0.15 s after the response, well inside the 0.5 s floor.

## Not checked

- I did not run the full suite (the orchestrator is running it). I did not check whether the
  `uncancellable_work` items in `conforming_full.py` disturb other `__hang__` rows in the whole-suite run. Its
  exact skip set would catch that.
- The throwaway fixture `/tmp/m2review/dup_cancel.py` is outside the repo and was not added to it.
