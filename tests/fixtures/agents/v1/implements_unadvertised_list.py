#!/usr/bin/env python3
"""Non-conforming fixture: answers `session/list` with a result although it does not advertise
`sessionCapabilities.list`, instead of `-32601`. Every other unadvertised gated method is still
rejected correctly. Violates ACP-ERROR-006 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ImplementsUnadvertisedListAgent(ConformingAgent):
    def _method_advertised(self, method: str) -> bool:
        return method == "session/list" or super()._method_advertised(method)


def main() -> None:
    ImplementsUnadvertisedListAgent(agent_name="tck-fixture-implements-unadvertised-list").run()


if __name__ == "__main__":
    main()
