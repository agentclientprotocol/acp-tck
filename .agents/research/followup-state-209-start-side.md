# PR #10 follow-up: the start-side half of `ACP-STATE-209` (v2): what it takes, how big

**Sources checked:** agent-client-protocol @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (the TCK pin; read with
`git show 3961af94:<path>`; the local checkout is on a user feature branch `eugenethedev/end-turn-token-rfd-update`,
not switched or modified); drift checked against `upstream/main` @ `4aab69b4` (2026-11-16): no change to the cited
background-work bullets. acp-tck @ `f5d3aa3` (branch `pr10-follow-ups`). PR #10 body (`gh pr view 10`). Rust/Python
SDKs not consulted: they are transport libraries with no background-list logic, and this is a TCK design question
on a docs-stated rule. A2A TCK not relevant.
**Confidence:** high on the rule, tier and observability argument; medium on the exact judging window (a design
choice, listed under open questions).

## Answer

The uncovered half is the **start** clause of one SHOULD: "When background work starts or ends, the Agent **SHOULD**
send a repeated `state_update` with the current state and the updated list" (`prompt-lifecycle.mdx:205`). 209
judges only "ends". The start clause is observable in one narrow case: a terminal or tool call first announced
**while the session is `idle`**, with the session reporting background lists, that no later snapshot lists. While
idle it cannot be foreground work, because foreground work MUST report `running` when it starts (`:152`). It is
**ADVISORY**: a SHOULD in the draft docs, with the Active RFD as secondary context, gated like 209 on
`capabilities.session`. I recommend a **new row `ACP-STATE-210`** rather than widening 209. The two halves need
different scenarios and SKIP conditions, and the start half has its own false-FAIL caveat (visible housekeeping).
No existing full-run fixture produces the scenario. `confirms_cancel_after_permission_answer.py` does, but only runs
under the item-cancel `-k` scope. A new `_base.py` hook plus two small fixtures covers both sides. The ledger entry
for `:205,207` must be narrowed to `:207` in the same change. **Complexity: S** (about 150 to 180 LOC, one slice, no
harness changes). It fits in a PR with other small and medium follow-ups.

## Requirements

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| 1 | When background work **starts**, the Agent sends a repeated `state_update` with the current state and the updated `background` list (the uncovered half). | SHOULD → ADVISORY (docs state it; RFD secondary) | spec `docs/protocol/v2/draft/prompt-lifecycle.mdx:205`; `docs/rfds/v2/background-work.mdx:193` (Active RFD) |
| 2 | (already covered by 209) the same re-send when background work **ends**. | SHOULD → ADVISORY | same lines |
| 3 | Foreground work MUST report `running` (or `requires_action`) when it starts. This is the premise that makes an item announced while `idle` background activity, not foreground work. | MUST (premise, not judged here) | `prompt-lifecycle.mdx:152`; also `:146,148` |
| 4 | The Agent MAY start its own tool call for background work and list it. It sends that tool call "before the first list that names it, even while the session is `idle`". So start-while-idle is an anticipated scenario. | MAY (context) | `prompt-lifecycle.mdx:184` |
| 5 | The Agent SHOULD NOT list housekeeping it starts on its own. "If housekeeping needs to be visible, the Agent represents it as a tool call." A conforming unlisted tool call while idle is therefore possible. | SHOULD NOT (caveat; ledgered as unobservable) | `prompt-lifecycle.mdx:186`; ledger `spec-tracker/maps/v2.toml:184-186` |
| 6 | Known follow-up foreground work is reported `running` no later than the removal snapshot. This stays unobservable and stays in the ledger. | SHOULD (not judged) | `prompt-lifecycle.mdx:207`; RFD `:195` |

Quotes (spec @ `3961af94`):

- `prompt-lifecycle.mdx:205`: "**The Agent re-sends the state when the list changes.** When background work starts
  or ends, the Agent **SHOULD** send a repeated `state_update` with the current state and the updated list. A
  repeated snapshot is not a state transition, and a repeated `idle` without a new stop reason is not a new
  completion."
- `background-work.mdx:193` (RFD stage **Active**: `docs/docs.json:211` "Active" > `:217` "v2" > `:233`
  `rfds/v2/background-work`): the same sentence, word for word.
- `prompt-lifecycle.mdx:152`: "When foreground work starts, the Agent **MUST** report `running`, or `requires_action`
  if the work starts blocked on user action."
- `prompt-lifecycle.mdx:148`: "A detached task continuing to run, its progress or completion updates, and session
  metadata updates do not by themselves start foreground work."
