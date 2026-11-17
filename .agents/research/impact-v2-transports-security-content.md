# Impact (v2): transports.mdx, security.mdx, content.mdx, 3961af94 -> 3ea94133

**Sources checked:** agent-client-protocol @ `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (read with `git show 3ea94133:<path>`;
the checkout's HEAD is `6ace4f6a`, one commit later, which does not touch these three docs), diffed against `3961af94`.
Files: `docs/protocol/v2/draft/{transports,security,content}.mdx` (whole), linked sections in
`prompt-lifecycle.mdx` (:323, :417-473), `slash-commands.mdx` (:167-259), `initialization.mdx` (:386-425),
`session-setup.mdx` (:57), `schema/v2/schema.unstable.json` and `schema.json` (`SkillReference`, `PromptSkillCapabilities`,
`PromptSkillInlineCapabilities`, `CommandsCapabilities`, `ClientSessionCapabilities`, `ContentBlock`, `ProviderInfo`,
`ProviderCurrentConfig`), `docs/docs.json` (RFD stages). TCK: `src/tck/v2/requirements.py`, `spec-tracker/maps/v2.toml`,
`src/tck/v2/conformance/test_prompt_capabilities.py`, `test_prompt.py`, `_helpers.py`, `src/tck/v2/__init__.py`.
I did not consult the reference SDKs: none of the proposed rows depends on runtime behaviour the spec leaves open.
**Confidence:** high for the classifications and line maps (mechanical, checked against both revisions); medium on the
ownership split with the slash-commands researcher, because most `skill` rules live in `slash-commands.mdx`.

## What changed
- **transports.mdx**: only line 45 changed. Two sentences were added after the unchanged first one: "A failed request may still
  have taken effect. A Client can send a `session/prompt` again on a new connection with the same `idempotencyKey`."
  These sentences are descriptive or bind the client, and they point at `prompt-lifecycle.mdx#retrying-a-prompt`. No
  line numbers moved.
- **security.mdx**: the session-directed-messages bullet (Client SHOULD/SHOULD NOT) moved from "Unstable features" to
  "Rendering Agent content" as line 22, and its anchor lost `-unstable`. In "Unstable features", "plan file `uri`"
  became "a markdown plan's `path`" (Client SHOULD NOT). Both are client rules, so they add no row and no ledger
  entry. Line shifts: base 22-78 -> target 23-79. Base 79-80 became target 80. Base 81 stays 81.
- **content.mdx**: line 20 is new (the `skill` block is an ACP addition that MCP does not define). Lines 233-252 are a
  new section, "Skill reference (unstable)". Line shifts: base 20-231 -> target 22-233 (+2).
- `skill` is unstable only. `SkillReference`, `PromptSkillCapabilities` and the `skill` `ContentBlock` variant are in
  `schema/v2/schema.unstable.json` but not in `schema.json`. `docs/rfds/agent-skills.mdx` is a **Draft RFD**. The docs
  state every rule below, so the RFD is not cited.

