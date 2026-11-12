#!/usr/bin/env python3
"""Non-conforming fixture: asks for permission mid-turn; on `session/cancel` it neither stops
waiting for the request nor withdraws it, and ends the work `cancelled` only once the client
answers it. After `session/cancel` the Agent MUST stop waiting (and SHOULD send
`$/cancel_request`): FAILs exactly `ACP-CANCEL-209` and the ADVISORY `ACP-CANCEL-213`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class CancelWaitsForPermissionAnswerAgent(AsksPermissionAgent):
    def _on_cancel_while_blocked(self, pending: dict[str, Any]) -> None:
        pass  # keep waiting; the answer then ends the work `cancelled`


def main() -> None:
    CancelWaitsForPermissionAnswerAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
