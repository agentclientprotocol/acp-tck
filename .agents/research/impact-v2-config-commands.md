# v2 impact: `session-config-options.mdx` + `slash-commands.mdx` (alpha.9 -> alpha.14)

**Sources checked:** agent-client-protocol (worktree `agent-client-protocol-2`), base `beac4ba96190` -> target `3961af94fa62`
(docs read whole at target, plus `git diff` of both docs; target `schema/v2/schema.unstable.json` `$defs` diffed
structurally against base; vendored `src/tck/v2/schema/schema.unstable.json` is byte-identical to base). acp-tck @
`200baba` (registry, `test_session_config.py`, `_helpers.py`, v2 fixtures, `tests/v2/test_cli.py`). Reference SDKs
**not consulted**: every rule below is stated explicitly in spec text and/or schema descriptions, so none relies on
implicit runtime behaviour. A2A TCK not consulted.
**Confidence:** high for the classifications and new MUSTs (explicit RFC-keyword text in doc and schema agree);
medium for the CONFIG-203 tightening and the attribution decision, which are judgement calls for the orchestrator.

All target citations below are `@ 3961af94fa62`. `SCO` = `docs/protocol/v2/draft/session-config-options.mdx`,
`SC` = `docs/protocol/v2/draft/slash-commands.mdx`, `SS` = `docs/protocol/v2/draft/session-setup.mdx`,
`schema#X` = `schema/v2/schema.unstable.json#/$defs/X`.

## Summary table

| id | classification | one-line note |
|----|----------------|---------------|
| ACP-CONFIG-201 | **changed text** (+ test change) | "the schema sets no minimum length" is now false: select options and each group MUST be non-empty (SCO:128-131, B7 `minItems: 1`). Test's hand check explicitly allows `[]`. |
| ACP-CONFIG-202 | changed text (minor) + citation | Add the new MUST "agents that advertise config options MUST support `session/set_config_option`" (SCO:234, initialization.mdx:239-240); test already asserts success. Text otherwise matches SCO:236/291. |
| ACP-CONFIG-203 | **changed text — DECISION NEEDED** | `SS` went from "MAY include" to "MUST include" config options in setup responses (SS:108, 333-335). Test SKIPs when resume omits `configOptions`; could now FAIL. Inherits 201's non-empty change. |
| ACP-CONFIG-204 | changed text + citation | Membership is now an explicit MUST (SCO:130; `schema#SessionConfigSelect` `currentValue` description), not "derived from C5's default-value MUST" (that sentence was removed). Test unchanged. |
| ACP-CONFIG-205 (unregistered) | stays unregistered -> **ledger** | SCO:236 now says outright the response "may report a `currentValue` different from the one requested". |
| ACP-CONFIG-206 | citation-only (meaning moved) | Cited range 331-386 now holds the new SHOULD-notify text; the completeness rule is SCO:459. Remap to 373-379,459. Text/test unchanged. |
| ACP-CONFIG-207 | **new**, CAPABILITY (inferred:configOptions) | Unknown `configId` -> `-32602` (SCO:234). |
| ACP-CONFIG-208 | **new**, CAPABILITY (inferred:configOptions) | Invalid value (undeclared select value, mismatched `type`, unsupported value `type`) -> `-32602` (SCO:234). |
| ACP-CONFIG-209 | **new**, CAPABILITY (inferred:configOptions) | A rejected set leaves the configuration unchanged (SCO:234). |
| ACP-CONFIG-210 | **new**, CAPABILITY (inferred:configOptions) | Select `value`s unique within an option, including across groups (SCO:128-130). |
| ACP-CONFIG-211 | **new**, ADVISORY | A state-changing `session/set_config_option` is accompanied by a `config_option_update` on the requesting connection (SCO:375). |
| ACP-CONFIG-212 | **new**, ADVISORY | That duplicate notification precedes the response (SCO:377-379). |
| ACP-COMMANDS-201 (area name open) | **new**, CAPABILITY (inferred:availableCommands) | Every advertised command validates as `AvailableCommand` (`type` required, B5) and its `name` has no whitespace and is unique within the list (SC:91-100, 110). |
| ledger x6 | new deliberate non-requirements | See "Ledger" below. |

