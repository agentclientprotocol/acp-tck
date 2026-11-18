#!/usr/bin/env python3
"""A conforming ACP v1 fixture agent that additionally advertises and correctly implements
`loadSession` and every `sessionCapabilities` marker, plus modes, config options, prompt
capabilities, and the authentication surface (including a `terminal` auth method for a client
that advertises `auth.terminal`) -- exercising the corresponding CAPABILITY-tier
tests end to end. `_base.py` already implements all the required behavior; this fixture only
needs to turn the capabilities on and hand it the modes/config-options/auth-methods data.
`conforming.py` deliberately stays at `agentCapabilities: {}` so these tests SKIP against it
instead.

The single config option with `type: "boolean"` is only visible to a client that advertised
`clientCapabilities.session.configOptions.boolean` (Req 33; `_base.py`'s
`_visible_config_options` enforces this) -- so `ACP-CONFIG-003` also passes against this fixture
even though it *does* have a boolean option, as long as the TCK's own probe connects without
that capability (see `test_session_config.py`).

For a client that advertised `clientCapabilities.plan` (only the `ACP-PLAN-*` tests do), each
prompt turn also sends two `plan_update` messages -- an item plan and a markdown plan with an
absolute `path` -- so ACP-PLAN-002/003/004 PASS non-vacuously. Without `plan`, no plan is sent.
For a client that advertised `clientCapabilities.session.promptSuggestions` it sends a suggestion
list after each prompt response and withdraws the previous one when the next prompt is accepted, so
ACP-SUGGEST-001..004 PASS non-vacuously (`_suggests.py`); the replay on `session/load` has none.
For a client that advertised `clientCapabilities.session.cursors` it reports each agent message
with a `messageId` and announces a fork-capable cursor after it (replayed on `session/load` with
the same id), and `session/fork` accepts those cursors and rejects any other with `-32602`, so
ACP-CURSOR-001..004 PASS non-vacuously (`_cursors.py`).
It advertises `sessionCapabilities.options`, and `_base.py` answers `session/options` (with or without a
persisted `sessionId`) without creating a session or touching MCP servers, so ACP-OPTIONS-001/002/003/009
PASS non-vacuously.
It also inherits `HonorsPermissionAgent`'s permission probe, so ACP-PERM-001/002 PASS
non-vacuously; ordinary prompts never request permission.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _cursors import CursorsMixin  # noqa: E402
from _suggests import SuggestsMixin  # noqa: E402
from honors_permission import HonorsPermissionAgent  # noqa: E402

CAPABILITIES = {
    "loadSession": True,
    "sessionCapabilities": {
        "list": {},
        "delete": {},
        "archive": {},
        "resume": {},
        "close": {},
        "fork": {},
        "additionalDirectories": {},
        "systemPrompt": {},
        "options": {},
    },
    "promptCapabilities": {
        "image": True,
        "audio": True,
        "embeddedContext": True,
    },
    "auth": {
        "logout": {},
        "status": {},
    },
}

MODES = {
    "currentModeId": "default",
    "availableModes": [
        {"id": "default", "name": "Default"},
        {"id": "yolo", "name": "YOLO"},
    ],
}

CONFIG_OPTIONS = [
    {
        "id": "model",
        "name": "Model",
        "type": "select",
        "currentValue": "fast",
        "options": [
            {"value": "fast", "name": "Fast"},
            {"value": "slow", "name": "Slow"},
        ],
    },
    {
        "id": "verbose",
        "name": "Verbose",
        "type": "boolean",
        "currentValue": False,
    },
]

AUTH_METHODS = [
    {"id": "tck", "name": "TCK", "description": None},
]

TERMINAL_AUTH_METHOD = {
    "type": "terminal",
    "id": "tck-terminal",
    "name": "TCK terminal login",
    "args": ["--login"],
    "env": {"TCK_LOGIN": "1"},
}


PLANS = [
    {
        "type": "items",
        "planId": "steps",
        "entries": [{"content": "Read the code", "priority": "medium", "status": "pending"}],
    },
    {
        "type": "markdown",
        "planId": "design-doc",
        "content": "## Steps\n- [ ] Read the code",
        "path": "/tmp/plan.md",
    },
]


class ConformingFullAgent(CursorsMixin, SuggestsMixin, HonorsPermissionAgent):
    # So load/resume can be probed from a fresh process (ACP-SYSPROMPT-002/003).
    _persist_sessions = True

    def _initialize_result(self) -> dict[str, Any]:
        # A terminal method only for a client that advertised `auth.terminal` (ACP-AUTH-002),
        # so ACP-AUTH-006 has a real one to validate.
        result = super()._initialize_result()
        auth = self._client_capabilities.get("auth")
        if isinstance(auth, dict) and auth.get("terminal") is True:
            result["authMethods"] = [*result.get("authMethods", []), TERMINAL_AUTH_METHOD]
        return result

    def _handle_prompt(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id in self._sessions and "plan" in self._client_capabilities:
            for plan in PLANS:
                self._notify(
                    "session/update",
                    {"sessionId": session_id, "update": {"sessionUpdate": "plan_update", "plan": plan}},
                )
        super()._handle_prompt(msg_id, params)


def main() -> None:
    ConformingFullAgent(
        capabilities=CAPABILITIES,
        agent_name="tck-fixture-conforming-full",
        modes=dict(MODES),
        config_options=[dict(opt) for opt in CONFIG_OPTIONS],
        auth_methods=AUTH_METHODS,
    ).run()


if __name__ == "__main__":
    main()
