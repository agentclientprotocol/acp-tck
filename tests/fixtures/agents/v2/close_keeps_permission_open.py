#!/usr/bin/env python3
"""Non-conforming fixture: asks for permission mid-turn; `session/close` while blocked cancels the
work and responds, but never withdraws the pending request with `$/cancel_request`. Before
responding to `session/close`, the Agent MUST cancel it: FAILs exactly `ACP-CLOSE-205`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class CloseKeepsPermissionOpenAgent(AsksPermissionAgent):
    def _withdraw_on_close(self, pending: dict[str, Any]) -> None:
        pass


def main() -> None:
    CloseKeepsPermissionOpenAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
