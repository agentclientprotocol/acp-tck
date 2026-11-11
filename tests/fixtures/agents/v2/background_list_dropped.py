#!/usr/bin/env python3
"""Non-conforming fixture: reports background work like `reports_background_work.py`, but its
`idle` state updates omit `background` after earlier updates carried it. An agent that reports
background work MUST include it on every `state_update` for the session: FAILs exactly
`ACP-STATE-206` (`ACP-STATE-208` SKIPs, since no idle snapshot carries a list).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class BackgroundListDroppedAgent(ConformingAgent):
    def _with_background(self, session_id: Any, update: dict[str, Any]) -> dict[str, Any]:
        if update.get("state") == "idle":
            return update
        return super()._with_background(session_id, update)


def main() -> None:
    BackgroundListDroppedAgent(capabilities={"session": {}}, report_background_work=True).run()


if __name__ == "__main__":
    main()
