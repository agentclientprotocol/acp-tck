# Spec change inventory, ACP v2 (Draft): `3961af94` -> `3ea94133`

**Sources checked:** agent-client-protocol (spec) read by ref from `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol` (user's feature branch `eugenethedev/end-turn-token-rfd-update`, working tree untouched; `git show`/`git diff` only), base `3961af94fa62d2386d993cadf1afc8b146fc799a`, target `3ea94133bb4e7cfdb1105df75660ff83e66acf62` ("docs: Update Cursor link with Grok Build reference (#2851)"; also the HEAD of `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`). 61 commits in range. TCK side read from `/Users/eugene/Documents/JetBrains/projects/acp-tck` (`spec-tracker/maps/v2.toml`, `src/tck/v2/requirements.py`, `src/tck/v2/schema/VENDORED.md`).
**Confidence:** high. `spec-impact` ran and exited 0; I cross-checked the stage table, the schema version and the doc-tree layout with direct `git show`/`git diff`.

## Headline

- v2 schema version: `2.0.0-alpha.14` -> `2.0.0-alpha.16` (two releases: alpha.15 on 2026-11-10 and alpha.16 on 2026-11-14). This is a v2 schema-version change, which the skill's depth rule says triggers a full audit. Read from `schema/v2/Cargo.toml` `version = ...` at each rev (base `2.0.0-alpha.14`, target `2.0.0-alpha.16`) and `schema/v2/CHANGELOG.md` headings. The base value also matches `src/tck/v2/schema/VENDORED.md` ("`2.0.0-alpha.14` as of the commit below"). Neither `schema.json`, `schema.unstable.json` nor `meta.unstable.json` carries a version field; `meta.unstable.json` only gained `"session_options": "session/options"`.
- `spec-impact` flags **core hit: yes, escalate** (`prompt-lifecycle.mdx` sections, plus `extensibility`, `initialization`, `session-setup`, `error`, `cancellation`, `content`, `transports`), **no `rfd_audit` marker** in `spec-tracker/maps/v2.toml` (so every tracked RFD is audited in full), 116 requirement ids and 30 ledger entries touched.
- The spec removed the RFD "Active" stage (commit `199fa7d1`, #2807). All 17 `rfds/v2/*` pages and `mcp-over-acp`, `streamable-http-websocket-transport` moved Active -> Draft. `subagents` moved Active -> **Preview**, `plan-operations` Draft -> **Preview**. Tracked RFDs for v2 at target are therefore only `subagents` and `plan-operations`.
- Subagents became a documented v2 feature: new `docs/protocol/v2/draft/subagents.mdx` (and a stable-tree copy `docs/protocol/v2/subagents.mdx`), and `SubagentUpdate`/`SessionMessage`/`ReplayComplete`/`IdempotencyKey` are now in the v2 **stable** `schema.json` (#2817).
- New wire features (unstable v2): `session/options`, initial config option values, `prompt_suggestions_update`, `cursor_update`/`cursorId`, `skill` command entries and `skill` content blocks, `speed` config category, `idempotencyKey` on `session/prompt`, `replay_complete`. Removed: `PlanFile` (file plans) in favour of an optional `path` on markdown plans.
- Tightened rules (SHOULD -> MUST): on `session/cancel`, the Agent must cancel abandoned pending permission and elicitation requests with `$/cancel_request` (cancellation.mdx, elicitation.mdx; #2852).

## 1. `spec-impact` output (verbatim)

Command, run from the acp-tck repo root, no `--fix`:

`uv run --package spec-tracker spec-impact 3961af94 3ea94133 --version v2 --spec-repo /Users/eugene/Documents/JetBrains/projects/agent-client-protocol`

Exit code 0. The script exists, so nothing was built by hand. The four `uv` build/install lines that preceded the report on stderr (`Building acp-tck ...`, a `uv-build` version warning, `Built ...`, `Uninstalled/Installed 1 package`) are omitted; everything from the `# Spec impact (v2)` heading on is unedited. Scope as printed: `docs/protocol/v2/draft/`, `schema/v2/`, `docs/rfds/`. Contents: section 1 changed files, 2 doc hunks, 3 core hits, 4 schema (`$defs` added/removed/changed and `$ref` closure), 5 link fan-out (706 links into changed docs), 6 affected entries, 7 RFD stages, then Summary.

~~~~markdown
# Spec impact (v2): `3961af94fa62` -> `3ea94133bb4e`

Base `3961af94fa62d2386d993cadf1afc8b146fc799a`, target `3ea94133bb4e7cfdb1105df75660ff83e66acf62`. Scope: `docs/protocol/v2/draft/`, `schema/v2/`, `docs/rfds/`.

## 1. Changed files

- modified: `docs/protocol/v2/draft/agent-plan.mdx`
- modified: `docs/protocol/v2/draft/authentication.mdx`
- modified: `docs/protocol/v2/draft/cancellation.mdx`
- modified: `docs/protocol/v2/draft/content.mdx`
- modified: `docs/protocol/v2/draft/elicitation.mdx`
- modified: `docs/protocol/v2/draft/error.mdx`
- modified: `docs/protocol/v2/draft/extensibility.mdx`
- modified: `docs/protocol/v2/draft/initialization.mdx`
- modified: `docs/protocol/v2/draft/overview.mdx`
- modified: `docs/protocol/v2/draft/prompt-lifecycle.mdx`
- modified: `docs/protocol/v2/draft/schema.mdx`
- modified: `docs/protocol/v2/draft/security.mdx`
- modified: `docs/protocol/v2/draft/session-config-options.mdx`
- modified: `docs/protocol/v2/draft/session-list.mdx`
- modified: `docs/protocol/v2/draft/session-setup.mdx`
- modified: `docs/protocol/v2/draft/slash-commands.mdx`
- added: `docs/protocol/v2/draft/subagents.mdx`
- modified: `docs/protocol/v2/draft/tool-calls.mdx`
- modified: `docs/protocol/v2/draft/transports.mdx`
- modified: `docs/rfds/TEMPLATE`
- modified: `docs/rfds/about.mdx`
- modified: `docs/rfds/additional-directories.mdx`
- added: `docs/rfds/agent-skills.mdx`
- modified: `docs/rfds/client-system-prompt.mdx`
- modified: `docs/rfds/end-turn-token-usage.mdx`
- modified: `docs/rfds/get-auth-state.mdx`
- modified: `docs/rfds/introduce-rfd-process.mdx`
- modified: `docs/rfds/plan-operations.mdx`
- added: `docs/rfds/prompt-suggestions.mdx`
- modified: `docs/rfds/request-cancellation.mdx`
- modified: `docs/rfds/session-archive.mdx`
- modified: `docs/rfds/session-close.mdx`
- modified: `docs/rfds/session-config-options.mdx`
- added: `docs/rfds/session-cursors.mdx`
- modified: `docs/rfds/session-fork.mdx`
- modified: `docs/rfds/session-notices.mdx`
- added: `docs/rfds/session-options.mdx`
- modified: `docs/rfds/session-resume.mdx`
- modified: `docs/rfds/session-set-title.mdx`
- modified: `docs/rfds/session-status.mdx`
- modified: `docs/rfds/session-usage.mdx`
- added: `docs/rfds/speed-config-category.mdx`
- modified: `docs/rfds/subagents.mdx`
- modified: `docs/rfds/tool-call-name.mdx`
- modified: `docs/rfds/updates.mdx`
- modified: `docs/rfds/v2/background-work.mdx`
- added: `docs/rfds/v2/idempotency-keys.mdx`
- modified: `docs/rfds/v2/meta-patches.mdx`
- modified: `docs/rfds/v2/overview.mdx`
- modified: `docs/rfds/v2/plan-variants.mdx`
- added: `docs/rfds/v2/session-replay-complete.mdx`
- modified: `docs/rfds/v2/session-resume-replay.mdx`
- modified: `schema/v2/CHANGELOG.md`
- modified: `schema/v2/Cargo.toml`
- modified: `schema/v2/meta.unstable.json`
- modified: `schema/v2/schema.json`
- modified: `schema/v2/schema.unstable.json`

## 2. Doc hunks -> sections

Base-side sections for removed or modified text, target-side for pure additions.

### `docs/protocol/v2/draft/agent-plan.mdx` (modified)

- `-69,1 +69,1` (base): `Unstable plan operations`
- `-92,1 +92,2` (base): `Unstable plan operations > Markdown plans`
- `-99,1 +100,3` (base): `Unstable plan operations > File plans`
- `-101,17 +104,6` (base): `Unstable plan operations > File plans`
- `-119,1 +111,1` (base): `Unstable plan operations > File plans`

### `docs/protocol/v2/draft/authentication.mdx` (modified)

- `-272,0 +273,2` (target): `Logging out`

### `docs/protocol/v2/draft/cancellation.mdx` (modified)

- `-30,0 +31,2` (target): ``$/cancel_request` notification`
- `-40,1 +42,1` (base): ``$/cancel_request` notification`

### `docs/protocol/v2/draft/content.mdx` (modified)

- `-19,0 +20,2` (target): `Content types`
- `-229,0 +232,21` (target): `Content types > Resource link` | `Content types > Skill reference (unstable)`

### `docs/protocol/v2/draft/elicitation.mdx` (modified)

- `-225,3 +225,4` (base): `Session cancellation`
- `-230,1 +231,3` (base): `Session cancellation`

### `docs/protocol/v2/draft/error.mdx` (modified)

- `-57,0 +58,2` (target): `Common cases > Unknown sessions`

### `docs/protocol/v2/draft/extensibility.mdx` (modified)

- `-31,8 +31,11` (base): `Experimental features and negotiation > When a capability is required`
- `-108,1 +111,1` (base): `The `_meta` field > Metadata patches`

### `docs/protocol/v2/draft/initialization.mdx` (modified)

- `-197,0 +198,73` (target): `Capabilities > Client capabilities > Session (unstable)`
- `-274,0 +348,7` (target): `Capabilities > Agent capabilities > Session capabilities`
- `-332,0 +413,14` (target): `Capabilities > Agent capabilities > Session prompt capabilities`

### `docs/protocol/v2/draft/overview.mdx` (modified)

- `-204,1 +204,2` (base): `Client > Notifications`
- `-208,2 +209,5` (base): `Client > Notifications`
- `-253,14 +257,13` (base): `Unstable features`
- `-273,0 +277,1` (target): `Next steps`

### `docs/protocol/v2/draft/prompt-lifecycle.mdx` (modified)

- `-16,25 +16,28` (base): `Session updates`
- `-54,10 +57,10` (base): `Session updates > Entity IDs`
- `-71,1 +74,3` (base): `Session updates > Session-directed messages (unstable)`
- `-137,1 +142,1` (base): `Session updates > Session-directed messages (unstable)`
- `-142,1 +147,6` (base): `Session updates > Session-directed messages (unstable)`
- `-182,1 +192,1` (base): `Foreground and background work > Background work`
- `-318,0 +329,6` (target): `Prompt lifecycle > 1. User message`
- `-372,1 +388,3` (base): `Prompt lifecycle > 2. Prompt accepted`
- `-384,1 +402,8` (base): `Prompt lifecycle > 2. Prompt accepted > Prompts during active work`
- `-391,0 +417,58` (target): `Prompt lifecycle > 2. Prompt accepted > Retrying a prompt`
- `-619,0 +703,67` (target): `Prompt lifecycle > 3. Agent reports output > Prompt suggestions (unstable)`
- `-758,0 +909,121` (target): `Prompt lifecycle > 3. Agent reports output > Session cursors (unstable)`
- `-783,0 +1055,2` (target): `Prompt lifecycle > 3. Agent reports output > Session usage updates`
- `-1015,1 +1288,1` (base): `Session states`
- `-1031,2 +1304,2` (base): `Session states`
- `-1042,1 +1315,1` (base): `Session states`
- `-1067,1 +1340,1` (base): `Session states > State transitions`
- `-1141,17 +1414,17` (base): `Session states > Lifecycle examples`
- `-1174,0 +1448,2` (target): `Cancellation`
- `-1177,1 +1452,1` (base): `Cancellation`

### `docs/protocol/v2/draft/schema.mdx` (modified)

- `-203,2 +203,2` (base): `Agent > auth/status > AuthStatusResponse`
- `-600,1 +600,1` (base): `Agent > session/cancel`
- `-803,0 +804,36` (target): `Agent > session/fork > ForkSessionRequest`
- `-982,0 +1019,20` (target): `Agent > session/new > NewSessionRequest`
- `-1043,0 +1100,101` (target): `Agent > session/new > NewSessionResponse` | `Agent > session/options` | `Agent > session/options > SessionOptionsRequest` | `Agent > session/options > SessionOptionsResponse`
- `-1087,0 +1245,19` (target): `Agent > session/prompt > PromptRequest`
- `-1183,0 +1360,23` (target): `Agent > session/resume > ResumeSessionRequest`
- `-1786,2 +1985,2` (base): `Client > auth/status_update > AuthStatusUpdateNotification`
- `-2241,1 +2440,1` (base): `Client > session/request_permission`
- `-2842,0 +3042,7` (target): `AuthAccount`
- `-3162,0 +3369,46` (target): `AvailableCommand`
- `-3172,2 +3424,2` (base): `AvailableCommand`
- `-3181,2 +3433,1` (base): `AvailableCommand`
- `-3273,4 +3523,0` (base): `BackgroundSubagent`
- `-3398,4 +3644,0` (base): `BackgroundWork`
- `-3602,0 +3846,52` (target): `ClientCapabilities` | `ClientSessionCapabilities`
- `-3667,0 +3963,57` (target): `CommandsCapabilities` | `CommandsSkillCapabilities`
- `-4041,0 +4394,34` (target): `ContentBlock`
- `-4121,1 +4507,430` (base): `Diff`
- `-5504,0 +6320,16` (target): `IdempotencyKey`
- `-5761,0 +6593,91` (target): `InitialSessionConfigOption`
- `-6650,30 +7571,0` (base): `PlanFile`
- `-6734,0 +7627,7` (target): `PlanMarkdown`
- `-6820,33 +7718,0` (base): `PlanUpdateContent`
- `-6871,0 +7738,7` (target): `PlanUpdateContent`
- `-6971,2 +7844,245` (base): `PromptCapabilities`
- `-6975,2 +8090,0` (base): `PromptCapabilities`
- `-6978,2 +8092,1` (base): `PromptCapabilities`
- `-6981,1 +8094,1` (base): `PromptCapabilities`
- `-6983,1 +8096,1` (base): `PromptEmbeddedContextCapabilities`
- `-6985,1 +8098,1` (base): `PromptEmbeddedContextCapabilities`
- `-6987,1 +8100,1` (base): `PromptEmbeddedContextCapabilities`
- `-7002,1 +8115,1` (base): `PromptImageCapabilities`
- `-7004,1 +8117,1` (base): `PromptImageCapabilities`
- `-7006,1 +8119,14` (base): `PromptImageCapabilities`
- `-7018,0 +8145,8` (target): `PromptSuggestionsUpdate`
- `-7132,0 +8267,29` (target): `ReplayComplete`
- `-7653,4 +8815,0` (base): `SessionCancelCapabilities`
- `-7746,0 +8906,12` (target): `SessionCapabilities`
- `-7942,0 +9114,9` (target): `SessionConfigOptionCategory`
- `-8208,4 +9387,0` (base): `SessionMessage`
- `-8267,4 +9442,0` (base): `SessionMessageChunk`
- `-8319,1 +9491,1` (base): `SessionReference`
- `-8324,0 +9497,20` (target): `SessionOptionsCapabilities` | `SessionReference`
- `-8963,4 +10154,0` (base): `SessionUpdate`
- `-9480,1 +10668,59` (base): `SessionUpdate`
- `-9484,0 +10731,44` (target): `SessionUpdate`
- `-9558,4 +10847,0` (base): `SessionUpdate`
- `-9621,4 +10906,0` (base): `SessionUpdate`
- `-9675,0 +10958,91` (target): `Skill` | `SkillReference`
- `-9962,4 +11334,0` (base): `StateUpdate`
- `-10156,4 +11524,0` (base): `SubagentSessionCapabilities`
- `-10164,0 +11530,2` (target): `SubagentSessionCapabilities`
- `-10185,4 +11551,0` (base): `SubagentUpdate`
- `-10221,0 +11585,2` (target): `SubagentUpdate`
- `-10876,4 +12240,0` (base): `ToolCallContent`
- `-11217,4 +12577,0` (base): `UnknownStateUpdate`
- `-11229,1 +12586,4` (base): `UnknownStateUpdate`

### `docs/protocol/v2/draft/security.mdx` (modified)

- `-21,0 +22,1` (target): `Rendering Agent content`
- `-79,2 +80,1` (base): `Unstable features`

### `docs/protocol/v2/draft/session-config-options.mdx` (modified)

- `-199,6 +199,7` (base): `Option categories`
- `-207,0 +209,2` (target): `Option categories`
- `-209,0 +213,12` (target): `Option categories > Speed options (unstable)`
- `-463,0 +479,107` (target): `Setting a config option > From the Agent` | `Options before a session exists (unstable)` | `Options before a session exists (unstable) > Querying options` | `Options before a session exists (unstable) > Initial values`

### `docs/protocol/v2/draft/session-list.mdx` (modified)

- `-6,1 +6,1` (base): `(intro)`

### `docs/protocol/v2/draft/session-setup.mdx` (modified)

- `-34,0 +35,1` (target): `(intro)`
- `-51,0 +53,1` (target): `Session lifecycle`
- `-55,1 +57,1` (base): `Session lifecycle`
- `-185,0 +188,5` (target): `Resuming sessions`
- `-209,1 +216,1` (base): `Resuming sessions`
- `-228,0 +236,1` (target): `Resuming sessions > Replay contents`
- `-295,1 +303,1` (base): `Resuming sessions > Replay contents`
- `-299,3 +307,11` (base): `Resuming sessions > Replay contents`
- `-303,3 +319,3` (base): `Resuming sessions > Replay contents`
- `-312,1 +328,1` (base): `Resuming sessions > Replay contents`
- `-320,0 +337,7` (target): `Resuming sessions > Replay contents`
- `-322,2 +345,2` (base): `Resuming sessions > Replay contents`
- `-336,0 +360,62` (target): `Resuming sessions > Replay complete` | `Resuming sessions > Replay complete > Child sessions`
- `-343,1 +428,1` (base): `Resuming sessions > Current-state synchronization`
- `-346,1 +431,1` (base): `Resuming sessions > Current-state synchronization`
- `-391,1 +476,1` (base): `Closing active sessions`
- `-508,0 +594,4` (target): `Initial config option values (unstable)`

### `docs/protocol/v2/draft/slash-commands.mdx` (modified)

- `-44,0 +45,2` (target): `Advertising commands > Initial commands`
- `-91,1 +93,1` (base): `Advertising commands > AvailableCommand`
- `-94,1 +96,2` (base): `Advertising commands > AvailableCommand`
- `-110,1 +113,1` (base): `Advertising commands > AvailableCommand`
- `-147,1 +150,1` (base): `Running commands`
- `-162,0 +166,94` (target): `Running commands` | `Skills (unstable)` | `Skills (unstable) > Invoking a skill`

### `docs/protocol/v2/draft/subagents.mdx` (added)

- `-0,0 +1,500` (target): `(intro)` | `Announcing a child session` | `Announcing a child session > Parents and nesting` | `Announcing a child session > What the Agent exposes` | `Child session updates` | `Child session updates > Working directories` | `Child session updates > Configuration` | `Messages between sessions` | `Messages between sessions > Messages from a parent to a child` | `Messages between sessions > Session references in tool calls` | `Messages between sessions > Session IDs in an update` | `Work state` | `Work state > Unknown state` | `Restricted methods` | `Cancellation` | `Cancellation > Pending requests` | `Closing the parent` | `Forking the parent (unstable)` | `Connection loss` | `Resuming` | `Resuming > What the Client keeps` | `Resuming > What the Agent sends` | `Resuming > Replayed child history` | `Usage and cost`

### `docs/protocol/v2/draft/tool-calls.mdx` (modified)

- `-326,1 +326,1` (base): `Requesting permission`
- `-457,1 +457,1` (base): `Status > Cancelling tool calls`
- `-459,1 +459,1` (base): `Status > Cancelling tool calls`
- `-603,1 +603,1` (base): `Content > Display-only terminals > Cancelling terminals`
- `-605,1 +605,1` (base): `Content > Display-only terminals > Cancelling terminals`
- `-728,1 +728,1` (base): `Content > Sessions (unstable)`
- `-730,2 +730,2` (base): `Content > Sessions (unstable)`
- `-749,2 +749,2` (base): `Content > Sessions (unstable)`
- `-752,0 +753,5` (target): `Content > Sessions`

### `docs/protocol/v2/draft/transports.mdx` (modified)

- `-45,1 +45,1` (base): `stdio > Shutdown`


## 3. Core hits

- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Session updates > (intro)`): `-16,25 +16,28`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Session updates > Entity IDs`): `-54,10 +57,10`, `-71,1 +74,3`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Foreground and background work`): `-182,1 +192,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `1. User message`): `-318,0 +329,6`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `2. Prompt accepted`): `-372,1 +388,3`, `-384,1 +402,8`, `-391,0 +417,58`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Session states`): `-1015,1 +1288,1`, `-1031,2 +1304,2`, `-1042,1 +1315,1`, `-1067,1 +1340,1`, `-1141,17 +1414,17`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx` (section `Cancellation`): `-1174,0 +1448,2`, `-1177,1 +1452,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_cancel.py`, `src/tck/v2/conformance/test_patches.py`, `src/tck/v2/conformance/test_permission.py`
- `docs/protocol/v2/draft/extensibility.mdx` (whole doc): `-31,8 +31,11`, `-108,1 +111,1`; code: `src/tck/v2/conformance/test_extensibility.py`, `src/tck/v2/conformance/test_enums.py`, `src/tck/v2/open_enums.py`, `src/tck/v2/validation.py`
- `docs/protocol/v2/draft/initialization.mdx` (whole doc): `-197,0 +198,73`, `-274,0 +348,7`, `-332,0 +413,14`; code: `src/tck/common/plugin.py`, `src/tck/v2/conformance/test_initialize.py`, `src/tck/v2/conformance/test_prompt_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Session lifecycle`): `-51,0 +53,1`, `-55,1 +57,1`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Resuming sessions`): `-185,0 +188,5`, `-209,1 +216,1`, `-228,0 +236,1`, `-295,1 +303,1`, `-299,3 +307,11`, `-303,3 +319,3`, `-312,1 +328,1`, `-320,0 +337,7`, `-322,2 +345,2`, `-336,0 +360,62`, `-343,1 +428,1`, `-346,1 +431,1`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/session-setup.mdx` (section `Closing active sessions`): `-391,1 +476,1`; code: `src/tck/v2/conformance/test_session.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`
- `docs/protocol/v2/draft/error.mdx` (whole doc): `-57,0 +58,2`; code: `src/tck/v2/protocol.py`, `src/tck/v2/conformance/test_jsonrpc.py`, `src/tck/v2/conformance/test_diagnostics.py`, `src/tck/v2/conformance/test_informational.py`, `src/tck/v2/conformance/test_errors.py`, `src/tck/v2/conformance/test_session_capabilities.py`, `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/validation.py`
- `docs/protocol/v2/draft/cancellation.mdx` (whole doc): `-30,0 +31,2`, `-40,1 +42,1`; code: `src/tck/v2/conformance/_helpers.py`, `src/tck/v2/conformance/test_cancel.py`
- `docs/protocol/v2/draft/content.mdx` (whole doc): `-19,0 +20,2`, `-229,0 +232,21`; code: `src/tck/v2/conformance/test_prompt.py`, `src/tck/v2/conformance/test_prompt_capabilities.py`
- `docs/protocol/v2/draft/transports.mdx` (whole doc): `-45,1 +45,1`; code: `src/tck/common/harness`, `src/tck/v2/conformance/test_transport.py`, `src/tck/v2/conformance/test_batch.py`, `src/tck/v2/conformance/test_diagnostics.py`, `src/tck/v2/validation.py`

