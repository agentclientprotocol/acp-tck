# Impact of spec update 3961af94 -> 3ea94133 on v2 `extensibility.mdx` (and `open_enums.py`)

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (target) vs
`3961af94fa62d2386d993cadf1afc8b146fc799a` (base). I read everything with `git show <rev>:<path>` in
`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`. Its HEAD is `6ace4f6a`, a descendant of the
target. I did not pull, because the brief pins the revision and forbids touching the checkout. HEAD and the target
have the same `extensibility.mdx`. Files read: `docs/protocol/v2/draft/extensibility.mdx` (the whole doc, both revs,
plus its diff); target `prompt-lifecycle.mdx:700-712,940-1000`, `slash-commands.mdx:165-175,250-258` and
`initialization.mdx:255-266`; `schema/v2/schema.unstable.json` at both revs, programmatically diffed. The TCK's
vendored `src/tck/v2/schema/schema.unstable.json` is byte-identical to the base file. I did not consult the
reference SDKs: no rule here depends on runtime behaviour the spec leaves implicit.
**Confidence:** high. The doc diff is two hunks; I mapped every citation line by line and checked the enum sets
programmatically against both schemas.

## Doc changes in brief
- `When a capability is required` table (base 31-38 -> target 31-41): "Markdown and file-backed plans" becomes
  "Markdown plans", and three rows are added: Prompt suggestions (`:39`), Skills (`:40`) and Session cursors (`:41`).
  **Line shift: base line N >= 39 maps to target N+3. Lines <= 30 are unchanged.**
- Metadata patches (base 108 -> target 111): `subagent_update` and `session_message` are no longer called
  "draft-only". The list of patch sites is otherwise the same.

## Registry rows citing `extensibility.mdx` (`src/tck/v2/requirements.py`)

| id | classification | target citation (`extensibility.mdx` @ 3ea94133) | note |
|---|---|---|---|
| ACP-STATE-203 | citation-only | `:238-243` (was 235-240) | |
| ACP-PROMPT-211 | citation-only | `:65-68` (was 62-65) | `ContentBlock` gains `skill`. The probe type `_tck_unknown` is still unknown, so the test is unaffected. |
| ACP-CLIENTCAP-202 | citation-only | `:168,177` (was 165,174) | |
| ACP-JSONRPC-004 | citation-only | `:205-216` (was 202-213) | |
| ACP-JSONRPC-005 | citation-only | `:205-216` (was 202-213) | |
| ACP-AUTH-206 | citation-only | `:236-245` (was 233-242) | |
| ACP-AUTH-008 | citation-only | `:238-243` (was 235-240) | |
| ACP-ENUM-201 | citation-only for this doc; **behaviour changes through `open_enums`/`protocol.py`** (see below); optional text change (Decision 1) | `:238-243` (was 235-240) | Its other citations (`agent-plan.mdx`, `slash-commands.mdx:110`) belong to those docs' researchers. |
| ACP-ENUM-203 | citation-only | `:54-58,240,252` (was 51-55,237,249) | |
| ACP-ENUM-204 | citation-only | `:245-248` (was 242-245) | |
| ACP-EXT-001 | citation-only | `:168,177,190,234` (was 165,174,187,231) | |
| ACP-META-001 | citation-only | `:75,77,100-105,107` (was 72,74,97-102,104) | |
| ACP-META-202 | citation-only | `:77` (was 74) | |
| ACP-META-203 | citation-only (the cited patch-list line changed, but not in a way that matters) | `:100-103,111-118` (was 97-100,108-115) | The row **text** contains the literal "`:108-115`", which must become "`:111-118`". |
| ACP-META-204 | citation-only | `:105,262` (was 102,259) | |
| ACP-EXT-002 | citation-only | `:234` (was 231) | |
| ACP-EXT-202 | citation-only | `:256-264` (was 253-261) | |
| ACP-EXT-204 | citation-only | `:54-55,160` (was 51-52,157) | The probe names (`tckFutureCapability`, `auth.tckFutureAuthMode`, `info.tckFutureField`) do not collide with the new client capabilities (`session.promptSuggestions`, `session.commands.skill`). |
| ACP-EXT-203 | citation-only | `:168,234` (was 165,231) | |
| ACP-SCHEMA-002 | citation-only | `:107,238-245` (was 104,235-242) | |

No row cites the changed table lines (31-41) or any RFD. No row is removed and no tier or gate changes.

## Ledger entries (`spec-tracker/maps/v2.toml:247-282`)

| citation (base) | classification | target citation | note |
|---|---|---|---|
| `:16-19,26` | unchanged | `:16-19,26` | Text identical. The reason does not rest on a TCK choice. |
| `:57-60,159` | citation-only | `:60-63,162` | |
| `:157,240` | citation-only | `:160,243` | |
| `:102` (MCP keys preserved) | citation-only | `:105` | The reason is "Deferred". It names a real blocker (no prompt can force a tool call); the stub's lack of tools is secondary. Acceptable. |
| `:102,259` | citation-only | `:105,262` | |
| `:215,253,261` | citation-only | `:218,256,264` | |
| `:249` | citation-only | `:252` | |

