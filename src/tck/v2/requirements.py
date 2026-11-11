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
            "regardless of the negotiated `protocolVersion` -- unlike `ACP-INIT-203`/"
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
        id="ACP-INIT-209",
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
            "`-32600`). A retry after `-32022` is deliberately not exercised: that error asks "
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
            "in effect: a following unknown `_tck/...` request is not answered with `-32600`. "
            "Binds agents implementing v2: SKIPPED with `VERSION-MISMATCH` unless the main "
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
        id="ACP-INIT-203",
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
        id="ACP-PROMPT-205",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "Every `session/update` notification the agent emits during a `session/prompt` "
            "turn validates against the v2 schema and carries the prompted `sessionId`, or that "
            "of a child session already announced (in wire order) by a `subagent_update` on a "
            "known session -- child traffic before its announcement FAILs. "
            "Vacuous pass if the agent emits no updates during the turn. NOT a reuse of v1's "
            "`ACP-PROMPT-002`: the requirement text is the same schema/sessionId "
            "check, but the *tier* differs -- v1 registers it `Tier.MANDATORY` (v1's whole "
            "session surface is unconditional), whereas v2's `session/prompt` only exists once "
            "the agent has advertised the optional `capabilities.session` at all, exactly like "
            "`ACP-SESSION-001`/`002` above, so this row is `Tier.CAPABILITY`. A changed tier is "
            "a changed requirement under the id-reuse convention, so this gets a fresh 2xx id "
            "(`ACP-PROMPT-205`) instead of reusing `ACP-PROMPT-002`."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/UpdateSessionNotification/required; "
            "schema/v2/schema.unstable.json#/$defs/SessionUpdate; "
            "schema/v2/schema.unstable.json#/$defs/SubagentUpdate"
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
        id="ACP-PROMPT-206",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A prompt of `text` + `resource_link` content blocks is accepted (a non-error "
            "`session/prompt` result), and the turn ends: agents advertising `session` MUST "
            "support both block types, and `content.mdx` states the `resource_link` MUST for all "
            "agents. Replaces v1's ADVISORY `ACP-PROMPT-003`, whose recorded doc conflict does "
            "not exist in v2."
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
            "docs/rfds/v2/prompt.mdx:88"
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
            "when its own prompt capability is absent, and SKIPPED when advertised (that "
            "positive case is `ACP-PROMPTCAP-001..003`). A client never sends an unadvertised "
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
        id="ACP-CLIENTCAP-201",
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
            "docs/rfds/v2/prompt.mdx:88"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-201",
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
        id="ACP-CANCEL-202",
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
            "Shares its test and citation with `ACP-CLOSE-202` (the same wire evidence, bound "
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
            "(the session last reported `requires_action`) ends the work with an idle "
            "`stopReason: \"cancelled\"` without the client answering that request: the agent "
            "MUST stop waiting for it. The TCK leaves it unanswered and answers it `cancelled` "
            "only once the agent withdraws it with `$/cancel_request` (waiting for that answer "
            "is allowed) or the turn has ended. A turn that ends only after the TCK answers it "
            "at the deadline FAILs. SKIPPED when no permission request was pending when cancel "
            "was sent, or the session was not reported blocked."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:1153,1177,1185-1189; "
            "docs/protocol/v2/draft/cancellation.mdx:20,31,40-43; "
            "docs/protocol/v2/draft/tool-calls.mdx:326; "
            "schema/v2/schema.unstable.json#/$defs/RequestPermissionOutcome; "
            "schema/v2/schema.unstable.json#/$defs/CancelledPermissionOutcome"
        ),
    ),
    Requirement(
        id="ACP-CANCEL-210",
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
        id="ACP-CANCEL-212",
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
        id="ACP-TRANSPORT-201",
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
            "Notifications never receive a response, success or error. Messages the agent "
            "itself initiates (they carry `method`) are not responses."
        ),
        citation=_cite("docs/protocol/v2/draft/overview.mdx:10,227"),
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
            "also fails `ACP-TRANSPORT-201` (MANDATORY)."
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
        id="ACP-RESUME-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/resume` (no `replayFrom`) of a session obtained via the harness's "
            "three-route strategy (create, create-then-close, then a `session/list` entry created in "
            "the TCK's own `cwd`) succeeds with a schema-valid object result. `-32601` FAILs "
            "(B3 makes `session/resume` a baseline-mandatory method); any other error from all "
            "three routes SKIPs -- no route is spec-guaranteed to work."
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
        id="ACP-RESUME-203",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "With `replayFrom` omitted (or `null`), no conversation-history `session/update` for "
            "the resumed session arrives before the response. Vacuous -- and recorded, never "
            "FAILed on that account -- for an agent that retains no history to replay."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:179-184 (the current-state snapshot is live sync, not history)"
        ),
    ),
    Requirement(
        id="ACP-RESUME-204",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A retained user message inserted by `session/prompt` replays, if it replays at all, "
            "with the same `messageId` that prompt's response returned. A narrow, conditional "
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
            "During replay, a `*_chunk` update for a `messageId` is preceded, within the same "
            "replay window, by a matching whole-message update for that id carrying a `content` "
            "array -- `[]` when chunks rebuild the message from its beginning, or full content "
            "the chunks then append to (a client cannot tell the two apart). Vacuous -- "
            "recorded, never FAILed -- for an agent whose replay uses only whole-message "
            "updates."
        ),
        citation=_cite("docs/protocol/v2/draft/session-setup.mdx:299-312"),
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
            "against the v2 schema and carries the resumed `sessionId`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:207-209,221,282-284; "
            "schema/v2/schema.unstable.json#/$defs/UpdateSessionNotification"
        ),
    ),
    Requirement(
        id="ACP-RESUME-211",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/resume` of a `sessionId` the agent never created (a `_tck`-prefixed id "
            "with the TCK's own `cwd`) is rejected with `-32002` and `data.sessionId` set to "
            "the requested id, never silently accepted. Judged with the same assertion as "
            "`ACP-ERROR-201`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:54-56; docs/protocol/v2/draft/session-setup.mdx:47; "
            "schema/v2/schema.unstable.json#/$defs/SessionNotFoundErrorData"
        ),
    ),
    Requirement(
        id="ACP-LIST-201",
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
        id="ACP-LIST-202",
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
            "equals the requested `cwd` (a per-entry check only; the reverse direction -- that a "
            "session at that `cwd` is returned at all -- is not asserted, since no upstream "
            "statement guarantees a freshly created session appears in `session/list`)."
        ),
        citation=_cite("docs/protocol/v2/draft/session-list.mdx:63-68"),
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
        id="ACP-CLOSE-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "`session/close` of a live, idle session succeeds with a schema-valid empty-object "
            "result -- `session/close`'s own baseline contract, distinct from the cancellation "
            "side effect `ACP-CLOSE-202`/`ACP-CANCEL-208` covers."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:367-369,389-405; "
            "schema/v2/schema.unstable.json#/$defs/CloseSessionRequest; "
            "schema/v2/schema.unstable.json#/$defs/CloseSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-CLOSE-202",
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
            "`ACP-CLOSE-202`'s finding) or the close lost the race."
        ),
        citation=_cite("docs/protocol/v2/draft/session-setup.mdx:393"),
    ),
    Requirement(
        id="ACP-CLOSE-204",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "A `session/prompt` sent immediately before `session/close` (without awaiting its "
            "receipt) is answered either with `-32800` (closing prevented insertion) or with a "
            "success carrying a string `messageId` (already inserted) -- never another error, "
            "never left unanswered. ADVISORY rather than CAPABILITY: the outcome depends on how "
            "the agent schedules two back-to-back requests, so a failure here is reported but "
            "does not by itself fail the verdict."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:395; "
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:374"
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
        id="ACP-DELETE-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.delete",
        text=(
            "`session/delete` of an existing, already-closed session succeeds with a "
            "schema-valid empty-object result. The session is closed first because deleting an "
            "active session is implementation-defined."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-delete.mdx:35,57,74-86,95; "
            "schema/v2/schema.unstable.json#/$defs/DeleteSessionResponse"
        ),
    ),
    Requirement(
        id="ACP-DELETE-202",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.delete",
        text=(
            "After a successful `session/delete` of a closed session, the session no longer "
            "appears in `session/list` results. SKIPs when the closed session was never observed "
            "in `session/list` in the first place (nothing to compare against). :90 is a plain "
            "declarative, not an RFC keyword, but it is what `session/delete` means (mirrored by "
            "the sequence diagram), so this stays CAPABILITY."
        ),
        citation=_cite("docs/protocol/v2/draft/session-delete.mdx:27-28,90,95"),
    ),
    Requirement(
        id="ACP-DELETE-203",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "Deleting an already-deleted or never-created `sessionId` SHOULD succeed silently, "
            "rather than erroring -- verbatim re-cite of v1's `ACP-DELETE-002`, new capability "
            "path."
        ),
        citation=_cite("docs/protocol/v2/draft/session-delete.mdx:91"),
    ),
    Requirement(
        id="ACP-ADDDIRS-201",
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
        id="ACP-FORK-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.fork",
        text=(
            "`session/fork` of an existing session (same `cwd`) succeeds with a schema-valid "
            "result whose `sessionId` is a non-empty string distinct from the source session's."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/initialization.mdx:269-273; "
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
            "the turn reaches a terminating idle. Definitional prose without an RFC keyword."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:49; "
            "docs/protocol/v2/draft/error.mdx:54; "
            "docs/rfds/session-fork.mdx:67"
        ),
    ),
    Requirement(
        id="ACP-SYSPROMPT-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session.systemPrompt",
        text=(
            "`session/new` with `systemPrompt: {mode: \"append\", content: [<text block>]}` "
            "succeeds. Only this positive path is probed: the error paths (unadvertised mode, "
            "non-text content) would require the TCK to break a client MUST."
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
        id="ACP-MCP-201",
        tier=Tier.INFORMATIONAL,
        capability=None,
        text=(
            "INFORMATIONAL, not CAPABILITY, despite the underlying `capabilities.session.mcp."
            "stdio` marker: records whether `session/new` accepts a "
            "well-formed stdio MCP server entry when the marker is advertised. A connect failure "
            "against a harmless, possibly-nonexistent command is the agent's own business "
            "(\"Agents SHOULD connect\" has no client-observable surface in stable v2) and is not "
            "provably non-conformant, so this never asserts on the outcome."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:555-607,656,681; "
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
        id="ACP-CONFIG-201",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "Every `configOptions` entry in `session/new`'s result validates: `configId` and "
            "`name` are present, `type` selects the right shape (`select` requires `currentValue`"
            "+`options`; `boolean` requires `currentValue`), and a `select` entry's `options` is "
            "an array -- either a flat `SessionConfigSelectOption[]` or a grouped "
            "`SessionConfigSelectGroup[]`, never mixed (the schema sets no minimum length). Inferred support, same encoding as v1's "
            "`ACP-MODES-001`/`ACP-CONFIG-001` -- `capability=\"inferred:configOptions\"` is "
            "documentation-only."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/SessionConfigOption; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigId; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigOptionCategory; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigValueId; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelectOptions; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelectOption; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelectGroup; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigGroupId; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigSelect; "
            "schema/v2/schema.unstable.json#/$defs/SessionConfigBoolean; "
            "docs/protocol/v2/draft/session-config-options.mdx:93-154"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-202",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "`session/set_config_option` responds with the complete post-change `configOptions` "
            "list: an array, schema-valid, containing the changed `configId`. Whether every "
            "previously-advertised `configId` is still present is recorded, never asserted -- a "
            "change may legitimately remove dependent options, so a partial reply and a "
            "dependent removal are wire-identical. SKIPs when `session/new` advertised no "
            "`configOptions`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:291,367-371; "
            "docs/rfds/session-config-options.mdx:45; "
            "schema/v2/schema.unstable.json#/$defs/SetSessionConfigOptionResponse"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-203",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "`session/resume`'s `configOptions`, when present, validates the same way as "
            "`ACP-CONFIG-201` -- a new carrier in v2 (v1's `session/load` had no analogous "
            "field). The session is obtained the same way as `ACP-RESUME-201`, so a resume "
            "error other than `-32601` SKIPs."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-setup.mdx:108,333-335; "
            "schema/v2/schema.unstable.json#/$defs/ResumeSessionResponse/properties/configOptions"
        ),
    ),
    Requirement(
        id="ACP-CONFIG-204",
        tier=Tier.CAPABILITY,
        capability="inferred:configOptions",
        text=(
            "A `select`-type option's `currentValue` is one of its declared `options` values "
            "(flat or grouped) -- derived from C5's always-a-default-value MUST plus the field "
            "descriptions, not itself schema-enforced."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/session-config-options.mdx:116-133,222; "
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
            "docs/protocol/v2/draft/session-config-options.mdx:373-375,459; "
            "docs/rfds/session-config-options.mdx:45; "
            "schema/v2/schema.unstable.json#/$defs/ConfigOptionUpdate"
        ),
    ),
    Requirement(
        id="ACP-AUTH-201",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`authMethods[*].methodId` values are unique. Re-cites v1's `ACP-AUTH-001`; only "
            "the field name changed (`id` -> `methodId`)."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AuthMethod; "
            "schema/v2/schema.unstable.json#/$defs/AuthMethodId"
        ),
    ),
    Requirement(
        id="ACP-AUTH-202",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "No `authMethods[*]` entry with `type: \"terminal\"` is advertised unless the "
            "client advertised `capabilities.auth.terminal: {}` in `initialize`'s params. New "
            "id, not a reuse of v1's `ACP-AUTH-002` -- the client-capability path and its "
            "encoding both changed (v1: top-level boolean `clientCapabilities.auth.terminal`; "
            "v2: nested object marker `capabilities.auth.terminal`)."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AuthMethodTerminal; "
            "schema/v2/schema.unstable.json#/$defs/ClientAuthCapabilities; "
            "schema/v2/schema.unstable.json#/$defs/TerminalAuthCapabilities; "
            "docs/protocol/v2/draft/authentication.mdx:149-151"
        ),
    ),
    Requirement(
        id="ACP-AUTH-203",
        tier=Tier.CAPABILITY,
        capability="inferred:authMethods",
        text=(
            "`auth/logout` returns a non-error, schema-valid result. Support is inferred from "
            "a non-empty `authMethods` -- v2 has no `agentCapabilities.auth.logout` marker at "
            "all (unlike v1); `capability=\"inferred:authMethods\"` is documentation-only. "
            "Replaces v1's `ACP-AUTH-004` outright. Only actually exercised when "
            "`--allow-logout`/`--tck-allow-logout` is given (destructive: may revoke the "
            "operator's own credentials); SKIPs otherwise."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/LogoutAuthRequest; "
            "schema/v2/schema.unstable.json#/$defs/LogoutAuthResponse; "
            "schema/v2/schema.unstable.json#/$defs/AgentAuthCapabilities"
        ),
    ),
    Requirement(
        id="ACP-AUTH-204",
        tier=Tier.CAPABILITY,
        capability="inferred:authMethods",
        text=(
            "Given `--auth-method <id>` naming a non-`terminal`, advertised `methodId`, "
            "`auth/login` does not answer `-32601` (Method not found) -- an agent advertising "
            "`authMethods` MUST implement it -- and, when `capabilities.session` is "
            "advertised, a subsequent `session/new` does not fail with `-32000`. Mirrors v1's "
            "`ACP-AUTH-003`, method renamed `authenticate` -> `auth/login`. SKIPs when "
            "`--auth-method` was not given, the agent advertises no `authMethods`, or "
            "`auth/login` fails with any other error."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/authentication.mdx:51-53; "
            "schema/v2/schema.unstable.json#/$defs/LoginAuthRequest/required (`methodId`); "
            "schema/v2/schema.unstable.json#/$defs/LoginAuthResponse"
        ),
    ),
    Requirement(
        id="ACP-AUTH-205",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "`session/new` does not fail with `-32000` (AUTHENTICATION_REQUIRED) when "
            "`authMethods` is empty or absent. Re-cites v1's `ACP-AUTH-005`/AUTH-A1; not "
            "promoted. SKIPs unless `capabilities.session` is advertised."
        ),
        citation=_cite("docs/protocol/v2/draft/schema.mdx:954 (-32000 is a MAY, not a MUST)"),
    ),
    Requirement(
        id="ACP-AUTH-206",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "Every `authMethods[*].type` is one of the schema's defined discriminator values "
            "(`\"agent\"`, `\"terminal\"`) or begins with `_` -- the general open-enum "
            "extensibility rule applied to this field. New in v2: v1's `type` could default to "
            "\"agent\" when absent and had no enum-closure rule at all."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/authentication.mdx:118-120; "
            "docs/protocol/v2/draft/extensibility.mdx:233-242; "
            "schema/v2/schema.unstable.json#/$defs/AuthMethod"
        ),
    ),
    Requirement(
        id="ACP-AUTH-207",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "On a connection that advertised `capabilities.auth.terminal: {}`, every "
            "`type: \"terminal\"` entry's `args` (if present; `null` counts as omitted) is an array "
            "of strings, `env` (if present; `null` counts as omitted) is an array of well-formed "
            "`EnvVariable` objects (`name`/`value` both required strings), and `env` entries' `name`s are unique within that "
            "descriptor. Conditional on at least one terminal entry actually appearing; SKIPs "
            "otherwise. New in v2 -- v1's terminal auth descriptor had no `args`/`env` fields."
        ),
        citation=_cite(
            "schema/v2/schema.unstable.json#/$defs/AuthMethodTerminal/properties/env (\"Names MUST be "
            "unique\"); schema/v2/schema.unstable.json#/$defs/EnvVariable; "
            "docs/protocol/v2/draft/authentication.mdx:203-205"
        ),
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
            "The first `tool_call_update` observed for a given `toolCallId` includes a "
            "non-empty `title`; `name`, if ever set, does not change across subsequent "
            "updates for the same id. Kept ADVISORY, not promoted to CAPABILITY under the "
            "session-baseline tiering rule -- the "
            "corresponding test is still `@pytest.mark.capability(\"capabilities.session\")`-"
            "gated for its own SKIP."
        ),
        citation=_cite("docs/protocol/v2/draft/tool-calls.mdx:41-54"),
    ),
    Requirement(
        id="ACP-PATCH-209",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "When the agent sends `session/request_permission` for the prompted session during "
            "a turn, it reports `state_update.state == \"requires_action\"` for that session "
            "at some point in the turn (SHOULD). What follows it is `ACP-STATE-205`'s MUST. "
            "The test is gated on `capabilities.session`."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/prompt-lifecycle.mdx:153,845,1074; "
            "docs/protocol/v2/draft/tool-calls.mdx:209"
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
            "`available_commands_update` commands' `type`, and `session/request_permission` "
            "options' `kind` (the permission sites are only observable if the agent asks for "
            "permission). A curated, non-exhaustive subset of the schema's open-enum sites; "
            "`subject.type` is not checked."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/extensibility.mdx:235-240; "
            "docs/protocol/v2/draft/tool-calls.mdx:76,372,419,662,685-686,700-701; "
            "docs/protocol/v2/draft/agent-plan.mdx:145,164,176; "
            "docs/protocol/v2/draft/slash-commands.mdx:110; "
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
            "`-32602`, and the turn still reaches idle. Untestable how the agent treats the "
            "value internally; only survival is checked."
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
            "strings. SKIPs when the agent emits none of these keys."
        ),
        citation=_cite("docs/protocol/v2/draft/extensibility.mdx:97-100"),
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
        id="ACP-EXT-201",
        tier=Tier.ADVISORY,
        capability=None,
        text=(
            "An unrecognized `_`-prefixed *notification* sent to the agent gets no response "
            "and causes no crash (SHOULD-ignore) -- the v2 analogue of v1's "
            "`answers_notifications.py` defect pattern, generalised from `session/cancel` "
            "specifically to any custom notification."
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
        id="ACP-ERROR-201",
        tier=Tier.CAPABILITY,
        capability="capabilities.session",
        text=(
            "A session-scoped request naming a session that does not exist or is not active on "
            "the connection gets error `-32002` with `data.sessionId` set to the requested id. "
            "Probes: `session/prompt` for a never-created id and for a session this connection "
            "already closed; `session/set_config_option` for a never-created id, when "
            "`session/new` returned `configOptions`. The schema's `Other` error-data branch "
            "accepts anything, so `data.sessionId` is checked by hand."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:54-56; docs/protocol/v2/draft/session-setup.mdx:47-51; "
            "schema/v2/schema.unstable.json#/$defs/SessionNotFoundErrorData"
        ),
    ),
    Requirement(
        id="ACP-ERROR-202",
        tier=Tier.MANDATORY,
        capability=None,
        text=(
            "A standard method gated on a capability the agent did not advertise gets error "
            "`-32601`. Sent only for what is not advertised: the `session/*` baseline "
            "(`capabilities.session`), `session/delete`, `session/fork` and `providers/list`. "
            "A `-32000` reply FAILs, since an unadvertised method has no authentication surface. "
            "SKIPs when every probed capability is advertised."
        ),
        citation=_cite(
            "docs/protocol/v2/draft/error.mdx:44,68; docs/protocol/v2/draft/overview.mdx:60,141-142"
        ),
    ),
    Requirement(
        id="ACP-ERROR-203",
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
