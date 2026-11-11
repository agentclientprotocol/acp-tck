#!/usr/bin/env python3
"""Defect fixture for ACP-AUTH-208: advertises one `type: "agent"` method but answers
`auth/login` with `{}` for any `methodId`, advertised or not, instead of rejecting an
unadvertised one (authentication.mdx:191). Fails ACP-AUTH-208 only; ACP-AUTH-210 SKIPs (nothing
was rejected, so there is no code to judge).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [{"methodId": "tck", "type": "agent", "name": "TCK"}]


class LoginAcceptsAnythingAgent(ConformingAgent):
    def _handle_login(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._authenticated = True
        self._reply(msg_id, {})


def main() -> None:
    LoginAcceptsAnythingAgent(
        capabilities={"session": {}},
        agent_name="tck-fixture-login-accepts-unadvertised-method",
        auth_methods=AUTH_METHODS,
    ).run()


if __name__ == "__main__":
    main()
