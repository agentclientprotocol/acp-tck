#!/usr/bin/env python3
"""Non-conforming fixture: echoes back any requested `protocolVersion` above 2 instead of
selecting its own highest supported version (initialization.mdx:98). Requests of 2 or below go
through the base negotiation unchanged. Mirrors `tests/fixtures/agents/v1/echoes_any_version.py`.

FAILs exactly `ACP-INIT-003`, whose `65535` probe must not be echoed. `ACP-INIT-201` does not
FAIL: its equality check only applies when the `65535` probe selects a version at or below 2.

Advertises `capabilities: {"session": {}}`, same as `conforming.py`, so `ACP-SESSION-001/002`
PASS (session/new is otherwise unmodified and correct) instead of SKIPping "not advertised".
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class EchoesAnyVersionAgent(ConformingAgent):
    def _initialize_result(self, params: dict[str, Any]) -> dict[str, Any]:
        # Only reached for a well-formed request of 2 or above (see `_handle_initialize`).
        requested = params.get("protocolVersion")
        return {
            "protocolVersion": requested,
            "capabilities": dict(self._capabilities),
            "info": {"name": "tck-fixture-echoes-any-version-v2", "version": "0.0.0"},
        }


def main() -> None:
    EchoesAnyVersionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
