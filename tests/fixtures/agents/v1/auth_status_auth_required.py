#!/usr/bin/env python3
"""Non-conforming fixture: advertises `auth.status`, but answers `auth/status` with `-32000`
(authentication required), the one rejection the method must never give since clients call it
to learn whether authentication is needed. Violates ACP-AUTH-007 only; ACP-AUTH-008 SKIPs (no
`state` to judge).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"auth": {"status": {}}}


class AuthStatusAuthRequiredAgent(ConformingAgent):
    def _handle_auth_status(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32000, "Authentication required")


def main() -> None:
    AuthStatusAuthRequiredAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-auth-status-auth-required"
    ).run()


if __name__ == "__main__":
    main()
