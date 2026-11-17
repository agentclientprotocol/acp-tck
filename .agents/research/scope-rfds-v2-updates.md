# Scope: testing the five never-backfilled v2 RFDs (message-updates, tool-call-updates, meta-patches, permission-requests, enum-variant-extension) in v2

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (target, checkout
`../agent-client-protocol-2`), diffed against base `3961af94`: the five RFDs, `docs/docs.json`,
`docs/protocol/v2/draft/{extensibility,tool-calls,prompt-lifecycle,session-setup,elicitation}.mdx`,
`schema/v2/schema.unstable.json`. acp-tck @ `ceef9a8`: `src/tck/v2/requirements.py`,
`spec-tracker/maps/v2.toml`, `src/tck/v2/open_enums.py`, `docs/requirements.md`, `docs/spec-updates.md`.
Reference SDKs not consulted: none of the rules depends on runtime behaviour the docs leave open.
**Confidence:** high. Every agent-side rule maps onto explicit draft-doc or schema text. The only judgement calls
are what counts as an "agent-side normative rule" (client-side application semantics left out) and the two
borderline items under Decisions.

## Answer

None of the five RFDs adds a testable agent-side rule that the v2 draft docs or schema don't already state. Nearly
all of them are already covered by existing v2 rows or ledger entries. The RFDs were written as specs for docs that
now exist: the docs absorbed them, sometimes with stronger keywords (e.g. enum `-32602` is a MUST in the docs, a
plain "rejects" in the RFD). Under the docs-precedence rule, and the Draft-RFD rule ("cite only where nothing else
states the rule"), none of them justifies a new row or citation. What's left is **doc-audit** work on
`extensibility.mdx` (five metadata-patch rules with no row or ledger entry, all present at base too) and one
small `tool-calls.mdx` / `extensibility.mdx` gap (ENUM-201 skips `subject.type`). Plus at most one optional
RFD-only ledger entry (keep permission prompt copy out of `ToolCallUpdate.title/content`), which I recommend not
adding. RFD-backfill effort: **none (0 rows, 0 fixtures)**. Doc-audit spillover: **S**.

**Stage and changes since base.** All five were under "Active > v2" at base (`docs/docs.json:211-226 @ 3961af94`).
At the target they're under "Draft > v2" (`docs/docs.json:200-226 @ 3ea94133`): **Draft RFD**, so untracked
(`docs/spec-updates.md:44-51`). Only `meta-patches.mdx` changed, and only editorially: `subagent_update` and
`session_message` are no longer "draft-only" (`docs/rfds/v2/meta-patches.mdx:49`), the extensibility link drops
`/draft/` (`:109`), and a revision-history line was added (`:173`). The other four are byte-identical.

## Summary per RFD

| RFD (Draft at target) | Agent-side rules | Covered (docs + existing row/ledger) | Docs-stated, uncovered (doc audit) | RFD-only testable | RFD-only ledger | Effort |
|---|---|---|---|---|---|---|
| message-updates | 6 | 6 | 0 | 0 | 0 | none (0 rows, 0 fixtures) |
| tool-call-updates | 7 | 6 | 0 | 0 | 1 (shared with permission-requests, optional) | none (0 rows; 0-1 ledger) |
| meta-patches | 6 | 1 | 5 | 0 | 0 | none for RFD; doc audit S (about 5 ledger entries, 0 rows) |
| permission-requests | 7 | 5 | 1 (`subject.type` not checked by ENUM-201) | 0 | 1 (shared, optional) | none for RFD; doc audit S (widen ENUM-201 plus 1 unit-test case) |
| enum-variant-extension | 9 | 9 | 0 | 0 | 0 | none (0 rows, 0 fixtures) |

Client-side application semantics (patch merging, apply order, unknown-subject display), adapter conversion rules
and SDK guidance are not agent rules and are left out of the counts. They're listed under each RFD for
completeness.

## Requirements

Abbreviations. Docs paths are `docs/protocol/v2/draft/…` at `3ea94133`. "Schema" is
`schema/v2/schema.unstable.json` at `3ea94133`. Row ids are in `src/tck/v2/requirements.py` and ledger lines in
`spec-tracker/maps/v2.toml`. TCK citations still carry base line numbers. Remapping them is the re-vendor and
doc-audit job, not this one.

### message-updates (`docs/rfds/v2/message-updates.mdx`, Draft RFD)

| # | Agent-side rule (RFD line) | Docs/schema stating it @ 3ea94133 | Docs tier | TCK coverage |
|---|---|---|---|---|
| M1 | `messageId` required on `user_message`/`agent_message`/`agent_thought` and all chunks (:48, :144) | `prompt-lifecycle.mdx:567` (MUST); schema `UserMessage`/`AgentMessage`/`AgentThought`/`ContentChunk` `required` | MUST | ACP-PATCH-201 (`requirements.py:3062`) |
| M2 | IDs unique per message type; no reuse for a different message of that type (:44) | `prompt-lifecycle.mdx:68-70` (MUST NOT) | MUST | ledger `v2.toml:205-206` (partly unobservable) + ACP-PATCH-203 (`:3079`), ACP-CANCEL-002 (`:1248`) |
| M3 | Accepted user message is reported by updates/chunks under the prompt response's `messageId` (:66) | `prompt-lifecycle.mdx:362` (MUST), `:384` | MUST | ACP-PROMPT-203 (`:742`), ACP-PROMPT-201 |
| M4 | A retained, replayed user message keeps that ID (:66) | `prompt-lifecycle.mdx:386` (MUST); `session-setup.mdx:282-287` | MUST | ACP-RESUME-204 (`:1763`) |
| M5 | Replay rebuilding a message from chunks first sends the whole-message update with `content: []`; a metadata-only update is not enough (:68) | `session-setup.mdx:307-321` (MUST) | MUST | ACP-RESUME-205 (`:1780`) |
| M6 | `content`/`_meta` are three-state patch fields; `content` is an array (:49-56, :145) | schema `AgentMessage` etc.; `prompt-lifecycle.mdx:569-579` | shape | ACP-SCHEMA-001 (`:295`), ACP-META-201 (`:3683`) |

Not agent rules: client apply order and replace/append semantics (:50-57, :64, :72-125, :161-167). Tolerating
updates before or after the response (:66) is a client MUST (`prompt-lifecycle.mdx:362`). The v1 adapter rule
(:147) is out of scope. "A field that refers to a message must identify its type" (:44) is a schema-design
statement (`prompt-lifecycle.mdx:70`).

### tool-call-updates (`docs/rfds/v2/tool-call-updates.mdx`, Draft RFD)

| # | Agent-side rule (RFD line) | Docs/schema @ 3ea94133 | Docs tier | TCK coverage |
|---|---|---|---|---|
| T1 | No `sessionUpdate: "tool_call"`; `tool_call_update` is the only create/update (:45, :88) | `prompt-lifecycle.mdx:16-45` (complete standard set, no `tool_call`); schema `SessionUpdate` | MUST (closed set; any other non-`_` value is an illegal custom value, `extensibility.mdx:242`) | ACP-ENUM-201 (`:3596`): `tool_call` is not in `SESSION_UPDATE_KIND` (checked: `tck.v2.protocol.SESSION_UPDATE_KIND` lacks it), so it is flagged as a non-underscore custom discriminator |
| T2 | `toolCallId` required (:49) | `tool-calls.mdx:37-39`; schema `ToolCallUpdate.required` | MUST | ACP-PATCH-204 (`:3090`) |
| T3 | Patch fields three-state; `content`/`locations` arrays (:50-56, :89) | `tool-calls.mdx:102-123`; schema | shape | ACP-SCHEMA-001 |
| T4 | Agents **SHOULD** include `title` the first time they report a `toolCallId` (:58) | `tool-calls.mdx:42-43` (SHOULD) | SHOULD | ACP-PATCH-208 (`:3148`), ADVISORY |
| T5 | `tool_call_content_chunk` carries required `toolCallId` and exactly one `ToolCallContent` (:70-71, :90) | `tool-calls.mdx:183-188`; schema `ToolCallContentChunk.required` | MUST | ACP-PATCH-204 |
| T6 | A tool-call permission carries the same `ToolCallUpdate` shape under `subject.toolCall` (:60) | `tool-calls.mdx:259-262,270-273`; schema `ToolCallPermissionSubject` | shape | ACP-PERM-201 (`:1075`), ACP-SCHEMA-001; PATCH-208/-210 already fold subjects into per-call state |
| T7 | Permission prompt text goes in the request's `title`/`description`, not `ToolCallUpdate.title`/`content` (:62, lowercase "should") | Docs say only that the fields are separate and don't replace tool-call state (`tool-calls.mdx:248-256`). No agent-directed keyword. | none | uncovered. RFD-only guidance, see D1 |

Not agent rules: client apply order, replacement and clearing (:51-57, :72-76). "Omitted fields on a new id start at
protocol defaults" (:57) is client state, with the defaults in `tool-calls.mdx:105-108`.

### meta-patches (`docs/rfds/v2/meta-patches.mdx`, Draft RFD)

| # | Agent-side rule (RFD line) | Docs @ 3ea94133 | Docs tier | TCK coverage |
|---|---|---|---|---|
| MP1 | Upsert top-level `_meta` is omitted, `null` or an object (:31-33, :108) | `extensibility.mdx:77,111-118`; schema | shape | ACP-META-201 (`:3683`); ACP-META-203 already treats a `null` key as a removal |
| MP2 | To resend current metadata the Client may already hold, the Agent removes stale keys (`null` each, or `_meta: null` then the object) (:91) | `extensibility.mdx:154`; `session-setup.mdx:333-335` | no keyword (imperative) | **none** |
| MP3 | When the current metadata is empty, send `_meta: null`, not `{}` (:92) | `extensibility.mdx:154` | no keyword (imperative) | **none** |
| MP4 | Replay applies patches as live delivery does and never resets implicitly; a content-replacing update keeps unmentioned keys (:89-90) | `extensibility.mdx:154`; `session-setup.mdx:330-332` | no keyword | **none** |
| MP5 | Intermediaries that combine updates **MUST** keep removals and clears (:94) | `extensibility.mdx:154` (MUST) | MUST (intermediary) | **none** |
| MP6 | Don't copy non-patch metadata (e.g. a `session/list` entry's `_meta`) into a patch unchanged (:137) | `extensibility.mdx:156` | no keyword (imperative) | **none** |