- `prompt-lifecycle.mdx:184`: "The Agent **MAY** start a tool call of its own for such work, with a title that
  describes the work, and list it. It sends that tool call like any other, before the first list that names it, even
  while the session is `idle`."
- `prompt-lifecycle.mdx:186`: "The Agent **SHOULD NOT** list housekeeping it starts on its own, such as memory
  consolidation. If housekeeping needs to be visible, the Agent represents it as a tool call."
- `prompt-lifecycle.mdx:181`: "`pending` and `paused` tool calls are still live."
- Schema `#/$defs/ToolCallUpdate/properties/status`: "Omission leaves the status unchanged, `null` resets it to
  `pending` … A new tool call starts as `pending`." So a new tool call with no `status` is live.

Tier, per `docs/requirements.md:48,53-58`: a SHOULD is `ADVISORY`. The docs govern and the RFD is secondary
context, so cite both and label the RFD "(Active RFD)", as 209 already does.

## Details

### What the TCK currently says

- Row `ACP-STATE-209` (`src/tck/v2/requirements.py:886-903`) judges only an end while idle. Its text says: "The start
  of background work is not judged here, nor is an end during active work".
- The test docstring (`src/tck/v2/conformance/test_background.py:189-193`) gives a reason: "The start half is not
  judged: an item announced but not yet listed cannot be told from foreground work." That holds during active
  work, but not while `idle`, because of `:152`.
- The ledger entry (`spec-tracker/maps/v2.toml:189-191`, citation `prompt-lifecycle.mdx:205,207`) already calls it
  out: "Deferred: the start-side re-send (a non-final tool call or running terminal announced while the session is
  `idle`, with neither a `running` state nor a list that names it afterwards) is observable but not yet built."
- PR #10 body, "Not yet covered": "the start-side half of `ACP-STATE-209`".

### Proposed rule for `ACP-STATE-210` (ADVISORY, `capability=None`, test marked `capabilities.session`)

Run the new test over `_session_updates` (one turn plus the quiet drain, as for 206 to 209), in wire order, while
tracking:

- `state`: the latest `state_update.state`;
- `latest list`: the `background_keys` of the latest background-carrying snapshot, or `None`;
- the effective status of each item, via `PatchTracker`, which already handles the `status: null` → `pending` patch
  rule and `terminal_ids`.

A **candidate** K is an item where all of these hold:

- it is a `tool_call_update` or `terminal_update` whose key is seen **for the first time** on the connection for
  this session;
- at that moment `state == "idle"` and the latest list is reported (not `None`);
- it is live after the update: the tool call is not `completed`/`failed`/`cancelled`, or the terminal has no
  non-null `exitStatus`.

For each candidate, look at the **first `state_update` for the session after the announcement**:

- `idle` with a reported list that names K → OK. For a tool call, a listed `("terminal", t)` for a `t` in its
  `terminal_ids` also counts (`:208`: process-backed work is listed as its terminal). For a terminal, being named by
  a listed tool call that references it could also count (lenient, see open questions).
- `idle` whose list does not name K while K is still live → **FAIL**.
- `running`, `requires_action`, `unknown`, or a custom state → **unjudged**. Foreground work may have started, and
  foreground work is never listed (`:208`). `unknown` means the agent cannot tell foreground state.
- `idle` with an omitted or `null` list → unjudged. That is ACP-STATE-206's concern.
- K reaches its final status before any `state_update` → unjudged. Work that started and ended between snapshots
  leaves the list unchanged.
- No `state_update` follows before the drain ends, and K is still live → **FAIL** (never re-sent).

The test SKIPs when there is no judged candidate, with the message "no terminal/tool_call item started while the
session was idle". Record the unjudged keys with `record_property`, as 208 does (`test_background.py:180-181`). The
failure message names K and says the agent SHOULD re-send the state when background work starts
(prompt-lifecycle.mdx:205). It also says that a visible housekeeping tool call (`:186`) cannot be told apart.

Subagent items are out of scope. Whether a new child must be listed depends on the child's own state and list
(`:210`), and the ledger (`v2.toml:199-201`) already defers the checkable converse.

### Draft row text

