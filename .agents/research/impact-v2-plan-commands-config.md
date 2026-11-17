# Impact (v2): `agent-plan.mdx`, `slash-commands.mdx`, `session-config-options.mdx`, 3961af94 -> 3ea94133

**Sources checked:** spec `3ea94133` (read with `git show 3ea94133:<path>` in `../agent-client-protocol-2`. Its HEAD
`6ace4f6a` is one commit later and touches only `Diff.changes` and `rfds/v2/diff-file-states.mdx`). Base `3961af94`
for the line maps. Files: the three docs (whole), their diffs, `initialization.mdx:248-268,312-313,348-353,413-425`,
`session-setup.mdx:45-56,98-110,594-597`, `error.mdx:40-72`, `content.mdx` (skill block), `docs/rfds/session-options.mdx`
(Draft RFD, discrepancy scan only), `docs/docs.json` (stages), `schema/v2/schema{,.unstable}.json` (`AvailableCommand`,
`Skill`, `CommandsCapabilities`, `ClientSessionCapabilities`, `PlanMarkdown`, `PlanUpdateContent`, `AbsolutePath`,
`SessionConfigOptionCategory`, `SessionOptions{Request,Response,Capabilities}`, `InitialSessionConfigOption`,
`{New,Resume,Fork}SessionRequest.configOptions`). TCK: `src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`,
`src/tck/v2/protocol.py`, `open_enums.py`, `conformance/test_slash_commands.py`, `test_patches.py`,
`test_session_config.py`, `_helpers.py`, and the v2 fixtures. Sibling reports `impact-v2-extensibility.md`,
`impact-v2-transports-security-content.md`, `impact-v2-overview-error.md`, `impact-rfd-plan-operations.md`,
`impact-v1-content-plan-commands.md`, `impact-v1-config-options.md` (read so the ids can be aligned).
I did not consult the SDKs: every proposed row rests on explicit doc or schema text.
**Confidence:** high for the classifications and line maps (checked line by line against both revisions). Medium for
the `session/options` probe designs and the tier choices listed under Decisions.

RFD stages at the target: `agent-skills`, `session-options` and `speed-config-category` are **Draft**
(`docs.json:234-237`, Draft group at `:200`). The docs state every rule below, so none of them is cited.
`plan-operations` is **Preview**, and its rules match `agent-plan.mdx` (see `impact-rfd-plan-operations.md`).

Line maps (base -> target). **agent-plan:** 1-91 unchanged. Base 99-119 (File plans) was replaced by target 100-111.
Base >= 120 maps to -8. **slash-commands:** 1-44 unchanged. Base 45-90 maps to +2, base 95-162 to +3, and target
166-259 is new. **session-config-options:** 1-198 unchanged. The table is now 199-205. New lines are 209-210 and
213-224. Base 210-463 maps to +15, and target 479-585 is new.

## agent-plan.mdx

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-PATCH-205 | citation-only | `agent-plan.mdx:139` (was 147) | The rule is verbatim. Also update the docstring at `test_patches.py:169`. |
| ACP-ENUM-201 (agent-plan part) | citation-only, plus a **code change** | `agent-plan.mdx:137,156,168` (was 145,164,176) | `protocol.py:113` `PLAN_CONTENT_TYPE` must drop `"file"`. `tests/v2/test_validation.py:260` forces this after the re-vendor, because `PlanUpdateContent` now defines only `items` and `markdown`. Consequence: an agent that still sends `type: "file"` now FAILs ENUM-201 (a non-underscore unknown value, `:137`). I agree with the extensibility report's Decision 3: accept this. No v2 fixture sends file plans (I grepped). |
| ledger `agent-plan.mdx:119` "Plan file URIs MUST be absolute" | **removed** | none | `PlanFile` and the rule are gone from the docs and from both v2 schemas. Delete the entry. Its successor is the new `path` rule (ACP-PLAN-003 below). |
| ledger `agent-plan.mdx:139` (`plan_removed` SHOULD) | citation-only | `:131` | The reason is spec-based. It is fine. |
| ledger `agent-plan.mdx:186` (complete item list) | citation-only | `:178` | The reason is fine. |

## slash-commands.mdx

