"""Shared core for the conforming ACP v2 (Draft) fixture agent.

Not part of the installed `tck` package: fixture scripts are launched as standalone
subprocesses (`python .../conforming.py`), so they import this module by inserting their own
directory onto `sys.path` rather than a package-relative import. Independent of v1's `_base.py`.

Wire shapes come from the vendored `src/tck/v2/schema/schema.unstable.json` -- verify against it,
not memory, before changing a field name. v2 renames vs. v1: the agent's identity is `info` (not
`agentInfo`) and its capabilities are `capabilities` (not `agentCapabilities`).

Negotiates as a v2-only endpoint (`_handle_initialize`): a malformed `protocolVersion` gets
`-32602`, one below 2 gets `-32022` with `data: {requested, supported: [2]}`, and 2 or above
selects 2. A failed `initialize` leaves the connection uninitialized: every other request gets
`-32600` and notifications are ignored (`_require_initialize`), until a retried `initialize`
succeeds. A second `initialize` is handled like the first until another request arrives; after
that it gets `-32600` (initialization.mdx:135-141, error.mdx:60). The agent sends nothing while
uninitialized.

Implements the full `capabilities.session` baseline (advertising `session`, even as `{}`, commits
the agent to `session/new`, `list`, `resume`, `close`, `prompt`, `cancel`, `update`), plus:

- `__hang__` cancel sentinel (as in v1's `conforming.py`): a prompt that is a single `__hang__`
  text block withholds its terminating idle update until `session/cancel` (`_handle_cancel`) or
  `session/close` (`_handle_close_session`) arrives. It runs before `_mid_turn_action`,
  preempting it for that prompt only. A prompt arriving while a session hangs is held, not
  inserted (`_prompt_while_busy`), and `session/cancel`/`session/close` answer every held prompt
  `-32800` (`_cancel_held_prompts`) before the handler runs, so a fixture overriding
  `_handle_cancel`/`_handle_close_session` keeps that behaviour.
- No batches (`transports.mdx:67`): any top-level JSON array line (empty or not) is rejected with
  one `-32600`/`id: null` object and no element is processed (`_handle_batch`, the hook that
  array-handling defect fixtures override).
- `session/resume` replay: each `session/update` is recorded per session (`_record_history`);
  `replayFrom: {"type": "start"}` replays it verbatim, omitted/`null` replays nothing, and any
  other or malformed cursor gets `-32602` (`_replay_from_rejection`). Every successful resume
  sends a `session_info_update` (`_send_resume_session_info`) and a current-state `state_update`
  (`_send_resume_snapshot`) before the response. Resume
  accepts a session that is live or closed on this connection (the routes
  `_helpers.obtain_resumable_session` tries first), and answers any other id with `-32002`
  (`_unknown_session`). The first `*_chunk` update for a `messageId`
  is preceded by a synthesized whole-message primer (`content: []`), which keeps history
  schema-correct for chunk-emitting subclasses. Each step is an overridable hook so the
  `resume_*.py` defect fixtures can break exactly one.
- `session/close` keeps the session in `session/list` (resumable) but refuses further prompts.
  `session/delete` (only when `capabilities.session.delete` is advertised, else `-32601`) removes
  it entirely, first cancelling a hanging `__hang__` turn as close does; an unknown id succeeds
  silently.
- `session/list` rejects a relative `cwd` filter (`_list_cwd_rejection`) and any cursor
  (`_list_cursor_rejection`, since it never issues one) with `-32602`; each is an overridable hook.
- A session-scoped request (`session/prompt`, `session/set_config_option`, `session/resume`)
  naming a session that is not active is answered by `_unknown_session`: `-32002` with
  `data.sessionId` (`error.mdx:54-56`). Defect fixtures override it, or the handlers, to break it.
  `session/close` and `session/delete` of an unknown id still succeed.
- `session/fork` (only when `capabilities.session.fork` is advertised) creates a live session with
  a copy of the source's history; a source it never created is `-32002` via `_unknown_session`.
  `systemPrompt` on `session/new` and `session/resume` is
  accepted only in an advertised mode with text content, else `-32602` and the session is
  neither created nor resumed (session-setup.mdx:481).
- `persist_sessions` (opt-in, default `False`): each created session's `cwd` is also written to
  `<cwd>/.tck-fixture-sessions.json`, so `session/resume` on a fresh process can restore it
  (`_restore`; history and closed state are not persisted). Off by default because it writes a
  file into the session's `cwd`.
- `session/new`/`session/resume` params are validated by `_setup_rejection`, each rule an
  overridable hook so a defect fixture can drop exactly one: a relative `cwd` (`_cwd_rejection`,
  session-setup.mdx:524), a relative `additionalDirectories` entry when the capability is
  advertised (`_additional_directories_rejection`, :443), an MCP transport that is not
  advertised under `session.mcp` (`_mcp_transport_rejection`, :545) and duplicate MCP server
  names (`_mcp_duplicate_name_rejection`, :547) -- all `-32602`. Stdio MCP servers of a
  successful `session/new` are launched and sent an MCP `initialize` (`_launch_mcp_servers`), so
  the TCK's stub server can observe the connection.
- `session/set_config_option` updates `currentValue` and replies with the complete list;
  `session/new`/`session/resume`/`session/fork` include `configOptions` (and `availableCommands`,
  from the opt-in `available_commands` argument) whenever any are configured
  (`_initial_state_fields`, session-setup.mdx:108).
  A valid `additionalDirectories`/`mcpServers` is accepted and otherwise ignored.
- `emit_rich_turn_updates` (opt-in, default `False`; only `conforming_full.py` sets it):
  `_send_rich_turn_updates` fires once per turn after the running update, emitting two
  `agent_message_chunk`s sharing a `messageId`, a `tool_call_update` create plus a content patch,
  a one-entry `plan_update`, a `terminal_update` + `terminal_output_chunk` sharing a
  `terminalId`, and an `available_commands_update` -- the content patch also carries a `diff`
  item -- so the patch/enum requirements observe something instead of SKIPping.
  `AsksPermissionAgent` also reports `requires_action`/`running` around its permission request.
- `report_background_work` (opt-in, default `False`; only `reports_background_work.py` and the
  `background_*.py` defect fixtures set it): every `state_update` carries the session's
  `background` list (`_with_background`), and each turn that does not end `cancelled` runs one
  background tool call (`_run_background_work`): announced, listed on a repeated `running`
  snapshot, then finalized, so the turn-ending idle removes it (prompt-lifecycle.mdx:203-206).
- `background_on_resume` (opt-in, default `False`, needs `report_background_work`): every
  resume leaves the session with one unfinished background tool call, listed on the snapshot and
  announced by a `tool_call_update` before it (`_resume_background`, session-setup.mdx:346).
- `terminal_auth_method`: appended to `authMethods` only when the `initialize` request's
  `capabilities.auth.terminal` object marker is present (the same gate the conformance test
  applies), so the default connection stays the negative control while a positive-capability
  connection sees it.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 2
UNSUPPORTED_PROTOCOL_VERSION = -32022


def _is_well_formed_protocol_version(value: Any) -> bool:
    """`ProtocolVersion` is a uint16; anything else is malformed and gets `-32602`."""
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 65535


class ConformingAgent:
    """A minimal, deterministic, offline ACP v2 agent.

    Handles `initialize` (v2-only negotiation, see `_handle_initialize`) and the full
    `capabilities.session` baseline: `session/new`, `session/list`, `session/resume`,
    `session/close`, `session/prompt`, `session/cancel`. Any other method gets `-32601`. Exits
    cleanly on stdin EOF (the `for` loop over `sys.stdin` simply ends).

    `capabilities`, if given, is merged verbatim into the `initialize` result's `capabilities`
    (empty by default, which advertises no `session` support; `{"session": {}}` commits the agent
    to the baseline session methods).
    """

    # A request other than `initialize` before initialization completes gets `-32600`
    # (error.mdx:60). `serves_before_initialize.py` switches it off.
    _require_initialize = True
    # A repeated `initialize` after another request gets `-32600` (error.mdx:60).
    # `accepts_initialize_after_request.py` switches it off.
    _reject_late_initialize = True
    # A repeated `initialize` before any other request is handled like the first
    # (initialization.mdx:137-139). `rejects_repeated_initialize.py` switches it off.
    _allow_repeated_initialize = True
    # A failed `initialize` can be retried (initialization.mdx:92).
    # `no_retry_after_failed_initialize.py` switches it off.
    _allow_initialize_retry = True

    # Versions reported in a `-32022`'s `data.supported`. A subclass that answers other versions
    # itself (e.g. `conforming_dual.py`) widens this.
    SUPPORTED_VERSIONS: tuple[int, ...] = (PROTOCOL_VERSION,)

    # `sessionUpdate` kinds that belong to the replayable conversation history, split into
    # whole-message and their `_chunk` counterparts.
    _WHOLE_MESSAGE_KINDS = {"user_message", "agent_message", "agent_thought"}
    _CHUNK_MESSAGE_KINDS = {"user_message_chunk", "agent_message_chunk", "agent_thought_chunk"}

    def __init__(
        self,
        *,
        capabilities: dict[str, Any] | None = None,
        agent_name: str = "tck-fixture-conforming-v2",
        config_options: list[dict[str, Any]] | None = None,
        auth_methods: list[dict[str, Any]] | None = None,
        require_auth: bool = False,
        emit_rich_turn_updates: bool = False,
        terminal_auth_method: dict[str, Any] | None = None,
        report_background_work: bool = False,
        persist_sessions: bool = False,
        available_commands: list[dict[str, Any]] | None = None,
        background_on_resume: bool = False,
    ) -> None:
        self._persist_sessions = persist_sessions
        self._available_commands: list[dict[str, Any]] = [dict(cmd) for cmd in (available_commands or [])]
        self._background_on_resume = background_on_resume
        self._session_count = 0
        self._message_count = 0
        self._tool_call_count = 0
        self._plan_count = 0
        self._terminal_count = 0
        self._emit_rich_turn_updates = emit_rich_turn_updates
        self._report_background_work = report_background_work
        self._background: dict[Any, list[dict[str, Any]]] = {}  # sessionId -> listed items
        self._capabilities = capabilities if capabilities is not None else {}
        self._agent_name = agent_name
        self._sessions: dict[str, str] = {}  # live sessionId -> cwd
        self._closed_sessions: dict[str, str] = {}  # closed but still listed sessionId -> cwd
        self._hanging_sessions: dict[Any, bool] = {}  # sessionId -> awaiting session/cancel
        # sessionId -> (id, params) of each prompt held while that session hangs, in order
        self._held_prompts: dict[Any, list[tuple[Any, dict[str, Any]]]] = {}
        # `session/new`/`session/resume`'s `configOptions`, mutated in place by
        # `session/set_config_option` (each entry's own dict, deep-copied from the constructor
        # argument so callers can safely reuse the same literal across several agent instances).
        self._config_options: list[dict[str, Any]] = [dict(opt) for opt in (config_options or [])]
        self._mcp_processes: list[subprocess.Popen] = []  # launched stdio MCP servers
        self._history: dict[str, list[dict[str, Any]]] = {}  # sessionId -> replayable updates
        self._primed_message_ids: dict[str, set[Any]] = {}  # sessionId -> messageIds already primed
        # `initialize`'s `authMethods` -- `auth/login`/`auth/logout` keyed by `methodId` (v1
        # keyed the equivalent field `id`; v2 renamed it, see
        # `schema/v2/schema.unstable.json#/$defs/AuthMethodId`). `require_auth` mirrors v1's `_base.py`: `session/new` errors
        # with `-32000` until a successful `auth/login` flips `self._authenticated`.
        self._auth_methods = auth_methods
        self._require_auth = require_auth
        self._authenticated = False
        # A `type: "terminal"` descriptor to append to `authMethods`, but only
        # for a connection whose `initialize` request actually advertised
        # `capabilities.auth.terminal` (see `_initialize_result`/`_client_wants_terminal_auth`
        # below) -- `ACP-AUTH-202`'s own gate, so this never leaks onto the default connection.
        self._terminal_auth_method = terminal_auth_method
        # Initialization completes with the first successful `initialize` response (`_reply`);
        # it stays in effect when a later `initialize` fails. `_request_seen` closes the repeat
        # window: set by the first request other than `initialize` on an initialized connection.
        # `_init_failed` is set by a failed `initialize`.
        self._initialized = False
        self._init_failed = False
        self._request_seen = False
        self._pending_initialize: tuple[Any] | None = None  # (id,) of the `initialize` in flight

    def run(self) -> None:
        for raw_line in sys.stdin:
            line = raw_line.rstrip("\n")
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self._handle_malformed_line()
                continue
            if isinstance(message, dict):
                self._handle(message)
            elif isinstance(message, list):
                self._handle_batch(message)

    def _handle_malformed_line(self) -> None:
        """A non-JSON stdin line: ignored by default (no rule requires a reply, and the client
        must not send one). Hook for fixtures that answer it."""

    def _handle_batch(self, items: list[Any]) -> None:
        """ACP has no batches: any array, empty or not, is one Invalid Request answered with a
        single error object (`id: null`); no element is dispatched."""
        self._write_line(
            {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
        )

    def _handle(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        if method is None:
            self._handle_response(message)
            return
        params = message.get("params") or {}
        if method == "initialize":
            if "id" in message and not self._initialize_refused(message["id"]):
                self._pending_initialize = (message["id"],)
                self._handle_request(method, message["id"], params)
                if self._pending_initialize is not None:  # no success reply was written
                    self._init_failed = True
                    self._pending_initialize = None
            return
        if self._require_initialize and not self._initialized:
            if "id" in message:
                self._error(message["id"], -32600, "Invalid Request: connection not initialized")
            return
        if "id" in message:
            self._request_seen = True
            self._handle_request(method, message["id"], params)
        elif method == "session/cancel":
            self._cancel_held_prompts(params.get("sessionId"))
            self._handle_cancel(params)

    def _prompt_while_busy(self, msg_id: Any, params: dict[str, Any]) -> None:
        """A prompt for a session whose `__hang__` prompt is still running: held until the hang
        ends (prompt-lifecycle.mdx:382-384). The hang only ends by cancel or close, which answer
        it `-32800`, so a held prompt is never inserted."""
        self._held_prompts.setdefault(params.get("sessionId"), []).append((msg_id, params))

    def _cancel_held_prompts(self, session_id: Any) -> None:
        """Answer every prompt held for `session_id` `-32800`: `session/cancel` and
        `session/close` cover prompts not yet inserted (prompt-lifecycle.mdx:384,1173)."""
        for msg_id, _ in self._held_prompts.pop(session_id, []):
            self._error(msg_id, -32800, "Request cancelled")

    def _initialize_refused(self, msg_id: Any) -> bool:
        """Answer an `initialize` this connection must not take, and return `True`: one repeated
        after another request, a repeat before any other request, or a retry after a failure,
        each unless its fixture switch is off."""
        if self._initialized and self._request_seen and self._reject_late_initialize:
            self._error(msg_id, -32600, "Invalid Request: initialize repeated after another request")
            return True
        if self._initialized and not self._request_seen and not self._allow_repeated_initialize:
            self._error(msg_id, -32600, "Invalid Request: initialize repeated")
            return True
        if self._init_failed and not self._initialized and not self._allow_initialize_retry:
            self._error(msg_id, -32600, "Invalid Request: connection not initialized")
            return True
        return False

    def _handle_response(self, message: dict[str, Any]) -> None:
        """Hook for a subclass that itself sent an agent -> client request mid-turn (a
        permission request, or an arbitrary probe method) to notice the client's reply and
        resume the turn. No-op by default -- `ConformingAgent` itself never sends one."""
        pass

    def _handle_cancel(self, params: dict[str, Any]) -> None:
        """`session/cancel` notification: resolve a hanging `__hang__` prompt (see
        `_handle_prompt`/`_is_hang_prompt`) for this session as `cancelled`. No-op if this
        session has no such prompt outstanding -- e.g. every non-hang prompt, which always
        finishes on its own before `session/cancel` could ever be sent."""
        session_id = params.get("sessionId")
        if self._hanging_sessions.pop(session_id, None) is not None:
            self._finish_turn(session_id, "cancelled")

    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method == "initialize":
            self._handle_initialize(msg_id, params)
        elif method == "session/new":
            self._handle_new_session(msg_id, params)
        elif method == "session/list":
            self._handle_list_sessions(msg_id, params)
        elif method == "session/resume":
            self._handle_resume_session(msg_id, params)
        elif method == "session/close":
            self._cancel_held_prompts(params.get("sessionId"))
            self._handle_close_session(msg_id, params)
        elif method == "session/delete" and self._session_capability("delete") is not None:
            self._handle_delete_session(msg_id, params)
        elif method == "session/fork" and self._session_capability("fork") is not None:
            self._handle_fork_session(msg_id, params)
        elif method == "session/set_config_option":
            self._handle_set_config_option(msg_id, params)
        elif method == "session/prompt":
            self._handle_prompt(msg_id, params)
        elif method == "auth/login":
            self._handle_login(msg_id, params)
        elif method == "auth/logout":
            self._handle_logout(msg_id, params)
        else:
            self._error(msg_id, -32601, "Method not found")

    def _handle_initialize(self, msg_id: Any, params: dict[str, Any]) -> None:
        """v2-only negotiation (initialization.mdx:108-112): a malformed `protocolVersion` gets
        `-32602`; one below 2 gets `-32022`; 2 or above selects 2. Only the success reply
        initializes the connection (`_reply`)."""
        requested = params.get("protocolVersion")
        if not _is_well_formed_protocol_version(requested):
            self._error(msg_id, -32602, "Invalid params: protocolVersion must be an integer in 0..65535")
            return
        if requested < PROTOCOL_VERSION:
            self._reject_unsupported_version(msg_id, requested)
            return
        self._reply(msg_id, self._initialize_result(params))

    def _reject_unsupported_version(self, msg_id: Any, requested: int) -> None:
        self._write(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": UNSUPPORTED_PROTOCOL_VERSION,
                    "message": "Unsupported protocol version",
                    "data": {"requested": requested, "supported": list(self.SUPPORTED_VERSIONS)},
                },
            }
        )

    def _initialize_result(self, params: dict[str, Any]) -> dict[str, Any]:
        """The v2 `initialize` result (protocolVersion 2)."""
        result: dict[str, Any] = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": dict(self._capabilities),
            "info": {"name": self._agent_name, "version": "0.0.0"},
        }
        auth_methods = list(self._auth_methods) if self._auth_methods is not None else []
        if self._terminal_auth_method is not None and self._client_wants_terminal_auth(params):
            auth_methods.append(self._terminal_auth_method)
        if auth_methods:
            result["authMethods"] = auth_methods
        return result

    @staticmethod
    def _client_wants_terminal_auth(params: dict[str, Any]) -> bool:
        """`ACP-AUTH-202`'s own object-marker gate, mirrored here: `True` iff
        the `initialize` request's `capabilities.auth.terminal` path resolves to a present,
        non-`null` value (an empty object still counts)."""
        capabilities = params.get("capabilities")
        if not isinstance(capabilities, dict):
            return False
        auth = capabilities.get("auth")
        if not isinstance(auth, dict):
            return False
        return auth.get("terminal") is not None

    def _handle_login(self, msg_id: Any, params: dict[str, Any]) -> None:
        method_id = params.get("methodId")
        valid_ids = {m.get("methodId") for m in (self._auth_methods or [])}
        if not isinstance(method_id, str) or method_id not in valid_ids:
            self._error(msg_id, -32602, "Invalid params: unknown or missing methodId")
            return
        self._authenticated = True
        self._reply(msg_id, {})

    def _handle_logout(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._authenticated = False
        self._reply(msg_id, {})

    def _session_capability(self, name: str) -> Any:
        session = self._capabilities.get("session")
        return session.get(name) if isinstance(session, dict) else None

    def _system_prompt_rejection(self, system_prompt: Any) -> str | None:
        """Why `systemPrompt` cannot be applied, or `None` if it can (or is absent). Only an
        advertised mode with text-only content is accepted (session-setup.mdx:474-481)."""
        if system_prompt is None:
            return None
        advertised = self._session_capability("systemPrompt")
        if advertised is None:
            return "systemPrompt is not supported"
        modes = {"append"}
        if isinstance(advertised, dict) and (advertised.get("mode") or {}).get("override") is not None:
            modes.add("override")
        if not isinstance(system_prompt, dict) or system_prompt.get("mode") not in modes:
            return "unsupported systemPrompt mode"
        content = system_prompt.get("content")
        if not isinstance(content, list) or not all(
            isinstance(block, dict) and block.get("type") == "text" for block in content
        ):
            return "unsupported systemPrompt content"
        return None

    def _setup_rejection(self, params: dict[str, Any]) -> str | None:
        """Why a `session/new`/`session/resume` request must be answered `-32602`, or `None`."""
        return (
            self._cwd_rejection(params.get("cwd"))
            or self._additional_directories_rejection(params.get("additionalDirectories"))
            or self._mcp_transport_rejection(params.get("mcpServers"))
            or self._mcp_duplicate_name_rejection(params.get("mcpServers"))
        )

    @staticmethod
    def _cwd_rejection(cwd: Any) -> str | None:
        if isinstance(cwd, str) and not os.path.isabs(cwd):
            return "cwd must be an absolute path"
        return None

    def _additional_directories_rejection(self, directories: Any) -> str | None:
        """Agents that advertise `session.additionalDirectories` reject a non-absolute entry;
        the field is ignored otherwise (session-setup.mdx:443)."""
        if self._session_capability("additionalDirectories") is None:
            return None
        if isinstance(directories, list) and any(
            not isinstance(entry, str) or not os.path.isabs(entry) for entry in directories
        ):
            return "additionalDirectories entries must be absolute paths"
        return None

    def _mcp_transport_rejection(self, servers: Any) -> str | None:
        """Only `stdio` and `http`, each only when advertised under `session.mcp`, are supported;
        anything else (`sse`, an unadvertised or reserved type) is rejected (:545)."""
        advertised = self._session_capability("mcp")
        supported = {
            transport
            for transport in ("stdio", "http")
            if isinstance(advertised, dict) and advertised.get(transport) is not None
        }
        for server in servers if isinstance(servers, list) else []:
            transport = server.get("type") if isinstance(server, dict) else None
            if transport not in supported:
                return f"unsupported MCP server transport {transport!r}"
        return None

    @staticmethod
    def _mcp_duplicate_name_rejection(servers: Any) -> str | None:
        if not isinstance(servers, list):
            return None
        names = [server.get("name") for server in servers if isinstance(server, dict)]
        if len(names) != len(set(names)):
            return "MCP server names must be unique"
        return None

    def _launch_mcp_servers(self, servers: list[Any]) -> None:
        """Launch every stdio MCP server entry and send it an MCP `initialize` request, so the
        TCK's stub server can observe the connection (`ACP-MCP-205`). The reply is discarded; the
        child exits on its own once this process's end of its stdin closes."""
        for server in servers:
            if not isinstance(server, dict) or server.get("type") != "stdio":
                continue
            if not server.get("command"):
                continue
            env = dict(os.environ)
            for var in server.get("env") or []:
                if isinstance(var, dict):
                    env[str(var.get("name"))] = str(var.get("value"))
            try:
                proc = subprocess.Popen(
                    [server["command"], *server.get("args", [])],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=env,
                )
                initialize = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": self._agent_name, "version": "0.0.0"},
                    },
                }
                proc.stdin.write((json.dumps(initialize) + "\n").encode())
                proc.stdin.flush()
            except OSError:
                continue
            self._mcp_processes.append(proc)

    def _before_new_response(self, session_id: str) -> None:
        """Hook: runs after the session exists and before the `session/new` response. Nothing is
        sent by default (session-setup.mdx:103)."""

    def _new_session_result(self, session_id: str) -> dict[str, Any]:
        return {"sessionId": session_id, **self._initial_state_fields()}

    def _initial_state_fields(self) -> dict[str, Any]:
        """`configOptions`/`availableCommands` for a setup response, each only when the session
        has any (session-setup.mdx:108, 134)."""
        fields: dict[str, Any] = {}
        if self._config_options:
            fields["configOptions"] = self._current_config_options()
        if self._available_commands:
            fields["availableCommands"] = [dict(cmd) for cmd in self._available_commands]
        return fields

    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        if self._require_auth and not self._authenticated:
            self._error(msg_id, -32000, "Authentication required")
            return
        rejection = self._setup_rejection(params) or self._system_prompt_rejection(
            params.get("systemPrompt")
        )
        if rejection is not None:
            self._error(msg_id, -32602, f"Invalid params: {rejection}")
            return
        self._session_count += 1
        session_id = f"sess-{self._session_count:04d}"
        self._sessions[session_id] = params.get("cwd", "")
        self._persist(session_id)
        self._launch_mcp_servers(params.get("mcpServers") or [])
        self._before_new_response(session_id)
        self._reply(msg_id, self._new_session_result(session_id))

    @staticmethod
    def _store_path(cwd: Any) -> Path | None:
        return Path(cwd) / ".tck-fixture-sessions.json" if isinstance(cwd, str) and cwd else None

    @staticmethod
    def _read_store(path: Path) -> dict[str, str]:
        try:
            stored = json.loads(path.read_text())
        except (OSError, ValueError):
            return {}
        return stored if isinstance(stored, dict) else {}

    def _persist(self, session_id: str) -> None:
        cwd = self._sessions.get(session_id)
        path = self._store_path(cwd)
        if not self._persist_sessions or path is None:
            return
        stored = self._read_store(path)
        stored[session_id] = cwd
        path.write_text(json.dumps(stored))

    def _restore(self, session_id: Any, cwd: Any) -> bool:
        """Bring a session persisted by an earlier process into `_sessions`, if there is one.
        Returns whether it was restored by this call."""
        path = self._store_path(cwd)
        if not self._persist_sessions or path is None or not isinstance(session_id, str):
            return False
        if session_id in self._sessions or session_id in self._closed_sessions:
            return False
        stored_cwd = self._read_store(path).get(session_id)
        if not isinstance(stored_cwd, str):
            return False
        self._sessions[session_id] = stored_cwd
        return True

    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        # All params optional; `SessionInfo` requires only `sessionId`/`cwd`. Filter by `cwd`
        # when given ("returns the first page" is trivially satisfied here -- no pagination, ever).
        rejection = self._list_cwd_rejection(params.get("cwd")) or self._list_cursor_rejection(
            params.get("cursor")
        )
        if rejection is not None:
            self._error(msg_id, -32602, f"Invalid params: {rejection}")
            return
        cwd_filter = params.get("cwd")
        sessions = [
            {"sessionId": session_id, "cwd": cwd}
            for session_id, cwd in {**self._closed_sessions, **self._sessions}.items()
            if cwd_filter is None or cwd == cwd_filter
        ]
        self._reply(msg_id, {"sessions": sessions})

    @staticmethod
    def _list_cwd_rejection(cwd: Any) -> str | None:
        """Hook: a `cwd` filter must be an absolute path; a relative one is `-32602`
        (`ACP-LIST-205`)."""
        if cwd is None or (isinstance(cwd, str) and os.path.isabs(cwd)):
            return None
        return f"cwd filter must be an absolute path, got {cwd!r}"

    @staticmethod
    def _list_cursor_rejection(cursor: Any) -> str | None:
        """Hook: this agent never issues a cursor, so any supplied one is invalid and `-32602`
        (`ACP-LIST-206`)."""
        if cursor is None:
            return None
        return f"invalid cursor {cursor!r}"

    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        # A session is resumable while it is live or closed on this connection; a deleted or
        # never-created one is `-32002` (`error.mdx:56`).
        session_id = params.get("sessionId")
        restored = self._restore(session_id, params.get("cwd"))
        if session_id not in self._sessions and session_id not in self._closed_sessions:
            self._unknown_session(msg_id, session_id)
            return
        rejection = (
            self._replay_from_rejection(params.get("replayFrom"))
            or self._setup_rejection(params)
            or self._system_prompt_rejection(params.get("systemPrompt"))
        )
        if rejection is not None:
            if restored:  # a refused resume must not leave the session live
                self._sessions.pop(session_id, None)
            self._error(msg_id, -32602, f"Invalid params: {rejection}")
            return
        if session_id in self._closed_sessions:
            self._sessions[session_id] = self._closed_sessions.pop(session_id)
        if self._should_replay(params.get("replayFrom")):
            self._replay_history(session_id)
        self._send_resume_session_info(session_id)
        self._resume_background(session_id)
        self._send_resume_snapshot(session_id)
        self._reply(msg_id, self._resume_result())

    @staticmethod
    def _replay_from_rejection(replay_from: Any) -> str | None:
        """Omitted/`null` (no replay) and `{"type": "start"}` are the only cursors this agent
        supports; any other well-formed cursor is unsupported and anything else is malformed --
        both `-32602` (session-setup.mdx:211-215)."""
        if replay_from is None:
            return None
        if not isinstance(replay_from, dict) or not isinstance(replay_from.get("type"), str):
            return "malformed replayFrom"
        if replay_from["type"] != "start":
            return f"unsupported replayFrom cursor type {replay_from['type']!r}"
        return None

    @staticmethod
    def _should_replay(replay_from: Any) -> bool:
        return isinstance(replay_from, dict) and replay_from.get("type") == "start"

    def _replay_history(self, session_id: Any) -> None:
        for update in self._history.get(session_id, []):
            # Replay via `_notify` directly (not `_send_update`): a replayed update must not
            # itself be re-recorded into history.
            self._notify("session/update", {"sessionId": session_id, "update": update})

    def _send_resume_session_info(self, session_id: Any) -> None:
        """Hook: the current `session_info_update` every successful resume sends after any
        replay and before responding (session-setup.mdx:358-361). Live state, not recorded."""
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {"sessionUpdate": "session_info_update", "title": "TCK fixture session"},
            },
        )

    def _resume_background(self, session_id: Any) -> None:
        """For `background_on_resume`: the session has one unfinished background tool call when
        it is resumed. List it (so the snapshot reports it) and announce it
        (session-setup.mdx:346). Idempotent across repeated resumes."""
        if not self._background_on_resume:
            return
        item = {"type": "tool_call", "toolCallId": "tool-bg-resume"}
        listed = self._background.setdefault(session_id, [])
        if item not in listed:
            listed.append(item)
        self._announce_resume_background(session_id, item["toolCallId"])

    def _announce_resume_background(self, session_id: Any, tool_call_id: str) -> None:
        """Hook: the `tool_call_update` sent before the snapshot that lists a resumed item."""
        self._announce_background_item(session_id, tool_call_id)

    def _send_resume_snapshot(self, session_id: Any) -> None:
        """The current-state `state_update` every successful resume sends before responding.
        Not recorded into history: it is live state, not conversation."""
        state = "running" if session_id in self._hanging_sessions else "idle"
        update: dict[str, Any] = {"sessionUpdate": "state_update", "state": state}
        if self._report_background_work:
            update = self._with_background(session_id, update)
        self._notify("session/update", {"sessionId": session_id, "update": update})

    def _resume_result(self) -> dict[str, Any]:
        return self._initial_state_fields()

    def _handle_fork_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        source_id = params.get("sessionId")
        if source_id not in self._sessions and source_id not in self._closed_sessions:
            self._unknown_session(msg_id, source_id)  # ACP-FORK-203
            return
        self._session_count += 1
        session_id = f"sess-{self._session_count:04d}"
        self._sessions[session_id] = params.get("cwd", "")
        self._history[session_id] = [dict(update) for update in self._history.get(source_id, [])]
        self._reply(msg_id, {"sessionId": session_id, **self._initial_state_fields()})

    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        # ACP-CANCEL-208: closing a session with a still-hanging `__hang__` prompt MUST cancel
        # that work as if `session/cancel` had been sent -- same resolution path, just triggered
        # by a different wire event, before the close itself is acknowledged.
        session_id = params.get("sessionId")
        if self._hanging_sessions.pop(session_id, None) is not None:
            self._finish_turn(session_id, "cancelled")
        if session_id in self._sessions:
            self._closed_sessions[session_id] = self._sessions.pop(session_id)
        self._reply(msg_id, {})

    def _handle_delete_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        # ACP-DELETE-204: deleting an active session cancels its work as if `session/close` had
        # been called -- a still-hanging `__hang__` prompt ends `cancelled` before the response.
        # ACP-DELETE-201/202/205: the session leaves `session/list` and can no longer be resumed.
        # ACP-DELETE-203: an unknown/already-deleted sessionId still succeeds silently.
        session_id = params.get("sessionId")
        if self._hanging_sessions.pop(session_id, None) is not None:
            self._finish_turn(session_id, "cancelled")
        cwd = self._sessions.pop(session_id, None) or self._closed_sessions.pop(session_id, None)
        self._history.pop(session_id, None)
        path = self._store_path(cwd)
        if self._persist_sessions and path is not None:
            stored = self._read_store(path)
            if stored.pop(session_id, None) is not None:
                path.write_text(json.dumps(stored))
        self._reply(msg_id, {})

    def _current_config_options(self) -> list[dict[str, Any]]:
        return [dict(option) for option in self._config_options]

    def _handle_set_config_option(self, msg_id: Any, params: dict[str, Any]) -> None:
        # ACP-CONFIG-202: replies with the *complete*, updated `configOptions` list, not just
        # the entry that changed.
        session_id = params.get("sessionId")
        if session_id not in self._sessions:
            self._unknown_session(msg_id, session_id)
            return
        config_id = params.get("configId")
        value = params.get("value")
        for option in self._config_options:
            if option.get("configId") == config_id:
                option["currentValue"] = value
                break
        else:
            self._error(msg_id, -32602, "Invalid params: unknown configId")
            return
        self._reply(msg_id, {"configOptions": self._current_config_options()})

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        # Minimal conforming sequence: result{messageId} -> user_message ->
        # state_update{running} -> agent_message_chunk -> state_update{idle,
        # stopReason:"end_turn"}. The response is an acceptance receipt only (no `stopReason`).
        #
        # Split into small overridable steps (`_reply_to_prompt`, `_send_user_message_update`,
        # `_send_running_update`, `_stop_reason`, `_send_idle_update`) so single-defect fixtures
        # under `tests/fixtures/agents/v2/` can override exactly one step. `_prompt_rejection`
        # (reject the prompt outright, e.g. `rejects_image_when_advertised.py`) and
        # `_mid_turn_action` (fire something -- a permission request, an arbitrary agent->client
        # probe -- after the running update; returning `True` defers the rest of the turn to a
        # later `_handle_response` call instead of finishing it immediately, for
        # `AsksPermissionAgent`) both no-op/pass-through by default.
        session_id = params.get("sessionId")
        # A session that was never created, or was closed, is not active.
        if session_id not in self._sessions:
            self._unknown_session(msg_id, session_id)
            return
        prompt = params.get("prompt") or []
        rejection = self._prompt_rejection(prompt)
        if rejection is not None:
            code, error_message = rejection
            self._error(msg_id, code, error_message)
            return
        if session_id in self._hanging_sessions:
            self._prompt_while_busy(msg_id, params)
            return
        self._message_count += 1
        message_id = f"msg-{self._message_count:04d}"
        self._reply_to_prompt(msg_id, message_id)
        self._send_user_message_update(session_id, message_id, prompt)
        self._send_running_update(session_id)
        self._send_rich_turn_updates(session_id)
        if self._is_hang_prompt(prompt):
            # Cancel sentinel: withhold the terminating idle until `session/cancel` (or
            # `session/close`) arrives for this session -- see `_handle_cancel`/
            # `_handle_close_session`. Preempts `_mid_turn_action` for this one prompt only.
            self._hanging_sessions[session_id] = True
            return
        if self._mid_turn_action(session_id):
            return  # the subclass deferred the rest of the turn to `_handle_response`
        self._finish_turn(session_id)

    @staticmethod
    def _is_hang_prompt(prompt: list[Any]) -> bool:
        """`True` iff `prompt` is the `__hang__` cancel sentinel: a single text block whose text
        is exactly `"__hang__"` (mirrors v1's `conforming.py` sentinel)."""
        return any(
            isinstance(block, dict) and block.get("type") == "text" and block.get("text") == "__hang__"
            for block in prompt
        )

    def _send_rich_turn_updates(self, session_id: Any) -> None:
        """Opt-in (`emit_rich_turn_updates=True`) emission of a two-chunk agent message, a
        tool_call create + follow-up patch, and a plan update -- so the ACP-PATCH-2xx/
        ACP-ENUM-2xx rows have something real to scan instead of vacuously SKIPping. No-op
        (default) for every fixture that doesn't opt in."""
        if not self._emit_rich_turn_updates:
            return
        self._message_count += 1
        chunk_message_id = f"msg-{self._message_count:04d}"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "agent_message_chunk",
                "messageId": chunk_message_id,
                "content": {"type": "text", "text": "Let me "},
            },
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "agent_message_chunk",
                "messageId": chunk_message_id,
                "content": {"type": "text", "text": "check that."},
            },
        )
        self._tool_call_count += 1
        tool_call_id = f"tool-{self._tool_call_count:04d}"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "title": "Reading a file",
                "kind": "read",
                "status": "in_progress",
            },
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "status": "completed",
                "content": [
                    {"type": "content", "content": {"type": "text", "text": "done"}},
                    {
                        "type": "diff",
                        "changes": [{"operation": "modify", "path": "/tmp/a.txt", "fileType": "text"}],
                        "patch": {
                            "format": "git_patch",
                            "text": "diff --git /tmp/a.txt /tmp/a.txt\n--- /tmp/a.txt\n+++ /tmp/a.txt\n"
                            "@@ -1 +1 @@\n-old\n+new\n",
                        },
                    },
                ],
            },
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "available_commands_update",
                "availableCommands": [
                    {"type": "command", "name": "tck", "description": "A fixture command"}
                ],
            },
        )
        self._plan_count += 1
        plan_id = f"plan-{self._plan_count:04d}"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "plan_update",
                "plan": {
                    "type": "items",
                    "planId": plan_id,
                    "entries": [
                        {
                            "content": "Check the file",
                            "priority": "medium",
                            "status": "completed",
                        }
                    ],
                },
            },
        )
        # One terminal_update (absolute cwd, ACP-PATCH-206) plus one terminal_output_chunk
        # (independently-decodable base64 data, ACP-PATCH-207), sharing a terminalId -- otherwise
        # both SKIP "no <variant> observed" against this fixture.
        self._terminal_count += 1
        terminal_id = f"term-{self._terminal_count:04d}"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "terminal_update",
                "terminalId": terminal_id,
                "command": "echo hi",
                "cwd": "/tmp",
            },
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "terminal_output_chunk",
                "terminalId": terminal_id,
                "data": base64.b64encode(b"hi\n").decode("ascii"),
            },
        )

    def _prompt_rejection(self, prompt: list[Any]) -> tuple[int, str] | None:
        """Hook: return `(code, message)` to reject this prompt outright with a JSON-RPC error
        instead of accepting it (e.g. `rejects_image_when_advertised.py`). By default a block
        the agent cannot take is rejected with `-32602` and nothing is inserted: an unknown
        type or an unadvertised `image`/`audio`/`resource`
        (`_unsupported_content_rejection`, `ACP-PROMPT-211`/`ACP-PROMPTCAP-201`), then an embedded
        `resource` with neither `text` nor `blob` (a closed site, `ACP-ENUM-204`)."""
        return self._unsupported_content_rejection(prompt) or self._contentless_resource_rejection(prompt)

    # Baseline content types, and the prompt capability each optional type needs
    # (initialization.mdx:306-331).
    _BASELINE_PROMPT_TYPES = frozenset({"text", "resource_link"})
    _PROMPT_CAPABILITY_FOR_TYPE = {"image": "image", "audio": "audio", "resource": "embeddedContext"}

    def _unsupported_content_rejection(self, prompt: list[Any]) -> tuple[int, str] | None:
        """`-32602` for a block that is neither baseline nor advertised, or of an unknown type
        (prompt-lifecycle.mdx:313)."""
        advertised = self._session_capability("prompt")
        for block in prompt:
            block_type = block.get("type") if isinstance(block, dict) else None
            if block_type in self._BASELINE_PROMPT_TYPES:
                continue
            capability = self._PROMPT_CAPABILITY_FOR_TYPE.get(block_type)
            if (
                capability is None
                or not isinstance(advertised, dict)
                or advertised.get(capability) is None
            ):
                return -32602, f"Invalid params: unsupported content type {block_type!r}"
        return None

    @staticmethod
    def _contentless_resource_rejection(prompt: list[Any]) -> tuple[int, str] | None:
        for block in prompt:
            if isinstance(block, dict) and block.get("type") == "resource":
                resource = block.get("resource")
                if not (isinstance(resource, dict) and ("text" in resource or "blob" in resource)):
                    return -32602, "Invalid params: embedded resource has neither text nor blob"
        return None

    def _mid_turn_action(self, session_id: Any) -> bool:
        """Hook fired once, right after the running update, before the reply chunk/idle. Return
        `True` to defer finishing the turn to a later `_handle_response` call (the action itself
        must arrange to call `_finish_turn` once it resolves); `False` (the default -- also used
        by an action that fires-and-forgets, not waiting for any reply) to finish the turn
        immediately, in the same call."""
        return False

    def _finish_turn(self, session_id: Any, stop_reason: str | None = None) -> None:
        """Send the closing `agent_message_chunk` and the terminating idle. `stop_reason`
        defaults to `self._stop_reason()` when omitted -- callers that already know the outcome
        (e.g. `AsksPermissionAgent`, once the permission answer is in) can pass it explicitly."""
        stop_reason = stop_reason if stop_reason is not None else self._stop_reason()
        if self._report_background_work and stop_reason != "cancelled":
            self._run_background_work(session_id)
        self._message_count += 1
        reply_message_id = f"msg-{self._message_count:04d}"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "agent_message_chunk",
                "messageId": reply_message_id,
                "content": {"type": "text", "text": "ok"},
            },
        )
        self._send_idle_update(session_id, stop_reason)

    def _run_background_work(self, session_id: Any) -> None:
        """One background tool call: announced, listed on a repeated `running` snapshot, then
        finalized and taken off the list, so the next snapshot (the turn-ending idle) removes
        it."""
        self._tool_call_count += 1
        tool_call_id = f"tool-bg-{self._tool_call_count:04d}"
        self._announce_background_item(session_id, tool_call_id)
        listed = self._background.setdefault(session_id, [])
        listed.append({"type": "tool_call", "toolCallId": tool_call_id})
        self._send_running_update(session_id)
        self._finalize_background_item(session_id, tool_call_id)
        listed.remove({"type": "tool_call", "toolCallId": tool_call_id})

    def _announce_background_item(self, session_id: Any, tool_call_id: str) -> None:
        """Hook: the `tool_call_update` sent before the first snapshot that lists the item."""
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "title": "Watching for changes",
                "kind": "other",
                "status": "in_progress",
            },
        )

    def _finalize_background_item(self, session_id: Any, tool_call_id: str) -> None:
        """Hook: the final status sent before the snapshot that removes the item."""
        self._send_update(
            session_id,
            {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id, "status": "completed"},
        )

    def _with_background(self, session_id: Any, update: dict[str, Any]) -> dict[str, Any]:
        """Hook: `update` (a `state_update`) carrying the session's current `background` list."""
        return {**update, "background": [dict(item) for item in self._background.get(session_id, [])]}

    def _reply_to_prompt(self, msg_id: Any, message_id: str) -> None:
        self._reply(msg_id, {"messageId": message_id})

    def _send_user_message_update(self, session_id: Any, message_id: str, prompt: Any) -> None:
        self._send_update(
            session_id,
            {"sessionUpdate": "user_message", "messageId": message_id, "content": prompt},
        )

    def _send_running_update(self, session_id: Any) -> None:
        self._send_update(session_id, {"sessionUpdate": "state_update", "state": "running"})

    def _stop_reason(self) -> str:
        return "end_turn"

    def _send_idle_update(self, session_id: Any, stop_reason: str | None) -> None:
        update: dict[str, Any] = {"sessionUpdate": "state_update", "state": "idle"}
        if stop_reason is not None:
            update["stopReason"] = stop_reason
        self._send_update(session_id, update)

    def _record_history(self, session_id: Any, update: dict[str, Any]) -> None:
        """Append `update` to `session_id`'s replayable history (R9), primed with a synthetic
        whole-message entry (`content: []`) the first time a `*_chunk` update's `messageId` is
        seen -- so a replay of chunk-built history is itself schema-shaped, even though this
        fixture never actually emits a chunk itself."""
        kind = update.get("sessionUpdate")
        if kind not in self._WHOLE_MESSAGE_KINDS and kind not in self._CHUNK_MESSAGE_KINDS:
            return
        history = self._history.setdefault(session_id, [])
        if kind in self._CHUNK_MESSAGE_KINDS:
            message_id = update.get("messageId")
            primed = self._primed_message_ids.setdefault(session_id, set())
            if message_id not in primed:
                primed.add(message_id)
                whole_kind = kind[: -len("_chunk")]
                history.append(
                    {"sessionUpdate": whole_kind, "messageId": message_id, "content": []}
                )
        history.append(dict(update))

    def _send_update(self, session_id: Any, update: dict[str, Any]) -> None:
        if self._report_background_work and update.get("sessionUpdate") == "state_update":
            update = self._with_background(session_id, update)
        self._record_history(session_id, update)
        self._notify("session/update", {"sessionId": session_id, "update": update})

    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        self._note_success_reply(msg_id)
        self._write({"jsonrpc": "2.0", "id": msg_id, "result": result})

    def _note_success_reply(self, msg_id: Any) -> None:
        """A success reply to the `initialize` in flight completes initialization. A fixture that
        writes its own `initialize` result instead of calling `_reply` calls this."""
        if self._pending_initialize == (msg_id,):
            self._initialized = True
            self._init_failed = False
            self._pending_initialize = None

    def _error(self, msg_id: Any, code: int, message: str, data: Any = None) -> None:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        self._write({"jsonrpc": "2.0", "id": msg_id, "error": error})

    def _unknown_session(self, msg_id: Any, session_id: Any) -> None:
        self._error(msg_id, -32002, "Resource not found", {"sessionId": session_id})

    def _notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params})

    def _write(self, obj: dict[str, Any]) -> None:
        self._write_line(obj)

    @staticmethod
    def _write_line(obj: dict[str, Any] | list[Any]) -> None:
        sys.stdout.write(json.dumps(obj, separators=(",", ":")) + "\n")
        sys.stdout.flush()


