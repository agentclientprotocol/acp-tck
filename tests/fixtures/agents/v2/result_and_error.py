#!/usr/bin/env python3
"""Non-conforming fixture: the `initialize` response carries both `result` and `error`.
Violates ACP-JSONRPC-002 (a response must have exactly one of `result`/`error`) and, since
`validate_response_envelope` is also part of the full-exchange schema check, ACP-SCHEMA-001 too.
Mirrors v1's `result_and_error.py` on top of v2's `_base.py`.

Note this does NOT fail ACP-INIT-001: that check only asserts `"result" in msg`, which is still
true even though `error` is illegally present too -- the narrower envelope/schema checks above
are what actually catch this defect in v2.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResultAndErrorAgent(ConformingAgent):
    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        # Only the successful `initialize` result (the one carrying `info`) is defective;
        # negotiation errors and every other reply go out normally.
        if "info" in result and "protocolVersion" in result:
            self._write(
                {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result,
                    "error": {"code": -32603, "message": "also an error, illegally"},
                }
            )
            return
        super()._reply(msg_id, result)


def main() -> None:
    ResultAndErrorAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