| id / ledger citation | classification | target citation | note |
|---|---|---|---|
| ACP-RESUME-210 | unchanged (for this doc) | `slash-commands.mdx:12` | Line 12 is verbatim. The `session-setup.mdx` lines in this row belong to that doc's researcher. |
| ACP-COMMANDS-201 | **changed text and citation** | `slash-commands.mdx:12,37-43,91-113,186-192` | The row text says "`type` discriminator (`command`, or a `_`-prefixed custom type)". It must add the unstable `skill` (`:93,96-97`). The uniqueness clause becomes "unique within the list, across commands and skills" (`:187-188`). Add `schema/v2/schema.unstable.json#/$defs/Skill`. The test logic needs no change: it validates against `AvailableCommand`, which now includes the `Skill` branch, and its `seen` set already spans the whole list. Proposed scope change: also run the scan on a connection that advertises `session.commands.skill: {}`. That is the only connection where skill entries may legally appear, so it is the only way to exercise the "across commands and skills" rule (Decision 3). Fixture docstrings citing `:98-100` become `:101-103`, and `:110` becomes `:113`. |
| ACP-ENUM-201 (slash-commands part) | citation-only, plus a **code change** | `slash-commands.mdx:113` (was 110) | `AVAILABLE_COMMAND_TYPE` must add `"skill"` (forced by `test_validation.py:264`). After that, ENUM-201 no longer flags a `skill` entry, so the new skill-gate row is the only check of `:171`. |
| ledger `slash-commands.mdx:12; session-setup.mdx:108` | citation-only | `:12` is unchanged | In the reason, "slash-commands.mdx:47" becomes `:49`. The `session-setup.mdx` line belongs to that researcher. |
| ledger `slash-commands.mdx:149,157-160` | citation-only | `:152,160-163` | The reason ("Unsafe") still holds. Line 150 changed its wording to "invokes a `command` entry", but this entry does not cite it. |

**Dedupe with `impact-v2-transports-security-content.md`** (the coordinator asked for this):
- **PROMPTCAP-201 extension (unadvertised `skill` block -> `-32602`, not inserted).** `slash-commands.mdx:255` states
  the same rule ("Clients MUST NOT send a `skill` block that the Agent's capability doesn't allow. The Agent MUST
  reject ... with `-32602` and without inserting it"). No change. Add `slash-commands.mdx:255` to its citation, as
  the sibling already does.
- **`ACP-PROMPTCAP-202` (unresolvable `skill` name -> `-32602`).** `:253,255` match it, and so does its test design.
  Putting the block first satisfies the position rule (`:238`), so a conforming agent can only be rejecting the name.
  No change. I do not propose a duplicate. One residue that 202 cannot reach is the position/count rule; see the
  new ledger entry below.
- **ADVISORY "skill blocks only in user messages".** `:256` ("The block is part of the inserted user message") is
  consistent with it. No change.
- **Ledger "agent treats a `skill` block as an invocation and echoes it in `user_message`/replay"**
  (`slash-commands.mdx:254,256`). I agree, and I record no duplicate. `:256`'s replay MAY (replace the block with
  text for a client without `commands.skill`) is a MAY and needs no entry.

## session-config-options.mdx

