# Impact: v2 `docs/protocol/v2/draft/subagents.mdx` (new) on v2 rows and ledger

**Sources checked:** agent-client-protocol @ `3ea94133` (read with `git show 3ea94133:<path>`; the checkout
HEAD is `6ace4f6a`, one commit later, which does not touch these docs): `docs/protocol/v2/draft/subagents.mdx`
(all 500 lines), `docs/rfds/subagents.mdx` (Preview, `docs/docs.json:242-243`), `docs/protocol/v2/draft/`
`prompt-lifecycle.mdx`, `session-setup.mdx`, `session-list.mdx`, `tool-calls.mdx`, `cancellation.mdx`,
`elicitation.mdx`, `schema.mdx`; `schema/v2/schema.unstable.json` (`SubagentUpdate`,
`SubagentSessionCapabilities`, `BackgroundSubagent`: only the `**UNSTABLE**` banner was removed and a docs link
added; `AbsolutePath` is unchanged, still a bare `string`). acp-tck: `src/tck/v2/requirements.py`,
`spec-tracker/maps/v2.toml`, `src/tck/v2/conformance/{test_subagents,_child_cancel}.py`.
**Confidence:** high for the classification and citations; medium for the new-row proposals (they need user
tier calls, listed under Decisions).

Below, `doc` means `docs/protocol/v2/draft/subagents.mdx @ 3ea94133` and `RFD` means `docs/rfds/subagents.mdx
(Preview RFD) @ 3ea94133`. I give RFD target lines as I mapped them by diff. The RFD researcher
(`impact-v2-rfd-subagents.md`) owns their exact remap.

## Headline

- The doc states nearly every subagent rule the TCK currently cites from the RFD. RFD `:1232-1233` says
  so too: "The v2 rules are specified on the v2 Subagents page. Where this RFD and that page differ for v2, the
  page applies." So docs precedence applies. The doc becomes the primary citation and the RFD becomes secondary.
- **No tier rises.** The doc says "Exposing subagents is optional for Agents" (`doc:8`) and "Subagents need no
  capability" (`doc:10`). The only capability, `capabilities.cancel`, is sent per child in `subagent_update`
  and is not an `initialize` path. So no real marker replaces `inferred:subagents` or `inferred:subagentCancel`,
  and a doc MUST about subagents stays `CAPABILITY` behind the inferred gate (`docs/requirements.md` Tiers,
  `inferred:` gates). I considered and rejected CAPABILITY->MANDATORY for every doc MUST row. See D1.
- Three rows stay RFD-only (`ACP-SUBAGENT-007/008/009`). The doc does not state their rules.

## Table: rows citing the RFD or gated `inferred:subagents`/`inferred:subagentCancel`

