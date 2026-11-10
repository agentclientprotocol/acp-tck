#!/usr/bin/env python3
"""A conforming agent that requires authentication before `session/new` (like
`gated_by_auth.py`) and advertises `auth.status`: `auth/status` answers
`state: "unauthenticated"` on a fresh connection instead of `-32000`, so ACP-AUTH-007 PASSes
against a genuinely unauthenticated agent. Passing `--auth-method tck` must not change that
result (ACP-AUTH-007's test skips the auto-`authenticate`).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

AUTH_METHODS = [
    {"id": "tck", "name": "TCK", "description": None},
]
CAPABILITIES = {"auth": {"status": {}}}


def main() -> None:
    ConformingAgent(
        capabilities=CAPABILITIES,
        agent_name="tck-fixture-gated-by-auth-with-status",
        auth_methods=AUTH_METHODS,
        require_auth=True,
    ).run()


if __name__ == "__main__":
    main()
