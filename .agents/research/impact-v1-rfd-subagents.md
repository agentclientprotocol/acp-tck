# Impact on v1: Subagents RFD (`docs/rfds/subagents.mdx`), full audit, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (2026-11-17), read from
the `agent-client-protocol-2` checkout. Its HEAD is `6ace4f6a`, one v2-only commit ahead. `git diff 3ea94133 HEAD`
on `docs/rfds/subagents.mdx`, `docs/protocol/v1/draft/`, `docs/docs.json` and `schema/v1` is empty. Base file
from `git show 3961af94:docs/rfds/subagents.mdx`. Read in full: the RFD (1791 lines) and
`docs/protocol/v1/draft/subagents.mdx` (550 lines; read only to tell which rules the docs now state). Spot-read:
`prompt-turn.mdx:42-118,736`, `tool-calls.mdx:337-365`, `error.mdx:57`, and the `schema/v1/schema.unstable.json`
descriptions of `SessionMessage`, `SubagentUpdate`, `SessionReference` and `UnknownStateUpdate`. TCK side:
`src/tck/v1/requirements.py` (17 rows cite the RFD), `spec-tracker/maps/v1.toml:319-397` (16 ledger entries), and
`src/tck/v1/conformance/test_subagents.py` / `test_subagent_controls.py`. I did not consult the SDKs. No rule
classified here depends on runtime behaviour the spec leaves implicit.
**Stage:** Preview at the target (`docs/docs.json:242-243`, group "Preview"). It was Active at the base.
**Confidence:** high for the line remaps and the doc-stated/RFD-only split (every range was re-located by text).
Medium for the ACP-SUBAGENT-012 decision (D2).

## Summary

- Every existing row and ledger entry needs its label changed from `(Active RFD)` to `(Preview RFD)`.
- No RFD rule that a row tests changed meaning. The changes are line remaps, plus row text that says "stated only by
  the Subagents RFD" for rules that the new draft doc `docs/protocol/v1/draft/subagents.mdx` now states.
- One ledger entry is **removed**: the cost-fabrication rule at base `:1168-1170`, whose text was deleted.
- One ledger entry **changes its statement**: `unknown` now also covers an agent that stops tracking a child.
- Nearly every new rule in the range is doc-stated (`unknown` state, restricted methods `-32602`, link evidence,
  sender not assumed, cost includes descendants). Those belong to the doc report.
- Three RFD-only agent SHOULD / SHOULD NOT rules have no row and no ledger entry. All three are unobservable, so I
  propose them as new ledger entries. No new rows.

Abbreviations used in the tables:

- "RFD" means `docs/rfds/subagents.mdx`.
- "doc" means `docs/protocol/v1/draft/subagents.mdx`.
- All lines are at 3ea94133.

## Registry rows (`src/tck/v1/requirements.py`)