| id | classification | target citation (primary first) | note |
|---|---|---|---|
| ACP-SUBAGENT-001 | citation-only (+ provenance wording) | `doc:68,70-78,198`; `schema/v2/schema.unstable.json#/$defs/SubagentUpdate`; RFD `:95-99,189-193` | `doc:70` states a MUST, and `doc:72,73,76` list exactly the row's three traffic kinds. Rewrite "Stated by the schema's `SubagentUpdate` and the Subagents RFD (Active RFD)" as "the draft docs and schema". Tier stays CAPABILITY. `doc:74` (session content) belongs to `-002` and `doc:75` (background list) to `ACP-STATE-207`. |
| ACP-SUBAGENT-002 | changed text (check unchanged) | `doc:70,74`; `tool-calls.mdx:741-742`; RFD `:647-649` | The row says "A reference does not count as traffic carrying the child's ID". `doc:74` now lists a `session` content item under the announcement MUST, so that sentence contradicts the doc. Reword it to "judged by this row, not by `ACP-SUBAGENT-001`, so one defect never FAILs both". Tier stays. |
| ACP-SUBAGENT-003 | citation-only (+ provenance) | `doc:68,126` ("cannot ... name its own outer session as the child"); RFD `:165-169` | Now stated by the doc, but with no RFC keyword. Drop "Stated only by the Subagents RFD ... capped". It stays CAPABILITY `inferred:subagents`, matching how the TCK encodes other no-keyword doc rules (e.g. `ACP-TOOLCANCEL-203`). |
| ACP-SUBAGENT-004 | citation-only (+ provenance) | `doc:6,68,81-83`; RFD `:122-124,165-169` | `doc:82-83` says "The Agent **MUST NOT** reuse it for an unrelated session", and `doc:6` says the Agent creates and owns the child. Drop "Stated only by the Subagents RFD". Optional extension: N8. |
| ACP-SUBAGENT-005 | citation-only (+ provenance) | `doc:68,126`; `schema.mdx:11552-11554`; RFD `:165-169` | The one-parent, no-move and no-cycle rules are now in `doc:68,126`. Change "the RFD states the one-parent, no-cycle rule" to the doc. `schema.mdx` target lines are given for the schema.mdx owner. |
| ACP-SUBAGENT-006 | citation-only | `doc:106-113,218`; `schema.mdx:11603,11619`; schema pointers unchanged; RFD `:298-308` | `doc:218`: "every path **MUST** be absolute". |
| ACP-SUBAGENT-007 | unchanged (RFD-only) | RFD `:485-488` (was 477-480) | The doc does not say "different sessions". Relabel it `(Preview RFD)`. It stays CAPABILITY under the RFD cap. |
| ACP-SUBAGENT-008 | unchanged (RFD-only) | RFD `:485-489` | `doc:302-307` says the outer `sessionId` is "the session whose transcript ... the update changes", and `doc:256` allows messages "between other known sessions". Neither states that the outer `sessionId` is one of the participants. Relabel only. |
| ACP-SUBAGENT-009 | unchanged (RFD-only MUST) | RFD `:466-475`; `prompt-lifecycle.mdx:133-137`; `schema.mdx:9413,9427` | `doc:263` adds only a SHOULD to link the views. The MUST that both references name each other is still RFD-only (`:472`). The new RFD `:477-483` and `prompt-lifecycle.mdx:150-152` (link only when the match is established) do not change the check. |
| ACP-SUBAGENT-011 | citation-only (+ provenance) | `doc:264`; `prompt-lifecycle.mdx:142-146`; RFD `:685-687` | SHOULD NOT, so ADVISORY is unchanged. |
| ACP-SUBAGENT-012 | citation-only | `doc:260,262`; `prompt-lifecycle.mdx:142-146`; RFD `:667-676` | SHOULD, so ADVISORY. `doc:262` says "before the child's response to it", which matches the row's "before the first agent output". |
| ACP-SUBAGENT-013 | unchanged (not this doc) | `prompt-lifecycle.mdx:84-86`; RFD `:461-464` | The subagents doc does not state the rule. RFD relabel only. The prompt-lifecycle researcher owns it. |
| ACP-SUBAGENT-014 | citation-only (+ provenance) | `doc:251-252`; RFD `:406-411,415-418` | `doc:252` has the SHOULD. Change "Stated only by the Subagents RFD (Active RFD)" to "the draft docs". ADVISORY is unchanged. |
| ACP-SUBAGENT-201 | citation-only | `doc:330,350-352`; `prompt-lifecycle.mdx:1288`; schema `SubagentUpdate`; RFD `:792-800` | SHOULD, so ADVISORY. New adjacent rule `doc:351`: see N5. |
| ACP-SUBAGENT-016 | citation-only (+ provenance); **decision D2** | `doc:373,378,386,398-403`; `schema.mdx:11545`; schema pointer unchanged; RFD `:1113-1117,1133-1139` | "The confirmation is stated only by the Subagents RFD" is no longer true: `doc:400` states it (no keyword, under "the ordinary cancellation rules"). `doc:400` names the child's own `state_update` as the confirmation, and the mirror is only a SHOULD (`doc:330`). The row also accepts a mirror-only confirmation. Gate `inferred:subagentCancel` stays. The id is shared with v1 (Rule B). |
| ACP-SUBAGENT-017 | citation-only (+ provenance) | `doc:398`; RFD `:1113-1117` | `doc:398` says "not the work of its parent or siblings. ... The Agent can cancel work it delegated at any time", which supports the row's choice not to judge siblings. |
| ACP-SUBAGENT-202 | citation-only (+ provenance) | `doc:405,407`; `prompt-lifecycle.mdx` (owner's remap); RFD `:1119-1131,1482-1494` | `doc:405` states the cascade, the "up to the Agent" rule, and "A child that does not advertise `cancel` is still stopped". No keyword. CAPABILITY `inferred:subagents` stays. |
| ACP-RESUME-002 | citation-only | `session-setup.mdx` (owner's remap); `doc:462`; RFD `:1047-1052` | The basis for "live child traffic not judged" is now `doc:462`. Change "(Active Subagents RFD)" to "(Subagents docs)". |
| ACP-RESUME-205 | citation-only | `doc:463-465`; `session-setup.mdx:412-417`; RFD `:1038-1045` | Same wording fix as RESUME-002. |
| ACP-RESUME-209 | citation-only | `doc:469,482,484`; `session-setup.mdx:414`; RFD `:962-972,1034-1042` | `doc:469`: "The announcement rule applies again on every resume ... announced every ancestor ... during this resume". This supports "even if an earlier turn announced it". Change "the Active Subagents RFD's rule" to the doc. See N6 for the case with no replay. |
| ACP-TOOLCANCEL-203 | citation-only | `doc:374,378`; `tool-calls.mdx:457` (owner's remap); RFD `:1081-1084` | The doc table at `:374` states the rule. |
| ACP-TERMCANCEL-203 | citation-only | `doc:374,378`; `tool-calls.mdx:603`; RFD `:1081-1084` | Same as TOOLCANCEL-203. |

These do not cite the RFD but the doc now also states their rules. Adding a secondary citation is optional:
`ACP-STATE-207` (`doc:75,356`), `ACP-PROMPT-002` (`doc:70-72,198`), `ACP-FORK-206` (`doc:440`: "The fork starts
with no background work"), `ACP-CLOSE-205` (`doc:427` extends it to descendants, see N1).

## Table: ledger entries (`spec-tracker/maps/v2.toml`)

| ledger citation (base) | classification | target citation | note |
|---|---|---|---|
| RFD 322-326 (dirs differ / SHOULD NOT share) | citation-only | `doc:239-240`; RFD `:322-326` | Reason holds. |
| RFD 381-382,387-390 (narrowest; current after resume; `null` when gone) | citation-only | `doc:241,473`; RFD same lines | Reason holds. |
| RFD 198-199,939-940 (no guessed parent) | citation-only | `doc:134,484`; RFD `:198-199,976-977` | Reason holds. |
| RFD 203-206 (no moving; exposed child uses its ID) | citation-only | `doc:135-136,413`; RFD `:203-206,1196-1197` | Add `doc:413`: a pending request stays attributed to the child and **MUST NOT** move. It is the same unobservable rule. |
| RFD 223-226 (automatic delivery, no subscribe) | citation-only | `doc:143`; RFD `:223-226` | Reason holds. |
| RFD 576-577 (each side only when observed) | citation-only | `prompt-lifecycle.mdx:137-139`; RFD `:584-585` | The subagents doc does not state this. The primary citation moves to prompt-lifecycle. The new RFD-only SHOULD NOT about failed sends (RFD `:586-588`) belongs to the RFD researcher. |
| UnknownStateUpdate; RFD 855-860 (`unknown` when lost) | citation-only, extend | `doc:360,365`; schema pointer; RFD `:881-889` | Fold in `doc:365`: "The Agent **MUST NOT** invent a final status" for unfinished items. It is unobservable for the same reason. |
| RFD 1117-1121 (close stops descendants) | citation-only | `doc:425,428`; `session-setup.mdx:476`; RFD `:1161-1165` | Reason holds. |
| RFD 1151-1153 (late response no restart) | **changed reason** | `doc:420`; RFD `:1198-1200` | The reason's second sentence relies on "the client rule at :1126-1128" (RFD `:1173-1175` at target). That rule is now **v1-only**: RFD `:1169-1170` says "This section describes v1. In v2 the Agent cancels these requests". In v2 a late non-`cancelled` answer is legitimate (`doc:420`). Delete the sentence. The first sentence alone carries the reason. |
| RFD 999-1001 (replay does not reissue requests) | citation-only | `doc:488`; RFD `:1038-1040` | Reason holds. `doc:488` also allows new live requests. |
| RFD 942-949 (no invented participant) | changed reason (cite only) | `doc:485`; RFD `:979-986` | The reason cites "(:945)". Point it at `doc:485` instead. |
| RFD 1024-1028 (no invented failure on resume) | citation-only | `doc:472`; RFD `:1063-1067` | Reason holds. |
| RFD 1168-1170 (no fabricated exclusive cost) | **removed** | none | Gone from both the RFD (now "Cost covers descendant sessions", `:1205-1228`) and the doc (`:492-500`). Delete the entry. The replacement is ledger entry E8 below. |
| `prompt-lifecycle.mdx:67`; RFD 439-441 (entity ID reuse) | unchanged (label only) | `prompt-lifecycle.mdx:70` (owner); RFD `:439-441` (Preview RFD) | `doc:196` (IDs scoped per session) is context only. |

No other existing ledger reason citing this doc rests on a TCK choice.

## New requirements (proposals)

Each item gives an id family (provisional), the rule, the tier and gate, the citation, how to test it, and what the harness needs.

- **N1 `ACP-SUBAGENT-2xx` close withdraws descendants' requests.** Rule: before the `session/close` response, the
  Agent sends a `$/cancel_request` for every pending child `session/request_permission` (and `elicitation/create`).
  MUST. Tier CAPABILITY, gate `capabilities.session.close` (a real gate). Citation `doc:427`; `session-setup.mdx:476`.
  - Test: hold a child's permission request unanswered in a driven turn, close the root, and require a
    `$/cancel_request` naming that id before the close result.
  - SKIP when no child request was pending at close, or the close failed.
  - Harness: this is the `ACP-CLOSE-205` machinery, extended to requests that carry an announced child's
    `sessionId`.
- **N2 `ACP-SUBAGENT-2xx` cancelled descendants' requests are withdrawn.** Rule: when a cancellation stops a
  session's work (a child cancelled directly, or a descendant stopped by the parent cascade), each of that
  session's pending permission requests gets a `$/cancel_request`. MUST. Tier CAPABILITY, gate
  `inferred:subagents` (or `inferred:subagentCancel` for the direct-child case). Citation `doc:417`;
  `prompt-lifecycle.mdx:1452`; `cancellation.mdx:42`.
  - Test: inside the `ACP-SUBAGENT-016`/`-202` driven turns, hold the child's permission requests. After the
    child reports `idle`/`cancelled`, require a `$/cancel_request` for each held request within `quiet_period`.
    The window matches `ACP-CANCEL-213`.
  - SKIP when no child request was held.
  - Harness: the child-cancel driver must hold child permission requests instead of answering them.
    `doc:419` only lets the Client answer `cancelled` after the child's cancelled idle (see the discrepancies).
  - Also check whether `ACP-CANCEL-213` (ADVISORY) should rise now that `prompt-lifecycle.mdx:1452` is a MUST.
    The prompt-lifecycle researcher owns that.
- **N3 `ACP-SUBAGENT-2xx` a child cannot be closed.** Two rules.
  - (a) `session/close` (or `session/delete`) naming a child does not report success. Stated without a keyword.
    Tier CAPABILITY, gate `capabilities.session.close` / `.delete`.
  - (b) The rejection is `-32602`. SHOULD, so ADVISORY.
  - Citation `doc:376,380`.
  - Test: after a child is announced, at the end of the run, send `session/close` with the child's ID. Expect an
    error, and expect `-32602` for (b).
  - SKIP when no child was announced.
  - The probe deliberately breaks the client MUST NOT at `doc:425`. See D3.
- **N4 `ACP-LIST-2xx` `session/list` does not return child sessions.** Stated without a keyword. Tier CAPABILITY,
  gate `capabilities.session.list`. Citation `doc:381`; `session-list.mdx:6`.
  - Test: after a turn that announced a child, call `session/list` filtered to the TCK's `cwd`. No announced
    child ID may appear.
  - SKIP when no child was announced.
  - Coordinate with the session-list researcher.
- **N5 `ACP-SUBAGENT-2xx` a stale mirror never overwrites newer state.** Rule: "The Agent sends both copies of a
  transition before a later transition on either path". Stated without a keyword. It binds only an Agent that
  mirrors. Tier CAPABILITY `inferred:subagents` or ADVISORY (D4). Citation `doc:351`; RFD `:799-800`.
  - Test: per child, keep the ordered distinct states of the child stream and of the mirror. FAIL when either
    path delivers state X after the other path has already reported a later, different transition that
    followed X.
  - SKIP when no child reports state on both paths.
  - Harness: none. Reuse `-201`'s per-child state tracking.
- **N6 `ACP-RESUME-2xx` (or widen `ACP-RESUME-209`) re-announcement after a resume without replay.** Rule: after
  `session/resume` with `replayFrom` omitted, every child update or request carries a child announced (with
  its ancestors, parent before child) since that resume request. MUST, from `doc:70` re-applied by `doc:469`.
  Tier CAPABILITY, with the same gate as `RESUME-209`. Citation `doc:462,469`.
  - Test: same as `RESUME-209`, without replay, over the resume exchange and a quiet period.
  - SKIP when no child traffic appears.
- **N7 `ACP-RESUME-2xx` replay keeps child identity and parent.** Rule: a child the TCK saw announced under
  parent P before the resume is not announced under a different parent in the replay. MUST. Tier CAPABILITY.
  Citation `doc:482`.
  - "their order within each session" is harder to judge. Leave it to D6.
  - Harness: the resume test must carry the live session tree across the reconnection. See D6.
- **N8 extend `ACP-SUBAGENT-004`.** Rule: a later `session/new` (or `session/fork`) result never returns an ID
  already announced as a child. MUST NOT. Citation `doc:82-83`.
  - Test: one `session/new` after the subagent turn.
  - SKIP when no child was announced.
- **N9 fold into `ACP-SUBAGENT-016`.** Rule: the Agent does not wait for the child's pending requests to resolve
  before it reports the child's cancelled state (`doc:421`, no keyword). Combined with N2's holding, a child
  that confirms only after the TCK answers at the deadline FAILs, as `ACP-CANCEL-209` does for the prompted
  session.
- **N10 fork remap.** Rules: copied child IDs are remapped consistently in `session_message` participants and in
  `session` content. Each copied child has its own `sessionId`. MUST. Tier CAPABILITY, gate
  `capabilities.session.fork`. Citation `doc:436-438`.
  - Observing it needs a fork of a parent with announced children, then a resume with replay of the fork.
    Recommend a Deferred ledger entry (blocker: no driver forks a parent that has children, then replays the
    fork) unless the user wants the row.
- **Cross-references, owned by the session-setup researcher:**
  - `session-setup.mdx:414`: exactly one `replay_complete` per announced child (MUST; also `doc:486`). There is
    no v2 row for `replay_complete` today.
  - `session-setup.mdx:431` and `doc:470`: after a replay, the current `subagent_update` for a listed background
    child follows the parent's `replay_complete`. `ACP-RESUME-213` checks only the no-replay case.
  - `doc:488`: a new child request during replay SHOULD wait for the child's `replay_complete`.

## New ledger entries (agent-side, not tested)

| # | citation | statement | reason |
|---|---|---|---|
| E1 | `doc:139` | The Agent does not use a child to get around a restriction the Client placed on the parent session (MUST NOT). | Unobservable: v2 Client restrictions such as permission policy are not on the wire. Client-capability rules apply to every session, and the existing rows already judge them whatever `sessionId` a request carries. |
| E2 | `doc:248,474` | Agents report a child's configuration with `config_option_update` when it is available, after the announcement, on change, and after a resume (SHOULD). | Unobservable: whether a child's configuration is available is internal. `-014` judges what is reported. |
| E3 | `doc:265`; `prompt-lifecycle.mdx:150-151` | With no evidence of the sender, the Agent omits `senderSessionId` and does not assume the parent (MUST NOT). | Unobservable: the true sender is known only to the Agent, so an assumed parent looks the same as a real one. |
| E4 | `doc:380` (first sentence) | The Agent ignores `session/cancel` for a child that does not advertise `cancel`. | Not observable as a violation: the Agent can cancel delegated work at any time (`doc:398`), so a child that stops after such a cancel looks the same as one the Agent stopped itself. |
| E5 | `doc:401,403` | The Agent reports `cancelled` only once it observes that the work stopped, and cancellation does not close the child. | Unobservable: when the provider work actually stopped is internal. A child need not get more work after a cancel (`doc:130`), so "not closed" has no wire signal. |
| E6 | `doc:418` | `session/cancel` on a parent does not resolve the requests of a child that keeps running. | Not observable as a violation: the Agent may stop other descendants (`doc:405`) and SHOULD withdraw requests it stops waiting on (`cancellation.mdx:33`), so a withdrawn request looks the same as abandoned work. |
| E7 | `doc:470,480,487` | The Agent reports each child's current state when it can determine it, replays the associations and child history it still has, and reports known gaps (SHOULD). | Unobservable: what the Agent can determine or still has is internal. |
| E8 | `doc:494-496` | A session's reported cost includes its descendants' costs (no keyword). | Not observable as a violation: a descendant's cost "can reach its ancestors later" with no bound, so an ancestor whose cost is below a descendant's may still be catching up. Cost is optional. See D5. |

## Discrepancies: doc vs RFD (target)

1. **Cancel withdrawal strength.** `doc:417` and `prompt-lifecycle.mdx:1452` say the Agent **MUST** cancel the
   pending permission requests of cancelled work, descendants included, with `$/cancel_request`. The RFD's v2
   section (`:1256-1262`) says this without a keyword. Its v1 section (`:1188-1191`) says `$/cancel_request` "remains
   optional". The doc governs v2, and the RFD defers to it (`:1232-1233`).
2. **When the Client may answer a child's request `cancelled`.** `doc:419` allows it only "once that child reports
   `idle` with `stopReason: "cancelled"`. Before that, it leaves the request open." RFD `:1260` and
   `prompt-lifecycle.mdx:1452` let the Client answer "a request it knows belongs to the cancelled work". This is a
   client-side rule, but it constrains the mock client in N2/N9: follow the doc.
3. **Close withdraws descendants' requests.** `doc:427` adds this MUST. The RFD has only the v1 client cleanup at
   `:1185-1186`.
4. **New child requests during replay.** `doc:488` adds that they SHOULD wait for the child's `replay_complete`.
   RFD `:1039-1040` says only that they "may proceed once their child and ancestors are announced".
5. **Cost model changed.** The base RFD's "no inferred aggregation / MUST NOT fabricate exclusive" rule is
   gone. The RFD at target and the doc agree on inclusive cost. This is why the ledger entry is removed.
6. **RFD links the stable tree.** The RFD links `/protocol/v2/subagents`, not the draft. The stable copy
   `docs/protocol/v2/subagents.mdx` differs from the draft only in link paths (checked with `diff`).

## Decisions for the user

- **D1. Keep the doc-stated MUST rows CAPABILITY behind `inferred:subagents` / `inferred:subagentCancel`.** These
  are `-001`, `-002`, `-004`, `-006`, and N1/N2/N6/N7/N8. Recommended. Exposing subagents is optional (`doc:8`).
  There is no `initialize` marker (`doc:10`), and the per-child `cancel` lives in `subagent_update`, which the
  capability plugin cannot read. A MANDATORY tier would misreport an optional feature.
- **D2. `ACP-SUBAGENT-016`: require the child's own `state_update`.** The row accepts either the child's
  `state_update` or the mirror. `doc:400` names the child's `state_update` as the confirmation, and the mirror
  is only a SHOULD (`doc:330`). Recommend: require the child's own `state_update` in v2, and let `-201` judge a
  missing mirror. Check against Rule B, since v1 shares the id and confirms through the parent snapshot.
- **D3. N3 needs a probe that breaks a client MUST NOT.** It sends `session/close` for a child, which `doc:425`
  forbids. Recommend adding N3 as the last action of a run, as with the existing `-32602` probes. If the user
  rejects probes, ledger it as Deferred with "needs a client-rule-violating probe".
- **D4. N5 tier.** The mirror is a SHOULD, but the ordering rule binds an Agent that does mirror. Recommend
  CAPABILITY `inferred:subagents`, consistent with the other no-keyword rules. The alternative is ADVISORY.
- **D5. Inclusive cost (E8).** Recommend the ledger entry. The other option is an INFORMATIONAL row that records
  parent vs child cost after both are idle.
- **D6. N7 and N10 need cross-connection or fork-then-replay drivers.** Recommend adding N7 only if the resume
  tests already reuse the live run's session tree, otherwise mark it Deferred. Mark N10 Deferred.
- **D7. Fix the stale ledger reason for RFD 1151-1153.** Its second sentence relies on a rule that is now v1-only.
  Recommended.
