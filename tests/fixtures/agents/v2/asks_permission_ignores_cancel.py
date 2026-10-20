#!/usr/bin/env python3
"""Non-conforming fixture: asks for permission mid-turn, but treats a `cancelled` outcome like
any other answer -- it resumes and ends the work with `end_turn`. Cancelling a turn blocked on
user action MUST end it with `idle(cancelled)`: FAILs exactly `ACP-CANCEL-209`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import AsksPermissionAgent  # noqa: E402


class AsksPermissionIgnoresCancelAgent(AsksPermissionAgent):
    def _after_permission(self, session_id: Any, outcome: Any) -> None:
        super()._after_permission(session_id, "selected")


def main() -> None:
    AsksPermissionIgnoresCancelAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
