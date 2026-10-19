#!/usr/bin/env python3
"""Non-conforming fixture: sends a `notice` session update on every prompt turn although the
client never advertised `clientCapabilities.session.notices`. Violates ACP-CLIENTCAP-004 only.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class EmitsNoticeAgent(EmitsUpdateAgent):
    _update = {"sessionUpdate": "notice", "severity": "warning", "title": "MCP server unavailable"}


def main() -> None:
    EmitsNoticeAgent(agent_name="tck-fixture-emits-notice-unadvertised").run()


if __name__ == "__main__":
    main()