> "When a `terminal` (no `exitStatus`) or `tool_call` (no final status) is first announced for the session while it
> is `idle` and its latest `background` list is reported, the next `state_update` for the session lists it, directly
> or (for a tool call) through a listed terminal it references: the Agent SHOULD re-send the state with the updated
> list when background work starts. Foreground work reports `running` when it starts, so an item announced while
> idle is background activity. Not judged when the next `state_update` is not an `idle` with a list (foreground work
> may have started), nor when the item ends before any `state_update`. A visible housekeeping tool call, which the
> Agent SHOULD NOT list, cannot be told apart. Judged over one prompt turn plus a quiet drain after it. SKIPPED when
> no item starts while idle. The test is gated on `capabilities.session`."

Citation: `prompt-lifecycle.mdx:152,184,205; docs/rfds/v2/background-work.mdx:193 (Active RFD)`.

### Changes to existing artifacts

- `ACP-STATE-209` text: replace "The start of background work is not judged here" with "The start of background work
  is judged by ACP-STATE-210". Fix the test docstring at `test_background.py:191-193` the same way, and the module
  docstring range at `:1` (`206..210`).
- Ledger `spec-tracker/maps/v2.toml:188-191`: `requirements.md` says "If a rule later becomes a requirement, add the
  row and delete its ledger entry in the same change". The `:205` part becomes fully covered (start by 210, end by
  209), so narrow the entry:
  - citation: `prompt-lifecycle.mdx:207 @ 3961af94…`;
  - statement: only the known-follow-up `running` rule;
  - reason: "Unobservable: whether the agent already knows of follow-up foreground work when it removes an item is
    internal to the agent."
  - Keep the `:184,186` housekeeping entry (`:184-186`) unchanged. It stays true and explains the caveat.

### Files to touch

| File | Change | ~LOC |
|------|--------|------|
| `src/tck/v2/requirements.py` | new `ACP-STATE-210` row after 209; reword 209 | +22 / -2 |
| `src/tck/v2/conformance/test_background.py` | new test; docstrings of the module and 209 | +55 |
| `tests/fixtures/agents/v2/_base.py` | opt-in knob (e.g. `background_after_idle=True`, needs `report_background_work`) plus hook `_start_background_after_idle(session_id)`, called at the end of `_finish_turn` after `_finish_outlasting_background` (`_base.py:1150`); module docstring bullet | +25 |
| `tests/fixtures/agents/v2/starts_background_after_idle.py` (new, conforming) | sets the knob | +20 |
| `tests/fixtures/agents/v2/background_start_not_resent.py` (new, defect) | overrides the hook to announce only | +25 |
| `tests/v2/test_cli.py` | add 210 to `_ADVISORY_IDS` (`:201`) and `_BACKGROUND_OTHER_SKIP_IDS` (`:336`), with an updated comment; one positive and one negative test | +25 |
| `tests/v2/test_registry.py` | id list (`:100`) and advisory set (`:319`) | +2 |
| `spec-tracker/maps/v2.toml` | narrow the `:205,207` entry | ~3 changed |

### Fixture design

- **Positive hook body**, reusing the existing helpers:
  1. `tool_call_id = self._list_background_item(session_id)` (announces an `in_progress` tool call and appends it);
  2. `self._resend_background_state(session_id)` (an idle listing K);
  3. `self._finalize_background_item(session_id, tool_call_id)`;
  4. `self._background[session_id].remove({...})`;
  5. `self._resend_background_state(session_id)`.

  This leaves nothing live at the end. Resume and fork rows (RESUME-213/217, FORK-206) are not disturbed, the
  fixture can use `_full_run` with an empty FAIL set, and it also PASSes 209.
- **Negative hook override**: allocate an id and `self._announce_background_item(...)` only, with no listing and no
  re-send. K stays live and unlisted:
  - 210 FAILs;
  - 209 SKIPs (K is never listed);
  - 208 still PASSes on the in-turn item;
  - 206 and 207 PASS.

  Expected exact FAIL set: `{"ACP-STATE-210"}`. That has to hold either in a full run or within
  `-k test_background`; use `_background_statuses`-style scoping if a full run shows cascades.
- Why the negative must leave K live: if it also finalized K and re-sent the end snapshot, the first `state_update`
  after the announcement would come after K's final status. Under the rule above that is "ended before any
  snapshot", so 210 would be unjudged and SKIP.

## Testability notes

- **Conforming:**
  - announce a live tool call or terminal while `idle`, then send an `idle` snapshot that lists it;
  - or announce it, then report `running` (unjudged);
  - or start and finish it with no snapshot in between (unjudged).
- **Non-conforming:**
  - an announcement while idle followed by an idle list without the item while it is live;
  - or no further `state_update` at all while it is live.