No existing ledger reason citing this doc rests on a TCK choice.

## Code comments and fixtures citing line numbers (update with the shift; no `@` rev, so no test catches them)
- `src/tck/v2/open_enums.py:7`: `237-240` -> `240-243`
- `src/tck/v2/protocol.py:176`: `108-115` -> `111-118`. `protocol.py:193`: `102,259` -> `105,262`
- `src/tck/v2/conformance/test_enums.py:5` (`242-247` -> `245-250`), `:21` (`235-240` -> `238-243`),
  `:27` (`51-55` -> `54-58`), `:224` (`242-245` -> `245-248`)
- `src/tck/v2/conformance/test_jsonrpc.py:14` (`187` -> `190`), `:165` (`202` -> `205`)
- `src/tck/v2/conformance/test_extensibility.py:44,133,189,239,272,297,327,356,361,392,419`: apply the same +3 to
  every line >= 39 (`74`->`77`, `97-100`->`100-103`, `102,259`->`105,262`, `231`->`234`, `253-261`->`256-264`,
  `51-52,157`->`54-55,160`, `261`->`264`, `165,231`->`168,234`, `104`->`107`)
- Fixtures: `accepts_contentless_embedded_resource.py:4` (`242-245`->`245-248`), `rejects_malformed_meta.py:3`
  (`74`->`77`), `malformed_traceparent.py:4` (`97-100`->`100-103`), `unprefixed_meta_key.py:3` (`102`->`105`).
  `rejects_unknown_capability_fields.py:4` cites `extensibility.mdx:148`, which was already stale at base (the rule
  was base `:157`). It should become `:160`.

## `open_enums.py` / `protocol.py` against the alpha.16 schema

I re-derived each set from the target schema with the same algorithm as
`tests/v2/test_validation.py::_consts_from_schema`.

| set (`protocol.py`) | `$def` | change at target | effect |
|---|---|---|---|
| `SESSION_UPDATE_KIND` | `SessionUpdate.sessionUpdate` | **+`cursor_update`, `prompt_suggestions_update`, `replay_complete`** | Must be added. Otherwise a conforming agent emitting them FAILs ACP-ENUM-201. |
| `PLAN_CONTENT_TYPE` | `PlanUpdateContent.type` | **-`file`** (the `PlanFile` `$def` is gone) | Must be dropped. After that, an agent that still emits `plan.type: "file"` FAILs ACP-ENUM-201 (a non-`_` value outside the defined set). This is correct at the target. |
| `AVAILABLE_COMMAND_TYPE` | `AvailableCommand.type` | **+`skill`** | Must be added. |
| `TOOL_KIND`, `TOOL_CALL_STATUS`, `PLAN_ENTRY_*`, `STATE_UPDATE_STATE`, `TOOL_CALL_CONTENT_TYPE`, `PERMISSION_OPTION_KIND`, `STOP_REASONS`, `DIFF_*`, `BACKGROUND_WORK_TYPE` | | unchanged | `BackgroundWork` changed only in a description (the UNSTABLE banner was removed from the subagent branch). |

`test_enum_sets_match_the_schema` will fail on the three changed sets as soon as the schema is re-vendored, which is
the intended tripwire. `open_enums.py` itself needs no logic change for these three.

The scan below covers every open union in the target schema (any `anyOf`/`oneOf` with a "custom or future"
fallback). Open-enum sites that are new or changed and that ENUM-201 does **not** currently check:
- `CursorAnchor.type` (`user_message`, `agent_message`, `agent_thought`, `session_message`, `tool_call`,
  `compaction`) and `CursorAnchorPosition` (`before`, `after`). Both are new and agent-emitted in `cursor_update`.
  `prompt-lifecycle.mdx:984` states that "`type` and `position` accept [custom and future values]" and links to
  extensibility's enum section. See Decision 1.
- `SessionConfigOptionCategory` gains `speed`. The TCK checks `category` nowhere, before or after this update, so
  there is no impact.
- `ContentBlock.type` gains `skill`. ENUM-201 does not check `ContentBlock` sites, so there is no impact.
- `InitialSessionConfigOption` is a new open union, but it is client-sent. The rule it carries belongs to the
  session-setup researcher (Open questions).

## New requirements

The two agent-side rules below appear in this doc's table only in lowercase ("must not") as examples. Their
normative MUST NOT is in docs other researchers own. I list them so they are not lost; **dedupe with the
prompt-lifecycle and slash-commands reports** and keep one row each.

