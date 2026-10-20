#!/usr/bin/env python3
"""Non-conforming fixture: advertises `sessionCapabilities.delete` and `.list`, and answers
`session/delete` with `{}`, but the deleted session keeps appearing in `session/list`. Violates
ACP-DELETE-003 only; ACP-DELETE-001/002 and ACP-LIST-001/002 still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}, "delete": {}}}


class DeleteKeepsListingAgent(ConformingAgent):
    def _handle_delete(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {})


def main() -> None:
    DeleteKeepsListingAgent(capabilities=CAPABILITIES, agent_name="tck-fixture-delete-keeps-listing").run()


if __name__ == "__main__":
    main()
