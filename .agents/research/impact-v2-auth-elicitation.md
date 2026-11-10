# v2 impact: `authentication.mdx`, `elicitation.mdx`, and unstable `auth/status` (alpha.9 -> alpha.14)

**Sources checked:** agent-client-protocol (spec) base `beac4ba96190` -> target `3961af94fa62` (read-only worktree `agent-client-protocol-2`, read via `git show`/`git diff`); acp-rust-sdk @ `e75d6f19fabb` (2026-11-09; `pull --ff-only` said already up to date), only to check whether `auth/status` is implemented; acp-tck working tree on `eugenethedev/update-spec` (registry, tests, fixtures, plugin). Python SDK not consulted: no requirement here depends on runtime behaviour the spec leaves open.
**Confidence:** high for classifications and citations (every line below was re-read at target). Medium for the three DECISION NEEDED tier calls, which are judgment, not lookups.

All `path:line` citations without a repo prefix are in the spec repo at `3961af94fa62`. TCK paths are repo-relative to acp-tck.

## Summary table

| Id | Classification | One-line note |
|----|----------------|---------------|
| ACP-AUTH-201 | **changed tier (DECISION NEEDED)** | Uniqueness is now a prose **MUST** (`authentication.mdx:51`). Recommend ADVISORY -> MANDATORY. Test unchanged. `test_cli` expectation for `duplicate_method_id.py` changes. |
| ACP-AUTH-202 | changed citation (dangling `$def`) + text tightened | `#/$defs/AuthCapabilities` -> `#/$defs/ClientAuthCapabilities` (B3). Prose is now an explicit **MUST NOT** at `authentication.mdx:149-151`. Tier and test unchanged. |
| ACP-AUTH-203 | citation-only (optional enrichment) | Logout obligation is now explicit at `:51-52,83,247-249`. Test unchanged. See the cross-connection credential note in Testability. |
| ACP-AUTH-204 | citation-only, plus an optional tightening (DECISION NEEDED, low) | `:51-54` -> `:51-53`. New `:191` reserves `-32602` for unadvertised/non-login ids, so an advertised `type:"agent"` id answered `-32602` could FAIL. The pending-login timeout issue is in Testability. |
| ACP-AUTH-205 | citation-only (meaning unchanged) | `schema.mdx:785` -> `schema.mdx:954`. Optionally add `authentication.mdx:193`. |
| ACP-AUTH-206 | citation-only | `:120-122` -> `:118-120`. Optionally add `:88-89` (type discriminator is now **MUST**). |
| ACP-AUTH-207 | citation-only | `:201-203` -> `:203-205`. |
| ACP-CLIENTCAP-201 | citation-only, but **meaning moved** (flag for review) | `elicitation.mdx:54,187` -> `:56,59`. Base line 187 (client answers `-32602`) was deleted and replaced by `:59` (`-32601` with no capability, `-32602` for an unadvertised mode). Test and fixture unchanged. |
| ACP-EXT-204 (not my doc) | unaffected | Probes unknown fields under `capabilities.auth`. The rename leaves the `ClientAuthCapabilities` shape the same and it is still open, so no change. |
| ACP-LOGOUT-* | n/a | No such ids exist. Logout is ACP-AUTH-203. |
| **ACP-AUTH-208** (new) | new, CAPABILITY `inferred:authMethods` (DECISION NEEDED) | `auth/login` with an unadvertised `methodId` -> `-32602` (`authentication.mdx:191`). |
| **ACP-AUTH-209** (new) | new, CAPABILITY `capabilities.auth.status` (DECISION NEEDED: now vs defer) | `auth/status` answers a schema-valid `AuthStatusResponse`, never `-32000`/`-32601`, and `state` is a defined or `_`-prefixed value. |
| Ledger L1-L16 | new deliberate non-requirements | Auth error paths that can't be triggered, terminal-flow SHOULDs, and the elicitation agent-side MUSTs that can't be triggered from the client side. `auth/status` side-effect and notification rules. |

## Answer

Both docs are non-core (the spec map does not list them). Most of the change is rewording and RFC-keyword bolding. Four things need action:

