#!/usr/bin/env python3
"""Conforming fixture: `exposes_subagent.py`, except that it advertises `loadSession` and
`sessionCapabilities` `list`, `close` and `delete`, so the child-session probes of the subagents
connection have something to ask: `session/load`, `session/close` and `session/delete` naming an
announced child get `-32602`, and `session/list` never returns a child. Must PASS every
`ACP-SUBAGENT-*` row, `ACP-SUBAGENT-018`, `-019` and `-020` and `ACP-LIST-004` included
(non-vacuously), within the `-k` scope of `test_subagents` and `test_client_capabilities`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402

CAPABILITIES = {
    "loadSession": True,
    "sessionCapabilities": {"list": {}, "close": {}, "delete": {}},
}


class ExposesSubagentFullAgent(ExposesSubagentAgent):
    pass


def main() -> None:
    ExposesSubagentFullAgent(
        capabilities=CAPABILITIES, agent_name="tck-fixture-exposes-subagent-full"
    ).run()


if __name__ == "__main__":
    main()
