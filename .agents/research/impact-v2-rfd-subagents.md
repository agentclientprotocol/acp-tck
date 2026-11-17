# Impact: `docs/rfds/subagents.mdx` on v2 (spec update 3961af94 -> 3ea94133, full RFD audit)

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read via `git show`; the
checkout's HEAD is `6ace4f6a`, not the target): `docs/rfds/subagents.mdx` (whole, 1791 lines) and its diff from
`3961af94`; `docs/docs.json` (stage); `docs/protocol/v2/draft/subagents.mdx` (whole, to tell doc-stated rules
from RFD-only ones); `docs/protocol/v2/draft/prompt-lifecycle.mdx:53-153,1030-1056,1432-1464`;
`docs/protocol/v2/draft/tool-calls.mdx:728-756`; `schema/v2/schema.unstable.json` (`$defs` named below).
acp-tck: `src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`, `src/tck/v2/conformance/_helpers.py`,
`src/tck/v2/conformance/test_session_capabilities.py`, `tests/v2/test_run_prompt.py`. I did not consult the SDKs:
nothing in scope needed runtime behaviour that the spec leaves open.
**Confidence:** high for line maps and classifications (diff-mapped, then checked by reading the text). Medium on
the scope of the RFD's "v1 only" pending-requests section (the RFD contradicts itself there, see D2).

**Stage:** `rfds/subagents` sits in `RFDs > Preview` at the target (`docs/docs.json`). Every `(Active RFD)` /
`Active Subagents RFD` label becomes `(Preview RFD)` / `Preview Subagents RFD`. The RFD now defers to the docs for v2
on its own terms: "The v2 rules are specified on the v2 Subagents page. Where this RFD and that page differ for v2,
the page applies" (`docs/rfds/subagents.mdx:1232-1233`). That page is `/protocol/v2/subagents` (stable). The draft
page the TCK cites is the same text plus a "Forking the parent (unstable)" section (`draft/subagents.mdx:432-440`).

**Doc-stated** below means that `docs/protocol/v2/draft/subagents.mdx` (written `doc:` here) or another v2 draft doc
states the rule. Under docs precedence those rules belong to the doc report (`impact-v2-subagents-doc.md`) or the
named doc's report, and the RFD becomes secondary context. This report gives only the RFD citation part of each row
or entry.

## Rows (`src/tck/v2/requirements.py`)

All RFD line maps are `docs/rfds/subagents.mdx @ 3ea94133`. "Label" means `(Active RFD)` -> `(Preview RFD)`.