1. **Two citations break or move in meaning.** ACP-AUTH-202 cites the removed `#/$defs/AuthCapabilities` (B3), which `tests/v2/test_registry.py` will flag. ACP-CLIENTCAP-201 cites `elicitation.mdx:187`, a client-side `-32602` sentence that was deleted and rewritten at `:59`.
2. **`methodId` uniqueness became a MUST** (`authentication.mdx:51`). ACP-AUTH-201 should be promoted from ADVISORY (DECISION NEEDED).
3. **`auth/login` error codes are now defined** (`:191`): `-32602` for an unadvertised or non-login method, `-32000` for a failed or abandoned login, `-32800` for a cancelled one. Only the `-32602` path can be safely observed, so it becomes the proposed ACP-AUTH-208.
4. **The `authMethods` trigger is now "a non-empty list"**, no longer "one or more valid entries" (`:51`, `InitializeResponse.authMethods`, `LoginAuthRequest`/`LogoutAuthRequest` descriptions). The TCK's `--auth-method`/`--allow-logout` flow already gates on list truthiness, so it now matches the spec exactly. No code change is needed. Interactive logins that stay pending (`:179`) are a new practical hazard; see Testability.

The B6 elicitation schema changes (`requestedSchema` requires `type`+`properties`; scope is `oneOf`), the B9 `ElicitationContentValue` loosening and B11 have no effect on any test or fixture. The TCK never advertises elicitation and never schema-validates `elicitation/create`. I re-validated the one fixture that sends one against the target schema, and it is still valid.

For `auth/status`, I recommend adding one CAPABILITY row now (ACP-AUTH-209). It is safe (a pure query), observable without credentials, has precedent (ACP-FORK-201/202 test an unstable RFD-backed method the same way), and the Rust SDK already wires it. The notification rules go to the ledger.

## Requirements (new rows and changed tiers)

| # | Requirement | Tier | Citation |
|---|-------------|------|----------|
| AUTH-201 (changed) | `authMethods[*].methodId` values are unique within the list | MUST -> MANDATORY (was ADVISORY) | `docs/protocol/v2/draft/authentication.mdx:51` |
| AUTH-208 (new) | With non-empty `authMethods`, `auth/login` with a `methodId` not in the list is answered `-32602` | MUST-equivalent declarative -> CAPABILITY `inferred:authMethods` | `authentication.mdx:191` |
| AUTH-209 (new) | If `capabilities.auth.status` is advertised, `auth/status` right after `initialize` (no login) returns a schema-valid `AuthStatusResponse`, never `-32000`/`-32601`, with `state` defined or `_`-prefixed | capability:`capabilities.auth.status` | `schema/v2/schema.unstable.json#/$defs/AuthStatusRequest`, `#/$defs/AuthStatusResponse`, `#/$defs/AuthState`, `#/$defs/AgentAuthCapabilities/properties/status`; `docs/protocol/v2/draft/schema.mdx:143-144`; `docs/protocol/v2/draft/initialization.mdx:215-219`; `docs/protocol/v2/draft/authentication.mdx:193`; RFD (Draft proposal) `docs/rfds/get-auth-state.mdx:293,297` |

## Details

### ACP-AUTH-201: DECISION NEEDED, recommend MANDATORY

