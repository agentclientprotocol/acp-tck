# Impact (v1): `docs/protocol/v1/draft/session-config-options.mdx`, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read through the
`agent-client-protocol-2` checkout, HEAD `6ace4f6a`. `git diff 3ea94133 -- docs/protocol/v1/draft schema/v1
docs/rfds/session-options.mdx docs/rfds/speed-config-category.mdx` is empty, so the text is identical to the target),
base `3961af94`. Files: `docs/protocol/v1/draft/session-config-options.mdx` (whole), `session-setup.mdx:454-456`,
`initialization.mdx:189-198,424-429`, `error.mdx:45-55,61-66`, `schema/v1/schema.unstable.json` (`SessionOptions*`,
`InitialSessionConfigOption`, `SessionConfigOptionCategory`, `*SessionRequest.configOptions`, `SessionCapabilities`,
`ClientSessionCapabilities`), `docs/rfds/session-options.mdx` and `docs/rfds/speed-config-category.mdx` (both **Draft**
at the target, per `docs/docs.json`; `rfds/session-config-options` is Completed). TCK: `src/tck/v1/requirements.py`,
`spec-tracker/maps/v1.toml`, `src/tck/v1/conformance/test_session_config.py`, `test_session.py` (MCP stub).
I did not consult the reference SDKs: every rule below is stated explicitly in the docs, and none relies on implicit
runtime behaviour.
**Confidence:** high for the classification and the line maps. Medium for the proposed tiers of the declarative
(no-keyword) sentences; these are listed under decisions.

Line map for this doc: base 1-221 = target 1-221; base 222-232 -> +1; base 233-457 -> +13; base 458-end -> +110.

## Existing rows and ledger entries

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-CONFIG-001 | citation-only | `session-config-options.mdx:118-130,258` | `245` -> `258`. The schema pointers are unchanged: `SessionConfigOptionCategory` gained the `speed` const, but its open `other` string branch already accepted any value. |
| ACP-CONFIG-002 | citation-only | `session-config-options.mdx:317,386-390` | `304` -> `317`, `373-377` -> `386-390`. |
| ACP-CONFIG-003 | **changed text (scope)**, tier unchanged (MANDATORY) | `session-config-options.mdx:207-209` (unchanged) + add `:535`; `initialization.mdx:189-198` (unchanged) | The rule covers "`configOptions` payloads", and line 535 says the `session/options` result uses "the same type and rules as on `NewSessionResponse`". Add the `session/options` result to the payloads the test checks, but only when `agentCapabilities.sessionCapabilities.options` is advertised (the TCK may not call it otherwise, line 475). This mirrors the existing conditional `session/load`/`resume` checks. |
| ledger `:245-249` (`currentValue` operability) | citation-only | `:258-262` | The reason ("Not observable") is spec-based, not a TCK choice. |
| ledger `:235` (higher-priority options first) | citation-only | `:248` | The reason is fine. |
| ledger `:462-471` (send both modes and a mode option, keep them in sync) | citation-only | `:572-581` | The reason is fine. |

Nothing was removed. None of the existing ledger reasons for this doc rests on a TCK choice.

## New requirements (provisional ids `ACP-OPTIONS-0xx`; v1 has no counterpart yet)

All of them are gated on the real capability `agentCapabilities.sessionCapabilities.options`
(`initialization.mdx:424-429`; `schema/v1/schema.unstable.json#/$defs/SessionCapabilities/properties/options`). The
section is marked "(unstable)", but the TCK already tests other unstable `sessionCapabilities` the same way. The TCK
must honour the client MUST NOTs: it calls `session/options` or sends `configOptions` only when the capability is
advertised (line 475). It sends `sessionId` only when `loadSession` or `sessionCapabilities.resume` is advertised.
Line 507 also allows `fork`, but the schema description does not (see discrepancies). Gating on load or resume
satisfies both texts. It sends `type: "boolean"` entries only on a connection that advertises
`clientCapabilities.session.configOptions.boolean`.

