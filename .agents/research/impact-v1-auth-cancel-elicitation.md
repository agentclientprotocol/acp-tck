# v1 impact: authentication.mdx, cancellation.mdx, elicitation.mdx, and unstable `auth/status`

**Sources checked:** agent-client-protocol (worktree `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`)
base `beac4ba96190` -> target `3961af94fa62` (read via `git show`/`git diff`, not pulled);
acp-rust-sdk @ `e75d6f1` (2026-11-09, `pull --ff-only`: already up to date). Python SDK not consulted
(nothing here depends on runtime behavior the spec leaves implicit).
**Confidence:** high for the classification of existing rows (the doc diffs are small and fully read);
medium for the proposed `auth/status` rows (the backing is an UNSTABLE schema plus a Draft RFD that was
rewritten two weeks before target).

## Summary table

| Id | Classification | Note |
|----|----------------|------|
| ACP-AUTH-001 | unchanged | Schema-only citation. `AuthMethod*.id` descriptions unchanged; only `description`/`_meta` wording changed. |
| ACP-AUTH-002 | unchanged | `authentication.mdx:126-128` and `initialization.mdx:123-127` untouched. The `AuthMethodTerminal` MUST changed punctuation only. |
| ACP-AUTH-003 | citation-only, **Needs review** | `authentication.mdx:136-167` overlaps hunk `-153` (bold added to an existing MUST NOT). Correct target range is still `136-167`. `187-188` unchanged. |
| ACP-AUTH-004 | citation-only, **Needs review** | `authentication.mdx:190-213` overlaps hunk `-190,1 +190,7` (new "Launch safety" block in front of the recased `## Logging out`). Correct target range: `196-219`. `74-76` unchanged. |
| ACP-AUTH-005 | unchanged | `authentication.mdx:46-48` untouched (the heading recase at 44 is outside the range). |
| ACP-AUTH-006 | unchanged (flag) | Citations untouched. `AuthMethodTerminal.args`/`env` gained `x-deserialize-default-on-null`. Strict validation still rejects `null`, which is a cross-cutting policy question (see Open questions). |
| ACP-JSONRPC-006 | citation-only, **Needs review** | `cancellation.mdx:12-14` overlaps hunks at 12 and 14 (rewording only). Range stays `12-14`, meaning unchanged. |
| ACP-JSONRPC-007 | citation-only, **Needs review**; DECISION NEEDED on text | `cancellation.mdx:16-22` overlaps hunk `-21`. Range stays `16-22`. Line 21 now gives `session/prompt` + `cancelled` stop reason as the example of a valid response. Recommend: keep the assertions and optionally update the text. |
| ACP-CANCEL-001 | citation-only (mechanical) | Cites `prompt-turn.mdx`, not cancellation.mdx. `618,625` -> `645,652`. `--fix` does this automatically. |
| ACP-CANCEL-002 | citation-only (mechanical) | `prompt-turn.mdx:38,629` -> `38,656`. `--fix` does this automatically. |
| ACP-CLIENTCAP-003 | unchanged | `elicitation.mdx:40-47,54` and `initialization.mdx:160-166` untouched. elicitation.mdx edits are punctuation only. |
| ACP-LOGOUT-*, ACP-ELICIT-* | n/a | No such ids exist. |
| *new* ACP-AUTH-007 | new, CAPABILITY `agentCapabilities.auth.status`, **DECISION NEEDED** | `auth/status` on a fresh, unauthenticated connection succeeds with a schema-valid `AuthStatusResponse`. It is never `-32000`. |
| *new* ACP-AUTH-008 | new, ADVISORY, gated on the same capability, **DECISION NEEDED** | `state` is one of the four defined values or `_`-prefixed. |
| ledger L1-L5 | new deliberate non-requirements | `auth/status` has no side effects; `accounts` carry no secrets; `auth/status` is fast or answers `unknown`; send `auth/status_update` after state change; terminal `env` values carry no secrets. |

**Overall DECISION NEEDED (auth/status): recommend adding AUTH-007 and AUTH-008 now as capability-gated rows, and putting
the remaining RFD-only behavior in the ledger.** The rationale is in "auth/status" below.