## 4. Schema

`$defs` compared between base and target `schema/v2/schema.unstable.json` (`(root)` = everything outside `$defs`).

- Added: `ClientSessionCapabilities`, `CommandsCapabilities`, `CommandsSkillCapabilities`, `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor`, `CursorForkCapabilities`, `CursorId`, `CursorMessageAnchor`, `CursorToolCallAnchor`, `CursorUpdate`, `IdempotencyKey`, `InitialSessionConfigOption`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `PromptSuggestion`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `PromptSuggestionsUpdate`, `ReplayComplete`, `SessionOptionsCapabilities`, `SessionOptionsRequest`, `SessionOptionsResponse`, `Skill`, `SkillReference`
- Removed: `PlanFile`
- Changed: `AgentRequest`, `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork`, `ClientCapabilities`, `ClientNotification`, `ClientRequest`, `ContentBlock`, `ForkSessionRequest`, `NewSessionRequest`, `PlanMarkdown`, `PlanUpdateContent`, `PromptCapabilities`, `PromptRequest`, `ResumeSessionRequest`, `SessionCancelCapabilities`, `SessionCapabilities`, `SessionConfigOptionCategory`, `SessionMessage`, `SessionMessageChunk`, `SessionReference`, `SessionUpdate`, `StateUpdate`, `SubagentSessionCapabilities`, `SubagentUpdate`, `ToolCallContent`, `UnknownStateUpdate`
- `$ref` closure (35 defs that transitively reference a changed def):
  - `(root)` -> `AgentRequest`, `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork` and 52 more
  - `AgentCapabilities` -> `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`
  - `AgentMessage` -> `ContentBlock`, `SkillReference`
  - `AgentNotification` -> `AuthAccount`, `AuthStatusUpdateNotification`, `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork`, `ContentBlock`, `CursorAnchor`, `CursorAnchorPosition` and 26 more
  - `AgentThought` -> `ContentBlock`, `SkillReference`
  - `AvailableCommandsUpdate` -> `AvailableCommand`, `Skill`
  - `CompactionSummaryChunk` -> `ContentBlock`, `SkillReference`
  - `CompactionUpdate` -> `ContentBlock`, `SkillReference`
  - `ConfigOptionUpdate` -> `SessionConfigOptionCategory`
  - `Content` -> `ContentBlock`, `SkillReference`
  - `ContentChunk` -> `ContentBlock`, `SkillReference`
  - `ForkSessionResponse` -> `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
  - `IdleStateUpdate` -> `BackgroundSubagent`, `BackgroundWork`
  - `InitializeProxyRequest` -> `ClientCapabilities`, `ClientSessionCapabilities`, `CommandsCapabilities`, `CommandsSkillCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`
  - `InitializeProxyResponse` -> `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`
  - `InitializeRequest` -> `ClientCapabilities`, `ClientSessionCapabilities`, `CommandsCapabilities`, `CommandsSkillCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`
  - `InitializeResponse` -> `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`
  - `NewSessionResponse` -> `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
  - `PlanUpdate` -> `PlanFile`, `PlanMarkdown`, `PlanUpdateContent`
  - `ProxyRequest` -> `ClientCapabilities`, `ClientSessionCapabilities`, `CommandsCapabilities`, `CommandsSkillCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`
  - `ProxyResponse` -> `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`
  - `RequestPermissionRequest` -> `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`
  - `RequestPermissionSubject` -> `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`
  - `RequiresActionStateUpdate` -> `BackgroundSubagent`, `BackgroundWork`
  - `ResumeSessionResponse` -> `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
  - `RunningStateUpdate` -> `BackgroundSubagent`, `BackgroundWork`
  - `SessionConfigOption` -> `SessionConfigOptionCategory`
  - `SessionStatusResponse` -> `BackgroundSubagent`, `BackgroundWork`, `StateUpdate`, `UnknownStateUpdate`
  - `SetSessionConfigOptionResponse` -> `SessionConfigOptionCategory`
  - `SystemPrompt` -> `ContentBlock`, `SkillReference`
  - `ToolCallContentChunk` -> `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`
  - `ToolCallPermissionSubject` -> `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`
  - `ToolCallUpdate` -> `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`
  - `UpdateSessionNotification` -> `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork`, `ContentBlock`, `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor` and 24 more
  - `UserMessage` -> `ContentBlock`, `SkillReference`
- Core `$defs` hit: `SessionUpdate` (changed directly); `ContentBlock` (changed directly); `AgentCapabilities` (via $ref closure of `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`); `ClientCapabilities` (changed directly)

## 5. Link fan-out

Docs under `docs/protocol/v2/draft/` at target that link to a changed doc.

### `docs/protocol/v2/draft/agent-plan.mdx`

- `docs/protocol/v2/draft/extensibility.mdx:37` `#unstable-plan-operations` (changed section)
- `docs/protocol/v2/draft/overview.mdx:204`
- `docs/protocol/v2/draft/overview.mdx:267` `#unstable-plan-operations` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:32`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:33` `#removing-plans` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:539`
- `docs/protocol/v2/draft/schema.mdx:7482` `#plan-entries` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:7513` `#plan-entries` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:7543` `#plan-entries` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:10403`

### `docs/protocol/v2/draft/authentication.mdx`

