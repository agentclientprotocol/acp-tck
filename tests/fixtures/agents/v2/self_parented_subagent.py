#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), plus a
`subagent_update` sent on the child that names the child itself, making it its own parent. The
update is schema-valid and the child is already announced, so `ACP-PROMPT-002` and
`ACP-SUBAGENT-001` pass and the other association rules leave a self-reference out: FAILs exactly
`ACP-SUBAGENT-003`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SelfParentedSubagentAgent(ExposesSubagentAgent):
    def _announce_nested_child(self, child_id):
        super()._announce_nested_child(child_id)
        self._send_update(child_id, {"sessionUpdate": "subagent_update", "sessionId": child_id})


def main() -> None:
    SelfParentedSubagentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