| id / ledger citation | classification | target citation | note |
|---|---|---|---|
| ACP-CONFIG-201 | unchanged | `:93-154` | `speed` joined `SessionConfigOptionCategory`, but the open `other` branch already accepted it. |
| ACP-CONFIG-001 | unchanged | `:116-119,125-133` | |
| ACP-CONFIG-210 | unchanged | `:125-133` | Fixture `config_duplicate_select_values.py` (`:128-130`) is unchanged. |
| ACP-CONFIG-002 | citation-only | `:249,251,306,382-386` | Its `initialization.mdx:239-240` is now `:312-313` (that doc's researcher should confirm). |
| ACP-CONFIG-206 | citation-only | `:251,388,474` | |
| ACP-CONFIG-207 | citation-only | `:249` | |
| ACP-CONFIG-208 | citation-only | `:249,279-288` | |
| ACP-CONFIG-209 | citation-only | `:249,474-478` | Also update `test_session_config.py:442`. |
| ACP-CONFIG-211 | citation-only | `:390` | |
| ACP-CONFIG-212 | citation-only | `:392-394` | |
| docstrings | citation-only | | `test_session_config.py:14` (`:236` becomes `:251`). Fixtures and `_base.py:881,914`: `:234` becomes `:249`, `:375(-379)` becomes `:390(-394)`. |
| ledger `:222` (operate with `currentValue`) | citation-only | `:237` | The reason is fine. |
| ledger `:375` (fan-out to every connection) | citation-only; **reason flagged** | `:390` | The reason says "fan-out to connections other than the requesting one is not judged". That reads as a TCK choice. The real blocker is a transport limit: over stdio each agent process is one connection, so a second connection to the same live session needs a multi-connection transport, which the TCK does not drive. Reword the reason as "Deferred: needs a second connection to the same agent instance, which the stdio transport cannot provide. Multi-connection activity is also optional (`session-setup.mdx:54`)." |

## New requirements

Ids follow rule B. Where the v1 researcher proposed the same rule (`impact-v1-config-options.md`,
`impact-v1-content-plan-commands.md`), I reuse its provisional id. `2xx` marks a v2-only rule.

1. **`ACP-PLAN-003`** (shared with v1): a markdown plan's `path` is absolute.
   - Text: "Every `plan_update` whose `plan.type` is `markdown` and whose `plan.path` is a string carries an absolute
     path in native syntax: POSIX, a Windows drive path or UNC, never a URI. An omitted or `null` `path` is not
     judged. SKIPs when no such plan is observed."
   - Tier: CAPABILITY, `capabilities.session`, following the PATCH-205/206 passive pattern. v1 proposes MANDATORY with
     a vacuous pass; rule B allows the tiers to differ (Decision 1).
   - Citation: `agent-plan.mdx:104-109`; `schema/v2/schema.unstable.json#/$defs/PlanMarkdown/properties/path`;
     `#/$defs/AbsolutePath`; `docs/rfds/plan-operations.mdx:64,196 (Preview RFD)` as secondary context (`:196`:
     "not a URI").
   - Test: reuse the plan-observing turn in `test_patches.py` that PATCH-205 uses, and apply `is_absolute_path`
     (`_helpers.py:770`).
   - Harness: none. Fixtures: one v2 agent that sends a markdown plan with `"path": "PLAN.md"`, and the conforming
     agent with an absolute path.
2. **`ACP-CLIENTCAP-2xx`**: no `skill` entries without the client capability. **I confirm the extensibility report's
   proposal, with refinements.**
   - Text: "With a client that does not advertise `capabilities.session.commands.skill`, no `availableCommands` entry
     has `type: \"skill\"`. The check covers setup responses (`session/new`, `session/resume`, `session/fork`),
     `available_commands_update`, and the `session/options` result."
   - Tier: CAPABILITY, `capabilities.session`, following the ACP-CLIENTCAP-003 precedent for a client-gated
     MUST NOT.
   - Citation: `slash-commands.mdx:171` (primary); `initialization.mdx:255-260`;
     `schema/v2/schema.unstable.json#/$defs/Skill` (whose description also states the MUST);
     `extensibility.mdx:40` (secondary).
   - Test: passive, on the default handshake (`capabilities: {}`, which omits `session`). Refinement (optional, cheap):
     a second connection with `{"session": {"commands": {"skill": null}}}`, because `:171` says `null` also means
     not advertised. That catches agents that test for key presence.
   - Harness: none (`v2_only_agent(capabilities=…)` exists).
3. **`ACP-COMMANDS-202`**: an agent that sends `skill` entries advertises `session.prompt.skill`.
   - Text: "On a connection advertising `session.commands.skill: {}`, if any `availableCommands` entry has
     `type: \"skill\"`, the `initialize` result carries `capabilities.session.prompt.skill` as an object. SKIPs when
     no skill entry is observed."
   - Tier: CAPABILITY, `inferred:skills`, a documentation-only gate. The row checks the agent's own marker, so it
     cannot be gated on it.
   - Citation: `slash-commands.mdx:173`; `initialization.mdx:417-418`; `#/$defs/Skill`.
   - Test: the TCK changes its own capabilities: open the connection with
     `capabilities={"session": {"commands": {"skill": {}}}}`, run `session/new`, and drain quietly. The same
     transcript feeds the COMMANDS-201 scope change.
   - Harness: none. Fixtures: an agent that sends a skill entry without `prompt.skill` (FAIL), and a conforming one
     that has both.
4. **`ACP-OPTIONS-001`** (shared): `session/options` works when advertised.
   - Text: "`session/options` with `{cwd: <abs tmp>}` succeeds with a schema-valid `SessionOptionsResponse`. Its
     `configOptions` meet the ACP-CONFIG-001/210 rules, and its `availableCommands` meet the ACP-COMMANDS-201 rules
     (whitespace-free names that are unique). A `-32000` reply SKIPs."
   - Tier: CAPABILITY, `capabilities.session.options`. The docs say "support" declaratively, as in the DELETE-001
     precedent.
   - Citation: `session-config-options.mdx:482,486-512,549`; `initialization.mdx:348-353`;
     `#/$defs/SessionOptionsRequest`; `#/$defs/SessionOptionsResponse`.
5. **`ACP-OPTIONS-002`** (shared; v2 asserts more): `session/options` creates, resumes and notifies nothing.
   - Text: "`session/options` sends no `session/update` (checked before the response and during the quiet drain), and
     `session/list {cwd: tmp}` shows no new session afterwards. With a `sessionId` of a session that was created and
     then `session/close`d, a following `session/prompt` on that id still gets `-32002`: the session was not
     resumed."
   - Tier: CAPABILITY, `capabilities.session.options`.
   - Citation: `session-config-options.mdx:551`; `session-setup.mdx:49,51`; `error.mdx:52`;
     `#/$defs/SessionOptionsRequest`.
   - Test: a fresh connection with no session and a unique tmp `cwd`. `session/list` is part of the v2 baseline.
     The "not resumed" probe is v2-specific: in v2, activity can be seen through `-32002`. Note that v1's ledger says
     "resuming has no client-visible marker", which does not carry over. The probe SKIPs if `session/options` errors
     on the closed id (the agent may have discarded the session).
6. **`ACP-OPTIONS-003`** (shared; v2 asserts the code): an unknown `sessionId` gets `-32002`.
   - Text: "`session/options` with a never-issued `sessionId` fails with `-32002`."
   - Tier: CAPABILITY, `capabilities.session.options`.
   - Citation: `session-config-options.mdx:514`; `#/$defs/SessionOptionsRequest/properties/sessionId`; `error.mdx:52`.
   - Note: `data.sessionId` is recorded, not asserted (Decision 5).
7. **`ACP-OPTIONS-004`** (shared): schema-invalid initial entries are rejected.
   - Text: "`session/new` with an initial entry that does not match `InitialSessionConfigOption` fails with
     `-32602`."
   - Tier: CAPABILITY, `capabilities.session.options`.
   - Citation: `:578`; `#/$defs/InitialSessionConfigOption`; `#/$defs/NewSessionRequest/properties/configOptions`.
   - Probes: `[{"type":"id","value":"x"}]` (missing `configId`) and `[{"configId":"x","type":"id","value":42}]`.
8. **`ACP-OPTIONS-201`** (v2 only): an unsupported value `type` is rejected.
   - Text: "An initial entry whose value `type` the agent does not support (probe `_tck_unsupported`, schema-valid
     through the open `other` branch) fails `session/new` with `-32602`."
   - Tier: CAPABILITY, `capabilities.session.options`.
   - Citation: `:579`; `#/$defs/InitialSessionConfigOption`.
   - Note: contrast it with OPTIONS-006, where a *known* `type` that does not match the option is ignored.
