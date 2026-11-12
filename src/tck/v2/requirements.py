"""ACP v2 (Draft) requirement registry.

Every conformance assertion the TCK makes is backed by exactly one `Requirement` here, keyed
by a stable id (`ACP-<AREA>-<NNN>`). `text`/`citation` come from the protocol specification --
see each entry's `citation` before changing wording, not memory of the spec.

A shared id (e.g. `ACP-SESSION-001`) means the same protocol rule in v1 and v2. Tier and
capability gate are per version (v2's object-marker `capabilities.*` paths differ from v1's
boolean `agentCapabilities.*` flags), and v1 and v2 keep fully separate `REGISTRY` dicts, so the
same id can carry a different tier or gate per version without conflict. A `2xx` id is a v2 rule
with no v1 counterpart.

Every requirement about a method in the `capabilities.session` seven-method baseline
(`session/new`, `session/list`, `session/resume`, `session/close`, `session/prompt`,
`session/cancel`, `session/update`) is `Tier.CAPABILITY`, `capability="capabilities.session"`,
never `Tier.MANDATORY`, regardless of the underlying spec obligation's own MUST-strength
wording -- only `initialize` itself is unconditionally required in v2; the whole session
surface is opt-in via that one capability marker. This applies throughout below and is not
repeated per row.

Conformance tests bind to a requirement via `@pytest.mark.requirement("ACP-…")` (see
`tck.common.plugin`). Two meta-tests (`tests/v2/test_registry.py`) keep this registry and the
test suite in sync: every marker id must exist here, and every id here must be referenced by
at least one test.
"""

from __future__ import annotations

from ..common.requirements import Requirement, Tier, make_cite
from .protocol import SCHEMA_REVISION

SPEC_REVISION = SCHEMA_REVISION
_cite = make_cite(SPEC_REVISION)