| id | classification | RFD citation at target | note |
|---|---|---|---|
| ACP-CLIENTCAP-007 | citation-only | `76-78,663-664` (was `76-78,644-645`) | Doc-stated (doc:61), see doc report. |
| ACP-SUBAGENT-001 | citation-only | `95-99,189-193,970-972,979-985,1018-1024` (was `…,933-935,942-948,981-987`) | Doc-stated (doc:90-97, 517, 531, 534), see doc report. Its three "(Active RFD)" asides about replay (announcements precede replayed traffic; replayed participant IDs are historical addresses) are now doc-stated at doc:531 and doc:534. |
| ACP-SUBAGENT-002 | citation-only | `647-650` (was `636-639`) | The rule is doc-stated (doc:94; `tool-calls.mdx:350-351`). The carve-out "a replayed reference to an unavailable session follows the historical replay rules" is still RFD-only (RFD:649-650), so keep that aside with a `(Preview RFD)` label. New RFD:655-661 (references are re-sent on content replacement and only for handles the agent can resolve) do not affect the check. They are doc-stated at `tool-calls.mdx:362-365`. |
| ACP-SUBAGENT-003 | changed text | `165-169` (unchanged) | Text says "Stated only by the Subagents RFD … capped at CAPABILITY". That is now false: doc:144 says a `subagent_update` cannot "name its own outer session as the child". The tier stays `CAPABILITY` / `inferred:subagents`, because only an agent that emits `subagent_update` is bound (same as -005). Doc citation, see doc report. |
| ACP-SUBAGENT-004 | changed text | `122-124,165-169` (unchanged) | Text says "Stated only by the Subagents RFD". The rule is now doc-stated at doc:99-103 (unique, MUST NOT reuse) and doc:144 (no cycle). Tier unchanged. |
| ACP-SUBAGENT-005 | changed text (minor) | `165-169` (unchanged) | Text says "the RFD states the one-parent, no-cycle rule". doc:88 and doc:144 now state it. Tier unchanged. |
| ACP-SUBAGENT-006 | citation-only (label) | `298-308` (unchanged) | Doc-stated (doc:232). |
| ACP-SUBAGENT-007 | citation-only | `485-488` (was `477-480`) | Still RFD-only: no draft doc or schema text says the participants "identify different sessions". Keep the cap note. |
| ACP-SUBAGENT-008 | citation-only | `485-489` (was `477-481`) | Still RFD-only ("the outer `params.sessionId` matches one of them"). |
| ACP-SUBAGENT-009 | citation-only (label) | `466-475` (unchanged) | The MUST "they name each other" (RFD:472) is still RFD-only. New RFD:477-483 (link two views only on evidence, else leave them unlinked) agrees with the row's "not judged" carve-outs. It is doc-stated at `prompt-turn.mdx:116-118`. |
| ACP-SUBAGENT-011 | citation-only | `667-690` (was `648-664`) | The new paragraph RFD:678-683 now sits inside the range (no sender evidence, so the agent MUST NOT assume the parent). Doc-stated (doc:286), see doc report. |
| ACP-SUBAGENT-012 | citation-only, plus decision D2 | `667-676` (was `648-657`) | New rule RFD:680-682 (doc:287, `prompt-turn.mdx:115-116`): an agent with no evidence of the sender omits `senderSessionId` and MUST NOT assume the parent. Today the test flags such a child as "unreported". See D2. |
| ACP-SUBAGENT-013 | citation-only (label) | `461-464` (unchanged) | Doc-stated (`prompt-turn.mdx:49-51`). |
| ACP-SUBAGENT-014 | changed text | `392-419` (unchanged; line 400 was only a link retarget) | Text says "Stated only by the Subagents RFD (Active RFD), so the row is ADVISORY". The rule is now doc-stated at doc:273, still a SHOULD, so the tier stays `ADVISORY`. Only the reason in the text changes. |
| ACP-SUBAGENT-015 | citation-only | `841-855` (was `815-829`) | Same payload list (`unknown` included). The schema change to `UnknownStateUpdate` belongs to the schema/doc report. |
| ACP-SUBAGENT-016 | changed text | `1113-1117,1133-1139` (was `1069-1073,1089-1095`) | Text says "the confirmation is stated only by the Subagents RFD". doc:449 now states it, also without an RFC keyword. The tier stays `CAPABILITY` / `inferred:subagentCancel`. New RFD:1093 ("An Agent ignores a `session/cancel` for a child that does not advertise `cancel`") is doc-stated at doc:428. It is consistent with the test, which never cancels such a child. |
| ACP-SUBAGENT-017 | changed text | `1113-1117` (was `1069-1073`) | Text says "Stated only by the Subagents RFD (… `not its parent or siblings`)". doc:447 now states it ("not the work of its parent or siblings … The Agent can cancel work it delegated at any time"). Tier unchanged. The sibling carve-out still holds. |

Counts (17 rows): 0 unchanged; 11 citation-only (CLIENTCAP-007, -001, -002, -006, -007, -008, -009, -011, -012,
-013, -015; -006, -009 and -013 need only the label); 6 changed text, none changed in tier or gate (-003, -004,
-005, -014, -016, -017); 0 removed; -012 also carries decision D2.

## Ledger entries (`spec-tracker/maps/v1.toml`)

Every entry needs `(Active RFD)` changed to `(Preview RFD)`, including the section comment at `:319`. Where the
doc now states the rule, docs precedence makes the doc citation primary. That move is the doc report's job. The
RFD part becomes secondary context with the line numbers below.

