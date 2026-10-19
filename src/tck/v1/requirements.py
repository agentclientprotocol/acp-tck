"""The ACP TCK requirement registry.

Every conformance assertion the TCK makes is backed by exactly one `Requirement` here, keyed
by a stable id (`ACP-<AREA>-<NNN>`). Requirements are *declared*, not derived from code, because
they encode a judgment call about spec text (tier, capability gating) that the schema itself
does not carry. `text`/`citation` come from the protocol specification -- see each entry's
`citation` before changing wording, not memory of the spec.

Conformance tests bind to a requirement via `@pytest.mark.requirement("ACP-…")` (see
`tck.common.plugin`). Two meta-tests (`tests/v1/test_registry.py`) keep this registry and the test suite
in sync: every marker id must exist here, and every id here must be referenced by at least one
test.
"""

from __future__ import annotations

from ..common.requirements import Requirement, Tier, make_cite
from .protocol import SCHEMA_REVISION

SPEC_REVISION = SCHEMA_REVISION
"""The spec commit every citation below is relative to (see `AGENTS.md` "Vendored schema").
Single source of truth is `tck.v1.protocol.SCHEMA_REVISION`."""

_cite = make_cite(SPEC_REVISION)


_DECLARATIONS: tuple[Requirement, ...] = (
    Requirement(
        id="ACP-TRANSPORT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text="Every line the agent writes to stdout is a single valid JSON-RPC 2.0 message.",
        citation=_cite("docs/protocol/v1/draft/transports.mdx:24,26"),
    ),
    Requirement(
        id="ACP-TRANSPORT-002",
        tier=Tier.MANDATORY,
        capability=None,
        text="The agent's stdout is valid UTF-8.",
        citation=_cite("docs/protocol/v1/draft/transports.mdx:6"),
    ),
    Requirement(
        id="ACP-JSONRPC-001",
        tier=Tier.MANDATORY,
        capability=None,
        text="A response's `id` echoes the request `id` exactly, for both integer and string ids.",
        citation=_cite("agent-client-protocol-schema/src/rpc.rs:12-39,250-294"),
    ),
    Requirement(
        id="ACP-JSONRPC-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A response carries exactly one of `result`/`error`; an error object has an "
            "integer `code` and a string `message`."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/overview.mdx:235-239; "
            "agent-client-protocol-schema/src/v1/error.rs:149-224"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Notifications never receive a response, success or error. Messages the agent "
            "itself initiates (they carry `method`) are not responses. Concluding \"no "
            "response arrived\" is inherently a heuristic wait (a quiet period derived from "
            "--tck-timeout, not an infinite one) -- see tck.v1.conformance._helpers.quiet_period."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/overview.mdx:239; "
            "agent-client-protocol-schema/src/v1/error.rs:9"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-004",
        tier=Tier.ADVISORY,
        capability=None,
        text="An unknown method yields error `-32601` (spec wording is \"should\").",
        citation=_cite("docs/protocol/v1/draft/extensibility.mdx:84-96"),
    ),
    Requirement(
        id="ACP-JSONRPC-005",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "After an erroneous request, the connection remains usable (subsequent requests "
            "still succeed)."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/overview.mdx:235-239 (J1), "
            "docs/protocol/v1/draft/extensibility.mdx:84-96 (J6); de-facto rule inferred from "
            "reference-SDK regression tests, not normative spec text -- rust-sdk "
            "src/agent-client-protocol/tests/jsonrpc_error_handling.rs:634-708,824-911, python-sdk "
            "tests/test_rpc.py:480-526 (Testability note 7)"
        ),
    ),
    Requirement(
        id="ACP-INIT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text="`initialize` succeeds and the result validates against the schema, with an integer `protocolVersion`.",
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:57; "
            "schema/v1/schema.unstable.json#/$defs/InitializeResponse"
        ),
    ),
    Requirement(
        id="ACP-INIT-002",
        tier=Tier.MANDATORY,
        capability=None,
        text="When the client requests protocol version 1, the agent returns 1.",
        citation=_cite("docs/protocol/v1/draft/initialization.mdx:99"),
    ),
    Requirement(
        id="ACP-INIT-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "When the client requests an unsupported protocol version (65535), the agent "
            "returns a successful result carrying an integer protocolVersion that (a) is not "
            "65535 -- echoing the client's requested version verbatim is not conformant, even "
            "though it is a successful result with an integer protocolVersion -- and (b) is at "
            "least the version the same agent returns for a v1 request. Equality is NOT "
            "required: an agent that legitimately supports multiple versions (e.g. answers 1 "
            "for a v1 request and 2 for anything >= 2) may correctly answer higher than its "
            "v1-request answer; only echoing 65535 verbatim, or answering something lower than "
            "its own v1 answer, is a violation -- an earlier, stricter equality rule produced a "
            "false FAIL against dual-version agents. The 65535 probe's params "
            "also carry a v2-shaped info object alongside the v1 fields, since the probe "
            "represents a future-version client and a dual-version router agent selects v2 for "
            "any requested version >= 2 (including 65535) and validates the params as a v2 "
            "InitializeRequest, whose info is REQUIRED -- omitting it would produce a spurious "
            "-32602 for a params-shape reason unrelated to version negotiation."
        ),
        citation=_cite("docs/protocol/v1/draft/initialization.mdx:97-101"),
    ),
    Requirement(
        id="ACP-INIT-004",
        tier=Tier.ADVISORY,
        capability=None,
        text="`agentInfo` with `name` and `version` is present in the `initialize` result.",
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:57,323; "
            "schema/v1/schema.unstable.json#/$defs/Implementation"
        ),
    ),
    Requirement(
        id="ACP-SCHEMA-001",
        tier=Tier.MANDATORY,
        capability=None,
        text="Every message the agent emits during a basic exchange validates against the vendored v1 schema.",
        citation=_cite(
            "schema/v1/schema.unstable.json#/anyOf/0 (the `Agent` envelope) (Testability notes)"
        ),
    ),
    Requirement(
        id="ACP-SESSION-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "`session/new` with an absolute `cwd` and `mcpServers: []` succeeds with a "
            "non-empty string `sessionId`, and the response validates against the schema."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:73; "
            "schema/v1/schema.unstable.json#/$defs/NewSessionResponse (Req 9; Testability notes "
            "'session/new with an absolute cwd...')"
        ),
    ),
    Requirement(
        id="ACP-SESSION-002",
        tier=Tier.MANDATORY,
        capability=None,
        text="Two `session/new` calls on the same connection return distinct `sessionId`s.",
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:73; "
            "schema/v1/schema.unstable.json#/$defs/NewSessionResponse (Req 9 'unique')"
        ),
    ),
    Requirement(
        id="ACP-SESSION-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "`session/new` with one stdio MCP server entry (`name`, absolute `command`, `args`, "
            "`env`) succeeds with a schema-valid result -- all agents MUST support the stdio "
            "MCP transport. The entry points at a stub MCP server shipped with the TCK "
            "(`tck.v1.conformance._mcp_stub`), run by the TCK's own Python interpreter."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:468,476-501; "
            "schema/v1/schema.unstable.json#/$defs/McpServer; "
            "schema/v1/schema.unstable.json#/$defs/McpServerStdio"
        ),
    ),
    Requirement(
        id="ACP-SESSION-004",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "After `session/new` with that stdio MCP server entry and one prompt turn, the agent "
            "has launched the stub server and sent it an MCP `initialize` request. SHOULD-level "
            "(\"Agents SHOULD connect to all MCP servers specified by the Client\"); the prompt "
            "turn gives an agent that connects lazily a chance to do so before the check."
        ),
        citation=_cite("docs/protocol/v1/draft/session-setup.mdx:638"),
    ),
    Requirement(
        id="ACP-PROMPT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A text-only `session/prompt` resolves with a successful result whose `stopReason` "
            "is one of the defined `StopReason` values."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:503; "
            "schema/v1/schema.unstable.json#/$defs/PromptResponse; "
            "schema/v1/schema.unstable.json#/$defs/StopReason (Req 24); "
            "docs/protocol/v1/draft/initialization.mdx:247, docs/protocol/v1/draft/content.mdx:31 "
            "(baseline text support, Req 7)"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Every `session/update` notification emitted during a prompt turn validates "
            "against the schema and carries the `sessionId` of the session being prompted. "
            "An agent that emits no updates during the turn is allowed (Req 1 places no MUST "
            "on emitting them, only on being *able* to send them); this test passes vacuously "
            "in that case."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:289 (Req 1); "
            "schema/v1/schema.unstable.json#/$defs/SessionNotification (SessionNotification); "
            "Testability notes 'Weakly assertable' first bullet"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A prompt containing a `resource_link` content block alongside text resolves with a "
            "successful result whose `stopReason` is a defined value. `initialization.mdx:247` "
            "and the schema's `PromptCapabilities` description both make Text and ResourceLink "
            "the baseline every agent MUST support; `content.mdx:31` only mentions text but does "
            "not exclude `resource_link`, which carries no prompt-capability requirement."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:247; "
            "schema/v1/schema.unstable.json#/$defs/PromptCapabilities; "
            "docs/protocol/v1/draft/content.mdx:31"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-004",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Every file path the agent emits is absolute: `locations[].path` and `diff` "
            "content `path` on any `tool_call`/`tool_call_update`, and `sessions[].cwd` in a "
            "`session/list` result (when `list` is advertised). Absolute means POSIX `/...`, a "
            "Windows drive path, or a UNC path. Passes vacuously when the agent emits no paths."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/overview.mdx:230; "
            "docs/protocol/v1/draft/session-list.mdx:136-137; "
            "schema/v1/schema.unstable.json#/$defs/ToolCallLocation/properties/path; "
            "schema/v1/schema.unstable.json#/$defs/Diff/properties/path"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "After `session/cancel` during an in-flight `session/prompt`, the prompt request "
            "resolves with a successful result whose `stopReason` is `cancelled`, not an error."
        ),
        citation=_cite("docs/protocol/v1/draft/prompt-turn.mdx:618,625 (Reqs 25, 26)"),
    ),
    Requirement(
        id="ACP-CANCEL-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Content and tool call updates (`user_message_chunk`, `agent_message_chunk`, "
            "`agent_thought_chunk`, `tool_call`, `tool_call_update`) for the cancelled session "
            "arrive before the `session/prompt` response; none arrive after it. Session-state "
            "updates (e.g. `session_info_update`, `usage_update`) are allowed outside a turn and "
            "are not judged. \"None arrive after it\" is checked with a quiet period derived from "
            "--tck-timeout (tck.v1.conformance._helpers.quiet_period), not an infinite wait."
        ),
        citation=_cite("docs/protocol/v1/draft/prompt-turn.mdx:38,629"),
    ),
    Requirement(
        id="ACP-LOAD-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.loadSession",
        text=(
            "`session/load` with a valid `sessionId`, `cwd`, and `mcpServers` succeeds with a "
            "schema-valid `LoadSessionResponse` object."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:106,110-200 (`{}` result example at "
            "191-200); "
            "schema/v1/schema.unstable.json#/$defs/AgentCapabilities/properties/loadSession; "
            "schema/v1/schema.unstable.json#/$defs/LoadSessionResponse; "
            "schema/v1/schema.unstable.json#/$defs/LoadSessionRequest (C1, L1, L4)"
        ),
    ),
    Requirement(
        id="ACP-LOAD-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.loadSession",
        text=(
            "Every history update belonging to the `session/load` replay arrives before the "
            "`session/load` response; no history-kind update (`user_message_chunk`, "
            "`agent_message_chunk`, `agent_thought_chunk`, `tool_call`, `tool_call_update`) for "
            "the session arrives after it. Session-state updates (e.g. "
            "`available_commands_update`) are allowed outside a turn and are not judged. No claim "
            "is made about how many history updates are replayed or their fidelity."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:136-142,191-192; "
            "docs/protocol/v1/draft/prompt-turn.mdx:38"
        ),
    ),
    Requirement(
        id="ACP-LOAD-003",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The `session/load` empty result is `{}` (an object), not `null`. The schema allows "
            "only an object and the docs example shows `{}` (corrected from `null` upstream in "
            "`d89c8d31`). ADVISORY only: upstream's Rust schema crate tolerates `null` for "
            "defaultable payloads on receipt (`ac82df63`, deserialization only; the schema is "
            "unchanged), and the Python SDK coerces it too, so mandatory schema validation "
            "(ACP-LOAD-001) treats `null` as equivalent for an all-optional object response."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:194-200; "
            "schema/v1/schema.unstable.json#/$defs/LoadSessionResponse; "
            "agent-client-protocol-schema/src/serde_util.rs:30-38"
        ),
    ),
    Requirement(
        id="ACP-RESUME-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.resume",
        text=(
            "`session/resume` with `sessionId`, `cwd`, and `mcpServers: []` succeeds with a "
            "schema-valid `ResumeSessionResponse` object."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:239-244,266-277; "
            "schema/v1/schema.unstable.json#/$defs/ResumeSessionRequest; "
            "schema/v1/schema.unstable.json#/$defs/ResumeSessionResponse (C2, R1, R3)"
        ),
    ),
    Requirement(
        id="ACP-RESUME-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.resume",
        text=(
            "No `session/update` carrying conversation history (`user_message_chunk`, "
            "`agent_message_chunk`, `agent_thought_chunk`, `tool_call`, `tool_call_update`) for "
            "the resumed session arrives before the `session/resume` response -- the prohibition "
            "is scoped to history updates in the pre-response window only, not to every update "
            "kind or to updates after the response."
        ),
        citation=_cite("docs/protocol/v1/draft/session-setup.mdx:266-269 (R2)"),
    ),
    Requirement(
        id="ACP-LIST-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.list",
        text=(
            "`session/list` with `params: {}` succeeds with a schema-valid "
            "`ListSessionsResponse` whose `sessions` field is present as an array."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:82,94; "
            "schema/v1/schema.unstable.json#/$defs/ListSessionsRequest; "
            "schema/v1/schema.unstable.json#/$defs/ListSessionsResponse; "
            "schema/v1/schema.unstable.json#/$defs/SessionInfo (C2, S1, S3, S4)"
        ),
    ),
    Requirement(
        id="ACP-LIST-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.list",
        text=(
            "`session/list` filtered by a `cwd` that no session uses returns `sessions: []` "
            "(an empty array, never `null`, never an error)."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:84-87,166; "
            "schema/v1/schema.unstable.json#/$defs/ListSessionsRequest/properties/cwd (S2, S5)"
        ),
    ),
    Requirement(
        id="ACP-DELETE-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.delete",
        text=(
            "`session/delete` for a session created earlier on the same connection succeeds "
            "with a schema-valid empty-object result. Deleting an active session is "
            "implementation-defined, so the session is closed first when `close` is advertised; "
            "otherwise an error from deleting the still-active session SKIPs rather than FAILs."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-delete.mdx:69-81,89; "
            "schema/v1/schema.unstable.json#/$defs/DeleteSessionRequest; "
            "schema/v1/schema.unstable.json#/$defs/DeleteSessionResponse (C2, D1)"
        ),
    ),
    Requirement(
        id="ACP-DELETE-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Deleting an already-deleted or never-created `sessionId` SHOULD succeed silently, "
            "rather than erroring."
        ),
        citation=_cite("docs/protocol/v1/draft/session-delete.mdx:86 (D2)"),
    ),
    Requirement(
        id="ACP-DELETE-003",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.delete",
        text=(
            "After a successful `session/delete`, the deleted `sessionId` does not appear in a "
            "subsequent `session/list` result (all pages, filtered by the session's `cwd`). Also "
            "needs `sessionCapabilities.list`; SKIPs without it. The session is closed first "
            "when `close` is advertised, as for ACP-DELETE-001."
        ),
        citation=_cite("docs/protocol/v1/draft/session-delete.mdx:85,89"),
    ),
    Requirement(
        id="ACP-CLOSE-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.close",
        text=(
            "`session/close` for an existing, idle session succeeds with a schema-valid "
            "empty-object result."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:328-343; "
            "schema/v1/schema.unstable.json#/$defs/CloseSessionRequest; "
            "schema/v1/schema.unstable.json#/$defs/CloseSessionResponse (C2, X1)"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.close",
        text=(
            "`session/close` on a session with an in-flight `session/prompt` cancels the "
            "ongoing work as if `session/cancel` had been called, so the prompt resolves with "
            "`stopReason: \"cancelled\"`. Derived obligation, medium confidence -- the spec "
            "states the cancel-as-if via X2 and never says \"close\" explicitly next to "
            "`stopReason`; inferred by reference to the cancellation contract (X3)."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:332-334 -> "
            "docs/protocol/v1/draft/prompt-turn.mdx:618,625,629 (X2, X3)"
        ),
    ),
    Requirement(
        id="ACP-ADDDIRS-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.additionalDirectories",
        text="`session/new` with an absolute `additionalDirectories` entry is accepted.",
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:351-380; "
            "schema/v1/schema.unstable.json#/$defs/NewSessionRequest/properties/additionalDirectories "
            "(C2, A1, A2)"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.systemPrompt",
        text=(
            "`session/new` with `systemPrompt: {mode: \"append\", content: [<text block>]}` "
            "succeeds with a schema-valid result: every agent advertising the capability "
            "supports `append`, and MUST accept text content blocks. Unstable feature."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:411,415; "
            "schema/v1/schema.unstable.json#/$defs/SystemPrompt; "
            "schema/v1/schema.unstable.json#/$defs/SessionSystemPromptModeCapabilities"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.systemPrompt",
        text=(
            "`session/new` with a `systemPrompt.mode` the agent cannot support (the "
            "implementation-reserved `_tck_unsupported`) returns an error rather than creating "
            "the session. The error code is recorded, not asserted (`-32602` is only "
            "RECOMMENDED). Unstable feature."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:412,418; "
            "schema/v1/schema.unstable.json#/$defs/SystemPromptMode"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-003",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.systemPrompt",
        text=(
            "`session/new` with a non-text `systemPrompt.content` block (`resource_link`) "
            "returns an error rather than creating the session -- only text blocks are "
            "supported for now. Unstable feature."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:415,418; "
            "schema/v1/schema.unstable.json#/$defs/SystemPrompt/properties/content"
        ),
    ),
    Requirement(
        id="ACP-MODES-001",
        tier=Tier.CAPABILITY,
        capability="inferred:modes",
        text=(
            "When `session/new` returns a non-null `modes`, it validates against the schema "
            "and `currentModeId` refers to one of `availableModes` (derived from the field "
            "descriptions, not a stated MUST). Inferred support, not a "
            "boolean/object marker in `initialize` -- there is no `agentCapabilities` field for "
            "this; support is inferred from `session/new`'s own response (`capability` is a "
            "documentation-only string, not a real initialize-result path -- see module "
            "docstring of `test_session_config.py`). SKIPs with reason 'session/new returned no "
            "modes/configOptions' when absent."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-modes.mdx:17,49-75; "
            "schema/v1/schema.unstable.json#/$defs/SessionModeState; "
            "schema/v1/schema.unstable.json#/$defs/SessionMode (§7, §0)"
        ),
    ),
    Requirement(
        id="ACP-MODES-002",
        tier=Tier.CAPABILITY,
        capability="inferred:modes",
        text=(
            "`session/set_mode` to a different `modeId` succeeds with a schema-valid "
            "`SetSessionModeResponse`. No echo notification is "
            "required (§7: \"do not assert an echo notification\"), but if a "
            "`current_mode_update` (`session/update` with `sessionUpdate: "
            "\"current_mode_update\"`) for the session is observed, it MUST carry the schema "
            "field name `currentModeId` -- the docs' example at `session-modes.mdx:117-119` "
            "showed `modeId` until upstream fixed that docs bug in `b96b439`; the schema was "
            "always the source of truth here."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-modes.mdx:83-122 (`currentModeId` example at 117-119 "
            "since upstream b96b439); schema/v1/schema.unstable.json#/$defs/SetSessionModeRequest; "
            "schema/v1/schema.unstable.json#/$defs/SetSessionModeResponse; "
            "schema/v1/schema.unstable.json#/$defs/CurrentModeUpdate (§7)"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-001",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "When `session/new` returns a non-null `configOptions`, every entry's "
            "`currentValue` is valid per its declared type: a `boolean` entry's `currentValue` "
            "is a bool; a `select` entry's `currentValue` is one of its `options` (flat or "
            "grouped shape). Inferred support, same encoding as ACP-MODES-001 -- "
            "`capability=\"inferred:configOptions\"` is documentation-only."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-config-options.mdx:118-127,242; "
            "schema/v1/schema.unstable.json#/$defs/SessionConfigOption; "
            "schema/v1/schema.unstable.json#/$defs/SessionConfigSelect; "
            "schema/v1/schema.unstable.json#/$defs/SessionConfigBoolean (§7, §0)"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-002",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "`session/set_config_option` responds with a schema-valid result carrying the "
            "*complete* list of every "
            "previously-advertised `configOptions` id (not only the changed one), with the new "
            "value applied to the option that was changed -- stated as a MUST twice in the "
            "docs."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-config-options.mdx:301,328-333; "
            "schema/v1/schema.unstable.json#/$defs/SetSessionConfigOptionRequest; "
            "schema/v1/schema.unstable.json#/$defs/SetSessionConfigOptionResponse (§7 'complete "
            "list' rule)"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "An agent MUST NOT include a `type: \"boolean\"` config option in any "
            "`configOptions` payload unless the client advertised "
            "`clientCapabilities.session.configOptions.boolean: {}` -- a genuine client- "
            "controlled MUST NOT. Checked on `session/new`'s result, a "
            "`session/set_config_option` result, `session/load`/`session/resume` results when "
            "advertised, and any `config_option_update` seen meanwhile. Passes vacuously if the "
            "agent has no config options, or none of `type: \"boolean\"`, at all."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/SessionConfigOption/oneOf/1; "
            "schema/v1/schema.unstable.json#/$defs/SessionConfigBoolean (SessionConfigOption "
            "boolean variant); docs/protocol/v1/draft/session-config-options.mdx:204-206 "
            "(normative MUST NOT text); docs/protocol/v1/draft/initialization.mdx:172-181"
        ),
    ),
    Requirement(
        id="ACP-PROMPTCAP-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.promptCapabilities.image",
        text=(
            "When `agentCapabilities.promptCapabilities.image` is `true`, a `session/prompt` "
            "containing an `image` content block (`ImageContent`: `data`, `mimeType`) alongside "
            "text resolves with a successful result whose `stopReason` is a defined value."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:249-253; "
            "docs/protocol/v1/draft/content.mdx:54-56; "
            "schema/v1/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/ImageContent"
        ),
    ),
    Requirement(
        id="ACP-PROMPTCAP-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.promptCapabilities.audio",
        text=(
            "When `agentCapabilities.promptCapabilities.audio` is `true`, a `session/prompt` "
            "containing an `audio` content block (`AudioContent`: `data`, `mimeType`) alongside "
            "text resolves with a successful result whose `stopReason` is a defined value."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:255-257; "
            "schema/v1/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/AudioContent"
        ),
    ),
    Requirement(
        id="ACP-PROMPTCAP-003",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.promptCapabilities.embeddedContext",
        text=(
            "When `agentCapabilities.promptCapabilities.embeddedContext` is `true`, a "
            "`session/prompt` containing a `resource` content block (`EmbeddedResource` "
            "wrapping a text or blob resource) alongside text resolves with a successful result "
            "whose `stopReason` is a defined value."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:259-261; "
            "docs/protocol/v1/draft/content.mdx:122-125; "
            "schema/v1/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/EmbeddedResource"
        ),
    ),
    Requirement(
        id="ACP-AUTH-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When `initialize`'s `authMethods` is present, its entries' `id`s are unique "
            "(AUTH-A5). Schema shape itself (array-ness, `id`/`name` being present) is already "
            "covered by ACP-SCHEMA-001's full-exchange validation, and the test itself defers "
            "shape to it -- so the only thing this requirement actually asserts is uniqueness. "
            "ADVISORY, not MANDATORY: the schema only *describes* `id` as \"Unique identifier\" "
            "(a description, not a MUST) -- retiered down from an earlier MANDATORY tier, under "
            "which an agent with duplicate ids was forced NOT CONFORMANT on the strength of a "
            "schema description alone."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AuthMethodAgent/properties/id; "
            "schema/v1/schema.unstable.json#/$defs/AuthMethodTerminal/properties/id (AuthMethod.id "
            "description) (AUTH-A5)"
        ),
    ),
    Requirement(
        id="ACP-AUTH-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "No `authMethods[*].type == \"terminal\"` entry is advertised unless the client "
            "advertised `clientCapabilities.auth.terminal` (Req 23, AUTH-M4) -- a client- "
            "controlled MUST NOT, checked by connecting once without that capability."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AuthMethodTerminal; "
            "docs/protocol/v1/draft/authentication.mdx:126-128 (normative MUST NOT text) (Req 23; "
            "AUTH-M4)"
        ),
    ),
    Requirement(
        id="ACP-AUTH-003",
        tier=Tier.CAPABILITY,
        capability="inferred:authMethods",
        text=(
            "Capability-conditional (AUTH-C4), same documentation-only encoding as "
            "ACP-MODES-001/ACP-CONFIG-001 -- `capability=\"inferred:authMethods\"` is not a real "
            "`initialize`-result path; support is inferred from `authMethods` being non-empty "
            "AND `--tck-auth-method <id>` being given. "
            "SKIPs otherwise, since v1 never requires an agent to expose a testable auth flow "
            "and the TCK cannot guess a valid `methodId`. `authenticate` succeeding is NOT "
            "itself assertable -- a real agent may legitimately reject bad/expired/cancelled "
            "credentials, so an `authenticate` error SKIPs with a distinct "
            "reason instead of failing. Only when `authenticate` returns a result is anything "
            "asserted, and only two things: (AUTH-C3, shape-only) the result is a JSON object; "
            "(AUTH-C4, the one hard assertion this requirement makes) a subsequent `session/new` "
            "on the same connection does not fail with `-32000`."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AuthenticateRequest; "
            "schema/v1/schema.unstable.json#/$defs/AuthenticateResponse (AUTH-C3, AUTH-C4)"
        ),
    ),
    Requirement(
        id="ACP-AUTH-004",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.auth.logout",
        text=(
            "When `agentCapabilities.auth.logout` is advertised (object marker), `logout` "
            "succeeds with an object result (AUTH-C1/C2). Nothing is asserted about sessions "
            "after logout (must-NOT list) -- if `--tck-auth-method` was given, `logout` is "
            "called after a successful `authenticate`; otherwise it is called standalone and "
            "only its own success is checked. Only actually exercised when "
            "`--allow-logout`/`--tck-allow-logout` is given (destructive: may revoke the "
            "operator's own credentials); SKIPs otherwise."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AgentAuthCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/LogoutCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/LogoutRequest (AUTH-C1, AUTH-C2)"
        ),
    ),
    Requirement(
        id="ACP-AUTH-005",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "AUTH-A1: if `initialize`'s `authMethods` is empty or absent, `session/new` does "
            "not fail with `-32000`. Nothing in v1 requires an agent to gate anything behind "
            "`authenticate`, and `authMethods` is not required in `InitializeResponse`; an "
            "agent that advertises none and then returns -32000 has made the connection "
            "unusable with no defined remedy (v2 makes this rule explicit; v1 leaves it "
            "advisory). `skip_if_auth_gated` only excuses `-32000` when `authMethods` is "
            "non-empty -- with it empty/absent, the ordinary `session/new` assertion is left to "
            "fail on its own terms, which is deliberate (a broken agent legitimately fails "
            "whatever MANDATORY requirement needed that session, not just this one)."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/schema.mdx (InitializeResponse.authMethods optional) (AUTH-A1)"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT call `fs/read_text_file` or `fs/write_text_file` during a "
            "session/prompt turn when the client did not advertise `fs` support -- the mock "
            "client always advertises `clientCapabilities: {}`, so no `fs/*` request may ever "
            "be observed. PASS is vacuous for an agent that never needs file access."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/file-system.mdx:10,29; "
            "schema/v1/schema.unstable.json#/$defs/FileSystemCapabilities (Req 29)"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT call any `terminal/*` method during a session/prompt turn when "
            "the client did not advertise `clientCapabilities.terminal === true`. PASS is "
            "vacuous for an agent that never needs a terminal."
        ),
        citation=_cite("docs/protocol/v1/draft/terminals.mdx:10,26 (Req 30)"),
    ),
    Requirement(
        id="ACP-CLIENTCAP-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT call `elicitation/create` during a session/prompt turn when "
            "the client did not advertise any elicitation mode. PASS is vacuous for an agent "
            "that never elicits."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/elicitation.mdx:40-47,54; "
            "docs/protocol/v1/draft/initialization.mdx:160-166"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-004",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT send a `notice` session update unless the client advertised "
            "`clientCapabilities.session.notices` -- checked over a whole connection with "
            "`clientCapabilities: {}` (session/new, one prompt turn, `session/load` when "
            "advertised, then a quiet period). PASS is vacuous for an agent that never sends "
            "notices."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:266-269; "
            "docs/protocol/v1/draft/initialization.mdx:211-217; "
            "schema/v1/schema.unstable.json#/$defs/Notice"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-005",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT send `compaction_update` or `compaction_summary_chunk` unless "
            "the client advertised `clientCapabilities.session.compaction`, live or during "
            "`session/load` replay -- checked the same way as ACP-CLIENTCAP-004. PASS is vacuous "
            "for an agent that never reports compaction."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:328-333; "
            "docs/protocol/v1/draft/session-setup.mdx:139-142; "
            "docs/protocol/v1/draft/initialization.mdx:193-199; "
            "schema/v1/schema.unstable.json#/$defs/CompactionUpdate; "
            "schema/v1/schema.unstable.json#/$defs/CompactionSummaryChunk"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-006",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT send `plan_update` or `plan_removed` unless the client "
            "advertised `clientCapabilities.plan` -- checked the same way as ACP-CLIENTCAP-004. "
            "Unstable feature: an agent that does not implement plan operations never sends "
            "these and passes vacuously."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/agent-plan.mdx:10,53; "
            "docs/protocol/v1/draft/prompt-turn.mdx:25-26; "
            "schema/v1/schema.unstable.json#/$defs/PlanCapabilities"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-007",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT send `subagent_update`, `session_message`, or "
            "`session_message_chunk` unless the client advertised `clientCapabilities.subagents` "
            "-- checked the same way as ACP-CLIENTCAP-004. Unstable feature: an agent that does "
            "not expose subagents never sends these and passes vacuously."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:19-21,42; "
            "docs/rfds/subagents.mdx:72-74; "
            "schema/v1/schema.unstable.json#/$defs/SubagentCapabilities"
        ),
    ),
    Requirement(
        id="ACP-EXT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A request to an unknown, `_`-prefixed custom method receives *some* response -- "
            "a result or any error, not necessarily `-32601`. Judgment call: Req 42's "
            "\"recipients must respond to custom requests\" (extensibility.mdx:43,52,65,109) is "
            "phrased as a MUST and covers custom requests in general, distinct from the J6 rule "
            "that tiers the *specific* `-32601` error code an unrecognised method gets as "
            "SHOULD -- so \"responds at all\" stays MANDATORY here (the two rules cover "
            "different observables: \"a response exists\" vs. \"which code it carries\"), while "
            "the specific code remains ACP-JSONRPC-004's ADVISORY concern under J6 (not "
            "duplicated here)."
        ),
        citation=_cite("docs/protocol/v1/draft/extensibility.mdx:47,56,69,113 (Req 42)"),
    ),
    Requirement(
        id="ACP-META-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A `session/prompt` carrying `_meta` (e.g. a `traceparent` key, SHOULD-reserved by "
            "Req 43) is accepted and resolves with a normal, defined `stopReason`."
        ),
        citation=_cite("docs/protocol/v1/draft/extensibility.mdx:10-14,37-41,43 (Reqs 41, 43)"),
    ),
    Requirement(
        id="ACP-ERROR-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Every error object's `message` is non-empty and free of embedded newlines (E3: "
            "\"should be limited to a concise single sentence\" -- checked leniently, exact "
            "wording is never asserted); `data`, if present, needs no further shape check "
            "beyond already being valid JSON. Evidence comes from errors already provoked "
            "elsewhere in the suite (an unrecognised method, an invalid-params request); "
            "passes vacuously if the agent returns none."
        ),
        citation=_cite("agent-client-protocol-schema/src/v1/error.rs:149-224 (E3)"),
    ),
    Requirement(
        id="ACP-SHUTDOWN-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "After the client closes stdin, the agent process exits on its own within a "
            "lenient window, without needing SIGTERM/SIGKILL. Warning-level only (Testability "
            "note 11): the spec defines no shutdown method, only that the client closes stdin "
            "then kills the process if needed."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/overview.mdx (no shutdown method defined; Testability note 11)"
        ),
    ),
    Requirement(
        id="ACP-SCHEMA-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "No agent-emitted spec object (a request/notification `params`, or a successful "
            "response `result`) carries a root-level key outside its `$def`'s resolved "
            "`properties` union (following `allOf`/`anyOf`/`oneOf`/`$ref`), other than `_meta` "
            "-- Req 41 says implementations MUST NOT add custom root fields, a genuine MUST NOT. "
            "Downgraded to ADVISORY not because the underlying rule is soft, but because the "
            "check itself is: the vendored schema has no `additionalProperties: false` anywhere, "
            "so this is a hand-written approximation of the allowed-keys union (see "
            "`tck.v1.validation.find_unknown_root_keys`), and a false positive against a genuinely "
            "conforming agent would be an unrecoverable, unfair FAIL -- a testability-driven "
            "downgrade, not a claim that Req 41 is itself only SHOULD/MAY."
        ),
        citation=_cite("docs/protocol/v1/draft/extensibility.mdx:43 (Req 41)"),
    ),
    Requirement(
        id="ACP-STDERR-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "The byte count of stderr output observed during a full exchange is reported for "
            "informational purposes; never asserted on itself (Testability note T6: the spec "
            "places no MUST on stderr content) -- but still FAILs if the prerequisite handshake "
            "(`initialize`, `session/new`) itself fails, since that is a real conformance problem "
            "the probe correctly surfaces."
        ),
        citation=_cite("docs/protocol/v1/draft/transports.mdx (Testability note T6)"),
    ),
    Requirement(
        id="ACP-INFO-PARSE-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Behaviour on a malformed (non-JSON) stdin line is recorded -- reply `-32700` with "
            "`id: null`, reply otherwise, or stay silent -- along with whether the connection "
            "remains usable afterwards (a subsequent `session/new` still succeeds). Spec "
            "silent; reference SDKs disagree (rust-sdk replies -32700, python-sdk silently "
            "drops the line). Never asserts on the probed behaviour itself, but still FAILs if "
            "the prerequisite `initialize` handshake fails."
        ),
        citation=_cite(
            "agent-client-protocol-schema (spec silent); rust-sdk vs python-sdk divergence "
            "(Assertable only as warnings/informational)"
        ),
    ),
    Requirement(
        id="ACP-INFO-INVALIDREQ-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Behaviour on a syntactically-valid JSON value that is not a JSON-RPC envelope "
            "(`{\"foo\": \"bar\"}`) is recorded, same shape as ACP-INFO-PARSE-001. Spec silent; "
            "reference SDKs disagree (rust-sdk replies -32600, python-sdk silently drops it). "
            "Never asserts on the probed behaviour itself, but still FAILs if the prerequisite "
            "`initialize` handshake fails."
        ),
        citation=_cite(
            "agent-client-protocol-schema (spec silent); rust-sdk vs python-sdk divergence "
            "(Assertable only as warnings/informational)"
        ),
    ),
    Requirement(
        id="ACP-INFO-UNKNOWNSESSION-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "The error code (if any) returned for `session/prompt` against a `sessionId` the "
            "agent never created is recorded, never asserted -- v1 does not specify one "
            "(Discrepancy 6). Even a successful result is only recorded. Never asserts on the "
            "probed behaviour itself, but still FAILs if the prerequisite `initialize`/"
            "`session/new` handshake fails."
        ),
        citation=_cite("docs/protocol/v1/draft/error.mdx (stub; Discrepancy 6)"),
    ),
)

REGISTRY: dict[str, Requirement] = {requirement.id: requirement for requirement in _DECLARATIONS}


def get(requirement_id: str) -> Requirement:
    """Look up a requirement by id, raising a helpful `KeyError` if it is not registered."""
    try:
        return REGISTRY[requirement_id]
    except KeyError:
        raise KeyError(
            f"{requirement_id!r} is not a registered requirement id; known ids: "
            f"{sorted(REGISTRY)}"
        ) from None
