# v1 impact: session config options, session modes, slash commands (`beac4ba96190` -> `3961af94fa62`)

**Sources checked:** `agent-client-protocol` checkout `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2` @ `3961af94fa62d2386d993cadf1afc8b146fc799a` (target), diffed against `beac4ba96190018e9f6d82e148ff275084c5aa3e` (base). Read via `git show`/`git diff` only, no pull. TCK repo @ `200baba` (registry `src/tck/v1/requirements.py`, test `src/tck/v1/conformance/test_session_config.py`). I did not consult the reference SDKs: no affected requirement depends on runtime behavior the spec leaves open.
**Confidence:** high. Every doc hunk and every relevant `$def` was diffed in full. The only judgment call is the low-stakes tier note on ACP-CONFIG-001.

## Answer

Nothing in these three docs, or in the `SessionConfigOption*` and mode `$defs`, changes what an agent must do on the wire. All 5 registry rows (ACP-MODES-001/002, ACP-CONFIG-001/002/003) keep their text, tier, capability gate, and test assertions. ACP-MODES-001/002 are unchanged; their line numbers did not move. ACP-CONFIG-001/002/003 need citation-only updates, and `spec-impact` will put most of those under "Needs review" because the cited lines fall inside changed hunks. The one normative rewording is "Default values". The old "Agents **MUST** always provide a default value" became "`currentValue` is the value the Agent uses until the Client changes it. Agents **MUST** be able to operate with it". ACP-CONFIG-001 cites that line, so its citation moves (242 -> 245). The new MUST is not observable from the client side, so I propose one ledger entry and no new requirement. slash-commands.mdx changed one prose sentence, and no registry row cites it. Schema: all cited `$defs` still exist at target. They changed only in description links and wording, with no structural change.

## Summary table

| Id | Classification | Note |
|----|----------------|------|
| ACP-MODES-001 | unchanged | Cited lines `session-modes.mdx:17,49-75` have the same content and the same line numbers. `SessionModeState`/`SessionMode` changed only their description links. |
| ACP-MODES-002 | unchanged | `session-modes.mdx:83-122` keeps the same lines. Line 83 changed only the link anchor (`#session%2Fset-mode` -> `#session%2Fset_mode`). The `currentModeId` example is still at 117-119. `spec-impact` lists the overlap, but nothing needs to change. |
| ACP-CONFIG-001 | citation-only change | `session-config-options.mdx:118-127,242` -> `118-130,245`. Line 245 is the reworded "Default values" MUST, so its meaning shifted (see details). The test still matches. Low-stakes tier note: keep CAPABILITY. |
| ACP-CONFIG-002 | citation-only change | `301,328-333` -> `304,373-377`. The Note was reworded with the same meaning. Optional: fix the registry text's "stated as a MUST twice" claim (inaccurate before and after). |
| ACP-CONFIG-003 | citation-only change | `session-config-options.mdx:204-206` -> `207-209` (pure shift). `initialization.mdx:172-181` -> `189-198` (the new "Plan operations" section was inserted above it, and base line 172 sits inside hunk `-172,1 +172,18`, so it goes to Needs review). Text unchanged. |
| (new ledger) | new deliberate non-requirement | `session-config-options.mdx:245-249`: "Agents MUST be able to operate with each option's `currentValue`…". Not observable. |
| (none) | no new requirement | No new agent-side rule a client could observe in these three docs. |

