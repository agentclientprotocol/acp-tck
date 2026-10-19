#!/usr/bin/env python3
"""Conforming fixture: advertises `capabilities: {}` (no `session`) and answers every `session/*`
method with `-32601`, as a real session-less v2 agent would. Only `initialize` is unconditional
in v2 (initialization.mdx:180-184), so this must have zero MANDATORY FAILs: every row that needs a
session either SKIPs "not advertised" or falls back to `_`-prefixed probe traffic.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class NoSessionCapabilityAgent(ConformingAgent):
    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method.startswith("session/"):
            self._error(msg_id, -32601, "Method not found")
            return
        super()._handle_request(method, msg_id, params)


def main() -> None:
    NoSessionCapabilityAgent(capabilities={}).run()


if __name__ == "__main__":
    main()