## Details: existing rows

### ACP-AUTH-003 (Needs review, numbers unchanged)
- The only change inside `136-167` is target line 153: `Clients MUST NOT pass` became `Clients **MUST NOT** pass`.
  This is emphasis only (`docs/protocol/v1/draft/authentication.mdx:151-154 @ 3961af94fa62`).
- `187-188` ("Client **MUST NOT** send an `authenticate` request for a terminal method") is byte-identical
  (`authentication.mdx:186-188`).
- The Terminal-authentication step list changed from "4. Reconnects and reinitializes" to "4. On success, reconnects and
  reinitializes" (`authentication.mdx:180`). This is a client-side flow that the TCK never runs. It does not affect AUTH-003.
- `src/tck/v1/conformance/_helpers.py:86` docstring cites `authentication.mdx:153,187-188`. Both line numbers are still
  correct at target. `--fix` does not touch docstrings, and none is needed here.
- Test `test_authenticate_then_session_new_succeeds` still matches the text. Action: leave the citation as written when
  `--fix` lists it under Needs review.

### ACP-AUTH-004 (Needs review, new range 196-219)
- Base 190-213 = `## Logging Out` through the empty-result example. At target that is `## Logging out` (196) through
  the closing fence (219) (`authentication.mdx:196-219 @ 3961af94fa62`). Hand-fix `190-213` -> `196-219`.
- Text is unchanged apart from the heading case. The `#logging-out` anchor slug is unchanged.
  The test (`test_logout_succeeds`, object result) still matches.
- The "Active sessions" section (`authentication.mdx:224-232`, recased only) still says the post-logout session behavior is
  unspecified. That is consistent with the row's "nothing asserted after logout".

### ACP-AUTH-006 (unchanged, flagged)
- The base->target diff of `$defs/AuthMethodTerminal` adds `"x-deserialize-default-on-null": true` on `args` (type `array`)
  and `env` (type `object`). It also makes punctuation edits to the description.
- JSON Schema types are unchanged, so the vendored-schema validator still rejects `"args": null`. The hint says a receiver
  should deserialize null as the default.
- `src/tck/v1/validation.py` has no carve-out for any `x-deserialize-*` hint. `x-deserialize-skip-invalid-items`
  appears 23 times in the base vendored schema already, so strict validation is the existing policy.
- No change is proposed here. This is the same cross-cutting question other `x-deserialize-default-on-null` fields raise
  (SESSION-003/LOAD-001/...), so it should be decided once (see Open questions).

### ACP-JSONRPC-006 (Needs review, unchanged)
- Line 12 "In order to provide a consistent approach" became "To make cancellation consistent". Line 14 "Cancellation will remain
  optional" became "Cancellation remains optional" (`cancellation.mdx:12-14 @ 3961af94fa62`).
- Meaning is unchanged, and the "connection stays usable" assertion is unaffected.
- `$defs/CancelRequestNotification` changed only its doc link.

### ACP-JSONRPC-007 (Needs review; DECISION NEEDED on text, recommend keep assertions)
- Base line 21: "A valid response with appropriate data (such as partial results or cancellation marker)".
- Target line 21: "A valid response with appropriate data, such as `session/prompt` with the `cancelled` stop reason or
  `session/request_permission` with the `cancelled` outcome" (`cancellation.mdx:20-22 @ 3961af94fa62`).
- This could be read as narrowing a valid `session/prompt` response after `$/cancel_request` to `stopReason: "cancelled"`.
  **Recommendation: do not tighten.** Reasons:
  1. The bullet list applies to "a supporting implementation" (`cancellation.mdx:16`), and support is optional
     (`cancellation.mdx:14`). The TCK cannot tell a non-supporting agent, which legitimately ends with `end_turn`, from a
     supporting one.
  2. "such as" introduces examples, not a closed list.
  3. The hard `cancelled` MUST for `session/prompt` is tied to `session/cancel` (`prompt-turn.mdx:645,652`), which
     ACP-CANCEL-001 already covers.