## Requirements

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| 1 | Agent MAY return `configOptions` during session setup | MAY (support inferred) | `docs/protocol/v1/draft/session-config-options.mdx:17` @ 3961af94fa62 |
| 2 | `currentValue` required; select = value ID, boolean = bool | schema-required (ACP-CONFIG-001) | `session-config-options.mdx:118-121`; `schema/v1/schema.unstable.json#/$defs/SessionConfigSelect`, `#/$defs/SessionConfigBoolean` |
| 3 | `options` required for select, omitted for boolean; flat or grouped, never mixed | schema-required | `session-config-options.mdx:123-130`; `#/$defs/SessionConfigSelectOptions` |
| 4 | Agents MUST NOT send `type:"boolean"` options unless the client advertised `session.configOptions.boolean` | MUST (ACP-CONFIG-003) | `session-config-options.mdx:207-209`; `initialization.mdx:189-198` |
| 5 | `currentValue` is what the agent uses until changed; agents MUST be able to operate with it | MUST, unobservable (ledger) | `session-config-options.mdx:245-249` |
| 6 | `session/set_config_option` response MUST carry the complete option list | MUST (ACP-CONFIG-002) | `session-config-options.mdx:304,373-377`; `#/$defs/SetSessionConfigOptionResponse` |
| 7 | Agent MAY return `modes`; `currentModeId`/`availableModes` required | MAY + schema (ACP-MODES-001) | `session-modes.mdx:17,49-75` |
| 8 | `session/set_mode`; `current_mode_update` uses `currentModeId` | schema (ACP-MODES-002) | `session-modes.mdx:83-122`; `#/$defs/CurrentModeUpdate` |
| 9 | Agent MAY send `available_commands_update` after session creation | MAY, no registry row | `slash-commands.mdx:10` |

## Details

### Schema (`schema/v1/schema.unstable.json`, base vs target, structural diff per `$def`)

- Identical at target: `SessionModeId`, `SessionConfigId`, `SessionConfigOptionCategory`, `SessionConfigValueId`, `SessionConfigSelectOptions`, `SessionConfigGroupId`, `SessionConfigSelect`, `SessionConfigBoolean`, `AvailableCommandInput`.
- Changed only in the `_meta` / "See protocol docs" link (`/protocol/...` -> `/protocol/v1/draft/...`): `SessionModeState`, `SessionMode`, `SessionConfigOption`, `SessionConfigSelectOption`, `SessionConfigSelectGroup`, `SetSessionModeRequest`, `SetSessionModeResponse`, `SetSessionConfigOptionResponse`, `CurrentModeUpdate`, `ConfigOptionUpdate`, `SessionConfigOptionsCapabilities`, `BooleanConfigOptionCapabilities`, `AvailableCommand`, `UnstructuredCommandInput`, `AvailableCommandsUpdate`.
- `SetSessionConfigOptionRequest`: link change, plus the `value_id` variant description changed from "A [`SessionConfigValueId`] string value" to "A `SessionConfigValueId` string value" (markup only).
- `NewSessionResponse`/`LoadSessionResponse`/`ResumeSessionResponse`/`ForkSessionResponse` `.properties.modes`: description link only. `.properties.configOptions`: identical.
- No `$def` was removed. Every pointer the 5 rows cite still resolves: `SessionModeState`, `SessionMode`, `SetSessionModeRequest/Response`, `CurrentModeUpdate`, `SessionConfigOption`, `SessionConfigOption/oneOf/1` (still the `boolean` variant), `SessionConfigSelect`, `SessionConfigBoolean`, `SetSessionConfigOptionRequest/Response`. The inventory's "$ref closure: `SessionConfigSelect` -> `SessionConfigSelectGroup`, `SessionConfigSelectOption`" entry comes from those two defs' link-only changes.
- The vendored-schema refresh therefore has no effect on validation of config/mode traffic.

### `session-config-options.mdx` (whole doc read at target; every hunk reviewed)