1. **`ACP-CLIENTCAP-2xx` (provisional): no prompt suggestions without the client capability.**
   - Text: "With a client advertising no `capabilities.session.promptSuggestions`, no `prompt_suggestions_update` is
     observed."
   - Tier: CAPABILITY, gate `capabilities.session` (the registry convention for the session surface).
   - Citation: `prompt-lifecycle.mdx:707` (MUST NOT, primary); `extensibility.mdx:39`;
     `schema/v2/schema.unstable.json#/$defs/PromptSuggestionsUpdate` (its description also says "Agents MUST only
     send this update when the Client advertised...").
   - Test: reuse the ordinary `session/new` plus prompt-turn transcript, as `ACP-CLIENTCAP-003` does. The TCK's
     default `initialize` sends `capabilities: {}` (`src/tck/v2/__init__.py:23`). Any `session/update` with that
     `sessionUpdate` FAILs, and absence PASSes.
   - Harness: none new.
2. **`ACP-CLIENTCAP-2xx` (provisional): no `skill` command entries without the client capability.**
   - Text: "With a client advertising no `capabilities.session.commands.skill`, no `availableCommands` entry has
     `type: "skill"`, in setup responses or in `available_commands_update`."
   - Tier: CAPABILITY, gate `capabilities.session`.
   - Citation: `slash-commands.mdx:171` (MUST NOT, primary); `extensibility.mdx:40`; `initialization.mdx:258-260`.
   - Test: same transcript. Scan the `session/new` result's `availableCommands` (if present) and every
     `available_commands_update`.
   - Note: once `skill` is added to `AVAILABLE_COMMAND_TYPE`, ENUM-201 alone would no longer flag such an entry, so
     this row is the only check for this rule.
   - Harness: none new.

The doc introduces no other agent-side rule. The remaining new table text binds clients ("Clients must not send
`skill` content blocks that it does not allow"; "a method that accepts a `cursorId` still needs its own
capability") or only describes behaviour ("an Agent that supports cursors sends `cursor_update`").

## New ledger entries
None. The new client-binding rules are excluded by the ledger's agent-side-only rule.

## Discrepancies
- **The metadata-patch site list is incomplete.** `extensibility.mdx:111` lists the upsert updates whose `_meta` is a
  patch, but it omits `cursor_update`. Yet `prompt-lifecycle.mdx:950` ("`_meta` follows the [metadata patch]
  rules") and `$defs/CursorUpdate` ("A concrete `_meta` object patches the stored metadata by top-level key") both
  make it a patch site. There is no TCK impact today, because no TCK code enumerates patch sites. ACP-META-203 skips
  `null` values at any `_meta`.
- Pre-existing, not caused by this update: ACP-META-203's test (`test_extensibility.py:194`) treats a `null` W3C key
  as a patch removal at every `_meta`. At non-patch sites `extensibility.mdx:156` says a `null` key is "ordinary
  data". The check is lenient there, but harmlessly so.
- The checkout's HEAD (`6ace4f6a`) adds `minItems: 1` to `Diff.changes`. This is beyond the target and out of scope.

## Decisions for the user
1. **Extend ACP-ENUM-201 to `cursor_update`'s `anchor.type` and `anchor.position`?** I recommend **yes**.
   - The change: add `CURSOR_ANCHOR_TYPE` and `CURSOR_ANCHOR_POSITION` sets to `protocol.py` with schema cross-checks,
     a `cursor_update` branch in `OpenEnumScan.scan_update`, the two sites in the row text, and the citation
     `prompt-lifecycle.mdx:984` plus `schema/v2/schema.unstable.json#/$defs/CursorAnchor`.
   - Why: the target doc ties these fields explicitly to the open-enum rule, and they appear in an ordinary exchange
     whenever an agent supports cursors.
   - The alternative is to leave the curated list as is. It is explicitly non-exhaustive, so that would not be a
     conformance gap.
2. **Who owns the two `ACP-CLIENTCAP-2xx` rows.** I recommend they live under the prompt-lifecycle and
   slash-commands reports, with `extensibility.mdx:39`/`:40` as secondary citations. The tier should be CAPABILITY
   `capabilities.session`, not ADVISORY: the primary text is MUST NOT, and the table's lowercase wording is only an
   example.
3. **The `PLAN_CONTENT_TYPE` drop of `file` turns a previously conforming `file` plan into an ENUM-201 FAIL.**
   I recommend accepting it, since it follows the target schema. Make sure the agent-plan researcher also removes
   any fixture or ledger that relies on file plans (the inventory already flags the "Plan file URIs MUST be
   absolute" ledger entry).

## Open questions (for other researchers)
- `InitialSessionConfigOption` (new, client-sent on session setup): an unknown `configId`, a mismatched `type`, or a
  disallowed value is "ignored instead of rejected". That rule belongs to the session-setup researcher, not here.
- Skill content blocks: the agent must reject a disallowed or unresolvable `skill` block with `-32602`
  (`slash-commands.mdx:255`). That rule belongs to the slash-commands researcher.