- Base: there was no uniqueness rule in prose. The schema says only "Unique identifier for this authentication method" (`#/$defs/AuthMethodAgent/properties/methodId`), which is why the row is ADVISORY.
- Target: `authentication.mdx:51`: "Each `methodId` **MUST** be unique within the list."
- Proposed text: "`authMethods[*].methodId` values are unique within the list." Drop "Re-cites v1's ACP-AUTH-001" or keep it as history (v1 stays ADVISORY; that is v1's call).
- Citation: `docs/protocol/v2/draft/authentication.mdx:51; schema/v2/schema.unstable.json#/$defs/AuthMethod; .../AuthMethodId`.
- Test (`src/tck/v2/conformance/test_authentication.py:55-71`): assertions unchanged. Update the docstring tier.
- `tests/v2/test_cli.py:2364` `test_duplicate_method_id_fails_auth_201_only_and_stays_conformant`: the FAIL set stays `{"ACP-AUTH-201"}`. The name and docstring ("stays conformant", "ADVISORY") become wrong. Rename the test and add `returncode != 0`, as for the other MANDATORY defect fixtures (e.g. `:2384-2389`). Fixture `tests/fixtures/agents/v2/duplicate_method_id.py` docstring says "ADVISORY" and needs the same change.

### ACP-AUTH-202: repoint citation; tier and test unchanged

- B3: `#/$defs/AuthCapabilities` is gone. `ClientCapabilities.properties.auth` now refs `#/$defs/ClientAuthCapabilities` (same shape: `terminal` + `_meta`).
- Prose went from "An Agent may advertise a `terminal` method only when this capability is present" (base `:151-152`) to "Agents **MUST NOT** advertise a `terminal` method unless this capability is present. Clients ignore `terminal` methods they did not enable." (target `authentication.mdx:149-151`). The schema already said "Agents MUST advertise this method only when the client enabled its terminal authentication capability" (`#/$defs/AuthMethodTerminal` description), so MANDATORY was already right. This change makes the prose agree with it.
- New citation: `schema/v2/schema.unstable.json#/$defs/AuthMethodTerminal; #/$defs/ClientAuthCapabilities; #/$defs/TerminalAuthCapabilities; docs/protocol/v2/draft/authentication.mdx:149-151`.
- Text: unchanged (it already says `capabilities.auth.terminal: {}`).

### ACP-AUTH-203: citation enrichment only

- The obligation is now explicit: `authentication.mdx:51-52` ("An Agent that does so **MUST** implement both `auth/login` and `auth/logout`"), `:83`, and `:247-249` (clients may call logout only when `authMethods` is non-empty; there is no logout capability marker). The schema `LogoutAuthRequest` description says "Agents MUST support this method when their `initialize` response included a non-empty `authMethods` list".
- Suggested citation: append `docs/protocol/v2/draft/authentication.mdx:51-52,247-249` to the existing schema pointers. `#/$defs/AgentAuthCapabilities` still resolves. Its description now explicitly says it does not advertise login/logout, which supports the "documentation-only" `inferred:authMethods` gate.
- Tier stays CAPABILITY / `inferred:authMethods`. The test is unchanged and still correct: it gates on non-empty `authMethods` plus `--allow-logout`, and checks only for an object result.

### ACP-AUTH-204: citation-only, optional tightening (DECISION NEEDED, low)

- `:51-54` -> `:51-53` (the base range ran one line into the `capabilities.auth` paragraph). The current test's `-32601` -> FAIL logic still matches `:51-52`.
- New `:191`: "If `methodId` is not an advertised method whose type uses `auth/login`, the Agent responds with `-32602`. If login fails or the user abandons it, the Agent responds with `-32000`. A login cancelled with `$/cancel_request` gets `-32800`."
  - So for an operator-supplied id naming an advertised **`type: "agent"`** entry, `-32602` is non-conforming: `agent` is the only standard type that "handles authentication through `auth/login`" (`:87-88`). The test currently SKIPs on any non-`-32601` error.
  - Recommendation: also FAIL on `-32602` when the matched entry's `type == "agent"`. Keep SKIP for `-32000` (legitimate failed login), for any other code, and for `_`-prefixed types, where `-32602` is legitimate if that custom type does not use `auth/login`.
  - If you accept this, add to the text: "... nor `-32602` for an advertised `type: \"agent\"` id".
  - Fixture: `login_advertised_agent_method_invalid_params.py` advertises `{"methodId":"tck","type":"agent"}` and answers `auth/login` `-32602`. Run with `--auth-method tck`, it should FAIL only AUTH-204. Check how `connected_agent`'s embedded login reacts: the SKIP path in `login_if_needed` would SKIP session tests, so scope with `-k authentication`.
- Optional extra citation: `authentication.mdx:191`.

### ACP-AUTH-205: citation-only

- `docs/protocol/v2/draft/schema.mdx:785` -> `:954` ("May return an `auth_required` (`-32000`) error if the agent requires authentication."). It is still a MAY. ADVISORY is unchanged.
- Optionally add `authentication.mdx:193` ("any request except `initialize`, `auth/login`, `auth/logout`, and `auth/status` may fail with `auth_required`").

### ACP-AUTH-206: citation-only

- `:120-122` -> `:118-120` ("Custom method types **MUST** begin with `_`. Unknown non-underscore method types are reserved for future ACP variants.").
- `:88-89` now bolds "Every authentication method **MUST** include a `type` discriminator". The test already FAILs a missing `type` (`is_valid_open_enum_value(None, …)` is False, `src/tck/v2/protocol.py:122`), and the schema requires `type` in all three `AuthMethod` branches. Optionally cite `:88-89` and say "present and" in the text.
- B11 (the "other" branch lost declared `description`/`_meta`, `additionalProperties: true` stays): no effect. A `{type:"_x", methodId, name, description, _meta}` entry validates at both base and target (checked with jsonschema against both schemas).
- Also update the docstring line reference at `test_authentication.py:78` and the fixture docstring at `tests/fixtures/agents/v2/custom_auth_type_unprefixed.py:4`.

### ACP-AUTH-207: citation-only

- `:201-203` -> `:203-205` (step 2 "Every `env` entry **MUST** have a unique `name`"). The `#/$defs/AuthMethodTerminal/properties/env` description still says "Names MUST be unique".
- `args`/`env` gained `x-deserialize-default-on-null`. This is a receiver hint only and does not affect the test's "if present" checks. Note: `null` `args`/`env` is still schema-invalid (`type: array`), and the test treats `None` as absent. That gap is unchanged and harmless.

### ACP-CLIENTCAP-201: repoint citation (meaning moved); text, tier and test unchanged

- Base `:54` = "Agents **MUST NOT** request a mode the Client has not advertised". At target this is `:56-57`, unchanged in substance.
- Base `:187` = "Requests using a mode the Client has not advertised produce JSON-RPC `-32602`". It was **deleted** and replaced by `:59`: a client with no `elicitation` capability answers `-32601`; one that advertised `elicitation` without the mode answers `-32602`. This is a client-side rule. The mock client in `run_prompt` already answers every agent->client request `-32601` (`src/tck/v2/conformance/_helpers.py:1037-1042`), which is correct for `capabilities: {}`.
- New citation: `docs/protocol/v2/draft/elicitation.mdx:56-57,59; schema/v2/schema.unstable.json#/$defs/CreateElicitationRequest (x-method: elicitation/create)`. `spec-impact --fix` cannot map `187` because the line was removed, so expect it under "Needs review".
- Test docstring `test_client_capabilities.py:43` (`elicitation.mdx:54`) should become `:56`.
- Fixture `tests/fixtures/agents/v2/calls_elicitation_unadvertised.py` sends `{sessionId, mode:"url", message, elicitationId, url}`. It is valid against the target `CreateElicitationRequest` (checked), satisfies `oneOf` scope (exactly one), and no test schema-validates `elicitation/create` anyway. No change.

### New: ACP-AUTH-208: DECISION NEEDED (tier, and whether the probe is acceptable client traffic)

- **Text:** "When `initialize` advertised a non-empty `authMethods`, `auth/login` with a `methodId` that is not among them (a TCK-chosen `_tck_unadvertised_method`) is rejected with `-32602`. A success, `-32000`, or any other code FAILs."
- **Tier:** CAPABILITY, `capability="inferred:authMethods"` (documentation-only, like AUTH-203/204; SKIP when `authMethods` is empty).
  - Justification: `:191` is declarative ("the Agent responds with `-32602`") with no RFC keyword. The registry already treats that strength as binding: ACP-RESUME-208 ("Malformed `replayFrom` values also result in `-32602`", `session-setup.mdx:200-201` at base) is CAPABILITY.
  - Alternative: ADVISORY, if you want declarative error sentences tiered as SHOULD.
- **Probe-legitimacy caveat (the main decision):**
  - `docs/protocol/v2/draft/schema.mdx:24-27` says "Clients MUST call this method only with a method whose type defines a protocol-driven login flow". `#/$defs/LoginAuthRequest/properties/methodId` says "Must be one of the methods advertised" (lowercase). `_helpers.validate_login_method_id`'s docstring treats unadvertised ids as a client MUST NOT ("V13").
  - But the doc now defines the agent's response to exactly this input, which makes it a specified error path, like RESUME-207's unsupported cursor probe.
  - Recommendation: add the probe, with an id that cannot collide with an advertised one (SKIP if it happens to). Never probe the `terminal`-id branch, which is under an explicit bold client MUST NOT (`authentication.mdx:176,217-218`).
- **Observation:** a fresh connection with `initialize` and no login (auth/login is exempt from auth gating, `:193`), then `auth/login {"methodId":"_tck_unadvertised_method"}`, then assert `error.code == -32602`. Safe: a conforming agent rejects before starting any interactive flow. No `--auth-method` needed.
- **Fixture:** `login_accepts_unadvertised_method.py` advertises `{"methodId":"tck","type":"agent","name":"TCK"}` and answers `auth/login` with `{}` for any `methodId`. It should FAIL only AUTH-208 (`-k authentication`). `_base.py:_handle_login` (`tests/fixtures/agents/v2/_base.py:296-303`) already answers `-32602` for unknown ids, so every existing auth fixture passes the new row without changes.

### New: ACP-AUTH-209 (`auth/status`): DECISION NEEDED, recommend adding now

Wire facts (target schema):

- **Capability.** `capabilities.auth.status` (`#/$defs/AgentAuthCapabilities/properties/status` -> `AuthStatusCapabilities`, an object marker; omitted or `null` = unsupported). Doc: `initialization.mdx:215-219`. Unstable table: `overview.mdx:260`.
- **`auth/status` request.** `AuthStatusRequest {_meta?}` (x-side agent). Its description says "Agents MUST NOT reject it with `auth_required` (`-32000`)". `schema.mdx:143-144`: "only available if the agent advertises the `auth.status` capability. It MUST NOT change any agent state, and agents MUST NOT reject it with `auth_required`." `authentication.mdx:193` lists `auth/status` among the requests that are never auth-gated.
- **`auth/status` response.** `AuthStatusResponse {state (required, AuthState), accounts?: AuthAccount[], _meta?}`.
  - `AuthState` is an open enum: `authenticated` | `unauthenticated` | `not_required` | `unknown`, plus an "other" branch whose values must be `_`-prefixed (non-`_` values are reserved, `#/$defs/AuthState/anyOf/4`).
  - `AuthAccount` requires `label`.
- **`auth/status_update` notification.** `AuthStatusUpdateNotification` (x-side client) has the same fields. Agents that advertise `auth.status` "MAY send it at any time after `initialize`, and SHOULD only send it when the reported status differs from the last one sent on the connection" (its `$def` description).
- **RFD (Draft, a proposal and not a requirement).** `docs/rfds/get-auth-state.mdx:291` (agent SHOULD advertise; client MUST check), `:293` (MUST be callable after `initialize`), `:295` (SHOULD be fast, else answer `unknown`), `:297` (MUST NOT modify state; MUST NOT reject with `-32000`), `:301` (SHOULD return `unknown` rather than guess), `:303` (accounts: MUST NOT include secrets), `:307` (update SHOULD be sent on change, connection-scoped). Status: "Accepted as a Draft RFD" (`:363`), rewritten 2026-10-29 (`:361-362`).
- **Rust SDK.** Wires both under the `unstable_auth_status` feature: `src/agent-client-protocol/src/schema/v2_impls.rs:214` (`auth/status` request), `:322` (`auth/status_update` notification), `src/agent-client-protocol/Cargo.toml:53,64` (acp-rust-sdk @ e75d6f19).

Proposed row:

- **Id:** ACP-AUTH-209. **Tier:** CAPABILITY. **Capability:** `capabilities.auth.status` (object marker; the default `capability_is_supported` handling).
- **Text:** "`auth/status` sent right after `initialize`, before any `auth/login`, returns a result that validates as `AuthStatusResponse`. It is never rejected with `-32000` (the agent MUST NOT auth-gate it) or `-32601` (the agent advertised it), and `state` is one of the defined `AuthState` values or begins with `_`."
- **Citation:** `schema/v2/schema.unstable.json#/$defs/AuthStatusRequest; #/$defs/AuthStatusResponse; #/$defs/AuthState; #/$defs/AgentAuthCapabilities/properties/status; docs/protocol/v2/draft/schema.mdx:143-144; docs/protocol/v2/draft/initialization.mdx:215-219; docs/protocol/v2/draft/authentication.mdx:193; docs/rfds/get-auth-state.mdx:293,297`.
- **Observation:** `handshake=False`, manual `initialize`, `skip_if_version_mismatch`. Do not log in even if `--auth-method` is given, so the unauthenticated case is the one exercised. Then send `auth/status {}`, run `validate_agent_response("auth/status", msg)`, and do the open-enum check with `is_valid_open_enum_value(state, {"authenticated","unauthenticated","not_required","unknown"})`. Safe: a pure query per `schema.mdx:144`. Calling it after `--auth-method` login is an optional second probe.
- **Why now:**
  - It is observable without credentials and has no side effects.
  - A CAPABILITY row only bites agents that opt in by advertising `auth.status`.
  - It follows the ACP-FORK-201/202 precedent for unstable, RFD-backed methods.
  - The vendored-schema refresh makes `auth/status`/`auth/status_update` known methods automatically (`tck.v2.protocol` derives its tables from meta), so ACP-CLIENTCAP-202 will already accept `auth/status_update`.
- **Why not (the case for deferral):** the feature is explicitly "may be removed or changed at any point", and the RFD was rewritten in this very window. A CAPABILITY FAIL affects the verdict. If you prefer deferral, put this whole row in the ledger as "unstable Draft RFD, revisit when stabilized".
- **Optional split:** keep the `state` open-enum check as its own row (ACP-AUTH-210) if you want a clearer failure attribution. Otherwise fold it in as above.
- **Fixtures:**
  - `auth_status_gated.py` advertises `capabilities.auth.status: {}` and one `agent` method, and answers `auth/status` with `-32000` until logged in. It should FAIL only AUTH-209.
  - Optionally `auth_status_unprefixed_state.py` (`state: "signed_in"`).
  - Extend `conforming_full.py`/`_base.py` with an `auth/status` handler (`{"state":"not_required"}` or an `authenticated` state that tracks `_authenticated`) and advertise `auth.status`, so the PASS path is covered.

### `--auth-method` / `--allow-logout` vs the new `authMethods` obligations

- **Trigger semantics match.** The plugin caches `authMethods` only if it is a list (`src/tck/common/plugin.py:332-334`). `login_if_needed` no-ops on an empty or absent list (`src/tck/v2/conformance/_helpers.py:145-152`). AUTH-203/204/205 gate on `init_result.get("authMethods") or []` truthiness. All of this is "non-empty list", which is the target trigger (`authentication.mdx:51-53`; `#/$defs/InitializeResponse/properties/authMethods`). The old "one or more *valid* entries" wording (base) is gone, so there is no longer a gap for lists of only-invalid entries. No change needed.
- **Client MUST NOTs the TCK observes.**
  - It never calls login/logout with empty `authMethods` (`:52-53`, `:248`).
  - It never sends a `terminal` `methodId` (`:176`, `:217-218`; `validate_login_method_id`, `_helpers.py:82-108`).
  - It never advertises `capabilities.auth.terminal` except on AUTH-207's dedicated connection, so "Clients ignore `terminal` methods they did not enable" (`:151`) holds.
- **Gap (pre-existing, made explicit).** `:47-49,159-161` and `schema.mdx:24-27`: the client sends `auth/login` only for a method "whose type defines that protocol-driven flow". `validate_login_method_id` blocks only `terminal`, so an operator-supplied `_custom`-type id is sent through.
  - Option A (recommended): leave it, and document that `--auth-method` is the operator vouching that the method uses `auth/login`. The TCK cannot know a custom type's semantics, and an agent that rejects it now answers `-32602` (`:191`), which SKIPs.
  - Option B: SKIP unless `type == "agent"`. This makes custom-type agents untestable behind auth.
- **Pending interactive logins (new text, `:179`).** "`auth/login` may stay pending while the user completes an interactive flow", e.g. the agent opens a browser. URL-mode elicitation is not available because the TCK advertises no `elicitation`, so a conforming agent must run the flow itself. Consequences:
  - `login_if_needed` waits `startup_timeout` and AUTH-203/204 wait `default_timeout`. An `AgentTimeout` there propagates as a **FAIL**, not an `AUTH-GATED` SKIP. Because `connected_agent` logs in on every connection, an operator whose method is interactive gets a FAIL on every session-dependent test.
  - Recommended follow-up (programmer, not a requirement): catch `AgentTimeout` on the embedded `auth/login` and SKIP with `AUTH-GATED:` plus a hint (a non-interactive method, or a larger `--timeout`). Also document that `--auth-method` should name a method that completes without user interaction, or one whose credentials persist across connections (`:179`: "Credentials are often stored where other connections can use them").
- **`--allow-logout` cross-test effect.** `:179` says credentials often outlive the connection, and AUTH-203 calls `auth/logout`. On agents that share stored credentials, every later test in the run may see auth gating, and the operator's real credentials may be revoked (the option's help text already warns about the latter). I found no ordering that runs AUTH-203 last (grep of `plugin.py`/`conftest.py`). Suggest a follow-up: order AUTH-203 last, or document the effect. This is pre-existing behaviour with sharper justification now.