Hunks, by kind:
- Type names in docs aligned to schema names (`ConfigOption` -> `SessionConfigOption`, `ConfigOptionValue` -> `SessionConfigSelectOption`, `ConfigOptionGroup` -> `SessionConfigSelectGroup`, `ConfigOptionCategory` -> `SessionConfigOptionCategory`, and `type`'s doc type `ConfigOptionType` -> `string`), at lines 87, 93, 107, 112, 123-126, 132, 168-170. No change to field requiredness or meaning.
- Headings sentence-cased (15, 146, 174, 211, 233, 243, 253, 460). Mintlify slugs are lowercase, so anchors like `#boolean-config-options` are unchanged.
- Examples expanded: the set response (306-371) and the `config_option_update` notification (383-452) now show complete option objects with `description`/`category`/`options` and a third `context_size` (`category: "model_config"`) option instead of `"options": [...]` placeholders. Illustrative only.
- Note at 373-377 reworded. Before: "This allows Agents to reflect dependent changes. For example, if changing the model affects available reasoning options, or if an option's available values change based on another selection." After: "so Agents can report dependent changes. For example, changing the model may change the available reasoning options." The same rationale remains, and it still supports ACP-CONFIG-002's subset (not set-equality) check.
- **Normative rewording, line 245** (base 242):
  - Base: "Agents **MUST** always provide a default value for every configuration option. This ensures the Agent can operate correctly even if: …"
  - Target: "Every configuration option's `currentValue` is the value the Agent uses until the Client changes it. Agents **MUST** be able to operate with it, even if: …"
  - Line 251: "The Agent will continue using its default value" -> "The Agent keeps using its `currentValue`."
  - Effect: the "default value" concept now explicitly *is* `currentValue`. The MUST moved from "provide a value", which the schema's `required: ["currentValue"]` already covered, to "be able to operate with it", which is internal agent behavior.

Unchanged normative statements still in force (listed for completeness; none is new): MAY return options (17); client SHOULD respect ordering (88-90); boolean MUST NOT (207-209); categories MUST NOT be required for correctness / clients MUST handle unknown categories (216-217, client-side); `_`-prefixed custom categories (220); agents SHOULD order by priority (235); client SHOULD ignore unrecognized `type` (251); options can change at any point, even mid-generation (255); set response MUST be the complete list (304); `config_option_update` "also contains the complete configuration state" (454, descriptive, no keyword); agents SHOULD send both `configOptions` and `modes` and SHOULD keep them in sync (462-471).

### `session-modes.mdx`

The only hunk is line 83, where the link anchor changed `schema#session%2Fset-mode` -> `schema#session%2Fset_mode`. No lines were inserted or removed, so every cited line number is still valid. Lines 117-119 still show `"sessionUpdate": "current_mode_update", "currentModeId": "code"`, so the ACP-MODES-002 registry text's reference to `session-modes.mdx:117-119` stays correct.

### `slash-commands.mdx`

The only hunk is line 73 (Dynamic updates), rewording "This allows commands to be added…" to "Agents can use this to add commands…". There is no RFC keyword, and the doc's only normative word is the pre-existing MAY at line 10. No registry row cites this doc. The TCK only mentions `available_commands_update` as an out-of-turn update that it ignores (`src/tck/v1/requirements.py:366`, `src/tck/v1/conformance/_helpers.py:189`), and that is unaffected.

### Per-row detail

**ACP-CONFIG-001 (citation-only; low-stakes tier note).**
- Old citation: `session-config-options.mdx:118-127,242`. New: `session-config-options.mdx:118-130,245`. The `$defs` citations are unchanged.
- 118-127 -> 118-130 because the `options` ResponseField grew from 5 to 8 lines (hunk `-123,1 +123,4`). 242 -> 245 is the reworded MUST above. Both overlap changed hunks, so expect `spec-impact --fix` to list them under Needs review rather than remap them silently.
- Test (`test_session_config.py:159-187`): checks `id`/`name` present, `boolean` -> bool `currentValue`, otherwise `currentValue` is in the flattened `options`. This still matches the target text: 118-121 says select `currentValue` is "a string value ID", and 127 says `options` are "the available values for a `select` option". No change needed.
- Tier note (low stakes; I recommend no change): the base row's "MUST always provide a default value" was the nearest keyword. At target that MUST is about operating with `currentValue`. The "`currentValue` is one of `options`" membership check was never a stated MUST, before or after; it is inferred from the field descriptions, and the registry text already says so for MODES-001 ("derived from the field descriptions, not a stated MUST"). The new wording arguably strengthens the basis: `currentValue` is "the value the Agent uses", and for a select the usable values are `options`. **Recommendation: keep `Tier.CAPABILITY`, `inferred:configOptions`.** Optionally add "(derived from field descriptions, not a stated MUST)" to the row text, to match MODES-001.

**ACP-CONFIG-002 (citation-only).**
- Old citation: `session-config-options.mdx:301,328-333`. New: `session-config-options.mdx:304,373-377`.
- 301 -> 304 is a plain +3 shift; the MUST line's text is unchanged. 328-333 -> 373-377 is the Note, reworded with the same meaning, and it overlaps hunk `-329,4 +374,3` (Needs review).
- Test (`test_session_config.py:190-266`) still matches. The subset rationale comment ("dependent changes … may *add* options") is still supported by the Note.
- Optional text fix: the row says "stated as a MUST twice in the docs". At both base and target there is one MUST (304), restated as a non-keyword "always contains the **complete** configuration state" Note (373-377). Suggest "stated as a MUST at line 304 and restated in the Note". This is not a behavior change.

**ACP-CONFIG-003 (citation-only).**
- `session-config-options.mdx:204-206` -> `207-209`: a pure shift with identical text.
- `initialization.mdx:172-181` -> `189-198`: the heading "Boolean Config Options" became "Boolean config options" and moved down 17 lines because the new "Plan operations" client-capability section was inserted at 172-187. The ParamField text (195-197) is identical.
- `#/$defs/SessionConfigOption/oneOf/1` is still `{type: const "boolean"} + SessionConfigBoolean`.
- Tier MANDATORY and gate `None` are unchanged. The test (`test_session_config.py:269-334`) still matches.

**ACP-MODES-001 / ACP-MODES-002: unchanged.** See the summary table. The tests do not change.

### New deliberate non-requirement (ledger)

```toml
[[not_requirement]]
citation = "docs/protocol/v1/draft/session-config-options.mdx:245-249 @ 3961af94fa62"
statement = "Every config option's currentValue is the value the Agent uses until the Client changes it, and Agents MUST be able to operate with it even if the Client doesn't support, display, or recognize the option."
reason = "not observable: concerns the agent's internal operation. The observable part, currentValue being present and type-valid, is already checked by schema validation and ACP-CONFIG-001."
```

## Testability notes

- None of the 5 tests or the fixtures (`mode_update_uses_modeId.py`, `config_partial_list.py`, `boolean_option_unadvertised.py`, `boolean_option_on_set.py`, `conforming_full.py`) need changes. `tests/v1/test_cli.py`'s expected FAIL/PASS sets for these ids stay as they are.
- Only `requirements.py` citation strings change (and the optional text tweaks to CONFIG-001/002).

## Discrepancies

- None introduced by this update. The docs now use schema `$def` names.
- Pre-existing, unchanged: docs line 112 types `type` as a plain `string`, and line 251 tells clients to ignore unrecognized types, which implies future types. But `#/$defs/SessionConfigOption` is a closed `oneOf` (`select` | `boolean`), and `src/tck/v1/validation.py` has no carve-out for it. So a v1 agent that sends a future/unknown `type` fails schema validation in the TCK, and `test_config_options_current_values_are_valid` would treat it as a select and fail the membership check. This is not part of this diff; listed for awareness.

## Open questions

1. **Route to the `error.mdx` owner (new doc, not mine):** `docs/protocol/v1/draft/error.mdx:47` says an unknown `configId` or value in `session/set_config_option`, and an unknown mode in `session/set_mode`, "get `-32602`" (declarative, no RFC keyword). `error.mdx:53-55` says the agent **SHOULD** answer `-32002` with `data.sessionId` for `session/set_mode` and `session/set_config_option` on an unknown session. A client can observe both. They would naturally be ADVISORY rows gated on inferred `modes`/`configOptions` support, or added to a general unknown-session row. I have not proposed ids, to avoid colliding with the `error.mdx` report.
2. **Pre-existing, untouched by this diff, not ledgered** (the v1 ledger is empty). The orchestrator should decide whether this update should backfill them:
   - "Agents SHOULD keep both [`configOptions` and `modes`] in sync" (`session-config-options.mdx:471`). Partially observable: when both are present with a `category:"mode"` option, after `session/set_mode` check the next config state.
   - "Agents SHOULD send both" (462). "Agents SHOULD place higher-priority options first" (235), which is not observable.
   - `config_option_update` "also contains the complete configuration state" (454). Observable, but there is no keyword and the TCK cannot trigger it.
3. `security.mdx:27` (Clients SHOULD keep agent slash commands distinguishable) is client-side and belongs to the security report (`.agents/research/impact-v1-security.md`).
4. Ambiguity carried over from base: neither the old nor the new Note says whether a dependent change may *remove* an option id. ACP-CONFIG-002 asserts that previously advertised ids are kept. That reading is consistent with "complete list" but not stated. It is unchanged by this update.
