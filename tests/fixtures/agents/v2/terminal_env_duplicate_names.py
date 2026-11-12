#!/usr/bin/env python3
"""A defect fixture for ACP-AUTH-006 (MANDATORY): advertises a `type: "terminal"` auth method
whose `env` array has two entries sharing the same `name` -- violating "Names MUST be unique"
(`schema/v2/schema.unstable.json#/$defs/AuthMethodTerminal`). v1's `env` is a string map, so the
duplicate-name defect has no v1 counterpart.

The terminal method is advertised *only* when the connecting client itself advertised
`capabilities.auth.terminal: {}` -- otherwise this fixture would also (correctly) trip
ACP-AUTH-002 on every other connection, muddying the "exactly ACP-AUTH-006" self-test. This
mirrors how ACP-AUTH-002/006 are tested against two different connections in
`test_authentication.py`: the default connection (no terminal capability) sees no `authMethods`
at all from this fixture and is unaffected; the dedicated second connection that does advertise
`capabilities.auth.terminal` is the only one that ever sees the malformed descriptor.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

TERMINAL_METHOD = {
    "methodId": "term",
    "type": "terminal",
    "name": "Terminal",
    "env": [
        {"name": "DUP", "value": "1"},
        {"name": "DUP", "value": "2"},
    ],
}


class ConditionalTerminalAgent(ConformingAgent):
    def _initialize_result(self, params: dict[str, Any]) -> dict[str, Any]:
        result = super()._initialize_result(params)
        client_capabilities = params.get("capabilities") or {}
        auth_capabilities = client_capabilities.get("auth")
        terminal_advertised = isinstance(auth_capabilities, dict) and isinstance(
            auth_capabilities.get("terminal"), dict
        )
        if terminal_advertised:
            result["authMethods"] = [TERMINAL_METHOD]
        return result


def main() -> None:
    ConditionalTerminalAgent(agent_name="tck-fixture-terminal-env-duplicate-names").run()


if __name__ == "__main__":
    main()