### Spec map

- Neither `authentication.mdx` nor `elicitation.mdx` appears in `spec-tracker/maps/v2.toml`, so there are no section addresses to update.
- New subsections:
  - `authentication.mdx` "Terminal authentication > Launch safety" (`:220-224`): client-only SHOULDs. Do not make it core.
  - `elicitation.mdx` "Session cancellation" (`:219-245`, renamed from "Session Cancellation"): restates `prompt-lifecycle.mdx` cancellation and `session-setup.mdx:391` (session/close cancels pending elicitations). Both docs are already core. Do not make it core.
- `authentication.mdx` "Advertising authentication" restates core `initialization.mdx:82,84`, so the core doc already carries the rule.

## Testability notes

- AUTH-201/202/206/207: from the `initialize` result alone, as today.
- AUTH-208: a conforming agent answers `-32602`. Non-conforming agents answer `{}` (they accept any id), `-32000`, `-32603`, or `-32601` (the last one also violates the "MUST implement" rule).
- AUTH-209: a conforming agent answers `{"state": "unauthenticated"}` (or another defined value) before login. Non-conforming agents answer `-32000`, `-32601` while advertising, return a missing or invalid `state`, or return `state:"signed_in"`.
- **Not observable:**
  - The `-32000` "login failed/abandoned" path (needs a controllable failing user).
  - The `-32800` cancelled-login path (it would start a real interactive login; unsafe).
  - "MUST NOT modify any agent state" for `auth/status`.
  - Every elicitation agent-side behaviour. The TCK advertises no elicitation mode, so a conforming agent never sends `elicitation/create`. Exercising these would need a connection advertising `form`/`url` and an operator-supplied prompt that deterministically triggers an elicitation, a new `--elicitation-prompt`-style option analogous to `--cancel-prompt`. That is a design decision, not a slice (see Open questions).