No registry row cites `slash-commands.mdx`. No v2 fixture or v2 conformance test sends or emits `availableCommands`/
`available_commands_update` (grep of `tests/`, `src/tck/v2/` for `available_commands|availableCommands|AvailableCommand`
hits only `src/tck/v2/protocol.py:93` (the discriminator name table) and `requirements.py:956` (RESUME-202 prose)).
**So B5 breaks no fixture and no `test_cli.py` expectation.** It does change what real agents get judged on. See D2.

## Wire changes that hit these docs (from the inventory, verified against target schema)

- **B5** `schema#AvailableCommand` is now `anyOf` [`{type: const "command"} + allOf $ref Command`, `other`: `{type,
  name, description}` required, `not type=="command"`, `additionalProperties: true`]. New `schema#Command` holds
  `name`, `description` (required), `input`, `_meta`. A command without `type` now fails validation everywhere it
  appears: `NewSessionResponse`/`ResumeSessionResponse`/`ForkSessionResponse.availableCommands`,
  `schema#AvailableCommandsUpdate`.
- **B7** `schema#SessionConfigSelectOptions` both branches `minItems: 1`; `schema#SessionConfigSelectGroup/properties/options`
  `minItems: 1`.
- Description-only (normative text in schema, not enforced): `schema#SessionConfigSelect` `currentValue` "MUST be one
  of the `value`s in `options`", `options` "MUST contain at least one value, and each `value` MUST be unique within
  the option, including across groups"; `schema#SetSessionConfigOptionRequest` "Agents MUST support this method for
  any session where they advertise config options. Agents MUST reject an unknown `configId` or invalid value with
  `-32602` and leave the configuration unchanged"; its `other` branch "Agents MUST reject ... a value type they do
  not support with `-32602`"; `Command`/`other` `name` "MUST NOT contain whitespace and MUST be unique within the
  command list"; setup responses' `configOptions` "Senders MUST use an array, not `null`".
- Removed `x-deserialize-default-on-error` on `AvailableCommandsUpdate`/`ConfigOptionUpdate`/
  `SetSessionConfigOptionResponse.configOptions`: receiver-side hints. The TCK's validator ignores `x-deserialize-*`
  (strict jsonschema, `src/tck/v2/validation.py`), so this has no effect.

## Details per existing requirement

### ACP-CONFIG-201: changed text, test change required

- Old text: "... a `select` entry's `options` is an array, either flat or grouped, never mixed (the schema sets
  no minimum length)."
- Target rule: SCO:125-133 "For a `select` option, Agents **MUST** offer at least one value ... Each group **MUST**
  contain at least one value." Schema enforces both (B7).
- Proposed text: "... a `select` entry's `options` is a **non-empty** array, either a flat `SessionConfigSelectOption[]`
  or a grouped `SessionConfigSelectGroup[]` whose every group has a non-empty `options`. Never mixed."
- Proposed citation: keep the schema pointers; doc `SCO:93-154` (old 93-146 mapped to target 93-147. Extend it to
  154 so the grouped-select section is included, since the row judges grouped shape). Add `schema#SessionConfigSelect`
  (already there).
- Test (`src/tck/v2/conformance/test_session_config.py::_assert_config_options_shape_valid`): drop the "No minimum
  length" comment. Assert `opts` is non-empty, and for the grouped shape assert every group's `options` is a non-empty
  list. This matters most for ACP-CONFIG-203, which reuses the helper on the `session/resume` result **without** schema
  validation. On the `session/new` path, `_new_session_full_result` already schema-validates, so after the refresh an
  empty list would FAIL there first.
- Fixtures: both config fixtures (`conforming_full.py`, `config_set_omits_changed_option.py`) use 3-value flat
  selects. Nothing breaks.

