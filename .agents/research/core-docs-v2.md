# Which ACP v2 draft docs are "core" (their rules are assumed elsewhere, so a change can alter behavior specified in other docs)?

**Sources checked:** agent-client-protocol @ `beac4ba96190018e9f6d82e148ff275084c5aa3e` (2026-10-19, the pin in `src/tck/v2/schema/VENDORED.md`). The checkout was pulled to HEAD `d7856fad`. `git diff beac4ba..HEAD -- docs/protocol/v2/draft` is empty, so the pin and HEAD match for this tree. Docs were read with `git archive` at the pin. acp-tck working tree @ `c7e818a` for `src/tck/v2/requirements.py` citations and the infra modules that depend on spec docs. No SDKs were used.
**Confidence:** medium-high. The dependency evidence is direct (cited restatements and term use). Where to draw the "core" line is a judgment call, and the reasoning for it is given below.

## Answer

Recommended core list (6 of 18 docs):

1. `docs/protocol/v2/draft/prompt-lifecycle.mdx`
2. `docs/protocol/v2/draft/extensibility.mdx`
3. `docs/protocol/v2/draft/initialization.mdx`
4. `docs/protocol/v2/draft/session-setup.mdx` (section-scoped, see below)
5. `docs/protocol/v2/draft/overview.mdx` (section-scoped)
6. `docs/protocol/v2/draft/transports.mdx`

Each of these defines a shared model that other docs restate or use without linking:
- the foreground-state machine, insertion boundary, upsert/entity-ID rules and cancellation;
- open-enum, unknown-field and `_meta`-patch rules, and when a capability is needed;
- capability-marker semantics and the baseline `session` surface;
- session existence, replay and current-state sync;
- cross-cutting conventions (absolute paths, error envelope, naming);
- JSON-RPC framing, batches and message timing.

Two features make these docs dangerous. Satellite docs restate their rules, so a core change can leave a stale restatement behind with no diff. And several of our requirement rows cite the satellite restatement rather than the core source.

To keep the audit cost bounded, escalate on specific sections, not on whole files, for session-setup and overview. The core sections are listed in Details.

## Requirements

n/a. This is a dependency-mapping question, not a conformance requirement.

## Details

### 1. `prompt-lifecycle.mdx` — core (whole file except leaf subsections)

What it defines that others assume:
- Foreground vs background work and the MUST/SHOULD state reports (`prompt-lifecycle.mdx:116-146`). Also the state table (`:983-1013`), waiting-for-user-action (`:1015-1030`) and work boundaries / local commands (`:1032-1047`).
- The insertion boundary: respond only after insertion, never an error after it, `-32800` before it (`:251-314`).
- The complete `SessionUpdate` variant set (`:14-49`).
- Entity-ID scoping by type plus ID, with a MUST NOT on reuse (`:51-68`).
- Message upsert/chunk semantics (`:406-420`).
- Stop reasons, including the `_`-prefixed custom rule (`:862-887`), and failures with `stopReason:"error"` plus the `error` object (`:889-929`).
- Session cancellation (`:1080-1130`).

Implicit or restating dependents (each line re-states the rule, so a core change can leave it stale without a diff):

| Dependent doc | Evidence | What it assumes |
|---|---|---|
| `tool-calls.mdx` | `:10` ("Tool call updates may arrive while the Agent reports `idle`. They do not change the state."), `:201` (restates requires_action → running/idle MUST), `:311`, `:326-327` (`cancelled` outcome tied to active-work cancellation) | state machine, cancellation |
| `elicitation.mdx` | `:73-92` (restates the foreground-state MUSTs), `:190-214` (cancellation races, resume idle snapshot with old `cancelled`) | state machine, cancellation, resume snapshot |
| `slash-commands.mdx` | `:136` (insertion contract), `:138` (live-only message, same ID on replay), `:142-149` (restates the local-command running→idle MUST and `end_turn` SHOULD) | insertion, work boundaries |
| `authentication.mdx` | `:219-236` (restates the insertion boundary and idle + `error.code:-32000` for auth failures) | insertion, failures |
| `cancellation.mdx` | `:28-39`, `:53`, `:57` (restates the session/cancel MUSTs, the `-32800`-only-before-insertion rule, and that the Client answers permissions with `cancelled`) | insertion, cancellation, state transitions |
| `session-setup.mdx` | `:84-92` (duplicates the initial state, compare `prompt-lifecycle.mdx:968-981`), `:261-299` (replay must reuse the prompt `messageId`, upsert/chunk semantics restated at `:275-292`), `:364-366` (close: idle(cancelled) before the close response, `-32800` vs `messageId`) | entity IDs, upserts, insertion, cancellation |
| `agent-plan.mdx` | `:143` (every plan variant MUST carry `planId`, which relies on the entity-ID rules at `prompt-lifecycle.mdx:51-68`) | entity IDs |
| `schema.mdx` (generated) | `:455-475` (session/cancel text restates `prompt-lifecycle.mdx:1103-1128`) | cancellation |

