# Impact: v2 `authentication.mdx` and `get-auth-state` RFD (3961af94 -> 3ea94133)

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read with
`git show 3ea94133:<path>`; the checkout's working tree is at `6ace4f6a`, whose `schema/v2/*.json` differ from the
target, so nothing was read from the working tree), diffed against `3961af94`. Files:
`docs/protocol/v2/draft/authentication.mdx` (whole), `docs/rfds/get-auth-state.mdx` (whole Behavior section and
all hunks), `schema/v2/schema.unstable.json` (`$defs` `AuthAccount`, `AuthStatusResponse`,
`AuthStatusUpdateNotification`, `LogoutAuthResponse` and every other auth `$def`, compared base vs target),
`docs/protocol/v2/draft/schema.mdx` (auth/status, AuthAccount, `session/new` lines),
`initialization.mdx`, `extensibility.mdx`, `overview.mdx`, and the diffs of linked docs `error.mdx`,
`security.mdx`, `session-setup.mdx` (none touch auth). `docs/docs.json` @ 3ea94133: `rfds/get-auth-state` is in the
**Draft** group (unchanged). TCK: `src/tck/v2/requirements.py` (ACP-AUTH-*), `spec-tracker/maps/v2.toml` (auth
ledger), `src/tck/v2/conformance/test_authentication.py`, `src/tck/v2/validation.py`. Reference SDKs were not
consulted: the new text is explicit and needs no runtime interpretation.

**Confidence:** high. The doc change is one added SHOULD sentence; the RFD changes add one display field plus
client-side text; every line mapping was checked by reading both revisions.

## What changed

- `authentication.mdx:273` (new, in "Logging out"): "Logging out is idempotent. If there is no authenticated state
  to end, for example because the Client already logged out, the Agent **SHOULD** respond with the same empty
  result." Lines 1-272 are byte-identical to the base, so no existing citation of this doc moves.
- `get-auth-state.mdx` (Draft RFD): new optional `AuthAccount.description` ("Never contains credentials",
  `:173-177`); example updated (`:249-250`); `state` comment reworded (`:139-140`, client-facing); new Behavior item
  10 (`:315`, Client MAY re-check cached outcomes, client-side only); FAQ additions (`:351-357`). Net +6 lines before
  the Behavior section, so every Behavior line moved by +6 (base 291..307 -> target 297..313).