MP2-MP6 were in the docs at base too (`extensibility.mdx:151,153 @ 3961af94`), so this gap predates this update and
was missed by the earlier doc audit. They belong to the **`extensibility.mdx` doc audit**, not to this RFD.
Not agent rules: "Clients **MUST NOT** merge nested objects" (:36), the merge table (:117-129, an SDK conformance
list) and the adapter rules (:133-137).

### permission-requests (`docs/rfds/v2/permission-requests.mdx`, Draft RFD)

| # | Agent-side rule (RFD line) | Docs/schema @ 3ea94133 | Docs tier | TCK coverage |
|---|---|---|---|---|
| P1 | `title` required (:36, :93) | `tool-calls.mdx:248-251`; schema `RequestPermissionRequest.required` = `sessionId,title,options` | MUST | ACP-PERM-201 (`:1075`) |
| P2 | `options` required, at least one (:94) | `tool-calls.mdx:275-277`; schema `minItems: 1` | MUST | ACP-PERM-201 |
| P3 | `subject` optional tagged union (`tool_call` with `toolCall`, `command`); omitted is the same as `null` (:38-51, :76) | `tool-calls.mdx:259-265`; schema `RequestPermissionSubject` (with an `other` fallback) | shape | ACP-SCHEMA-001 (PERM-201 validates the request against the schema) |
| P4 | Command subject: `command` and `cwd` required (:68) | `tool-calls.mdx:302`; schema `CommandPermissionSubject.required` | MUST | ACP-SCHEMA-001 / ACP-PERM-201 |
| P5 | Command subject `cwd` **MUST** be absolute (:68) | `tool-calls.mdx:302-303` (MUST) | MUST | ACP-PERM-202 (`:1094`) |
| P6 | Custom subject types use the `_` namespace (:78 together with the enum RFD) | `extensibility.mdx:238-243`; schema `RequestPermissionSubject` `other` branch (`_` reserved for extensions, non-`_` for ACP) | MUST NOT (custom non-`_`) | **gap**: ACP-ENUM-201 deliberately skips `subject.type` (`open_enums.py:8`; `requirements.py:3613`; added in `6d61343` with no recorded reason). Doc audit |
| P7 | Permission copy lives in `title`/`description`, not subject tool-call fields (:13, :21, :113-115) | see T7 | none | uncovered. Same item as T7, see D1 |

