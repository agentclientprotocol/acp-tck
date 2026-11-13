#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except that right after announcing the child it
sends an `fs/read_text_file` request carrying the child's `sessionId`. The announcement came first,
so `ACP-SUBAGENT-001` passes. The client advertised only `subagents`, so the request is
unadvertised: FAILs exactly `ACP-CLIENTCAP-001`, which judges the subagents connection as well as
the default one (where this agent, sending child traffic only to a client that asked for it, sends
nothing).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import exposes_subagent  # noqa: E402
from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildFsRequestAfterAnnounceAgent(ExposesSubagentAgent):
    def _announce_child(self, session_id, child_id):
        super()._announce_child(session_id, child_id)
        self._write(
            {
                "jsonrpc": "2.0",
                "id": f"{child_id}-fs",
                "method": "fs/read_text_file",
                "params": {"sessionId": child_id, "path": exposes_subagent._CHILD_DIR + "/README.md"},
            }
        )


def main() -> None:
    ChildFsRequestAfterAnnounceAgent(agent_name="tck-fixture-child-fs-request-after-announce").run()


if __name__ == "__main__":
    main()