## transports.mdx

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-TRANSPORT-001 | unchanged | `transports.mdx:20,23,67` | |
| ACP-TRANSPORT-002 | unchanged | `transports.mdx:6` | |
| ACP-TRANSPORT-203 | unchanged | `transports.mdx:21` | |
| ACP-BATCH-209 | unchanged (transports part) | `transports.mdx:65-67` | `overview.mdx:21` is another researcher's |
| ACP-ERROR-204 | unchanged (transports part) | `transports.mdx:24` | `error.mdx` part is another researcher's |
| ACP-SHUTDOWN-001 | unchanged | `transports.mdx:43` | line 43 text identical |
| ACP-STDERR-001 | unchanged | `transports.mdx:22` | |
| ACP-INFO-PARSE-001 | unchanged (transports part) | `transports.mdx:24` | |
| ACP-INFO-INVALIDREQ-001 | unchanged (transports part) | `transports.mdx:24` | |
| ledger `transports.mdx:61` (transports deliver in order) | unchanged | `transports.mdx:61` | |
| ledger `transports.mdx:45` (agent treats its unanswered requests as failed) | unchanged | `transports.mdx:45` | The cited sentence is unchanged. The two sentences added to the line bind the client. The statement and the reason ("not observable") still hold. |
| ledger `transports.mdx:43; session-setup.mdx:55` (sessions stop being active at EOF) | citation-only | `transports.mdx:43; session-setup.mdx:57` | session-setup line moved 55 -> 57. That line now also says "MAY insert or discard held prompts", which is a MAY and does not change the statement. |
| ledger `transports.mdx:10,71,73` (stdio SHOULD; custom transports MUST preserve…) | unchanged | `transports.mdx:10,71,73` | The reason is acceptable. The blocker is that ACP does not specify custom transports, so a client cannot speak one generically. That is not a TCK choice. |

Code comments citing transports lines (`validation.py:10`, `test_transport.py`, `test_batch.py`, `test_diagnostics.py`,
`test_informational.py`, fixtures) all point at unchanged lines. They need no edit.

## security.mdx

No registry row cites security.mdx.

| ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| `security.mdx:13` (`info` not used for security decisions) | unchanged | `security.mdx:13` | |
| `security.mdx:39` (Agents apply root set and fetch rules to prompt URIs) | citation-only | `security.mdx:40` | |
| `security.mdx:43` (no credentials in `_meta`) | citation-only | `security.mdx:44` | |
| `security.mdx:48,49,50` (prompt-injection SHOULDs) | citation-only | `security.mdx:49,50,51` | The reason's "(security.mdx:15)" is unchanged and still correct. |
| `security.mdx:58` (multi-user scoping) | citation-only | `security.mdx:59` | Unchanged pre-existing gap: the second sentence of the same line (authorize `cwd`/`additionalDirectories`/`mcpServers` per user; SHOULD NOT launch unpermitted stdio MCP servers) is not in the statement. The same reason (no user identity on the wire) covers it, so widening the statement is optional. |
| `security.mdx:81; …ProviderInfo` (no provider `headers` from `providers/list`) | unchanged citation; **reason flagged** | `security.mdx:81; schema/v2/schema.unstable.json#/$defs/ProviderInfo` | Base line 81 (provider headers) is target line 81. See the decision D3: part of the reason rests on a TCK choice. |

The new and moved client bullets (`:22` session-directed messages, `:80` markdown plan `path`) bind the client, so they are
not recorded.

## content.mdx

| id / ledger citation | classification | target citation (`@ 3ea94133`) | note |
|---|---|---|---|
| ACP-PROMPT-003 | citation-only | `content.mdx:180` (was 178) | |
| ACP-PROMPT-211 | citation-only | `content.mdx:24` (was 22) | `prompt-lifecycle.mdx:313` is now `:323`, which is the prompt-lifecycle researcher's to confirm. The `test_prompt.py:322` docstring cites `content.mdx:22` and needs the same remap. |
| ACP-PROMPTCAP-001 | citation-only | `content.mdx:64-66` (was 62-64) | |
| ACP-PROMPTCAP-002 | citation-only | `content.mdx:97-99` (was 95-97) | |
| ACP-PROMPTCAP-003 | citation-only | `content.mdx:133-135` (was 131-133) | |
| ACP-PROMPTCAP-201 | **changed text (recommended)**, else citation-only | `content.mdx:24,64-66,97-99,133-135,244-246` | See N1: add `skill` to the probed types. The `test_prompt_capabilities.py:160` docstring cites `content.mdx:22` and needs the remap. |
| ledger `content.mdx:18,20` (forward MCP content; convert/omit later MCP types) | citation-only | `content.mdx:18,22` | |
| ledger `content.mdx:24` (Agents also include content as text) | citation-only | `content.mdx:26` | |

