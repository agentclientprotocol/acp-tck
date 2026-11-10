#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: advertises `sessionCapabilities.list`, but ignores
the `cursor` and returns the first page instead of failing with `-32602` for a cursor it never
issued. Trips only ACP-LIST-003; ACP-LIST-001/002 still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"sessionCapabilities": {"list": {}}}


class ListIgnoresBadCursorAgent(ConformingAgent):
    def _handle_list(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_list(msg_id, {k: v for k, v in params.items() if k != "cursor"})


def main() -> None:
    ListIgnoresBadCursorAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-list-ignores-bad-cursor"
    ).run()


if __name__ == "__main__":
    main()
