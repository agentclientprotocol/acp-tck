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
"""The spec commit every citation below is relative to (see `docs/development.md` "Vendored schema").
Single source of truth is `tck.v1.protocol.SCHEMA_REVISION`."""

_cite = make_cite(SPEC_REVISION)


_DECLARATIONS: tuple[Requirement, ...] = (
    Requirement(
        id="ACP-TRANSPORT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text="Every line the agent writes to stdout is a single valid JSON-RPC 2.0 message.",
        citation=_cite("docs/protocol/v1/draft/transports.mdx:20,21,23"),
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
        citation=_cite("agent-client-protocol-schema/src/v1/rpc.rs:11-13"),
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
            "docs/protocol/v1/draft/error.mdx:6-10; "
            "docs/protocol/v1/draft/overview.mdx:235-239; "
            "agent-client-protocol-schema/src/v1/error.rs:25-49; "
            "schema/v1/schema.unstable.json#/$defs/Error"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Notifications never receive a response, success or error. Probed with `session/cancel` "
            "(no prompt in flight), an unrecognized `_`-prefixed custom notification, "
            "`$/cancel_request` for a request id the agent never saw, and `mcp/message` "
            "notifications (the unstable MCP-over-ACP envelope, well-formed and malformed; the "
            "rule binds every agent, so the probe is not gated on `mcpCapabilities.acp`). The "
            "`mcp/message` probes break client rules on purpose: the envelope is sent only for "
            "an active request on a declared `acp` MCP server, to an agent that advertised "
            "`acp`, and `requestId` and `method` are required; the spec defines the agent's "
            "answer to exactly these inputs (no reply). An agent that exits instead of replying "
            "sent no reply (`ACP-EXT-002` judges a crash on `mcp/message`). Messages the agent "
            "itself initiates (they carry `method`) are not responses. Concluding \"no response arrived\" "
            "is a heuristic wait (a quiet period derived from --tck-timeout) -- see "
            "tck.v1.conformance._helpers.quiet_period."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/overview.mdx:239; "
            "agent-client-protocol-schema/src/v1/error.rs:9; "
            "docs/rfds/mcp-over-acp.mdx:225,257 (Active RFD); "
            "schema/v1/schema.unstable.json#/$defs/MessageMcpNotification"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-004",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "An unknown method yields error `-32601`. Only the code is a \"should\"; replying at all "
            "is ACP-EXT-001's concern."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:41-43; docs/protocol/v1/draft/extensibility.mdx:84-96"
        ),
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
            "docs/protocol/v1/draft/overview.mdx:235-239; "
            "docs/protocol/v1/draft/extensibility.mdx:84-96; spec silent, de-facto rule from "
            "reference-SDK regression tests -- rust-sdk@d5e8bf4 "
            "src/agent-client-protocol/tests/jsonrpc_error_handling.rs:697-772,796-886, "
            "python-sdk@11f8a4c tests/test_rpc.py:515-531"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-006",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "After a `$/cancel_request` notification naming a request id the agent never received, "
            "the connection stays usable: a subsequent `session/new` still succeeds. An agent is "
            "free to ignore `$/` notifications it does not support, but a notification must never "
            "break the connection."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/cancellation.mdx:12-14; "
            "schema/v1/schema.unstable.json#/anyOf/2/properties/params/anyOf/0; "
            "schema/v1/schema.unstable.json#/$defs/CancelRequestNotification"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-007",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "After `$/cancel_request` for an in-flight `session/prompt`, the agent still sends "
            "exactly one response to that request: a schema-valid `PromptResponse` result, or an "
            "error with code `-32800` (Request cancelled). Any other error code fails. An agent "
            "that does not support `$/cancel_request` and finishes the turn normally also "
            "satisfies this. SKIPs (\"cancellation not exercised\") when the prompt resolved "
            "before the notification could be sent, or when no response arrives within "
            "--tck-timeout: support is optional, so an ignored notification and a still-running "
            "turn look the same."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/cancellation.mdx:16-22; "
            "schema/v1/schema.unstable.json#/$defs/CancelRequestNotification; "
            "schema/v1/schema.unstable.json#/$defs/ErrorCode"
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
            "When the client requests an unsupported protocol version (65535), the agent returns a "
            "successful result whose integer `protocolVersion` (a) is not 65535 -- echoing an "
            "unsupported version verbatim breaks the MUST to answer with the latest supported "
            "version -- and (b) is at least the version the same agent returns for a v1 request. "
            "Equality is not required: an agent supporting several versions (e.g. 1 for a v1 "
            "request, 2 for anything >= 2) may answer higher than its v1 answer. The probe's "
            "params also carry a v2-shaped `info` object alongside the v1 fields: dual-version "
            "routers, and v1-only Rust SDK agents (which parse `info` for any requested version "
            ">= 2), reject such a request without it with `-32602`, a params-shape reason "
            "unrelated to version negotiation."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:97-101; rust-sdk@d5e8bf4 "
            "src/agent-client-protocol/src/jsonrpc/protocol_compat.rs:454-484, "
            "src/agent-client-protocol/tests/protocol_negotiation.rs:59-133,162-187"
        ),
    ),
    Requirement(
        id="ACP-INIT-004",
        tier=Tier.ADVISORY,
        capability=None,
        text="`agentInfo` with `name` and `version` is present in the `initialize` result.",
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:57,369; "
            "schema/v1/schema.unstable.json#/$defs/Implementation"
        ),
    ),
    Requirement(
        id="ACP-SCHEMA-001",
        tier=Tier.MANDATORY,
        capability=None,
        text="Every message the agent emits during a basic exchange validates against the vendored v1 schema.",
        citation=_cite("schema/v1/schema.unstable.json#/anyOf/0 (the `Agent` envelope)"),
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
            "docs/protocol/v1/draft/session-setup.mdx:480,488-513; "
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
        citation=_cite("docs/protocol/v1/draft/session-setup.mdx:650"),
    ),
    Requirement(
        id="ACP-SESSION-006",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The value of a stdio MCP server `env` entry (a random canary the TCK sends on "
            "`session/new`) never appears on the agent's stdout or stderr: not in responses, "
            "errors, `session/update`, `_meta`, `session/list` results or replayed history, and "
            "not in the stub MCP server's own command line. SHOULD-level, and only the "
            "client-observable part of the rule: model context, logging beyond stderr and "
            "persistence are not covered."
        ),
        citation=_cite("docs/protocol/v1/draft/session-setup.mdx:660"),
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
            "docs/protocol/v1/draft/prompt-turn.mdx:530; "
            "schema/v1/schema.unstable.json#/$defs/PromptResponse; "
            "schema/v1/schema.unstable.json#/$defs/StopReason (Req 24); "
            "docs/protocol/v1/draft/initialization.mdx:264, docs/protocol/v1/draft/content.mdx:31 "
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
            "docs/protocol/v1/draft/initialization.mdx:313 (Req 1); "
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
            "successful result whose `stopReason` is a defined value. All agents MUST support "
            "`resource_link` in prompts: it is part of the baseline every agent supports, "
            "independent of any prompt capability."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/content.mdx:170; "
            "docs/protocol/v1/draft/initialization.mdx:264; "
            "schema/v1/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/ContentBlock"
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
        citation=_cite("docs/protocol/v1/draft/prompt-turn.mdx:645,652 (Reqs 25, 26)"),
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
        citation=_cite("docs/protocol/v1/draft/prompt-turn.mdx:38,656"),
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
            "docs/protocol/v1/draft/session-setup.mdx:106,110-201 (`{}` result example at "
            "192-201); "
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
            "docs/protocol/v1/draft/session-setup.mdx:136-142,192-193; "
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
            "docs/protocol/v1/draft/session-setup.mdx:195-201; "
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
            "docs/protocol/v1/draft/session-setup.mdx:240-245,267-278; "
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
        citation=_cite("docs/protocol/v1/draft/session-setup.mdx:267-270 (R2)"),
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
        id="ACP-LIST-003",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/list` with a `cursor` the agent never issued SHOULD fail with `-32602` "
            "(Invalid params). A success (the cursor was ignored) or any other error code is an "
            "ADVISORY FAIL; `-32000` (authentication required) SKIPs. Only callable when "
            "`sessionCapabilities.list` is advertised; the test is gated on it."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:174; docs/protocol/v1/draft/error.mdx:47"
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
            "otherwise an error from deleting the still-active session SKIPs rather than FAILs. "
            "After that close, a `-32002` answer counts as a successful delete (an agent that "
            "forgets a session on close; ACP-DELETE-002 judges the SHOULD)."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-delete.mdx:69-81,85,87,90; "
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
            "when `close` is advertised, as for ACP-DELETE-001. A `-32002` answer to the delete "
            "counts as a successful delete, so the list check still runs."
        ),
        citation=_cite("docs/protocol/v1/draft/session-delete.mdx:85,87,90"),
    ),
    Requirement(
        id="ACP-ARCHIVE-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.archive",
        text=(
            "An agent advertising `sessionCapabilities.archive` also advertises "
            "`sessionCapabilities.list`. Judged from the `initialize` result alone."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:229; "
            "schema/v1/schema.unstable.json#/$defs/SessionCapabilities/properties/archive"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.archive",
        text=(
            "Every `SessionInfo` in a `session/list` result carries a boolean (non-null) "
            "`archived`: checked on the default view, and on the `only` view once the test's own "
            "session is archived. Needs `sessionCapabilities.list`; SKIPs without it, or when "
            "the list is empty."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:254; "
            "schema/v1/schema.unstable.json#/$defs/SessionInfo/properties/archived"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-003",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.archive",
        text=(
            "`session/archive` then `session/unarchive` on an existing session both succeed with "
            "schema-valid empty results. After archive the session is absent from the default "
            "`session/list` view and present under `archived: \"only\"`; after unarchive it is "
            "back in the default view and absent from `only`. Needs `sessionCapabilities.list`; "
            "SKIPs without it, or when the new session is not listed to begin with. An agent "
            "that rejects `only` FAILs, on the Draft RFD's rule that an agent advertising "
            "`archive` MUST support all three `archived` values."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:231,244-250; "
            "docs/rfds/session-archive.mdx:112 (Draft RFD); "
            "schema/v1/schema.unstable.json#/$defs/ArchiveSessionResponse; "
            "schema/v1/schema.unstable.json#/$defs/UnarchiveSessionResponse; "
            "schema/v1/schema.unstable.json#/$defs/SessionArchiveFilter"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-004",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.archive",
        text=(
            "`session/list` with an `archived` filter value the agent does not support fails "
            "with `-32602`, rather than falling back to the default (`exclude`) view. A success "
            "or any other error code is a FAIL; `-32000` (authentication required) SKIPs. Needs "
            "`sessionCapabilities.list`; SKIPs without it."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:252; "
            "schema/v1/schema.unstable.json#/$defs/SessionArchiveFilter"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-005",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.archive",
        text=(
            "Archiving an already-archived session and unarchiving a not-archived one both "
            "succeed. `session/archive` and `session/unarchive` of a never-created `sessionId` "
            "fail with an error rather than succeeding silently; the error code is not "
            "asserted."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:260; docs/protocol/v1/draft/error.mdx:67; "
            "schema/v1/schema.unstable.json#/$defs/ArchiveSessionRequest; "
            "schema/v1/schema.unstable.json#/$defs/UnarchiveSessionRequest"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-006",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.archive",
        text=(
            "After a successful `session/delete`, the deleted session appears under no "
            "`archived` filter value (`exclude`, `include`, `only`). Needs "
            "`sessionCapabilities.delete` and `.list`; SKIPs without them. The session is "
            "closed first when `close` is advertised, as for ACP-DELETE-001, and must be listed "
            "(under `include`) before the delete, else the row SKIPs. An agent that rejects "
            "`include` or `only` FAILs, on the Draft RFD's rule that an agent advertising "
            "`archive` MUST support all three `archived` values."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-list.mdx:261; "
            "docs/rfds/session-archive.mdx:112 (Draft RFD)"
        ),
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
            "docs/protocol/v1/draft/session-setup.mdx:329-344; "
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
            "docs/protocol/v1/draft/session-setup.mdx:333-335 -> "
            "docs/protocol/v1/draft/prompt-turn.mdx:645,652,656 (X2, X3)"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-003",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/close` is idempotent: closing a session this connection already closed, "
            "or one it never created, succeeds with the same empty result instead of an error. "
            "A `-32002` answer is the behavior clients are told to tolerate, but the agent "
            "SHOULD still return the empty result, so it is an ADVISORY FAIL. Only callable "
            "when `sessionCapabilities.close` is advertised; the test is gated on it."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:347-350; "
            "docs/protocol/v1/draft/error.mdx:55"
        ),
    ),
    Requirement(
        id="ACP-ADDDIRS-001",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.additionalDirectories",
        text="`session/new` with an absolute `additionalDirectories` entry is accepted.",
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:354-383; "
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
            "supports `append`, and MUST accept text content blocks."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:414,418; "
            "schema/v1/schema.unstable.json#/$defs/SystemPrompt; "
            "schema/v1/schema.unstable.json#/$defs/SessionSystemPromptModeCapabilities"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-002",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.systemPrompt",
        text=(
            "`session/new`, and `session/load`/`session/resume` of an existing session (each "
            "also gated on its own capability, `loadSession`/`sessionCapabilities.resume`), "
            "with a `systemPrompt.mode` the agent cannot support (the implementation-reserved "
            "`_tck_unsupported`) returns an error rather than creating, loading or resuming "
            "the session; after a refused load/resume, `session/prompt` on that id does not "
            "succeed. The error code is recorded, not asserted (`-32602` is only RECOMMENDED)."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:415,422; "
            "schema/v1/schema.unstable.json#/$defs/SystemPromptMode"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-003",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.sessionCapabilities.systemPrompt",
        text=(
            "`session/new`, and `session/load`/`session/resume` of an existing session (each "
            "also gated on its own capability, `loadSession`/`sessionCapabilities.resume`), "
            "with a non-text `systemPrompt.content` block (`resource_link`) returns an error "
            "rather than creating, loading or resuming the session -- only text blocks are "
            "supported for now; after a refused load/resume, `session/prompt` on that id does "
            "not succeed."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/session-setup.mdx:418,422; "
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
            "docs/protocol/v1/draft/session-config-options.mdx:118-130,245; "
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
            "docs/protocol/v1/draft/session-config-options.mdx:304,373-377; "
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
            "boolean variant); docs/protocol/v1/draft/session-config-options.mdx:207-209 "
            "(normative MUST NOT text); docs/protocol/v1/draft/initialization.mdx:189-198"
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
            "docs/protocol/v1/draft/initialization.mdx:266-270; "
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
            "docs/protocol/v1/draft/initialization.mdx:272-274; "
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
            "docs/protocol/v1/draft/initialization.mdx:276-278; "
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
            "When `initialize`'s `authMethods` is present, its entries' string `id`s are unique. "
            "Shape (array-ness, `id`/`name` present and typed) is ACP-SCHEMA-001's concern, so "
            "entries without a string `id` are left to it. ADVISORY: the schema only describes "
            "`id` as a \"Unique identifier\", without a MUST."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AuthMethodAgent/properties/id; "
            "schema/v1/schema.unstable.json#/$defs/AuthMethodTerminal/properties/id"
        ),
    ),
    Requirement(
        id="ACP-AUTH-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "No `authMethods[*].type == \"terminal\"` entry is advertised unless the client "
            "advertised `clientCapabilities.auth.terminal` -- checked by connecting once without "
            "that capability."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AuthMethodTerminal (description: agents MUST "
            "advertise it only when the client enabled terminal authentication); "
            "docs/protocol/v1/draft/authentication.mdx:126-128; "
            "docs/protocol/v1/draft/initialization.mdx:123-127"
        ),
    ),
    Requirement(
        id="ACP-AUTH-003",
        tier=Tier.CAPABILITY,
        capability="inferred:authMethods",
        text=(
            "After a successful `authenticate`, `session/new` on the same connection does not fail "
            "with `-32000` (authentication required). `capability=\"inferred:authMethods\"` is "
            "documentation-only (same encoding as ACP-MODES-001): the test runs only when "
            "`authMethods` is non-empty and `--tck-auth-method <id>` names one of its non-terminal "
            "entries, and SKIPs otherwise -- the client MUST NOT `authenticate` with a `terminal` "
            "method, and the TCK cannot guess a valid `methodId`. An `authenticate` error SKIPs "
            "too, since a real agent may legitimately reject bad or expired credentials. When it "
            "returns a result, that result is a JSON object (shape only) and the `session/new` "
            "check above is the one hard assertion."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/authentication.mdx:136-167,187-188; "
            "docs/protocol/v1/draft/session-setup.mdx:10; "
            "schema/v1/schema.unstable.json#/$defs/AuthenticateRequest; "
            "schema/v1/schema.unstable.json#/$defs/AuthenticateResponse"
        ),
    ),
    Requirement(
        id="ACP-AUTH-004",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.auth.logout",
        text=(
            "When `agentCapabilities.auth.logout` is advertised (object marker), `logout` succeeds "
            "with an object result. Nothing is asserted about sessions after logout (the spec "
            "leaves that unspecified) -- if `--tck-auth-method` was given, `logout` is called after "
            "a successful `authenticate`; otherwise it is called standalone and only its own "
            "success is checked. Only exercised when `--allow-logout`/`--tck-allow-logout` is "
            "given (destructive: may revoke the operator's own credentials); SKIPs otherwise."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/authentication.mdx:74-76,196-219; "
            "schema/v1/schema.unstable.json#/$defs/AgentAuthCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/LogoutCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/LogoutRequest"
        ),
    ),
    Requirement(
        id="ACP-AUTH-005",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "If `initialize`'s `authMethods` is empty or absent, `session/new` does not fail with "
            "`-32000` (authentication required). `session/new` may fail that way only if the agent "
            "requires authentication, and with no advertised method there is no defined remedy. "
            "Only `-32000` is judged here; any other `session/new` failure is ACP-SESSION-001's "
            "concern. `skip_if_auth_gated` only excuses `-32000` when `authMethods` is non-empty, "
            "so with it empty the session-dependent tests fail on their own terms too."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/InitializeResponse/properties/authMethods; "
            "docs/protocol/v1/draft/session-setup.mdx:10; "
            "docs/protocol/v1/draft/authentication.mdx:46-48"
        ),
    ),
    Requirement(
        id="ACP-AUTH-006",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "When the client advertises `clientCapabilities.auth.terminal: true`, the `initialize` "
            "result validates against the schema, including any `type: \"terminal\"` auth methods "
            "it now advertises (`args` an array of strings, `env` a string map; `null` `args`/`env` "
            "counts as omitted). `type` is the "
            "`AuthMethod` discriminator, so a `type: \"terminal\"` entry is also checked against "
            "`AuthMethodTerminal` itself (the schema's `anyOf` would otherwise accept it as an "
            "`agent` method). Passes with no terminal-specific evidence if the agent advertises "
            "none. The TCK never launches the terminal flow."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AuthMethod; "
            "schema/v1/schema.unstable.json#/$defs/AuthMethodTerminal; "
            "docs/protocol/v1/draft/initialization.mdx:123-127"
        ),
    ),
    Requirement(
        id="ACP-AUTH-007",
        tier=Tier.CAPABILITY,
        capability="agentCapabilities.auth.status",
        text=(
            "When `agentCapabilities.auth.status` is advertised (object marker), `auth/status` "
            "sent with `{}` params right after `initialize`, before any `authenticate` on the "
            "connection, returns a result that validates against `AuthStatusResponse` (an object "
            "with a string `state`). It is never an error, and in particular never `-32000` "
            "(authentication required): clients call it to learn whether authentication is "
            "needed. The test skips the `--tck-auth-method` auto-authenticate so the agent is "
            "observed unauthenticated."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/initialization.mdx:300-304; "
            "schema/v1/schema.unstable.json#/$defs/AgentAuthCapabilities/properties/status; "
            "schema/v1/schema.unstable.json#/$defs/AuthStatusRequest; "
            "schema/v1/schema.unstable.json#/$defs/AuthStatusResponse; "
            "docs/rfds/get-auth-state.mdx:293,297 (Draft RFD)"
        ),
    ),
    Requirement(
        id="ACP-AUTH-008",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When `auth.status` is advertised, the `state` in the `auth/status` result is one of "
            "`authenticated`, `unauthenticated`, `not_required`, `unknown`, or begins with `_`; "
            "other strings are reserved for future ACP variants. The schema accepts any string, "
            "so ACP-AUTH-007 cannot catch this. Only the result is judged: SKIPs when the call "
            "returns no string `state` (ACP-AUTH-007's concern). The test is gated on "
            "`agentCapabilities.auth.status`."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/AuthState; "
            "docs/rfds/get-auth-state.mdx:160-161 (Draft RFD)"
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
            "be observed. Also judged over the connection that advertises only "
            "`clientCapabilities.subagents` (the one `ACP-SUBAGENT-*` judge: `session/new`, one "
            "prompt turn, `session/load` when advertised, quiet periods): no `fs/*` request "
            "there either, including one carrying a child session's ID. PASS is vacuous for an "
            "agent that never needs file access."
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
            "the client did not advertise `clientCapabilities.terminal === true`. Also judged "
            "over the connection that advertises only `clientCapabilities.subagents` (see "
            "`ACP-CLIENTCAP-001`): no `terminal/*` request there either, including one carrying "
            "a child session's ID. PASS is vacuous for an agent that never needs a terminal."
        ),
        citation=_cite("docs/protocol/v1/draft/terminals.mdx:10,26 (Req 30)"),
    ),
    Requirement(
        id="ACP-CLIENTCAP-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent MUST NOT call `elicitation/create` during a session/prompt turn when "
            "the client did not advertise any elicitation mode. Also judged over the connection "
            "that advertises only `clientCapabilities.subagents` (see `ACP-CLIENTCAP-001`): no "
            "`elicitation/create` request there either, including one carrying a child "
            "session's ID. PASS is vacuous for an agent that never elicits."
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
            "docs/protocol/v1/draft/prompt-turn.mdx:293-296; "
            "docs/protocol/v1/draft/initialization.mdx:228-234; "
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
            "docs/protocol/v1/draft/prompt-turn.mdx:355-360; "
            "docs/protocol/v1/draft/session-setup.mdx:139-142; "
            "docs/protocol/v1/draft/initialization.mdx:210-216; "
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
            "`session_message_chunk`, nor `session` content (`{\"type\": \"session\"}`) in a "
            "`tool_call`, a `tool_call_update`, or a `session/request_permission` `toolCall`, "
            "unless the client advertised `clientCapabilities.subagents` -- checked the same way "
            "as ACP-CLIENTCAP-004. Unstable feature: an agent that does not expose subagents "
            "never sends these and passes vacuously."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:19-21,42; "
            "docs/protocol/v1/draft/tool-calls.mdx:358; "
            "docs/rfds/subagents.mdx:76-78,644-645 (Active RFD); "
            "schema/v1/schema.unstable.json#/$defs/SubagentCapabilities; "
            "schema/v1/schema.unstable.json#/$defs/SessionReference"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-001",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "The announcing `subagent_update` precedes every request or notification on a "
            "connection that advertised `clientCapabilities.subagents` and carries a child "
            "session's ID: a `session/update` for the child (inside a prompt turn or outside it, "
            "including after the turn ends and during `session/load` replay), an agent -> client "
            "request such as `session/request_permission`, `elicitation/create`, `fs/*` or "
            "`terminal/*` with the child's `sessionId`, and a live `session_message` naming the "
            "child as `senderSessionId` or `recipientSessionId`. The announcement must itself be "
            "sent on a known session (nested children included); traffic for an unannounced "
            "child FAILs. Stated by the draft docs' `SubagentUpdate` and the Subagents RFD "
            "(Active RFD). Replay is judged on its own terms: inside the `session/load` exchange "
            "only an announcement made within it counts, even if an earlier turn announced the "
            "child, because the client need not retain an earlier session tree and replayed "
            "child updates keep announcements before child traffic (Active RFD); a replayed "
            "`session_message`'s participant IDs are historical addresses, not announcements, "
            "and are not judged (Active RFD). Judged in wire order over one `session/new`, one "
            "prompt turn, a `session/load` of that session when `loadSession` is advertised "
            "(after a quiet period, so child traffic trailing the turn is not read as replay) "
            "and a quiet period after them. The mock client advertises only `subagents`, so "
            "which `fs/*`/`terminal/*`/`elicitation/create` requests an agent may send at all "
            "is not judged here (`ACP-CLIENTCAP-001`..`003` judge it, on this connection too); "
            "this row judges only whether the child's ID was announced first. Subagents have an "
            "`initialize` marker only on the client side, so support is inferred from the "
            "traffic (`capability=\"inferred:subagents\"` is documentation-only); SKIPs when no "
            "session ID the client did not create appears on the connection. Shared id: the v2 "
            "row judges the same rule without the client marker and without `fs/*`/`terminal/*`, "
            "which v2 removed."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/schema.mdx:8709-8713; "
            "schema/v1/schema.unstable.json#/$defs/SubagentUpdate; "
            "docs/rfds/subagents.mdx:95-99,189-193,933-935,942-948,981-987 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-002",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "A `session` tool-call content item (`SessionReference`) names a session already "
            "known: one the client created, or a child announced by an earlier `subagent_update` "
            "on a known session. Judged for every such item in a `tool_call` or "
            "`tool_call_update` `content` array and a `session/request_permission` request's "
            "`toolCall.content`, in wire order over the connection that advertised `subagents` "
            "(see `ACP-SUBAGENT-001` for its scope). A reference to a session no announcement "
            "preceded FAILs. A reference replayed inside the `session/load` exchange is a "
            "historical address, so is neither judged nor counted (Active RFD: a replayed "
            "reference to an unavailable session follows the historical replay rules). A "
            "reference does not count as traffic carrying the child's ID, so it never FAILs "
            "`ACP-SUBAGENT-001`. The draft docs state the rule, but only an agent that emits "
            "`session` content is bound and no agent-side `initialize` marker announces that, so "
            "the row is gated by `inferred:subagents` (documentation-only) and SKIPs when no "
            "`session` content item appears outside a replay. Shared id with v2."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/tool-calls.mdx:349-351; "
            "docs/rfds/subagents.mdx:636-639 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-003",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "A `subagent_update` never makes a session its own parent: `update.sessionId` differs "
            "from the `sessionId` of the session the notification is sent on, whichever session "
            "that is. Stated only by the Subagents RFD (Active RFD: `the association cannot ... "
            "refer to itself`), so the row is capped at CAPABILITY and gated by "
            "`inferred:subagents` (documentation-only). Judged for every `subagent_update` over "
            "the connection that advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); "
            "SKIPs when none appears. A self-referencing update is judged here and by no other "
            "association row (`ACP-SUBAGENT-004`/`-005` leave it out), so one defect never FAILs "
            "several. Shared id with v2."
        ),
        citation=_cite("docs/rfds/subagents.mdx:165-169 (Active RFD)"),
    ),
    Requirement(
        id="ACP-SUBAGENT-004",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "A `subagent_update` never announces a session ID that is already an ordinary session "
            "the client created with `session/new`, as the child of another session. The child's "
            "ID identifies the child session in all ACP messages and is unique within the "
            "connection, so it is not reused for an unrelated session. Stated only by the "
            "Subagents RFD (Active RFD), so the row is capped at CAPABILITY and gated by "
            "`inferred:subagents`. A client session announced as its own child is "
            "`ACP-SUBAGENT-003`'s. Judged for every `subagent_update` over the connection that "
            "advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); SKIPs when none "
            "appears. Announcing a client session under one of its own descendants is the cycle "
            "case of this row. Shared id with v2."
        ),
        citation=_cite("docs/rfds/subagents.mdx:122-124,165-169 (Active RFD)"),
    ),
    Requirement(
        id="ACP-SUBAGENT-005",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "A child announced on a known session keeps that one immediate parent: a later "
            "`subagent_update` for the same `sessionId` sent on a different session (a "
            "reparenting, which includes one that would create a cycle) FAILs. Later updates only "
            "modify the association's metadata, not its ownership. The draft docs state the "
            "ownership rule and the RFD states the one-parent, no-cycle rule; the rule binds only "
            "an agent that emits `subagent_update`, so the row is CAPABILITY and gated by "
            "`inferred:subagents`. The remaining ways to close a cycle are `ACP-SUBAGENT-003` (a "
            "self-parent) and `-004` (a client session announced as a child), so a cycle never "
            "FAILs more than one row. Judged for every `subagent_update` sent on a known session "
            "over the connection that advertised `subagents` (see `ACP-SUBAGENT-001` for its "
            "scope); SKIPs when none appears. Shared id with v2."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/schema.mdx:8705-8707; "
            "docs/rfds/subagents.mdx:165-169 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-006",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "`SubagentUpdate.cwd` and every `additionalDirectories` entry is an absolute path: "
            "POSIX `/...`, a Windows drive path or a UNC path (native syntax of the agent's "
            "machine, not a URI). `null` clears the field and an omitted field is unchanged, so "
            "neither is judged. The vendored schema types both as a bare `string`, so schema "
            "validation (`ACP-SUBAGENT-015`) accepts a relative path and this row is the only "
            "check for it; a value of the wrong type (a non-string `cwd`, a non-array "
            "`additionalDirectories`, a non-string entry) is a schema defect, "
            "`ACP-SUBAGENT-015`'s, and is not judged here. The draft docs state the rule; only an "
            "agent that emits `subagent_update` is bound, so the row is CAPABILITY and gated by "
            "`inferred:subagents`. Judged for every `subagent_update` over the connection that "
            "advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); SKIPs when none "
            "carries a string `cwd` or `additionalDirectories` entry. Shared id with v2."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/schema.mdx:8741,8760; "
            "schema/v1/schema.unstable.json#/$defs/SubagentUpdate/properties/cwd; "
            "schema/v1/schema.unstable.json#/$defs/SubagentUpdate/properties/additionalDirectories; "
            "docs/rfds/subagents.mdx:298-308 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-007",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "In a `session_message` whose `senderSessionId` and `recipientSessionId` are both "
            "known (supplied by this upsert or an earlier one for the same `messageId` in the "
            "same transcript; `null` clears, omitted keeps), they identify different sessions. A "
            "message a session sends to itself FAILs, whatever session the update is sent on "
            "(`ACP-SUBAGENT-008` judges only messages with different participants, so one defect "
            "never FAILs both). Stated only by the Subagents RFD (Active RFD: `they identify "
            "different sessions`), so the row is capped at CAPABILITY and gated by "
            "`inferred:subagents` (documentation-only). Judged for every `session_message` over "
            "the connection that advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); "
            "SKIPs when no message has both participants known. Shared id with v2."
        ),
        citation=_cite("docs/rfds/subagents.mdx:477-480 (Active RFD)"),
    ),
    Requirement(
        id="ACP-SUBAGENT-008",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "In a `session_message` whose `senderSessionId` and `recipientSessionId` are both "
            "known and different, the outer `params.sessionId` is one of them: the sender's "
            "transcript holds the outgoing view and the recipient's the incoming view, so an "
            "update sent on a third session FAILs. Participants are stored across upserts of the "
            "same `messageId`, as for `ACP-SUBAGENT-007`, whose equal-participant case this row "
            "leaves out. Stated only by the Subagents RFD (Active RFD: `the outer "
            "params.sessionId matches one of them`), so the row is capped at CAPABILITY and gated "
            "by `inferred:subagents`. Judged for every `session_message` over the connection that "
            "advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); SKIPs when no message "
            "has both participants known. A participant that was never announced is "
            "`ACP-SUBAGENT-001`'s. Shared id with v2."
        ),
        citation=_cite("docs/rfds/subagents.mdx:477-481 (Active RFD)"),
    ),
    Requirement(
        id="ACP-SUBAGENT-009",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "When both views of one message carry a reference, they name each other: an outgoing "
            "view's `recipientMessageId` names a view in the recipient's transcript, an incoming "
            "view's `senderMessageId` one in the sender's, and if that view was reported on the "
            "connection and carries the reverse reference, it names the first view's "
            "`messageId`. Conflicting references FAIL. Only that back-reference is compared, not "
            "the referenced view's own participants. A reference to a view the agent never "
            "reported, or to a view with no reference of its own, is not judged (each side is "
            "reported only when observed, and the draft docs add that views are not linked by "
            "equal IDs alone). The draft docs define what each field names; the RFD alone states "
            "the MUST that both references agree, so the row is capped at CAPABILITY and gated by "
            "`inferred:subagents`. Judged on the stored state after every `session_message` over "
            "the connection that advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); "
            "SKIPs when no two views were found that both carry a reference, so no link was "
            "judged. `session_message_chunk` carries no identity, so is not judged. Shared id "
            "with v2."
        ),
        citation=_cite(
            "docs/rfds/subagents.mdx:466-475 (Active RFD); "
            "docs/protocol/v1/draft/prompt-turn.mdx:96-100; "
            "docs/protocol/v1/draft/schema.mdx:7249,7263"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-011",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The task a parent gives a child is not reported as a `user_message_chunk` in the "
            "child's transcript (SHOULD NOT): none appears for an announced child before that "
            "child's first agent output (`agent_message_chunk` or `agent_thought_chunk`), which "
            "is when the first task has started its work. The Client cannot prompt a child, so "
            "such a message would attribute the task to the user. Judged over the connection that "
            "advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); SKIPs itself when no "
            "announced child produces agent output and none has a user message. Shared id with "
            "v2, whose rule also covers its `user_message`."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:106-111; "
            "docs/rfds/subagents.mdx:648-664 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-012",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The task a parent gives a child is reported as an incoming `session_message` in the "
            "child's transcript, with `senderSessionId` set to the parent, before the child's "
            "first agent output (SHOULD): the child's `agent_message_chunk` or "
            "`agent_thought_chunk` is preceded by such an upsert (the sender is stored across "
            "upserts of the `messageId`; the parent is the session that announced the child). A "
            "child whose task was reported as a `user_message_chunk` is `ACP-SUBAGENT-011`'s "
            "FAIL, so is not judged here. Judged over the connection that advertised `subagents` "
            "(see `ACP-SUBAGENT-001` for its scope); SKIPs itself when no announced child that "
            "was not told its task as a `user_message_chunk` produces agent output. Shared id "
            "with v2."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:106-111; "
            "docs/rfds/subagents.mdx:648-657 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-013",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Participant IDs go on the first `session_message` for a message when available, "
            "before the first `session_message_chunk` of a streamed message (SHOULD). Whether "
            "they were available cannot be seen, so a streamed message is flagged only when no "
            "participant ID was stored when its first chunk arrived and a later `session_message` "
            "for it supplies one (participant IDs follow the patch convention). A message that "
            "never names a participant, or has one before its first chunk, is not flagged. The "
            "draft docs state it without an RFC keyword (\"Include them ... when available\") "
            "and the Active RFD as a SHOULD; either way it is not a MUST. Judged over the "
            "connection that advertised `subagents` (see `ACP-SUBAGENT-001` for its scope); "
            "SKIPs itself when no `session_message_chunk` appears. Shared id with v2."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/prompt-turn.mdx:46-50; "
            "docs/rfds/subagents.mdx:461-464 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-014",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A select config option reported for a child in a `config_option_update` offers only "
            "its current value (SHOULD): the child does not permit Client-initiated "
            "configuration changes (the only mutation the Subagents RFD defines is `cancel`, and "
            "`session/set_config_option` is not authorized for a child), so the value is kept for "
            "its name without advertising choices the Client cannot select. Values are counted "
            "across option groups; boolean options and updates for a not-yet-announced child are "
            "not judged. Stated only by the Subagents RFD (Active RFD), so the row is ADVISORY. "
            "Judged over the connection that advertised `subagents` (see `ACP-SUBAGENT-001` for "
            "its scope); SKIPs itself when no `config_option_update` for an announced child "
            "carries a select. Shared id with v2."
        ),
        citation=_cite("docs/rfds/subagents.mdx:392-419 (Active RFD)"),
    ),
    Requirement(
        id="ACP-SUBAGENT-015",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "Every subagent message the agent sends to a client that advertised `subagents` "
            "validates against the v1 schema: the `update` of a `session/update` of kind "
            "`subagent_update`, `session_message` or `session_message_chunk` (`SessionUpdate`), "
            "and each `session` content item (`ToolCallContent`) of a `tool_call` / "
            "`tool_call_update` update or a `session/request_permission` request's `toolCall`. "
            "That includes a `subagent_update.state` (v1 reports a child's work state only "
            "there): a `StateUpdate` with a `state` discriminator. Only these subagent-specific "
            "parts are judged; the rest of a tool call or permission request, and the "
            "notification around an update, belong to the schema rows that judge them "
            "(`ACP-PROMPT-002`, `ACP-SCHEMA-001`), so one defect there never FAILs this row too. "
            "The draft schema defines these shapes; only an agent that exposes subagents is "
            "bound, so the row is CAPABILITY and gated by `inferred:subagents` "
            "(documentation-only) and SKIPs when no such update or item appears. Judged over the "
            "connection that advertised `subagents` (see `ACP-SUBAGENT-001` for its scope). "
            "v1-only: v2 validates every update of a turn in `ACP-PROMPT-002`, so this has no v2 "
            "counterpart."
        ),
        citation=_cite(
            "schema/v1/schema.unstable.json#/$defs/SubagentUpdate; "
            "schema/v1/schema.unstable.json#/$defs/StateUpdate; "
            "schema/v1/schema.unstable.json#/$defs/SessionMessage; "
            "schema/v1/schema.unstable.json#/$defs/SessionMessageChunk; "
            "schema/v1/schema.unstable.json#/$defs/SessionReference; "
            "docs/rfds/subagents.mdx:815-829 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-016",
        tier=Tier.CAPABILITY,
        capability="inferred:subagentCancel",
        text=(
            "A child whose `subagent_update` capabilities carry a `cancel` object may be cancelled "
            "with `session/cancel` for the child's `sessionId`, and confirms it: the child's "
            "state snapshot on the parent association (`subagent_update.state`, the only place v1 "
            "reports a child's work state) becomes `idle` with `stopReason: \"cancelled\"`. The "
            "per-child capability is stated by the draft docs and schema "
            "(`SubagentSessionCapabilities`: `cancel` `Permits the client to cancel this child's "
            "current work`); the confirmation is stated only by the Subagents RFD (Active RFD), "
            "and no `initialize` marker announces it, so the row is CAPABILITY, gated by "
            "`inferred:subagentCancel` (documentation-only). Judged on the connection that "
            "advertised `subagents`, in a driven turn of the cancel prompt: the TCK sends the "
            "request only to a child that advertises `cancel` and was last reported running (the "
            "client MUST NOT cancel one that does not) and gives the child `timeout / 2` to "
            "confirm. A child reported idle without being cancelled within `quiet_period` of the "
            "request, with a stop reason it could have reached on its own (the race window of "
            "`ACP-CANCEL-*`), had ended first: a cancellation racing with already-ended work "
            "does not rewrite its outcome, so that SKIPs. A later one means the child finished "
            "by other means and FAILs. SKIPs when no child advertised `cancel` while reported "
            "running. Shared id with v2 (which also accepts the confirmation on the child's own "
            "`state_update`)."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/schema.mdx:8694; "
            "schema/v1/schema.unstable.json#/$defs/SubagentSessionCapabilities/properties/cancel; "
            "docs/rfds/subagents.mdx:1069-1073,1089-1095 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-017",
        tier=Tier.CAPABILITY,
        capability="inferred:subagentCancel",
        text=(
            "`session/cancel` for a child cancels current work in that child, not its parent: "
            "after the TCK cancels a running child that advertises `cancel`, the parent's "
            "`session/prompt` is not answered with `stopReason: \"cancelled\"` before the TCK "
            "itself cancels the parent. Stated only by the Subagents RFD (Active RFD: `This "
            "cancels current work in that child, not its parent or siblings`), so the row is "
            "CAPABILITY, gated by `inferred:subagentCancel` (documentation-only). Siblings are "
            "not judged: the same RFD says the per-child capability `does not prevent the Agent "
            "from cancelling its own delegated work`, and an Agent that reacts to the cancelled "
            "child by stopping a sibling is indistinguishable on the wire from a cancel that "
            "leaked, so a sibling reported `idle`/`cancelled` is only recorded on the test's "
            "report entry (`acp_tck_cancelled_siblings`). Judged over the same driven turn as "
            "`ACP-SUBAGENT-016`, which owns the child's own confirmation, so one defect never "
            "FAILs both; a window of `quiet_period` after the child settles catches the parent's "
            "reaction. SKIPs when no child was cancelled or it had ended first. Shared id with "
            "v2."
        ),
        citation=_cite("docs/rfds/subagents.mdx:1069-1073 (Active RFD)"),
    ),
    Requirement(
        id="ACP-PLAN-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "When the client advertised `clientCapabilities.plan`, every `plan_update` whose "
            "`plan.type` is `\"file\"` carries an absolute `plan.uri`. The spec does not define "
            "\"absolute\"; the TCK reads it as an RFC 3986 URI with a scheme and, for `file:`, "
            "an RFC 8089 absolute path (`file:///tmp/plan.md`, `file:/tmp/plan.md`), so "
            "`plan.md`, `/tmp/plan.md` and `file:plan.md` fail. Unstable feature: an agent that "
            "sends no file plan passes vacuously."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/agent-plan.mdx:127; "
            "docs/rfds/plan-operations.mdx:63 (Draft RFD); "
            "schema/v1/schema.unstable.json#/$defs/PlanFile"
        ),
    ),
    Requirement(
        id="ACP-PLAN-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When the client advertised `clientCapabilities.plan`, the agent SHOULD send its "
            "plans with `plan_update` instead of the baseline `plan` update. Unstable feature: "
            "an agent that does not implement plan operations may keep sending `plan`, and an "
            "agent that sends no plan passes vacuously."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/agent-plan.mdx:57; "
            "docs/protocol/v1/draft/initialization.mdx:172-179; "
            "schema/v1/schema.unstable.json#/$defs/PlanCapabilities"
        ),
    ),
    Requirement(
        id="ACP-PERM-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "After the client answers `session/request_permission` by selecting the offered "
            "`reject_once` option, the agent does not carry out the operation. Observed as a "
            "file the agent was asked to create in its `cwd` not appearing; SKIPs when the agent "
            "asks no permission or offers no `reject_once` option."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/tool-calls.mdx:247; "
            "docs/protocol/v1/draft/security.mdx:12"
        ),
    ),
    Requirement(
        id="ACP-PERM-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "After the client answers `session/request_permission` with a `selected` outcome "
            "whose `optionId` the agent never offered, the agent does not carry out the "
            "operation: an outcome it does not recognise is not approval. Observed the same way "
            "as ACP-PERM-001; SKIPs when the agent asks no permission."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/tool-calls.mdx:249; "
            "schema/v1/schema.unstable.json#/$defs/SelectedPermissionOutcome"
        ),
    ),
    Requirement(
        id="ACP-EXT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A request to an unknown, `_`-prefixed custom method receives *some* response -- a "
            "result or any error, not necessarily `-32601`. Custom requests must get a response "
            "(ACP follows JSON-RPC 2.0, where every request expects a result or error); only the "
            "specific `-32601` code is a \"should\", which is ACP-JSONRPC-004's concern."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/extensibility.mdx:47,56,69,84; "
            "docs/protocol/v1/draft/overview.mdx:10-12"
        ),
    ),
    Requirement(
        id="ACP-EXT-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "An unrecognized `_`-prefixed custom notification is ignored: the connection stays "
            "usable and a subsequent `session/new` still succeeds. The same holds for "
            "`mcp/message` notifications (the unstable MCP-over-ACP envelope, well-formed and "
            "malformed) sent to an agent that does not advertise `mcpCapabilities.acp`, which "
            "has not recognized the method; those probes break client rules on purpose (the "
            "envelope is for an active request on a declared `acp` server, and `requestId` and "
            "`method` are required) because the spec defines how an agent treats a "
            "notification it does not recognize, and that probe SKIPs when `acp` is "
            "advertised. That a notification gets no reply is ACP-JSONRPC-003's concern."
        ),
        citation=_cite("docs/protocol/v1/draft/extensibility.mdx:113"),
    ),
    Requirement(
        id="ACP-META-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A `session/prompt` carrying `_meta` (including a `traceparent` key, reserved for "
            "trace context) is accepted and resolves with a normal, defined `stopReason`."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/extensibility.mdx:10-14,37-43; "
            "schema/v1/schema.unstable.json#/$defs/PromptRequest/properties/_meta"
        ),
    ),
    Requirement(
        id="ACP-ERROR-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Every error object's `message` is non-empty and free of embedded newlines (the schema "
            "says it \"should be limited to a concise single sentence\" -- checked leniently, exact "
            "wording is never asserted); `data` needs no further shape check. Evidence comes from "
            "an unrecognized-method request and an invalid-params `session/new`. A probe the agent "
            "leaves unanswered contributes no sample (silence on the custom method is ACP-EXT-001's "
            "concern); passes vacuously if the agent returns no errors."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:9; "
            "agent-client-protocol-schema/src/v1/error.rs:40-42; "
            "schema/v1/schema.unstable.json#/$defs/Error/properties/message"
        ),
    ),
    Requirement(
        id="ACP-ERROR-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A request with invalid params (`session/new` without the required `cwd`) yields error "
            "`-32602` (Invalid params). SKIPs on `-32000`, since the agent may check "
            "authentication before params."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:31,45-47; "
            "schema/v1/schema.unstable.json#/$defs/ErrorCode; "
            "schema/v1/schema.unstable.json#/$defs/NewSessionRequest; JSON-RPC 2.0 section 5.1; "
            "rust-sdk@d5e8bf4 src/agent-client-protocol/tests/jsonrpc_error_handling.rs:746,846; "
            "python-sdk@11f8a4c tests/test_rpc.py:515-529"
        ),
    ),
    Requirement(
        id="ACP-ERROR-003",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/prompt` naming a session that does not exist, or that this connection "
            "already closed (probed only when `sessionCapabilities.close` is advertised), gets "
            "error `-32002` with `data.sessionId` set to the requested id. Only SHOULD; a "
            "`-32000` reply SKIPs."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:51-55; "
            "schema/v1/schema.unstable.json#/$defs/ErrorCode"
        ),
    ),
    Requirement(
        id="ACP-ERROR-004",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/set_mode` and `session/set_config_option` naming an unknown session, and "
            "`session/load` or `session/resume` of a session that does not exist, get error "
            "`-32002` with `data.sessionId` set to the requested id (not a silent create-and-"
            "succeed). One probe per method, each gated on what it needs: `modes`/`configOptions` "
            "in `session/new`'s result, `loadSession`, `sessionCapabilities.resume`. Only SHOULD."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:51-55; "
            "schema/v1/schema.unstable.json#/$defs/ErrorCode"
        ),
    ),
    Requirement(
        id="ACP-ERROR-005",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A request other than `initialize` sent before initialization (a valid `session/new` "
            "as the connection's first message) gets error `-32600`. Only SHOULD; nothing is "
            "asserted about the connection afterwards."
        ),
        citation=_cite("docs/protocol/v1/draft/error.mdx:29,59-61"),
    ),
    Requirement(
        id="ACP-ERROR-006",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A stable capability-gated method the agent did not advertise (`session/load` without "
            "`loadSession`; `session/list`/`resume`/`close`/`delete` without the matching "
            "`sessionCapabilities` key), sent with well-formed params, gets error `-32601`. "
            "Probes every unadvertised method in one run and SKIPs if all are advertised (an "
            "inverted gate, computed in the test rather than by a capability marker). Only "
            "SHOULD; a `-32000` reply SKIPs."
        ),
        citation=_cite("docs/protocol/v1/draft/error.mdx:30,41-43"),
    ),
    Requirement(
        id="ACP-ERROR-007",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "On a known session, `session/set_mode` with an unknown `modeId`, and "
            "`session/set_config_option` with an unknown `configId` or an unsupported value for a "
            "select option, get error `-32602`. One probe each, gated on `modes`/`configOptions` "
            "in `session/new`'s result; the probe ids and values are `_tck`-prefixed so they "
            "cannot collide with real ones. The sentence has no RFC keyword, so ADVISORY."
        ),
        citation=_cite("docs/protocol/v1/draft/error.mdx:31,45-47"),
    ),
    Requirement(
        id="ACP-ERROR-008",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Every error code the agent returns that lies in a range reserved for JSON-RPC and "
            "ACP (`-32768..-32000` or `-32899..-32800`) is an ACP-defined one (`-32700`, "
            "`-32600`..`-32603`, `-32800`, `-32000`, `-32002`); implementation-specific errors "
            "SHOULD use codes outside those ranges. Sampled from the error replies to an "
            "unrecognised method, an invalid `session/new`, and a `session/prompt` for an "
            "unknown session; passes vacuously if none is an error."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:37; schema/v1/schema.unstable.json#/$defs/ErrorCode"
        ),
    ),
    Requirement(
        id="ACP-SHUTDOWN-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "After the client closes stdin, the agent process exits on its own within the close "
            "grace period, without needing SIGTERM/SIGKILL. Informational: the spec defines no "
            "shutdown method or timing, only that the client closes stdin and terminates the "
            "subprocess. FAILs if the agent needed a signal, or if `initialize`/`session/new` got "
            "no response at all (timeout or exit)."
        ),
        citation=_cite("docs/protocol/v1/draft/transports.mdx:37"),
    ),
    Requirement(
        id="ACP-SCHEMA-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "No agent-emitted spec object (a request/notification `params`, a successful response "
            "`result`, or an error object) carries a root-level key outside its `$def`'s resolved "
            "`properties` union (following `allOf`/`anyOf`/`oneOf`/`$ref`). `_meta` is allowed, "
            "except on error objects: `Error` defines only `code`, `message` and `data`. "
            "Implementations MUST NOT add custom root fields; ADVISORY only because the check is "
            "an approximation -- the vendored schema has no `additionalProperties: false`, so the "
            "allowed-keys union is built by hand (`tck.v1.validation.find_unknown_root_keys`), and "
            "a false positive against a conforming agent would be an unfair FAIL."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/extensibility.mdx:10-14,43; "
            "schema/v1/schema.unstable.json#/$defs/Error"
        ),
    ),
    Requirement(
        id="ACP-STDERR-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "The byte count of stderr output observed during an ordinary exchange is reported for "
            "information only, never asserted (the agent MAY log UTF-8 to stderr). FAILs only if "
            "`initialize` or `session/new` got no response at all (timeout or exit)."
        ),
        citation=_cite("docs/protocol/v1/draft/transports.mdx:22"),
    ),
    Requirement(
        id="ACP-INFO-PARSE-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Behaviour on a malformed (non-JSON) stdin line is recorded -- reply `-32700` with "
            "`id: null`, reply otherwise, or stay silent -- along with whether the connection "
            "remains usable afterwards (a subsequent `session/new` still succeeds). The spec "
            "assigns `-32700` to non-JSON input but requires no reply, and the client MUST NOT "
            "send such a line; reference SDKs disagree (rust-sdk replies -32700, python-sdk "
            "silently drops the line). Never asserts on the probed behaviour itself, but still "
            "FAILs if the prerequisite `initialize` handshake fails."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:28; "
            "docs/protocol/v1/draft/transports.mdx:24 (the client MUST NOT send this, so agent "
            "behaviour is undefined); rust-sdk vs python-sdk divergence"
        ),
    ),
    Requirement(
        id="ACP-INFO-INVALIDREQ-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Behaviour on a syntactically-valid JSON value that is not a JSON-RPC envelope "
            "(`{\"foo\": \"bar\"}`) is recorded, same shape as ACP-INFO-PARSE-001. The spec "
            "assigns `-32600` to a message that is not a valid request object but requires no "
            "reply, and the client MUST NOT send one; reference SDKs disagree (rust-sdk replies "
            "-32600, python-sdk silently drops it). Never asserts on the probed behaviour "
            "itself, but still FAILs if the prerequisite `initialize` handshake fails."
        ),
        citation=_cite(
            "docs/protocol/v1/draft/error.mdx:29; "
            "docs/protocol/v1/draft/transports.mdx:24 (the client MUST NOT send this, so agent "
            "behaviour is undefined); rust-sdk vs python-sdk divergence"
        ),
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