## Ledger (new deliberate non-requirements)

All citations are `@ 3961af94fa62`.

| # | Citation | Statement | Reason |
|---|----------|-----------|--------|
| L1 | `docs/protocol/v2/draft/authentication.mdx:191` | A failed or abandoned `auth/login` is answered `-32000`. | Not observable: needs a controllable failing or abandoning user. |
| L2 | `docs/protocol/v2/draft/authentication.mdx:191` | An `auth/login` cancelled with `$/cancel_request` is answered `-32800`. | Unsafe: needs a valid advertised method and starts a real interactive login on the operator's agent. |
| L3 | `docs/protocol/v2/draft/authentication.mdx:212-214` | Agents SHOULD provide terminal `args` that enter a login-only flow and exit when it completes. | Out of scope: terminal auth is an out-of-band, client-side relaunch the TCK does not drive. |
| L4 | `docs/protocol/v2/draft/authentication.mdx:224` | Terminal-method `env` values SHOULD NOT contain secrets. | Not observable: the TCK cannot tell whether a value is a secret. |
| L5 | `docs/protocol/v2/draft/authentication.mdx:232-236` | After insertion, an auth failure still gets a successful `messageId` response, the agent MUST report `idle`, and it SHOULD use `stopReason:"error"` with `-32000`. | Not triggerable: needs auth to fail mid-turn. The general insertion/idle rules are covered by the prompt-lifecycle rows. |
| L6 | `docs/protocol/v2/draft/authentication.mdx:270-277` | After `auth/logout`, auth-gated requests require authentication again; what happens to active sessions is unspecified. | Destructive (needs `--allow-logout`) and gating is only a MAY (`schema.mdx:954`). |
| L7 | `schema/v2/schema.unstable.json#/$defs/AuthStatusRequest`; `docs/protocol/v2/draft/schema.mdx:144` | `auth/status` MUST NOT change any agent state. | Not observable from the client side in general. |
| L8 | `schema/v2/schema.unstable.json#/$defs/AuthStatusUpdateNotification` | `auth/status_update` SHOULD be sent only when the status differs from the last one sent on the connection, and only by agents advertising `auth.status`. | Not triggerable: the TCK cannot cause an auth-state change except by a destructive logout. Unstable. |
| L9 | `docs/protocol/v2/draft/elicitation.mdx:56` | Agents MUST NOT request a mode the client has not advertised (the partial-mode case: e.g. `url` when only `form` is advertised). | Not triggerable. ACP-CLIENTCAP-201 covers only the zero-modes case. |
| L10 | `docs/protocol/v2/draft/elicitation.mdx:67-74` | Exactly one of `sessionId`/`requestId`. `requestId` MUST name a pending client-to-agent request on the same connection. | Not triggerable. Shape is schema-enforced (`oneOf`) wherever it is observed. |
| L11 | `docs/protocol/v2/draft/elicitation.mdx:76-77` | The agent MUST cancel pending request-scoped elicitations before responding to their request. | Not triggerable. |
| L12 | `docs/protocol/v2/draft/elicitation.mdx:157-163,186-187,255-256,268` | Form mode MUST NOT request secrets; sensitive data uses URL mode; no fallback to form; no credentials over ACP or in the URL; user/connection binding of completion. | Not observable: semantic or out-of-band. |
| L13 | `docs/protocol/v2/draft/elicitation.mdx:197` | Agents MUST handle an unknown response action as `cancel`. | Not triggerable, and "handled as cancel" is only weakly observable. |
| L14 | `docs/protocol/v2/draft/elicitation.mdx:211-216` | `elicitationId` is unique among outstanding URL elicitations; `elicitation/complete` goes only to the originating client and carries the original id. | Not triggerable. |
| L15 | `docs/protocol/v2/draft/elicitation.mdx:233` (restates `session-setup.mdx:391`) | Before responding to `session/close`, the agent MUST cancel every pending elicitation scoped to that session. | Not triggerable for elicitation. The permission-request half of `session-setup.mdx:391` *is* observable; route it to the session-setup owner. |
| L16 | `docs/protocol/v2/draft/elicitation.mdx:54` | An agent forwarding elicitation to an MCP server MUST NOT copy the client's capability object unchanged. | Out of scope: it is the agent<->MCP side and needs a TCK-supplied MCP server. |

