#!/usr/bin/env python3
"""A v2-only agent with the old negotiation behaviour: it answers every well-formed `initialize`
with `protocolVersion: 2`, including a v1-shaped request (`{"protocolVersion": 1,
"clientCapabilities": {}}`), instead of rejecting a version below 2 with `-32022`. Under the
current draft that selects a version higher than requested (initialization.mdx:98-100), so under
`--protocol-version 2` it FAILs `ACP-INIT-202` and `ACP-INIT-205`.

Used by `tests/v1/test_cli.py` for the version-mismatch path where the agent *answers* the v1
handshake with another version: its v2-shaped result cannot be judged against v1's shape rules,
so every v1-shape-dependent row SKIPs with the `VERSION-MISMATCH:` marker -- the mirror image of
a v1-only agent run under `--protocol-version 2`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent, _is_well_formed_protocol_version  # noqa: E402


class V2OnlyHonestAgent(ConformingAgent):
    def _handle_initialize(self, msg_id: Any, params: dict[str, Any]) -> None:
        if _is_well_formed_protocol_version(params.get("protocolVersion")):
            self._reply(msg_id, self._initialize_result(params))
            return
        super()._handle_initialize(msg_id, params)


def main() -> None:
    V2OnlyHonestAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