- The test already prefers `cancelled`: a non-`cancelled` result inside the race window SKIPs
  (`test_jsonrpc.py:266-270`), and later ones PASS.
- Optional text tweak, for clarity only: "...a schema-valid `PromptResponse` result (the spec's example is
  `stopReason: "cancelled"`, but any valid result passes because support is optional)...". No test change.
- The new `session/request_permission` example is a response the *client* writes. The mock client already answers
  pending permission requests with `cancelled` once a cancel has fired (`_helpers.py:403-412`), so nothing changes.

### ACP-CANCEL-001 / 002 (mechanical remap)
- These rows cite `prompt-turn.mdx`, not cancellation.mdx. The cited text is identical at target:
  - base 618 -> 645, 625 -> 652, 629 -> 656 (`docs/protocol/v1/draft/prompt-turn.mdx:645,652,656 @ 3961af94fa62`);
  - 38 -> 38 (unchanged).
- spec-impact lists both as "Not affected", so `--fix` remaps them without review. Tests are unaffected.
- cancellation.mdx:42 still states the client-side "answer pending permission requests with `cancelled`" MUST (reworded only).

### ACP-CLIENTCAP-003 (unchanged)
- elicitation.mdx hunks (`-60`, `-111`, `-145,2`) only replace semicolons with full stops. The `content`-on-`accept` sentence
  at `elicitation.mdx:145-147` is split but keeps the same meaning.
- Cited `40-47,54` are byte-identical (`elicitation.mdx:40-55 @ 3961af94fa62`). No ELICIT rows exist, and nothing new
  is observable from the client side.

### authentication.mdx "Launch safety" (`authentication.mdx:190-194 @ 3961af94fa62`)
All of it is client-side behavior for the terminal-auth launch, which the TCK never performs (see the AUTH-006 text):
- pass `args` as separate argv and do not offer terminal auth when the launch target re-parses arguments (SHOULD/SHOULD NOT);
- do not apply lookup-, loader-, startup-, proxy- or TLS-changing `env` without approval (SHOULD NOT);
- show `args`/`env` before launch (SHOULD).

No requirement is proposed. The one agent-authored clause is "`env` values **SHOULD NOT** contain secrets" (line 194):
the Agent writes the `AuthMethodTerminal.env` map. It is unobservable because the TCK cannot classify a value as secret,
so it goes to the ledger (L5).

`security.mdx:66` links to `#launch-safety` as feature guidance only and adds no rule.

## auth/status (unstable): DECISION NEEDED

### What the sources say
- **Draft doc:** `initialization.mdx:300-305 @ 3961af94fa62`. Under Authentication capabilities, `status`
  (`AuthStatusCapabilities`) is "**Unstable.** The `auth/status` method and the `auth/status_update` notification are
  available. Omitted or `null` both mean the Agent does not advertise support. Supplying an empty object means the Agent
  supports them." This is the only draft-doc text; authentication.mdx does not mention `auth/status`.
