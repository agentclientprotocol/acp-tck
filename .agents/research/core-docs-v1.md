# Which ACP v1 draft docs are "core" (define rules other docs assume without linking)?

**Sources checked:** agent-client-protocol @ `beac4ba96190018e9f6d82e148ff275084c5aa3e` (the
commit pinned in `src/tck/v1/schema/VENDORED.md`). I read it with `git archive`, so the checkout's
working tree was not touched. acp-tck @ `c7e818a` (`src/tck/v1/requirements.py`,
`src/tck/v1/conformance/_helpers.py`). I used no SDKs, as the brief asked.
**Refresh note:** `git pull --ff-only` on the spec checkout failed with "Cannot fast-forward to
multiple branches". The checkout is on branch `eugenethedev/end-turn-token-rfd-update` @ `d7856fa`.
This did not affect the answer, because every citation below is against the pinned commit, not
HEAD.
**Confidence:** medium-high. The evidence for the six substantive docs is direct. Two calls are
judgment calls, stated as such: `error.mdx` is included even though it is only a stub, and
`prompt-turn.mdx`/`session-setup.mdx` are core only in certain sections.

All doc paths below are relative to `docs/protocol/v1/draft/` in the spec repo, unless they
start with `src/`, which means acp-tck.

## Answer

Recommended core list (7 docs):

1. `docs/protocol/v1/draft/transports.mdx`: whole doc
2. `docs/protocol/v1/draft/overview.mdx`: whole doc
3. `docs/protocol/v1/draft/extensibility.mdx`: whole doc
4. `docs/protocol/v1/draft/error.mdx`: whole doc. It is a stub today, so including it is pre-emptive.
5. `docs/protocol/v1/draft/initialization.mdx`: whole doc. The general rules are core. The
   capability catalogue entries are effectively leaf entries.
6. `docs/protocol/v1/draft/session-setup.mdx`: core sections only: intro/preconditions
   (L6-10), "Session ID" (L441-451), "Working Directory" (L453-462)
7. `docs/protocol/v1/draft/prompt-turn.mdx`: core sections only: "Session Updates" (L10-38),
   "Stop Reasons" (L578-596), "Cancellation" (L598-631)

What makes these core: each one defines a rule that applies globally (framing, the JSON-RPC
error/notification model, absolute paths, `_meta`/`_`-methods, capability-absence semantics,
the session ID and root set, the `session/update` envelope, and cancel/stop-reason semantics).
Feature docs rely on these rules without linking to them. No doc links to `transports.mdx` or
`extensibility.mdx`'s global rules at all. The other 13 docs, plus `schema.mdx`, are rejected
below. Most are leaf features that are linked explicitly. `schema.mdx` is generated, and changes
to it should be handled by the vendored-schema refresh path instead.

## Requirements

n/a. This is a dependency-mapping question, not a conformance requirement.

## Details

### Method used

- I extracted all intra-spec links per doc at the pinned commit. Inbound link counts (excluding
  `schema.mdx`) are: `transports` **0**, `extensibility` 3 (all from overview/initialization/
  session-list), `error` **0**, `overview` 7, `initialization` 15, `session-setup` 13,
  `prompt-turn` 21.
- For each candidate, I grepped every other doc for the candidate's concepts (`absolute`,
  `_meta`, `session/update`, `sessionId`, `omitted`/`null` capability phrasing, error codes,
  `cancel`, stop reasons), recording uses that are **not** accompanied by a link.
- I cross-checked against what the TCK cites. Citation counts in `src/tck/v1/requirements.py`
  are: session-setup 18, initialization 16, prompt-turn 9, transports 6, extensibility 6,
  overview 5, content 4, authentication 4, and ≤3 for every other doc.

### Core doc 1: `transports.mdx` (whole doc)

Rules it defines: UTF-8 (L6). The stdio subprocess model (L21-22). Newline-delimited messages
with no embedded newlines (L23-24). Stdout carries only ACP messages (L26). Stderr is for logging
(L25). Shutdown is close-stdin-then-terminate (L40). Custom transports must keep "the JSON-RPC
message format and lifecycle requirements defined by ACP" (L52).

Why it is core:
- **No doc links to it** (0 inbound links). Yet every message example in every doc is a
  single-line-framed JSON-RPC message, and the TCK harness and every conformance test depend on
  its framing.
