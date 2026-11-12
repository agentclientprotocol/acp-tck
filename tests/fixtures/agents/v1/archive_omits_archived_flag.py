#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.archive` and implements it
correctly, but never reports `archived` on a listed session. Violates ACP-ARCHIVE-002 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}, "archive": {}}}


class ArchiveOmitsArchivedFlagAgent(ConformingAgent):
    def _reply(self, msg_id: Any, result: dict[str, Any]) -> None:
        if isinstance(result.get("sessions"), list):
            result = {
                **result,
                "sessions": [
                    {k: v for k, v in info.items() if k != "archived"} for info in result["sessions"]
                ],
            }
        super()._reply(msg_id, result)


def main() -> None:
    ArchiveOmitsArchivedFlagAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-archive-omits-archived-flag"
    ).run()


if __name__ == "__main__":
    main()