- **Schema** (`schema/v1/schema.unstable.json @ 3961af94fa62`; every def is marked `**UNSTABLE** ... may be removed or changed
  at any point`):
  - `#/$defs/AgentAuthCapabilities/properties/status`: `AuthStatusCapabilities | null`, with `x-deserialize-default-on-error`.
  - `#/$defs/AuthStatusRequest`: `x-side: agent`, `x-method: auth/status`. `{_meta?}`. Its description says: "Agents MUST
    NOT reject it with `auth_required` (`-32000`), since Clients call it to learn whether authentication is required."
    Wired at `#/$defs/ClientRequest/properties/params/anyOf/0/anyOf/6`.
  - `#/$defs/AuthStatusResponse`: `required: ["state"]`; `accounts?: AuthAccount[]` (`x-deserialize-skip-invalid-items`);
    `_meta?`. Wired at `#/$defs/AgentResponse/anyOf/0/properties/result/anyOf/6`.
  - `#/$defs/AuthState`: `anyOf` of the consts `authenticated` | `unauthenticated` | `not_required` | `unknown`, plus an
    open `string` ("Values beginning with `_` are reserved for implementation-specific extensions. Unknown values that do
    not begin with `_` are reserved for future ACP variants.").
  - `#/$defs/AuthAccount`: `required: ["label"]`; `active`/`name`/`email`/`organization` nullable. Clients MUST NOT use
    these as identifiers and SHOULD NOT log them.
  - `#/$defs/AuthStatusUpdateNotification`: `x-side: client`, `x-method: auth/status_update`. Same fields as the response,
    `state` required. "Agents that advertise the `auth.status` capability MAY send it at any time after `initialize`, and
    SHOULD only send it when the reported status differs from the last one sent on the connection." Wired at
    `#/$defs/AgentNotification/properties/params/anyOf/0/anyOf/2`.
- **RFD** `docs/rfds/get-auth-state.mdx @ 3961af94fa62`. Status is Draft, and RFD text is a proposal, not a requirement.
  Behavior section, lines 291-307:
  - 291: the agent SHOULD advertise `auth.status` if supported; clients MUST check it before calling.
  - 293: `auth/status` "MUST be callable after `initialize`", and MAY be called multiple times.
  - 295: SHOULD be fast; if a check would block, SHOULD answer `unknown` and follow up with `auth/status_update`.
  - 297: "MUST NOT modify any agent state"; MUST NOT reject with `-32000`.
  - 301: SHOULD return `unknown` rather than guess.
  - 303: `accounts` is for display; "Agents MUST NOT include secrets".
  - 307: MAY send `auth/status_update` at any time after `initialize`; SHOULD send it when status changes, including after
    `authenticate`/`logout`; SHOULD only send it on a difference; the notification is connection-scoped.
  - 187: receivers ignore malformed `accounts` values.
  - Revision history (361-362): the shape was rewritten on 2026-10-29, from boolean capability and `authenticated`/`message`
    to an object capability and `state`/`accounts`.
- **Rust SDK** @ `e75d6f1`: wire types only, behind cargo feature `unstable_auth_status`
  (`src/agent-client-protocol/Cargo.toml:64`; `src/agent-client-protocol/src/schema/agent_to_client/notifications.rs:7-11`).
  Round-trip tests only (`src/agent-client-protocol/tests/schema_1_15.rs:39-59`). There is no runtime behavior, such as
  gating or defaults, to compare against.

### Options
- **A (recommended): add two capability-gated rows now** (AUTH-007, AUTH-008 below), and put the rest in the ledger.
  - Precedent: the registry already has CAPABILITY rows for features that were UNSTABLE at base: ACP-SYSPROMPT-001..003,
    ACP-CLIENTCAP-006 (`PlanCapabilities`) and ACP-CLIENTCAP-007 (which cites an RFD).
  - CLAUDE.md: the TCK verifies against the unstable superset, where RFD-gated methods are "optional for agents, but any an
    agent uses are validated".
  - The rows only run when the agent advertises `auth.status`, so they cannot hurt agents that don't. A CAPABILITY SKIP
    never affects the verdict.
  - The `-32000` MUST is in the schema itself, not only in the RFD.
- **B: ledger only, defer.** The RFD was rewritten on 2026-10-29 and the schema says "may be removed or changed at any
  point", so a row may churn on the next update. Agents implementing the earlier RFD revision would send `auth.status: true`
  (a boolean). That would already FAIL ACP-SCHEMA-001/INIT-001 under strict validation, whatever is decided here.
- Consistency note: the same choice comes up for `session/status`, `session/archive`, `session/set_title` and `proxy/*`
  in this update. Whichever option is chosen should be applied to all of them.

### Proposed new rows (option A)

**ACP-AUTH-007**: Tier CAPABILITY, `capability="agentCapabilities.auth.status"` (object marker, default
`capability_is_supported`).
- Text: "When `agentCapabilities.auth.status` is advertised, `auth/status` sent with `{}` params right after `initialize`,
  before any `authenticate` on the connection, returns a result that validates against `AuthStatusResponse` (an object with
  a string `state`). It is never an error, and in particular never `-32000` (authentication required)."
- Tier justification:
  - The capability doc says supplying `{}` "means the Agent supports" the method (`initialization.mdx:303-304`). This is the
    same basis as ACP-AUTH-004's "`logout` succeeds".
  - The schema MUST NOT for `-32000` (`#/$defs/AuthStatusRequest`).
  - The RFD MUST "callable after `initialize`" (`get-auth-state.mdx:293`, proposal).
  - It is not MANDATORY because the method is opt-in.
- Citation:
  - `docs/protocol/v1/draft/initialization.mdx:300-305 @ 3961af94fa62`
  - `schema/v1/schema.unstable.json#/$defs/AgentAuthCapabilities/properties/status`
  - `schema/v1/schema.unstable.json#/$defs/AuthStatusRequest`
  - `schema/v1/schema.unstable.json#/$defs/AuthStatusResponse`
  - `docs/rfds/get-auth-state.mdx:293,297 @ 3961af94fa62`
- How a client-side TCK observes it:
  - Spawn a fresh connection and send `initialize` with `clientCapabilities: {}`. Do **not** let `connected_agent`
    auto-`authenticate`: it does so whenever `--tck-auth-method` is set (`_helpers.py:55-79`). Use `handshake=False` with
    the test's own `initialize`, or a new opt-out.
  - Send `auth/status` with `{}` and assert there is a `result`, and that `validate_agent_response("auth/status", msg)` is
    clean. The method tables are derived from the schema, so this works once the schema is re-vendored.
  - On `error.code == -32000`, fail with a specific message. This row must not route through `skip_if_auth_gated`/
    `AUTH-GATED:`, since this method exists precisely so it is answerable while unauthenticated.
  - Optional extra: when `--tck-auth-method` is given, call `auth/status` again after a successful `authenticate` and apply
    the same assertions (RFD 293: "MAY be called multiple times").
  - Malformed `accounts` entries fail through schema validation. This is consistent with current strict policy, but see
    Open questions: the RFD says receivers skip them (line 187).
- Suggested fixtures, each trips only AUTH-007:
  - `auth_status_auth_required.py`: conforming baseline plus `auth: {status: {}}`, answers `auth/status` with `-32000`.
  - `auth_status_missing_state.py`: answers `{"accounts": []}`.
- The conforming baseline fixture should advertise `auth.status` and answer `{"state": "not_required"}`, so that
  AUTH-007/008 have PASS evidence.

**ACP-AUTH-008**: Tier ADVISORY, gated on `agentCapabilities.auth.status`.
- Text: "When `auth.status` is advertised, the `state` in the `auth/status` result (and in any observed
  `auth/status_update`) is one of `authenticated`, `unauthenticated`, `not_required`, `unknown`, or begins with `_`.
  Other strings are reserved for future ACP variants."