The `core_doc` entry for content.mdx (`v2.toml:132`) still holds. Its reason could mention the `skill` block, which is
optional.

## New requirements

**N1. Extend ACP-PROMPTCAP-201 to cover `skill`. This is a changed row, not a new id.**
- Text addition: "…for each of `image`, `audio`, `resource` (embedded context) and `skill` (unstable) that the agent does
  NOT advertise under `capabilities.session.prompt`…"
- Tier and gate: CAPABILITY, `capabilities.session`, unchanged. This is the same rule (Rule B): a type that is neither
  baseline nor advertised is rejected with `-32602` and not inserted.
- Citation: `content.mdx:24,244-246`; `prompt-lifecycle.mdx:323` (the MUST); `slash-commands.mdx:255`;
  `schema/v2/schema.unstable.json#/$defs/PromptSkillCapabilities`.
- Test: add `"skill": ("capabilities.session.prompt.skill", lambda _: {"type": "skill", "name": "_tck_skill"})` to
  `_UNADVERTISED_CASES` in `test_prompt_capabilities.py`. The existing `_advertised` object-only logic and
  `assert_prompt_rejected_not_inserted` apply unchanged. When the capability is not advertised, the block's position
  does not matter. The case SKIPs when `prompt.skill` is an object (N2 covers that side).
- Harness: none. The v2 fixture agents must reject an unadvertised `skill` block. A fixture that treats it as an
  unknown type already does.

**N2. `ACP-PROMPTCAP-202` (provisional): a `skill` block that names no invocable skill is rejected.**
- Text: "When the agent advertises `capabilities.session.prompt.skill`, a prompt whose first block is
  `{type: skill, name: <TCK-generated name no agent lists>}` followed by text is answered with `-32602`, and the prompt
  is not inserted. That means no `user_message`/`user_message_chunk` and no `running`/`requires_action` within a short
  quiet period."
- Tier and gate: CAPABILITY, `capabilities.session.prompt.skill`, a real object marker.
- Citation: `slash-commands.mdx:253,255`; `content.mdx:244-250`;
  `schema/v2/schema.unstable.json#/$defs/SkillReference/properties/name` (its description also states the MUST).
- Test: use a fresh session and the default handshake. The TCK does not need to advertise `commands.skill`: an unlisted
  `_tck_no_such_skill_<uuid>` cannot resolve either way. Putting the block first keeps the position rule satisfied even
  without `inline`, so the only reason to reject is the name. Reuse `assert_prompt_rejected_not_inserted`. This is safe:
  a conforming agent runs nothing.
- Harness: none. The fixtures need one agent that advertises `prompt.skill` and rejects unknown names, and a
  non-conforming twin that accepts them.
- Ownership: the MUST lives in `slash-commands.mdx`. If the slash-commands researcher also proposes this row, keep one.

**N3. `ACP-CONTENT-2xx` (provisional; or `ACP-PROMPT-2xx`): the agent never emits a `skill` block outside user messages.**
- Text: "No `skill` content block appears in any agent-authored content other than a `user_message`/
  `user_message_chunk`. That covers agent message and thought chunks, tool-call content, compaction updates,
  permission-request subjects and prompt suggestions."
- Tier: ADVISORY. `content.mdx:252` ("appears only in user messages") carries no RFC 2119 keyword, and the schema does not
  enforce it: the `ContentBlock` union admits `skill` everywhere.
- Citation: `content.mdx:252`; `schema/v2/schema.unstable.json#/$defs/SkillReference`.
- Test: passive. Scan every `session/update` and agent->client request over the run, or the prompt turns of existing
  tests, for `ContentBlock` objects with `type == "skill"` outside user-message updates. It PASSes vacuously on almost
  every agent.
- Harness: a shared passive content-block walker, if one does not exist yet.

## New ledger entries