### ACP-CONFIG-202: minor text addition, citation remap

- SCO:234 (new): "Agents that advertise config options for a session **MUST** support `session/set_config_option`
  for it." Restated at initialization.mdx:239-240 and overview.mdx:132-134 ("required when the Agent advertises
  config options"). SCO:236 (new): "The response's `configOptions` is the complete list as of the response ... It
  may report a `currentValue` different from the one requested." SCO:291 MUST respond with the complete list
  (unchanged). Note at SCO:367-371 (reworded, same meaning).
- The test already asserts the set succeeds (`result` object) and only *records* echo and id-superset. That matches
  SCO:236, which now explicitly permits a different `currentValue`.
- Proposed: prepend "A well-formed set of an advertised option succeeds (agents advertising config options MUST
  support the method); ...". Citation: `SCO:234,236,291,367-371; docs/protocol/v2/draft/initialization.mdx:239-240;
  docs/rfds/session-config-options.mdx:45; schema#SetSessionConfigOptionRequest; schema#SetSessionConfigOptionResponse`
  (the RFD line 45 is unchanged, and the RFD was not touched by the diff).
- Alternative: register the "MUST support" rule as its own id. I don't recommend it, because its only observable
  failure (an error on a valid set) is exactly what 202 already FAILs on.

### ACP-CONFIG-203: DECISION NEEDED (tighten "when present")

- Old cited text (base SS:94, 313-315): setup responses "**MAY** include" `configOptions`, and the resume response
  "**MAY** also include" them.
- Target: SS:108 "Because a setup response replaces the lists the Client holds, an Agent whose session has
  configuration options or commands **MUST** include them in that response." SS:333-335 "The response also includes
  the current `configOptions` and `availableCommands`". SS:136 "Agents **MUST NOT** send `null` for these fields". The
  same MUST appears for commands at SC:12.
- Current test: SKIPs "session/resume result carried no configOptions to validate".
- **Recommendation:** split the change. (a) Keep 203 as the shape row, inheriting 201's non-empty rule (citation
  `SS:108,136,333-335; schema#ResumeSessionResponse/properties/configOptions`). (b) Tighten 203, or add a separate id,
  so that a resume omitting `configOptions` FAILs when `session/new` on the same connection/route advertised them. The
  catch is observability. `obtain_resumable_session` doesn't return the resumed session's own `session/new` result,
  and the test only knows that *a* session (on another connection) had config options. An agent whose session
  legitimately lost all options between new and resume is wire-identical to a non-conforming one, though that is
  unusual. If tightened, keep it CAPABILITY and FAIL only when the resumed session's own `session/new` response
  (route 1/2 transcript) carried non-empty `configOptions`. Otherwise SKIP. This rule lives in `session-setup.mdx`,
  so the session-setup researcher may also propose it. Coordinate so only one id is created.

### ACP-CONFIG-204: changed text, citation remap; test unchanged

- Old basis: "derived from C5's always-a-default-value MUST plus the field descriptions". The base sentence "Agents
  **MUST** always provide a default value for every configuration option" is **gone** (replaced at SCO:222 by
  "Every configuration option's `currentValue` is the value the Agent is using ... Agents **MUST** be able to operate
  with it").
- Target: an explicit MUST at SCO:130 ("`currentValue` **MUST** be one of them"), mirrored in
  `schema#SessionConfigSelect` `currentValue` description. Still not schema-enforced.
- Proposed text: "A `select`-type option's `currentValue` is one of its declared `options` values (flat or grouped).
  Explicit MUST, not schema-enforced." Citation `SCO:116-119,125-133; schema#SessionConfigSelect`.
- Optional widening (not required by the diff): the same MUST applies to every carrier (set response,
  `config_option_update`, resume). The test checks only `session/new`.

### ACP-CONFIG-205: not registered; keep it that way and record it in the ledger

History: commit 057f45c left the set-value-reflection ADVISORY unregistered. SCO:236 now explicitly permits a
different `currentValue` in the response. See ledger L5.

