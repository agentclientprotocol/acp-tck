# Spec change inventory: ACP v1, `3961af94` -> `3ea94133`

**Sources checked:** agent-client-protocol, base `3961af94fa62d2386d993cadf1afc8b146fc799a` (current pin in `src/tck/v1/schema/VENDORED.md`), target `3ea94133bb4e7cfdb1105df75660ff83e66acf62` (upstream/main), 61 commits between. Read by ref only from `/Users/eugene/Documents/JetBrains/projects/agent-client-protocol` (working tree untouched). Stage data re-derived independently from `docs/docs.json` at both revs and matches `spec-impact`.
**Confidence:** high. `spec-impact` ran cleanly (exit 0, no stderr), and its stage list was cross-checked by hand. This is an inventory only, with no impact analysis.

## Method

- `uv run --package spec-tracker spec-impact 3961af94 3ea94133 --version v1 --spec-repo <spec checkout>` ran from the acp-tck repo root, without `--fix`. It worked, so nothing was built by hand. The full output is in section 1.
- Its scope is `docs/protocol/v1/draft/`, `schema/v1/` and `docs/rfds/`. It does not cover v1 stable docs (`docs/protocol/v1/*.mdx` outside `draft/`). Section 4 handles those by hand.
- `spec-map` has no `rfd_audit` key in `spec-tracker/maps/v1.toml` (`spec-impact` also says "none"). This is the first run under the RFD policy, so **every tracked RFD goes to impact research in full, changed or not**.

## 1. Full `spec-impact` output (verbatim)

### Spec impact (v1): `3961af94fa62` -> `3ea94133bb4e`

Base `3961af94fa62d2386d993cadf1afc8b146fc799a`, target `3ea94133bb4e7cfdb1105df75660ff83e66acf62`. Scope: `docs/protocol/v1/draft/`, `schema/v1/`, `docs/rfds/`.

## 1. Changed files

- modified: `docs/protocol/v1/draft/agent-plan.mdx`
- modified: `docs/protocol/v1/draft/error.mdx`
- modified: `docs/protocol/v1/draft/initialization.mdx`
- modified: `docs/protocol/v1/draft/overview.mdx`
- modified: `docs/protocol/v1/draft/prompt-turn.mdx`
- modified: `docs/protocol/v1/draft/schema.mdx`
- modified: `docs/protocol/v1/draft/session-config-options.mdx`
- modified: `docs/protocol/v1/draft/session-setup.mdx`
- modified: `docs/protocol/v1/draft/slash-commands.mdx`
- added: `docs/protocol/v1/draft/subagents.mdx`
- modified: `docs/protocol/v1/draft/tool-calls.mdx`
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
- modified: `schema/v1/CHANGELOG.md`
- modified: `schema/v1/Cargo.toml`
- modified: `schema/v1/meta.unstable.json`
- modified: `schema/v1/schema.unstable.json`

## 2. Doc hunks -> sections

Base-side sections for removed or modified text, target-side for pure additions.

### `docs/protocol/v1/draft/agent-plan.mdx` (modified)

- `-100,1 +100,2` (base): `Plan operations > Markdown plans`
- `-107,1 +108,3` (base): `Plan operations > File plans`
- `-109,17 +112,6` (base): `Plan operations > File plans`
- `-127,1 +119,1` (base): `Plan operations > File plans`

### `docs/protocol/v1/draft/error.mdx` (modified)

- `-56,0 +57,2` (target): `Common cases > Unknown sessions`

### `docs/protocol/v1/draft/initialization.mdx` (modified)

- `-243,0 +244,76` (target): `Capabilities > Client capabilities > Prompt suggestions (unstable)` | `Capabilities > Client capabilities > Session cursors (unstable)` | `Capabilities > Client capabilities > Subagents (unstable)`
- `-347,0 +424,7` (target): `Capabilities > Agent capabilities > Session capabilities`

### `docs/protocol/v1/draft/overview.mdx` (modified)

- `-224,0 +225,3` (target): `Client > Notifications`

### `docs/protocol/v1/draft/prompt-turn.mdx` (modified)

- `-19,1 +19,1` (base): `Session updates`
- `-34,0 +35,2` (target): `Session updates`
- `-103,2 +105,2` (base): `Session updates > Session-directed messages (unstable)`
- `-106,1 +108,1` (base): `Session updates > Session-directed messages (unstable)`
- `-111,1 +113,6` (base): `Session updates > Session-directed messages (unstable)`
- `-352,0 +360,67` (target): `The prompt turn lifecycle > 3. Agent reports output > Prompt suggestions (unstable)`
- `-502,0 +577,134` (target): `The prompt turn lifecycle > 3. Agent reports output > Session cursors (unstable)`
- `-527,0 +736,2` (target): `The prompt turn lifecycle > 3. Agent reports output > Session usage updates`

### `docs/protocol/v1/draft/schema.mdx` (modified)