Not agent rules: the command subject's IDs "do not change state" and the command "never asks the Client to
execute" (:68, `tool-calls.mdx:305-307`), which describe semantics. Preserving or displaying unknown subjects
(:78) is a client SHOULD (`tool-calls.mdx:263-265`).

### enum-variant-extension (`docs/rfds/v2/enum-variant-extension.mdx`, Draft RFD)

| # | Agent-side rule (RFD line) | Docs @ 3ea94133 | Docs tier | TCK coverage |
|---|---|---|---|---|
| E1 | `_` values are extension-owned; non-`_` values are ACP-owned, including future ACP variants (:33-35) | `extensibility.mdx:238-241` | definitional | enforced through E2 |
| E2 | Extensions MUST NOT define custom non-underscore values (:36) | `extensibility.mdx:242`; also `tool-calls.mdx:76,372` | MUST | ACP-ENUM-201 (`:3596`), ACP-STATE-203 (`:787`), ACP-AUTH-206 (`:2955`) and other per-site rows |
| E3 | MUST NOT treat an unknown non-`_` value as a custom extension (:37) | `extensibility.mdx:243` | MUST | ledger `v2.toml:260-262` (not observable) |
| E4 | SHOULD preserve unknown values when storing, replaying, proxying or forwarding (:38) | `extensibility.mdx:252` | SHOULD | ledger `v2.toml:280-282` |
| E5 | SHOULD degrade gracefully on an unknown value it cannot act on (:39, :72) | `extensibility.mdx:65-68,252` | SHOULD (display) / see E6 | ACP-ENUM-203 (`:3626`, agent survives a `_` outcome); display half in ledger `v2.toml:280-282` |
| E6 | A request that can't be fulfilled without understanding the variant is rejected with `-32602` (:43, no keyword) | `extensibility.mdx:65-66` (**MUST**) | MUST | ACP-PROMPT-211 (`:982`), ACP-ENUM-204 (`:3642`, closed site) |
| E7 | Unknown permission outcomes are never treated as approval (:43) | `tool-calls.mdx:347-349` (MUST NOT) | MUST | ACP-PERM-204 (`:1140`), ACP-PERM-002 |
| E8 | An unknown response variant (e.g. elicitation action) falls back to the most conservative known behaviour (:43) | `elicitation.mdx:197` (MUST: unknown action is handled as `cancel`) | MUST | ledger `v2.toml:381-383` (Deferred, elicitation coverage) |
| E9 | A malformed known discriminator must not fall through to the fallback (:63) | `extensibility.mdx:60-62,162` (MUST NOT) | MUST | ledger `v2.toml:255-257` |