### ACP-CONFIG-206: citation-only, but the cited range's meaning moved

- Old 331-386 = "From the Agent" heading + example. At target, "From the Agent" is SCO:373-457. Its first lines are
  now the new SHOULD-notify/ordering text (375-379), which belongs to the proposed 211/212. The completeness
  statement is SCO:459 ("This notification also contains the complete configuration state"), and SCO:236 "each
  replacing the whole list".
- Proposed citation: `SCO:236,373,459; docs/rfds/session-config-options.mdx:45; schema#ConfigOptionUpdate`. Tier stays
  CAPABILITY (the completeness rule is unchanged). Text and test are unchanged. The docstring's "vacuous when none
  observed" stays right for 206. Not observing one becomes 211's ADVISORY concern.
- `spec-impact --fix` will shift line numbers. It cannot know that 375-379 is now a different rule, so set this
  citation by hand.

## New requirements

All config rows follow the existing pattern: `Tier.CAPABILITY`, `capability="inferred:configOptions"`
(documentation-only), and SKIP "session/new returned no configOptions". Next free number is 207. 205 stays unused
for historical clarity.

### ACP-CONFIG-207: unknown `configId` is rejected with `-32602`
- Tier: CAPABILITY (MUST, conditional on advertising config options). Citation `SCO:234; docs/protocol/v2/draft/error.mdx:48;
  schema#SetSessionConfigOptionRequest`.
- Text: "`session/set_config_option` naming a `configId` the session did not advertise is rejected with `-32602`."
- Observe: after `session/new` with configOptions, send `{sessionId, configId: "_tck_unknown_config", type: "id",
  value: "x"}` and expect a JSON-RPC error with `code == -32602`.
- Fixture: `config_set_unknown_id_accepted.py`, which answers an unknown configId with success (the unchanged list). That
  trips only 207. Note the current `_base.py` (lines 453-465) already rejects unknown ids with `-32602`, so the baseline
  passes.

### ACP-CONFIG-208: invalid value is rejected with `-32602`
- Tier: CAPABILITY. Citation `SCO:234,264-273; docs/protocol/v2/draft/error.mdx:48;
  schema#SetSessionConfigOptionRequest` (incl. its `other` branch description "MUST reject ... a value type they do
  not support with `-32602`").
- Text: "`session/set_config_option` for an advertised option with an invalid value is rejected with `-32602`: a
  `select` value not among its declared values, a value `type` that doesn't match the option (`boolean` for a select,
  `id` for a boolean), or an unsupported value `type`."
