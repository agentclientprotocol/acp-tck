#!/usr/bin/env python3
"""Defect fixture for ACP-AUTH-007: advertises `auth.status` and answers `auth/status` with a
result that lacks the required `state`, so it fails `AuthStatusResponse` validation. ACP-AUTH-008
SKIPs: there is no `state` to judge.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

CAPABILITIES = {"session": {}, "auth": {"status": {}}}


class AuthStatusMissingStateAgent(ConformingAgent):
    def _handle_auth_status(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._reply(msg_id, {"accounts": [{"label": "TCK"}]})


def main() -> None:
    AuthStatusMissingStateAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-auth-status-missing-state"
    ).run()


if __name__ == "__main__":
    main()