- **Unobservable:**
  - work that starts later than the quiet drain;
  - work that the agent never announces;
  - whether an unlisted live tool call is housekeeping (`:186`).

  A real agent rarely starts background work while idle within one drained turn, so expect mostly SKIP in the
  field. The row's value is mainly completeness and catching adapters that forget the start re-send.
- **Fixture compatibility:**
  - `conforming.py` and the agents that report no lists SKIP, so add the id to the expected-SKIP set.
  - `finishes_background_after_idle.py` sends only a final status after the idle, which is not a start, so it SKIPs.
  - `confirms_cancel_after_permission_answer.py` (`:28-44`) would PASS the row (an announcement after the idle plus
    a listing re-send), but it only runs under the `test_item_controls` scope (`test_cli.py:4333-4343`).
  - **Hypothesis, unverified:** no other full-run fixture announces a new item for the prompted session after its
    idle while reporting lists. The background fixtures I read announce items in the turn, before `running`. The
    programmer must confirm with the full `test_cli.py` run.
- **No PATCH-211 cascade expected:** PATCH-211 judges tool calls "reported for the prompted session during the turn"
  (`requirements.py:3177`). An item announced after the idle is outside it. This is also unverified; check the
  negative fixture's full-run FAIL set.

## Discrepancies

- The TCK contradicts itself. The 209 test docstring (`test_background.py:191-193`) says the start half is
  unobservable in general, while the ledger (`v2.toml:191`) says the idle case is observable. Spec `:152` supports
  the ledger for the idle case. The docstring should be corrected.
- Spec docs and the Active RFD do not conflict on `:205` / RFD `:193` (same sentence). The RFD's announce bullet
  (`:194`) also allows a `tool_call` (not just `tool_call_update`) as the announcement. That is a v1-era name, and
  the v2 schema has only `tool_call_update`. It does not matter here.

## Open questions

1. **Tier caveat (needs a user or orchestrator decision).** A conforming agent with a *visible housekeeping* tool call
   started while idle (`:186`) would FAIL an ADVISORY row. Precedent is mixed: `ACP-INFO-BACKGROUND-201` went
   INFORMATIONAL when "the client cannot tell", while `ACP-PATCH-211` stays ADVISORY despite ambiguity. Options:
   - (a) ADVISORY for both item types, with the caveat in the text. This is my recommendation: the verdict is
     unaffected, and the ledger already calls the deferred check observable.
   - (b) ADVISORY for terminals only (the docs say housekeeping is represented as a tool call), plus an INFORMATIONAL
     record for tool calls.
   - (c) INFORMATIONAL only.
2. **Judging window.** Should only the *first* `state_update` after the announcement count (my proposal: strict, and
   simple to explain)? Or should any later idle snapshot that lists K before it ends count (more lenient, more code)?
3. **Terminal named through its tool call.** Should a terminal announced while idle count as listed when the list
   names a tool call that references it instead of the terminal? That inverts `:208`'s "listed as its terminal", a
   MUST NOT that `ACP-INFO-BACKGROUND-201` only records. I recommend lenient, so 210 does not double-judge `:208`.
4. Separate row (my recommendation) versus a second test bound to `ACP-STATE-209`. Both are allowed (several tests
   per id aggregate with FAIL winning, `requirements.md:89`). A second test would make 209's SKIP and PASS mean
   "either half", and a start-side FAIL would be indistinguishable by id from an end-side FAIL.

## Risks

- **False FAIL on visible housekeeping** (open question 1). It is ADVISORY only, so the verdict is unaffected.
- **Slow agents.** An agent that re-sends the snapshot after the quiet drain FAILs. This is the same exposure as 209,
  which uses the same drain.
- **Hidden fixture cascades** in full runs (hypothesis above). They are cheap to detect with the existing
  exact-FAIL-set CLI tests.
- **Ledger hygiene.** Forgetting to narrow the `:205,207` entry would leave a "Deferred" entry for a rule that now has
  a row.

## Complexity

**S**, about 150 to 180 LOC across 8 files, all in one area (background rows):

- no new harness or helper machinery (`_session_updates`, `background_keys`, `PatchTracker`, `_key_of` and
  `_is_final` are reused);
- one `_base.py` hook built from existing helpers;
- two small fixtures;
- id-set bookkeeping in two test files;
- one ledger edit.

The only real cost is settling open questions 1 to 3 before coding, and they do not change the size. It fits
comfortably in one PR alongside other small and medium follow-ups.
