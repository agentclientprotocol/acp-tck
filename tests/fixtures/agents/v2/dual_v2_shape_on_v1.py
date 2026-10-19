#!/usr/bin/env python3
"""Non-conforming fixture: a dual-stack agent that selects v1 for `initialize(1)` but still answers
with a v2-shaped result (`info`/`capabilities`) -- "MUST use the selected version's
initialization response shape" (initialization.mdx:98). FAILs exactly `ACP-INIT-208`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class DualV2ShapeOnV1Agent(ConformingAgent):
    SUPPORTED_VERSIONS = (1, 2)

    def _handle_initialize(self, msg_id: Any, params: dict[str, Any]) -> None:
        requested = params.get("protocolVersion")
        if requested == 1 and not isinstance(requested, bool):
            self._reply(msg_id, {**self._initialize_result(params), "protocolVersion": 1})
            return
        super()._handle_initialize(msg_id, params)


def main() -> None:
    DualV2ShapeOnV1Agent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
