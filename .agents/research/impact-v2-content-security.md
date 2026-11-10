# v2 impact: `content.mdx` (modified) and `security.mdx` (new)

**Sources checked:** agent-client-protocol (checkout `agent-client-protocol-2`, HEAD = `3961af94fa62d2386d993cadf1afc8b146fc799a`, not pulled per brief), diffed against base `beac4ba96190018e9f6d82e148ff275084c5aa3e`. TCK repo at branch `eugenethedev/update-spec`. Reference SDKs not consulted: the spec text, the schema and the `session/prompt` doc all state the one behavioral rule found, so nothing relies on implicit runtime behavior.
**Confidence:** high for the doc/schema reading. Medium for the one new-requirement proposal, because its real-agent pass rate is unknown (see Testability).

All `path:line` citations below are `@ 3961af94fa62` and repo-relative to the spec checkout unless prefixed `src/`, `tests/`, `spec-tracker/`.

## Answer

1. **`security.mdx` yields no new requirement.** Its only MUSTs are the icon rules on line 35 (five MUSTs in one bullet), and they bind Clients. Everything else is SHOULD/SHOULD NOT/MAY. Every Agent-bound rule is SHOULD and depends on model behavior, on deployment (multi-user), or on network canaries. I propose ledger entries only. No registry row cites it.
2. **`content.mdx` itself adds one agent-observable MUST that no registry row covers, and the existing "unadvertised content is undefined" assumption is now wrong.** `content.mdx:22` says "Agents reject others with `-32602`". It restates `prompt-lifecycle.mdx:313` ("Agents **MUST** reject a prompt containing a content type that is neither baseline (`text`, `resource_link`) nor advertised, or that they don't understand with `-32602`, without inserting it") and the schema's `ContentBlock` "other" variant description. All three agree. The docstring of `src/tck/v2/conformance/test_prompt_capabilities.py:11-12` ("agent-side behavior for that case is undefined by the spec") is now out of date. I propose two new CAPABILITY requirements (`ACP-PROMPT-209`, `ACP-PROMPTCAP-004`). The `prompt-lifecycle` report owns the primary rule at `prompt-lifecycle.mdx:313`, so the orchestrator must merge ids if that report proposes the same row.
3. **v2 does say "All Agents MUST support resource links when included in prompts"** (`content.mdx:178`, new in this range), matching v1's `content.mdx` and the schema `ContentBlock` resource_link variant ("All agents MUST support resource links in prompts."), and `initialization.mdx:308`. No contradiction. `ACP-PROMPT-206`'s text claim "`content.mdx` is silent on `resource_link`" is now false and must change. The test needs no change.
4. `ACP-PROMPTCAP-001..003` stay valid. Their citations should gain `content.mdx` (the "Requires the `image`/`audio`/`embeddedContext` prompt capability" lines) and their `initialization.mdx` line ranges move (mechanical).

## Summary table

| id | classification | note |
|---|---|---|
| ACP-PROMPT-206 | changed text + citation | Text says `content.mdx` is "silent on `resource_link`"; now `content.mdx:178` states the MUST. Add `content.mdx:178` to the citation. `initialization.mdx:248` -> `:308` (mechanical). Test unchanged. |
| ACP-PROMPTCAP-001 | citation-only change (+ add content.mdx) | `initialization.mdx:246-271` -> `306-331` (mechanical). Recommend adding `content.mdx:62-64` (image). |
| ACP-PROMPTCAP-002 | citation-only change (+ add content.mdx) | Same range move. Recommend adding `content.mdx:95-97` (audio). |
| ACP-PROMPTCAP-003 | citation-only change (+ add content.mdx) | Same range move. Recommend adding `content.mdx:131-133` (embedded resource). |
| (no other row cites `content.mdx` or `security.mdx`) | unchanged | `grep` of `src/tck/v2/requirements.py`: only the `content.mdx` mention inside ACP-PROMPT-206's prose. |
| ACP-PROMPT-207 | unchanged | Cites `prompt-lifecycle.mdx`, not mine. Relevant because the new `ACP-PROMPT-209` reuses its "error -> no user_message" check. |
| ACP-PROMPT-209 (proposed) | new, CAPABILITY | Unknown/custom content block type in a prompt is rejected with `-32602`, not inserted. |
| ACP-PROMPTCAP-004 (proposed) | new, CAPABILITY (needs negative gate) | A known-but-unadvertised type (`image`/`audio`/`resource`) is rejected with `-32602`. |
| LEDGER-CNT-01..04 | new ledger entries | content.mdx client-side or unobservable statements. |
| LEDGER-SEC-01..13 | new ledger entries | security.mdx statements. |
| spec-tracker map | decision | Recommend adding `content.mdx` as a whole-doc core doc. Do not add `security.mdx`. |