class AsksPermissionAgent(ConformingAgent):
    """Conforming, but sends `session/request_permission` mid-turn (after the running update)
    and only finishes the turn once the client answers -- the normal shape a real tool-using
    agent produces (`title`/`options` required, each option carrying `optionId`/`name`/`kind`).
    Reports `requires_action` while blocked and honors the outcome (`_after_permission`).

    `session/cancel` while blocked stops waiting: it withdraws the request with
    `$/cancel_request` and ends the work as for a `cancelled` outcome, without the answer
    (prompt-lifecycle.mdx:1177). `session/close` withdraws it the same way before responding
    (session-setup.mdx:391). A late answer is ignored. The self-test for `ACP-PERM-201`/
    `ACP-PATCH-209`/`ACP-STATE-205`/`ACP-CANCEL-209`/`ACP-CANCEL-213`/`ACP-CLOSE-205`.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._perm_counter = 0
        self._pending_permission: dict[str, Any] | None = None

    def _mid_turn_action(self, session_id: Any) -> bool:
        perm_id = self._next_permission_id()
        self._pending_permission = {"perm_id": perm_id, "session_id": session_id}
        # ACP-PATCH-209: report `requires_action` while blocked on the client's answer.
        self._send_update(session_id, {"sessionUpdate": "state_update", "state": "requires_action"})
        self._send_permission_request(perm_id, session_id)
        return True  # defer finishing the turn to `_handle_response`, below

    def _send_permission_request(self, perm_id: Any, session_id: Any) -> None:
        self._write(
            {
                "jsonrpc": "2.0",
                "id": perm_id,
                "method": "session/request_permission",
                "params": {
                    "sessionId": session_id,
                    "title": "Allow this action?",
                    "options": self._permission_options(),
                },
            }
        )

    def _next_permission_id(self) -> Any:
        """Hook: the JSON-RPC `id` of the next permission request."""
        self._perm_counter += 1
        return f"perm-{self._perm_counter}"

    def _permission_options(self) -> list[dict[str, Any]]:
        return [
            {"optionId": "allow-once", "name": "Allow", "kind": "allow_once"},
            {"optionId": "reject-once", "name": "Reject", "kind": "reject_once"},
        ]

    def _handle_response(self, message: dict[str, Any]) -> None:
        pending = self._pending_permission
        if pending is None or message.get("id") != pending["perm_id"]:
            return  # not a reply to our own outstanding permission request
        self._pending_permission = None
        result = message.get("result") or {}
        outcome = (result.get("outcome") or {}).get("outcome")
        self._after_permission(pending["session_id"], outcome)

    def _send_cancel_request(self, pending: dict[str, Any]) -> None:
        self._notify("$/cancel_request", {"requestId": pending["perm_id"]})

    def _on_cancel_while_blocked(self, pending: dict[str, Any]) -> None:
        """Hook: `session/cancel` arrived while `pending` is unanswered. Stops waiting, withdraws
        it, and ends the work as for a `cancelled` outcome."""
        self._pending_permission = None
        self._send_cancel_request(pending)
        self._after_permission(pending["session_id"], "cancelled")

    def _withdraw_on_close(self, pending: dict[str, Any]) -> None:
        """Hook: withdraw `pending` before the `session/close` response."""
        self._send_cancel_request(pending)

    def _handle_cancel(self, params: dict[str, Any]) -> None:
        pending = self._pending_permission
        if pending is not None and pending["session_id"] == params.get("sessionId"):
            self._on_cancel_while_blocked(pending)
            return
        super()._handle_cancel(params)

    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        # ACP-CLOSE-203/205: closing a session blocked on our permission request withdraws it,
        # then cancels that work, so its cancelled idle goes out before the close response.
        pending = self._pending_permission
        if pending is not None and pending["session_id"] == params.get("sessionId"):
            self._pending_permission = None
            self._withdraw_on_close(pending)
            self._send_idle_update(pending["session_id"], "cancelled")
        super()._handle_close_session(msg_id, params)

    def _after_permission(self, session_id: Any, outcome: Any) -> None:
        """Hook: a `cancelled` outcome ends the blocked work without resuming (`idle` straight
        from `requires_action`); anything else reports `running` before resuming output
        (`ACP-STATE-205`) and finishes with `end_turn`."""
        if outcome == "cancelled":
            self._send_idle_update(session_id, "cancelled")
            return
        self._send_update(session_id, {"sessionUpdate": "state_update", "state": "running"})
        self._finish_turn(session_id, "end_turn")


class SendsClientRequestAgent(ConformingAgent):
    """Conforming, but fires one arbitrary agent -> client request mid-turn (after the running
    update) and continues immediately -- it never waits for a reply, since the CLIENTCAP
    fixtures built on this only care *whether/what* was sent, not how the mock client answered
    it. Subclasses provide the method name (`_client_request_method`) and, optionally, its
    params (`_client_request_params`, empty `{}` by default).
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._probe_counter = 0

    def _client_request_method(self) -> str:
        raise NotImplementedError

    def _client_request_params(self, session_id: Any) -> dict[str, Any]:
        return {}

    def _mid_turn_action(self, session_id: Any) -> bool:
        self._probe_counter += 1
        self._write(
            {
                "jsonrpc": "2.0",
                "id": f"probe-{self._probe_counter}",
                "method": self._client_request_method(),
                "params": self._client_request_params(session_id),
            }
        )
        return False  # fire-and-forget: finish the turn immediately, in the same call