- Tier justification:
  - The schema reserves non-`_` unknown values but states no MUST (`#/$defs/AuthState`, the `other` branch). Any string
    passes JSON Schema, so ACP-SCHEMA-001/AUTH-007 cannot catch it.
  - This mirrors the `_`-prefix extensibility convention. Hence ADVISORY, not MANDATORY.
- Citation: `schema/v1/schema.unstable.json#/$defs/AuthState`; `docs/rfds/get-auth-state.mdx:154-164 @ 3961af94fa62`.
- Observation: piggy-back on the AUTH-007 test's result. A separate test id is not needed.
- Fixture: `auth_status_unreserved_state.py` answers `{"state": "logged_in"}`. It FAILs AUTH-008 only, ADVISORY, so the
  verdict stays CONFORMANT.
- If the orchestrator prefers fewer rows, this check can be dropped (spec-silent) or demoted to INFORMATIONAL.

`auth/status_update` shape needs no row of its own: it is in the schema's `AgentNotification` union, so any instance an
agent emits is validated by the generic agent-message validation once the schema is vendored. The mock client in
`run_prompt` already ignores unknown agent notifications (`_helpers.py:428-430`).

### Ledger entries (both options)
`spec-tracker/maps/v1.toml` `[[not_requirement]]`, citations `@ 3961af94fa62`:

