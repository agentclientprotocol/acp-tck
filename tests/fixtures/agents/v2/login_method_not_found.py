#!/usr/bin/env python3
"""Non-conforming fixture: advertises an `authMethods` entry but answers `auth/login` with
`-32601` (Method not found). Advertising `authMethods` means the agent MUST implement
`auth/login` and `auth/logout` (authentication.mdx:51-54). Run with `--auth-method tck`, it FAILs
exactly `ACP-AUTH-204`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [{"methodId": "tck", "type": "agent", "name": "TCK"}]


class LoginMethodNotFoundAgent(ConformingAgent):
    def _handle_login(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32601, "Method not found")


def main() -> None:
    LoginMethodNotFoundAgent(capabilities={"session": {}}, auth_methods=AUTH_METHODS).run()


if __name__ == "__main__":
    main()