1. **ACP-OPTIONS-001**: `session/options` with `{cwd: <abs tmp>}` succeeds with a schema-valid
   `SessionOptionsResponse`. Every `configOptions` entry's `currentValue` is valid for its type, by the same check as
   ACP-CONFIG-001.
   - Tier: CAPABILITY. The docs say "Agents that advertise ... support `session/options`" (declarative). The Draft
     RFD says MUST (`docs/rfds/session-options.mdx:64`, secondary context only).
   - Citation: `session-config-options.mdx:475,479-500,511-535`; `#/$defs/SessionOptionsRequest`;
     `#/$defs/SessionOptionsResponse`.
   - Test: fresh connection, then `session/options`. Validate it with `validate_agent_response("session/options", …)`,
     which works after the re-vendor because the method mapping comes from `x-method`. Reuse
     `_flatten_select_values`. A `-32000` reply SKIPs.
2. **ACP-OPTIONS-002**: `session/options` sends no `session/update` notification and adds no entry to `session/list`.
   - Tier: CAPABILITY (MUST NOT).
   - Citation: `:537`; `#/$defs/SessionOptionsRequest` (description restates the rule).
   - Test: fresh connection with no session. When `sessionCapabilities.list` is advertised, run `session/list {cwd: tmp}`
     first (follow `nextCursor`). Then call `session/options {cwd: tmp}` and wait for the response plus
     `quiet_period`. FAIL on any received `session/update`. With `list` advertised, run `session/list {cwd: tmp}` again
     and FAIL if new `sessionId`s appear. This is the observable form of "MUST NOT create". Without `list`, only the
     notification half is checked.
3. **ACP-OPTIONS-003**: `session/options` with a `sessionId` the agent never issued fails with an error rather than a
   result.
   - Tier: CAPABILITY. Needs `loadSession` or `resume`, else SKIP.
   - Citation: `:507` ("A session the Agent does not know gets `-32002`").
   - Test: send `sessionId: "acp-tck-unknown-<uuid>"`. FAIL on success. Asserting the code is a decision (see below).
4. **ACP-OPTIONS-004**: in initial `configOptions`, an entry that does not match the schema fails the setup request
   with `-32602`.
   - Tier: CAPABILITY (MUST).
   - Citation: `:563`; `#/$defs/InitialSessionConfigOption`;
     `#/$defs/NewSessionRequest/properties/configOptions`.
   - Test: `session/new {cwd, mcpServers: [], configOptions: [{"value": "x"}]}` (missing `configId`). Optionally a
     second probe `[{"configId": "x", "value": 42}]`, which matches neither `anyOf` branch and needs no boolean
     capability. Expect error `-32602`. A success or any other code is a FAIL, and `-32000` SKIPs.
5. **ACP-OPTIONS-005**: two initial entries with the same `configId` fail the setup request with `-32602`.
   - Tier: CAPABILITY (MUST).
   - Citation: `:564`.
   - Test: take a `select` option and its `currentValue` from `session/options`, send them twice on `session/new`, and
     expect `-32602`. If the agent has no select option, see decision D3.
6. **ACP-OPTIONS-006**: initial entries the agent cannot apply are ignored, not rejected. The request succeeds, and the
   option does not take the bad value.
   - Tier: CAPABILITY (MUST).
   - Citation: `:475` ("accept initial values"), `:565-566`.
   - Test, on `session/new`:
     1. send `[{"configId": "acp-tck-unknown-option", "value": "x"}]`; expect a success.
     2. If `session/options` returned a `select` option O, send `[{"configId": O, "value": "acp-tck-not-a-value"}]`.
        Expect a success whose O `currentValue` is not the bogus value and is among O's options.
     3. Optionally, on a connection advertising `clientCapabilities.session.configOptions.boolean`, send
        `[{"configId": O, "type": "boolean", "value": true}]` to cover the type-mismatch case.
     4. Optionally repeat probe 1 on `session/load` or `session/resume` of a created session when those are
        advertised. Line 475 names both.
7. **ACP-OPTIONS-007**: applying initial entries sends no `config_option_update`.
   - Tier: ADVISORY (SHOULD NOT).
   - Citation: `:567`.
   - Test: from `session/options`, pick a `select` option O and an alternative value V (else SKIP). Send `session/new`
     with `[{O, V}]`. FAIL if any `config_option_update` for the returned `sessionId` arrives before the response or
     within `quiet_period` after it. Attribution is heuristic: an idle fresh session has no other reason to update.
     That is acceptable for ADVISORY.