- `-87,2 +87,2` (base): `Agent > auth/status > AuthStatusResponse`
- `-756,0 +757,36` (target): `Agent > session/fork > ForkSessionRequest`
- `-923,0 +960,18` (target): `Agent > session/load > LoadSessionRequest`
- `-1012,0 +1067,20` (target): `Agent > session/new > NewSessionRequest`
- `-1062,0 +1137,100` (target): `Agent > session/new > NewSessionResponse` | `Agent > session/options` | `Agent > session/options > SessionOptionsRequest` | `Agent > session/options > SessionOptionsResponse`
- `-1187,0 +1362,18` (target): `Agent > session/resume > ResumeSessionRequest`
- `-1649,2 +1841,2` (base): `Client > auth/status_update > AuthStatusUpdateNotification`
- `-2999,0 +3192,7` (target): `AuthAccount`
- `-3518,0 +3718,11` (target): `ClientSessionCapabilities`
- `-3525,0 +3736,12` (target): `ClientSessionCapabilities`
- `-3945,1 +4167,1` (base): `Diff`
- `-3947,1 +4169,1` (base): `Diff`
- `-3949,1 +4171,1` (base): `Diff`
- `-3951,1 +4173,1` (base): `Diff`
- `-3953,1 +4175,3` (base): `Diff`
- `-3955,1 +4179,8` (base): `Diff`
- `-3959,2 +4190,2` (base): `Diff`
- `-3965,2 +4196,2` (base): `Diff`
- `-3968,2 +4199,2` (base): `Diff`
- `-3971,2 +4202,2` (base): `Diff`
- `-3975,1 +4206,2` (base): `ElicitationAcceptAction`
- `-3977,1 +4209,2` (base): `ElicitationAcceptAction`
- `-3979,1 +4212,1` (base): `ElicitationAcceptAction`
- `-3981,1 +4214,4` (base): `ElicitationAcceptAction`
- `-3983,3 +4219,1` (base): `ElicitationAcceptAction`
- `-3987,1 +4221,10` (base): `ElicitationCapabilities`
- `-3989,1 +4232,2` (base): `ElicitationCapabilities`
- `-3991,1 +4235,2` (base): `ElicitationCapabilities`
- `-3993,1 +4238,1` (base): `ElicitationCapabilities`
- `-3997,4 +4242,2` (base): `ElicitationCapabilities`
- `-4005,6 +4248,8` (base): `ElicitationCapabilities`
- `-4012,5 +4256,0` (base): `ElicitationCapabilities`
- `-4017,0 +4258,1` (target): `CursorAnchor`
- `-4020,1 +4261,2` (base): `ElicitationContentValue`
- `-4022,1 +4264,1` (base): `ElicitationContentValue`
- `-4024,1 +4266,4` (base): `ElicitationContentValue`
- `-4026,3 +4271,1` (base): `ElicitationContentValue`
- `-4030,2 +4272,0` (base): `ElicitationContentValue`
- `-4033,3 +4274,2` (base): `ElicitationContentValue`
- `-4037,3 +4277,2` (base): `ElicitationContentValue`
- `-4041,3 +4280,2` (base): `ElicitationContentValue`
- `-4046,5 +4284,2` (base): `ElicitationFormCapabilities`
- `-4052,1 +4287,2` (base): `ElicitationFormCapabilities`
- `-4054,1 +4290,1` (base): `ElicitationFormCapabilities`
- `-4058,4 +4294,2` (base): `ElicitationFormCapabilities`
- `-4065,0 +4300,9` (target): `CursorAnchor`
- `-4067,1 +4310,2` (base): `ElicitationFormMode`
- `-4069,1 +4313,2` (base): `ElicitationFormMode`
- `-4071,1 +4316,1` (base): `ElicitationFormMode`
- `-4073,1 +4318,4` (base): `ElicitationFormMode`
- `-4075,6 +4323,402` (base): `ElicitationFormMode`
- `-4953,1 +5597,1` (base): `IdleStateUpdate`
- `-5132,0 +5777,68` (target): `InitialSessionConfigOption`
- `-6018,1 +6730,1` (base): `PlanFile`
- `-6024,1 +6736,11` (base): `PlanFile`
- `-6036,0 +6759,7` (target): `PlanItems`
- `-6041,2 +6770,23` (base): `PlanFile`
- `-6043,0 +6794,2` (target): `PlanMarkdown`
- `-6045,1 +6797,10` (base): `PlanId`
- `-6051,1 +6812,1` (base): `PlanId`
- `-6053,1 +6814,1` (base): `PlanId`
- `-6055,1 +6816,15` (base): `PlanItems`
- `-6061,1 +6836,1` (base): `PlanItems`
- `-6065,1 +6840,58` (base): `PlanItems`
- `-6075,2 +6907,5` (base): `PlanItems`
- `-6078,2 +6913,3` (base): `PlanItems`
- `-6084,0 +6921,3` (target): `PlanUpdateContent`
- `-6086,1 +6925,2` (base): `PlanMarkdown`
- `-6088,1 +6928,1` (base): `PlanMarkdown`
- `-6090,1 +6930,1` (base): `PlanMarkdown`
- `-6092,1 +6932,10` (base): `PlanMarkdown`
- `-6106,2 +6955,5` (base): `PlanMarkdown`
- `-6109,2 +6961,14` (base): `PlanMarkdown`
- `-6113,1 +6977,1` (base): `PlanRemoved`
- `-6119,1 +6983,1` (base): `PlanRemoved`
- `-6133,2 +6997,13` (base): `PlanRemoved`
- `-6137,1 +7012,1` (base): `PlanUpdate`
- `-6143,1 +7018,3` (base): `PlanUpdate`
- `-6157,3 +7033,0` (base): `PlanUpdate`
- `-6161,1 +7035,1` (base): `PlanUpdateContent`
- `-6167,1 +7041,1` (base): `PlanUpdateContent`
- `-6169,1 +7043,4` (base): `PlanUpdateContent`
- `-6171,2 +7048,1` (base): `PlanUpdateContent`
- `-6174,1 +7050,1` (base): `PlanUpdateContent`
- `-6184,2 +7060,2` (base): `PlanUpdateContent`
- `-6187,2 +7063,2` (base): `PlanUpdateContent`
- `-6191,5 +7067,7` (base): `PlanUpdateContent`
- `-6196,0 +7075,5` (target): `PromptSuggestionsCapabilities`
- `-6198,1 +7080,0` (base): `PlanUpdateContent`
- `-6201,2 +7083,1` (base): `PlanUpdateContent`
- `-6204,1 +7085,12` (base): `PlanUpdateContent`
- `-6214,9 +7105,0` (base): `PlanUpdateContent`
- `-6224,2 +7107,1` (base): `PlanUpdateContent`
- `-6227,2 +7109,1` (base): `PlanUpdateContent`
- `-6230,1 +7111,9` (base): `PlanUpdateContent`
- `-6240,9 +7128,0` (base): `PlanUpdateContent`
- `-6250,2 +7130,1` (base): `PlanUpdateContent`
- `-6253,1 +7132,1` (base): `PromptCapabilities`
- `-6255,1 +7134,1` (base): `PromptCapabilities`
- `-6257,2 +7136,1` (base): `PromptCapabilities`
- `-6260,2 +7138,4` (base): `PromptCapabilities`
- `-6263,2 +7143,2` (base): `PromptCapabilities`
- `-6266,1 +7146,2` (base): `PromptCapabilities`
- `-6280,17 +7161,2` (base): `PromptCapabilities`
- `-6298,1 +7164,3` (base): `PromptCapabilities`
- `-6765,0 +7634,12` (target): `SessionCapabilities`
- `-6947,0 +7828,9` (target): `SessionConfigOptionCategory`
- `-7076,0 +7966,12` (target): `SessionCursorsCapabilities`
- `-7361,0 +8263,24` (target): `SessionOptionsCapabilities`
- `-8102,0 +9028,75` (target): `SessionUpdate`
- `-8319,1 +9319,1` (base): `StateUpdate`
- `-9359,1 +10359,4` (base): `UnknownStateUpdate`

### `docs/protocol/v1/draft/session-config-options.mdx` (modified)

- `-222,6 +222,7` (base): `Option categories`
- `-232,0 +234,12` (target): `Option categories > Speed options (unstable)`
- `-459,0 +473,97` (target): `Options before a session exists (unstable)` | `Options before a session exists (unstable) > Querying options` | `Options before a session exists (unstable) > Initial values`

### `docs/protocol/v1/draft/session-setup.mdx` (modified)

- `-149,0 +150,9` (target): `Loading sessions > Loading a session`
- `-444,0 +454,4` (target): `Initial config option values (unstable)`

### `docs/protocol/v1/draft/slash-commands.mdx` (modified)

- `-45,1 +45,1` (base): `Advertising commands`

### `docs/protocol/v1/draft/subagents.mdx` (added)

- `-0,0 +1,550` (target): `(intro)` | `Checking support` | `Announcing a child session` | `Announcing a child session > Parents and nesting` | `Announcing a child session > What the Agent exposes` | `Child session updates` | `Child session updates > Working directories` | `Child session updates > Configuration` | `Messages between sessions` | `Messages between sessions > Messages from a parent to a child` | `Messages between sessions > Session references in tool calls` | `Messages between sessions > Session IDs in an update` | `Work state` | `Work state > Unknown state` | `Restricted methods` | `Cancellation` | `Cancellation > Pending requests` | `Closing the parent` | `Forking the parent (unstable)` | `Connection loss` | `Loading and resuming` | `Loading and resuming > What the Client keeps` | `Loading and resuming > What the Agent sends` | `Loading and resuming > Replayed child history` | `Usage and cost`

### `docs/protocol/v1/draft/tool-calls.mdx` (modified)

- `-340,1 +340,1` (base): `Content > Sessions (unstable)`
- `-358,1 +358,1` (base): `Content > Sessions (unstable)`
- `-361,0 +362,5` (target): `Content > Sessions (unstable)`


## 3. Core hits

- `docs/protocol/v1/draft/overview.mdx` (whole doc): `-224,0 +225,3`; code: `src/tck/v1/conformance/test_jsonrpc.py`, `src/tck/v1/conformance/test_prompt.py`, `src/tck/v1/validation.py`
- `docs/protocol/v1/draft/initialization.mdx` (whole doc): `-243,0 +244,76`, `-347,0 +424,7`; code: `src/tck/common/plugin.py`, `src/tck/v1/conformance/test_initialize.py`, `src/tck/v1/conformance/test_prompt_capabilities.py`, `src/tck/v1/conformance/_helpers.py`
- `docs/protocol/v1/draft/prompt-turn.mdx` (section `Session updates`): `-19,1 +19,1`, `-34,0 +35,2`, `-103,2 +105,2`, `-106,1 +108,1`, `-111,1 +113,6`; code: `src/tck/v1/conformance/test_prompt.py`, `src/tck/v1/conformance/test_cancel.py`, `src/tck/v1/conformance/_helpers.py`
- `docs/protocol/v1/draft/error.mdx` (whole doc): `-56,0 +57,2`; code: `src/tck/v1/protocol.py`, `src/tck/v1/conformance/test_jsonrpc.py`, `src/tck/v1/conformance/test_diagnostics.py`, `src/tck/v1/conformance/test_informational.py`, `src/tck/v1/conformance/test_errors.py`, `src/tck/v1/conformance/test_session_capabilities.py`, `src/tck/v1/conformance/_helpers.py`

## 4. Schema

`$defs` compared between base and target `schema/v1/schema.unstable.json` (`(root)` = everything outside `$defs`).