- **Citation:** `docs/protocol/v2/draft/content.mdx:252; docs/protocol/v2/draft/slash-commands.mdx:254,256 @ 3ea94133…`
  - **Statement:** "An Agent treats a `skill` block as the user invoking that skill, and reports the block as part of the
    inserted user message in `user_message` and in replay."
  - **Reason:** "Unsafe: it needs an accepted prompt that invokes a skill the agent lists, and running an arbitrary
    user-installed skill has side effects the TCK cannot predict. This is the same blocker as the command-invocation entry
    at base `slash-commands.mdx:149,157-160`, which is target `:152,160-163`."
  - Do not record it if the slash-commands researcher records the same rule; there should be one entry.

The transports.mdx:45 addition and the security.mdx changes need no new ledger entries. They bind clients, are
descriptive, or point at prompt-lifecycle.

## Decisions for the user

- **D1. Extend ACP-PROMPTCAP-201 with `skill` (N1), or add a separate row.** I recommend extending it: it is the same rule,
  Rule B says to keep the id, and the test is one more parametrize case. The alternative is a new
  `ACP-PROMPTCAP-2xx` that covers only `skill`.
- **D2. N3's tier.** I recommend ADVISORY with a passive check. The alternatives are a ledger entry ("descriptive, no
  keyword") or dropping it. If you consider it too vacuous to be worth a row, a ledger entry is acceptable.
- **D3. Existing ledger reason, `security.mdx:81` (provider `headers`).** "The TCK never obtains a populated
  `providers/list` result" rests on a TCK choice. When `capabilities.providers` is advertised, the TCK could call
  `providers/list`, which is read-only, and check that no `ProviderInfo` or `current` object carries a `headers` key.
  At target, `ProviderInfo` = {providerId, supported, required, current, _meta} and `ProviderCurrentConfig` =
  {apiType, baseUrl, _meta}, so only an extra key could violate the rule.
  - I recommend rewording it as "Deferred". The real blocker: the schema has no `headers` field in any agent response,
    so a violation is an off-schema nested key, which the validator's root-key check does not see. A useful check also
    needs a `providers/set` with a canary header first, and that would change persistent agent configuration (unsafe).
  - The alternative is an ADVISORY row gated on `capabilities.providers` that calls `providers/list` and checks that no
    `headers` key appears anywhere in the result, SKIPping when the list is empty.
  - This entry is not changed by this update; it is flagged per brief step 5.
- **D4. Ownership of N2 and the ledger entry.** Both rest mainly on `slash-commands.mdx`. Planning should dedupe them
  against the slash-commands report.

## Open questions (route elsewhere)

- These rules in `slash-commands.mdx` and `initialization.mdx` belong to those researchers and are not proposed here:
  - `slash-commands.mdx:171`: the Agent MUST NOT send `skill` entries unless the client supplied
    `capabilities.session.commands.skill`. The TCK sends `capabilities: {}`, so this is passively observable today.
  - `slash-commands.mdx:173` and `initialization.mdx:417-418`: an agent that sends `skill` entries MUST advertise
    `session.prompt.skill`. This is observable only if the TCK advertises `commands.skill`, which
    `connected_agent(capabilities=...)` already supports.
  - `slash-commands.mdx:238,255`: with `skill: {}` but no `inline`, a non-first or second `skill` block is rejected. A
    meaningful probe needs a listed, resolvable skill name. A conforming agent rejects without running anything, but a
    non-conforming one would run the skill.
- The `prompt-lifecycle.mdx:323` citation in ACP-PROMPT-211 and ACP-PROMPTCAP-201 (was `:313`) belongs to the
  prompt-lifecycle researcher.
- The idempotency rules that transports.mdx:45 now points to (`prompt-lifecycle.mdx:417-473`) belong to the
  prompt-lifecycle researcher. That includes "recognize the key … across connections and Agent restarts" at `:465`,
  which might be observable via a restart plus `session/resume`.