Not agent rules: SDK fallback-variant guidance (:59-66, :70) and v2-to-v1 conversion failure (:67). E10, "parsers
must not fail solely because a value is unknown" (:72), is `extensibility.mdx:54-55` (MUST accept). It is
covered by ACP-ENUM-203 and ACP-EXT-204 and folded into E5/E6 above, so it isn't counted separately.

## Details

Proposed work, if the orchestrator wants the spillover done. All of it is doc-audit work, so it cites docs, not
these RFDs.

1. **`extensibility.mdx` metadata-patch ledger entries (doc audit, S).** Five `[[not_requirement]]` entries, or
   fewer if grouped:
   - `extensibility.mdx:154; session-setup.mdx:333-335`: on resync the Agent removes stale keys. Reason: not
     observable. The client can't know which keys the agent considers current. On a full replay the client
     rebuilds rather than merges (`session-setup.mdx:300`), and a new connection holds no metadata.
   - `extensibility.mdx:154`: send `_meta: null`, not `{}`, for empty metadata. Reason: not decidable. `_meta: {}`
     is a legal no-op patch (`:116`), so an occurrence can't be told apart from an intentional no-op.
   - `extensibility.mdx:154`: replay never resets metadata implicitly. Reason: client-side application, and
     whether replayed metadata reproduces the agent's intended state isn't visible.
   - `extensibility.mdx:154`: intermediaries that combine updates MUST keep removals and clears. Reason: not
     observable. Combining happens inside the agent or proxy, and the TCK sees only the result stream with no
     record of the pre-combination updates.
   - `extensibility.mdx:156`: don't copy non-patch `_meta` into a patch. Reason: not decidable. A
     `session_info_update` with a `null` key may be a deliberate removal.
   None of these reasons rests on a TCK choice.