- `docs/protocol/v2/draft/error.mdx:34`
- `docs/protocol/v2/draft/initialization.mdx:180`
- `docs/protocol/v2/draft/initialization.mdx:448`
- `docs/protocol/v2/draft/overview.mdx:82` `#logging-out` (changed section)
- `docs/protocol/v2/draft/security.mdx:68` `#launch-safety` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:10`

### `docs/protocol/v2/draft/cancellation.mdx`

- `docs/protocol/v2/draft/authentication.mdx:191`
- `docs/protocol/v2/draft/elicitation.mdx:227`
- `docs/protocol/v2/draft/error.mdx:33`
- `docs/protocol/v2/draft/extensibility.mdx:168`
- `docs/protocol/v2/draft/overview.mdx:218`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:341`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:405`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:413`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:458`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1446`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1452`
- `docs/protocol/v2/draft/schema.mdx:2741`
- `docs/protocol/v2/draft/schema.mdx:2747`
- `docs/protocol/v2/draft/session-setup.mdx:404`
- `docs/protocol/v2/draft/subagents.mdx:417`
- `docs/protocol/v2/draft/tool-calls.mdx:326`

### `docs/protocol/v2/draft/content.mdx`

- `docs/protocol/v2/draft/initialization.mdx:316`
- `docs/protocol/v2/draft/initialization.mdx:390`
- `docs/protocol/v2/draft/initialization.mdx:415` `#skill-reference-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:201`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:325`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:743`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:825`
- `docs/protocol/v2/draft/schema.mdx:4173`
- `docs/protocol/v2/draft/slash-commands.mdx:216` `#skill-reference-unstable` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:470`

### `docs/protocol/v2/draft/elicitation.mdx`

- `docs/protocol/v2/draft/authentication.mdx:179`
- `docs/protocol/v2/draft/cancellation.mdx:46` `#session-cancellation` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:34` `#checking-support` (unchanged section)
- `docs/protocol/v2/draft/initialization.mdx:194`
- `docs/protocol/v2/draft/overview.mdx:179`
- `docs/protocol/v2/draft/overview.mdx:190` `#url-completion` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:184`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1452` `#session-cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1995` `#url-completion` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:2024`
- `docs/protocol/v2/draft/schema.mdx:2044`
- `docs/protocol/v2/draft/security.mdx:72` `#user-interaction-requirements` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:72` `#url-security` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:476` `#session-cancellation` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:415` `#session-cancellation` (changed section)

### `docs/protocol/v2/draft/error.mdx`

- `docs/protocol/v2/draft/elicitation.mdx:59` `#unknown-methods` (unchanged section)
- `docs/protocol/v2/draft/initialization.mdx:90` `#requests-before-initialization` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:233`
- `docs/protocol/v2/draft/schema.mdx:9473` `#unknown-sessions` (changed section)
- `docs/protocol/v2/draft/session-delete.mdx:94` `#unknown-sessions` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:52` `#unknown-sessions` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:495` `#unknown-sessions` (changed section)

### `docs/protocol/v2/draft/extensibility.mdx`

- `docs/protocol/v2/draft/agent-plan.mdx:77` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/content.mdx:24` `#advertising-custom-capabilities` (unchanged section)
- `docs/protocol/v2/draft/initialization.mdx:156` `#unknown-object-fields` (unchanged section)
- `docs/protocol/v2/draft/initialization.mdx:158` `#advertising-custom-capabilities` (unchanged section)
- `docs/protocol/v2/draft/initialization.mdx:162` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/overview.mdx:251`
- `docs/protocol/v2/draft/overview.mdx:255` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/overview.mdx:278`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:47` `#enum-and-tagged-union-variants` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:125` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:323` `#advertising-custom-capabilities` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:578` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:648` `#enum-and-tagged-union-variants` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:650` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:774` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:887` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:918` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:950` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:984` `#enum-and-tagged-union-variants` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1112` `#experimental-features-and-negotiation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:56`
- `docs/protocol/v2/draft/schema.mdx:77`
- `docs/protocol/v2/draft/schema.mdx:113`
- `docs/protocol/v2/draft/schema.mdx:130`
- `docs/protocol/v2/draft/schema.mdx:168`
- `docs/protocol/v2/draft/schema.mdx:189`
- `docs/protocol/v2/draft/schema.mdx:242`
- `docs/protocol/v2/draft/schema.mdx:275`
- `docs/protocol/v2/draft/schema.mdx:331`
- `docs/protocol/v2/draft/schema.mdx:373`
- `docs/protocol/v2/draft/schema.mdx:397`
- `docs/protocol/v2/draft/schema.mdx:427`
- `docs/protocol/v2/draft/schema.mdx:448`
- `docs/protocol/v2/draft/schema.mdx:483`
- `docs/protocol/v2/draft/schema.mdx:520`
- `docs/protocol/v2/draft/schema.mdx:559`
- `docs/protocol/v2/draft/schema.mdx:583`
- `docs/protocol/v2/draft/schema.mdx:636`
- `docs/protocol/v2/draft/schema.mdx:683`
- `docs/protocol/v2/draft/schema.mdx:703`
- `docs/protocol/v2/draft/schema.mdx:729`
- `docs/protocol/v2/draft/schema.mdx:749`
- `docs/protocol/v2/draft/schema.mdx:794`
- `docs/protocol/v2/draft/schema.mdx:878`
- `docs/protocol/v2/draft/schema.mdx:921`
- `docs/protocol/v2/draft/schema.mdx:965`
- `docs/protocol/v2/draft/schema.mdx:1009`
- `docs/protocol/v2/draft/schema.mdx:1074`
- `docs/protocol/v2/draft/schema.mdx:1136`
- `docs/protocol/v2/draft/schema.mdx:1178`
- `docs/protocol/v2/draft/schema.mdx:1243`
- `docs/protocol/v2/draft/schema.mdx:1310`
- `docs/protocol/v2/draft/schema.mdx:1349`
- `docs/protocol/v2/draft/schema.mdx:1445`
- `docs/protocol/v2/draft/schema.mdx:1489`
- `docs/protocol/v2/draft/schema.mdx:1575`
- `docs/protocol/v2/draft/schema.mdx:1621`
- `docs/protocol/v2/draft/schema.mdx:1654`
- `docs/protocol/v2/draft/schema.mdx:1699`
- `docs/protocol/v2/draft/schema.mdx:1726`
- `docs/protocol/v2/draft/schema.mdx:1782`
- `docs/protocol/v2/draft/schema.mdx:1806`
- `docs/protocol/v2/draft/schema.mdx:1844`
- `docs/protocol/v2/draft/schema.mdx:1867`
- `docs/protocol/v2/draft/schema.mdx:1904`
- `docs/protocol/v2/draft/schema.mdx:1927`
- `docs/protocol/v2/draft/schema.mdx:1971`
- `docs/protocol/v2/draft/schema.mdx:2012`
- `docs/protocol/v2/draft/schema.mdx:2055`
- `docs/protocol/v2/draft/schema.mdx:2259`
- `docs/protocol/v2/draft/schema.mdx:2357`
- `docs/protocol/v2/draft/schema.mdx:2399`
- `docs/protocol/v2/draft/schema.mdx:2420`
- `docs/protocol/v2/draft/schema.mdx:2462`
- `docs/protocol/v2/draft/schema.mdx:2507`
- `docs/protocol/v2/draft/schema.mdx:2547`
- `docs/protocol/v2/draft/schema.mdx:2639`
- `docs/protocol/v2/draft/schema.mdx:2688`
- `docs/protocol/v2/draft/schema.mdx:2758`
- `docs/protocol/v2/draft/schema.mdx:2792`
- `docs/protocol/v2/draft/schema.mdx:2825`
- `docs/protocol/v2/draft/schema.mdx:2887` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2925` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2948`
- `docs/protocol/v2/draft/schema.mdx:2991`
- `docs/protocol/v2/draft/schema.mdx:3032`
- `docs/protocol/v2/draft/schema.mdx:3092`
- `docs/protocol/v2/draft/schema.mdx:3134`
- `docs/protocol/v2/draft/schema.mdx:3202`
- `docs/protocol/v2/draft/schema.mdx:3243`
- `docs/protocol/v2/draft/schema.mdx:3322`
- `docs/protocol/v2/draft/schema.mdx:3344`
- `docs/protocol/v2/draft/schema.mdx:3386`
- `docs/protocol/v2/draft/schema.mdx:3463`
- `docs/protocol/v2/draft/schema.mdx:3515`
- `docs/protocol/v2/draft/schema.mdx:3535`
- `docs/protocol/v2/draft/schema.mdx:3555`
- `docs/protocol/v2/draft/schema.mdx:3575`
- `docs/protocol/v2/draft/schema.mdx:3606`
- `docs/protocol/v2/draft/schema.mdx:3631`
- `docs/protocol/v2/draft/schema.mdx:3655`
- `docs/protocol/v2/draft/schema.mdx:3705`
- `docs/protocol/v2/draft/schema.mdx:3740`
- `docs/protocol/v2/draft/schema.mdx:3775`
- `docs/protocol/v2/draft/schema.mdx:3796`
- `docs/protocol/v2/draft/schema.mdx:3827`
- `docs/protocol/v2/draft/schema.mdx:3881`
- `docs/protocol/v2/draft/schema.mdx:3915`
- `docs/protocol/v2/draft/schema.mdx:3947`
- `docs/protocol/v2/draft/schema.mdx:3984`
- `docs/protocol/v2/draft/schema.mdx:4016`
- `docs/protocol/v2/draft/schema.mdx:4071`
- `docs/protocol/v2/draft/schema.mdx:4103` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:4132`
- `docs/protocol/v2/draft/schema.mdx:4152`
- `docs/protocol/v2/draft/schema.mdx:4191`
- `docs/protocol/v2/draft/schema.mdx:4222`
- `docs/protocol/v2/draft/schema.mdx:4267`
- `docs/protocol/v2/draft/schema.mdx:4304`
- `docs/protocol/v2/draft/schema.mdx:4375`
- `docs/protocol/v2/draft/schema.mdx:4411`
- `docs/protocol/v2/draft/schema.mdx:4469`
- `docs/protocol/v2/draft/schema.mdx:4496`
- `docs/protocol/v2/draft/schema.mdx:4533`
- `docs/protocol/v2/draft/schema.mdx:4559`
- `docs/protocol/v2/draft/schema.mdx:4585`
- `docs/protocol/v2/draft/schema.mdx:4611`
- `docs/protocol/v2/draft/schema.mdx:4637`
- `docs/protocol/v2/draft/schema.mdx:4663`
- `docs/protocol/v2/draft/schema.mdx:4754`
- `docs/protocol/v2/draft/schema.mdx:4782`
- `docs/protocol/v2/draft/schema.mdx:4811`
- `docs/protocol/v2/draft/schema.mdx:4847`
- `docs/protocol/v2/draft/schema.mdx:4874`
- `docs/protocol/v2/draft/schema.mdx:4914` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:4956`
- `docs/protocol/v2/draft/schema.mdx:4989`
- `docs/protocol/v2/draft/schema.mdx:5181`
- `docs/protocol/v2/draft/schema.mdx:5288`
- `docs/protocol/v2/draft/schema.mdx:5355`
- `docs/protocol/v2/draft/schema.mdx:5439`
- `docs/protocol/v2/draft/schema.mdx:5519`
- `docs/protocol/v2/draft/schema.mdx:5569`
- `docs/protocol/v2/draft/schema.mdx:5619`
- `docs/protocol/v2/draft/schema.mdx:5657`
- `docs/protocol/v2/draft/schema.mdx:5762`
- `docs/protocol/v2/draft/schema.mdx:5838`
- `docs/protocol/v2/draft/schema.mdx:5911`
- `docs/protocol/v2/draft/schema.mdx:5940`
- `docs/protocol/v2/draft/schema.mdx:5972`
- `docs/protocol/v2/draft/schema.mdx:6010`
- `docs/protocol/v2/draft/schema.mdx:6039`
- `docs/protocol/v2/draft/schema.mdx:6152`
- `docs/protocol/v2/draft/schema.mdx:6175`
- `docs/protocol/v2/draft/schema.mdx:6209`
- `docs/protocol/v2/draft/schema.mdx:6217`
- `docs/protocol/v2/draft/schema.mdx:6225`
- `docs/protocol/v2/draft/schema.mdx:6240`
- `docs/protocol/v2/draft/schema.mdx:6263`
- `docs/protocol/v2/draft/schema.mdx:6356`
- `docs/protocol/v2/draft/schema.mdx:6530`
- `docs/protocol/v2/draft/schema.mdx:6572`
- `docs/protocol/v2/draft/schema.mdx:6614`
- `docs/protocol/v2/draft/schema.mdx:6697`
- `docs/protocol/v2/draft/schema.mdx:6794`
- `docs/protocol/v2/draft/schema.mdx:6811`
- `docs/protocol/v2/draft/schema.mdx:6878`
- `docs/protocol/v2/draft/schema.mdx:6915`
- `docs/protocol/v2/draft/schema.mdx:6955`
- `docs/protocol/v2/draft/schema.mdx:6987`
- `docs/protocol/v2/draft/schema.mdx:7056`
- `docs/protocol/v2/draft/schema.mdx:7096`
- `docs/protocol/v2/draft/schema.mdx:7126`
- `docs/protocol/v2/draft/schema.mdx:7158`
- `docs/protocol/v2/draft/schema.mdx:7194`
- `docs/protocol/v2/draft/schema.mdx:7236`
- `docs/protocol/v2/draft/schema.mdx:7259`
- `docs/protocol/v2/draft/schema.mdx:7319`
- `docs/protocol/v2/draft/schema.mdx:7377`
- `docs/protocol/v2/draft/schema.mdx:7424`
- `docs/protocol/v2/draft/schema.mdx:7493`
- `docs/protocol/v2/draft/schema.mdx:7591`
- `docs/protocol/v2/draft/schema.mdx:7622`
- `docs/protocol/v2/draft/schema.mdx:7656`
- `docs/protocol/v2/draft/schema.mdx:7676`
- `docs/protocol/v2/draft/schema.mdx:7699`
- `docs/protocol/v2/draft/schema.mdx:7733`
- `docs/protocol/v2/draft/schema.mdx:7800`
- `docs/protocol/v2/draft/schema.mdx:7828`
- `docs/protocol/v2/draft/schema.mdx:7883`
- `docs/protocol/v2/draft/schema.mdx:7902`
- `docs/protocol/v2/draft/schema.mdx:7926`
- `docs/protocol/v2/draft/schema.mdx:7958`
- `docs/protocol/v2/draft/schema.mdx:7979`
- `docs/protocol/v2/draft/schema.mdx:8016`
- `docs/protocol/v2/draft/schema.mdx:8042`
- `docs/protocol/v2/draft/schema.mdx:8088`
- `docs/protocol/v2/draft/schema.mdx:8111`
- `docs/protocol/v2/draft/schema.mdx:8143`
- `docs/protocol/v2/draft/schema.mdx:8186`
- `docs/protocol/v2/draft/schema.mdx:8226`
- `docs/protocol/v2/draft/schema.mdx:8263`
- `docs/protocol/v2/draft/schema.mdx:8292`
- `docs/protocol/v2/draft/schema.mdx:8314`
- `docs/protocol/v2/draft/schema.mdx:8363`
- `docs/protocol/v2/draft/schema.mdx:8410`
- `docs/protocol/v2/draft/schema.mdx:8433`
- `docs/protocol/v2/draft/schema.mdx:8488`
- `docs/protocol/v2/draft/schema.mdx:8516`
- `docs/protocol/v2/draft/schema.mdx:8584`
- `docs/protocol/v2/draft/schema.mdx:8612`
- `docs/protocol/v2/draft/schema.mdx:8699`
- `docs/protocol/v2/draft/schema.mdx:8727`
- `docs/protocol/v2/draft/schema.mdx:8752`
- `docs/protocol/v2/draft/schema.mdx:8776`
- `docs/protocol/v2/draft/schema.mdx:8829`
- `docs/protocol/v2/draft/schema.mdx:8856`
- `docs/protocol/v2/draft/schema.mdx:8997`
- `docs/protocol/v2/draft/schema.mdx:9173`
- `docs/protocol/v2/draft/schema.mdx:9199`
- `docs/protocol/v2/draft/schema.mdx:9250`
- `docs/protocol/v2/draft/schema.mdx:9273`
- `docs/protocol/v2/draft/schema.mdx:9301`
- `docs/protocol/v2/draft/schema.mdx:9367` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9402` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9458`
- `docs/protocol/v2/draft/schema.mdx:9484`
- `docs/protocol/v2/draft/schema.mdx:9511`
- `docs/protocol/v2/draft/schema.mdx:9534`
- `docs/protocol/v2/draft/schema.mdx:9597`
- `docs/protocol/v2/draft/schema.mdx:9617`
- `docs/protocol/v2/draft/schema.mdx:9643`
- `docs/protocol/v2/draft/schema.mdx:9671`
- `docs/protocol/v2/draft/schema.mdx:9695`
- `docs/protocol/v2/draft/schema.mdx:9720`
- `docs/protocol/v2/draft/schema.mdx:9757` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9784`
- `docs/protocol/v2/draft/schema.mdx:9821` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9848`
- `docs/protocol/v2/draft/schema.mdx:9885` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9924`
- `docs/protocol/v2/draft/schema.mdx:9955`
- `docs/protocol/v2/draft/schema.mdx:10133`
- `docs/protocol/v2/draft/schema.mdx:10165`
- `docs/protocol/v2/draft/schema.mdx:10226`
- `docs/protocol/v2/draft/schema.mdx:10255` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10332` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10382`
- `docs/protocol/v2/draft/schema.mdx:10412`
- `docs/protocol/v2/draft/schema.mdx:10439`
- `docs/protocol/v2/draft/schema.mdx:10462`
- `docs/protocol/v2/draft/schema.mdx:10485`
- `docs/protocol/v2/draft/schema.mdx:10511` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10540`
- `docs/protocol/v2/draft/schema.mdx:10581`
- `docs/protocol/v2/draft/schema.mdx:10619` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10652`
- `docs/protocol/v2/draft/schema.mdx:10681`
- `docs/protocol/v2/draft/schema.mdx:10708`
- `docs/protocol/v2/draft/schema.mdx:10746` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10788` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10861` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10917`
- `docs/protocol/v2/draft/schema.mdx:10985`
- `docs/protocol/v2/draft/schema.mdx:11038`
- `docs/protocol/v2/draft/schema.mdx:11104`
- `docs/protocol/v2/draft/schema.mdx:11135`
- `docs/protocol/v2/draft/schema.mdx:11313`
- `docs/protocol/v2/draft/schema.mdx:11345`
- `docs/protocol/v2/draft/schema.mdx:11436`
- `docs/protocol/v2/draft/schema.mdx:11459`
- `docs/protocol/v2/draft/schema.mdx:11541`
- `docs/protocol/v2/draft/schema.mdx:11599` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11670`
- `docs/protocol/v2/draft/schema.mdx:11750`
- `docs/protocol/v2/draft/schema.mdx:11774`
- `docs/protocol/v2/draft/schema.mdx:11793`
- `docs/protocol/v2/draft/schema.mdx:11815`
- `docs/protocol/v2/draft/schema.mdx:11842`
- `docs/protocol/v2/draft/schema.mdx:11877`
- `docs/protocol/v2/draft/schema.mdx:11901`
- `docs/protocol/v2/draft/schema.mdx:11927`
- `docs/protocol/v2/draft/schema.mdx:11971` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12017`
- `docs/protocol/v2/draft/schema.mdx:12037`
- `docs/protocol/v2/draft/schema.mdx:12063`
- `docs/protocol/v2/draft/schema.mdx:12095`
- `docs/protocol/v2/draft/schema.mdx:12117`
- `docs/protocol/v2/draft/schema.mdx:12139`
- `docs/protocol/v2/draft/schema.mdx:12171`
- `docs/protocol/v2/draft/schema.mdx:12194`
- `docs/protocol/v2/draft/schema.mdx:12227`
- `docs/protocol/v2/draft/schema.mdx:12250`
- `docs/protocol/v2/draft/schema.mdx:12307`
- `docs/protocol/v2/draft/schema.mdx:12341`
- `docs/protocol/v2/draft/schema.mdx:12368`
- `docs/protocol/v2/draft/schema.mdx:12456` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12600`
- `docs/protocol/v2/draft/schema.mdx:12630`
- `docs/protocol/v2/draft/schema.mdx:12657`
- `docs/protocol/v2/draft/schema.mdx:12716`
- `docs/protocol/v2/draft/schema.mdx:12766` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/security.mdx:44` `#enum-and-tagged-union-variants` (unchanged section)
- `docs/protocol/v2/draft/session-list.mdx:136`
- `docs/protocol/v2/draft/session-list.mdx:198` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:331` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:115` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:114` `#metadata-patches` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:551` `#metadata-patches` (changed section)

