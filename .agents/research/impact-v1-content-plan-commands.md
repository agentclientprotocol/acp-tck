# Impact research, v1: `content.mdx`, `agent-plan.mdx`, `slash-commands.mdx` (draft and stable)

**Sources checked:** agent-client-protocol, read with `git show` at base `3961af94` and target `3ea94133` from
`/Users/eugene/Documents/JetBrains/projects/agent-client-protocol-2`. That checkout's HEAD is `6ace4f6a`, which
descends from the target, and none of the files below differ between `3ea94133` and HEAD. Files read:
`docs/protocol/v1/draft/{content,agent-plan,slash-commands,overview,prompt-turn,initialization}.mdx`,
`docs/protocol/v1/slash-commands.mdx`, `docs/rfds/plan-operations.mdx` (used as context only), `docs/docs.json`,
`schema/v1/schema.unstable.json`, `schema/v1/schema.json` and `agent-client-protocol-schema/src/v1/plan.rs`.
TCK files: `src/tck/v1/requirements.py`, `spec-tracker/maps/v1.toml`, `src/tck/v1/conformance/test_plan.py`,
`_helpers.py`, `test_initialize.py`, the v1 plan fixtures, `tests/v1/test_cli.py` and `tests/v1/test_plan_uri.py`.
I did not consult the SDKs: the RFD settles what "absolute path" means (see below).
**Confidence:** high. The changes are small, the diffs are unambiguous, and the schema, the docs and the Rust model
agree.

## Summary of upstream changes in range

- `content.mdx`: **no change** (`git diff 3961af94..3ea94133` is empty). The schema defs it describes
  (`ContentBlock`, `TextContent`, `ImageContent`, `AudioContent`, `EmbeddedResource`, `EmbeddedResourceResource`,
  `ResourceLink`, `Text/BlobResourceContents`, `Annotations`) are byte-identical at base and target.
