# Impact research (v1): authentication.mdx, elicitation.mdx, security.mdx, get-auth-state RFD

**Sources checked:** agent-client-protocol @ `3ea94133` (read with `git show 3ea94133:<path>`; the checkout's HEAD
`6ace4f6a` descends from it and has no diff in these files), base `3961af94`. Files:
`docs/protocol/v1/draft/{authentication,elicitation,security,initialization,session-setup}.mdx`,
`docs/rfds/get-auth-state.mdx` (Draft RFD at both revisions: `docs/docs.json` group `Draft`),
`schema/v1/schema.unstable.json` (`$defs` compared programmatically). TCK: `src/tck/v1/requirements.py`,
`spec-tracker/maps/v1.toml`, `src/tck/v1/conformance/test_authentication.py`, `src/tck/v1/validation.py`.
Reference SDKs not consulted: no affected rule depends on runtime behaviour the spec leaves implicit.
**Confidence:** high. The three docs have no diff, and the RFD and schema changes are small and fully read.

## What changed upstream (relevant to this slice)
- `authentication.mdx`, `elicitation.mdx`, `security.mdx`: **no diff** (`git diff --stat 3961af94..3ea94133` empty).
- `docs/rfds/get-auth-state.mdx` (Draft RFD), +27 lines:
  - `AuthAccount.description?: string | null`, "Never contains credentials" (`:173-177`).
  - The `state` comment now reads "Clients use this field to decide whether sign-in is needed" instead of "The only
    field clients act on" (`:139-140`). This is client-side wording.
  - New Behavior item 10 (`:315`): a Client MAY re-check cached outcomes when the snapshot changes. This is a
    client-side MAY.
  - FAQ and revision history (`:342`, `:351-357`, `:377`). These are non-normative.
  - Line shift: every line after `:172` moves +5, and every line after `:248` moves +6 (so Behavior `:291-307`
    becomes `:297-313`).
- `schema/v1/schema.unstable.json`:
  - `AuthAccount` gains `properties.description`, `type: ["string","null"]`, `x-deserialize-default-on-error`.
    Its description reads "MUST NOT contain credentials".
  - `AuthStatusResponse.properties.state` and `AuthStatusUpdateNotification.properties.state` get the same rewording.
  - No other `Auth*`, `Logout*` or `Elicitation*` `$def` changed. `AgentAuthCapabilities`, `AuthStatusRequest`,
    `AuthMethod*`, `ClientCapabilities` and `ElicitationCapabilities` are identical.
- `initialization.mdx`: a +76 hunk at `@@ -241` moves the `auth.status` field from `:300-304` to `:376-380`. Cited
  lines `:123-127` and `:160-166` sit before the hunk and are unchanged.

## authentication.mdx (and the auth rows citing linked docs)
| id / ledger | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-AUTH-002 | citation-only (revision bump) | `authentication.mdx:126-128`; `initialization.mdx:123-127`; schema `AuthMethodTerminal` | Text is identical. |
| ACP-AUTH-003 | citation-only (revision bump) | `authentication.mdx:136-167,187-188`; `session-setup.mdx:10` | `session-setup.mdx:10` is unchanged (its hunks start at `:147`). |
| ACP-AUTH-004 | citation-only (revision bump) | `authentication.mdx:74-76,196-219` | |
| ACP-AUTH-005 | citation-only (revision bump) | `authentication.mdx:46-48`; `session-setup.mdx:10`; schema `InitializeResponse/properties/authMethods` | The inventory hit is the `InitializeResponse` $ref closure via `SessionCapabilities`/`SessionOptionsCapabilities`, which is unrelated to auth. |
| ACP-AUTH-006 | citation-only (revision bump) | `initialization.mdx:123-127`; schema `AuthMethod`, `AuthMethodTerminal` | Does not cite authentication.mdx directly. Listed because it shares the initialization auth lines. |
| ACP-AUTH-001 | unchanged | schema `AuthMethodAgent/Terminal .../id` only | Out of scope (cites no doc of mine). Listed for completeness. |
| ledger `authentication.mdx:194` (terminal `env` SHOULD NOT contain secrets) | citation-only (revision bump) | `authentication.mdx:194` | Reason still holds. |