TCK areas that do not cite prompt-lifecycle but depend on it:
- `ACP-PERM-201`, which cites `tool-calls.mdx:201`;
- `ACP-CLIENTCAP-201` (elicitation);
- `ACP-CANCEL-209` and `ACP-PROMPT-207`, which cite `cancellation.mdx:33-38` and `:53`, both restatements;
- `ACP-PATCH-205..208` (agent-plan and tool-calls entity upserts);
- `ACP-CLOSE-201/203`.

The `run_prompt` turn-end predicate in `src/tck/v2/conformance/_helpers.py` also implements this doc (per `CLAUDE.md`). Rows that cite it directly: PROMPT-201/203/207/208, STATE-201..205, CANCEL-201..203/206/207/209, RESUME-202/204/206, CLOSE-202/204, PATCH-201/203/209.

Leaf subsections that could be excluded from escalation, because they are capability-free informational additions with no dependents found:
- Session Notices `:483-541`;
- Session Compaction `:542-686`;
- Session Usage Updates `:687-711`;
- End-Turn Token Usage `:735-767`;
- Session-directed messages `:70-114`.

One caveat: `session-setup.mdx:212-215` restates the notice no-replay rule (`prompt-lifecycle.mdx:46-47`), so the Notices section still has one dependent.

### 2. `extensibility.mdx` — core (whole file)

What it defines:
- When a capability is required, with "omitted or `null` support marker means unsupported" (`:21-39`) and "MUST NOT infer peer support from schema selection" (`:16-19`).
- Validation: accept unknown fields and unknown open discriminators, and a malformed known discriminator MUST NOT fall through (`:47-62`).
- `_meta` reservation and the root-field ban (`:64-95`).
- Metadata Patches, including the list of entity updates whose `_meta` is a patch (`:97-144`).
- Unknown object fields (`:146-152`).
- `_`-prefixed extension methods and `-32601` (`:154-222`).
- The open enum / tagged-union rule (`:224-235`).
- Custom capability advertisement, including "MUST NOT send `capabilities.session: {_meta}` unless it supports all seven baseline session methods" (`:237-245`).

Implicit dependents. Most of these restate the `_`-prefix open-enum rule without linking to `extensibility.mdx#enum-and-tagged-union-variants`:

| Dependent doc | Evidence |
|---|---|
| `tool-calls.mdx` | `:77` (tool kinds), `:353` (permission option kinds), `:380` (status), `:386` (unknown content preserve); `:103-124`, `:439-442` (restates the patch semantics, links only at `:112`) |
| `agent-plan.mdx` | `:71-75` (unknown fallback), `:141`, `:160`, `:172` |
| `content.mdx` | `:20` (content block types) |
| `slash-commands.mdx` | `:107` (input types) |
| `session-config-options.mdx` | `:186-189` (categories), `:220` (option types) |
| `authentication.mdx` | `:121-123` (auth method types) |
| `prompt-lifecycle.mdx` | `:44` (unknown session updates), `:887` (custom stop reasons), `:485-490`, `:762-767` (capability-free informational delivery) |
| `session-setup.mdx` | `:197-201` (custom/future `replayFrom.type`), `:442` (systemPrompt `mode` `_`-prefix), `:294-299` (replay applies `_meta` as a patch) |
| `session-list.mdx` | `:188-191` (`session_info_update._meta` patch) |
| `initialization.mdx` | `:134-142` (unknown capability fields, experimental negotiation) |
| `overview.mdx` | `:203` (restates the open-enum convention in brief) |

