#!/usr/bin/env python3
"""Conforming fixture that advertises every capability the suite exercises and asks for
permission on every turn: `capabilities.session.prompt.{image,audio,embeddedContext}`,
`session.prompt.skill` (plus one `skill` command entry, listed only to a client that advertised
`session.commands.skill`, so `ACP-COMMANDS-202` and `ACP-PROMPTCAP-202` PASS non-vacuously),
`session.delete`/`archive`/`additionalDirectories`/`mcp: {stdio, http}`/`fork`/`systemPrompt` (with
`mode.override`), plus a `select`-type and a
`boolean`-type `configOptions` entry (`_base.ConformingAgent`'s `config_options` param; the second
lets `ACP-CONFIG-208`/`209` probe both option types), one `availableCommands`
entry (so `ACP-RESUME-210` checks both lists), one `type: "agent"`
auth method (`methodId: "tck"`), `capabilities.auth.status` (`ACP-AUTH-007`/`008`), `emit_rich_turn_updates=True`, and `persist_sessions=True` (so
`ACP-SYSPROMPT-002`/`003`'s resume probes can restore a session on a fresh process). Built on
`AsksPermissionAgent` with `permission_tool_call=True`, so every turn also exercises the
permission-request shape and a `tool_call` subject that ends `completed` only when approved
(`ACP-PERM-203`/`ACP-PERM-002`). Must PASS every
CAPABILITY/INFORMATIONAL id its advertised capabilities gate (see `tests/v2/test_cli.py` for the
exact set).

The `tck` auth method correctly implements `auth/login`/`auth/logout` via
`_base.ConformingAgent`, but does not set `require_auth`, so `session/new` never actually gates
on it -- the `--auth-method`/`--allow-logout`-gated AUTH ids SKIP rather than FAIL when those
flags are omitted. ACP-AUTH-006 SKIPs regardless of flags: this fixture advertises no
`type: "terminal"` method at all.

`emit_rich_turn_updates=True` makes every turn also emit a two-chunk agent message, a
`tool_call_update` create+patch pair, a `plan_update`, and a terminal (`terminal_update`,
`terminal_output_chunk`, then an exit `terminal_update`), the tool call and the terminal advertising
`capabilities.cancel` until they finish (see `_base.ConformingAgent._send_rich_turn_updates`) -- this is what
lets the update-shape/enum tests PASS here instead of SKIPping "no <variant> observed".

`cancellable_work=True` makes a `__hang__` turn also start one tool call and one terminal that
advertise `capabilities.cancel` and stay open, and implements `tool_call/cancel`/`terminal/cancel`
for them (`_base.ConformingAgent._start_cancellable_work`), so `ACP-TOOLCANCEL-201/202` and
`ACP-TERMCANCEL-201/202` PASS under `--cancel-prompt __hang__` instead of SKIPping. Any other id
gets `-32602`, so the unknown-id rows (`-206/207`) PASS too. `uncancellable_work=True` adds a live
tool call and terminal that advertise no `cancel` (`_base.ConformingAgent._start_uncancellable_work`),
which the cancel methods also answer `-32602`, so the not-cancellable rows (`-208/209`) PASS.

`terminal_auth_method` gives ACP-AUTH-006's dedicated `capabilities.auth.terminal: {}`
connection a well-formed `type: "terminal"` descriptor to see (ACP-AUTH-002 still PASSes: the
default connection this fixture also answers under advertises no `auth.terminal` capability, so
the descriptor never appears there).

For a client that advertised `capabilities.session.promptSuggestions` (only the `ACP-SUGGEST-*` tests
do) it withdraws the previous suggestion list when a prompt is accepted and sends a fresh one
after each turn's idle (`_suggests.py`), so ACP-SUGGEST-001..003 PASS non-vacuously. A resume
sends none.

It advertises `capabilities.session.options`, and `_base.py` answers `session/options` (with or
without a closed or persisted `sessionId`) without creating or resuming a session or launching an
MCP server, so ACP-OPTIONS-001/002/003/009 PASS non-vacuously.

It advertises `capabilities.session.title`, and `_base.py` follows a `session/set_title` of a live
session with a `session_info_update` carrying the stored title, so ACP-LIST-208 PASSes.

Every turn also announces a fork-capable cursor before the turn's user message (v2 has no client
capability for cursors); a full resume replays it with the same `cursorId`, and `session/fork`
accepts those cursors and rejects any other with `-32602`, so ACP-CURSOR-001..004 PASS
non-vacuously (`_cursors.py`).

It supports `idempotencyKey` (`_base.py`: a retry gets the original `messageId`, a malformed key is
`-32602`, a rejected prompt leaves its key unused, keys are per session and never echoed), and
`persist_sessions` also keeps each session's history and keys, so a fresh process resumes the
session, replays the message and still recognizes the key: ACP-PROMPT-212..219 PASS non-vacuously
(`--cancel-prompt __hang__` for ACP-PROMPT-215).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402
from _cursors import CursorsMixin  # noqa: E402
from _suggests import SuggestsMixin  # noqa: E402


class ConformingFullAgent(CursorsMixin, SuggestsMixin, AsksPermissionAgent):
    pass


def main() -> None:
    ConformingFullAgent(
        capabilities={
            "session": {
                "prompt": {"image": {}, "audio": {}, "embeddedContext": {}, "skill": {}},
                "delete": {},
                "archive": {},
                "additionalDirectories": {},
                "mcp": {"stdio": {}, "http": {}},
                "fork": {},
                "systemPrompt": {"mode": {"override": {}}},
                "options": {},
                "title": {},
            },
            "auth": {"status": {}},
        },
        config_options=[
            {
                "configId": "verbosity",
                "name": "Verbosity",
                "type": "select",
                "currentValue": "normal",
                "options": [
                    {"value": "quiet", "name": "Quiet"},
                    {"value": "normal", "name": "Normal"},
                    {"value": "verbose", "name": "Verbose"},
                ],
            },
            {
                "configId": "debug_mode",
                "name": "Debug mode",
                "type": "boolean",
                "currentValue": False,
            },
        ],
        available_commands=[
            {"type": "command", "name": "tck", "description": "A TCK command"},
        ],
        skill_commands=[
            {
                "type": "skill",
                "name": "tck-skill",
                "description": "A TCK skill",
                "path": "/tmp/skills/tck-skill/SKILL.md",
            },
        ],
        auth_methods=[
            {"methodId": "tck", "type": "agent", "name": "TCK"},
        ],
        terminal_auth_method={
            "methodId": "term",
            "type": "terminal",
            "name": "Terminal Login",
            "args": ["--login"],
            "env": [{"name": "TCK_TERMINAL_AUTH", "value": "1"}],
        },
        emit_rich_turn_updates=True,
        cancellable_work=True,
        uncancellable_work=True,
        persist_sessions=True,
        permission_tool_call=True,
    ).run()


if __name__ == "__main__":
    main()