8. **ACP-OPTIONS-008**: before the `session/new` response, the agent sends no other `session/update` caused by applying
   the entries.
   - Tier: ADVISORY (SHOULD NOT).
   - Citation: `:568`.
   - Test: same exchange as 007, so one test can bind both ids. FAIL if a `current_mode_update` or
     `config_option_update` arrives before the `session/new` response. Restrict the check to these kinds, because the
     doc limits the rule to updates "caused by applying the entries".
9. **ACP-OPTIONS-009**: `session/options` with a `sessionId` does not connect to MCP servers.
   - Tier: ADVISORY (SHOULD NOT).
   - Citation: `:509`.
   - Test: needs `loadSession` or `resume`. On connection 1, run `session/new` with the stdio `_mcp_stub` (marker M) and
     wait for M to appear. SKIP if it never appears. Close connection 1. Delete M. On a fresh connection, call
     `session/options {cwd, sessionId}`; a `-32002` or other error SKIPs, because the agent does not persist. Wait for
     the response plus `quiet_period`. FAIL if M exists.
   - Harness: move `_stdio_mcp_server`/`_MCP_STUB` from `test_session.py` into `_helpers.py`. Without `sessionId` the
     request carries no `mcpServers`, so there is nothing the TCK can observe.
10. *(optional, see D4)* **ACP-OPTIONS-010**: a valid initial value is reflected in the setup response.
    - Tier: INFORMATIONAL.
    - Citation: `:559,566`.
    - Test: the 007 exchange. Record whether O's returned `currentValue` equals V. Assert nothing, because lines 565
      and 561 let the agent ignore a value its runtime refuses or one that changed since `session/options`.

Harness and fixture needs:
- The mock client needs no new behaviour. `connected_agent(client_capabilities=…)`, `send_request`, `quiet_period` and
  `session_update_kind` cover everything.
- The v1 conforming fixture (`tests/fixtures/agents/v1/conforming.py`) must advertise
  `sessionCapabilities.options: {}` and implement `session/options` and initial values. Non-conforming fixtures are
  needed for the MUST rows, and `test_cli.py` id sets need updating.
- The CONFIG-003 extension needs only a conditional `session/options` call.

## New ledger entries

Agent-side rules that the TCK deliberately does not test, all citing `session-config-options.mdx @ 3ea94133`:

- `:236,238`
  - Statement: in a `boolean` `speed` option `true` is the faster setting, and agents SHOULD list a `select` `speed`
    option's values from slowest to fastest.
  - Reason: Not observable. The protocol carries no speed measure for option values. Which value is faster is the
    agent's own judgement.
- `:240`
  - Statement: agents SHOULD NOT use the `speed` category for an option that mainly selects a model, reasoning level or
    session mode.
  - Reason: Not observable. Whether an option "mainly" selects a model is a semantic judgement that the wire format
    does not express.
- `:507`
  - Statement: with a `sessionId`, `session/options` returns what `session/load` or `session/resume` with the same
    `cwd` and `additionalDirectories` would return.
  - Reason: Not deterministically observable. The response is a snapshot, and options can change between
    `session/options` and session setup (`:537,561`), so a mismatch with a later load or resume is not a violation.
- `:537` (the parts not covered by ACP-OPTIONS-002)
  - Statement: `session/options` MUST NOT resume a session or change an existing session, and writes nothing to the
    history of `sessionId`.
  - Reason: Not deterministically observable. The only window is comparing `session/load` replays before and after,
    and replays need not be identical (`session-setup.mdx:157 @ 3ea94133`: message ids need not stay the same across
    a load). Resuming has no client-visible marker.
- `:559`
  - Statement: the agent applies initial entries in list order, each checked against the option set as it stands at
    that point, on top of a restored session's configuration, or of the fork's starting configuration.
  - Reason: Not observable. Order only matters through dependencies between options, which are agent-specific and not
    described on the wire. The resulting values are covered as far as observable by ACP-OPTIONS-006 and -010.