TCK infra that depends on it:
- `src/tck/v2/validation.py:20-25` (open tagged-union "other" fallback carve-out) and `:278` (extension methods have no fixed shape);
- `tck.v2.protocol.is_valid_open_enum_value` (referenced at `validation.py:22`).

Rows that cite it directly: STATE-203, CLIENTCAP-202, JSONRPC-004/005, AUTH-206, ENUM-201/203, EXT-001/201/202/204, META-001, SCHEMA-002. Rows that depend on it without citing it: PATCH-206..209 (via the tool-calls restatement), LIST-* (`_meta` patch), CONFIG-* (open option types).

Churn is low: 7 commits in total, 4 since 2026-07-19. Including it costs little.

### 3. `initialization.mdx` — core (whole file; Implementation Information `:291-308` is a leaf)

What it defines:
- The `authMethods` → MUST implement `auth/login` and `auth/logout` surface rule (`:82-84`).
- Version negotiation and `-32022` (`:94-119`).
- Omitted capability = unsupported (`:127`).
- The per-field null/`{}` marker semantics (`:151-155`, `:163-169`, `:179-198`, `:223-244`, `:252-285`).
- The baseline `session` surface (seven methods) (`:179-185`, `:202-204`).
- The baseline prompt content Text + ResourceLink (`:248`).

Implicit dependents:

| Dependent doc | Evidence |
|---|---|
| `session-setup.mdx` | `:129-130` and `:338-340` ("Agents that support the `session` method surface MUST support `session/resume` / `session/close`"); `:383-386`, `:411` (additionalDirectories gate); `:415`, `:450` (systemPrompt gate); MCP transport check (section at `:610`) |
| `session-list.mdx` | `:10` (session surface → MUST support `session/list`) |
| `session-delete.mdx` | `:35`, `:57` (restates the `session.delete` omitted/null/`{}` semantics) |
| `elicitation.mdx` | `:24-56` (mode advertisement), `:187` (`-32602` for an unadvertised mode) |
| `authentication.mdx` | `:128-154` (`auth.terminal` gate), `:240-243` (logout availability = authMethods) |
| `content.mdx` | `:57`, `:90`, `:126` (image/audio/resource gates) |
| `prompt-lifecycle.mdx` | `:243` (Clients MUST restrict prompt content to the capabilities) |
| `overview.mdx` | `:56` (duplicates the `authMethods` rule) |
| `extensibility.mdx` | `:243` ("all seven baseline session methods", a count that must track `initialization.mdx:182-184`) |

TCK infra that depends on it:
- `src/tck/common/plugin.py:416` `capability_is_supported` (object-marker semantics). Every `@pytest.mark.capability` test inherits it: DELETE, ADDDIRS, SYSPROMPT, MCP, FORK, CLIENTCAP, PROMPTCAP.
- `plugin.py:353-357`, `:465` (the `-32022` version-rejection gate).
- `plugin.py:304-306` (the auth gate keys on advertised authMethods).

Rows that cite it directly: INIT-*, SCHEMA-001, PROMPT-206, PROMPTCAP-001..003, SYSPROMPT-202, EXT-204.

### 4. `session-setup.mdx` — core, section-scoped

Core sections:
- Creating a Session (`:45-82`);
- Initial Session State (`:84-125`);
- Resuming Sessions, including Current-State Synchronization (`:127-334`);
- Closing Active Sessions (`:336-379`);
- Session ID (`:476-485`);
- Working Directory (`:487-496`).

Leaf sections (not core): Additional Workspace Roots (`:381-411`), System Prompt (`:413-474`), MCP Servers (`:498-643`). Only their own rows cite them.

Implicit dependents:

| Dependent doc / area | Evidence |
|---|---|
| `session-config-options.mdx` | `:10` (initial `configOptions` in setup responses, defined at `session-setup.mdx:94`) |
| `slash-commands.mdx` | initial `availableCommands` (section `:10-44`, defined at `session-setup.mdx:94-125`) |
| `session-list.mdx` | `:197-198`, `:200-206` (list → resume with `replayFrom`) |
| `session-delete.mdx` | `:93-94` (resume or delete on deleted or active sessions is implementation-defined, which presumes the session-setup lifecycle) |
| `prompt-lifecycle.mdx` | `:300` (replay must reuse the ID), `:304` (close cancels a pending prompt), `:968-981` (initial/resume state) |
| `tool-calls.mdx` / `elicitation.mdx` | pending interactions on resume (`session-setup.mdx:333-334`); `cwd` root-set boundary for tool operations (`session-setup.mdx:496`) |
| `transports.mdx` | `:54-55` ("session-scoped messages still require a valid session") |
| `authentication.mdx` | `:267-275` (active sessions after logout) |
| `schema.mdx` | `:622-624` (`session/fork` is defined "as with `session/new`") |

