#!/usr/bin/env python3
"""Non-conforming fixture: advertises `auth.status` and answers `auth/status` with a result
that omits the required `state`. Violates ACP-AUTH-007 only; ACP-AUTH-008 SKIPs (no `state` to
judge).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"auth": {"status": {}}}


class AuthStatusMissingStateAgent(ConformingAgent):
    def _handle_auth_status(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {"accounts": []})


def main() -> None:
    AuthStatusMissingStateAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-auth-status-missing-state"
    ).run()


if __name__ == "__main__":
    main()