9. **`ACP-OPTIONS-005`** (shared): duplicate `configId`s are rejected.
   - Text: "Two initial entries with the same `configId` fail `session/new` with `-32602`."
   - Tier: CAPABILITY, `capabilities.session.options`.
   - Citation: `:580`.
   - Test: use a select option and its `currentValue` from `session/options`. Fall back to a synthetic id only if
     there is none (same as v1 D3).
10. **`ACP-OPTIONS-006`** (shared): inapplicable initial entries are ignored, not rejected.
    - Text: "`session/new` succeeds when an initial entry has an unknown `configId`
      (`{\"configId\":\"_tck_unknown_config\",\"type\":\"id\",\"value\":\"x\"}`), a value the option does not allow
      (`_tck_unknown_value` on a select option), or a known `type` that does not match the option (`boolean` on a
      select option, `id` on a boolean option). The option keeps a valid `currentValue`, never the bogus one."
    - Tier: CAPABILITY, `capabilities.session.options`.
    - Citation: `:482,581`; `#/$defs/InitialSessionConfigOption`.
    - Note: v2 needs no client capability for `boolean` probes. CONFIG-208 already sends them.
11. **`ACP-OPTIONS-007`** (shared): no `config_option_update` for initial entries.
    - Text: "After `session/new` with a valid initial entry, no `config_option_update` for the new session arrives on
      the requesting connection before the response or during the quiet drain."
    - Tier: ADVISORY. It is a SHOULD NOT. The check is heuristic, because the agent may have its own reasons to
      update.
    - Citation: `:583`.
    - Note: the before-response half overlaps ACP-SESSION-207. Keep both, since this rule also covers after the
      response.
