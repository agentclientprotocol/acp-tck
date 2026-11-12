#!/usr/bin/env python3
"""Non-conforming fixture: advertises `auth.status` and answers `auth/status` with
`state: "logged_in"`, a string that is neither one of the four defined values nor `_`-prefixed.
The schema accepts any string, so ACP-AUTH-007 PASSes; violates ACP-AUTH-008 (ADVISORY) only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"auth": {"status": {}}}


class AuthStatusUnreservedStateAgent(ConformingAgent):
    def _handle_auth_status(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {"state": "logged_in"})


def main() -> None:
    AuthStatusUnreservedStateAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-auth-status-unreserved-state"
    ).run()


if __name__ == "__main__":
    main()