_DECLARATIONS: tuple[Requirement, ...] = (
    Requirement(
        id="ACP-INIT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "`initialize` succeeds with a non-error JSON-RPC result. Judged the same "
            "regardless of the negotiated `protocolVersion` -- unlike `ACP-INIT-004`/"
            "`ACP-INIT-204`/`ACP-SCHEMA-001`, this row does not SKIP when the agent negotiates "
            "down to a version other than 2. It does SKIP with `VERSION-MISMATCH` when the "
            "request of 2 is rejected with `-32022` (the agent has no version <= 2). "
            "Schema/shape validation of the result lives in `ACP-SCHEMA-001`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:24,51; "
            "schema/v2/schema.unstable.json#/$defs/InitializeResponse"
        ),
    ),
    Requirement(
        id="ACP-INIT-201",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent selects the highest version it supports that is <= the requested one: "
            "the result for a request of `2` has an integer `protocolVersion` no higher than "
            "2, and equals what a request of `65535` selects whenever that is <= 2. A `-32022` "
            "for the request of 2 is accepted only if the `65535` probe selects nothing <= 2."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:110; "
            "schema/v2/schema.unstable.json#/$defs/InitializeResponse/properties/protocolVersion"
        ),
    ),
    Requirement(
        id="ACP-INIT-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A request for a version above every supported one (`protocolVersion: 65535`, "
            "in range for the uint16 `ProtocolVersion`) succeeds -- neither `-32602` nor "
            "`-32022` applies -- and selects the agent's highest supported version: not the "
            "request echoed back, and at least what the same agent selects for a request of "
            "`2`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:108,110; "
            "schema/v2/schema.unstable.json#/$defs/ProtocolVersion"
        ),
    ),
    Requirement(
        id="ACP-INIT-202",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A v1-shaped request (`protocolVersion: 1`, no `info`) either succeeds selecting a "
            "version <= 1 (a dual-stack or v1 agent) or is rejected with `-32022` (a v2-only "
            "agent). Selecting 2 or higher FAILs, and so does `-32602`, which is reserved for "
            "a malformed `protocolVersion`."
        ),
        citation=_cite("docs/protocol/v2/draft/initialization.mdx:108,110,112"),
    ),
    Requirement(
        id="ACP-INIT-205",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A request with no supported version at or below it (`protocolVersion: 0`) either "
            "selects 0 or is rejected with `-32022` whose `data` is an object with "
            "`requested` (the requested version) and `supported` (an integer array with no "
            "entry <= the request, containing 2). Any `-32022` to `ACP-INIT-202`'s v1 request "
            "is held to the same `data` shape. Binds agents implementing v2: SKIPPED with "
            "`VERSION-MISMATCH` unless the main handshake selected 2."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:112-127; "
            "schema/v2/schema.unstable.json#/$defs/ErrorCode"
        ),
    ),
    Requirement(
        id="ACP-INIT-206",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A missing, non-integer (`\"2\"`, `null`), or out-of-range (`-1`, `65536`) "
            "`protocolVersion` is answered with `-32602` -- never a result, and not `-32022`. "
            "Binds agents implementing v2: SKIPPED with `VERSION-MISMATCH` unless the main "
            "handshake selected 2."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:108; "
            "schema/v2/schema.unstable.json#/$defs/ProtocolVersion"
        ),
    ),
    Requirement(
        id="ACP-INIT-207",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "After rejecting `initialize` with `-32022`, the agent does not begin "
            "version-specific operations on that connection: a following `session/new` does "
            "not succeed, and the agent sends no `session/*` or `elicitation/*` message. "
            "SKIPPED when no `-32022` is observed, and with `VERSION-MISMATCH` unless the main "
            "handshake selected 2."
        ),
        citation=_cite("docs/protocol/v2/draft/initialization.mdx:129"),
    ),
    Requirement(
        id="ACP-INIT-208",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A successful response uses the selected version's response shape: when the v1 "
            "request selects 1, the result has no v2-only root `info` or `capabilities` key. "
            "SKIPPED when the agent does not select 1."
        ),
        citation=_cite("docs/protocol/v2/draft/initialization.mdx:110"),
    ),
    Requirement(
        id="ACP-ERROR-005",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A request other than `initialize` that arrives before initialization completes is "
            "rejected with `-32600`: on a fresh connection, and after an `initialize` that "
            "failed (`protocolVersion` omitted, or `protocolVersion: 0` rejected with "
            "`-32022`). The probe is `session/new`; no reply FAILs. The \"ignore "
            "notifications\" half is not checked (the expected behaviour is silence, which "
            "`ACP-JSONRPC-003` already covers). Binds agents implementing v2: SKIPPED with "
            "`VERSION-MISMATCH` unless the main handshake selected 2."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:29,60; "
            "docs/protocol/v2/draft/initialization.mdx:90"
        ),
    ),
    Requirement(
        id="ACP-INIT-210",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "While the connection is uninitialized the agent sends no JSON-RPC request or "
            "notification: not at startup before `initialize`, not before the first successful "
            "`initialize` response, and not after an `initialize` that failed (`protocolVersion` "
            "omitted, or `protocolVersion: 0` rejected with `-32022`). Binds agents "
            "implementing v2: SKIPPED with `VERSION-MISMATCH` unless the main handshake "
            "selected 2."
        ),
        citation=_cite("docs/protocol/v2/draft/initialization.mdx:88,91"),
    ),
    Requirement(
        id="ACP-INIT-211",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "After an `initialize` that failed with `-32602` (`protocolVersion` omitted), a "
            "corrected `initialize` on the same connection succeeds, and the connection is "
            "then initialized (a following unknown `_tck/...` request is not answered with "
            "`-32600`; no reply to it is no evidence, `ACP-EXT-001` judges that). A retry after `-32022` is deliberately not exercised: that error asks "
            "the client to close the connection. Binds agents implementing v2: SKIPPED with "
            "`VERSION-MISMATCH` unless the main handshake selected 2."
        ),
        citation=_cite("docs/protocol/v2/draft/initialization.mdx:92"),
    ),
    Requirement(
        id="ACP-INIT-212",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "`initialize` repeated before any other request is handled like the first: "
            "two repeats after a successful `initialize(2)` each get a result selecting 2. A "
            "repeat that fails (`protocolVersion` omitted) leaves the previous initialization "
            "in effect: a following unknown `_tck/...` request is not answered with `-32600` "
            "(no reply to it is no evidence, `ACP-EXT-001` judges that). Binds agents implementing v2: SKIPPED with `VERSION-MISMATCH` unless the main "
            "handshake selected 2."
        ),
        citation=_cite("docs/protocol/v2/draft/initialization.mdx:139"),
    ),
    Requirement(
        id="ACP-INIT-213",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "An `initialize` repeated after another request is rejected with an error, not "
            "answered with a result. The request in between is an unknown `_tck/...` method: "
            "any request closes the repeat window. The exact code is `ACP-INIT-215`'s concern. "
            "Binds agents implementing v2: SKIPPED with `VERSION-MISMATCH` unless the main "
            "handshake selected 2."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:29,60; "
            "docs/protocol/v2/draft/initialization.mdx:139"
        ),
    ),
    Requirement(
        id="ACP-INIT-215",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The error that rejects an `initialize` repeated after another request is "
            "`-32600`. SKIPPED when the repeat is not answered with an error (that is "
            "`ACP-INIT-213`'s FAIL). Binds agents implementing v2: SKIPPED with "
            "`VERSION-MISMATCH` unless the main handshake selected 2."
        ),
        citation=_cite("docs/protocol/v2/draft/error.mdx:29,60"),
    ),
    Requirement(
        id="ACP-INIT-214",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "An `initialize` requesting a version above the agent's highest "
            "(`protocolVersion: 65535`) whose `capabilities` cannot be parsed (a non-object, "
            "`42`) is not rejected: the agent ignores the unparseable parameter and answers "
            "with a result. Which version it selects is `ACP-INIT-003`'s concern. Binds agents "
            "implementing v2: SKIPPED with `VERSION-MISMATCH` unless the main handshake "
            "selected 2."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:131; "
            "schema/v2/schema.unstable.json#/$defs/InitializeRequest/properties/capabilities"
        ),
    ),
    Requirement(
        id="ACP-INIT-004",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The `initialize` result's `info` is present and is an object with string `name` "
            "and `version` (`title` optional, may be `null`) -- REQUIRED in v2, "
            "unlike v1's optional `agentInfo`. A v2-only shape requirement: SKIPPED with a "
            "`VERSION-MISMATCH` note whenever the agent honestly negotiated down to a version "
            "other than 2, since it never claimed its result was v2-shaped."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/InitializeResponse/properties/info; "
            "schema/v2/schema.unstable.json#/$defs/InitializeResponse/required; "
            "schema/v2/schema.unstable.json#/$defs/Implementation; "
            "docs/protocol/v2/draft/initialization.mdx:360"
        ),
    ),
    Requirement(
        id="ACP-INIT-204",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "When the `initialize` result's `capabilities` is present, it is an object, and "
            "every object-typed capability marker within it (derived from the schema, at any "
            "depth; non-object fields are not judged) is either "
            "absent/`null` or an object -- never a boolean. A v2-only shape requirement: SKIPPED "
            "with a `VERSION-MISMATCH` note whenever the agent honestly negotiated down to a "
            "version other than 2. A dedicated diagnostic id for report legibility, kept as its "
            "own row even though the same defect also trips `ACP-SCHEMA-001`'s general schema "
            "validation."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AgentCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/SessionCapabilities -- all `type: \"object\"`"
        ),
    ),
    Requirement(
        id="ACP-SCHEMA-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Every message the agent emits during the `initialize` exchange validates against "
            "the vendored v2 schema. A v2-only shape requirement: SKIPPED with a "
            "`VERSION-MISMATCH` note whenever the agent honestly negotiated down to a version "
            "other than 2, since a v1-shaped result cannot be judged against the v2 schema."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/anyOf; docs/protocol/v2/draft/initialization.mdx"
        ),
    ),
    Requirement(
        id="ACP-SESSION-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/new` with an absolute `cwd` and no `mcpServers` succeeds with a "
            "non-empty string `sessionId`, and the response validates against the v2 schema."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:84; "
            "schema/v2/schema.unstable.json#/$defs/NewSessionRequest/required (`cwd`); "
            "schema/v2/schema.unstable.json#/$defs/NewSessionResponse/required (`sessionId`)"
        ),
    ),
    Requirement(
        id="ACP-SESSION-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text="Two `session/new` calls on one connection return distinct `sessionId`s.",
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:84,511; "
            "schema/v2/schema.unstable.json#/$defs/SessionId"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every `session/update` notification the agent emits during a `session/prompt` "
            "turn validates against the v2 schema and carries the prompted `sessionId`, or that "
            "of a child session already announced (in wire order) by a `subagent_update` on a "
            "known session -- child traffic before its announcement FAILs. "
            "Vacuous pass if the agent emits no updates during the turn."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/UpdateSessionNotification/required; "
            "schema/v2/schema.unstable.json#/$defs/SessionUpdate; "
            "schema/v2/schema.unstable.json#/$defs/SubagentUpdate"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-001",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "The announcing `subagent_update` precedes every live request or notification on "
            "the connection that carries a child session's ID: a `session/update` for the child "
            "(inside a prompt turn or outside it, including after the turn ends), an "
            "agent -> client request such as `session/request_permission` or "
            "`elicitation/create` with the child's `sessionId`, and a `session_message` naming "
            "the child as `senderSessionId` or `recipientSessionId`. The announcement must itself "
            "be sent on a known session (nested children included); traffic for an unannounced "
            "child FAILs. Stated by the schema's `SubagentUpdate` and the Subagents RFD (Active "
            "RFD). Judged in wire order over one `session/new`, one prompt turn and a quiet "
            "period after it (`session/resume` replay is `ACP-RESUME-209`'s). Subagents have no "
            "`initialize` marker, so support is inferred from the traffic "
            "(`capability=\"inferred:subagents\"` is documentation-only); SKIPs when no "
            "session ID the client did not create appears on the connection."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/SubagentUpdate; "
            "docs/rfds/subagents.mdx:95-99,189-193 (Active RFD)"
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
            "`tool_call_update` `content` array, a `tool_call_content_chunk`'s `content`, and a "
            "`session/request_permission` request's `subject.toolCall.content` (a `tool_call` "
            "subject; a `command` subject carries only a tool call ID), in wire order over one "
            "`session/new`, one prompt turn and a quiet period after it. A reference to a "
            "session no announcement preceded FAILs. A reference does not count as traffic "
            "carrying the child's ID, so it never FAILs `ACP-SUBAGENT-001`. The draft docs state "
            "the MUST, but only an agent that emits `session` content is bound and no "
            "`initialize` marker announces that, so the row is gated by `inferred:subagents` "
            "(documentation-only) and SKIPs when no `session` content item appears."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:740-742; "
            "docs/rfds/subagents.mdx:636-638 (Active RFD)"
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
            "`inferred:subagents` (documentation-only, no `initialize` marker). Judged for every "
            "`subagent_update` over one `session/new`, one prompt turn and a quiet period after "
            "it; SKIPs when none appears. A self-referencing update is judged here and by no "
            "other association row (`ACP-SUBAGENT-004`/`-005` leave it out), so one defect never "
            "FAILs several."
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
            "`ACP-SUBAGENT-003`'s. Judged for every `subagent_update` over one `session/new`, one "
            "prompt turn and a quiet period after it; SKIPs when none appears. Announcing a "
            "client session under one of its own descendants is the cycle case of this row."
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
            "ownership rule and the RFD states the one-parent, no-cycle rule; there is no "
            "`initialize` marker and the rule binds only an agent that emits `subagent_update`, "
            "so the row is CAPABILITY and gated by `inferred:subagents`. The remaining ways to "
            "close a cycle are `ACP-SUBAGENT-003` (a self-parent) and `-004` (a client session "
            "announced as a child), so a cycle never FAILs more than one row. Judged for every "
            "`subagent_update` sent on a known session over one `session/new`, one prompt turn and "
            "a quiet period after it; SKIPs when none appears."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/schema.mdx:10189-10193; "
            "docs/rfds/subagents.mdx:165-169 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-006",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "`SubagentUpdate.cwd` and every `additionalDirectories` entry is an `AbsolutePath`: "
            "POSIX `/...`, a Windows drive path or a UNC path (native syntax of the agent's "
            "machine, not a URI). `null` clears the field and an omitted field is unchanged, so "
            "neither is judged. The vendored schema defines `AbsolutePath` as a bare `string`, so "
            "`ACP-PROMPT-002`'s schema validation accepts a relative path and this row is the "
            "only check for it; a value of the wrong type (a non-string `cwd`, a non-array "
            "`additionalDirectories`, a non-string entry) is a schema defect, "
            "`ACP-PROMPT-002`'s, and is not judged here. The draft docs state the rule; only an "
            "agent that emits `subagent_update` is bound and no `initialize` marker announces it, "
            "so the row is CAPABILITY and gated by `inferred:subagents`. Judged for every `subagent_update` over one `session/new`, "
            "one prompt turn and a quiet period after it; SKIPs when none carries a string `cwd` or "
            "`additionalDirectories` entry."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/schema.mdx:10238,10254; "
            "schema/v2/schema.unstable.json#/$defs/SubagentUpdate/properties/cwd; "
            "schema/v2/schema.unstable.json#/$defs/SubagentUpdate/properties/additionalDirectories; "
            "schema/v2/schema.unstable.json#/$defs/AbsolutePath; "
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
            "`inferred:subagents` (documentation-only, no `initialize` marker). Judged for every "
            "`session_message` over one `session/new`, one prompt turn and a quiet period after "
            "it; SKIPs when no message has both participants known."
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
            "by `inferred:subagents`. Judged for every `session_message` over one `session/new`, "
            "one prompt turn and a quiet period after it; SKIPs when no message has both participants "
            "known. A participant that was never announced is `ACP-SUBAGENT-001`'s."
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
            "`messageId`. Conflicting references FAIL, including when the referenced view's own "
            "sender or recipient is a third session. A reference to a view the agent never "
            "reported, or to a view with no reference of its own, is not judged (each side is "
            "reported only when observed, and the draft docs add that views are not linked by "
            "equal IDs alone). The draft docs define what each field names; the RFD alone states "
            "the MUST that both references agree, so the row is capped at CAPABILITY and gated by "
            "`inferred:subagents`. Judged on the stored state after every `session_message` of "
            "one `session/new`, one prompt turn and a quiet period after it; SKIPs when no two views "
            "were found that both carry a reference, so no link was judged. "
            "`session_message_chunk` carries no identity, so is not judged."
        ),
        citation=_cite(
            "docs/rfds/subagents.mdx:466-475 (Active RFD); "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:128-132; "
            "docs/protocol/v2/draft/schema.mdx:8237,8251"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-011",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The task a parent gives a child is not reported as a `user_message` or "
            "`user_message_chunk` in the child's transcript (SHOULD NOT): none appears for an "
            "announced child before that child's first agent output (`agent_message`, "
            "`agent_thought` or a chunk of either), which is when the first task has started its "
            "work. The Client cannot prompt a child, so such a message would attribute the task "
            "to the user. Judged over one `session/new`, one prompt turn and a quiet period "
            "after it; SKIPs itself when no announced child produces agent output and none has a "
            "user message."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:137-142; "
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
            "first agent output (SHOULD): the child's `agent_message`, `agent_thought` or a "
            "chunk of either is preceded by such an upsert (the sender is stored across upserts "
            "of the `messageId`; the parent is the session that announced the child). A child "
            "whose task was reported as a `user_message` is `ACP-SUBAGENT-011`'s FAIL, so is not "
            "judged here. Judged over one `session/new`, one prompt turn and a quiet period "
            "after it; SKIPs itself when no announced child that was not told its task as a "
            "`user_message` produces agent output."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:137-142; "
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
            "never names a participant, or has one before its first chunk, is not flagged. "
            "The draft docs state it without an RFC keyword (\"Include them ... when "
            "available\") and the Active RFD as a SHOULD; either way it is not a MUST. Judged "
            "over one `session/new`, one prompt turn and a quiet period after it; SKIPs itself "
            "when no `session_message_chunk` appears."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:77-81; "
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
            "Judged over one `session/new`, one prompt turn and a quiet period after it; SKIPS "
            "itself when no `config_option_update` for an announced child carries a select."
        ),
        citation=_cite("docs/rfds/subagents.mdx:392-419 (Active RFD)"),
    ),
    Requirement(
        id="ACP-SUBAGENT-201",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Every state a child reports in its own `state_update` is mirrored on the immediate "
            "parent (the session that announced it) as the `state` of a `subagent_update` for "
            "that child (SHOULD). For each child announced on a known session, the distinct "
            "consecutive states of its own `state_update`s appear, in order, among the states "
            "of its `subagent_update` mirrors; a mirror may arrive before or after the copy on "
            "the child's stream, a repeated snapshot needs no second mirror, and only `state` "
            "is compared. Judged over one `session/new`, one prompt turn and a quiet period "
            "after it; SKIPs itself when no announced child reports a `state_update` (an agent "
            "that exposes no subagent, or none that reports state). ADVISORY rows carry no "
            "`capability`, so the SKIP is the test's own. v2-only (`2xx`): v1 has no "
            "child-addressed `state_update` stream and reports a child's work state through the "
            "association alone (`subagent_update.state`), so there is nothing to mirror."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1015-1018; "
            "schema/v2/schema.unstable.json#/$defs/SubagentUpdate; "
            "docs/rfds/subagents.mdx:765-774 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-016",
        tier=Tier.CAPABILITY,
        capability="inferred:subagentCancel",
        text=(
            "A child whose `subagent_update` capabilities carry a `cancel` object may be cancelled "
            "with `session/cancel` for the child's `sessionId`, and confirms it: the child "
            "reports `idle` with `stopReason: \"cancelled\"` in a `state_update` on its own "
            "session, or in its mirror on the parent association (`subagent_update.state`). The "
            "per-child capability is stated by the draft docs and schema (`SubagentSessionCapabilities`: "
            "`cancel` `Permits the client to cancel this child's current work`); the confirmation "
            "is stated only by the Subagents RFD (Active RFD), and no `initialize` marker "
            "announces it, so the row is CAPABILITY, gated by `inferred:subagentCancel` "
            "(documentation-only). The TCK sends the request only to a child that advertises "
            "`cancel` and was last reported running (the client MUST NOT cancel one that does "
            "not), in the driven turn of the cancel prompt, and gives the child `timeout / 2` to "
            "confirm. A child that reports an idle that is not a cancellation had ended first: a "
            "cancellation racing with already-ended work does not rewrite its outcome, so that "
            "SKIPs. SKIPs when no child advertised `cancel` while reported running. Shared id "
            "with v1 (which confirms through the parent snapshot alone)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/schema.mdx:10178; "
            "schema/v2/schema.unstable.json#/$defs/SubagentSessionCapabilities/properties/cancel; "
            "docs/rfds/subagents.mdx:1069-1073,1089-1095 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SUBAGENT-017",
        tier=Tier.CAPABILITY,
        capability="inferred:subagentCancel",
        text=(
            "`session/cancel` for a child cancels current work in that child, not its parent or "
            "its siblings: after the TCK cancels a running child that advertises `cancel`, "
            "neither the parent nor another child (other than the cancelled child's own "
            "descendants, which the cascade may stop) reports `idle` with `stopReason: "
            "\"cancelled\"` before the TCK itself cancels the parent. Stated only by the "
            "Subagents RFD (Active RFD: `This cancels current work in that child, not its parent "
            "or siblings`), so the row is CAPABILITY, gated by `inferred:subagentCancel` "
            "(documentation-only). Judged over the same driven turn as `ACP-SUBAGENT-016`, which "
            "owns the child's own confirmation, so one defect never FAILs both; a window of "
            "`quiet_period` after the child settles catches the parent's or a sibling's reaction. "
            "SKIPs when no child was cancelled or it had ended first. Shared id with v1."
        ),
        citation=_cite("docs/rfds/subagents.mdx:1069-1073 (Active RFD)"),
    ),
    Requirement(
        id="ACP-SUBAGENT-202",
        tier=Tier.CAPABILITY,
        capability="inferred:subagents",
        text=(
            "Cancelling a session's current work also cancels the descendant work it waits on, "
            "and the Client learns that from the descendants' reported state: after the TCK "
            "sends `session/cancel` for the parent and its turn ends `cancelled`, every "
            "descendant that was running at that moment and is foreground work (not in its "
            "parent's latest `background` list) reaches `idle`. A descendant in the list, or "
            "one whose parent never reported a `background` list (the TCK cannot tell which "
            "children the parent waits on), is not judged: whether other descendants keep "
            "running is the Agent's choice. An omitted per-child `cancel` capability does not "
            "waive the cascade. The draft docs state that `session/cancel` covers foreground "
            "work and that foreground work is not listed in `background`; that a child the "
            "cancelled work waits on stops is stated by the Subagents RFD (Active RFD), so the "
            "row is CAPABILITY, gated by `inferred:subagents` (documentation-only). Each "
            "descendant gets `timeout / 2` after the parent's turn ends. SKIPs when the parent's "
            "turn did not end `cancelled` (the cancel raced with its end, or `ACP-CANCEL-*` own "
            "that turn), or no such descendant was running. v2-only (`2xx`): v1 has no "
            "`background` list, so the TCK cannot tell which running children the parent waits "
            "on."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:208,210,1173; "
            "docs/rfds/subagents.mdx:1075-1087,1413-1425 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "The `session/prompt` result is a non-error object carrying a non-empty string "
            "`messageId` -- the acceptance receipt sent at insertion time, not a turn result "
            "(there is no `stopReason` here at all in v2). Non-empty is a TCK strengthening: "
            "`MessageId` is a plain string."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:323-325,341-344; "
            "schema/v2/schema.unstable.json#/$defs/PromptResponse/required; "
            "schema/v2/schema.unstable.json#/$defs/MessageId"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "The agent reports the inserted user message via a `user_message` update or at "
            "least one `user_message_chunk` update, carrying the same `messageId` as the "
            "`session/prompt` response, for the prompted session -- before or after the "
            "response, no later than the turn-ending idle."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:346,803; "
            "schema/v2/schema.unstable.json#/$defs/UserMessage; "
            "schema/v2/schema.unstable.json#/$defs/ContentChunk"
        ),
    ),
    Requirement(
        id="ACP-STATE-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "The agent reports `running` or `requires_action` for the prompted session before "
            "the idle that ends the turn. FAILs when the turn could only be ended by a "
            "stopReason-bearing idle with no active state before it (confirmed after a quiet "
            "period); SKIPPED when the prompt was rejected with no foreground work."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:152,394-397,1073,1080-1082,1121-1126; "
            "schema/v2/schema.unstable.json#/$defs/StateUpdate"
        ),
    ),
    Requirement(
        id="ACP-STATE-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Once the prompted session reported `running` or `requires_action`, an idle "
            "`state_update` for it arrives within the turn's timeout budget -- also when the "
            "prompt was rejected after foreground work had started. SKIPPED as 'no foreground "
            "work observed' when no active state was seen."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:154,390,786,1076,1114,1121-1124"
        ),
    ),
    Requirement(
        id="ACP-STATE-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "If the idle that ends the turn carries a non-null `stopReason`, its value is one "
            "of the six defined constants (`end_turn`, `max_tokens`, `max_turn_requests`, "
            "`refusal`, `cancelled`, `error`) or begins with `_`. A missing or `null` "
            "stopReason is SKIPPED here (it is only SHOULD; see `ACP-STATE-204`)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:786,805,936,965; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/properties/stopReason; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/anyOf/6; "
            "docs/protocol/v2/draft/extensibility.mdx:235-240"
        ),
    ),
    Requirement(
        id="ACP-STATE-204",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The idle that ends the turn carries a non-null `stopReason` (SHOULD; an agent that "
            "cannot determine why work stopped may omit it). The test is gated on "
            "`capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:154,786,936,1092; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate"
        ),
    ),
    Requirement(
        id="ACP-STATE-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "After `requires_action` for the prompted session, the agent reports `running` "
            "before progress resumes, or `idle` if the work ends without resuming: no "
            "`agent_message`/`agent_message_chunk`/`agent_thought`/`agent_thought_chunk` "
            "update for the session arrives before the next `running` or `idle` for it. "
            "Tool-call updates are not judged (background activity may continue while blocked). "
            "SKIPPED when `requires_action` is never observed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:153,845,1075,1104-1105; "
            "schema/v2/schema.unstable.json#/$defs/RequiresActionStateUpdate"
        ),
    ),
    Requirement(
        id="ACP-STATE-206",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Once a `state_update` for the session carries a `background` array (`[]` counts), "
            "every later `running`/`requires_action`/`idle`/`unknown` `state_update` for that "
            "session on the connection carries an array too, not an omitted or `null` one. "
            "Judged over one prompt turn plus a quiet drain after it; custom states are not "
            "judged. SKIPPED when no background list is reported."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:188,203-204; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/properties/background; "
            "schema/v2/schema.unstable.json#/$defs/RunningStateUpdate/properties/background"
        ),
    ),
    Requirement(
        id="ACP-STATE-207",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every `terminal`/`tool_call`/`subagent` item in a session's `background` list was "
            "announced earlier on the connection, for the same session, by a `terminal_update` "
            "with its `terminalId`, a `tool_call_update` with its `toolCallId`, or a "
            "`subagent_update` with its `sessionId`. Items of other types are not judged. "
            "SKIPPED when no such item is listed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:206,209; "
            "schema/v2/schema.unstable.json#/$defs/BackgroundWork"
        ),
    ),
    Requirement(
        id="ACP-STATE-208",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "When an `idle` `state_update` drops a `terminal`/`tool_call` item from the "
            "session's previous `background` list, a `terminal_update` with a non-null "
            "`exitStatus` or a `tool_call_update` with status `completed`/`failed`/`cancelled` "
            "for it arrived earlier. Removals in a `running`/`requires_action`/`unknown` "
            "snapshot are not judged (foreground work that waits on an item takes it off the "
            "list unfinished), nor are subagent removals. SKIPPED when no idle snapshot "
            "removes such an item."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:206,208; "
            "schema/v2/schema.unstable.json#/$defs/ToolCallStatus; "
            "schema/v2/schema.unstable.json#/$defs/TerminalUpdate/properties/exitStatus"
        ),
    ),
    Requirement(
        id="ACP-STATE-209",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When a `terminal`/`tool_call` item in the session's latest `background` list "
            "reaches its final status (a `terminal_update` with a non-null `exitStatus`, or a "
            "`tool_call_update` with status `completed`/`failed`/`cancelled`) while the "
            "session is `idle`, a later `state_update` for the session drops it from the list: "
            "the Agent SHOULD re-send the state with the updated list when background work "
            "ends. Judged over one prompt turn plus a quiet drain after it. The start of "
            "background work is not judged (an announced item that no list names yet cannot be "
            "told from foreground work), nor is an end during active work (the next snapshot "
            "follows anyway). SKIPPED when no listed item ends while idle. The test is gated "
            "on `capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:205-206; "
            "docs/rfds/v2/background-work.mdx:193-194 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A prompt of `text` + `resource_link` content blocks is accepted (a non-error "
            "`session/prompt` result), and the turn ends: agents advertising `session` MUST "
            "support both block types, and `content.mdx` states the `resource_link` MUST for all "
            "agents. Gated on `session` (v1 has it MANDATORY) because without it there is no "
            "`session/prompt`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:308; "
            "docs/protocol/v2/draft/content.mdx:178; "
            "schema/v2/schema.unstable.json#/$defs/PromptRequest/properties/prompt; "
            "schema/v2/schema.unstable.json#/$defs/ResourceLink"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-207",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "If `session/prompt` is answered with a JSON-RPC error, no `user_message`/"
            "`user_message_chunk` update was emitted for that submission: a prompt rejected "
            "before insertion emits no user-message update, and an inserted one must not get an "
            "error. Checked on an ordinary and on a cancelled turn; SKIPPED when the prompt "
            "succeeded."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:325,346,388; "
            "docs/protocol/v2/draft/cancellation.mdx:59"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-209",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A `session/prompt` sent while the session's foreground work is active (on the "
            "first `running`/`requires_action` of a cancel-prompt turn) is not rejected: until "
            "the TCK's `session/cancel` it is either answered with a success (inserted right "
            "away) or left pending (held). An error before the cancel FAILs, `-32800` included, "
            "since nothing asked for cancellation. SKIPPED when the first prompt's work may "
            "have ended before the agent read the second prompt."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:382,384; "
            "docs/rfds/v2/prompt.mdx:88 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-PROMPT-211",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A `session/prompt` whose `prompt` contains a content block of a type the agent "
            "cannot understand (a `_tck_unknown` probe type, not baseline and not advertised) is "
            "answered with a JSON-RPC error with code `-32602`, and the prompt is not inserted: "
            "no `user_message`/`user_message_chunk` update and no `running`/`requires_action` "
            "state follows for it within a short quiet period. A client never sends such a "
            "block; the probe breaks that rule on purpose because the spec defines the agent's "
            "answer."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:313,388; "
            "docs/protocol/v2/draft/content.mdx:22; "
            "docs/protocol/v2/draft/extensibility.mdx:62-65; "
            "schema/v2/schema.unstable.json#/$defs/ContentBlock"
        ),
    ),
    Requirement(
        id="ACP-PROMPTCAP-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.prompt.image",
        text=(
            "A prompt containing an `image` content block alongside text is accepted (a "
            "non-error `session/prompt` result), and the turn reaches idle, when the agent "
            "advertises `capabilities.session.prompt.image`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:306-331; "
            "docs/protocol/v2/draft/content.mdx:62-64; "
            "schema/v2/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/ImageContent"
        ),
    ),
    Requirement(
        id="ACP-PROMPTCAP-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.prompt.audio",
        text=(
            "A prompt containing an `audio` content block alongside text is accepted (a "
            "non-error `session/prompt` result), and the turn reaches idle, when the agent "
            "advertises `capabilities.session.prompt.audio`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:306-331; "
            "docs/protocol/v2/draft/content.mdx:95-97; "
            "schema/v2/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/AudioContent"
        ),
    ),
    Requirement(
        id="ACP-PROMPTCAP-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.prompt.embeddedContext",
        text=(
            "A prompt containing a `resource` (embedded context) content block alongside text "
            "is accepted (a non-error `session/prompt` result), and the turn reaches idle, "
            "when the agent advertises `capabilities.session.prompt.embeddedContext`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:306-331; "
            "docs/protocol/v2/draft/content.mdx:131-133; "
            "schema/v2/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/EmbeddedResource"
        ),
    ),
    Requirement(
        id="ACP-PROMPTCAP-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "For each of `image`, `audio` and `resource` (embedded context) that the agent does "
            "NOT advertise under `capabilities.session.prompt`, a well-formed prompt containing "
            "that block type alongside text is answered with a JSON-RPC error with code "
            "`-32602`, and the prompt is not inserted (no user-message update and no active "
            "state follows within a short quiet period). A runtime negative gate: the "
            "registry capability only says the agent offers sessions; each block type is judged only "
            "when its own prompt capability is not an object, and SKIPPED when advertised (that "
            "positive case is `ACP-PROMPTCAP-001..003`); a `true` value deserializes as not "
            "advertised, so it is probed. A client never sends an unadvertised "
            "block; the probe breaks that rule on purpose because the spec defines the agent's "
            "answer."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:313,388; "
            "docs/protocol/v2/draft/content.mdx:22,62-64,95-97,131-133; "
            "docs/protocol/v2/draft/initialization.mdx:306-331; "
            "schema/v2/schema.unstable.json#/$defs/PromptCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/ContentBlock"
        ),
    ),
    Requirement(
        id="ACP-PERM-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Any `session/request_permission` request the agent sends during a turn "
            "validates against the v2 schema: `sessionId`, `title`, and an `options` array of "
            "at least one option, each carrying `optionId`/`name`/`kind`. Once the client "
            "answers with a `selected` outcome, the turn still reaches an idle. Vacuous "
            "(SKIPPED) when no permission request was observed during the turn -- sending one "
            "is only MAY."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/RequestPermissionRequest/required; "
            "schema/v2/schema.unstable.json#/$defs/RequestPermissionRequest/properties/options (minItems: 1); "
            "schema/v2/schema.unstable.json#/$defs/PermissionOption/required; "
            "docs/protocol/v2/draft/tool-calls.mdx:209,244-278,356-374"
        ),
    ),
    Requirement(
        id="ACP-PERM-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "In every `session/request_permission` the agent sends during a turn, the "
            "`options[].optionId` values are pairwise distinct, and a `subject` with `type: "
            "\"command\"` carries an absolute `cwd`. Both are schema-valid when broken "
            "(`AbsolutePath` is a plain string). SKIPPED when no permission request is observed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:302-303,357; "
            "schema/v2/schema.unstable.json#/$defs/PermissionOption/properties/optionId; "
            "schema/v2/schema.unstable.json#/$defs/CommandPermissionSubject"
        ),
    ),
    Requirement(
        id="ACP-PERM-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "After the client declines a `session/request_permission` whose `subject` is a "
            "`tool_call` X by policy with the `cancelled` outcome (no `session/cancel`), the "
            "agent never reports X `completed` later in the turn, on a `tool_call_update` or a "
            "later subject. Which stop reason the turn ends with is not judged. SKIPPED when no "
            "permission request with a `tool_call` subject is observed."
        ),
        citation=_cite("docs/protocol/v2/draft/tool-calls.mdx:340,423"),
    ),
    Requirement(
        id="ACP-PERM-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "After the client answers a `session/request_permission` whose `subject` is a "
            "`tool_call` X with a `selected` outcome naming an `optionId` the agent never "
            "offered, the agent treats the request as not approved: it never reports X "
            "`completed` later in the turn. SKIPPED when no permission request with a "
            "`tool_call` subject is observed. The probe answer breaks the client rule on "
            "purpose, because the spec defines the agent's answer."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:346-347,423; "
            "schema/v2/schema.unstable.json#/$defs/SelectedPermissionOutcome"
        ),
    ),
    Requirement(
        id="ACP-PERM-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "After the client answers a `session/request_permission` whose `subject` is a "
            "`tool_call` X with a `_`-prefixed custom outcome (`_tck_unknown`) the agent does "
            "not understand, the agent does not treat it as approval: it never reports X "
            "`completed` later in the turn. SKIPPED when no permission request with a "
            "`tool_call` subject is observed. The probe is a legal client answer: the outcome "
            "is an open enum. `ACP-ENUM-203` judges only that the agent survives such a value."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:348-349,423; "
            "schema/v2/schema.unstable.json#/$defs/RequestPermissionOutcome/anyOf/2"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "With a mock client advertising no `capabilities.elicitation.*` mode, no "
            "`elicitation/create` request is observed during a prompt turn."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/elicitation.mdx:56-57,59; "
            "schema/v2/schema.unstable.json#/$defs/CreateElicitationRequest (x-method: elicitation/create)"
        ),
    ),
    Requirement(
        id="ACP-CLIENTCAP-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every agent->client request/notification method observed during a prompt turn "
            "is a member of `CLIENT_METHODS` or `PROTOCOL_METHODS` (e.g. `$/cancel_request`), "
            "or begins with `_`. `fs/*`/`terminal/*` do not exist as v2 methods at all, so "
            "calling either FAILs here as an undefined method (the v2 collapse of v1's "
            "separate `ACP-CLIENTCAP-001/002` rows)."
        ),
        citation=_cite(
            "schema/v2/meta.unstable.json:28-38 (agent->client method inventory); "
            "docs/protocol/v2/draft/extensibility.mdx:165,174 (only `_`-prefixed custom methods may be called)"
        ),
    ),
    Requirement(
        id="ACP-INFO-CONCURRENT-201",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Record (never assert) whether a `session/prompt` sent during active foreground "
            "work (the `ACP-PROMPT-209` scenario) is inserted right away or held until "
            "`session/cancel`, and how a held one is then answered. Which of the two an agent "
            "does, and whether inserting steers the current turn or starts the next, is up to "
            "the agent. SKIPPED when not exercised."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:382-384,1118-1119; "
            "docs/rfds/v2/prompt.mdx:88 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-INFO-BACKGROUND-201",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Record (never assert) which tool calls a `background` list names together with a "
            "terminal that they reference in `terminal` content and that the list also names. "
            "Process-backed work is listed as its terminal, and the Agent MUST NOT also list a "
            "tool call whose only live work is a listed terminal, but the client cannot tell "
            "whether the tool call has other live work. SKIPPED when no list is reported."
        ),
        citation=_cite("docs/protocol/v2/draft/prompt-lifecycle.mdx:208"),
    ),
    Requirement(
        id="ACP-INFO-BACKGROUND-202",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Record (never assert) what happens to the items of the latest `background` list "
            "when `session/cancel` is sent: which of them reach a final status before the "
            "cancelled turn's idle, and which the idle still lists. Work in the list is not "
            "covered by `session/cancel` and keeps running, but it may also end on its own, so "
            "an item finishing proves nothing. SKIPPED when the cancel did not land or no "
            "work was listed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1173; "
            "docs/protocol/v2/draft/tool-calls.mdx:268"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "After `session/cancel`, if foreground work was active when cancellation took "
            "effect, the agent sends a `session/update` whose `update` is `{\"sessionUpdate\": "
            "\"state_update\", \"state\": \"idle\", \"stopReason\": \"cancelled\"}`. A prompt "
            "cancelled before insertion (`-32800`) with no active state owes no idle."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1093,1185-1192,1199; "
            "docs/protocol/v2/draft/cancellation.mdx:41-44; "
            "docs/protocol/v2/draft/schema.mdx:603-607"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every update for the cancelled foreground work precedes its cancelled idle: "
            "within `quiet_period(...)` after that idle, no `agent_message*`/`agent_thought*` "
            "update for the session reuses a `messageId` (of the same entity type) seen during "
            "the cancelled turn. Repeated idle snapshots, `unknown`, and new work are allowed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:803,1084-1087,1203; "
            "docs/protocol/v2/draft/schema.mdx:615-617"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Cancellation is never surfaced as a generic failure: after `session/cancel`, an "
            "error response to `session/prompt` is conforming only as `-32800` for a prompt "
            "cancelled before insertion (no user-message update emitted for it); and the "
            "turn-ending idle does not carry a non-`cancelled` known stop reason such as "
            "`error` or `end_turn`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:325,388,1004,1173,1194-1201; "
            "docs/protocol/v2/draft/cancellation.mdx:59; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/anyOf/4 (`cancelled` branch description)"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-204",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "On receiving `session/cancel`, the agent SHOULD stop all language model requests "
            "and all tool call invocations of the cancelled foreground work as soon as "
            "possible. Unobservable "
            "from a client-only TCK -- nothing on the wire distinguishes 'stopped as soon as "
            "possible' from 'stopped eventually', so the test "
            "records the observation and always SKIPs, never asserting on timing. INFORMATIONAL, "
            "not ADVISORY: a row that can never be judged, only "
            "ever SKIPped, belongs in the record-only tier, not the SHOULD tier."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1179; "
            "docs/protocol/v2/draft/schema.mdx:595-597"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/cancel` is a notification: the agent MUST NOT send any JSON-RPC response "
            "(result or error) for it."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/ClientNotification/properties/params/anyOf/0/anyOf/0 (CancelSessionNotification sits under ClientNotification); "
            "schema/v2/schema.unstable.json#/$defs/CancelSessionNotification; "
            "docs/protocol/v2/draft/overview.mdx:13,151-153,227"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-206",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/cancel` params are exactly `{sessionId}` (required) plus optional `_meta`; "
            "the agent MUST accept a cancel that carries only `sessionId`, and MUST accept one "
            "that additionally carries `_meta`."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/CancelSessionNotification; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1163-1171"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-207",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A custom stop reason MUST begin with `_`; an unknown non-`_` stop reason is "
            "reserved for future ACP and is non-conformant today. Applied to the cancellation "
            "assertion itself: the agent may not substitute e.g. `aborted` for `cancelled`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:965; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/anyOf/6 (`other` branch description)"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-208",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/close` on a session with foreground work in flight MUST cancel that work "
            "as if `session/cancel` had been sent (same idle `cancelled` state_update), then "
            "free resources; a prompt the close kept from being inserted is answered `-32800`. "
            "Shares its test and citation with `ACP-CLOSE-002` (the same wire evidence, bound "
            "to both ids via a second `@pytest.mark.requirement(...)` marker) -- deliberately "
            "counted twice, once under each id."
        ),
        citation=_cite("docs/protocol/v2/draft/session-setup.mdx:389-395"),
    ),
    Requirement(
        id="ACP-CANCEL-209",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Cancelling a turn blocked on the agent's own pending `session/request_permission` "
            "for foreground work (not for an item in the latest `background` list; no "
            "`requires_action` needed) ends the work with an idle "
            "`stopReason: \"cancelled\"` without the client answering that request: the agent "
            "MUST stop waiting for it. The TCK leaves it unanswered and answers it `cancelled` "
            "only once the agent withdraws it with `$/cancel_request` (waiting for that answer "
            "is allowed) or the turn has ended. A turn that ends only after the TCK answers it "
            "at the deadline FAILs. SKIPPED when no foreground permission request was pending "
            "when cancel was sent."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:246-247,1153,1173,1177,1185-1189; "
            "docs/protocol/v2/draft/cancellation.mdx:20,31,40-43; "
            "docs/protocol/v2/draft/tool-calls.mdx:326; "
            "schema/v2/schema.unstable.json#/$defs/RequestPermissionOutcome; "
            "schema/v2/schema.unstable.json#/$defs/CancelledPermissionOutcome"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-006",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A `$/cancel_request` naming a request id the client never sent gets no response of "
            "any kind, and the agent keeps serving the connection: a following request is still "
            "answered."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/cancellation.mdx:24; "
            "schema/v2/schema.unstable.json#/$defs/CancelRequestNotification"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-211",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A `$/cancel_request` naming a request the agent already answered (the connection's "
            "own `initialize`) gets no response, in particular no second one for that id, and "
            "the agent keeps serving the connection."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/cancellation.mdx:22,24; "
            "schema/v2/schema.unstable.json#/$defs/CancelRequestNotification"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-007",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A `session/prompt` the client withdraws with `$/cancel_request` right after sending "
            "it still gets exactly one response: a success (inserted) or an error, and `-32800` "
            "only if no user-message update was emitted for it. Other error codes are recorded, "
            "not failed: an agent may decline to cancel and send its normal response. A prompt "
            "still unanswered after `--timeout` is also covered by a `session/cancel` the TCK "
            "then sends; one unanswered even after that FAILs."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/cancellation.mdx:20,22,24,26-29,59; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:325,384,388"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-213",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When `session/cancel` cancels work blocked on the agent's own pending "
            "`session/request_permission` (held unanswered, as in `ACP-CANCEL-209`), the agent "
            "withdraws that request with `$/cancel_request` naming its id, before or shortly "
            "after the cancelled idle. Same SKIPs as `ACP-CANCEL-209`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1177; "
            "docs/protocol/v2/draft/cancellation.mdx:40,63; "
            "schema/v2/schema.unstable.json#/$defs/CancelRequestNotification"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-214",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A `session/prompt` held (still unanswered) when `session/cancel` is sent is covered "
            "by the cancel: it is answered `-32800`, and no user-message update for a new "
            "message follows within `quiet_period(...)`. A held prompt left unanswered, or "
            "answered with another error, FAILs; so does a success arriving after the race "
            "window (inserted after the cancel). A success within it SKIPs (the agent may have "
            "inserted it just before reading the cancel), as does a prompt answered before the "
            "cancel. Uses the `ACP-PROMPT-209` scenario."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:384,1173; "
            "schema/v2/schema.unstable.json#/$defs/CancelSessionNotification"
        ),
    ),
    Requirement(
        id="ACP-INFO-CANCEL-201",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Record (never assert) the agent's behaviour on `session/cancel` for an active "
            "session with no foreground work (no completion update is required) and for a "
            "session that is not active, one closed on this connection and one never created "
            "(the agent ignores it). Nothing beyond `ACP-CANCEL-205`'s no-response rule is "
            "assertable."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1157,1191-1192; "
            "docs/protocol/v2/draft/cancellation.mdx:43-44; "
            "docs/protocol/v2/draft/session-setup.mdx:51"
        ),
    ),
    Requirement(
        id="ACP-TRANSPORT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Every line the agent writes to stdout parses as JSON and is a single JSON-RPC "
            "2.0 message object; a JSON array (empty or not) is non-conformant, since ACP "
            "does not use batches."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/transports.mdx:20,23,67; "
            "schema/v2/schema.unstable.json#/anyOf (Agent/Client/ProtocolLevel/Proxy envelopes, "
            "all `type: object`)"
        ),
    ),
    Requirement(
        id="ACP-TRANSPORT-002",
        tier=Tier.MANDATORY,
        capability=None,
        text="The agent's stdout is valid UTF-8.",
        citation=_cite("docs/protocol/v2/draft/transports.mdx:6"),
    ),
    Requirement(
        id="ACP-TRANSPORT-203",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Messages are newline-delimited and MUST NOT contain embedded newlines."
        ),
        citation=_cite("docs/protocol/v2/draft/transports.mdx:21"),
    ),
    Requirement(
        id="ACP-JSONRPC-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A response's `id` echoes the request `id` exactly (integer and string ids), "
            "whether it is a result or an error."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/overview.mdx:15-17,233 (JSON-RPC envelope fields, including `id`, follow the base JSON-RPC 2.0 spec, where id-echo is itself normative); "
            "schema/v2/schema.unstable.json#/$defs/AgentResponse (Result/Error, both required id)"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A response carries exactly one of `result`/`error`, and an `id` that is a string "
            "or an integer; only an error response may carry `id: null` (when the request id "
            "could not be determined). An error object has an integer `code` and a string "
            "`message`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/overview.mdx:15-17,225-226; "
            "docs/protocol/v2/draft/error.mdx:6-10; "
            "schema/v2/schema.unstable.json#/$defs/AgentResponse (disjoint Result/Error branches; "
            "only the Error branch's `id` allows null); "
            "schema/v2/schema.unstable.json#/$defs/RequestId"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-003",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Notifications never receive a response, success or error. Probed with `session/cancel` "
            "(no prompt in flight), or `_tck/notify` for an agent without `capabilities.session`, "
            "and with `mcp/message` notifications (the unstable MCP-over-ACP envelope, "
            "well-formed and malformed; the rule binds every agent, so the probe is not gated "
            "on `capabilities.session.mcp.acp`). The `mcp/message` probes break client rules "
            "on purpose: the envelope is sent only for an active request on a declared `acp` "
            "MCP server, to an agent that advertised `acp`, and `requestId` and `method` are "
            "required; the spec defines the agent's answer to exactly these inputs (no "
            "reply). An agent that exits instead of replying sent no reply (`ACP-EXT-002` "
            "judges a crash on `mcp/message`). Messages the agent "
            "itself initiates (they carry `method`) are not responses."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/overview.mdx:10,227; "
            "docs/rfds/mcp-over-acp.mdx:225,257 (Active RFD); "
            "schema/v2/schema.unstable.json#/$defs/MessageMcpNotification"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-004",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A request for a method the agent does not recognize -- probed with an unknown "
            "`_`-prefixed custom method -- is answered with `-32601` (Method not found). "
            "Replying at all is `ACP-EXT-001`'s concern; an agent that never replies SKIPs "
            "here rather than failing both rows."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:202-213; "
            "docs/protocol/v2/draft/error.mdx:44"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-202",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Every request the agent sends to the client has an `id` that is a string or an "
            "integer, never `null`, and the agent does not reuse an `id` while an earlier "
            "request with it is still awaiting the client's response. Passive: judged on "
            "the requests the agent sends during a prompt turn, and SKIPs when it sends none "
            "(or, for the reuse half, never has two requests pending at once)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/overview.mdx:15-19; "
            "schema/v2/schema.unstable.json#/$defs/RequestId; "
            "schema/v2/schema.unstable.json#/$defs/AgentRequest"
        ),
    ),
    Requirement(
        id="ACP-JSONRPC-005",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "After an erroneous request -- including a rejected JSON array -- the "
            "connection remains usable."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/overview.mdx:221-227; "
            "docs/protocol/v2/draft/extensibility.mdx:202-213"
        ),
    ),
    Requirement(
        id="ACP-BATCH-209",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Any JSON array the agent receives on stdin -- empty, request-only, "
            "notification-only, containing non-object elements, or mixing call- and "
            "response-shaped elements -- is rejected with exactly one Invalid Request "
            "(`-32600`) error object whose `id` is `null`; no element is processed (no "
            "response carries an element's `id`). ADVISORY: the receiver clause carries no "
            "RFC-2119 keyword (only the sender's does). An agent that answers with an array "
            "also fails `ACP-TRANSPORT-001` (MANDATORY)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/transports.mdx:65-67; "
            "docs/protocol/v2/draft/overview.mdx:21"
        ),
    ),
    Requirement(
        id="ACP-SESSION-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/new` is accepted whether `mcpServers` is omitted entirely or sent as `[]` "
            "-- the two forms are equivalent in v2 (unlike v1, where the field was required-"
            "even-if-empty)."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/NewSessionRequest/properties/mcpServers; "
            "schema/v2/schema.unstable.json#/$defs/NewSessionRequest/required"
        ),
    ),
    Requirement(
        id="ACP-SESSION-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/new` with a relative `cwd` is rejected with an error, not answered with a "
            "result (\"Agents reject a request with a relative `cwd`\"). The code is judged "
            "separately (`ACP-SESSION-209`). The probe breaks the client rule that `cwd` be "
            "absolute on purpose, because the spec defines the agent's answer to exactly that "
            "input."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:524; "
            "schema/v2/schema.unstable.json#/$defs/NewSessionRequest/properties/cwd"
        ),
    ),
    Requirement(
        id="ACP-SESSION-209",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The rejection of `session/new` with a relative `cwd` (`ACP-SESSION-204`'s probe) "
            "uses `-32602` (Invalid params). The sentence naming the code carries no RFC "
            "keyword (the MUST binds the client's path), so the code is ADVISORY while the "
            "rejection itself is not. SKIPs when the probe was not rejected "
            "(`ACP-SESSION-204`'s concern). An agent that accepts the relative `cwd` FAILs "
            "`ACP-SESSION-204` and is not judged here."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:524; docs/protocol/v2/draft/error.mdx:48"
        ),
    ),
    Requirement(
        id="ACP-SESSION-206",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Before its `session/new` response, the agent sends no session-scoped request "
            "(for example a permission request or an elicitation) naming the new session -- "
            "the client cannot yet show it for that session. SHOULD NOT. The test is gated on "
            "`capabilities.session`."
        ),
        citation=_cite("docs/protocol/v2/draft/session-setup.mdx:103"),
    ),
    Requirement(
        id="ACP-SESSION-207",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Before its `session/new` response, the agent sends no `config_option_update` or "
            "`available_commands_update` for the new session: initial state belongs in the "
            "response. SHOULD. `state_update` is explicitly allowed before the response and "
            "is not judged. The test is gated on `capabilities.session`."
        ),
        citation=_cite("docs/protocol/v2/draft/session-setup.mdx:98-99,103"),
    ),
    Requirement(
        id="ACP-SESSION-208",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "When the latest `config_option_update`/`available_commands_update` for the new "
            "session that arrives before the `session/new` response carries a non-empty list, "
            "the response carries the corresponding list (`configOptions`/`availableCommands`), "
            "non-empty: a setup response replaces the lists the client holds, so an agent whose "
            "session has options or commands MUST include them. The premise \"the session has "
            "them\" is inferred from that notification; a response arriving with no such "
            "notification before it is recorded, not judged (vacuous)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:108,136,138; "
            "schema/v2/schema.unstable.json#/$defs/NewSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-RESUME-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/resume` (no `replayFrom`) of a session obtained via the harness's "
            "three-route strategy (create, create-then-close, then a `session/list` entry created in "
            "the TCK's own `cwd`) succeeds with a schema-valid object result. `-32601` FAILs "
            "(`session/resume` is part of the baseline once `capabilities.session` is "
            "advertised); any other error from all three routes SKIPs -- no route is "
            "spec-guaranteed to work."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:144-145; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionRequest; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-RESUME-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "With `replayFrom: {\"type\": \"start\"}`, replayed conversation history arrives "
            "before the `session/resume` response: no replayed-history update (`user_message`/"
            "`agent_message`/`agent_thought` or their `_chunk` forms) for the resumed session "
            "arrives within a quiet period after it. Other kinds -- the current-state snapshot "
            "repeated, `available_commands_update`, `session_info_update`, "
            "`config_option_update`, `usage_update`, live `notice`s -- may legitimately follow "
            "and are not judged. Zero replayed updates is conforming (R5's retention escape "
            "hatch) and is recorded, never FAILed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:138,207-209,225-229,321-323,339-342; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:561-571,613-616,1044,1084-1087; "
            "docs/protocol/v2/draft/session-list.mdx:204-205"
        ),
    ),
    Requirement(
        id="ACP-RESUME-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "With `replayFrom` omitted (or `null`), no conversation-history `session/update` for "
            "the resumed session arrives before the response. Vacuous -- and recorded, never "
            "FAILed on that account -- for an agent that retains no history to replay. Live "
            "traffic for other (child) sessions is not judged (Active Subagents RFD)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:179-184 (the current-state snapshot is live sync, not history); "
            "docs/rfds/subagents.mdx:1008-1013 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-RESUME-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A retained user message inserted by `session/prompt` replays, if it replays at all, "
            "with the same `messageId` that prompt's response returned. Judged for the resumed "
            "session only: a child session's own `user_message` is not that message. A narrow, conditional "
            "trigger: absence of the message from replay is conforming (R5) and SKIPs this "
            "check rather than FAILing it."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:282-287; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:370; "
            "schema/v2/schema.unstable.json#/$defs/PromptResponse/properties/messageId"
        ),
    ),
    Requirement(
        id="ACP-RESUME-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "During replay, a `*_chunk` update for the resumed session and a `messageId` is "
            "preceded, within the same replay window, by a matching whole-message update for that id carrying a `content` "
            "array -- `[]` when chunks rebuild the message from its beginning, or full content "
            "the chunks then append to (a client cannot tell the two apart). Vacuous -- "
            "recorded, never FAILed -- for an agent whose replay uses only whole-message "
            "updates. Live traffic for other (child) sessions, which may accompany a replay, "
            "is not judged (Active Subagents RFD)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:299-312; "
            "docs/rfds/subagents.mdx:999-1006 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-RESUME-206",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every successful `session/resume` -- with `replayFrom` omitted or "
            "`{\"type\": \"start\"}` -- is preceded by a current-state `state_update` for the "
            "resumed session, sent after every replayed history update and before the response."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:36-37,321-323,339-344; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1055-1061; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-RESUME-207",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/resume` with a cursor type the agent does not support (the schema-valid "
            "custom `{\"type\": \"_tck_unsupported_cursor\"}`) is rejected with `-32602`. A "
            "success -- silently substituting another cursor or resuming without replay -- "
            "FAILs, as does any other error code."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:211-215; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionRequest/properties/replayFrom; "
            "schema/v2/schema.unstable.json#/$defs/ReplayFrom/anyOf/1"
        ),
    ),
    Requirement(
        id="ACP-RESUME-208",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/resume` with a malformed `replayFrom` (a bare `\"start\"` string, `{}`, "
            "or `{\"type\": 5}`) is rejected with `-32602`. `null` is not malformed -- it means "
            "omitted -- and is not probed here."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:214-215; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionRequest/properties/replayFrom"
        ),
    ),
    Requirement(
        id="ACP-RESUME-209",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every `session/update` the agent sends during a `session/resume` exchange with "
            "`replayFrom: {\"type\": \"start\"}` (replay plus the state snapshot) validates "
            "against the v2 schema and carries the resumed `sessionId` or that of a child "
            "session announced earlier in that same exchange by a `subagent_update` (on the "
            "Active Subagents RFD's rule that child updates keep the child's own `sessionId` and "
            "follow its announcement within the load/resume). An update for a session not "
            "announced within the exchange FAILs, even if an earlier turn announced it."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:207-209,221,282-284; "
            "docs/rfds/subagents.mdx:925-935,995-1003 (Active RFD); "
            "schema/v2/schema.unstable.json#/$defs/UpdateSessionNotification"
        ),
    ),
    Requirement(
        id="ACP-RESUME-210",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A successful `session/resume` of a session carries each list -- `configOptions`, "
            "`availableCommands` -- that the same session's own `session/new` response carried "
            "non-empty, and non-empty: a setup response replaces the lists the client holds, so "
            "an agent whose session has options or commands MUST include them. The session is "
            "resumed on the connection that created it. SKIPs when `session/new` carried "
            "neither list, or when that resume errors (`ACP-RESUME-216` judges the error). The "
            "premise \"the session still has them\" is inferred from `session/new`: an agent "
            "whose session legitimately lost every option in between answers the same way."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:108,136,333-335; "
            "docs/protocol/v2/draft/slash-commands.mdx:12; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-RESUME-212",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "With `replayFrom: {\"type\": \"start\"}` on a session whose last turn reached idle, "
            "no earlier `state_update` with `state` `running` or `requires_action` precedes the "
            "current-state snapshot (the last `state_update` before the response): replay "
            "carries no historical `state_update` as current activity. The snapshot itself may "
            "report any state, and a replayed historical `idle` cannot be told from the idle "
            "snapshot's optional stop reason, so neither is judged."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:227,348; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1084-1087"
        ),
    ),
    Requirement(
        id="ACP-RESUME-213",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every item in the `background` list of a resume's current-state snapshot (a "
            "`terminal`, `tool_call` or `subagent` item) is announced before that snapshot, "
            "within the resume exchange, by a `terminal_update` with its `terminalId`, a "
            "`tool_call_update` with its `toolCallId` or a `subagent_update` with its "
            "`sessionId`. Checked with `replayFrom` omitted, where nothing is replayed, so every "
            "listed item needs its own update. SKIPs when the snapshot lists no such item, "
            "which is the norm for an agent with no live background work, rather than passing "
            "vacuously. Items of other (custom) types are not judged."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:346; "
            "schema/v2/schema.unstable.json#/$defs/BackgroundWork"
        ),
    ),
    Requirement(
        id="ACP-RESUME-214",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A successful `session/resume` -- with `replayFrom` omitted or `{\"type\": "
            "\"start\"}` -- is preceded by a `session_info_update` for the resumed session, sent "
            "after every replayed history update, so the client can synchronize current session "
            "info. SHOULD. The test is gated on `capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:358-361; "
            "schema/v2/schema.unstable.json#/$defs/SessionInfoUpdate"
        ),
    ),
    Requirement(
        id="ACP-RESUME-216",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/resume` of a session this connection created and has not closed succeeds: "
            "the session is active, agents SHOULD NOT discard an active session, and resuming "
            "it again just synchronizes it. SHOULD. Any error FAILs here, where `ACP-RESUME-001` "
            "SKIPs on one. The test is gated on `capabilities.session`."
        ),
        citation=_cite("docs/protocol/v2/draft/session-setup.mdx:49,53"),
    ),
    Requirement(
        id="ACP-RESUME-217",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "When the agent reported a `background` array for a session before it was resumed "
            "(on the connection that created it, `[]` counts), the resume's current-state "
            "snapshot carries an array too, not an omitted or `null` one: the snapshot carries "
            "the list like any other, and an agent that reports background work MUST include "
            "it on every `state_update`. Checked with `replayFrom` omitted, after a turn on the "
            "session. SKIPs when no list was reported before the resume, or the resume sent no "
            "snapshot (`ACP-RESUME-206` judges that)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:346; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:204; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/properties/background"
        ),
    ),
    Requirement(
        id="ACP-LIST-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/list` with `params: {}` succeeds; the result's `sessions` field is "
            "present as an array, and the response validates against the v2 schema."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:10,76,111; "
            "schema/v2/schema.unstable.json#/$defs/ListSessionsResponse"
        ),
    ),
    Requirement(
        id="ACP-LIST-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/list` filtered by a `cwd` no session plausibly uses returns "
            "`sessions: []` -- never `null`, never an error."
        ),
        citation=_cite("docs/protocol/v2/draft/session-list.mdx:148"),
    ),
    Requirement(
        id="ACP-LIST-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "When `session/list` is filtered by a real `cwd`, every returned `SessionInfo.cwd` "
            "names that same directory. Agents MAY normalize paths when comparing, so equality is "
            "judged after path normalization (for example a trailing separator). A session whose "
            "`cwd` is a subdirectory of the filter is never returned. A per-entry check only; the "
            "reverse direction -- that a session at that `cwd` is returned at all -- is not "
            "asserted, since no upstream statement guarantees a freshly created session appears "
            "in `session/list`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:63-69; "
            "schema/v2/schema.unstable.json#/$defs/ListSessionsRequest/properties/cwd"
        ),
    ),
    Requirement(
        id="ACP-LIST-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text="Every returned `SessionInfo.cwd` is an absolute path.",
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:118-120; "
            "docs/protocol/v2/draft/overview.mdx:218"
        ),
    ),
    Requirement(
        id="ACP-LIST-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/list` with a relative `cwd` filter is rejected with an error, not answered "
            "with a result (\"Agents reject a relative path\"; declarative, no RFC keyword). The "
            "code is judged separately (`ACP-LIST-207`). The probe breaks the client rule that "
            "the filter be absolute on purpose, because the spec defines the agent's answer to "
            "exactly that input."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:64-65; "
            "docs/protocol/v2/draft/error.mdx:48; "
            "schema/v2/schema.unstable.json#/$defs/ListSessionsRequest/properties/cwd"
        ),
    ),
    Requirement(
        id="ACP-LIST-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/list` with a `cursor` the agent never issued is rejected with `-32602` (a "
            "MUST that names the code). A success, or another error code, FAILs. The probe is a "
            "fabricated `_tck`-prefixed token, never the empty string, which is a valid cursor. "
            "Cursors are opaque, but a token the agent never issued is invalid under every "
            "encoding."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:157; "
            "docs/protocol/v2/draft/error.mdx:48; "
            "schema/v2/schema.unstable.json#/$defs/ListSessionsRequest/properties/cursor"
        ),
    ),
    Requirement(
        id="ACP-LIST-207",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The rejection of `session/list` with a relative `cwd` filter (`ACP-LIST-205`'s "
            "probe) uses `-32602` (Invalid params). The sentence naming the code carries no RFC "
            "keyword, so the code is ADVISORY while the rejection itself is not. SKIPs when the "
            "probe was not rejected (`ACP-LIST-205`'s concern). An agent that accepts the "
            "relative filter FAILs `ACP-LIST-205` and is not judged here."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:64-65; docs/protocol/v2/draft/error.mdx:48"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/close` of a live, idle session succeeds with a schema-valid empty-object "
            "result -- `session/close`'s own baseline contract, distinct from the cancellation "
            "side effect `ACP-CLOSE-002`/`ACP-CANCEL-208` covers."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:367-369,389-405; "
            "schema/v2/schema.unstable.json#/$defs/CloseSessionRequest; "
            "schema/v2/schema.unstable.json#/$defs/CloseSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/close` on a session with foreground work in flight cancels that work as "
            "if `session/cancel` had been sent -- the same idle `state_update` with "
            "`stopReason: \"cancelled\"` evidence `ACP-CANCEL-208` already checks, deliberately "
            "reused verbatim rather than gathered by a second, near-identical probe. The id is "
            "registered separately from `ACP-CANCEL-208` purely for this area's own report "
            "legibility."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:389-393; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:374,1185-1188,1199"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "When `session/close` cancels in-flight foreground work, the idle `state_update` "
            "with `stopReason: \"cancelled\"` for that session arrives before the successful "
            "`session/close` response. SKIPs when the turn did not end `cancelled` (that is "
            "`ACP-CLOSE-002`'s finding) or the close lost the race."
        ),
        citation=_cite("docs/protocol/v2/draft/session-setup.mdx:393"),
    ),
    Requirement(
        id="ACP-CLOSE-204",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A `session/prompt` sent immediately before `session/close` (without awaiting its "
            "receipt) is answered with `-32800` (closing prevented insertion), with a success "
            "carrying a string `messageId` (already inserted), or with `-32002` (the agent "
            "processed the close first, so the session was no longer active when it reached the "
            "prompt) -- never another error, never left unanswered. ADVISORY rather than "
            "CAPABILITY: the outcome depends on how the agent schedules two back-to-back "
            "requests, so a failure here is reported but does not by itself fail the verdict."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:51,395; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:374; "
            "docs/protocol/v2/draft/error.mdx:54"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "When `session/close` arrives while the agent's own `session/request_permission` "
            "for that session is pending (the TCK holds it unanswered), the agent sends "
            "`$/cancel_request` naming it before its successful `session/close` response. "
            "SKIPPED when no permission request was pending when close was sent, or the close "
            "did not succeed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:391; "
            "schema/v2/schema.unstable.json#/$defs/CancelRequestNotification"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-206",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "After its successful `session/close` response, the agent sends no `session/update` "
            "and no agent -> client request carrying that `sessionId` on the connection. "
            "Responses to earlier `session/prompt` requests are exempt. Judged for closing an "
            "idle session and for a close that cancels work mid-turn (that second run SKIPs "
            "unless the turn ended `cancelled`)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:395; "
            "schema/v2/schema.unstable.json#/$defs/CloseSessionRequest"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-003",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/close` is idempotent: closing a session this connection already closed, "
            "or one that does not exist, succeeds with the same empty result. SHOULD. A "
            "`-32002` answer is the behavior clients are told to tolerate as success, but the "
            "agent SHOULD still return the empty result, so it is an ADVISORY FAIL. The test is "
            "gated on `capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:407-410; "
            "docs/protocol/v2/draft/error.mdx:56"
        ),
    ),
    Requirement(
        id="ACP-DELETE-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.delete",
        text=(
            "`session/delete` of a session active and idle on this connection succeeds with a "
            "schema-valid empty-object result (deleting an active session closes it first). The "
            "session certainly exists, so a `-32002` answer is not the tolerated \"already gone\" "
            "case here and FAILs."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-delete.mdx:35,57,78-86,95; "
            "docs/protocol/v2/draft/session-setup.mdx:49; "
            "schema/v2/schema.unstable.json#/$defs/DeleteSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-DELETE-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.delete",
        text=(
            "After a `session/delete` of a closed session, the session no longer appears in "
            "`session/list` results. A `-32002` answer to the delete counts as a successful "
            "delete (clients SHOULD treat it as one), so the listing is still judged; any other "
            "error FAILs. SKIPs when the closed session was never observed in `session/list` in "
            "the first place (nothing to compare against). :90 is a plain declarative, not an "
            "RFC keyword, but it is what `session/delete` means (mirrored by the sequence "
            "diagram), so this stays CAPABILITY."
        ),
        citation=_cite("docs/protocol/v2/draft/session-delete.mdx:27-28,90,92"),
    ),
    Requirement(
        id="ACP-DELETE-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Deleting an already-deleted or never-created `sessionId` SHOULD succeed silently, "
            "rather than erroring. A `-32002` answer is the deviation clients are told to "
            "tolerate as success, but the agent SHOULD still return the empty result, so it is "
            "an ADVISORY FAIL; any other error is worse."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-delete.mdx:91; docs/protocol/v2/draft/error.mdx:56"
        ),
    ),
    Requirement(
        id="ACP-DELETE-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.delete",
        text=(
            "`session/delete` of a session with foreground work in flight cancels that work as "
            "if `session/close` had been called: the idle `state_update` ending the turn carries "
            "`stopReason: \"cancelled\"` and arrives before the delete response. If the delete "
            "kept the prompt from being inserted, the prompt is answered `-32800`. A delete "
            "rejected without cancelling the work FAILs. SKIPs when the turn ended on its own "
            "before the delete landed (cancellation not exercised)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-delete.mdx:95; "
            "docs/protocol/v2/draft/session-setup.mdx:393,395"
        ),
    ),
    Requirement(
        id="ACP-DELETE-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.delete",
        text=(
            "After `session/delete` of a session, `session/resume` of that `sessionId` (same "
            "`cwd`) is answered with `-32002` and `data.sessionId` set to the requested id (a "
            "MUST that names the code). A `-32002` answer to the delete itself counts as a "
            "successful delete, so the resume is still judged."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-delete.mdx:92,94; "
            "docs/protocol/v2/draft/error.mdx:54,56"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.archive",
        text=(
            "Every `SessionInfo` in a `session/list` result carries a boolean (non-null) "
            "`archived`: checked on the default view, and on the `only` view once the test's own "
            "session is archived. SKIPs when the default list is empty. Same rule as v1; "
            "`session/list` is part of the baseline here, so there is no `list` gate."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:245; "
            "schema/v2/schema.unstable.json#/$defs/SessionInfo/properties/archived"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.archive",
        text=(
            "`session/archive` then `session/unarchive` on an existing session both succeed with "
            "schema-valid empty results. After archive the session is absent from the default "
            "`session/list` view and present under `archived: \"only\"` and `\"include\"`; after "
            "unarchive it is present in the default and `include` views and absent from `only`. "
            "SKIPs when the new session is not listed to begin with. An agent that rejects "
            "`include` or `only` FAILs, on the Draft RFD's rule that an agent advertising "
            "`archive` MUST support all three `archived` values."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:222,237-241; "
            "docs/rfds/session-archive.mdx:112 (Draft RFD); "
            "schema/v2/schema.unstable.json#/$defs/ArchiveSessionResponse; "
            "schema/v2/schema.unstable.json#/$defs/UnarchiveSessionResponse; "
            "schema/v2/schema.unstable.json#/$defs/SessionArchiveFilter"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-004",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.archive",
        text=(
            "`session/list` with an `archived` filter value the agent does not support fails "
            "with `-32602`, rather than falling back to the default (`exclude`) view. The probe "
            "value is `_tck_unsupported`, schema-valid through the open `other` branch. A "
            "success or any other error code is a FAIL; `-32000` (authentication required) "
            "SKIPs."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:243; docs/protocol/v2/draft/error.mdx:66; "
            "schema/v2/schema.unstable.json#/$defs/SessionArchiveFilter"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-005",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.archive",
        text=(
            "Archiving an already-archived session and unarchiving a not-archived one both "
            "succeed. `session/archive` and `session/unarchive` of a never-created `sessionId` "
            "fail with `-32002` and `data.sessionId` set to the requested id, rather than "
            "succeeding silently the way `session/delete` does. Same rule as v1, which asserts "
            "only error-vs-success; the v2 docs name the code."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:251; docs/protocol/v2/draft/error.mdx:54,66; "
            "schema/v2/schema.unstable.json#/$defs/ArchiveSessionRequest; "
            "schema/v2/schema.unstable.json#/$defs/UnarchiveSessionRequest"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-006",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.archive",
        text=(
            "After a successful `session/delete`, the deleted session appears under no "
            "`archived` filter value (`exclude`, `include`, `only`). Needs "
            "`capabilities.session.delete` as well; SKIPs without it. The session must be "
            "listed (under `include`) before the delete, else the row SKIPs. A `-32002` answer "
            "to the delete counts as success. An agent that rejects `include` or `only` FAILs, "
            "on the Draft RFD's rule that an agent advertising `archive` MUST support all three "
            "`archived` values."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:252; "
            "docs/rfds/session-archive.mdx:112 (Draft RFD)"
        ),
    ),
    Requirement(
        id="ACP-ARCHIVE-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.archive",
        text=(
            "`session/archive` of a session with foreground work in flight cancels that work as "
            "if `session/close` had been called: the idle `state_update` ending the turn carries "
            "`stopReason: \"cancelled\"` and arrives before the archive response. If the archive "
            "kept the prompt from being inserted, the prompt is answered `-32800`. An archive "
            "rejected without cancelling the work FAILs (an active session is archivable). "
            "SKIPs when the turn ended on its own before the archive landed (cancellation not "
            "exercised)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-list.mdx:247; "
            "docs/protocol/v2/draft/session-setup.mdx:393,395; "
            "schema/v2/schema.unstable.json#/$defs/ArchiveSessionRequest"
        ),
    ),
    Requirement(
        id="ACP-ADDDIRS-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.additionalDirectories",
        text="`session/new` with an absolute `additionalDirectories` entry is accepted.",
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:412-441; "
            "schema/v2/schema.unstable.json#/$defs/NewSessionRequest/properties/additionalDirectories"
        ),
    ),
    Requirement(
        id="ACP-ADDDIRS-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.additionalDirectories",
        text=(
            "`session/resume` with an absolute `additionalDirectories` entry (matching the "
            "session's own `cwd`) is accepted -- a new carrier statement in v2; v1 had no "
            "`session/resume`/`session/load` analogue to this rule at all."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:416,439; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionRequest/properties/additionalDirectories"
        ),
    ),
    Requirement(
        id="ACP-ADDDIRS-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.additionalDirectories",
        text=(
            "`session/new` with a relative `additionalDirectories` entry is rejected with "
            "`-32602` when the agent advertises the capability (the code is named by the "
            "spec). A success, or another error code, FAILs. The probe breaks the client rule "
            "that each entry be absolute on purpose, because the spec defines the agent's "
            "answer to exactly that input."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:437,443; "
            "schema/v2/schema.unstable.json#/$defs/NewSessionRequest/properties/additionalDirectories"
        ),
    ),
    Requirement(
        id="ACP-FORK-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.fork",
        text=(
            "`session/fork` of an existing session (same `cwd`) succeeds with a schema-valid "
            "result whose `sessionId` is a non-empty string distinct from the source session's."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:269-273; "
            "docs/protocol/v2/draft/session-setup.mdx:49; "
            "schema/v2/schema.unstable.json#/$defs/ForkSessionResponse; "
            "schema/v2/schema.unstable.json#/$defs/ForkSessionResponse/properties/sessionId; "
            "schema/v2/schema.unstable.json#/$defs/SessionCapabilities/properties/fork"
        ),
    ),
    Requirement(
        id="ACP-FORK-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.fork",
        text=(
            "The forked session is active once `session/fork` responds: a `session/prompt` on "
            "the forked id, with no `session/resume` first, is accepted with a `messageId` and "
            "the turn reaches a terminating idle. Definitional (the draft docs bold **active**, "
            "with no RFC keyword), but an unknown or non-active session MUST get `-32002`, so an "
            "active forked session must be accepted."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:49; "
            "docs/protocol/v2/draft/error.mdx:54; "
            "docs/rfds/session-fork.mdx:67 (Draft RFD)"
        ),
    ),
    Requirement(
        id="ACP-FORK-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.fork",
        text=(
            "`session/fork` of a `sessionId` the agent never created is answered with `-32002` "
            "and `data.sessionId` set to the requested id (a MUST that names the code)."
        ),
        citation=_cite("docs/protocol/v2/draft/error.mdx:54,64"),
    ),
    Requirement(
        id="ACP-FORK-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.fork",
        text=(
            "`session/fork` of an existing session that is no longer active on the connection "
            "(created, then closed, and still listed by `session/list`) succeeds with a new "
            "`sessionId`: the source session only has to exist. SKIPs when the closed session "
            "is not listed (its existence cannot be established)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:64; docs/protocol/v2/draft/session-setup.mdx:52"
        ),
    ),
    Requirement(
        id="ACP-FORK-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.fork",
        text=(
            "A successful `session/fork` response carries `configOptions`, non-empty, when the "
            "source session's own `session/new` response carried it non-empty: a setup response "
            "replaces the list the client holds, so an agent whose session has configuration "
            "options MUST include them. The source is forked on the connection that created it. "
            "Presence and non-emptiness only; shape is `ACP-CONFIG-201`/`203`'s concern. "
            "`availableCommands` is not judged: a fork's commands are the new session's own, "
            "not the source's. SKIPs when `session/new` carried no `configOptions`, or when the "
            "fork errors (`ACP-FORK-201`/`202` judge the error). The premise \"the new session "
            "has them\" is inferred from the source's `session/new`: an agent whose fork "
            "legitimately has no options answers the same way."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:108,140; "
            "schema/v2/schema.unstable.json#/$defs/ForkSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-FORK-206",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.fork",
        text=(
            "When the source session's latest `background` list is non-empty at fork time, no "
            "`state_update` of the forked session lists one of those items: a fork starts with "
            "no background work, and its snapshots report `background: []` until it starts its "
            "own. The fork is prompted once so that it reports its state. Definitional (the "
            "draft docs state it with no RFC keyword), like `ACP-FORK-202`. SKIPs when the "
            "source has no listed work at fork time, or when the fork or its turn fails "
            "(`ACP-FORK-201`/`202` judge those)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:49; "
            "schema/v2/schema.unstable.json#/$defs/IdleStateUpdate/properties/background; "
            "docs/rfds/v2/background-work.mdx:226 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-001",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.systemPrompt",
        text=(
            "`session/new` with `systemPrompt: {mode: \"append\", content: [<text block>]}` "
            "succeeds. The error paths are `ACP-SYSPROMPT-002`/`003`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:473-477,483; "
            "schema/v2/schema.unstable.json#/$defs/SystemPromptMode/anyOf/0"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.systemPrompt.mode.override",
        text=(
            "`session/new` with `systemPrompt: {mode: \"override\", content: [<text block>]}` "
            "succeeds when `session.systemPrompt.mode.override` is advertised."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:476-477,483; "
            "docs/protocol/v2/draft/initialization.mdx:298-304; "
            "schema/v2/schema.unstable.json#/$defs/SessionSystemPromptModeCapabilities"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-002",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.systemPrompt",
        text=(
            "`session/new`, and `session/resume` of an existing session, with a "
            "`systemPrompt.mode` the agent cannot support (the implementation-reserved "
            "`_tck_unsupported`) returns an error rather than creating or resuming the "
            "session; after a refused resume, `session/prompt` on that id does not succeed. "
            "The error code is recorded, not asserted (`-32602` is only RECOMMENDED). The probes "
            "break the client rule to use only an advertised mode on purpose: the spec defines "
            "the agent's answer."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:474,481; "
            "schema/v2/schema.unstable.json#/$defs/SystemPromptMode"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.systemPrompt",
        text=(
            "`session/new`, and `session/resume` of an existing session, with a non-text "
            "`systemPrompt.content` block (`resource_link`) returns an error rather than "
            "creating or resuming the session -- only text blocks are supported for now; "
            "after a refused resume, `session/prompt` on that id does not succeed. The probes "
            "break the client rule to send only text blocks on purpose: the spec defines the "
            "agent's answer."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:477,481; "
            "schema/v2/schema.unstable.json#/$defs/SystemPrompt/properties/content"
        ),
    ),
    Requirement(
        id="ACP-MCP-201",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "INFORMATIONAL, not CAPABILITY, despite the underlying `capabilities.session.mcp."
            "stdio` marker: records whether `session/new` accepts a well-formed stdio MCP "
            "server entry when the marker is advertised, and whether a `notice` for the new "
            "session followed an accepted request. A connect failure against a harmless, "
            "possibly-nonexistent command is the agent's own business: the spec lets it either "
            "fail the request or continue without that server, and only says that if it "
            "continues it SHOULD tell the user (\"for example with a notice\"), which is not "
            "tied to a wire event. So this never asserts on the outcome."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:555-607,656,681-685; "
            "schema/v2/schema.unstable.json#/$defs/McpServerStdio"
        ),
    ),
    Requirement(
        id="ACP-MCP-202",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "INFORMATIONAL, not CAPABILITY, same reasoning as `ACP-MCP-201`: records whether "
            "`session/new` accepts a well-formed http MCP server entry when `capabilities."
            "session.mcp.http` is advertised. Never asserts on the outcome."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:609-652; "
            "schema/v2/schema.unstable.json#/$defs/McpServerHttp"
        ),
    ),
    Requirement(
        id="ACP-MCP-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/new` with an MCP server of a transport the agent does not support is "
            "rejected with `-32602` (the code is named by the spec). Three probes: v1's `sse`, "
            "which the spec names explicitly, the implementation-reserved "
            "`_tck_unsupported_transport`, which no agent supports, and `acp` (the unstable "
            "MCP-over-ACP transport, covered by the spec's \"a transport they did not "
            "advertise\"), sent only when the agent does not advertise "
            "`capabilities.session.mcp.acp`. A success, or another error code, on any probe "
            "FAILs. The probes break the client rule to use only advertised transports on "
            "purpose, because the spec defines the agent's answer to exactly those inputs."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:545,553; "
            "schema/v2/schema.unstable.json#/$defs/McpServer"
        ),
    ),
    Requirement(
        id="ACP-MCP-204",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/new` with two MCP servers sharing a `name` is rejected with `-32602`. "
            "ADVISORY rather than CAPABILITY: the sentence carries no keyword for the agent, "
            "and an agent that launches servers before validating may fail with a launch error "
            "instead, which the spec allows without naming a code. The probe breaks the "
            "client MUST that names be unique on purpose. The test is gated on "
            "`capabilities.session.mcp.stdio`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:547,685; "
            "schema/v2/schema.unstable.json#/$defs/NewSessionRequest/properties/mcpServers"
        ),
    ),
    Requirement(
        id="ACP-SESSION-006",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A random canary the TCK puts in an MCP server's credentials -- a stdio server's "
            "`env` value, or an http server's `headers` value, sent on `session/new` -- never "
            "appears on the agent's stdout or stderr after one prompt turn, `session/list` and "
            "a `session/resume` with the same servers: not in responses, errors, "
            "`session/update`, `_meta`, listings or replayed history, and not in the stdio "
            "server's own command line. SHOULD NOT. Only the client-observable part of the "
            "rule: model context, logging beyond stderr and persistence are not covered. The "
            "stdio test is gated on `capabilities.session.mcp.stdio`, the http test on "
            "`capabilities.session.mcp.http`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:691,695; "
            "schema/v2/schema.unstable.json#/$defs/EnvVariable; "
            "schema/v2/schema.unstable.json#/$defs/HttpHeader"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-201",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "Every `configOptions` entry in `session/new`'s result validates: `configId` and "
            "`name` are present, `type` selects the right shape (`select` requires `currentValue`"
            "+`options`; `boolean` requires `currentValue`), and a `select` entry's `options` is "
            "an array -- either a flat `SessionConfigSelectOption[]` or a grouped "
            "`SessionConfigSelectGroup[]`, never mixed. A `select` entry offers at least one value "
            "and every group holds at least one (`minItems: 1`). An empty `configOptions` list "
            "itself is valid and means the session has none (a SKIP, not a violation). Only the "
            "`configOptions` items are judged, not the rest of the carrying message. Inferred "
            "support, same encoding as v1's `ACP-MODES-001`/`ACP-CONFIG-001` -- "
            "`capability=\"inferred:configOptions\"` is documentation-only."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/SessionConfigOption; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigId; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigOptionCategory; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigValueId; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelectOptions; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelectOption; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelectGroup; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelectGroup/properties/options; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigGroupId; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelect; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigBoolean; "
            "docs/protocol/v2/draft/session-config-options.mdx:93-154"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-002",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "A well-formed `session/set_config_option` of an advertised option succeeds (agents "
            "advertising config options MUST support the method) and responds with the complete "
            "post-change `configOptions` list: an array, schema-valid, containing the changed "
            "`configId`. Whether every "
            "previously-advertised `configId` is still present is recorded, never asserted -- a "
            "change may legitimately remove dependent options, so a partial reply and a "
            "dependent removal are wire-identical. SKIPs when `session/new` advertised no "
            "`configOptions`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:234,236,291,367-371; "
            "docs/protocol/v2/draft/initialization.mdx:239-240; "
            "docs/rfds/session-config-options.mdx:45 (Completed RFD); "
            "schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionRequest; "
            "schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionResponse"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-203",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "`session/resume`'s `configOptions`, when present, validates the same way as "
            "`ACP-CONFIG-201` (including its non-empty `select` options) -- a new carrier in v2 (v1's `session/load` had no analogous "
            "field). Shape only: whether the resume carries the list at all is "
            "`ACP-RESUME-210`'s concern, and an absent list SKIPs. The session is obtained the "
            "same way as `ACP-RESUME-001`, so a resume error other than `-32601` SKIPs."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:136,333-335; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionResponse/properties/configOptions"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-001",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "A `select`-type option's `currentValue` is one of its declared `options` values "
            "(flat or grouped). An explicit MUST, not schema-enforced."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:116-119,125-133; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelect"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-206",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "An observed `config_option_update` `session/update` carries the complete current "
            "configuration state as a schema-valid `configOptions` array. Whether it is a "
            "superset of the last known `configId` set is recorded, never asserted -- the "
            "current state may legitimately drop options (e.g. a model fallback). Conditional "
            "and vacuous (recorded, never FAILed) when no such update is ever observed."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:236,373,459; "
            "docs/rfds/session-config-options.mdx:45 (Completed RFD); "
            "schema/v2/schema.unstable.json#/$defs/ConfigOptionUpdate"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-207",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "`session/set_config_option` naming a `configId` the session did not advertise is "
            "rejected with `-32602`. The TCK sends the probe id `_tck_unknown_config` on purpose: "
            "clients MUST only send advertised ids, but the same sentence fixes the agent's "
            "answer to one that doesn't. SKIPs when `session/new` advertised no `configOptions`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:234; "
            "docs/protocol/v2/draft/error.mdx:48; "
            "schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionRequest"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-208",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "`session/set_config_option` for an advertised option with an invalid value is "
            "rejected with `-32602`: a `select` value it does not declare (probe "
            "`_tck_unknown_value`), a value `type` that does not match the option (`boolean` "
            "for a `select`, `id` for a `boolean`), or an unsupported value `type` (probe "
            "`_tck_unsupported`). Probes that need an option type the session lacks are "
            "skipped. SKIPs when `session/new` advertised no `configOptions`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:234,264-273; "
            "docs/protocol/v2/draft/error.mdx:48; "
            "schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionRequest"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-209",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "A rejected `session/set_config_option` leaves the configuration unchanged. After "
            "each of the unknown-`configId` and invalid-value probes of `ACP-CONFIG-207`/`208` "
            "is rejected, a no-op set of a different option returns a list whose `(configId, "
            "currentValue)` pairs equal the previous list. Probes the agent did not reject "
            "are not judged here (`ACP-CONFIG-207`/`208` FAIL them; the baseline is re-taken "
            "after them). The invalid-value probe needs a second settable option, and the "
            "whole row SKIPs when the session has no option besides the one the follow-up sets "
            "(nothing to observe through). A `config_option_update` arriving meanwhile also "
            "SKIPs (the agent may change configuration itself)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:234,459-463; "
            "schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionRequest"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-210",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "Within one `select` option every declared `value` is unique, across groups as "
            "well. Not schema-enforced."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:125-133; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelect"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-211",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When a `session/set_config_option` changes the configuration (the response's "
            "`(configId, currentValue)` pairs differ from the list before the call), the agent "
            "also sends a `config_option_update` for the session on the requesting connection, "
            "before the response or within the quiet drain after it. Only the requesting "
            "connection is judged. SKIPs when no `configOptions` were advertised or the call "
            "changed nothing."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:375; "
            "schema/v2/schema.unstable.json#/$defs/ConfigOptionUpdate"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-212",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The `config_option_update` that duplicates a `session/set_config_option` change "
            "arrives before that request's response. Judged only when an update carrying the "
            "response's state is observed (a later update with different state may be a "
            "legitimate subsequent change); FAILs when every such update arrives after the "
            "response. SKIPs otherwise."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:377-379; "
            "schema/v2/schema.unstable.json#/$defs/ConfigOptionUpdate"
        ),
    ),
    Requirement(
        id="ACP-COMMANDS-201",
        tier=Tier.CAPABILITY,
        capability="inferred:availableCommands",
        text=(
            "Every command the agent advertises (in a setup response's `availableCommands` or "
            "an `available_commands_update`) validates as `AvailableCommand` -- it carries a "
            "`type` discriminator (`command`, or a `_`-prefixed custom type) -- and within each "
            "list every `name` contains no whitespace and is unique. Only the command items are "
            "judged, not the rest of the carrying message. No `availableCommands` capability "
            "marker exists, so support is inferred from the agent advertising any command "
            "(`capability=\"inferred:availableCommands\"` is documentation-only); SKIPs when "
            "none is observed. A leading `/` in `name` is not judged: the spec says \"without the "
            "leading `/`\" with no RFC keyword."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/slash-commands.mdx:12,37-43,89-110; "
            "schema/v2/schema.unstable.json#/$defs/AvailableCommand; "
            "schema/v2/schema.unstable.json#/$defs/Command; "
            "schema/v2/schema.unstable.json#/$defs/AvailableCommandsUpdate"
        ),
    ),
    Requirement(
        id="ACP-AUTH-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "`authMethods[*].methodId` values are unique within the list. Schema validation "
            "alone cannot express this. SKIPs when no `authMethods` are advertised."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/authentication.mdx:51; "
            "schema/v2/schema.unstable.json#/$defs/AuthMethod; "
            "schema/v2/schema.unstable.json#/$defs/AuthMethodId"
        ),
    ),
    Requirement(
        id="ACP-AUTH-002",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "No `authMethods[*]` entry with `type: \"terminal\"` is advertised unless the "
            "client advertised `capabilities.auth.terminal: {}` in `initialize`'s params "
            "(\"Agents MUST NOT advertise a `terminal` method unless this capability is "
            "present\"). The capability is a nested object marker in v2 (v1: top-level "
            "boolean `clientCapabilities.auth.terminal`)."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AuthMethodTerminal; "
            "schema/v2/schema.unstable.json#/$defs/ClientAuthCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/TerminalAuthCapabilities; "
            "docs/protocol/v2/draft/authentication.mdx:149-151"
        ),
    ),
    Requirement(
        id="ACP-AUTH-004",
        tier=Tier.CAPABILITY,
        capability="inferred:authMethods",
        text=(
            "`auth/logout` returns a non-error, schema-valid result. Support is inferred from "
            "a non-empty `authMethods` -- v2 has no `agentCapabilities.auth.logout` marker at "
            "all (unlike v1); `capability=\"inferred:authMethods\"` is documentation-only. "
            "Only actually exercised when `--allow-logout`/`--tck-allow-logout` is given "
            "(destructive: may revoke the operator's own credentials); SKIPs otherwise."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/LogoutAuthRequest; "
            "schema/v2/schema.unstable.json#/$defs/LogoutAuthResponse; "
            "schema/v2/schema.unstable.json#/$defs/AgentAuthCapabilities; "
            "docs/protocol/v2/draft/authentication.mdx:51-52,247-249"
        ),
    ),
    Requirement(
        id="ACP-AUTH-003",
        tier=Tier.CAPABILITY,
        capability="inferred:authMethods",
        text=(
            "Given `--auth-method <id>` naming a non-`terminal`, advertised `methodId`, "
            "`auth/login` does not answer `-32601` (Method not found) -- an agent advertising "
            "`authMethods` MUST implement it -- nor `-32602` (Invalid params) when the "
            "advertised entry is `type: \"agent\"` (the one standard type that uses "
            "`auth/login`; `-32602` is for an id that is not an advertised login method). "
            "When `capabilities.session` is advertised, a subsequent `session/new` does not "
            "fail with `-32000`. v1's `authenticate` is renamed `auth/login`. SKIPs when "
            "`--auth-method` was not given, the agent advertises no `authMethods`, or "
            "`auth/login` fails with any other error (`-32602` for a custom `_`-prefixed type "
            "included, since that type may not use `auth/login`)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/authentication.mdx:51-53,87-88,191; "
            "schema/v2/schema.unstable.json#/$defs/LoginAuthRequest/required (`methodId`); "
            "schema/v2/schema.unstable.json#/$defs/LoginAuthResponse"
        ),
    ),
    Requirement(
        id="ACP-AUTH-005",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/new` does not fail with `-32000` (AUTHENTICATION_REQUIRED) when "
            "`authMethods` is empty or absent. SKIPs unless `capabilities.session` is advertised."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/schema.mdx:954 (-32000 is a MAY, not a MUST); "
            "docs/protocol/v2/draft/authentication.mdx:193"
        ),
    ),
    Requirement(
        id="ACP-AUTH-206",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Every `authMethods[*]` entry carries a `type` that is one of the schema's defined "
            "discriminator values (`\"agent\"`, `\"terminal\"`) or begins with `_` -- the general open-enum "
            "extensibility rule applied to this field. New in v2: v1's `type` could default to "
            "\"agent\" when absent and had no enum-closure rule at all."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/authentication.mdx:87-89,118-120; "
            "docs/protocol/v2/draft/extensibility.mdx:233-242; "
            "schema/v2/schema.unstable.json#/$defs/AuthMethod"
        ),
    ),
    Requirement(
        id="ACP-AUTH-006",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "On a connection that advertised `capabilities.auth.terminal: {}`, every "
            "`type: \"terminal\"` entry's `args` (if present; `null` counts as omitted) is an array "
            "of strings, `env` (if present; `null` counts as omitted) is an array of well-formed "
            "`EnvVariable` objects (`name`/`value` both required strings), and `env` entries' `name`s are unique within that "
            "descriptor. Conditional on at least one terminal entry actually appearing; SKIPs "
            "otherwise. v1's `env` is a string map, unique by construction; v2's is an array, so "
            "name uniqueness is checked by hand."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AuthMethodTerminal/properties/env (\"Names MUST be "
            "unique\"); schema/v2/schema.unstable.json#/$defs/EnvVariable; "
            "docs/protocol/v2/draft/authentication.mdx:203-205"
        ),
    ),
    Requirement(
        id="ACP-AUTH-208",
        tier=Tier.CAPABILITY,
        capability="inferred:authMethods",
        text=(
            "When `initialize` advertised a non-empty `authMethods`, `auth/login` with a "
            "`methodId` that is not among them (the implementation-reserved "
            "`_tck_unadvertised_method`) is rejected with an error rather than answered with "
            "a result. The code is judged separately "
            "(`ACP-AUTH-210`). The probe breaks the client rule to send only an advertised "
            "`methodId` on purpose: the spec defines the agent's answer. Sent on a fresh "
            "connection with no `--auth-method` login, and never for a `terminal` id. SKIPs "
            "when no `authMethods` are advertised."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/authentication.mdx:191; "
            "schema/v2/schema.unstable.json#/$defs/LoginAuthRequest"
        ),
    ),
    Requirement(
        id="ACP-AUTH-007",
        tier=Tier.CAPABILITY,
        capability="capabilities.auth.status",
        text=(
            "When `capabilities.auth.status` is advertised (object marker), `auth/status` sent "
            "with `{}` params right after `initialize`, before any `auth/login` on the "
            "connection, returns a result that validates as `AuthStatusResponse`. It is never "
            "an error: not `-32000` (the agent MUST NOT auth-gate it, since clients call it to "
            "learn whether authentication is needed) and not `-32601` (the agent advertised "
            "it). The test skips the `--auth-method` login so the agent is observed "
            "unauthenticated. Unstable method."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AuthStatusRequest; "
            "schema/v2/schema.unstable.json#/$defs/AuthStatusResponse; "
            "schema/v2/schema.unstable.json#/$defs/AgentAuthCapabilities/properties/status; "
            "docs/protocol/v2/draft/schema.mdx:143-144; "
            "docs/protocol/v2/draft/initialization.mdx:215-219; "
            "docs/protocol/v2/draft/authentication.mdx:193; "
            "docs/rfds/get-auth-state.mdx:293,297 (Draft RFD)"
        ),
    ),
    Requirement(
        id="ACP-AUTH-008",
        tier=Tier.CAPABILITY,
        capability="capabilities.auth.status",
        text=(
            "When `capabilities.auth.status` is advertised, the `state` in the `auth/status` "
            "result is one of the defined `AuthState` values or begins with `_`: `AuthState` has "
            "a fallback branch, and extensions MUST NOT define custom non-underscore values "
            "there (other strings are reserved for future ACP variants). The schema accepts any "
            "string, so `ACP-AUTH-007` cannot catch this. Only the result is judged: SKIPs when "
            "the call returns no string `state` (`ACP-AUTH-007`'s concern)."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AuthState; "
            "docs/protocol/v2/draft/extensibility.mdx:235-240"
        ),
    ),
    Requirement(
        id="ACP-AUTH-210",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The rejection of `auth/login` for an unadvertised `methodId` (`ACP-AUTH-208`'s "
            "probe) uses `-32602` (Invalid params). The sentence naming the code carries no "
            "RFC keyword, so the code is ADVISORY while the rejection itself is not. SKIPs "
            "when no `authMethods` are advertised or the probe was not rejected "
            "(`ACP-AUTH-208`'s concern)."
        ),
        citation=_cite("docs/protocol/v2/draft/authentication.mdx:191"),
    ),
    Requirement(
        id="ACP-PATCH-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every agent-emitted message update/chunk "
            "(`user_message_chunk`/`user_message`/`agent_message_chunk`/`agent_message`/"
            "`agent_thought_chunk`/`agent_thought`) carries a non-empty string `messageId`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:484; "
            "schema/v2/schema.unstable.json#/$defs/ContentChunk; "
            "schema/v2/schema.unstable.json#/$defs/UserMessage; "
            "schema/v2/schema.unstable.json#/$defs/AgentMessage; "
            "schema/v2/schema.unstable.json#/$defs/AgentThought"
        ),
    ),
    Requirement(
        id="ACP-PATCH-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Two `session/prompt`s on the same session receive two distinct `messageId` "
            "values -- the v2 analogue of v1's `duplicate_session_id.py` defect pattern, "
            "applied to message ids instead of session ids."
        ),
        citation=_cite("docs/protocol/v2/draft/prompt-lifecycle.mdx:368"),
    ),
    Requirement(
        id="ACP-PATCH-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every `tool_call_update` carries a non-empty `toolCallId`; every "
            "`tool_call_content_chunk` carries a non-empty `toolCallId` and `content`. There "
            "is no separate tool-call \"create\" message in v2 -- an update for a "
            "previously-unseen `toolCallId` is itself the create, so no create-before-update "
            "ordering is asserted. Conditional on "
            "at least one such update being observed during the run, else SKIP."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/ToolCallUpdate; "
            "schema/v2/schema.unstable.json#/$defs/ToolCallId; "
            "schema/v2/schema.unstable.json#/$defs/ToolCallContentChunk; "
            "schema/v2/schema.unstable.json#/$defs/TerminalOutput; "
            "schema/v2/schema.unstable.json#/$defs/TerminalExitStatus"
        ),
    ),
    Requirement(
        id="ACP-PATCH-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every `plan_update.plan` -- including an unknown/`_`-prefixed `type` variant -- "
            "carries a non-empty `planId`. Conditional on at least one `plan_update` being "
            "observed, else SKIP."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/agent-plan.mdx:147; "
            "schema/v2/schema.unstable.json#/$defs/PlanUpdateContent; "
            "schema/v2/schema.unstable.json#/$defs/PlanId"
        ),
    ),
    Requirement(
        id="ACP-PATCH-206",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every `terminal_update` carries a `terminalId`, and a supplied `cwd` is an "
            "absolute path. `cwd` is a patch field, so a later concrete value may replace an "
            "earlier one. Conditional on at least one `terminal_update` being observed, else "
            "SKIP."
        ),
        citation=_cite("docs/protocol/v2/draft/tool-calls.mdx:493-499,523-531"),
    ),
    Requirement(
        id="ACP-PATCH-207",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`terminal_output_chunk.data` and `terminal_update.output.data` each decode as "
            "standalone, valid RFC 4648 base64 -- independent of any other chunk. Conditional "
            "on at least one such field being observed, else SKIP."
        ),
        citation=_cite("docs/protocol/v2/draft/tool-calls.mdx:536-537,566-570"),
    ),
    Requirement(
        id="ACP-PATCH-208",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "The first report of a given `toolCallId` includes a non-empty `title`; `name`, if "
            "ever set, does not change across later reports of the same id. A first report is "
            "a `tool_call_update`, a permission request's `tool_call` subject, or a "
            "`tool_call_content_chunk`; a chunk carries no title, so a tool call a chunk "
            "creates misses the SHOULD. Kept ADVISORY, not promoted to CAPABILITY under the "
            "session-baseline tiering rule -- the "
            "corresponding test is still `@pytest.mark.capability(\"capabilities.session\")`-"
            "gated for its own SKIP."
        ),
        citation=_cite("docs/protocol/v2/draft/tool-calls.mdx:41-54,198-200,270-273"),
    ),
    Requirement(
        id="ACP-PATCH-209",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When the agent sends `session/request_permission` for the prompted session during "
            "a turn, other than one whose `subject` references an item in the latest reported "
            "`background` list (background work may leave the session `idle`), it reports "
            "`state_update.state == \"requires_action\"` for that session at some point in the "
            "turn (SHOULD). What follows it is `ACP-STATE-205`'s MUST. The test is gated on "
            "`capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:153,174,845,1074; "
            "docs/protocol/v2/draft/tool-calls.mdx:209,268"
        ),
    ),
    Requirement(
        id="ACP-PATCH-210",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Per `toolCallId`, the effective `status` (applying every `tool_call_update` and "
            "`tool_call` permission subject in wire order; `null` resets it to `pending`) never "
            "goes back to `pending` and never changes once `completed`, `failed` or "
            "`cancelled`: a final tool call is not reopened. SKIPPED when no tool call is "
            "reported during the turn."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:102-108,421,423; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:184"
        ),
    ),
    Requirement(
        id="ACP-PATCH-211",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When the turn's idle arrives, every tool call reported for the prompted session "
            "during the turn has a final status (`completed`, `failed` or `cancelled`), unless "
            "a `background` list reported during the turn names it, or names a terminal it "
            "references with a `terminal` content item (a tool call that references a listed "
            "terminal is live, like Codex's command items that stay `in_progress` until the "
            "process exits; an Active RFD allows this explicitly). The docs are not uniform: "
            "`tool-calls.mdx:423` exempts only tool calls in the list, while the other draft "
            "docs treat a tool call that references a listed terminal as live too, so the row "
            "follows the broader text. SKIPPED when no tool call is reported, or the turn ends "
            "with an error response. The test is gated on `capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:216,998,1175; "
            "docs/protocol/v2/draft/session-setup.mdx:391; "
            "docs/protocol/v2/draft/tool-calls.mdx:423; "
            "docs/rfds/v2/background-work.mdx:56 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-PATCH-212",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Once a tool call's effective status is final, or a terminal's effective "
            "`exitStatus` is an object, its effective `capabilities.cancel` is absent or "
            "`null`. `capabilities` is a nullable patch, so a final status sent without "
            "clearing it keeps advertising `cancel`. Passive: the TCK sends no "
            "`tool_call/cancel` or `terminal/cancel`. SKIPPED when no tool call or terminal "
            "advertises `cancel` during the turn. The test is gated on `capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:440,600; "
            "schema/v2/schema.unstable.json#/$defs/ToolCallCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/TerminalCapabilities"
        ),
    ),
    Requirement(
        id="ACP-TOOLCANCEL-201",
        tier=Tier.CAPABILITY,
        capability="inferred:toolCallCancel",
        text=(
            "A tool call that currently advertises `capabilities.cancel` (an object) and is not "
            "final accepts `tool_call/cancel`: the agent answers it with an empty result, not an "
            "error. The docs state this as the rule without an RFC keyword, and no `initialize` "
            "marker announces it, so the row is CAPABILITY and gated by `inferred:toolCallCancel` "
            "(documentation-only): the test SKIPs itself when no tool call advertises `cancel` "
            "while live during the driven turn. The TCK sends the request only for such a tool "
            "call (the client MUST NOT otherwise) and treats a `-32602` that follows the tool "
            "call's own final update as the legitimate `already final` answer, not judged; it "
            "then tries the next live tool call. The driven turn runs the cancel prompt; a "
            "`tool_call/cancel` stops a real tool call, and the TCK then sends `session/cancel` so "
            "no work is left running."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:440,456-459; "
            "schema/v2/schema.unstable.json#/$defs/CancelToolCallRequest; "
            "schema/v2/schema.unstable.json#/$defs/CancelToolCallResponse"
        ),
    ),
    Requirement(
        id="ACP-TOOLCANCEL-202",
        tier=Tier.CAPABILITY,
        capability="inferred:toolCallCancel",
        text=(
            "After it accepted `tool_call/cancel`, the agent confirms with a `tool_call_update` "
            "that gives that tool call a final status (`completed`, `failed` or `cancelled`: "
            "normally `cancelled`, and the other two when the work finished first). Gated by "
            "`inferred:toolCallCancel` like `ACP-TOOLCANCEL-201`; SKIPPED when no cancel was "
            "accepted (nothing advertised `cancel`, the agent rejected the request, which is "
            "`ACP-TOOLCANCEL-201`'s finding, or the tool call was already final). The final "
            "status must arrive within half the run's per-response timeout."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:423,458; "
            "schema/v2/schema.unstable.json#/$defs/CancelToolCallRequest"
        ),
    ),
    Requirement(
        id="ACP-TOOLCANCEL-203",
        tier=Tier.CAPABILITY,
        capability="inferred:toolCallCancel",
        text=(
            "`tool_call/cancel` sent with a child session's `sessionId` for a child tool call that "
            "currently advertises `capabilities.cancel` and is not final is accepted and "
            "confirmed like a tool call of the prompted session (`ACP-TOOLCANCEL-201/202`): an "
            "empty result, then a `tool_call_update` that gives it a final status. `sessionId` is "
            "the session that reports the tool call, and the tool call's own `cancel` enables the "
            "request even when the child advertises no `cancel`. The docs state this as the rule "
            "without an RFC keyword, and no `initialize` marker announces it, so the row is "
            "CAPABILITY and gated by `inferred:toolCallCancel` (documentation-only). A separate "
            "row from 201/202 because the prompted-session driver does not follow a child's "
            "items: judged over the driven turn that also exercises the child cancel "
            "(`ACP-SUBAGENT-016`), for the first child tool call that advertises `cancel` while "
            "live, so a defect in routing by the child's `sessionId` fails exactly this row. "
            "SKIPs when no child tool call advertises `cancel` while live, or it was final when "
            "the agent read the request (a `-32602` after its own final update is the "
            "`already final` answer, not judged). v2-only (`2xx`)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:440,456-459; "
            "schema/v2/schema.unstable.json#/$defs/CancelToolCallRequest; "
            "docs/rfds/subagents.mdx:1042-1045 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-TERMCANCEL-201",
        tier=Tier.CAPABILITY,
        capability="inferred:terminalCancel",
        text=(
            "A terminal that currently advertises `capabilities.cancel` (an object) and has no "
            "`exitStatus` accepts `terminal/cancel`: the agent answers it with an empty result, "
            "not an error. Same encoding as `ACP-TOOLCANCEL-201`: no RFC keyword and no "
            "`initialize` marker, so the row is CAPABILITY, gated by `inferred:terminalCancel` "
            "(documentation-only) and SKIPPED when no terminal advertises `cancel` while running "
            "during the driven turn. The TCK sends the request only for such a terminal and "
            "treats a `-32602` that follows the terminal's own `exitStatus` as the legitimate "
            "`already exited` answer, not judged. `terminal/cancel` stops a real process; the "
            "TCK then sends `session/cancel` so no work is left running."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:600-605; "
            "schema/v2/schema.unstable.json#/$defs/CancelTerminalRequest; "
            "schema/v2/schema.unstable.json#/$defs/CancelTerminalResponse"
        ),
    ),
    Requirement(
        id="ACP-TERMCANCEL-202",
        tier=Tier.CAPABILITY,
        capability="inferred:terminalCancel",
        text=(
            "After it accepted `terminal/cancel`, the agent confirms with a `terminal_update` "
            "that sets `exitStatus` for that terminal. Gated by `inferred:terminalCancel` like "
            "`ACP-TERMCANCEL-201`; SKIPPED when no cancel was accepted. The `exitStatus` must "
            "arrive within half the run's per-response timeout."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:604; "
            "schema/v2/schema.unstable.json#/$defs/CancelTerminalRequest"
        ),
    ),
    Requirement(
        id="ACP-TERMCANCEL-203",
        tier=Tier.CAPABILITY,
        capability="inferred:terminalCancel",
        text=(
            "`terminal/cancel` sent with a child session's `sessionId` for a child terminal that "
            "currently advertises `capabilities.cancel` and has no `exitStatus` is accepted and "
            "confirmed like a terminal of the prompted session (`ACP-TERMCANCEL-201/202`): an "
            "empty result, then a `terminal_update` that sets `exitStatus`. `sessionId` is the "
            "session that reports the terminal, and the terminal's own `cancel` enables the "
            "request even when the child advertises no `cancel`. Same encoding and separate-row "
            "reason as `ACP-TOOLCANCEL-203`: CAPABILITY, gated by `inferred:terminalCancel` "
            "(documentation-only), judged over the child-cancel driven turn for the first child "
            "terminal that advertises `cancel` while running; SKIPs when none does, or it had "
            "already exited when the agent read the request. v2-only (`2xx`)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/tool-calls.mdx:600-605; "
            "schema/v2/schema.unstable.json#/$defs/CancelTerminalRequest; "
            "docs/rfds/subagents.mdx:1042-1045 (Active RFD)"
        ),
    ),
    Requirement(
        id="ACP-ENUM-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every value the agent emits at an open-enum site is a defined constant or begins "
            "with `_`: extensions MUST NOT define custom non-underscore values wherever the "
            "schema has a fallback branch (which accepts any string, so schema validation can't "
            "catch it). Sites checked: `session/update`'s `sessionUpdate` discriminator, "
            "`state_update.state`, `tool_call_update` (and a permission request's "
            "`subject.toolCall`) `kind`/`status`, tool-call content `type` (on "
            "`tool_call_update`, on a chunk's single `content` object, and on a `subject.toolCall`), "
            "`diff` content's `changes[].operation`/`changes[].fileType`/`patch.format`, "
            "`plan_update`'s `plan.type` and plan entries' `priority`/`status`, "
            "`available_commands_update` commands' `type`, a defined state's `background[].type`, "
            "and `session/request_permission` "
            "options' `kind` (the permission sites are only observable if the agent asks for "
            "permission). A curated, non-exhaustive subset of the schema's open-enum sites; "
            "`subject.type` is not checked."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:235-240; "
            "docs/protocol/v2/draft/tool-calls.mdx:76,372,419,662,685-686,700-701; "
            "docs/protocol/v2/draft/agent-plan.mdx:145,164,176; "
            "docs/protocol/v2/draft/slash-commands.mdx:110; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:209; "
            "schema/v2/schema.unstable.json#/$defs/BackgroundWork; "
            "schema/v2/schema.unstable.json#/$defs/PermissionOptionKind"
        ),
    ),
    Requirement(
        id="ACP-ENUM-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A `_`-prefixed value at an open-enum site the client sends (here: "
            "`session/request_permission`'s answered `outcome`, whose schema has an `other` "
            "fallback) is accepted by the agent -- no crash, the prompt is not answered with "
            "`-32602`, and the turn still reaches idle. Only survival is checked; that it is "
            "not treated as approval is `ACP-PERM-204`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:51-55,237,249; "
            "schema/v2/schema.unstable.json#/$defs/RequestPermissionOutcome/anyOf/2"
        ),
    ),
    Requirement(
        id="ACP-ENUM-204",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A prompt `resource` (embedded context) block whose `resource` carries neither "
            "`text` nor `blob` falls outside a closed site and is rejected with `-32602`, not "
            "accepted. ADVISORY because the rule has no RFC keyword. The test is gated on "
            "`capabilities.session.prompt.embeddedContext`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:242-245; "
            "docs/protocol/v2/draft/error.mdx:31; "
            "schema/v2/schema.unstable.json#/$defs/EmbeddedResourceResource"
        ),
    ),
    Requirement(
        id="ACP-EXT-001",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A `_`-prefixed custom method request receives *some* response -- a result, or "
            "an error with any code. The `-32601` code specifically is `ACP-JSONRPC-004`'s "
            "separate concern."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:165,174,187,231; "
            "docs/protocol/v2/draft/overview.mdx:223 (JSON-RPC 2.0 §4: every request gets a response)"
        ),
    ),
    Requirement(
        id="ACP-META-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A `session/prompt` request carrying a `_meta` object is accepted -- the turn "
            "still proceeds normally. Re-cited from v1 unchanged: `PromptRequest._meta` "
            "still exists in v2."
        ),
        citation=_cite("docs/protocol/v2/draft/extensibility.mdx:72,74,97-102,104"),
    ),
    Requirement(
        id="ACP-META-201",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Every `_meta` value the agent emits, anywhere in the transcript, is a JSON "
            "object or `null` -- never a string/array/number. New in v2; every `_meta` site "
            "in the schema is typed `[\"object\", \"null\"]`."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/UpdateSessionNotification/properties/_meta"
        ),
    ),
    Requirement(
        id="ACP-META-202",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A `session/prompt` whose `_meta` is not an object (probed with a string) is "
            "treated as if `_meta` were omitted: it is accepted and the turn reaches idle, "
            "not rejected. ADVISORY because the rule has no RFC keyword. The test is gated "
            "on `capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:74; "
            "schema/v2/schema.unstable.json#/$defs/PromptRequest/properties/_meta"
        ),
    ),
    Requirement(
        id="ACP-META-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Wherever the agent emits a `_meta` object with a root `traceparent`, `tracestate` "
            "or `baggage` key during an ordinary `session/new` + `session/prompt` exchange, "
            "the value is in the corresponding W3C format. `traceparent` is checked against "
            "the Trace Context grammar; `tracestate` and `baggage` are only checked to be "
            "strings. A `null` value is a metadata-patch removal (`:108-115`), not a value, and "
            "is not judged. SKIPs when the agent emits none of these keys."
        ),
        citation=_cite("docs/protocol/v2/draft/extensibility.mdx:97-100,108-115"),
    ),
    Requirement(
        id="ACP-META-204",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Every key of a `_meta` object the agent authors on an ACP-defined object (the "
            "`initialize` result's `capabilities` tree, response results, request/notification "
            "params, and a `session/update`'s `update`) is `traceparent`/`tracestate`/"
            "`baggage` or carries a reverse-DNS prefix ending in `/` whose second label is not "
            "`agentclientprotocol`: unprefixed keys and those prefixes are reserved for ACP "
            "(extension keys SHOULD be namespaced). `_meta` inside content blocks and tool "
            "output is not checked, since forwarded MCP content keeps MCP's own keys. SKIPs "
            "when the agent emits no `_meta` at those positions. The test is gated on "
            "`capabilities.session`."
        ),
        citation=_cite("docs/protocol/v2/draft/extensibility.mdx:102,259"),
    ),
    Requirement(
        id="ACP-EXT-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "An unrecognized `_`-prefixed *notification* sent to the agent gets no response "
            "and causes no crash (SHOULD-ignore) -- the v2 analogue of v1's "
            "`answers_notifications.py` defect pattern, generalised from `session/cancel` "
            "specifically to any custom notification. The same holds for `mcp/message` "
            "notifications (the unstable MCP-over-ACP envelope, well-formed and malformed) "
            "sent to an agent that does not advertise `capabilities.session.mcp.acp`, which "
            "has not recognized the method; those probes break client rules on purpose (the "
            "envelope is for an active request on a declared `acp` server, and `requestId` "
            "and `method` are required) because the spec defines how an agent treats a "
            "notification it does not recognize, and that probe SKIPs when `acp` is "
            "advertised."
        ),
        citation=_cite("docs/protocol/v2/draft/extensibility.mdx:231"),
    ),
    Requirement(
        id="ACP-EXT-202",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Vendor extensions the agent advertises live under `initialize` -> "
            "`result.capabilities._meta`, not as an unrecognized root key of `capabilities` "
            "itself."
        ),
        citation=_cite("docs/protocol/v2/draft/extensibility.mdx:253-261"),
    ),
    Requirement(
        id="ACP-EXT-204",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "The agent ignores unknown fields in the client's `initialize` params -- at the "
            "`capabilities` root, nested under `capabilities.auth`, and in `info` -- rather than "
            "rejecting the request, and an unknown field advertises nothing (no `type: "
            "\"terminal\"` auth method appears). The probe names are not `_`-prefixed, so they "
            "stand in for fields of a future ACP revision."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:156; "
            "docs/protocol/v2/draft/extensibility.mdx:51-52,157"
        ),
    ),
    Requirement(
        id="ACP-EXT-203",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "An unrecognized `$/`-prefixed protocol-level notification (standing in for one "
            "from a later ACP version) sent to the agent gets no response and causes no crash "
            "(SHOULD ignore)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:165,231; "
            "docs/protocol/v2/draft/error.mdx:44"
        ),
    ),
    Requirement(
        id="ACP-ERROR-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A JSON-RPC error's `message` is a non-empty, single-line string, and its "
            "optional `data` is well-formed JSON."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:6-10; docs/protocol/v2/draft/overview.mdx:223-227; "
            "schema/v2/schema.unstable.json#/$defs/Error"
        ),
    ),
    Requirement(
        id="ACP-ERROR-003",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/prompt` naming a session that does not exist, or that this connection "
            "already closed, gets error `-32002` with `data.sessionId` set to the requested id. "
            "The schema's `Other` error-data branch accepts anything, so `data.sessionId` is "
            "checked by hand."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:54-56; docs/protocol/v2/draft/session-setup.mdx:47-51; "
            "schema/v2/schema.unstable.json#/$defs/SessionNotFoundErrorData"
        ),
    ),
    Requirement(
        id="ACP-ERROR-004",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/set_config_option` naming a never-created session (probed when "
            "`session/new` returned `configOptions`), and `session/resume` of a `sessionId` the "
            "agent never created (a nonce id with the TCK's own `cwd`), get error `-32002` with "
            "`data.sessionId` set to the requested id, never a silent create-and-succeed. "
            "Judged with the same assertion as `ACP-ERROR-003`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:54-56; docs/protocol/v2/draft/session-setup.mdx:47-51; "
            "schema/v2/schema.unstable.json#/$defs/SessionNotFoundErrorData"
        ),
    ),
    Requirement(
        id="ACP-ERROR-006",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A standard method gated on a capability the agent did not advertise gets error "
            "`-32601`. Sent only for what is not advertised: the `session/*` baseline "
            "(`capabilities.session`), `session/delete`, `session/archive`/`session/unarchive`, "
            "`session/fork` and `providers/list`. "
            "A `-32000` reply FAILs, since an unadvertised method has no authentication surface. "
            "SKIPs when every probed capability is advertised."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:44,68; docs/protocol/v2/draft/overview.mdx:60,141-142"
        ),
    ),
    Requirement(
        id="ACP-ERROR-008",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Every error `code` the agent returns in `-32768..-32000` or `-32899..-32800` is one "
            "ACP defines (`ErrorCode`'s named members); implementation-specific errors use codes "
            "outside those ranges. Sampled from the error replies to an unrecognised method, "
            "and, when `capabilities.session` is advertised, a `session/new` missing `cwd` and a "
            "`session/prompt` for an unknown session; passes vacuously if no probe yields an error."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:38; schema/v2/schema.unstable.json#/$defs/ErrorCode"
        ),
    ),
    Requirement(
        id="ACP-ERROR-204",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "If the agent answers a non-JSON stdin line, the answer is an error response with "
            "`code: -32700` and `id: null`. Conditional: SKIPs when the agent stays silent or "
            "exits, since no rule obliges a reply and the probe itself breaks a client MUST NOT."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:28; docs/protocol/v2/draft/transports.mdx:24; "
            "schema/v2/schema.unstable.json#/$defs/AgentResponse"
        ),
    ),
    Requirement(
        id="ACP-SHUTDOWN-001",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "After the client closes stdin, the agent treats end of input as the end of the "
            "connection and SHOULD exit once it has finished or stopped its work, without "
            "needing SIGTERM/SIGKILL."
        ),
        citation=_cite("docs/protocol/v2/draft/transports.mdx:43"),
    ),
    Requirement(
        id="ACP-SCHEMA-002",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "No agent-authored request/notification `params` or response `result` carries an "
            "unrecognized root-level key. Re-cited from v1, with a v2-specific carve-out: "
            "unknown-root-key detection is skipped for any object matched by an `other` "
            "fallback branch, since an unknown/`_`-prefixed variant is by construction not "
            "\"a type that's part of the specification\" -- already implemented in "
            "`tck.v2.validation.find_unknown_root_keys`."
        ),
        citation=_cite("docs/protocol/v2/draft/extensibility.mdx:104,235-242"),
    ),
    Requirement(
        id="ACP-STDERR-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Stderr byte count is recorded for a human reading the report. The agent MAY "
            "write UTF-8 logging to stderr, so there is nothing to assert."
        ),
        citation=_cite("docs/protocol/v2/draft/transports.mdx:22"),
    ),
    Requirement(
        id="ACP-INFO-PARSE-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Behaviour on a malformed (non-JSON) stdin line is recorded, never asserted. "
            "`error.mdx` assigns `-32700` to non-JSON input but requires no reply, and the "
            "client MUST NOT send such a line; the shape of a reply the agent chooses to send "
            "is `ACP-ERROR-204`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:28; docs/protocol/v2/draft/transports.mdx:24 "
            "(the client MUST NOT send this, so agent behaviour is undefined)"
        ),
    ),
    Requirement(
        id="ACP-INFO-INVALIDREQ-001",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "Behaviour on a structurally-invalid (well-formed JSON, not a valid JSON-RPC "
            "envelope) request line is recorded, never asserted. `error.mdx` assigns `-32600` "
            "to a message that is not a valid request object but requires no reply, and the "
            "client MUST NOT send one; reference SDKs disagree (rust-sdk replies `-32600`, "
            "python-sdk stays silent)."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:29; docs/protocol/v2/draft/transports.mdx:24 "
            "(the client MUST NOT send this, so agent behaviour is undefined)"
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