12. **`ACP-OPTIONS-009`** (shared): `session/options` does not connect to MCP servers.
    - Text: "`session/options` with the `sessionId` of a closed session that was created with the TCK's stdio MCP stub
      does not relaunch the stub (no new marker during the response and the quiet drain)."
    - Tier: ADVISORY (SHOULD NOT).
    - Citation: `:516`.
    - Harness: reuse `conformance/_mcp_stub.py` (from `test_session_capabilities.py`). Same connection: create with
      the stub, wait for the marker, close, delete the marker, then call `session/options`. If the agent keeps the
      stub alive after close, the row passes vacuously (Decision 6).
13. **`ACP-OPTIONS-010`** (shared, INFORMATIONAL): record whether a valid initial value shows in the setup response.
    - Citation: `:572,582`.
    - Test: same exchange as 007.
14. *(optional)* **`ACP-OPTIONS-011`** (shared if v1 adopts it): the setup response tells the truth.
    - Text: "After `session/new` with initial entries, a no-op `session/set_config_option` (one option set to the
      `currentValue` the setup response reported) returns `(configId, currentValue)` pairs equal to the setup
      response's. SKIPs if a `config_option_update` arrives meanwhile."
    - Tier: CAPABILITY, `capabilities.session.options`.
    - Citation: `:582`; `:249,251`.
    - Note: this is the CONFIG-209 observation technique (Decision 7).
15. **ACP-ERROR-006 extension** (owned by the overview-error report). I agree: add `session/options` with
    `{"cwd": <abs>}` to the probes used when `capabilities.session.options` is not advertised (`error.mdx:44`;
    `session-config-options.mdx:482`). ERROR-006 already probes unstable methods (`session/archive`, `session/fork`,
    `providers/list`), so the v1 report's "stable only" objection does not apply to v2.

The TCK must keep the client MUST NOTs (`:482`): it calls `session/options` and sends `configOptions` only when
`capabilities.session.options` is advertised. Probes go on `session/new`. Probing `session/resume` is optional, for
OPTIONS-006 only. Probing `session/fork` needs `capabilities.session.fork`.

Fixtures for OPTIONS-*: the v2 conforming fixture must advertise `session.options: {}` and implement `session/options`
and initial values. Each MUST row needs a non-conforming twin. Update the `test_cli.py` id sets.

## New ledger entries

All cite `docs/protocol/v2/draft/<doc> @ 3ea94133…`.

- `session-config-options.mdx:209`
  - Statement: Agents SHOULD list a `select` `thought_level` option's values from lowest to highest.
  - Reason: Not observable. Value ids are opaque, and the protocol carries no reasoning-level measure.
- `session-config-options.mdx:215,217`
  - Statement: in a `boolean` `speed` option `true` is faster, and Agents SHOULD list a `select` `speed` option from
    slowest to fastest.
  - Reason: Not observable. The protocol carries no speed measure for option values.
- `session-config-options.mdx:219`
  - Statement: Agents SHOULD NOT use `speed` for an option that mainly selects a model, reasoning level or mode.
  - Reason: Not observable. "Mainly selects" is a semantic judgement that the wire does not express.
- `session-config-options.mdx:514`
  - Statement: with a `sessionId`, `session/options` returns what `session/resume` with the same `cwd` and
    `additionalDirectories` would return.
  - Reason: Not deterministically observable. The result is a snapshot (`:551`), and options can change before setup
    (`:576`).
- `session-config-options.mdx:551` (beyond OPTIONS-002)
  - Statement: `session/options` does not change an existing session and writes nothing to the history of
    `sessionId`.
  - Reason: Not deterministically observable. A change shows only through a later resume or replay, which the agent
    may legitimately vary (it may expire or rewrite stored sessions, `session-setup.mdx:47`).
- `session-config-options.mdx:572,574`
  - Statement: initial entries are applied in list order, each against the option set at that point, on top of the
    restored or fork configuration. On `session/resume` they are applied before replay and before the response.
  - Reason: Not observable. Order matters only through agent-specific dependencies between options, and replay
    carries history, not configuration.