- `authentication.mdx:173-180` (terminal auth) assumes the stdio subprocess launch model without
  linking here: it relies on "same configured Agent program and base launch configuration as the
  ACP connection" and on "Reconnects and reinitializes".
- `session-setup.mdx:468,476` uses "stdio transport" for MCP servers. This is a different
  transport, and a diff tool could conflate the two. It is not a dependency, but it is worth
  noting.

Dependent TCK areas: `ACP-TRANSPORT-*`, `ACP-STDERR-001`, `ACP-SHUTDOWN-001`, the harness
(`tck.common.harness`), and therefore every test.

### Core doc 2: `overview.mdx` (whole doc)

Rules it defines:
- The JSON-RPC 2.0 methods/notifications model (L10-13).
- The lifecycle order initialize → (auth) → session → prompt (L17-42).
- **All file paths MUST be absolute** (L230).
- **Line numbers are 1-based** (L231).
- **Error handling:** a successful response includes `result`, an error includes `error` with
  `code`/`message`, and **notifications never receive responses** (L235-239).
- A summary of extensibility (L241-249).

Implicit dependents (each one restates or assumes a rule without linking to `overview`):
- Absolute paths: `session-list.mdx:85` ("Must be an absolute path") and `:137`.
  `terminals.mdx:76`. `tool-calls.mdx:289,333`. `file-system.mdx:55,101`. `session-setup.mdx:376,457`.
- 1-based lines: `file-system.mdx:59`. `tool-calls.mdx:338`. Neither links to `overview`.
- "Notifications never receive responses" applies to every notification: `session/cancel`
  (`prompt-turn.mdx:600`), `session/update`, `elicitation/complete`, `$/cancel_request`
  (`cancellation.mdx:12`), and custom notifications (`extensibility.mdx:101-113`).
- Lifecycle order: the "MUST complete initialization first" restatements in
  `session-setup.mdx:8`, `prompt-turn.mdx:8`, `session-list.mdx:10` and `session-delete.mdx:8`
  all assume the overall flow from L17-42.

Dependent TCK areas: `ACP-JSONRPC-002/003/005`, `ACP-PROMPT-004`, `ACP-EXT-001`. Through the
absolute-path rule, also the FS, terminal, tool-call-location and list-`cwd` checks.

### Core doc 3: `extensibility.mdx` (whole doc)

Rules it defines:
- `_meta` on types that define it (L10-14).
- Reserved W3C trace keys (L37-41).
- **MUST NOT add custom fields at the root of a spec type** (L43).
- `_`-prefixed method names are reserved for extensions (L47).
- Custom requests MUST be answered (L69).
- Unknown methods get `-32601` (L84-95).
- Unknown notifications SHOULD be ignored (L113).
- Custom capabilities go in `_meta` (L117-138).

Implicit dependents:
- `_meta` fields described in feature docs without linking here: `session-config-options.mdx:167-168`,
  `prompt-turn.mdx:72,303-304,410-411,445`, `session-list.mdx:107,154,190,209`. Only session-list
  links here.
- L43 (no custom root fields) constrains every request, response and notification type in every
  doc. This is the rule behind the TCK's schema `additionalProperties` strictness.
- The `-32601` rule (L84-95) is the only doc-level statement of what happens for an unrecognized
  method, so it governs every method an agent does not implement, including optional ones such as
  `session/load`, `session/list` and `session/delete`.
- `initialization.mdx:115` links here for custom capabilities. That dependency is explicit.

Dependent TCK areas: `ACP-EXT-001/002`, `ACP-META-001`, `ACP-SCHEMA-002`, `ACP-JSONRPC-004/005`.
The TCK's own probe-method naming (`_tck/...`, CLAUDE.md step 4) also depends on it.