TCK-level dependence: every session-dependent test creates its session through `session/new` in `connected_agent()`/fixtures. A change to the required `session/new` params (`cwd`, `mcpServers`) or to the response shape affects every row past INIT. Rows that cite it directly: SESSION-*, RESUME-*, CLOSE-*, CANCEL-208, CONFIG-203. Implicit dependents: LIST-*, DELETE-*, FORK-*, STATE-* (resume snapshot).

Churn is high: 29 commits in total, 12 since 2026-07-19. Section scoping is how this avoids turning most updates into a full audit.

### 5. `overview.mdx` — core, section-scoped

Core sections: Agent Baseline Methods (`:54-128`, including the auth surface rule `:56`), Argument requirements (`:186-189`), Error Handling (`:191-197`), Conventions (`:199-203`). Message Flow (`:19-48`) and Next Steps (`:215-221`) are non-normative.

Implicit dependents:
- **Absolute paths** (`:188`) are restated in `tool-calls.mdx:288`, `:446`, `:492`, in `agent-plan.mdx:119`, in `session-list.mdx:64` and `:116`, and in `session-setup.mdx:407` and `:491`. A change in the base rule (for example allowing relative paths) would leave all of these stale.
- **Notifications never get responses** (`:197`) underlies `transports.mdx:78-79` and every notification row (CANCEL-205, JSONRPC-003).
- **The JSON-RPC error object shape** (`:193-196`) is the only general error rule in v2, because `error.mdx` is a placeholder (`error.mdx:6`). `prompt-lifecycle.mdx:912-916` reuses it for the `error` stop-reason payload.
- **Naming conventions** (`:201`): camelCase keys and snake_case discriminators apply to every doc.

Rows that cite it directly: CANCEL-205, JSONRPC-001/002/003/005, LIST-204, EXT-001, ERROR-001.

### 6. `transports.mdx` — core (whole file; very low churn: 6 commits, 1 since 2026-07-19)

What it defines:
- UTF-8 and newline framing, and no non-ACP stdout (`:6`, `:23-28`);
- message timing, where Agents MAY send at any time after initialize (`:45-55`);
- batch rules, including `-32700`/`-32600` with `id:null` (`:57-97`).

Implicit dependents:
- the "may arrive before or after the response" tolerance in `prompt-lifecycle.mdx:276` and `:970-972` and in `session-setup.mdx:86-88`, which presumes message timing;
- `extensibility.mdx:142` (a batch is not atomic for `_meta` clears);
- `overview.mdx:15-17` (batch, linked).

TCK infra that depends on it:
- `src/tck/common/harness.py` (NDJSON framing, per `CLAUDE.md`);
- `src/tck/v2/validation.py:8-12`, `:220-256` (batch dispatch and empty-batch issue);
- every row's ability to read traffic at all.

Rows that cite it directly: TRANSPORT-*, BATCH-*, JSONRPC-001/003, CANCEL-205, SHUTDOWN-001, STDERR-001.

### Considered and rejected

