#!/usr/bin/env python3
"""Defect fixture for ACP-AUTH-008: advertises `auth.status` and answers `state: "logged_in"`,
which the schema accepts (open enum, so ACP-AUTH-007 PASSes) but is neither a defined
`AuthState` value nor `_`-prefixed, so it is reserved for future ACP variants.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {}, "auth": {"status": {}}}


class AuthStatusUnreservedStateAgent(ConformingAgent):
    def _handle_auth_status(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {"state": "logged_in"})


def main() -> None:
    AuthStatusUnreservedStateAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-auth-status-unreserved-state"
    ).run()


if __name__ == "__main__":
    main()