- `session-config-options.mdx:584`
  - Statement: before the `session/new`/`session/fork` response, the Agent SHOULD NOT send other `session/update`s
    caused by applying initial entries.
  - Reason: Not attributable. The only update kind that can be tied to the entries is `config_option_update`, which
    ACP-SESSION-207 and ACP-OPTIONS-007 already judge. v2 has no `current_mode_update`, so v1's OPTIONS-008 has no
    v2 counterpart.
- `session-config-options.mdx:585`
  - Statement: a `session/resume` with initial entries SHOULD send `config_option_update` on other connections where
    the session is active.
  - Reason: Deferred, with the same blocker as the reworded `:390` entry (no second connection to one agent instance
    over stdio).
- `slash-commands.mdx:194-197`
  - Statement: an Agent that has a shorter user-facing skill description SHOULD send it.
  - Reason: Not observable. The client cannot see the skill's frontmatter.
- `slash-commands.mdx:210`
  - Statement: Agents SHOULD advertise only skills the user can invoke.
  - Reason: Unsafe. The only evidence is invoking a listed skill, which runs arbitrary user-installed code.
- `slash-commands.mdx:238-239,255` (the position/count half)
  - Statement: with `prompt.skill: {}` (no `inline`), a prompt with a `skill` block that is not first, or with two of
    them, MUST be rejected with `-32602`.
  - Reason: Unsafe. With a made-up name, the agent rejects for the name anyway, so the probe cannot tell the two
    causes apart (ACP-PROMPTCAP-202 covers the name). With a real listed name, a non-conforming agent would run a
    user skill.

## Decisions for the user

1. **ACP-PLAN-003 tier in v2.** CAPABILITY `capabilities.session` (PATCH-205/206 pattern, SKIP when unobserved) or
   MANDATORY with a vacuous pass (v1's choice). Recommendation: CAPABILITY. The id is shared, and rule B allows the
   tiers to differ.
2. **Skill gate row id: `ACP-CLIENTCAP-2xx` or `ACP-COMMANDS-2xx`.** Recommendation: CLIENTCAP, following
   CLIENTCAP-003 and the sibling prompt-suggestions row. Tier: CAPABILITY `capabilities.session`, not MANDATORY,
   following the same precedent. Include the `skill: null` sub-probe.
3. **COMMANDS-201 on a `commands.skill` connection.** Recommendation: yes. Otherwise the doc's "unique across commands
   and skills" MUST is never exercised. Also add COMMANDS-202 (`inferred:skills`, a new documentation-only gate
   name).
4. **`Skill.path` absoluteness.** `slash-commands.mdx:200-201` says "Optional absolute path" with no keyword. Unlike
   `agent-plan.mdx:109`, it carries no MUST. Recommendation: no row, or at most an INFORMATIONAL record. `:208`
   tells clients to treat an invalid value as absent.
5. **OPTIONS-003 assertion.** Recommendation: assert `-32002` (`:514` and the schema name it, and v2's `error.mdx:52`
   is a MUST for nonexistent sessions). Record `data.sessionId` without asserting it, because `error.mdx`'s Unstable
   list does not mention `session/options` (the gap the overview-error report found).
6. **OPTIONS-009.** An ADVISORY row with a known vacuous-pass case, or a Deferred ledger entry. Recommendation: the
   row, as v1 recommends.
7. **OPTIONS-011.** Add it, or leave `:582` to OPTIONS-006/010. Recommendation: add it if v1 adopts it too.
   Otherwise put a ledger entry, "partially covered by ACP-OPTIONS-006/010".
8. **Reword the existing ledger reason at `:390`** as above (it currently reads as a TCK choice).

## Discrepancies

- `docs/rfds/session-options.mdx` (Draft RFD) says MUST where the docs speak declaratively: "MUST implement
  `session/options`" (`:64`) against docs `:482` "support". "MUST return `-32002`" (`:87`) against docs `:514`
  "gets". RFD `:151` drops the docs' "on the requesting connection" (`:583`). The docs govern. These are differences
  in strength, not conflicts.
- `error.mdx`'s Unstable features list (`:66-70`) omits `session/options` `-32002`, which `:514` and the schema
  state (already reported by the overview-error researcher).

## Open questions

- ENUM-201 does not check `SessionConfigOption.category`, an agent-emitted open-enum site (`:197`; `speed` added). This
  gap predates the update and is optional; it belongs to the extensibility owner.
- `session-setup.mdx:594-597` restates the initial-values rules. The session-setup researcher should cite the
  OPTIONS rows above rather than add duplicates.
