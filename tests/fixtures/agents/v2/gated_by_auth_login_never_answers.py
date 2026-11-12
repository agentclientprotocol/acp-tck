#!/usr/bin/env python3
"""Like `gated_by_auth.py`, but `auth/login` is never answered (an interactive login that stays
pending). With `--auth-method tck` every session-dependent test must SKIP with the `AUTH-GATED:`
marker (not FAIL) and the run is NOT CONFORMANT via `Verdict.blocked_by_auth`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [
    {"methodId": "tck", "type": "agent", "name": "TCK"},
]


class LoginNeverAnswersAgent(ConformingAgent):
    def _handle_login(self, msg_id: Any, params: dict[str, Any]) -> None:
        return


def main() -> None:
    LoginNeverAnswersAgent(
        agent_name="tck-fixture-gated-login-never-answers-v2",
        capabilities={"session": {}},
        auth_methods=AUTH_METHODS,
        require_auth=True,
    ).run()


if __name__ == "__main__":
    main()