### `docs/protocol/v2/draft/initialization.mdx`

- `docs/protocol/v2/draft/authentication.mdx:7`
- `docs/protocol/v2/draft/content.mdx:65` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/content.mdx:98` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/content.mdx:134` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/content.mdx:245` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/elicitation.mdx:27` `#client-capabilities` (changed section)
- `docs/protocol/v2/draft/error.mdx:36` `#version-negotiation` (unchanged section)
- `docs/protocol/v2/draft/error.mdx:62` `#before-initialization-completes` (unchanged section)
- `docs/protocol/v2/draft/error.mdx:70` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:35` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/overview.mdx:67`
- `docs/protocol/v2/draft/overview.mdx:259` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/overview.mdx:274`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:10`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:323` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:323`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:748` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:748` `#session-unstable` (changed section)
- `docs/protocol/v2/draft/schema.mdx:35`
- `docs/protocol/v2/draft/schema.mdx:223`
- `docs/protocol/v2/draft/schema.mdx:231`
- `docs/protocol/v2/draft/schema.mdx:264`
- `docs/protocol/v2/draft/schema.mdx:2814` `#agent-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:3816` `#client-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:7817` `#session-prompt-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8845` `#session-capabilities` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12619` `#version-negotiation` (unchanged section)
- `docs/protocol/v2/draft/session-delete.mdx:8`
- `docs/protocol/v2/draft/session-list.mdx:10`
- `docs/protocol/v2/draft/session-setup.mdx:8`
- `docs/protocol/v2/draft/slash-commands.mdx:173` `#session-prompt-capabilities` (changed section)

### `docs/protocol/v2/draft/overview.mdx`

- `docs/protocol/v2/draft/initialization.mdx:6` `#client` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:6` `#agent` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:6` `#agent` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:6` `#client` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:6` `#agent` (unchanged section)
- `docs/protocol/v2/draft/subagents.mdx:6` `#agent` (unchanged section)
- `docs/protocol/v2/draft/subagents.mdx:6` `#client` (changed section)

### `docs/protocol/v2/draft/prompt-lifecycle.mdx`

- `docs/protocol/v2/draft/agent-plan.mdx:8` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/authentication.mdx:243` `#failures` (unchanged section)
- `docs/protocol/v2/draft/cancellation.mdx:35` `#cancellation` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:40` `#state-transitions` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:61` `#cancellation` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:61` `#stop-reasons` (unchanged section)
- `docs/protocol/v2/draft/cancellation.mdx:61` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/cancellation.mdx:65` `#cancellation` (changed section)
- `docs/protocol/v2/draft/content.mdx:10` `#1-user-message` (changed section)
- `docs/protocol/v2/draft/content.mdx:11` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/elicitation.mdx:86` `#waiting-for-user-action` (unchanged section)
- `docs/protocol/v2/draft/elicitation.mdx:221` `#cancellation` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:36` `#session-notices` (unchanged section)
- `docs/protocol/v2/draft/extensibility.mdx:36` `#session-compaction` (unchanged section)
- `docs/protocol/v2/draft/extensibility.mdx:38` `#end-turn-token-usage-unstable` (unchanged section)
- `docs/protocol/v2/draft/extensibility.mdx:39` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:41` `#session-cursors-unstable` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:243` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:97` `#1-user-message` (changed section)
- `docs/protocol/v2/draft/overview.mdx:152` `#cancellation` (changed section)
- `docs/protocol/v2/draft/overview.mdx:199` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/overview.mdx:208` `#session-compaction` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:209` `#session-notices` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:211` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:213` `#session-cursors-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:268` `#end-turn-token-usage-unstable` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:276`
- `docs/protocol/v2/draft/schema.mdx:619` `#cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:625` `#cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1224`
- `docs/protocol/v2/draft/schema.mdx:1232` `#1-user-message` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1262` `#retrying-a-prompt` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1299` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2528` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2536` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/schema.mdx:3591` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6327` `#retrying-a-prompt` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6367` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6375` `#stop-reasons` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:7308` `#session-notices` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:8401` `#cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8595` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:8710` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9705` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9935` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9966` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9977` `#stop-reasons` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:10144` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:10176` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11090` `#session-states` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11115` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11146` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11157` `#stop-reasons` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:11324` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11356` `#background-work` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12611` `#background-work` (changed section)
- `docs/protocol/v2/draft/security.mdx:22` `#session-directed-messages` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:57` `#prompts-during-active-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:57` `#retrying-a-prompt` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:188` `#background-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:226` `#session-compaction` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:235` `#session-notices` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:236` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:292` `#entity-ids` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:297` `#entity-ids` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:337` `#session-cursors-unstable` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:392` `#session-notices` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:425` `#session-states` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:431` `#background-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:475` `#cancellation` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:476` `#background-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:480` `#prompts-during-active-work` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:480` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:774` `#session-notices` (unchanged section)
- `docs/protocol/v2/draft/slash-commands.mdx:6`
- `docs/protocol/v2/draft/slash-commands.mdx:152` `#2-prompt-accepted` (changed section)
- `docs/protocol/v2/draft/slash-commands.mdx:159` `#work-boundaries-and-local-commands` (unchanged section)
- `docs/protocol/v2/draft/subagents.mdx:15` `#session-directed-messages` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:75` `#background-work` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:196` `#entity-ids` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:256` `#session-directed-messages` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:313` `#session-states` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:356` `#background-work` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:360` `#session-states` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:386` `#cancellation` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:400` `#cancellation` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:409` `#cancellation` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:415` `#cancellation` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:440` `#background-work` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:487` `#session-notices` (unchanged section)
- `docs/protocol/v2/draft/subagents.mdx:492` `#session-usage-updates` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:6`
- `docs/protocol/v2/draft/tool-calls.mdx:8` `#3-agent-reports-output` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:125` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:209` `#waiting-for-user-action` (unchanged section)
- `docs/protocol/v2/draft/tool-calls.mdx:268` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:268` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:326` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:344` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:423` `#cancellation` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:423` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:587` `#background-work` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:750` `#session-directed-messages` (changed section)
- `docs/protocol/v2/draft/transports.mdx:45` `#retrying-a-prompt` (changed section)

### `docs/protocol/v2/draft/schema.mdx`

- `docs/protocol/v2/draft/authentication.mdx:153` `#authmethod` (unchanged section)
- `docs/protocol/v2/draft/cancellation.mdx:29` `#errorcode` (unchanged section)
- `docs/protocol/v2/draft/elicitation.mdx:273` `#elicitation%2Fcreate` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:64` `#initialize` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:72` `#auth%2Flogin` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:79` `#auth%2Flogout` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:87` `#session%2Fnew` (changed section)
- `docs/protocol/v2/draft/overview.mdx:95` `#session%2Fprompt` (changed section)
- `docs/protocol/v2/draft/overview.mdx:103` `#session%2Flist` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:110` `#session%2Fresume` (changed section)
- `docs/protocol/v2/draft/overview.mdx:118` `#session%2Fclose` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:129` `#session%2Fset_config_option` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:139` `#session%2Fdelete` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:149` `#session%2Fcancel` (changed section)
- `docs/protocol/v2/draft/overview.mdx:165` `#session%2Frequest_permission` (changed section)
- `docs/protocol/v2/draft/overview.mdx:177` `#elicitation%2Fcreate` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:187` `#elicitation%2Fcomplete` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:196` `#session%2Fupdate` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:45` `#sessionupdate` (changed section)

### `docs/protocol/v2/draft/security.mdx`

- `docs/protocol/v2/draft/content.mdx:16` `#rendering-agent-content` (changed section)
- `docs/protocol/v2/draft/content.mdx:16` `#uris-and-remote-resources` (unchanged section)
- `docs/protocol/v2/draft/content.mdx:32` `#rendering-agent-content` (changed section)
- `docs/protocol/v2/draft/overview.mdx:273`

### `docs/protocol/v2/draft/session-config-options.mdx`

- `docs/protocol/v2/draft/initialization.mdx:312` `#setting-a-config-option` (changed section)
- `docs/protocol/v2/draft/overview.mdx:133` `#from-the-client` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:207` `#from-the-agent` (changed section)
- `docs/protocol/v2/draft/overview.mdx:263` `#options-before-a-session-exists-unstable` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:35` `#from-the-agent` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1478` `#setting-a-config-option` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12559`
- `docs/protocol/v2/draft/session-list.mdx:164` `#from-the-agent` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:110`
- `docs/protocol/v2/draft/session-setup.mdx:596` `#options-before-a-session-exists-unstable` (changed section)
- `docs/protocol/v2/draft/slash-commands.mdx:45` `#options-before-a-session-exists-unstable` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:248` `#from-the-agent` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:69`

### `docs/protocol/v2/draft/session-list.mdx`

- `docs/protocol/v2/draft/error.mdx:68` `#archived-sessions-unstable` (unchanged section)
- `docs/protocol/v2/draft/initialization.mdx:339` `#archived-sessions-unstable` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:105`
- `docs/protocol/v2/draft/overview.mdx:261` `#archived-sessions-unstable` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:36` `#updating-session-metadata` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:528`
- `docs/protocol/v2/draft/subagents.mdx:122` `#updating-session-metadata` (unchanged section)
- `docs/protocol/v2/draft/subagents.mdx:381`

