#!/usr/bin/env python3
"""Non-conforming fixture: when the client advertises `clientCapabilities.auth.terminal`, it
advertises a `type: "terminal"` auth method whose `args` is a string instead of an array of
strings. Violates ACP-AUTH-006 only; without the capability it advertises no terminal method,
so ACP-AUTH-002 still PASSes.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class TerminalAuthBadShapeAgent(ConformingAgent):
    def _initialize_result(self) -> dict[str, Any]:
        result = super()._initialize_result()
        auth = self._client_capabilities.get("auth")
        if isinstance(auth, dict) and auth.get("terminal") is True:
            result["authMethods"] = [
                {"type": "terminal", "id": "tck-terminal", "name": "Terminal", "args": "--login"}
            ]
        return result


def main() -> None:
    TerminalAuthBadShapeAgent().run()


if __name__ == "__main__":
    main()