- Observe (parametrize, each on a fresh session or with 209's restore check in between):
  (a) select option, `type: "id", value: "_tck_not_a_value"`;
  (b) select option, `type: "boolean", value: true`;
  (c) boolean option (if any), `type: "id", value: "x"`;
  (d) any option, `type: "_tck_unsupported", value: 1` (`_`-prefixed per the TCK's probe convention; schema-valid via
  the `other` branch).
  Each must yield `code == -32602`. Skip sub-cases whose option type is absent.
- Fixture: `config_set_invalid_value_wrong_code.py`, which rejects invalid values with `-32603` and leaves state
  untouched. That trips only 208.
- **The baseline must change:** `_base.py::_handle_set_config_option` currently stores any value for a known
  `configId` and replies success. The conforming baseline would FAIL 208 and 209. It must validate `type` against the
  option type and select membership, then answer `-32602` without mutating.

### ACP-CONFIG-209: a rejected set leaves the configuration unchanged
- Tier: CAPABILITY. Citation `SCO:234; schema#SetSessionConfigOptionRequest`.
- Text: "After `session/set_config_option` is rejected, the session's configuration is unchanged."
- Observe: after each 208 rejection, send a *valid no-op* set (the same option, to its pre-probe `currentValue`) and
  compare the returned list's `(configId, currentValue)` pairs with the pre-probe list. Excuse (SKIP) the check if a
  `config_option_update` arrived between probe and follow-up, since the agent may change config on its own (SCO:459-463).
  Judge only when the probe actually got an error (if it got success, 208 already FAILed).
- Fixture: `config_set_invalid_value_mutates.py`, which stores the invalid value and then answers `-32602`. That trips
  only 209.
- Merge option: fold into 208 as a second assertion. Kept separate so that "wrong code" and "state corrupted" are
  reported distinctly.

### ACP-CONFIG-210: select values are unique within an option, including across groups
- Tier: CAPABILITY. Citation `SCO:128-130; schema#SessionConfigSelect` (`options` description).
- Text: "Within one `select` option, every declared `value` is unique, across groups as well."
- Observe: passive, on `session/new`'s `configOptions` (and optionally every other carrier). Flatten with the
  existing `_flatten_select_values` and compare `len` with `len(set(...))`. Not schema-enforced.
- Fixture: `config_duplicate_select_values.py`, a grouped select with `normal` in two groups and `currentValue: normal`
  (so 204 still passes). That trips only 210.

### ACP-CONFIG-211 (ADVISORY): a state-changing set is accompanied by `config_option_update`
- Tier: ADVISORY ("Agents **SHOULD** send ..."). Citation `SCO:375; schema#ConfigOptionUpdate`.
- Text: "When a `session/set_config_option` changes configuration state, the agent sends a `config_option_update`
  on the requesting connection."
- Observe: reuse 206's flow, which already records `acp_tck_config_option_update_observed`. Judge only when the
  response's list differs from the pre-set list (if the agent adjusted back to the old value, nothing changed, so
  SKIP). FAIL (advisory) if no update is seen before the response or within the quiet drain after it.
- Scope: SCO:375 says "on each connection where the session is active". Only the requesting connection is judged.
  Multi-connection fan-out goes to ledger L6.
- **The baseline must change:** `_base.py` sends no `config_option_update`. The conforming baseline should emit one
  *before* the response. That also makes 206 non-vacuous for the fixtures. The fixture for this row is the old
  behaviour: `config_set_no_update_notification.py`.

### ACP-CONFIG-212 (ADVISORY): the duplicate precedes the response
- Tier: ADVISORY ("Agents **SHOULD** send that duplicate before the response and notifications for subsequent changes
  after it"). Citation `SCO:377-379`.
- Text: "The `config_option_update` duplicating a `session/set_config_option` change arrives before that request's
  response."
- Observe: transcript order. Judge only when 211 saw an update. FAIL (advisory) if the only update matching the
  response's list arrives after the response. An update after the response whose list differs from the response could
  be a legitimate "subsequent change", so don't judge it.
- Fixture: `config_update_after_response.py`. That trips only 212.
- Merge option: one ADVISORY row "sends a duplicate update, before the response" covering 211 and 212.

### ACP-COMMANDS-201 (new area; pick the area token, e.g. `COMMANDS`/`CMD`)
- Tier: CAPABILITY with documentation-only `capability="inferred:availableCommands"`. Same encoding as config:
  no capability marker exists, and support is inferred from the agent advertising any command. SKIP when no
  `availableCommands` (setup response) and no `available_commands_update` is observed.
- Text: "Every command the agent advertises (in a setup response's `availableCommands` or an
  `available_commands_update`) validates as `AvailableCommand` (it carries a `type` discriminator, `\"command\"` or
  `_`-prefixed custom), and within each list every `name` contains no whitespace and is unique."
- Citation: `SC:12,37-43,87-100,110; schema#AvailableCommand; schema#Command; schema#AvailableCommandsUpdate`.
- Observe: `session/new` result plus a quiet drain after it (agents commonly push `available_commands_update` right
  after setup), and optionally the first prompt turn. Validate each item against `#/$defs/AvailableCommand`. Check `not
  re.search(r"\s", name)` and uniqueness per list.
- Fixtures: `commands_name_with_whitespace.py` (`"name": "web search"`, `type: "command"`). Optionally
  `commands_duplicate_names.py`. Add a typed command to `conforming_full.py` (`_base.py` needs an `available_commands`
  param) so the row PASSes rather than SKIPs in the conforming run.