Skipped as client-side or pure prose that nobody would expect the TCK to test: the Launch safety client bullets (`authentication.mdx:222-224` client parts), the terminal reconnect SHOULD/MAY (`:209`), the elicitation UI rules (`elicitation.mdx:17-22,144-155,259-267`), and the client `-32601`/`-32602` responses (`:59`, which the mock client already follows).

## Discrepancies

- **RFD vs schema/doc naming for `auth/status`.** `docs/rfds/get-auth-state.mdx` examples use v1 shapes (`agentCapabilities.auth.status`, `"protocolVersion": 1`, `authenticate`). The v2 schema and docs use `capabilities.auth.status` and `auth/login` (`initialization.mdx:215`). The schema is authoritative for shape; cite the RFD only for intent.
- **v1 model vs v1 JSON schema.** The spec repo's Rust model has a v1 `AuthStatusRequest` (`agent-client-protocol-schema/src/v1/agent.rs:468`, feature `unstable_auth_status`, `agent-client-protocol-schema/Cargo.toml:30,46`), and the Rust SDK wires a v1 `auth/status` (`src/agent-client-protocol/src/schema/client_to_agent/requests.rs:7,46`). But `schema/v1/schema.unstable.json` at target contains no `AuthStatus` `$def` (grep count 0). This matters to the v1 researcher, not here.
- **`auth/login` with an unadvertised id: client MUST vs defined agent error.** `schema.mdx:24-27` restricts clients to login-flow method types, yet `authentication.mdx:191` defines the agent's `-32602` answer. This is not a contradiction, but it bears on whether ACP-AUTH-208's probe is acceptable (see its DECISION).
- **`:193` vs `:191`.** `auth/login` is listed as exempt from `auth_required`, yet `:191` uses `-32000` for a failed login. These read consistently as "not gated, but can fail". The `error.mdx:34` description ("or an `auth/login` attempt failed") confirms that reading.

## Open questions

1. **Elicitation coverage design** (orchestrator/user): add an opt-in `--elicitation-prompt` plus a connection advertising `form`/`url`, so the L9-L15 MUSTs become opportunistic CAPABILITY rows (SKIP if no elicitation arrives)? Until then they stay in the ledger.
2. The **`session/close` cancels pending permission requests** half of `session-setup.mdx:391` is observable with the existing permission machinery. Route it to whoever owns `session-setup.mdx`.
3. The **v1 `auth/status`** schema/model mismatch above: route to the v1 researcher.
4. **Pending-login timeout** handling in `login_if_needed`/AUTH-203/204 and AUTH-203 ordering: programmer follow-ups (not requirement changes).
5. A possible plugin follow-up: when `auth.status` is advertised and returns `unauthenticated` with no `--auth-method`, give a clearer `AUTH-GATED` diagnostic. This is a design idea only.
