#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except that before announcing the child it sends
an `fs/read_text_file` request carrying the child's `sessionId`. The client advertised only
`subagents`, so the mock client answers `-32601`, which the fixture ignores. The ID is carried by
a request that is not a `session/update`, so it FAILs `ACP-SUBAGENT-001` (v1 child requests
include `fs/*` and `terminal/*`). The request is unadvertised too, so it also FAILs
`ACP-CLIENTCAP-001`, which judges the subagents connection as well as the default one. Those are
the only two. Sent only to a client that advertised `subagents`, so `ACP-CLIENTCAP-001` passes on
the default connection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import exposes_subagent  # noqa: E402
from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildFsRequestBeforeAnnounceAgent(ExposesSubagentAgent):
    def _announce_child(self, session_id, child_id):
        self._write(
            {
                "jsonrpc": "2.0",
                "id": f"{child_id}-fs",
                "method": "fs/read_text_file",
                "params": {"sessionId": child_id, "path": exposes_subagent._CHILD_DIR + "/README.md"},
            }
        )
        super()._announce_child(session_id, child_id)


def main() -> None:
    ChildFsRequestBeforeAnnounceAgent(agent_name="tck-fixture-child-fs-request-before-announce").run()


if __name__ == "__main__":
    main()