## Part 1: `content.mdx`

### What changed (target text, whole-doc read)

- Intro reworded (`:6`). Headings sentence-cased (`## Content types` :14, `### Text content` :28, `### Image content` :50, `### Audio content` :83, `### Embedded resource` :112, `### Resource link` :174).
- `:16` content from the Agent is untrusted (links to `security.mdx`).
- `:18-20` ACP `ContentBlock` is a superset of MCP 2026-07-28 `ContentBlock`; ACP-only additions listed; later-MCP types ACP doesn't define are converted or omitted by Agents.
- `:22` (new sentence): "In prompts, Clients send only baseline content types (`text` and `resource_link`) and content types the Agent advertised, including custom types advertised through a custom capability, and Agents reject others with `-32602`."
- `:24` display baseline (Clients SHOULD show text, placeholder for unrenderable image/audio/resource/link, SHOULD NOT drop silently; Agents SHOULD also include content as text if it must reach the user in a particular form).
- `:26` annotations semantics: `audience` `user` = person using the Client, `assistant` = Agent's model; `priority` 0..1; Clients MAY collapse/hide content whose audience lacks `user`.
- `:30` text Markdown rule moved here: Clients SHOULD render as CommonMark, MAY support GFM extensions.
- `:39` "All Agents **MUST** support text content blocks when included in prompts." (unchanged text).
- `:178` (new): "All Agents **MUST** support resource links when included in prompts." Also `:176` "References to resources that the receiver may be able to read." (was "the Agent can access").
- Prompt-capability anchors repointed `#prompt-capabilities` -> `#session-prompt-capabilities` (`:63,96,132`).
- Schema deltas for these types (diff `schema/v2/schema.unstable.json`): `ResourceLink.size` now `format: uint64, minimum: 0` (nullable integer); `Annotations.lastModified` lost `format: date-time` and now says "Should be an ISO 8601 formatted string ... as in MCP"; `Annotations.priority` description gains the 0..1 range (min/max already present); `Icon.src` description now "MUST be an `https:` or `data:` URI. Clients reject other schemes ..."; `Role` and `IconTheme` get an open `other` branch; `ContentBlock` "other" variant description adds the rejection MUST (below).

### Normative statements in `content.mdx`

| Line | Statement | Wording | Binds | Observable by client-driven TCK? | Disposition |
|---|---|---|---|---|---|
| 22 | Agents reject non-baseline, non-advertised prompt content types with `-32602` | MUST (bare "reject"; the MUST is at `prompt-lifecycle.mdx:313` and in the schema) | Agent | Yes | New: ACP-PROMPT-209 / ACP-PROMPTCAP-004 |
| 22 | Clients send only baseline + advertised content types | (MUST at `prompt-lifecycle.mdx:313`) | Client | n/a (the TCK honors it; see ACP-PROMPTCAP-001..003 gating) | none |
| 39 | Agents support text blocks in prompts | MUST | Agent | Yes, implicitly (every conformance prompt is text) | covered by every `run_prompt` test; no dedicated row. See Open questions. |
| 178 | Agents support resource links in prompts | MUST | Agent | Yes | ACP-PROMPT-206 (existing) |
| 62-64, 95-97, 131-133 | image/audio/resource require the matching prompt capability when included in prompts | MUST-ish (capability-gated, "Requires") | Client sends only when advertised | Yes, positive path | ACP-PROMPTCAP-001..003 (existing) |
| 16 | Agent content is untrusted | statement | Client | No | LEDGER-CNT-01 |
| 18, 20 | MCP superset; agents forward MCP output unchanged; convert-or-omit later-MCP types | statement / no keyword | Agent | No (internal; the TCK cannot inject MCP output) | LEDGER-CNT-02 |
| 22 | Custom content block types MUST begin with `_` | MUST | Sender (both sides) | Agent-emitted custom types are validated by the generic schema/enum layer | existing ACP-ENUM rows; unchanged |
| 24 | Clients SHOULD show text; placeholder for unrenderable types; SHOULD NOT drop silently | SHOULD / SHOULD NOT | Client | No | LEDGER-CNT-03 |
| 24 | Agents SHOULD also include content as text if it must reach the user in a particular form | SHOULD | Agent | No (intent) | LEDGER-CNT-03 |
| 26 | Annotation semantics; Clients MAY collapse/hide non-`user` audience | MAY | Client | No | LEDGER-CNT-04. `priority` range is already enforced by the schema validator on agent-authored annotations. |
| 30 | Clients SHOULD render text as CommonMark, MAY support GFM | SHOULD / MAY | Client | No | LEDGER-CNT-04 |