| Doc | Why not core |
|---|---|
| `schema.mdx` | Generated from `schema/v2/schema.unstable.json` (`schema.mdx:6-10`) and the highest churn (84 commits). Its prose mostly restates the core docs (for example `:455-475`). The real trigger is the vendored-schema refresh, which already self-updates `tck.v2.protocol`/`validation`. Exception: a few rules exist only here, such as `session/fork` (`:612-624`) and the `auth_required` MAY (`:785`), so treat its diffs as direct-change only. |
| `error.mdx` | Placeholder (`error.mdx:6`, "_Documentation coming soon_"); 1 commit. **Watch item:** once it is populated it will define cross-cutting error codes and should be promoted to core. Any diff to it should trigger a core-list review. Three INFO rows cite it (`requirements.py:526`, `:1823`, `:1835`). |
| `cancellation.mdx` | It defines `$/cancel_request` and `-32800`, but its session-level content restates prompt-lifecycle (`:28-39`, `:53`, `:57`). Its own dependents (`prompt-lifecycle.mdx:255`, `:312`, `:1094`; `elicitation.mdx:198`) link to it explicitly. It is a dependent of core, not core itself. The one unlinked use is `session-setup.mdx:366` (`-32800` on close). Map it as a direct input to CANCEL-*, PROMPT-207 and CLOSE-202. |
| `tool-calls.mdx` | High churn (12 commits in 90 days), but leaf-shaped. Its rules are consumed only by its own rows and by the cancellation path through the permission `cancelled` outcome (`:311`, `:326`). Add an edge from `tool-calls#requesting-permission` to CANCEL-* and the `run_prompt` permission answering, rather than making the whole doc core. |
| `authentication.mdx` | Others reference `auth_required`/`-32000` (`session-setup.mdx:10`, `prompt-lifecycle.mdx:918`), but by link or as an example. Its session-failure section (`:219-236`) restates prompt-lifecycle, which makes it a dependent, not a source. Add an infra edge to the `plugin.py:304-306` auth gate, which decides whether session-dependent tests run at all. |
| `content.mdx` | A shared data type, but the normative gating lives in `initialization.mdx:246-271`, and the shape lives in the schema, which is caught by the schema refresh. 0 requirement citations and 0 commits in 90 days. |
| `elicitation.mdx`, `session-list.mdx`, `session-delete.mdx`, `session-config-options.mdx`, `slash-commands.mdx`, `agent-plan.mdx` | Capability- or feature-scoped leaves. Each one consumes core rules (shown in the tables above) and no other doc assumes its rules without a link. |

## Testability notes

- Escalation rule for `spec_map.toml`: when a core doc changes, re-check (a) the TCK rows listed under it, including the ones that only cite a satellite restatement, and (b) the satellite restatement lines. The restatements, not only our rows, are where a transitive change shows up first: the upstream doc stays unchanged while its restated rule goes stale.
- Section-scoped escalation for `session-setup.mdx` and `overview.mdx` (and optionally the prompt-lifecycle leaf subsections) keeps the list at six without making every high-churn session-setup edit a full audit. This depends on the diff tool being able to map changed lines to `##` headings.
- Some escalations land on TCK infrastructure rather than requirement rows: `common/harness.py`, `common/plugin.py` gates, `v2/validation.py` carve-outs, and `_helpers.run_prompt`. `spec_map.toml` should be able to name modules as well as requirement areas.

## Discrepancies

- `content.mdx:57`, `:90` and `:126` link to `/protocol/v2/draft/initialization#prompt-capabilities`. The heading is "Session Prompt Capabilities" (`initialization.mdx:246`), and `prompt-lifecycle.mdx:243` links to `#session-prompt-capabilities`. The `content.mdx` anchor is probably broken. This is a hypothesis about Mintlify's slugging, not verified by rendering. It matters only if the diff tooling resolves links.
- `overview.mdx:218` says "creating and loading sessions", but v2 has no `session/load` (the baseline at `initialization.mdx:182-184` lists resume). This is stale wording and not normative.
- No conflicts found between a core rule and its restatements at this pin. The restated MUSTs in `tool-calls.mdx:201`, `elicitation.mdx:77-79`, `slash-commands.mdx:144-147`, `authentication.mdx:226-229`, `cancellation.mdx:33-38` and `session-setup.mdx:364-366` match the `prompt-lifecycle.mdx` text.

## Open questions

- Several v2 rows cite `schema.mdx` by line number (`requirements.py:251`, `:541`, `:556`, `:590`, `:1244`, `:1259`, `:1489`). That doc regenerates on every schema change (84 commits), so these citations drift. This is worth routing to whoever owns citation hygiene. `CLAUDE.md` says v2 cites the schema by JSON Pointer, but that applies to `schema.unstable.json`, not to `schema.mdx`.
- `ACP-CANCEL-209` and `ACP-PROMPT-207` cite `cancellation.mdx` restatements of prompt-lifecycle rules. Should they also cite the source sections (`prompt-lifecycle.mdx:1098-1113`, `:255`), so a direct diff reaches them without core escalation?
- `docs/rfds/v2/*` is cited by at least one row (`requirements.py:512`). RFDs were out of scope here. Whether RFD diffs belong in the spec map at all is a separate decision.