- Added: `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor`, `CursorForkCapabilities`, `CursorId`, `CursorMessageAnchor`, `CursorToolCallAnchor`, `CursorUpdate`, `InitialSessionConfigOption`, `PromptSuggestion`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `PromptSuggestionsUpdate`, `SessionCursorsCapabilities`, `SessionOptionsCapabilities`, `SessionOptionsRequest`, `SessionOptionsResponse`
- Removed: `PlanFile`
- Changed: `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `ClientRequest`, `ClientSessionCapabilities`, `ForkSessionRequest`, `IdleStateUpdate`, `LoadSessionRequest`, `NewSessionRequest`, `PlanMarkdown`, `PlanUpdateContent`, `ResumeSessionRequest`, `SessionCapabilities`, `SessionConfigOptionCategory`, `SessionUpdate`, `UnknownStateUpdate`
- `$ref` closure (21 defs that transitively reference a changed def):
  - `(root)` -> `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `ClientRequest`, `ClientSessionCapabilities`, `CursorAnchor`, `CursorAnchorPosition` and 30 more
  - `AgentCapabilities` -> `SessionCapabilities`, `SessionOptionsCapabilities`
  - `AgentNotification` -> `AuthAccount`, `AuthStatusUpdateNotification`, `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor`, `CursorForkCapabilities`, `CursorId` and 12 more
  - `ClientCapabilities` -> `ClientSessionCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `SessionCursorsCapabilities`
  - `ConfigOptionUpdate` -> `SessionConfigOptionCategory`
  - `ForkSessionResponse` -> `SessionConfigOptionCategory`
  - `InitializeProxyRequest` -> `ClientSessionCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `SessionCursorsCapabilities`
  - `InitializeProxyResponse` -> `SessionCapabilities`, `SessionOptionsCapabilities`
  - `InitializeRequest` -> `ClientSessionCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `SessionCursorsCapabilities`
  - `InitializeResponse` -> `SessionCapabilities`, `SessionOptionsCapabilities`
  - `LoadSessionResponse` -> `SessionConfigOptionCategory`
  - `NewSessionResponse` -> `SessionConfigOptionCategory`
  - `PlanUpdate` -> `PlanFile`, `PlanMarkdown`, `PlanUpdateContent`
  - `ProxyRequest` -> `ClientSessionCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `SessionCursorsCapabilities`
  - `ProxyResponse` -> `SessionCapabilities`, `SessionOptionsCapabilities`
  - `ResumeSessionResponse` -> `SessionConfigOptionCategory`
  - `SessionConfigOption` -> `SessionConfigOptionCategory`
  - `SessionNotification` -> `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor`, `CursorForkCapabilities`, `CursorId`, `CursorMessageAnchor`, `CursorToolCallAnchor` and 10 more
  - `SetSessionConfigOptionResponse` -> `SessionConfigOptionCategory`
  - `StateUpdate` -> `IdleStateUpdate`, `UnknownStateUpdate`
  - `SubagentUpdate` -> `IdleStateUpdate`, `UnknownStateUpdate`
- Core `$defs` hit: `SessionUpdate` (changed directly); `AgentCapabilities` (via $ref closure of `SessionCapabilities`, `SessionOptionsCapabilities`); `ClientCapabilities` (via $ref closure of `ClientSessionCapabilities`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `SessionCursorsCapabilities`)

## 5. Link fan-out

Docs under `docs/protocol/v1/draft/` at target that link to a changed doc.

### `docs/protocol/v1/draft/agent-plan.mdx`

- `docs/protocol/v1/draft/initialization.mdx:184` `#plan-operations` (changed section)
- `docs/protocol/v1/draft/overview.mdx:220`
- `docs/protocol/v1/draft/prompt-turn.mdx:24`
- `docs/protocol/v1/draft/prompt-turn.mdx:25` `#plan-operations` (changed section)
- `docs/protocol/v1/draft/prompt-turn.mdx:26` `#removing-plans` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:251`
- `docs/protocol/v1/draft/schema.mdx:6613`
- `docs/protocol/v1/draft/schema.mdx:6662` `#plan-entries` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:6693` `#plan-entries` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:6714` `#plan-entries` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:8700`

### `docs/protocol/v1/draft/error.mdx`

- `docs/protocol/v1/draft/overview.mdx:244`
- `docs/protocol/v1/draft/session-setup.mdx:359` `#unknown-sessions` (changed section)

### `docs/protocol/v1/draft/initialization.mdx`

- `docs/protocol/v1/draft/agent-plan.mdx:10` `#client-capabilities` (changed section)
- `docs/protocol/v1/draft/authentication.mdx:7`
- `docs/protocol/v1/draft/content.mdx:55` `#prompt-capabilities` (unchanged section)
- `docs/protocol/v1/draft/content.mdx:88` `#prompt-capabilities` (unchanged section)
- `docs/protocol/v1/draft/content.mdx:124` `#prompt-capabilities` (unchanged section)
- `docs/protocol/v1/draft/elicitation.mdx:27` `#client-capabilities` (changed section)
- `docs/protocol/v1/draft/file-system.mdx:10` `#client-capabilities` (changed section)
- `docs/protocol/v1/draft/overview.mdx:56`
- `docs/protocol/v1/draft/overview.mdx:263`
- `docs/protocol/v1/draft/prompt-turn.mdx:8`
- `docs/protocol/v1/draft/prompt-turn.mdx:200` `#prompt-capabilities` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:200`
- `docs/protocol/v1/draft/prompt-turn.mdx:405` `#prompt-capabilities` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:405` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v1/draft/schema.mdx:103`
- `docs/protocol/v1/draft/schema.mdx:157`
- `docs/protocol/v1/draft/schema.mdx:165`
- `docs/protocol/v1/draft/schema.mdx:201`
- `docs/protocol/v1/draft/schema.mdx:3052` `#agent-capabilities` (changed section)
- `docs/protocol/v1/draft/schema.mdx:3617` `#client-capabilities` (changed section)
- `docs/protocol/v1/draft/schema.mdx:5527` `#filesystem` (unknown anchor)
- `docs/protocol/v1/draft/schema.mdx:6941` `#prompt-capabilities` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:7565` `#session-capabilities` (changed section)
- `docs/protocol/v1/draft/session-delete.mdx:8`
- `docs/protocol/v1/draft/session-list.mdx:10`
- `docs/protocol/v1/draft/session-setup.mdx:8`
- `docs/protocol/v1/draft/terminals.mdx:10` `#client-capabilities` (changed section)

### `docs/protocol/v1/draft/overview.mdx`

- `docs/protocol/v1/draft/initialization.mdx:6` `#client` (changed section)
- `docs/protocol/v1/draft/initialization.mdx:6` `#agent` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:6` `#client` (changed section)
- `docs/protocol/v1/draft/prompt-turn.mdx:6` `#agent` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:2185` `#client` (changed section)
- `docs/protocol/v1/draft/schema.mdx:2252` `#client` (changed section)
- `docs/protocol/v1/draft/session-setup.mdx:6` `#client` (changed section)
- `docs/protocol/v1/draft/session-setup.mdx:6` `#agent` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:8` `#agent` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:8` `#client` (changed section)

### `docs/protocol/v1/draft/prompt-turn.mdx`

- `docs/protocol/v1/draft/agent-plan.mdx:8` `#3-agent-reports-output` (changed section)
- `docs/protocol/v1/draft/cancellation.mdx:26` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/cancellation.mdx:42` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/content.mdx:10` `#1-user-message` (unchanged section)
- `docs/protocol/v1/draft/content.mdx:11` `#3-agent-reports-output` (changed section)
- `docs/protocol/v1/draft/initialization.mdx:221` `#session-compaction` (unchanged section)
- `docs/protocol/v1/draft/initialization.mdx:239` `#session-notices` (unchanged section)
- `docs/protocol/v1/draft/initialization.mdx:284` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v1/draft/initialization.mdx:301` `#session-cursors-unstable` (changed section)
- `docs/protocol/v1/draft/overview.mdx:78` `#1-user-message` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:115` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:215` `#3-agent-reports-output` (changed section)
- `docs/protocol/v1/draft/overview.mdx:223` `#session-notices` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:224` `#session-compaction` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:225` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v1/draft/overview.mdx:226` `#session-cursors-unstable` (changed section)
- `docs/protocol/v1/draft/overview.mdx:265`
- `docs/protocol/v1/draft/schema.mdx:583` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:589` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:1251`
- `docs/protocol/v1/draft/schema.mdx:1259` `#1-user-message` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:1297` `#4-check-for-completion` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:2466` `#3-agent-reports-output` (changed section)
- `docs/protocol/v1/draft/schema.mdx:2474` `#3-agent-reports-output` (changed section)
- `docs/protocol/v1/draft/schema.mdx:7318` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:8500` `#3-agent-reports-output` (changed section)
- `docs/protocol/v1/draft/schema.mdx:9495` `#stop-reasons` (unchanged section)
- `docs/protocol/v1/draft/session-setup.mdx:139` `#session-compaction` (unchanged section)
- `docs/protocol/v1/draft/session-setup.mdx:144` `#session-notices` (unchanged section)
- `docs/protocol/v1/draft/session-setup.mdx:150` `#prompt-suggestions-unstable` (changed section)
- `docs/protocol/v1/draft/session-setup.mdx:152` `#session-cursors-unstable` (changed section)
- `docs/protocol/v1/draft/session-setup.mdx:343` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/slash-commands.mdx:6`
- `docs/protocol/v1/draft/subagents.mdx:59` `#session-directed-messages-unstable` (changed section)
- `docs/protocol/v1/draft/subagents.mdx:278` `#session-directed-messages-unstable` (changed section)
- `docs/protocol/v1/draft/subagents.mdx:365` `#stop-reasons` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:435` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:458` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:466` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:536` `#session-notices` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:542` `#session-usage-updates` (changed section)
- `docs/protocol/v1/draft/tool-calls.mdx:6`
- `docs/protocol/v1/draft/tool-calls.mdx:8` `#3-agent-reports-output` (changed section)
- `docs/protocol/v1/draft/tool-calls.mdx:196` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/tool-calls.mdx:212` `#cancellation` (unchanged section)
- `docs/protocol/v1/draft/tool-calls.mdx:359` `#session-directed-messages-unstable` (changed section)