- `agent-plan.mdx` (commit `29a455b1`, #2815): the "File plans" section is removed, including the sentence "Plan
  file URIs **MUST** be absolute." (base `:127`). The Markdown plan example gains
  `"path": "/home/user/project/PLAN.md"`. Added text: `plan.content` (string, required)
  `docs/protocol/v1/draft/agent-plan.mdx:108-110`; `plan.path` (`string | null`, where omitted and `null` both mean
  "no file") `:112-115`; "`path` **MUST** be an absolute path." `:117`; "`content` is the plan to display whether
  or not `path` is set. Clients render `content` ... can use `path` to open the file." `:119`. The file shrinks by
  8 lines, so every line from base `:129` on moves up by 8.
- Schema (`schema.unstable.json`): `PlanFile` is removed. `PlanUpdateContent` is now `oneOf` with only `items` and
  `markdown`. `PlanMarkdown` gains `path: string|null` (with `x-deserialize-default-on-error`). `required` stays
  `["planId","content"]`. The Rust model is `path: Option<PathBuf>`
  (`agent-client-protocol-schema/src/v1/plan.rs:250,263 @ 3ea94133`), so the field has no typed absolute-path check
  in v1.
- `slash-commands.mdx`, draft `:45` and stable `docs/protocol/v1/slash-commands.mdx:45` (commit `172f9a86`,
  #2804): the `availableCommands` `ResponseField` gains `required`. Docs-only. Both `schema.json` and
  `schema.unstable.json` already had `AvailableCommandsUpdate.required = ["availableCommands"]` at base and still do.
  The commit message says it aligns the page with the schema. Apart from the link prefix on line 6, the stable page
  is identical to the draft page.
- Context: the RFD `docs/rfds/plan-operations.mdx` is now **Preview** (`docs/docs.json` group `Preview` at
  `3ea94133`). It states the same `path` rule (`:64`) and adds "`path` is an absolute path and not a URI, like the
  paths in tool call locations and diffs" (`:196`). Because the draft docs state the rule, the docs govern and the
  RFD is secondary.

## Table: `content.mdx`

The registry cites no other `content.mdx` lines, and the ledger has no `content.mdx` entries.

| Id / ledger | Classification | Target citation | Note |
|---|---|---|---|
| ACP-PROMPT-001 (`content.mdx:31`) | unchanged | `docs/protocol/v1/draft/content.mdx:31 @ 3ea94133` | Text MUST is unchanged. The same row's `initialization.mdx:264` moves to `:340` (initialization researcher's area). |
| ACP-PROMPT-003 (`content.mdx:170`) | unchanged | `content.mdx:170` | Its `initialization.mdx:264` citation moves to `:340` (not my doc). |
| ACP-PROMPTCAP-001 (`content.mdx:54-56`) | unchanged | `content.mdx:54-56` | Its `initialization.mdx:266-270` citation moves to `:342-346` (not my doc). |
| ACP-PROMPTCAP-003 (`content.mdx:122-125`) | unchanged | `content.mdx:122-125` | Its `initialization.mdx:276-278` citation moves to `:352-354` (not my doc). |
| ACP-PROMPTCAP-002 | n/a | | Cites no `content.mdx` line. Its `initialization.mdx:272-274` citation moves to `:348-350`, noted here only because it is the same family. |

There are no new requirements and no new ledger entries, because no text changed.

## Table: `agent-plan.mdx`

| Id / ledger | Classification | Target citation | Note |
|---|---|---|---|
| ACP-CLIENTCAP-006 (`agent-plan.mdx:10,53`) | unchanged | `agent-plan.mdx:10,53`, `prompt-turn.mdx:25-26` @ 3ea94133 | Both lines come before the hunks and are verbatim. `PlanCapabilities` is unchanged. |
| ACP-PLAN-001 (`agent-plan.mdx:127`, `plan-operations.mdx:63`, `#/$defs/PlanFile`) | **removed** | none | Upstream deleted the `file` plan type and its "URIs MUST be absolute" rule. The `PlanFile` pointer no longer resolves, so `test_registry.py` fails after re-vendor. Lifecycle: delete the row, `test_plan_file_uri_is_absolute`, `is_absolute_uri` (the only user is `test_plan.py`) and its unit tests in `tests/v1/test_plan_uri.py`, the fixture `emits_relative_plan_file_uri.py`, `test_relative_plan_file_uri_fails_plan_001_only`, and the id from `tests/v1/test_cli.py:59,525` and `:1909,1922`. Per guard 1, do not reuse `001` in this change. |
| ACP-PLAN-002 (`agent-plan.mdx:57`) | unchanged | `agent-plan.mdx:57`, `initialization.mdx:172-179` @ 3ea94133 | Verbatim. The fixtures that make it pass non-vacuously must stop sending a `file` plan (see the harness and fixture notes). |
| ledger `agent-plan.mdx:179,181` (complete list of entries) | citation-only | `agent-plan.mdx:171,173 @ 3ea94133` | The **reason text** also says "line 185 allows removing entries", which is now **line 177**. `spec-impact --fix` rewrites citations, not prose inside `reason`, so this needs a hand edit. The reason does not rest on a TCK choice. |
| ledger `agent-plan.mdx:147` (`plan_removed` SHOULD) | citation-only | `agent-plan.mdx:139 @ 3ea94133` | Text is verbatim. The reason ("no protocol event marks a plan as rejected or abandoned") does not rest on a TCK choice. |

### New requirements (agent-plan)

1. **`ACP-PLAN-003` (provisional): markdown plan `path` is absolute.**
   - Text: "When the client advertised `clientCapabilities.plan`, every `plan_update` whose `plan.type` is
     `\"markdown\"` and whose `plan.path` is a string carries an absolute path: POSIX `/...`, a Windows drive path or
     a UNC path, and not a URI. Omitted or `null` `path` means the plan has no file and is not judged. Unstable
     feature: an agent that sends no markdown plan with a `path` passes vacuously."
   - Tier: **MANDATORY**. The draft-docs MUST is the source, and the RFD is only secondary context. The only gate is a
     client capability, so it uses the same vacuous-pass pattern as ACP-PLAN-001 and ACP-CLIENTCAP-006. A `CAPABILITY`
     gate needs an agent-advertised path, so it does not fit.
   - Citation: `docs/protocol/v1/draft/agent-plan.mdx:112-117; docs/protocol/v1/draft/overview.mdx:233` ("All file
     paths in the protocol MUST be absolute"); `schema/v1/schema.unstable.json#/$defs/PlanMarkdown/properties/path`;
     secondary: `docs/rfds/plan-operations.mdx:64,196 (Preview RFD)`. Line 196 is the "not a URI, like tool call
     locations and diffs" reading.
   - Test: reuse `_updates_with_plan_capability` in `test_plan.py`, which opens a connection with `plan: {}`, sends a
     plan prompt and waits a quiet period. For each `plan_update` with `plan.type == "markdown"` and
     `isinstance(plan.get("path"), str)`, assert `is_absolute_path(path)`, the existing helper behind ACP-PROMPT-004
     and the subagent `cwd` checks (`_helpers.py:903`). A non-string `path` is a schema defect, so this row leaves it
     unjudged (see decision 2). A `file:///...` value fails, which is correct per RFD `:196`.
   - Harness: nothing new.
   - Fixtures:
     - `conforming_full.py` `PLANS`: replace the `file` entry with a markdown plan that carries `content` and an
       absolute `path`, for example `/tmp/plan.md`. `is_absolute_path` accepts a POSIX absolute path on any host.
     - New `emits_relative_plan_markdown_path.py`: a `plan_update` markdown plan with `"path": "plan.md"`, sent only to
       a `plan` client. Its CLI expectation is FAIL ids == {the new id}, with ACP-CLIENTCAP-006 PASS.
     - `plan_turn_never_ends.py`: switch from the `file` plan to a valid markdown or items plan.
     - Update `tests/v1/test_plan_uri.py::test_conforming_full_sends_plan_updates_only_when_plan_is_advertised`. It
       expects `{"items","file"}` and should expect `{"items","markdown"}`. Rename the module, since it no longer
       tests URIs.
     - `test_cli.py` id sets: add the new id wherever ACP-PLAN-001 was.
   - SDKs: no runtime question. Rust accepts any string (`PathBuf`), so a reference agent would not catch a relative
     path itself.

### New ledger entries (agent-plan)

None. The `content` sentence at `:119` is addressed to clients ("Clients render `content` ..."). Its agent-side
reading is RFD-only ("holds the whole plan", `plan-operations.mdx:62,68`) and carries no keyword (see decision 3).

## Table: `slash-commands.mdx` (draft) and stable `docs/protocol/v1/slash-commands.mdx`

No registry row or ledger entry cites either file (`grep` finds none in `requirements.py` or `v1.toml`).

| Id / ledger | Classification | Target citation | Note |
|---|---|---|---|
| (none) | n/a | `docs/protocol/v1/draft/slash-commands.mdx:45 @ 3ea94133` | The `required` attribute only restates the schema (`#/$defs/AvailableCommandsUpdate`, `required: ["availableCommands"]`, unchanged in range). The rule is already enforced: ACP-SCHEMA-001 validates every agent message over initialize, session/new and session/prompt (`test_initialize.py:141-`), which covers an `available_commands_update` sent after `session/new`, and ACP-PROMPT-002 covers updates during a turn. The v1 validator does not relax required properties: its carve-outs are only `null` under `x-deserialize-default-on-null` (`src/tck/v1/validation.py:22-31`), and `availableCommands` carries `default-on-error`, not `default-on-null`. |
| stable `docs/protocol/v1/slash-commands.mdx:45` | n/a | | The TCK never cites the stable docs tree (`docs/requirements.md` "Citations"; `test_registry.py` rejects such citations). The stable schema already required the field. **No TCK row should change.** |

There are no new requirements and no new ledger entries. The v1 slash-commands page has no agent-binding RFC 2119
rule beyond the MAY at `:10`. Lines `:73` and `:96` are descriptive, and the page is unchanged apart from `:45`.

## New requirements (all docs)

- `ACP-PLAN-003` (provisional): markdown `plan.path` is absolute. MANDATORY, no gate (vacuous pass). Details above.
- Optional `ACP-PLAN-004` (provisional; see decision 2): "Every `plan_update` or `plan_removed` the agent sends to a
  client that advertised `clientCapabilities.plan` validates against `#/$defs/SessionUpdate`." MANDATORY, backed by
  the schema plus `agent-plan.mdx:55,108-117`. The test validates each such `update` with `validate_against_def`
  over `_updates_with_plan_capability`, and it passes vacuously.

## New ledger entries

None.

## Decisions for the user

1. **Replace ACP-PLAN-001 with a new id, or rewrite it in place?** Upstream removed the URI rule and added a
   different rule on a different field (`path`, an absolute path and not a URI). Recommendation: **delete
   ACP-PLAN-001 and add `ACP-PLAN-003`** (lifecycle guard 1 forbids reusing `001` in this change). Coordinate the
   number with the v2 researcher: v2's `PlanMarkdown` also gained `path` (`src/v2/plan.rs:293`, `AbsolutePath`). If
   v2 adds the same rule, it should share this id (rule B, settled at id alignment).
2. **Close the shape gap on the `plan` connection (optional `ACP-PLAN-004`)?** No current row schema-validates the
   traffic on the connection that advertises `plan`. ACP-SCHEMA-001 and ACP-PROMPT-002 run on `plan`-less
   connections. After this update an agent that still sends a `file` plan sends a schema-invalid `plan_update`, and
   per the RFD a v1 client then fails to parse it (`plan-operations.mdx:79`). Yet that agent passes every row, because
   ACP-PLAN-001 is deleted and PLAN-003 only judges markdown. Recommendation: **add it, MANDATORY**, following the
   ACP-SUBAGENT-015 precedent (judge only the plan-specific `update`). This is a pre-existing gap that the change
   makes relevant, not new upstream text, so it is the user's call.
3. **Ledger entry for "`content` is the plan to display whether or not `path` is set" (`agent-plan.mdx:119`)?** The
   sentence is addressed to clients and has no keyword. The agent-side reading (content holds the whole plan) is
   RFD-only (`:62`). Nothing observable separates a "whole" plan from a short one. Recommendation: **no entry**. If
   the user prefers parity with the `ToolCallLocation.line` precedent, use reason "Not enforced: no RFC 2119
   keyword, and the protocol does not define how `content` relates to the file at `path`".
4. **Stable `slash-commands.mdx` `required`:** recommendation is **no TCK change** (the schema already enforces it,
   and stable docs are never cited).

## Ordering note for the plan

The re-vendor slice will fail `tests/v1/test_registry.py` because ACP-PLAN-001 cites `#/$defs/PlanFile`. It may
also fail any fixture check that validates `conforming_full.py`'s `file` plan against the new schema. Either the
re-vendor slice removes ACP-PLAN-001 along with its test and fixtures (a semantics change inside re-vendor), or it
temporarily retargets the pointer to `#/$defs/PlanUpdateContent` and the plan area slice deletes the row. The
orchestrator should pick one.

## Open questions

- Does v2 get a matching markdown-`path` row? This is for the v2 agent-plan or plan-operations researcher, and it
  decides whether `ACP-PLAN-003` is shared.
- `ledger agent-plan.mdx:179,181`: the reason's in-prose line number (`185` becomes `177`) is not covered by
  `spec-impact --fix`, so the slice must edit it by hand.