| base citation | classification | RFD citation at target | note |
|---|---|---|---|
| `322-326` directories reported before dependent traffic | citation-only (label) | `322-326` | Doc-stated (doc:253-254). |
| `381-382,387-390` narrowest dirs; directories on reconnect | citation-only (label) | `381-382,387-390` | Doc-stated (doc:255, 521). |
| `198-199,939-940` parentage not guessed | citation-only | `198-199,976-977` | Doc-stated (doc:152, 533). |
| `203-206` interaction not moved; child ID used once exposed | citation-only (label) | `203-206` | Doc-stated (doc:153-154). The new RFD:1196 / doc:462 ("requests … MUST NOT move to the parent or a later operation") restates this. See the doc report. |
| `223-226` automatic delivery | citation-only (label) | `223-226` | Doc-stated (doc:161). |
| `576-577` each side reported only when observed | citation-only | `584-585` | Doc-stated (`prompt-turn.mdx:102-103`). The adjacent new SHOULD NOT (RFD:586-588) is RFD-only. See new ledger L1. |
| `831-841` running/idle MUST, requires_action/stopReason SHOULD | citation-only | `857-867` | Doc-stated (doc:374-375). |
| `UnknownStateUpdate; 855-860` `unknown` when observability is lost | **changed text** + citation | `881-889` | Proposed statement: "When observability of a child's foreground work is actually lost, including when the Agent itself stops tracking a child that may still be working, the Agent reports the `unknown` state on the parent's `subagent_update.state` (MUST), and not merely because the child has been quiet." The reason still holds; stopping tracking is just as internal. Doc-stated (doc:410). The new related MUST NOT, "invent a final status for unfinished tool calls/terminals" (RFD:898-900, doc:415), is doc-stated. See the doc report. |
| `1117-1121` closing the parent cancels descendants | citation-only | `1161-1165` | Doc-stated (doc:475). |
| `1151-1153` late response not used | citation-only, **reason text** | `1198-1200` | The reason cites the client rule at `:1126-1128`. That rule is now `:1173-1175` (also doc:466). Fix the reason. Doc-stated (doc:470). |
| `999-1001` replay does not reissue requests | citation-only | `1038-1040` | Doc-stated (doc:537). |
| `942-949` replayed directed messages: no invented IDs | citation-only, **reason text** | `979-986` | The reason cites `(:945)` ("a historical address is not an announcement"). That sentence is now `:982`, and no doc line states it, so keep the RFD reference. Fix the reason. Rule doc-stated (doc:534). |
| `1024-1028` no manufactured failure | citation-only | `1063-1067` | Doc-stated (doc:520). |
| `1168-1170` no fabricated exclusive cost | **removed** | (none: the text is deleted) | The section "Cost reporting without inferred aggregation" (base `:1158-1188`) was replaced by "Cost covers descendant sessions" (RFD:1205-1228). The MUST NOT is gone, so delete the entry. The replacement rule, that a parent's `usage_update.cost` includes its descendants (RFD:1207-1213), is doc-stated (doc:544, `prompt-turn.mdx:736`), so any row or ledger entry for it belongs to the doc report. Input for that report: the rule looks unobservable as a violation. "A descendant's cost can reach its ancestors later" (doc:544) sets no deadline, currencies may differ, and true provider cost is unknown. So even a parent cost below a child's cost proves nothing. |
| `439-441` `messageId` unique, identifies the entry | citation-only (label) | `439-441` | Only partly doc-stated: transcript scope at `prompt-turn.mdx:47-48` and doc:210. "Unique" appears only in the RFD, so keep the RFD citation. |
| `361-363` explicit `cwd` on a child's `terminal/create` (Deferred) | citation-only (label) | `361-363` | Doc-stated (doc:265). The "Deferred" reason names a real blocker (the mock client has no `terminal`), so it complies with the TCK-choice rule. |

TCK-choice check on existing reasons: none rests on a TCK choice. `361-363` is correctly marked Deferred. The
reason for `1151-1153` rests on a client MUST (`:1173-1175`), not on a TCK choice.

## RFD rules applying to v1, outside the rows and entries above

Every agent-binding statement of the RFD was checked. Each one is covered above, doc-stated, client-side, a MAY,
or v2-only. A rule marked doc-stated goes to the doc report (see the doc report).

- **Doc-stated, new or changed in the range** (see doc report):
  - restricted methods: ignore `session/cancel` for a child without `cancel`, SHOULD reject other requests with
    `-32602` (RFD:1093-1096; doc:428; `error.mdx:57`);
  - `unknown` covers losing track of a child (RFD:885-888; doc:410);
  - no invented final status while `unknown` (RFD:898-900; doc:415);
  - sender not assumed (RFD:680-682; doc:287);
  - link needs evidence (RFD:477-483; `prompt-turn.mdx:116-118`);
  - reference only for resolvable handles, MUST NOT guess (RFD:659-661; `tool-calls.mdx:363-365`);
  - cost includes descendants (RFD:1207-1213; doc:544).