### `docs/protocol/v1/draft/schema.mdx`

- `docs/protocol/v1/draft/authentication.mdx:130` `#authmethod` (unchanged section)
- `docs/protocol/v1/draft/cancellation.mdx:22` `#errorcode` (unchanged section)
- `docs/protocol/v1/draft/elicitation.mdx:193` `#elicitation%2Fcreate` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:53` `#initialize` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:61` `#authenticate` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:68` `#session%2Fnew` (changed section)
- `docs/protocol/v1/draft/overview.mdx:76` `#session%2Fprompt` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:86` `#session%2Fload` (changed section)
- `docs/protocol/v1/draft/overview.mdx:94` `#logout` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:103` `#session%2Fset_mode` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:113` `#session%2Fcancel` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:128` `#session%2Frequest_permission` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:140` `#fs%2Fread_text_file` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:148` `#fs%2Fwrite_text_file` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:156` `#terminal%2Fcreate` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:164` `#terminal%2Foutput` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:171` `#terminal%2Frelease` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:179` `#terminal%2Fwait_for_exit` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:187` `#terminal%2Fkill` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:194` `#elicitation%2Fcreate` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:204` `#elicitation%2Fcomplete` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:213` `#session%2Fupdate` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:38` `#sessionupdate` (changed section)
- `docs/protocol/v1/draft/session-modes.mdx:83` `#session%2Fset_mode` (unchanged section)

### `docs/protocol/v1/draft/session-config-options.mdx`

- `docs/protocol/v1/draft/initialization.mdx:203`
- `docs/protocol/v1/draft/prompt-turn.mdx:29` `#from-the-agent` (unchanged section)
- `docs/protocol/v1/draft/session-modes.mdx:8`
- `docs/protocol/v1/draft/session-setup.mdx:456` `#options-before-a-session-exists-unstable` (changed section)
- `docs/protocol/v1/draft/subagents.mdx:269` `#from-the-agent` (unchanged section)

### `docs/protocol/v1/draft/session-setup.mdx`

- `docs/protocol/v1/draft/error.mdx:49` `#system-prompt` (unchanged section)
- `docs/protocol/v1/draft/error.mdx:55` `#closing-active-sessions` (unchanged section)
- `docs/protocol/v1/draft/file-system.mdx:50` `#session-id` (unchanged section)
- `docs/protocol/v1/draft/file-system.mdx:96` `#session-id` (unchanged section)
- `docs/protocol/v1/draft/file-system.mdx:125` `#workspace-root-security` (unchanged section)
- `docs/protocol/v1/draft/initialization.mdx:325` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/initialization.mdx:418` `#system-prompt` (unchanged section)
- `docs/protocol/v1/draft/initialization.mdx:476`
- `docs/protocol/v1/draft/overview.mdx:71` `#creating-a-session` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:88` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/overview.mdx:264`
- `docs/protocol/v1/draft/prompt-turn.mdx:8`
- `docs/protocol/v1/draft/prompt-turn.mdx:40` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/prompt-turn.mdx:195` `#session-id` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:565` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/prompt-turn.mdx:674` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/schema.mdx:930` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/schema.mdx:938` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/schema.mdx:1040`
- `docs/protocol/v1/draft/schema.mdx:1046` `#creating-a-session` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:1107` `#creating-a-session` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:6034` `#mcp-servers` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:8027` `#session-id` (unchanged section)
- `docs/protocol/v1/draft/security.mdx:37` `#workspace-root-security` (unchanged section)
- `docs/protocol/v1/draft/security.mdx:51` `#system-prompt` (unchanged section)
- `docs/protocol/v1/draft/security.mdx:65` `#workspace-root-security` (unchanged section)
- `docs/protocol/v1/draft/security.mdx:67` `#security` (unchanged section)
- `docs/protocol/v1/draft/session-config-options.mdx:17`
- `docs/protocol/v1/draft/session-list.mdx:225` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/session-list.mdx:256` `#closing-active-sessions` (unchanged section)
- `docs/protocol/v1/draft/session-modes.mdx:17`
- `docs/protocol/v1/draft/subagents.mdx:232` `#working-directory` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:262` `#workspace-root-security` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:475` `#closing-active-sessions` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:500` `#loading-sessions` (changed section)
- `docs/protocol/v1/draft/subagents.mdx:500` `#resuming-sessions` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:528` `#loading-a-session` (changed section)
- `docs/protocol/v1/draft/terminals.mdx:54` `#session-id` (unchanged section)
- `docs/protocol/v1/draft/terminals.mdx:288` `#workspace-root-security` (unchanged section)
- `docs/protocol/v1/draft/tool-calls.mdx:388` `#workspace-root-security` (unchanged section)

### `docs/protocol/v1/draft/slash-commands.mdx`

- `docs/protocol/v1/draft/overview.mdx:221` `#advertising-commands` (changed section)
- `docs/protocol/v1/draft/prompt-turn.mdx:27`
- `docs/protocol/v1/draft/security.mdx:27`
- `docs/protocol/v1/draft/session-list.mdx:179`
- `docs/protocol/v1/draft/subagents.mdx:226`

### `docs/protocol/v1/draft/subagents.mdx`

- `docs/protocol/v1/draft/error.mdx:57`
- `docs/protocol/v1/draft/error.mdx:57` `#restricted-methods` (changed section)
- `docs/protocol/v1/draft/initialization.mdx:316`
- `docs/protocol/v1/draft/overview.mdx:227`
- `docs/protocol/v1/draft/prompt-turn.mdx:19`
- `docs/protocol/v1/draft/prompt-turn.mdx:105`
- `docs/protocol/v1/draft/prompt-turn.mdx:113` `#messages-from-a-parent-to-a-child` (changed section)
- `docs/protocol/v1/draft/prompt-turn.mdx:736` `#usage-and-cost` (changed section)
- `docs/protocol/v1/draft/schema.mdx:5597` `#work-state` (changed section)
- `docs/protocol/v1/draft/schema.mdx:9319` `#work-state` (changed section)
- `docs/protocol/v1/draft/tool-calls.mdx:340`

### `docs/protocol/v1/draft/tool-calls.mdx`

- `docs/protocol/v1/draft/content.mdx:12`
- `docs/protocol/v1/draft/overview.mdx:132` `#requesting-permission` (unchanged section)
- `docs/protocol/v1/draft/overview.mdx:219`
- `docs/protocol/v1/draft/prompt-turn.mdx:22` `#creating` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:23` `#updating` (unchanged section)
- `docs/protocol/v1/draft/prompt-turn.mdx:805`
- `docs/protocol/v1/draft/schema.mdx:2401` `#requesting-permission` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:2409` `#requesting-permission` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:4595` `#content` (changed section)
- `docs/protocol/v1/draft/schema.mdx:10012`
- `docs/protocol/v1/draft/schema.mdx:10067` `#content` (changed section)
- `docs/protocol/v1/draft/schema.mdx:10190` `#following-the-agent` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:10220` `#status` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:10248` `#updating` (unchanged section)
- `docs/protocol/v1/draft/schema.mdx:10301` `#creating` (unchanged section)
- `docs/protocol/v1/draft/security.mdx:68` `#security` (unchanged section)
- `docs/protocol/v1/draft/session-modes.mdx:178` `#requesting-permission` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:61` `#sessions-unstable` (changed section)
- `docs/protocol/v1/draft/subagents.mdx:94` `#sessions-unstable` (changed section)
- `docs/protocol/v1/draft/subagents.mdx:182` `#requesting-permission` (unchanged section)
- `docs/protocol/v1/draft/subagents.mdx:318` `#sessions-unstable` (changed section)
- `docs/protocol/v1/draft/terminals.mdx:115`

### `docs/rfds/get-auth-state.mdx`

- `docs/protocol/v1/draft/initialization.mdx:377`

