#!/usr/bin/env python3
"""Non-conforming fixture: reports a `tool_call` whose `locations[].path` is relative
(`src/main.py`) on every prompt turn, although every file path in the protocol MUST be absolute.
Violates ACP-PROMPT-004 only; the update is otherwise schema-valid.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class RelativeToolCallPathAgent(EmitsUpdateAgent):
    _update = {
        "sessionUpdate": "tool_call",
        "toolCallId": "call-0001",
        "title": "Reading src/main.py",
        "kind": "read",
        "status": "completed",
        "locations": [{"path": "src/main.py"}],
    }


def main() -> None:
    RelativeToolCallPathAgent(agent_name="tck-fixture-relative-tool-call-path").run()


if __name__ == "__main__":
    main()
