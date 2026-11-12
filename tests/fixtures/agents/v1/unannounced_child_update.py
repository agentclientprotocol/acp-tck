#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`'s child traffic, but without ever sending the
`subagent_update` that must announce the child first. The child's updates, permission request and
`session_message` participants all name an unannounced session: FAILs exactly `ACP-SUBAGENT-001`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class UnannouncedChildUpdateAgent(ExposesSubagentAgent):
    announce_child = False


def main() -> None:
    UnannouncedChildUpdateAgent(agent_name="tck-fixture-unannounced-child-update").run()


if __name__ == "__main__":
    main()