### `docs/rfds/session-archive.mdx`

- `docs/protocol/v1/draft/session-list.mdx:229`

### `docs/rfds/session-cursors.mdx`

- `docs/protocol/v1/draft/schema.mdx:4179`
- `docs/protocol/v1/draft/schema.mdx:4403`
- `docs/protocol/v1/draft/schema.mdx:4486`
- `docs/protocol/v1/draft/schema.mdx:4561`
- `docs/protocol/v1/draft/schema.mdx:7974`

### `docs/rfds/session-fork.mdx`

- `docs/protocol/v1/draft/subagents.mdx:484`

### `docs/rfds/session-notices.mdx`

- `docs/protocol/v1/draft/schema.mdx:6440`

### `docs/rfds/session-options.mdx`

- `docs/protocol/v1/draft/initialization.mdx:425`
- `docs/protocol/v1/draft/session-config-options.mdx:475`

### `docs/rfds/session-set-title.mdx`

- `docs/protocol/v1/draft/initialization.mdx:438`

### `docs/rfds/session-status.mdx`

- `docs/protocol/v1/draft/initialization.mdx:432`
- `docs/protocol/v1/draft/session-list.mdx:259`

### `docs/rfds/speed-config-category.mdx`

- `docs/protocol/v1/draft/session-config-options.mdx:236`


## 6. Affected entries

