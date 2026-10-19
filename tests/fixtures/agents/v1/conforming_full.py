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
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {
    "loadSession": True,
    "sessionCapabilities": {
        "list": {},
        "delete": {},
        "resume": {},
        "close": {},
        "additionalDirectories": {},
    },
    "promptCapabilities": {
        "image": True,
        "audio": True,
        "embeddedContext": True,
    },
    "auth": {
        "logout": {},
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


class ConformingFullAgent(ConformingAgent):
    def _initialize_result(self) -> dict[str, Any]:
        # A terminal method only for a client that advertised `auth.terminal` (ACP-AUTH-002),
        # so ACP-AUTH-006 has a real one to validate.
        result = super()._initialize_result()
        auth = self._client_capabilities.get("auth")
        if isinstance(auth, dict) and auth.get("terminal") is True:
            result["authMethods"] = [*result.get("authMethods", []), TERMINAL_AUTH_METHOD]
        return result


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