- Leading `/`: SC:98 says "without the leading `/`" with no RFC keyword. Do not FAIL on it. At most record it.

## Ledger: proposed deliberate non-requirements (`[[not_requirement]]` in `spec-tracker/maps/v2.toml`)

| # | citation | statement | reason |
|---|----------|-----------|--------|
| L1 | `docs/protocol/v2/draft/slash-commands.mdx:12 @ 3961af94fa62` | An Agent with commands MUST include them in `availableCommands` in setup responses. | Unobservable: the client cannot know the agent "has" commands, and SC:47 lets it announce commands "not included in the response" later, so a late `available_commands_update` is not evidence of a violation. (The config-options half of SS:108 is observable; see CONFIG-203.) |
| L2 | `docs/protocol/v2/draft/slash-commands.mdx:147-160 @ 3961af94fa62` | Command invocation semantics: a prompt whose first text block is `/<name>` invokes it, and local command handling MUST report an active state then `idle`. | Unsafe: invoking an arbitrary advertised command (`/compact`, `/clear`, `/logout` ...) has side effects the TCK can't predict. The generic turn lifecycle is already judged by the STATE rows. |
| L3 | `docs/protocol/v2/draft/slash-commands.mdx:147 @ 3961af94fa62` | Clients recognizing a command SHOULD require the name to be followed by whitespace or end of the text block. | Client-side rule (the headline of #2646, so someone may expect it tested). |
| L4 | `docs/protocol/v2/draft/session-config-options.mdx:222 @ 3961af94fa62` | Agents MUST be able to operate with each option's `currentValue` even if the Client doesn't support, display, or recognize the option. | Unobservable: it's internal agent behaviour, and a TCK turn that ignores config options cannot distinguish "operates with the default" from anything else. |
| L5 | `docs/protocol/v2/draft/session-config-options.mdx:236 @ 3961af94fa62` | The set response may report a `currentValue` different from the requested one. | Not a requirement: the spec explicitly permits it. This is why the set-value-reflection check (formerly planned as ACP-CONFIG-205) is recorded via `acp_tck_config_option_echoes_sent_value` and never asserted. |
| L6 | `docs/protocol/v2/draft/session-config-options.mdx:375 @ 3961af94fa62` | `config_option_update` SHOULD be sent on *each* connection where the session is active. | Out of scope: whether a session can be active on several connections is the agent's choice (SS:53), so fan-out to non-requesting connections isn't judged. ACP-CONFIG-211 covers the requesting connection. |

Considered and not ledgered: SCO:131 "Clients SHOULD hide a group that ends up empty" (pure client UI), SCO:234
"Clients MUST NOT call it otherwise and MUST only send an advertised `configId`" (client rule. See D3.), SCO:236
"whether a change during foreground work applies to it is up to the Agent" (pure permission).

## Decisions needed

- **D1 (CONFIG-203):** tighten to FAIL a resume that omits `configOptions` when that session's own `session/new`
  advertised them (SS:108 MUST), or keep "when present". *Recommend tightening, judged only against the resumed
  session's own `session/new` response, SKIP otherwise.* Coordinate with the session-setup researcher (SS:108 also
  covers commands, see L1).
- **D2 (attribution of B5 failures):** `_new_session_full_result` (`test_session_config.py:46-57`) schema-validates the
  **whole** `session/new` result *before* checking whether `configOptions` is present. After the refresh, a real agent
  whose commands lack `type` (anything built on a pre-alpha.10 SDK) FAILs ACP-CONFIG-201/202/204/206 (and 203's first
  step), even with no `configOptions` at all, instead of SKIPping. The same violation is already FAILed under
  ACP-SESSION-001 (`test_session.py:33`), ACP-SCHEMA-001 (`test_initialize.py`, whole output), ACP-PROMPT-205
  (in-turn updates), and RESUME-201. *Recommend:* in the config tests, SKIP on absent `configOptions` first, then
  validate only the `configOptions` items against `#/$defs/SessionConfigOption` rather than the whole result. This
  pre-existed, but B5 makes it likely against real agents.