| id | classification | RFD citation at target | note |
|---|---|---|---|
| ACP-SUBAGENT-001 | citation-only (label; lines unchanged) | `95-99,189-193` | Doc-stated (`doc:70-78`, MUST). The doc widens the covered traffic to a `background` list that names the child (`doc:75`). See doc report. |
| ACP-SUBAGENT-002 | citation-only | `636-638` -> `647-649` | Doc-stated (`doc:74`; `tool-calls.mdx:740-742`). |
| ACP-SUBAGENT-003 | citation-only (label); text stale | `165-169` | Text says "Stated only by the Subagents RFD", but `doc:126` now states it ("cannot ... name its own outer session as the child"). Rewrite per doc report. Tier stays CAPABILITY `inferred:subagents`. |
| ACP-SUBAGENT-004 | citation-only (label); text stale | `122-124,165-169` | "Stated only by the RFD" is stale: `doc:80-83` (MUST NOT reuse). See doc report. |
| ACP-SUBAGENT-005 | citation-only (label) | `165-169` | Doc-stated (`doc:68,126`). |
| ACP-SUBAGENT-006 | citation-only (label) | `298-308` | Doc-stated (`doc:218`). |
| ACP-SUBAGENT-007 | citation-only | `477-480` -> `485-488` | Still RFD-only. Neither `doc:` nor `prompt-lifecycle.mdx:76-152` says the participants differ. CAPABILITY cap stands. |
| ACP-SUBAGENT-008 | citation-only | `477-481` -> `485-489` | Still RFD-only (outer `sessionId` matches one participant). Cap stands. |
| ACP-SUBAGENT-009 | citation-only (label) | `466-475` | Still RFD-only for the MUST that the references "name each other" (`:472`). New context at `477-483`: link only an established match, and unlinked views are valid. The docs state the same in `prompt-lifecycle.mdx:150-152`, which supports the row's "not judged" cases. No change in what the test checks. |
| ACP-SUBAGENT-011 | citation-only | `648-664` -> `667-676,685-690` | The new block `678-684` (MUST NOT assume the parent) sits between the two old parts, so cite them separately. Doc-stated (`doc:264`; `prompt-lifecycle.mdx:142-147`). |
| ACP-SUBAGENT-012 | citation-only; flagged | `648-657` -> `667-676` | Doc-stated (`doc:262`). Interacts with the new MUST NOT at `678-683` / `doc:265` / `prompt-lifecycle.mdx:149-151`. See D4. |
| ACP-SUBAGENT-013 | citation-only (label) | `461-464` | Text "the Active RFD as a SHOULD" -> "Preview RFD". Doc wording: `prompt-lifecycle.mdx:84-86` (prompt-lifecycle report). |
| ACP-SUBAGENT-014 | citation-only (label); text stale | `392-419` (only `:400`, a link, changed) | "Stated only by the Subagents RFD ... so the row is ADVISORY" is stale: `doc:252` states it (SHOULD). Tier stays ADVISORY. |
| ACP-SUBAGENT-201 | citation-only | `765-774` -> `791-800` | Doc-stated (`doc:330,350-351`). |
| ACP-SUBAGENT-016 | citation-only; text stale | `1069-1073,1089-1095` -> `1113-1117,1133-1139` | "Confirmation is stated only by the RFD" is stale: `doc:400` states it. Gate unchanged. |
| ACP-SUBAGENT-017 | citation-only; text stale | `1069-1073` -> `1113-1117` | "Stated only by the RFD" is stale: `doc:398`. The sibling carve-out now rests on `doc:398` ("The Agent can cancel work it delegated at any time"). |
| ACP-SUBAGENT-202 | citation-only; text stale | `1075-1087,1413-1425` -> `1119-1131,1482-1494` | The cascade "stated by the RFD" is now `doc:405`. Gate unchanged. |
| ACP-RESUME-002 | citation-only | `1008-1013` -> `1047-1052` | Text "(Active Subagents RFD)" -> "(Preview ...)". Also doc-stated: `doc:462`. |
| ACP-RESUME-205 | citation-only | `999-1006` -> `1038-1045` | Label in text. |
| ACP-RESUME-209 | citation-only, re-scope recommended | `925-935` -> `962-972`; `995-1003` -> `1034-1042` | `1034-1036` now sits under "In v1:" (`1026-1029`). Recommend `962-972,1018-1024,1038-1042`: announcements precede traffic, ancestors announced "during this load/resume", new requests follow announcement. Doc-stated: `doc:469,482`. The new per-child `replay_complete` (`1249-1254`; `doc:486`) may change this row: session-setup / doc report. |
| ACP-TOOLCANCEL-203 | citation-only | `1042-1045` -> `1081-1084` | Doc-stated (`doc:374,378`). |
| ACP-TERMCANCEL-203 | citation-only | `1042-1045` -> `1081-1084` | Same. |

No row is removed. No row's rule changed in the RFD text itself.

## Ledger (`spec-tracker/maps/v2.toml`)

| ledger citation (base) | classification | RFD citation at target | note |
|---|---|---|---|
| `prompt-lifecycle.mdx:67; rfds/subagents.mdx:439-441` | citation-only (label) | `439-441` | The prompt-lifecycle part moved (the MUST NOT is now `prompt-lifecycle.mdx:70`); that belongs to the prompt-lifecycle report. |
| `322-326` | citation-only (label) | `322-326` | Doc-stated `doc:239-240`; re-cite per doc report. The reason holds. |
| `381-382,387-390` | citation-only (label) | `381-382,387-390` | Doc-stated `doc:241,473`. The reason holds. |
| `198-199,939-940` | citation-only | `198-199,976-977` | Doc-stated `doc:134,484`. |
| `203-206` | citation-only (label) | `203-206` | Doc-stated `doc:135-136`. |
| `223-226` | citation-only (label) | `223-226` | Doc-stated `doc:143`. |
| `576-577` | citation-only | `584-585` | Base `:577` was edited only after the cited sentence. Doc-stated `prompt-lifecycle.mdx:137-138` ("The Agent reports each side only when observed"). |
| `schema...#/$defs/UnknownStateUpdate; 855-860` | **changed text** | `881-889` | New case at `885-888`: observability is also lost when the Agent itself stops tracking a child that may still be working. Statement should read "...when observability is actually lost, including when the Agent stops tracking a child that may still be working...". The reason still holds (internal). Doc-stated `doc:360`. The pointer still resolves. |
| `1117-1121` | citation-only; reason partly stale | `1161-1165` | The RFD text is unchanged. But `doc:427` now adds a wire signal: before the close response the Agent MUST cancel descendants' pending permission requests and elicitations with `$/cancel_request`. So the reason's "the rule requires no wire signal" no longer holds for v2. Doc report: propose a row for `doc:427` and narrow this entry. |
| `1151-1153` | **changed** (source scope, reason) | `1198-1200` | The section is now marked "This section describes v1" (`1169-1170`), while `1270-1272` says only its Client MUST is v1-only (D2). `doc:420` states the rule for v2, so it should be the primary citation (doc report). The reason's second sentence relies on the v1 Client MUST ("the client rule at :1126-1128"). In v2 the Client only **SHOULD** answer `cancelled` after `$/cancel_request` and **MAY** answer early (`prompt-lifecycle.mdx:1452`). Drop that sentence or re-derive it. The first sentence (a late answer's use cannot be observed) still justifies the entry. |
| `999-1001` | citation-only | `1038-1040` | Doc-stated `doc:488`. The reason holds: a request before the child's `replay_complete` is either a re-issued recorded one (MUST NOT) or a live one sent early (`doc:488` SHOULD wait), and the client cannot tell them apart. |
| `942-949` | citation-only | `979-986` | Doc-stated `doc:485`. |
| `1024-1028` | citation-only | `1063-1067` | Doc-stated `doc:472`. |
| `1168-1170` ("do not fabricate an exclusive parent or child cost") | **removed** | (deleted) | The whole "Cost reporting without inferred aggregation" section was replaced by "Cost covers descendant sessions" (`1205-1228`). Delete the entry. The replacement rule (a session's `usage_update.cost` includes its descendants') is doc-stated (`doc:494`; `prompt-lifecycle.mdx:1055`): doc report. |

