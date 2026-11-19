#!/usr/bin/env python3
"""Non-conforming fixture: asks for permission mid-turn; on `session/cancel` it stops waiting
and ends the work `cancelled`, but never withdraws the pending request with `$/cancel_request`.
The Agent MUST cancel it: FAILs exactly `ACP-CANCEL-213` (CAPABILITY, so the verdict is NOT
CONFORMANT).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class CancelWithoutCancelRequestAgent(AsksPermissionAgent):
    def _on_cancel_while_blocked(self, pending: dict[str, Any]) -> None:
        self._pending_permission = None
        self._after_permission(pending["session_id"], "cancelled")


def main() -> None:
    CancelWithoutCancelRequestAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