2. **Widen ACP-ENUM-201 to `subject.type` (doc audit, S).** One check in
   `OpenEnumScan.scan_permission_request` (`open_enums.py:74-85`) against `{"tool_call", "command"}` (derive from
   schema `RequestPermissionSubject` in `tck.v2.protocol`, as the other constants are). Flip
   `test_subject_type_itself_is_not_judged` into a violation case. Edit the row text at `requirements.py:3613` and
   add `tool-calls.mdx:259-265` to the citation. No new fixture is needed, because the existing permission-requesting
   fixture's `subject.type` is already `tool_call`. A negative fixture is optional (the unit test suffices). Only
   observable when the agent asks for permission, the same as the existing permission sites. Ask the user first
   whether the original exclusion had a reason (see Open questions).

## Testability notes

- Every covered rule is already asserted passively over the normal prompt turn (PATCH-201/-204/-208, PERM-201/-202,
  ENUM-201) or over the resume replay (RESUME-204/-205). No new mock-client or harness behaviour is needed for
  anything in this report.
- The client-side rules these RFDs define (merging, apply order, displaying unknown values) aren't observable from
  the client, by construction. The TCK *is* the client.
- T7/P7 (prompt copy kept out of `ToolCallUpdate.title/content`) can't be decided: a `subject.toolCall.title` that
  differs from the earlier title can be a legitimate title update.

## Discrepancies

Docs win in every case. None of these changes a tier on an existing row.

- **E6:** the RFD states `-32602` rejection without a keyword (`enum-variant-extension.mdx:43`). The docs make it a
  MUST (`extensibility.mdx:65-66`). Rows already follow the docs.
- **E8:** the RFD says "most conservative known behaviour" in general terms (`:43`). The docs pin it to "handle as
  `cancel`" for elicitation (`elicitation.mdx:197`).
- **E5/closed sites:** the RFD lets request-core unions "stay closed or be opened" (`:43`). The docs enumerate the
  closed sites (`extensibility.mdx:245-250`). ACP-ENUM-204 follows the docs.
- **T3:** the RFD's patch-field list (`tool-call-updates.mdx:50`) omits `capabilities`, which the schema has
  (`ToolCallUpdate.properties.capabilities`). The RFD says `null` "clears or unsets" (`:52`); the docs say `null`
  "resets the field to its default" (`tool-calls.mdx:104`, so `status: null` means `pending`). ACP-PATCH-210
  follows the docs.
- **meta-patches:** the RFD's "draft-only" qualifier was removed at the target (`:49`), matching
  `extensibility.mdx:111`. No conflict remains.

## Decisions for the user

- **D1 (recommend: no entry).** The RFD-only guidance "put permission prompt copy in `title`/`description`, not in
  `ToolCallUpdate.title`/`content`" (`tool-call-updates.mdx:62`, `permission-requests.mdx:13,21,115`, Draft RFD)
  has no RFC keyword and is not decidable. A ledger entry citing a Draft RFD for a non-keyword design statement
  adds noise. If one is wanted anyway, use a single entry citing `docs/rfds/v2/permission-requests.mdx:13,115
  (Draft RFD)`, reason "Not observable: whether a tool-call title is permission copy is agent intent".
- **D2 (recommend: yes).** Is citing these Draft RFDs justified? **No.** `docs/spec-updates.md:69` allows a Draft
  RFD citation only where nothing else states the rule, and the docs or schema state every agent-side rule here.
  The deferred "backfill the other 13 `rfds/v2/*`" item, at least for these five, should be closed as "absorbed by
  the docs". The remaining work moves to the `extensibility.mdx` doc audit (items 1 and 2 under Details).

## Open questions

- Why does ACP-ENUM-201 skip `subject.type`? It was added in `6d61343` with no recorded reason (a test pins the
  exclusion). If there was none, widen it (Details item 2).
- Outside this scope: the ledger group header at `v2.toml:358` ("coverage deferred: the TCK never advertises an
  elicitation mode") states a TCK choice as the blocker. The entries below it give real blockers (e.g. `:381-383`
  needs an agent with a live elicitation). Worth a look by whoever owns the elicitation audit.
- The other eight `rfds/v2/*` pages that are now Draft were not examined.