No existing reason citing this RFD rests on a TCK choice. The `1151-1153` reason relied on a v1 client rule (above).

## Full audit: RFD rules that apply to v2 and have no row or ledger entry

All of these are doc-stated, so the doc report (or the named doc's report) owns them and I propose no RFD-sourced
row: `216-217` / `doc:139` (no circumventing parent restrictions through a child); `252-254` / `doc:198`;
`353-356` / `doc:242`; `394-401` / `doc:248` (SHOULD report child config); `421-423` / `doc:474`; `674-675` /
`doc:263` (SHOULD report and link the outgoing view); `678-683` / `doc:265` (new MUST NOT assume the parent);
`797-800` / `doc:351`; `898-905` / `doc:365` (new: `unknown` MUST NOT invent final statuses);
`962-966` / `doc:480`; `970-972` / `doc:482`; `987-989` / `doc:487`; `990-993` / `doc:486`;
`1018-1024` / `doc:469`; `1062` / `doc:470`; `1093-1096` / `doc:380` (new; the `-32602` row is already proposed in
`impact-v2-overview-error.md`); `1098-1100` / `doc:381`; `1102-1109` / `doc:436-440` (unstable fork);
`1141-1145` / `doc:401`; `1205-1216` / `doc:494`; `1249-1254` / `doc:486` (new per-child `replay_complete`);
`1255-1263` / `doc:463-465,470` (new freshness boundary; the doc makes it a MUST); `1264-1269` / `doc:417`;
`655-661` / `tool-calls.mdx:753-756` (new; tool-calls report, see Discrepancies).
These bind only the Client and are out of the ledger's scope: `226-227, 291-292, 403-405, 411-413, 589-593, 889-894,
901-903, 932-936, 1008-1016, 1073-1075, 1088-1091, 1147-1155, 1218-1221, 1238-1244`. These are v1-only: `62-78,
285-287, 361-369, 857-867, 1026-1036, 1167-1203` (D2).

## New requirements

None from RFD-only text. Every new RFD rule that a client could observe is doc-stated (see above).

## New ledger entries

All are RFD-only and capped below MANDATORY, and none is observable. Label `(Preview RFD)`.

1. `docs/rfds/subagents.mdx:586-588 (Preview RFD)`. New at the target.
   Statement: "The Agent SHOULD NOT report an outgoing view of a session-directed message for a send it knows
   failed before the message left the sender."
   Reason: "Unobservable: whether a send failed, and whether the agent knew it, is internal. An outgoing view with no
   incoming view looks the same as a delivered message whose receipt the agent did not observe, which `:584-585`
   allows."
2. `docs/rfds/subagents.mdx:471-472 (Preview RFD)`. Present at the base too; missed by the earlier audit.
   Statement: "Agents SHOULD supply each message reference (`senderMessageId`, `recipientMessageId`) once they know
   it."
   Reason: "Unobservable: when the agent learns the other view's ID is internal, and unlinked views are valid
   (`:482-483`). Conflicting references are judged by ACP-SUBAGENT-009."
3. `docs/rfds/subagents.mdx:995-1000 (Preview RFD)`. Present at the base too; missed.
   Statement: "Adapters SHOULD retain or reconstruct child identity, associations and ACP-visible conversation data
   where practical."
   Reason: "Unobservable: what the agent retained, and what was practical, is internal. Replay is best-effort
   (`:962-966`), so a missing child history cannot be told from one that was never retainable."

## Decisions for the user

- **D1. Remove the cost ledger entry** (`1168-1170`). The rule it recorded was deleted and reversed at the target.
  Recommend deleting it in the same change that handles the doc-stated replacement (`doc:494`), which belongs to the
  doc report.
- **D2. The pending-requests section's v2 scope.** `1169-1170` says the whole section describes v1. `1270-1272` says
  only its Client MUST is v1-only, and `1280` says the rest of the cancellation flow applies to v2. Recommend
  following the doc: cite `doc:420` (late response, single response) and `doc:413` (requests stay attributed) as
  primary for v2, keep the RFD at `1195-1200` only as secondary context, and rewrite the `1151-1153` ledger reason as
  described above.
- **D3. Rows whose text says "stated only by the Subagents RFD"** but the doc now states the rule: 003, 004, 014,
  016 (confirmation), 017 and 202 (cascade). Recommend that the doc report rewrite the text and primary citations
  and keep the RFD lines from the table above as secondary. Tiers do not change: the doc MUSTs bind only Agents that
  expose subagents (`doc:8`), and nothing in `initialize` announces that, so the rows stay CAPABILITY
  `inferred:subagents` / `inferred:subagentCancel`. 014 stays ADVISORY. 007, 008 and 009 stay RFD-only.
- **D4. ACP-SUBAGENT-012 against the new "MUST NOT assume the parent"** (`678-683`; `doc:265`;
  `prompt-lifecycle.mdx:149-151`). The doc now explicitly allows an incoming view with no `senderSessionId` when the
  agent has no evidence of the sender. Row 012 (ADVISORY) flags a child whose first output is not preceded by an
  incoming message from the parent, and a client cannot tell "no evidence" from a plain omission. Recommend: count an
  incoming `session_message` with no stored sender as reporting the task, record it instead of flagging it, and flag
  only when no incoming `session_message` precedes the output. The doc report decides, because the row's primary
  source is doc-stated.
- **D5. Harness comments cite a v1-only section.** `_helpers.py:1972-1974` and `tests/v2/test_run_prompt.py:847`
  justify answering a cancelled session's permission requests `cancelled` with the RFD's "Pending permission and
  elicitation requests" section, which is now v1-only. The behaviour is still allowed in v2: the client answers only
  for a session the TCK itself cancelled, which the Client **MAY** do (`prompt-lifecycle.mdx:1452`; RFD `1268`).
  Re-cite to those and relabel. No behaviour change. Other `Active Subagents RFD` / `(Active RFD)` strings to relabel:
  `_helpers.py:645,674,722,796,821,826,839,889,935,942,964,1051,1164,1181,1216,1986` and
  `test_session_capabilities.py:197,287,434,468`. Failure messages for rules that are now doc-stated (821, 826, 839,
  1216) should probably cite the doc instead of the RFD (doc report).

## Discrepancies (RFD vs v2 docs; the docs govern)

- New child requests during replay: the RFD says live requests "follow" the child's `replay_complete` (`1253`) and
  "may proceed once their child and ancestors are announced" (`1039-1040`). `doc:488` makes waiting for the child's
  `replay_complete` a SHOULD.
- Current `subagent_update` for each background child before the state snapshot: declarative in the RFD
  (`1259-1261`), **MUST** in `doc:470`.
- Session reference by handle: the RFD has **MUST NOT** guess the session (`661`). `tool-calls.mdx:754-756` states
  the same rule with no keyword (tool-calls report).
- Closing a parent: the RFD requires no new notification (`1163-1164`). `doc:427` adds a **MUST** to cancel
  descendants' pending requests with `$/cancel_request` before the close response.
- Config after a resume with replay: the RFD says current config snapshots follow the load/resume *response*
  (`424-426`), but v2's freshness boundary is the parent's `replay_complete` (`1255-1258`, which covers state and
  capabilities only). `doc:474` gives no timing. No row depends on this.
- `$/cancel_request` is optional in the v1 section (`1187-1190`) and a MUST for v2 (`1267-1268`; `doc:417`).
  Consistent across versions, but worth knowing when reading the RFD.

## Open questions

- Not this doc: `src/tck/v2/conformance/test_jsonrpc.py:141` calls the MCP-over-ACP RFD "(Active)". It is Draft at
  the target, so the extensibility or transports researcher should relabel it.
