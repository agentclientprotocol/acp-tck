#!/usr/bin/env python3
"""Non-conforming fixture: answers an unrecognised method with `-32001`, a JSON-RPC server-error
code inside the range ACP reserves, instead of `-32601`. Violates ACP-ERROR-008 and, since the
code is also not `-32601`, ACP-JSONRPC-004.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class LegacyServerErrorCodeAgent(ConformingAgent):
    def _handle_request(self, method: str, msg_id: Any, params: dict[str, Any]) -> None:
        if method == "_tck/does_not_exist":
            self._error(msg_id, -32001, "Server error")
            return
        super()._handle_request(method, msg_id, params)


def main() -> None:
    LegacyServerErrorCodeAgent(agent_name="tck-fixture-legacy-server-error-code").run()


if __name__ == "__main__":
    main()