- ACP-JSONRPC-006: `#/anyOf/2/properties/params/anyOf/0`: `(root)` in $ref closure of `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `ClientRequest`, `ClientSessionCapabilities`, `CursorAnchor`, `CursorAnchorPosition` and 30 more
- ACP-INIT-001: `#/$defs/InitializeResponse`: `InitializeResponse` in $ref closure of `SessionCapabilities`, `SessionOptionsCapabilities`
- ACP-SCHEMA-001: `#/anyOf/0`: `(root)` in $ref closure of `AgentResponse`, `AuthAccount`, `AuthStatusResponse`, `AuthStatusUpdateNotification`, `ClientRequest`, `ClientSessionCapabilities`, `CursorAnchor`, `CursorAnchorPosition` and 30 more
- ACP-SESSION-001: `#/$defs/NewSessionResponse`: `NewSessionResponse` in $ref closure of `SessionConfigOptionCategory`
- ACP-SESSION-002: `#/$defs/NewSessionResponse`: `NewSessionResponse` in $ref closure of `SessionConfigOptionCategory`
- ACP-PROMPT-002: `#/$defs/SessionNotification`: `SessionNotification` in $ref closure of `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor`, `CursorForkCapabilities`, `CursorId`, `CursorMessageAnchor`, `CursorToolCallAnchor` and 10 more
- ACP-LOAD-001: `docs/protocol/v1/draft/session-setup.mdx:110-201` overlaps hunk `-149,0 +150,9`; `#/$defs/AgentCapabilities/properties/loadSession`: `AgentCapabilities` in $ref closure of `SessionCapabilities`, `SessionOptionsCapabilities`; `#/$defs/LoadSessionResponse`: `LoadSessionResponse` in $ref closure of `SessionConfigOptionCategory`; `#/$defs/LoadSessionRequest`: `LoadSessionRequest` changed
- ACP-LOAD-003: `#/$defs/LoadSessionResponse`: `LoadSessionResponse` in $ref closure of `SessionConfigOptionCategory`
- ACP-RESUME-001: `#/$defs/ResumeSessionRequest`: `ResumeSessionRequest` changed; `#/$defs/ResumeSessionResponse`: `ResumeSessionResponse` in $ref closure of `SessionConfigOptionCategory`
- ACP-ARCHIVE-001: `#/$defs/SessionCapabilities/properties/archive`: `SessionCapabilities` changed
- ACP-ARCHIVE-003: cites changed RFD `docs/rfds/session-archive.mdx` (cited lines untouched)
- ACP-ARCHIVE-006: cites changed RFD `docs/rfds/session-archive.mdx` (cited lines untouched)
- ACP-ADDDIRS-001: `#/$defs/NewSessionRequest/properties/additionalDirectories`: `NewSessionRequest` changed
- ACP-CONFIG-001: `#/$defs/SessionConfigOption`: `SessionConfigOption` in $ref closure of `SessionConfigOptionCategory`
- ACP-CONFIG-002: `#/$defs/SetSessionConfigOptionResponse`: `SetSessionConfigOptionResponse` in $ref closure of `SessionConfigOptionCategory`
- ACP-CONFIG-003: `#/$defs/SessionConfigOption/oneOf/1`: `SessionConfigOption` in $ref closure of `SessionConfigOptionCategory`
- ACP-AUTH-005: `#/$defs/InitializeResponse/properties/authMethods`: `InitializeResponse` in $ref closure of `SessionCapabilities`, `SessionOptionsCapabilities`
- ACP-AUTH-007: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched); `#/$defs/AuthStatusResponse`: `AuthStatusResponse` changed
- ACP-AUTH-008: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ACP-CLIENTCAP-007: `docs/protocol/v1/draft/prompt-turn.mdx:19-21` overlaps hunk `-19,1 +19,1`; `docs/protocol/v1/draft/tool-calls.mdx:358` overlaps hunk `-358,1 +358,1`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-001: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/SubagentUpdate`: `SubagentUpdate` in $ref closure of `IdleStateUpdate`, `UnknownStateUpdate`
- ACP-SUBAGENT-002: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-003: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-004: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-005: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-006: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/SubagentUpdate/properties/cwd`: `SubagentUpdate` in $ref closure of `IdleStateUpdate`, `UnknownStateUpdate`; `#/$defs/SubagentUpdate/properties/additionalDirectories`: `SubagentUpdate` in $ref closure of `IdleStateUpdate`, `UnknownStateUpdate`
- ACP-SUBAGENT-007: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-008: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-009: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-011: `docs/protocol/v1/draft/prompt-turn.mdx:106-111` overlaps hunk `-106,1 +108,1`, `-111,1 +113,6`; `docs/rfds/subagents.mdx:648-664` overlaps hunk `-658,0 +678,7`
- ACP-SUBAGENT-012: `docs/protocol/v1/draft/prompt-turn.mdx:106-111` overlaps hunk `-106,1 +108,1`, `-111,1 +113,6`; cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-013: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-014: `docs/rfds/subagents.mdx:392-419` overlaps hunk `-400,1 +400,1`
- ACP-SUBAGENT-015: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched); `#/$defs/SubagentUpdate`: `SubagentUpdate` in $ref closure of `IdleStateUpdate`, `UnknownStateUpdate`; `#/$defs/StateUpdate`: `StateUpdate` in $ref closure of `IdleStateUpdate`, `UnknownStateUpdate`
- ACP-SUBAGENT-016: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-SUBAGENT-017: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ACP-PLAN-001: `docs/protocol/v1/draft/agent-plan.mdx:127` overlaps hunk `-127,1 +119,1`; `docs/rfds/plan-operations.mdx:63` overlaps hunk `-63,1 +62,7`; `#/$defs/PlanFile`: `PlanFile` removed
- ACP-ERROR-002: `#/$defs/NewSessionRequest`: `NewSessionRequest` changed
- ledger `Calling `auth/status` MUST NOT modify any agent state.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `An agent that supports `auth/status` SHOULD advertise `auth.status` in `agentCapabilities`.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `Agents SHOULD list the accounts and credentials they have configured in `auth/status` `accounts`, and SHOULD mark the ones in effect with `active: true`.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger ``auth/status` `accounts` MUST NOT include secrets.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `Agents SHOULD keep `auth/status` fast, answering `unknown` and sending `auth/status_update` later rather than blocking, and SHOULD return `unknown` rather than guess.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `Agents SHOULD send `auth/status_update` when their status changes (including after `authenticate` or `logout`), and only when it differs from the last one sent on the connection.`: cites changed RFD `docs/rfds/get-auth-state.mdx` (cited lines untouched)
- ledger `Agents treat a `null` in a client-authored list field marked `x-deserialize-default-on-null` as the default.`: `#/$defs/NewSessionRequest/properties/mcpServers`: `NewSessionRequest` changed
- ledger `An Agent reports a child directory that differs from the parent's before it sends child traffic that depends on it (MUST), and does not expose a child whose directories it cannot determine as sharing the parent's workspace (SHOULD NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `Agents report the narrowest directories a child needs (SHOULD), send current directory values after reconnecting when they differ (SHOULD), and report a new value or `null` when a child's directory no longer exists (MUST).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `An Agent does not guess a child's parentage, and does not temporarily announce a nested child under the root, whether live or when a replay cannot reconstruct the association truthfully (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `An Agent that keeps an operation unexposed does not later move an already-issued interaction to a different session, and once a child is exposed its new interactions use the child's session ID rather than falling back to the root (MUST NOT / MUST).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `After announcing a child the Agent sends its events automatically, without waiting for another Client request, and with no `session/attach`, `session/subscribe` or per-child opt-in.`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `An Agent reports each side of a session-directed message only when it can observe that side, and does not manufacture an incoming entry from an outgoing one.`: `docs/rfds/subagents.mdx:576-577` overlaps hunk `-577,1 +585,4`
- ledger `When the Agent observes a child's foreground work starting, resuming or stopping it reports `running` or `idle` in the parent's `subagent_update.state` (MUST), reports `requires_action` while observed work is blocked on user action (SHOULD), and includes `stopReason` when the reason for stopping is known (SHOULD).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `When observability of a child's foreground work is actually lost the Agent reports the `unknown` state on the parent's `subagent_update.state` (MUST), and not merely because the child has been quiet.`: `docs/rfds/subagents.mdx:855-860` overlaps hunk `-859,1 +885,4`; `#/$defs/UnknownStateUpdate`: `UnknownStateUpdate` changed
- ledger `Closing a parent session cancels all of its active descendant work, background children included, and releases the associated active resources, without requiring a new terminal-state notification.`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `A late response still resolves its original request, but the Agent does not use it to restart cancelled or otherwise abandoned work, or to authorize a new assignment to the same child (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `Replay (v1 `session/load` with history) does not reissue recorded permission, elicitation or other Agent-to-Client requests (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `When replaying a recorded directed message the Agent does not invent either participant ID, and does not reinterpret its content as an ordinary message to or from the human user (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `The Agent does not manufacture a failure, cancellation or permanent orphan outcome for a child solely because the persisted history lacks a final update or a runtime could not be restored (MUST NOT).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `Agents do not fabricate an exclusive parent or child cost amount from incomplete token counts or an aggregate total (MUST NOT).`: `docs/rfds/subagents.mdx:1168-1170` overlaps hunk `-1158,31 +1205,24`
- ledger `A session-directed message's `messageId` is unique within the enclosing session's transcript and identifies that entry, not a shared message or either participant.`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger `In v1 an Agent passes an explicit `cwd` on a child's `terminal/create` request, even though the Client uses the child's effective `cwd` when it is omitted (SHOULD).`: cites changed RFD `docs/rfds/subagents.mdx` (cited lines untouched)
- ledger ``session/status` reports an archived session as `saved`, answers an unknown session with `-32002` and the requested `sessionId` in `data`, and MUST NOT have side effects.`: cites changed RFD `docs/rfds/session-status.mdx` (cited lines untouched)
- ledger `After a successful `session/set_title` the agent SHOULD NOT replace the title with one it generates automatically, and SHOULD discard a title it was generating; a session that does not exist gets `-32002` and a title the agent rejects gets `-32602`.`: cites changed RFD `docs/rfds/session-set-title.mdx` (cited lines untouched)

## 7. RFD stages

Stage = nearest stage group in `docs/docs.json` (Draft, Active, Preview, Completed), read at base and at target. Tracked = Active or Preview at target (not `rfds/v2/*`); Completed RFDs are never tracked.

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

- Changed files: 48 (11 draft docs, 4 schema files, 33 RFDs); doc hunks: 138.
- `$defs`: 20 added, 1 removed, 17 changed; closure: 21.
- Links into changed docs: 218.
- Tracked RFDs: 2 (2 changed); stage moves: 25.
- Affected entries: 38 requirements, 25 ledger entries.
- Core hit: **yes, escalate** (`docs/protocol/v1/draft/overview.mdx`; `docs/protocol/v1/draft/initialization.mdx`; `docs/protocol/v1/draft/prompt-turn.mdx` > `Session updates`; `docs/protocol/v1/draft/error.mdx`; `$defs/SessionUpdate`; `$defs/AgentCapabilities`; `$defs/ClientCapabilities`)

## 2. CHANGELOG entries and RFD status changes

### `schema/v1/CHANGELOG.md` (`git diff`, two releases: 1.31.0, 1.32.0; `Cargo.toml` 1.30.0 -> 1.32.0)

```
## [1.32.0] - 2026-11-14
### Added
- (unstable) add prompt suggestions session update and client capability (#2821)
- (unstable) replace file plan type with path on markdown plans (#2815)
- (unstable) add speed session config option category (#2809)
- (unstable) accept initial config options on session/fork and clarify notifications (#2794)
### Other
- (rust) fix clippy map_unwrap_or lint in schema generator (#2806)
- (unstable) clarify subagent message views, unknown state, and session references (#2801)

## [1.31.0] - 2026-11-10
### Added
- (unstable) add description to AuthAccount (#2793)
- (unstable) add session/options and initial config option values (#2792)
- (unstable) add session tool call content and clarify one-shot subagents (#2787)
```

Not in the v1 changelog but visible in the v1 schema diff: `cursor_update` / `CursorId` / `cursorId` on `session/fork` and `session.cursors` (commit `417a9f59`, #2843, "add session cursors and cursorId on session/fork"). The v1 changelog entry for this is still unreleased (`## [Unreleased]` is empty). `schema/v1/Cargo.toml` also gained `rust-version.workspace = true` (non-protocol).

### Other schema files

- `schema/v1/schema.json` (stable) is **unchanged**. Only `schema.unstable.json` (+931 lines net) and `meta.unstable.json` changed.
- `meta.unstable.json`: adds `"session_options": "session/options"` (agent method map). No other change.

### RFD status changes (stage group moves in `docs/docs.json`)

- Commit `199fa7d1` "docs(rfd): remove the Active lifecycle stage (#2807)": the Active group is gone. Former Active RFDs fold into Draft, except `subagents`, which went to Preview (`12d4555a`, #2800).
- Commit `d70cc617` "docs(rfd): move plan operations to preview (#2845)": `plan-operations` Draft -> Preview.
- The sidebar at target has groups Draft, Preview (`rfds/plan-operations`, `rfds/subagents`) and Completed. The old Active group no longer exists.
- Structural note: the `v2` RFD sub-group now sits under **Draft**, so every `rfds/v2/*` RFD is Draft at target (v2-only anyway).

## 3. RFD stages (base vs target) and tracked RFDs for v1

Stage = nearest enclosing stage group in `docs/docs.json`. `-` means not listed in the sidebar at that rev. `None` means not in a stage group (`about`, `updates`).

| RFD | Base | Target | Moved | RFD file changed in range |
|---|---|---|---|---|
| about | None | None | no | yes (process text) |
| acp-agent-registry | Completed | Completed | no | no |
| additional-directories | Completed | Completed | no | yes (1 line) |
| agent-skills | - | Draft | yes (new) | added |
| auth-methods | Completed | Completed | no | no |
| boolean-config-option | Completed | Completed | no | no |
| client-system-prompt | Completed | Completed | no | yes (1 line) |
| custom-llm-endpoint | Draft | Draft | no | no |
| elicitation | Completed | Completed | no | no |
| end-turn-token-usage | Draft | Draft | no | yes (1 line) |
| get-auth-state | Draft | Draft | no | yes (+27/-) |
| introduce-rfd-process | Completed | Completed | no | yes (process text) |
| logout-method | Completed | Completed | no | no |
| **mcp-over-acp** | Active | Draft | **Active -> Draft** | no |
| message-id | Completed | Completed | no | no |
| meta-propagation | Completed | Completed | no | no |
| model-config-category | Completed | Completed | no | no |
| **plan-operations** | Draft | **Preview** | **Draft -> Preview** | yes (+81/-) |
| prompt-suggestions | - | Draft | yes (new) | added |
| proxy-chains | Draft | Draft | no | no |
| request-cancellation | Completed | Completed | no | yes (3 lines) |
| rust-sdk-v1 | Completed | Completed | no | no |
| session-archive | Draft | Draft | no | yes (1 line) |
| session-close | Completed | Completed | no | yes (1 line) |
| session-compaction | Completed | Completed | no | no |
| session-config-options | Completed | Completed | no | yes (1 line) |
| session-cursors | - | Draft | yes (new) | added |
| session-delete | Completed | Completed | no | no |
| session-fork | Draft | Draft | no | yes (+70) |
| session-info-update | Completed | Completed | no | no |
| session-list | Completed | Completed | no | no |
| session-notices | Completed | Completed | no | yes (1 line) |
| session-options | - | Draft | yes (new) | added |
| session-resume | Completed | Completed | no | yes (1 line) |
| session-set-title | Draft | Draft | no | yes (1 line) |
| session-status | Draft | Draft | no | yes (1 line) |
| session-usage | Completed | Completed | no | yes (1 line) |
| speed-config-category | - | Draft | yes (new) | added |
| **streamable-http-websocket-transport** | Active | Draft | **Active -> Draft** | no |
| **subagents** | Active | **Preview** | **Active -> Preview** | yes (+212/-, see below) |
| tool-call-name | Completed | Completed | no | yes (1 line) |
| updates | None | None | no | yes (+51) |
| v2/background-work | Active | Draft | Active -> Draft | yes |
| v2/client-filesystem-terminal-capabilities | Active | Draft | Active -> Draft | no |
| v2/diff-file-states | Active | Draft | Active -> Draft | no |
| v2/enum-variant-extension | Active | Draft | Active -> Draft | no |
| v2/idempotency-keys | - | Draft | yes (new) | added |
| v2/message-updates | Active | Draft | Active -> Draft | no |
| v2/meta-patches | Active | Draft | Active -> Draft | yes |
| v2/overview | Active | Draft | Active -> Draft | yes |
| v2/permission-requests | Active | Draft | Active -> Draft | no |
| v2/plan-variants | Active | Draft | Active -> Draft | yes |
| v2/prompt | Active | Draft | Active -> Draft | no |
| v2/required-session-methods | Active | Draft | Active -> Draft | no |
| v2/session-replay-complete | - | Draft | yes (new) | added |
| v2/session-resume-replay | Active | Draft | Active -> Draft | yes |
| v2/terminal-output | Active | Draft | Active -> Draft | no |
| v2/tool-call-updates | Active | Draft | Active -> Draft | no |

Totals: 25 stage moves (10 `rfds/*` + 15 `rfds/v2/*`), matching `spec-impact` section 7. One-line file edits in Completed and other RFDs are mostly a link or label touch-up (not examined line by line, inventory only).

### Tracked RFDs for v1 (Active/Preview at target, applying to v1)

At target only two RFDs are Active or Preview, and **both apply to v1**:

| RFD | Stage base -> target | Changed in range | v1 wire shapes |
|---|---|---|---|
| `docs/rfds/plan-operations.mdx` | Draft -> **Preview** | yes, text (+81/-), and a **schema change**: the `file` plan type is removed (`PlanFile` def gone), `PlanMarkdown` gains `path` | v1 unstable schema (`PlanUpdate`, `PlanUpdateContent`, `PlanItems`, `PlanMarkdown`, `PlanRemoved`, `PlanId`, `PlanCapabilities`; `ClientCapabilities.plan`) |
| `docs/rfds/subagents.mdx` | Active -> **Preview** | yes, text (+212/-): see list below | v1 unstable schema (`SubagentUpdate`, `StateUpdate`, `IdleStateUpdate`, `UnknownStateUpdate`, `session_message`, `session_message_chunk`, `SubagentCapabilities`, tool-call `session` content). It is also now documented in the new draft doc `docs/protocol/v1/draft/subagents.mdx` |

Not tracked, with reason:

- All `rfds/v2/*`: v2-only (and now Draft).
- `mcp-over-acp`, `streamable-http-websocket-transport`: moved Active -> Draft, so no longer tracked (the old registry still carries one `(Active RFD)` citation to `mcp-over-acp`, see section 6).
- Newly Draft RFDs (`agent-skills`, `prompt-suggestions`, `session-cursors`, `session-options`, `speed-config-category`): Draft, not tracked. Their wire shapes are nevertheless **in the v1 unstable schema and the v1 draft docs** (see section 4), so the docs/schema diff covers them.
- Completed RFDs: never tracked.

`subagents.mdx` RFD changes in range (from `git diff`, headline items):

- Link retarget to the new draft doc and v2 page.
- New "A link between views needs evidence" text: two views are linked only when the same message can be established (`MUST NOT` assume the parent as sender when there is no evidence, omit `senderSessionId`).
- Outgoing-view timing: may be reported when the send starts or completes, `SHOULD NOT` report for a send known to have failed before leaving.
- Tool call `content` replace semantics for session references, and an unresolvable handle gets no reference (`MUST NOT` guess).
- `unknown` state: also entered when the Agent itself stops tracking a child that may still be working. While `unknown`, unfinished tool calls and terminals stay as last reported (the Agent `MUST NOT` invent a final status).
- The note "`unknown` added to `StateUpdate` under `unstable_subagents`" is changed to "added to ordinary `StateUpdate`".
- Restricted methods: an Agent ignores `session/cancel` for a child without `cancel`, and `SHOULD` reject other not-permitted Client requests naming a child (including `session/close`, `session/delete`) with `-32602`.
- **Cost rule reversed**: the section "Cost reporting without inferred aggregation" is deleted and replaced by "Cost covers descendant sessions". A parent's `usage_update.cost` now includes its descendants, and Clients `MUST NOT` add a child's cost to an ancestor's. The old "Agents MUST NOT fabricate an exclusive parent or child amount" sentence is removed (this is the text ledger entry at `docs/rfds/subagents.mdx:1168-1170` cites).
- v2-vs-v1 boundary notes (replay boundary, cancel of abandoned requests).

`plan-operations.mdx` RFD changes in range: the `file` plan type (URI) removed; `markdown` gains optional absolute `path` (omitted and `null` equivalent); `content` always required; v1 and v2 sections separated; the Preview move does not stabilize the feature (still behind `unstable_plan_operations`).

## 4. One-line summary per changed area

**Does v1 stable change?**

- v1 stable schema (`schema/v1/schema.json`, `meta.json`): **no**.
- v1 stable docs (`docs/protocol/v1/*.mdx` outside `draft/`): **one file**, `docs/protocol/v1/slash-commands.mdx`. It marks `availableCommands` as `required` in the `ResponseField` (a docs-only attribute, same one-line change as in the draft copy, commit `172f9a86` #2804). The TCK registry and map cite no `slash-commands.mdx`, so no citation is hit, but `spec-impact` does not scan this file (outside its scope).
- Everything else is in `draft/` docs and the unstable schema, i.e. unstable-only.

### Docs (`docs/protocol/v1/draft/`)

| Doc | Summary |
|---|---|
| `subagents.mdx` (new, 550 lines) | New page absorbing the Subagents RFD into the v1 draft docs: capability check, announcing child sessions, parents and nesting, child updates, session-directed messages, work state (`unknown`), restricted methods, cancellation, closing the parent, forking, connection loss, load/resume replay, usage and cost. |
| `agent-plan.mdx` | `file` plan type and "Plan file URIs MUST be absolute" removed; `markdown` plan gains optional nullable absolute `path` (`MUST` be absolute), `content` required. |
| `error.mdx` | Unknown sessions: a child session announced with `subagent_update` is not unknown; `session/cancel` may name a child; Agents `SHOULD` reject other requests naming a child with `-32602` (draft only). |
| `initialization.mdx` | New client capabilities `session.promptSuggestions` (+ `image`/`audio`/`embeddedContext` opt-ins), `session.cursors`, `subagents` (subagent section documented); new agent capability `sessionCapabilities.options`. |
| `overview.mdx` | Client notification list gains links to prompt suggestions, session cursors, subagent sessions. |
| `prompt-turn.mdx` | New session updates `prompt_suggestions_update` and `cursor_update` with full sections (Prompt suggestions, Session cursors); subagent / session-directed message text reworded to point at the new page (no sender assumed without evidence); `usage_update.cost` includes descendants. |
| `schema.mdx` | Generated reference: tracks all schema changes below. |
| `session-config-options.mdx` | New `speed` category (unstable): `SHOULD` order select values slowest to fastest, `SHOULD NOT` use for model/thought-level/mode; new "Options before a session exists" with `session/options` and initial `configOptions` values (`-32602` on schema-invalid or duplicate `configId`, unknown/disallowed entries ignored). |
| `session-setup.mdx` | `session/load` replay: prompt suggestions `SHOULD NOT` be replayed, cursor replay rules (`session.cursors`); new "Initial config option values (unstable)" section. |
| `slash-commands.mdx` | `availableCommands` marked required (docs attribute only). |
| `tool-calls.mdx` | Session content item links to the new subagents page; `tool_call_update.content` replaces the whole array, so session references must be re-sent; only references handles it can resolve. |

### Schema (`schema/v1/schema.unstable.json`)

- **Added** (20): `CursorAnchor`, `CursorAnchorPosition`, `CursorCapabilities`, `CursorCompactionAnchor`, `CursorForkCapabilities`, `CursorId`, `CursorMessageAnchor`, `CursorToolCallAnchor`, `CursorUpdate`, `InitialSessionConfigOption`, `PromptSuggestion`, `PromptSuggestionsAudioCapabilities`, `PromptSuggestionsCapabilities`, `PromptSuggestionsEmbeddedContextCapabilities`, `PromptSuggestionsImageCapabilities`, `PromptSuggestionsUpdate`, `SessionCursorsCapabilities`, `SessionOptionsCapabilities`, `SessionOptionsRequest`, `SessionOptionsResponse`.
- **Removed** (1): `PlanFile`.
- **Changed** (17), with the observed change:
  - `ClientSessionCapabilities`: gains `cursors`, `promptSuggestions`.
  - `SessionCapabilities`: gains `options`.
  - `SessionUpdate`: gains variants `cursor_update`, `prompt_suggestions_update`.
  - `SessionConfigOptionCategory`: gains `speed`.
  - `NewSessionRequest`, `LoadSessionRequest`, `ResumeSessionRequest`: gain `configOptions`.
  - `ForkSessionRequest`: gains `configOptions` and `cursorId`.
  - `PlanMarkdown`: gains `path`.
  - `PlanUpdateContent`: loses the `file` variant.
  - `AuthAccount`: gains `description`.
  - `ClientRequest`, `AgentResponse`: carry the new `session/options` method (variant added, shape-only).
  - `AuthStatusResponse`, `AuthStatusUpdateNotification`, `IdleStateUpdate`, `UnknownStateUpdate`: description-text-only changes (no property or variant change seen).
- Closure: 21 defs transitively reach a changed def (listed in section 1 part 4). Core `$defs` hit: `SessionUpdate` (directly), `AgentCapabilities` and `ClientCapabilities` (via closure).
- New agent method `session/options` (`SessionOptionsRequest`/`Response`).

### Core docs touched (escalation trigger)

`overview.mdx` (notification link list only), `initialization.mdx` (new capabilities), `prompt-turn.mdx` section `Session updates` (new updates, subagent wording), `error.mdx` (unknown sessions / children). `spec-impact` says: **core hit: yes, escalate**.

## 5. Requirement ids and ledger entries whose citations fall inside a change

From `spec-impact` section 6 (38 requirement ids, 25 ledger entries). Grouped by cause:

**Requirement ids** (`src/tck/v1/requirements.py`)

| Cause | Ids |
|---|---|
| `PlanFile` removed, plus doc and RFD hunks (also cites `plan-operations.mdx:63`, hunk `-63,1 +62,7`) | `ACP-PLAN-001` (direct text overlap: `agent-plan.mdx:127`, `rfds/plan-operations.mdx:63`) |
| Direct hunk overlap in docs | `ACP-LOAD-001` (`session-setup.mdx:110-201` vs `-149,0 +150,9`), `ACP-CLIENTCAP-007` (`prompt-turn.mdx:19-21`, `tool-calls.mdx:358`), `ACP-SUBAGENT-011` and `ACP-SUBAGENT-012` (`prompt-turn.mdx:106-111`; `-011` also `rfds/subagents.mdx:648-664`), `ACP-SUBAGENT-014` (`rfds/subagents.mdx:392-419` vs `-400,1 +400,1`) |
| `$ref` closure of changed schema defs | `ACP-JSONRPC-006`, `ACP-SCHEMA-001` (root closure), `ACP-INIT-001`, `ACP-AUTH-005` (`InitializeResponse` via `SessionCapabilities`/`SessionOptionsCapabilities`), `ACP-SESSION-001`/`-002`, `ACP-LOAD-001`/`-003`, `ACP-RESUME-001`, `ACP-CONFIG-001`/`-002`/`-003` (via `SessionConfigOptionCategory`), `ACP-PROMPT-002` (`SessionNotification` via cursor defs), `ACP-SUBAGENT-001`/`-006`/`-015` (`SubagentUpdate`/`StateUpdate` via `IdleStateUpdate`/`UnknownStateUpdate`) |
| Changed `$def` directly | `ACP-ARCHIVE-001` (`SessionCapabilities`), `ACP-ADDDIRS-001` and `ACP-ERROR-002` (`NewSessionRequest`), `ACP-LOAD-001` (`LoadSessionRequest`), `ACP-RESUME-001` (`ResumeSessionRequest`), `ACP-AUTH-007` (`AuthStatusResponse`) |
| Cites a changed RFD, cited lines untouched | `ACP-ARCHIVE-003`, `ACP-ARCHIVE-006` (`session-archive.mdx`), `ACP-AUTH-007`, `ACP-AUTH-008` (`get-auth-state.mdx`), `ACP-CLIENTCAP-007`, `ACP-SUBAGENT-001` to `-009`, `-012`, `-013`, `-015` to `-017` (`rfds/subagents.mdx`) |

Affected requirement ids, full list: ACP-JSONRPC-006, ACP-INIT-001, ACP-SCHEMA-001, ACP-SESSION-001, ACP-SESSION-002, ACP-PROMPT-002, ACP-LOAD-001, ACP-LOAD-003, ACP-RESUME-001, ACP-ARCHIVE-001, ACP-ARCHIVE-003, ACP-ARCHIVE-006, ACP-ADDDIRS-001, ACP-CONFIG-001, ACP-CONFIG-002, ACP-CONFIG-003, ACP-AUTH-005, ACP-AUTH-007, ACP-AUTH-008, ACP-CLIENTCAP-007, ACP-SUBAGENT-001..009 (001, 002, 003, 004, 005, 006, 007, 008, 009), ACP-SUBAGENT-011..017 (011, 012, 013, 014, 015, 016, 017), ACP-PLAN-001, ACP-ERROR-002. (ACP-SUBAGENT-010 is not reported.)

**Ledger entries** (`spec-tracker/maps/v1.toml`), all 25 as listed in section 1 part 6, by cause:

- Cite changed `rfds/get-auth-state.mdx` (6 entries: `auth/status` MUST NOT modify state; SHOULD advertise `auth.status`; SHOULD list accounts / `active: true`; `accounts` MUST NOT include secrets; SHOULD keep `auth/status` fast; SHOULD send `auth/status_update` on change).
- Cite `rfds/session-status.mdx` (1 entry), `rfds/session-set-title.mdx` (1 entry): RFD file touched, lines untouched.
- `x-deserialize-default-on-null` entry: `NewSessionRequest.mcpServers` (`NewSessionRequest` changed).
- Cite `rfds/subagents.mdx` (15 entries), of which three overlap a changed hunk: "reports each side of a session-directed message only when it can observe that side" (`:576-577`, hunk `-577,1 +585,4`), "reports the `unknown` state" (`:855-860`, hunk `-859,1 +885,4`, also `UnknownStateUpdate` changed), "do not fabricate an exclusive parent or child cost amount" (`:1168-1170`, hunk `-1158,31 +1205,24`: the section is **deleted**).

## 6. Stage-label refresh candidates (re-vendor step 4)

Citations in `src/tck/v1/requirements.py` and `spec-tracker/maps/v1.toml` carry a stage label. Counts of `(<Stage> RFD)` labels by RFD, against the stage at the target:

| RFD cited | Label now | Stage at target | Count |
|---|---|---|---|
| `subagents.mdx` | Active | Preview | 33 (17 in `requirements.py`, 16 in the map) |
| `plan-operations.mdx` | Draft | Preview | 1 (`ACP-PLAN-001`, `requirements.py:1531`) |
| `mcp-over-acp.mdx` | Active | Draft | 1 (`requirements.py:86`) |
| `get-auth-state.mdx` | Draft | Draft | 8 (unchanged) |
| `session-archive.mdx`, `session-set-title.mdx`, `session-status.mdx`, `proxy-chains.mdx` | Draft | Draft | 2, 1, 1, 1 (unchanged) |

Counts come from a grep on `docs/rfds/...mdx ... (<Stage> RFD)` in both files.

## Observations for the orchestrator (no impact analysis)

- The `file` plan type is gone from the v1 unstable schema, and `ACP-PLAN-001` cites `PlanFile`. The TCK's own validation is vendored-schema-driven, so the vendored copy will need re-vendoring before anything depends on it.
- The subagents cost rule is reversed (inclusive of descendants, Clients MUST NOT add). The ledger entry about "do not fabricate an exclusive parent or child cost amount" now cites deleted text.
- New v1 draft doc `subagents.mdx` absorbs the Subagents RFD text, so docs-over-RFD precedence now applies to the subagents requirements (cite the doc as primary, RFD as secondary).
- The v1 draft docs now document features whose RFDs are Draft (cursors, prompt suggestions, options, speed): docs govern for those, and none of them has any registry rows yet.
- No `rfd_audit` key in `spec-tracker/maps/v1.toml`: full audit of both tracked RFDs is required whatever the mode.