I propose no ledger entry for the client-side rules (`:475` and `:507` client MUST NOTs, `:541` boolean entries, `:559`
client ordering SHOULD, `:537` "no timer" SHOULD, `:244` client rendering) or for the MAY at `:537`.

## Discrepancies

- **Wrong capability path in the docs and schema text.** `:535` and `:541`, `schema.mdx:1209,5790`, and the
  `SessionOptionsResponse`/`InitialSessionConfigOption` descriptions say "`sessionCapabilities.configOptions.boolean`".
  That path does not exist: `SessionCapabilities` has no `configOptions`. The real path is
  `clientCapabilities.session.configOptions.boolean` (`:114-115,176-189`; `initialization.mdx:189-198`;
  `#/$defs/ClientSessionCapabilities`). The TCK should use the real client path and mention the upstream wording in
  the CONFIG-003 / OPTIONS row text.
- **`sessionId` gate.** Docs `:507` and the Draft RFD `:170` allow `sessionId` when the agent supports load, resume
  **or fork**. The schema `SessionOptionsRequest.sessionId` description says only load or resume. This is client-side;
  gating on load or resume satisfies both.
- **`type` default.** `:541` says "`type` is optional and defaults to `id`". The schema's default branch is titled
  `value_id` (a string `value`). The wording is loose and the wire behaviour is unambiguous.
- No conflict between the docs and the Draft RFDs on agent-side rules. The RFD's MUST for "implement `session/options`"
  (`rfds/session-options.mdx:64`) matches the docs' declarative sentence. The docs govern, and the capability gate
  makes the row CAPABILITY either way.

## Decisions for the user

- **D1. Tier of the "support / accept" rule** (OPTIONS-001 and the accept half of 006). The docs use declarative
  wording, and only the Draft RFD says MUST.
  - Recommendation: CAPABILITY. The gate is real, and advertising the capability is the opt-in, as with ACP-CLOSE-001.
- **D2. OPTIONS-003 error code.** `:507` says "gets `-32002`" without a keyword, and the general rule in `error.mdx:51`
  is SHOULD `-32002` and does not list `session/options`.
  - Recommendation: the CAPABILITY row asserts only "an error, not a result", following the ACP-ARCHIVE-005
    precedent. Route an ADVISORY `-32002` + `data.sessionId` check to whoever owns ACP-ERROR-003/004 (the `error.mdx`
    impact research). Alternative: put the code check in this row as ADVISORY.
- **D3. OPTIONS-005 when the agent has no `select` option.** The rule is unconditional, but sending duplicates of an
  unknown id puts it next to the "unknown is ignored" rule.
  - Recommendation: use a known id when one exists, and otherwise a synthetic id. `:564` lists duplicates as a failure
    with no qualification.
  - Alternative: SKIP when there is no option.
- **D4. OPTIONS-010.** Add it as INFORMATIONAL, or drop it.
  - Recommendation: add it. It is cheap, it reuses the 007 exchange, and it shows whether initial values work at all.
- **D5. OPTIONS-009.** Make it an ADVISORY row (feasible with the existing MCP stub, but multi-connection and
  persistence-dependent), or a ledger entry.
  - Recommendation: a row, because the rule is observable when the TCK supplies the MCP server. A ledger entry would
    have to be "Deferred", not "not observable".
- **D6. Scope of OPTIONS-004/005/006 across setup methods.** The rules apply to `session/new`, `load`, `resume` and
  `fork`.
  - Recommendation: test on `session/new`, and add the `load`/`resume` probe for 006 only. The row text should say
    which methods it checks.

## Open questions (for other researchers)

- `session-setup.mdx:454-456` (new "Initial config option values" section) restates `:559`. The `session-setup.mdx`
  impact research should cite this report's rows rather than add duplicates.
- ACP-ERROR-006 probes only *stable* unadvertised methods (`-32601`). `session/options` is unstable, so it stays out
  unless the `error.mdx` research decides otherwise.
- v2 has the same feature, with differences: the `type` discriminator is required, unsupported `type` gets `-32602`,
  and `availableCommands` is in the response (`rfds/session-options.mdx:175-200`). The v2 researcher must derive its
  rows on its own. Id alignment may share `ACP-OPTIONS-0xx` where the rules match.