### Existing rows

- **ACP-PROMPT-206** (`src/tck/v2/requirements.py:364`): *changed text + citation.*
  - Old text (tail): "Replaces v1's ADVISORY `ACP-PROMPT-003`, whose recorded doc conflict does not exist in v2 (`content.mdx` is silent on `resource_link`, not contradictory)."
  - Proposed text tail: "Replaces v1's ADVISORY `ACP-PROMPT-003`. `content.mdx` now states the MUST outright, so no doc conflict exists."
  - Proposed citation: `docs/protocol/v2/draft/initialization.mdx:308; docs/protocol/v2/draft/content.mdx:178; schema/v2/schema.unstable.json#/$defs/PromptRequest/properties/prompt; schema/v2/schema.unstable.json#/$defs/ResourceLink`. (The schema `ContentBlock` resource_link variant also says "All agents MUST support resource links in prompts.")
  - Tier unchanged (CAPABILITY, gate `capabilities.session`): the MUST binds "Agents that advertise `session`" (`initialization.mdx:308`); `content.mdx:178` says "All Agents", which is wider but not testable outside a session.
  - Test (`src/tck/v2/conformance/test_prompt.py:228-244`): no change. It sends `text` + `resource_link` and asserts a non-error result.
- **ACP-PROMPTCAP-001/002/003** (`requirements.py:409,424,439`): *citation-only change.* `initialization.mdx:246-271` -> `306-331` (heading "Session prompt capabilities" at :306, baseline MUST :308, `image` :312-316, `audio` :318-322, `embeddedContext` :324-331). `spec-impact --fix` will remap the numbers. The "Requires ... capability" lines in `content.mdx` are an extra primary source; add them by hand. Tier, text, gate and tests unchanged. The module docstring of `test_prompt_capabilities.py:11-12` must be edited once ACP-PROMPTCAP-004 lands (or deleted if it is not).
- Schema pointers cited by these rows (`PromptCapabilities`, `ImageContent`, `AudioContent`, `EmbeddedResource`, `ResourceLink`, `PromptRequest/properties/prompt`) all still exist in the target schema (verified by loading `$defs`). `tests/v2/test_registry.py` pointer resolution is unaffected.
- Wire changes B1-B12 (spec-diff-v2 section 5) hitting these rows: none found. `ResourceLink.size` `minimum: 0` is enforced by the Draft 2020-12 validator in `src/tck/v2/validation.py`. No v2 fixture or test emits `size` or `lastModified` (grep over `tests/fixtures/agents/v2/*.py` and `src/tck/v2/conformance/*.py`), and the validator has no `format_checker`, so the `date-time` removal has no TCK effect either way.

### New requirements (proposed)

Both rules cite the same sentence in three places. Citation set for both: `docs/protocol/v2/draft/content.mdx:22; docs/protocol/v2/draft/prompt-lifecycle.mdx:313; schema/v2/schema.unstable.json#/$defs/ContentBlock/anyOf/5 @ 3961af94fa62` (index 5 = the `other` variant, verified in the target schema).

