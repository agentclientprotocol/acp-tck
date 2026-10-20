#!/usr/bin/env python3
"""Conforming fixture: a dual-stack (v1 + v2) agent. `initialize(1)` selects v1 and answers with
a v1-shaped result (`agentInfo`/`agentCapabilities`, no `info`/`capabilities`);
`initialize(0)` gets `-32022` with `supported: [1, 2]`; 2 and above select v2 as usual
(initialization.mdx:98-100). Only the v1 `initialize` response is implemented -- the TCK never
drives v1 traffic on a connection that selected 1.

Positive control for `ACP-INIT-202`'s result path and `ACP-INIT-208`: must FAIL nothing.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ConformingDualAgent(ConformingAgent):
    SUPPORTED_VERSIONS = (1, 2)

    def _handle_initialize(self, msg_id: Any, params: dict[str, Any]) -> None:
        requested = params.get("protocolVersion")
        if requested == 1 and not isinstance(requested, bool):
            self._reply(
                msg_id,
                {
                    "protocolVersion": 1,
                    "agentCapabilities": {},
                    "agentInfo": {"name": "tck-fixture-conforming-dual", "version": "0.0.0"},
                    "authMethods": [],
                },
            )
            return
        super()._handle_initialize(msg_id, params)


def main() -> None:
    ConformingDualAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