### `docs/protocol/v2/draft/session-setup.mdx`

- `docs/protocol/v2/draft/elicitation.mdx:236` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/error.mdx:50` `#system-prompt` (unchanged section)
- `docs/protocol/v2/draft/error.mdx:54` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/error.mdx:56` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:380` `#system-prompt` (unchanged section)
- `docs/protocol/v2/draft/initialization.mdx:474`
- `docs/protocol/v2/draft/overview.mdx:90` `#creating-a-session` (unchanged section)
- `docs/protocol/v2/draft/overview.mdx:113` `#resuming-sessions` (changed section)
- `docs/protocol/v2/draft/overview.mdx:121` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/overview.mdx:275`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:10`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:41` `#replay-complete` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:49` `#replay-contents` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:225` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:316` `#session-id` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:386` `#resuming-sessions` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:392` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:455` `#current-state-synchronization` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:768` `#replay-contents` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:902` `#replay-contents` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:993` `#replay-contents` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1333` `#current-state-synchronization` (changed section)
- `docs/protocol/v2/draft/schema.mdx:992`
- `docs/protocol/v2/draft/schema.mdx:998` `#creating-a-session` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:1063` `#creating-a-session` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:1434` `#current-state-synchronization` (changed section)
- `docs/protocol/v2/draft/schema.mdx:6899` `#mcp-servers` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:8281` `#replay-complete` (changed section)
- `docs/protocol/v2/draft/schema.mdx:9284` `#session-id` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:39` `#workspace-root-security` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:53` `#system-prompt` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:67` `#workspace-root-security` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:69` `#security` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:80` `#workspace-root-security` (unchanged section)
- `docs/protocol/v2/draft/session-config-options.mdx:10`
- `docs/protocol/v2/draft/session-config-options.mdx:390` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/session-config-options.mdx:584` `#initial-session-state` (unchanged section)
- `docs/protocol/v2/draft/session-delete.mdx:95` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:162` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:207` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:216` `#resuming-sessions` (changed section)
- `docs/protocol/v2/draft/session-list.mdx:247` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/slash-commands.mdx:12` `#initial-session-state` (unchanged section)
- `docs/protocol/v2/draft/subagents.mdx:218` `#working-directory` (unchanged section)
- `docs/protocol/v2/draft/subagents.mdx:379` `#session-lifecycle` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:425` `#closing-active-sessions` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:450` `#resuming-sessions` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:463` `#child-sessions` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:470` `#current-state-synchronization` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:480` `#replay-contents` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:486` `#child-sessions` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:488` `#replay-complete` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:779` `#workspace-root-security` (unchanged section)
- `docs/protocol/v2/draft/transports.mdx:43` `#session-lifecycle` (changed section)

### `docs/protocol/v2/draft/slash-commands.mdx`

- `docs/protocol/v2/draft/content.mdx:235` `#skills-unstable` (changed section)
- `docs/protocol/v2/draft/content.mdx:252` `#invoking-a-skill` (changed section)
- `docs/protocol/v2/draft/extensibility.mdx:40` `#skills-unstable` (changed section)
- `docs/protocol/v2/draft/initialization.mdx:266` `#skills-unstable` (changed section)
- `docs/protocol/v2/draft/overview.mdx:206` `#advertising-commands` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:34`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:343` `#running-commands` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:466` `#running-commands` (changed section)
- `docs/protocol/v2/draft/security.mdx:28`
- `docs/protocol/v2/draft/session-setup.mdx:110`
- `docs/protocol/v2/draft/subagents.mdx:212`

### `docs/protocol/v2/draft/subagents.mdx`

- `docs/protocol/v2/draft/error.mdx:58`
- `docs/protocol/v2/draft/error.mdx:58` `#restricted-methods` (changed section)
- `docs/protocol/v2/draft/overview.mdx:205`
- `docs/protocol/v2/draft/overview.mdx:277`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:24`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:147` `#messages-from-a-parent-to-a-child` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:192` `#work-state` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1055` `#usage-and-cost` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1288` `#work-state` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1448` `#cancellation` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11530` `#restricted-methods` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11585`
- `docs/protocol/v2/draft/session-list.mdx:6`
- `docs/protocol/v2/draft/session-setup.mdx:53`
- `docs/protocol/v2/draft/session-setup.mdx:53` `#restricted-methods` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:412` `#replayed-child-history` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:416` `#resuming` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:431` `#resuming` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:476` `#closing-the-parent` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:457` `#restricted-methods` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:603` `#restricted-methods` (changed section)
- `docs/protocol/v2/draft/tool-calls.mdx:731`

### `docs/protocol/v2/draft/tool-calls.mdx`

- `docs/protocol/v2/draft/content.mdx:12`
- `docs/protocol/v2/draft/overview.mdx:169` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/overview.mdx:202`
- `docs/protocol/v2/draft/overview.mdx:203` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:28` `#streaming-content` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:29` `#reporting` (unchanged section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:30` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:31` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:184` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:190` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:191` `#status` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1166` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1197`
- `docs/protocol/v2/draft/prompt-lifecycle.mdx:1450` `#status` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1833` `#cancelling-terminals` (changed section)
- `docs/protocol/v2/draft/schema.mdx:1893` `#cancelling-tool-calls` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2443` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/schema.mdx:2451` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/schema.mdx:4945` `#content` (changed section)
- `docs/protocol/v2/draft/schema.mdx:11804` `#cancelling-terminals` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12128` `#cancelling-tool-calls` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12157` `#content` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12330` `#following-the-agent` (unchanged section)
- `docs/protocol/v2/draft/schema.mdx:12386` `#status` (changed section)
- `docs/protocol/v2/draft/schema.mdx:12442`
- `docs/protocol/v2/draft/schema.mdx:12521` `#reporting` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:70` `#security` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:71` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/security.mdx:71` `#diffs` (unchanged section)
- `docs/protocol/v2/draft/session-setup.mdx:226` `#display-only-terminals` (changed section)
- `docs/protocol/v2/draft/session-setup.mdx:388` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:74` `#sessions` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:164` `#requesting-permission` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:296` `#sessions` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:374` `#cancelling-tool-calls` (changed section)
- `docs/protocol/v2/draft/subagents.mdx:374` `#display-only-terminals` (changed section)

### `docs/protocol/v2/draft/transports.mdx`

- `docs/protocol/v2/draft/overview.mdx:21` `#no-batches` (unchanged section)
- `docs/protocol/v2/draft/security.mdx:63` `#custom-transports` (unchanged section)

### `docs/rfds/agent-skills.mdx`

- `docs/protocol/v2/draft/slash-commands.mdx:169`

### `docs/rfds/get-auth-state.mdx`

- `docs/protocol/v2/draft/initialization.mdx:289`
- `docs/protocol/v2/draft/overview.mdx:265`

### `docs/rfds/plan-operations.mdx`

- `docs/protocol/v2/draft/overview.mdx:267`

### `docs/rfds/session-archive.mdx`

- `docs/protocol/v2/draft/overview.mdx:261`
- `docs/protocol/v2/draft/session-list.mdx:220`

### `docs/rfds/session-cursors.mdx`

- `docs/protocol/v2/draft/schema.mdx:4519`
- `docs/protocol/v2/draft/schema.mdx:4743`
- `docs/protocol/v2/draft/schema.mdx:4826`
- `docs/protocol/v2/draft/schema.mdx:4900`

### `docs/rfds/session-fork.mdx`

- `docs/protocol/v2/draft/initialization.mdx:343`
- `docs/protocol/v2/draft/overview.mdx:260`
- `docs/protocol/v2/draft/subagents.mdx:434`

### `docs/rfds/session-options.mdx`

- `docs/protocol/v2/draft/initialization.mdx:349`
- `docs/protocol/v2/draft/overview.mdx:263`
- `docs/protocol/v2/draft/session-config-options.mdx:482`

### `docs/rfds/session-set-title.mdx`

- `docs/protocol/v2/draft/initialization.mdx:362`
- `docs/protocol/v2/draft/overview.mdx:264`

### `docs/rfds/session-status.mdx`

- `docs/protocol/v2/draft/initialization.mdx:356`
- `docs/protocol/v2/draft/overview.mdx:262`
- `docs/protocol/v2/draft/session-list.mdx:250`

### `docs/rfds/speed-config-category.mdx`

- `docs/protocol/v2/draft/session-config-options.mdx:215`


## 6. Affected entries