## get-auth-state RFD (Draft RFD) and the `auth/status` rows
| id / ledger | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-AUTH-007 | citation-only (line remap). The effective check widens via the schema refresh, with no text change. | `initialization.mdx:376-380` (was 300-304); schema `AgentAuthCapabilities/properties/status`, `AuthStatusRequest`, `AuthStatusResponse`; `docs/rfds/get-auth-state.mdx:299,303 (Draft RFD)` (was 293,297) | Tier stays CAPABILITY behind `agentCapabilities.auth.status`: the MUST is RFD-only, and the docs only say the method "is available". Once the vendored schema is refreshed, a non-string, non-null `accounts[*].description` fails this row. `validation.py:22-31` honours only `x-deserialize-default-on-null`, not `-default-on-error` or `-skip-invalid-items`, so an agent-authored bad value is a violation. That matches how `name`/`email` are treated today. No test change is needed beyond the re-vendor. A fixture or unit test for a bad `description` is optional. |
| ACP-AUTH-008 | citation-only (revision bump) | schema `AuthState` (unchanged); `docs/rfds/get-auth-state.mdx:160-161 (Draft RFD)` (unchanged lines) | |
| ledger "`auth/status` MUST NOT modify any agent state" | citation-only | `docs/rfds/get-auth-state.mdx:303 (Draft RFD)` (was 297) | Reason holds. |
| ledger "SHOULD advertise `auth.status`" | citation-only, plus a **reason flag** | `docs/rfds/get-auth-state.mdx:297 (Draft RFD)` (was 291) | The reason ends "...and the TCK only calls it when it is advertised", which is a TCK choice. The real blocker is the client rule on the same line: "Clients MUST check for this capability before calling the method" (`:297`). Probing an unadvertised `auth/status` would break that rule. Recommend rewording the reason to name the client MUST. |
| ledger "SHOULD list accounts / mark `active`" | citation-only | `docs/rfds/get-auth-state.mdx:309 (Draft RFD)` (was 303) | Reason holds. |
| ledger "`accounts` MUST NOT include secrets" | citation-only | `docs/rfds/get-auth-state.mdx:309 (Draft RFD)` (was 303) | Reason holds. See the new entry below for `description`. |
| ledger "SHOULD keep `auth/status` fast / return `unknown`" | citation-only | `docs/rfds/get-auth-state.mdx:301,307 (Draft RFD)` (was 295,301) | Reason holds. |
| ledger "SHOULD send `auth/status_update` on change" | citation-only (see Decisions, item 3) | `docs/rfds/get-auth-state.mdx:313 (Draft RFD)` (was 307) | Reason is "out of scope for now", not a TCK choice. But the rule is partly observable today with `--tck-auth-method`. |

## elicitation.mdx
| id / ledger | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-CLIENTCAP-003 | citation-only (revision bump) | `elicitation.mdx:40-47,54`; `initialization.mdx:160-166` | The capability semantics and the `{}`-advertises-no-modes rule are unchanged. |
| (no v1 ledger entries cite elicitation.mdx) | pre-existing gap, not caused by this update | see Decisions, item 4 | |

## security.mdx
| id / ledger | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-PERM-001 | citation-only (revision bump) | `security.mdx:12`; `tool-calls.mdx:247` | `tool-calls.mdx` hunks start at `:337`, so `:247` is unchanged. That doc belongs to another researcher. |
| ledger `security.mdx:13` (`clientInfo`/`agentInfo`) | citation-only (revision bump) | `security.mdx:13` | |
| ledger `security.mdx:38` (URIs in prompts) | citation-only (revision bump) | `security.mdx:38` | |
| ledger `security.mdx:42` (credentials in `_meta`) | citation-only (revision bump) | `security.mdx:42` | |
| ledger `security.mdx:47-49` (prompt injection) | citation-only (revision bump) | `security.mdx:47-49` | |
| ledger `security.mdx:57` (multi-user scoping) | citation-only (revision bump) | `security.mdx:57` | |
| `core_doc` transports reason mentions security.mdx | unchanged | n/a | |