**ACP-PROMPT-209**
- **Text:** A `session/prompt` whose `prompt` contains a content block of a type the agent has not advertised and cannot understand (a `_`-prefixed probe type such as `_tck_unadvertised_probe`) is answered with a JSON-RPC error with code `-32602`, and no `user_message`/`user_message_chunk` update is emitted for it.
- **Tier:** CAPABILITY, gate `capabilities.session`, like ACP-PROMPT-206/207. The wording is MUST ("Agents **MUST** reject ... with `-32602`, without inserting it", `prompt-lifecycle.mdx:313`; "Agents MUST reject a `session/prompt` request with a content block type they do not support with `-32602`", schema `ContentBlock` other variant).
- **Why unconditional on prompt sub-capabilities:** a custom type needs a custom capability (`prompt-lifecycle.mdx:313`, e.g. an entry in `capabilities.session.prompt._meta`). The TCK probe name is random and cannot be advertised, so the test never needs to inspect the agent's capabilities beyond `session`.
- **How a client-side TCK observes it:** open a session, send `session/prompt` with `[{"type":"text","text":"hi"},{"type":"_tck_unadvertised_probe","payload":"x"}]` (schema-valid via the `other` branch; the `_` prefix keeps the TCK's own traffic within the extensibility rule), read the response for that id, assert `error.code == -32602` and that no user-message update for the submission precedes it (reuse `_assert_no_user_message_on_error` logic from `test_prompt.py:247-256`). The agent must also stay usable: optional follow-up: a plain text prompt on the same session still succeeds (not part of the rule; skip unless wanted).
- **Suggested non-conforming fixtures:** `accepts_unknown_content_type.py` (current `ConformingAgent` already behaves this way, because `_prompt_rejection` defaults to `None` at `tests/fixtures/agents/v2/_base.py:606-610`). Trips only ACP-PROMPT-209 (and ACP-PROMPTCAP-004 if the agent does not advertise image/audio/resource, see below). A second variant: rejects with a wrong code (`-32600`) to check the code is judged.
- **Fixture baseline consequence (important):** to make the new rows PASS on the conforming fixtures, `ConformingAgent._prompt_rejection` default in `tests/fixtures/agents/v2/_base.py` must reject unknown types and unadvertised known types with `-32602`. Every fixture that inherits it changes behavior; the `accepts_*` fixtures then override it back. `tests/v2/test_cli.py` PASS/FAIL sets need the new ids added (it lists all ids per fixture at e.g. lines 64-68, 209-211, 332-334).

**ACP-PROMPTCAP-004** (negative-gate sibling)
- **Text:** For each of `image`, `audio`, `resource` that the agent does NOT advertise under `capabilities.session.prompt`, a prompt containing that block type alongside text is answered with `-32602` and no user-message update. SKIPPED when the agent advertises all three.
- **Tier:** CAPABILITY, gate `capabilities.session`. The wording is the same MUST ("neither baseline nor advertised"). `PromptCapabilities` omitted-or-`null` means "does not advertise" (`initialization.mdx:312-331`, schema `PromptCapabilities`), so the unadvertised state is observable from the initialize result.
- **Harness note:** the `@pytest.mark.capability(...)` marker only gates on "advertised". It has no inverse, so the test must read the negotiated capabilities at run time and `pytest.skip` per type. That is a small harness/test-design decision, not a spec question.
- **Risk / DECISION NEEDED:** this makes a client-visible MUST out of something many real agents may not enforce, and the TCK's v2 docstring deliberately avoided it. Recommendation: **adopt ACP-PROMPT-209 (unconditional probe) and ACP-PROMPTCAP-004, both CAPABILITY.** If cross-check shows widespread non-enforcement and the maintainers want less verdict churn, demote ACP-PROMPTCAP-004 to ADVISORY while keeping ACP-PROMPT-209 CAPABILITY. The spec's MUST is unambiguous, so I do not recommend demoting on spec grounds.
- **Suggested fixture:** `accepts_unadvertised_image.py`: advertises no `prompt.image`, accepts an `image` block. Trips only ACP-PROMPTCAP-004 (and 209 if it also accepts the probe, so make it accept only known types).

**Ambiguity noted (not blocking):** `prompt-lifecycle.mdx:313` says "or that they don't understand". An agent could advertise `image` yet fail to decode a malformed image; that is outside this rule. The TCK sends well-formed blocks only. Whether `-32602` applies to a recognized-but-malformed block is not stated for content blocks; no row proposed.

### Ledger entries for `content.mdx`

Citation form: `docs/protocol/v2/draft/content.mdx:<lines> @ 3961af94fa62`.

| Key | Citation | Statement | Reason |
|---|---|---|---|
| LEDGER-CNT-01 | :16 | Content from the Agent is untrusted. | client-side trust rule, unobservable (details in LEDGER-SEC-*) |
| LEDGER-CNT-02 | :18,20 | ACP `ContentBlock` is a superset of MCP's; Agents forward MCP tool output unchanged, and convert or omit later-MCP content types ACP doesn't define. | internal agent behavior; the TCK cannot feed MCP output. Wire shape is already covered by schema validation. |
| LEDGER-CNT-03 | :24 | Clients show text and a placeholder for unrenderable content and do not drop it silently; Agents also include text when content must reach the user in a particular form. | client display rule; agent half is a SHOULD about intent, unobservable |
| LEDGER-CNT-04 | :26,30 | Annotation `audience`/`priority` semantics; Clients MAY hide non-`user` content; Clients SHOULD render text as CommonMark and MAY support GFM. | client rendering rules, unobservable |

## Part 2: `security.mdx` (new, 81 lines)

Statements below are all of those with a normative keyword. Target lines in `docs/protocol/v2/draft/security.mdx`. The doc contains **MUST only at line 35**, and it binds Clients. The v2 page differs from v1's `security.mdx` only in the lines listed at the end of this part.

| Line | Statement | Wording | Binds | Observable by TCK? | Disposition |
|---|---|---|---|---|---|
| 13 | `info` in `initialize` not used for security decisions; Client identifies the Agent from launch configuration | SHOULD NOT / SHOULD | Any implementation / Client | No | LEDGER-SEC-04 |
| 21-28 | Rendering: no scripts, sanitize HTML, no auto-run active content, no auto-open links, confirm non-http(s), show full target, reveal bidi/zero-width/tag chars, neutralize terminal control sequences, keep Agent slash commands distinguishable; MAY bound/throttle | SHOULD (x7), SHOULD NOT (x3), MAY | Client | No | LEDGER-SEC-01, -02, -06 |
| 34 | Render images from `data`; do not fetch Agent-supplied remote URIs without user action | SHOULD / SHOULD NOT | Client | No | LEDGER-SEC-03 |
| 35 | **Icon `src`:** Clients accept only `https:`/`data:`, reject other schemes incl. `file:`; fetch without credentials; do not follow scheme- or origin-changing redirects; apply checks to every hop; Clients that display icons support PNG and JPEG | **MUST** (x5) | Client | No (the TCK is the client and does not display or fetch icons) | LEDGER-SEC-12 |
| 36 | Automatic fetches only `https:`/`data:`, no credentials, refuse loopback/private, bound size | SHOULD (x4) | Client | No | LEDGER-SEC-03 |
| 37 | No scripts in SVG | SHOULD NOT | Client | No | LEDGER-SEC-03 |
| 38 | No reading a `file:` URI outside the root set without user action | SHOULD NOT | Client | No | LEDGER-SEC-03 |
| 39 | Agents apply the root set and fetch rules to URIs in prompts | SHOULD | Agent | Only with a network canary; a quiet agent proves nothing | LEDGER-SEC-08 |
| 43 | No credentials in `_meta` (incl. `traceparent`, `tracestate`, `baggage`) | SHOULD NOT | Any implementation | Not generally ("credential" undefined) | LEDGER-SEC-07 |
| 48-50 | Treat embedded resources/files/tool/MCP results as data; request permission before off-machine sends after untrusted reads and before writing execution/approval-controlling files | SHOULD | Agent | No (model behavior) | LEDGER-SEC-09, -10 |
| 51 | Clients do not open links, run commands, change settings, or send data from Agent-authored text alone | SHOULD NOT | Client | No | LEDGER-SEC-02 |
| 52 | Clients send only trusted content as system prompt; Agents MAY reject it | SHOULD / MAY | Client / Agent | MAY is not requirable. The stated rejection MUSTs live in `session-setup.mdx` and are handled by the session-setup report. | LEDGER-SEC-05 |
| 56-57 | Use only trusted intermediaries; intermediaries do not answer permission requests/elicitations except under user policy and forward `subject` unchanged | SHOULD / SHOULD NOT | Client / Intermediary | No (the TCK is a direct client) | LEDGER-SEC-11 |
| 58 | Multi-user Agent scopes `session/list`, every session-naming request, permission requests, elicitations to the owning user; another user's session behaves as nonexistent (not listed, resume `-32002`, delete no-op); authorizes `cwd`/`additionalDirectories`/`mcpServers`; does not launch stdio MCP servers the user may not run | SHOULD (x3), SHOULD NOT | Agent | No (no user identity on the wire; deployment property) | LEDGER-SEC-13 |
| 62 | Custom transports document their security considerations | SHOULD | Transport author | No (documentation) | not ledgered (documentation duty) |
| 79 | Clients do not read a plan file `uri` outside the root set without user action | SHOULD NOT | Client | No | LEDGER-SEC-03 |
| 80 | Session-directed messages are Agent content; Clients attribute them to the sending session and do not present them as user messages | SHOULD / SHOULD NOT | Client | No | LEDGER-SEC-01 |
| 81 | Provider `headers` are credentials; Agents do not return them from `providers/list` | SHOULD NOT | Agent | Only if the TCK exercised `providers/*` (unstable; no v2 row touches it; `ProviderInfo` has no `headers` field, so only an extra, off-schema key would violate it) | LEDGER-SEC-09b below |

Pure prose, skipped: trust-model bullets without keywords (:10-12, :15), `:44` (IDs are not credentials), feature-guidance links (:64-71), residual-risk note (:75).

### Observable-agent-side analysis

I considered each Agent-bound statement for a deterministic client-driven check.

1. **:39 URI handling in prompts.** Needs a TCK-hosted listener to detect a fetch. Agents are not required to dereference `resource_link`, and a quiet agent proves nothing. Unsafe / out of scope.
2. **:43 credentials in `_meta`.** Only checkable by planting a sentinel secret. The natural carrier is MCP `env`/`headers` (`session-setup.mdx`, session-setup report) and the TCK does not currently send non-empty ones. Weak (a pass proves little), and "credential" is undefined. Belongs to a cross-doc candidate for the session-setup report, as in v1 (`impact-v1-security.md`, "Cross-doc candidate").
3. **:48-50 prompt injection.** Model behavior; the doc itself puts detecting injection out of scope (:15).
4. **:58 multi-user.** No user identity in ACP.
5. **:81 provider headers.** Not exercised by any TCK row. If a `providers` conformance area is ever added, a passive check "no `headers` key anywhere in a `providers/list` result" is deterministic and cheap. Until then, ledger.
6. **:35 icon MUSTs.** The TCK is the client and does not render or fetch icons. A passive agent-side companion exists: `Icon.src` schema text says "MUST be an `https:` or `data:` URI" (`schema/v2/schema.unstable.json#/$defs/Icon/properties/src`), but the schema has no `pattern`, only `format: uri`, and the validator has no format checker, so the TCK would not catch a `file:` icon from an agent, and it would only ever fire if the agent emits an icon (the baseline fixtures emit none; icons live on `ResourceLink.icons`, the only `$ref` to `Icon`). **DECISION NEEDED (low priority):** recommend ledger only. If the maintainers want it, the cheapest form is an ADVISORY passive scan of agent-emitted `resource_link` blocks for `icons[].src` scheme (SKIPPED when none observed), cited at the schema `Icon.src` description. I do not recommend it: agents rarely emit icons, and the rule's MUST subject is the Client.

**Result: no new requirements from `security.mdx`.**

### Ledger entries for `security.mdx`

Same shape as v1's proposals (`.agents/research/impact-v1-security.md`), adapted to v2 text. Citation form `docs/protocol/v2/draft/security.mdx:<lines> @ 3961af94fa62`. Format: see `spec-tracker/maps/v2.toml` header (`citation`, `statement`, `reason`).

| Key | Citation | Statement | Reason |
|---|---|---|---|
| LEDGER-SEC-01 | :21-28,80 | Clients neutralize scripts/HTML/active content/bidi, zero-width and tag characters/terminal control sequences; keep Agent slash commands distinguishable; attribute session-directed messages to the sending session | client-side rendering rules, unobservable |
| LEDGER-SEC-02 | :23-24,51 | Clients do not open links, run commands, change settings or send data from Agent text alone; show the full target and confirm non-http(s) | client-side, unobservable |
| LEDGER-SEC-03 | :34,36-38,79 | Client remote-URI fetch rules: render `data`, no unprompted fetches, https/data only, no credentials, refuse loopback/private, bound size, no SVG scripts, no out-of-root `file:` reads (incl. plan file `uri`) | client-side, unobservable |
| LEDGER-SEC-04 | :13 | `info` is self-reported and not used for security decisions; Client identifies the Agent from launch configuration | internal decision logic. The TCK only records `agentInfo` (`src/tck/common/plugin.py`). |
| LEDGER-SEC-05 | :52 | Clients send only trusted content as `systemPrompt`; Agents MAY reject it | client half is client-side, agent half is MAY. Stated MUST rejections stay with the session-setup rows. |
| LEDGER-SEC-06 | :28 | Clients MAY bound or throttle permission requests, elicitations, output | optional, client-side |
| LEDGER-SEC-07 | :43 | No credentials in `_meta` | "credential" undefined, no deterministic check; possible session-setup secret-echo candidate (see analysis item 2) |
| LEDGER-SEC-08 | :39 | Agents apply root-set and fetch rules to URIs in prompts | needs a network canary; a quiet agent proves nothing; TCK should not host listeners (unsafe / out of scope) |
| LEDGER-SEC-09 | :48; :81 (as "09b") | Agents treat embedded resources/files/tool/MCP results as data; Agents do not return provider `headers` from `providers/list` | 48: model behavior. 81: unstable `providers/*` not exercised by the TCK; `ProviderInfo` has no `headers` field. |
| LEDGER-SEC-10 | :49-50 | Agents request permission before off-machine sends after untrusted reads and before writing execution/approval-controlling files | needs a real tool-using turn with agent-specific triggers; permission requests are advisory (:12) |
| LEDGER-SEC-11 | :56-57 | Use trusted intermediaries only; intermediaries do not answer permission requests/elicitations except under user policy and forward `subject` unchanged | the TCK is a direct client with no intermediary |
| LEDGER-SEC-12 | :35 | Clients MUST accept only `https:`/`data:` icon URIs, fetch icons without credentials, not follow scheme/origin-changing redirects (every hop), and support PNG and JPEG | client-side MUSTs; the TCK neither displays nor fetches icons (agent-side companion discussed above) |
| LEDGER-SEC-13 | :58 | A multi-user Agent scopes sessions, permission requests, elicitations, `cwd`/`additionalDirectories`/`mcpServers` to the owning user; foreign sessions behave as nonexistent (`-32002`) | no user identity on the wire; deployment property |

### v1 vs v2 differences (for LEDGER reuse)

From `diff` of v1/v2 draft `security.mdx`: v2 adds the icon MUST bullet (:35) and "Apart from icons" qualifier (:38); `info` instead of `clientInfo`/`agentInfo` (:13); `subject` forwarding and the expanded multi-user rule with `-32002` (:57-58); an "Unstable features" section (:77-81); drops the v1 file-system/terminal client-performed note; links display-only terminals/diffs and elicitation URL security. Everything else is identical. LEDGER-SEC-11 / -12 / -13 and the :79-81 part of SEC-01/03/09 are v2-specific.

## Spec map (`spec-tracker/maps/v2.toml`)

- `content.mdx` and `security.mdx` are not in the map today (the file has no `content`/`security` entries). `ContentBlock` is already in `core_defs`.
- **Recommendation (DECISION NEEDED, orchestrator/maintainer):** add `content.mdx` as a whole-doc `[[core_doc]]` (no `sections`; its headings are now sentence-cased, `Content types`, `Text content`, `Image content`, `Audio content`, `Embedded resource`, `Resource link`, so a whole-doc entry avoids heading-address churn). Reason: it holds rules other areas assume without linking (text/resource_link MUSTs, unadvertised-content rejection, Markdown rule), and `ContentBlock` is already core. Suggested `reason`: "Baseline prompt content (`text`, `resource_link`), advertised-only content types and `-32602` rejection, Markdown/display rules that prompt, tool-call and session-update areas assume."
- **Do not add `security.mdx` as core.** All of it is client-side or SHOULD guidance, and the whole page is carried by ledger entries. It is the target of many links from other docs (`tool-calls.mdx#security`, `session-setup.mdx#security`, ...), so changes to it should show up through the ledger, not as a core hit that forces re-checks of every area. If the maintainers prefer visibility, add only the `## Trust model` and `## Unstable features` sections.
- Core-doc section addresses in my docs: none exist.

## Testability notes

- **ACP-PROMPT-209**: conforming = JSON-RPC error `-32602` (error object, not a result), response read, no user-message update for the submission. Non-conforming = success result (ignores the block), or any other error code, or a crash/hang (timeout is FAIL per the project's status rules), or an emitted user-message update followed by an error. The probe uses `_`-prefixed type, schema-valid via the `other` branch.
- **ACP-PROMPTCAP-004**: same observation per unadvertised type, with a runtime negative gate. All-advertised agents SKIP. Agents that do not enforce capabilities (common in lightweight agents) FAIL; hence the ADVISORY fallback offered above.
- Everything in `security.mdx` is unobservable from the client side or non-deterministic, as tabulated.
- Nothing in `content.mdx` display rules (:24-:30) is observable: the Agent cannot see how the Client renders.
- Annotations: agent-emitted `annotations.priority` range is already enforced by the generic schema validation; `lastModified` is now unconstrained by format in both schema and TCK, so no new check is possible or needed.

## Discrepancies

None found for the proposed rows: `content.mdx:22`, `prompt-lifecycle.mdx:313`, the `ContentBlock` other-variant description and `initialization.mdx:308` (baseline) agree. Minor wording gap only: `content.mdx:22` says "reject" without MUST; the MUST is in the other two places. Reference SDKs were not consulted, so I cannot say whether they enforce this.

One internal TCK inconsistency to fix: the `ACP-PROMPT-206` prose and the `test_prompt_capabilities.py` module docstring (:11-12) both assert the spec is silent/undefined on points that the target spec now defines.

## Open questions

1. **Ownership of the unadvertised-content-type rule.** Primary source is `prompt-lifecycle.mdx:313` (hunk in the prompt-lifecycle report's scope). The orchestrator should merge this proposal with that report's, keeping one id. I used `ACP-PROMPT-209`/`ACP-PROMPTCAP-004` (next free numbers in `requirements.py`: PROMPT-208 and PROMPTCAP-003 are last).
2. **Empty `prompt` array** (`prompt-lifecycle.mdx:311`: Clients MUST NOT send; Agents MAY reject with `-32602`). Adjacent, not mine. MAY, so not requirable; belongs to the prompt-lifecycle report.
3. **Dedicated text-MUST row** (`content.mdx:39`, "All Agents MUST support text content blocks")? Today covered implicitly by every prompt test. No row names it. Route to the orchestrator: probably leave implicit.
4. **TCK as a terminal-printing client** (`security.mdx:26`): carried over from the v1 security report (`src/tck/common/report.py` carries raw transcript/stderr). Not a conformance item.
5. **Session-setup secret-echo candidate** (security.mdx:43 + session-setup MCP `env`/`headers`): needs an owner in the session-setup report.
6. Whether `-32602` also applies to a recognized-but-malformed content block is unstated. No row proposed.