- ACP-INIT-001: `#/$defs/InitializeResponse`: `InitializeResponse` in $ref closure of `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`
- ACP-INIT-201: `#/$defs/InitializeResponse/properties/protocolVersion`: `InitializeResponse` in $ref closure of `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`
- ACP-INIT-214: `#/$defs/InitializeRequest/properties/capabilities`: `InitializeRequest` in $ref closure of `ClientCapabilities`, `ClientSessionCapabilities`, `CommandsCapabilities`, `CommandsSkillCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`
- ACP-INIT-004: `#/$defs/InitializeResponse/properties/info`: `InitializeResponse` in $ref closure of `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`; `#/$defs/InitializeResponse/required`: `InitializeResponse` in $ref closure of `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`
- ACP-INIT-204: `#/$defs/AgentCapabilities`: `AgentCapabilities` in $ref closure of `PromptCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`, `SessionCapabilities`, `SessionOptionsCapabilities`; `#/$defs/SessionCapabilities`: `SessionCapabilities` changed
- ACP-SCHEMA-001: cites all of `docs/protocol/v2/draft/initialization.mdx`, which changed; `#/anyOf`: `(root)` in $ref closure of `AgentRequest`, `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork` and 52 more
- ACP-SESSION-001: `#/$defs/NewSessionRequest/required`: `NewSessionRequest` changed; `#/$defs/NewSessionResponse/required`: `NewSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
- ACP-PROMPT-002: `#/$defs/UpdateSessionNotification/required`: `UpdateSessionNotification` in $ref closure of `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork`, `ContentBlock`, `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor` and 24 more; `#/$defs/SessionUpdate`: `SessionUpdate` changed; `#/$defs/SubagentUpdate`: `SubagentUpdate` changed
- ACP-SUBAGENT-001: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/SubagentUpdate`: `SubagentUpdate` changed
- ACP-SUBAGENT-002: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-003: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-004: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-005: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-006: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/SubagentUpdate/properties/cwd`: `SubagentUpdate` changed; `#/$defs/SubagentUpdate/properties/additionalDirectories`: `SubagentUpdate` changed
- ACP-SUBAGENT-007: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-008: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-009: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-011: `docs/protocol/v2/draft/prompt-lifecycle.mdx:137-142` overlaps hunk `-137,1 +142,1`, `-142,1 +147,6`; `docs/rfds/subagents.mdx:648-664` overlaps hunk `-658,0 +678,7`
- ACP-SUBAGENT-012: `docs/protocol/v2/draft/prompt-lifecycle.mdx:137-142` overlaps hunk `-137,1 +142,1`, `-142,1 +147,6`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-013: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-014: `docs/rfds/subagents.mdx:392-419` overlaps hunk `-400,1 +400,1`
- ACP-SUBAGENT-201: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1015-1018` overlaps hunk `-1015,1 +1288,1`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/SubagentUpdate`: `SubagentUpdate` changed
- ACP-SUBAGENT-016: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/SubagentSessionCapabilities/properties/cancel`: `SubagentSessionCapabilities` changed
- ACP-SUBAGENT-017: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-202: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-PROMPT-203: `#/$defs/UserMessage`: `UserMessage` in $ref closure of `ContentBlock`, `SkillReference`; `#/$defs/ContentChunk`: `ContentChunk` in $ref closure of `ContentBlock`, `SkillReference`
- ACP-STATE-201: `#/$defs/StateUpdate`: `StateUpdate` changed
- ACP-STATE-203: `#/$defs/IdleStateUpdate/properties/stopReason`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`; `#/$defs/IdleStateUpdate/anyOf/6`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-STATE-204: `#/$defs/IdleStateUpdate`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-STATE-205: `#/$defs/RequiresActionStateUpdate`: `RequiresActionStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-STATE-206: `#/$defs/IdleStateUpdate/properties/background`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`; `#/$defs/RunningStateUpdate/properties/background`: `RunningStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-STATE-207: `#/$defs/BackgroundWork`: `BackgroundWork` changed
- ACP-STATE-209: cites changed RFD `docs/rfds/v2/background-work.mdx` (cited lines untouched)
- ACP-STATE-210: cites changed RFD `docs/rfds/v2/background-work.mdx` (cited lines untouched)
- ACP-PROMPT-003: `#/$defs/PromptRequest/properties/prompt`: `PromptRequest` changed
- ACP-PROMPT-209: `docs/protocol/v2/draft/prompt-lifecycle.mdx:384` overlaps hunk `-384,1 +402,8`
- ACP-PROMPT-211: `#/$defs/ContentBlock`: `ContentBlock` changed
- ACP-PROMPTCAP-001: `#/$defs/PromptCapabilities`: `PromptCapabilities` changed
- ACP-PROMPTCAP-002: `#/$defs/PromptCapabilities`: `PromptCapabilities` changed
- ACP-PROMPTCAP-003: `#/$defs/PromptCapabilities`: `PromptCapabilities` changed
- ACP-PROMPTCAP-201: `#/$defs/PromptCapabilities`: `PromptCapabilities` changed; `#/$defs/ContentBlock`: `ContentBlock` changed
- ACP-PERM-201: `#/$defs/RequestPermissionRequest/required`: `RequestPermissionRequest` in $ref closure of `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`; `#/$defs/RequestPermissionRequest/properties/options`: `RequestPermissionRequest` in $ref closure of `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`
- ACP-INFO-CONCURRENT-201: `docs/protocol/v2/draft/prompt-lifecycle.mdx:382-384` overlaps hunk `-384,1 +402,8`
- ACP-CANCEL-203: `#/$defs/IdleStateUpdate/anyOf/4`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-CANCEL-205: `#/$defs/ClientNotification/properties/params/anyOf/0/anyOf/0`: `ClientNotification` changed
- ACP-CANCEL-207: `#/$defs/IdleStateUpdate/anyOf/6`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-CANCEL-208: `docs/protocol/v2/draft/session-setup.mdx:389-395` overlaps hunk `-391,1 +476,1`
- ACP-CANCEL-209: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1153` overlaps hunk `-1141,17 +1414,17`; `docs/protocol/v2/draft/prompt-lifecycle.mdx:1177` overlaps hunk `-1177,1 +1452,1`; `docs/protocol/v2/draft/cancellation.mdx:40-43` overlaps hunk `-40,1 +42,1`; `docs/protocol/v2/draft/tool-calls.mdx:326` overlaps hunk `-326,1 +326,1`
- ACP-JSONRPC-007: `docs/protocol/v2/draft/prompt-lifecycle.mdx:384` overlaps hunk `-384,1 +402,8`
- ACP-CANCEL-213: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1177` overlaps hunk `-1177,1 +1452,1`; `docs/protocol/v2/draft/cancellation.mdx:40` overlaps hunk `-40,1 +42,1`
- ACP-CANCEL-214: `docs/protocol/v2/draft/prompt-lifecycle.mdx:384` overlaps hunk `-384,1 +402,8`
- ACP-INFO-CANCEL-201: `docs/protocol/v2/draft/prompt-lifecycle.mdx:1157` overlaps hunk `-1141,17 +1414,17`
- ACP-TRANSPORT-001: `#/anyOf`: `(root)` in $ref closure of `AgentRequest`, `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork` and 52 more
- ACP-JSONRPC-001: `#/$defs/AgentResponse`: `AgentResponse` changed
- ACP-JSONRPC-002: `#/$defs/AgentResponse`: `AgentResponse` changed
- ACP-JSONRPC-202: `#/$defs/AgentRequest`: `AgentRequest` changed
- ACP-SESSION-203: `#/$defs/NewSessionRequest/properties/mcpServers`: `NewSessionRequest` changed; `#/$defs/NewSessionRequest/required`: `NewSessionRequest` changed
- ACP-SESSION-204: `#/$defs/NewSessionRequest/properties/cwd`: `NewSessionRequest` changed
- ACP-SESSION-208: `#/$defs/NewSessionResponse`: `NewSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
- ACP-RESUME-001: `#/$defs/ResumeSessionRequest`: `ResumeSessionRequest` changed; `#/$defs/ResumeSessionResponse`: `ResumeSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
- ACP-RESUME-202: `docs/protocol/v2/draft/session-setup.mdx:207-209` overlaps hunk `-209,1 +216,1`; `docs/protocol/v2/draft/session-setup.mdx:225-229` overlaps hunk `-228,0 +236,1`; `docs/protocol/v2/draft/session-setup.mdx:321-323` overlaps hunk `-322,2 +345,2`
- ACP-RESUME-002: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-RESUME-205: `docs/protocol/v2/draft/session-setup.mdx:299-312` overlaps hunk `-299,3 +307,11`, `-303,3 +319,3`, `-312,1 +328,1`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-RESUME-206: `docs/protocol/v2/draft/session-setup.mdx:321-323` overlaps hunk `-322,2 +345,2`; `docs/protocol/v2/draft/session-setup.mdx:339-344` overlaps hunk `-343,1 +428,1`; `#/$defs/ResumeSessionResponse`: `ResumeSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
- ACP-RESUME-207: `#/$defs/ResumeSessionRequest/properties/replayFrom`: `ResumeSessionRequest` changed
- ACP-RESUME-208: `#/$defs/ResumeSessionRequest/properties/replayFrom`: `ResumeSessionRequest` changed
- ACP-RESUME-209: `docs/protocol/v2/draft/session-setup.mdx:207-209` overlaps hunk `-209,1 +216,1`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/UpdateSessionNotification`: `UpdateSessionNotification` in $ref closure of `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork`, `ContentBlock`, `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor` and 24 more
- ACP-RESUME-210: `#/$defs/ResumeSessionResponse`: `ResumeSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
- ACP-RESUME-213: `docs/protocol/v2/draft/session-setup.mdx:346` overlaps hunk `-346,1 +431,1`; `#/$defs/BackgroundWork`: `BackgroundWork` changed
- ACP-RESUME-217: `docs/protocol/v2/draft/session-setup.mdx:346` overlaps hunk `-346,1 +431,1`; `#/$defs/IdleStateUpdate/properties/background`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-CLOSE-001: `docs/protocol/v2/draft/session-setup.mdx:389-405` overlaps hunk `-391,1 +476,1`
- ACP-CLOSE-002: `docs/protocol/v2/draft/session-setup.mdx:389-393` overlaps hunk `-391,1 +476,1`
- ACP-CLOSE-205: `docs/protocol/v2/draft/session-setup.mdx:391` overlaps hunk `-391,1 +476,1`
- ACP-ARCHIVE-003: cites changed RFD `docs/rfds/session-archive.mdx` (cited lines untouched)
- ACP-ARCHIVE-006: cites changed RFD `docs/rfds/session-archive.mdx` (cited lines untouched)
- ACP-ADDDIRS-001: `#/$defs/NewSessionRequest/properties/additionalDirectories`: `NewSessionRequest` changed
- ACP-ADDDIRS-202: `#/$defs/ResumeSessionRequest/properties/additionalDirectories`: `ResumeSessionRequest` changed
- ACP-ADDDIRS-203: `#/$defs/NewSessionRequest/properties/additionalDirectories`: `NewSessionRequest` changed
- ACP-FORK-201: `#/$defs/ForkSessionResponse`: `ForkSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`; `#/$defs/ForkSessionResponse/properties/sessionId`: `ForkSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`; `#/$defs/SessionCapabilities/properties/fork`: `SessionCapabilities` changed
- ACP-FORK-202: cites changed RFD `docs/rfds/session-fork.mdx` (cited lines untouched)
- ACP-FORK-205: `#/$defs/ForkSessionResponse`: `ForkSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
- ACP-FORK-206: cites changed RFD `docs/rfds/v2/background-work.mdx` (cited lines untouched); `#/$defs/IdleStateUpdate/properties/background`: `IdleStateUpdate` in $ref closure of `BackgroundSubagent`, `BackgroundWork`
- ACP-SYSPROMPT-003: `#/$defs/SystemPrompt/properties/content`: `SystemPrompt` in $ref closure of `ContentBlock`, `SkillReference`
- ACP-MCP-204: `#/$defs/NewSessionRequest/properties/mcpServers`: `NewSessionRequest` changed
- ACP-CONFIG-201: `#/$defs/SessionConfigOption`: `SessionConfigOption` in $ref closure of `SessionConfigOptionCategory`; `#/$defs/SessionConfigOptionCategory`: `SessionConfigOptionCategory` changed
- ACP-CONFIG-002: cites changed RFD `docs/rfds/session-config-options.mdx` (cited lines untouched); `#/$defs/SetSessionConfigOptionResponse`: `SetSessionConfigOptionResponse` in $ref closure of `SessionConfigOptionCategory`
- ACP-CONFIG-203: `#/$defs/ResumeSessionResponse/properties/configOptions`: `ResumeSessionResponse` in $ref closure of `AvailableCommand`, `SessionConfigOptionCategory`, `Skill`
- ACP-CONFIG-206: cites changed RFD `docs/rfds/session-config-options.mdx` (cited lines untouched); `#/$defs/ConfigOptionUpdate`: `ConfigOptionUpdate` in $ref closure of `SessionConfigOptionCategory`
- ACP-CONFIG-211: `#/$defs/ConfigOptionUpdate`: `ConfigOptionUpdate` in $ref closure of `SessionConfigOptionCategory`
- ACP-CONFIG-212: `#/$defs/ConfigOptionUpdate`: `ConfigOptionUpdate` in $ref closure of `SessionConfigOptionCategory`
- ACP-COMMANDS-201: `docs/protocol/v2/draft/slash-commands.mdx:89-110` overlaps hunk `-91,1 +93,1`, `-94,1 +96,2`, `-110,1 +113,1`; `#/$defs/AvailableCommand`: `AvailableCommand` changed; `#/$defs/AvailableCommandsUpdate`: `AvailableCommandsUpdate` in $ref closure of `AvailableCommand`, `Skill`
- ACP-AUTH-007: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched); `#/$defs/AuthStatusResponse`: `AuthStatusResponse` changed
- ACP-PATCH-201: `#/$defs/ContentChunk`: `ContentChunk` in $ref closure of `ContentBlock`, `SkillReference`; `#/$defs/UserMessage`: `UserMessage` in $ref closure of `ContentBlock`, `SkillReference`; `#/$defs/AgentMessage`: `AgentMessage` in $ref closure of `ContentBlock`, `SkillReference`; `#/$defs/AgentThought`: `AgentThought` in $ref closure of `ContentBlock`, `SkillReference`
- ACP-PATCH-204: `#/$defs/ToolCallUpdate`: `ToolCallUpdate` in $ref closure of `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`; `#/$defs/ToolCallContentChunk`: `ToolCallContentChunk` in $ref closure of `ContentBlock`, `SessionReference`, `SkillReference`, `ToolCallContent`
- ACP-PATCH-205: `#/$defs/PlanUpdateContent`: `PlanUpdateContent` changed
- ACP-PATCH-211: `docs/protocol/v2/draft/session-setup.mdx:391` overlaps hunk `-391,1 +476,1`; cites changed RFD `docs/rfds/v2/background-work.mdx` (cited lines untouched)
- ACP-TOOLCANCEL-204: `docs/protocol/v2/draft/tool-calls.mdx:459` overlaps hunk `-459,1 +459,1`
- ACP-TOOLCANCEL-205: `docs/protocol/v2/draft/tool-calls.mdx:459` overlaps hunk `-459,1 +459,1`
- ACP-TOOLCANCEL-206: `docs/protocol/v2/draft/tool-calls.mdx:459` overlaps hunk `-459,1 +459,1`; cites changed RFD `docs/rfds/v2/background-work.mdx` (cited lines untouched)
- ACP-TOOLCANCEL-207: `docs/protocol/v2/draft/tool-calls.mdx:459` overlaps hunk `-459,1 +459,1`
- ACP-TOOLCANCEL-208: `docs/protocol/v2/draft/tool-calls.mdx:459` overlaps hunk `-459,1 +459,1`
- ACP-TOOLCANCEL-209: `docs/protocol/v2/draft/tool-calls.mdx:459` overlaps hunk `-459,1 +459,1`
- ACP-TOOLCANCEL-203: `docs/protocol/v2/draft/tool-calls.mdx:456-458` overlaps hunk `-457,1 +457,1`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-TERMCANCEL-201: `docs/protocol/v2/draft/tool-calls.mdx:600-604` overlaps hunk `-603,1 +603,1`
- ACP-TERMCANCEL-204: `docs/protocol/v2/draft/tool-calls.mdx:605` overlaps hunk `-605,1 +605,1`
- ACP-TERMCANCEL-205: `docs/protocol/v2/draft/tool-calls.mdx:605` overlaps hunk `-605,1 +605,1`
- ACP-TERMCANCEL-206: `docs/protocol/v2/draft/tool-calls.mdx:605` overlaps hunk `-605,1 +605,1`; cites changed RFD `docs/rfds/v2/background-work.mdx` (cited lines untouched)
- ACP-TERMCANCEL-207: `docs/protocol/v2/draft/tool-calls.mdx:605` overlaps hunk `-605,1 +605,1`
- ACP-TERMCANCEL-208: `docs/protocol/v2/draft/tool-calls.mdx:605` overlaps hunk `-605,1 +605,1`
- ACP-TERMCANCEL-209: `docs/protocol/v2/draft/tool-calls.mdx:605` overlaps hunk `-605,1 +605,1`
- ACP-TERMCANCEL-203: `docs/protocol/v2/draft/tool-calls.mdx:600-604` overlaps hunk `-603,1 +603,1`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-ENUM-201: `docs/protocol/v2/draft/slash-commands.mdx:110` overlaps hunk `-110,1 +113,1`; `#/$defs/BackgroundWork`: `BackgroundWork` changed
- ACP-META-201: `#/$defs/UpdateSessionNotification/properties/_meta`: `UpdateSessionNotification` in $ref closure of `AvailableCommand`, `BackgroundSubagent`, `BackgroundWork`, `ContentBlock`, `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor` and 24 more
- ACP-META-202: `#/$defs/PromptRequest/properties/_meta`: `PromptRequest` changed
- ACP-META-203: `docs/protocol/v2/draft/extensibility.mdx:108-115` overlaps hunk `-108,1 +111,1`
- ACP-ERROR-204: `#/$defs/AgentResponse`: `AgentResponse` changed
- ledger `The Agent responds to `session/prompt` once the message is inserted, without waiting for foreground work to finish.`: `docs/protocol/v2/draft/prompt-lifecycle.mdx:372` overlaps hunk `-372,1 +388,3`
- ledger `The Agent does not reuse an entity ID for a different entity of the same type within a session, including the `messageId` of session-directed messages (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `When the connection ends, an agent treats the requests it sent that have no response as failed.`: `docs/protocol/v2/draft/transports.mdx:45` overlaps hunk `-45,1 +45,1`
- ledger `At the end of the connection (stdin EOF), the agent's sessions stop being active.`: `docs/protocol/v2/draft/session-setup.mdx:55` overlaps hunk `-55,1 +57,1`
- ledger `Calling `auth/status` MUST NOT modify any agent state.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `An agent that supports `auth/status` SHOULD advertise `auth.status` in `agentCapabilities`.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `Agents SHOULD list the accounts and credentials they have configured in `auth/status` `accounts`, and SHOULD mark the ones in effect with `active: true`.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger ``auth/status` `accounts` MUST NOT include secrets.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `Agents SHOULD keep `auth/status` fast, answering `unknown` and sending `auth/status_update` later rather than blocking, and SHOULD return `unknown` rather than guess.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `Agents that advertise `auth.status` SHOULD send `auth/status_update` when their status changes (including after `auth/login` or `auth/logout`), and only when it differs from the last one sent on the connection.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched); `#/$defs/AuthStatusUpdateNotification`: `AuthStatusUpdateNotification` changed
- ledger `On `session/cancel` the Agent SHOULD cancel with `$/cancel_request` each pending elicitation the cancelled work made irrelevant, and before responding to `session/close` it MUST cancel every pending elicitation scoped to that session.`: `docs/protocol/v2/draft/elicitation.mdx:225-227` overlaps hunk `-225,3 +225,4`; `docs/protocol/v2/draft/session-setup.mdx:391` overlaps hunk `-391,1 +476,1`
- ledger `Closing, deleting or archiving an active session frees its resources, and closing also stops the session's background work.`: `docs/protocol/v2/draft/session-setup.mdx:391` overlaps hunk `-391,1 +476,1`
- ledger `Plan file URIs MUST be absolute.`: `docs/protocol/v2/draft/agent-plan.mdx:119` overlaps hunk `-119,1 +111,1`
- ledger `After cancellation completes, or once the work has ended, Agents SHOULD ignore late responses and URL completions rather than use them to resume the work.`: `docs/protocol/v2/draft/cancellation.mdx:40` overlaps hunk `-40,1 +42,1`
- ledger `An Agent reports a child directory that differs from the parent's before it sends child traffic that depends on it (MUST), and does not expose a child whose directories it cannot determine as sharing the parent's workspace (SHOULD NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `Agents report the narrowest directories a child needs (SHOULD), send current directory values after reconnecting when they differ (SHOULD), and report a new value or `null` when a child's directory no longer exists (MUST).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `An Agent does not guess a child's parentage, and does not temporarily announce a nested child under the root, whether live or when a replay cannot reconstruct the association truthfully (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `An Agent that keeps an operation unexposed does not later move an already-issued interaction to a different session, and once a child is exposed its new interactions use the child's session ID rather than falling back to the root (MUST NOT / MUST).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `After announcing a child the Agent sends its events automatically, without waiting for another Client request, and with no `session/attach`, `session/subscribe` or per-child opt-in.`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `An Agent reports each side of a session-directed message only when it can observe that side, and does not manufacture an incoming entry from an outgoing one.`: `docs/rfds/subagents.mdx:576-577` overlaps hunk `-577,1 +585,4`
- ledger `When observability of a child's foreground work is actually lost the Agent reports the `unknown` state as a `state_update` on the child's own stream, mirrored on the parent association (MUST), and not merely because the child has been quiet.`: `docs/rfds/subagents.mdx:855-860` overlaps hunk `-859,1 +885,4`; `#/$defs/UnknownStateUpdate`: `UnknownStateUpdate` changed
- ledger `Closing a parent session cancels all of its active descendant work, background children included, and releases the associated active resources, without requiring a new terminal-state notification.`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `A late response still resolves its original request, but the Agent does not use it to restart cancelled or otherwise abandoned work, or to authorize a new assignment to the same child (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `Replay (v2 `session/resume` with history) does not reissue recorded permission, elicitation or other Agent-to-Client requests (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `When replaying a recorded directed message the Agent does not invent either participant ID, and does not reinterpret its content as an ordinary message to or from the human user (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `The Agent does not manufacture a failure, cancellation or permanent orphan outcome for a child solely because the persisted history lacks a final update or a runtime could not be restored (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `Agents do not fabricate an exclusive parent or child cost amount from incomplete token counts or an aggregate total (MUST NOT).`: `docs/rfds/subagents.mdx:1168-1170` overlaps hunk `-1158,31 +1205,24`
- ledger ``session/status` answers an unknown session with `-32002` and the requested `sessionId` in `data`, reports an archived session as `saved`, and MUST NOT have side effects.`: cites changed RFD `docs/rfds/session-status.mdx` (cited lines untouched)
- ledger `After a successful `session/set_title` the agent SHOULD NOT replace the title with one it generates automatically, and SHOULD discard a title it was generating; a session that does not exist gets `-32002` and a title the agent rejects gets `-32602`.`: cites changed RFD `docs/rfds/session-set-title.mdx` (cited lines untouched)
- ledger `Agents receive `initialize` and are terminal; only a conductor sends `proxy/initialize`, and `proxy/successor` is exchanged only between a conductor and its proxies.`: `docs/protocol/v2/draft/overview.mdx:266` overlaps hunk `-253,14 +257,13`; `#/$defs/ProxyRequest`: `ProxyRequest` in $ref closure of `ClientCapabilities`, `ClientSessionCapabilities`, `CommandsCapabilities`, `CommandsSkillCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`

## 7. RFD stages

Stage = nearest stage group in `docs/docs.json` (Draft, Active, Preview, Completed), read at base and at target. Tracked = Active or Preview at target (all RFDs); Completed RFDs are never tracked.

Full RFD audit marker (`rfd_audit` in the spec map): **none: audit every tracked RFD in full, changed or not.**

Tracked at target:

- `docs/rfds/plan-operations.mdx` (Preview; changed, moved from Draft)
- `docs/rfds/subagents.mdx` (Preview; changed, moved from Active)

Stage moves (base -> target):

- `docs/rfds/agent-skills.mdx`: not listed -> Draft
- `docs/rfds/mcp-over-acp.mdx`: Active -> Draft
- `docs/rfds/plan-operations.mdx`: Draft -> Preview
- `docs/rfds/prompt-suggestions.mdx`: not listed -> Draft
- `docs/rfds/session-cursors.mdx`: not listed -> Draft
- `docs/rfds/session-options.mdx`: not listed -> Draft
- `docs/rfds/speed-config-category.mdx`: not listed -> Draft
- `docs/rfds/streamable-http-websocket-transport.mdx`: Active -> Draft
- `docs/rfds/subagents.mdx`: Active -> Preview
- `docs/rfds/v2/background-work.mdx`: Active -> Draft
- `docs/rfds/v2/client-filesystem-terminal-capabilities.mdx`: Active -> Draft
- `docs/rfds/v2/diff-file-states.mdx`: Active -> Draft
- `docs/rfds/v2/enum-variant-extension.mdx`: Active -> Draft
- `docs/rfds/v2/idempotency-keys.mdx`: not listed -> Draft
- `docs/rfds/v2/message-updates.mdx`: Active -> Draft
- `docs/rfds/v2/meta-patches.mdx`: Active -> Draft
- `docs/rfds/v2/overview.mdx`: Active -> Draft
- `docs/rfds/v2/permission-requests.mdx`: Active -> Draft
- `docs/rfds/v2/plan-variants.mdx`: Active -> Draft
- `docs/rfds/v2/prompt.mdx`: Active -> Draft
- `docs/rfds/v2/required-session-methods.mdx`: Active -> Draft
- `docs/rfds/v2/session-replay-complete.mdx`: not listed -> Draft
- `docs/rfds/v2/session-resume-replay.mdx`: Active -> Draft
- `docs/rfds/v2/terminal-output.mdx`: Active -> Draft
- `docs/rfds/v2/tool-call-updates.mdx`: Active -> Draft

## Summary

- Changed files: 57 (19 draft docs, 5 schema files, 33 RFDs); doc hunks: 141.
- `$defs`: 28 added, 1 removed, 31 changed; closure: 35.
- Links into changed docs: 706.
- Tracked RFDs: 2 (2 changed); stage moves: 25.
- Affected entries: 116 requirements, 30 ledger entries.
- Core hit: **yes, escalate** (`docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Session updates > (intro)`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Session updates > Entity IDs`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Foreground and background work`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `1. User message`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `2. Prompt accepted`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Session states`; `docs/protocol/v2/draft/prompt-lifecycle.mdx` > `Cancellation`; `docs/protocol/v2/draft/extensibility.mdx`; `docs/protocol/v2/draft/initialization.mdx`; `docs/protocol/v2/draft/session-setup.mdx` > `Session lifecycle`; `docs/protocol/v2/draft/session-setup.mdx` > `Resuming sessions`; `docs/protocol/v2/draft/session-setup.mdx` > `Closing active sessions`; `docs/protocol/v2/draft/error.mdx`; `docs/protocol/v2/draft/cancellation.mdx`; `docs/protocol/v2/draft/content.mdx`; `docs/protocol/v2/draft/transports.mdx`; `$defs/SessionUpdate`; `$defs/ContentBlock`; `$defs/AgentCapabilities`; `$defs/ClientCapabilities`)
~~~~

## 2. CHANGELOG entries and RFD status changes in the range

### `schema/v2/CHANGELOG.md` (`git diff 3961af94 3ea94133 -- schema/v2/CHANGELOG.md`, +30 lines; `[Unreleased]` is empty at target)

Version at base: `2.0.0-alpha.14` (`schema/v2/Cargo.toml:3`; top released heading `[2.0.0-alpha.14] - 2026-11-09`). Version at target: `2.0.0-alpha.16` (`schema/v2/Cargo.toml:3`; top released heading `[2.0.0-alpha.16] - 2026-11-14`). `Cargo.toml` also gained `rust-version.workspace = true` (irrelevant to the wire).

**2.0.0-alpha.16 (2026-11-14)**

Added:
- (unstable-v2) add skill command entries and skill content blocks (#2822)
- (unstable) add prompt suggestions session update and client capability (#2821)
- (unstable-v2) include subagents in v2 without `unstable_subagents` (#2817)
- (unstable) replace file plan type with path on markdown plans (#2815)
- (unstable-v2) add `replay_complete` session update (#2813)
- (unstable) add speed session config option category (#2809)
- (unstable) accept initial config options on `session/fork` and clarify notifications (#2794)

Other:
- (unstable-v2) ignore command types the client doesn't understand (#2816)
- (rust) fix clippy map_unwrap_or lint in schema generator (#2806)
- (unstable) clarify subagent message views, unknown state, and session references (#2801)

**2.0.0-alpha.15 (2026-11-10)**

Added:
- (unstable) add description to `AuthAccount` (#2793)
- (unstable) add `session/options` and initial config option values (#2792)
- (unstable) add session tool call content and clarify one-shot subagents (#2787)

Other:
- (unstable-v2) clarify `session/cancel` only cancels foreground work (#2776)

**Commits in the range that are not in the CHANGELOG but touch v2 (from `git log 3961af94..3ea94133`):** #2849 add subagents pages for v2 and the v1 draft; #2847 add `idempotencyKey` to `session/prompt`; #2846 method-aware payload dispatch (schema generator; `AgentRequest`/`AgentResponse`/`ClientRequest`/`ClientNotification` show as changed in the `$defs` diff); #2843 session cursors and `cursorId` on `session/fork`; #2857 what a resume without replay leaves out; #2856 clear every chunked entity before replaying its chunks; #2855 include descendants in a session's cost; #2854 close the `replay_complete` open questions; #2852 require Agents to cancel abandoned requests; #2850 say how a held prompt is dropped; #2811 order `thought_level` select values; #2808 clarify repeated `auth/logout` and cancel requests; #2804 mark `availableCommands` required in the slash-commands page.

### RFD status changes in the range

- #2807 (`199fa7d1`) "remove the Active lifecycle stage": `docs/docs.json` drops the "Active" group; `docs/rfds/about.mdx`, `introduce-rfd-process.mdx`, `v2/overview.mdx`, `updates.mdx` updated. Lifecycle is now Draft -> Preview -> Completed (plus "To be removed").
- #2800 (`12d4555a`) "move subagents to preview"; #2845 (`d70cc617`) "move plan operations to preview".
- New RFD pages (all Draft at target): `agent-skills` (#2818), `prompt-suggestions` (#2404), `session-cursors` (#2114), `session-options` (#2791), `speed-config-category`, `v2/session-replay-complete` (#2407), `v2/idempotency-keys` (#2810). Text edits (no stage move) to `get-auth-state`, `session-fork`, `v2/background-work`, `v2/meta-patches`, `v2/overview`, `v2/plan-variants`, `v2/session-resume-replay`, and (1-2 line edits) several Completed RFDs.
- `docs/docs.json` diff also adds `protocol/v1/draft/subagents`, `protocol/v2/subagents`, `protocol/v2/draft/subagents` to the doc navigation and moves the whole `rfds/v2` group from under "Active" to under "Draft".

## 3. RFD stages at base and target

Stage = nearest enclosing stage group in `docs/docs.json` (Draft/Active/Preview/Completed), computed independently with a script over `git show <rev>:docs/docs.json`; it matches `spec-impact` section 7 for every RFD. At base `rfds/v2/*` sat in "Active > v2"; at target the `v2` group sits inside "Draft" and there is no Active group.

**Stage moves (base -> target); `spec-impact` section 7 lists the same 25:**

| RFD page | Base | Target | In v2 schema/docs? |
|---|---|---|---|
| `rfds/subagents` | Active | **Preview** | yes: `SubagentUpdate`, `SessionMessage*`, ... in v2 stable and unstable schema |
| `rfds/plan-operations` | Draft | **Preview** | yes: `PlanMarkdown`, `PlanUpdateContent`, `plan_removed` in v2 unstable schema |
| `rfds/mcp-over-acp` | Active | Draft | n/a (Draft, not tracked) |
| `rfds/streamable-http-websocket-transport` | Active | Draft | n/a |
| `rfds/v2/background-work`, `client-filesystem-terminal-capabilities`, `diff-file-states`, `enum-variant-extension`, `message-updates`, `meta-patches`, `overview`, `permission-requests`, `plan-variants`, `prompt`, `required-session-methods`, `session-resume-replay`, `terminal-output`, `tool-call-updates` (14 pages) | Active | Draft | Draft, not tracked |
| `rfds/agent-skills`, `prompt-suggestions`, `session-cursors`, `session-options`, `speed-config-category`, `v2/idempotency-keys`, `v2/session-replay-complete` (7 new pages) | not listed | Draft | Draft, not tracked |

Unchanged stages that the TCK cites: `get-auth-state`, `session-fork`, `session-archive`, `session-set-title`, `session-status`, `proxy-chains`, `custom-llm-endpoint`, `end-turn-token-usage` all Draft; `session-config-options` Completed.

**Tracked RFDs for v2 (Active or Preview at target, wire shapes in v2 schema or applying to v2):**

| RFD | Stage at target | Changed in range? | Notes |
|---|---|---|---|
| `docs/rfds/subagents.mdx` | Preview (moved from Active) | yes: 212 lines changed (+ stage move) | Rules now also stated in new `docs/protocol/v2/draft/subagents.mdx` (docs take precedence per policy). `spec-impact` also lists it as changed with cited-lines-untouched for most citing rows. |
| `docs/rfds/plan-operations.mdx` | Preview (moved from Draft) | yes: 81 lines changed (+ stage move) | Now says v2 baseline is `plan_update` with items; adds markdown plans (with optional `path`) and `plan_removed`; file plans dropped. Documented in `docs/protocol/v2/draft/agent-plan.mdx` "Unstable plan operations" (docs govern). No requirement row or ledger entry in the TCK cites it today (grep of `requirements.py` and `v2.toml`: 0 hits). |

No other RFD is Active or Preview at target (the Active group no longer exists; Preview lists exactly these two). Completed RFDs are never tracked. `rfd_audit` is absent from `spec-tracker/maps/v2.toml`, so per the skill both are audited in full regardless of change.

**Stage labels in the TCK that become stale** (citation text in `src/tck/v2/requirements.py` / `spec-tracker/maps/v2.toml`): `docs/rfds/subagents.mdx` is labelled `(Active RFD)` in 22 places in `requirements.py` and 14 in `v2.toml` -> now Preview; `docs/rfds/v2/background-work.mdx` (6, `requirements.py`), `docs/rfds/v2/prompt.mdx` (2), `docs/rfds/mcp-over-acp.mdx` (1) are labelled `(Active RFD)` -> now Draft (so no longer tracked; docs govern where they state the rule). Other labels (`Draft`: `session-archive`, `session-fork`, `get-auth-state`, `proxy-chains`, `session-set-title`, `session-status`; `Completed`: `session-config-options`) are still correct.

## 4. One-line summary per changed area

**Docs, `docs/protocol/v2/draft/`** (19 files changed, 1 new; the TCK's tree, see 4a):

- `agent-plan.mdx`: file plans removed; markdown plans gain optional `path` (absolute; null/omitted = no file); `content` is always what to render.
- `authentication.mdx`: `auth/logout` is idempotent; Agent SHOULD return the same empty result when there is no state to end.
- `cancellation.mdx`: SHOULD -> MUST: on `session/cancel` the Agent cancels pending permission requests of the cancelled foreground work with `$/cancel_request` (Agent decides which belong); Clients SHOULD dismiss and answer `cancelled`.
- `content.mdx`: new `skill` content block ("Skill reference (unstable)"), new text in Content types intro.
- `elicitation.mdx`: SHOULD -> MUST for cancelling pending elicitations whose work was cancelled; Client SHOULD answer `cancel` on `$/cancel_request`.
- `error.mdx`: an announced child session is not an unknown session; other requests naming a child SHOULD get `-32602`.
- `extensibility.mdx`: unstable-feature table gains prompt suggestions, skills, session cursors; file plans dropped; `subagent_update`/`session_message` no longer "draft-only" in the `_meta` patch list.
- `initialization.mdx`: new client capabilities `session.promptSuggestions` and `session.commands.skill`; new agent capabilities `session.options` and `prompt.skill` (`PromptSkillCapabilities`, inline).
- `overview.mdx`: feature table gains Session options, drops Subagents and Unknown state rows; links the new Subagents page; notification list mentions prompt suggestions and cursors.
- `prompt-lifecycle.mdx` (core): `sessionUpdate` table adds `replay_complete`, `prompt_suggestions_update`, `cursor_update`; subagent/session-directed messages no longer "draft only"; new "Retrying a prompt" (`idempotencyKey`); held-prompt dropping text; new sections "Prompt suggestions (unstable)" and "Session cursors (unstable)"; session-usage/cost includes descendants; session-state and cancellation wording edits.
- `schema.mdx`: generated reference; mirrors the `$defs` changes in 4b.
- `security.mdx`: session-directed messages are Agent content (SHOULD attribute, SHOULD NOT show as user message); plan `path` instead of file `uri`.
- `session-config-options.mdx`: new `speed` category; new "Options before a session exists (unstable)" (`session/options`, initial values on `session/new`/`fork`/`resume`).
- `session-list.mdx`: `session/list` does not return child sessions.
- `session-setup.mdx` (core): new "Replay complete" section (`replay_complete` MUST be sent exactly once after the last replayed update and before the response; not sent without `replayFrom` or on `session/new`; held non-history updates come after it); chunked-entity first-update table for replay; cursor replay; prompt suggestions not replayed; resume-without-replay semantics; connection end may insert/discard held prompts; initial config option values.
- `slash-commands.mdx`: `availableCommands` required; unknown command types are ignored by the Client; new "Skills (unstable)" with `skill` entries and invocation via `skill` content block.
- `subagents.mdx` (NEW, 500 lines): child sessions, `subagent_update` announcement, nesting, working directories, config, messages between sessions, restricted methods, work state/unknown state, cancellation, closing/forking the parent, connection loss, resuming/replay, usage and cost.
- `tool-calls.mdx`: permission request cancelled by `$/cancel_request` -> Client SHOULD dismiss and answer `cancelled`; repeated `tool_call/cancel`/`terminal/cancel` after acceptance gets `-32602`; "Sessions" content item no longer unstable; `content` replacement keeps session references.
- `transports.mdx`: failed requests at connection end may still have taken effect; retry `session/prompt` with the same `idempotencyKey`.
- Unchanged in the draft tree: `session-delete.mdx`.

**Schema, `schema/v2/` (`schema.unstable.json` is what the TCK vendors)** (spec-impact section 4: 28 added, 1 removed, 31 changed, 35 in the `$ref` closure):

- Added, session options and config: `SessionOptionsRequest`, `SessionOptionsResponse`, `SessionOptionsCapabilities`, `InitialSessionConfigOption`; `SessionConfigOptionCategory` changed (adds `speed`); `NewSessionRequest`/`ForkSessionRequest`/`ResumeSessionRequest` changed (new `configOptions`; `ForkSessionRequest` also gains `cursorId`).
- Added, skills: `Skill`, `SkillReference`, `CommandsCapabilities`, `CommandsSkillCapabilities`, `PromptSkillCapabilities`, `PromptSkillInlineCapabilities`; `AvailableCommand`, `ContentBlock`, `PromptCapabilities` changed.
- Added, prompt suggestions: `PromptSuggestion`, `PromptSuggestionsUpdate`, `PromptSuggestionsCapabilities` (+ audio/image/embedded-context sub-capabilities), `ClientSessionCapabilities`; `ClientCapabilities` changed.
- Added, cursors: `CursorId`, `CursorAnchor`, `CursorAnchorPosition`, `CursorMessageAnchor`, `CursorToolCallAnchor`, `CursorCompactionAnchor`, `CursorCapabilities`, `CursorForkCapabilities`, `CursorUpdate`; `SessionUpdate` changed.
- Added, replay and idempotency: `ReplayComplete`, `IdempotencyKey`; `PromptRequest`, `SessionUpdate` changed.
- Removed: `PlanFile`; `PlanMarkdown` (gains `path`), `PlanUpdateContent` changed.
- Changed, subagents/state: `SubagentUpdate`, `SubagentSessionCapabilities` (cancel), `SessionCancelCapabilities`, `SessionMessage`, `SessionMessageChunk`, `SessionReference`, `ToolCallContent`, `StateUpdate`, `UnknownStateUpdate`, `BackgroundSubagent`, `BackgroundWork`.
- Changed, auth: `AuthAccount` (new `description`), `AuthStatusResponse`, `AuthStatusUpdateNotification` (changed `$defs` per spec-impact; nature of the change not examined here, `schema.mdx` shows 2-line hunks at `AuthStatusResponse` and `AuthStatusUpdateNotification`).
- Changed, dispatch envelopes: `AgentRequest`, `AgentResponse`, `ClientRequest`, `ClientNotification` (#2846 method-aware payload dispatch; `SessionCapabilities` also changed).
- `meta.unstable.json`: adds `session_options` -> `session/options`. Stable `schema.json` (not vendored) additionally gained `SubagentUpdate`, `SessionMessage`, `ReplayComplete`, `IdempotencyKey` (verified by `$defs` membership at both revs).

**RFDs** (33 files): see sections 2 and 3. Substantive edits: `subagents.mdx` (+212/-), `plan-operations.mdx`, `get-auth-state.mdx` (+27), `session-fork.mdx` (+70), `v2/background-work.mdx`, `v2/meta-patches.mdx`, `v2/plan-variants.mdx`, `v2/session-resume-replay.mdx`; seven new Draft RFDs; the rest are stage/lifecycle wording.

### 4a. Which doc tree the TCK uses, and tree layout

- The TCK's v2 citations and map use only the **`docs/protocol/v2/draft/`** tree: `grep -c "docs/protocol/v2/[a-z-]*\.mdx"` (non-draft paths) returns 0 in both `src/tck/v2/requirements.py` and `spec-tracker/maps/v2.toml`; `spec-tracker/maps/v2.toml:11` states "draft tree, `docs/protocol/v2/draft/*.mdx`"; `spec-impact` scopes itself to `docs/protocol/v2/draft/`. (Lines containing a draft-tree path: 290 in `requirements.py`, 101 in `v2.toml`.)
- The non-draft tree `docs/protocol/v2/*.mdx` is the stable v2 doc set; it also changed (17 files, +1615/-120, including `migration.mdx` and the new `subagents.mdx`), but `spec-impact` does not scan it and the TCK does not cite it.
- **New tree layout: no new tree.** Both trees already existed at base. What is new: `docs/protocol/v2/draft/subagents.mdx` (500 lines) **and** `docs/protocol/v2/subagents.mdx` (490 lines) both appeared in the range (neither existed at base; `docs/protocol/v1/draft/subagents.mdx` also appeared). The stable copy differs from the draft one by link prefixes (`/protocol/v2/...` vs `/protocol/v2/draft/...`) and omitted unstable sections (48 insertions/38 deletions between them). Before this, subagent rules for v2 lived only in `docs/rfds/subagents.mdx`, which the TCK's 22 + 14 subagent citations point to. This is the main new citable draft doc.
- `docs/docs.json` registers `protocol/v2/subagents`, `protocol/v2/draft/subagents` and `protocol/v1/draft/subagents`.

## 5. Requirement ids and ledger entries whose citations fall inside a change

`spec-impact` section 6 (inside the verbatim output above) lists them with the exact overlapping hunk or closure; this is the index. **116 requirement ids and 30 ledger entries**, all from `src/tck/v2/requirements.py` / `spec-tracker/maps/v2.toml`.

Grouped by trigger (an id can have more than one trigger; it is listed under the first that applies in the order doc hunk, schema `$def`, changed RFD only; see the output for all triggers):

- **Cited doc lines overlap a doc hunk, or the whole doc changed (41 ids):** `ACP-SCHEMA-001`, `ACP-SUBAGENT-011`, `ACP-SUBAGENT-012`, `ACP-SUBAGENT-014`, `ACP-SUBAGENT-201`, `ACP-PROMPT-209`, `ACP-INFO-CONCURRENT-201`, `ACP-CANCEL-208`, `ACP-CANCEL-209`, `ACP-JSONRPC-007`, `ACP-CANCEL-213`, `ACP-CANCEL-214`, `ACP-INFO-CANCEL-201`, `ACP-RESUME-202`, `ACP-RESUME-205`, `ACP-RESUME-206`, `ACP-RESUME-209`, `ACP-RESUME-213`, `ACP-RESUME-217`, `ACP-CLOSE-001`, `ACP-CLOSE-002`, `ACP-CLOSE-205`, `ACP-COMMANDS-201`, `ACP-PATCH-211`, `ACP-TOOLCANCEL-204`, `ACP-TOOLCANCEL-205`, `ACP-TOOLCANCEL-206`, `ACP-TOOLCANCEL-207`, `ACP-TOOLCANCEL-208`, `ACP-TOOLCANCEL-209`, `ACP-TOOLCANCEL-203`, `ACP-TERMCANCEL-201`, `ACP-TERMCANCEL-204`, `ACP-TERMCANCEL-205`, `ACP-TERMCANCEL-206`, `ACP-TERMCANCEL-207`, `ACP-TERMCANCEL-208`, `ACP-TERMCANCEL-209`, `ACP-TERMCANCEL-203`, `ACP-ENUM-201`, `ACP-META-203`
- **Cited `$def`/schema pointer changed or is in the `$ref` closure of a changed `$def` (59 ids):** `ACP-INIT-001`, `ACP-INIT-201`, `ACP-INIT-214`, `ACP-INIT-004`, `ACP-INIT-204`, `ACP-SESSION-001`, `ACP-PROMPT-002`, `ACP-SUBAGENT-001`, `ACP-SUBAGENT-006`, `ACP-SUBAGENT-016`, `ACP-PROMPT-203`, `ACP-STATE-201`, `ACP-STATE-203`, `ACP-STATE-204`, `ACP-STATE-205`, `ACP-STATE-206`, `ACP-STATE-207`, `ACP-PROMPT-003`, `ACP-PROMPT-211`, `ACP-PROMPTCAP-001`, `ACP-PROMPTCAP-002`, `ACP-PROMPTCAP-003`, `ACP-PROMPTCAP-201`, `ACP-PERM-201`, `ACP-CANCEL-203`, `ACP-CANCEL-205`, `ACP-CANCEL-207`, `ACP-TRANSPORT-001`, `ACP-JSONRPC-001`, `ACP-JSONRPC-002`, `ACP-JSONRPC-202`, `ACP-SESSION-203`, `ACP-SESSION-204`, `ACP-SESSION-208`, `ACP-RESUME-001`, `ACP-RESUME-207`, `ACP-RESUME-208`, `ACP-RESUME-210`, `ACP-ADDDIRS-001`, `ACP-ADDDIRS-202`, `ACP-ADDDIRS-203`, `ACP-FORK-201`, `ACP-FORK-205`, `ACP-FORK-206`, `ACP-SYSPROMPT-003`, `ACP-MCP-204`, `ACP-CONFIG-201`, `ACP-CONFIG-002`, `ACP-CONFIG-203`, `ACP-CONFIG-206`, `ACP-CONFIG-211`, `ACP-CONFIG-212`, `ACP-AUTH-007`, `ACP-PATCH-201`, `ACP-PATCH-204`, `ACP-PATCH-205`, `ACP-META-201`, `ACP-META-202`, `ACP-ERROR-204`
- **Only because they cite a changed RFD, cited lines untouched (16 ids):** `ACP-SUBAGENT-002`, `ACP-SUBAGENT-003`, `ACP-SUBAGENT-004`, `ACP-SUBAGENT-005`, `ACP-SUBAGENT-007`, `ACP-SUBAGENT-008`, `ACP-SUBAGENT-009`, `ACP-SUBAGENT-013`, `ACP-SUBAGENT-017`, `ACP-SUBAGENT-202`, `ACP-STATE-209`, `ACP-STATE-210`, `ACP-RESUME-002`, `ACP-ARCHIVE-003`, `ACP-ARCHIVE-006`, `ACP-FORK-202`

**Ledger entries (30):** printed in full in section 6 of the output (lines starting `- ledger`). By trigger: auth/status group (6 entries, cite changed `get-auth-state` RFD and `AuthStatusUpdateNotification`); subagents group (14 entries citing `docs/rfds/subagents.mdx`, two of them with overlapping hunks `-577,1 +585,4`, `-859,1 +885,4`, `-1158,31 +1205,24`); `session/status` and `session/set_title` entries (changed RFDs); transport-end, stdin-EOF, elicitation-cancel, close-frees-resources, "Plan file URIs MUST be absolute" (`agent-plan.mdx:119`, whose rule was removed with file plans), late-response-ignore (`cancellation.mdx:40`), prompt-accepted (`prompt-lifecycle.mdx:372`) and proxy/initialize (`overview.mdx:266`) entries (doc hunks).

## 6. Observations for the orchestrator (inventory only, not impact analysis)

- Depth triggers met: core hit, v2 schema version changed (`alpha.14` -> `alpha.16`), no `rfd_audit` in the map. Per `SKILL.md` step 3 these point to a full audit plus an audit of both tracked RFDs.
- The ledger entry "Plan file URIs MUST be absolute." cites a rule whose subject (`PlanFile`, `type: "file"`) no longer exists; the new rule is "`path` MUST be an absolute path" on markdown plans (`agent-plan.mdx` target text).
- Hunks in `cancellation.mdx`/`elicitation.mdx` change SHOULD to MUST for abandoned permission/elicitation requests; ledger entries and `ACP-CANCEL-209/-213/-214` rows cite these lines.
- The TCK vendors `schema.unstable.json` only; items that moved into the stable schema (`SubagentUpdate`, `SessionMessage`, `ReplayComplete`, `IdempotencyKey`) are still in the unstable file.
- `docs/protocol/v2/migration.mdx` (stable tree, +86/-86 lines) changed in the range and is not scanned by `spec-impact`; I did not read it.