| # | citation | statement | reason |
|---|----------|-----------|--------|
| L1 | `docs/rfds/get-auth-state.mdx:297` | Calling `auth/status` MUST NOT modify any agent state. | unobservable: a client cannot enumerate agent state. RFD-only (Draft). |
| L2 | `docs/rfds/get-auth-state.mdx:303` | `auth/status` `accounts` MUST NOT include secrets. | unobservable: the TCK cannot tell a secret from a label. |
| L3 | `docs/rfds/get-auth-state.mdx:295,301` | Agents SHOULD answer `auth/status` quickly, returning `unknown` and a later `auth/status_update` rather than blocking or guessing. | not reliably observable: timing is environment-dependent, and "guessing" is internal. |
| L4 | `docs/rfds/get-auth-state.mdx:307` and `schema/v1/schema.unstable.json#/$defs/AuthStatusUpdateNotification` | Agents SHOULD send `auth/status_update` when their status changes (including after `authenticate`/`logout`), and only when it differs from the last one sent. | out of scope for now: RFD-only SHOULD; needs a live credential change (`--auth-method`, or the destructive `--allow-logout`); a real agent may already be authenticated, so no change may occur. Revisit if the RFD stabilizes. |
| L5 | `docs/protocol/v1/draft/authentication.mdx:194` | Terminal auth method `env` values SHOULD NOT contain secrets. | unobservable: the TCK cannot classify values as secret. The other launch-safety bullets (190-194) are client-side. |

Client-only rules (Launch safety clauses for the client, the RFD's "Clients MUST check the capability" and "MUST treat
unknown `state` as `unknown`", the `AuthAccount` "MUST NOT use as identifiers / SHOULD NOT log") need no ledger entries.
The TCK's capability gate already makes it obey the "check before calling" rule.

## Testability notes
- AUTH-007 is the only row that needs new harness behavior: a way to open a connection without the auto-`authenticate`.
  Everything else reuses `validate_agent_response` and `capability_is_supported`.
- A conforming agent advertises `auth: {status: {}}` and answers `{"state": "<one of four>"}` even when it would gate
  `session/new` behind `-32000`.
- A non-conforming agent does one of: advertises `auth.status` but answers `-32601`, `-32000`, or another error; omits
  `state`; or sends a non-string `state`.
- Sending `auth/status_update` without advertising `auth.status` is not judged, because the spec is silent (see Open
  questions).

## Discrepancies
- `x-deserialize-default-on-null` (on `AuthMethodTerminal.args/env`, new at target) and `x-deserialize-skip-invalid-items`
  (on `AuthStatusResponse.accounts`, and RFD line 187 "a receiver ignores a malformed value") document receiver tolerance
  that the JSON Schema types do not express. The TCK validates strictly. This is not a spec-vs-SDK conflict but a schema
  annotation vs JSON Schema type mismatch.
- The RFD calls the `auth.status` advertisement a SHOULD for supporting agents (`get-auth-state.mdx:291`). The draft doc and
  schema make it the sole signal, since "omitted or `null` means not advertised" (`initialization.mdx:302-303`). No
  conflict for the TCK: it only calls the method when the capability is advertised.

## Open questions
1. Cross-cutting (route to whoever owns the schema/validation slice): should `tck.v1.validation` honor
   `x-deserialize-default-on-null` (accept `null`) or `x-deserialize-skip-invalid-items`? This affects AUTH-006, AUTH-007,
   SESSION-003, LOAD-001, ADDDIRS-001 and others. The current behavior is strict.
2. Should the add-now-or-defer decision for unstable methods be made once for `auth/status`, `session/status`,
   `session/archive`, `session/set_title` and `proxy/*`?
3. Spec silent: may an agent send `auth/status_update` without advertising `auth.status`? The schema text addresses only
   agents that do advertise it. If the orchestrator wants coverage, an INFORMATIONAL row would fit. No requirement is
   recommended.
4. `initialization.mdx:123-127` (AUTH-002/006) and `prompt-turn.mdx` (CANCEL-*) belong to other researchers' docs. The
   line facts above are verified, but those owners should confirm nothing else in their hunks affects these rows.