- **D3 (probe legitimacy):** ACP-CONFIG-207/208 make the TCK deliberately break client MUSTs (SCO:234 "MUST only send
  an advertised `configId`", SCO:270-272 value "MUST be one of the values ... MUST be a boolean"). *Recommend
  accepting:* the agent-side MUST in the same sentence (SCO:234) exists precisely to handle such requests. Use
  `_tck_`-prefixed ids and values so no real option can collide.
- **D4 (tiers):** 207-210 as CAPABILITY (explicit MUST, conditional on advertised config options); 211/212 as ADVISORY
  (SHOULD); COMMANDS-201 as CAPABILITY (explicit MUST, conditional on advertised commands). Confirm the
  `inferred:availableCommands` encoding.

## Spec-map notes (`spec-tracker/maps/v2.toml`)

Neither doc is a core doc (the map's `[[core_doc]]` entries don't list them), so the sentence-cased headings ("Initial
state", "Setting a config option", "From the Client", "From the Agent", "Default values and graceful degradation",
"Option categories", "Option ordering", "Grouped select options", "Boolean config options"; slash-commands headings
were already sentence-case) need no remap. **Don't make either core.** initialization.mdx:239 and the SCO references
in session-setup link to SCO explicitly. error.mdx:48 restates the `-32602` rule in its own words and is consistent.

## Testability notes

- Everything proposed is observable from one client connection. 207-209 need one extra request each (plus one no-op
  restore for 209). 210 and COMMANDS-201 are passive.
- Conforming vs non-conforming for 208: an agent built on a typed SDK will typically fail deserialization of a
  mismatched `type`/`value` pair. Whether its SDK maps that to `-32602` is SDK behaviour I did not check (hypothesis
  only). The spec requires `-32602` either way.
- 211/212 depend on the quiet-drain window (`quiet_period`). An agent that notifies late beyond it reads as "no
  update" (advisory FAIL), and that's acceptable for an ADVISORY row.

## Discrepancies

- Spec doc vs schema: none. Every new MUST in SCO/SC is mirrored in a `$def` description, and B7's `minItems` matches
  the "at least one value"/"each group" text.
- Internal tension in SC: SC:12 "An Agent with commands **MUST** include them ... in setup responses" vs SC:47 "After
  session setup, the Agent **MAY** announce commands that were not included in the response". Presumably this
  reconciles as "commands available at setup time". That's my reading, not stated. It's why L1 is a ledger entry.
- Registry vs spec: ACP-CONFIG-201's text asserts "the schema sets no minimum length", which is now false. ACP-CONFIG-204
  cites a removed sentence as its basis.

## Open questions / follow-ups (for other owners)

- **ACP-ENUM-201 site list** (extensibility owner): four open-enum sites in these docs are not in its curated list:
  `SessionConfigOption.type` (SCO:228 "Custom option types **MUST** begin with `_`", pre-existing),
  `SessionConfigOptionCategory` (SCO:197), `AvailableCommand.type` (SC:110, **new** with B5), and
  `AvailableCommandInput.type` (SC:120). Add them there rather than as per-doc rows.
- **`-32002` for `session/set_config_option` on an inactive/unknown session** (error.mdx:54-56, SS:51): new text, owned
  by whoever audits error.mdx/session-setup.
- **`configId` uniqueness within `configOptions`**: SCO:96 "Unique identifier for this configuration option" has no RFC
  keyword. If wanted, it would be INFORMATIONAL/ADVISORY at most. Not proposed.
- `_base.py` changes implied by 208/209/211 (validate set values, emit `config_option_update` before the response, an
  `available_commands` param) touch the shared baseline every v2 fixture inherits. The programmer slice should re-run
  `tests/v2/test_cli.py` in full, not only the config subset.