Caveat: the open-enum convention ("values beginning with `_` are reserved for
implementation-specific …, other unknown values for future ACP") is **not** defined here. Each
doc restates it on its own: `prompt-turn.mdx:296-299,383-386`, `session-setup.mdx:412`,
`session-config-options.mdx:217`. A change to `extensibility.mdx` therefore does not necessarily
propagate to those rules. That convention has no single home (see Discrepancies).

### Core doc 4: `error.mdx` (whole doc; pre-emptive)

Today the entire doc is `_Documentation coming soon_` (`error.mdx:6`). The error codes that docs
use without links are defined only in the generated `schema.mdx:4104-4152` (`ErrorCode`:
`-32000` "Authentication required", `-32002`, `-32602`, `-32601`, `-32800`, …). Docs that use
named or numbered errors without linking to any error doc:
- `auth_required`: `session-setup.mdx:10`, `authentication.mdx:167,222`. Nothing in the prose maps
  it to `-32000`.
- `-32602`: `session-setup.mdx:418`, `elicitation.mdx:166`.
- `-32601`: `extensibility.mdx:84-95`.
- `-32800`: `cancellation.mdx:22,37`. This one links to the schema anchor.

Why include a stub: a core entry only costs something when the doc changes. While it is a stub,
it never changes. When it does gain content, that content will by definition be cross-cutting
error rules (codes, `data` shape, `message` rules), which is exactly the case that needs
escalation. TCK areas likely affected: `ACP-ERROR-001/002`, `ACP-JSONRPC-002/004/005/007`,
`ACP-AUTH-003/005`, and the auth-gate in `src/tck/v1/conformance/_helpers.py:103-128`, which keys
on `-32000`.

### Core doc 5: `initialization.mdx` (whole doc)

Rules it defines that other docs assume:
- Version negotiation (L89-101): every doc's behavior is "per the negotiated version" (L91).
- **All capabilities are OPTIONAL. Peers SHOULD support all combinations. Omitted capabilities
  MUST be treated as UNSUPPORTED** (L107-109). This is the generic gating rule behind every
  "if X is not present, MUST NOT call Y".
- Baseline MUSTs: text and resource_link prompt content (L247). `session/new`, `session/prompt`,
  `session/cancel` and `session/update` (L289).
- "MAY support other session methods … by specifying additional capabilities" (L291).

Implicit dependents:
- `session-setup.mdx:234-235` (`resume`) and `:309-310` (`close`), and `session-list.mdx:37`
  (`list`). These gate on `sessionCapabilities.resume/close/list`, but `initialization.mdx`'s
  Session Capabilities catalogue (L287-314) lists only `delete`, `additionalDirectories` and
  `systemPrompt`. Those features rest entirely on the generic rules at L109/L291, not on a
  catalogue entry or a link.
- Restatements of the omitted/`null` ⇒ unsupported semantics: `session-delete.mdx:52`,
  `authentication.mdx:74-76`, `elicitation.mdx:42-47`, `prompt-turn.mdx:266-269,328-333`. If L109
  changed, for example so that `null` was no longer equivalent to omitted, all of these would
  silently diverge.
- Capability gates that do link here (explicit, but they need re-checking when the generic rule
  moves): `file-system.mdx:10`, `terminals.mdx:10`, `agent-plan.mdx:10`, `content.mdx:54-56,88,124`,
  `session-config-options.mdx:174`, `authentication.mdx:7,108`.

Dependent TCK areas: `ACP-INIT-*`, `ACP-PROMPT-001/002/003`, `ACP-PROMPTCAP-*`, `ACP-CLIENTCAP-*`,
`ACP-AUTH-002/006`, `ACP-CONFIG-003`, every capability-gated test (via the `capability` marker
and `capability_is_supported()`), and the handshake in every test
(`src/tck/v1/conformance/_helpers.py:47`).

Scoping note: a diff that touches only one catalogue entry (for example `elicitation` at L158-166)
is effectively a leaf change for that feature. A diff to L87-115, L245-247 or L287-291 is a core
change.

### Core doc 6: `session-setup.mdx` (core sections: L6-10, L441-451, L453-462)

Core rules:
- Sessions are independent contexts (L6). Initialization must happen first (L8).
  `session/new` may fail with `auth_required` (L10).
- **Session ID** (L441-451): the identifier that every session-scoped method in every doc
  addresses.
- **Working Directory and effective root set** (L455-462): `cwd` MUST be absolute, is the base
  for relative paths, and is part of the root set. The root set SHOULD bound file-system tool
  operations.

Implicit dependents:
- The root set: `file-system.mdx:49-51,95-97` ("The session determines which filesystem roots are
  in scope for the path"). It links only to the Session ID anchor, not to the root-set rule.
  `terminals.mdx:76` (`cwd`). `tool-calls.mdx:289,333` (locations).
- `sessionId` is used as a parameter without a definition link in `session-modes.mdx:97`,
  `session-config-options.mdx:271`, `slash-commands.mdx:17,85` and `elicitation.mdx:65-71`.
- "During Session Setup the Agent MAY return …" is the initial-state contract for
  `session-modes.mdx:17` and `session-config-options.mdx:17`, and slash commands are "After
  creating a session" (`slash-commands.mdx:10`). These are explicit links, but they depend on the
  `session/new`/`load`/`resume` response shape, which this doc owns (L202-203, L279-280).

Dependent TCK areas: `ACP-SESSION-*`, `ACP-LOAD-*`, `ACP-RESUME-*`, `ACP-CLOSE-*`, `ACP-ADDDIRS-001`,
`ACP-SYSPROMPT-*`, `ACP-MODES-*`, `ACP-CONFIG-*`, `ACP-LIST-*`, `ACP-DELETE-*`,
`ACP-AUTH-003/005`, and `new_session()` (`src/tck/v1/conformance/_helpers.py:134-144`), which
every session-dependent test uses.

The remaining sections (Loading, Resuming, Closing, Additional Roots, System Prompt, MCP Servers)
are feature specifications. Their dependents are explicit, so treat a diff there as leaf.

### Core doc 7: `prompt-turn.mdx` (core sections: L10-38, L578-596, L598-631)

Core rules:
- The **`session/update` envelope and the full `sessionUpdate` variant catalogue** (L12-36).
  **Updates are not limited to prompt turns** (L38).
- **Stop reasons** (L578-596).
- **`session/cancel` semantics** (L598-631): the agent MUST answer `session/prompt` with
  `cancelled` (L618) and MUST catch abort errors (L625). Updates after cancel must come before
  the response (L629).

Implicit dependents:
- Docs that use `session/update` without linking to the envelope: `session-modes.mdx:113`,
  `session-config-options.mdx:342`, `terminals.mdx:120`. Docs that link to it explicitly:
  `agent-plan.mdx:8`, `tool-calls.mdx:8`, `slash-commands.mdx:6`, `session-list.mdx:179`.
- Docs that reuse cancel semantics:
  - `session-setup.mdx:332-334` (`session/close` "as if `session/cancel` had been called").
    The link uses a non-draft path, see Discrepancies.
  - `tool-calls.mdx:196,211-212`: the permission `cancelled` outcome.
  - `cancellation.mdx:26,42`.
- `session-setup.mdx:136-137`: replay is "in the form of `session/update` notifications (like
  `session/prompt`)".

Dependent TCK areas: `ACP-PROMPT-001`, `ACP-CANCEL-*`, `ACP-CLOSE-002`, `ACP-LOAD-002`,
`ACP-CLIENTCAP-004..007`, `ACP-MODES-002`, and `run_prompt()`'s turn-end and cancel-race logic
(CLAUDE.md "Mock-client prompt driver").

The other sections (plan/tool walkthrough, notices, compaction, usage, session-directed messages)
are feature specifications with explicit capability gates. Treat a diff there as leaf. This
matters because `prompt-turn.mdx` is where most draft additions land.

### Rejected docs

| Doc | Reason rejected |
|-----|-----------------|
| `schema.mdx` | Generated from the Rust models (`schema-generator/src/main.rs:228-231`) and mirrors `schema.unstable.json`, which the TCK already vendors and refreshes through `VENDORED.md`. It is 8497 lines and changes with every schema change, so listing it as core would turn every update into a full audit. It *is* the only home of the `ErrorCode` table (`schema.mdx:4104-4152`). The recommendation is to handle that through the schema-diff path. |
| `content.mdx` | `ContentBlock` is shared by `prompt-turn`, `tool-calls`, `session-setup` (`systemPrompt`, L415) and compaction summaries, but dependents link to it explicitly (`prompt-turn.mdx:170,389`, `tool-calls.mdx:263`). Its only behavioral MUSTs (`content.mdx:31` and the capability gates at L54-56, L88, L124) are duplicated in `initialization.mdx:247-261`, which is core. Shape changes appear as schema diffs. **Borderline:** map it as an explicit dependency of `prompt-turn`, `tool-calls` and `session-setup`. |
| `cancellation.mdx` | The generic `$/cancel_request` and `-32800` are explicitly optional (`cancellation.mdx:14`). Their only feature-specific user, `prompt-turn`, cross-links in both directions (L26, L42). No other doc mentions `$/cancel_request` or `-32800`. **Watch:** L35-37 ("internal cancellation SHOULD send `-32800`") does apply to any request. If that ever becomes a MUST, or `$/cancel_request` becomes mandatory, promote this doc to core. |
| `authentication.mdx` | Cross-cutting in the TCK, because its gating drives the auth-gate in `_helpers.py:103-128` and the `blocked_by_auth` verdict. In the spec, however, the only cross-doc consequence is `auth_required` on `session/new`. That consequence is stated in `session-setup.mdx:10` (core) with an explicit link back here. **Borderline:** map it explicitly to the TCK's auth-gate code and `ACP-AUTH-*` rather than listing it as core. |
| `tool-calls.mdx` | Its permission flow and status lifecycle are used by `prompt-turn` and `terminals` through explicit links (`prompt-turn.mdx:22-23,568`, `terminals.mdx` links it). Leaf. |
| `session-modes.mdx`, `session-config-options.mdx` | Each defers to the other explicitly (`session-modes.mdx:6-11`, `session-config-options.mdx:10-15`). Both depend on core docs, not the other way round. Leaf pair: map each as a dependent of the other. |
| `session-list.mdx`, `session-delete.mdx` | `session-delete` depends on `session-list` explicitly (`initialization.mdx:296`, `session-list.mdx:61`). Leaf pair. |
| `file-system.mdx`, `terminals.mdx`, `elicitation.mdx`, `agent-plan.mdx`, `slash-commands.mdx` | Leaf features gated by client capabilities. Nothing else assumes their rules. `cancellation.mdx`'s terminal example (L54-66) is illustrative only. |

## Testability notes

These notes concern spec-map design, not agent conformance.
- A link-graph pass can find explicit dependents automatically. Core status is needed only for
  the implicit cases listed above. For those, `spec_map.toml` should name the dependent areas
  (TCK id prefixes) directly rather than relying on links.
- Section-scoped core status (items 5-7) keeps `prompt-turn`/`session-setup` updates from
  always triggering a full audit. Use heading anchors rather than line numbers for the scope, so
  it survives line drift: for example `prompt-turn#session-updates`, `#stop-reasons`,
  `#cancellation`; `session-setup#session-id`, `#working-directory`. Whether to support
  section scoping is a design decision for the orchestrator. If it is not supported, list the
  whole doc.
- This is a recommendation, not something found in the spec: diffs to the vendored schema at
  `$defs/ErrorCode`, `$defs/SessionUpdate`, `$defs/ContentBlock`, `$defs/AgentCapabilities` and
  `$defs/ClientCapabilities` are core-equivalent and should escalate the same way.

## Discrepancies

- **Non-draft link targets inside draft docs.** `session-setup.mdx:6,8,333`,
  `session-delete.mdx:8`, `session-list.mdx:10` and `file-system.mdx:10,51` link to
  `/protocol/v1/<page>`, the stable tree, instead of `/protocol/v1/draft/<page>`. A link-graph
  tool restricted to draft paths will miss these edges unless it normalizes them. One of the
  missed edges is the `session/close` → prompt-turn cancellation dependency.
- **Capability catalogue is incomplete.** `initialization.mdx:287-314` omits
  `sessionCapabilities.resume`, `close` and `list`, which `session-setup.mdx:210,284` and
  `session-list.mdx:37` gate on. Those features depend only on the generic rule.
- **Error rules have no prose home.** `error.mdx:6` is a stub. `auth_required` is never mapped to
  `-32000` in prose. The mapping exists only in `schema.mdx:4141-4144`.
- **The open-enum `_` convention is restated in each doc** (`prompt-turn.mdx:296,383`,
  `session-setup.mdx:412`, `session-config-options.mdx:217`) and is not defined in
  `extensibility.mdx`, which reserves only method names (L47) and root fields (L43).
- **The method catalogue in `overview.mdx` is incomplete** (L49-117). It omits
  `session/list/resume/close/delete`, so it cannot serve as an authoritative method index.

## Open questions

- Should `spec_map.toml` support section-scoped core entries? If not, items 6 and 7 become
  whole-doc entries, and every `prompt-turn` draft addition will escalate. This is an
  orchestrator or design decision.
- Should vendored-schema `$defs` diffs feed the same escalation? This needs routing to whoever
  owns the spec-update workflow.
- The spec checkout cannot fast-forward ("multiple branches"). The user should decide whether to
  fix the checkout's branch configuration. This does not block the work, since the pinned commit
  was readable.