- **Doc-stated, unchanged, with no row or entry today** (see doc report):
  - a child is not used to circumvent the parent's restrictions (RFD:216-217; doc:157);
  - SHOULD report child config, refreshed after load (RFD:394-401, 421-426; doc:269, 522);
  - SHOULD report the outgoing view and link it (RFD:674-675; doc:285);
  - SHOULD replay child history (RFD:962-964; doc:528);
  - SHOULD make gaps apparent (RFD:987-989; doc:536);
  - all selected history before the response, and no historical state after it (RFD:990-993; doc:535);
  - current snapshots after the `session/load` response (RFD:1033-1036; doc:513);
  - no child updates on replay to a client without `subagents` (RFD:1002-1005; doc:530);
  - live traffic during replay (RFD:1042-1045; doc:538);
  - SHOULD report current state after reconnect (RFD:1062; doc:518);
  - cancellation reported from evidence (RFD:1141-1145; doc:450);
  - cascade to waited-on descendants (RFD:1119-1125; doc:454);
  - fork remapping (RFD:1102-1104; doc:486).
- **RFD-only, no keyword:** "Advertise individual cancellation only when the adapter can target the child's
  current work correctly" (RFD:1129-1131). This is guidance, not a stated MUST or SHOULD. In practice
  ACP-SUBAGENT-016 enforces it: a child that advertises `cancel` but does not confirm FAILs. No entry proposed.
- **RFD-only, keyword, unobservable:** three rules, listed below as new ledger entries L1-L3.

## New requirements

None. Every RFD-only rule that applies to v1 and is not yet covered is a SHOULD or SHOULD NOT whose condition is
internal to the agent (see below). Rules that are new and observable, such as `-32602` for restricted child
methods, are doc-stated and go to the doc report.

## New ledger entries (section `subagents (docs/rfds/subagents.mdx, Preview RFD)`)

- **L1** (new in range)
  - citation: `docs/rfds/subagents.mdx:586-588 (Preview RFD)`
  - statement: "An Agent SHOULD NOT report an outgoing view of a session-directed message for a send it knows
    failed before the message left the sender."
  - reason: "Unobservable: whether a send failed, and whether the agent knew it had, is internal to the agent. An
    outgoing view looks the same whether or not its delivery failed."
- **L2** (present at base, missed because no full audit had run)
  - citation: `docs/rfds/subagents.mdx:471-472 (Preview RFD)`
  - statement: "Agents SHOULD supply each `senderMessageId` / `recipientMessageId` reference once they know it."
  - reason: "Unobservable: when, or whether, the agent learns the other view's `messageId` is internal. The agent
    leaves views unlinked when it cannot establish that they are the same message (:477-483). So two unlinked
    views cannot be told from views the agent could have linked. Conflicting references are judged by
    ACP-SUBAGENT-009."
- **L3** (present at base, missed)
  - citation: `docs/rfds/subagents.mdx:995-996 (Preview RFD)`
  - statement: "Agents SHOULD retain or reconstruct child identity, associations and ACP-visible conversation data
    where practical."
  - reason: "Unobservable: what the agent retained, and what was practical, is internal to the agent. Child
    replay is best-effort (:962-966), so missing child history after `session/load` is not a violation a client
    can prove."

## Decisions for the user

- **D1. Rows that are now doc-stated keep their tier.** ACP-SUBAGENT-003, -004, -005, -016 and -017 were
  `CAPABILITY` under the RFD-only cap. The doc now states their rules. They stay `CAPABILITY` behind
  `inferred:subagents` / `inferred:subagentCancel`, because only an agent that opts in by behaviour is bound. This
  is the same reasoning as -005 and -006 today. ACP-SUBAGENT-014 stays `ADVISORY` (a SHOULD).
  **Recommendation:** keep the tiers. Rewrite the "stated only by the Subagents RFD" phrases. Move the doc
  citation first, as the doc report proposes.
- **D2. ACP-SUBAGENT-012 against the new "MUST NOT assume the parent" rule** (RFD:680-682, doc:287,
  `prompt-turn.mdx:115-116`). An agent with no evidence of the sender correctly omits `senderSessionId` from the
  child's incoming `session_message`. Today -012 marks that child as "unreported", an ADVISORY FAIL.
  **Recommendation:** count an incoming `session_message` in the child's transcript before its first output as
  meeting -012 when its stored `senderSessionId` is absent. Keep flagging a child with no incoming
  `session_message` at all. Possibly also flag one whose stored sender is a known session other than the parent;
  the user decides, since a sibling may legitimately message the child first (RFD:678-679). The doc report owns
  the doc citation (doc:284, 287) and may weigh in. This is the only test-logic change this report suggests.
- **D3. Delete the cost ledger entry** (base `:1168-1170`). Leave any coverage of the new inclusive-cost rule to
  the doc report. My view: ledger it as unobservable (see the table note).
- **D4. Add L1-L3.** L2 and L3 fill gaps from before this range, found because this is the first full audit.

## Harness or mock-client needs

None from this report.