security.mdx links to `session-setup#system-prompt` (`:51`). The changed `session-setup.mdx` hunk at `@@ -442` only adds
a new "Initial config option values" section after the system-prompt text, so this doc's rules are unaffected. That
new section belongs to the session-setup researcher.

## New requirements
None. The `AuthAccount.description` shape (`string | null`) is enforced automatically by ACP-AUTH-007's schema
validation, and by ACP-SCHEMA-001 for any `auth/status_update` seen in the basic exchange, once the vendored schema
is refreshed. A separate row would duplicate that check.

## New ledger entries
1. citation: `schema/v1/schema.unstable.json#/$defs/AuthAccount/properties/description; docs/rfds/get-auth-state.mdx:173-177 (Draft RFD) @ 3ea94133…`
   - statement: "An `auth/status` account's `description` MUST NOT contain credentials."
   - reason: "Not observable: the TCK cannot tell a credential from display text."
   - The schema is the primary source; the Draft RFD says "Never contains credentials". Only agent-side,
     non-MAY rules are added. Item 10 (`:315`) and the client rules in the `AuthAccount` description are left out
     under the ledger's agent-side-only rule.

## Decisions for the user
1. **`description` no-credentials rule: new entry or merged into the existing "`accounts` MUST NOT include secrets"
   entry?** Recommend a **separate entry** (above). Its primary source is the schema, while the existing entry is
   Draft-RFD-only, and the citation rules want the schema cited first where it states the rule.
2. **Reword the "SHOULD advertise `auth.status`" reason** so it rests on the client MUST at
   `get-auth-state.mdx:297 (Draft RFD)` ("Clients MUST check for this capability before calling the method")
   rather than on what the TCK chooses to call. Recommend: yes. This is a wording-only ledger change.
3. **"SHOULD send `auth/status_update` on change" (`:313`, Draft RFD) is observable today.** A test could:
   - send `auth/status` before authenticating on a connection run with `--tck-auth-method`;
   - then `authenticate`, then send `auth/status` again;
   - if the two `state`s differ, expect an `auth/status_update` with the new state before the second response or
     within a quiet period;
   - SKIP when the method is not advertised, no `--tck-auth-method` is given, `authenticate` errors, or the state
     is unchanged.

   It would be ADVISORY (RFD SHOULD), and the mock client must record unsolicited `auth/status_update`
   notifications. Neither the rule nor its observability changed in this update. Recommend: **keep the ledger
   entry for this update** and record it as a follow-up. Converting it is optional new scope.
4. **Pre-existing v1 gap: elicitation.mdx agent-side rules have no v1 ledger entries.** Unrecorded rules:
   - `:54-55` (no unadvertised mode, graceful fallback)
   - `:69-71` (bind to connection/user)
   - `:105-111` (no secrets in form mode, no form fallback)
   - `:134-135` (URL-mode credentials never over ACP)
   - `:151-153` (handle decline/cancel/failure)
   - `:158-163` (`elicitationId` unique, `elicitation/complete` only to the originating client)
   - `:177-178` (no credentials or personal data in the URL, HTTPS)
   - `:179-180` (no clickable URLs in form-mode fields)
   - `:190-191` (verify the completing user)

   v2 has equivalent entries (`spec-tracker/maps/v2.toml:358-393`). The text has not changed, so this update did
   not cause the gap, but `spec-impact` cannot tell "missed" from "not covered on purpose" here. Recommend: backfill
   the v1 ledger in a separate slice, re-deriving each reason for v1 rather than copying v2's. Many are Deferred:
   they need a mock client that advertises a mode and answers `elicitation/create`, and an agent that elicits,
   which no prompt can force. The secrets, URL and user-binding rules are not observable.

## Open questions (route elsewhere)
- v2 ledger header `spec-tracker/maps/v2.toml:358` ("coverage deferred: the TCK never advertises an elicitation
  mode") is worded as a TCK choice. The individual v2 entries do name real blockers. This is for the v2 researcher.
- The re-vendor of `schema.unstable.json` (schema slice) is a prerequisite for ACP-AUTH-007 to pick up
  `description`.