- `schema/v2/schema.unstable.json`: `AuthAccount` gains `properties.description` (`["string","null"]`,
  `x-deserialize-default-on-error`), described "Short text shown with the label, such as the credential source ...
  MUST NOT contain credentials." (rendered at `schema.mdx:3043-3049`). `AuthStatusResponse` and
  `AuthStatusUpdateNotification` changed only in the `state` description text ("This is the only field clients
  should act on" -> "Clients use this field to decide whether sign-in is needed"), plus `AuthAccount` in their
  closure. `LogoutAuthResponse` and all other auth `$defs` are unchanged.

## Registry rows (`src/tck/v2/requirements.py`)

| id | classification | target citation (@ 3ea94133) | note |
|---|---|---|---|
| ACP-AUTH-001 | unchanged | `authentication.mdx:51`; `$defs/AuthMethod`, `AuthMethodId` | |
| ACP-AUTH-002 | unchanged | `authentication.mdx:149-151`; `$defs` unchanged | |
| ACP-AUTH-003 | unchanged | `authentication.mdx:51-53,87-88,191`; `$defs` unchanged | |
| ACP-AUTH-004 | unchanged (see decision D2) | `authentication.mdx:51-52,247-249`; `$defs` unchanged | New `:273` SHOULD bears on its standalone (no-login) path. |
| ACP-AUTH-005 | citation-only (co-cited doc) | `schema.mdx:990` (was `:954`); `authentication.mdx:193` | `schema.mdx:990` text identical ("May return an `auth_required` ..."). |
| ACP-AUTH-206 | citation-only (co-cited doc) | `authentication.mdx:87-89,118-120`; `extensibility.mdx:236-245` (was `:233-242`) | |
| ACP-AUTH-006 | unchanged | `authentication.mdx:203-205`; `$defs` unchanged | |
| ACP-AUTH-208 | unchanged | `authentication.mdx:191` | |
| ACP-AUTH-007 | citation-only | `schema.mdx:143-144` (unchanged); `initialization.mdx:288-292` (was `:215-219`); `authentication.mdx:193`; `docs/rfds/get-auth-state.mdx:299,303 (Draft RFD)` (was `:293,297`) | `AuthStatusResponse` change is description text plus the new optional `AuthAccount.description`; the test needs no change beyond re-vendoring. After re-vendor, a non-string `description` fails AUTH-007 like a non-string `name`/`email` does today (`validation.py` honours only `x-deserialize-default-on-null`, not `-on-error`; the agent authored the value). `find_unknown_root_keys` checks root keys only, so `description` inside an account never tripped it at the old schema either. |
| ACP-AUTH-008 | citation-only (co-cited doc) | `$defs/AuthState` (unchanged); `extensibility.mdx:238-243` (was `:235-240`) | |
| ACP-AUTH-210 | unchanged | `authentication.mdx:191` | |

No row is removed and no tier or gate changes.

## Ledger entries (`spec-tracker/maps/v2.toml`, "authentication.mdx" group)

| ledger citation (base) | classification | target citation (@ 3ea94133) | note |
|---|---|---|---|
| `authentication.mdx:191` (failed/abandoned login -> -32000) | unchanged | `:191` | |
| `authentication.mdx:191` (cancelled login -> -32800) | unchanged | `:191` | |
| `authentication.mdx:213,214` (terminal args login-only) | unchanged | `:213,214` | |
| `authentication.mdx:224` (env values no secrets) | unchanged | `:224` | |
| `authentication.mdx:233,235,236` (auth failure after insertion) | unchanged | `:233,235,236` | |
| `authentication.mdx:270,271` (re-auth after logout) | unchanged | `:270,271` | Reason is sound: the decisive part is that gating is a MAY (`schema.mdx:990` now, cited as `:954` in the reason text; update that reference). |
| `get-auth-state.mdx:297 (Draft RFD); schema.mdx:144` (auth/status MUST NOT modify state) | citation-only | `get-auth-state.mdx:303 (Draft RFD); schema.mdx:144` | Optional: put `schema.mdx:144` first, since the schema docs state the rule (docs take precedence). |
| `get-auth-state.mdx:291` (SHOULD advertise `auth.status`) | citation-only | `:297` | Reason partly rests on a TCK choice, see D3. |
| `get-auth-state.mdx:303` (SHOULD list accounts, mark active) | citation-only | `:309` | Optional: also cite `schema/v2/schema.unstable.json#/$defs/AuthStatusResponse/properties/accounts` (schema states the same SHOULD), primary per docs precedence. Pre-existing, not caused by this update. |
| `get-auth-state.mdx:303` (accounts MUST NOT include secrets) | citation-only | `:309` | See new ledger entry below for the schema-stated `description` rule. |
| `get-auth-state.mdx:295,301` (keep fast, return unknown) | citation-only | `:301,307` | |
| `get-auth-state.mdx:307; $defs/AuthStatusUpdateNotification` (send status_update on change) | citation-only | `:313`; `$defs/AuthStatusUpdateNotification` (description text change only) | Reason worded as "out of scope for now", see D3. |

## New requirements

1. **ACP-AUTH-211** (provisional; v2-only `2xx`, since v1's draft `authentication.mdx` has no idempotency text, so no
   shared id under Rule B).
   - Text: "With `--allow-logout`, a second `auth/logout` sent right after a successful one on the same connection
     (no authenticated state left to end) succeeds with the same empty result: a non-error object result that
     validates as `LogoutAuthResponse`. SKIPs when no `authMethods` are advertised, `--allow-logout` was not
     given, or the first `auth/logout` did not succeed (`ACP-AUTH-004`'s concern)."
   - Tier: **ADVISORY** (agent-side SHOULD in the docs), `capability=None`.
   - Citation: `docs/protocol/v2/draft/authentication.mdx:273; schema/v2/schema.unstable.json#/$defs/LogoutAuthResponse`.
   - Test approach: same setup as `test_logout_succeeds` (fresh initialized connection; optional `--auth-method`
     login exactly as AUTH-004 does; `@pytest.mark.revokes("auth", ...)`). Send `auth/logout {}`; if it is not an
     object result, SKIP. Send `auth/logout {}` again; assert an object `result` and
     `validate_agent_response("auth/logout", msg)` is empty. Do not compare the two results byte-for-byte: "the
     same empty result" means the empty `LogoutAuthResponse`, and `_meta` may legitimately differ. The second call
     costs nothing extra destructively (credentials are already dropped by the first).
   - Harness / mock client: nothing new. Fixtures: the v2 `_base.py` `_handle_logout` must answer a repeated
     logout with `{}` (check it does); add a non-conforming v2 fixture that errors on a repeated logout (for
     example `-32000`), and update `tests/v2/test_cli.py` id sets.

No other new agent-side rule. RFD Behavior item 10 (`get-auth-state.mdx:315`) and the reworded `state` comments are
Client-side (MAY / Client decision), so they are neither rows nor ledger entries.

## New ledger entries

1. citation: `schema/v2/schema.unstable.json#/$defs/AuthAccount/properties/description; docs/rfds/get-auth-state.mdx:174-176 (Draft RFD)`
   statement: "An `AuthAccount` `description` MUST NOT contain credentials."
   reason: "Not observable: the TCK cannot tell a credential from display text such as a credential source name."
   (Stated in the draft schema, not only in the RFD, so it would be `CAPABILITY` behind `capabilities.auth.status`
   if it were testable; it is not. Alternatively fold it into the existing "accounts MUST NOT include secrets"
   entry by adding this pointer as its primary citation; see D1.)

## Decisions for the user

- **D1. Ledger shape for the new `description` credential rule.** Separate entry (above) vs. adding the schema
  pointer to the existing "`accounts` MUST NOT include secrets" entry. Recommendation: separate entry, because it
  is a schema-stated rule with its own citation, while the broader "no secrets in any account field" remains
  Draft-RFD-only (`:309`).
- **D2. ACP-AUTH-004's standalone path.** Without `--auth-method`, AUTH-004 calls `auth/logout` without logging in
  first and FAILs (CAPABILITY) on any error. If the agent had no authenticated state, `:273` now says success is
  only a SHOULD, so an error there violates a SHOULD, not the MUST ("MUST implement `auth/logout`", `:51-52`).
  Options: (a) leave AUTH-004 as is (simple; slightly stricter than the text for an agent that was not signed in);
  (b) when no TCK login preceded the logout, FAIL only on `-32601` and SKIP on any other error with a reason citing
  `:273`, keeping the non-error assertion after a successful TCK login. Recommendation: (b), since the TCK cannot
  know whether a standalone logout had state to end. It stays the shared id (a narrower v2 assertion keeps the id
  under Rule B); v1 has no such sentence, so the v1 test is untouched.
- **D3. Existing ledger reasons that lean on TCK choices.**
  - "SHOULD advertise `auth.status`" ends with "the TCK only calls it when it is advertised". The real blocker is a
    spec rule: "Clients MUST check for this capability before calling the method" (`get-auth-state.mdx:297`, Draft
    RFD). Recommendation: reword the reason to cite that client MUST instead of the TCK's behaviour.
  - "SHOULD send `auth/status_update` on change" is "out of scope for now ... revisit if the RFD stabilizes" and
    mentions operator flags. Recommendation: reword to the real blockers: the rule is a Draft-RFD-only SHOULD with
    no deadline, so the absence of a notification after a credential change is never conclusive within a bounded
    wait (and the TCK cannot cause a credential change without the operator's `--auth-method`/`--allow-logout`).
    Not "Deferred", since the missing deadline does not go away when the TCK changes its behaviour.
- **D4. Tier of ACP-AUTH-211.** ADVISORY per the SHOULD. No alternative recommended.

## Discrepancies

None between docs, schema and RFD. The RFD says the description "Never contains credentials" (no keyword); the
schema says "MUST NOT contain credentials". The schema governs (docs precedence), so the ledger entry uses MUST NOT.

## Open questions

None for this doc. Out of scope here: the `schema.mdx`, `initialization.mdx` and `extensibility.mdx` line moves in
co-cited citations (AUTH-005/007/008/206) should match whatever the owners of those docs report; the mappings above
were checked against both revisions.
