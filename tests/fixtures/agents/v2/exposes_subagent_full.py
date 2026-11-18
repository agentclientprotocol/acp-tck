#!/usr/bin/env python3
"""Conforming fixture: `exposes_subagent.py`, except that it also advertises
`capabilities.session.delete`, so the child-session probes of the subagents connection have one
more method to ask: `session/resume`, `session/delete` and `session/close` naming an announced
child get `-32602`, `session/list` never returns a child and a later `session/new` never reuses a
child's ID. Must PASS every `ACP-SUBAGENT-*` row, `ACP-SUBAGENT-018`, `-019` and `-205` and
`ACP-LIST-004` included (non-vacuously, the delete probe among them), within the `-k` scope of
`test_subagents`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402

CAPABILITIES = {"session": {"delete": {}}}


class ExposesSubagentFullAgent(ExposesSubagentAgent):
    pass


def main() -> None:
    ExposesSubagentFullAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-exposes-subagent-full"
    ).run()


if __name__ == "__main__":
    main()
